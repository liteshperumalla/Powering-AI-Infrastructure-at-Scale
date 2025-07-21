#!/usr/bin/env python3
"""
Demo script for CTO Agent functionality.

This script demonstrates the CTO Agent's strategic planning and business alignment capabilities.
"""

import asyncio
import logging
import json
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_cto_agent():
    """Demonstrate CTO Agent functionality."""
    print("=" * 60)
    print("DEMO: CTO Agent - Strategic Planning & Business Alignment")
    print("=" * 60)
    
    try:
        from src.infra_mind.agents.cto_agent import CTOAgent
        from src.infra_mind.agents.base import AgentConfig, AgentRole
        from src.infra_mind.models.assessment import Assessment
        
        print("\n1. Creating sample assessment...")
        
        # Create sample business requirements
        business_req = {
            "company_size": "startup",
            "industry": "fintech",
            "budget_range": "$50k-100k",
            "primary_goals": ["scalability", "cost_reduction", "compliance"],
            "timeline": "6 months",
            "success_metrics": ["reduce_costs_by_30%", "handle_10x_traffic", "achieve_compliance"]
        }
        
        # Create sample technical requirements
        technical_req = {
            "workload_types": ["web_application", "ai_ml", "data_processing"],
            "expected_users": 25000,
            "performance_requirements": {
                "response_time": "< 100ms",
                "availability": "99.9%",
                "throughput": "1000 rps"
            },
            "integration_needs": ["database", "api", "payment_gateway", "analytics"],
            "data_requirements": {
                "storage_size": "10TB",
                "backup_frequency": "daily",
                "retention_period": "7 years"
            }
        }
        
        # Add compliance requirements to business requirements
        business_req["compliance_requirements"] = {
            "regulations": ["PCI_DSS", "SOX"],
            "data_residency": "US",
            "encryption_requirements": ["data_at_rest", "data_in_transit"],
            "audit_requirements": ["quarterly_audits", "continuous_monitoring"]
        }
        
        # Create mock assessment for demo (avoiding database dependencies)
        from unittest.mock import Mock
        assessment = Mock()
        assessment.id = "demo_assessment_id"
        assessment.user_id = "demo_user"
        assessment.title = "Fintech Infrastructure Assessment"
        assessment.business_requirements = business_req
        assessment.technical_requirements = technical_req
        
        # Mock the dict() method
        assessment.dict.return_value = {
            "id": assessment.id,
            "user_id": assessment.user_id,
            "title": assessment.title,
            "business_requirements": business_req,
            "technical_requirements": technical_req
        }
        
        print(f"   ✅ Created assessment for {business_req['company_size']} {business_req['industry']} company")
        print(f"   📊 Budget: {business_req['budget_range']}")
        print(f"   👥 Expected users: {technical_req['expected_users']:,}")
        print(f"   🎯 Goals: {', '.join(business_req['primary_goals'])}")
        print(f"   📋 Compliance: {', '.join(business_req['compliance_requirements']['regulations'])}")
        
        print("\n2. Initializing CTO Agent...")
        
        # Create CTO Agent with custom configuration
        config = AgentConfig(
            name="Strategic CTO Agent",
            role=AgentRole.CTO,
            tools_enabled=["data_processor", "calculator", "cloud_api"],
            temperature=0.1,
            max_tokens=2000,
            metrics_enabled=False,  # Disable for demo
            memory_enabled=False    # Disable for demo
        )
        
        cto_agent = CTOAgent(config)
        print(f"   ✅ Initialized {cto_agent.name}")
        print(f"   🔧 Tools enabled: {', '.join(cto_agent.config.tools_enabled)}")
        print(f"   📈 Strategic frameworks: {len(cto_agent.strategic_frameworks)}")
        
        print("\n3. Executing strategic analysis...")
        
        # Execute CTO Agent
        result = await cto_agent.execute(assessment)
        
        if result.status.value == "completed":
            print(f"   ✅ Analysis completed successfully in {result.execution_time:.2f}s")
            print(f"   📋 Generated {len(result.recommendations)} strategic recommendations")
            
            # Display results
            await display_cto_results(result)
            
        else:
            print(f"   ❌ Analysis failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")


async def display_cto_results(result):
    """Display CTO Agent results in a formatted way."""
    print("\n" + "=" * 60)
    print("CTO AGENT ANALYSIS RESULTS")
    print("=" * 60)
    
    # Executive Summary
    if "executive_summary" in result.data:
        executive_summary = result.data["executive_summary"]
        
        print("\n📊 EXECUTIVE SUMMARY")
        print("-" * 30)
        
        if "key_findings" in executive_summary:
            print("Key Findings:")
            for finding in executive_summary["key_findings"]:
                print(f"  • {finding}")
        
        if "strategic_priorities" in executive_summary:
            print(f"\nTop Strategic Priorities:")
            for i, priority in enumerate(executive_summary["strategic_priorities"], 1):
                print(f"  {i}. {priority}")
        
        if "investment_summary" in executive_summary:
            inv_summary = executive_summary["investment_summary"]
            print(f"\nInvestment Summary:")
            print(f"  • Total recommendations: {inv_summary.get('total_recommendations', 0)}")
            print(f"  • High priority actions: {inv_summary.get('high_priority_count', 0)}")
            print(f"  • Estimated investment: {inv_summary.get('estimated_investment', 'TBD')}")
            print(f"  • Expected timeline: {inv_summary.get('expected_timeline', 'TBD')}")
    
    # Strategic Recommendations
    print(f"\n🎯 STRATEGIC RECOMMENDATIONS ({len(result.recommendations)})")
    print("-" * 40)
    
    for i, rec in enumerate(result.recommendations, 1):
        priority_emoji = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
        print(f"\n{i}. {priority_emoji} {rec['title']} ({rec['priority'].upper()} PRIORITY)")
        print(f"   Category: {rec['category']}")
        print(f"   Description: {rec['description']}")
        print(f"   Business Impact: {rec['business_impact']}")
        print(f"   Timeline: {rec['timeline']}")
        
        if "actions" in rec and rec["actions"]:
            print(f"   Key Actions:")
            for action in rec["actions"][:3]:  # Show top 3 actions
                print(f"     • {action}")
    
    # Financial Analysis
    if "financial_analysis" in result.data:
        financial = result.data["financial_analysis"]
        
        print(f"\n💰 FINANCIAL ANALYSIS")
        print("-" * 25)
        
        if "budget_analysis" in financial:
            budget = financial["budget_analysis"]
            print(f"Budget Analysis:")
            print(f"  • Requested range: {budget.get('requested_range', 'N/A')}")
            print(f"  • Recommended budget: ${budget.get('recommended_budget', 0):,.0f}")
        
        if "roi_analysis" in financial:
            roi = financial["roi_analysis"]
            print(f"ROI Analysis:")
            print(f"  • Expected ROI: {roi.get('roi_percentage', 0):.1f}%")
            print(f"  • Payback period: {roi.get('payback_period_years', 0):.1f} years")
            print(f"  • Total savings: ${roi.get('total_savings', 0):,.0f}")
        
        if "financial_metrics" in financial:
            metrics = financial["financial_metrics"]
            print(f"Financial Metrics:")
            print(f"  • Cost per user: ${metrics.get('cost_per_user', 0):.2f}")
            print(f"  • Budget efficiency: {metrics.get('budget_efficiency', 'N/A')}")
    
    # Risk Assessment
    if "risk_assessment" in result.data:
        risks = result.data["risk_assessment"]
        
        print(f"\n⚠️  RISK ASSESSMENT")
        print("-" * 20)
        
        print(f"Overall Risk Level: {risks.get('overall_risk_level', 'Unknown')}")
        
        if "identified_risks" in risks:
            identified_risks = risks["identified_risks"]
            high_risks = [r for r in identified_risks if r.get("impact") == "high"]
            
            if high_risks:
                print(f"\nHigh-Impact Risks ({len(high_risks)}):")
                for risk in high_risks[:3]:  # Show top 3 high-impact risks
                    print(f"  • {risk['risk']}")
                    print(f"    Impact: {risk['impact']}, Probability: {risk['probability']}")
                    print(f"    Mitigation: {risk['mitigation']}")
        
        if "mitigation_priorities" in risks:
            priorities = risks["mitigation_priorities"]
            if priorities:
                print(f"\nTop Risk Mitigation Priorities:")
                for priority in priorities[:3]:
                    print(f"  • {priority}")
    
    # Strategic Alignment
    if "strategic_alignment" in result.data:
        alignment = result.data["strategic_alignment"]
        
        print(f"\n🎯 STRATEGIC ALIGNMENT")
        print("-" * 25)
        
        score = alignment.get("alignment_score", 0)
        level = alignment.get("alignment_level", "Unknown")
        print(f"Alignment Score: {score:.1f}/1.0 ({level})")
        
        if "alignment_factors" in alignment:
            factors = alignment["alignment_factors"]
            if factors:
                print(f"Alignment Factors:")
                for factor in factors[:3]:
                    print(f"  • {factor}")
    
    print(f"\n📈 ANALYSIS METADATA")
    print("-" * 22)
    print(f"Analysis timestamp: {result.data.get('analysis_timestamp', 'N/A')}")
    print(f"Frameworks used: {len(result.data.get('frameworks_used', []))}")
    print(f"Execution time: {result.execution_time:.2f} seconds")
    
    if result.metrics:
        print(f"Agent metrics available: Yes")
    else:
        print(f"Agent metrics available: No")


async def demo_agent_capabilities():
    """Demonstrate CTO Agent capabilities and configuration."""
    print("\n" + "=" * 60)
    print("CTO AGENT CAPABILITIES DEMO")
    print("=" * 60)
    
    try:
        from src.infra_mind.agents.cto_agent import CTOAgent
        from src.infra_mind.agents.base import AgentRole
        from src.infra_mind.agents import agent_registry, AgentFactory
        
        print("\n1. Agent Registry Integration...")
        
        # Test agent registry
        factory = AgentFactory(agent_registry)
        cto_agent = await factory.create_agent(AgentRole.CTO)
        
        if cto_agent:
            print(f"   ✅ CTO Agent created through factory")
            print(f"   🆔 Agent ID: {cto_agent.agent_id}")
            print(f"   📝 Agent Name: {cto_agent.name}")
        
        print("\n2. Agent Capabilities...")
        capabilities = cto_agent.get_capabilities()
        for capability in capabilities:
            print(f"   • {capability}")
        
        print("\n3. Health Check...")
        health = await cto_agent.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Role: {health['role']}")
        print(f"   Version: {health['version']}")
        print(f"   Tools: {health['tools_count']}")
        
        print("\n4. Strategic Frameworks...")
        print("   Available frameworks:")
        for framework in cto_agent.strategic_frameworks:
            print(f"     • {framework}")
        
        print("\n5. Business Priorities...")
        print("   Focus areas:")
        for priority in cto_agent.business_priorities:
            print(f"     • {priority}")
        
    except Exception as e:
        logger.error(f"Capabilities demo error: {e}")
        print(f"❌ Capabilities demo failed: {e}")


async def main():
    """Run all CTO Agent demos."""
    print("🚀 Starting CTO Agent Demo")
    print("This demo shows the CTO Agent's strategic planning capabilities")
    print("for task 6.1: Implement CTO Agent (MVP Priority)")
    
    await demo_cto_agent()
    await demo_agent_capabilities()
    
    print("\n" + "=" * 60)
    print("✅ CTO Agent Demo completed!")
    print("=" * 60)
    print("\nKey features demonstrated:")
    print("• Strategic business alignment analysis")
    print("• ROI calculations and financial projections")
    print("• Business risk assessment and mitigation")
    print("• Executive-level recommendations")
    print("• Integration with agent registry and factory")
    print("• Comprehensive strategic frameworks")


if __name__ == "__main__":
    asyncio.run(main())