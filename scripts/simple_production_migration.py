#!/usr/bin/env python3
"""
Simplified Production Data Migration Script

This script performs a direct data migration from demo to production database
without strict model validation, focusing on data transfer and basic transformation.

Usage:
    python scripts/simple_production_migration.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from bson import ObjectId


class SimpleProductionMigrator:
    """
    Simple production data migrator that focuses on data transfer
    without strict model validation.
    """
    
    def __init__(self):
        self.source_db_url = "mongodb://admin:password@localhost:27017/infra_mind_demo?authSource=admin"
        self.target_db_url = "mongodb://admin:password@localhost:27017/infra_mind_production?authSource=admin"
        self.source_client = None
        self.target_client = None
        self.source_db = None
        self.target_db = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to source and target databases."""
        try:
            logger.info("🔌 Connecting to databases...")
            
            # Connect to source database
            self.source_client = AsyncIOMotorClient(self.source_db_url)
            self.source_db = self.source_client["infra_mind_demo"]
            
            # Connect to target database
            self.target_client = AsyncIOMotorClient(self.target_db_url)
            self.target_db = self.target_client["infra_mind_production"]
            
            # Test connections
            await self.source_client.admin.command('ping')
            await self.target_client.admin.command('ping')
            
            logger.success("✅ Database connections established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to databases: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from databases."""
        if self.source_client:
            self.source_client.close()
        if self.target_client:
            self.target_client.close()
        logger.info("🔌 Database connections closed")
    
    async def migrate_data(self):
        """Perform the complete data migration."""
        try:
            logger.info("🚀 Starting simplified production data migration...")
            
            # Collections to migrate in order (respecting dependencies)
            collections_to_migrate = [
                "users",
                "assessments", 
                "recommendations",
                "reports",
                "metrics"
            ]
            
            migration_summary = {}
            total_migrated = 0
            
            for collection_name in collections_to_migrate:
                logger.info(f"🔄 Migrating collection: {collection_name}")
                
                # Get source documents
                source_collection = self.source_db[collection_name]
                source_docs = await source_collection.find({}).to_list(length=None)
                
                if not source_docs:
                    logger.warning(f"⚠️ No documents found in {collection_name}")
                    migration_summary[collection_name] = 0
                    continue
                
                # Transform documents
                transformed_docs = []
                for doc in source_docs:
                    transformed_doc = await self.transform_document(collection_name, doc)
                    if transformed_doc:
                        transformed_docs.append(transformed_doc)
                
                if transformed_docs:
                    # Clear target collection
                    target_collection = self.target_db[collection_name]
                    await target_collection.delete_many({})
                    
                    # Insert transformed documents
                    await target_collection.insert_many(transformed_docs)
                    
                    migrated_count = len(transformed_docs)
                    migration_summary[collection_name] = migrated_count
                    total_migrated += migrated_count
                    
                    logger.success(f"✅ {collection_name}: {migrated_count} documents migrated")
                else:
                    logger.warning(f"⚠️ No valid documents to migrate for {collection_name}")
                    migration_summary[collection_name] = 0
            
            # Create indexes on target database
            await self.create_production_indexes()
            
            # Generate migration report
            await self.generate_migration_report(migration_summary, total_migrated)
            
            logger.success(f"🎉 Migration completed successfully! Total: {total_migrated} documents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def transform_document(self, collection_name: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform document for production with minimal validation."""
        try:
            if collection_name == "users":
                return await self.transform_user(doc)
            elif collection_name == "assessments":
                return await self.transform_assessment(doc)
            elif collection_name == "recommendations":
                return await self.transform_recommendation(doc)
            elif collection_name == "reports":
                return await self.transform_report(doc)
            elif collection_name == "metrics":
                return await self.transform_metric(doc)
            else:
                # For other collections, return as-is
                return doc
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to transform {collection_name} document {doc.get('_id')}: {e}")
            return None
    
    async def transform_user(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user document with basic field mapping."""
        # Map industry values to lowercase
        industry_mapping = {
            "Technology": "technology",
            "Healthcare": "healthcare", 
            "Financial Services": "finance",
            "Finance": "finance",
            "Education": "education",
            "Retail": "retail",
            "Manufacturing": "manufacturing",
            "Government": "government",
            "Media": "other",
            "Transportation": "other",
            "Energy": "other",
            "Real Estate": "other",
            "E-commerce": "retail"
        }
        
        # Map company size values to lowercase
        company_size_mapping = {
            "Startup": "startup",
            "Small Business": "small",
            "Mid-Market": "medium",
            "Enterprise": "enterprise"
        }
        
        return {
            "_id": doc.get("_id"),
            "email": doc.get("email", "").lower().strip(),
            "full_name": doc.get("full_name", ""),
            "hashed_password": doc.get("hashed_password", ""),
            "is_active": doc.get("is_active", True),
            "is_verified": doc.get("is_verified", False),
            "role": doc.get("role", "user"),
            "company_name": doc.get("company_name", ""),
            "industry": industry_mapping.get(doc.get("industry", ""), "other"),
            "company_size": company_size_mapping.get(doc.get("company_size", ""), "medium"),
            "job_title": doc.get("job_title", ""),
            "phone": doc.get("phone", ""),
            "timezone": doc.get("timezone", "UTC"),
            "preferred_cloud_providers": [],
            "notification_preferences": {
                "email_reports": True,
                "assessment_updates": True,
                "marketing": False
            },
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "last_login": doc.get("last_login"),
            "login_count": doc.get("login_count", 0)
        }
    
    async def transform_assessment(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform assessment document."""
        return {
            "_id": doc.get("_id"),
            "user_id": doc.get("user_id"),
            "title": doc.get("title", ""),
            "description": doc.get("description", ""),
            "status": doc.get("status", "draft"),
            "completion_percentage": min(100.0, max(0.0, float(doc.get("completion_percentage", 0.0)))),
            "business_requirements": doc.get("business_requirements", {}),
            "technical_requirements": doc.get("technical_requirements", {}),
            "risk_assessment": doc.get("risk_assessment", {}),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "completed_at": doc.get("completed_at"),
            "metadata": doc.get("metadata", {})
        }
    
    async def transform_recommendation(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform recommendation document."""
        return {
            "_id": doc.get("_id"),
            "assessment_id": doc.get("assessment_id"),
            "agent_name": doc.get("agent_name", ""),
            "agent_version": doc.get("agent_version", "1.0.0"),
            "recommendation_type": doc.get("recommendation_type", ""),
            "title": doc.get("title", ""),
            "description": doc.get("description", ""),
            "priority": doc.get("priority", "Medium"),
            "confidence_score": min(1.0, max(0.0, float(doc.get("confidence_score", 0.5)))),
            "estimated_cost_monthly": max(0.0, float(doc.get("estimated_cost_monthly", 0.0))),
            "estimated_implementation_time": doc.get("estimated_implementation_time", ""),
            "cloud_provider": doc.get("cloud_provider", "AWS"),
            "services": doc.get("services", []),
            "benefits": doc.get("benefits", []),
            "risks": doc.get("risks", []),
            "implementation_steps": doc.get("implementation_steps", []),
            "metrics": doc.get("metrics", {}),
            "status": doc.get("status", "pending"),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow())
        }
    
    async def transform_report(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform report document."""
        return {
            "_id": doc.get("_id"),
            "assessment_id": doc.get("assessment_id"),
            "user_id": doc.get("user_id"),
            "title": doc.get("title", ""),
            "description": doc.get("description"),
            "report_type": doc.get("report_type", "full_assessment"),
            "format": doc.get("format", "PDF"),
            "status": doc.get("status", "pending"),
            "progress_percentage": min(100.0, max(0.0, float(doc.get("progress_percentage", 0.0)))),
            "sections": doc.get("sections", []),
            "file_path": doc.get("file_path"),
            "file_size_bytes": doc.get("file_size_bytes"),
            "generated_by": doc.get("generated_by", []),
            "sharing": doc.get("sharing", {"is_public": False, "shared_with": [], "access_level": "private"}),
            "metadata": doc.get("metadata", {}),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "completed_at": doc.get("completed_at")
        }
    
    async def transform_metric(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform metric document."""
        return {
            "_id": doc.get("_id"),
            "metric_type": doc.get("metric_type", "system"),
            "metric_name": doc.get("metric_name", ""),
            "value": float(doc.get("value", 0.0)),
            "unit": doc.get("unit", "count"),
            "timestamp": doc.get("timestamp", datetime.utcnow()),
            "source": doc.get("source", "system"),
            "tags": doc.get("tags", {})
        }
    
    async def create_production_indexes(self):
        """Create essential indexes on production database."""
        try:
            logger.info("📊 Creating production database indexes...")
            
            # User indexes
            await self.target_db["users"].create_index("email", unique=True)
            await self.target_db["users"].create_index("created_at")
            
            # Assessment indexes
            await self.target_db["assessments"].create_index("user_id")
            await self.target_db["assessments"].create_index("status")
            await self.target_db["assessments"].create_index([("user_id", 1), ("created_at", -1)])
            
            # Recommendation indexes
            await self.target_db["recommendations"].create_index("assessment_id")
            await self.target_db["recommendations"].create_index("agent_name")
            
            # Report indexes
            await self.target_db["reports"].create_index("assessment_id")
            await self.target_db["reports"].create_index("user_id")
            await self.target_db["reports"].create_index("status")
            
            # Metrics indexes
            await self.target_db["metrics"].create_index("timestamp")
            await self.target_db["metrics"].create_index("metric_type")
            
            logger.success("✅ Production indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    async def generate_migration_report(self, migration_summary: Dict[str, int], total_migrated: int):
        """Generate migration completion report."""
        try:
            report = {
                "migration_id": f"simple_migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "total_documents_migrated": total_migrated,
                "collections": migration_summary,
                "source_database": "infra_mind_demo",
                "target_database": "infra_mind_production"
            }
            
            report_file = f"simple_migration_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.success(f"📄 Migration report saved: {report_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate report: {e}")


async def main():
    """Main entry point for simple migration."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    try:
        async with SimpleProductionMigrator() as migrator:
            success = await migrator.migrate_data()
            return 0 if success else 1
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)