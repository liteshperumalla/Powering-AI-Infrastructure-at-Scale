"""
Comprehensive tests for system resilience features.

Tests health checks, failover mechanisms, circuit breakers,
and system recovery capabilities.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.infra_mind.core.health_checks import (
    HealthCheckManager, DatabaseHealthCheck, CacheHealthCheck,
    ExternalAPIHealthCheck, AgentHealthCheck, HealthStatus,
    ComponentType, HealthCheckConfig, get_health_manager
)
from src.infra_mind.core.failover import (
    FailoverOrchestrator, ActivePassiveFailoverManager,
    RoundRobinFailoverManager, WeightedFailoverManager,
    ServiceEndpoint, FailoverConfig, FailoverStrategy,
    get_failover_orchestrator
)
from src.infra_mind.core.resilience import (
    ResilienceManager, CircuitBreaker, RetryMechanism,
    FallbackManager, SystemRecoveryManager, CircuitBreakerConfig,
    RetryConfig, FallbackConfig, get_system_recovery_manager
)


class TestHealthChecks:
    """Test health check system."""
    
    @pytest.fixture
    def health_manager(self):
        """Create health check manager for testing."""
        return HealthCheckManager()
    
    @pytest.fixture
    def mock_database_check(self):
        """Create mock database health check."""
        config = HealthCheckConfig(timeout_seconds=5.0)
        return DatabaseHealthCheck("test_db", "mongodb://localhost:27017", config)
    
    @pytest.fixture
    def mock_cache_check(self):
        """Create mock cache health check."""
        config = HealthCheckConfig(timeout_seconds=3.0)
        return CacheHealthCheck("test_cache", "redis://localhost:6379", config)
    
    @pytest.fixture
    def mock_api_check(self):
        """Create mock API health check."""
        config = HealthCheckConfig(timeout_seconds=10.0)
        return ExternalAPIHealthCheck("test_api", "https://api.example.com/health", config)
    
    @pytest.mark.asyncio
    async def test_health_manager_registration(self, health_manager, mock_database_check):
        """Test health check registration."""
        health_manager.register_health_check(mock_database_check)
        
        assert "test_db" in health_manager.health_checks
        assert health_manager.health_checks["test_db"] == mock_database_check
    
    @pytest.mark.asyncio
    async def test_database_health_check_success(self, mock_database_check):
        """Test successful database health check."""
        with patch.object(mock_database_check, 'perform_check') as mock_perform:
            mock_perform.return_value = Mock(
                component_name="test_db",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                timestamp=datetime.utcnow(),
                details={"server_version": "4.4.0"},
                error_message=None
            )
            
            result = await mock_database_check.check_health()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component_name == "test_db"
            assert result.response_time_ms > 0
            assert mock_database_check.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_database_health_check_failure(self, mock_database_check):
        """Test failed database health check."""
        with patch.object(mock_database_check, 'perform_check') as mock_perform:
            mock_perform.side_effect = Exception("Connection failed")
            
            result = await mock_database_check.check_health()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error_message == "Connection failed"
            assert mock_database_check.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self, mock_api_check):
        """Test health check timeout handling."""
        with patch.object(mock_api_check, 'perform_check') as mock_perform:
            # Simulate timeout
            async def slow_check():
                await asyncio.sleep(15)  # Longer than timeout
                return Mock()
            
            mock_perform.side_effect = slow_check
            
            result = await mock_api_check.check_health()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_system_health_summary(self, health_manager, mock_database_check, mock_cache_check):
        """Test system health summary generation."""
        health_manager.register_health_check(mock_database_check)
        health_manager.register_health_check(mock_cache_check)
        
        # Mock health check results
        with patch.object(mock_database_check, 'check_health') as mock_db_check, \
             patch.object(mock_cache_check, 'check_health') as mock_cache_check_method:
            
            mock_db_check.return_value = Mock(
                status=HealthStatus.HEALTHY,
                timestamp=datetime.utcnow(),
                response_time_ms=50.0,
                error_message=None
            )
            
            mock_cache_check_method.return_value = Mock(
                status=HealthStatus.DEGRADED,
                timestamp=datetime.utcnow(),
                response_time_ms=200.0,
                error_message="High response time"
            )
            
            # Add mock results to history
            health_manager.health_history["test_db"] = [mock_db_check.return_value]
            health_manager.health_history["test_cache"] = [mock_cache_check_method.return_value]
            
            summary = health_manager.get_system_health_summary()
            
            assert summary["total_components"] == 2
            assert summary["healthy_components"] == 1
            assert summary["degraded_components"] == 1
            assert summary["overall_status"] == HealthStatus.DEGRADED


class TestFailoverSystem:
    """Test failover system."""
    
    @pytest.fixture
    def failover_orchestrator(self):
        """Create failover orchestrator for testing."""
        return FailoverOrchestrator()
    
    @pytest.fixture
    def service_endpoints(self):
        """Create test service endpoints."""
        return [
            ServiceEndpoint("primary", "https://primary.example.com", priority=1, weight=100),
            ServiceEndpoint("secondary", "https://secondary.example.com", priority=2, weight=50),
            ServiceEndpoint("tertiary", "https://tertiary.example.com", priority=3, weight=25)
        ]
    
    @pytest.mark.asyncio
    async def test_active_passive_failover(self, service_endpoints):
        """Test active-passive failover strategy."""
        config = FailoverConfig(strategy=FailoverStrategy.ACTIVE_PASSIVE)
        manager = ActivePassiveFailoverManager("test_service", config)
        
        # Add endpoints
        for endpoint in service_endpoints:
            manager.add_endpoint(endpoint)
        
        # Test primary selection
        selected = await manager.select_endpoint()
        assert selected.name == "primary"
        
        # Mark primary as unhealthy
        service_endpoints[0].is_healthy = False
        
        # Test failover to secondary
        selected = await manager.select_endpoint()
        assert selected.name == "secondary"
    
    @pytest.mark.asyncio
    async def test_round_robin_failover(self, service_endpoints):
        """Test round-robin failover strategy."""
        config = FailoverConfig(strategy=FailoverStrategy.ROUND_ROBIN)
        manager = RoundRobinFailoverManager("test_service", config)
        
        # Add healthy endpoints
        for endpoint in service_endpoints:
            endpoint.is_healthy = True
            manager.add_endpoint(endpoint)
        
        # Test round-robin selection
        selections = []
        for _ in range(6):  # Two full rounds
            selected = await manager.select_endpoint()
            selections.append(selected.name)
        
        # Should cycle through all endpoints
        assert selections == ["primary", "secondary", "tertiary"] * 2
    
    @pytest.mark.asyncio
    async def test_weighted_failover(self, service_endpoints):
        """Test weighted failover strategy."""
        config = FailoverConfig(strategy=FailoverStrategy.WEIGHTED)
        manager = WeightedFailoverManager("test_service", config)
        
        # Add healthy endpoints with different weights
        for endpoint in service_endpoints:
            endpoint.is_healthy = True
            manager.add_endpoint(endpoint)
        
        # Test weighted selection (primary should be selected more often)
        selections = {}
        for _ in range(1000):
            selected = await manager.select_endpoint()
            selections[selected.name] = selections.get(selected.name, 0) + 1
        
        # Primary (weight 100) should be selected most often
        assert selections["primary"] > selections["secondary"]
        assert selections["secondary"] > selections["tertiary"]
    
    @pytest.mark.asyncio
    async def test_manual_failover(self, failover_orchestrator, service_endpoints):
        """Test manual failover trigger."""
        manager = failover_orchestrator.register_service(
            "test_service",
            FailoverStrategy.ACTIVE_PASSIVE
        )
        
        for endpoint in service_endpoints:
            manager.add_endpoint(endpoint)
        
        # Test manual failover
        success = await failover_orchestrator.manual_failover("test_service", "secondary")
        assert success
        
        current = await manager.get_current_endpoint()
        assert current.name == "secondary"
    
    @pytest.mark.asyncio
    async def test_failover_cooldown(self, service_endpoints):
        """Test failover cooldown period."""
        config = FailoverConfig(cooldown_period_seconds=1)
        manager = ActivePassiveFailoverManager("test_service", config)
        
        for endpoint in service_endpoints:
            manager.add_endpoint(endpoint)
        
        # Trigger first failover
        await manager._trigger_failover("HEALTH_CHECK_FAILURE", "Test failure")
        assert manager.is_in_cooldown
        
        # Try to trigger another failover immediately
        result = await manager._trigger_failover("HEALTH_CHECK_FAILURE", "Another failure")
        assert not result  # Should fail due to cooldown
        
        # Wait for cooldown to expire
        await asyncio.sleep(1.1)
        assert not manager.is_in_cooldown


class TestCircuitBreakers:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,
            timeout=0.5
        )
        return CircuitBreaker("test_service", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state."""
        async def successful_call():
            return "success"
        
        result = await circuit_breaker.call(successful_call)
        assert result == "success"
        assert circuit_breaker.state.value == "closed"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures."""
        async def failing_call():
            raise Exception("Service unavailable")
        
        # Trigger failures to reach threshold
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)
        
        # Circuit should now be open
        assert circuit_breaker.state.value == "open"
        
        # Next call should be blocked
        with pytest.raises(Exception) as exc_info:
            await circuit_breaker.call(failing_call)
        
        assert "circuit breaker" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery through half-open state."""
        async def failing_call():
            raise Exception("Service unavailable")
        
        async def successful_call():
            return "success"
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)
        
        assert circuit_breaker.state.value == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Check state transition to half-open
        await circuit_breaker._check_state()
        assert circuit_breaker.state.value == "half_open"
        
        # Successful calls should close the circuit
        for _ in range(3):  # success_threshold
            result = await circuit_breaker.call(successful_call)
            assert result == "success"
        
        assert circuit_breaker.state.value == "closed"


class TestRetryMechanism:
    """Test retry mechanism."""
    
    @pytest.fixture
    def retry_mechanism(self):
        """Create retry mechanism for testing."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0
        )
        return RetryMechanism(config)
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self, retry_mechanism):
        """Test successful execution on first attempt."""
        async def successful_call():
            return "success"
        
        result = await retry_mechanism.execute(successful_call)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, retry_mechanism):
        """Test successful execution after initial failures."""
        call_count = 0
        
        async def eventually_successful_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await retry_mechanism.execute(eventually_successful_call)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, retry_mechanism):
        """Test retry exhaustion after max attempts."""
        async def always_failing_call():
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception) as exc_info:
            await retry_mechanism.execute(always_failing_call)
        
        assert "failed after" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, retry_mechanism):
        """Test exponential backoff delay calculation."""
        delays = []
        for attempt in range(3):
            delay = retry_mechanism._calculate_delay(attempt)
            delays.append(delay)
        
        # Each delay should be roughly double the previous (with jitter)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]


class TestSystemRecovery:
    """Test system recovery capabilities."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create system recovery manager for testing."""
        return SystemRecoveryManager()
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_registration(self, recovery_manager):
        """Test recovery strategy registration."""
        async def custom_recovery(error_context):
            return {"success": True, "action": "Custom recovery"}
        
        recovery_manager.register_recovery_strategy("test_component", custom_recovery)
        
        assert "test_component" in recovery_manager.recovery_strategies
        assert custom_recovery in recovery_manager.recovery_strategies["test_component"]
    
    @pytest.mark.asyncio
    async def test_successful_recovery(self, recovery_manager):
        """Test successful component recovery."""
        async def successful_recovery(error_context):
            return {"success": True, "action": "Component recovered"}
        
        recovery_manager.register_recovery_strategy("test_component", successful_recovery)
        
        error_context = {"error": "Test failure", "timestamp": datetime.utcnow().isoformat()}
        result = await recovery_manager.attempt_recovery("test_component", error_context)
        
        assert result["success"] is True
        assert len(result["actions_taken"]) > 0
        assert result["recovery_time_seconds"] > 0
    
    @pytest.mark.asyncio
    async def test_failed_recovery(self, recovery_manager):
        """Test failed component recovery."""
        async def failing_recovery(error_context):
            raise Exception("Recovery failed")
        
        recovery_manager.register_recovery_strategy("test_component", failing_recovery)
        
        error_context = {"error": "Test failure", "timestamp": datetime.utcnow().isoformat()}
        result = await recovery_manager.attempt_recovery("test_component", error_context)
        
        assert result["success"] is False
        assert "Recovery failed" in str(result["actions_taken"])
    
    @pytest.mark.asyncio
    async def test_default_recovery_strategies(self, recovery_manager):
        """Test default recovery strategies for different component types."""
        # Test database recovery
        error_context = {"error": "Database connection failed"}
        result = await recovery_manager.attempt_recovery("database", error_context)
        
        assert "actions_taken" in result
        assert len(result["actions_taken"]) > 0
        
        # Test cache recovery
        result = await recovery_manager.attempt_recovery("cache", error_context)
        
        assert "actions_taken" in result
        assert len(result["actions_taken"]) > 0
    
    def test_recovery_stats(self, recovery_manager):
        """Test recovery statistics calculation."""
        # Add some mock recovery history
        recovery_manager.recovery_history = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "component_name": "test1",
                "success": True,
                "recovery_time_seconds": 2.5,
                "actions_taken": ["Action 1"]
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "component_name": "test2",
                "success": False,
                "recovery_time_seconds": 1.0,
                "actions_taken": ["Action 2"]
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "component_name": "test1",
                "success": True,
                "recovery_time_seconds": 1.5,
                "actions_taken": ["Action 3"]
            }
        ]
        
        stats = recovery_manager.get_recovery_stats()
        
        assert stats["total_attempts"] == 3
        assert stats["successful_attempts"] == 2
        assert stats["failed_attempts"] == 1
        assert stats["success_rate_percent"] == 66.67
        assert stats["avg_recovery_time_seconds"] == 2.0  # Average of successful attempts
        assert "test1" in stats["components_recovered"]
    
    def test_auto_recovery_toggle(self, recovery_manager):
        """Test enabling/disabling auto-recovery."""
        # Test enabling
        recovery_manager.enable_auto_recovery()
        assert recovery_manager.auto_recovery_enabled is True
        
        # Test disabling
        recovery_manager.disable_auto_recovery()
        assert recovery_manager.auto_recovery_enabled is False


class TestResilienceIntegration:
    """Test integration of all resilience components."""
    
    @pytest.mark.asyncio
    async def test_full_resilience_flow(self):
        """Test complete resilience flow with all components."""
        # Create resilience manager
        resilience_manager = ResilienceManager()
        
        # Register a service
        resilience_manager.register_service("test_service")
        
        # Mock a service call that fails initially then succeeds
        call_count = 0
        
        async def flaky_service():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Service temporarily unavailable")
            return {"data": "success"}
        
        # Execute with resilience patterns
        async with resilience_manager.resilient_call(
            "test_service",
            fallback_key="test_fallback"
        ) as execute:
            result = await execute(flaky_service)
        
        # Should eventually succeed with retry mechanism
        assert result["data"] is not None or result["fallback_used"] is True
    
    @pytest.mark.asyncio
    async def test_resilience_with_fallback(self):
        """Test resilience with fallback data."""
        resilience_manager = ResilienceManager()
        resilience_manager.register_service("test_service")
        
        async def always_failing_service():
            raise Exception("Service permanently unavailable")
        
        default_data = {"data": "fallback_value"}
        
        # Execute with fallback
        async with resilience_manager.resilient_call(
            "test_service",
            fallback_key="test_fallback",
            default_data=default_data
        ) as execute:
            result = await execute(always_failing_service)
        
        # Should use fallback data
        assert result["fallback_used"] is True
        assert result["data"] == default_data


@pytest.mark.asyncio
async def test_resilience_system_initialization():
    """Test complete resilience system initialization."""
    from src.infra_mind.core.resilience import initialize_system_resilience, shutdown_system_resilience
    
    # Mock the dependencies
    with patch('src.infra_mind.core.health_checks.initialize_health_checks') as mock_health, \
         patch('src.infra_mind.core.failover.initialize_failover_system') as mock_failover:
        
        mock_health.return_value = None
        mock_failover.return_value = None
        
        # Test initialization
        await initialize_system_resilience()
        
        # Verify all components were initialized
        mock_health.assert_called_once()
        mock_failover.assert_called_once()
        
        # Test shutdown
        with patch('src.infra_mind.core.health_checks.shutdown_health_checks') as mock_health_shutdown, \
             patch('src.infra_mind.core.failover.shutdown_failover_system') as mock_failover_shutdown:
            
            mock_health_shutdown.return_value = None
            mock_failover_shutdown.return_value = None
            
            await shutdown_system_resilience()
            
            mock_health_shutdown.assert_called_once()
            mock_failover_shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])