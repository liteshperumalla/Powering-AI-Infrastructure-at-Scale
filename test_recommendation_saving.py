#!/usr/bin/env python3
"""
Test script to check if agent recommendations are being saved to the database.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_recommendations():
    """Check existing recommendations in the database."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    
    # Initialize Beanie with all models
    await init_beanie(
        database=client.infra_mind,
        document_models=[User, Assessment, Recommendation]
    )
    
    # Count recommendations
    total_recommendations = await Recommendation.count()
    logger.info(f"📊 Total recommendations in database: {total_recommendations}")
    
    # Get recent recommendations
    recent_recommendations = await Recommendation.find().sort("-created_at").limit(5).to_list()
    
    if recent_recommendations:
        logger.info(f"📝 Recent recommendations:")
        for rec in recent_recommendations:
            logger.info(f"  - {rec.title} (Agent: {rec.agent_name}, Created: {rec.created_at})")
    else:
        logger.info("❌ No recommendations found in database")
    
    # Count assessments with recommendations
    assessments_with_recs = await Assessment.find({"recommendations_generated": True}).count()
    total_assessments = await Assessment.count()
    
    logger.info(f"📋 Assessments: {total_assessments} total, {assessments_with_recs} with recommendations generated")
    
    # Get assessments that should have recommendations but don't
    assessments = await Assessment.find().limit(5).to_list()
    for assessment in assessments:
        recs_for_assessment = await Recommendation.find({"assessment_id": str(assessment.id)}).count()
        logger.info(f"  Assessment {assessment.title}: {recs_for_assessment} recommendations (status: {assessment.status})")
        if hasattr(assessment, 'agent_states') and assessment.agent_states:
            logger.info(f"    Agent states: {list(assessment.agent_states.keys())}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(check_recommendations())