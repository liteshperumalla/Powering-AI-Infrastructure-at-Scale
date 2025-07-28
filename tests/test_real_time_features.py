"""
Tests for real-time features including WebSocket integration, notifications,
live collaboration, and real-time metrics dashboard.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infra_mind.api.websocket import (
    WebSocketManager, WebSocketMessage, MessageType, WebSocketConnection
)
from infra_mind.orchestration.events import EventManager, EventType as WorkflowEventType, AgentEvent
from infra_mind.orchestration.monitoring import WorkflowMonitor, PerformanceAlert, AlertSeverity
from infra_mind.models.user import User


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    @pytest.fixture
    async def event_manager(self):
        """Create event manager for testing."""
        return EventManager()
    
    @pytest.fixture
    async def workflow_monitor(self, event_manager):
        """Create workflow monitor for testing."""
        return WorkflowMonitor(event_manager)
    
    @pytest.fixture
    async def websocket_manager(self, event_manager, workflow_monitor):
        """Create WebSocket manager for testing."""
        return WebSocketManager(event_manager, workflow_monitor)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="test_user_123",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, websocket_manager, mock_websocket, test_user):
        """Test WebSocket connection establishment."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "assessment_123")
        
        # Verify connection
        assert session_id in websocket_manager.connections
        connection = websocket_manager.connections[session_id]
        assert connection.user_id == test_user.id
        assert connection.assessment_id == "assessment_123"
        assert connection.websocket == mock_websocket
        
        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify user was added to assessment room
        assert "assessment_123" in websocket_manager.assessment_rooms
        assert session_id in websocket_manager.assessment_rooms["assessment_123"]
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection(self, websocket_manager, mock_websocket, test_user):
        """Test WebSocket disconnection cleanup."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "assessment_123")
        
        # Disconnect user
        await websocket_manager.disconnect(session_id)
        
        # Verify cleanup
        assert session_id not in websocket_manager.connections
        assert test_user.id not in websocket_manager.user_sessions
        assert "assessment_123" not in websocket_manager.assessment_rooms
        
        # Verify WebSocket was closed
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_handling(self, websocket_manager, mock_websocket, test_user):
        """Test WebSocket message handling."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "assessment_123")
        
        # Test heartbeat message
        heartbeat_message = json.dumps({
            "type": "heartbeat",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await websocket_manager.handle_message(session_id, heartbeat_message)
        
        # Verify heartbeat was processed (connection should still exist)
        assert session_id in websocket_manager.connections
        
        # Test cursor update message
        cursor_message = json.dumps({
            "type": "cursor_update",
            "cursor_position": {"x": 100, "y": 200, "fieldId": "test_field"},
            "field_id": "test_field"
        })
        
        await websocket_manager.handle_message(session_id, cursor_message)
        
        # Verify message was processed (no errors)
        assert session_id in websocket_manager.connections
    
    @pytest.mark.asyncio
    async def test_workflow_event_handling(self, websocket_manager, event_manager, mock_websocket, test_user):
        """Test workflow event handling and broadcasting."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "workflow_123")
        
        # Publish workflow started event
        await event_manager.publish_workflow_started("workflow_123", {
            "name": "Test Workflow",
            "total_steps": 5,
            "estimated_duration": 300
        })
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        workflow_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'workflow_progress'
        ]
        
        assert len(workflow_messages) > 0
        workflow_msg = workflow_messages[0]
        assert workflow_msg['data']['workflow_id'] == "workflow_123"
        assert workflow_msg['data']['status'] == "started"
        assert workflow_msg['data']['progress'] == 0
    
    @pytest.mark.asyncio
    async def test_agent_event_handling(self, websocket_manager, event_manager, mock_websocket, test_user):
        """Test agent event handling and broadcasting."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "workflow_123")
        
        # Publish agent started event
        agent_event = AgentEvent(
            event_type=WorkflowEventType.AGENT_STARTED,
            agent_name="test_agent",
            data={
                "workflow_id": "workflow_123",
                "step_id": "step_1",
                "estimated_duration": 30
            }
        )
        
        await event_manager.publish(agent_event)
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        agent_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'agent_status'
        ]
        
        assert len(agent_messages) > 0
        agent_msg = agent_messages[0]
        assert agent_msg['data']['agent_name'] == "test_agent"
        assert agent_msg['data']['status'] == "started"
    
    @pytest.mark.asyncio
    async def test_performance_alert_handling(self, websocket_manager, workflow_monitor, mock_websocket, test_user):
        """Test performance alert handling and broadcasting."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "workflow_123")
        
        # Create performance alert
        alert = PerformanceAlert(
            alert_type="high_cpu_usage",
            severity=AlertSeverity.HIGH,
            message="CPU usage exceeded 80%",
            workflow_id="workflow_123",
            metric_name="cpu_usage_percent",
            metric_value=85.0,
            threshold=80.0
        )
        
        # Trigger alert
        await workflow_monitor._trigger_alert(alert)
        
        # Wait for alert processing
        await asyncio.sleep(0.1)
        
        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        alert_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'alert'
        ]
        
        assert len(alert_messages) > 0
        alert_msg = alert_messages[0]
        assert alert_msg['data']['alert_type'] == "high_cpu_usage"
        assert alert_msg['data']['severity'] == "high"
        assert alert_msg['data']['message'] == "CPU usage exceeded 80%"
    
    @pytest.mark.asyncio
    async def test_collaboration_features(self, websocket_manager, mock_websocket, test_user):
        """Test live collaboration features."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "assessment_123")
        
        # Connect second user
        mock_websocket2 = Mock(spec=WebSocket)
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        mock_websocket2.close = AsyncMock()
        
        test_user2 = User(
            id="test_user_456",
            email="test2@example.com",
            full_name="Test User 2",
            hashed_password="hashed_password",
            is_active=True
        )
        
        session_id2 = await websocket_manager.connect(mock_websocket2, test_user2, "assessment_123")
        
        # Test form update collaboration
        form_update_message = json.dumps({
            "type": "form_update",
            "field_id": "company_size",
            "field_value": "large",
            "field_type": "select"
        })
        
        await websocket_manager.handle_message(session_id, form_update_message)
        
        # Wait for message processing
        await asyncio.sleep(0.1)
        
        # Verify second user received the form update
        mock_websocket2.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket2.send_text.call_args_list]
        form_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'form_update'
        ]
        
        assert len(form_messages) > 0
        form_msg = form_messages[0]
        assert form_msg['data']['field_id'] == "company_size"
        assert form_msg['data']['field_value'] == "large"
        assert form_msg['data']['user_id'] == test_user.id
    
    @pytest.mark.asyncio
    async def test_notification_system(self, websocket_manager, mock_websocket, test_user):
        """Test notification system."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user)
        
        # Send notification
        await websocket_manager.send_notification(
            user_id=test_user.id,
            notification_type="success",
            title="Test Notification",
            message="This is a test notification",
            data={"extra": "data"}
        )
        
        # Wait for message processing
        await asyncio.sleep(0.1)
        
        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        notification_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'notification'
        ]
        
        assert len(notification_messages) > 0
        notification_msg = notification_messages[0]
        assert notification_msg['data']['type'] == "success"
        assert notification_msg['data']['title'] == "Test Notification"
        assert notification_msg['data']['message'] == "This is a test notification"
        assert notification_msg['data']['extra'] == "data"
    
    @pytest.mark.asyncio
    async def test_metrics_updates(self, websocket_manager, mock_websocket, test_user):
        """Test real-time metrics updates."""
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user)
        
        # Send metrics update
        metrics_data = {
            "system_health": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 67.8,
                "response_time_ms": 245
            },
            "workflow_metrics": {
                "active_workflows": 3,
                "completed_workflows": 15
            }
        }
        
        await websocket_manager.send_metrics_update(metrics_data)
        
        # Wait for message processing
        await asyncio.sleep(0.1)
        
        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called()
        
        # Check message content
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        metrics_messages = [
            json.loads(msg) for msg in sent_messages 
            if json.loads(msg).get('type') == 'metrics_update'
        ]
        
        assert len(metrics_messages) > 0
        metrics_msg = metrics_messages[0]
        assert metrics_msg['data']['system_health']['cpu_usage_percent'] == 45.2
        assert metrics_msg['data']['workflow_metrics']['active_workflows'] == 3
    
    def test_websocket_message_serialization(self):
        """Test WebSocket message serialization."""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={"title": "Test", "message": "Test message"},
            timestamp=datetime.now(timezone.utc),
            user_id="user_123",
            session_id="session_456"
        )
        
        # Test to_dict
        message_dict = message.to_dict()
        assert message_dict['type'] == 'notification'
        assert message_dict['data']['title'] == "Test"
        assert message_dict['user_id'] == "user_123"
        assert message_dict['session_id'] == "session_456"
        assert 'timestamp' in message_dict
        
        # Test to_json
        message_json = message.to_json()
        parsed = json.loads(message_json)
        assert parsed['type'] == 'notification'
        assert parsed['data']['title'] == "Test"
    
    def test_connection_stats(self, websocket_manager):
        """Test connection statistics."""
        stats = websocket_manager.get_connection_stats()
        
        assert 'total_connections' in stats
        assert 'active_assessments' in stats
        assert 'connected_users' in stats
        assert 'assessment_participants' in stats
        
        assert stats['total_connections'] == 0
        assert stats['active_assessments'] == 0
        assert stats['connected_users'] == 0


class TestWebSocketIntegration:
    """Test WebSocket integration with FastAPI."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api.app import app
        return TestClient(app)
    
    def test_websocket_status_endpoint(self, client):
        """Test WebSocket status endpoint."""
        response = client.get("/api/websocket/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'timestamp' in data
        assert 'connections' in data
        assert 'features' in data
        
        expected_features = [
            "Real-time progress updates",
            "Live collaboration",
            "Instant notifications",
            "Performance alerts",
            "Team chat"
        ]
        
        for feature in expected_features:
            assert feature in data['features']


class TestRealTimeFeatures:
    """Integration tests for real-time features."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end real-time workflow."""
        # This would be a comprehensive integration test
        # that tests the full workflow from WebSocket connection
        # to receiving real-time updates
        
        # Setup
        event_manager = EventManager()
        workflow_monitor = WorkflowMonitor(event_manager)
        websocket_manager = WebSocketManager(event_manager, workflow_monitor)
        
        # Mock WebSocket and user
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        test_user = User(
            id="integration_user",
            email="integration@example.com",
            full_name="Integration User",
            hashed_password="hashed_password",
            is_active=True
        )
        
        # Connect user
        session_id = await websocket_manager.connect(mock_websocket, test_user, "integration_assessment")
        
        # Simulate workflow events
        await event_manager.publish_workflow_started("integration_assessment", {
            "name": "Integration Test Workflow",
            "total_steps": 3
        })
        
        # Simulate agent events
        agent_event = AgentEvent(
            event_type=WorkflowEventType.AGENT_COMPLETED,
            agent_name="test_agent",
            data={
                "workflow_id": "integration_assessment",
                "step_id": "step_1",
                "execution_time": 2.5,
                "results_summary": "Test completed successfully"
            }
        )
        await event_manager.publish(agent_event)
        
        # Simulate workflow completion
        await event_manager.publish_workflow_completed("integration_assessment", {
            "completed_steps": 3,
            "total_steps": 3,
            "duration": 180
        })
        
        # Wait for all events to be processed
        await asyncio.sleep(0.2)
        
        # Verify messages were sent
        assert mock_websocket.send_text.call_count >= 3  # At least workflow start, agent complete, workflow complete
        
        # Verify message types
        sent_messages = [call.args[0] for call in mock_websocket.send_text.call_args_list]
        message_types = [json.loads(msg)['type'] for msg in sent_messages]
        
        assert 'workflow_progress' in message_types
        assert 'agent_status' in message_types
        
        # Cleanup
        await websocket_manager.disconnect(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])