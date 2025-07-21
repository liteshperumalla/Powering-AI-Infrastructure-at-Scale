#!/usr/bin/env python3
"""
Simple demo script for the Report Generator Agent.

This script demonstrates the report generation functionality without database dependencies.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.infra_mind.agents.report_generator_agent import ReportGeneratorAgent, Report, ReportSection
from src.infra_mind.agents.base import AgentConfig, AgentRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(title: str) -> None:
    """Print a section separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def create_sample_assessment() -> dict:
    """Create sample assessment data for testing."""
    return {
        "id": "assessment_123",
        "title": "TechCorp Infrastructure Assessment",
        "business_requirements": {
            "company_name": "TechCorp Solutions",
            "industry": "technology",
            "company_size": "medium",
            "contact_email": "cto@techcorp.com",
            "primary_goals": ["cost_reduction", "scalability", "performance"],
            "budget_range": "100k_500k",
            "timeline": "medium_term",
            "success_metrics": ["cost_savings", "performance_improvement", "roi"],
            "infrastructure_maturity": "intermediate",
            "main_challenges": ["high_costs", "scalability_issues", "lack_expertise"],
            "additional_context": "Growing company needing to modernize infrastructure"
        },
        "technical_requirements": {
            "current_hosting": ["aws", "on_premises"],
            "current_technologies": ["containers", "databases", "load_balancers"],
            "team_expertise": "intermediate",
            "workload_types": ["web_applications", "apis", "databases", "machine_learning"],
            "expected_users": 10000,
            "data_volume": "1tb_10tb",
            "performance_requirements": ["high_availability", "auto_scaling", "monitoring_alerting"],
            "preferred_cloud_providers": ["aws", "azure"],
            "geographic_requirements": ["north_america", "europe"],
            "compliance_requirements": ["gdpr", "iso_27001"],
            "security_requirements": ["encryption_at_rest", "encryption_in_transit", "network_isolation", "access_control"]
        }
    }


def create_sample_recommendations() -> list:
    """Create sample recommendations for testing."""
    return [
        {
            "id": "rec_1",
            "title": "Migrate to Container Orchestration",
            "description": "Implement Kubernetes-based container orchestration to improve scalability and resource utilization. This will enable better application deployment, scaling, and management.",
            "category": "infrastructure",
            "priority": "high",
            "estimated_cost": 75000,
            "implementation_time": "3-4 months",
            "benefits": [
                "Improved scalability and resource efficiency",
                "Faster deployment and rollback capabilities",
                "Better application isolation and security",
                "Reduced operational overhead"
            ],
            "risks": [
                "Learning curve for development team",
                "Initial complexity in setup and configuration",
                "Potential downtime during migration"
            ]
        },
        {
            "id": "rec_2",
            "title": "Implement Multi-Cloud Strategy",
            "description": "Adopt a multi-cloud approach using AWS and Azure to improve reliability, reduce vendor lock-in, and optimize costs through competitive pricing.",
            "category": "cloud_strategy",
            "priority": "high",
            "estimated_cost": 120000,
            "implementation_time": "6-8 months",
            "benefits": [
                "Reduced vendor lock-in and increased negotiating power",
                "Improved disaster recovery and business continuity",
                "Access to best-of-breed services from multiple providers",
                "Geographic distribution and compliance flexibility"
            ],
            "risks": [
                "Increased complexity in management and operations",
                "Higher skill requirements for team",
                "Potential for increased costs if not managed properly"
            ]
        },
        {
            "id": "rec_3",
            "title": "Enhance Monitoring and Observability",
            "description": "Implement comprehensive monitoring, logging, and observability solutions to improve system reliability and troubleshooting capabilities.",
            "category": "operations",
            "priority": "medium",
            "estimated_cost": 45000,
            "implementation_time": "2-3 months",
            "benefits": [
                "Proactive issue detection and resolution",
                "Improved system reliability and uptime",
                "Better performance optimization insights",
                "Enhanced security monitoring capabilities"
            ],
            "risks": [
                "Information overload if not properly configured",
                "Additional operational overhead",
                "Privacy concerns with extensive logging"
            ]
        }
    ]


async def demo_direct_report_generation():
    """Demonstrate direct report generation without full agent execution."""
    print_separator("Direct Report Generation Demo")
    
    # Create Report Generator Agent
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR,
        tools_enabled=[],
        metrics_enabled=False  # Disable metrics to avoid database dependency
    )
    
    agent = ReportGeneratorAgent(config)
    print(f"Created Report Generator Agent: {agent.name}")
    
    # Create sample data
    assessment_data = create_sample_assessment()
    recommendations_data = create_sample_recommendations()
    
    # Set context directly
    agent.context = {
        "assessment": assessment_data,
        "recommendations": recommendations_data,
        "report_type": "full"
    }
    
    print(f"Sample assessment: {assessment_data['business_requirements']['company_name']}")
    print(f"Sample recommendations: {len(recommendations_data)} items")
    
    # Call the main logic directly
    print("\nGenerating full report...")
    result = await agent._execute_main_logic()
    
    if result.status.value == "completed":
        print(f"✅ Report generation successful!")
        print(f"Report ID: {result.data['report_id']}")
        print(f"Report type: {result.data['report_type']}")
        print(f"Report sections: {result.data['metadata']['report_sections']}")
        print(f"Report length: {result.data['metadata']['report_length']} characters")
        
        # Show report structure
        report_dict = result.data['report']
        print(f"\nReport Structure:")
        for i, section in enumerate(report_dict['sections'], 1):
            print(f"  {i}. {section['title']}")
        
        return result.data['report_markdown']
    else:
        print(f"❌ Report generation failed: {result.error}")
        return None


async def demo_different_report_types():
    """Demonstrate different report types."""
    print_separator("Different Report Types Demo")
    
    # Create agent
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR,
        metrics_enabled=False
    )
    agent = ReportGeneratorAgent(config)
    
    # Sample data
    assessment_data = create_sample_assessment()
    recommendations_data = create_sample_recommendations()
    
    report_types = ["executive", "technical", "full"]
    
    for report_type in report_types:
        print(f"\n--- Generating {report_type.title()} Report ---")
        
        agent.context = {
            "assessment": assessment_data,
            "recommendations": recommendations_data,
            "report_type": report_type
        }
        
        result = await agent._execute_main_logic()
        
        if result.status.value == "completed":
            report_dict = result.data['report']
            print(f"✅ {report_type.title()} report generated")
            print(f"   Sections: {len(report_dict['sections'])}")
            print(f"   Length: {len(result.data['report_markdown'])} characters")
            
            # Show section titles
            print("   Section titles:")
            for section in report_dict['sections']:
                print(f"     - {section['title']}")
        else:
            print(f"❌ {report_type.title()} report failed: {result.error}")


async def demo_report_export():
    """Demonstrate report export functionality."""
    print_separator("Report Export Demo")
    
    # Generate a sample report
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR,
        metrics_enabled=False
    )
    agent = ReportGeneratorAgent(config)
    
    assessment_data = create_sample_assessment()
    recommendations_data = create_sample_recommendations()
    
    agent.context = {
        "assessment": assessment_data,
        "recommendations": recommendations_data,
        "report_type": "executive"
    }
    
    result = await agent._execute_main_logic()
    
    if result.status.value == "completed":
        report_markdown = result.data['report_markdown']
        report_dict = result.data['report']
        
        print("✅ Report generated for export demo")
        
        # Save markdown version
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        
        markdown_file = output_dir / f"report_{result.data['report_id']}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(report_markdown)
        
        print(f"📄 Markdown report saved: {markdown_file}")
        print(f"   File size: {markdown_file.stat().st_size} bytes")
        
        # Save JSON version
        json_file = output_dir / f"report_{result.data['report_id']}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"📄 JSON report saved: {json_file}")
        print(f"   File size: {json_file.stat().st_size} bytes")
        
        # Show markdown preview
        print(f"\n--- Markdown Preview (first 500 characters) ---")
        print(report_markdown[:500] + "...")
        
        return report_markdown
        
    else:
        print(f"❌ Report generation failed: {result.error}")
        return None


async def demo_report_content():
    """Demonstrate report content quality."""
    print_separator("Report Content Quality Demo")
    
    # Generate a full report
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR,
        metrics_enabled=False
    )
    agent = ReportGeneratorAgent(config)
    
    assessment_data = create_sample_assessment()
    recommendations_data = create_sample_recommendations()
    
    agent.context = {
        "assessment": assessment_data,
        "recommendations": recommendations_data,
        "report_type": "full"
    }
    
    result = await agent._execute_main_logic()
    
    if result.status.value == "completed":
        report_dict = result.data['report']
        
        print("✅ Full report generated for content analysis")
        print(f"Report title: {report_dict['title']}")
        print(f"Total sections: {len(report_dict['sections'])}")
        
        # Analyze each section
        for section in report_dict['sections']:
            print(f"\n--- {section['title']} ---")
            print(f"Content length: {len(section['content'])} characters")
            
            # Show first few lines
            lines = section['content'].split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"Preview: {line[:100]}...")
                    break
        
        # Calculate total report statistics
        total_chars = sum(len(section['content']) for section in report_dict['sections'])
        avg_section_length = total_chars / len(report_dict['sections'])
        
        print(f"\n📊 Report Statistics:")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Average section length: {avg_section_length:.0f} characters")
        print(f"   Estimated reading time: {total_chars / 1000:.1f} minutes")
        
    else:
        print(f"❌ Report generation failed: {result.error}")


async def main():
    """Run all report generator demos."""
    print("Starting Simple Report Generator Demo")
    
    try:
        # Run individual demos
        report_markdown = await demo_direct_report_generation()
        await demo_different_report_types()
        exported_report = await demo_report_export()
        await demo_report_content()
        
        print_separator("Demo Completed Successfully")
        
        if exported_report:
            print(f"\nFull report sample (first 1000 characters):")
            print("-" * 60)
            print(exported_report[:1000] + "...")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\nDemo failed with error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())