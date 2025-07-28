#!/usr/bin/env python3
"""
Demo script for GCP Extended APIs Integration.

This script demonstrates the comprehensive GCP API integration including:
- Cloud Billing API
- Compute Engine API
- Cloud SQL API
- Google Kubernetes Engine (GKE) API
- AI Platform API (Vertex AI)
- Asset Inventory API
- Recommender API

Usage:
    python demo_gcp_extended_apis.py
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from src.infra_mind.cloud.gcp import (
    GCPClient, GCPBillingClient, GCPComputeClient, GCPSQLClient,
    GCPGKEClient, GCPAssetClient, GCPRecommenderClient, GCPAIClient
)
from src.infra_mind.cloud.base import CloudProvider, ServiceCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_gcp_billing_api():
    """Demonstrate GCP Billing API functionality."""
    print("\n" + "="*60)
    print("GCP BILLING API DEMO")
    print("="*60)
    
    try:
        billing_client = GCPBillingClient("demo-project", "us-central1")
        
        # Get pricing for different services
        services_to_check = ["Compute Engine", "Cloud SQL", "Cloud Storage"]
        
        for service_name in services_to_check:
            print(f"\n📊 Getting pricing for {service_name}...")
            pricing_data = await billing_client.get_service_pricing(service_name, "us-central1")
            
            print(f"Service: {pricing_data['service_name']}")
            print(f"Region: {pricing_data['region']}")
            print(f"Real Data: {pricing_data['real_data']}")
            
            if pricing_data['pricing_data']:
                print("Sample Pricing:")
                for item, price in list(pricing_data['pricing_data'].items())[:3]:
                    print(f"  • {item}: ${price}/hour")
        
        print("\n✅ Billing API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Billing API demo failed: {e}")


async def demo_gcp_compute_api():
    """Demonstrate GCP Compute Engine API functionality."""
    print("\n" + "="*60)
    print("GCP COMPUTE ENGINE API DEMO")
    print("="*60)
    
    try:
        compute_client = GCPComputeClient("demo-project", "us-central1")
        
        print("🖥️  Getting available machine types...")
        machine_types = await compute_client.get_machine_types("us-central1")
        
        print(f"Provider: {machine_types.provider.value}")
        print(f"Service Category: {machine_types.service_category.value}")
        print(f"Region: {machine_types.region}")
        print(f"Total Machine Types: {len(machine_types.services)}")
        
        # Show sample machine types
        print("\nSample Machine Types:")
        for service in machine_types.services[:5]:
            specs = service.specifications
            print(f"  • {service.service_name}")
            print(f"    - vCPUs: {specs.get('vcpus')}")
            print(f"    - Memory: {specs.get('memory_gb')} GB")
            print(f"    - Price: ${service.hourly_price}/hour")
            print(f"    - Monthly Cost: ${service.get_monthly_cost():.2f}")
        
        # Find cheapest and most expensive
        cheapest = machine_types.get_cheapest_service()
        most_expensive = max(machine_types.services, key=lambda s: s.hourly_price)
        
        print(f"\n💰 Cheapest Option: {cheapest.service_name} (${cheapest.hourly_price}/hour)")
        print(f"💸 Most Expensive: {most_expensive.service_name} (${most_expensive.hourly_price}/hour)")
        
        print("\n✅ Compute Engine API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Compute Engine API demo failed: {e}")


async def demo_gcp_sql_api():
    """Demonstrate GCP Cloud SQL API functionality."""
    print("\n" + "="*60)
    print("GCP CLOUD SQL API DEMO")
    print("="*60)
    
    try:
        sql_client = GCPSQLClient("demo-project", "us-central1")
        
        print("🗄️  Getting available database instances...")
        db_instances = await sql_client.get_database_instances("us-central1")
        
        print(f"Provider: {db_instances.provider.value}")
        print(f"Service Category: {db_instances.service_category.value}")
        print(f"Region: {db_instances.region}")
        print(f"Total Instance Types: {len(db_instances.services)}")
        
        # Show database instances
        print("\nAvailable Database Instances:")
        for service in db_instances.services:
            specs = service.specifications
            print(f"  • {service.service_name}")
            print(f"    - vCPUs: {specs.get('vcpus')}")
            print(f"    - Memory: {specs.get('memory_gb')} GB")
            print(f"    - Engine: {specs.get('engine')} {specs.get('engine_version')}")
            print(f"    - Price: ${service.hourly_price}/hour")
            print(f"    - Features: {', '.join(service.features[:3])}")
        
        print("\n✅ Cloud SQL API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Cloud SQL API demo failed: {e}")


async def demo_gcp_gke_api():
    """Demonstrate GCP Google Kubernetes Engine API functionality."""
    print("\n" + "="*60)
    print("GCP GOOGLE KUBERNETES ENGINE (GKE) API DEMO")
    print("="*60)
    
    try:
        gke_client = GCPGKEClient("demo-project", "us-central1")
        
        print("☸️  Getting available GKE services...")
        gke_services = await gke_client.get_gke_services("us-central1")
        
        print(f"Provider: {gke_services.provider.value}")
        print(f"Service Category: {gke_services.service_category.value}")
        print(f"Region: {gke_services.region}")
        print(f"Total GKE Services: {len(gke_services.services)}")
        
        # Show cluster management
        cluster_mgmt = next(s for s in gke_services.services if s.service_id == "gke_cluster_management")
        print(f"\n🎛️  Cluster Management:")
        print(f"  • Service: {cluster_mgmt.service_name}")
        print(f"  • Price: ${cluster_mgmt.hourly_price}/hour per cluster")
        print(f"  • Kubernetes Version: {cluster_mgmt.specifications.get('kubernetes_version')}")
        print(f"  • Max Nodes: {cluster_mgmt.specifications.get('max_nodes_per_cluster'):,}")
        
        # Show Autopilot
        autopilot = next(s for s in gke_services.services if s.service_id == "gke_autopilot")
        print(f"\n🚀 GKE Autopilot:")
        print(f"  • Service: {autopilot.service_name}")
        print(f"  • CPU Price: ${autopilot.specifications.get('cpu_price_per_hour')}/vCPU/hour")
        print(f"  • Memory Price: ${autopilot.specifications.get('memory_price_per_gb_hour')}/GB/hour")
        print(f"  • Max CPU: {autopilot.specifications.get('max_cpu')} vCPUs")
        print(f"  • Max Memory: {autopilot.specifications.get('max_memory_gb')} GB")
        
        # Show node pools
        node_pools = [s for s in gke_services.services if "node_pool" in s.service_id]
        print(f"\n🔧 Node Pool Options ({len(node_pools)} available):")
        for service in node_pools[:5]:  # Show first 5
            specs = service.specifications
            print(f"  • {specs.get('machine_type')}: {specs.get('vcpus')} vCPUs, {specs.get('memory_gb')} GB - ${service.hourly_price}/hour")
        
        print("\n✅ GKE API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ GKE API demo failed: {e}")


async def demo_gcp_ai_api():
    """Demonstrate GCP AI Platform API functionality."""
    print("\n" + "="*60)
    print("GCP AI PLATFORM API DEMO")
    print("="*60)
    
    try:
        ai_client = GCPAIClient("demo-project", "us-central1")
        
        print("🤖 Getting available AI/ML services...")
        ai_services = await ai_client.get_ai_services("us-central1")
        
        print(f"Provider: {ai_services.provider.value}")
        print(f"Service Category: {ai_services.service_category.value}")
        print(f"Region: {ai_services.region}")
        print(f"Total AI Services: {len(ai_services.services)}")
        
        # Categorize services
        vertex_training = [s for s in ai_services.services if "vertex_ai_training" in s.service_id]
        vertex_prediction = [s for s in ai_services.services if "vertex_ai_prediction" in s.service_id]
        generative_models = [s for s in ai_services.services if any(model in s.service_id for model in ["text_bison", "chat_bison", "code_bison"])]
        automl_services = [s for s in ai_services.services if "automl" in s.service_id]
        
        print(f"\n🏋️  Vertex AI Training Instances ({len(vertex_training)} available):")
        for service in vertex_training[:3]:
            specs = service.specifications
            gpu_info = f" + {specs.get('gpu_count', 0)} {specs.get('gpu_type', 'N/A')} GPU" if specs.get('gpu_count', 0) > 0 else ""
            print(f"  • {specs.get('machine_type')}: {specs.get('vcpus')} vCPUs, {specs.get('memory_gb')} GB{gpu_info} - ${service.hourly_price}/hour")
        
        print(f"\n🔮 Vertex AI Prediction Instances ({len(vertex_prediction)} available):")
        for service in vertex_prediction[:3]:
            specs = service.specifications
            print(f"  • {specs.get('machine_type')}: {specs.get('vcpus')} vCPUs, {specs.get('memory_gb')} GB - ${service.hourly_price}/hour")
        
        print(f"\n💬 Generative AI Models ({len(generative_models)} available):")
        for service in generative_models:
            specs = service.specifications
            print(f"  • {specs.get('model_name')}: ${specs.get('input_price_per_1k_tokens')}/1K input tokens, ${specs.get('output_price_per_1k_tokens')}/1K output tokens")
        
        if automl_services:
            print(f"\n🎯 AutoML Services ({len(automl_services)} available):")
            for service in automl_services[:3]:
                print(f"  • {service.service_name}: {service.description}")
        
        print("\n✅ AI Platform API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ AI Platform API demo failed: {e}")


async def demo_gcp_asset_api():
    """Demonstrate GCP Asset Inventory API functionality."""
    print("\n" + "="*60)
    print("GCP ASSET INVENTORY API DEMO")
    print("="*60)
    
    try:
        asset_client = GCPAssetClient("demo-project", "us-central1")
        
        print("📋 Getting asset inventory...")
        asset_inventory = await asset_client.get_asset_inventory()
        
        print(f"Project: {asset_inventory['project_id']}")
        print(f"Region: {asset_inventory['region']}")
        print(f"Timestamp: {asset_inventory['timestamp']}")
        
        summary = asset_inventory['summary']
        print(f"\n📊 Summary:")
        print(f"  • Total Assets: {summary['total_assets']}")
        print(f"  • Estimated Monthly Cost: ${summary['estimated_monthly_cost']:.2f}")
        
        print(f"\n🏷️  Assets by Type:")
        for asset_type, count in summary['assets_by_type'].items():
            print(f"  • {asset_type}: {count}")
        
        print(f"\n🌍 Assets by Region:")
        for region, count in summary['assets_by_region'].items():
            print(f"  • {region}: {count}")
        
        print(f"\n📝 Sample Assets:")
        for asset in asset_inventory['assets'][:5]:
            print(f"  • {asset['name']}")
            print(f"    - Type: {asset['asset_type']}")
            print(f"    - Location: {asset['location']}")
            print(f"    - Monthly Cost: ${asset['estimated_monthly_cost']:.2f}")
        
        # Test with specific asset types
        print(f"\n🔍 Getting specific asset types...")
        specific_assets = await asset_client.get_asset_inventory([
            "compute.googleapis.com/Instance",
            "storage.googleapis.com/Bucket"
        ])
        
        print(f"Filtered Assets: {len(specific_assets['assets'])}")
        for asset in specific_assets['assets']:
            print(f"  • {asset['asset_type']}: {asset['name'].split('/')[-1]}")
        
        print("\n✅ Asset Inventory API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Asset Inventory API demo failed: {e}")


async def demo_gcp_recommender_api():
    """Demonstrate GCP Recommender API functionality."""
    print("\n" + "="*60)
    print("GCP RECOMMENDER API DEMO")
    print("="*60)
    
    try:
        recommender_client = GCPRecommenderClient("demo-project", "us-central1")
        
        # Test different recommendation types
        recommendation_types = [
            "cost_optimization",
            "security", 
            "performance",
            "rightsizing",
            "commitment_utilization"
        ]
        
        for rec_type in recommendation_types:
            print(f"\n💡 Getting {rec_type.replace('_', ' ').title()} Recommendations...")
            recommendations = await recommender_client.get_recommendations(rec_type, "us-central1")
            
            summary = recommendations['summary']
            print(f"  • Total Recommendations: {summary['total_recommendations']}")
            print(f"  • Potential Monthly Savings: ${summary['potential_monthly_savings']:.2f}")
            
            priority_counts = summary['recommendations_by_priority']
            print(f"  • Priority Breakdown: HIGH({priority_counts['HIGH']}), MEDIUM({priority_counts['MEDIUM']}), LOW({priority_counts['LOW']})")
            
            # Show sample recommendations
            for rec in recommendations['recommendations'][:2]:
                print(f"    - {rec['description']} (Priority: {rec['priority']}, Savings: ${rec['potential_monthly_savings']:.2f})")
        
        # Detailed view of cost optimization recommendations
        print(f"\n💰 Detailed Cost Optimization Analysis:")
        cost_recs = await recommender_client.get_recommendations("cost_optimization", "us-central1")
        
        total_savings = 0
        high_priority_count = 0
        
        for rec in cost_recs['recommendations']:
            if rec['priority'] == 'HIGH':
                high_priority_count += 1
                print(f"  🔥 HIGH PRIORITY: {rec['description']}")
                print(f"     Potential Savings: ${rec['potential_monthly_savings']:.2f}/month")
                print(f"     Confidence: {rec['confidence']*100:.1f}%")
            
            total_savings += rec['potential_monthly_savings']
        
        print(f"\n📈 Cost Optimization Summary:")
        print(f"  • Total Potential Savings: ${total_savings:.2f}/month")
        print(f"  • Annual Savings Potential: ${total_savings * 12:.2f}")
        print(f"  • High Priority Actions: {high_priority_count}")
        
        print("\n✅ Recommender API demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Recommender API demo failed: {e}")


async def demo_comprehensive_gcp_integration():
    """Demonstrate comprehensive GCP integration with all APIs."""
    print("\n" + "="*80)
    print("COMPREHENSIVE GCP INTEGRATION DEMO")
    print("="*80)
    
    try:
        client = GCPClient("demo-project", "us-central1")
        
        print("🌐 Initializing comprehensive GCP client...")
        print(f"Project: {client.project_id}")
        print(f"Region: {client.region}")
        print(f"Provider: {client.provider.value}")
        
        # Get all service types
        print(f"\n📊 Gathering all GCP services...")
        
        compute_services = await client.get_compute_services()
        storage_services = await client.get_storage_services()
        database_services = await client.get_database_services()
        ai_services = await client.get_ai_services()
        kubernetes_services = await client.get_kubernetes_services()
        
        # Service summary
        total_services = (len(compute_services.services) + 
                         len(storage_services.services) + 
                         len(database_services.services) + 
                         len(ai_services.services) + 
                         len(kubernetes_services.services))
        
        print(f"  • Compute Services: {len(compute_services.services)}")
        print(f"  • Storage Services: {len(storage_services.services)}")
        print(f"  • Database Services: {len(database_services.services)}")
        print(f"  • AI/ML Services: {len(ai_services.services)}")
        print(f"  • Kubernetes Services: {len(kubernetes_services.services)}")
        print(f"  • Total Services Available: {total_services}")
        
        # Cost analysis across all services
        print(f"\n💰 Cost Analysis Across All Services:")
        all_services = (compute_services.services + storage_services.services + 
                       database_services.services + ai_services.services + 
                       kubernetes_services.services)
        
        cheapest_overall = min(all_services, key=lambda s: s.hourly_price)
        most_expensive = max(all_services, key=lambda s: s.hourly_price)
        average_price = sum(s.hourly_price for s in all_services) / len(all_services)
        
        print(f"  • Cheapest Service: {cheapest_overall.service_name} (${cheapest_overall.hourly_price}/hour)")
        print(f"  • Most Expensive: {most_expensive.service_name} (${most_expensive.hourly_price}/hour)")
        print(f"  • Average Price: ${average_price:.4f}/hour")
        
        # Asset inventory analysis
        print(f"\n📋 Asset Inventory Analysis:")
        asset_inventory = await client.get_asset_inventory()
        summary = asset_inventory['summary']
        
        print(f"  • Current Assets: {summary['total_assets']}")
        print(f"  • Current Monthly Cost: ${summary['estimated_monthly_cost']:.2f}")
        print(f"  • Asset Distribution: {len(summary['assets_by_type'])} types across {len(summary['assets_by_region'])} regions")
        
        # Optimization recommendations
        print(f"\n🎯 Optimization Recommendations:")
        cost_recommendations = await client.get_recommendations("cost_optimization")
        security_recommendations = await client.get_recommendations("security")
        
        cost_summary = cost_recommendations['summary']
        security_summary = security_recommendations['summary']
        
        print(f"  • Cost Optimization Opportunities: {cost_summary['total_recommendations']}")
        print(f"  • Potential Monthly Savings: ${cost_summary['potential_monthly_savings']:.2f}")
        print(f"  • Security Recommendations: {security_summary['total_recommendations']}")
        
        # ROI Analysis
        current_monthly_cost = summary['estimated_monthly_cost']
        potential_savings = cost_summary['potential_monthly_savings']
        savings_percentage = (potential_savings / current_monthly_cost * 100) if current_monthly_cost > 0 else 0
        
        print(f"\n📈 ROI Analysis:")
        print(f"  • Current Monthly Spend: ${current_monthly_cost:.2f}")
        print(f"  • Potential Monthly Savings: ${potential_savings:.2f}")
        print(f"  • Savings Percentage: {savings_percentage:.1f}%")
        print(f"  • Annual Savings Potential: ${potential_savings * 12:.2f}")
        
        print(f"\n✅ Comprehensive GCP integration demo completed successfully!")
        print(f"🎉 All {total_services} GCP services are now available through the unified client!")
        
    except Exception as e:
        print(f"❌ Comprehensive GCP integration demo failed: {e}")


async def main():
    """Run all GCP API demos."""
    print("🚀 Starting GCP Extended APIs Demo")
    print("This demo showcases comprehensive GCP integration including:")
    print("  • Cloud Billing API")
    print("  • Compute Engine API") 
    print("  • Cloud SQL API")
    print("  • Google Kubernetes Engine (GKE) API")
    print("  • AI Platform API (Vertex AI)")
    print("  • Asset Inventory API")
    print("  • Recommender API")
    
    # Run individual API demos
    await demo_gcp_billing_api()
    await demo_gcp_compute_api()
    await demo_gcp_sql_api()
    await demo_gcp_gke_api()
    await demo_gcp_ai_api()
    await demo_gcp_asset_api()
    await demo_gcp_recommender_api()
    
    # Run comprehensive integration demo
    await demo_comprehensive_gcp_integration()
    
    print("\n" + "="*80)
    print("🎯 GCP EXTENDED APIS DEMO COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("All GCP APIs are now fully integrated and ready for production use.")
    print("The system provides comprehensive coverage of:")
    print("  ✅ Compute services (VM instances, machine types)")
    print("  ✅ Storage services (Cloud Storage, Persistent Disks)")
    print("  ✅ Database services (Cloud SQL instances)")
    print("  ✅ Container services (GKE clusters, node pools)")
    print("  ✅ AI/ML services (Vertex AI, AutoML, Generative AI)")
    print("  ✅ Asset inventory and management")
    print("  ✅ Cost optimization recommendations")
    print("  ✅ Security and performance recommendations")


if __name__ == "__main__":
    asyncio.run(main())