"""
Cache warming service for unified cloud caching.

This service provides automated cache warming for frequently accessed cloud service data
across all providers (AWS, Azure, GCP, Terraform) with intelligent scheduling and
monitoring capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum

from .unified_cloud_cache import UnifiedCloudCacheManager, ServiceType

logger = logging.getLogger(__name__)


class WarmingPriority(Enum):
    """Cache warming priority levels."""
    CRITICAL = 1  # Must be warmed immediately
    HIGH = 2      # Should be warmed within 1 hour
    MEDIUM = 3    # Should be warmed within 4 hours
    LOW = 4       # Can be warmed within 24 hours


@dataclass
class WarmingSchedule:
    """Schedule configuration for cache warming."""
    service_type: ServiceType
    provider: str
    region: str
    priority: WarmingPriority
    frequency_minutes: int
    params: Optional[Dict[str, Any]] = None
    last_warmed: Optional[datetime] = None
    warming_count: int = 0
    error_count: int = 0
    avg_warming_time: float = 0.0


class CacheWarmingService:
    """
    Service for automated cache warming across all cloud providers.
    
    This service:
    - Maintains warming schedules for different service types
    - Prioritizes warming based on usage patterns
    - Monitors warming success rates and performance
    - Provides intelligent scheduling to avoid API rate limits
    - Supports dynamic schedule adjustment based on cache hit rates
    """
    
    def __init__(self, unified_cache: UnifiedCloudCacheManager):
        """
        Initialize cache warming service.
        
        Args:
            unified_cache: Unified cloud cache manager instance
        """
        self.unified_cache = unified_cache
        self.warming_schedules: List[WarmingSchedule] = []
        self.fetch_functions: Dict[str, Callable] = {}
        self.warming_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.warming_stats = {
            "total_warmings": 0,
            "successful_warmings": 0,
            "failed_warmings": 0,
            "avg_warming_time": 0.0,
            "last_warming_cycle": None
        }
        
        # Initialize default warming schedules
        self._initialize_default_schedules()
    
    def _initialize_default_schedules(self):
        """Initialize default warming schedules for common services."""
        # AWS warming schedules
        aws_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        for region in aws_regions:
            self.warming_schedules.extend([
                # Critical services - warm every 30 minutes
                WarmingSchedule(ServiceType.PRICING, "aws", region, WarmingPriority.CRITICAL, 30),
                WarmingSchedule(ServiceType.COMPUTE, "aws", region, WarmingPriority.CRITICAL, 30),
                
                # High priority services - warm every hour
                WarmingSchedule(ServiceType.STORAGE, "aws", region, WarmingPriority.HIGH, 60),
                WarmingSchedule(ServiceType.DATABASE, "aws", region, WarmingPriority.HIGH, 60),
                
                # Medium priority services - warm every 4 hours
                WarmingSchedule(ServiceType.AI_ML, "aws", region, WarmingPriority.MEDIUM, 240),
            ])
        
        # Azure warming schedules
        azure_regions = ["eastus", "westus2", "westeurope", "southeastasia"]
        for region in azure_regions:
            self.warming_schedules.extend([
                WarmingSchedule(ServiceType.PRICING, "azure", region, WarmingPriority.CRITICAL, 30),
                WarmingSchedule(ServiceType.COMPUTE, "azure", region, WarmingPriority.CRITICAL, 30),
                WarmingSchedule(ServiceType.STORAGE, "azure", region, WarmingPriority.HIGH, 60),
                WarmingSchedule(ServiceType.DATABASE, "azure", region, WarmingPriority.HIGH, 60),
                WarmingSchedule(ServiceType.AI_ML, "azure", region, WarmingPriority.MEDIUM, 240),
            ])
        
        # GCP warming schedules
        gcp_regions = ["us-central1", "us-west1", "europe-west1", "asia-southeast1"]
        for region in gcp_regions:
            self.warming_schedules.extend([
                WarmingSchedule(ServiceType.PRICING, "gcp", region, WarmingPriority.CRITICAL, 30),
                WarmingSchedule(ServiceType.COMPUTE, "gcp", region, WarmingPriority.CRITICAL, 30),
                WarmingSchedule(ServiceType.STORAGE, "gcp", region, WarmingPriority.HIGH, 60),
                WarmingSchedule(ServiceType.DATABASE, "gcp", region, WarmingPriority.HIGH, 60),
                WarmingSchedule(ServiceType.AI_ML, "gcp", region, WarmingPriority.MEDIUM, 240),
            ])
        
        # Terraform warming schedules (global services)
        self.warming_schedules.extend([
            # Low priority - warm daily
            WarmingSchedule(ServiceType.TERRAFORM_PROVIDERS, "terraform", "global", WarmingPriority.LOW, 1440),
            WarmingSchedule(ServiceType.TERRAFORM_MODULES, "terraform", "global", WarmingPriority.LOW, 1440,
                          {"namespace": "hashicorp"}),
            WarmingSchedule(ServiceType.TERRAFORM_MODULES, "terraform", "global", WarmingPriority.LOW, 1440,
                          {"namespace": "terraform-aws-modules"}),
            WarmingSchedule(ServiceType.TERRAFORM_MODULES, "terraform", "global", WarmingPriority.LOW, 1440,
                          {"namespace": "Azure"}),
        ])
    
    def register_fetch_function(self, service_key: str, fetch_func: Callable):
        """
        Register a fetch function for a specific service.
        
        Args:
            service_key: Service key in format "provider_servicetype"
            fetch_func: Async function to fetch data for the service
        """
        self.fetch_functions[service_key] = fetch_func
        logger.info(f"Registered fetch function for {service_key}")
    
    def add_warming_schedule(self, service_type: ServiceType, provider: str, region: str,
                           priority: WarmingPriority, frequency_minutes: int,
                           params: Optional[Dict[str, Any]] = None):
        """
        Add a new warming schedule.
        
        Args:
            service_type: Type of service to warm
            provider: Cloud provider
            region: Cloud region
            priority: Warming priority
            frequency_minutes: How often to warm in minutes
            params: Additional parameters for the service
        """
        schedule = WarmingSchedule(
            service_type=service_type,
            provider=provider,
            region=region,
            priority=priority,
            frequency_minutes=frequency_minutes,
            params=params
        )
        
        self.warming_schedules.append(schedule)
        logger.info(f"Added warming schedule: {provider}:{service_type.value}:{region}")
    
    def remove_warming_schedule(self, service_type: ServiceType, provider: str, region: str,
                              params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Remove a warming schedule.
        
        Args:
            service_type: Type of service
            provider: Cloud provider
            region: Cloud region
            params: Additional parameters
            
        Returns:
            True if schedule was found and removed
        """
        for i, schedule in enumerate(self.warming_schedules):
            if (schedule.service_type == service_type and
                schedule.provider == provider and
                schedule.region == region and
                schedule.params == params):
                
                del self.warming_schedules[i]
                logger.info(f"Removed warming schedule: {provider}:{service_type.value}:{region}")
                return True
        
        return False
    
    def _should_warm_schedule(self, schedule: WarmingSchedule) -> bool:
        """Check if a schedule should be warmed based on frequency and priority."""
        if schedule.last_warmed is None:
            return True
        
        time_since_warmed = datetime.utcnow() - schedule.last_warmed
        frequency_delta = timedelta(minutes=schedule.frequency_minutes)
        
        # For critical services, allow some flexibility in timing
        if schedule.priority == WarmingPriority.CRITICAL:
            return time_since_warmed >= frequency_delta * 0.8
        
        return time_since_warmed >= frequency_delta
    
    async def warm_single_schedule(self, schedule: WarmingSchedule) -> bool:
        """
        Warm cache for a single schedule.
        
        Args:
            schedule: Warming schedule to execute
            
        Returns:
            True if warming was successful
        """
        service_key = f"{schedule.provider}_{schedule.service_type.value}"
        
        if service_key not in self.fetch_functions:
            logger.warning(f"No fetch function registered for {service_key}")
            return False
        
        start_time = datetime.utcnow()
        
        try:
            fetch_func = self.fetch_functions[service_key]
            
            # Call fetch function with appropriate parameters
            if schedule.params:
                data = await fetch_func(schedule.region, **schedule.params)
            else:
                data = await fetch_func(schedule.region)
            
            # Cache the data using unified cache
            success = await self.unified_cache.set_cached_data(
                provider=schedule.provider,
                service_type=schedule.service_type,
                region=schedule.region,
                data=data,
                params=schedule.params,
                tags=[f"warmed:{start_time.isoformat()}", f"priority:{schedule.priority.name}"]
            )
            
            if success:
                # Update schedule statistics
                warming_time = (datetime.utcnow() - start_time).total_seconds()
                schedule.last_warmed = start_time
                schedule.warming_count += 1
                schedule.avg_warming_time = (
                    (schedule.avg_warming_time * (schedule.warming_count - 1) + warming_time) /
                    schedule.warming_count
                )
                
                # Update global statistics
                self.warming_stats["total_warmings"] += 1
                self.warming_stats["successful_warmings"] += 1
                self.warming_stats["avg_warming_time"] = (
                    (self.warming_stats["avg_warming_time"] * (self.warming_stats["total_warmings"] - 1) + warming_time) /
                    self.warming_stats["total_warmings"]
                )
                
                logger.debug(f"Successfully warmed {service_key} for {schedule.region} in {warming_time:.2f}s")
                return True
            else:
                schedule.error_count += 1
                self.warming_stats["failed_warmings"] += 1
                logger.warning(f"Failed to cache warmed data for {service_key}")
                return False
        
        except Exception as e:
            schedule.error_count += 1
            self.warming_stats["total_warmings"] += 1
            self.warming_stats["failed_warmings"] += 1
            
            logger.error(f"Error warming {service_key} for {schedule.region}: {e}")
            return False
    
    async def run_warming_cycle(self) -> Dict[str, Any]:
        """
        Run a complete warming cycle for all due schedules.
        
        Returns:
            Dictionary with warming cycle results
        """
        cycle_start = datetime.utcnow()
        
        # Get schedules that need warming, sorted by priority
        due_schedules = [s for s in self.warming_schedules if self._should_warm_schedule(s)]
        due_schedules.sort(key=lambda s: s.priority.value)
        
        if not due_schedules:
            logger.debug("No schedules due for warming")
            return {
                "cycle_time": (datetime.utcnow() - cycle_start).total_seconds(),
                "schedules_processed": 0,
                "successful_warmings": 0,
                "failed_warmings": 0
            }
        
        logger.info(f"Starting warming cycle with {len(due_schedules)} schedules")
        
        successful_warmings = 0
        failed_warmings = 0
        
        # Process schedules by priority groups to avoid overwhelming APIs
        priority_groups = {}
        for schedule in due_schedules:
            priority = schedule.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(schedule)
        
        # Process each priority group
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
            schedules = priority_groups[priority]
            logger.info(f"Processing {len(schedules)} {priority.name} priority schedules")
            
            # Process schedules in batches to avoid rate limits
            batch_size = 5 if priority == WarmingPriority.CRITICAL else 3
            
            for i in range(0, len(schedules), batch_size):
                batch = schedules[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [self.warm_single_schedule(schedule) for schedule in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        failed_warmings += 1
                        logger.error(f"Warming task failed: {result}")
                    elif result:
                        successful_warmings += 1
                    else:
                        failed_warmings += 1
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(schedules):
                    delay = 2.0 if priority == WarmingPriority.CRITICAL else 5.0
                    await asyncio.sleep(delay)
            
            # Add delay between priority groups
            if priority != WarmingPriority.LOW:
                await asyncio.sleep(10.0)
        
        cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
        self.warming_stats["last_warming_cycle"] = cycle_start.isoformat()
        
        logger.info(f"Warming cycle completed in {cycle_time:.2f}s: "
                   f"{successful_warmings} successful, {failed_warmings} failed")
        
        return {
            "cycle_time": cycle_time,
            "schedules_processed": len(due_schedules),
            "successful_warmings": successful_warmings,
            "failed_warmings": failed_warmings,
            "priority_breakdown": {
                priority.name: len(schedules) for priority, schedules in priority_groups.items()
            }
        }
    
    async def start_warming_service(self, cycle_interval_minutes: int = 15):
        """
        Start the automatic cache warming service.
        
        Args:
            cycle_interval_minutes: Interval between warming cycles in minutes
        """
        if self.is_running:
            logger.warning("Cache warming service is already running")
            return
        
        async def warming_loop():
            self.is_running = True
            logger.info(f"Cache warming service started with {cycle_interval_minutes} minute intervals")
            
            while self.is_running:
                try:
                    cycle_results = await self.run_warming_cycle()
                    logger.info(f"Warming cycle results: {cycle_results}")
                    
                    # Wait for next cycle
                    await asyncio.sleep(cycle_interval_minutes * 60)
                    
                except asyncio.CancelledError:
                    logger.info("Cache warming service cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in warming cycle: {e}")
                    # Wait shorter time before retrying on error
                    await asyncio.sleep(60)
            
            self.is_running = False
        
        self.warming_task = asyncio.create_task(warming_loop())
    
    async def stop_warming_service(self):
        """Stop the automatic cache warming service."""
        if not self.is_running:
            logger.warning("Cache warming service is not running")
            return
        
        self.is_running = False
        
        if self.warming_task:
            self.warming_task.cancel()
            try:
                await self.warming_task
            except asyncio.CancelledError:
                pass
            self.warming_task = None
        
        logger.info("Cache warming service stopped")
    
    def get_warming_status(self) -> Dict[str, Any]:
        """
        Get current warming service status and statistics.
        
        Returns:
            Dictionary with service status and statistics
        """
        # Calculate schedule statistics
        total_schedules = len(self.warming_schedules)
        schedules_by_priority = {}
        schedules_by_provider = {}
        schedules_needing_warming = 0
        
        for schedule in self.warming_schedules:
            # Count by priority
            priority_name = schedule.priority.name
            schedules_by_priority[priority_name] = schedules_by_priority.get(priority_name, 0) + 1
            
            # Count by provider
            schedules_by_provider[schedule.provider] = schedules_by_provider.get(schedule.provider, 0) + 1
            
            # Count schedules needing warming
            if self._should_warm_schedule(schedule):
                schedules_needing_warming += 1
        
        return {
            "is_running": self.is_running,
            "total_schedules": total_schedules,
            "schedules_needing_warming": schedules_needing_warming,
            "schedules_by_priority": schedules_by_priority,
            "schedules_by_provider": schedules_by_provider,
            "registered_fetch_functions": len(self.fetch_functions),
            "warming_statistics": self.warming_stats.copy(),
            "next_warming_due": self._get_next_warming_time()
        }
    
    def _get_next_warming_time(self) -> Optional[str]:
        """Get the time when the next warming is due."""
        next_warming = None
        
        for schedule in self.warming_schedules:
            if schedule.last_warmed:
                next_time = schedule.last_warmed + timedelta(minutes=schedule.frequency_minutes)
            else:
                next_time = datetime.utcnow()
            
            if next_warming is None or next_time < next_warming:
                next_warming = next_time
        
        return next_warming.isoformat() if next_warming else None
    
    def get_schedule_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about all warming schedules."""
        return [
            {
                "service_type": schedule.service_type.value,
                "provider": schedule.provider,
                "region": schedule.region,
                "priority": schedule.priority.name,
                "frequency_minutes": schedule.frequency_minutes,
                "params": schedule.params,
                "last_warmed": schedule.last_warmed.isoformat() if schedule.last_warmed else None,
                "warming_count": schedule.warming_count,
                "error_count": schedule.error_count,
                "avg_warming_time": round(schedule.avg_warming_time, 2),
                "needs_warming": self._should_warm_schedule(schedule),
                "success_rate": (
                    (schedule.warming_count / (schedule.warming_count + schedule.error_count) * 100)
                    if (schedule.warming_count + schedule.error_count) > 0 else 0.0
                )
            }
            for schedule in self.warming_schedules
        ]
    
    async def optimize_schedules(self) -> Dict[str, Any]:
        """
        Optimize warming schedules based on cache hit rates and usage patterns.
        
        Returns:
            Dictionary with optimization results and recommendations
        """
        optimization_report = await self.unified_cache.get_cache_optimization_report()
        service_metrics = optimization_report.get("service_metrics", {})
        
        optimizations_made = 0
        recommendations = []
        
        for schedule in self.warming_schedules:
            service_key = f"{schedule.provider}:{schedule.service_type.value}"
            
            if service_key in service_metrics:
                metrics = service_metrics[service_key]
                hit_rate = metrics.get("hit_rate", 0.0)
                
                # Optimize frequency based on hit rate
                if hit_rate > 95.0 and schedule.frequency_minutes < 240:
                    # Very high hit rate - can reduce warming frequency
                    new_frequency = min(schedule.frequency_minutes * 2, 240)
                    recommendations.append({
                        "type": "reduce_frequency",
                        "schedule": f"{schedule.provider}:{schedule.service_type.value}:{schedule.region}",
                        "current_frequency": schedule.frequency_minutes,
                        "recommended_frequency": new_frequency,
                        "reason": f"High hit rate ({hit_rate}%) allows less frequent warming"
                    })
                    schedule.frequency_minutes = new_frequency
                    optimizations_made += 1
                
                elif hit_rate < 70.0 and schedule.frequency_minutes > 15:
                    # Low hit rate - increase warming frequency
                    new_frequency = max(schedule.frequency_minutes // 2, 15)
                    recommendations.append({
                        "type": "increase_frequency",
                        "schedule": f"{schedule.provider}:{schedule.service_type.value}:{schedule.region}",
                        "current_frequency": schedule.frequency_minutes,
                        "recommended_frequency": new_frequency,
                        "reason": f"Low hit rate ({hit_rate}%) requires more frequent warming"
                    })
                    schedule.frequency_minutes = new_frequency
                    optimizations_made += 1
        
        logger.info(f"Schedule optimization completed: {optimizations_made} optimizations made")
        
        return {
            "optimizations_made": optimizations_made,
            "recommendations": recommendations,
            "optimization_report": optimization_report
        }


# Global cache warming service instance
cache_warming_service: Optional[CacheWarmingService] = None


async def init_cache_warming_service(unified_cache: UnifiedCloudCacheManager) -> CacheWarmingService:
    """
    Initialize the global cache warming service.
    
    Args:
        unified_cache: Unified cloud cache manager instance
        
    Returns:
        Initialized cache warming service
    """
    global cache_warming_service
    
    cache_warming_service = CacheWarmingService(unified_cache)
    logger.info("Cache warming service initialized")
    
    return cache_warming_service


async def get_cache_warming_service() -> Optional[CacheWarmingService]:
    """Get the global cache warming service instance."""
    return cache_warming_service


async def cleanup_cache_warming_service():
    """Cleanup the cache warming service."""
    global cache_warming_service
    
    if cache_warming_service:
        await cache_warming_service.stop_warming_service()
        cache_warming_service = None
    
    logger.info("Cache warming service cleaned up")