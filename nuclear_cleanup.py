#!/usr/bin/env python3
"""
Nuclear cleanup - remove ALL orphaned data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def nuclear_cleanup():
    """Remove ALL orphaned recommendations and reports"""
    print("☢️ Nuclear Database Cleanup")
    print("=" * 60)
    
    # MongoDB connection
    mongodb_url = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    client = AsyncIOMotorClient(mongodb_url)
    db = client["infra_mind"]
    
    try:
        # Get user info
        user_email = "liteshperumalla@gmail.com"
        user_collection = db["users"]
        user = await user_collection.find_one({"email": user_email})
        
        if not user:
            print(f"❌ User {user_email} not found")
            return
        
        user_id = str(user["_id"])
        print(f"👤 User: {user['full_name']} (ID: {user_id})")
        
        # Get all current assessment IDs (should be none)
        assessments_collection = db["assessments"]
        valid_assessment_ids = []
        async for assessment in assessments_collection.find({"user_id": user_id}):
            valid_assessment_ids.append(str(assessment["_id"]))
        
        print(f"📊 Valid assessments found: {len(valid_assessment_ids)}")
        
        # Delete ALL recommendations for this user (regardless of assessment)
        print("\n1️⃣ Deleting ALL recommendations...")
        recommendations_collection = db["recommendations"]
        
        # First, find recommendations by user_id if that field exists
        user_recommendations = await recommendations_collection.count_documents({"user_id": user_id})
        if user_recommendations > 0:
            delete_result = await recommendations_collection.delete_many({"user_id": user_id})
            print(f"   🗑️ Deleted {delete_result.deleted_count} recommendations by user_id")
        
        # Also delete by assessment_id lookup
        if valid_assessment_ids:
            assess_recs_result = await recommendations_collection.delete_many(
                {"assessment_id": {"$in": valid_assessment_ids}}
            )
            print(f"   🗑️ Deleted {assess_recs_result.deleted_count} recommendations by assessment_id")
        
        # Nuclear option: find all recommendations that reference non-existent assessments
        print("\n2️⃣ Finding orphaned recommendations...")
        all_assessment_ids = []
        async for assessment in assessments_collection.find({}):
            all_assessment_ids.append(str(assessment["_id"]))
        
        orphaned_recs = 0
        async for rec in recommendations_collection.find({}):
            rec_assessment_id = rec.get("assessment_id")
            if rec_assessment_id and rec_assessment_id not in all_assessment_ids:
                await recommendations_collection.delete_one({"_id": rec["_id"]})
                orphaned_recs += 1
                print(f"   🗑️ Deleted orphaned recommendation for assessment: {rec_assessment_id}")
        
        print(f"   📊 Total orphaned recommendations deleted: {orphaned_recs}")
        
        # Delete ALL reports for this user
        print("\n3️⃣ Deleting ALL reports...")
        reports_collection = db["reports"]
        
        # Delete by user_id if field exists
        user_reports = await reports_collection.count_documents({"user_id": user_id})
        if user_reports > 0:
            delete_result = await reports_collection.delete_many({"user_id": user_id})
            print(f"   🗑️ Deleted {delete_result.deleted_count} reports by user_id")
        
        # Delete by assessment_id
        if valid_assessment_ids:
            assess_reports_result = await reports_collection.delete_many(
                {"assessment_id": {"$in": valid_assessment_ids}}
            )
            print(f"   🗑️ Deleted {assess_reports_result.deleted_count} reports by assessment_id")
        
        # Nuclear option: find orphaned reports
        orphaned_reports = 0
        async for report in reports_collection.find({}):
            report_assessment_id = report.get("assessment_id")
            if report_assessment_id and report_assessment_id not in all_assessment_ids:
                await reports_collection.delete_one({"_id": report["_id"]})
                orphaned_reports += 1
                print(f"   🗑️ Deleted orphaned report for assessment: {report_assessment_id}")
        
        print(f"   📊 Total orphaned reports deleted: {orphaned_reports}")
        
        # Clear any remaining user-specific data
        print("\n4️⃣ Clearing remaining user data...")
        
        collections_to_clean = [
            "workflow_states",
            "audit_logs", 
            "cache",
            "metrics",
            "conversations"
        ]
        
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            delete_result = await collection.delete_many({"user_id": user_id})
            if delete_result.deleted_count > 0:
                print(f"   🗑️ Deleted {delete_result.deleted_count} items from {collection_name}")
        
        # Final verification
        print("\n5️⃣ Final verification...")
        remaining_assessments = await assessments_collection.count_documents({"user_id": user_id})
        remaining_recommendations = await recommendations_collection.count_documents({})
        remaining_reports = await reports_collection.count_documents({})
        
        print(f"   📊 Remaining assessments: {remaining_assessments}")
        print(f"   💡 Total recommendations in DB: {remaining_recommendations}")
        print(f"   📄 Total reports in DB: {remaining_reports}")
        
        # Check specifically for user's data
        user_recs = await recommendations_collection.count_documents({"user_id": user_id})
        user_reports = await reports_collection.count_documents({"user_id": user_id})
        
        print(f"   🎯 User's recommendations: {user_recs}")
        print(f"   🎯 User's reports: {user_reports}")
        
        success = (remaining_assessments == 0 and user_recs == 0 and user_reports == 0)
        
        if success:
            print("\n🎉 NUCLEAR CLEANUP SUCCESSFUL!")
            print("✅ All user data completely removed from database")
        else:
            print("\n⚠️ Some data may still remain")
            
        return success
        
    except Exception as e:
        print(f"❌ Nuclear cleanup error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(nuclear_cleanup())
    
    print("\n" + "=" * 60)
    print("🎯 BROWSER CACHE CLEANUP INSTRUCTIONS")
    print("=" * 60)
    
    if success:
        print("✅ Database is now completely clean!")
    
    print("\n📋 TO COMPLETE THE CLEANUP:")
    print("1. Open this file in your browser:")
    print("   file:///Users/liteshperumalla/Desktop/Files/masters/AI Scaling Infrastrcture/Powering-AI-Infrastructure-at-Scale/clear_browser_cache.html")
    print("\n2. Or manually clear browser cache:")
    print("   - Press Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)")
    print("   - Select 'All time'")
    print("   - Check all boxes")
    print("   - Click 'Clear data'")
    print("\n3. Close browser completely and reopen")
    print("4. Go to http://localhost:3000")
    print("5. Login fresh - dashboard should be empty!")
    
    print(f"\n🏁 Nuclear cleanup: {'SUCCESS' if success else 'NEEDS REVIEW'}")