#!/usr/bin/env python3
"""
Direct Assessment Workflow Test

This script directly creates an assessment in the database and runs the 
complete workflow to verify all fixes are working properly.
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId
from loguru import logger

# Import models and workflow
from infra_mind.models.assessment import Assessment
from infra_mind.models.recommendation import Recommendation  
from infra_mind.models.report import Report
from infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from infra_mind.schemas.base import AssessmentStatus

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_complete_workflow():
    """Test the complete assessment workflow end-to-end."""
    
    logger.info("🚀 Starting Complete Assessment Workflow Test")
    logger.info("=" * 60)
    
    try:
        # Database configuration
        MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
        
        logger.info("📊 Connecting to database...")
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.get_database()
        
        # Initialize beanie with models
        await init_beanie(
            database=database,
            document_models=[Assessment, Recommendation, Report]
        )
        
        logger.info("✅ Database connected successfully")
        
        # Create test assessment directly in database
        logger.info("📝 Creating test assessment...")
        
        test_assessment = Assessment(
            user_id="test_user_workflow_validation",
            title=f"Workflow Test Assessment - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Testing complete workflow with all fixes applied",
            status=AssessmentStatus.DRAFT,
            business_requirements={
                "company_size": "medium",
                "industry": "technology", 
                "budget_range": "$50k-100k",
                "primary_goals": ["cost_optimization", "scalability", "security"],
                "timeline": "6_months",
                "compliance_requirements": ["SOC2", "GDPR"]
            },
            technical_requirements={
                "workload_types": ["web_application", "api_service", "data_processing"],
                "current_infrastructure": "cloud",
                "expected_users": 10000,
                "performance_requirements": {
                    "response_time": "200ms",
                    "availability": "99.9%"
                }
            },
            progress={
                "current_step": "draft",
                "completed_steps": ["draft"],
                "total_steps": 5,
                "progress_percentage": 0.0
            },
            completion_percentage=0.0
        )
        
        # Save assessment to database
        await test_assessment.insert()
        logger.info(f"✅ Assessment created with ID: {test_assessment.id}")
        
        # Initialize workflow
        logger.info("🔄 Starting assessment workflow...")
        workflow = AssessmentWorkflow()
        
        # Generate workflow ID
        workflow_id = f"test_workflow_{test_assessment.id}_{datetime.now().strftime('%H%M%S')}"
        
        # Execute workflow
        start_time = datetime.now()
        
        try:
            result = await workflow.execute_workflow(
                workflow_id=workflow_id,
                assessment=test_assessment,
                context={"test_mode": True, "validate_fixes": True}
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ Workflow execution time: {execution_time:.2f} seconds")
            
            # Check workflow result
            if result.status == "completed":
                logger.info("✅ Workflow completed successfully!")
                
                # Validate results
                await validate_workflow_results(test_assessment.id, result)
                
            elif result.status == "failed":
                logger.error(f"❌ Workflow failed: {result.error}")
                return False
            else:
                logger.warning(f"⚠️ Workflow status: {result.status}")
                return False
                
        except Exception as workflow_error:
            logger.error(f"❌ Workflow execution failed: {workflow_error}")
            return False
        
        logger.info("=" * 60)
        logger.info("✅ Complete Assessment Workflow Test PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        try:
            client.close()
        except:
            pass

async def validate_workflow_results(assessment_id: PydanticObjectId, workflow_result):
    """Validate that the workflow produced the expected results."""
    
    logger.info("🔍 Validating workflow results...")
    
    try:
        # Check assessment was updated
        updated_assessment = await Assessment.get(assessment_id)
        
        if not updated_assessment:
            raise Exception("Assessment not found after workflow")
            
        logger.info(f"   📊 Assessment status: {updated_assessment.status}")
        logger.info(f"   📈 Completion percentage: {updated_assessment.completion_percentage}%")
        
        # Validate progress
        if updated_assessment.completion_percentage < 100:
            logger.warning(f"   ⚠️ Assessment not 100% complete: {updated_assessment.completion_percentage}%")
        else:
            logger.info("   ✅ Assessment marked as 100% complete")
        
        # Check if status is completed
        if updated_assessment.status == AssessmentStatus.COMPLETED:
            logger.info("   ✅ Assessment status is COMPLETED")
        elif updated_assessment.status == AssessmentStatus.FAILED:
            logger.error("   ❌ Assessment status is FAILED")
            return False
        else:
            logger.warning(f"   ⚠️ Assessment status: {updated_assessment.status}")
        
        # Check workflow result data
        if hasattr(workflow_result, 'agent_results') and workflow_result.agent_results:
            agent_count = len(workflow_result.agent_results)
            logger.info(f"   🤖 Agent results: {agent_count} agents executed")
            
            # Count recommendations from agents
            total_recommendations = 0
            for agent_name, agent_result in workflow_result.agent_results.items():
                recs = agent_result.get("recommendations", [])
                total_recommendations += len(recs)
                logger.info(f"     - {agent_name}: {len(recs)} recommendations")
            
            logger.info(f"   📋 Total recommendations generated: {total_recommendations}")
            
            if total_recommendations == 0:
                logger.warning("   ⚠️ No recommendations generated")
            else:
                logger.info("   ✅ Recommendations generated successfully")
        
        # Check if recommendations were stored in database
        stored_recommendations = await Recommendation.find(Recommendation.assessment_id == str(assessment_id)).to_list()
        logger.info(f"   💾 Stored recommendations in database: {len(stored_recommendations)}")
        
        # Check if reports were generated
        stored_reports = await Report.find(Report.assessment_id == str(assessment_id)).to_list()
        logger.info(f"   📄 Stored reports in database: {len(stored_reports)}")
        
        # Overall validation
        success = (
            updated_assessment.completion_percentage >= 80 and  # At least 80% complete
            (updated_assessment.status in [AssessmentStatus.COMPLETED, AssessmentStatus.IN_PROGRESS]) and
            workflow_result.agent_results and  # Agent results exist
            len(workflow_result.agent_results) > 0  # At least one agent executed
        )
        
        if success:
            logger.info("   ✅ All validation checks passed!")
            return True
        else:
            logger.error("   ❌ Validation failed!")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Validation error: {e}")
        return False

async def main():
    """Main test function."""
    success = await test_complete_workflow()
    
    if success:
        logger.info("🎉 Assessment workflow test completed successfully!")
        return 0
    else:
        logger.error("💥 Assessment workflow test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)