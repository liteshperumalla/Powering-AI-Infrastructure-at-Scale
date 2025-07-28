#!/usr/bin/env python3
"""
Demo script for Performance Optimization features.

Tests database query optimization, advanced caching, LLM prompt optimization,
and horizontal scaling capabilities.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import performance optimization components
from src.infra_mind.core.performance_optimizer import (
    DatabaseQueryOptimizer,
    AdvancedCacheManager,
    LLMPromptOptimizer,
    HorizontalScalingManager,
    PerformanceOptimizer,
    performance_optimizer
)
from src.infra_mind.core.cache import init_cache
from src.infra_mind.core.database import init_database
from src.infra_mind.core.metrics_collector import initialize_metrics_collection


async def demo_database_optimization():
    """Demonstrate database query optimization."""
    print("\n" + "="*60)
    print("🗄️  DATABASE QUERY OPTIMIZATION DEMO")
    print("="*60)
    
    db_optimizer = DatabaseQueryOptimizer()
    
    # Simulate some database queries
    test_queries = [
        {
            "collection": "assessments",
            "operation": "find",
            "query": {"user_id": "user123", "status": "active"}
        },
        {
            "collection": "recommendations",
            "operation": "find",
            "query": {"assessment_id": "assess123", "confidence_score": {"$gte": 0.8}}
        },
        {
            "collection": "users",
            "operation": "find",
            "query": {"email": "user@example.com"}
        }
    ]
    
    print("📊 Profiling database queries...")
    
    for query_data in test_queries:
        async with db_optimizer.profile_query(
            query_data["collection"],
            query_data["operation"],
            query_data["query"]
        ) as query_hash:
            # Simulate query execution time
            await asyncio.sleep(0.1 + (hash(query_hash) % 100) / 1000)
            print(f"   ✓ Profiled query: {query_data['collection']}.{query_data['operation']}")
    
    # Get performance report
    print("\n📈 Database Performance Report:")
    report = await db_optimizer.get_query_performance_report()
    
    if "summary" in report:
        summary = report["summary"]
        print(f"   • Total queries: {summary['total_queries']}")
        print(f"   • Average execution time: {summary['avg_execution_time_ms']:.2f}ms")
        print(f"   • Slow queries: {summary['slow_queries_count']}")
        print(f"   • Slow query rate: {summary['slow_query_rate']:.1f}%")
    
    # Get index optimization suggestions
    print("\n🔍 Index Optimization Analysis:")
    index_report = await db_optimizer.optimize_indexes()
    
    if "suggestions" in index_report:
        suggestions = index_report["suggestions"]
        if suggestions:
            for suggestion in suggestions[:3]:  # Show first 3
                print(f"   • {suggestion['collection']}: {suggestion['suggestion']}")
        else:
            print("   ✓ No index optimization suggestions at this time")
    
    print("✅ Database optimization demo completed")


async def demo_advanced_caching():
    """Demonstrate advanced caching strategies."""
    print("\n" + "="*60)
    print("🚀 ADVANCED CACHING DEMO")
    print("="*60)
    
    cache_manager = AdvancedCacheManager()
    
    # Start prefetch worker
    prefetch_task = asyncio.create_task(cache_manager.start_prefetch_worker())
    
    print("💾 Testing intelligent caching...")
    
    # Test cache operations
    test_data = [
        {"provider": "aws", "service": "ec2", "region": "us-east-1", "data": {"instances": ["t3.micro", "t3.small"]}},
        {"provider": "azure", "service": "compute", "region": "eastus", "data": {"vms": ["Standard_B1s", "Standard_B2s"]}},
        {"provider": "gcp", "service": "compute", "region": "us-central1", "data": {"machines": ["e2-micro", "e2-small"]}}
    ]
    
    # Cache some data
    for item in test_data:
        success = await cache_manager.intelligent_set(
            item["provider"], 
            item["service"], 
            item["region"], 
            item["data"]
        )
        print(f"   ✓ Cached {item['provider']} {item['service']} data: {'Success' if success else 'Failed'}")
    
    # Retrieve cached data
    print("\n🔍 Testing cache retrieval...")
    for item in test_data:
        cached_data = await cache_manager.intelligent_get(
            item["provider"], 
            item["service"], 
            item["region"]
        )
        status = "Hit" if cached_data else "Miss"
        print(f"   • {item['provider']} {item['service']}: Cache {status}")
    
    # Warm cache with additional data
    print("\n🔥 Testing cache warming...")
    warmup_data = [
        {"provider": "aws", "service": "rds", "region": "us-east-1", "data": {"engines": ["mysql", "postgres"]}},
        {"provider": "aws", "service": "lambda", "region": "us-east-1", "data": {"runtimes": ["python3.9", "nodejs18"]}}
    ]
    
    warm_result = await cache_manager.warm_cache(warmup_data)
    print(f"   ✓ Cache warming completed: {warm_result['warmed_count']}/{warm_result['total_items']} items")
    
    # Get performance report
    print("\n📊 Cache Performance Report:")
    cache_report = await cache_manager.get_cache_performance_report()
    
    if "summary" in cache_report:
        summary = cache_report["summary"]
        print(f"   • Total operations: {summary['total_operations']}")
        print(f"   • Hit rate: {summary['hit_rate_percent']:.1f}%")
        print(f"   • Average response time: {summary['avg_response_time_ms']:.2f}ms")
        print(f"   • Prefetch queue size: {summary['prefetch_queue_size']}")
    
    # Cancel prefetch worker
    prefetch_task.cancel()
    try:
        await prefetch_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Advanced caching demo completed")


async def demo_llm_optimization():
    """Demonstrate LLM prompt optimization."""
    print("\n" + "="*60)
    print("🤖 LLM PROMPT OPTIMIZATION DEMO")
    print("="*60)
    
    llm_optimizer = LLMPromptOptimizer()
    
    # Test prompts for different agents
    test_prompts = [
        {
            "agent": "cto_agent",
            "prompt": """
            Please analyze the following business requirements and provide strategic recommendations 
            for AI infrastructure planning. I would like you to consider the following factors:
            
            1. The company size is mid-size with 500 employees
            2. They are in the healthcare industry
            3. Budget range is $100,000 to $500,000 annually
            4. They need HIPAA compliance
            5. Current infrastructure is mostly on-premises
            
            For example, you should consider cloud migration strategies, compliance requirements,
            cost optimization opportunities, and scalability planning. Please provide detailed
            recommendations with clear justifications for each suggestion.
            """
        },
        {
            "agent": "cloud_engineer_agent",
            "prompt": """
            Could you please help me select the most appropriate cloud services for a machine learning
            workload? I would like you to analyze AWS, Azure, and GCP options and provide recommendations.
            
            The requirements are:
            - GPU compute for model training
            - Managed database for storing training data
            - Container orchestration for model deployment
            - Monitoring and logging capabilities
            
            Please provide a detailed comparison with pros and cons for each cloud provider.
            """
        },
        {
            "agent": "research_agent",
            "prompt": """
            Please research the current pricing and capabilities of cloud AI services across major providers.
            I need comprehensive information about:
            
            1. Machine learning platforms (AWS SageMaker, Azure ML, Google AI Platform)
            2. Current pricing models and cost structures
            3. Available GPU instances and their specifications
            4. Managed database options for ML workloads
            5. Recent updates and new service announcements
            
            Please gather the most up-to-date information and present it in a structured format.
            """
        }
    ]
    
    print("✂️  Optimizing prompts for token efficiency...")
    
    total_original_tokens = 0
    total_optimized_tokens = 0
    
    for prompt_data in test_prompts:
        agent_name = prompt_data["agent"]
        original_prompt = prompt_data["prompt"]
        
        optimized_prompt, metrics = llm_optimizer.optimize_prompt(agent_name, original_prompt)
        
        total_original_tokens += metrics["original_tokens"]
        total_optimized_tokens += metrics["optimized_tokens"]
        
        print(f"\n📝 {agent_name}:")
        print(f"   • Original tokens: {metrics['original_tokens']}")
        print(f"   • Optimized tokens: {metrics['optimized_tokens']}")
        print(f"   • Compression ratio: {metrics['compression_ratio']:.1f}%")
        print(f"   • Cost savings: {metrics['cost_savings_percent']:.1f}%")
        print(f"   • Estimated savings: ${metrics['estimated_cost_savings']:.4f}")
    
    # Get optimization report
    print("\n📊 LLM Optimization Report:")
    opt_report = llm_optimizer.get_optimization_report()
    
    if "summary" in opt_report:
        summary = opt_report["summary"]
        print(f"   • Total optimizations: {summary['total_optimizations']}")
        print(f"   • Total original tokens: {summary['total_original_tokens']:,}")
        print(f"   • Total optimized tokens: {summary['total_optimized_tokens']:,}")
        print(f"   • Overall compression: {summary['overall_compression_ratio']:.1f}%")
        print(f"   • Total cost savings: ${summary['estimated_total_cost_savings']:.4f}")
        print(f"   • Average quality score: {summary['avg_quality_score']:.2f}")
    
    print("✅ LLM optimization demo completed")


async def demo_horizontal_scaling():
    """Demonstrate horizontal scaling capabilities."""
    print("\n" + "="*60)
    print("📈 HORIZONTAL SCALING DEMO")
    print("="*60)
    
    scaling_manager = HorizontalScalingManager()
    
    # Mock agent factory
    class MockAgent:
        def __init__(self, agent_type: str):
            self.agent_type = agent_type
            self.is_busy = False
            self.created_at = datetime.utcnow()
        
        async def cleanup(self):
            pass
    
    def create_cto_agent():
        return MockAgent("cto_agent")
    
    def create_research_agent():
        return MockAgent("research_agent")
    
    # Register agent types
    print("🔧 Registering agent types...")
    
    scaling_manager.register_agent_type("cto_agent", create_cto_agent, {
        "min_instances": 2,
        "max_instances": 8,
        "scale_up_threshold": 75,
        "scale_down_threshold": 25
    })
    
    scaling_manager.register_agent_type("research_agent", create_research_agent, {
        "min_instances": 1,
        "max_instances": 5,
        "scale_up_threshold": 80,
        "scale_down_threshold": 20
    })
    
    print("   ✓ Registered CTO agent type")
    print("   ✓ Registered Research agent type")
    
    # Test agent allocation
    print("\n🎯 Testing agent allocation...")
    
    # Get some agents
    agents_in_use = []
    for i in range(3):
        agent = await scaling_manager.get_available_agent("cto_agent")
        if agent:
            agent.is_busy = True
            agents_in_use.append(("cto_agent", agent))
            print(f"   ✓ Allocated CTO agent #{i+1}")
        else:
            print(f"   ❌ Failed to allocate CTO agent #{i+1}")
    
    # Simulate load and scaling
    print("\n⚖️  Simulating load and auto-scaling...")
    
    # Return some agents to simulate load reduction
    for agent_type, agent in agents_in_use[:2]:
        scaling_manager.return_agent(agent_type, agent)
        print(f"   ↩️  Returned {agent_type} agent")
    
    # Perform auto-scaling
    scaling_actions = await scaling_manager.auto_scale_all()
    
    print("\n📊 Auto-scaling results:")
    for agent_type, action_data in scaling_actions.items():
        actions = action_data["actions"]
        current_instances = action_data["current_instances"]
        current_load = action_data["current_load"]
        
        print(f"   • {agent_type}:")
        print(f"     - Actions: {', '.join(actions)}")
        print(f"     - Instances: {current_instances}")
        print(f"     - Load: {current_load:.1f}%")
    
    # Get scaling status
    print("\n📈 Current Scaling Status:")
    status = scaling_manager.get_scaling_status()
    
    for agent_type, agent_status in status.items():
        print(f"   • {agent_type}:")
        print(f"     - Current: {agent_status['current_instances']}")
        print(f"     - Min/Max: {agent_status['min_instances']}/{agent_status['max_instances']}")
        print(f"     - Load: {agent_status['current_load_percent']:.1f}%")
        print(f"     - Busy: {agent_status['busy_instances']}")
    
    print("✅ Horizontal scaling demo completed")


async def demo_comprehensive_performance_report():
    """Demonstrate comprehensive performance reporting."""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE PERFORMANCE REPORT")
    print("="*60)
    
    print("🔄 Generating comprehensive performance report...")
    
    # Get comprehensive report
    report = await performance_optimizer.get_comprehensive_performance_report()
    
    if "error" in report:
        print(f"   ❌ Error generating report: {report['error']}")
        return
    
    # System resources
    if "system_resources" in report:
        resources = report["system_resources"]
        print(f"\n💻 System Resources:")
        print(f"   • CPU Usage: {resources['cpu_usage_percent']:.1f}%")
        print(f"   • Memory Usage: {resources['memory_usage_percent']:.1f}%")
        print(f"   • Disk Usage: {resources['disk_usage_percent']:.1f}%")
        print(f"   • Available Memory: {resources['available_memory_gb']:.1f} GB")
    
    # Database performance
    if "database_performance" in report:
        db_perf = report["database_performance"]
        if "summary" in db_perf:
            summary = db_perf["summary"]
            print(f"\n🗄️  Database Performance:")
            print(f"   • Total Queries: {summary['total_queries']}")
            print(f"   • Avg Response Time: {summary['avg_execution_time_ms']:.2f}ms")
            print(f"   • Slow Query Rate: {summary['slow_query_rate']:.1f}%")
    
    # Cache performance
    if "cache_performance" in report:
        cache_perf = report["cache_performance"]
        if "summary" in cache_perf:
            summary = cache_perf["summary"]
            print(f"\n🚀 Cache Performance:")
            print(f"   • Total Operations: {summary['total_operations']}")
            print(f"   • Hit Rate: {summary['hit_rate_percent']:.1f}%")
            print(f"   • Avg Response Time: {summary['avg_response_time_ms']:.2f}ms")
    
    # LLM optimization
    if "llm_optimization" in report:
        llm_opt = report["llm_optimization"]
        if "summary" in llm_opt:
            summary = llm_opt["summary"]
            print(f"\n🤖 LLM Optimization:")
            print(f"   • Total Optimizations: {summary['total_optimizations']}")
            print(f"   • Compression Ratio: {summary['overall_compression_ratio']:.1f}%")
            print(f"   • Cost Savings: ${summary['estimated_total_cost_savings']:.4f}")
    
    # Scaling status
    if "scaling_status" in report:
        scaling = report["scaling_status"]
        print(f"\n📈 Scaling Status:")
        for agent_type, status in scaling.items():
            print(f"   • {agent_type}: {status['current_instances']} instances ({status['current_load_percent']:.1f}% load)")
    
    # Optimization recommendations
    if "optimization_recommendations" in report:
        recommendations = report["optimization_recommendations"]
        if recommendations:
            print(f"\n💡 Optimization Recommendations:")
            for rec in recommendations[:5]:  # Show top 5
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                print(f"   {priority_icon} {rec['category']}: {rec['issue']}")
                print(f"      → {rec['recommendation']}")
        else:
            print(f"\n✅ No optimization recommendations at this time")
    
    print("\n✅ Comprehensive performance report completed")


async def main():
    """Run all performance optimization demos."""
    print("🚀 INFRA MIND PERFORMANCE OPTIMIZATION DEMO")
    print("=" * 80)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        await init_cache()
        await init_database()
        await initialize_metrics_collection()
        await performance_optimizer.start_optimization_services()
        
        # Run demos
        await demo_database_optimization()
        await demo_advanced_caching()
        await demo_llm_optimization()
        await demo_horizontal_scaling()
        await demo_comprehensive_performance_report()
        
        print("\n" + "="*80)
        print("🎉 ALL PERFORMANCE OPTIMIZATION DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")
    
    finally:
        # Cleanup
        try:
            await performance_optimizer.stop_optimization_services()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())