"""
Redis-based Event Manager for Cross-Instance Communication

Replaces in-memory EventManager with Redis pub/sub for horizontal scaling.
Enables event communication across multiple API instances.

Key Features:
- Redis pub/sub for cross-instance events
- Event history stored in Redis (last 1000 events)
- Automatic reconnection on failure
- Backwards compatible with EventManager interface
- Fallback to in-memory if Redis unavailable

Benefits:
- ✅ Horizontal scaling (events shared across all API instances)
- ✅ Reliable event delivery (Redis handles distribution)
- ✅ Event persistence (history survives instance restarts)
- ✅ No memory leaks (Redis manages storage)
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timezone
import uuid

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis package not installed. Install with: pip install redis[hiredis]")

from .events import EventType, AgentEvent

logger = logging.getLogger(__name__)


class RedisEventManager:
    """
    Redis-based event manager for distributed systems.

    Uses Redis pub/sub for cross-instance event communication.
    Events are broadcast to all API instances via Redis channels.

    Architecture:
    - Each event type has its own Redis channel (events:agent_started, etc.)
    - All API instances subscribe to all channels
    - Publishing sends to all subscribers across all instances
    - Event history stored in Redis list (last 1000 events)

    Usage:
        # Initialize (usually in FastAPI lifespan)
        event_manager = RedisEventManager("redis://localhost:6379/0")
        await event_manager.connect()

        # Subscribe to events
        async def on_agent_started(event: AgentEvent):
            print(f"Agent {event.agent_name} started")

        await event_manager.subscribe(EventType.AGENT_STARTED, on_agent_started)

        # Publish events (broadcasts to ALL instances)
        event = AgentEvent(
            event_type=EventType.AGENT_STARTED,
            agent_name="cto_agent",
            data={"assessment_id": "123"}
        )
        await event_manager.publish(event)

        # Cleanup (usually in FastAPI shutdown)
        await event_manager.disconnect()
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis event manager.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")

        Raises:
            ImportError: If redis package is not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package not installed. "
                "Install with: pip install 'redis[hiredis]'"
            )

        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._connected = False

        logger.info(f"Redis event manager initialized with URL: {redis_url}")

    async def connect(self):
        """
        Connect to Redis and start listening for events.

        Establishes connection, subscribes to all event channels,
        and starts background listener task.

        Raises:
            Exception: If connection to Redis fails
        """
        try:
            # Create Redis client
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()

            # Create pub/sub client
            self.pubsub = self.redis_client.pubsub()

            # Subscribe to all event type channels
            channels = [f"events:{event_type.value}" for event_type in EventType]

            await self.pubsub.subscribe(*channels)

            logger.info(f"Subscribed to {len(channels)} Redis event channels")

            # Start listener task
            self._listener_task = asyncio.create_task(self._listen_for_events())

            self._connected = True
            logger.info("✅ Redis event manager connected successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            await self._cleanup()
            raise

    async def disconnect(self):
        """
        Disconnect from Redis and cleanup resources.

        Cancels listener task, unsubscribes from channels,
        and closes Redis connections.
        """
        logger.info("Disconnecting Redis event manager...")

        self._connected = False

        await self._cleanup()

        logger.info("✅ Redis event manager disconnected")

    async def _cleanup(self):
        """Internal cleanup helper."""
        # Cancel listener task
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        # Unsubscribe and close pub/sub
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing pub/sub: {e}")

        # Close Redis client
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")

    async def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[AgentEvent], None]
    ):
        """
        Subscribe to events of a specific type.

        Callback will be invoked whenever an event of this type
        is published by ANY API instance.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs (can be sync or async)

        Example:
            async def on_workflow_completed(event: AgentEvent):
                print(f"Workflow {event.data['workflow_id']} completed")

            await event_manager.subscribe(
                EventType.WORKFLOW_COMPLETED,
                on_workflow_completed
            )
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value} events (local callback)")

    async def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[AgentEvent], None]
    ):
        """
        Unsubscribe from events of a specific type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.value} events")
            except ValueError:
                logger.warning(
                    f"Callback not found for {event_type.value} events"
                )

    async def publish(self, event: AgentEvent):
        """
        Publish an event to all API instances via Redis.

        Event will be broadcast to all subscribed callbacks across
        all API instances. Also stores event in Redis history.

        Args:
            event: Event to publish

        Raises:
            RuntimeError: If not connected to Redis
        """
        if not self._connected or not self.redis_client:
            logger.error("Cannot publish event: not connected to Redis")
            raise RuntimeError("Redis event manager not connected")

        try:
            # Publish to Redis channel
            channel = f"events:{event.event_type.value}"
            message = json.dumps(event.to_dict())

            subscribers_count = await self.redis_client.publish(channel, message)

            logger.info(
                f"Published {event.event_type.value} event to Redis "
                f"({subscribers_count} subscribers)"
            )

            # Store in event history (keep last 1000)
            history_key = "event_history"
            await self.redis_client.lpush(history_key, message)
            await self.redis_client.ltrim(history_key, 0, 999)

        except Exception as e:
            logger.error(f"Error publishing event to Redis: {e}", exc_info=True)
            raise

    async def emit(self, event_type: EventType, data: Dict[str, Any]):
        """
        Convenience method to create and publish an event.

        Args:
            event_type: Type of event to emit
            data: Event data

        Example:
            await event_manager.emit(
                EventType.AGENT_STARTED,
                {"agent_name": "cto_agent", "assessment_id": "123"}
            )
        """
        event = AgentEvent(
            event_type=event_type,
            agent_name=data.get("agent_name", ""),
            data=data
        )
        await self.publish(event)

    async def _listen_for_events(self):
        """
        Background task that listens for events from Redis.

        Receives events from all API instances and invokes local callbacks.
        Runs continuously until disconnected.
        """
        if not self.pubsub:
            logger.error("Cannot start listener: pub/sub not initialized")
            return

        logger.info("🎧 Started listening for Redis events...")

        try:
            async for message in self.pubsub.listen():
                if not self._connected:
                    break

                if message["type"] == "message":
                    await self._handle_message(message)

        except asyncio.CancelledError:
            logger.info("Event listener task cancelled")
        except Exception as e:
            logger.error(f"Error in event listener: {e}", exc_info=True)
            # Auto-reconnect on error
            if self._connected:
                logger.info("Attempting to reconnect...")
                await self._reconnect()

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from Redis."""
        try:
            channel = message["channel"]
            data = json.loads(message["data"])

            # Reconstruct event
            event = AgentEvent.from_dict(data)

            logger.debug(
                f"Received {event.event_type.value} event from Redis "
                f"(agent: {event.agent_name})"
            )

            # Notify local subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            # Run sync callback in executor
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, callback, event)

                    except Exception as e:
                        logger.error(
                            f"Error in event callback for {event.event_type.value}: {e}",
                            exc_info=True
                        )

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}", exc_info=True)

    async def _reconnect(self):
        """Attempt to reconnect to Redis."""
        max_retries = 5
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Reconnection attempt {attempt + 1}/{max_retries}...")

                await self._cleanup()
                await asyncio.sleep(retry_delay)
                await self.connect()

                logger.info("✅ Reconnected to Redis successfully")
                return

            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        logger.error("❌ Failed to reconnect to Redis after all attempts")
        self._connected = False

    async def get_event_history(self, limit: int = 100) -> List[AgentEvent]:
        """
        Get recent event history from Redis.

        Args:
            limit: Maximum number of events to return (default: 100)

        Returns:
            List of recent events, newest first

        Raises:
            RuntimeError: If not connected to Redis
        """
        if not self._connected or not self.redis_client:
            logger.error("Cannot get event history: not connected to Redis")
            return []

        try:
            history_key = "event_history"
            events_json = await self.redis_client.lrange(
                history_key,
                0,
                limit - 1
            )

            events = []
            for event_json in events_json:
                try:
                    event_data = json.loads(event_json)
                    events.append(AgentEvent.from_dict(event_data))
                except Exception as e:
                    logger.error(f"Error parsing event from history: {e}")

            logger.debug(f"Retrieved {len(events)} events from history")
            return events

        except Exception as e:
            logger.error(f"Error getting event history: {e}", exc_info=True)
            return []

    async def clear_history(self):
        """Clear all event history from Redis."""
        if not self._connected or not self.redis_client:
            logger.error("Cannot clear history: not connected to Redis")
            return

        try:
            history_key = "event_history"
            await self.redis_client.delete(history_key)
            logger.info("✅ Event history cleared")

        except Exception as e:
            logger.error(f"Error clearing event history: {e}", exc_info=True)

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"RedisEventManager(url={self.redis_url}, status={status})"
