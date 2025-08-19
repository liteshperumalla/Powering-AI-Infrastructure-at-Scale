#!/usr/bin/env python3
"""
Test script to manually trigger agent execution and debug recommendation saving.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.user import User
from src.infra_mind.workflows.orchestrator import agent_orchestrator, OrchestrationConfig
from src.infra_mind.agents.base import AgentRole

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_execution():
    """Test agent execution and recommendation saving."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    
    # Initialize Beanie with all models
    await init_beanie(
        database=client.infra_mind,
        document_models=[User, Assessment, Recommendation]
    )
    
    # Get an existing assessment to test with
    assessment = await Assessment.find_one()
    if not assessment:
        logger.error("❌ No assessments found in database")
        return
    
    logger.info(f"🧪 Testing with assessment: {assessment.title} (ID: {assessment.id})")
    
    # Configure orchestrator for single agent test
    orchestration_config = OrchestrationConfig(
        max_parallel_agents=1,
        agent_timeout_seconds=60,
        retry_failed_agents=True,
        max_retries=1,
        require_consensus=False,
        enable_agent_communication=True
    )
    
    # Update orchestrator config
    agent_orchestrator.config = orchestration_config
    
    # Test with just one agent first (CTO agent)
    agent_roles = [AgentRole.CTO]
    
    logger.info(f"🚀 Starting orchestration with {len(agent_roles)} agent(s)...")
    
    try:
        # Execute orchestration
        orchestration_result = await agent_orchestrator.orchestrate_assessment(
            assessment=assessment,
            agent_roles=agent_roles,
            context={
                "assessment_id": str(assessment.id),
                "orchestration_mode": "test",
                "priority": "high"
            }
        )
        
        logger.info(f"✅ Orchestration completed:")
        logger.info(f"  - Total agents: {orchestration_result.total_agents}")
        logger.info(f"  - Successful agents: {orchestration_result.successful_agents}")
        logger.info(f"  - Failed agents: {orchestration_result.failed_agents}")
        logger.info(f"  - Execution time: {orchestration_result.execution_time:.2f}s")
        logger.info(f"  - Synthesized recommendations: {len(orchestration_result.synthesized_recommendations)}")
        
        # Check agent results
        for agent_name, result in orchestration_result.agent_results.items():
            logger.info(f"  - Agent {agent_name}: {result.status.value}")
            if result.error:
                logger.error(f"    Error: {result.error}")
            logger.info(f"    Recommendations: {len(result.recommendations)}")
            if result.recommendations:
                for i, rec in enumerate(result.recommendations[:2]):  # Show first 2
                    logger.info(f"      {i+1}. {rec.get('title', 'No title')}")
        
        # Now test the recommendation saving part manually
        logger.info(f"🔄 Testing recommendation saving...")
        
        saved_count = 0
        for synthesized_rec in orchestration_result.synthesized_recommendations:
            try:
                # Create a test recommendation
                recommendation = Recommendation(
                    assessment_id=str(assessment.id),
                    user_id=assessment.user_id,
                    agent_name=synthesized_rec.get("source_agent", "test_agent"),
                    title=synthesized_rec.get("title", "Test Recommendation"),
                    summary=synthesized_rec.get("description", "Test recommendation from orchestration"),
                    confidence_level="high",
                    confidence_score=85.0,
                    business_alignment=90.0,
                    recommended_services=[],
                    cost_estimates={},
                    total_estimated_monthly_cost=1500.00,
                    implementation_steps=synthesized_rec.get("implementation_steps", ["Test step"]),
                    prerequisites=[],
                    risks_and_considerations=["Test risk"],
                    business_impact="high",
                    alignment_score=90.0,
                    tags=["test", "orchestrated"],
                    priority="high",
                    category=synthesized_rec.get("type", "test")
                )
                
                # Try to save it
                await recommendation.insert()
                saved_count += 1
                logger.info(f"✅ Saved recommendation: {recommendation.title}")
                
            except Exception as e:
                logger.error(f"❌ Failed to save recommendation: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"💾 Total recommendations saved: {saved_count}")
        
        # Verify saved recommendations
        total_recommendations = await Recommendation.find({"assessment_id": str(assessment.id)}).count()
        logger.info(f"📊 Total recommendations in database for this assessment: {total_recommendations}")
        
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_agent_execution())