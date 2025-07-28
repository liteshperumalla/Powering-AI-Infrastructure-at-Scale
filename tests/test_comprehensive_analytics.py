"""
Tests for Comprehensive Analytics Dashboard.

Tests the advanced analytics dashboard functionality including user behavior analysis,
recommendation quality tracking, system performance monitoring, and alerting.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.infra_mind.orchestration.analytics_dashboard import (
    AnalyticsDashboard, AnalyticsTimeframe, UserAnalytics,
    RecommendationQualityMetrics, SystemPerformanceAnalytics,
    AlertAnalytics, TrendAnalysis, MetricTrend, ComprehensiveAnalytics
)
from src.infra_mind.orchestration.monitoring import WorkflowMonitor, PerformanceAlert, AlertSeverity
from src.infra_mind.orchestration.dashboard import WorkflowDashboard
from src.infra_mind.core.metrics_collector import MetricsCollector


@pytest.fixture
def mock_workflow_monitor():
    """Create mock workflow monitor."""
    monitor = Mock(spec=WorkflowMonitor)
    monitor.get_active_traces.return_value = []
    monitor.get_completed_traces.return_value = []
    monitor.get_active_alerts.return_value = []
    monitor.get_all_alerts.return_value = []
    monitor.get_monitoring_stats.return_value = {
        "active_traces": 0,
        "completed_traces": 0,
        "active_spans": 0,
        "active_alerts": 0
    }
    return monitor


@pytest.fixture
def mock_workflow_dashboard():
    """Create mock workflow dashboard."""
    dashboard = Mock(spec=WorkflowDashboard)
    return dashboard


@pytest.fixture
def mock_metrics_collector():
    """Create mock metrics collector."""
    collector = Mock(spec=MetricsCollector)
    collector.get_system_health = AsyncMock()
    collector.get_user_engagement_summary = AsyncMock()
    return collector


@pytest.fixture
async def analytics_dashboard(mock_workflow_monitor, mock_workflow_dashboard):
    """Create analytics dashboard instance."""
    dashboard = AnalyticsDashboard(mock_workflow_monitor, mock_workflow_dashboard)
    yield dashboard
    await dashboard.stop()


class TestTrendAnalysis:
    """Test trend analysis functionality."""
    
    def test_trend_analysis_calculation_up_trend(self):
        """Test trend analysis with upward trend."""
        values = [10, 12, 14, 16, 18]
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 18
        assert trend.previous_value == 16
        assert trend.change_percent == 12.5  # (18-16)/16 * 100
        assert trend.trend == MetricTrend.UP
        assert trend.data_points == 5
        assert 0 <= trend.confidence <= 1
    
    def test_trend_analysis_calculation_down_trend(self):
        """Test trend analysis with downward trend."""
        values = [20, 18, 16, 14, 12]
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 12
        assert trend.previous_value == 14
        assert trend.change_percent == -14.285714285714286  # (12-14)/14 * 100
        assert trend.trend == MetricTrend.DOWN
        assert trend.data_points == 5
    
    def test_trend_analysis_calculation_stable_trend(self):
        """Test trend analysis with stable trend."""
        values = [10, 10.2, 9.8, 10.1, 10]
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 10
        assert trend.previous_value == 10.1
        assert abs(trend.change_percent) < 5  # Should be stable
        assert trend.trend == MetricTrend.STABLE
        assert trend.data_points == 5
    
    def test_trend_analysis_calculation_volatile_trend(self):
        """Test trend analysis with volatile trend."""
        values = [10, 20, 5, 25, 8, 30, 3, 28, 12, 35]
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 35
        assert trend.previous_value == 12
        assert trend.trend == MetricTrend.VOLATILE
        assert trend.data_points == 10
    
    def test_trend_analysis_single_value(self):
        """Test trend analysis with single value."""
        values = [15]
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 15
        assert trend.previous_value == 0
        assert trend.change_percent == 0
        assert trend.trend == MetricTrend.STABLE
        assert trend.confidence == 0
        assert trend.data_points == 1
    
    def test_trend_analysis_empty_values(self):
        """Test trend analysis with empty values."""
        values = []
        trend = TrendAnalysis.calculate(values)
        
        assert trend.current_value == 0
        assert trend.previous_value == 0
        assert trend.change_percent == 0
        assert trend.trend == MetricTrend.STABLE
        assert trend.confidence == 0
        assert trend.data_points == 0


class TestAnalyticsDashboard:
    """Test analytics dashboard functionality."""
    
    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, mock_workflow_monitor, mock_workflow_dashboard):
        """Test analytics dashboard initialization."""
        dashboard = AnalyticsDashboard(mock_workflow_monitor, mock_workflow_dashboard)
        
        assert dashboard.workflow_monitor == mock_workflow_monitor
        assert dashboard.workflow_dashboard == mock_workflow_dashboard
        assert not dashboard.is_running
        assert dashboard.cached_analytics is None
        assert dashboard.last_update is None
    
    @pytest.mark.asyncio
    async def test_dashboard_start_stop(self, analytics_dashboard):
        """Test dashboard start and stop functionality."""
        # Test start
        await analytics_dashboard.start()
        assert analytics_dashboard.is_running
        assert analytics_dashboard._analytics_task is not None
        
        # Test stop
        await analytics_dashboard.stop()
        assert not analytics_dashboard.is_running
    
    @pytest.mark.asyncio
    async def test_dashboard_start_already_running(self, analytics_dashboard):
        """Test starting dashboard when already running."""
        await analytics_dashboard.start()
        
        # Try to start again
        await analytics_dashboard.start()  # Should not raise error
        assert analytics_dashboard.is_running
    
    @pytest.mark.asyncio
    async def test_user_behavior_analysis(self, analytics_dashboard):
        """Test user behavior analysis."""
        # Mock metrics collector
        with patch.object(analytics_dashboard, 'metrics_collector') as mock_collector:
            mock_engagement = Mock()
            mock_engagement.active_users_count = 50
            mock_engagement.new_users_count = 5
            mock_engagement.assessments_started = 25
            mock_engagement.assessments_completed = 20
            mock_engagement.reports_generated = 15
            mock_engagement.average_session_duration_minutes = 30.0
            mock_engagement.bounce_rate_percent = 15.0
            
            mock_collector.get_user_engagement_summary.return_value = mock_engagement
            
            user_analytics = await analytics_dashboard._analyze_user_behavior()
            
            assert isinstance(user_analytics, UserAnalytics)
            assert user_analytics.active_users_24h == 50
            assert user_analytics.new_users_24h == 5
            assert user_analytics.avg_session_duration_minutes == 30.0
            assert user_analytics.bounce_rate_percent == 15.0
            assert user_analytics.user_engagement_score > 0
            assert len(user_analytics.geographic_distribution) > 0
            assert len(user_analytics.company_size_distribution) > 0
            assert len(user_analytics.industry_distribution) > 0
    
    @pytest.mark.asyncio
    async def test_recommendation_quality_analysis(self, analytics_dashboard):
        """Test recommendation quality analysis."""
        # Mock workflow traces
        mock_trace = Mock()
        mock_trace.spans = []
        
        mock_span = Mock()
        mock_span.service_name = "test_agent"
        mock_span.status = "completed"
        mock_span.tags = {"confidence_score": 0.85}
        mock_trace.spans = [mock_span]
        
        analytics_dashboard.workflow_monitor.get_active_traces.return_value = []
        analytics_dashboard.workflow_monitor.get_completed_traces.return_value = [mock_trace]
        
        rec_quality = await analytics_dashboard._analyze_recommendation_quality()
        
        assert isinstance(rec_quality, RecommendationQualityMetrics)
        assert rec_quality.total_recommendations >= 0
        assert 0 <= rec_quality.avg_confidence_score <= 1
        assert 0 <= rec_quality.user_satisfaction_score <= 5
        assert 0 <= rec_quality.implementation_success_rate <= 1
        assert 0 <= rec_quality.recommendation_accuracy <= 1
        assert len(rec_quality.agent_performance_breakdown) >= 0
    
    @pytest.mark.asyncio
    async def test_system_performance_analysis(self, analytics_dashboard):
        """Test system performance analysis."""
        # Mock system health
        with patch.object(analytics_dashboard, 'metrics_collector') as mock_collector:
            mock_health = Mock()
            mock_health.response_time_ms = 500.0
            mock_health.error_rate_percent = 1.5
            mock_health.cpu_usage_percent = 45.0
            mock_health.memory_usage_percent = 60.0
            mock_health.disk_usage_percent = 30.0
            
            mock_collector.get_system_health.return_value = mock_health
            
            sys_perf = await analytics_dashboard._analyze_system_performance()
            
            assert isinstance(sys_perf, SystemPerformanceAnalytics)
            assert sys_perf.avg_response_time_ms == 500.0
            assert sys_perf.error_rate_percent == 1.5
            assert sys_perf.p95_response_time_ms > sys_perf.avg_response_time_ms
            assert sys_perf.p99_response_time_ms > sys_perf.p95_response_time_ms
            assert len(sys_perf.resource_utilization) > 0
            assert len(sys_perf.bottleneck_analysis) >= 0
            assert len(sys_perf.capacity_projections) > 0
    
    @pytest.mark.asyncio
    async def test_alert_analysis(self, analytics_dashboard):
        """Test alert analysis."""
        # Mock alerts
        mock_alert = Mock()
        mock_alert.timestamp = datetime.now(timezone.utc)
        mock_alert.resolved = False
        mock_alert.alert_type = "high_cpu"
        mock_alert.severity = AlertSeverity.HIGH
        
        analytics_dashboard.workflow_monitor.get_active_alerts.return_value = [mock_alert]
        analytics_dashboard.workflow_monitor.get_all_alerts.return_value = [mock_alert]
        
        alert_analytics = await analytics_dashboard._analyze_alerts()
        
        assert isinstance(alert_analytics, AlertAnalytics)
        assert alert_analytics.active_alerts >= 0
        assert alert_analytics.total_alerts_24h >= 0
        assert alert_analytics.resolved_alerts_24h >= 0
        assert alert_analytics.avg_resolution_time_minutes >= 0
        assert len(alert_analytics.alert_frequency_by_type) >= 0
        assert len(alert_analytics.alert_severity_distribution) >= 0
    
    @pytest.mark.asyncio
    async def test_business_metrics_calculation(self, analytics_dashboard):
        """Test business metrics calculation."""
        business_metrics = await analytics_dashboard._calculate_business_metrics()
        
        assert isinstance(business_metrics, dict)
        assert "user_metrics" in business_metrics
        assert "cost_metrics" in business_metrics
        assert "efficiency_metrics" in business_metrics
        assert "growth_metrics" in business_metrics
        
        user_metrics = business_metrics["user_metrics"]
        assert "monthly_active_users" in user_metrics
        assert "conversion_rate" in user_metrics
        assert "customer_lifetime_value" in user_metrics
        assert "churn_rate" in user_metrics
    
    @pytest.mark.asyncio
    async def test_operational_insights_generation(self, analytics_dashboard):
        """Test operational insights generation."""
        # Mock system health with issues
        with patch.object(analytics_dashboard, 'metrics_collector') as mock_collector:
            mock_health = Mock()
            mock_health.response_time_ms = 3000.0  # High response time
            mock_health.error_rate_percent = 1.0
            mock_health.cpu_usage_percent = 45.0
            mock_health.memory_usage_percent = 60.0
            
            mock_collector.get_system_health.return_value = mock_health
            
            insights = await analytics_dashboard._generate_operational_insights()
            
            assert isinstance(insights, list)
            # Should generate insight about high response time
            assert any("Response Time" in insight.get("title", "") for insight in insights)
            
            for insight in insights:
                assert "type" in insight
                assert "priority" in insight
                assert "title" in insight
                assert "description" in insight
                assert "recommendation" in insight
                assert "impact" in insight
                assert "estimated_effort" in insight
    
    @pytest.mark.asyncio
    async def test_predictive_analytics_generation(self, analytics_dashboard):
        """Test predictive analytics generation."""
        predictive = await analytics_dashboard._generate_predictive_analytics()
        
        assert isinstance(predictive, dict)
        assert "user_forecast" in predictive
        assert "load_forecast" in predictive
        assert "cost_forecast" in predictive
        assert "failure_prediction" in predictive
        assert "quality_forecast" in predictive
        assert "generated_at" in predictive
        assert "model_version" in predictive
        
        user_forecast = predictive["user_forecast"]
        assert "next_month" in user_forecast
        assert "next_quarter" in user_forecast
        assert "next_year" in user_forecast
        assert "confidence" in user_forecast
        assert 0 <= user_forecast["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_comprehensive_analytics_collection(self, analytics_dashboard):
        """Test comprehensive analytics data collection."""
        # Start dashboard to trigger data collection
        await analytics_dashboard.start()
        
        # Wait for initial collection
        await asyncio.sleep(0.1)
        
        # Mock the collection methods
        with patch.object(analytics_dashboard, '_analyze_user_behavior') as mock_user, \
             patch.object(analytics_dashboard, '_analyze_recommendation_quality') as mock_rec, \
             patch.object(analytics_dashboard, '_analyze_system_performance') as mock_sys, \
             patch.object(analytics_dashboard, '_analyze_alerts') as mock_alerts, \
             patch.object(analytics_dashboard, '_calculate_business_metrics') as mock_business, \
             patch.object(analytics_dashboard, '_generate_operational_insights') as mock_insights, \
             patch.object(analytics_dashboard, '_generate_predictive_analytics') as mock_predictive:
            
            mock_user.return_value = UserAnalytics()
            mock_rec.return_value = RecommendationQualityMetrics()
            mock_sys.return_value = SystemPerformanceAnalytics()
            mock_alerts.return_value = AlertAnalytics()
            mock_business.return_value = {}
            mock_insights.return_value = []
            mock_predictive.return_value = {}
            
            # Trigger collection
            await analytics_dashboard._collect_and_analyze()
            
            # Verify analytics were collected
            assert analytics_dashboard.cached_analytics is not None
            assert isinstance(analytics_dashboard.cached_analytics, ComprehensiveAnalytics)
            assert analytics_dashboard.last_update is not None
    
    def test_get_comprehensive_analytics(self, analytics_dashboard):
        """Test getting comprehensive analytics."""
        # Initially should return None
        analytics = analytics_dashboard.get_comprehensive_analytics()
        assert analytics is None
        
        # Set cached analytics
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        
        # Should return cached analytics
        analytics = analytics_dashboard.get_comprehensive_analytics(AnalyticsTimeframe.DAY)
        assert analytics is not None
        assert analytics.timeframe == AnalyticsTimeframe.DAY
    
    def test_get_historical_data(self, analytics_dashboard):
        """Test getting historical data."""
        # Add some historical data
        now = datetime.now(timezone.utc)
        analytics_dashboard.historical_data["test_metric"].extend([
            {"timestamp": now - timedelta(hours=2), "value": 10},
            {"timestamp": now - timedelta(hours=1), "value": 15},
            {"timestamp": now, "value": 20}
        ])
        
        # Get historical data
        data = analytics_dashboard.get_historical_data("test_metric", AnalyticsTimeframe.DAY)
        assert len(data) == 3
        assert all("timestamp" in item and "value" in item for item in data)
        
        # Test with non-existent metric
        data = analytics_dashboard.get_historical_data("non_existent", AnalyticsTimeframe.DAY)
        assert len(data) == 0
    
    def test_update_alert_threshold(self, analytics_dashboard):
        """Test updating alert thresholds."""
        # Test valid metric
        success = analytics_dashboard.update_alert_threshold("error_rate_percent", 10.0)
        assert success
        assert analytics_dashboard.alert_thresholds["error_rate_percent"] == 10.0
        
        # Test invalid metric
        success = analytics_dashboard.update_alert_threshold("invalid_metric", 5.0)
        assert not success
    
    def test_get_performance_comparison(self, analytics_dashboard):
        """Test performance comparison."""
        # Set cached analytics
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        analytics_dashboard.cached_analytics.system_performance.avg_response_time_ms = 1200.0
        analytics_dashboard.cached_analytics.system_performance.error_rate_percent = 2.0
        analytics_dashboard.cached_analytics.recommendation_quality.user_satisfaction_score = 4.5
        
        comparison = analytics_dashboard.get_performance_comparison()
        
        assert isinstance(comparison, dict)
        assert "avg_response_time_ms" in comparison
        assert "error_rate_percent" in comparison
        assert "user_satisfaction_score" in comparison
        
        for metric, data in comparison.items():
            assert "current" in data
            assert "baseline" in data
            assert "change_percent" in data
            assert "status" in data
    
    def test_export_analytics_report(self, analytics_dashboard):
        """Test analytics report export."""
        # Set cached analytics
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        
        # Test JSON export
        report = analytics_dashboard.export_analytics_report("json")
        assert isinstance(report, str)
        
        import json
        report_data = json.loads(report)
        assert "report_generated" in report_data
        assert "analytics" in report_data
        assert "historical_summary" in report_data
        assert "performance_comparison" in report_data
        
        # Test invalid format
        with pytest.raises(ValueError):
            analytics_dashboard.export_analytics_report("invalid_format")
    
    def test_get_dashboard_summary(self, analytics_dashboard):
        """Test dashboard summary."""
        # Initially should return empty dict
        summary = analytics_dashboard.get_dashboard_summary()
        assert isinstance(summary, dict)
        
        # Set cached analytics
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        analytics_dashboard.last_update = datetime.now(timezone.utc)
        
        summary = analytics_dashboard.get_dashboard_summary()
        assert "last_updated" in summary
        assert "system_health" in summary
        assert "active_users" in summary
        assert "user_satisfaction" in summary
        assert "system_performance" in summary
        assert "active_alerts" in summary
        assert "key_trends" in summary


class TestAnalyticsIntegration:
    """Test analytics dashboard integration."""
    
    @pytest.mark.asyncio
    async def test_alert_condition_checking(self, analytics_dashboard):
        """Test alert condition checking."""
        # Set cached analytics with threshold violations
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        analytics_dashboard.cached_analytics.system_performance.error_rate_percent = 10.0  # Above threshold
        analytics_dashboard.cached_analytics.system_performance.avg_response_time_ms = 6000.0  # Above threshold
        analytics_dashboard.cached_analytics.recommendation_quality.user_satisfaction_score = 2.0  # Below threshold
        
        # Check alert conditions (should not raise errors)
        await analytics_dashboard._check_alert_conditions()
    
    @pytest.mark.asyncio
    async def test_historical_data_storage(self, analytics_dashboard):
        """Test historical data storage."""
        # Set cached analytics
        analytics_dashboard.cached_analytics = ComprehensiveAnalytics()
        analytics_dashboard.cached_analytics.user_analytics.user_engagement_score = 8.5
        analytics_dashboard.cached_analytics.recommendation_quality.recommendation_accuracy = 0.85
        analytics_dashboard.cached_analytics.system_performance.avg_response_time_ms = 1200.0
        
        # Store historical data
        analytics_dashboard._store_historical_data()
        
        # Verify data was stored
        assert len(analytics_dashboard.historical_data["user_engagement_score"]) > 0
        assert len(analytics_dashboard.historical_data["recommendation_accuracy"]) > 0
        assert len(analytics_dashboard.historical_data["system_response_time"]) > 0
        
        # Check data structure
        for metric_data in analytics_dashboard.historical_data["user_engagement_score"]:
            assert "timestamp" in metric_data
            assert "value" in metric_data
    
    @pytest.mark.asyncio
    async def test_baseline_initialization(self, analytics_dashboard):
        """Test performance baseline initialization."""
        await analytics_dashboard._initialize_baselines()
        
        assert len(analytics_dashboard.performance_baselines) > 0
        assert "avg_response_time_ms" in analytics_dashboard.performance_baselines
        assert "error_rate_percent" in analytics_dashboard.performance_baselines
        assert "user_satisfaction_score" in analytics_dashboard.performance_baselines
        assert "recommendation_accuracy" in analytics_dashboard.performance_baselines
        assert "system_availability_percent" in analytics_dashboard.performance_baselines


if __name__ == "__main__":
    pytest.main([__file__])