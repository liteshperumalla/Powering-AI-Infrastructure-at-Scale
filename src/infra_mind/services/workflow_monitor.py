"""
Workflow monitoring service for proactive detection and recovery of stuck assessments.

This service runs continuously to monitor workflow health and automatically
recover from deadlocks, failed tasks, and other workflow issues.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from beanie import PydanticObjectId

from ..models.assessment import Assessment
from ..schemas.base import AssessmentStatus
from ..core.database import get_database

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """
    Proactive workflow monitoring and recovery service.

    Features:
    - Detects stuck assessments automatically
    - Recovers deadlocked workflows
    - Monitors workflow health metrics
    - Provides early warning alerts
    """

    def __init__(self, check_interval: int = 300):  # 5 minutes
        self.check_interval = check_interval
        self.running = False
        self.deadlock_threshold = timedelta(minutes=30)
        self.stale_threshold = timedelta(hours=2)

    async def start_monitoring(self):
        """Start the continuous monitoring loop."""
        if self.running:
            logger.warning("Workflow monitor is already running")
            return

        self.running = True
        logger.info("🔍 Starting workflow monitoring service...")

        while self.running:
            try:
                await self._check_workflow_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in workflow monitoring cycle: {e}")
                await asyncio.sleep(30)  # Short retry delay

    async def stop_monitoring(self):
        """Stop the monitoring service."""
        self.running = False
        logger.info("⏹️ Workflow monitoring service stopped")

    async def _check_workflow_health(self):
        """Main health check routine."""
        logger.debug("🔍 Running workflow health check...")

        try:
            # Find potentially stuck assessments
            stuck_assessments = await self._find_stuck_assessments()

            if stuck_assessments:
                logger.warning(f"Found {len(stuck_assessments)} potentially stuck assessments")

                for assessment in stuck_assessments:
                    await self._recover_stuck_assessment(assessment)

            # Check for very stale assessments
            stale_assessments = await self._find_stale_assessments()
            if stale_assessments:
                logger.warning(f"Found {len(stale_assessments)} stale assessments")
                await self._handle_stale_assessments(stale_assessments)

            # Log health metrics
            await self._log_health_metrics()

        except Exception as e:
            logger.error(f"Error during workflow health check: {e}")

    async def _find_stuck_assessments(self) -> List[Assessment]:
        """Find assessments that appear to be stuck in processing."""
        cutoff_time = datetime.utcnow() - self.deadlock_threshold

        stuck_assessments = await Assessment.find({
            "status": AssessmentStatus.IN_PROGRESS,
            "updated_at": {"$lt": cutoff_time}
        }).to_list()

        return stuck_assessments

    async def _find_stale_assessments(self) -> List[Assessment]:
        """Find assessments that have been processing for too long."""
        cutoff_time = datetime.utcnow() - self.stale_threshold

        stale_assessments = await Assessment.find({
            "status": AssessmentStatus.IN_PROGRESS,
            "started_at": {"$lt": cutoff_time}
        }).to_list()

        return stale_assessments

    async def _recover_stuck_assessment(self, assessment: Assessment):
        """Attempt to recover a stuck assessment."""
        logger.warning(f"🔧 Attempting to recover stuck assessment: {assessment.id}")

        try:
            # Check if assessment is truly stuck or just slow
            progress = assessment.progress or {}
            last_step = progress.get('current_step', 'unknown')
            progress_pct = progress.get('progress_percentage', 0)

            logger.info(f"Assessment {assessment.id} stuck at: {last_step} ({progress_pct}%)")

            # Reset to draft state for restart
            assessment.status = AssessmentStatus.DRAFT
            assessment.progress = {
                "current_step": "auto_recovered",
                "completed_steps": ["created", "auto_recovered"],
                "total_steps": 5,
                "progress_percentage": 0.0,
                "recovery_reason": f"Auto-recovered from stuck state: {last_step}",
                "recovered_at": datetime.utcnow().isoformat(),
                "previous_progress": progress_pct
            }
            assessment.workflow_id = None
            assessment.updated_at = datetime.utcnow()

            await assessment.save()

            logger.info(f"✅ Successfully recovered assessment {assessment.id}")

        except Exception as e:
            logger.error(f"❌ Failed to recover assessment {assessment.id}: {e}")

    async def _handle_stale_assessments(self, stale_assessments: List[Assessment]):
        """Handle assessments that have been processing for too long."""
        for assessment in stale_assessments:
            logger.warning(f"⚠️ Assessment {assessment.id} has been processing for over 2 hours")

            # Mark as failed if it's been too long
            try:
                assessment.status = AssessmentStatus.FAILED
                assessment.progress = {
                    "current_step": "timed_out",
                    "completed_steps": ["created"],
                    "total_steps": 5,
                    "progress_percentage": 20.0,
                    "error": "Assessment timed out after 2 hours",
                    "timed_out_at": datetime.utcnow().isoformat()
                }
                await assessment.save()

                logger.info(f"⏰ Marked assessment {assessment.id} as failed due to timeout")

            except Exception as e:
                logger.error(f"Failed to mark assessment {assessment.id} as timed out: {e}")

    async def _log_health_metrics(self):
        """Log workflow health metrics for monitoring."""
        try:
            # Count assessments by status
            metrics = {}
            for status in AssessmentStatus:
                count = await Assessment.find({"status": status}).count()
                metrics[status.value] = count

            logger.info(f"📊 Workflow health metrics: {metrics}")

            # Check for concerning patterns
            in_progress_count = metrics.get('in_progress', 0)
            failed_count = metrics.get('failed', 0)

            if in_progress_count > 10:
                logger.warning(f"⚠️ High number of in-progress assessments: {in_progress_count}")

            if failed_count > metrics.get('completed', 0):
                logger.warning(f"⚠️ More failed than completed assessments: {failed_count} failed")

        except Exception as e:
            logger.error(f"Error logging health metrics: {e}")


# Global monitor instance
workflow_monitor = WorkflowMonitor()


async def start_workflow_monitoring():
    """Start the global workflow monitoring service."""
    await workflow_monitor.start_monitoring()


async def stop_workflow_monitoring():
    """Stop the global workflow monitoring service."""
    await workflow_monitor.stop_monitoring()