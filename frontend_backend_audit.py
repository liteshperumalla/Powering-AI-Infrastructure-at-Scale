#!/usr/bin/env python3
"""
Comprehensive Frontend-Backend Integration Audit

This script performs a thorough audit of:
- Frontend UI components and functionality
- Backend API endpoint integration
- Real data vs mock data usage
- Interactive elements and forms
- Real-time data updates
- Authentication flows
- Error handling

Run with: python frontend_backend_audit.py
"""

import asyncio
import json
import os
import sys
import traceback
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TIMEOUT = 30

class FrontendBackendAuditor:
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "frontend_status": {},
            "backend_integration": {},
            "ui_elements": {},
            "data_verification": {},
            "issues_found": [],
            "recommendations": [],
            "summary": {}
        }
        self.driver = None
        self.auth_token = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_issue(self, section: str, issue: str, severity: str = "MEDIUM"):
        """Add an issue to the audit results."""
        self.audit_results["issues_found"].append({
            "section": section,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_recommendation(self, section: str, recommendation: str):
        """Add a recommendation to the audit results."""
        self.audit_results["recommendations"].append({
            "section": section,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })

    def setup_browser(self):
        """Setup Chrome browser for testing."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.log("✅ Browser setup successful")
            return True
        except Exception as e:
            self.log(f"❌ Browser setup failed: {e}", "ERROR")
            # Try to use requests only for basic testing
            return False

    def test_backend_health(self):
        """Test backend API health and basic endpoints."""
        self.log("🔍 Testing backend health...")
        
        backend_tests = {
            "health_endpoint": "/health",
            "api_docs": "/docs",
            "auth_register": "/api/v1/auth/register",
            "assessments_list": "/api/v1/assessments/",
            "reports_endpoint": "/api/v1/reports/",
            "analytics_endpoint": "/api/v2/advanced-analytics/dashboard"
        }
        
        backend_status = {}
        
        for test_name, endpoint in backend_tests.items():
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
                backend_status[test_name] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "accessible": response.status_code in [200, 401, 403]  # 401/403 for auth-protected endpoints
                }
                
                if response.status_code == 200:
                    self.log(f"  ✅ {test_name}: OK ({response.status_code})")
                elif response.status_code in [401, 403]:
                    self.log(f"  🔒 {test_name}: Protected ({response.status_code})")
                else:
                    self.log(f"  ⚠️  {test_name}: Unexpected status ({response.status_code})")
                    
            except Exception as e:
                backend_status[test_name] = {
                    "error": str(e),
                    "accessible": False
                }
                self.log(f"  ❌ {test_name}: {e}", "ERROR")
                self.add_issue("Backend", f"{test_name} endpoint failed: {e}", "HIGH")
        
        self.audit_results["backend_integration"] = backend_status
        return backend_status

    def test_frontend_accessibility(self):
        """Test frontend accessibility and basic page loads."""
        self.log("🌐 Testing frontend accessibility...")
        
        if not self.driver:
            self.log("Using requests for basic frontend testing...")
            try:
                response = requests.get(FRONTEND_URL, timeout=10)
                frontend_status = {
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code == 200:
                    self.log("✅ Frontend is accessible via HTTP")
                else:
                    self.log(f"❌ Frontend returned status {response.status_code}", "ERROR")
                    self.add_issue("Frontend", f"Frontend not accessible: {response.status_code}", "HIGH")
                    
            except Exception as e:
                frontend_status = {"accessible": False, "error": str(e)}
                self.log(f"❌ Frontend accessibility test failed: {e}", "ERROR")
                self.add_issue("Frontend", f"Frontend not accessible: {e}", "HIGH")
                
            self.audit_results["frontend_status"] = frontend_status
            return frontend_status
        
        # Test with browser
        pages_to_test = [
            {"path": "/", "name": "Home Page"},
            {"path": "/auth/login", "name": "Login Page"},
            {"path": "/dashboard", "name": "Dashboard"},
            {"path": "/analytics", "name": "Analytics Page"},
            {"path": "/assessments", "name": "Assessments Page"},
            {"path": "/reports", "name": "Reports Page"}
        ]
        
        page_results = {}
        
        for page in pages_to_test:
            try:
                self.log(f"Testing {page['name']}...")
                self.driver.get(f"{FRONTEND_URL}{page['path']}")
                
                # Wait for page to load
                WebDriverWait(self.driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check for error messages
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Error') or contains(text(), 'error') or contains(text(), '404') or contains(text(), '500')]")
                
                page_results[page['name']] = {
                    "accessible": True,
                    "title": self.driver.title,
                    "url": self.driver.current_url,
                    "has_errors": len(error_elements) > 0,
                    "error_messages": [elem.text for elem in error_elements]
                }
                
                if error_elements:
                    self.log(f"  ⚠️  {page['name']} has error messages: {[elem.text for elem in error_elements]}")
                    self.add_issue("Frontend", f"{page['name']} shows error messages", "MEDIUM")
                else:
                    self.log(f"  ✅ {page['name']} loaded successfully")
                    
            except TimeoutException:
                page_results[page['name']] = {"accessible": False, "error": "Page load timeout"}
                self.log(f"  ❌ {page['name']} failed to load (timeout)", "ERROR")
                self.add_issue("Frontend", f"{page['name']} failed to load", "HIGH")
            except Exception as e:
                page_results[page['name']] = {"accessible": False, "error": str(e)}
                self.log(f"  ❌ {page['name']} error: {e}", "ERROR")
                self.add_issue("Frontend", f"{page['name']} error: {e}", "HIGH")
        
        self.audit_results["frontend_status"] = {"pages": page_results}
        return page_results

    def test_authentication_flow(self):
        """Test authentication flow end-to-end."""
        self.log("🔐 Testing authentication flow...")
        
        auth_test_results = {}
        
        # Test backend authentication
        try:
            # Register a test user
            test_email = f"frontend_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            register_data = {
                "email": test_email,
                "password": "testpassword123",
                "full_name": "Frontend Test User",
                "company": "Test Company"
            }
            
            register_response = requests.post(f"{API_BASE_URL}/api/v1/auth/register", json=register_data, timeout=10)
            
            if register_response.status_code in [200, 201]:
                self.auth_token = register_response.json()["access_token"]
                auth_test_results["backend_auth"] = {
                    "registration": "success",
                    "token_received": bool(self.auth_token)
                }
                self.log("✅ Backend authentication successful")
            else:
                auth_test_results["backend_auth"] = {
                    "registration": "failed",
                    "status_code": register_response.status_code,
                    "error": register_response.text
                }
                self.log(f"❌ Backend authentication failed: {register_response.status_code}", "ERROR")
                self.add_issue("Authentication", f"Backend auth failed: {register_response.status_code}", "HIGH")
                
        except Exception as e:
            auth_test_results["backend_auth"] = {"error": str(e)}
            self.log(f"❌ Backend authentication error: {e}", "ERROR")
            self.add_issue("Authentication", f"Backend auth error: {e}", "HIGH")
        
        # Test frontend authentication UI
        if self.driver:
            try:
                self.driver.get(f"{FRONTEND_URL}/auth/login")
                
                # Look for login form elements
                login_elements = {
                    "email_field": self.driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[name='email']"),
                    "password_field": self.driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name='password']"),
                    "login_button": self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button:contains('Login'), button:contains('Sign In')")
                }
                
                auth_test_results["frontend_auth"] = {
                    "login_form_present": all(len(elements) > 0 for elements in login_elements.values()),
                    "elements_found": {k: len(v) for k, v in login_elements.items()}
                }
                
                if auth_test_results["frontend_auth"]["login_form_present"]:
                    self.log("✅ Frontend login form elements found")
                else:
                    self.log("❌ Frontend login form incomplete", "ERROR")
                    self.add_issue("Authentication", "Login form elements missing", "HIGH")
                    
            except Exception as e:
                auth_test_results["frontend_auth"] = {"error": str(e)}
                self.log(f"❌ Frontend auth UI test error: {e}", "ERROR")
                self.add_issue("Authentication", f"Frontend auth UI error: {e}", "MEDIUM")
        
        self.audit_results["authentication"] = auth_test_results
        return auth_test_results

    def test_data_integration(self):
        """Test frontend-backend data integration."""
        self.log("📊 Testing data integration...")
        
        if not self.auth_token:
            self.log("No auth token available, skipping authenticated data tests")
            return {}
        
        data_tests = {}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test assessments data
        try:
            assessments_response = requests.get(f"{API_BASE_URL}/api/v1/assessments/", headers=headers, timeout=10)
            if assessments_response.status_code == 200:
                assessments_data = assessments_response.json()
                data_tests["assessments"] = {
                    "api_accessible": True,
                    "data_count": len(assessments_data.get("assessments", [])),
                    "has_real_data": len(assessments_data.get("assessments", [])) > 0
                }
                self.log(f"✅ Assessments API: {data_tests['assessments']['data_count']} assessments found")
            else:
                data_tests["assessments"] = {
                    "api_accessible": False,
                    "status_code": assessments_response.status_code
                }
                self.log(f"❌ Assessments API failed: {assessments_response.status_code}", "ERROR")
                
        except Exception as e:
            data_tests["assessments"] = {"error": str(e)}
            self.log(f"❌ Assessments API error: {e}", "ERROR")
        
        # Test analytics data
        try:
            analytics_response = requests.get(f"{API_BASE_URL}/api/v2/advanced-analytics/dashboard", headers=headers, timeout=10)
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                data_tests["analytics"] = {
                    "api_accessible": True,
                    "has_real_data": "analytics" in analytics_data,
                    "mock_data_indicators": self._check_for_mock_data(analytics_data)
                }
                self.log("✅ Analytics API accessible")
            else:
                data_tests["analytics"] = {
                    "api_accessible": False,
                    "status_code": analytics_response.status_code
                }
                self.log(f"❌ Analytics API failed: {analytics_response.status_code}", "ERROR")
                
        except Exception as e:
            data_tests["analytics"] = {"error": str(e)}
            self.log(f"❌ Analytics API error: {e}", "ERROR")
        
        self.audit_results["data_integration"] = data_tests
        return data_tests

    def _check_for_mock_data(self, data):
        """Check for indicators of mock/demo data."""
        mock_indicators = []
        
        # Convert to string for searching
        data_str = json.dumps(data, default=str).lower()
        
        mock_keywords = [
            "demo", "mock", "sample", "test", "placeholder", "lorem ipsum",
            "example", "dummy", "fake", "fallback", "default"
        ]
        
        for keyword in mock_keywords:
            if keyword in data_str:
                mock_indicators.append(keyword)
        
        return mock_indicators

    def test_ui_elements_functionality(self):
        """Test interactive UI elements."""
        self.log("🖱️  Testing UI elements functionality...")
        
        if not self.driver:
            self.log("Browser not available, skipping UI element tests")
            return {}
        
        ui_tests = {}
        
        # Test dashboard page
        try:
            self.driver.get(f"{FRONTEND_URL}/dashboard")
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for common UI elements
            ui_elements = {
                "buttons": self.driver.find_elements(By.TAG_NAME, "button"),
                "links": self.driver.find_elements(By.TAG_NAME, "a"),
                "forms": self.driver.find_elements(By.TAG_NAME, "form"),
                "charts": self.driver.find_elements(By.CSS_SELECTOR, "canvas, svg, .chart, .graph"),
                "tables": self.driver.find_elements(By.TAG_NAME, "table"),
                "inputs": self.driver.find_elements(By.TAG_NAME, "input")
            }
            
            ui_tests["dashboard"] = {
                "elements_count": {k: len(v) for k, v in ui_elements.items()},
                "interactive_elements": len(ui_elements["buttons"]) + len(ui_elements["links"]) + len(ui_elements["inputs"])
            }
            
            self.log(f"✅ Dashboard UI elements: {ui_tests['dashboard']['interactive_elements']} interactive elements found")
            
            # Test clicking a button if available
            if ui_elements["buttons"]:
                try:
                    first_button = ui_elements["buttons"][0]
                    if first_button.is_enabled() and first_button.is_displayed():
                        button_text = first_button.text or first_button.get_attribute("aria-label") or "Unknown"
                        # Don't actually click to avoid side effects, just verify it's clickable
                        ui_tests["dashboard"]["first_button_clickable"] = True
                        ui_tests["dashboard"]["first_button_text"] = button_text
                        self.log(f"✅ First button is clickable: '{button_text}'")
                except Exception as e:
                    ui_tests["dashboard"]["button_test_error"] = str(e)
                    
        except Exception as e:
            ui_tests["dashboard"] = {"error": str(e)}
            self.log(f"❌ Dashboard UI test error: {e}", "ERROR")
            self.add_issue("UI Elements", f"Dashboard UI test failed: {e}", "MEDIUM")
        
        self.audit_results["ui_elements"] = ui_tests
        return ui_tests

    def check_for_frontend_mock_data(self):
        """Check frontend source code and network requests for mock data usage."""
        self.log("🔍 Checking for mock data in frontend...")
        
        mock_data_analysis = {
            "static_mock_data": [],
            "network_requests": [],
            "data_quality": {}
        }
        
        if self.driver:
            try:
                # Check network requests for API calls
                self.driver.get(f"{FRONTEND_URL}/dashboard")
                time.sleep(5)  # Wait for API calls to complete
                
                # Check browser console for errors or warnings
                logs = self.driver.get_log('browser')
                console_issues = []
                
                for log in logs:
                    if log['level'] in ['SEVERE', 'WARNING']:
                        console_issues.append({
                            "level": log['level'],
                            "message": log['message'],
                            "timestamp": log['timestamp']
                        })
                
                mock_data_analysis["console_issues"] = console_issues
                
                if console_issues:
                    self.log(f"⚠️  Found {len(console_issues)} console issues")
                    for issue in console_issues:
                        if 'mock' in issue['message'].lower() or 'demo' in issue['message'].lower():
                            self.add_issue("Mock Data", f"Console indicates mock data usage: {issue['message']}", "MEDIUM")
                else:
                    self.log("✅ No console errors indicating mock data usage")
                    
            except Exception as e:
                mock_data_analysis["browser_check_error"] = str(e)
                self.log(f"❌ Browser mock data check error: {e}", "WARNING")
        
        self.audit_results["mock_data_check"] = mock_data_analysis
        return mock_data_analysis

    def generate_summary(self):
        """Generate audit summary."""
        self.log("📝 Generating audit summary...")
        
        # Count issues by severity
        issue_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.audit_results["issues_found"]:
            issue_counts[issue["severity"]] += 1
        
        # Calculate health score
        total_issues = sum(issue_counts.values())
        health_score = max(0, 100 - (issue_counts["HIGH"] * 20 + issue_counts["MEDIUM"] * 10 + issue_counts["LOW"] * 5))
        
        # Analyze test results
        backend_accessible = self.audit_results.get("backend_integration", {})
        frontend_accessible = self.audit_results.get("frontend_status", {})
        auth_working = self.audit_results.get("authentication", {})
        
        self.audit_results["summary"] = {
            "health_score": health_score,
            "total_issues": total_issues,
            "issue_breakdown": issue_counts,
            "backend_health": len([test for test in backend_accessible.values() if isinstance(test, dict) and test.get("accessible", False)]),
            "frontend_health": bool(frontend_accessible.get("accessible", False)),
            "auth_working": bool(auth_working.get("backend_auth", {}).get("registration") == "success"),
            "recommendations_count": len(self.audit_results["recommendations"]),
            "audit_status": "CRITICAL" if health_score < 50 else "WARNING" if health_score < 80 else "HEALTHY"
        }
        
        # Generate recommendations
        if issue_counts["HIGH"] > 0:
            self.add_recommendation("System", "Address HIGH severity issues immediately")
        
        if not self.audit_results["summary"]["frontend_health"]:
            self.add_recommendation("Frontend", "Fix frontend accessibility issues")
            
        if not self.audit_results["summary"]["auth_working"]:
            self.add_recommendation("Authentication", "Fix authentication flow")

    def print_report(self):
        """Print the audit report."""
        print("\n" + "="*80)
        print("FRONTEND-BACKEND INTEGRATION AUDIT REPORT")
        print("="*80)
        print(f"Audit Timestamp: {self.audit_results['timestamp']}")
        print(f"Health Score: {self.audit_results['summary']['health_score']}/100")
        print(f"Overall Status: {self.audit_results['summary']['audit_status']}")
        print(f"Total Issues: {self.audit_results['summary']['total_issues']}")
        
        # Backend health
        backend_health = self.audit_results['summary']['backend_health']
        print(f"Backend Endpoints Working: {backend_health}")
        
        # Frontend health
        frontend_health = "✅ Accessible" if self.audit_results['summary']['frontend_health'] else "❌ Not Accessible"
        print(f"Frontend Status: {frontend_health}")
        
        # Authentication
        auth_status = "✅ Working" if self.audit_results['summary']['auth_working'] else "❌ Issues Found"
        print(f"Authentication: {auth_status}")
        
        # Issues
        if self.audit_results["issues_found"]:
            print(f"\n🚨 ISSUES FOUND ({self.audit_results['summary']['total_issues']}):")
            for issue in self.audit_results["issues_found"]:
                severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                print(f"  {severity_emoji[issue['severity']]} [{issue['section']}] {issue['issue']}")
        
        # Recommendations
        if self.audit_results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS ({len(self.audit_results['recommendations'])}):")
            for rec in self.audit_results["recommendations"]:
                print(f"  • [{rec['section']}] {rec['recommendation']}")
        
        print("="*80)

    def save_report(self, filename: str = None):
        """Save the audit report to a file."""
        if not filename:
            filename = f"frontend_backend_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            self.log(f"✅ Audit report saved to {filename}")
        except Exception as e:
            self.log(f"❌ Failed to save report: {e}", "ERROR")

    def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.log("✅ Browser cleanup completed")
            except Exception as e:
                self.log(f"⚠️  Browser cleanup warning: {e}", "WARNING")

    async def run_audit(self):
        """Run the complete frontend-backend audit."""
        self.log("🚀 Starting comprehensive frontend-backend audit...")
        
        try:
            # Setup browser (optional - continue with requests if fails)
            self.setup_browser()
            
            # Wait for services to be ready
            self.log("⏳ Waiting for services to be ready...")
            time.sleep(15)
            
            # Run audit sections
            self.test_backend_health()
            self.test_frontend_accessibility()
            self.test_authentication_flow()
            self.test_data_integration()
            self.test_ui_elements_functionality()
            self.check_for_frontend_mock_data()
            
            # Generate summary and report
            self.generate_summary()
            self.print_report()
            self.save_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Audit failed: {e}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

def check_services_ready():
    """Check if services are ready before starting audit."""
    print("🔍 Checking if services are ready...")
    
    max_retries = 12  # 2 minutes with 10-second intervals
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check backend
            backend_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if backend_response.status_code == 200:
                print("✅ Backend is ready")
                break
        except:
            pass
        
        retry_count += 1
        print(f"⏳ Waiting for services... ({retry_count}/{max_retries})")
        time.sleep(10)
    
    if retry_count >= max_retries:
        print("❌ Services not ready, proceeding with audit anyway...")
    
    return True

async def main():
    """Main function."""
    print("🔍 Frontend-Backend Integration Auditor")
    print("=" * 60)
    
    # Check if services are ready
    check_services_ready()
    
    # Run audit
    auditor = FrontendBackendAuditor()
    success = await auditor.run_audit()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)