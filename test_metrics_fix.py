#!/usr/bin/env python3
"""
Test script to check metrics collection issues.
"""

import sys
import os
import asyncio
import logging

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging to see detailed errors
logging.basicConfig(level=logging.DEBUG)

from infra_mind.core.metrics_collector import MetricsCollector

async def test_metrics():
    """Test metrics collection to identify specific issues."""
    print("🧪 Testing metrics collection...")
    
    collector = MetricsCollector()
    
    try:
        print("1. Testing system metrics collection...")
        await collector.collect_system_metrics()
        print("✅ System metrics collection successful")
    except Exception as e:
        print(f"❌ System metrics collection failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("2. Testing health metrics collection...")
        await collector.collect_health_metrics()
        print("✅ Health metrics collection successful")
    except Exception as e:
        print(f"❌ Health metrics collection failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("3. Testing user engagement metrics collection...")
        await collector.collect_user_engagement_metrics()
        print("✅ User engagement metrics collection successful")
    except Exception as e:
        print(f"❌ User engagement metrics collection failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("4. Testing business metrics collection...")
        await collector.collect_business_metrics()
        print("✅ Business metrics collection successful")
    except Exception as e:
        print(f"❌ Business metrics collection failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("5. Testing real-time metrics collection...")
        await collector._collect_real_time_metrics()
        print("✅ Real-time metrics collection successful")
    except Exception as e:
        print(f"❌ Real-time metrics collection failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("6. Testing system health...")
        health = await collector.get_system_health()
        print(f"✅ System health successful: {health.status}")
    except Exception as e:
        print(f"❌ System health failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_metrics())