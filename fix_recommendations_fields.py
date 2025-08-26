#!/usr/bin/env python3
"""
Fix missing required fields in recommendations to resolve API 500 errors.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

async def fix_recommendations():
    """Fix missing fields in recommendations that cause Pydantic validation errors."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_database("infra_mind")
    
    print("🔧 FIXING RECOMMENDATIONS API VALIDATION ISSUES")
    print("=" * 55)
    
    # Get all recommendations
    recommendations = await db.recommendations.find({}).to_list(length=None)
    print(f"📊 Found {len(recommendations)} recommendations to check")
    
    fixed_count = 0
    
    for rec in recommendations:
        rec_id = rec["_id"]
        title = rec.get("title", "Unknown")
        
        # Build update document
        updates = {}
        
        if not rec.get("agent_name"):
            category = rec.get("category", "infrastructure")
            updates["agent_name"] = f"ai_{category}_agent"
        
        if not rec.get("confidence_level"):
            updates["confidence_level"] = "high"
            
        if not rec.get("confidence_score"):
            updates["confidence_score"] = 0.85
            
        if not rec.get("updated_at"):
            updates["updated_at"] = datetime.now(timezone.utc)
        
        if updates:
            print(f"  📝 Fixing: {title}")
            print(f"    Adding fields: {list(updates.keys())}")
            
            # Update the document
            result = await db.recommendations.update_one(
                {"_id": rec_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                fixed_count += 1
                print(f"    ✅ Successfully updated")
            else:
                print(f"    ❌ Failed to update")
        else:
            print(f"  ✅ {title}: All required fields present")
    
    print(f"\n🎉 COMPLETED: Fixed {fixed_count} recommendations")
    
    # Verify fixes
    print("\n🔍 VERIFICATION:")
    updated_recs = await db.recommendations.find({}).to_list(length=None)
    
    for rec in updated_recs:
        title = rec.get("title", "Unknown")
        required_fields = ["agent_name", "confidence_level", "confidence_score", "updated_at"]
        missing = [field for field in required_fields if not rec.get(field)]
        
        if missing:
            print(f"  ❌ {title}: Missing {missing}")
        else:
            print(f"  ✅ {title}: All fields present")
            # Show field values
            print(f"    agent_name: {rec.get('agent_name')}")
            print(f"    confidence_level: {rec.get('confidence_level')}")
            print(f"    confidence_score: {rec.get('confidence_score')}")
            print(f"    updated_at: {rec.get('updated_at')}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(fix_recommendations())