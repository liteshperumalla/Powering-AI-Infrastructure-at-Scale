#!/usr/bin/env python3
"""
Test script for assessment progress tracking.

This script tests the progress tracking system to ensure it updates correctly
throughout the assessment workflow.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_test_assessment() -> Assessment:
    """Create a test assessment for progress tracking testing."""
    logger.info("Creating test assessment...")
    
    class MockAssessment:
        def __init__(self):
            self.id = "progress_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            self.status = "draft"
            self.completion_percentage = 0.0
            self.created_at = datetime.utcnow() 
            self.updated_at = datetime.utcnow()
            self.completed_at = None
            self.recommendations_generated = False
            self.reports_generated = True
            self.metadata = {}
            
            # Progress tracking
            self.progress = {
                "current_step": "created",
                "completed_steps": ["created"],
                "total_steps": 5,
                "progress_percentage": 0.0
            }
            
            # Business requirements
            self.business_requirements = {
                "company_size": "small",
                "industry": "technology", 
                "budget_range": "10k-25k",
                "timeline": "3-6 months"
            }
            
            # Technical requirements
            self.technical_requirements = {
                "current_infrastructure": "on_premise",
                "workload_types": ["web_application"],
                "performance_requirements": {"api_latency": "< 500ms"},
                "scalability_needs": {"auto_scaling": False}
            }
        
        async def save(self):
            """Mock save method that logs progress updates."""
            logger.info(f"📊 Progress Update: {self.progress['progress_percentage']:.1f}% - {self.progress['current_step']} - {self.progress.get('message', 'No message')}")
            return self
    
    return MockAssessment()


async def test_progress_tracking():
    """Test the progress tracking throughout the workflow."""
    logger.info("🚀 Starting progress tracking test...")
    
    try:
        # Create test assessment
        assessment = await create_test_assessment()
        logger.info(f"Created test assessment: {assessment.id}")
        
        # Track progress updates
        progress_updates = []
        
        # Store original save method to capture progress updates
        original_save = assessment.save
        
        async def capture_progress_save():
            progress_updates.append({
                "timestamp": datetime.now(),
                "step": assessment.progress["current_step"],
                "percentage": assessment.progress["progress_percentage"], 
                "completed_steps": assessment.progress["completed_steps"].copy(),
                "message": assessment.progress.get("message", "")
            })
            return await original_save()
        
        assessment.save = capture_progress_save
        
        # Create workflow instance
        workflow = AssessmentWorkflow()
        
        # Execute workflow and capture progress
        logger.info("▶️  Executing assessment workflow...")
        result = await workflow.execute_workflow(
            workflow_id="progress_test_workflow",
            assessment=assessment,
            context={"test_mode": True}
        )
        
        # Analyze progress tracking
        logger.info("\n📈 Progress Tracking Analysis")
        logger.info("=" * 50)
        
        for i, update in enumerate(progress_updates):
            logger.info(
                f"{i+1:2d}. {update['timestamp'].strftime('%H:%M:%S')} | "
                f"{update['percentage']:5.1f}% | "
                f"{update['step']:15s} | "
                f"Steps: {len(update['completed_steps'])} | "
                f"{update['message']}"
            )
        
        # Verify progress tracking requirements
        logger.info("\n✅ Progress Tracking Verification")
        logger.info("=" * 50)
        
        checks = [
            ("Progress updates captured", len(progress_updates) > 0),
            ("Started at 0%", progress_updates[0]["percentage"] == 0.0),
            ("Ended at 100%", progress_updates[-1]["percentage"] == 100.0),
            ("Correct step sequence", verify_step_sequence(progress_updates)),
            ("Progressive percentage increase", verify_progressive_increase(progress_updates)),
            ("All steps completed", verify_all_steps_completed(progress_updates[-1]))
        ]
        
        passed_checks = 0
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} | {check_name}")
            if passed:
                passed_checks += 1
        
        # Final results
        logger.info(f"\n📊 Final Results")
        logger.info("=" * 50)
        logger.info(f"Workflow Status: {result.status}")
        logger.info(f"Progress Updates: {len(progress_updates)}")
        logger.info(f"Final Progress: {progress_updates[-1]['percentage']:.1f}%")
        logger.info(f"Final Step: {progress_updates[-1]['step']}")
        logger.info(f"Checks Passed: {passed_checks}/{len(checks)}")
        
        if passed_checks == len(checks):
            logger.info("🎉 All progress tracking tests PASSED!")
            return True
        else:
            logger.error(f"💥 {len(checks) - passed_checks} progress tracking tests FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Progress tracking test FAILED with exception: {e}")
        logger.exception("Full exception details:")
        return False


def verify_step_sequence(progress_updates):
    """Verify that steps follow the correct sequence."""
    expected_sequence = ["created", "analysis", "recommendations", "reports", "visualization"]
    
    steps_seen = []
    for update in progress_updates:
        if update["step"] not in steps_seen:
            steps_seen.append(update["step"])
    
    # Check if steps appear in correct order (allowing for some flexibility)
    for i, expected_step in enumerate(expected_sequence):
        if expected_step in steps_seen:
            actual_index = steps_seen.index(expected_step)
            if actual_index != i and expected_step != "created":  # created can appear multiple times
                return False
    
    return True


def verify_progressive_increase(progress_updates):
    """Verify that progress percentage generally increases."""
    if len(progress_updates) < 2:
        return False
    
    # Allow for small decreases but overall trend should be increasing
    significant_decreases = 0
    for i in range(1, len(progress_updates)):
        if progress_updates[i]["percentage"] < progress_updates[i-1]["percentage"] - 5:
            significant_decreases += 1
    
    # Allow up to 1 significant decrease (e.g., during step transitions)
    return significant_decreases <= 1


def verify_all_steps_completed(final_update):
    """Verify that all expected steps are marked as completed."""
    expected_steps = {"created", "analysis", "recommendations", "reports", "visualization"}
    completed_steps = set(final_update["completed_steps"])
    
    return expected_steps.issubset(completed_steps)


async def main():
    """Main test function."""
    logger.info("🧪 Assessment Progress Tracking Test Suite")
    logger.info("=" * 60)
    
    # Run progress tracking test
    success = await test_progress_tracking()
    
    if success:
        logger.info("\n🎯 Progress tracking system is working correctly!")
        return 0
    else:
        logger.error("\n🚨 Progress tracking system has issues that need to be fixed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)