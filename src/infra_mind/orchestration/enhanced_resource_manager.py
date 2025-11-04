"""
Enhanced Resource Manager with Race Condition Fixes.

Addresses critical issues:
1. Race conditions in queue processing (atomic operations)
2. Sliding window rate limiting (vs simple counter)
3. Resource leak prevention
4. Better concurrency control

Author: AI Workflow Specialist
Date: 2025-11-04
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources to manage."""
    LLM_TOKENS = "llm_tokens"
    CLOUD_API_CALLS = "cloud_api_calls"
    DATABASE_CONNECTIONS = "database_connections"
    MEMORY = "memory"
    CPU = "cpu"


@dataclass
class ResourceRequest:
    """Resource allocation request."""
    agent_name: str
    request_id: str
    resource_requirements: Dict[ResourceType, int]
    priority: int = 1
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeout: int = 300  # 5 minutes default


@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_llm_tokens_per_minute: int = 100000
    max_cloud_api_calls_per_minute: int = 100
    max_database_connections: int = 50
    max_memory_mb: int = 4096
    max_cpu_percent: int = 80


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    llm_tokens_used: int = 0
    cloud_api_calls_used: int = 0
    database_connections_used: int = 0
    memory_mb_used: int = 0
    cpu_percent_used: float = 0.0


@dataclass
class RateLimitWindow:
    """Sliding window for rate limiting."""
    timestamps: deque = field(default_factory=deque)
    window_size: int = 60  # seconds
    max_requests: int = 100

    def add_request(self, timestamp: Optional[datetime] = None) -> None:
        """Add a request to the window."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self.timestamps.append(timestamp)

    def get_current_count(self) -> int:
        """Get number of requests in current window."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_size)

        # Remove old timestamps (atomic operation using deque)
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        return len(self.timestamps)

    def can_allow_request(self) -> bool:
        """Check if request can be allowed."""
        return self.get_current_count() < self.max_requests


class EnhancedResourceManager:
    """
    Enhanced resource manager with race condition fixes.

    Key Improvements:
    1. Atomic queue operations using deque
    2. Sliding window rate limiting
    3. Async lock for all critical sections
    4. Resource leak prevention
    5. Better error handling
    """

    def __init__(self, limits: Optional[ResourceLimits] = None):
        """Initialize enhanced resource manager."""
        self.limits = limits or ResourceLimits()
        self.current_usage = ResourceUsage()

        # Use deque for O(1) queue operations (thread-safe for single producer/consumer)
        self.resource_queue: deque = deque()

        # Active allocations tracking
        self.active_allocations: Dict[str, ResourceRequest] = {}

        # Async lock for all critical sections
        self._lock = asyncio.Lock()

        # Sliding window rate limiters
        self.rate_limiters: Dict[ResourceType, RateLimitWindow] = {
            ResourceType.LLM_TOKENS: RateLimitWindow(
                window_size=60,
                max_requests=self.limits.max_llm_tokens_per_minute
            ),
            ResourceType.CLOUD_API_CALLS: RateLimitWindow(
                window_size=60,
                max_requests=self.limits.max_cloud_api_calls_per_minute
            )
        }

        # Metrics
        self.metrics = {
            "allocations_granted": 0,
            "allocations_denied": 0,
            "queue_waits": 0,
            "rate_limit_hits": 0,
            "resource_leaks_prevented": 0
        }

        logger.info("Enhanced resource manager initialized")

    async def request_resources(
        self,
        agent_name: str,
        resource_requirements: Dict[ResourceType, int],
        priority: int = 1,
        timeout: int = 300
    ) -> bool:
        """
        Request resources for agent execution.

        Returns:
            True if resources allocated, False if denied
        """
        request = ResourceRequest(
            agent_name=agent_name,
            request_id=f"{agent_name}_{datetime.now(timezone.utc).timestamp()}",
            resource_requirements=resource_requirements,
            priority=priority,
            timeout=timeout
        )

        async with self._lock:
            # Check rate limits first (sliding window)
            for resource_type, amount in resource_requirements.items():
                if resource_type in self.rate_limiters:
                    rate_limiter = self.rate_limiters[resource_type]
                    if not rate_limiter.can_allow_request():
                        logger.warning(
                            f"Rate limit exceeded for {resource_type.value}: "
                            f"{rate_limiter.get_current_count()}/{rate_limiter.max_requests}"
                        )
                        self.metrics["rate_limit_hits"] += 1

                        # Add to queue
                        self.resource_queue.append(request)
                        self.metrics["queue_waits"] += 1
                        logger.info(f"Agent {agent_name} queued (rate limit), queue size: {len(self.resource_queue)}")
                        return False

            # Check resource availability
            if await self._can_allocate_resources(request):
                await self._allocate_resources(request)
                self.metrics["allocations_granted"] += 1
                return True
            else:
                # Add to queue (atomic operation with deque)
                self.resource_queue.append(request)
                self.metrics["queue_waits"] += 1
                logger.info(f"Agent {agent_name} queued (resources), queue size: {len(self.resource_queue)}")
                return False

    async def release_resources(self, request_id: str) -> None:
        """
        Release allocated resources.

        Prevents resource leaks by cleaning up allocations.
        """
        async with self._lock:
            if request_id not in self.active_allocations:
                logger.warning(f"Attempted to release non-existent allocation: {request_id}")
                self.metrics["resource_leaks_prevented"] += 1
                return

            request = self.active_allocations.pop(request_id)

            # Update usage
            for resource_type, amount in request.resource_requirements.items():
                if resource_type == ResourceType.LLM_TOKENS:
                    self.current_usage.llm_tokens_used -= amount
                elif resource_type == ResourceType.CLOUD_API_CALLS:
                    self.current_usage.cloud_api_calls_used -= amount
                elif resource_type == ResourceType.DATABASE_CONNECTIONS:
                    self.current_usage.database_connections_used -= amount
                elif resource_type == ResourceType.MEMORY:
                    self.current_usage.memory_mb_used -= amount

            logger.debug(f"Released resources for {request.agent_name}")

            # Process queue (atomic operation)
            await self._process_queue()

    async def _can_allocate_resources(self, request: ResourceRequest) -> bool:
        """Check if resources can be allocated."""
        for resource_type, amount in request.resource_requirements.items():
            if resource_type == ResourceType.LLM_TOKENS:
                if self.current_usage.llm_tokens_used + amount > self.limits.max_llm_tokens_per_minute:
                    return False

            elif resource_type == ResourceType.CLOUD_API_CALLS:
                if self.current_usage.cloud_api_calls_used + amount > self.limits.max_cloud_api_calls_per_minute:
                    return False

            elif resource_type == ResourceType.DATABASE_CONNECTIONS:
                if self.current_usage.database_connections_used + amount > self.limits.max_database_connections:
                    return False

            elif resource_type == ResourceType.MEMORY:
                if self.current_usage.memory_mb_used + amount > self.limits.max_memory_mb:
                    return False

        return True

    async def _allocate_resources(self, request: ResourceRequest) -> None:
        """Allocate resources to request."""
        # Update usage
        for resource_type, amount in request.resource_requirements.items():
            if resource_type == ResourceType.LLM_TOKENS:
                self.current_usage.llm_tokens_used += amount
                # Record in rate limiter
                self.rate_limiters[resource_type].add_request()

            elif resource_type == ResourceType.CLOUD_API_CALLS:
                self.current_usage.cloud_api_calls_used += amount
                # Record in rate limiter
                self.rate_limiters[resource_type].add_request()

            elif resource_type == ResourceType.DATABASE_CONNECTIONS:
                self.current_usage.database_connections_used += amount

            elif resource_type == ResourceType.MEMORY:
                self.current_usage.memory_mb_used += amount

        # Track allocation
        self.active_allocations[request.request_id] = request

        logger.info(f"Allocated resources for {request.agent_name}")

    async def _process_queue(self) -> None:
        """
        Process queued resource requests atomically.

        Fixed race conditions:
        1. Use deque for atomic popleft() operations
        2. Process one at a time to avoid conflicts
        3. All operations under lock
        """
        if not self.resource_queue:
            return

        # Process requests in FIFO order (priority can be added later)
        # Use popleft() for O(1) atomic operation
        processed_count = 0
        max_process = len(self.resource_queue)

        while self.resource_queue and processed_count < max_process:
            # Peek at next request (atomic)
            request = self.resource_queue[0]

            # Check if timed out
            elapsed = (datetime.now(timezone.utc) - request.requested_at).total_seconds()
            if elapsed > request.timeout:
                # Remove timed out request (atomic popleft)
                self.resource_queue.popleft()
                logger.warning(f"Request {request.request_id} timed out after {elapsed}s")
                processed_count += 1
                continue

            # Try to allocate
            if await self._can_allocate_resources(request):
                # Remove from queue (atomic popleft)
                self.resource_queue.popleft()
                await self._allocate_resources(request)
                logger.info(f"Queued agent {request.agent_name} allocated resources")
                processed_count += 1
            else:
                # Can't allocate yet, stop processing
                break

    async def cleanup_stale_allocations(self, max_age_seconds: int = 3600) -> int:
        """
        Cleanup stale resource allocations to prevent leaks.

        Returns:
            Number of allocations cleaned up
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            stale_requests = []

            for request_id, request in self.active_allocations.items():
                age = (now - request.requested_at).total_seconds()
                if age > max_age_seconds:
                    stale_requests.append(request_id)

            # Release stale allocations
            for request_id in stale_requests:
                logger.warning(f"Cleaning up stale allocation: {request_id}")
                request = self.active_allocations.pop(request_id)

                # Update usage
                for resource_type, amount in request.resource_requirements.items():
                    if resource_type == ResourceType.LLM_TOKENS:
                        self.current_usage.llm_tokens_used = max(0, self.current_usage.llm_tokens_used - amount)
                    elif resource_type == ResourceType.CLOUD_API_CALLS:
                        self.current_usage.cloud_api_calls_used = max(0, self.current_usage.cloud_api_calls_used - amount)
                    elif resource_type == ResourceType.DATABASE_CONNECTIONS:
                        self.current_usage.database_connections_used = max(0, self.current_usage.database_connections_used - amount)
                    elif resource_type == ResourceType.MEMORY:
                        self.current_usage.memory_mb_used = max(0, self.current_usage.memory_mb_used - amount)

            if stale_requests:
                self.metrics["resource_leaks_prevented"] += len(stale_requests)
                # Process queue after cleanup
                await self._process_queue()

            return len(stale_requests)

    def get_metrics(self) -> Dict:
        """Get resource manager metrics."""
        return {
            **self.metrics,
            "current_usage": {
                "llm_tokens": self.current_usage.llm_tokens_used,
                "cloud_api_calls": self.current_usage.cloud_api_calls_used,
                "database_connections": self.current_usage.database_connections_used,
                "memory_mb": self.current_usage.memory_mb_used
            },
            "queue_size": len(self.resource_queue),
            "active_allocations": len(self.active_allocations),
            "rate_limiters": {
                rt.value: {
                    "current_count": rl.get_current_count(),
                    "max_requests": rl.max_requests
                }
                for rt, rl in self.rate_limiters.items()
            }
        }


# Global singleton
_enhanced_resource_manager = None

def get_enhanced_resource_manager(limits: Optional[ResourceLimits] = None) -> EnhancedResourceManager:
    """Get or create enhanced resource manager singleton."""
    global _enhanced_resource_manager

    if _enhanced_resource_manager is None:
        _enhanced_resource_manager = EnhancedResourceManager(limits)

    return _enhanced_resource_manager
