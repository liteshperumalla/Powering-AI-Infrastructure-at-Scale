#!/usr/bin/env python3
"""
Demo script for metrics collection system.

Demonstrates basic metrics collection for system performance, user engagement,
and system health monitoring as implemented in task 12.1.
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from infra_mind.core.metrics_collector import (
    MetricsCollector,
    get_metrics_collector,
    initialize_metrics_collection,
    shutdown_metrics_collection
)
from infra_mind.models.metrics import Metric, AgentMetrics, MetricType, MetricCategory
from infra_mind.core.database import init_database, close_database


async def demo_basic_metrics_collection():
    """Demonstrate basic metrics collection functionality."""
    print("🔍 Demo: Basic Metrics Collection")
    print("=" * 50)
    
    # Get metrics collector
    collector = get_metrics_collector()
    
    # Simulate some system activity
    print("\n📊 Simulating system activity...")
    
    # Track some API requests
    for i in range(10):
        response_time = 100 + (i * 20)  # Simulate varying response times
        success = i < 8  # Simulate some failures
        collector.track_request(response_time, success)
        print(f"  Request {i+1}: {response_time}ms, Success: {success}")
    
    # Track user actions
    print("\n👥 Simulating user engagement...")
    user_actions = [
        ("user1", "assessment_started", {"source": "web"}),
        ("user2", "dashboard_viewed", {"page": "main"}),
        ("user1", "assessment_completed", {"duration": 300}),
        ("user3", "report_generated", {"format": "pdf"}),
        ("user2", "recommendations_viewed", {"count": 5})
    ]
    
    for user_id, action_type, metadata in user_actions:
        collector.track_user_action(user_id, action_type, metadata)
        print(f"  User {user_id}: {action_type}")
    
    # Collect system metrics manually
    print("\n🖥️  Collecting system metrics...")
    await collector.collect_system_metrics()
    print("  ✅ System performance metrics collected")
    
    await collector.collect_health_metrics()
    print("  ✅ Health monitoring metrics collected")
    
    await collector.collect_user_engagement_metrics()
    print("  ✅ User engagement metrics collected")
    
    print("\n✅ Basic metrics collection demo completed!")


async def demo_agent_performance_tracking():
    """Demonstrate agent performance tracking."""
    print("\n🤖 Demo: Agent Performance Tracking")
    print("=" * 50)
    
    collector = get_metrics_collector()
    
    # Simulate different agent executions
    agents = [
        ("cto_agent", 2.5, True, 0.85, 3),
        ("cloud_engineer_agent", 4.2, True, 0.92, 5),
        ("research_agent", 1.8, True, 0.78, 2),
        ("report_generator_agent", 3.1, False, None, 0),  # Failed execution
    ]
    
    print("\n📈 Recording agent performance metrics...")
    
    for agent_name, exec_time, success, confidence, rec_count in agents:
        await collector.record_agent_performance(
            agent_name=agent_name,
            execution_time=exec_time,
            success=success,
            confidence_score=confidence,
            recommendations_count=rec_count,
            assessment_id="demo_assessment_123"
        )
        
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {agent_name}: {exec_time}s, {status}, Confidence: {confidence or 'N/A'}")
    
    print("\n✅ Agent performance tracking demo completed!")


async def demo_system_health_monitoring():
    """Demonstrate system health monitoring."""
    print("\n🏥 Demo: System Health Monitoring")
    print("=" * 50)
    
    collector = get_metrics_collector()
    
    # Get current system health
    print("\n📋 Current system health status:")
    health = await collector.get_system_health()
    
    print(f"  Status: {health.status.upper()}")
    print(f"  CPU Usage: {health.cpu_usage_percent:.1f}%")
    print(f"  Memory Usage: {health.memory_usage_percent:.1f}%")
    print(f"  Disk Usage: {health.disk_usage_percent:.1f}%")
    print(f"  Active Connections: {health.active_connections}")
    print(f"  Avg Response Time: {health.response_time_ms:.1f}ms")
    print(f"  Error Rate: {health.error_rate_percent:.1f}%")
    print(f"  Uptime: {health.uptime_seconds:.0f} seconds")
    
    # Get user engagement summary
    print("\n👥 User engagement summary:")
    engagement = await collector.get_user_engagement_summary()
    
    print(f"  Active Users: {engagement.active_users_count}")
    print(f"  Assessments Started: {engagement.assessments_started}")
    print(f"  Assessments Completed: {engagement.assessments_completed}")
    print(f"  Reports Generated: {engagement.reports_generated}")
    print(f"  Avg Session Duration: {engagement.average_session_duration_minutes:.1f} minutes")
    
    print("\n✅ System health monitoring demo completed!")


async def demo_operation_tracking():
    """Demonstrate operation tracking with context manager."""
    print("\n⚡ Demo: Operation Tracking")
    print("=" * 50)
    
    collector = get_metrics_collector()
    
    # Track different operations
    operations = [
        ("database_query", 0.1, False),
        ("api_call", 0.3, False),
        ("report_generation", 2.0, False),
        ("failing_operation", 0.5, True)  # This will fail
    ]
    
    print("\n📊 Tracking various operations...")
    
    for op_name, duration, should_fail in operations:
        try:
            async with collector.track_operation(op_name):
                await asyncio.sleep(duration)
                if should_fail:
                    raise ValueError(f"Simulated failure in {op_name}")
                print(f"  ✅ {op_name}: {duration}s")
        except ValueError as e:
            print(f"  ❌ {op_name}: Failed - {e}")
    
    print("\n✅ Operation tracking demo completed!")


async def demo_metrics_collection_lifecycle():
    """Demonstrate metrics collection lifecycle."""
    print("\n🔄 Demo: Metrics Collection Lifecycle")
    print("=" * 50)
    
    collector = get_metrics_collector()
    
    print("\n🚀 Starting automatic metrics collection...")
    await collector.start_collection()
    print("  ✅ Metrics collection started")
    
    # Let it run for a few seconds
    print("\n⏱️  Letting metrics collection run for 5 seconds...")
    await asyncio.sleep(5)
    
    # Generate some activity during collection
    print("\n📊 Generating activity during collection...")
    for i in range(5):
        collector.track_request(150 + i * 10, True)
        collector.track_user_action(f"user{i}", "test_action", {"test": True})
        await asyncio.sleep(0.5)
    
    print("\n🛑 Stopping metrics collection...")
    await collector.stop_collection()
    print("  ✅ Metrics collection stopped")
    
    print("\n✅ Metrics collection lifecycle demo completed!")


async def demo_metrics_export():
    """Demonstrate metrics data export."""
    print("\n📤 Demo: Metrics Data Export")
    print("=" * 50)
    
    collector = get_metrics_collector()
    
    # Create some sample metrics data
    sample_metrics = {
        "system_health": await collector.get_system_health(),
        "user_engagement": await collector.get_user_engagement_summary(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Convert to JSON-serializable format
    export_data = {
        "system_health": {
            "status": sample_metrics["system_health"].status,
            "cpu_usage_percent": sample_metrics["system_health"].cpu_usage_percent,
            "memory_usage_percent": sample_metrics["system_health"].memory_usage_percent,
            "disk_usage_percent": sample_metrics["system_health"].disk_usage_percent,
            "active_connections": sample_metrics["system_health"].active_connections,
            "response_time_ms": sample_metrics["system_health"].response_time_ms,
            "error_rate_percent": sample_metrics["system_health"].error_rate_percent,
            "uptime_seconds": sample_metrics["system_health"].uptime_seconds,
            "timestamp": sample_metrics["system_health"].timestamp.isoformat()
        },
        "user_engagement": {
            "active_users_count": sample_metrics["user_engagement"].active_users_count,
            "assessments_started": sample_metrics["user_engagement"].assessments_started,
            "assessments_completed": sample_metrics["user_engagement"].assessments_completed,
            "reports_generated": sample_metrics["user_engagement"].reports_generated,
            "average_session_duration_minutes": sample_metrics["user_engagement"].average_session_duration_minutes,
            "bounce_rate_percent": sample_metrics["user_engagement"].bounce_rate_percent,
            "timestamp": sample_metrics["user_engagement"].timestamp.isoformat()
        },
        "export_timestamp": sample_metrics["timestamp"]
    }
    
    print("\n📊 Sample metrics export (JSON format):")
    print(json.dumps(export_data, indent=2))
    
    print("\n✅ Metrics data export demo completed!")


async def main():
    """Run all metrics collection demos."""
    print("🎯 Infra Mind - Metrics Collection System Demo")
    print("=" * 60)
    print("Demonstrating task 12.1: Basic metrics collection for:")
    print("• System performance monitoring")
    print("• User engagement tracking") 
    print("• System health monitoring")
    print("=" * 60)
    
    try:
        # Initialize database (in memory for demo)
        print("\n🔧 Initializing demo environment...")
        # Note: In a real environment, you would call init_database()
        # For demo purposes, we'll skip database initialization
        
        # Run all demos
        await demo_basic_metrics_collection()
        await demo_agent_performance_tracking()
        await demo_system_health_monitoring()
        await demo_operation_tracking()
        await demo_metrics_collection_lifecycle()
        await demo_metrics_export()
        
        print("\n" + "=" * 60)
        print("🎉 All metrics collection demos completed successfully!")
        print("=" * 60)
        
        print("\n📋 Summary of implemented features:")
        print("✅ System performance metrics (CPU, memory, disk, network)")
        print("✅ User engagement tracking (sessions, actions, patterns)")
        print("✅ System health monitoring (status, error rates, uptime)")
        print("✅ Agent performance tracking (execution time, success rates)")
        print("✅ Operation tracking with context managers")
        print("✅ Automatic metrics collection lifecycle")
        print("✅ Metrics data export capabilities")
        
        print("\n🔗 Integration points:")
        print("• FastAPI middleware for automatic request tracking")
        print("• Agent base class integration for performance monitoring")
        print("• Health check endpoints (/health, /metrics)")
        print("• MongoDB storage for persistent metrics")
        print("• Redis caching for real-time data")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up demo environment...")
        try:
            await shutdown_metrics_collection()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())