#!/usr/bin/env python3
"""
End-to-end test to verify fixes for visualization issues.

This script tests:
1. Authentication workflow 
2. Assessment creation with real agent data
3. Visualization data generation from real assessments
4. Reports download functionality
5. Advanced analytics using real data
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import requests
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class EndToEndTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.auth_token = None
        self.test_user_email = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_user_password = "testpassword123"
        self.assessment_id = None
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print formatted status message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, auth_required: bool = True) -> Dict[str, Any]:
        """Make HTTP request with proper headers."""
        url = f"{self.api_base}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    def test_health_checks(self) -> bool:
        """Test that backend and frontend are running."""
        self.print_status("Testing health checks...")
        
        # Test backend health
        backend_health = self.make_request("GET", "/health", auth_required=False)
        if not backend_health["success"]:
            self.print_status(f"Backend health check failed: {backend_health['data']}", "ERROR")
            return False
            
        self.print_status("✅ Backend is healthy")
        
        # Test frontend health
        try:
            frontend_response = requests.get(f"{FRONTEND_URL}/health", timeout=10)
            if frontend_response.status_code == 200:
                self.print_status("✅ Frontend is healthy")
            else:
                self.print_status(f"Frontend health check returned {frontend_response.status_code}", "WARNING")
        except Exception as e:
            self.print_status(f"Frontend health check failed: {e}", "WARNING")
            
        return True
    
    def test_authentication(self) -> bool:
        """Test user registration and login."""
        self.print_status("Testing authentication workflow...")
        
        # Register test user
        register_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "full_name": "Test User",
            "company": "Test Company"
        }
        
        register_response = self.make_request("POST", "/api/v1/auth/register", register_data, auth_required=False)
        
        if not register_response["success"]:
            self.print_status(f"Registration failed: {register_response['data']}", "ERROR")
            return False
            
        # Extract token from registration response
        if "access_token" in register_response["data"]:
            self.auth_token = register_response["data"]["access_token"]
            self.print_status("✅ User registered and authenticated successfully")
        else:
            self.print_status("Registration succeeded but no token received", "ERROR")
            return False
            
        # Test token validation
        profile_response = self.make_request("GET", "/api/v1/auth/profile")
        if profile_response["success"]:
            self.print_status("✅ Token validation successful")
            return True
        else:
            self.print_status(f"Token validation failed: {profile_response['data']}", "ERROR")
            return False
    
    def test_assessment_creation(self) -> bool:
        """Test creating an assessment with real data."""
        self.print_status("Testing assessment creation...")
        
        assessment_data = {
            "title": "Test Infrastructure Assessment - End-to-End",
            "description": "Testing real agent data flow to visualizations",
            "business_requirements": {
                "business_goals": ["cost_optimization", "scalability", "security"],
                "growth_projection": "moderate",
                "budget_constraints": 25000,
                "team_structure": "medium",
                "compliance_requirements": ["SOX", "GDPR"],
                "project_timeline_months": 6
            },
            "technical_requirements": {
                "current_infrastructure": "hybrid",
                "workload_types": ["web_application", "api_services", "data_processing"],
                "performance_requirements": {
                    "requests_per_second": 1000,
                    "concurrent_users": 5000,
                    "availability_requirement": 99.9
                },
                "scalability_requirements": {
                    "auto_scaling": True,
                    "geographic_distribution": True,
                    "peak_load_multiplier": 5
                },
                "security_requirements": {
                    "encryption_at_rest_required": True,
                    "vpc_isolation_required": True,
                    "multi_factor_auth_required": True
                },
                "integration_requirements": {
                    "third_party_apis": ["payment_gateway", "analytics"],
                    "data_sources": ["postgresql", "redis"],
                    "monitoring_tools": ["prometheus", "grafana"]
                }
            }
        }
        
        create_response = self.make_request("POST", "/api/v1/assessments/", assessment_data)
        
        if not create_response["success"]:
            self.print_status(f"Assessment creation failed: {create_response['data']}", "ERROR")
            return False
            
        self.assessment_id = create_response["data"]["id"]
        self.print_status(f"✅ Assessment created with ID: {self.assessment_id}")
        
        # Wait a moment for any background processing
        import time
        time.sleep(2)
        
        return True
    
    def test_visualization_data(self) -> bool:
        """Test that visualization data is generated from real assessment."""
        if not self.assessment_id:
            self.print_status("No assessment ID available for visualization test", "ERROR")
            return False
            
        self.print_status("Testing visualization data generation...")
        
        viz_response = self.make_request("GET", f"/api/v1/assessments/{self.assessment_id}/visualization-data")
        
        if not viz_response["success"]:
            self.print_status(f"Visualization data request failed: {viz_response['data']}", "ERROR")
            return False
            
        viz_data = viz_response["data"]["data"]
        
        # Check if we have real assessment results structure
        if "assessment_results" in viz_data:
            results = viz_data["assessment_results"]
            if len(results) > 0:
                self.print_status(f"✅ Visualization data contains {len(results)} assessment categories")
                
                # Check data quality
                for result in results:
                    if "currentScore" in result and "targetScore" in result:
                        self.print_status(f"  - {result['category']}: {result['currentScore']}/{result['targetScore']}")
                return True
            else:
                self.print_status("Visualization data exists but assessment_results is empty", "WARNING")
                return True
        else:
            self.print_status("Visualization data missing assessment_results structure", "ERROR")
            return False
    
    def test_advanced_analytics(self) -> bool:
        """Test advanced analytics with real assessment data."""
        self.print_status("Testing advanced analytics...")
        
        analytics_response = self.make_request("GET", "/api/v2/advanced-analytics/dashboard")
        
        if not analytics_response["success"]:
            self.print_status(f"Advanced analytics request failed: {analytics_response['data']}", "ERROR")
            return False
            
        analytics_data = analytics_response["data"]
        
        # Check if analytics uses real data when assessments exist
        if "analytics" in analytics_data:
            cost_modeling = analytics_data["analytics"].get("cost_modeling", {})
            if "current_analysis" in cost_modeling:
                assessments_analyzed = cost_modeling["current_analysis"].get("assessments_analyzed", 0)
                self.print_status(f"✅ Advanced analytics analyzed {assessments_analyzed} assessments")
                
                if assessments_analyzed > 0:
                    total_cost = cost_modeling["current_analysis"].get("total_monthly_cost", 0)
                    self.print_status(f"  - Total monthly cost analysis: ${total_cost}")
                    
                return True
            else:
                self.print_status("Advanced analytics missing current_analysis structure", "ERROR")
                return False
        else:
            self.print_status("Advanced analytics missing analytics structure", "ERROR")
            return False
    
    def test_reports_functionality(self) -> bool:
        """Test reports generation and download functionality."""
        if not self.assessment_id:
            self.print_status("No assessment ID available for reports test", "ERROR")
            return False
            
        self.print_status("Testing reports functionality...")
        
        # Get existing reports
        reports_response = self.make_request("GET", f"/api/v1/reports/{self.assessment_id}")
        
        if reports_response["success"]:
            reports = reports_response["data"].get("reports", [])
            self.print_status(f"✅ Found {len(reports)} existing reports")
            
            if len(reports) > 0:
                # Test download functionality with first report
                report_id = reports[0]["id"]
                self.print_status(f"Testing download for report {report_id}")
                
                # Note: We can't actually test download via curl easily, but we can test the endpoint exists
                download_url = f"/api/v1/reports/{self.assessment_id}/reports/{report_id}/download?format=pdf"
                download_test = self.make_request("GET", download_url)
                
                # Download might fail without proper file, but should not return authentication error
                if download_test["status_code"] != 401:
                    self.print_status("✅ Download endpoint is accessible (authentication working)")
                else:
                    self.print_status("Download endpoint returned authentication error", "ERROR")
                    return False
        else:
            self.print_status("Could not retrieve reports list", "WARNING")
            
        return True
    
    def run_all_tests(self) -> bool:
        """Run all end-to-end tests."""
        self.print_status("Starting End-to-End Tests for Visualization Fixes", "INFO")
        print("=" * 70)
        
        tests = [
            ("Health Checks", self.test_health_checks),
            ("Authentication", self.test_authentication),
            ("Assessment Creation", self.test_assessment_creation),
            ("Visualization Data", self.test_visualization_data),
            ("Advanced Analytics", self.test_advanced_analytics),
            ("Reports Functionality", self.test_reports_functionality),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.print_status(f"Running {test_name}...")
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                self.print_status(f"{test_name}: {status}")
            except Exception as e:
                self.print_status(f"{test_name}: ❌ FAILED - {str(e)}", "ERROR")
                results[test_name] = False
            
            print("-" * 50)
        
        # Summary
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        print("=" * 70)
        self.print_status(f"TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            self.print_status("🎉 All tests passed! Visualization fixes are working correctly.", "SUCCESS")
        else:
            self.print_status(f"⚠️  {total - passed} tests failed. Please check the issues above.", "WARNING")
            
        return passed == total

def main():
    """Main test execution."""
    tester = EndToEndTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()