#!/usr/bin/env python3
"""
Create a test assessment for testing real agents.
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

sys.path.append('/Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/src')

MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"

async def create_test_assessment():
    """Create a simple test assessment."""
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.infra_mind
        await database.command("ping")
        
        # Initialize Beanie
        from infra_mind.models import DOCUMENT_MODELS
        await init_beanie(database=database, document_models=DOCUMENT_MODELS)
        
        # Create assessment
        from infra_mind.models.assessment import Assessment
        
        assessment = Assessment(
            title="Test AI Infrastructure Assessment",
            description="Test assessment for real agent execution",
            status="draft",
            priority="medium",
            requirements={
                "budget": 100000,
                "timeline": "6 months",
                "compliance": ["SOC2", "GDPR"]
            },
            current_infrastructure={
                "cloud_provider": "AWS",
                "services": ["EC2", "RDS", "S3"],
                "estimated_cost": 5000
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await assessment.save()
        print(f"✅ Created test assessment: {assessment.id}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create assessment: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_test_assessment())