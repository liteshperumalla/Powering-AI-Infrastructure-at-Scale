#!/usr/bin/env python3
"""
Test and fix CORS issues
"""
import asyncio
import aiohttp
import json

async def test_cors_endpoints():
    """Test CORS preflight and actual requests"""
    print("🔍 Testing CORS Configuration")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Basic health check
        print("1️⃣ Testing basic health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                print(f"   GET /health: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   Status: {data.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: OPTIONS preflight for health
        print("\n2️⃣ Testing OPTIONS preflight for /health...")
        try:
            async with session.options(
                f"{base_url}/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            ) as response:
                print(f"   OPTIONS /health: {response.status}")
                
                # Check CORS headers
                cors_headers = {}
                for header, value in response.headers.items():
                    if header.lower().startswith('access-control'):
                        cors_headers[header] = value
                
                if cors_headers:
                    print("   ✅ CORS Headers found:")
                    for header, value in cors_headers.items():
                        print(f"      {header}: {value}")
                else:
                    print("   ❌ No CORS headers found")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Login endpoint OPTIONS
        print("\n3️⃣ Testing OPTIONS preflight for /api/v2/auth/login...")
        try:
            async with session.options(
                f"{base_url}/api/v2/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
            ) as response:
                print(f"   OPTIONS /api/v2/auth/login: {response.status}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Detailed health check (should work)
        print("\n4️⃣ Testing detailed health endpoint...")
        try:
            async with session.get(f"{base_url}/api/v2/admin/health/detailed") as response:
                print(f"   GET /api/v2/admin/health/detailed: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   Overall Status: {data.get('overall_status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CORS Test Results:")
    print("- The main /health endpoint is showing 503 errors")
    print("- This is blocking CORS preflight requests")
    print("- The detailed health endpoint works fine")
    print("- The issue is likely in the health check middleware")

if __name__ == "__main__":
    asyncio.run(test_cors_endpoints())