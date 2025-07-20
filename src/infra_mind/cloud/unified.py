"""Unified cloud service interface for Infra Mind.

Provides a single interface for accessing multiple cloud providers.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from .aws import AWSClient
from .azure import AzureClient
from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, AuthenticationError
)

logger = logging.getLogger(__name__)


class UnifiedCloudClient:
    """
    Unified cloud client that provides access to multiple cloud providers.
    
    This client serves as a facade for all supported cloud providers,
    allowing seamless access to services across different clouds.
    """
    
    def __init__(self, aws_region: str = "us-east-1", azure_region: str = "eastus",
                 aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None,
                 azure_subscription_id: Optional[str] = None, azure_client_id: Optional[str] = None,
                 azure_client_secret: Optional[str] = None):
        """
        Initialize the unified cloud client.
        
        Args:
            aws_region: Default AWS region
            azure_region: Default Azure region
            aws_access_key_id: AWS access key ID (optional)
            aws_secret_access_key: AWS secret access key (optional)
            azure_subscription_id: Azure subscription ID (optional)
            azure_client_id: Azure client ID (optional)
            azure_client_secret: Azure client secret (optional)
        """
        self.clients: Dict[CloudProvider, BaseCloudClient] = {}
        self.provider_regions = {
            CloudProvider.AWS: aws_region,
            CloudProvider.AZURE: azure_region
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