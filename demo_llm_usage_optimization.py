#!/usr/bin/env python3
"""
Demo script for LLM Usage Optimization features.

This script demonstrates the comprehensive LLM usage optimization system including:
- Prompt engineering optimization for cost reduction
- Response caching for similar queries
- Token usage limits and budget controls
- Usage pattern analysis and recommendations
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.llm.manager import LLMManager
from src.infra_mind.llm.interface import LLMRequest, LLMProvider
from src.infra_mind.llm.usage_optimizer import OptimizationStrategy, UsageLimits
from src.infra_mind.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMOptimizationDemo:
    """Demo class for LLM usage optimization features."""
    
    def __init__(self):
        """Initialize the demo."""
        self.settings = get_settings()
        
        # Initialize LLM manager with optimization enabled
        manager_config = {
            "optimization_strategy": "balanced",
            "usage_limits": {
                "daily_token_limit": 50000,
                "daily_budget_limit": 10.0,
                "per_request_token_limit": 2000,
                "per_agent_daily_limit": 10000
            },
            "validation": {
                "enable_quality_checks": True,
                "min_response_length": 10
            }
        }
        
        self.llm_manager = LLMManager(config=manager_config)
    
    async def run_demo(self):
        """Run the complete optimization demo."""
        print("🚀 LLM Usage Optimization Demo")
        print("=" * 50)
        
        try:
            # Demo 1: Prompt optimization
            await self.demo_prompt_optimization()
            
            # Demo 2: Response caching
            await self.demo_response_caching()
            
            # Demo 3: Usage limits and budget controls
            await self.demo_usage_limits()
            
            # Demo 4: Optimization strategies
            await self.demo_optimization_strategies()
            
            # Demo 5: Custom optimization rules
            await self.demo_custom_optimization_rules()
            
            # Demo 6: Usage analytics and recommendations
            await self.demo_usage_analytics()
            
            print("\n✅ Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")
    
    async def demo_prompt_optimization(self):
        """Demonstrate prompt optimization for cost reduction."""
        print("\n📝 Demo 1: Prompt Optimization for Cost Reduction")
        print("-" * 50)
        
        # Test prompts with different complexity levels
        test_prompts = [
            {
                "prompt": "Please kindly provide me with a very detailed and comprehensive list of all the AWS services that are actually available in the us-east-1 region, and please make sure to include all the pricing information as well.",
                "description": "Verbose prompt with redundant words",
                "agent": "cloud_engineer_agent"
            },
            {
                "prompt": "List AWS services in us-east-1 with pricing",
                "description": "Already optimized prompt",
                "agent": "cloud_engineer_agent"
            },
            {
                "prompt": "Analyze the comprehensive security implications and provide detailed recommendations for implementing a multi-cloud infrastructure strategy across AWS, Azure, and GCP for a financial services company with strict compliance requirements.",
                "description": "Complex prompt (minimal optimization)",
                "agent": "cto_agent"
            },
            {
                "prompt": "CRITICAL: Production system down - need immediate troubleshooting steps for database connection failure",
                "description": "Critical prompt (no optimization)",
                "agent": "infrastructure_agent"
            }
        ]
        
        for i, test_case in enumerate(test_prompts, 1):
            print(f"\n{i}. Testing: {test_case['description']}")
            print(f"   Agent: {test_case['agent']}")
            print(f"   Original: {test_case['prompt'][:100]}...")
            
            # Create request
            request = LLMRequest(
                prompt=test_case["prompt"],
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000,
                agent_name=test_case["agent"]
            )
            
            try:
                # Get optimization stats before
                stats_before = self.llm_manager.get_optimization_stats()
                
                # Generate response (this will apply optimizations)
                response = await self.llm_manager.generate_response(
                    request, 
                    validate_response=False,  # Skip validation for demo
                    enable_optimization=True
                )
                
                # Get optimization metadata
                optimization_data = response.metadata.get("optimization", {})
                
                if optimization_data.get("optimizations_applied"):
                    print(f"   ✅ Optimizations applied: {len(optimization_data['optimizations_applied'])}")
                    print(f"   💰 Tokens saved: {optimization_data.get('tokens_saved', 0)}")
                    print(f"   💵 Estimated cost savings: ${optimization_data.get('estimated_cost_savings', 0):.4f}")
                    
                    # Show specific optimizations
                    for opt in optimization_data["optimizations_applied"][:3]:  # Show first 3
                        print(f"      - {opt.get('rule', opt.get('type', 'Unknown'))}")
                else:
                    print(f"   ℹ️  No optimizations applied (complexity: {optimization_data.get('complexity', 'unknown')})")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    async def demo_response_caching(self):
        """Demonstrate response caching for similar queries."""
        print("\n💾 Demo 2: Response Caching for Similar Queries")
        print("-" * 50)
        
        # Test similar queries that should hit cache
        similar_queries = [
            "What are the main AWS compute services?",
            "List the primary AWS compute services",
            "Show me AWS compute service options",
            "What compute services does AWS offer?"
        ]
        
        print("Testing cache behavior with similar queries...")
        
        for i, query in enumerate(similar_queries, 1):
            print(f"\n{i}. Query: {query}")
            
            request = LLMRequest(
                prompt=query,
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=500,
                agent_name="cloud_engineer_agent"
            )
            
            try:
                start_time = datetime.now(timezone.utc)
                
                response = await self.llm_manager.generate_response(
                    request,
                    validate_response=False,
                    enable_optimization=True
                )
                
                response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                
                # Check if it was a cache hit
                cache_hit = response.metadata.get("cache_hit", False)
                optimization_data = response.metadata.get("optimization", {})
                
                if cache_hit:
                    print(f"   ✅ Cache HIT! Response time: {response_time:.2f}ms")
                else:
                    print(f"   ❌ Cache MISS. Response time: {response_time:.2f}ms")
                
                # Show cache stats
                if i == len(similar_queries):
                    cache_stats = self.llm_manager.get_optimization_stats()["cache_stats"]
                    print(f"\n📊 Final Cache Statistics:")
                    print(f"   Total entries: {cache_stats['total_entries']}")
                    print(f"   Total hits: {cache_stats['total_hits']}")
                    print(f"   Cache size: {cache_stats['cache_size_mb']:.2f} MB")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    async def demo_usage_limits(self):
        """Demonstrate usage limits and budget controls."""
        print("\n🚦 Demo 3: Usage Limits and Budget Controls")
        print("-" * 50)
        
        # Set strict limits for demo
        strict_limits = {
            "daily_token_limit": 1000,  # Very low for demo
            "daily_budget_limit": 0.50,  # $0.50 daily limit
            "per_request_token_limit": 200,
            "per_agent_daily_limit": 300
        }
        
        print("Setting strict usage limits for demonstration:")
        for key, value in strict_limits.items():
            print(f"   {key}: {value}")
        
        self.llm_manager.set_usage_limits(strict_limits)
        
        # Test requests that should hit limits
        test_requests = [
            {
                "prompt": "Generate a comprehensive 5000-word analysis of cloud computing trends",
                "max_tokens": 2000,  # Exceeds per_request_token_limit
                "agent": "research_agent",
                "description": "Request exceeding per-request token limit"
            },
            {
                "prompt": "List top 5 AWS services",
                "max_tokens": 100,
                "agent": "cloud_engineer_agent",
                "description": "Normal request within limits"
            }
        ]
        
        for i, test_case in enumerate(test_requests, 1):
            print(f"\n{i}. Testing: {test_case['description']}")
            
            request = LLMRequest(
                prompt=test_case["prompt"],
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=test_case["max_tokens"],
                agent_name=test_case["agent"]
            )
            
            try:
                response = await self.llm_manager.generate_response(
                    request,
                    validate_response=False,
                    enable_optimization=True
                )
                
                optimization_data = response.metadata.get("optimization", {})
                token_optimization = None
                
                for opt in optimization_data.get("optimizations_applied", []):
                    if opt.get("type") == "token_limit_optimization":
                        token_optimization = opt
                        break
                
                if token_optimization:
                    print(f"   ✅ Token limit applied: {token_optimization['optimized_max_tokens']} tokens")
                    print(f"   📉 Reduced from: {token_optimization['original_max_tokens']} tokens")
                else:
                    print(f"   ✅ Request processed normally")
                
            except ValueError as e:
                if "Usage limits exceeded" in str(e):
                    print(f"   🚫 Request blocked: Usage limits exceeded")
                else:
                    print(f"   ❌ Error: {e}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Show current usage
        stats = self.llm_manager.get_optimization_stats()
        current_usage = stats.get("current_usage", {})
        print(f"\n📊 Current Usage:")
        print(f"   Daily tokens: {current_usage.get('daily_tokens', 0)}")
        print(f"   Daily cost: ${current_usage.get('daily_cost', 0):.4f}")
    
    async def demo_optimization_strategies(self):
        """Demonstrate different optimization strategies."""
        print("\n⚙️ Demo 4: Optimization Strategies")
        print("-" * 50)
        
        strategies = ["conservative", "balanced", "aggressive"]
        test_prompt = "Please provide me with a very comprehensive and detailed analysis of the current cloud computing market trends and please include all the major providers like AWS, Azure, and GCP with their respective market shares and competitive advantages."
        
        for strategy in strategies:
            print(f"\n🔧 Testing {strategy.upper()} strategy:")
            
            # Set strategy
            self.llm_manager.set_optimization_strategy(strategy)
            
            request = LLMRequest(
                prompt=test_prompt,
                model="gpt-4",  # Expensive model to test optimization
                temperature=0.7,
                max_tokens=1500,
                agent_name="research_agent"
            )
            
            try:
                response = await self.llm_manager.generate_response(
                    request,
                    validate_response=False,
                    enable_optimization=True
                )
                
                optimization_data = response.metadata.get("optimization", {})
                
                print(f"   Optimizations applied: {len(optimization_data.get('optimizations_applied', []))}")
                print(f"   Tokens saved: {optimization_data.get('tokens_saved', 0)}")
                print(f"   Model used: {response.metadata.get('model', 'unknown')}")
                
                # Show model optimization if applied
                for opt in optimization_data.get("optimizations_applied", []):
                    if opt.get("type") == "model_optimization":
                        print(f"   Model optimized: {opt['original_model']} → {opt['optimized_model']}")
                        print(f"   Estimated savings: {opt['estimated_cost_savings_percentage']:.1f}%")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    async def demo_custom_optimization_rules(self):
        """Demonstrate adding custom optimization rules."""
        print("\n🛠️ Demo 5: Custom Optimization Rules")
        print("-" * 50)
        
        # Add custom optimization rules
        custom_rules = [
            {
                "name": "remove_cloud_redundancy",
                "pattern": r"\bcloud computing\b",
                "replacement": "cloud",
                "token_savings": 1,
                "quality_impact": 0.0,
                "enabled": True
            },
            {
                "name": "abbreviate_infrastructure",
                "pattern": r"\binfrastructure\b",
                "replacement": "infra",
                "token_savings": 1,
                "quality_impact": 0.1,
                "enabled": True
            }
        ]
        
        print("Adding custom optimization rules:")
        for rule in custom_rules:
            print(f"   - {rule['name']}: '{rule['pattern']}' → '{rule['replacement']}'")
            self.llm_manager.add_optimization_rule(rule)
        
        # Test with prompt that should trigger custom rules
        test_prompt = "Explain cloud computing infrastructure best practices for cloud computing deployments in modern infrastructure environments."
        
        print(f"\nTesting with prompt: {test_prompt}")
        
        request = LLMRequest(
            prompt=test_prompt,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500,
            agent_name="infrastructure_agent"
        )
        
        try:
            response = await self.llm_manager.generate_response(
                request,
                validate_response=False,
                enable_optimization=True
            )
            
            optimization_data = response.metadata.get("optimization", {})
            
            print(f"\nOptimization results:")
            print(f"   Total optimizations: {len(optimization_data.get('optimizations_applied', []))}")
            
            # Show which custom rules were applied
            custom_rules_applied = [
                opt for opt in optimization_data.get("optimizations_applied", [])
                if opt.get("rule") in ["remove_cloud_redundancy", "abbreviate_infrastructure"]
            ]
            
            if custom_rules_applied:
                print(f"   Custom rules applied: {len(custom_rules_applied)}")
                for rule in custom_rules_applied:
                    print(f"      - {rule['rule']}")
            else:
                print("   No custom rules were triggered")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def demo_usage_analytics(self):
        """Demonstrate usage analytics and recommendations."""
        print("\n📊 Demo 6: Usage Analytics and Recommendations")
        print("-" * 50)
        
        # Get comprehensive optimization statistics
        stats = self.llm_manager.get_optimization_stats()
        
        print("📈 Optimization Performance Metrics:")
        metrics = stats.get("metrics", {})
        print(f"   Total requests: {metrics.get('total_requests', 0)}")
        print(f"   Optimized requests: {metrics.get('optimized_requests', 0)}")
        print(f"   Optimization rate: {metrics.get('optimization_rate', 0):.1f}%")
        print(f"   Cache hit rate: {metrics.get('cache_hit_rate', 0):.1f}%")
        print(f"   Total tokens saved: {metrics.get('tokens_saved', 0)}")
        print(f"   Total cost saved: ${metrics.get('cost_saved', 0):.4f}")
        print(f"   Avg optimization time: {metrics.get('avg_optimization_time_ms', 0):.2f}ms")
        
        print("\n💾 Cache Statistics:")
        cache_stats = stats.get("cache_stats", {})
        print(f"   Total entries: {cache_stats.get('total_entries', 0)}")
        print(f"   Valid entries: {cache_stats.get('valid_entries', 0)}")
        print(f"   Total hits: {cache_stats.get('total_hits', 0)}")
        print(f"   Cache size: {cache_stats.get('cache_size_mb', 0):.2f} MB")
        
        print("\n🎯 Current Usage Limits:")
        usage_limits = stats.get("usage_limits", {})
        for key, value in usage_limits.items():
            if value is not None:
                print(f"   {key}: {value}")
        
        print("\n📋 Active Optimization Rules:")
        rules = stats.get("optimization_rules", [])
        enabled_rules = [rule for rule in rules if rule["enabled"]]
        print(f"   Total rules: {len(rules)} ({len(enabled_rules)} enabled)")
        
        for rule in enabled_rules[:5]:  # Show first 5
            print(f"   - {rule['name']}: saves {rule['token_savings']} tokens")
        
        # Get optimization recommendations
        print("\n💡 Optimization Recommendations:")
        recommendations = self.llm_manager.get_optimization_recommendations()
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n   {i}. {rec['title']} (Priority: {rec['priority']})")
                print(f"      {rec['description']}")
                if rec.get('actions'):
                    print(f"      Actions:")
                    for action in rec['actions'][:2]:  # Show first 2 actions
                        print(f"        • {action}")
        else:
            print("   No specific recommendations at this time")
        
        # Show cost optimization recommendations from cost tracker
        print("\n💰 Cost Optimization Recommendations:")
        cost_recommendations = self.llm_manager.get_cost_optimization_recommendations()
        
        if cost_recommendations:
            for i, rec in enumerate(cost_recommendations, 1):
                print(f"\n   {i}. {rec['title']} (Priority: {rec['priority']})")
                print(f"      {rec['description']}")
                print(f"      Potential savings: {rec['potential_savings']}")
        else:
            print("   No cost optimization recommendations available")


async def main():
    """Main demo function."""
    demo = LLMOptimizationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())