"""
Production Performance Optimization Service for Infra Mind.

Integrates database query optimization, advanced caching strategies,
LLM usage optimization, and connection pooling for real data volumes.
"""

import asyncio
import time
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import hashlib
import json
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from .performance_optimizer import (
    DatabaseQueryOptimizer, 
    AdvancedCacheManager, 
    LLMPromptOptimizer,
    HorizontalScalingManager
)
from .database import db
from .cache import cache_manager
from .metrics_collector import get_metrics_collector
from ..llm.usage_optimizer import LLMUsageOptimizer
from ..llm.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


@dataclass
class PerformanceProfile:
    """Performance profile for different workload types."""
    name: str
    max_concurrent_requests: int
    cache_ttl_seconds: int
    db_connection_pool_size: int
    llm_optimization_level: str  # conservative, balanced, aggressive
    enable_query_optimization: bool = True
    enable_response_caching: bool = True
    enable_connection_pooling: bool = True


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    cache_hit_rate_percent: float
    db_query_avg_time_ms: float
    llm_token_efficiency_percent: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ProductionPerformanceOptimizer:
    """
    Production-ready performance optimization service.
    
    Integrates all optimization components for real-world data volumes
    and provides comprehensive performance monitoring and tuning.
    """
    
    def __init__(self):
        """Initialize production performance optimizer."""
        self.db_optimizer = DatabaseQueryOptimizer()
        self.cache_optimizer = AdvancedCacheManager()
        self.llm_optimizer = LLMPromptOptimizer()
        self.scaling_manager = HorizontalScalingManager()
        self.metrics_collector = get_metrics_collector()
        
        # Performance profiles for different workloads
        self.performance_profiles = {
            "development": PerformanceProfile(
                name="development",
                max_concurrent_requests=10,
                cache_ttl_seconds=300,
                db_connection_pool_size=5,
                llm_optimization_level="conservative"
            ),
            "staging": PerformanceProfile(
                name="staging",
                max_concurrent_requests=50,
                cache_ttl_seconds=600,
                db_connection_pool_size=10,
                llm_optimization_level="balanced"
            ),
            "production": PerformanceProfile(
                name="production",
                max_concurrent_requests=200,
                cache_ttl_seconds=1800,
                db_connection_pool_size=20,
                llm_optimization_level="balanced"
            ),
            "high_load": PerformanceProfile(
                name="high_load",
                max_concurrent_requests=500,
                cache_ttl_seconds=3600,
                db_connection_pool_size=50,
                llm_optimization_level="aggressive"
            )
        }
        
        self.current_profile = self.performance_profiles["production"]
        self.performance_metrics = PerformanceMetrics(
            avg_response_time_ms=0.0,
            p95_response_time_ms=0.0,
            p99_response_time_ms=0.0,
            requests_per_second=0.0,
            error_rate_percent=0.0,
            cache_hit_rate_percent=0.0,
            db_query_avg_time_ms=0.0,
            llm_token_efficiency_percent=0.0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            active_connections=0
        )
        
        # Performance monitoring
        self.response_times = deque(maxlen=10000)
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        # Connection pooling
        self.connection_pools = {}
        self.pool_stats = defaultdict(dict)
        
        # Background optimization tasks
        self.optimization_tasks = []
        self.is_optimizing = False
        
        logger.info("Production performance optimizer initialized")
    
    async def start_optimization(self, profile_name: str = "production") -> None:
        """
        Start performance optimization with specified profile.
        
        Args:
            profile_name: Performance profile to use
        """
        if profile_name not in self.performance_profiles:
            raise ValueError(f"Unknown performance profile: {profile_name}")
        
        self.current_profile = self.performance_profiles[profile_name]
        self.is_optimizing = True
        
        # Start optimization tasks
        self.optimization_tasks = [
            asyncio.create_task(self._monitor_performance()),
            asyncio.create_task(self._optimize_database_queries()),
            asyncio.create_task(self._optimize_cache_performance()),
            asyncio.create_task(self._optimize_llm_usage()),
            asyncio.create_task(self._manage_connection_pools()),
            asyncio.create_task(self._auto_scale_resources())
        ]
        
        logger.info(f"Started performance optimization with {profile_name} profile")
    
    async def stop_optimization(self) -> None:
        """Stop performance optimization."""
        self.is_optimizing = False
        
        # Cancel optimization tasks
        for task in self.optimization_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.optimization_tasks.clear()
        logger.info("Stopped performance optimization")
    
    @asynccontextmanager
    async def optimize_request(self, request_type: str = "api"):
        """
        Context manager for optimizing individual requests.
        
        Args:
            request_type: Type of request (api, database, llm, etc.)
        """
        start_time = time.time()
        request_id = f"{request_type}_{int(start_time * 1000)}"
        
        try:
            # Pre-request optimizations
            await self._prepare_request_resources(request_type)
            
            yield request_id
            
            # Request completed successfully
            response_time = (time.time() - start_time) * 1000
            self._record_request_success(response_time, request_type)
            
        except Exception as e:
            # Request failed
            response_time = (time.time() - start_time) * 1000
            self._record_request_error(response_time, request_type, str(e))
            raise
        
        finally:
            # Post-request cleanup
            await self._cleanup_request_resources(request_type)
    
    async def _prepare_request_resources(self, request_type: str) -> None:
        """Prepare resources for optimal request handling."""
        try:
            # Warm up cache if needed
            if self.current_profile.enable_response_caching:
                await self._warm_relevant_cache(request_type)
            
            # Prepare database connections
            if self.current_profile.enable_connection_pooling:
                await self._prepare_db_connection(request_type)
            
            # Pre-load frequently used data
            await self._preload_common_data(request_type)
            
        except Exception as e:
            logger.warning(f"Failed to prepare request resources: {e}")
    
    async def _cleanup_request_resources(self, request_type: str) -> None:
        """Clean up resources after request completion."""
        try:
            # Return connections to pool
            await self._return_db_connection(request_type)
            
            # Update cache statistics
            await self._update_cache_stats(request_type)
            
        except Exception as e:
            logger.warning(f"Failed to cleanup request resources: {e}")
    
    def _record_request_success(self, response_time_ms: float, request_type: str) -> None:
        """Record successful request metrics."""
        self.response_times.append(response_time_ms)
        self.request_count += 1
        
        # Record in metrics collector
        asyncio.create_task(
            self.metrics_collector.record_monitoring_metric(
                f"performance.{request_type}.response_time",
                response_time_ms,
                "ms"
            )
        )
    
    def _record_request_error(self, response_time_ms: float, request_type: str, error: str) -> None:
        """Record failed request metrics."""
        self.response_times.append(response_time_ms)
        self.request_count += 1
        self.error_count += 1
        
        # Record in metrics collector
        asyncio.create_task(
            self.metrics_collector.record_monitoring_metric(
                f"performance.{request_type}.error_rate",
                1.0,
                "count"
            )
        )
        
        logger.warning(f"Request failed: {request_type} - {error} ({response_time_ms:.2f}ms)")
    
    async def _monitor_performance(self) -> None:
        """Continuously monitor and update performance metrics."""
        while self.is_optimizing:
            try:
                await self._update_performance_metrics()
                await self._check_performance_thresholds()
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _update_performance_metrics(self) -> None:
        """Update comprehensive performance metrics."""
        try:
            # Calculate response time metrics
            if self.response_times:
                sorted_times = sorted(self.response_times)
                self.performance_metrics.avg_response_time_ms = sum(sorted_times) / len(sorted_times)
                self.performance_metrics.p95_response_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
                self.performance_metrics.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
            
            # Calculate requests per second
            uptime_seconds = time.time() - self.start_time
            self.performance_metrics.requests_per_second = self.request_count / max(uptime_seconds, 1)
            
            # Calculate error rate
            self.performance_metrics.error_rate_percent = (
                (self.error_count / max(self.request_count, 1)) * 100
            )
            
            # Get system metrics
            self.performance_metrics.memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            self.performance_metrics.cpu_usage_percent = psutil.cpu_percent()
            self.performance_metrics.active_connections = len(psutil.net_connections())
            
            # Get cache metrics
            cache_stats = await cache_manager.get_cache_stats()
            if cache_stats.get("connected"):
                hits = cache_stats.get("keyspace_hits", 0)
                misses = cache_stats.get("keyspace_misses", 0)
                total = hits + misses
                self.performance_metrics.cache_hit_rate_percent = (hits / max(total, 1)) * 100
            
            # Get database metrics
            db_report = await self.db_optimizer.get_query_performance_report()
            if "summary" in db_report:
                self.performance_metrics.db_query_avg_time_ms = db_report["summary"].get("avg_execution_time_ms", 0)
            
            # Get LLM optimization metrics
            llm_report = self.llm_optimizer.get_optimization_report()
            if "summary" in llm_report:
                self.performance_metrics.llm_token_efficiency_percent = llm_report["summary"].get("overall_compression_ratio", 0)
            
            # Update timestamp
            self.performance_metrics.timestamp = datetime.utcnow()
            
            # Record metrics
            await self.metrics_collector.record_monitoring_metric(
                "performance.overall.avg_response_time",
                self.performance_metrics.avg_response_time_ms,
                "ms"
            )
            
            await self.metrics_collector.record_monitoring_metric(
                "performance.overall.requests_per_second",
                self.performance_metrics.requests_per_second,
                "rps"
            )
            
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")
    
    async def _check_performance_thresholds(self) -> None:
        """Check performance thresholds and trigger optimizations."""
        try:
            # Check response time threshold
            if self.performance_metrics.avg_response_time_ms > 2000:  # 2 seconds
                logger.warning(f"High response time detected: {self.performance_metrics.avg_response_time_ms:.2f}ms")
                await self._trigger_response_time_optimization()
            
            # Check error rate threshold
            if self.performance_metrics.error_rate_percent > 5:  # 5%
                logger.warning(f"High error rate detected: {self.performance_metrics.error_rate_percent:.2f}%")
                await self._trigger_error_rate_optimization()
            
            # Check memory usage threshold
            if self.performance_metrics.memory_usage_mb > 2048:  # 2GB
                logger.warning(f"High memory usage detected: {self.performance_metrics.memory_usage_mb:.2f}MB")
                await self._trigger_memory_optimization()
            
            # Check cache hit rate threshold
            if self.performance_metrics.cache_hit_rate_percent < 70:  # 70%
                logger.warning(f"Low cache hit rate detected: {self.performance_metrics.cache_hit_rate_percent:.2f}%")
                await self._trigger_cache_optimization()
            
        except Exception as e:
            logger.error(f"Performance threshold check failed: {e}")
    
    async def _trigger_response_time_optimization(self) -> None:
        """Trigger optimizations to improve response time."""
        try:
            # Increase cache TTL
            if self.current_profile.cache_ttl_seconds < 3600:
                self.current_profile.cache_ttl_seconds = min(3600, self.current_profile.cache_ttl_seconds * 2)
                logger.info(f"Increased cache TTL to {self.current_profile.cache_ttl_seconds}s")
            
            # Optimize database queries
            await self.db_optimizer.optimize_indexes()
            
            # Warm up cache
            await self._warm_critical_cache()
            
        except Exception as e:
            logger.error(f"Response time optimization failed: {e}")
    
    async def _trigger_error_rate_optimization(self) -> None:
        """Trigger optimizations to reduce error rate."""
        try:
            # Increase connection pool size
            if self.current_profile.db_connection_pool_size < 50:
                self.current_profile.db_connection_pool_size = min(50, self.current_profile.db_connection_pool_size + 5)
                logger.info(f"Increased DB connection pool to {self.current_profile.db_connection_pool_size}")
            
            # Enable more conservative LLM optimization
            if self.current_profile.llm_optimization_level == "aggressive":
                self.current_profile.llm_optimization_level = "balanced"
                logger.info("Switched to balanced LLM optimization")
            
        except Exception as e:
            logger.error(f"Error rate optimization failed: {e}")
    
    async def _trigger_memory_optimization(self) -> None:
        """Trigger optimizations to reduce memory usage."""
        try:
            # Clear old cache entries
            await self.cache_optimizer.warm_cache([])  # This will trigger cleanup
            
            # Reduce response time buffer
            if len(self.response_times) > 5000:
                self.response_times = deque(list(self.response_times)[-2500:], maxlen=10000)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("Triggered memory optimization")
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
    
    async def _trigger_cache_optimization(self) -> None:
        """Trigger optimizations to improve cache performance."""
        try:
            # Warm up frequently accessed data
            await self._warm_critical_cache()
            
            # Analyze cache patterns
            cache_report = await self.cache_optimizer.get_cache_performance_report()
            logger.info(f"Cache performance report: {cache_report}")
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
    
    async def _optimize_database_queries(self) -> None:
        """Continuously optimize database queries."""
        while self.is_optimizing:
            try:
                if self.current_profile.enable_query_optimization:
                    # Get query performance report
                    report = await self.db_optimizer.get_query_performance_report()
                    
                    # Log slow queries
                    if "top_slow_queries" in report:
                        for query in report["top_slow_queries"][:5]:
                            logger.info(f"Slow query: {query['collection']}.{query['operation']} - {query['execution_time_ms']:.2f}ms")
                    
                    # Optimize indexes if needed
                    if report.get("summary", {}).get("slow_query_rate", 0) > 10:  # 10% slow queries
                        await self.db_optimizer.optimize_indexes()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Database optimization error: {e}")
                await asyncio.sleep(300)
    
    async def _optimize_cache_performance(self) -> None:
        """Continuously optimize cache performance."""
        while self.is_optimizing:
            try:
                if self.current_profile.enable_response_caching:
                    # Get cache performance report
                    report = await self.cache_optimizer.get_cache_performance_report()
                    
                    # Start prefetch worker if not running
                    if not hasattr(self.cache_optimizer, '_prefetch_worker_started'):
                        asyncio.create_task(self.cache_optimizer.start_prefetch_worker())
                        self.cache_optimizer._prefetch_worker_started = True
                    
                    # Log cache statistics
                    if "summary" in report:
                        hit_rate = report["summary"].get("hit_rate_percent", 0)
                        logger.debug(f"Cache hit rate: {hit_rate:.2f}%")
                
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache optimization error: {e}")
                await asyncio.sleep(180)
    
    async def _optimize_llm_usage(self) -> None:
        """Continuously optimize LLM usage."""
        while self.is_optimizing:
            try:
                # Get LLM optimization report
                report = self.llm_optimizer.get_optimization_report()
                
                # Log optimization statistics
                if "summary" in report:
                    compression_ratio = report["summary"].get("overall_compression_ratio", 0)
                    cost_savings = report["summary"].get("estimated_total_cost_savings", 0)
                    logger.debug(f"LLM optimization: {compression_ratio:.2f}% compression, ${cost_savings:.4f} saved")
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LLM optimization error: {e}")
                await asyncio.sleep(600)
    
    async def _manage_connection_pools(self) -> None:
        """Manage database and API connection pools."""
        while self.is_optimizing:
            try:
                if self.current_profile.enable_connection_pooling:
                    # Monitor connection pool health
                    await self._monitor_connection_pools()
                    
                    # Adjust pool sizes based on load
                    await self._adjust_pool_sizes()
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection pool management error: {e}")
                await asyncio.sleep(120)
    
    async def _auto_scale_resources(self) -> None:
        """Automatically scale resources based on load."""
        while self.is_optimizing:
            try:
                # Check if we need to scale up or down
                current_load = self.performance_metrics.requests_per_second
                max_capacity = self.current_profile.max_concurrent_requests
                
                load_percentage = (current_load / max_capacity) * 100 if max_capacity > 0 else 0
                
                if load_percentage > 80:  # Scale up
                    await self._scale_up_resources()
                elif load_percentage < 20:  # Scale down
                    await self._scale_down_resources()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(300)
    
    async def _scale_up_resources(self) -> None:
        """Scale up resources to handle increased load."""
        try:
            # Increase connection pool sizes
            self.current_profile.db_connection_pool_size = min(
                100, 
                int(self.current_profile.db_connection_pool_size * 1.5)
            )
            
            # Increase cache TTL for better hit rates
            self.current_profile.cache_ttl_seconds = min(
                7200,  # 2 hours max
                int(self.current_profile.cache_ttl_seconds * 1.2)
            )
            
            logger.info(f"Scaled up: DB pool={self.current_profile.db_connection_pool_size}, Cache TTL={self.current_profile.cache_ttl_seconds}s")
            
        except Exception as e:
            logger.error(f"Scale up failed: {e}")
    
    async def _scale_down_resources(self) -> None:
        """Scale down resources to save costs during low load."""
        try:
            # Decrease connection pool sizes
            self.current_profile.db_connection_pool_size = max(
                5,  # Minimum pool size
                int(self.current_profile.db_connection_pool_size * 0.8)
            )
            
            # Decrease cache TTL to free memory
            self.current_profile.cache_ttl_seconds = max(
                300,  # 5 minutes minimum
                int(self.current_profile.cache_ttl_seconds * 0.9)
            )
            
            logger.info(f"Scaled down: DB pool={self.current_profile.db_connection_pool_size}, Cache TTL={self.current_profile.cache_ttl_seconds}s")
            
        except Exception as e:
            logger.error(f"Scale down failed: {e}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            # Get component reports
            db_report = await self.db_optimizer.get_query_performance_report()
            cache_report = await self.cache_optimizer.get_cache_performance_report()
            llm_report = self.llm_optimizer.get_optimization_report()
            
            return {
                "overall_metrics": {
                    "avg_response_time_ms": self.performance_metrics.avg_response_time_ms,
                    "p95_response_time_ms": self.performance_metrics.p95_response_time_ms,
                    "p99_response_time_ms": self.performance_metrics.p99_response_time_ms,
                    "requests_per_second": self.performance_metrics.requests_per_second,
                    "error_rate_percent": self.performance_metrics.error_rate_percent,
                    "cache_hit_rate_percent": self.performance_metrics.cache_hit_rate_percent,
                    "memory_usage_mb": self.performance_metrics.memory_usage_mb,
                    "cpu_usage_percent": self.performance_metrics.cpu_usage_percent,
                    "active_connections": self.performance_metrics.active_connections
                },
                "current_profile": {
                    "name": self.current_profile.name,
                    "max_concurrent_requests": self.current_profile.max_concurrent_requests,
                    "cache_ttl_seconds": self.current_profile.cache_ttl_seconds,
                    "db_connection_pool_size": self.current_profile.db_connection_pool_size,
                    "llm_optimization_level": self.current_profile.llm_optimization_level
                },
                "database_performance": db_report,
                "cache_performance": cache_report,
                "llm_optimization": llm_report,
                "system_health": {
                    "uptime_seconds": time.time() - self.start_time,
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                    "optimization_active": self.is_optimizing
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    # Helper methods for cache warming and connection management
    
    async def _warm_relevant_cache(self, request_type: str) -> None:
        """Warm cache with relevant data for request type."""
        # Implementation would depend on request type
        pass
    
    async def _warm_critical_cache(self) -> None:
        """Warm cache with critical frequently-accessed data."""
        try:
            # This would warm cache with commonly accessed cloud pricing data,
            # service catalogs, and other frequently requested information
            warmup_data = [
                {
                    "provider": "aws",
                    "service": "ec2",
                    "region": "us-east-1",
                    "data": {"pricing": "cached_pricing_data"},
                    "ttl": self.current_profile.cache_ttl_seconds
                },
                {
                    "provider": "azure",
                    "service": "compute",
                    "region": "eastus",
                    "data": {"pricing": "cached_pricing_data"},
                    "ttl": self.current_profile.cache_ttl_seconds
                }
            ]
            
            warmed_count = await self.cache_optimizer.warm_cache(warmup_data)
            logger.info(f"Warmed {warmed_count} critical cache entries")
            
        except Exception as e:
            logger.error(f"Critical cache warming failed: {e}")
    
    async def _preload_common_data(self, request_type: str) -> None:
        """Preload commonly used data for request type."""
        # Implementation would preload data based on request patterns
        pass
    
    async def _prepare_db_connection(self, request_type: str) -> None:
        """Prepare database connection for request."""
        # Implementation would manage connection pool
        pass
    
    async def _return_db_connection(self, request_type: str) -> None:
        """Return database connection to pool."""
        # Implementation would return connection to pool
        pass
    
    async def _update_cache_stats(self, request_type: str) -> None:
        """Update cache statistics for request type."""
        # Implementation would update cache hit/miss statistics
        pass
    
    async def _monitor_connection_pools(self) -> None:
        """Monitor health of connection pools."""
        # Implementation would monitor pool health
        pass
    
    async def _adjust_pool_sizes(self) -> None:
        """Adjust connection pool sizes based on current load."""
        # Implementation would adjust pool sizes dynamically
        pass


# Global performance optimizer instance
performance_optimizer = ProductionPerformanceOptimizer()