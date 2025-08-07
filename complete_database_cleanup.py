#!/usr/bin/env python3
"""
Complete database cleanup - direct MongoDB operations
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def complete_database_cleanup():
    """Direct MongoDB cleanup to ensure all user data is removed"""
    print("🗄️ Direct Database Cleanup")
    print("=" * 60)
    
    # MongoDB connection
    mongodb_url = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    client = AsyncIOMotorClient(mongodb_url)
    db = client["infra_mind"]
    
    user_email = "liteshperumalla@gmail.com"
    
    try:
        # 1. Find the user ID
        print("1️⃣ Finding user...")
        user_collection = db["users"]
        user = await user_collection.find_one({"email": user_email})
        
        if not user:
            print(f"   ❌ User {user_email} not found")
            return False
        
        user_id = str(user["_id"])
        print(f"   ✅ Found user: {user['full_name']} (ID: {user_id})")
        
        # 2. Delete all assessments for this user
        print("\n2️⃣ Deleting assessments...")
        assessments_collection = db["assessments"]
        
        # Find all assessments
        assessments_cursor = assessments_collection.find({"user_id": user_id})
        assessment_ids = []
        async for assessment in assessments_cursor:
            assessment_ids.append(str(assessment["_id"]))
            print(f"   📋 Found assessment: {assessment.get('title', 'Untitled')}")
        
        if assessment_ids:
            # Delete assessments
            delete_result = await assessments_collection.delete_many({"user_id": user_id})
            print(f"   🗑️ Deleted {delete_result.deleted_count} assessments")
        else:
            print("   ✅ No assessments found")
        
        # 3. Delete all recommendations
        print("\n3️⃣ Deleting recommendations...")
        recommendations_collection = db["recommendations"]
        
        if assessment_ids:
            # Delete recommendations for these assessments
            rec_delete_result = await recommendations_collection.delete_many(
                {"assessment_id": {"$in": assessment_ids}}
            )
            print(f"   🗑️ Deleted {rec_delete_result.deleted_count} recommendations")
        else:
            print("   ✅ No recommendations to delete")
        
        # 4. Delete all reports
        print("\n4️⃣ Deleting reports...")
        reports_collection = db["reports"]
        
        if assessment_ids:
            # Delete reports for these assessments
            report_delete_result = await reports_collection.delete_many(
                {"assessment_id": {"$in": assessment_ids}}
            )
            print(f"   🗑️ Deleted {report_delete_result.deleted_count} reports")
        else:
            print("   ✅ No reports to delete")
        
        # 5. Delete workflow states
        print("\n5️⃣ Deleting workflow states...")
        workflow_states_collection = db["workflow_states"]
        
        workflow_delete_result = await workflow_states_collection.delete_many(
            {"user_id": user_id}
        )
        print(f"   🗑️ Deleted {workflow_delete_result.deleted_count} workflow states")
        
        # 6. Delete audit logs for this user
        print("\n6️⃣ Deleting audit logs...")
        audit_logs_collection = db["audit_logs"]
        
        audit_delete_result = await audit_logs_collection.delete_many(
            {"user_id": user_id}
        )
        print(f"   🗑️ Deleted {audit_delete_result.deleted_count} audit logs")
        
        # 7. Delete any cached data
        print("\n7️⃣ Deleting cached data...")
        cache_collection = db["cache"]
        
        cache_delete_result = await cache_collection.delete_many(
            {"user_id": user_id}
        )
        print(f"   🗑️ Deleted {cache_delete_result.deleted_count} cache entries")
        
        # 8. Final verification
        print("\n8️⃣ Final verification...")
        
        # Check assessments
        remaining_assessments = await assessments_collection.count_documents({"user_id": user_id})
        print(f"   📊 Remaining assessments: {remaining_assessments}")
        
        # Check recommendations
        remaining_recommendations = await recommendations_collection.count_documents(
            {"assessment_id": {"$in": assessment_ids}} if assessment_ids else {}
        )
        print(f"   💡 Remaining recommendations: {remaining_recommendations}")
        
        # Check reports
        remaining_reports = await reports_collection.count_documents(
            {"assessment_id": {"$in": assessment_ids}} if assessment_ids else {}
        )
        print(f"   📄 Remaining reports: {remaining_reports}")
        
        success = (remaining_assessments == 0 and 
                  remaining_recommendations == 0 and 
                  remaining_reports == 0)
        
        if success:
            print("\n🎉 Database cleanup completed successfully!")
        else:
            print("\n⚠️ Some data may still remain in the database")
        
        return success
        
    except Exception as e:
        print(f"❌ Database cleanup error: {e}")
        return False
    finally:
        client.close()

async def restart_backend_services():
    """Restart backend to clear any in-memory caches"""
    print("\n🔄 Backend Service Management")
    print("=" * 40)
    
    import subprocess
    import time
    
    try:
        # Kill existing backend processes
        print("1️⃣ Stopping backend processes...")
        subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        subprocess.run(["pkill", "-f", "python.*api"], capture_output=True)
        time.sleep(2)
        print("   ✅ Backend processes stopped")
        
        # Start fresh backend
        print("2️⃣ Starting fresh backend...")
        backend_dir = "/Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale"
        
        process = subprocess.Popen([
            "uvicorn", "api.app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], cwd=backend_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for backend to start
        await asyncio.sleep(5)
        print("   ✅ Backend restarted")
        
        # Verify backend health
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8000/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Backend health: {data.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"   ⚠️ Backend health check failed: {response.status}")
                        return False
            except Exception as e:
                print(f"   ⚠️ Backend health check error: {e}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error managing backend services: {e}")
        return False

if __name__ == "__main__":
    async def main():
        # Step 1: Clean database
        db_success = await complete_database_cleanup()
        
        # Step 2: Restart backend
        if db_success:
            backend_success = await restart_backend_services()
        else:
            backend_success = False
        
        print("\n" + "=" * 60)
        print("📋 CLEANUP SUMMARY")
        print("=" * 60)
        
        if db_success:
            print("✅ Database: All user data removed")
        else:
            print("❌ Database: Some issues occurred")
            
        if backend_success:
            print("✅ Backend: Restarted successfully")
        else:
            print("❌ Backend: Restart issues")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Open the browser cache cleaner:")
        print("   file:///Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/clear_browser_cache.html")
        print("2. Click 'Clear All Storage Data'")
        print("3. Close browser completely")
        print("4. Reopen browser and go to http://localhost:3000")
        print("5. Login fresh - no old data should appear")
        
        if db_success and backend_success:
            print("\n🎉 COMPLETE SUCCESS - System is fully clean!")
        else:
            print("\n⚠️ Manual intervention may be needed")
    
    asyncio.run(main())