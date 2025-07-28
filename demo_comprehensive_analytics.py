#!/usr/bin/env python3
"""
Comprehensive Analytics Dashboard Demo

Demonstrates the advanced analytics dashboard functionality including:
- User behavior analysis
- Recommendation quality tracking
- System performance monitoring
- Alert analytics
- Predictive insights
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from src.infra_mind.orchestration.analytics_dashboard import (
    AnalyticsDashboard, get_analytics_dashboard, initialize_analytics_dashboard,
    AnalyticsTimeframe, UserAnalytics, RecommendationQualityMetrics,
    SystemPerformanceAnalytics, AlertAnalytics
)
from src.infra_mind.orchestration.monitoring import (
    WorkflowMonitor, get_workflow_monitor, initialize_workflow_monitoring
)
from src.infra_mind.orchestration.dashboard import (
    WorkflowDashboard, get_workflow_dashboard, initialize_workflow_dashboard
)
from src.infra_mind.orchestration.events import EventManager
from src.infra_mind.core.metrics_collector import (
    get_metrics_collector, initialize_metrics_collection
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_analytics_initialization():
    """Demonstrate analytics dashboard initialization."""
    print("\n" + "="*60)
    print("COMPREHENSIVE ANALYTICS DASHBOARD DEMO")
    print("="*60)
    
    try:
        # Initialize core components
        print("\n1. Initializing core monitoring components...")
        
        # Initialize metrics collection
        await initialize_metrics_collection()
        print("✓ Metrics collection initialized")
        
        # Initialize event manager and workflow monitoring
        event_manager = EventManager()
        await initialize_workflow_monitoring(event_manager)
        print("✓ Workflow monitoring initialized")
        
        # Initialize workflow dashboard
        workflow_monitor = get_workflow_monitor()
        await initialize_workflow_dashboard(workflow_monitor)
        print("✓ Workflow dashboard initialized")
        
        # Initialize analytics dashboard
        workflow_dashboard = get_workflow_dashboard()
        await initialize_analytics_dashboard(workflow_monitor, workflow_dashboard)
        print("✓ Analytics dashboard initialized")
        
        return get_analytics_dashboard()
        
    except Exception as e:
        logger.error(f"Failed to initialize analytics dashboard: {e}")
        raise


async def demo_comprehensive_analytics(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate comprehensive analytics data collection."""
    print("\n2. Collecting comprehensive analytics data...")
    
    try:
        # Wait for initial data collection
        await asyncio.sleep(2)
        
        # Get comprehensive analytics
        analytics = analytics_dashboard.get_comprehensive_analytics(AnalyticsTimeframe.DAY)
        
        if not analytics:
            print("⚠️  Analytics data not yet available, waiting for collection...")
            await asyncio.sleep(5)
            analytics = analytics_dashboard.get_comprehensive_analytics(AnalyticsTimeframe.DAY)
        
        if analytics:
            print("✓ Comprehensive analytics data collected")
            
            # Display key metrics
            print(f"\n📊 Analytics Summary (Timeframe: {analytics.timeframe}):")
            print(f"   Timestamp: {analytics.timestamp}")
            
            # User Analytics
            user_analytics = analytics.user_analytics
            print(f"\n👥 User Analytics:")
            print(f"   Total Users: {user_analytics.total_users:,}")
            print(f"   Active Users (24h): {user_analytics.active_users_24h:,}")
            print(f"   New Users (24h): {user_analytics.new_users_24h:,}")
            print(f"   User Retention Rate: {user_analytics.user_retention_rate:.1%}")
            print(f"   User Engagement Score: {user_analytics.user_engagement_score:.1f}/10")
            print(f"   Avg Session Duration: {user_analytics.avg_session_duration_minutes:.1f} minutes")
            
            # Recommendation Quality
            rec_quality = analytics.recommendation_quality
            print(f"\n🎯 Recommendation Quality:")
            print(f"   Total Recommendations: {rec_quality.total_recommendations:,}")
            print(f"   Avg Confidence Score: {rec_quality.avg_confidence_score:.2f}")
            print(f"   User Satisfaction: {rec_quality.user_satisfaction_score:.1f}/5.0")
            print(f"   Implementation Success Rate: {rec_quality.implementation_success_rate:.1%}")
            print(f"   Recommendation Accuracy: {rec_quality.recommendation_accuracy:.1%}")
            print(f"   Cost Savings Achieved: ${rec_quality.cost_savings_achieved:,.0f}")
            
            # System Performance
            sys_perf = analytics.system_performance
            print(f"\n⚡ System Performance:")
            print(f"   Avg Response Time: {sys_perf.avg_response_time_ms:.0f}ms")
            print(f"   P95 Response Time: {sys_perf.p95_response_time_ms:.0f}ms")
            print(f"   Error Rate: {sys_perf.error_rate_percent:.2f}%")
            print(f"   Throughput: {sys_perf.throughput_requests_per_minute:.0f} req/min")
            print(f"   System Availability: {sys_perf.system_availability_percent:.1f}%")
            
            # Alert Analytics
            alert_analytics = analytics.alert_analytics
            print(f"\n🚨 Alert Analytics:")
            print(f"   Active Alerts: {alert_analytics.active_alerts}")
            print(f"   Alerts (24h): {alert_analytics.total_alerts_24h}")
            print(f"   Resolved (24h): {alert_analytics.resolved_alerts_24h}")
            print(f"   Avg Resolution Time: {alert_analytics.avg_resolution_time_minutes:.0f} minutes")
            
            return analytics
        else:
            print("❌ Failed to collect analytics data")
            return None
            
    except Exception as e:
        logger.error(f"Error collecting comprehensive analytics: {e}")
        return None


async def demo_user_behavior_analysis(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate user behavior analysis."""
    print("\n3. Analyzing user behavior patterns...")
    
    try:
        analytics = analytics_dashboard.get_comprehensive_analytics()
        if not analytics:
            print("❌ Analytics data not available")
            return
        
        user_analytics = analytics.user_analytics
        
        print("✓ User behavior analysis completed")
        
        # Geographic distribution
        print(f"\n🌍 Geographic Distribution:")
        for region, percentage in user_analytics.geographic_distribution.items():
            print(f"   {region}: {percentage}%")
        
        # Company size distribution
        print(f"\n🏢 Company Size Distribution:")
        for size, percentage in user_analytics.company_size_distribution.items():
            print(f"   {size.title()}: {percentage}%")
        
        # Industry distribution
        print(f"\n🏭 Industry Distribution:")
        for industry, percentage in user_analytics.industry_distribution.items():
            print(f"   {industry.title()}: {percentage}%")
        
        # Feature usage
        print(f"\n🔧 Feature Usage:")
        for feature, usage in user_analytics.feature_usage.items():
            print(f"   {feature.title()}: {usage:,} uses")
        
        # User journey patterns
        print(f"\n🛤️  User Journey Patterns:")
        for pattern in user_analytics.user_journey_patterns:
            print(f"   {pattern['pattern']}: {pattern['frequency']}% frequency, {pattern['success_rate']}% success")
        
    except Exception as e:
        logger.error(f"Error analyzing user behavior: {e}")


async def demo_recommendation_quality_tracking(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate recommendation quality tracking."""
    print("\n4. Tracking recommendation quality metrics...")
    
    try:
        analytics = analytics_dashboard.get_comprehensive_analytics()
        if not analytics:
            print("❌ Analytics data not available")
            return
        
        rec_quality = analytics.recommendation_quality
        
        print("✓ Recommendation quality tracking completed")
        
        # Agent performance breakdown
        print(f"\n🤖 Agent Performance Breakdown:")
        for agent_name, performance in rec_quality.agent_performance_breakdown.items():
            print(f"   {agent_name}:")
            print(f"     Executions: {performance.get('executions', 0)}")
            print(f"     Success Rate: {performance.get('success_rate', 0):.1%}")
            print(f"     Avg Confidence: {performance.get('avg_confidence', 0):.2f}")
        
        # Quality trends
        print(f"\n📈 Quality Trends:")
        for metric, trend in rec_quality.quality_trends.items():
            trend_symbol = "📈" if trend.trend == "up" else "📉" if trend.trend == "down" else "➡️"
            print(f"   {metric.title()}: {trend_symbol} {trend.change_percent:+.1f}% (confidence: {trend.confidence:.0%})")
        
        # Feedback distribution
        print(f"\n💬 User Feedback Distribution:")
        for rating, count in rec_quality.feedback_distribution.items():
            print(f"   {rating.title()}: {count}%")
        
        # Recommendation categories
        print(f"\n📂 Recommendation Categories:")
        for category, percentage in rec_quality.recommendation_categories.items():
            print(f"   {category.replace('_', ' ').title()}: {percentage}%")
        
    except Exception as e:
        logger.error(f"Error tracking recommendation quality: {e}")


async def demo_system_performance_monitoring(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate system performance monitoring."""
    print("\n5. Monitoring system performance...")
    
    try:
        analytics = analytics_dashboard.get_comprehensive_analytics()
        if not analytics:
            print("❌ Analytics data not available")
            return
        
        sys_perf = analytics.system_performance
        
        print("✓ System performance monitoring completed")
        
        # Resource utilization
        print(f"\n💻 Resource Utilization:")
        for resource, usage in sys_perf.resource_utilization.items():
            status = "🔴" if usage > 80 else "🟡" if usage > 60 else "🟢"
            print(f"   {resource.upper()}: {status} {usage:.1f}%")
        
        # Performance trends
        print(f"\n📊 Performance Trends:")
        for metric, trend in sys_perf.performance_trends.items():
            trend_symbol = "📈" if trend.trend == "up" else "📉" if trend.trend == "down" else "➡️"
            print(f"   {metric.replace('_', ' ').title()}: {trend_symbol} {trend.change_percent:+.1f}%")
        
        # Bottleneck analysis
        print(f"\n🚧 Bottleneck Analysis:")
        for bottleneck in sys_perf.bottleneck_analysis:
            severity = "🔴" if bottleneck['impact_score'] > 7 else "🟡" if bottleneck['impact_score'] > 5 else "🟢"
            print(f"   {bottleneck['component']}: {severity} Impact {bottleneck['impact_score']:.1f}/10")
            print(f"     Description: {bottleneck['description']}")
            print(f"     Recommendation: {bottleneck['recommendation']}")
        
        # Capacity projections
        print(f"\n🔮 Capacity Projections (30 days):")
        for metric, value in sys_perf.capacity_projections.items():
            print(f"   {metric.replace('_', ' ').title()}: {value:,}" + 
                  (" users" if "users" in metric else " GB" if "storage" in metric else ""))
        
    except Exception as e:
        logger.error(f"Error monitoring system performance: {e}")


async def demo_alert_analytics(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate alert analytics and patterns."""
    print("\n6. Analyzing alert patterns...")
    
    try:
        analytics = analytics_dashboard.get_comprehensive_analytics()
        if not analytics:
            print("❌ Analytics data not available")
            return
        
        alert_analytics = analytics.alert_analytics
        
        print("✓ Alert analytics completed")
        
        # Alert frequency by type
        print(f"\n🚨 Alert Frequency by Type:")
        for alert_type, count in alert_analytics.alert_frequency_by_type.items():
            print(f"   {alert_type.replace('_', ' ').title()}: {count}")
        
        # Alert severity distribution
        print(f"\n⚠️  Alert Severity Distribution:")
        for severity, count in alert_analytics.alert_severity_distribution.items():
            severity_icon = "🔴" if severity == "critical" else "🟡" if severity == "high" else "🔵"
            print(f"   {severity_icon} {severity.title()}: {count}")
        
        # Most common issues
        print(f"\n🔍 Most Common Issues:")
        for issue in alert_analytics.most_common_issues:
            print(f"   {issue['issue']}: {issue['count']} occurrences ({issue['percentage']:.1f}%)")
        
        # Alert trends
        print(f"\n📈 Alert Trends:")
        for metric, trend in alert_analytics.alert_trends.items():
            trend_symbol = "📈" if trend.trend == "up" else "📉" if trend.trend == "down" else "➡️"
            print(f"   {metric.replace('_', ' ').title()}: {trend_symbol} {trend.change_percent:+.1f}%")
        
        # Escalation patterns
        print(f"\n🔄 Escalation Patterns:")
        for pattern in alert_analytics.escalation_patterns:
            print(f"   {pattern['pattern']}: {pattern['frequency']} occurrences")
            print(f"     Avg Escalation Time: {pattern['avg_escalation_time_minutes']} minutes")
        
    except Exception as e:
        logger.error(f"Error analyzing alerts: {e}")


async def demo_predictive_analytics(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate predictive analytics and forecasting."""
    print("\n7. Generating predictive analytics...")
    
    try:
        analytics = analytics_dashboard.get_comprehensive_analytics()
        if not analytics:
            print("❌ Analytics data not available")
            return
        
        predictive = analytics.predictive_analytics
        
        print("✓ Predictive analytics generated")
        
        # User growth forecast
        if 'user_forecast' in predictive:
            user_forecast = predictive['user_forecast']
            print(f"\n👥 User Growth Forecast:")
            print(f"   Next Month: {user_forecast['next_month']:,} users")
            print(f"   Next Quarter: {user_forecast['next_quarter']:,} users")
            print(f"   Next Year: {user_forecast['next_year']:,} users")
            print(f"   Confidence: {user_forecast['confidence']:.0%}")
        
        # System load forecast
        if 'load_forecast' in predictive:
            load_forecast = predictive['load_forecast']
            print(f"\n⚡ System Load Forecast:")
            print(f"   Next Month: {load_forecast['next_month_rpm']:,} req/min")
            print(f"   Next Quarter: {load_forecast['next_quarter_rpm']:,} req/min")
            print(f"   Scaling Needed: {load_forecast['scaling_needed_date']}")
            print(f"   Confidence: {load_forecast['confidence']:.0%}")
        
        # Cost forecast
        if 'cost_forecast' in predictive:
            cost_forecast = predictive['cost_forecast']
            print(f"\n💰 Cost Forecast:")
            print(f"   Next Month: ${cost_forecast['next_month']:,}")
            print(f"   Next Quarter: ${cost_forecast['next_quarter']:,}")
            print(f"   Optimization Potential: {cost_forecast['optimization_potential']:.0%}")
            print(f"   Confidence: {cost_forecast['confidence']:.0%}")
        
        # Failure prediction
        if 'failure_prediction' in predictive:
            failure_pred = predictive['failure_prediction']
            print(f"\n🚨 Failure Risk Assessment:")
            print(f"   Risk Score: {failure_pred['risk_score']:.0%}")
            print(f"   Most Likely Failure Points:")
            for component in failure_pred['most_likely_failure_points']:
                risk_level = "🔴" if component['risk'] > 0.2 else "🟡" if component['risk'] > 0.1 else "🟢"
                print(f"     {component['component']}: {risk_level} {component['risk']:.0%} risk")
        
        # Operational insights
        print(f"\n💡 Operational Insights:")
        for insight in analytics.operational_insights[:3]:
            priority_icon = "🔴" if insight['priority'] == 'critical' else "🟡" if insight['priority'] == 'high' else "🔵"
            print(f"   {priority_icon} {insight['title']}")
            print(f"     {insight['description']}")
            print(f"     Recommendation: {insight['recommendation']}")
            print(f"     Impact: {insight['impact']}")
        
    except Exception as e:
        logger.error(f"Error generating predictive analytics: {e}")


async def demo_historical_data_analysis(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate historical data analysis."""
    print("\n8. Analyzing historical data trends...")
    
    try:
        # Get historical data for key metrics
        metrics_to_analyze = [
            "user_engagement_score",
            "recommendation_accuracy",
            "system_response_time",
            "error_rate",
            "active_alerts"
        ]
        
        print("✓ Historical data analysis completed")
        
        for metric in metrics_to_analyze:
            historical_data = analytics_dashboard.get_historical_data(metric, AnalyticsTimeframe.DAY)
            
            if historical_data:
                values = [data["value"] for data in historical_data]
                print(f"\n📊 {metric.replace('_', ' ').title()}:")
                print(f"   Data Points: {len(historical_data)}")
                print(f"   Current Value: {values[-1]:.2f}")
                print(f"   Min: {min(values):.2f}")
                print(f"   Max: {max(values):.2f}")
                print(f"   Average: {sum(values)/len(values):.2f}")
            else:
                print(f"\n📊 {metric.replace('_', ' ').title()}: No historical data available")
        
    except Exception as e:
        logger.error(f"Error analyzing historical data: {e}")


async def demo_performance_comparison(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate performance comparison against baselines."""
    print("\n9. Comparing performance against baselines...")
    
    try:
        comparison = analytics_dashboard.get_performance_comparison()
        
        if comparison:
            print("✓ Performance comparison completed")
            
            print(f"\n📊 Performance vs Baselines:")
            for metric, data in comparison.items():
                status_icon = "🟢" if data['status'] == 'improved' else "🔴" if data['status'] == 'degraded' else "➡️"
                print(f"   {metric.replace('_', ' ').title()}: {status_icon}")
                print(f"     Current: {data['current']:.2f}")
                print(f"     Baseline: {data['baseline']:.2f}")
                print(f"     Change: {data['change_percent']:+.1f}%")
                print(f"     Status: {data['status'].title()}")
        else:
            print("❌ Performance comparison data not available")
        
    except Exception as e:
        logger.error(f"Error comparing performance: {e}")


async def demo_dashboard_export(analytics_dashboard: AnalyticsDashboard):
    """Demonstrate analytics dashboard export functionality."""
    print("\n10. Exporting analytics report...")
    
    try:
        # Export analytics report
        report_data = analytics_dashboard.export_analytics_report("json")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            f.write(report_data)
        
        print(f"✓ Analytics report exported to {filename}")
        
        # Display summary
        report_dict = json.loads(report_data)
        print(f"\n📄 Report Summary:")
        print(f"   Generated: {report_dict['report_generated']}")
        print(f"   Historical Data Points: {sum(report_dict['historical_summary'].values())}")
        print(f"   Performance Comparisons: {len(report_dict['performance_comparison'])}")
        print(f"   Alert Thresholds: {len(report_dict['alert_thresholds'])}")
        
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")


async def main():
    """Main demo function."""
    try:
        # Initialize analytics dashboard
        analytics_dashboard = await demo_analytics_initialization()
        
        # Run comprehensive demos
        await demo_comprehensive_analytics(analytics_dashboard)
        await demo_user_behavior_analysis(analytics_dashboard)
        await demo_recommendation_quality_tracking(analytics_dashboard)
        await demo_system_performance_monitoring(analytics_dashboard)
        await demo_alert_analytics(analytics_dashboard)
        await demo_predictive_analytics(analytics_dashboard)
        await demo_historical_data_analysis(analytics_dashboard)
        await demo_performance_comparison(analytics_dashboard)
        await demo_dashboard_export(analytics_dashboard)
        
        print("\n" + "="*60)
        print("COMPREHENSIVE ANALYTICS DASHBOARD DEMO COMPLETED")
        print("="*60)
        print("\n✅ All analytics features demonstrated successfully!")
        print("\n📊 Key Features Demonstrated:")
        print("   • User behavior analysis and engagement tracking")
        print("   • Recommendation quality metrics and agent performance")
        print("   • System performance monitoring and bottleneck analysis")
        print("   • Alert analytics and escalation patterns")
        print("   • Predictive analytics and capacity forecasting")
        print("   • Historical data analysis and trend tracking")
        print("   • Performance comparison against baselines")
        print("   • Comprehensive analytics report export")
        
        print("\n🎯 Business Value:")
        print("   • Data-driven decision making for system optimization")
        print("   • Proactive issue identification and resolution")
        print("   • User experience insights for product improvement")
        print("   • Cost optimization and capacity planning")
        print("   • Quality assurance for AI recommendations")
        
        # Keep dashboard running for a bit
        print("\n⏳ Keeping analytics dashboard running for 30 seconds...")
        await asyncio.sleep(30)
        
        # Cleanup
        print("\n🧹 Shutting down analytics dashboard...")
        await analytics_dashboard.stop()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
    finally:
        print("\n👋 Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())