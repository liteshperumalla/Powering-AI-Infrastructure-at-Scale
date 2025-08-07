#!/usr/bin/env python3
"""
Test API connection and basic functionality
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"

async def test_api():
    """Test basic API functionality"""
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['status']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return
        
        # Test API info endpoint
        print("\n🔍 Testing API info endpoint...")
        try:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API info: {data['message']}")
                    print(f"   Version: {data['version']}")
                    print(f"   Status: {data['status']}")
                else:
                    print(f"❌ API info failed: {response.status}")
        except Exception as e:
            print(f"❌ API info error: {e}")
        
        # Test assessments endpoint (should require auth)
        print("\n🔍 Testing assessments endpoint (without auth)...")
        try:
            async with session.get(f"{BASE_URL}/api/v2/assessments") as response:
                print(f"📊 Assessments endpoint status: {response.status}")
                if response.status == 401:
                    print("✅ Authentication required (expected)")
                elif response.status == 307:
                    print("🔄 Redirect response (may be normal)")
        except Exception as e:
            print(f"❌ Assessments test error: {e}")

        # Test registration endpoint
        print("\n🔍 Testing user registration...")
        try:
            registration_data = {
                "email": "testuser@example.com",
                "password": "TestPass123!",
                "full_name": "Test User",
                "company": "Test Company"
            }
            
            async with session.post(
                f"{BASE_URL}/api/v2/auth/register", 
                json=registration_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📝 Registration status: {response.status}")
                text = await response.text()
                print(f"   Response: {text[:200]}...")
                
        except Exception as e:
            print(f"❌ Registration test error: {e}")

if __name__ == "__main__":
    print("🚀 Testing API Connection")
    print("=" * 50)
    asyncio.run(test_api())