#!/usr/bin/env python3
"""
Test Azure OpenAI Connection

This script tests the Azure OpenAI connection to verify the AI agents
can properly communicate with the LLM service.
"""

import os
import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI Configuration from environment
AZURE_OPENAI_ENDPOINT = os.getenv("INFRA_MIND_AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("INFRA_MIND_AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("INFRA_MIND_AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("INFRA_MIND_AZURE_OPENAI_API_VERSION")

def test_azure_openai_connection():
    """Test direct connection to Azure OpenAI."""
    try:
        logger.info("🔍 Testing Azure OpenAI Connection...")
        logger.info(f"Endpoint: {AZURE_OPENAI_ENDPOINT}")
        logger.info(f"Deployment: {AZURE_OPENAI_DEPLOYMENT}")
        logger.info(f"API Version: {AZURE_OPENAI_API_VERSION}")
        
        if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION]):
            logger.error("❌ Missing Azure OpenAI configuration")
            return False
        
        # Construct the API URL
        url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        
        # Simple test payload
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful infrastructure assessment agent."
                },
                {
                    "role": "user", 
                    "content": "Generate a brief infrastructure recommendation for a startup company."
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }
        
        logger.info("📡 Sending test request to Azure OpenAI...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info("✅ Azure OpenAI connection successful!")
            logger.info(f"Response preview: {content[:100]}...")
            return True
        else:
            logger.error(f"❌ Azure OpenAI request failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Azure OpenAI connection error: {e}")
        return False

def test_api_workflow_trigger():
    """Test triggering workflows through the API."""
    try:
        logger.info("\n🚀 Testing API workflow trigger...")
        
        # Login
        login_data = {
            "email": "liteshperumalla@gmail.com",
            "password": "Litesh@#12345"
        }
        
        response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            logger.error("❌ Login failed")
            return False
        
        token = response.json().get('access_token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get assessments
        response = requests.get("http://localhost:8000/api/v1/assessments/", headers=headers)
        if response.status_code != 200:
            logger.error("❌ Failed to get assessments")
            return False
        
        assessments = response.json().get('assessments', [])
        if not assessments:
            logger.error("❌ No assessments found")
            return False
        
        assessment_id = assessments[0]['id']
        logger.info(f"📋 Testing with assessment: {assessment_id}")
        
        # Trigger recommendation workflow
        request_body = {
            "agent_names": None,
            "priority_override": None,
            "custom_config": None
        }
        
        response = requests.post(
            f"http://localhost:8000/api/v1/recommendations/{assessment_id}/generate",
            headers=headers,
            json=request_body,
            timeout=10
        )
        
        logger.info(f"Workflow trigger status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            result = response.json()
            workflow_id = result.get('workflow_id')
            logger.info(f"✅ Workflow triggered successfully: {workflow_id}")
            return True, workflow_id
        else:
            logger.error(f"❌ Failed to trigger workflow: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ API workflow trigger error: {e}")
        return False, None

def main():
    """Main test function."""
    print("🧪 TESTING AI WORKFLOW CONNECTIVITY")
    print("=" * 50)
    
    # Test 1: Azure OpenAI Connection
    print("\n1️⃣ Testing Azure OpenAI Connection...")
    openai_success = test_azure_openai_connection()
    
    # Test 2: API Workflow Trigger
    print("\n2️⃣ Testing API Workflow Trigger...")
    workflow_success, workflow_id = test_api_workflow_trigger()
    
    # Summary
    print("\n" + "=" * 50)
    print("🔍 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Azure OpenAI Connection: {'✅ SUCCESS' if openai_success else '❌ FAILED'}")
    print(f"API Workflow Trigger: {'✅ SUCCESS' if workflow_success else '❌ FAILED'}")
    
    if openai_success and workflow_success:
        print("\n🎉 All tests passed! The AI workflow system should be working.")
        print(f"📋 Workflow ID: {workflow_id}")
        print("\n💡 The workflows may be processing in the background.")
        print("   Let's wait a few minutes and check for results.")
    else:
        print("\n⚠️ Some tests failed. This explains why workflows are taking too long.")
        if not openai_success:
            print("   • Azure OpenAI connection issue - check API key and endpoint")
        if not workflow_success:
            print("   • API workflow trigger issue - check backend logs")

if __name__ == "__main__":
    main()