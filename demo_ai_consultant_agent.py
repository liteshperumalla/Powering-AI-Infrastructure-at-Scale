#!/usr/bin/env python3
"""
Demo script for AI Consultant Agent.

This script demonstrates the AI Consultant Agent's capabilities for:
- Business process analysis and AI opportunity identification
- Industry-specific AI use case recommendations
- Change management strategies for AI adoption
- AI ethics and responsible AI implementation guidance
- Custom AI solution architecture recommendations
- Training and upskilling program suggestions
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.agents.ai_consultant_agent import AIConsultantAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole
from src.infra_mind.models.assessment import Assessment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_assessment():
    """Create a sample assessment for testing."""
    # Create a mock assessment object that mimics the Assessment model structure
    class MockAssessment:
        def __init__(self):
            self.id = "demo_assessment_id_123"
            self.user_id = "demo_user_123"
            self.title = "Healthcare AI Transformation Assessment"
            self.description = "Demo assessment for healthcare AI infrastructure transformation"
            self.business_requirements = {
                "company_size": "medium",
                "industry": "healthcare",
                "budget_range": "$50k-100k",
                "primary_goals": ["efficiency", "innovation", "compliance"],
                "timeline": "6-12 months",
                "current_challenges": [
                    "Manual data processing",
                    "Inconsistent patient communication",
                    "Regulatory compliance burden"
                ],
                "compliance_requirements": {
                    "regulations": ["HIPAA", "GDPR"],
                    "data_residency": "US",
                    "audit_requirements": True
                }
            }
            self.technical_requirements = {
                "workload_types": ["web_application", "database", "api"],
                "expected_users": 5000,
                "performance_requirements": {
                    "response_time": "< 2 seconds",
                    "availability": "99.9%",
                    "scalability": "auto-scaling"
                },
                "integration_requirements": [
                    "EHR systems",
                    "Payment processing",
                    "Compliance reporting"
                ]
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


async def demo_business_process_analysis():
    """Demonstrate business process analysis capabilities."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - BUSINESS PROCESS ANALYSIS DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    
    # Create sample assessment
    assessment = create_sample_assessment()
    
    print(f"\nAssessment Context:")
    print(f"- Company: {assessment.business_requirements['company_size']} {assessment.business_requirements['industry']} company")
    print(f"- Budget: {assessment.business_requirements['budget_range']}")
    print(f"- Goals: {', '.join(assessment.business_requirements['primary_goals'])}")
    print(f"- Users: {assessment.technical_requirements['expected_users']:,}")
    print(f"- Compliance: {', '.join(assessment.business_requirements['compliance_requirements']['regulations'])}")
    
    # Execute agent analysis
    print(f"\n🤖 Executing AI Consultant Agent analysis...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        print(f"✅ Analysis completed successfully in {result.execution_time:.2f} seconds")
        
        # Display business process analysis
        business_analysis = result.data.get("business_process_analysis", {})
        print(f"\n📊 Business Process Analysis:")
        
        industry_context = business_analysis.get("industry_context", {})
        print(f"  Industry Context: {industry_context.get('industry')} - {industry_context.get('company_size')}")
        
        key_processes = business_analysis.get("key_processes", [])
        print(f"  Key Business Processes:")
        for process in key_processes:
            print(f"    • {process.get('name')} (Automation Potential: {process.get('automation_potential')})")
        
        automation_potential = business_analysis.get("automation_potential", {})
        print(f"  Overall Automation Readiness: {automation_potential.get('automation_readiness', 'unknown')}")
        print(f"  Automation Score: {automation_potential.get('overall_score', 0):.2f}")
        
    else:
        print(f"❌ Analysis failed: {result.error}")


async def demo_ai_opportunities_identification():
    """Demonstrate AI opportunities identification."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - AI OPPORTUNITIES IDENTIFICATION DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    # Execute agent analysis
    print(f"\n🔍 Identifying AI opportunities...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        ai_opportunities = result.data.get("ai_opportunities", {})
        
        print(f"\n🎯 AI Opportunities Analysis:")
        print(f"  Industry: {ai_opportunities.get('industry_context')}")
        
        budget_constraints = ai_opportunities.get("budget_constraints", {})
        print(f"  Budget Range: ${budget_constraints.get('min', 0):,} - ${budget_constraints.get('max', 0):,}")
        
        relevant_use_cases = ai_opportunities.get("relevant_use_cases", [])
        print(f"  Relevant Use Cases: {', '.join(relevant_use_cases)}")
        
        feasible_use_cases = ai_opportunities.get("feasible_use_cases", [])
        print(f"  Budget-Feasible Use Cases: {', '.join(feasible_use_cases)}")
        
        prioritized_opportunities = ai_opportunities.get("prioritized_opportunities", [])
        print(f"\n📈 Top AI Opportunities:")
        for i, opp in enumerate(prioritized_opportunities[:3], 1):
            print(f"    {i}. {opp.get('use_case', 'Unknown')}")
            print(f"       Priority Score: {opp.get('priority_score', 0):.2f}")
            print(f"       Business Value: {opp.get('business_value', 'N/A')}")
            print(f"       Timeline: {opp.get('implementation_time', 'N/A')}")
            print(f"       Cost: {opp.get('estimated_cost', 'N/A')}")
        
        quick_wins = ai_opportunities.get("quick_wins", [])
        if quick_wins:
            print(f"\n⚡ Quick Wins:")
            for win in quick_wins:
                print(f"    • {win.get('use_case', 'Unknown')}")
        
        strategic_initiatives = ai_opportunities.get("strategic_initiatives", [])
        if strategic_initiatives:
            print(f"\n🎯 Strategic Initiatives:")
            for initiative in strategic_initiatives:
                print(f"    • {initiative.get('use_case', 'Unknown')}")


async def demo_ai_readiness_assessment():
    """Demonstrate AI readiness assessment."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - AI READINESS ASSESSMENT DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    # Execute agent analysis
    print(f"\n📋 Assessing AI readiness...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        readiness_assessment = result.data.get("readiness_assessment", {})
        
        print(f"\n🎯 AI Readiness Assessment:")
        overall_score = readiness_assessment.get("overall_readiness_score", 0)
        readiness_level = readiness_assessment.get("readiness_level", "Unknown")
        print(f"  Overall Readiness Score: {overall_score:.2f}")
        print(f"  Readiness Level: {readiness_level}")
        
        readiness_dimensions = readiness_assessment.get("readiness_dimensions", {})
        print(f"\n📊 Readiness Dimensions:")
        for dimension, details in readiness_dimensions.items():
            score = details.get("score", 0)
            level = details.get("level", "unknown")
            print(f"    • {dimension.replace('_', ' ').title()}: {score:.2f} ({level})")
        
        readiness_gaps = readiness_assessment.get("readiness_gaps", [])
        if readiness_gaps:
            print(f"\n⚠️  Readiness Gaps:")
            for gap in readiness_gaps:
                print(f"    • {gap}")
        
        improvement_priorities = readiness_assessment.get("improvement_priorities", [])
        if improvement_priorities:
            print(f"\n🔧 Improvement Priorities:")
            for priority in improvement_priorities:
                dimension = priority.get("dimension", "unknown")
                current_score = priority.get("current_score", 0)
                priority_level = priority.get("priority", "medium")
                print(f"    • {dimension.replace('_', ' ').title()}: {current_score:.2f} (Priority: {priority_level})")


async def demo_use_case_recommendations():
    """Demonstrate AI use case recommendations."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - USE CASE RECOMMENDATIONS DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    # Execute agent analysis
    print(f"\n💡 Generating AI use case recommendations...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        recommendations = result.recommendations
        
        print(f"\n🎯 AI Use Case Recommendations ({len(recommendations)} total):")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.get('title', 'Unknown Recommendation')}")
            print(f"   Category: {rec.get('category', 'N/A')}")
            print(f"   Priority: {rec.get('priority', 'medium')}")
            print(f"   Description: {rec.get('description', 'N/A')}")
            print(f"   Business Value: {rec.get('business_value', 'N/A')}")
            print(f"   Implementation Complexity: {rec.get('implementation_complexity', 'N/A')}")
            print(f"   ROI Potential: {rec.get('roi_potential', 'N/A')}")
            print(f"   Timeline: {rec.get('estimated_timeline', 'N/A')}")
            print(f"   Cost: {rec.get('estimated_cost', 'N/A')}")
            
            technologies = rec.get('technologies_required', [])
            if technologies:
                print(f"   Technologies: {', '.join(technologies)}")
            
            success_metrics = rec.get('success_metrics', [])
            if success_metrics:
                print(f"   Success Metrics:")
                for metric in success_metrics[:2]:  # Show first 2 metrics
                    print(f"     • {metric}")
            
            next_steps = rec.get('next_steps', [])
            if next_steps:
                print(f"   Next Steps:")
                for step in next_steps[:2]:  # Show first 2 steps
                    print(f"     • {step}")


async def demo_transformation_strategy():
    """Demonstrate AI transformation strategy."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - TRANSFORMATION STRATEGY DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    # Execute agent analysis
    print(f"\n🚀 Creating AI transformation strategy...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        transformation_strategy = result.data.get("transformation_strategy", {})
        
        print(f"\n🎯 AI Transformation Strategy:")
        strategy_approach = transformation_strategy.get("strategy_approach", "unknown")
        print(f"  Strategy Approach: {strategy_approach}")
        
        phases = transformation_strategy.get("transformation_phases", [])
        print(f"  Transformation Phases: {' → '.join(phases)}")
        
        success_criteria = transformation_strategy.get("success_criteria", [])
        if success_criteria:
            print(f"\n✅ Success Criteria:")
            for criterion in success_criteria[:3]:  # Show first 3 criteria
                print(f"    • {criterion}")
        
        investment_analysis = transformation_strategy.get("investment_analysis", {})
        if investment_analysis:
            print(f"\n💰 Investment Analysis:")
            total_investment = investment_analysis.get("total_investment", 0)
            expected_roi = investment_analysis.get("expected_roi", "N/A")
            payback_period = investment_analysis.get("payback_period", "N/A")
            print(f"    Total Investment: ${total_investment:,.0f}")
            print(f"    Expected ROI: ${expected_roi}")
            print(f"    Payback Period: {payback_period}")
        
        change_management = transformation_strategy.get("change_management_strategy", {})
        if change_management:
            print(f"\n🔄 Change Management Strategy:")
            communication_plan = change_management.get("communication_plan", [])
            if communication_plan:
                print(f"    Communication Plan:")
                for item in communication_plan[:2]:  # Show first 2 items
                    print(f"      • {item}")


async def demo_ethics_and_governance():
    """Demonstrate AI ethics and governance framework."""
    print("\n" + "="*60)
    print("AI CONSULTANT AGENT - ETHICS & GOVERNANCE DEMO")
    print("="*60)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    # Execute agent analysis
    print(f"\n⚖️  Developing AI ethics and governance framework...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        ethics_governance = result.data.get("ethics_governance", {})
        
        print(f"\n🎯 AI Ethics & Governance Framework:")
        
        core_principles = ethics_governance.get("core_principles", [])
        if core_principles:
            print(f"  Core Principles:")
            for principle in core_principles:
                print(f"    • {principle}")
        
        governance_structure = ethics_governance.get("governance_structure", {})
        if governance_structure:
            print(f"\n🏛️  Governance Structure:")
            for role, description in governance_structure.items():
                print(f"    • {role.replace('_', ' ').title()}: {description}")
        
        compliance_considerations = ethics_governance.get("compliance_considerations", {})
        if compliance_considerations:
            applicable_regs = compliance_considerations.get("applicable_regulations", [])
            if applicable_regs:
                print(f"\n📋 Compliance Considerations:")
                print(f"    Applicable Regulations: {', '.join(applicable_regs)}")
        
        risk_assessment = ethics_governance.get("risk_assessment", [])
        if risk_assessment:
            print(f"\n⚠️  Ethical Risk Assessment:")
            for risk in risk_assessment[:3]:  # Show first 3 risks
                risk_name = risk.get("risk", "Unknown")
                impact = risk.get("impact", "unknown")
                mitigation = risk.get("mitigation", "N/A")
                print(f"    • {risk_name} (Impact: {impact})")
                print(f"      Mitigation: {mitigation}")
        
        training_requirements = ethics_governance.get("training_requirements", [])
        if training_requirements:
            print(f"\n🎓 Training Requirements:")
            for training in training_requirements[:2]:  # Show first 2 training programs
                audience = training.get("audience", "Unknown")
                training_name = training.get("training", "Unknown")
                duration = training.get("duration", "N/A")
                print(f"    • {audience}: {training_name} ({duration})")


async def demo_comprehensive_analysis():
    """Demonstrate comprehensive AI consultant analysis."""
    print("\n" + "="*80)
    print("AI CONSULTANT AGENT - COMPREHENSIVE ANALYSIS DEMO")
    print("="*80)
    
    # Create agent
    config = AgentConfig(
        name="AI Consultant Demo Agent",
        role=AgentRole.AI_CONSULTANT,
        temperature=0.3,
        metrics_enabled=False  # Disable metrics for demo
    )
    agent = AIConsultantAgent(config)
    assessment = create_sample_assessment()
    
    print(f"\nInput Assessment:")
    print(f"- Company: {assessment.business_requirements['company_size']} {assessment.business_requirements['industry']} company")
    print(f"- Budget: {assessment.business_requirements['budget_range']}")
    print(f"- Goals: {', '.join(assessment.business_requirements['primary_goals'])}")
    print(f"- Compliance: {', '.join(assessment.business_requirements['compliance_requirements']['regulations'])}")
    
    # Execute comprehensive analysis
    print(f"\n🤖 Executing comprehensive AI transformation analysis...")
    start_time = datetime.now()
    result = await agent.execute(assessment)
    end_time = datetime.now()
    
    if result.status.value == "completed":
        print(f"✅ Comprehensive analysis completed in {result.execution_time:.2f} seconds")
        
        # Summary of all analysis components
        data = result.data
        print(f"\n📊 Analysis Summary:")
        print(f"  • Business Process Analysis: ✅")
        print(f"  • AI Opportunities Identification: ✅")
        print(f"  • AI Readiness Assessment: ✅")
        print(f"  • Use Case Recommendations: {len(result.recommendations)} generated")
        print(f"  • Transformation Strategy: ✅")
        print(f"  • Implementation Roadmap: ✅")
        print(f"  • Ethics & Governance Framework: ✅")
        
        # Key insights
        readiness_score = data.get("readiness_assessment", {}).get("overall_readiness_score", 0)
        strategy_approach = data.get("transformation_strategy", {}).get("strategy_approach", "unknown")
        total_investment = data.get("transformation_strategy", {}).get("investment_analysis", {}).get("total_investment", 0)
        
        print(f"\n🎯 Key Insights:")
        print(f"  • AI Readiness Score: {readiness_score:.2f}")
        print(f"  • Recommended Strategy: {strategy_approach}")
        print(f"  • Total Investment: ${total_investment:,.0f}")
        print(f"  • Top Use Case: {result.recommendations[0].get('use_case', 'N/A') if result.recommendations else 'None'}")
        
        # Frameworks used
        frameworks = data.get("frameworks_used", [])
        if frameworks:
            print(f"\n🔧 Frameworks Applied:")
            for framework in frameworks:
                print(f"    • {framework}")
        
    else:
        print(f"❌ Analysis failed: {result.error}")


async def main():
    """Run all AI Consultant Agent demos."""
    print("🚀 Starting AI Consultant Agent Demonstrations")
    print("=" * 80)
    
    try:
        # Run individual demos
        await demo_business_process_analysis()
        await demo_ai_opportunities_identification()
        await demo_ai_readiness_assessment()
        await demo_use_case_recommendations()
        await demo_transformation_strategy()
        await demo_ethics_and_governance()
        
        # Run comprehensive demo
        await demo_comprehensive_analysis()
        
        print(f"\n✅ All AI Consultant Agent demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())