"""
Tests for Real API Integration (Production).

Tests the real API-only cloud integration without mock data fallbacks.
These tests verify proper error handling and real API behavior.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.infra_mind.cloud.azure import AzureClient, AzurePricingClient
from src.infra_mind.cloud.aws import AWSClient
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse, 
    CloudServiceError, AuthenticationError
)


class TestRealAPIIntegration:
    """Test real API integration behavior."""
    
    @pytest.mark.asyncio
    async def test_azure_pricing_api_success(self):
        """Test successful Azure pricing API call."""
        client = AzurePricingClient(region="eastus")
        
        # Mock successful API response
        mock_response_data = {
            "Items": [
                {
                    "serviceName": "Virtual Machines",
                    "productName": "Virtual Machines Bs Series",
                    "skuName": "Standard_B1s",
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
            
            result = await client.get_service_pricing("Virtual Machines", "eastus")
            
            assert result["real_data"] is True
            assert result["service_name"] == "Virtual Machines"
            assert result["region"] == "eastus"
            assert len(result["items"]) == 1
            assert "processed_pricing" in result
    
    @pytest.mark.asyncio
    async def test_azure_pricing_api_failure(self):
        """Test Azure pricing API failure handling."""
        client = AzurePricingClient(region="eastus")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(CloudServiceError) as exc_info:
                await client.get_service_pricing("Virtual Machines", "eastus")
            
            assert exc_info.value.provider == CloudProvider.AZURE
            assert "HTTP_500" in exc_info.value.error_code
    
    @pytest.mark.asyncio
    async def test_azure_pricing_no_data(self):
        """Test Azure pricing API with no valid data."""
        client = AzurePricingClient(region="eastus")
        
        # Mock response with no valid pricing data
        mock_response_data = {
            "Items": [],
            "NextPageLink": None,
            "Count": 0
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(CloudServiceError) as exc_info:
                await client.get_service_pricing("Virtual Machines", "eastus")
            
            assert "NO_PRICING_DATA" in exc_info.value.error_code
    
    @pytest.mark.asyncio
    async def test_azure_compute_real_pricing_integration(self):
        """Test Azure compute service integration with real pricing."""
        client = AzureClient(region="eastus")
        
        # Mock successful pricing API response
        mock_pricing_data = {
            "Items": [
                {
                    "serviceName": "Virtual Machines",
                    "productName": "Virtual Machines Bs Series",
                    "skuName": "Standard_B1s",
                    "retailPrice": 0.0052,
                    "unitOfMeasure": "1 Hour"
                }
            ],
            "Count": 1
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pricing_data
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await client.get_compute_services()
            
            assert isinstance(result, CloudServiceResponse)
            assert result.provider == CloudProvider.AZURE
            assert result.service_category == ServiceCategory.COMPUTE
            assert result.metadata.get("real_pricing") is True
            assert len(result.services) > 0
            
            # Verify service has real pricing
            service = result.services[0]
            assert service.hourly_price == 0.0052
            assert service.service_id == "Standard_B1s"
    
    def test_aws_client_credential_validation(self):
        """Test AWS client credential validation."""
        # Test with no credentials should raise AuthenticationError
        with patch('boto3.client') as mock_boto:
            mock_boto.side_effect = Exception("No credentials")
            
            with pytest.raises(AuthenticationError) as exc_info:
                AWSClient(region="us-east-1")
            
            assert exc_info.value.provider == CloudProvider.AWS
            assert "INVALID_CREDENTIALS" in exc_info.value.error_code
    
    @pytest.mark.asyncio
    async def test_azure_data_validation(self):
        """Test Azure pricing data validation (filtering high prices)."""
        client = AzurePricingClient(region="eastus")
        
        # Mock response with mix of normal and unusually high prices
        mock_pricing_data = {
            "Items": [
                {
                    "serviceName": "Virtual Machines",
                    "productName": "Virtual Machines Bs Series",
                    "skuName": "Standard_B1s",
                    "retailPrice": 0.0052,  # Normal price
                    "unitOfMeasure": "1 Hour"
                },
                {
                    "serviceName": "Virtual Machines",
                    "productName": "Virtual Machines High Memory",
                    "skuName": "Standard_M128ms",
                    "retailPrice": 15000.0,  # Unusually high price (should be filtered)
                    "unitOfMeasure": "1 Hour"
                }
            ],
            "Count": 2
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pricing_data
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await client.get_service_pricing("Virtual Machines", "eastus")
            
            # Should only have the normal priced VM (high price filtered out)
            processed = result["processed_pricing"]
            assert "Standard_B1s" in processed
            assert "Standard_M128ms" not in processed  # Filtered out due to high price
    
    @pytest.mark.asyncio
    async def test_azure_timeout_handling(self):
        """Test Azure API timeout handling."""
        client = AzurePricingClient(region="eastus")
        
        with patch('httpx.AsyncClient') as mock_client:
            # Simulate timeout
            mock_client.return_value.__aenter__.return_value.get.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(CloudServiceError) as exc_info:
                await client.get_service_pricing("Virtual Machines", "eastus")
            
            assert "API_TIMEOUT" in exc_info.value.error_code


class TestProductionReadiness:
    """Test production readiness features."""
    
    def test_error_types_defined(self):
        """Test that proper error types are defined."""
        # Verify error classes exist and have proper inheritance
        assert issubclass(CloudServiceError, Exception)
        assert issubclass(AuthenticationError, CloudServiceError)
    
    @pytest.mark.asyncio
    async def test_no_mock_fallbacks(self):
        """Test that there are no mock data fallbacks in production code."""
        # This test ensures we don't accidentally reintroduce mock fallbacks
        client = AzurePricingClient(region="eastus")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Should raise error, not return mock data
            with pytest.raises(CloudServiceError):
                await client.get_service_pricing("Virtual Machines", "eastus")
    
    def test_cloud_service_response_structure(self):
        """Test CloudServiceResponse has proper structure."""
        services = [
            CloudService(
                provider=CloudProvider.AZURE,
                service_name="Test VM",
                service_id="test_vm",
                category=ServiceCategory.COMPUTE,
                region="eastus",
                hourly_price=0.05
            )
        ]
        
        response = CloudServiceResponse(
            provider=CloudProvider.AZURE,
            service_category=ServiceCategory.COMPUTE,
            region="eastus",
            services=services,
            metadata={"real_pricing": True}
        )
        
        # Test utility methods
        cheapest = response.get_cheapest_service()
        assert cheapest.service_id == "test_vm"
        
        # Test filtering
        filtered = response.filter_by_specs(service_id="test_vm")
        assert len(filtered) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])