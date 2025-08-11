"""
Event Bus System for Real-time Communication

Centralized event management system supporting publish-subscribe patterns,
event filtering, priority handling, and distributed event processing.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Set, Any, Optional, Callable, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import weakref
from concurrent.futures import ThreadPoolExecutor

from loguru import logger


class EventType(Enum):
    """System event types."""
    # Assessment events
    ASSESSMENT_CREATED = "assessment_created"
    ASSESSMENT_UPDATED = "assessment_updated"
    ASSESSMENT_DELETED = "assessment_deleted"
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"
    
    # Report events
    REPORT_GENERATED = "report_generated"
    REPORT_UPDATED = "report_updated"
    REPORT_SHARED = "report_shared"
    REPORT_EXPORTED = "report_exported"
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_PROGRESS = "analysis_progress"
    
    # Infrastructure events
    INFRASTRUCTURE_DEPLOYED = "infrastructure_deployed"
    INFRASTRUCTURE_UPDATED = "infrastructure_updated"
    INFRASTRUCTURE_DESTROYED = "infrastructure_destroyed"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    
    # Real-time events
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    ROOM_CREATED = "room_created"
    ROOM_DELETED = "room_deleted"
    ROOM_USER_JOINED = "room_user_joined"
    ROOM_USER_LEFT = "room_user_left"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_ALERT = "system_alert"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    
    # Cache events
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_EVICTION = "cache_eviction"
    CACHE_ERROR = "cache_error"
    
    # Security events
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILED = "auth_failed"
    AUTHORIZATION_DENIED = "auth_denied"
    SECURITY_VIOLATION = "security_violation"


class EventPriority(IntEnum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class EventDeliveryMode(Enum):
    """Event delivery modes."""
    FIRE_AND_FORGET = "fire_and_forget"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    delivery_mode: EventDeliveryMode = EventDeliveryMode.FIRE_AND_FORGET
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if event has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


@dataclass
class EventFilter:
    """Event filtering configuration."""
    event_types: Optional[Set[EventType]] = None
    sources: Optional[Set[str]] = None
    priority_min: Optional[EventPriority] = None
    priority_max: Optional[EventPriority] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check source
        if self.sources and event.source not in self.sources:
            return False
        
        # Check priority range
        if self.priority_min and event.priority < self.priority_min:
            return False
        
        if self.priority_max and event.priority > self.priority_max:
            return False
        
        # Check metadata filters
        for key, value in self.metadata_filters.items():
            if key not in event.metadata or event.metadata[key] != value:
                return False
        
        return True


# Type alias for event handlers
EventHandler = Union[
    Callable[[Event], None],
    Callable[[Event], Awaitable[None]]
]


@dataclass
class Subscription:
    """Event subscription information."""
    subscription_id: str
    handler: EventHandler
    event_filter: EventFilter
    created_at: datetime = field(default_factory=datetime.utcnow)
    call_count: int = 0
    error_count: int = 0
    last_called: Optional[datetime] = None
    last_error: Optional[str] = None
    is_active: bool = True


@dataclass
class EventBusMetrics:
    """Event bus metrics."""
    total_events_published: int = 0
    total_events_delivered: int = 0
    total_events_failed: int = 0
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    events_by_type: Dict[EventType, int] = field(default_factory=lambda: defaultdict(int))
    events_by_priority: Dict[EventPriority, int] = field(default_factory=lambda: defaultdict(int))
    delivery_latency_ms: List[float] = field(default_factory=list)
    
    def get_average_latency(self) -> float:
        """Get average delivery latency."""
        if not self.delivery_latency_ms:
            return 0.0
        return sum(self.delivery_latency_ms) / len(self.delivery_latency_ms)


class EventBus:
    """
    Advanced event bus system for real-time communication.
    
    Provides publish-subscribe messaging with priority handling,
    event filtering, retry mechanisms, and delivery guarantees.
    """
    
    def __init__(self, max_queue_size: int = 10000, num_workers: int = 5):
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in EventPriority
        }
        self.metrics = EventBusMetrics()
        self.is_running = False
        self.num_workers = num_workers
        self.workers: List[asyncio.Task] = []
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        
        # Event history for debugging and replay
        self.event_history: deque = deque(maxlen=1000)
        
    async def start(self):
        """Start the event bus."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks for each priority level
        for priority in EventPriority:
            for i in range(self.num_workers):
                worker = asyncio.create_task(
                    self._event_worker(priority, f"worker-{priority.name}-{i}")
                )
                self.workers.append(worker)
        
        # Start maintenance task
        maintenance_task = asyncio.create_task(self._maintenance_task())
        self.workers.append(maintenance_task)
        
        logger.info(f"Event bus started with {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the event bus."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all worker tasks
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to complete
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("Event bus stopped")
    
    def subscribe(
        self,
        event_types: Union[EventType, List[EventType], Set[EventType]],
        handler: EventHandler,
        event_filter: Optional[EventFilter] = None,
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_types: Event type(s) to subscribe to
            handler: Event handler function
            event_filter: Optional event filter
            subscription_id: Optional custom subscription ID
            
        Returns:
            Subscription ID
        """
        # Normalize event_types to set
        if isinstance(event_types, EventType):
            event_types_set = {event_types}
        elif isinstance(event_types, (list, set)):
            event_types_set = set(event_types)
        else:
            raise ValueError("event_types must be EventType, list, or set")
        
        # Create event filter if not provided
        if event_filter is None:
            event_filter = EventFilter(event_types=event_types_set)
        else:
            # Merge event types into existing filter
            if event_filter.event_types:
                event_filter.event_types.update(event_types_set)
            else:
                event_filter.event_types = event_types_set
        
        # Generate subscription ID if not provided
        if subscription_id is None:
            subscription_id = str(uuid.uuid4())
        
        # Create subscription
        subscription = Subscription(
            subscription_id=subscription_id,
            handler=handler,
            event_filter=event_filter
        )
        
        self.subscriptions[subscription_id] = subscription
        self.metrics.total_subscriptions += 1
        self.metrics.active_subscriptions += 1
        
        logger.debug(f"Subscription {subscription_id} created for {event_types_set}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if subscription was removed, False if not found
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return False
        
        if subscription.is_active:
            self.metrics.active_subscriptions -= 1
        
        del self.subscriptions[subscription_id]
        
        logger.debug(f"Subscription {subscription_id} removed")
        return True
    
    async def publish(self, event: Event) -> bool:
        """
        Publish an event.
        
        Args:
            event: Event to publish
            
        Returns:
            True if event was queued successfully
        """
        if not self.is_running:
            logger.warning("Event bus is not running")
            return False
        
        # Check if event has expired
        if event.is_expired():
            logger.debug(f"Event {event.event_id} expired before publishing")
            return False
        
        try:
            # Add to appropriate priority queue
            queue = self.event_queues[event.priority]
            
            # Try to add to queue (non-blocking)
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for priority {event.priority}, dropping event {event.event_id}")
                return False
            
            # Add to history
            self.event_history.append(event)
            
            # Update metrics
            self.metrics.total_events_published += 1
            self.metrics.events_by_type[event.event_type] += 1
            self.metrics.events_by_priority[event.priority] += 1
            
            logger.debug(f"Event {event.event_id} ({event.event_type}) published with priority {event.priority}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing event {event.event_id}: {e}")
            return False
    
    async def publish_simple(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish a simple event.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Event source identifier
            priority: Event priority
            correlation_id: Correlation ID for event tracking
            
        Returns:
            True if event was published successfully
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            priority=priority,
            correlation_id=correlation_id
        )
        
        return await self.publish(event)
    
    async def _event_worker(self, priority: EventPriority, worker_name: str):
        """Event processing worker for a specific priority level."""
        queue = self.event_queues[priority]
        
        while self.is_running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # Process event
                await self._process_event(event)
                
                # Mark task as done
                queue.task_done()
                
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def _process_event(self, event: Event):
        """Process a single event by delivering to matching subscriptions."""
        start_time = datetime.utcnow()
        
        try:
            # Check if event has expired
            if event.is_expired():
                logger.debug(f"Event {event.event_id} expired before processing")
                return
            
            # Find matching subscriptions
            matching_subscriptions = []
            for subscription in self.subscriptions.values():
                if subscription.is_active and subscription.event_filter.matches(event):
                    matching_subscriptions.append(subscription)
            
            if not matching_subscriptions:
                logger.debug(f"No subscriptions for event {event.event_id} ({event.event_type})")
                return
            
            # Deliver event to all matching subscriptions
            delivery_tasks = []
            for subscription in matching_subscriptions:
                task = asyncio.create_task(self._deliver_event(event, subscription))
                delivery_tasks.append(task)
            
            # Wait for all deliveries to complete
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            # Count successful deliveries
            successful_deliveries = sum(1 for result in results if result is True)
            failed_deliveries = len(results) - successful_deliveries
            
            self.metrics.total_events_delivered += successful_deliveries
            self.metrics.total_events_failed += failed_deliveries
            
            # Calculate delivery latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.delivery_latency_ms.append(latency)
            
            # Keep only recent latency measurements
            if len(self.metrics.delivery_latency_ms) > 1000:
                self.metrics.delivery_latency_ms = self.metrics.delivery_latency_ms[-1000:]
            
            logger.debug(f"Event {event.event_id} processed: {successful_deliveries} delivered, {failed_deliveries} failed")
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            self.metrics.total_events_failed += 1
    
    async def _deliver_event(self, event: Event, subscription: Subscription) -> bool:
        """Deliver event to a specific subscription."""
        try:
            subscription.call_count += 1
            subscription.last_called = datetime.utcnow()
            
            # Call handler
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(event)
            else:
                # Run synchronous handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, subscription.handler, event)
            
            logger.debug(f"Event {event.event_id} delivered to subscription {subscription.subscription_id}")
            return True
            
        except Exception as e:
            subscription.error_count += 1
            subscription.last_error = str(e)
            
            logger.error(f"Error delivering event {event.event_id} to subscription {subscription.subscription_id}: {e}")
            
            # Handle retry logic for critical events
            if (event.priority >= EventPriority.HIGH and 
                event.retry_count < event.max_retries):
                
                event.retry_count += 1
                logger.info(f"Retrying event {event.event_id} (attempt {event.retry_count}/{event.max_retries})")
                
                # Re-queue event with slight delay
                await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                await self.publish(event)
            else:
                # Move to dead letter queue
                self.dead_letter_queue.append(event)
                logger.warning(f"Event {event.event_id} moved to dead letter queue")
            
            return False
    
    async def _maintenance_task(self):
        """Background maintenance task."""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Clean up expired events from history
                expired_events = []
                for event in self.event_history:
                    if event.is_expired():
                        expired_events.append(event)
                
                for event in expired_events:
                    self.event_history.remove(event)
                
                # Clean up inactive subscriptions (optional)
                inactive_subscriptions = []
                for sub_id, subscription in self.subscriptions.items():
                    if (subscription.last_called and 
                        current_time - subscription.last_called > timedelta(hours=24) and
                        subscription.error_count > subscription.call_count * 0.5):  # High error rate
                        inactive_subscriptions.append(sub_id)
                
                for sub_id in inactive_subscriptions:
                    subscription = self.subscriptions[sub_id]
                    logger.warning(f"Deactivating subscription {sub_id} due to high error rate")
                    subscription.is_active = False
                    self.metrics.active_subscriptions -= 1
                
                # Wait before next maintenance cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Maintenance task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def get_subscription_stats(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific subscription."""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        return {
            "subscription_id": subscription.subscription_id,
            "created_at": subscription.created_at.isoformat(),
            "call_count": subscription.call_count,
            "error_count": subscription.error_count,
            "success_rate": (subscription.call_count - subscription.error_count) / max(subscription.call_count, 1),
            "last_called": subscription.last_called.isoformat() if subscription.last_called else None,
            "last_error": subscription.last_error,
            "is_active": subscription.is_active
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            "is_running": self.is_running,
            "total_events_published": self.metrics.total_events_published,
            "total_events_delivered": self.metrics.total_events_delivered,
            "total_events_failed": self.metrics.total_events_failed,
            "total_subscriptions": self.metrics.total_subscriptions,
            "active_subscriptions": self.metrics.active_subscriptions,
            "events_by_type": {event_type.value: count for event_type, count in self.metrics.events_by_type.items()},
            "events_by_priority": {priority.name: count for priority, count in self.metrics.events_by_priority.items()},
            "average_delivery_latency_ms": self.metrics.get_average_latency(),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "event_history_size": len(self.event_history),
            "queue_sizes": {
                priority.name: queue.qsize() for priority, queue in self.event_queues.items()
            }
        }
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history."""
        events = list(self.event_history)[-limit:]
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "priority": event.priority.name,
                "correlation_id": event.correlation_id,
                "retry_count": event.retry_count
            }
            for event in events
        ]
    
    def replay_events(
        self,
        event_filter: Optional[EventFilter] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """
        Replay events matching criteria.
        
        Args:
            event_filter: Optional filter for events
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of matching events
        """
        matching_events = []
        
        for event in self.event_history:
            # Check time range
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            # Check event filter
            if event_filter and not event_filter.matches(event):
                continue
            
            matching_events.append(event)
        
        return matching_events
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()