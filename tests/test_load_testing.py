"""
Load testing suite for concurrent user scenarios.

Tests system behavior under realistic load conditions with multiple
concurrent users and sustained traffic patterns.
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging
import json

from api.app import app
from src.infra_mind.core.production_performance_optimizer import performance_optimizer
from src.infra_mind.core.database import db
from src.infra_mind.core.cache import cache_manager
from src.infra_mind.agents.cto_agent import CTOAgent
from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
from src.infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    name: str
    concurrent_users: int
    test_duration_seconds: int
    ramp_up_seconds: int
    requests_per_user: int
    think_time_seconds: float = 1.0
    failure_threshold_percent: float = 5.0
    response_time_threshold_ms: float = 5000.0


@dataclass
class LoadTestResult:
    """Results from a load test scenario."""
    config: LoadTestConfig
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate_percent(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def failure_rate_percent(self) -> float:
        """Calculate failure rate percentage."""
        return 100.0 - self.success_rate_percent
    
    @property
    def duration_seconds(self) -> float:
        """Calculate test duration in seconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


class LoadTestRunner:
    """Load test runner for concurrent user scenarios."""
    
    def __init__(self):
        self.test_results: List[LoadTestResult] = []
        self.is_running = False
        self.base_url = "http://localhost:8000"
        
        # Load test scenarios
        self.test_scenarios = {
            "light_load": LoadTestConfig(
                name="light_load",
                concurrent_users=10,
                test_duration_seconds=60,
                ramp_up_seconds=10,
                requests_per_user=5,
                think_time_seconds=2.0
            ),
            "moderate_load": LoadTestConfig(
                name="moderate_load",
                concurrent_users=50,
                test_duration_seconds=120,
                ramp_up_seconds=20,
                requests_per_user=10,
                think_time_seconds=1.5
            ),
            "heavy_load": LoadTestConfig(
                name="heavy_load",
                concurrent_users=100,
                test_duration_seconds=180,
                ramp_up_seconds=30,
                requests_per_user=15,
                think_time_seconds=1.0
            ),
            "stress_test": LoadTestConfig(
                name="stress_test",
                concurrent_users=200,
                test_duration_seconds=300,
                ramp_up_seconds=60,
                requests_per_user=20,
                think_time_seconds=0.5,
                failure_threshold_percent=15.0,
                response_time_threshold_ms=10000.0
            )
        }
    
    async def run_load_test(self, scenario_name: str) -> LoadTestResult:
        """
        Run a load test scenario.
        
        Args:
            scenario_name: Name of the test scenario to run
            
        Returns:
            LoadTestResult with test metrics
        """
        if scenario_name not in self.test_scenarios:
            raise ValueError(f"Unknown test scenario: {scenario_name}")
        
        config = self.test_scenarios[scenario_name]
        result = LoadTestResult(config=config, total_requests=0, successful_requests=0, failed_requests=0,
                               avg_response_time_ms=0.0, p95_response_time_ms=0.0, p99_response_time_ms=0.0,
                               max_response_time_ms=0.0, requests_per_second=0.0)
        
        logger.info(f"Starting load test: {config.name} with {config.concurrent_users} users")
        
        try:
            self.is_running = True
            
            # Start performance monitoring
            await performance_optimizer.start_optimization("production")
            
            # Create user sessions
            user_tasks = []
            
            # Ramp up users gradually
            users_per_batch = max(1, config.concurrent_users // (config.ramp_up_seconds // 2))
            
            for batch in range(0, config.concurrent_users, users_per_batch):
                batch_size = min(users_per_batch, config.concurrent_users - batch)
                
                for i in range(batch_size):
                    user_id = batch + i
                    task = asyncio.create_task(self._simulate_user_session(user_id, config, result))
                    user_tasks.append(task)
                
                # Wait before starting next batch (ramp up)
                if batch + batch_size < config.concurrent_users:
                    await asyncio.sleep(2)
            
            # Wait for test duration
            await asyncio.sleep(config.test_duration_seconds)
            
            # Stop test
            self.is_running = False
            
            # Wait for all users to complete
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Calculate final metrics
            result.end_time = datetime.utcnow()
            await self._calculate_final_metrics(result)
            
            self.test_results.append(result)
            
            logger.info(f"Load test completed: {result.success_rate_percent:.2f}% success rate, "
                       f"{result.avg_response_time_ms:.2f}ms avg response time")
            
            return result
            
        except Exception as e:
            logger.error(f"Load test failed: {e}")
            result.errors.append(f"Test execution failed: {str(e)}")
            result.end_time = datetime.utcnow()
            return result
        
        finally:
            self.is_running = False
            await performance_optimizer.stop_optimization()
    
    async def _simulate_user_session(self, user_id: int, config: LoadTestConfig, result: LoadTestResult):
        """
        Simulate a single user session.
        
        Args:
            user_id: Unique user identifier
            config: Load test configuration
            result: Result object to update with metrics
        """
        session_requests = 0
        
        async with aiohttp.ClientSession() as session:
            try:
                while self.is_running and session_requests < config.requests_per_user:
                    # Choose random endpoint to test
                    endpoint_result = await self._make_random_request(session, user_id)
                    
                    # Update results
                    result.total_requests += 1
                    session_requests += 1
                    
                    if endpoint_result["success"]:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1
                        result.errors.append(f"User {user_id}: {endpoint_result['error']}")
                    
                    result.response_times.append(endpoint_result["response_time"])
                    
                    # Think time between requests
                    if self.is_running:
                        await asyncio.sleep(config.think_time_seconds + random.uniform(0, 1))
                
            except Exception as e:
                result.errors.append(f"User {user_id} session failed: {str(e)}")
    
    async def _make_random_request(self, session: aiohttp.ClientSession, user_id: int) -> Dict[str, Any]:
        """
        Make a random API request to simulate user behavior.
        
        Args:
            session: HTTP session
            user_id: User identifier
            
        Returns:
            Dictionary with request result
        """
        # Define realistic API endpoints to test
        endpoints = [
            {
                "method": "GET",
                "path": "/api/v1/health",
                "weight": 10  # Higher weight = more likely to be chosen
            },
            {
                "method": "POST",
                "path": "/api/v1/assessments",
                "weight": 5,
                "data": {
                    "user_id": f"load_test_user_{user_id}",
                    "business_requirements": {
                        "industry": random.choice(["technology", "finance", "healthcare"]),
                        "company_size": random.choice(["small", "medium", "large"])
                    }
                }
            },
            {
                "method": "GET",
                "path": f"/api/v1/assessments/user/load_test_user_{user_id}",
                "weight": 8
            },
            {
                "method": "GET",
                "path": "/api/v1/cloud/services",
                "weight": 7,
                "params": {"provider": random.choice(["aws", "azure", "gcp"])}
            },
            {
                "method": "GET",
                "path": "/api/v1/recommendations/templates",
                "weight": 6
            },
            {
                "method": "POST",
                "path": "/api/v1/reports/generate",
                "weight": 3,
                "data": {
                    "assessment_id": f"test_assessment_{user_id}",
                    "report_type": "summary"
                }
            }
        ]
        
        # Choose endpoint based on weights
        total_weight = sum(ep["weight"] for ep in endpoints)
        random_value = random.randint(1, total_weight)
        
        current_weight = 0
        chosen_endpoint = endpoints[0]
        
        for endpoint in endpoints:
            current_weight += endpoint["weight"]
            if random_value <= current_weight:
                chosen_endpoint = endpoint
                break
        
        # Make request
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{chosen_endpoint['path']}"
            
            if chosen_endpoint["method"] == "GET":
                params = chosen_endpoint.get("params", {})
                async with session.get(url, params=params, timeout=30) as response:
                    await response.text()  # Read response body
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        "success": response.status < 400,
                        "response_time": response_time,
                        "status_code": response.status,
                        "error": None if response.status < 400 else f"HTTP {response.status}"
                    }
            
            elif chosen_endpoint["method"] == "POST":
                data = chosen_endpoint.get("data", {})
                async with session.post(url, json=data, timeout=30) as response:
                    await response.text()  # Read response body
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        "success": response.status < 400,
                        "response_time": response_time,
                        "status_code": response.status,
                        "error": None if response.status < 400 else f"HTTP {response.status}"
                    }
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "response_time": response_time,
                "status_code": 0,
                "error": "Request timeout"
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "response_time": response_time,
                "status_code": 0,
                "error": str(e)
            }
    
    async def _calculate_final_metrics(self, result: LoadTestResult):
        """Calculate final test metrics."""
        if result.response_times:
            result.avg_response_time_ms = statistics.mean(result.response_times)
            result.max_response_time_ms = max(result.response_times)
            
            sorted_times = sorted(result.response_times)
            result.p95_response_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
            result.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
        
        if result.duration_seconds > 0:
            result.requests_per_second = result.total_requests / result.duration_seconds
    
    def generate_load_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive load test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "tests_passed": len([r for r in self.test_results if r.failure_rate_percent <= r.config.failure_threshold_percent]),
                "tests_failed": len([r for r in self.test_results if r.failure_rate_percent > r.config.failure_threshold_percent]),
                "overall_status": "PASS" if all(r.failure_rate_percent <= r.config.failure_threshold_percent for r in self.test_results) else "FAIL"
            },
            "test_results": [],
            "performance_analysis": {
                "avg_response_times": [],
                "success_rates": [],
                "throughput": []
            },
            "recommendations": []
        }
        
        for result in self.test_results:
            test_data = {
                "scenario": result.config.name,
                "configuration": {
                    "concurrent_users": result.config.concurrent_users,
                    "test_duration_seconds": result.config.test_duration_seconds,
                    "requests_per_user": result.config.requests_per_user
                },
                "metrics": {
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "success_rate_percent": result.success_rate_percent,
                    "failure_rate_percent": result.failure_rate_percent,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "p95_response_time_ms": result.p95_response_time_ms,
                    "p99_response_time_ms": result.p99_response_time_ms,
                    "max_response_time_ms": result.max_response_time_ms,
                    "requests_per_second": result.requests_per_second
                },
                "status": "PASS" if result.failure_rate_percent <= result.config.failure_threshold_percent else "FAIL",
                "errors": result.errors[:10],  # Limit to first 10 errors
                "duration_seconds": result.duration_seconds
            }
            
            report["test_results"].append(test_data)
            
            # Add to performance analysis
            report["performance_analysis"]["avg_response_times"].append({
                "scenario": result.config.name,
                "value": result.avg_response_time_ms
            })
            report["performance_analysis"]["success_rates"].append({
                "scenario": result.config.name,
                "value": result.success_rate_percent
            })
            report["performance_analysis"]["throughput"].append({
                "scenario": result.config.name,
                "value": result.requests_per_second
            })
        
        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations()
        
        return report
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        if not self.test_results:
            return recommendations
        
        # Analyze response times
        avg_response_times = [r.avg_response_time_ms for r in self.test_results]
        if avg_response_times and max(avg_response_times) > 3000:
            recommendations.append("Consider optimizing slow endpoints - average response times exceed 3 seconds")
        
        # Analyze success rates
        success_rates = [r.success_rate_percent for r in self.test_results]
        if success_rates and min(success_rates) < 95:
            recommendations.append("Improve error handling and system reliability - success rates below 95%")
        
        # Analyze throughput
        throughput_values = [r.requests_per_second for r in self.test_results]
        if throughput_values and max(throughput_values) < 10:
            recommendations.append("Consider scaling infrastructure - low throughput detected")
        
        # Analyze error patterns
        all_errors = []
        for result in self.test_results:
            all_errors.extend(result.errors)
        
        if len(all_errors) > 0:
            timeout_errors = len([e for e in all_errors if "timeout" in e.lower()])
            if timeout_errors > len(all_errors) * 0.3:
                recommendations.append("High number of timeout errors - consider increasing timeout values or optimizing slow operations")
        
        return recommendations


class TestLoadTesting:
    """Load testing test cases."""
    
    @pytest.fixture
    async def load_test_runner(self):
        """Fixture for load test runner."""
        runner = LoadTestRunner()
        yield runner
    
    @pytest.mark.asyncio
    async def test_light_load_scenario(self, load_test_runner):
        """Test system under light load conditions."""
        result = await load_test_runner.run_load_test("light_load")
        
        # Assertions
        assert result.success_rate_percent >= 95, f"Light load success rate too low: {result.success_rate_percent}%"
        assert result.avg_response_time_ms < 2000, f"Light load response time too high: {result.avg_response_time_ms}ms"
        assert result.requests_per_second > 1, f"Light load throughput too low: {result.requests_per_second} RPS"
        
        logger.info(f"Light load test: {result.success_rate_percent:.2f}% success, {result.avg_response_time_ms:.2f}ms avg response")
    
    @pytest.mark.asyncio
    async def test_moderate_load_scenario(self, load_test_runner):
        """Test system under moderate load conditions."""
        result = await load_test_runner.run_load_test("moderate_load")
        
        # Assertions
        assert result.success_rate_percent >= 90, f"Moderate load success rate too low: {result.success_rate_percent}%"
        assert result.avg_response_time_ms < 3000, f"Moderate load response time too high: {result.avg_response_time_ms}ms"
        assert result.p95_response_time_ms < 5000, f"Moderate load P95 response time too high: {result.p95_response_time_ms}ms"
        
        logger.info(f"Moderate load test: {result.success_rate_percent:.2f}% success, {result.avg_response_time_ms:.2f}ms avg response")
    
    @pytest.mark.asyncio
    async def test_heavy_load_scenario(self, load_test_runner):
        """Test system under heavy load conditions."""
        result = await load_test_runner.run_load_test("heavy_load")
        
        # Assertions
        assert result.success_rate_percent >= 85, f"Heavy load success rate too low: {result.success_rate_percent}%"
        assert result.avg_response_time_ms < 5000, f"Heavy load response time too high: {result.avg_response_time_ms}ms"
        assert result.p99_response_time_ms < 10000, f"Heavy load P99 response time too high: {result.p99_response_time_ms}ms"
        
        logger.info(f"Heavy load test: {result.success_rate_percent:.2f}% success, {result.avg_response_time_ms:.2f}ms avg response")
    
    @pytest.mark.asyncio
    async def test_stress_scenario(self, load_test_runner):
        """Test system under stress conditions."""
        result = await load_test_runner.run_load_test("stress_test")
        
        # More lenient assertions for stress test
        assert result.success_rate_percent >= 70, f"Stress test success rate too low: {result.success_rate_percent}%"
        assert result.avg_response_time_ms < 8000, f"Stress test response time too high: {result.avg_response_time_ms}ms"
        
        # Log stress test results for analysis
        logger.info(f"Stress test: {result.success_rate_percent:.2f}% success, {result.avg_response_time_ms:.2f}ms avg response")
        logger.info(f"Stress test errors: {len(result.errors)} total errors")
    
    @pytest.mark.asyncio
    async def test_generate_load_test_report(self, load_test_runner):
        """Test load test report generation."""
        # Run a quick test
        await load_test_runner.run_load_test("light_load")
        
        # Generate report
        report = load_test_runner.generate_load_test_report()
        
        # Assertions
        assert "summary" in report
        assert "test_results" in report
        assert "performance_analysis" in report
        assert "recommendations" in report
        assert report["summary"]["total_tests"] > 0
        
        # Save report
        with open("load_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Load test report generated: load_test_report.json")


class TestAgentLoadTesting:
    """Load testing specifically for agent workflows."""
    
    @pytest.mark.asyncio
    async def test_concurrent_cto_agent_requests(self):
        """Test CTO agent under concurrent load."""
        async def cto_agent_request(user_id: int):
            agent = CTOAgent()
            
            assessment_data = {
                "user_id": f"load_test_cto_{user_id}",
                "business_requirements": {
                    "industry": random.choice(["technology", "finance", "healthcare"]),
                    "company_size": random.choice(["small", "medium", "large"]),
                    "budget_range": "100000-500000"
                }
            }
            
            start_time = time.time()
            try:
                result = await agent.analyze_requirements(assessment_data)
                response_time = (time.time() - start_time) * 1000
                return {"success": True, "response_time": response_time, "user_id": user_id}
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return {"success": False, "response_time": response_time, "user_id": user_id, "error": str(e)}
        
        # Run concurrent requests
        num_concurrent = 10
        tasks = [cto_agent_request(i) for i in range(num_concurrent)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        success_rate = len(successful) / len(tasks) * 100
        
        if successful:
            avg_response_time = statistics.mean([r["response_time"] for r in successful])
        else:
            avg_response_time = 0
        
        # Assertions
        assert success_rate >= 70, f"CTO agent concurrent success rate too low: {success_rate}%"
        assert avg_response_time < 30000, f"CTO agent response time too high: {avg_response_time}ms"
        
        logger.info(f"CTO agent load test: {success_rate}% success, {avg_response_time:.2f}ms avg response")
    
    @pytest.mark.asyncio
    async def test_concurrent_cloud_engineer_requests(self):
        """Test Cloud Engineer agent under concurrent load."""
        async def cloud_engineer_request(user_id: int):
            agent = CloudEngineerAgent()
            
            requirements = {
                "user_id": f"load_test_ce_{user_id}",
                "technical_requirements": {
                    "workload_type": random.choice(["web_application", "data_processing", "machine_learning"]),
                    "expected_users": random.randint(1000, 100000),
                    "preferred_cloud": random.choice(["aws", "azure", "gcp"])
                }
            }
            
            start_time = time.time()
            try:
                result = await agent.analyze_technical_requirements(requirements)
                response_time = (time.time() - start_time) * 1000
                return {"success": True, "response_time": response_time, "user_id": user_id}
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return {"success": False, "response_time": response_time, "user_id": user_id, "error": str(e)}
        
        # Run concurrent requests
        num_concurrent = 8
        tasks = [cloud_engineer_request(i) for i in range(num_concurrent)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        success_rate = len(successful) / len(tasks) * 100
        
        if successful:
            avg_response_time = statistics.mean([r["response_time"] for r in successful])
        else:
            avg_response_time = 0
        
        # Assertions
        assert success_rate >= 60, f"Cloud Engineer agent concurrent success rate too low: {success_rate}%"
        assert avg_response_time < 45000, f"Cloud Engineer agent response time too high: {avg_response_time}ms"
        
        logger.info(f"Cloud Engineer agent load test: {success_rate}% success, {avg_response_time:.2f}ms avg response")


if __name__ == "__main__":
    # Run load tests
    pytest.main([__file__, "-v", "--tb=short"])