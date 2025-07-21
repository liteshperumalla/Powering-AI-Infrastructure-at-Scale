#!/usr/bin/env python3
"""
Demo script for Cloud Engineer Agent functionality.

This script demonstrates the Cloud Engineer Agent's service curation and optimization capabilities.
"""

import asyncio
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_cloud_engineer_agent():
    """Demonstrate Cloud Engineer Agent functionality."""
    print("=" * 70)
    print("DEMO: Cloud Engineer Agent - Service Curation & Optimization")
    print("=" * 70)
    
    try:
        from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
        from src.infra_mind.agents.base import AgentConfig, AgentRole
        from unittest.mock import Mock
        
        print("\n1. Creating sample assessment...")
        
        # Create sample business requirements
        business_req = {
            "company_size": "medium",
            "industry": "e-commerce",
            "budget_range": "$50k-100k",
            "primary_goals": ["scalability", "cost_reduction", "performance"],
            "timeline": "4 months",
            "success_metrics": ["handle_50k_users", "reduce_costs_by_25%", "99.9%_uptime"]
        }
        
        # Create sample technical requirements
        technical_req = {
            "workload_types": ["web_application", "data_processing", "ai_ml"],
            "expected_users": 50000,
            "performance_requirements": {
                "response_time": "< 200ms",
                "availability": "99.9%",
                "throughput": "5000 rps"
            },
            "integration_needs": ["database", "api", "payment_gateway", "analytics", "cdn"],
            "data_requirements": {
                "storage_size": "50TB",
                "backup_frequency": "daily",
                "retention_period": "5 years"
            }
        }
        
        # Create mock assessment
        assessment = Mock()
        assessment.id = "demo_assessment_id"
        assessment.user_id = "demo_user"
        assessment.title = "E-commerce Platform Infrastructure Assessment"
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
        print(f"   ⚡ Workloads: {', '.join(technical_req['workload_types'])}")
        
        print("\n2. Initializing Cloud Engineer Agent...")
        
        # Create Cloud Engineer Agent with custom configuration
        config = AgentConfig(
            name="Senior Cloud Engineer Agent",
            role=AgentRole.CLOUD_ENGINEER,
            tools_enabled=["cloud_api", "calculator", "data_processor"],
            temperature=0.2,
            max_tokens=2500,
            metrics_enabled=False,  # Disable for demo
            memory_enabled=False    # Disable for demo
        )
        
        cloud_engineer_agent = CloudEngineerAgent(config)
        print(f"   ✅ Initialized {cloud_engineer_agent.name}")
        print(f"   🔧 Tools enabled: {', '.join(cloud_engineer_agent.config.tools_enabled)}")
        print(f"   ☁️  Cloud platforms: {', '.join(cloud_engineer_agent.cloud_platforms)}")
        print(f"   📋 Service categories: {len(cloud_engineer_agent.service_categories)}")
        
        print("\n3. Executing service curation analysis...")
        
        # Execute Cloud Engineer Agent
        result = await cloud_engineer_agent.execute(assessment)
        
        if result.status.value == "completed":
            print(f"   ✅ Analysis completed successfully in {result.execution_time:.2f}s")
            print(f"   📋 Generated {len(result.recommendations)} service recommendations")
            
            # Display results
            await display_cloud_engineer_results(result)
            
        else:
            print(f"   ❌ Analysis failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")


async def display_cloud_engineer_results(result):
    """Display Cloud Engineer Agent results in a formatted way."""
    print("\n" + "=" * 70)
    print("CLOUD ENGINEER AGENT ANALYSIS RESULTS")
    print("=" * 70)
    
    # Technical Analysis Summary
    if "technical_analysis" in result.data:
        technical_analysis = result.data["technical_analysis"]
        
        print("\n🔧 TECHNICAL ANALYSIS SUMMARY")
        print("-" * 35)
        
        if "workload_analysis" in technical_analysis:
            workload = technical_analysis["workload_analysis"]
            print(f"Workload Types: {', '.join(workload.get('types', []))}")
            print(f"Expected Users: {workload.get('expected_users', 0):,}")
            print(f"Performance Requirements: {workload.get('performance_requirements', {})}")
        
        if "service_needs" in technical_analysis:
            service_needs = technical_analysis["service_needs"]
            needed_services = [k for k, v in service_needs.items() if v.get("needed", False)]
            print(f"Required Services: {', '.join(needed_services)}")
        
        if "scalability_needs" in technical_analysis:
            scalability = technical_analysis["scalability_needs"]
            print(f"Auto-scaling needed: {scalability.get('auto_scaling_needed', False)}")
            print(f"CDN recommended: {scalability.get('cdn_recommended', False)}")
    
    # Service Recommendations
    print(f"\n☁️  SERVICE RECOMMENDATIONS ({len(result.recommendations)})")
    print("-" * 45)
    
    for i, rec in enumerate(result.recommendations, 1):
        priority_emoji = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
        service = rec["service"]
        
        print(f"\n{i}. {priority_emoji} {rec['title']} ({rec['priority'].upper()} PRIORITY)")
        print(f"   Provider: {service.get('provider', 'Unknown').upper()}")
        print(f"   Service: {service.get('name', 'Unknown')}")
        print(f"   Category: {rec['category']}")
        print(f"   Rationale: {rec['rationale']}")
        
        if "cost_impact" in rec:
            cost = rec["cost_impact"]
            print(f"   Monthly Cost: ${cost.get('monthly_cost', 0):.2f}")
            print(f"   Cost Category: {cost.get('cost_category', 'unknown')}")
        
        if "alternatives" in rec and rec["alternatives"]:
            alt_count = len(rec["alternatives"])
            print(f"   Alternatives: {alt_count} other options available")
        
        if "business_alignment" in rec:
            alignment = rec["business_alignment"]
            print(f"   Business Alignment: {alignment.get('overall_alignment', 'unknown')}")
    
    # Cost Analysis
    if "cost_analysis" in result.data:
        cost_analysis = result.data["cost_analysis"]
        
        print(f"\n💰 COST ANALYSIS")
        print("-" * 20)
        
        total_monthly = cost_analysis.get("total_monthly_cost", 0)
        total_annual = cost_analysis.get("annual_cost", 0)
        
        print(f"Total Monthly Cost: ${total_monthly:.2f}")
        print(f"Total Annual Cost: ${total_annual:.2f}")
        
        if "cost_breakdown" in cost_analysis:
            breakdown = cost_analysis["cost_breakdown"]
            if "by_category" in breakdown:
                print(f"\nCost Breakdown by Category:")
                for category, info in breakdown["by_category"].items():
                    monthly_cost = info.get("monthly_cost", 0)
                    percentage = info.get("percentage", 0)
                    print(f"  • {category.title()}: ${monthly_cost:.2f}/month ({percentage:.1f}%)")
        
        if "optimization_recommendations" in cost_analysis:
            optimizations = cost_analysis["optimization_recommendations"]
            if optimizations:
                print(f"\nCost Optimization Opportunities:")
                for opt in optimizations[:3]:  # Show top 3
                    savings = opt.get("monthly_savings", 0)
                    print(f"  • {opt['recommendation']}")
                    print(f"    Potential savings: ${savings:.2f}/month")
    
    # Implementation Guidance
    if "implementation_guidance" in result.data:
        guidance = result.data["implementation_guidance"]
        
        print(f"\n🚀 IMPLEMENTATION GUIDANCE")
        print("-" * 30)
        
        if "deployment_roadmap" in guidance:
            roadmap = guidance["deployment_roadmap"]
            phases = roadmap.get("phases", [])
            total_weeks = roadmap.get("total_duration_weeks", 0)
            
            print(f"Deployment Timeline: {total_weeks} weeks total")
            print(f"Deployment Phases:")
            for phase in phases:
                print(f"  Phase {phase['phase']}: {phase['name']} ({phase['duration_weeks']} weeks)")
                print(f"    Services: {', '.join(phase['services'])}")
        
        if "best_practices" in guidance:
            practices = guidance["best_practices"]
            if practices:
                print(f"\nKey Best Practices:")
                for practice in practices[:4]:  # Show top 4
                    print(f"  • {practice['category']}: {practice['practice']}")
        
        if "cost_management" in guidance:
            cost_mgmt = guidance["cost_management"]
            if cost_mgmt:
                print(f"\nCost Management Strategies:")
                for strategy in cost_mgmt[:2]:  # Show top 2
                    print(f"  • {strategy['strategy']}: {strategy['description']}")
                    savings = strategy.get("potential_savings", "Unknown")
                    print(f"    Potential savings: {savings}")
    
    # Service Data Summary
    if "service_data" in result.data:
        service_data = result.data["service_data"]
        successful_providers = service_data.get("successful_providers", [])
        
        print(f"\n📊 DATA COLLECTION SUMMARY")
        print("-" * 30)
        print(f"Providers analyzed: {', '.join(successful_providers)}")
        print(f"Collection timestamp: {service_data.get('collection_timestamp', 'N/A')}")
    
    print(f"\n📈 ANALYSIS METADATA")
    print("-" * 22)
    print(f"Platforms analyzed: {', '.join(result.data.get('platforms_analyzed', []))}")
    print(f"Analysis timestamp: {result.data.get('analysis_timestamp', 'N/A')}")
    print(f"Execution time: {result.execution_time:.2f} seconds")
    
    if result.metrics:
        print(f"Agent metrics available: Yes")
    else:
        print(f"Agent metrics available: No")


async def demo_agent_capabilities():
    """Demonstrate Cloud Engineer Agent capabilities and configuration."""
    print("\n" + "=" * 70)
    print("CLOUD ENGINEER AGENT CAPABILITIES DEMO")
    print("=" * 70)
    
    try:
        from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
        from src.infra_mind.agents.base import AgentRole
        from src.infra_mind.agents import agent_registry, AgentFactory
        
        print("\n1. Agent Registry Integration...")
        
        # Test agent registry
        factory = AgentFactory(agent_registry)
        cloud_engineer_agent = await factory.create_agent(AgentRole.CLOUD_ENGINEER)
        
        if cloud_engineer_agent:
            print(f"   ✅ Cloud Engineer Agent created through factory")
            print(f"   🆔 Agent ID: {cloud_engineer_agent.agent_id}")
            print(f"   📝 Agent Name: {cloud_engineer_agent.name}")
        
        print("\n2. Agent Capabilities...")
        capabilities = cloud_engineer_agent.get_capabilities()
        for capability in capabilities:
            print(f"   • {capability}")
        
        print("\n3. Health Check...")
        health = await cloud_engineer_agent.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Role: {health['role']}")
        print(f"   Version: {health['version']}")
        print(f"   Tools: {health['tools_count']}")
        
        print("\n4. Cloud Platforms...")
        print("   Supported platforms:")
        for platform in cloud_engineer_agent.cloud_platforms:
            print(f"     • {platform.upper()}")
        
        print("\n5. Service Categories...")
        print("   Service categories:")
        for category in cloud_engineer_agent.service_categories:
            print(f"     • {category.replace('_', ' ').title()}")
        
        print("\n6. Ranking Criteria...")
        print("   Service ranking criteria:")
        for criteria in cloud_engineer_agent.ranking_criteria:
            print(f"     • {criteria.replace('_', ' ').title()}")
        
    except Exception as e:
        logger.error(f"Capabilities demo error: {e}")
        print(f"❌ Capabilities demo failed: {e}")


async def main():
    """Run all Cloud Engineer Agent demos."""
    print("🚀 Starting Cloud Engineer Agent Demo")
    print("This demo shows the Cloud Engineer Agent's service curation capabilities")
    print("for task 6.2: Implement Cloud Engineer Agent (MVP Priority)")
    
    await demo_cloud_engineer_agent()
    await demo_agent_capabilities()
    
    print("\n" + "=" * 70)
    print("✅ Cloud Engineer Agent Demo completed!")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("• Multi-cloud service curation and comparison")
    print("• Cost optimization using real-time pricing")
    print("• Service ranking based on multiple criteria")
    print("• Business goal alignment assessment")
    print("• Implementation guidance and roadmaps")
    print("• Best practices and cost management strategies")
    print("• Integration with agent registry and factory")


if __name__ == "__main__":
    asyncio.run(main())