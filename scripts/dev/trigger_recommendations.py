#!/usr/bin/env python3
"""
Trigger Recommendations Generation

This script specifically triggers the recommendation generation workflow
to ensure real AI-generated recommendations are available.
"""

import requests
import json
import time

def trigger_recommendations():
    base_url = "http://localhost:8000"

    # Get access token
    login_data = {
        "username": "data.generator@infra-mind.com",
        "password": "SecurePassword123!"
    }

    session = requests.Session()
    response = session.post(f"{base_url}/api/v2/auth/login", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
        print("✅ Authenticated successfully")
    else:
        print("❌ Authentication failed")
        return

    # Get available assessments
    assessments_response = session.get(f"{base_url}/api/v2/assessments/")
    if assessments_response.status_code == 200:
        assessments_data = assessments_response.json()
        assessments = assessments_data.get("assessments", [])

        if assessments:
            assessment_id = assessments[0].get("id") or assessments[0].get("_id")
            print(f"📊 Using assessment: {assessment_id}")

            # Trigger recommendation generation using workflow
            workflow_data = {
                "assessment_id": assessment_id,
                "agent_types": ["infrastructure", "cost_optimization", "security", "mlops", "compliance"],
                "priority": "high"
            }

            # Try to trigger through workflow endpoint
            workflow_response = session.post(
                f"{base_url}/api/v2/assessments/{assessment_id}/workflow/recommendations",
                json=workflow_data
            )

            if workflow_response.status_code in [200, 201, 202]:
                print("✅ Triggered recommendation workflow")
            else:
                print(f"⚠️ Workflow trigger failed: {workflow_response.status_code}")
                # Try direct recommendation generation
                print("🔄 Trying direct recommendation generation...")

                direct_response = session.post(
                    f"{base_url}/api/v2/recommendations/{assessment_id}/generate"
                )

                if direct_response.status_code in [200, 201, 202]:
                    print("✅ Triggered direct recommendation generation")
                else:
                    print(f"⚠️ Direct generation also failed: {direct_response.status_code}")

            # Wait and check results
            print("⏳ Waiting for recommendations to generate...")
            time.sleep(10)

            # Check recommendations
            recs_response = session.get(f"{base_url}/api/v2/recommendations/{assessment_id}")
            if recs_response.status_code == 200:
                recs_data = recs_response.json()
                recommendations = recs_data.get("recommendations", [])
                print(f"🎉 Found {len(recommendations)} recommendations")

                if recommendations:
                    for i, rec in enumerate(recommendations[:3]):  # Show first 3
                        print(f"  {i+1}. {rec.get('title', 'Untitled')} - {rec.get('category', 'General')}")
                else:
                    print("⚠️ No recommendations generated yet")
            else:
                print(f"⚠️ Could not fetch recommendations: {recs_response.status_code}")
        else:
            print("❌ No assessments found")
    else:
        print("❌ Could not fetch assessments")

if __name__ == "__main__":
    print("🔥 Triggering Recommendations Generation")
    print("=" * 40)
    trigger_recommendations()