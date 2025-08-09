#!/usr/bin/env python3
"""
Test authentication with the credentials we created
"""

import asyncio
import aiohttp
import json

async def test_authentication():
    """Test the authentication flow"""
    
    print("🔐 Testing Authentication Flow")
    print("=" * 50)
    
    # Test credentials
    email = "liteshperumalla@gmail.com"
    password = "Litesh@#12345"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Test login
            print("\n1️⃣ Testing login...")
            login_data = {
                "email": email,
                "password": password
            }
            
            async with session.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"Login response status: {response.status}")
                
                if response.status == 200:
                    login_result = await response.json()
                    print("✅ Login successful!")
                    print(f"Access token received: {login_result.get('access_token', 'N/A')[:20]}...")
                    print(f"User ID: {login_result.get('user_id')}")
                    print(f"Email: {login_result.get('email')}")
                    print(f"Full name: {login_result.get('full_name')}")
                    
                    access_token = login_result.get('access_token')
                    
                    # Step 2: Test profile endpoint
                    print("\n2️⃣ Testing profile endpoint...")
                    async with session.get(
                        "http://localhost:8000/api/v1/auth/profile",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as profile_response:
                        
                        print(f"Profile response status: {profile_response.status}")
                        
                        if profile_response.status == 200:
                            profile_data = await profile_response.json()
                            print("✅ Profile fetch successful!")
                            print(json.dumps(profile_data, indent=2))
                        else:
                            profile_error = await profile_response.text()
                            print(f"❌ Profile fetch failed: {profile_error}")
                    
                    # Step 3: Test token verification
                    print("\n3️⃣ Testing token verification...")
                    async with session.get(
                        "http://localhost:8000/api/v1/auth/verify-token",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as verify_response:
                        
                        print(f"Token verify response status: {verify_response.status}")
                        
                        if verify_response.status == 200:
                            verify_data = await verify_response.json()
                            print("✅ Token verification successful!")
                            print(json.dumps(verify_data, indent=2))
                        else:
                            verify_error = await verify_response.text()
                            print(f"❌ Token verification failed: {verify_error}")
                            
                    # Step 4: Test chat conversations API
                    print("\n4️⃣ Testing chat conversations API...")
                    async with session.get(
                        "http://localhost:8000/api/v1/chat/conversations",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as chat_response:
                        
                        print(f"Chat conversations response status: {chat_response.status}")
                        
                        if chat_response.status == 200:
                            chat_data = await chat_response.json()
                            print("✅ Chat API accessible!")
                            print(f"Conversations found: {len(chat_data.get('conversations', []))}")
                        else:
                            chat_error = await chat_response.text()
                            print(f"❌ Chat API error: {chat_error}")
                    
                else:
                    login_error = await response.text()
                    print(f"❌ Login failed: {login_error}")
                    
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")

async def main():
    await test_authentication()

if __name__ == "__main__":
    asyncio.run(main())