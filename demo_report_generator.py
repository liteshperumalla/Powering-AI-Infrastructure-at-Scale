#!/usr/bin/env python3
"""
Demo script for the Report Generator Agent.

This script demonstrates the report generation functionality including:
- Creating reports from assessment data
- Different report types (executive, technical, full)
- Report formatting and export capabilities
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
        },
        {
            "id": "rec_4",
            "title": "Implement Infrastructure as Code",
            "description": "Adopt Infrastructure as Code (IaC) practices using tools like Terraform to improve consistency, repeatability, and version control of infrastructure changes.",
            "category": "automation",
            "priority": "medium",
            "estimated_cost": 35000,
            "implementation_time": "2-3 months",
            "benefits": [
                "Consistent and repeatable infrastructure deployments",
                "Version control and audit trail for infrastructure changes",
                "Faster environment provisioning and scaling",
                "Reduced human error in infrastructure management"
            ],
            "risks": [
                "Initial learning curve for team",
                "Potential for configuration drift if not properly managed",
                "Dependency on IaC tool availability"
            ]
        },
        {
            "id": "rec_5",
            "title": "Strengthen Security Posture",
            "description": "Implement comprehensive security measures including zero-trust architecture, advanced threat detection, and compliance automation.",
            "category": "security",
            "priority": "high",
            "estimated_cost": 85000,
            "implementation_time": "4-6 months",
            "benefits": [
                "Enhanced protection against cyber threats",
                "Improved compliance with regulatory requirements",
                "Better incident response and recovery capabilities",
                "Increased customer and stakeholder confidence"
            ],
            "risks": [
                "Potential impact on system performance",
                "User experience friction with additional security measures",
                "Ongoing maintenance and update requirements"
            ]
        }
    ]


async def demo_report_creation():
    """Demonstrate basic report creation."""
    print_separator("Report Creation Demo")
    
    # Create Report Generator Agent
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR,
        tools_enabled=["document_generator", "template_engine"]
    )
    
    agent = ReportGeneratorAgent(config)
    print(f"Created Report Generator Agent: {agent.name}")
    
    # Create sample data
    assessment = create_sample_assessment()
    recommendations = create_sample_recommendations()
    
    print(f"Sample assessment: {assessment['business_requirements']['company_name']}")
    print(f"Sample recommendations: {len(recommendations)} items")
    
    # Set context for the agent
    agent.context = {
        "assessment": assessment,
        "recommendations": recommendations,
        "report_type": "full"
    }
    
    # Create a mock assessment object
    mock_assessment = type('Assessment', (), {})()
    mock_assessment.id = assessment["id"]
    mock_assessment.title = assessment["title"]
    mock_assessment.business_requirements = assessment["business_requirements"]
    mock_assessment.technical_requirements = assessment["technical_requirements"]
    
    # Generate report
    print("\nGenerating full report...")
    result = await agent.execute(mock_assessment)
    
    if result.status.value == "completed":
        print(f"✅ Report generation successful!")
        print(f"Report ID: {result.data['report_id']}")
        print(f"Report type: {result.data['report_type']}")
        print(f"Report sections: {result.metadata['report_sections']}")
        print(f"Report length: {result.metadata['report_length']} characters")
        
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
        role=AgentRole.REPORT_GENERATOR
    )
    agent = ReportGeneratorAgent(config)
    
    # Sample data
    assessment = create_sample_assessment()
    recommendations = create_sample_recommendations()
    
    report_types = ["executive", "technical", "full"]
    
    for report_type in report_types:
        print(f"\n--- Generating {report_type.title()} Report ---")
        
        agent.context = {
            "assessment": assessment,
            "recommendations": recommendations,
            "report_type": report_type
        }
        
        # Create mock assessment
        mock_assessment = type('Assessment', (), {})()
        mock_assessment.id = assessment["id"]
        mock_assessment.title = assessment["title"]
        mock_assessment.business_requirements = assessment["business_requirements"]
        mock_assessment.technical_requirements = assessment["technical_requirements"]
        
        result = await agent.execute(mock_assessment)
        
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


async def demo_report_sections():
    """Demonstrate individual report sections."""
    print_separator("Report Sections Demo")
    
    # Create agent
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR
    )
    agent = ReportGeneratorAgent(config)
    
    # Sample data
    assessment = create_sample_assessment()
    recommendations = create_sample_recommendations()
    
    # Test individual section generation
    sections_to_test = [
        "Executive Summary",
        "Business Context",
        "Current State Analysis",
        "Key Recommendations",
        "Cost Analysis"
    ]
    
    for section_title in sections_to_test:
        print(f"\n--- Testing {section_title} Section ---")
        
        try:
            # Convert dict to mock objects for testing
            mock_assessment = type('Assessment', (), {})()
            mock_assessment.id = assessment["id"]
            mock_assessment.business_requirements = assessment["business_requirements"]
            mock_assessment.technical_requirements = assessment["technical_requirements"]
            
            mock_recommendations = []
            for rec_data in recommendations:
                mock_rec = type('Recommendation', (), {})()
                for key, value in rec_data.items():
                    setattr(mock_rec, key, value)
                mock_recommendations.append(mock_rec)
            
            # Generate section
            section = await agent._generate_section(section_title, 1, mock_assessment, mock_recommendations)
            
            print(f"✅ Section generated successfully")
            print(f"   Title: {section.title}")
            print(f"   Content length: {len(section.content)} characters")
            print(f"   Content preview: {section.content[:200]}...")
            
        except Exception as e:
            print(f"❌ Section generation failed: {str(e)}")


async def demo_report_export():
    """Demonstrate report export functionality."""
    print_separator("Report Export Demo")
    
    # Generate a sample report
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR
    )
    agent = ReportGeneratorAgent(config)
    
    assessment = create_sample_assessment()
    recommendations = create_sample_recommendations()
    
    agent.context = {
        "assessment": assessment,
        "recommendations": recommendations,
        "report_type": "executive"
    }
    
    # Create mock assessment
    mock_assessment = type('Assessment', (), {})()
    mock_assessment.id = assessment["id"]
    mock_assessment.title = assessment["title"]
    mock_assessment.business_requirements = assessment["business_requirements"]
    mock_assessment.technical_requirements = assessment["technical_requirements"]
    
    result = await agent.execute(mock_assessment)
    
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
        
    else:
        print(f"❌ Report generation failed: {result.error}")


async def demo_cost_analysis():
    """Demonstrate cost analysis in reports."""
    print_separator("Cost Analysis Demo")
    
    # Create recommendations with varying costs
    high_cost_recommendations = [
        {
            "id": "rec_1",
            "title": "Enterprise Cloud Migration",
            "category": "infrastructure",
            "priority": "high",
            "estimated_cost": 250000,
            "implementation_time": "6-12 months",
            "benefits": ["Scalability", "Cost optimization"],
            "risks": ["Migration complexity"]
        },
        {
            "id": "rec_2", 
            "title": "Security Enhancement Program",
            "category": "security",
            "priority": "high",
            "estimated_cost": 150000,
            "implementation_time": "3-6 months",
            "benefits": ["Enhanced security", "Compliance"],
            "risks": ["Implementation complexity"]
        },
        {
            "id": "rec_3",
            "title": "Monitoring and Observability",
            "category": "operations",
            "priority": "medium",
            "estimated_cost": 75000,
            "implementation_time": "2-3 months",
            "benefits": ["Better visibility", "Proactive monitoring"],
            "risks": ["Learning curve"]
        },
        {
            "id": "rec_4",
            "title": "Team Training and Certification",
            "category": "training",
            "priority": "low",
            "estimated_cost": 25000,
            "implementation_time": "1-2 months",
            "benefits": ["Improved skills", "Better productivity"],
            "risks": ["Time investment"]
        }
    ]
    
    # Create agent and generate report
    config = AgentConfig(
        name="Report Generator",
        role=AgentRole.REPORT_GENERATOR
    )
    agent = ReportGeneratorAgent(config)
    
    assessment = create_sample_assessment()
    
    agent.context = {
        "assessment": assessment,
        "recommendations": high_cost_recommendations,
        "report_type": "executive"
    }
    
    # Create mock assessment
    mock_assessment = type('Assessment', (), {})()
    mock_assessment.id = assessment["id"]
    mock_assessment.title = assessment["title"]
    mock_assessment.business_requirements = assessment["business_requirements"]
    mock_assessment.technical_requirements = assessment["technical_requirements"]
    
    result = await agent.execute(mock_assessment)
    
    if result.status.value == "completed":
        # Extract cost analysis section
        report_dict = result.data['report']
        cost_section = None
        
        for section in report_dict['sections']:
            if 'cost' in section['title'].lower() or 'investment' in section['title'].lower():
                cost_section = section
                break
        
        if cost_section:
            print("✅ Cost analysis section found")
            print(f"Section title: {cost_section['title']}")
            print(f"Content length: {len(cost_section['content'])} characters")
            print("\n--- Cost Analysis Content ---")
            print(cost_section['content'])
        else:
            print("❌ Cost analysis section not found")
            
        # Calculate totals
        total_cost = sum(rec['estimated_cost'] for rec in high_cost_recommendations)
        print(f"\n💰 Total estimated cost: ${total_cost:,.2f}")
        
    else:
        print(f"❌ Report generation failed: {result.error}")


async def main():
    """Run all report generator demos."""
    print("Starting Report Generator Agent Demo")
    
    try:
        # Run individual demos
        report_markdown = await demo_report_creation()
        await demo_different_report_types()
        await demo_report_sections()
        await demo_report_export()
        await demo_cost_analysis()
        
        print_separator("Demo Completed Successfully")
        
        if report_markdown:
            print(f"\nSample report preview (first 1000 characters):")
            print("-" * 60)
            print(report_markdown[:1000] + "...")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\nDemo failed with error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())