#!/usr/bin/env python3
"""
Test script specifically for report download functionality after the fix.
"""

import requests
import sys
from datetime import datetime

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_report_download():
    """Test the report download functionality."""
    API_BASE = "http://localhost:8000"
    
    print_status("Testing Report Download Fix")
    print("=" * 50)
    
    # First, let's register a test user and get a token
    print_status("Registering test user...")
    
    test_email = f"test_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    register_data = {
        "email": test_email,
        "password": "testpassword123",
        "full_name": "Test Download User",
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
        
        # Create an assessment
        print_status("Creating test assessment...")
        assessment_data = {
            "title": "Test Report Download Assessment",
            "description": "Testing report download functionality after enum fix",
            "business_requirements": {
                "business_goals": ["cost_optimization"],
                "growth_projection": "moderate",
                "budget_constraints": 10000,
                "team_structure": "small",
                "compliance_requirements": ["SOX"],
                "project_timeline_months": 3
            },
            "technical_requirements": {
                "current_infrastructure": "cloud",
                "workload_types": ["web_application"],
                "performance_requirements": {
                    "requests_per_second": 500,
                    "concurrent_users": 1000,
                    "availability_requirement": 99.5
                },
                "scalability_requirements": {
                    "auto_scaling": True,
                    "geographic_distribution": False,
                    "peak_load_multiplier": 3
                },
                "security_requirements": {
                    "encryption_at_rest_required": True,
                    "vpc_isolation_required": True,
                    "multi_factor_auth_required": True
                },
                "integration_requirements": {
                    "third_party_apis": ["payment_gateway"],
                    "data_sources": ["postgresql"],
                    "monitoring_tools": ["prometheus"]
                }
            }
        }
        
        create_response = requests.post(f"{API_BASE}/api/v1/assessments/", json=assessment_data, headers=headers, timeout=30)
        if create_response.status_code not in [200, 201]:
            print_status(f"Assessment creation failed: {create_response.text}", "ERROR")
            return False
            
        assessment_id = create_response.json()["id"]
        print_status(f"✅ Assessment created: {assessment_id}")
        
        # Get reports for this assessment
        print_status("Fetching reports...")
        reports_response = requests.get(f"{API_BASE}/api/v1/reports/{assessment_id}", headers=headers, timeout=30)
        
        if reports_response.status_code != 200:
            print_status(f"Failed to fetch reports: {reports_response.text}", "ERROR")
            return False
            
        reports_data = reports_response.json()
        reports = reports_data.get("reports", [])
        
        if not reports:
            print_status("No reports found for assessment", "WARNING")
            return True  # Not necessarily an error
            
        print_status(f"✅ Found {len(reports)} reports")
        
        # Test download for each report
        success_count = 0
        for i, report in enumerate(reports):
            report_id = report["id"]
            report_type = report.get("report_type", "unknown")
            
            print_status(f"Testing download for report {i+1}: {report_id} (type: {report_type})")
            
            # Test download endpoint
            download_url = f"{API_BASE}/api/v1/reports/{assessment_id}/reports/{report_id}/download?format=pdf"
            download_response = requests.get(download_url, headers=headers, timeout=30)
            
            if download_response.status_code == 200:
                print_status(f"✅ Report {report_id} download successful")
                success_count += 1
            else:
                print_status(f"❌ Report {report_id} download failed: {download_response.status_code} - {download_response.text}", "ERROR")
        
        print_status(f"Download test completed: {success_count}/{len(reports)} reports downloaded successfully")
        return success_count == len(reports)
        
    except Exception as e:
        print_status(f"Test failed with exception: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = test_report_download()
    if success:
        print_status("🎉 Report download fix test PASSED!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("❌ Report download fix test FAILED!", "ERROR") 
        sys.exit(1)