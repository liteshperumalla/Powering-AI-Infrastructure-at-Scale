#!/usr/bin/env python3
"""
Final cleanup of all remaining problematic fields.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def final_cleanup():
    """Remove all remaining recommended_services fields"""
    
    print("🧹 FINAL CLEANUP - REMOVING ALL RECOMMENDED_SERVICES")
    print("=" * 60)
    
    mongo_uri = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database('infra_mind')
    
    # Remove ALL recommended_services fields
    result = await db.recommendations.update_many(
        {'recommended_services': {'$exists': True}},
        {'$unset': {'recommended_services': 1}}
    )
    
    print(f'✅ Removed recommended_services from {result.modified_count} recommendations')
    
    # Verify cleanup
    remaining = await db.recommendations.find({'recommended_services': {'$exists': True}}).to_list(length=None)
    print(f'📊 Remaining with recommended_services: {len(remaining)}')
    
    # Test API compatibility one more time
    print(f"\n🧪 Final API compatibility test...")
    query_filters = {'assessment_id': '689f9a8608403c57b7b791cb'}
    cursor = db.recommendations.find(query_filters)
    test_recs = await cursor.to_list(length=None)
    
    print(f"✅ Found {len(test_recs)} recommendations for API test")
    
    for rec in test_recs:
        if 'recommended_services' in rec:
            print(f"  ⚠️ Still has recommended_services: {rec.get('title')}")
        else:
            print(f"  ✅ Clean: {rec.get('title')}")
    
    print(f"\n🎉 CLEANUP COMPLETE!")

if __name__ == "__main__":
    asyncio.run(final_cleanup())