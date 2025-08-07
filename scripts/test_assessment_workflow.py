#!/usr/bin/env python3
"""
Test script for the complete assessment workflow.

This script tests the assessment submission and processing workflow
to ensure everything works correctly from start to finish.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from infra_mind.models.assessment import Assessment
from infra_mind.workflows.base import WorkflowState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_test_assessment() -> Assessment:
    """Create a test assessment for workflow testing."""
    logger.info("Creating test assessment...")
    
    # Create a mock assessment object with realistic data
    class MockAssessment:
        def __init__(self):
            self.id = "test_assessment_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            self.status = "draft"
            self.completion_percentage = 0.0
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.completed_at = None
            self.recommendations_generated = False
            self.reports_generated = False
            self.metadata = {}
            
            # Business requirements
            self.business_requirements = {
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "25k-100k",
                "timeline": "6-12 months",
                "compliance_needs": ["SOC2", "GDPR"],
                "business_goals": ["cost_optimization", "scalability", "security"]
            }
            
            # Technical requirements
            self.technical_requirements = {
                "current_infrastructure": "hybrid_cloud",
                "workload_types": ["web_application", "data_processing"],
                "performance_requirements": {"api_latency": "< 200ms", "throughput": "> 1000 rps"},
                "scalability_needs": {"auto_scaling": True, "global_presence": False},
                "security_requirements": {"encryption": True, "access_control": True},
                "integration_requirements": {"third_party_apis": True, "database_integration": True}
            }
            
            # Progress tracking
            self.progress = {
                "current_step": "created",
                "completed_steps": ["created"],
                "total_steps": 5,
                "progress_percentage": 0.0
            }
        
        async def save(self):
            """Mock save method."""
            logger.info(f"Saving assessment {self.id} with status {self.status}")
            return self
    
    return MockAssessment()


async def test_assessment_workflow():
    """Test the complete assessment workflow."""
    logger.info("Starting assessment workflow test...")
    
    try:
        # Create test assessment
        assessment = await create_test_assessment()
        logger.info(f"Created test assessment: {assessment.id}")
        
        # Create workflow instance
        workflow = AssessmentWorkflow()
        
        # Execute workflow
        logger.info("Executing assessment workflow...")
        result = await workflow.execute_workflow(
            workflow_id="assessment_workflow",
            assessment=assessment,
            context={"test_mode": True}
        )
        
        # Verify results
        logger.info("Verifying workflow results...")
        logger.info(f"Workflow Status: {result.status}")
        logger.info(f"Execution Time: {result.execution_time:.2f}s" if result.execution_time else "N/A")
        logger.info(f"Agent Results: {len(result.agent_results)}")
        logger.info(f"Node Count: {result.node_count}")
        logger.info(f"Completed Nodes: {result.completed_nodes}")
        logger.info(f"Failed Nodes: {result.failed_nodes}")
        
        if result.error:
            logger.error(f"Workflow Error: {result.error}")
        
        # Display agent results summary
        if result.agent_results:
            logger.info("\n=== Agent Results Summary ===")
            for agent_name, agent_result in result.agent_results.items():
                recommendations_count = len(agent_result.get("recommendations", []))
                confidence = agent_result.get("confidence_score", 0.0)
                logger.info(f"{agent_name}: {recommendations_count} recommendations, {confidence:.2f} confidence")
        
        # Display final data summary
        if result.final_data:
            logger.info("\n=== Final Data Summary ===")
            visualization_data = result.final_data.get("visualization_data")
            if visualization_data:
                logger.info(f"Visualization Data Available: {len(visualization_data.get('assessment_results', []))} categories")
                logger.info(f"Overall Score: {visualization_data.get('overall_score', 'N/A')}")
            
            reports_generated = result.final_data.get("reports_generated", False)
            reports_count = result.final_data.get("reports_count", 0)
            logger.info(f"Reports Generated: {reports_generated} ({reports_count} reports)")
        
        # Test success/failure
        if result.status == "completed":
            logger.info("\n✅ Assessment workflow test PASSED!")
            return True
        else:
            logger.error(f"\n❌ Assessment workflow test FAILED with status: {result.status}")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Assessment workflow test FAILED with exception: {e}")
        logger.exception("Full exception details:")
        return False


async def test_visualization_data_generation():
    """Test the visualization data generation specifically."""
    logger.info("\n=== Testing Visualization Data Generation ===")
    
    try:
        # Create workflow and mock state
        workflow = AssessmentWorkflow()
        
        # Create mock state with agent results
        mock_state = WorkflowState(
            workflow_id="test_viz",
            assessment_id="test_assessment"
        )
        
        # Add mock agent results
        mock_state.agent_results = {
            "cto_agent": {
                "recommendations": [
                    {"title": "Cloud Strategy", "category": "strategic", "priority": "high"}
                ],
                "confidence_score": 0.85
            },
            "cloud_engineer_agent": {
                "recommendations": [
                    {"title": "Architecture Design", "category": "technical", "priority": "high"}
                ],
                "confidence_score": 0.82
            },
            "compliance_agent": {
                "recommendations": [
                    {"title": "Security Framework", "category": "security", "priority": "high"}
                ],
                "confidence_score": 0.88
            }
        }
        
        # Generate visualization data
        viz_data = await workflow._generate_visualization_data(mock_state)
        
        # Verify structure
        assert "assessment_results" in viz_data
        assert "overall_score" in viz_data
        assert "recommendations_count" in viz_data
        
        logger.info(f"Generated visualization data with {len(viz_data['assessment_results'])} categories")
        logger.info(f"Overall score: {viz_data['overall_score']}")
        logger.info(f"Recommendations count: {viz_data['recommendations_count']}")
        
        logger.info("✅ Visualization data generation test PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visualization data generation test FAILED: {e}")
        logger.exception("Full exception details:")
        return False


async def main():
    """Main test function."""
    logger.info("=== Assessment Workflow Test Suite ===")
    
    # Run tests
    test_results = []
    
    # Test 1: Complete workflow
    logger.info("\n1. Testing complete assessment workflow...")
    result1 = await test_assessment_workflow()
    test_results.append(("Complete Workflow", result1))
    
    # Test 2: Visualization data generation
    logger.info("\n2. Testing visualization data generation...")
    result2 = await test_visualization_data_generation()
    test_results.append(("Visualization Data", result2))
    
    # Summary
    logger.info("\n=== Test Results Summary ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests PASSED! The assessment workflow is working correctly.")
        return 0
    else:
        logger.error("💥 Some tests FAILED. Please check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)