"""
Unified cloud service caching layer for all cloud providers including Terraform.

This module provides a comprehensive caching solution that:
- Integrates with all cloud providers (AWS, Azure, GCP, Terraform)
- Implements intelligent cache invalidation strategies
- Provides cache warming procedures for frequently accessed data
- Monitors cache hit rates and optimizes caching strategies
- Supports different data freshness requirements per service type
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from .cache import ProductionCacheManager, CacheStrategy, CacheMetrics
from ..cloud.base import CloudProvider

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Cloud service types with different freshness requirements."""
    PRICING = "pricing"  # Pricing data - moderate freshness (1 hour)
    COMPUTE = "compute"  # Compute services - high freshness (30 minutes)
    STORAGE = "storage"  # Storage services - moderate freshness (1 hour)
    DATABASE = "database"  # Database services - moderate freshness (1 hour)
    AI_ML = "ai_ml"  # AI/ML services - low freshness (4 hours)
    TERRAFORM_MODULES = "terraform_modules"  # Terraform modules - low freshness (24 hours)
    TERRAFORM_PROVIDERS = "terraform_providers"  # Terraform providers - low freshness (24 hours)
    COST_ESTIMATION = "cost_estimation"  # Cost estimates - high freshness (15 minutes)
    COMPLIANCE = "compliance"  # Compliance data - low freshness (24 hours)
    REGIONS = "regions"  # Region data - very low freshness (7 days)


@dataclass
class CacheWarmingEntry:
    """Entry for cache warming procedures."""
    provider: str
    service_type: ServiceType
    region: str
    params: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    frequency_hours: int = 1  # How often to warm this entry
    last_warmed: Optional[datetime] = None


@dataclass
class CacheOptimizationMetrics:
    """Metrics for cache optimization."""
    service_type: ServiceType
    provider: str
    hit_rate: float
    miss_rate: float
    avg_response_time: float
    data_staleness_avg: float
    cost_savings: float  # Estimated cost savings from caching
    optimization_score: float  # Overall optimization score (0-100)


class UnifiedCloudCacheManager:
    """
    Unified caching manager for all cloud services including Terraform.
    
    This manager provides:
    - Service-specific caching strategies based on data freshness requirements
    - Intelligent cache invalidation based on service type and provider
    - Cache warming for frequently accessed data
    - Performance monitoring and optimization
    - Cost optimization through reduced API calls
    """
    
    def __init__(self, cache_manager: ProductionCacheManager):
        """
        Initialize unified cloud cache manager.
        
        Args:
            cache_manager: Production cache manager instance
        """
        self.cache_manager = cache_manager
        self.warming_entries: List[CacheWarmingEntry] = []
        self.optimization_metrics: Dict[str, CacheOptimizationMetrics] = {}
        self.warming_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Service-specific TTL configurations (in seconds)
        self.service_ttls = {
            ServiceType.PRICING: 3600,  # 1 hour
            ServiceType.COMPUTE: 1800,  # 30 minutes
            ServiceType.STORAGE: 3600,  # 1 hour
            ServiceType.DATABASE: 3600,  # 1 hour
            ServiceType.AI_ML: 14400,  # 4 hours
            ServiceType.TERRAFORM_MODULES: 86400,  # 24 hours
            ServiceType.TERRAFORM_PROVIDERS: 86400,  # 24 hours
            ServiceType.COST_ESTIMATION: 900,  # 15 minutes
            ServiceType.COMPLIANCE: 86400,  # 24 hours
            ServiceType.REGIONS: 604800,  # 7 days
        }
        
        # Service-specific cache strategies
        self.service_strategies = {
            ServiceType.PRICING: CacheStrategy.REFRESH_AHEAD,
            ServiceType.COMPUTE: CacheStrategy.REFRESH_AHEAD,
            ServiceType.STORAGE: CacheStrategy.TTL_ONLY,
            ServiceType.DATABASE: CacheStrategy.TTL_ONLY,
            ServiceType.AI_ML: CacheStrategy.TTL_ONLY,
            ServiceType.TERRAFORM_MODULES: CacheStrategy.TTL_ONLY,
            ServiceType.TERRAFORM_PROVIDERS: CacheStrategy.TTL_ONLY,
            ServiceType.COST_ESTIMATION: CacheStrategy.REFRESH_AHEAD,
            ServiceType.COMPLIANCE: CacheStrategy.TTL_ONLY,
            ServiceType.REGIONS: CacheStrategy.TTL_ONLY,
        }
        
        # Initialize default warming entries
        self._initialize_default_warming_entries()
    
    def _initialize_default_warming_entries(self):
        """Initialize default cache warming entries for frequently accessed data."""
        # Common regions for each provider
        aws_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        azure_regions = ["eastus", "westus2", "westeurope", "southeastasia"]
        gcp_regions = ["us-central1", "us-west1", "europe-west1", "asia-southeast1"]
        
        # High-priority warming entries
        for region in aws_regions:
            self.warming_entries.extend([
                CacheWarmingEntry("aws", ServiceType.PRICING, region, priority=1, frequency_hours=2),
                CacheWarmingEntry("aws", ServiceType.COMPUTE, region, priority=1, frequency_hours=1),
                CacheWarmingEntry("aws", ServiceType.STORAGE, region, priority=2, frequency_hours=4),
                CacheWarmingEntry("aws", ServiceType.DATABASE, region, priority=2, frequency_hours=4),
            ])
        
        for region in azure_regions:
            self.warming_entries.extend([
                CacheWarmingEntry("azure", ServiceType.PRICING, region, priority=1, frequency_hours=2),
                CacheWarmingEntry("azure", ServiceType.COMPUTE, region, priority=1, frequency_hours=1),
                CacheWarmingEntry("azure", ServiceType.STORAGE, region, priority=2, frequency_hours=4),
                CacheWarmingEntry("azure", ServiceType.DATABASE, region, priority=2, frequency_hours=4),
            ])
        
        for region in gcp_regions:
            self.warming_entries.extend([
                CacheWarmingEntry("gcp", ServiceType.PRICING, region, priority=1, frequency_hours=2),
                CacheWarmingEntry("gcp", ServiceType.COMPUTE, region, priority=1, frequency_hours=1),
                CacheWarmingEntry("gcp", ServiceType.STORAGE, region, priority=2, frequency_hours=4),
                CacheWarmingEntry("gcp", ServiceType.DATABASE, region, priority=2, frequency_hours=4),
            ])
        
        # Terraform-specific warming entries (global)
        self.warming_entries.extend([
            CacheWarmingEntry("terraform", ServiceType.TERRAFORM_PROVIDERS, "global", priority=2, frequency_hours=24),
            CacheWarmingEntry("terraform", ServiceType.TERRAFORM_MODULES, "global", 
                            {"namespace": "hashicorp"}, priority=2, frequency_hours=12),
            CacheWarmingEntry("terraform", ServiceType.TERRAFORM_MODULES, "global", 
                            {"namespace": "terraform-aws-modules"}, priority=2, frequency_hours=12),
            CacheWarmingEntry("terraform", ServiceType.TERRAFORM_MODULES, "global", 
                            {"namespace": "Azure"}, priority=2, frequency_hours=12),
        ])
    
    async def get_cached_data(self, provider: str, service_type: ServiceType, region: str,
                            params: Optional[Dict[str, Any]] = None,
                            allow_stale: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get cached data with service-specific strategies.
        
        Args:
            provider: Cloud provider (aws, azure, gcp, terraform)
            service_type: Type of service being cached
            region: Cloud region or 'global' for global services
            params: Additional parameters for cache key generation
            allow_stale: Whether to return stale data if available
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            # Get service-specific strategy and TTL
            strategy = self.service_strategies.get(service_type, CacheStrategy.TTL_ONLY)
            
            # Use the cache manager with service-specific strategy
            cached_data = await self.cache_manager.get(
                provider=provider,
                service=service_type.value,
                region=region,
                params=params,
                allow_stale=allow_stale,
                strategy=strategy
            )
            
            # Update metrics
            await self._update_access_metrics(provider, service_type, cached_data is not None)
            
            return cached_data
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    async def set_cached_data(self, provider: str, service_type: ServiceType, region: str,
                            data: Dict[str, Any], params: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> bool:
        """
        Cache data with service-specific strategies and TTL.
        
        Args:
            provider: Cloud provider
            service_type: Type of service being cached
            region: Cloud region or 'global' for global services
            data: Data to cache
            params: Additional parameters for cache key generation
            tags: Cache tags for invalidation
            
        Returns:
            True if cached successfully
        """
        try:
            # Get service-specific TTL and strategy
            ttl = self.service_ttls.get(service_type, 3600)
            strategy = self.service_strategies.get(service_type, CacheStrategy.TTL_ONLY)
            
            # Add service-specific tags
            service_tags = tags or []
            service_tags.extend([
                f"provider:{provider}",
                f"service_type:{service_type.value}",
                f"region:{region}"
            ])
            
            # Cache the data
            success = await self.cache_manager.set(
                provider=provider,
                service=service_type.value,
                region=region,
                data=data,
                ttl=ttl,
                params=params,
                tags=service_tags,
                strategy=strategy
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting cached data: {e}")
            return False
    
    async def invalidate_service_cache(self, provider: str, service_type: ServiceType,
                                     region: Optional[str] = None) -> int:
        """
        Invalidate cache for specific service type.
        
        Args:
            provider: Cloud provider
            service_type: Type of service to invalidate
            region: Specific region or None for all regions
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            if region:
                # Invalidate specific region
                pattern = f"cloud_api:{provider}:{service_type.value}:{region}:*"
            else:
                # Invalidate all regions for this service type
                pattern = f"cloud_api:{provider}:{service_type.value}:*"
            
            return await self.cache_manager.invalidate_by_pattern(pattern)
            
        except Exception as e:
            logger.error(f"Error invalidating service cache: {e}")
            return 0
    
    async def invalidate_provider_cache(self, provider: str) -> int:
        """
        Invalidate all cache entries for a provider.
        
        Args:
            provider: Cloud provider to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        return await self.cache_manager.invalidate_provider_cache(provider)
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags.
        
        Args:
            tags: List of tags to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        total_invalidated = 0
        for tag in tags:
            invalidated = await self.cache_manager.invalidate_by_tag(tag)
            total_invalidated += invalidated
        
        return total_invalidated
    
    async def warm_cache(self, fetch_functions: Dict[str, Callable]) -> Dict[str, int]:
        """
        Warm cache with frequently accessed data.
        
        Args:
            fetch_functions: Dictionary mapping service keys to fetch functions
            
        Returns:
            Dictionary with warming results per service
        """
        warming_results = {}
        
        # Sort warming entries by priority
        sorted_entries = sorted(self.warming_entries, key=lambda x: x.priority)
        
        for entry in sorted_entries:
            try:
                # Check if this entry needs warming
                if not self._should_warm_entry(entry):
                    continue
                
                # Generate service key for fetch function lookup
                service_key = f"{entry.provider}_{entry.service_type.value}"
                
                if service_key not in fetch_functions:
                    logger.warning(f"No fetch function available for {service_key}")
                    continue
                
                # Fetch and cache data
                fetch_func = fetch_functions[service_key]
                
                try:
                    logger.info(f"Warming cache for {entry.provider}:{entry.service_type.value}:{entry.region}")
                    
                    # Call fetch function with appropriate parameters
                    if entry.params:
                        data = await fetch_func(entry.region, **entry.params)
                    else:
                        data = await fetch_func(entry.region)
                    
                    # Cache the data
                    success = await self.set_cached_data(
                        provider=entry.provider,
                        service_type=entry.service_type,
                        region=entry.region,
                        data=data,
                        params=entry.params,
                        tags=[f"warmed:{datetime.utcnow().isoformat()}"]
                    )
                    
                    if success:
                        entry.last_warmed = datetime.utcnow()
                        warming_results[service_key] = warming_results.get(service_key, 0) + 1
                        logger.info(f"Successfully warmed cache for {service_key}")
                    else:
                        logger.warning(f"Failed to warm cache for {service_key}")
                
                except Exception as e:
                    logger.error(f"Error warming cache for {service_key}: {e}")
                    continue
                
                # Add small delay to avoid overwhelming APIs
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing warming entry: {e}")
                continue
        
        logger.info(f"Cache warming completed: {warming_results}")
        return warming_results
    
    def _should_warm_entry(self, entry: CacheWarmingEntry) -> bool:
        """Check if a cache entry should be warmed based on frequency."""
        if entry.last_warmed is None:
            return True
        
        time_since_warmed = datetime.utcnow() - entry.last_warmed
        return time_since_warmed >= timedelta(hours=entry.frequency_hours)
    
    async def start_cache_warming(self, fetch_functions: Dict[str, Callable],
                                interval_minutes: int = 30) -> None:
        """
        Start automatic cache warming process.
        
        Args:
            fetch_functions: Dictionary mapping service keys to fetch functions
            interval_minutes: Interval between warming cycles in minutes
        """
        if self.warming_task and not self.warming_task.done():
            logger.warning("Cache warming task already running")
            return
        
        async def warming_loop():
            while True:
                try:
                    logger.info("Starting cache warming cycle")
                    results = await self.warm_cache(fetch_functions)
                    logger.info(f"Cache warming cycle completed: {results}")
                    
                    # Wait for next cycle
                    await asyncio.sleep(interval_minutes * 60)
                    
                except asyncio.CancelledError:
                    logger.info("Cache warming task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cache warming cycle: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        self.warming_task = asyncio.create_task(warming_loop())
        logger.info(f"Cache warming started with {interval_minutes} minute intervals")
    
    async def stop_cache_warming(self) -> None:
        """Stop automatic cache warming process."""
        if self.warming_task:
            self.warming_task.cancel()
            try:
                await self.warming_task
            except asyncio.CancelledError:
                pass
            self.warming_task = None
            logger.info("Cache warming stopped")
    
    async def _update_access_metrics(self, provider: str, service_type: ServiceType, 
                                   cache_hit: bool) -> None:
        """Update cache access metrics for optimization."""
        try:
            metrics_key = f"{provider}:{service_type.value}"
            
            if metrics_key not in self.optimization_metrics:
                self.optimization_metrics[metrics_key] = CacheOptimizationMetrics(
                    service_type=service_type,
                    provider=provider,
                    hit_rate=0.0,
                    miss_rate=0.0,
                    avg_response_time=0.0,
                    data_staleness_avg=0.0,
                    cost_savings=0.0,
                    optimization_score=0.0
                )
            
            metrics = self.optimization_metrics[metrics_key]
            
            # Update hit/miss rates (simple moving average)
            if cache_hit:
                metrics.hit_rate = (metrics.hit_rate * 0.9) + (100.0 * 0.1)
                metrics.miss_rate = (metrics.miss_rate * 0.9) + (0.0 * 0.1)
            else:
                metrics.hit_rate = (metrics.hit_rate * 0.9) + (0.0 * 0.1)
                metrics.miss_rate = (metrics.miss_rate * 0.9) + (100.0 * 0.1)
            
            # Calculate optimization score (0-100)
            metrics.optimization_score = min(100.0, metrics.hit_rate * 0.7 + 
                                           (100.0 - metrics.miss_rate) * 0.3)
            
        except Exception as e:
            logger.error(f"Error updating access metrics: {e}")
    
    async def get_cache_optimization_report(self) -> Dict[str, Any]:
        """
        Generate cache optimization report with recommendations.
        
        Returns:
            Comprehensive cache optimization report
        """
        try:
            # Get overall cache stats
            cache_stats = await self.cache_manager.get_cache_stats()
            
            # Calculate service-specific metrics
            service_metrics = {}
            total_optimization_score = 0.0
            
            for key, metrics in self.optimization_metrics.items():
                service_metrics[key] = {
                    "service_type": metrics.service_type.value,
                    "provider": metrics.provider,
                    "hit_rate": round(metrics.hit_rate, 2),
                    "miss_rate": round(metrics.miss_rate, 2),
                    "optimization_score": round(metrics.optimization_score, 2),
                    "ttl_seconds": self.service_ttls.get(metrics.service_type, 3600),
                    "strategy": self.service_strategies.get(metrics.service_type, CacheStrategy.TTL_ONLY).value
                }
                total_optimization_score += metrics.optimization_score
            
            # Calculate overall optimization score
            overall_score = (total_optimization_score / len(self.optimization_metrics) 
                           if self.optimization_metrics else 0.0)
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_optimization_score": round(overall_score, 2),
                "cache_stats": cache_stats,
                "service_metrics": service_metrics,
                "warming_entries_count": len(self.warming_entries),
                "active_warming": self.warming_task is not None and not self.warming_task.done(),
                "recommendations": recommendations,
                "service_ttl_configuration": {
                    service_type.value: ttl for service_type, ttl in self.service_ttls.items()
                },
                "service_strategy_configuration": {
                    service_type.value: strategy.value for service_type, strategy in self.service_strategies.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cache optimization recommendations."""
        recommendations = []
        
        for key, metrics in self.optimization_metrics.items():
            # Low hit rate recommendation
            if metrics.hit_rate < 50.0:
                recommendations.append({
                    "type": "low_hit_rate",
                    "service": key,
                    "current_hit_rate": round(metrics.hit_rate, 2),
                    "recommendation": f"Consider increasing TTL for {key} or adding cache warming",
                    "priority": "high" if metrics.hit_rate < 30.0 else "medium"
                })
            
            # High hit rate with potential for longer TTL
            if metrics.hit_rate > 90.0:
                current_ttl = self.service_ttls.get(metrics.service_type, 3600)
                if current_ttl < 7200:  # Less than 2 hours
                    recommendations.append({
                        "type": "extend_ttl",
                        "service": key,
                        "current_ttl": current_ttl,
                        "recommended_ttl": min(current_ttl * 2, 14400),  # Max 4 hours
                        "recommendation": f"High hit rate for {key}, consider extending TTL",
                        "priority": "low"
                    })
        
        # General recommendations
        if len(self.optimization_metrics) > 0:
            avg_score = sum(m.optimization_score for m in self.optimization_metrics.values()) / len(self.optimization_metrics)
            
            if avg_score < 70.0:
                recommendations.append({
                    "type": "general_optimization",
                    "recommendation": "Overall cache performance is below optimal. Consider reviewing TTL settings and warming strategies",
                    "priority": "medium"
                })
        
        return recommendations
    
    async def add_warming_entry(self, provider: str, service_type: ServiceType, region: str,
                              params: Optional[Dict[str, Any]] = None, priority: int = 2,
                              frequency_hours: int = 4) -> None:
        """
        Add a new cache warming entry.
        
        Args:
            provider: Cloud provider
            service_type: Type of service
            region: Cloud region
            params: Additional parameters
            priority: Priority level (1=high, 2=medium, 3=low)
            frequency_hours: How often to warm this entry
        """
        entry = CacheWarmingEntry(
            provider=provider,
            service_type=service_type,
            region=region,
            params=params,
            priority=priority,
            frequency_hours=frequency_hours
        )
        
        self.warming_entries.append(entry)
        logger.info(f"Added cache warming entry: {provider}:{service_type.value}:{region}")
    
    async def remove_warming_entry(self, provider: str, service_type: ServiceType, 
                                 region: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Remove a cache warming entry.
        
        Args:
            provider: Cloud provider
            service_type: Type of service
            region: Cloud region
            params: Additional parameters
            
        Returns:
            True if entry was found and removed
        """
        for i, entry in enumerate(self.warming_entries):
            if (entry.provider == provider and 
                entry.service_type == service_type and 
                entry.region == region and 
                entry.params == params):
                
                del self.warming_entries[i]
                logger.info(f"Removed cache warming entry: {provider}:{service_type.value}:{region}")
                return True
        
        return False
    
    async def get_warming_entries(self) -> List[Dict[str, Any]]:
        """Get all cache warming entries."""
        return [
            {
                "provider": entry.provider,
                "service_type": entry.service_type.value,
                "region": entry.region,
                "params": entry.params,
                "priority": entry.priority,
                "frequency_hours": entry.frequency_hours,
                "last_warmed": entry.last_warmed.isoformat() if entry.last_warmed else None,
                "needs_warming": self._should_warm_entry(entry)
            }
            for entry in self.warming_entries
        ]
    
    def _should_warm_entry(self, entry: CacheWarmingEntry) -> bool:
        """Check if a cache entry should be warmed based on frequency."""
        if entry.last_warmed is None:
            return True
        
        time_since_warmed = datetime.utcnow() - entry.last_warmed
        return time_since_warmed >= timedelta(hours=entry.frequency_hours)


# Global unified cache manager instance
unified_cache_manager: Optional[UnifiedCloudCacheManager] = None


async def init_unified_cache(cache_manager: ProductionCacheManager) -> UnifiedCloudCacheManager:
    """
    Initialize the global unified cloud cache manager.
    
    Args:
        cache_manager: Production cache manager instance
        
    Returns:
        Initialized unified cache manager
    """
    global unified_cache_manager
    
    unified_cache_manager = UnifiedCloudCacheManager(cache_manager)
    logger.info("Unified cloud cache manager initialized")
    
    return unified_cache_manager


async def get_unified_cache_manager() -> Optional[UnifiedCloudCacheManager]:
    """Get the global unified cache manager instance."""
    return unified_cache_manager


async def cleanup_unified_cache() -> None:
    """Cleanup the unified cache manager."""
    global unified_cache_manager
    
    if unified_cache_manager:
        await unified_cache_manager.stop_cache_warming()
        unified_cache_manager = None
    
    logger.info("Unified cloud cache manager cleaned up")