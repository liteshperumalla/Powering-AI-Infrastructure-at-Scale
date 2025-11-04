"""
Response Caching Decorator - Redis-based caching for FastAPI endpoints.

Provides automatic caching of API responses with TTL support,
cache invalidation, and compression for large responses.
"""

import json
import hashlib
import gzip
from functools import wraps
from typing import Any, Optional, Callable
import redis.asyncio as aioredis
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client."""
    global _redis_client

    if _redis_client is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False  # We'll handle encoding ourselves
        )
        logger.info(f"Redis client connected: {redis_url}")

    return _redis_client


def cache_key_generator(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate cache key from function name and arguments.

    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Filter out non-serializable arguments (like Request objects)
    safe_kwargs = {}
    for key, value in kwargs.items():
        try:
            # Skip non-JSON-serializable objects
            if key in ['request', 'current_user', 'db']:
                continue
            # Try to serialize
            json.dumps(value)
            safe_kwargs[key] = value
        except (TypeError, ValueError):
            # Skip non-serializable values
            safe_kwargs[key] = str(type(value))

    # Create deterministic key
    key_data = {
        'func': func_name,
        'args': str(args),
        'kwargs': safe_kwargs
    }

    key_string = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()

    return f"cache:{func_name}:{key_hash}"


def compress_data(data: str) -> bytes:
    """Compress string data using gzip."""
    return gzip.compress(data.encode('utf-8'))


def decompress_data(data: bytes) -> str:
    """Decompress gzip data to string."""
    return gzip.decompress(data).decode('utf-8')


def cache_response(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    compress: bool = True,
    include_user: bool = True
):
    """
    Decorator to cache API endpoint responses in Redis.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache key
        compress: Whether to compress cached data (recommended for large responses)
        include_user: Whether to include user ID in cache key (for user-specific data)

    Example:
        @router.get("/dashboard/stats")
        @cache_response(ttl=300)  # Cache for 5 minutes
        async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
            # Expensive computation here
            return stats
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get Redis client
            try:
                redis = await get_redis_client()
            except Exception as e:
                logger.warning(f"Redis connection failed, bypassing cache: {e}")
                return await func(*args, **kwargs)

            # Generate cache key
            func_name = f"{key_prefix or func.__module__}.{func.__name__}"

            # Include user ID if requested
            if include_user and 'current_user' in kwargs:
                user = kwargs['current_user']
                user_id = getattr(user, 'id', None)
                if user_id:
                    func_name = f"{func_name}:user:{user_id}"

            cache_key = cache_key_generator(func_name, args, kwargs)

            # Try to get from cache
            try:
                cached_data = await redis.get(cache_key)

                if cached_data:
                    # Cache hit!
                    if compress:
                        cached_data = decompress_data(cached_data)
                    else:
                        cached_data = cached_data.decode('utf-8')

                    result = json.loads(cached_data)
                    logger.debug(f"Cache HIT: {cache_key}")

                    # Add cache metadata
                    if isinstance(result, dict):
                        result['_cached'] = True
                        result['_cache_key'] = cache_key

                    return result

            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                result_json = json.dumps(result)

                if compress:
                    cached_data = compress_data(result_json)
                else:
                    cached_data = result_json.encode('utf-8')

                await redis.setex(cache_key, ttl, cached_data)
                logger.debug(f"Cached result: {cache_key} (TTL: {ttl}s, Size: {len(cached_data)} bytes)")

            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result

        return wrapper
    return decorator


async def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "cache:assessments:*")

    Returns:
        Number of keys deleted
    """
    try:
        redis = await get_redis_client()

        # Find matching keys
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await redis.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted

        return 0

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


async def invalidate_cache_for_user(user_id: str, pattern: str = "*") -> int:
    """
    Invalidate all cache entries for a specific user.

    Args:
        user_id: User ID
        pattern: Additional pattern matching

    Returns:
        Number of keys deleted
    """
    full_pattern = f"cache:*:user:{user_id}:{pattern}"
    return await invalidate_cache(full_pattern)


async def get_cache_stats() -> dict:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    try:
        redis = await get_redis_client()

        info = await redis.info('stats')
        keyspace = await redis.info('keyspace')

        # Count cache keys
        cache_keys = 0
        async for _ in redis.scan_iter(match="cache:*"):
            cache_keys += 1

        return {
            "total_keys": cache_keys,
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "hit_rate": (
                info.get('keyspace_hits', 0) /
                (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
                * 100
            ),
            "memory_used": info.get('used_memory_human', 'unknown'),
            "connected_clients": info.get('connected_clients', 0)
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e)}


# Convenience decorators for common TTLs

def cache_short(func: Callable) -> Callable:
    """Cache for 1 minute (frequently changing data)."""
    return cache_response(ttl=60)(func)


def cache_medium(func: Callable) -> Callable:
    """Cache for 5 minutes (standard)."""
    return cache_response(ttl=300)(func)


def cache_long(func: Callable) -> Callable:
    """Cache for 1 hour (rarely changing data)."""
    return cache_response(ttl=3600)(func)


def cache_very_long(func: Callable) -> Callable:
    """Cache for 24 hours (static data)."""
    return cache_response(ttl=86400)(func)
