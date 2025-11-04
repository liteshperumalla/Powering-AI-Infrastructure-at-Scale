"""
Rate Limiter for Chat and API Endpoints.

Provides token bucket and sliding window rate limiting to prevent abuse.
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int
    window_seconds: int
    burst_size: Optional[int] = None  # Token bucket burst


class TokenBucket:
    """
    Token bucket rate limiter.

    Allows burst traffic while maintaining average rate limit.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second refill rate
            capacity: Maximum token capacity (burst size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait until tokens are available."""
        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.rate


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    Tracks requests in a sliding time window for accurate rate limiting.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = {}
        self.lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed for key.

        Args:
            key: Identifier (e.g., user_id, IP address)

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Initialize request queue for new key
            if key not in self.requests:
                self.requests[key] = deque()

            # Remove requests outside the window
            while (
                self.requests[key] and
                self.requests[key][0] < window_start
            ):
                self.requests[key].popleft()

            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True, None

            # Calculate retry-after time
            oldest_request = self.requests[key][0]
            retry_after = (
                oldest_request + timedelta(seconds=self.window_seconds) - now
            ).total_seconds()

            return False, int(retry_after) + 1

    def get_current_usage(self, key: str) -> int:
        """Get current request count for key."""
        if key not in self.requests:
            return 0

        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Count valid requests in window
        count = sum(1 for req_time in self.requests[key] if req_time >= window_start)
        return count

    async def cleanup(self):
        """Clean up old request records (call periodically)."""
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds * 2)

            # Remove expired keys
            keys_to_remove = []
            for key, req_queue in self.requests.items():
                if not req_queue or req_queue[-1] < window_start:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.requests[key]

            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit keys")


class ChatRateLimiter:
    """
    Chat-specific rate limiter with multiple tiers.

    Prevents spam while allowing legitimate use.
    """

    def __init__(self):
        """Initialize chat rate limiter with default limits."""
        # Per-user message limits
        self.message_limiter = SlidingWindowRateLimiter(
            max_requests=30,  # 30 messages per minute
            window_seconds=60
        )

        # Per-user conversation creation limits
        self.conversation_limiter = SlidingWindowRateLimiter(
            max_requests=10,  # 10 new conversations per hour
            window_seconds=3600
        )

        # Per-IP limits for anonymous chat
        self.ip_limiter = SlidingWindowRateLimiter(
            max_requests=20,  # 20 messages per minute per IP
            window_seconds=60
        )

        # Token bucket for burst protection
        self.token_buckets: Dict[str, TokenBucket] = {}

    async def check_message_limit(self, user_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if user can send a message.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # Check sliding window limit
        allowed, retry_after = await self.message_limiter.is_allowed(user_id)

        if not allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}: {self.message_limiter.get_current_usage(user_id)} messages in window")

        return allowed, retry_after

    async def check_conversation_limit(self, user_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if user can create a new conversation.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        return await self.conversation_limiter.is_allowed(user_id)

    async def check_ip_limit(self, ip_address: str) -> Tuple[bool, Optional[int]]:
        """
        Check if IP can send a message (for anonymous chat).

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        return await self.ip_limiter.is_allowed(ip_address)

    def get_usage_stats(self, user_id: str) -> Dict[str, int]:
        """Get current usage statistics for user."""
        return {
            "messages_in_window": self.message_limiter.get_current_usage(user_id),
            "max_messages": self.message_limiter.max_requests,
            "window_seconds": self.message_limiter.window_seconds,
            "conversations_in_window": self.conversation_limiter.get_current_usage(user_id),
            "max_conversations": self.conversation_limiter.max_requests
        }

    async def cleanup_old_records(self):
        """Clean up old rate limit records."""
        await self.message_limiter.cleanup()
        await self.conversation_limiter.cleanup()
        await self.ip_limiter.cleanup()


# Global rate limiter instance
_chat_rate_limiter: Optional[ChatRateLimiter] = None


def get_chat_rate_limiter() -> ChatRateLimiter:
    """Get or create global chat rate limiter instance."""
    global _chat_rate_limiter

    if _chat_rate_limiter is None:
        _chat_rate_limiter = ChatRateLimiter()
        logger.info("Initialized chat rate limiter")

    return _chat_rate_limiter


async def cleanup_rate_limiters():
    """Background task to cleanup rate limiter records."""
    limiter = get_chat_rate_limiter()

    while True:
        await asyncio.sleep(600)  # Every 10 minutes
        try:
            await limiter.cleanup_old_records()
        except Exception as e:
            logger.error(f"Failed to cleanup rate limiters: {e}")
