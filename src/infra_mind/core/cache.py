"""
Redis-based caching system for cloud API responses.

Provides caching functionality with TTL support and rate limiting compliance.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import redis.asyncio as redis
from redis.asyncio import Redis
import hashlib

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager for API responses.
    
    Provides caching with TTL support and rate limiting compliance
    for AWS and Azure API calls.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 default_ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (1 hour = 3600)
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")
    
    def _generate_cache_key(self, provider: str, service: str, region: str, 
                          params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a unique cache key for API requests.
        
        Args:
            provider: Cloud provider (aws, azure, gcp)
            service: Service name (ec2, pricing, etc.)
            region: Cloud region
            params: Additional parameters
            
        Returns:
            Unique cache key
        """
        key_parts = [provider, service, region]
        
        if params:
            # Sort params for consistent key generation
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return f"cloud_api:{':'.join(key_parts)}"
    
    async def get(self, provider: str, service: str, region: str,
                  params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached API response.
        
        Args:
            provider: Cloud provider
            service: Service name
            region: Cloud region
            params: Additional parameters
            
        Returns:
            Cached data or None if not found/expired
        """
        if not self._connected or not self.redis_client:
            logger.warning("Redis not connected, cache miss")
            return None
        
        try:
            cache_key = self._generate_cache_key(provider, service, region, params)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                
                # Check if data includes staleness information
                cached_at = data.get("cached_at")
                if cached_at:
                    cached_time = datetime.fromisoformat(cached_at)
                    age_hours = (datetime.utcnow() - cached_time).total_seconds() / 3600
                    data["cache_age_hours"] = round(age_hours, 2)
                    data["is_stale"] = age_hours > 1  # Mark as stale after 1 hour
                
                logger.info(f"Cache hit for {cache_key}")
                return data
            
            logger.debug(f"Cache miss for {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, provider: str, service: str, region: str,
                  data: Dict[str, Any], ttl: Optional[int] = None,
                  params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache API response data.
        
        Args:
            provider: Cloud provider
            service: Service name
            region: Cloud region
            data: Data to cache
            ttl: Time to live in seconds (uses default if None)
            params: Additional parameters
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self._connected or not self.redis_client:
            logger.warning("Redis not connected, cannot cache")
            return False
        
        try:
            cache_key = self._generate_cache_key(provider, service, region, params)
            
            # Add metadata to cached data
            cache_data = {
                **data,
                "cached_at": datetime.utcnow().isoformat(),
                "provider": provider,
                "service": service,
                "region": region
            }
            
            cache_ttl = ttl or self.default_ttl
            
            await self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached data for {cache_key} with TTL {cache_ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, provider: str, service: str, region: str,
                     params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete cached data.
        
        Args:
            provider: Cloud provider
            service: Service name
            region: Cloud region
            params: Additional parameters
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._connected or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(provider, service, region, params)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                logger.info(f"Deleted cache for {cache_key}")
                return True
            else:
                logger.debug(f"No cache found to delete for {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_provider_cache(self, provider: str) -> int:
        """
        Clear all cached data for a specific provider.
        
        Args:
            provider: Cloud provider
            
        Returns:
            Number of keys deleted
        """
        if not self._connected or not self.redis_client:
            return 0
        
        try:
            pattern = f"cloud_api:{provider}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries for {provider}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self._connected or not self.redis_client:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info()
            keys = await self.redis_client.keys("cloud_api:*")
            
            return {
                "connected": True,
                "total_keys": len(keys),
                "memory_used": info.get("used_memory_human", "Unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "redis_version": info.get("redis_version", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


class RateLimiter:
    """
    Redis-based rate limiter for API compliance.
    
    Implements sliding window rate limiting for AWS and Azure APIs.
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize rate limiter.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager
        
        # Get rate limits from configuration
        from .config import get_rate_limit_config
        rate_config = get_rate_limit_config()
        
        # Rate limits per provider (requests per minute)
        self.rate_limits = {
            "aws": {
                "pricing": rate_config["aws_limit"],
                "ec2": rate_config["aws_limit"],
                "rds": rate_config["aws_limit"],
                "storage": rate_config["aws_limit"],
                "ai": rate_config["aws_limit"],
                "default": rate_config["aws_limit"]
            },
            "azure": {
                "pricing": rate_config["azure_limit"],  # Azure Retail Prices API (public, higher limit)
                "compute": rate_config["azure_limit"],
                "sql": rate_config["azure_limit"],
                "storage": rate_config["azure_limit"],
                "ai": rate_config["azure_limit"],
                "default": rate_config["azure_limit"]
            },
            "gcp": {
                "billing": rate_config["gcp_limit"],
                "compute": rate_config["gcp_limit"],
                "storage": rate_config["gcp_limit"],
                "ai": rate_config["gcp_limit"],
                "default": rate_config["gcp_limit"]
            }
        }
    
    def _get_rate_limit_key(self, provider: str, service: str) -> str:
        """Generate rate limit key."""
        return f"rate_limit:{provider}:{service}"
    
    async def check_rate_limit(self, provider: str, service: str) -> Dict[str, Any]:
        """
        Check if request is within rate limits.
        
        Args:
            provider: Cloud provider
            service: Service name
            
        Returns:
            Dictionary with rate limit status
        """
        if not self.cache_manager._connected or not self.cache_manager.redis_client:
            # If Redis is not available, allow the request but log warning
            logger.warning("Rate limiter not available, allowing request")
            return {
                "allowed": True,
                "remaining": -1,
                "reset_time": None,
                "warning": "Rate limiter unavailable"
            }
        
        try:
            rate_limit_key = self._get_rate_limit_key(provider, service)
            
            # Get rate limit for this provider/service
            provider_limits = self.rate_limits.get(provider, {})
            limit = provider_limits.get(service, provider_limits.get("default", 100))
            
            # Use sliding window with Redis
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=1)
            
            # Count requests in the last minute
            pipe = self.cache_manager.redis_client.pipeline()
            
            # Remove old entries
            await pipe.zremrangebyscore(
                rate_limit_key,
                0,
                window_start.timestamp()
            )
            
            # Count current requests
            current_count = await self.cache_manager.redis_client.zcard(rate_limit_key)
            
            if current_count >= limit:
                # Rate limit exceeded
                oldest_request = await self.cache_manager.redis_client.zrange(
                    rate_limit_key, 0, 0, withscores=True
                )
                
                reset_time = None
                if oldest_request:
                    reset_time = datetime.fromtimestamp(oldest_request[0][1]) + timedelta(minutes=1)
                
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": reset_time.isoformat() if reset_time else None,
                    "limit": limit,
                    "current": current_count
                }
            
            # Add current request to the window
            await self.cache_manager.redis_client.zadd(
                rate_limit_key,
                {str(now.timestamp()): now.timestamp()}
            )
            
            # Set expiry for the key (cleanup)
            await self.cache_manager.redis_client.expire(rate_limit_key, 120)  # 2 minutes
            
            return {
                "allowed": True,
                "remaining": limit - current_count - 1,
                "reset_time": (now + timedelta(minutes=1)).isoformat(),
                "limit": limit,
                "current": current_count + 1
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request but log the issue
            return {
                "allowed": True,
                "remaining": -1,
                "reset_time": None,
                "error": str(e)
            }
    
    async def get_rate_limit_status(self, provider: str, service: str) -> Dict[str, Any]:
        """
        Get current rate limit status without incrementing counter.
        
        Args:
            provider: Cloud provider
            service: Service name
            
        Returns:
            Dictionary with current rate limit status
        """
        if not self.cache_manager._connected or not self.cache_manager.redis_client:
            return {"available": False}
        
        try:
            rate_limit_key = self._get_rate_limit_key(provider, service)
            
            # Get rate limit for this provider/service
            provider_limits = self.rate_limits.get(provider, {})
            limit = provider_limits.get(service, provider_limits.get("default", 100))
            
            # Count current requests in the last minute
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=1)
            
            # Clean up old entries first
            await self.cache_manager.redis_client.zremrangebyscore(
                rate_limit_key,
                0,
                window_start.timestamp()
            )
            
            current_count = await self.cache_manager.redis_client.zcard(rate_limit_key)
            
            return {
                "available": True,
                "limit": limit,
                "current": current_count,
                "remaining": max(0, limit - current_count),
                "window_reset": (now + timedelta(minutes=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rate limit status error: {e}")
            return {"available": False, "error": str(e)}


# Global cache manager instance
cache_manager = CacheManager()
rate_limiter = RateLimiter(cache_manager)


async def init_cache(redis_url: Optional[str] = None) -> None:
    """Initialize the global cache manager."""
    global cache_manager, rate_limiter
    
    # Get configuration if not provided
    if redis_url is None:
        from .config import get_cache_config
        cache_config = get_cache_config()
        redis_url = cache_config["redis_url"]
        default_ttl = cache_config["cache_ttl"]
    else:
        default_ttl = 3600
    
    cache_manager = CacheManager(redis_url, default_ttl)
    
    try:
        await cache_manager.connect()
        rate_limiter = RateLimiter(cache_manager)
        logger.info("Cache system initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize cache system: {e}")
        # Create a disabled cache manager for graceful degradation
        cache_manager._connected = False
        rate_limiter = RateLimiter(cache_manager)


async def cleanup_cache() -> None:
    """Cleanup the global cache manager."""
    global cache_manager
    
    if cache_manager:
        await cache_manager.disconnect()
    
    logger.info("Cache system cleaned up")