#!/usr/bin/env python3
"""
Demo script for Terraform API integration.

This script demonstrates the Terraform Cloud API and Terraform Registry API
functionality for cost estimation and provider information retrieval.

Usage:
    python demo_terraform_apis.py

Environment Variables:
    TERRAFORM_TOKEN: Terraform Cloud API token (optional for registry-only operations)
    TERRAFORM_ORG: Terraform Cloud organization name (optional)
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.cloud.terraform import TerraformClient, TerraformCloudClient, TerraformRegistryClient
from src.infra_mind.cloud.base import CloudServiceError, AuthenticationError, RateLimitError


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def format_json(data: Dict[str, Any]) -> str:
    """Format dictionary as pretty JSON."""
    return json.dumps(data, indent=2, default=str)


async def demo_terraform_registry():
    """Demonstrate Terraform Registry API functionality."""
    print_section("Terraform Registry API Demo")
    
    registry_client = TerraformRegistryClient()
    
    try:
        # Demo 1: Get popular providers
        print_subsection("Popular Terraform Providers")
        providers = await registry_client.get_providers()
        
        print(f"Found {providers['total_count']} providers")
        for provider in providers['providers'][:5]:  # Show first 5
            print(f"  • {provider['full_name']}: {provider['description'][:80]}...")
            print(f"    Downloads: {provider['downloads']:,}")
        
        # Demo 2: Get AWS-specific providers
        print_subsection("HashiCorp Providers")
        hashicorp_providers = await registry_client.get_providers(namespace="hashicorp")
        
        print(f"Found {hashicorp_providers['total_count']} HashiCorp providers")
        for provider in hashicorp_providers['providers'][:3]:
            print(f"  • {provider['name']}: {provider['description'][:60]}...")
        
        # Demo 3: Get AWS modules
        print_subsection("AWS Terraform Modules")
        aws_modules = await registry_client.get_modules(provider="aws")
        
        print(f"Found {aws_modules['total_count']} AWS modules")
        for module in aws_modules['modules'][:5]:
            print(f"  • {module['namespace']}/{module['name']}")
            print(f"    Description: {module['description'][:70]}...")
            print(f"    Downloads: {module['downloads']:,} | Verified: {module['verified']}")
        
        # Demo 4: Get compute modules across providers
        print_subsection("Compute Modules (Multi-Cloud)")
        compute_services = await registry_client.get_compute_modules()
        
        print(f"Found {len(compute_services.services)} compute-related modules")
        for service in compute_services.services[:5]:
            print(f"  • {service.provider.value}: {service.service_name}")
            print(f"    Description: {service.description[:60]}...")
            print(f"    Downloads: {service.specifications.get('downloads', 0):,}")
        
        # Demo 5: Get storage modules
        print_subsection("Storage Modules")
        storage_services = await registry_client.get_storage_modules()
        
        print(f"Found {len(storage_services.services)} storage-related modules")
        for service in storage_services.services[:3]:
            print(f"  • {service.provider.value}: {service.service_name}")
            print(f"    Features: {', '.join(service.features)}")
        
        # Demo 6: Get AI/ML modules
        print_subsection("AI/ML Modules")
        ai_services = await registry_client.get_ai_modules()
        
        print(f"Found {len(ai_services.services)} AI/ML-related modules")
        for service in ai_services.services[:3]:
            print(f"  • {service.provider.value}: {service.service_name}")
            print(f"    Category: {service.category.value}")
        
    except RateLimitError as e:
        print(f"⚠️  Rate limit exceeded: {e}")
        print("   Try again later or implement rate limiting in your application")
    except CloudServiceError as e:
        print(f"❌ Registry API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await registry_client.close()


async def demo_terraform_cloud():
    """Demonstrate Terraform Cloud API functionality."""
    print_section("Terraform Cloud API Demo")
    
    # Check for required environment variables
    terraform_token = os.getenv('TERRAFORM_TOKEN')
    terraform_org = os.getenv('TERRAFORM_ORG')
    
    if not terraform_token:
        print("⚠️  TERRAFORM_TOKEN environment variable not set")
        print("   Terraform Cloud API features require authentication")
        print("   Set TERRAFORM_TOKEN to your Terraform Cloud API token to test these features")
        return
    
    if not terraform_org:
        print("⚠️  TERRAFORM_ORG environment variable not set")
        print("   Using 'demo-org' as default organization name")
        terraform_org = "demo-org"
    
    cloud_client = TerraformCloudClient(terraform_token, terraform_org)
    
    try:
        # Demo 1: Create a test workspace
        print_subsection("Creating Test Workspace")
        workspace_config = {
            "name": f"infra-mind-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "description": "Demo workspace created by InfraMind Terraform integration",
            "terraform_version": "1.5.0",
            "auto_apply": False,
            "queue_all_runs": False
        }
        
        print(f"Creating workspace: {workspace_config['name']}")
        workspace = await cloud_client.create_workspace(workspace_config)
        
        print("✅ Workspace created successfully!")
        print(f"   ID: {workspace['id']}")
        print(f"   Name: {workspace['name']}")
        print(f"   Terraform Version: {workspace['terraform_version']}")
        print(f"   Created: {workspace['created_at']}")
        
        # Demo 2: Simulate a plan run (this would normally require actual Terraform configuration)
        print_subsection("Simulating Plan Run")
        print("ℹ️  Note: This demo simulates a plan run without actual Terraform configuration")
        print("   In a real scenario, you would upload Terraform files to the workspace")
        
        try:
            plan_config = {
                "message": "Demo plan run from InfraMind",
                "is_destroy": False
            }
            
            print(f"Starting plan run for workspace: {workspace['id']}")
            plan_result = await cloud_client.run_plan(workspace['id'], plan_config)
            
            print("✅ Plan run initiated!")
            print(f"   Run ID: {plan_result['run_id']}")
            print(f"   Status: {plan_result['status']}")
            print(f"   Plan URL: {plan_result['plan_url']}")
            
            # Demo 3: Get cost estimation (if available)
            if plan_result.get('cost_estimation'):
                cost_data = plan_result['cost_estimation']
                if cost_data.get('monthly_cost'):
                    print(f"   Monthly Cost: ${cost_data['monthly_cost']} {cost_data.get('currency', 'USD')}")
                    if cost_data.get('delta_monthly_cost'):
                        print(f"   Cost Change: ${cost_data['delta_monthly_cost']}")
                else:
                    print("   Cost estimation not available for this run")
            
        except CloudServiceError as e:
            print(f"⚠️  Plan run simulation failed: {e}")
            print("   This is expected without actual Terraform configuration")
        
        # Demo 4: Direct cost estimation query
        print_subsection("Cost Estimation Query")
        print("ℹ️  Attempting to query cost estimation for a hypothetical run")
        
        try:
            cost_estimation = await cloud_client.get_cost_estimation("run-demo-123")
            if cost_estimation.get('cost_estimate') is None:
                print("   Cost estimation not available (expected for demo run)")
            else:
                print(f"   Monthly Cost: ${cost_estimation['monthly_cost']}")
                print(f"   Resources: {len(cost_estimation.get('resources', []))}")
        except CloudServiceError as e:
            print(f"   Cost estimation query result: {e}")
    
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please check your TERRAFORM_TOKEN environment variable")
    except CloudServiceError as e:
        print(f"❌ Terraform Cloud API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await cloud_client.close()


async def demo_unified_terraform_client():
    """Demonstrate the unified Terraform client."""
    print_section("Unified Terraform Client Demo")
    
    terraform_token = os.getenv('TERRAFORM_TOKEN')
    terraform_org = os.getenv('TERRAFORM_ORG', 'demo-org')
    
    # Create client (works with or without token)
    client = TerraformClient(terraform_token, terraform_org)
    
    try:
        # Demo 1: Get compute services
        print_subsection("Compute Services via Unified Client")
        compute_services = await client.get_compute_services()
        
        print(f"Found {len(compute_services.services)} compute services")
        
        # Group by provider
        by_provider = {}
        for service in compute_services.services:
            provider = service.provider.value
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(service)
        
        for provider, services in by_provider.items():
            print(f"  {provider}: {len(services)} services")
            for service in services[:2]:  # Show first 2 per provider
                print(f"    • {service.service_name}")
        
        # Demo 2: Get providers through unified client
        print_subsection("Providers via Unified Client")
        providers = await client.get_providers(namespace="hashicorp")
        
        print(f"Found {providers['total_count']} HashiCorp providers")
        for provider in providers['providers'][:3]:
            print(f"  • {provider['name']}: {provider['downloads']:,} downloads")
        
        # Demo 3: Get modules through unified client
        print_subsection("AWS Modules via Unified Client")
        modules = await client.get_modules(provider="aws")
        
        print(f"Found {modules['total_count']} AWS modules")
        for module in modules['modules'][:3]:
            print(f"  • {module['namespace']}/{module['name']}")
            print(f"    Version: {module['version']} | Verified: {module['verified']}")
        
        # Demo 4: Cost estimation (if token available)
        if terraform_token:
            print_subsection("Cost Estimation via Unified Client")
            try:
                cost_data = await client.get_service_pricing("run-demo-123")
                print("Cost estimation query completed")
                if cost_data.get('cost_estimate') is None:
                    print("  No cost data available for demo run (expected)")
                else:
                    print(f"  Monthly cost: ${cost_data['monthly_cost']}")
            except CloudServiceError as e:
                print(f"  Cost estimation result: {e}")
        else:
            print_subsection("Cost Estimation (Skipped)")
            print("  TERRAFORM_TOKEN not provided - skipping cost estimation demo")
    
    except Exception as e:
        print(f"❌ Unified client error: {e}")


async def demo_caching_behavior():
    """Demonstrate caching behavior of Terraform clients."""
    print_section("Caching Behavior Demo")
    
    client = TerraformClient()
    
    try:
        print_subsection("Cache Performance Test")
        
        # First call - should fetch from API
        print("First call to get_compute_services() - fetching from API...")
        start_time = datetime.now()
        result1 = await client.get_compute_services()
        first_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"  ✅ First call completed in {first_duration:.2f} seconds")
        print(f"  Found {len(result1.services)} services")
        
        # Second call - should use cache
        print("\nSecond call to get_compute_services() - using cache...")
        start_time = datetime.now()
        result2 = await client.get_compute_services()
        second_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"  ✅ Second call completed in {second_duration:.2f} seconds")
        print(f"  Found {len(result2.services)} services")
        
        # Compare results
        if first_duration > second_duration:
            speedup = first_duration / second_duration
            print(f"  🚀 Cache provided {speedup:.1f}x speedup!")
        
        print(f"\nCache metadata:")
        print(f"  Source: {result2.metadata.get('source', 'unknown')}")
        print(f"  Cache TTL: 1 hour for modules")
        
    except Exception as e:
        print(f"❌ Caching demo error: {e}")


async def main():
    """Run all Terraform API demos."""
    print("🚀 InfraMind Terraform API Integration Demo")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check environment
    terraform_token = os.getenv('TERRAFORM_TOKEN')
    terraform_org = os.getenv('TERRAFORM_ORG')
    
    print(f"\nEnvironment:")
    print(f"  TERRAFORM_TOKEN: {'✅ Set' if terraform_token else '❌ Not set'}")
    print(f"  TERRAFORM_ORG: {terraform_org or '❌ Not set'}")
    
    if not terraform_token:
        print(f"\n💡 To test Terraform Cloud features, set environment variables:")
        print(f"   export TERRAFORM_TOKEN='your-terraform-cloud-token'")
        print(f"   export TERRAFORM_ORG='your-organization-name'")
    
    # Run demos
    await demo_terraform_registry()
    await demo_terraform_cloud()
    await demo_unified_terraform_client()
    await demo_caching_behavior()
    
    print_section("Demo Complete")
    print("✅ All Terraform API demos completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Terraform Registry API - Provider and module information")
    print("  • Terraform Cloud API - Cost estimation and workspace management")
    print("  • Unified client interface - Simplified access to both APIs")
    print("  • Caching behavior - Performance optimization")
    print("  • Error handling - Robust error management")
    print("  • Multi-cloud support - AWS, Azure, GCP modules")
    
    print(f"\n📚 Next Steps:")
    print(f"  • Integrate with InfraMind agents for infrastructure recommendations")
    print(f"  • Use cost estimation data for budget planning")
    print(f"  • Leverage module information for infrastructure-as-code suggestions")
    print(f"  • Implement real-time pricing updates in recommendations")


if __name__ == "__main__":
    asyncio.run(main())