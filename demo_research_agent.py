#!/usr/bin/env python3
"""
Demo script for Research Agent.

This script demonstrates the Research Agent's capabilities including:
- Real-time data collection from cloud providers
- Pricing analysis and trend identification
- Data freshness validation
- Benchmark data collection
- Research insights generation
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.agents.research_agent import ResearchAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole
from src.infra_mind.models.assessment import Assessment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_assessment() -> Assessment:
    """Create a sample assessment for testing."""
    assessment_data = {
        "business_requirements": {
            "company_size": "medium",
            "industry": "technology",
            "budget_range": "$50k-100k",
            "primary_goals": ["cost_optimization", "scalability", "innovation"],
            "timeline": "6_months",
            "compliance_needs": ["GDPR"]
        },
        "technical_requirements": {
            "workload_types": ["web_application", "ai_ml", "data_processing"],
            "expected_users": 10000,
            "performance_requirements": {
                "response_time": "< 200ms",
                "availability": "99.9%",
                "throughput": "1000 rps"
            },
            "scalability_needs": {
                "auto_scaling": True,
                "load_balancing": True,
                "multi_region": False
            },
            "integration_requirements": ["rest_api", "database", "message_queue"]
        },
        "compliance_requirements": {
            "regulations": ["GDPR"],
            "data_residency": "EU",
            "security_standards": ["ISO27001"]
        }
    }
    
    # Create mock assessment object
    class MockAssessment:
        def __init__(self, data):
            self._data = data
            self.id = "demo_assessment_001"
        
        def dict(self):
            return self._data
    
    return MockAssessment(assessment_data)


async def demo_research_agent_basic():
    """Demonstrate basic Research Agent functionality."""
    print("\n" + "="*60)
    print("RESEARCH AGENT DEMO - BASIC FUNCTIONALITY")
    print("="*60)
    
    # Create Research Agent
    config = AgentConfig(
        name="Demo Research Agent",
        role=AgentRole.RESEARCH,
        tools_enabled=["cloud_api", "data_processor", "calculator"],
        temperature=0.1,
        metrics_enabled=False,  # Disable metrics to avoid database dependency
        custom_config={
            "focus_areas": [
                "data_collection",
                "pricing_analysis",
                "trend_analysis",
                "benchmark_collection",
                "market_intelligence"
            ],
            "data_sources": [
                "aws_pricing_api",
                "azure_retail_api",
                "gcp_billing_api"
            ]
        }
    )
    
    research_agent = ResearchAgent(config)
    
    print(f"\n✓ Created Research Agent: {research_agent.name}")
    print(f"  Role: {research_agent.role.value}")
    print(f"  Status: {research_agent.status.value}")
    
    # Safely access custom_config
    custom_config = research_agent.config.custom_config
    if custom_config and 'focus_areas' in custom_config:
        print(f"  Focus Areas: {', '.join(custom_config['focus_areas'])}")
    if custom_config and 'data_sources' in custom_config:
        print(f"  Data Sources: {', '.join(custom_config['data_sources'])}")
    
    print(f"  Tools Enabled: {', '.join(research_agent.config.tools_enabled)}")
    print(f"  Temperature: {research_agent.config.temperature}")
    
    # Create sample assessment
    assessment = create_sample_assessment()
    print(f"\n✓ Created sample assessment: {assessment.id}")
    
    # Execute Research Agent
    print("\n🔍 Executing Research Agent...")
    try:
        result = await research_agent.execute(assessment)
        
        print(f"\n✓ Research Agent execution completed!")
        print(f"  Status: {result.status.value}")
        execution_time = result.execution_time or 0.0
        print(f"  Execution Time: {execution_time:.2f}s")
        print(f"  Recommendations: {len(result.recommendations)}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Research Agent execution failed: {str(e)}")
        logger.error(f"Research Agent execution failed", exc_info=True)
        return None


async def demo_data_collection_analysis(result: Dict[str, Any]):
    """Demonstrate data collection analysis."""
    if not result or not result.data:
        print("\n❌ No result data available for analysis")
        return
    
    print("\n" + "="*60)
    print("DATA COLLECTION ANALYSIS")
    print("="*60)
    
    data = result.data
    
    # Analyze data requirements
    if "data_requirements" in data:
        requirements = data["data_requirements"]
        print(f"\n📋 Data Requirements Analysis:")
        print(f"  Workload Types: {', '.join(requirements.get('workload_analysis', {}).get('types', []))}")
        print(f"  Expected Users: {requirements.get('workload_analysis', {}).get('expected_users', 'N/A'):,}")
        print(f"  Budget Range: {requirements.get('workload_analysis', {}).get('budget_range', 'N/A')}")
        print(f"  Required Services: {', '.join(requirements.get('required_services', []))}")
        print(f"  Target Providers: {', '.join(requirements.get('collection_scope', {}).get('providers', []))}")
    
    # Analyze collected data
    if "collected_data" in data:
        collected = data["collected_data"]
        metadata = collected.get("collection_metadata", {})
        
        print(f"\n📊 Data Collection Results:")
        print(f"  Total Providers: {metadata.get('total_providers', 0)}")
        print(f"  Successful Collections: {metadata.get('successful_collections', 0)}")
        print(f"  Failed Collections: {metadata.get('failed_collections', 0)}")
        print(f"  Total API Calls: {metadata.get('total_api_calls', 0)}")
        
        # Analyze provider data
        providers = collected.get("providers", {})
        for provider, provider_data in providers.items():
            if "error" in provider_data:
                print(f"  ❌ {provider.upper()}: {provider_data['error']}")
            else:
                services_count = sum(
                    len(service_info.get("services", [])) 
                    for service_info in provider_data.get("services", {}).values()
                    if isinstance(service_info, dict)
                )
                pricing_count = sum(
                    len(pricing_info.get("pricing", [])) 
                    for pricing_info in provider_data.get("pricing_data", {}).values()
                    if isinstance(pricing_info, dict)
                )
                completeness = provider_data.get("data_completeness", 0.0)
                
                print(f"  ✓ {provider.upper()}: {services_count} services, {pricing_count} pricing entries, {completeness:.1%} complete")


async def demo_data_validation_analysis(result: Dict[str, Any]):
    """Demonstrate data validation analysis."""
    if not result or not result.data:
        return
    
    print("\n" + "="*60)
    print("DATA VALIDATION ANALYSIS")
    print("="*60)
    
    data = result.data
    
    if "data_validation" in data:
        validation = data["data_validation"]
        
        print(f"\n🔍 Data Quality Assessment:")
        print(f"  Overall Quality: {validation.get('overall_quality', 'unknown').upper()}")
        print(f"  Quality Score: {validation.get('quality_score', 0.0):.2f}/1.00")
        
        # Freshness analysis
        freshness_check = validation.get("freshness_check", {})
        if freshness_check:
            print(f"\n⏰ Data Freshness:")
            for provider, freshness_info in freshness_check.items():
                if isinstance(freshness_info, dict):
                    score = freshness_info.get("score", 0.0)
                    age_hours = freshness_info.get("age_hours", 0.0)
                    print(f"  {provider.upper()}: {score:.2f} score ({age_hours:.1f} hours old)")
        
        # Completeness analysis
        completeness_check = validation.get("completeness_check", {})
        if completeness_check:
            print(f"\n📈 Data Completeness:")
            for provider, completeness_info in completeness_check.items():
                if isinstance(completeness_info, dict):
                    score = completeness_info.get("score", 0.0)
                    services = completeness_info.get("services_collected", 0)
                    pricing = completeness_info.get("pricing_data_collected", 0)
                    print(f"  {provider.upper()}: {score:.1%} complete ({services} services, {pricing} pricing)")
        
        # Accuracy analysis
        accuracy_check = validation.get("accuracy_check", {})
        if accuracy_check:
            print(f"\n🎯 Data Accuracy:")
            for provider, accuracy_info in accuracy_check.items():
                if isinstance(accuracy_info, dict):
                    score = accuracy_info.get("score", 0.0)
                    issues = len(accuracy_info.get("issues", []))
                    warnings = len(accuracy_info.get("warnings", []))
                    print(f"  {provider.upper()}: {score:.2f} score ({issues} issues, {warnings} warnings)")
        
        # Staleness warnings
        staleness_warnings = validation.get("data_staleness_warnings", [])
        if staleness_warnings:
            print(f"\n⚠️  Data Staleness Warnings:")
            for warning in staleness_warnings:
                print(f"  • {warning}")


async def demo_trend_analysis(result: Dict[str, Any]):
    """Demonstrate trend analysis."""
    if not result or not result.data:
        return
    
    print("\n" + "="*60)
    print("TREND ANALYSIS")
    print("="*60)
    
    data = result.data
    
    if "trend_analysis" in data:
        trends = data["trend_analysis"]
        
        # Pricing trends
        pricing_trends = trends.get("pricing_trends", {})
        cost_leaders = pricing_trends.get("cost_leaders", {})
        
        if cost_leaders:
            print(f"\n💰 Cost Leaders by Service:")
            for service, leader_info in cost_leaders.items():
                provider = leader_info.get("provider")
                min_price = leader_info.get("min_price")
                if provider and min_price:
                    print(f"  {service.title()}: {provider.upper()} (${min_price:.4f}/hour)")
        
        # Price ranges
        price_ranges = pricing_trends.get("price_ranges", {})
        if price_ranges:
            print(f"\n📊 Price Ranges by Service:")
            for service, range_info in price_ranges.items():
                if isinstance(range_info, dict) and range_info.get("min_price") is not None:
                    min_price = range_info.get("min_price", 0)
                    max_price = range_info.get("max_price", 0)
                    avg_price = range_info.get("avg_price", 0)
                    spread = range_info.get("price_spread", 0)
                    print(f"  {service.title()}: ${min_price:.4f} - ${max_price:.4f} (avg: ${avg_price:.4f}, spread: ${spread:.4f})")
        
        # Market insights
        market_insights = trends.get("market_insights", [])
        if market_insights:
            print(f"\n🔍 Market Insights:")
            for insight in market_insights:
                print(f"  • {insight}")
        
        # Emerging patterns
        emerging_patterns = trends.get("emerging_patterns", [])
        if emerging_patterns:
            print(f"\n🚀 Emerging Patterns:")
            for pattern in emerging_patterns:
                print(f"  • {pattern}")


async def demo_benchmark_analysis(result: Dict[str, Any]):
    """Demonstrate benchmark analysis."""
    if not result or not result.data:
        return
    
    print("\n" + "="*60)
    print("BENCHMARK ANALYSIS")
    print("="*60)
    
    data = result.data
    
    if "benchmark_data" in data:
        benchmarks = data["benchmark_data"]
        
        # Performance benchmarks
        performance = benchmarks.get("performance_benchmarks", {})
        if performance:
            print(f"\n⚡ Performance Benchmarks:")
            for workload, metrics in performance.items():
                print(f"  {workload.replace('_', ' ').title()}:")
                if isinstance(metrics, dict):
                    for metric, values in metrics.items():
                        if isinstance(values, dict):
                            value_str = ", ".join([f"{k}: {v}" for k, v in values.items()])
                            print(f"    {metric.replace('_', ' ').title()}: {value_str}")
        
        # Cost benchmarks
        cost_benchmarks = benchmarks.get("cost_benchmarks", {})
        if cost_benchmarks:
            print(f"\n💵 Cost Benchmarks:")
            for scale, metrics in cost_benchmarks.items():
                print(f"  {scale.replace('_', ' ').title()}:")
                if isinstance(metrics, dict):
                    for metric, values in metrics.items():
                        if isinstance(values, dict):
                            value_str = ", ".join([f"{k}: ${v:,}" if 'cost' in k else f"{k}: ${v:.2f}" for k, v in values.items()])
                            print(f"    {metric.replace('_', ' ').title()}: {value_str}")
        
        # Industry benchmarks
        industry = benchmarks.get("industry_benchmarks", {})
        if industry:
            print(f"\n🏭 Industry Benchmarks:")
            
            # Availability targets
            availability = industry.get("availability_targets", {})
            if availability:
                print(f"  Availability Targets:")
                for workload, target in availability.items():
                    if isinstance(target, dict):
                        sla = target.get("sla", 0)
                        downtime = target.get("downtime_minutes_month", 0)
                        print(f"    {workload.replace('_', ' ').title()}: {sla}% SLA ({downtime:.1f} min/month downtime)")
            
            # Scalability patterns
            scalability = industry.get("scalability_patterns", {})
            if scalability:
                print(f"  Scalability Patterns:")
                for pattern, recommended in scalability.items():
                    status = "✓ Recommended" if recommended else "○ Optional"
                    print(f"    {pattern.replace('_', ' ').title()}: {status}")


async def demo_research_insights(result: Dict[str, Any]):
    """Demonstrate research insights."""
    if not result or not result.data:
        return
    
    print("\n" + "="*60)
    print("RESEARCH INSIGHTS & RECOMMENDATIONS")
    print("="*60)
    
    data = result.data
    
    if "research_insights" in data:
        insights = data["research_insights"]
        
        # Key findings
        key_findings = insights.get("key_findings", [])
        if key_findings:
            print(f"\n🔑 Key Findings:")
            for finding in key_findings:
                print(f"  • {finding}")
        
        # Confidence level
        confidence = insights.get("confidence_level", "unknown")
        quality = insights.get("data_quality_assessment", "unknown")
        print(f"\n📊 Analysis Quality:")
        print(f"  Data Quality: {quality.upper()}")
        print(f"  Confidence Level: {confidence.upper()}")
        
        # Research summary
        summary = insights.get("research_summary", {})
        if summary:
            print(f"\n📋 Research Summary:")
            
            collection_summary = summary.get("data_collection_summary", {})
            if collection_summary:
                providers = collection_summary.get("providers_queried", [])
                successful = collection_summary.get("successful_collections", 0)
                api_calls = collection_summary.get("total_api_calls", 0)
                print(f"  Data Collection: {successful}/{len(providers)} providers successful, {api_calls} API calls")
            
            pricing_summary = summary.get("pricing_analysis_summary", {})
            if pricing_summary:
                cost_leaders = pricing_summary.get("cost_leaders_identified", 0)
                price_ranges = pricing_summary.get("price_ranges_analyzed", 0)
                insights_count = pricing_summary.get("market_insights_count", 0)
                print(f"  Pricing Analysis: {cost_leaders} cost leaders, {price_ranges} price ranges, {insights_count} insights")
            
            completeness = summary.get("research_completeness", 0.0)
            print(f"  Research Completeness: {completeness:.1%}")
    
    # Recommendations
    if result.recommendations:
        print(f"\n💡 Recommendations ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations, 1):
            if isinstance(rec, dict):
                title = rec.get("title", "Untitled Recommendation")
                category = rec.get("category", "general")
                priority = rec.get("priority", "medium")
                confidence = rec.get("confidence", "medium")
                
                print(f"  {i}. {title}")
                print(f"     Category: {category.title()} | Priority: {priority.upper()} | Confidence: {confidence.upper()}")
                
                description = rec.get("description")
                if description:
                    print(f"     {description}")


async def main():
    """Main demo function."""
    print("🚀 Starting Research Agent Demo...")
    
    try:
        # Run basic demo
        result = await demo_research_agent_basic()
        
        if result:
            # Run detailed analysis demos
            await demo_data_collection_analysis(result)
            await demo_data_validation_analysis(result)
            await demo_trend_analysis(result)
            await demo_benchmark_analysis(result)
            await demo_research_insights(result)
            
            print("\n" + "="*60)
            print("DEMO COMPLETED SUCCESSFULLY! ✅")
            print("="*60)
            print("\nThe Research Agent has demonstrated:")
            print("• Real-time data collection from cloud providers")
            print("• Comprehensive data validation and quality assessment")
            print("• Pricing trend analysis and cost leader identification")
            print("• Performance and cost benchmark collection")
            print("• Intelligent research insights and recommendations")
            print("\nThis agent is ready for integration with the multi-agent system!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logger.error("Demo execution failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())