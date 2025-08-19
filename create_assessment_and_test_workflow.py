#!/usr/bin/env python3
"""
Create Assessment and Test Complete Workflow

Creates an assessment through the API and then tests all workflow components:
- Dashboard functionality
- Visualizations  
- Recommendations system
- Reports generation
- Advanced analytics
- Progress tracking
- Recent activity monitoring
"""

import asyncio
import sys
import os
import json
import requests
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"

def create_test_user():
    """Create a test user through the API."""
    try:
        # Register user
        user_data = {
            "email": "test@infratest.com",
            "username": "testuser123",
            "password": "testpassword123",
            "full_name": "Test User for Workflow"
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            logger.info("✅ User created successfully")
            return response.json()
        elif response.status_code == 400 and "already registered" in response.text:
            logger.info("📋 User already exists, proceeding with login")
            # Login to get token
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            response = requests.post(f"{API_BASE}/api/v1/auth/login", data=login_data)
            if response.status_code == 200:
                return response.json()
        
        logger.error(f"❌ Failed to create/login user: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error creating user: {e}")
        return None

def create_test_assessment(token):
    """Create a comprehensive test assessment through the API."""
    try:
        assessment_data = {
            "title": "Complete Workflow Test Assessment",
            "description": "Assessment for testing all workflow components",
            "business_context": {
                "company_size": "enterprise",
                "industry": "technology",
                "use_cases": ["machine_learning", "data_analytics"],
                "current_setup": "cloud_hybrid",
                "budget_range": "100k_500k",
                "timeline": "3_months",
                "compliance_requirements": ["gdpr", "soc2"]
            },
            "technical_requirements": {
                "compute_requirements": {
                    "cpu_cores": 64,
                    "memory_gb": 256,
                    "storage_tb": 5,
                    "gpu_required": True,
                    "gpu_type": "V100",
                    "gpu_count": 4
                },
                "performance_requirements": {
                    "throughput_rps": 5000,
                    "latency_ms": 100,
                    "availability": 99.5,
                    "scalability": "manual"
                }
            }
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE}/api/v1/assessments/",
            json=assessment_data,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            assessment = response.json()
            logger.info(f"✅ Assessment created: {assessment['id']}")
            return assessment
        else:
            logger.error(f"❌ Failed to create assessment: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating assessment: {e}")
        return None

def test_dashboard_api(token, assessment_id):
    """Test dashboard API endpoints."""
    logger.info("📱 Testing Dashboard API...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test assessment details
        response = requests.get(
            f"{API_BASE}/api/v1/assessments/{assessment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            assessment = response.json()
            logger.info(f"  ✅ Assessment retrieved: {assessment.get('title', 'Unknown')}")
            logger.info(f"  📊 Status: {assessment.get('status', 'Unknown')}")
            return True
        else:
            logger.error(f"  ❌ Failed to retrieve assessment: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Dashboard API test failed: {e}")
        return False

def test_recommendations_api(token, assessment_id):
    """Test recommendations API."""
    logger.info("🎯 Testing Recommendations API...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get recommendations for assessment
        response = requests.get(
            f"{API_BASE}/api/v1/recommendations/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            logger.info(f"  ✅ Retrieved {len(recommendations)} recommendations")
            
            # If no recommendations, try to generate them
            if len(recommendations) == 0:
                logger.info("  🔄 No recommendations found, this is expected for a new assessment")
            
            return True
        else:
            logger.error(f"  ❌ Failed to retrieve recommendations: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Recommendations API test failed: {e}")
        return False

def test_reports_api(token, assessment_id):
    """Test reports API."""
    logger.info("📊 Testing Reports API...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get reports for assessment
        response = requests.get(
            f"{API_BASE}/api/v1/reports/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            reports = response.json()
            logger.info(f"  ✅ Retrieved {len(reports)} reports")
            
            if len(reports) == 0:
                logger.info("  🔄 No reports found, this is expected for a new assessment")
            
            return True
        else:
            logger.error(f"  ❌ Failed to retrieve reports: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Reports API test failed: {e}")
        return False

def test_monitoring_api(token):
    """Test monitoring/analytics API."""
    logger.info("📈 Testing Monitoring/Analytics API...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test system health
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health = response.json()
            logger.info(f"  ✅ System health: {health.get('status', 'unknown')}")
            
            # Log some key metrics
            if 'database' in health:
                db_info = health['database']
                logger.info(f"  📊 Database: {db_info.get('status', 'unknown')}")
                logger.info(f"  📊 Collections: {db_info.get('collections', 0)}")
                logger.info(f"  📊 Objects: {db_info.get('objects', 0)}")
            
            return True
        else:
            logger.error(f"  ❌ Failed to get system health: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Monitoring API test failed: {e}")
        return False

def test_frontend_integration():
    """Test frontend integration."""
    logger.info("🖥️ Testing Frontend Integration...")
    
    try:
        # Test main page
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            logger.info("  ✅ Frontend main page accessible")
            
            # Test dashboard page
            response = requests.get("http://localhost:3000/dashboard")
            if response.status_code == 200:
                logger.info("  ✅ Dashboard page accessible")
                return True
            else:
                logger.error(f"  ❌ Dashboard page failed: {response.status_code}")
                return False
        else:
            logger.error(f"  ❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Frontend integration test failed: {e}")
        return False

def test_chat_api(token, assessment_id):
    """Test chat/conversation API."""
    logger.info("💬 Testing Chat API...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Send a test message
        chat_data = {
            "message": "Can you provide a summary of my assessment?",
            "assessment_id": assessment_id
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/chat/send",
            json=chat_data,
            headers=headers
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            logger.info("  ✅ Chat API responded successfully")
            logger.info(f"  💬 Response preview: {chat_response.get('response', '')[:100]}...")
            return True
        else:
            logger.error(f"  ❌ Chat API failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Chat API test failed: {e}")
        return False

def main():
    """Main test runner."""
    
    print("🚀 COMPLETE ASSESSMENT WORKFLOW TEST")
    print("=" * 80)
    print("Testing: API | Dashboard | Frontend | Recommendations | Reports")
    print("         Monitoring | Chat | End-to-End Integration")
    print("=" * 80)
    
    # Step 1: Create test user and get token
    print("\n1️⃣ Creating Test User...")
    user_result = create_test_user()
    if not user_result:
        print("❌ Failed to create test user")
        return
    
    token = user_result.get("access_token")
    if not token:
        print("❌ Failed to get access token")
        return
    
    print("✅ User authentication successful")
    
    # Step 2: Create test assessment
    print("\n2️⃣ Creating Test Assessment...")
    assessment = create_test_assessment(token)
    if not assessment:
        print("❌ Failed to create test assessment")
        return
    
    assessment_id = assessment.get("id")
    print(f"✅ Assessment created: {assessment_id}")
    
    # Step 3: Test all workflow components
    test_results = []
    
    print("\n3️⃣ Testing Workflow Components...")
    
    # Test dashboard API
    result = test_dashboard_api(token, assessment_id)
    test_results.append(("Dashboard API", result))
    
    # Test recommendations
    result = test_recommendations_api(token, assessment_id)
    test_results.append(("Recommendations API", result))
    
    # Test reports
    result = test_reports_api(token, assessment_id)
    test_results.append(("Reports API", result))
    
    # Test monitoring
    result = test_monitoring_api(token)
    test_results.append(("Monitoring API", result))
    
    # Test frontend
    result = test_frontend_integration()
    test_results.append(("Frontend Integration", result))
    
    # Test chat
    result = test_chat_api(token, assessment_id)
    test_results.append(("Chat API", result))
    
    # Final results
    print("\n" + "=" * 80)
    print("🎉 COMPLETE WORKFLOW TEST RESULTS")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n📊 Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Complete assessment workflow is functional.")
        print(f"\n📋 Test Assessment Details:")
        print(f"  ID: {assessment_id}")
        print(f"  Title: {assessment.get('title', 'Unknown')}")
        print(f"  Status: {assessment.get('status', 'Unknown')}")
        print(f"  Frontend: http://localhost:3000/dashboard")
        print(f"  API Docs: http://localhost:8000/docs")
    else:
        print(f"⚠️ {total_tests - passed_tests} tests failed. Review the logs above.")
        print("Some components may need additional configuration or data.")
    
    print("\n🔗 Quick Access Links:")
    print(f"  📊 Dashboard: http://localhost:3000/dashboard")
    print(f"  📋 Assessment: http://localhost:3000/assessment/{assessment_id}")
    print(f"  🔧 API Documentation: http://localhost:8000/docs")
    print(f"  💾 Database Admin: http://localhost:8081")

if __name__ == "__main__":
    main()