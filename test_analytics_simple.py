#!/usr/bin/env python3
"""
Simple test for analytics dashboard components.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_analytics_imports():
    """Test importing analytics components."""
    try:
        print("Testing analytics dashboard imports...")
        
        # Test basic imports
        from infra_mind.orchestration.analytics_dashboard import (
            AnalyticsDashboard, AnalyticsTimeframe, TrendAnalysis, MetricTrend
        )
        print("✓ Analytics dashboard imports successful")
        
        # Test trend analysis
        values = [10, 12, 14, 16, 18]
        trend = TrendAnalysis.calculate(values)
        print(f"✓ Trend analysis working: {trend.trend.value} trend with {trend.change_percent:.1f}% change")
        
        # Test timeframes
        timeframes = list(AnalyticsTimeframe)
        print(f"✓ Available timeframes: {[tf.value for tf in timeframes]}")
        
        print("\n🎉 All analytics components imported and tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing analytics imports: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("="*60)
    print("SIMPLE ANALYTICS DASHBOARD TEST")
    print("="*60)
    
    success = await test_analytics_imports()
    
    if success:
        print("\n✅ Analytics dashboard components are working correctly!")
    else:
        print("\n❌ Analytics dashboard test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())