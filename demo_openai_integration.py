#!/usr/bin/env python3
"""
Demo script for OpenAI LLM integration.

This script demonstrates the real OpenAI API integration with
token usage tracking, cost monitoring, and response validation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.llm.openai_provider import OpenAIProvider
from infra_mind.llm.manager import LLMManager
from infra_mind.llm.interface import LLMRequest
from infra_mind.llm.cost_tracker import CostTracker, BudgetAlert, CostPeriod
from infra_mind.llm.response_validator import ResponseValidator
from infra_mind.agents.cto_agent import CTOAgent
from infra_mind.agents.base import AgentConfig, AgentRole
from infra_mind.models.assessment import Assessment


async def demo_openai_provider():
    """Demonstrate OpenAI provider functionality."""
    print("🤖 OpenAI Provider Demo")
    print("=" * 50)
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize provider
        provider = OpenAIProvider(
            api_key=api_key,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )
        
        print(f"✅ Initialized OpenAI provider with model: {provider.model}")
        print(f"📊 Supported models: {', '.join(provider.supported_models[:3])}...")
        
        # Test API key validation
        print("\n🔑 Testing API key validation...")
        is_valid = await provider.validate_api_key()
        print(f"API key valid: {'✅ Yes' if is_valid else '❌ No'}")
        
        if not is_valid:
            print("❌ Invalid API key - cannot proceed with demo")
            return
        
        # Test response generation
        print("\n💬 Testing response generation...")
        request = LLMRequest(
            prompt="Explain the benefits of cloud computing in 2-3 sentences.",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )
        
        response = await provider.generate_response(request)
        
        print(f"📝 Response: {response.content}")
        print(f"🔢 Tokens used: {response.token_usage.total_tokens}")
        print(f"💰 Estimated cost: ${response.token_usage.estimated_cost:.4f}")
        print(f"⏱️  Response time: {response.response_time:.2f}s")
        
        # Test cost estimation
        print("\n💰 Testing cost estimation...")
        cost_gpt35 = provider.estimate_cost(1000, 500, "gpt-3.5-turbo")
        cost_gpt4 = provider.estimate_cost(1000, 500, "gpt-4")
        
        print(f"GPT-3.5-turbo (1000+500 tokens): ${cost_gpt35:.4f}")
        print(f"GPT-4 (1000+500 tokens): ${cost_gpt4:.4f}")
        print(f"GPT-4 is {cost_gpt4/cost_gpt35:.1f}x more expensive")
        
        # Get usage statistics
        print("\n📈 Usage statistics:")
        stats = provider.get_usage_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Total cost: ${stats['total_cost']:.4f}")
        
    except Exception as e:
        print(f"❌ Error in OpenAI provider demo: {str(e)}")


async def demo_llm_manager():
    """Demonstrate LLM manager functionality."""
    print("\n🎯 LLM Manager Demo")
    print("=" * 50)
    
    try:
        # Initialize manager
        manager = LLMManager()
        
        print(f"✅ Initialized LLM manager")
        
        # Get provider statistics
        stats = manager.get_provider_stats()
        print(f"📊 Total providers: {stats['total_providers']}")
        print(f"🟢 Healthy providers: {stats['healthy_providers']}")
        print(f"⚖️  Load balancing: {stats['load_balancing_strategy']}")
        
        # Test response generation with validation
        print("\n💬 Testing managed response generation...")
        request = LLMRequest(
            prompt="As a CTO, what are the top 3 considerations for cloud migration?",
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=200
        )
        
        response = await manager.generate_response(
            request, 
            validate_response=True,
            agent_name="CTO Agent"
        )
        
        print(f"📝 Response: {response.content}")
        print(f"🔢 Tokens: {response.token_usage.total_tokens}")
        print(f"💰 Cost: ${response.token_usage.estimated_cost:.4f}")
        
        # Check validation results
        validation = response.metadata.get("validation", {})
        print(f"✅ Valid response: {validation.get('is_valid', False)}")
        print(f"⭐ Quality score: {validation.get('quality_score', 0):.2f}")
        
        if validation.get('issues'):
            print("⚠️  Validation issues:")
            for issue in validation['issues'][:3]:  # Show first 3 issues
                print(f"  - {issue['severity']}: {issue['message']}")
        
    except Exception as e:
        print(f"❌ Error in LLM manager demo: {str(e)}")


async def demo_cost_tracking():
    """Demonstrate cost tracking functionality."""
    print("\n💰 Cost Tracking Demo")
    print("=" * 50)
    
    try:
        # Initialize cost tracker
        tracker = CostTracker()
        
        # Set up budget alerts
        daily_alert = BudgetAlert(
            name="Daily Budget Alert",
            threshold_percentage=0.8,  # 80% of budget
            period=CostPeriod.DAILY,
            budget_amount=5.0  # $5 daily budget
        )
        tracker.add_budget_alert(daily_alert)
        
        # Simulate some usage
        from infra_mind.llm.interface import TokenUsage, LLMProvider
        
        print("📊 Simulating LLM usage...")
        for i in range(5):
            token_usage = TokenUsage(
                prompt_tokens=100 + i * 20,
                completion_tokens=50 + i * 10,
                total_tokens=150 + i * 30,
                estimated_cost=0.001 + i * 0.0005,
                model="gpt-3.5-turbo",
                provider=LLMProvider.OPENAI
            )
            
            tracker.track_usage(token_usage, f"agent_{i}", f"request_{i}")
        
        # Get cost summary
        daily_summary = tracker.get_cost_summary(CostPeriod.DAILY)
        print(f"📈 Daily summary:")
        print(f"  Total cost: ${daily_summary.total_cost:.4f}")
        print(f"  Total tokens: {daily_summary.total_tokens}")
        print(f"  Total requests: {daily_summary.total_requests}")
        print(f"  Avg cost/request: ${daily_summary.total_cost/daily_summary.total_requests:.4f}")
        
        # Get top cost drivers
        cost_drivers = tracker.get_top_cost_drivers(CostPeriod.DAILY, limit=3)
        print(f"\n🔝 Top cost drivers:")
        for provider in cost_drivers['providers']:
            print(f"  Provider {provider['name']}: ${provider['cost']:.4f}")
        
        # Get optimization recommendations
        recommendations = tracker.get_cost_optimization_recommendations()
        print(f"\n💡 Optimization recommendations: {len(recommendations)}")
        for rec in recommendations[:2]:  # Show first 2
            print(f"  - {rec['title']} (Priority: {rec['priority']})")
        
    except Exception as e:
        print(f"❌ Error in cost tracking demo: {str(e)}")


async def demo_response_validation():
    """Demonstrate response validation functionality."""
    print("\n✅ Response Validation Demo")
    print("=" * 50)
    
    try:
        # Initialize validator
        validator = ResponseValidator({
            "min_length": 20,
            "max_length": 1000,
            "check_profanity": True,
            "check_safety": True
        })
        
        # Test different response types
        from infra_mind.llm.interface import LLMResponse, TokenUsage, LLMProvider
        
        test_responses = [
            {
                "name": "Good Response",
                "content": "Cloud computing offers significant benefits including cost savings, scalability, and improved reliability. Organizations can reduce infrastructure costs while gaining access to enterprise-grade services.",
                "context": {"agent_name": "CTO Agent"}
            },
            {
                "name": "Short Response",
                "content": "Yes.",
                "context": {}
            },
            {
                "name": "Technical Response",
                "content": "AWS EC2 instances provide scalable compute capacity. You can configure auto-scaling groups with load balancers for high availability.",
                "context": {"agent_name": "Cloud Engineer Agent"}
            }
        ]
        
        for test in test_responses:
            print(f"\n🧪 Testing: {test['name']}")
            
            response = LLMResponse(
                content=test["content"],
                model="gpt-3.5-turbo",
                provider=LLMProvider.OPENAI,
                token_usage=TokenUsage(10, 15, 25, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
                response_time=1.0
            )
            
            result = validator.validate_response(response, test["context"])
            
            print(f"  ✅ Valid: {result.is_valid}")
            print(f"  ⭐ Quality: {result.quality_score:.2f}")
            print(f"  ⚠️  Issues: {len(result.issues)}")
            
            if result.issues:
                for issue in result.issues[:2]:  # Show first 2 issues
                    print(f"    - {issue.severity.value}: {issue.message}")
        
        # Show validator statistics
        stats = validator.get_validation_stats()
        print(f"\n📊 Validator configuration:")
        print(f"  Min length: {stats['config']['min_length']}")
        print(f"  Max length: {stats['config']['max_length']}")
        print(f"  Safety checks: {stats['config']['check_safety']}")
        
    except Exception as e:
        print(f"❌ Error in response validation demo: {str(e)}")


async def demo_agent_integration():
    """Demonstrate agent integration with real LLM."""
    print("\n🤖 Agent Integration Demo")
    print("=" * 50)
    
    try:
        # Create a sample assessment
        assessment = Assessment(
            user_id="demo_user",
            title="Demo Assessment",
            business_requirements={
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "$50k-100k",
                "primary_goals": ["scalability", "cost_reduction"],
                "timeline": "6 months"
            },
            technical_requirements={
                "workload_types": ["web_application", "ai_ml"],
                "expected_users": 5000,
                "data_sensitivity": "medium",
                "performance_requirements": ["high_availability", "low_latency"]
            }
        )
        
        # Initialize CTO agent with real LLM
        config = AgentConfig(
            name="CTO Agent Demo",
            role=AgentRole.CTO,
            temperature=0.1,
            max_tokens=300
        )
        
        cto_agent = CTOAgent(config)
        
        print("🎯 Running CTO Agent with real LLM...")
        print("📋 Assessment context:")
        print(f"  Company: {assessment.business_requirements['company_size']} {assessment.business_requirements['industry']}")
        print(f"  Budget: {assessment.business_requirements['budget_range']}")
        print(f"  Users: {assessment.technical_requirements['expected_users']:,}")
        
        # Execute agent
        result = await cto_agent.execute(assessment)
        
        print(f"\n📊 Agent execution results:")
        print(f"  Status: {result.status.value}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        print(f"  Recommendations: {len(result.recommendations)}")
        
        if result.recommendations:
            print(f"\n💡 Sample recommendations:")
            for i, rec in enumerate(result.recommendations[:2], 1):
                print(f"  {i}. {rec.get('title', 'Recommendation')}")
                print(f"     Priority: {rec.get('priority', 'N/A')}")
        
        # Show metrics if available
        if result.metrics:
            metrics = result.metrics
            if 'llm_tokens_used' in metrics:
                print(f"\n📈 LLM Usage:")
                print(f"  Tokens used: {metrics.get('llm_tokens_used', 0)}")
                print(f"  Cost: ${metrics.get('llm_cost', 0):.4f}")
                print(f"  Requests: {metrics.get('llm_requests', 0)}")
        
    except Exception as e:
        print(f"❌ Error in agent integration demo: {str(e)}")


async def main():
    """Run all demos."""
    print("🚀 OpenAI Integration Demo Suite")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("Some demos will be skipped or use mock data")
        print("\nTo run with real OpenAI API:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("python demo_openai_integration.py")
        print()
    
    try:
        # Run demos
        await demo_openai_provider()
        await demo_llm_manager()
        await demo_cost_tracking()
        await demo_response_validation()
        await demo_agent_integration()
        
        print("\n🎉 Demo completed successfully!")
        print("\n📚 Next steps:")
        print("1. Set up your OpenAI API key for real testing")
        print("2. Run the test suite: python -m pytest tests/test_openai_integration.py")
        print("3. Monitor costs using the cost tracking features")
        print("4. Customize validation rules for your use case")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())