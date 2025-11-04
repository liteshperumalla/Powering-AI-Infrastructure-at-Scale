"""
Celery Application Configuration

Configures Celery for background task processing with Redis backend.
Enables instant API responses and fault-tolerant, scalable processing.

Key Features:
- Redis as message broker and result backend
- Automatic task retries with exponential backoff
- Task result persistence (24 hours)
- Worker monitoring and health checks
- Horizontal scaling support
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery application
celery_app = Celery(
    "infra_mind",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "infra_mind.tasks.assessment_tasks",
        "infra_mind.tasks.report_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task result settings
    result_expires=86400,  # 24 hours
    result_extended=True,  # Store additional task info
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True
    },

    # Task retry settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue on worker crash
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Worker settings
    worker_prefetch_multiplier=4,  # Tasks to prefetch per worker
    worker_max_tasks_per_child=1000,  # Restart worker after N tasks (prevent memory leaks)
    worker_disable_rate_limits=False,

    # Task routing
    task_routes={
        "infra_mind.tasks.assessment_tasks.*": {
            "queue": "assessments",
            "routing_key": "assessment"
        },
        "infra_mind.tasks.report_tasks.*": {
            "queue": "reports",
            "routing_key": "report"
        }
    },

    # Queue definitions
    task_queues=(
        Queue("assessments", Exchange("assessments"), routing_key="assessment", priority=10),
        Queue("reports", Exchange("reports"), routing_key="report", priority=5),
        Queue("celery", Exchange("celery"), routing_key="celery", priority=1),  # Default queue
    ),

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Time limits
    task_soft_time_limit=600,  # 10 minutes soft limit
    task_time_limit=900,  # 15 minutes hard limit

    # Redis broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_transport_options={
        "visibility_timeout": 3600,  # 1 hour
        "fanout_prefix": True,
        "fanout_patterns": True
    }
)

# Task base class configuration
celery_app.Task.bind = True
celery_app.Task.track_started = True

# Health check task
@celery_app.task(name="health_check", bind=True)
def health_check(self):
    """Simple health check task for monitoring."""
    return {
        "status": "healthy",
        "worker_id": self.request.id,
        "queue": self.request.delivery_info.get("routing_key")
    }

if __name__ == "__main__":
    celery_app.start()
