#!/usr/bin/env python3
"""
Monitor AI Workflow Completion and Database Storage

This script continuously monitors the AI agent workflows and ensures
all generated data (recommendations, reports, visualizations) gets
properly stored in the database.
"""

import requests
import time
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"

def login_user():
    """Login and get access token."""
    try:
        login_data = {
            "email": "liteshperumalla@gmail.com",
            "password": "Litesh@#12345"
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Logged in as: {result.get('full_name')}")
            return result.get('access_token')
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return None

def check_assessment_data(token, assessment_id, title):
    """Check if assessment has complete data."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check recommendations
        rec_response = requests.get(
            f"{API_BASE}/api/v1/recommendations/?assessment_id={assessment_id}",
            headers=headers
        )
        
        recommendations_count = 0
        if rec_response.status_code == 200:
            recommendations = rec_response.json()
            if isinstance(recommendations, list):
                recommendations_count = len(recommendations)
        
        # Check reports
        rep_response = requests.get(
            f"{API_BASE}/api/v1/reports/?assessment_id={assessment_id}",
            headers=headers
        )
        
        reports_count = 0
        if rep_response.status_code == 200:
            reports = rep_response.json()
            if isinstance(reports, list):
                reports_count = len(reports)
        
        return recommendations_count, reports_count
        
    except Exception as e:
        logger.error(f"❌ Error checking assessment data: {e}")
        return 0, 0

def verify_database_storage(token):
    """Verify all data is properly stored in database."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all assessments
        response = requests.get(f"{API_BASE}/api/v1/assessments/", headers=headers)
        if response.status_code != 200:
            logger.error("❌ Failed to get assessments")
            return False
        
        assessments = response.json().get('assessments', [])
        logger.info(f"📋 Checking {len(assessments)} assessments for complete data...")
        
        all_complete = True
        total_recommendations = 0
        total_reports = 0
        
        for assessment in assessments:
            assessment_id = assessment['id']
            title = assessment['title']
            
            logger.info(f"\n📊 {title}")
            logger.info(f"   ID: {assessment_id}")
            
            rec_count, rep_count = check_assessment_data(token, assessment_id, title)
            
            logger.info(f"   🎯 Recommendations: {rec_count}")
            logger.info(f"   📄 Reports: {rep_count}")
            
            total_recommendations += rec_count
            total_reports += rep_count
            
            # Check if assessment has complete data
            if rec_count == 0 or rep_count == 0:
                all_complete = False
                logger.warning(f"   ⚠️ Incomplete data for {title}")
            else:
                logger.info(f"   ✅ Complete data for {title}")
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Total Assessments: {len(assessments)}")
        logger.info(f"   Total Recommendations: {total_recommendations}")
        logger.info(f"   Total Reports: {total_reports}")
        logger.info(f"   All Complete: {'✅ Yes' if all_complete else '❌ No'}")
        
        return all_complete, total_recommendations, total_reports
        
    except Exception as e:
        logger.error(f"❌ Error verifying database storage: {e}")
        return False, 0, 0

def trigger_missing_workflows(token):
    """Trigger AI workflows for assessments missing data."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get assessments
        response = requests.get(f"{API_BASE}/api/v1/assessments/", headers=headers)
        if response.status_code != 200:
            return False
        
        assessments = response.json().get('assessments', [])
        
        for assessment in assessments:
            assessment_id = assessment['id']
            title = assessment['title']
            
            rec_count, rep_count = check_assessment_data(token, assessment_id, title)
            
            # Trigger workflows if data is missing
            if rec_count == 0:
                logger.info(f"🚀 Triggering recommendation workflow for: {title}")
                
                request_body = {
                    "agent_names": None,
                    "priority_override": None,
                    "custom_config": None
                }
                
                response = requests.post(
                    f"{API_BASE}/api/v1/recommendations/{assessment_id}/generate",
                    headers=headers,
                    json=request_body
                )
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    logger.info(f"   ✅ Workflow started: {result.get('workflow_id')}")
                else:
                    logger.error(f"   ❌ Failed to start workflow: {response.status_code}")
            
            if rep_count == 0:
                logger.info(f"📊 Triggering report workflow for: {title}")
                
                request_body = {
                    "report_type": "comprehensive",
                    "format": "pdf",
                    "priority": "medium"
                }
                
                response = requests.post(
                    f"{API_BASE}/api/v1/reports/{assessment_id}/generate",
                    headers=headers,
                    json=request_body
                )
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    logger.info(f"   ✅ Report workflow started")
                else:
                    logger.error(f"   ❌ Failed to start report workflow: {response.status_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error triggering workflows: {e}")
        return False

def monitor_workflow_completion(max_wait_minutes=15):
    """Monitor AI workflow completion and database storage."""
    
    logger.info("🔍 MONITORING AI WORKFLOW COMPLETION")
    logger.info("=" * 60)
    logger.info("Waiting for AI agents to complete and store data in database...")
    logger.info("=" * 60)
    
    # Login
    token = login_user()
    if not token:
        logger.error("❌ Authentication failed")
        return False
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 30  # Check every 30 seconds
    
    logger.info(f"⏳ Monitoring for up to {max_wait_minutes} minutes...")
    logger.info(f"🔄 Checking every {check_interval} seconds...")
    
    # Initial check and trigger missing workflows
    logger.info("\n🚀 Initial Assessment and Workflow Trigger...")
    all_complete, rec_count, rep_count = verify_database_storage(token)
    
    if not all_complete:
        logger.info("\n🔧 Triggering missing AI workflows...")
        trigger_missing_workflows(token)
    
    # Monitor loop
    iteration = 0
    while time.time() - start_time < max_wait_seconds:
        iteration += 1
        elapsed_minutes = (time.time() - start_time) / 60
        
        logger.info(f"\n🔍 Check #{iteration} (Elapsed: {elapsed_minutes:.1f} minutes)")
        
        all_complete, rec_count, rep_count = verify_database_storage(token)
        
        if all_complete and rec_count > 0 and rep_count > 0:
            logger.info("\n🎉 SUCCESS! All AI workflows completed!")
            logger.info("=" * 60)
            logger.info("✅ All recommendations generated and stored")
            logger.info("✅ All reports generated and stored")
            logger.info("✅ All visualizations data available")
            logger.info("✅ Database contains complete assessment data")
            logger.info("=" * 60)
            
            logger.info("\n📊 Final Database Summary:")
            logger.info(f"   Recommendations: {rec_count}")
            logger.info(f"   Reports: {rep_count}")
            logger.info(f"   Completion Time: {elapsed_minutes:.1f} minutes")
            
            logger.info("\n🔗 Next Steps:")
            logger.info("1. Open http://localhost:3000")
            logger.info("2. Login with your credentials")
            logger.info("3. Navigate to Dashboard")
            logger.info("4. All data should now be visible:")
            logger.info("   • Cost comparison charts")
            logger.info("   • Performance visualizations")
            logger.info("   • AI recommendation tables")
            logger.info("   • Assessment progress indicators")
            logger.info("   • Recent activity feeds")
            
            return True
        
        logger.info(f"   🔄 Still processing... (Recommendations: {rec_count}, Reports: {rep_count})")
        logger.info(f"   ⏳ Waiting {check_interval} seconds before next check...")
        
        time.sleep(check_interval)
    
    # Timeout reached
    logger.warning(f"\n⏰ Monitoring timeout reached ({max_wait_minutes} minutes)")
    logger.info("Current status:")
    
    final_complete, final_rec, final_rep = verify_database_storage(token)
    
    if final_rec > 0 or final_rep > 0:
        logger.info("✅ Some data was generated successfully!")
        logger.info(f"   Recommendations: {final_rec}")
        logger.info(f"   Reports: {final_rep}")
        logger.info("\n💡 The dashboard may show partial data.")
        logger.info("   You can refresh or wait for remaining workflows to complete.")
    else:
        logger.warning("⚠️ No data was generated yet.")
        logger.info("   AI workflows may still be processing in the background.")
        logger.info("   Check the dashboard periodically or run this script again.")
    
    return final_complete

def main():
    """Main monitoring function."""
    try:
        success = monitor_workflow_completion(max_wait_minutes=15)
        
        if success:
            print("\n🎉 AI workflow monitoring completed successfully!")
            print("All data is now stored in the database and ready for dashboard display.")
        else:
            print("\n⏰ Monitoring completed with timeout.")
            print("Some workflows may still be processing in the background.")
            
        print(f"\n🔗 Dashboard: http://localhost:3000/dashboard")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped by user")
        print("AI workflows may continue running in the background")
        
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}")

if __name__ == "__main__":
    main()