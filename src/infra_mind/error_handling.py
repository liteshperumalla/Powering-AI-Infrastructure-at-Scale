"""
Advanced Error Handling System

Comprehensive error handling with structured logging, error tracking,
circuit breakers, retry mechanisms, and error analytics.
"""

import traceback
import asyncio
import functools
import inspect
import time
from typing import Any, Dict, List, Optional, Type, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid

from loguru import logger
from .realtime.event_bus import EventBus, EventType, EventPriority


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category types."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"
    TIMEOUT = "timeout"
    INTERNAL = "internal"
    CONFIGURATION = "configuration"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.INTERNAL
    message: str = ""
    exception_type: str = ""
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_exceptions: tuple = (Exception,)
    stop_exceptions: tuple = ()


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_duration: float = 60.0
    expected_exception: Type[Exception] = Exception


class InfraMindException(Exception):
    """Base exception for Infra Mind application."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.correlation_id = correlation_id
        self.user_message = user_message or message
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()


class ValidationError(InfraMindException):
    """Validation error."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(
            message, 
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )
        if field:
            self.context["field"] = field


class AuthenticationError(InfraMindException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            **kwargs
        )


class AuthorizationError(InfraMindException):
    """Authorization error."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH, 
            category=ErrorCategory.AUTHORIZATION,
            **kwargs
        )


class NotFoundError(InfraMindException):
    """Resource not found error."""
    
    def __init__(self, message: str, resource_type: str = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.NOT_FOUND,
            **kwargs
        )
        if resource_type:
            self.context["resource_type"] = resource_type


class ExternalServiceError(InfraMindException):
    """External service error."""
    
    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL_SERVICE,
            **kwargs
        )
        if service_name:
            self.context["service_name"] = service_name


class RateLimitError(InfraMindException):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RATE_LIMIT,
            **kwargs
        )


class DatabaseError(InfraMindException):
    """Database error."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            **kwargs
        )
        if operation:
            self.context["operation"] = operation


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt_time:
                raise ExternalServiceError(f"Circuit breaker {self.name} is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            return self._handle_success(result)
            
        except self.config.expected_exception as e:
            self._handle_failure(e)
            raise
    
    def _handle_success(self, result):
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker {self.name} transitioned to CLOSED")
        
        return result
    
    def _handle_failure(self, exception):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if (self.state == CircuitState.CLOSED and 
            self.failure_count >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.config.timeout_duration
            logger.warning(f"Circuit breaker {self.name} transitioned to OPEN")
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.config.timeout_duration
            logger.warning(f"Circuit breaker {self.name} transitioned back to OPEN")


class ErrorTracker:
    """Error tracking and analytics."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.error_history: deque = deque(maxlen=10000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_trends: Dict[str, List[datetime]] = defaultdict(list)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def track_error(self, error_info: ErrorInfo):
        """Track an error occurrence."""
        # Add to history
        self.error_history.append(error_info)
        
        # Update counts
        self.error_counts[error_info.category.value] += 1
        self.error_counts[f"severity_{error_info.severity.value}"] += 1
        
        # Update trends
        self.error_trends[error_info.category.value].append(error_info.timestamp)
        
        # Clean old trend data (keep only last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        for category in self.error_trends:
            self.error_trends[category] = [
                ts for ts in self.error_trends[category] if ts > cutoff
            ]
        
        # Publish error event
        if self.event_bus:
            asyncio.create_task(self._publish_error_event(error_info))
        
        # Log error
        self._log_error(error_info)
    
    async def _publish_error_event(self, error_info: ErrorInfo):
        """Publish error event to event bus."""
        try:
            event_priority = {
                ErrorSeverity.LOW: EventPriority.LOW,
                ErrorSeverity.MEDIUM: EventPriority.NORMAL,
                ErrorSeverity.HIGH: EventPriority.HIGH,
                ErrorSeverity.CRITICAL: EventPriority.CRITICAL
            }.get(error_info.severity, EventPriority.NORMAL)
            
            await self.event_bus.publish_simple(
                EventType.SYSTEM_ERROR,
                {
                    "error_id": error_info.error_id,
                    "severity": error_info.severity.value,
                    "category": error_info.category.value,
                    "message": error_info.message,
                    "context": error_info.context,
                    "user_id": error_info.user_id,
                    "timestamp": error_info.timestamp.isoformat()
                },
                priority=event_priority,
                correlation_id=error_info.correlation_id
            )
        except Exception as e:
            logger.error(f"Failed to publish error event: {e}")
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level."""
        log_data = {
            "error_id": error_info.error_id,
            "category": error_info.category.value,
            "user_id": error_info.user_id,
            "correlation_id": error_info.correlation_id,
            "context": error_info.context
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"{error_info.message}", **log_data)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"{error_info.message}", **log_data)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"{error_info.message}", **log_data)
        else:
            logger.info(f"{error_info.message}", **log_data)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = len(self.error_history)
        
        # Error rate by category
        category_stats = {}
        for category in ErrorCategory:
            count = self.error_counts.get(category.value, 0)
            rate = (count / total_errors) * 100 if total_errors > 0 else 0
            category_stats[category.value] = {
                "count": count,
                "rate_percent": round(rate, 2)
            }
        
        # Error rate by severity
        severity_stats = {}
        for severity in ErrorSeverity:
            count = self.error_counts.get(f"severity_{severity.value}", 0)
            rate = (count / total_errors) * 100 if total_errors > 0 else 0
            severity_stats[severity.value] = {
                "count": count,
                "rate_percent": round(rate, 2)
            }
        
        # Recent error trend (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp > one_hour_ago
        ]
        
        return {
            "total_errors": total_errors,
            "recent_errors_1h": len(recent_errors),
            "error_rate_1h": len(recent_errors),  # errors per hour
            "category_breakdown": category_stats,
            "severity_breakdown": severity_stats,
            "circuit_breaker_states": {
                name: breaker.state.value 
                for name, breaker in self.circuit_breakers.items()
            }
        }
    
    def add_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Add a circuit breaker."""
        breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = breaker
        return breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)


class ErrorHandler:
    """Global error handler."""
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> ErrorInfo:
        """Handle an exception and create error info."""
        
        # Extract frame information
        frame = inspect.currentframe()
        caller_frame = frame.f_back if frame else None
        module_name = None
        function_name = None
        line_number = None
        
        if caller_frame:
            module_name = caller_frame.f_globals.get('__name__')
            function_name = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno
        
        # Determine error properties
        if isinstance(exception, InfraMindException):
            severity = exception.severity
            category = exception.category
            message = exception.message
            error_context = {**(context or {}), **exception.context}
            correlation_id = correlation_id or exception.correlation_id
        else:
            severity = ErrorSeverity.HIGH
            category = ErrorCategory.INTERNAL
            message = str(exception)
            error_context = context or {}
        
        # Create error info
        error_info = ErrorInfo(
            severity=severity,
            category=category,
            message=message,
            exception_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            context=error_context,
            user_id=user_id,
            correlation_id=correlation_id,
            module=module_name,
            function=function_name,
            line_number=line_number
        )
        
        # Track the error
        self.error_tracker.track_error(error_info)
        
        return error_info


# Global error handler instance
_error_tracker = ErrorTracker()
_error_handler = ErrorHandler(_error_tracker)


def handle_error(
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    reraise: bool = True
):
    """Decorator for handling errors."""
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = _error_handler.handle_exception(
                    e, context, user_id, correlation_id
                )
                if reraise:
                    raise
                return error_info
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = _error_handler.handle_exception(
                    e, context, user_id, correlation_id
                )
                if reraise:
                    raise
                return error_info
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry(config: RetryConfig = None):
    """Decorator for retry logic."""
    
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.stop_exceptions:
                    # Don't retry for stop exceptions
                    raise
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt, re-raise
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random())
                    
                    logger.debug(f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1}/{config.max_attempts})")
                    await asyncio.sleep(delay)
            
            # All retries failed
            if last_exception:
                raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.stop_exceptions:
                    # Don't retry for stop exceptions
                    raise
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt, re-raise
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random())
                    
                    logger.debug(f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1}/{config.max_attempts})")
                    time.sleep(delay)
            
            # All retries failed
            if last_exception:
                raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection."""
    
    if config is None:
        config = CircuitBreakerConfig()
    
    # Get or create circuit breaker
    breaker = _error_tracker.get_circuit_breaker(name)
    if breaker is None:
        breaker = _error_tracker.add_circuit_breaker(name, config)
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Utility functions

def get_error_stats() -> Dict[str, Any]:
    """Get global error statistics."""
    return _error_tracker.get_error_stats()


def set_event_bus(event_bus: EventBus):
    """Set the event bus for error tracking."""
    _error_tracker.event_bus = event_bus


def create_error_info(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> ErrorInfo:
    """Create and track an error info object."""
    
    error_info = ErrorInfo(
        severity=severity,
        category=category,
        message=message,
        context=context or {},
        user_id=user_id,
        correlation_id=correlation_id
    )
    
    _error_tracker.track_error(error_info)
    return error_info