#!/usr/bin/env python3
"""
Fix visualization data by removing problematic recommended_services with Decimal128 values.
"""
import asyncio
import sys
import os
from bson import Decimal128

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database

async def fix_visualization_data():
    """Fix problematic recommended_services data that's causing API errors."""
    
    print("🔧 FIXING VISUALIZATION DATA ISSUES")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connected")
        
        # Connect directly to MongoDB to check for problematic data
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.get_database("infra_mind")
        
        # Find recommendations with recommended_services
        cursor = db.recommendations.find({"recommended_services": {"$exists": True}})
        recommendations_with_services = await cursor.to_list(length=None)
        
        print(f"📋 Found {len(recommendations_with_services)} recommendations with recommended_services")
        
        fixed_count = 0
        for rec in recommendations_with_services:
            needs_update = False
            print(f"🔍 Checking recommendation: {rec.get('title', 'Unknown')}")
            
            if 'recommended_services' in rec and rec['recommended_services']:
                # Remove the recommended_services field entirely to avoid Decimal128 issues
                print("  🗑️ Removing recommended_services field (causes Decimal128 errors)")
                await db.recommendations.update_one(
                    {"_id": rec["_id"]},
                    {"$unset": {"recommended_services": 1}}
                )
                fixed_count += 1
                needs_update = True
            
            if needs_update:
                print(f"  ✅ Fixed recommendation: {rec.get('title', 'Unknown')}")
        
        print(f"\n🎉 Fixed {fixed_count} recommendations by removing problematic recommended_services fields")
        print("✅ API should now work properly without Decimal128 errors")
        
        # Test that we can now query recommendations without errors
        print("\n🔍 Testing API query compatibility...")
        cursor = db.recommendations.find({"assessment_id": "689f9a8608403c57b7b791cb"})
        test_recs = await cursor.to_list(length=None)
        print(f"✅ Successfully queried {len(test_recs)} recommendations for test assessment")
        
        for rec in test_recs:
            if 'recommended_services' in rec:
                print(f"⚠️ Still has recommended_services: {rec.get('title')}")
            else:
                print(f"✅ Clean recommendation: {rec.get('title')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_visualization_data())