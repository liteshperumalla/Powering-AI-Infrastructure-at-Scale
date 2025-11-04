"""
Circuit Breaker Pattern for LLM API Resilience.

Implements the circuit breaker pattern to protect against cascading failures
when LLM APIs (OpenAI, Anthropic, Azure) are experiencing issues.

Features:
- Three states: CLOSED, OPEN, HALF_OPEN
- Automatic failure detection and recovery
- Configurable thresholds and timeouts
- Metrics and monitoring
- Fallback strategies

Usage:
```python
circuit_breaker = LLMCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=openai.error.APIError
)

@circuit_breaker.call
async def call_llm_api(prompt: str):
    return await openai.ChatCompletion.create(...)

# Or use as context manager
async with circuit_breaker:
    result = await call_llm_api(prompt)
```
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any, Type, List
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    current_state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))

    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successful_calls + self.failed_calls
        if total == 0:
            return 0.0
        return (self.successful_calls / total) * 100


class LLMCircuitBreaker:
    """
    Circuit breaker for LLM API calls.

    Protects against cascading failures by temporarily blocking requests
    when the API is experiencing issues.
    """

    def __init__(
        self,
        name: str = "llm_circuit_breaker",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        half_open_max_calls: int = 3,
        expected_exception: Optional[Type[Exception]] = None,
        fallback: Optional[Callable] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successes needed in half-open to close circuit
            half_open_max_calls: Max calls allowed in half-open state
            expected_exception: Exception type that triggers the circuit
            fallback: Optional fallback function when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception or Exception
        self.fallback = fallback

        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s"
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from func
        """
        async with self._lock:
            # Check circuit state before calling
            if not self._can_execute():
                self.metrics.rejected_calls += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' is {self.state.value}, "
                    f"rejecting call"
                )

                # Use fallback if available
                if self.fallback:
                    logger.info(f"Using fallback for '{self.name}'")
                    return await self.fallback(*args, **kwargs)

                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is {self.state.value}. "
                    f"Service unavailable."
                )

        # Execute the call
        start_time = time.time()
        self.metrics.total_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success(time.time() - start_time)
            return result

        except self.expected_exception as e:
            await self._on_failure(e)
            raise

        except Exception as e:
            # Unexpected exception, don't count toward circuit breaker
            logger.error(f"Unexpected error in circuit breaker '{self.name}': {e}")
            raise

    def _can_execute(self) -> bool:
        """Check if call can be executed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        f"Circuit breaker '{self.name}' transitioning to HALF_OPEN "
                        f"after {elapsed:.1f}s"
                    )
                    self._transition_to_half_open()
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.half_open_calls < self.half_open_max_calls

        return False

    async def _on_success(self, response_time: float) -> None:
        """Handle successful call."""
        async with self._lock:
            self.metrics.successful_calls += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.now()
            self.metrics.response_times.append(response_time)

            # Update average response time
            if self.metrics.response_times:
                self.metrics.average_response_time = sum(self.metrics.response_times) / len(
                    self.metrics.response_times
                )

            # State transitions
            if self.state == CircuitState.HALF_OPEN:
                if self.metrics.consecutive_successes >= self.success_threshold:
                    logger.info(
                        f"Circuit breaker '{self.name}' recovered after "
                        f"{self.metrics.consecutive_successes} successful calls"
                    )
                    self._transition_to_closed()

            logger.debug(
                f"Circuit breaker '{self.name}' success: "
                f"response_time={response_time:.3f}s, "
                f"consecutive={self.metrics.consecutive_successes}"
            )

    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed call."""
        async with self._lock:
            self.metrics.failed_calls += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = datetime.now()
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' failure: "
                f"{type(exception).__name__}: {str(exception)}, "
                f"consecutive={self.metrics.consecutive_failures}"
            )

            # State transitions
            if self.state == CircuitState.CLOSED:
                if self.metrics.consecutive_failures >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker '{self.name}' opening after "
                        f"{self.metrics.consecutive_failures} consecutive failures"
                    )
                    self._transition_to_open()

            elif self.state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' re-opening after failure in "
                    "HALF_OPEN state"
                )
                self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.metrics.state_changes += 1
        self.metrics.current_state = CircuitState.OPEN
        self.half_open_calls = 0

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.metrics.state_changes += 1
        self.metrics.current_state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes = 0

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.metrics.state_changes += 1
        self.metrics.current_state = CircuitState.CLOSED
        self.half_open_calls = 0
        self.metrics.consecutive_failures = 0

    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        return self.metrics

    def get_state(self) -> CircuitState:
        """Get current state."""
        return self.state

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        logger.info(f"Resetting circuit breaker '{self.name}'")
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_failure_time = None
        self.half_open_calls = 0

    async def __aenter__(self):
        """Context manager entry."""
        if not self._can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            await self._on_success(0)
        elif isinstance(exc_val, self.expected_exception):
            await self._on_failure(exc_val)
        return False


class LLMCircuitBreakerManager:
    """
    Manages multiple circuit breakers for different LLM providers.

    Provides a centralized way to manage circuit breakers for
    OpenAI, Anthropic, Azure OpenAI, etc.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self.breakers: dict[str, LLMCircuitBreaker] = {}
        logger.info("LLM Circuit Breaker Manager initialized")

    def create_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        **kwargs,
    ) -> LLMCircuitBreaker:
        """
        Create and register a circuit breaker.

        Args:
            name: Unique identifier for the breaker
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before attempting recovery
            **kwargs: Additional LLMCircuitBreaker arguments

        Returns:
            Created circuit breaker
        """
        if name in self.breakers:
            logger.warning(f"Circuit breaker '{name}' already exists, returning existing")
            return self.breakers[name]

        breaker = LLMCircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            **kwargs,
        )
        self.breakers[name] = breaker

        logger.info(f"Created circuit breaker '{name}'")
        return breaker

    def get_breaker(self, name: str) -> Optional[LLMCircuitBreaker]:
        """Get circuit breaker by name."""
        return self.breakers.get(name)

    def get_all_metrics(self) -> dict[str, CircuitBreakerMetrics]:
        """Get metrics for all circuit breakers."""
        return {name: breaker.get_metrics() for name, breaker in self.breakers.items()}

    def get_health_status(self) -> dict[str, Any]:
        """
        Get health status of all circuit breakers.

        Returns:
            Dictionary with health status for each breaker
        """
        status = {}
        for name, breaker in self.breakers.items():
            metrics = breaker.get_metrics()
            status[name] = {
                "state": breaker.get_state().value,
                "success_rate": metrics.success_rate(),
                "total_calls": metrics.total_calls,
                "failed_calls": metrics.failed_calls,
                "rejected_calls": metrics.rejected_calls,
                "consecutive_failures": metrics.consecutive_failures,
                "average_response_time": metrics.average_response_time,
                "healthy": breaker.get_state() == CircuitState.CLOSED,
            }
        return status

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        logger.info("Resetting all circuit breakers")
        for breaker in self.breakers.values():
            breaker.reset()


# Global circuit breaker manager instance
circuit_breaker_manager = LLMCircuitBreakerManager()


# Example usage:
"""
# Create circuit breakers for different LLM providers
openai_breaker = circuit_breaker_manager.create_breaker(
    name="openai",
    failure_threshold=5,
    recovery_timeout=60,
)

anthropic_breaker = circuit_breaker_manager.create_breaker(
    name="anthropic",
    failure_threshold=3,
    recovery_timeout=30,
)

# Use in LLM calls
async def call_openai_with_protection(prompt: str):
    return await openai_breaker.call(
        openai.ChatCompletion.create,
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Or as context manager
async def call_anthropic_with_protection(prompt: str):
    async with anthropic_breaker:
        return await anthropic.completions.create(
            model="claude-2",
            prompt=prompt
        )

# Get health status
health = circuit_breaker_manager.get_health_status()
print(health)
# {
#     "openai": {
#         "state": "closed",
#         "success_rate": 98.5,
#         "healthy": true
#     },
#     "anthropic": {
#         "state": "half_open",
#         "success_rate": 85.2,
#         "healthy": false
#     }
# }
"""
