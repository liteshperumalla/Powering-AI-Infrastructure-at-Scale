#!/usr/bin/env python3
"""
Demo script for Infrastructure Agent.

This script demonstrates the Infrastructure Agent's capabilities for:
- Compute resource planning and optimization
- Performance benchmarking and capacity planning
- Infrastructure scaling strategies and automation
- Resource utilization optimization
- Cost-effective infrastructure sizing
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.agents.infrastructure_agent import InfrastructureAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAssessment:
    """Mock assessment for demo purposes."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = "demo_assessment_id"
    
    def dict(self):
        return {
            "user_id": getattr(self, "user_id", "demo_user"),
            "title": getattr(self, "title", "Demo Assessment"),
            "business_requirements": getattr(self, "business_requirements", {}),
            "technical_requirements": getattr(self, "technical_requirements", {}),
            "status": getattr(self, "status", "draft")
        }


def create_sample_assessment() -> MockAssessment:
    """Create a sample assessment for testing."""
    return MockAssessment(
        user_id="demo_user",
        title="Infrastructure Agent Demo Assessment",
        description="Demo assessment for infrastructure agent capabilities",
        business_requirements={
            "company_size": "mid-size",
            "industry": "technology",
            "budget_range": "100k-500k",
            "timeline": "6_months",
            "compliance_needs": ["SOC2"],
            "business_goals": [
                "scale_ai_infrastructure",
                "optimize_costs",
                "improve_performance"
            ]
        },
        technical_requirements={
            "workload_types": [
                "ai_ml",
                "data_processing",
                "web_application"
            ],
            "expected_users": 5000,
            "performance_requirements": {
                "response_time_target": 200,
                "throughput_target": 2000,
                "availability_target": 99.9
            },
            "current_infrastructure": {
                "cloud_provider": "aws",
                "instance_count": 10,
                "instance_types": ["m5.large", "c5.xlarge"]
            },
            "scalability_needs": {
                "auto_scaling": True,
                "peak_capacity": "3x_normal",
                "geographic_distribution": False
            }
        },
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


async def demo_infrastructure_analysis():
    """Demonstrate Infrastructure Agent analysis capabilities."""
    print("🏗️  Infrastructure Agent Demo")
    print("=" * 50)
    
    # Create Infrastructure Agent
    config = AgentConfig(
        name="Demo Infrastructure Agent",
        role=AgentRole.INFRASTRUCTURE,
        temperature=0.1,
        max_tokens=3000,
        metrics_enabled=False  # Disable metrics for demo
    )
    
    agent = InfrastructureAgent(config)
    
    # Create sample assessment
    assessment = create_sample_assessment()
    
    print(f"📊 Assessment Overview:")
    print(f"   Company Size: {assessment.business_requirements['company_size']}")
    print(f"   Industry: {assessment.business_requirements['industry']}")
    print(f"   Expected Users: {assessment.technical_requirements['expected_users']:,}")
    print(f"   Workload Types: {', '.join(assessment.technical_requirements['workload_types'])}")
    print()
    
    # Execute Infrastructure Agent
    print("🔄 Running Infrastructure Agent analysis...")
    result = await agent.execute(assessment)
    
    if result.status.value == "completed":
        print("✅ Infrastructure analysis completed successfully!")
        print()
        
        # Display recommendations
        recommendations = result.recommendations
        print(f"📋 Infrastructure Recommendations ({len(recommendations)} total):")
        print("-" * 50)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['title']}")
            print(f"   Category: {rec['category']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Description: {rec['description']}")
            print(f"   Timeline: {rec['timeline']}")
            print(f"   Investment: {rec['investment_required']}")
            print(f"   Business Impact: {rec['business_impact']}")
            
            if 'expected_savings' in rec:
                print(f"   Expected Savings: {rec['expected_savings']}")
            
            print()
        
        # Display analysis data
        analysis_data = result.data
        print("📈 Infrastructure Analysis Details:")
        print("-" * 50)
        
        # Infrastructure Analysis
        infra_analysis = analysis_data.get("infrastructure_analysis", {})
        if infra_analysis:
            print("🔍 Infrastructure Requirements Analysis:")
            workload_chars = infra_analysis.get("workload_characteristics", {})
            print(f"   Primary Workload Type: {workload_chars.get('primary_workload_type', 'N/A')}")
            print(f"   Resource Intensity: {workload_chars.get('resource_intensity', 'N/A')}")
            print(f"   Scalability Pattern: {workload_chars.get('scalability_pattern', 'N/A')}")
            
            compute_req = infra_analysis.get("compute_requirements", {})
            print(f"   Recommended CPU Cores: {compute_req.get('cpu_cores', 'N/A')}")
            print(f"   Recommended Memory: {compute_req.get('memory_gb', 'N/A')} GB")
            print(f"   Instance Type: {compute_req.get('instance_type', 'N/A')}")
            print()
        
        # Capacity Analysis
        capacity_analysis = analysis_data.get("capacity_analysis", {})
        if capacity_analysis:
            print("📊 Capacity Planning Analysis:")
            current_capacity = capacity_analysis.get("current_capacity", {})
            print(f"   Required Instances: {current_capacity.get('required_instances', 'N/A')}")
            print(f"   CPU Utilization Target: {current_capacity.get('cpu_utilization_target', 'N/A')}%")
            print(f"   Memory Utilization Target: {current_capacity.get('memory_utilization_target', 'N/A')}%")
            print(f"   Planning Confidence: {capacity_analysis.get('confidence_level', 'N/A')}")
            print()
        
        # Scaling Strategies
        scaling_strategies = analysis_data.get("scaling_strategies", {})
        if scaling_strategies:
            print("⚡ Scaling Strategies:")
            optimal_patterns = scaling_strategies.get("optimal_scaling_patterns", [])
            for pattern in optimal_patterns:
                print(f"   Pattern: {pattern.get('pattern', 'N/A')}")
                print(f"   Rationale: {pattern.get('rationale', 'N/A')}")
                print(f"   Scaling Factor: {pattern.get('scaling_factor', 'N/A')}x")
            print()
        
        # Cost Optimization
        cost_optimization = analysis_data.get("cost_optimization", {})
        if cost_optimization:
            print("💰 Cost Optimization Analysis:")
            current_costs = cost_optimization.get("current_costs", {})
            potential_savings = cost_optimization.get("potential_savings", {})
            
            print(f"   Current Annual Cost: ${current_costs.get('annual_cost', 0):,.0f}")
            print(f"   Potential Annual Savings: ${potential_savings.get('annual_savings', 0):,.0f}")
            print(f"   Savings Percentage: {potential_savings.get('total_savings_percentage', 0):.1f}%")
            
            savings_breakdown = potential_savings.get("savings_breakdown", {})
            if savings_breakdown:
                print("   Savings Breakdown:")
                for source, amount in savings_breakdown.items():
                    print(f"     {source.replace('_', ' ').title()}: ${amount:,.0f}")
            print()
        
        # Performance Benchmarking
        benchmarking_plan = analysis_data.get("benchmarking_plan", {})
        if benchmarking_plan:
            print("🎯 Performance Benchmarking Plan:")
            benchmarking_metrics = benchmarking_plan.get("benchmarking_metrics", {})
            if benchmarking_metrics:
                print(f"   Metrics: {benchmarking_metrics.get('metrics', [])}")
            
            load_testing = benchmarking_plan.get("load_testing_strategy", {})
            if load_testing:
                print(f"   Load Testing Strategy: {load_testing.get('strategy', 'N/A')}")
                print(f"   Max Test Users: {load_testing.get('max_users', 'N/A'):,}")
            print()
        
        # Agent Performance
        if result.execution_time:
            print(f"⏱️  Agent Execution Time: {result.execution_time:.2f} seconds")
        
        if result.metrics:
            print(f"📊 Agent Metrics: {json.dumps(result.metrics, indent=2)}")
    
    else:
        print(f"❌ Infrastructure analysis failed: {result.error}")
        return False
    
    return True


async def demo_infrastructure_scenarios():
    """Demonstrate Infrastructure Agent with different scenarios."""
    print("\n🎭 Infrastructure Agent Scenario Testing")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "High-Traffic E-commerce",
            "business_requirements": {
                "company_size": "large",
                "industry": "ecommerce",
                "budget_range": "500k-1m"
            },
            "technical_requirements": {
                "workload_types": ["web_application", "database", "ai_ml"],
                "expected_users": 50000,
                "performance_requirements": {
                    "response_time_target": 100,
                    "throughput_target": 10000,
                    "availability_target": 99.99
                }
            }
        },
        {
            "name": "AI Research Startup",
            "business_requirements": {
                "company_size": "startup",
                "industry": "technology",
                "budget_range": "50k-100k"
            },
            "technical_requirements": {
                "workload_types": ["ai_ml", "data_processing"],
                "expected_users": 100,
                "performance_requirements": {
                    "response_time_target": 1000,
                    "throughput_target": 100,
                    "availability_target": 99.0
                }
            }
        },
        {
            "name": "Healthcare Data Platform",
            "business_requirements": {
                "company_size": "medium",
                "industry": "healthcare",
                "budget_range": "200k-500k"
            },
            "technical_requirements": {
                "workload_types": ["data_processing", "web_application"],
                "expected_users": 5000,
                "performance_requirements": {
                    "response_time_target": 300,
                    "throughput_target": 1000,
                    "availability_target": 99.9
                }
            }
        }
    ]
    
    config = AgentConfig(
        name="Scenario Infrastructure Agent",
        role=AgentRole.INFRASTRUCTURE,
        metrics_enabled=False
    )
    agent = InfrastructureAgent(config)
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 30)
        
        # Create assessment for scenario
        assessment = MockAssessment(
            user_id="scenario_user",
            title=f"Scenario: {scenario['name']}",
            description=f"Infrastructure assessment for {scenario['name']} scenario",
            business_requirements=scenario["business_requirements"],
            technical_requirements=scenario["technical_requirements"],
            status="draft",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Run analysis
        result = await agent.execute(assessment)
        
        if result.status.value == "completed":
            recommendations = result.recommendations
            print(f"✅ Generated {len(recommendations)} recommendations")
            
            # Show top recommendation
            if recommendations:
                top_rec = recommendations[0]
                print(f"🔝 Top Recommendation: {top_rec['title']}")
                print(f"   Priority: {top_rec['priority']}")
                print(f"   Impact: {top_rec['business_impact']}")
            
            # Show key metrics
            analysis_data = result.data
            infra_analysis = analysis_data.get("infrastructure_analysis", {})
            compute_req = infra_analysis.get("compute_requirements", {})
            
            print(f"💻 Compute Requirements:")
            print(f"   CPU Cores: {compute_req.get('cpu_cores', 'N/A')}")
            print(f"   Memory: {compute_req.get('memory_gb', 'N/A')} GB")
            print(f"   Instance Type: {compute_req.get('instance_type', 'N/A')}")
            
            cost_optimization = analysis_data.get("cost_optimization", {})
            if cost_optimization:
                current_costs = cost_optimization.get("current_costs", {})
                print(f"💰 Estimated Annual Cost: ${current_costs.get('annual_cost', 0):,.0f}")
        else:
            print(f"❌ Analysis failed: {result.error}")


async def main():
    """Main demo function."""
    print("🚀 Starting Infrastructure Agent Demo")
    print("=" * 60)
    
    try:
        # Run main demo
        success = await demo_infrastructure_analysis()
        
        if success:
            # Run scenario testing
            await demo_infrastructure_scenarios()
            
            print("\n✅ Infrastructure Agent demo completed successfully!")
            print("\n📝 Summary:")
            print("   - Infrastructure Agent provides compute resource planning")
            print("   - Performs capacity planning and scaling strategy design")
            print("   - Optimizes resource allocation and costs")
            print("   - Creates performance benchmarking plans")
            print("   - Generates actionable infrastructure recommendations")
        else:
            print("\n❌ Demo failed - check logs for details")
            
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())