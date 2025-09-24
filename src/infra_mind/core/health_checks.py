"""
Comprehensive health check system for all system components.

Provides health monitoring for databases, caches, external APIs,
agents, and other critical system components with automatic
recovery and self-healing capabilities.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import aiohttp
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """System component types."""
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    AGENT = "agent"
    QUEUE = "queue"
    STORAGE = "storage"
    NETWORK = "network"
    SERVICE = "service"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    recovery_actions: List[str] = field(default_factory=list)


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    check_interval_seconds: int = 30
    timeout_seconds: float = 10.0
    failure_threshold: int = 3
    recovery_threshold: int = 2
    enable_auto_recovery: bool = True
    enable_notifications: bool = True
    critical_component: bool = False


class BaseHealthCheck(ABC):
    """Base class for health check implementations."""
    
    def __init__(self, name: str, component_type: ComponentType, config: HealthCheckConfig):
        """
        Initialize health check.
        
        Args:
            name: Component name
            component_type: Type of component
            config: Health check configuration
        """
        self.name = name
        self.component_type = component_type
        self.config = config
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time: Optional[datetime] = None
        self.last_status = HealthStatus.UNKNOWN
        self.is_recovering = False
    
    @abstractmethod
    async def perform_check(self) -> HealthCheckResult:
        """
        Perform the actual health check.
        
        Returns:
            Health check result
        """
        pass
    
    async def check_health(self) -> HealthCheckResult:
        """
        Execute health check with error handling and timing.
        
        Returns:
            Health check result
        """
        start_time = time.time()
        self.last_check_time = datetime.utcnow()
        
        try:
            # Perform check with timeout
            result = await asyncio.wait_for(
                self.perform_check(),
                timeout=self.config.timeout_seconds
            )
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            result.response_time_ms = response_time
            result.timestamp = self.last_check_time
            
            # Update status tracking
            if result.status == HealthStatus.HEALTHY:
                self.consecutive_failures = 0
                self.consecutive_successes += 1
                
                # Check if component recovered
                if self.is_recovering and self.consecutive_successes >= self.config.recovery_threshold:
                    self.is_recovering = False
                    logger.info(f"Component {self.name} has recovered")
                    result.recovery_actions.append("Component recovered from failure")
            else:
                self.consecutive_successes = 0
                self.consecutive_failures += 1
                
                # Check if component needs recovery
                if (self.consecutive_failures >= self.config.failure_threshold and 
                    not self.is_recovering):
                    self.is_recovering = True
                    logger.warning(f"Component {self.name} requires recovery")
                    
                    if self.config.enable_auto_recovery:
                        recovery_result = await self.attempt_recovery()
                        result.recovery_actions.extend(recovery_result)
            
            self.last_status = result.status
            return result
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                timestamp=self.last_check_time,
                error_message=f"Health check timeout after {self.config.timeout_seconds}s",
                recovery_actions=["Timeout detected - component may be overloaded"]
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            logger.error(f"Health check failed for {self.name}: {e}")
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                timestamp=self.last_check_time,
                error_message=str(e),
                recovery_actions=[f"Exception occurred: {str(e)}"]
            )
    
    async def attempt_recovery(self) -> List[str]:
        """
        Attempt to recover the component.
        
        Returns:
            List of recovery actions taken
        """
        recovery_actions = []
        
        try:
            # Override in subclasses for specific recovery logic
            recovery_actions.append(f"Attempted automatic recovery for {self.name}")
            logger.info(f"Recovery attempted for component {self.name}")
            
        except Exception as e:
            recovery_actions.append(f"Recovery failed: {str(e)}")
            logger.error(f"Recovery failed for {self.name}: {e}")
        
        return recovery_actions


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for MongoDB database."""
    
    def __init__(self, name: str, connection_string: str, config: HealthCheckConfig):
        """
        Initialize database health check.
        
        Args:
            name: Database name
            connection_string: MongoDB connection string
            config: Health check configuration
        """
        super().__init__(name, ComponentType.DATABASE, config)
        self.connection_string = connection_string
        self.client: Optional[AsyncIOMotorClient] = None
    
    async def perform_check(self) -> HealthCheckResult:
        """Perform database health check."""
        try:
            # Create client if needed
            if not self.client:
                self.client = AsyncIOMotorClient(self.connection_string)
            
            # Test connection with ping
            await self.client.admin.command('ping')
            
            # Get database stats
            db = self.client.get_default_database()
            stats = await db.command('dbStats')
            
            # Check connection pool
            server_info = await self.client.server_info()
            
            details = {
                "server_version": server_info.get("version"),
                "database_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "collections": stats.get("collections", 0),
                "indexes": stats.get("indexes", 0),
                "connection_pool_size": getattr(self.client, 'max_pool_size', 'unknown')
            }
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY,
                response_time_ms=0,  # Will be set by parent
                timestamp=datetime.utcnow(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def attempt_recovery(self) -> List[str]:
        """Attempt database recovery."""
        recovery_actions = await super().attempt_recovery()
        
        try:
            # Close and recreate connection
            if self.client:
                self.client.close()
                self.client = None
            
            # Wait before reconnecting
            await asyncio.sleep(1)
            
            # Create new connection
            self.client = AsyncIOMotorClient(self.connection_string)
            
            recovery_actions.append("Database connection reset")
            
        except Exception as e:
            recovery_actions.append(f"Database recovery failed: {str(e)}")
        
        return recovery_actions


class CacheHealthCheck(BaseHealthCheck):
    """Health check for Redis cache."""
    
    def __init__(self, name: str, redis_url: str, config: HealthCheckConfig):
        """
        Initialize cache health check.
        
        Args:
            name: Cache name
            redis_url: Redis connection URL
            config: Health check configuration
        """
        super().__init__(name, ComponentType.CACHE, config)
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
    
    async def perform_check(self) -> HealthCheckResult:
        """Perform cache health check."""
        try:
            # Create client if needed
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)
            
            # Test connection with ping
            await self.redis_client.ping()
            
            # Get Redis info
            info = await self.redis_client.info()
            
            # Test set/get operation
            test_key = f"health_check_{int(time.time())}"
            await self.redis_client.set(test_key, "test_value", ex=60)
            test_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            if test_value != b"test_value":
                raise Exception("Cache read/write test failed")
            
            details = {
                "redis_version": info.get("redis_version"),
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate_percent": self._calculate_hit_rate(info)
            }
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate percentage."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    async def attempt_recovery(self) -> List[str]:
        """Attempt cache recovery."""
        recovery_actions = await super().attempt_recovery()
        
        try:
            # Close and recreate connection
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            
            # Wait before reconnecting
            await asyncio.sleep(1)
            
            # Create new connection
            self.redis_client = redis.from_url(self.redis_url)
            
            recovery_actions.append("Cache connection reset")
            
        except Exception as e:
            recovery_actions.append(f"Cache recovery failed: {str(e)}")
        
        return recovery_actions


class ExternalAPIHealthCheck(BaseHealthCheck):
    """Health check for external APIs."""
    
    def __init__(self, name: str, api_url: str, config: HealthCheckConfig, 
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize external API health check.
        
        Args:
            name: API name
            api_url: API endpoint URL
            config: Health check configuration
            headers: Optional HTTP headers
        """
        super().__init__(name, ComponentType.EXTERNAL_API, config)
        self.api_url = api_url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def perform_check(self) -> HealthCheckResult:
        """Perform external API health check."""
        try:
            # Create session if needed
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Make health check request
            async with self.session.get(
                self.api_url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                
                status = HealthStatus.HEALTHY
                details = {
                    "status_code": response.status,
                    "content_type": response.headers.get("content-type"),
                    "server": response.headers.get("server"),
                    "response_size_bytes": len(await response.read())
                }
                
                # Determine health based on status code
                if response.status >= 500:
                    status = HealthStatus.UNHEALTHY
                elif response.status >= 400:
                    status = HealthStatus.DEGRADED
                
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=status,
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                    details=details
                )
                
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def attempt_recovery(self) -> List[str]:
        """Attempt API recovery."""
        recovery_actions = await super().attempt_recovery()
        
        try:
            # Close and recreate session
            if self.session:
                await self.session.close()
                self.session = None
            
            # Wait before reconnecting
            await asyncio.sleep(2)
            
            recovery_actions.append("API session reset")
            
        except Exception as e:
            recovery_actions.append(f"API recovery failed: {str(e)}")
        
        return recovery_actions


class AgentHealthCheck(BaseHealthCheck):
    """Health check for AI agents."""
    
    def __init__(self, name: str, agent_instance: Any, config: HealthCheckConfig):
        """
        Initialize agent health check.
        
        Args:
            name: Agent name
            agent_instance: Agent instance to check
            config: Health check configuration
        """
        super().__init__(name, ComponentType.AGENT, config)
        self.agent_instance = agent_instance
    
    async def perform_check(self) -> HealthCheckResult:
        """Perform agent health check."""
        try:
            # Check if agent is responsive
            if hasattr(self.agent_instance, 'health_check'):
                health_result = await self.agent_instance.health_check()
            else:
                # Basic health check - verify agent attributes
                health_result = {
                    "status": "healthy",
                    "memory_usage": getattr(self.agent_instance, 'memory_usage', 0),
                    "active_tasks": getattr(self.agent_instance, 'active_tasks', 0)
                }
            
            details = {
                "agent_type": type(self.agent_instance).__name__,
                "memory_usage_mb": health_result.get("memory_usage", 0),
                "active_tasks": health_result.get("active_tasks", 0),
                "last_activity": getattr(self.agent_instance, 'last_activity', None)
            }
            
            status = HealthStatus.HEALTHY
            if health_result.get("status") == "degraded":
                status = HealthStatus.DEGRADED
            elif health_result.get("status") == "unhealthy":
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def attempt_recovery(self) -> List[str]:
        """Attempt agent recovery."""
        recovery_actions = await super().attempt_recovery()
        
        try:
            # Attempt to restart agent if it has restart method
            if hasattr(self.agent_instance, 'restart'):
                await self.agent_instance.restart()
                recovery_actions.append("Agent restarted")
            elif hasattr(self.agent_instance, 'reset'):
                await self.agent_instance.reset()
                recovery_actions.append("Agent reset")
            else:
                recovery_actions.append("No recovery method available for agent")
            
        except Exception as e:
            recovery_actions.append(f"Agent recovery failed: {str(e)}")
        
        return recovery_actions


class HealthCheckManager:
    """
    Centralized health check manager for all system components.
    
    Coordinates health checks, manages recovery actions, and provides
    system-wide health status reporting.
    """
    
    def __init__(self):
        """Initialize health check manager."""
        self.health_checks: Dict[str, BaseHealthCheck] = {}
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.is_running = False
        self.check_task: Optional[asyncio.Task] = None
        self.notification_callbacks: List[Callable] = []
    
    def register_health_check(self, health_check: BaseHealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            health_check: Health check instance to register
        """
        self.health_checks[health_check.name] = health_check
        self.health_history[health_check.name] = []
        logger.info(f"Registered health check for {health_check.name}")
    
    def register_notification_callback(self, callback: Callable) -> None:
        """
        Register a callback for health status notifications.
        
        Args:
            callback: Callback function to call on status changes
        """
        self.notification_callbacks.append(callback)
    
    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self.is_running:
            logger.warning("Health monitoring is already running")
            return
        
        self.is_running = True
        self.check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started health monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                # Run all health checks
                await self.check_all_components()
                
                # Wait for next check interval
                await asyncio.sleep(30)  # Default 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def check_all_components(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all registered components.
        
        Returns:
            Dictionary of component names to health check results
        """
        results = {}
        
        # Run all health checks concurrently
        tasks = []
        for name, health_check in self.health_checks.items():
            task = asyncio.create_task(health_check.check_health())
            tasks.append((name, task))
        
        # Collect results
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                
                # Store in history
                self.health_history[name].append(result)
                
                # Keep only last 100 results
                if len(self.health_history[name]) > 100:
                    self.health_history[name] = self.health_history[name][-100:]
                
                # Send notifications if enabled
                if self.health_checks[name].config.enable_notifications:
                    await self._send_notifications(result)
                
            except Exception as e:
                logger.error(f"Error checking health of {name}: {e}")
                results[name] = HealthCheckResult(
                    component_name=name,
                    component_type=ComponentType.SERVICE,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                    error_message=str(e)
                )
        
        return results
    
    async def check_component(self, component_name: str) -> Optional[HealthCheckResult]:
        """
        Check health of a specific component.
        
        Args:
            component_name: Name of component to check
            
        Returns:
            Health check result or None if component not found
        """
        if component_name not in self.health_checks:
            return None
        
        health_check = self.health_checks[component_name]
        result = await health_check.check_health()
        
        # Store in history
        self.health_history[component_name].append(result)
        if len(self.health_history[component_name]) > 100:
            self.health_history[component_name] = self.health_history[component_name][-100:]
        
        return result
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            System health summary
        """
        if not self.health_checks:
            return {
                "overall_status": HealthStatus.UNKNOWN,
                "total_components": 0,
                "healthy_components": 0,
                "degraded_components": 0,
                "unhealthy_components": 0,
                "components": {}
            }
        
        # Get latest results
        component_statuses = {}
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for name, health_check in self.health_checks.items():
            latest_result = None
            if name in self.health_history and self.health_history[name]:
                latest_result = self.health_history[name][-1]
            
            if latest_result:
                status = latest_result.status
                component_statuses[name] = {
                    "status": status,
                    "last_check": latest_result.timestamp.isoformat(),
                    "response_time_ms": latest_result.response_time_ms,
                    "component_type": latest_result.component_type,
                    "error_message": latest_result.error_message
                }
                
                if status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif status == HealthStatus.DEGRADED:
                    degraded_count += 1
                elif status == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
            else:
                component_statuses[name] = {
                    "status": HealthStatus.UNKNOWN,
                    "last_check": None,
                    "response_time_ms": 0,
                    "component_type": health_check.component_type,
                    "error_message": "No health check data available"
                }
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        if unhealthy_count > 0:
            # Check if any critical components are unhealthy
            critical_unhealthy = any(
                self.health_checks[name].config.critical_component
                for name, status in component_statuses.items()
                if status["status"] == HealthStatus.UNHEALTHY
            )
            overall_status = HealthStatus.UNHEALTHY if critical_unhealthy else HealthStatus.DEGRADED
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        
        return {
            "overall_status": overall_status,
            "total_components": len(self.health_checks),
            "healthy_components": healthy_count,
            "degraded_components": degraded_count,
            "unhealthy_components": unhealthy_count,
            "unknown_components": len(self.health_checks) - healthy_count - degraded_count - unhealthy_count,
            "components": component_statuses,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_component_history(self, component_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get health check history for a component.
        
        Args:
            component_name: Name of component
            limit: Maximum number of results to return
            
        Returns:
            List of health check results
        """
        if component_name not in self.health_history:
            return []
        
        history = self.health_history[component_name][-limit:]
        return [
            {
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "error_message": result.error_message,
                "details": result.details,
                "recovery_actions": result.recovery_actions
            }
            for result in history
        ]
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status (alias for get_system_health_summary for backward compatibility).
        
        Returns:
            System health summary
        """
        return self.get_system_health_summary()
    
    async def _send_notifications(self, result: HealthCheckResult) -> None:
        """Send notifications for health status changes."""
        try:
            for callback in self.notification_callbacks:
                await callback(result)
        except Exception as e:
            logger.error(f"Error sending health notification: {e}")


# Global health check manager instance
health_manager = HealthCheckManager()


def get_health_manager() -> HealthCheckManager:
    """Get the global health check manager instance."""
    return health_manager


class AlertingSystem:
    """Comprehensive alerting system for health monitoring."""
    
    def __init__(self):
        """Initialize alerting system."""
        self.alert_rules: List[Dict[str, Any]] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.notification_channels: List[Callable] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.escalation_rules: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_alert_rule(self, rule: Dict[str, Any]) -> None:
        """Add an alert rule."""
        required_fields = ['name', 'condition', 'severity', 'message']
        if not all(field in rule for field in required_fields):
            raise ValueError(f"Alert rule must contain: {required_fields}")
        
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule['name']}")
    
    def add_notification_channel(self, channel: Callable) -> None:
        """Add a notification channel."""
        self.notification_channels.append(channel)
    
    async def evaluate_alerts(self, health_results: Dict[str, HealthCheckResult]) -> None:
        """Evaluate alert rules against health check results."""
        current_time = datetime.utcnow()
        
        for rule in self.alert_rules:
            try:
                alert_key = rule['name']
                
                # Check cooldown
                if alert_key in self.alert_cooldowns:
                    cooldown_end = self.alert_cooldowns[alert_key]
                    if current_time < cooldown_end:
                        continue
                
                # Evaluate condition
                if await self._evaluate_condition(rule['condition'], health_results):
                    # Create or update alert
                    if alert_key not in self.active_alerts:
                        alert = {
                            'id': f"{alert_key}_{int(current_time.timestamp())}",
                            'rule_name': rule['name'],
                            'severity': rule['severity'],
                            'message': rule['message'],
                            'created_at': current_time,
                            'updated_at': current_time,
                            'count': 1,
                            'status': 'active',
                            'affected_components': self._get_affected_components(rule['condition'], health_results)
                        }
                        
                        self.active_alerts[alert_key] = alert
                        self.alert_history.append(alert.copy())
                        
                        # Send notifications
                        await self._send_alert_notifications(alert)
                        
                        # Set cooldown
                        cooldown_minutes = rule.get('cooldown_minutes', 15)
                        self.alert_cooldowns[alert_key] = current_time + timedelta(minutes=cooldown_minutes)
                        
                        logger.warning(f"Alert triggered: {rule['name']}")
                    else:
                        # Update existing alert
                        self.active_alerts[alert_key]['count'] += 1
                        self.active_alerts[alert_key]['updated_at'] = current_time
                
                else:
                    # Clear alert if condition no longer met
                    if alert_key in self.active_alerts:
                        alert = self.active_alerts[alert_key]
                        alert['status'] = 'resolved'
                        alert['resolved_at'] = current_time
                        
                        # Send resolution notification
                        await self._send_resolution_notification(alert)
                        
                        del self.active_alerts[alert_key]
                        logger.info(f"Alert resolved: {rule['name']}")
            
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")
    
    async def _evaluate_condition(self, condition: Dict[str, Any], health_results: Dict[str, HealthCheckResult]) -> bool:
        """Evaluate alert condition."""
        condition_type = condition.get('type')
        
        if condition_type == 'component_status':
            component = condition.get('component')
            expected_status = condition.get('status')
            
            if component in health_results:
                return health_results[component].status == expected_status
        
        elif condition_type == 'response_time':
            component = condition.get('component')
            threshold_ms = condition.get('threshold_ms')
            operator = condition.get('operator', 'gt')
            
            if component in health_results:
                response_time = health_results[component].response_time_ms
                if operator == 'gt':
                    return response_time > threshold_ms
                elif operator == 'lt':
                    return response_time < threshold_ms
        
        elif condition_type == 'error_rate':
            # Calculate error rate from recent results
            error_count = sum(1 for result in health_results.values() if result.status == HealthStatus.UNHEALTHY)
            total_count = len(health_results)
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0
            
            threshold = condition.get('threshold_percent')
            return error_rate > threshold
        
        elif condition_type == 'multiple_failures':
            # Check if multiple components are failing
            failure_count = sum(1 for result in health_results.values() if result.status == HealthStatus.UNHEALTHY)
            threshold = condition.get('threshold_count', 2)
            return failure_count >= threshold
        
        return False
    
    def _get_affected_components(self, condition: Dict[str, Any], health_results: Dict[str, HealthCheckResult]) -> List[str]:
        """Get list of components affected by the alert condition."""
        affected = []
        
        condition_type = condition.get('type')
        
        if condition_type == 'component_status':
            component = condition.get('component')
            if component:
                affected.append(component)
        elif condition_type in ['error_rate', 'multiple_failures']:
            # Include all unhealthy components
            affected = [
                name for name, result in health_results.items()
                if result.status == HealthStatus.UNHEALTHY
            ]
        
        return affected
    
    async def _send_alert_notifications(self, alert: Dict[str, Any]) -> None:
        """Send alert notifications through all channels."""
        for channel in self.notification_channels:
            try:
                await channel(alert, 'alert')
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
    
    async def _send_resolution_notification(self, alert: Dict[str, Any]) -> None:
        """Send alert resolution notifications."""
        for channel in self.notification_channels:
            try:
                await channel(alert, 'resolution')
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alert_history[-limit:]


class AutoRecoverySystem:
    """Automated recovery system for failed components."""
    
    def __init__(self):
        """Initialize auto-recovery system."""
        self.recovery_strategies: Dict[str, List[Callable]] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.recovery_cooldowns: Dict[str, datetime] = {}
    
    def register_recovery_strategy(self, component_name: str, strategy: Callable) -> None:
        """Register a recovery strategy for a component."""
        if component_name not in self.recovery_strategies:
            self.recovery_strategies[component_name] = []
        
        self.recovery_strategies[component_name].append(strategy)
        logger.info(f"Registered recovery strategy for {component_name}")
    
    async def attempt_recovery(self, component_name: str, health_result: HealthCheckResult) -> Dict[str, Any]:
        """Attempt to recover a failed component."""
        current_time = datetime.utcnow()
        
        # Check cooldown
        cooldown_key = f"{component_name}_recovery"
        if cooldown_key in self.recovery_cooldowns:
            if current_time < self.recovery_cooldowns[cooldown_key]:
                return {
                    'success': False,
                    'message': 'Recovery in cooldown period',
                    'next_attempt': self.recovery_cooldowns[cooldown_key].isoformat()
                }
        
        recovery_result = {
            'component_name': component_name,
            'started_at': current_time,
            'strategies_attempted': [],
            'success': False,
            'error_message': None
        }
        
        if component_name in self.recovery_strategies:
            for strategy in self.recovery_strategies[component_name]:
                try:
                    strategy_name = getattr(strategy, '__name__', 'unknown_strategy')
                    logger.info(f"Attempting recovery strategy '{strategy_name}' for {component_name}")
                    
                    result = await strategy(health_result)
                    recovery_result['strategies_attempted'].append({
                        'strategy': strategy_name,
                        'success': result.get('success', False),
                        'message': result.get('message')
                    })
                    
                    if result.get('success', False):
                        recovery_result['success'] = True
                        break
                
                except Exception as e:
                    logger.error(f"Recovery strategy failed for {component_name}: {e}")
                    recovery_result['strategies_attempted'].append({
                        'strategy': strategy_name,
                        'success': False,
                        'message': str(e)
                    })
        
        recovery_result['completed_at'] = datetime.utcnow()
        self.recovery_history.append(recovery_result)
        
        # Set cooldown (5 minutes)
        self.recovery_cooldowns[cooldown_key] = current_time + timedelta(minutes=5)
        
        return recovery_result
    
    def get_recovery_history(self, component_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recovery history."""
        history = self.recovery_history
        
        if component_name:
            history = [r for r in history if r['component_name'] == component_name]
        
        return history[-limit:]


async def initialize_health_checks(
    mongodb_url: str,
    redis_url: str,
    external_apis: Optional[Dict[str, str]] = None
) -> None:
    """
    Initialize comprehensive health checks for core system components.
    
    Args:
        mongodb_url: MongoDB connection URL
        redis_url: Redis connection URL
        external_apis: Dictionary of external API names to URLs
    """
    manager = get_health_manager()
    
    # Database health check
    db_config = HealthCheckConfig(
        check_interval_seconds=30,
        timeout_seconds=10.0,
        failure_threshold=3,
        critical_component=True
    )
    db_check = DatabaseHealthCheck("mongodb", mongodb_url, db_config)
    manager.register_health_check(db_check)
    
    # Cache health check
    cache_config = HealthCheckConfig(
        check_interval_seconds=30,
        timeout_seconds=5.0,
        failure_threshold=3,
        critical_component=True
    )
    cache_check = CacheHealthCheck("redis", redis_url, cache_config)
    manager.register_health_check(cache_check)
    
    # External API health checks
    if external_apis:
        api_config = HealthCheckConfig(
            check_interval_seconds=60,
            timeout_seconds=15.0,
            failure_threshold=5,
            critical_component=False
        )
        
        for api_name, api_url in external_apis.items():
            api_check = ExternalAPIHealthCheck(api_name, api_url, api_config)
            manager.register_health_check(api_check)
    
    # Start monitoring
    await manager.start_monitoring()
    logger.info("Health check system initialized")


async def shutdown_health_checks() -> None:
    """Shutdown health check system."""
    manager = get_health_manager()
    await manager.stop_monitoring()
    logger.info("Health check system shutdown")


async def setup_monitoring_dashboard(
    mongodb_url: str = "mongodb://localhost:27017",
    redis_url: str = "redis://localhost:6379",
    external_apis: Optional[Dict[str, str]] = None
) -> None:
    """Setup comprehensive monitoring dashboard with health checks."""
    manager = get_health_manager()
    
    # Database health check
    db_config = HealthCheckConfig(
        check_interval_seconds=30,
        timeout_seconds=10.0,
        failure_threshold=3,
        recovery_threshold=2,
        enable_auto_recovery=True,
        critical_component=True
    )
    db_health_check = DatabaseHealthCheck("mongodb", mongodb_url, db_config)
    manager.register_health_check(db_health_check)
    
    # Cache health check
    cache_config = HealthCheckConfig(
        check_interval_seconds=30,
        timeout_seconds=5.0,
        failure_threshold=3,
        recovery_threshold=2,
        enable_auto_recovery=True,
        critical_component=True
    )
    cache_health_check = CacheHealthCheck("redis", redis_url, cache_config)
    manager.register_health_check(cache_health_check)
    
    # External API health checks
    if external_apis:
        api_config = HealthCheckConfig(
            check_interval_seconds=60,
            timeout_seconds=15.0,
            failure_threshold=5,
            recovery_threshold=3,
            enable_auto_recovery=False,
            critical_component=False
        )
        
        for api_name, api_url in external_apis.items():
            api_health_check = ExternalAPIHealthCheck(api_name, api_url, api_config)
            manager.register_health_check(api_health_check)
    
    # Start monitoring
    await manager.start_monitoring()
    logger.info("Monitoring dashboard setup completed")


async def shutdown_health_checks() -> None:
    """Shutdown health check system."""
    manager = get_health_manager()
    await manager.stop_monitoring()
    logger.info("Health check system shutdown")