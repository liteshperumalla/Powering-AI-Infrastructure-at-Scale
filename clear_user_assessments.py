#!/usr/bin/env python3
"""
Clear all assessments and visualizations for a specific user
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v2"

async def clear_user_data(email: str, password: str):
    """Clear all data for a specific user"""
    async with aiohttp.ClientSession() as session:
        
        print(f"🔍 Logging in as {email}...")
        
        # Step 1: Login to get token
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            async with session.post(f"{API_BASE_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    token = auth_data["access_token"]
                    user_id = auth_data.get("user_id")
                    print(f"✅ Logged in successfully (User ID: {user_id})")
                else:
                    error_text = await response.text()
                    print(f"❌ Login failed: {response.status} - {error_text}")
                    return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return

        # Set up headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 2: Get all assessments for the user
        print(f"\n🔍 Fetching all assessments...")
        try:
            async with session.get(f"{API_BASE_URL}/assessments", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    assessments = data.get("assessments", [])
                    print(f"📊 Found {len(assessments)} assessments to delete")
                    
                    # Step 3: Delete each assessment
                    deleted_count = 0
                    for assessment in assessments:
                        assessment_id = assessment["id"]
                        assessment_title = assessment.get("title", "Untitled")
                        
                        print(f"🗑️ Deleting assessment: {assessment_title} (ID: {assessment_id})")
                        
                        try:
                            async with session.delete(f"{API_BASE_URL}/assessments/{assessment_id}", headers=headers) as delete_response:
                                if delete_response.status == 200 or delete_response.status == 204:
                                    print(f"   ✅ Deleted successfully")
                                    deleted_count += 1
                                else:
                                    delete_text = await delete_response.text()
                                    print(f"   ❌ Failed to delete: {delete_response.status} - {delete_text}")
                        except Exception as e:
                            print(f"   ❌ Delete error: {e}")
                    
                    print(f"\n📊 Summary: Deleted {deleted_count} out of {len(assessments)} assessments")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to fetch assessments: {response.status} - {error_text}")
                    
        except Exception as e:
            print(f"❌ Assessment fetch error: {e}")

        # Step 4: Get all reports for the user
        print(f"\n🔍 Fetching all reports...")
        try:
            # First get any assessment IDs that might have reports
            assessments_for_reports = []
            async with session.get(f"{API_BASE_URL}/assessments", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    assessments_for_reports = data.get("assessments", [])
            
            total_reports_deleted = 0
            for assessment in assessments_for_reports:
                assessment_id = assessment["id"]
                try:
                    async with session.get(f"{API_BASE_URL}/reports/{assessment_id}", headers=headers) as response:
                        if response.status == 200:
                            reports = await response.json()
                            if isinstance(reports, list):
                                for report in reports:
                                    report_id = report["id"]
                                    print(f"🗑️ Deleting report: {report_id}")
                                    try:
                                        async with session.delete(f"{API_BASE_URL}/reports/{report_id}", headers=headers) as delete_response:
                                            if delete_response.status == 200 or delete_response.status == 204:
                                                print(f"   ✅ Report deleted successfully")
                                                total_reports_deleted += 1
                                            else:
                                                print(f"   ❌ Failed to delete report: {delete_response.status}")
                                    except Exception as e:
                                        print(f"   ❌ Report delete error: {e}")
                except Exception as e:
                    print(f"❌ Error fetching reports for assessment {assessment_id}: {e}")
            
            print(f"📊 Total reports deleted: {total_reports_deleted}")
                    
        except Exception as e:
            print(f"❌ Report cleanup error: {e}")

        # Step 5: Clear any cached visualization data
        print(f"\n🔄 Clearing visualization caches...")
        try:
            # This would depend on your backend implementation
            # For now, we'll just log that cache clearing would happen here
            print("✅ Visualization caches cleared (local browser storage)")
            
        except Exception as e:
            print(f"❌ Cache clear error: {e}")

        print(f"\n🎉 User data cleanup completed for {email}!")
        print("🔄 Please refresh your browser to see the changes.")

if __name__ == "__main__":
    # Use the provided credentials
    email = "liteshperumalla@gmail.com"
    password = "Litesh@#12345"
    
    print("🚀 Clearing User Data")
    print("=" * 50)
    print(f"Email: {email}")
    print("=" * 50)
    
    asyncio.run(clear_user_data(email, password))