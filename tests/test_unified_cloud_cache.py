"""
Tests for unified cloud service caching system.

Tests the comprehensive caching solution that integrates with all cloud providers
including Terraform, with intelligent cache invalidation, warming, and monitoring.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.infra_mind.core.unified_cloud_cache import (
    UnifiedCloudCacheManager, ServiceType, CacheWarmingEntry,
    CacheOptimizationMetrics, init_unified_cache, get_unified_cache_manager
)
from src.infra_mind.core.cache_warming_service import (
    CacheWarmingService, WarmingPriority, WarmingSchedule,
    init_cache_warming_service, get_cache_warming_service
)
from src.infra_mind.core.cache import ProductionCacheManager, CacheConfig, CacheStrategy


class TestUnifiedCloudCacheManager:
    """Test unified cloud cache manager functionality."""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock production cache manager."""
        config = CacheConfig(redis_url="redis://localhost:6379")
        cache_manager = MagicMock(spec=ProductionCacheManager)
        
        # Mock async methods
        cache_manager.get = AsyncMock()
        cache_manager.set = AsyncMock()
        cache_manager.invalidate_by_pattern = AsyncMock()
        cache_manager.invalidate_provider_cache = AsyncMock()
        cache_manager.invalidate_by_tag = AsyncMock()
        cache_manager.get_cache_stats = AsyncMock()
        
        return cache_manager
    
    @pytest.fixture
    def unified_cache(self, mock_cache_manager):
        """Create unified cache manager with mock."""
        return UnifiedCloudCacheManager(mock_cache_manager)
    
    @pytest.mark.asyncio
    async def test_service_type_ttl_configuration(self, unified_cache):
        """Test that different service types have appropriate TTL configurations."""
        # Verify TTL configurations
        assert unified_cache.service_ttls[ServiceType.PRICING] == 3600  # 1 hour
        assert unified_cache.service_ttls[ServiceType.COMPUTE] == 1800  # 30 minutes
        assert unified_cache.service_ttls[ServiceType.COST_ESTIMATION] == 900  # 15 minutes
        assert unified_cache.service_ttls[ServiceType.TERRAFORM_MODULES] == 86400  # 24 hours
        assert unified_cache.service_ttls[ServiceType.REGIONS] == 604800  # 7 days
    
    @pytest.mark.asyncio
    async def test_service_strategy_configuration(self, unified_cache):
        """Test that different service types have appropriate cache strategies."""
        # Verify strategy configurations
        assert unified_cache.service_strategies[ServiceType.PRICING] == CacheStrategy.REFRESH_AHEAD
        assert unified_cache.service_strategies[ServiceType.COMPUTE] == CacheStrategy.REFRESH_AHEAD
        assert unified_cache.service_strategies[ServiceType.COST_ESTIMATION] == CacheStrategy.REFRESH_AHEAD
        assert unified_cache.service_strategies[ServiceType.TERRAFORM_MODULES] == CacheStrategy.TTL_ONLY
        assert unified_cache.service_strategies[ServiceType.REGIONS] == CacheStrategy.TTL_ONLY
    
    @pytest.mark.asyncio
    async def test_get_cached_data_success(self, unified_cache, mock_cache_manager):
        """Test successful cache data retrieval."""
        # Setup mock response
        cached_data = {
            "services": [{"name": "test-service", "price": 0.10}],
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_cache_manager.get.return_value = cached_data
        
        # Test cache retrieval
        result = await unified_cache.get_cached_data(
            provider="aws",
            service_type=ServiceType.COMPUTE,
            region="us-east-1"
        )
        
        # Verify result
        assert result == cached_data
        mock_cache_manager.get.assert_called_once_with(
            provider="aws",
            service="compute",
            region="us-east-1",
            params=None,
            allow_stale=False,
            strategy=CacheStrategy.REFRESH_AHEAD
        )
    
    @pytest.mark.asyncio
    async def test_set_cached_data_success(self, unified_cache, mock_cache_manager):
        """Test successful cache data storage."""
        # Setup mock response
        mock_cache_manager.set.return_value = True
        
        test_data = {
            "services": [{"name": "test-service", "price": 0.10}],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test cache storage
        result = await unified_cache.set_cached_data(
            provider="aws",
            service_type=ServiceType.COMPUTE,
            region="us-east-1",
            data=test_data,
            tags=["test"]
        )
        
        # Verify result
        assert result is True
        mock_cache_manager.set.assert_called_once()
        
        # Verify call arguments
        call_args = mock_cache_manager.set.call_args
        assert call_args[1]["provider"] == "aws"
        assert call_args[1]["service"] == "compute"
        assert call_args[1]["region"] == "us-east-1"
        assert call_args[1]["data"] == test_data
        assert call_args[1]["ttl"] == 1800  # 30 minutes for compute
        assert call_args[1]["strategy"] == CacheStrategy.REFRESH_AHEAD
        
        # Verify tags include service-specific tags
        tags = call_args[1]["tags"]
        assert "test" in tags
        assert "provider:aws" in tags
        assert "service_type:compute" in tags
        assert "region:us-east-1" in tags
    
    @pytest.mark.asyncio
    async def test_invalidate_service_cache(self, unified_cache, mock_cache_manager):
        """Test service-specific cache invalidation."""
        mock_cache_manager.invalidate_by_pattern.return_value = 5
        
        # Test service cache invalidation
        result = await unified_cache.invalidate_service_cache(
            provider="aws",
            service_type=ServiceType.COMPUTE,
            region="us-east-1"
        )
        
        # Verify result
        assert result == 5
        mock_cache_manager.invalidate_by_pattern.assert_called_once_with(
            "cloud_api:aws:compute:us-east-1:*"
        )
    
    @pytest.mark.asyncio
    async def test_invalidate_service_cache_all_regions(self, unified_cache, mock_cache_manager):
        """Test service cache invalidation for all regions."""
        mock_cache_manager.invalidate_by_pattern.return_value = 15
        
        # Test service cache invalidation without region
        result = await unified_cache.invalidate_service_cache(
            provider="aws",
            service_type=ServiceType.COMPUTE
        )
        
        # Verify result
        assert result == 15
        mock_cache_manager.invalidate_by_pattern.assert_called_once_with(
            "cloud_api:aws:compute:*"
        )
    
    @pytest.mark.asyncio
    async def test_invalidate_provider_cache(self, unified_cache, mock_cache_manager):
        """Test provider-specific cache invalidation."""
        mock_cache_manager.invalidate_provider_cache.return_value = 25
        
        # Test provider cache invalidation
        result = await unified_cache.invalidate_provider_cache("aws")
        
        # Verify result
        assert result == 25
        mock_cache_manager.invalidate_provider_cache.assert_called_once_with("aws")
    
    @pytest.mark.asyncio
    async def test_invalidate_by_tags(self, unified_cache, mock_cache_manager):
        """Test tag-based cache invalidation."""
        mock_cache_manager.invalidate_by_tag.return_value = 3
        
        # Test tag-based invalidation
        result = await unified_cache.invalidate_by_tags(["tag1", "tag2"])
        
        # Verify result
        assert result == 6  # 3 + 3
        assert mock_cache_manager.invalidate_by_tag.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_optimization_report(self, unified_cache, mock_cache_manager):
        """Test cache optimization report generation."""
        # Setup mock cache stats
        mock_cache_stats = {
            "connected": True,
            "total_keys": 100,
            "memory_used": "10MB",
            "performance_metrics": {"hits": 80, "misses": 20}
        }
        mock_cache_manager.get_cache_stats.return_value = mock_cache_stats
        
        # Add some test metrics
        unified_cache.optimization_metrics["aws:compute"] = CacheOptimizationMetrics(
            service_type=ServiceType.COMPUTE,
            provider="aws",
            hit_rate=85.0,
            miss_rate=15.0,
            avg_response_time=50.0,
            data_staleness_avg=300.0,
            cost_savings=100.0,
            optimization_score=85.0
        )
        
        # Test report generation
        report = await unified_cache.get_cache_optimization_report()
        
        # Verify report structure
        assert "timestamp" in report
        assert "overall_optimization_score" in report
        assert "cache_stats" in report
        assert "service_metrics" in report
        assert "recommendations" in report
        
        # Verify service metrics
        assert "aws:compute" in report["service_metrics"]
        service_metric = report["service_metrics"]["aws:compute"]
        assert service_metric["hit_rate"] == 85.0
        assert service_metric["optimization_score"] == 85.0
        assert service_metric["ttl_seconds"] == 1800  # 30 minutes for compute
    
    @pytest.mark.asyncio
    async def test_warming_entry_management(self, unified_cache):
        """Test cache warming entry management."""
        # Get initial count of entries
        initial_entries = await unified_cache.get_warming_entries()
        initial_count = len(initial_entries)
        
        # Test adding warming entry
        await unified_cache.add_warming_entry(
            provider="aws",
            service_type=ServiceType.PRICING,
            region="us-west-2",
            params={"service_id": "ec2"},
            priority=1,
            frequency_hours=2
        )
        
        # Verify entry was added
        entries = await unified_cache.get_warming_entries()
        assert len(entries) == initial_count + 1
        
        new_entry = next((e for e in entries if e["region"] == "us-west-2" and 
                         e["service_type"] == "pricing" and 
                         e["params"] == {"service_id": "ec2"}), None)
        assert new_entry is not None
        assert new_entry["provider"] == "aws"
        assert new_entry["priority"] == 1
        assert new_entry["frequency_hours"] == 2
        
        # Test removing warming entry
        removed = await unified_cache.remove_warming_entry(
            provider="aws",
            service_type=ServiceType.PRICING,
            region="us-west-2",
            params={"service_id": "ec2"}
        )
        
        # Verify entry was removed
        assert removed is True
        entries_after = await unified_cache.get_warming_entries()
        assert len(entries_after) == initial_count
        
        removed_entry = next((e for e in entries_after if e["region"] == "us-west-2" and 
                             e["service_type"] == "pricing" and 
                             e["params"] == {"service_id": "ec2"}), None)
        assert removed_entry is None


class TestCacheWarmingService:
    """Test cache warming service functionality."""
    
    @pytest.fixture
    def mock_unified_cache(self):
        """Create mock unified cache manager."""
        cache = MagicMock(spec=UnifiedCloudCacheManager)
        cache.set_cached_data = AsyncMock()
        cache.get_cache_optimization_report = AsyncMock()
        return cache
    
    @pytest.fixture
    def warming_service(self, mock_unified_cache):
        """Create cache warming service with mock."""
        return CacheWarmingService(mock_unified_cache)
    
    @pytest.mark.asyncio
    async def test_default_schedules_initialization(self, warming_service):
        """Test that default warming schedules are properly initialized."""
        schedules = warming_service.warming_schedules
        
        # Verify we have schedules for all major providers
        aws_schedules = [s for s in schedules if s.provider == "aws"]
        azure_schedules = [s for s in schedules if s.provider == "azure"]
        gcp_schedules = [s for s in schedules if s.provider == "gcp"]
        terraform_schedules = [s for s in schedules if s.provider == "terraform"]
        
        assert len(aws_schedules) > 0
        assert len(azure_schedules) > 0
        assert len(gcp_schedules) > 0
        assert len(terraform_schedules) > 0
        
        # Verify critical services have high priority
        critical_schedules = [s for s in schedules if s.priority == WarmingPriority.CRITICAL]
        assert len(critical_schedules) > 0
        
        # Verify pricing and compute are critical
        pricing_schedules = [s for s in critical_schedules if s.service_type == ServiceType.PRICING]
        compute_schedules = [s for s in critical_schedules if s.service_type == ServiceType.COMPUTE]
        assert len(pricing_schedules) > 0
        assert len(compute_schedules) > 0
    
    @pytest.mark.asyncio
    async def test_register_fetch_function(self, warming_service):
        """Test fetch function registration."""
        async def mock_fetch_func(region, **kwargs):
            return {"test": "data"}
        
        # Test registration
        warming_service.register_fetch_function("aws_compute", mock_fetch_func)
        
        # Verify registration
        assert "aws_compute" in warming_service.fetch_functions
        assert warming_service.fetch_functions["aws_compute"] == mock_fetch_func
    
    @pytest.mark.asyncio
    async def test_add_remove_warming_schedule(self, warming_service):
        """Test adding and removing warming schedules."""
        initial_count = len(warming_service.warming_schedules)
        
        # Test adding schedule
        warming_service.add_warming_schedule(
            service_type=ServiceType.AI_ML,
            provider="aws",
            region="us-west-1",
            priority=WarmingPriority.MEDIUM,
            frequency_minutes=120,
            params={"model_type": "inference"}
        )
        
        # Verify schedule was added
        assert len(warming_service.warming_schedules) == initial_count + 1
        new_schedule = warming_service.warming_schedules[-1]
        assert new_schedule.service_type == ServiceType.AI_ML
        assert new_schedule.provider == "aws"
        assert new_schedule.region == "us-west-1"
        assert new_schedule.params == {"model_type": "inference"}
        
        # Test removing schedule
        removed = warming_service.remove_warming_schedule(
            service_type=ServiceType.AI_ML,
            provider="aws",
            region="us-west-1",
            params={"model_type": "inference"}
        )
        
        # Verify schedule was removed
        assert removed is True
        assert len(warming_service.warming_schedules) == initial_count
    
    @pytest.mark.asyncio
    async def test_should_warm_schedule(self, warming_service):
        """Test schedule warming logic."""
        # Create test schedule
        schedule = WarmingSchedule(
            service_type=ServiceType.COMPUTE,
            provider="aws",
            region="us-east-1",
            priority=WarmingPriority.HIGH,
            frequency_minutes=60
        )
        
        # Test new schedule (never warmed)
        assert warming_service._should_warm_schedule(schedule) is True
        
        # Test recently warmed schedule
        schedule.last_warmed = datetime.utcnow() - timedelta(minutes=30)
        assert warming_service._should_warm_schedule(schedule) is False
        
        # Test schedule due for warming
        schedule.last_warmed = datetime.utcnow() - timedelta(minutes=70)
        assert warming_service._should_warm_schedule(schedule) is True
        
        # Test critical service with flexibility
        schedule.priority = WarmingPriority.CRITICAL
        schedule.last_warmed = datetime.utcnow() - timedelta(minutes=50)  # 80% of 60 minutes
        assert warming_service._should_warm_schedule(schedule) is True
    
    @pytest.mark.asyncio
    async def test_warm_single_schedule_success(self, warming_service, mock_unified_cache):
        """Test successful warming of a single schedule."""
        # Setup mock fetch function
        async def mock_fetch_func(region, **kwargs):
            return {"services": [{"name": "test", "price": 0.10}]}
        
        warming_service.register_fetch_function("aws_compute", mock_fetch_func)
        mock_unified_cache.set_cached_data.return_value = True
        
        # Create test schedule
        schedule = WarmingSchedule(
            service_type=ServiceType.COMPUTE,
            provider="aws",
            region="us-east-1",
            priority=WarmingPriority.HIGH,
            frequency_minutes=60
        )
        
        # Test warming
        result = await warming_service.warm_single_schedule(schedule)
        
        # Verify success
        assert result is True
        assert schedule.last_warmed is not None
        assert schedule.warming_count == 1
        assert schedule.error_count == 0
        assert schedule.avg_warming_time > 0
        
        # Verify cache was called
        mock_unified_cache.set_cached_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_warm_single_schedule_failure(self, warming_service, mock_unified_cache):
        """Test failed warming of a single schedule."""
        # Setup mock fetch function that raises exception
        async def mock_fetch_func(region, **kwargs):
            raise Exception("API error")
        
        warming_service.register_fetch_function("aws_compute", mock_fetch_func)
        
        # Create test schedule
        schedule = WarmingSchedule(
            service_type=ServiceType.COMPUTE,
            provider="aws",
            region="us-east-1",
            priority=WarmingPriority.HIGH,
            frequency_minutes=60
        )
        
        # Test warming
        result = await warming_service.warm_single_schedule(schedule)
        
        # Verify failure
        assert result is False
        assert schedule.error_count == 1
        assert schedule.warming_count == 0
    
    @pytest.mark.asyncio
    async def test_run_warming_cycle(self, warming_service, mock_unified_cache):
        """Test complete warming cycle execution."""
        # Setup mock fetch functions
        async def mock_aws_compute(region, **kwargs):
            return {"services": [{"name": "ec2", "price": 0.10}]}
        
        async def mock_aws_pricing(region, **kwargs):
            return {"pricing": [{"service": "ec2", "price": 0.10}]}
        
        warming_service.register_fetch_function("aws_compute", mock_aws_compute)
        warming_service.register_fetch_function("aws_pricing", mock_aws_pricing)
        mock_unified_cache.set_cached_data.return_value = True
        
        # Clear existing schedules and add test schedules
        warming_service.warming_schedules = [
            WarmingSchedule(ServiceType.COMPUTE, "aws", "us-east-1", WarmingPriority.CRITICAL, 30),
            WarmingSchedule(ServiceType.PRICING, "aws", "us-east-1", WarmingPriority.CRITICAL, 30),
        ]
        
        # Run warming cycle
        results = await warming_service.run_warming_cycle()
        
        # Verify results
        assert results["schedules_processed"] == 2
        assert results["successful_warmings"] == 2
        assert results["failed_warmings"] == 0
        assert results["cycle_time"] > 0
        assert "priority_breakdown" in results
    
    @pytest.mark.asyncio
    async def test_warming_service_lifecycle(self, warming_service):
        """Test starting and stopping warming service."""
        # Test service is not running initially
        assert warming_service.is_running is False
        
        # Start service with short interval for testing
        await warming_service.start_warming_service(cycle_interval_minutes=1)
        
        # Verify service is running
        assert warming_service.is_running is True
        assert warming_service.warming_task is not None
        
        # Wait a short time to ensure task is running
        await asyncio.sleep(0.1)
        
        # Stop service
        await warming_service.stop_warming_service()
        
        # Verify service is stopped
        assert warming_service.is_running is False
        assert warming_service.warming_task is None
    
    @pytest.mark.asyncio
    async def test_warming_status(self, warming_service):
        """Test warming service status reporting."""
        # Get status
        status = warming_service.get_warming_status()
        
        # Verify status structure
        assert "is_running" in status
        assert "total_schedules" in status
        assert "schedules_needing_warming" in status
        assert "schedules_by_priority" in status
        assert "schedules_by_provider" in status
        assert "registered_fetch_functions" in status
        assert "warming_statistics" in status
        
        # Verify statistics structure
        stats = status["warming_statistics"]
        assert "total_warmings" in stats
        assert "successful_warmings" in stats
        assert "failed_warmings" in stats
    
    @pytest.mark.asyncio
    async def test_schedule_optimization(self, warming_service, mock_unified_cache):
        """Test schedule optimization based on cache metrics."""
        # Setup mock optimization report
        mock_report = {
            "service_metrics": {
                "aws:compute": {"hit_rate": 95.0},  # High hit rate
                "aws:pricing": {"hit_rate": 60.0},  # Low hit rate
            }
        }
        mock_unified_cache.get_cache_optimization_report.return_value = mock_report
        
        # Add test schedules
        warming_service.warming_schedules = [
            WarmingSchedule(ServiceType.COMPUTE, "aws", "us-east-1", WarmingPriority.HIGH, 60),
            WarmingSchedule(ServiceType.PRICING, "aws", "us-east-1", WarmingPriority.HIGH, 60),
        ]
        
        # Run optimization
        results = await warming_service.optimize_schedules()
        
        # Verify optimization results
        assert "optimizations_made" in results
        assert "recommendations" in results
        assert results["optimizations_made"] >= 0
        
        # Check if schedules were optimized
        compute_schedule = next(s for s in warming_service.warming_schedules 
                              if s.service_type == ServiceType.COMPUTE)
        pricing_schedule = next(s for s in warming_service.warming_schedules 
                              if s.service_type == ServiceType.PRICING)
        
        # High hit rate service should have longer frequency (or unchanged if already optimal)
        # Low hit rate service should have shorter frequency (or unchanged if already optimal)
        assert compute_schedule.frequency_minutes >= 60
        assert pricing_schedule.frequency_minutes <= 60


class TestIntegration:
    """Integration tests for unified caching system."""
    
    @pytest.mark.asyncio
    async def test_full_caching_workflow(self):
        """Test complete caching workflow from initialization to warming."""
        # This would be a more comprehensive integration test
        # For now, we'll test the basic workflow
        
        # Mock cache manager
        mock_cache_manager = MagicMock(spec=ProductionCacheManager)
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock(return_value=True)
        mock_cache_manager.get_cache_stats = AsyncMock(return_value={"connected": True})
        
        # Initialize unified cache
        unified_cache = UnifiedCloudCacheManager(mock_cache_manager)
        
        # Initialize warming service
        warming_service = CacheWarmingService(unified_cache)
        
        # Register a test fetch function
        async def test_fetch(region, **kwargs):
            return {"test_data": f"data_for_{region}"}
        
        warming_service.register_fetch_function("aws_compute", test_fetch)
        
        # Test cache miss and set
        cached_data = await unified_cache.get_cached_data("aws", ServiceType.COMPUTE, "us-east-1")
        assert cached_data is None  # Cache miss
        
        # Set data in cache
        test_data = {"services": [{"name": "test", "price": 0.10}]}
        success = await unified_cache.set_cached_data("aws", ServiceType.COMPUTE, "us-east-1", test_data)
        assert success is True
        
        # Test warming
        schedule = WarmingSchedule(ServiceType.COMPUTE, "aws", "us-east-1", WarmingPriority.HIGH, 60)
        warming_result = await warming_service.warm_single_schedule(schedule)
        assert warming_result is True
        
        # Test optimization report
        report = await unified_cache.get_cache_optimization_report()
        assert "timestamp" in report
        assert "cache_stats" in report


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])