#!/usr/bin/env python3
"""
Demo script for Redis-based caching and rate limiting.

This script demonstrates the caching functionality implemented for task 5.4.
"""

import asyncio
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_cache_functionality():
    """Demonstrate basic cache functionality."""
    print("=" * 60)
    print("DEMO: Redis-based Caching and Rate Limiting")
    print("=" * 60)
    
    try:
        # Initialize cache system
        from src.infra_mind.core.cache import init_cache, cache_manager, rate_limiter, cleanup_cache
        
        print("\n1. Initializing cache system...")
        await init_cache()
        
        if not cache_manager._connected:
            print("⚠️  Redis not available - using fallback mode")
            print("   (Install and start Redis server for full functionality)")
        else:
            print("✅ Redis cache connected successfully")
        
        # Test cache operations
        print("\n2. Testing cache operations...")
        
        # Test data
        test_data = {
            "services": ["ec2.t3.micro", "ec2.t3.small", "ec2.t3.medium"],
            "pricing": {
                "ec2.t3.micro": 0.0104,
                "ec2.t3.small": 0.0208,
                "ec2.t3.medium": 0.0416
            },
            "region": "us-east-1",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the data
        print("   Setting cache data for AWS EC2 services...")
        success = await cache_manager.set("aws", "ec2", "us-east-1", test_data, ttl=300)
        print(f"   Cache set result: {'✅ Success' if success else '❌ Failed'}")
        
        # Retrieve from cache
        print("   Retrieving data from cache...")
        cached_data = await cache_manager.get("aws", "ec2", "us-east-1")
        
        if cached_data:
            print("   ✅ Cache hit!")
            print(f"   Cached services: {cached_data['services']}")
            print(f"   Cache age: {cached_data.get('cache_age_hours', 0):.2f} hours")
            print(f"   Is stale: {cached_data.get('is_stale', False)}")
        else:
            print("   ❌ Cache miss")
        
        # Test cache with different parameters
        print("\n3. Testing cache with parameters...")
        params = {"service_id": "AmazonEC2"}
        pricing_data = {
            "service": "AmazonEC2",
            "prices": [
                {"instance": "t3.micro", "price": 0.0104},
                {"instance": "t3.small", "price": 0.0208}
            ]
        }
        
        await cache_manager.set("aws", "pricing", "us-east-1", pricing_data, params=params)
        retrieved_pricing = await cache_manager.get("aws", "pricing", "us-east-1", params=params)
        
        if retrieved_pricing:
            print("   ✅ Parameterized cache working")
            print(f"   Service: {retrieved_pricing['service']}")
        else:
            print("   ❌ Parameterized cache failed")
        
        # Test rate limiting
        print("\n4. Testing rate limiting...")
        
        # Check rate limit status
        status = await rate_limiter.get_rate_limit_status("aws", "ec2")
        if status.get("available"):
            print(f"   AWS EC2 rate limit: {status['current']}/{status['limit']} requests")
            print(f"   Remaining: {status['remaining']} requests")
        else:
            print("   ⚠️  Rate limiter not available (Redis required)")
        
        # Simulate multiple API calls
        print("   Simulating API calls...")
        for i in range(5):
            rate_check = await rate_limiter.check_rate_limit("aws", "ec2")
            if rate_check["allowed"]:
                print(f"   Request {i+1}: ✅ Allowed (remaining: {rate_check['remaining']})")
            else:
                print(f"   Request {i+1}: ❌ Rate limited")
                break
        
        # Test different providers
        print("\n5. Testing different cloud providers...")
        
        providers = ["aws", "azure", "gcp"]
        for provider in providers:
            rate_check = await rate_limiter.check_rate_limit(provider, "compute")
            print(f"   {provider.upper()}: {'✅ Allowed' if rate_check['allowed'] else '❌ Rate limited'}")
            if rate_check.get("limit"):
                print(f"     Limit: {rate_check['limit']} requests/minute")
        
        # Test cache statistics
        print("\n6. Cache statistics...")
        stats = await cache_manager.get_cache_stats()
        
        if stats["connected"]:
            print(f"   Total cache keys: {stats['total_keys']}")
            print(f"   Memory used: {stats['memory_used']}")
            print(f"   Redis version: {stats['redis_version']}")
        else:
            print("   ⚠️  Cache statistics not available (Redis required)")
        
        # Test cache cleanup
        print("\n7. Testing cache cleanup...")
        deleted_count = await cache_manager.clear_provider_cache("aws")
        print(f"   Cleared {deleted_count} AWS cache entries")
        
        # Cleanup
        print("\n8. Cleaning up...")
        await cleanup_cache()
        print("   ✅ Cache system cleaned up")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")


async def demo_cloud_client_caching():
    """Demonstrate caching with cloud clients."""
    print("\n" + "=" * 60)
    print("DEMO: Cloud Client Caching Integration")
    print("=" * 60)
    
    try:
        from src.infra_mind.core.cache import init_cache, cleanup_cache
        from src.infra_mind.cloud.aws import AWSClient
        from src.infra_mind.cloud.azure import AzureClient
        from src.infra_mind.cloud.base import CloudServiceError
        
        # Initialize cache
        await init_cache()
        
        print("\n1. Testing AWS client with caching...")
        
        # Note: This will fail without real AWS credentials, but shows the caching integration
        try:
            aws_client = AWSClient()
            
            print("   Attempting to get compute services (will use cache if available)...")
            start_time = time.time()
            
            # This will likely fail due to credentials, but shows the caching flow
            services = await aws_client.get_compute_services("us-east-1")
            
            end_time = time.time()
            print(f"   ✅ Retrieved {len(services.services)} services in {end_time - start_time:.2f}s")
            
            # Second call should be faster (cached)
            print("   Making second call (should use cache)...")
            start_time = time.time()
            services2 = await aws_client.get_compute_services("us-east-1")
            end_time = time.time()
            print(f"   ✅ Retrieved {len(services2.services)} services in {end_time - start_time:.2f}s")
            
        except CloudServiceError as e:
            print(f"   ⚠️  AWS client error (expected without credentials): {e}")
        except Exception as e:
            print(f"   ⚠️  Unexpected error: {e}")
        
        print("\n2. Testing Azure client with caching...")
        
        try:
            azure_client = AzureClient()
            
            print("   Attempting to get compute services...")
            start_time = time.time()
            
            # Azure pricing API is public, so this might work
            services = await azure_client.get_compute_services("eastus")
            
            end_time = time.time()
            print(f"   ✅ Retrieved {len(services.services)} services in {end_time - start_time:.2f}s")
            
        except CloudServiceError as e:
            print(f"   ⚠️  Azure client error: {e}")
        except Exception as e:
            print(f"   ⚠️  Unexpected error: {e}")
        
        # Cleanup
        await cleanup_cache()
        
    except Exception as e:
        logger.error(f"Cloud client demo error: {e}")
        print(f"❌ Cloud client demo failed: {e}")


async def main():
    """Run all demos."""
    print("🚀 Starting Infra Mind Caching Demo")
    print("This demo shows the Redis-based caching and rate limiting implementation")
    print("for task 5.4: Basic caching mechanisms (MVP Priority)")
    
    await demo_cache_functionality()
    await demo_cloud_client_caching()
    
    print("\n" + "=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)
    print("\nKey features demonstrated:")
    print("• Redis-based caching with 1-hour TTL")
    print("• Rate limiting compliance for AWS and Azure APIs")
    print("• Fallback to cached data when rate limited")
    print("• Cache key generation with parameters")
    print("• Integration with cloud service clients")
    print("• Graceful degradation when Redis unavailable")


if __name__ == "__main__":
    asyncio.run(main())