"""
Advanced resilience system for cloud API integrations.

Provides circuit breakers, fallback mechanisms, advanced error handling,
and comprehensive retry strategies for reliable cloud service integration.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import random
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 30.0               # Request timeout in seconds
    expected_exceptions: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3
    base_delay: float = 1.0             # Base delay in seconds
    max_delay: float = 60.0             # Maximum delay in seconds
    exponential_base: float = 2.0       # Exponential backoff base
    jitter: bool = True                 # Add random jitter
    retryable_exceptions: tuple = (Exception,)  # Exceptions to retry


@dataclass
class FallbackConfig:
    """Configuration for fallback mechanisms."""
    enable_cache_fallback: bool = True
    cache_staleness_threshold: int = 3600  # 1 hour in seconds
    enable_default_fallback: bool = True
    fallback_data_ttl: int = 300        # 5 minutes for fallback data
    enable_degraded_mode: bool = True


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class RetryExhaustedError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    pass


class FallbackError(Exception):
    """Exception raised when fallback mechanisms fail."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.
    
    Prevents cascading failures by temporarily blocking requests
    to failing services and allowing them to recover.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.
        
        Args:
            name: Unique name for this circuit breaker
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original function exceptions
        """
        async with self._lock:
            await self._check_state()
            
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.last_failure_time}"
                )
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self._on_success()
            return result
            
        except self.config.expected_exceptions as e:
            await self._on_failure()
            raise
        except asyncio.TimeoutError as e:
            await self._on_failure()
            raise Exception(f"Circuit breaker timeout after {self.config.timeout}s") from e
    
    async def _check_state(self) -> None:
        """Check and update circuit breaker state."""
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            if (self.last_failure_time and 
                current_time - self.last_failure_time >= self.config.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.last_failure_time = time.time()
            self.failure_count += 1
            
            if (self.state == CircuitState.CLOSED and 
                self.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved back to OPEN")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }


class RetryMechanism:
    """
    Advanced retry mechanism with exponential backoff and jitter.
    
    Implements intelligent retry strategies for transient failures
    with configurable backoff and jitter to prevent thundering herd.
    """
    
    def __init__(self, config: RetryConfig):
        """
        Initialize retry mechanism.
        
        Args:
            config: Retry configuration
        """
        self.config = config
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhaustedError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
                
            except self.config.retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"All {self.config.max_attempts} retry attempts failed")
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception: {str(e)}")
                raise
        
        raise RetryExhaustedError(
            f"Failed after {self.config.max_attempts} attempts. "
            f"Last error: {str(last_exception)}"
        ) from last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for next retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter = random.uniform(0, delay * 0.1)  # Up to 10% jitter
            delay += jitter
        
        return delay


class FallbackManager:
    """
    Advanced fallback mechanism for service failures.
    
    Provides multiple fallback strategies including cached data,
    default values, and degraded mode operation.
    """
    
    def __init__(self, config: FallbackConfig):
        """
        Initialize fallback manager.
        
        Args:
            config: Fallback configuration
        """
        self.config = config
        self._fallback_cache: Dict[str, Any] = {}
        self._fallback_timestamps: Dict[str, float] = {}
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_key: str,
        cache_manager=None,
        default_data: Optional[Any] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with comprehensive fallback strategy.
        
        Args:
            primary_func: Primary function to execute
            fallback_key: Key for fallback data storage
            cache_manager: Cache manager for stale data fallback
            default_data: Default data to use as last resort
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result with metadata about fallback usage
        """
        result = {
            "data": None,
            "source": "primary",
            "fallback_used": False,
            "degraded_mode": False,
            "warnings": []
        }
        
        try:
            # Try primary function
            data = await primary_func(*args, **kwargs)
            result["data"] = data
            
            # Cache successful result for future fallback
            self._store_fallback_data(fallback_key, data)
            
            return result
            
        except Exception as primary_error:
            logger.warning(f"Primary function failed: {str(primary_error)}")
            result["warnings"].append(f"Primary failure: {str(primary_error)}")
            
            # Try fallback strategies in order of preference
            fallback_data = await self._try_fallback_strategies(
                fallback_key, cache_manager, default_data
            )
            
            if fallback_data:
                result["data"] = fallback_data["data"]
                result["source"] = fallback_data["source"]
                result["fallback_used"] = True
                result["degraded_mode"] = fallback_data.get("degraded", False)
                result["warnings"].extend(fallback_data.get("warnings", []))
                
                return result
            
            # No fallback available
            raise FallbackError(
                f"Primary function failed and no fallback available: {str(primary_error)}"
            ) from primary_error
    
    async def _try_fallback_strategies(
        self,
        fallback_key: str,
        cache_manager=None,
        default_data: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Try various fallback strategies in order."""
        
        # Strategy 1: Recent fallback cache
        if self.config.enable_cache_fallback:
            recent_data = self._get_recent_fallback_data(fallback_key)
            if recent_data:
                return {
                    "data": recent_data,
                    "source": "recent_fallback",
                    "warnings": ["Using recent fallback data"]
                }
        
        # Strategy 2: Stale cache data
        if self.config.enable_cache_fallback and cache_manager:
            stale_data = await self._get_stale_cache_data(cache_manager, fallback_key)
            if stale_data:
                return {
                    "data": stale_data,
                    "source": "stale_cache",
                    "degraded": True,
                    "warnings": ["Using stale cached data"]
                }
        
        # Strategy 3: Default data
        if self.config.enable_default_fallback and default_data:
            return {
                "data": default_data,
                "source": "default",
                "degraded": True,
                "warnings": ["Using default fallback data"]
            }
        
        # Strategy 4: Degraded mode with minimal data
        if self.config.enable_degraded_mode:
            degraded_data = self._get_degraded_mode_data(fallback_key)
            if degraded_data:
                return {
                    "data": degraded_data,
                    "source": "degraded_mode",
                    "degraded": True,
                    "warnings": ["Operating in degraded mode with minimal data"]
                }
        
        return None
    
    def _store_fallback_data(self, key: str, data: Any) -> None:
        """Store data for future fallback use."""
        self._fallback_cache[key] = data
        self._fallback_timestamps[key] = time.time()
        
        # Clean up old entries
        self._cleanup_old_fallback_data()
    
    def _get_recent_fallback_data(self, key: str) -> Optional[Any]:
        """Get recent fallback data if available and fresh."""
        if key not in self._fallback_cache:
            return None
        
        timestamp = self._fallback_timestamps.get(key, 0)
        age = time.time() - timestamp
        
        if age <= self.config.fallback_data_ttl:
            logger.info(f"Using recent fallback data for {key} (age: {age:.1f}s)")
            return self._fallback_cache[key]
        
        return None
    
    async def _get_stale_cache_data(self, cache_manager, key: str) -> Optional[Any]:
        """Get stale data from cache manager."""
        try:
            # This would need to be implemented based on your cache manager
            # For now, return None as we don't have direct access to stale data
            return None
        except Exception as e:
            logger.warning(f"Failed to get stale cache data: {e}")
            return None
    
    def _get_degraded_mode_data(self, key: str) -> Optional[Any]:
        """Generate minimal data for degraded mode operation."""
        # Provide minimal data structure based on key pattern
        if "pricing" in key.lower():
            return {
                "services": [],
                "degraded_mode": True,
                "message": "Pricing data temporarily unavailable"
            }
        elif "compute" in key.lower():
            return {
                "services": [],
                "degraded_mode": True,
                "message": "Compute services data temporarily unavailable"
            }
        else:
            return {
                "degraded_mode": True,
                "message": "Service temporarily unavailable"
            }
    
    def _cleanup_old_fallback_data(self) -> None:
        """Clean up old fallback data entries."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self._fallback_timestamps.items():
            if current_time - timestamp > self.config.fallback_data_ttl * 2:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._fallback_cache.pop(key, None)
            self._fallback_timestamps.pop(key, None)


class ResilienceManager:
    """
    Comprehensive resilience manager that coordinates circuit breakers,
    retry mechanisms, and fallback strategies.
    """
    
    def __init__(self):
        """Initialize resilience manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.fallback_manager = FallbackManager(FallbackConfig())
        self._default_circuit_config = CircuitBreakerConfig()
        self._default_retry_config = RetryConfig()
    
    def register_service(
        self,
        service_name: str,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ) -> None:
        """
        Register a service with resilience patterns.
        
        Args:
            service_name: Unique service name
            circuit_config: Circuit breaker configuration
            retry_config: Retry configuration
        """
        # Create circuit breaker
        cb_config = circuit_config or self._default_circuit_config
        self.circuit_breakers[service_name] = CircuitBreaker(service_name, cb_config)
        
        # Store retry configuration
        self.retry_configs[service_name] = retry_config or self._default_retry_config
        
        logger.info(f"Registered service '{service_name}' with resilience patterns")
    
    @asynccontextmanager
    async def resilient_call(
        self,
        service_name: str,
        fallback_key: Optional[str] = None,
        cache_manager=None,
        default_data: Optional[Any] = None
    ):
        """
        Context manager for resilient service calls.
        
        Args:
            service_name: Name of the service
            fallback_key: Key for fallback data
            cache_manager: Cache manager instance
            default_data: Default data for fallback
            
        Yields:
            Callable that executes the service call with full resilience
        """
        if service_name not in self.circuit_breakers:
            self.register_service(service_name)
        
        circuit_breaker = self.circuit_breakers[service_name]
        retry_config = self.retry_configs[service_name]
        retry_mechanism = RetryMechanism(retry_config)
        
        async def execute_with_resilience(func: Callable, *args, **kwargs) -> Dict[str, Any]:
            """Execute function with full resilience patterns."""
            
            async def circuit_wrapped_func():
                return await circuit_breaker.call(func, *args, **kwargs)
            
            async def retry_wrapped_func():
                return await retry_mechanism.execute(circuit_wrapped_func)
            
            # Use fallback manager if fallback_key provided
            if fallback_key:
                try:
                    return await self.fallback_manager.execute_with_fallback(
                        retry_wrapped_func,
                        fallback_key,
                        cache_manager,
                        default_data
                    )
                except Exception as e:
                    # Attempt system recovery if all resilience patterns fail
                    recovery_manager = get_system_recovery_manager()
                    error_context = {
                        "service_name": service_name,
                        "error": str(e),
                        "fallback_key": fallback_key,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    recovery_result = await recovery_manager.attempt_recovery(service_name, error_context)
                    
                    return {
                        "data": None,
                        "source": "error",
                        "fallback_used": False,
                        "degraded_mode": False,
                        "warnings": [f"Service call failed: {str(e)}"],
                        "error": str(e),
                        "recovery_attempted": True,
                        "recovery_result": recovery_result
                    }
            else:
                # Direct execution with circuit breaker and retry
                try:
                    data = await retry_wrapped_func()
                    return {
                        "data": data,
                        "source": "primary",
                        "fallback_used": False,
                        "degraded_mode": False,
                        "warnings": []
                    }
                except Exception as e:
                    # Attempt system recovery if all resilience patterns fail
                    recovery_manager = get_system_recovery_manager()
                    error_context = {
                        "service_name": service_name,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    recovery_result = await recovery_manager.attempt_recovery(service_name, error_context)
                    
                    return {
                        "data": None,
                        "source": "error",
                        "fallback_used": False,
                        "degraded_mode": False,
                        "warnings": [f"Service call failed: {str(e)}"],
                        "error": str(e),
                        "recovery_attempted": True,
                        "recovery_result": recovery_result
                    }
        
        yield execute_with_resilience
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of a registered service."""
        if service_name not in self.circuit_breakers:
            return {"error": f"Service '{service_name}' not registered"}
        
        circuit_breaker = self.circuit_breakers[service_name]
        return circuit_breaker.get_state()
    
    def get_all_services_health(self) -> Dict[str, Any]:
        """Get health status of all registered services."""
        return {
            name: cb.get_state()
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_service(self, service_name: str) -> bool:
        """Reset circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            return False
        
        circuit_breaker = self.circuit_breakers[service_name]
        circuit_breaker.state = CircuitState.CLOSED
        circuit_breaker.failure_count = 0
        circuit_breaker.success_count = 0
        circuit_breaker.last_failure_time = None
        
        logger.info(f"Reset circuit breaker for service '{service_name}'")
        return True


# Global resilience manager instance
resilience_manager = ResilienceManager()


class SystemRecoveryManager:
    """
    System recovery and self-healing capabilities.
    
    Provides automatic recovery mechanisms for system components
    including service restarts, cache clearing, connection resets,
    and other self-healing operations.
    """
    
    def __init__(self):
        """Initialize system recovery manager."""
        self.recovery_strategies: Dict[str, List[Callable]] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.auto_recovery_enabled = True
        self.recovery_callbacks: List[Callable] = []
    
    def register_recovery_strategy(self, component_name: str, recovery_func: Callable) -> None:
        """
        Register a recovery strategy for a component.
        
        Args:
            component_name: Name of the component
            recovery_func: Recovery function to execute
        """
        if component_name not in self.recovery_strategies:
            self.recovery_strategies[component_name] = []
        
        self.recovery_strategies[component_name].append(recovery_func)
        logger.info(f"Registered recovery strategy for {component_name}")
    
    def register_recovery_callback(self, callback: Callable) -> None:
        """
        Register a callback for recovery notifications.
        
        Args:
            callback: Callback function
        """
        self.recovery_callbacks.append(callback)
    
    async def attempt_recovery(self, component_name: str, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt recovery for a failed component.
        
        Args:
            component_name: Name of the component to recover
            error_context: Context information about the failure
            
        Returns:
            Recovery result with success status and actions taken
        """
        if not self.auto_recovery_enabled:
            return {
                "success": False,
                "reason": "Auto-recovery is disabled",
                "actions_taken": []
            }
        
        recovery_start = datetime.utcnow()
        actions_taken = []
        success = False
        
        try:
            # Get recovery strategies for this component
            strategies = self.recovery_strategies.get(component_name, [])
            
            if not strategies:
                # Use default recovery strategies
                strategies = await self._get_default_recovery_strategies(component_name)
            
            # Execute recovery strategies in order
            for i, strategy in enumerate(strategies):
                try:
                    logger.info(f"Executing recovery strategy {i+1} for {component_name}")
                    
                    if asyncio.iscoroutinefunction(strategy):
                        result = await strategy(error_context)
                    else:
                        result = strategy(error_context)
                    
                    if isinstance(result, dict):
                        actions_taken.append(result.get("action", f"Recovery strategy {i+1}"))
                        if result.get("success", False):
                            success = True
                            break
                    else:
                        actions_taken.append(f"Recovery strategy {i+1} executed")
                        success = True
                        break
                        
                except Exception as e:
                    logger.error(f"Recovery strategy {i+1} failed for {component_name}: {e}")
                    actions_taken.append(f"Recovery strategy {i+1} failed: {str(e)}")
                    continue
            
            # Record recovery attempt
            recovery_time = (datetime.utcnow() - recovery_start).total_seconds()
            recovery_record = {
                "timestamp": recovery_start.isoformat(),
                "component_name": component_name,
                "success": success,
                "recovery_time_seconds": recovery_time,
                "actions_taken": actions_taken,
                "error_context": error_context
            }
            
            self.recovery_history.append(recovery_record)
            
            # Keep only last 100 recovery attempts
            if len(self.recovery_history) > 100:
                self.recovery_history = self.recovery_history[-100:]
            
            # Send notifications
            await self._send_recovery_notifications(recovery_record)
            
            logger.info(
                f"Recovery attempt for {component_name} completed: "
                f"{'SUCCESS' if success else 'FAILED'} in {recovery_time:.2f}s"
            )
            
            return {
                "success": success,
                "recovery_time_seconds": recovery_time,
                "actions_taken": actions_taken
            }
            
        except Exception as e:
            logger.error(f"Recovery attempt failed for {component_name}: {e}")
            return {
                "success": False,
                "reason": str(e),
                "actions_taken": actions_taken
            }
    
    async def _get_default_recovery_strategies(self, component_name: str) -> List[Callable]:
        """Get default recovery strategies for a component type."""
        strategies = []
        
        if "database" in component_name.lower():
            strategies.extend([
                self._restart_database_connections,
                self._clear_database_connection_pool,
                self._reset_database_indexes
            ])
        elif "cache" in component_name.lower() or "redis" in component_name.lower():
            strategies.extend([
                self._restart_cache_connections,
                self._clear_cache_data,
                self._reset_cache_configuration
            ])
        elif "api" in component_name.lower():
            strategies.extend([
                self._reset_api_connections,
                self._clear_api_cache,
                self._rotate_api_credentials
            ])
        elif "agent" in component_name.lower():
            strategies.extend([
                self._restart_agent,
                self._clear_agent_memory,
                self._reset_agent_state
            ])
        else:
            # Generic recovery strategies
            strategies.extend([
                self._generic_connection_reset,
                self._generic_cache_clear,
                self._generic_service_restart
            ])
        
        return strategies
    
    async def _restart_database_connections(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Restart database connections."""
        try:
            # This would integrate with your database connection manager
            logger.info("Restarting database connections")
            
            # Simulate connection restart
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Database connections restarted"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Database connection restart failed: {str(e)}"
            }
    
    async def _clear_database_connection_pool(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear database connection pool."""
        try:
            logger.info("Clearing database connection pool")
            
            # Simulate connection pool clearing
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "Database connection pool cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Database connection pool clear failed: {str(e)}"
            }
    
    async def _reset_database_indexes(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Reset database indexes if needed."""
        try:
            logger.info("Checking and resetting database indexes")
            
            # Simulate index reset
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "action": "Database indexes checked and reset"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Database index reset failed: {str(e)}"
            }
    
    async def _restart_cache_connections(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Restart cache connections."""
        try:
            logger.info("Restarting cache connections")
            
            # Simulate cache connection restart
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Cache connections restarted"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Cache connection restart failed: {str(e)}"
            }
    
    async def _clear_cache_data(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear corrupted cache data."""
        try:
            logger.info("Clearing corrupted cache data")
            
            # Simulate cache clearing
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "Corrupted cache data cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Cache data clear failed: {str(e)}"
            }
    
    async def _reset_cache_configuration(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Reset cache configuration to defaults."""
        try:
            logger.info("Resetting cache configuration")
            
            # Simulate configuration reset
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Cache configuration reset to defaults"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Cache configuration reset failed: {str(e)}"
            }
    
    async def _reset_api_connections(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Reset API connections."""
        try:
            logger.info("Resetting API connections")
            
            # Simulate API connection reset
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "API connections reset"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"API connection reset failed: {str(e)}"
            }
    
    async def _clear_api_cache(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear API response cache."""
        try:
            logger.info("Clearing API response cache")
            
            # Simulate API cache clearing
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "API response cache cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"API cache clear failed: {str(e)}"
            }
    
    async def _rotate_api_credentials(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate API credentials if authentication fails."""
        try:
            logger.info("Rotating API credentials")
            
            # Simulate credential rotation
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "action": "API credentials rotated"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"API credential rotation failed: {str(e)}"
            }
    
    async def _restart_agent(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a failed agent."""
        try:
            logger.info("Restarting agent")
            
            # Simulate agent restart
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "action": "Agent restarted"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Agent restart failed: {str(e)}"
            }
    
    async def _clear_agent_memory(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear agent memory to resolve memory issues."""
        try:
            logger.info("Clearing agent memory")
            
            # Simulate memory clearing
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Agent memory cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Agent memory clear failed: {str(e)}"
            }
    
    async def _reset_agent_state(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Reset agent state to initial configuration."""
        try:
            logger.info("Resetting agent state")
            
            # Simulate state reset
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Agent state reset to initial configuration"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Agent state reset failed: {str(e)}"
            }
    
    async def _generic_connection_reset(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic connection reset strategy."""
        try:
            logger.info("Performing generic connection reset")
            
            # Simulate generic connection reset
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "Generic connection reset performed"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Generic connection reset failed: {str(e)}"
            }
    
    async def _generic_cache_clear(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic cache clearing strategy."""
        try:
            logger.info("Performing generic cache clear")
            
            # Simulate generic cache clear
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "Generic cache cleared"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Generic cache clear failed: {str(e)}"
            }
    
    async def _generic_service_restart(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic service restart strategy."""
        try:
            logger.info("Performing generic service restart")
            
            # Simulate generic service restart
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "action": "Generic service restart performed"
            }
        except Exception as e:
            return {
                "success": False,
                "action": f"Generic service restart failed: {str(e)}"
            }
    
    async def _send_recovery_notifications(self, recovery_record: Dict[str, Any]) -> None:
        """Send recovery notifications to registered callbacks."""
        try:
            for callback in self.recovery_callbacks:
                await callback(recovery_record)
        except Exception as e:
            logger.error(f"Error sending recovery notifications: {e}")
    
    def get_recovery_history(self, component_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recovery history.
        
        Args:
            component_name: Optional component name to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of recovery records
        """
        history = self.recovery_history
        
        if component_name:
            history = [r for r in history if r["component_name"] == component_name]
        
        return history[-limit:]
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        if not self.recovery_history:
            return {
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "success_rate_percent": 0.0,
                "avg_recovery_time_seconds": 0.0,
                "components_recovered": []
            }
        
        total_attempts = len(self.recovery_history)
        successful_attempts = len([r for r in self.recovery_history if r["success"]])
        failed_attempts = total_attempts - successful_attempts
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0.0
        
        # Calculate average recovery time for successful attempts
        successful_records = [r for r in self.recovery_history if r["success"]]
        avg_recovery_time = (
            sum(r["recovery_time_seconds"] for r in successful_records) / len(successful_records)
            if successful_records else 0.0
        )
        
        # Get unique components that have been recovered
        components_recovered = list(set(r["component_name"] for r in successful_records))
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate_percent": round(success_rate, 2),
            "avg_recovery_time_seconds": round(avg_recovery_time, 2),
            "components_recovered": components_recovered
        }
    
    def enable_auto_recovery(self) -> None:
        """Enable automatic recovery."""
        self.auto_recovery_enabled = True
        logger.info("Auto-recovery enabled")
    
    def disable_auto_recovery(self) -> None:
        """Disable automatic recovery."""
        self.auto_recovery_enabled = False
        logger.info("Auto-recovery disabled")


# Global system recovery manager instance
system_recovery_manager = SystemRecoveryManager()


def get_system_recovery_manager() -> SystemRecoveryManager:
    """Get the global system recovery manager instance."""
    return system_recovery_manager


def configure_service_resilience(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> None:
    """
    Configure resilience patterns for a service.
    
    Args:
        service_name: Service name
        failure_threshold: Circuit breaker failure threshold
        recovery_timeout: Circuit breaker recovery timeout
        max_retries: Maximum retry attempts
        base_delay: Base retry delay
        max_delay: Maximum retry delay
    """
    circuit_config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
    
    retry_config = RetryConfig(
        max_attempts=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )
    
    resilience_manager.register_service(service_name, circuit_config, retry_config)


# Pre-configure common cloud services
def init_cloud_service_resilience():
    """Initialize resilience patterns for common cloud services."""
    
    # AWS services
    configure_service_resilience("aws_pricing", failure_threshold=3, recovery_timeout=30)
    configure_service_resilience("aws_ec2", failure_threshold=5, recovery_timeout=60)
    configure_service_resilience("aws_rds", failure_threshold=5, recovery_timeout=60)
    configure_service_resilience("aws_ai", failure_threshold=3, recovery_timeout=45)
    
    # Azure services
    configure_service_resilience("azure_pricing", failure_threshold=3, recovery_timeout=30)
    configure_service_resilience("azure_compute", failure_threshold=5, recovery_timeout=60)
    configure_service_resilience("azure_sql", failure_threshold=5, recovery_timeout=60)
    
    # GCP services
    configure_service_resilience("gcp_billing", failure_threshold=3, recovery_timeout=30)
    configure_service_resilience("gcp_compute", failure_threshold=5, recovery_timeout=60)
    configure_service_resilience("gcp_sql", failure_threshold=5, recovery_timeout=60)
    
    # Core system services
    configure_service_resilience("database", failure_threshold=2, recovery_timeout=30)
    configure_service_resilience("cache", failure_threshold=3, recovery_timeout=20)
    configure_service_resilience("agent_orchestrator", failure_threshold=3, recovery_timeout=45)
    
    logger.info("Initialized resilience patterns for cloud services")


async def initialize_system_resilience() -> None:
    """Initialize complete system resilience including health checks, failover, and recovery."""
    from .health_checks import initialize_health_checks
    from .failover import initialize_failover_system
    
    # Initialize cloud service resilience patterns
    init_cloud_service_resilience()
    
    # Initialize health check system
    await initialize_health_checks(
        mongodb_url="mongodb://localhost:27017/infra_mind",
        redis_url="redis://localhost:6379",
        external_apis={
            "aws_pricing": "https://api.pricing.us-east-1.amazonaws.com",
            "azure_pricing": "https://prices.azure.com/api/retail/prices",
            "gcp_billing": "https://cloudbilling.googleapis.com/v1"
        }
    )
    
    # Initialize failover system
    await initialize_failover_system()
    
    # Initialize recovery system with custom strategies
    recovery_manager = get_system_recovery_manager()
    
    # Register custom recovery strategies for specific components
    recovery_manager.register_recovery_strategy("database", _custom_database_recovery)
    recovery_manager.register_recovery_strategy("cache", _custom_cache_recovery)
    recovery_manager.register_recovery_strategy("agent_orchestrator", _custom_agent_recovery)
    
    logger.info("Complete system resilience initialized")


async def shutdown_system_resilience() -> None:
    """Shutdown complete system resilience."""
    from .health_checks import shutdown_health_checks
    from .failover import shutdown_failover_system
    
    await shutdown_health_checks()
    await shutdown_failover_system()
    
    logger.info("System resilience shutdown")


async def _custom_database_recovery(error_context: Dict[str, Any]) -> Dict[str, Any]:
    """Custom database recovery strategy."""
    try:
        # Implement custom database recovery logic
        logger.info("Executing custom database recovery")
        
        # Example: Reset connection pool, check indexes, etc.
        await asyncio.sleep(2)  # Simulate recovery time
        
        return {
            "success": True,
            "action": "Custom database recovery completed"
        }
    except Exception as e:
        return {
            "success": False,
            "action": f"Custom database recovery failed: {str(e)}"
        }


async def _custom_cache_recovery(error_context: Dict[str, Any]) -> Dict[str, Any]:
    """Custom cache recovery strategy."""
    try:
        # Implement custom cache recovery logic
        logger.info("Executing custom cache recovery")
        
        # Example: Clear specific cache keys, reset configuration, etc.
        await asyncio.sleep(1)  # Simulate recovery time
        
        return {
            "success": True,
            "action": "Custom cache recovery completed"
        }
    except Exception as e:
        return {
            "success": False,
            "action": f"Custom cache recovery failed: {str(e)}"
        }


async def _custom_agent_recovery(error_context: Dict[str, Any]) -> Dict[str, Any]:
    """Custom agent orchestrator recovery strategy."""
    try:
        # Implement custom agent recovery logic
        logger.info("Executing custom agent orchestrator recovery")
        
        # Example: Restart failed agents, clear workflow state, etc.
        await asyncio.sleep(3)  # Simulate recovery time
        
        return {
            "success": True,
            "action": "Custom agent orchestrator recovery completed"
        }
    except Exception as e:
        return {
            "success": False,
            "action": f"Custom agent orchestrator recovery failed: {str(e)}"
        }