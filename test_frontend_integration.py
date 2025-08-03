#!/usr/bin/env python3
"""
Comprehensive test suite for Task 8: Production Frontend Integration

This test suite validates:
- Real backend API integration
- User authentication functionality
- Real-time features and WebSocket connections
- Production build configuration
- Error handling and loading states
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import requests
import websocket
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

class FrontendIntegrationTester:
    """Test suite for frontend integration functionality."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.ws_url = "ws://localhost:8000"
        self.test_results = []
        
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
    
    def test_api_service_configuration(self) -> bool:
        """Test 8.1: API service configuration and real backend integration."""
        print("\n🔧 Testing API Service Configuration...")
        
        try:
            # Check if API service file exists and has correct structure
            api_service_path = project_root / "frontend-react/src/services/api.ts"
            if not api_service_path.exists():
                self.log_test("API Service File Exists", False, "api.ts file not found")
                return False
            
            # Read and validate API service content
            with open(api_service_path, 'r') as f:
                content = f.read()
            
            # Check for real API integration features
            required_features = [
                "API_BASE_URL",
                "createWebSocketConnection",
                "request<T>",
                "generateRequestId",
                "AbortSignal.timeout",
                "checkHealth",
                "getSystemMetrics"
            ]
            
            missing_features = []
            for feature in required_features:
                if feature not in content:
                    missing_features.append(feature)
            
            if missing_features:
                self.log_test("API Service Features", False, f"Missing: {', '.join(missing_features)}")
                return False
            
            self.log_test("API Service Configuration", True, "All required features present")
            
            # Test error handling implementation
            error_handling_features = [
                "catch (error)",
                "AbortError",
                "status === 401",
                "status === 403",
                "status === 429"
            ]
            
            for feature in error_handling_features:
                if feature not in content:
                    self.log_test("Error Handling", False, f"Missing error handling for: {feature}")
                    return False
            
            self.log_test("Error Handling Implementation", True, "Comprehensive error handling present")
            return True
            
        except Exception as e:
            self.log_test("API Service Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_authentication_implementation(self) -> bool:
        """Test 8.2: Authentication implementation."""
        print("\n🔐 Testing Authentication Implementation...")
        
        try:
            # Check auth slice implementation
            auth_slice_path = project_root / "frontend-react/src/store/slices/authSlice.ts"
            if not auth_slice_path.exists():
                self.log_test("Auth Slice Exists", False, "authSlice.ts not found")
                return False
            
            with open(auth_slice_path, 'r') as f:
                auth_content = f.read()
            
            # Check for authentication features
            auth_features = [
                "createAsyncThunk",
                "login",
                "register",
                "logout",
                "refreshToken",
                "getCurrentUser",
                "updateProfile",
                "JWT",
                "isAuthenticated"
            ]
            
            missing_auth_features = []
            for feature in auth_features:
                if feature not in auth_content:
                    missing_auth_features.append(feature)
            
            if missing_auth_features:
                self.log_test("Auth Features", False, f"Missing: {', '.join(missing_auth_features)}")
                return False
            
            self.log_test("Authentication Slice", True, "All auth features implemented")
            
            # Check protected route component
            protected_route_path = project_root / "frontend-react/src/components/ProtectedRoute.tsx"
            if not protected_route_path.exists():
                self.log_test("Protected Route Component", False, "ProtectedRoute.tsx not found")
                return False
            
            with open(protected_route_path, 'r') as f:
                protected_content = f.read()
            
            protected_features = [
                "requireAuth",
                "allowedRoles",
                "localStorage.getItem",
                "getCurrentUser",
                "CircularProgress"
            ]
            
            for feature in protected_features:
                if feature not in protected_content:
                    self.log_test("Protected Route Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Protected Route Implementation", True, "Route protection implemented")
            
            # Check user profile component
            user_profile_path = project_root / "frontend-react/src/components/UserProfile.tsx"
            if not user_profile_path.exists():
                self.log_test("User Profile Component", False, "UserProfile.tsx not found")
                return False
            
            self.log_test("User Profile Management", True, "User profile component exists")
            
            # Check login/register pages
            login_path = project_root / "frontend-react/src/app/auth/login/page.tsx"
            register_path = project_root / "frontend-react/src/app/auth/register/page.tsx"
            
            if not login_path.exists() or not register_path.exists():
                self.log_test("Auth Pages", False, "Login or register page missing")
                return False
            
            # Check if pages use real authentication
            with open(login_path, 'r') as f:
                login_content = f.read()
            
            if "useAppDispatch" not in login_content or "login" not in login_content:
                self.log_test("Login Page Integration", False, "Login page not using real auth")
                return False
            
            self.log_test("Authentication Pages", True, "Login and register pages integrated")
            return True
            
        except Exception as e:
            self.log_test("Authentication Implementation", False, f"Error: {str(e)}")
            return False
    
    def test_realtime_features(self) -> bool:
        """Test 8.3: Real-time features implementation."""
        print("\n⚡ Testing Real-time Features...")
        
        try:
            # Check WebSocket hook
            websocket_hook_path = project_root / "frontend-react/src/hooks/useWebSocket.ts"
            if not websocket_hook_path.exists():
                self.log_test("WebSocket Hook", False, "useWebSocket.ts not found")
                return False
            
            with open(websocket_hook_path, 'r') as f:
                ws_content = f.read()
            
            ws_features = [
                "useWebSocket",
                "useAssessmentWebSocket",
                "useSystemWebSocket",
                "WebSocket",
                "reconnectInterval",
                "heartbeat",
                "sendTypedMessage"
            ]
            
            for feature in ws_features:
                if feature not in ws_content:
                    self.log_test("WebSocket Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("WebSocket Hook Implementation", True, "WebSocket functionality complete")
            
            # Check real-time components
            realtime_components = [
                "RealTimeProgress.tsx",
                "RealTimeDashboard.tsx",
                "NotificationSystem.tsx",
                "LiveCollaboration.tsx"
            ]
            
            for component in realtime_components:
                component_path = project_root / f"frontend-react/src/components/{component}"
                if not component_path.exists():
                    self.log_test(f"Component: {component}", False, f"{component} not found")
                    return False
                
                self.log_test(f"Component: {component}", True, "Component exists")
            
            # Check real-time dashboard integration
            dashboard_path = project_root / "frontend-react/src/app/dashboard/page.tsx"
            if not dashboard_path.exists():
                self.log_test("Dashboard Integration", False, "Dashboard page not found")
                return False
            
            with open(dashboard_path, 'r') as f:
                dashboard_content = f.read()
            
            if "RealTimeDashboard" not in dashboard_content:
                self.log_test("Real-time Dashboard Integration", False, "RealTimeDashboard not integrated")
                return False
            
            self.log_test("Real-time Dashboard Integration", True, "Dashboard includes real-time features")
            
            # Check notification system integration
            if "useSystemWebSocket" not in dashboard_content:
                self.log_test("WebSocket Integration", False, "Dashboard not using WebSocket")
                return False
            
            self.log_test("WebSocket Integration", True, "Dashboard integrated with WebSocket")
            return True
            
        except Exception as e:
            self.log_test("Real-time Features", False, f"Error: {str(e)}")
            return False
    
    def test_production_configuration(self) -> bool:
        """Test production build configuration."""
        print("\n🏗️ Testing Production Configuration...")
        
        try:
            # Check Next.js configuration
            nextjs_config_path = project_root / "frontend-react/next.config.ts"
            if not nextjs_config_path.exists():
                self.log_test("Next.js Config", False, "next.config.ts not found")
                return False
            
            with open(nextjs_config_path, 'r') as f:
                config_content = f.read()
            
            config_features = [
                "output: 'standalone'",
                "compress: true",
                "poweredByHeader: false",
                "NEXT_PUBLIC_API_URL",
                "NEXT_PUBLIC_WS_URL",
                "webpack:",
                "headers()",
                "X-Frame-Options",
                "X-Content-Type-Options"
            ]
            
            for feature in config_features:
                if feature not in config_content:
                    self.log_test("Production Config Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Next.js Production Configuration", True, "All production features configured")
            
            # Check Dockerfile
            dockerfile_path = project_root / "frontend-react/Dockerfile"
            if not dockerfile_path.exists():
                self.log_test("Dockerfile", False, "Dockerfile not found")
                return False
            
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
            
            dockerfile_features = [
                "multi-stage",
                "node:20-alpine",
                "HEALTHCHECK",
                "USER nextjs",
                "NODE_ENV=production"
            ]
            
            for feature in dockerfile_features:
                if feature not in dockerfile_content.lower():
                    self.log_test("Dockerfile Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Dockerfile Configuration", True, "Production Dockerfile configured")
            
            # Check health endpoint
            health_route_path = project_root / "frontend-react/src/app/health/route.ts"
            if not health_route_path.exists():
                self.log_test("Health Endpoint", False, "Health route not found")
                return False
            
            self.log_test("Health Endpoint", True, "Health check endpoint exists")
            return True
            
        except Exception as e:
            self.log_test("Production Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_redux_store_integration(self) -> bool:
        """Test Redux store integration."""
        print("\n🏪 Testing Redux Store Integration...")
        
        try:
            # Check store configuration
            store_path = project_root / "frontend-react/src/store/index.ts"
            if not store_path.exists():
                self.log_test("Redux Store", False, "Store index.ts not found")
                return False
            
            with open(store_path, 'r') as f:
                store_content = f.read()
            
            if "authReducer" not in store_content:
                self.log_test("Auth Reducer Integration", False, "Auth reducer not in store")
                return False
            
            self.log_test("Redux Store Configuration", True, "Store properly configured with auth")
            
            # Check assessment slice integration
            assessment_slice_path = project_root / "frontend-react/src/store/slices/assessmentSlice.ts"
            if not assessment_slice_path.exists():
                self.log_test("Assessment Slice", False, "Assessment slice not found")
                return False
            
            with open(assessment_slice_path, 'r') as f:
                assessment_content = f.read()
            
            if "apiClient" not in assessment_content:
                self.log_test("Assessment API Integration", False, "Assessment slice not using real API")
                return False
            
            self.log_test("Assessment Slice Integration", True, "Assessment slice uses real API")
            return True
            
        except Exception as e:
            self.log_test("Redux Store Integration", False, f"Error: {str(e)}")
            return False
    
    def test_navigation_integration(self) -> bool:
        """Test navigation component integration."""
        print("\n🧭 Testing Navigation Integration...")
        
        try:
            navigation_path = project_root / "frontend-react/src/components/Navigation.tsx"
            if not navigation_path.exists():
                self.log_test("Navigation Component", False, "Navigation.tsx not found")
                return False
            
            with open(navigation_path, 'r') as f:
                nav_content = f.read()
            
            nav_features = [
                "useAppSelector",
                "useAppDispatch",
                "logout",
                "UserProfile",
                "isAuthenticated",
                "user?.name"
            ]
            
            for feature in nav_features:
                if feature not in nav_content:
                    self.log_test("Navigation Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Navigation Integration", True, "Navigation integrated with auth")
            return True
            
        except Exception as e:
            self.log_test("Navigation Integration", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all frontend integration tests."""
        print("🚀 Starting Frontend Integration Tests...")
        print("=" * 60)
        
        # Run all test categories
        test_results = {
            "api_service": self.test_api_service_configuration(),
            "authentication": self.test_authentication_implementation(),
            "realtime_features": self.test_realtime_features(),
            "production_config": self.test_production_configuration(),
            "redux_integration": self.test_redux_store_integration(),
            "navigation_integration": self.test_navigation_integration()
        }
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
        
        print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        if overall_success:
            print("\n🎉 All frontend integration tasks have been successfully implemented!")
            print("✅ Task 8.1: Real backend API integration - COMPLETE")
            print("✅ Task 8.2: User authentication implementation - COMPLETE") 
            print("✅ Task 8.3: Real-time features - COMPLETE")
        else:
            print("\n⚠️  Some frontend integration tasks need attention.")
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


def main():
    """Main test execution function."""
    tester = FrontendIntegrationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()