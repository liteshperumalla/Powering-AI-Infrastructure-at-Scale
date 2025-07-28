#!/usr/bin/env python3
"""
Database Connection Test Script

Tests the MongoDB connection and basic database operations.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.infra_mind.core.database import init_database, close_database, get_database_info, db
from src.infra_mind.core.config import settings


async def test_database_connection():
    """Test database connection and basic operations."""
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Print current configuration
        print(f"📋 Database Configuration:")
        print(f"   • MongoDB URL: {settings.mongodb_url}")
        print(f"   • Database Name: {settings.mongodb_database}")
        print(f"   • Environment: {settings.environment}")
        
        # Test database initialization
        print(f"\n🔌 Testing database initialization...")
        await init_database()
        
        # Check if database is connected
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
                print(f"   • Storage Size: {db_info.get('storageSize', 'N/A')} bytes")
            else:
                print(f"⚠️  Database info status: {db_info}")
            
            # Test basic database operations
            print(f"\n🧪 Testing basic database operations...")
            
            # Test ping
            ping_result = await db.client.admin.command('ping')
            print(f"✅ Ping successful: {ping_result}")
            
            # List collections
            collections = await db.database.list_collection_names()
            print(f"📁 Available collections: {collections}")
            
            # Test a simple write operation
            test_collection = db.database.test_connection
            test_doc = {
                "test_id": "connection_test",
                "timestamp": datetime.utcnow(),
                "message": "Database connection test successful"
            }
            
            result = await test_collection.insert_one(test_doc)
            print(f"✅ Test document inserted with ID: {result.inserted_id}")
            
            # Test read operation
            found_doc = await test_collection.find_one({"test_id": "connection_test"})
            if found_doc:
                print(f"✅ Test document retrieved: {found_doc['message']}")
            
            # Clean up test document
            await test_collection.delete_one({"test_id": "connection_test"})
            print(f"🧹 Test document cleaned up")
            
        else:
            print("❌ Database connection failed - running in development mode")
            print("   This means the system will use mock data instead of a real database")
        
        print(f"\n🎉 Database test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        logger.error(f"Database test error: {e}", exc_info=True)
        
        # Provide troubleshooting information
        print(f"\n🔧 Troubleshooting Information:")
        print(f"   • Make sure MongoDB is running")
        print(f"   • Check if the connection URL is correct: {settings.mongodb_url}")
        print(f"   • Verify network connectivity to the database")
        print(f"   • Check if authentication credentials are correct")
        
        if "mongodb:27017" in settings.mongodb_url:
            print(f"   • It looks like you're using Docker. Make sure:")
            print(f"     - Docker containers are running")
            print(f"     - MongoDB container is accessible")
            print(f"     - Run: docker-compose up -d")
        
        if "localhost:27017" in settings.mongodb_url:
            print(f"   • For localhost connection:")
            print(f"     - Install MongoDB locally")
            print(f"     - Start MongoDB service")
            print(f"     - Or use Docker: docker run -d -p 27017:27017 mongo")
    
    finally:
        # Clean up
        await close_database()


async def test_database_models():
    """Test database models and document operations."""
    print(f"\n📋 TESTING DATABASE MODELS")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_database()
        
        if db.database is None:
            print("⚠️  Database not available - skipping model tests")
            return
        
        # Test importing models
        print("📦 Testing model imports...")
        try:
            from src.infra_mind.models import DOCUMENT_MODELS
            print(f"✅ Successfully imported {len(DOCUMENT_MODELS)} document models")
            
            for model in DOCUMENT_MODELS:
                print(f"   • {model.__name__}")
                
        except Exception as e:
            print(f"❌ Failed to import models: {e}")
        
        # Test creating a simple document
        print(f"\n🧪 Testing document creation...")
        try:
            from src.infra_mind.models.metrics import Metric, MetricType, MetricCategory
            
            # Create a test metric
            test_metric = await Metric.record_metric(
                name="database_test_metric",
                value=42.0,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="test_units",
                source="database_test"
            )
            
            print(f"✅ Test metric created successfully")
            
            # Query the metric back
            found_metric = await Metric.find_one({"name": "database_test_metric"})
            if found_metric:
                print(f"✅ Test metric retrieved: {found_metric.name} = {found_metric.value}")
                
                # Clean up
                await found_metric.delete()
                print(f"🧹 Test metric cleaned up")
            
        except Exception as e:
            print(f"❌ Document operations failed: {e}")
            logger.error(f"Document test error: {e}", exc_info=True)
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        logger.error(f"Model test error: {e}", exc_info=True)
    
    finally:
        await close_database()


async def main():
    """Run all database tests."""
    print("🚀 INFRA MIND DATABASE CONNECTION TEST")
    print("=" * 80)
    
    # Test basic connection
    await test_database_connection()
    
    # Test models
    await test_database_models()
    
    print(f"\n" + "=" * 80)
    print("🏁 DATABASE TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())