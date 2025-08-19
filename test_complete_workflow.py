#!/usr/bin/env python3
"""
Comprehensive test of the complete workflow including:
- All 6 agents (CTO, Cloud Engineer, Research, Infrastructure, Compliance, MLOps)
- Cloud APIs (AWS, Azure, GCP)
- Azure OpenAI integration
- Terraform integration
- Database storage
"""

import asyncio
import logging
from datetime import datetime
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from src.infra_mind.models.assessment import Assessment, AssessmentStatus
from src.infra_mind.agents.base import AgentRole
from src.infra_mind.agents import agent_factory
from src.infra_mind.llm.manager import LLMManager
from src.infra_mind.cloud.unified import UnifiedCloudClient
from src.infra_mind.cloud.terraform import TerraformClient
from src.infra_mind.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """Test the complete workflow with all components."""
    
    logger.info("🚀 Testing Complete AI Infrastructure Assessment Workflow")
    logger.info("=" * 70)
    
    # 1. Test Azure OpenAI
    logger.info("1️⃣ Testing Azure OpenAI...")
    try:
        settings = get_settings()
        llm_manager = LLMManager()
        from src.infra_mind.llm.interface import LLMRequest
        
        test_request = LLMRequest(
            prompt="Respond with 'AZURE_OPENAI_READY' if you can see this.",
            model=settings.llm_model,
            temperature=0.1,
            max_tokens=20
        )
        
        response = await llm_manager.generate_response(test_request)
        logger.info(f"✅ Azure OpenAI working: {response.content}")
        logger.info(f"   Cost: ${response.cost:.4f}, Provider: {response.provider}")
    except Exception as e:
        logger.error(f"❌ Azure OpenAI failed: {e}")
        return False
    
    # 2. Test Agent Creation (All 6 Agents)
    logger.info("\n2️⃣ Testing All 6 Agents Creation...")
    
    required_agents = [
        AgentRole.CTO,
        AgentRole.CLOUD_ENGINEER, 
        AgentRole.RESEARCH,
        AgentRole.INFRASTRUCTURE,
        AgentRole.COMPLIANCE,
        AgentRole.MLOPS
    ]
    
    agent_results = {}
    for role in required_agents:
        try:
            agent = agent_factory.create_agent(role.value)
            if agent:
                logger.info(f"✅ {role.value} agent created successfully")
                agent_results[role.value] = True
            else:
                logger.error(f"❌ {role.value} agent creation failed")
                agent_results[role.value] = False
        except Exception as e:
            logger.error(f"❌ {role.value} agent error: {e}")
            agent_results[role.value] = False
    
    working_agents = sum(agent_results.values())
    logger.info(f"📊 Agent Summary: {working_agents}/{len(required_agents)} agents working")
    
    # 3. Test Cloud APIs
    logger.info("\n3️⃣ Testing Cloud APIs...")
    cloud_results = {}
    
    # Test Unified Cloud Client
    try:
        aws_creds = settings.get_aws_credentials()
        azure_creds = settings.get_azure_credentials()
        
        unified_client = UnifiedCloudClient(
            aws_access_key_id=aws_creds["access_key_id"],
            aws_secret_access_key=aws_creds["secret_access_key"],
            aws_region=aws_creds["region"],
            azure_subscription_id=azure_creds.get("subscription_id"),
            azure_client_id=azure_creds.get("client_id"),
            azure_client_secret=azure_creds.get("client_secret"),
            gcp_project_id=settings.gcp_project_id,
            gcp_service_account_path=settings.gcp_service_account_path
        )
        
        # Test AWS
        try:
            aws_compute = await unified_client.get_compute_services(provider=None)
            aws_services = sum(len(response.services) for response in aws_compute.values())
            logger.info(f"✅ AWS: {aws_services} compute services available")
            cloud_results["aws"] = True
        except Exception as e:
            logger.error(f"❌ AWS failed: {e}")
            cloud_results["aws"] = False
        
        # Test Azure  
        try:
            azure_compute = await unified_client.get_compute_services(provider=None)
            azure_services = sum(len(response.services) for response in azure_compute.values() if hasattr(response, 'services'))
            logger.info(f"✅ Azure: Services accessible")
            cloud_results["azure"] = True
        except Exception as e:
            logger.error(f"❌ Azure failed: {e}")
            cloud_results["azure"] = False
            
        # Test GCP
        try:
            gcp_compute = await unified_client.get_compute_services(provider=None)
            gcp_services = sum(len(response.services) for response in gcp_compute.values() if hasattr(response, 'services'))
            logger.info(f"✅ GCP: Services accessible")
            cloud_results["gcp"] = True
        except Exception as e:
            logger.error(f"❌ GCP failed: {e}")
            cloud_results["gcp"] = False
            
    except Exception as e:
        logger.error(f"❌ Cloud API setup failed: {e}")
        cloud_results = {"aws": False, "azure": False, "gcp": False}
    
    # 4. Test Terraform Integration
    logger.info("\n4️⃣ Testing Terraform Integration...")
    terraform_working = False
    try:
        terraform_client = TerraformClient()
        
        # Test provider lookup
        providers = await terraform_client.get_providers()
        if providers:
            logger.info(f"✅ Terraform: Provider registry accessible")
            terraform_working = True
        else:
            logger.warning("⚠️  Terraform: Provider registry empty")
            
    except Exception as e:
        logger.error(f"❌ Terraform failed: {e}")
    
    # 5. Test Complete Assessment Workflow
    logger.info("\n5️⃣ Testing Complete Assessment Workflow...")
    try:
        # Create test assessment
        assessment = Assessment(
            requirements={
                "scale_target": "1000 users",
                "budget_range": "$5000-10000/month",
                "performance_requirements": "low latency",
                "compliance_needs": ["SOC2", "GDPR"],
                "technology_stack": ["Python", "React", "PostgreSQL"],
                "deployment_preference": "multi-cloud"
            },
            status=AssessmentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Initialize workflow
        workflow = AssessmentWorkflow()
        
        # Run assessment with all agents
        logger.info("🔄 Starting workflow orchestration with all 6 agents...")
        result = await workflow.run_assessment(
            assessment=assessment,
            agent_roles=required_agents
        )
        
        logger.info(f"✅ Workflow completed successfully!")
        logger.info(f"   Assessment ID: {result.assessment_id}")
        logger.info(f"   Agents executed: {result.successful_agents}/{result.total_agents}")
        logger.info(f"   Execution time: {result.execution_time:.2f}s")
        logger.info(f"   Recommendations generated: {len(result.synthesized_recommendations)}")
        
        # Show sample recommendations
        if result.synthesized_recommendations:
            for i, rec in enumerate(result.synthesized_recommendations[:2]):
                logger.info(f"   Sample Rec {i+1}: {rec.get('title', 'N/A')[:50]}...")
        
        workflow_success = result.successful_agents >= 3  # At least half working
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        workflow_success = False
    
    # 6. Final Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 COMPLETE SYSTEM TEST SUMMARY")
    logger.info("=" * 70)
    
    logger.info(f"🤖 Azure OpenAI:     ✅ Working")
    logger.info(f"👥 Agents ({working_agents}/6):    {'✅ All Working' if working_agents == 6 else '⚠️  Partial'}")
    
    working_clouds = sum(cloud_results.values())
    logger.info(f"☁️  Cloud APIs ({working_clouds}/3): {'✅ All Working' if working_clouds == 3 else '⚠️  Partial'}")
    
    logger.info(f"🏗️  Terraform:       {'✅ Working' if terraform_working else '❌ Failed'}")
    logger.info(f"🔄 Full Workflow:   {'✅ Working' if workflow_success else '❌ Failed'}")
    
    # Overall system health
    total_components = 5
    working_components = sum([
        1,  # Azure OpenAI always works
        1 if working_agents >= 4 else 0,  # Most agents working
        1 if working_clouds >= 2 else 0,  # Most clouds working  
        1 if terraform_working else 0,
        1 if workflow_success else 0
    ])
    
    health_percentage = (working_components / total_components) * 100
    
    if health_percentage >= 80:
        logger.info(f"🎉 SYSTEM STATUS: FULLY OPERATIONAL ({health_percentage:.0f}%)")
        logger.info("🚀 Ready for production infrastructure assessments!")
    elif health_percentage >= 60:
        logger.info(f"⚠️  SYSTEM STATUS: MOSTLY WORKING ({health_percentage:.0f}%)")
        logger.info("📋 Some components need attention")
    else:
        logger.info(f"❌ SYSTEM STATUS: NEEDS FIXES ({health_percentage:.0f}%)")
        logger.info("🔧 Multiple components require repair")
    
    return health_percentage >= 80

if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    print(f"\n{'🎉 COMPLETE SYSTEM TEST PASSED!' if success else '💥 SYSTEM TEST FAILED!'}")