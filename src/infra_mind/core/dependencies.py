"""
FastAPI Dependency Injection Providers

Centralized location for all dependency injection logic.
Enables testability, horizontal scaling, and loose coupling.

Key Benefits:
- Testable: Can override dependencies in tests with mocks
- Scalable: No global singletons preventing horizontal scaling
- Type-safe: FastAPI validates dependency types
- Maintainable: Explicit dependencies, no hidden coupling
"""

import logging
from typing import Optional, Annotated
from fastapi import Depends
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ============================================================================
# LLM Manager Dependencies
# ============================================================================

def get_llm_manager():
    """
    Provide EnhancedLLMManager instance.

    Creates a new instance per request. This is safe because EnhancedLLMManager
    is stateless and lightweight.

    Returns:
        EnhancedLLMManager instance

    Usage:
        @router.post("/endpoint")
        async def endpoint(llm_manager: LLMManagerDep):
            result = await llm_manager.generate(...)
    """
    from ..llm.enhanced_llm_manager import EnhancedLLMManager
    from ..core.config import settings

    return EnhancedLLMManager(
        default_model=getattr(settings, 'llm_model', 'gpt-4'),
        strict_mode=getattr(settings, 'llm_strict_mode', True)
    )


@lru_cache()
def get_cached_llm_manager():
    """
    Provide cached EnhancedLLMManager instance (singleton-like but controllable).

    Use this for better performance when initialization is expensive.
    Can be cleared for testing: get_cached_llm_manager.cache_clear()

    Returns:
        Cached EnhancedLLMManager instance

    Usage:
        @router.post("/endpoint")
        async def endpoint(llm_manager: CachedLLMManagerDep):
            result = await llm_manager.generate(...)
    """
    from ..llm.enhanced_llm_manager import EnhancedLLMManager
    from ..core.config import settings

    logger.info("Creating cached LLM manager instance")

    return EnhancedLLMManager(
        default_model=getattr(settings, 'llm_model', 'gpt-4'),
        strict_mode=getattr(settings, 'llm_strict_mode', True)
    )


# Type aliases for convenience
LLMManagerDep = Annotated["EnhancedLLMManager", Depends(get_llm_manager)]
CachedLLMManagerDep = Annotated["EnhancedLLMManager", Depends(get_cached_llm_manager)]


# ============================================================================
# Database Dependencies
# ============================================================================

# Database connection pool (application-level, one per API instance)
_db_client: Optional[AsyncIOMotorClient] = None


async def get_database_client() -> AsyncIOMotorClient:
    """
    Get database client with connection pooling.

    Creates one client per application instance (not per request).
    This is safe because Motor manages connection pooling internally.

    Returns:
        AsyncIOMotorClient with connection pool

    Note:
        This maintains a single client per API instance, which is the
        recommended pattern for Motor/AsyncIO MongoDB driver.
    """
    global _db_client

    if _db_client is None:
        from ..core.config import settings

        logger.info("🔌 Initializing database client with connection pool")

        # Get database URL from settings
        import os

        # Try settings first
        db_url = None
        if hasattr(settings, 'mongodb_url'):
            db_url = settings.mongodb_url
        elif hasattr(settings, 'database_url'):
            db_url = settings.database_url

        # Handle Pydantic SecretStr
        if db_url and hasattr(db_url, 'get_secret_value'):
            db_url = db_url.get_secret_value()

        # Fallback to environment variable
        if not db_url:
            db_url = os.getenv("INFRA_MIND_MONGODB_URL")

        if not db_url:
            raise ValueError("Database URL not configured. Set INFRA_MIND_MONGODB_URL environment variable.")

        # Create client with connection pooling
        _db_client = AsyncIOMotorClient(
            db_url,
            maxPoolSize=getattr(settings, 'mongodb_max_connections', 100),
            minPoolSize=getattr(settings, 'mongodb_min_connections', 10),
            maxIdleTimeMS=45000,  # Keep connections alive
            waitQueueTimeoutMS=10000,  # Wait time for connection from pool
            connectTimeoutMS=10000,  # Connection timeout
            serverSelectionTimeoutMS=10000,  # Server selection timeout
            socketTimeoutMS=30000,  # Socket timeout
            heartbeatFrequencyMS=10000  # Heartbeat frequency
        )

        # Test connection
        try:
            await _db_client.admin.command('ping')
            logger.info("✅ Database client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            _db_client = None
            raise

    return _db_client


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance with dependency injection.

    Provides access to the MongoDB database with connection pooling.
    Use this in all endpoints via dependency injection.

    Returns:
        AsyncIOMotorDatabase instance

    Usage:
        @router.get("/assessments")
        async def get_assessments(db: DatabaseDep):
            assessments = await db.assessments.find({}).to_list(100)
            return assessments

    Benefits:
        - Automatic connection pooling
        - Testable (can mock in tests)
        - Type-safe (FastAPI validates types)
        - No global state issues
    """
    from ..core.config import settings

    client = await get_database_client()
    db_name = getattr(settings, 'database_name', 'infra_mind')

    return client.get_database(db_name)


# Type alias for convenience
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


# ============================================================================
# Event Manager Dependencies
# ============================================================================

# Event manager (application-level, one per API instance)
_event_manager: Optional["RedisEventManager"] = None


async def get_event_manager():
    """
    Get Redis-based event manager for cross-instance communication.

    Creates one event manager per application instance.
    Uses Redis pub/sub for event communication across multiple API instances.

    Returns:
        RedisEventManager instance

    Usage:
        @router.post("/assessments/{id}/analyze")
        async def analyze(
            id: str,
            event_manager: EventManagerDep
        ):
            await event_manager.publish(event)

    Note:
        Requires Redis to be running and configured.
        Falls back to in-memory EventManager if Redis is not available.
    """
    global _event_manager

    if _event_manager is None:
        from ..core.config import settings
        import os

        logger.info("🔌 Initializing event manager")

        # Get Redis URL
        redis_url = getattr(settings, 'redis_url', None) or os.getenv("REDIS_URL") or "redis://localhost:6379/0"

        try:
            # Try to use Redis-based event manager
            from ..orchestration.redis_event_manager import RedisEventManager

            _event_manager = RedisEventManager(redis_url)
            await _event_manager.connect()

            logger.info("✅ Redis event manager initialized (cross-instance support)")

        except ImportError:
            # Redis event manager not available, use in-memory fallback
            logger.warning("⚠️ Redis event manager not available, using in-memory fallback")
            logger.warning("⚠️ Events will NOT be shared across multiple API instances")

            from ..orchestration.events import EventManager
            _event_manager = EventManager()

            logger.info("✅ In-memory event manager initialized (single-instance only)")

        except Exception as e:
            # Redis connection failed, use in-memory fallback
            logger.warning(f"⚠️ Redis connection failed: {e}, using in-memory fallback")
            logger.warning("⚠️ Events will NOT be shared across multiple API instances")

            from ..orchestration.events import EventManager
            _event_manager = EventManager()

            logger.info("✅ In-memory event manager initialized (single-instance only)")

    return _event_manager


# Type alias
EventManagerDep = Annotated["EventManager", Depends(get_event_manager)]


# ============================================================================
# Application Lifecycle Management
# ============================================================================

async def close_database_client():
    """
    Close database client on application shutdown.

    Call this in FastAPI lifespan/shutdown event.
    """
    global _db_client

    if _db_client:
        logger.info("🔌 Closing database client...")
        _db_client.close()
        _db_client = None
        logger.info("✅ Database client closed")


async def close_event_manager():
    """
    Close event manager on application shutdown.

    Call this in FastAPI lifespan/shutdown event.
    """
    global _event_manager

    if _event_manager:
        logger.info("🔌 Closing event manager...")

        # Check if it's Redis-based (has disconnect method)
        if hasattr(_event_manager, 'disconnect'):
            await _event_manager.disconnect()

        _event_manager = None
        logger.info("✅ Event manager closed")


async def cleanup_dependencies():
    """
    Cleanup all dependencies on application shutdown.

    Call this in FastAPI lifespan/shutdown event:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        yield
        # Shutdown
        await cleanup_dependencies()
    """
    await close_database_client()
    await close_event_manager()
    logger.info("✅ All dependencies cleaned up")


# ============================================================================
# Testing Utilities
# ============================================================================

def clear_dependency_cache():
    """
    Clear all cached dependencies.

    Use this in tests to reset singleton-like caches:

    def test_something():
        clear_dependency_cache()
        # Test with fresh instances
    """
    global _db_client, _event_manager

    # Clear LRU caches
    get_cached_llm_manager.cache_clear()

    # Reset global instances
    _db_client = None
    _event_manager = None

    logger.info("🧪 Dependency cache cleared (for testing)")


# ============================================================================
# Backwards Compatibility (DEPRECATED)
# ============================================================================

async def get_database_legacy():
    """
    Legacy function for backwards compatibility.

    DEPRECATED: Use DatabaseDep with dependency injection instead.

    This function is kept to maintain compatibility with existing code
    during the migration period. It will be removed in a future release.
    """
    logger.warning(
        "DEPRECATED: get_database_legacy() is deprecated. "
        "Use DatabaseDep with dependency injection instead."
    )
    return await get_database()
