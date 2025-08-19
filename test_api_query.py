#!/usr/bin/env python3
"""
Test the exact query the API uses to see if there are any issues.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_api_query():
    """Test the exact query the API uses"""
    
    # Connect directly to MongoDB to test the query the API uses
    mongo_uri = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database('infra_mind')
    
    print("🔍 Testing API query for assessment 689f9a8608403c57b7b791cb")
    
    # Query the same way the API does
    query_filters = {'assessment_id': '689f9a8608403c57b7b791cb'}
    cursor = db.recommendations.find(query_filters)
    recommendations_docs = await cursor.to_list(length=None)
    
    print(f'📋 Found {len(recommendations_docs)} recommendations')
    
    for i, rec in enumerate(recommendations_docs):
        print(f'\n🔍 Recommendation {i+1}:')
        print(f'  Title: {rec.get("title", "Unknown")}')
        print(f'  Agent: {rec.get("agent_name", "Unknown")}')
        
        # Check for problematic fields
        if 'recommended_services' in rec:
            print(f'  ⚠️ Still has recommended_services field!')
            for j, service in enumerate(rec['recommended_services']):
                print(f'    Service {j+1}: {service.get("service_name", "Unknown")}')
                if 'estimated_monthly_cost' in service:
                    cost = service['estimated_monthly_cost']
                    print(f'      Cost type: {type(cost)}, Value: {cost}')
                    # This is what causes the error!
        else:
            print(f'  ✅ No recommended_services field')
        
        # Check other fields that could cause issues
        fields_to_check = ['cost_estimates', 'total_estimated_monthly_cost', 'recommendation_data']
        for field in fields_to_check:
            if field in rec and rec[field]:
                print(f'  {field}: {type(rec[field])} - {rec[field]}')
    
    # Test creating the response format
    print(f'\n🧪 Testing API response creation...')
    try:
        for rec in recommendations_docs:
            # Simulate what the API does
            service_recs = []
            for service in rec.get('recommended_services', []):
                # This is where the error occurs
                print(f'  Processing service: {service}')
                estimated_cost = service.get('estimated_monthly_cost')
                print(f'  Estimated cost: {estimated_cost} (type: {type(estimated_cost)})')
                
        print('✅ API response creation test passed')
        
    except Exception as e:
        print(f'❌ API response creation test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_query())