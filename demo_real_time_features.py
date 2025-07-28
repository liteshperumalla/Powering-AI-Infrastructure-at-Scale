#!/usr/bin/env python3
"""
Real-Time Features Demo Script

Demonstrates the WebSocket integration, notification system, live collaboration,
and real-time metrics dashboard functionality of the Infra Mind platform.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import websockets
import requests
from concurrent.futures import ThreadPoolExecutor
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.orchestration.events import EventManager, EventType
from infra_mind.orchestration.monitoring import WorkflowMonitor
from infra_mind.api.websocket import WebSocketManager
from infra_mind.core.metrics_collector import get_metrics_collector
from infra_mind.models.user import User


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealTimeFeaturesDemo:
    """Demo class for real-time features."""
    
    def __init__(self):
        """Initialize the demo."""
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000"
        self.auth_token = None
        self.user_id = None
        self.assessment_id = None
        
        # Demo users
        self.demo_users = [
            {"email": "alice@example.com", "password": "password123", "full_name": "Alice Johnson"},
            {"email": "bob@example.com", "password": "password123", "full_name": "Bob Smith"},
            {"email": "charlie@example.com", "password": "password123", "full_name": "Charlie Brown"}
        ]
        
        self.user_tokens = {}
        self.websockets = {}
    
    async def setup_demo_environment(self):
        """Set up the demo environment with users and assessment."""
        logger.info("Setting up demo environment...")
        
        # Register and login demo users
        for user_data in self.demo_users:
            try:
                # Register user
                register_response = requests.post(
                    f"{self.base_url}/api/auth/register",
                    json=user_data
                )
                
                if register_response.status_code in [200, 201]:
                    logger.info(f"Registered user: {user_data['email']}")
                elif register_response.status_code == 400:
                    logger.info(f"User already exists: {user_data['email']}")
                
                # Login user
                login_response = requests.post(
                    f"{self.base_url}/api/auth/login",
                    data={
                        "username": user_data["email"],
                        "password": user_data["password"]
                    }
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.user_tokens[user_data["email"]] = token_data["access_token"]
                    logger.info(f"Logged in user: {user_data['email']}")
                    
                    # Set primary user
                    if not self.auth_token:
                        self.auth_token = token_data["access_token"]
                        self.user_id = user_data["email"]
                
            except Exception as e:
                logger.error(f"Error setting up user {user_data['email']}: {e}")
        
        # Create a demo assessment
        if self.auth_token:
            try:
                assessment_data = {
                    "title": "Real-Time Demo Assessment",
                    "description": "Demo assessment for testing real-time features",
                    "business_requirements": {
                        "company_size": "medium",
                        "industry": "technology",
                        "budget_range": "100k_500k",
                        "timeline": "3_months",
                        "compliance_needs": ["GDPR"],
                        "business_goals": ["scalability", "cost_optimization"]
                    },
                    "technical_requirements": {
                        "current_infrastructure": {
                            "cloud_provider": "aws",
                            "compute_instances": 10,
                            "storage_gb": 1000
                        },
                        "workload_characteristics": {
                            "workload_types": ["web_application", "data_processing"],
                            "peak_users": 10000,
                            "data_volume_gb": 500
                        },
                        "performance_requirements": {
                            "api_response_time_ms": 200,
                            "requests_per_second": 1000,
                            "availability_percent": 99.9
                        }
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}/api/assessments",
                    json=assessment_data,
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                if response.status_code in [200, 201]:
                    assessment = response.json()
                    self.assessment_id = assessment["id"]
                    logger.info(f"Created demo assessment: {self.assessment_id}")
                else:
                    logger.error(f"Failed to create assessment: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error creating assessment: {e}")
    
    async def demo_websocket_connections(self):
        """Demo WebSocket connections and real-time communication."""
        logger.info("=== WebSocket Connections Demo ===")
        
        async def connect_user(email: str, token: str):
            """Connect a user via WebSocket."""
            try:
                uri = f"{self.ws_url}/ws/{self.assessment_id}?token={token}"
                
                async with websockets.connect(uri) as websocket:
                    logger.info(f"Connected {email} to WebSocket")
                    self.websockets[email] = websocket
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            logger.info(f"[{email}] Received: {data['type']} - {data.get('data', {}).get('message', '')}")
                            
                            # Simulate user interactions
                            if data['type'] == 'user_joined':
                                # Send a chat message
                                await websocket.send(json.dumps({
                                    "type": "chat_message",
                                    "message": f"Hello from {email}!",
                                    "user_name": email.split('@')[0].title()
                                }))
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received by {email}: {message}")
                        except Exception as e:
                            logger.error(f"Error processing message for {email}: {e}")
                            
            except Exception as e:
                logger.error(f"WebSocket connection error for {email}: {e}")
        
        # Connect multiple users concurrently
        tasks = []
        for email, token in list(self.user_tokens.items())[:3]:  # Connect first 3 users
            task = asyncio.create_task(connect_user(email, token))
            tasks.append(task)
        
        # Let connections establish and interact
        await asyncio.sleep(2)
        
        # Simulate form updates and cursor movements
        await self.simulate_collaboration()
        
        # Wait a bit more for interactions
        await asyncio.sleep(3)
        
        # Cancel tasks
        for task in tasks:
            task.cancel()
    
    async def simulate_collaboration(self):
        """Simulate live collaboration features."""
        logger.info("=== Live Collaboration Demo ===")
        
        # Simulate form field updates
        collaboration_events = [
            {
                "type": "form_update",
                "field_id": "company_size",
                "field_value": "large",
                "field_type": "select"
            },
            {
                "type": "cursor_update",
                "cursor_position": {"x": 100, "y": 200, "fieldId": "budget_range"}
            },
            {
                "type": "form_update",
                "field_id": "budget_range",
                "field_value": "500k_1m",
                "field_type": "select"
            }
        ]
        
        # Send collaboration events from different users
        user_emails = list(self.user_tokens.keys())
        for i, event in enumerate(collaboration_events):
            if i < len(user_emails) and user_emails[i] in self.websockets:
                try:
                    websocket = self.websockets[user_emails[i]]
                    await websocket.send(json.dumps(event))
                    logger.info(f"Sent collaboration event from {user_emails[i]}: {event['type']}")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error sending collaboration event: {e}")
    
    async def demo_workflow_progress(self):
        """Demo workflow progress updates."""
        logger.info("=== Workflow Progress Demo ===")
        
        if not self.assessment_id or not self.auth_token:
            logger.error("Assessment ID or auth token not available")
            return
        
        try:
            # Start assessment workflow
            response = requests.post(
                f"{self.base_url}/api/assessments/{self.assessment_id}/start",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                logger.info("Started assessment workflow")
                
                # Wait for workflow events
                await asyncio.sleep(5)
                
                # Generate recommendations
                response = requests.post(
                    f"{self.base_url}/api/recommendations/{self.assessment_id}/generate",
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                if response.status_code in [200, 202]:
                    logger.info("Started recommendation generation")
                    await asyncio.sleep(3)
                
            else:
                logger.error(f"Failed to start workflow: {response.text}")
                
        except Exception as e:
            logger.error(f"Error in workflow demo: {e}")
    
    async def demo_notifications(self):
        """Demo notification system."""
        logger.info("=== Notifications Demo ===")
        
        # Simulate various notification types
        notifications = [
            {
                "type": "success",
                "title": "Assessment Complete",
                "message": "Your infrastructure assessment has been completed successfully."
            },
            {
                "type": "warning",
                "title": "High CPU Usage",
                "message": "System CPU usage is above 80%. Consider scaling resources."
            },
            {
                "type": "info",
                "title": "New Recommendation",
                "message": "Cloud Engineer Agent has generated new service recommendations."
            },
            {
                "type": "error",
                "title": "API Rate Limit",
                "message": "AWS API rate limit exceeded. Retrying in 60 seconds."
            }
        ]
        
        # Send notifications through WebSocket
        for notification in notifications:
            try:
                # Simulate sending notification to all connected users
                for email, websocket in self.websockets.items():
                    if websocket:
                        message = {
                            "type": "notification",
                            "data": notification,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await websocket.send(json.dumps(message))
                        logger.info(f"Sent notification to {email}: {notification['title']}")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    async def demo_metrics_updates(self):
        """Demo real-time metrics updates."""
        logger.info("=== Real-Time Metrics Demo ===")
        
        # Simulate metrics data
        metrics_data = [
            {
                "system_health": {
                    "cpu_usage_percent": 45.2,
                    "memory_usage_percent": 67.8,
                    "disk_usage_percent": 23.1,
                    "network_latency_ms": 15,
                    "error_rate_percent": 0.1,
                    "active_connections": 25,
                    "response_time_ms": 245
                },
                "workflow_metrics": {
                    "active_workflows": 3,
                    "completed_workflows": 15,
                    "failed_workflows": 1,
                    "average_duration_ms": 180000,
                    "agent_performance": {
                        "cto_agent": {
                            "success_rate": 0.95,
                            "avg_response_time": 2500,
                            "total_executions": 20
                        },
                        "cloud_engineer_agent": {
                            "success_rate": 0.92,
                            "avg_response_time": 3200,
                            "total_executions": 18
                        }
                    }
                }
            },
            {
                "system_health": {
                    "cpu_usage_percent": 52.1,
                    "memory_usage_percent": 71.2,
                    "disk_usage_percent": 23.5,
                    "network_latency_ms": 18,
                    "error_rate_percent": 0.2,
                    "active_connections": 28,
                    "response_time_ms": 267
                },
                "workflow_metrics": {
                    "active_workflows": 4,
                    "completed_workflows": 16,
                    "failed_workflows": 1,
                    "average_duration_ms": 175000
                }
            }
        ]
        
        # Send metrics updates
        for metrics in metrics_data:
            try:
                # Send to all connected users
                for email, websocket in self.websockets.items():
                    if websocket:
                        message = {
                            "type": "metrics_update",
                            "data": metrics,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await websocket.send(json.dumps(message))
                        logger.info(f"Sent metrics update to {email}")
                
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error sending metrics update: {e}")
    
    async def demo_performance_alerts(self):
        """Demo performance alerts."""
        logger.info("=== Performance Alerts Demo ===")
        
        # Simulate performance alerts
        alerts = [
            {
                "alert_id": "alert_001",
                "alert_type": "high_cpu_usage",
                "severity": "medium",
                "message": "CPU usage has exceeded 80% for the last 5 minutes",
                "metric_name": "cpu_usage_percent",
                "metric_value": 85.3,
                "threshold": 80.0
            },
            {
                "alert_id": "alert_002",
                "alert_type": "slow_agent_response",
                "severity": "high",
                "message": "Cloud Engineer Agent response time exceeded 30 seconds",
                "agent_name": "cloud_engineer_agent",
                "metric_name": "agent_response_time_ms",
                "metric_value": 35000,
                "threshold": 30000
            },
            {
                "alert_id": "alert_003",
                "alert_type": "workflow_failure",
                "severity": "critical",
                "message": "Assessment workflow failed due to API timeout",
                "workflow_id": self.assessment_id
            }
        ]
        
        # Send alerts
        for alert in alerts:
            try:
                # Send to all connected users
                for email, websocket in self.websockets.items():
                    if websocket:
                        message = {
                            "type": "alert",
                            "data": alert,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await websocket.send(json.dumps(message))
                        logger.info(f"Sent alert to {email}: {alert['alert_type']} ({alert['severity']})")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
    
    def test_websocket_status_endpoint(self):
        """Test WebSocket status endpoint."""
        logger.info("=== WebSocket Status Endpoint Test ===")
        
        try:
            response = requests.get(f"{self.base_url}/api/websocket/status")
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info("WebSocket Status:")
                logger.info(f"  Status: {status_data['status']}")
                logger.info(f"  Total Connections: {status_data['connections']['total_connections']}")
                logger.info(f"  Active Assessments: {status_data['connections']['active_assessments']}")
                logger.info(f"  Connected Users: {status_data['connections']['connected_users']}")
                logger.info(f"  Features: {', '.join(status_data['features'])}")
            else:
                logger.error(f"Failed to get WebSocket status: {response.text}")
                
        except Exception as e:
            logger.error(f"Error testing WebSocket status endpoint: {e}")
    
    async def run_comprehensive_demo(self):
        """Run the comprehensive real-time features demo."""
        logger.info("🚀 Starting Real-Time Features Demo")
        logger.info("=" * 50)
        
        try:
            # Setup
            await self.setup_demo_environment()
            
            if not self.auth_token or not self.assessment_id:
                logger.error("Demo setup failed. Cannot continue.")
                return
            
            # Test WebSocket status endpoint
            self.test_websocket_status_endpoint()
            
            # Run WebSocket demos concurrently
            websocket_task = asyncio.create_task(self.demo_websocket_connections())
            
            # Wait for connections to establish
            await asyncio.sleep(2)
            
            # Run other demos
            await self.demo_notifications()
            await self.demo_metrics_updates()
            await self.demo_performance_alerts()
            await self.demo_workflow_progress()
            
            # Wait for WebSocket demo to complete
            await asyncio.sleep(5)
            websocket_task.cancel()
            
            logger.info("✅ Real-Time Features Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
        
        finally:
            # Cleanup
            for websocket in self.websockets.values():
                if websocket:
                    try:
                        await websocket.close()
                    except:
                        pass


async def main():
    """Main demo function."""
    demo = RealTimeFeaturesDemo()
    
    try:
        await demo.run_comprehensive_demo()
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("""
    🌟 Infra Mind Real-Time Features Demo
    =====================================
    
    This demo showcases:
    • WebSocket connections for real-time communication
    • Live collaboration features (form updates, cursors, chat)
    • Real-time notifications system
    • Live metrics dashboard updates
    • Performance alerts and monitoring
    
    Make sure the API server is running on localhost:8000
    
    Press Ctrl+C to stop the demo at any time.
    """)
    
    asyncio.run(main())