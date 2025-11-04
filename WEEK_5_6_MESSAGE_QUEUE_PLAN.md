# Week 5-6: Message Queue (Celery) Implementation

**Date:** November 4, 2025
**Phase:** Phase 1 - Final Component
**Expected Impact:** Instant API responses, fault-tolerant processing, unlimited horizontal scaling

---

## 📋 Executive Summary

This is the **final component of Phase 1**, completing the transformation from a prototype to a production-ready, horizontally scalable system. Implementing a message queue with Celery will:

1. **Instant API responses** - Return immediately instead of blocking for 10+ minutes
2. **Fault-tolerant processing** - Tasks survive server restarts and failures
3. **Automatic retries** - Transient failures automatically handled
4. **Horizontal scaling** - Add/remove workers dynamically based on load
5. **Task monitoring** - Track task progress, failures, and performance

### Current Problem:
```python
# BLOCKING - User waits 10-15 minutes!
@router.post("/assessments/{id}/analyze")
async def analyze(id: str):
    workflow = ParallelAssessmentWorkflow()
    result = await workflow.execute(assessment)  # Blocks for 10+ minutes!
    return result
```

### After Celery:
```python
# INSTANT - Returns in < 200ms!
@router.post("/assessments/{id}/analyze")
async def analyze(id: str):
    task = process_assessment.delay(id)  # Queue task, return immediately
    return {"task_id": task.id, "status": "queued"}  # < 200ms response!
```

---

## 🎯 Key Objectives

1. ✅ Implement Celery with Redis backend
2. ✅ Convert long-running operations to background tasks
3. ✅ Add task monitoring and progress tracking
4. ✅ Deploy Celery workers with horizontal scaling
5. ✅ Implement automatic retry logic
6. ✅ Add task result persistence and retrieval

---

## 🏗️ Architecture Design

### Current Architecture (Blocking):
```
User Request → API Endpoint → Workflow Execution (10+ min) → Response
                    ↑
                 BLOCKS HERE
                User waits...
```

### New Architecture (Non-Blocking):
```
User Request → API Endpoint → Queue Task → Immediate Response (< 200ms)
                                    ↓
                            Celery Worker Pool
                                    ↓
                            Background Execution
                                    ↓
                            Task Result in Redis
                                    ↓
                            User polls for status
```

### Components:

**1. Celery Workers** (Background Processors)
- Consume tasks from Redis queue
- Execute workflows in background
- Report progress and results
- Automatic failover and retry

**2. Redis Queue** (Message Broker)
- Task queue (pending tasks)
- Result backend (completed tasks)
- Task status tracking
- Progress updates

**3. API Endpoints** (Non-Blocking)
- Queue tasks (instant response)
- Check task status
- Retrieve task results
- Cancel running tasks

---

## 📂 File Structure

```
src/infra_mind/
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py              # Celery application configuration
│   ├── assessment_tasks.py        # Assessment processing tasks
│   ├── report_tasks.py            # Report generation tasks
│   ├── recommendation_tasks.py    # Recommendation tasks
│   └── monitoring.py              # Task monitoring utilities
│
├── api/endpoints/
│   ├── task_status.py             # Task status endpoints (NEW)
│   └── assessments.py             # Updated with task queueing
│
└── core/
    └── task_config.py              # Task configuration

docker-compose.yml                  # Add Celery worker service
requirements.txt                    # Add Celery dependencies
```

---

## 🔧 Implementation Plan

### Day 1-2: Celery Setup and Configuration

#### Step 1: Install Celery
```bash
# Add to requirements.txt
celery[redis]==5.3.4
flower==2.0.1  # Web-based monitoring tool
```

#### Step 2: Create Celery Application
**File:** `src/infra_mind/tasks/celery_app.py`

```python
"""
Celery application configuration for Infra Mind.

Features:
- Redis broker and result backend
- Task routing by priority
- Automatic retries with exponential backoff
- Result persistence for 24 hours
- Worker prefetch optimization
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue, Exchange
import logging
import os

logger = logging.getLogger(__name__)

# Celery application
celery_app = Celery(
    'infra_mind',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# Celery configuration
celery_app.conf.update(
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task result backend
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    result_expires=86400,  # 24 hours
    result_persistent=True,

    # Task routing
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('assessments', Exchange('assessments'), routing_key='assessments'),
        Queue('reports', Exchange('reports'), routing_key='reports'),
        Queue('priority', Exchange('priority'), routing_key='priority'),
    ),

    # Task execution settings
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch 1 task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 3},
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # 10 minutes max
    task_retry_jitter=True,  # Add random jitter
)

# Task routes (which queue for which task)
celery_app.conf.task_routes = {
    'tasks.assessment_tasks.*': {'queue': 'assessments'},
    'tasks.report_tasks.*': {'queue': 'reports'},
    'tasks.recommendation_tasks.*': {'queue': 'default'},
}


# Task lifecycle hooks
@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Called before task execution."""
    logger.info(f"Task started: {task.name} (id: {task_id})")


@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    """Called after task execution."""
    logger.info(f"Task completed: {task.name} (id: {task_id})")


@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    """Called when task fails."""
    logger.error(f"Task failed: {task_id}, exception: {exception}")


# Auto-discover tasks in tasks/ directory
celery_app.autodiscover_tasks(['src.infra_mind.tasks'])

logger.info("✅ Celery application initialized")
```

#### Step 3: Create Assessment Background Task
**File:** `src/infra_mind/tasks/assessment_tasks.py`

```python
"""
Background tasks for assessment processing.

All long-running assessment operations are handled here.
Tasks are automatically retried on failure and results are persisted.
"""

import logging
from typing import Dict, Any
from celery import Task
from .celery_app import celery_app

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """
    Base task with callbacks for progress updates.

    Supports:
    - Progress updates via state
    - Automatic error handling
    - Result persistence
    """

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} succeeded with result: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying due to: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.assessment_tasks.process_assessment',
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True
)
async def process_assessment(self, assessment_id: str) -> Dict[str, Any]:
    """
    Process an assessment in the background.

    This task:
    1. Loads assessment from database
    2. Executes parallel workflow (1-2 minutes)
    3. Saves results to database
    4. Returns summary

    Args:
        self: Celery task instance
        assessment_id: Assessment ID to process

    Returns:
        Dict with task result summary

    Raises:
        Exception: Any error during processing (will retry)
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={
                'current': 0,
                'total': 100,
                'status': 'Loading assessment...'
            }
        )

        # Import here to avoid circular dependencies
        from ..models.assessment import Assessment
        from ..workflows.parallel_assessment_workflow import ParallelAssessmentWorkflow
        from ..core.database import get_database

        # Load assessment
        db = await get_database()
        assessment = await Assessment.get(assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': 'Starting workflow execution...'
            }
        )

        # Execute workflow (parallel execution, 1-2 minutes)
        workflow = ParallelAssessmentWorkflow()

        # Execute with progress callbacks
        result = await workflow.execute(
            assessment,
            context={
                'task_id': self.request.id,
                'user_id': str(assessment.user_id)
            }
        )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 90,
                'total': 100,
                'status': 'Saving results...'
            }
        )

        # Update assessment with results
        assessment.status = "completed"
        assessment.workflow_result = result.data
        assessment.execution_metrics = workflow.get_execution_metrics()
        await assessment.save()

        # Return success
        return {
            'assessment_id': assessment_id,
            'status': 'success',
            'execution_time': workflow.execution_metrics['total_time'],
            'agents_completed': workflow.execution_metrics['completed_agents'],
            'agents_failed': workflow.execution_metrics['failed_agents'],
            'success_rate': workflow.execution_metrics['success_rate']
        }

    except Exception as e:
        logger.error(f"Assessment processing failed: {e}", exc_info=True)

        # Update task state to FAILURE
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'status': 'Failed to process assessment'
            }
        )

        # Mark assessment as failed
        try:
            assessment.status = "failed"
            assessment.error = str(e)
            await assessment.save()
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")

        # Retry with exponential backoff
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name='tasks.assessment_tasks.generate_recommendations',
    max_retries=2
)
async def generate_recommendations(self, assessment_id: str) -> Dict[str, Any]:
    """Generate recommendations for a completed assessment."""
    # Implementation similar to process_assessment
    pass


@celery_app.task(
    bind=True,
    name='tasks.assessment_tasks.generate_report',
    max_retries=2
)
async def generate_report(
    self,
    assessment_id: str,
    report_type: str = "executive"
) -> Dict[str, Any]:
    """Generate report for a completed assessment."""
    # Implementation for report generation
    pass
```

---

### Day 3-4: API Integration

#### Step 1: Create Task Status Endpoints
**File:** `src/infra_mind/api/endpoints/task_status.py` (NEW)

```python
"""
Task status and management endpoints.

Allows users to:
- Check task status
- Get task results
- Cancel running tasks
- List user's tasks
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from celery.result import AsyncResult
from datetime import datetime, timezone

from ...tasks.celery_app import celery_app
from ...models.user import User
from ..endpoints.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Task Management"])


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a background task.

    Returns:
    - state: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
    - result: Task result (if completed)
    - progress: Progress info (if in progress)
    """
    task = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "state": task.state,
        "current": 0,
        "total": 100,
        "status": "",
        "result": None
    }

    if task.state == 'PENDING':
        response['status'] = 'Task is waiting to be processed...'

    elif task.state == 'STARTED':
        response['status'] = 'Task is being processed...'
        if task.info:
            response.update(task.info)

    elif task.state == 'PROGRESS':
        response.update(task.info)

    elif task.state == 'SUCCESS':
        response['status'] = 'Task completed successfully'
        response['current'] = 100
        response['result'] = task.result

    elif task.state == 'FAILURE':
        response['status'] = 'Task failed'
        response['error'] = str(task.info)

    return response


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running task.

    Note: Task may not stop immediately if already executing.
    """
    task = AsyncResult(task_id, app=celery_app)

    # Revoke task (terminate=True to forcefully stop)
    celery_app.control.revoke(task_id, terminate=True)

    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancellation requested"
    }


@router.get("/")
async def list_user_tasks(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    List user's recent tasks.

    Returns last 50 tasks by default.
    """
    # Get active tasks from Celery
    inspect = celery_app.control.inspect()
    active = inspect.active()
    scheduled = inspect.scheduled()
    reserved = inspect.reserved()

    # Combine all tasks
    all_tasks = []

    if active:
        for worker, tasks in active.items():
            all_tasks.extend(tasks)

    if scheduled:
        for worker, tasks in scheduled.items():
            all_tasks.extend(tasks)

    if reserved:
        for worker, tasks in reserved.items():
            all_tasks.extend(tasks)

    # Filter by user (if task has user_id in args/kwargs)
    # This is simplified - in production, maintain task-user mapping in database

    return {
        "total": len(all_tasks),
        "tasks": all_tasks[:limit]
    }
```

#### Step 2: Update Assessment Endpoints
**File:** `src/infra_mind/api/endpoints/assessments.py` (MODIFY)

```python
# Add import
from ...tasks.assessment_tasks import process_assessment

# Update analyze endpoint
@router.post("/{id}/analyze")
async def analyze_assessment(
    id: str,
    background: bool = True,  # NEW: Option for background processing
    current_user: User = Depends(get_current_user)
):
    """
    Start assessment analysis.

    Args:
        id: Assessment ID
        background: If True, queue as background task (instant response)
                   If False, process synchronously (blocks)

    Returns:
        If background=True: {"task_id": "...", "status": "queued"}
        If background=False: Full workflow result
    """
    assessment = await Assessment.get(id)

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if background:
        # Queue background task (INSTANT RESPONSE!)
        task = process_assessment.delay(str(assessment.id))

        # Update assessment status
        assessment.status = "queued"
        assessment.task_id = task.id
        await assessment.save()

        return {
            "assessment_id": str(assessment.id),
            "task_id": task.id,
            "status": "queued",
            "message": "Assessment queued for processing",
            "check_status_url": f"/api/v1/tasks/{task.id}/status"
        }

    else:
        # Synchronous processing (BLOCKS - OLD WAY)
        workflow = ParallelAssessmentWorkflow()
        result = await workflow.execute(assessment)

        assessment.status = "completed"
        await assessment.save()

        return result
```

---

### Day 5: Docker Integration

#### Update docker-compose.yml
```yaml
# Add Celery worker service
celery-worker:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A src.infra_mind.tasks.celery_app worker --loglevel=info --concurrency=4
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
    CELERY_RESULT_BACKEND: redis://redis:6379/1
    INFRA_MIND_MONGODB_URL: mongodb://admin:password@mongodb:27017/infra_mind?authSource=admin
    # Copy all API environment variables
  depends_on:
    - redis
    - mongodb
  deploy:
    replicas: 3  # 3 worker instances for horizontal scaling
    resources:
      limits:
        cpus: '2.0'
        memory: 2G

# Add Flower (task monitoring UI)
flower:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A src.infra_mind.tasks.celery_app flower --port=5555
  ports:
    - "5555:5555"
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
    CELERY_RESULT_BACKEND: redis://redis:6379/1
  depends_on:
    - redis
    - celery-worker
```

---

## 📊 Expected Improvements

| Metric | Before Celery | After Celery | Improvement |
|--------|--------------|--------------|-------------|
| **API Response Time** | 10-15 min (blocking) | < 200ms | **4500x faster** |
| **User Experience** | Poor (long wait) | Excellent (instant feedback) | Dramatic |
| **Concurrent Assessments** | ~10 (limited by API workers) | Unlimited | Infinite scale |
| **Fault Tolerance** | ❌ Lost on restart | ✅ Survives restarts | Production-grade |
| **Automatic Retries** | ❌ Manual only | ✅ Automatic (3x) | Reliable |
| **Task Monitoring** | ❌ None | ✅ Real-time dashboard | Full visibility |
| **Worker Scaling** | ❌ Not possible | ✅ Add/remove dynamically | Elastic |

---

## 🎯 Success Criteria

**Functionality:**
- [ ] Celery workers start successfully
- [ ] Tasks queue and execute in background
- [ ] API returns instantly (< 200ms)
- [ ] Task status endpoint works
- [ ] Task results retrievable
- [ ] Automatic retries working

**Performance:**
- [ ] 100+ concurrent tasks supported
- [ ] Task completion time same as before (1-2 min)
- [ ] Zero data loss on worker restart
- [ ] Flower monitoring UI accessible

**Scalability:**
- [ ] Can add workers dynamically
- [ ] Workers distribute load evenly
- [ ] System handles 1000+ queued tasks

---

## 📅 Timeline

**Week 5:**
- Day 1-2: Celery setup and configuration
- Day 3-4: API integration and testing
- Day 5: Docker integration and deployment

**Week 6:**
- Day 1-2: Load testing and optimization
- Day 3-4: Monitoring and alerting setup
- Day 5: Production deployment and validation

---

**Document Version:** 1.0
**Status:** Planning Phase
**Target Completion:** Week 6 End
**Created By:** System Design Expert
**Date:** November 4, 2025

---

*Week 5-6 message queue implementation completes Phase 1, providing instant API responses and unlimited horizontal scaling capability.*
