"""
Tests for the Report Generator Agent.

Tests report generation functionality, different report types, and content quality.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.infra_mind.agents.report_generator_agent import (
    ReportGeneratorAgent, 
    Report, 
    ReportSection
)
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus


@pytest.fixture(autouse=True)
def stub_report_agent_dependencies(monkeypatch):
    """Prevent external API/DB calls in report generator tests."""
    async def fake_collect(self, assessment, recommendations):
        return {
            "market_intelligence": {},
            "technology_trends": {},
            "industry_insights": {},
            "competitive_analysis": {},
        }

    async def fake_store(self, report, assessment):
        return "mock_report_id"

    monkeypatch.setattr(
        ReportGeneratorAgent,
        "_collect_research_data",
        fake_collect,
    )
    monkeypatch.setattr(
        ReportGeneratorAgent,
        "_store_report_in_database",
        fake_store,
    )


class TestReportSection:
    """Test suite for ReportSection."""
    
    def test_report_section_creation(self):
        """Test creating a report section."""
        section = ReportSection(
            title="Test Section",
            content="This is test content",
            order=1
        )
        
        assert section.title == "Test Section"
        assert section.content == "This is test content"
        assert section.order == 1
        assert len(section.subsections) == 0
    
    def test_report_section_to_dict(self):
        """Test converting section to dictionary."""
        section = ReportSection(
            title="Test Section",
            content="This is test content",
            order=1,
            metadata={"test": "value"}
        )
        
        section_dict = section.to_dict()
        
        assert section_dict["title"] == "Test Section"
        assert section_dict["content"] == "This is test content"
        assert section_dict["order"] == 1
        assert section_dict["metadata"] == {"test": "value"}
        assert section_dict["subsections"] == []


class TestReport:
    """Test suite for Report."""
    
    def test_report_creation(self):
        """Test creating a report."""
        report = Report(
            id="test_report_123",
            title="Test Report",
            assessment_id="assessment_123",
            report_type="executive"
        )
        
        assert report.id == "test_report_123"
        assert report.title == "Test Report"
        assert report.assessment_id == "assessment_123"
        assert report.report_type == "executive"
        assert len(report.sections) == 0
    
    def test_add_section(self):
        """Test adding sections to a report."""
        report = Report(
            id="test_report_123",
            title="Test Report",
            assessment_id="assessment_123",
            report_type="executive"
        )
        
        section1 = ReportSection(title="Section 1", content="Content 1", order=2)
        section2 = ReportSection(title="Section 2", content="Content 2", order=1)
        
        report.add_section(section1)
        report.add_section(section2)
        
        # Should be sorted by order
        assert len(report.sections) == 2
        assert report.sections[0].title == "Section 2"  # order=1
        assert report.sections[1].title == "Section 1"  # order=2
    
    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = Report(
            id="test_report_123",
            title="Test Report",
            assessment_id="assessment_123",
            report_type="executive"
        )
        
        section = ReportSection(title="Test Section", content="Test content", order=1)
        report.add_section(section)
        
        report_dict = report.to_dict()
        
        assert report_dict["id"] == "test_report_123"
        assert report_dict["title"] == "Test Report"
        assert report_dict["assessment_id"] == "assessment_123"
        assert report_dict["report_type"] == "executive"
        assert len(report_dict["sections"]) == 1
        assert report_dict["sections"][0]["title"] == "Test Section"
    
    def test_report_to_markdown(self):
        """Test converting report to markdown."""
        report = Report(
            id="test_report_123",
            title="Test Report",
            assessment_id="assessment_123",
            report_type="executive"
        )
        
        section = ReportSection(title="Test Section", content="Test content", order=1)
        report.add_section(section)
        
        markdown = report.to_markdown()
        
        assert "# Test Report" in markdown
        assert "**Report ID:** test_report_123" in markdown
        assert "**Assessment ID:** assessment_123" in markdown
        assert "## Test Section" in markdown
        assert "Test content" in markdown


class TestReportGeneratorAgent:
    """Test suite for ReportGeneratorAgent."""
    
    def test_agent_creation(self):
        """Test creating a report generator agent."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        assert agent.name == "Test Report Generator"
        assert agent.role == AgentRole.REPORT_GENERATOR
        assert len(agent.report_templates) > 0
        assert "executive" in agent.report_templates
        assert "technical" in agent.report_templates
        assert "full" in agent.report_templates
    
    def test_report_templates(self):
        """Test report templates are properly loaded."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        # Check executive template
        exec_template = agent.report_templates["executive"]
        assert "title_template" in exec_template
        assert "sections" in exec_template
        assert len(exec_template["sections"]) > 0
        
        # Check technical template
        tech_template = agent.report_templates["technical"]
        assert "title_template" in tech_template
        assert "sections" in tech_template
        assert len(tech_template["sections"]) > 0
        
        # Check full template
        full_template = agent.report_templates["full"]
        assert "title_template" in full_template
        assert "sections" in full_template
        assert len(full_template["sections"]) > 0
    
    def create_sample_assessment(self):
        """Create sample assessment data for testing."""
        return {
            "id": "test_assessment_123",
            "title": "Test Assessment",
            "business_requirements": {
                "company_name": "Test Company",
                "industry": "technology",
                "company_size": "medium",
                "primary_goals": ["cost_reduction", "scalability"],
                "budget_range": "100k_500k",
                "timeline": "medium_term",
                "infrastructure_maturity": "intermediate",
                "main_challenges": ["high_costs", "scalability_issues"]
            },
            "technical_requirements": {
                "current_hosting": ["aws"],
                "current_technologies": ["containers", "databases"],
                "team_expertise": "intermediate",
                "workload_types": ["web_applications", "apis"],
                "expected_users": 5000,
                "data_volume": "100gb_1tb",
                "performance_requirements": ["high_availability", "auto_scaling"],
                "preferred_cloud_providers": ["aws", "azure"],
                "compliance_requirements": ["gdpr"],
                "security_requirements": ["encryption_at_rest", "network_isolation"]
            }
        }
    
    def create_sample_recommendations(self):
        """Create sample recommendations for testing."""
        return [
            {
                "id": "rec_1",
                "title": "Test Recommendation 1",
                "description": "This is a test recommendation",
                "category": "infrastructure",
                "priority": "high",
                "estimated_cost": 50000,
                "implementation_time": "3 months",
                "benefits": ["Improved performance", "Cost savings"],
                "risks": ["Implementation complexity"]
            },
            {
                "id": "rec_2",
                "title": "Test Recommendation 2",
                "description": "This is another test recommendation",
                "category": "security",
                "priority": "medium",
                "estimated_cost": 25000,
                "implementation_time": "2 months",
                "benefits": ["Enhanced security"],
                "risks": ["Learning curve"]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_execute_main_logic_success(self):
        """Test successful report generation."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        # Set context
        agent.context = {
            "assessment": self.create_sample_assessment(),
            "recommendations": self.create_sample_recommendations(),
            "report_type": "executive"
        }
        
        # Execute main logic
        result = await agent._execute_main_logic()
        
        # Check result
        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == "Test Report Generator"
        assert "report" in result.data
        assert "report_markdown" in result.data
        assert "report_id" in result.data
        assert "report_type" in result.data
        assert result.data["report_type"] == "executive"
        
        # Check report structure
        report_dict = result.data["report"]
        assert report_dict["title"] == "Infrastructure Assessment Report - Test Company"
        assert report_dict["assessment_id"] == "test_assessment_123"
        assert report_dict["report_type"] == "executive"
        assert len(report_dict["sections"]) > 0
        
        # Check markdown content
        markdown = result.data["report_markdown"]
        assert "# Infrastructure Assessment Report - Test Company" in markdown
        assert "Test Company" in markdown
        assert "Executive Summary" in markdown
    
    @pytest.mark.asyncio
    async def test_execute_main_logic_different_report_types(self):
        """Test generating different report types."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        assessment = self.create_sample_assessment()
        recommendations = self.create_sample_recommendations()
        
        report_types = ["executive", "technical", "full"]
        
        for report_type in report_types:
            agent.context = {
                "assessment": assessment,
                "recommendations": recommendations,
                "report_type": report_type
            }
            
            result = await agent._execute_main_logic()
            
            assert result.status == AgentStatus.COMPLETED
            assert result.data["report_type"] == report_type
            
            report_dict = result.data["report"]
            
            # Check that different report types have different section counts
            if report_type == "executive":
                assert len(report_dict["sections"]) == 6
            elif report_type == "technical":
                assert len(report_dict["sections"]) == 7
            elif report_type == "full":
                assert len(report_dict["sections"]) == 10
    
    @pytest.mark.asyncio
    async def test_execute_main_logic_no_assessment(self):
        """Test error handling when no assessment is provided."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        # Set context without assessment
        agent.context = {
            "recommendations": self.create_sample_recommendations(),
            "report_type": "executive"
        }
        
        # Execute main logic
        result = await agent._execute_main_logic()
        
        # Check result
        assert result.status == AgentStatus.FAILED
        assert result.error is not None
        assert "No assessment data provided" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_section_executive_summary(self):
        """Test generating executive summary section."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        # Create mock assessment and recommendations
        assessment = agent._dict_to_assessment(self.create_sample_assessment())
        recommendations = [agent._dict_to_recommendation(rec) for rec in self.create_sample_recommendations()]
        
        # Generate executive summary section
        section = await agent._generate_section("Executive Summary", 1, assessment, recommendations)
        
        assert section.title == "Executive Summary"
        assert section.order == 1
        assert len(section.content) > 0
        assert "Test Company" in section.content
        assert "technology" in section.content
        assert "2 strategic recommendations" in section.content
    
    @pytest.mark.asyncio
    async def test_generate_section_cost_analysis(self):
        """Test generating cost analysis section."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        # Create mock assessment and recommendations
        assessment = agent._dict_to_assessment(self.create_sample_assessment())
        recommendations = [agent._dict_to_recommendation(rec) for rec in self.create_sample_recommendations()]
        
        # Generate cost analysis section
        section = await agent._generate_section("Cost Analysis", 1, assessment, recommendations)
        
        assert section.title == "Cost Analysis"
        assert section.order == 1
        assert len(section.content) > 0
        assert "$75,000.00" in section.content  # Total cost of recommendations
        assert "Investment Overview" in section.content
        assert "Cost Breakdown by Priority" in section.content
    
    def test_dict_to_assessment(self):
        """Test converting dictionary to assessment object."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        assessment_data = self.create_sample_assessment()
        assessment = agent._dict_to_assessment(assessment_data)
        
        assert assessment.id == "test_assessment_123"
        assert assessment.title == "Test Assessment"
        assert assessment.business_requirements == assessment_data["business_requirements"]
        assert assessment.technical_requirements == assessment_data["technical_requirements"]
    
    def test_dict_to_recommendation(self):
        """Test converting dictionary to recommendation object."""
        config = AgentConfig(
            name="Test Report Generator",
            role=AgentRole.REPORT_GENERATOR,
            metrics_enabled=False
        )
        
        agent = ReportGeneratorAgent(config)
        
        rec_data = self.create_sample_recommendations()[0]
        recommendation = agent._dict_to_recommendation(rec_data)
        
        assert recommendation.id == "rec_1"
        assert recommendation.title == "Test Recommendation 1"
        assert recommendation.description == "This is a test recommendation"
        assert recommendation.category == "infrastructure"
        assert recommendation.priority == "high"
        assert recommendation.estimated_cost == 50000
        assert recommendation.implementation_time == "3 months"
        assert recommendation.benefits == ["Improved performance", "Cost savings"]
        assert recommendation.risks == ["Implementation complexity"]
