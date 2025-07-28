"""
Comprehensive tests for the error handling system.

Tests retry mechanisms, graceful degradation, fallback mechanisms,
and error logging and monitoring.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.core.error_handling import (
    ComprehensiveErrorHandler, ErrorClassifier, ErrorRecoveryManager,
    ErrorContext, ErrorInfo, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    RecoveryResult, error_handler
)
from src.infra_mind.core.error_monitoring import (
    ErrorMonitor, AlertManager, AlertRule, MonitoringMetric, AlertLevel,
    error_monitor
)
from src.infra_mind.core.resilience import (
    CircuitBreakerError, RetryExhaustedError, FallbackError
)


class TestErrorClassifier:
    """Test error classification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ErrorClassifier()
        self.context = ErrorContext(
            operation="test_operation",
            component="test_component"
        )
    
    def test_classify_network_error(self):
        """Test classification of network errors."""
        exception = ConnectionError("Connection failed")
        error_info = self.classifier.classify_error(exception, self.context)
        
        assert error_info.error_category == ErrorCategory.NETWORK_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recovery_strategy == RecoveryStrategy.RETRY
        assert error_info.is_recoverable is True
        assert error_info.max_retries == 3
    
    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        exception = TimeoutError("Operation timed out")
        error_info = self.classifier.classify_error(exception, self.context)
        
        assert error_info.error_category == ErrorCategory.TIMEOUT_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recovery_strategy == RecoveryStrategy.RETRY
        assert error_info.is_recoverable is True
        assert error_info.max_retries == 2
    
    def test_classify_validation_error(self):
        """Test classification of validation errors."""
        exception = ValueError("Invalid input")
        error_info = self.classifier.classify_error(exception, self.context)
        
        assert error_info.error_category == ErrorCategory.VALIDATION_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recovery_strategy == RecoveryStrategy.FAIL_FAST
        assert error_info.is_recoverable is False
        assert error_info.max_retries == 0
    
    def test_classify_circuit_breaker_error(self):
        """Test classification of circuit breaker errors."""
        exception = CircuitBreakerError("Circuit breaker is open")
        error_info = self.classifier.classify_error(exception, self.context)
        
        assert error_info.error_category == ErrorCategory.API_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.recovery_strategy == RecoveryStrategy.FALLBACK
        assert error_info.is_recoverable is True
        assert error_info.max_retries == 0
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        exception = RuntimeError("Unknown error")
        error_info = self.classifier.classify_error(exception, self.context)
        
        assert error_info.error_category == ErrorCategory.UNKNOWN_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recovery_strategy == RecoveryStrategy.RETRY
        assert error_info.is_recoverable is True
        assert error_info.max_retries == 2


class TestErrorRecoveryManager:
    """Test error recovery functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recovery_manager = ErrorRecoveryManager()
        self.context = ErrorContext(
            operation="test_operation",
            component="test_component"
        )
    
    @pytest.mark.asyncio
    async def test_handle_retry_recovery(self):
        """Test retry recovery strategy."""
        exception = ConnectionError("Connection failed")
        error_info = self.recovery_manager.classifier.classify_error(exception, self.context)
        
        with patch.object(self.recovery_manager, '_log_error'), \
             patch.object(self.recovery_manager, '_record_error_metrics'), \
             patch.object(self.recovery_manager, '_log_recovery_result'), \
             patch.object(self.recovery_manager, '_record_error_event_for_monitoring'):
            
            recovery_result = await self.recovery_manager.handle_error(exception, self.context)
            
            assert recovery_result.success is False
            assert recovery_result.strategy_used == RecoveryStrategy.RETRY
            assert "Retry recovery indicated" in recovery_result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_handle_fallback_recovery_with_data(self):
        """Test fallback recovery with provided data."""
        # Use an exception that triggers fallback strategy
        from src.infra_mind.core.resilience import CircuitBreakerError
        exception = CircuitBreakerError("Circuit breaker is open")
        fallback_data = {"fallback": True, "data": "test"}
        
        with patch.object(self.recovery_manager, '_log_error'), \
             patch.object(self.recovery_manager, '_record_error_metrics'), \
             patch.object(self.recovery_manager, '_log_recovery_result'), \
             patch.object(self.recovery_manager, '_record_error_event_for_monitoring'):
            
            recovery_result = await self.recovery_manager.handle_error(
                exception, self.context, fallback_data
            )
            
            assert recovery_result.success is True
            assert recovery_result.strategy_used == RecoveryStrategy.FALLBACK
            assert recovery_result.data == fallback_data
            assert recovery_result.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_handle_fail_fast_recovery(self):
        """Test fail fast recovery strategy."""
        exception = ValueError("Invalid input")
        
        with patch.object(self.recovery_manager, '_log_error'), \
             patch.object(self.recovery_manager, '_record_error_metrics'), \
             patch.object(self.recovery_manager, '_log_recovery_result'), \
             patch.object(self.recovery_manager, '_record_error_event_for_monitoring'):
            
            recovery_result = await self.recovery_manager.handle_error(exception, self.context)
            
            assert recovery_result.success is False
            assert recovery_result.strategy_used == RecoveryStrategy.FAIL_FAST
            assert "not recoverable" in recovery_result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_generate_minimal_fallback_data(self):
        """Test minimal fallback data generation."""
        self.context.operation = "pricing_lookup"
        fallback_data = self.recovery_manager._generate_minimal_fallback_data(
            ErrorInfo(
                error_type="TestError",
                error_message="Test error",
                error_category=ErrorCategory.API_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context=self.context
            )
        )
        
        assert fallback_data is not None
        assert fallback_data["fallback_mode"] is True
        assert "pricing" in fallback_data["message"].lower()
        assert "services" in fallback_data


class TestComprehensiveErrorHandler:
    """Test comprehensive error handler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ComprehensiveErrorHandler()
    
    @pytest.mark.asyncio
    async def test_handle_errors_context_manager_success(self):
        """Test error handling context manager with successful operation."""
        async def successful_operation():
            return {"result": "success"}
        
        async with self.error_handler.handle_errors(
            operation="test_operation",
            component="test_component"
        ) as handle_error:
            result = await handle_error(successful_operation)
            assert result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_handle_errors_context_manager_with_error(self):
        """Test error handling context manager with error."""
        async def failing_operation():
            raise ConnectionError("Connection failed")
        
        with patch.object(self.error_handler.recovery_manager, 'handle_error') as mock_handle:
            mock_handle.return_value = RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                data={"fallback": True}
            )
            
            async with self.error_handler.handle_errors(
                operation="test_operation",
                component="test_component"
            ) as handle_error:
                result = await handle_error(failing_operation)
                assert result == {"fallback": True}
    
    @pytest.mark.asyncio
    async def test_handle_agent_error(self):
        """Test agent-specific error handling."""
        exception = Exception("Agent failed")
        
        with patch.object(self.error_handler.recovery_manager, 'handle_error') as mock_handle:
            mock_handle.return_value = RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY
            )
            
            result = await self.error_handler.handle_agent_error(
                agent_name="test_agent",
                operation="test_operation",
                exception=exception
            )
            
            assert result.success is False
            assert result.strategy_used == RecoveryStrategy.RETRY
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_api_error(self):
        """Test API-specific error handling."""
        exception = ConnectionError("API connection failed")
        
        with patch.object(self.error_handler.recovery_manager, 'handle_error') as mock_handle:
            mock_handle.return_value = RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                data={"cached": True}
            )
            
            result = await self.error_handler.handle_api_error(
                service_name="test_service",
                operation="api_call",
                exception=exception
            )
            
            assert result.success is True
            assert result.data == {"cached": True}
    
    def test_configure_service_error_handling(self):
        """Test service error handling configuration."""
        service_name = "test_service"
        
        self.error_handler.configure_service_error_handling(
            service_name=service_name,
            failure_threshold=3,
            max_retries=2
        )
        
        # Verify service was registered with resilience manager
        assert service_name in self.error_handler.resilience_manager.circuit_breakers
    
    @pytest.mark.asyncio
    async def test_get_error_statistics(self):
        """Test error statistics retrieval."""
        with patch.object(self.error_handler.resilience_manager, 'get_all_services_health') as mock_health, \
             patch.object(self.error_handler.recovery_manager.metrics_collector, 'get_error_metrics') as mock_metrics:
            
            mock_health.return_value = {"test_service": {"state": "closed"}}
            mock_metrics.return_value = {"total_errors": 5}
            
            stats = await self.error_handler.get_error_statistics()
            
            assert "service_health" in stats
            assert "error_metrics" in stats
            assert "timestamp" in stats


class TestErrorMonitoring:
    """Test error monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_monitor = ErrorMonitor(time_window_minutes=5)
        self.alert_manager = AlertManager()
    
    @pytest.mark.asyncio
    async def test_record_error_event(self):
        """Test recording error events."""
        error_info = ErrorInfo(
            error_type="TestError",
            error_message="Test error message",
            error_category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=ErrorContext(operation="test_op", component="test_component")
        )
        
        recovery_result = RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.FALLBACK
        )
        
        await self.error_monitor.record_error_event(
            error_info=error_info,
            recovery_result=recovery_result,
            service_name="test_service"
        )
        
        # Verify event was recorded
        events = self.error_monitor.metrics_calculator._get_events_in_window()
        assert len(events) == 1
        assert events[0].error_info.error_type == "TestError"
        assert events[0].service_name == "test_service"
    
    def test_alert_rule_creation(self):
        """Test alert rule creation and management."""
        rule = AlertRule(
            name="test_rule",
            metric=MonitoringMetric.ERROR_RATE,
            threshold=5.0,
            alert_level=AlertLevel.WARNING
        )
        
        self.alert_manager.add_rule(rule)
        
        assert "test_rule" in self.alert_manager.rules
        assert self.alert_manager.rules["test_rule"].threshold == 5.0
    
    def test_metrics_calculation(self):
        """Test error metrics calculation."""
        calculator = self.error_monitor.metrics_calculator
        
        # Add some test events
        error_info = ErrorInfo(
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=ErrorContext(operation="test_op", component="test_component")
        )
        
        from src.infra_mind.core.error_monitoring import ErrorEvent
        
        event1 = ErrorEvent(
            timestamp=datetime.now(timezone.utc),
            error_info=error_info,
            service_name="test_service"
        )
        
        event2 = ErrorEvent(
            timestamp=datetime.now(timezone.utc),
            error_info=error_info,
            service_name="test_service",
            recovery_result=RecoveryResult(success=True, strategy_used=RecoveryStrategy.RETRY)
        )
        
        calculator.add_event(event1)
        calculator.add_event(event2)
        
        # Test calculations
        error_count = calculator.calculate_error_count("test_service")
        assert error_count == 2
        
        error_rate = calculator.calculate_error_rate("test_service")
        assert error_rate == 2.0 / 5.0  # 2 errors in 5 minute window
        
        recovery_rate = calculator.calculate_recovery_rate("test_service")
        assert recovery_rate == 1.0  # 1 successful recovery out of 1 recovery attempt
    
    @pytest.mark.asyncio
    async def test_monitoring_start_stop(self):
        """Test starting and stopping monitoring."""
        assert not self.error_monitor.running
        
        # Start monitoring
        await self.error_monitor.start_monitoring(check_interval_seconds=0.1)
        assert self.error_monitor.running
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await self.error_monitor.stop_monitoring()
        assert not self.error_monitor.running
    
    def test_get_monitoring_status(self):
        """Test monitoring status retrieval."""
        status = self.error_monitor.get_monitoring_status()
        
        assert "running" in status
        assert "time_window_minutes" in status
        assert "active_alerts" in status
        assert "metrics" in status
        assert status["time_window_minutes"] == 5
    
    def test_get_service_health(self):
        """Test service health status retrieval."""
        health = self.error_monitor.get_service_health("test_service")
        
        assert "service_name" in health
        assert "error_rate" in health
        assert "error_count" in health
        assert "recovery_rate" in health
        assert "availability" in health
        assert health["service_name"] == "test_service"


class TestIntegration:
    """Integration tests for the complete error handling system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_handling(self):
        """Test complete error handling flow."""
        # Simulate an API error
        exception = ConnectionError("API connection failed")
        
        # Create error context
        context = ErrorContext(
            operation="api_call",
            component="api_client",
            additional_context={"service_name": "test_api"}
        )
        
        # Handle the error
        with patch.object(error_monitor, 'record_error_event') as mock_record:
            recovery_result = await error_handler.recovery_manager.handle_error(
                exception, context, fallback_data={"cached": True}
            )
            
            # Verify recovery was successful with fallback
            assert recovery_result.success is True
            assert recovery_result.strategy_used == RecoveryStrategy.FALLBACK
            assert recovery_result.data == {"cached": True}
            assert recovery_result.fallback_used is True
            
            # Verify monitoring was notified
            mock_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_error_handling_integration(self):
        """Test agent error handling integration."""
        # This would test the integration with the base agent class
        # For now, we'll test the error handler directly
        
        exception = TimeoutError("Agent execution timeout")
        
        with patch.object(error_handler.recovery_manager, 'handle_error') as mock_handle:
            mock_handle.return_value = RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                data={"recommendations": [], "fallback_mode": True}
            )
            
            result = await error_handler.handle_agent_error(
                agent_name="test_agent",
                operation="agent_execution",
                exception=exception,
                workflow_id="test_workflow"
            )
            
            assert result.success is True
            assert result.data["fallback_mode"] is True
    
    @pytest.mark.asyncio
    async def test_monitoring_alert_generation(self):
        """Test monitoring and alert generation."""
        # Add multiple error events to trigger alert
        error_info = ErrorInfo(
            error_type="TestError",
            error_message="Test error",
            error_category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=ErrorContext(operation="test_op", component="test_component")
        )
        
        from src.infra_mind.core.error_monitoring import ErrorEvent
        
        # Add enough events to trigger high error rate alert
        for i in range(10):
            event = ErrorEvent(
                timestamp=datetime.now(timezone.utc),
                error_info=error_info,
                service_name="test_service"
            )
            error_monitor.metrics_calculator.add_event(event)
        
        # Check alert rules
        recent_events = error_monitor.metrics_calculator._get_events_in_window()
        alerts = await error_monitor.alert_manager.check_rules(
            error_monitor.metrics_calculator, recent_events
        )
        
        # Should have generated alerts for high error rate
        assert len(alerts) > 0
        assert any(alert.rule_name == "high_error_rate" for alert in alerts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])