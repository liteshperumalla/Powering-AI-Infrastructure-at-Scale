"""
Database configuration and initialization for Infra Mind.

Uses Motor (async MongoDB driver) with Beanie (async ODM) for modern,
high-performance database operations.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from .config import settings


class Database:
    """
    Database connection manager.
    
    Learning Note: This singleton pattern ensures we have one database
    connection throughout the application lifecycle.
    """
    
    client: Optional[AsyncIOMotorClient] = None
    database = None


db = Database()


async def init_database() -> None:
    """
    Initialize database connection and Beanie ODM.
    
    Learning Note: This function sets up the async MongoDB connection
    and initializes Beanie with our document models.
    """
    try:
        # Create MongoDB client
        logger.info(f"🔌 Connecting to MongoDB: {settings.mongodb_url}")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            # Connection pool settings for performance
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            # Timeout settings
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
        )
        
        # Get database
        db.database = db.client[settings.mongodb_database]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.success("✅ MongoDB connection established")
        
        # Initialize Beanie with document models
        # We'll import models here to avoid circular imports
        from ..models import DOCUMENT_MODELS
        
        await init_beanie(
            database=db.database,
            document_models=DOCUMENT_MODELS
        )
        
        logger.success("✅ Beanie ODM initialized with document models")
        
        # Create indexes for performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close database connection.
    
    Learning Note: Always clean up connections when shutting down
    to prevent connection leaks.
    """
    if db.client:
        logger.info("🔌 Closing MongoDB connection")
        db.client.close()
        logger.success("✅ MongoDB connection closed")


async def create_indexes() -> None:
    """
    Create database indexes for optimal query performance.
    
    Learning Note: Indexes are crucial for MongoDB performance.
    We create them programmatically to ensure consistency.
    """
    try:
        logger.info("📊 Creating database indexes...")
        
        # Assessment indexes
        await db.database.assessments.create_index([("user_id", 1), ("status", 1)])
        await db.database.assessments.create_index([("created_at", -1)])
        await db.database.assessments.create_index([("status", 1), ("priority", 1)])
        await db.database.assessments.create_index([("tags", 1)])
        
        # Recommendation indexes
        await db.database.recommendations.create_index([("assessment_id", 1), ("agent_name", 1)])
        await db.database.recommendations.create_index([("confidence_score", -1)])
        await db.database.recommendations.create_index([("category", 1), ("priority", 1)])
        await db.database.recommendations.create_index([("total_estimated_monthly_cost", 1)])
        await db.database.recommendations.create_index([("business_impact", 1)])
        
        # Service recommendation indexes
        await db.database.service_recommendations.create_index([("provider", 1), ("service_category", 1)])
        await db.database.service_recommendations.create_index([("estimated_monthly_cost", 1)])
        
        # User indexes
        await db.database.users.create_index([("email", 1)], unique=True)
        await db.database.users.create_index([("is_active", 1)])
        await db.database.users.create_index([("company_size", 1), ("industry", 1)])
        
        # Report indexes
        await db.database.reports.create_index([("assessment_id", 1)])
        await db.database.reports.create_index([("user_id", 1), ("status", 1)])
        await db.database.reports.create_index([("report_type", 1)])
        await db.database.reports.create_index([("created_at", -1)])
        
        # Report section indexes
        await db.database.report_sections.create_index([("report_id", 1), ("order", 1)])
        
        # Metrics indexes
        await db.database.metrics.create_index([("name", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("metric_type", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("source", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("timestamp", -1)])
        
        # Agent metrics indexes
        await db.database.agent_metrics.create_index([("agent_name", 1), ("completed_at", -1)])
        await db.database.agent_metrics.create_index([("assessment_id", 1)])
        await db.database.agent_metrics.create_index([("confidence_score", -1)])
        await db.database.agent_metrics.create_index([("execution_time_seconds", 1)])
        
        logger.success("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Some indexes may already exist: {e}")


async def get_database_info() -> dict:
    """
    Get database information for health checks.
    
    Returns:
        Dictionary with database statistics
    """
    if not db.database:
        return {"status": "disconnected"}
    
    try:
        # Get database stats
        stats = await db.database.command("dbStats")
        
        return {
            "status": "connected",
            "database": settings.mongodb_database,
            "collections": stats.get("collections", 0),
            "objects": stats.get("objects", 0),
            "dataSize": stats.get("dataSize", 0),
            "storageSize": stats.get("storageSize", 0),
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"status": "error", "error": str(e)}