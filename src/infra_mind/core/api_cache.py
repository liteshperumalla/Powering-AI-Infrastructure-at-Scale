"""
Production-Grade API Response Caching System.

Implements multi-layer caching strategy with Redis for optimal API performance:
- Response caching with automatic invalidation
- Smart cache key generation
- Cache warming and preloading
- Compression for large responses
- Cache metrics and monitoring

Features:
- Automatic cache invalidation on data updates
- Configurable TTL per endpoint
- Cache bypass for authenticated requests
- Compression for responses > 1KB
- Cache hit/miss metrics

Usage:
```python
from infra_mind.core.api_cache import cached_endpoint, invalidate_cache

@app.get("/api/assessments")
@cached_endpoint(ttl=300, key_prefix="assessments:list")
async def list_assessments():
    return await Assessment.find_all().to_list()

# Invalidate on updates
@app.post("/api/assessments")
async def create_assessment(data: AssessmentCreate):
    assessment = await Assessment(**data.dict()).insert()
    await invalidate_cache(pattern="assessments:*")
    return assessment
```
"""

import asyncio
import hashlib
import json
import gzip
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
import pickle

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from loguru import logger

from .config import settings


class CacheMetrics:
    """Track cache performance metrics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.invalidations = 0
        self.errors = 0
        self.total_response_time_saved = 0.0

    def record_hit(self, time_saved: float = 0.0):
        """Record cache hit."""
        self.hits += 1
        self.total_response_time_saved += time_saved

    def record_miss(self):
        """Record cache miss."""
        self.misses += 1

    def record_set(self):
        """Record cache set operation."""
        self.sets += 1

    def record_invalidation(self):
        """Record cache invalidation."""
        self.invalidations += 1

    def record_error(self):
        """Record cache error."""
        self.errors += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "invalidations": self.invalidations,
            "errors": self.errors,
            "hit_rate": self.get_hit_rate(),
            "time_saved_seconds": self.total_response_time_saved,
        }


class APICache:
    """Production-grade API response cache with Redis."""

    def __init__(self):
        """Initialize API cache."""
        self.redis: Optional[aioredis.Redis] = None
        self.metrics = CacheMetrics()
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.enabled = True

    async def connect(self):
        """Connect to Redis."""
        if self.redis:
            return

        try:
            redis_url = settings.redis_url or "redis://localhost:6379"
            self.redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding
                max_connections=50,
            )

            # Test connection
            await self.redis.ping()
            logger.info(f" API Cache connected to Redis: {redis_url}")

        except Exception as e:
            logger.error(f"L Failed to connect to Redis for caching: {e}")
            self.enabled = False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("API Cache disconnected from Redis")

    def _generate_cache_key(
        self,
        prefix: str,
        request: Request,
        include_user: bool = False,
        **kwargs
    ) -> str:
        """
        Generate cache key from request parameters.

        Args:
            prefix: Cache key prefix (e.g., "assessments:list")
            request: FastAPI request object
            include_user: Include user ID in cache key
            **kwargs: Additional parameters to include in key

        Returns:
            Cache key string
        """
        # Start with prefix
        key_parts = [prefix]

        # Add query parameters
        if request.query_params:
            query_string = str(sorted(request.query_params.items()))
            query_hash = hashlib.md5(query_string.encode()).hexdigest()[:8]
            key_parts.append(f"q:{query_hash}")

        # Add user ID if requested
        if include_user and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
            if user_id:
                key_parts.append(f"u:{user_id}")

        # Add custom parameters
        if kwargs:
            params_string = str(sorted(kwargs.items()))
            params_hash = hashlib.md5(params_string.encode()).hexdigest()[:8]
            key_parts.append(f"p:{params_hash}")

        return ":".join(key_parts)

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data if above threshold."""
        if len(data) > self.compression_threshold:
            return gzip.compress(data)
        return data

    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """Decompress data if it was compressed."""
        if compressed:
            return gzip.decompress(data)
        return data

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis:
            return None

        try:
            start_time = time.time()

            # Get from Redis
            data = await self.redis.get(f"cache:{key}")

            if data is None:
                self.metrics.record_miss()
                return None

            # Deserialize
            cached = pickle.loads(data)

            # Decompress if needed
            if cached.get("compressed"):
                cached["data"] = self._decompress_data(
                    cached["data"],
                    compressed=True
                )

            # Record hit
            time_saved = time.time() - start_time
            self.metrics.record_hit(time_saved)

            logger.debug(f"Cache HIT: {key} (saved {time_saved*1000:.1f}ms)")

            return pickle.loads(cached["data"])

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            self.metrics.record_error()
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        compress: bool = True
    ):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            compress: Whether to compress large responses
        """
        if not self.enabled or not self.redis:
            return

        try:
            # Serialize value
            data = pickle.dumps(value)

            # Compress if needed
            compressed = False
            if compress and len(data) > self.compression_threshold:
                data = self._compress_data(data)
                compressed = True

            # Create cache entry
            cache_entry = {
                "data": data,
                "compressed": compressed,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl,
            }

            # Store in Redis
            await self.redis.setex(
                f"cache:{key}",
                ttl,
                pickle.dumps(cache_entry)
            )

            self.metrics.record_set()
            logger.debug(f"Cache SET: {key} (ttl={ttl}s, compressed={compressed})")

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            self.metrics.record_error()

    async def delete(self, key: str):
        """Delete specific cache key."""
        if not self.enabled or not self.redis:
            return

        try:
            await self.redis.delete(f"cache:{key}")
            logger.debug(f"Cache DELETE: {key}")

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "assessments:*")
        """
        if not self.enabled or not self.redis:
            return

        try:
            # Find matching keys
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=f"cache:{pattern}",
                    count=100
                )

                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            self.metrics.record_invalidation()
            logger.info(f"Cache INVALIDATE: {pattern} ({deleted_count} keys)")

        except Exception as e:
            logger.error(f"Cache invalidation error for {pattern}: {e}")

    async def clear_all(self):
        """Clear all cache entries."""
        if not self.enabled or not self.redis:
            return

        try:
            await self.invalidate_pattern("*")
            logger.warning("Cache CLEARED: All cache entries removed")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return self.metrics.get_stats()


# Global cache instance
api_cache = APICache()


def cached_endpoint(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    include_user: bool = False,
    compress: bool = True,
    bypass_on_auth: bool = False,
):
    """
    Decorator for caching API endpoint responses.

    Args:
        ttl: Cache TTL in seconds (default 5 minutes)
        key_prefix: Custom cache key prefix
        include_user: Include user ID in cache key
        compress: Compress large responses
        bypass_on_auth: Skip cache for authenticated requests

    Usage:
        @app.get("/api/assessments")
        @cached_endpoint(ttl=300, key_prefix="assessments:list")
        async def list_assessments():
            return await Assessment.find_all().to_list()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request: Optional[Request] = kwargs.get("request")

            if not request:
                # No request object, can't cache
                return await func(*args, **kwargs)

            # Skip cache for authenticated requests if configured
            if bypass_on_auth and hasattr(request.state, "user"):
                return await func(*args, **kwargs)

            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = api_cache._generate_cache_key(
                prefix=prefix,
                request=request,
                include_user=include_user,
            )

            # Try to get from cache
            cached_response = await api_cache.get(cache_key)
            if cached_response is not None:
                # Add cache hit header
                if isinstance(cached_response, dict):
                    return JSONResponse(
                        content=cached_response,
                        headers={"X-Cache": "HIT"}
                    )
                return cached_response

            # Execute function
            start_time = time.time()
            response = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Cache the response
            if response is not None:
                # Extract content from Response objects
                if isinstance(response, Response):
                    # Don't cache Response objects, only data
                    logger.debug(f"Skipping cache for Response object: {cache_key}")
                else:
                    await api_cache.set(
                        key=cache_key,
                        value=response,
                        ttl=ttl,
                        compress=compress
                    )

            # Add cache miss header
            if isinstance(response, dict):
                return JSONResponse(
                    content=response,
                    headers={
                        "X-Cache": "MISS",
                        "X-Execution-Time": f"{execution_time:.3f}s"
                    }
                )

            return response

        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching pattern.

    Usage:
        await invalidate_cache("assessments:*")
        await invalidate_cache("users:123:*")
    """
    await api_cache.invalidate_pattern(pattern)


async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return api_cache.get_metrics()


async def warm_cache(
    key: str,
    value_func: Callable,
    ttl: int = 300
):
    """
    Pre-warm cache with expensive operation.

    Args:
        key: Cache key
        value_func: Async function to generate value
        ttl: Cache TTL

    Usage:
        async def get_dashboard_data():
            return await compute_expensive_dashboard()

        await warm_cache(
            "dashboard:data",
            get_dashboard_data,
            ttl=600
        )
    """
    try:
        value = await value_func()
        await api_cache.set(key, value, ttl=ttl)
        logger.info(f"Cache warmed: {key}")
    except Exception as e:
        logger.error(f"Cache warming failed for {key}: {e}")


# Example usage in FastAPI app:
"""
from fastapi import FastAPI, Depends
from infra_mind.core.api_cache import cached_endpoint, invalidate_cache, api_cache

app = FastAPI()

@app.on_event("startup")
async def startup():
    await api_cache.connect()

@app.on_event("shutdown")
async def shutdown():
    await api_cache.disconnect()

# Cached endpoint (5 minutes)
@app.get("/api/assessments")
@cached_endpoint(ttl=300, key_prefix="assessments:list")
async def list_assessments(request: Request):
    return await Assessment.find_all().to_list()

# User-specific cache
@app.get("/api/users/{user_id}/assessments")
@cached_endpoint(ttl=60, include_user=True)
async def get_user_assessments(user_id: str, request: Request):
    return await Assessment.find(Assessment.user_id == user_id).to_list()

# Invalidate on updates
@app.post("/api/assessments")
async def create_assessment(data: AssessmentCreate):
    assessment = await Assessment(**data.dict()).insert()
    await invalidate_cache("assessments:*")
    return assessment

# Get cache stats
@app.get("/admin/cache/stats")
async def get_stats():
    return await get_cache_stats()
"""
