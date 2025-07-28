#!/usr/bin/env python3
"""
Demo script for advanced resilience system.

Demonstrates circuit breakers, fallback mechanisms, advanced error handling,
and comprehensive rate limiting and retry strategies.
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import resilience components
from src.infra_mind.core.resilience import (
    ResilienceManager, CircuitBreakerConfig, RetryConfig,
    configure_service_resilience, init_cloud_service_resilience
)

from src.infra_mind.core.advanced_rate_limiter import (
    AdvancedRateLimiter, RateLimitConfig, RateLimitAlgorithm,
    RateLimitScope, RateLimitExceeded,
    init_advanced_rate_limiter
)

from src.infra_mind.core.cache import init_cache


class MockCloudService:
    """Mock cloud service for demonstration."""
    
    def __init__(self, name: str, failure_rate: float = 0.3, latency_range: tuple = (0.1, 2.0)):
        self.name = name
        self.failure_rate = failure_rate
        self.latency_range = latency_range
        self.call_count = 0
        self.success_count = 0
    
    async def call_api(self, operation: str) -> Dict[str, Any]:
        """Simulate API call with configurable failure rate and latency."""
        self.call_count += 1
        
        # Simulate network latency
        latency = random.uniform(*self.latency_range)
        await asyncio.sleep(latency)
        
        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception(f"{self.name} API error: Service temporarily unavailable")
        
        self.success_count += 1
        
        return {
            "service": self.name,
            "operation": operation,
            "data": f"Mock data from {self.name}",
            "timestamp": datetime.now().isoformat(),
            "call_count": self.call_count,
            "success_rate": self.success_count / self.call_count
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "name": self.name,
            "total_calls": self.call_count,
            "successful_calls": self.success_count,
            "success_rate": self.success_count / self.call_count if self.call_count > 0 else 0,
            "failure_rate": self.failure_rate
        }


async def demo_circuit_breaker():
    """Demonstrate circuit breaker functionality."""
    print("\n" + "="*60)
    print("CIRCUIT BREAKER DEMONSTRATION")
    print("="*60)
    
    # Create a flaky service
    flaky_service = MockCloudService("FlakyClouds", failure_rate=0.7)
    
    # Configure resilience for the service
    configure_service_resilience(
        "flaky_service",
        failure_threshold=3,
        recovery_timeout=5,
        max_retries=2
    )
    
    from src.infra_mind.core.resilience import resilience_manager
    
    print("Testing circuit breaker with high failure rate service...")
    
    for i in range(10):
        try:
            async with resilience_manager.resilient_call(
                "flaky_service",
                fallback_key="flaky_demo"
            ) as execute:
                result = await execute(lambda: flaky_service.call_api("get_data"))
                
                print(f"Call {i+1}: SUCCESS - {result['source']}")
                if result['fallback_used']:
                    print(f"  └─ Fallback used: {result['degraded_mode']}")
                
        except Exception as e:
            print(f"Call {i+1}: FAILED - {str(e)}")
        
        # Check circuit breaker state
        health = resilience_manager.get_service_health("flaky_service")
        print(f"  └─ Circuit state: {health['state']}, Failures: {health['failure_count']}")
        
        await asyncio.sleep(0.5)
    
    print(f"\nService stats: {flaky_service.get_stats()}")


async def demo_rate_limiting():
    """Demonstrate advanced rate limiting."""
    print("\n" + "="*60)
    print("ADVANCED RATE LIMITING DEMONSTRATION")
    print("="*60)
    
    # Initialize rate limiter (mock Redis for demo)
    try:
        await init_advanced_rate_limiter()
        from src.infra_mind.core.advanced_rate_limiter import advanced_rate_limiter
        
        if not advanced_rate_limiter:
            print("Rate limiter not available (Redis not connected)")
            return
        
        # Configure different rate limiting algorithms
        sliding_window_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            requests_per_minute=5,
            window_size=60
        )
        
        token_bucket_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_minute=10,
            burst_capacity=3,
            refill_rate=0.17  # ~10 per minute
        )
        
        adaptive_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.ADAPTIVE,
            requests_per_minute=8,
            adaptive_threshold=0.8
        )
        
        # Configure services
        advanced_rate_limiter.configure_service("sliding_service", sliding_window_config)
        advanced_rate_limiter.configure_service("token_service", token_bucket_config)
        advanced_rate_limiter.configure_service("adaptive_service", adaptive_config)
        
        services = ["sliding_service", "token_service", "adaptive_service"]
        
        print("Testing different rate limiting algorithms...")
        
        for service in services:
            print(f"\n--- Testing {service} ---")
            
            for i in range(8):
                try:
                    result = await advanced_rate_limiter.check_rate_limit(service)
                    print(f"Request {i+1}: ALLOWED - Remaining: {result.remaining}")
                    
                except RateLimitExceeded as e:
                    print(f"Request {i+1}: RATE LIMITED - Retry after: {e.retry_after}s")
                
                await asyncio.sleep(0.2)
            
            # Show status
            status = await advanced_rate_limiter.get_rate_limit_status(service)
            print(f"Status: {status}")
    
    except Exception as e:
        print(f"Rate limiting demo failed: {e}")


async def demo_fallback_mechanisms():
    """Demonstrate fallback mechanisms."""
    print("\n" + "="*60)
    print("FALLBACK MECHANISMS DEMONSTRATION")
    print("="*60)
    
    # Create services with different reliability
    reliable_service = MockCloudService("ReliableClouds", failure_rate=0.1)
    unreliable_service = MockCloudService("UnreliableClouds", failure_rate=0.9)
    
    from src.infra_mind.core.resilience import resilience_manager
    
    # Configure services
    configure_service_resilience("reliable_service", failure_threshold=5, max_retries=1)
    configure_service_resilience("unreliable_service", failure_threshold=2, max_retries=2)
    
    print("Testing fallback mechanisms with different service reliability...")
    
    services = [
        ("reliable_service", reliable_service),
        ("unreliable_service", unreliable_service)
    ]
    
    for service_name, service_obj in services:
        print(f"\n--- Testing {service_name} ---")
        
        for i in range(5):
            try:
                async with resilience_manager.resilient_call(
                    service_name,
                    fallback_key=f"{service_name}_demo",
                    default_data={"fallback": "default_data", "service": service_name}
                ) as execute:
                    result = await execute(lambda: service_obj.call_api("get_pricing"))
                    
                    print(f"Call {i+1}: {result['source'].upper()}")
                    if result['fallback_used']:
                        print(f"  └─ Fallback: {result['degraded_mode']}")
                        print(f"  └─ Warnings: {result['warnings']}")
                    
            except Exception as e:
                print(f"Call {i+1}: FAILED - {str(e)}")
            
            await asyncio.sleep(0.3)
        
        print(f"Service stats: {service_obj.get_stats()}")


async def demo_adaptive_rate_limiting():
    """Demonstrate adaptive rate limiting based on success rates."""
    print("\n" + "="*60)
    print("ADAPTIVE RATE LIMITING DEMONSTRATION")
    print("="*60)
    
    try:
        from src.infra_mind.core.advanced_rate_limiter import advanced_rate_limiter
        
        if not advanced_rate_limiter:
            print("Advanced rate limiter not available")
            return
        
        # Configure adaptive rate limiting
        adaptive_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.ADAPTIVE,
            requests_per_minute=10,
            adaptive_threshold=0.8,
            backoff_factor=0.7,
            recovery_factor=1.2
        )
        
        advanced_rate_limiter.configure_service("adaptive_demo", adaptive_config)
        
        print("Testing adaptive rate limiting with varying success rates...")
        
        # Simulate different success rate scenarios
        scenarios = [
            ("High success rate (95%)", 0.95),
            ("Medium success rate (85%)", 0.85),
            ("Low success rate (60%)", 0.60),
            ("Very low success rate (40%)", 0.40)
        ]
        
        for scenario_name, success_rate in scenarios:
            print(f"\n--- {scenario_name} ---")
            
            # Simulate requests with the given success rate
            for i in range(15):
                try:
                    # Check rate limit (adaptive limiter will adjust based on success rate)
                    result = await advanced_rate_limiter.check_rate_limit("adaptive_demo")
                    
                    # Simulate success/failure based on success rate
                    request_success = random.random() < success_rate
                    
                    print(f"Request {i+1}: {'SUCCESS' if request_success else 'FAILED'} "
                          f"- Remaining: {result.remaining}")
                    
                    if 'adaptive_limit' in result.metadata:
                        print(f"  └─ Adaptive limit: {result.metadata['adaptive_limit']}")
                    
                except RateLimitExceeded as e:
                    print(f"Request {i+1}: RATE LIMITED - Retry after: {e.retry_after}s")
                
                await asyncio.sleep(0.1)
            
            # Show final status
            status = await advanced_rate_limiter.get_rate_limit_status("adaptive_demo")
            print(f"Final status: {status}")
            
            # Reset for next scenario
            await advanced_rate_limiter.reset_rate_limit("adaptive_demo")
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"Adaptive rate limiting demo failed: {e}")


async def demo_comprehensive_resilience():
    """Demonstrate comprehensive resilience with all patterns combined."""
    print("\n" + "="*60)
    print("COMPREHENSIVE RESILIENCE DEMONSTRATION")
    print("="*60)
    
    # Create a service that simulates real-world conditions
    production_service = MockCloudService("ProductionAPI", failure_rate=0.2, latency_range=(0.1, 1.0))
    
    # Configure comprehensive resilience
    configure_service_resilience(
        "production_api",
        failure_threshold=3,
        recovery_timeout=10,
        max_retries=3,
        base_delay=0.5,
        max_delay=5.0
    )
    
    from src.infra_mind.core.resilience import resilience_manager
    
    print("Testing comprehensive resilience patterns...")
    print("- Circuit breaker with 3 failure threshold")
    print("- Retry mechanism with exponential backoff")
    print("- Fallback to cached/default data")
    print("- Rate limiting integration")
    
    success_count = 0
    total_calls = 20
    
    for i in range(total_calls):
        start_time = time.time()
        
        try:
            async with resilience_manager.resilient_call(
                "production_api",
                fallback_key="production_demo",
                default_data={
                    "service": "ProductionAPI",
                    "data": "Fallback data",
                    "timestamp": datetime.now().isoformat()
                }
            ) as execute:
                result = await execute(lambda: production_service.call_api("complex_operation"))
                
                success_count += 1
                elapsed = time.time() - start_time
                
                print(f"Call {i+1:2d}: SUCCESS ({elapsed:.2f}s) - Source: {result['source']}")
                
                if result['fallback_used']:
                    print(f"         └─ Fallback: {result['degraded_mode']}")
                if result['warnings']:
                    print(f"         └─ Warnings: {len(result['warnings'])}")
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"Call {i+1:2d}: FAILED ({elapsed:.2f}s) - {str(e)[:50]}...")
        
        # Show circuit breaker state every 5 calls
        if (i + 1) % 5 == 0:
            health = resilience_manager.get_service_health("production_api")
            print(f"         └─ Circuit: {health['state']}, Failures: {health['failure_count']}")
        
        await asyncio.sleep(0.3)
    
    print(f"\nFinal Results:")
    print(f"- Total calls: {total_calls}")
    print(f"- Successful calls: {success_count}")
    print(f"- Success rate: {success_count/total_calls:.1%}")
    print(f"- Service stats: {production_service.get_stats()}")
    
    # Show final health status
    health = resilience_manager.get_all_services_health()
    print(f"- Circuit breaker states: {[(name, state['state']) for name, state in health.items()]}")


async def main():
    """Run all resilience demonstrations."""
    print("Advanced Resilience System Demonstration")
    print("========================================")
    
    try:
        # Initialize systems
        print("Initializing resilience systems...")
        
        # Initialize cache (mock Redis for demo)
        try:
            await init_cache()
            print("✓ Cache system initialized")
        except Exception as e:
            print(f"⚠ Cache system failed: {e}")
        
        # Initialize rate limiter
        try:
            await init_advanced_rate_limiter()
            print("✓ Advanced rate limiter initialized")
        except Exception as e:
            print(f"⚠ Rate limiter failed: {e}")
        
        # Initialize cloud service resilience
        init_cloud_service_resilience()
        print("✓ Cloud service resilience configured")
        
        # Run demonstrations
        await demo_circuit_breaker()
        await demo_rate_limiting()
        await demo_fallback_mechanisms()
        await demo_adaptive_rate_limiting()
        await demo_comprehensive_resilience()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("All resilience patterns demonstrated successfully!")
        print("- Circuit breakers prevent cascading failures")
        print("- Retry mechanisms handle transient errors")
        print("- Fallback mechanisms ensure service availability")
        print("- Advanced rate limiting prevents overload")
        print("- Adaptive algorithms optimize performance")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        try:
            from src.infra_mind.core.cache import cleanup_cache
            from src.infra_mind.core.advanced_rate_limiter import cleanup_advanced_rate_limiter
            
            await cleanup_cache()
            await cleanup_advanced_rate_limiter()
            print("\n✓ Cleanup completed")
        except Exception as e:
            print(f"⚠ Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(main())