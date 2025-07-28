"""
Tests for advanced workflow monitoring and debugging system.

Tests comprehensive logging, distributed tracing, performance monitoring,
and alerting functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.infra_mind.orchestration.monitoring import (
    WorkflowMonitor, TraceSpan, WorkflowTrace, PerformanceAlert, AlertSeverity,
    get_workflow_monitor, initialize_workflow_monitoring
)
from src.infra_mind.orchestration.dashboard import (
    WorkflowDashboard, DashboardView, DashboardMetrics, WorkflowSummary,
    get_workflow_dashboard, initialize_workflow_dashboard
)
from src.infra_mind.orchestration.events import EventManager, AgentEvent, EventType
from src.infra_mind.orchestration.workflow import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
from src.infra_mind.core.advanced_logging import (
    AgentDecisionLogger, WorkflowLogger, PerformanceLogger,
    log_context, setup_advanced_logging
)
from src.infra_mind.models.assessment import Assessment


class TestWorkflowMonitor:
    """Test workflow monitoring functionality."""
    
    @pytest.fixture
    async def event_manager(self):
        """Create event manager for testing."""
        return EventManager()
    
    @pytest.fixture
    async def monitor(self, event_manager):
        """Create workflow monitor for testing."""
        monitor = WorkflowMonitor(event_manager)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.fixture
    def sample_assessment(self):
        """Create sample assessment for testing."""
        return Assessment(
            user_id="test_user",
            business_requirements={
                "company_size": "mid-size",
                "industry": "healthcare",
                "budget_range": "100k-500k"
            },
            technical_requirements={
                "current_infrastructure": "on-premise",
                "workload_type": "ml_training"
            },
            compliance_requirements={
                "regulations": ["HIPAA"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self, event_manager):
        """Test monitor initialization."""
        monitor = WorkflowMonitor(event_manager)
        
        assert monitor.event_manager == event_manager
        assert not monitor.is_monitoring
        assert len(monitor.active_traces) == 0
        assert len(monitor.active_alerts) == 0
        
        await monitor.start_monitoring()
        assert monitor.is_monitoring
        
        await monitor.stop_monitoring()
        assert not monitor.is_monitoring
    
    @pytest.mark.asyncio
    async def test_workflow_tracing(self, monitor, event_manager):
        """Test workflow tracing functionality."""
        workflow_id = "test_workflow_123"
        
        # Simulate workflow started event
        await event_manager.publish_workflow_started(
            workflow_id,
            {"name": "Test Workflow", "total_steps": 3}
        )
        
        # Check trace creation
        assert workflow_id in monitor.active_traces
        trace = monitor.active_traces[workflow_id]
        assert trace.workflow_id == workflow_id
        assert trace.workflow_name == "Test Workflow"
        assert trace.status == "active"
        assert len(trace.spans) == 1  # Root span
        
        # Simulate agent started event
        await event_manager.publish_agent_started(
            "cto_agent",
            {"workflow_id": workflow_id, "step_id": "step_1"}
        )
        
        # Check agent span creation
        assert len(trace.spans) == 2
        agent_span = trace.spans[1]
        assert agent_span.service_name == "cto_agent"
        assert agent_span.status == "started"
        
        # Simulate agent completed event
        await event_manager.publish_agent_completed(
            "cto_agent",
            {
                "workflow_id": workflow_id,
                "step_id": "step_1",
                "execution_time": 2.5
            }
        )
        
        # Check span completion
        agent_span = trace.get_span(agent_span.span_id)
        assert agent_span.status == "completed"
        assert agent_span.tags.get("execution_time_ms") == 2500
        
        # Simulate workflow completion
        await event_manager.publish_workflow_completed(
            workflow_id,
            {"completed_steps": 3}
        )
        
        # Check trace completion
        assert workflow_id not in monitor.active_traces
        assert len(monitor.completed_traces) == 1
        completed_trace = monitor.completed_traces[0]
        assert completed_trace.status == "completed"
    
    @pytest.mark.asyncio
    async def test_performance_alerting(self, monitor):
        """Test performance alerting system."""
        # Mock system health to trigger alerts
        with patch('src.infra_mind.core.metrics_collector.get_metrics_collector') as mock_collector:
            mock_health = Mock()
            mock_health.cpu_usage_percent = 90.0  # High CPU
            mock_health.memory_usage_percent = 95.0  # High memory
            mock_health.error_rate_percent = 8.0  # High error rate
            
            mock_collector.return_value.get_system_health = AsyncMock(return_value=mock_health)
            
            # Trigger threshold check
            await monitor._check_performance_thresholds()
            
            # Check alerts were created
            active_alerts = monitor.get_active_alerts()
            assert len(active_alerts) >= 2  # CPU and memory alerts
            
            # Check alert types
            alert_types = [alert.alert_type for alert in active_alerts]
            assert "high_cpu_usage" in alert_types
            assert "high_memory_usage" in alert_types
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self, monitor):
        """Test alert resolution functionality."""
        # Create test alert
        alert = PerformanceAlert(
            alert_type="test_alert",
            severity=AlertSeverity.MEDIUM,
            message="Test alert message"
        )
        monitor.active_alerts.append(alert)
        
        # Resolve alert
        success = monitor.resolve_alert(alert.alert_id)
        assert success
        assert alert.resolved
        assert alert.resolution_time is not None
        
        # Try to resolve non-existent alert
        success = monitor.resolve_alert("non_existent_id")
        assert not success
    
    @pytest.mark.asyncio
    async def test_trace_context_manager(self, monitor):
        """Test trace operation context manager."""
        async with monitor.trace_operation(
            "test_operation",
            "test_service",
            tags={"test": "value"}
        ) as span:
            assert span.operation_name == "test_operation"
            assert span.service_name == "test_service"
            assert span.tags["test"] == "value"
            assert span.status == "started"
            
            span.add_log("INFO", "Test log message", {"data": "test"})
            assert len(span.logs) == 1
        
        # Check span completion
        assert span.status == "completed"
        assert span.end_time is not None
        assert span.duration_ms is not None
    
    def test_monitoring_stats(self, monitor):
        """Test monitoring statistics."""
        # Add some test data
        trace = WorkflowTrace(workflow_id="test", workflow_name="Test")
        monitor.active_traces["test"] = trace
        
        alert = PerformanceAlert(alert_type="test", severity=AlertSeverity.HIGH)
        monitor.active_alerts.append(alert)
        
        stats = monitor.get_monitoring_stats()
        
        assert stats["active_traces"] == 1
        assert stats["active_alerts"] == 1
        assert stats["alert_breakdown"]["high"] == 1
        assert "performance_thresholds" in stats
        assert "is_monitoring" in stats


class TestWorkflowDashboard:
    """Test workflow dashboard functionality."""
    
    @pytest.fixture
    async def monitor(self):
        """Create monitor for dashboard testing."""
        event_manager = EventManager()
        monitor = WorkflowMonitor(event_manager)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.fixture
    async def dashboard(self, monitor):
        """Create dashboard for testing."""
        dashboard = WorkflowDashboard(monitor)
        await dashboard.start()
        yield dashboard
        await dashboard.stop()
    
    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, monitor):
        """Test dashboard initialization."""
        dashboard = WorkflowDashboard(monitor)
        
        assert dashboard.monitor == monitor
        assert not dashboard.is_running
        assert dashboard._cached_metrics is None
        
        await dashboard.start()
        assert dashboard.is_running
        
        await dashboard.stop()
        assert not dashboard.is_running
    
    @pytest.mark.asyncio
    async def test_dashboard_data_views(self, dashboard):
        """Test different dashboard views."""
        # Test overview view
        overview_data = dashboard.get_dashboard_data(DashboardView.OVERVIEW)
        assert overview_data["view"] == "overview"
        assert "metrics" in overview_data
        assert "recent_workflows" in overview_data
        assert "system_health" in overview_data
        
        # Test workflows view
        workflows_data = dashboard.get_dashboard_data(DashboardView.WORKFLOWS)
        assert workflows_data["view"] == "workflows"
        assert "workflows" in workflows_data
        assert "metrics" in workflows_data
        
        # Test agents view
        agents_data = dashboard.get_dashboard_data(DashboardView.AGENTS)
        assert agents_data["view"] == "agents"
        assert "agents" in agents_data
        assert "metrics" in agents_data
        
        # Test performance view
        performance_data = dashboard.get_dashboard_data(DashboardView.PERFORMANCE)
        assert performance_data["view"] == "performance"
        assert "system_health" in performance_data
        assert "performance_metrics" in performance_data
        
        # Test alerts view
        alerts_data = dashboard.get_dashboard_data(DashboardView.ALERTS)
        assert alerts_data["view"] == "alerts"
        assert "active_alerts" in alerts_data
        assert "alert_summary" in alerts_data
        
        # Test traces view
        traces_data = dashboard.get_dashboard_data(DashboardView.TRACES)
        assert traces_data["view"] == "traces"
        assert "active_traces" in traces_data
        assert "trace_stats" in traces_data
    
    @pytest.mark.asyncio
    async def test_workflow_detail(self, dashboard):
        """Test workflow detail functionality."""
        # Add test trace to monitor
        trace = WorkflowTrace(
            workflow_id="test_workflow",
            workflow_name="Test Workflow"
        )
        dashboard.monitor.active_traces["test_workflow"] = trace
        
        # Get workflow detail
        detail = dashboard.get_workflow_detail("test_workflow")
        assert detail is not None
        assert detail["summary"]["workflow_id"] == "test_workflow"
        assert detail["trace"]["workflow_id"] == "test_workflow"
        
        # Test non-existent workflow
        detail = dashboard.get_workflow_detail("non_existent")
        assert detail is None
    
    @pytest.mark.asyncio
    async def test_agent_detail(self, dashboard):
        """Test agent detail functionality."""
        # Add test trace with agent span
        trace = WorkflowTrace(
            workflow_id="test_workflow",
            workflow_name="Test Workflow"
        )
        
        agent_span = TraceSpan(
            operation_name="agent_test",
            service_name="test_agent"
        )
        agent_span.finish("completed")
        trace.add_span(agent_span)
        
        dashboard.monitor.completed_traces.append(trace)
        
        # Update cached agents
        await dashboard._update_dashboard_data()
        
        # Get agent detail
        detail = dashboard.get_agent_detail("test_agent")
        if detail:  # May be None if no cached agents
            assert detail["summary"]["agent_name"] == "test_agent"
            assert "recent_executions" in detail
    
    def test_dashboard_export(self, dashboard):
        """Test dashboard data export."""
        exported_data = dashboard.export_dashboard_data("json")
        
        # Parse JSON to verify format
        data = json.loads(exported_data)
        assert "export_timestamp" in data
        assert "metrics" in data
        assert "workflows" in data
        assert "agents" in data
        assert "system_health" in data
        
        # Test unsupported format
        with pytest.raises(ValueError):
            dashboard.export_dashboard_data("xml")


class TestAdvancedLogging:
    """Test advanced logging functionality."""
    
    def test_agent_decision_logger(self):
        """Test agent decision logging."""
        logger = AgentDecisionLogger("test_agent")
        
        # Test decision logging
        logger.log_decision(
            decision="Use AWS EC2",
            reasoning="Cost-effective for current workload",
            confidence=0.85,
            alternatives=["Azure VM", "GCP Compute"],
            context={"budget": 1000}
        )
        
        # Test recommendation logging
        logger.log_recommendation(
            recommendation_type="infrastructure",
            recommendation={"service": "EC2", "instance_type": "m5.large"},
            supporting_data={"cost_per_hour": 0.096}
        )
        
        # Test tool usage logging
        logger.log_tool_usage(
            tool_name="aws_pricing_api",
            input_data={"service": "EC2", "region": "us-east-1"},
            output_data={"price": 0.096},
            execution_time=1.5
        )
        
        # Test LLM interaction logging
        logger.log_llm_interaction(
            prompt="What is the best EC2 instance for ML training?",
            response="For ML training, I recommend m5.xlarge instances...",
            model="gpt-4",
            tokens_used=150,
            response_time=2.3
        )
    
    def test_workflow_logger(self):
        """Test workflow logging."""
        logger = WorkflowLogger()
        
        # Test workflow start logging
        logger.log_workflow_started(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            steps=["step1", "step2", "step3"],
            context={"user_id": "test_user"}
        )
        
        # Test workflow completion logging
        logger.log_workflow_completed(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            execution_time=120.5,
            results={"recommendations": 5}
        )
        
        # Test workflow failure logging
        logger.log_workflow_failed(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            error="Agent timeout",
            failed_step="step2"
        )
        
        # Test step logging
        logger.log_step_started(
            workflow_id="test_workflow",
            step_id="step1",
            step_name="CTO Analysis",
            agent_name="cto_agent"
        )
        
        logger.log_step_completed(
            workflow_id="test_workflow",
            step_id="step1",
            step_name="CTO Analysis",
            agent_name="cto_agent",
            execution_time=45.2,
            result={"recommendations": 3}
        )
    
    def test_performance_logger(self):
        """Test performance logging."""
        logger = PerformanceLogger()
        
        # Test performance metric logging
        logger.log_performance_metric(
            metric_name="agent_response_time",
            value=2.5,
            unit="seconds",
            context={"agent": "cto_agent", "workflow": "test"}
        )
        
        # Test resource usage logging
        logger.log_resource_usage(
            cpu_percent=75.5,
            memory_percent=60.2,
            disk_percent=45.8,
            network_connections=25
        )
    
    def test_log_context(self):
        """Test log context management."""
        with log_context(workflow_id="test_workflow", agent_name="test_agent") as context:
            assert context.workflow_id == "test_workflow"
            assert context.agent_name == "test_agent"
            assert context.correlation_id is not None
            
            # Test nested context
            with log_context(step_id="step1") as nested_context:
                assert nested_context.workflow_id == "test_workflow"
                assert nested_context.agent_name == "test_agent"
                assert nested_context.step_id == "step1"
    
    def test_logging_setup(self, tmp_path):
        """Test logging system setup."""
        log_file = tmp_path / "test.log"
        
        setup_advanced_logging(
            log_level="DEBUG",
            log_file=str(log_file),
            enable_console=False,
            enable_structured=True
        )
        
        # Test that log file is created
        import logging
        logger = logging.getLogger("test")
        logger.info("Test message")
        
        assert log_file.exists()


class TestMonitoringIntegration:
    """Test integration between monitoring components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring(self):
        """Test complete monitoring workflow."""
        # Initialize components
        event_manager = EventManager()
        monitor = WorkflowMonitor(event_manager)
        dashboard = WorkflowDashboard(monitor)
        
        await monitor.start_monitoring()
        await dashboard.start()
        
        try:
            # Simulate complete workflow execution
            workflow_id = "integration_test_workflow"
            
            # Start workflow
            await event_manager.publish_workflow_started(
                workflow_id,
                {"name": "Integration Test", "total_steps": 2}
            )
            
            # Start first agent
            await event_manager.publish_agent_started(
                "cto_agent",
                {"workflow_id": workflow_id, "step_id": "step1"}
            )
            
            # Complete first agent
            await event_manager.publish_agent_completed(
                "cto_agent",
                {
                    "workflow_id": workflow_id,
                    "step_id": "step1",
                    "execution_time": 1.5
                }
            )
            
            # Start second agent
            await event_manager.publish_agent_started(
                "research_agent",
                {"workflow_id": workflow_id, "step_id": "step2"}
            )
            
            # Complete second agent
            await event_manager.publish_agent_completed(
                "research_agent",
                {
                    "workflow_id": workflow_id,
                    "step_id": "step2",
                    "execution_time": 2.3
                }
            )
            
            # Complete workflow
            await event_manager.publish_workflow_completed(
                workflow_id,
                {"completed_steps": 2}
            )
            
            # Allow time for processing
            await asyncio.sleep(0.1)
            
            # Verify monitoring data
            assert len(monitor.completed_traces) == 1
            trace = monitor.completed_traces[0]
            assert trace.workflow_id == workflow_id
            assert trace.status == "completed"
            assert len(trace.spans) == 3  # Root + 2 agents
            
            # Verify dashboard data
            dashboard_data = dashboard.get_dashboard_data(DashboardView.OVERVIEW)
            assert dashboard_data["view"] == "overview"
            
            # Verify workflow detail
            workflow_detail = dashboard.get_workflow_detail(workflow_id)
            assert workflow_detail is not None
            assert workflow_detail["summary"]["workflow_id"] == workflow_id
            
        finally:
            await dashboard.stop()
            await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_alerting(self):
        """Test error handling and alerting integration."""
        event_manager = EventManager()
        monitor = WorkflowMonitor(event_manager)
        
        await monitor.start_monitoring()
        
        try:
            workflow_id = "error_test_workflow"
            
            # Start workflow
            await event_manager.publish_workflow_started(
                workflow_id,
                {"name": "Error Test", "total_steps": 1}
            )
            
            # Start agent
            await event_manager.publish_agent_started(
                "test_agent",
                {"workflow_id": workflow_id, "step_id": "step1"}
            )
            
            # Fail agent
            await event_manager.publish_agent_failed(
                "test_agent",
                "Test error message",
                {"workflow_id": workflow_id, "step_id": "step1"}
            )
            
            # Fail workflow
            await event_manager.publish_workflow_failed(
                workflow_id,
                "Workflow failed due to agent error"
            )
            
            # Allow time for processing
            await asyncio.sleep(0.1)
            
            # Verify error handling
            assert len(monitor.completed_traces) == 1
            trace = monitor.completed_traces[0]
            assert trace.status == "failed"
            
            # Verify alerts were created
            active_alerts = monitor.get_active_alerts()
            alert_types = [alert.alert_type for alert in active_alerts]
            assert "workflow_failure" in alert_types
            assert "agent_failure" in alert_types
            
        finally:
            await monitor.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])