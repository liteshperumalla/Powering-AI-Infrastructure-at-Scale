"""
Integration tests for metrics collection system.

Tests the integration of metrics collection with other system components.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.infra_mind.core.metrics_collector import (
    MetricsCollector,
    get_metrics_collector,
    initialize_metrics_collection,
    shutdown_metrics_collection
)
from src.infra_mind.core.metrics_middleware import (
    MetricsMiddleware,
    HealthCheckMiddleware,
    MetricsEndpointMiddleware
)
from src.infra_mind.models.metrics import Metric, AgentMetrics, MetricType, MetricCategory
from src.infra_mind.agents.base import BaseAgent, AgentConfig, AgentRole


class TestMetricsIntegration:
    """Test metrics integration with other system components."""
    
    @pytest_asyncio.fixture
    async def metrics_collector(self):
        """Create a metrics collector for testing."""
        collector = get_metrics_collector()
        await initialize_metrics_collection()
        yield collector
        await shutdown_metrics_collection()
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.AgentMetrics.create_for_agent')
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_agent_metrics_integration(self, mock_record_metric, mock_create_agent, metrics_collector):
        """Test integration of metrics with agent system."""
        # Mock agent metrics
        mock_agent_metrics = Mock()
        mock_agent_metrics.save = AsyncMock()
        mock_agent_metrics.update_performance = Mock()
        mock_agent_metrics.update_quality = Mock()
        mock_agent_metrics.update_output = Mock()
        mock_create_agent.return_value = mock_agent_metrics
        mock_record_metric.return_value = AsyncMock()
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment_id"
        
        # Record agent performance
        await metrics_collector.record_agent_performance(
            agent_name="test_agent",
            execution_time=2.5,
            success=True,
            confidence_score=0.85,
            recommendations_count=3,
            assessment_id=str(mock_assessment.id)
        )
        
        # Verify agent metrics were created and updated
        mock_create_agent.assert_called_once()
        mock_agent_metrics.update_performance.assert_called_once()
        mock_agent_metrics.update_quality.assert_called_once()
        mock_agent_metrics.update_output.assert_called_once()
        mock_agent_metrics.save.assert_called_once()
        
        # Verify general metrics were recorded
        assert mock_record_metric.call_count >= 2  # execution_time and confidence_score
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.psutil')
    async def test_system_health_integration(self, mock_psutil, metrics_collector):
        """Test system health monitoring integration."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.0
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        mock_psutil.disk_usage.return_value = Mock(used=500000000000, total=1000000000000)
        mock_psutil.net_connections.return_value = [Mock()] * 20
        
        # Set up test data
        metrics_collector._request_times = [100, 150, 200]
        metrics_collector._request_count = 100
        metrics_collector._error_count = 2
        
        # Get system health
        health = await metrics_collector.get_system_health()
        
        # Verify health status
        assert health.cpu_usage_percent == 45.0
        assert health.memory_usage_percent == 60.0
        assert health.disk_usage_percent == 50.0
        assert health.active_connections == 20
        assert health.error_rate_percent == 2.0
        assert health.status == "healthy"
    
    @pytest.mark.asyncio
    async def test_user_engagement_integration(self, metrics_collector):
        """Test user engagement tracking integration."""
        # Track user actions
        metrics_collector.track_user_action(
            user_id="user1",
            action_type="assessment_started",
            metadata={"source": "web"}
        )
        
        metrics_collector.track_user_action(
            user_id="user2",
            action_type="dashboard_viewed",
            metadata={"page": "main"}
        )
        
        metrics_collector.track_user_action(
            user_id="user1",
            action_type="assessment_completed",
            metadata={"duration": 300}
        )
        
        # Get engagement summary
        engagement = await metrics_collector.get_user_engagement_summary()
        
        # Verify engagement metrics
        assert engagement.active_users_count == 2
        assert engagement.assessments_started == 1
        assert engagement.assessments_completed == 1
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_operation_tracking_integration(self, mock_record_metric, metrics_collector):
        """Test operation tracking integration."""
        mock_record_metric.return_value = AsyncMock()
        
        # Track operation with context manager
        async with metrics_collector.track_operation("test_operation"):
            await asyncio.sleep(0.1)  # Simulate work
        
        # Verify metrics were recorded
        mock_record_metric.assert_called_once()
        call_args = mock_record_metric.call_args
        assert call_args[1]['name'] == "operation.test_operation.duration"
        assert call_args[1]['dimensions']['success'] is True


class TestMetricsMiddlewareIntegration:
    """Test metrics middleware integration."""
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.get_metrics_collector')
    async def test_metrics_middleware_request_tracking(self, mock_get_collector):
        """Test metrics middleware request tracking."""
        # Mock collector
        mock_collector = Mock()
        mock_collector.track_request = Mock()
        mock_collector.track_user_action = Mock()
        mock_get_collector.return_value = mock_collector
        
        # Create middleware
        middleware = MetricsMiddleware(app=Mock())
        
        # Mock request and response
        mock_request = Mock()
        mock_request.url.path = "/api/assessments"
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.state = Mock()
        mock_request.state.user = Mock()
        mock_request.state.user.id = "test_user_id"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        # Mock call_next function
        async def mock_call_next(request):
            return mock_response
        
        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify request was tracked
        mock_collector.track_request.assert_called_once()
        
        # Verify user action was tracked
        mock_collector.track_user_action.assert_called_once()
        
        # Verify response headers were added
        assert "X-Response-Time" in response.headers
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.get_metrics_collector')
    async def test_health_check_middleware(self, mock_get_collector):
        """Test health check middleware."""
        # Mock collector
        mock_collector = Mock()
        mock_collector.get_system_health = AsyncMock()
        mock_collector.get_system_health.return_value = Mock(
            status="healthy",
            cpu_usage_percent=45.0,
            memory_usage_percent=60.0,
            disk_usage_percent=50.0,
            active_connections=20,
            response_time_ms=150.0,
            error_rate_percent=2.0,
            uptime_seconds=3600,
            timestamp=datetime.utcnow()
        )
        mock_get_collector.return_value = mock_collector
        
        # Create middleware
        middleware = HealthCheckMiddleware(app=Mock())
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/health"
        
        # Process request
        response = await middleware.dispatch(mock_request, None)
        
        # Verify health check was performed
        mock_collector.get_system_health.assert_called_once()
        
        # Verify response
        assert response.status_code == 200
        assert "status" in response.body.decode()
        assert "system" in response.body.decode()
        assert "performance" in response.body.decode()
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.get_metrics_collector')
    async def test_metrics_endpoint_middleware(self, mock_get_collector):
        """Test metrics endpoint middleware."""
        # Mock collector
        mock_collector = Mock()
        mock_collector.get_system_health = AsyncMock()
        mock_collector.get_system_health.return_value = Mock(
            status="healthy",
            cpu_usage_percent=45.0,
            memory_usage_percent=60.0,
            disk_usage_percent=50.0,
            active_connections=20,
            response_time_ms=150.0,
            error_rate_percent=2.0,
            uptime_seconds=3600,
            timestamp=datetime.utcnow()
        )
        mock_collector.get_user_engagement_summary = AsyncMock()
        mock_collector.get_user_engagement_summary.return_value = Mock(
            active_users_count=5,
            assessments_started=3,
            assessments_completed=2,
            reports_generated=1,
            average_session_duration_minutes=15.0,
            bounce_rate_percent=20.0
        )
        mock_get_collector.return_value = mock_collector
        
        # Create middleware
        middleware = MetricsEndpointMiddleware(app=Mock())
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/metrics"
        
        # Process request
        response = await middleware.dispatch(mock_request, None)
        
        # Verify metrics were collected
        mock_collector.get_system_health.assert_called_once()
        mock_collector.get_user_engagement_summary.assert_called_once()
        
        # Verify response
        assert response.status_code == 200
        assert "system_health" in response.body.decode()
        assert "user_engagement" in response.body.decode()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])