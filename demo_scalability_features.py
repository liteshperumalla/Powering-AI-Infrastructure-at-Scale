#!/usr/bin/env python3
"""
Demo script for Scalability Features.

Tests load balancing, auto-scaling policies, resource monitoring,
and cost optimization features.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import scalability components
from src.infra_mind.core.scalability_manager import (
    ScalabilityManager,
    LoadBalancer,
    AutoScaler,
    ResourceMonitor,
    CostOptimizer,
    LoadBalancingStrategy,
    ScalingPolicy,
    AgentInstance,
    scalability_manager
)
from src.infra_mind.core.metrics_collector import initialize_metrics_collection


class MockAgent:
    """Mock agent for testing purposes."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.is_busy = False
        self.created_at = datetime.utcnow()
        self.request_count = 0
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate processing a request."""
        self.is_busy = True
        self.request_count += 1
        
        # Simulate processing time
        processing_time = 0.1 + (hash(str(request_data)) % 100) / 1000
        await asyncio.sleep(processing_time)
        
        self.is_busy = False
        
        return {
            "result": f"Processed by {self.agent_type}",
            "processing_time": processing_time,
            "request_count": self.request_count
        }
    
    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info(f"Cleaning up {self.agent_type} agent")


async def demo_load_balancing():
    """Demonstrate load balancing capabilities."""
    print("\n" + "="*60)
    print("⚖️  LOAD BALANCING DEMO")
    print("="*60)
    
    # Test different load balancing strategies
    strategies = [
        LoadBalancingStrategy.ROUND_ROBIN,
        LoadBalancingStrategy.LEAST_CONNECTIONS,
        LoadBalancingStrategy.RESOURCE_BASED
    ]
    
    for strategy in strategies:
        print(f"\n🔄 Testing {strategy.value} strategy:")
        
        load_balancer = LoadBalancer(strategy)
        
        # Create mock agent instances
        for i in range(3):
            agent = MockAgent("cto_agent")
            instance = AgentInstance(
                instance_id=f"cto_agent_{i}",
                agent_type="cto_agent",
                weight=1.0 + (i * 0.2)  # Different weights for testing
            )
            instance._agent_ref = agent
            load_balancer.register_agent_instance(instance)
        
        # Simulate load balancing
        print("   📊 Distributing requests:")
        for request_num in range(6):
            agent_instance = await load_balancer.get_next_agent("cto_agent")
            if agent_instance:
                print(f"   • Request {request_num + 1} → {agent_instance.instance_id}")
                
                # Simulate request processing
                start_time = time.time()
                success = True
                try:
                    if hasattr(agent_instance, '_agent_ref'):
                        await agent_instance._agent_ref.process_request({"request_id": request_num})
                except Exception:
                    success = False
                
                response_time = (time.time() - start_time) * 1000
                load_balancer.release_agent(agent_instance, success, response_time)
            else:
                print(f"   ❌ Request {request_num + 1} → No available agents")
        
        # Get load balancer stats
        stats = load_balancer.get_load_balancer_stats()
        pool_stats = stats["agent_pools"].get("cto_agent", {})
        
        print(f"   📈 Results:")
        print(f"     - Total instances: {pool_stats.get('total_instances', 0)}")
        print(f"     - Total requests: {pool_stats.get('total_requests', 0)}")
        print(f"     - Success rate: {pool_stats.get('success_rate', 0):.1%}")
        print(f"     - Avg response time: {pool_stats.get('avg_response_time', 0):.2f}ms")
    
    print("✅ Load balancing demo completed")


async def demo_auto_scaling():
    """Demonstrate auto-scaling capabilities."""
    print("\n" + "="*60)
    print("📈 AUTO-SCALING DEMO")
    print("="*60)
    
    load_balancer = LoadBalancer()
    auto_scaler = AutoScaler(load_balancer)
    
    # Define agent factory
    def create_cto_agent():
        return MockAgent("cto_agent")
    
    # Register agent type with scaling policy
    scaling_policy = ScalingPolicy(
        agent_type="cto_agent",
        min_instances=2,
        max_instances=6,
        scale_up_threshold=75.0,
        scale_down_threshold=25.0,
        scale_up_cooldown_seconds=60,  # Reduced for demo
        scale_down_cooldown_seconds=120
    )
    
    auto_scaler.register_agent_factory("cto_agent", create_cto_agent)
    auto_scaler.register_scaling_policy(scaling_policy)
    
    print("🔧 Registered scaling policy:")
    print(f"   • Min instances: {scaling_policy.min_instances}")
    print(f"   • Max instances: {scaling_policy.max_instances}")
    print(f"   • Scale up threshold: {scaling_policy.scale_up_threshold}%")
    print(f"   • Scale down threshold: {scaling_policy.scale_down_threshold}%")
    
    # Initialize with minimum instances
    print(f"\n🚀 Initializing with {scaling_policy.min_instances} instances...")
    for i in range(scaling_policy.min_instances):
        agent = create_cto_agent()
        instance = AgentInstance(
            instance_id=f"cto_agent_init_{i}",
            agent_type="cto_agent"
        )
        instance._agent_ref = agent
        load_balancer.register_agent_instance(instance)
    
    print(f"   ✓ Started with {len(load_balancer.agent_pools['cto_agent'])} instances")
    
    # Simulate high load to trigger scale up
    print("\n📊 Simulating high load scenario...")
    
    # Mark instances as busy to simulate high utilization
    pool = load_balancer.agent_pools["cto_agent"]
    for instance in pool:
        instance.is_busy = True
        instance.current_load = 0.9  # 90% load
    
    # Evaluate scaling decision
    decisions = await auto_scaler.evaluate_scaling_decisions()
    print(f"   • Scaling decision: {decisions.get('cto_agent', 'none')}")
    
    # Execute scaling action
    if decisions.get("cto_agent") == "up":
        success = await auto_scaler.execute_scaling_action("cto_agent", decisions["cto_agent"])
        if success:
            print(f"   ✓ Scaled up successfully")
            print(f"   • New instance count: {len(load_balancer.agent_pools['cto_agent'])}")
        else:
            print(f"   ❌ Scale up failed")
    
    # Simulate low load to trigger scale down
    print("\n📉 Simulating low load scenario...")
    
    # Mark instances as idle
    for instance in pool:
        instance.is_busy = False
        instance.current_load = 0.1  # 10% load
    
    # Wait for cooldown (simulate)
    print("   ⏳ Waiting for cooldown period...")
    await asyncio.sleep(2)  # Simulate cooldown
    
    # Clear last scaling action to allow scale down
    auto_scaler.last_scaling_action.clear()
    
    # Evaluate scaling decision again
    decisions = await auto_scaler.evaluate_scaling_decisions()
    print(f"   • Scaling decision: {decisions.get('cto_agent', 'none')}")
    
    # Execute scaling action
    if decisions.get("cto_agent") == "down":
        success = await auto_scaler.execute_scaling_action("cto_agent", decisions["cto_agent"])
        if success:
            print(f"   ✓ Scaled down successfully")
            print(f"   • New instance count: {len(load_balancer.agent_pools['cto_agent'])}")
        else:
            print(f"   ❌ Scale down failed")
    
    # Get scaling status
    print("\n📊 Current Scaling Status:")
    status = auto_scaler.get_scaling_status()
    
    if "cto_agent" in status:
        agent_status = status["cto_agent"]
        print(f"   • Current instances: {agent_status['current_instances']}")
        print(f"   • Min/Max instances: {agent_status['min_instances']}/{agent_status['max_instances']}")
        print(f"   • Can scale up: {agent_status['can_scale_up']}")
        print(f"   • Can scale down: {agent_status['can_scale_down']}")
    
    print("✅ Auto-scaling demo completed")


async def demo_resource_monitoring():
    """Demonstrate resource monitoring and capacity planning."""
    print("\n" + "="*60)
    print("📊 RESOURCE MONITORING DEMO")
    print("="*60)
    
    resource_monitor = ResourceMonitor()
    
    print("🔍 Collecting resource metrics...")
    
    # Collect several data points
    for i in range(5):
        metrics = await resource_monitor.collect_resource_metrics()
        print(f"   • Sample {i+1}:")
        print(f"     - CPU: {metrics.cpu_percent:.1f}%")
        print(f"     - Memory: {metrics.memory_percent:.1f}%")
        print(f"     - Disk: {metrics.disk_percent:.1f}%")
        print(f"     - Connections: {metrics.active_connections}")
        
        await asyncio.sleep(0.5)  # Small delay between samples
    
    # Get resource trends
    print("\n📈 Resource Trends Analysis:")
    trends = resource_monitor.get_resource_trends(1)  # Last hour (simulated)
    
    if "error" not in trends:
        print(f"   • Analysis period: {trends['time_period_hours']} hour(s)")
        print(f"   • Data points: {trends['data_points']}")
        
        for resource in ["cpu_usage", "memory_usage", "disk_usage"]:
            if resource in trends:
                data = trends[resource]
                print(f"   • {resource.replace('_', ' ').title()}:")
                print(f"     - Current: {data['current']:.1f}%")
                print(f"     - Average: {data['average']:.1f}%")
                print(f"     - Range: {data['min']:.1f}% - {data['max']:.1f}%")
                print(f"     - Trend: {data['trend']}")
    else:
        print(f"   ⚠️  {trends['error']}")
    
    # Get capacity predictions
    print("\n🔮 Capacity Predictions:")
    predictions = resource_monitor.predict_capacity_needs(24)  # Next 24 hours
    
    if "error" not in predictions:
        print(f"   • Forecast period: {predictions['forecast_hours']} hours")
        
        for resource, data in predictions["predictions"].items():
            print(f"   • {resource.replace('_', ' ').title()}:")
            print(f"     - Current: {data['current']:.1f}%")
            print(f"     - Predicted: {data['predicted']:.1f}%")
            print(f"     - Trend: {data['trend']}")
            print(f"     - Confidence: {data['confidence']}")
        
        if predictions["recommendations"]:
            print("   💡 Recommendations:")
            for rec in predictions["recommendations"]:
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
                print(f"     {priority_icon} {rec['recommendation']}")
        else:
            print("   ✅ No capacity issues predicted")
    else:
        print(f"   ⚠️  {predictions['error']}")
    
    print("✅ Resource monitoring demo completed")


async def demo_cost_optimization():
    """Demonstrate cost optimization and budget management."""
    print("\n" + "="*60)
    print("💰 COST OPTIMIZATION DEMO")
    print("="*60)
    
    # Set up load balancer with various agent types
    load_balancer = LoadBalancer()
    cost_optimizer = CostOptimizer()
    
    # Create mock agent instances of different types
    agent_types = ["cto_agent", "research_agent", "cloud_engineer_agent", "mlops_agent"]
    instance_counts = [3, 2, 4, 1]  # Different numbers for each type
    
    print("🏗️  Setting up agent instances:")
    for agent_type, count in zip(agent_types, instance_counts):
        for i in range(count):
            agent = MockAgent(agent_type)
            instance = AgentInstance(
                instance_id=f"{agent_type}_{i}",
                agent_type=agent_type,
                current_load=0.3 + (i * 0.1),  # Varying load levels
            )
            instance._agent_ref = agent
            instance.total_requests = 50 + (i * 20)  # Simulate request history
            instance.successful_requests = instance.total_requests - (i * 2)  # Some failures
            
            load_balancer.register_agent_instance(instance)
        
        print(f"   ✓ Created {count} {agent_type} instances")
    
    # Calculate current costs
    print("\n💵 Calculating current costs...")
    cost_metrics = await cost_optimizer.calculate_current_costs(load_balancer)
    
    print(f"   • Total instances: {cost_metrics.total_instances}")
    print(f"   • Total hourly cost: ${cost_metrics.total_hourly_cost:.3f}")
    print(f"   • Projected monthly cost: ${cost_metrics.projected_monthly_cost:.2f}")
    print(f"   • Utilization efficiency: {cost_metrics.utilization_efficiency:.1%}")
    print(f"   • Cost per request: ${cost_metrics.cost_per_request:.4f}")
    
    print("\n📊 Cost breakdown by agent type:")
    for agent_type, cost in cost_metrics.instance_costs.items():
        print(f"   • {agent_type}: ${cost:.3f}/hour")
    
    # Get cost optimization recommendations
    print("\n💡 Cost Optimization Recommendations:")
    recommendations = cost_optimizer.get_cost_optimization_recommendations(load_balancer)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"   {priority_icon} Recommendation {i}:")
            print(f"     - Agent: {rec['agent_type']}")
            print(f"     - Issue: {rec['issue']}")
            print(f"     - Action: {rec['recommendation']}")
            
            if "potential_monthly_savings" in rec:
                print(f"     - Potential savings: ${rec['potential_monthly_savings']:.2f}/month")
            if "current_utilization" in rec:
                print(f"     - Current utilization: {rec['current_utilization']:.1f}%")
    else:
        print("   ✅ No cost optimization recommendations at this time")
    
    # Simulate cost history and generate report
    print("\n📈 Cost Analysis Report:")
    
    # Add some historical data points
    for i in range(5):
        # Simulate different cost scenarios
        modified_metrics = CostMetrics(
            timestamp=datetime.utcnow() - timedelta(hours=i),
            total_instances=cost_metrics.total_instances + (i % 2),
            instance_costs=cost_metrics.instance_costs,
            total_hourly_cost=cost_metrics.total_hourly_cost * (1 + i * 0.1),
            utilization_efficiency=max(0.3, cost_metrics.utilization_efficiency - i * 0.05),
            cost_per_request=cost_metrics.cost_per_request * (1 + i * 0.05),
            projected_monthly_cost=cost_metrics.projected_monthly_cost * (1 + i * 0.1)
        )
        cost_optimizer.cost_history.append(modified_metrics)
    
    cost_report = cost_optimizer.get_cost_report(1)  # Last day
    
    if "error" not in cost_report:
        summary = cost_report["cost_summary"]
        efficiency = cost_report["efficiency_summary"]
        
        print(f"   • Analysis period: {cost_report['analysis_period_days']} day(s)")
        print(f"   • Current hourly cost: ${summary['current_hourly_cost']:.3f}")
        print(f"   • Average hourly cost: ${summary['average_hourly_cost']:.3f}")
        print(f"   • Projected monthly cost: ${summary['projected_monthly_cost']:.2f}")
        print(f"   • Current efficiency: {efficiency['current_efficiency']:.1%}")
        print(f"   • Average efficiency: {efficiency['average_efficiency']:.1%}")
        print(f"   • Efficiency trend: {efficiency['efficiency_trend']}")
        
        if "agent_costs" in cost_report:
            print("   📊 Agent cost breakdown:")
            for agent_type, costs in cost_report["agent_costs"].items():
                print(f"     - {agent_type}: ${costs['average_hourly_cost']:.3f}/hour avg")
    else:
        print(f"   ⚠️  {cost_report['error']}")
    
    print("✅ Cost optimization demo completed")


async def demo_comprehensive_scalability():
    """Demonstrate comprehensive scalability management."""
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE SCALABILITY DEMO")
    print("="*60)
    
    # Use the global scalability manager
    manager = scalability_manager
    
    # Register agent types
    print("🔧 Registering agent types with scalability manager...")
    
    def create_agent(agent_type):
        return MockAgent(agent_type)
    
    agent_types = [
        ("cto_agent", ScalingPolicy(
            agent_type="cto_agent",
            min_instances=2,
            max_instances=6,
            target_utilization_percent=70.0
        )),
        ("research_agent", ScalingPolicy(
            agent_type="research_agent",
            min_instances=1,
            max_instances=4,
            target_utilization_percent=75.0
        ))
    ]
    
    for agent_type, policy in agent_types:
        manager.register_agent_type(
            agent_type,
            lambda at=agent_type: create_agent(at),
            policy
        )
        print(f"   ✓ Registered {agent_type}")
    
    # Start monitoring services
    print("\n🔄 Starting monitoring services...")
    await manager.start_monitoring()
    print("   ✓ All monitoring services started")
    
    # Let monitoring run for a short time
    print("\n⏳ Collecting monitoring data...")
    await asyncio.sleep(3)
    
    # Get comprehensive status
    print("\n📊 Comprehensive Scalability Status:")
    status = await manager.get_comprehensive_status()
    
    if "error" not in status:
        print(f"   • Monitoring enabled: {status['monitoring_enabled']}")
        print(f"   • Total agent instances: {status['system_health']['total_agent_instances']}")
        print(f"   • Active agent types: {status['system_health']['active_agent_types']}")
        print(f"   • Background tasks: {status['system_health']['background_tasks_running']}")
        
        # Load balancer status
        if "load_balancer" in status:
            lb_stats = status["load_balancer"]
            print(f"\n   ⚖️  Load Balancer:")
            print(f"     - Strategy: {lb_stats['strategy']}")
            for agent_type, pool_stats in lb_stats["agent_pools"].items():
                print(f"     - {agent_type}: {pool_stats['total_instances']} instances")
        
        # Auto-scaling status
        if "auto_scaling" in status:
            scaling = status["auto_scaling"]
            print(f"\n   📈 Auto-scaling:")
            for agent_type, agent_status in scaling.items():
                print(f"     - {agent_type}: {agent_status['current_instances']} instances")
                print(f"       (min: {agent_status['min_instances']}, max: {agent_status['max_instances']})")
        
        # Resource trends
        if "resource_trends" in status and "error" not in status["resource_trends"]:
            trends = status["resource_trends"]
            print(f"\n   📊 Resource Trends:")
            for resource in ["cpu_usage", "memory_usage"]:
                if resource in trends:
                    data = trends[resource]
                    print(f"     - {resource.replace('_', ' ').title()}: {data['current']:.1f}% ({data['trend']})")
        
        # Cost analysis
        if "cost_analysis" in status and "error" not in status["cost_analysis"]:
            cost = status["cost_analysis"]
            if "cost_summary" in cost:
                summary = cost["cost_summary"]
                print(f"\n   💰 Cost Analysis:")
                print(f"     - Current hourly: ${summary['current_hourly_cost']:.3f}")
                print(f"     - Projected monthly: ${summary['projected_monthly_cost']:.2f}")
        
        # Cost recommendations
        if "cost_recommendations" in status:
            recommendations = status["cost_recommendations"]
            if recommendations:
                print(f"\n   💡 Cost Recommendations:")
                for rec in recommendations[:3]:  # Show top 3
                    priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
                    print(f"     {priority_icon} {rec['issue']} ({rec['agent_type']})")
            else:
                print(f"\n   ✅ No cost optimization recommendations")
    else:
        print(f"   ❌ Error getting status: {status['error']}")
    
    # Stop monitoring services
    print("\n🛑 Stopping monitoring services...")
    await manager.stop_monitoring()
    print("   ✓ All monitoring services stopped")
    
    print("✅ Comprehensive scalability demo completed")


async def main():
    """Run all scalability demos."""
    print("🚀 INFRA MIND SCALABILITY FEATURES DEMO")
    print("=" * 80)
    
    try:
        # Initialize metrics collection
        print("🔧 Initializing services...")
        await initialize_metrics_collection()
        
        # Run demos
        await demo_load_balancing()
        await demo_auto_scaling()
        await demo_resource_monitoring()
        await demo_cost_optimization()
        await demo_comprehensive_scalability()
        
        print("\n" + "="*80)
        print("🎉 ALL SCALABILITY DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())