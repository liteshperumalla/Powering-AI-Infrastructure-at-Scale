"""
Tests for Azure API integration (Real API Only).

Tests the Azure Retail Prices API, Compute, and SQL Database clients.
Note: These tests work with real APIs and proper error handling.
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud.azure import AzureClient, AzurePricingClient, AzureComputeClient, AzureSQLClient
from src.infra_mind.cloud.base import CloudProvider, ServiceCategory, CloudService, CloudServiceResponse, CloudServiceError

RUN_CLOUD_TESTS = os.getenv("RUN_CLOUD_INTEGRATION_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_CLOUD_TESTS,
    reason="Azure integration tests require live credentials/network. Set RUN_CLOUD_INTEGRATION_TESTS=1 to enable.",
)


class TestAzurePricingClient:
    """Test Azure Retail Prices API client."""
    
    @pytest.fixture
    def pricing_client(self):
        """Create pricing client for testing."""
        return AzurePricingClient(region="eastus")
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_api_failure(self, pricing_client):
        """Test proper error handling when API fails."""
        # Mock httpx to simulate API failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Should raise CloudServiceError instead of returning mock data
            with pytest.raises(CloudServiceError) as exc_info:
                await pricing_client.get_service_pricing("Virtual Machines", "eastus")
            
            assert "HTTP_500" in str(exc_info.value)
            assert exc_info.value.provider == CloudProvider.AZURE
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_sql_mock(self, pricing_client):
        """Test getting SQL Database pricing data."""
        # Force mock mode by simulating API failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await pricing_client.get_service_pricing("SQL Database", "eastus")
            
            assert result["service_name"] == "SQL Database"
            assert "Basic" in result["pricing_data"]
            assert result["pricing_data"]["Basic"]["hourly"] == 0.0068
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_success(self, pricing_client):
        """Test successful API call."""
        mock_response_data = {
            "Items": [
                {
                    "serviceName": "Virtual Machines",
                    "productName": "Virtual Machines Bs Series",
                    "skuName": "B1s",
                    "retailPrice": 0.0052,
                    "unitPrice": 0.0052,
                    "currencyCode": "USD",
                    "unitOfMeasure": "1 Hour"
                }
            ],
            "NextPageLink": None,
            "Count": 1
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await pricing_client.get_service_pricing("Virtual Machines", "eastus")
            
            assert result["service_name"] == "Virtual Machines"
            assert result["region"] == "eastus"
            assert len(result["items"]) == 1
            assert result["items"][0]["skuName"] == "B1s"
            assert result["count"] == 1


class TestAzureComputeClient:
    """Test Azure Compute client."""
    
    @pytest.fixture
    def compute_client(self):
        """Create compute client for testing."""
        return AzureComputeClient(region="eastus")
    
    @pytest.mark.asyncio
    async def test_get_vm_sizes_mock(self, compute_client):
        """Test getting Azure VM sizes with mock data."""
        result = await compute_client.get_vm_sizes("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.COMPUTE
        assert result.region == "eastus"
        assert len(result.services) > 0
        
        # Check first service
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AZURE
        assert service.category == ServiceCategory.COMPUTE
        assert service.service_id == "Standard_B1s"
        assert service.hourly_price == 0.0052
        assert "vcpus" in service.specifications
        assert "memory_gb" in service.specifications
    
    @pytest.mark.asyncio
    async def test_mock_vm_sizes_structure(self, compute_client):
        """Test the structure of mock Azure VM sizes."""
        result = await compute_client.get_vm_sizes("westus2")
        
        # Verify all services have required fields
        for service in result.services:
            assert service.service_name.startswith("Azure VM")
            assert service.hourly_price is not None
            assert service.specifications["vcpus"] > 0
            assert service.specifications["memory_gb"] > 0
            assert "os_disk_size_gb" in service.specifications
            assert "max_data_disks" in service.specifications
            assert len(service.features) > 0
    
    @pytest.mark.asyncio
    async def test_vm_sizes_different_regions(self, compute_client):
        """Test VM sizes for different regions."""
        regions = ["eastus", "westus2", "northeurope"]
        
        for region in regions:
            result = await compute_client.get_vm_sizes(region)
            assert result.region == region
            assert len(result.services) > 0
            
            # All services should have the same structure regardless of region
            for service in result.services:
                assert service.region == region
                assert service.provider == CloudProvider.AZURE


class TestAzureSQLClient:
    """Test Azure SQL Database client."""
    
    @pytest.fixture
    def sql_client(self):
        """Create SQL client for testing."""
        return AzureSQLClient(region="eastus")
    
    @pytest.mark.asyncio
    async def test_get_database_services_mock(self, sql_client):
        """Test getting Azure SQL Database services with mock data."""
        result = await sql_client.get_database_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.DATABASE
        assert result.region == "eastus"
        assert len(result.services) > 0
        
        # Check first service (Basic tier)
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AZURE
        assert service.category == ServiceCategory.DATABASE
        assert service.service_id == "Basic"
        assert service.hourly_price == 0.0068
        assert service.specifications["service_tier"] == "Basic"
        assert service.specifications["engine"] == "sql_server"
    
    @pytest.mark.asyncio
    async def test_sql_services_tiers(self, sql_client):
        """Test different SQL Database service tiers."""
        result = await sql_client.get_database_services("eastus")
        
        # Check that we have different service tiers
        service_tiers = [s.specifications["service_tier"] for s in result.services]
        assert "Basic" in service_tiers
        assert "Standard" in service_tiers
        assert "Premium" in service_tiers
        
        # Check that Premium tier is more expensive than Basic
        basic_service = next(s for s in result.services if s.specifications["service_tier"] == "Basic")
        premium_service = next(s for s in result.services if s.specifications["service_tier"] == "Premium")
        
        assert premium_service.hourly_price > basic_service.hourly_price
        assert premium_service.specifications["max_size_gb"] > basic_service.specifications["max_size_gb"]
    
    @pytest.mark.asyncio
    async def test_sql_services_features(self, sql_client):
        """Test SQL Database services have expected features."""
        result = await sql_client.get_database_services("westeurope")
        
        for service in result.services:
            assert "automated_backups" in service.features
            assert "point_in_time_restore" in service.features
            assert "geo_replication" in service.features
            assert service.specifications["engine_version"] == "12.0"


class TestAzureClient:
    """Test main Azure client."""
    
    @pytest.fixture
    def azure_client(self):
        """Create Azure client for testing."""
        return AzureClient(region="eastus")
    
    @pytest.mark.asyncio
    async def test_get_compute_services(self, azure_client):
        """Test getting compute services."""
        result = await azure_client.get_compute_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.COMPUTE
        assert len(result.services) > 0
    
    @pytest.mark.asyncio
    async def test_get_storage_services(self, azure_client):
        """Test getting storage services."""
        result = await azure_client.get_storage_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.STORAGE
        assert len(result.services) >= 2  # Blob Storage and Managed Disks
        
        # Check for Blob Storage service
        blob_services = [s for s in result.services if s.service_id == "blob_storage"]
        assert len(blob_services) == 1
        assert blob_services[0].service_name == "Azure Blob Storage"
        
        # Check for Managed Disk service
        disk_services = [s for s in result.services if s.service_id == "managed_disk_premium"]
        assert len(disk_services) == 1
        assert disk_services[0].hourly_price == 0.135
    
    @pytest.mark.asyncio
    async def test_get_database_services(self, azure_client):
        """Test getting database services."""
        result = await azure_client.get_database_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.DATABASE
        assert len(result.services) > 0
    
    @pytest.mark.asyncio
    async def test_get_service_pricing(self, azure_client):
        """Test getting service pricing."""
        # Mock the pricing client to avoid actual API calls
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500  # Force mock data
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await azure_client.get_service_pricing("Virtual Machines", "eastus")
            
            assert result["service_name"] == "Virtual Machines"
            assert result["region"] == "eastus"
            assert "pricing_data" in result


class TestAzureIntegration:
    """Integration tests for Azure services."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_service_discovery(self):
        """Test end-to-end service discovery workflow."""
        client = AzureClient(region="eastus")
        
        # Get all service types
        compute_services = await client.get_compute_services()
        storage_services = await client.get_storage_services()
        database_services = await client.get_database_services()
        
        # Verify we got services from all categories
        assert len(compute_services.services) > 0
        assert len(storage_services.services) > 0
        assert len(database_services.services) > 0
        
        # Verify all services have the required fields
        all_services = (compute_services.services + 
                       storage_services.services + 
                       database_services.services)
        
        for service in all_services:
            assert service.provider == CloudProvider.AZURE
            assert service.region == "eastus"
            assert service.service_name
            assert service.service_id
            assert service.category in [ServiceCategory.COMPUTE, ServiceCategory.STORAGE, ServiceCategory.DATABASE]
    
    @pytest.mark.asyncio
    async def test_cost_comparison_workflow(self):
        """Test cost comparison workflow."""
        client = AzureClient(region="eastus")
        
        compute_services = await client.get_compute_services()
        
        # Find cheapest compute service
        cheapest = compute_services.get_cheapest_service()
        assert cheapest is not None
        assert cheapest.service_id == "Standard_B1s"  # Should be cheapest in mock data
        assert cheapest.hourly_price == 0.0052
        
        # Calculate monthly costs
        monthly_cost = cheapest.get_monthly_cost()
        assert monthly_cost == 0.0052 * 730  # Default 730 hours per month
    
    @pytest.mark.asyncio
    async def test_service_filtering(self):
        """Test service filtering by specifications."""
        client = AzureClient(region="eastus")
        
        compute_services = await client.get_compute_services()
        
        # Filter by memory
        high_memory_services = compute_services.filter_by_specs(memory_gb=16)
        assert len(high_memory_services) > 0
        
        for service in high_memory_services:
            assert service.specifications["memory_gb"] == 16
    
    @pytest.mark.asyncio
    async def test_multi_region_support(self):
        """Test multi-region support."""
        regions = ["eastus", "westus2", "northeurope"]
        
        for region in regions:
            client = AzureClient(region=region)
            
            compute_services = await client.get_compute_services()
            database_services = await client.get_database_services()
            
            # Verify region is set correctly
            assert compute_services.region == region
            assert database_services.region == region
            
            # Verify services exist
            assert len(compute_services.services) > 0
            assert len(database_services.services) > 0
    
    def test_cloud_service_response_utilities(self):
        """Test CloudServiceResponse utility methods with Azure services."""
        # Create test Azure services
        services = [
            CloudService(
                provider=CloudProvider.AZURE,
                service_name="Azure VM Standard_B1s",
                service_id="Standard_B1s",
                category=ServiceCategory.COMPUTE,
                region="eastus",
                hourly_price=0.0052,
                specifications={"vcpus": 1, "memory_gb": 1}
            ),
            CloudService(
                provider=CloudProvider.AZURE,
                service_name="Azure VM Standard_B2s",
                service_id="Standard_B2s",
                category=ServiceCategory.COMPUTE,
                region="eastus",
                hourly_price=0.0208,
                specifications={"vcpus": 2, "memory_gb": 4}
            )
        ]
        
        response = CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.COMPUTE,
            region="eastus",
            services=services
        )
        
        # Test cheapest service
        cheapest = response.get_cheapest_service()
        assert cheapest.service_id == "Standard_B1s"
        assert cheapest.hourly_price == 0.0052
        
        # Test filtering
        filtered = response.filter_by_specs(vcpus=2)
        assert len(filtered) == 1
        assert filtered[0].service_id == "Standard_B2s"


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
