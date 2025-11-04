# Week 3-4: Singleton Removal & Dependency Injection

**Date:** November 4, 2025
**Phase:** Phase 1 - Critical Fixes
**Expected Impact:** Enable horizontal scaling, improve testability, remove tight coupling

---

## 📋 Executive Summary

This week focuses on removing global singleton patterns and implementing proper dependency injection throughout the codebase. This is **critical for horizontal scaling** - the system currently cannot run multiple API instances due to singleton-based shared state.

### Key Objectives:
1. ✅ Remove `get_enhanced_llm_manager()` singleton pattern
2. ✅ Implement dependency injection for database connections
3. ✅ Refactor EventManager to use Redis pub/sub (for cross-instance communication)
4. ✅ Update all endpoints to use FastAPI `Depends()` pattern
5. ✅ Enable horizontal scaling across multiple servers

---

## 🔍 Singleton Patterns Identified

### 1. EnhancedLLMManager Singleton ⚠️ CRITICAL
**File:** `src/infra_mind/llm/enhanced_llm_manager.py:309-326`

```python
# CURRENT (SINGLETON - BAD):
_enhanced_manager_instance = None

def get_enhanced_llm_manager(
    base_manager=None,
    model: str = "gpt-4",
    strict_mode: bool = True
) -> EnhancedLLMManager:
    """Get or create enhanced LLM manager instance."""
    global _enhanced_manager_instance

    if _enhanced_manager_instance is None:
        _enhanced_manager_instance = EnhancedLLMManager(
            base_manager=base_manager,
            default_model=model,
            strict_mode=strict_mode
        )

    return _enhanced_manager_instance
```

**Problems:**
- ❌ Not thread-safe (race conditions in async context)
- ❌ Prevents horizontal scaling (shared state across workers)
- ❌ Cannot test with mocks (global state persists)
- ❌ Hidden dependencies (implicit coupling)
- ❌ Memory leak (never garbage collected)

**Usage Locations:** 1 file (not widely used - GOOD!)

---

### 2. Database Connection Singleton ⚠️ HIGH PRIORITY
**File:** `src/infra_mind/core/database.py:63-64`

```python
# CURRENT (SINGLETON - BAD):
class ProductionDatabase:
    client: Optional[AsyncIOMotorClient] = None  # Class variable = shared state
    database = None
    _connection_pool_stats: Dict[str, Any] = {}

# Global instance
db = ProductionDatabase()
```

**Problems:**
- ❌ Single connection pool shared across all workers
- ❌ Cannot scale horizontally (each server needs own pool)
- ❌ Connection pool exhaustion under load
- ❌ Testing requires global state reset

**Usage Locations:** 50+ files (WIDELY USED!)

---

### 3. EventManager - NOT A SINGLETON ✅
**File:** `src/infra_mind/orchestration/events.py:67-82`

```python
# CURRENT (GOOD - NOT A SINGLETON):
class EventManager:
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[AgentEvent] = []
        self.active_workflows: Set[str] = set()
```

**Status:** ✅ Already properly designed (not a singleton)

**However:** Uses in-memory event storage which doesn't work across multiple API instances. We'll refactor to use **Redis pub/sub** for cross-instance communication.

---

## 🏗️ Dependency Injection Architecture

### FastAPI Dependency Injection Pattern

FastAPI has built-in dependency injection using `Depends()`:

```python
from fastapi import Depends
from typing import Annotated

# Define dependency provider
async def get_llm_manager() -> EnhancedLLMManager:
    """Provide LLM manager instance (fresh per request or cached)."""
    return EnhancedLLMManager(
        default_model="gpt-4",
        strict_mode=True
    )

# Use in endpoint
@router.post("/assessments/{id}/analyze")
async def analyze_assessment(
    id: str,
    llm_manager: Annotated[EnhancedLLMManager, Depends(get_llm_manager)],
    current_user: User = Depends(get_current_user)
):
    # llm_manager is injected automatically by FastAPI
    result = await llm_manager.generate(...)
    return result
```

**Benefits:**
- ✅ Testable (can override dependencies in tests)
- ✅ Type-safe (FastAPI validates types)
- ✅ Explicit dependencies (no hidden coupling)
- ✅ Flexible (can swap implementations easily)
- ✅ Cacheable (can use `lru_cache` for singletons if needed)

---

## 🔧 Implementation Plan

### Task 1: Remove EnhancedLLMManager Singleton (Day 1)

#### Step 1: Create Dependency Provider
**File:** `src/infra_mind/core/dependencies.py` (NEW)

```python
"""
FastAPI dependency injection providers.

Centralized location for all dependency injection logic.
"""

import logging
from typing import Optional, Annotated
from fastapi import Depends
from functools import lru_cache

from ..llm.enhanced_llm_manager import EnhancedLLMManager
from ..core.config import settings

logger = logging.getLogger(__name__)


# LLM Manager Dependency
def get_llm_manager() -> EnhancedLLMManager:
    """
    Provide EnhancedLLMManager instance.

    Creates a new instance per request. For heavy initialization,
    use @lru_cache() to cache the instance.
    """
    return EnhancedLLMManager(
        default_model=settings.llm_model or "gpt-4",
        strict_mode=settings.llm_strict_mode or True
    )


# Optional: Cached version for performance
@lru_cache()
def get_cached_llm_manager() -> EnhancedLLMManager:
    """
    Provide cached EnhancedLLMManager instance (singleton-like but controllable).

    Use this for better performance when initialization is expensive.
    Can be cleared for testing: get_cached_llm_manager.cache_clear()
    """
    logger.info("Creating cached LLM manager instance")
    return EnhancedLLMManager(
        default_model=settings.llm_model or "gpt-4",
        strict_mode=settings.llm_strict_mode or True
    )


# Type alias for convenience
LLMManagerDep = Annotated[EnhancedLLMManager, Depends(get_llm_manager)]
```

#### Step 2: Remove Singleton Function
**File:** `src/infra_mind/llm/enhanced_llm_manager.py:309-326`

```python
# DELETE THIS ENTIRE SECTION:
# _enhanced_manager_instance = None
# def get_enhanced_llm_manager(...): ...

# No replacement needed - use dependency injection instead!
```

#### Step 3: Update Usage (if any)
Search for `get_enhanced_llm_manager()` and replace with dependency injection:

```python
# BEFORE:
from ..llm.enhanced_llm_manager import get_enhanced_llm_manager

@router.post("/endpoint")
async def endpoint():
    manager = get_enhanced_llm_manager()  # BAD
    result = await manager.generate(...)

# AFTER:
from ..core.dependencies import LLMManagerDep

@router.post("/endpoint")
async def endpoint(llm_manager: LLMManagerDep):
    result = await llm_manager.generate(...)  # GOOD
```

---

### Task 2: Database Connection Dependency Injection (Days 2-3)

This is more complex due to widespread usage (50+ files).

#### Step 1: Create Database Dependency Provider
**File:** `src/infra_mind/core/dependencies.py` (ADD)

```python
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from ..core.config import settings


# Database Connection Pool (application-level singleton)
_db_client: Optional[AsyncIOMotorClient] = None

async def get_database_client() -> AsyncIOMotorClient:
    """
    Get database client with connection pooling.

    Creates one client per application (not per request).
    """
    global _db_client

    if _db_client is None:
        logger.info("Initializing database client with connection pool")

        _db_client = AsyncIOMotorClient(
            settings.get_database_url(),
            maxPoolSize=settings.mongodb_max_connections or 100,
            minPoolSize=settings.mongodb_min_connections or 10,
            maxIdleTimeMS=45000,
            waitQueueTimeoutMS=10000,
            serverSelectionTimeoutMS=10000
        )

        # Test connection
        await _db_client.admin.command('ping')
        logger.info("✅ Database client initialized successfully")

    return _db_client


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.

    Provides access to the database with connection pooling.
    Use this in all endpoints via dependency injection.
    """
    client = await get_database_client()
    return client.get_database(settings.database_name or "infra_mind")


# Type alias for convenience
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]
```

#### Step 2: Gradual Migration Strategy

**Phase 2a:** New endpoints use dependency injection (immediate)
**Phase 2b:** Refactor high-traffic endpoints (Week 4)
**Phase 2c:** Refactor remaining endpoints (Week 5)

```python
# NEW ENDPOINTS (immediate):
from ..core.dependencies import DatabaseDep

@router.get("/new-endpoint")
async def new_endpoint(db: DatabaseDep):
    results = await db.assessments.find({}).to_list(100)
    return results

# OLD ENDPOINTS (refactor gradually):
from ..core.database import get_database

@router.get("/old-endpoint")
async def old_endpoint():
    db = await get_database()  # OLD WAY (still works)
    results = await db.assessments.find({}).to_list(100)
    return results
```

#### Step 3: Update Core Database Module
**File:** `src/infra_mind/core/database.py`

Keep `get_database()` function for backwards compatibility, but internally use dependency injection logic:

```python
async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance (legacy function).

    DEPRECATED: Use dependency injection with DatabaseDep instead.
    This function is kept for backwards compatibility.
    """
    # Import here to avoid circular dependency
    from .dependencies import get_database as get_db_new
    return await get_db_new()
```

---

### Task 3: EventManager Redis Pub/Sub (Days 4-5)

Refactor EventManager to use Redis for cross-instance communication.

#### Step 1: Create Redis-Based EventManager
**File:** `src/infra_mind/orchestration/redis_event_manager.py` (NEW)

```python
"""
Redis-based event manager for cross-instance communication.

Replaces in-memory EventManager with Redis pub/sub for horizontal scaling.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import redis.asyncio as aioredis

from .events import EventType, AgentEvent

logger = logging.getLogger(__name__)


class RedisEventManager:
    """
    Redis-based event manager for distributed systems.

    Uses Redis pub/sub for cross-instance event communication.
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis event manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self._listener_task: Optional[asyncio.Task] = None

        logger.info(f"Redis event manager initialized with URL: {redis_url}")

    async def connect(self):
        """Connect to Redis and start listening."""
        self.redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        self.pubsub = self.redis_client.pubsub()

        # Subscribe to all event channels
        for event_type in EventType:
            channel = f"events:{event_type.value}"
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")

        # Start listener task
        self._listener_task = asyncio.create_task(self._listen_for_events())

        logger.info("✅ Redis event manager connected")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Redis event manager disconnected")

    async def subscribe(self, event_type: EventType, callback: Callable[[AgentEvent], None]):
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value} events")

    async def publish(self, event: AgentEvent):
        """
        Publish an event to all instances via Redis.

        Args:
            event: Event to publish
        """
        if not self.redis_client:
            logger.error("Redis client not connected")
            return

        channel = f"events:{event.event_type.value}"
        message = json.dumps(event.to_dict())

        await self.redis_client.publish(channel, message)
        logger.info(f"Published event to Redis: {event.event_type.value}")

        # Also store in Redis list for history (keep last 1000)
        history_key = "event_history"
        await self.redis_client.lpush(history_key, message)
        await self.redis_client.ltrim(history_key, 0, 999)  # Keep only last 1000

    async def _listen_for_events(self):
        """Listen for events from Redis pub/sub."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    # Reconstruct event
                    event = AgentEvent.from_dict(data)

                    # Notify local subscribers
                    if event.event_type in self.subscribers:
                        for callback in self.subscribers[event.event_type]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(event)
                                else:
                                    callback(event)
                            except Exception as e:
                                logger.error(f"Error in event callback: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.info("Event listener task cancelled")
        except Exception as e:
            logger.error(f"Error in event listener: {e}", exc_info=True)

    async def get_event_history(self, limit: int = 100) -> List[AgentEvent]:
        """
        Get recent event history from Redis.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        if not self.redis_client:
            return []

        history_key = "event_history"
        events_json = await self.redis_client.lrange(history_key, 0, limit - 1)

        events = []
        for event_json in events_json:
            try:
                event_data = json.loads(event_json)
                events.append(AgentEvent.from_dict(event_data))
            except Exception as e:
                logger.error(f"Error parsing event: {e}")

        return events
```

#### Step 2: Create EventManager Dependency
**File:** `src/infra_mind/core/dependencies.py` (ADD)

```python
from ..orchestration.redis_event_manager import RedisEventManager

# Event Manager (application-level singleton)
_event_manager: Optional[RedisEventManager] = None

async def get_event_manager() -> RedisEventManager:
    """
    Get Redis-based event manager.

    Creates one event manager per application for cross-instance communication.
    """
    global _event_manager

    if _event_manager is None:
        logger.info("Initializing Redis event manager")

        redis_url = settings.redis_url or "redis://localhost:6379/0"
        _event_manager = RedisEventManager(redis_url)
        await _event_manager.connect()

        logger.info("✅ Redis event manager initialized")

    return _event_manager


# Type alias
EventManagerDep = Annotated[RedisEventManager, Depends(get_event_manager)]
```

#### Step 3: Update Usage
```python
# BEFORE (in-memory EventManager):
from ..orchestration.events import EventManager

event_manager = EventManager()  # Each instance has own events
await event_manager.publish(event)

# AFTER (Redis-based):
from ..core.dependencies import EventManagerDep

@router.post("/endpoint")
async def endpoint(event_manager: EventManagerDep):
    await event_manager.publish(event)  # Shared across all instances!
```

---

## 📊 Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Horizontal Scaling** | ❌ Not possible | ✅ Unlimited | Infinite scale |
| **Test Coverage** | 10% (hard to test) | 60%+ (easy to mock) | 6x better |
| **Memory Leaks** | ❌ Singleton never GC'd | ✅ No leaks | Fixed |
| **Thread Safety** | ❌ Race conditions | ✅ Safe | Fixed |
| **Coupling** | ❌ High (global state) | ✅ Low (DI) | Much better |
| **API Instances** | 1 (cannot scale) | Unlimited | Infinite scale |

---

## 🧪 Testing Strategy

### Unit Tests with Dependency Injection

```python
# tests/test_assessments_with_di.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.infra_mind.main import app
from src.infra_mind.core.dependencies import get_llm_manager, get_database


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing."""
    mock = AsyncMock(spec=EnhancedLLMManager)
    mock.generate.return_value = LLMResponse(
        content="Test response",
        tokens_used=100,
        model_used="gpt-4",
        sanitization_applied=True,
        budget_validated=True,
        json_validated=False,
        warnings=[],
        success=True
    )
    return mock


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    mock = AsyncMock()
    mock.assessments.find_one.return_value = {
        "_id": "test_id",
        "user_id": "test_user",
        "status": "completed"
    }
    return mock


def test_assessment_with_mocks(mock_llm_manager, mock_database):
    """Test assessment endpoint with mocked dependencies."""

    # Override dependencies
    app.dependency_overrides[get_llm_manager] = lambda: mock_llm_manager
    app.dependency_overrides[get_database] = lambda: mock_database

    client = TestClient(app)
    response = client.post("/api/v1/assessments/test_id/analyze")

    assert response.status_code == 200
    assert mock_llm_manager.generate.called
    assert mock_database.assessments.find_one.called

    # Cleanup
    app.dependency_overrides.clear()
```

---

## 📅 Week 3-4 Timeline

### Week 3: Core Refactoring

**Day 1 (Monday):**
- [ ] Create `dependencies.py` with LLM manager provider
- [ ] Remove `get_enhanced_llm_manager()` singleton
- [ ] Test LLM manager dependency injection

**Day 2 (Tuesday):**
- [ ] Create database dependency provider
- [ ] Update 10 high-traffic endpoints to use DatabaseDep
- [ ] Test database dependency injection

**Day 3 (Wednesday):**
- [ ] Create Redis event manager implementation
- [ ] Create event manager dependency provider
- [ ] Test cross-instance event communication

**Day 4 (Thursday):**
- [ ] Update 20 more endpoints to use dependency injection
- [ ] Write unit tests with mocked dependencies
- [ ] Test horizontal scaling with 2 API instances

**Day 5 (Friday):**
- [ ] Update remaining high-priority endpoints
- [ ] Load testing with multiple instances
- [ ] Documentation and code review

### Week 4: Complete Migration

**Day 1-2 (Monday-Tuesday):**
- [ ] Update all remaining endpoints (50+ files)
- [ ] Remove old singleton code
- [ ] Comprehensive testing

**Day 3-4 (Wednesday-Thursday):**
- [ ] Integration testing with real workloads
- [ ] Performance benchmarking
- [ ] Fix any issues discovered

**Day 5 (Friday):**
- [ ] Final testing and validation
- [ ] Documentation updates
- [ ] Deploy to production

---

## 🚀 Deployment Strategy

### Step 1: Deploy with Backwards Compatibility
- Keep old singleton functions working
- New code uses dependency injection
- Gradual migration over 2 weeks

### Step 2: Test Horizontal Scaling
```bash
# Start 3 API instances
docker-compose up --scale api=3

# Test load balancing
for i in {1..100}; do
  curl http://localhost:8000/api/v1/assessments
done

# Verify events shared across instances
curl http://localhost:8000/api/v1/events/history
```

### Step 3: Remove Old Code (After 2 weeks)
- Delete singleton functions
- Remove backwards compatibility code
- Clean up unused imports

---

## ✅ Success Criteria

**Code Quality:**
- [ ] No global singletons remaining
- [ ] All endpoints use dependency injection
- [ ] 80%+ unit test coverage
- [ ] Type hints on all dependency functions

**Performance:**
- [ ] System can run 3+ API instances simultaneously
- [ ] Event communication < 10ms between instances
- [ ] No memory leaks detected
- [ ] Database connections properly pooled

**Scalability:**
- [ ] Load balancer distributes traffic evenly
- [ ] Can handle 100+ concurrent requests
- [ ] Horizontal scaling works (add/remove instances dynamically)
- [ ] No shared state issues

---

**Document Version:** 1.0
**Status:** Planning Phase
**Start Date:** November 4, 2025
**Target Completion:** November 22, 2025 (18 days)

---

*Week 3-4 singleton removal and dependency injection implementation enables true horizontal scaling and sets the foundation for enterprise deployment.*
