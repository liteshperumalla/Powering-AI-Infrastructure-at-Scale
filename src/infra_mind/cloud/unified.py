"""Unified cloud service interface for Infra Mind.

Provides a single interface for accessing multiple cloud providers with
integrated caching and warming capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone

from .aws import AWSClient
from .azure import AzureClient
from .gcp import GCPClient
from .alibaba import AlibabaCloudClient
from .ibm import IBMCloudClient
from .terraform import TerraformClient
from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, AuthenticationError
)

logger = logging.getLogger(__name__)


# Alias for backward compatibility
UnifiedCloudManager = None  # Will be set after class definition

class UnifiedCloudClient:
    """
    Unified cloud client that provides access to multiple cloud providers.
    
    This client serves as a facade for all supported cloud providers,
    allowing seamless access to services across different clouds.
    """
    
    def __init__(self, aws_region: str = "us-east-1", azure_region: str = "eastus", gcp_region: str = "us-central1",
                 alibaba_region: str = "cn-beijing", ibm_region: str = "us-south",
                 aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None,
                 azure_subscription_id: Optional[str] = None, azure_client_id: Optional[str] = None,
                 azure_client_secret: Optional[str] = None,
                 gcp_project_id: Optional[str] = None, gcp_service_account_path: Optional[str] = None,
                 alibaba_access_key_id: Optional[str] = None, alibaba_access_key_secret: Optional[str] = None,
                 ibm_api_key: Optional[str] = None, ibm_account_id: Optional[str] = None,
                 terraform_token: Optional[str] = None, terraform_organization: Optional[str] = None):
        """
        Initialize the unified cloud client.
        
        Args:
            aws_region: Default AWS region
            azure_region: Default Azure region
            gcp_region: Default GCP region
            aws_access_key_id: AWS access key ID (optional)
            aws_secret_access_key: AWS secret access key (optional)
            azure_subscription_id: Azure subscription ID (optional)
            azure_client_id: Azure client ID (optional)
            azure_client_secret: Azure client secret (optional)
            gcp_project_id: GCP project ID (optional)
            gcp_service_account_path: Path to GCP service account JSON (optional)
            terraform_token: Terraform Cloud API token (optional)
            terraform_organization: Terraform Cloud organization (optional)
        """
        self.clients: Dict[CloudProvider, BaseCloudClient] = {}
        self.provider_regions = {
            CloudProvider.AWS: aws_region,
            CloudProvider.AZURE: azure_region,
            CloudProvider.GCP: gcp_region,
            CloudProvider.ALIBABA: alibaba_region,
            CloudProvider.IBM: ibm_region
        }
        
        # Initialize cloud clients
        try:
            self.clients[CloudProvider.AWS] = AWSClient(
                region=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            logger.info("AWS client initialized successfully")
        except AuthenticationError as e:
            logger.warning(f"AWS client initialization failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS client: {e}")
        
        try:
            self.clients[CloudProvider.AZURE] = AzureClient(
                region=azure_region,
                subscription_id=azure_subscription_id,
                client_id=azure_client_id,
                client_secret=azure_client_secret
            )
            logger.info("Azure client initialized successfully")
        except Exception as e:
            logger.error(f"Unexpected error initializing Azure client: {e}")
        
        try:
            if gcp_project_id:
                self.clients[CloudProvider.GCP] = GCPClient(
                    project_id=gcp_project_id,
                    region=gcp_region,
                    service_account_path=gcp_service_account_path
                )
                logger.info("GCP client initialized successfully")
            else:
                logger.info("GCP project ID not provided, skipping GCP client initialization")
        except Exception as e:
            logger.error(f"Unexpected error initializing GCP client: {e}")
        
        try:
            if alibaba_access_key_id and alibaba_access_key_secret:
                self.clients[CloudProvider.ALIBABA] = AlibabaCloudClient()
                logger.info("Alibaba Cloud client initialized successfully")
            else:
                logger.info("Alibaba Cloud credentials not provided, skipping initialization")
        except Exception as e:
            logger.error(f"Unexpected error initializing Alibaba Cloud client: {e}")
        
        try:
            if ibm_api_key and ibm_account_id:
                self.clients[CloudProvider.IBM] = IBMCloudClient()
                logger.info("IBM Cloud client initialized successfully")
            else:
                logger.info("IBM Cloud credentials not provided, skipping initialization")
        except Exception as e:
            logger.error(f"Unexpected error initializing IBM Cloud client: {e}")
        
        # Initialize Terraform client (always available for registry access)
        try:
            self.terraform_client = TerraformClient(
                terraform_token=terraform_token,
                organization=terraform_organization
            )
            logger.info("Terraform client initialized successfully")
        except Exception as e:
            logger.error(f"Unexpected error initializing Terraform client: {e}")
            self.terraform_client = None
    
    def get_available_providers(self) -> List[CloudProvider]:
        """Get list of available cloud providers."""
        return list(self.clients.keys())
    
    async def get_compute_services(self, provider: Optional[CloudProvider] = None,
                                 region: Optional[str] = None) -> Dict[CloudProvider, CloudServiceResponse]:
        """
        Get compute services from specified provider(s).
        
        Args:
            provider: Specific cloud provider (optional, if None, query all available)
            region: Region to query (optional, if None, use default for provider)
            
        Returns:
            Dictionary mapping providers to their compute service responses
        """
        return await self._get_services_by_category(ServiceCategory.COMPUTE, provider, region)
    
    async def get_storage_services(self, provider: Optional[CloudProvider] = None,
                                 region: Optional[str] = None) -> Dict[CloudProvider, CloudServiceResponse]:
        """
        Get storage services from specified provider(s).
        
        Args:
            provider: Specific cloud provider (optional, if None, query all available)
            region: Region to query (optional, if None, use default for provider)
            
        Returns:
            Dictionary mapping providers to their storage service responses
        """
        return await self._get_services_by_category(ServiceCategory.STORAGE, provider, region)
    
    async def get_database_services(self, provider: Optional[CloudProvider] = None,
                                  region: Optional[str] = None) -> Dict[CloudProvider, CloudServiceResponse]:
        """
        Get database services from specified provider(s).
        
        Args:
            provider: Specific cloud provider (optional, if None, query all available)
            region: Region to query (optional, if None, use default for provider)
            
        Returns:
            Dictionary mapping providers to their database service responses
        """
        return await self._get_services_by_category(ServiceCategory.DATABASE, provider, region)
    
    async def get_ai_services(self, provider: Optional[CloudProvider] = None,
                            region: Optional[str] = None) -> Dict[CloudProvider, CloudServiceResponse]:
        """
        Get AI/ML services from specified provider(s).
        
        Args:
            provider: Specific cloud provider (optional, if None, query all available)
            region: Region to query (optional, if None, use default for provider)
            
        Returns:
            Dictionary mapping providers to their AI/ML service responses
        """
        return await self._get_services_by_category(ServiceCategory.MACHINE_LEARNING, provider, region)
    
    async def _get_services_by_category(self, category: ServiceCategory,
                                      provider: Optional[CloudProvider] = None,
                                      region: Optional[str] = None) -> Dict[CloudProvider, CloudServiceResponse]:
        """
        Get services by category from specified provider(s).
        
        Args:
            category: Service category to query
            provider: Specific cloud provider (optional, if None, query all available)
            region: Region to query (optional, if None, use default for provider)
            
        Returns:
            Dictionary mapping providers to their service responses
        """
        results = {}
        providers = [provider] if provider else self.get_available_providers()
        
        for p in providers:
            if p not in self.clients:
                logger.warning(f"Provider {p} not available")
                continue
            
            client = self.clients[p]
            provider_region = region or self.provider_regions.get(p)
            
            try:
                if category == ServiceCategory.COMPUTE:
                    result = await client.get_compute_services(provider_region)
                elif category == ServiceCategory.STORAGE:
                    result = await client.get_storage_services(provider_region)
                elif category == ServiceCategory.DATABASE:
                    result = await client.get_database_services(provider_region)
                elif category == ServiceCategory.MACHINE_LEARNING:
                    result = await client.get_ai_services(provider_region)
                else:
                    logger.warning(f"Unsupported service category: {category}")
                    continue
                
                results[p] = result
                
            except CloudServiceError as e:
                logger.warning(f"Error getting {category} services from {p}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error getting {category} services from {p}: {e}")
        
        return results
    
    def get_cheapest_service(self, results: Dict[CloudProvider, CloudServiceResponse]) -> Optional[Dict[str, Any]]:
        """
        Find the cheapest service across all providers.
        
        Args:
            results: Dictionary mapping providers to their service responses
            
        Returns:
            Dictionary with provider, service, and price information for the cheapest service
        """
        cheapest_service = None
        cheapest_provider = None
        cheapest_price = float('inf')
        
        for provider, response in results.items():
            service = response.get_cheapest_service()
            if service and service.hourly_price and service.hourly_price < cheapest_price:
                cheapest_service = service
                cheapest_provider = provider
                cheapest_price = service.hourly_price
        
        if cheapest_service and cheapest_provider:
            return {
                "provider": cheapest_provider,
                "service": cheapest_service,
                "hourly_price": cheapest_price,
                "monthly_price": cheapest_service.get_monthly_cost()
            }
        
        return None
    
    def filter_services_by_specs(self, results: Dict[CloudProvider, CloudServiceResponse],
                               **specs) -> Dict[CloudProvider, List[CloudService]]:
        """
        Filter services by specifications across all providers.
        
        Args:
            results: Dictionary mapping providers to their service responses
            **specs: Specifications to filter by (e.g., vcpus=2, memory_gb=4)
            
        Returns:
            Dictionary mapping providers to their filtered services
        """
        filtered_results = {}
        
        for provider, response in results.items():
            filtered = response.filter_by_specs(**specs)
            if filtered:
                filtered_results[provider] = filtered
        
        return filtered_results
    
    def compare_providers(self, results: Dict[CloudProvider, CloudServiceResponse],
                        metric: str = "price") -> Dict[str, Any]:
        """
        Compare providers based on specified metric.
        
        Args:
            results: Dictionary mapping providers to their service responses
            metric: Metric to compare by (price, count, etc.)
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "providers": {},
            "cheapest_provider": None,
            "most_options": None,
            "price_difference": None
        }
        
        cheapest_prices = {}
        service_counts = {}
        
        for provider, response in results.items():
            service_count = len(response.services)
            service_counts[provider] = service_count
            
            cheapest = response.get_cheapest_service()
            if cheapest and cheapest.hourly_price:
                cheapest_prices[provider] = cheapest.hourly_price
            
            comparison["providers"][provider.name] = {
                "service_count": service_count,
                "cheapest_price": cheapest.hourly_price if cheapest else None,
                "cheapest_service": cheapest.service_id if cheapest else None
            }
        
        # Determine cheapest provider
        if cheapest_prices:
            cheapest_provider = min(cheapest_prices.items(), key=lambda x: x[1])[0]
            comparison["cheapest_provider"] = cheapest_provider.name
        
        # Determine provider with most options
        if service_counts:
            most_options_provider = max(service_counts.items(), key=lambda x: x[1])[0]
            comparison["most_options"] = most_options_provider.name
        
        # Calculate price difference if multiple providers
        if len(cheapest_prices) > 1:
            min_price = min(cheapest_prices.values())
            max_price = max(cheapest_prices.values())
            comparison["price_difference"] = {
                "absolute": max_price - min_price,
                "percentage": (max_price - min_price) / min_price * 100 if min_price > 0 else 0
            }
        
        return comparison
    
    async def initialize_cache_warming(self) -> None:
        """Initialize cache warming for all available providers."""
        try:
            from ..core.unified_cloud_cache import get_unified_cache_manager
            from ..core.cache_warming_service import get_cache_warming_service, init_cache_warming_service
            
            # Get unified cache manager
            unified_cache = await get_unified_cache_manager()
            if not unified_cache:
                logger.warning("Unified cache manager not available, skipping cache warming initialization")
                return
            
            # Initialize cache warming service if not already done
            warming_service = await get_cache_warming_service()
            if not warming_service:
                warming_service = await init_cache_warming_service(unified_cache)
            
            # Register fetch functions for all available providers
            fetch_functions = {}
            
            # AWS fetch functions
            if CloudProvider.AWS in self.clients:
                aws_client = self.clients[CloudProvider.AWS]
                fetch_functions.update({
                    "aws_pricing": self._create_fetch_wrapper(aws_client.get_service_pricing, "pricing"),
                    "aws_compute": aws_client.get_compute_services,
                    "aws_storage": aws_client.get_storage_services,
                    "aws_database": aws_client.get_database_services,
                    "aws_ai_ml": aws_client.get_ai_services,
                })
            
            # Azure fetch functions
            if CloudProvider.AZURE in self.clients:
                azure_client = self.clients[CloudProvider.AZURE]
                fetch_functions.update({
                    "azure_pricing": self._create_fetch_wrapper(azure_client.get_service_pricing, "pricing"),
                    "azure_compute": azure_client.get_compute_services,
                    "azure_storage": azure_client.get_storage_services,
                    "azure_database": azure_client.get_database_services,
                    "azure_ai_ml": azure_client.get_ai_services,
                })
            
            # GCP fetch functions
            if CloudProvider.GCP in self.clients:
                gcp_client = self.clients[CloudProvider.GCP]
                fetch_functions.update({
                    "gcp_pricing": self._create_fetch_wrapper(gcp_client.get_service_pricing, "pricing"),
                    "gcp_compute": gcp_client.get_compute_services,
                    "gcp_storage": gcp_client.get_storage_services,
                    "gcp_database": gcp_client.get_database_services,
                    "gcp_ai_ml": gcp_client.get_ai_services,
                })
            
            # Terraform fetch functions
            if self.terraform_client:
                fetch_functions.update({
                    "terraform_terraform_providers": self._create_terraform_providers_wrapper(),
                    "terraform_terraform_modules": self._create_terraform_modules_wrapper(),
                    "terraform_cost_estimation": self._create_terraform_cost_wrapper(),
                })
            
            # Register all fetch functions
            for service_key, fetch_func in fetch_functions.items():
                warming_service.register_fetch_function(service_key, fetch_func)
            
            logger.info(f"Cache warming initialized with {len(fetch_functions)} fetch functions")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache warming: {e}")
    
    def _create_fetch_wrapper(self, pricing_func: Callable, service_type: str) -> Callable:
        """Create a wrapper for pricing functions to match expected signature."""
        async def wrapper(region: str, **kwargs) -> Dict[str, Any]:
            # For pricing functions, we need to provide a service_id
            # This is a simplified approach - in production, you'd want more specific service IDs
            service_id = kwargs.get("service_id", f"{service_type}_service")
            return await pricing_func(service_id, region)
        
        return wrapper
    
    def _create_terraform_providers_wrapper(self) -> Callable:
        """Create wrapper for Terraform providers fetch function."""
        async def wrapper(region: str, **kwargs) -> Dict[str, Any]:
            namespace = kwargs.get("namespace")
            return await self.terraform_client.get_providers(namespace)
        
        return wrapper
    
    def _create_terraform_modules_wrapper(self) -> Callable:
        """Create wrapper for Terraform modules fetch function."""
        async def wrapper(region: str, **kwargs) -> Dict[str, Any]:
            namespace = kwargs.get("namespace")
            provider = kwargs.get("provider")
            return await self.terraform_client.get_modules(namespace, provider)
        
        return wrapper
    
    def _create_terraform_cost_wrapper(self) -> Callable:
        """Create wrapper for Terraform cost estimation fetch function."""
        async def wrapper(region: str, **kwargs) -> Dict[str, Any]:
            service_id = kwargs.get("service_id", "default_run")
            return await self.terraform_client.get_service_pricing(service_id, region)
        
        return wrapper
    
    async def start_cache_warming(self, interval_minutes: int = 30) -> bool:
        """
        Start automatic cache warming for all providers.
        
        Args:
            interval_minutes: Interval between warming cycles
            
        Returns:
            True if warming was started successfully
        """
        try:
            from ..core.cache_warming_service import get_cache_warming_service
            
            warming_service = await get_cache_warming_service()
            if not warming_service:
                logger.error("Cache warming service not initialized")
                return False
            
            await warming_service.start_warming_service(interval_minutes)
            logger.info(f"Cache warming started with {interval_minutes} minute intervals")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start cache warming: {e}")
            return False
    
    async def stop_cache_warming(self) -> bool:
        """
        Stop automatic cache warming.
        
        Returns:
            True if warming was stopped successfully
        """
        try:
            from ..core.cache_warming_service import get_cache_warming_service
            
            warming_service = await get_cache_warming_service()
            if warming_service:
                await warming_service.stop_warming_service()
                logger.info("Cache warming stopped")
                return True
            else:
                logger.warning("Cache warming service not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop cache warming: {e}")
            return False
    
    async def get_cache_status(self) -> Dict[str, Any]:
        """
        Get comprehensive cache status across all providers.
        
        Returns:
            Dictionary with cache status and performance metrics
        """
        try:
            from ..core.unified_cloud_cache import get_unified_cache_manager
            from ..core.cache_warming_service import get_cache_warming_service
            
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "providers": list(self.clients.keys()),
                "terraform_available": self.terraform_client is not None
            }
            
            # Get unified cache status
            unified_cache = await get_unified_cache_manager()
            if unified_cache:
                cache_report = await unified_cache.get_cache_optimization_report()
                status["cache_optimization"] = cache_report
            else:
                status["cache_optimization"] = {"error": "Unified cache manager not available"}
            
            # Get warming service status
            warming_service = await get_cache_warming_service()
            if warming_service:
                warming_status = warming_service.get_warming_status()
                status["cache_warming"] = warming_status
            else:
                status["cache_warming"] = {"error": "Cache warming service not available"}
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def invalidate_cache(self, provider: Optional[str] = None, 
                             service_type: Optional[str] = None,
                             region: Optional[str] = None) -> Dict[str, Any]:
        """
        Invalidate cache entries with optional filtering.
        
        Args:
            provider: Specific provider to invalidate (optional)
            service_type: Specific service type to invalidate (optional)
            region: Specific region to invalidate (optional)
            
        Returns:
            Dictionary with invalidation results
        """
        try:
            from ..core.unified_cloud_cache import get_unified_cache_manager, ServiceType
            
            unified_cache = await get_unified_cache_manager()
            if not unified_cache:
                return {"error": "Unified cache manager not available"}
            
            invalidated_count = 0
            
            if provider and service_type:
                # Invalidate specific service type for provider
                try:
                    service_enum = ServiceType(service_type)
                    invalidated_count = await unified_cache.invalidate_service_cache(
                        provider, service_enum, region
                    )
                except ValueError:
                    return {"error": f"Invalid service type: {service_type}"}
            
            elif provider:
                # Invalidate all cache for provider
                invalidated_count = await unified_cache.invalidate_provider_cache(provider)
            
            else:
                # Invalidate all cache (use with caution)
                for p in self.clients.keys():
                    count = await unified_cache.invalidate_provider_cache(p.value)
                    invalidated_count += count
                
                # Also invalidate Terraform cache
                if self.terraform_client:
                    count = await unified_cache.invalidate_provider_cache("terraform")
                    invalidated_count += count
            
            return {
                "invalidated_entries": invalidated_count,
                "provider": provider,
                "service_type": service_type,
                "region": region,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return {"error": str(e)}
    
    async def warm_cache_manually(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Manually trigger cache warming for specific provider or all providers.
        
        Args:
            provider: Specific provider to warm (optional, if None warm all)
            
        Returns:
            Dictionary with warming results
        """
        try:
            from ..core.cache_warming_service import get_cache_warming_service
            
            warming_service = await get_cache_warming_service()
            if not warming_service:
                return {"error": "Cache warming service not available"}
            
            # Filter schedules by provider if specified
            if provider:
                original_schedules = warming_service.warming_schedules.copy()
                warming_service.warming_schedules = [
                    s for s in warming_service.warming_schedules if s.provider == provider
                ]
            
            # Run warming cycle
            results = await warming_service.run_warming_cycle()
            
            # Restore original schedules if filtered
            if provider:
                warming_service.warming_schedules = original_schedules
            
            return {
                "manual_warming": True,
                "provider_filter": provider,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual cache warming: {e}")
            return {"error": str(e)}


# Set the alias for backward compatibility
UnifiedCloudManager = UnifiedCloudClient