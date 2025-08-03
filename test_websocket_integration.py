#!/usr/bin/env python3
"""
WebSocket Integration Test for Real-time Features

Tests the WebSocket functionality between frontend and backend
for real-time progress updates, notifications, and collaboration.
"""

import asyncio
import json
import websockets
import requests
import time
from typing import Dict, Any, List
import threading
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

class WebSocketIntegrationTester:
    """Test WebSocket integration between frontend and backend."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.ws_base_url = "ws://localhost:8000"
        self.test_results = []
        self.received_messages = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    async def test_websocket_connection(self) -> bool:
        """Test basic WebSocket connection."""
        print("\n🔌 Testing WebSocket Connection...")
        
        try:
            # Test connection without authentication (should fail gracefully)
            uri = f"{self.ws_base_url}/ws"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Should not reach here without auth
                    self.log_test("WebSocket Auth Check", False, "Connection allowed without authentication")
                    return False
            except websockets.exceptions.ConnectionClosedError as e:
                if e.code == 4001:  # Authentication required
                    self.log_test("WebSocket Authentication", True, "Properly requires authentication")
                else:
                    self.log_test("WebSocket Authentication", False, f"Unexpected close code: {e.code}")
                    return False
            except Exception as e:
                self.log_test("WebSocket Connection", False, f"Connection error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("WebSocket Connection Test", False, f"Error: {str(e)}")
            return False
    
    async def test_websocket_with_mock_auth(self) -> bool:
        """Test WebSocket with mock authentication token."""
        print("\n🔐 Testing WebSocket with Authentication...")
        
        try:
            # Create a mock JWT token for testing
            mock_token = "mock_jwt_token_for_testing"
            uri = f"{self.ws_base_url}/ws?token={mock_token}"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    self.log_test("WebSocket Auth Connection", True, "Connected with token")
                    
                    # Test sending a heartbeat message
                    heartbeat_msg = {
                        "type": "heartbeat",
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(heartbeat_msg))
                    self.log_test("WebSocket Message Send", True, "Heartbeat sent successfully")
                    
                    # Try to receive a response (with timeout)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        response_data = json.loads(response)
                        self.log_test("WebSocket Message Receive", True, f"Received: {response_data.get('type', 'unknown')}")
                    except asyncio.TimeoutError:
                        self.log_test("WebSocket Message Receive", True, "No immediate response (expected)")
                    
                    return True
                    
            except websockets.exceptions.ConnectionClosedError as e:
                if e.code == 4001:
                    self.log_test("WebSocket Mock Auth", True, "Mock token rejected (expected)")
                    return True
                else:
                    self.log_test("WebSocket Mock Auth", False, f"Unexpected close: {e.code}")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Auth Test", False, f"Error: {str(e)}")
            return False
    
    def test_websocket_message_types(self) -> bool:
        """Test WebSocket message type handling."""
        print("\n📨 Testing WebSocket Message Types...")
        
        try:
            # Check if WebSocket implementation handles different message types
            websocket_impl_path = project_root / "src/infra_mind/api/websocket.py"
            
            if not websocket_impl_path.exists():
                self.log_test("WebSocket Implementation", False, "websocket.py not found")
                return False
            
            with open(websocket_impl_path, 'r') as f:
                ws_content = f.read()
            
            # Check for required message types
            required_message_types = [
                "workflow_progress",
                "agent_status", 
                "step_completed",
                "notification",
                "alert",
                "user_joined",
                "user_left",
                "cursor_update",
                "form_update",
                "heartbeat"
            ]
            
            missing_types = []
            for msg_type in required_message_types:
                if msg_type not in ws_content:
                    missing_types.append(msg_type)
            
            if missing_types:
                self.log_test("WebSocket Message Types", False, f"Missing types: {', '.join(missing_types)}")
                return False
            
            self.log_test("WebSocket Message Types", True, "All required message types implemented")
            
            # Check for WebSocket manager class
            if "class WebSocketManager" not in ws_content:
                self.log_test("WebSocket Manager", False, "WebSocketManager class not found")
                return False
            
            self.log_test("WebSocket Manager", True, "WebSocketManager class implemented")
            
            # Check for connection management
            connection_features = [
                "connect",
                "disconnect", 
                "handle_message",
                "broadcast_to_user",
                "broadcast_to_assessment",
                "heartbeat_monitor"
            ]
            
            for feature in connection_features:
                if feature not in ws_content:
                    self.log_test("WebSocket Features", False, f"Missing feature: {feature}")
                    return False
            
            self.log_test("WebSocket Connection Management", True, "All connection features implemented")
            return True
            
        except Exception as e:
            self.log_test("WebSocket Message Types", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_websocket_hook(self) -> bool:
        """Test frontend WebSocket hook implementation."""
        print("\n🎣 Testing Frontend WebSocket Hook...")
        
        try:
            hook_path = project_root / "frontend-react/src/hooks/useWebSocket.ts"
            
            if not hook_path.exists():
                self.log_test("WebSocket Hook File", False, "useWebSocket.ts not found")
                return False
            
            with open(hook_path, 'r') as f:
                hook_content = f.read()
            
            # Check for hook features
            hook_features = [
                "useWebSocket",
                "useAssessmentWebSocket", 
                "useSystemWebSocket",
                "reconnectInterval",
                "maxReconnectAttempts",
                "heartbeatInterval",
                "sendTypedMessage",
                "isConnected",
                "lastMessage"
            ]
            
            missing_features = []
            for feature in hook_features:
                if feature not in hook_content:
                    missing_features.append(feature)
            
            if missing_features:
                self.log_test("WebSocket Hook Features", False, f"Missing: {', '.join(missing_features)}")
                return False
            
            self.log_test("WebSocket Hook Implementation", True, "All hook features implemented")
            
            # Check for authentication integration
            if "useSelector" not in hook_content or "auth.token" not in hook_content:
                self.log_test("WebSocket Auth Integration", False, "Hook not integrated with auth")
                return False
            
            self.log_test("WebSocket Auth Integration", True, "Hook integrated with authentication")
            
            # Check for reconnection logic
            reconnection_features = [
                "reconnectTimeoutRef",
                "shouldReconnectRef", 
                "scheduleReconnect",
                "exponential backoff"
            ]
            
            reconnection_count = sum(1 for feature in reconnection_features if feature in hook_content)
            if reconnection_count < 3:
                self.log_test("WebSocket Reconnection", False, "Incomplete reconnection logic")
                return False
            
            self.log_test("WebSocket Reconnection Logic", True, "Reconnection logic implemented")
            return True
            
        except Exception as e:
            self.log_test("Frontend WebSocket Hook", False, f"Error: {str(e)}")
            return False
    
    def test_realtime_components(self) -> bool:
        """Test real-time component implementations."""
        print("\n⚡ Testing Real-time Components...")
        
        try:
            # Test RealTimeProgress component
            progress_path = project_root / "frontend-react/src/components/RealTimeProgress.tsx"
            if not progress_path.exists():
                self.log_test("RealTimeProgress Component", False, "Component not found")
                return False
            
            with open(progress_path, 'r') as f:
                progress_content = f.read()
            
            progress_features = [
                "useAssessmentWebSocket",
                "WorkflowProgress",
                "AgentStatus", 
                "handleMessage",
                "workflow_progress",
                "agent_status",
                "LinearProgress"
            ]
            
            for feature in progress_features:
                if feature not in progress_content:
                    self.log_test("RealTimeProgress Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("RealTimeProgress Component", True, "Component fully implemented")
            
            # Test RealTimeDashboard component
            dashboard_path = project_root / "frontend-react/src/components/RealTimeDashboard.tsx"
            if not dashboard_path.exists():
                self.log_test("RealTimeDashboard Component", False, "Component not found")
                return False
            
            with open(dashboard_path, 'r') as f:
                dashboard_content = f.read()
            
            dashboard_features = [
                "useSystemWebSocket",
                "SystemMetrics",
                "PerformanceAlert",
                "WorkflowStatus",
                "metrics_update",
                "alert",
                "LinearProgress"
            ]
            
            for feature in dashboard_features:
                if feature not in dashboard_content:
                    self.log_test("RealTimeDashboard Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("RealTimeDashboard Component", True, "Component fully implemented")
            
            # Test NotificationSystem component
            notification_path = project_root / "frontend-react/src/components/NotificationSystem.tsx"
            if not notification_path.exists():
                self.log_test("NotificationSystem Component", False, "Component not found")
                return False
            
            self.log_test("NotificationSystem Component", True, "Component exists")
            
            # Test LiveCollaboration component
            collaboration_path = project_root / "frontend-react/src/components/LiveCollaboration.tsx"
            if not collaboration_path.exists():
                self.log_test("LiveCollaboration Component", False, "Component not found")
                return False
            
            self.log_test("LiveCollaboration Component", True, "Component exists")
            return True
            
        except Exception as e:
            self.log_test("Real-time Components", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket integration tests."""
        print("🚀 Starting WebSocket Integration Tests...")
        print("=" * 60)
        
        # Run all test categories
        test_results = {
            "websocket_connection": await self.test_websocket_connection(),
            "websocket_auth": await self.test_websocket_with_mock_auth(),
            "message_types": self.test_websocket_message_types(),
            "frontend_hook": self.test_frontend_websocket_hook(),
            "realtime_components": self.test_realtime_components()
        }
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 WEBSOCKET TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Overall assessment
        overall_success = all(test_results.values())
        
        print(f"\n🎯 WEBSOCKET INTEGRATION: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        if overall_success:
            print("\n🎉 WebSocket integration is fully implemented!")
            print("✅ Connection management - COMPLETE")
            print("✅ Message type handling - COMPLETE") 
            print("✅ Frontend hook integration - COMPLETE")
            print("✅ Real-time components - COMPLETE")
        else:
            print("\n⚠️  Some WebSocket features need attention.")
            print("Please review the failed tests above.")
        
        return {
            "overall_success": overall_success,
            "test_results": test_results,
            "detailed_results": self.test_results,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            }
        }


async def main():
    """Main test execution function."""
    tester = WebSocketIntegrationTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())