#!/usr/bin/env python3
"""
Check Recommendations Status
Verifies if AI recommendations and reports have been generated
"""

import requests
import json

API_BASE = "http://localhost:8000"

def login_and_check():
    """Login and check recommendation status."""
    
    # Login
    login_data = {
        "email": "liteshperumalla@gmail.com",
        "password": "Litesh@#12345"
    }
    
    response = requests.post(f"{API_BASE}/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Logged in successfully")
    
    # Get assessments
    response = requests.get(f"{API_BASE}/api/v1/assessments/", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get assessments")
        return
    
    assessments = response.json().get('assessments', [])
    print(f"📋 Found {len(assessments)} assessments")
    
    # Check each assessment
    for assessment in assessments:
        assessment_id = assessment['id']
        title = assessment['title']
        
        print(f"\n📊 Assessment: {title}")
        print(f"   ID: {assessment_id}")
        print(f"   Status: {assessment['status']}")
        
        # Check recommendations
        rec_response = requests.get(
            f"{API_BASE}/api/v1/recommendations/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if rec_response.status_code == 200:
            recommendations = rec_response.json()
            if isinstance(recommendations, list):
                print(f"   🎯 Recommendations: {len(recommendations)} found")
                if len(recommendations) > 0:
                    print(f"      Sample: {recommendations[0].get('title', 'N/A')}")
            else:
                print(f"   🎯 Recommendations: {recommendations}")
        else:
            print(f"   🎯 Recommendations: Failed to fetch ({rec_response.status_code})")
        
        # Check reports
        rep_response = requests.get(
            f"{API_BASE}/api/v1/reports/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if rep_response.status_code == 200:
            reports = rep_response.json()
            if isinstance(reports, list):
                print(f"   📄 Reports: {len(reports)} found")
                if len(reports) > 0:
                    print(f"      Sample: {reports[0].get('title', 'N/A')}")
            else:
                print(f"   📄 Reports: {reports}")
        else:
            print(f"   📄 Reports: Failed to fetch ({rep_response.status_code})")
    
    print(f"\n🔗 Dashboard: http://localhost:3000/dashboard")
    print("💡 If data shows up, refresh your browser dashboard!")

if __name__ == "__main__":
    print("🔍 CHECKING AI RECOMMENDATIONS STATUS")
    print("=" * 50)
    login_and_check()