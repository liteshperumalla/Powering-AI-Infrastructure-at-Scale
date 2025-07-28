#!/usr/bin/env python3
"""
Demo script showcasing the complete Azure API suite implementation.

This demonstrates the enhanced Azure integration features including:
- Resource Manager API with real authentication support
- AKS API with real cluster data integration
- Machine Learning API with real workspace data
- Cost Management API with real cost analysis
- Advanced integration features like multi-region analysis and optimization recommendations
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.cloud.azure import AzureClient

async def demo_azure_resource_manager():
    """Demonstrate Azure Resource Manager capabilities."""
    print("\n" + "="*60)
    print("AZURE RESOURCE MANAGER DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("🔍 Getting Resource Groups...")
    resource_groups = await client.get_resource_groups("eastus")
    print(f"Found {len(resource_groups.services)} resource management services")
    
    # Show sample resource group
    if resource_groups.services:
        sample = resource_groups.services[0]
        print(f"\n📁 Sample Resource Group:")
        print(f"   Name: {sample.service_name}")
        print(f"   Region: {sample.region}")
        print(f"   Features: {', '.join(sample.features[:3])}...")
    
    print("\n💡 Getting Resource Recommendations...")
    recommendations = await client.get_resource_recommendations("all")
    print(f"Found {recommendations.get('total_recommendations', 0)} optimization recommendations")
    
    # Show sample recommendation
    if recommendations.get('recommendations'):
        sample_rec = recommendations['recommendations'][0]
        print(f"\n🎯 Sample Recommendation:")
        print(f"   Title: {sample_rec['title']}")
        print(f"   Impact: {sample_rec['impact']}")
        print(f"   Category: {sample_rec['category']}")
    
    print("\n❤️  Getting Resource Health...")
    health = await client.get_resource_health()
    print(f"Monitoring {health.get('total_resources', 0)} resources")

async def demo_azure_aks():
    """Demonstrate Azure Kubernetes Service capabilities."""
    print("\n" + "="*60)
    print("AZURE KUBERNETES SERVICE (AKS) DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("☸️  Getting AKS Services...")
    aks_services = await client.get_aks_services("eastus")
    print(f"Found {len(aks_services.services)} AKS services")
    
    # Show control plane and node pools
    control_plane = None
    node_pools = []
    
    for service in aks_services.services:
        if "Control Plane" in service.service_name:
            control_plane = service
        elif "Node Pool" in service.service_name:
            node_pools.append(service)
    
    if control_plane:
        print(f"\n🎛️  Control Plane:")
        print(f"   Service: {control_plane.service_name}")
        print(f"   Pricing: ${control_plane.hourly_price}/hour ({control_plane.pricing_model})")
        print(f"   Max Nodes: {control_plane.specifications.get('max_nodes_per_cluster', 'N/A')}")
        print(f"   SLA: {control_plane.specifications.get('sla', 'N/A')}")
    
    print(f"\n🖥️  Node Pools ({len(node_pools)} available):")
    for i, node_pool in enumerate(node_pools[:3]):  # Show first 3
        print(f"   {i+1}. {node_pool.service_name}")
        print(f"      VM Size: {node_pool.specifications.get('vm_size', 'N/A')}")
        print(f"      vCPUs: {node_pool.specifications.get('vcpus', 'N/A')}")
        print(f"      Memory: {node_pool.specifications.get('memory_gb', 'N/A')} GB")
        print(f"      Pricing: ${node_pool.hourly_price}/hour")

async def demo_azure_machine_learning():
    """Demonstrate Azure Machine Learning capabilities."""
    print("\n" + "="*60)
    print("AZURE MACHINE LEARNING DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("🤖 Getting ML Services...")
    ml_services = await client.get_machine_learning_services("eastus")
    print(f"Found {len(ml_services.services)} ML services")
    
    # Show workspace and compute instances
    workspace = None
    compute_instances = []
    
    for service in ml_services.services:
        if "Workspace" in service.service_name:
            workspace = service
        elif "Compute" in service.service_name:
            compute_instances.append(service)
    
    if workspace:
        print(f"\n🏢 ML Workspace:")
        print(f"   Service: {workspace.service_name}")
        print(f"   Pricing: ${workspace.hourly_price}/hour ({workspace.pricing_model})")
        print(f"   Storage: {workspace.specifications.get('storage_included', 'N/A')}")
        print(f"   Features: {', '.join(workspace.features[:4])}...")
    
    print(f"\n💻 Compute Instances ({len(compute_instances)} available):")
    for i, compute in enumerate(compute_instances[:3]):  # Show first 3
        print(f"   {i+1}. {compute.service_name}")
        specs = compute.specifications
        print(f"      vCPUs: {specs.get('vcpus', 'N/A')}")
        print(f"      Memory: {specs.get('memory_gb', 'N/A')} GB")
        print(f"      GPU: {specs.get('gpu_type', 'None')}")
        print(f"      Pricing: ${compute.hourly_price}/hour")

async def demo_azure_cost_management():
    """Demonstrate Azure Cost Management capabilities."""
    print("\n" + "="*60)
    print("AZURE COST MANAGEMENT DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("💰 Getting Cost Analysis...")
    cost_analysis = await client.get_cost_analysis("subscription", "month")
    print(f"Total Monthly Cost: ${cost_analysis.get('total_cost', 0):,.2f} {cost_analysis.get('currency', 'USD')}")
    
    # Show cost breakdown
    cost_by_service = cost_analysis.get('cost_by_service', {})
    print(f"\n📊 Top Services by Cost:")
    for i, (service, cost) in enumerate(sorted(cost_by_service.items(), key=lambda x: x[1], reverse=True)[:5]):
        print(f"   {i+1}. {service}: ${cost:,.2f}")
    
    # Show optimization opportunities
    opportunities = cost_analysis.get('cost_optimization_opportunities', [])
    total_savings = sum(opp['potential_savings'] for opp in opportunities)
    print(f"\n💡 Optimization Opportunities (${total_savings:,.2f} potential savings):")
    for i, opp in enumerate(opportunities[:3]):
        print(f"   {i+1}. {opp['category']}: ${opp['potential_savings']:,.2f}")
        print(f"      {opp['description']}")
        print(f"      Effort: {opp['implementation_effort']}, Risk: {opp['risk_level']}")
    
    print("\n🚨 Getting Budget Alerts...")
    budget_alerts = await client.get_budget_alerts()
    print(f"Configured Budgets: {budget_alerts.get('total_budgets', 0)}")
    print(f"Active Alerts: {budget_alerts.get('active_alerts', 0)}")
    
    summary = budget_alerts.get('summary', {})
    if summary:
        print(f"Total Budget: ${summary.get('total_budget_amount', 0):,.2f}")
        print(f"Total Spent: ${summary.get('total_spent', 0):,.2f}")
        print(f"Highest Utilization: {summary.get('highest_utilization', 0):.1f}%")
    
    print("\n📈 Getting Cost Recommendations...")
    cost_recommendations = await client.get_cost_recommendations()
    print(f"Total Recommendations: {cost_recommendations.get('total_recommendations', 0)}")
    print(f"Potential Savings: ${cost_recommendations.get('total_potential_savings', 0):,.2f}")
    
    # Show recommendation categories
    categories = cost_recommendations.get('categories', {})
    print("Categories:")
    for category, count in categories.items():
        if count > 0:
            print(f"   {category.replace('_', ' ').title()}: {count}")

async def demo_comprehensive_analysis():
    """Demonstrate comprehensive Azure analysis."""
    print("\n" + "="*60)
    print("COMPREHENSIVE AZURE ANALYSIS DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("🔍 Running Comprehensive Analysis...")
    analysis = await client.get_comprehensive_analysis("eastus")
    
    print(f"Analysis completed at: {analysis.get('timestamp')}")
    print(f"Region: {analysis.get('region')}")
    
    # Show services summary
    services = analysis.get('services', {})
    print(f"\n📋 Services Analyzed:")
    service_count = 0
    for service_type, service_data in services.items():
        if service_data and hasattr(service_data, 'services'):
            count = len(service_data.services)
            service_count += count
            print(f"   {service_type.title()}: {count} services")
        elif service_data:
            print(f"   {service_type.title()}: Available")
    
    summary = analysis.get('summary', {})
    print(f"\n📊 Summary:")
    print(f"   Total Services: {summary.get('total_services_analyzed', service_count)}")
    print(f"   Errors: {summary.get('errors_encountered', 0)}")
    print(f"   Data Freshness: {summary.get('data_freshness', 'unknown')}")
    
    print("\n🎯 Getting Optimization Recommendations...")
    optimization = await client.get_optimization_recommendations()
    
    cost_opt = optimization.get('cost_optimization', {})
    print(f"Cost Optimization Savings: ${cost_opt.get('total_potential_savings', 0):,.2f}")
    
    priority_actions = optimization.get('priority_actions', [])
    print(f"Priority Actions: {len(priority_actions)}")
    
    for category in ['cost_optimization', 'performance_optimization', 'security_optimization', 'reliability_optimization']:
        category_data = optimization.get(category, {})
        recommendations = category_data.get('recommendations', [])
        if recommendations:
            print(f"   {category.replace('_', ' ').title()}: {len(recommendations)} recommendations")

async def demo_security_posture():
    """Demonstrate security posture analysis."""
    print("\n" + "="*60)
    print("AZURE SECURITY POSTURE DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("🔒 Analyzing Security Posture...")
    security_analysis = await client.get_security_posture_analysis()
    
    print(f"Overall Security Score: {security_analysis.get('overall_score', 0)}/100")
    
    # Show security categories
    categories = ['compliance_status', 'threat_detection', 'access_management', 'data_protection', 'network_security']
    print(f"\n🛡️  Security Categories:")
    for category in categories:
        category_data = security_analysis.get(category, {})
        status = "✓ Available" if category_data else "⚠️ Not Available"
        print(f"   {category.replace('_', ' ').title()}: {status}")
    
    # Show priority actions
    priority_actions = security_analysis.get('priority_actions', [])
    print(f"\n🚨 Priority Security Actions ({len(priority_actions)}):")
    for i, action in enumerate(priority_actions[:3]):
        print(f"   {i+1}. {action.get('title', 'No title')}")
        print(f"      Priority: {action.get('priority', 'unknown')}")
        print(f"      Category: {action.get('category', 'unknown')}")

async def demo_advanced_features():
    """Demonstrate advanced Azure integration features."""
    print("\n" + "="*60)
    print("ADVANCED AZURE FEATURES DEMO")
    print("="*60)
    
    client = AzureClient(region="eastus")
    
    print("🌍 Multi-Region Analysis...")
    regions = ["eastus", "westus2", "northeurope"]
    try:
        multi_region_analysis = await client.get_multi_region_analysis(regions)
        
        print(f"Regions Analyzed: {len(multi_region_analysis.get('regions_analyzed', []))}")
        
        metadata = multi_region_analysis.get('metadata', {})
        print(f"Successful Regions: {metadata.get('successful_regions', 0)}")
        print(f"Failed Regions: {metadata.get('failed_regions', 0)}")
        
        # Show cross-region insights
        insights = multi_region_analysis.get('cross_region_insights', {})
        cost_comparison = insights.get('cost_comparison', {})
        if cost_comparison:
            print(f"\n💰 Cost Comparison by Region:")
            for region, cost_data in cost_comparison.items():
                print(f"   {region}: ${cost_data.get('total_cost', 0):,.2f}")
        
        recommendations = multi_region_analysis.get('recommendations', [])
        print(f"\n📋 Multi-Region Recommendations: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:2]):
            print(f"   {i+1}. {rec.get('title', 'No title')}")
            print(f"      Type: {rec.get('type', 'unknown')}")
            print(f"      Priority: {rec.get('priority', 'unknown')}")
    
    except Exception as e:
        print(f"Multi-region analysis encountered an issue: {str(e)}")
    
    print(f"\n📊 Resource Usage Metrics...")
    try:
        # Demo resource usage metrics
        resource_id = "/subscriptions/demo-sub/resourceGroups/demo-rg/providers/Microsoft.Compute/virtualMachines/demo-vm"
        usage_metrics = await client.cost_management_client.get_resource_usage_metrics(
            resource_id, "Percentage CPU", "24h"
        )
        
        stats = usage_metrics.get('statistics', {})
        print(f"CPU Usage Statistics (24h):")
        print(f"   Average: {stats.get('average', 0):.1f}%")
        print(f"   Minimum: {stats.get('minimum', 0):.1f}%")
        print(f"   Maximum: {stats.get('maximum', 0):.1f}%")
        print(f"   Latest: {stats.get('latest', 0):.1f}%")
        
        analysis = usage_metrics.get('utilization_analysis', {})
        print(f"   Optimization Potential: {analysis.get('optimization_potential', 'unknown')}")
        print(f"   Underutilized Periods: {analysis.get('underutilized_periods', 0)}")
        print(f"   Peak Periods: {analysis.get('peak_periods', 0)}")
    
    except Exception as e:
        print(f"Resource usage metrics encountered an issue: {str(e)}")

async def main():
    """Run the complete Azure API suite demo."""
    print("AZURE API SUITE COMPLETE DEMO")
    print("="*60)
    print(f"Demo started at: {datetime.now(timezone.utc).isoformat()}")
    print("\nThis demo showcases the enhanced Azure integration features:")
    print("• Resource Manager API with real authentication support")
    print("• AKS API with real cluster data integration")
    print("• Machine Learning API with real workspace data")
    print("• Cost Management API with real cost analysis")
    print("• Advanced features like multi-region analysis and optimization")
    
    demos = [
        ("Azure Resource Manager", demo_azure_resource_manager),
        ("Azure Kubernetes Service", demo_azure_aks),
        ("Azure Machine Learning", demo_azure_machine_learning),
        ("Azure Cost Management", demo_azure_cost_management),
        ("Comprehensive Analysis", demo_comprehensive_analysis),
        ("Security Posture Analysis", demo_security_posture),
        ("Advanced Features", demo_advanced_features),
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ {demo_name} demo failed: {str(e)}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("✅ Azure API suite demonstration completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Real-time Azure service data integration")
    print("• Comprehensive cost analysis and optimization")
    print("• Multi-service orchestration and recommendations")
    print("• Advanced security and compliance analysis")
    print("• Multi-region comparison and insights")
    print("• Resource usage monitoring and optimization")
    
    print(f"\nDemo completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())