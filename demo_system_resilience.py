#!/usr/bin/env python3
"""
Demo script for system resilience features.

Demonstrates health checks, failover mechanisms, circuit breakers,
and system recovery capabilities in action.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import json
import random

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.health_checks import (
    HealthCheckManager, DatabaseHealthCheck, CacheHealthCheck,
    ExternalAPIHealthCheck, HealthCheckConfig, ComponentType
)
from infra_mind.core.failover import (
    FailoverOrchestrator, ServiceEndpoint, FailoverConfig,
    FailoverStrategy
)
from infra_mind.core.resilience import (
    ResilienceManager, SystemRecoveryManager, CircuitBreakerConfig,
    RetryConfig, FallbackConfig, initialize_system_resilience
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockService:
    """Mock service for demonstration purposes."""
    
    def __init__(self, name: str, failure_rate: float = 0.3, response_time_range: tuple = (50, 200)):
        """
        Initialize mock service.
        
        Args:
            name: Service name
            failure_rate: Probability of failure (0.0 to 1.0)
            response_time_range: Range of response times in milliseconds
        """
        self.name = name
        self.failure_rate = failure_rate
        self.response_time_range = response_time_range
        self.call_count = 0
        self.is_healthy = True
    
    async def call(self, operation: str = "default") -> dict:
        """Simulate service call."""
        self.call_count += 1
        
        # Simulate response time
        response_time = random.uniform(*self.response_time_range)
        await asyncio.sleep(response_time / 1000)  # Convert to seconds
        
        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception(f"{self.name} service temporarily unavailable")
        
        return {
            "service": self.name,
            "operation": operation,
            "call_count": self.call_count,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> dict:
        """Simulate health check."""
        # Randomly toggle health status
        if random.random() < 0.1:  # 10% chance to change health
            self.is_healthy = not self.is_healthy
        
        if not self.is_healthy:
            raise Exception(f"{self.name} health check failed")
        
        return {
            "status": "healthy",
            "call_count": self.call_count,
            "uptime": "99.9%"
        }


async def demo_health_checks():
    """Demonstrate health check system."""
    print("\n" + "="*60)
    print("HEALTH CHECK SYSTEM DEMO")
    print("="*60)
    
    # Create health check manager
    health_manager = HealthCheckManager()
    
    # Create mock services
    database_service = MockService("database", failure_rate=0.1)
    cache_service = MockService("cache", failure_rate=0.2)
    api_service = MockService("external_api", failure_rate=0.3)
    
    # Create health checks (using mock implementations)
    class MockDatabaseHealthCheck:
        def __init__(self, name, service):
            self.name = name
            self.service = service
            self.component_type = ComponentType.DATABASE
            self.config = HealthCheckConfig()
            self.consecutive_failures = 0
            self.consecutive_successes = 0
            self.last_check_time = None
            self.last_status = None
            self.is_recovering = False
        
        async def check_health(self):
            from infra_mind.core.health_checks import HealthCheckResult, HealthStatus
            try:
                await self.service.health_check()
                status = HealthStatus.HEALTHY
                error_msg = None
                self.consecutive_failures = 0
                self.consecutive_successes += 1
            except Exception as e:
                status = HealthStatus.UNHEALTHY
                error_msg = str(e)
                self.consecutive_successes = 0
                self.consecutive_failures += 1
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=random.uniform(10, 100),
                timestamp=datetime.utcnow(),
                error_message=error_msg
            )
    
    # Register health checks
    db_check = MockDatabaseHealthCheck("database", database_service)
    cache_check = MockDatabaseHealthCheck("cache", cache_service)
    api_check = MockDatabaseHealthCheck("external_api", api_service)
    
    health_manager.register_health_check(db_check)
    health_manager.register_health_check(cache_check)
    health_manager.register_health_check(api_check)
    
    print("Registered health checks for:")
    print("- Database service")
    print("- Cache service")
    print("- External API service")
    
    # Perform health checks
    print("\nPerforming health checks...")
    results = await health_manager.check_all_components()
    
    for name, result in results.items():
        status_color = "🟢" if result.status == "healthy" else "🔴" if result.status == "unhealthy" else "🟡"
        print(f"{status_color} {name}: {result.status} ({result.response_time_ms:.1f}ms)")
        if result.error_message:
            print(f"   Error: {result.error_message}")
    
    # Get system health summary
    print("\nSystem Health Summary:")
    summary = health_manager.get_system_health_summary()
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Total Components: {summary['total_components']}")
    print(f"Healthy: {summary['healthy_components']}")
    print(f"Degraded: {summary['degraded_components']}")
    print(f"Unhealthy: {summary['unhealthy_components']}")
    
    return health_manager


async def demo_failover_system():
    """Demonstrate failover system."""
    print("\n" + "="*60)
    print("FAILOVER SYSTEM DEMO")
    print("="*60)
    
    # Create failover orchestrator
    orchestrator = FailoverOrchestrator()
    
    # Register database service with active-passive failover
    db_manager = orchestrator.register_service(
        "database",
        FailoverStrategy.ACTIVE_PASSIVE,
        FailoverConfig(health_check_failures=2, cooldown_period_seconds=5)
    )
    
    # Add database endpoints
    db_endpoints = [
        ServiceEndpoint("db-primary", "mongodb://primary:27017", priority=1, weight=100),
        ServiceEndpoint("db-secondary", "mongodb://secondary:27017", priority=2, weight=50),
        ServiceEndpoint("db-tertiary", "mongodb://tertiary:27017", priority=3, weight=25)
    ]
    
    for endpoint in db_endpoints:
        db_manager.add_endpoint(endpoint)
    
    print("Registered database service with endpoints:")
    for endpoint in db_endpoints:
        print(f"- {endpoint.name} (priority: {endpoint.priority}, weight: {endpoint.weight})")
    
    # Register API service with round-robin failover
    api_manager = orchestrator.register_service(
        "external_api",
        FailoverStrategy.ROUND_ROBIN,
        FailoverConfig(health_check_failures=3, cooldown_period_seconds=10)
    )
    
    # Add API endpoints
    api_endpoints = [
        ServiceEndpoint("api-us-east", "https://api-us-east.example.com", weight=100),
        ServiceEndpoint("api-us-west", "https://api-us-west.example.com", weight=100),
        ServiceEndpoint("api-eu", "https://api-eu.example.com", weight=80)
    ]
    
    for endpoint in api_endpoints:
        api_manager.add_endpoint(endpoint)
    
    print("\nRegistered API service with endpoints:")
    for endpoint in api_endpoints:
        print(f"- {endpoint.name} (weight: {endpoint.weight})")
    
    # Demonstrate endpoint selection
    print("\nDemonstrating endpoint selection:")
    
    # Active-passive selection
    current_db = await db_manager.get_current_endpoint()
    print(f"Database current endpoint: {current_db.name}")
    
    # Round-robin selection
    print("API round-robin selection:")
    for i in range(5):
        current_api = await api_manager.select_endpoint()
        print(f"  Request {i+1}: {current_api.name}")
    
    # Simulate failover
    print("\nSimulating database primary failure...")
    db_endpoints[0].is_healthy = False
    db_endpoints[0].consecutive_failures = 3
    
    # Trigger failover
    await db_manager._trigger_failover(
        "HEALTH_CHECK_FAILURE",
        "Primary database health check failed"
    )
    
    new_db = await db_manager.get_current_endpoint()
    print(f"Failed over to: {new_db.name}")
    
    # Get system status
    print("\nFailover System Status:")
    status = orchestrator.get_system_status()
    print(f"Total Services: {status['total_services']}")
    print(f"Healthy Services: {status['healthy_services']}")
    print(f"Degraded Services: {status['degraded_services']}")
    
    return orchestrator


async def demo_circuit_breakers():
    """Demonstrate circuit breaker functionality."""
    print("\n" + "="*60)
    print("CIRCUIT BREAKER DEMO")
    print("="*60)
    
    # Create resilience manager
    resilience_manager = ResilienceManager()
    
    # Register services with circuit breakers
    resilience_manager.register_service(
        "flaky_service",
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5),
        RetryConfig(max_attempts=2, base_delay=0.1)
    )
    
    print("Registered flaky_service with circuit breaker:")
    print("- Failure threshold: 3")
    print("- Recovery timeout: 5 seconds")
    print("- Max retries: 2")
    
    # Create a flaky service
    flaky_service = MockService("flaky_service", failure_rate=0.8)  # High failure rate
    
    # Demonstrate circuit breaker states
    print("\nDemonstrating circuit breaker states...")
    
    # Closed state - normal operation
    print("\n1. CLOSED state (normal operation):")
    for i in range(2):
        try:
            async with resilience_manager.resilient_call("flaky_service") as execute:
                result = await execute(flaky_service.call)
                if result["data"]:
                    print(f"   Call {i+1}: SUCCESS")
                else:
                    print(f"   Call {i+1}: FAILED - {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   Call {i+1}: FAILED - {str(e)}")
    
    # Trigger failures to open circuit
    print("\n2. Triggering failures to OPEN circuit:")
    for i in range(5):
        try:
            async with resilience_manager.resilient_call("flaky_service") as execute:
                result = await execute(flaky_service.call)
                if result["data"]:
                    print(f"   Call {i+1}: SUCCESS")
                else:
                    print(f"   Call {i+1}: FAILED - Circuit may be opening")
        except Exception as e:
            print(f"   Call {i+1}: FAILED - {str(e)}")
    
    # Check circuit breaker status
    cb_status = resilience_manager.get_service_health("flaky_service")
    print(f"\nCircuit breaker state: {cb_status.get('state', 'unknown')}")
    print(f"Failure count: {cb_status.get('failure_count', 0)}")
    
    # Open state - requests blocked
    print("\n3. OPEN state (requests blocked):")
    try:
        async with resilience_manager.resilient_call("flaky_service") as execute:
            result = await execute(flaky_service.call)
            print("   Unexpected success - circuit should be open")
    except Exception as e:
        print(f"   Request blocked: {str(e)}")
    
    # Wait for recovery timeout
    print("\n4. Waiting for recovery timeout...")
    await asyncio.sleep(6)  # Wait longer than recovery timeout
    
    # Half-open state - testing recovery
    print("\n5. HALF-OPEN state (testing recovery):")
    # Reduce failure rate for recovery
    flaky_service.failure_rate = 0.1
    
    for i in range(3):
        try:
            async with resilience_manager.resilient_call("flaky_service") as execute:
                result = await execute(flaky_service.call)
                if result["data"]:
                    print(f"   Recovery test {i+1}: SUCCESS")
                else:
                    print(f"   Recovery test {i+1}: FAILED")
        except Exception as e:
            print(f"   Recovery test {i+1}: FAILED - {str(e)}")
    
    # Final status
    final_status = resilience_manager.get_service_health("flaky_service")
    print(f"\nFinal circuit breaker state: {final_status.get('state', 'unknown')}")
    
    return resilience_manager


async def demo_system_recovery():
    """Demonstrate system recovery capabilities."""
    print("\n" + "="*60)
    print("SYSTEM RECOVERY DEMO")
    print("="*60)
    
    # Create recovery manager
    recovery_manager = SystemRecoveryManager()
    
    # Register custom recovery strategies
    async def database_recovery(error_context):
        print("   Executing database recovery strategy...")
        await asyncio.sleep(1)  # Simulate recovery time
        return {
            "success": True,
            "action": "Database connections reset and indexes rebuilt"
        }
    
    async def cache_recovery(error_context):
        print("   Executing cache recovery strategy...")
        await asyncio.sleep(0.5)  # Simulate recovery time
        return {
            "success": True,
            "action": "Cache cleared and connections reset"
        }
    
    async def failing_recovery(error_context):
        print("   Attempting recovery that will fail...")
        await asyncio.sleep(0.3)
        raise Exception("Recovery strategy failed")
    
    # Register strategies
    recovery_manager.register_recovery_strategy("database", database_recovery)
    recovery_manager.register_recovery_strategy("cache", cache_recovery)
    recovery_manager.register_recovery_strategy("problematic_service", failing_recovery)
    
    print("Registered custom recovery strategies for:")
    print("- Database service")
    print("- Cache service")
    print("- Problematic service (will fail)")
    
    # Demonstrate successful recovery
    print("\n1. Successful database recovery:")
    error_context = {
        "error": "Database connection timeout",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "database"
    }
    
    result = await recovery_manager.attempt_recovery("database", error_context)
    print(f"   Recovery success: {result['success']}")
    print(f"   Recovery time: {result['recovery_time_seconds']:.2f}s")
    print(f"   Actions taken: {result['actions_taken']}")
    
    # Demonstrate successful cache recovery
    print("\n2. Successful cache recovery:")
    error_context = {
        "error": "Cache memory exhausted",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "cache"
    }
    
    result = await recovery_manager.attempt_recovery("cache", error_context)
    print(f"   Recovery success: {result['success']}")
    print(f"   Recovery time: {result['recovery_time_seconds']:.2f}s")
    print(f"   Actions taken: {result['actions_taken']}")
    
    # Demonstrate failed recovery
    print("\n3. Failed recovery attempt:")
    error_context = {
        "error": "Service completely broken",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "problematic_service"
    }
    
    result = await recovery_manager.attempt_recovery("problematic_service", error_context)
    print(f"   Recovery success: {result['success']}")
    print(f"   Recovery time: {result['recovery_time_seconds']:.2f}s")
    print(f"   Actions taken: {result['actions_taken']}")
    
    # Demonstrate default recovery for unknown service
    print("\n4. Default recovery for unknown service:")
    error_context = {
        "error": "Unknown service failure",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "unknown_service"
    }
    
    result = await recovery_manager.attempt_recovery("unknown_service", error_context)
    print(f"   Recovery success: {result['success']}")
    print(f"   Recovery time: {result['recovery_time_seconds']:.2f}s")
    print(f"   Actions taken: {result['actions_taken']}")
    
    # Show recovery statistics
    print("\nRecovery Statistics:")
    stats = recovery_manager.get_recovery_stats()
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful attempts: {stats['successful_attempts']}")
    print(f"Failed attempts: {stats['failed_attempts']}")
    print(f"Success rate: {stats['success_rate_percent']:.1f}%")
    print(f"Average recovery time: {stats['avg_recovery_time_seconds']:.2f}s")
    print(f"Components recovered: {stats['components_recovered']}")
    
    return recovery_manager


async def demo_integrated_resilience():
    """Demonstrate integrated resilience system."""
    print("\n" + "="*60)
    print("INTEGRATED RESILIENCE DEMO")
    print("="*60)
    
    # Create a service that demonstrates all resilience patterns
    class IntegratedService:
        def __init__(self):
            self.call_count = 0
            self.failure_modes = ["timeout", "error", "success"]
            self.current_mode_index = 0
        
        async def call(self, operation="test"):
            self.call_count += 1
            mode = self.failure_modes[self.current_mode_index % len(self.failure_modes)]
            self.current_mode_index += 1
            
            print(f"   Service call #{self.call_count} - Mode: {mode}")
            
            if mode == "timeout":
                await asyncio.sleep(2)  # Simulate timeout
                raise Exception("Service timeout")
            elif mode == "error":
                raise Exception("Service error")
            else:
                return {
                    "operation": operation,
                    "call_count": self.call_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    # Create resilience manager with all patterns
    resilience_manager = ResilienceManager()
    resilience_manager.register_service(
        "integrated_service",
        CircuitBreakerConfig(failure_threshold=2, recovery_timeout=3),
        RetryConfig(max_attempts=3, base_delay=0.2)
    )
    
    service = IntegratedService()
    
    print("Created integrated service with:")
    print("- Circuit breaker (threshold: 2, recovery: 3s)")
    print("- Retry mechanism (max: 3 attempts)")
    print("- Fallback data support")
    
    # Demonstrate resilience patterns working together
    print("\nDemonstrating integrated resilience patterns:")
    
    fallback_data = {"fallback": True, "message": "Using cached data"}
    
    for i in range(8):
        print(f"\nRequest {i+1}:")
        try:
            async with resilience_manager.resilient_call(
                "integrated_service",
                fallback_key=f"request_{i}",
                default_data=fallback_data
            ) as execute:
                result = await execute(service.call, f"operation_{i}")
                
                if result["data"]:
                    print(f"   ✅ SUCCESS: {result['data']}")
                elif result["fallback_used"]:
                    print(f"   🔄 FALLBACK: {result['data']}")
                else:
                    print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                
                if result["warnings"]:
                    for warning in result["warnings"]:
                        print(f"   ⚠️  Warning: {warning}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {str(e)}")
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Show final circuit breaker status
    print("\nFinal Circuit Breaker Status:")
    cb_status = resilience_manager.get_service_health("integrated_service")
    print(f"State: {cb_status.get('state', 'unknown')}")
    print(f"Failure count: {cb_status.get('failure_count', 0)}")
    print(f"Success count: {cb_status.get('success_count', 0)}")
    
    return resilience_manager


async def main():
    """Run all resilience demos."""
    print("🚀 INFRA MIND SYSTEM RESILIENCE DEMO")
    print("Demonstrating health checks, failover, circuit breakers, and recovery")
    print("=" * 80)
    
    try:
        # Run individual demos
        health_manager = await demo_health_checks()
        await asyncio.sleep(1)
        
        failover_orchestrator = await demo_failover_system()
        await asyncio.sleep(1)
        
        circuit_breaker_manager = await demo_circuit_breakers()
        await asyncio.sleep(1)
        
        recovery_manager = await demo_system_recovery()
        await asyncio.sleep(1)
        
        integrated_manager = await demo_integrated_resilience()
        
        # Final summary
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        print("✅ Health Check System: Monitors component health and provides status")
        print("✅ Failover System: Automatically switches to backup endpoints")
        print("✅ Circuit Breakers: Prevents cascading failures with smart blocking")
        print("✅ System Recovery: Automatically attempts to recover failed components")
        print("✅ Integrated Resilience: All patterns working together seamlessly")
        
        print("\n🎯 Key Benefits:")
        print("- Improved system reliability and availability")
        print("- Automatic failure detection and recovery")
        print("- Graceful degradation under load")
        print("- Comprehensive monitoring and alerting")
        print("- Self-healing capabilities")
        
        print("\n📊 System Status:")
        print(f"Health checks performed: {len(health_manager.health_checks)}")
        print(f"Failover services configured: {len(failover_orchestrator.failover_managers)}")
        print(f"Circuit breakers active: {len(circuit_breaker_manager.circuit_breakers)}")
        print(f"Recovery attempts: {len(recovery_manager.recovery_history)}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    
    print("\n🏁 Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())