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
    retry_jitter=True,
    ignore_result=False,  # We DO want results, but not state updates
    track_started=False   # Don't track intermediate states
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

    # Skip state updates to avoid Redis backend issues
    # State is tracked in MongoDB via assessment.progress field

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
        # Error state tracked in MongoDB, not Celery backend
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
    # Initialize Beanie if not already initialized (worker-safe)
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import init_beanie
        import os

        mongodb_url = os.getenv(
            "MONGODB_URL",
            "mongodb://admin:password@mongodb:27017/infra_mind?authSource=admin"
        )

        client = AsyncIOMotorClient(mongodb_url)

        # Import all models
        from ..models.recommendation import Recommendation
        from ..models.report import Report, ReportSection
        from ..models.user import User
        from ..models.experiment import Experiment

        # Initialize Beanie
        await init_beanie(
            database=client.infra_mind,
            document_models=[
                Assessment,
                Recommendation,
                Report,
                ReportSection,
                User,
                Experiment
            ]
        )
        logger.info("✅ Beanie initialized for workflow execution")
    except Exception as e:
        logger.warning(f"Beanie initialization (may already be initialized): {e}")

    # Fetch assessment from database
    assessment = await Assessment.get(PydanticObjectId(assessment_id))

    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Progress tracked in MongoDB assessment.progress field
    logger.info(f"📊 Initializing workflow for assessment {assessment_id}")

    # Create workflow instance
    workflow = ParallelAssessmentWorkflow()

    # Define progress callback
    async def progress_callback(step: str, progress: float, message: str = ""):
        """Log workflow progress (state tracked in MongoDB)."""
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

        # Update both progress tracking fields
        assessment.completion_percentage = 100.0  # Top-level field used by API
        if hasattr(assessment, 'progress') and isinstance(assessment.progress, dict):
            assessment.progress['progress_percentage'] = 100.0  # Nested field for workflow tracking

        await assessment.save()

        # Dispatch report and recommendation generation tasks
        # These run as separate Celery tasks to avoid blocking
        try:
            from .report_tasks import generate_assessment_reports
            generate_assessment_reports.apply_async(
                args=[assessment_id],
                queue='reports',
                routing_key='report'
            )
            logger.info(f"📝 Dispatched report generation for assessment {assessment_id}")
        except Exception as e:
            logger.warning(f"Failed to dispatch report generation: {e}")

        try:
            generate_assessment_recommendations.apply_async(
                args=[assessment_id],
                queue='assessments',
                routing_key='assessment'
            )
            logger.info(f"💡 Dispatched recommendation generation for assessment {assessment_id}")
        except Exception as e:
            logger.warning(f"Failed to dispatch recommendation generation: {e}")

        # Update progress: Complete
        await progress_callback("Completed", 100)

        # Convert WorkflowResult to dict for JSON serialization
        workflow_data = workflow_result.final_data if hasattr(workflow_result, 'final_data') else {}

        return {
            "assessment_id": assessment_id,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "workflow_status": workflow_result.status.value if hasattr(workflow_result, 'status') else "completed",
            "execution_time": workflow_result.execution_time if hasattr(workflow_result, 'execution_time') else None,
            "results": workflow_data
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

    # Skip state updates to avoid Redis backend issues
    # self.update_state(
    #     state="STARTED",
    #     meta={"assessment_id": assessment_id, "progress": 0}
    # )

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

    # Skip state updates to avoid Redis backend issues
    # task_instance.update_state(
    #     state="PROGRESS",
    #     meta={"assessment_id": assessment_id, "progress": 50}
    # )

    # Generate recommendations
    await generate_orchestrated_recommendations(assessment)

    # Skip state updates to avoid Redis backend issues
    # task_instance.update_state(
    #     state="PROGRESS",
    #     meta={"assessment_id": assessment_id, "progress": 100}
    # )

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
