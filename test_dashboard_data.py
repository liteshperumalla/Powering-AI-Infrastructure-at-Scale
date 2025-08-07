#!/usr/bin/env python3
"""
Test dashboard data API endpoints
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v2"

async def test_dashboard_data():
    """Test dashboard data endpoints"""
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Register a user
        print("🔍 Step 1: Registering test user...")
        user_data = {
            "email": "dashboard_test@example.com",
            "password": "TestPass123!",
            "full_name": "Dashboard Test User",
            "company": "Test Company"
        }
        
        try:
            async with session.post(f"{API_BASE_URL}/auth/register", json=user_data) as response:
                if response.status == 201:
                    auth_data = await response.json()
                    token = auth_data["access_token"]
                    print(f"✅ User registered successfully")
                else:
                    # Try to login if user already exists
                    print(f"🔄 Registration failed ({response.status}), trying login...")
                    async with session.post(f"{API_BASE_URL}/auth/login", json={
                        "email": user_data["email"],
                        "password": user_data["password"]
                    }) as login_response:
                        if login_response.status == 200:
                            auth_data = await login_response.json()
                            token = auth_data["access_token"]
                            print(f"✅ User logged in successfully")
                        else:
                            print(f"❌ Both registration and login failed")
                            return
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return

        # Set up headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 2: Create a test assessment
        print("\n🔍 Step 2: Creating test assessment...")
        assessment_data = {
            "title": "Test Dashboard Assessment",
            "description": "Assessment for testing dashboard data",
            "business_requirements": {
                "business_goals": ["scalability", "cost_optimization"],
                "growth_projection": "high_growth",
                "budget_constraints": 100000,
                "team_structure": "medium",
                "compliance_requirements": ["gdpr", "hipaa"],
                "project_timeline_months": 12
            },
            "technical_requirements": {
                "current_infrastructure": "cloud_hybrid",
                "workload_types": ["web_application", "data_processing"],
                "performance_requirements": {
                    "api_response_time_ms": 200,
                    "requests_per_second": 1000,
                    "concurrent_users": 5000
                },
                "scalability_requirements": {
                    "auto_scaling": True,
                    "load_balancing": True,
                    "geographic_distribution": ["us_east", "us_west", "eu_west"]
                },
                "security_requirements": {
                    "data_encryption": True,
                    "access_control": "rbac",
                    "audit_logging": True
                },
                "integration_requirements": {
                    "apis": ["rest", "graphql"],
                    "databases": ["postgresql", "redis"],
                    "message_queues": ["kafka"]
                }
            }
        }
        
        try:
            async with session.post(f"{API_BASE_URL}/assessments", json=assessment_data, headers=headers) as response:
                if response.status == 201:
                    assessment = await response.json()
                    assessment_id = assessment["id"]
                    print(f"✅ Assessment created: {assessment_id}")
                else:
                    text = await response.text()
                    print(f"❌ Failed to create assessment: {response.status} - {text}")
                    return
        except Exception as e:
            print(f"❌ Assessment creation error: {e}")
            return

        # Step 3: Test assessments endpoint
        print(f"\n🔍 Step 3: Testing assessments endpoint...")
        try:
            async with session.get(f"{API_BASE_URL}/assessments", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    assessments = data.get("assessments", [])
                    print(f"✅ Found {len(assessments)} assessments")
                    if assessments:
                        print(f"   First assessment: {assessments[0]['title']}")
                else:
                    print(f"❌ Assessments fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Assessments fetch error: {e}")

        # Step 4: Test recommendations endpoint
        print(f"\n🔍 Step 4: Testing recommendations endpoint...")
        try:
            async with session.get(f"{API_BASE_URL}/recommendations/{assessment_id}", headers=headers) as response:
                print(f"📊 Recommendations status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    recommendations = data.get("recommendations", [])
                    print(f"✅ Found {len(recommendations)} recommendations")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:200]}...")
        except Exception as e:
            print(f"❌ Recommendations fetch error: {e}")

        # Step 5: Test visualization data endpoint
        print(f"\n🔍 Step 5: Testing visualization data endpoint...")
        try:
            async with session.get(f"{API_BASE_URL}/assessments/{assessment_id}/visualization-data", headers=headers) as response:
                print(f"📊 Visualization data status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Visualization data available")
                    if 'data' in data and 'assessment_results' in data['data']:
                        results = data['data']['assessment_results']
                        print(f"   Assessment results count: {len(results)}")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:200]}...")
        except Exception as e:
            print(f"❌ Visualization data fetch error: {e}")

        # Step 6: Generate recommendations
        print(f"\n🔍 Step 6: Generating recommendations...")
        try:
            async with session.post(f"{API_BASE_URL}/recommendations/{assessment_id}/generate", headers=headers) as response:
                print(f"🔄 Generate recommendations status: {response.status}")
                if response.status == 202:
                    data = await response.json()
                    workflow_id = data.get("workflow_id")
                    print(f"✅ Recommendations generation started: {workflow_id}")
                    
                    # Wait a bit and check again
                    await asyncio.sleep(2)
                    async with session.get(f"{API_BASE_URL}/recommendations/{assessment_id}", headers=headers) as check_response:
                        if check_response.status == 200:
                            check_data = await check_response.json()
                            recommendations = check_data.get("recommendations", [])
                            print(f"📊 Recommendations after generation: {len(recommendations)}")
                else:
                    text = await response.text()
                    print(f"   Response: {text[:200]}...")
        except Exception as e:
            print(f"❌ Generate recommendations error: {e}")

        print(f"\n🎯 Dashboard data test completed!")

if __name__ == "__main__":
    print("🚀 Testing Dashboard Data APIs")
    print("=" * 60)
    asyncio.run(test_dashboard_data())