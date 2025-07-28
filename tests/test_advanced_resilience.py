"""
Tests for advanced resilience system including circuit breakers,
fallback mechanisms, and advanced rate limiting.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infra_mind.core.resilience import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    RetryMechanism, RetryConfig,
    FallbackManager, FallbackConfig,
    ResilienceManager,
    CircuitBreakerError, RetryExhaustedError, FallbackError
)

from src.infra_mind.core.advanced_rate_limiter import (
    AdvancedRateLimiter, RateLimitConfig, RateLimitAlgorithm,
    SlidingWindowRateLimiter, TokenBucketRateLimiter, AdaptiveRateLimiter,
    RateLimitExceeded, RateLimitResult
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit_config(self):
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=5,
            success_threshold=2,
            timeout=1.0
        )
    
    @pytest.fixture
    def circuit_breaker(self, circuit_config):
        return CircuitBreaker("test_service", circuit_config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state allows calls."""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after failure threshold."""
        async def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failure_count == 3
        
        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery through half-open state."""
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.1)  # Simulate time passage
        circuit_breaker.last_failure_time = time.time() - 6  # Force timeout
        
        # Check state should move to half-open
        await circuit_breaker._check_state()
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        
        # Successful calls should close the circuit
        for i in range(2):
            result = await circuit_breaker.call(success_func)
            assert result == "success"
        
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self, circuit_breaker):
        """Test circuit breaker timeout handling."""
        async def slow_func():
            await asyncio.sleep(2)  # Longer than timeout
            return "success"
        
        with pytest.raises(Exception, match="timeout"):
            await circuit_breaker.call(slow_func)
        
        assert circuit_breaker.failure_count == 1


class TestRetryMechanism:
    """Test retry mechanism functionality."""
    
    @pytest.fixture
    def retry_config(self):
        return RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False  # Disable for predictable testing
        )
    
    @pytest.fixture
    def retry_mechanism(self, retry_config):
        return RetryMechanism(retry_config)
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self, retry_mechanism):
        """Test successful execution on first attempt."""
        async def success_func():
            return "success"
        
        result = await retry_mechanism.execute(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, retry_mechanism):
        """Test successful execution after initial failures."""
        call_count = 0
        
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await retry_mechanism.execute(flaky_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self, retry_mechanism):
        """Test retry exhaustion after max attempts."""
        async def failing_func():
            raise Exception("Persistent failure")
        
        with pytest.raises(RetryExhaustedError):
            await retry_mechanism.execute(failing_func)
    
    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self, retry_mechanism):
        """Test non-retryable exceptions are not retried."""
        class NonRetryableError(Exception):
            pass
        
        # Configure to only retry specific exceptions
        retry_mechanism.config.retryable_exceptions = (ValueError,)
        
        async def non_retryable_func():
            raise NonRetryableError("Should not retry")
        
        with pytest.raises(NonRetryableError):
            await retry_mechanism.execute(non_retryable_func)
    
    def test_delay_calculation(self, retry_mechanism):
        """Test exponential backoff delay calculation."""
        # Test exponential backoff without jitter
        delay_0 = retry_mechanism._calculate_delay(0)
        delay_1 = retry_mechanism._calculate_delay(1)
        delay_2 = retry_mechanism._calculate_delay(2)
        
        assert delay_0 == 0.1  # base_delay
        assert delay_1 == 0.2  # base_delay * 2^1
        assert delay_2 == 0.4  # base_delay * 2^2


class TestFallbackManager:
    """Test fallback manager functionality."""
    
    @pytest.fixture
    def fallback_config(self):
        return FallbackConfig(
            enable_cache_fallback=True,
            cache_staleness_threshold=3600,
            enable_default_fallback=True,
            fallback_data_ttl=300,
            enable_degraded_mode=True
        )
    
    @pytest.fixture
    def fallback_manager(self, fallback_config):
        return FallbackManager(fallback_config)
    
    @pytest.mark.asyncio
    async def test_fallback_primary_success(self, fallback_manager):
        """Test successful primary function execution."""
        async def success_func():
            return {"data": "primary_result"}
        
        result = await fallback_manager.execute_with_fallback(
            success_func, "test_key"
        )
        
        assert result["data"]["data"] == "primary_result"
        assert result["source"] == "primary"
        assert not result["fallback_used"]
    
    @pytest.mark.asyncio
    async def test_fallback_with_default_data(self, fallback_manager):
        """Test fallback to default data on primary failure."""
        async def failing_func():
            raise Exception("Primary failure")
        
        default_data = {"data": "default_result"}
        
        result = await fallback_manager.execute_with_fallback(
            failing_func, "test_key", default_data=default_data
        )
        
        assert result["data"]["data"] == "default_result"
        assert result["source"] == "default"
        assert result["fallback_used"]
        assert result["degraded_mode"]
    
    @pytest.mark.asyncio
    async def test_fallback_degraded_mode(self, fallback_manager):
        """Test degraded mode fallback."""
        async def failing_func():
            raise Exception("Primary failure")
        
        result = await fallback_manager.execute_with_fallback(
            failing_func, "pricing_test_key"
        )
        
        assert result["data"]["degraded_mode"]
        assert result["source"] == "degraded_mode"
        assert result["fallback_used"]
        assert result["degraded_mode"]
    
    @pytest.mark.asyncio
    async def test_fallback_no_options_available(self, fallback_manager):
        """Test fallback failure when no options available."""
        # Disable all fallback options
        fallback_manager.config.enable_cache_fallback = False
        fallback_manager.config.enable_default_fallback = False
        fallback_manager.config.enable_degraded_mode = False
        
        async def failing_func():
            raise Exception("Primary failure")
        
        with pytest.raises(FallbackError):
            await fallback_manager.execute_with_fallback(
                failing_func, "test_key"
            )


class TestResilienceManager:
    """Test resilience manager coordination."""
    
    @pytest.fixture
    def resilience_manager(self):
        return ResilienceManager()
    
    @pytest.mark.asyncio
    async def test_resilience_manager_service_registration(self, resilience_manager):
        """Test service registration with resilience patterns."""
        circuit_config = CircuitBreakerConfig(failure_threshold=2)
        retry_config = RetryConfig(max_attempts=2)
        
        resilience_manager.register_service(
            "test_service", circuit_config, retry_config
        )
        
        assert "test_service" in resilience_manager.circuit_breakers
        assert "test_service" in resilience_manager.retry_configs
    
    @pytest.mark.asyncio
    async def test_resilient_call_success(self, resilience_manager):
        """Test successful resilient call."""
        resilience_manager.register_service("test_service")
        
        async with resilience_manager.resilient_call("test_service") as execute:
            async def success_func():
                return "success"
            
            result = await execute(success_func)
            assert result["data"] == "success"
            assert result["source"] == "primary"
    
    @pytest.mark.asyncio
    async def test_resilient_call_with_fallback(self, resilience_manager):
        """Test resilient call with fallback data."""
        resilience_manager.register_service("test_service")
        
        async with resilience_manager.resilient_call(
            "test_service", 
            fallback_key="test_key",
            default_data={"fallback": "data"}
        ) as execute:
            async def failing_func():
                raise Exception("Service failure")
            
            result = await execute(failing_func)
            assert result["fallback_used"]
            assert result["degraded_mode"]
    
    def test_service_health_status(self, resilience_manager):
        """Test service health status reporting."""
        resilience_manager.register_service("test_service")
        
        health = resilience_manager.get_service_health("test_service")
        assert health["name"] == "test_service"
        assert health["state"] == "closed"
        assert "failure_count" in health
    
    def test_reset_service(self, resilience_manager):
        """Test service reset functionality."""
        resilience_manager.register_service("test_service")
        
        # Simulate some failures
        circuit_breaker = resilience_manager.circuit_breakers["test_service"]
        circuit_breaker.failure_count = 5
        circuit_breaker.state = CircuitState.OPEN
        
        # Reset service
        success = resilience_manager.reset_service("test_service")
        assert success
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0


@pytest.mark.asyncio
class TestAdvancedRateLimiter:
    """Test advanced rate limiter functionality."""
    
    @pytest.fixture
    async def mock_redis(self):
        """Mock Redis client for testing."""
        redis_mock = AsyncMock()
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.zremrangebyscore = AsyncMock(return_value=0)
        redis_mock.zcard = AsyncMock(return_value=0)
        redis_mock.zadd = AsyncMock(return_value=1)
        redis_mock.expire = AsyncMock(return_value=True)
        redis_mock.hgetall = AsyncMock(return_value={})
        redis_mock.hset = AsyncMock(return_value=True)
        redis_mock.delete = AsyncMock(return_value=1)
        return redis_mock
    
    @pytest.fixture
    def rate_limit_config(self):
        return RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            requests_per_minute=10,
            window_size=60
        )
    
    @pytest.fixture
    def advanced_rate_limiter(self, mock_redis):
        return AdvancedRateLimiter(mock_redis)
    
    async def test_sliding_window_rate_limiter(self, mock_redis, rate_limit_config):
        """Test sliding window rate limiter."""
        limiter = SlidingWindowRateLimiter(mock_redis, rate_limit_config)
        
        # Mock Redis responses for allowed request
        mock_redis.zcard.return_value = 5  # Current count below limit
        
        result = await limiter.check_rate_limit("test_key", "user1")
        
        assert result.allowed
        assert result.remaining == 4  # 10 - 5 - 1
        assert result.algorithm_used == "sliding_window"
    
    async def test_sliding_window_rate_limit_exceeded(self, mock_redis, rate_limit_config):
        """Test sliding window rate limiter when limit exceeded."""
        limiter = SlidingWindowRateLimiter(mock_redis, rate_limit_config)
        
        # Mock Redis responses for exceeded limit
        mock_redis.zcard.return_value = 10  # At limit
        mock_redis.zrange.return_value = [(b"request1", 1234567890.0)]
        
        result = await limiter.check_rate_limit("test_key", "user1")
        
        assert not result.allowed
        assert result.remaining == 0
        assert result.retry_after is not None
    
    async def test_token_bucket_rate_limiter(self, mock_redis):
        """Test token bucket rate limiter."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_capacity=5,
            refill_rate=1.0
        )
        limiter = TokenBucketRateLimiter(mock_redis, config)
        
        # Mock empty bucket (new bucket)
        mock_redis.hgetall.return_value = {}
        
        result = await limiter.check_rate_limit("test_key", "user1")
        
        assert result.allowed
        assert result.remaining == 4  # 5 - 1
        assert result.algorithm_used == "token_bucket"
    
    async def test_token_bucket_insufficient_tokens(self, mock_redis):
        """Test token bucket when insufficient tokens."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_capacity=5,
            refill_rate=1.0
        )
        limiter = TokenBucketRateLimiter(mock_redis, config)
        
        # Mock bucket with insufficient tokens
        current_time = time.time()
        mock_redis.hgetall.return_value = {
            "tokens": "0.5",
            "last_refill": str(current_time - 1)
        }
        
        result = await limiter.check_rate_limit("test_key", "user1")
        
        assert not result.allowed
        assert result.retry_after is not None
    
    async def test_adaptive_rate_limiter(self, mock_redis, rate_limit_config):
        """Test adaptive rate limiter."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.ADAPTIVE,
            requests_per_minute=10,
            adaptive_threshold=0.8
        )
        limiter = AdaptiveRateLimiter(mock_redis, config)
        
        # Mock Redis responses
        mock_redis.hgetall.return_value = {}
        mock_redis.zcard.return_value = 3
        
        # Test with good success rate
        result = await limiter.check_rate_limit("test_key", "user1", success_rate=0.9)
        
        assert result.allowed
        assert result.algorithm_used == "adaptive"
        assert "adaptive_limit" in result.metadata
    
    async def test_advanced_rate_limiter_service_configuration(self, advanced_rate_limiter, rate_limit_config):
        """Test service configuration in advanced rate limiter."""
        advanced_rate_limiter.configure_service("test_service", rate_limit_config)
        
        assert "test_service" in advanced_rate_limiter.configs
        assert "test_service" in advanced_rate_limiter.limiters
    
    async def test_advanced_rate_limiter_check_limit(self, advanced_rate_limiter, rate_limit_config):
        """Test rate limit checking in advanced rate limiter."""
        advanced_rate_limiter.configure_service("test_service", rate_limit_config)
        
        # Mock the underlying limiter
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock(return_value=RateLimitResult(
            allowed=True,
            remaining=5,
            reset_time=None,
            retry_after=None,
            algorithm_used="sliding_window"
        ))
        advanced_rate_limiter.limiters["test_service"] = mock_limiter
        
        result = await advanced_rate_limiter.check_rate_limit("test_service")
        
        assert result.allowed
        assert result.remaining == 5
    
    async def test_advanced_rate_limiter_limit_exceeded(self, advanced_rate_limiter, rate_limit_config):
        """Test rate limit exceeded in advanced rate limiter."""
        advanced_rate_limiter.configure_service("test_service", rate_limit_config)
        
        # Mock the underlying limiter to return exceeded
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock(return_value=RateLimitResult(
            allowed=False,
            remaining=0,
            reset_time=datetime.now() + timedelta(seconds=60),
            retry_after=60,
            algorithm_used="sliding_window"
        ))
        advanced_rate_limiter.limiters["test_service"] = mock_limiter
        
        with pytest.raises(RateLimitExceeded) as exc_info:
            await advanced_rate_limiter.check_rate_limit("test_service")
        
        assert exc_info.value.retry_after == 60
        assert exc_info.value.result is not None
    
    async def test_rate_limit_status(self, advanced_rate_limiter, rate_limit_config):
        """Test rate limit status reporting."""
        advanced_rate_limiter.configure_service("test_service", rate_limit_config)
        
        status = await advanced_rate_limiter.get_rate_limit_status("test_service")
        
        assert status["configured"]
        assert status["algorithm"] == "sliding_window"
        assert status["requests_per_minute"] == 10
    
    async def test_reset_rate_limit(self, advanced_rate_limiter, rate_limit_config):
        """Test rate limit reset functionality."""
        advanced_rate_limiter.configure_service("test_service", rate_limit_config)
        
        success = await advanced_rate_limiter.reset_rate_limit("test_service")
        
        # Should succeed (mocked Redis delete returns 1)
        assert success


@pytest.mark.asyncio
async def test_integration_resilience_with_rate_limiting():
    """Test integration between resilience manager and rate limiting."""
    from src.infra_mind.core.resilience import resilience_manager, configure_service_resilience
    
    # Configure a service with resilience patterns
    configure_service_resilience(
        "integration_test_service",
        failure_threshold=2,
        recovery_timeout=30,
        max_retries=2
    )
    
    call_count = 0
    
    async def flaky_service():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Service temporarily unavailable")
        return {"data": "success", "call_count": call_count}
    
    # Test resilient call with retry
    async with resilience_manager.resilient_call(
        "integration_test_service",
        fallback_key="integration_test"
    ) as execute:
        result = await execute(flaky_service)
        
        assert result["data"]["data"] == "success"
        assert result["data"]["call_count"] == 3
        assert result["source"] == "primary"
        assert not result["fallback_used"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])