"""
Tests for scalability features.

Tests load balancing, auto-scaling policies, resource monitoring,
and cost optimization capabilities.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.infra_mind.core.scalability_manager import (
    LoadBalancer,
    AutoScaler,
    ResourceMonitor,
    CostOptimizer,
    ScalabilityManager,
    LoadBalancingStrategy,
    ScalingPolicy,
    ScalingDirection,
    AgentInstance,
    ResourceMetrics,
    CostMetrics
)


class TestLoadBalancer:
    """Test load balancer functionality."""
    
    @pytest.fixture
    def load_balancer(self):
        """Create load balancer instance."""
        return LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
    
    @pytest.fixture
    def agent_instances(self):
        """Create test agent instances."""
        instances = []
        for i in range(3):
            instance = AgentInstance(
                instance_id=f"test_agent_{i}",
                agent_type="test_agent",
                weight=1.0 + (i * 0.2)
            )
            instances.append(instance)
        return instances
    
    def test_register_agent_instance(self, load_balancer, agent_instances):
        """Test agent instance registration."""
        instance = agent_instances[0]
        load_balancer.register_agent_instance(instance)
        
        assert "test_agent" in load_balancer.agent_pools
        assert len(load_balancer.agent_pools["test_agent"]) == 1
        assert load_balancer.agent_pools["test_agent"][0] == instance
    
    def test_unregister_agent_instance(self, load_balancer, agent_instances):
        """Test agent instance unregistration."""
        instance = agent_instances[0]
        load_balancer.register_agent_instance(instance)
        
        # Unregister existing instance
        result = load_balancer.unregister_agent_instance("test_agent", instance.instance_id)
        assert result is True
        assert len(load_balancer.agent_pools["test_agent"]) == 0
        
        # Try to unregister non-existing instance
        result = load_balancer.unregister_agent_instance("test_agent", "non_existing")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_round_robin_selection(self, load_balancer, agent_instances):
        """Test round robin load balancing."""
        # Register instances
        for instance in agent_instances:
            load_balancer.register_agent_instance(instance)
        
        # Test round robin distribution
        selected_instances = []
        for _ in range(6):  # More than number of instances
            instance = await load_balancer.get_next_agent("test_agent")
            if instance:
                selected_instances.append(instance.instance_id)
                load_balancer.release_agent(instance, True, 100.0)
        
        # Should cycle through instances
        assert len(selected_instances) == 6
        assert selected_instances[0] == selected_instances[3]  # Should repeat after 3
        assert selected_instances[1] == selected_instances[4]
        assert selected_instances[2] == selected_instances[5]
    
    @pytest.mark.asyncio
    async def test_least_connections_selection(self, agent_instances):
        """Test least connections load balancing."""
        load_balancer = LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS)
        
        # Register instances with different request counts
        for i, instance in enumerate(agent_instances):
            instance.total_requests = i * 10  # 0, 10, 20 requests
            load_balancer.register_agent_instance(instance)
        
        # Should select instance with least requests (first one)
        selected = await load_balancer.get_next_agent("test_agent")
        assert selected.instance_id == "test_agent_0"
        assert selected.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_resource_based_selection(self, agent_instances):
        """Test resource-based load balancing."""
        load_balancer = LoadBalancer(LoadBalancingStrategy.RESOURCE_BASED)
        
        # Register instances with different utilization
        for i, instance in enumerate(agent_instances):
            instance.current_load = i * 0.3  # 0.0, 0.3, 0.6 utilization
            load_balancer.register_agent_instance(instance)
        
        # Should select instance with lowest utilization
        selected = await load_balancer.get_next_agent("test_agent")
        assert selected.instance_id == "test_agent_0"
        assert selected.current_load == 0.0
    
    def test_release_agent(self, load_balancer, agent_instances):
        """Test agent release functionality."""
        instance = agent_instances[0]
        instance.is_busy = True
        instance.total_requests = 5
        instance.successful_requests = 4
        instance.avg_response_time = 200.0
        
        # Release agent with success
        load_balancer.release_agent(instance, True, 150.0)
        
        assert instance.is_busy is False
        assert instance.total_requests == 6
        assert instance.successful_requests == 5
        assert instance.success_rate == 5/6
        # Response time should be updated (exponential moving average)
        assert instance.avg_response_time < 200.0
    
    def test_get_load_balancer_stats(self, load_balancer, agent_instances):
        """Test load balancer statistics."""
        # Register instances
        for instance in agent_instances:
            instance.total_requests = 10
            instance.successful_requests = 9
            instance.avg_response_time = 100.0
            load_balancer.register_agent_instance(instance)
        
        stats = load_balancer.get_load_balancer_stats()
        
        assert stats["strategy"] == LoadBalancingStrategy.ROUND_ROBIN.value
        assert "agent_pools" in stats
        assert "test_agent" in stats["agent_pools"]
        
        pool_stats = stats["agent_pools"]["test_agent"]
        assert pool_stats["total_instances"] == 3
        assert pool_stats["total_requests"] == 30
        assert pool_stats["success_rate"] == 0.9


class TestAutoScaler:
    """Test auto-scaling functionality."""
    
    @pytest.fixture
    def load_balancer(self):
        """Create load balancer for auto-scaler."""
        return LoadBalancer()
    
    @pytest.fixture
    def auto_scaler(self, load_balancer):
        """Create auto-scaler instance."""
        return AutoScaler(load_balancer)
    
    @pytest.fixture
    def scaling_policy(self):
        """Create test scaling policy."""
        return ScalingPolicy(
            agent_type="test_agent",
            min_instances=1,
            max_instances=5,
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            scale_up_cooldown_seconds=60,
            scale_down_cooldown_seconds=120
        )
    
    def test_register_scaling_policy(self, auto_scaler, scaling_policy):
        """Test scaling policy registration."""
        auto_scaler.register_scaling_policy(scaling_policy)
        
        assert "test_agent" in auto_scaler.scaling_policies
        assert auto_scaler.scaling_policies["test_agent"] == scaling_policy
    
    def test_register_agent_factory(self, auto_scaler):
        """Test agent factory registration."""
        def mock_factory():
            return Mock()
        
        auto_scaler.register_agent_factory("test_agent", mock_factory)
        
        assert "test_agent" in auto_scaler.agent_factories
        assert auto_scaler.agent_factories["test_agent"] == mock_factory
    
    @pytest.mark.asyncio
    async def test_get_scaling_metrics(self, auto_scaler, scaling_policy):
        """Test scaling metrics collection."""
        auto_scaler.register_scaling_policy(scaling_policy)
        
        # Add some mock instances
        instances = [
            AgentInstance("test_1", "test_agent", current_load=0.8, is_busy=True),
            AgentInstance("test_2", "test_agent", current_load=0.6, is_busy=False)
        ]
        auto_scaler.load_balancer.agent_pools["test_agent"] = instances
        
        metrics = await auto_scaler._get_scaling_metrics("test_agent", scaling_policy)
        
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "avg_utilization" in metrics
        assert "busy_ratio" in metrics
        assert metrics["busy_ratio"] == 50.0  # 1 out of 2 busy
    
    def test_should_scale_up(self, auto_scaler, scaling_policy):
        """Test scale up decision logic."""
        # High load metrics
        metrics = {
            "cpu_percent": 85.0,
            "memory_percent": 82.0,
            "avg_utilization": 0.9,
            "busy_ratio": 90.0
        }
        
        should_scale = auto_scaler._should_scale_up(metrics, scaling_policy)
        assert should_scale is True
        
        # Low load metrics
        metrics = {
            "cpu_percent": 50.0,
            "memory_percent": 45.0,
            "avg_utilization": 0.4,
            "busy_ratio": 40.0
        }
        
        should_scale = auto_scaler._should_scale_up(metrics, scaling_policy)
        assert should_scale is False
    
    def test_should_scale_down(self, auto_scaler, scaling_policy):
        """Test scale down decision logic."""
        # Low load metrics
        metrics = {
            "cpu_percent": 20.0,
            "memory_percent": 25.0,
            "avg_utilization": 0.2,
            "busy_ratio": 15.0
        }
        
        should_scale = auto_scaler._should_scale_down(metrics, scaling_policy)
        assert should_scale is True
        
        # High load metrics
        metrics = {
            "cpu_percent": 70.0,
            "memory_percent": 65.0,
            "avg_utilization": 0.7,
            "busy_ratio": 75.0
        }
        
        should_scale = auto_scaler._should_scale_down(metrics, scaling_policy)
        assert should_scale is False
    
    @pytest.mark.asyncio
    async def test_scale_up(self, auto_scaler, scaling_policy):
        """Test scale up execution."""
        def mock_factory():
            return Mock()
        
        auto_scaler.register_scaling_policy(scaling_policy)
        auto_scaler.register_agent_factory("test_agent", mock_factory)
        
        # Start with minimum instances
        initial_count = len(auto_scaler.load_balancer.agent_pools["test_agent"])
        
        success = await auto_scaler._scale_up("test_agent", scaling_policy)
        assert success is True
        
        # Should have added instances
        final_count = len(auto_scaler.load_balancer.agent_pools["test_agent"])
        assert final_count > initial_count
    
    @pytest.mark.asyncio
    async def test_scale_down(self, auto_scaler, scaling_policy):
        """Test scale down execution."""
        auto_scaler.register_scaling_policy(scaling_policy)
        
        # Add some idle instances
        instances = [
            AgentInstance("test_1", "test_agent", is_busy=False, health_score=0.8),
            AgentInstance("test_2", "test_agent", is_busy=False, health_score=0.6),
            AgentInstance("test_3", "test_agent", is_busy=True, health_score=0.9)
        ]
        auto_scaler.load_balancer.agent_pools["test_agent"] = instances
        
        initial_count = len(auto_scaler.load_balancer.agent_pools["test_agent"])
        
        success = await auto_scaler._scale_down("test_agent", scaling_policy)
        assert success is True
        
        # Should have removed an idle instance
        final_count = len(auto_scaler.load_balancer.agent_pools["test_agent"])
        assert final_count < initial_count
    
    def test_get_scaling_status(self, auto_scaler, scaling_policy):
        """Test scaling status retrieval."""
        auto_scaler.register_scaling_policy(scaling_policy)
        
        # Add some instances
        instances = [
            AgentInstance("test_1", "test_agent"),
            AgentInstance("test_2", "test_agent")
        ]
        auto_scaler.load_balancer.agent_pools["test_agent"] = instances
        
        status = auto_scaler.get_scaling_status()
        
        assert "test_agent" in status
        agent_status = status["test_agent"]
        assert agent_status["current_instances"] == 2
        assert agent_status["min_instances"] == scaling_policy.min_instances
        assert agent_status["max_instances"] == scaling_policy.max_instances
        assert agent_status["can_scale_up"] is True
        assert agent_status["can_scale_down"] is True


class TestResourceMonitor:
    """Test resource monitoring functionality."""
    
    @pytest.fixture
    def resource_monitor(self):
        """Create resource monitor instance."""
        return ResourceMonitor()
    
    @pytest.mark.asyncio
    async def test_collect_resource_metrics(self, resource_monitor):
        """Test resource metrics collection."""
        metrics = await resource_monitor.collect_resource_metrics()
        
        assert isinstance(metrics, ResourceMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.disk_percent >= 0
        assert metrics.active_connections >= 0
        assert isinstance(metrics.timestamp, datetime)
        
        # Should be stored in history
        assert len(resource_monitor.resource_history) == 1
        assert resource_monitor.resource_history[0] == metrics
    
    def test_get_resource_trends(self, resource_monitor):
        """Test resource trends analysis."""
        # Add some test data
        for i in range(5):
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                cpu_percent=50.0 + i * 5,
                memory_percent=60.0 + i * 3,
                disk_percent=70.0 + i * 2,
                network_io_bytes=1000 + i * 100,
                active_connections=10 + i,
                load_average=1.0 + i * 0.1
            )
            resource_monitor.resource_history.append(metrics)
        
        trends = resource_monitor.get_resource_trends(1)  # Last hour
        
        assert "time_period_hours" in trends
        assert "data_points" in trends
        assert "cpu_usage" in trends
        assert "memory_usage" in trends
        assert "disk_usage" in trends
        
        cpu_data = trends["cpu_usage"]
        assert "current" in cpu_data
        assert "average" in cpu_data
        assert "min" in cpu_data
        assert "max" in cpu_data
        assert "trend" in cpu_data
    
    def test_calculate_trend(self, resource_monitor):
        """Test trend calculation."""
        # Increasing trend
        increasing_values = [10, 15, 20, 25, 30]
        trend = resource_monitor._calculate_trend(increasing_values)
        assert trend == "increasing"
        
        # Decreasing trend
        decreasing_values = [30, 25, 20, 15, 10]
        trend = resource_monitor._calculate_trend(decreasing_values)
        assert trend == "decreasing"
        
        # Stable trend
        stable_values = [20, 21, 19, 20, 21]
        trend = resource_monitor._calculate_trend(stable_values)
        assert trend == "stable"
    
    def test_predict_capacity_needs(self, resource_monitor):
        """Test capacity prediction."""
        # Add sufficient historical data
        for i in range(30):
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                cpu_percent=40.0 + i * 1.5,  # Increasing trend
                memory_percent=50.0 + i * 1.0,
                disk_percent=60.0 + i * 0.5,
                network_io_bytes=1000,
                active_connections=10,
                load_average=1.0
            )
            resource_monitor.resource_history.append(metrics)
        
        predictions = resource_monitor.predict_capacity_needs(24)  # 24 hours
        
        assert "forecast_hours" in predictions
        assert "predictions" in predictions
        assert "recommendations" in predictions
        
        # Should have predictions for each resource
        assert "cpu_usage" in predictions["predictions"]
        assert "memory_usage" in predictions["predictions"]
        assert "disk_usage" in predictions["predictions"]


class TestCostOptimizer:
    """Test cost optimization functionality."""
    
    @pytest.fixture
    def cost_optimizer(self):
        """Create cost optimizer instance."""
        return CostOptimizer()
    
    @pytest.fixture
    def load_balancer_with_agents(self):
        """Create load balancer with test agents."""
        load_balancer = LoadBalancer()
        
        # Add different types of agents
        agent_types = ["cto_agent", "research_agent", "cloud_engineer_agent"]
        for agent_type in agent_types:
            for i in range(2):
                instance = AgentInstance(
                    instance_id=f"{agent_type}_{i}",
                    agent_type=agent_type,
                    current_load=0.5 + i * 0.2,
                    total_requests=100 + i * 50,
                    is_busy=(i == 0)  # First instance busy
                )
                load_balancer.register_agent_instance(instance)
        
        return load_balancer
    
    @pytest.mark.asyncio
    async def test_calculate_current_costs(self, cost_optimizer, load_balancer_with_agents):
        """Test current cost calculation."""
        metrics = await cost_optimizer.calculate_current_costs(load_balancer_with_agents)
        
        assert isinstance(metrics, CostMetrics)
        assert metrics.total_instances > 0
        assert metrics.total_hourly_cost > 0
        assert metrics.projected_monthly_cost > 0
        assert 0 <= metrics.utilization_efficiency <= 1
        assert metrics.cost_per_request >= 0
        
        # Should have costs for each agent type
        assert "cto_agent" in metrics.instance_costs
        assert "research_agent" in metrics.instance_costs
        assert "cloud_engineer_agent" in metrics.instance_costs
        
        # Should be stored in history
        assert len(cost_optimizer.cost_history) == 1
    
    def test_get_cost_optimization_recommendations(self, cost_optimizer, load_balancer_with_agents):
        """Test cost optimization recommendations."""
        recommendations = cost_optimizer.get_cost_optimization_recommendations(load_balancer_with_agents)
        
        assert isinstance(recommendations, list)
        
        # Check recommendation structure
        for rec in recommendations:
            assert "agent_type" in rec
            assert "issue" in rec
            assert "recommendation" in rec
            assert "priority" in rec
    
    def test_get_cost_report(self, cost_optimizer):
        """Test cost report generation."""
        # Add some historical data
        for i in range(10):
            metrics = CostMetrics(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                total_instances=5 + i % 3,
                instance_costs={"test_agent": 0.05 * (5 + i % 3)},
                total_hourly_cost=0.25 + i * 0.01,
                utilization_efficiency=0.7 + i * 0.02,
                cost_per_request=0.001 + i * 0.0001,
                projected_monthly_cost=180.0 + i * 5
            )
            cost_optimizer.cost_history.append(metrics)
        
        report = cost_optimizer.get_cost_report(1)  # Last day
        
        assert "analysis_period_days" in report
        assert "data_points" in report
        assert "cost_summary" in report
        assert "efficiency_summary" in report
        assert "agent_costs" in report
        
        cost_summary = report["cost_summary"]
        assert "current_hourly_cost" in cost_summary
        assert "average_hourly_cost" in cost_summary
        assert "projected_monthly_cost" in cost_summary


class TestScalabilityManager:
    """Test main scalability manager."""
    
    @pytest.fixture
    def scalability_manager(self):
        """Create scalability manager instance."""
        return ScalabilityManager()
    
    def test_register_agent_type(self, scalability_manager):
        """Test agent type registration."""
        def mock_factory():
            return Mock()
        
        scaling_policy = ScalingPolicy(agent_type="test_agent")
        
        scalability_manager.register_agent_type("test_agent", mock_factory, scaling_policy)
        
        # Should be registered with auto-scaler
        assert "test_agent" in scalability_manager.auto_scaler.agent_factories
        assert "test_agent" in scalability_manager.auto_scaler.scaling_policies
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, scalability_manager):
        """Test monitoring service lifecycle."""
        assert scalability_manager._monitoring_enabled is False
        assert len(scalability_manager._background_tasks) == 0
        
        # Mock asyncio.create_task to avoid actual background execution
        with patch('asyncio.create_task') as mock_create_task:
            mock_task = Mock()
            mock_create_task.return_value = mock_task
            
            await scalability_manager.start_monitoring()
            
            assert scalability_manager._monitoring_enabled is True
            assert len(scalability_manager._background_tasks) == 3  # 3 monitoring loops
            
            # Test stopping
            mock_task.cancel = Mock()
            
            with patch('asyncio.gather', return_value=None):
                await scalability_manager.stop_monitoring()
                
                assert scalability_manager._monitoring_enabled is False
                assert len(scalability_manager._background_tasks) == 0
                mock_task.cancel.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_status(self, scalability_manager):
        """Test comprehensive status retrieval."""
        # Mock the component methods to avoid actual system calls
        with patch.object(scalability_manager.load_balancer, 'get_load_balancer_stats') as mock_lb:
            with patch.object(scalability_manager.auto_scaler, 'get_scaling_status') as mock_scaling:
                with patch.object(scalability_manager.resource_monitor, 'get_resource_trends') as mock_trends:
                    with patch.object(scalability_manager.resource_monitor, 'predict_capacity_needs') as mock_capacity:
                        with patch.object(scalability_manager.cost_optimizer, 'get_cost_report') as mock_cost:
                            with patch.object(scalability_manager.cost_optimizer, 'get_cost_optimization_recommendations') as mock_rec:
                                
                                # Setup mock returns
                                mock_lb.return_value = {"strategy": "round_robin", "agent_pools": {}}
                                mock_scaling.return_value = {"test_agent": {"current_instances": 2}}
                                mock_trends.return_value = {"cpu_usage": {"current": 50.0, "trend": "stable"}}
                                mock_capacity.return_value = {"predictions": {}, "recommendations": []}
                                mock_cost.return_value = {"cost_summary": {"current_hourly_cost": 0.1}}
                                mock_rec.return_value = []
                                
                                status = await scalability_manager.get_comprehensive_status()
                                
                                assert "timestamp" in status
                                assert "monitoring_enabled" in status
                                assert "load_balancer" in status
                                assert "auto_scaling" in status
                                assert "resource_trends" in status
                                assert "capacity_predictions" in status
                                assert "cost_analysis" in status
                                assert "cost_recommendations" in status
                                assert "system_health" in status


@pytest.mark.asyncio
async def test_integration_scalability_features():
    """Integration test for scalability features."""
    # Test that all components work together
    manager = ScalabilityManager()
    
    # Register agent type
    def mock_factory():
        return Mock(is_busy=False)
    
    policy = ScalingPolicy(
        agent_type="test_agent",
        min_instances=1,
        max_instances=3
    )
    
    manager.register_agent_type("test_agent", mock_factory, policy)
    
    # Test load balancing
    agent = await manager.load_balancer.get_next_agent("test_agent")
    assert agent is None  # No instances yet
    
    # Test auto-scaling evaluation
    decisions = await manager.auto_scaler.evaluate_scaling_decisions()
    assert "test_agent" in decisions
    
    # Test resource monitoring
    metrics = await manager.resource_monitor.collect_resource_metrics()
    assert isinstance(metrics, ResourceMetrics)
    
    # Test cost calculation
    cost_metrics = await manager.cost_optimizer.calculate_current_costs(manager.load_balancer)
    assert isinstance(cost_metrics, CostMetrics)


if __name__ == "__main__":
    pytest.main([__file__])