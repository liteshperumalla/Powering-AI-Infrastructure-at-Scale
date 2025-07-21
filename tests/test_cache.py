"""
Tests for the caching system.

Tests Redis-based caching and rate limiting functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from src.infra_mind.core.cache import CacheManager, RateLimiter, init_cache, cleanup_cache
from src.infra_mind.cloud.base import CloudProvider


@pytest.fixture
async def cache_manager():
    """Create a cache manager for testing."""
    # Use a test Redis URL or mock Redis
    cache_mgr = CacheManager("redis://localhost:6379/1", default_ttl=60)  # Use test DB 1
    
    try:
        await cache_mgr.connect()
        yield cache_mgr
    except Exception:
        # If Redis is not available, create a mock
        cache_mgr._connected = False
        yield cache_mgr
    finally:
        if cache_mgr._connected:
            await cache_mgr.disconnect()


@pytest.fixture
async def rate_limiter():
    """Create a rate limiter for testing."""
    cache_mgr = CacheManager("redis://localhost:6379/1", default_ttl=60)
    try:
        await cache_mgr.connect()
        limiter = RateLimiter(cache_mgr)
        yield limiter
    except Exception:
        cache_mgr._connected = False
        limiter = RateLimiter(cache_mgr)
        yield limiter
    finally:
        if cache_mgr._connected:
            await cache_mgr.disconnect()


class TestCacheManager:
    """Test the CacheManager class."""
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache_manager):
        """Test cache key generation."""
        key1 = cache_manager._generate_cache_key("aws", "ec2", "us-east-1")
        key2 = cache_manager._generate_cache_key("aws", "ec2", "us-east-1")
        key3 = cache_manager._generate_cache_key("aws", "ec2", "us-west-2")
        
        assert key1 == key2
        assert key1 != key3
        assert key1.startswith("cloud_api:aws:ec2:us-east-1")
    
    @pytest.mark.asyncio
    async def test_cache_key_with_params(self, cache_manager):
        """Test cache key generation with parameters."""
        params1 = {"service_id": "AmazonEC2"}
        params2 = {"service_id": "AmazonRDS"}
        
        key1 = cache_manager._generate_cache_key("aws", "pricing", "us-east-1", params1)
        key2 = cache_manager._generate_cache_key("aws", "pricing", "us-east-1", params2)
        
        assert key1 != key2
        assert "cloud_api:aws:pricing:us-east-1" in key1
        assert "cloud_api:aws:pricing:us-east-1" in key2
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        if not cache_manager._connected:
            pytest.skip("Redis not available for testing")
        
        test_data = {
            "services": ["ec2", "rds"],
            "pricing": {"ec2": 0.10, "rds": 0.20}
        }
        
        # Set cache
        success = await cache_manager.set("aws", "ec2", "us-east-1", test_data, ttl=60)
        assert success
        
        # Get cache
        cached_data = await cache_manager.get("aws", "ec2", "us-east-1")
        assert cached_data is not None
        assert cached_data["services"] == test_data["services"]
        assert cached_data["pricing"] == test_data["pricing"]
        assert "cached_at" in cached_data
        assert "provider" in cached_data
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """Test cache miss scenario."""
        cached_data = await cache_manager.get("aws", "nonexistent", "us-east-1")
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_manager):
        """Test cache deletion."""
        if not cache_manager._connected:
            pytest.skip("Redis not available for testing")
        
        test_data = {"test": "data"}
        
        # Set cache
        await cache_manager.set("aws", "test", "us-east-1", test_data)
        
        # Verify it exists
        cached_data = await cache_manager.get("aws", "test", "us-east-1")
        assert cached_data is not None
        
        # Delete cache
        deleted = await cache_manager.delete("aws", "test", "us-east-1")
        assert deleted
        
        # Verify it's gone
        cached_data = await cache_manager.get("aws", "test", "us-east-1")
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics."""
        stats = await cache_manager.get_cache_stats()
        
        if cache_manager._connected:
            assert stats["connected"] is True
            assert "total_keys" in stats
            assert "memory_used" in stats
        else:
            assert stats["connected"] is False


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_check_allowed(self, rate_limiter):
        """Test rate limit check when requests are allowed."""
        result = await rate_limiter.check_rate_limit("aws", "ec2")
        
        assert result["allowed"] is True
        assert "remaining" in result
        assert "reset_time" in result
        assert "limit" in result
    
    @pytest.mark.asyncio
    async def test_rate_limit_status(self, rate_limiter):
        """Test rate limit status check."""
        status = await rate_limiter.get_rate_limit_status("aws", "ec2")
        
        if rate_limiter.cache_manager._connected:
            assert status["available"] is True
            assert "limit" in status
            assert "current" in status
            assert "remaining" in status
        else:
            assert status["available"] is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_different_providers(self, rate_limiter):
        """Test rate limits for different providers."""
        aws_result = await rate_limiter.check_rate_limit("aws", "ec2")
        azure_result = await rate_limiter.check_rate_limit("azure", "compute")
        
        # Both should be allowed initially
        assert aws_result["allowed"] is True
        assert azure_result["allowed"] is True
        
        # Azure should have higher limits
        if rate_limiter.cache_manager._connected:
            assert azure_result["limit"] > aws_result["limit"]


class TestCacheIntegration:
    """Test cache integration with cloud clients."""
    
    @pytest.mark.asyncio
    async def test_init_and_cleanup_cache(self):
        """Test cache initialization and cleanup."""
        # Test initialization
        await init_cache("redis://localhost:6379/2")  # Use test DB 2
        
        # Test cleanup
        await cleanup_cache()
    
    @pytest.mark.asyncio
    async def test_cache_with_mock_redis(self):
        """Test cache behavior when Redis is not available."""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Redis not available")
            
            cache_mgr = CacheManager("redis://localhost:6379")
            
            # Should handle connection failure gracefully
            with pytest.raises(Exception):
                await cache_mgr.connect()
            
            # Cache operations should return None/False when not connected
            result = await cache_mgr.get("aws", "ec2", "us-east-1")
            assert result is None
            
            success = await cache_mgr.set("aws", "ec2", "us-east-1", {"test": "data"})
            assert success is False


class TestCacheWithCloudClients:
    """Test cache integration with actual cloud clients."""
    
    @pytest.mark.asyncio
    async def test_cached_fetch_method(self):
        """Test the _get_cached_or_fetch method."""
        from src.infra_mind.cloud.aws import AWSClient
        from src.infra_mind.cloud.base import CloudServiceError
        
        # Mock the fetch function
        async def mock_fetch():
            return {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        
        # Create a mock AWS client
        with patch('src.infra_mind.cloud.aws.AWSClient._validate_credentials'):
            client = AWSClient()
            
            # Test successful fetch and cache
            result = await client._get_cached_or_fetch(
                service="test",
                region="us-east-1",
                fetch_func=mock_fetch,
                cache_ttl=60
            )
            
            assert result is not None
            assert result["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback(self):
        """Test fallback to cached data when rate limited."""
        from src.infra_mind.cloud.aws import AWSClient
        
        # Mock rate limiter to return rate limit exceeded
        with patch('src.infra_mind.core.cache.rate_limiter.check_rate_limit') as mock_rate_check:
            mock_rate_check.return_value = {
                "allowed": False,
                "remaining": 0,
                "reset_time": (datetime.utcnow() + timedelta(minutes=1)).isoformat()
            }
            
            # Mock cache to return stale data
            with patch('src.infra_mind.core.cache.cache_manager.get') as mock_cache_get:
                mock_cache_get.return_value = {
                    "test": "stale_data",
                    "cached_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
                }
                
                with patch('src.infra_mind.cloud.aws.AWSClient._validate_credentials'):
                    client = AWSClient()
                    
                    async def mock_fetch():
                        return {"test": "fresh_data"}
                    
                    result = await client._get_cached_or_fetch(
                        service="test",
                        region="us-east-1",
                        fetch_func=mock_fetch
                    )
                    
                    # Should return stale data with rate limit flags
                    assert result["test"] == "stale_data"
                    assert result["is_stale"] is True
                    assert result["rate_limited"] is True


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(pytest.main([__file__, "-v"]))