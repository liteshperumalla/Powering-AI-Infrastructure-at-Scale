"""
Assessment Background Tasks

Celery tasks for processing infrastructure assessments asynchronously.
Enables instant API responses while workflows execute in background workers.

Key Features:
- Non-blocking assessment execution
- Progress tracking and updates
- Automatic retry on failure
- Result persistence
- Fault tolerance
"""

import asyncio
from typing import Dict, Any, Optional
from celery import Task
from loguru import logger
from datetime import datetime

from .celery_app import celery_app
from ..workflows.parallel_assessment_workflow import ParallelAssessmentWorkflow
from ..models.assessment import Assessment
from beanie import PydanticObjectId


class AssessmentTask(Task):
    """
    Base class for assessment tasks with progress tracking.

    Provides:
    - Progress updates during execution
    - Error handling and retries
    - Result persistence
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Assessment task {task_id} failed: {exc}")
        # Could send notifications, update database, etc.

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Assessment task {task_id} completed successfully")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Assessment task {task_id} retrying due to: {exc}")


@celery_app.task(
    bind=True,
    base=AssessmentTask,
    name="process_assessment",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_assessment(self, assessment_id: str) -> Dict[str, Any]:
    """
    Process an infrastructure assessment in the background.

    Args:
        assessment_id: Assessment ID to process

    Returns:
        Dict with assessment results

    Raises:
        Exception: On processing failure (triggers retry)
    """
    logger.info(f"🚀 Starting background assessment processing: {assessment_id}")

    # Update task state to indicate we're starting
    self.update_state(
        state="STARTED",
        meta={
            "assessment_id": assessment_id,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0
        }
    )

    try:
        # Run async workflow in event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(_execute_assessment_workflow(
            assessment_id=assessment_id,
            task_instance=self
        ))

        logger.info(f"✅ Assessment {assessment_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"❌ Assessment {assessment_id} failed: {e}")

        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={
                "assessment_id": assessment_id,
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )

        # Re-raise to trigger retry mechanism
        raise


async def _execute_assessment_workflow(
    assessment_id: str,
    task_instance: Task
) -> Dict[str, Any]:
    """
    Execute the assessment workflow asynchronously.

    Args:
        assessment_id: Assessment ID
        task_instance: Celery task instance for progress updates

    Returns:
        Assessment results
    """
    # Fetch assessment from database
    assessment = await Assessment.get(PydanticObjectId(assessment_id))

    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Update progress: Starting
    task_instance.update_state(
        state="PROGRESS",
        meta={
            "assessment_id": assessment_id,
            "current_step": "Initializing workflow",
            "progress": 5
        }
    )

    # Create workflow instance
    workflow = ParallelAssessmentWorkflow()

    # Define progress callback
    async def progress_callback(step: str, progress: float, message: str = ""):
        """Update task progress during workflow execution."""
        task_instance.update_state(
            state="PROGRESS",
            meta={
                "assessment_id": assessment_id,
                "current_step": step,
                "progress": progress,
                "message": message,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        logger.info(f"📊 Assessment {assessment_id}: {step} - {progress}%")

    # Execute workflow with progress tracking
    try:
        # Update progress: Executing agents
        await progress_callback("Executing AI agents", 10)

        # Execute the workflow
        workflow_result = await workflow.execute(assessment)

        # Update progress: Processing results
        await progress_callback("Processing results", 90)

        # Update assessment status
        assessment.status = "completed"
        assessment.completed_at = datetime.utcnow()
        await assessment.save()

        # Update progress: Complete
        await progress_callback("Completed", 100)

        return {
            "assessment_id": assessment_id,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "results": workflow_result
        }

    except Exception as e:
        # Update assessment with error
        assessment.status = "failed"
        assessment.metadata = assessment.metadata or {}
        assessment.metadata["error"] = str(e)
        await assessment.save()

        raise


@celery_app.task(
    bind=True,
    name="generate_assessment_recommendations",
    max_retries=2
)
def generate_assessment_recommendations(self, assessment_id: str) -> Dict[str, Any]:
    """
    Generate recommendations for an assessment (can be called separately).

    Args:
        assessment_id: Assessment ID

    Returns:
        Recommendations results
    """
    logger.info(f"🎯 Generating recommendations for assessment: {assessment_id}")

    self.update_state(
        state="STARTED",
        meta={"assessment_id": assessment_id, "progress": 0}
    )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(_generate_recommendations(
            assessment_id=assessment_id,
            task_instance=self
        ))

        return result

    except Exception as e:
        logger.error(f"❌ Recommendation generation failed: {e}")
        raise


async def _generate_recommendations(
    assessment_id: str,
    task_instance: Task
) -> Dict[str, Any]:
    """Generate recommendations asynchronously."""
    from ..api.endpoints.assessments import generate_orchestrated_recommendations

    assessment = await Assessment.get(PydanticObjectId(assessment_id))

    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    task_instance.update_state(
        state="PROGRESS",
        meta={"assessment_id": assessment_id, "progress": 50}
    )

    # Generate recommendations
    await generate_orchestrated_recommendations(assessment)

    task_instance.update_state(
        state="PROGRESS",
        meta={"assessment_id": assessment_id, "progress": 100}
    )

    return {
        "assessment_id": assessment_id,
        "status": "completed",
        "recommendations_generated": True
    }


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Periodic task to clean up old task results from Redis.

    Run this with celery beat scheduler:
    celery -A infra_mind.tasks beat --loglevel=info
    """
    logger.info("🧹 Cleaning up old task results")

    # Celery automatically expires results after result_expires time (24h)
    # This task is just for any additional cleanup needed

    return {"status": "cleanup_completed", "timestamp": datetime.utcnow().isoformat()}
