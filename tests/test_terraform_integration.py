"""
Tests for Terraform API integration.

This module tests the Terraform Cloud API and Terraform Registry API clients
to ensure they can fetch cost estimation and provider information correctly.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from src.infra_mind.cloud.terraform import (
    TerraformClient, TerraformCloudClient, TerraformRegistryClient,
    TerraformProvider
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudServiceError,
    AuthenticationError, RateLimitError
)


class TestTerraformRegistryClient:
    """Test Terraform Registry API client."""
    
    @pytest.fixture
    def registry_client(self):
        """Create a Terraform Registry client for testing."""
        return TerraformRegistryClient()
    
    @pytest.mark.asyncio
    async def test_get_providers_success(self, registry_client):
        """Test successful provider retrieval from registry."""
        mock_response_data = {
            "data": [
                {
                    "attributes": {
                        "namespace": "hashicorp",
                        "name": "aws",
                        "full-name": "hashicorp/aws",
                        "description": "The Amazon Web Services (AWS) provider",
                        "source": "https://github.com/hashicorp/terraform-provider-aws",
                        "downloads": 1000000,
                        "published-at": "2023-01-01T00:00:00Z"
                    }
                },
                {
                    "attributes": {
                        "namespace": "hashicorp",
                        "name": "azurerm",
                        "full-name": "hashicorp/azurerm",
                        "description": "The Azure Resource Manager provider",
                        "source": "https://github.com/hashicorp/terraform-provider-azurerm",
                        "downloads": 800000,
                        "published-at": "2023-01-01T00:00:00Z"
                    }
                }
            ]
        }
        
        with patch.object(registry_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await registry_client.get_providers()
            
            assert "providers" in result
            assert len(result["providers"]) == 2
            assert result["providers"][0]["namespace"] == "hashicorp"
            assert result["providers"][0]["name"] == "aws"
            assert result["providers"][1]["name"] == "azurerm"
            assert result["total_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_providers_with_namespace(self, registry_client):
        """Test provider retrieval with specific namespace."""
        mock_response_data = {
            "data": {
                "attributes": {
                    "namespace": "hashicorp",
                    "name": "aws",
                    "full-name": "hashicorp/aws",
                    "description": "The Amazon Web Services (AWS) provider",
                    "source": "https://github.com/hashicorp/terraform-provider-aws",
                    "downloads": 1000000,
                    "published-at": "2023-01-01T00:00:00Z"
                }
            }
        }
        
        with patch.object(registry_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await registry_client.get_providers(namespace="hashicorp")
            
            assert "providers" in result
            assert len(result["providers"]) == 1
            assert result["providers"][0]["namespace"] == "hashicorp"
            assert result["namespace"] == "hashicorp"
    
    @pytest.mark.asyncio
    async def test_get_modules_success(self, registry_client):
        """Test successful module retrieval from registry."""
        mock_response_data = {
            "modules": [
                {
                    "namespace": "terraform-aws-modules",
                    "name": "vpc",
                    "provider": "aws",
                    "description": "Terraform module to create VPC resources on AWS",
                    "source": "https://github.com/terraform-aws-modules/terraform-aws-vpc",
                    "downloads": 500000,
                    "published_at": "2023-01-01T00:00:00Z",
                    "verified": True,
                    "version": "3.14.0"
                },
                {
                    "namespace": "terraform-aws-modules",
                    "name": "ec2-instance",
                    "provider": "aws",
                    "description": "Terraform module to create EC2 instances on AWS",
                    "source": "https://github.com/terraform-aws-modules/terraform-aws-ec2-instance",
                    "downloads": 300000,
                    "published_at": "2023-01-01T00:00:00Z",
                    "verified": True,
                    "version": "4.1.4"
                }
            ]
        }
        
        with patch.object(registry_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await registry_client.get_modules(provider="aws")
            
            assert "modules" in result
            assert len(result["modules"]) == 2
            assert result["modules"][0]["name"] == "vpc"
            assert result["modules"][1]["name"] == "ec2-instance"
            assert result["provider"] == "aws"
    
    @pytest.mark.asyncio
    async def test_get_compute_modules(self, registry_client):
        """Test compute module retrieval and processing."""
        mock_aws_response = {
            "modules": [
                {
                    "namespace": "terraform-aws-modules",
                    "name": "ec2-instance",
                    "provider": "aws",
                    "description": "Terraform module to create EC2 instances",
                    "downloads": 300000,
                    "verified": True,
                    "version": "4.1.4"
                }
            ]
        }
        
        mock_azure_response = {
            "modules": [
                {
                    "namespace": "Azure",
                    "name": "compute",
                    "provider": "azurerm",
                    "description": "Terraform module for Azure compute resources",
                    "downloads": 150000,
                    "verified": True,
                    "version": "1.2.0"
                }
            ]
        }
        
        mock_gcp_response = {
            "modules": [
                {
                    "namespace": "terraform-google-modules",
                    "name": "vm",
                    "provider": "google",
                    "description": "Terraform module for GCP compute instances",
                    "downloads": 100000,
                    "verified": True,
                    "version": "7.9.0"
                }
            ]
        }
        
        with patch.object(registry_client, 'get_modules') as mock_get_modules:
            mock_get_modules.side_effect = [
                mock_aws_response,
                mock_azure_response,
                mock_gcp_response
            ]
            
            result = await registry_client.get_compute_modules()
            
            assert result.service_category == ServiceCategory.COMPUTE
            assert len(result.services) == 3
            
            # Check AWS service
            aws_service = next(s for s in result.services if s.provider == CloudProvider.AWS)
            assert "ec2-instance" in aws_service.service_name
            assert aws_service.category == ServiceCategory.COMPUTE
            
            # Check Azure service
            azure_service = next(s for s in result.services if s.provider == CloudProvider.AZURE)
            assert "compute" in azure_service.service_name
            
            # Check GCP service
            gcp_service = next(s for s in result.services if s.provider == CloudProvider.GCP)
            assert "vm" in gcp_service.service_name
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, registry_client):
        """Test handling of rate limit errors."""
        with patch.object(registry_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            # Mock the HTTPStatusError
            from httpx import HTTPStatusError, Request, Response
            mock_request = Request("GET", "https://example.com")
            mock_http_response = Response(429, request=mock_request)
            mock_client.get.side_effect = HTTPStatusError(
                "Rate limit exceeded", 
                request=mock_request, 
                response=mock_http_response
            )
            
            with pytest.raises(RateLimitError):
                await registry_client.get_providers()


class TestTerraformCloudClient:
    """Test Terraform Cloud API client."""
    
    @pytest.fixture
    def cloud_client(self):
        """Create a Terraform Cloud client for testing."""
        return TerraformCloudClient(
            terraform_token="test-token",
            organization="test-org"
        )
    
    @pytest.mark.asyncio
    async def test_get_cost_estimation_success(self, cloud_client):
        """Test successful cost estimation retrieval."""
        mock_response_data = {
            "data": {
                "attributes": {
                    "status": "finished",
                    "monthly-cost": "150.00",
                    "prior-monthly-cost": "100.00",
                    "delta-monthly-cost": "50.00",
                    "currency": "USD",
                    "resources": [
                        {
                            "name": "aws_instance.example",
                            "monthly_cost": "75.00"
                        }
                    ]
                }
            }
        }
        
        with patch.object(cloud_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await cloud_client.get_cost_estimation("run-123")
            
            assert result["run_id"] == "run-123"
            assert result["status"] == "finished"
            assert result["monthly_cost"] == "150.00"
            assert result["delta_monthly_cost"] == "50.00"
            assert result["currency"] == "USD"
            assert len(result["resources"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_cost_estimation_not_available(self, cloud_client):
        """Test cost estimation when not available."""
        with patch.object(cloud_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await cloud_client.get_cost_estimation("run-123")
            
            assert result["cost_estimate"] is None
            assert "not available" in result["message"]
            assert result["run_id"] == "run-123"
    
    @pytest.mark.asyncio
    async def test_create_workspace_success(self, cloud_client):
        """Test successful workspace creation."""
        workspace_config = {
            "name": "test-workspace",
            "description": "Test workspace for InfraMind",
            "terraform_version": "1.5.0",
            "auto_apply": False
        }
        
        mock_response_data = {
            "data": {
                "id": "ws-123",
                "attributes": {
                    "name": "test-workspace",
                    "description": "Test workspace for InfraMind",
                    "terraform-version": "1.5.0",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:00:00Z"
                }
            }
        }
        
        with patch.object(cloud_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_session.return_value = mock_client
            
            result = await cloud_client.create_workspace(workspace_config)
            
            assert result["id"] == "ws-123"
            assert result["name"] == "test-workspace"
            assert result["description"] == "Test workspace for InfraMind"
            assert result["terraform_version"] == "1.5.0"
            assert result["organization"] == "test-org"
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, cloud_client):
        """Test handling of authentication errors."""
        with patch.object(cloud_client, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client.get.return_value = mock_response
            mock_session.return_value = mock_client
            
            # Mock the HTTPStatusError
            from httpx import HTTPStatusError, Request, Response
            mock_request = Request("GET", "https://example.com")
            mock_http_response = Response(401, request=mock_request)
            mock_client.get.side_effect = HTTPStatusError(
                "Unauthorized", 
                request=mock_request, 
                response=mock_http_response
            )
            
            with pytest.raises(AuthenticationError):
                await cloud_client.get_cost_estimation("run-123")


class TestTerraformClient:
    """Test main Terraform client facade."""
    
    @pytest.fixture
    def terraform_client(self):
        """Create a Terraform client for testing."""
        return TerraformClient(
            terraform_token="test-token",
            organization="test-org"
        )
    
    @pytest.mark.asyncio
    async def test_get_compute_services(self, terraform_client):
        """Test compute services retrieval through main client."""
        mock_response = MagicMock()
        mock_response.services = []
        mock_response.service_category = ServiceCategory.COMPUTE
        
        with patch.object(terraform_client.registry_client, 'get_compute_modules', return_value=mock_response):
            result = await terraform_client.get_compute_services()
            
            assert result.service_category == ServiceCategory.COMPUTE
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_without_token(self):
        """Test pricing retrieval without authentication token."""
        client = TerraformClient()  # No token provided
        
        with pytest.raises(AuthenticationError):
            await client.get_service_pricing("run-123")
    
    @pytest.mark.asyncio
    async def test_get_providers(self, terraform_client):
        """Test provider retrieval through main client."""
        mock_response = {
            "providers": [
                {"namespace": "hashicorp", "name": "aws"},
                {"namespace": "hashicorp", "name": "azurerm"}
            ],
            "total_count": 2
        }
        
        with patch.object(terraform_client.registry_client, 'get_providers', return_value=mock_response):
            result = await terraform_client.get_providers()
            
            assert "providers" in result
            assert result["total_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_modules(self, terraform_client):
        """Test module retrieval through main client."""
        mock_response = {
            "modules": [
                {"name": "vpc", "provider": "aws"},
                {"name": "ec2-instance", "provider": "aws"}
            ],
            "total_count": 2
        }
        
        with patch.object(terraform_client.registry_client, 'get_modules', return_value=mock_response):
            result = await terraform_client.get_modules(provider="aws")
            
            assert "modules" in result
            assert result["total_count"] == 2


class TestTerraformIntegration:
    """Integration tests for Terraform API clients."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self):
        """Test a complete workflow simulation."""
        # This test simulates a full workflow without making real API calls
        client = TerraformClient(terraform_token="test-token", organization="test-org")
        
        # Mock all external calls
        with patch.object(client.registry_client, 'get_providers') as mock_providers, \
             patch.object(client.registry_client, 'get_modules') as mock_modules, \
             patch.object(client.cloud_client, 'create_workspace') as mock_workspace, \
             patch.object(client.cloud_client, 'run_plan') as mock_plan:
            
            # Setup mock responses
            mock_providers.return_value = {
                "providers": [{"namespace": "hashicorp", "name": "aws"}],
                "total_count": 1
            }
            
            mock_modules.return_value = {
                "modules": [{"name": "vpc", "provider": "aws"}],
                "total_count": 1
            }
            
            mock_workspace.return_value = {
                "id": "ws-123",
                "name": "test-workspace"
            }
            
            mock_plan.return_value = {
                "run_id": "run-123",
                "status": "planned",
                "cost_estimation": {"monthly_cost": "100.00"}
            }
            
            # Execute workflow
            providers = await client.get_providers()
            modules = await client.get_modules(provider="aws")
            workspace = await client.create_workspace({"name": "test-workspace"})
            plan = await client.run_plan("ws-123", {"message": "Test plan"})
            
            # Verify results
            assert providers["total_count"] == 1
            assert modules["total_count"] == 1
            assert workspace["id"] == "ws-123"
            assert plan["run_id"] == "run-123"
    
    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test error handling across the client chain."""
        client = TerraformClient(terraform_token="invalid-token", organization="test-org")
        
        with patch.object(client.cloud_client, 'get_cost_estimation') as mock_cost:
            mock_cost.side_effect = AuthenticationError(
                "Invalid token", CloudProvider.AWS, "INVALID_TOKEN"
            )
            
            with pytest.raises(AuthenticationError):
                await client.get_service_pricing("run-123")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])