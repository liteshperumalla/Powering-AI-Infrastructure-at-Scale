"""
Comprehensive tests for AWS extended services (EKS, Lambda, SageMaker, Cost Explorer, Budgets).

This module provides comprehensive testing and error handling validation for the complete AWS API suite.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

from src.infra_mind.cloud.aws import (
    AWSClient, AWSEKSClient, AWSLambdaClient, AWSSageMakerClient, 
    AWSCostExplorerClient, AWSBudgetsClient
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse,
    CloudServiceError, RateLimitError, AuthenticationError
)


class TestAWSEKSClientComprehensive:
    """Comprehensive tests for AWS EKS client."""
    
    @pytest.fixture
    def eks_client(self):
        """Create EKS client for testing."""
        return AWSEKSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_eks_services_comprehensive_structure(self, eks_client):
        """Test comprehensive EKS services structure."""
        eks_client.boto_client = None
        
        result = await eks_client.get_eks_services("us-east-1")
        
        # Verify control plane service
        control_plane = next((s for s in result.services if s.service_id == "eks_control_plane"), None)
        assert control_plane is not None
        assert control_plane.hourly_price == 0.10
        assert control_plane.specifications["kubernetes_version"] == "1.28"
        assert control_plane.specifications["high_availability"] is True
        assert "auto_scaling" in control_plane.features
        
        # Verify Fargate service
        fargate = next((s for s in result.services if s.service_id == "eks_fargate"), None)
        assert fargate is not None
        assert fargate.specifications["serverless"] is True
        assert fargate.specifications["max_vcpu_per_pod"] == 4
        assert "serverless" in fargate.features
    
    @pytest.mark.asyncio
    async def test_eks_error_handling_no_credentials(self, eks_client):
        """Test EKS error handling when no credentials available."""
        eks_client.boto_client = None
        
        # Should still return mock data
        result = await eks_client.get_eks_services("us-west-2")
        assert isinstance(result, CloudServiceResponse)
        assert len(result.services) >= 2
        assert result.metadata["real_api"] is False
    
    @pytest.mark.asyncio
    async def test_eks_pricing_fallback_mechanism(self, eks_client):
        """Test EKS pricing fallback mechanism."""
        # Test known instance types
        assert eks_client._get_fallback_eks_pricing("t3.medium") == 0.0416
        assert eks_client._get_fallback_eks_pricing("m5.large") == 0.096
        assert eks_client._get_fallback_eks_pricing("c5.xlarge") == 0.17
        
        # Test unknown instance type
        assert eks_client._get_fallback_eks_pricing("unknown.type") is None
    
    @pytest.mark.asyncio
    async def test_eks_node_group_specifications(self, eks_client):
        """Test EKS node group specifications are complete."""
        eks_client.boto_client = None
        
        result = await eks_client.get_eks_services("eu-west-1")
        
        node_services = [s for s in result.services if "Node Group" in s.service_name]
        for service in node_services:
            assert "instance_type" in service.specifications
            assert "vcpus" in service.specifications
            assert "memory_gb" in service.specifications
            assert "managed_node_group" in service.specifications
            assert service.specifications["managed_node_group"] is True
            assert "auto_scaling" in service.features
            assert "spot_instances" in service.features
    
    @pytest.mark.asyncio
    async def test_eks_api_error_simulation(self, eks_client):
        """Test EKS API error handling."""
        with patch.object(eks_client, 'boto_client') as mock_client:
            mock_client.list_clusters.side_effect = ClientError(
                {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                'ListClusters'
            )
            
            # Should handle error gracefully and return mock data
            result = await eks_client.get_eks_services("us-east-1")
            assert isinstance(result, CloudServiceResponse)
            assert len(result.services) >= 2


class TestAWSLambdaClientComprehensive:
    """Comprehensive tests for AWS Lambda client."""
    
    @pytest.fixture
    def lambda_client(self):
        """Create Lambda client for testing."""
        return AWSLambdaClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_lambda_services_comprehensive_structure(self, lambda_client):
        """Test comprehensive Lambda services structure."""
        lambda_client.boto_client = None
        
        result = await lambda_client.get_lambda_services("us-east-1")
        
        # Verify request pricing service
        request_service = next((s for s in result.services if s.service_id == "lambda_requests"), None)
        assert request_service is not None
        assert request_service.pricing_model == "per_request"
        assert request_service.specifications["free_tier_requests"] == 1000000
        assert request_service.specifications["max_execution_time"] == "15 minutes"
        assert "auto_scaling" in request_service.features
        
        # Verify duration services for different memory configurations
        duration_services = [s for s in result.services if "Duration" in s.service_name]
        assert len(duration_services) >= 7  # Different memory configurations
        
        for service in duration_services:
            assert "memory_mb" in service.specifications
            assert "memory_gb" in service.specifications
            assert service.specifications["billing_increment"] == "100ms"
            assert service.specifications["free_tier_gb_seconds"] == 400000
    
    @pytest.mark.asyncio
    async def test_lambda_provisioned_concurrency_pricing(self, lambda_client):
        """Test Lambda provisioned concurrency pricing."""
        lambda_client.boto_client = None
        
        result = await lambda_client.get_lambda_services("us-east-1")
        
        provisioned_service = next((s for s in result.services if "Provisioned Concurrency" in s.service_name), None)
        assert provisioned_service is not None
        assert provisioned_service.service_id == "lambda_provisioned_concurrency"
        assert provisioned_service.pricing_model == "provisioned"
        assert provisioned_service.specifications["cold_start_elimination"] is True
        assert "no_cold_starts" in provisioned_service.features
    
    @pytest.mark.asyncio
    async def test_lambda_edge_service(self, lambda_client):
        """Test Lambda@Edge service configuration."""
        lambda_client.boto_client = None
        
        result = await lambda_client.get_lambda_services("us-east-1")
        
        edge_service = next((s for s in result.services if s.service_id == "lambda_edge"), None)
        assert edge_service is not None
        assert edge_service.specifications["edge_locations"] == 400
        assert edge_service.specifications["max_execution_time"] == "30 seconds"
        assert edge_service.specifications["global_distribution"] is True
        assert "edge_computing" in edge_service.features
    
    @pytest.mark.asyncio
    async def test_lambda_memory_configuration_pricing(self, lambda_client):
        """Test Lambda memory configuration pricing calculations."""
        lambda_client.boto_client = None
        
        result = await lambda_client.get_lambda_services("us-east-1")
        
        # Test specific memory configurations
        duration_128mb = next((s for s in result.services if "Duration (128MB)" in s.service_name), None)
        duration_1024mb = next((s for s in result.services if "Duration (1024MB)" in s.service_name), None)
        
        assert duration_128mb is not None
        assert duration_1024mb is not None
        
        # 1024MB should cost 8x more than 128MB (8x memory)
        assert duration_1024mb.hourly_price == duration_128mb.hourly_price * 8
    
    @pytest.mark.asyncio
    async def test_lambda_error_handling_comprehensive(self, lambda_client):
        """Test comprehensive Lambda error handling."""
        with patch.object(lambda_client, 'boto_client') as mock_client:
            # Test different error scenarios
            mock_client.list_functions.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'ListFunctions'
            )
            
            # Should handle throttling gracefully
            result = await lambda_client.get_lambda_services("us-east-1")
            assert isinstance(result, CloudServiceResponse)
            assert len(result.services) > 0


class TestAWSSageMakerClientComprehensive:
    """Comprehensive tests for AWS SageMaker client."""
    
    @pytest.fixture
    def sagemaker_client(self):
        """Create SageMaker client for testing."""
        return AWSSageMakerClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_sagemaker_training_instances_comprehensive(self, sagemaker_client):
        """Test comprehensive SageMaker training instances."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.get_sagemaker_services("us-east-1")
        
        training_services = [s for s in result.services if "Training" in s.service_name]
        assert len(training_services) >= 11  # Various instance types
        
        # Test GPU instances
        gpu_services = [s for s in training_services if s.specifications.get("gpu_enabled")]
        assert len(gpu_services) >= 4  # p3.2xlarge, p3.8xlarge, g4dn.xlarge, g4dn.2xlarge
        
        for gpu_service in gpu_services:
            assert gpu_service.specifications["gpu_enabled"] is True
            assert gpu_service.hourly_price > 0.5  # GPU instances are more expensive
            assert "distributed_training" in gpu_service.features
    
    @pytest.mark.asyncio
    async def test_sagemaker_inference_endpoints_comprehensive(self, sagemaker_client):
        """Test comprehensive SageMaker inference endpoints."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.get_sagemaker_services("us-east-1")
        
        inference_services = [s for s in result.services if "Inference" in s.service_name]
        assert len(inference_services) >= 9  # Various instance types
        
        # Test Inferentia instances
        inferentia_services = [s for s in inference_services if s.specifications.get("inferentia_enabled")]
        assert len(inferentia_services) >= 1
        
        for inf_service in inferentia_services:
            assert inf_service.specifications["inferentia_enabled"] is True
            assert "real_time_inference" in inf_service.features
    
    @pytest.mark.asyncio
    async def test_sagemaker_serverless_inference(self, sagemaker_client):
        """Test SageMaker serverless inference configuration."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.get_sagemaker_services("us-east-1")
        
        serverless_service = next((s for s in result.services if "Serverless Inference" in s.service_name), None)
        assert serverless_service is not None
        assert serverless_service.service_id == "sagemaker_serverless_inference"
        assert serverless_service.specifications["serverless"] is True
        assert serverless_service.specifications["max_memory"] == "6GB"
        assert serverless_service.specifications["max_concurrent_invocations"] == 1000
        assert "pay_per_use" in serverless_service.features
    
    @pytest.mark.asyncio
    async def test_sagemaker_studio_and_data_wrangler(self, sagemaker_client):
        """Test SageMaker Studio and Data Wrangler services."""
        sagemaker_client.boto_client = None
        
        result = await sagemaker_client.get_sagemaker_services("us-east-1")
        
        # Test Studio service
        studio_service = next((s for s in result.services if s.service_id == "sagemaker_studio"), None)
        assert studio_service is not None
        assert studio_service.specifications["ide_type"] == "jupyter_lab"
        assert studio_service.specifications["collaborative"] is True
        assert "collaboration" in studio_service.features
        
        # Test Data Wrangler service
        data_wrangler_service = next((s for s in result.services if s.service_id == "sagemaker_data_wrangler"), None)
        assert data_wrangler_service is not None
        assert data_wrangler_service.specifications["built_in_transformations"] == 300
        assert "S3" in data_wrangler_service.specifications["data_sources"]
        assert "visual_data_prep" in data_wrangler_service.features
    
    @pytest.mark.asyncio
    async def test_sagemaker_error_handling_comprehensive(self, sagemaker_client):
        """Test comprehensive SageMaker error handling."""
        with patch.object(sagemaker_client, 'boto_client') as mock_client:
            mock_client.list_training_jobs.side_effect = ClientError(
                {'Error': {'Code': 'ValidationException', 'Message': 'Invalid parameter'}},
                'ListTrainingJobs'
            )
            
            # Should handle validation errors gracefully
            result = await sagemaker_client.get_sagemaker_services("us-east-1")
            assert isinstance(result, CloudServiceResponse)
            assert len(result.services) > 0


class TestAWSCostExplorerClientComprehensive:
    """Comprehensive tests for AWS Cost Explorer client."""
    
    @pytest.fixture
    def cost_explorer_client(self):
        """Create Cost Explorer client for testing."""
        return AWSCostExplorerClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_cost_and_usage_comprehensive_structure(self, cost_explorer_client):
        """Test comprehensive cost and usage data structure."""
        cost_explorer_client.boto_client = None
        
        result = await cost_explorer_client.get_cost_and_usage(
            "2024-01-01", "2024-01-31", "MONTHLY"
        )
        
        assert "cost_data" in result
        assert "time_period" in result
        assert result["time_period"]["start"] == "2024-01-01"
        assert result["time_period"]["end"] == "2024-01-31"
        assert result["granularity"] == "MONTHLY"
        assert result["real_data"] is False
        
        # Verify cost data structure
        cost_data = result["cost_data"][0]
        assert "TimePeriod" in cost_data
        assert "Total" in cost_data
        assert "Groups" in cost_data
        
        # Verify groups structure
        groups = cost_data["Groups"]
        assert len(groups) >= 2
        for group in groups:
            assert "Keys" in group
            assert "Metrics" in group
            assert "BlendedCost" in group["Metrics"]
    
    @pytest.mark.asyncio
    async def test_usage_forecast_comprehensive(self, cost_explorer_client):
        """Test comprehensive usage forecast functionality."""
        cost_explorer_client.boto_client = None
        
        result = await cost_explorer_client.get_usage_forecast(
            "2024-02-01", "2024-02-29", "BLENDED_COST"
        )
        
        assert "forecast_results" in result
        assert "total" in result
        assert result["metric"] == "BLENDED_COST"
        assert result["real_data"] is False
        
        # Verify forecast structure
        forecast = result["forecast_results"][0]
        assert "MeanValue" in forecast
        assert "PredictionIntervalLowerBound" in forecast
        assert "PredictionIntervalUpperBound" in forecast
        assert "TimePeriod" in forecast
        
        # Verify prediction intervals make sense
        mean_value = float(forecast["MeanValue"])
        lower_bound = float(forecast["PredictionIntervalLowerBound"])
        upper_bound = float(forecast["PredictionIntervalUpperBound"])
        
        assert lower_bound <= mean_value <= upper_bound
    
    @pytest.mark.asyncio
    async def test_cost_explorer_different_granularities(self, cost_explorer_client):
        """Test Cost Explorer with different granularities."""
        cost_explorer_client.boto_client = None
        
        # Test DAILY granularity
        daily_result = await cost_explorer_client.get_cost_and_usage(
            "2024-01-01", "2024-01-07", "DAILY"
        )
        assert daily_result["granularity"] == "DAILY"
        
        # Test MONTHLY granularity
        monthly_result = await cost_explorer_client.get_cost_and_usage(
            "2024-01-01", "2024-03-31", "MONTHLY"
        )
        assert monthly_result["granularity"] == "MONTHLY"
    
    @pytest.mark.asyncio
    async def test_cost_explorer_error_handling_comprehensive(self, cost_explorer_client):
        """Test comprehensive Cost Explorer error handling."""
        with patch.object(cost_explorer_client, 'boto_client') as mock_client:
            mock_client.get_cost_and_usage.side_effect = ClientError(
                {'Error': {'Code': 'DataUnavailableException', 'Message': 'Data not available'}},
                'GetCostAndUsage'
            )
            
            # Should handle data unavailable errors gracefully
            with pytest.raises(CloudServiceError) as exc_info:
                await cost_explorer_client.get_cost_and_usage("2024-01-01", "2024-01-31")
            
            assert exc_info.value.error_code == "COST_EXPLORER_API_ERROR"


class TestAWSBudgetsClientComprehensive:
    """Comprehensive tests for AWS Budgets client."""
    
    @pytest.fixture
    def budgets_client(self):
        """Create Budgets client for testing."""
        return AWSBudgetsClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_budgets_comprehensive_structure(self, budgets_client):
        """Test comprehensive budgets data structure."""
        budgets_client.boto_client = None
        
        result = await budgets_client.get_budgets("123456789012")
        
        assert "budgets" in result
        assert result["account_id"] == "123456789012"
        assert result["real_data"] is False
        assert len(result["budgets"]) >= 2
        
        # Verify budget structure
        budget = result["budgets"][0]
        assert "BudgetName" in budget
        assert "BudgetLimit" in budget
        assert "TimeUnit" in budget
        assert "BudgetType" in budget
        assert "TimePeriod" in budget
        
        # Verify budget limit structure
        limit = budget["BudgetLimit"]
        assert "Amount" in limit
        assert "Unit" in limit
        assert limit["Unit"] == "USD"
        
        # Verify time period structure
        time_period = budget["TimePeriod"]
        assert "Start" in time_period
        assert "End" in time_period
    
    @pytest.mark.asyncio
    async def test_budget_performance_comprehensive(self, budgets_client):
        """Test comprehensive budget performance data."""
        budgets_client.boto_client = None
        
        result = await budgets_client.get_budget_performance("123456789012", "Monthly-Cost-Budget")
        
        assert "budget_performance_history" in result
        assert result["account_id"] == "123456789012"
        assert result["budget_name"] == "Monthly-Cost-Budget"
        assert result["real_data"] is False
        
        # Verify performance history structure
        history = result["budget_performance_history"]
        assert "BudgetName" in history
        assert "BudgetType" in history
        assert "BudgetedAndActualAmountsList" in history
        
        # Verify amounts list structure
        amounts_list = history["BudgetedAndActualAmountsList"]
        assert len(amounts_list) >= 1
        
        amount_data = amounts_list[0]
        assert "BudgetedAmount" in amount_data
        assert "ActualAmount" in amount_data
        assert "TimePeriod" in amount_data
        
        # Verify amount structure
        budgeted = amount_data["BudgetedAmount"]
        actual = amount_data["ActualAmount"]
        assert "Amount" in budgeted
        assert "Unit" in budgeted
        assert "Amount" in actual
        assert "Unit" in actual
    
    @pytest.mark.asyncio
    async def test_create_budget_comprehensive(self, budgets_client):
        """Test comprehensive budget creation."""
        budgets_client.boto_client = None
        
        budget_config = {
            "BudgetName": "Test-ML-Budget",
            "BudgetLimit": {"Amount": "2000.00", "Unit": "USD"},
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST",
            "CostFilters": {
                "Service": ["Amazon SageMaker"]
            },
            "TimePeriod": {
                "Start": "2024-01-01",
                "End": "2087-06-15"
            }
        }
        
        result = await budgets_client.create_budget("123456789012", budget_config)
        
        assert result["success"] is False  # Mock mode
        assert result["real_data"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_budgets_error_handling_comprehensive(self, budgets_client):
        """Test comprehensive Budgets error handling."""
        with patch.object(budgets_client, 'boto_client') as mock_client:
            # Test access denied error
            mock_client.describe_budgets.side_effect = ClientError(
                {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
                'DescribeBudgets'
            )
            
            # Should handle access denied gracefully and return mock data
            result = await budgets_client.get_budgets("123456789012")
            assert "budgets" in result
            assert result["real_data"] is False
            
            # Test not found error for budget performance
            mock_client.describe_budget_performance_history.side_effect = ClientError(
                {'Error': {'Code': 'NotFoundException', 'Message': 'Budget not found'}},
                'DescribeBudgetPerformanceHistory'
            )
            
            result = await budgets_client.get_budget_performance("123456789012", "NonExistent-Budget")
            assert "error" in result
            assert "not found" in result["error"]
            assert result["real_data"] is True


class TestAWSExtendedIntegration:
    """Integration tests for all extended AWS services."""
    
    @pytest.fixture
    def aws_client(self):
        """Create AWS client for testing."""
        with patch.object(AWSClient, '_validate_credentials'):
            return AWSClient(region="us-east-1")
    
    @pytest.mark.asyncio
    async def test_all_extended_services_integration(self, aws_client):
        """Test integration of all extended AWS services."""
        # Mock all clients
        aws_client.eks_client.boto_client = None
        aws_client.lambda_client.boto_client = None
        aws_client.sagemaker_client.boto_client = None
        aws_client.cost_explorer_client.boto_client = None
        aws_client.budgets_client.boto_client = None
        
        # Test all service categories
        container_services = await aws_client.get_container_services("us-east-1")
        serverless_services = await aws_client.get_serverless_services("us-east-1")
        ml_services = await aws_client.get_ml_services("us-east-1")
        cost_analysis = await aws_client.get_cost_analysis("2024-01-01", "2024-01-31")
        budgets = await aws_client.get_budgets("123456789012")
        
        # Verify all services returned successfully
        assert isinstance(container_services, CloudServiceResponse)
        assert isinstance(serverless_services, CloudServiceResponse)
        assert isinstance(ml_services, CloudServiceResponse)
        assert isinstance(cost_analysis, dict)
        assert isinstance(budgets, dict)
        
        # Verify service counts
        assert len(container_services.services) >= 2  # EKS Control Plane + Fargate
        assert len(serverless_services.services) >= 10
        assert len(ml_services.services) >= 15
        assert "cost_data" in cost_analysis
        assert "budgets" in budgets
    
    @pytest.mark.asyncio
    async def test_service_category_consistency(self, aws_client):
        """Test service category consistency across all extended services."""
        # Mock all clients
        aws_client.eks_client.boto_client = None
        aws_client.lambda_client.boto_client = None
        aws_client.sagemaker_client.boto_client = None
        
        container_services = await aws_client.get_container_services("us-east-1")
        serverless_services = await aws_client.get_serverless_services("us-east-1")
        ml_services = await aws_client.get_ml_services("us-east-1")
        
        # Verify service categories
        for service in container_services.services:
            assert service.category == ServiceCategory.CONTAINERS
        
        for service in serverless_services.services:
            assert service.category == ServiceCategory.SERVERLESS
        
        for service in ml_services.services:
            assert service.category == ServiceCategory.MACHINE_LEARNING
    
    @pytest.mark.asyncio
    async def test_pricing_consistency_across_services(self, aws_client):
        """Test pricing consistency across all extended services."""
        # Mock all clients
        aws_client.eks_client.boto_client = None
        aws_client.lambda_client.boto_client = None
        aws_client.sagemaker_client.boto_client = None
        
        container_services = await aws_client.get_container_services("us-east-1")
        serverless_services = await aws_client.get_serverless_services("us-east-1")
        ml_services = await aws_client.get_ml_services("us-east-1")
        
        all_services = (container_services.services + 
                       serverless_services.services + 
                       ml_services.services)
        
        # Verify all services have valid pricing
        for service in all_services:
            assert service.hourly_price is not None
            assert service.hourly_price >= 0
            assert service.pricing_unit is not None
            assert service.pricing_model is not None
    
    @pytest.mark.asyncio
    async def test_error_resilience_across_all_services(self, aws_client):
        """Test error resilience across all extended services."""
        # Simulate various error conditions
        with patch.object(aws_client.eks_client, 'boto_client') as mock_eks:
            with patch.object(aws_client.lambda_client, 'boto_client') as mock_lambda:
                with patch.object(aws_client.sagemaker_client, 'boto_client') as mock_sagemaker:
                    
                    # Set up different error scenarios
                    mock_eks.list_clusters.side_effect = ClientError(
                        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                        'ListClusters'
                    )
                    mock_lambda.list_functions.side_effect = ClientError(
                        {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                        'ListFunctions'
                    )
                    mock_sagemaker.list_training_jobs.side_effect = ClientError(
                        {'Error': {'Code': 'ValidationException', 'Message': 'Invalid parameter'}},
                        'ListTrainingJobs'
                    )
                    
                    # All services should handle errors gracefully
                    container_services = await aws_client.get_container_services("us-east-1")
                    serverless_services = await aws_client.get_serverless_services("us-east-1")
                    ml_services = await aws_client.get_ml_services("us-east-1")
                    
                    # Verify services still returned (with mock data)
                    assert len(container_services.services) > 0
                    assert len(serverless_services.services) > 0
                    assert len(ml_services.services) > 0


class TestAWSServiceSpecifications:
    """Test AWS service specifications and features."""
    
    @pytest.mark.asyncio
    async def test_service_specifications_completeness(self):
        """Test that all services have complete specifications."""
        with patch.object(AWSClient, '_validate_credentials'):
            client = AWSClient(region="us-east-1")
        
        # Mock all clients
        client.eks_client.boto_client = None
        client.lambda_client.boto_client = None
        client.sagemaker_client.boto_client = None
        
        # Get all services
        all_responses = [
            await client.get_container_services("us-east-1"),
            await client.get_serverless_services("us-east-1"),
            await client.get_ml_services("us-east-1")
        ]
        
        for response in all_responses:
            for service in response.services:
                # Verify required fields
                assert service.service_name
                assert service.service_id
                assert service.description
                assert service.specifications is not None
                assert service.features is not None
                assert len(service.features) > 0
                
                # Verify pricing information
                assert service.hourly_price is not None
                assert service.pricing_model is not None
                assert service.pricing_unit is not None
    
    @pytest.mark.asyncio
    async def test_service_features_consistency(self):
        """Test service features consistency."""
        with patch.object(AWSClient, '_validate_credentials'):
            client = AWSClient(region="us-east-1")
        
        # Mock all clients
        client.eks_client.boto_client = None
        client.lambda_client.boto_client = None
        client.sagemaker_client.boto_client = None
        
        # Test EKS services
        eks_services = await client.get_container_services("us-east-1")
        for service in eks_services.services:
            if "Control Plane" in service.service_name:
                assert "auto_scaling" in service.features
                assert "logging" in service.features
            elif "Fargate" in service.service_name:
                assert "serverless" in service.features
                assert "security_isolation" in service.features
        
        # Test Lambda services
        lambda_services = await client.get_serverless_services("us-east-1")
        for service in lambda_services.services:
            # Different Lambda services have different features based on their purpose
            if "Provisioned Concurrency" in service.service_name:
                assert "no_cold_starts" in service.features
                assert "predictable_performance" in service.features
            elif "Edge" in service.service_name:
                assert "edge_computing" in service.features
                assert "global_distribution" in service.features
            elif "Duration" in service.service_name or "Requests" in service.service_name:
                assert "auto_scaling" in service.features
        
        # Test SageMaker services
        ml_services = await client.get_ml_services("us-east-1")
        for service in ml_services.services:
            # All services should have at least one feature
            assert len(service.features) > 0
            
            if "Training" in service.service_name:
                # Training services should have training-related features
                training_features = ["managed_training", "distributed_training", "spot_training"]
                assert any(feature in service.features for feature in training_features)
            elif "Inference" in service.service_name:
                # Inference services should have inference-related features
                inference_features = ["real_time_inference", "serverless", "auto_scaling"]
                assert any(feature in service.features for feature in inference_features)
            elif "Serverless" in service.service_name:
                assert "serverless" in service.features
                assert "pay_per_use" in service.features


if __name__ == "__main__":
    pytest.main([__file__, "-v"])