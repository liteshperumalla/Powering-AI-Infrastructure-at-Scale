#!/usr/bin/env python3
"""
Debug assessment workflow script to identify and fix failed assessment issues.
This script connects to the MongoDB database and investigates the failed assessment.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

# MongoDB connection details from docker-compose.dev.yml
MONGODB_URL = "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"

async def debug_assessment_workflow():
    """Debug the failed assessment workflow and identify issues."""
    
    print("🔍 Debugging Assessment Workflow...")
    print("=" * 50)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Find the failed assessment
        failed_assessment = await db.assessments.find_one({"status": "failed"})
        
        if not failed_assessment:
            print("❌ No failed assessments found")
            return
        
        assessment_id = failed_assessment["_id"]
        print(f"📋 Failed Assessment ID: {assessment_id}")
        print(f"📝 Title: {failed_assessment.get('title', 'No title')}")
        print(f"📅 Created: {failed_assessment.get('created_at', 'Unknown')}")
        print(f"📅 Updated: {failed_assessment.get('updated_at', 'Unknown')}")
        print(f"🔄 Completion: {failed_assessment.get('completion_percentage', 0)}%")
        
        # Check for any workflow-related fields
        workflow_fields = ['workflow_id', 'current_phase', 'phase_errors', 'agent_results', 'error_info']
        print("\n🔧 Workflow Status Fields:")
        for field in workflow_fields:
            value = failed_assessment.get(field)
            print(f"  {field}: {value if value else 'Not set'}")
        
        # Check for related records in other collections
        print(f"\n🔍 Checking related records for assessment {assessment_id}...")
        
        # Check recommendations
        recommendations_count = await db.recommendations.count_documents({"assessment_id": str(assessment_id)})
        print(f"📊 Recommendations: {recommendations_count}")
        
        # Check reports
        reports_count = await db.reports.count_documents({"assessment_id": str(assessment_id)})
        print(f"📄 Reports: {reports_count}")
        
        # Check workflow progress (if there's a workflow collection)
        try:
            workflow_count = await db.workflows.count_documents({"assessment_id": str(assessment_id)})
            print(f"⚙️ Workflows: {workflow_count}")
        except Exception as e:
            print(f"⚙️ Workflows collection not found or error: {e}")
        
        # Check for any error logs or audit entries related to this assessment
        try:
            audit_logs = await db.audit_logs.find({
                "$or": [
                    {"resource_id": str(assessment_id)},
                    {"details.assessment_id": str(assessment_id)}
                ]
            }).limit(5).to_list(length=5)
            print(f"📋 Related audit logs: {len(audit_logs)}")
            for log in audit_logs:
                print(f"  - {log.get('timestamp', 'Unknown time')}: {log.get('action', 'Unknown action')} - {log.get('outcome', 'Unknown outcome')}")
        except Exception as e:
            print(f"📋 Audit logs not found or error: {e}")
        
        # Analyze the assessment structure to identify potential issues
        print(f"\n🔬 Analyzing Assessment Structure...")
        
        # Check required fields
        required_fields = ['business_requirements', 'technical_requirements', 'user_id']
        missing_fields = []
        for field in required_fields:
            if field not in failed_assessment or not failed_assessment[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        else:
            print("✅ All required fields present")
        
        # Check business requirements structure
        if 'business_requirements' in failed_assessment:
            br = failed_assessment['business_requirements']
            print(f"🏢 Business Requirements:")
            print(f"  - Company size: {br.get('company_size', 'Not set')}")
            print(f"  - Industry: {br.get('industry', 'Not set')}")
            print(f"  - Business goals: {len(br.get('business_goals', []))} goals")
            print(f"  - Team structure: {'Present' if br.get('team_structure') else 'Missing'}")
        
        # Check technical requirements structure
        if 'technical_requirements' in failed_assessment:
            tr = failed_assessment['technical_requirements']
            print(f"🔧 Technical Requirements:")
            print(f"  - Workload types: {len(tr.get('workload_types', []))} types")
            print(f"  - Performance requirements: {'Present' if tr.get('performance_requirements') else 'Missing'}")
            print(f"  - Security requirements: {'Present' if tr.get('security_requirements') else 'Missing'}")
        
        # Propose solutions
        print(f"\n💡 Proposed Solutions:")
        print("1. The assessment failed without specific error details stored")
        print("2. This suggests the failure occurred early in the workflow process")
        print("3. Possible causes:")
        print("   - Missing environment variables (AI API keys)")
        print("   - Database connection issues during workflow execution") 
        print("   - Workflow orchestration service not properly configured")
        print("   - AI agent execution timeouts or failures")
        
        # Attempt to restart the assessment
        print(f"\n🔄 Attempting to restart assessment workflow...")
        
        # Reset the assessment status to pending
        result = await db.assessments.update_one(
            {"_id": assessment_id},
            {
                "$set": {
                    "status": "pending",
                    "completion_percentage": 0,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "error_info": "",
                    "phase_errors": ""
                }
            }
        )
        
        if result.modified_count > 0:
            print("✅ Assessment status reset to pending")
            print("ℹ️  The assessment can now be restarted via the API")
            print(f"🚀 To restart: POST /api/v2/assessments/{assessment_id}/start")
        else:
            print("❌ Failed to reset assessment status")
        
        print(f"\n🏁 Diagnosis Complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_assessment_workflow())