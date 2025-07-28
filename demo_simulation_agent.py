#!/usr/bin/env python3
"""
Demo script for Simulation Agent.

This script demonstrates the Simulation Agent's capabilities for scenario modeling,
cost projections, capacity planning, and mathematical forecasting.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the Simulation Agent
from src.infra_mind.agents.simulation_agent import SimulationAgent, AgentConfig, AgentRole
from src.infra_mind.models.assessment import Assessment


def create_sample_assessment() -> Assessment:
    """Create a sample assessment for testing."""
    return Assessment(
        user_id="demo_user_123",
        title="Demo Infrastructure Assessment",
        description="Sample assessment for testing Simulation Agent capabilities",
        business_requirements={
            "company_size": "medium",
            "industry": "technology",
            "budget_range": "200k-800k",
            "timeline": "18_months",
            "growth_expectations": "high",
            "primary_concerns": ["cost", "scalability", "performance"],
            "risk_tolerance": "medium",
            "compliance_needs": ["GDPR"]
        },
        technical_requirements={
            "expected_users": 5000,
            "workload_types": ["ai_ml", "data_processing", "web_application"],
            "performance_requirements": {
                "response_time": "< 300ms",
                "throughput": "> 1000 rps",
                "availability": "99.9%"
            },
            "scalability_needs": {
                "auto_scaling": True,
                "peak_capacity": "10x normal load",
                "geographic_distribution": ["US", "EU"]
            },
            "current_infrastructure": {
                "cloud_provider": "aws",
                "compute_instances": 10,
                "storage_gb": 5000,
                "monthly_cost": 15000
            }
        }
    )


async def demo_simulation_agent():
    """Demonstrate Simulation Agent capabilities."""
    print("=" * 80)
    print("SIMULATION AGENT DEMO")
    print("=" * 80)
    
    # Create agent configuration
    config = AgentConfig(
        name="Demo Simulation Agent",
        role=AgentRole.SIMULATION,
        temperature=0.1,
        max_tokens=3000,
        tools_enabled=["calculator", "data_processor", "cloud_api"]
    )
    
    # Initialize the agent
    agent = SimulationAgent(config)
    print(f"✓ Initialized {agent.name}")
    print(f"  Role: {agent.role.value}")
    print(f"  Agent ID: {agent.agent_id}")
    
    # Create sample assessment
    assessment = create_sample_assessment()
    print(f"✓ Created sample assessment")
    print(f"  Expected users: {assessment.technical_requirements['expected_users']:,}")
    print(f"  Budget range: {assessment.business_requirements['budget_range']}")
    print(f"  Growth expectations: {assessment.business_requirements['growth_expectations']}")
    
    # Execute the agent
    print("\n" + "=" * 60)
    print("EXECUTING SIMULATION ANALYSIS")
    print("=" * 60)
    
    try:
        result = await agent.execute(assessment)
        
        if result.status.value == "completed":
            print("✓ Simulation Agent completed successfully!")
            print(f"  Execution time: {result.execution_time:.2f} seconds")
            print(f"  Recommendations: {len(result.recommendations)}")
            
            # Display simulation results
            await display_simulation_results(result)
            
        else:
            print(f"✗ Agent execution failed: {result.error}")
            
    except Exception as e:
        print(f"✗ Error during execution: {str(e)}")
        logger.error("Agent execution failed", exc_info=True)


async def display_simulation_results(result):
    """Display simulation results in a formatted way."""
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    
    data = result.data
    
    # Display scenario analysis
    scenario_analysis = data.get("scenario_analysis", {})
    print("\n📊 SCENARIO ANALYSIS:")
    print(f"  Required scenarios: {len(scenario_analysis.get('required_scenarios', []))}")
    print(f"  Time horizons: {scenario_analysis.get('time_horizons', [])}")
    print(f"  Growth model: {scenario_analysis.get('growth_parameters', {}).get('growth_model', 'N/A')}")
    print(f"  Base growth rate: {scenario_analysis.get('growth_parameters', {}).get('base_growth_rate', 0)*100:.1f}%")
    
    # Display cost projections
    cost_projections = data.get("cost_projections", {})
    baseline_projections = cost_projections.get("baseline_projections", {})
    print("\n💰 COST PROJECTIONS:")
    for horizon, projection in baseline_projections.items():
        if isinstance(projection, dict) and "total_cost" in projection:
            print(f"  {horizon}: ${projection['total_cost']:,.0f}")
            print(f"    Average monthly: ${projection.get('average_monthly_cost', 0):,.0f}")
            print(f"    Final users: {projection.get('final_user_count', 0):,}")
    
    # Display Monte Carlo results
    monte_carlo = cost_projections.get("monte_carlo_results", {})
    if monte_carlo:
        print("\n🎲 MONTE CARLO SIMULATION:")
        for horizon, mc_result in monte_carlo.items():
            if isinstance(mc_result, dict):
                print(f"  {horizon}:")
                print(f"    Mean cost: ${mc_result.get('mean', 0):,.0f}")
                print(f"    95% confidence: ${mc_result.get('confidence_interval_95', [0, 0])[0]:,.0f} - ${mc_result.get('confidence_interval_95', [0, 0])[1]:,.0f}")
    
    # Display capacity simulations
    capacity_simulations = data.get("capacity_simulations", {})
    capacity_projections = capacity_simulations.get("capacity_projections", {})
    print("\n🏗️ CAPACITY PROJECTIONS:")
    for horizon, projection in capacity_projections.items():
        if isinstance(projection, dict):
            final_capacity = projection.get("final_capacity", {})
            print(f"  {horizon}:")
            print(f"    CPU: {final_capacity.get('cpu', 0)} cores")
            print(f"    Memory: {final_capacity.get('memory', 0)} GB")
            print(f"    Storage: {final_capacity.get('storage', 0)} GB")
            print(f"    Scaling factor: {projection.get('scaling_factor', 1.0):.1f}x")
    
    # Display bottleneck analysis
    bottleneck_analysis = capacity_simulations.get("bottleneck_analysis", {})
    critical_bottlenecks = bottleneck_analysis.get("critical_bottlenecks", [])
    if critical_bottlenecks:
        print("\n⚠️ CRITICAL BOTTLENECKS:")
        for bottleneck in critical_bottlenecks[:3]:  # Show top 3
            print(f"  {bottleneck.get('resource_type', 'Unknown').title()}:")
            print(f"    Timeline: {bottleneck.get('timeline', 'Unknown')}")
            print(f"    Severity: {bottleneck.get('severity', 'Unknown')}")
            print(f"    Investment required: ${bottleneck.get('investment_required', 0):,.0f}")
    
    # Display scaling simulations
    scaling_simulations = data.get("scaling_simulations", {})
    scenario_results = scaling_simulations.get("scenario_results", {})
    print("\n📈 SCALING SCENARIOS:")
    for scenario_name, scenario_result in scenario_results.items():
        if isinstance(scenario_result, dict):
            print(f"  {scenario_name.title()}:")
            print(f"    Strategy: {scenario_result.get('scaling_strategy', 'Unknown')}")
            print(f"    Projected cost: ${scenario_result.get('projected_cost', 0):,.0f}")
            print(f"    Performance score: {scenario_result.get('performance_score', 0):.0f}/100")
            print(f"    Risk score: {scenario_result.get('risk_score', 0):.1f}")
    
    # Display optimal scaling path
    optimal_scaling = scaling_simulations.get("optimal_scaling_path", {})
    if optimal_scaling:
        print("\n🎯 OPTIMAL SCALING PATH:")
        print(f"  Strategy: {optimal_scaling.get('strategy', 'Unknown')}")
        print(f"  Efficiency gain: {optimal_scaling.get('efficiency_gain', 0):.0f}%")
        print(f"  Confidence level: {optimal_scaling.get('confidence_level', 0)*100:.0f}%")
    
    # Display performance modeling
    performance_modeling = data.get("performance_modeling", {})
    performance_projections = performance_modeling.get("performance_projections", {})
    print("\n⚡ PERFORMANCE PROJECTIONS:")
    for horizon, projection in performance_projections.items():
        if isinstance(projection, dict):
            trend = projection.get("performance_trend", "Unknown")
            critical_thresholds = projection.get("critical_thresholds", {})
            print(f"  {horizon}:")
            print(f"    Trend: {trend}")
            if critical_thresholds.get("cpu_threshold_month"):
                print(f"    CPU threshold: Month {critical_thresholds['cpu_threshold_month']}")
            if critical_thresholds.get("memory_threshold_month"):
                print(f"    Memory threshold: Month {critical_thresholds['memory_threshold_month']}")
    
    # Display risk analysis
    risk_analysis = data.get("risk_analysis", {})
    identified_risks = risk_analysis.get("identified_risks", [])
    print("\n🚨 RISK ANALYSIS:")
    print(f"  Overall risk score: {risk_analysis.get('risk_score', 0):.2f}")
    if identified_risks:
        print("  Top risks:")
        for risk in identified_risks[:3]:  # Show top 3 risks
            print(f"    {risk.get('risk_type', 'Unknown').replace('_', ' ').title()}:")
            print(f"      Probability: {risk.get('probability', 0)*100:.0f}%")
            print(f"      Impact: {risk.get('impact_multiplier', 1.0):.1f}x")
            print(f"      Potential cost: ${risk.get('potential_cost_impact', 0):,.0f}")
    
    # Display recommendations
    print("\n" + "=" * 60)
    print("SIMULATION RECOMMENDATIONS")
    print("=" * 60)
    
    for i, rec in enumerate(result.recommendations, 1):
        print(f"\n{i}. {rec.get('title', 'Untitled Recommendation')}")
        print(f"   Category: {rec.get('category', 'general')}")
        print(f"   Priority: {rec.get('priority', 'medium').upper()}")
        print(f"   Description: {rec.get('description', 'No description')}")
        print(f"   Business Impact: {rec.get('business_impact', 'Not specified')}")
        print(f"   Timeline: {rec.get('timeline', 'Not specified')}")
        print(f"   Investment: {rec.get('investment_required', 'Not specified')}")
        
        if rec.get('confidence_level'):
            print(f"   Confidence: {rec['confidence_level']*100:.0f}%")
        
        # Show implementation steps
        steps = rec.get('implementation_steps', [])
        if steps:
            print("   Implementation Steps:")
            for j, step in enumerate(steps[:3], 1):  # Show first 3 steps
                print(f"     {j}. {step}")
    
    # Display simulation metadata
    metadata = data.get("simulation_metadata", {})
    print(f"\n📋 Simulation completed at: {metadata.get('simulation_timestamp', 'Unknown')}")
    print(f"   Confidence level: {metadata.get('confidence_level', 0)*100:.0f}%")
    print(f"   Monte Carlo iterations: {metadata.get('monte_carlo_iterations', 0):,}")


async def demo_agent_health_check():
    """Demonstrate agent health check."""
    print("\n" + "=" * 60)
    print("AGENT HEALTH CHECK")
    print("=" * 60)
    
    agent = SimulationAgent()
    health = await agent.health_check()
    
    print("Agent Health Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")


async def demo_agent_capabilities():
    """Demonstrate agent capabilities."""
    print("\n" + "=" * 60)
    print("AGENT CAPABILITIES")
    print("=" * 60)
    
    agent = SimulationAgent()
    capabilities = agent.get_capabilities()
    
    print("Simulation Agent Capabilities:")
    for capability in capabilities:
        print(f"  • {capability}")


async def main():
    """Main demo function."""
    print("Starting Simulation Agent Demo...")
    
    try:
        # Run the main demo
        await demo_simulation_agent()
        
        # Run additional demos
        await demo_agent_health_check()
        await demo_agent_capabilities()
        
        print("\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logger.error("Demo execution failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())