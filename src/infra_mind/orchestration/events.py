"""
Event management system for multi-agent orchestration.

Handles event-driven communication between agents and workflow coordination.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events in the orchestration system."""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    DATA_UPDATED = "data_updated"
    USER_INPUT_RECEIVED = "user_input_received"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    REPORT_GENERATED = "report_generated"


@dataclass
class AgentEvent:
    """Event data structure for agent communications."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.AGENT_COMPLETED
    agent_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEvent":
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data.get("event_type", EventType.AGENT_COMPLETED.value)),
            agent_name=data.get("agent_name", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )


class EventManager:
    """
    Event manager for coordinating agent communications.
    
    Provides pub/sub functionality for agent coordination and workflow management.
    """
    
    def __init__(self):
        """Initialize event manager."""
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[AgentEvent] = []
        self.active_workflows: Set[str] = set()
        self._lock = asyncio.Lock()
        
        logger.info("Event manager initialized")
    
    async def subscribe(self, event_type: EventType, callback: Callable[[AgentEvent], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        async with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            
            self.subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type.value} events")
    
    async def unsubscribe(self, event_type: EventType, callback: Callable[[AgentEvent], None]) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        async with self._lock:
            if event_type in self.subscribers:
                try:
                    self.subscribers[event_type].remove(callback)
                    logger.debug(f"Unsubscribed from {event_type.value} events")
                except ValueError:
                    logger.warning(f"Callback not found for {event_type.value} events")
    
    async def publish(self, event: AgentEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        async with self._lock:
            # Add to event history
            self.event_history.append(event)
            
            # Keep only last 1000 events to prevent memory issues
            if len(self.event_history) > 1000:
                self.event_history = self.event_history[-1000:]
            
            logger.info(f"Publishing event: {event.event_type.value} from {event.agent_name}")
            
            # Notify subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in event callback: {str(e)}", exc_info=True)
    
    async def publish_agent_started(self, agent_name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish agent started event."""
        event = AgentEvent(
            event_type=EventType.AGENT_STARTED,
            agent_name=agent_name,
            data=data or {}
        )
        await self.publish(event)
    
    async def publish_agent_completed(self, agent_name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish agent completed event."""
        event = AgentEvent(
            event_type=EventType.AGENT_COMPLETED,
            agent_name=agent_name,
            data=data or {}
        )
        await self.publish(event)
    
    async def publish_agent_failed(self, agent_name: str, error: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish agent failed event."""
        event = AgentEvent(
            event_type=EventType.AGENT_FAILED,
            agent_name=agent_name,
            data=data or {},
            metadata={"error": error}
        )
        await self.publish(event)
    
    async def publish_workflow_started(self, workflow_id: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish workflow started event."""
        self.active_workflows.add(workflow_id)
        event = AgentEvent(
            event_type=EventType.WORKFLOW_STARTED,
            agent_name="orchestrator",
            data=data or {},
            metadata={"workflow_id": workflow_id}
        )
        await self.publish(event)
    
    async def publish_workflow_completed(self, workflow_id: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish workflow completed event."""
        self.active_workflows.discard(workflow_id)
        event = AgentEvent(
            event_type=EventType.WORKFLOW_COMPLETED,
            agent_name="orchestrator",
            data=data or {},
            metadata={"workflow_id": workflow_id}
        )
        await self.publish(event)
    
    async def publish_workflow_failed(self, workflow_id: str, error: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish workflow failed event."""
        self.active_workflows.discard(workflow_id)
        event = AgentEvent(
            event_type=EventType.WORKFLOW_FAILED,
            agent_name="orchestrator",
            data=data or {},
            metadata={"workflow_id": workflow_id, "error": error}
        )
        await self.publish(event)
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         agent_name: Optional[str] = None,
                         limit: int = 100) -> List[AgentEvent]:
        """
        Get event history with optional filtering.
        
        Args:
            event_type: Filter by event type
            agent_name: Filter by agent name
            limit: Maximum number of events to return
            
        Returns:
            List of events matching the criteria
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        return events[-limit:] if limit > 0 else events
    
    def get_active_workflows(self) -> Set[str]:
        """Get set of active workflow IDs."""
        return self.active_workflows.copy()
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        logger.info("Event history cleared")
    
    async def wait_for_event(self, event_type: EventType, 
                           agent_name: Optional[str] = None,
                           timeout: float = 30.0) -> Optional[AgentEvent]:
        """
        Wait for a specific event to occur.
        
        Args:
            event_type: Type of event to wait for
            agent_name: Optional agent name to filter by
            timeout: Maximum time to wait in seconds
            
        Returns:
            The event if it occurs within timeout, None otherwise
        """
        event_received = asyncio.Event()
        received_event = None
        
        async def event_handler(event: AgentEvent):
            nonlocal received_event
            if agent_name is None or event.agent_name == agent_name:
                received_event = event
                event_received.set()
        
        await self.subscribe(event_type, event_handler)
        
        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            return received_event
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for {event_type.value} event")
            return None
        finally:
            await self.unsubscribe(event_type, event_handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics."""
        event_counts = {}
        for event in self.event_history:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_events": len(self.event_history),
            "event_counts": event_counts,
            "active_workflows": len(self.active_workflows),
            "subscriber_counts": {
                event_type.value: len(callbacks) 
                for event_type, callbacks in self.subscribers.items()
            }
        }