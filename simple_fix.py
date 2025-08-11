#!/usr/bin/env python3
"""Simple fix for the failed assessment - just reset it to ready state."""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"

async def simple_fix():
    """Reset the failed assessment to ready state."""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Reset all failed/pending assessments to ready state
        result = await db.assessments.update_many(
            {"status": {"$in": ["failed", "pending"]}},
            {
                "$set": {
                    "status": "draft",
                    "completion_percentage": 0.0,
                    "started_at": None,
                    "completed_at": None,
                    "updated_at": datetime.utcnow(),
                    "progress": {
                        "current_step": "ready_to_start",
                        "completed_steps": ["created"],
                        "total_steps": 5,
                        "progress_percentage": 0.0
                    }
                },
                "$unset": {
                    "error_info": "",
                    "phase_errors": "",
                    "workflow_errors": ""
                }
            }
        )
        
        print(f"✅ Fixed {result.modified_count} assessments")
        
        # Show current assessments
        assessments = await db.assessments.find({}, {"title": 1, "status": 1, "created_at": 1}).to_list(length=10)
        print("\n📋 Current Assessments:")
        for assessment in assessments:
            print(f"  - {assessment['_id']}: {assessment.get('title', 'No title')} [{assessment.get('status', 'unknown')}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(simple_fix())