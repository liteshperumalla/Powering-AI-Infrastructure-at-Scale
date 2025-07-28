"""
Tests for Extended Azure API Suite.

Tests the Azure Resource Manager, AKS, Machine Learning, and Cost Management clients
with advanced integration features.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.cloud.azure import (
    AzureClient, AzureResourceManagerClient, AzureAKSClient, 
    AzureMachineLearningClient, AzureCostManagementClient
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudService, CloudServiceResponse, CloudServiceError
)


class TestAzureResourceManagerClient:
    """Test Azure Resource Manager API client."""
    
    @pytest.fixture
    def resource_manager_client(self):
        """Create Resource Manager client for testing."""
        return AzureResourceManagerClient(
            region="eastus",
            subscription_id="test-subscription-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_get_resource_groups_mock_mode(self, resource_manager_client):
        """Test getting resource groups in mock mode."""
        # Force mock mode
        resource_manager_client.use_mock_data = True
        
        result = await resource_manager_client.get_resource_groups("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.MANAGEMENT
        assert result.region == "eastus"
        assert len(result.services) > 0
        
        # Check for Azure Resource Manager service
        arm_service = next((s for s in result.services if "Resource Manager" in s.service_name), None)
        assert arm_service is not None
        assert arm_service.pricing_model == "free"
        assert arm_service.hourly_price == 0.0
    
    @pytest.mark.asyncio
    async def test_get_advisor_recommendations_mock_mode(self, resource_manager_client):
        """Test getting Azure Advisor recommendations."""
        # Force mock mode
        resource_manager_client.use_mock_data = True
        
        result = await resource_manager_client.get_advisor_recommendations("all")
        
        assert isinstance(result, dict)
        assert "recommendations" in result
        assert "summary" in result
        assert "categories" in result
        
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "title" in rec
            assert "description" in rec
            assert "category" in rec
            assert "impact" in rec
            assert rec["category"] in ["Cost", "Performance", "Security", "Reliability"]
    
    @pytest.mark.asyncio
    async def test_get_resource_health_mock_mode(self, resource_manager_client):
        """Test getting resource health information."""
        # Force mock mode
        resource_manager_client.use_mock_data = True
        
        result = await resource_manager_client.get_resource_health()
        
        assert isinstance(result, dict)
        assert "overall_health" in result
        assert "resource_health_summary" in result
        assert "service_health" in result
        
        assert result["overall_health"]["status"] in ["healthy", "warning", "critical"]
        assert "healthy_resources" in result["overall_health"]
        assert "unhealthy_resources" in result["overall_health"]


class TestAzureAKSClient:
    """Test Azure Kubernetes Service (AKS) client."""
    
    @pytest.fixture
    def aks_client(self):
        """Create AKS client for testing."""
        return AzureAKSClient(
            region="eastus",
            subscription_id="test-subscription-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_get_aks_services_mock_mode(self, aks_client):
        """Test getting AKS services in mock mode."""
        # Force mock mode
        aks_client.use_mock_data = True
        
        result = await aks_client.get_aks_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.CONTAINER
        assert result.region == "eastus"
        assert len(result.services) > 0
        
        # Check for AKS Control Plane service
        control_plane = next((s for s in result.services if "Control Plane" in s.service_name), None)
        assert control_plane is not None
        assert control_plane.pricing_model == "free"
        assert control_plane.hourly_price == 0.0
        assert "managed_control_plane" in control_plane.features
        
        # Check for node pool services
        node_pools = [s for s in result.services if "Node Pool" in s.service_name]
        assert len(node_pools) > 0
        
        for node_pool in node_pools:
            assert node_pool.category == ServiceCategory.CONTAINER
            assert "vcpus" in node_pool.specifications
            assert "memory_gb" in node_pool.specifications
            assert node_pool.hourly_price > 0
    
    @pytest.mark.asyncio
    async def test_get_aks_services_with_real_pricing(self, aks_client):
        """Test getting AKS services with real VM pricing."""
        # Mock the pricing client to return real-looking data
        mock_pricing_data = {
            "Standard_B2s": {
                "hourly": 0.0416,
                "monthly": 30.368,
                "unit": "1 Hour",
                "product": "Virtual Machines"
            },
            "Standard_D2s_v3": {
                "hourly": 0.096,
                "monthly": 70.08,
                "unit": "1 Hour", 
                "product": "Virtual Machines"
            }
        }
        
        with patch.object(aks_client, '_get_mock_aks_services') as mock_method:
            # Mock the method to use real pricing
            mock_method.return_value = await aks_client._get_aks_services_with_real_pricing("eastus", mock_pricing_data)
            
            result = await aks_client.get_aks_services("eastus")
            
            assert isinstance(result, CloudServiceResponse)
            assert len(result.services) > 0
            
            # Check that some services have real pricing
            priced_services = [s for s in result.services if s.hourly_price > 0]
            assert len(priced_services) > 0


class TestAzureMachineLearningClient:
    """Test Azure Machine Learning service client."""
    
    @pytest.fixture
    def ml_client(self):
        """Create ML client for testing."""
        return AzureMachineLearningClient(
            region="eastus",
            subscription_id="test-subscription-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_get_ml_services_mock_mode(self, ml_client):
        """Test getting ML services in mock mode."""
        # Force mock mode
        ml_client.use_mock_data = True
        
        result = await ml_client.get_ml_services("eastus")
        
        assert isinstance(result, CloudServiceResponse)
        assert result.provider == CloudProvider.AZURE
        assert result.service_category == ServiceCategory.MACHINE_LEARNING
        assert result.region == "eastus"
        assert len(result.services) > 0
        
        # Check for ML Workspace service
        workspace = next((s for s in result.services if "Workspace" in s.service_name), None)
        assert workspace is not None
        assert workspace.pricing_model == "free"
        assert workspace.hourly_price == 0.0
        assert "experiment_tracking" in workspace.features
        
        # Check for compute instances
        compute_instances = [s for s in result.services if "Compute" in s.service_name]
        assert len(compute_instances) > 0
        
        for compute in compute_instances:
            assert compute.category == ServiceCategory.MACHINE_LEARNING
            assert "vcpus" in compute.specifications
            assert "memory_gb" in compute.specifications
    
    @pytest.mark.asyncio
    async def test_get_ml_services_with_real_pricing(self, ml_client):
        """Test getting ML services with real VM pricing."""
        # Mock the pricing client to return real-looking data
        mock_pricing_data = {
            "Standard_DS3_v2": {
                "hourly": 0.192,
                "monthly": 140.16,
                "unit": "1 Hour",
                "product": "Virtual Machines"
            },
            "Standard_NC6s_v3": {
                "hourly": 3.06,
                "monthly": 2233.8,
                "unit": "1 Hour",
                "product": "Virtual Machines"
            }
        }
        
        with patch.object(ml_client, '_get_mock_ml_services') as mock_method:
            # Mock the method to use real pricing
            mock_method.return_value = await ml_client._get_ml_services_with_real_pricing("eastus", mock_pricing_data)
            
            result = await ml_client.get_ml_services("eastus")
            
            assert isinstance(result, CloudServiceResponse)
            assert len(result.services) > 0
            
            # Check that some services have real pricing
            priced_services = [s for s in result.services if s.hourly_price > 0]
            assert len(priced_services) > 0


class TestAzureCostManagementClient:
    """Test Azure Cost Management and Billing API client."""
    
    @pytest.fixture
    def cost_client(self):
        """Create Cost Management client for testing."""
        return AzureCostManagementClient(
            region="eastus",
            subscription_id="test-subscription-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_get_cost_analysis_mock_mode(self, cost_client):
        """Test getting cost analysis in mock mode."""
        # Force mock mode
        cost_client.use_mock_data = True
        
        result = await cost_client.get_cost_analysis("subscription", "month")
        
        assert isinstance(result, dict)
        assert "total_cost" in result
        assert "currency" in result
        assert "time_period" in result
        assert "cost_by_service" in result
        assert "cost_by_resource_group" in result
        assert "cost_trend" in result
        assert "budget_status" in result
        assert "cost_optimization_opportunities" in result
        
        assert result["currency"] == "USD"
        assert result["time_period"] == "month"
        assert result["total_cost"] > 0
        
        # Check cost breakdown
        cost_by_service = result["cost_by_service"]
        assert "Virtual Machines" in cost_by_service
        assert "Storage" in cost_by_service
        assert "SQL Database" in cost_by_service
        
        # Check optimization opportunities
        opportunities = result["cost_optimization_opportunities"]
        assert len(opportunities) > 0
        
        for opp in opportunities:
            assert "category" in opp
            assert "potential_savings" in opp
            assert "description" in opp
            assert "implementation_effort" in opp
    
    @pytest.mark.asyncio
    async def test_get_budget_alerts_mock_mode(self, cost_client):
        """Test getting budget alerts."""
        # Force mock mode
        cost_client.use_mock_data = True
        
        result = await cost_client.get_budget_alerts()
        
        assert isinstance(result, dict)
        assert "active_alerts" in result
        assert "budget_summary" in result
        assert "alert_history" in result
        
        # Check budget summary
        budget_summary = result["budget_summary"]
        assert "total_budgets" in budget_summary
        assert "budgets_on_track" in budget_summary
        assert "budgets_at_risk" in budget_summary
        
        # Check active alerts
        active_alerts = result["active_alerts"]
        for alert in active_alerts:
            assert "budget_name" in alert
            assert "alert_type" in alert
            assert "threshold_percentage" in alert
            assert "current_spend" in alert


class TestAzureClientAdvancedFeatures:
    """Test advanced Azure integration features."""
    
    @pytest.fixture
    def azure_client(self):
        """Create Azure client for testing."""
        return AzureClient(
            region="eastus",
            subscription_id="test-subscription-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analysis(self, azure_client):
        """Test comprehensive Azure analysis."""
        # Mock all the individual service calls
        with patch.object(azure_client, 'get_compute_services') as mock_compute, \
             patch.object(azure_client, 'get_storage_services') as mock_storage, \
             patch.object(azure_client, 'get_database_services') as mock_database, \
             patch.object(azure_client, 'get_ai_services') as mock_ai, \
             patch.object(azure_client, 'get_aks_services') as mock_aks, \
             patch.object(azure_client, 'get_machine_learning_services') as mock_ml, \
             patch.object(azure_client, 'get_cost_analysis') as mock_cost, \
             patch.object(azure_client, 'get_resource_recommendations') as mock_recommendations, \
             patch.object(azure_client, 'get_budget_alerts') as mock_budget, \
             patch.object(azure_client, 'get_resource_health') as mock_health:
            
            # Set up mock returns
            mock_compute.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.COMPUTE, "eastus", [])
            mock_storage.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.STORAGE, "eastus", [])
            mock_database.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.DATABASE, "eastus", [])
            mock_ai.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.AI_ML, "eastus", [])
            mock_aks.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.CONTAINER, "eastus", [])
            mock_ml.return_value = CloudServiceResponse(CloudProvider.AZURE, ServiceCategory.MACHINE_LEARNING, "eastus", [])
            mock_cost.return_value = {"total_cost": 1000, "currency": "USD"}
            mock_recommendations.return_value = {"recommendations": []}
            mock_budget.return_value = {"active_alerts": []}
            mock_health.return_value = {"overall_health": {"status": "healthy"}}
            
            result = await azure_client.get_comprehensive_analysis("eastus")
            
            assert isinstance(result, dict)
            assert "region" in result
            assert "timestamp" in result
            assert "services" in result
            assert "cost_analysis" in result
            assert "recommendations" in result
            assert "budget_alerts" in result
            assert "resource_health" in result
            assert "summary" in result
            
            assert result["region"] == "eastus"
            assert result["services"]["compute"] is not None
            assert result["services"]["storage"] is not None
            assert result["services"]["database"] is not None
    
    @pytest.mark.asyncio
    async def test_get_multi_region_analysis(self, azure_client):
        """Test multi-region analysis feature."""
        regions = ["eastus", "westus2", "northeurope"]
        
        # Mock the comprehensive analysis for each region
        with patch.object(azure_client, 'get_comprehensive_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "services": {"compute": {"services": []}, "storage": {"services": []}},
                "cost_analysis": {"total_cost": 1000, "cost_by_service": {"Virtual Machines": 600}},
                "recommendations": {"recommendations": []},
                "summary": {"total_services_analyzed": 5}
            }
            
            result = await azure_client.get_multi_region_analysis(regions)
            
            assert isinstance(result, dict)
            assert "regions_analyzed" in result
            assert "region_analyses" in result
            assert "cross_region_insights" in result
            assert "recommendations" in result
            assert "metadata" in result
            
            assert result["regions_analyzed"] == regions
            assert len(result["region_analyses"]) == len(regions)
            
            # Check cross-region insights
            insights = result["cross_region_insights"]
            assert "cost_comparison" in insights
            assert "service_availability" in insights
            assert "performance_comparison" in insights
            
            # Verify all regions were analyzed
            for region in regions:
                assert region in result["region_analyses"]
    
    @pytest.mark.asyncio
    async def test_get_security_posture_analysis(self, azure_client):
        """Test security posture analysis."""
        # Mock the required service calls
        with patch.object(azure_client, 'get_resource_recommendations') as mock_recommendations, \
             patch.object(azure_client, 'get_resource_health') as mock_health:
            
            mock_recommendations.return_value = {
                "recommendations": [
                    {
                        "title": "Enable disk encryption",
                        "description": "Encrypt VM disks for security",
                        "category": "Security",
                        "impact": "High",
                        "recommended_action": "Enable Azure Disk Encryption"
                    },
                    {
                        "title": "Configure network security groups",
                        "description": "Restrict network access",
                        "category": "Security",
                        "impact": "Medium",
                        "recommended_action": "Review NSG rules"
                    }
                ]
            }
            mock_health.return_value = {"overall_health": {"status": "healthy"}}
            
            result = await azure_client.get_security_posture_analysis()
            
            assert isinstance(result, dict)
            assert "overall_score" in result
            assert "security_recommendations" in result
            assert "compliance_status" in result
            assert "threat_detection" in result
            assert "access_management" in result
            assert "priority_actions" in result
            
            # Check that security score is calculated
            assert 0 <= result["overall_score"] <= 100
            
            # Check compliance status
            compliance = result["compliance_status"]
            assert "azure_security_benchmark" in compliance
            assert "pci_dss" in compliance
            assert "iso_27001" in compliance
            
            # Check that high-impact security issues are in priority actions
            priority_actions = result["priority_actions"]
            high_impact_actions = [a for a in priority_actions if a.get("urgency") == "critical"]
            assert len(high_impact_actions) > 0
    
    @pytest.mark.asyncio
    async def test_get_governance_and_compliance_report(self, azure_client):
        """Test governance and compliance reporting."""
        # Mock the cost analysis call
        with patch.object(azure_client, 'get_cost_analysis') as mock_cost:
            mock_cost.return_value = {"total_cost": 2500, "currency": "USD"}
            
            result = await azure_client.get_governance_and_compliance_report()
            
            assert isinstance(result, dict)
            assert "policy_compliance" in result
            assert "resource_governance" in result
            assert "cost_governance" in result
            assert "security_governance" in result
            assert "operational_governance" in result
            assert "recommendations" in result
            assert "metadata" in result
            
            # Check policy compliance
            policy_compliance = result["policy_compliance"]
            assert "total_policies" in policy_compliance
            assert "compliant_resources" in policy_compliance
            assert "non_compliant_resources" in policy_compliance
            assert "compliance_percentage" in policy_compliance
            
            # Check resource governance
            resource_governance = result["resource_governance"]
            assert "resource_groups" in resource_governance
            assert "tagged_resources_percentage" in resource_governance
            assert "naming_convention_compliance" in resource_governance
            
            # Check recommendations
            recommendations = result["recommendations"]
            assert len(recommendations) > 0
            
            for rec in recommendations:
                assert "category" in rec
                assert "priority" in rec
                assert "title" in rec
                assert "description" in rec
    
    @pytest.mark.asyncio
    async def test_error_handling_in_advanced_features(self, azure_client):
        """Test error handling in advanced features."""
        # Test multi-region analysis with some failures
        regions = ["eastus", "invalid-region", "westus2"]
        
        def mock_analysis_side_effect(region):
            if region == "invalid-region":
                raise CloudServiceError("Invalid region", CloudProvider.AZURE, "INVALID_REGION")
            return {
                "services": {"compute": {"services": []}},
                "cost_analysis": {"total_cost": 1000},
                "summary": {"total_services_analyzed": 1}
            }
        
        with patch.object(azure_client, 'get_comprehensive_analysis', side_effect=mock_analysis_side_effect):
            result = await azure_client.get_multi_region_analysis(regions)
            
            assert isinstance(result, dict)
            assert result["metadata"]["successful_regions"] == 2
            assert result["metadata"]["failed_regions"] == 1
            assert "invalid-region" in result["region_analyses"]
            assert "error" in result["region_analyses"]["invalid-region"]


if __name__ == "__main__":
    pytest.main([__file__])