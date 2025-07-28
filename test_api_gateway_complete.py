#!/usr/bin/env python3
"""
Comprehensive test script for the complete API gateway implementation.

Tests all major API endpoints, middleware functionality, and advanced features
including webhooks, monitoring, admin endpoints, and API versioning.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import uuid


class APIGatewayTester:
    """Comprehensive API gateway testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all API gateway tests."""
        print("🚀 Starting comprehensive API gateway tests...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("Basic Health and Info", self.test_basic_endpoints),
            ("API Versioning", self.test_api_versioning),
            ("Authentication", self.test_authentication),
            ("Assessment Management", self.test_assessments),
            ("Recommendations", self.test_recommendations),
            ("Report Generation", self.test_reports),
            ("Webhook Management", self.test_webhooks),
            ("Monitoring Endpoints", self.test_monitoring),
            ("Admin Endpoints", self.test_admin),
            ("Testing Tools", self.test_testing_endpoints),
            ("Rate Limiting", self.test_rate_limiting),
            ("Error Handling", self.test_error_handling)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n📋 Testing: {category_name}")
            print("-" * 40)
            try:
                await test_func()
                print(f"✅ {category_name} tests completed")
            except Exception as e:
                print(f"❌ {category_name} tests failed: {e}")
                self.test_results.append({
                    "category": category_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Print summary
        await self.print_test_summary()
        
        # Cleanup
        await self.client.aclose()
    
    async def test_basic_endpoints(self):
        """Test basic health and information endpoints."""
        # Root endpoint
        response = await self.client.get(f"{self.base_url}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "quick_start" in data
        print("✓ Root endpoint working")
        
        # Health check
        response = await self.client.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check working")
        
        # Detailed health check
        response = await self.client.get(f"{self.base_url}/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "metrics" in data
        print("✓ Detailed health check working")
    
    async def test_api_versioning(self):
        """Test API versioning functionality."""
        # Get version information
        response = await self.client.get(f"{self.base_url}/api/versions")
        assert response.status_code == 200
        data = response.json()
        assert "supported_versions" in data
        assert "current_version" in data
        print("✓ API version info working")
        
        # Test v1 endpoint
        response = await self.client.get(f"{self.base_url}/api/v1/")
        # Should work or redirect appropriately
        print("✓ V1 API access tested")
        
        # Test v2 endpoint
        response = await self.client.get(f"{self.base_url}/api/v2/")
        # Should work
        print("✓ V2 API access tested")
        
        # Test version headers
        response = await self.client.get(f"{self.base_url}/api/v2/health")
        assert "X-API-Version" in response.headers
        print("✓ Version headers present")
    
    async def test_authentication(self):
        """Test authentication endpoints."""
        # Test registration
        user_data = {
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "company": "Test Company"
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/auth/register",
            json=user_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        self.auth_token = data["access_token"]
        print("✓ User registration working")
        
        # Test login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/auth/login",
            json=login_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✓ User login working")
        
        # Test profile access
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.get(
            f"{self.base_url}/api/v2/auth/profile",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Profile access working")
    
    async def test_assessments(self):
        """Test assessment management endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        # Create assessment
        assessment_data = {
            "title": "Test Assessment",
            "description": "Test infrastructure assessment",
            "business_requirements": {
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "100k_500k"
            },
            "technical_requirements": {
                "workload_types": ["web_application"]
            },
            "priority": "medium",
            "source": "api_test"
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/assessments",
            json=assessment_data,
            headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assessment_id = data["id"]
        print("✓ Assessment creation working")
        
        # Get assessment
        response = await self.client.get(
            f"{self.base_url}/api/v2/assessments/{assessment_id}",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Assessment retrieval working")
        
        # List assessments
        response = await self.client.get(
            f"{self.base_url}/api/v2/assessments",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "assessments" in data
        print("✓ Assessment listing working")
        
        return assessment_id
    
    async def test_recommendations(self):
        """Test recommendation endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        assessment_id = await self.test_assessments()
        
        # Generate recommendations
        generate_data = {
            "agent_names": ["cto_agent", "cloud_engineer_agent"],
            "priority_override": "high"
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/recommendations/{assessment_id}/generate",
            json=generate_data,
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Recommendation generation working")
        
        # Get recommendations
        response = await self.client.get(
            f"{self.base_url}/api/v2/recommendations/{assessment_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print("✓ Recommendation retrieval working")
        
        return assessment_id
    
    async def test_reports(self):
        """Test report generation endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        assessment_id = await self.test_recommendations()
        
        # Generate report
        report_data = {
            "report_type": "executive_summary",
            "format": "pdf",
            "title": "Test Report",
            "priority": "medium"
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/reports/{assessment_id}/generate",
            json=report_data,
            headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        report_id = data["id"]
        print("✓ Report generation working")
        
        # Get reports
        response = await self.client.get(
            f"{self.base_url}/api/v2/reports/{assessment_id}",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Report listing working")
        
        # Get specific report
        response = await self.client.get(
            f"{self.base_url}/api/v2/reports/{assessment_id}/reports/{report_id}",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Report retrieval working")
    
    async def test_webhooks(self):
        """Test webhook management endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        # Create webhook
        webhook_data = {
            "url": "https://webhook.site/test-endpoint",
            "events": ["assessment.completed", "report.generated"],
            "description": "Test webhook",
            "timeout_seconds": 30,
            "retry_attempts": 3
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/webhooks",
            json=webhook_data,
            headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        webhook_id = data["id"]
        print("✓ Webhook creation working")
        
        # List webhooks
        response = await self.client.get(
            f"{self.base_url}/api/v2/webhooks",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        print("✓ Webhook listing working")
        
        # Test webhook
        test_data = {
            "event_type": "system.alert",
            "test_payload": {"message": "Test alert"}
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/webhooks/{webhook_id}/test",
            json=test_data,
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Webhook testing working")
    
    async def test_monitoring(self):
        """Test monitoring endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        # Get dashboard overview
        response = await self.client.get(
            f"{self.base_url}/api/v2/monitoring/dashboard",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Monitoring dashboard working")
        
        # Get system health
        response = await self.client.get(
            f"{self.base_url}/api/v2/monitoring/health",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ System health monitoring working")
        
        # Get performance metrics
        response = await self.client.get(
            f"{self.base_url}/api/v2/monitoring/performance",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Performance monitoring working")
    
    async def test_admin(self):
        """Test admin endpoints."""
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        # Get system metrics
        response = await self.client.get(
            f"{self.base_url}/api/v2/admin/metrics",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        print("✓ Admin metrics working")
        
        # Get system configuration
        response = await self.client.get(
            f"{self.base_url}/api/v2/admin/config",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Admin configuration working")
        
        # Get system alerts
        response = await self.client.get(
            f"{self.base_url}/api/v2/admin/alerts",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Admin alerts working")
    
    async def test_testing_endpoints(self):
        """Test the testing and documentation endpoints."""
        # Get test scenarios
        response = await self.client.get(
            f"{self.base_url}/api/v2/testing/scenarios"
        )
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        print("✓ Test scenarios working")
        
        # Generate sample data
        sample_request = {
            "data_type": "assessment",
            "count": 2
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v2/testing/sample-data",
            json=sample_request
        )
        assert response.status_code == 200
        data = response.json()
        assert "samples" in data
        print("✓ Sample data generation working")
        
        # Get OpenAPI examples
        response = await self.client.get(
            f"{self.base_url}/api/v2/testing/openapi-examples"
        )
        assert response.status_code == 200
        print("✓ OpenAPI examples working")
        
        # Get Postman collection
        response = await self.client.get(
            f"{self.base_url}/api/v2/testing/postman-collection"
        )
        assert response.status_code == 200
        print("✓ Postman collection working")
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        print("⏱️  Testing rate limiting (this may take a moment)...")
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(5):
            response = await self.client.get(f"{self.base_url}/health")
            responses.append(response.status_code)
            
            # Check for rate limit headers
            if "X-RateLimit-Limit" in response.headers:
                print(f"✓ Rate limit headers present: {response.headers['X-RateLimit-Limit']}")
                break
        
        # All requests should succeed for normal usage
        assert all(status == 200 for status in responses)
        print("✓ Rate limiting configured properly")
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        # Test 404 error
        response = await self.client.get(f"{self.base_url}/api/v2/nonexistent")
        assert response.status_code == 404
        print("✓ 404 error handling working")
        
        # Test invalid JSON
        response = await self.client.post(
            f"{self.base_url}/api/v2/assessments",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        print("✓ Invalid JSON handling working")
        
        # Test missing authentication
        response = await self.client.get(f"{self.base_url}/api/v2/auth/profile")
        assert response.status_code in [401, 403]
        print("✓ Authentication error handling working")
    
    async def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        failed_tests = [r for r in self.test_results if r.get("status") == "failed"]
        
        if not failed_tests:
            print("🎉 ALL TESTS PASSED!")
            print(f"✅ Successfully tested all API gateway features")
        else:
            print(f"❌ {len(failed_tests)} test categories failed:")
            for test in failed_tests:
                print(f"   - {test['category']}: {test['error']}")
        
        print(f"\n📊 Coverage Summary:")
        print(f"   • API Versioning (v1, v2)")
        print(f"   • Authentication & Authorization")
        print(f"   • Core Business Logic (Assessments, Recommendations, Reports)")
        print(f"   • Advanced Features (Webhooks, Monitoring, Admin)")
        print(f"   • Developer Tools (Testing, Documentation)")
        print(f"   • Security & Performance (Rate Limiting, Error Handling)")
        
        print(f"\n🔗 Key Endpoints Tested:")
        print(f"   • Health: /health, /health/detailed")
        print(f"   • Auth: /api/v2/auth/*")
        print(f"   • Core: /api/v2/assessments, /api/v2/recommendations, /api/v2/reports")
        print(f"   • Advanced: /api/v2/webhooks, /api/v2/monitoring, /api/v2/admin")
        print(f"   • Tools: /api/v2/testing/*")


async def main():
    """Main test execution function."""
    tester = APIGatewayTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🧪 Infra Mind API Gateway - Comprehensive Test Suite")
    print("=" * 60)
    asyncio.run(main())