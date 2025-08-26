#!/usr/bin/env python3
"""
Test the reports API endpoint with proper authentication to debug 500 error.
"""

import requests
import sys
from datetime import datetime

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_reports_api_with_auth():
    """Test the reports API endpoint with authentication."""
    API_BASE = "http://localhost:8000"
    
    print_status("Testing Reports API With Authentication")
    print("=" * 50)
    
    # Register a test user and get a token
    print_status("Registering test user...")
    
    test_email = f"test_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    register_data = {
        "email": test_email,
        "password": "testpassword123",
        "full_name": "Test Reports User",
        "company": "Test Company"
    }
    
    try:
        # Register user
        register_response = requests.post(f"{API_BASE}/api/v1/auth/register", json=register_data, timeout=30)
        if register_response.status_code not in [200, 201]:
            print_status(f"Registration failed: {register_response.text}", "ERROR")
            return False
            
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        print_status("✅ User registered successfully")
        
        # Test the specific failing report endpoint
        failing_report_id = "68aa4e80fd10b653d6f148f0"
        print_status(f"Testing failing report endpoint: {failing_report_id}")
        
        # Test direct report endpoint (the one that's failing)
        report_response = requests.get(f"{API_BASE}/api/v1/reports/{failing_report_id}", headers=headers, timeout=30)
        
        print_status(f"Report API Response Status: {report_response.status_code}")
        
        if report_response.status_code == 200:
            print_status("✅ Report API working successfully!")
            report_data = report_response.json()
            print_status(f"Report Title: {report_data.get('title', 'Unknown')}")
            print_status(f"Report Type: {report_data.get('report_type', 'Unknown')}")
            print_status(f"Report Status: {report_data.get('status', 'Unknown')}")
            return True
        else:
            print_status(f"❌ Report API failed with status {report_response.status_code}", "ERROR")
            print_status(f"Error Response: {report_response.text}", "ERROR")
            
            # Try to get more detailed error info
            try:
                error_data = report_response.json()
                print_status(f"Error Detail: {error_data.get('detail', 'Unknown error')}", "ERROR")
            except:
                print_status("Could not parse error response as JSON", "ERROR")
            
            return False
        
    except Exception as e:
        print_status(f"Test failed with exception: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = test_reports_api_with_auth()
    if success:
        print_status("🎉 Reports API test PASSED!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("❌ Reports API test FAILED!", "ERROR") 
        sys.exit(1)