"""
Tests for AWS API integration.

Tests the AWS Pricing API, EC2, and RDS clients.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud.aws import AWSClient, AWSPricingClient, AWSEC2Client, AWSRDSClient
from src.infra_mind.cloud.base import CloudProvider, ServiceCategory, CloudService, CloudServiceResponse


class TestAWSPricingClient:
    """Test AWS Pricing API client."""
    
    @pytest.fixture
    def pricing_client(self):
        """Create pricing client for testing."""
        return AWSPricingClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_mock_data(self, pricing_client):
        """Test getting mock pricing data when no credentials."""
        # Force mock mode by setting boto_client to None
        pricing_client.boto_client = None
        
        result = await pricing_client.get_service_pricing("AmazonEC2", "us-east-1")
        
        assert result["service_code"] == "AmazonEC2"
        assert result["region"] == "us-east-1"
        assert result["mock_data"] is True
        assert "pricing_data" in result
        assert "t3.micro" in result["pricing_data"]
    
    @pytest.mark.asyncio
    async def test_get_service_pricing_rds_mock(self, pricing_client):
        """Test getting RDS pricing data."""
        pricing_client.boto_client = None
        
        result = await pricing_client.get_service_pricing("AmazonRDS", "us-east-1")
        
        assert result["service_code"] == "AmazonRDS"
        assert "db.t3.micro" in result["pricing_data"]
        assert result["pricing_data"]["db.t3.micro"]["hourly"] == 0.017
    
    def test_region_to_location_mapping(self, pricing_client):
        """Test region to location mapping."""
        assert pricing_client._region_to_location("us-east-1") == "US East (N. Virginia)"
        assert pricing_client._region_to_location("us-west-2") == "US West (Oregon)"
        assert pricing_client._region_to_location("unknown-region") == "unknown-region"


class TestAWSEC2Client:
    """Test AWS EC2 client."""
    
    @pytest.fixture
    def ec2_client(self):
        """Create EC2 client for testing."""
        return AWSEC2Client(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_instance_types_mock(self, ec2_client):
        """Test getting EC2 instance types with mock data."""
        # Force mock mode
        ec2_client.boto_client = None
        
        result = await ec2_client.get_instance_types("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.COMPUTE
        assert result.region == "us-east-1"
        assert len(result.services) > 0
        
        # Check first service
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AWS
        assert service.category == ServiceCategory.COMPUTE
        assert service.service_id == "t3.micro"
        assert service.hourly_price == 0.0104
        assert "vcpus" in service.specifications
        assert "memory_gb" in service.specifications
    
    @pytest.mark.asyncio
    async def test_mock_ec2_instances_structure(self, ec2_client):
        """Test the structure of mock EC2 instances."""
        ec2_client.boto_client = None
        
        result = await ec2_client.get_instance_types("us-west-2")
        
        # Verify all services have required fields
        for service in result.services:
            assert service.service_name.startswith("Amazon EC2")
            assert service.hourly_price is not None
            assert service.specifications["vcpus"] > 0
            assert service.specifications["memory_gb"] > 0
            assert "network_performance" in service.specifications
            assert len(service.features) > 0


class TestAWSRDSClient:
    """Test AWS RDS client."""
    
    @pytest.fixture
    def rds_client(self):
        """Create RDS client for testing."""
        return AWSRDSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_database_instances_mock(self, rds_client):
        """Test getting RDS instances with mock data."""
        # Force mock mode
        rds_client.boto_client = None
        
        result = await rds_client.get_database_instances("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.DATABASE
        assert result.region == "us-east-1"
        assert len(result.services) > 0
        
        # Check first service
        service = result.services[0]
        assert isinstance(service, CloudService)
        assert service.provider == CloudProvider.AWS
        assert service.category == ServiceCategory.DATABASE
        assert service.service_id == "db.t3.micro"
        assert service.hourly_price == 0.017
        assert service.specifications["engine"] == "mysql"
    
    @pytest.mark.asyncio
    async def test_mock_rds_instances_features(self, rds_client):
        """Test RDS instances have expected features."""
        rds_client.boto_client = None
        
        result = await rds_client.get_database_instances("eu-west-1")
        
        for service in result.services:
            assert "automated_backups" in service.features
            assert "multi_az" in service.features
            assert "encryption" in service.features
            assert service.specifications["engine_version"] == "8.0"


class TestAWSClient:
    """Test main AWS client."""
    
    @pytest.fixture
    def aws_client(self):
        """Create AWS client for testing."""
        return AWSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_compute_services(self, aws_client):
        """Test getting compute services."""
        # Mock the EC2 client
        aws_client.ec2_client.boto_client = None
        
        result = await aws_client.get_compute_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.COMPUTE
        assert len(result.services) > 0
    
    @pytest.mark.asyncio
    async def test_get_storage_services(self, aws_client):
        """Test getting storage services."""
        result = await aws_client.get_storage_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.STORAGE
        assert len(result.services) >= 2  # S3 and EBS
        
        # Check for S3 service
        s3_services = [s for s in result.services if s.service_id == "s3"]
        assert len(s3_services) == 1
        assert s3_services[0].service_name == "Amazon S3"
        
        # Check for EBS service
        ebs_services = [s for s in result.services if s.service_id == "ebs_gp3"]
        assert len(ebs_services) == 1
        assert ebs_services[0].hourly_price == 0.08
    
    @pytest.mark.asyncio
    async def test_get_database_services(self, aws_client):
        """Test getting database services."""
        # Mock the RDS client
        aws_client.rds_client.boto_client = None
        
        result = await aws_client.get_database_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.DATABASE
        assert len(result.services) > 0
    
    @pytest.mark.asyncio
    async def test_get_service_pricing(self, aws_client):
        """Test getting service pricing."""
        # Mock the pricing client
        aws_client.pricing_client.boto_client = None
        
        result = await aws_client.get_service_pricing("AmazonEC2", "us-east-1")
        
        assert result["service_code"] == "AmazonEC2"
        assert result["region"] == "us-east-1"
        assert "pricing_data" in result


class TestAWSIntegration:
    """Integration tests for AWS services."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_service_discovery(self):
        """Test end-to-end service discovery workflow."""
        client = AWSClient(region="us-east-1")
        
        # Force mock mode for all clients
        client.pricing_client.boto_client = None
        client.ec2_client.boto_client = None
        client.rds_client.boto_client = None
        
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
            assert service.provider == CloudProvider.AWS
            assert service.region == "us-east-1"
            assert service.service_name
            assert service.service_id
            assert service.category in [ServiceCategory.COMPUTE, ServiceCategory.STORAGE, ServiceCategory.DATABASE]
    
    @pytest.mark.asyncio
    async def test_cost_comparison_workflow(self):
        """Test cost comparison workflow."""
        client = AWSClient(region="us-east-1")
        client.ec2_client.boto_client = None
        
        compute_services = await client.get_compute_services()
        
        # Find cheapest compute service
        cheapest = compute_services.get_cheapest_service()
        assert cheapest is not None
        assert cheapest.service_id == "t3.micro"  # Should be cheapest in mock data
        assert cheapest.hourly_price == 0.0104
        
        # Calculate monthly costs
        monthly_cost = cheapest.get_monthly_cost()
        assert monthly_cost == 0.0104 * 730  # Default 730 hours per month
    
    @pytest.mark.asyncio
    async def test_service_filtering(self):
        """Test service filtering by specifications."""
        client = AWSClient(region="us-east-1")
        client.ec2_client.boto_client = None
        
        compute_services = await client.get_compute_services()
        
        # Filter by memory
        high_memory_services = compute_services.filter_by_specs(memory_gb=16)
        assert len(high_memory_services) > 0
        
        for service in high_memory_services:
            assert service.specifications["memory_gb"] == 16
    
    def test_cloud_service_response_utilities(self):
        """Test CloudServiceResponse utility methods."""
        # Create test services
        services = [
            CloudService(
                provider=CloudProvider.AWS,
                service_name="Test Service 1",
                service_id="test1",
                category=ServiceCategory.COMPUTE,
                region="us-east-1",
                hourly_price=0.1,
                specifications={"vcpus": 2, "memory_gb": 4}
            ),
            CloudService(
                provider=CloudProvider.AWS,
                service_name="Test Service 2",
                service_id="test2",
                category=ServiceCategory.COMPUTE,
                region="us-east-1",
                hourly_price=0.05,
                specifications={"vcpus": 1, "memory_gb": 2}
            )
        ]
        
        response = CloudServiceResponse(
            provider=CloudProvider.AWS,
            service_category=ServiceCategory.COMPUTE,
            region="us-east-1",
            services=services
        )
        
        # Test cheapest service
        cheapest = response.get_cheapest_service()
        assert cheapest.service_id == "test2"
        assert cheapest.hourly_price == 0.05
        
        # Test filtering
        filtered = response.filter_by_specs(vcpus=2)
        assert len(filtered) == 1
        assert filtered[0].service_id == "test1"


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])