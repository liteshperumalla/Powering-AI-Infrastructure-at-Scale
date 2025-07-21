"""Tests for GCP cloud integration."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud import (
    GCPClient, GCPBillingClient, GCPComputeClient, GCPSQLClient,
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse, CloudServiceError
)


class TestGCPBillingClient:
    """Test the GCP Billing client."""
    
    @pytest.fixture
    def billing_client(self):
        """Create a GCP billing client for testing."""
        return GCPBillingClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_service_pricing(self, billing_client):
        """Test getting service pricing."""
        result = await billing_client.get_service_pricing("Compute Engine", "us-central1")
        
        assert result["service_name"] == "Compute Engine"
        assert result["region"] == "us-central1"
        assert "pricing_data" in result
        assert isinstance(result["pricing_data"], dict)
    
    def test_get_fallback_pricing(self, billing_client):
        """Test fallback pricing data."""
        compute_pricing = billing_client._get_fallback_pricing("Compute Engine")
        
        assert isinstance(compute_pricing, dict)
        assert "n1-standard-1" in compute_pricing
        assert "e2-micro" in compute_pricing
        
        sql_pricing = billing_client._get_fallback_pricing("Cloud SQL")
        
        assert isinstance(sql_pricing, dict)
        assert "db-f1-micro" in sql_pricing


class TestGCPComputeClient:
    """Test the GCP Compute client."""
    
    @pytest.fixture
    def compute_client(self):
        """Create a GCP compute client for testing."""
        return GCPComputeClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_machine_types(self, compute_client):
        """Test getting machine types."""
        result = await compute_client.get_machine_types("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.COMPUTE
        assert result.region == "us-central1"
        assert len(result.services) > 0
        
        # Check first service
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.GCP
        assert service.category == ServiceCategory.COMPUTE
        assert service.hourly_price is not None
        assert "vcpus" in service.specifications
        assert "memory_gb" in service.specifications


class TestGCPSQLClient:
    """Test the GCP Cloud SQL client."""
    
    @pytest.fixture
    def sql_client(self):
        """Create a GCP SQL client for testing."""
        return GCPSQLClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_database_instances(self, sql_client):
        """Test getting database instances."""
        result = await sql_client.get_database_instances("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.DATABASE
        assert result.region == "us-central1"
        assert len(result.services) > 0
        
        # Check first service
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.GCP
        assert service.category == ServiceCategory.DATABASE
        assert service.hourly_price is not None
        assert "vcpus" in service.specifications
        assert "memory_gb" in service.specifications
        assert "engine" in service.specifications


class TestGCPClient:
    """Test the main GCP client."""
    
    @pytest.fixture
    def gcp_client(self):
        """Create a GCP client for testing."""
        return GCPClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_compute_services(self, gcp_client):
        """Test getting compute services."""
        result = await gcp_client.get_compute_services("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.COMPUTE
        assert len(result.services) > 0
    
    @pytest.mark.asyncio
    async def test_get_storage_services(self, gcp_client):
        """Test getting storage services."""
        result = await gcp_client.get_storage_services("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.STORAGE
        assert len(result.services) > 0
        
        # Check for expected storage services
        service_ids = [s.service_id for s in result.services]
        assert "cloud_storage" in service_ids
        assert "persistent_disk_ssd" in service_ids
        assert "persistent_disk_standard" in service_ids
    
    @pytest.mark.asyncio
    async def test_get_database_services(self, gcp_client):
        """Test getting database services."""
        result = await gcp_client.get_database_services("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.DATABASE
        assert len(result.services) > 0


class TestGCPIntegration:
    """Test GCP integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_service_discovery(self):
        """Test end-to-end service discovery."""
        client = GCPClient("test-project", "us-central1")
        
        # Get all service types
        compute_services = await client.get_compute_services()
        storage_services = await client.get_storage_services()
        database_services = await client.get_database_services()
        
        # Verify we got services from each category
        assert len(compute_services.services) > 0
        assert len(storage_services.services) > 0
        assert len(database_services.services) > 0
        
        # Verify all services have required fields
        all_services = (compute_services.services + 
                       storage_services.services + 
                       database_services.services)
        
        for service in all_services:
            assert service.provider == CloudProvider.GCP
            assert service.service_name
            assert service.service_id
            assert service.hourly_price is not None
            assert service.specifications
    
    @pytest.mark.asyncio
    async def test_cost_comparison_workflow(self):
        """Test cost comparison workflow."""
        client = GCPClient("test-project", "us-central1")
        
        # Get compute services
        compute_services = await client.get_compute_services()
        
        # Find cheapest service
        cheapest = compute_services.get_cheapest_service()
        assert cheapest is not None
        assert cheapest.hourly_price > 0
        
        # Calculate monthly cost
        monthly_cost = cheapest.get_monthly_cost()
        assert monthly_cost > 0
        assert monthly_cost == cheapest.hourly_price * 730  # Default 730 hours per month
    
    @pytest.mark.asyncio
    async def test_service_filtering(self):
        """Test service filtering capabilities."""
        client = GCPClient("test-project", "us-central1")
        
        # Get compute services
        compute_services = await client.get_compute_services()
        
        # Filter by specifications
        high_memory_services = compute_services.filter_by_specs(memory_gb=8)
        
        # Verify filtering worked
        for service in high_memory_services:
            assert service.specifications.get("memory_gb", 0) >= 8
    
    def test_cloud_service_response_utilities(self):
        """Test CloudServiceResponse utility methods."""
        services = [
            CloudService(
                provider=CloudProvider.GCP,
                service_name="Test Service 1",
                service_id="test-1",
                category=ServiceCategory.COMPUTE,
                region="us-central1",
                hourly_price=0.10,
                specifications={"vcpus": 2, "memory_gb": 4}
            ),
            CloudService(
                provider=CloudProvider.GCP,
                service_name="Test Service 2", 
                service_id="test-2",
                category=ServiceCategory.COMPUTE,
                region="us-central1",
                hourly_price=0.05,
                specifications={"vcpus": 1, "memory_gb": 2}
            )
        ]
        
        response = CloudServiceResponse(
            provider=CloudProvider.GCP,
            service_category=ServiceCategory.COMPUTE,
            region="us-central1",
            services=services
        )
        
        # Test cheapest service
        cheapest = response.get_cheapest_service()
        assert cheapest.service_id == "test-2"
        assert cheapest.hourly_price == 0.05
        
        # Test filtering
        filtered = response.filter_by_specs(vcpus=2)
        assert len(filtered) == 1
        assert filtered[0].service_id == "test-1"