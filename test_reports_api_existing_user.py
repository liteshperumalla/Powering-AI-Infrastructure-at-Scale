#!/usr/bin/env python3
"""
Test the reports API endpoint with existing user to debug 500 error.
"""

import requests
import sys
from datetime import datetime

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_reports_api_with_existing_user():
    """Test the reports API endpoint with existing user."""
    API_BASE = "http://localhost:8000"
    
    print_status("Testing Reports API With Existing User")
    print("=" * 50)
    
    # Login with existing user
    print_status("Logging in with existing user...")
    
    login_data = {
        "email": "liteshperumalla@gmail.com",
        "password": "Litesh@#12345"
    }
    
    try:
        # Login
        login_response = requests.post(f"{API_BASE}/api/v1/auth/login", json=login_data, timeout=30)
        if login_response.status_code not in [200, 201]:
            print_status(f"Login failed: {login_response.text}", "ERROR")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        print_status("✅ User logged in successfully")
        
        # Test the specific failing report endpoint
        failing_report_id = "68aa4e80fd10b653d6f148f0"
        print_status(f"Testing report endpoint: {failing_report_id}")
        
        # Test direct report endpoint (the one that's failing)
        report_response = requests.get(f"{API_BASE}/api/v1/reports/{failing_report_id}", headers=headers, timeout=30)
        
        print_status(f"Report API Response Status: {report_response.status_code}")
        
        if report_response.status_code == 200:
            print_status("✅ Report API working successfully!")
            report_data = report_response.json()
            print_status(f"Report Title: {report_data.get('title', 'Unknown')}")
            print_status(f"Report Type: {report_data.get('report_type', 'Unknown')}")
            print_status(f"Report Status: {report_data.get('status', 'Unknown')}")
            print_status(f"Word Count: {report_data.get('word_count', 0)}")
            print_status(f"Pages: {report_data.get('total_pages', 0)}")
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
    success = test_reports_api_with_existing_user()
    if success:
        print_status("🎉 Reports API test PASSED!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("❌ Reports API test FAILED!", "ERROR") 
        sys.exit(1)