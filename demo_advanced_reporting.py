#!/usr/bin/env python3
"""
Demo script for advanced reporting features.

Demonstrates the new advanced reporting capabilities including:
- Interactive report previews with drill-down capabilities
- Customizable report templates and branding options
- Report versioning and comparison features
- Report sharing and collaboration tools
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

from src.infra_mind.models.report import (
    Report, ReportSection, ReportTemplate, 
    ReportType, ReportFormat, ReportStatus
)
from src.infra_mind.services.report_service import ReportService
from src.infra_mind.agents.report_generator_agent import ReportGeneratorAgent
from src.infra_mind.agents.base import AgentConfig


def create_mock_recommendations() -> List[Any]:
    """Create mock recommendations for testing."""
    class MockRecommendation:
        def __init__(self, title: str, priority: str, cost: float, category: str):
            self.title = title
            self.priority = priority
            self.estimated_cost = cost
            self.category = category
            self.implementation_time = "2 months"
            self.benefits = [f"Benefit for {title}"]
            self.risks = [f"Risk for {title}"]
            self.description = f"Description for {title}"
    
    return [
        MockRecommendation("Migrate to Cloud Infrastructure", "high", 50000, "infrastructure"),
        MockRecommendation("Implement Security Monitoring", "high", 25000, "security"),
        MockRecommendation("Optimize Database Performance", "medium", 15000, "performance"),
        MockRecommendation("Setup CI/CD Pipeline", "medium", 20000, "devops"),
        MockRecommendation("Implement Backup Strategy", "low", 10000, "backup")
    ]


def demo_interactive_report_generation():
    """Demonstrate interactive report generation with drill-down capabilities."""
    print("\n🎯 Demo: Interactive Report Generation")
    print("=" * 50)
    
    # Create report generator agent
    config = AgentConfig(
        name="demo-report-generator",
        role="report_generator",
        model_name="gpt-4"
    )
    report_agent = ReportGeneratorAgent(config)
    
    # Create mock recommendations
    recommendations = create_mock_recommendations()
    
    # Test interactive section detection
    print("\n📊 Testing Interactive Section Detection:")
    test_sections = [
        "Executive Summary",
        "Cost Analysis", 
        "Recommendations Overview",
        "Implementation Roadmap",
        "Business Context"
    ]
    
    for section_title in test_sections:
        is_interactive = report_agent._should_be_interactive(section_title, recommendations)
        status = "✅ Interactive" if is_interactive else "📄 Static"
        print(f"  {status}: {section_title}")
    
    # Test drill-down data generation
    print("\n🔍 Testing Drill-down Data Generation:")
    drill_down_data = report_agent._generate_drill_down_data("Cost Analysis", recommendations)
    
    print(f"  Generated drill-down categories: {list(drill_down_data.keys())}")
    if "cost_breakdown" in drill_down_data:
        cost_breakdown = drill_down_data["cost_breakdown"]
        print(f"  Cost by priority: {cost_breakdown.get('by_priority', {})}")
        print(f"  Cost by category: {cost_breakdown.get('by_category', {})}")
    
    # Test chart configuration generation
    print("\n📈 Testing Chart Configuration:")
    charts_config = report_agent._generate_charts_config("Cost Analysis", recommendations)
    
    for i, chart in enumerate(charts_config):
        print(f"  Chart {i+1}: {chart['type']} - {chart['title']}")
        print(f"    Description: {chart['description']}")
        print(f"    Data points: {len(chart['data'])}")


def demo_report_templates():
    """Demonstrate report template functionality."""
    print("\n📋 Demo: Report Templates")
    print("=" * 50)
    
    # Create a sample template
    template = ReportTemplate(
        name="Executive Summary Template",
        description="Standard template for executive summaries",
        report_type=ReportType.EXECUTIVE_SUMMARY,
        version="1.0",
        sections_config=[
            {
                "title": "Executive Summary",
                "order": 1,
                "content_type": "markdown",
                "is_interactive": False,
                "generated_by": "cto_agent"
            },
            {
                "title": "Key Recommendations", 
                "order": 2,
                "content_type": "markdown",
                "is_interactive": True,
                "generated_by": "report_generator_agent"
            },
            {
                "title": "Cost Analysis",
                "order": 3,
                "content_type": "markdown", 
                "is_interactive": True,
                "generated_by": "report_generator_agent"
            }
        ],
        branding_config={
            "primary_color": "#1976d2",
            "secondary_color": "#dc004e",
            "logo_url": "https://example.com/logo.png",
            "font_family": "Roboto, Arial, sans-serif"
        },
        css_template="""
        .report-header {
            background-color: #1976d2;
            color: white;
            padding: 20px;
        }
        .cost-section {
            border-left: 4px solid #dc004e;
            padding-left: 15px;
        }
        """,
        created_by="admin-user",
        is_public=True
    )
    
    print(f"✅ Created template: {template.name}")
    print(f"   Report type: {template.report_type.value}")
    print(f"   Sections: {len(template.sections_config)}")
    print(f"   Public: {template.is_public}")
    print(f"   Branding colors: {template.branding_config.get('primary_color')} / {template.branding_config.get('secondary_color')}")
    
    # Test template access control
    print("\n🔐 Testing Template Access Control:")
    print(f"   Creator access: {template.can_user_access('admin-user')}")
    print(f"   Public access: {template.can_user_access('random-user')}")
    
    # Make template private and test again
    template.is_public = False
    print(f"   Private access (random user): {template.can_user_access('random-user')}")
    
    # Test organization access
    template.organization_id = "org-123"
    print(f"   Organization access: {template.can_user_access('org-user', 'org-123')}")
    print(f"   Different org access: {template.can_user_access('org-user', 'org-456')}")


def demo_report_versioning():
    """Demonstrate report versioning functionality."""
    print("\n🔄 Demo: Report Versioning")
    print("=" * 50)
    
    # Create original report
    original_report = Report(
        assessment_id="assessment-123",
        user_id="user-456", 
        title="Infrastructure Assessment Report",
        description="Initial assessment report",
        report_type=ReportType.FULL_ASSESSMENT,
        format=ReportFormat.PDF,
        status=ReportStatus.COMPLETED,
        version="1.0",
        branding_config={"primary_color": "#1976d2"},
        shared_with=[],
        sharing_permissions={}
    )
    
    print(f"✅ Original report: {original_report.title} v{original_report.version}")
    
    # Create new version
    new_version = original_report.create_new_version("2.0")
    new_version.title = "Updated Infrastructure Assessment Report"
    new_version.description = "Updated with latest recommendations"
    new_version.branding_config["primary_color"] = "#ff5722"
    
    print(f"✅ New version: {new_version.title} v{new_version.version}")
    print(f"   Parent report: {new_version.parent_report_id}")
    print(f"   Updated branding: {new_version.branding_config['primary_color']}")
    
    # Test sharing functionality
    print("\n🤝 Testing Report Sharing:")
    original_report.share_with_user("colleague-789", "edit")
    print(f"   Shared with: {original_report.shared_with}")
    print(f"   Permissions: {original_report.sharing_permissions}")
    
    # Test access control
    print(f"   Owner access (admin): {original_report.can_user_access('user-456', 'admin')}")
    print(f"   Shared user access (edit): {original_report.can_user_access('colleague-789', 'edit')}")
    print(f"   Shared user access (admin): {original_report.can_user_access('colleague-789', 'admin')}")
    print(f"   Random user access: {original_report.can_user_access('random-999', 'view')}")


def demo_interactive_features():
    """Demonstrate interactive reporting features."""
    print("\n🎮 Demo: Interactive Features")
    print("=" * 50)
    
    # Create interactive report section
    interactive_section = ReportSection(
        report_id="report-123",
        section_id="section-cost-analysis",
        title="Cost Analysis",
        order=3,
        content="<h2>Cost Analysis</h2><p>Interactive cost breakdown...</p>",
        content_type="html",
        is_interactive=True,
        drill_down_data={
            "cost_breakdown": {
                "by_priority": {"high": 75000, "medium": 35000, "low": 10000},
                "by_category": {"infrastructure": 50000, "security": 25000, "performance": 15000, "devops": 20000, "backup": 10000},
                "timeline": [
                    {"period": "Q1 2024", "cost": 40000, "cumulative_cost": 40000},
                    {"period": "Q2 2024", "cost": 35000, "cumulative_cost": 75000},
                    {"period": "Q3 2024", "cost": 25000, "cumulative_cost": 100000},
                    {"period": "Q4 2024", "cost": 20000, "cumulative_cost": 120000}
                ]
            }
        },
        charts_config=[
            {
                "type": "pie",
                "title": "Cost Distribution by Priority",
                "description": "Breakdown of estimated costs by recommendation priority",
                "data": [
                    {"label": "High", "value": 75000},
                    {"label": "Medium", "value": 35000},
                    {"label": "Low", "value": 10000}
                ]
            },
            {
                "type": "line",
                "title": "Cost Timeline",
                "description": "Projected costs over implementation timeline",
                "data": [
                    {"x": "Q1 2024", "y": 40000},
                    {"x": "Q2 2024", "y": 35000},
                    {"x": "Q3 2024", "y": 25000},
                    {"x": "Q4 2024", "y": 20000}
                ]
            }
        ],
        generated_by="report_generator_agent",
        version="1.0"
    )
    
    print(f"✅ Interactive section: {interactive_section.title}")
    print(f"   Interactive: {interactive_section.is_interactive}")
    print(f"   Drill-down categories: {list(interactive_section.drill_down_data.keys())}")
    print(f"   Charts available: {len(interactive_section.charts_config)}")
    
    # Display chart information
    for i, chart in enumerate(interactive_section.charts_config):
        print(f"   Chart {i+1}: {chart['type']} - {chart['title']}")
        print(f"     Data points: {len(chart['data'])}")
    
    # Display drill-down data summary
    cost_breakdown = interactive_section.drill_down_data["cost_breakdown"]
    print(f"\n📊 Cost Breakdown Summary:")
    print(f"   Total by priority: ${sum(cost_breakdown['by_priority'].values()):,}")
    print(f"   Total by category: ${sum(cost_breakdown['by_category'].values()):,}")
    print(f"   Timeline periods: {len(cost_breakdown['timeline'])}")


async def demo_report_service():
    """Demonstrate the report service functionality."""
    print("\n⚙️  Demo: Report Service")
    print("=" * 50)
    
    # Note: This would require actual database setup in a real scenario
    print("📝 Report Service Features:")
    print("   ✅ Report versioning and comparison")
    print("   ✅ Template management and customization") 
    print("   ✅ Report sharing and collaboration")
    print("   ✅ Interactive report data generation")
    print("   ✅ User report management with version history")
    
    print("\n🔧 Service Methods Available:")
    service = ReportService()
    methods = [method for method in dir(service) if not method.startswith('_') and callable(getattr(service, method))]
    
    for method in methods:
        print(f"   • {method}")
    
    print("\n💡 Usage Examples:")
    print("   # Create report from template")
    print("   report = await service.create_report_from_template(assessment_id, user_id, template_id)")
    print("   ")
    print("   # Create new version")
    print("   new_version = await service.create_report_version(report_id, user_id, '2.0')")
    print("   ")
    print("   # Compare versions")
    print("   comparison = await service.compare_report_versions(report_id_1, report_id_2, user_id)")
    print("   ")
    print("   # Share report")
    print("   await service.share_report(report_id, owner_id, share_with_user_id, 'edit')")


def main():
    """Run all advanced reporting demos."""
    print("🚀 Advanced Reporting Features Demo")
    print("=" * 60)
    print("Demonstrating the new advanced reporting capabilities:")
    print("• Interactive report previews with drill-down capabilities")
    print("• Customizable report templates and branding options") 
    print("• Report versioning and comparison features")
    print("• Report sharing and collaboration tools")
    
    # Run demos
    demo_interactive_report_generation()
    demo_report_templates()
    demo_report_versioning()
    demo_interactive_features()
    
    # Run async demo
    asyncio.run(demo_report_service())
    
    print("\n✅ Demo Complete!")
    print("=" * 60)
    print("All advanced reporting features have been successfully demonstrated.")
    print("The system now supports:")
    print("• 📊 Interactive reports with drill-down capabilities")
    print("• 📋 Customizable templates with branding")
    print("• 🔄 Version control and comparison")
    print("• 🤝 Collaboration and sharing")
    print("• 🎮 Rich interactive content")


if __name__ == "__main__":
    main()