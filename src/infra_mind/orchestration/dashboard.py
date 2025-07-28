"""
Workflow Visualization Dashboard.

Provides real-time monitoring dashboard for workflow execution,
agent performance, and system health.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from .monitoring import WorkflowMonitor, WorkflowTrace, TraceSpan, PerformanceAlert, AlertSeverity
from .workflow import WorkflowState, WorkflowStatus, StepStatus
from ..core.metrics_collector import get_metrics_collector


logger = logging.getLogger(__name__)


class DashboardView(str, Enum):
    """Dashboard view types."""
    OVERVIEW = "overview"
    WORKFLOWS = "workflows"
    AGENTS = "agents"
    PERFORMANCE = "performance"
    ALERTS = "alerts"
    TRACES = "traces"


@dataclass
class DashboardMetrics:
    """Dashboard metrics summary."""
    active_workflows: int = 0
    completed_workflows: int = 0
    failed_workflows: int = 0
    total_agents: int = 0
    active_agents: int = 0
    avg_workflow_duration_minutes: float = 0.0
    avg_agent_response_time_seconds: float = 0.0
    system_health_score: float = 100.0
    active_alerts: int = 0
    critical_alerts: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class WorkflowSummary:
    """Workflow summary for dashboard."""
    workflow_id: str
    name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[float]
    total_steps: int
    completed_steps: int
    failed_steps: int
    progress_percent: float
    current_agents: List[str]
    
    @classmethod
    def from_workflow_state(cls, workflow: WorkflowState) -> "WorkflowSummary":
        """Create summary from workflow state."""
        duration_minutes = None
        if workflow.execution_time:
            duration_minutes = workflow.execution_time / 60
        
        progress_percent = 0.0
        if workflow.steps:
            progress_percent = (len(workflow.completed_steps) / len(workflow.steps)) * 100
        
        current_agents = [step.agent_name for step in workflow.running_steps]
        
        return cls(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            status=workflow.status.value,
            start_time=workflow.start_time or datetime.now(timezone.utc),
            end_time=workflow.end_time,
            duration_minutes=duration_minutes,
            total_steps=len(workflow.steps),
            completed_steps=len(workflow.completed_steps),
            failed_steps=len(workflow.failed_steps),
            progress_percent=progress_percent,
            current_agents=current_agents
        )


@dataclass
class AgentSummary:
    """Agent summary for dashboard."""
    agent_name: str
    status: str  # idle, running, error
    current_workflow: Optional[str]
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time_seconds: float
    last_execution: Optional[datetime]
    success_rate_percent: float


@dataclass
class SystemHealthSummary:
    """System health summary for dashboard."""
    overall_status: str  # healthy, warning, critical
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    response_time_ms: float
    error_rate_percent: float
    uptime_hours: float


class WorkflowDashboard:
    """
    Real-time workflow visualization dashboard.
    
    Provides comprehensive monitoring interface for workflow execution,
    agent performance, and system health.
    """
    
    def __init__(self, monitor: WorkflowMonitor):
        """
        Initialize dashboard.
        
        Args:
            monitor: Workflow monitor instance
        """
        self.monitor = monitor
        self.metrics_collector = get_metrics_collector()
        
        # Dashboard state
        self.connected_clients: Set[str] = set()
        self.update_interval = 5  # seconds
        self.is_running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Cached data
        self._cached_metrics: Optional[DashboardMetrics] = None
        self._cached_workflows: List[WorkflowSummary] = []
        self._cached_agents: List[AgentSummary] = []
        self._cached_health: Optional[SystemHealthSummary] = None
        self._last_update: Optional[datetime] = None
        
        logger.info("Workflow dashboard initialized")
    
    async def start(self) -> None:
        """Start dashboard updates."""
        if self.is_running:
            logger.warning("Dashboard already running")
            return
        
        self.is_running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Dashboard started")
    
    async def stop(self) -> None:
        """Stop dashboard updates."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Dashboard stopped")
    
    async def _update_loop(self) -> None:
        """Main dashboard update loop."""
        while self.is_running:
            try:
                await self._update_dashboard_data()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _update_dashboard_data(self) -> None:
        """Update all dashboard data."""
        try:
            # Update metrics
            self._cached_metrics = await self._calculate_dashboard_metrics()
            
            # Update workflow summaries
            self._cached_workflows = await self._get_workflow_summaries()
            
            # Update agent summaries
            self._cached_agents = await self._get_agent_summaries()
            
            # Update system health
            self._cached_health = await self._get_system_health_summary()
            
            self._last_update = datetime.now(timezone.utc)
            
            logger.debug("Dashboard data updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
    
    async def _calculate_dashboard_metrics(self) -> DashboardMetrics:
        """Calculate dashboard metrics summary."""
        active_traces = self.monitor.get_active_traces()
        completed_traces = self.monitor.get_completed_traces(limit=100)
        active_alerts = self.monitor.get_active_alerts()
        
        # Count workflow statuses
        active_workflows = len(active_traces)
        completed_workflows = sum(1 for trace in completed_traces if trace.status == "completed")
        failed_workflows = sum(1 for trace in completed_traces if trace.status == "failed")
        
        # Calculate average workflow duration
        avg_workflow_duration_minutes = 0.0
        completed_with_duration = [
            trace for trace in completed_traces
            if trace.end_time and trace.start_time
        ]
        
        if completed_with_duration:
            total_duration = sum(
                (trace.end_time - trace.start_time).total_seconds()
                for trace in completed_with_duration
            )
            avg_workflow_duration_minutes = (total_duration / len(completed_with_duration)) / 60
        
        # Calculate agent metrics
        agent_spans = []
        for trace in active_traces + completed_traces:
            agent_spans.extend([
                span for span in trace.spans
                if span.service_name != "orchestrator"
            ])
        
        total_agents = len(set(span.service_name for span in agent_spans))
        active_agents = len(set(
            span.service_name for span in agent_spans
            if span.status == "started"
        ))
        
        # Calculate average agent response time
        avg_agent_response_time_seconds = 0.0
        completed_agent_spans = [
            span for span in agent_spans
            if span.status == "completed" and span.duration_ms
        ]
        
        if completed_agent_spans:
            total_response_time = sum(span.duration_ms for span in completed_agent_spans)
            avg_agent_response_time_seconds = (total_response_time / len(completed_agent_spans)) / 1000
        
        # Get system health
        health = await self.metrics_collector.get_system_health()
        
        # Count alerts
        critical_alerts = sum(1 for alert in active_alerts if alert.severity == AlertSeverity.CRITICAL)
        
        return DashboardMetrics(
            active_workflows=active_workflows,
            completed_workflows=completed_workflows,
            failed_workflows=failed_workflows,
            total_agents=total_agents,
            active_agents=active_agents,
            avg_workflow_duration_minutes=avg_workflow_duration_minutes,
            avg_agent_response_time_seconds=avg_agent_response_time_seconds,
            system_health_score=health.uptime_seconds / 3600,  # Simple health score
            active_alerts=len(active_alerts),
            critical_alerts=critical_alerts
        )
    
    async def _get_workflow_summaries(self) -> List[WorkflowSummary]:
        """Get workflow summaries for dashboard."""
        summaries = []
        
        # Get active workflows from traces
        active_traces = self.monitor.get_active_traces()
        for trace in active_traces:
            # Create a mock workflow state from trace
            workflow_state = self._trace_to_workflow_state(trace)
            summary = WorkflowSummary.from_workflow_state(workflow_state)
            summaries.append(summary)
        
        # Get recent completed workflows
        completed_traces = self.monitor.get_completed_traces(limit=20)
        for trace in completed_traces[-10:]:  # Last 10 completed
            workflow_state = self._trace_to_workflow_state(trace)
            summary = WorkflowSummary.from_workflow_state(workflow_state)
            summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x.start_time, reverse=True)
    
    def _trace_to_workflow_state(self, trace: WorkflowTrace) -> WorkflowState:
        """Convert trace to workflow state for summary."""
        from .workflow import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
        
        # Create mock workflow state from trace
        status_map = {
            "active": WorkflowStatus.RUNNING,
            "completed": WorkflowStatus.COMPLETED,
            "failed": WorkflowStatus.FAILED
        }
        
        # Create steps from spans
        steps = []
        for span in trace.spans:
            if span.service_name != "orchestrator":
                step_status_map = {
                    "started": StepStatus.RUNNING,
                    "completed": StepStatus.COMPLETED,
                    "failed": StepStatus.FAILED
                }
                
                step = WorkflowStep(
                    step_id=span.span_id,
                    name=span.operation_name,
                    agent_name=span.service_name,
                    status=step_status_map.get(span.status, StepStatus.PENDING),
                    start_time=span.start_time,
                    end_time=span.end_time
                )
                steps.append(step)
        
        return WorkflowState(
            workflow_id=trace.workflow_id,
            name=trace.workflow_name,
            status=status_map.get(trace.status, WorkflowStatus.PENDING),
            steps=steps,
            start_time=trace.start_time,
            end_time=trace.end_time
        )
    
    async def _get_agent_summaries(self) -> List[AgentSummary]:
        """Get agent summaries for dashboard."""
        summaries = []
        
        # Get all traces
        all_traces = self.monitor.get_active_traces() + self.monitor.get_completed_traces(limit=100)
        
        # Group spans by agent
        agent_spans: Dict[str, List[TraceSpan]] = {}
        for trace in all_traces:
            for span in trace.spans:
                if span.service_name != "orchestrator":
                    if span.service_name not in agent_spans:
                        agent_spans[span.service_name] = []
                    agent_spans[span.service_name].append(span)
        
        # Create summaries
        for agent_name, spans in agent_spans.items():
            # Determine current status
            status = "idle"
            current_workflow = None
            
            running_spans = [span for span in spans if span.status == "started"]
            if running_spans:
                status = "running"
                # Find the trace for the running span
                for trace in self.monitor.get_active_traces():
                    if any(span.span_id == running_span.span_id for running_span in running_spans for span in trace.spans):
                        current_workflow = trace.workflow_id
                        break
            
            # Check for recent errors
            recent_errors = [
                span for span in spans
                if span.status == "failed" and span.end_time and
                (datetime.now(timezone.utc) - span.end_time).total_seconds() < 3600
            ]
            if recent_errors and status == "idle":
                status = "error"
            
            # Calculate metrics
            total_executions = len(spans)
            successful_executions = sum(1 for span in spans if span.status == "completed")
            failed_executions = sum(1 for span in spans if span.status == "failed")
            
            success_rate_percent = 0.0
            if total_executions > 0:
                success_rate_percent = (successful_executions / total_executions) * 100
            
            # Calculate average execution time
            avg_execution_time_seconds = 0.0
            completed_spans = [span for span in spans if span.status == "completed" and span.duration_ms]
            if completed_spans:
                total_time = sum(span.duration_ms for span in completed_spans)
                avg_execution_time_seconds = (total_time / len(completed_spans)) / 1000
            
            # Find last execution
            last_execution = None
            if spans:
                last_span = max(spans, key=lambda x: x.start_time)
                last_execution = last_span.start_time
            
            summary = AgentSummary(
                agent_name=agent_name,
                status=status,
                current_workflow=current_workflow,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                avg_execution_time_seconds=avg_execution_time_seconds,
                last_execution=last_execution,
                success_rate_percent=success_rate_percent
            )
            summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x.agent_name)
    
    async def _get_system_health_summary(self) -> SystemHealthSummary:
        """Get system health summary."""
        health = await self.metrics_collector.get_system_health()
        
        return SystemHealthSummary(
            overall_status=health.status,
            cpu_usage_percent=health.cpu_usage_percent,
            memory_usage_percent=health.memory_usage_percent,
            disk_usage_percent=health.disk_usage_percent,
            active_connections=health.active_connections,
            response_time_ms=health.response_time_ms,
            error_rate_percent=health.error_rate_percent,
            uptime_hours=health.uptime_seconds / 3600
        )
    
    # Public API
    
    def get_dashboard_data(self, view: DashboardView = DashboardView.OVERVIEW) -> Dict[str, Any]:
        """Get dashboard data for specific view."""
        base_data = {
            "view": view.value,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if view == DashboardView.OVERVIEW:
            return {
                **base_data,
                "metrics": asdict(self._cached_metrics) if self._cached_metrics else None,
                "recent_workflows": [asdict(w) for w in self._cached_workflows[:5]],
                "system_health": asdict(self._cached_health) if self._cached_health else None,
                "active_alerts": len(self.monitor.get_active_alerts())
            }
        
        elif view == DashboardView.WORKFLOWS:
            return {
                **base_data,
                "workflows": [asdict(w) for w in self._cached_workflows],
                "metrics": {
                    "active": self._cached_metrics.active_workflows if self._cached_metrics else 0,
                    "completed": self._cached_metrics.completed_workflows if self._cached_metrics else 0,
                    "failed": self._cached_metrics.failed_workflows if self._cached_metrics else 0
                }
            }
        
        elif view == DashboardView.AGENTS:
            return {
                **base_data,
                "agents": [asdict(a) for a in self._cached_agents],
                "metrics": {
                    "total": self._cached_metrics.total_agents if self._cached_metrics else 0,
                    "active": self._cached_metrics.active_agents if self._cached_metrics else 0,
                    "avg_response_time": self._cached_metrics.avg_agent_response_time_seconds if self._cached_metrics else 0
                }
            }
        
        elif view == DashboardView.PERFORMANCE:
            return {
                **base_data,
                "system_health": asdict(self._cached_health) if self._cached_health else None,
                "performance_metrics": {
                    "avg_workflow_duration": self._cached_metrics.avg_workflow_duration_minutes if self._cached_metrics else 0,
                    "avg_agent_response_time": self._cached_metrics.avg_agent_response_time_seconds if self._cached_metrics else 0,
                    "system_health_score": self._cached_metrics.system_health_score if self._cached_metrics else 0
                },
                "monitoring_stats": self.monitor.get_monitoring_stats()
            }
        
        elif view == DashboardView.ALERTS:
            active_alerts = self.monitor.get_active_alerts()
            all_alerts = self.monitor.get_all_alerts(limit=50)
            
            return {
                **base_data,
                "active_alerts": [asdict(alert) for alert in active_alerts],
                "recent_alerts": [asdict(alert) for alert in all_alerts[-20:]],
                "alert_summary": {
                    "total_active": len(active_alerts),
                    "critical": sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL),
                    "high": sum(1 for a in active_alerts if a.severity == AlertSeverity.HIGH),
                    "medium": sum(1 for a in active_alerts if a.severity == AlertSeverity.MEDIUM),
                    "low": sum(1 for a in active_alerts if a.severity == AlertSeverity.LOW)
                }
            }
        
        elif view == DashboardView.TRACES:
            active_traces = self.monitor.get_active_traces()
            completed_traces = self.monitor.get_completed_traces(limit=20)
            
            return {
                **base_data,
                "active_traces": [trace.to_dict() for trace in active_traces],
                "recent_traces": [trace.to_dict() for trace in completed_traces[-10:]],
                "trace_stats": {
                    "active_count": len(active_traces),
                    "completed_count": len(completed_traces),
                    "total_spans": sum(len(trace.spans) for trace in active_traces + completed_traces)
                }
            }
        
        return base_data
    
    def get_workflow_detail(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific workflow."""
        trace = self.monitor.get_trace(workflow_id)
        if not trace:
            return None
        
        workflow_state = self._trace_to_workflow_state(trace)
        summary = WorkflowSummary.from_workflow_state(workflow_state)
        
        return {
            "summary": asdict(summary),
            "trace": trace.to_dict(),
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "agent_name": step.agent_name,
                    "status": step.status.value,
                    "start_time": step.start_time.isoformat() if step.start_time else None,
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                    "execution_time": step.execution_time,
                    "error": step.error,
                    "retry_count": step.retry_count
                }
                for step in workflow_state.steps
            ]
        }
    
    def get_agent_detail(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific agent."""
        agent_summary = next(
            (agent for agent in self._cached_agents if agent.agent_name == agent_name),
            None
        )
        
        if not agent_summary:
            return None
        
        # Get recent executions
        all_traces = self.monitor.get_active_traces() + self.monitor.get_completed_traces(limit=50)
        agent_executions = []
        
        for trace in all_traces:
            for span in trace.spans:
                if span.service_name == agent_name:
                    agent_executions.append({
                        "workflow_id": trace.workflow_id,
                        "workflow_name": trace.workflow_name,
                        "span_id": span.span_id,
                        "operation": span.operation_name,
                        "start_time": span.start_time.isoformat(),
                        "end_time": span.end_time.isoformat() if span.end_time else None,
                        "duration_ms": span.duration_ms,
                        "status": span.status,
                        "error": span.error
                    })
        
        # Sort by start time, most recent first
        agent_executions.sort(key=lambda x: x["start_time"], reverse=True)
        
        return {
            "summary": asdict(agent_summary),
            "recent_executions": agent_executions[:20],
            "performance_trends": {
                # TODO: Add performance trend analysis
                "avg_duration_trend": [],
                "success_rate_trend": [],
                "error_rate_trend": []
            }
        }
    
    def export_dashboard_data(self, format: str = "json") -> str:
        """Export dashboard data in specified format."""
        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": asdict(self._cached_metrics) if self._cached_metrics else None,
            "workflows": [asdict(w) for w in self._cached_workflows],
            "agents": [asdict(a) for a in self._cached_agents],
            "system_health": asdict(self._cached_health) if self._cached_health else None,
            "active_alerts": [asdict(alert) for alert in self.monitor.get_active_alerts()],
            "monitoring_stats": self.monitor.get_monitoring_stats()
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global dashboard instance
_workflow_dashboard: Optional[WorkflowDashboard] = None


def get_workflow_dashboard(monitor: Optional[WorkflowMonitor] = None) -> WorkflowDashboard:
    """Get the global workflow dashboard instance."""
    global _workflow_dashboard
    if _workflow_dashboard is None:
        if monitor is None:
            raise ValueError("WorkflowMonitor required for first initialization")
        _workflow_dashboard = WorkflowDashboard(monitor)
    return _workflow_dashboard


async def initialize_workflow_dashboard(monitor: WorkflowMonitor) -> None:
    """Initialize and start workflow dashboard."""
    dashboard = get_workflow_dashboard(monitor)
    await dashboard.start()
    logger.info("Workflow dashboard initialized")


async def shutdown_workflow_dashboard() -> None:
    """Shutdown workflow dashboard."""
    global _workflow_dashboard
    if _workflow_dashboard:
        await _workflow_dashboard.stop()
        logger.info("Workflow dashboard shutdown")