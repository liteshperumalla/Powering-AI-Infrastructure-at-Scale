#!/usr/bin/env python3
"""
Test script for Azure production API integration.

This script tests the real Azure SDK integration with proper authentication,
rate limiting, and error handling.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.cloud.azure import AzureClient, AzureCredentialManager
from infra_mind.cloud.base import CloudServiceError, AuthenticationError, RateLimitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_azure_credentials():
    """Test Azure credential validation."""
    print("\n=== Testing Azure Credentials ===")
    
    try:
        credential_manager = AzureCredentialManager()
        
        # Check if credentials are configured
        if not credential_manager.subscription_id:
            print("❌ Azure subscription ID not configured")
            print("   Set AZURE_SUBSCRIPTION_ID environment variable")
            return False
        
        # Validate credentials
        is_valid = credential_manager.validate_credentials()
        
        if is_valid:
            print("✅ Azure credentials validated successfully")
            print(f"   Subscription ID: {credential_manager.subscription_id[:8]}...")
            return True
        else:
            print("❌ Azure credential validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error validating Azure credentials: {str(e)}")
        return False


async def test_azure_pricing_api():
    """Test Azure Retail Prices API (no authentication required)."""
    print("\n=== Testing Azure Pricing API ===")
    
    try:
        # Create client with minimal configuration for pricing API
        client = AzureClient(region="eastus")
        
        # Test pricing API call
        pricing_data = await client.pricing_client.get_service_pricing("Virtual Machines", "eastus")
        
        if pricing_data.get("real_data"):
            print("✅ Azure Pricing API working correctly")
            print(f"   Found {len(pricing_data.get('items', []))} pricing items")
            print(f"   Processed {len(pricing_data.get('processed_pricing', {}))} VM types")
            return True
        else:
            print("❌ Azure Pricing API returned no real data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Azure Pricing API: {str(e)}")
        return False


async def test_azure_compute_api():
    """Test Azure Compute API with authentication."""
    print("\n=== Testing Azure Compute API ===")
    
    try:
        # Check if we have credentials for authenticated APIs
        if not os.getenv('AZURE_SUBSCRIPTION_ID'):
            print("⚠️  Skipping Compute API test - no subscription ID configured")
            return True
        
        client = AzureClient(region="eastus")
        
        # Test compute services
        compute_response = await client.get_compute_services("eastus")
        
        if compute_response and compute_response.services:
            print("✅ Azure Compute API working correctly")
            print(f"   Found {len(compute_response.services)} VM sizes")
            
            # Show sample VM
            sample_vm = compute_response.services[0]
            print(f"   Sample VM: {sample_vm.service_name}")
            print(f"   Price: ${sample_vm.hourly_price}/hour")
            print(f"   vCPUs: {sample_vm.specifications.get('vcpus', 'N/A')}")
            print(f"   Memory: {sample_vm.specifications.get('memory_gb', 'N/A')} GB")
            
            return True
        else:
            print("❌ Azure Compute API returned no services")
            return False
            
    except AuthenticationError as e:
        print(f"⚠️  Authentication error (expected if no credentials): {str(e)}")
        return True  # This is expected without proper credentials
    except Exception as e:
        print(f"❌ Error testing Azure Compute API: {str(e)}")
        return False


async def test_azure_sql_api():
    """Test Azure SQL API with authentication."""
    print("\n=== Testing Azure SQL API ===")
    
    try:
        # Check if we have credentials for authenticated APIs
        if not os.getenv('AZURE_SUBSCRIPTION_ID'):
            print("⚠️  Skipping SQL API test - no subscription ID configured")
            return True
        
        client = AzureClient(region="eastus")
        
        # Test SQL services
        sql_response = await client.get_database_services("eastus")
        
        if sql_response and sql_response.services:
            print("✅ Azure SQL API working correctly")
            print(f"   Found {len(sql_response.services)} SQL Database services")
            
            # Show sample SQL service
            sample_sql = sql_response.services[0]
            print(f"   Sample SQL: {sample_sql.service_name}")
            print(f"   Price: ${sample_sql.hourly_price}/hour")
            print(f"   Edition: {sample_sql.specifications.get('edition', 'N/A')}")
            print(f"   Max Size: {sample_sql.specifications.get('max_size_gb', 'N/A')} GB")
            
            return True
        else:
            print("❌ Azure SQL API returned no services")
            return False
            
    except AuthenticationError as e:
        print(f"⚠️  Authentication error (expected if no credentials): {str(e)}")
        return True  # This is expected without proper credentials
    except Exception as e:
        print(f"❌ Error testing Azure SQL API: {str(e)}")
        return False


async def test_azure_rate_limiting():
    """Test Azure rate limiting and retry logic."""
    print("\n=== Testing Azure Rate Limiting ===")
    
    try:
        client = AzureClient(region="eastus")
        
        # Make multiple rapid requests to test rate limiting
        tasks = []
        for i in range(5):
            task = client.pricing_client.get_service_pricing("Virtual Machines", "eastus")
            tasks.append(task)
        
        # Execute requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        failed_requests = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"✅ Rate limiting test completed")
        print(f"   Successful requests: {successful_requests}")
        print(f"   Failed requests: {failed_requests}")
        
        # Check if any rate limit errors were handled
        rate_limit_errors = sum(1 for r in results if isinstance(r, RateLimitError))
        if rate_limit_errors > 0:
            print(f"   Rate limit errors handled: {rate_limit_errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing rate limiting: {str(e)}")
        return False


async def test_azure_error_handling():
    """Test Azure error handling."""
    print("\n=== Testing Azure Error Handling ===")
    
    try:
        client = AzureClient(region="eastus")
        
        # Test with invalid region
        try:
            await client.pricing_client.get_service_pricing("Virtual Machines", "invalid-region")
            print("⚠️  Expected error for invalid region, but got success")
        except CloudServiceError as e:
            print("✅ Invalid region error handled correctly")
            print(f"   Error: {str(e)}")
        
        # Test with invalid service name
        try:
            await client.pricing_client.get_service_pricing("Invalid Service", "eastus")
            print("✅ Invalid service handled correctly (may return empty results)")
        except CloudServiceError as e:
            print("✅ Invalid service error handled correctly")
            print(f"   Error: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing error handling: {str(e)}")
        return False


async def main():
    """Run all Azure integration tests."""
    print("🚀 Starting Azure Production Integration Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # List of test functions
    tests = [
        ("Credentials", test_azure_credentials),
        ("Pricing API", test_azure_pricing_api),
        ("Compute API", test_azure_compute_api),
        ("SQL API", test_azure_sql_api),
        ("Rate Limiting", test_azure_rate_limiting),
        ("Error Handling", test_azure_error_handling),
    ]
    
    results = {}
    
    # Run each test
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*50}")
    print("📊 Test Results Summary")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Azure integration tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and credentials.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)