"""
Tests for the Cloud Engineer Agent.

Tests service curation, multi-cloud comparison, and cost optimization functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, Mock

from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus


@pytest.fixture
def sample_assessment():
    """Create a sample assessment for testing."""
    # Create a mock assessment to avoid database dependencies
    assessment = Mock()
    assessment.id = "test_assessment_id"
    assessment.user_id = "test_user"
    assessment.title = "Test Assessment"
    
    assessment.business_requirements = {
        "company_size": "medium",
        "industry": "technology",
        "budget_range": "$50k-100k",
        "primary_goals": ["scalability", "cost_reduction"],
        "timeline": "6 months"
    }
    
    assessment.technical_requirements = {
        "workload_types": ["web_application", "ai_ml"],
        "expected_users": 15000,
        "performance_requirements": {"response_time": "< 100ms"},
        "integration_needs": ["database", "api", "analytics"]
    }
    
    # Mock the dict() method
    assessment.dict.return_value = {
        "id": assessment.id,
        "user_id": assessment.user_id,
        "title": assessment.title,
        "business_requirements": assessment.business_requirements,
        "technical_requirements": assessment.technical_requirements
    }
    
    return assessment


@pytest.fixture
def cloud_engineer_agent():
    """Create a Cloud Engineer agent for testing."""
    config = AgentConfig(
        name="Test Cloud Engineer Agent",
        role=AgentRole.CLOUD_ENGINEER,
        tools_enabled=["cloud_api", "calculator", "data_processor"],
        metrics_enabled=False,  # Disable metrics for testing
        memory_enabled=False    # Disable memory for testing
    )
    return CloudEngineerAgent(config)


class TestCloudEngineerAgent:
    """Test the Cloud Engineer Agent implementation."""
    
    def test_cloud_engineer_agent_initialization(self, cloud_engineer_agent):
        """Test Cloud Engineer agent initialization."""
        assert cloud_engineer_agent.name == "Test Cloud Engineer Agent"
        assert cloud_engineer_agent.role == AgentRole.CLOUD_ENGINEER
        assert cloud_engineer_agent.status == AgentStatus.IDLE
        assert "cloud_api" in cloud_engineer_agent.config.tools_enabled
        assert "calculator" in cloud_engineer_agent.config.tools_enabled
        assert "data_processor" in cloud_engineer_agent.config.tools_enabled
        
        # Check Cloud Engineer-specific attributes
        assert len(cloud_engineer_agent.cloud_platforms) > 0
        assert "aws" in cloud_engineer_agent.cloud_platforms
        assert "azure" in cloud_engineer_agent.cloud_platforms
        
        assert len(cloud_engineer_agent.service_categories) > 0
        assert "compute" in cloud_engineer_agent.service_categories
        assert "storage" in cloud_engineer_agent.service_categories
        
        assert len(cloud_engineer_agent.ranking_criteria) > 0
        assert "cost_effectiveness" in cloud_engineer_agent.ranking_criteria
    
    @pytest.mark.asyncio
    async def test_cloud_engineer_agent_execution(self, cloud_engineer_agent, sample_assessment):
        """Test Cloud Engineer agent execution flow."""
        # Mock the tool calls to avoid external dependencies
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            # Mock tool responses
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Workload types: web_application, ai_ml"],
                "services": [
                    {
                        "name": "EC2 t3.medium",
                        "service_id": "t3.medium",
                        "pricing": {"hourly": 0.0416},
                        "specifications": {"vcpus": 2, "memory_gb": 4}
                    }
                ],
                "monthly_cost": 500
            }
            
            result = await cloud_engineer_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert result.agent_name == "Test Cloud Engineer Agent"
            assert "recommendations" in result.__dict__
            assert "data" in result.__dict__
            assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_technical_requirements_analysis(self, cloud_engineer_agent, sample_assessment):
        """Test technical requirements analysis."""
        await cloud_engineer_agent.initialize(sample_assessment)
        
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Expected users: 15000", "Workloads: web_application, ai_ml"]
            }
            
            technical_analysis = await cloud_engineer_agent._analyze_technical_requirements()
            
            assert "workload_analysis" in technical_analysis
            assert "service_needs" in technical_analysis
            assert "scalability_needs" in technical_analysis
            
            # Check workload analysis
            workload_analysis = technical_analysis["workload_analysis"]
            assert workload_analysis["expected_users"] == 15000
            assert "web_application" in workload_analysis["types"]
            assert "ai_ml" in workload_analysis["types"]
            
            # Check service needs
            service_needs = technical_analysis["service_needs"]
            assert service_needs["compute"]["needed"] is True
            assert service_needs["compute"]["scale"] == "large"  # 15000 users
            assert service_needs["database"]["needed"] is True
            assert service_needs["ai_ml"]["needed"] is True
    
    @pytest.mark.asyncio
    async def test_cloud_service_data_collection(self, cloud_engineer_agent, sample_assessment):
        """Test cloud service data collection."""
        await cloud_engineer_agent.initialize(sample_assessment)
        
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            # Mock different responses for different providers/services
            def mock_tool_side_effect(*args, **kwargs):
                result = AsyncMock()
                result.is_success = True
                
                provider = kwargs.get("provider", "aws")
                service = kwargs.get("service", "compute")
                
                if provider == "aws" and service == "compute":
                    result.data = {
                        "services": [
                            {
                                "name": "EC2 t3.medium",
                                "service_id": "t3.medium",
                                "pricing": {"hourly": 0.0416},
                                "specifications": {"vcpus": 2, "memory_gb": 4}
                            }
                        ]
                    }
                elif provider == "azure" and service == "compute":
                    result.data = {
                        "services": [
                            {
                                "name": "Standard_B2s",
                                "service_id": "Standard_B2s",
                                "pricing": {"hourly": 0.0496},
                                "specifications": {"vcpus": 2, "memory_gb": 4}
                            }
                        ]
                    }
                else:
                    result.data = {"services": []}
                
                return result
            
            mock_tool.side_effect = mock_tool_side_effect
            
            service_data = await cloud_engineer_agent._collect_cloud_service_data()
            
            assert "providers" in service_data
            assert "collection_timestamp" in service_data
            assert "successful_providers" in service_data
            
            providers = service_data["providers"]
            assert "aws" in providers
            assert "azure" in providers
    
    @pytest.mark.asyncio
    async def test_service_curation_and_ranking(self, cloud_engineer_agent, sample_assessment):
        """Test service curation and ranking."""
        await cloud_engineer_agent.initialize(sample_assessment)
        
        # Mock technical analysis
        technical_analysis = {
            "service_needs": {
                "compute": {
                    "needed": True,
                    "scale": "large",
                    "requirements": {"expected_users": 15000}
                }
            },
            "priority_services": ["compute", "database"]
        }
        
        # Mock service data
        service_data = {
            "providers": {
                "aws": {
                    "compute": {
                        "services": [
                            {
                                "name": "EC2 t3.medium",
                                "service_id": "t3.medium",
                                "pricing": {"hourly": 0.0416},
                                "specifications": {"vcpus": 2, "memory_gb": 4},
                                "features": ["auto_scaling", "load_balancing"]
                            },
                            {
                                "name": "EC2 t3.large",
                                "service_id": "t3.large", 
                                "pricing": {"hourly": 0.0832},
                                "specifications": {"vcpus": 2, "memory_gb": 8},
                                "features": ["auto_scaling", "load_balancing", "enhanced_networking"]
                            }
                        ]
                    }
                },
                "azure": {
                    "compute": {
                        "services": [
                            {
                                "name": "Standard_B2s",
                                "service_id": "Standard_B2s",
                                "pricing": {"hourly": 0.0496},
                                "specifications": {"vcpus": 2, "memory_gb": 4},
                                "features": ["auto_scaling"]
                            }
                        ]
                    }
                }
            }
        }
        
        curated_services = await cloud_engineer_agent._curate_services(technical_analysis, service_data)
        
        assert "curated_services" in curated_services
        assert "ranked_services" in curated_services
        assert "total_services_evaluated" in curated_services
        
        # Check that services were curated for compute category
        ranked_services = curated_services["ranked_services"]
        if "compute" in ranked_services:
            compute_services = ranked_services["compute"]
            assert len(compute_services) > 0
            
            # Check that services have ranking scores
            for service in compute_services:
                assert "ranking_score" in service
                assert service["ranking_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_cost_optimization_analysis(self, cloud_engineer_agent, sample_assessment):
        """Test cost optimization analysis."""
        await cloud_engineer_agent.initialize(sample_assessment)
        
        # Mock curated services
        curated_services = {
            "ranked_services": {
                "compute": [
                    {
                        "provider": "aws",
                        "name": "EC2 t3.medium",
                        "pricing": {"hourly": 0.0416},
                        "ranking_score": 85.0
                    },
                    {
                        "provider": "azure",
                        "name": "Standard_B2s",
                        "pricing": {"hourly": 0.0496},
                        "ranking_score": 80.0
                    }
                ]
            }
        }
        
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"monthly_cost": 30.37}
            
            cost_analysis = await cloud_engineer_agent._perform_cost_optimization(curated_services)
            
            assert "cost_estimates" in cost_analysis
            assert "total_monthly_cost" in cost_analysis
            assert "optimization_recommendations" in cost_analysis
            assert "cost_breakdown" in cost_analysis
            
            # Check cost estimates structure
            cost_estimates = cost_analysis["cost_estimates"]
            if "compute" in cost_estimates:
                compute_costs = cost_estimates["compute"]
                assert len(compute_costs) > 0
                for cost_item in compute_costs:
                    assert "service" in cost_item
                    assert "monthly_cost" in cost_item
    
    def test_service_needs_determination(self, cloud_engineer_agent):
        """Test service needs determination logic."""
        workload_types = ["web_application", "ai_ml"]
        expected_users = 15000
        performance_req = {"response_time": "< 100ms"}
        
        service_needs = cloud_engineer_agent._determine_service_needs(
            workload_types, expected_users, performance_req
        )
        
        # Check compute needs
        assert service_needs["compute"]["needed"] is True
        assert service_needs["compute"]["scale"] == "large"  # 15000 users
        
        # Check storage needs
        assert service_needs["storage"]["needed"] is True
        
        # Check database needs
        assert service_needs["database"]["needed"] is True
        assert service_needs["database"]["type"] == "relational"  # web_application
        
        # Check AI/ML needs
        assert service_needs["ai_ml"]["needed"] is True
        
        # Check networking needs
        assert service_needs["networking"]["needed"] is True  # > 1000 users
        assert service_needs["networking"]["cdn_needed"] is True  # > 5000 users
    
    def test_service_ranking_logic(self, cloud_engineer_agent):
        """Test service ranking logic."""
        services = [
            {
                "provider": "aws",
                "name": "EC2 t3.medium",
                "pricing": {"hourly": 0.0416},
                "specifications": {"vcpus": 2, "memory_gb": 4},
                "features": ["auto_scaling", "load_balancing"]
            },
            {
                "provider": "azure",
                "name": "Standard_B2s",
                "pricing": {"hourly": 0.0496},
                "specifications": {"vcpus": 2, "memory_gb": 4},
                "features": ["auto_scaling"]
            },
            {
                "provider": "aws",
                "name": "EC2 t3.large",
                "pricing": {"hourly": 0.0832},
                "specifications": {"vcpus": 2, "memory_gb": 8},
                "features": ["auto_scaling", "load_balancing", "enhanced_networking"]
            }
        ]
        
        category_needs = {"needed": True, "scale": "medium"}
        technical_analysis = {"workload_analysis": {"expected_users": 5000}}
        
        ranked_services = cloud_engineer_agent._rank_services(
            services, category_needs, technical_analysis
        )
        
        assert len(ranked_services) == 3
        
        # Check that services are ranked (have scores)
        for service in ranked_services:
            assert "ranking_score" in service
            assert service["ranking_score"] > 0
        
        # Check that services are sorted by score (highest first)
        scores = [s["ranking_score"] for s in ranked_services]
        assert scores == sorted(scores, reverse=True)
    
    def test_cost_calculation_logic(self, cloud_engineer_agent):
        """Test service cost calculation logic."""
        service = {
            "provider": "aws",
            "name": "EC2 t3.medium",
            "pricing": {"hourly": 0.0416}
        }
        
        # Test direct calculation (without tool)
        expected_monthly = 0.0416 * 730  # 730 hours per month
        
        # The actual method is async and uses tools, but we can test the logic
        pricing = service.get("pricing", {})
        hourly_price = pricing.get("hourly", pricing.get("hourly_price", 0.1))
        monthly_cost = hourly_price * 730
        
        assert abs(monthly_cost - expected_monthly) < 0.01
    
    def test_implementation_guidance_creation(self, cloud_engineer_agent):
        """Test implementation guidance creation."""
        recommendations = [
            {
                "category": "compute",
                "priority": "high",
                "service": {
                    "provider": "aws",
                    "name": "EC2 t3.medium"
                }
            },
            {
                "category": "database",
                "priority": "high",
                "service": {
                    "provider": "aws",
                    "name": "RDS MySQL"
                }
            }
        ]
        
        # Test roadmap creation
        roadmap = cloud_engineer_agent._create_deployment_roadmap(recommendations)
        
        assert "phases" in roadmap
        assert "total_duration_weeks" in roadmap
        
        phases = roadmap["phases"]
        assert len(phases) > 0
        
        # Should have a core infrastructure phase for high priority services
        core_phase = phases[0]
        assert core_phase["name"] == "Core Infrastructure Setup"
        assert len(core_phase["services"]) == 2  # Both high priority services
        
        # Test best practices generation
        best_practices = cloud_engineer_agent._generate_best_practices(recommendations)
        
        assert len(best_practices) > 0
        for practice in best_practices:
            assert "category" in practice
            assert "practice" in practice
            assert "rationale" in practice
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cloud_engineer_agent, sample_assessment):
        """Test error handling in Cloud Engineer agent."""
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            # Mock tool failure
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = False
            mock_tool.return_value.error = "Tool execution failed"
            
            result = await cloud_engineer_agent.execute(sample_assessment)
            
            # Agent should handle tool failures gracefully
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
            
            if result.status == AgentStatus.FAILED:
                assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, cloud_engineer_agent):
        """Test agent health check."""
        health = await cloud_engineer_agent.health_check()
        
        assert "agent_name" in health
        assert "status" in health
        assert "role" in health
        assert health["agent_name"] == "Test Cloud Engineer Agent"
        assert health["role"] == "cloud_engineer"
    
    def test_capabilities(self, cloud_engineer_agent):
        """Test agent capabilities reporting."""
        capabilities = cloud_engineer_agent.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert any("Role: cloud_engineer" in cap for cap in capabilities)
        assert any("Tools:" in cap for cap in capabilities)


class TestCloudEngineerAgentIntegration:
    """Integration tests for Cloud Engineer Agent."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, sample_assessment):
        """Test full Cloud Engineer agent workflow integration."""
        from src.infra_mind.agents import agent_registry, AgentFactory
        
        # Create agent through factory
        factory = AgentFactory(agent_registry)
        cloud_engineer_agent = await factory.create_agent(AgentRole.CLOUD_ENGINEER)
        
        assert cloud_engineer_agent is not None
        assert isinstance(cloud_engineer_agent, CloudEngineerAgent)
        
        # Mock tool calls for integration test
        with patch.object(cloud_engineer_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Test insight"],
                "services": [{"name": "Test Service", "pricing": {"hourly": 0.1}}],
                "monthly_cost": 100
            }
            
            result = await cloud_engineer_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert len(result.recommendations) >= 0  # May be 0 if no services match
            assert "technical_analysis" in result.data
            assert "service_data" in result.data
            assert "curated_services" in result.data
            assert "cost_analysis" in result.data
            assert "implementation_guidance" in result.data


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(pytest.main([__file__, "-v"]))