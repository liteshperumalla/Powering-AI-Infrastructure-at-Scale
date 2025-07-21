"""
Azure cloud service integration for Infra Mind.

Provides clients for Azure Retail Prices API, Compute, SQL Database, and other services.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx

from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, RateLimitError, AuthenticationError
)

logger = logging.getLogger(__name__)


class AzureClient(BaseCloudClient):
    """
    Main Azure client that coordinates other Azure service clients.
    
    Learning Note: This acts as a facade for various Azure services,
    providing a unified interface for Azure operations.
    """
    
    def __init__(self, region: str = "eastus", subscription_id: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize Azure client.
        
        Args:
            region: Azure region
            subscription_id: Azure subscription ID (optional for pricing API)
            client_id: Azure client ID (optional for pricing API)
            client_secret: Azure client secret (optional for pricing API)
        """
        super().__init__(CloudProvider.AZURE, region)
        
        # Initialize service clients
        self.pricing_client = AzurePricingClient(region)
        self.compute_client = AzureComputeClient(region, subscription_id, client_id, client_secret)
        self.sql_client = AzureSQLClient(region, subscription_id, client_id, client_secret)
        self.ai_client = AzureAIClient(region, subscription_id, client_id, client_secret)
    
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Azure compute services (Virtual Machines)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="compute",
            region=target_region,
            fetch_func=lambda: self.compute_client.get_vm_sizes(target_region),
            cache_ttl=3600  # 1 hour cache for compute services
        )
    
    async def get_storage_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """
        Get Azure storage services using real pricing data.
        
        Args:
            region: Azure region
            
        Returns:
            CloudServiceResponse with Azure storage services
            
        Raises:
            CloudServiceError: If unable to fetch real pricing data
        """
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="storage",
            region=target_region,
            fetch_func=lambda: self._fetch_storage_services(target_region),
            cache_ttl=3600  # 1 hour cache for storage services
        )
    
    async def _fetch_storage_services(self, region: str) -> CloudServiceResponse:
        """Fetch storage services from Azure APIs."""
        try:
            # Get real pricing data for Storage services
            pricing_data = await self.pricing_client.get_service_pricing("Storage", region)
            
            if not pricing_data.get("real_data") or not pricing_data.get("processed_pricing"):
                raise CloudServiceError(
                    f"Failed to get real pricing data for Storage in {region}",
                    CloudProvider.AZURE,
                    "NO_REAL_PRICING"
                )
            
            return await self._get_storage_services_with_real_pricing(
                region, 
                pricing_data["processed_pricing"]
            )
            
        except CloudServiceError:
            raise
        except Exception as e:
            raise CloudServiceError(
                f"Azure Storage API error: {str(e)}",
                CloudProvider.AZURE,
                "STORAGE_API_ERROR"
            )
    
    async def _get_storage_services_with_real_pricing(self, region: str, pricing_data: Dict[str, Dict[str, Any]]) -> CloudServiceResponse:
        """Get storage services with real pricing data from Azure API."""
        services = []
        
        # Storage service specifications
        storage_specs = {
            "blob": {
                "service_name": "Azure Blob Storage",
                "description": "Object storage service for unstructured data",
                "specifications": {"storage_type": "blob", "redundancy": "LRS", "durability": "99.999999999%"},
                "features": ["versioning", "encryption", "lifecycle_management", "cdn_integration"]
            },
            "disk": {
                "service_name": "Azure Managed Disks",
                "description": "High-performance SSD storage for VMs",
                "specifications": {"disk_type": "Premium_LRS", "iops": 5000, "throughput": 200},
                "features": ["encryption", "snapshots", "backup", "high_iops"]
            }
        }
        
        # Match pricing data with storage specifications
        for storage_name, pricing_info in pricing_data.items():
            # Determine storage type
            storage_type = "blob"
            if "disk" in storage_name.lower() or "managed" in storage_name.lower():
                storage_type = "disk"
            
            spec = storage_specs.get(storage_type, storage_specs["blob"])
            
            service = CloudService(
                provider=CloudProvider.AZURE,
                service_name=spec["service_name"],
                service_id=storage_name,
                category=ServiceCategory.STORAGE,
                region=region,
                description=spec["description"],
                pricing_model="pay_as_you_go",
                hourly_price=pricing_info["hourly"],
                pricing_unit=pricing_info["unit"],
                specifications=spec["specifications"],
                features=spec["features"]
            )
            services.append(service)
        
        if not services:
            raise CloudServiceError(
                f"No Storage pricing matches found for region {region}. Available services: {list(pricing_data.keys())}",
                CloudProvider.AZURE,
                "NO_STORAGE_MATCHES"
            )
        
        return CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.STORAGE,
            region=region,
            services=services,
            metadata={"real_pricing": True, "pricing_source": "azure_retail_api"}
        )
    
    async def get_database_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Azure database services (SQL Database)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="sql",
            region=target_region,
            fetch_func=lambda: self.sql_client.get_database_services(target_region),
            cache_ttl=3600  # 1 hour cache for database services
        )
    
    async def get_ai_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Azure AI/ML services."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="ai",
            region=target_region,
            fetch_func=lambda: self.ai_client.get_ai_services(target_region),
            cache_ttl=3600  # 1 hour cache for AI services
        )
    
    async def get_service_pricing(self, service_name: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing for a specific Azure service."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="pricing",
            region=target_region,
            fetch_func=lambda: self.pricing_client.get_service_pricing(service_name, target_region),
            params={"service_name": service_name},
            cache_ttl=3600  # 1 hour cache for pricing data
        )


class AzurePricingClient:
    """
    Azure Retail Prices API client.
    
    Learning Note: The Azure Retail Prices API is a public API that provides
    pricing information for Azure services without requiring authentication.
    """
    
    def __init__(self, region: str = "eastus"):
        self.region = region
        self.base_url = "https://prices.azure.com/api/retail/prices"
        self.session = None
    
    async def get_service_pricing(self, service_name: str, region: str) -> Dict[str, Any]:
        """
        Get pricing information for an Azure service using real API data only.
        
        Args:
            service_name: Azure service name (e.g., 'Virtual Machines', 'SQL Database')
            region: Azure region
            
        Returns:
            Pricing information dictionary
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            async with httpx.AsyncClient() as client:
                # Build query parameters
                params = {
                    "api-version": "2023-01-01-preview",
                    "$filter": f"serviceName eq '{service_name}' and armRegionName eq '{region}'",
                    "$top": 1000  # Increased to get more comprehensive data
                }
                
                response = await client.get(self.base_url, params=params, timeout=60.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Process real API data into structured format
                    processed_pricing = self._process_real_pricing_data(data.get("Items", []))
                    
                    if not processed_pricing:
                        raise CloudServiceError(
                            f"No valid pricing data found for {service_name} in {region}",
                            CloudProvider.AZURE,
                            "NO_PRICING_DATA"
                        )
                    
                    return {
                        "service_name": service_name,
                        "region": region,
                        "items": data.get("Items", []),
                        "processed_pricing": processed_pricing,
                        "next_page_link": data.get("NextPageLink"),
                        "count": data.get("Count", 0),
                        "real_data": True
                    }
                else:
                    raise CloudServiceError(
                        f"Azure Pricing API returned status {response.status_code}",
                        CloudProvider.AZURE,
                        f"HTTP_{response.status_code}"
                    )
                    
        except httpx.TimeoutException:
            raise CloudServiceError(
                f"Azure Pricing API timeout for {service_name} in {region}",
                CloudProvider.AZURE,
                "API_TIMEOUT"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Azure Pricing API error: {str(e)}",
                CloudProvider.AZURE,
                "API_ERROR"
            )
    
    def _process_real_pricing_data(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Process real Azure pricing data into structured format."""
        processed = {}
        
        for item in items:
            sku_name = item.get("skuName", "")
            product_name = item.get("productName", "")
            retail_price = item.get("retailPrice", 0)
            unit_of_measure = item.get("unitOfMeasure", "")
            
            # Skip if no price or invalid data
            if not retail_price or not sku_name:
                continue
            
            # Skip obviously incorrect pricing (likely errors in API data)
            # Most VM instances should be under $100/hour for standard usage
            if retail_price > 100:
                logger.warning(f"Skipping {sku_name} with unusually high price: ${retail_price}/hour")
                continue
            
            # Create a clean key for the service
            if "Virtual Machines" in product_name:
                # Extract VM size from SKU name
                key = sku_name.replace(" Low Priority", "").replace(" Spot", "").strip()
                if key and "Standard_" in key:
                    # Skip if we already have this VM (prefer regular over spot pricing)
                    if key not in processed or "Low Priority" not in sku_name:
                        processed[key] = {
                            "hourly": retail_price,
                            "monthly": retail_price * 730,  # Approximate monthly hours
                            "unit": unit_of_measure,
                            "product": product_name,
                            "is_spot": "Low Priority" in sku_name or "Spot" in sku_name
                        }
            elif "SQL Database" in product_name:
                # Process SQL Database pricing
                key = sku_name.strip()
                if key and retail_price < 50:  # Reasonable limit for SQL Database
                    processed[key] = {
                        "hourly": retail_price,
                        "monthly": retail_price * 730,
                        "unit": unit_of_measure,
                        "product": product_name
                    }
        
        return processed
    
    async def get_all_service_pricing(self, service_name: str, region: str) -> Dict[str, Any]:
        """
        Get comprehensive pricing information by fetching multiple pages.
        
        Args:
            service_name: Azure service name
            region: Azure region
            
        Returns:
            Complete pricing information dictionary
        """
        all_items = []
        next_link = None
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    if next_link:
                        response = await client.get(next_link, timeout=60.0)
                    else:
                        params = {
                            "api-version": "2023-01-01-preview",
                            "$filter": f"serviceName eq '{service_name}' and armRegionName eq '{region}'",
                            "$top": 1000
                        }
                        response = await client.get(self.base_url, params=params, timeout=60.0)
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    all_items.extend(data.get("Items", []))
                    
                    next_link = data.get("NextPageLink")
                    if not next_link:
                        break
                
                # Process all collected data
                processed_pricing = self._process_real_pricing_data(all_items)
                
                return {
                    "service_name": service_name,
                    "region": region,
                    "items": all_items,
                    "processed_pricing": processed_pricing,
                    "count": len(all_items),
                    "real_data": True
                }
                
        except Exception as e:
            raise CloudServiceError(
                f"Failed to fetch comprehensive pricing data: {str(e)}",
                CloudProvider.AZURE,
                "COMPREHENSIVE_FETCH_ERROR"
            )


class AzureComputeClient:
    """
    Azure Compute service client.
    
    Learning Note: Azure Compute provides virtual machines and related services.
    This client provides access to VM sizes, pricing, and availability information.
    """
    
    def __init__(self, region: str = "eastus", subscription_id: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.region = region
        self.subscription_id = subscription_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # For now, we'll use mock data since Azure SDK requires complex authentication
        # In production, this would use azure-mgmt-compute with proper authentication
        self.use_mock_data = True
    
    async def get_vm_sizes(self, region: str) -> CloudServiceResponse:
        """
        Get available Azure VM sizes using real pricing data only.
        
        Args:
            region: Azure region
            
        Returns:
            CloudServiceResponse with Azure VM sizes
            
        Raises:
            CloudServiceError: If unable to fetch real pricing data
        """
        try:
            # Get real pricing data
            pricing_client = AzurePricingClient(region)
            pricing_data = await pricing_client.get_service_pricing("Virtual Machines", region)
            
            if not pricing_data.get("real_data") or not pricing_data.get("processed_pricing"):
                raise CloudServiceError(
                    f"Failed to get real pricing data for Virtual Machines in {region}",
                    CloudProvider.AZURE,
                    "NO_REAL_PRICING"
                )
            
            # Use real pricing data
            return await self._get_vm_sizes_with_real_pricing(region, pricing_data["processed_pricing"])
                
        except CloudServiceError:
            raise
        except Exception as e:
            raise CloudServiceError(
                f"Azure Compute API error: {str(e)}",
                CloudProvider.AZURE,
                "COMPUTE_API_ERROR"
            )
    
    async def _get_vm_sizes_with_real_pricing(self, region: str, pricing_data: Dict[str, Dict[str, float]]) -> CloudServiceResponse:
        """Get VM sizes with real pricing data from Azure API."""
        services = []
        
        # Expanded VM specifications to match more real Azure VMs
        vm_specs = self._get_azure_vm_specifications()
        
        # Match pricing data with VM specifications
        for vm_name, pricing_info in pricing_data.items():
            if vm_name in vm_specs:
                specs = vm_specs[vm_name]
                
                service = CloudService(
                    provider=CloudProvider.AZURE,
                    service_name=f"Azure VM {vm_name}",
                    service_id=vm_name,
                    category=ServiceCategory.COMPUTE,
                    region=region,
                    description=f"Azure virtual machine {vm_name} with real-time pricing",
                    hourly_price=pricing_info["hourly"],
                    specifications={
                        "vcpus": specs["vcpus"],
                        "memory_gb": specs["memory_gb"],
                        "os_disk_size_gb": specs["os_disk_size_gb"],
                        "max_data_disks": specs["max_data_disks"],
                        "vm_generation": "V1"
                    },
                    features=["premium_storage", "accelerated_networking", "nested_virtualization"]
                )
                services.append(service)
        
        # If no matches found, raise error instead of falling back to mock data
        if not services:
            raise CloudServiceError(
                f"No VM pricing matches found for region {region}. Available VMs: {list(pricing_data.keys())}",
                CloudProvider.AZURE,
                "NO_VM_MATCHES"
            )
        
        return CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.COMPUTE,
            region=region,
            services=services,
            metadata={"real_pricing": True, "pricing_source": "azure_retail_api"}
        )
    
    def _get_azure_vm_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Get Azure VM specifications for common VM sizes."""
        return {
            # B-series (Burstable)
            "Standard_B1s": {"vcpus": 1, "memory_gb": 1, "os_disk_size_gb": 4, "max_data_disks": 2},
            "Standard_B1ms": {"vcpus": 1, "memory_gb": 2, "os_disk_size_gb": 4, "max_data_disks": 2},
            "Standard_B2s": {"vcpus": 2, "memory_gb": 4, "os_disk_size_gb": 8, "max_data_disks": 4},
            "Standard_B2ms": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_B4ms": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            
            # D-series v3 (General Purpose)
            "Standard_D2s_v3": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_D4s_v3": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_D8s_v3": {"vcpus": 8, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 16},
            "Standard_D16s_v3": {"vcpus": 16, "memory_gb": 64, "os_disk_size_gb": 128, "max_data_disks": 32},
            
            # D-series v4 (General Purpose)
            "Standard_D2s_v4": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_D4s_v4": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_D8s_v4": {"vcpus": 8, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 16},
            
            # D-series v5 (General Purpose)
            "Standard_D2_v5": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_D4_v5": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_D8_v5": {"vcpus": 8, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 16},
            "Standard_D2s_v5": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_D4s_v5": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_D2ds_v5": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_D4ds_v5": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            
            # E-series v3 (Memory Optimized)
            "Standard_E2s_v3": {"vcpus": 2, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 4},
            "Standard_E4s_v3": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            "Standard_E8s_v3": {"vcpus": 8, "memory_gb": 64, "os_disk_size_gb": 128, "max_data_disks": 16},
            
            # E-series v4 (Memory Optimized)
            "Standard_E2s_v4": {"vcpus": 2, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 4},
            "Standard_E4s_v4": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            "Standard_E8s_v4": {"vcpus": 8, "memory_gb": 64, "os_disk_size_gb": 128, "max_data_disks": 16},
            
            # E-series v5 (Memory Optimized)
            "Standard_E2_v5": {"vcpus": 2, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 4},
            "Standard_E4_v5": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            "Standard_E2s_v5": {"vcpus": 2, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 4},
            "Standard_E4s_v5": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            "Standard_E2ds_v5": {"vcpus": 2, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 4},
            "Standard_E4ds_v5": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            "Standard_E4pds_v5": {"vcpus": 4, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 8},
            
            # F-series v2 (Compute Optimized)
            "Standard_F2s_v2": {"vcpus": 2, "memory_gb": 4, "os_disk_size_gb": 16, "max_data_disks": 4},
            "Standard_F4s_v2": {"vcpus": 4, "memory_gb": 8, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_F8s_v2": {"vcpus": 8, "memory_gb": 16, "os_disk_size_gb": 64, "max_data_disks": 16},
            
            # A-series (Basic)
            "Standard_A1_v2": {"vcpus": 1, "memory_gb": 2, "os_disk_size_gb": 10, "max_data_disks": 2},
            "Standard_A2_v2": {"vcpus": 2, "memory_gb": 4, "os_disk_size_gb": 20, "max_data_disks": 4},
            "Standard_A4_v2": {"vcpus": 4, "memory_gb": 8, "os_disk_size_gb": 40, "max_data_disks": 8},
            
            # DC-series (Confidential Computing)
            "Standard_DC2s_v2": {"vcpus": 2, "memory_gb": 8, "os_disk_size_gb": 100, "max_data_disks": 2},
            "Standard_DC4s_v2": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 200, "max_data_disks": 4},
            "Standard_DC4as_cc_v5": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 200, "max_data_disks": 4},
            
            # Dads-series (AMD)
            "Standard_D4ads_v5": {"vcpus": 4, "memory_gb": 16, "os_disk_size_gb": 32, "max_data_disks": 8},
            "Standard_D8ads_v5": {"vcpus": 8, "memory_gb": 32, "os_disk_size_gb": 64, "max_data_disks": 16},
        }
    



class AzureSQLClient:
    """
    Azure SQL Database service client.
    
    Learning Note: Azure SQL Database provides managed database services
    with different service tiers (Basic, Standard, Premium).
    """
    
    def __init__(self, region: str = "eastus", subscription_id: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.region = region
        self.subscription_id = subscription_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # For now, we'll use mock data since Azure SDK requires complex authentication
        # In production, this would use azure-mgmt-sql with proper authentication
        self.use_mock_data = True
    
    async def get_database_services(self, region: str) -> CloudServiceResponse:
        """
        Get available Azure SQL Database services using real pricing data.
        
        Args:
            region: Azure region
            
        Returns:
            CloudServiceResponse with Azure SQL Database services
            
        Raises:
            CloudServiceError: If unable to fetch real pricing data
        """
        try:
            # Get real pricing data for SQL Database
            pricing_client = AzurePricingClient(region)
            pricing_data = await pricing_client.get_service_pricing("SQL Database", region)
            
            if not pricing_data.get("real_data") or not pricing_data.get("processed_pricing"):
                raise CloudServiceError(
                    f"Failed to get real pricing data for SQL Database in {region}",
                    CloudProvider.AZURE,
                    "NO_REAL_PRICING"
                )
            
            return await self._get_sql_services_with_real_pricing(region, pricing_data["processed_pricing"])
                
        except CloudServiceError:
            raise
        except Exception as e:
            raise CloudServiceError(
                f"Azure SQL API error: {str(e)}",
                CloudProvider.AZURE,
                "SQL_API_ERROR"
            )
    
    async def _get_sql_services_with_real_pricing(self, region: str, pricing_data: Dict[str, Dict[str, Any]]) -> CloudServiceResponse:
        """Get SQL Database services with real pricing data from Azure API."""
        services = []
        
        # SQL Database tier specifications (based on Azure documentation)
        sql_specs = self._get_sql_database_specifications()
        
        # Match pricing data with SQL specifications
        for sql_name, pricing_info in pricing_data.items():
            # Try to match with known SQL tiers
            matched_spec = None
            for spec_name, spec_info in sql_specs.items():
                if spec_name.lower() in sql_name.lower() or sql_name.lower() in spec_name.lower():
                    matched_spec = spec_info
                    break
            
            # If no exact match, create basic specification
            if not matched_spec:
                matched_spec = {
                    "service_tier": "Unknown",
                    "max_size_gb": 100,
                    "dtu": 10,
                    "description": f"SQL Database service {sql_name}"
                }
            
            service = CloudService(
                provider=CloudProvider.AZURE,
                service_name=f"Azure SQL Database {sql_name}",
                service_id=sql_name,
                category=ServiceCategory.DATABASE,
                region=region,
                description=matched_spec["description"],
                hourly_price=pricing_info["hourly"],
                specifications={
                    "service_tier": matched_spec["service_tier"],
                    "max_size_gb": matched_spec["max_size_gb"],
                    "dtu": matched_spec["dtu"],
                    "engine": "sql_server",
                    "engine_version": "12.0"
                },
                features=["automated_backups", "point_in_time_restore", "geo_replication", "threat_detection"]
            )
            services.append(service)
        
        if not services:
            raise CloudServiceError(
                f"No SQL Database pricing matches found for region {region}. Available services: {list(pricing_data.keys())}",
                CloudProvider.AZURE,
                "NO_SQL_MATCHES"
            )
        
        return CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.DATABASE,
            region=region,
            services=services,
            metadata={"real_pricing": True, "pricing_source": "azure_retail_api"}
        )
    
    def _get_sql_database_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Get Azure SQL Database specifications for common tiers."""
        return {
            "Basic": {
                "service_tier": "Basic",
                "max_size_gb": 2,
                "dtu": 5,
                "description": "Basic tier for light workloads"
            },
            "S0": {
                "service_tier": "Standard",
                "max_size_gb": 250,
                "dtu": 10,
                "description": "Standard S0 tier"
            },
            "S1": {
                "service_tier": "Standard",
                "max_size_gb": 250,
                "dtu": 20,
                "description": "Standard S1 tier"
            },
            "S2": {
                "service_tier": "Standard",
                "max_size_gb": 250,
                "dtu": 50,
                "description": "Standard S2 tier"
            },
            "S3": {
                "service_tier": "Standard",
                "max_size_gb": 250,
                "dtu": 100,
                "description": "Standard S3 tier"
            },
            "P1": {
                "service_tier": "Premium",
                "max_size_gb": 500,
                "dtu": 125,
                "description": "Premium P1 tier"
            },
            "P2": {
                "service_tier": "Premium",
                "max_size_gb": 500,
                "dtu": 250,
                "description": "Premium P2 tier"
            },
            "P4": {
                "service_tier": "Premium",
                "max_size_gb": 500,
                "dtu": 500,
                "description": "Premium P4 tier"
            }
        }


class AzureAIClient:
    """
    Azure AI/ML services client.
    
    Provides access to Azure AI and machine learning services including
    Azure OpenAI, Cognitive Services, Machine Learning, and others.
    """
    
    def __init__(self, region: str = "eastus", subscription_id: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize Azure AI client."""
        self.region = region
        self.subscription_id = subscription_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.use_mock_data = True  # Azure AI APIs require complex authentication
    
    async def get_ai_services(self, region: str) -> CloudServiceResponse:
        """
        Get Azure AI/ML services with pricing information.
        
        Args:
            region: Azure region
            
        Returns:
            CloudServiceResponse with AI/ML services
        """
        services = []
        
        # Azure OpenAI services
        openai_services = self._get_azure_openai_services(region)
        services.extend(openai_services)
        
        # Azure Machine Learning services
        ml_services = self._get_azure_ml_services(region)
        services.extend(ml_services)
        
        # Cognitive Services
        cognitive_services = self._get_cognitive_services(region)
        services.extend(cognitive_services)
        
        return CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            services=services,
            metadata={"ai_services_count": len(services)}
        )
    
    def _get_azure_openai_services(self, region: str) -> List[CloudService]:
        """Get Azure OpenAI services with pricing."""
        services = []
        
        # Azure OpenAI models
        openai_models = [
            {
                "model_name": "GPT-4",
                "model_version": "0613",
                "input_price_per_1k": 0.03,
                "output_price_per_1k": 0.06,
                "context_length": 8192,
                "description": "Most capable GPT-4 model"
            },
            {
                "model_name": "GPT-4-32k",
                "model_version": "0613",
                "input_price_per_1k": 0.06,
                "output_price_per_1k": 0.12,
                "context_length": 32768,
                "description": "GPT-4 with extended context window"
            },
            {
                "model_name": "GPT-3.5-Turbo",
                "model_version": "0613",
                "input_price_per_1k": 0.0015,
                "output_price_per_1k": 0.002,
                "context_length": 4096,
                "description": "Fast and efficient language model"
            },
            {
                "model_name": "GPT-3.5-Turbo-16k",
                "model_version": "0613",
                "input_price_per_1k": 0.003,
                "output_price_per_1k": 0.004,
                "context_length": 16384,
                "description": "GPT-3.5 with extended context window"
            },
            {
                "model_name": "text-embedding-ada-002",
                "model_version": "2",
                "input_price_per_1k": 0.0001,
                "output_price_per_1k": 0.0,
                "context_length": 8191,
                "description": "Text embedding model"
            },
            {
                "model_name": "DALL-E-3",
                "model_version": "3.0",
                "price_per_image_standard": 0.04,
                "price_per_image_hd": 0.08,
                "description": "Advanced image generation model"
            }
        ]
        
        for model in openai_models:
            if "price_per_image_standard" in model:
                # Image generation model
                service = CloudService(
                    provider=CloudProvider.AZURE,
                    service_name=f"Azure OpenAI - {model['model_name']}",
                    service_id=f"azure_openai_{model['model_name'].lower().replace('-', '_').replace('.', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=model['description'],
                    pricing_model="pay_per_image",
                    hourly_price=model['price_per_image_standard'],
                    pricing_unit="image",
                    specifications={
                        "model_name": model['model_name'],
                        "model_version": model['model_version'],
                        "model_type": "image_generation",
                        "standard_price": model['price_per_image_standard'],
                        "hd_price": model['price_per_image_hd'],
                        "max_resolution": "1024x1024"
                    },
                    features=["managed_service", "enterprise_security", "content_filtering", "multiple_styles"]
                )
            else:
                # Text/embedding model
                service = CloudService(
                    provider=CloudProvider.AZURE,
                    service_name=f"Azure OpenAI - {model['model_name']}",
                    service_id=f"azure_openai_{model['model_name'].lower().replace('-', '_').replace('.', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=model['description'],
                    pricing_model="pay_per_token",
                    hourly_price=model['input_price_per_1k'],
                    pricing_unit="1K tokens",
                    specifications={
                        "model_name": model['model_name'],
                        "model_version": model['model_version'],
                        "model_type": "text_generation" if "embedding" not in model['model_name'].lower() else "embedding",
                        "context_length": model['context_length'],
                        "input_price_per_1k_tokens": model['input_price_per_1k'],
                        "output_price_per_1k_tokens": model['output_price_per_1k']
                    },
                    features=["managed_service", "enterprise_security", "content_filtering", "fine_tuning"]
                )
            services.append(service)
        
        return services
    
    def _get_azure_ml_services(self, region: str) -> List[CloudService]:
        """Get Azure Machine Learning services with pricing."""
        services = []
        
        # Azure ML compute instances
        ml_compute_instances = [
            {
                "instance_type": "Standard_DS3_v2",
                "vcpus": 4,
                "memory_gb": 14,
                "hourly_price": 0.192,
                "description": "General purpose compute instance"
            },
            {
                "instance_type": "Standard_DS4_v2",
                "vcpus": 8,
                "memory_gb": 28,
                "hourly_price": 0.384,
                "description": "General purpose compute instance"
            },
            {
                "instance_type": "Standard_NC6",
                "vcpus": 6,
                "memory_gb": 56,
                "hourly_price": 0.90,
                "gpu_count": 1,
                "gpu_type": "K80",
                "description": "GPU compute instance for training"
            },
            {
                "instance_type": "Standard_NC12",
                "vcpus": 12,
                "memory_gb": 112,
                "hourly_price": 1.80,
                "gpu_count": 2,
                "gpu_type": "K80",
                "description": "GPU compute instance for training"
            },
            {
                "instance_type": "Standard_ND40rs_v2",
                "vcpus": 40,
                "memory_gb": 672,
                "hourly_price": 22.032,
                "gpu_count": 8,
                "gpu_type": "V100",
                "description": "High-performance GPU instance for deep learning"
            }
        ]
        
        for instance in ml_compute_instances:
            service = CloudService(
                provider=CloudProvider.AZURE,
                service_name=f"Azure ML Compute - {instance['instance_type']}",
                service_id=f"azure_ml_{instance['instance_type'].lower().replace('_', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=instance['description'],
                pricing_model="pay_as_you_go",
                hourly_price=instance['hourly_price'],
                pricing_unit="hour",
                specifications={
                    "instance_type": instance['instance_type'],
                    "vcpus": instance['vcpus'],
                    "memory_gb": instance['memory_gb'],
                    "gpu_count": instance.get('gpu_count', 0),
                    "gpu_type": instance.get('gpu_type', 'None'),
                    "use_case": "ml_training_inference"
                },
                features=["managed_notebooks", "auto_scaling", "distributed_training", "model_deployment"]
            )
            services.append(service)
        
        # Azure ML managed endpoints
        endpoint_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure ML Managed Online Endpoints",
            service_id="azure_ml_managed_endpoints",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Managed inference endpoints for ML models",
            pricing_model="pay_as_you_go",
            hourly_price=0.50,  # Base price per endpoint per hour
            pricing_unit="endpoint-hour",
            specifications={
                "endpoint_type": "managed_online",
                "auto_scaling": True,
                "load_balancing": True,
                "monitoring": True
            },
            features=["auto_scaling", "load_balancing", "monitoring", "a_b_testing"]
        )
        services.append(endpoint_service)
        
        return services
    
    def _get_cognitive_services(self, region: str) -> List[CloudService]:
        """Get Azure Cognitive Services with pricing."""
        services = []
        
        # Computer Vision
        computer_vision_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure Computer Vision",
            service_id="azure_computer_vision",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Image analysis and optical character recognition",
            pricing_model="pay_per_transaction",
            hourly_price=0.001,  # Per transaction
            pricing_unit="transaction",
            specifications={
                "service_type": "computer_vision",
                "max_image_size": "4MB",
                "supported_formats": ["JPEG", "PNG", "GIF", "BMP"]
            },
            features=["object_detection", "ocr", "face_detection", "image_analysis"]
        )
        services.append(computer_vision_service)
        
        # Text Analytics
        text_analytics_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure Text Analytics",
            service_id="azure_text_analytics",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Natural language processing and text analysis",
            pricing_model="pay_per_transaction",
            hourly_price=0.001,  # Per 1000 characters
            pricing_unit="1000 characters",
            specifications={
                "service_type": "nlp",
                "languages_supported": 120,
                "max_document_size": "5120 characters"
            },
            features=["sentiment_analysis", "key_phrase_extraction", "language_detection", "entity_recognition"]
        )
        services.append(text_analytics_service)
        
        # Speech Services
        speech_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure Speech Services",
            service_id="azure_speech_services",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Speech-to-text and text-to-speech services",
            pricing_model="pay_per_hour",
            hourly_price=1.0,  # Per hour of audio
            pricing_unit="audio-hour",
            specifications={
                "service_type": "speech",
                "languages_supported": 85,
                "audio_formats": ["WAV", "MP3", "OGG"]
            },
            features=["speech_to_text", "text_to_speech", "speaker_recognition", "custom_models"]
        )
        services.append(speech_service)
        
        # Translator
        translator_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure Translator",
            service_id="azure_translator",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Real-time text translation service",
            pricing_model="pay_per_character",
            hourly_price=0.00001,  # Per character
            pricing_unit="character",
            specifications={
                "service_type": "translation",
                "languages_supported": 90,
                "max_text_size": "50000 characters"
            },
            features=["real_time_translation", "document_translation", "custom_models", "transliteration"]
        )
        services.append(translator_service)
        
        # Form Recognizer
        form_recognizer_service = CloudService(
            provider=CloudProvider.AZURE,
            service_name="Azure Form Recognizer",
            service_id="azure_form_recognizer",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="AI-powered document processing service",
            pricing_model="pay_per_page",
            hourly_price=0.05,  # Per page
            pricing_unit="page",
            specifications={
                "service_type": "document_processing",
                "max_file_size": "50MB",
                "supported_formats": ["PDF", "JPEG", "PNG", "TIFF"]
            },
            features=["form_extraction", "table_extraction", "custom_models", "receipt_processing"]
        )
        services.append(form_recognizer_service)
        
        return services