#!/usr/bin/env python3
"""
Test the recommendations API endpoint after fixing validation issues.
"""

import requests
import sys
from datetime import datetime

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_recommendations_api():
    """Test the recommendations API endpoint."""
    API_BASE = "http://localhost:8000"
    
    print_status("Testing Recommendations API After Fix")
    print("=" * 50)
    
    # First, register a test user and get a token
    print_status("Registering test user...")
    
    test_email = f"test_rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    register_data = {
        "email": test_email,
        "password": "testpassword123",
        "full_name": "Test Recommendations User",
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
        
        # Create a test assessment (we'll use this to test recommendations)
        print_status("Creating test assessment...")
        assessment_data = {
            "title": "Test Recommendations API Assessment",
            "description": "Testing recommendations API after validation fix",
            "business_requirements": {
                "business_goals": ["cost_optimization", "scalability"],
                "growth_projection": "moderate",
                "budget_constraints": 15000,
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
        
        # Test recommendations endpoint using our existing assessment with fixed data
        existing_assessment_id = "68aa4e80fd10b653d6f148ed"
        print_status(f"Testing recommendations API with existing assessment: {existing_assessment_id}")
        
        recommendations_response = requests.get(f"{API_BASE}/api/v1/recommendations/{existing_assessment_id}", headers=headers, timeout=30)
        
        print_status(f"Response status: {recommendations_response.status_code}")
        
        if recommendations_response.status_code == 200:
            print_status("✅ Recommendations API working successfully!")
            
            recommendations_data = recommendations_response.json()
            recommendations = recommendations_data.get("recommendations", [])
            summary = recommendations_data.get("summary", {})
            
            print_status(f"Retrieved {len(recommendations)} recommendations")
            print_status(f"Summary: {summary}")
            
            # Show details of first recommendation
            if recommendations:
                first_rec = recommendations[0]
                print_status("First recommendation details:")
                print(f"  Title: {first_rec.get('title', 'Unknown')}")
                print(f"  Agent: {first_rec.get('agent_name', 'Unknown')}")
                print(f"  Confidence Level: {first_rec.get('confidence_level', 'Unknown')}")
                print(f"  Confidence Score: {first_rec.get('confidence_score', 'Unknown')}")
                print(f"  Category: {first_rec.get('category', 'Unknown')}")
                print(f"  Updated At: {first_rec.get('updated_at', 'Unknown')}")
            
            return True
        else:
            print_status(f"❌ Recommendations API failed: {recommendations_response.status_code}", "ERROR")
            print_status(f"Response: {recommendations_response.text}", "ERROR")
            return False
        
    except Exception as e:
        print_status(f"Test failed with exception: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = test_recommendations_api()
    if success:
        print_status("🎉 Recommendations API test PASSED!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("❌ Recommendations API test FAILED!", "ERROR") 
        sys.exit(1)