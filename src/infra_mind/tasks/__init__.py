"""
Celery Tasks Package

Background task processing with Celery for long-running operations.
Enables instant API responses and fault-tolerant processing.
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
