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
        # Create MongoDB client with optimized connection pool settings
        logger.info(f"🔌 Connecting to MongoDB: {settings.mongodb_url}")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            # Optimized connection pool settings for performance
            maxPoolSize=50,  # Increased for better concurrency
            minPoolSize=5,   # Higher minimum to avoid connection overhead
            maxIdleTimeMS=30000,  # Reduced idle time for better resource management
            # Optimized timeout settings
            connectTimeoutMS=3000,  # Faster connection timeout
            serverSelectionTimeoutMS=3000,  # Faster server selection
            socketTimeoutMS=10000,  # Socket timeout for long operations
            # Additional performance settings
            retryWrites=True,  # Enable retry writes for better reliability
            retryReads=True,   # Enable retry reads for better reliability
            compressors="zstd,zlib,snappy",  # Enable compression for better network performance
            zlibCompressionLevel=6,  # Balanced compression level
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
        logger.warning(f"⚠️ Database initialization failed: {e}")
        logger.info("🔄 Running in development mode without database")
        # In development mode, we can continue without database
        # The API endpoints will use mock data
        if settings.environment == "development":
            logger.info("✅ Development mode: API will use mock data")
        else:
            # In production, database is required
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
        
        # Assessment indexes with performance optimization
        await db.database.assessments.create_index([("user_id", 1), ("status", 1)])
        await db.database.assessments.create_index([("created_at", -1)])
        await db.database.assessments.create_index([("status", 1), ("priority", 1)])
        await db.database.assessments.create_index([("tags", 1)])
        # Compound index for common queries
        await db.database.assessments.create_index([("user_id", 1), ("created_at", -1)])
        await db.database.assessments.create_index([("status", 1), ("created_at", -1)])
        
        # Recommendation indexes with performance optimization
        await db.database.recommendations.create_index([("assessment_id", 1), ("agent_name", 1)])
        await db.database.recommendations.create_index([("confidence_score", -1)])
        await db.database.recommendations.create_index([("category", 1), ("priority", 1)])
        await db.database.recommendations.create_index([("total_estimated_monthly_cost", 1)])
        await db.database.recommendations.create_index([("business_impact", 1)])
        # Compound indexes for complex queries
        await db.database.recommendations.create_index([("assessment_id", 1), ("confidence_score", -1)])
        await db.database.recommendations.create_index([("agent_name", 1), ("created_at", -1)])
        
        # Service recommendation indexes
        await db.database.service_recommendations.create_index([("provider", 1), ("service_category", 1)])
        await db.database.service_recommendations.create_index([("estimated_monthly_cost", 1)])
        await db.database.service_recommendations.create_index([("provider", 1), ("estimated_monthly_cost", 1)])
        
        # User indexes with performance optimization
        await db.database.users.create_index([("email", 1)], unique=True)
        await db.database.users.create_index([("is_active", 1)])
        await db.database.users.create_index([("company_size", 1), ("industry", 1)])
        await db.database.users.create_index([("created_at", -1)])
        
        # Report indexes with performance optimization
        await db.database.reports.create_index([("assessment_id", 1)])
        await db.database.reports.create_index([("user_id", 1), ("status", 1)])
        await db.database.reports.create_index([("report_type", 1)])
        await db.database.reports.create_index([("created_at", -1)])
        # Compound indexes for common report queries
        await db.database.reports.create_index([("user_id", 1), ("created_at", -1)])
        await db.database.reports.create_index([("assessment_id", 1), ("report_type", 1)])
        
        # Report section indexes
        await db.database.report_sections.create_index([("report_id", 1), ("order", 1)])
        
        # Metrics indexes with time-series optimization
        await db.database.metrics.create_index([("name", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("metric_type", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("source", 1), ("timestamp", -1)])
        await db.database.metrics.create_index([("timestamp", -1)])
        # TTL index for automatic cleanup of old metrics (30 days)
        await db.database.metrics.create_index([("timestamp", 1)], expireAfterSeconds=2592000)
        
        # Agent metrics indexes with performance optimization
        await db.database.agent_metrics.create_index([("agent_name", 1), ("completed_at", -1)])
        await db.database.agent_metrics.create_index([("assessment_id", 1)])
        await db.database.agent_metrics.create_index([("confidence_score", -1)])
        await db.database.agent_metrics.create_index([("execution_time_seconds", 1)])
        # Compound indexes for agent performance analysis
        await db.database.agent_metrics.create_index([("agent_name", 1), ("execution_time_seconds", 1)])
        await db.database.agent_metrics.create_index([("agent_name", 1), ("confidence_score", -1)])
        
        # Performance monitoring indexes
        await db.database.query_performance.create_index([("query_hash", 1), ("timestamp", -1)])
        await db.database.query_performance.create_index([("collection", 1), ("execution_time_ms", -1)])
        await db.database.query_performance.create_index([("timestamp", -1)])
        
        logger.success("✅ Database indexes created successfully with performance optimizations")
        
    except Exception as e:
        logger.warning(f"⚠️ Some indexes may already exist: {e}")


async def get_database():
    """Get database instance for quality modules."""
    if db.database is None:
        # Return a mock database for testing
        from unittest.mock import Mock
        mock_db = Mock()
        mock_db.feedback = Mock()
        mock_db.quality_scores = Mock()
        mock_db.agent_metrics = Mock()
        mock_db.experiments = Mock()
        mock_db.experiment_assignments = Mock()
        mock_db.experiment_events = Mock()
        mock_db.quality_alerts = Mock()
        mock_db.improvement_actions = Mock()
        mock_db.quality_reports = Mock()
        mock_db.quality_trends = Mock()
        mock_db.improvement_queue = Mock()
        return mock_db
    return db.database


async def get_database_info() -> dict:
    """
    Get database information for health checks.
    
    Returns:
        Dictionary with database statistics
    """
    if db.database is None:
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