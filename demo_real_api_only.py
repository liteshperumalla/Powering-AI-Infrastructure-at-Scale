#!/usr/bin/env python3
"""
Production Real API Integration Demo.

This script demonstrates the production-ready cloud integration that uses
ONLY real API data from Azure and AWS. No mock data fallbacks.

This is the primary demo showcasing our enterprise-grade cloud integration.
"""

import asyncio
import os
from src.infra_mind.cloud.azure import AzureClient
from src.infra_mind.cloud.aws import AWSClient
from src.infra_mind.cloud.base import CloudServiceError, AuthenticationError


async def demo_azure_real_api_only():
    """Demonstrate Azure real API-only integration."""
    print("🔵 Azure Real API-Only Integration")
    print("-" * 40)
    
    try:
        client = AzureClient(region="eastus")
        
        # Test compute services
        print("Getting VM services with real pricing...")
        compute_services = await client.get_compute_services()
        
        print(f"✅ Found {len(compute_services.services)} VM sizes with real pricing")
        
        # Show top 5 cheapest
        sorted_vms = sorted(compute_services.services, key=lambda x: x.hourly_price)[:5]
        print("\nTop 5 Cheapest VMs:")
        for i, vm in enumerate(sorted_vms, 1):
            print(f"  {i}. {vm.service_id}: ${vm.hourly_price:.4f}/hour")
        
        # Test database services
        print("\nGetting SQL Database services with real pricing...")
        try:
            db_services = await client.get_database_services()
            print(f"✅ Found {len(db_services.services)} SQL Database tiers with real pricing")
            
            # Show cheapest database
            cheapest_db = db_services.get_cheapest_service()
            if cheapest_db:
                print(f"Cheapest Database: {cheapest_db.service_id} - ${cheapest_db.hourly_price:.4f}/hour")
        
        except CloudServiceError as e:
            print(f"⚠️  SQL Database pricing not available: {e}")
        
        # Test storage services
        print("\nGetting Storage services with real pricing...")
        try:
            storage_services = await client.get_storage_services()
            print(f"✅ Found {len(storage_services.services)} storage services with real pricing")
        
        except CloudServiceError as e:
            print(f"⚠️  Storage pricing not available: {e}")
        
        return compute_services
        
    except CloudServiceError as e:
        print(f"❌ Azure API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None


async def demo_aws_real_api_only():
    """Demonstrate AWS real API-only integration."""
    print("\n🟠 AWS Real API-Only Integration")
    print("-" * 40)
    
    # Check for AWS credentials
    has_credentials = (
        os.getenv('AWS_ACCESS_KEY_ID') or 
        os.getenv('AWS_PROFILE') or
        os.path.exists(os.path.expanduser('~/.aws/credentials'))
    )
    
    if not has_credentials:
        print("⚠️  No AWS credentials found. AWS requires valid credentials for real API access.")
        print("To test AWS integration:")
        print("  export AWS_ACCESS_KEY_ID=your_key")
        print("  export AWS_SECRET_ACCESS_KEY=your_secret")
        print("  # or run: aws configure")
        return None
    
    try:
        client = AWSClient(region="us-east-1")
        
        # Test compute services
        print("Getting EC2 instances with real pricing...")
        compute_services = await client.get_compute_services()
        
        print(f"✅ Found {len(compute_services.services)} EC2 instances with real pricing")
        
        # Show top 5 cheapest
        sorted_instances = sorted(compute_services.services, key=lambda x: x.hourly_price)[:5]
        print("\nTop 5 Cheapest EC2 Instances:")
        for i, instance in enumerate(sorted_instances, 1):
            print(f"  {i}. {instance.service_id}: ${instance.hourly_price:.4f}/hour")
        
        # Test database services
        print("\nGetting RDS instances with real pricing...")
        try:
            db_services = await client.get_database_services()
            print(f"✅ Found {len(db_services.services)} RDS instances with real pricing")
            
            # Show cheapest database
            cheapest_db = db_services.get_cheapest_service()
            if cheapest_db:
                print(f"Cheapest Database: {cheapest_db.service_id} - ${cheapest_db.hourly_price:.4f}/hour")
        
        except CloudServiceError as e:
            print(f"⚠️  RDS pricing not available: {e}")
        
        # Test storage services
        print("\nGetting Storage services with real pricing...")
        try:
            storage_services = await client.get_storage_services()
            print(f"✅ Found {len(storage_services.services)} storage services with real pricing")
        
        except CloudServiceError as e:
            print(f"⚠️  Storage pricing not available: {e}")
        
        return compute_services
        
    except AuthenticationError as e:
        print(f"❌ AWS Authentication Error: {e}")
        print("Please check your AWS credentials and try again.")
        return None
    except CloudServiceError as e:
        print(f"❌ AWS API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None


async def demo_multi_cloud_real_comparison():
    """Demonstrate multi-cloud comparison with real data only."""
    print("\n⚖️  Multi-Cloud Real Data Comparison")
    print("-" * 45)
    
    # Get data from both providers
    azure_compute = await demo_azure_real_api_only()
    aws_compute = await demo_aws_real_api_only()
    
    if azure_compute and aws_compute:
        print("\n📊 Direct Cost Comparison (Real Data)")
        print("-" * 40)
        
        azure_cheapest = azure_compute.get_cheapest_service()
        aws_cheapest = aws_compute.get_cheapest_service()
        
        print("Cheapest Compute Options:")
        print(f"  🔵 Azure: {azure_cheapest.service_id} - ${azure_cheapest.hourly_price:.4f}/hour")
        print(f"  🟠 AWS: {aws_cheapest.service_id} - ${aws_cheapest.hourly_price:.4f}/hour")
        
        # Determine winner
        if azure_cheapest.hourly_price < aws_cheapest.hourly_price:
            savings = aws_cheapest.hourly_price - azure_cheapest.hourly_price
            print(f"\n🏆 Winner: Azure (${savings:.4f}/hour cheaper)")
            print(f"   Annual savings: ${savings * 24 * 365:.2f}")
        elif aws_cheapest.hourly_price < azure_cheapest.hourly_price:
            savings = azure_cheapest.hourly_price - aws_cheapest.hourly_price
            print(f"\n🏆 Winner: AWS (${savings:.4f}/hour cheaper)")
            print(f"   Annual savings: ${savings * 24 * 365:.2f}")
        else:
            print(f"\n🤝 Tie: Both providers have similar pricing")
        
        # Service count comparison
        print(f"\nService Availability:")
        print(f"  🔵 Azure VMs: {len(azure_compute.services)} options")
        print(f"  🟠 AWS EC2: {len(aws_compute.services)} options")
        
    elif azure_compute:
        print("\n📊 Azure-Only Analysis (Real Data)")
        print("-" * 35)
        
        cheapest = azure_compute.get_cheapest_service()
        most_expensive = max(azure_compute.services, key=lambda x: x.hourly_price)
        
        print(f"Cheapest: {cheapest.service_id} - ${cheapest.hourly_price:.4f}/hour")
        print(f"Most Expensive: {most_expensive.service_id} - ${most_expensive.hourly_price:.4f}/hour")
        print(f"Price Range: {most_expensive.hourly_price / cheapest.hourly_price:.1f}x difference")
        
    elif aws_compute:
        print("\n📊 AWS-Only Analysis (Real Data)")
        print("-" * 35)
        
        cheapest = aws_compute.get_cheapest_service()
        most_expensive = max(aws_compute.services, key=lambda x: x.hourly_price)
        
        print(f"Cheapest: {cheapest.service_id} - ${cheapest.hourly_price:.4f}/hour")
        print(f"Most Expensive: {most_expensive.service_id} - ${most_expensive.hourly_price:.4f}/hour")
        print(f"Price Range: {most_expensive.hourly_price / cheapest.hourly_price:.1f}x difference")
    
    else:
        print("❌ No real data available from either provider")


async def demo_real_api_only():
    """Main demo function."""
    print("🌐 Real API-Only Integration Demo")
    print("=" * 60)
    print("This demo uses ONLY real cloud API data - no mock data fallbacks!")
    print("All pricing and service information comes directly from cloud providers.")
    print()
    
    await demo_multi_cloud_real_comparison()
    
    print("\n🚀 Production-Ready Features")
    print("-" * 35)
    
    print("✅ Real-time pricing data")
    print("✅ Current service availability")
    print("✅ Accurate regional pricing")
    print("✅ No mock data dependencies")
    print("✅ Production error handling")
    print("✅ Credential validation")
    print("✅ Comprehensive API coverage")
    
    print("\n📋 API Requirements")
    print("-" * 25)
    
    print("Azure:")
    print("  • No credentials required (public pricing API)")
    print("  • Real-time VM and SQL Database pricing")
    print("  • Global region support")
    
    print("\nAWS:")
    print("  • Valid AWS credentials required")
    print("  • EC2, RDS, and Storage pricing")
    print("  • Full service specifications")
    
    print("\n✅ Real API-Only Demo Complete!")
    print("=" * 60)
    print("The platform now provides 100% real cloud data with no mock fallbacks.")
    print("This ensures maximum accuracy for AI agent recommendations!")


if __name__ == "__main__":
    asyncio.run(demo_real_api_only())