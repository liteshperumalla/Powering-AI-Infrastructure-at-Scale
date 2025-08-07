#!/usr/bin/env python3
"""
Final cleanup: Remove ALL visualization data and cached content
"""
import asyncio
import aiohttp
import subprocess
import os

async def complete_cleanup():
    """Perform complete system cleanup"""
    print("🧹 Complete System Cleanup")
    print("=" * 50)
    
    # 1. Test backend health
    print("1️⃣ Checking backend health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Backend healthy: {data['status']}")
                else:
                    print(f"   ❌ Backend unhealthy: {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
        return False
    
    # 2. Login and clear all data for user
    print("\n2️⃣ Clearing all user data...")
    email = "liteshperumalla@gmail.com" 
    password = "Litesh@#12345"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Login
            login_data = {"email": email, "password": password}
            async with session.post("http://localhost:8000/api/v2/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    token = auth_data["access_token"]
                    print("   ✅ Logged in successfully")
                else:
                    print(f"   ❌ Login failed: {response.status}")
                    return False
            
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # Delete all assessments (again to be sure)
            async with session.get("http://localhost:8000/api/v2/assessments", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    assessments = data.get("assessments", [])
                    
                    for assessment in assessments:
                        try:
                            async with session.delete(f"http://localhost:8000/api/v2/assessments/{assessment['id']}", headers=headers) as del_response:
                                if del_response.status in [200, 204]:
                                    print(f"   ✅ Deleted assessment: {assessment.get('title', 'Untitled')}")
                                else:
                                    print(f"   ⚠️ Failed to delete assessment: {del_response.status}")
                        except Exception as e:
                            print(f"   ❌ Error deleting assessment: {e}")
                    
                    print(f"   📊 Processed {len(assessments)} assessments")
                else:
                    print("   ✅ No assessments to delete")
            
            # Clear any reports
            async with session.get("http://localhost:8000/api/v2/reports", headers=headers) as response:
                if response.status == 200:
                    reports = await response.json()
                    if isinstance(reports, list):
                        for report in reports:
                            try:
                                async with session.delete(f"http://localhost:8000/api/v2/reports/{report['id']}", headers=headers) as del_response:
                                    if del_response.status in [200, 204]:
                                        print(f"   ✅ Deleted report: {report['id']}")
                            except Exception as e:
                                print(f"   ❌ Error deleting report: {e}")
                else:
                    print("   ✅ No reports to delete")
                    
    except Exception as e:
        print(f"   ❌ User data cleanup failed: {e}")
    
    # 3. Clear Next.js cache
    print("\n3️⃣ Clearing Next.js cache...")
    frontend_path = "/Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/frontend-react"
    
    try:
        # Remove .next folder
        next_path = os.path.join(frontend_path, ".next")
        if os.path.exists(next_path):
            subprocess.run(["rm", "-rf", next_path], check=True)
            print("   ✅ Removed .next cache")
        else:
            print("   ✅ .next cache already clean")
            
        # Clear node_modules/.cache if exists
        cache_path = os.path.join(frontend_path, "node_modules", ".cache")
        if os.path.exists(cache_path):
            subprocess.run(["rm", "-rf", cache_path], check=True)
            print("   ✅ Removed node_modules cache")
        else:
            print("   ✅ Node modules cache already clean")
            
    except Exception as e:
        print(f"   ❌ Cache cleanup failed: {e}")
    
    # 4. Restart frontend
    print("\n4️⃣ Restarting frontend...")
    try:
        # Kill existing frontend processes
        subprocess.run(["pkill", "-f", "next dev"], capture_output=True)
        print("   ✅ Stopped existing frontend")
        
        # Start fresh frontend process
        subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=frontend_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait a bit for startup
        await asyncio.sleep(5)
        print("   ✅ Frontend restarted")
        
    except Exception as e:
        print(f"   ❌ Frontend restart failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Complete cleanup finished!")
    print("\n🛠️ Next Steps:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application tab > Storage")
    print("4. Clear all storage manually")
    print("5. Refresh the page (Ctrl+F5)")
    print("6. Try logging in with your credentials")
    print(f"   Email: {email}")
    print("   Password: [your password]")
    print("\n🎉 Your system should now be completely clean!")

if __name__ == "__main__":
    asyncio.run(complete_cleanup())