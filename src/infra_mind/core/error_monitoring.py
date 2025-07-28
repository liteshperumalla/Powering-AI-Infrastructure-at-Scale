"""
Comprehensive Error Monitoring System.

Provides real-time error monitoring, alerting, and analytics
for the Infra Mind platform.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import statistics

from .error_handling import ErrorInfo, ErrorSeverity, ErrorCategory, RecoveryResult
from .advanced_logging import get_performance_logger, log_context, LogCategory
from .metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringMetric(str, Enum):
    """Monitoring metrics."""
    ERROR_RATE = "error_rate"
    ERROR_COUNT = "error_count"
    RECOVERY_RATE = "recovery_rate"
    MEAN_TIME_TO_RECOVERY = "mean_time_to_recovery"
    SERVICE_AVAILABILITY = "service_availability"
    CIRCUIT_BREAKER_TRIPS = "circuit_breaker_trips"


@dataclass
class ErrorEvent:
    """Error event for monitoring."""
    timestamp: datetime
    error_info: ErrorInfo
    recovery_result: Optional[RecoveryResult] = None
    service_name: Optional[str] = None
    component: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_id": self.error_info.context.error_id,
            "error_type": self.error_info.error_type,
            "error_category": self.error_info.error_category.value,
            "severity": self.error_info.severity.value,
            "component": self.component,
            "service_name": self.service_name,
            "recovery_success": self.recovery_result.success if self.recovery_result else None,
            "recovery_strategy": self.recovery_result.strategy_used.value if self.recovery_result else None,
            "degraded_mode": self.recovery_result.degraded_mode if self.recovery_result else False
        }


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric: MonitoringMetric
    threshold: float
    time_window_minutes: int = 5
    alert_level: AlertLevel = AlertLevel.WARNING
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    cooldown_minutes: int = 15
    
    def matches_conditions(self, event: ErrorEvent) -> bool:
        """Check if event matches rule conditions."""
        if not self.enabled:
            return False
        
        for key, value in self.conditions.items():
            if key == "error_category" and event.error_info.error_category.value != value:
                return False
            elif key == "severity" and event.error_info.severity.value != value:
                return False
            elif key == "component" and event.component != value:
                return False
            elif key == "service_name" and event.service_name != value:
                return False
        
        return True


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float
    events: List[ErrorEvent] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "rule_name": self.rule_name,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "event_count": len(self.events),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved
        }


class ErrorMetricsCalculator:
    """Calculates error metrics for monitoring."""
    
    def __init__(self, time_window_minutes: int = 5):
        """
        Initialize metrics calculator.
        
        Args:
            time_window_minutes: Time window for calculations
        """
        self.time_window_minutes = time_window_minutes
        self.events: deque = deque()
        self.service_events: Dict[str, deque] = defaultdict(lambda: deque())
    
    def add_event(self, event: ErrorEvent) -> None:
        """Add error event for metrics calculation."""
        self.events.append(event)
        
        if event.service_name:
            self.service_events[event.service_name].append(event)
        
        # Clean old events
        self._cleanup_old_events()
    
    def calculate_error_rate(self, service_name: Optional[str] = None) -> float:
        """Calculate error rate (errors per minute)."""
        events = self._get_events_in_window(service_name)
        if not events:
            return 0.0
        
        return len(events) / self.time_window_minutes
    
    def calculate_error_count(self, service_name: Optional[str] = None) -> int:
        """Calculate total error count in time window."""
        events = self._get_events_in_window(service_name)
        return len(events)
    
    def calculate_recovery_rate(self, service_name: Optional[str] = None) -> float:
        """Calculate recovery success rate."""
        events = self._get_events_in_window(service_name)
        if not events:
            return 1.0
        
        recovery_events = [e for e in events if e.recovery_result]
        if not recovery_events:
            return 0.0
        
        successful_recoveries = [e for e in recovery_events if e.recovery_result.success]
        return len(successful_recoveries) / len(recovery_events)
    
    def calculate_mean_time_to_recovery(self, service_name: Optional[str] = None) -> float:
        """Calculate mean time to recovery in seconds."""
        events = self._get_events_in_window(service_name)
        recovery_times = []
        
        for event in events:
            if event.recovery_result and event.recovery_result.recovery_time:
                recovery_times.append(event.recovery_result.recovery_time)
        
        if not recovery_times:
            return 0.0
        
        return statistics.mean(recovery_times)
    
    def calculate_service_availability(self, service_name: str) -> float:
        """Calculate service availability percentage."""
        events = self._get_events_in_window(service_name)
        if not events:
            return 100.0
        
        # Simple availability calculation based on error frequency
        # In a real system, this would be based on uptime/downtime
        error_rate = self.calculate_error_rate(service_name)
        max_acceptable_rate = 10.0  # errors per minute
        
        availability = max(0.0, (max_acceptable_rate - error_rate) / max_acceptable_rate * 100)
        return min(100.0, availability)
    
    def calculate_circuit_breaker_trips(self, service_name: Optional[str] = None) -> int:
        """Calculate circuit breaker trip count."""
        events = self._get_events_in_window(service_name)
        return len([e for e in events if "CircuitBreakerError" in e.error_info.error_type])
    
    def _get_events_in_window(self, service_name: Optional[str] = None) -> List[ErrorEvent]:
        """Get events within the time window."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.time_window_minutes)
        
        if service_name:
            events = self.service_events.get(service_name, deque())
        else:
            events = self.events
        
        return [e for e in events if e.timestamp >= cutoff_time]
    
    def _cleanup_old_events(self) -> None:
        """Remove events older than time window."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.time_window_minutes * 2)
        
        # Clean main events
        while self.events and self.events[0].timestamp < cutoff_time:
            self.events.popleft()
        
        # Clean service events
        for service_name, events in self.service_events.items():
            while events and events[0].timestamp < cutoff_time:
                events.popleft()


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.last_alert_times: Dict[str, datetime] = {}
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule."""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove alert rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler."""
        self.alert_handlers.append(handler)
    
    async def check_rules(self, metrics_calculator: ErrorMetricsCalculator, 
                         recent_events: List[ErrorEvent]) -> List[Alert]:
        """Check alert rules and generate alerts."""
        new_alerts = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule.name):
                continue
            
            # Calculate metric value
            metric_value = await self._calculate_metric_value(rule, metrics_calculator)
            
            # Check threshold
            if metric_value >= rule.threshold:
                # Find matching events
                matching_events = [e for e in recent_events if rule.matches_conditions(e)]
                
                if matching_events or rule.metric in [MonitoringMetric.ERROR_RATE, MonitoringMetric.SERVICE_AVAILABILITY]:
                    alert = await self._create_alert(rule, metric_value, matching_events)
                    new_alerts.append(alert)
                    self.active_alerts[alert.alert_id] = alert
                    self.alert_history.append(alert)
                    self.last_alert_times[rule.name] = datetime.now(timezone.utc)
                    
                    # Notify handlers
                    await self._notify_handlers(alert)
        
        return new_alerts
    
    async def _calculate_metric_value(self, rule: AlertRule, 
                                    metrics_calculator: ErrorMetricsCalculator) -> float:
        """Calculate metric value for rule."""
        service_name = rule.conditions.get("service_name")
        
        if rule.metric == MonitoringMetric.ERROR_RATE:
            return metrics_calculator.calculate_error_rate(service_name)
        elif rule.metric == MonitoringMetric.ERROR_COUNT:
            return float(metrics_calculator.calculate_error_count(service_name))
        elif rule.metric == MonitoringMetric.RECOVERY_RATE:
            return 1.0 - metrics_calculator.calculate_recovery_rate(service_name)  # Invert for threshold
        elif rule.metric == MonitoringMetric.MEAN_TIME_TO_RECOVERY:
            return metrics_calculator.calculate_mean_time_to_recovery(service_name)
        elif rule.metric == MonitoringMetric.SERVICE_AVAILABILITY:
            return 100.0 - metrics_calculator.calculate_service_availability(service_name)  # Invert for threshold
        elif rule.metric == MonitoringMetric.CIRCUIT_BREAKER_TRIPS:
            return float(metrics_calculator.calculate_circuit_breaker_trips(service_name))
        else:
            return 0.0
    
    async def _create_alert(self, rule: AlertRule, metric_value: float, 
                          events: List[ErrorEvent]) -> Alert:
        """Create alert from rule and events."""
        alert_id = f"{rule.name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        message = f"Alert: {rule.name} - {rule.metric.value} ({metric_value:.2f}) exceeded threshold ({rule.threshold})"
        
        return Alert(
            alert_id=alert_id,
            rule_name=rule.name,
            level=rule.alert_level,
            message=message,
            timestamp=datetime.now(timezone.utc),
            metric_value=metric_value,
            threshold=rule.threshold,
            events=events
        )
    
    async def _notify_handlers(self, alert: Alert) -> None:
        """Notify alert handlers."""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {str(e)}")
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period."""
        if rule_name not in self.last_alert_times:
            return False
        
        rule = self.rules[rule_name]
        last_alert_time = self.last_alert_times[rule_name]
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now(timezone.utc) - last_alert_time < cooldown_period
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return self.alert_history[-limit:]


class ErrorMonitor:
    """Main error monitoring system."""
    
    def __init__(self, time_window_minutes: int = 5):
        """
        Initialize error monitor.
        
        Args:
            time_window_minutes: Time window for metrics calculation
        """
        self.metrics_calculator = ErrorMetricsCalculator(time_window_minutes)
        self.alert_manager = AlertManager()
        self.performance_logger = get_performance_logger()
        self.metrics_collector = get_metrics_collector()
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        # Setup default alert handlers
        self._setup_default_alert_handlers()
    
    def _setup_default_alert_rules(self) -> None:
        """Setup default alert rules."""
        # High error rate
        self.alert_manager.add_rule(AlertRule(
            name="high_error_rate",
            metric=MonitoringMetric.ERROR_RATE,
            threshold=5.0,  # 5 errors per minute
            time_window_minutes=5,
            alert_level=AlertLevel.WARNING
        ))
        
        # Critical error rate
        self.alert_manager.add_rule(AlertRule(
            name="critical_error_rate",
            metric=MonitoringMetric.ERROR_RATE,
            threshold=10.0,  # 10 errors per minute
            time_window_minutes=5,
            alert_level=AlertLevel.CRITICAL
        ))
        
        # Low recovery rate
        self.alert_manager.add_rule(AlertRule(
            name="low_recovery_rate",
            metric=MonitoringMetric.RECOVERY_RATE,
            threshold=0.5,  # Less than 50% recovery rate
            time_window_minutes=10,
            alert_level=AlertLevel.ERROR
        ))
        
        # High mean time to recovery
        self.alert_manager.add_rule(AlertRule(
            name="high_recovery_time",
            metric=MonitoringMetric.MEAN_TIME_TO_RECOVERY,
            threshold=30.0,  # 30 seconds
            time_window_minutes=10,
            alert_level=AlertLevel.WARNING
        ))
        
        # Low service availability
        self.alert_manager.add_rule(AlertRule(
            name="low_service_availability",
            metric=MonitoringMetric.SERVICE_AVAILABILITY,
            threshold=5.0,  # Less than 95% availability
            time_window_minutes=15,
            alert_level=AlertLevel.ERROR
        ))
        
        # Circuit breaker trips
        self.alert_manager.add_rule(AlertRule(
            name="circuit_breaker_trips",
            metric=MonitoringMetric.CIRCUIT_BREAKER_TRIPS,
            threshold=3.0,  # 3 trips in time window
            time_window_minutes=10,
            alert_level=AlertLevel.WARNING
        ))
    
    def _setup_default_alert_handlers(self) -> None:
        """Setup default alert handlers."""
        self.alert_manager.add_alert_handler(self._log_alert)
        self.alert_manager.add_alert_handler(self._record_alert_metric)
    
    async def _log_alert(self, alert: Alert) -> None:
        """Log alert to system logs."""
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(alert.level, logging.WARNING)
        
        logger.log(
            log_level,
            f"ALERT: {alert.message}",
            extra={
                'category': LogCategory.SYSTEM,
                'data': alert.to_dict()
            }
        )
    
    async def _record_alert_metric(self, alert: Alert) -> None:
        """Record alert as metric."""
        try:
            await self.metrics_collector.record_alert(
                alert_id=alert.alert_id,
                rule_name=alert.rule_name,
                level=alert.level.value,
                metric_value=alert.metric_value,
                threshold=alert.threshold
            )
        except Exception as e:
            logger.warning(f"Failed to record alert metric: {str(e)}")
    
    async def record_error_event(self, error_info: ErrorInfo, 
                                recovery_result: Optional[RecoveryResult] = None,
                                service_name: Optional[str] = None) -> None:
        """Record an error event for monitoring."""
        event = ErrorEvent(
            timestamp=datetime.now(timezone.utc),
            error_info=error_info,
            recovery_result=recovery_result,
            service_name=service_name,
            component=error_info.context.component or "unknown"
        )
        
        self.metrics_calculator.add_event(event)
        
        # Log the event
        with log_context(
            correlation_id=error_info.context.correlation_id,
            workflow_id=error_info.context.workflow_id,
            agent_name=error_info.context.agent_name
        ):
            logger.info(
                f"Error event recorded: {error_info.error_type}",
                extra={
                    'category': LogCategory.SYSTEM,
                    'data': event.to_dict()
                }
            )
    
    async def start_monitoring(self, check_interval_seconds: int = 30) -> None:
        """Start error monitoring."""
        if self.running:
            logger.warning("Error monitoring is already running")
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(
            self._monitoring_loop(check_interval_seconds)
        )
        
        logger.info("Error monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop error monitoring."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Error monitoring stopped")
    
    async def _monitoring_loop(self, check_interval_seconds: int) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Get recent events
                recent_events = self.metrics_calculator._get_events_in_window()
                
                # Check alert rules
                new_alerts = await self.alert_manager.check_rules(
                    self.metrics_calculator, recent_events
                )
                
                if new_alerts:
                    logger.info(f"Generated {len(new_alerts)} new alerts")
                
                # Record monitoring metrics
                await self._record_monitoring_metrics()
                
                await asyncio.sleep(check_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                await asyncio.sleep(check_interval_seconds)
    
    async def _record_monitoring_metrics(self) -> None:
        """Record monitoring metrics."""
        try:
            # Overall metrics
            error_rate = self.metrics_calculator.calculate_error_rate()
            recovery_rate = self.metrics_calculator.calculate_recovery_rate()
            
            await self.metrics_collector.record_monitoring_metric(
                "error_rate", error_rate, "errors_per_minute"
            )
            await self.metrics_collector.record_monitoring_metric(
                "recovery_rate", recovery_rate, "percentage"
            )
            
            # Active alerts count
            active_alerts_count = len(self.alert_manager.get_active_alerts())
            await self.metrics_collector.record_monitoring_metric(
                "active_alerts", float(active_alerts_count), "count"
            )
            
        except Exception as e:
            logger.warning(f"Failed to record monitoring metrics: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "running": self.running,
            "time_window_minutes": self.metrics_calculator.time_window_minutes,
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "alert_rules": len(self.alert_manager.rules),
            "recent_events": len(self.metrics_calculator._get_events_in_window()),
            "metrics": {
                "error_rate": self.metrics_calculator.calculate_error_rate(),
                "error_count": self.metrics_calculator.calculate_error_count(),
                "recovery_rate": self.metrics_calculator.calculate_recovery_rate(),
                "mean_time_to_recovery": self.metrics_calculator.calculate_mean_time_to_recovery()
            }
        }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for a specific service."""
        return {
            "service_name": service_name,
            "error_rate": self.metrics_calculator.calculate_error_rate(service_name),
            "error_count": self.metrics_calculator.calculate_error_count(service_name),
            "recovery_rate": self.metrics_calculator.calculate_recovery_rate(service_name),
            "availability": self.metrics_calculator.calculate_service_availability(service_name),
            "circuit_breaker_trips": self.metrics_calculator.calculate_circuit_breaker_trips(service_name)
        }


# Global error monitor instance
error_monitor = ErrorMonitor()