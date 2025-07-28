#!/usr/bin/env python3
"""
Direct Database Connection Test

Tests MongoDB connection with explicit credentials.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test_direct_connection():
    """Test direct MongoDB connection with credentials."""
    print("🔍 TESTING DIRECT DATABASE CONNECTION")
    print("=" * 50)
    
    # Use the correct connection string with authentication
    mongodb_url = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    
    print(f"📋 Connection Details:")
    print(f"   • URL: {mongodb_url}")
    
    try:
        # Create client with authentication
        client = AsyncIOMotorClient(mongodb_url)
        
        # Get database
        database = client.infra_mind
        
        # Test connection
        print(f"\n🔌 Testing connection...")
        result = await client.admin.command('ping')
        print(f"✅ Ping successful: {result}")
        
        # Test database operations
        print(f"\n🧪 Testing database operations...")
        
        # List collections
        collections = await database.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        # Test write operation
        test_collection = database.test_connection
        test_doc = {
            "test_id": "direct_connection_test",
            "timestamp": datetime.utcnow(),
            "message": "Direct database connection test successful"
        }
        
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Document inserted with ID: {result.inserted_id}")
        
        # Test read operation
        found_doc = await test_collection.find_one({"test_id": "direct_connection_test"})
        if found_doc:
            print(f"✅ Document retrieved: {found_doc['message']}")
        
        # Get database stats
        stats = await database.command("dbStats")
        print(f"📊 Database stats:")
        print(f"   • Collections: {stats.get('collections', 0)}")
        print(f"   • Objects: {stats.get('objects', 0)}")
        print(f"   • Data Size: {stats.get('dataSize', 0)} bytes")
        
        # Clean up test document
        await test_collection.delete_one({"test_id": "direct_connection_test"})
        print(f"🧹 Test document cleaned up")
        
        # Close connection
        client.close()
        
        print(f"\n🎉 Direct database connection test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Direct connection test failed: {str(e)}")
        return False

async def test_with_beanie():
    """Test with Beanie ODM initialization."""
    print(f"\n🔍 TESTING WITH BEANIE ODM")
    print("=" * 50)
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import init_beanie
        
        # Use the correct connection string
        mongodb_url = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
        
        # Create client and get database
        client = AsyncIOMotorClient(mongodb_url)
        database = client.infra_mind
        
        # Test connection first
        await client.admin.command('ping')
        print("✅ MongoDB connection established")
        
        # Import models
        from src.infra_mind.models import DOCUMENT_MODELS
        print(f"📦 Imported {len(DOCUMENT_MODELS)} document models")
        
        # Initialize Beanie
        await init_beanie(database=database, document_models=DOCUMENT_MODELS)
        print("✅ Beanie ODM initialized successfully")
        
        # Test creating a document
        from src.infra_mind.models.metrics import Metric, MetricType, MetricCategory
        
        test_metric = await Metric.record_metric(
            name="beanie_test_metric",
            value=123.45,
            metric_type=MetricType.SYSTEM_PERFORMANCE,
            category=MetricCategory.TECHNICAL,
            unit="test_units",
            source="beanie_test"
        )
        
        print(f"✅ Test metric created: {test_metric.name} = {test_metric.value}")
        
        # Query it back
        found_metric = await Metric.find_one({"name": "beanie_test_metric"})
        if found_metric:
            print(f"✅ Test metric retrieved: {found_metric.name} = {found_metric.value}")
            
            # Clean up
            await found_metric.delete()
            print(f"🧹 Test metric cleaned up")
        
        # Close connection
        client.close()
        
        print(f"\n🎉 Beanie ODM test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Beanie ODM test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all direct connection tests."""
    print("🚀 DIRECT DATABASE CONNECTION TESTS")
    print("=" * 80)
    
    # Test direct connection
    direct_success = await test_direct_connection()
    
    # Test with Beanie if direct connection works
    if direct_success:
        beanie_success = await test_with_beanie()
        
        if beanie_success:
            print(f"\n" + "=" * 80)
            print("🎉 ALL DATABASE TESTS PASSED!")
            print("✅ Your database is working correctly!")
            print("=" * 80)
        else:
            print(f"\n" + "=" * 80)
            print("⚠️  Direct connection works, but Beanie ODM has issues")
            print("=" * 80)
    else:
        print(f"\n" + "=" * 80)
        print("❌ Database connection failed")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())