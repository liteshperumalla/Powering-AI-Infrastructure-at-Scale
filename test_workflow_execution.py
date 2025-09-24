#!/usr/bin/env python3
"""
Test script to verify workflow content generation functions work correctly.
"""

import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database
from infra_mind.models.assessment import Assessment
from infra_mind.models.recommendation import Recommendation
from infra_mind.models.report import Report

async def test_workflow_execution():
    """Test the workflow execution with actual content generation."""
    print("🧪 Starting workflow execution test...")

    # Initialize database connection
    await init_database()
    print("✅ Database initialized")

    # Get our test assessment
    assessment_id = "68ce016c047215025c4f87fe"
    assessment = await Assessment.get(assessment_id)

    if not assessment:
        print(f"❌ Assessment {assessment_id} not found")
        return

    print(f"✅ Found assessment: {assessment.title}")
    print(f"   Current status: {assessment.status}")
    print(f"   Progress: {assessment.workflow_progress.get('progress_percentage', 0)}%")

    # Check initial recommendations count
    initial_recs = await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()
    initial_reports = await Report.find(Report.assessment_id == assessment_id).to_list()

    print(f"📊 Initial state:")
    print(f"   Recommendations: {len(initial_recs)}")
    print(f"   Reports: {len(initial_reports)}")

    # Test each workflow execution function
    try:
        # Import the execution functions
        from infra_mind.api.endpoints.assessments import (
            _execute_agent_analysis_step,
            _execute_optimization_step,
            _execute_report_generation_step
        )

        print("\n🔄 Testing agent analysis step...")
        await _execute_agent_analysis_step(assessment)
        print("✅ Agent analysis step completed")

        print("\n🔄 Testing optimization step...")
        await _execute_optimization_step(assessment)
        print("✅ Optimization step completed")

        # Check if recommendations were created
        new_recs = await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()
        print(f"📊 Recommendations after optimization: {len(new_recs)}")

        print("\n🔄 Testing report generation step...")
        await _execute_report_generation_step(assessment)
        print("✅ Report generation step completed")

        # Check if reports were created
        new_reports = await Report.find(Report.assessment_id == assessment_id).to_list()
        print(f"📊 Reports after generation: {len(new_reports)}")

        # Final assessment state
        updated_assessment = await Assessment.get(assessment_id)
        print(f"\n🎯 Final assessment state:")
        print(f"   Recommendations generated: {updated_assessment.recommendations_generated}")
        print(f"   Report generated: {updated_assessment.report_generated}")

        if len(new_recs) > len(initial_recs):
            print(f"✅ SUCCESS: {len(new_recs) - len(initial_recs)} new recommendations created")
        else:
            print("❌ FAILURE: No new recommendations created")

        if len(new_reports) > len(initial_reports):
            print(f"✅ SUCCESS: {len(new_reports) - len(initial_reports)} new reports created")
        else:
            print("❌ FAILURE: No new reports created")

    except Exception as e:
        print(f"❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_execution())