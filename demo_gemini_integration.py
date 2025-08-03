#!/usr/bin/env python3
"""
Demo script for Gemini 2.5 Pro API integration and cost comparison.

This script demonstrates:
1. Gemini provider initialization and testing
2. Cost comparison between OpenAI and Gemini
3. Provider switching and failover scenarios
4. Prompt formatting consistency across providers
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.llm.manager import LLMManager, LoadBalancingStrategy
from infra_mind.llm.interface import LLMRequest, LLMProvider
from infra_mind.llm.gemini_provider import GeminiProvider
from infra_mind.llm.openai_provider import OpenAIProvider
from infra_mind.core.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gemini_provider():
    """Test Gemini provider directly."""
    print("\n" + "="*60)
    print("TESTING GEMINI PROVIDER DIRECTLY")
    print("="*60)
    
    settings = get_settings()
    gemini_key = settings.get_gemini_api_key()
    
    if not gemini_key:
        print("❌ No Gemini API key found. Set INFRA_MIND_GEMINI_API_KEY environment variable.")
        return False
    
    try:
        # Initialize Gemini provider
        gemini_provider = GeminiProvider(
            api_key=gemini_key,
            model="gemini-1.5-pro",
            temperature=0.1
        )
        
        print(f"✅ Gemini provider initialized")
        print(f"   Model: {gemini_provider.model}")
        print(f"   Supported models: {gemini_provider.supported_models}")
        
        # Test API key validation
        print("\n🔑 Testing API key validation...")
        is_valid = await gemini_provider.validate_api_key()
        print(f"   API key valid: {'✅' if is_valid else '❌'}")
        
        if not is_valid:
            return False
        
        # Test connection
        print("\n🔗 Testing connection...")
        connection_test = await gemini_provider.test_connection()
        print(f"   Connection status: {connection_test['overall_status']}")
        
        for test_name, test_result in connection_test['tests'].items():
            status_icon = "✅" if test_result['status'] == 'pass' else "❌"
            print(f"   {test_name}: {status_icon} {test_result['message']}")
        
        # Test simple generation
        print("\n💬 Testing simple generation...")
        test_request = LLMRequest(
            prompt="Explain what cloud infrastructure is in one sentence.",
            model="gemini-1.5-pro",
            temperature=0.1,
            max_tokens=100
        )
        
        response = await gemini_provider.generate_response(test_request)
        print(f"   Response: {response.content[:100]}...")
        print(f"   Tokens used: {response.token_usage.total_tokens}")
        print(f"   Cost: ${response.token_usage.estimated_cost:.6f}")
        print(f"   Response time: {response.response_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini provider test failed: {str(e)}")
        return False


async def test_cost_comparison():
    """Test cost comparison between providers."""
    print("\n" + "="*60)
    print("TESTING COST COMPARISON")
    print("="*60)
    
    try:
        # Initialize LLM manager
        manager = LLMManager({
            "load_balancing": LoadBalancingStrategy.COST_OPTIMIZED.value
        })
        
        if not manager.providers:
            print("❌ No providers available for cost comparison")
            return False
        
        print(f"✅ LLM Manager initialized with {len(manager.providers)} providers:")
        for provider_type in manager.providers.keys():
            print(f"   - {provider_type.value}")
        
        # Test request for cost comparison
        test_request = LLMRequest(
            prompt="""
            Analyze the following infrastructure scenario and provide recommendations:
            
            A mid-sized company is running their applications on a single cloud provider
            and experiencing high costs. They have:
            - 50 virtual machines running 24/7
            - 10TB of data storage
            - High network traffic during business hours
            - Compliance requirements for data security
            
            What are the top 3 cost optimization strategies they should consider?
            """,
            system_prompt="You are an expert cloud infrastructure consultant.",
            temperature=0.1,
            max_tokens=500
        )
        
        print("\n💰 Comparing costs across providers...")
        cost_comparison = await manager.compare_provider_costs(test_request)
        
        print(f"   Request ID: {cost_comparison['request_id']}")
        print(f"   Timestamp: {cost_comparison['timestamp']}")
        
        print("\n📊 Provider Cost Analysis:")
        for provider_name, data in cost_comparison['providers'].items():
            if 'error' in data:
                print(f"   {provider_name}: ❌ {data['error']}")
                continue
            
            print(f"   {provider_name}:")
            print(f"     Model: {data['model']}")
            print(f"     Estimated cost: ${data['estimated_cost']:.6f}")
            print(f"     Estimated tokens: {data['estimated_total_tokens']}")
            print(f"     Performance score: {data['performance_score']:.3f}")
            print(f"     Health: {data['health_status']}")
        
        # Show recommendations
        if 'recommendations' in cost_comparison:
            recs = cost_comparison['recommendations']
            print(f"\n🎯 Recommendations:")
            print(f"   Cheapest provider: {recs.get('cheapest_provider', 'N/A')}")
            print(f"   Cheapest cost: ${recs.get('cheapest_cost', 0):.6f}")
            print(f"   Best value provider: {recs.get('best_value_provider', 'N/A')}")
            
            if 'cost_savings' in recs:
                print(f"\n💡 Potential savings:")
                for provider, savings in recs['cost_savings'].items():
                    print(f"     vs {provider}: ${savings['absolute_savings']:.6f} ({savings['percentage_savings']:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Cost comparison test failed: {str(e)}")
        return False


async def test_provider_switching():
    """Test provider switching and failover."""
    print("\n" + "="*60)
    print("TESTING PROVIDER SWITCHING & FAILOVER")
    print("="*60)
    
    try:
        # Initialize manager with cost optimization
        manager = LLMManager({
            "load_balancing": LoadBalancingStrategy.COST_OPTIMIZED.value
        })
        
        if len(manager.providers) < 2:
            print("⚠️  Need at least 2 providers for switching test")
            return False
        
        test_request = LLMRequest(
            prompt="What are the benefits of multi-cloud architecture?",
            temperature=0.1,
            max_tokens=200
        )
        
        print("🔄 Testing automatic provider selection...")
        
        # Test multiple requests to see provider selection
        for i in range(3):
            print(f"\n   Request {i+1}:")
            
            # Get optimal provider
            optimal_provider = await manager.optimize_provider_selection(test_request)
            print(f"     Optimal provider: {optimal_provider.value}")
            
            # Generate response
            response = await manager.generate_response(
                test_request, 
                agent_name="test_agent"
            )
            
            print(f"     Used provider: {response.provider.value}")
            print(f"     Cost: ${response.token_usage.estimated_cost:.6f}")
            print(f"     Tokens: {response.token_usage.total_tokens}")
            print(f"     Response time: {response.response_time:.2f}s")
            print(f"     Response preview: {response.content[:80]}...")
        
        # Test failover by simulating provider failure
        print("\n🚨 Testing failover scenario...")
        
        # Temporarily mark first provider as unhealthy
        first_provider = list(manager.providers.keys())[0]
        manager._provider_health[first_provider] = False
        print(f"   Marked {first_provider.value} as unhealthy")
        
        # Try request - should use backup provider
        response = await manager.generate_response(
            test_request,
            agent_name="failover_test"
        )
        
        print(f"   Failover successful: Used {response.provider.value}")
        print(f"   Cost: ${response.token_usage.estimated_cost:.6f}")
        
        # Restore provider health
        manager._provider_health[first_provider] = True
        print(f"   Restored {first_provider.value} health")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching test failed: {str(e)}")
        return False


async def test_prompt_formatting():
    """Test consistent prompt formatting across providers."""
    print("\n" + "="*60)
    print("TESTING PROMPT FORMATTING CONSISTENCY")
    print("="*60)
    
    try:
        manager = LLMManager()
        
        if not manager.providers:
            print("❌ No providers available for formatting test")
            return False
        
        # Test request with system prompt
        test_request = LLMRequest(
            prompt="List 3 key benefits of containerization.",
            system_prompt="You are a DevOps expert. Provide concise, technical answers.",
            temperature=0.1,
            max_tokens=150
        )
        
        print("📝 Testing prompt formatting across providers...")
        
        responses = {}
        
        for provider_type, provider in manager.providers.items():
            if not manager._provider_health.get(provider_type, False):
                continue
            
            try:
                print(f"\n   Testing {provider_type.value}:")
                
                # Format request for provider
                from infra_mind.llm.prompt_formatter import prompt_formatter
                formatted_request = prompt_formatter.format_request_for_provider(
                    test_request, provider_type
                )
                
                print(f"     Original prompt length: {len(test_request.prompt)}")
                print(f"     Formatted prompt length: {len(formatted_request.prompt)}")
                print(f"     Has system prompt: {bool(formatted_request.system_prompt)}")
                
                # Generate response
                response = await provider.generate_response(formatted_request)
                responses[provider_type.value] = response
                
                print(f"     Response length: {len(response.content)}")
                print(f"     Tokens used: {response.token_usage.total_tokens}")
                print(f"     Cost: ${response.token_usage.estimated_cost:.6f}")
                print(f"     Preview: {response.content[:60]}...")
                
            except Exception as e:
                print(f"     ❌ Failed: {str(e)}")
        
        # Compare response quality
        if len(responses) > 1:
            print(f"\n🔍 Response Comparison:")
            for provider_name, response in responses.items():
                print(f"   {provider_name}:")
                print(f"     Length: {len(response.content)} chars")
                print(f"     Cost: ${response.token_usage.estimated_cost:.6f}")
                print(f"     Time: {response.response_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt formatting test failed: {str(e)}")
        return False


async def test_cost_optimization():
    """Test cost optimization recommendations."""
    print("\n" + "="*60)
    print("TESTING COST OPTIMIZATION RECOMMENDATIONS")
    print("="*60)
    
    try:
        manager = LLMManager()
        
        # Generate some usage data by making requests
        print("📈 Generating usage data...")
        
        test_requests = [
            LLMRequest(prompt="What is cloud computing?", max_tokens=100),
            LLMRequest(prompt="Explain microservices architecture.", max_tokens=200),
            LLMRequest(prompt="Benefits of Infrastructure as Code?", max_tokens=150),
        ]
        
        for i, request in enumerate(test_requests):
            try:
                response = await manager.generate_response(request, agent_name=f"test_agent_{i}")
                print(f"   Request {i+1}: {response.provider.value} - ${response.token_usage.estimated_cost:.6f}")
            except Exception as e:
                print(f"   Request {i+1}: Failed - {str(e)}")
        
        # Get optimization recommendations
        print("\n💡 Getting cost optimization recommendations...")
        recommendations = manager.get_cost_optimization_recommendations()
        
        print(f"   Timestamp: {recommendations['timestamp']}")
        print(f"   Estimated savings: ${recommendations['estimated_savings']:.4f}")
        
        if recommendations['provider_recommendations']:
            print(f"\n🔄 Provider Recommendations:")
            for rec in recommendations['provider_recommendations']:
                print(f"     Type: {rec['type']}")
                print(f"     Provider: {rec['current_provider']}")
                print(f"     Issue: {rec['issue']}")
                print(f"     Recommendation: {rec['recommendation']}")
        
        if recommendations['usage_optimization']:
            print(f"\n⚡ Usage Optimization:")
            for rec in recommendations['usage_optimization']:
                print(f"     Type: {rec['type']}")
                print(f"     Recommendation: {rec['recommendation']}")
                print(f"     Potential savings: {rec.get('potential_savings_percentage', 0)}%")
        
        if recommendations['model_recommendations']:
            print(f"\n🎯 Model Recommendations:")
            for rec in recommendations['model_recommendations']:
                print(f"     Provider: {rec['provider']}")
                print(f"     Current model: {rec['current_model']}")
                print(f"     Recommendation: {rec['recommendation']}")
                print(f"     Suggested models: {rec.get('suggested_models', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cost optimization test failed: {str(e)}")
        return False


async def main():
    """Run all Gemini integration tests."""
    print("🚀 GEMINI 2.5 PRO INTEGRATION & COST COMPARISON DEMO")
    print("="*60)
    
    # Check environment
    settings = get_settings()
    openai_key = settings.get_openai_api_key()
    gemini_key = settings.get_gemini_api_key()
    
    print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"Gemini API Key: {'✅ Set' if gemini_key else '❌ Missing'}")
    
    if not openai_key and not gemini_key:
        print("\n❌ No API keys found. Please set environment variables:")
        print("   INFRA_MIND_OPENAI_API_KEY")
        print("   INFRA_MIND_GEMINI_API_KEY")
        return
    
    # Run tests
    tests = [
        ("Gemini Provider", test_gemini_provider),
        ("Cost Comparison", test_cost_comparison),
        ("Provider Switching", test_provider_switching),
        ("Prompt Formatting", test_prompt_formatting),
        ("Cost Optimization", test_cost_optimization),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"\n{test_name}: ❌ ERROR - {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())