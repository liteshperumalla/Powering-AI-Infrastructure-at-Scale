"""
Task Status API Endpoints

Provides endpoints to check status and results of background Celery tasks.

Key Features:
- Check task status (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE)
- Get task results
- Cancel running tasks
- List all tasks for a user
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from loguru import logger
from celery.result import AsyncResult

from ...tasks.celery_app import celery_app
from ..endpoints.auth import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status and progress of a background task.

    Returns:
        - state: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY
        - info: Task metadata (progress, current_step, etc.)
        - result: Final result if task completed

    Example response:
    {
        "task_id": "abc-123",
        "state": "PROGRESS",
        "info": {
            "assessment_id": "xyz-789",
            "current_step": "Executing AI agents",
            "progress": 45,
            "message": "Processing..."
        }
    }
    """
    try:
        # Get task result object
        task = AsyncResult(task_id, app=celery_app)

        # Build response
        response = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),  # True if task completed
            "successful": task.successful() if task.ready() else None,
            "failed": task.failed() if task.ready() else None
        }

        # Add task info based on state
        if task.state == "PENDING":
            response["info"] = {
                "message": "Task is waiting to be executed"
            }
        elif task.state == "STARTED":
            response["info"] = task.info or {}
        elif task.state == "PROGRESS":
            response["info"] = task.info or {}
        elif task.state == "SUCCESS":
            response["result"] = task.result
            response["info"] = task.info or {}
        elif task.state == "FAILURE":
            response["error"] = str(task.info)
            response["traceback"] = task.traceback
        elif task.state == "RETRY":
            response["info"] = {
                "message": "Task is retrying after failure",
                "retry_count": task.info.get("retry_count") if task.info else 0
            }

        logger.info(f"Task status check: {task_id} -> {task.state}")
        return response

    except Exception as e:
        logger.error(f"Error checking task status {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the result of a completed task.

    Returns:
        Task result if completed, error if task not ready

    Raises:
        404: Task not found or not completed
        500: Task failed
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        if not task.ready():
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} is not completed yet. Current state: {task.state}"
            )

        if task.failed():
            raise HTTPException(
                status_code=500,
                detail=f"Task {task_id} failed: {str(task.info)}"
            )

        return {
            "task_id": task_id,
            "state": task.state,
            "result": task.result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task result: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running or pending task.

    Note: Tasks already executing may not stop immediately.
    The worker will mark the task as revoked and skip execution
    if it hasn't started yet.

    Returns:
        Cancellation status
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        # Revoke the task
        task.revoke(terminate=True, signal="SIGTERM")

        logger.info(f"Task {task_id} cancelled by user {current_user.email}")

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation requested. May take a moment to stop if already executing."
        }

    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get("/tasks")
async def list_tasks(
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    List recent tasks (limited functionality - Celery doesn't track all tasks by default).

    For production, consider using Flower (Celery monitoring tool):
    - Install: pip install flower
    - Run: celery -A infra_mind.tasks flower
    - Access: http://localhost:5555

    Returns:
        List of task IDs and states (if available)
    """
    try:
        # Note: This requires Celery result backend with extended results
        # For basic tracking, use Flower or Redis directly

        # Get active tasks from workers
        inspect = celery_app.control.inspect()

        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}

        all_tasks = []

        # Collect active tasks
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "task_id": task["id"],
                    "name": task["name"],
                    "state": "ACTIVE",
                    "worker": worker,
                    "args": task.get("args"),
                })

        # Collect scheduled tasks
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "task_id": task["request"]["id"],
                    "name": task["request"]["name"],
                    "state": "SCHEDULED",
                    "worker": worker
                })

        return {
            "tasks": all_tasks[:limit],
            "total": len(all_tasks),
            "note": "For comprehensive task monitoring, use Flower at http://localhost:5555"
        }

    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.get("/workers/status")
async def get_worker_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get status of all Celery workers.

    Returns:
        Worker health, active tasks, stats
    """
    try:
        inspect = celery_app.control.inspect()

        # Get worker stats
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        registered = inspect.registered() or {}

        workers_info = []

        for worker_name in stats.keys():
            worker_stats = stats[worker_name]
            workers_info.append({
                "name": worker_name,
                "status": "online",
                "pool": worker_stats.get("pool", {}).get("implementation"),
                "max_concurrency": worker_stats.get("pool", {}).get("max-concurrency"),
                "active_tasks": len(active.get(worker_name, [])),
                "registered_tasks": len(registered.get(worker_name, []))
            })

        return {
            "workers": workers_info,
            "total_workers": len(workers_info),
            "total_active_tasks": sum(w["active_tasks"] for w in workers_info)
        }

    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get worker status: {str(e)}"
        )
