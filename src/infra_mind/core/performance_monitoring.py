"""
Real-time performance monitoring and alerting system.

Implements comprehensive performance monitoring with automated scaling policies,
real-time alerting, and performance optimization recommendations.
"""

import asyncio
import time
import logging
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import aiohttp
import websockets
from collections import deque, defaultdict

from .metrics_collector import get_metrics_collector
from .production_performance_optimizer import performance_optimizer
from .database import db
from .cache import cache_manager
from ..models.metrics import Metric, MetricType, MetricCategory

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(str, Enum):
    """Alert notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    SMS = "sms"
    DASHBOARD = "dashboard"


@dataclass
class PerformanceThreshold:
    """Performance monitoring threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: Optional[float] = None
    comparison_operator: str = ">"  # >, <, >=, <=, ==, !=
    evaluation_window_seconds: int = 300  # 5 minutes
    min_data_points: int = 3
    enabled: bool = True


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    description: str
    threshold: PerformanceThreshold
    channels: List[AlertChannel]
    cooldown_seconds: int = 1800  # 30 minutes
    auto_resolve: bool = True
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Alert:
    """Performance alert instance."""
    id: str
    rule_name: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    escalated: bool = False
    escalation_level: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingPolicy:
    """Automated scaling policy configuration."""
    name: str
    description: str
    trigger_metric: str
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_action: Callable
    scale_down_action: Callable
    cooldown_seconds: int = 600  # 10 minutes
    min_instances: int = 1
    max_instances: int = 10
    enabled: bool = True


class PerformanceMonitoringSystem:
    """
    Comprehensive performance monitoring and alerting system.
    
    Features:
    - Real-time performance monitoring
    - Configurable alert rules and thresholds
    - Multiple notification channels
    - Automated scaling policies
    - Performance optimization recommendations
    - Alert escalation and acknowledgment
    """
    
    def __init__(self):
        """Initialize performance monitoring system."""
        self.metrics_collector = get_metrics_collector()
        self.is_monitoring = False
        self.monitoring_tasks = []
        
        # Alert management
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.alert_cooldowns = {}
        
        # Scaling policies
        self.scaling_policies = {}
        self.scaling_cooldowns = {}
        
        # Performance data
        self.performance_data = defaultdict(lambda: deque(maxlen=1000))
        self.performance_trends = {}
        
        # Notification channels
        self.notification_channels = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.DASHBOARD: self._send_dashboard_alert
        }
        
        # WebSocket connections for real-time updates
        self.websocket_clients = set()
        
        # Configuration
        self.config = {
            "monitoring_interval_seconds": 30,
            "alert_evaluation_interval_seconds": 60,
            "performance_data_retention_hours": 24,
            "email_smtp_server": "localhost",
            "email_smtp_port": 587,
            "email_from": "alerts@infra-mind.com",
            "webhook_timeout_seconds": 10,
            "slack_webhook_url": None
        }
        
        # Initialize default thresholds and rules
        self._initialize_default_monitoring()
        
        logger.info("Performance monitoring system initialized")
    
    def _initialize_default_monitoring(self):
        """Initialize default monitoring thresholds and alert rules."""
        # Default performance thresholds
        default_thresholds = [
            PerformanceThreshold(
                metric_name="system.cpu.usage_percent",
                warning_threshold=70.0,
                critical_threshold=85.0,
                emergency_threshold=95.0
            ),
            PerformanceThreshold(
                metric_name="system.memory.usage_percent",
                warning_threshold=75.0,
                critical_threshold=90.0,
                emergency_threshold=98.0
            ),
            PerformanceThreshold(
                metric_name="system.disk.usage_percent",
                warning_threshold=80.0,
                critical_threshold=90.0,
                emergency_threshold=95.0
            ),
            PerformanceThreshold(
                metric_name="system.avg_response_time_ms",
                warning_threshold=2000.0,
                critical_threshold=5000.0,
                emergency_threshold=10000.0
            ),
            PerformanceThreshold(
                metric_name="system.error_rate_percent",
                warning_threshold=5.0,
                critical_threshold=10.0,
                emergency_threshold=25.0
            ),
            PerformanceThreshold(
                metric_name="database.query.avg_execution_time_ms",
                warning_threshold=500.0,
                critical_threshold=1000.0,
                emergency_threshold=2000.0
            ),
            PerformanceThreshold(
                metric_name="cache.hit_rate_percent",
                warning_threshold=70.0,
                critical_threshold=50.0,
                comparison_operator="<"
            )
        ]
        
        # Create default alert rules
        for threshold in default_thresholds:
            rule = AlertRule(
                name=f"{threshold.metric_name}_alert",
                description=f"Alert for {threshold.metric_name} performance threshold",
                threshold=threshold,
                channels=[AlertChannel.DASHBOARD, AlertChannel.EMAIL],
                cooldown_seconds=1800
            )
            self.alert_rules[rule.name] = rule
        
        # Default scaling policies
        self.scaling_policies["cpu_scaling"] = ScalingPolicy(
            name="cpu_scaling",
            description="Scale based on CPU usage",
            trigger_metric="system.cpu.usage_percent",
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            scale_up_action=self._scale_up_cpu_resources,
            scale_down_action=self._scale_down_cpu_resources
        )
        
        self.scaling_policies["memory_scaling"] = ScalingPolicy(
            name="memory_scaling",
            description="Scale based on memory usage",
            trigger_metric="system.memory.usage_percent",
            scale_up_threshold=85.0,
            scale_down_threshold=40.0,
            scale_up_action=self._scale_up_memory_resources,
            scale_down_action=self._scale_down_memory_resources
        )
    
    async def start_monitoring(self):
        """Start performance monitoring and alerting."""
        if self.is_monitoring:
            logger.warning("Performance monitoring already started")
            return
        
        self.is_monitoring = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
            asyncio.create_task(self._scaling_evaluation_loop()),
            asyncio.create_task(self._performance_analysis_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring and alerting."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.monitoring_tasks.clear()
        logger.info("Performance monitoring stopped")
    
    async def _performance_monitoring_loop(self):
        """Main performance monitoring loop."""
        while self.is_monitoring:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(self.config["monitoring_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
                await asyncio.sleep(self.config["monitoring_interval_seconds"])
    
    async def _alert_evaluation_loop(self):
        """Alert evaluation and notification loop."""
        while self.is_monitoring:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(self.config["alert_evaluation_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation loop error: {e}")
                await asyncio.sleep(self.config["alert_evaluation_interval_seconds"])
    
    async def _scaling_evaluation_loop(self):
        """Automated scaling evaluation loop."""
        while self.is_monitoring:
            try:
                await self._evaluate_scaling_policies()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling evaluation loop error: {e}")
                await asyncio.sleep(300)
    
    async def _performance_analysis_loop(self):
        """Performance trend analysis loop."""
        while self.is_monitoring:
            try:
                await self._analyze_performance_trends()
                await asyncio.sleep(1800)  # Analyze every 30 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance analysis loop error: {e}")
                await asyncio.sleep(1800)
    
    async def _cleanup_loop(self):
        """Cleanup old data and resolved alerts."""
        while self.is_monitoring:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Cleanup every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _collect_performance_metrics(self):
        """Collect current performance metrics."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Store metrics
            timestamp = datetime.utcnow()
            self.performance_data["system.cpu.usage_percent"].append({
                "value": cpu_percent,
                "timestamp": timestamp
            })
            self.performance_data["system.memory.usage_percent"].append({
                "value": memory.percent,
                "timestamp": timestamp
            })
            self.performance_data["system.disk.usage_percent"].append({
                "value": (disk.used / disk.total) * 100,
                "timestamp": timestamp
            })
            
            # Get performance optimizer metrics
            if performance_optimizer.is_optimizing:
                perf_metrics = performance_optimizer.performance_metrics
                
                self.performance_data["system.avg_response_time_ms"].append({
                    "value": perf_metrics.avg_response_time_ms,
                    "timestamp": timestamp
                })
                self.performance_data["system.error_rate_percent"].append({
                    "value": perf_metrics.error_rate_percent,
                    "timestamp": timestamp
                })
                self.performance_data["cache.hit_rate_percent"].append({
                    "value": perf_metrics.cache_hit_rate_percent,
                    "timestamp": timestamp
                })
                self.performance_data["database.query.avg_execution_time_ms"].append({
                    "value": perf_metrics.db_query_avg_time_ms,
                    "timestamp": timestamp
                })
            
            # Broadcast real-time metrics to WebSocket clients
            await self._broadcast_real_time_metrics()
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
    
    async def _evaluate_alert_rules(self):
        """Evaluate alert rules against current metrics."""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_single_alert_rule(rule)
            except Exception as e:
                logger.error(f"Failed to evaluate alert rule {rule_name}: {e}")
    
    async def _evaluate_single_alert_rule(self, rule: AlertRule):
        """Evaluate a single alert rule."""
        threshold = rule.threshold
        metric_data = self.performance_data.get(threshold.metric_name, deque())
        
        if len(metric_data) < threshold.min_data_points:
            return
        
        # Get recent data points within evaluation window
        cutoff_time = datetime.utcnow() - timedelta(seconds=threshold.evaluation_window_seconds)
        recent_data = [
            point for point in metric_data
            if point["timestamp"] > cutoff_time
        ]
        
        if len(recent_data) < threshold.min_data_points:
            return
        
        # Calculate current value (average of recent data points)
        current_value = sum(point["value"] for point in recent_data) / len(recent_data)
        
        # Evaluate threshold
        severity = self._evaluate_threshold(current_value, threshold)
        
        if severity:
            # Check cooldown
            if self._is_in_cooldown(rule.name):
                return
            
            # Create or update alert
            await self._create_or_update_alert(rule, severity, current_value)
        else:
            # Check if we should resolve existing alert
            await self._resolve_alert_if_exists(rule.name)
    
    def _evaluate_threshold(self, value: float, threshold: PerformanceThreshold) -> Optional[AlertSeverity]:
        """Evaluate if value exceeds threshold and return severity."""
        op = threshold.comparison_operator
        
        def compare(val, thresh):
            if op == ">":
                return val > thresh
            elif op == "<":
                return val < thresh
            elif op == ">=":
                return val >= thresh
            elif op == "<=":
                return val <= thresh
            elif op == "==":
                return val == thresh
            elif op == "!=":
                return val != thresh
            return False
        
        if threshold.emergency_threshold and compare(value, threshold.emergency_threshold):
            return AlertSeverity.EMERGENCY
        elif compare(value, threshold.critical_threshold):
            return AlertSeverity.CRITICAL
        elif compare(value, threshold.warning_threshold):
            return AlertSeverity.WARNING
        
        return None
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if alert rule is in cooldown period."""
        if rule_name not in self.alert_cooldowns:
            return False
        
        cooldown_until = self.alert_cooldowns[rule_name]
        return datetime.utcnow() < cooldown_until
    
    async def _create_or_update_alert(self, rule: AlertRule, severity: AlertSeverity, current_value: float):
        """Create new alert or update existing one."""
        alert_id = f"{rule.name}_{severity.value}"
        
        if alert_id in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[alert_id]
            alert.current_value = current_value
            alert.timestamp = datetime.utcnow()
        else:
            # Create new alert
            threshold_value = self._get_threshold_value_for_severity(rule.threshold, severity)
            
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                severity=severity,
                metric_name=rule.threshold.metric_name,
                current_value=current_value,
                threshold_value=threshold_value,
                message=self._generate_alert_message(rule, severity, current_value, threshold_value),
                timestamp=datetime.utcnow(),
                metadata={
                    "rule_description": rule.description,
                    "evaluation_window": rule.threshold.evaluation_window_seconds
                }
            )
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Set cooldown
            self.alert_cooldowns[rule.name] = datetime.utcnow() + timedelta(seconds=rule.cooldown_seconds)
            
            # Send notifications
            await self._send_alert_notifications(alert, rule.channels)
            
            logger.warning(f"Alert created: {alert.message}")
    
    async def _resolve_alert_if_exists(self, rule_name: str):
        """Resolve alert if it exists and conditions are no longer met."""
        alerts_to_resolve = [
            alert for alert in self.active_alerts.values()
            if alert.rule_name == rule_name and not alert.resolved
        ]
        
        for alert in alerts_to_resolve:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            # Remove from active alerts
            if alert.id in self.active_alerts:
                del self.active_alerts[alert.id]
            
            # Send resolution notification
            await self._send_alert_resolution_notification(alert)
            
            logger.info(f"Alert resolved: {alert.rule_name}")
    
    def _get_threshold_value_for_severity(self, threshold: PerformanceThreshold, severity: AlertSeverity) -> float:
        """Get threshold value for given severity."""
        if severity == AlertSeverity.EMERGENCY and threshold.emergency_threshold:
            return threshold.emergency_threshold
        elif severity == AlertSeverity.CRITICAL:
            return threshold.critical_threshold
        elif severity == AlertSeverity.WARNING:
            return threshold.warning_threshold
        return 0.0
    
    def _generate_alert_message(self, rule: AlertRule, severity: AlertSeverity, current_value: float, threshold_value: float) -> str:
        """Generate alert message."""
        return (
            f"{severity.value.upper()}: {rule.threshold.metric_name} "
            f"is {current_value:.2f} (threshold: {threshold_value:.2f}). "
            f"{rule.description}"
        )
    
    async def _send_alert_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send alert notifications through specified channels."""
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    await self.notification_channels[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    async def _send_alert_resolution_notification(self, alert: Alert):
        """Send alert resolution notification."""
        resolution_message = f"RESOLVED: {alert.message} - Alert resolved at {alert.resolved_at}"
        
        # Create temporary resolution alert for notification
        resolution_alert = Alert(
            id=f"{alert.id}_resolved",
            rule_name=alert.rule_name,
            severity=AlertSeverity.INFO,
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold_value=alert.threshold_value,
            message=resolution_message,
            timestamp=alert.resolved_at or datetime.utcnow(),
            resolved=True
        )
        
        await self._send_dashboard_alert(resolution_alert)
    
    # Notification channel implementations
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email_from"]
            msg['To'] = "admin@infra-mind.com"  # This would be configurable
            msg['Subject'] = f"Infra Mind Alert: {alert.severity.value.upper()} - {alert.metric_name}"
            
            body = f"""
            Alert Details:
            - Severity: {alert.severity.value.upper()}
            - Metric: {alert.metric_name}
            - Current Value: {alert.current_value:.2f}
            - Threshold: {alert.threshold_value:.2f}
            - Time: {alert.timestamp}
            - Message: {alert.message}
            
            Please investigate and take appropriate action.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # This would use actual SMTP configuration in production
            logger.info(f"Email alert would be sent: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook."""
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "metric": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=self.config["webhook_timeout_seconds"]
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent successfully: {alert.id}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _send_slack_alert(self, alert: Alert):
        """Send alert via Slack webhook."""
        try:
            slack_url = self.config.get("slack_webhook_url")
            if not slack_url:
                return
            
            color = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.EMERGENCY: "danger"
            }.get(alert.severity, "warning")
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"Infra Mind Alert: {alert.severity.value.upper()}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Current Value", "value": f"{alert.current_value:.2f}", "short": True},
                        {"title": "Threshold", "value": f"{alert.threshold_value:.2f}", "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ],
                    "ts": alert.timestamp.timestamp()
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent successfully: {alert.id}")
                    else:
                        logger.error(f"Slack alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_dashboard_alert(self, alert: Alert):
        """Send alert to dashboard via WebSocket."""
        try:
            message = {
                "type": "alert",
                "data": {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "metric": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
            }
            
            await self._broadcast_to_websockets(message)
            
        except Exception as e:
            logger.error(f"Failed to send dashboard alert: {e}")
    
    async def _broadcast_to_websockets(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket clients."""
        if not self.websocket_clients:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected_clients = set()
        
        for client in self.websocket_clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients
    
    async def _broadcast_real_time_metrics(self):
        """Broadcast real-time metrics to WebSocket clients."""
        try:
            # Get latest metrics
            latest_metrics = {}
            for metric_name, data in self.performance_data.items():
                if data:
                    latest_metrics[metric_name] = data[-1]["value"]
            
            message = {
                "type": "metrics",
                "data": latest_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._broadcast_to_websockets(message)
            
        except Exception as e:
            logger.error(f"Failed to broadcast real-time metrics: {e}")
    
    # Scaling policy implementations
    
    async def _evaluate_scaling_policies(self):
        """Evaluate automated scaling policies."""
        for policy_name, policy in self.scaling_policies.items():
            if not policy.enabled:
                continue
            
            try:
                await self._evaluate_single_scaling_policy(policy)
            except Exception as e:
                logger.error(f"Failed to evaluate scaling policy {policy_name}: {e}")
    
    async def _evaluate_single_scaling_policy(self, policy: ScalingPolicy):
        """Evaluate a single scaling policy."""
        # Check cooldown
        if policy.name in self.scaling_cooldowns:
            if datetime.utcnow() < self.scaling_cooldowns[policy.name]:
                return
        
        # Get current metric value
        metric_data = self.performance_data.get(policy.trigger_metric, deque())
        if not metric_data:
            return
        
        # Get recent average
        recent_data = list(metric_data)[-5:]  # Last 5 data points
        if len(recent_data) < 3:
            return
        
        current_value = sum(point["value"] for point in recent_data) / len(recent_data)
        
        # Evaluate scaling action
        if current_value > policy.scale_up_threshold:
            await self._execute_scale_up(policy, current_value)
        elif current_value < policy.scale_down_threshold:
            await self._execute_scale_down(policy, current_value)
    
    async def _execute_scale_up(self, policy: ScalingPolicy, current_value: float):
        """Execute scale up action."""
        try:
            await policy.scale_up_action(current_value)
            
            # Set cooldown
            self.scaling_cooldowns[policy.name] = datetime.utcnow() + timedelta(seconds=policy.cooldown_seconds)
            
            logger.info(f"Scaling up: {policy.name} - {policy.trigger_metric}={current_value:.2f}")
            
            # Create scaling alert
            scaling_alert = Alert(
                id=f"scaling_{policy.name}_up_{int(time.time())}",
                rule_name=f"scaling_{policy.name}",
                severity=AlertSeverity.INFO,
                metric_name=policy.trigger_metric,
                current_value=current_value,
                threshold_value=policy.scale_up_threshold,
                message=f"Scaling up: {policy.description} - {policy.trigger_metric}={current_value:.2f}",
                timestamp=datetime.utcnow()
            )
            
            await self._send_dashboard_alert(scaling_alert)
            
        except Exception as e:
            logger.error(f"Failed to execute scale up for {policy.name}: {e}")
    
    async def _execute_scale_down(self, policy: ScalingPolicy, current_value: float):
        """Execute scale down action."""
        try:
            await policy.scale_down_action(current_value)
            
            # Set cooldown
            self.scaling_cooldowns[policy.name] = datetime.utcnow() + timedelta(seconds=policy.cooldown_seconds)
            
            logger.info(f"Scaling down: {policy.name} - {policy.trigger_metric}={current_value:.2f}")
            
            # Create scaling alert
            scaling_alert = Alert(
                id=f"scaling_{policy.name}_down_{int(time.time())}",
                rule_name=f"scaling_{policy.name}",
                severity=AlertSeverity.INFO,
                metric_name=policy.trigger_metric,
                current_value=current_value,
                threshold_value=policy.scale_down_threshold,
                message=f"Scaling down: {policy.description} - {policy.trigger_metric}={current_value:.2f}",
                timestamp=datetime.utcnow()
            )
            
            await self._send_dashboard_alert(scaling_alert)
            
        except Exception as e:
            logger.error(f"Failed to execute scale down for {policy.name}: {e}")
    
    # Scaling action implementations (these would be customized based on infrastructure)
    
    async def _scale_up_cpu_resources(self, current_value: float):
        """Scale up CPU resources."""
        # This would implement actual CPU scaling logic
        logger.info(f"CPU scaling up triggered - current usage: {current_value:.2f}%")
        
        # Example: Increase performance optimizer settings
        if performance_optimizer.current_profile.max_concurrent_requests < 500:
            performance_optimizer.current_profile.max_concurrent_requests = min(
                500, 
                int(performance_optimizer.current_profile.max_concurrent_requests * 1.5)
            )
    
    async def _scale_down_cpu_resources(self, current_value: float):
        """Scale down CPU resources."""
        # This would implement actual CPU scaling logic
        logger.info(f"CPU scaling down triggered - current usage: {current_value:.2f}%")
        
        # Example: Decrease performance optimizer settings
        if performance_optimizer.current_profile.max_concurrent_requests > 10:
            performance_optimizer.current_profile.max_concurrent_requests = max(
                10,
                int(performance_optimizer.current_profile.max_concurrent_requests * 0.8)
            )
    
    async def _scale_up_memory_resources(self, current_value: float):
        """Scale up memory resources."""
        logger.info(f"Memory scaling up triggered - current usage: {current_value:.2f}%")
        
        # Example: Increase cache TTL to reduce memory pressure
        if performance_optimizer.current_profile.cache_ttl_seconds < 7200:
            performance_optimizer.current_profile.cache_ttl_seconds = min(
                7200,
                int(performance_optimizer.current_profile.cache_ttl_seconds * 1.2)
            )
    
    async def _scale_down_memory_resources(self, current_value: float):
        """Scale down memory resources."""
        logger.info(f"Memory scaling down triggered - current usage: {current_value:.2f}%")
        
        # Example: Decrease cache TTL to free memory
        if performance_optimizer.current_profile.cache_ttl_seconds > 300:
            performance_optimizer.current_profile.cache_ttl_seconds = max(
                300,
                int(performance_optimizer.current_profile.cache_ttl_seconds * 0.9)
            )
    
    async def _analyze_performance_trends(self):
        """Analyze performance trends and generate recommendations."""
        try:
            recommendations = []
            
            for metric_name, data in self.performance_data.items():
                if len(data) < 10:
                    continue
                
                # Calculate trend
                recent_values = [point["value"] for point in list(data)[-10:]]
                if len(recent_values) >= 5:
                    # Simple trend analysis
                    first_half = recent_values[:len(recent_values)//2]
                    second_half = recent_values[len(recent_values)//2:]
                    
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    
                    trend_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
                    
                    self.performance_trends[metric_name] = {
                        "trend_percent": trend_percent,
                        "direction": "increasing" if trend_percent > 5 else "decreasing" if trend_percent < -5 else "stable",
                        "current_avg": second_avg,
                        "previous_avg": first_avg,
                        "analyzed_at": datetime.utcnow()
                    }
                    
                    # Generate recommendations based on trends
                    if abs(trend_percent) > 20:  # Significant trend
                        if "cpu" in metric_name and trend_percent > 20:
                            recommendations.append(f"CPU usage trending up {trend_percent:.1f}% - consider scaling or optimization")
                        elif "memory" in metric_name and trend_percent > 20:
                            recommendations.append(f"Memory usage trending up {trend_percent:.1f}% - monitor for memory leaks")
                        elif "response_time" in metric_name and trend_percent > 20:
                            recommendations.append(f"Response time trending up {trend_percent:.1f}% - investigate performance bottlenecks")
            
            # Store recommendations
            if recommendations:
                await self._store_performance_recommendations(recommendations)
            
        except Exception as e:
            logger.error(f"Performance trend analysis failed: {e}")
    
    async def _store_performance_recommendations(self, recommendations: List[str]):
        """Store performance recommendations."""
        try:
            if db.database:
                recommendation_doc = {
                    "type": "performance_optimization",
                    "recommendations": recommendations,
                    "generated_at": datetime.utcnow(),
                    "trends": self.performance_trends
                }
                await db.database.performance_recommendations.insert_one(recommendation_doc)
            
            # Send recommendations to dashboard
            message = {
                "type": "recommendations",
                "data": {
                    "recommendations": recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await self._broadcast_to_websockets(message)
            
        except Exception as e:
            logger.error(f"Failed to store performance recommendations: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old performance data and resolved alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.config["performance_data_retention_hours"])
            
            # Clean up performance data
            for metric_name, data in self.performance_data.items():
                # Remove old data points
                while data and data[0]["timestamp"] < cutoff_time:
                    data.popleft()
            
            # Clean up resolved alerts from history
            self.alert_history = deque([
                alert for alert in self.alert_history
                if alert.timestamp > cutoff_time
            ], maxlen=10000)
            
            # Clean up old cooldowns
            expired_cooldowns = [
                rule_name for rule_name, cooldown_until in self.alert_cooldowns.items()
                if datetime.utcnow() > cooldown_until
            ]
            for rule_name in expired_cooldowns:
                del self.alert_cooldowns[rule_name]
            
            logger.debug("Performance monitoring cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    # Public API methods
    
    def add_websocket_client(self, websocket):
        """Add WebSocket client for real-time updates."""
        self.websocket_clients.add(websocket)
        logger.info(f"WebSocket client added - total clients: {len(self.websocket_clients)}")
    
    def remove_websocket_client(self, websocket):
        """Remove WebSocket client."""
        self.websocket_clients.discard(websocket)
        logger.info(f"WebSocket client removed - total clients: {len(self.websocket_clients)}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return list(self.alert_history)[-limit:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary."""
        return {
            "monitoring_active": self.is_monitoring,
            "active_alerts_count": len(self.active_alerts),
            "alert_rules_count": len(self.alert_rules),
            "scaling_policies_count": len(self.scaling_policies),
            "websocket_clients_count": len(self.websocket_clients),
            "performance_trends": self.performance_trends,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
        
        return False
    
    def add_alert_rule(self, rule: AlertRule):
        """Add new alert rule."""
        self.alert_rules[rule.name] = rule
        logger.info(f"Alert rule added: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove alert rule."""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Alert rule removed: {rule_name}")
            return True
        return False
    
    def add_scaling_policy(self, policy: ScalingPolicy):
        """Add new scaling policy."""
        self.scaling_policies[policy.name] = policy
        logger.info(f"Scaling policy added: {policy.name}")
    
    def remove_scaling_policy(self, policy_name: str) -> bool:
        """Remove scaling policy."""
        if policy_name in self.scaling_policies:
            del self.scaling_policies[policy_name]
            logger.info(f"Scaling policy removed: {policy_name}")
            return True
        return False


# Global performance monitoring instance
performance_monitoring = PerformanceMonitoringSystem()