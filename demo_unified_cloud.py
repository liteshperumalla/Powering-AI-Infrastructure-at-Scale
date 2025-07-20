#!/usr/bin/env python3
"""
Unified Cloud Client Demo.

This script demonstrates the unified cloud client that provides
a single interface for accessing multiple cloud providers.
"""

import asyncio
import os
from src.infra_mind.cloud import UnifiedCloudClient, CloudProvider, ServiceCategory


async def demo_unified_cloud():
    """Demonstrate the unified cloud client."""
    print("🌐 Unified Cloud Client Demo")
    print("=" * 50)
    print("This demo shows how to use a single interface to access multiple cloud providers.")
    print()
    
    # Initialize the unified cloud client
    client = UnifiedCloudClient(
        aws_region="us-east-1",
        azure_region="eastus",
        # AWS credentials can be provided here or via environment variables
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    
    # Check available providers
    available_providers = client.get_available_providers()
    print(f"Available Cloud Providers: {[p.name for p in available_providers]}")
    print()
    
    # Get compute services from all providers
    print("1. 💻 Getting Compute Services from All Providers")
    print("-" * 50)
    
    compute_results = await client.get_compute_services()
    
    for provider, response in compute_results.items():
        print(f"✅ {provider.name}: Found {len(response.services)} compute services")
        
        # Show top 3 cheapest services
        sorted_services = sorted(response.services, key=lambda x: x.hourly_price or float('inf'))[:3]
        print(f"Top 3 Cheapest {provider.name} Compute Services:")
        for i, service in enumerate(sorted_services, 1):
            print(f"  {i}. {service.service_id}: ${service.hourly_price:.4f}/hour")
        print()
    
    # Find cheapest compute service across all providers
    print("2. 🔍 Finding Cheapest Compute Service Across All Providers")
    print("-" * 60)
    
    cheapest = client.get_cheapest_service(compute_results)
    if cheapest:
        provider_name = cheapest["provider"].name
        service = cheapest["service"]
        print(f"🏆 Cheapest Compute: {provider_name} {service.service_id}")
        print(f"   ${service.hourly_price:.4f}/hour (${service.get_monthly_cost():.2f}/month)")
        print(f"   {service.specifications.get('vcpus', 'N/A')} vCPUs, {service.specifications.get('memory_gb', 'N/A')} GB RAM")
    else:
        print("❌ No compute services found")
    print()
    
    # Filter services by specifications
    print("3. 🔎 Filtering Services by Specifications")
    print("-" * 45)
    
    # Find services with 2 vCPUs
    filtered_results = client.filter_services_by_specs(compute_results, vcpus=2)
    
    print("Services with 2 vCPUs:")
    for provider, services in filtered_results.items():
        print(f"  {provider.name}: {len(services)} services")
        for service in services[:2]:  # Show first 2
            print(f"    • {service.service_id}: ${service.hourly_price:.4f}/hour")
    print()
    
    # Compare providers
    print("4. ⚖️  Provider Comparison")
    print("-" * 30)
    
    comparison = client.compare_providers(compute_results)
    
    print("Provider Statistics:")
    for provider_name, stats in comparison["providers"].items():
        print(f"  {provider_name}:")
        print(f"    - Service Count: {stats['service_count']}")
        if stats['cheapest_price']:
            print(f"    - Cheapest Service: {stats['cheapest_service']} (${stats['cheapest_price']:.4f}/hour)")
    
    if comparison["cheapest_provider"]:
        print(f"\n🏆 Cheapest Provider: {comparison['cheapest_provider']}")
    
    if comparison["most_options"]:
        print(f"🔢 Most Options: {comparison['most_options']}")
    
    if comparison["price_difference"]:
        diff = comparison["price_difference"]
        print(f"💰 Price Difference: ${diff['absolute']:.4f}/hour ({diff['percentage']:.1f}%)")
    print()
    
    # Get database services
    print("5. 🗄️  Database Services Comparison")
    print("-" * 40)
    
    try:
        db_results = await client.get_database_services()
        
        for provider, response in db_results.items():
            print(f"✅ {provider.name}: Found {len(response.services)} database services")
            
            # Show cheapest database service
            cheapest_db = response.get_cheapest_service()
            if cheapest_db:
                print(f"Cheapest {provider.name} Database: {cheapest_db.service_id}")
                print(f"  ${cheapest_db.hourly_price:.4f}/hour (${cheapest_db.get_monthly_cost():.2f}/month)")
            print()
        
        # Find cheapest database service across all providers
        cheapest_db_overall = client.get_cheapest_service(db_results)
        if cheapest_db_overall:
            provider_name = cheapest_db_overall["provider"].name
            service = cheapest_db_overall["service"]
            print(f"🏆 Cheapest Database Overall: {provider_name} {service.service_id}")
            print(f"   ${service.hourly_price:.4f}/hour (${service.get_monthly_cost():.2f}/month)")
    
    except Exception as e:
        print(f"❌ Error getting database services: {e}")
    
    print("\n✅ Unified Cloud Client Demo Complete!")
    print("=" * 50)
    print("Key Benefits of Unified Cloud Client:")
    print("• Single interface for multiple cloud providers")
    print("• Cross-cloud service comparison")
    print("• Automatic provider selection based on price")
    print("• Consistent service filtering across providers")
    print("• Graceful handling of unavailable providers")


if __name__ == "__main__":
    asyncio.run(demo_unified_cloud())