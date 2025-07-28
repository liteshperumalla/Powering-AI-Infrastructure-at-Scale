#!/usr/bin/env python3
"""
Database Connection Test with Fresh Configuration

Tests the database connection by forcing a fresh configuration load.
"""

import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_fresh_config():
    """Test database connection with fresh configuration."""
    print("🚀 TESTING DATABASE WITH FRESH CONFIGURATION")
    print("=" * 80)
    
    # Set environment variable directly
    os.environ["INFRA_MIND_MONGODB_URL"] = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    
    # Clear any cached configuration
    from src.infra_mind.core.config import get_settings
    get_settings.cache_clear()
    
    # Import after setting environment
    from src.infra_mind.core.database import init_database, close_database, get_database_info, db
    from src.infra_mind.core.config import settings
    
    print(f"📋 Configuration:")
    print(f"   • MongoDB URL: {settings.mongodb_url}")
    print(f"   • Database Name: {settings.mongodb_database}")
    print(f"   • Environment: {settings.environment}")
    
    try:
        # Test database initialization
        print(f"\n🔌 Testing database initialization...")
        await init_database()
        
        if db.database is not None:
            print("✅ Database connection successful!")
            
            # Get database info
            print(f"\n📊 Getting database information...")
            db_info = await get_database_info()
            
            if db_info.get("status") == "connected":
                print("✅ Database info retrieved successfully:")
                print(f"   • Status: {db_info['status']}")
                print(f"   • Database: {db_info['database']}")
                print(f"   • Collections: {db_info.get('collections', 'N/A')}")
                print(f"   • Objects: {db_info.get('objects', 'N/A')}")
                print(f"   • Data Size: {db_info.get('dataSize', 'N/A')} bytes")
            else:
                print(f"⚠️  Database info error: {db_info}")
            
            # Test basic operations
            print(f"\n🧪 Testing basic database operations...")
            
            # Test ping
            ping_result = await db.client.admin.command('ping')
            print(f"✅ Ping successful: {ping_result}")
            
            # List collections
            collections = await db.database.list_collection_names()
            print(f"📁 Available collections: {collections}")
            
            # Test document operations with Beanie
            print(f"\n📋 Testing Beanie ODM operations...")
            from src.infra_mind.models.metrics import Metric, MetricType, MetricCategory
            
            # Create a test metric
            test_metric = await Metric.record_metric(
                name="config_test_metric",
                value=99.9,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="test_units",
                source="config_test"
            )
            
            print(f"✅ Test metric created: {test_metric.name} = {test_metric.value}")
            
            # Query it back
            found_metric = await Metric.find_one({"name": "config_test_metric"})
            if found_metric:
                print(f"✅ Test metric retrieved: {found_metric.name} = {found_metric.value}")
                
                # Clean up
                await found_metric.delete()
                print(f"🧹 Test metric cleaned up")
            
            print(f"\n🎉 All database tests PASSED!")
            print("✅ Your database is fully working with the application!")
            
        else:
            print("❌ Database connection failed")
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        logger.error(f"Database test error: {e}", exc_info=True)
    
    finally:
        await close_database()

async def main():
    """Run the database test with fresh configuration."""
    await test_with_fresh_config()

if __name__ == "__main__":
    asyncio.run(main())