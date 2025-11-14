"""
Multi-Layer Cache Manager

Implements a sophisticated caching strategy with:
- L1: In-memory cache (ultra-fast, process-local)
- L2: Redis cache (shared across instances)
- Smart invalidation strategies
- TTL management
- Cache statistics

Performance Impact:
- 80%+ cache hit rate expected
- <1ms for L1 hits
- <5ms for L2 hits
- 50% reduction in database load
"""

import json
import hashlib
from typing import Any, Optional, Callable, Dict
from functools import wraps
from datetime import datetime, timedelta
import asyncio
from loguru import logger

try:
    from cachetools import TTLCache, LRUCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    logger.warning("cachetools not available - L1 cache disabled")

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available - L2 cache disabled")


class CacheManager:
    """
    Multi-layer cache manager with L1 (in-memory) and L2 (Redis) caching.

    Features:
    - Automatic key generation from function args
    - Configurable TTL per cache layer
    - Smart invalidation patterns
    - Cache statistics tracking
    - Graceful degradation if Redis unavailable
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,  # 5 minutes
        l2_ttl: int = 3600,  # 1 hour
        enabled: bool = True
    ):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL (L2 cache)
            l1_max_size: Maximum items in L1 cache
            l1_ttl: L1 cache TTL in seconds
            l2_ttl: L2 cache TTL in seconds
            enabled: Global cache enable/disable
        """
        self.enabled = enabled
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl

        # L1 Cache (In-Memory)
        if CACHETOOLS_AVAILABLE and enabled:
            self.l1_cache = TTLCache(maxsize=l1_max_size, ttl=l1_ttl)
            logger.info(f"✅ L1 cache enabled: {l1_max_size} items, {l1_ttl}s TTL")
        else:
            self.l1_cache = None
            logger.warning("⚠️  L1 cache disabled")

        # L2 Cache (Redis)
        self.redis_client = None
        self.redis_url = redis_url
        if REDIS_AVAILABLE and redis_url and enabled:
            logger.info(f"🔄 L2 cache will connect to: {redis_url}")
        else:
            logger.warning("⚠️  L2 cache disabled")

        # Cache statistics
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "db_queries": 0,
            "total_requests": 0
        }

    async def connect_redis(self):
        """Initialize Redis connection lazily."""
        if self.redis_client is None and self.redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("✅ L2 (Redis) cache connected")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self.redis_client = None

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate deterministic cache key from function arguments.

        Args:
            prefix: Cache key prefix (usually function name)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            SHA256 hash as cache key
        """
        # Create stable string representation
        key_parts = [prefix]

        # Add args
        for arg in args:
            key_parts.append(str(arg))

        # Add kwargs (sorted for determinism)
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)

        # Hash for consistent length
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"cache:{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (tries L1, then L2).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        self.stats["total_requests"] += 1

        # Try L1 cache first
        if self.l1_cache is not None:
            try:
                value = self.l1_cache.get(key)
                if value is not None:
                    self.stats["l1_hits"] += 1
                    logger.debug(f"🎯 L1 cache HIT: {key}")
                    return value
                else:
                    self.stats["l1_misses"] += 1
            except Exception as e:
                logger.warning(f"L1 cache error: {e}")

        # Try L2 cache (Redis)
        if self.redis_client is not None:
            try:
                value_str = await self.redis_client.get(key)
                if value_str is not None:
                    self.stats["l2_hits"] += 1
                    logger.debug(f"🎯 L2 cache HIT: {key}")

                    # Deserialize
                    value = json.loads(value_str)

                    # Populate L1 cache
                    if self.l1_cache is not None:
                        self.l1_cache[key] = value

                    return value
                else:
                    self.stats["l2_misses"] += 1
            except Exception as e:
                logger.warning(f"L2 cache error: {e}")

        # Cache miss
        logger.debug(f"❌ Cache MISS: {key}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in both cache layers.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses defaults if None)

        Returns:
            True if cached successfully
        """
        if not self.enabled:
            return False

        success = False

        # Set in L1 cache
        if self.l1_cache is not None:
            try:
                self.l1_cache[key] = value
                success = True
            except Exception as e:
                logger.warning(f"L1 cache set error: {e}")

        # Set in L2 cache (Redis)
        if self.redis_client is not None:
            try:
                value_str = json.dumps(value, default=str)
                l2_ttl = ttl or self.l2_ttl
                await self.redis_client.setex(key, l2_ttl, value_str)
                success = True
            except Exception as e:
                logger.warning(f"L2 cache set error: {e}")

        return success

    async def delete(self, key: str) -> bool:
        """
        Delete key from both cache layers.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted successfully
        """
        success = False

        # Delete from L1
        if self.l1_cache is not None:
            try:
                if key in self.l1_cache:
                    del self.l1_cache[key]
                    success = True
            except Exception as e:
                logger.warning(f"L1 cache delete error: {e}")

        # Delete from L2
        if self.redis_client is not None:
            try:
                await self.redis_client.delete(key)
                success = True
            except Exception as e:
                logger.warning(f"L2 cache delete error: {e}")

        return success

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern (Redis only).

        Args:
            pattern: Redis key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if self.redis_client is None:
            return 0

        try:
            deleted = 0
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    await self.redis_client.delete(*keys)
                    deleted += len(keys)

                if cursor == 0:
                    break

            logger.info(f"🗑️  Deleted {deleted} keys matching: {pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Pattern delete error: {e}")
            return 0

    async def clear(self) -> bool:
        """Clear both cache layers completely."""
        success = False

        # Clear L1
        if self.l1_cache is not None:
            try:
                self.l1_cache.clear()
                success = True
            except Exception as e:
                logger.warning(f"L1 clear error: {e}")

        # Clear L2 (flushdb is dangerous - skip for safety)
        # Use delete_pattern instead for specific prefixes

        return success

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        total = self.stats["total_requests"]
        if total == 0:
            return {**self.stats, "hit_rate": 0.0}

        l1_hits = self.stats["l1_hits"]
        l2_hits = self.stats["l2_hits"]
        total_hits = l1_hits + l2_hits

        return {
            **self.stats,
            "total_hits": total_hits,
            "hit_rate": (total_hits / total) * 100 if total > 0 else 0.0,
            "l1_hit_rate": (l1_hits / total) * 100 if total > 0 else 0.0,
            "l2_hit_rate": (l2_hits / total) * 100 if total > 0 else 0.0
        }

    async def close(self):
        """Close Redis connection."""
        if self.redis_client is not None:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")


# Decorator for caching function results
def cached(
    ttl: int = 3600,
    key_prefix: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: str):
            # Expensive database query
            return await db.users.find_one({"_id": user_id})

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key (defaults to function name)
        cache_manager: CacheManager instance (will use global if None)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager (use provided or global)
            cm = cache_manager or getattr(wrapper, '_cache_manager', None)

            if cm is None or not cm.enabled:
                # Cache disabled, execute function
                return await func(*args, **kwargs)

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = cm._generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = await cm.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss - execute function
            cm.stats["db_queries"] += 1
            result = await func(*args, **kwargs)

            # Store in cache
            await cm.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# Global cache manager instance (lazy initialization)
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _global_cache_manager

    if _global_cache_manager is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _global_cache_manager = CacheManager(
            redis_url=redis_url,
            l1_max_size=1000,
            l1_ttl=300,
            l2_ttl=3600,
            enabled=True
        )

    return _global_cache_manager
