"""
Automatic failover mechanisms for critical services.

Provides automatic failover capabilities for databases, caches,
external APIs, and other critical system components to ensure
high availability and system resilience.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import random

from .health_checks import HealthStatus, HealthCheckResult, get_health_manager

logger = logging.getLogger(__name__)


class FailoverStrategy(str, Enum):
    """Failover strategy types."""
    ACTIVE_PASSIVE = "active_passive"
    ACTIVE_ACTIVE = "active_active"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    PRIORITY = "priority"


class FailoverTrigger(str, Enum):
    """Failover trigger conditions."""
    HEALTH_CHECK_FAILURE = "health_check_failure"
    RESPONSE_TIME_THRESHOLD = "response_time_threshold"
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class FailoverConfig:
    """Configuration for failover behavior."""
    strategy: FailoverStrategy = FailoverStrategy.ACTIVE_PASSIVE
    health_check_failures: int = 3
    response_time_threshold_ms: float = 5000.0
    error_rate_threshold_percent: float = 10.0
    cooldown_period_seconds: int = 300
    auto_failback: bool = True
    failback_health_checks: int = 5
    notification_enabled: bool = True


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration."""
    name: str
    url: str
    weight: int = 100
    priority: int = 1
    is_active: bool = True
    is_healthy: bool = True
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    response_time_ms: float = 0.0
    error_rate_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailoverEvent:
    """Failover event record."""
    timestamp: datetime
    service_name: str
    trigger: FailoverTrigger
    from_endpoint: Optional[str]
    to_endpoint: Optional[str]
    reason: str
    success: bool
    recovery_time_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseFailoverManager(ABC):
    """Base class for failover managers."""
    
    def __init__(self, service_name: str, config: FailoverConfig):
        """
        Initialize failover manager.
        
        Args:
            service_name: Name of the service
            config: Failover configuration
        """
        self.service_name = service_name
        self.config = config
        self.endpoints: List[ServiceEndpoint] = []
        self.current_endpoint: Optional[ServiceEndpoint] = None
        self.failover_history: List[FailoverEvent] = []
        self.last_failover_time: Optional[datetime] = None
        self.is_in_cooldown = False
        self.notification_callbacks: List[Callable] = []
    
    def add_endpoint(self, endpoint: ServiceEndpoint) -> None:
        """
        Add a service endpoint.
        
        Args:
            endpoint: Service endpoint to add
        """
        self.endpoints.append(endpoint)
        
        # Set as current if it's the first active endpoint
        if not self.current_endpoint and endpoint.is_active:
            self.current_endpoint = endpoint
        
        logger.info(f"Added endpoint {endpoint.name} to service {self.service_name}")
    
    def remove_endpoint(self, endpoint_name: str) -> bool:
        """
        Remove a service endpoint.
        
        Args:
            endpoint_name: Name of endpoint to remove
            
        Returns:
            True if endpoint was removed, False if not found
        """
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.name == endpoint_name:
                removed_endpoint = self.endpoints.pop(i)
                
                # If this was the current endpoint, trigger failover
                if self.current_endpoint and self.current_endpoint.name == endpoint_name:
                    asyncio.create_task(self._trigger_failover(
                        FailoverTrigger.MANUAL,
                        f"Endpoint {endpoint_name} manually removed"
                    ))
                
                logger.info(f"Removed endpoint {endpoint_name} from service {self.service_name}")
                return True
        
        return False
    
    def register_notification_callback(self, callback: Callable) -> None:
        """
        Register a callback for failover notifications.
        
        Args:
            callback: Callback function
        """
        self.notification_callbacks.append(callback)
    
    @abstractmethod
    async def select_endpoint(self) -> Optional[ServiceEndpoint]:
        """
        Select the best available endpoint based on strategy.
        
        Returns:
            Selected endpoint or None if none available
        """
        pass
    
    async def get_current_endpoint(self) -> Optional[ServiceEndpoint]:
        """
        Get the current active endpoint.
        
        Returns:
            Current endpoint or None if none available
        """
        if not self.current_endpoint or not self.current_endpoint.is_active:
            self.current_endpoint = await self.select_endpoint()
        
        return self.current_endpoint
    
    async def check_failover_conditions(self, endpoint: ServiceEndpoint, 
                                      health_result: HealthCheckResult) -> bool:
        """
        Check if failover conditions are met.
        
        Args:
            endpoint: Endpoint to check
            health_result: Latest health check result
            
        Returns:
            True if failover should be triggered
        """
        # Health check failure condition
        if (health_result.status == HealthStatus.UNHEALTHY and 
            endpoint.consecutive_failures >= self.config.health_check_failures):
            return True
        
        # Response time threshold condition
        if (health_result.response_time_ms > self.config.response_time_threshold_ms):
            return True
        
        # Error rate threshold condition
        if endpoint.error_rate_percent > self.config.error_rate_threshold_percent:
            return True
        
        return False
    
    async def _trigger_failover(self, trigger: FailoverTrigger, reason: str) -> bool:
        """
        Trigger failover to a different endpoint.
        
        Args:
            trigger: What triggered the failover
            reason: Reason for failover
            
        Returns:
            True if failover was successful
        """
        # Check cooldown period
        if self.is_in_cooldown:
            logger.warning(f"Failover for {self.service_name} is in cooldown period")
            return False
        
        start_time = datetime.utcnow()
        old_endpoint = self.current_endpoint
        
        try:
            # Select new endpoint
            new_endpoint = await self.select_endpoint()
            
            if not new_endpoint:
                logger.error(f"No healthy endpoints available for {self.service_name}")
                await self._record_failover_event(
                    trigger, old_endpoint, None, reason, False, start_time
                )
                return False
            
            if old_endpoint and new_endpoint.name == old_endpoint.name:
                logger.info(f"No failover needed for {self.service_name} - same endpoint selected")
                return True
            
            # Perform failover
            self.current_endpoint = new_endpoint
            self.last_failover_time = start_time
            self.is_in_cooldown = True
            
            # Schedule cooldown reset
            asyncio.create_task(self._reset_cooldown())
            
            # Record event
            recovery_time = (datetime.utcnow() - start_time).total_seconds()
            await self._record_failover_event(
                trigger, old_endpoint, new_endpoint, reason, True, start_time, recovery_time
            )
            
            # Send notifications
            if self.config.notification_enabled:
                await self._send_failover_notifications(
                    trigger, old_endpoint, new_endpoint, reason, True
                )
            
            logger.info(
                f"Failover successful for {self.service_name}: "
                f"{old_endpoint.name if old_endpoint else 'None'} -> {new_endpoint.name}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failover failed for {self.service_name}: {e}")
            await self._record_failover_event(
                trigger, old_endpoint, None, f"{reason} - Error: {str(e)}", False, start_time
            )
            return False
    
    async def _reset_cooldown(self) -> None:
        """Reset cooldown period after configured time."""
        await asyncio.sleep(self.config.cooldown_period_seconds)
        self.is_in_cooldown = False
        logger.info(f"Cooldown period reset for {self.service_name}")
    
    async def _record_failover_event(self, trigger: FailoverTrigger, 
                                   from_endpoint: Optional[ServiceEndpoint],
                                   to_endpoint: Optional[ServiceEndpoint],
                                   reason: str, success: bool,
                                   start_time: datetime,
                                   recovery_time: Optional[float] = None) -> None:
        """Record failover event in history."""
        event = FailoverEvent(
            timestamp=start_time,
            service_name=self.service_name,
            trigger=trigger,
            from_endpoint=from_endpoint.name if from_endpoint else None,
            to_endpoint=to_endpoint.name if to_endpoint else None,
            reason=reason,
            success=success,
            recovery_time_seconds=recovery_time
        )
        
        self.failover_history.append(event)
        
        # Keep only last 100 events
        if len(self.failover_history) > 100:
            self.failover_history = self.failover_history[-100:]
    
    async def _send_failover_notifications(self, trigger: FailoverTrigger,
                                         from_endpoint: Optional[ServiceEndpoint],
                                         to_endpoint: Optional[ServiceEndpoint],
                                         reason: str, success: bool) -> None:
        """Send failover notifications to registered callbacks."""
        try:
            notification_data = {
                "service_name": self.service_name,
                "trigger": trigger,
                "from_endpoint": from_endpoint.name if from_endpoint else None,
                "to_endpoint": to_endpoint.name if to_endpoint else None,
                "reason": reason,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for callback in self.notification_callbacks:
                await callback(notification_data)
                
        except Exception as e:
            logger.error(f"Error sending failover notifications: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and endpoint information."""
        return {
            "service_name": self.service_name,
            "current_endpoint": self.current_endpoint.name if self.current_endpoint else None,
            "total_endpoints": len(self.endpoints),
            "healthy_endpoints": len([e for e in self.endpoints if e.is_healthy]),
            "active_endpoints": len([e for e in self.endpoints if e.is_active]),
            "is_in_cooldown": self.is_in_cooldown,
            "last_failover": self.last_failover_time.isoformat() if self.last_failover_time else None,
            "failover_count_24h": len([
                e for e in self.failover_history 
                if e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]),
            "endpoints": [
                {
                    "name": e.name,
                    "url": e.url,
                    "is_active": e.is_active,
                    "is_healthy": e.is_healthy,
                    "weight": e.weight,
                    "priority": e.priority,
                    "consecutive_failures": e.consecutive_failures,
                    "consecutive_successes": e.consecutive_successes,
                    "response_time_ms": e.response_time_ms,
                    "error_rate_percent": e.error_rate_percent
                }
                for e in self.endpoints
            ]
        }


class ActivePassiveFailoverManager(BaseFailoverManager):
    """Active-passive failover manager."""
    
    async def select_endpoint(self) -> Optional[ServiceEndpoint]:
        """Select endpoint using active-passive strategy."""
        # Sort by priority (lower number = higher priority)
        sorted_endpoints = sorted(
            [e for e in self.endpoints if e.is_active],
            key=lambda x: x.priority
        )
        
        # Return first healthy endpoint
        for endpoint in sorted_endpoints:
            if endpoint.is_healthy:
                return endpoint
        
        # If no healthy endpoints, return first active endpoint
        return sorted_endpoints[0] if sorted_endpoints else None


class RoundRobinFailoverManager(BaseFailoverManager):
    """Round-robin failover manager."""
    
    def __init__(self, service_name: str, config: FailoverConfig):
        super().__init__(service_name, config)
        self.current_index = 0
    
    async def select_endpoint(self) -> Optional[ServiceEndpoint]:
        """Select endpoint using round-robin strategy."""
        healthy_endpoints = [e for e in self.endpoints if e.is_active and e.is_healthy]
        
        if not healthy_endpoints:
            # Fallback to any active endpoint
            active_endpoints = [e for e in self.endpoints if e.is_active]
            return active_endpoints[0] if active_endpoints else None
        
        # Round-robin selection
        endpoint = healthy_endpoints[self.current_index % len(healthy_endpoints)]
        self.current_index = (self.current_index + 1) % len(healthy_endpoints)
        
        return endpoint


class WeightedFailoverManager(BaseFailoverManager):
    """Weighted failover manager."""
    
    async def select_endpoint(self) -> Optional[ServiceEndpoint]:
        """Select endpoint using weighted strategy."""
        healthy_endpoints = [e for e in self.endpoints if e.is_active and e.is_healthy]
        
        if not healthy_endpoints:
            # Fallback to any active endpoint
            active_endpoints = [e for e in self.endpoints if e.is_active]
            return active_endpoints[0] if active_endpoints else None
        
        # Weighted random selection
        total_weight = sum(e.weight for e in healthy_endpoints)
        if total_weight == 0:
            return healthy_endpoints[0]
        
        random_weight = random.uniform(0, total_weight)
        current_weight = 0
        
        for endpoint in healthy_endpoints:
            current_weight += endpoint.weight
            if random_weight <= current_weight:
                return endpoint
        
        return healthy_endpoints[-1]  # Fallback


class FailoverOrchestrator:
    """
    Orchestrates failover for multiple services.
    
    Manages failover managers for different services and coordinates
    system-wide failover operations.
    """
    
    def __init__(self):
        """Initialize failover orchestrator."""
        self.failover_managers: Dict[str, BaseFailoverManager] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
    
    def register_service(self, service_name: str, strategy: FailoverStrategy,
                        config: Optional[FailoverConfig] = None) -> BaseFailoverManager:
        """
        Register a service for failover management.
        
        Args:
            service_name: Name of the service
            strategy: Failover strategy to use
            config: Failover configuration
            
        Returns:
            Failover manager instance
        """
        if not config:
            config = FailoverConfig()
        
        # Create appropriate failover manager
        if strategy == FailoverStrategy.ACTIVE_PASSIVE:
            manager = ActivePassiveFailoverManager(service_name, config)
        elif strategy == FailoverStrategy.ROUND_ROBIN:
            manager = RoundRobinFailoverManager(service_name, config)
        elif strategy == FailoverStrategy.WEIGHTED:
            manager = WeightedFailoverManager(service_name, config)
        else:
            # Default to active-passive
            manager = ActivePassiveFailoverManager(service_name, config)
        
        self.failover_managers[service_name] = manager
        logger.info(f"Registered service {service_name} with {strategy} failover strategy")
        
        return manager
    
    def get_service_manager(self, service_name: str) -> Optional[BaseFailoverManager]:
        """
        Get failover manager for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Failover manager or None if not found
        """
        return self.failover_managers.get(service_name)
    
    async def start_monitoring(self) -> None:
        """Start monitoring all services for failover conditions."""
        if self.is_monitoring:
            logger.warning("Failover monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started failover monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop failover monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped failover monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for failover conditions."""
        health_manager = get_health_manager()
        
        while self.is_monitoring:
            try:
                # Check health of all registered services
                for service_name, manager in self.failover_managers.items():
                    current_endpoint = await manager.get_current_endpoint()
                    
                    if not current_endpoint:
                        continue
                    
                    # Get health check result
                    health_result = await health_manager.check_component(current_endpoint.name)
                    
                    if health_result:
                        # Update endpoint health status
                        current_endpoint.is_healthy = health_result.status == HealthStatus.HEALTHY
                        current_endpoint.response_time_ms = health_result.response_time_ms
                        current_endpoint.last_health_check = health_result.timestamp
                        
                        if health_result.status == HealthStatus.HEALTHY:
                            current_endpoint.consecutive_failures = 0
                            current_endpoint.consecutive_successes += 1
                        else:
                            current_endpoint.consecutive_successes = 0
                            current_endpoint.consecutive_failures += 1
                        
                        # Check failover conditions
                        if await manager.check_failover_conditions(current_endpoint, health_result):
                            await manager._trigger_failover(
                                FailoverTrigger.HEALTH_CHECK_FAILURE,
                                f"Health check failed: {health_result.error_message or 'Unknown error'}"
                            )
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in failover monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system-wide failover status."""
        services_status = {}
        total_services = len(self.failover_managers)
        healthy_services = 0
        
        for service_name, manager in self.failover_managers.items():
            status = manager.get_service_status()
            services_status[service_name] = status
            
            if status["healthy_endpoints"] > 0:
                healthy_services += 1
        
        return {
            "is_monitoring": self.is_monitoring,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": total_services - healthy_services,
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def manual_failover(self, service_name: str, target_endpoint: Optional[str] = None) -> bool:
        """
        Manually trigger failover for a service.
        
        Args:
            service_name: Name of service to failover
            target_endpoint: Optional specific endpoint to failover to
            
        Returns:
            True if failover was successful
        """
        manager = self.failover_managers.get(service_name)
        if not manager:
            logger.error(f"Service {service_name} not found for manual failover")
            return False
        
        # If target endpoint specified, temporarily set it as preferred
        if target_endpoint:
            target_ep = None
            for endpoint in manager.endpoints:
                if endpoint.name == target_endpoint:
                    target_ep = endpoint
                    break
            
            if not target_ep:
                logger.error(f"Target endpoint {target_endpoint} not found")
                return False
            
            # Temporarily boost priority for target endpoint
            original_priority = target_ep.priority
            target_ep.priority = 0
            
            try:
                result = await manager._trigger_failover(
                    FailoverTrigger.MANUAL,
                    f"Manual failover to {target_endpoint}"
                )
            finally:
                target_ep.priority = original_priority
            
            return result
        else:
            return await manager._trigger_failover(
                FailoverTrigger.MANUAL,
                "Manual failover requested"
            )


# Global failover orchestrator instance
failover_orchestrator = FailoverOrchestrator()


def get_failover_orchestrator() -> FailoverOrchestrator:
    """Get the global failover orchestrator instance."""
    return failover_orchestrator


async def initialize_failover_system() -> None:
    """Initialize the failover system with default configurations."""
    orchestrator = get_failover_orchestrator()
    
    # Register core services with failover
    
    # Database service (active-passive)
    db_manager = orchestrator.register_service(
        "database",
        FailoverStrategy.ACTIVE_PASSIVE,
        FailoverConfig(
            health_check_failures=2,
            response_time_threshold_ms=3000.0,
            cooldown_period_seconds=180,
            auto_failback=True
        )
    )
    
    # Cache service (active-active with round-robin)
    cache_manager = orchestrator.register_service(
        "cache",
        FailoverStrategy.ROUND_ROBIN,
        FailoverConfig(
            health_check_failures=3,
            response_time_threshold_ms=1000.0,
            cooldown_period_seconds=60,
            auto_failback=True
        )
    )
    
    # External API service (weighted)
    api_manager = orchestrator.register_service(
        "external_apis",
        FailoverStrategy.WEIGHTED,
        FailoverConfig(
            health_check_failures=5,
            response_time_threshold_ms=10000.0,
            error_rate_threshold_percent=15.0,
            cooldown_period_seconds=300,
            auto_failback=False  # Manual failback for external APIs
        )
    )
    
    # Start monitoring
    await orchestrator.start_monitoring()
    logger.info("Failover system initialized")


async def shutdown_failover_system() -> None:
    """Shutdown the failover system."""
    orchestrator = get_failover_orchestrator()
    await orchestrator.stop_monitoring()
    logger.info("Failover system shutdown")