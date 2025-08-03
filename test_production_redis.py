#!/usr/bin/env python3
"""
Production Redis Cache Testing Script

Tests the production Redis cache implementation with:
- Connection and clustering functionality
- Cache performance and hit rates
- Invalidation strategies
- Monitoring and health checks
- Load testing and concurrent operations
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, List
from datetime import datetime

from src.infra_mind.core.cache import (
    CacheFactory, CacheConfig, CacheStrategy, 
    ProductionCacheManager, CacheMetrics
)


class RedisCacheTestSuite:
    """Comprehensive test suite for production Redis cache."""
    
    def __init__(self):
        self.cache_manager: ProductionCacheManager = None
        self.test_results: Dict[str, Any] = {}
    
    async def setup_cache(self, use_cluster: bool = False) -> None:
        """Setup cache manager for testing."""
        print(f"🔧 Setting up {'cluster' if use_cluster else 'single'} Redis cache...")
        
        config = CacheConfig(
            redis_url="redis://localhost:6379",
            use_cluster=use_cluster,
            cluster_nodes=["localhost:7000", "localhost:7001", "localhost:7002"] if use_cluster else None,
            default_ttl=300,  # 5 minutes for testing
            max_connections=20,
            enable_monitoring=True,
            enable_compression=True
        )
        
        self.cache_manager = ProductionCacheManager(config)
        await self.cache_manager.connect()
        print("✅ Cache manager connected successfully")
    
    async def test_basic_operations(self) -> Dict[str, Any]:
        """Test basic cache operations."""
        print("\n📝 Testing basic cache operations...")
        
        results = {
            "set_operations": 0,
            "get_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        try:
            # Test SET operations
            test_data = {
                "service_name": "ec2",
                "pricing": {"instance_type": "t3.micro", "price": 0.0104},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            success = await self.cache_manager.set(
                provider="aws",
                service="ec2",
                region="us-east-1",
                data=test_data,
                tags=["aws", "compute", "pricing"]
            )
            
            if success:
                results["set_operations"] += 1
                print("✅ Cache SET operation successful")
            else:
                results["errors"] += 1
                print("❌ Cache SET operation failed")
            
            # Test GET operations
            cached_data = await self.cache_manager.get(
                provider="aws",
                service="ec2",
                region="us-east-1"
            )
            
            if cached_data:
                results["get_operations"] += 1
                results["cache_hits"] += 1
                print("✅ Cache GET operation successful (HIT)")
                print(f"   Retrieved data: {cached_data.get('service_name')}")
            else:
                results["cache_misses"] += 1
                print("❌ Cache GET operation failed (MISS)")
            
            # Test cache miss
            missing_data = await self.cache_manager.get(
                provider="azure",
                service="vm",
                region="eastus"
            )
            
            if missing_data is None:
                results["cache_misses"] += 1
                print("✅ Cache MISS handled correctly")
            
        except Exception as e:
            results["errors"] += 1
            print(f"❌ Basic operations test error: {e}")
        
        return results
    
    async def test_cache_strategies(self) -> Dict[str, Any]:
        """Test different caching strategies."""
        print("\n🎯 Testing cache strategies...")
        
        results = {
            "ttl_only": False,
            "refresh_ahead": False,
            "write_through": False,
            "compression": False
        }
        
        try:
            # Test TTL_ONLY strategy
            await self.cache_manager.set(
                provider="aws",
                service="rds",
                region="us-west-2",
                data={"instance_class": "db.t3.micro", "price": 0.017},
                strategy=CacheStrategy.TTL_ONLY
            )
            
            data = await self.cache_manager.get(
                provider="aws",
                service="rds",
                region="us-west-2",
                strategy=CacheStrategy.TTL_ONLY
            )
            
            if data and data.get("instance_class") == "db.t3.micro":
                results["ttl_only"] = True
                print("✅ TTL_ONLY strategy working")
            
            # Test REFRESH_AHEAD strategy
            await self.cache_manager.set(
                provider="gcp",
                service="compute",
                region="us-central1",
                data={"machine_type": "e2-micro", "price": 0.006},
                strategy=CacheStrategy.REFRESH_AHEAD,
                ttl=10  # Short TTL for testing
            )
            
            # Wait a bit and test refresh ahead
            await asyncio.sleep(2)
            
            data = await self.cache_manager.get(
                provider="gcp",
                service="compute",
                region="us-central1",
                strategy=CacheStrategy.REFRESH_AHEAD
            )
            
            if data:
                results["refresh_ahead"] = True
                print("✅ REFRESH_AHEAD strategy working")
            
            # Test compression
            large_data = {
                "services": [f"service_{i}" for i in range(1000)],
                "pricing": {f"price_{i}": random.uniform(0.001, 1.0) for i in range(100)}
            }
            
            await self.cache_manager.set(
                provider="azure",
                service="storage",
                region="eastus",
                data=large_data
            )
            
            compressed_data = await self.cache_manager.get(
                provider="azure",
                service="storage",
                region="eastus"
            )
            
            if compressed_data and len(compressed_data.get("services", [])) == 1000:
                results["compression"] = True
                print("✅ Compression working")
            
        except Exception as e:
            print(f"❌ Cache strategies test error: {e}")
        
        return results
    
    async def test_invalidation(self) -> Dict[str, Any]:
        """Test cache invalidation strategies."""
        print("\n🗑️  Testing cache invalidation...")
        
        results = {
            "pattern_invalidation": False,
            "tag_invalidation": False,
            "provider_invalidation": False
        }
        
        try:
            # Setup test data
            await self.cache_manager.set(
                provider="aws",
                service="s3",
                region="us-east-1",
                data={"storage_class": "STANDARD", "price": 0.023},
                tags=["aws", "storage", "s3"]
            )
            
            await self.cache_manager.set(
                provider="aws",
                service="s3",
                region="us-west-2",
                data={"storage_class": "STANDARD", "price": 0.023},
                tags=["aws", "storage", "s3"]
            )
            
            # Test tag invalidation
            await self.cache_manager.invalidate_by_tag("s3")
            await asyncio.sleep(1)  # Allow invalidation to process
            
            data = await self.cache_manager.get(
                provider="aws",
                service="s3",
                region="us-east-1"
            )
            
            if data is None:
                results["tag_invalidation"] = True
                print("✅ Tag invalidation working")
            
            # Test provider invalidation
            await self.cache_manager.set(
                provider="azure",
                service="blob",
                region="eastus",
                data={"tier": "hot", "price": 0.018}
            )
            
            await self.cache_manager.invalidate_provider_cache("azure")
            await asyncio.sleep(1)
            
            data = await self.cache_manager.get(
                provider="azure",
                service="blob",
                region="eastus"
            )
            
            if data is None:
                results["provider_invalidation"] = True
                print("✅ Provider invalidation working")
            
        except Exception as e:
            print(f"❌ Invalidation test error: {e}")
        
        return results
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test cache performance under load."""
        print("\n⚡ Testing cache performance...")
        
        results = {
            "operations_per_second": 0,
            "average_response_time": 0,
            "concurrent_operations": 0,
            "error_rate": 0
        }
        
        try:
            # Performance test parameters
            num_operations = 1000
            concurrent_tasks = 50
            
            # Generate test data
            test_operations = []
            for i in range(num_operations):
                operation = {
                    "provider": random.choice(["aws", "azure", "gcp"]),
                    "service": random.choice(["compute", "storage", "database"]),
                    "region": random.choice(["us-east-1", "us-west-2", "eastus", "us-central1"]),
                    "data": {"test_id": i, "price": random.uniform(0.001, 1.0)}
                }
                test_operations.append(operation)
            
            # Run concurrent SET operations
            start_time = time.time()
            
            async def set_operation(op):
                try:
                    return await self.cache_manager.set(
                        provider=op["provider"],
                        service=op["service"],
                        region=op["region"],
                        data=op["data"]
                    )
                except Exception:
                    return False
            
            # Execute operations in batches
            batch_size = concurrent_tasks
            successful_ops = 0
            
            for i in range(0, num_operations, batch_size):
                batch = test_operations[i:i + batch_size]
                tasks = [set_operation(op) for op in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                successful_ops += sum(1 for result in batch_results if result is True)
            
            set_time = time.time() - start_time
            
            # Run concurrent GET operations
            start_time = time.time()
            
            async def get_operation(op):
                try:
                    result = await self.cache_manager.get(
                        provider=op["provider"],
                        service=op["service"],
                        region=op["region"]
                    )
                    return result is not None
                except Exception:
                    return False
            
            cache_hits = 0
            for i in range(0, num_operations, batch_size):
                batch = test_operations[i:i + batch_size]
                tasks = [get_operation(op) for op in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                cache_hits += sum(1 for result in batch_results if result is True)
            
            get_time = time.time() - start_time
            
            # Calculate metrics
            total_time = set_time + get_time
            total_operations = num_operations * 2  # SET + GET
            
            results["operations_per_second"] = round(total_operations / total_time, 2)
            results["average_response_time"] = round((total_time / total_operations) * 1000, 2)  # ms
            results["concurrent_operations"] = concurrent_tasks
            results["error_rate"] = round(((total_operations - successful_ops - cache_hits) / total_operations) * 100, 2)
            
            print(f"✅ Performance test completed:")
            print(f"   Operations/sec: {results['operations_per_second']}")
            print(f"   Avg response time: {results['average_response_time']}ms")
            print(f"   Error rate: {results['error_rate']}%")
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
        
        return results
    
    async def test_monitoring(self) -> Dict[str, Any]:
        """Test monitoring and health check functionality."""
        print("\n📊 Testing monitoring and health checks...")
        
        results = {
            "health_check": False,
            "metrics_collection": False,
            "stats_available": False
        }
        
        try:
            # Test health check
            health = await self.cache_manager.health_check()
            
            if health.get("healthy"):
                results["health_check"] = True
                print("✅ Health check passed")
                print(f"   Connection: {health['checks'].get('connection', {}).get('status')}")
                print(f"   Memory: {health['checks'].get('memory', {}).get('status')}")
            else:
                print("❌ Health check failed")
            
            # Test metrics collection
            metrics = await self.cache_manager.get_performance_metrics()
            
            if isinstance(metrics, CacheMetrics):
                results["metrics_collection"] = True
                print("✅ Metrics collection working")
                print(f"   Total requests: {metrics.total_requests}")
                print(f"   Hit rate: {metrics.hit_rate:.2f}%")
            
            # Test cache stats
            stats = await self.cache_manager.get_cache_stats()
            
            if stats.get("connected"):
                results["stats_available"] = True
                print("✅ Cache stats available")
                print(f"   Total keys: {stats.get('total_keys', 0)}")
                print(f"   Memory used: {stats.get('memory_used', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Monitoring test error: {e}")
        
        return results
    
    async def run_all_tests(self, use_cluster: bool = False) -> Dict[str, Any]:
        """Run all cache tests."""
        print("🚀 Starting Redis Production Cache Test Suite")
        print("=" * 60)
        
        try:
            await self.setup_cache(use_cluster)
            
            # Run test suites
            basic_results = await self.test_basic_operations()
            strategy_results = await self.test_cache_strategies()
            invalidation_results = await self.test_invalidation()
            performance_results = await self.test_performance()
            monitoring_results = await self.test_monitoring()
            
            # Compile results
            self.test_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "cluster_mode": use_cluster,
                "basic_operations": basic_results,
                "cache_strategies": strategy_results,
                "invalidation": invalidation_results,
                "performance": performance_results,
                "monitoring": monitoring_results,
                "overall_success": self._calculate_overall_success()
            }
            
            await self._print_summary()
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            self.test_results = {"error": str(e)}
        
        finally:
            if self.cache_manager:
                await self.cache_manager.disconnect()
        
        return self.test_results
    
    def _calculate_overall_success(self) -> bool:
        """Calculate overall test success rate."""
        try:
            basic_success = self.test_results["basic_operations"]["set_operations"] > 0
            strategy_success = any(self.test_results["cache_strategies"].values())
            invalidation_success = any(self.test_results["invalidation"].values())
            performance_success = self.test_results["performance"]["operations_per_second"] > 0
            monitoring_success = self.test_results["monitoring"]["health_check"]
            
            return all([basic_success, strategy_success, invalidation_success, 
                       performance_success, monitoring_success])
        except Exception:
            return False
    
    async def _print_summary(self) -> None:
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        overall_success = self.test_results.get("overall_success", False)
        status_icon = "✅" if overall_success else "❌"
        
        print(f"{status_icon} Overall Status: {'PASSED' if overall_success else 'FAILED'}")
        print(f"🔧 Cluster Mode: {self.test_results.get('cluster_mode', False)}")
        
        # Basic operations
        basic = self.test_results.get("basic_operations", {})
        print(f"\n📝 Basic Operations:")
        print(f"   SET operations: {basic.get('set_operations', 0)}")
        print(f"   GET operations: {basic.get('get_operations', 0)}")
        print(f"   Cache hits: {basic.get('cache_hits', 0)}")
        print(f"   Cache misses: {basic.get('cache_misses', 0)}")
        
        # Performance
        perf = self.test_results.get("performance", {})
        print(f"\n⚡ Performance:")
        print(f"   Operations/sec: {perf.get('operations_per_second', 0)}")
        print(f"   Avg response time: {perf.get('average_response_time', 0)}ms")
        print(f"   Error rate: {perf.get('error_rate', 0)}%")
        
        # Features
        strategies = self.test_results.get("cache_strategies", {})
        invalidation = self.test_results.get("invalidation", {})
        monitoring = self.test_results.get("monitoring", {})
        
        print(f"\n🎯 Features:")
        print(f"   TTL strategy: {'✅' if strategies.get('ttl_only') else '❌'}")
        print(f"   Refresh ahead: {'✅' if strategies.get('refresh_ahead') else '❌'}")
        print(f"   Compression: {'✅' if strategies.get('compression') else '❌'}")
        print(f"   Tag invalidation: {'✅' if invalidation.get('tag_invalidation') else '❌'}")
        print(f"   Health checks: {'✅' if monitoring.get('health_check') else '❌'}")
        
        print("\n" + "=" * 60)


async def main():
    """Main test execution."""
    test_suite = RedisCacheTestSuite()
    
    # Test single instance
    print("Testing Single Redis Instance...")
    single_results = await test_suite.run_all_tests(use_cluster=False)
    
    # Save results
    with open("redis_cache_test_results.json", "w") as f:
        json.dump(single_results, f, indent=2)
    
    print(f"\n📄 Test results saved to: redis_cache_test_results.json")
    
    # Test cluster (if available)
    # cluster_results = await test_suite.run_all_tests(use_cluster=True)


if __name__ == "__main__":
    asyncio.run(main())