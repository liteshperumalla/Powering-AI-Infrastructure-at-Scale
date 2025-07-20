#!/usr/bin/env python3
"""
Multi-Cloud Comparison Demo (Legacy - with mock data fallbacks).

This script demonstrates comparing services across AWS and Azure.
Note: This demo includes mock data fallbacks for development purposes.
For production-ready real API integration, use demo_real_api_only.py
"""

import asyncio
from src.infra_mind.cloud.aws import AWSClient
from src.infra_mind.cloud.azure import AzureClient
from src.infra_mind.cloud.base import CloudProvider


async def demo_multi_cloud_comparison():
    """Demonstrate multi-cloud service comparison."""
    print("🌐 Multi-Cloud Comparison Demo")
    print("=" * 50)
    
    # Initialize both cloud clients
    aws_client = AWSClient(region="us-east-1")
    azure_client = AzureClient(region="eastus")
    
    # Force mock mode for both clients
    aws_client.pricing_client.boto_client = None
    aws_client.ec2_client.boto_client = None
    aws_client.rds_client.boto_client = None
    
    print("\n1. 💻 Compute Services Comparison")
    print("-" * 40)
    
    # Get compute services from both providers
    aws_compute = await aws_client.get_compute_services()
    azure_compute = await azure_client.get_compute_services()
    
    print(f"AWS EC2 Instances: {len(aws_compute.services)}")
    print(f"Azure Virtual Machines: {len(azure_compute.services)}")
    
    # Find cheapest compute from each provider
    aws_cheapest_compute = aws_compute.get_cheapest_service()
    azure_cheapest_compute = azure_compute.get_cheapest_service()
    
    print("\nCheapest Compute Options:")
    if aws_cheapest_compute:
        print(f"  🟠 AWS: {aws_cheapest_compute.service_id}")
        print(f"     - ${aws_cheapest_compute.hourly_price:.4f}/hour")
        print(f"     - {aws_cheapest_compute.specifications['vcpus']} vCPUs, {aws_cheapest_compute.specifications['memory_gb']} GB RAM")
    
    if azure_cheapest_compute:
        print(f"  🔵 Azure: {azure_cheapest_compute.service_id}")
        print(f"     - ${azure_cheapest_compute.hourly_price:.4f}/hour")
        print(f"     - {azure_cheapest_compute.specifications['vcpus']} vCPUs, {azure_cheapest_compute.specifications['memory_gb']} GB RAM")
    
    # Determine winner
    if aws_cheapest_compute and azure_cheapest_compute:
        if aws_cheapest_compute.hourly_price < azure_cheapest_compute.hourly_price:
            savings = azure_cheapest_compute.hourly_price - aws_cheapest_compute.hourly_price
            print(f"\n🏆 Winner: AWS (${savings:.4f}/hour cheaper)")
        elif azure_cheapest_compute.hourly_price < aws_cheapest_compute.hourly_price:
            savings = aws_cheapest_compute.hourly_price - azure_cheapest_compute.hourly_price
            print(f"\n🏆 Winner: Azure (${savings:.4f}/hour cheaper)")
        else:
            print(f"\n🤝 Tie: Both providers have the same price")
    
    print("\n2. 🗄️ Database Services Comparison")
    print("-" * 40)
    
    # Get database services from both providers
    aws_database = await aws_client.get_database_services()
    azure_database = await azure_client.get_database_services()
    
    print(f"AWS RDS Instances: {len(aws_database.services)}")
    print(f"Azure SQL Database Tiers: {len(azure_database.services)}")
    
    # Find cheapest database from each provider
    aws_cheapest_db = aws_database.get_cheapest_service()
    azure_cheapest_db = azure_database.get_cheapest_service()
    
    print("\nCheapest Database Options:")
    if aws_cheapest_db:
        print(f"  🟠 AWS: {aws_cheapest_db.service_id}")
        print(f"     - ${aws_cheapest_db.hourly_price:.4f}/hour")
        print(f"     - {aws_cheapest_db.specifications['memory_gb']} GB RAM")
        print(f"     - Engine: {aws_cheapest_db.specifications['engine']}")
    
    if azure_cheapest_db:
        print(f"  🔵 Azure: {azure_cheapest_db.service_id}")
        print(f"     - ${azure_cheapest_db.hourly_price:.4f}/hour")
        print(f"     - Max Size: {azure_cheapest_db.specifications['max_size_gb']} GB")
        print(f"     - DTU: {azure_cheapest_db.specifications['dtu']}")
    
    # Determine winner
    if aws_cheapest_db and azure_cheapest_db:
        if aws_cheapest_db.hourly_price < azure_cheapest_db.hourly_price:
            savings = azure_cheapest_db.hourly_price - aws_cheapest_db.hourly_price
            print(f"\n🏆 Winner: AWS (${savings:.4f}/hour cheaper)")
        elif azure_cheapest_db.hourly_price < aws_cheapest_db.hourly_price:
            savings = aws_cheapest_db.hourly_price - azure_cheapest_db.hourly_price
            print(f"\n🏆 Winner: Azure (${savings:.4f}/hour cheaper)")
        else:
            print(f"\n🤝 Tie: Both providers have the same price")
    
    print("\n3. 💾 Storage Services Comparison")
    print("-" * 40)
    
    # Get storage services from both providers
    aws_storage = await aws_client.get_storage_services()
    azure_storage = await azure_client.get_storage_services()
    
    print("Object Storage Comparison:")
    
    # Find object storage services
    aws_s3 = next((s for s in aws_storage.services if s.service_id == "s3"), None)
    azure_blob = next((s for s in azure_storage.services if s.service_id == "blob_storage"), None)
    
    if aws_s3:
        print(f"  🟠 AWS S3: {aws_s3.description}")
        print(f"     - Features: {', '.join(aws_s3.features[:3])}")
    
    if azure_blob:
        print(f"  🔵 Azure Blob: {azure_blob.description}")
        print(f"     - Features: {', '.join(azure_blob.features[:3])}")
    
    print("\nBlock Storage Comparison:")
    
    # Find block storage services
    aws_ebs = next((s for s in aws_storage.services if s.service_id == "ebs_gp3"), None)
    azure_disk = next((s for s in azure_storage.services if s.service_id == "managed_disk_premium"), None)
    
    if aws_ebs:
        print(f"  🟠 AWS EBS: ${aws_ebs.hourly_price} per {aws_ebs.pricing_unit}")
        print(f"     - IOPS: {aws_ebs.specifications['iops']}")
        print(f"     - Throughput: {aws_ebs.specifications['throughput']} MB/s")
    
    if azure_disk:
        print(f"  🔵 Azure Managed Disk: ${azure_disk.hourly_price} per {azure_disk.pricing_unit}")
        print(f"     - IOPS: {azure_disk.specifications['iops']}")
        print(f"     - Throughput: {azure_disk.specifications['throughput']} MB/s")
    
    # Determine storage winner
    if aws_ebs and azure_disk:
        if aws_ebs.hourly_price < azure_disk.hourly_price:
            savings = azure_disk.hourly_price - aws_ebs.hourly_price
            print(f"\n🏆 Block Storage Winner: AWS (${savings:.3f} per GB cheaper)")
        elif azure_disk.hourly_price < aws_ebs.hourly_price:
            savings = aws_ebs.hourly_price - azure_disk.hourly_price
            print(f"\n🏆 Block Storage Winner: Azure (${savings:.3f} per GB cheaper)")
    
    print("\n4. 📊 Total Cost Analysis")
    print("-" * 30)
    
    # Calculate basic setup costs for both providers
    aws_total = 0
    azure_total = 0
    
    print("Basic Setup Cost Comparison (1 VM + 1 DB + 100GB Storage):")
    
    # AWS costs
    if aws_cheapest_compute:
        aws_total += aws_cheapest_compute.get_monthly_cost() or 0
    if aws_cheapest_db:
        aws_total += aws_cheapest_db.get_monthly_cost() or 0
    aws_total += 2.30  # S3 storage estimate
    
    print(f"  🟠 AWS Total: ${aws_total:.2f}/month")
    if aws_cheapest_compute:
        print(f"     - Compute: ${aws_cheapest_compute.get_monthly_cost():.2f}")
    if aws_cheapest_db:
        print(f"     - Database: ${aws_cheapest_db.get_monthly_cost():.2f}")
    print(f"     - Storage: $2.30")
    
    # Azure costs
    if azure_cheapest_compute:
        azure_total += azure_cheapest_compute.get_monthly_cost() or 0
    if azure_cheapest_db:
        azure_total += azure_cheapest_db.get_monthly_cost() or 0
    azure_total += 2.00  # Blob storage estimate
    
    print(f"  🔵 Azure Total: ${azure_total:.2f}/month")
    if azure_cheapest_compute:
        print(f"     - Compute: ${azure_cheapest_compute.get_monthly_cost():.2f}")
    if azure_cheapest_db:
        print(f"     - Database: ${azure_cheapest_db.get_monthly_cost():.2f}")
    print(f"     - Storage: $2.00")
    
    # Overall winner
    if aws_total < azure_total:
        savings = azure_total - aws_total
        print(f"\n🏆 Overall Winner: AWS (${savings:.2f}/month cheaper)")
        print(f"   Annual Savings: ${savings * 12:.2f}")
    elif azure_total < aws_total:
        savings = aws_total - azure_total
        print(f"\n🏆 Overall Winner: Azure (${savings:.2f}/month cheaper)")
        print(f"   Annual Savings: ${savings * 12:.2f}")
    else:
        print(f"\n🤝 Overall Tie: Both providers cost the same")
    
    print("\n5. 🔍 Service Feature Comparison")
    print("-" * 35)
    
    # Compare high-memory compute options
    aws_high_memory = aws_compute.filter_by_specs(memory_gb=16)
    azure_high_memory = azure_compute.filter_by_specs(memory_gb=16)
    
    print("High Memory Compute Options (16GB RAM):")
    print(f"  🟠 AWS Options: {len(aws_high_memory)}")
    for service in aws_high_memory:
        print(f"     - {service.service_id}: ${service.hourly_price:.3f}/hour")
    
    print(f"  🔵 Azure Options: {len(azure_high_memory)}")
    for service in azure_high_memory:
        print(f"     - {service.service_id}: ${service.hourly_price:.3f}/hour")
    
    # Find cheapest high-memory option
    all_high_memory = aws_high_memory + azure_high_memory
    if all_high_memory:
        cheapest_high_memory = min(all_high_memory, key=lambda s: s.hourly_price)
        provider_name = "AWS" if cheapest_high_memory.provider == CloudProvider.AWS else "Azure"
        print(f"\n🏆 Cheapest High-Memory: {provider_name} {cheapest_high_memory.service_id}")
        print(f"   ${cheapest_high_memory.hourly_price:.3f}/hour")
    
    print("\n6. 📈 Scaling Cost Projections")
    print("-" * 35)
    
    # Project costs for different scales
    scales = [1, 5, 10, 50]
    
    print("Multi-instance scaling cost comparison:")
    print("Instances | AWS Monthly | Azure Monthly | Difference")
    print("-" * 50)
    
    for scale in scales:
        aws_scaled = aws_total * scale
        azure_scaled = azure_total * scale
        difference = abs(aws_scaled - azure_scaled)
        winner = "AWS" if aws_scaled < azure_scaled else "Azure" if azure_scaled < aws_scaled else "Tie"
        
        print(f"{scale:8d}  | ${aws_scaled:10.2f} | ${azure_scaled:12.2f} | ${difference:6.2f} ({winner})")
    
    print("\n✅ Multi-Cloud Comparison Complete!")
    print("=" * 50)
    print("This demo showed multi-cloud capabilities:")
    print("• Side-by-side service comparison")
    print("• Cost analysis across providers")
    print("• Feature and specification comparison")
    print("• Scaling cost projections")
    print("• Winner determination for each category")
    print("\nKey Benefits of Multi-Cloud Analysis:")
    print("• Avoid vendor lock-in")
    print("• Optimize costs across providers")
    print("• Choose best services for each workload")
    print("• Negotiate better pricing")
    print("• Improve disaster recovery options")


if __name__ == "__main__":
    asyncio.run(demo_multi_cloud_comparison())