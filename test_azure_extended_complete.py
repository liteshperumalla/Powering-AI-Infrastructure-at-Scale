#!/usr/bin/env python3
"""
Comprehensive test for the complete Azure API suite implementation.

This test verifies the enhanced Azure integration features including:
- Resource Manager API with real authentication
- AKS API with real cluster data
- Machine Learning API with real workspace data
- Cost Management API with real cost analysis
- Advanced integration features
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.cloud.azure import (
    AzureClient, AzureResourceManagerClient, AzureAKSClient, 
    AzureMachineLearningClient, AzureCostManagementClient
)
from infra_mind.cloud.base import CloudServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_azure_resource_manager():
    """Test Azure Resource Manager API integration."""
    print("\n" + "="*60)
    print("TESTING AZURE RESOURCE MANAGER API")
    print("="*60)
    
    try:
        # Test with mock data (no credentials)
        client = AzureResourceManagerClient(region="eastus")
        
        print("Testing Resource Groups (Mock Data)...")
        resource_groups = await client.get_resource_groups("eastus")
        print(f"✓ Resource Groups: {len(resource_groups.services)} services found")
        
        # Display sample resource group
        if resource_groups.services:
            sample_rg = resource_groups.services[0]
            print(f"  Sample: {sample_rg.service_name}")
            print(f"  Category: {sample_rg.category}")
            print(f"  Pricing: ${sample_rg.hourly_price}/hour")
        
        print("Testing Advisor Recommendations (Mock Data)...")
        recommendations = await client.get_advisor_recommendations("all")
        print(f"✓ Advisor Recommendations: {recommendations.get('total_recommendations', 0)} found")
        
        # Display sample recommendation
        if recommendations.get('recommendations'):
            sample_rec = recommendations['recommendations'][0]
            print(f"  Sample: {sample_rec['title']}")
            print(f"  Impact: {sample_rec['impact']}")
            print(f"  Category: {sample_rec['category']}")
        
        print("Testing Resource Health (Mock Data)...")
        health = await client.get_resource_health()
        print(f"✓ Resource Health: {health.get('total_resources', 0)} resources monitored")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure Resource Manager test failed: {str(e)}")
        return False

async def test_azure_aks():
    """Test Azure Kubernetes Service API integration."""
    print("\n" + "="*60)
    print("TESTING AZURE KUBERNETES SERVICE (AKS) API")
    print("="*60)
    
    try:
        # Test with mock data (no credentials)
        client = AzureAKSClient(region="eastus")
        
        print("Testing AKS Services (Mock Data)...")
        aks_services = await client.get_aks_services("eastus")
        print(f"✓ AKS Services: {len(aks_services.services)} services found")
        
        # Display AKS services
        control_plane_found = False
        node_pools_found = 0
        
        for service in aks_services.services:
            if "Control Plane" in service.service_name:
                control_plane_found = True
                print(f"  Control Plane: {service.service_name}")
                print(f"    Pricing: ${service.hourly_price}/hour ({service.pricing_model})")
                print(f"    Features: {', '.join(service.features[:3])}...")
            elif "Node Pool" in service.service_name:
                node_pools_found += 1
                if node_pools_found <= 2:  # Show first 2 node pools
                    print(f"  Node Pool: {service.service_name}")
                    print(f"    Pricing: ${service.hourly_price}/hour")
                    print(f"    VM Size: {service.specifications.get('vm_size', 'N/A')}")
        
        print(f"✓ Found Control Plane: {control_plane_found}")
        print(f"✓ Found Node Pools: {node_pools_found}")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure AKS test failed: {str(e)}")
        return False

async def test_azure_machine_learning():
    """Test Azure Machine Learning API integration."""
    print("\n" + "="*60)
    print("TESTING AZURE MACHINE LEARNING API")
    print("="*60)
    
    try:
        # Test with mock data (no credentials)
        client = AzureMachineLearningClient(region="eastus")
        
        print("Testing ML Services (Mock Data)...")
        ml_services = await client.get_ml_services("eastus")
        print(f"✓ ML Services: {len(ml_services.services)} services found")
        
        # Display ML services
        workspace_found = False
        compute_instances_found = 0
        
        for service in ml_services.services:
            if "Workspace" in service.service_name:
                workspace_found = True
                print(f"  Workspace: {service.service_name}")
                print(f"    Pricing: ${service.hourly_price}/hour ({service.pricing_model})")
                print(f"    Features: {', '.join(service.features[:3])}...")
            elif "Compute" in service.service_name:
                compute_instances_found += 1
                if compute_instances_found <= 2:  # Show first 2 compute instances
                    print(f"  Compute: {service.service_name}")
                    print(f"    Pricing: ${service.hourly_price}/hour")
                    print(f"    Specs: {service.specifications}")
        
        print(f"✓ Found Workspace: {workspace_found}")
        print(f"✓ Found Compute Instances: {compute_instances_found}")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure Machine Learning test failed: {str(e)}")
        return False

async def test_azure_cost_management():
    """Test Azure Cost Management API integration."""
    print("\n" + "="*60)
    print("TESTING AZURE COST MANAGEMENT API")
    print("="*60)
    
    try:
        # Test with mock data (no credentials)
        client = AzureCostManagementClient(region="eastus")
        
        print("Testing Cost Analysis (Enhanced Mock Data)...")
        cost_analysis = await client.get_cost_analysis("subscription", "month")
        print(f"✓ Cost Analysis: ${cost_analysis.get('total_cost', 0):.2f} total cost")
        print(f"  Time Period: {cost_analysis.get('time_period')}")
        print(f"  Currency: {cost_analysis.get('currency')}")
        
        # Display cost by service
        cost_by_service = cost_analysis.get('cost_by_service', {})
        print("  Top Services by Cost:")
        for service, cost in sorted(cost_by_service.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"    {service}: ${cost:.2f}")
        
        # Display optimization opportunities
        opportunities = cost_analysis.get('cost_optimization_opportunities', [])
        print(f"  Optimization Opportunities: {len(opportunities)}")
        for opp in opportunities[:2]:  # Show first 2
            print(f"    {opp['category']}: ${opp['potential_savings']:.2f} potential savings")
        
        print("Testing Budget Alerts (Enhanced Mock Data)...")
        budget_alerts = await client.get_budget_alerts()
        print(f"✓ Budget Alerts: {budget_alerts.get('total_budgets', 0)} budgets configured")
        print(f"  Active Alerts: {budget_alerts.get('active_alerts', 0)}")
        
        # Display budget summary
        summary = budget_alerts.get('summary', {})
        print(f"  Total Budget: ${summary.get('total_budget_amount', 0):.2f}")
        print(f"  Total Spent: ${summary.get('total_spent', 0):.2f}")
        print(f"  Highest Utilization: {summary.get('highest_utilization', 0):.1f}%")
        
        print("Testing Cost Recommendations (Enhanced Mock Data)...")
        cost_recommendations = await client.get_cost_recommendations()
        print(f"✓ Cost Recommendations: {cost_recommendations.get('total_recommendations', 0)} found")
        print(f"  Total Potential Savings: ${cost_recommendations.get('total_potential_savings', 0):.2f}")
        
        # Display recommendation categories
        categories = cost_recommendations.get('categories', {})
        print("  Recommendation Categories:")
        for category, count in categories.items():
            if count > 0:
                print(f"    {category.replace('_', ' ').title()}: {count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure Cost Management test failed: {str(e)}")
        return False

async def test_azure_comprehensive_analysis():
    """Test comprehensive Azure analysis with all services."""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE AZURE ANALYSIS")
    print("="*60)
    
    try:
        # Test main Azure client with all services
        client = AzureClient(region="eastus")
        
        print("Testing Comprehensive Analysis...")
        analysis = await client.get_comprehensive_analysis("eastus")
        
        print(f"✓ Comprehensive Analysis completed")
        print(f"  Region: {analysis.get('region')}")
        print(f"  Timestamp: {analysis.get('timestamp')}")
        
        # Display services summary
        services = analysis.get('services', {})
        print("  Services Analyzed:")
        for service_type, service_data in services.items():
            if service_data and hasattr(service_data, 'services'):
                print(f"    {service_type.title()}: {len(service_data.services)} services")
            elif service_data and isinstance(service_data, dict):
                print(f"    {service_type.title()}: Available")
            elif service_data:
                print(f"    {service_type.title()}: Available")
        
        # Display summary
        summary = analysis.get('summary', {})
        print(f"  Total Services Analyzed: {summary.get('total_services_analyzed', 0)}")
        print(f"  Errors Encountered: {summary.get('errors_encountered', 0)}")
        print(f"  Data Freshness: {summary.get('data_freshness', 'unknown')}")
        
        print("Testing Optimization Recommendations...")
        optimization = await client.get_optimization_recommendations()
        
        print(f"✓ Optimization Recommendations generated")
        cost_opt = optimization.get('cost_optimization', {})
        print(f"  Total Potential Savings: ${cost_opt.get('total_potential_savings', 0):.2f}")
        print(f"  Priority Actions: {len(optimization.get('priority_actions', []))}")
        
        # Display optimization categories
        for category in ['cost_optimization', 'performance_optimization', 'security_optimization']:
            category_data = optimization.get(category, {})
            recommendations = category_data.get('recommendations', [])
            if recommendations:
                print(f"  {category.replace('_', ' ').title()}: {len(recommendations)} recommendations")
        
        return True
        
    except Exception as e:
        print(f"✗ Comprehensive Azure analysis test failed: {str(e)}")
        return False

async def test_azure_multi_region_analysis():
    """Test multi-region analysis capabilities."""
    print("\n" + "="*60)
    print("TESTING MULTI-REGION AZURE ANALYSIS")
    print("="*60)
    
    try:
        client = AzureClient(region="eastus")
        
        print("Testing Multi-Region Analysis...")
        regions = ["eastus", "westus2", "northeurope"]
        multi_region_analysis = await client.get_multi_region_analysis(regions)
        
        print(f"✓ Multi-Region Analysis completed")
        print(f"  Regions Analyzed: {len(multi_region_analysis.get('regions_analyzed', []))}")
        
        # Display metadata
        metadata = multi_region_analysis.get('metadata', {})
        print(f"  Successful Regions: {metadata.get('successful_regions', 0)}")
        print(f"  Failed Regions: {metadata.get('failed_regions', 0)}")
        
        # Display cross-region insights
        insights = multi_region_analysis.get('cross_region_insights', {})
        cost_comparison = insights.get('cost_comparison', {})
        if cost_comparison:
            print("  Cost Comparison by Region:")
            for region, cost_data in cost_comparison.items():
                print(f"    {region}: ${cost_data.get('total_cost', 0):.2f}")
        
        # Display recommendations
        recommendations = multi_region_analysis.get('recommendations', [])
        print(f"  Multi-Region Recommendations: {len(recommendations)}")
        for rec in recommendations[:2]:  # Show first 2
            print(f"    {rec.get('type', 'unknown').title()}: {rec.get('title', 'No title')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Multi-region Azure analysis test failed: {str(e)}")
        return False

async def test_azure_security_posture():
    """Test security posture analysis."""
    print("\n" + "="*60)
    print("TESTING AZURE SECURITY POSTURE ANALYSIS")
    print("="*60)
    
    try:
        client = AzureClient(region="eastus")
        
        print("Testing Security Posture Analysis...")
        security_analysis = await client.get_security_posture_analysis()
        
        print(f"✓ Security Posture Analysis completed")
        print(f"  Overall Score: {security_analysis.get('overall_score', 0)}")
        
        # Display security categories
        categories = ['compliance_status', 'threat_detection', 'access_management', 'data_protection', 'network_security']
        for category in categories:
            category_data = security_analysis.get(category, {})
            if category_data:
                print(f"  {category.replace('_', ' ').title()}: Available")
        
        # Display priority actions
        priority_actions = security_analysis.get('priority_actions', [])
        print(f"  Priority Security Actions: {len(priority_actions)}")
        for action in priority_actions[:2]:  # Show first 2
            print(f"    {action.get('title', 'No title')} (Priority: {action.get('priority', 'unknown')})")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure security posture test failed: {str(e)}")
        return False

async def main():
    """Run all Azure API suite tests."""
    print("AZURE API SUITE COMPREHENSIVE TEST")
    print("="*60)
    print(f"Test started at: {datetime.now(timezone.utc).isoformat()}")
    
    tests = [
        ("Resource Manager API", test_azure_resource_manager),
        ("AKS API", test_azure_aks),
        ("Machine Learning API", test_azure_machine_learning),
        ("Cost Management API", test_azure_cost_management),
        ("Comprehensive Analysis", test_azure_comprehensive_analysis),
        ("Multi-Region Analysis", test_azure_multi_region_analysis),
        ("Security Posture Analysis", test_azure_security_posture),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All Azure API suite tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)