#!/usr/bin/env python3
"""
Fix existing reports with invalid report_type values.

This script updates any reports in the database that have report_type values
that don't match the current enum, ensuring all reports can be downloaded properly.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from loguru import logger

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

# Valid report types (must match the enum in models/report.py)
VALID_REPORT_TYPES = [
    "executive_summary",
    "technical_roadmap", 
    "cost_analysis",
    "compliance_report",
    "architecture_overview",
    "full_assessment",
    "comprehensive"
]

# Mapping for converting invalid report types
REPORT_TYPE_MAPPING = {
    "executive": "executive_summary",
    "technical": "technical_roadmap",
    "full": "full_assessment",
    "comprehensive": "comprehensive",  # Already valid
    # Add more mappings as needed
}

async def fix_report_types():
    """Fix invalid report types in the database."""
    logger.info("Starting report type fix...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.get_database("infra_mind")
        reports_collection = db.reports
        
        # Find all reports
        reports = await reports_collection.find({}).to_list(None)
        logger.info(f"Found {len(reports)} reports to check")
        
        fixed_count = 0
        
        for report in reports:
            report_id = report.get("_id")
            current_type = report.get("report_type")
            
            if not current_type:
                logger.warning(f"Report {report_id} has no report_type field")
                continue
                
            if current_type not in VALID_REPORT_TYPES:
                # Try to map to a valid type
                new_type = REPORT_TYPE_MAPPING.get(current_type)
                
                if not new_type:
                    # Default to comprehensive for unknown types
                    new_type = "comprehensive"
                    logger.warning(f"Unknown report type '{current_type}' for report {report_id}, defaulting to 'comprehensive'")
                else:
                    logger.info(f"Mapping report type '{current_type}' to '{new_type}' for report {report_id}")
                
                # Update the report
                result = await reports_collection.update_one(
                    {"_id": report_id},
                    {"$set": {"report_type": new_type}}
                )
                
                if result.modified_count > 0:
                    fixed_count += 1
                    logger.success(f"Fixed report {report_id}: '{current_type}' -> '{new_type}'")
                else:
                    logger.error(f"Failed to update report {report_id}")
            else:
                logger.debug(f"Report {report_id} has valid type: '{current_type}'")
        
        logger.info(f"Report type fix completed. Fixed {fixed_count} reports.")
        
        # Close the connection
        client.close()
        
        return fixed_count
        
    except Exception as e:
        logger.error(f"Error fixing report types: {e}")
        return -1

async def main():
    """Main function."""
    logger.info("Report Type Fixer - Fixing invalid report_type values")
    logger.info("=" * 60)
    
    fixed_count = await fix_report_types()
    
    if fixed_count >= 0:
        logger.success(f"✅ Successfully fixed {fixed_count} reports")
        sys.exit(0)
    else:
        logger.error("❌ Failed to fix report types")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())