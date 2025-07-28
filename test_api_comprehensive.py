#!/usr/bin/env python3
"""
Comprehensive API Gateway Test Script for Infra Mind.

Tests all essential REST API endpoints for frontend integration.
This script validates the basic API gateway implementation.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
import httpx
from loguru import logger

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.test_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_health_endpoints(self):
        """Test health and root endpoints."""
        logger.info("🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, f"Version: {data.get('version')}")
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {e}")
        
        # Test health endpoint
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Endpoint", True, f"Status: {data.get('status')}")
            else:
                self.log_test("Health Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {e}")
    
    async def test_openapi_docs(self):
        """Test OpenAPI documentation endpoints."""
        logger.info("📚 Testing OpenAPI Documentation...")
        
        # Test OpenAPI JSON
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                data = response.json()
                self.log_test("OpenAPI JSON", True, f"Title: {data.get('info', {}).get('title')}")
            else:
                self.log_test("OpenAPI JSON", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("OpenAPI JSON", False, f"Error: {e}")
        
        # Test Swagger UI
        try:
            response = await self.client.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_test("Swagger UI", True, "Documentation accessible")
            else:
                self.log_test("Swagger UI", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Swagger UI", False, f"Error: {e}")
    
    async def test_auth_endpoints(self):
        """Test authentication endpoints."""
        logger.info("🔐 Testing Authentication Endpoints...")
        
        # Test user registration
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "company": "Test Company"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/auth/register",
                json=register_data
            )
            if response.status_code == 201:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log_test("User Registration", True, f"Token received: {bool(self.auth_token)}")
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {e}")
        
        # Test user login
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/auth/login",
                json=login_data
            )
            if response.status_code == 200:
                data = response.json()
                if not self.auth_token:  # Use login token if registration failed
                    self.auth_token = data.get("access_token")
                self.log_test("User Login", True, f"Email: {data.get('email')}")
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Login", False, f"Error: {e}")
        
        # Test token verification
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            try:
                response = await self.client.get(
                    f"{self.base_url}{API_PREFIX}/auth/verify-token",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Token Verification", True, f"Valid: {data.get('valid')}")
                else:
                    self.log_test("Token Verification", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Token Verification", False, f"Error: {e}")
        
        # Test user profile
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            try:
                response = await self.client.get(
                    f"{self.base_url}{API_PREFIX}/auth/profile",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("User Profile", True, f"Name: {data.get('full_name')}")
                else:
                    self.log_test("User Profile", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("User Profile", False, f"Error: {e}")
    
    async def test_assessment_endpoints(self):
        """Test assessment management endpoints."""
        logger.info("📋 Testing Assessment Endpoints...")
        
        # Sample assessment data
        assessment_data = {
            "title": "Test Infrastructure Assessment",
            "description": "Test assessment for API validation",
            "business_requirements": {
                "company_size": "medium",
                "industry": "technology",
                "business_goals": [
                    {
                        "goal": "Reduce costs by 30%",
                        "priority": "high",
                        "timeline_months": 6,
                        "success_metrics": ["Cost reduction", "Performance maintained"]
                    }
                ],
                "growth_projection": {
                    "current_users": 1000,
                    "projected_users_6m": 2000,
                    "projected_users_12m": 5000,
                    "current_revenue": "500000",
                    "projected_revenue_12m": "1000000"
                },
                "budget_constraints": {
                    "total_budget_range": "100k_500k",
                    "monthly_budget_limit": "25000",
                    "compute_percentage": 40,
                    "storage_percentage": 20,
                    "networking_percentage": 20,
                    "security_percentage": 20,
                    "cost_optimization_priority": "high"
                },
                "team_structure": {
                    "total_developers": 8,
                    "senior_developers": 3,
                    "devops_engineers": 2,
                    "data_engineers": 1,
                    "cloud_expertise_level": 3,
                    "kubernetes_expertise": 2,
                    "database_expertise": 4,
                    "preferred_technologies": ["Python", "React", "PostgreSQL"]
                },
                "compliance_requirements": ["gdpr"],
                "project_timeline_months": 6,
                "urgency_level": "high",
                "current_pain_points": ["High costs", "Manual scaling"],
                "success_criteria": ["30% cost reduction", "Automated scaling"],
                "multi_cloud_acceptable": True
            },
            "technical_requirements": {
                "workload_types": ["web_application", "data_processing"],
                "performance_requirements": {
                    "api_response_time_ms": 200,
                    "requests_per_second": 1000,
                    "concurrent_users": 500,
                    "uptime_percentage": "99.9",
                    "real_time_processing_required": False
                },
                "scalability_requirements": {
                    "current_data_size_gb": 100,
                    "current_daily_transactions": 10000,
                    "expected_data_growth_rate": "20% monthly",
                    "peak_load_multiplier": "5.0",
                    "auto_scaling_required": True,
                    "global_distribution_required": False,
                    "cdn_required": True,
                    "planned_regions": ["us-east-1", "eu-west-1"]
                },
                "security_requirements": {
                    "encryption_at_rest_required": True,
                    "encryption_in_transit_required": True,
                    "multi_factor_auth_required": True,
                    "vpc_isolation_required": True,
                    "security_monitoring_required": True,
                    "audit_logging_required": True
                },
                "integration_requirements": {
                    "existing_databases": ["PostgreSQL"],
                    "existing_apis": ["Payment API", "Analytics API"],
                    "rest_api_required": True,
                    "real_time_sync_required": False,
                    "batch_sync_acceptable": True
                },
                "preferred_programming_languages": ["Python", "JavaScript"],
                "monitoring_requirements": ["Application metrics", "Infrastructure monitoring"],
                "backup_requirements": ["Daily backups", "Cross-region replication"],
                "ci_cd_requirements": ["Automated testing", "Blue-green deployment"]
            },
            "priority": "medium",
            "tags": ["test", "api_validation"],
            "source": "api_test"
        }
        
        assessment_id = None
        
        # Test create assessment
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/assessments/",
                json=assessment_data
            )
            if response.status_code == 201:
                data = response.json()
                assessment_id = data.get("id")
                self.log_test("Create Assessment", True, f"ID: {assessment_id}")
            else:
                self.log_test("Create Assessment", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Assessment", False, f"Error: {e}")
        
        # Test list assessments
        try:
            response = await self.client.get(f"{self.base_url}{API_PREFIX}/assessments/")
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("assessments", []))
                self.log_test("List Assessments", True, f"Count: {count}")
            else:
                self.log_test("List Assessments", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List Assessments", False, f"Error: {e}")
        
        # Test get specific assessment
        if assessment_id:
            try:
                response = await self.client.get(
                    f"{self.base_url}{API_PREFIX}/assessments/{assessment_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Get Assessment", True, f"Title: {data.get('title')}")
                else:
                    self.log_test("Get Assessment", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Get Assessment", False, f"Error: {e}")
        
        # Test start assessment analysis
        if assessment_id:
            start_data = {
                "assessment_id": assessment_id,
                "agent_config": {"priority": "high"}
            }
            try:
                response = await self.client.post(
                    f"{self.base_url}{API_PREFIX}/assessments/{assessment_id}/start",
                    json=start_data
                )
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Start Assessment", True, f"Status: {data.get('status')}")
                else:
                    self.log_test("Start Assessment", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Start Assessment", False, f"Error: {e}")
        
        return assessment_id
    
    async def test_recommendation_endpoints(self, assessment_id: str = None):
        """Test recommendation endpoints."""
        logger.info("🎯 Testing Recommendation Endpoints...")
        
        # Use a mock assessment ID if none provided
        test_assessment_id = assessment_id or "test-assessment-123"
        
        # Test get recommendations
        try:
            response = await self.client.get(
                f"{self.base_url}{API_PREFIX}/recommendations/{test_assessment_id}"
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("recommendations", []))
                self.log_test("Get Recommendations", True, f"Count: {count}")
            else:
                self.log_test("Get Recommendations", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Recommendations", False, f"Error: {e}")
        
        # Test generate recommendations
        generate_data = {
            "agent_names": ["cto_agent", "cloud_engineer_agent"],
            "priority_override": "high"
        }
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/recommendations/{test_assessment_id}/generate",
                json=generate_data
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Generate Recommendations", True, f"Status: {data.get('status')}")
            else:
                self.log_test("Generate Recommendations", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Generate Recommendations", False, f"Error: {e}")
        
        # Test get agent-specific recommendation
        try:
            response = await self.client.get(
                f"{self.base_url}{API_PREFIX}/recommendations/{test_assessment_id}/agents/cto_agent"
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Agent Recommendation", True, f"Agent: {data.get('agent_name')}")
            else:
                self.log_test("Get Agent Recommendation", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Agent Recommendation", False, f"Error: {e}")
        
        # Test validate recommendations
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/recommendations/{test_assessment_id}/validate"
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Validate Recommendations", True, f"Score: {data.get('overall_score')}")
            else:
                self.log_test("Validate Recommendations", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Validate Recommendations", False, f"Error: {e}")
    
    async def test_report_endpoints(self, assessment_id: str = None):
        """Test report generation endpoints."""
        logger.info("📄 Testing Report Endpoints...")
        
        # Use a mock assessment ID if none provided
        test_assessment_id = assessment_id or "test-assessment-123"
        
        # Test get reports
        try:
            response = await self.client.get(
                f"{self.base_url}{API_PREFIX}/reports/{test_assessment_id}"
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("reports", []))
                self.log_test("Get Reports", True, f"Count: {count}")
            else:
                self.log_test("Get Reports", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Reports", False, f"Error: {e}")
        
        # Test generate report
        report_data = {
            "report_type": "executive_summary",
            "format": "pdf",
            "title": "Test Executive Summary",
            "priority": "medium"
        }
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/reports/{test_assessment_id}/generate",
                json=report_data
            )
            if response.status_code == 201:
                data = response.json()
                report_id = data.get("id")
                self.log_test("Generate Report", True, f"ID: {report_id}")
                
                # Test get specific report
                if report_id:
                    try:
                        response = await self.client.get(
                            f"{self.base_url}{API_PREFIX}/reports/{test_assessment_id}/reports/{report_id}"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            self.log_test("Get Specific Report", True, f"Status: {data.get('status')}")
                        else:
                            self.log_test("Get Specific Report", False, f"Status: {response.status_code}")
                    except Exception as e:
                        self.log_test("Get Specific Report", False, f"Error: {e}")
            else:
                self.log_test("Generate Report", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Generate Report", False, f"Error: {e}")
        
        # Test report preview
        try:
            response = await self.client.get(
                f"{self.base_url}{API_PREFIX}/reports/{test_assessment_id}/preview",
                params={"report_type": "executive_summary"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Report Preview", True, f"Pages: {data.get('estimated_pages')}")
            else:
                self.log_test("Report Preview", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Report Preview", False, f"Error: {e}")
    
    async def run_all_tests(self):
        """Run all API tests."""
        logger.info("🚀 Starting Comprehensive API Gateway Tests")
        logger.info("=" * 60)
        
        # Test basic endpoints
        await self.test_health_endpoints()
        await self.test_openapi_docs()
        
        # Test authentication
        await self.test_auth_endpoints()
        
        # Test core functionality
        assessment_id = await self.test_assessment_endpoints()
        await self.test_recommendation_endpoints(assessment_id)
        await self.test_report_endpoints(assessment_id)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 Test Summary")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test']}: {result['details']}")
        
        return passed_tests, failed_tests


async def main():
    """Main test function."""
    logger.info("🧪 Infra Mind API Gateway Comprehensive Test Suite")
    
    async with APITester() as tester:
        try:
            passed, failed = await tester.run_all_tests()
            
            # Exit with appropriate code
            if failed == 0:
                logger.success("🎉 All tests passed!")
                sys.exit(0)
            else:
                logger.error(f"💥 {failed} tests failed")
                sys.exit(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"💥 Test suite failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())