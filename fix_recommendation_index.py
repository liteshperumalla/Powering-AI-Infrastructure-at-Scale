#!/usr/bin/env python3
"""
Fix Recommendation Index Issue

This script drops the problematic unique index on recommendation_id 
that's causing duplicate key errors.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

async def fix_recommendation_index():
    """Drop the problematic unique index on recommendation_id."""
    
    try:
        # Connect to database
        MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.get_database()
        
        logger.info("🔧 Fixing recommendation index issue...")
        
        # Try to drop the problematic index
        try:
            await database.recommendations.drop_index("idx_recommendations_id_unique")
            logger.success("✅ Dropped problematic index: idx_recommendations_id_unique")
        except Exception as e:
            if "index not found" in str(e).lower():
                logger.info("ℹ️ Index idx_recommendations_id_unique not found (already removed)")
            else:
                logger.warning(f"⚠️ Could not drop index: {e}")
        
        # List current indexes to verify
        indexes = await database.recommendations.list_indexes().to_list(length=None)
        logger.info("📊 Current recommendation indexes:")
        for idx in indexes:
            logger.info(f"   • {idx.get('name', 'unnamed')}")
        
        logger.success("✅ Recommendation index fix completed")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to fix recommendation index: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_recommendation_index())