"""
Comprehensive performance integration tests for real external services.

Tests system performance with actual cloud APIs, databases, and LLM services
under realistic load conditions.
"""

import pytest
import asyncio
import time
import statistics
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock
import aiohttp
import psutil
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.infra_mind.core.production_performance_optimizer import performance_optimizer
    from src.infra_mind.core.database import db, init_database, close_database
    from src.infra_mind.core.cache import cache_manager
    from src.infra_mind.core.metrics_collector import get_metrics_collector
    from src.infra_mind.cloud.aws import AWSCloudProvider
    from src.infra_mind.cloud.azure import AzureCloudProvider
    from src.infra_mind.cloud.gcp import GCPCloudProvider
    from src.infra_mind.llm.openai_provider import OpenAIProvider
    from src.infra_mind.agents.cto_agent import CTOAgent
    from src.infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator
    PERFORMANCE_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Some performance modules may not be available for testing")
    PERFORMANCE_IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = []
        self.error_log = []
        self.start_time = None
        self.end_time = None
    
    async def setup_test_environment(self):
        """Set up test environment with real services."""
        try:
            # Initialize database
            await init_database()
            
            # Initialize cache
            await cache_manager.connect()
            
            # Start performance optimizer
            await performance_optimizer.start_optimization("staging")
            
            # Initialize metrics collector
            metrics_collector = get_metrics_collector()
            await metrics_collector.start_collection()
            
            logger.info("Test environment setup completed")
            
        except Exception as e:
            logger.error(f"Test environment setup failed: {e}")
            raise
    
    async def teardown_test_environment(self):
        """Clean up test environment."""
        try:
            # Stop performance optimizer
            await performance_optimizer.stop_optimization()
            
            # Close database
            await close_database()
            
            # Disconnect cache
            await cache_manager.disconnect()
            
            logger.info("Test environment cleanup completed")
            
        except Exception as e:
            logger.error(f"Test environment cleanup failed: {e}")
    
    def record_performance_metric(self, test_name: str, metric_name: str, value: float, unit: str):
        """Record performance metric for analysis."""
        self.performance_metrics.append({
            "test_name": test_name,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow()
        })
    
    def record_error(self, test_name: str, error: str):
        """Record test error."""
        self.error_log.append({
            "test_name": test_name,
            "error": error,
            "timestamp": datetime.utcnow()
        })


@pytest.fixture
async def performance_test_suite():
    """Fixture for performance test suite."""
    suite = PerformanceTestSuite()
    await suite.setup_test_environment()
    yield suite
    await suite.teardown_test_environment()


class TestRealCloudAPIIntegration:
    """Test real cloud API integration performance."""
    
    @pytest.mark.asyncio
    async def test_aws_api_performance(self, performance_test_suite):
        """Test AWS API performance with real endpoints."""
        test_name = "aws_api_performance"
        
        try:
            aws_provider = AWSCloudProvider()
            
            # Test multiple concurrent requests
            tasks = []
            for i in range(10):
                task = aws_provider.get_pricing_data("ec2", "us-east-1")
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            successful_requests = [r for r in results if not isinstance(r, Exception)]
            failed_requests = [r for r in results if isinstance(r, Exception)]
            
            total_time = (end_time - start_time) * 1000  # ms
            avg_response_time = total_time / len(tasks)
            success_rate = len(successful_requests) / len(tasks) * 100
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "avg_response_time_ms", avg_response_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "success_rate_percent", success_rate, "percent"
            )
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_requests", len(tasks), "count"
            )
            
            # Assertions
            assert success_rate >= 90, f"AWS API success rate too low: {success_rate}%"
            assert avg_response_time < 5000, f"AWS API response time too high: {avg_response_time}ms"
            
            # Log failed requests
            for error in failed_requests:
                performance_test_suite.record_error(test_name, str(error))
            
            logger.info(f"AWS API test: {success_rate}% success, {avg_response_time:.2f}ms avg response")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"AWS API performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_azure_api_performance(self, performance_test_suite):
        """Test Azure API performance with real endpoints."""
        test_name = "azure_api_performance"
        
        try:
            azure_provider = AzureCloudProvider()
            
            # Test sequential requests to measure individual performance
            response_times = []
            errors = []
            
            for i in range(5):
                start_time = time.time()
                try:
                    result = await azure_provider.get_pricing_data("compute", "eastus")
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                except Exception as e:
                    errors.append(str(e))
                    response_times.append(10000)  # Penalty for failed request
            
            # Calculate statistics
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 5 else max(response_times)
            success_rate = (len(response_times) - len(errors)) / len(response_times) * 100
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "avg_response_time_ms", avg_response_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "p95_response_time_ms", p95_response_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "success_rate_percent", success_rate, "percent"
            )
            
            # Assertions
            assert success_rate >= 80, f"Azure API success rate too low: {success_rate}%"
            assert avg_response_time < 8000, f"Azure API response time too high: {avg_response_time}ms"
            
            logger.info(f"Azure API test: {success_rate}% success, {avg_response_time:.2f}ms avg response")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Azure API performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gcp_api_performance(self, performance_test_suite):
        """Test GCP API performance with real endpoints."""
        test_name = "gcp_api_performance"
        
        try:
            gcp_provider = GCPCloudProvider()
            
            # Test with different regions
            regions = ["us-central1", "us-east1", "europe-west1"]
            all_response_times = []
            total_errors = 0
            
            for region in regions:
                start_time = time.time()
                try:
                    result = await gcp_provider.get_pricing_data("compute", region)
                    response_time = (time.time() - start_time) * 1000
                    all_response_times.append(response_time)
                except Exception as e:
                    total_errors += 1
                    performance_test_suite.record_error(test_name, f"{region}: {str(e)}")
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                max_response_time = max(all_response_times)
                success_rate = len(all_response_times) / len(regions) * 100
                
                # Record metrics
                performance_test_suite.record_performance_metric(
                    test_name, "avg_response_time_ms", avg_response_time, "ms"
                )
                performance_test_suite.record_performance_metric(
                    test_name, "max_response_time_ms", max_response_time, "ms"
                )
                performance_test_suite.record_performance_metric(
                    test_name, "success_rate_percent", success_rate, "percent"
                )
                
                # Assertions
                assert success_rate >= 70, f"GCP API success rate too low: {success_rate}%"
                assert avg_response_time < 10000, f"GCP API response time too high: {avg_response_time}ms"
                
                logger.info(f"GCP API test: {success_rate}% success, {avg_response_time:.2f}ms avg response")
            else:
                pytest.fail("All GCP API requests failed")
                
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"GCP API performance test failed: {e}")


class TestRealLLMIntegration:
    """Test real LLM integration performance."""
    
    @pytest.mark.asyncio
    async def test_openai_llm_performance(self, performance_test_suite):
        """Test OpenAI LLM performance with real API."""
        test_name = "openai_llm_performance"
        
        try:
            llm_provider = OpenAIProvider()
            
            # Test prompts of different complexities
            test_prompts = [
                "What is cloud computing?",  # Simple
                "Compare AWS EC2 vs Azure Virtual Machines for a medium-sized enterprise.",  # Moderate
                "Design a comprehensive multi-cloud infrastructure strategy for a financial services company with strict compliance requirements.",  # Complex
            ]
            
            all_response_times = []
            token_usage = []
            
            for i, prompt in enumerate(test_prompts):
                start_time = time.time()
                try:
                    response = await llm_provider.generate_response(prompt, {})
                    response_time = (time.time() - start_time) * 1000
                    all_response_times.append(response_time)
                    
                    # Track token usage if available
                    if hasattr(response, 'token_usage'):
                        token_usage.append(response.token_usage.total_tokens)
                    
                except Exception as e:
                    performance_test_suite.record_error(test_name, f"Prompt {i}: {str(e)}")
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                max_response_time = max(all_response_times)
                avg_tokens = statistics.mean(token_usage) if token_usage else 0
                
                # Record metrics
                performance_test_suite.record_performance_metric(
                    test_name, "avg_response_time_ms", avg_response_time, "ms"
                )
                performance_test_suite.record_performance_metric(
                    test_name, "max_response_time_ms", max_response_time, "ms"
                )
                performance_test_suite.record_performance_metric(
                    test_name, "avg_tokens_used", avg_tokens, "tokens"
                )
                
                # Assertions
                assert avg_response_time < 30000, f"LLM response time too high: {avg_response_time}ms"
                assert len(all_response_times) >= 2, "Too many LLM requests failed"
                
                logger.info(f"OpenAI LLM test: {avg_response_time:.2f}ms avg response, {avg_tokens:.0f} avg tokens")
            else:
                pytest.fail("All LLM requests failed")
                
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"OpenAI LLM performance test failed: {e}")


class TestDatabasePerformance:
    """Test database performance with real data volumes."""
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, performance_test_suite):
        """Test database query performance with realistic data volumes."""
        test_name = "database_query_performance"
        
        try:
            if db.database is None:
                pytest.skip("Database not available")
            
            # Test different query patterns
            query_tests = [
                {
                    "name": "simple_find",
                    "collection": "assessments",
                    "operation": lambda: db.database.assessments.find_one({"status": "completed"})
                },
                {
                    "name": "complex_aggregation",
                    "collection": "assessments",
                    "operation": lambda: db.database.assessments.aggregate([
                        {"$match": {"status": "completed"}},
                        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ]).to_list(None)
                },
                {
                    "name": "index_scan",
                    "collection": "users",
                    "operation": lambda: db.database.users.find({"email": {"$regex": "@example.com"}}).to_list(100)
                }
            ]
            
            for query_test in query_tests:
                response_times = []
                
                # Run each query multiple times
                for i in range(5):
                    start_time = time.time()
                    try:
                        result = await query_test["operation"]()
                        response_time = (time.time() - start_time) * 1000
                        response_times.append(response_time)
                    except Exception as e:
                        performance_test_suite.record_error(
                            test_name, f"{query_test['name']}: {str(e)}"
                        )
                
                if response_times:
                    avg_response_time = statistics.mean(response_times)
                    max_response_time = max(response_times)
                    
                    # Record metrics
                    performance_test_suite.record_performance_metric(
                        f"{test_name}_{query_test['name']}", "avg_response_time_ms", avg_response_time, "ms"
                    )
                    performance_test_suite.record_performance_metric(
                        f"{test_name}_{query_test['name']}", "max_response_time_ms", max_response_time, "ms"
                    )
                    
                    # Assertions
                    assert avg_response_time < 1000, f"Database query {query_test['name']} too slow: {avg_response_time}ms"
                    
                    logger.info(f"DB query {query_test['name']}: {avg_response_time:.2f}ms avg")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Database performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_database_concurrent_operations(self, performance_test_suite):
        """Test database performance under concurrent load."""
        test_name = "database_concurrent_operations"
        
        try:
            if db.database is None:
                pytest.skip("Database not available")
            
            # Create concurrent read operations
            async def read_operation():
                return await db.database.assessments.find({"status": "completed"}).limit(10).to_list(None)
            
            # Create concurrent write operations
            async def write_operation(i):
                test_doc = {
                    "test_id": f"perf_test_{i}",
                    "created_at": datetime.utcnow(),
                    "data": {"test": True}
                }
                return await db.database.test_collection.insert_one(test_doc)
            
            # Test concurrent reads
            read_tasks = [read_operation() for _ in range(20)]
            start_time = time.time()
            read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
            read_time = (time.time() - start_time) * 1000
            
            # Test concurrent writes
            write_tasks = [write_operation(i) for i in range(10)]
            start_time = time.time()
            write_results = await asyncio.gather(*write_tasks, return_exceptions=True)
            write_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful_reads = [r for r in read_results if not isinstance(r, Exception)]
            successful_writes = [r for r in write_results if not isinstance(r, Exception)]
            
            read_success_rate = len(successful_reads) / len(read_tasks) * 100
            write_success_rate = len(successful_writes) / len(write_tasks) * 100
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_read_time_ms", read_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_write_time_ms", write_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "read_success_rate_percent", read_success_rate, "percent"
            )
            performance_test_suite.record_performance_metric(
                test_name, "write_success_rate_percent", write_success_rate, "percent"
            )
            
            # Assertions
            assert read_success_rate >= 95, f"Concurrent read success rate too low: {read_success_rate}%"
            assert write_success_rate >= 90, f"Concurrent write success rate too low: {write_success_rate}%"
            assert read_time < 5000, f"Concurrent read time too high: {read_time}ms"
            assert write_time < 10000, f"Concurrent write time too high: {write_time}ms"
            
            # Cleanup test data
            await db.database.test_collection.delete_many({"test": True})
            
            logger.info(f"Concurrent DB test: {read_success_rate}% read success, {write_success_rate}% write success")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Database concurrent operations test failed: {e}")


class TestEndToEndWorkflows:
    """Test complete end-to-end user workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_assessment_workflow(self, performance_test_suite):
        """Test complete assessment workflow performance."""
        test_name = "complete_assessment_workflow"
        
        try:
            # Initialize orchestrator
            orchestrator = LangGraphOrchestrator()
            
            # Create test assessment data
            assessment_data = {
                "user_id": "test_user_performance",
                "business_requirements": {
                    "industry": "technology",
                    "company_size": "medium",
                    "budget_range": "100000-500000"
                },
                "technical_requirements": {
                    "current_infrastructure": "on_premise",
                    "preferred_cloud": "aws",
                    "compliance_requirements": ["gdpr", "soc2"]
                }
            }
            
            start_time = time.time()
            
            try:
                # Run complete workflow
                result = await orchestrator.run_assessment_workflow(assessment_data)
                
                end_time = time.time()
                total_time = (end_time - start_time) * 1000  # ms
                
                # Record metrics
                performance_test_suite.record_performance_metric(
                    test_name, "total_workflow_time_ms", total_time, "ms"
                )
                
                # Analyze result
                if result and "recommendations" in result:
                    num_recommendations = len(result["recommendations"])
                    performance_test_suite.record_performance_metric(
                        test_name, "recommendations_generated", num_recommendations, "count"
                    )
                
                # Assertions
                assert total_time < 120000, f"Complete workflow too slow: {total_time}ms"  # 2 minutes max
                assert result is not None, "Workflow returned no result"
                
                logger.info(f"Complete workflow test: {total_time:.2f}ms total time")
                
            except Exception as e:
                end_time = time.time()
                total_time = (end_time - start_time) * 1000
                performance_test_suite.record_error(test_name, f"Workflow failed after {total_time}ms: {str(e)}")
                raise
                
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Complete assessment workflow test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_workflows(self, performance_test_suite):
        """Test system performance with multiple concurrent users."""
        test_name = "concurrent_user_workflows"
        
        try:
            # Simulate multiple users running assessments concurrently
            async def user_workflow(user_id: int):
                cto_agent = CTOAgent()
                
                assessment_data = {
                    "user_id": f"concurrent_user_{user_id}",
                    "business_requirements": {
                        "industry": "technology",
                        "company_size": "small" if user_id % 2 == 0 else "medium"
                    }
                }
                
                start_time = time.time()
                try:
                    result = await cto_agent.analyze_requirements(assessment_data)
                    response_time = (time.time() - start_time) * 1000
                    return {"success": True, "response_time": response_time, "user_id": user_id}
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    return {"success": False, "response_time": response_time, "user_id": user_id, "error": str(e)}
            
            # Run concurrent workflows
            num_concurrent_users = 5
            tasks = [user_workflow(i) for i in range(num_concurrent_users)]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful_workflows = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_workflows = [r for r in results if isinstance(r, dict) and not r.get("success")]
            exception_workflows = [r for r in results if isinstance(r, Exception)]
            
            success_rate = len(successful_workflows) / len(tasks) * 100
            
            if successful_workflows:
                avg_response_time = statistics.mean([r["response_time"] for r in successful_workflows])
                max_response_time = max([r["response_time"] for r in successful_workflows])
            else:
                avg_response_time = 0
                max_response_time = 0
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_workflows_total_time_ms", total_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_workflows_success_rate", success_rate, "percent"
            )
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_workflows_avg_response_time", avg_response_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "concurrent_workflows_max_response_time", max_response_time, "ms"
            )
            
            # Log errors
            for failed in failed_workflows:
                performance_test_suite.record_error(
                    test_name, f"User {failed['user_id']}: {failed.get('error', 'Unknown error')}"
                )
            
            for exception in exception_workflows:
                performance_test_suite.record_error(test_name, str(exception))
            
            # Assertions
            assert success_rate >= 60, f"Concurrent workflow success rate too low: {success_rate}%"
            assert total_time < 180000, f"Concurrent workflows took too long: {total_time}ms"  # 3 minutes max
            
            logger.info(f"Concurrent workflows test: {success_rate}% success, {avg_response_time:.2f}ms avg response")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Concurrent user workflows test failed: {e}")


class TestSystemResourceUsage:
    """Test system resource usage under load."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_test_suite):
        """Test memory usage during high load scenarios."""
        test_name = "memory_usage_under_load"
        
        try:
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Create memory-intensive operations
            async def memory_intensive_operation():
                # Simulate processing large datasets
                large_data = [{"id": i, "data": "x" * 1000} for i in range(1000)]
                await asyncio.sleep(0.1)  # Simulate processing time
                return len(large_data)
            
            # Run multiple operations concurrently
            tasks = [memory_intensive_operation() for _ in range(20)]
            
            # Monitor memory during execution
            memory_samples = []
            
            async def monitor_memory():
                for _ in range(10):  # Sample for 10 seconds
                    current_memory = process.memory_info().rss / (1024 * 1024)
                    memory_samples.append(current_memory)
                    await asyncio.sleep(1)
            
            # Run operations and monitoring concurrently
            monitor_task = asyncio.create_task(monitor_memory())
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await monitor_task
            
            # Get final memory usage
            final_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Calculate memory statistics
            max_memory = max(memory_samples) if memory_samples else final_memory
            avg_memory = statistics.mean(memory_samples) if memory_samples else final_memory
            memory_increase = final_memory - initial_memory
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "initial_memory_mb", initial_memory, "mb"
            )
            performance_test_suite.record_performance_metric(
                test_name, "final_memory_mb", final_memory, "mb"
            )
            performance_test_suite.record_performance_metric(
                test_name, "max_memory_mb", max_memory, "mb"
            )
            performance_test_suite.record_performance_metric(
                test_name, "avg_memory_mb", avg_memory, "mb"
            )
            performance_test_suite.record_performance_metric(
                test_name, "memory_increase_mb", memory_increase, "mb"
            )
            
            # Assertions
            assert max_memory < 2048, f"Memory usage too high: {max_memory}MB"  # 2GB limit
            assert memory_increase < 500, f"Memory increase too high: {memory_increase}MB"  # 500MB increase limit
            
            logger.info(f"Memory test: {initial_memory:.2f}MB -> {final_memory:.2f}MB (max: {max_memory:.2f}MB)")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"Memory usage test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(self, performance_test_suite):
        """Test CPU usage during high load scenarios."""
        test_name = "cpu_usage_under_load"
        
        try:
            # Create CPU-intensive operations
            async def cpu_intensive_operation():
                # Simulate CPU-intensive work
                result = 0
                for i in range(100000):
                    result += i * i
                await asyncio.sleep(0.01)  # Small async break
                return result
            
            # Monitor CPU usage
            cpu_samples = []
            
            async def monitor_cpu():
                for _ in range(10):  # Sample for 10 seconds
                    cpu_percent = psutil.cpu_percent(interval=1)
                    cpu_samples.append(cpu_percent)
            
            # Run operations and monitoring concurrently
            tasks = [cpu_intensive_operation() for _ in range(10)]
            monitor_task = asyncio.create_task(monitor_cpu())
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await monitor_task
            execution_time = (time.time() - start_time) * 1000
            
            # Calculate CPU statistics
            max_cpu = max(cpu_samples) if cpu_samples else 0
            avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
            
            # Record metrics
            performance_test_suite.record_performance_metric(
                test_name, "execution_time_ms", execution_time, "ms"
            )
            performance_test_suite.record_performance_metric(
                test_name, "max_cpu_percent", max_cpu, "percent"
            )
            performance_test_suite.record_performance_metric(
                test_name, "avg_cpu_percent", avg_cpu, "percent"
            )
            
            # Assertions
            assert max_cpu < 90, f"CPU usage too high: {max_cpu}%"  # 90% limit
            assert execution_time < 15000, f"CPU-intensive operations took too long: {execution_time}ms"
            
            logger.info(f"CPU test: {avg_cpu:.2f}% avg, {max_cpu:.2f}% max, {execution_time:.2f}ms execution")
            
        except Exception as e:
            performance_test_suite.record_error(test_name, str(e))
            pytest.fail(f"CPU usage test failed: {e}")


@pytest.mark.asyncio
async def test_generate_performance_report(performance_test_suite):
    """Generate comprehensive performance test report."""
    try:
        # Get performance report from optimizer
        performance_report = await performance_optimizer.get_performance_report()
        
        # Combine with test results
        test_report = {
            "test_execution": {
                "start_time": performance_test_suite.start_time,
                "end_time": performance_test_suite.end_time,
                "total_tests": len(performance_test_suite.performance_metrics),
                "total_errors": len(performance_test_suite.error_log)
            },
            "performance_metrics": performance_test_suite.performance_metrics,
            "error_log": performance_test_suite.error_log,
            "system_performance": performance_report,
            "summary": {
                "overall_status": "PASS" if len(performance_test_suite.error_log) == 0 else "FAIL",
                "critical_errors": len([e for e in performance_test_suite.error_log if "failed" in e["error"].lower()]),
                "performance_warnings": len([m for m in performance_test_suite.performance_metrics if m["value"] > 5000 and m["unit"] == "ms"])
            }
        }
        
        # Save report to file
        import json
        with open("performance_test_report.json", "w") as f:
            json.dump(test_report, f, indent=2, default=str)
        
        logger.info("Performance test report generated: performance_test_report.json")
        
        # Assert overall test success
        assert test_report["summary"]["overall_status"] == "PASS", "Performance tests failed"
        
    except Exception as e:
        pytest.fail(f"Performance report generation failed: {e}")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])