"""
Advanced Workflow Monitoring and Debugging System.

Provides comprehensive logging, distributed tracing, and real-time monitoring
for multi-agent workflow execution.
"""

import asyncio
import logging
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import traceback

from .events import EventManager, AgentEvent, EventType
from .workflow import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
from ..core.metrics_collector import get_metrics_collector
from ..models.metrics import Metric, MetricType, MetricCategory


logger = logging.getLogger(__name__)


class TraceLevel(str, Enum):
    """Trace logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TraceSpan:
    """Distributed tracing span for agent operations."""
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    service_name: str = ""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "started"  # started, completed, failed
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def finish(self, status: str = "completed", error: Optional[str] = None) -> None:
        """Finish the span."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        self.error = error
    
    def add_log(self, level: TraceLevel, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a log entry to the span."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "message": message,
            "data": data or {}
        }
        self.logs.append(log_entry)
    
    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span."""
        self.tags[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tags": self.tags,
            "logs": self.logs,
            "error": self.error
        }


@dataclass
class WorkflowTrace:
    """Complete trace for a workflow execution."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    spans: List[TraceSpan] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_span(self, span: TraceSpan) -> None:
        """Add a span to the trace."""
        span.trace_id = self.trace_id
        self.spans.append(span)
    
    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get span by ID."""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None
    
    def finish(self, status: str = "completed") -> None:
        """Finish the trace."""
        self.end_time = datetime.now(timezone.utc)
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "spans": [span.to_dict() for span in self.spans],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "metadata": self.metadata,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.end_time else None
            )
        }


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str = ""
    severity: AlertSeverity = AlertSeverity.LOW
    message: str = ""
    workflow_id: Optional[str] = None
    agent_name: Optional[str] = None
    metric_name: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolution_time = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None
        }


class WorkflowMonitor:
    """
    Advanced workflow monitoring and debugging system.
    
    Provides comprehensive logging, distributed tracing, performance monitoring,
    and alerting for multi-agent workflows.
    """
    
    def __init__(self, event_manager: EventManager):
        """
        Initialize workflow monitor.
        
        Args:
            event_manager: Event manager for workflow coordination
        """
        self.event_manager = event_manager
        self.metrics_collector = get_metrics_collector()
        
        # Tracing storage
        self.active_traces: Dict[str, WorkflowTrace] = {}
        self.completed_traces: List[WorkflowTrace] = []
        self.active_spans: Dict[str, TraceSpan] = {}
        
        # Performance monitoring
        self.performance_thresholds = {
            "workflow_duration_ms": 300000,  # 5 minutes
            "step_duration_ms": 120000,      # 2 minutes
            "agent_response_time_ms": 30000,  # 30 seconds
            "memory_usage_percent": 85,
            "cpu_usage_percent": 80,
            "error_rate_percent": 5
        }
        
        # Alerting
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Monitoring state
        self.is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Subscribe to workflow events
        asyncio.create_task(self._setup_event_subscriptions())
        
        logger.info("Workflow monitor initialized")
    
    async def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for monitoring."""
        await self.event_manager.subscribe(EventType.WORKFLOW_STARTED, self._on_workflow_started)
        await self.event_manager.subscribe(EventType.WORKFLOW_COMPLETED, self._on_workflow_completed)
        await self.event_manager.subscribe(EventType.WORKFLOW_FAILED, self._on_workflow_failed)
        await self.event_manager.subscribe(EventType.AGENT_STARTED, self._on_agent_started)
        await self.event_manager.subscribe(EventType.AGENT_COMPLETED, self._on_agent_completed)
        await self.event_manager.subscribe(EventType.AGENT_FAILED, self._on_agent_failed)
    
    async def start_monitoring(self) -> None:
        """Start continuous monitoring."""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started workflow monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped workflow monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_performance_thresholds()
                await self._cleanup_old_traces()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    # Event handlers
    
    async def _on_workflow_started(self, event: AgentEvent) -> None:
        """Handle workflow started event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id:
            return
        
        trace = WorkflowTrace(
            workflow_id=workflow_id,
            workflow_name=event.data.get("name", "Unknown Workflow"),
            metadata=event.data
        )
        
        self.active_traces[workflow_id] = trace
        
        # Create root span
        root_span = TraceSpan(
            operation_name="workflow_execution",
            service_name="orchestrator",
            tags={
                "workflow.id": workflow_id,
                "workflow.name": trace.workflow_name,
                "workflow.total_steps": event.data.get("total_steps", 0)
            }
        )
        
        trace.add_span(root_span)
        self.active_spans[f"workflow_{workflow_id}"] = root_span
        
        logger.info(f"Started monitoring workflow: {workflow_id}")
    
    async def _on_workflow_completed(self, event: AgentEvent) -> None:
        """Handle workflow completed event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id or workflow_id not in self.active_traces:
            return
        
        trace = self.active_traces[workflow_id]
        trace.finish("completed")
        
        # Finish root span
        root_span_key = f"workflow_{workflow_id}"
        if root_span_key in self.active_spans:
            root_span = self.active_spans[root_span_key]
            root_span.finish("completed")
            root_span.add_tag("workflow.completed_steps", event.data.get("completed_steps", 0))
            del self.active_spans[root_span_key]
        
        # Move to completed traces
        self.completed_traces.append(trace)
        del self.active_traces[workflow_id]
        
        # Record metrics
        if trace.end_time:
            duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
            await Metric.record_metric(
                name="workflow.execution_time",
                value=duration_ms,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit="ms",
                source="workflow_monitor",
                dimensions={
                    "workflow_id": workflow_id,
                    "workflow_name": trace.workflow_name,
                    "status": "completed"
                }
            )
        
        logger.info(f"Workflow completed: {workflow_id}")
    
    async def _on_workflow_failed(self, event: AgentEvent) -> None:
        """Handle workflow failed event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id or workflow_id not in self.active_traces:
            return
        
        trace = self.active_traces[workflow_id]
        trace.finish("failed")
        
        # Finish root span with error
        root_span_key = f"workflow_{workflow_id}"
        if root_span_key in self.active_spans:
            root_span = self.active_spans[root_span_key]
            root_span.finish("failed", event.metadata.get("error"))
            del self.active_spans[root_span_key]
        
        # Move to completed traces
        self.completed_traces.append(trace)
        del self.active_traces[workflow_id]
        
        # Create alert
        alert = PerformanceAlert(
            alert_type="workflow_failure",
            severity=AlertSeverity.HIGH,
            message=f"Workflow {workflow_id} failed: {event.metadata.get('error', 'Unknown error')}",
            workflow_id=workflow_id
        )
        await self._trigger_alert(alert)
        
        logger.error(f"Workflow failed: {workflow_id}")
    
    async def _on_agent_started(self, event: AgentEvent) -> None:
        """Handle agent started event."""
        workflow_id = event.data.get("workflow_id")
        step_id = event.data.get("step_id")
        
        if not workflow_id or workflow_id not in self.active_traces:
            return
        
        trace = self.active_traces[workflow_id]
        
        # Create agent span
        agent_span = TraceSpan(
            operation_name=f"agent_{event.agent_name}",
            service_name=event.agent_name,
            parent_span_id=f"workflow_{workflow_id}",
            tags={
                "agent.name": event.agent_name,
                "workflow.id": workflow_id,
                "step.id": step_id
            }
        )
        
        trace.add_span(agent_span)
        self.active_spans[f"agent_{event.agent_name}_{step_id}"] = agent_span
        
        agent_span.add_log(TraceLevel.INFO, f"Agent {event.agent_name} started", event.data)
        
        logger.debug(f"Agent started: {event.agent_name} for workflow {workflow_id}")
    
    async def _on_agent_completed(self, event: AgentEvent) -> None:
        """Handle agent completed event."""
        workflow_id = event.data.get("workflow_id")
        step_id = event.data.get("step_id")
        execution_time = event.data.get("execution_time", 0)
        
        span_key = f"agent_{event.agent_name}_{step_id}"
        if span_key in self.active_spans:
            span = self.active_spans[span_key]
            span.finish("completed")
            span.add_tag("execution_time_ms", execution_time * 1000 if execution_time else 0)
            span.add_log(TraceLevel.INFO, f"Agent {event.agent_name} completed", event.data)
            del self.active_spans[span_key]
        
        # Record agent performance metrics
        await self.metrics_collector.record_agent_performance(
            agent_name=event.agent_name,
            execution_time=execution_time,
            success=True,
            assessment_id=workflow_id
        )
        
        # Check for performance alerts
        if execution_time and execution_time * 1000 > self.performance_thresholds["agent_response_time_ms"]:
            alert = PerformanceAlert(
                alert_type="slow_agent_response",
                severity=AlertSeverity.MEDIUM,
                message=f"Agent {event.agent_name} took {execution_time:.2f}s to complete",
                workflow_id=workflow_id,
                agent_name=event.agent_name,
                metric_name="agent_response_time_ms",
                metric_value=execution_time * 1000,
                threshold=self.performance_thresholds["agent_response_time_ms"]
            )
            await self._trigger_alert(alert)
        
        logger.debug(f"Agent completed: {event.agent_name} in {execution_time:.2f}s")
    
    async def _on_agent_failed(self, event: AgentEvent) -> None:
        """Handle agent failed event."""
        workflow_id = event.data.get("workflow_id")
        step_id = event.data.get("step_id")
        error = event.metadata.get("error", "Unknown error")
        
        span_key = f"agent_{event.agent_name}_{step_id}"
        if span_key in self.active_spans:
            span = self.active_spans[span_key]
            span.finish("failed", error)
            span.add_log(TraceLevel.ERROR, f"Agent {event.agent_name} failed", {
                "error": error,
                **event.data
            })
            del self.active_spans[span_key]
        
        # Record agent failure
        await self.metrics_collector.record_agent_performance(
            agent_name=event.agent_name,
            execution_time=0,
            success=False,
            assessment_id=workflow_id
        )
        
        # Create alert
        alert = PerformanceAlert(
            alert_type="agent_failure",
            severity=AlertSeverity.HIGH,
            message=f"Agent {event.agent_name} failed: {error}",
            workflow_id=workflow_id,
            agent_name=event.agent_name
        )
        await self._trigger_alert(alert)
        
        logger.error(f"Agent failed: {event.agent_name} - {error}")
    
    # Performance monitoring
    
    async def _check_performance_thresholds(self) -> None:
        """Check performance thresholds and trigger alerts."""
        try:
            # Check system health
            health = await self.metrics_collector.get_system_health()
            
            # CPU usage alert
            if health.cpu_usage_percent > self.performance_thresholds["cpu_usage_percent"]:
                alert = PerformanceAlert(
                    alert_type="high_cpu_usage",
                    severity=AlertSeverity.HIGH if health.cpu_usage_percent > 90 else AlertSeverity.MEDIUM,
                    message=f"High CPU usage: {health.cpu_usage_percent:.1f}%",
                    metric_name="cpu_usage_percent",
                    metric_value=health.cpu_usage_percent,
                    threshold=self.performance_thresholds["cpu_usage_percent"]
                )
                await self._trigger_alert(alert)
            
            # Memory usage alert
            if health.memory_usage_percent > self.performance_thresholds["memory_usage_percent"]:
                alert = PerformanceAlert(
                    alert_type="high_memory_usage",
                    severity=AlertSeverity.HIGH if health.memory_usage_percent > 95 else AlertSeverity.MEDIUM,
                    message=f"High memory usage: {health.memory_usage_percent:.1f}%",
                    metric_name="memory_usage_percent",
                    metric_value=health.memory_usage_percent,
                    threshold=self.performance_thresholds["memory_usage_percent"]
                )
                await self._trigger_alert(alert)
            
            # Error rate alert
            if health.error_rate_percent > self.performance_thresholds["error_rate_percent"]:
                alert = PerformanceAlert(
                    alert_type="high_error_rate",
                    severity=AlertSeverity.CRITICAL if health.error_rate_percent > 10 else AlertSeverity.HIGH,
                    message=f"High error rate: {health.error_rate_percent:.1f}%",
                    metric_name="error_rate_percent",
                    metric_value=health.error_rate_percent,
                    threshold=self.performance_thresholds["error_rate_percent"]
                )
                await self._trigger_alert(alert)
            
            # Check long-running workflows
            for workflow_id, trace in self.active_traces.items():
                duration_ms = (datetime.now(timezone.utc) - trace.start_time).total_seconds() * 1000
                if duration_ms > self.performance_thresholds["workflow_duration_ms"]:
                    alert = PerformanceAlert(
                        alert_type="long_running_workflow",
                        severity=AlertSeverity.MEDIUM,
                        message=f"Workflow {workflow_id} has been running for {duration_ms/1000/60:.1f} minutes",
                        workflow_id=workflow_id,
                        metric_name="workflow_duration_ms",
                        metric_value=duration_ms,
                        threshold=self.performance_thresholds["workflow_duration_ms"]
                    )
                    await self._trigger_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
    
    async def _trigger_alert(self, alert: PerformanceAlert) -> None:
        """Trigger a performance alert."""
        # Check if similar alert already exists
        for existing_alert in self.active_alerts:
            if (existing_alert.alert_type == alert.alert_type and
                existing_alert.workflow_id == alert.workflow_id and
                existing_alert.agent_name == alert.agent_name and
                not existing_alert.resolved):
                return  # Don't duplicate alerts
        
        self.active_alerts.append(alert)
        
        # Record alert metric
        await Metric.record_metric(
            name=f"alert.{alert.alert_type}",
            value=1,
            metric_type=MetricType.ERROR_TRACKING,
            category=MetricCategory.OPERATIONAL,
            unit="count",
            source="workflow_monitor",
            dimensions={
                "severity": alert.severity.value,
                "workflow_id": alert.workflow_id,
                "agent_name": alert.agent_name
            }
        )
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.warning(f"Alert triggered: {alert.alert_type} - {alert.message}")
    
    async def _cleanup_old_traces(self) -> None:
        """Clean up old completed traces."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        self.completed_traces = [
            trace for trace in self.completed_traces
            if trace.end_time and trace.end_time > cutoff_time
        ]
    
    # Public API
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Remove alert callback."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_active_traces(self) -> List[WorkflowTrace]:
        """Get list of active workflow traces."""
        return list(self.active_traces.values())
    
    def get_completed_traces(self, limit: int = 100) -> List[WorkflowTrace]:
        """Get list of completed workflow traces."""
        return self.completed_traces[-limit:] if limit > 0 else self.completed_traces
    
    def get_trace(self, workflow_id: str) -> Optional[WorkflowTrace]:
        """Get trace by workflow ID."""
        if workflow_id in self.active_traces:
            return self.active_traces[workflow_id]
        
        for trace in self.completed_traces:
            if trace.workflow_id == workflow_id:
                return trace
        
        return None
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get list of active alerts."""
        return [alert for alert in self.active_alerts if not alert.resolved]
    
    def get_all_alerts(self, limit: int = 100) -> List[PerformanceAlert]:
        """Get all alerts (active and resolved)."""
        return self.active_alerts[-limit:] if limit > 0 else self.active_alerts
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.resolve()
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False
    
    def update_performance_threshold(self, metric_name: str, threshold: float) -> None:
        """Update performance threshold."""
        if metric_name in self.performance_thresholds:
            self.performance_thresholds[metric_name] = threshold
            logger.info(f"Updated threshold for {metric_name}: {threshold}")
        else:
            logger.warning(f"Unknown performance metric: {metric_name}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring system statistics."""
        active_alerts = self.get_active_alerts()
        
        return {
            "active_traces": len(self.active_traces),
            "completed_traces": len(self.completed_traces),
            "active_spans": len(self.active_spans),
            "active_alerts": len(active_alerts),
            "alert_breakdown": {
                severity.value: sum(1 for alert in active_alerts if alert.severity == severity)
                for severity in AlertSeverity
            },
            "performance_thresholds": self.performance_thresholds,
            "is_monitoring": self.is_monitoring
        }
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, service_name: str, 
                            parent_span_id: Optional[str] = None,
                            tags: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations."""
        span = TraceSpan(
            operation_name=operation_name,
            service_name=service_name,
            parent_span_id=parent_span_id,
            tags=tags or {}
        )
        
        span_key = f"{service_name}_{operation_name}_{span.span_id}"
        self.active_spans[span_key] = span
        
        try:
            yield span
            span.finish("completed")
        except Exception as e:
            span.finish("failed", str(e))
            span.add_log(TraceLevel.ERROR, f"Operation failed: {str(e)}", {
                "exception": str(e),
                "traceback": traceback.format_exc()
            })
            raise
        finally:
            if span_key in self.active_spans:
                del self.active_spans[span_key]


# Global monitor instance
_workflow_monitor: Optional[WorkflowMonitor] = None


def get_workflow_monitor(event_manager: Optional[EventManager] = None) -> WorkflowMonitor:
    """Get the global workflow monitor instance."""
    global _workflow_monitor
    if _workflow_monitor is None:
        if event_manager is None:
            raise ValueError("EventManager required for first initialization")
        _workflow_monitor = WorkflowMonitor(event_manager)
    return _workflow_monitor


async def initialize_workflow_monitoring(event_manager: EventManager) -> None:
    """Initialize and start workflow monitoring."""
    monitor = get_workflow_monitor(event_manager)
    await monitor.start_monitoring()
    logger.info("Workflow monitoring initialized")


async def shutdown_workflow_monitoring() -> None:
    """Shutdown workflow monitoring."""
    global _workflow_monitor
    if _workflow_monitor:
        await _workflow_monitor.stop_monitoring()
        logger.info("Workflow monitoring shutdown")