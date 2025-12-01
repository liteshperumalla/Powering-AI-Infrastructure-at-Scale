"""Tests for GCP cloud integration."""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud import (
    GCPClient, GCPBillingClient, GCPComputeClient, GCPSQLClient,
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse, CloudServiceError
)
from src.infra_mind.cloud.gcp import GCPGKEClient, GCPAssetClient, GCPRecommenderClient, GCPAIClient

RUN_CLOUD_TESTS = os.getenv("RUN_CLOUD_INTEGRATION_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_CLOUD_TESTS,
    reason="GCP integration tests require credentials/network. Set RUN_CLOUD_INTEGRATION_TESTS=1 to enable.",
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


class TestGCPGKEClient:
    """Test the GCP GKE client."""
    
    @pytest.fixture
    def gke_client(self):
        """Create a GCP GKE client for testing."""
        return GCPGKEClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_gke_services(self, gke_client):
        """Test getting GKE services."""
        result = await gke_client.get_gke_services("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.CONTAINER
        assert result.region == "us-central1"
        assert len(result.services) > 0
        
        # Check for expected GKE services
        service_ids = [s.service_id for s in result.services]
        assert "gke_cluster_management" in service_ids
        assert "gke_autopilot" in service_ids
        
        # Check cluster management service
        cluster_service = next(s for s in result.services if s.service_id == "gke_cluster_management")
        assert cluster_service.provider == CloudProvider.GCP
        assert cluster_service.category == ServiceCategory.CONTAINER
        assert cluster_service.hourly_price is not None
        assert "service_type" in cluster_service.specifications
        
        # Check node pool services
        node_pool_services = [s for s in result.services if "node_pool" in s.service_id]
        assert len(node_pool_services) > 0
        
        for service in node_pool_services:
            assert service.provider == CloudProvider.GCP
            assert service.category == ServiceCategory.CONTAINER
            assert "machine_type" in service.specifications
            assert "vcpus" in service.specifications
            assert "memory_gb" in service.specifications


class TestGCPAssetClient:
    """Test the GCP Asset client."""
    
    @pytest.fixture
    def asset_client(self):
        """Create a GCP Asset client for testing."""
        return GCPAssetClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_asset_inventory_default(self, asset_client):
        """Test getting asset inventory with default asset types."""
        result = await asset_client.get_asset_inventory()
        
        assert isinstance(result, dict)
        assert result["project_id"] == "test-project"
        assert result["region"] == "us-central1"
        assert "timestamp" in result
        assert "assets" in result
        assert "summary" in result
        
        # Check summary
        summary = result["summary"]
        assert "total_assets" in summary
        assert "assets_by_type" in summary
        assert "assets_by_region" in summary
        assert "estimated_monthly_cost" in summary
        assert summary["total_assets"] > 0
        assert summary["estimated_monthly_cost"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_asset_inventory_specific_types(self, asset_client):
        """Test getting asset inventory with specific asset types."""
        asset_types = ["compute.googleapis.com/Instance", "storage.googleapis.com/Bucket"]
        result = await asset_client.get_asset_inventory(asset_types)
        
        assert isinstance(result, dict)
        assert result["asset_types_queried"] == asset_types
        assert len(result["assets"]) > 0
        
        # Check that only requested asset types are returned
        returned_types = set(asset["asset_type"] for asset in result["assets"])
        for asset_type in returned_types:
            assert asset_type in asset_types
    
    def test_generate_sample_assets(self, asset_client):
        """Test sample asset generation."""
        asset_types = ["compute.googleapis.com/Instance", "storage.googleapis.com/Bucket"]
        assets = asset_client._generate_sample_assets(asset_types)
        
        assert isinstance(assets, list)
        assert len(assets) > 0
        
        for asset in assets:
            assert "name" in asset
            assert "asset_type" in asset
            assert "location" in asset
            assert "resource" in asset
            assert "estimated_monthly_cost" in asset
            assert asset["asset_type"] in asset_types


class TestGCPRecommenderClient:
    """Test the GCP Recommender client."""
    
    @pytest.fixture
    def recommender_client(self):
        """Create a GCP Recommender client for testing."""
        return GCPRecommenderClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_cost_optimization_recommendations(self, recommender_client):
        """Test getting cost optimization recommendations."""
        result = await recommender_client.get_recommendations("cost_optimization", "us-central1")
        
        assert isinstance(result, dict)
        assert result["project_id"] == "test-project"
        assert result["region"] == "us-central1"
        assert result["recommender_type"] == "cost_optimization"
        assert "recommendations" in result
        assert "summary" in result
        
        # Check summary
        summary = result["summary"]
        assert "total_recommendations" in summary
        assert "potential_monthly_savings" in summary
        assert "recommendations_by_priority" in summary
        assert summary["total_recommendations"] > 0
        
        # Check recommendations structure
        recommendations = result["recommendations"]
        for rec in recommendations:
            assert "name" in rec
            assert "description" in rec
            assert "priority" in rec
            assert "category" in rec
            assert "potential_monthly_savings" in rec
            assert "confidence" in rec
    
    @pytest.mark.asyncio
    async def test_get_security_recommendations(self, recommender_client):
        """Test getting security recommendations."""
        result = await recommender_client.get_recommendations("security", "us-central1")
        
        assert isinstance(result, dict)
        assert result["recommender_type"] == "security"
        assert len(result["recommendations"]) > 0
        
        # Check that security recommendations have appropriate structure
        for rec in result["recommendations"]:
            assert rec["category"] == "SECURITY"
            assert "impact" in rec
    
    @pytest.mark.asyncio
    async def test_get_performance_recommendations(self, recommender_client):
        """Test getting performance recommendations."""
        result = await recommender_client.get_recommendations("performance", "us-central1")
        
        assert isinstance(result, dict)
        assert result["recommender_type"] == "performance"
        assert len(result["recommendations"]) > 0
        
        # Check that performance recommendations have appropriate structure
        for rec in result["recommendations"]:
            assert rec["category"] == "PERFORMANCE"
    
    @pytest.mark.asyncio
    async def test_get_rightsizing_recommendations(self, recommender_client):
        """Test getting rightsizing recommendations."""
        result = await recommender_client.get_recommendations("rightsizing", "us-central1")
        
        assert isinstance(result, dict)
        assert result["recommender_type"] == "rightsizing"
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_commitment_recommendations(self, recommender_client):
        """Test getting commitment utilization recommendations."""
        result = await recommender_client.get_recommendations("commitment_utilization", "us-central1")
        
        assert isinstance(result, dict)
        assert result["recommender_type"] == "commitment_utilization"
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_recommender_type_defaults_to_cost(self, recommender_client):
        """Test that invalid recommender type defaults to cost optimization."""
        result = await recommender_client.get_recommendations("invalid_type", "us-central1")
        
        assert result["recommender_type"] == "cost_optimization"
    
    def test_generate_sample_recommendations(self, recommender_client):
        """Test sample recommendation generation."""
        recommendations = recommender_client._generate_sample_recommendations("cost_optimization")
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert "name" in rec
            assert "description" in rec
            assert "priority" in rec
            assert "category" in rec
            assert "potential_monthly_savings" in rec
            assert "confidence" in rec
            assert rec["priority"] in ["HIGH", "MEDIUM", "LOW"]


class TestGCPAIClient:
    """Test the GCP AI client."""
    
    @pytest.fixture
    def ai_client(self):
        """Create a GCP AI client for testing."""
        return GCPAIClient("test-project", "us-central1")
    
    @pytest.mark.asyncio
    async def test_get_ai_services(self, ai_client):
        """Test getting AI services."""
        result = await ai_client.get_ai_services("us-central1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.MACHINE_LEARNING
        assert result.region == "us-central1"
        assert len(result.services) > 0
        
        # Check for expected AI services
        service_ids = [s.service_id for s in result.services]
        
        # Check for Vertex AI services
        vertex_training_services = [s for s in result.services if "vertex_ai_training" in s.service_id]
        assert len(vertex_training_services) > 0
        
        vertex_prediction_services = [s for s in result.services if "vertex_ai_prediction" in s.service_id]
        assert len(vertex_prediction_services) > 0
        
        # Check for generative AI models
        generative_services = [s for s in result.services if any(model in s.service_id for model in ["text_bison", "chat_bison", "code_bison"])]
        assert len(generative_services) > 0
        
        # Verify service structure
        for service in result.services:
            assert service.provider == CloudProvider.GCP
            assert service.category == ServiceCategory.MACHINE_LEARNING
            assert service.hourly_price is not None
            assert service.specifications
            assert service.features


class TestGCPExtendedIntegration:
    """Test extended GCP integration with new clients."""
    
    @pytest.mark.asyncio
    async def test_full_gcp_client_with_extensions(self):
        """Test the main GCP client with all extended services."""
        client = GCPClient("test-project", "us-central1")
        
        # Test all service types
        compute_services = await client.get_compute_services()
        storage_services = await client.get_storage_services()
        database_services = await client.get_database_services()
        ai_services = await client.get_ai_services()
        kubernetes_services = await client.get_kubernetes_services()
        
        # Verify all service responses
        assert len(compute_services.services) > 0
        assert len(storage_services.services) > 0
        assert len(database_services.services) > 0
        assert len(ai_services.services) > 0
        assert len(kubernetes_services.services) > 0
        
        # Test asset inventory
        asset_inventory = await client.get_asset_inventory()
        assert isinstance(asset_inventory, dict)
        assert "assets" in asset_inventory
        assert "summary" in asset_inventory
        
        # Test recommendations
        cost_recommendations = await client.get_recommendations("cost_optimization")
        assert isinstance(cost_recommendations, dict)
        assert "recommendations" in cost_recommendations
        assert len(cost_recommendations["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_service_discovery(self):
        """Test comprehensive service discovery across all GCP services."""
        client = GCPClient("test-project", "us-central1")
        
        # Get all service categories
        all_services = []
        
        compute_response = await client.get_compute_services()
        all_services.extend(compute_response.services)
        
        storage_response = await client.get_storage_services()
        all_services.extend(storage_response.services)
        
        database_response = await client.get_database_services()
        all_services.extend(database_response.services)
        
        ai_response = await client.get_ai_services()
        all_services.extend(ai_response.services)
        
        kubernetes_response = await client.get_kubernetes_services()
        all_services.extend(kubernetes_response.services)
        
        # Verify comprehensive coverage
        assert len(all_services) > 50  # Should have many services across all categories
        
        # Check service categories are represented
        categories = set(service.category for service in all_services)
        expected_categories = {
            ServiceCategory.COMPUTE,
            ServiceCategory.STORAGE,
            ServiceCategory.DATABASE,
            ServiceCategory.MACHINE_LEARNING,
            ServiceCategory.CONTAINER
        }
        assert expected_categories.issubset(categories)
        
        # Verify all services have required fields
        for service in all_services:
            assert service.provider == CloudProvider.GCP
            assert service.service_name
            assert service.service_id
            assert service.hourly_price is not None
            assert service.specifications
            assert isinstance(service.features, list)
    
    @pytest.mark.asyncio
    async def test_cost_analysis_workflow(self):
        """Test cost analysis workflow with extended services."""
        client = GCPClient("test-project", "us-central1")
        
        # Get services for cost analysis
        compute_services = await client.get_compute_services()
        kubernetes_services = await client.get_kubernetes_services()
        
        # Find cost-effective options
        cheapest_compute = compute_services.get_cheapest_service()
        cheapest_kubernetes = kubernetes_services.get_cheapest_service()
        
        assert cheapest_compute is not None
        assert cheapest_kubernetes is not None
        
        # Get cost optimization recommendations
        recommendations = await client.get_recommendations("cost_optimization")
        
        # Verify recommendations provide actionable cost savings
        total_potential_savings = sum(
            rec.get("potential_monthly_savings", 0) 
            for rec in recommendations["recommendations"]
        )
        assert total_potential_savings > 0
    
    @pytest.mark.asyncio
    async def test_asset_and_recommendation_correlation(self):
        """Test correlation between asset inventory and recommendations."""
        client = GCPClient("test-project", "us-central1")
        
        # Get asset inventory
        asset_inventory = await client.get_asset_inventory()
        
        # Get recommendations
        recommendations = await client.get_recommendations("cost_optimization")
        
        # Verify data consistency
        assert asset_inventory["project_id"] == recommendations["project_id"]
        assert asset_inventory["summary"]["total_assets"] > 0
        assert recommendations["summary"]["total_recommendations"] > 0
        
        # Check that recommendations reference actual asset types
        asset_types = set(asset["asset_type"] for asset in asset_inventory["assets"])
        
        # At least some recommendations should reference compute instances
        compute_recommendations = [
            rec for rec in recommendations["recommendations"]
            if "compute.googleapis.com/Instance" in rec.get("content", {}).get("operation_groups", [{}])[0].get("operations", [{}])[0].get("resource_type", "")
        ]
        
        if "compute.googleapis.com/Instance" in asset_types:
            assert len(compute_recommendations) > 0
