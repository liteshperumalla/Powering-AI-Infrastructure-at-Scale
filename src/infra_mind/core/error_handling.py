"""
Comprehensive Error Handling System for Infra Mind.

Implements retry mechanisms with exponential backoff, graceful degradation,
fallback mechanisms, and comprehensive error logging and monitoring.
"""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import uuid
import json

from .resilience import (
    resilience_manager, RetryConfig, CircuitBreakerConfig, 
    FallbackConfig, RetryExhaustedError, CircuitBreakerError, FallbackError
)
from .advanced_logging import (
    get_agent_logger, get_workflow_logger, get_performance_logger,
    log_context, LogCategory, LogLevel
)
from .metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    AGENT_ERROR = "agent_error"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"
    DATA_ERROR = "data_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    DEGRADE = "degrade"
    FAIL_FAST = "fail_fast"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    agent_name: Optional[str] = None
    step_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    error_type: str
    error_message: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    original_exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    recovery_strategy: Optional[RecoveryStrategy] = None
    retry_count: int = 0
    max_retries: int = 3
    is_recoverable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Result of error recovery attempt."""
    success: bool
    strategy_used: RecoveryStrategy
    data: Optional[Any] = None
    fallback_used: bool = False
    degraded_mode: bool = False
    warnings: List[str] = field(default_factory=list)
    recovery_time: Optional[float] = None
    error_info: Optional[ErrorInfo] = None


class ErrorClassifier:
    """Classifies errors and determines appropriate recovery strategies."""
    
    def __init__(self):
        """Initialize error classifier."""
        self._classification_rules = self._build_classification_rules()
    
    def classify_error(self, exception: Exception, context: ErrorContext) -> ErrorInfo:
        """
        Classify an error and determine recovery strategy.
        
        Args:
            exception: The exception to classify
            context: Error context information
            
        Returns:
            ErrorInfo with classification and recovery strategy
        """
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Determine category and severity
        category, severity = self._categorize_error(exception, error_message)
        
        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(exception, category, severity)
        
        # Check if error is recoverable
        is_recoverable = self._is_recoverable(exception, category, severity)
        
        # Get retry configuration
        max_retries = self._get_max_retries(category, severity)
        
        return ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            error_category=category,
            severity=severity,
            context=context,
            original_exception=exception,
            stack_trace=traceback.format_exc(),
            recovery_strategy=recovery_strategy,
            is_recoverable=is_recoverable,
            max_retries=max_retries,
            metadata={
                "exception_module": getattr(exception, "__module__", "unknown"),
                "exception_args": getattr(exception, "args", [])
            }
        )
    
    def _build_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build error classification rules."""
        return {
            # Network and API errors
            "ConnectionError": {
                "category": ErrorCategory.NETWORK_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": True,
                "max_retries": 3,
                "strategy": RecoveryStrategy.RETRY
            },
            "TimeoutError": {
                "category": ErrorCategory.TIMEOUT_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": True,
                "max_retries": 2,
                "strategy": RecoveryStrategy.RETRY
            },
            "HTTPError": {
                "category": ErrorCategory.API_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": True,
                "max_retries": 3,
                "strategy": RecoveryStrategy.FALLBACK
            },
            
            # Authentication and authorization
            "AuthenticationError": {
                "category": ErrorCategory.AUTHENTICATION_ERROR,
                "severity": ErrorSeverity.HIGH,
                "recoverable": False,
                "max_retries": 1,
                "strategy": RecoveryStrategy.FAIL_FAST
            },
            "PermissionError": {
                "category": ErrorCategory.AUTHORIZATION_ERROR,
                "severity": ErrorSeverity.HIGH,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.FAIL_FAST
            },
            
            # Resource errors
            "MemoryError": {
                "category": ErrorCategory.RESOURCE_ERROR,
                "severity": ErrorSeverity.CRITICAL,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.ESCALATE
            },
            "DiskSpaceError": {
                "category": ErrorCategory.RESOURCE_ERROR,
                "severity": ErrorSeverity.HIGH,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.ESCALATE
            },
            
            # Validation errors
            "ValidationError": {
                "category": ErrorCategory.VALIDATION_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.FAIL_FAST
            },
            "ValueError": {
                "category": ErrorCategory.VALIDATION_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.FAIL_FAST
            },
            
            # Configuration errors
            "ConfigurationError": {
                "category": ErrorCategory.CONFIGURATION_ERROR,
                "severity": ErrorSeverity.HIGH,
                "recoverable": False,
                "max_retries": 0,
                "strategy": RecoveryStrategy.FAIL_FAST
            },
            
            # Circuit breaker errors
            "CircuitBreakerError": {
                "category": ErrorCategory.API_ERROR,
                "severity": ErrorSeverity.HIGH,
                "recoverable": True,
                "max_retries": 0,
                "strategy": RecoveryStrategy.FALLBACK
            },
            
            # Default for unknown errors
            "Exception": {
                "category": ErrorCategory.UNKNOWN_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "recoverable": True,
                "max_retries": 2,
                "strategy": RecoveryStrategy.RETRY
            }
        }
    
    def _categorize_error(self, exception: Exception, message: str) -> tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error based on exception type and message."""
        error_type = type(exception).__name__
        
        # Check specific error types first
        if error_type in self._classification_rules:
            rule = self._classification_rules[error_type]
            return rule["category"], rule["severity"]
        
        # Check message patterns for additional classification
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM
        
        if any(keyword in message_lower for keyword in ["connection", "network", "dns"]):
            return ErrorCategory.NETWORK_ERROR, ErrorSeverity.MEDIUM
        
        if any(keyword in message_lower for keyword in ["unauthorized", "forbidden", "access denied"]):
            return ErrorCategory.AUTHORIZATION_ERROR, ErrorSeverity.HIGH
        
        if any(keyword in message_lower for keyword in ["invalid", "validation", "format"]):
            return ErrorCategory.VALIDATION_ERROR, ErrorSeverity.MEDIUM
        
        if any(keyword in message_lower for keyword in ["memory", "out of memory", "oom"]):
            return ErrorCategory.RESOURCE_ERROR, ErrorSeverity.CRITICAL
        
        # Default classification
        return ErrorCategory.UNKNOWN_ERROR, ErrorSeverity.MEDIUM
    
    def _determine_recovery_strategy(self, exception: Exception, 
                                   category: ErrorCategory, 
                                   severity: ErrorSeverity) -> RecoveryStrategy:
        """Determine appropriate recovery strategy."""
        error_type = type(exception).__name__
        
        if error_type in self._classification_rules:
            return self._classification_rules[error_type]["strategy"]
        
        # Strategy based on category and severity
        if category == ErrorCategory.NETWORK_ERROR:
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.API_ERROR:
            return RecoveryStrategy.FALLBACK
        elif category == ErrorCategory.TIMEOUT_ERROR:
            return RecoveryStrategy.RETRY
        elif category in [ErrorCategory.AUTHENTICATION_ERROR, ErrorCategory.AUTHORIZATION_ERROR]:
            return RecoveryStrategy.FAIL_FAST
        elif category == ErrorCategory.RESOURCE_ERROR and severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ESCALATE
        elif category == ErrorCategory.VALIDATION_ERROR:
            return RecoveryStrategy.FAIL_FAST
        else:
            return RecoveryStrategy.RETRY
    
    def _is_recoverable(self, exception: Exception, 
                       category: ErrorCategory, 
                       severity: ErrorSeverity) -> bool:
        """Determine if error is recoverable."""
        error_type = type(exception).__name__
        
        if error_type in self._classification_rules:
            return self._classification_rules[error_type]["recoverable"]
        
        # Non-recoverable categories
        non_recoverable = [
            ErrorCategory.AUTHENTICATION_ERROR,
            ErrorCategory.AUTHORIZATION_ERROR,
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.CONFIGURATION_ERROR
        ]
        
        if category in non_recoverable:
            return False
        
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        return True
    
    def _get_max_retries(self, category: ErrorCategory, severity: ErrorSeverity) -> int:
        """Get maximum retry count for error category and severity."""
        if category in [ErrorCategory.AUTHENTICATION_ERROR, ErrorCategory.AUTHORIZATION_ERROR]:
            return 0
        elif category == ErrorCategory.VALIDATION_ERROR:
            return 0
        elif severity == ErrorSeverity.CRITICAL:
            return 0
        elif severity == ErrorSeverity.HIGH:
            return 1
        elif category == ErrorCategory.TIMEOUT_ERROR:
            return 2
        else:
            return 3


class ErrorRecoveryManager:
    """Manages error recovery strategies and execution."""
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.classifier = ErrorClassifier()
        self.metrics_collector = get_metrics_collector()
        self._recovery_handlers = self._build_recovery_handlers()
    
    async def handle_error(self, exception: Exception, 
                          context: ErrorContext,
                          fallback_data: Optional[Any] = None,
                          cache_manager: Optional[Any] = None) -> RecoveryResult:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            exception: The exception to handle
            context: Error context information
            fallback_data: Optional fallback data
            cache_manager: Optional cache manager for fallback
            
        Returns:
            RecoveryResult with recovery outcome
        """
        start_time = time.time()
        
        # Classify the error
        error_info = self.classifier.classify_error(exception, context)
        
        # Log the error
        await self._log_error(error_info)
        
        # Record error metrics
        await self._record_error_metrics(error_info)
        
        # Attempt recovery
        recovery_result = await self._attempt_recovery(
            error_info, fallback_data, cache_manager
        )
        
        # Calculate recovery time
        recovery_result.recovery_time = time.time() - start_time
        recovery_result.error_info = error_info
        
        # Log recovery result
        await self._log_recovery_result(recovery_result)
        
        # Record error event for monitoring
        await self._record_error_event_for_monitoring(error_info, recovery_result, context)
        
        return recovery_result
    
    async def _attempt_recovery(self, error_info: ErrorInfo,
                              fallback_data: Optional[Any] = None,
                              cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Attempt error recovery based on strategy."""
        strategy = error_info.recovery_strategy
        
        if strategy in self._recovery_handlers:
            handler = self._recovery_handlers[strategy]
            return await handler(error_info, fallback_data, cache_manager)
        else:
            # Default to fail fast
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FAIL_FAST,
                warnings=[f"No recovery handler for strategy: {strategy}"]
            )
    
    def _build_recovery_handlers(self) -> Dict[RecoveryStrategy, Callable]:
        """Build recovery strategy handlers."""
        return {
            RecoveryStrategy.RETRY: self._handle_retry_recovery,
            RecoveryStrategy.FALLBACK: self._handle_fallback_recovery,
            RecoveryStrategy.DEGRADE: self._handle_degrade_recovery,
            RecoveryStrategy.FAIL_FAST: self._handle_fail_fast_recovery,
            RecoveryStrategy.CIRCUIT_BREAK: self._handle_circuit_break_recovery,
            RecoveryStrategy.ESCALATE: self._handle_escalate_recovery
        }
    
    async def _handle_retry_recovery(self, error_info: ErrorInfo,
                                   fallback_data: Optional[Any] = None,
                                   cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle retry recovery strategy."""
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RETRY,
            warnings=[
                f"Retry recovery indicated for {error_info.error_type}. "
                f"Caller should implement retry logic with max_retries={error_info.max_retries}"
            ]
        )
    
    async def _handle_fallback_recovery(self, error_info: ErrorInfo,
                                      fallback_data: Optional[Any] = None,
                                      cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle fallback recovery strategy."""
        warnings = []
        
        # Try fallback data first
        if fallback_data is not None:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                data=fallback_data,
                fallback_used=True,
                warnings=["Using provided fallback data"]
            )
        
        # Try cache manager fallback
        if cache_manager and hasattr(cache_manager, 'get_stale_data'):
            try:
                stale_data = await cache_manager.get_stale_data(
                    error_info.context.operation or "unknown"
                )
                if stale_data:
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.FALLBACK,
                        data=stale_data,
                        fallback_used=True,
                        degraded_mode=True,
                        warnings=["Using stale cached data as fallback"]
                    )
            except Exception as e:
                warnings.append(f"Cache fallback failed: {str(e)}")
        
        # Generate minimal fallback data
        minimal_data = self._generate_minimal_fallback_data(error_info)
        if minimal_data:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                data=minimal_data,
                fallback_used=True,
                degraded_mode=True,
                warnings=warnings + ["Using minimal fallback data"]
            )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FALLBACK,
            warnings=warnings + ["No fallback data available"]
        )
    
    async def _handle_degrade_recovery(self, error_info: ErrorInfo,
                                     fallback_data: Optional[Any] = None,
                                     cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle degraded mode recovery strategy."""
        degraded_data = self._generate_degraded_mode_data(error_info)
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.DEGRADE,
            data=degraded_data,
            degraded_mode=True,
            warnings=["Operating in degraded mode with limited functionality"]
        )
    
    async def _handle_fail_fast_recovery(self, error_info: ErrorInfo,
                                       fallback_data: Optional[Any] = None,
                                       cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle fail fast recovery strategy."""
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FAIL_FAST,
            warnings=["Error is not recoverable - failing fast"]
        )
    
    async def _handle_circuit_break_recovery(self, error_info: ErrorInfo,
                                           fallback_data: Optional[Any] = None,
                                           cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle circuit breaker recovery strategy."""
        # Circuit breaker should be handled at the service level
        # This is a fallback for when circuit breaker is already open
        return await self._handle_fallback_recovery(error_info, fallback_data, cache_manager)
    
    async def _handle_escalate_recovery(self, error_info: ErrorInfo,
                                      fallback_data: Optional[Any] = None,
                                      cache_manager: Optional[Any] = None) -> RecoveryResult:
        """Handle escalation recovery strategy."""
        # Log critical error for escalation
        logger.critical(
            f"Critical error requiring escalation: {error_info.error_type}",
            extra={
                'category': LogCategory.SYSTEM,
                'data': {
                    'error_id': error_info.context.error_id,
                    'error_type': error_info.error_type,
                    'error_message': error_info.error_message,
                    'severity': error_info.severity.value,
                    'context': error_info.context.additional_context
                }
            }
        )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ESCALATE,
            warnings=["Critical error escalated to system administrators"]
        )
    
    def _generate_minimal_fallback_data(self, error_info: ErrorInfo) -> Optional[Dict[str, Any]]:
        """Generate minimal fallback data based on error context."""
        operation = error_info.context.operation
        
        if not operation:
            return None
        
        operation_lower = operation.lower()
        
        if "pricing" in operation_lower:
            return {
                "services": [],
                "fallback_mode": True,
                "message": "Pricing data temporarily unavailable",
                "error_id": error_info.context.error_id
            }
        elif "compute" in operation_lower or "instance" in operation_lower:
            return {
                "instances": [],
                "fallback_mode": True,
                "message": "Compute instance data temporarily unavailable",
                "error_id": error_info.context.error_id
            }
        elif "recommendation" in operation_lower:
            return {
                "recommendations": [],
                "fallback_mode": True,
                "message": "Recommendations temporarily unavailable",
                "error_id": error_info.context.error_id
            }
        else:
            return {
                "data": None,
                "fallback_mode": True,
                "message": f"Service temporarily unavailable: {operation}",
                "error_id": error_info.context.error_id
            }
    
    def _generate_degraded_mode_data(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """Generate degraded mode data."""
        return {
            "degraded_mode": True,
            "message": f"Operating in degraded mode due to {error_info.error_category.value}",
            "error_id": error_info.context.error_id,
            "limitations": [
                "Some features may be unavailable",
                "Data may be incomplete or stale",
                "Performance may be reduced"
            ]
        }
    
    async def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information."""
        log_level = self._get_log_level_for_severity(error_info.severity)
        
        with log_context(
            correlation_id=error_info.context.correlation_id,
            workflow_id=error_info.context.workflow_id,
            agent_name=error_info.context.agent_name,
            step_id=error_info.context.step_id
        ):
            logger.log(
                log_level,
                f"Error occurred: {error_info.error_type} - {error_info.error_message}",
                extra={
                    'category': LogCategory.SYSTEM,
                    'data': {
                        'error_id': error_info.context.error_id,
                        'error_type': error_info.error_type,
                        'error_category': error_info.error_category.value,
                        'severity': error_info.severity.value,
                        'recovery_strategy': error_info.recovery_strategy.value if error_info.recovery_strategy else None,
                        'is_recoverable': error_info.is_recoverable,
                        'max_retries': error_info.max_retries,
                        'context': error_info.context.additional_context,
                        'stack_trace': error_info.stack_trace
                    }
                }
            )
    
    async def _log_recovery_result(self, recovery_result: RecoveryResult) -> None:
        """Log recovery result."""
        if recovery_result.success:
            logger.info(
                f"Error recovery successful using {recovery_result.strategy_used.value}",
                extra={
                    'category': LogCategory.SYSTEM,
                    'data': {
                        'strategy_used': recovery_result.strategy_used.value,
                        'fallback_used': recovery_result.fallback_used,
                        'degraded_mode': recovery_result.degraded_mode,
                        'warnings': recovery_result.warnings,
                        'recovery_time': recovery_result.recovery_time
                    }
                }
            )
        else:
            logger.error(
                f"Error recovery failed with {recovery_result.strategy_used.value}",
                extra={
                    'category': LogCategory.SYSTEM,
                    'data': {
                        'strategy_used': recovery_result.strategy_used.value,
                        'warnings': recovery_result.warnings,
                        'recovery_time': recovery_result.recovery_time
                    }
                }
            )
    
    async def _record_error_metrics(self, error_info: ErrorInfo) -> None:
        """Record error metrics."""
        try:
            await self.metrics_collector.record_error(
                error_type=error_info.error_type,
                error_category=error_info.error_category.value,
                severity=error_info.severity.value,
                component=error_info.context.component or "unknown",
                agent_name=error_info.context.agent_name,
                workflow_id=error_info.context.workflow_id,
                is_recoverable=error_info.is_recoverable
            )
        except Exception as e:
            logger.warning(f"Failed to record error metrics: {str(e)}")
    
    def _get_log_level_for_severity(self, severity: ErrorSeverity) -> int:
        """Get logging level for error severity."""
        severity_mapping = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_mapping.get(severity, logging.WARNING)
    
    async def _record_error_event_for_monitoring(self, error_info: ErrorInfo, 
                                               recovery_result: RecoveryResult,
                                               context: ErrorContext) -> None:
        """Record error event for monitoring system."""
        try:
            # Import here to avoid circular imports
            from .error_monitoring import error_monitor
            
            # Extract service name from context
            service_name = context.additional_context.get("service_name")
            
            # Record the error event
            await error_monitor.record_error_event(
                error_info=error_info,
                recovery_result=recovery_result,
                service_name=service_name
            )
            
        except Exception as e:
            logger.warning(f"Failed to record error event for monitoring: {str(e)}")


class ComprehensiveErrorHandler:
    """
    Comprehensive error handler that integrates all error handling components.
    
    This is the main interface for error handling in the system.
    """
    
    def __init__(self):
        """Initialize comprehensive error handler."""
        self.recovery_manager = ErrorRecoveryManager()
        self.resilience_manager = resilience_manager
    
    @asynccontextmanager
    async def handle_errors(self, 
                           operation: str,
                           component: str,
                           agent_name: Optional[str] = None,
                           workflow_id: Optional[str] = None,
                           fallback_data: Optional[Any] = None,
                           cache_manager: Optional[Any] = None,
                           **context_kwargs):
        """
        Context manager for comprehensive error handling.
        
        Args:
            operation: Name of the operation being performed
            component: Component performing the operation
            agent_name: Optional agent name
            workflow_id: Optional workflow ID
            fallback_data: Optional fallback data
            cache_manager: Optional cache manager
            **context_kwargs: Additional context information
            
        Yields:
            Callable for executing operations with error handling
        """
        error_context = ErrorContext(
            operation=operation,
            component=component,
            agent_name=agent_name,
            workflow_id=workflow_id,
            additional_context=context_kwargs
        )
        
        async def execute_with_error_handling(func: Callable, *args, **kwargs) -> Any:
            """Execute function with comprehensive error handling."""
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Handle the error
                recovery_result = await self.recovery_manager.handle_error(
                    e, error_context, fallback_data, cache_manager
                )
                
                if recovery_result.success:
                    return recovery_result.data
                else:
                    # Re-raise the original exception with additional context
                    raise type(e)(
                        f"{str(e)} (Error ID: {error_context.error_id}, "
                        f"Recovery: {recovery_result.strategy_used.value})"
                    ) from e
        
        yield execute_with_error_handling
    
    async def handle_agent_error(self, 
                                agent_name: str,
                                operation: str,
                                exception: Exception,
                                workflow_id: Optional[str] = None,
                                fallback_data: Optional[Any] = None) -> RecoveryResult:
        """
        Handle agent-specific errors.
        
        Args:
            agent_name: Name of the agent
            operation: Operation that failed
            exception: The exception that occurred
            workflow_id: Optional workflow ID
            fallback_data: Optional fallback data
            
        Returns:
            RecoveryResult with recovery outcome
        """
        error_context = ErrorContext(
            operation=operation,
            component="agent",
            agent_name=agent_name,
            workflow_id=workflow_id
        )
        
        return await self.recovery_manager.handle_error(
            exception, error_context, fallback_data
        )
    
    async def handle_api_error(self,
                              service_name: str,
                              operation: str,
                              exception: Exception,
                              fallback_data: Optional[Any] = None,
                              cache_manager: Optional[Any] = None) -> RecoveryResult:
        """
        Handle API-specific errors with resilience patterns.
        
        Args:
            service_name: Name of the service
            operation: Operation that failed
            exception: The exception that occurred
            fallback_data: Optional fallback data
            cache_manager: Optional cache manager
            
        Returns:
            RecoveryResult with recovery outcome
        """
        error_context = ErrorContext(
            operation=operation,
            component="api",
            additional_context={"service_name": service_name}
        )
        
        return await self.recovery_manager.handle_error(
            exception, error_context, fallback_data, cache_manager
        )
    
    async def handle_workflow_error(self,
                                   workflow_id: str,
                                   step_id: str,
                                   operation: str,
                                   exception: Exception,
                                   agent_name: Optional[str] = None) -> RecoveryResult:
        """
        Handle workflow-specific errors.
        
        Args:
            workflow_id: Workflow ID
            step_id: Step ID where error occurred
            operation: Operation that failed
            exception: The exception that occurred
            agent_name: Optional agent name
            
        Returns:
            RecoveryResult with recovery outcome
        """
        error_context = ErrorContext(
            operation=operation,
            component="workflow",
            workflow_id=workflow_id,
            step_id=step_id,
            agent_name=agent_name
        )
        
        return await self.recovery_manager.handle_error(exception, error_context)
    
    def configure_service_error_handling(self,
                                       service_name: str,
                                       failure_threshold: int = 5,
                                       recovery_timeout: int = 60,
                                       max_retries: int = 3,
                                       base_delay: float = 1.0,
                                       max_delay: float = 60.0) -> None:
        """
        Configure error handling for a specific service.
        
        Args:
            service_name: Service name
            failure_threshold: Circuit breaker failure threshold
            recovery_timeout: Circuit breaker recovery timeout
            max_retries: Maximum retry attempts
            base_delay: Base retry delay
            max_delay: Maximum retry delay
        """
        # Configure resilience patterns
        circuit_config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        
        retry_config = RetryConfig(
            max_attempts=max_retries,
            base_delay=base_delay,
            max_delay=max_delay
        )
        
        self.resilience_manager.register_service(
            service_name, circuit_config, retry_config
        )
        
        logger.info(f"Configured error handling for service: {service_name}")
    
    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        try:
            # Get circuit breaker health
            service_health = self.resilience_manager.get_all_services_health()
            
            # Get error metrics from metrics collector
            error_metrics = await self.recovery_manager.metrics_collector.get_error_metrics()
            
            return {
                "service_health": service_health,
                "error_metrics": error_metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get error statistics: {str(e)}")
            return {
                "error": "Failed to retrieve error statistics",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global error handler instance
error_handler = ComprehensiveErrorHandler()


def configure_default_error_handling():
    """Configure default error handling for common services."""
    # Configure cloud services
    services = [
        "aws_pricing", "aws_ec2", "aws_rds", "aws_ai",
        "azure_pricing", "azure_compute", "azure_sql",
        "gcp_billing", "gcp_compute", "gcp_sql"
    ]
    
    for service in services:
        error_handler.configure_service_error_handling(service)
    
    logger.info("Configured default error handling for cloud services")


# Initialize default error handling
configure_default_error_handling()