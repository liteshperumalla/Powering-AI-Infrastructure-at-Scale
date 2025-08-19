#!/usr/bin/env python3
"""
Test script to verify all cloud service APIs are working.
"""

import asyncio
import logging
import os
from src.infra_mind.core.config import get_settings
from src.infra_mind.cloud.aws import AWSClient
from src.infra_mind.cloud.azure import AzureClient  
from src.infra_mind.cloud.gcp import GCPClient
from src.infra_mind.cloud.unified import UnifiedCloudClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cloud_apis():
    """Test all cloud service API connectivity."""
    
    logger.info("🧪 Testing Cloud Service APIs...")
    
    settings = get_settings()
    results = {}
    
    # Test AWS
    logger.info("🔧 Testing AWS API...")
    try:
        aws_creds = settings.get_aws_credentials()
        if aws_creds["access_key_id"] and aws_creds["secret_access_key"]:
            aws_client = AWSClient(
                aws_access_key_id=aws_creds["access_key_id"],
                aws_secret_access_key=aws_creds["secret_access_key"],
                region=aws_creds["region"]
            )
            
            # Test basic AWS API call
            compute_services = await aws_client.get_compute_services()
            logger.info(f"✅ AWS API working - {len(compute_services.services)} compute services available")
            logger.info(f"  Sample services: {[s.service_id for s in compute_services.services[:3]]}...")
            results["aws"] = {"status": "success", "services": len(compute_services.services)}
        else:
            logger.error("❌ AWS credentials not configured")
            results["aws"] = {"status": "error", "message": "Credentials not configured"}
    except Exception as e:
        logger.error(f"❌ AWS API failed: {e}")
        results["aws"] = {"status": "error", "message": str(e)}
    
    # Test Azure
    logger.info("🔧 Testing Azure API...")
    try:
        azure_creds = settings.get_azure_credentials()
        # Try with client credentials first, then fall back to Azure CLI
        azure_client = AzureClient(
            subscription_id=azure_creds.get("subscription_id"),
            client_id=azure_creds.get("client_id"),
            client_secret=azure_creds.get("client_secret"),
            tenant_id=azure_creds.get("tenant_id")
        )
        
        # Test basic Azure API call
        compute_services = await azure_client.get_compute_services()
        logger.info(f"✅ Azure API working - {len(compute_services.services)} compute services available")
        logger.info(f"  Sample services: {[s.service_id for s in compute_services.services[:3]]}...")
        results["azure"] = {"status": "success", "services": len(compute_services.services)}
    except Exception as e:
        logger.error(f"❌ Azure API failed: {e}")
        results["azure"] = {"status": "error", "message": str(e)}
    
    # Test GCP
    logger.info("🔧 Testing GCP API...")
    try:
        if settings.gcp_service_account_path and os.path.exists(settings.gcp_service_account_path):
            gcp_client = GCPClient(
                project_id=settings.gcp_project_id,
                service_account_path=settings.gcp_service_account_path
            )
            
            # Test basic GCP API call
            compute_services = await gcp_client.get_compute_services()
            logger.info(f"✅ GCP API working - {len(compute_services.services)} compute services available")
            logger.info(f"  Sample services: {[s.service_id for s in compute_services.services[:3]]}...")
            results["gcp"] = {"status": "success", "services": len(compute_services.services)}
        else:
            logger.error("❌ GCP service account file not found")
            results["gcp"] = {"status": "error", "message": "Service account file not found"}
    except Exception as e:
        logger.error(f"❌ GCP API failed: {e}")
        results["gcp"] = {"status": "error", "message": str(e)}
    
    # Summary
    logger.info("📊 Cloud API Test Results:")
    working_apis = [name for name, result in results.items() if result["status"] == "success"]
    failed_apis = [name for name, result in results.items() if result["status"] == "error"]
    
    if working_apis:
        logger.info(f"✅ Working APIs: {', '.join(working_apis)}")
    if failed_apis:
        logger.info(f"❌ Failed APIs: {', '.join(failed_apis)}")
        for api in failed_apis:
            logger.info(f"  {api}: {results[api]['message']}")
    
    return len(working_apis) > 0

if __name__ == "__main__":
    success = asyncio.run(test_cloud_apis())
    if success:
        print("🎉 At least one cloud API is working!")
    else:
        print("💥 All cloud APIs failed!")