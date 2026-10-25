#!/usr/bin/env python3
"""
Generate Real AI Recommendations using Agents and LLM APIs

This script uses the actual AI agents and LLM system to generate authentic
recommendations and reports for your assessments.
"""

import requests
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"

def login_user(email, password):
    """Login and get access token."""
    try:
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Logged in as: {result.get('full_name')}")
            return result.get('access_token')
        else:
            logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return None

def get_user_assessments(token):
    """Get user's assessments."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/api/v1/assessments/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            assessments = result.get('assessments', [])
            logger.info(f"✅ Found {len(assessments)} assessments")
            return assessments
        else:
            logger.error(f"❌ Failed to get assessments: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error getting assessments: {e}")
        return []

def generate_recommendations_via_api(token, assessment_id):
    """Generate recommendations using the AI agents through the API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        logger.info(f"🤖 Starting AI recommendation generation for assessment {assessment_id}...")
        
        # Trigger recommendation generation through the API
        request_body = {
            "agent_names": None,  # Run all agents
            "priority_override": None,
            "custom_config": None
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/recommendations/{assessment_id}/generate",
            headers=headers,
            json=request_body
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Recommendation generation started successfully")
            logger.info(f"📋 Workflow ID: {result.get('workflow_id', 'N/A')}")
            return result
        elif response.status_code == 202:
            result = response.json()
            logger.info("✅ Recommendation generation accepted and processing")
            logger.info(f"📋 Workflow ID: {result.get('workflow_id', 'N/A')}")
            return result
        else:
            logger.error(f"❌ Failed to start recommendation generation: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating recommendations: {e}")
        return None

def generate_reports_via_api(token, assessment_id):
    """Generate reports using the AI system through the API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        logger.info(f"📊 Starting AI report generation for assessment {assessment_id}...")
        
        # Trigger report generation through the API
        request_body = {
            "report_type": "comprehensive",
            "format": "pdf",
            "title": None,
            "sections": None,
            "custom_template": None,
            "priority": "medium"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/reports/{assessment_id}/generate",
            headers=headers,
            json=request_body
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Report generation started successfully")
            return result
        elif response.status_code == 202:
            result = response.json()
            logger.info("✅ Report generation accepted and processing")
            return result
        else:
            logger.error(f"❌ Failed to start report generation: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating reports: {e}")
        return None

def check_workflow_status(token, workflow_id):
    """Check the status of a workflow."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{API_BASE}/api/v1/workflows/{workflow_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"⚠️ Could not check workflow status: {response.status_code}")
            return None
            
    except Exception as e:
        logger.warning(f"⚠️ Error checking workflow status: {e}")
        return None

def wait_for_completion(token, workflow_id, max_wait_minutes=10):
    """Wait for workflow completion with progress updates."""
    if not workflow_id:
        logger.warning("⚠️ No workflow ID provided, skipping wait")
        return True
    
    logger.info(f"⏳ Waiting for workflow completion (max {max_wait_minutes} minutes)...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        status = check_workflow_status(token, workflow_id)
        
        if status:
            state = status.get('status', 'unknown')
            logger.info(f"🔄 Workflow status: {state}")
            
            if state in ['completed', 'success']:
                logger.info("✅ Workflow completed successfully!")
                return True
            elif state in ['failed', 'error']:
                logger.error("❌ Workflow failed")
                return False
        
        # Wait before checking again
        time.sleep(15)  # Check every 15 seconds
    
    logger.warning(f"⏰ Workflow did not complete within {max_wait_minutes} minutes")
    return False

def verify_recommendations_created(token, assessment_id):
    """Verify that recommendations were actually created."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{API_BASE}/api/v1/recommendations/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            count = len(recommendations) if isinstance(recommendations, list) else 0
            logger.info(f"✅ Verified: {count} recommendations created")
            return count > 0
        else:
            logger.warning(f"⚠️ Could not verify recommendations: {response.status_code}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Error verifying recommendations: {e}")
        return False

def verify_reports_created(token, assessment_id):
    """Verify that reports were actually created."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{API_BASE}/api/v1/reports/?assessment_id={assessment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            reports = response.json()
            count = len(reports) if isinstance(reports, list) else 0
            logger.info(f"✅ Verified: {count} reports created")
            return count > 0
        else:
            logger.warning(f"⚠️ Could not verify reports: {response.status_code}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Error verifying reports: {e}")
        return False

def regenerate_assessment_data(token, assessment):
    """Regenerate recommendations and reports for a single assessment using AI agents."""
    
    assessment_id = assessment['id']
    title = assessment['title']
    
    logger.info(f"\n🚀 Processing Assessment: {title}")
    logger.info(f"📋 ID: {assessment_id}")
    logger.info(f"📊 Status: {assessment['status']}")
    
    success_count = 0
    
    # Step 1: Generate AI Recommendations
    logger.info("\n1️⃣ Generating AI Recommendations...")
    rec_result = generate_recommendations_via_api(token, assessment_id)
    
    if rec_result:
        workflow_id = rec_result.get('workflow_id')
        logger.info(f"🔄 Recommendation workflow started: {workflow_id}")
        
        # Wait for completion
        if wait_for_completion(token, workflow_id, max_wait_minutes=8):
            if verify_recommendations_created(token, assessment_id):
                success_count += 1
                logger.info("✅ Recommendations generated successfully!")
            else:
                logger.warning("⚠️ Recommendations workflow completed but no data found")
        else:
            logger.warning("⚠️ Recommendation generation timed out or failed")
    else:
        logger.error("❌ Failed to start recommendation generation")
    
    # Step 2: Generate AI Reports
    logger.info("\n2️⃣ Generating AI Reports...")
    report_result = generate_reports_via_api(token, assessment_id)
    
    if report_result:
        workflow_id = report_result.get('workflow_id')
        logger.info(f"🔄 Report workflow started: {workflow_id}")
        
        # Wait for completion
        if wait_for_completion(token, workflow_id, max_wait_minutes=5):
            if verify_reports_created(token, assessment_id):
                success_count += 1
                logger.info("✅ Reports generated successfully!")
            else:
                logger.warning("⚠️ Report workflow completed but no data found")
        else:
            logger.warning("⚠️ Report generation timed out or failed")
    else:
        logger.error("❌ Failed to start report generation")
    
    return success_count

def main():
    """Main function to generate real AI recommendations and reports."""
    
    print("🤖 GENERATE REAL AI RECOMMENDATIONS & REPORTS")
    print("=" * 80)
    print("Using actual AI agents and LLM APIs to generate authentic data")
    print("=" * 80)
    
    # Step 1: Login
    print("\n1️⃣ Authenticating...")
    email = "liteshperumalla@gmail.com"
    password = "Litesh@#12345"
    
    token = login_user(email, password)
    if not token:
        print("❌ Authentication failed")
        return
    
    # Step 2: Get assessments
    print("\n2️⃣ Loading your assessments...")
    assessments = get_user_assessments(token)
    
    if not assessments:
        print("❌ No assessments found")
        return
    
    print(f"📋 Found {len(assessments)} assessments to process")
    
    # Step 3: Process each assessment
    print("\n3️⃣ Generating AI recommendations and reports...")
    
    total_success = 0
    total_assessments = len(assessments)
    
    for i, assessment in enumerate(assessments, 1):
        print(f"\n--- Processing Assessment {i}/{total_assessments} ---")
        
        success_count = regenerate_assessment_data(token, assessment)
        total_success += success_count
        
        print(f"✅ Completed: {success_count}/2 components generated")
        
        # Add small delay between assessments
        if i < total_assessments:
            time.sleep(5)
    
    # Step 4: Final results
    print("\n" + "=" * 80)
    print("🎉 AI GENERATION COMPLETE!")
    print("=" * 80)
    print(f"📊 Processed: {total_assessments} assessments")
    print(f"✅ Successfully generated: {total_success} components")
    print(f"📈 Success rate: {(total_success / (total_assessments * 2)) * 100:.1f}%")
    
    if total_success > 0:
        print("\n🌟 Your dashboard should now show:")
        print("   ✅ AI-generated recommendations with confidence scores")
        print("   ✅ Comprehensive reports with technical analysis")
        print("   ✅ Cost optimization suggestions")
        print("   ✅ Performance and security recommendations")
        print("   ✅ Real-time dashboard visualizations")
        
        print("\n🔗 Next Steps:")
        print("1. Open http://localhost:3000")
        print("2. Login with your credentials")
        print("3. Go to Dashboard - you should see AI-generated content!")
        print("4. Click 'Refresh Data' if needed")
        
        print("\n💡 What you'll see:")
        print("   📊 Cost comparison charts with real data")
        print("   🎯 AI recommendation scores and confidence levels")
        print("   📈 Performance metrics and improvement suggestions")
        print("   📋 Detailed assessment results")
        print("   🔄 Real-time progress tracking")
    else:
        print("\n⚠️ No data was generated successfully.")
        print("   • Check that the AI agents are properly configured")
        print("   • Verify the LLM service is running")
        print("   • Try running the script again")
    
    print(f"\n🔗 Dashboard: http://localhost:3000/dashboard")

if __name__ == "__main__":
    main()