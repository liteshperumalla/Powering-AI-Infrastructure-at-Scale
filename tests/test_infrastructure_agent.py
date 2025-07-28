"""
Tests for Infrastructure Agent.

Tests the Infrastructure Agent's capabilities for compute resource planning,
capacity planning, scaling strategies, and performance optimization.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.agents.infrastructure_agent import InfrastructureAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestInfrastructureAgent:
    """Test cases for Infrastructure Agent."""
    
    @pytest.fixture
    def sample_assessment(self):
        """Create a sample assessment for testing."""
        return Assessment(
            user_id="test_user",
            title="Test Infrastructure Assessment",
            description="Test assessment for infrastructure agent",
            business_requirements={
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "100k-500k",
                "timeline": "6_months",
                "compliance_needs": ["SOC2"],
                "business_goals": ["scale_infrastructure", "optimize_costs"]
            },
            technical_requirements={
                "workload_types": ["ai_ml", "web_application"],
                "expected_users": 5000,
                "performance_requirements": {
                    "response_time_target": 300,
                    "throughput_target": 1500,
                    "availability_target": 99.9
                },
                "current_infrastructure": {
                    "cloud_provider": "aws",
                    "instance_count": 8,
                    "instance_types": ["m5.large"]
                }
            },
            status="draft",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def infrastructure_agent(self):
        """Create Infrastructure Agent for testing."""
        config = AgentConfig(
            name="Test Infrastructure Agent",
            role=AgentRole.INFRASTRUCTURE,
            temperature=0.1,
            max_tokens=2000
        )
        return InfrastructureAgent(config)
    
    def test_infrastructure_agent_initialization(self, infrastructure_agent):
        """Test Infrastructure Agent initialization."""
        assert infrastructure_agent.name == "Test Infrastructure Agent"
        assert infrastructure_agent.role == AgentRole.INFRASTRUCTURE
        assert infrastructure_agent.status == AgentStatus.IDLE
        
        # Check infrastructure-specific attributes
        assert "cpu_optimized" in infrastructure_agent.compute_types
        assert "horizontal_scaling" in infrastructure_agent.scaling_patterns
        assert "steady_state" in infrastructure_agent.workload_patterns
        assert "cpu_intensive" in infrastructure_agent.performance_benchmarks
        assert "linear_growth" in infrastructure_agent.capacity_models
    
    def test_agent_capabilities(self, infrastructure_agent):
        """Test agent capabilities reporting."""
        capabilities = infrastructure_agent.get_capabilities()
        
        assert any("infrastructure" in cap.lower() for cap in capabilities)
        assert any("model" in cap.lower() for cap in capabilities)
        assert len(capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_infrastructure_analysis_execution(self, infrastructure_agent, sample_assessment):
        """Test infrastructure analysis execution."""
        # Mock the tool usage
        mock_tool_result = Mock()
        mock_tool_result.is_success = True
        mock_tool_result.data = {"analysis": "completed"}
        
        with patch.object(infrastructure_agent, '_use_tool', return_value=mock_tool_result):
            result = await infrastructure_agent.execute(sample_assessment)
        
        # Verify execution completed
        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "Test Infrastructure Agent"
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
        assert isinstance(result.data, dict)
        assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_workload_characteristics_analysis(self, infrastructure_agent, sample_assessment):
        """Test workload characteristics analysis."""
        await infrastructure_agent.initialize(sample_assessment)
        
        # Test workload analysis
        workload_types = ["ai_ml", "web_application"]
        expected_users = 5000
        performance_req = {"response_time_target": 300}
        
        characteristics = infrastructure_agent._analyze_workload_characteristics(
            workload_types, expected_users, performance_req
        )
        
        assert characteristics["primary_workload_type"] == "gpu_intensive"  # AI/ML workload
        assert characteristics["resource_intensity"] == "high"
        assert characteristics["scalability_pattern"] in ["horizontal", "hybrid"]
        assert characteristics["performance_sensitivity"] in ["medium", "high"]
    
    @pytest.mark.asyncio
    async def test_compute_requirements_assessment(self, infrastructure_agent, sample_assessment):
        """Test compute requirements assessment."""
        await infrastructure_agent.initialize(sample_assessment)
        
        workload_characteristics = {
            "primary_workload_type": "gpu_intensive",
            "resource_intensity": "high",
            "scalability_pattern": "horizontal"
        }
        
        compute_req = infrastructure_agent._assess_compute_requirements(workload_characteristics)
        
        assert compute_req["cpu_cores"] >= 8
        assert compute_req["memory_gb"] >= 32
        assert compute_req["instance_type"] == "gpu_accelerated"
        assert "gpu_count" in compute_req
    
    @pytest.mark.asyncio
    async def test_storage_requirements_assessment(self, infrastructure_agent, sample_assessment):
        """Test storage requirements assessment."""
        await infrastructure_agent.initialize(sample_assessment)
        
        workload_characteristics = {"primary_workload_type": "gpu_intensive"}
        expected_users = 5000
        
        storage_req = infrastructure_agent._assess_storage_requirements(
            workload_characteristics, expected_users
        )
        
        assert storage_req["total_storage_gb"] >= 100
        assert storage_req["storage_type"] in ["ssd", "standard"]
        assert storage_req["iops_requirement"] in ["high", "medium", "low"]
        assert storage_req["backup_storage_gb"] > 0
        assert storage_req["growth_factor"] > 1.0
    
    @pytest.mark.asyncio
    async def test_network_requirements_assessment(self, infrastructure_agent, sample_assessment):
        """Test network requirements assessment."""
        await infrastructure_agent.initialize(sample_assessment)
        
        workload_characteristics = {"primary_workload_type": "gpu_intensive"}
        expected_users = 5000
        
        network_req = infrastructure_agent._assess_network_requirements(
            workload_characteristics, expected_users
        )
        
        assert network_req["total_bandwidth_mbps"] >= 10
        assert network_req["latency_requirement"] in ["low", "medium", "high"]
        assert isinstance(network_req["cdn_recommended"], bool)
        assert isinstance(network_req["load_balancer_required"], bool)
    
    @pytest.mark.asyncio
    async def test_workload_patterns_identification(self, infrastructure_agent, sample_assessment):
        """Test workload patterns identification."""
        await infrastructure_agent.initialize(sample_assessment)
        
        business_req = {"industry": "ecommerce"}
        expected_users = 5000
        workload_types = ["web_application"]
        
        patterns = infrastructure_agent._identify_workload_patterns(
            business_req, expected_users, workload_types
        )
        
        assert len(patterns) > 0
        for pattern in patterns:
            assert "pattern" in pattern
            assert "description" in pattern
            assert "scaling_factor" in pattern
            assert "duration" in pattern
            assert pattern["scaling_factor"] > 1.0
    
    @pytest.mark.asyncio
    async def test_growth_projections_calculation(self, infrastructure_agent, sample_assessment):
        """Test growth projections calculation."""
        await infrastructure_agent.initialize(sample_assessment)
        
        business_req = {"company_size": "startup"}
        expected_users = 1000
        
        projections = infrastructure_agent._calculate_growth_projections(
            business_req, expected_users
        )
        
        assert "3_months" in projections
        assert "6_months" in projections
        assert "12_months" in projections
        assert "24_months" in projections
        
        for period, data in projections.items():
            assert "projected_users" in data
            assert "growth_factor" in data
            assert "additional_capacity_needed" in data
            assert data["projected_users"] >= expected_users
            assert data["growth_factor"] >= 1.0
    
    @pytest.mark.asyncio
    async def test_capacity_requirements_calculation(self, infrastructure_agent, sample_assessment):
        """Test current capacity requirements calculation."""
        await infrastructure_agent.initialize(sample_assessment)
        
        workload_characteristics = {"primary_workload_type": "cpu_intensive"}
        expected_users = 5000
        
        capacity = infrastructure_agent._calculate_current_capacity_requirements(
            workload_characteristics, expected_users
        )
        
        assert capacity["required_instances"] >= 1
        assert 0 < capacity["cpu_utilization_target"] <= 100
        assert 0 < capacity["memory_utilization_target"] <= 100
        assert 0 < capacity["scaling_threshold"] <= 100
        assert 0 < capacity["capacity_buffer"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_scaling_patterns_determination(self, infrastructure_agent, sample_assessment):
        """Test optimal scaling patterns determination."""
        await infrastructure_agent.initialize(sample_assessment)
        
        workload_patterns = [
            {"pattern": "seasonal_variations", "scaling_factor": 3.0},
            {"pattern": "unpredictable_bursts", "scaling_factor": 2.0}
        ]
        workload_characteristics = {"primary_workload_type": "cpu_intensive"}
        
        optimal_patterns = infrastructure_agent._determine_optimal_scaling_patterns(
            workload_patterns, workload_characteristics
        )
        
        assert len(optimal_patterns) > 0
        for pattern in optimal_patterns:
            assert "pattern" in pattern
            assert "rationale" in pattern
            assert "implementation" in pattern
            assert "scaling_factor" in pattern
            assert pattern["scaling_factor"] > 1.0
    
    @pytest.mark.asyncio
    async def test_cost_optimization_calculation(self, infrastructure_agent, sample_assessment):
        """Test cost optimization calculation."""
        await infrastructure_agent.initialize(sample_assessment)
        
        current_capacity = {"required_instances": 10}
        current_costs = infrastructure_agent._calculate_current_infrastructure_costs(current_capacity)
        
        assert current_costs["monthly_cost"] > 0
        assert current_costs["annual_cost"] > 0
        assert current_costs["cost_per_instance"] > 0
        assert "cost_breakdown" in current_costs
        
        cost_breakdown = current_costs["cost_breakdown"]
        assert cost_breakdown["compute"] > 0
        assert cost_breakdown["storage"] > 0
        assert cost_breakdown["network"] > 0
    
    @pytest.mark.asyncio
    async def test_optimization_potential_calculation(self, infrastructure_agent, sample_assessment):
        """Test optimization potential calculation."""
        await infrastructure_agent.initialize(sample_assessment)
        
        current_capacity = {"required_instances": 10}
        compute_optimization = {
            "recommended_instances": 8,
            "performance_improvement": 15
        }
        
        optimization = infrastructure_agent._calculate_optimization_potential(
            current_capacity, compute_optimization
        )
        
        assert optimization["instance_reduction"] >= 0
        assert 0 <= optimization["cost_savings_percentage"] <= 100
        assert optimization["performance_improvement"] >= 0
        assert optimization["optimization_confidence"] in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, infrastructure_agent, sample_assessment):
        """Test infrastructure recommendations generation."""
        # Mock the tool usage
        mock_tool_result = Mock()
        mock_tool_result.is_success = True
        mock_tool_result.data = {"analysis": "completed"}
        
        with patch.object(infrastructure_agent, '_use_tool', return_value=mock_tool_result):
            result = await infrastructure_agent.execute(sample_assessment)
        
        recommendations = result.recommendations
        
        # Verify recommendation structure
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec
            assert "rationale" in rec
            assert "implementation_steps" in rec
            assert "business_impact" in rec
            assert "timeline" in rec
            assert "investment_required" in rec
            
            # Verify priority values
            assert rec["priority"] in ["high", "medium", "low"]
            
            # Verify category values
            assert rec["category"] in [
                "compute_resources", "scaling_strategy", "capacity_planning",
                "performance_benchmarking", "cost_optimization"
            ]
    
    @pytest.mark.asyncio
    async def test_different_workload_types(self, infrastructure_agent):
        """Test agent behavior with different workload types."""
        workload_scenarios = [
            {
                "workload_types": ["ai_ml"],
                "expected_workload_type": "gpu_intensive"
            },
            {
                "workload_types": ["database"],
                "expected_workload_type": "memory_intensive"
            },
            {
                "workload_types": ["compute_processing"],
                "expected_workload_type": "cpu_intensive"
            },
            {
                "workload_types": ["file_storage"],
                "expected_workload_type": "io_intensive"
            }
        ]
        
        for scenario in workload_scenarios:
            characteristics = infrastructure_agent._analyze_workload_characteristics(
                scenario["workload_types"], 1000, {}
            )
            assert characteristics["primary_workload_type"] == scenario["expected_workload_type"]
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, infrastructure_agent):
        """Test performance benchmarks configuration."""
        benchmarks = infrastructure_agent.performance_benchmarks
        
        # Verify all workload types have benchmarks
        required_workload_types = ["cpu_intensive", "memory_intensive", "gpu_intensive", "io_intensive"]
        for workload_type in required_workload_types:
            assert workload_type in benchmarks
            
            benchmark = benchmarks[workload_type]
            assert "cpu_utilization_target" in benchmark
            assert "memory_utilization_target" in benchmark
            assert "scaling_threshold" in benchmark
            
            # Verify reasonable values
            assert 0 < benchmark["cpu_utilization_target"] <= 100
            assert 0 < benchmark["memory_utilization_target"] <= 100
            assert 0 < benchmark["scaling_threshold"] <= 100
    
    @pytest.mark.asyncio
    async def test_error_handling(self, infrastructure_agent, sample_assessment):
        """Test error handling in Infrastructure Agent."""
        # Mock tool failure
        mock_tool_result = Mock()
        mock_tool_result.is_success = False
        mock_tool_result.error = "Tool execution failed"
        
        with patch.object(infrastructure_agent, '_use_tool', side_effect=Exception("Tool error")):
            result = await infrastructure_agent.execute(sample_assessment)
        
        # Verify error handling
        assert result.status == AgentStatus.FAILED
        assert result.error is not None
        assert "Tool error" in result.error
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, infrastructure_agent, sample_assessment):
        """Test agent health check functionality."""
        await infrastructure_agent.initialize(sample_assessment)
        
        health_status = await infrastructure_agent.health_check()
        
        assert health_status["agent_name"] == "Test Infrastructure Agent"
        assert health_status["role"] == "infrastructure"
        assert health_status["status"] == "initializing"
        assert "version" in health_status
        assert "memory_enabled" in health_status
        assert "tools_count" in health_status
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self, infrastructure_agent):
        """Test concurrent execution of Infrastructure Agent."""
        assessments = []
        
        # Create multiple assessments
        for i in range(3):
            assessment = Assessment(
                user_id=f"user_{i}",
                title=f"Test Assessment {i}",
                business_requirements={"company_size": "medium", "industry": "technology"},
                technical_requirements={
                    "workload_types": ["web_application"],
                    "expected_users": 1000 * (i + 1)
                },
                status="draft",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            assessments.append(assessment)
        
        # Mock tool usage for all executions
        mock_tool_result = Mock()
        mock_tool_result.is_success = True
        mock_tool_result.data = {"analysis": "completed"}
        
        with patch.object(infrastructure_agent, '_use_tool', return_value=mock_tool_result):
            # Execute concurrently
            tasks = [infrastructure_agent.execute(assessment) for assessment in assessments]
            results = await asyncio.gather(*tasks)
        
        # Verify all executions completed
        assert len(results) == 3
        for result in results:
            assert result.status == AgentStatus.COMPLETED
            assert len(result.recommendations) > 0


class TestInfrastructureAgentIntegration:
    """Integration tests for Infrastructure Agent."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_infrastructure_analysis(self):
        """Test end-to-end infrastructure analysis workflow."""
        # Create agent
        agent = InfrastructureAgent()
        
        # Create comprehensive assessment
        assessment = Assessment(
            user_id="integration_test_user",
            title="Integration Test Assessment",
            description="Comprehensive test for infrastructure agent",
            business_requirements={
                "company_size": "large",
                "industry": "fintech",
                "budget_range": "1m+",
                "timeline": "12_months",
                "compliance_needs": ["PCI_DSS", "SOX"],
                "business_goals": [
                    "scale_infrastructure",
                    "optimize_costs",
                    "improve_performance",
                    "ensure_compliance"
                ]
            },
            technical_requirements={
                "workload_types": [
                    "ai_ml",
                    "database",
                    "web_application",
                    "data_processing"
                ],
                "expected_users": 100000,
                "performance_requirements": {
                    "response_time_target": 50,
                    "throughput_target": 50000,
                    "availability_target": 99.99
                },
                "current_infrastructure": {
                    "cloud_provider": "aws",
                    "instance_count": 50,
                    "instance_types": ["m5.large", "c5.xlarge", "r5.2xlarge"]
                },
                "scalability_needs": {
                    "auto_scaling": True,
                    "peak_capacity": "5x_normal",
                    "geographic_distribution": True
                }
            },
            status="draft",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock tool usage
        mock_tool_result = Mock()
        mock_tool_result.is_success = True
        mock_tool_result.data = {
            "analysis": "completed",
            "workload_analysis": "high_performance_requirements",
            "capacity_analysis": "significant_scaling_needed"
        }
        
        with patch.object(agent, '_use_tool', return_value=mock_tool_result):
            result = await agent.execute(assessment)
        
        # Verify comprehensive analysis
        assert result.status == AgentStatus.COMPLETED
        assert len(result.recommendations) >= 3  # Should have multiple recommendations
        
        # Verify recommendation categories
        categories = [rec["category"] for rec in result.recommendations]
        expected_categories = ["compute_resources", "scaling_strategy", "capacity_planning"]
        assert any(cat in categories for cat in expected_categories)
        
        # Verify high-priority recommendations for large-scale deployment
        high_priority_recs = [rec for rec in result.recommendations if rec["priority"] == "high"]
        assert len(high_priority_recs) >= 2
        
        # Verify analysis data completeness
        analysis_data = result.data
        required_sections = [
            "infrastructure_analysis",
            "capacity_analysis", 
            "scaling_strategies",
            "cost_optimization"
        ]
        
        for section in required_sections:
            assert section in analysis_data
            assert analysis_data[section] is not None
        
        # Verify execution metrics
        assert result.execution_time is not None
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_infrastructure_agent_with_registry(self):
        """Test Infrastructure Agent integration with agent registry."""
        from src.infra_mind.agents import agent_registry, agent_factory, AgentRole
        
        # Verify agent is registered
        agent_type = agent_registry.get_agent_type(AgentRole.INFRASTRUCTURE)
        assert agent_type is not None
        assert agent_type == InfrastructureAgent
        
        # Create agent through factory
        agent = await agent_factory.create_agent(AgentRole.INFRASTRUCTURE)
        assert agent is not None
        assert isinstance(agent, InfrastructureAgent)
        assert agent.role == AgentRole.INFRASTRUCTURE
        
        # Verify agent is in registry
        registered_agents = agent_registry.list_agent_instances()
        assert any(agent.role == AgentRole.INFRASTRUCTURE for agent in registered_agents)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])