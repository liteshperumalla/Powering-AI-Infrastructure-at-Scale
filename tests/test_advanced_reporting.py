"""
Tests for advanced reporting features.

Tests the new advanced reporting capabilities including versioning,
collaboration, templates, and interactive features.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.models.report import Report, ReportSection, ReportTemplate, ReportType, ReportFormat, ReportStatus
from src.infra_mind.services.report_service import ReportService
from src.infra_mind.agents.report_generator_agent import ReportGeneratorAgent


class TestReportVersioning:
    """Test report versioning functionality."""
    
    @pytest.fixture
    def report_service(self):
        """Create a report service instance for testing."""
        return ReportService()
    
    @pytest.fixture
    def mock_report(self):
        """Create a mock report for testing."""
        return Report(
            assessment_id="test-assessment-123",
            user_id="test-user-456",
            title="Test Report",
            description="Test report description",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
            version="1.0"
        )
    
    @pytest.mark.asyncio
    async def test_create_report_version(self, report_service, mock_report):
        """Test creating a new version of a report."""
        with patch.object(Report, 'get', return_value=mock_report):
            with patch.object(Report, 'insert', new_callable=AsyncMock):
                new_report = await report_service.create_report_version(
                    original_report_id="original-123",
                    user_id="test-user-456",
                    version="2.0",
                    changes={"title": "Updated Test Report"}
                )
                
                assert new_report.version == "2.0"
                assert new_report.parent_report_id == "original-123"
                assert new_report.title == "Updated Test Report"
    
    @pytest.mark.asyncio
    async def test_compare_report_versions(self, report_service):
        """Test comparing two report versions."""
        report1 = Report(
            assessment_id="test-assessment-123",
            user_id="test-user-456",
            title="Original Report",
            version="1.0",
            branding_config={"color": "blue"}
        )
        
        report2 = Report(
            assessment_id="test-assessment-123",
            user_id="test-user-456",
            title="Updated Report",
            version="2.0",
            branding_config={"color": "red"}
        )
        
        with patch.object(Report, 'get', side_effect=[report1, report2]):
            with patch.object(ReportSection, 'find') as mock_find:
                mock_find.return_value.to_list = AsyncMock(return_value=[])
                
                comparison = await report_service.compare_report_versions(
                    report_id_1="report-1",
                    report_id_2="report-2",
                    user_id="test-user-456"
                )
                
                assert comparison["report1"]["title"] == "Original Report"
                assert comparison["report2"]["title"] == "Updated Report"
                assert "title" in comparison["differences"]["metadata"]
                assert "branding_config" in comparison["differences"]["metadata"]


class TestReportCollaboration:
    """Test report sharing and collaboration features."""
    
    @pytest.fixture
    def report_service(self):
        """Create a report service instance for testing."""
        return ReportService()
    
    @pytest.fixture
    def mock_report(self):
        """Create a mock report for testing."""
        return Report(
            assessment_id="test-assessment-123",
            user_id="owner-user-456",
            title="Shared Report",
            shared_with=[],
            sharing_permissions={}
        )
    
    @pytest.mark.asyncio
    async def test_share_report(self, report_service, mock_report):
        """Test sharing a report with another user."""
        with patch.object(Report, 'get', return_value=mock_report):
            with patch.object(Report, 'save', new_callable=AsyncMock):
                await report_service.share_report(
                    report_id="report-123",
                    owner_id="owner-user-456",
                    share_with_user_id="shared-user-789",
                    permission="edit"
                )
                
                assert "shared-user-789" in mock_report.shared_with
                assert mock_report.sharing_permissions["shared-user-789"] == "edit"
    
    @pytest.mark.asyncio
    async def test_create_public_link(self, report_service, mock_report):
        """Test creating a public link for a report."""
        with patch.object(Report, 'get', return_value=mock_report):
            with patch.object(Report, 'save', new_callable=AsyncMock):
                public_token = await report_service.create_public_link(
                    report_id="report-123",
                    user_id="owner-user-456"
                )
                
                assert public_token is not None
                assert mock_report.is_public is True
                assert mock_report.public_link_token == public_token
    
    def test_can_user_access(self, mock_report):
        """Test user access permission checking."""
        # Owner should have access
        assert mock_report.can_user_access("owner-user-456", "admin") is True
        
        # Shared user with edit permission
        mock_report.share_with_user("shared-user-789", "edit")
        assert mock_report.can_user_access("shared-user-789", "view") is True
        assert mock_report.can_user_access("shared-user-789", "edit") is True
        assert mock_report.can_user_access("shared-user-789", "admin") is False
        
        # Public report
        mock_report.is_public = True
        assert mock_report.can_user_access("random-user-999", "view") is True
        assert mock_report.can_user_access("random-user-999", "edit") is False


class TestReportTemplates:
    """Test report template functionality."""
    
    @pytest.fixture
    def report_service(self):
        """Create a report service instance for testing."""
        return ReportService()
    
    @pytest.fixture
    def mock_template(self):
        """Create a mock report template for testing."""
        return ReportTemplate(
            name="Test Template",
            description="Test template description",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            sections_config=[
                {"title": "Executive Summary", "order": 1},
                {"title": "Recommendations", "order": 2}
            ],
            branding_config={"primary_color": "#1976d2"},
            created_by="template-creator-123",
            is_public=True
        )
    
    @pytest.mark.asyncio
    async def test_create_report_from_template(self, report_service, mock_template):
        """Test creating a report from a template."""
        with patch.object(ReportTemplate, 'get', return_value=mock_template):
            with patch.object(Report, 'insert', new_callable=AsyncMock) as mock_insert:
                with patch.object(ReportTemplate, 'save', new_callable=AsyncMock):
                    report = await report_service.create_report_from_template(
                        assessment_id="assessment-123",
                        user_id="user-456",
                        template_id="template-789",
                        custom_config={"title": "Custom Report Title"}
                    )
                    
                    assert report.title == "Custom Report Title"
                    assert report.report_type == ReportType.EXECUTIVE_SUMMARY
                    assert report.template_id == "template-789"
                    assert report.branding_config["primary_color"] == "#1976d2"
                    mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_template_from_report(self, report_service):
        """Test creating a template from an existing report."""
        mock_report = Report(
            assessment_id="assessment-123",
            user_id="user-456",
            title="Source Report",
            report_type=ReportType.TECHNICAL_ROADMAP,
            branding_config={"primary_color": "#ff5722"}
        )
        
        mock_sections = [
            ReportSection(
                report_id="report-123",
                section_id="section-1",
                title="Technical Overview",
                order=1,
                content_type="markdown",
                is_interactive=False,
                generated_by="agent"
            )
        ]
        
        with patch.object(Report, 'get', return_value=mock_report):
            with patch.object(ReportSection, 'find') as mock_find:
                mock_find.return_value.to_list = AsyncMock(return_value=mock_sections)
                with patch.object(ReportTemplate, 'insert', new_callable=AsyncMock) as mock_insert:
                    template = await report_service.create_template_from_report(
                        report_id="report-123",
                        user_id="user-456",
                        template_name="New Template",
                        template_description="Template from report",
                        is_public=False
                    )
                    
                    assert template.name == "New Template"
                    assert template.report_type == ReportType.TECHNICAL_ROADMAP
                    assert len(template.sections_config) == 1
                    assert template.sections_config[0]["title"] == "Technical Overview"
                    mock_insert.assert_called_once()
    
    def test_template_access_control(self, mock_template):
        """Test template access control."""
        # Creator should have access
        assert mock_template.can_user_access("template-creator-123") is True
        
        # Public template should be accessible to anyone
        assert mock_template.can_user_access("random-user-999") is True
        
        # Private template
        mock_template.is_public = False
        assert mock_template.can_user_access("random-user-999") is False
        
        # Organization access
        mock_template.organization_id = "org-123"
        assert mock_template.can_user_access("user-456", "org-123") is True
        assert mock_template.can_user_access("user-456", "org-456") is False


class TestInteractiveReporting:
    """Test interactive reporting features."""
    
    @pytest.fixture
    def report_generator(self):
        """Create a report generator agent for testing."""
        from src.infra_mind.agents.base import AgentConfig
        config = AgentConfig(
            name="test-report-generator",
            role="report_generator",
            model_name="gpt-4"
        )
        return ReportGeneratorAgent(config)
    
    @pytest.fixture
    def mock_recommendations(self):
        """Create mock recommendations for testing."""
        recommendations = []
        for i in range(3):
            rec = Mock()
            rec.title = f"Recommendation {i+1}"
            rec.priority = "high" if i == 0 else "medium"
            rec.estimated_cost = (i + 1) * 10000
            rec.category = "infrastructure" if i % 2 == 0 else "security"
            rec.implementation_time = "1 month"
            rec.benefits = [f"Benefit {i+1}"]
            rec.risks = [f"Risk {i+1}"]
            recommendations.append(rec)
        return recommendations
    
    def test_should_be_interactive(self, report_generator, mock_recommendations):
        """Test determining if a section should be interactive."""
        assert report_generator._should_be_interactive("Cost Analysis", mock_recommendations) is True
        assert report_generator._should_be_interactive("Recommendations Overview", mock_recommendations) is True
        assert report_generator._should_be_interactive("Business Context", mock_recommendations) is False
    
    def test_generate_drill_down_data(self, report_generator, mock_recommendations):
        """Test generating drill-down data for interactive sections."""
        drill_down_data = report_generator._generate_drill_down_data("Cost Analysis", mock_recommendations)
        
        assert "cost_breakdown" in drill_down_data
        assert "by_priority" in drill_down_data["cost_breakdown"]
        assert "by_category" in drill_down_data["cost_breakdown"]
        assert "timeline" in drill_down_data["cost_breakdown"]
    
    def test_generate_charts_config(self, report_generator, mock_recommendations):
        """Test generating chart configurations."""
        charts_config = report_generator._generate_charts_config("Cost Analysis", mock_recommendations)
        
        assert len(charts_config) == 2  # Pie chart and line chart for cost analysis
        assert charts_config[0]["type"] == "pie"
        assert charts_config[0]["title"] == "Cost Distribution by Priority"
        assert charts_config[1]["type"] == "line"
        assert charts_config[1]["title"] == "Cost Timeline"
    
    def test_group_costs_by_priority(self, report_generator, mock_recommendations):
        """Test grouping costs by priority."""
        costs_by_priority = report_generator._group_costs_by_priority(mock_recommendations)
        
        assert costs_by_priority["high"] == 10000  # First recommendation
        assert costs_by_priority["medium"] == 50000  # Second and third recommendations
        assert costs_by_priority["low"] == 0
    
    def test_generate_risk_matrix(self, report_generator, mock_recommendations):
        """Test generating risk matrix data."""
        risk_matrix = report_generator._generate_risk_matrix(mock_recommendations)
        
        assert len(risk_matrix) == 3
        for risk_item in risk_matrix:
            assert "recommendation" in risk_item
            assert "probability" in risk_item
            assert "impact" in risk_item
            assert "risk_score" in risk_item
            assert isinstance(risk_item["risk_score"], int)


class TestReportService:
    """Test the report service integration."""
    
    @pytest.fixture
    def report_service(self):
        """Create a report service instance for testing."""
        return ReportService()
    
    @pytest.mark.asyncio
    async def test_get_report_with_interactive_data(self, report_service):
        """Test getting report with interactive data."""
        mock_report = Report(
            assessment_id="assessment-123",
            user_id="user-456",
            title="Interactive Report",
            version="1.0",
            branding_config={"primary_color": "#1976d2"}
        )
        
        mock_sections = [
            ReportSection(
                report_id="report-123",
                section_id="section-1",
                title="Cost Analysis",
                order=1,
                content="Cost analysis content",
                content_type="markdown",
                is_interactive=True,
                drill_down_data={"cost_breakdown": {"by_priority": {"high": 10000}}},
                charts_config=[{"type": "pie", "title": "Cost Distribution"}]
            )
        ]
        
        with patch.object(Report, 'get', return_value=mock_report):
            with patch.object(ReportSection, 'find') as mock_find:
                mock_find.return_value.to_list = AsyncMock(return_value=mock_sections)
                
                interactive_data = await report_service.get_report_with_interactive_data(
                    report_id="report-123",
                    user_id="user-456"
                )
                
                assert interactive_data["report"]["title"] == "Interactive Report"
                assert len(interactive_data["sections"]) == 1
                assert interactive_data["sections"][0]["is_interactive"] is True
                assert "drill_down_data" in interactive_data["sections"][0]
                assert "charts_config" in interactive_data["sections"][0]
                assert len(interactive_data["navigation"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_user_reports_with_versions(self, report_service):
        """Test getting user reports with version information."""
        mock_reports = [
            Report(
                assessment_id="assessment-123",
                user_id="user-456",
                title="Report v1",
                version="1.0",
                parent_report_id=None
            ),
            Report(
                assessment_id="assessment-123",
                user_id="user-456",
                title="Report v2",
                version="2.0",
                parent_report_id="report-1"
            )
        ]
        
        with patch.object(Report, 'find') as mock_find:
            mock_find.return_value.to_list = AsyncMock(return_value=mock_reports)
            
            reports_with_versions = await report_service.get_user_reports_with_versions(
                user_id="user-456",
                include_shared=True
            )
            
            assert len(reports_with_versions) == 1  # One report group
            assert reports_with_versions[0]["total_versions"] == 2
            assert len(reports_with_versions[0]["versions"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])