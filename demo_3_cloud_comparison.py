#!/usr/bin/env python3
"""
3-Cloud Comparison Demo (AWS + Azure + GCP).

This script demonstrates comprehensive multi-cloud service comparison
across Amazon Web Services, Microsoft Azure, and Google Cloud Platform.
"""

import asyncio
import os
from src.infra_mind.cloud import UnifiedCloudClient, CloudProvider
from dotenv import load_dotenv

load_dotenv()


async def demo_3_cloud_comparison():
    """Demonstrate comprehensive 3-cloud service comparison."""
    print("🌐 3-Cloud Comparison Demo")
    print("=" * 60)
    print("Comparing AWS + Azure + GCP services with real-time pricing")
    print()
    
    # Initialize unified client with all three providers
    client = UnifiedCloudClient(
        aws_region="us-east-1",
        azure_region="eastus", 
        gcp_region="us-central1",
        # AWS credentials from environment
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        # Azure credentials from environment
        azure_subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
        azure_client_id=os.getenv("AZURE_CLIENT_ID"),
        azure_client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        # GCP credentials from environment
        gcp_project_id=os.getenv("GCP_PROJECT_ID", "infra-mind-api"),
        gcp_service_account_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    
    providers = client.get_available_providers()
    print(f"🔗 Connected Providers: {[p.name for p in providers]}")
    print()
    
    # 1. Compute Services Comparison
    print("1. 💻 Compute Services Cross-Cloud Analysis")
    print("-" * 50)
    
    compute_results = await client.get_compute_services()
    
    print("Provider Summary:")
    for provider, response in compute_results.items():
        cheapest = response.get_cheapest_service()
        print(f"  {provider.name:6s}: {len(response.services):3d} services | Cheapest: {cheapest.service_id if cheapest else 'N/A'}")
        if cheapest:
            print(f"          ${cheapest.hourly_price:.4f}/hour | {cheapest.specifications.get('vcpus', 'N/A')} vCPUs, {cheapest.specifications.get('memory_gb', 'N/A')} GB RAM")
    
    # Find overall winner
    overall_cheapest = client.get_cheapest_service(compute_results)
    if overall_cheapest:
        winner = overall_cheapest["provider"].name
        service = overall_cheapest["service"]
        print(f"\\n🏆 Compute Winner: {winner} {service.service_id}")
        print(f"   ${service.hourly_price:.4f}/hour (${service.get_monthly_cost():.2f}/month)")
        
        # Calculate savings vs other providers
        for provider, response in compute_results.items():
            if provider != overall_cheapest["provider"]:
                other_cheapest = response.get_cheapest_service()
                if other_cheapest:
                    savings = other_cheapest.hourly_price - service.hourly_price
                    savings_pct = (savings / other_cheapest.hourly_price) * 100
                    print(f"   💰 vs {provider.name}: ${savings:.4f}/hour cheaper ({savings_pct:.1f}% savings)")
    
    # 2. Database Services Comparison
    print("\\n2. 🗄️ Database Services Cross-Cloud Analysis")
    print("-" * 50)
    
    try:
        database_results = await client.get_database_services()
        
        print("Database Provider Summary:")
        for provider, response in database_results.items():
            cheapest_db = response.get_cheapest_service()
            print(f"  {provider.name:6s}: {len(response.services):3d} services | Cheapest: {cheapest_db.service_id if cheapest_db else 'N/A'}")
            if cheapest_db:
                print(f"          ${cheapest_db.hourly_price:.4f}/hour | {cheapest_db.specifications.get('memory_gb', 'N/A')} GB RAM")
        
        # Find database winner
        cheapest_db_overall = client.get_cheapest_service(database_results)
        if cheapest_db_overall:
            db_winner = cheapest_db_overall["provider"].name
            db_service = cheapest_db_overall["service"]
            print(f"\\n🏆 Database Winner: {db_winner} {db_service.service_id}")
            print(f"   ${db_service.hourly_price:.4f}/hour (${db_service.get_monthly_cost():.2f}/month)")
    
    except Exception as e:
        print(f"⚠️  Database comparison unavailable: {e}")
    
    # 3. Storage Services Comparison
    print("\\n3. 💾 Storage Services Cross-Cloud Analysis")
    print("-" * 50)
    
    try:
        storage_results = await client.get_storage_services()
        
        print("Storage Provider Summary:")
        for provider, response in storage_results.items():
            print(f"  {provider.name:6s}: {len(response.services):3d} storage services")
            
            # Show object storage pricing
            object_storage = next((s for s in response.services if "storage" in s.service_id.lower() or "blob" in s.service_id.lower()), None)
            if object_storage:
                print(f"          Object Storage: ${object_storage.hourly_price:.4f}/{object_storage.pricing_unit}")
    
    except Exception as e:
        print(f"⚠️  Storage comparison unavailable: {e}")
    
    # 4. Cost Analysis for Different Workloads
    print("\\n4. 💰 Workload Cost Analysis")
    print("-" * 35)
    
    # Small workload (1 small instance)
    print("Small Workload (1 micro/small instance):")
    small_costs = {}
    for provider, response in compute_results.items():
        # Find smallest instance
        small_instances = [s for s in response.services if 
                          any(size in s.service_id.lower() for size in ['micro', 'nano', 'small', 'f1-micro', 'e2-micro'])]
        if small_instances:
            cheapest_small = min(small_instances, key=lambda x: x.hourly_price)
            small_costs[provider.name] = cheapest_small.get_monthly_cost()
            print(f"  {provider.name:6s}: ${cheapest_small.get_monthly_cost():6.2f}/month ({cheapest_small.service_id})")
    
    if small_costs:
        cheapest_provider = min(small_costs.items(), key=lambda x: x[1])
        print(f"  🏆 Winner: {cheapest_provider[0]} (${cheapest_provider[1]:.2f}/month)")
    
    # Medium workload (2-4 vCPUs)
    print("\\nMedium Workload (2-4 vCPUs):")
    medium_costs = {}
    for provider, response in compute_results.items():
        medium_instances = response.filter_by_specs(vcpus=2) + response.filter_by_specs(vcpus=4)
        if medium_instances:
            cheapest_medium = min(medium_instances, key=lambda x: x.hourly_price)
            medium_costs[provider.name] = cheapest_medium.get_monthly_cost()
            print(f"  {provider.name:6s}: ${cheapest_medium.get_monthly_cost():6.2f}/month ({cheapest_medium.service_id})")
    
    if medium_costs:
        cheapest_provider = min(medium_costs.items(), key=lambda x: x[1])
        print(f"  🏆 Winner: {cheapest_provider[0]} (${cheapest_provider[1]:.2f}/month)")
    
    # 5. Provider Comparison Matrix
    print("\\n5. 📊 Provider Comparison Matrix")
    print("-" * 40)
    
    comparison = client.compare_providers(compute_results)
    
    print("Provider Statistics:")
    print(f"{'Provider':<10} {'Services':<10} {'Cheapest Price':<15} {'Best For'}")
    print("-" * 55)
    
    for provider_name, stats in comparison["providers"].items():
        best_for = ""
        if provider_name == comparison.get("cheapest_provider"):
            best_for += "💰 Cost "
        if provider_name == comparison.get("most_options"):
            best_for += "🔢 Options "
        
        cheapest_price = f"${stats['cheapest_price']:.4f}/h" if stats['cheapest_price'] else "N/A"
        print(f"{provider_name:<10} {stats['service_count']:<10} {cheapest_price:<15} {best_for}")
    
    # 6. Regional Availability Analysis
    print("\\n6. 🌍 Regional Availability Analysis")
    print("-" * 40)
    
    regions = {
        "AWS": "us-east-1 (N. Virginia)",
        "AZURE": "eastus (East US)",
        "GCP": "us-central1 (Iowa)"
    }
    
    print("Current Analysis Regions:")
    for provider_name, region in regions.items():
        if any(p.name == provider_name for p in providers):
            print(f"  ✅ {provider_name}: {region}")
        else:
            print(f"  ❌ {provider_name}: Not connected")
    
    # 7. Recommendations
    print("\\n7. 🎯 Multi-Cloud Recommendations")
    print("-" * 40)
    
    print("Based on this analysis:")
    
    if comparison.get("cheapest_provider"):
        print(f"• For cost optimization: Choose {comparison['cheapest_provider']}")
    
    if comparison.get("most_options"):
        print(f"• For service variety: Choose {comparison['most_options']}")
    
    print("• For high availability: Use multi-cloud deployment")
    print("• For vendor lock-in avoidance: Distribute workloads across providers")
    
    # Calculate potential multi-cloud savings
    if len(compute_results) >= 2:
        all_services = []
        for response in compute_results.values():
            all_services.extend(response.services)
        
        if all_services:
            avg_price = sum(s.hourly_price for s in all_services) / len(all_services)
            cheapest_price = min(s.hourly_price for s in all_services)
            potential_savings = (avg_price - cheapest_price) / avg_price * 100
            
            print(f"• Potential savings with optimal selection: {potential_savings:.1f}%")
    
    print("\\n8. 📈 Scaling Projections")
    print("-" * 30)
    
    if overall_cheapest:
        base_cost = overall_cheapest["service"].get_monthly_cost()
        scales = [1, 5, 10, 25, 50, 100]
        
        print("Multi-instance scaling costs (cheapest option):")
        print(f"{'Instances':<10} {'Monthly Cost':<15} {'Annual Cost'}")
        print("-" * 35)
        
        for scale in scales:
            monthly = base_cost * scale
            annual = monthly * 12
            print(f"{scale:<10} ${monthly:<14.2f} ${annual:,.2f}")
    
    print("\\n✅ 3-Cloud Comparison Complete!")
    print("=" * 60)
    print("🎉 Successfully compared AWS + Azure + GCP!")
    print("\\nKey Benefits of 3-Cloud Analysis:")
    print("• Comprehensive cost comparison across all major providers")
    print("• Avoid vendor lock-in with multi-cloud strategy")
    print("• Optimize workload placement based on pricing and features")
    print("• Improve disaster recovery with geographic distribution")
    print("• Leverage best-of-breed services from each provider")
    print("• Negotiate better pricing with competitive alternatives")


if __name__ == "__main__":
    asyncio.run(demo_3_cloud_comparison())