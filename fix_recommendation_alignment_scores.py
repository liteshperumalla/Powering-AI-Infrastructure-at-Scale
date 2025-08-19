#!/usr/bin/env python3
"""
Fix missing alignment_score values in existing recommendations.

This script updates all recommendations that are missing the alignment_score field
with calculated values based on their confidence_score and business context.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

async def fix_alignment_scores():
    """Fix missing alignment_score values in recommendations."""
    logger.info("Starting alignment score fix...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.get_database("infra_mind")
        recommendations_collection = db.recommendations
        
        # Find recommendations without alignment_score
        recommendations = await recommendations_collection.find({
            "$or": [
                {"alignment_score": {"$exists": False}},
                {"alignment_score": None}
            ]
        }).to_list(None)
        
        logger.info(f"Found {len(recommendations)} recommendations without alignment_score")
        
        if not recommendations:
            logger.info("All recommendations already have alignment_score")
            return
        
        fixed_count = 0
        
        for rec in recommendations:
            rec_id = rec["_id"]
            confidence_score = rec.get("confidence_score", 0.5)
            
            # Calculate alignment_score based on confidence and business context
            # Use confidence as base, but add business alignment factors
            alignment_score = confidence_score
            
            # Adjust based on business impact
            business_impact = rec.get("business_impact", "medium")
            if business_impact == "high":
                alignment_score = min(1.0, alignment_score + 0.1)
            elif business_impact == "low":
                alignment_score = max(0.0, alignment_score - 0.1)
            
            # Adjust based on agent type (some agents are more business-aligned)
            agent_name = rec.get("agent_name", "")
            if agent_name in ["cto", "ai_consultant"]:
                alignment_score = min(1.0, alignment_score + 0.05)
            elif agent_name in ["cloud_engineer", "infrastructure"]:
                alignment_score = max(0.0, alignment_score - 0.05)
            
            # Ensure reasonable bounds
            alignment_score = max(0.0, min(1.0, alignment_score))
            
            # Update the recommendation
            result = await recommendations_collection.update_one(
                {"_id": rec_id},
                {"$set": {"alignment_score": alignment_score}}
            )
            
            if result.modified_count > 0:
                fixed_count += 1
                logger.info(f"Fixed recommendation {rec_id}: alignment_score = {alignment_score:.3f}")
            else:
                logger.error(f"Failed to update recommendation {rec_id}")
        
        logger.success(f"Successfully fixed {fixed_count} recommendations")
        client.close()
        return fixed_count
        
    except Exception as e:
        logger.error(f"Error fixing alignment scores: {e}")
        return -1

async def main():
    """Main function."""
    logger.info("Alignment Score Fixer - Adding missing alignment_score values")
    logger.info("=" * 60)
    
    fixed_count = await fix_alignment_scores()
    
    if fixed_count >= 0:
        logger.success(f"✅ Successfully fixed {fixed_count} recommendations")
        sys.exit(0)
    else:
        logger.error("❌ Failed to fix alignment scores")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())