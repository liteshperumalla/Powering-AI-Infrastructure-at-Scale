#!/usr/bin/env python3
"""
Demo script for AWS production integration.

This script demonstrates the enhanced AWS API integration with real boto3 clients,
rate limiting, retry logic, and comprehensive error handling.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.cloud.aws import AWSClient
from infra_mind.cloud.base import CloudServiceError, RateLimitError, AuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_aws_credentials_validation():
    """Demo AWS credentials validation."""
    print("\n" + "="*60)
    print("AWS CREDENTIALS VALIDATION DEMO")
    print("="*60)
    
    # Get credentials from environment
    access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
    region = os.getenv('INFRA_MIND_AWS_REGION', 'us-east-1')
    
    if not access_key or not secret_key:
        print("❌ AWS credentials not found in environment variables")
        print("   Please set INFRA_MIND_AWS_ACCESS_KEY_ID and INFRA_MIND_AWS_SECRET_ACCESS_KEY")
        return None
    
    try:
        print(f"🔑 Validating AWS credentials for region: {region}")
        client = AWSClient(
            region=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        print("✅ AWS credentials validated successfully")
        return client
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


async def demo_rate_limiting(client: AWSClient):
    """Demo rate limiting functionality."""
    print("\n" + "="*60)
    print("RATE LIMITING DEMO")
    print("="*60)
    
    print("🚦 Testing rate limiting for pricing service...")
    
    # Make several rapid API calls to test rate limiting
    for i in range(15):
        try:
            await client._check_rate_limit('pricing')
            print(f"   Call {i+1}: ✅ Rate limit check passed")
        except RateLimitError as e:
            print(f"   Call {i+1}: ⚠️  Rate limit exceeded: {e}")
            break
        except Exception as e:
            print(f"   Call {i+1}: ❌ Error: {e}")
            break
    
    # Show rate limit history
    history_count = len(client.api_call_history.get('pricing', []))
    print(f"📊 API call history for pricing: {history_count} calls tracked")


async def demo_retry_logic(client: AWSClient):
    """Demo retry logic with simulated failures."""
    print("\n" + "="*60)
    print("RETRY LOGIC DEMO")
    print("="*60)
    
    print("🔄 Testing retry logic with simulated failures...")
    
    # Create a mock function that fails twice then succeeds (for demonstration only)
    call_count = 0
    async def mock_failing_function():
        nonlocal call_count
        call_count += 1
        print(f"   Attempt {call_count}: ", end="")
        
        if call_count <= 2:
            print("❌ Simulated failure (throttling) - Demo only, not using real credentials")
            from botocore.exceptions import ClientError
            raise ClientError(
                error_response={'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                operation_name='TestOperation'
            )
        
        print("✅ Success!")
        return {"success": True, "attempt": call_count}
    
    try:
        result = await client._execute_with_retry(
            'pricing', 'test_operation', mock_failing_function
        )
        print(f"🎉 Retry logic succeeded after {result['attempt']} attempts")
        
    except Exception as e:
        print(f"❌ Retry logic failed: {e}")


async def demo_service_discovery(client: AWSClient):
    """Demo service discovery with real AWS APIs."""
    print("\n" + "="*60)
    print("SERVICE DISCOVERY DEMO")
    print("="*60)
    
    try:
        print("🔍 Discovering AWS compute services...")
        compute_services = await client.get_compute_services()
        print(f"   Found {len(compute_services.services)} compute services")
        
        if compute_services.services:
            cheapest = compute_services.get_cheapest_service()
            if cheapest:
                print(f"   💰 Cheapest service: {cheapest.service_name} (${cheapest.hourly_price:.4f}/hour)")
        
        print("🔍 Discovering AWS storage services...")
        storage_services = await client.get_storage_services()
        print(f"   Found {len(storage_services.services)} storage services")
        
        for service in storage_services.services[:3]:  # Show first 3
            print(f"   📦 {service.service_name}: ${service.hourly_price:.4f}/{service.pricing_unit}")
        
        print("🔍 Discovering AWS database services...")
        database_services = await client.get_database_services()
        print(f"   Found {len(database_services.services)} database services")
        
        for service in database_services.services[:3]:  # Show first 3
            print(f"   🗄️  {service.service_name}: ${service.hourly_price:.4f}/hour")
            
    except CloudServiceError as e:
        print(f"❌ Service discovery error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def demo_pricing_accuracy(client: AWSClient):
    """Demo pricing data accuracy."""
    print("\n" + "="*60)
    print("PRICING ACCURACY DEMO")
    print("="*60)
    
    try:
        print("💲 Getting real-time AWS pricing data...")
        pricing_data = await client.get_service_pricing("AmazonEC2")
        
        if pricing_data.get("real_data"):
            print("✅ Using real AWS Pricing API data")
            print(f"   📊 Retrieved {len(pricing_data.get('products', []))} pricing products")
            print(f"   📄 Pages fetched: {pricing_data.get('pages_fetched', 'N/A')}")
        else:
            print("⚠️  Using fallback pricing data")
        
        # Parse and show sample pricing
        import json
        products = pricing_data.get("products", [])
        if products:
            sample_product = json.loads(products[0])
            product_attrs = sample_product.get("product", {}).get("attributes", {})
            instance_type = product_attrs.get("instanceType", "Unknown")
            location = product_attrs.get("location", "Unknown")
            
            print(f"   🖥️  Sample product: {instance_type} in {location}")
            
    except Exception as e:
        print(f"❌ Pricing accuracy demo error: {e}")


async def demo_error_handling(client: AWSClient):
    """Demo comprehensive error handling."""
    print("\n" + "="*60)
    print("ERROR HANDLING DEMO")
    print("="*60)
    
    print("🛡️  Testing error handling scenarios...")
    
    # Test with invalid service
    try:
        await client._check_rate_limit('invalid_service')
        print("   ✅ Invalid service handled gracefully")
    except Exception as e:
        print(f"   ❌ Invalid service error: {e}")
    
    # Test with non-retryable error (for demonstration only)
    async def mock_auth_error():
        from botocore.exceptions import ClientError
        raise ClientError(
            error_response={'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Not authorized'}},
            operation_name='TestOperation'
        )
    
    try:
        await client._execute_with_retry('pricing', 'test_auth_error', mock_auth_error)
    except CloudServiceError as e:
        print(f"   ✅ Non-retryable error handled correctly: {e.error_code}")
    except Exception as e:
        print(f"   ❌ Unexpected error handling issue: {e}")


async def demo_performance_metrics(client: AWSClient):
    """Demo performance metrics and monitoring."""
    print("\n" + "="*60)
    print("PERFORMANCE METRICS DEMO")
    print("="*60)
    
    print("📈 Performance metrics:")
    print(f"   🔢 Total API calls made: {client.api_call_count}")
    
    # Show rate limit configurations
    print("⚙️  Rate limit configurations:")
    for service, limits in client.rate_limits.items():
        calls_per_sec = limits['calls_per_second']
        burst = limits['burst']
        history_count = len(client.api_call_history.get(service, []))
        print(f"   {service}: {calls_per_sec}/sec (burst: {burst}, history: {history_count})")
    
    # Health check
    health = await client.health_check()
    print(f"🏥 Health status: {health['status']}")
    if health.get('last_error'):
        print(f"   ⚠️  Last error: {health['last_error']}")


async def main():
    """Main demo function."""
    print("🚀 AWS Production Integration Demo")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate credentials and create client
    client = await demo_aws_credentials_validation()
    if not client:
        print("\n❌ Cannot proceed without valid AWS credentials")
        return
    
    # Run all demos
    await demo_rate_limiting(client)
    await demo_retry_logic(client)
    await demo_service_discovery(client)
    await demo_pricing_accuracy(client)
    await demo_error_handling(client)
    await demo_performance_metrics(client)
    
    print("\n" + "="*60)
    print("✅ AWS Production Integration Demo Completed Successfully!")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()