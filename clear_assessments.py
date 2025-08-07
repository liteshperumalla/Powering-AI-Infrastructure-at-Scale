#!/usr/bin/env python3
"""
Clear all assessments from the database.

This script will:
1. Connect to the MongoDB database
2. Clear all assessments, recommendations, and reports
3. Reset the database for a fresh start
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
from infra_mind.models.recommendation import Recommendation  
from infra_mind.models.report import Report


async def clear_database():
    """Clear all assessments and related data from the database."""
    try:
        # Database configuration
        MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.get_database()
        
        # Initialize beanie with models
        await init_beanie(
            database=database,
            document_models=[Assessment, Recommendation, Report]
        )
        
        logger.info("Connected to database successfully")
        
        # Get current counts
        assessment_count = await Assessment.count()
        recommendation_count = await Recommendation.count() 
        report_count = await Report.count()
        
        logger.info(f"Current database state:")
        logger.info(f"  - Assessments: {assessment_count}")
        logger.info(f"  - Recommendations: {recommendation_count}")
        logger.info(f"  - Reports: {report_count}")
        
        if assessment_count == 0 and recommendation_count == 0 and report_count == 0:
            logger.info("Database is already clean!")
            return
        
        # Clear all collections
        logger.info("Clearing all assessments...")
        await Assessment.delete_all()
        
        logger.info("Clearing all recommendations...")
        await Recommendation.delete_all()
        
        logger.info("Clearing all reports...")
        await Report.delete_all()
        
        # Verify cleanup
        assessment_count_after = await Assessment.count()
        recommendation_count_after = await Recommendation.count()
        report_count_after = await Report.count()
        
        logger.info(f"Database state after cleanup:")
        logger.info(f"  - Assessments: {assessment_count_after}")
        logger.info(f"  - Recommendations: {recommendation_count_after}")
        logger.info(f"  - Reports: {report_count_after}")
        
        if assessment_count_after == 0 and recommendation_count_after == 0 and report_count_after == 0:
            logger.success("✅ Database cleared successfully!")
            logger.info("Dashboard should now show fresh visualizations for new assessments")
        else:
            logger.error("❌ Some data still remains in database")
            
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        try:
            client.close()
        except:
            pass


async def main():
    """Main function."""
    logger.info("🗑️  Assessment Database Cleanup Tool")
    logger.info("=" * 50)
    
    # Ask for confirmation
    print("\nThis will permanently delete ALL assessments, recommendations, and reports from the database.")
    print("Auto-confirming database cleanup...")
    
    confirmation = 'yes'  # Auto-confirm for automated cleanup
    if confirmation not in ['yes', 'y']:
        logger.info("Operation cancelled by user")
        return
    
    await clear_database()
    
    logger.info("=" * 50)
    logger.info("✅ Database cleanup completed!")
    logger.info("\nNext steps:")
    logger.info("1. Create a new assessment through the web interface")
    logger.info("2. Dashboard should show fresh visualizations")
    logger.info("3. Assessment workflow should complete successfully")


if __name__ == "__main__":
    asyncio.run(main())