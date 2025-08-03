"""
Production AWS API Integration Tests.

Tests the enhanced AWS implementation with real API calls, rate limiting,
retry logic, and comprehensive error handling.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.infra_mind.cloud.aws import (
    AWSClient, AWSPricingClient, AWSEC2Client, AWSRDSClient,
    AWSEKSClient, AWSLambdaClient, AWSSageMakerClient, 
    AWSCostExplorerClient, AWSBudgetsClient
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse,
    CloudServiceError, RateLimitError, AuthenticationError
)


class TestAWSProductionIntegration:
    """Test AWS production integration with real API calls."""
    
    @pytest.fixture
    def aws_credentials(self):
        """Get AWS credentials from environment or skip tests."""
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        region = os.getenv('INFRA_MIND_AWS_REGION', 'us-east-1')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for integration tests")
        
        return {
            'access_key': access_key,
            'secret_key': secret_key,
            'region': region
        }
    
    @pytest.fixture
    def aws_client(self, aws_credentials):
        """Create AWS client with real credentials."""
        return AWSClient(
            region=aws_credentials['region'],
            aws_access_key_id=aws_credentials['access_key'],
            aws_secret_access_key=aws_credentials['secret_key']
        )
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_aws_pricing_api(self, aws_credentials):
        """Test real AWS Pricing API integration."""
        pricing_client = AWSPricingClient(
            region=aws_credentials['region'],
            aws_access_key_id=aws_credentials['access_key'],
            aws_secret_access_key=aws_credentials['secret_key']
        )
        
        # Test getting EC2 pricing
        result = await pricing_client.get_service_pricing("AmazonEC2", aws_credentials['region'])
        
        assert result["service_code"] == "AmazonEC2"
        assert result["region"] == aws_credentials['region']
        assert result["real_data"] is True
        assert "products" in result
        assert len(result["products"]) > 0
        assert "pages_fetched" in result
        
        # Verify product structure
        first_product = result["products"][0]
        assert isinstance(first_product, str)  # Products are JSON strings
        
        # Test parsing the product
        import json
        product_data = json.loads(first_product)
        assert "product" in product_data
        assert "terms" in product_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_ec2_instance_types(self, aws_credentials):
        """Test real EC2 instance types API."""
        ec2_client = AWSEC2Client(
            region=aws_credentials['region'],
            aws_access_key_id=aws_credentials['access_key'],
            aws_secret_access_key=aws_credentials['secret_key']
        )
        
        result = await ec2_client.get_instance_types(aws_credentials['region'])
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.COMPUTE
        assert result.region == aws_credentials['region']
        assert len(result.services) > 0
        assert result.metadata["real_api"] is True
        
        # Verify service structure
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AWS
        assert service.category == ServiceCategory.COMPUTE
        assert service.hourly_price is not None
        assert service.hourly_price > 0
        assert "vcpus" in service.specifications
        assert "memory_gb" in service.specifications
        assert service.specifications["vcpus"] > 0
        assert service.specifications["memory_gb"] > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_rds_instances(self, aws_credentials):
        """Test real RDS instances API."""
        rds_client = AWSRDSClient(
            region=aws_credentials['region'],
            aws_access_key_id=aws_credentials['access_key'],
            aws_secret_access_key=aws_credentials['secret_key']
        )
        
        result = await rds_client.get_database_instances(aws_credentials['region'])
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.DATABASE
        assert result.region == aws_credentials['region']
        assert len(result.services) > 0
        assert result.metadata["real_api"] is True
        
        # Verify service structure
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AWS
        assert service.category == ServiceCategory.DATABASE
        assert service.hourly_price is not None
        assert service.hourly_price > 0
        assert service.specifications["engine"] == "mysql"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_aws_client_rate_limiting(self, aws_client):
        """Test AWS client rate limiting functionality."""
        # Test rate limit checking
        await aws_client._check_rate_limit('pricing')
        
        # Verify rate limit history is tracked
        assert 'pricing' in aws_client.api_call_history
        assert len(aws_client.api_call_history['pricing']) == 1
        
        # Test multiple rapid calls
        for _ in range(5):
            await aws_client._check_rate_limit('pricing')
        
        assert len(aws_client.api_call_history['pricing']) == 6
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_aws_client_retry_logic(self, aws_client):
        """Test AWS client retry logic with mocked failures."""
        
        # Mock a function that fails twice then succeeds
        call_count = 0
        async def mock_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ClientError(
                    error_response={'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                    operation_name='TestOperation'
                )
            return {"success": True, "attempt": call_count}
        
        # Test retry logic
        result = await aws_client._execute_with_retry(
            'pricing', 'test_operation', mock_failing_function
        )
        
        assert result["success"] is True
        assert result["attempt"] == 3  # Should succeed on third attempt
        assert call_count == 3
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_aws_client_error_handling(self, aws_client):
        """Test AWS client comprehensive error handling."""
        
        # Test non-retryable error
        async def mock_auth_error():
            raise ClientError(
                error_response={'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Not authorized'}},
                operation_name='TestOperation'
            )
        
        with pytest.raises(CloudServiceError) as exc_info:
            await aws_client._execute_with_retry(
                'pricing', 'test_operation', mock_auth_error
            )
        
        assert exc_info.value.provider == CloudProvider.AWS
        assert exc_info.value.error_code == "UnauthorizedOperation"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_service_discovery(self, aws_client):
        """Test end-to-end service discovery with real APIs."""
        
        # Get compute services
        compute_services = await aws_client.get_compute_services()
        assert len(compute_services.services) > 0
        assert all(s.provider == CloudProvider.AWS for s in compute_services.services)
        assert all(s.category == ServiceCategory.COMPUTE for s in compute_services.services)
        
        # Get storage services
        storage_services = await aws_client.get_storage_services()
        assert len(storage_services.services) >= 2  # S3 and EBS
        assert all(s.provider == CloudProvider.AWS for s in storage_services.services)
        assert all(s.category == ServiceCategory.STORAGE for s in storage_services.services)
        
        # Get database services
        database_services = await aws_client.get_database_services()
        assert len(database_services.services) > 0
        assert all(s.provider == CloudProvider.AWS for s in database_services.services)
        assert all(s.category == ServiceCategory.DATABASE for s in database_services.services)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cost_comparison_workflow(self, aws_client):
        """Test cost comparison workflow with real data."""
        
        compute_services = await aws_client.get_compute_services()
        
        # Find cheapest compute service
        cheapest = compute_services.get_cheapest_service()
        assert cheapest is not None
        assert cheapest.hourly_price > 0
        
        # Calculate monthly costs
        monthly_cost = cheapest.get_monthly_cost()
        assert monthly_cost > 0
        assert monthly_cost == cheapest.hourly_price * 730
        
        # Test service filtering
        high_memory_services = compute_services.filter_by_specs(memory_gb=16)
        if high_memory_services:  # Only test if such services exist
            for service in high_memory_services:
                assert service.specifications["memory_gb"] == 16
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_aws_service_pricing_accuracy(self, aws_client):
        """Test that pricing data is accurate and up-to-date."""
        
        # Get pricing for EC2
        pricing_data = await aws_client.get_service_pricing("AmazonEC2")
        assert pricing_data["real_data"] is True
        assert len(pricing_data["products"]) > 0
        
        # Verify pricing data structure
        import json
        product = json.loads(pricing_data["products"][0])
        
        # Check product structure
        assert "product" in product
        assert "terms" in product
        
        product_info = product["product"]
        assert "attributes" in product_info
        assert "productFamily" in product_info["attributes"]
        
        # Check terms structure
        terms = product["terms"]
        if "OnDemand" in terms:
            on_demand = terms["OnDemand"]
            assert len(on_demand) > 0
            
            # Check price dimensions
            for term_key, term_data in on_demand.items():
                if "priceDimensions" in term_data:
                    price_dims = term_data["priceDimensions"]
                    for price_key, price_data in price_dims.items():
                        if "pricePerUnit" in price_data:
                            price_per_unit = price_data["pricePerUnit"]
                            assert "USD" in price_per_unit
                            # Verify price is a valid number
                            usd_price = float(price_per_unit["USD"])
                            assert usd_price >= 0


class TestAWSErrorHandling:
    """Test AWS error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_credentials_handling(self):
        """Test handling of invalid AWS credentials."""
        
        # Test with clearly invalid credentials (not real credentials)
        with pytest.raises(AuthenticationError) as exc_info:
            AWSClient(
                region="us-east-1",
                aws_access_key_id="AKIA0000000000000000",  # Invalid format but not real
                aws_secret_access_key="0000000000000000000000000000000000000000"  # Invalid format but not real
            )
        
        assert exc_info.value.provider == CloudProvider.AWS
        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
    
    @pytest.mark.asyncio
    async def test_no_credentials_fallback(self):
        """Test fallback behavior when no credentials are provided."""
        
        # Mock boto3 to simulate no credentials
        with patch('boto3.client') as mock_boto:
            mock_boto.side_effect = NoCredentialsError()
            
            with pytest.raises(AuthenticationError):
                AWSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_service_unavailable_handling(self):
        """Test handling of AWS service unavailability."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for service unavailable test")
        
        # Create client with real credentials but mock the service call
        with patch('boto3.client') as mock_boto:
            # Mock successful credential validation
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_boto.return_value = mock_sts
            
            client = AWSClient(
                region="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Mock service unavailable error
            async def mock_service_error():
                raise ClientError(
                    error_response={'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
                    operation_name='TestOperation'
                )
            
            with pytest.raises(CloudServiceError) as exc_info:
                await client._execute_with_retry('pricing', 'test_operation', mock_service_error)
            
            assert exc_info.value.provider == CloudProvider.AWS
            assert exc_info.value.error_code == "ServiceUnavailable"
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handling(self):
        """Test handling of rate limit exceeded scenarios."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for rate limit test")
        
        with patch('boto3.client') as mock_boto:
            # Mock successful credential validation
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_boto.return_value = mock_sts
            
            client = AWSClient(
                region="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Simulate rate limit exceeded by making many rapid calls
            with pytest.raises(RateLimitError):
                for _ in range(25):  # Exceed burst limit
                    await client._check_rate_limit('pricing')


class TestAWSConfigurationValidation:
    """Test AWS configuration and validation."""
    
    def test_boto_config_creation(self):
        """Test that boto3 configuration is created correctly."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for boto config test")
        
        with patch('boto3.client') as mock_boto:
            # Mock successful credential validation
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_boto.return_value = mock_sts
            
            client = AWSClient(
                region="us-west-2",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Verify boto config is set correctly
            assert client.boto_config.region_name == "us-west-2"
            assert client.boto_config.retries['max_attempts'] == 3
            assert client.boto_config.retries['mode'] == 'adaptive'
            assert client.boto_config.read_timeout == 60
            assert client.boto_config.connect_timeout == 10
    
    def test_rate_limit_configuration(self):
        """Test that rate limiting is configured correctly."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for rate limit configuration test")
        
        with patch('boto3.client') as mock_boto:
            # Mock successful credential validation
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_boto.return_value = mock_sts
            
            client = AWSClient(
                region="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Verify rate limits are configured
            assert 'pricing' in client.rate_limits
            assert 'ec2' in client.rate_limits
            assert 'rds' in client.rate_limits
            
            # Verify rate limit structure
            pricing_limits = client.rate_limits['pricing']
            assert 'calls_per_second' in pricing_limits
            assert 'burst' in pricing_limits
            assert pricing_limits['calls_per_second'] > 0
            assert pricing_limits['burst'] > 0
    
    def test_api_call_history_initialization(self):
        """Test that API call history is initialized correctly."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for API call history test")
        
        with patch('boto3.client') as mock_boto:
            # Mock successful credential validation
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_boto.return_value = mock_sts
            
            client = AWSClient(
                region="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Verify API call history is initialized
            assert isinstance(client.api_call_history, dict)
            assert 'pricing' in client.api_call_history
            assert 'ec2' in client.api_call_history
            assert isinstance(client.api_call_history['pricing'], list)
            assert len(client.api_call_history['pricing']) == 0


class TestAWSServiceClients:
    """Test individual AWS service clients."""
    
    @pytest.fixture
    def mock_boto_config(self):
        """Create mock boto config for testing."""
        from botocore.config import Config
        return Config(
            region_name='us-east-1',
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=10
        )
    
    def test_pricing_client_initialization(self, mock_boto_config):
        """Test AWSPricingClient initialization."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for pricing client test")
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.describe_services.return_value = {"Services": []}
            mock_boto.return_value = mock_client
            
            pricing_client = AWSPricingClient(
                region="us-east-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                boto_config=mock_boto_config
            )
            
            assert pricing_client.region == "us-east-1"
            assert pricing_client.boto_client is not None
            
            # Verify boto3 client was called with correct parameters
            mock_boto.assert_called_with(
                'pricing',
                region_name='us-east-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=mock_boto_config
            )
    
    def test_ec2_client_initialization(self, mock_boto_config):
        """Test AWSEC2Client initialization."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for EC2 client test")
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.describe_regions.return_value = {"Regions": []}
            mock_boto.return_value = mock_client
            
            ec2_client = AWSEC2Client(
                region="us-west-2",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                boto_config=mock_boto_config
            )
            
            assert ec2_client.region == "us-west-2"
            assert ec2_client.boto_client is not None
            
            # Verify boto3 client was called with correct parameters
            mock_boto.assert_called_with(
                'ec2',
                region_name='us-west-2',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=mock_boto_config
            )
    
    def test_rds_client_initialization(self, mock_boto_config):
        """Test AWSRDSClient initialization."""
        
        # Skip this test if no real credentials are available
        access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
        
        if not access_key or not secret_key:
            pytest.skip("AWS credentials not available for RDS client test")
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.describe_db_engine_versions.return_value = {"DBEngineVersions": []}
            mock_boto.return_value = mock_client
            
            rds_client = AWSRDSClient(
                region="eu-west-1",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                boto_config=mock_boto_config
            )
            
            assert rds_client.region == "eu-west-1"
            assert rds_client.boto_client is not None
            
            # Verify boto3 client was called with correct parameters
            mock_boto.assert_called_with(
                'rds',
                region_name='eu-west-1',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=mock_boto_config
            )


if __name__ == "__main__":
    # Run integration tests only if AWS credentials are available
    if os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID') and os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY'):
        pytest.main([__file__, "-v", "-m", "integration"])
    else:
        print("AWS credentials not available. Skipping integration tests.")
        pytest.main([__file__, "-v", "-m", "not integration"])