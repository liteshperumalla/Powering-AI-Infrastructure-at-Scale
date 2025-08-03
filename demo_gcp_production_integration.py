#!/usr/bin/env python3
"""
Demo script for GCP production API integration.

This script demonstrates the real GCP API integration with proper authentication,
rate limiting, and error handling.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.cloud.gcp import GCPClient
from infra_mind.cloud.base import AuthenticationError, RateLimitError, CloudServiceError


async def demo_gcp_production_integration():
    """Demonstrate GCP production API integration."""
    print("🚀 GCP Production API Integration Demo")
    print("=" * 50)
    
    # Configuration
    project_id = os.getenv('GCP_PROJECT_ID', 'demo-project-12345')
    region = os.getenv('GCP_REGION', 'us-central1')
    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"Project ID: {project_id}")
    print(f"Region: {region}")
    print(f"Service Account: {'✓ Set' if service_account_path else '✗ Not set (using ADC)'}")
    print()
    
    try:
        # Initialize GCP client
        print("🔧 Initializing GCP client...")
        client = GCPClient(project_id, region, service_account_path)
        print("✅ GCP client initialized successfully")
        print()
        
        # Test Compute Engine API
        print("💻 Testing Compute Engine API...")
        try:
            compute_response = await client.get_compute_services(region)
            print(f"✅ Found {len(compute_response.services)} compute services")
            print(f"   Real API: {compute_response.metadata.get('real_api', False)}")
            
            # Show first few services
            for i, service in enumerate(compute_response.services[:3]):
                print(f"   - {service.service_name}: ${service.hourly_price:.4f}/hour")
            
            if len(compute_response.services) > 3:
                print(f"   ... and {len(compute_response.services) - 3} more")
        except Exception as e:
            print(f"⚠️  Compute Engine API error: {e}")
        print()
        
        # Test Cloud SQL API
        print("🗄️  Testing Cloud SQL API...")
        try:
            sql_response = await client.get_database_services(region)
            print(f"✅ Found {len(sql_response.services)} database services")
            print(f"   Real API: {sql_response.metadata.get('real_api', False)}")
            
            # Show first few services
            for i, service in enumerate(sql_response.services[:3]):
                print(f"   - {service.service_name}: ${service.hourly_price:.4f}/hour")
        except Exception as e:
            print(f"⚠️  Cloud SQL API error: {e}")
        print()
        
        # Test Cloud Billing API
        print("💰 Testing Cloud Billing API...")
        try:
            pricing_data = await client.billing_client.get_service_pricing("Compute Engine", region)
            print(f"✅ Retrieved pricing data for Compute Engine")
            print(f"   Real API: {pricing_data.get('real_data', False)}")
            print(f"   Pricing entries: {len(pricing_data.get('pricing_data', {}))}")
        except Exception as e:
            print(f"⚠️  Cloud Billing API error: {e}")
        print()
        
        # Test GKE API
        print("☸️  Testing GKE API...")
        try:
            gke_response = await client.get_kubernetes_services(region)
            print(f"✅ Found {len(gke_response.services)} GKE services")
            print(f"   Real API: {gke_response.metadata.get('real_api', False)}")
            
            # Show first few services
            for i, service in enumerate(gke_response.services[:2]):
                print(f"   - {service.service_name}: ${service.hourly_price:.4f}/hour")
        except Exception as e:
            print(f"⚠️  GKE API error: {e}")
        print()
        
        # Test Asset Inventory API
        print("📦 Testing Asset Inventory API...")
        try:
            assets = await client.get_asset_inventory()
            print(f"✅ Found {assets.get('total_count', 0)} assets")
            print(f"   Real API: {assets.get('real_api', False)}")
        except Exception as e:
            print(f"⚠️  Asset Inventory API error: {e}")
        print()
        
        # Test AI Services
        print("🤖 Testing AI Services...")
        try:
            ai_response = await client.get_ai_services(region)
            print(f"✅ Found {len(ai_response.services)} AI services")
            print(f"   Real API: {ai_response.metadata.get('real_api', False)}")
            
            # Show first few services
            for i, service in enumerate(ai_response.services[:3]):
                print(f"   - {service.service_name}: ${service.hourly_price:.4f}/hour")
        except Exception as e:
            print(f"⚠️  AI Services API error: {e}")
        print()
        
        print("🎉 GCP Production API Integration Demo Complete!")
        print()
        print("📋 Summary:")
        print("- All GCP clients initialized with real API authentication")
        print("- Rate limiting and retry logic implemented")
        print("- Comprehensive error handling in place")
        print("- Fallback mechanisms available when APIs are unavailable")
        
    except AuthenticationError as e:
        print(f"🔐 Authentication Error: {e}")
        print()
        print("💡 To fix this:")
        print("1. Set up a GCP service account with appropriate permissions")
        print("2. Download the service account JSON key file")
        print("3. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("4. Or use Application Default Credentials (gcloud auth application-default login)")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    print("Starting GCP Production API Integration Demo...")
    print()
    
    # Check for required environment variables
    if not os.getenv('GCP_PROJECT_ID'):
        print("⚠️  Warning: GCP_PROJECT_ID not set, using demo project ID")
        print("   Set GCP_PROJECT_ID environment variable for your actual project")
        print()
    
    # Run the demo
    asyncio.run(demo_gcp_production_integration())


if __name__ == "__main__":
    main()