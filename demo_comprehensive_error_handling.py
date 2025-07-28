#!/usr/bin/env python3
"""
Comprehensive Error Handling System Demo.

Demonstrates retry mechanisms, graceful degradation, fallback mechanisms,
and comprehensive error logging and monitoring.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone

from src.infra_mind.core.error_handling import (
    error_handler, ErrorContext, ErrorCategory, ErrorSeverity
)
from src.infra_mind.core.error_monitoring import error_monitor
from src.infra_mind.core.advanced_logging import setup_advanced_logging, log_context
from src.infra_mind.core.resilience import resilience_manager


# Setup logging
setup_advanced_logging(log_level="INFO", enable_console=True, enable_structured=True)
logger = logging.getLogger(__name__)


class MockAPIService:
    """Mock API service for testing error handling."""
    
    def __init__(self, name: str, failure_rate: float = 0.3):
        """
        Initialize mock API service.
        
        Args:
            name: Service name
            failure_rate: Probability of failure (0.0 to 1.0)
        """
        self.name = name
        self.failure_rate = failure_rate
        self.call_count = 0
    
    async def make_api_call(self, operation: str) -> dict:
        """Simulate API call that may fail."""
        self.call_count += 1
        
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Randomly fail based on failure rate
        if random.random() < self.failure_rate:
            error_types = [
                ConnectionError("Connection failed"),
                TimeoutError("Request timed out"),
                Exception("Service unavailable"),
                ValueError("Invalid request format")
            ]
            raise random.choice(error_types)
        
        return {
            "service": self.name,
            "operation": operation,
            "data": f"Success from {self.name}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "call_count": self.call_count
        }


class MockAgent:
    """Mock agent for testing agent error handling."""
    
    def __init__(self, name: str):
        """Initialize mock agent."""
        self.name = name
        self.api_service = MockAPIService(f"{name}_api", failure_rate=0.4)
    
    async def execute_task(self, task: str) -> dict:
        """Execute agent task that may fail."""
        logger.info(f"Agent {self.name} executing task: {task}")
        
        try:
            # Simulate agent work with API calls
            api_result = await self.api_service.make_api_call(task)
            
            # Simulate processing
            await asyncio.sleep(random.uniform(0.2, 0.8))
            
            # Sometimes fail during processing
            if random.random() < 0.2:
                raise RuntimeError(f"Agent {self.name} processing failed")
            
            return {
                "agent": self.name,
                "task": task,
                "result": api_result,
                "recommendations": [f"Recommendation {i}" for i in range(3)],
                "confidence": random.uniform(0.7, 0.95)
            }
            
        except Exception as e:
            logger.error(f"Agent {self.name} task failed: {str(e)}")
            raise


async def demo_basic_error_handling():
    """Demonstrate basic error handling with retry and fallback."""
    print("\n" + "="*60)
    print("DEMO: Basic Error Handling")
    print("="*60)
    
    service = MockAPIService("pricing_service", failure_rate=0.6)
    
    # Configure error handling for the service
    error_handler.configure_service_error_handling(
        service_name="pricing_service",
        failure_threshold=3,
        max_retries=3
    )
    
    # Test with error handling
    async with error_handler.handle_errors(
        operation="get_pricing_data",
        component="api_client",
        service_name="pricing_service",
        fallback_data={"prices": [], "fallback_mode": True}
    ) as handle_error:
        
        try:
            result = await handle_error(service.make_api_call, "get_pricing")
            print(f"✅ Success: {result}")
        except Exception as e:
            print(f"❌ Failed even with error handling: {str(e)}")


async def demo_agent_error_handling():
    """Demonstrate agent-specific error handling."""
    print("\n" + "="*60)
    print("DEMO: Agent Error Handling")
    print("="*60)
    
    agent = MockAgent("cto_agent")
    
    # Test multiple agent executions
    tasks = ["analyze_infrastructure", "generate_recommendations", "create_roadmap"]
    
    for task in tasks:
        print(f"\n🤖 Testing agent task: {task}")
        
        try:
            # Use agent error handling
            recovery_result = await error_handler.handle_agent_error(
                agent_name=agent.name,
                operation=f"execute_{task}",
                exception=Exception("Simulated agent error"),
                workflow_id="demo_workflow",
                fallback_data={
                    "recommendations": ["Fallback recommendation"],
                    "confidence": 0.5,
                    "fallback_mode": True
                }
            )
            
            if recovery_result.success:
                print(f"✅ Agent recovered: {recovery_result.strategy_used.value}")
                print(f"   Data: {recovery_result.data}")
            else:
                print(f"❌ Agent recovery failed: {recovery_result.strategy_used.value}")
                
        except Exception as e:
            print(f"❌ Agent execution failed: {str(e)}")


async def demo_resilience_patterns():
    """Demonstrate resilience patterns (circuit breaker, retry, fallback)."""
    print("\n" + "="*60)
    print("DEMO: Resilience Patterns")
    print("="*60)
    
    # Create a service that will trigger circuit breaker
    failing_service = MockAPIService("failing_service", failure_rate=0.9)
    
    # Configure resilience
    error_handler.configure_service_error_handling(
        service_name="failing_service",
        failure_threshold=2,  # Low threshold for demo
        recovery_timeout=5,
        max_retries=2
    )
    
    print("🔄 Making multiple calls to trigger circuit breaker...")
    
    # Make multiple calls to trigger circuit breaker
    for i in range(8):
        print(f"\n📞 Call {i+1}:")
        
        try:
            async with resilience_manager.resilient_call(
                service_name="failing_service",
                fallback_key="failing_service_data",
                default_data={"fallback": True, "message": "Service unavailable"}
            ) as execute:
                
                result = await execute(failing_service.make_api_call, "test_operation")
                
                if result.get("fallback_used"):
                    print(f"🔄 Fallback used: {result['source']}")
                    if result.get("degraded_mode"):
                        print("⚠️  Operating in degraded mode")
                else:
                    print(f"✅ Success: {result['data']}")
                    
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Small delay between calls
        await asyncio.sleep(0.5)
    
    # Show circuit breaker status
    health = resilience_manager.get_service_health("failing_service")
    print(f"\n🏥 Service health: {health}")


async def demo_error_monitoring():
    """Demonstrate error monitoring and alerting."""
    print("\n" + "="*60)
    print("DEMO: Error Monitoring and Alerting")
    print("="*60)
    
    # Start error monitoring
    await error_monitor.start_monitoring(check_interval_seconds=2)
    
    print("📊 Starting error monitoring...")
    print("🚨 Generating errors to trigger alerts...")
    
    # Generate various types of errors
    error_scenarios = [
        ("network_error", ConnectionError("Network connection failed")),
        ("timeout_error", TimeoutError("Request timed out")),
        ("api_error", Exception("API service unavailable")),
        ("validation_error", ValueError("Invalid input data")),
    ]
    
    # Generate errors rapidly to trigger alerts
    for i in range(15):
        scenario_name, exception = random.choice(error_scenarios)
        
        context = ErrorContext(
            operation=f"test_operation_{i}",
            component="demo_component",
            additional_context={"service_name": "demo_service"}
        )
        
        # Handle the error (this will record it for monitoring)
        recovery_result = await error_handler.recovery_manager.handle_error(
            exception, context, fallback_data={"demo": True}
        )
        
        print(f"🔍 Error {i+1}: {scenario_name} -> {recovery_result.strategy_used.value}")
        
        # Small delay
        await asyncio.sleep(0.1)
    
    # Wait for monitoring to process
    await asyncio.sleep(3)
    
    # Show monitoring status
    status = error_monitor.get_monitoring_status()
    print(f"\n📈 Monitoring Status:")
    print(f"   Running: {status['running']}")
    print(f"   Active Alerts: {status['active_alerts']}")
    print(f"   Recent Events: {status['recent_events']}")
    print(f"   Error Rate: {status['metrics']['error_rate']:.2f} errors/min")
    print(f"   Recovery Rate: {status['metrics']['recovery_rate']:.2%}")
    
    # Show active alerts
    active_alerts = error_monitor.alert_manager.get_active_alerts()
    if active_alerts:
        print(f"\n🚨 Active Alerts ({len(active_alerts)}):")
        for alert in active_alerts:
            print(f"   - {alert.rule_name}: {alert.message}")
            print(f"     Level: {alert.level.value}, Value: {alert.metric_value:.2f}")
    else:
        print("\n✅ No active alerts")
    
    # Show service health
    service_health = error_monitor.get_service_health("demo_service")
    print(f"\n🏥 Demo Service Health:")
    print(f"   Error Rate: {service_health['error_rate']:.2f}/min")
    print(f"   Error Count: {service_health['error_count']}")
    print(f"   Recovery Rate: {service_health['recovery_rate']:.2%}")
    print(f"   Availability: {service_health['availability']:.1f}%")
    
    # Stop monitoring
    await error_monitor.stop_monitoring()


async def demo_graceful_degradation():
    """Demonstrate graceful degradation scenarios."""
    print("\n" + "="*60)
    print("DEMO: Graceful Degradation")
    print("="*60)
    
    # Simulate different degradation scenarios
    scenarios = [
        {
            "name": "Pricing Service Degradation",
            "operation": "get_pricing_data",
            "error": ConnectionError("Pricing API unavailable"),
            "fallback": {
                "services": [],
                "message": "Pricing data temporarily unavailable",
                "degraded_mode": True
            }
        },
        {
            "name": "Recommendation Engine Degradation", 
            "operation": "generate_recommendations",
            "error": TimeoutError("Recommendation engine timeout"),
            "fallback": {
                "recommendations": ["Basic recommendation based on cached data"],
                "confidence": 0.3,
                "degraded_mode": True
            }
        },
        {
            "name": "Compliance Check Degradation",
            "operation": "check_compliance",
            "error": Exception("Compliance service unavailable"),
            "fallback": {
                "compliance_status": "unknown",
                "warnings": ["Compliance check unavailable - manual review required"],
                "degraded_mode": True
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔧 Testing: {scenario['name']}")
        
        context = ErrorContext(
            operation=scenario["operation"],
            component="degradation_demo"
        )
        
        recovery_result = await error_handler.recovery_manager.handle_error(
            scenario["error"],
            context,
            fallback_data=scenario["fallback"]
        )
        
        if recovery_result.success:
            print(f"✅ Graceful degradation successful")
            print(f"   Strategy: {recovery_result.strategy_used.value}")
            print(f"   Degraded Mode: {recovery_result.degraded_mode}")
            if recovery_result.warnings:
                print(f"   Warnings: {recovery_result.warnings}")
        else:
            print(f"❌ Degradation failed: {recovery_result.warnings}")


async def demo_comprehensive_logging():
    """Demonstrate comprehensive error logging."""
    print("\n" + "="*60)
    print("DEMO: Comprehensive Error Logging")
    print("="*60)
    
    # Test logging with different contexts
    contexts = [
        {
            "workflow_id": "wf_001",
            "agent_name": "cto_agent",
            "step_id": "step_1",
            "operation": "strategic_analysis"
        },
        {
            "workflow_id": "wf_002", 
            "agent_name": "cloud_engineer_agent",
            "step_id": "step_2",
            "operation": "service_selection"
        }
    ]
    
    for ctx in contexts:
        print(f"\n📝 Testing logging for: {ctx['agent_name']}")
        
        with log_context(**ctx):
            try:
                # Simulate some work that fails
                if random.random() < 0.7:  # 70% chance of failure for demo
                    raise ConnectionError(f"API call failed for {ctx['operation']}")
                
                logger.info(f"Operation {ctx['operation']} completed successfully")
                
            except Exception as e:
                # Handle error with comprehensive logging
                error_context = ErrorContext(
                    operation=ctx["operation"],
                    component="agent",
                    workflow_id=ctx["workflow_id"],
                    agent_name=ctx["agent_name"],
                    step_id=ctx["step_id"]
                )
                
                recovery_result = await error_handler.recovery_manager.handle_error(
                    e, error_context
                )
                
                print(f"   Error handled: {recovery_result.strategy_used.value}")


async def demo_error_statistics():
    """Demonstrate error statistics and reporting."""
    print("\n" + "="*60)
    print("DEMO: Error Statistics and Reporting")
    print("="*60)
    
    # Get comprehensive error statistics
    stats = await error_handler.get_error_statistics()
    
    print("📊 Error Handling Statistics:")
    print(f"   Timestamp: {stats.get('timestamp', 'N/A')}")
    
    if "service_health" in stats:
        print(f"\n🏥 Service Health:")
        for service, health in stats["service_health"].items():
            print(f"   {service}: {health.get('state', 'unknown')}")
    
    if "error_metrics" in stats:
        print(f"\n📈 Error Metrics:")
        metrics = stats["error_metrics"]
        print(f"   Total Errors: {metrics.get('total_errors', 0)}")
        print(f"   Error Rate: {metrics.get('error_rate', 0):.2f}%")
        print(f"   Recovery Rate: {metrics.get('recovery_rate', 0):.2%}")
    
    # Show resilience manager health
    print(f"\n🛡️  Resilience Manager Health:")
    all_health = resilience_manager.get_all_services_health()
    for service, health in all_health.items():
        print(f"   {service}:")
        print(f"     State: {health.get('state', 'unknown')}")
        print(f"     Failures: {health.get('failure_count', 0)}")


async def main():
    """Run all error handling demos."""
    print("🚀 Comprehensive Error Handling System Demo")
    print("=" * 80)
    
    try:
        # Run all demos
        await demo_basic_error_handling()
        await demo_agent_error_handling()
        await demo_resilience_patterns()
        await demo_error_monitoring()
        await demo_graceful_degradation()
        await demo_comprehensive_logging()
        await demo_error_statistics()
        
        print("\n" + "="*80)
        print("✅ All error handling demos completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logger.error("Demo execution failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())