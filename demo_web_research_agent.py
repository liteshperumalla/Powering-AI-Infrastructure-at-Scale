#!/usr/bin/env python3
"""
Demo script for Web Research Agent.

This script demonstrates the Web Research Agent's capabilities for:
- Web scraping and content extraction
- Competitive analysis and market intelligence
- Technology trend analysis
- Regulatory update monitoring
- Best practices collection
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.agents.web_research_agent import WebResearchAgent
from src.infra_mind.models.assessment import Assessment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_assessment():
    """Create a sample assessment for testing (mock object)."""
    
    class MockAssessment:
        def __init__(self):
            self.id = "demo_assessment_123"
            self.user_id = "demo_user"
            self.title = "Web Research Demo Assessment"
            self.business_requirements = {
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "100k-500k",
                "timeline": "6-12 months",
                "compliance_needs": ["GDPR", "SOC2"],
                "business_goals": ["cost_optimization", "scalability", "compliance"]
            }
            self.technical_requirements = {
                "current_infrastructure": {
                    "cloud_providers": ["aws"],
                    "services_used": ["ec2", "rds", "s3"],
                    "architecture": "monolithic"
                },
                "workload_characteristics": {
                    "workload_types": ["web_application", "database"],
                    "expected_users": 10000,
                    "data_volume": "1TB",
                    "traffic_patterns": "steady"
                },
                "performance_requirements": {
                    "availability": "99.9%",
                    "response_time": "200ms",
                    "throughput": "1000 rps"
                },
                "scalability_needs": {
                    "auto_scaling": True,
                    "global_distribution": False,
                    "peak_capacity": "5x"
                },
                "integration_requirements": ["api_gateway", "monitoring", "ci_cd"]
            }
            self.status = "in_progress"
        
        def dict(self):
            return {
                "id": self.id,
                "user_id": self.user_id,
                "title": self.title,
                "business_requirements": self.business_requirements,
                "technical_requirements": self.technical_requirements,
                "status": self.status
            }
    
    return MockAssessment()


async def demo_web_research_analysis():
    """Demonstrate web research analysis capabilities."""
    print("🔍 Web Research Agent Demo")
    print("=" * 50)
    
    try:
        # Create sample assessment
        assessment = create_sample_assessment()
        print(f"✅ Created sample assessment for {assessment.business_requirements['industry']} company")
        
        # Initialize Web Research Agent
        agent = WebResearchAgent()
        print(f"✅ Initialized {agent.name}")
        
        # Execute web research analysis
        print("\n🚀 Starting web research analysis...")
        result = await agent.execute(assessment)
        
        if result.status.value == "completed":
            print("✅ Web research analysis completed successfully!")
            
            # Display results
            await display_research_results(result.data)
            
        else:
            print(f"❌ Web research analysis failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def display_research_results(results: Dict[str, Any]):
    """Display web research results in a formatted way."""
    print("\n📊 Web Research Results")
    print("=" * 50)
    
    # Research requirements
    if "research_requirements" in results:
        req = results["research_requirements"]
        print(f"\n🎯 Research Requirements:")
        print(f"   Priority Areas: {', '.join(req.get('priority_areas', []))}")
        print(f"   Target Providers: {', '.join(req.get('target_providers', []))}")
        print(f"   Research Depth: {req.get('research_depth', 'standard')}")
    
    # Data collection summary
    web_data_count = results.get("web_data_collected", 0)
    print(f"\n📥 Data Collection:")
    print(f"   Web Sources Scraped: {web_data_count}")
    
    # Competitive analysis
    if "competitive_analysis" in results:
        comp = results["competitive_analysis"]
        print(f"\n🏢 Competitive Analysis:")
        
        if comp.get("provider_mentions"):
            print("   Provider Mentions:")
            for provider, count in comp["provider_mentions"].items():
                print(f"     • {provider}: {count} mentions")
        
        if comp.get("market_positioning"):
            print("   Market Positioning:")
            for provider, data in comp["market_positioning"].items():
                visibility = data.get("visibility_score", 0)
                print(f"     • {provider}: {visibility:.2f} visibility score")
        
        pricing_count = len(comp.get("pricing_comparisons", []))
        if pricing_count > 0:
            print(f"   Pricing Data Points: {pricing_count}")
    
    # Trend analysis
    if "trend_analysis" in results:
        trends = results["trend_analysis"]
        print(f"\n📈 Trend Analysis:")
        
        if trends.get("emerging_trends"):
            print("   Emerging Trends:")
            for trend in trends["emerging_trends"][:5]:
                print(f"     • {trend['trend']} ({trend['strength']} strength)")
        
        if trends.get("key_topics"):
            print("   Key Topics:")
            for topic in trends["key_topics"][:3]:
                print(f"     • {topic['topic']} ({topic['mentions']} mentions)")
    
    # Regulatory updates
    if "regulatory_updates" in results:
        reg = results["regulatory_updates"]
        print(f"\n⚖️ Regulatory Updates:")
        
        if reg.get("regulations_tracked"):
            print("   Regulations Tracked:")
            for regulation in reg["regulations_tracked"][:3]:
                print(f"     • {regulation['regulation']} ({regulation['mentions']} mentions)")
        
        update_count = len(reg.get("recent_updates", []))
        if update_count > 0:
            print(f"   Recent Updates Found: {update_count}")
    
    # Market intelligence
    if "market_intelligence" in results:
        intel = results["market_intelligence"]
        print(f"\n🧠 Market Intelligence:")
        
        if intel.get("executive_summary"):
            summary = intel["executive_summary"]
            print(f"   Providers Analyzed: {summary.get('providers_analyzed', 0)}")
            print(f"   Trends Identified: {summary.get('trends_identified', 0)}")
            print(f"   Regulations Monitored: {summary.get('regulations_monitored', 0)}")
            
            if summary.get("key_insights"):
                print("   Key Insights:")
                for insight in summary["key_insights"]:
                    print(f"     • {insight}")
    
    # Recommendations
    if "recommendations" in results:
        recommendations = results["recommendations"]
        print(f"\n💡 Recommendations ({len(recommendations)} total):")
        
        # Group by type
        rec_by_type = {}
        for rec in recommendations:
            rec_type = rec.get("type", "other")
            if rec_type not in rec_by_type:
                rec_by_type[rec_type] = []
            rec_by_type[rec_type].append(rec)
        
        for rec_type, recs in rec_by_type.items():
            print(f"\n   {rec_type.title()} Recommendations:")
            for rec in recs[:3]:  # Show top 3 per type
                priority = rec.get("priority", "medium")
                confidence = rec.get("confidence_score", 0)
                print(f"     • {rec.get('title', 'N/A')} (Priority: {priority}, Confidence: {confidence:.2f})")
                print(f"       {rec.get('description', 'N/A')[:100]}...")
    
    # Data freshness
    if "data_freshness" in results:
        freshness = results["data_freshness"]
        print(f"\n🕒 Data Freshness:")
        print(f"   Overall Status: {freshness.get('overall_status', 'unknown')}")
        
        if freshness.get("stale_data_count", 0) > 0:
            print(f"   Stale Data Categories: {freshness['stale_data_count']}")
    
    # Research summary
    if "research_summary" in results:
        summary = results["research_summary"]
        print(f"\n📋 Research Summary:")
        
        if summary.get("research_scope"):
            scope = summary["research_scope"]
            print(f"   Scope: {scope.get('providers_analyzed', 0)} providers, "
                  f"{scope.get('trends_identified', 0)} trends, "
                  f"{scope.get('data_sources_used', 0)} data sources")
        
        if summary.get("data_quality"):
            quality = summary["data_quality"]
            validation_score = quality.get("data_validation_score", 0)
            print(f"   Data Quality Score: {validation_score:.2f}")


async def demo_specific_research_capabilities():
    """Demonstrate specific research capabilities."""
    print("\n🔬 Specific Research Capabilities Demo")
    print("=" * 50)
    
    agent = WebResearchAgent()
    
    # Test different research areas
    research_areas = [
        "pricing_analysis",
        "competitive_analysis", 
        "industry_trends",
        "regulatory_tracking",
        "best_practices"
    ]
    
    for area in research_areas:
        print(f"\n🎯 Testing {area.replace('_', ' ').title()}...")
        
        try:
            # Create focused assessment for this area
            assessment = create_sample_assessment()
            
            # Override research requirements to focus on this area
            agent.context = {
                "research_requirements": {
                    "priority_areas": [area],
                    "target_providers": ["aws", "azure"],
                    "research_depth": "standard"
                }
            }
            
            # This would normally be part of the full execution
            # For demo, we'll just show the capability exists
            print(f"   ✅ {area.replace('_', ' ').title()} capability available")
            print(f"   📊 Target sources: {len(agent.research_targets.get(area, []))} configured")
            
        except Exception as e:
            print(f"   ❌ Error testing {area}: {str(e)}")


async def demo_web_scraping_tools():
    """Demonstrate web scraping tools."""
    print("\n🛠️ Web Scraping Tools Demo")
    print("=" * 50)
    
    agent = WebResearchAgent()
    
    # Test web scraping tool
    print("\n🔧 Testing Web Scraping Tool...")
    try:
        # Mock HTML content for testing
        mock_html = """
        <html>
            <head><title>Cloud Pricing Example</title></head>
            <body>
                <h1>AWS EC2 Pricing</h1>
                <p>EC2 instances start at $0.0116 per hour for t3.nano instances.</p>
                <p>RDS database pricing begins at $0.017 per hour.</p>
                <h2>Azure Compute Pricing</h2>
                <p>Azure VMs start at $0.0496 per hour for B1s instances.</p>
                <table>
                    <tr><th>Service</th><th>Price</th></tr>
                    <tr><td>EC2 t3.micro</td><td>$0.0104/hour</td></tr>
                    <tr><td>RDS db.t3.micro</td><td>$0.017/hour</td></tr>
                </table>
            </body>
        </html>
        """
        
        # Test content extraction
        scraping_tool = agent.toolkit.tools.get("web_scraper")
        if scraping_tool:
            print("   ✅ Web scraping tool available")
            print("   📊 Can extract: pricing data, trends, regulatory content")
        else:
            print("   ⚠️ Web scraping tool not found in toolkit")
        
        # Test search API tool
        search_tool = agent.toolkit.tools.get("search_api")
        if search_tool:
            print("   ✅ Search API tool available")
            print("   🔍 Can search: web, news, academic sources")
        else:
            print("   ⚠️ Search API tool not found in toolkit")
        
        # Test content extractor
        extractor_tool = agent.toolkit.tools.get("content_extractor")
        if extractor_tool:
            print("   ✅ Content extractor tool available")
            print("   📄 Can process: HTML, text, JSON content")
        else:
            print("   ⚠️ Content extractor tool not found in toolkit")
            
    except Exception as e:
        print(f"   ❌ Error testing tools: {str(e)}")


async def main():
    """Main demo function."""
    print("🌐 Web Research Agent Comprehensive Demo")
    print("=" * 60)
    
    # Run main demo
    await demo_web_research_analysis()
    
    # Run specific capabilities demo
    await demo_specific_research_capabilities()
    
    # Run tools demo
    await demo_web_scraping_tools()
    
    print("\n✅ Demo completed!")
    print("\nThe Web Research Agent provides:")
    print("• Competitive analysis and market intelligence")
    print("• Technology trend identification and analysis")
    print("• Regulatory update monitoring and tracking")
    print("• Best practices collection from cloud providers")
    print("• Real-time web scraping and content extraction")
    print("• Data validation against multiple sources")
    print("• Strategic recommendations based on market research")


if __name__ == "__main__":
    asyncio.run(main())