#!/usr/bin/env python3
"""
Pytest-friendly workflow execution regression test.

This requires access to the backing Mongo database plus the asynchronous
assessment workflow helpers. The test is skipped by default unless
RUN_WORKFLOW_EXECUTION_TESTS=1.
"""

import os
from typing import List

import pytest

from src.infra_mind.api.endpoints.assessments import (
    _execute_agent_analysis_step,
    _execute_optimization_step,
    _execute_report_generation_step,
)
from src.infra_mind.core.database import init_database
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report

RUN_WORKFLOW_EXECUTION_TESTS = os.getenv("RUN_WORKFLOW_EXECUTION_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_WORKFLOW_EXECUTION_TESTS,
    reason="Requires MongoDB plus seeded assessment data. "
    "Set RUN_WORKFLOW_EXECUTION_TESTS=1 to enable.",
)

ASSESSMENT_ID = os.getenv("TEST_WORKFLOW_ASSESSMENT_ID", "68ce016c047215025c4f87fe")


async def _get_recommendations(assessment_id: str) -> List[Recommendation]:
    """Helper to fetch recommendations for readability."""
    return await Recommendation.find(
        Recommendation.assessment_id == assessment_id
    ).to_list()


async def _get_reports(assessment_id: str) -> List[Report]:
    """Helper to fetch generated reports."""
    return await Report.find(Report.assessment_id == assessment_id).to_list()


@pytest.mark.asyncio
async def test_workflow_execution_generates_recommendations_and_reports() -> None:
    """Run the agent workflow and ensure it produces new artifacts."""
    await init_database()

    assessment = await Assessment.get(ASSESSMENT_ID)
    if not assessment:
        pytest.skip(f"Assessment {ASSESSMENT_ID} not found in database")

    initial_recs = await _get_recommendations(ASSESSMENT_ID)
    initial_reports = await _get_reports(ASSESSMENT_ID)

    await _execute_agent_analysis_step(assessment)
    await _execute_optimization_step(assessment)
    await _execute_report_generation_step(assessment)

    new_recs = await _get_recommendations(ASSESSMENT_ID)
    new_reports = await _get_reports(ASSESSMENT_ID)
    updated_assessment = await Assessment.get(ASSESSMENT_ID)

    assert len(new_recs) >= len(
        initial_recs
    ), "Optimization step should not reduce recommendation count"
    assert len(new_reports) >= len(
        initial_reports
    ), "Report generation step should not reduce report count"
    assert (
        updated_assessment.recommendations_generated
    ), "Assessment flag should mark recommendations as generated"
    assert (
        updated_assessment.report_generated
    ), "Assessment flag should mark report generation as complete"
