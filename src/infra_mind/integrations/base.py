"""
Base integration framework for third-party services.

This module provides the foundation for all third-party integrations including
authentication, error handling, rate limiting, and monitoring.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class IntegrationStatus(str, Enum):
    """Integration status states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


class IntegrationType(str, Enum):
    """Types of integrations supported."""
    API = "api"
    WEBHOOK = "webhook"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_STORAGE = "file_storage"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    NOTIFICATION = "notification"


@dataclass
class IntegrationMetrics:
    """Metrics for integration monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
    uptime_percentage: float = 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0


@dataclass 
class IntegrationConfig:
    """Configuration for third-party integrations."""
    name: str
    type: IntegrationType
    enabled: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_config: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: int = 300  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "custom_headers": self.custom_headers,
            "custom_config": self.custom_config,
            "health_check_interval": self.health_check_interval
        }


class BaseIntegration(ABC):
    """
    Abstract base class for all third-party integrations.
    
    Provides common functionality for authentication, error handling,
    rate limiting, and monitoring.
    """
    
    def __init__(self, config: IntegrationConfig):
        """Initialize base integration."""
        self.config = config
        self.status = IntegrationStatus.DISCONNECTED
        self.metrics = IntegrationMetrics()
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            config.rate_limit_per_minute,
            config.rate_limit_per_hour
        )
        self._last_health_check = None
        
        logger.info(f"Initialized {config.name} integration ({config.type.value})")
    
    @property
    def is_connected(self) -> bool:
        """Check if integration is connected."""
        return self.status == IntegrationStatus.CONNECTED
    
    @property
    def is_healthy(self) -> bool:
        """Check if integration is healthy."""
        return self.status in [IntegrationStatus.CONNECTED, IntegrationStatus.CONNECTING]
    
    async def connect(self) -> bool:
        """
        Connect to the third-party service.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.config.enabled:
            logger.info(f"Integration {self.config.name} is disabled")
            return False
            
        try:
            self.status = IntegrationStatus.CONNECTING
            logger.info(f"Connecting to {self.config.name}...")
            
            # Create HTTP session if needed
            if self.config.type == IntegrationType.API and not self._session:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers=self.config.custom_headers
                )
            
            # Call integration-specific connection logic
            success = await self._connect()
            
            if success:
                self.status = IntegrationStatus.CONNECTED
                self.metrics.last_success = datetime.now(timezone.utc)
                logger.info(f"Successfully connected to {self.config.name}")
            else:
                self.status = IntegrationStatus.ERROR
                logger.error(f"Failed to connect to {self.config.name}")
            
            return success
            
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.metrics.last_error = str(e)
            logger.error(f"Connection error for {self.config.name}: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the third-party service."""
        try:
            logger.info(f"Disconnecting from {self.config.name}...")
            
            await self._disconnect()
            
            if self._session:
                await self._session.close()
                self._session = None
            
            self.status = IntegrationStatus.DISCONNECTED
            logger.info(f"Disconnected from {self.config.name}")
            
        except Exception as e:
            logger.error(f"Disconnection error for {self.config.name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the integration.
        
        Returns:
            Dict containing health status and metrics
        """
        try:
            self._last_health_check = datetime.now(timezone.utc)
            
            # Call integration-specific health check
            health_data = await self._health_check()
            
            return {
                "name": self.config.name,
                "type": self.config.type.value,
                "status": self.status.value,
                "is_healthy": self.is_healthy,
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "success_rate": self.metrics.success_rate,
                    "average_response_time": self.metrics.average_response_time,
                    "uptime_percentage": self.metrics.uptime_percentage,
                    "last_success": self.metrics.last_success.isoformat() if self.metrics.last_success else None,
                    "last_error": self.metrics.last_error
                },
                "custom_health": health_data,
                "last_check": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check error for {self.config.name}: {e}")
            return {
                "name": self.config.name,
                "status": IntegrationStatus.ERROR.value,
                "is_healthy": False,
                "error": str(e)
            }
    
    @asynccontextmanager
    async def request_context(self):
        """Context manager for tracking requests."""
        start_time = datetime.now(timezone.utc)
        self.metrics.total_requests += 1
        
        try:
            # Check rate limit
            if not await self._rate_limiter.acquire():
                self.status = IntegrationStatus.RATE_LIMITED
                self.metrics.rate_limit_hits += 1
                raise Exception("Rate limit exceeded")
            
            yield
            
            # Request successful
            self.metrics.successful_requests += 1
            self.metrics.last_success = datetime.now(timezone.utc)
            
            if self.status == IntegrationStatus.RATE_LIMITED:
                self.status = IntegrationStatus.CONNECTED
                
        except Exception as e:
            self.metrics.failed_requests += 1
            self.metrics.last_error = str(e)
            
            if "rate limit" in str(e).lower():
                self.status = IntegrationStatus.RATE_LIMITED
            else:
                self.status = IntegrationStatus.ERROR
            
            raise
        finally:
            # Update response time
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._update_response_time(duration)
    
    def _update_response_time(self, duration: float) -> None:
        """Update average response time."""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = duration
        else:
            # Exponential moving average
            self.metrics.average_response_time = (
                0.8 * self.metrics.average_response_time + 0.2 * duration
            )
    
    @abstractmethod
    async def _connect(self) -> bool:
        """Integration-specific connection logic."""
        pass
    
    async def _disconnect(self) -> None:
        """Integration-specific disconnection logic."""
        pass
    
    async def _health_check(self) -> Dict[str, Any]:
        """Integration-specific health check logic."""
        return {"status": "healthy"}
    
    def get_metrics(self) -> IntegrationMetrics:
        """Get integration metrics."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset integration metrics."""
        self.metrics = IntegrationMetrics()


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, per_minute: int, per_hour: int):
        """Initialize rate limiter."""
        self.per_minute = per_minute
        self.per_hour = per_hour
        self.minute_requests = []
        self.hour_requests = []
    
    async def acquire(self) -> bool:
        """
        Try to acquire permission for a request.
        
        Returns:
            bool: True if request allowed, False if rate limited
        """
        now = datetime.now(timezone.utc)
        
        # Clean old requests
        minute_ago = now.timestamp() - 60
        hour_ago = now.timestamp() - 3600
        
        self.minute_requests = [
            req_time for req_time in self.minute_requests 
            if req_time > minute_ago
        ]
        self.hour_requests = [
            req_time for req_time in self.hour_requests 
            if req_time > hour_ago
        ]
        
        # Check limits
        if (len(self.minute_requests) >= self.per_minute or
            len(self.hour_requests) >= self.per_hour):
            return False
        
        # Record request
        request_time = now.timestamp()
        self.minute_requests.append(request_time)
        self.hour_requests.append(request_time)
        
        return True


class IntegrationManager:
    """
    Manager for all third-party integrations.
    
    Handles registration, lifecycle management, and monitoring
    of all integrations in the system.
    """
    
    def __init__(self):
        """Initialize integration manager."""
        self.integrations: Dict[str, BaseIntegration] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        self.health_check_interval = 300  # 5 minutes
        
        logger.info("Integration manager initialized")
    
    def register(self, integration: BaseIntegration) -> None:
        """
        Register an integration.
        
        Args:
            integration: Integration instance to register
        """
        name = integration.config.name
        self.integrations[name] = integration
        logger.info(f"Registered integration: {name}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister an integration.
        
        Args:
            name: Name of integration to unregister
        """
        if name in self.integrations:
            del self.integrations[name]
            logger.info(f"Unregistered integration: {name}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        Connect all registered integrations.
        
        Returns:
            Dict mapping integration names to connection success
        """
        results = {}
        
        for name, integration in self.integrations.items():
            try:
                success = await integration.connect()
                results[name] = success
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        
        return results
    
    async def disconnect_all(self) -> None:
        """Disconnect all integrations."""
        for integration in self.integrations.values():
            try:
                await integration.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {integration.config.name}: {e}")
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all integrations.
        
        Returns:
            Dict mapping integration names to health data
        """
        results = {}
        
        for name, integration in self.integrations.items():
            try:
                health_data = await integration.health_check()
                results[name] = health_data
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = {
                    "name": name,
                    "status": "error",
                    "is_healthy": False,
                    "error": str(e)
                }
        
        return results
    
    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """
        Get integration by name.
        
        Args:
            name: Integration name
            
        Returns:
            Integration instance or None if not found
        """
        return self.integrations.get(name)
    
    def list_integrations(self) -> List[str]:
        """List all registered integration names."""
        return list(self.integrations.keys())
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all integration statuses."""
        total = len(self.integrations)
        connected = sum(1 for i in self.integrations.values() if i.is_connected)
        healthy = sum(1 for i in self.integrations.values() if i.is_healthy)
        
        return {
            "total_integrations": total,
            "connected": connected,
            "healthy": healthy,
            "connection_rate": (connected / total * 100) if total > 0 else 0,
            "health_rate": (healthy / total * 100) if total > 0 else 0,
            "integrations": {
                name: {
                    "status": integration.status.value,
                    "is_connected": integration.is_connected,
                    "is_healthy": integration.is_healthy,
                    "success_rate": integration.metrics.success_rate
                }
                for name, integration in self.integrations.items()
            }
        }
    
    async def start_health_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started integration health monitoring")
    
    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring."""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped integration health monitoring")
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                health_results = await self.health_check_all()
                
                # Log unhealthy integrations
                for name, health in health_results.items():
                    if not health.get("is_healthy", False):
                        logger.warning(f"Integration {name} is unhealthy: {health}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")


# Global integration manager instance
integration_manager = IntegrationManager()