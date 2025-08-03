#!/usr/bin/env python3
"""
Demo script for unified cloud service caching system.

This script demonstrates the comprehensive caching solution that:
- Integrates with all cloud providers (AWS, Azure, GCP, Terraform)
- Implements intelligent cache invalidation strategies
- Provides cache warming procedures for frequently accessed data
- Monitors cache hit rates and optimizes caching strategies
- Supports different data freshness requirements per service type
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.cache import CacheFactory, CacheConfig
from infra_mind.core.unified_cloud_cache import (
    UnifiedCloudCacheManager, ServiceType, init_unified_cache, get_unified_cache_manager
)
from infra_mind.core.cache_warming_service import (
    CacheWarmingService, WarmingPriority, init_cache_warming_service, get_cache_warming_service
)
from infra_mind.cloud.unified import UnifiedCloudClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedCloudCacheDemo:
    """Demo class for unified cloud caching system."""
    
    def __init__(self):
        """Initialize demo components."""
        self.cache_manager = None
        self.unified_cache = None
        self.warming_service = None
        self.unified_client = None
    
    async def initialize_cache_system(self):
        """Initialize the complete caching system."""
        logger.info("🚀 Initializing unified cloud caching system...")
        
        try:
            # Initialize production cache manager
            redis_url = os.getenv('INFRA_MIND_REDIS_URL', 'redis://localhost:6379')
            
            config = CacheConfig(
                redis_url=redis_url,
                default_ttl=3600,
                max_connections=20,
                enable_monitoring=True,
                enable_compression=True
            )
            
            self.cache_manager = CacheFactory.create_production_cache(redis_url)
            await self.cache_manager.connect()
            logger.info("✅ Production cache manager initialized")
            
            # Initialize unified cache manager
            self.unified_cache = await init_unified_cache(self.cache_manager)
            logger.info("✅ Unified cloud cache manager initialized")
            
            # Initialize cache warming service
            self.warming_service = await init_cache_warming_service(self.unified_cache)
            logger.info("✅ Cache warming service initialized")
            
            # Initialize unified cloud client
            self.unified_client = UnifiedCloudClient()
            await self.unified_client.initialize_cache_warming()
            logger.info("✅ Unified cloud client initialized with cache warming")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize cache system: {e}")
            raise
    
    async def demonstrate_service_specific_caching(self):
        """Demonstrate service-specific caching with different TTLs and strategies."""
        logger.info("\n📊 Demonstrating service-specific caching...")
        
        # Test data for different service types
        test_services = [
            {
                "provider": "aws",
                "service_type": ServiceType.PRICING,
                "region": "us-east-1",
                "data": {
                    "services": [
                        {"name": "EC2 t3.micro", "hourly_price": 0.0104, "currency": "USD"},
                        {"name": "EC2 t3.small", "hourly_price": 0.0208, "currency": "USD"}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            {
                "provider": "azure",
                "service_type": ServiceType.COMPUTE,
                "region": "eastus",
                "data": {
                    "services": [
                        {"name": "Standard_B1s", "hourly_price": 0.0104, "currency": "USD"},
                        {"name": "Standard_B2s", "hourly_price": 0.0416, "currency": "USD"}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            {
                "provider": "gcp",
                "service_type": ServiceType.AI_ML,
                "region": "us-central1",
                "data": {
                    "services": [
                        {"name": "AI Platform Training", "hourly_price": 0.50, "currency": "USD"},
                        {"name": "AI Platform Prediction", "hourly_price": 0.30, "currency": "USD"}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            {
                "provider": "terraform",
                "service_type": ServiceType.TERRAFORM_MODULES,
                "region": "global",
                "data": {
                    "modules": [
                        {"name": "terraform-aws-modules/vpc/aws", "version": "3.14.0"},
                        {"name": "terraform-aws-modules/eks/aws", "version": "18.26.6"}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        ]
        
        # Cache data for each service type
        for service in test_services:
            logger.info(f"  📝 Caching {service['provider']} {service['service_type'].value} data...")
            
            success = await self.unified_cache.set_cached_data(
                provider=service["provider"],
                service_type=service["service_type"],
                region=service["region"],
                data=service["data"],
                tags=[f"demo:{datetime.utcnow().isoformat()}"]
            )
            
            if success:
                logger.info(f"    ✅ Successfully cached {service['provider']} {service['service_type'].value}")
                
                # Show TTL and strategy for this service type
                ttl = self.unified_cache.service_ttls.get(service["service_type"], 3600)
                strategy = self.unified_cache.service_strategies.get(service["service_type"])
                logger.info(f"    ⏰ TTL: {ttl}s, Strategy: {strategy.value}")
            else:
                logger.warning(f"    ❌ Failed to cache {service['provider']} {service['service_type'].value}")
        
        # Test cache retrieval
        logger.info("\n  🔍 Testing cache retrieval...")
        for service in test_services:
            cached_data = await self.unified_cache.get_cached_data(
                provider=service["provider"],
                service_type=service["service_type"],
                region=service["region"]
            )
            
            if cached_data:
                logger.info(f"    ✅ Cache hit for {service['provider']} {service['service_type'].value}")
                logger.info(f"    📊 Data: {len(cached_data.get('services', cached_data.get('modules', [])))} items")
            else:
                logger.warning(f"    ❌ Cache miss for {service['provider']} {service['service_type'].value}")
    
    async def demonstrate_cache_warming(self):
        """Demonstrate automated cache warming functionality."""
        logger.info("\n🔥 Demonstrating cache warming...")
        
        # Register mock fetch functions for demonstration
        async def mock_aws_pricing(region, **kwargs):
            return {
                "services": [
                    {"name": f"EC2 instance in {region}", "hourly_price": 0.10, "currency": "USD"}
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mock_api"
            }
        
        async def mock_azure_compute(region, **kwargs):
            return {
                "services": [
                    {"name": f"VM in {region}", "hourly_price": 0.12, "currency": "USD"}
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mock_api"
            }
        
        async def mock_terraform_modules(region, **kwargs):
            namespace = kwargs.get("namespace", "hashicorp")
            return {
                "modules": [
                    {"name": f"{namespace}/example/aws", "version": "1.0.0"}
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mock_api"
            }
        
        # Register fetch functions
        self.warming_service.register_fetch_function("aws_pricing", mock_aws_pricing)
        self.warming_service.register_fetch_function("azure_compute", mock_azure_compute)
        self.warming_service.register_fetch_function("terraform_terraform_modules", mock_terraform_modules)
        
        logger.info("  📋 Registered mock fetch functions")
        
        # Add custom warming schedules
        self.warming_service.add_warming_schedule(
            service_type=ServiceType.PRICING,
            provider="aws",
            region="us-west-2",
            priority=WarmingPriority.HIGH,
            frequency_minutes=30
        )
        
        self.warming_service.add_warming_schedule(
            service_type=ServiceType.TERRAFORM_MODULES,
            provider="terraform",
            region="global",
            priority=WarmingPriority.LOW,
            frequency_minutes=60,
            params={"namespace": "terraform-aws-modules"}
        )
        
        logger.info("  ➕ Added custom warming schedules")
        
        # Run a warming cycle
        logger.info("  🔄 Running warming cycle...")
        warming_results = await self.warming_service.run_warming_cycle()
        
        logger.info(f"  📊 Warming results:")
        logger.info(f"    • Schedules processed: {warming_results['schedules_processed']}")
        logger.info(f"    • Successful warmings: {warming_results['successful_warmings']}")
        logger.info(f"    • Failed warmings: {warming_results['failed_warmings']}")
        logger.info(f"    • Cycle time: {warming_results['cycle_time']:.2f}s")
        
        if warming_results.get('priority_breakdown'):
            logger.info("    • Priority breakdown:")
            for priority, count in warming_results['priority_breakdown'].items():
                logger.info(f"      - {priority}: {count} schedules")
    
    async def demonstrate_cache_invalidation(self):
        """Demonstrate intelligent cache invalidation strategies."""
        logger.info("\n🗑️  Demonstrating cache invalidation...")
        
        # Test service-specific invalidation
        logger.info("  🎯 Testing service-specific invalidation...")
        invalidated = await self.unified_cache.invalidate_service_cache(
            provider="aws",
            service_type=ServiceType.PRICING,
            region="us-east-1"
        )
        logger.info(f"    ✅ Invalidated {invalidated} AWS pricing entries for us-east-1")
        
        # Test provider-wide invalidation
        logger.info("  🌐 Testing provider-wide invalidation...")
        invalidated = await self.unified_cache.invalidate_provider_cache("azure")
        logger.info(f"    ✅ Invalidated {invalidated} Azure cache entries")
        
        # Test tag-based invalidation
        logger.info("  🏷️  Testing tag-based invalidation...")
        invalidated = await self.unified_cache.invalidate_by_tags(["demo:*"])
        logger.info(f"    ✅ Invalidated {invalidated} demo-tagged entries")
    
    async def demonstrate_cache_monitoring(self):
        """Demonstrate cache monitoring and optimization."""
        logger.info("\n📈 Demonstrating cache monitoring and optimization...")
        
        # Get cache optimization report
        logger.info("  📊 Generating cache optimization report...")
        report = await self.unified_cache.get_cache_optimization_report()
        
        logger.info(f"  📋 Cache Optimization Report:")
        logger.info(f"    • Overall optimization score: {report.get('overall_optimization_score', 0):.1f}%")
        logger.info(f"    • Warming entries: {report.get('warming_entries_count', 0)}")
        logger.info(f"    • Active warming: {report.get('active_warming', False)}")
        
        # Show service metrics
        service_metrics = report.get('service_metrics', {})
        if service_metrics:
            logger.info("    • Service metrics:")
            for service_key, metrics in service_metrics.items():
                logger.info(f"      - {service_key}: {metrics['hit_rate']:.1f}% hit rate, "
                          f"{metrics['optimization_score']:.1f}% optimization score")
        
        # Show recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            logger.info("    • Recommendations:")
            for rec in recommendations:
                logger.info(f"      - {rec['type']}: {rec['recommendation']}")
        
        # Get warming service status
        logger.info("\n  🔥 Cache warming service status:")
        warming_status = self.warming_service.get_warming_status()
        
        logger.info(f"    • Running: {warming_status['is_running']}")
        logger.info(f"    • Total schedules: {warming_status['total_schedules']}")
        logger.info(f"    • Schedules needing warming: {warming_status['schedules_needing_warming']}")
        logger.info(f"    • Registered fetch functions: {warming_status['registered_fetch_functions']}")
        
        # Show warming statistics
        stats = warming_status.get('warming_statistics', {})
        logger.info(f"    • Total warmings: {stats.get('total_warmings', 0)}")
        logger.info(f"    • Successful warmings: {stats.get('successful_warmings', 0)}")
        logger.info(f"    • Failed warmings: {stats.get('failed_warmings', 0)}")
        logger.info(f"    • Average warming time: {stats.get('avg_warming_time', 0):.2f}s")
    
    async def demonstrate_unified_client_integration(self):
        """Demonstrate unified client integration with caching."""
        logger.info("\n🔗 Demonstrating unified client integration...")
        
        try:
            # Get cache status through unified client
            logger.info("  📊 Getting cache status through unified client...")
            cache_status = await self.unified_client.get_cache_status()
            
            logger.info(f"  📋 Unified Client Cache Status:")
            logger.info(f"    • Available providers: {cache_status.get('providers', [])}")
            logger.info(f"    • Terraform available: {cache_status.get('terraform_available', False)}")
            
            # Show cache optimization from client perspective
            cache_opt = cache_status.get('cache_optimization', {})
            if 'overall_optimization_score' in cache_opt:
                logger.info(f"    • Overall optimization: {cache_opt['overall_optimization_score']:.1f}%")
            
            # Test manual cache warming through client
            logger.info("  🔥 Testing manual cache warming through client...")
            warming_result = await self.unified_client.warm_cache_manually(provider="aws")
            
            if 'error' not in warming_result:
                logger.info(f"    ✅ Manual warming completed:")
                logger.info(f"      - Provider filter: {warming_result.get('provider_filter', 'all')}")
                results = warming_result.get('results', {})
                logger.info(f"      - Successful: {results.get('successful_warmings', 0)}")
                logger.info(f"      - Failed: {results.get('failed_warmings', 0)}")
            else:
                logger.warning(f"    ❌ Manual warming failed: {warming_result['error']}")
            
            # Test cache invalidation through client
            logger.info("  🗑️  Testing cache invalidation through client...")
            invalidation_result = await self.unified_client.invalidate_cache(
                provider="aws",
                service_type="compute",
                region="us-east-1"
            )
            
            if 'error' not in invalidation_result:
                logger.info(f"    ✅ Invalidated {invalidation_result.get('invalidated_entries', 0)} entries")
            else:
                logger.warning(f"    ❌ Invalidation failed: {invalidation_result['error']}")
        
        except Exception as e:
            logger.error(f"  ❌ Unified client integration error: {e}")
    
    async def demonstrate_performance_optimization(self):
        """Demonstrate performance optimization features."""
        logger.info("\n⚡ Demonstrating performance optimization...")
        
        # Simulate some cache access patterns
        logger.info("  📊 Simulating cache access patterns...")
        
        # Simulate high-frequency access to pricing data
        for i in range(10):
            await self.unified_cache.get_cached_data("aws", ServiceType.PRICING, "us-east-1")
        
        # Simulate low-frequency access to AI/ML data
        for i in range(2):
            await self.unified_cache.get_cached_data("gcp", ServiceType.AI_ML, "us-central1")
        
        # Run schedule optimization
        logger.info("  🔧 Running schedule optimization...")
        optimization_results = await self.warming_service.optimize_schedules()
        
        logger.info(f"  📊 Optimization Results:")
        logger.info(f"    • Optimizations made: {optimization_results['optimizations_made']}")
        
        recommendations = optimization_results.get('recommendations', [])
        if recommendations:
            logger.info("    • Recommendations:")
            for rec in recommendations:
                logger.info(f"      - {rec['type']}: {rec.get('schedule', 'N/A')}")
                logger.info(f"        Reason: {rec.get('reason', 'N/A')}")
        else:
            logger.info("    • No optimization recommendations at this time")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("\n🧹 Cleaning up resources...")
        
        try:
            if self.warming_service:
                await self.warming_service.stop_warming_service()
                logger.info("  ✅ Cache warming service stopped")
            
            if self.unified_client:
                await self.unified_client.stop_cache_warming()
                logger.info("  ✅ Unified client cache warming stopped")
            
            if self.cache_manager:
                await self.cache_manager.disconnect()
                logger.info("  ✅ Cache manager disconnected")
        
        except Exception as e:
            logger.error(f"  ❌ Cleanup error: {e}")
    
    async def run_complete_demo(self):
        """Run the complete unified cloud caching demo."""
        logger.info("🎯 Starting Unified Cloud Caching System Demo")
        logger.info("=" * 60)
        
        try:
            # Initialize system
            await self.initialize_cache_system()
            
            # Run demonstrations
            await self.demonstrate_service_specific_caching()
            await self.demonstrate_cache_warming()
            await self.demonstrate_cache_invalidation()
            await self.demonstrate_cache_monitoring()
            await self.demonstrate_unified_client_integration()
            await self.demonstrate_performance_optimization()
            
            logger.info("\n🎉 Demo completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        
        finally:
            await self.cleanup()


async def main():
    """Main demo function."""
    demo = UnifiedCloudCacheDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Check for Redis availability
    redis_url = os.getenv('INFRA_MIND_REDIS_URL', 'redis://localhost:6379')
    
    print("🚀 Unified Cloud Caching System Demo")
    print("=" * 50)
    print(f"Redis URL: {redis_url}")
    print("Note: This demo requires a running Redis instance")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)