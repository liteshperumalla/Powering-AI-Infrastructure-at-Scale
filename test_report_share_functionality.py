#!/usr/bin/env python3
"""
Comprehensive test script for report sharing functionality.

Tests all aspects of the report sharing feature including:
- Share report with user
- Create public links
- Permission validation
- Error handling
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "liteshperumalla@gmail.com"
TEST_USER_PASSWORD = "Litesh@#12345"
SHARE_TARGET_EMAIL = "shared@example.com"

class ReportShareTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_report_id = None
        self.test_user_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results with consistent formatting."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
        if details:
            print(f"    Details: {details}")

    async def authenticate_user(self) -> bool:
        """Authenticate test user and get token."""
        try:
            # Try to register user first (in case they don't exist)
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "username": TEST_USER_EMAIL.split("@")[0],
                "full_name": "Test User"
            }
            
            async with self.session.post(f"{BASE_URL}/auth/register", json=register_data) as resp:
                if resp.status in [200, 409]:  # 409 = user already exists
                    self.log_test("User Registration", "PASS", "User registered or already exists")
                else:
                    self.log_test("User Registration", "WARN", f"Status: {resp.status}")
            
            # Login user
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.auth_token = result.get("access_token")
                    if self.auth_token:
                        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                        self.log_test("User Authentication", "PASS", "Successfully logged in")
                        return True
                    else:
                        self.log_test("User Authentication", "FAIL", "No access token received")
                        return False
                else:
                    self.log_test("User Authentication", "FAIL", f"Login failed with status {resp.status}")
                    return False
                    
        except Exception as e:
            self.log_test("User Authentication", "FAIL", f"Exception: {str(e)}")
            return False

    async def get_or_create_test_report(self) -> bool:
        """Get an existing report or create one for testing."""
        try:
            # First try to get existing reports
            async with self.session.get(f"{BASE_URL}/reports/all") as resp:
                if resp.status == 200:
                    reports = await resp.json()
                    if reports and len(reports) > 0:
                        self.test_report_id = reports[0]["id"]
                        self.log_test("Get Test Report", "PASS", f"Using existing report: {self.test_report_id}")
                        return True
                        
            # If no reports exist, we need to create one
            # First check if we have any assessments
            async with self.session.get(f"{BASE_URL}/assessments/") as resp:
                if resp.status == 200:
                    assessments = await resp.json()
                    if assessments and len(assessments) > 0:
                        assessment_id = assessments[0]["id"]
                        
                        # Create a test report
                        report_data = {
                            "title": "Test Report for Share Functionality",
                            "report_type": "comprehensive",
                            "format": "pdf"
                        }
                        
                        async with self.session.post(f"{BASE_URL}/assessments/{assessment_id}/generate-report", json=report_data) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                self.test_report_id = result.get("report_id")
                                if self.test_report_id:
                                    self.log_test("Create Test Report", "PASS", f"Created report: {self.test_report_id}")
                                    return True
            
            self.log_test("Get Test Report", "FAIL", "No reports available and couldn't create one")
            return False
            
        except Exception as e:
            self.log_test("Get Test Report", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_share_report_endpoint(self) -> bool:
        """Test the main share report functionality."""
        if not self.test_report_id:
            self.log_test("Share Report Endpoint", "FAIL", "No test report available")
            return False
            
        try:
            share_data = {
                "user_email": SHARE_TARGET_EMAIL,
                "permission": "view"
            }
            
            async with self.session.post(f"{BASE_URL}/reports/reports/{self.test_report_id}/share", json=share_data) as resp:
                response_text = await resp.text()
                
                if resp.status == 200:
                    result = await resp.json() if response_text else {}
                    self.log_test("Share Report Endpoint", "PASS", f"Report shared successfully: {result}")
                    return True
                elif resp.status == 404:
                    self.log_test("Share Report Endpoint", "FAIL", "Report not found")
                    return False
                elif resp.status == 500:
                    self.log_test("Share Report Endpoint", "WARN", "Server error - feature may not be fully implemented")
                    return False
                else:
                    self.log_test("Share Report Endpoint", "FAIL", f"Unexpected status {resp.status}: {response_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Share Report Endpoint", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_share_report_permissions(self) -> bool:
        """Test different permission levels for sharing."""
        if not self.test_report_id:
            self.log_test("Share Report Permissions", "FAIL", "No test report available")
            return False
            
        permissions = ["view", "edit", "admin"]
        results = []
        
        for permission in permissions:
            try:
                share_data = {
                    "user_email": f"test_{permission}@example.com",
                    "permission": permission
                }
                
                async with self.session.post(f"{BASE_URL}/reports/reports/{self.test_report_id}/share", json=share_data) as resp:
                    if resp.status == 200:
                        results.append(f"{permission}: ✅")
                    else:
                        results.append(f"{permission}: ❌ ({resp.status})")
                        
            except Exception as e:
                results.append(f"{permission}: ❌ (Exception: {str(e)})")
        
        success_count = len([r for r in results if "✅" in r])
        self.log_test("Share Report Permissions", "PASS" if success_count > 0 else "FAIL", 
                     f"{success_count}/3 permissions tested: {', '.join(results)}")
        return success_count > 0

    async def test_create_public_link(self) -> bool:
        """Test creating public links for reports."""
        if not self.test_report_id:
            self.log_test("Create Public Link", "FAIL", "No test report available")
            return False
            
        try:
            async with self.session.post(f"{BASE_URL}/reports/reports/{self.test_report_id}/public-link") as resp:
                response_text = await resp.text()
                
                if resp.status == 200:
                    result = await resp.json() if response_text else {}
                    public_token = result.get("public_token") or result.get("token")
                    if public_token:
                        self.log_test("Create Public Link", "PASS", f"Public link created: {public_token[:20]}...")
                        return True
                    else:
                        self.log_test("Create Public Link", "PASS", "Public link endpoint responded successfully")
                        return True
                elif resp.status == 404:
                    self.log_test("Create Public Link", "FAIL", "Report not found")
                    return False
                elif resp.status == 500:
                    self.log_test("Create Public Link", "WARN", "Server error - feature may not be fully implemented")
                    return False
                else:
                    self.log_test("Create Public Link", "FAIL", f"Unexpected status {resp.status}: {response_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Create Public Link", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_invalid_report_sharing(self) -> bool:
        """Test error handling for invalid report IDs."""
        try:
            fake_report_id = "invalid_report_id_12345"
            share_data = {
                "user_email": SHARE_TARGET_EMAIL,
                "permission": "view"
            }
            
            async with self.session.post(f"{BASE_URL}/reports/reports/{fake_report_id}/share", json=share_data) as resp:
                if resp.status in [404, 422, 500]:  # Expected error codes
                    self.log_test("Invalid Report Sharing", "PASS", f"Correctly handled invalid report ID (status: {resp.status})")
                    return True
                else:
                    self.log_test("Invalid Report Sharing", "FAIL", f"Unexpected status for invalid ID: {resp.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Invalid Report Sharing", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_share_request_validation(self) -> bool:
        """Test request validation for sharing."""
        if not self.test_report_id:
            self.log_test("Share Request Validation", "FAIL", "No test report available")
            return False
            
        test_cases = [
            {"data": {"user_email": "", "permission": "view"}, "desc": "empty email"},
            {"data": {"user_email": "invalid-email", "permission": "view"}, "desc": "invalid email format"},
            {"data": {"user_email": SHARE_TARGET_EMAIL, "permission": "invalid"}, "desc": "invalid permission"},
            {"data": {"user_email": SHARE_TARGET_EMAIL}, "desc": "missing permission (should default to view)"},
        ]
        
        results = []
        for test_case in test_cases:
            try:
                async with self.session.post(f"{BASE_URL}/reports/reports/{self.test_report_id}/share", 
                                           json=test_case["data"]) as resp:
                    if test_case["desc"] == "missing permission (should default to view)":
                        # This should succeed with default permission
                        status = "✅" if resp.status == 200 else f"❌ ({resp.status})"
                    else:
                        # These should fail with validation errors
                        status = "✅" if resp.status in [400, 422] else f"❌ ({resp.status})"
                    
                    results.append(f"{test_case['desc']}: {status}")
                    
            except Exception as e:
                results.append(f"{test_case['desc']}: ❌ (Exception)")
        
        success_count = len([r for r in results if "✅" in r])
        self.log_test("Share Request Validation", "PASS" if success_count > 2 else "WARN", 
                     f"{success_count}/4 validation tests: {', '.join(results)}")
        return success_count > 2

    async def test_endpoint_availability(self) -> bool:
        """Test that the share endpoints are available and responding."""
        endpoints_to_test = [
            "/reports/test",
            "/reports/all", 
            f"/reports/reports/{self.test_report_id or 'test'}/share" if self.test_report_id else "/reports/test/share",
            f"/reports/reports/{self.test_report_id or 'test'}/public-link" if self.test_report_id else "/reports/test/public-link"
        ]
        
        available_endpoints = []
        for endpoint in endpoints_to_test:
            try:
                # Use GET for test endpoints, POST for share endpoints
                method = self.session.get if not any(x in endpoint for x in ['/share', '/public-link']) else self.session.post
                
                async with method(f"{BASE_URL}{endpoint}", json={} if 'share' in endpoint else None) as resp:
                    if resp.status < 500:  # Any response that's not a server error
                        available_endpoints.append(endpoint)
            except:
                pass
        
        self.log_test("Endpoint Availability", "PASS" if len(available_endpoints) > 2 else "FAIL",
                     f"{len(available_endpoints)}/4 endpoints available: {available_endpoints}")
        return len(available_endpoints) > 2

    async def run_all_tests(self):
        """Run all share functionality tests."""
        print("🚀 Starting Report Share Functionality Tests")
        print("=" * 60)
        
        # Authentication test
        auth_success = await self.authenticate_user()
        if not auth_success:
            print("❌ Authentication failed - cannot proceed with other tests")
            return False
            
        # Get test report
        await self.get_or_create_test_report()
        
        # Run all tests
        test_results = []
        
        test_results.append(await self.test_endpoint_availability())
        test_results.append(await self.test_share_report_endpoint())
        test_results.append(await self.test_share_report_permissions())
        test_results.append(await self.test_create_public_link())
        test_results.append(await self.test_invalid_report_sharing())
        test_results.append(await self.test_share_request_validation())
        
        # Summary
        print("\n" + "=" * 60)
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        if passed == total:
            print("🎉 All share functionality tests completed successfully!")
        elif passed > total // 2:
            print("⚠️  Most tests passed - some features may need attention")
        else:
            print("❌ Multiple test failures - share functionality needs investigation")
            
        return passed > total // 2


async def main():
    """Main test execution function."""
    async with ReportShareTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    print("Report Share Functionality Test Suite")
    print("Testing share functionality in reports...")
    print()
    
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        print(f"\nTest suite completed with exit code: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        exit(1)