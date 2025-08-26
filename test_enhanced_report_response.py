#!/usr/bin/env python3
"""
Test the enhanced report API response structure to verify sections, key_findings, and recommendations.
"""

import requests
import json
import sys
from datetime import datetime

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_enhanced_report_response():
    """Test the enhanced report API response structure."""
    API_BASE = "http://localhost:8000"
    
    print_status("Testing Enhanced Report API Response Structure")
    print("=" * 60)
    
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
        
        # Test the enhanced report endpoint
        report_id = "68aa4e80fd10b653d6f148f0"
        print_status(f"Testing enhanced report response for: {report_id}")
        
        # Get report with enhanced structure
        report_response = requests.get(f"{API_BASE}/api/v1/reports/{report_id}", headers=headers, timeout=30)
        
        print_status(f"Report API Response Status: {report_response.status_code}")
        
        if report_response.status_code == 200:
            print_status("✅ Report API working successfully!")
            report_data = report_response.json()
            
            print_status("📊 ENHANCED REPORT RESPONSE ANALYSIS:")
            print_status(f"Report Title: {report_data.get('title', 'Unknown')}")
            print_status(f"Report Type: {report_data.get('report_type', 'Unknown')}")
            print_status(f"Status: {report_data.get('status', 'Unknown')}")
            print_status(f"Word Count: {report_data.get('word_count', 0)}")
            print_status(f"Pages: {report_data.get('total_pages', 0)}")
            
            # Test sections structure
            sections = report_data.get('sections', [])
            print_status(f"📝 SECTIONS ({len(sections)}):")
            for i, section in enumerate(sections):
                if isinstance(section, dict):
                    title = section.get('title', 'No Title')
                    section_type = section.get('type', 'No Type')
                    content = section.get('content', 'No Content')
                    order = section.get('order', 'No Order')
                    print_status(f"  {i+1}. {title} ({section_type})")
                    print_status(f"      Content: {content[:100]}..." if len(content) > 100 else f"      Content: {content}")
                    print_status(f"      Order: {order}")
                else:
                    print_status(f"  {i+1}. {section} (string format - old structure)")
            
            # Test key findings
            key_findings = report_data.get('key_findings', [])
            print_status(f"🔍 KEY FINDINGS ({len(key_findings)}):")
            for i, finding in enumerate(key_findings):
                print_status(f"  {i+1}. {finding}")
            
            # Test recommendations  
            recommendations = report_data.get('recommendations', [])
            print_status(f"💡 RECOMMENDATIONS ({len(recommendations)}):")
            for i, rec in enumerate(recommendations):
                print_status(f"  {i+1}. {rec}")
            
            # Check if enhanced structure is working
            has_enhanced_sections = any(isinstance(section, dict) for section in sections)
            has_key_findings = len(key_findings) > 0
            has_recommendations = len(recommendations) > 0
            
            print_status("")
            print_status("🔍 ENHANCEMENT STATUS:")
            print_status(f"✅ Enhanced sections: {has_enhanced_sections}")
            print_status(f"✅ Key findings present: {has_key_findings}")
            print_status(f"✅ Recommendations present: {has_recommendations}")
            
            if has_enhanced_sections and has_key_findings and has_recommendations:
                print_status("🎉 FULL ENHANCEMENT SUCCESSFUL!", "SUCCESS")
                return True
            else:
                print_status("⚠️ Partial enhancement - some features missing", "WARN")
                return False
        else:
            print_status(f"❌ Report API failed: {report_response.status_code}", "ERROR")
            print_status(f"Response: {report_response.text}", "ERROR")
            return False
        
    except Exception as e:
        print_status(f"Test failed with exception: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = test_enhanced_report_response()
    if success:
        print_status("🎉 Enhanced report API test PASSED!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("❌ Enhanced report API test FAILED!", "ERROR") 
        sys.exit(1)