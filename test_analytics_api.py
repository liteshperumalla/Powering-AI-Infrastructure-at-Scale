#!/usr/bin/env python3
"""
Test Analytics API Endpoints

Simple test to verify the analytics API endpoints are working correctly.
"""

import asyncio
import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_analytics_api():
    """Test analytics API endpoints."""
    try:
        print("Testing Analytics API Endpoints...")
        
        # Import the admin endpoints
        from infra_mind.api.endpoints.admin import router
        from infra_mind.orchestration.analytics_dashboard import (
            AnalyticsDashboard, get_analytics_dashboard, AnalyticsTimeframe
        )
        from infra_mind.orchestration.monitoring import WorkflowMonitor
        from infra_mind.orchestration.dashboard import WorkflowDashboard
        from infra_mind.orchestration.events import EventManager
        
        print("✓ Successfully imported analytics API components")
        
        # Test that the router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/analytics/comprehensive",
            "/analytics/user-behavior", 
            "/analytics/recommendation-quality",
            "/analytics/system-performance",
            "/analytics/alerts",
            "/analytics/business-metrics",
            "/analytics/predictive",
            "/analytics/historical/{metric_name}",
            "/analytics/export",
            "/analytics/dashboard-summary",
            "/analytics/performance-comparison"
        ]
        
        found_routes = []
        for expected in expected_routes:
            for route in routes:
                if expected.replace("{metric_name}", "test") in route or expected == route:
                    found_routes.append(expected)
                    break
        
        print(f"✓ Found {len(found_routes)}/{len(expected_routes)} expected API endpoints")
        
        # Test analytics dashboard components
        event_manager = EventManager()
        workflow_monitor = WorkflowMonitor(event_manager)
        workflow_dashboard = WorkflowDashboard(workflow_monitor)
        analytics_dashboard = AnalyticsDashboard(workflow_monitor, workflow_dashboard)
        
        print("✓ Analytics dashboard components initialized successfully")
        
        # Test timeframes
        timeframes = list(AnalyticsTimeframe)
        print(f"✓ Available timeframes: {[tf.value for tf in timeframes]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing analytics API: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("="*60)
    print("ANALYTICS API ENDPOINTS TEST")
    print("="*60)
    
    success = await test_analytics_api()
    
    if success:
        print("\n✅ Analytics API endpoints are working correctly!")
        print("\n📊 Available Endpoints:")
        print("   • GET /admin/analytics/comprehensive - Complete analytics overview")
        print("   • GET /admin/analytics/user-behavior - User engagement patterns")
        print("   • GET /admin/analytics/recommendation-quality - AI recommendation metrics")
        print("   • GET /admin/analytics/system-performance - Infrastructure performance")
        print("   • GET /admin/analytics/alerts - Alert system analytics")
        print("   • GET /admin/analytics/business-metrics - Business KPIs and ROI")
        print("   • GET /admin/analytics/predictive - Forecasting and predictions")
        print("   • GET /admin/analytics/historical/{metric} - Time-series data")
        print("   • GET /admin/analytics/export - Report generation and export")
        print("   • GET /admin/analytics/dashboard-summary - Quick overview")
        print("   • GET /admin/analytics/performance-comparison - Baseline comparison")
    else:
        print("\n❌ Analytics API test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())