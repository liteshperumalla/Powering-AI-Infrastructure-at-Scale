#!/usr/bin/env python3
"""
Fix assessment data to match Pydantic schema expectations.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://localhost:27017/infra_mind")

async def fix_assessment_data():
    """Fix assessment data structure to match Pydantic models."""
    print("🔧 Fixing Assessment Data Structure")
    print("=" * 40)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.infra_mind
        assessments_collection = db.assessments
        
        # Find all assessments
        assessments = await assessments_collection.find().to_list(None)
        print(f"Found {len(assessments)} assessments to fix")
        
        for assessment in assessments:
            assessment_id = assessment['_id']
            updates = {}
            
            # Fix agent_states if it's empty or has wrong structure
            if 'agent_states' not in assessment or assessment['agent_states'] == {}:
                updates['agent_states'] = {
                    'active_agents': {},
                    'completed_agents': {},
                    'failed_agents': {},
                    'consensus_score': {},
                    'execution_time': {}
                }
            
            # Ensure required fields exist
            if 'user_id' not in assessment:
                updates['user_id'] = 'anonymous_user'
                
            if 'tags' not in assessment:
                updates['tags'] = []
                
            if 'metadata' not in assessment:
                updates['metadata'] = {
                    'source': 'legacy',
                    'version': '1.0',
                    'tags': []
                }
            
            # Update the assessment if needed
            if updates:
                result = await assessments_collection.update_one(
                    {'_id': assessment_id},
                    {'$set': updates}
                )
                if result.modified_count > 0:
                    print(f"✅ Fixed assessment {assessment_id}")
                else:
                    print(f"⚠️  No changes needed for assessment {assessment_id}")
            else:
                print(f"✅ Assessment {assessment_id} is already correct")
        
        print("")
        print("🎉 Assessment data structure fixes completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(fix_assessment_data())