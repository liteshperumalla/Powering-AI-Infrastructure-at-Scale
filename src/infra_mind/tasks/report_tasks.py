"""
Report Generation Background Tasks

Celery tasks for generating infrastructure reports asynchronously.
"""

import asyncio
from typing import Dict, Any
from celery import Task
from loguru import logger
from datetime import datetime

from .celery_app import celery_app
from ..models.assessment import Assessment
from beanie import PydanticObjectId


@celery_app.task(
    bind=True,
    name="generate_assessment_reports",
    max_retries=2,
    default_retry_delay=60
)
def generate_assessment_reports(self, assessment_id: str) -> Dict[str, Any]:
    """
    Generate reports for an assessment in the background.

    Args:
        assessment_id: Assessment ID

    Returns:
        Report generation results
    """
    logger.info(f"📄 Generating reports for assessment: {assessment_id}")

    self.update_state(
        state="STARTED",
        meta={"assessment_id": assessment_id, "progress": 0}
    )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(_generate_reports(
            assessment_id=assessment_id,
            task_instance=self
        ))

        return result

    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        raise


async def _generate_reports(
    assessment_id: str,
    task_instance: Task
) -> Dict[str, Any]:
    """Generate reports asynchronously."""
    from ..api.endpoints.assessments import generate_actual_reports

    assessment = await Assessment.get(PydanticObjectId(assessment_id))

    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    task_instance.update_state(
        state="PROGRESS",
        meta={"assessment_id": assessment_id, "progress": 30}
    )

    # Generate reports
    await generate_actual_reports(assessment)

    task_instance.update_state(
        state="PROGRESS",
        meta={"assessment_id": assessment_id, "progress": 100}
    )

    return {
        "assessment_id": assessment_id,
        "status": "completed",
        "reports_generated": True
    }
