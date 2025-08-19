#!/usr/bin/env python3
"""
Test script to trigger a complete workflow through the API and check if recommendations are saved.
"""

import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_workflow():
    """Test complete workflow through API."""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Create a test user and authenticate
        logger.info("🔐 Creating test user...")
        
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        
        try:
            async with session.post(f"{base_url}/api/v1/auth/register", json=user_data) as response:
                if response.status in [200, 201]:
                    user_response = await response.json()
                    logger.info(f"✅ User created: {user_response.get('id')}")
                elif response.status == 400:
                    # User might already exist, try to login
                    logger.info("User already exists, attempting login...")
                else:
                    logger.error(f"Failed to create user: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error: {error_text}")
                    return
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        
        # Step 2: Login
        logger.info("🔑 Logging in...")
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        try:
            async with session.post(f"{base_url}/api/v1/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_response = await response.json()
                    access_token = auth_response.get("access_token")
                    logger.info("✅ Successfully logged in")
                    
                    # Set authorization header for subsequent requests
                    session.headers.update({"Authorization": f"Bearer {access_token}"})
                else:
                    logger.error(f"Failed to login: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error: {error_text}")
                    return
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return
        
        # Step 3: Create an assessment
        logger.info("📝 Creating test assessment...")
        
        assessment_data = {
            "title": "Test Workflow Assessment",
            "description": "Testing agent orchestration and recommendation generation",
            "industry": "technology",
            "company_size": "medium",
            "current_infrastructure": {
                "cloud_providers": ["aws"],
                "compute_services": ["ec2"],
                "storage_services": ["s3"],
                "network_services": ["vpc"]
            },
            "ai_requirements": {
                "use_cases": ["data_processing"],
                "model_types": ["supervised_learning"],
                "data_volume": "medium",
                "performance_requirements": "standard"
            },
            "budget_constraints": {
                "monthly_budget": 5000,
                "budget_flexibility": "medium"
            },
            "timeline": {
                "implementation_timeline": "3_months",
                "urgency": "medium"
            },
            "compliance_requirements": ["gdpr"],
            "technical_expertise": "intermediate"
        }
        
        try:
            async with session.post(f"{base_url}/api/v1/assessments/", json=assessment_data) as response:
                if response.status == 201:
                    assessment_response = await response.json()
                    assessment_id = assessment_response.get("id")
                    logger.info(f"✅ Assessment created: {assessment_id}")
                    
                    # Step 4: Submit the assessment to trigger workflow
                    logger.info("🚀 Submitting assessment to trigger workflow...")
                    
                    async with session.post(f"{base_url}/api/v1/assessments/{assessment_id}/submit") as submit_response:
                        if submit_response.status == 200:
                            submit_result = await submit_response.json()
                            logger.info("✅ Assessment submitted successfully")
                            logger.info(f"Workflow ID: {submit_result.get('workflow_id')}")
                            
                            # Step 5: Wait and check for recommendations
                            logger.info("⏳ Waiting for workflow to complete...")
                            await asyncio.sleep(30)  # Wait 30 seconds for workflow
                            
                            # Step 6: Check recommendations
                            async with session.get(f"{base_url}/api/v1/recommendations/{assessment_id}") as rec_response:
                                if rec_response.status == 200:
                                    recommendations = await rec_response.json()
                                    logger.info(f"📊 Found {len(recommendations)} recommendations")
                                    
                                    if recommendations:
                                        for i, rec in enumerate(recommendations[:3]):
                                            logger.info(f"  {i+1}. {rec.get('title', 'No title')} (Agent: {rec.get('agent_name', 'Unknown')})")
                                        return True
                                    else:
                                        logger.warning("❌ No recommendations were generated")
                                        return False
                                else:
                                    logger.error(f"Failed to get recommendations: {rec_response.status}")
                                    return False
                        else:
                            logger.error(f"Failed to submit assessment: {submit_response.status}")
                            return False
                else:
                    logger.error(f"Failed to create assessment: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error in workflow test: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_full_workflow())
    if success:
        print("🎉 Full workflow test PASSED! Recommendations are being generated and saved.")
    else:
        print("💥 Full workflow test FAILED! Recommendations are not being generated.")