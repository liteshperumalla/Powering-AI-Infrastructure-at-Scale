#!/usr/bin/env python3
"""
Demo script for Extended Azure API Suite.

This script demonstrates the advanced Azure integration features including:
- Resource Manager API
- AKS (Azure Kubernetes Service) API
- Machine Learning API
- Cost Management API
- Monitor API
- DevOps API
- Backup API
- Multi-region analysis
- Security posture analysis
- Governance and compliance reporting
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.cloud.azure import AzureClient
from src.infra_mind.cloud.base import CloudServiceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_extended_azure_apis():
    """Demonstrate extended Azure API suite capabilities."""
    print("🚀 Azure Extended API Suite Demo")
    print("=" * 50)
    
    # Initialize Azure client
    azure_client = AzureClient(
        region="eastus",
        subscription_id="demo-subscription-id",
        client_id="demo-client-id", 
        client_secret="demo-client-secret"
    )
    
    try:
        # 1. Resource Manager API Demo
        print("\n📋 1. Azure Resource Manager API")
        print("-" * 30)
        
        resource_groups = await azure_client.get_resource_groups("eastus")
        print(f"✅ Found {len(resource_groups.services)} resource management services")
        
        for service in resource_groups.services[:3]:  # Show first 3
            print(f"   • {service.service_name}: {service.description}")
        
        # Get advisor recommendations
        recommendations = await azure_client.get_resource_recommendations("all")
        print(f"✅ Retrieved {len(recommendations.get('recommendations', []))} advisor recommendations")
        
        # 2. AKS API Demo
        print("\n🐳 2. Azure Kubernetes Service (AKS) API")
        print("-" * 40)
        
        aks_services = await azure_client.get_aks_services("eastus")
        print(f"✅ Found {len(aks_services.services)} AKS services")
        
        control_plane = next((s for s in aks_services.services if "Control Plane" in s.service_name), None)
        if control_plane:
            print(f"   • {control_plane.service_name}: ${control_plane.hourly_price}/hour")
            print(f"     Features: {', '.join(control_plane.features[:3])}...")
        
        node_pools = [s for s in aks_services.services if "Node Pool" in s.service_name]
        print(f"   • Available node pool types: {len(node_pools)}")
        
        # 3. Machine Learning API Demo
        print("\n🤖 3. Azure Machine Learning API")
        print("-" * 35)
        
        ml_services = await azure_client.get_machine_learning_services("eastus")
        print(f"✅ Found {len(ml_services.services)} ML services")
        
        workspace = next((s for s in ml_services.services if "Workspace" in s.service_name), None)
        if workspace:
            print(f"   • {workspace.service_name}: {workspace.pricing_model}")
            print(f"     Features: {', '.join(workspace.features[:3])}...")
        
        compute_instances = [s for s in ml_services.services if "Compute" in s.service_name]
        print(f"   • Available compute instances: {len(compute_instances)}")
        
        # 4. Cost Management API Demo
        print("\n💰 4. Azure Cost Management API")
        print("-" * 35)
        
        cost_analysis = await azure_client.get_cost_analysis("subscription", "month")
        print(f"✅ Total monthly cost: ${cost_analysis['total_cost']:,.2f} {cost_analysis['currency']}")
        
        print("   • Cost by service:")
        for service, cost in list(cost_analysis['cost_by_service'].items())[:3]:
            print(f"     - {service}: ${cost:,.2f}")
        
        budget_alerts = await azure_client.get_budget_alerts()
        active_alerts = budget_alerts.get('active_alerts', [])
        print(f"   • Active budget alerts: {len(active_alerts)}")
        
        # 5. Advanced Integration Features Demo
        print("\n🔧 5. Advanced Integration Features")
        print("-" * 40)
        
        # Multi-region analysis
        regions = ["eastus", "westus2", "northeurope"]
        print(f"   Analyzing regions: {', '.join(regions)}")
        
        multi_region_analysis = await azure_client.get_multi_region_analysis(regions)
        successful_regions = multi_region_analysis['metadata']['successful_regions']
        print(f"✅ Successfully analyzed {successful_regions}/{len(regions)} regions")
        
        # Show cost comparison across regions
        cost_comparison = multi_region_analysis['cross_region_insights']['cost_comparison']
        if cost_comparison:
            print("   • Cost comparison across regions:")
            for region, cost_info in cost_comparison.items():
                print(f"     - {region}: ${cost_info['total_cost']:,.2f}")
        
        # Security posture analysis
        print("\n🔒 6. Security Posture Analysis")
        print("-" * 35)
        
        security_analysis = await azure_client.get_security_posture_analysis()
        print(f"✅ Overall security score: {security_analysis['overall_score']}/100")
        
        priority_actions = security_analysis.get('priority_actions', [])
        print(f"   • Priority security actions: {len(priority_actions)}")
        
        for action in priority_actions[:2]:  # Show first 2
            print(f"     - {action['title']} (Urgency: {action['urgency']})")
        
        # Compliance status
        compliance_status = security_analysis.get('compliance_status', {})
        print("   • Compliance scores:")
        for framework, status in compliance_status.items():
            print(f"     - {framework.upper()}: {status['score']}%")
        
        # 7. Governance and Compliance Report
        print("\n📊 7. Governance and Compliance Report")
        print("-" * 42)
        
        governance_report = await azure_client.get_governance_and_compliance_report()
        
        policy_compliance = governance_report['policy_compliance']
        print(f"✅ Policy compliance: {policy_compliance['compliance_percentage']:.1f}%")
        print(f"   • Compliant resources: {policy_compliance['compliant_resources']}")
        print(f"   • Non-compliant resources: {policy_compliance['non_compliant_resources']}")
        
        resource_governance = governance_report['resource_governance']
        print(f"   • Tagged resources: {resource_governance['tagged_resources_percentage']}%")
        print(f"   • Naming convention compliance: {resource_governance['naming_convention_compliance']}%")
        
        # 8. Extended Service APIs Demo
        print("\n🛠️ 8. Extended Service APIs")
        print("-" * 30)
        
        # Monitor services
        monitoring_services = await azure_client.get_monitoring_services("eastus")
        print(f"✅ Monitoring services: {len(monitoring_services.services)}")
        
        # DevOps services
        devops_services = await azure_client.get_devops_services("eastus")
        print(f"✅ DevOps services: {len(devops_services.services)}")
        
        # Backup services
        backup_services = await azure_client.get_backup_services("eastus")
        print(f"✅ Backup services: {len(backup_services.services)}")
        
        # Performance metrics demo
        print("\n📈 9. Performance Metrics")
        print("-" * 25)
        
        resource_id = "/subscriptions/demo/resourceGroups/demo-rg/providers/Microsoft.Compute/virtualMachines/demo-vm"
        cpu_metrics = await azure_client.get_performance_metrics(resource_id, "cpu_utilization", "24h")
        
        print(f"✅ Retrieved CPU metrics for last 24 hours")
        print(f"   • Data points: {len(cpu_metrics['data_points'])}")
        print(f"   • Average CPU: {cpu_metrics['metadata']['avg_value']:.1f}%")
        print(f"   • Peak CPU: {cpu_metrics['metadata']['max_value']:.1f}%")
        
        # 10. Comprehensive Analysis Demo
        print("\n🔍 10. Comprehensive Analysis")
        print("-" * 32)
        
        comprehensive_analysis = await azure_client.get_comprehensive_analysis("eastus")
        
        services_summary = comprehensive_analysis['summary']
        print(f"✅ Services analyzed: {services_summary['total_services_analyzed']}")
        print(f"   • Errors encountered: {services_summary['errors_encountered']}")
        print(f"   • Data freshness: {services_summary['data_freshness']}")
        
        # Show service counts by category
        services = comprehensive_analysis['services']
        service_counts = {}
        for category, service_data in services.items():
            if service_data and isinstance(service_data, dict) and 'services' in service_data:
                service_counts[category] = len(service_data['services'])
            elif service_data:
                service_counts[category] = 1
        
        print("   • Services by category:")
        for category, count in service_counts.items():
            print(f"     - {category.title()}: {count}")
        
        print("\n✨ Extended Azure API Suite Demo Complete!")
        print("=" * 50)
        
        return {
            "status": "success",
            "regions_analyzed": len(regions),
            "services_discovered": sum(service_counts.values()),
            "security_score": security_analysis['overall_score'],
            "compliance_percentage": policy_compliance['compliance_percentage'],
            "total_cost": cost_analysis['total_cost'],
            "recommendations_count": len(recommendations.get('recommendations', [])),
            "timestamp": datetime.now().isoformat()
        }
        
    except CloudServiceError as e:
        logger.error(f"Cloud service error: {e}")
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        return {"status": "error", "error": str(e)}


async def demo_optimization_recommendations():
    """Demonstrate optimization recommendations feature."""
    print("\n🎯 Optimization Recommendations Demo")
    print("=" * 40)
    
    azure_client = AzureClient(region="eastus")
    
    try:
        recommendations = await azure_client.get_optimization_recommendations()
        
        print(f"✅ Total potential savings: ${recommendations['cost_optimization']['total_potential_savings']:,.2f}/year")
        
        print("\n💰 Cost Optimization Opportunities:")
        for rec in recommendations['cost_optimization']['recommendations'][:3]:
            print(f"   • {rec['title']}")
            print(f"     Savings: ${rec['potential_savings']:,.2f}")
            print(f"     Effort: {rec['implementation_effort']}")
        
        print(f"\n🔒 Security Recommendations: {len(recommendations['security_optimization']['recommendations'])}")
        print(f"⚡ Performance Recommendations: {len(recommendations['performance_optimization']['recommendations'])}")
        print(f"🛡️ Reliability Recommendations: {len(recommendations['reliability_optimization']['recommendations'])}")
        
        priority_actions = recommendations.get('priority_actions', [])
        if priority_actions:
            print(f"\n🚨 Priority Actions ({len(priority_actions)}):")
            for action in priority_actions[:2]:
                print(f"   • {action['title']} (Impact: {action['impact']})")
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        print(f"❌ Error: {e}")


def save_demo_results(results: Dict[str, Any], filename: str = "azure_extended_api_demo_results.json"):
    """Save demo results to file."""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Demo results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")


async def main():
    """Main demo function."""
    print("🌟 Starting Azure Extended API Suite Demo")
    
    # Run main demo
    results = await demo_extended_azure_apis()
    
    # Run optimization demo
    await demo_optimization_recommendations()
    
    # Save results
    if results.get("status") == "success":
        save_demo_results(results)
    
    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())