"""
Tests for the CTO Agent.

Tests strategic planning, ROI calculations, and business alignment functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.infra_mind.agents.cto_agent import CTOAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


@pytest.fixture
def sample_assessment():
    """Create a sample assessment for testing."""
    from unittest.mock import Mock
    
    # Create a mock assessment to avoid database dependencies
    assessment = Mock()
    assessment.id = "test_assessment_id"
    assessment.user_id = "test_user"
    assessment.title = "Test Assessment"
    
    assessment.business_requirements = {
        "company_size": "startup",
        "industry": "technology",
        "budget_range": "$10k-50k",
        "primary_goals": ["cost_reduction", "scalability"],
        "timeline": "3-6 months"
    }
    
    assessment.technical_requirements = {
        "workload_types": ["web_application", "ai_ml"],
        "expected_users": 5000,
        "performance_requirements": {"response_time": "< 200ms"},
        "integration_needs": ["database", "api"]
    }
    
    # Mock the dict() method to return the assessment data
    assessment.dict.return_value = {
        "id": assessment.id,
        "user_id": assessment.user_id,
        "title": assessment.title,
        "business_requirements": assessment.business_requirements,
        "technical_requirements": assessment.technical_requirements
    }
    
    return assessment


@pytest.fixture
def cto_agent():
    """Create a CTO agent for testing."""
    config = AgentConfig(
        name="Test CTO Agent",
        role=AgentRole.CTO,
        tools_enabled=["data_processor", "calculator", "cloud_api"],
        metrics_enabled=False,  # Disable metrics for testing
        memory_enabled=False    # Disable memory for testing
    )
    return CTOAgent(config)


class TestCTOAgent:
    """Test the CTO Agent implementation."""
    
    def test_cto_agent_initialization(self, cto_agent):
        """Test CTO agent initialization."""
        assert cto_agent.name == "CTO Agent"
        assert cto_agent.role == AgentRole.CTO
        assert cto_agent.status == AgentStatus.IDLE
        assert "data_processor" in cto_agent.config.tools_enabled
        assert "calculator" in cto_agent.config.tools_enabled
        assert "cloud_api" in cto_agent.config.tools_enabled
        
        # Check CTO-specific attributes
        assert len(cto_agent.strategic_frameworks) > 0
        assert "Total Cost of Ownership (TCO)" in cto_agent.strategic_frameworks
        assert "Return on Investment (ROI)" in cto_agent.strategic_frameworks
        
        assert len(cto_agent.business_priorities) > 0
        assert "cost_optimization" in cto_agent.business_priorities
        assert "scalability" in cto_agent.business_priorities
    
    @pytest.mark.asyncio
    async def test_cto_agent_execution(self, cto_agent, sample_assessment):
        """Test CTO agent execution flow."""
        # Mock the tool calls to avoid external dependencies
        with patch.object(cto_agent, '_use_tool') as mock_tool:
            # Mock tool responses
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Budget range specified: $10k-50k"],
                "monthly_cost": 2500,
                "roi_percentage": 75.0,
                "payback_period_years": 1.5
            }
            
            result = await cto_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert result.agent_name == "CTO Agent"
            assert "recommendations" in result.__dict__
            assert "data" in result.__dict__
            assert result.execution_time is not None
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_business_context_analysis(self, cto_agent, sample_assessment):
        """Test business context analysis."""
        await cto_agent.initialize(sample_assessment)
        
        with patch.object(cto_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Company size: startup", "Budget range: $10k-50k"]
            }
            
            business_analysis = await cto_agent._analyze_business_context()
            
            assert "company_profile" in business_analysis
            assert "business_drivers" in business_analysis
            assert "current_challenges" in business_analysis
            
            # Check company profile extraction
            company_profile = business_analysis["company_profile"]
            assert company_profile["company_size"] == "startup"
            assert company_profile["industry"] == "technology"
            assert company_profile["budget_range"] == "$10k-50k"
            
            # Check business drivers identification
            business_drivers = business_analysis["business_drivers"]
            assert len(business_drivers) > 0
            assert any("cost" in driver.lower() for driver in business_drivers)
    
    @pytest.mark.asyncio
    async def test_strategic_alignment_assessment(self, cto_agent, sample_assessment):
        """Test strategic alignment assessment."""
        await cto_agent.initialize(sample_assessment)
        
        alignment = await cto_agent._assess_strategic_alignment()
        
        assert "alignment_score" in alignment
        assert "alignment_level" in alignment
        assert "alignment_factors" in alignment
        assert "strategic_gaps" in alignment
        
        # Check alignment score calculation
        alignment_score = alignment["alignment_score"]
        assert 0.0 <= alignment_score <= 1.0
        
        # Check alignment level categorization
        alignment_level = alignment["alignment_level"]
        assert alignment_level in ["Excellent", "Good", "Fair", "Poor"]
        
        # Check alignment factors
        alignment_factors = alignment["alignment_factors"]
        assert isinstance(alignment_factors, list)
    
    @pytest.mark.asyncio
    async def test_financial_analysis(self, cto_agent, sample_assessment):
        """Test financial analysis and ROI calculations."""
        await cto_agent.initialize(sample_assessment)
        
        with patch.object(cto_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "monthly_cost": 2500,
                "annual_cost": 30000,
                "roi_percentage": 75.0,
                "payback_period_years": 1.5
            }
            
            financial_analysis = await cto_agent._perform_financial_analysis()
            
            assert "budget_analysis" in financial_analysis
            assert "cost_projections" in financial_analysis
            assert "roi_analysis" in financial_analysis
            assert "financial_metrics" in financial_analysis
            
            # Check budget analysis
            budget_analysis = financial_analysis["budget_analysis"]
            assert budget_analysis["requested_range"] == "$10k-50k"
            assert budget_analysis["min_budget"] == 10000
            assert budget_analysis["max_budget"] == 50000
            
            # Check financial metrics
            financial_metrics = financial_analysis["financial_metrics"]
            assert "average_budget" in financial_metrics
            assert "cost_per_user" in financial_metrics
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self, cto_agent, sample_assessment):
        """Test business risk assessment."""
        await cto_agent.initialize(sample_assessment)
        
        risk_assessment = await cto_agent._assess_business_risks()
        
        assert "identified_risks" in risk_assessment
        assert "risk_matrix" in risk_assessment
        assert "mitigation_priorities" in risk_assessment
        assert "overall_risk_level" in risk_assessment
        
        # Check identified risks
        risks = risk_assessment["identified_risks"]
        assert isinstance(risks, list)
        assert len(risks) > 0
        
        # Check risk structure
        for risk in risks:
            assert "category" in risk
            assert "risk" in risk
            assert "impact" in risk
            assert "probability" in risk
            assert "mitigation" in risk
        
        # Check overall risk level
        overall_risk = risk_assessment["overall_risk_level"]
        assert overall_risk in ["High", "Medium", "Low"]
    
    @pytest.mark.asyncio
    async def test_strategic_recommendations_generation(self, cto_agent, sample_assessment):
        """Test strategic recommendations generation."""
        await cto_agent.initialize(sample_assessment)
        
        # Mock analysis results
        business_analysis = {
            "company_profile": {"company_size": "startup"},
            "growth_trajectory": {"growth_rate": "high"}
        }
        
        strategic_alignment = {
            "alignment_score": 0.5,
            "alignment_level": "Fair"
        }
        
        financial_analysis = {
            "roi_analysis": {"roi_percentage": 30}
        }
        
        risk_assessment = {
            "identified_risks": [
                {
                    "category": "technology",
                    "risk": "AI/ML Complexity",
                    "impact": "high",
                    "probability": "medium",
                    "mitigation": "Use managed AI services"
                }
            ]
        }
        
        recommendations = await cto_agent._generate_strategic_recommendations(
            business_analysis, strategic_alignment, financial_analysis, risk_assessment
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec
            assert "actions" in rec
            assert "business_impact" in rec
            assert "timeline" in rec
            
            # Check priority values
            assert rec["priority"] in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_executive_summary_creation(self, cto_agent):
        """Test executive summary creation."""
        recommendations = [
            {
                "category": "strategic_alignment",
                "priority": "high",
                "title": "Improve Strategic Alignment",
                "description": "Test recommendation",
                "actions": ["Action 1", "Action 2"],
                "business_impact": "High impact",
                "timeline": "2-4 weeks"
            },
            {
                "category": "financial_optimization",
                "priority": "medium",
                "title": "Optimize Costs",
                "description": "Test recommendation",
                "actions": ["Action 3"],
                "business_impact": "Medium impact",
                "timeline": "1-2 months"
            }
        ]
        
        executive_summary = await cto_agent._create_executive_summary(recommendations)
        
        assert "key_findings" in executive_summary
        assert "strategic_priorities" in executive_summary
        assert "investment_summary" in executive_summary
        assert "business_impact" in executive_summary
        assert "next_steps" in executive_summary
        
        # Check investment summary
        investment_summary = executive_summary["investment_summary"]
        assert investment_summary["total_recommendations"] == 2
        assert investment_summary["high_priority_count"] == 1
        assert "estimated_investment" in investment_summary
        assert "expected_timeline" in investment_summary
    
    def test_helper_methods(self, cto_agent):
        """Test helper methods."""
        # Test budget range parsing
        min_budget, max_budget = cto_agent._parse_budget_range("$10k-50k")
        assert min_budget == 10000
        assert max_budget == 50000
        
        # Test scaling factor
        scaling_factor = cto_agent._get_scaling_factor("startup")
        assert scaling_factor == 1.5
        
        # Test alignment categorization
        assert cto_agent._categorize_alignment(0.9) == "Excellent"
        assert cto_agent._categorize_alignment(0.7) == "Good"
        assert cto_agent._categorize_alignment(0.5) == "Fair"
        assert cto_agent._categorize_alignment(0.3) == "Poor"
        
        # Test annual savings estimation
        savings = cto_agent._estimate_annual_savings("startup", 1000)
        assert savings > 0
        assert isinstance(savings, float)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cto_agent, sample_assessment):
        """Test error handling in CTO agent."""
        with patch.object(cto_agent, '_use_tool') as mock_tool:
            # Mock tool failure
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = False
            mock_tool.return_value.error = "Tool execution failed"
            
            result = await cto_agent.execute(sample_assessment)
            
            # Agent should handle tool failures gracefully
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
            
            if result.status == AgentStatus.FAILED:
                assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, cto_agent):
        """Test agent health check."""
        health = await cto_agent.health_check()
        
        assert "agent_name" in health
        assert "status" in health
        assert "role" in health
        assert health["agent_name"] == "CTO Agent"
        assert health["role"] == "cto"
    
    def test_capabilities(self, cto_agent):
        """Test agent capabilities reporting."""
        capabilities = cto_agent.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert any("Role: cto" in cap for cap in capabilities)
        assert any("Tools:" in cap for cap in capabilities)


class TestCTOAgentIntegration:
    """Integration tests for CTO Agent."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, sample_assessment):
        """Test full CTO agent workflow integration."""
        from src.infra_mind.agents import agent_registry, AgentFactory
        
        # Create agent through factory
        factory = AgentFactory(agent_registry)
        cto_agent = await factory.create_agent(AgentRole.CTO)
        
        assert cto_agent is not None
        assert isinstance(cto_agent, CTOAgent)
        
        # Mock tool calls for integration test
        with patch.object(cto_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["Test insight"],
                "monthly_cost": 1000,
                "roi_percentage": 50.0
            }
            
            result = await cto_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert len(result.recommendations) > 0
            assert "business_analysis" in result.data
            assert "strategic_alignment" in result.data
            assert "financial_analysis" in result.data
            assert "risk_assessment" in result.data
            assert "executive_summary" in result.data


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(pytest.main([__file__, "-v"]))