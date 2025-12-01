"""
Tests for AWS API integration.

Tests the AWS Pricing API, EC2, RDS, and extended services (EKS, Lambda, SageMaker, Cost Explorer, Budgets).
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud.aws import (
    AWSClient, AWSPricingClient, AWSEC2Client, AWSRDSClient,
    AWSEKSClient, AWSLambdaClient, AWSSageMakerClient, 
    AWSCostExplorerClient, AWSBudgetsClient
)
from src.infra_mind.cloud.base import CloudProvider, ServiceCategory, CloudService, CloudServiceResponse

RUN_CLOUD_TESTS = os.getenv("RUN_CLOUD_INTEGRATION_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_CLOUD_TESTS,
    reason="Cloud integration tests require credentials/network. Set RUN_CLOUD_INTEGRATION_TESTS=1 to enable.",
)


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


class TestAWSEKSClient:
    """Test AWS EKS client."""
    
    @pytest.fixture
    def eks_client(self):
        """Create EKS client for testing."""
        return AWSEKSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_eks_services_mock(self, eks_client):
        """Test getting EKS services with mock data."""
        # Force mock mode
        eks_client.boto_client = None
        
        result = await eks_client.get_eks_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.CONTAINER
        assert result.region == "us-east-1"
        assert len(result.services) >= 3  # Control plane, node groups, Fargate
        
        # Check for control plane service
        control_plane_services = [s for s in result.services if "Control Plane" in s.service_name]
        assert len(control_plane_services) == 1
        assert control_plane_services[0].service_id == "eks_control_plane"
        assert control_plane_services[0].hourly_price == 0.10
        
        # Check for Fargate service
        fargate_services = [s for s in result.services if "Fargate" in s.service_name]
        assert len(fargate_services) == 1
        assert fargate_services[0].service_id == "eks_fargate"
    
    @pytest.mark.asyncio
    async def test_eks_node_group_pricing(self, eks_client):
        """Test EKS node group pricing extraction."""
        eks_client.boto_client = None
        
        result = await eks_client.get_eks_services("us-west-2")
        
        # Check for node group services
        node_services = [s for s in result.services if "Node Group" in s.service_name]
        assert len(node_services) > 0
        
        for service in node_services:
            assert service.hourly_price > 0
            assert "vcpus" in service.specifications
            assert "memory_gb" in service.specifications
            assert "kubernetes" in service.features
    
    def test_fallback_eks_pricing(self, eks_client):
        """Test fallback pricing for EKS instances."""
        price = eks_client._get_fallback_eks_pricing("t3.medium")
        assert price == 0.0416
        
        price = eks_client._get_fallback_eks_pricing("m5.large")
        assert price == 0.096
        
        # Test unknown instance type
        price = eks_client._get_fallback_eks_pricing("unknown.type")
        assert price == 0.05  # Default fallback


class TestAWSLambdaClient:
    """Test AWS Lambda client."""
    
    @pytest.fixture
    def lambda_client(self):
        """Create Lambda client for testing."""
        return AWSLambdaClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_lambda_services_mock(self, lambda_client):
        """Test getting Lambda services with mock data."""
        # Force mock mode
        lambda_client.boto_client = None
        
        result = await lambda_client.get_lambda_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.SERVERLESS
        assert result.region == "us-east-1"
        assert len(result.services) >= 3  # Requests, compute time, provisioned concurrency
        
        # Check for request pricing
        request_services = [s for s in result.services if "Requests" in s.service_name]
        assert len(request_services) == 1
        assert request_services[0].service_id == "lambda_requests"
        assert request_services[0].pricing_unit == "1M requests"
        
        # Check for compute time pricing
        compute_services = [s for s in result.services if "Compute Time" in s.service_name]
        assert len(compute_services) == 1
        assert compute_services[0].service_id == "lambda_compute_time"
        assert compute_services[0].pricing_unit == "GB-second"
    
    @pytest.mark.asyncio
    async def test_lambda_function_list_mock(self, lambda_client):
        """Test listing Lambda functions with mock data."""
        lambda_client.boto_client = None
        
        result = await lambda_client.list_functions()
        
        assert "functions" in result
        assert result["real_data"] is False
        assert len(result["functions"]) >= 2
        
        # Check function structure
        function = result["functions"][0]
        assert "FunctionName" in function
        assert "Runtime" in function
        assert "MemorySize" in function
        assert "Timeout" in function
    
    @pytest.mark.asyncio
    async def test_lambda_error_handling(self, lambda_client):
        """Test Lambda client error handling."""
        lambda_client.boto_client = None
        
        # Test with invalid region
        result = await lambda_client.get_lambda_services("invalid-region")
        assert result.region == "invalid-region"
        assert len(result.services) > 0  # Should still return mock data


class TestAWSSageMakerClient:
    """Test AWS SageMaker client."""
    
    @pytest.fixture
    def sagemaker_client(self):
        """Create SageMaker client for testing."""
        return AWSSageMakerClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_sagemaker_services_mock(self, sagemaker_client):
        """Test getting SageMaker services with mock data."""
        # Force mock mode
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.get_sagemaker_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.AI_ML
        assert result.region == "us-east-1"
        assert len(result.services) >= 4  # Training, hosting, processing, studio
        
        # Check for training instances
        training_services = [s for s in result.services if "Training" in s.service_name]
        assert len(training_services) >= 1
        
        # Check for hosting instances
        hosting_services = [s for s in result.services if "Hosting" in s.service_name]
        assert len(hosting_services) >= 1
        
        # Check for processing instances
        processing_services = [s for s in result.services if "Processing" in s.service_name]
        assert len(processing_services) >= 1
    
    @pytest.mark.asyncio
    async def test_sagemaker_notebook_instances_mock(self, sagemaker_client):
        """Test listing SageMaker notebook instances."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.list_notebook_instances()
        
        assert "notebook_instances" in result
        assert result["real_data"] is False
        assert len(result["notebook_instances"]) >= 1
        
        # Check notebook instance structure
        notebook = result["notebook_instances"][0]
        assert "NotebookInstanceName" in notebook
        assert "InstanceType" in notebook
        assert "NotebookInstanceStatus" in notebook
    
    @pytest.mark.asyncio
    async def test_sagemaker_endpoints_mock(self, sagemaker_client):
        """Test listing SageMaker endpoints."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.list_endpoints()
        
        assert "endpoints" in result
        assert result["real_data"] is False
        assert len(result["endpoints"]) >= 1
        
        # Check endpoint structure
        endpoint = result["endpoints"][0]
        assert "EndpointName" in endpoint
        assert "EndpointStatus" in endpoint
        assert "CreationTime" in endpoint
    
    def test_sagemaker_fallback_pricing(self, sagemaker_client):
        """Test fallback pricing for SageMaker instances."""
        price = sagemaker_client._get_fallback_sagemaker_pricing("ml.t3.medium", "training")
        assert price == 0.0582
        
        price = sagemaker_client._get_fallback_sagemaker_pricing("ml.m5.large", "hosting")
        assert price == 0.115
        
        # Test unknown instance type
        price = sagemaker_client._get_fallback_sagemaker_pricing("ml.unknown.type", "training")
        assert price == 0.10  # Default fallback


class TestAWSCostExplorerClient:
    """Test AWS Cost Explorer client."""
    
    @pytest.fixture
    def cost_explorer_client(self):
        """Create Cost Explorer client for testing."""
        return AWSCostExplorerClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_cost_and_usage_mock(self, cost_explorer_client):
        """Test getting cost and usage data with mock data."""
        # Force mock mode
        cost_explorer_client.boto_client = None
        
        result = await cost_explorer_client.get_cost_and_usage(
            "2024-01-01", "2024-01-31", "MONTHLY"
        )
        
        assert "results_by_time" in result
        assert result["real_data"] is False
        assert len(result["results_by_time"]) >= 1
        
        # Check result structure
        time_period = result["results_by_time"][0]
        assert "time_period" in time_period
        assert "total" in time_period
        assert "groups" in time_period
        
        # Check total cost structure
        total = time_period["total"]
        assert "BlendedCost" in total
        assert "Amount" in total["BlendedCost"]
        assert "Unit" in total["BlendedCost"]
    
    @pytest.mark.asyncio
    async def test_get_dimension_values_mock(self, cost_explorer_client):
        """Test getting dimension values."""
        cost_explorer_client.boto_client = None
        
        result = await cost_explorer_client.get_dimension_values(
            "SERVICE", "2024-01-01", "2024-01-31"
        )
        
        assert "dimension_values" in result
        assert result["real_data"] is False
        assert len(result["dimension_values"]) >= 3
        
        # Check dimension value structure
        dimension = result["dimension_values"][0]
        assert "Value" in dimension
        assert "Attributes" in dimension
    
    @pytest.mark.asyncio
    async def test_get_rightsizing_recommendation_mock(self, cost_explorer_client):
        """Test getting rightsizing recommendations."""
        cost_explorer_client.boto_client = None
        
        result = await cost_explorer_client.get_rightsizing_recommendation()
        
        assert "rightsizing_recommendations" in result
        assert result["real_data"] is False
        assert len(result["rightsizing_recommendations"]) >= 1
        
        # Check recommendation structure
        recommendation = result["rightsizing_recommendations"][0]
        assert "AccountId" in recommendation
        assert "CurrentInstance" in recommendation
        assert "RightsizingType" in recommendation
    
    @pytest.mark.asyncio
    async def test_cost_explorer_error_handling(self, cost_explorer_client):
        """Test Cost Explorer error handling."""
        cost_explorer_client.boto_client = None
        
        # Test with invalid date range
        result = await cost_explorer_client.get_cost_and_usage(
            "invalid-date", "2024-01-31", "MONTHLY"
        )
        assert "results_by_time" in result
        assert result["real_data"] is False


class TestAWSBudgetsClient:
    """Test AWS Budgets client."""
    
    @pytest.fixture
    def budgets_client(self):
        """Create Budgets client for testing."""
        return AWSBudgetsClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_budgets_mock(self, budgets_client):
        """Test getting budgets with mock data."""
        # Force mock mode
        budgets_client.boto_client = None
        
        result = await budgets_client.get_budgets("123456789012")
        
        assert "budgets" in result
        assert result["real_data"] is False
        assert result["account_id"] == "123456789012"
        assert len(result["budgets"]) >= 2
        
        # Check budget structure
        budget = result["budgets"][0]
        assert "BudgetName" in budget
        assert "BudgetLimit" in budget
        assert "TimeUnit" in budget
        assert "BudgetType" in budget
        
        # Check budget limit structure
        limit = budget["BudgetLimit"]
        assert "Amount" in limit
        assert "Unit" in limit
    
    @pytest.mark.asyncio
    async def test_create_budget_mock(self, budgets_client):
        """Test creating a budget."""
        budgets_client.boto_client = None
        
        budget_config = {
            "BudgetName": "Test-Budget",
            "BudgetLimit": {"Amount": "500.00", "Unit": "USD"},
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST"
        }
        
        result = await budgets_client.create_budget("123456789012", budget_config)
        
        assert result["success"] is False  # Mock mode
        assert result["real_data"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_get_budget_performance_mock(self, budgets_client):
        """Test getting budget performance data."""
        budgets_client.boto_client = None
        
        result = await budgets_client.get_budget_performance("123456789012", "Monthly-Cost-Budget")
        
        assert "budget_performance_history" in result
        assert result["real_data"] is False
        assert result["account_id"] == "123456789012"
        assert result["budget_name"] == "Monthly-Cost-Budget"
        
        # Check performance history structure
        history = result["budget_performance_history"]
        assert "BudgetName" in history
        assert "BudgetType" in history
        assert "BudgetedAndActualAmountsList" in history
        
        # Check amounts list
        amounts_list = history["BudgetedAndActualAmountsList"]
        assert len(amounts_list) >= 1
        
        amount_data = amounts_list[0]
        assert "BudgetedAmount" in amount_data
        assert "ActualAmount" in amount_data
        assert "TimePeriod" in amount_data
    
    @pytest.mark.asyncio
    async def test_budgets_error_handling(self, budgets_client):
        """Test Budgets client error handling."""
        budgets_client.boto_client = None
        
        # Test with invalid account ID
        result = await budgets_client.get_budgets("invalid-account")
        assert "budgets" in result
        assert result["real_data"] is False


class TestExtendedAWSClient:
    """Test extended AWS client functionality."""
    
    @pytest.fixture
    def aws_client(self):
        """Create AWS client for testing."""
        return AWSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_get_container_services(self, aws_client):
        """Test getting container services (EKS)."""
        # Mock the EKS client
        aws_client.eks_client.boto_client = None
        
        result = await aws_client.get_container_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.CONTAINER
        assert len(result.services) >= 3
    
    @pytest.mark.asyncio
    async def test_get_serverless_services(self, aws_client):
        """Test getting serverless services (Lambda)."""
        # Mock the Lambda client
        aws_client.lambda_client.boto_client = None
        
        result = await aws_client.get_serverless_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.SERVERLESS
        assert len(result.services) >= 3
    
    @pytest.mark.asyncio
    async def test_get_ml_services(self, aws_client):
        """Test getting ML services (SageMaker)."""
        # Mock the SageMaker client
        aws_client.sagemaker_client.boto_client = None
        
        result = await aws_client.get_ml_services("us-east-1")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AWS
        assert result.service_category == ServiceCategory.AI_ML
        assert len(result.services) >= 4
    
    @pytest.mark.asyncio
    async def test_get_cost_analysis(self, aws_client):
        """Test getting cost analysis."""
        # Mock the Cost Explorer client
        aws_client.cost_explorer_client.boto_client = None
        
        result = await aws_client.get_cost_analysis("2024-01-01", "2024-01-31", "MONTHLY")
        
        assert "results_by_time" in result
        assert result["real_data"] is False
        assert len(result["results_by_time"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_budgets(self, aws_client):
        """Test getting budgets."""
        # Mock the Budgets client
        aws_client.budgets_client.boto_client = None
        
        result = await aws_client.get_budgets("123456789012")
        
        assert "budgets" in result
        assert result["real_data"] is False
        assert len(result["budgets"]) >= 2
    
    @pytest.mark.asyncio
    async def test_create_budget(self, aws_client):
        """Test creating a budget."""
        # Mock the Budgets client
        aws_client.budgets_client.boto_client = None
        
        budget_config = {
            "BudgetName": "Test-Budget",
            "BudgetLimit": {"Amount": "1000.00", "Unit": "USD"},
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST"
        }
        
        result = await aws_client.create_budget("123456789012", budget_config)
        
        assert result["success"] is False  # Mock mode
        assert result["real_data"] is False


class TestExtendedAWSIntegration:
    """Integration tests for extended AWS services."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_service_discovery(self):
        """Test comprehensive service discovery across all AWS services."""
        client = AWSClient(region="us-east-1")
        
        # Force mock mode for all clients
        client.pricing_client.boto_client = None
        client.ec2_client.boto_client = None
        client.rds_client.boto_client = None
        client.eks_client.boto_client = None
        client.lambda_client.boto_client = None
        client.sagemaker_client.boto_client = None
        client.cost_explorer_client.boto_client = None
        client.budgets_client.boto_client = None
        
        # Get all service types
        compute_services = await client.get_compute_services()
        storage_services = await client.get_storage_services()
        database_services = await client.get_database_services()
        container_services = await client.get_container_services()
        serverless_services = await client.get_serverless_services()
        ml_services = await client.get_ml_services()
        
        # Verify we got services from all categories
        assert len(compute_services.services) > 0
        assert len(storage_services.services) > 0
        assert len(database_services.services) > 0
        assert len(container_services.services) > 0
        assert len(serverless_services.services) > 0
        assert len(ml_services.services) > 0
        
        # Verify service categories
        assert compute_services.service_category == ServiceCategory.COMPUTE
        assert storage_services.service_category == ServiceCategory.STORAGE
        assert database_services.service_category == ServiceCategory.DATABASE
        assert container_services.service_category == ServiceCategory.CONTAINER
        assert serverless_services.service_category == ServiceCategory.SERVERLESS
        assert ml_services.service_category == ServiceCategory.AI_ML
    
    @pytest.mark.asyncio
    async def test_cost_management_workflow(self):
        """Test cost management workflow with Cost Explorer and Budgets."""
        client = AWSClient(region="us-east-1")
        
        # Force mock mode
        client.cost_explorer_client.boto_client = None
        client.budgets_client.boto_client = None
        
        # Get cost analysis
        cost_analysis = await client.get_cost_analysis("2024-01-01", "2024-01-31", "MONTHLY")
        assert "results_by_time" in cost_analysis
        
        # Get budgets
        budgets = await client.get_budgets("123456789012")
        assert "budgets" in budgets
        assert len(budgets["budgets"]) >= 2
        
        # Create a new budget
        budget_config = {
            "BudgetName": "Integration-Test-Budget",
            "BudgetLimit": {"Amount": "2000.00", "Unit": "USD"},
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST"
        }
        
        create_result = await client.create_budget("123456789012", budget_config)
        assert "success" in create_result
    
    @pytest.mark.asyncio
    async def test_ml_workflow_integration(self):
        """Test ML workflow integration with SageMaker services."""
        client = AWSClient(region="us-east-1")
        client.sagemaker_client.boto_client = None
        
        # Get ML services
        ml_services = await client.get_ml_services()
        
        # Find training instances
        training_services = [s for s in ml_services.services if "Training" in s.service_name]
        assert len(training_services) > 0
        
        # Find hosting instances
        hosting_services = [s for s in ml_services.services if "Hosting" in s.service_name]
        assert len(hosting_services) > 0
        
        # Verify all ML services have proper pricing
        for service in ml_services.services:
            assert service.hourly_price > 0
            assert service.category == ServiceCategory.AI_ML
    
    @pytest.mark.asyncio
    async def test_container_orchestration_workflow(self):
        """Test container orchestration workflow with EKS."""
        client = AWSClient(region="us-east-1")
        client.eks_client.boto_client = None
        
        # Get container services
        container_services = await client.get_container_services()
        
        # Find EKS control plane
        control_plane_services = [s for s in container_services.services if "Control Plane" in s.service_name]
        assert len(control_plane_services) == 1
        assert control_plane_services[0].hourly_price == 0.10
        
        # Find EKS node groups
        node_services = [s for s in container_services.services if "Node Group" in s.service_name]
        assert len(node_services) > 0
        
        # Find Fargate services
        fargate_services = [s for s in container_services.services if "Fargate" in s.service_name]
        assert len(fargate_services) == 1
        
        # Calculate total EKS cost for a basic setup
        control_plane_cost = control_plane_services[0].get_monthly_cost()
        cheapest_node = min(node_services, key=lambda s: s.hourly_price)
        node_cost = cheapest_node.get_monthly_cost()
        
        total_monthly_cost = control_plane_cost + node_cost
        assert total_monthly_cost > 0
    
    @pytest.mark.asyncio
    async def test_serverless_cost_optimization(self):
        """Test serverless cost optimization with Lambda."""
        client = AWSClient(region="us-east-1")
        client.lambda_client.boto_client = None
        
        # Get serverless services
        serverless_services = await client.get_serverless_services()
        
        # Find Lambda request pricing
        request_services = [s for s in serverless_services.services if "Requests" in s.service_name]
        assert len(request_services) == 1
        
        # Find Lambda compute time pricing
        compute_services = [s for s in serverless_services.services if "Compute Time" in s.service_name]
        assert len(compute_services) == 1
        
        # Verify pricing units are correct
        assert request_services[0].pricing_unit == "1M requests"
        assert compute_services[0].pricing_unit == "GB-second"
    
    def test_error_handling_across_services(self):
        """Test error handling across all extended services."""
        client = AWSClient(region="us-east-1")
        
        # Test that all service clients are properly initialized
        assert client.eks_client is not None
        assert client.lambda_client is not None
        assert client.sagemaker_client is not None
        assert client.cost_explorer_client is not None
        assert client.budgets_client is not None
        
        # Test that all clients handle missing credentials gracefully
        assert hasattr(client.eks_client, 'boto_client')
        assert hasattr(client.lambda_client, 'boto_client')
        assert hasattr(client.sagemaker_client, 'boto_client')
        assert hasattr(client.cost_explorer_client, 'boto_client')
        assert hasattr(client.budgets_client, 'boto_client')


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
