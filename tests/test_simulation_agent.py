"""
Tests for Simulation Agent.

This module contains comprehensive tests for the Simulation Agent's scenario modeling,
cost projections, capacity planning, and mathematical forecasting capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.agents.simulation_agent import (
    SimulationAgent, AgentConfig, AgentRole, ScenarioType, GrowthModel,
    SimulationParameters, SimulationResult
)
from src.infra_mind.agents.base import AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestSimulationAgent:
    """Test cases for Simulation Agent."""
    
    @pytest.fixture
    def sample_assessment(self):
        """Create a sample assessment for testing."""
        return Assessment(
            user_id="test_user_123",
            title="Test Infrastructure Assessment",
            business_requirements={
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "200k-800k",
                "timeline": "18_months",
                "growth_expectations": "high",
                "primary_concerns": ["cost", "scalability"],
                "risk_tolerance": "medium"
            },
            technical_requirements={
                "expected_users": 5000,
                "workload_types": ["ai_ml", "data_processing"],
                "performance_requirements": {
                    "response_time": "< 300ms",
                    "throughput": "> 1000 rps"
                },
                "scalability_needs": {
                    "auto_scaling": True,
                    "peak_capacity": "10x normal load"
                }
            }
        )
    
    @pytest.fixture
    def agent_config(self):
        """Create agent configuration for testing."""
        return AgentConfig(
            name="Test Simulation Agent",
            role=AgentRole.SIMULATION,
            temperature=0.1,
            max_tokens=3000,
            tools_enabled=["calculator", "data_processor"]
        )
    
    @pytest.fixture
    def simulation_agent(self, agent_config):
        """Create a Simulation Agent instance for testing."""
        return SimulationAgent(agent_config)
    
    def test_agent_initialization(self, simulation_agent):
        """Test agent initialization."""
        assert simulation_agent.name == "Test Simulation Agent"
        assert simulation_agent.role == AgentRole.SIMULATION
        assert simulation_agent.status == AgentStatus.IDLE
        assert len(simulation_agent.scenario_types) == 6
        assert len(simulation_agent.growth_models) == 6
        assert "compute" in simulation_agent.cost_factors
        assert "cpu_utilization" in simulation_agent.performance_models
        assert "market_volatility" in simulation_agent.risk_factors
    
    def test_agent_capabilities(self, simulation_agent):
        """Test agent capabilities reporting."""
        capabilities = simulation_agent.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert any("Role: simulation" in cap for cap in capabilities)
        assert any("Temperature: 0.1" in cap for cap in capabilities)
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, simulation_agent):
        """Test agent health check."""
        health = await simulation_agent.health_check()
        
        assert isinstance(health, dict)
        assert health["agent_name"] == "Test Simulation Agent"
        assert health["role"] == "simulation"
        assert health["status"] == "idle"
        assert "version" in health
        assert "tools_count" in health
    
    @pytest.mark.asyncio
    async def test_execute_main_logic(self, simulation_agent, sample_assessment):
        """Test main execution logic."""
        # Mock the tool usage
        with patch.object(simulation_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"analysis": "test"}
            
            # Initialize agent
            await simulation_agent.initialize(sample_assessment)
            
            # Execute main logic
            result = await simulation_agent._execute_main_logic()
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "recommendations" in result
            assert "data" in result
            assert isinstance(result["recommendations"], list)
            assert isinstance(result["data"], dict)
            
            # Verify data components
            data = result["data"]
            assert "scenario_analysis" in data
            assert "cost_projections" in data
            assert "capacity_simulations" in data
            assert "scaling_simulations" in data
            assert "performance_modeling" in data
            assert "optimization_simulations" in data
            assert "risk_analysis" in data
            assert "simulation_metadata" in data
    
    @pytest.mark.asyncio
    async def test_full_agent_execution(self, simulation_agent, sample_assessment):
        """Test full agent execution."""
        with patch.object(simulation_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"analysis": "test"}
            
            result = await simulation_agent.execute(sample_assessment)
            
            assert result.agent_name == "Test Simulation Agent"
            assert result.status == AgentStatus.COMPLETED
            assert isinstance(result.recommendations, list)
            assert isinstance(result.data, dict)
            assert result.execution_time is not None
            assert result.execution_time > 0
    
    def test_determine_required_scenarios(self, simulation_agent):
        """Test scenario requirement determination."""
        technical_req = {
            "expected_users": 10000,
            "performance_requirements": {"response_time": "< 200ms"}
        }
        business_req = {
            "growth_expectations": "high",
            "primary_concerns": ["cost"],
            "criticality": "high"
        }
        
        scenarios = simulation_agent._determine_required_scenarios(
            technical_req, business_req, 10000
        )
        
        assert isinstance(scenarios, list)
        assert ScenarioType.COST_PROJECTION in scenarios
        assert ScenarioType.CAPACITY_PLANNING in scenarios
        assert ScenarioType.SCALING_SIMULATION in scenarios
        assert ScenarioType.PERFORMANCE_MODELING in scenarios
        assert ScenarioType.RESOURCE_OPTIMIZATION in scenarios
        assert ScenarioType.DISASTER_RECOVERY in scenarios
    
    def test_extract_growth_parameters(self, simulation_agent):
        """Test growth parameter extraction."""
        growth_params = simulation_agent._extract_growth_parameters(
            "high", 5000, "12_months"
        )
        
        assert isinstance(growth_params, dict)
        assert growth_params["growth_model"] == GrowthModel.EXPONENTIAL
        assert growth_params["base_growth_rate"] == 0.20
        assert growth_params["initial_users"] == 5000
        assert growth_params["volatility"] == 0.15
        assert growth_params["compound_factor"] == 1.0
    
    def test_determine_time_horizons(self, simulation_agent):
        """Test time horizon determination."""
        horizons = simulation_agent._determine_time_horizons("24_months", "high")
        
        assert isinstance(horizons, list)
        assert 3 in horizons  # Short-term for aggressive growth
        assert 6 in horizons
        assert 12 in horizons
        assert 24 in horizons
        assert all(isinstance(h, int) for h in horizons)
        assert horizons == sorted(horizons)  # Should be sorted
    
    def test_extract_workload_characteristics(self, simulation_agent):
        """Test workload characteristics extraction."""
        technical_req = {
            "workload_types": ["ai_ml", "data_processing"],
            "performance_requirements": {"response_time": "< 200ms"}
        }
        
        characteristics = simulation_agent._extract_workload_characteristics(technical_req)
        
        assert isinstance(characteristics, dict)
        assert characteristics["workload_pattern"] == "gpu_intensive"
        assert characteristics["resource_multiplier"] == 2.5
        assert characteristics["scalability_factor"] == 1.2
        assert characteristics["performance_sensitivity"] == "high"
    
    def test_parse_budget_range(self, simulation_agent):
        """Test budget range parsing."""
        # Test range format
        budget = simulation_agent._parse_budget_range("200k-800k")
        assert budget["min_budget"] == 200000
        assert budget["max_budget"] == 800000
        assert budget["target_budget"] == 500000
        
        # Test single value format
        budget = simulation_agent._parse_budget_range("500k")
        assert budget["min_budget"] == 400000  # 80% of 500k
        assert budget["max_budget"] == 600000  # 120% of 500k
        
        # Test invalid format (should use defaults)
        budget = simulation_agent._parse_budget_range("unlimited")
        assert budget["min_budget"] == 50000
        assert budget["max_budget"] == 200000
    
    @pytest.mark.asyncio
    async def test_run_cost_projection_for_horizon(self, simulation_agent):
        """Test cost projection for specific horizon."""
        growth_parameters = {
            "growth_model": GrowthModel.LINEAR,
            "base_growth_rate": 0.10,
            "initial_users": 1000
        }
        workload_characteristics = {
            "resource_multiplier": 1.5
        }
        budget_constraints = {
            "min_budget": 50000,
            "max_budget": 200000
        }
        
        projection = await simulation_agent._run_cost_projection_for_horizon(
            12, growth_parameters, workload_characteristics, budget_constraints
        )
        
        assert isinstance(projection, dict)
        assert projection["horizon_months"] == 12
        assert "monthly_projections" in projection
        assert "total_cost" in projection
        assert "average_monthly_cost" in projection
        assert "final_user_count" in projection
        
        # Verify monthly projections structure
        monthly_projections = projection["monthly_projections"]
        assert len(monthly_projections) == 12
        
        for month_data in monthly_projections:
            assert "month" in month_data
            assert "users" in month_data
            assert "compute_cost" in month_data
            assert "storage_cost" in month_data
            assert "network_cost" in month_data
            assert "total_monthly_cost" in month_data
            assert "cumulative_cost" in month_data
        
        # Verify growth pattern
        assert monthly_projections[0]["users"] > 1000  # Growth from initial
        assert monthly_projections[-1]["users"] > monthly_projections[0]["users"]  # Continued growth
    
    def test_calculate_compute_cost(self, simulation_agent):
        """Test compute cost calculation."""
        cost = simulation_agent._calculate_compute_cost(1000, 1.0)
        assert isinstance(cost, float)
        assert cost > 0
        
        # Test scaling with user count
        cost_2x = simulation_agent._calculate_compute_cost(2000, 1.0)
        assert cost_2x > cost
        
        # Test resource multiplier effect
        cost_2x_resources = simulation_agent._calculate_compute_cost(1000, 2.0)
        assert cost_2x_resources > cost
    
    def test_calculate_storage_cost(self, simulation_agent):
        """Test storage cost calculation."""
        cost = simulation_agent._calculate_storage_cost(1000, 1.0)
        assert isinstance(cost, float)
        assert cost > 0
        
        # Storage should grow sublinearly
        cost_10x = simulation_agent._calculate_storage_cost(10000, 1.0)
        compute_cost = simulation_agent._calculate_compute_cost(1000, 1.0)
        compute_cost_10x = simulation_agent._calculate_compute_cost(10000, 1.0)
        
        storage_ratio = cost_10x / cost
        compute_ratio = compute_cost_10x / compute_cost
        
        # Storage should scale less than compute
        assert storage_ratio < compute_ratio
    
    def test_calculate_network_cost(self, simulation_agent):
        """Test network cost calculation."""
        cost = simulation_agent._calculate_network_cost(1000, 1.0)
        assert isinstance(cost, float)
        assert cost > 0
        
        # Test linear scaling with users
        cost_2x = simulation_agent._calculate_network_cost(2000, 1.0)
        assert abs(cost_2x / cost - 2.0) < 0.1  # Should be approximately 2x
    
    @pytest.mark.asyncio
    async def test_run_monte_carlo_cost_simulation(self, simulation_agent):
        """Test Monte Carlo cost simulation."""
        growth_parameters = {
            "base_growth_rate": 0.10,
            "initial_users": 1000
        }
        workload_characteristics = {
            "resource_multiplier": 1.0
        }
        time_horizons = [6, 12]
        
        with patch('random.random', return_value=0.5):
            results = await simulation_agent._run_monte_carlo_cost_simulation(
                growth_parameters, workload_characteristics, time_horizons
            )
        
        assert isinstance(results, dict)
        assert "6_months" in results
        assert "12_months" in results
        
        for horizon_result in results.values():
            assert "mean" in horizon_result
            assert "std" in horizon_result
            assert "percentile_5" in horizon_result
            assert "percentile_95" in horizon_result
            assert "confidence_interval_95" in horizon_result
            
            # Verify confidence interval structure
            ci = horizon_result["confidence_interval_95"]
            assert isinstance(ci, tuple)
            assert len(ci) == 2
            assert ci[0] < ci[1]  # Lower bound < upper bound
    
    def test_calculate_complexity_score(self, simulation_agent):
        """Test complexity score calculation."""
        assert simulation_agent._calculate_complexity_score("vertical") == 2.0
        assert simulation_agent._calculate_complexity_score("horizontal") == 4.0
        assert simulation_agent._calculate_complexity_score("auto_scaling") == 6.0
        assert simulation_agent._calculate_complexity_score("hybrid") == 5.0
        assert simulation_agent._calculate_complexity_score("unknown") == 3.0
    
    def test_calculate_scenario_risk_score(self, simulation_agent):
        """Test scenario risk score calculation."""
        risk_score = simulation_agent._calculate_scenario_risk_score("vertical", 1.0)
        assert isinstance(risk_score, float)
        assert risk_score > 0
        
        # Higher growth multiplier should increase risk
        higher_risk = simulation_agent._calculate_scenario_risk_score("vertical", 2.0)
        assert higher_risk > risk_score
        
        # Different strategies should have different base risks
        horizontal_risk = simulation_agent._calculate_scenario_risk_score("horizontal", 1.0)
        assert horizontal_risk != risk_score
    
    def test_predict_scaling_events(self, simulation_agent):
        """Test scaling event prediction."""
        # High growth scenario
        high_growth_params = {"base_growth_rate": 0.20}
        events = simulation_agent._predict_scaling_events(high_growth_params)
        
        assert isinstance(events, list)
        assert len(events) >= 3  # Should predict multiple events for high growth
        
        for event in events:
            assert "month" in event
            assert "event" in event
            assert "magnitude" in event
            assert event["event"] == "scale_up"
            assert event["magnitude"] > 1.0
        
        # Low growth scenario
        low_growth_params = {"base_growth_rate": 0.03}
        events = simulation_agent._predict_scaling_events(low_growth_params)
        
        assert len(events) == 1  # Should predict fewer events for low growth
    
    def test_calculate_performance_grade(self, simulation_agent):
        """Test performance grade calculation."""
        assert simulation_agent._calculate_performance_grade(150, 99.8) == "A"
        assert simulation_agent._calculate_performance_grade(400, 99.2) == "B"
        assert simulation_agent._calculate_performance_grade(800, 96.0) == "C"
        assert simulation_agent._calculate_performance_grade(1500, 92.0) == "D"
        assert simulation_agent._calculate_performance_grade(3000, 85.0) == "F"
    
    @pytest.mark.asyncio
    async def test_analyze_simulation_requirements(self, simulation_agent, sample_assessment):
        """Test simulation requirements analysis."""
        await simulation_agent.initialize(sample_assessment)
        
        with patch.object(simulation_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"analysis": "test"}
            
            analysis = await simulation_agent._analyze_simulation_requirements()
            
            assert isinstance(analysis, dict)
            assert "required_scenarios" in analysis
            assert "growth_parameters" in analysis
            assert "time_horizons" in analysis
            assert "workload_characteristics" in analysis
            assert "budget_constraints" in analysis
            assert "expected_users" in analysis
            assert "business_context" in analysis
            
            # Verify required scenarios
            scenarios = analysis["required_scenarios"]
            assert isinstance(scenarios, list)
            assert len(scenarios) > 0
            
            # Verify growth parameters
            growth_params = analysis["growth_parameters"]
            assert "growth_model" in growth_params
            assert "base_growth_rate" in growth_params
            assert "initial_users" in growth_params
            
            # Verify time horizons
            horizons = analysis["time_horizons"]
            assert isinstance(horizons, list)
            assert all(isinstance(h, int) for h in horizons)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, simulation_agent, sample_assessment):
        """Test error handling in agent execution."""
        # Mock a tool failure
        with patch.object(simulation_agent, '_use_tool') as mock_tool:
            mock_tool.side_effect = Exception("Tool failure")
            
            result = await simulation_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.FAILED
            assert result.error is not None
            assert "Tool failure" in result.error
            assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_generate_simulation_recommendations(self, simulation_agent):
        """Test simulation recommendation generation."""
        # Mock data for recommendation generation
        scenario_analysis = {"expected_users": 5000}
        cost_projections = {"optimization_scenarios": {"reserved_instances": {"savings": 0.20}}}
        capacity_simulations = {
            "bottleneck_analysis": {
                "critical_bottlenecks": [{
                    "resource_type": "memory",
                    "timeline": "8_months",
                    "scaling_factor": 2.0,
                    "investment_required": 75000,
                    "confidence_level": 0.90
                }]
            }
        }
        scaling_simulations = {
            "optimal_scaling_path": {
                "strategy": "hybrid",
                "efficiency_gain": 25,
                "confidence_level": 0.80
            }
        }
        performance_modeling = {
            "performance_bottlenecks": [{
                "component": "cpu",
                "impact": "significant",
                "improvement_potential": 30,
                "confidence_level": 0.75
            }]
        }
        optimization_simulations = {
            "optimization_results": {
                "cost_minimization": {
                    "potential_savings": 0.25,
                    "annual_savings": 75000,
                    "confidence_level": 0.80
                }
            }
        }
        risk_analysis = {
            "identified_risks": [{
                "risk_type": "capacity_shortage",
                "description": "Insufficient capacity during peak demand",
                "probability": 0.3,
                "impact_multiplier": 2.0,
                "severity": "high",
                "potential_cost_impact": 150000,
                "mitigation_cost": 30000
            }]
        }
        
        recommendations = await simulation_agent._generate_simulation_recommendations(
            scenario_analysis, cost_projections, capacity_simulations,
            scaling_simulations, performance_modeling, optimization_simulations, risk_analysis
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Verify recommendation structure
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
            
            # Verify implementation steps
            assert isinstance(rec["implementation_steps"], list)
            assert len(rec["implementation_steps"]) > 0
    
    def test_scenario_types_enum(self):
        """Test ScenarioType enum values."""
        assert ScenarioType.COST_PROJECTION == "cost_projection"
        assert ScenarioType.CAPACITY_PLANNING == "capacity_planning"
        assert ScenarioType.SCALING_SIMULATION == "scaling_simulation"
        assert ScenarioType.PERFORMANCE_MODELING == "performance_modeling"
        assert ScenarioType.RESOURCE_OPTIMIZATION == "resource_optimization"
        assert ScenarioType.DISASTER_RECOVERY == "disaster_recovery"
    
    def test_growth_model_enum(self):
        """Test GrowthModel enum values."""
        assert GrowthModel.LINEAR == "linear"
        assert GrowthModel.EXPONENTIAL == "exponential"
        assert GrowthModel.LOGARITHMIC == "logarithmic"
        assert GrowthModel.SEASONAL == "seasonal"
        assert GrowthModel.STEP_FUNCTION == "step_function"
        assert GrowthModel.COMPOUND == "compound"
    
    def test_simulation_parameters_dataclass(self):
        """Test SimulationParameters dataclass."""
        params = SimulationParameters(
            scenario_type=ScenarioType.COST_PROJECTION,
            time_horizon_months=12,
            growth_model=GrowthModel.LINEAR,
            confidence_level=0.95,
            monte_carlo_iterations=1000
        )
        
        assert params.scenario_type == ScenarioType.COST_PROJECTION
        assert params.time_horizon_months == 12
        assert params.growth_model == GrowthModel.LINEAR
        assert params.confidence_level == 0.95
        assert params.monte_carlo_iterations == 1000
        assert params.custom_parameters is None
    
    def test_simulation_result_dataclass(self):
        """Test SimulationResult dataclass."""
        result = SimulationResult(
            scenario_name="test_scenario",
            scenario_type=ScenarioType.COST_PROJECTION,
            time_horizon=12,
            projections=[{"month": 1, "cost": 1000}],
            confidence_intervals={"cost": (800, 1200)},
            key_metrics={"total_cost": 12000},
            risk_factors=[{"type": "market_volatility", "impact": 0.2}],
            recommendations=["Implement cost optimization"]
        )
        
        assert result.scenario_name == "test_scenario"
        assert result.scenario_type == ScenarioType.COST_PROJECTION
        assert result.time_horizon == 12
        assert len(result.projections) == 1
        assert "cost" in result.confidence_intervals
        assert result.key_metrics["total_cost"] == 12000
        assert len(result.risk_factors) == 1
        assert len(result.recommendations) == 1


class TestSimulationAgentIntegration:
    """Integration tests for Simulation Agent."""
    
    @pytest.mark.asyncio
    async def test_full_simulation_workflow(self):
        """Test complete simulation workflow."""
        # Create assessment
        assessment = Assessment(
            user_id="integration_test_user",
            title="Integration Test Assessment",
            business_requirements={
                "company_size": "large",
                "industry": "finance",
                "budget_range": "500k-2m",
                "timeline": "24_months",
                "growth_expectations": "moderate",
                "risk_tolerance": "low"
            },
            technical_requirements={
                "expected_users": 10000,
                "workload_types": ["database", "web_application"],
                "performance_requirements": {
                    "response_time": "< 200ms",
                    "availability": "99.99%"
                }
            }
        )
        
        # Create and execute agent
        agent = SimulationAgent()
        
        with patch.object(agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"analysis": "integration_test"}
            
            result = await agent.execute(assessment)
            
            # Verify successful execution
            assert result.status == AgentStatus.COMPLETED
            assert len(result.recommendations) > 0
            assert result.execution_time > 0
            
            # Verify data structure
            data = result.data
            assert "scenario_analysis" in data
            assert "cost_projections" in data
            assert "capacity_simulations" in data
            assert "scaling_simulations" in data
            assert "performance_modeling" in data
            assert "optimization_simulations" in data
            assert "risk_analysis" in data
            assert "simulation_metadata" in data
            
            # Verify recommendations have required fields
            for rec in result.recommendations:
                assert "category" in rec
                assert "priority" in rec
                assert "title" in rec
                assert "description" in rec
                assert "business_impact" in rec
    
    @pytest.mark.asyncio
    async def test_concurrent_simulations(self):
        """Test concurrent simulation executions."""
        assessments = []
        
        # Create multiple assessments
        for i in range(3):
            assessment = Assessment(
                user_id=f"concurrent_test_user_{i}",
                title=f"Concurrent Test Assessment {i+1}",
                business_requirements={
                    "company_size": "medium",
                    "budget_range": f"{100+i*100}k-{500+i*200}k",
                    "growth_expectations": ["low", "moderate", "high"][i]
                },
                technical_requirements={
                    "expected_users": 1000 * (i + 1),
                    "workload_types": ["web_application"]
                }
            )
            assessments.append(assessment)
        
        # Execute simulations concurrently
        agents = [SimulationAgent() for _ in range(3)]
        
        with patch.object(SimulationAgent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"analysis": "concurrent_test"}
            
            tasks = [agent.execute(assessment) for agent, assessment in zip(agents, assessments)]
            results = await asyncio.gather(*tasks)
            
            # Verify all executions completed successfully
            assert len(results) == 3
            for result in results:
                assert result.status == AgentStatus.COMPLETED
                assert len(result.recommendations) > 0
                assert result.execution_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])