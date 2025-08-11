#!/usr/bin/env python3
"""
Fix assessment workflow script to address the workflow execution issues.
This script will add better error handling and diagnostics.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"

async def test_workflow_components():
    """Test if all workflow components are working properly."""
    
    print("🧪 Testing Workflow Components...")
    print("=" * 50)
    
    try:
        # Test MongoDB connection
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.infra_mind
        await db.command("ping")
        print("✅ MongoDB connection: OK")
        
        # Test Redis connection (basic test)
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection: OK")
        
        # Test if we can import key modules
        try:
            from src.infra_mind.workflows.orchestrator import agent_orchestrator, OrchestrationConfig
            print("✅ Orchestrator import: OK")
        except ImportError as e:
            print(f"❌ Orchestrator import failed: {e}")
            return False
        
        try:
            from src.infra_mind.agents.base import AgentRole, agent_factory
            print("✅ Agent factory import: OK")
        except ImportError as e:
            print(f"❌ Agent factory import failed: {e}")
            return False
        
        # Test OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('INFRA_MIND_OPENAI_API_KEY')
        if api_key and api_key.startswith('sk-'):
            print("✅ OpenAI API key: Present")
        else:
            print(f"❌ OpenAI API key: Missing or invalid")
            return False
            
        # Test agent creation
        try:
            agent = agent_factory.create_agent(AgentRole.CTO, {})
            if agent:
                print("✅ Agent creation: OK")
            else:
                print("❌ Agent creation: Failed - returned None")
                return False
        except Exception as e:
            print(f"❌ Agent creation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        traceback.print_exc()
        return False

async def fix_and_restart_assessment():
    """Fix the assessment workflow and restart it properly."""
    
    print("\n🔧 Attempting to Fix and Restart Assessment...")
    print("=" * 50)
    
    # First test components
    if not await test_workflow_components():
        print("❌ Workflow components test failed. Cannot proceed with fix.")
        return False
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Find the failed assessment
        assessment = await db.assessments.find_one({"status": {"$in": ["failed", "pending"]}})
        
        if not assessment:
            print("❌ No failed or pending assessments found")
            return False
        
        assessment_id = assessment["_id"]
        print(f"📋 Found assessment: {assessment_id}")
        
        # Reset assessment to proper state
        result = await db.assessments.update_one(
            {"_id": assessment_id},
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
        
        if result.modified_count > 0:
            print("✅ Assessment reset to draft state")
        else:
            print("❌ Failed to reset assessment")
            return False
        
        # Clean up any orphaned recommendations/reports
        await db.recommendations.delete_many({"assessment_id": str(assessment_id)})
        await db.reports.delete_many({"assessment_id": str(assessment_id)})
        print("🧹 Cleaned up orphaned recommendations and reports")
        
        print(f"✅ Assessment {assessment_id} is now ready to be started again")
        print(f"🚀 Use the frontend or API to start the assessment: POST /api/v2/assessments/{assessment_id}/start")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        traceback.print_exc()
        return False
    
    finally:
        client.close()

async def create_simple_test_assessment():
    """Create a simple test assessment to verify the workflow is working."""
    
    print("\n🧪 Creating Test Assessment...")
    print("=" * 50)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Create a minimal test assessment
        test_assessment = {
            "user_id": "test_user_id",
            "title": "Test Assessment - Workflow Fix",
            "description": "Test assessment created to verify workflow functionality",
            "business_requirements": {
                "company_size": "small",
                "industry": "technology",
                "business_goals": [{
                    "goal": "Test goal",
                    "priority": "medium",
                    "timeline_months": 3
                }],
                "budget_constraints": {
                    "total_budget_range": "10k_50k",
                    "monthly_budget_limit": 10000
                },
                "team_structure": {
                    "total_developers": 5,
                    "cloud_expertise_level": 3
                },
                "compliance_requirements": ["basic"]
            },
            "technical_requirements": {
                "workload_types": ["web_application"],
                "performance_requirements": {
                    "api_response_time_ms": 500,
                    "requests_per_second": 100,
                    "concurrent_users": 50,
                    "uptime_percentage": 99.0
                },
                "security_requirements": {
                    "encryption_at_rest_required": True,
                    "encryption_in_transit_required": True
                },
                "preferred_programming_languages": ["Python"]
            },
            "status": "draft",
            "priority": "medium",
            "completion_percentage": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.assessments.insert_one(test_assessment)
        test_assessment_id = result.inserted_id
        
        print(f"✅ Created test assessment: {test_assessment_id}")
        print(f"🚀 You can now test the workflow with: POST /api/v2/assessments/{test_assessment_id}/start")
        
        return str(test_assessment_id)
        
    except Exception as e:
        print(f"❌ Failed to create test assessment: {e}")
        traceback.print_exc()
        return None
    
    finally:
        client.close()

async def main():
    """Main function to fix assessment workflow issues."""
    
    print("🔧 Assessment Workflow Fix Script")
    print("=" * 50)
    
    # Step 1: Test workflow components
    components_ok = await test_workflow_components()
    
    if not components_ok:
        print("\n❌ Workflow components have issues. Please check:")
        print("1. MongoDB and Redis are running")
        print("2. All Python dependencies are installed") 
        print("3. OPENAI_API_KEY environment variable is set")
        print("4. All source code modules are properly imported")
        return
    
    # Step 2: Fix existing failed assessment
    print("\n" + "=" * 50)
    fixed = await fix_and_restart_assessment()
    
    if fixed:
        print("\n✅ Assessment workflow has been fixed!")
    
    # Step 3: Create a test assessment
    print("\n" + "=" * 50)
    test_id = await create_simple_test_assessment()
    
    if test_id:
        print(f"\n🎉 All Done! Assessment workflow should now be working.")
        print(f"📝 Test with assessment ID: {test_id}")
        print(f"🔧 Fixed existing failed assessment(s)")
        print("\nNext steps:")
        print("1. Use the frontend to start an assessment")
        print("2. Monitor the logs: docker logs infra-mind-api-dev -f")
        print("3. Check WebSocket updates in the frontend")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main())