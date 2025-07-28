"""
Tests for metrics collection system.

Tests basic metrics collection for system performance, user engagement,
and system health monitoring as required by task 12.1.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.infra_mind.core.metrics_collector import (
    MetricsCollector, 
    SystemHealthStatus, 
    UserEngagementMetrics,
    get_metrics_collector,
    initialize_metrics_collection,
    shutdown_metrics_collection
)
from src.infra_mind.models.metrics import Metric, AgentMetrics, MetricType, MetricCategory


class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    @pytest_asyncio.fixture
    async def metrics_collector(self):
        """Create a metrics collector for testing."""
        collector = MetricsCollector()
        yield collector
        # Cleanup
        if collector.is_collecting:
            await collector.stop_collection()
    
    @pytest.mark.asyncio
    async def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initialization."""
        assert metrics_collector.collection_interval == 60
        assert not metrics_collector.is_collecting
        assert metrics_collector._collection_task is None
        assert isinstance(metrics_collector.start_time, datetime)
    
    @pytest.mark.asyncio
    async def test_start_stop_collection(self, metrics_collector):
        """Test starting and stopping metrics collection."""
        # Start collection
        await metrics_collector.start_collection()
        assert metrics_collector.is_collecting
        assert metrics_collector._collection_task is not None
        
        # Stop collection
        await metrics_collector.stop_collection()
        assert not metrics_collector.is_collecting
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.psutil')
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_collect_system_metrics(self, mock_record_metric, mock_psutil, metrics_collector):
        """Test system metrics collection."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value = Mock(
            percent=60.2,
            total=8589934592,  # 8GB
            available=3221225472  # 3GB
        )
        mock_psutil.disk_usage.return_value = Mock(
            total=1000000000000,  # 1TB
            used=500000000000,    # 500GB
            free=500000000000     # 500GB
        )
        mock_psutil.net_connections.return_value = [Mock()] * 25
        mock_psutil.Process.return_value.memory_info.return_value.rss = 104857600  # 100MB
        
        mock_record_metric.return_value = AsyncMock()
        
        # Collect metrics
        await metrics_collector.collect_system_metrics()
        
        # Verify metrics were recorded
        assert mock_record_metric.call_count >= 5  # CPU, memory, disk, network, process
        
        # Check specific metric calls
        calls = mock_record_metric.call_args_list
        metric_names = [call[1]['name'] for call in calls]
        
        assert "system.cpu.usage_percent" in metric_names
        assert "system.memory.usage_percent" in metric_names
        assert "system.disk.usage_percent" in metric_names
        assert "system.network.active_connections" in metric_names
        assert "system.process.memory_mb" in metric_names
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_collect_health_metrics(self, mock_record_metric, metrics_collector):
        """Test health metrics collection."""
        mock_record_metric.return_value = AsyncMock()
        
        # Set up some test data
        metrics_collector._request_count = 100
        metrics_collector._error_count = 5
        metrics_collector._request_times = [100, 150, 200, 120, 180]
        
        # Collect health metrics
        await metrics_collector.collect_health_metrics()
        
        # Verify metrics were recorded
        assert mock_record_metric.call_count >= 3  # uptime, error_rate, response_time, health_score
        
        # Check specific metrics
        calls = mock_record_metric.call_args_list
        metric_names = [call[1]['name'] for call in calls]
        
        assert "system.uptime_seconds" in metric_names
        assert "system.error_rate_percent" in metric_names
        assert "system.avg_response_time_ms" in metric_names
        assert "system.health_score" in metric_names
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_collect_user_engagement_metrics(self, mock_record_metric, metrics_collector):
        """Test user engagement metrics collection."""
        mock_record_metric.return_value = AsyncMock()
        
        # Set up test user data
        now = datetime.utcnow()
        metrics_collector._active_sessions = {
            "user1": now - timedelta(minutes=5),
            "user2": now - timedelta(minutes=45),  # Should be considered inactive
            "user3": now - timedelta(minutes=10)
        }
        
        metrics_collector._user_actions = [
            {"user_id": "user1", "type": "assessment_started", "timestamp": now - timedelta(minutes=30)},
            {"user_id": "user2", "type": "report_generated", "timestamp": now - timedelta(minutes=15)},
            {"user_id": "user3", "type": "dashboard_viewed", "timestamp": now - timedelta(minutes=5)}
        ]
        
        # Collect engagement metrics
        await metrics_collector.collect_user_engagement_metrics()
        
        # Verify metrics were recorded
        assert mock_record_metric.call_count >= 2  # active_sessions, actions_per_hour, action types
        
        # Check specific metrics
        calls = mock_record_metric.call_args_list
        metric_names = [call[1]['name'] for call in calls]
        
        assert "user.active_sessions" in metric_names
        assert "user.actions_per_hour" in metric_names
    
    @pytest.mark.asyncio
    async def test_track_request(self, metrics_collector):
        """Test request tracking."""
        # Track successful request
        metrics_collector.track_request(150.5, success=True)
        assert len(metrics_collector._request_times) == 1
        assert metrics_collector._request_count == 1
        assert metrics_collector._error_count == 0
        
        # Track failed request
        metrics_collector.track_request(300.0, success=False)
        assert len(metrics_collector._request_times) == 2
        assert metrics_collector._request_count == 2
        assert metrics_collector._error_count == 1
    
    @pytest.mark.asyncio
    async def test_track_user_action(self, metrics_collector):
        """Test user action tracking."""
        # Track user action
        metrics_collector.track_user_action(
            user_id="test_user",
            action_type="assessment_started",
            metadata={"source": "web"}
        )
        
        assert len(metrics_collector._user_actions) == 1
        assert "test_user" in metrics_collector._active_sessions
        
        action = metrics_collector._user_actions[0]
        assert action["user_id"] == "test_user"
        assert action["type"] == "assessment_started"
        assert action["metadata"]["source"] == "web"
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.AgentMetrics.create_for_agent')
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_record_agent_performance(self, mock_record_metric, mock_create_agent, metrics_collector):
        """Test agent performance recording."""
        # Mock agent metrics
        mock_agent_metrics = Mock()
        mock_agent_metrics.save = AsyncMock()
        mock_create_agent.return_value = mock_agent_metrics
        mock_record_metric.return_value = AsyncMock()
        
        # Record agent performance
        await metrics_collector.record_agent_performance(
            agent_name="test_agent",
            execution_time=2.5,
            success=True,
            confidence_score=0.85,
            recommendations_count=3,
            assessment_id="test_assessment"
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
    async def test_get_system_health(self, mock_psutil, metrics_collector):
        """Test system health status retrieval."""
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
        
        assert isinstance(health, SystemHealthStatus)
        assert health.cpu_usage_percent == 45.0
        assert health.memory_usage_percent == 60.0
        assert health.disk_usage_percent == 50.0
        assert health.active_connections == 20
        assert health.error_rate_percent == 2.0
        assert health.status == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_summary(self, metrics_collector):
        """Test user engagement summary retrieval."""
        # Set up test data
        now = datetime.utcnow()
        metrics_collector._active_sessions = {
            "user1": now - timedelta(minutes=5),
            "user2": now - timedelta(minutes=10)
        }
        
        metrics_collector._user_actions = [
            {"user_id": "user1", "type": "assessment_started", "timestamp": now - timedelta(minutes=30)},
            {"user_id": "user2", "type": "assessment_completed", "timestamp": now - timedelta(minutes=15)},
            {"user_id": "user3", "type": "report_generated", "timestamp": now - timedelta(minutes=5)}
        ]
        
        # Get engagement summary
        engagement = await metrics_collector.get_user_engagement_summary()
        
        assert isinstance(engagement, UserEngagementMetrics)
        assert engagement.active_users_count == 2
        assert engagement.assessments_started == 1
        assert engagement.assessments_completed == 1
        assert engagement.reports_generated == 1
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.models.metrics.Metric.record_metric')
    async def test_track_operation_context_manager(self, mock_record_metric, metrics_collector):
        """Test operation tracking context manager."""
        mock_record_metric.return_value = AsyncMock()
        
        # Test successful operation
        async with metrics_collector.track_operation("test_operation"):
            await asyncio.sleep(0.1)  # Simulate work
        
        # Verify metrics were recorded
        mock_record_metric.assert_called_once()
        call_args = mock_record_metric.call_args
        assert call_args[1]['name'] == "operation.test_operation.duration"
        assert call_args[1]['dimensions']['success'] is True
        
        # Test failed operation
        mock_record_metric.reset_mock()
        
        with pytest.raises(ValueError):
            async with metrics_collector.track_operation("failing_operation"):
                raise ValueError("Test error")
        
        # Verify failure was recorded
        mock_record_metric.assert_called_once()
        call_args = mock_record_metric.call_args
        assert call_args[1]['name'] == "operation.failing_operation.duration"
        assert call_args[1]['dimensions']['success'] is False


class TestMetricsIntegration:
    """Test metrics integration with the system."""
    
    @pytest.mark.asyncio
    async def test_global_metrics_collector(self):
        """Test global metrics collector instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        # Should return the same instance
        assert collector1 is collector2
    
    @pytest.mark.asyncio
    @patch('src.infra_mind.core.metrics_collector.get_metrics_collector')
    async def test_initialize_shutdown_metrics_collection(self, mock_get_collector):
        """Test metrics collection initialization and shutdown."""
        mock_collector = Mock()
        mock_collector.start_collection = AsyncMock()
        mock_collector.stop_collection = AsyncMock()
        mock_get_collector.return_value = mock_collector
        
        # Test initialization
        await initialize_metrics_collection()
        mock_collector.start_collection.assert_called_once()
        
        # Test shutdown
        await shutdown_metrics_collection()
        mock_collector.stop_collection.assert_called_once()


class TestMetricsModels:
    """Test metrics data models."""
    
    @pytest.mark.asyncio
    async def test_metric_record_metric(self):
        """Test Metric.record_metric class method."""
        with patch('src.infra_mind.models.metrics.Metric.insert') as mock_insert:
            mock_insert.return_value = AsyncMock()
            
            metric = await Metric.record_metric(
                name="test.metric",
                value=42.5,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="ms",
                source="test_source"
            )
            
            assert metric.name == "test.metric"
            assert metric.value == 42.5
            assert metric.metric_type == MetricType.SYSTEM_PERFORMANCE
            assert metric.category == MetricCategory.TECHNICAL
            assert metric.unit == "ms"
            assert metric.source == "test_source"
            
            mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_metrics_creation(self):
        """Test AgentMetrics creation and updates."""
        with patch('src.infra_mind.models.metrics.AgentMetrics.insert') as mock_insert:
            mock_insert.return_value = AsyncMock()
            
            started_at = datetime.utcnow()
            agent_metrics = await AgentMetrics.create_for_agent(
                agent_name="test_agent",
                agent_version="1.0.0",
                started_at=started_at,
                assessment_id="test_assessment"
            )
            
            assert agent_metrics.agent_name == "test_agent"
            assert agent_metrics.agent_version == "1.0.0"
            assert agent_metrics.started_at == started_at
            assert agent_metrics.assessment_id == "test_assessment"
            
            # Test performance update
            agent_metrics.update_performance(
                execution_time=2.5,
                memory_usage=128.0,
                api_calls=5
            )
            
            assert agent_metrics.execution_time_seconds == 2.5
            assert agent_metrics.memory_usage_mb == 128.0
            assert agent_metrics.api_calls_made == 5
            
            # Test quality update
            agent_metrics.update_quality(
                confidence_score=0.85,
                validation_score=0.90,
                user_feedback=4.5
            )
            
            assert agent_metrics.confidence_score == 0.85
            assert agent_metrics.validation_score == 0.90
            assert agent_metrics.user_feedback_score == 4.5
            
            # Test output update
            agent_metrics.update_output(
                recommendations=3,
                services=5,
                cost_estimates=2
            )
            
            assert agent_metrics.recommendations_generated == 3
            assert agent_metrics.services_recommended == 5
            assert agent_metrics.cost_estimates_provided == 2
            
            # Test error recording
            agent_metrics.record_error(error_count=2, warning_count=1)
            
            assert agent_metrics.errors_encountered == 2
            assert agent_metrics.warnings_generated == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])