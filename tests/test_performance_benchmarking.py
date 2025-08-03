"""
Performance benchmarking and regression testing suite.

Establishes performance baselines and detects performance regressions
across different system components and workflows.
"""

import pytest
import asyncio
import time
import statistics
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import hashlib
import psutil

from src.infra_mind.core.production_performance_optimizer import performance_optimizer
from src.infra_mind.core.database import db
from src.infra_mind.core.cache import cache_manager
from src.infra_mind.cloud.aws import AWSClient
from src.infra_mind.cloud.azure import AzureCloudProvider
from src.infra_mind.cloud.gcp import GCPCloudProvider
from src.infra_mind.llm.openai_provider import OpenAIProvider
from src.infra_mind.agents.cto_agent import CTOAgent
from src.infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition."""
    name: str
    description: str
    test_function: str
    baseline_metrics: Dict[str, float]
    regression_thresholds: Dict[str, float]  # Percentage increase that indicates regression
    iterations: int = 10
    warmup_iterations: int = 3
    timeout_seconds: int = 300


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""
    benchmark_name: str
    timestamp: datetime
    iterations: int
    metrics: Dict[str, List[float]]
    aggregated_metrics: Dict[str, Dict[str, float]]  # min, max, avg, p95, p99
    baseline_comparison: Dict[str, Dict[str, float]]  # comparison to baseline
    regression_detected: bool
    regression_details: List[str]
    system_info: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class PerformanceBenchmarkSuite:
    """Performance benchmarking and regression testing suite."""
    
    def __init__(self):
        self.benchmarks = self._create_benchmarks()
        self.results_history = []
        self.baseline_file = "performance_baselines.json"
        self.results_file = "benchmark_results_history.json"
        
        # Load existing baselines and history
        self._load_baselines()
        self._load_results_history()
    
    def _create_benchmarks(self) -> Dict[str, PerformanceBenchmark]:
        """Create performance benchmarks."""
        return {
            "database_query_performance": PerformanceBenchmark(
                name="database_query_performance",
                description="Database query performance benchmark",
                test_function="benchmark_database_queries",
                baseline_metrics={
                    "simple_query_ms": 50.0,
                    "complex_query_ms": 200.0,
                    "aggregation_query_ms": 300.0,
                    "concurrent_queries_ms": 500.0
                },
                regression_thresholds={
                    "simple_query_ms": 20.0,  # 20% increase
                    "complex_query_ms": 25.0,
                    "aggregation_query_ms": 30.0,
                    "concurrent_queries_ms": 40.0
                },
                iterations=20,
                warmup_iterations=5
            ),
            
            "cache_performance": PerformanceBenchmark(
                name="cache_performance",
                description="Cache operations performance benchmark",
                test_function="benchmark_cache_operations",
                baseline_metrics={
                    "cache_get_ms": 5.0,
                    "cache_set_ms": 10.0,
                    "cache_delete_ms": 8.0,
                    "cache_hit_rate_percent": 85.0
                },
                regression_thresholds={
                    "cache_get_ms": 50.0,
                    "cache_set_ms": 50.0,
                    "cache_delete_ms": 50.0,
                    "cache_hit_rate_percent": -10.0  # Negative means decrease is bad
                },
                iterations=50,
                warmup_iterations=10
            ),
            
            "cloud_api_performance": PerformanceBenchmark(
                name="cloud_api_performance",
                description="Cloud API integration performance benchmark",
                test_function="benchmark_cloud_apis",
                baseline_metrics={
                    "aws_api_ms": 2000.0,
                    "azure_api_ms": 2500.0,
                    "gcp_api_ms": 3000.0,
                    "api_success_rate_percent": 95.0
                },
                regression_thresholds={
                    "aws_api_ms": 30.0,
                    "azure_api_ms": 30.0,
                    "gcp_api_ms": 30.0,
                    "api_success_rate_percent": -5.0
                },
                iterations=10,
                warmup_iterations=2,
                timeout_seconds=600
            ),
            
            "llm_performance": PerformanceBenchmark(
                name="llm_performance",
                description="LLM integration performance benchmark",
                test_function="benchmark_llm_operations",
                baseline_metrics={
                    "simple_prompt_ms": 3000.0,
                    "complex_prompt_ms": 8000.0,
                    "prompt_optimization_ms": 100.0,
                    "token_efficiency_percent": 15.0
                },
                regression_thresholds={
                    "simple_prompt_ms": 25.0,
                    "complex_prompt_ms": 25.0,
                    "prompt_optimization_ms": 50.0,
                    "token_efficiency_percent": -20.0
                },
                iterations=5,
                warmup_iterations=1,
                timeout_seconds=900
            ),
            
            "agent_workflow_performance": PerformanceBenchmark(
                name="agent_workflow_performance",
                description="Agent workflow execution performance benchmark",
                test_function="benchmark_agent_workflows",
                baseline_metrics={
                    "cto_agent_ms": 15000.0,
                    "orchestration_ms": 30000.0,
                    "recommendation_generation_ms": 10000.0,
                    "workflow_success_rate_percent": 90.0
                },
                regression_thresholds={
                    "cto_agent_ms": 20.0,
                    "orchestration_ms": 20.0,
                    "recommendation_generation_ms": 25.0,
                    "workflow_success_rate_percent": -10.0
                },
                iterations=5,
                warmup_iterations=1,
                timeout_seconds=1200
            ),
            
            "system_resource_performance": PerformanceBenchmark(
                name="system_resource_performance",
                description="System resource usage performance benchmark",
                test_function="benchmark_system_resources",
                baseline_metrics={
                    "memory_usage_mb": 512.0,
                    "cpu_usage_percent": 30.0,
                    "disk_io_ms": 50.0,
                    "network_latency_ms": 10.0
                },
                regression_thresholds={
                    "memory_usage_mb": 25.0,
                    "cpu_usage_percent": 30.0,
                    "disk_io_ms": 40.0,
                    "network_latency_ms": 50.0
                },
                iterations=30,
                warmup_iterations=5
            )
        }
    
    def _load_baselines(self):
        """Load performance baselines from file."""
        try:
            if os.path.exists(self.baseline_file):
                with open(self.baseline_file, 'r') as f:
                    baselines = json.load(f)
                
                # Update benchmark baselines
                for benchmark_name, baseline_data in baselines.items():
                    if benchmark_name in self.benchmarks:
                        self.benchmarks[benchmark_name].baseline_metrics.update(
                            baseline_data.get("metrics", {})
                        )
                
                logger.info(f"Loaded performance baselines from {self.baseline_file}")
        except Exception as e:
            logger.warning(f"Failed to load baselines: {e}")
    
    def _load_results_history(self):
        """Load benchmark results history from file."""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r') as f:
                    self.results_history = json.load(f)
                
                logger.info(f"Loaded {len(self.results_history)} historical results")
        except Exception as e:
            logger.warning(f"Failed to load results history: {e}")
    
    def _save_baselines(self):
        """Save current baselines to file."""
        try:
            baselines = {}
            for benchmark_name, benchmark in self.benchmarks.items():
                baselines[benchmark_name] = {
                    "metrics": benchmark.baseline_metrics,
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            with open(self.baseline_file, 'w') as f:
                json.dump(baselines, f, indent=2)
            
            logger.info(f"Saved performance baselines to {self.baseline_file}")
        except Exception as e:
            logger.error(f"Failed to save baselines: {e}")
    
    def _save_results_history(self):
        """Save benchmark results history to file."""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results_history, f, indent=2, default=str)
            
            logger.info(f"Saved benchmark results history to {self.results_file}")
        except Exception as e:
            logger.error(f"Failed to save results history: {e}")
    
    async def run_benchmark(self, benchmark_name: str) -> BenchmarkResult:
        """
        Run a specific performance benchmark.
        
        Args:
            benchmark_name: Name of the benchmark to run
            
        Returns:
            BenchmarkResult with performance metrics
        """
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
        
        benchmark = self.benchmarks[benchmark_name]
        
        logger.info(f"Running benchmark: {benchmark_name}")
        
        # Initialize result
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            timestamp=datetime.utcnow(),
            iterations=benchmark.iterations,
            metrics={},
            aggregated_metrics={},
            baseline_comparison={},
            regression_detected=False,
            regression_details=[],
            system_info=self._get_system_info()
        )
        
        try:
            # Get benchmark function
            benchmark_function = getattr(self, benchmark.test_function)
            
            # Run warmup iterations
            logger.info(f"Running {benchmark.warmup_iterations} warmup iterations")
            for i in range(benchmark.warmup_iterations):
                try:
                    await asyncio.wait_for(
                        benchmark_function(),
                        timeout=benchmark.timeout_seconds
                    )
                except Exception as e:
                    logger.warning(f"Warmup iteration {i+1} failed: {e}")
            
            # Run actual benchmark iterations
            logger.info(f"Running {benchmark.iterations} benchmark iterations")
            iteration_results = []
            
            for i in range(benchmark.iterations):
                try:
                    iteration_start = time.time()
                    iteration_metrics = await asyncio.wait_for(
                        benchmark_function(),
                        timeout=benchmark.timeout_seconds
                    )
                    iteration_time = (time.time() - iteration_start) * 1000
                    
                    # Add iteration time to metrics
                    iteration_metrics["total_iteration_ms"] = iteration_time
                    iteration_results.append(iteration_metrics)
                    
                    logger.debug(f"Iteration {i+1}/{benchmark.iterations} completed in {iteration_time:.2f}ms")
                    
                except asyncio.TimeoutError:
                    result.errors.append(f"Iteration {i+1} timed out after {benchmark.timeout_seconds}s")
                except Exception as e:
                    result.errors.append(f"Iteration {i+1} failed: {str(e)}")
            
            # Aggregate results
            if iteration_results:
                result.metrics = self._aggregate_iteration_results(iteration_results)
                result.aggregated_metrics = self._calculate_aggregated_metrics(result.metrics)
                result.baseline_comparison = self._compare_to_baseline(
                    result.aggregated_metrics, benchmark.baseline_metrics
                )
                result.regression_detected, result.regression_details = self._detect_regressions(
                    result.baseline_comparison, benchmark.regression_thresholds
                )
            
            # Add to results history
            self.results_history.append(result)
            
            logger.info(f"Benchmark completed: {benchmark_name} - Regression: {result.regression_detected}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Benchmark execution failed: {str(e)}")
            logger.error(f"Benchmark {benchmark_name} failed: {e}")
            return result
    
    def _aggregate_iteration_results(self, iteration_results: List[Dict[str, float]]) -> Dict[str, List[float]]:
        """Aggregate results from multiple iterations."""
        aggregated = {}
        
        for iteration in iteration_results:
            for metric_name, value in iteration.items():
                if metric_name not in aggregated:
                    aggregated[metric_name] = []
                aggregated[metric_name].append(value)
        
        return aggregated
    
    def _calculate_aggregated_metrics(self, metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Calculate aggregated statistics for metrics."""
        aggregated = {}
        
        for metric_name, values in metrics.items():
            if values:
                sorted_values = sorted(values)
                aggregated[metric_name] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "p95": sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) >= 20 else max(values),
                    "p99": sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) >= 100 else max(values)
                }
        
        return aggregated
    
    def _compare_to_baseline(
        self, 
        current_metrics: Dict[str, Dict[str, float]], 
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Compare current metrics to baseline."""
        comparison = {}
        
        for metric_name, baseline_value in baseline_metrics.items():
            if metric_name in current_metrics:
                current_avg = current_metrics[metric_name]["avg"]
                
                # Calculate percentage change
                if baseline_value != 0:
                    percent_change = ((current_avg - baseline_value) / baseline_value) * 100
                else:
                    percent_change = 0.0
                
                comparison[metric_name] = {
                    "baseline": baseline_value,
                    "current": current_avg,
                    "absolute_change": current_avg - baseline_value,
                    "percent_change": percent_change,
                    "improved": percent_change < 0 if "percent" not in metric_name else percent_change > 0
                }
        
        return comparison
    
    def _detect_regressions(
        self, 
        baseline_comparison: Dict[str, Dict[str, float]], 
        regression_thresholds: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """Detect performance regressions."""
        regression_detected = False
        regression_details = []
        
        for metric_name, threshold in regression_thresholds.items():
            if metric_name in baseline_comparison:
                percent_change = baseline_comparison[metric_name]["percent_change"]
                
                # Check for regression based on threshold
                if threshold > 0:  # Positive threshold means increase is bad
                    if percent_change > threshold:
                        regression_detected = True
                        regression_details.append(
                            f"{metric_name}: {percent_change:.2f}% increase (threshold: {threshold}%)"
                        )
                else:  # Negative threshold means decrease is bad
                    if percent_change < threshold:
                        regression_detected = True
                        regression_details.append(
                            f"{metric_name}: {percent_change:.2f}% decrease (threshold: {threshold}%)"
                        )
        
        return regression_detected, regression_details
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                "platform": psutil.platform.system(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to get system info: {e}")
            return {}
    
    # Benchmark implementations
    
    async def benchmark_database_queries(self) -> Dict[str, float]:
        """Benchmark database query performance."""
        metrics = {}
        
        if db.database is None:
            return {"error": 1.0}
        
        try:
            # Simple query
            start_time = time.time()
            await db.database.assessments.find_one({"status": "completed"})
            metrics["simple_query_ms"] = (time.time() - start_time) * 1000
            
            # Complex query with aggregation
            start_time = time.time()
            pipeline = [
                {"$match": {"status": "completed"}},
                {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            await db.database.assessments.aggregate(pipeline).to_list(None)
            metrics["aggregation_query_ms"] = (time.time() - start_time) * 1000
            
            # Concurrent queries
            async def concurrent_query():
                return await db.database.assessments.find({"status": "completed"}).limit(10).to_list(None)
            
            start_time = time.time()
            tasks = [concurrent_query() for _ in range(5)]
            await asyncio.gather(*tasks)
            metrics["concurrent_queries_ms"] = (time.time() - start_time) * 1000
            
        except Exception as e:
            logger.error(f"Database benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def benchmark_cache_operations(self) -> Dict[str, float]:
        """Benchmark cache operations performance."""
        metrics = {}
        
        try:
            # Cache set operation
            test_data = {"test": "data", "timestamp": time.time()}
            start_time = time.time()
            await cache_manager.set("aws", "test_service", "us-east-1", test_data, 300)
            metrics["cache_set_ms"] = (time.time() - start_time) * 1000
            
            # Cache get operation
            start_time = time.time()
            result = await cache_manager.get("aws", "test_service", "us-east-1")
            metrics["cache_get_ms"] = (time.time() - start_time) * 1000
            
            # Calculate hit rate
            metrics["cache_hit_rate_percent"] = 100.0 if result else 0.0
            
            # Cache delete operation
            start_time = time.time()
            await cache_manager.delete("aws", "test_service", "us-east-1")
            metrics["cache_delete_ms"] = (time.time() - start_time) * 1000
            
        except Exception as e:
            logger.error(f"Cache benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def benchmark_cloud_apis(self) -> Dict[str, float]:
        """Benchmark cloud API performance."""
        metrics = {}
        successful_calls = 0
        total_calls = 0
        
        try:
            # AWS API
            aws_provider = AWSCloudProvider()
            start_time = time.time()
            try:
                await aws_provider.get_pricing_data("ec2", "us-east-1")
                metrics["aws_api_ms"] = (time.time() - start_time) * 1000
                successful_calls += 1
            except Exception as e:
                metrics["aws_api_ms"] = 10000.0  # Penalty for failure
                logger.warning(f"AWS API benchmark failed: {e}")
            total_calls += 1
            
            # Azure API
            azure_provider = AzureCloudProvider()
            start_time = time.time()
            try:
                await azure_provider.get_pricing_data("compute", "eastus")
                metrics["azure_api_ms"] = (time.time() - start_time) * 1000
                successful_calls += 1
            except Exception as e:
                metrics["azure_api_ms"] = 10000.0  # Penalty for failure
                logger.warning(f"Azure API benchmark failed: {e}")
            total_calls += 1
            
            # GCP API
            gcp_provider = GCPCloudProvider()
            start_time = time.time()
            try:
                await gcp_provider.get_pricing_data("compute", "us-central1")
                metrics["gcp_api_ms"] = (time.time() - start_time) * 1000
                successful_calls += 1
            except Exception as e:
                metrics["gcp_api_ms"] = 10000.0  # Penalty for failure
                logger.warning(f"GCP API benchmark failed: {e}")
            total_calls += 1
            
            # Calculate success rate
            metrics["api_success_rate_percent"] = (successful_calls / total_calls) * 100 if total_calls > 0 else 0
            
        except Exception as e:
            logger.error(f"Cloud API benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def benchmark_llm_operations(self) -> Dict[str, float]:
        """Benchmark LLM operations performance."""
        metrics = {}
        
        try:
            llm_provider = OpenAIProvider()
            
            # Simple prompt
            simple_prompt = "What is cloud computing?"
            start_time = time.time()
            try:
                response = await llm_provider.generate_response(simple_prompt, {})
                metrics["simple_prompt_ms"] = (time.time() - start_time) * 1000
                
                # Calculate token efficiency (mock calculation)
                original_tokens = len(simple_prompt.split()) * 1.3  # Rough estimate
                if hasattr(response, 'token_usage') and response.token_usage:
                    actual_tokens = response.token_usage.total_tokens
                    metrics["token_efficiency_percent"] = max(0, (original_tokens - actual_tokens) / original_tokens * 100)
                else:
                    metrics["token_efficiency_percent"] = 0.0
                    
            except Exception as e:
                metrics["simple_prompt_ms"] = 30000.0  # Penalty for failure
                metrics["token_efficiency_percent"] = 0.0
                logger.warning(f"Simple prompt benchmark failed: {e}")
            
            # Complex prompt
            complex_prompt = """
            Design a comprehensive multi-cloud infrastructure strategy for a financial services company 
            with strict compliance requirements including GDPR, SOX, and PCI DSS. The solution should 
            include high availability, disaster recovery, and cost optimization across AWS, Azure, and GCP.
            """
            start_time = time.time()
            try:
                await llm_provider.generate_response(complex_prompt, {})
                metrics["complex_prompt_ms"] = (time.time() - start_time) * 1000
            except Exception as e:
                metrics["complex_prompt_ms"] = 60000.0  # Penalty for failure
                logger.warning(f"Complex prompt benchmark failed: {e}")
            
            # Prompt optimization (mock)
            start_time = time.time()
            # Simulate prompt optimization processing
            await asyncio.sleep(0.05)  # 50ms simulation
            metrics["prompt_optimization_ms"] = (time.time() - start_time) * 1000
            
        except Exception as e:
            logger.error(f"LLM benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def benchmark_agent_workflows(self) -> Dict[str, float]:
        """Benchmark agent workflow performance."""
        metrics = {}
        successful_workflows = 0
        total_workflows = 0
        
        try:
            # CTO Agent benchmark
            cto_agent = CTOAgent()
            assessment_data = {
                "user_id": "benchmark_user",
                "business_requirements": {
                    "industry": "technology",
                    "company_size": "medium",
                    "budget_range": "100000-500000"
                }
            }
            
            start_time = time.time()
            try:
                await cto_agent.analyze_requirements(assessment_data)
                metrics["cto_agent_ms"] = (time.time() - start_time) * 1000
                successful_workflows += 1
            except Exception as e:
                metrics["cto_agent_ms"] = 60000.0  # Penalty for failure
                logger.warning(f"CTO agent benchmark failed: {e}")
            total_workflows += 1
            
            # Orchestration benchmark
            orchestrator = LangGraphOrchestrator()
            workflow_data = {
                "assessment_id": "benchmark_assessment",
                "business_requirements": assessment_data["business_requirements"]
            }
            
            start_time = time.time()
            try:
                await orchestrator.run_assessment_workflow(workflow_data)
                metrics["orchestration_ms"] = (time.time() - start_time) * 1000
                successful_workflows += 1
            except Exception as e:
                metrics["orchestration_ms"] = 120000.0  # Penalty for failure
                logger.warning(f"Orchestration benchmark failed: {e}")
            total_workflows += 1
            
            # Mock recommendation generation
            start_time = time.time()
            await asyncio.sleep(5)  # Simulate recommendation generation
            metrics["recommendation_generation_ms"] = (time.time() - start_time) * 1000
            successful_workflows += 1
            total_workflows += 1
            
            # Calculate success rate
            metrics["workflow_success_rate_percent"] = (successful_workflows / total_workflows) * 100 if total_workflows > 0 else 0
            
        except Exception as e:
            logger.error(f"Agent workflow benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def benchmark_system_resources(self) -> Dict[str, float]:
        """Benchmark system resource usage."""
        metrics = {}
        
        try:
            # Memory usage
            process = psutil.Process()
            metrics["memory_usage_mb"] = process.memory_info().rss / (1024 * 1024)
            
            # CPU usage
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1)
            
            # Disk I/O (mock)
            start_time = time.time()
            # Simulate disk operation
            await asyncio.sleep(0.01)
            metrics["disk_io_ms"] = (time.time() - start_time) * 1000
            
            # Network latency (mock)
            start_time = time.time()
            # Simulate network operation
            await asyncio.sleep(0.005)
            metrics["network_latency_ms"] = (time.time() - start_time) * 1000
            
        except Exception as e:
            logger.error(f"System resource benchmark failed: {e}")
            metrics["error"] = 1.0
        
        return metrics
    
    async def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Run all performance benchmarks."""
        results = {}
        
        for benchmark_name in self.benchmarks.keys():
            try:
                result = await self.run_benchmark(benchmark_name)
                results[benchmark_name] = result
            except Exception as e:
                logger.error(f"Failed to run benchmark {benchmark_name}: {e}")
        
        # Save results
        self._save_results_history()
        
        return results
    
    def update_baselines(self, benchmark_results: Dict[str, BenchmarkResult]):
        """Update performance baselines based on current results."""
        for benchmark_name, result in benchmark_results.items():
            if benchmark_name in self.benchmarks and result.aggregated_metrics:
                # Update baselines with current average values
                for metric_name, stats in result.aggregated_metrics.items():
                    if metric_name in self.benchmarks[benchmark_name].baseline_metrics:
                        self.benchmarks[benchmark_name].baseline_metrics[metric_name] = stats["avg"]
        
        self._save_baselines()
        logger.info("Performance baselines updated")
    
    def generate_benchmark_report(self, results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        report = {
            "summary": {
                "total_benchmarks": len(results),
                "successful_benchmarks": len([r for r in results.values() if not r.errors]),
                "failed_benchmarks": len([r for r in results.values() if r.errors]),
                "regressions_detected": len([r for r in results.values() if r.regression_detected]),
                "overall_status": "PASS" if not any(r.regression_detected for r in results.values()) else "REGRESSION_DETECTED"
            },
            "benchmark_results": {},
            "regression_analysis": {
                "regressions": [],
                "improvements": [],
                "stable_metrics": []
            },
            "performance_trends": self._analyze_performance_trends(),
            "recommendations": []
        }
        
        # Process individual benchmark results
        for benchmark_name, result in results.items():
            report["benchmark_results"][benchmark_name] = {
                "status": "PASS" if not result.regression_detected else "REGRESSION",
                "duration_seconds": sum(result.metrics.get("total_iteration_ms", [0])) / 1000,
                "iterations": result.iterations,
                "error_count": len(result.errors),
                "regression_detected": result.regression_detected,
                "regression_details": result.regression_details,
                "key_metrics": {
                    metric_name: stats["avg"]
                    for metric_name, stats in result.aggregated_metrics.items()
                    if metric_name in self.benchmarks[benchmark_name].baseline_metrics
                }
            }
            
            # Analyze regressions and improvements
            for metric_name, comparison in result.baseline_comparison.items():
                if comparison["percent_change"] > 10:  # Significant change
                    if comparison["improved"]:
                        report["regression_analysis"]["improvements"].append({
                            "benchmark": benchmark_name,
                            "metric": metric_name,
                            "improvement_percent": abs(comparison["percent_change"])
                        })
                    else:
                        report["regression_analysis"]["regressions"].append({
                            "benchmark": benchmark_name,
                            "metric": metric_name,
                            "regression_percent": comparison["percent_change"]
                        })
                else:
                    report["regression_analysis"]["stable_metrics"].append({
                        "benchmark": benchmark_name,
                        "metric": metric_name,
                        "change_percent": comparison["percent_change"]
                    })
        
        # Generate recommendations
        if report["summary"]["regressions_detected"] > 0:
            report["recommendations"].append("Performance regressions detected - investigate and optimize affected components")
        
        if report["summary"]["failed_benchmarks"] > 0:
            report["recommendations"].append("Some benchmarks failed - check system health and external service availability")
        
        if len(report["regression_analysis"]["improvements"]) > 0:
            report["recommendations"].append("Performance improvements detected - consider updating baselines")
        
        return report
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends from historical data."""
        trends = {
            "trend_analysis": "Historical trend analysis would be implemented here",
            "data_points": len(self.results_history),
            "time_range": "Analysis of performance over time"
        }
        
        # This would implement actual trend analysis using historical data
        # For now, return placeholder
        
        return trends


@pytest.fixture
async def benchmark_suite():
    """Fixture for performance benchmark suite."""
    suite = PerformanceBenchmarkSuite()
    yield suite


class TestPerformanceBenchmarking:
    """Performance benchmarking test cases."""
    
    @pytest.mark.asyncio
    async def test_database_performance_benchmark(self, benchmark_suite):
        """Test database performance benchmark."""
        result = await benchmark_suite.run_benchmark("database_query_performance")
        
        # Assertions
        assert not result.errors, f"Database benchmark failed: {result.errors}"
        assert "simple_query_ms" in result.aggregated_metrics
        assert result.aggregated_metrics["simple_query_ms"]["avg"] < 1000  # 1 second max
        
        logger.info(f"Database benchmark: {result.aggregated_metrics}")
    
    @pytest.mark.asyncio
    async def test_cache_performance_benchmark(self, benchmark_suite):
        """Test cache performance benchmark."""
        result = await benchmark_suite.run_benchmark("cache_performance")
        
        # Assertions
        assert not result.errors, f"Cache benchmark failed: {result.errors}"
        assert "cache_get_ms" in result.aggregated_metrics
        assert result.aggregated_metrics["cache_get_ms"]["avg"] < 100  # 100ms max
        
        logger.info(f"Cache benchmark: {result.aggregated_metrics}")
    
    @pytest.mark.asyncio
    async def test_system_resource_benchmark(self, benchmark_suite):
        """Test system resource benchmark."""
        result = await benchmark_suite.run_benchmark("system_resource_performance")
        
        # Assertions
        assert not result.errors, f"System resource benchmark failed: {result.errors}"
        assert "memory_usage_mb" in result.aggregated_metrics
        assert result.aggregated_metrics["memory_usage_mb"]["avg"] < 2048  # 2GB max
        
        logger.info(f"System resource benchmark: {result.aggregated_metrics}")
    
    @pytest.mark.asyncio
    async def test_run_all_benchmarks(self, benchmark_suite):
        """Test running all benchmarks."""
        results = await benchmark_suite.run_all_benchmarks()
        
        # Assertions
        assert len(results) > 0, "No benchmark results"
        
        # Generate report
        report = benchmark_suite.generate_benchmark_report(results)
        
        # Save report
        with open("performance_benchmark_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Performance benchmark report generated: performance_benchmark_report.json")
        
        # Assert no critical regressions
        critical_regressions = [
            r for r in report["regression_analysis"]["regressions"]
            if r["regression_percent"] > 50  # 50% regression is critical
        ]
        assert len(critical_regressions) == 0, f"Critical performance regressions detected: {critical_regressions}"
    
    @pytest.mark.asyncio
    async def test_baseline_update(self, benchmark_suite):
        """Test baseline update functionality."""
        # Run a benchmark
        results = {"system_resource_performance": await benchmark_suite.run_benchmark("system_resource_performance")}
        
        # Update baselines
        benchmark_suite.update_baselines(results)
        
        # Verify baselines were updated
        assert os.path.exists(benchmark_suite.baseline_file)
        
        logger.info("Baseline update test completed")


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "--tb=short"])