#!/usr/bin/env python3
"""
Fix progress data in assessments to remove invalid fields.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

# Import models
from infra_mind.models.assessment import Assessment


async def fix_progress_data():
    """Fix progress data to remove invalid fields."""
    try:
        # Database configuration
        MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.get_database()
        
        # Initialize beanie with models
        await init_beanie(
            database=database,
            document_models=[Assessment]
        )
        
        logger.info("Connected to database successfully")
        
        # Get all assessments
        assessments = await Assessment.find_all().to_list()
        logger.info(f"Found {len(assessments)} assessments to fix")
        
        for assessment in assessments:
            logger.info(f"Fixing assessment: {assessment.id}")
            
            # Clean progress data
            if assessment.progress and isinstance(assessment.progress, dict):
                # Remove problematic fields
                cleaned_progress = {k: v for k, v in assessment.progress.items() 
                                 if k not in ["error"] and not str(v).startswith("E11000")}
                
                # Update the assessment
                assessment.progress = cleaned_progress
                await assessment.save()
                logger.success(f"✅ Fixed progress data for assessment {assessment.id}")
            
        logger.success("✅ All assessments fixed!")
        
    except Exception as e:
        logger.error(f"Failed to fix progress data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(fix_progress_data())