#!/usr/bin/env python3
"""
Demo script for Compliance Agent.

This script demonstrates the Compliance Agent's capabilities for regulatory
compliance analysis, security assessment, and data residency recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.agents.compliance_agent import ComplianceAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole
from src.infra_mind.models.assessment import Assessment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_assessment() -> Assessment:
    """Create a sample assessment for testing."""
    return Assessment(
        user_id="demo_user",
        title="Healthcare AI Platform Compliance Assessment",
        description="Compliance assessment for a healthcare AI platform processing patient data",
        business_requirements={
            "company_size": "medium",
            "industry": "healthcare",
            "company_location": "united_states",
            "target_markets": ["us", "eu"],
            "data_types": ["personal_data", "health_data", "medical_records"],
            "budget_range": "$100k+",
            "primary_goals": ["compliance", "security", "scalability"],
            "timeline": "6_months"
        },
        technical_requirements={
            "workload_types": ["web_application", "ai_ml", "database"],
            "expected_users": 5000,
            "data_volume": "1TB+",
            "performance_requirements": {
                "availability": "99.9%",
                "response_time": "< 200ms"
            },
            "security_requirements": {
                "encryption_at_rest": False,  # Current state - needs improvement
                "encryption_in_transit": True,
                "multi_factor_auth": False,
                "role_based_access": True,
                "access_monitoring": False,
                "audit_logging": True,
                "backup_encryption": False,
                "data_retention_policy": False,
                "secure_deletion": False,
                "centralized_logging": True,
                "security_monitoring": False,
                "business_associate_agreements": False
            },
            "preferred_regions": ["us-east-1", "eu-west-1"]
        }
    )


async def demo_compliance_analysis():
    """Demonstrate compliance analysis capabilities."""
    print("\n" + "="*80)
    print("COMPLIANCE AGENT DEMO - REGULATORY ANALYSIS")
    print("="*80)
    
    # Create compliance agent
    config = AgentConfig(
        name="Demo Compliance Agent",
        role=AgentRole.COMPLIANCE,
        tools_enabled=["data_processor", "compliance_checker", "security_analyzer"]
    )
    
    agent = ComplianceAgent(config)
    assessment = create_sample_assessment()
    
    print(f"\n📋 Assessment: {assessment.title}")
    print(f"🏢 Industry: {assessment.business_requirements['industry']}")
    print(f"🌍 Target Markets: {', '.join(assessment.business_requirements['target_markets'])}")
    print(f"📊 Data Types: {', '.join(assessment.business_requirements['data_types'])}")
    
    try:
        # Execute compliance analysis
        print(f"\n🔍 Starting compliance analysis...")
        result = await agent.execute(assessment)
        
        if result.status.value == "completed":
            print(f"✅ Analysis completed successfully!")
            
            # Display applicable regulations
            applicable_regs = result.data["applicable_regulations"]
            print(f"\n📜 APPLICABLE REGULATIONS:")
            for reg in applicable_regs["applicable_regulations"]:
                details = applicable_regs["regulation_details"].get(reg, {})
                print(f"  • {reg}: {details.get('name', 'Unknown')}")
                print(f"    Jurisdiction: {details.get('jurisdiction', 'Unknown')}")
                print(f"    Penalties: {details.get('penalties', 'Unknown')}")
            
            # Display compliance assessment
            compliance_assessment = result.data["compliance_assessment"]
            print(f"\n📊 COMPLIANCE ASSESSMENT:")
            print(f"  Overall Score: {compliance_assessment['overall_compliance_score']}/1.0")
            print(f"  Maturity Level: {compliance_assessment['maturity_level']}")
            
            for reg, score in compliance_assessment["regulation_scores"].items():
                status = compliance_assessment["compliance_status"][reg]
                print(f"  • {reg}: {score:.2f} ({status})")
            
            # Display data residency analysis
            data_residency = result.data["data_residency_analysis"]
            print(f"\n🌐 DATA RESIDENCY ANALYSIS:")
            print(f"  Recommended Regions: {', '.join(data_residency['recommended_regions'])}")
            print(f"  Current Regions: {', '.join(data_residency['current_regions'])}")
            
            if data_residency["compliance_conflicts"]:
                print(f"  ⚠️  Conflicts:")
                for conflict in data_residency["compliance_conflicts"]:
                    print(f"    - {conflict}")
            
            # Display security assessment
            security_assessment = result.data["security_controls_assessment"]
            print(f"\n🔒 SECURITY CONTROLS ASSESSMENT:")
            print(f"  Overall Security Score: {security_assessment['overall_security_score']:.2f}/1.0")
            
            for category, details in security_assessment.items():
                if isinstance(details, dict) and "score" in details:
                    print(f"  • {category.replace('_', ' ').title()}: {details['score']:.2f}")
            
            # Display compliance gaps
            compliance_gaps = result.data["compliance_gaps"]
            print(f"\n⚠️  COMPLIANCE GAPS:")
            print(f"  Total Gaps: {compliance_gaps['total_gaps']}")
            print(f"  Overall Risk Level: {compliance_gaps['overall_risk_level']}")
            
            if compliance_gaps["high_risk_gaps"]:
                print(f"  High Risk Gaps:")
                for gap in compliance_gaps["high_risk_gaps"]:
                    if gap.get("regulation"):
                        print(f"    - {gap['regulation']}: Score {gap['current_score']:.2f}")
                    else:
                        print(f"    - {gap.get('category', 'Unknown')}: Score {gap['current_score']:.2f}")
            
            # Display top recommendations
            print(f"\n💡 TOP COMPLIANCE RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"  {i}. {rec['title']} (Priority: {rec['priority']})")
                print(f"     {rec['description']}")
                print(f"     Timeline: {rec['timeline']}")
                print(f"     Investment: {rec['investment_required']}")
                print()
            
            # Display compliance roadmap
            roadmap = result.data["compliance_roadmap"]
            print(f"\n🗺️  COMPLIANCE ROADMAP:")
            for phase, details in roadmap.items():
                if phase.startswith("phase_"):
                    print(f"  {phase.replace('_', ' ').title()}:")
                    print(f"    Timeline: {details['timeline']}")
                    print(f"    Focus: {details['focus']}")
                    print(f"    Items: {len(details['items'])} recommendations")
            
        else:
            print(f"❌ Analysis failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")


async def demo_compliance_tools():
    """Demonstrate compliance-specific tools."""
    print("\n" + "="*80)
    print("COMPLIANCE TOOLS DEMO")
    print("="*80)
    
    # Create compliance agent to access tools
    config = AgentConfig(
        name="Demo Compliance Agent",
        role=AgentRole.COMPLIANCE,
        tools_enabled=["compliance_checker", "security_analyzer"]
    )
    
    agent = ComplianceAgent(config)
    assessment = create_sample_assessment()
    await agent.initialize(assessment)
    
    # Demo compliance checker tool
    print(f"\n🔍 COMPLIANCE CHECKER TOOL DEMO:")
    
    security_req = assessment.technical_requirements["security_requirements"]
    
    # Check GDPR compliance
    gdpr_result = await agent._use_tool(
        "compliance_checker",
        regulation="GDPR",
        requirements=security_req,
        operation="check"
    )
    
    if gdpr_result.is_success:
        gdpr_data = gdpr_result.data
        print(f"  GDPR Compliance:")
        print(f"    Score: {gdpr_data['compliance_score']:.2f}")
        print(f"    Level: {gdpr_data['compliance_level']}")
        print(f"    Status: {gdpr_data['overall_status']}")
        print(f"    Findings: {len(gdpr_data['findings'])} items")
    
    # Check HIPAA compliance
    hipaa_result = await agent._use_tool(
        "compliance_checker",
        regulation="HIPAA",
        requirements=security_req,
        operation="check"
    )
    
    if hipaa_result.is_success:
        hipaa_data = hipaa_result.data
        print(f"  HIPAA Compliance:")
        print(f"    Score: {hipaa_data['compliance_score']:.2f}")
        print(f"    Level: {hipaa_data['compliance_level']}")
        print(f"    Status: {hipaa_data['overall_status']}")
    
    # Demo security analyzer tool
    print(f"\n🔒 SECURITY ANALYZER TOOL DEMO:")
    
    security_result = await agent._use_tool(
        "security_analyzer",
        security_config=security_req,
        analysis_type="comprehensive"
    )
    
    if security_result.is_success:
        security_data = security_result.data
        print(f"  Overall Security Score: {security_data['overall_score']:.2f}")
        print(f"  Categories Analyzed: {len(security_data['categories'])}")
        print(f"  Recommendations: {len(security_data['recommendations'])}")
        print(f"  Critical Issues: {len(security_data['critical_issues'])}")
        
        if security_data['critical_issues']:
            print(f"  Critical Issues:")
            for issue in security_data['critical_issues'][:3]:
                print(f"    - {issue}")


async def demo_regulation_specific_analysis():
    """Demonstrate regulation-specific analysis."""
    print("\n" + "="*80)
    print("REGULATION-SPECIFIC ANALYSIS DEMO")
    print("="*80)
    
    # Test different industry scenarios
    scenarios = [
        {
            "name": "Healthcare Provider",
            "industry": "healthcare",
            "data_types": ["health_data", "personal_data"],
            "target_markets": ["us"],
            "expected_regulations": ["HIPAA"]
        },
        {
            "name": "EU E-commerce",
            "industry": "retail",
            "data_types": ["personal_data", "payment_data"],
            "target_markets": ["eu", "uk"],
            "expected_regulations": ["GDPR"]
        },
        {
            "name": "California Tech Startup",
            "industry": "technology",
            "data_types": ["personal_data", "user_data"],
            "target_markets": ["california", "us"],
            "expected_regulations": ["CCPA"]
        }
    ]
    
    config = AgentConfig(
        name="Regulation Analysis Agent",
        role=AgentRole.COMPLIANCE
    )
    
    agent = ComplianceAgent(config)
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Industry: {scenario['industry']}")
        print(f"   Data Types: {', '.join(scenario['data_types'])}")
        print(f"   Markets: {', '.join(scenario['target_markets'])}")
        
        # Create assessment for scenario
        assessment = Assessment(
            user_id="demo_user",
            title=f"{scenario['name']} Assessment",
            business_requirements={
                "industry": scenario["industry"],
                "data_types": scenario["data_types"],
                "target_markets": scenario["target_markets"],
                "company_size": "medium"
            },
            technical_requirements={
                "security_requirements": {
                    "encryption_at_rest": True,
                    "encryption_in_transit": True,
                    "access_controls": True
                }
            }
        )
        
        await agent.initialize(assessment)
        
        # Analyze applicable regulations
        applicable_regs = await agent._identify_applicable_regulations()
        
        print(f"   Identified Regulations: {', '.join(applicable_regs['applicable_regulations'])}")
        
        # Check if expected regulations were identified
        for expected_reg in scenario["expected_regulations"]:
            if expected_reg in applicable_regs["applicable_regulations"]:
                print(f"   ✅ Correctly identified {expected_reg}")
            else:
                print(f"   ❌ Missed {expected_reg}")


async def main():
    """Run all compliance agent demos."""
    print("🚀 Starting Compliance Agent Demo Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run main compliance analysis demo
        await demo_compliance_analysis()
        
        # Run tools demo
        await demo_compliance_tools()
        
        # Run regulation-specific analysis
        await demo_regulation_specific_analysis()
        
        print(f"\n✅ All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo suite failed: {str(e)}")
        print(f"❌ Demo suite failed: {str(e)}")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())