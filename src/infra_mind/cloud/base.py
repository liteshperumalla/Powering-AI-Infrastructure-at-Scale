"""
Base classes for cloud service integration.

Defines common interfaces and data structures for cloud providers.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALIBABA = "alibaba"
    IBM = "ibm"


class ServiceCategory(str, Enum):
    """Cloud service categories."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    SECURITY = "security"
    ANALYTICS = "analytics"
    MACHINE_LEARNING = "machine_learning"
    SERVERLESS = "serverless"
    CONTAINERS = "containers"
    MONITORING = "monitoring"
    CONTAINER = "container"  # For Kubernetes services
    AI_ML = "ai_ml"  # For AI/ML services
    MANAGEMENT = "management"  # For resource management
    DEVELOPER_TOOLS = "developer_tools"  # For DevOps services
    BACKUP = "backup"  # For backup services
    DISASTER_RECOVERY = "disaster_recovery"  # For disaster recovery


@dataclass
class CloudService:
    """Represents a cloud service offering."""
    provider: CloudProvider
    service_name: str
    service_id: str
    category: ServiceCategory
    region: str
    description: str = ""
    pricing_model: str = "pay_as_you_go"
    
    # Pricing information
    hourly_price: Optional[float] = None
    monthly_price: Optional[float] = None
    pricing_unit: str = "hour"
    currency: str = "USD"
    
    # Service specifications
    specifications: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    
    # Metadata
    availability: str = "general"  # general, preview, deprecated
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_monthly_cost(self, usage_hours: float = 730) -> Optional[float]:
        """Calculate monthly cost based on hourly pricing."""
        if self.hourly_price is not None:
            return self.hourly_price * usage_hours
        return self.monthly_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "provider": self.provider.value,
            "service_name": self.service_name,
            "service_id": self.service_id,
            "category": self.category.value,
            "region": self.region,
            "description": self.description,
            "pricing_model": self.pricing_model,
            "hourly_price": self.hourly_price,
            "monthly_price": self.monthly_price,
            "pricing_unit": self.pricing_unit,
            "currency": self.currency,
            "specifications": self.specifications,
            "features": self.features,
            "availability": self.availability,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class CloudServiceResponse:
    """Response from cloud service API calls."""
    provider: CloudProvider
    service_category: ServiceCategory
    region: str
    services: List[CloudService] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_cheapest_service(self) -> Optional[CloudService]:
        """Get the cheapest service from the response."""
        if not self.services:
            return None
        
        services_with_pricing = [s for s in self.services if s.hourly_price is not None]
        if not services_with_pricing:
            return None
        
        return min(services_with_pricing, key=lambda s: s.hourly_price)
    
    def filter_by_specs(self, **specs) -> List[CloudService]:
        """Filter services by specifications."""
        filtered = []
        for service in self.services:
            match = True
            for key, value in specs.items():
                if key not in service.specifications or service.specifications[key] != value:
                    match = False
                    break
            if match:
                filtered.append(service)
        return filtered


class BaseCloudClient(ABC):
    """
    Base class for cloud provider clients.
    
    Learning Note: This abstract base class ensures all cloud provider
    clients implement the same interface for consistency.
    """
    
    def __init__(self, provider: CloudProvider, region: str = "us-east-1"):
        """
        Initialize the cloud client.
        
        Args:
            provider: Cloud provider
            region: Default region for API calls
        """
        self.provider = provider
        self.region = region
        self.api_call_count = 0
        self.last_error: Optional[str] = None
        self.cache_enabled = True
    
    @abstractmethod
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get available compute services."""
        pass
    
    @abstractmethod
    async def get_storage_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get available storage services."""
        pass
    
    @abstractmethod
    async def get_database_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get available database services."""
        pass
    
    @abstractmethod
    async def get_ai_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get available AI/ML services."""
        pass
    
    @abstractmethod
    async def get_service_pricing(self, service_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing information for a specific service."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the client."""
        return {
            "provider": self.provider.value,
            "region": self.region,
            "api_calls_made": self.api_call_count,
            "last_error": self.last_error,
            "status": "healthy" if not self.last_error else "error"
        }
    
    def _increment_api_calls(self) -> None:
        """Increment API call counter."""
        self.api_call_count += 1
    
    def _set_last_error(self, error: str) -> None:
        """Set the last error message."""
        self.last_error = error
        logger.error(f"{self.provider.value} client error: {error}")
    
    async def _get_cached_or_fetch(self, service: str, region: str, 
                                   fetch_func, params: Optional[Dict[str, Any]] = None,
                                   cache_ttl: int = 3600) -> Any:
        """
        Get data from cache or fetch from API with unified cloud caching and resilience patterns.
        
        Args:
            service: Service name for caching
            region: Cloud region
            fetch_func: Function to fetch data from API
            params: Additional parameters for caching key
            cache_ttl: Cache TTL in seconds (deprecated, now determined by service type)
            
        Returns:
            Data from cache or API with resilience metadata
        """
        from ..core.unified_cloud_cache import get_unified_cache_manager, ServiceType
        from ..core.resilience import resilience_manager
        from ..core.advanced_rate_limiter import advanced_rate_limiter, RateLimitExceeded
        from ..core.cache import rate_limiter as legacy_rate_limiter, cache_manager as legacy_cache_manager
        
        import inspect

        async def _execute_fetch_direct():
            """Execute fetch_func handling sync/async callables."""
            result = fetch_func()
            if inspect.iscoroutine(result):
                return await result
            if inspect.iscoroutinefunction(fetch_func):
                return await fetch_func()
            return result

        if not self.cache_enabled:
            return await _execute_fetch_direct()
        
        # Get unified cache manager
        unified_cache = await get_unified_cache_manager()
        if not unified_cache:
            logger.warning("Unified cache manager not available, calling API directly")
            if legacy_rate_limiter:
                try:
                    status = await legacy_rate_limiter.check_rate_limit(self.provider.value, service)
                except Exception as exc:
                    logger.warning(f"Legacy rate limiter check failed: {exc}")
                else:
                    if status and not status.get("allowed", True):
                        if hasattr(legacy_cache_manager, "get"):
                            stale_data = await legacy_cache_manager.get(
                                self.provider.value,
                                service,
                                region
                            )
                            if stale_data:
                                stale_data["rate_limited"] = True
                                stale_data["is_stale"] = True
                                stale_data["retry_after"] = status.get("reset_time")
                                return stale_data
            return await _execute_fetch_direct()
        
        # Map service names to ServiceType enum
        service_type_mapping = {
            "pricing": ServiceType.PRICING,
            "compute": ServiceType.COMPUTE,
            "storage": ServiceType.STORAGE,
            "database": ServiceType.DATABASE,
            "ai": ServiceType.AI_ML,
            "ai_services": ServiceType.AI_ML,
            "ml": ServiceType.AI_ML,
            "cost_estimation": ServiceType.COST_ESTIMATION,
            "compliance": ServiceType.COMPLIANCE,
            "regions": ServiceType.REGIONS,
            "compute_modules": ServiceType.TERRAFORM_MODULES,
            "storage_modules": ServiceType.TERRAFORM_MODULES,
            "database_modules": ServiceType.TERRAFORM_MODULES,
            "ai_modules": ServiceType.TERRAFORM_MODULES,
            "modules": ServiceType.TERRAFORM_MODULES,
            "providers": ServiceType.TERRAFORM_PROVIDERS,
        }
        
        service_type = service_type_mapping.get(service, ServiceType.COMPUTE)
        
        # Generate service name for resilience patterns
        service_name = f"{self.provider.value}_{service}"
        fallback_key = f"{self.provider.value}:{service}:{region}"
        
        # Try to get from unified cache first
        try:
            cached_data = await unified_cache.get_cached_data(
                provider=self.provider.value,
                service_type=service_type,
                region=region,
                params=params,
                allow_stale=False
            )
            
            if cached_data:
                logger.debug(f"Cache hit for {self.provider.value}:{service}:{region}")
                # Add provider metadata
                cached_data["provider"] = self.provider.value
                cached_data["service"] = service
                cached_data["region"] = region
                cached_data["cache_source"] = "unified_cache"
                return cached_data
        
        except Exception as e:
            logger.warning(f"Error accessing unified cache: {e}")
        
        # Respect legacy cache rate limiter if configured
        legacy_rate_status = None
        if legacy_rate_limiter:
            try:
                legacy_rate_status = await legacy_rate_limiter.check_rate_limit(self.provider.value, service)
            except Exception as exc:
                logger.warning(f"Legacy rate limiter check failed: {exc}")
                legacy_rate_status = None

            if legacy_rate_status and not legacy_rate_status.get("allowed", True):
                if unified_cache:
                    stale_data = await unified_cache.get_cached_data(
                        provider=self.provider.value,
                        service_type=service_type,
                        region=region,
                        params=params,
                        allow_stale=True
                    )
                    if stale_data:
                        stale_data["rate_limited"] = True
                        stale_data["is_stale"] = True
                        stale_data["retry_after"] = legacy_rate_status.get("reset_time")
                        return stale_data
                elif legacy_cache_manager and hasattr(legacy_cache_manager, "get"):
                    stale_data = await legacy_cache_manager.get(
                        self.provider.value,
                        service,
                        region
                    )
                    if stale_data:
                        stale_data["rate_limited"] = True
                        stale_data["is_stale"] = True
                        stale_data["retry_after"] = legacy_rate_status.get("reset_time")
                        return stale_data

        # Use resilience manager for comprehensive error handling
        try:
            from ..core.resilience import resilience_manager
            
            async with resilience_manager.resilient_call(
                service_name=service_name,
                fallback_key=fallback_key,
                cache_manager=unified_cache.cache_manager if unified_cache else None
            ) as resilient_execute:
                
                async def fetch_with_rate_limiting():
                    """Fetch data with rate limiting check."""
                    # Check advanced rate limits if available
                    if advanced_rate_limiter:
                        try:
                            await advanced_rate_limiter.check_rate_limit(service_name)
                        except RateLimitExceeded as e:
                            logger.warning(f"Advanced rate limit exceeded: {e}")
                            
                            # Try to get stale cached data from unified cache
                            if unified_cache:
                                stale_data = await unified_cache.get_cached_data(
                                    provider=self.provider.value,
                                    service_type=service_type,
                                    region=region,
                                    params=params,
                                    allow_stale=True
                                )
                                
                                if stale_data:
                                    stale_data["rate_limited"] = True
                                    stale_data["is_stale"] = True
                                    stale_data["retry_after"] = e.retry_after
                                    return stale_data
                            
                            raise
                    
                    # Fetch fresh data from API
                    logger.info(f"Fetching fresh data for {self.provider.value}:{service}:{region}")
                    import inspect
                    import asyncio

                    result = fetch_func()
                    if inspect.iscoroutine(result):
                        fresh_data = await result
                    elif inspect.iscoroutinefunction(fetch_func):
                        fresh_data = await fetch_func()
                    else:
                        fresh_data = result
                    
                    # Cache the fresh data using unified cache
                    if unified_cache:
                        await unified_cache.set_cached_data(
                            provider=self.provider.value,
                            service_type=service_type,
                            region=region,
                            data=fresh_data,
                            params=params,
                            tags=[f"api_call:{datetime.now(timezone.utc).isoformat()}"]
                        )
                    
                    self._increment_api_calls()
                    return fresh_data
                
                # Execute with full resilience patterns
                result = await resilient_execute(fetch_with_rate_limiting)
                
                # Add provider metadata to result
                if isinstance(result.get("data"), dict):
                    result["data"]["provider"] = self.provider.value
                    result["data"]["service"] = service
                    result["data"]["region"] = region
                    result["data"]["resilience_metadata"] = {
                        "source": result["source"],
                        "fallback_used": result["fallback_used"],
                        "degraded_mode": result["degraded_mode"],
                        "warnings": result["warnings"]
                    }
                
                return result["data"]
        
        except ImportError:
            # Fallback if resilience manager not available
            logger.warning("Resilience manager not available, using simple caching")
            
            # Simple fetch and cache
            try:
                fresh_data = await fetch_func()
                
                if unified_cache:
                    await unified_cache.set_cached_data(
                        provider=self.provider.value,
                        service_type=service_type,
                        region=region,
                        data=fresh_data,
                        params=params
                    )
                
                self._increment_api_calls()
                return fresh_data
                
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                
                # Try to get stale data as last resort
                if unified_cache:
                    stale_data = await unified_cache.get_cached_data(
                        provider=self.provider.value,
                        service_type=service_type,
                        region=region,
                        params=params,
                        allow_stale=True
                    )
                    
                    if stale_data:
                        stale_data["error_fallback"] = True
                        stale_data["error"] = str(e)
                        return stale_data
                
                raise


class CloudServiceError(Exception):
    """Base exception for cloud service errors."""
    
    def __init__(self, message: str, provider: CloudProvider, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class RateLimitError(CloudServiceError):
    """Exception for rate limiting errors."""
    pass


class AuthenticationError(CloudServiceError):
    """Exception for authentication errors."""
    pass


class ServiceUnavailableError(CloudServiceError):
    """Exception for service unavailability."""
    pass
