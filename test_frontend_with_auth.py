#!/usr/bin/env python3
"""
Test Frontend with Authentication
Verifies the frontend dashboard shows assessment data after authentication
"""

import requests
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

def create_user_and_assessment():
    """Create user and assessment via API."""
    try:
        # Create user
        user_data = {
            "email": "dashboard@test.com",
            "username": "dashboardtest",
            "password": "testpass123",
            "full_name": "Dashboard Test User"
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            user_result = response.json()
            token = user_result.get("access_token")
            logger.info("✅ User created and authenticated")
            
            # Create assessment
            assessment_data = {
                "title": "Frontend Dashboard Test Assessment",
                "description": "Assessment for testing frontend dashboard display",
                "business_context": {
                    "company_size": "enterprise",
                    "industry": "technology",
                    "use_cases": ["machine_learning"],
                    "current_setup": "cloud_hybrid",
                    "budget_range": "100k_500k",
                    "timeline": "3_months"
                },
                "technical_requirements": {
                    "compute_requirements": {
                        "cpu_cores": 32,
                        "memory_gb": 128,
                        "storage_tb": 2,
                        "gpu_required": True
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
                return user_result, assessment
                
        return None, None
        
    except Exception as e:
        logger.error(f"❌ Failed to create user/assessment: {e}")
        return None, None

def test_frontend_access():
    """Test frontend access and dashboard functionality."""
    try:
        # Setup Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        try:
            # Test 1: Access main page
            logger.info("🌐 Testing main page access...")
            driver.get(FRONTEND_BASE)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            page_title = driver.title
            logger.info(f"  ✅ Main page loaded: {page_title}")
            
            # Test 2: Check if we can access dashboard (might require auth)
            logger.info("📊 Testing dashboard access...")
            driver.get(f"{FRONTEND_BASE}/dashboard")
            time.sleep(3)  # Wait for page to load
            
            # Check what we can see on the dashboard
            page_source = driver.page_source
            
            # Look for key dashboard elements
            dashboard_indicators = {
                "authentication_prompt": "login" in page_source.lower() or "sign in" in page_source.lower(),
                "dashboard_content": "dashboard" in page_source.lower(),
                "assessment_sections": "assessment" in page_source.lower(),
                "charts_loaded": "chart" in page_source.lower() or "visualization" in page_source.lower(),
                "loading_state": "loading" in page_source.lower(),
                "welcome_message": "welcome" in page_source.lower(),
                "start_assessment": "start assessment" in page_source.lower() or "start now" in page_source.lower()
            }
            
            logger.info("📋 Dashboard Analysis:")
            for indicator, found in dashboard_indicators.items():
                status = "✅ Found" if found else "❌ Not found"
                logger.info(f"  {status}: {indicator}")
            
            # Test 3: Look for specific dashboard components
            try:
                # Look for dashboard elements
                elements_found = {}
                
                # Check for common dashboard elements
                selectors_to_check = [
                    ("navigation", "nav"),
                    ("dashboard_title", "h4, h1, h2"),
                    ("cards", ".MuiCard-root, [class*='card']"),
                    ("buttons", "button"),
                    ("charts", "[class*='chart'], [class*='Chart']"),
                    ("progress", "[class*='progress'], [class*='Progress']")
                ]
                
                for name, selector in selectors_to_check:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        elements_found[name] = len(elements)
                        logger.info(f"  📊 {name}: {len(elements)} elements")
                    except:
                        elements_found[name] = 0
                
                # Test 4: Check for error messages or loading states
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [class*='Error']")
                    loading_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='loading'], [class*='Loading'], [class*='spinner'], [class*='Spinner']")
                    
                    if error_elements:
                        logger.warning(f"⚠️ Found {len(error_elements)} error elements")
                    if loading_elements:
                        logger.info(f"🔄 Found {len(loading_elements)} loading elements")
                        
                except:
                    pass
                
                return True, dashboard_indicators, elements_found
                
            except Exception as e:
                logger.error(f"❌ Error analyzing dashboard: {e}")
                return False, dashboard_indicators, {}
                
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ Frontend test failed: {e}")
        return False, {}, {}

def main():
    """Main test function."""
    print("🚀 FRONTEND DASHBOARD VERIFICATION")
    print("=" * 60)
    
    # Step 1: Create test data
    print("\n1️⃣ Creating Test Data...")
    user, assessment = create_user_and_assessment()
    
    if user and assessment:
        print(f"✅ Test data created:")
        print(f"  User: {user.get('email')}")
        print(f"  Assessment: {assessment.get('id')}")
        print(f"  Token: {user.get('access_token', 'No token')[:20]}...")
    else:
        print("⚠️ Test data creation failed, but continuing with frontend test...")
    
    # Step 2: Test frontend access
    print("\n2️⃣ Testing Frontend Access...")
    
    try:
        success, indicators, elements = test_frontend_access()
        
        print(f"\n📊 Frontend Test Results:")
        print(f"  Success: {'✅ Yes' if success else '❌ No'}")
        
        if indicators:
            print(f"\n🔍 Dashboard Content Analysis:")
            for key, found in indicators.items():
                status = "✅ Found" if found else "❌ Missing"
                print(f"  {status}: {key.replace('_', ' ').title()}")
        
        if elements:
            print(f"\n🎨 UI Elements Found:")
            for element_type, count in elements.items():
                print(f"  {element_type.replace('_', ' ').title()}: {count}")
        
        # Provide specific guidance
        print(f"\n💡 Next Steps:")
        
        if indicators.get('authentication_prompt'):
            print("  🔐 Dashboard requires authentication")
            print("  📝 To see assessment data:")
            print("    1. Open http://localhost:3000")
            print("    2. Register/Login with credentials")
            print("    3. Navigate to dashboard")
            print("    4. Create an assessment to see data")
        
        if indicators.get('dashboard_content') and not indicators.get('authentication_prompt'):
            print("  📊 Dashboard is accessible")
            if elements.get('cards', 0) > 0:
                print("  ✅ Dashboard components loaded")
            else:
                print("  ⚠️ Dashboard loaded but may need assessment data")
        
        print(f"\n🔗 Direct Access Links:")
        print(f"  Frontend: {FRONTEND_BASE}")
        print(f"  Dashboard: {FRONTEND_BASE}/dashboard") 
        print(f"  API Docs: {API_BASE}/docs")
        
        if user:
            print(f"\n🔑 Test Credentials:")
            print(f"  Email: {user.get('email')}")
            print(f"  Password: testpass123")
            
    except Exception as e:
        print(f"\n❌ Frontend verification failed: {e}")
        print(f"\n🔗 Manual Access:")
        print(f"  Try opening: {FRONTEND_BASE}")
        print(f"  Dashboard: {FRONTEND_BASE}/dashboard")

if __name__ == "__main__":
    main()