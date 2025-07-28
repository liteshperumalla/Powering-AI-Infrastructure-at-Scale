"""
Advanced rate limiting system with multiple algorithms and adaptive strategies.

Provides sophisticated rate limiting with sliding window, token bucket,
adaptive rate limiting, and distributed rate limiting capabilities.
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import redis.asyncio as redis
from redis.asyncio import Redis
import hashlib

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"


class RateLimitScope(str, Enum):
    """Rate limiting scopes."""
    GLOBAL = "global"
    PER_SERVICE = "per_service"
    PER_USER = "per_user"
    PER_IP = "per_ip"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_capacity: int = 20            # For token bucket
    refill_rate: float = 1.0           # Tokens per second for token bucket
    window_size: int = 60              # Window size in seconds
    adaptive_threshold: float = 0.8    # Threshold for adaptive rate limiting
    backoff_factor: float = 0.5        # Backoff factor for adaptive limiting
    recovery_factor: float = 1.1       # Recovery factor for adaptive limiting


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: Optional[datetime]
    retry_after: Optional[int]
    algorithm_used: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, 
                 result: Optional[RateLimitResult] = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.result = result


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter implementation.
    
    Uses Redis sorted sets to maintain a sliding window of requests.
    """
    
    def __init__(self, redis_client: Redis, config: RateLimitConfig):
        self.redis_client = redis_client
        self.config = config
    
    async def check_rate_limit(self, key: str, identifier: str) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        now = time.time()
        window_start = now - self.config.window_size
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Execute pipeline
        results = await pipe.execute()
        current_count = results[1]
        
        # Check if limit exceeded
        limit = self.config.requests_per_minute
        if current_count >= limit:
            # Find when the oldest request will expire
            oldest_requests = await self.redis_client.zrange(
                key, 0, 0, withscores=True
            )
            
            reset_time = None
            if oldest_requests:
                reset_time = datetime.fromtimestamp(
                    oldest_requests[0][1] + self.config.window_size
                )
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=int(self.config.window_size),
                algorithm_used="sliding_window",
                metadata={
                    "current_count": current_count,
                    "limit": limit,
                    "window_size": self.config.window_size
                }
            )
        
        # Add current request
        await self.redis_client.zadd(key, {identifier: now})
        
        # Set expiry for cleanup
        await self.redis_client.expire(key, self.config.window_size + 60)
        
        return RateLimitResult(
            allowed=True,
            remaining=limit - current_count - 1,
            reset_time=datetime.fromtimestamp(now + self.config.window_size),
            retry_after=None,
            algorithm_used="sliding_window",
            metadata={
                "current_count": current_count + 1,
                "limit": limit,
                "window_size": self.config.window_size
            }
        )


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.
    
    Allows burst traffic up to bucket capacity while maintaining
    average rate over time.
    """
    
    def __init__(self, redis_client: Redis, config: RateLimitConfig):
        self.redis_client = redis_client
        self.config = config
    
    async def check_rate_limit(self, key: str, identifier: str) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        bucket_key = f"{key}:bucket"
        
        # Get current bucket state
        bucket_data = await self.redis_client.hgetall(bucket_key)
        
        now = time.time()
        
        if bucket_data:
            tokens = float(bucket_data.get("tokens", self.config.burst_capacity))
            last_refill = float(bucket_data.get("last_refill", now))
        else:
            tokens = self.config.burst_capacity
            last_refill = now
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = now - last_refill
        tokens_to_add = time_elapsed * self.config.refill_rate
        tokens = min(self.config.burst_capacity, tokens + tokens_to_add)
        
        if tokens < 1:
            # Not enough tokens
            retry_after = int((1 - tokens) / self.config.refill_rate)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(now + retry_after),
                retry_after=retry_after,
                algorithm_used="token_bucket",
                metadata={
                    "tokens": tokens,
                    "capacity": self.config.burst_capacity,
                    "refill_rate": self.config.refill_rate
                }
            )
        
        # Consume one token
        tokens -= 1
        
        # Update bucket state
        await self.redis_client.hset(bucket_key, mapping={
            "tokens": str(tokens),
            "last_refill": str(now)
        })
        
        # Set expiry
        await self.redis_client.expire(bucket_key, 3600)  # 1 hour
        
        return RateLimitResult(
            allowed=True,
            remaining=int(tokens),
            reset_time=None,
            retry_after=None,
            algorithm_used="token_bucket",
            metadata={
                "tokens": tokens,
                "capacity": self.config.burst_capacity,
                "refill_rate": self.config.refill_rate
            }
        )


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system performance.
    
    Monitors success rates and adjusts rate limits dynamically to
    maintain system stability while maximizing throughput.
    """
    
    def __init__(self, redis_client: Redis, config: RateLimitConfig):
        self.redis_client = redis_client
        self.config = config
        self.base_limiter = SlidingWindowRateLimiter(redis_client, config)
    
    async def check_rate_limit(self, key: str, identifier: str, 
                             success_rate: Optional[float] = None) -> RateLimitResult:
        """Check rate limit with adaptive adjustment."""
        
        # Get current adaptive state
        adaptive_key = f"{key}:adaptive"
        adaptive_data = await self.redis_client.hgetall(adaptive_key)
        
        current_limit = self.config.requests_per_minute
        
        if adaptive_data:
            current_limit = int(adaptive_data.get("current_limit", current_limit))
            last_adjustment = float(adaptive_data.get("last_adjustment", time.time()))
            adjustment_count = int(adaptive_data.get("adjustment_count", 0))
        else:
            last_adjustment = time.time()
            adjustment_count = 0
        
        # Adjust limit based on success rate if provided
        if success_rate is not None:
            new_limit = await self._adjust_limit(
                current_limit, success_rate, last_adjustment, adjustment_count
            )
            
            if new_limit != current_limit:
                await self.redis_client.hset(adaptive_key, mapping={
                    "current_limit": str(new_limit),
                    "last_adjustment": str(time.time()),
                    "adjustment_count": str(adjustment_count + 1)
                })
                
                current_limit = new_limit
                logger.info(f"Adaptive rate limit adjusted to {new_limit} for {key}")
        
        # Create temporary config with adjusted limit
        adjusted_config = RateLimitConfig(
            algorithm=self.config.algorithm,
            requests_per_minute=current_limit,
            requests_per_hour=self.config.requests_per_hour,
            window_size=self.config.window_size
        )
        
        # Use base limiter with adjusted config
        temp_limiter = SlidingWindowRateLimiter(self.redis_client, adjusted_config)
        result = await temp_limiter.check_rate_limit(key, identifier)
        
        # Update algorithm used
        result.algorithm_used = "adaptive"
        result.metadata["adaptive_limit"] = current_limit
        result.metadata["base_limit"] = self.config.requests_per_minute
        
        return result
    
    async def _adjust_limit(self, current_limit: int, success_rate: float,
                          last_adjustment: float, adjustment_count: int) -> int:
        """Adjust rate limit based on success rate."""
        
        # Don't adjust too frequently
        if time.time() - last_adjustment < 60:  # Wait at least 1 minute
            return current_limit
        
        base_limit = self.config.requests_per_minute
        
        if success_rate < self.config.adaptive_threshold:
            # Reduce limit due to poor success rate
            new_limit = max(
                int(current_limit * self.config.backoff_factor),
                int(base_limit * 0.1)  # Don't go below 10% of base
            )
        elif success_rate > 0.95:
            # Increase limit due to good success rate
            new_limit = min(
                int(current_limit * self.config.recovery_factor),
                int(base_limit * 2.0)  # Don't exceed 200% of base
            )
        else:
            # Success rate is acceptable, no change
            new_limit = current_limit
        
        return new_limit


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple algorithms and scopes.
    
    Provides comprehensive rate limiting with support for different
    algorithms, scopes, and adaptive behavior.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.limiters: Dict[str, Any] = {}
        self.configs: Dict[str, RateLimitConfig] = {}
        self.success_trackers: Dict[str, List[Tuple[float, bool]]] = {}
    
    def configure_service(self, service_name: str, config: RateLimitConfig) -> None:
        """Configure rate limiting for a service."""
        self.configs[service_name] = config
        
        # Create appropriate limiter based on algorithm
        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self.limiters[service_name] = SlidingWindowRateLimiter(
                self.redis_client, config
            )
        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self.limiters[service_name] = TokenBucketRateLimiter(
                self.redis_client, config
            )
        elif config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            self.limiters[service_name] = AdaptiveRateLimiter(
                self.redis_client, config
            )
        else:
            # Default to sliding window
            self.limiters[service_name] = SlidingWindowRateLimiter(
                self.redis_client, config
            )
        
        logger.info(f"Configured {config.algorithm.value} rate limiter for {service_name}")
    
    async def check_rate_limit(
        self,
        service_name: str,
        scope: RateLimitScope = RateLimitScope.GLOBAL,
        identifier: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check rate limit for a service.
        
        Args:
            service_name: Name of the service
            scope: Rate limiting scope
            identifier: Identifier for scoped rate limiting
            
        Returns:
            Rate limit result
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if service_name not in self.limiters:
            # No rate limiting configured, allow request
            return RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_time=None,
                retry_after=None,
                algorithm_used="none",
                metadata={"message": "No rate limiting configured"}
            )
        
        # Generate rate limit key based on scope
        key = self._generate_rate_limit_key(service_name, scope, identifier)
        
        limiter = self.limiters[service_name]
        config = self.configs[service_name]
        
        # For adaptive limiter, calculate success rate
        success_rate = None
        if config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            success_rate = self._calculate_success_rate(service_name)
        
        # Check rate limit
        if hasattr(limiter, 'check_rate_limit'):
            if config.algorithm == RateLimitAlgorithm.ADAPTIVE:
                result = await limiter.check_rate_limit(key, identifier or "default", success_rate)
            else:
                result = await limiter.check_rate_limit(key, identifier or "default")
        else:
            # Fallback for any limiter without the method
            result = RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_time=None,
                retry_after=None,
                algorithm_used="fallback"
            )
        
        # Track request for adaptive learning
        if not result.allowed:
            self._track_request(service_name, False)
            
            raise RateLimitExceeded(
                f"Rate limit exceeded for {service_name}",
                retry_after=result.retry_after,
                result=result
            )
        else:
            self._track_request(service_name, True)
        
        return result
    
    def _generate_rate_limit_key(
        self,
        service_name: str,
        scope: RateLimitScope,
        identifier: Optional[str]
    ) -> str:
        """Generate Redis key for rate limiting."""
        key_parts = ["rate_limit", service_name]
        
        if scope == RateLimitScope.GLOBAL:
            key_parts.append("global")
        elif scope == RateLimitScope.PER_SERVICE:
            key_parts.append("service")
        elif scope == RateLimitScope.PER_USER and identifier:
            key_parts.extend(["user", identifier])
        elif scope == RateLimitScope.PER_IP and identifier:
            key_parts.extend(["ip", hashlib.md5(identifier.encode()).hexdigest()[:8]])
        else:
            key_parts.append("default")
        
        return ":".join(key_parts)
    
    def _track_request(self, service_name: str, success: bool) -> None:
        """Track request success/failure for adaptive learning."""
        if service_name not in self.success_trackers:
            self.success_trackers[service_name] = []
        
        tracker = self.success_trackers[service_name]
        current_time = time.time()
        
        # Add current request
        tracker.append((current_time, success))
        
        # Keep only last 100 requests or last 5 minutes
        cutoff_time = current_time - 300  # 5 minutes
        self.success_trackers[service_name] = [
            (t, s) for t, s in tracker[-100:]
            if t > cutoff_time
        ]
    
    def _calculate_success_rate(self, service_name: str) -> float:
        """Calculate success rate for adaptive rate limiting."""
        if service_name not in self.success_trackers:
            return 1.0  # Assume good if no data
        
        tracker = self.success_trackers[service_name]
        if not tracker:
            return 1.0
        
        successful_requests = sum(1 for _, success in tracker if success)
        total_requests = len(tracker)
        
        return successful_requests / total_requests if total_requests > 0 else 1.0
    
    async def get_rate_limit_status(self, service_name: str) -> Dict[str, Any]:
        """Get current rate limit status for a service."""
        if service_name not in self.configs:
            return {"configured": False}
        
        config = self.configs[service_name]
        success_rate = self._calculate_success_rate(service_name)
        
        status = {
            "configured": True,
            "algorithm": config.algorithm.value,
            "requests_per_minute": config.requests_per_minute,
            "success_rate": success_rate,
            "recent_requests": len(self.success_trackers.get(service_name, []))
        }
        
        # Add algorithm-specific status
        if config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            adaptive_key = f"rate_limit:{service_name}:global:adaptive"
            adaptive_data = await self.redis_client.hgetall(adaptive_key)
            
            if adaptive_data:
                status["adaptive_limit"] = int(adaptive_data.get("current_limit", config.requests_per_minute))
                status["adjustment_count"] = int(adaptive_data.get("adjustment_count", 0))
        
        return status
    
    async def reset_rate_limit(self, service_name: str, 
                             scope: RateLimitScope = RateLimitScope.GLOBAL,
                             identifier: Optional[str] = None) -> bool:
        """Reset rate limit for a service."""
        key = self._generate_rate_limit_key(service_name, scope, identifier)
        
        # Delete rate limit data
        deleted = await self.redis_client.delete(key)
        
        # Reset adaptive data if applicable
        if service_name in self.configs:
            config = self.configs[service_name]
            if config.algorithm == RateLimitAlgorithm.ADAPTIVE:
                adaptive_key = f"{key}:adaptive"
                await self.redis_client.delete(adaptive_key)
        
        # Clear success tracker
        if service_name in self.success_trackers:
            self.success_trackers[service_name] = []
        
        logger.info(f"Reset rate limit for {service_name} (scope: {scope.value})")
        return deleted > 0


# Global advanced rate limiter instance
advanced_rate_limiter: Optional[AdvancedRateLimiter] = None


async def init_advanced_rate_limiter(redis_url: str = "redis://localhost:6379") -> None:
    """Initialize the global advanced rate limiter."""
    global advanced_rate_limiter
    
    try:
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        await redis_client.ping()
        
        advanced_rate_limiter = AdvancedRateLimiter(redis_client)
        
        # Configure default cloud service rate limits
        await _configure_default_cloud_services()
        
        logger.info("Advanced rate limiter initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize advanced rate limiter: {e}")
        advanced_rate_limiter = None


async def _configure_default_cloud_services() -> None:
    """Configure default rate limits for cloud services."""
    if not advanced_rate_limiter:
        return
    
    # AWS services with conservative limits
    aws_config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.ADAPTIVE,
        requests_per_minute=20,
        requests_per_hour=1000,
        adaptive_threshold=0.8,
        backoff_factor=0.7,
        recovery_factor=1.2
    )
    
    advanced_rate_limiter.configure_service("aws_pricing", aws_config)
    advanced_rate_limiter.configure_service("aws_ec2", aws_config)
    advanced_rate_limiter.configure_service("aws_rds", aws_config)
    
    # Azure services with higher limits (public API)
    azure_config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_minute=100,
        requests_per_hour=5000,
        burst_capacity=50,
        refill_rate=1.67  # 100 requests per minute
    )
    
    advanced_rate_limiter.configure_service("azure_pricing", azure_config)
    advanced_rate_limiter.configure_service("azure_compute", azure_config)
    
    # GCP services
    gcp_config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        requests_per_minute=60,
        requests_per_hour=3000,
        window_size=60
    )
    
    advanced_rate_limiter.configure_service("gcp_billing", gcp_config)
    advanced_rate_limiter.configure_service("gcp_compute", gcp_config)
    
    logger.info("Configured default rate limits for cloud services")


async def cleanup_advanced_rate_limiter() -> None:
    """Cleanup the global advanced rate limiter."""
    global advanced_rate_limiter
    
    if advanced_rate_limiter and advanced_rate_limiter.redis_client:
        await advanced_rate_limiter.redis_client.close()
    
    advanced_rate_limiter = None
    logger.info("Advanced rate limiter cleaned up")