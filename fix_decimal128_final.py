#!/usr/bin/env python3
"""
Fix all remaining Decimal128 values in the database.
"""
import asyncio
import os
from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_all_decimal128_values():
    """Fix all Decimal128 values in recommendations."""
    
    print("🔧 FIXING ALL DECIMAL128 VALUES")
    print("=" * 50)
    
    # Connect directly to MongoDB
    mongo_uri = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database('infra_mind')
    
    # Find all recommendations
    cursor = db.recommendations.find({})
    all_recs = await cursor.to_list(length=None)
    
    print(f"📋 Found {len(all_recs)} recommendations to check")
    
    fixed_count = 0
    
    for rec in all_recs:
        updates = {}
        needs_update = False
        
        print(f"🔍 Checking: {rec.get('title', 'Unknown')}")
        
        # Check total_estimated_monthly_cost
        if 'total_estimated_monthly_cost' in rec and isinstance(rec['total_estimated_monthly_cost'], Decimal128):
            decimal_value = rec['total_estimated_monthly_cost']
            float_value = float(str(decimal_value))
            updates['total_estimated_monthly_cost'] = float_value
            needs_update = True
            print(f"  🔄 Converting total_estimated_monthly_cost: {decimal_value} -> {float_value}")
        
        # Check cost_estimates for nested Decimal128 values
        if 'cost_estimates' in rec and isinstance(rec['cost_estimates'], dict):
            cost_estimates = rec['cost_estimates'].copy()
            updated_cost_estimates = False
            
            for key, value in cost_estimates.items():
                if isinstance(value, Decimal128):
                    cost_estimates[key] = float(str(value))
                    updated_cost_estimates = True
                    print(f"  🔄 Converting cost_estimates.{key}: {value} -> {float(str(value))}")
                elif isinstance(value, dict):
                    # Check nested dictionaries
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, Decimal128):
                            value[sub_key] = float(str(sub_value))
                            updated_cost_estimates = True
                            print(f"  🔄 Converting cost_estimates.{key}.{sub_key}: {sub_value} -> {float(str(sub_value))}")
            
            if updated_cost_estimates:
                updates['cost_estimates'] = cost_estimates
                needs_update = True
        
        # Check recommendation_data for Decimal128 values
        if 'recommendation_data' in rec and isinstance(rec['recommendation_data'], dict):
            recommendation_data = rec['recommendation_data'].copy()
            updated_recommendation_data = False
            
            for key, value in recommendation_data.items():
                if isinstance(value, Decimal128):
                    recommendation_data[key] = float(str(value))
                    updated_recommendation_data = True
                    print(f"  🔄 Converting recommendation_data.{key}: {value} -> {float(str(value))}")
            
            if updated_recommendation_data:
                updates['recommendation_data'] = recommendation_data
                needs_update = True
        
        # Apply updates if needed
        if needs_update:
            await db.recommendations.update_one(
                {"_id": rec["_id"]},
                {"$set": updates}
            )
            fixed_count += 1
            print(f"  ✅ Fixed recommendation: {rec.get('title', 'Unknown')}")
        else:
            print(f"  ✅ No Decimal128 values found")
    
    print(f"\n🎉 Fixed {fixed_count} recommendations with Decimal128 values")
    print("✅ All values are now properly encoded as floats")
    
    # Test the API query one more time
    print(f"\n🧪 Testing API compatibility...")
    query_filters = {'assessment_id': '689f9a8608403c57b7b791cb'}
    cursor = db.recommendations.find(query_filters)
    test_recs = await cursor.to_list(length=None)
    
    print(f"📋 Found {len(test_recs)} recommendations for test")
    
    for rec in test_recs:
        # Check if any Decimal128 values remain
        total_cost = rec.get('total_estimated_monthly_cost')
        if total_cost:
            print(f"  Total cost: {total_cost} (type: {type(total_cost)})")
            if isinstance(total_cost, Decimal128):
                print(f"  ⚠️ Still has Decimal128 value!")
            else:
                print(f"  ✅ Properly converted to {type(total_cost)}")

if __name__ == "__main__":
    asyncio.run(fix_all_decimal128_values())