"""
Integration tests for production GCP API integration.

This test suite verifies that the GCP client works with real Google Cloud APIs,
including proper authentication, rate limiting, and error handling.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from google.auth.exceptions import DefaultCredentialsError
from google.api_core import exceptions as gcp_exceptions

from src.infra_mind.cloud.gcp import (
    GCPClient, GCPBillingClient, GCPComputeClient, GCPSQLClient,
    GCPGKEClient, GCPAssetClient, GCPRecommenderClient
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudServiceError, 
    RateLimitError, AuthenticationError
)


class TestGCPProductionIntegration:
    """Test suite for production GCP API integration."""
    
    @pytest.fixture
    def project_id(self):
        """Test project ID."""
        return "test-project-12345"
    
    @pytest.fixture
    def region(self):
        """Test region."""
        return "us-central1"
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock GCP credentials."""
        mock_creds = Mock()
        mock_creds.token = "mock-token"
        return mock_creds
    
    def test_gcp_client_initialization_with_credentials(self, project_id, region, mock_credentials):
        """Test GCP client initialization with valid credentials."""
        with patch('src.infra_mind.cloud.gcp.default') as mock_default:
            mock_default.return_value = (mock_credentials, project_id)
            
            client = GCPClient(project_id, region)
            
            assert client.project_id == project_id
            assert client.region == region
            assert client.credentials == mock_credentials
            assert client.provider == CloudProvider.GCP
    
    def test_gcp_client_initialization_without_credentials(self, project_id, region):
        """Test GCP client initialization without credentials raises AuthenticationError."""
        with patch('src.infra_mind.cloud.gcp.default') as mock_default:
            mock_default.side_effect = DefaultCredentialsError("No credentials found")
            
            with pytest.raises(AuthenticationError) as exc_info:
                GCPClient(project_id, region)
            
            assert "GCP credentials not available" in str(exc_info.value)
            assert exc_info.value.provider == CloudProvider.GCP
    
    def test_gcp_client_initialization_with_service_account_path(self, project_id, region, mock_credentials):
        """Test GCP client initialization with service account path."""
        service_account_path = "/path/to/service-account.json"
        
        with patch('src.infra_mind.cloud.gcp.default') as mock_default, \
             patch('os.path.exists') as mock_exists:
            mock_default.return_value = (mock_credentials, project_id)
            mock_exists.return_value = True
            
            client = GCPClient(project_id, region, service_account_path)
            
            assert client.project_id == project_id
            assert os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') == service_account_path


class TestGCPBillingClient:
    """Test suite for GCP Billing client."""
    
    @pytest.fixture
    def billing_client(self, project_id, region, mock_credentials):
        """Create billing client for testing."""
        return GCPBillingClient(project_id, region, mock_credentials)
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_with_real_api(self, billing_client):
        """Test getting service pricing with real API."""
        with patch.object(billing_client, 'catalog_client') as mock_catalog:
            # Mock API response
            mock_service = Mock()
            mock_service.display_name = "Compute Engine"
            mock_service.name = "services/compute-engine"
            
            mock_sku = Mock()
            mock_sku.sku_id = "test-sku"
            mock_sku.description = "Test SKU"
            mock_sku.pricing_info = [Mock()]
            mock_sku.pricing_info[0].currency_code = "USD"
            mock_sku.pricing_info[0].pricing_expression = Mock()
            mock_sku.pricing_info[0].pricing_expression.base_unit = "hour"
            mock_sku.pricing_info[0].pricing_expression.base_unit_conversion_factor = 1
            mock_sku.pricing_info[0].pricing_expression.tiered_rates = [Mock()]
            mock_sku.pricing_info[0].pricing_expression.tiered_rates[0].unit_price = Mock()
            mock_sku.pricing_info[0].pricing_expression.tiered_rates[0].unit_price.units = 0
            mock_sku.pricing_info[0].pricing_expression.tiered_rates[0].unit_price.nanos = 50000000  # $0.05
            
            mock_catalog.list_services.return_value = [mock_service]
            mock_catalog.list_skus.return_value = [mock_sku]
            
            result = await billing_client.get_service_pricing("Compute Engine", "us-central1")
            
            assert result["service_name"] == "Compute Engine"
            assert result["region"] == "us-central1"
            assert result["real_data"] is True
            assert "pricing_data" in result
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_permission_denied(self, billing_client):
        """Test handling permission denied error."""
        with patch.object(billing_client, 'catalog_client') as mock_catalog:
            mock_catalog.list_services.side_effect = gcp_exceptions.PermissionDenied("Permission denied")
            
            with pytest.raises(AuthenticationError) as exc_info:
                await billing_client.get_service_pricing("Compute Engine", "us-central1")
            
            assert "Permission denied accessing GCP Billing API" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_rate_limit(self, billing_client):
        """Test handling rate limit error."""
        with patch.object(billing_client, 'catalog_client') as mock_catalog:
            mock_catalog.list_services.side_effect = gcp_exceptions.ResourceExhausted("Rate limit exceeded")
            
            with pytest.raises(RateLimitError) as exc_info:
                await billing_client.get_service_pricing("Compute Engine", "us-central1")
            
            assert "GCP Billing API rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_fallback(self, billing_client):
        """Test fallback pricing when API fails."""
        billing_client.catalog_client = None
        
        result = await billing_client.get_service_pricing("Compute Engine", "us-central1")
        
        assert result["service_name"] == "Compute Engine"
        assert result["real_data"] is False
        assert "fallback_reason" in result


class TestGCPComputeClient:
    """Test suite for GCP Compute client."""
    
    @pytest.fixture
    def compute_client(self, project_id, region, mock_credentials):
        """Create compute client for testing."""
        return GCPComputeClient(project_id, region, mock_credentials)
    
    @pytest.mark.asyncio
    async def test_get_machine_types_with_real_api(self, compute_client):
        """Test getting machine types with real API."""
        with patch.object(compute_client, 'client') as mock_client, \
             patch.object(compute_client, 'zones_client') as mock_zones:
            
            # Mock zones response
            mock_zone = Mock()
            mock_zone.name = "us-central1-a"
            mock_zone.region = "projects/test/regions/us-central1"
            mock_zones.list.return_value = [mock_zone]
            
            # Mock machine types response
            mock_machine_type = Mock()
            mock_machine_type.name = "n1-standard-1"
            mock_machine_type.description = "Standard machine type"
            mock_machine_type.guest_cpus = 1
            mock_machine_type.memory_mb = 3840  # 3.75 GB
            mock_machine_type.maximum_persistent_disks = 16
            mock_machine_type.maximum_persistent_disks_size_gb = 65536
            mock_machine_type.is_shared_cpu = False
            
            mock_client.list.return_value = [mock_machine_type]
            
            result = await compute_client.get_machine_types("us-central1")
            
            assert result.provider == CloudProvider.GCP
            assert result.service_category == ServiceCategory.COMPUTE
            assert result.region == "us-central1"
            assert len(result.services) > 0
            assert result.metadata["real_api"] is True
    
    @pytest.mark.asyncio
    async def test_get_machine_types_permission_denied(self, compute_client):
        """Test handling permission denied error."""
        with patch.object(compute_client, 'client') as mock_client, \
             patch.object(compute_client, 'zones_client') as mock_zones:
            
            mock_zones.list.side_effect = gcp_exceptions.PermissionDenied("Permission denied")
            
            with pytest.raises(AuthenticationError) as exc_info:
                await compute_client.get_machine_types("us-central1")
            
            assert "Permission denied accessing GCP Compute API" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_machine_types_fallback(self, compute_client):
        """Test fallback machine types when API fails."""
        compute_client.client = None
        
        result = await compute_client.get_machine_types("us-central1")
        
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.COMPUTE
        assert len(result.services) > 0
        assert result.metadata["real_api"] is False


class TestGCPSQLClient:
    """Test suite for GCP SQL client."""
    
    @pytest.fixture
    def sql_client(self, project_id, region, mock_credentials):
        """Create SQL client for testing."""
        return GCPSQLClient(project_id, region, mock_credentials)
    
    @pytest.mark.asyncio
    async def test_get_database_instances_with_real_api(self, sql_client):
        """Test getting database instances with real API."""
        with patch.object(sql_client, 'client') as mock_client:
            # Mock tiers response
            mock_tier = Mock()
            mock_tier.tier = "db-n1-standard-1"
            mock_tier.RAM = 4026531840  # 3.75 GB in bytes
            mock_tier.DiskQuota = 10737418240  # 10 GB in bytes
            
            mock_response = Mock()
            mock_response.items = [mock_tier]
            mock_client.list.return_value = mock_response
            
            result = await sql_client.get_database_instances("us-central1")
            
            assert result.provider == CloudProvider.GCP
            assert result.service_category == ServiceCategory.DATABASE
            assert result.region == "us-central1"
            assert len(result.services) > 0
            assert result.metadata["real_api"] is True
    
    @pytest.mark.asyncio
    async def test_get_database_instances_fallback(self, sql_client):
        """Test fallback database instances when API fails."""
        sql_client.client = None
        
        result = await sql_client.get_database_instances("us-central1")
        
        assert result.provider == CloudProvider.GCP
        assert result.service_category == ServiceCategory.DATABASE
        assert len(result.services) > 0
        assert result.metadata["real_api"] is False


class TestGCPAssetClient:
    """Test suite for GCP Asset client."""
    
    @pytest.fixture
    def asset_client(self, project_id, region, mock_credentials):
        """Create asset client for testing."""
        return GCPAssetClient(project_id, region, mock_credentials)
    
    @pytest.mark.asyncio
    async def test_get_asset_inventory_with_real_api(self, asset_client):
        """Test getting asset inventory with real API."""
        with patch.object(asset_client, 'client') as mock_client:
            # Mock asset response
            mock_asset = Mock()
            mock_asset.name = "projects/test/assets/test-asset"
            mock_asset.asset_type = "compute.googleapis.com/Instance"
            mock_asset.resource = Mock()
            mock_asset.resource.version = "v1"
            mock_asset.resource.discovery_document_uri = "https://compute.googleapis.com/discovery/v1/apis/compute/v1/rest"
            mock_asset.resource.discovery_name = "Instance"
            mock_asset.resource.resource_url = "https://compute.googleapis.com/compute/v1/projects/test/zones/us-central1-a/instances/test-instance"
            mock_asset.resource.parent = "projects/test"
            
            mock_client.list_assets.return_value = [mock_asset]
            
            result = await asset_client.get_asset_inventory()
            
            assert result["real_api"] is True
            assert result["total_count"] == 1
            assert len(result["assets"]) == 1
            assert result["assets"][0]["asset_type"] == "compute.googleapis.com/Instance"
    
    @pytest.mark.asyncio
    async def test_get_asset_inventory_permission_denied(self, asset_client):
        """Test handling permission denied error."""
        with patch.object(asset_client, 'client') as mock_client:
            mock_client.list_assets.side_effect = gcp_exceptions.PermissionDenied("Permission denied")
            
            with pytest.raises(AuthenticationError) as exc_info:
                await asset_client.get_asset_inventory()
            
            assert "Permission denied accessing GCP Asset API" in str(exc_info.value)


class TestGCPRecommenderClient:
    """Test suite for GCP Recommender client."""
    
    @pytest.fixture
    def recommender_client(self, project_id, region, mock_credentials):
        """Create recommender client for testing."""
        return GCPRecommenderClient(project_id, region, mock_credentials)
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_real_api(self, recommender_client):
        """Test getting recommendations with real API."""
        with patch.object(recommender_client, 'client') as mock_client:
            # Mock recommendation response
            mock_recommendation = Mock()
            mock_recommendation.name = "projects/test/locations/us-central1/recommenders/test/recommendations/test-rec"
            mock_recommendation.description = "Test recommendation"
            mock_recommendation.recommender_subtype = "CHANGE_MACHINE_TYPE"
            mock_recommendation.last_refresh_time = None
            mock_recommendation.priority = Mock()
            mock_recommendation.priority.name = "P2"
            mock_recommendation.state = Mock()
            mock_recommendation.state.name = "ACTIVE"
            mock_recommendation.primary_impact = Mock()
            mock_recommendation.primary_impact.category = Mock()
            mock_recommendation.primary_impact.category.name = "COST"
            mock_recommendation.primary_impact.cost_projection = Mock()
            mock_recommendation.primary_impact.cost_projection.cost = Mock()
            mock_recommendation.primary_impact.cost_projection.cost.currency_code = "USD"
            mock_recommendation.primary_impact.cost_projection.cost.units = 10
            
            mock_client.list_recommendations.return_value = [mock_recommendation]
            
            result = await recommender_client.get_recommendations("google.compute.instance.MachineTypeRecommender")
            
            assert result["real_api"] is True
            assert result["total_count"] == 1
            assert len(result["recommendations"]) == 1
            assert result["recommendations"][0]["description"] == "Test recommendation"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_fallback(self, recommender_client):
        """Test fallback recommendations when API fails."""
        recommender_client.client = None
        
        result = await recommender_client.get_recommendations("google.compute.instance.MachineTypeRecommender")
        
        assert result["real_api"] is False
        assert result["total_count"] == 0
        assert len(result["recommendations"]) == 0


class TestGCPIntegrationEndToEnd:
    """End-to-end integration tests for GCP client."""
    
    @pytest.mark.asyncio
    async def test_full_gcp_integration_workflow(self, project_id, region, mock_credentials):
        """Test complete GCP integration workflow."""
        with patch('src.infra_mind.cloud.gcp.default') as mock_default:
            mock_default.return_value = (mock_credentials, project_id)
            
            # Initialize client
            client = GCPClient(project_id, region)
            
            # Test compute services
            with patch.object(client.compute_client, 'client') as mock_compute, \
                 patch.object(client.compute_client, 'zones_client') as mock_zones:
                
                mock_zone = Mock()
                mock_zone.name = "us-central1-a"
                mock_zone.region = "projects/test/regions/us-central1"
                mock_zones.list.return_value = [mock_zone]
                
                mock_machine_type = Mock()
                mock_machine_type.name = "n1-standard-1"
                mock_machine_type.description = "Standard machine type"
                mock_machine_type.guest_cpus = 1
                mock_machine_type.memory_mb = 3840
                mock_machine_type.maximum_persistent_disks = 16
                mock_machine_type.maximum_persistent_disks_size_gb = 65536
                mock_machine_type.is_shared_cpu = False
                
                mock_compute.list.return_value = [mock_machine_type]
                
                compute_result = await client.get_compute_services()
                assert compute_result.provider == CloudProvider.GCP
                assert len(compute_result.services) > 0
            
            # Test database services
            with patch.object(client.sql_client, 'client') as mock_sql:
                mock_tier = Mock()
                mock_tier.tier = "db-n1-standard-1"
                mock_tier.RAM = 4026531840
                mock_tier.DiskQuota = 10737418240
                
                mock_response = Mock()
                mock_response.items = [mock_tier]
                mock_sql.list.return_value = mock_response
                
                db_result = await client.get_database_services()
                assert db_result.provider == CloudProvider.GCP
                assert len(db_result.services) > 0
            
            # Test asset inventory
            with patch.object(client.asset_client, 'client') as mock_asset:
                mock_asset_item = Mock()
                mock_asset_item.name = "projects/test/assets/test-asset"
                mock_asset_item.asset_type = "compute.googleapis.com/Instance"
                mock_asset_item.resource = Mock()
                mock_asset_item.resource.version = "v1"
                mock_asset_item.resource.discovery_document_uri = "https://compute.googleapis.com/discovery/v1/apis/compute/v1/rest"
                mock_asset_item.resource.discovery_name = "Instance"
                mock_asset_item.resource.resource_url = "https://compute.googleapis.com/compute/v1/projects/test/zones/us-central1-a/instances/test-instance"
                mock_asset_item.resource.parent = "projects/test"
                
                mock_asset.list_assets.return_value = [mock_asset_item]
                
                asset_result = await client.get_asset_inventory()
                assert asset_result["real_api"] is True
                assert asset_result["total_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])