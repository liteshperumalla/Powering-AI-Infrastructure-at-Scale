"""
Metrics Collection Service for Infra Mind.

Implements basic metrics collection for system performance, user engagement,
and system health monitoring as required by task 12.1.
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from ..models.metrics import Metric, AgentMetrics, MetricType, MetricCategory
from ..core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class SystemHealthStatus:
    """System health status data structure."""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    response_time_ms: float
    error_rate_percent: float
    uptime_seconds: float
    status: str = "healthy"  # healthy, warning, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEngagementMetrics:
    """User engagement metrics data structure."""
    active_users_count: int
    new_users_count: int
    assessments_started: int
    assessments_completed: int
    reports_generated: int
    average_session_duration_minutes: float
    bounce_rate_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """
    Central metrics collection service.
    
    Handles collection of system performance, user engagement,
    and health monitoring metrics.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
        self.collection_interval = 60  # seconds
        self.is_collecting = False
        self._collection_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._request_times: List[float] = []
        self._error_count = 0
        self._request_count = 0
        
        # User engagement tracking
        self._active_sessions: Dict[str, datetime] = {}
        self._user_actions: List[Dict[str, Any]] = []
    
    async def start_collection(self) -> None:
        """Start automatic metrics collection."""
        if self.is_collecting:
            logger.warning("Metrics collection already started")
            return
        
        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Started metrics collection")
    
    async def stop_collection(self) -> None:
        """Stop automatic metrics collection."""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped metrics collection")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self.is_collecting:
            try:
                await self.collect_system_metrics()
                await self.collect_health_metrics()
                await self.collect_user_engagement_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            await Metric.record_metric(
                name="system.cpu.usage_percent",
                value=cpu_percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor"
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            await Metric.record_metric(
                name="system.memory.usage_percent",
                value=memory.percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor",
                dimensions={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            )
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await Metric.record_metric(
                name="system.disk.usage_percent",
                value=disk_percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor",
                dimensions={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
            # Network connections
            connections = len(psutil.net_connections())
            await Metric.record_metric(
                name="system.network.active_connections",
                value=connections,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="count",
                source="system_monitor"
            )
            
            # Process metrics
            process = psutil.Process()
            await Metric.record_metric(
                name="system.process.memory_mb",
                value=process.memory_info().rss / (1024 * 1024),
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="mb",
                source="system_monitor"
            )
            
            logger.debug("Collected system performance metrics")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def collect_health_metrics(self) -> None:
        """Collect system health monitoring metrics."""
        try:
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            await Metric.record_metric(
                name="system.uptime_seconds",
                value=uptime_seconds,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit="seconds",
                source="health_monitor"
            )
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            await Metric.record_metric(
                name="system.error_rate_percent",
                value=error_rate,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="percent",
                source="health_monitor",
                dimensions={
                    "total_requests": self._request_count,
                    "total_errors": self._error_count
                }
            )
            
            # Calculate average response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times) / len(self._request_times)
            
            await Metric.record_metric(
                name="system.avg_response_time_ms",
                value=avg_response_time,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="ms",
                source="health_monitor",
                dimensions={
                    "sample_count": len(self._request_times)
                }
            )
            
            # Determine health status
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            health_score = 100.0
            if cpu_percent > 80:
                health_score -= 30
            elif cpu_percent > 60:
                health_score -= 15
            
            if memory_percent > 85:
                health_score -= 30
            elif memory_percent > 70:
                health_score -= 15
            
            if error_rate > 5:
                health_score -= 25
            elif error_rate > 1:
                health_score -= 10
            
            await Metric.record_metric(
                name="system.health_score",
                value=health_score,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit="score",
                source="health_monitor",
                dimensions={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "error_rate": error_rate
                }
            )
            
            # Reset counters periodically
            if len(self._request_times) > 1000:
                self._request_times = self._request_times[-500:]
            
            logger.debug("Collected health monitoring metrics")
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
    
    async def collect_user_engagement_metrics(self) -> None:
        """Collect user engagement tracking metrics."""
        try:
            # Active sessions count
            now = datetime.utcnow()
            active_sessions = sum(
                1 for last_activity in self._active_sessions.values()
                if (now - last_activity).total_seconds() < 1800  # 30 minutes
            )
            
            await Metric.record_metric(
                name="user.active_sessions",
                value=active_sessions,
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # User actions in the last hour
            hour_ago = now - timedelta(hours=1)
            recent_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > hour_ago
            ]
            
            await Metric.record_metric(
                name="user.actions_per_hour",
                value=len(recent_actions),
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # Action type breakdown
            action_types = {}
            for action in recent_actions:
                action_type = action.get('type', 'unknown')
                action_types[action_type] = action_types.get(action_type, 0) + 1
            
            for action_type, count in action_types.items():
                await Metric.record_metric(
                    name=f"user.action.{action_type}",
                    value=count,
                    metric_type=MetricType.USER_ENGAGEMENT,
                    category=MetricCategory.USER_EXPERIENCE,
                    unit="count",
                    source="engagement_tracker",
                    tags=[action_type]
                )
            
            # Clean up old actions
            self._user_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > hour_ago
            ]
            
            logger.debug("Collected user engagement metrics")
            
        except Exception as e:
            logger.error(f"Error collecting user engagement metrics: {e}")
    
    # API tracking methods
    
    def track_request(self, response_time_ms: float, success: bool = True) -> None:
        """Track API request metrics."""
        self._request_times.append(response_time_ms)
        self._request_count += 1
        if not success:
            self._error_count += 1
    
    def track_user_action(
        self,
        user_id: str,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user engagement action."""
        now = datetime.utcnow()
        self._active_sessions[user_id] = now
        
        action = {
            'user_id': user_id,
            'type': action_type,
            'timestamp': now,
            'metadata': metadata or {}
        }
        self._user_actions.append(action)
    
    async def record_agent_performance(
        self,
        agent_name: str,
        execution_time: float,
        success: bool,
        confidence_score: Optional[float] = None,
        recommendations_count: int = 0,
        assessment_id: Optional[str] = None
    ) -> None:
        """Record agent performance metrics."""
        try:
            # Create agent metrics record
            agent_metrics = await AgentMetrics.create_for_agent(
                agent_name=agent_name,
                agent_version="1.0.0",  # TODO: Get from agent
                started_at=datetime.utcnow() - timedelta(seconds=execution_time),
                assessment_id=assessment_id
            )
            
            # Update performance data
            agent_metrics.update_performance(
                execution_time=execution_time,
                api_calls=1  # Basic tracking
            )
            
            if confidence_score is not None:
                agent_metrics.update_quality(confidence_score=confidence_score)
            
            agent_metrics.update_output(recommendations=recommendations_count)
            
            if not success:
                agent_metrics.record_error()
            
            await agent_metrics.save()
            
            # Also record as general metrics
            await Metric.record_metric(
                name=f"agent.{agent_name}.execution_time",
                value=execution_time,
                metric_type=MetricType.AGENT_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="seconds",
                source=f"agent_{agent_name}",
                dimensions={
                    "success": success,
                    "recommendations_count": recommendations_count
                }
            )
            
            if confidence_score is not None:
                await Metric.record_metric(
                    name=f"agent.{agent_name}.confidence_score",
                    value=confidence_score,
                    metric_type=MetricType.AGENT_PERFORMANCE,
                    category=MetricCategory.BUSINESS,
                    unit="score",
                    source=f"agent_{agent_name}"
                )
            
        except Exception as e:
            logger.error(f"Error recording agent performance: {e}")
    
    async def record_error(self, error_type: str, error_category: str, severity: str,
                          component: str, agent_name: Optional[str] = None,
                          workflow_id: Optional[str] = None, is_recoverable: bool = True) -> None:
        """Record error metrics."""
        try:
            await Metric.record_metric(
                name="system.error_event",
                value=1.0,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="count",
                source="error_handler",
                dimensions={
                    "error_type": error_type,
                    "error_category": error_category,
                    "severity": severity,
                    "component": component,
                    "agent_name": agent_name,
                    "workflow_id": workflow_id,
                    "is_recoverable": is_recoverable
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record error metric: {str(e)}")
    
    async def record_alert(self, alert_id: str, rule_name: str, level: str,
                          metric_value: float, threshold: float) -> None:
        """Record alert metrics."""
        try:
            await Metric.record_metric(
                name="system.alert",
                value=1.0,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="count",
                source="alert_manager",
                dimensions={
                    "alert_id": alert_id,
                    "rule_name": rule_name,
                    "level": level,
                    "metric_value": metric_value,
                    "threshold": threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record alert metric: {str(e)}")
    
    async def record_monitoring_metric(self, metric_name: str, value: float, unit: str) -> None:
        """Record monitoring metrics."""
        try:
            await Metric.record_metric(
                name=f"monitoring.{metric_name}",
                value=value,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit=unit,
                source="error_monitor"
            )
            
        except Exception as e:
            logger.error(f"Failed to record monitoring metric: {str(e)}")
    
    async def get_error_metrics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error metrics for the specified time window."""
        try:
            # This would query the actual metrics storage
            # For now, return basic data based on tracked errors
            return {
                "total_errors": self._error_count,
                "error_rate": (self._error_count / max(self._request_count, 1)) * 100,
                "recovery_rate": 1.0,  # Would be calculated from actual recovery data
                "error_categories": {},
                "time_window_hours": time_window_hours
            }
        except Exception as e:
            logger.error(f"Failed to get error metrics: {str(e)}")
            return {}
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status."""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            connections = len(psutil.net_connections())
            
            # Calculate response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times[-10:]) / min(len(self._request_times), 10)
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            # Determine status
            status = "healthy"
            if cpu_usage > 80 or memory.percent > 85 or error_rate > 5:
                status = "critical"
            elif cpu_usage > 60 or memory.percent > 70 or error_rate > 1:
                status = "warning"
            
            return SystemHealthStatus(
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=connections,
                response_time_ms=avg_response_time,
                error_rate_percent=error_rate,
                uptime_seconds=(datetime.utcnow() - self.start_time).total_seconds(),
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return SystemHealthStatus(
                cpu_usage_percent=0,
                memory_usage_percent=0,
                disk_usage_percent=0,
                active_connections=0,
                response_time_ms=0,
                error_rate_percent=100,
                uptime_seconds=0,
                status="critical"
            )
    
    async def get_user_engagement_summary(self) -> UserEngagementMetrics:
        """Get user engagement metrics summary."""
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            # Count active sessions
            active_users = sum(
                1 for last_activity in self._active_sessions.values()
                if (now - last_activity).total_seconds() < 1800
            )
            
            # Count recent actions
            recent_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > hour_ago
            ]
            
            # Count specific action types
            assessments_started = sum(
                1 for action in recent_actions
                if action.get('type') == 'assessment_started'
            )
            
            assessments_completed = sum(
                1 for action in recent_actions
                if action.get('type') == 'assessment_completed'
            )
            
            reports_generated = sum(
                1 for action in recent_actions
                if action.get('type') == 'report_generated'
            )
            
            return UserEngagementMetrics(
                active_users_count=active_users,
                new_users_count=0,  # TODO: Implement new user tracking
                assessments_started=assessments_started,
                assessments_completed=assessments_completed,
                reports_generated=reports_generated,
                average_session_duration_minutes=30.0,  # TODO: Calculate actual duration
                bounce_rate_percent=0.0  # TODO: Implement bounce rate calculation
            )
            
        except Exception as e:
            logger.error(f"Error getting user engagement summary: {e}")
            return UserEngagementMetrics(
                active_users_count=0,
                new_users_count=0,
                assessments_started=0,
                assessments_completed=0,
                reports_generated=0,
                average_session_duration_minutes=0,
                bounce_rate_percent=0
            )
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str):
        """Context manager to track operation performance."""
        start_time = time.time()
        success = True
        
        try:
            yield
        except Exception as e:
            success = False
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self.track_request(execution_time, success)
            
            # Record operation-specific metric
            await Metric.record_metric(
                name=f"operation.{operation_name}.duration",
                value=execution_time,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="ms",
                source="operation_tracker",
                dimensions={"success": success}
            )


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


async def initialize_metrics_collection() -> None:
    """Initialize and start metrics collection."""
    collector = get_metrics_collector()
    await collector.start_collection()
    logger.info("Metrics collection initialized")


async def shutdown_metrics_collection() -> None:
    """Shutdown metrics collection."""
    collector = get_metrics_collector()
    await collector.stop_collection()
    logger.info("Metrics collection shutdown")