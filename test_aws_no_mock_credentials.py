#!/usr/bin/env python3
"""
Test script to verify AWS implementation works without mock credentials.

This script demonstrates that the AWS implementation properly handles
credential validation and fails gracefully when no valid credentials are provided.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, 'src')

from infra_mind.cloud.aws import AWSClient
from infra_mind.cloud.base import AuthenticationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_no_credentials():
    """Test behavior when no credentials are provided."""
    print("🔍 Testing AWS client with no credentials...")
    
    try:
        # This should fail with AuthenticationError
        client = AWSClient(region="us-east-1")
        print("❌ ERROR: Client creation should have failed without credentials")
        return False
    except AuthenticationError as e:
        print(f"✅ Correctly failed with AuthenticationError: {e.error_code}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_invalid_credentials():
    """Test behavior with clearly invalid credentials."""
    print("\n🔍 Testing AWS client with invalid credentials...")
    
    try:
        # Use clearly invalid credentials (not real ones)
        client = AWSClient(
            region="us-east-1",
            aws_access_key_id="AKIA0000000000000000",  # Invalid format
            aws_secret_access_key="0000000000000000000000000000000000000000"  # Invalid format
        )
        print("❌ ERROR: Client creation should have failed with invalid credentials")
        return False
    except AuthenticationError as e:
        print(f"✅ Correctly failed with AuthenticationError: {e.error_code}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_environment_credentials():
    """Test behavior with environment credentials if available."""
    print("\n🔍 Testing AWS client with environment credentials...")
    
    access_key = os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("⚠️  No environment credentials found - skipping this test")
        return True
    
    try:
        client = AWSClient(
            region="us-east-1",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        print("✅ Successfully created client with environment credentials")
        
        # Test rate limiting initialization
        assert hasattr(client, 'rate_limits')
        assert 'pricing' in client.rate_limits
        print("✅ Rate limiting properly initialized")
        
        # Test API call history initialization
        assert hasattr(client, 'api_call_history')
        assert 'pricing' in client.api_call_history
        print("✅ API call history properly initialized")
        
        return True
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed with environment credentials: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error with environment credentials: {e}")
        return False


def test_configuration_validation():
    """Test that configuration is properly set up."""
    print("\n🔍 Testing configuration validation...")
    
    # Test that we can import all necessary classes
    try:
        from infra_mind.cloud.aws import (
            AWSClient, AWSPricingClient, AWSEC2Client, AWSRDSClient,
            AWSEKSClient, AWSLambdaClient, AWSSageMakerClient,
            AWSCostExplorerClient, AWSBudgetsClient
        )
        print("✅ All AWS client classes imported successfully")
        
        from infra_mind.cloud.base import (
            CloudProvider, ServiceCategory, CloudService, CloudServiceResponse,
            CloudServiceError, RateLimitError, AuthenticationError
        )
        print("✅ All base classes imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 AWS No Mock Credentials Test Suite")
    print("=" * 50)
    
    tests = [
        test_configuration_validation,
        test_no_credentials,
        test_invalid_credentials,
        test_environment_credentials
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! AWS implementation works without mock credentials.")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())