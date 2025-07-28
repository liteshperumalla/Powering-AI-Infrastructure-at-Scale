"""
Tests for AI Consultant Agent.

Tests the AI Consultant Agent's capabilities for generative AI business integration
and strategy consulting.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from src.infra_mind.agents.ai_consultant_agent import AIConsultantAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


@pytest.fixture
def sample_assessment():
    """Create a sample assessment for testing."""
    # Create a mock assessment object that mimics the Assessment model structure
    class MockAssessment:
        def __init__(self):
            self.id = "test_assessment_id_123"
            self.user_id = "test_user_123"
            self.title = "Healthcare AI Transformation Assessment"
            self.description = "Assessment for healthcare AI infrastructure transformation"
            self.business_requirements = {
                "company_size": "medium",
                "industry": "healthcare",
                "budget_range": "$50k-100k",
                "primary_goals": ["efficiency", "innovation", "compliance"],
                "timeline": "6-12 months",
                "compliance_requirements": {
                    "regulations": ["HIPAA", "GDPR"],
                    "data_residency": "US"
                }
            }
            self.technical_requirements = {
                "workload_types": ["web_application", "database", "api"],
                "expected_users": 5000,
                "performance_requirements": {
                    "response_time": "< 2 seconds",
                    "availability": "99.9%"
                }
            }
        
        def dict(self):
            """Return dictionary representation like Pydantic models."""
            return {
                "id": self.id,
                "user_id": self.user_id,
                "title": self.title,
                "description": self.description,
                "business_requirements": self.business_requirements,
                "technical_requirements": self.technical_requirements
            }
    
    return MockAssessment()


@pytest.fixture
def ai_consultant_agent():
    """Create an AI Consultant Agent for testing."""
    config = AgentConfig(
        name="Test AI Consultant Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for testing
    )
    return AIConsultantAgent(config)


class TestAIConsultantAgent:
    """Test cases for AI Consultant Agent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = AIConsultantAgent()
        
        assert agent.config.name == "AI Consultant Agent"
        assert agent.config.role == AgentRole.AI_CONSULTANT
        assert agent.config.temperature == 0.3
        assert agent.config.max_tokens == 2500
        assert "business_process_analysis" in agent.config.custom_config["focus_areas"]
        assert "generative_ai" in agent.config.custom_config["ai_domains"]
        assert "healthcare" in agent.config.custom_config["industry_expertise"]
        
        # Check AI use cases
        assert "customer_service" in agent.ai_use_cases
        assert "content_generation" in agent.ai_use_cases
        assert "predictive_analytics" in agent.ai_use_cases
        
        # Check transformation frameworks
        assert "AI Readiness Assessment" in agent.transformation_frameworks
        assert "Business Process Mapping" in agent.transformation_frameworks
    
    @pytest.mark.asyncio
    async def test_execute_main_logic(self, ai_consultant_agent, sample_assessment):
        """Test main execution logic."""
        # Mock tool usage
        with patch.object(ai_consultant_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = Mock(
                is_success=True,
                data={"insights": ["Test insight"]}
            )
            
            result = await ai_consultant_agent._execute_main_logic()
            
            assert isinstance(result, dict)
            assert "recommendations" in result
            assert "data" in result
            assert "business_process_analysis" in result["data"]
            assert "ai_opportunities" in result["data"]
            assert "readiness_assessment" in result["data"]
            assert "transformation_strategy" in result["data"]
            assert "implementation_roadmap" in result["data"]
            assert "ethics_governance" in result["data"]
    
    @pytest.mark.asyncio
    async def test_analyze_business_processes(self, ai_consultant_agent, sample_assessment):
        """Test business process analysis."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        with patch.object(ai_consultant_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = Mock(
                is_success=True,
                data={"insights": ["Healthcare industry analysis"]}
            )
            
            result = await ai_consultant_agent._analyze_business_processes()
            
            assert isinstance(result, dict)
            assert "industry_context" in result
            assert "key_processes" in result
            assert "process_assessment" in result
            assert "automation_potential" in result
            
            industry_context = result["industry_context"]
            assert industry_context["industry"] == "healthcare"
            assert industry_context["company_size"] == "medium"
            
            key_processes = result["key_processes"]
            assert len(key_processes) > 0
            assert any("Patient Care" in process["name"] for process in key_processes)
    
    @pytest.mark.asyncio
    async def test_identify_ai_opportunities(self, ai_consultant_agent, sample_assessment):
        """Test AI opportunities identification."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        result = await ai_consultant_agent._identify_ai_opportunities()
        
        assert isinstance(result, dict)
        assert "industry_context" in result
        assert "budget_constraints" in result
        assert "relevant_use_cases" in result
        assert "feasible_use_cases" in result
        assert "prioritized_opportunities" in result
        
        assert result["industry_context"] == "healthcare"
        
        budget_constraints = result["budget_constraints"]
        assert budget_constraints["min"] == 50000
        assert budget_constraints["max"] == 100000
        
        relevant_use_cases = result["relevant_use_cases"]
        assert "predictive_analytics" in relevant_use_cases
        assert "document_processing" in relevant_use_cases
        
        prioritized_opportunities = result["prioritized_opportunities"]
        assert len(prioritized_opportunities) > 0
        assert all("use_case" in opp for opp in prioritized_opportunities)
        assert all("priority_score" in opp for opp in prioritized_opportunities)
    
    @pytest.mark.asyncio
    async def test_assess_ai_readiness(self, ai_consultant_agent, sample_assessment):
        """Test AI readiness assessment."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        result = await ai_consultant_agent._assess_ai_readiness()
        
        assert isinstance(result, dict)
        assert "overall_readiness_score" in result
        assert "readiness_level" in result
        assert "readiness_dimensions" in result
        assert "readiness_gaps" in result
        assert "improvement_priorities" in result
        
        assert 0 <= result["overall_readiness_score"] <= 1
        
        readiness_dimensions = result["readiness_dimensions"]
        expected_dimensions = [
            "data_readiness", "technical_readiness", "organizational_readiness",
            "cultural_readiness", "governance_readiness"
        ]
        for dimension in expected_dimensions:
            assert dimension in readiness_dimensions
            assert "score" in readiness_dimensions[dimension]
            assert "level" in readiness_dimensions[dimension]
    
    @pytest.mark.asyncio
    async def test_generate_use_case_recommendations(self, ai_consultant_agent, sample_assessment):
        """Test use case recommendations generation."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        # Mock business analysis and AI opportunities
        business_analysis = {
            "automation_potential": {"overall_score": 0.7}
        }
        ai_opportunities = {
            "prioritized_opportunities": [
                {
                    "use_case": "customer_service",
                    "priority_score": 0.8,
                    "business_value": "Improved patient communication",
                    "implementation_time": "3-4 months",
                    "estimated_cost": "$30,000 - $60,000"
                },
                {
                    "use_case": "predictive_analytics",
                    "priority_score": 0.7,
                    "business_value": "Better patient outcomes",
                    "implementation_time": "6-8 months",
                    "estimated_cost": "$60,000 - $120,000"
                }
            ]
        }
        
        result = await ai_consultant_agent._generate_use_case_recommendations(
            business_analysis, ai_opportunities
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        for recommendation in result:
            assert "category" in recommendation
            assert "priority" in recommendation
            assert "title" in recommendation
            assert "description" in recommendation
            assert "business_value" in recommendation
            assert "technologies_required" in recommendation
            assert "success_metrics" in recommendation
            assert "risks_and_mitigation" in recommendation
            assert "next_steps" in recommendation
    
    @pytest.mark.asyncio
    async def test_create_transformation_strategy(self, ai_consultant_agent, sample_assessment):
        """Test transformation strategy creation."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        readiness_assessment = {
            "overall_readiness_score": 0.6
        }
        use_case_recommendations = [
            {"title": "Implement AI Chatbot", "implementation_complexity": "medium"},
            {"title": "Predictive Analytics", "implementation_complexity": "high"}
        ]
        
        result = await ai_consultant_agent._create_transformation_strategy(
            readiness_assessment, use_case_recommendations
        )
        
        assert isinstance(result, dict)
        assert "strategy_approach" in result
        assert "transformation_phases" in result
        assert "phased_recommendations" in result
        assert "success_criteria" in result
        assert "investment_analysis" in result
        assert "change_management_strategy" in result
        assert "risk_mitigation_plan" in result
        
        assert result["strategy_approach"] in ["foundation_first", "pilot_driven", "accelerated"]
        assert len(result["transformation_phases"]) > 0
        assert len(result["success_criteria"]) > 0
    
    @pytest.mark.asyncio
    async def test_address_ethics_and_governance(self, ai_consultant_agent, sample_assessment):
        """Test ethics and governance framework."""
        ai_consultant_agent.current_assessment = sample_assessment
        
        result = await ai_consultant_agent._address_ethics_and_governance()
        
        assert isinstance(result, dict)
        assert "core_principles" in result
        assert "governance_structure" in result
        assert "compliance_considerations" in result
        assert "risk_assessment" in result
        assert "monitoring_framework" in result
        assert "training_requirements" in result
        
        core_principles = result["core_principles"]
        assert "Transparency and Explainability" in core_principles
        assert "Fairness and Non-discrimination" in core_principles
        
        compliance_considerations = result["compliance_considerations"]
        assert "applicable_regulations" in compliance_considerations
        assert "HIPAA" in compliance_considerations["applicable_regulations"]
        assert "GDPR" in compliance_considerations["applicable_regulations"]
    
    def test_identify_key_processes(self, ai_consultant_agent):
        """Test key process identification."""
        # Test healthcare industry
        processes = ai_consultant_agent._identify_key_processes("healthcare", ["efficiency"])
        assert len(processes) > 0
        assert any("Patient Care" in process["name"] for process in processes)
        assert any("Medical Records" in process["name"] for process in processes)
        
        # Test technology industry
        processes = ai_consultant_agent._identify_key_processes("technology", ["innovation"])
        assert len(processes) > 0
        assert any("Software Development" in process["name"] for process in processes)
        
        # Test unknown industry
        processes = ai_consultant_agent._identify_key_processes("unknown", [])
        assert len(processes) > 0
        assert any("Customer Service" in process["name"] for process in processes)
    
    def test_get_industry_specific_use_cases(self, ai_consultant_agent):
        """Test industry-specific use case identification."""
        # Test healthcare
        use_cases = ai_consultant_agent._get_industry_specific_use_cases("healthcare")
        assert "predictive_analytics" in use_cases
        assert "document_processing" in use_cases
        
        # Test finance
        use_cases = ai_consultant_agent._get_industry_specific_use_cases("finance")
        assert "predictive_analytics" in use_cases
        assert "process_automation" in use_cases
        
        # Test retail
        use_cases = ai_consultant_agent._get_industry_specific_use_cases("retail")
        assert "recommendation_systems" in use_cases
        
        # Test unknown industry
        use_cases = ai_consultant_agent._get_industry_specific_use_cases("unknown")
        assert "customer_service" in use_cases
    
    def test_parse_budget_range(self, ai_consultant_agent):
        """Test budget range parsing."""
        # Test different budget ranges
        min_budget, max_budget = ai_consultant_agent._parse_budget_range("$1k-10k")
        assert min_budget == 1000
        assert max_budget == 10000
        
        min_budget, max_budget = ai_consultant_agent._parse_budget_range("$50k-100k")
        assert min_budget == 50000
        assert max_budget == 100000
        
        min_budget, max_budget = ai_consultant_agent._parse_budget_range("$100k+")
        assert min_budget == 100000
        assert max_budget == 500000
        
        # Test unknown range
        min_budget, max_budget = ai_consultant_agent._parse_budget_range("unknown")
        assert min_budget == 10000
        assert max_budget == 50000
    
    def test_filter_use_cases_by_budget(self, ai_consultant_agent):
        """Test use case filtering by budget."""
        use_cases = ["customer_service", "content_generation", "predictive_analytics"]
        
        # Test low budget
        filtered = ai_consultant_agent._filter_use_cases_by_budget(use_cases, 30000)
        assert "customer_service" in filtered
        assert "content_generation" in filtered
        assert "predictive_analytics" not in filtered  # Too expensive
        
        # Test high budget
        filtered = ai_consultant_agent._filter_use_cases_by_budget(use_cases, 100000)
        assert len(filtered) == len(use_cases)  # All should be included
    
    def test_assess_readiness_dimensions(self, ai_consultant_agent):
        """Test individual readiness dimension assessments."""
        # Test data readiness
        technical_req = {"workload_types": ["database", "analytics"]}
        result = ai_consultant_agent._assess_data_readiness(technical_req)
        assert "score" in result
        assert "level" in result
        assert "gaps" in result
        assert 0 <= result["score"] <= 1
        
        # Test technical readiness
        technical_req = {"workload_types": ["web_application", "ai_ml"], "expected_users": 5000}
        result = ai_consultant_agent._assess_technical_readiness(technical_req)
        assert result["score"] > 0.5  # Should be higher with AI/ML workloads
        
        # Test organizational readiness
        business_req = {"company_size": "medium", "primary_goals": ["innovation"]}
        result = ai_consultant_agent._assess_organizational_readiness(business_req)
        assert result["score"] > 0.5  # Medium company with innovation focus
        
        # Test cultural readiness
        business_req = {"industry": "technology", "company_size": "startup"}
        result = ai_consultant_agent._assess_cultural_readiness(business_req)
        assert result["score"] > 0.6  # Tech startup should have high cultural readiness
        
        # Test governance readiness
        business_req = {"company_size": "enterprise", "industry": "finance"}
        result = ai_consultant_agent._assess_governance_readiness(business_req)
        assert result["score"] > 0.7  # Large finance company should have good governance
    
    def test_categorize_readiness(self, ai_consultant_agent):
        """Test readiness score categorization."""
        assert "Excellent" in ai_consultant_agent._categorize_readiness(0.9)
        assert "Good" in ai_consultant_agent._categorize_readiness(0.7)
        assert "Fair" in ai_consultant_agent._categorize_readiness(0.5)
        assert "Poor" in ai_consultant_agent._categorize_readiness(0.2)
    
    def test_define_success_metrics(self, ai_consultant_agent):
        """Test success metrics definition."""
        # Test customer service metrics
        metrics = ai_consultant_agent._define_success_metrics("customer_service")
        assert len(metrics) > 0
        assert any("satisfaction" in metric.lower() for metric in metrics)
        
        # Test content generation metrics
        metrics = ai_consultant_agent._define_success_metrics("content_generation")
        assert len(metrics) > 0
        assert any("production" in metric.lower() for metric in metrics)
        
        # Test unknown use case
        metrics = ai_consultant_agent._define_success_metrics("unknown")
        assert len(metrics) > 0
        assert any("adoption" in metric.lower() for metric in metrics)
    
    def test_identify_risks_and_mitigation(self, ai_consultant_agent):
        """Test risk identification and mitigation."""
        # Test customer service risks
        risks = ai_consultant_agent._identify_risks_and_mitigation("customer_service")
        assert len(risks) > 0
        assert any("resistance" in risk.lower() for risk in risks)
        
        # Test predictive analytics risks
        risks = ai_consultant_agent._identify_risks_and_mitigation("predictive_analytics")
        assert len(risks) > 0
        assert any("bias" in risk.lower() for risk in risks)
        
        # Test unknown use case
        risks = ai_consultant_agent._identify_risks_and_mitigation("unknown")
        assert len(risks) > 0
    
    def test_estimate_implementation_time_and_cost(self, ai_consultant_agent):
        """Test implementation time and cost estimation."""
        # Test time estimation
        time_estimate = ai_consultant_agent._estimate_implementation_time("customer_service", "medium")
        assert "months" in time_estimate
        assert "-" in time_estimate  # Should be a range
        
        # Test cost estimation
        cost_estimate = ai_consultant_agent._estimate_implementation_cost("customer_service", "medium")
        assert "$" in cost_estimate
        assert "-" in cost_estimate  # Should be a range
        assert "," in cost_estimate  # Should have comma separators
        
        # Test different company sizes affect estimates
        startup_time = ai_consultant_agent._estimate_implementation_time("customer_service", "startup")
        enterprise_time = ai_consultant_agent._estimate_implementation_time("customer_service", "enterprise")
        # Enterprise should take longer (higher multiplier)
        assert startup_time != enterprise_time
    
    @pytest.mark.asyncio
    async def test_full_agent_execution(self, ai_consultant_agent, sample_assessment):
        """Test full agent execution."""
        with patch.object(ai_consultant_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = Mock(
                is_success=True,
                data={"insights": ["Test insight"]}
            )
            
            result = await ai_consultant_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert result.agent_name == "Test AI Consultant Agent"
            assert len(result.recommendations) > 0
            assert result.data is not None
            assert result.execution_time is not None
            assert result.execution_time > 0
            
            # Check that all expected data components are present
            data = result.data
            assert "business_process_analysis" in data
            assert "ai_opportunities" in data
            assert "readiness_assessment" in data
            assert "transformation_strategy" in data
            assert "implementation_roadmap" in data
            assert "ethics_governance" in data
            assert "frameworks_used" in data
            assert "analysis_timestamp" in data
    
    def test_ai_use_cases_structure(self, ai_consultant_agent):
        """Test AI use cases data structure."""
        for use_case_name, use_case_details in ai_consultant_agent.ai_use_cases.items():
            assert "description" in use_case_details
            assert "technologies" in use_case_details
            assert "roi_potential" in use_case_details
            assert "implementation_complexity" in use_case_details
            
            # Check valid values
            assert use_case_details["roi_potential"] in ["low", "medium", "high", "very_high"]
            assert use_case_details["implementation_complexity"] in ["low", "medium", "high"]
            assert isinstance(use_case_details["technologies"], list)
    
    def test_transformation_frameworks(self, ai_consultant_agent):
        """Test transformation frameworks list."""
        frameworks = ai_consultant_agent.transformation_frameworks
        
        expected_frameworks = [
            "AI Readiness Assessment",
            "Business Process Mapping",
            "AI Opportunity Matrix",
            "Change Management Strategy",
            "Ethics and Governance Framework",
            "Implementation Roadmap"
        ]
        
        for framework in expected_frameworks:
            assert framework in frameworks


if __name__ == "__main__":
    pytest.main([__file__])