"""
WebSocket Manager for Real-time Communication

Advanced WebSocket management system with connection pooling,
room-based messaging, automatic reconnection, and scalable event handling.
"""

import json
import asyncio
import uuid
from typing import Dict, List, Set, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import weakref
from collections import defaultdict

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException
from loguru import logger

from ..models.user import User
from .event_bus import EventBus, EventType


class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types."""
    HEARTBEAT = "heartbeat"
    AUTHENTICATION = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe" 
    DATA = "data"
    ERROR = "error"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    ROOM_JOIN = "room_join"
    ROOM_LEAVE = "room_leave"
    ROOM_MESSAGE = "room_message"


@dataclass
class WebSocketConnection:
    """WebSocket connection information."""
    connection_id: str
    websocket: WebSocketServerProtocol
    user_id: Optional[str] = None
    user: Optional[User] = None
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: Optional[str] = None
    target_room: Optional[str] = None
    requires_auth: bool = False


@dataclass
class RoomInfo:
    """Room information for managing grouped connections."""
    room_id: str
    name: str
    description: str = ""
    max_connections: int = 100
    created_at: datetime = field(default_factory=datetime.utcnow)
    owner_id: Optional[str] = None
    is_private: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """Manages WebSocket connections and rooms."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.rooms: Dict[str, RoomInfo] = {}
        self.room_connections: Dict[str, Set[str]] = defaultdict(set)  # room_id -> connection_ids
        self.subscription_connections: Dict[str, Set[str]] = defaultdict(set)  # topic -> connection_ids
        self._cleanup_task: Optional[asyncio.Task] = None
        
    def add_connection(self, connection: WebSocketConnection):
        """Add a new WebSocket connection."""
        self.connections[connection.connection_id] = connection
        
        if connection.user_id:
            self.user_connections[connection.user_id].add(connection.connection_id)
        
        logger.info(f"Connection {connection.connection_id} added. Total: {len(self.connections)}")
    
    def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        # Remove from user connections
        if connection.user_id:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from rooms
        for room_id in connection.rooms.copy():
            self.leave_room(connection_id, room_id)
        
        # Remove from subscriptions
        for topic in connection.subscriptions.copy():
            self.unsubscribe(connection_id, topic)
        
        # Remove the connection
        del self.connections[connection_id]
        logger.info(f"Connection {connection_id} removed. Total: {len(self.connections)}")
    
    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get connection by ID."""
        return self.connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Get all connections for a user."""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[conn_id] for conn_id in connection_ids 
                if conn_id in self.connections]
    
    def create_room(self, room_info: RoomInfo):
        """Create a new room."""
        self.rooms[room_info.room_id] = room_info
        logger.info(f"Room {room_info.room_id} created")
    
    def delete_room(self, room_id: str):
        """Delete a room and remove all connections."""
        if room_id not in self.rooms:
            return
        
        # Remove all connections from room
        connection_ids = self.room_connections[room_id].copy()
        for connection_id in connection_ids:
            self.leave_room(connection_id, room_id)
        
        # Delete room
        del self.rooms[room_id]
        del self.room_connections[room_id]
        logger.info(f"Room {room_id} deleted")
    
    def join_room(self, connection_id: str, room_id: str) -> bool:
        """Add connection to a room."""
        connection = self.connections.get(connection_id)
        room = self.rooms.get(room_id)
        
        if not connection or not room:
            return False
        
        # Check room capacity
        if len(self.room_connections[room_id]) >= room.max_connections:
            logger.warning(f"Room {room_id} is at capacity")
            return False
        
        # Add to room
        self.room_connections[room_id].add(connection_id)
        connection.rooms.add(room_id)
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
        return True
    
    def leave_room(self, connection_id: str, room_id: str):
        """Remove connection from a room."""
        connection = self.connections.get(connection_id)
        
        if connection and room_id in connection.rooms:
            connection.rooms.remove(room_id)
        
        self.room_connections[room_id].discard(connection_id)
        
        # Clean up empty room connections
        if not self.room_connections[room_id]:
            del self.room_connections[room_id]
        
        logger.info(f"Connection {connection_id} left room {room_id}")
    
    def get_room_connections(self, room_id: str) -> List[WebSocketConnection]:
        """Get all connections in a room."""
        connection_ids = self.room_connections.get(room_id, set())
        return [self.connections[conn_id] for conn_id in connection_ids 
                if conn_id in self.connections]
    
    def subscribe(self, connection_id: str, topic: str):
        """Subscribe connection to a topic."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscriptions.add(topic)
            self.subscription_connections[topic].add(connection_id)
            logger.debug(f"Connection {connection_id} subscribed to {topic}")
    
    def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe connection from a topic."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(topic)
            self.subscription_connections[topic].discard(connection_id)
            
            # Clean up empty subscriptions
            if not self.subscription_connections[topic]:
                del self.subscription_connections[topic]
            
            logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
    
    def get_topic_connections(self, topic: str) -> List[WebSocketConnection]:
        """Get all connections subscribed to a topic."""
        connection_ids = self.subscription_connections.get(topic, set())
        return [self.connections[conn_id] for conn_id in connection_ids 
                if conn_id in self.connections]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics."""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len([c for c in self.connections.values() if c.user_id]),
            "total_users": len(self.user_connections),
            "total_rooms": len(self.rooms),
            "total_subscriptions": len(self.subscription_connections),
            "connections_by_state": {
                state.value: len([c for c in self.connections.values() if c.state == state])
                for state in ConnectionState
            }
        }


class WebSocketManager:
    """
    Advanced WebSocket manager with real-time capabilities.
    
    Provides connection management, room-based messaging, event handling,
    and integration with the event bus for scalable real-time features.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connection_manager = ConnectionManager()
        self.server = None
        self.is_running = False
        self.host = "localhost"
        self.port = 8765
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # seconds
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.AUTHENTICATION: self._handle_authentication,
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.ROOM_JOIN: self._handle_room_join,
            MessageType.ROOM_LEAVE: self._handle_room_leave,
            MessageType.ROOM_MESSAGE: self._handle_room_message,
        }
        
        # Register event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register event bus handlers."""
        self.event_bus.subscribe(EventType.ASSESSMENT_UPDATED, self._on_assessment_updated)
        self.event_bus.subscribe(EventType.REPORT_GENERATED, self._on_report_generated)
        self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self._on_analysis_completed)
        self.event_bus.subscribe(EventType.SYSTEM_ALERT, self._on_system_alert)
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server."""
        self.host = host
        self.port = port
        
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                host,
                port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.is_running = True
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_task())
            asyncio.create_task(self._cleanup_task())
            
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("WebSocket server stopped")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTING
        )
        
        self.connection_manager.add_connection(connection)
        connection.state = ConnectionState.CONNECTED
        
        try:
            # Send welcome message
            await self._send_message(connection, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={"message": "Connected successfully", "connection_id": connection_id}
            ))
            
            # Handle messages
            async for raw_message in websocket:
                try:
                    message_data = json.loads(raw_message)
                    message = WebSocketMessage(
                        type=MessageType(message_data.get("type")),
                        data=message_data.get("data"),
                        sender_id=connection.user_id
                    )
                    
                    await self._handle_message(connection, message)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Invalid message from {connection_id}: {e}")
                    await self._send_error(connection, "Invalid message format")
                
        except ConnectionClosed:
            logger.info(f"Connection {connection_id} closed normally")
        except WebSocketException as e:
            logger.warning(f"WebSocket error for {connection_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for {connection_id}: {e}")
        finally:
            connection.state = ConnectionState.DISCONNECTED
            self.connection_manager.remove_connection(connection_id)
    
    async def _handle_message(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle incoming message."""
        # Update last heartbeat
        connection.last_heartbeat = datetime.utcnow()
        
        # Check authentication requirement
        if message.requires_auth and not connection.user_id:
            await self._send_error(connection, "Authentication required")
            return
        
        # Get message handler
        handler = self.message_handlers.get(message.type)
        if handler:
            await handler(connection, message)
        else:
            logger.warning(f"No handler for message type: {message.type}")
            await self._send_error(connection, f"Unknown message type: {message.type.value}")
    
    async def _handle_heartbeat(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle heartbeat message."""
        await self._send_message(connection, WebSocketMessage(
            type=MessageType.HEARTBEAT,
            data={"timestamp": datetime.utcnow().isoformat()}
        ))
    
    async def _handle_authentication(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle authentication message."""
        try:
            token = message.data.get("token")
            if not token:
                await self._send_error(connection, "Token required")
                return
            
            # TODO: Implement actual token validation
            # For now, simulate authentication
            user_id = message.data.get("user_id", "anonymous")
            
            connection.user_id = user_id
            self.connection_manager.user_connections[user_id].add(connection.connection_id)
            
            await self._send_message(connection, WebSocketMessage(
                type=MessageType.AUTHENTICATION,
                data={"status": "authenticated", "user_id": user_id}
            ))
            
            logger.info(f"Connection {connection.connection_id} authenticated as {user_id}")
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self._send_error(connection, "Authentication failed")
    
    async def _handle_subscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle subscription message."""
        topic = message.data.get("topic")
        if not topic:
            await self._send_error(connection, "Topic required")
            return
        
        self.connection_manager.subscribe(connection.connection_id, topic)
        
        await self._send_message(connection, WebSocketMessage(
            type=MessageType.SUBSCRIBE,
            data={"topic": topic, "status": "subscribed"}
        ))
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle unsubscription message."""
        topic = message.data.get("topic")
        if not topic:
            await self._send_error(connection, "Topic required")
            return
        
        self.connection_manager.unsubscribe(connection.connection_id, topic)
        
        await self._send_message(connection, WebSocketMessage(
            type=MessageType.UNSUBSCRIBE,
            data={"topic": topic, "status": "unsubscribed"}
        ))
    
    async def _handle_room_join(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle room join message."""
        room_id = message.data.get("room_id")
        if not room_id:
            await self._send_error(connection, "Room ID required")
            return
        
        # Create room if it doesn't exist
        if room_id not in self.connection_manager.rooms:
            room_info = RoomInfo(
                room_id=room_id,
                name=message.data.get("room_name", room_id),
                description=message.data.get("description")
            )
            self.connection_manager.create_room(room_info)
        
        success = self.connection_manager.join_room(connection.connection_id, room_id)
        
        if success:
            await self._send_message(connection, WebSocketMessage(
                type=MessageType.ROOM_JOIN,
                data={"room_id": room_id, "status": "joined"}
            ))
            
            # Notify other room members
            await self._broadcast_to_room(room_id, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    "message": f"User {connection.user_id or 'Anonymous'} joined the room",
                    "room_id": room_id
                }
            ), exclude_connection=connection.connection_id)
        else:
            await self._send_error(connection, "Failed to join room")
    
    async def _handle_room_leave(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle room leave message."""
        room_id = message.data.get("room_id")
        if not room_id:
            await self._send_error(connection, "Room ID required")
            return
        
        self.connection_manager.leave_room(connection.connection_id, room_id)
        
        await self._send_message(connection, WebSocketMessage(
            type=MessageType.ROOM_LEAVE,
            data={"room_id": room_id, "status": "left"}
        ))
        
        # Notify other room members
        await self._broadcast_to_room(room_id, WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "message": f"User {connection.user_id or 'Anonymous'} left the room",
                "room_id": room_id
            }
        ))
    
    async def _handle_room_message(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle room message."""
        room_id = message.data.get("room_id")
        content = message.data.get("content")
        
        if not room_id or not content:
            await self._send_error(connection, "Room ID and content required")
            return
        
        # Broadcast message to room
        await self._broadcast_to_room(room_id, WebSocketMessage(
            type=MessageType.ROOM_MESSAGE,
            data={
                "room_id": room_id,
                "sender_id": connection.user_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
    
    async def _send_message(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Send message to a specific connection."""
        try:
            if connection.state != ConnectionState.CONNECTED:
                return
            
            message_data = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            }
            
            await connection.websocket.send(json.dumps(message_data))
            
        except ConnectionClosed:
            logger.info(f"Connection {connection.connection_id} closed while sending message")
            connection.state = ConnectionState.DISCONNECTED
        except Exception as e:
            logger.error(f"Error sending message to {connection.connection_id}: {e}")
    
    async def _send_error(self, connection: WebSocketConnection, error_message: str):
        """Send error message to connection."""
        await self._send_message(connection, WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message}
        ))
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients."""
        tasks = []
        for connection in self.connection_manager.connections.values():
            if connection.state == ConnectionState.CONNECTED:
                tasks.append(self._send_message(connection, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage):
        """Broadcast message to all connections of a specific user."""
        connections = self.connection_manager.get_user_connections(user_id)
        tasks = []
        
        for connection in connections:
            if connection.state == ConnectionState.CONNECTED:
                tasks.append(self._send_message(connection, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _broadcast_to_room(
        self, 
        room_id: str, 
        message: WebSocketMessage, 
        exclude_connection: Optional[str] = None
    ):
        """Broadcast message to all connections in a room."""
        connections = self.connection_manager.get_room_connections(room_id)
        tasks = []
        
        for connection in connections:
            if (connection.state == ConnectionState.CONNECTED and 
                connection.connection_id != exclude_connection):
                tasks.append(self._send_message(connection, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """Broadcast message to all connections subscribed to a topic."""
        connections = self.connection_manager.get_topic_connections(topic)
        tasks = []
        
        for connection in connections:
            if connection.state == ConnectionState.CONNECTED:
                tasks.append(self._send_message(connection, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _heartbeat_task(self):
        """Background task to send heartbeats and check connection health."""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                timeout_threshold = current_time - timedelta(seconds=self.connection_timeout)
                
                # Check for timed out connections
                timeout_connections = []
                for connection in self.connection_manager.connections.values():
                    if connection.last_heartbeat < timeout_threshold:
                        timeout_connections.append(connection)
                
                # Clean up timed out connections
                for connection in timeout_connections:
                    logger.info(f"Connection {connection.connection_id} timed out")
                    connection.state = ConnectionState.DISCONNECTED
                    try:
                        await connection.websocket.close()
                    except:
                        pass
                    self.connection_manager.remove_connection(connection.connection_id)
                
                # Wait for next heartbeat interval
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Heartbeat task error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _cleanup_task(self):
        """Background task for general cleanup."""
        while self.is_running:
            try:
                # Clean up empty rooms
                empty_rooms = [
                    room_id for room_id, connections in self.connection_manager.room_connections.items()
                    if not connections
                ]
                
                for room_id in empty_rooms:
                    if room_id in self.connection_manager.rooms:
                        room = self.connection_manager.rooms[room_id]
                        # Only delete rooms that are not permanent
                        if not room.metadata.get("permanent", False):
                            self.connection_manager.delete_room(room_id)
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(300)
    
    # Event handlers for integration with event bus
    
    async def _on_assessment_updated(self, event_data: Dict[str, Any]):
        """Handle assessment updated event."""
        assessment_id = event_data.get("assessment_id")
        if assessment_id:
            await self.broadcast_to_topic(f"assessment:{assessment_id}", WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    "event": "assessment_updated",
                    "assessment_id": assessment_id,
                    "data": event_data
                }
            ))
    
    async def _on_report_generated(self, event_data: Dict[str, Any]):
        """Handle report generated event."""
        report_id = event_data.get("report_id")
        user_id = event_data.get("user_id")
        
        if user_id:
            await self.broadcast_to_user(user_id, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    "event": "report_generated",
                    "report_id": report_id,
                    "data": event_data
                }
            ))
    
    async def _on_analysis_completed(self, event_data: Dict[str, Any]):
        """Handle analysis completed event."""
        analysis_id = event_data.get("analysis_id")
        if analysis_id:
            await self.broadcast_to_topic(f"analysis:{analysis_id}", WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    "event": "analysis_completed",
                    "analysis_id": analysis_id,
                    "data": event_data
                }
            ))
    
    async def _on_system_alert(self, event_data: Dict[str, Any]):
        """Handle system alert event."""
        severity = event_data.get("severity", "info")
        
        # Broadcast to all users for high severity alerts
        if severity in ["error", "critical"]:
            await self.broadcast_to_all(WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    "event": "system_alert",
                    "severity": severity,
                    "data": event_data
                }
            ))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "server_status": "running" if self.is_running else "stopped",
            "host": self.host,
            "port": self.port,
            **self.connection_manager.get_stats()
        }