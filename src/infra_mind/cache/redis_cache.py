"""
Redis Cache Implementation

High-performance Redis-based caching system with advanced features
including intelligent expiration, compression, and distributed caching.
"""

import json
import pickle
import zlib
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from loguru import logger


class CacheStrategy(Enum):
    """Cache strategy types."""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind" 
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"


class SerializationFormat(Enum):
    """Serialization formats for cached data."""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"


@dataclass
class CacheConfig:
    """Redis cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    retry_on_timeout: bool = True
    decode_responses: bool = True
    compression_enabled: bool = True
    compression_threshold: int = 1024  # bytes
    default_ttl: int = 3600  # seconds
    key_prefix: str = "infra_mind"
    serialization_format: SerializationFormat = SerializationFormat.PICKLE


@dataclass  
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate


class RedisCache:
    """
    Advanced Redis cache implementation with intelligent caching strategies.
    
    Provides high-performance caching with features like compression,
    intelligent expiration, distributed locking, and cache warming.
    """
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.client: Optional[redis.Redis] = None
        self.stats = CacheStats()
        self.is_connected = False
        self._locks: Dict[str, asyncio.Lock] = {}
        
    async def connect(self) -> bool:
        """Connect to Redis server."""
        try:
            self.client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                health_check_interval=self.config.health_check_interval,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses
            )
            
            # Test connection
            await self.client.ping()
            self.is_connected = True
            
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis server."""
        if self.client:
            await self.client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Generate Redis key with prefix and namespace."""
        parts = [self.config.key_prefix]
        
        if namespace:
            parts.append(namespace)
        
        parts.append(key)
        return ":".join(parts)
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage."""
        try:
            if self.config.serialization_format == SerializationFormat.JSON:
                serialized = json.dumps(data, default=str).encode('utf-8')
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                serialized = pickle.dumps(data)
            else:  # MSGPACK
                import msgpack
                serialized = msgpack.packb(data)
            
            # Apply compression if enabled and data is large enough
            if (self.config.compression_enabled and 
                len(serialized) > self.config.compression_threshold):
                compressed = zlib.compress(serialized)
                # Only use compression if it actually reduces size
                if len(compressed) < len(serialized):
                    return b'COMPRESSED:' + compressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage."""
        try:
            # Check if data is compressed
            if data.startswith(b'COMPRESSED:'):
                data = zlib.decompress(data[11:])  # Remove 'COMPRESSED:' prefix
            
            if self.config.serialization_format == SerializationFormat.JSON:
                return json.loads(data.decode('utf-8'))
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                return pickle.loads(data)
            else:  # MSGPACK
                import msgpack
                return msgpack.unpackb(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    async def get(self, key: str, namespace: Optional[str] = None) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected:
            logger.warning("Redis not connected")
            return None
        
        try:
            redis_key = self._make_key(key, namespace)
            data = await self.client.get(redis_key)
            
            if data is None:
                self.stats.misses += 1
                return None
            
            self.stats.hits += 1
            return self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set value in cache."""
        if not self.is_connected:
            logger.warning("Redis not connected")
            return False
        
        try:
            redis_key = self._make_key(key, namespace)
            serialized_value = self._serialize(value)
            
            # Use default TTL if not specified
            expiry = ttl or self.config.default_ttl
            
            await self.client.setex(redis_key, expiry, serialized_value)
            self.stats.sets += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete value from cache."""
        if not self.is_connected:
            logger.warning("Redis not connected")
            return False
        
        try:
            redis_key = self._make_key(key, namespace)
            result = await self.client.delete(redis_key)
            
            if result > 0:
                self.stats.deletes += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected:
            return False
        
        try:
            redis_key = self._make_key(key, namespace)
            return bool(await self.client.exists(redis_key))
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, namespace: Optional[str] = None) -> bool:
        """Set expiration time for key."""
        if not self.is_connected:
            return False
        
        try:
            redis_key = self._make_key(key, namespace)
            return bool(await self.client.expire(redis_key, ttl))
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str, namespace: Optional[str] = None) -> int:
        """Get time to live for key."""
        if not self.is_connected:
            return -1
        
        try:
            redis_key = self._make_key(key, namespace)
            return await self.client.ttl(redis_key)
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    async def increment(
        self, 
        key: str, 
        amount: int = 1, 
        namespace: Optional[str] = None
    ) -> Optional[int]:
        """Increment numeric value in cache."""
        if not self.is_connected:
            return None
        
        try:
            redis_key = self._make_key(key, namespace)
            return await self.client.incrby(redis_key, amount)
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def decrement(
        self, 
        key: str, 
        amount: int = 1, 
        namespace: Optional[str] = None
    ) -> Optional[int]:
        """Decrement numeric value in cache."""
        if not self.is_connected:
            return None
        
        try:
            redis_key = self._make_key(key, namespace)
            return await self.client.decrby(redis_key, amount)
            
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return None
    
    async def get_multiple(
        self, 
        keys: List[str], 
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get multiple values from cache."""
        if not self.is_connected or not keys:
            return {}
        
        try:
            redis_keys = [self._make_key(key, namespace) for key in keys]
            values = await self.client.mget(redis_keys)
            
            result = {}
            for i, (original_key, value) in enumerate(zip(keys, values)):
                if value is not None:
                    result[original_key] = self._deserialize(value)
                    self.stats.hits += 1
                else:
                    self.stats.misses += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get_multiple error: {e}")
            self.stats.misses += len(keys)
            return {}
    
    async def set_multiple(
        self, 
        items: Dict[str, Any], 
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set multiple values in cache."""
        if not self.is_connected or not items:
            return False
        
        try:
            # Prepare pipeline for batch operations
            pipe = self.client.pipeline()
            
            expiry = ttl or self.config.default_ttl
            
            for key, value in items.items():
                redis_key = self._make_key(key, namespace)
                serialized_value = self._serialize(value)
                pipe.setex(redis_key, expiry, serialized_value)
            
            await pipe.execute()
            self.stats.sets += len(items)
            return True
            
        except Exception as e:
            logger.error(f"Cache set_multiple error: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        if not self.is_connected:
            return 0
        
        try:
            pattern = self._make_key("*", namespace)
            keys = await self.client.keys(pattern)
            
            if not keys:
                return 0
            
            count = await self.client.delete(*keys)
            self.stats.deletes += count
            return count
            
        except Exception as e:
            logger.error(f"Cache clear_namespace error for {namespace}: {e}")
            return 0
    
    async def flush_all(self) -> bool:
        """Flush all cached data."""
        if not self.is_connected:
            return False
        
        try:
            await self.client.flushdb()
            logger.info("Cache flushed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    async def get_with_lock(
        self, 
        key: str, 
        loader: Callable[[], Any],
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
        lock_timeout: int = 30
    ) -> Any:
        """
        Get value with distributed lock to prevent cache stampede.
        
        If key doesn't exist, acquires lock and calls loader function.
        """
        # Try to get from cache first
        value = await self.get(key, namespace)
        if value is not None:
            return value
        
        # Acquire lock
        lock_key = f"lock:{key}"
        if namespace:
            lock_key = f"lock:{namespace}:{key}"
        
        # Use local asyncio lock per key to prevent multiple coroutines
        # from competing for the same cache key
        if lock_key not in self._locks:
            self._locks[lock_key] = asyncio.Lock()
        
        async with self._locks[lock_key]:
            # Double-check pattern: another coroutine might have loaded the value
            value = await self.get(key, namespace)
            if value is not None:
                return value
            
            # Acquire distributed lock
            redis_lock_key = self._make_key(lock_key)
            lock_acquired = await self.client.set(
                redis_lock_key, 
                "locked", 
                ex=lock_timeout, 
                nx=True
            )
            
            if not lock_acquired:
                # Wait for lock to be released and try to get value again
                await asyncio.sleep(0.1)
                return await self.get(key, namespace)
            
            try:
                # Load data using provided function
                value = await loader() if asyncio.iscoroutinefunction(loader) else loader()
                
                # Cache the loaded value
                await self.set(key, value, ttl, namespace)
                
                return value
                
            finally:
                # Release the distributed lock
                await self.client.delete(redis_lock_key)
    
    async def warm_cache(
        self, 
        warmer: Callable[[], Dict[str, Any]],
        namespace: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> int:
        """Warm cache with data from warmer function."""
        try:
            logger.info(f"Starting cache warming for namespace: {namespace}")
            
            # Load data from warmer
            data = await warmer() if asyncio.iscoroutinefunction(warmer) else warmer()
            
            if not data:
                return 0
            
            # Set multiple items in cache
            success = await self.set_multiple(data, ttl, namespace)
            
            count = len(data) if success else 0
            logger.info(f"Cache warming completed: {count} items loaded")
            
            return count
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return 0
    
    async def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        if self.is_connected:
            try:
                info = await self.client.info('memory')
                self.stats.memory_usage = info.get('used_memory', 0)
            except Exception as e:
                logger.warning(f"Could not fetch memory stats: {e}")
        
        return self.stats
    
    async def reset_stats(self):
        """Reset cache statistics."""
        self.stats = CacheStats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        try:
            if not self.is_connected:
                return {"status": "disconnected", "latency_ms": None}
            
            # Measure ping latency
            start_time = datetime.now()
            await self.client.ping()
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get server info
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "redis_version": info.get('redis_version'),
                "used_memory_human": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "hit_rate": round(self.stats.hit_rate * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()