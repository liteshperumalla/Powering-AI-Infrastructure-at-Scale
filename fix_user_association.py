#!/usr/bin/env python3
"""
Fix user association issue - update all assessments to belong to the main user.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_user_association():
    """Update all assessments to belong to the main user."""
    
    print("🔧 FIXING USER ASSOCIATION ISSUE")
    print("=" * 50)
    
    mongo_uri = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database('infra_mind')
    
    # Find the main user (liteshperumalla@gmail.com)
    main_user = await db.users.find_one({"email": "liteshperumalla@gmail.com"})
    if not main_user:
        print("❌ Main user (liteshperumalla@gmail.com) not found!")
        return False
    
    main_user_id = str(main_user["_id"])
    print(f"📧 Main user found: {main_user['email']} (ID: {main_user_id})")
    
    # Get all assessments
    assessments = await db.assessments.find({}).to_list(length=None)
    print(f"📋 Found {len(assessments)} assessments to update")
    
    # Update all assessments to belong to the main user
    for assessment in assessments:
        current_user_id = assessment.get("user_id")
        print(f"  🔄 Assessment {assessment['_id']}: {current_user_id} → {main_user_id}")
        
        await db.assessments.update_one(
            {"_id": assessment["_id"]},
            {"$set": {"user_id": main_user_id}}
        )
    
    # Also update recommendations to have correct user reference if needed
    recommendations = await db.recommendations.find({}).to_list(length=None)
    print(f"🎯 Found {len(recommendations)} recommendations to check")
    
    updated_recs = 0
    for rec in recommendations:
        # Get the assessment this recommendation belongs to
        assessment_id = rec.get("assessment_id")
        if assessment_id:
            # Update user_id if it exists in recommendation
            if "user_id" in rec and rec["user_id"] != main_user_id:
                await db.recommendations.update_one(
                    {"_id": rec["_id"]},
                    {"$set": {"user_id": main_user_id}}
                )
                updated_recs += 1
    
    print(f"✅ Updated {len(assessments)} assessments")
    print(f"✅ Updated {updated_recs} recommendations")
    
    # Verify the fix
    print(f"\n🔍 VERIFICATION:")
    user_assessments = await db.assessments.find({"user_id": main_user_id}).to_list(length=None)
    print(f"📊 Assessments now owned by main user: {len(user_assessments)}")
    
    for assessment in user_assessments:
        print(f"  ✅ {assessment.get('title', 'Unknown')} - Status: {assessment.get('status', 'unknown')}")
    
    print(f"\n🎉 USER ASSOCIATION FIX COMPLETED!")
    print(f"🔗 Dashboard should now show all assessments and reports for liteshperumalla@gmail.com")
    
    client.close()
    return True

if __name__ == "__main__":
    asyncio.run(fix_user_association())