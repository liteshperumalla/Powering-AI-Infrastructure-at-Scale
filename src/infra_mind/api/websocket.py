"""
WebSocket integration for real-time progress updates and notifications.

Provides WebSocket endpoints for real-time communication between the backend
and frontend, including workflow progress updates, notifications, and live
collaboration features.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

from ..orchestration.events import EventManager, AgentEvent, EventType
from ..orchestration.monitoring import WorkflowMonitor, PerformanceAlert
from ..core.auth import get_current_user
from ..models.user import User


logger = logging.getLogger(__name__)
security = HTTPBearer()


class MessageType(str, Enum):
    """WebSocket message types."""
    # Progress updates
    WORKFLOW_PROGRESS = "workflow_progress"
    AGENT_STATUS = "agent_status"
    STEP_COMPLETED = "step_completed"
    
    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"
    
    # Collaboration
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_UPDATE = "cursor_update"
    FORM_UPDATE = "form_update"
    
    # System
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    METRICS_UPDATE = "metrics_update"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class WebSocketConnection:
    """WebSocket connection information."""
    websocket: WebSocket
    user_id: str
    session_id: str
    assessment_id: Optional[str] = None
    subscriptions: Set[str] = None
    last_heartbeat: datetime = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now(timezone.utc)


class WebSocketManager:
    """
    WebSocket connection manager for real-time features.
    
    Manages WebSocket connections, message routing, and real-time updates
    for workflow progress, notifications, and collaboration features.
    """
    
    def __init__(self, event_manager: EventManager, workflow_monitor: WorkflowMonitor):
        """
        Initialize WebSocket manager.
        
        Args:
            event_manager: Event manager for workflow events
            workflow_monitor: Workflow monitor for performance alerts
        """
        self.event_manager = event_manager
        self.workflow_monitor = workflow_monitor
        
        # Connection management
        self.connections: Dict[str, WebSocketConnection] = {}
        self.assessment_rooms: Dict[str, Set[str]] = {}  # assessment_id -> set of session_ids
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        
        # Heartbeat management
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.CURSOR_UPDATE: self._handle_cursor_update,
            MessageType.FORM_UPDATE: self._handle_form_update,
        }
        
        # Setup event subscriptions
        asyncio.create_task(self._setup_event_subscriptions())
        
        logger.info("WebSocket manager initialized")
    
    async def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for real-time updates."""
        # Workflow events
        await self.event_manager.subscribe(EventType.WORKFLOW_STARTED, self._on_workflow_started)
        await self.event_manager.subscribe(EventType.WORKFLOW_COMPLETED, self._on_workflow_completed)
        await self.event_manager.subscribe(EventType.WORKFLOW_FAILED, self._on_workflow_failed)
        
        # Agent events
        await self.event_manager.subscribe(EventType.AGENT_STARTED, self._on_agent_started)
        await self.event_manager.subscribe(EventType.AGENT_COMPLETED, self._on_agent_completed)
        await self.event_manager.subscribe(EventType.AGENT_FAILED, self._on_agent_failed)
        
        # Data events
        await self.event_manager.subscribe(EventType.DATA_UPDATED, self._on_data_updated)
        await self.event_manager.subscribe(EventType.RECOMMENDATION_GENERATED, self._on_recommendation_generated)
        await self.event_manager.subscribe(EventType.REPORT_GENERATED, self._on_report_generated)
        
        # Performance alerts
        self.workflow_monitor.add_alert_callback(self._on_performance_alert)
    
    async def start_heartbeat_monitor(self) -> None:
        """Start heartbeat monitoring task."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            logger.info("Started WebSocket heartbeat monitor")
    
    async def stop_heartbeat_monitor(self) -> None:
        """Stop heartbeat monitoring task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Stopped WebSocket heartbeat monitor")
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor WebSocket connections and send heartbeats."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                disconnected_sessions = []
                
                for session_id, connection in self.connections.items():
                    # Check for stale connections
                    time_since_heartbeat = (current_time - connection.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        logger.warning(f"Connection timeout for session {session_id}")
                        disconnected_sessions.append(session_id)
                    elif time_since_heartbeat > self.heartbeat_interval:
                        # Send heartbeat
                        try:
                            await self._send_to_connection(
                                connection,
                                WebSocketMessage(
                                    type=MessageType.HEARTBEAT,
                                    data={"timestamp": current_time.isoformat()},
                                    timestamp=current_time
                                )
                            )
                        except Exception as e:
                            logger.error(f"Failed to send heartbeat to {session_id}: {e}")
                            disconnected_sessions.append(session_id)
                
                # Clean up disconnected sessions
                for session_id in disconnected_sessions:
                    await self._cleanup_connection(session_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def connect(self, websocket: WebSocket, user: User, assessment_id: Optional[str] = None) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            assessment_id: Optional assessment ID for room-based features
            
        Returns:
            Session ID for the connection
        """
        await websocket.accept()
        
        session_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user.id,
            session_id=session_id,
            assessment_id=assessment_id
        )
        
        # Store connection
        self.connections[session_id] = connection
        
        # Add to user sessions
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = set()
        self.user_sessions[user.id].add(session_id)
        
        # Add to assessment room if specified
        if assessment_id:
            if assessment_id not in self.assessment_rooms:
                self.assessment_rooms[assessment_id] = set()
            self.assessment_rooms[assessment_id].add(session_id)
            
            # Notify other users in the room
            await self._broadcast_to_assessment(
                assessment_id,
                WebSocketMessage(
                    type=MessageType.USER_JOINED,
                    data={
                        "user_id": user.id,
                        "user_name": user.full_name,
                        "session_id": session_id
                    },
                    timestamp=datetime.now(timezone.utc)
                ),
                exclude_session=session_id
            )
        
        # Start heartbeat monitor if not already running
        await self.start_heartbeat_monitor()
        
        logger.info(f"WebSocket connected: user={user.id}, session={session_id}, assessment={assessment_id}")
        return session_id
    
    async def disconnect(self, session_id: str) -> None:
        """
        Handle WebSocket disconnection.
        
        Args:
            session_id: Session ID to disconnect
        """
        await self._cleanup_connection(session_id)
    
    async def _cleanup_connection(self, session_id: str) -> None:
        """Clean up a disconnected connection."""
        if session_id not in self.connections:
            return
        
        connection = self.connections[session_id]
        
        # Remove from user sessions
        if connection.user_id in self.user_sessions:
            self.user_sessions[connection.user_id].discard(session_id)
            if not self.user_sessions[connection.user_id]:
                del self.user_sessions[connection.user_id]
        
        # Remove from assessment room and notify others
        if connection.assessment_id:
            if connection.assessment_id in self.assessment_rooms:
                self.assessment_rooms[connection.assessment_id].discard(session_id)
                
                # Notify other users in the room
                await self._broadcast_to_assessment(
                    connection.assessment_id,
                    WebSocketMessage(
                        type=MessageType.USER_LEFT,
                        data={
                            "user_id": connection.user_id,
                            "session_id": session_id
                        },
                        timestamp=datetime.now(timezone.utc)
                    ),
                    exclude_session=session_id
                )
                
                # Clean up empty room
                if not self.assessment_rooms[connection.assessment_id]:
                    del self.assessment_rooms[connection.assessment_id]
        
        # Close WebSocket connection
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket: {e}")
        
        # Remove connection
        del self.connections[session_id]
        
        logger.info(f"WebSocket disconnected: session={session_id}")
    
    async def handle_message(self, session_id: str, message: str) -> None:
        """
        Handle incoming WebSocket message.
        
        Args:
            session_id: Session ID that sent the message
            message: JSON message string
        """
        try:
            data = json.loads(message)
            message_type = MessageType(data.get("type"))
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](session_id, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self._send_error(session_id, f"Error processing message: {str(e)}")
    
    async def _send_to_connection(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Send message to a specific connection."""
        try:
            await connection.websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Failed to send message to {connection.session_id}: {e}")
            raise
    
    async def _send_to_session(self, session_id: str, message: WebSocketMessage) -> None:
        """Send message to a specific session."""
        if session_id in self.connections:
            await self._send_to_connection(self.connections[session_id], message)
    
    async def _send_error(self, session_id: str, error_message: str) -> None:
        """Send error message to a session."""
        message = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message},
            timestamp=datetime.now(timezone.utc)
        )
        await self._send_to_session(session_id, message)
    
    async def _broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> None:
        """Broadcast message to all sessions of a user."""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id].copy():
                try:
                    await self._send_to_session(session_id, message)
                except Exception as e:
                    logger.error(f"Failed to send to user session {session_id}: {e}")
                    await self._cleanup_connection(session_id)
    
    async def _broadcast_to_assessment(self, assessment_id: str, message: WebSocketMessage, 
                                     exclude_session: Optional[str] = None) -> None:
        """Broadcast message to all users in an assessment room."""
        if assessment_id in self.assessment_rooms:
            for session_id in self.assessment_rooms[assessment_id].copy():
                if session_id != exclude_session:
                    try:
                        await self._send_to_session(session_id, message)
                    except Exception as e:
                        logger.error(f"Failed to send to assessment session {session_id}: {e}")
                        await self._cleanup_connection(session_id)
    
    async def _broadcast_to_all(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected users."""
        for session_id in list(self.connections.keys()):
            try:
                await self._send_to_session(session_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session_id}: {e}")
                await self._cleanup_connection(session_id)
    
    # Message handlers
    
    async def _handle_heartbeat(self, session_id: str, data: Dict[str, Any]) -> None:
        """Handle heartbeat message."""
        if session_id in self.connections:
            self.connections[session_id].last_heartbeat = datetime.now(timezone.utc)
    
    async def _handle_cursor_update(self, session_id: str, data: Dict[str, Any]) -> None:
        """Handle cursor position update for collaboration."""
        if session_id not in self.connections:
            return
        
        connection = self.connections[session_id]
        if not connection.assessment_id:
            return
        
        # Broadcast cursor update to other users in the assessment
        message = WebSocketMessage(
            type=MessageType.CURSOR_UPDATE,
            data={
                "user_id": connection.user_id,
                "session_id": session_id,
                "cursor_position": data.get("cursor_position"),
                "field_id": data.get("field_id")
            },
            timestamp=datetime.now(timezone.utc)
        )
        
        await self._broadcast_to_assessment(
            connection.assessment_id,
            message,
            exclude_session=session_id
        )
    
    async def _handle_form_update(self, session_id: str, data: Dict[str, Any]) -> None:
        """Handle form field update for collaboration."""
        if session_id not in self.connections:
            return
        
        connection = self.connections[session_id]
        if not connection.assessment_id:
            return
        
        # Broadcast form update to other users in the assessment
        message = WebSocketMessage(
            type=MessageType.FORM_UPDATE,
            data={
                "user_id": connection.user_id,
                "session_id": session_id,
                "field_id": data.get("field_id"),
                "field_value": data.get("field_value"),
                "field_type": data.get("field_type")
            },
            timestamp=datetime.now(timezone.utc)
        )
        
        await self._broadcast_to_assessment(
            connection.assessment_id,
            message,
            exclude_session=session_id
        )
    
    # Event handlers
    
    async def _on_workflow_started(self, event: AgentEvent) -> None:
        """Handle workflow started event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.WORKFLOW_PROGRESS,
            data={
                "workflow_id": workflow_id,
                "status": "started",
                "progress": 0,
                "current_step": "initialization",
                "total_steps": event.data.get("total_steps", 0),
                "estimated_duration": event.data.get("estimated_duration")
            },
            timestamp=event.timestamp
        )
        
        # Send to users working on this assessment
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
    
    async def _on_workflow_completed(self, event: AgentEvent) -> None:
        """Handle workflow completed event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.WORKFLOW_PROGRESS,
            data={
                "workflow_id": workflow_id,
                "status": "completed",
                "progress": 100,
                "completed_steps": event.data.get("completed_steps", 0),
                "total_steps": event.data.get("total_steps", 0),
                "duration": event.data.get("duration")
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
        
        # Send notification
        notification_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": "success",
                "title": "Assessment Complete",
                "message": "Your infrastructure assessment has been completed successfully.",
                "workflow_id": workflow_id
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, notification_message)
    
    async def _on_workflow_failed(self, event: AgentEvent) -> None:
        """Handle workflow failed event."""
        workflow_id = event.metadata.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.WORKFLOW_PROGRESS,
            data={
                "workflow_id": workflow_id,
                "status": "failed",
                "error": event.metadata.get("error"),
                "completed_steps": event.data.get("completed_steps", 0),
                "total_steps": event.data.get("total_steps", 0)
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
        
        # Send error notification
        notification_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": "error",
                "title": "Assessment Failed",
                "message": f"Your assessment failed: {event.metadata.get('error', 'Unknown error')}",
                "workflow_id": workflow_id
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, notification_message)
    
    async def _on_agent_started(self, event: AgentEvent) -> None:
        """Handle agent started event."""
        workflow_id = event.data.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.AGENT_STATUS,
            data={
                "workflow_id": workflow_id,
                "agent_name": event.agent_name,
                "status": "started",
                "step_id": event.data.get("step_id"),
                "estimated_duration": event.data.get("estimated_duration")
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
    
    async def _on_agent_completed(self, event: AgentEvent) -> None:
        """Handle agent completed event."""
        workflow_id = event.data.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.AGENT_STATUS,
            data={
                "workflow_id": workflow_id,
                "agent_name": event.agent_name,
                "status": "completed",
                "step_id": event.data.get("step_id"),
                "execution_time": event.data.get("execution_time"),
                "results_summary": event.data.get("results_summary")
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
        
        # Send step completion update
        step_message = WebSocketMessage(
            type=MessageType.STEP_COMPLETED,
            data={
                "workflow_id": workflow_id,
                "agent_name": event.agent_name,
                "step_id": event.data.get("step_id"),
                "progress": event.data.get("progress", 0)
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, step_message)
    
    async def _on_agent_failed(self, event: AgentEvent) -> None:
        """Handle agent failed event."""
        workflow_id = event.data.get("workflow_id")
        if not workflow_id:
            return
        
        message = WebSocketMessage(
            type=MessageType.AGENT_STATUS,
            data={
                "workflow_id": workflow_id,
                "agent_name": event.agent_name,
                "status": "failed",
                "step_id": event.data.get("step_id"),
                "error": event.metadata.get("error")
            },
            timestamp=event.timestamp
        )
        
        if workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
    
    async def _on_data_updated(self, event: AgentEvent) -> None:
        """Handle data updated event."""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": "info",
                "title": "Data Updated",
                "message": f"Data has been updated: {event.data.get('description', 'Unknown update')}",
                "data_type": event.data.get("data_type")
            },
            timestamp=event.timestamp
        )
        
        await self._broadcast_to_all(message)
    
    async def _on_recommendation_generated(self, event: AgentEvent) -> None:
        """Handle recommendation generated event."""
        workflow_id = event.data.get("workflow_id")
        
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": "success",
                "title": "New Recommendation",
                "message": f"New recommendation from {event.agent_name}",
                "agent_name": event.agent_name,
                "workflow_id": workflow_id
            },
            timestamp=event.timestamp
        )
        
        if workflow_id and workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
    
    async def _on_report_generated(self, event: AgentEvent) -> None:
        """Handle report generated event."""
        workflow_id = event.data.get("workflow_id")
        
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": "success",
                "title": "Report Generated",
                "message": "Your infrastructure report is ready for download",
                "report_id": event.data.get("report_id"),
                "report_type": event.data.get("report_type"),
                "workflow_id": workflow_id
            },
            timestamp=event.timestamp
        )
        
        if workflow_id and workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(workflow_id, message)
    
    async def _on_performance_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        message = WebSocketMessage(
            type=MessageType.ALERT,
            data={
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "workflow_id": alert.workflow_id,
                "agent_name": alert.agent_name,
                "metric_name": alert.metric_name,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold
            },
            timestamp=alert.timestamp
        )
        
        # Send to relevant users
        if alert.workflow_id and alert.workflow_id in self.assessment_rooms:
            await self._broadcast_to_assessment(alert.workflow_id, message)
        else:
            # Send to all admin users or broadcast to all
            await self._broadcast_to_all(message)
    
    # Public API
    
    async def send_notification(self, user_id: str, notification_type: str, 
                              title: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send notification to a specific user."""
        notification_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "type": notification_type,
                "title": title,
                "message": message,
                **(data or {})
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id
        )
        
        await self._broadcast_to_user(user_id, notification_message)
    
    async def send_metrics_update(self, metrics_data: Dict[str, Any]) -> None:
        """Send metrics update to all connected users."""
        message = WebSocketMessage(
            type=MessageType.METRICS_UPDATE,
            data=metrics_data,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self._broadcast_to_all(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "total_connections": len(self.connections),
            "active_assessments": len(self.assessment_rooms),
            "connected_users": len(self.user_sessions),
            "assessment_participants": {
                assessment_id: len(sessions)
                for assessment_id, sessions in self.assessment_rooms.items()
            }
        }


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager(event_manager: Optional[EventManager] = None,
                         workflow_monitor: Optional[WorkflowMonitor] = None) -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        if event_manager is None or workflow_monitor is None:
            raise ValueError("EventManager and WorkflowMonitor required for first initialization")
        _websocket_manager = WebSocketManager(event_manager, workflow_monitor)
    return _websocket_manager


async def initialize_websocket_manager(event_manager: EventManager, 
                                     workflow_monitor: WorkflowMonitor) -> None:
    """Initialize the WebSocket manager."""
    manager = get_websocket_manager(event_manager, workflow_monitor)
    await manager.start_heartbeat_monitor()
    logger.info("WebSocket manager initialized")


async def shutdown_websocket_manager() -> None:
    """Shutdown the WebSocket manager."""
    global _websocket_manager
    if _websocket_manager:
        await _websocket_manager.stop_heartbeat_monitor()
        logger.info("WebSocket manager shutdown")