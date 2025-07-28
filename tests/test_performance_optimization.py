"""
Tests for performance optimization features.

Tests database query optimization, advanced caching, LLM prompt optimization,
and horizontal scaling capabilities.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.infra_mind.core.performance_optimizer import (
    DatabaseQueryOptimizer,
    AdvancedCacheManager,
    LLMPromptOptimizer,
    HorizontalScalingManager,
    PerformanceOptimizer,
    QueryPerformanceMetrics,
    CachePerformanceMetrics,
    LLMOptimizationMetrics
)


class TestDatabaseQueryOptimizer:
    """Test database query optimization."""
    
    @pytest.fixture
    def db_optimizer(self):
        """Create database query optimizer instance."""
        return DatabaseQueryOptimizer()
    
    def test_generate_query_hash(self, db_optimizer):
        """Test query hash generation."""
        query1 = {"user_id": "123", "status": "active"}
        query2 = {"status": "active", "user_id": "123"}  # Same query, different order
        
        hash1 = db_optimizer._generate_query_hash("users", "find", query1)
        hash2 = db_optimizer._generate_query_hash("users", "find", query2)
        
        assert hash1 == hash2  # Should be same due to sorting
        assert len(hash1) == 12  # Should be 12 characters
    
    @pytest.mark.asyncio
    async def test_profile_query(self, db_optimizer):
        """Test query profiling context manager."""
        collection = "test_collection"
        operation = "find"
        query = {"test": "value"}
        
        async with db_optimizer.profile_query(collection, operation, query) as query_hash:
            # Simulate some work
            await asyncio.sleep(0.01)
            assert query_hash is not None
            assert len(query_hash) == 12
        
        # Check that metrics were recorded
        assert query_hash in db_optimizer.query_metrics
        metrics = db_optimizer.query_metrics[query_hash]
        assert len(metrics) == 1
        assert metrics[0].collection == collection
        assert metrics[0].operation == operation
        assert metrics[0].execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_analyze_slow_query(self, db_optimizer):
        """Test slow query analysis."""
        metrics = QueryPerformanceMetrics(
            query_hash="test_hash",
            collection="test_collection",
            operation="find",
            execution_time_ms=2500,  # Slow query
            documents_examined=10000,
            documents_returned=10,
            index_used=False
        )
        
        await db_optimizer._analyze_slow_query(metrics, {"test": "query"})
        
        # Check that suggestions were generated
        assert "test_hash" in db_optimizer.optimization_suggestions
        suggestions = db_optimizer.optimization_suggestions["test_hash"]
        assert len(suggestions) > 0
        assert any("index" in suggestion.lower() for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_get_query_performance_report(self, db_optimizer):
        """Test query performance report generation."""
        # Add some test metrics
        test_metrics = [
            QueryPerformanceMetrics(
                query_hash="hash1",
                collection="users",
                operation="find",
                execution_time_ms=100,
                documents_examined=50,
                documents_returned=10,
                index_used=True
            ),
            QueryPerformanceMetrics(
                query_hash="hash2",
                collection="assessments",
                operation="find",
                execution_time_ms=1500,  # Slow query
                documents_examined=1000,
                documents_returned=5,
                index_used=False
            )
        ]
        
        for metric in test_metrics:
            db_optimizer.query_metrics[metric.query_hash].append(metric)
        
        report = await db_optimizer.get_query_performance_report()
        
        assert "summary" in report
        assert report["summary"]["total_queries"] == 2
        assert report["summary"]["slow_queries_count"] == 1
        assert "collection_stats" in report
        assert "users" in report["collection_stats"]
        assert "assessments" in report["collection_stats"]


class TestAdvancedCacheManager:
    """Test advanced cache management."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create advanced cache manager instance."""
        return AdvancedCacheManager()
    
    def test_determine_cache_tier(self, cache_manager):
        """Test cache tier determination."""
        cache_key = "test_key"
        
        # No access history - should be cold
        tier = cache_manager._determine_cache_tier(cache_key)
        assert tier == "cold"
        
        # Add frequent accesses
        current_time = time.time()
        for i in range(15):
            cache_manager.access_patterns[cache_key].append(current_time - i * 60)  # Every minute
        
        tier = cache_manager._determine_cache_tier(cache_key)
        assert tier == "hot"
    
    def test_get_related_services(self, cache_manager):
        """Test related services identification."""
        related = cache_manager._get_related_services("ec2")
        assert "ebs" in related
        assert "vpc" in related
        
        related = cache_manager._get_related_services("unknown_service")
        assert related == []
    
    @pytest.mark.asyncio
    async def test_intelligent_cache_operations(self, cache_manager):
        """Test intelligent cache get and set operations."""
        with patch('src.infra_mind.core.cache.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"test": "data"})
            mock_cache.set = AsyncMock(return_value=True)
            
            # Test get
            result = await cache_manager.intelligent_get("aws", "ec2", "us-east-1")
            assert result == {"test": "data"}
            
            # Test set
            success = await cache_manager.intelligent_set(
                "aws", "ec2", "us-east-1", {"test": "data"}
            )
            assert success is True
    
    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_manager):
        """Test cache warming functionality."""
        warmup_data = [
            {
                "provider": "aws",
                "service": "ec2",
                "region": "us-east-1",
                "data": {"instances": ["t3.micro"]}
            }
        ]
        
        with patch.object(cache_manager, 'intelligent_set', return_value=True):
            result = await cache_manager.warm_cache(warmup_data)
            
            assert result["warmed_count"] == 1
            assert result["failed_count"] == 0
            assert result["total_items"] == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_performance_report(self, cache_manager):
        """Test cache performance report generation."""
        # Add some test metrics
        test_metrics = [
            CachePerformanceMetrics(
                cache_key="test_key_1",
                operation="get",
                hit=True,
                execution_time_ms=5.0,
                data_size_bytes=1024
            ),
            CachePerformanceMetrics(
                cache_key="test_key_2",
                operation="get",
                hit=False,
                execution_time_ms=10.0,
                data_size_bytes=0
            )
        ]
        
        for metric in test_metrics:
            cache_manager.cache_metrics[metric.cache_key].append(metric)
        
        report = await cache_manager.get_cache_performance_report()
        
        assert "summary" in report
        assert report["summary"]["total_operations"] == 2
        assert report["summary"]["hit_rate_percent"] == 50.0


class TestLLMPromptOptimizer:
    """Test LLM prompt optimization."""
    
    @pytest.fixture
    def llm_optimizer(self):
        """Create LLM prompt optimizer instance."""
        return LLMPromptOptimizer()
    
    def test_count_tokens(self, llm_optimizer):
        """Test token counting."""
        text = "This is a test prompt with some words."
        tokens = llm_optimizer._count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_optimization_rules(self, llm_optimizer):
        """Test prompt optimization rules."""
        original_prompt = """
        Please help me with this task. I would like you to analyze the following data.
        For example, you could look at the trends and patterns.
        
        1. First item
        2. Second item
        3. Third item
        """
        
        optimized_prompt = original_prompt
        for rule in llm_optimizer.optimization_rules:
            optimized_prompt = rule(optimized_prompt)
        
        # Should be shorter after optimization
        assert len(optimized_prompt) <= len(original_prompt)
        # Should remove redundant phrases
        assert "please" not in optimized_prompt.lower()
        assert "i would like you to" not in optimized_prompt.lower()
    
    def test_optimize_prompt(self, llm_optimizer):
        """Test prompt optimization."""
        agent_name = "test_agent"
        original_prompt = "Please help me analyze this data. I would like you to provide recommendations."
        
        optimized_prompt, metrics = llm_optimizer.optimize_prompt(agent_name, original_prompt)
        
        assert len(optimized_prompt) <= len(original_prompt)
        assert metrics["original_tokens"] > 0
        assert metrics["optimized_tokens"] > 0
        assert metrics["compression_ratio"] >= 0
        assert metrics["cost_savings_percent"] >= 0
        
        # Check that metrics were recorded
        assert agent_name in llm_optimizer.optimization_metrics
        assert len(llm_optimizer.optimization_metrics[agent_name]) == 1
    
    def test_get_optimization_report(self, llm_optimizer):
        """Test optimization report generation."""
        # Add some test metrics
        test_metrics = [
            LLMOptimizationMetrics(
                prompt_hash="hash1",
                agent_name="agent1",
                original_tokens=100,
                optimized_tokens=80,
                compression_ratio=20.0,
                response_quality_score=0.95,
                cost_savings_percent=20.0
            ),
            LLMOptimizationMetrics(
                prompt_hash="hash2",
                agent_name="agent2",
                original_tokens=200,
                optimized_tokens=150,
                compression_ratio=25.0,
                response_quality_score=0.90,
                cost_savings_percent=25.0
            )
        ]
        
        for metric in test_metrics:
            llm_optimizer.optimization_metrics[metric.agent_name].append(metric)
        
        report = llm_optimizer.get_optimization_report()
        
        assert "summary" in report
        assert report["summary"]["total_optimizations"] == 2
        assert report["summary"]["total_original_tokens"] == 300
        assert report["summary"]["total_optimized_tokens"] == 230
        assert "agent_stats" in report
        assert "agent1" in report["agent_stats"]
        assert "agent2" in report["agent_stats"]


class TestHorizontalScalingManager:
    """Test horizontal scaling management."""
    
    @pytest.fixture
    def scaling_manager(self):
        """Create horizontal scaling manager instance."""
        return HorizontalScalingManager()
    
    def test_register_agent_type(self, scaling_manager):
        """Test agent type registration."""
        def mock_factory():
            return Mock(is_busy=False)
        
        scaling_policy = {
            "min_instances": 2,
            "max_instances": 5,
            "scale_up_threshold": 80,
            "scale_down_threshold": 30
        }
        
        scaling_manager.register_agent_type("test_agent", mock_factory, scaling_policy)
        
        assert "test_agent" in scaling_manager.scaling_policies
        assert scaling_manager.scaling_policies["test_agent"] == scaling_policy
        assert "test_agent" in scaling_manager.agent_pools
        assert len(scaling_manager.agent_pools["test_agent"]) == 2  # min_instances
    
    @pytest.mark.asyncio
    async def test_get_available_agent(self, scaling_manager):
        """Test agent allocation."""
        def mock_factory():
            return Mock(is_busy=False)
        
        scaling_manager.register_agent_type("test_agent", mock_factory)
        
        agent = await scaling_manager.get_available_agent("test_agent")
        assert agent is not None
        assert hasattr(agent, 'is_busy')
    
    def test_return_agent(self, scaling_manager):
        """Test agent return to pool."""
        mock_agent = Mock(is_busy=True)
        
        scaling_manager.return_agent("test_agent", mock_agent)
        
        assert mock_agent.is_busy is False
    
    def test_record_load_metric(self, scaling_manager):
        """Test load metric recording."""
        # Add some mock agents
        scaling_manager.agent_pools["test_agent"] = [
            Mock(is_busy=True),
            Mock(is_busy=False),
            Mock(is_busy=True)
        ]
        
        scaling_manager._record_load_metric("test_agent")
        
        assert "test_agent" in scaling_manager.load_metrics
        metrics = list(scaling_manager.load_metrics["test_agent"])
        assert len(metrics) == 1
        assert metrics[0]["load_percent"] == (2/3) * 100  # 2 busy out of 3
    
    @pytest.mark.asyncio
    async def test_should_scale_up(self, scaling_manager):
        """Test scale up decision logic."""
        # Setup agent pool and policy
        scaling_manager.scaling_policies["test_agent"] = {
            "min_instances": 1,
            "max_instances": 5,
            "scale_up_threshold": 75
        }
        scaling_manager.agent_pools["test_agent"] = [Mock()]
        
        # Add high load metrics
        for _ in range(10):
            scaling_manager.load_metrics["test_agent"].append({
                "timestamp": time.time(),
                "load_percent": 85.0  # Above threshold
            })
        
        should_scale = await scaling_manager._should_scale_up("test_agent")
        assert should_scale is True
    
    @pytest.mark.asyncio
    async def test_should_scale_down(self, scaling_manager):
        """Test scale down decision logic."""
        # Setup agent pool and policy
        scaling_manager.scaling_policies["test_agent"] = {
            "min_instances": 1,
            "max_instances": 5,
            "scale_down_threshold": 25
        }
        scaling_manager.agent_pools["test_agent"] = [Mock(), Mock()]  # 2 instances
        
        # Add low load metrics
        for _ in range(20):
            scaling_manager.load_metrics["test_agent"].append({
                "timestamp": time.time(),
                "load_percent": 15.0  # Below threshold
            })
        
        should_scale = await scaling_manager._should_scale_down("test_agent")
        assert should_scale is True
    
    def test_get_scaling_status(self, scaling_manager):
        """Test scaling status retrieval."""
        # Setup test data
        scaling_manager.scaling_policies["test_agent"] = {
            "min_instances": 1,
            "max_instances": 5
        }
        scaling_manager.agent_pools["test_agent"] = [Mock(is_busy=False), Mock(is_busy=True)]
        scaling_manager.load_metrics["test_agent"].append({
            "timestamp": time.time(),
            "load_percent": 50.0
        })
        
        status = scaling_manager.get_scaling_status()
        
        assert "test_agent" in status
        agent_status = status["test_agent"]
        assert agent_status["current_instances"] == 2
        assert agent_status["min_instances"] == 1
        assert agent_status["max_instances"] == 5
        assert agent_status["busy_instances"] == 1


class TestPerformanceOptimizer:
    """Test main performance optimizer."""
    
    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer instance."""
        return PerformanceOptimizer()
    
    @pytest.mark.asyncio
    async def test_start_stop_optimization_services(self, performance_optimizer):
        """Test starting and stopping optimization services."""
        # Mock the background tasks to avoid actual execution
        with patch('asyncio.create_task') as mock_create_task:
            mock_task = Mock()
            mock_create_task.return_value = mock_task
            
            await performance_optimizer.start_optimization_services()
            
            assert len(performance_optimizer._background_tasks) == 2
            assert mock_create_task.call_count == 2
            
            # Test stopping services
            mock_task.cancel = Mock()
            
            with patch('asyncio.gather', return_value=None):
                await performance_optimizer.stop_optimization_services()
                
                mock_task.cancel.assert_called()
                assert len(performance_optimizer._background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_performance_report(self, performance_optimizer):
        """Test comprehensive performance report generation."""
        # Mock the component reports
        with patch.object(performance_optimizer.db_optimizer, 'get_query_performance_report') as mock_db:
            with patch.object(performance_optimizer.cache_manager, 'get_cache_performance_report') as mock_cache:
                with patch.object(performance_optimizer.llm_optimizer, 'get_optimization_report') as mock_llm:
                    with patch.object(performance_optimizer.scaling_manager, 'get_scaling_status') as mock_scaling:
                        
                        # Setup mock returns
                        mock_db.return_value = {"summary": {"total_queries": 10}}
                        mock_cache.return_value = {"summary": {"hit_rate_percent": 85.0}}
                        mock_llm.return_value = {"summary": {"total_optimizations": 5}}
                        mock_scaling.return_value = {"agent1": {"current_instances": 2}}
                        
                        report = await performance_optimizer.get_comprehensive_performance_report()
                        
                        assert "timestamp" in report
                        assert "system_resources" in report
                        assert "database_performance" in report
                        assert "cache_performance" in report
                        assert "llm_optimization" in report
                        assert "scaling_status" in report
                        assert "optimization_recommendations" in report
    
    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, performance_optimizer):
        """Test optimization recommendations generation."""
        with patch('psutil.cpu_percent', return_value=85.0):  # High CPU
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.percent = 90.0  # High memory
                
                recommendations = await performance_optimizer._generate_optimization_recommendations()
                
                assert len(recommendations) >= 2  # Should have CPU and memory recommendations
                
                cpu_rec = next((r for r in recommendations if "CPU" in r["issue"]), None)
                assert cpu_rec is not None
                assert cpu_rec["priority"] == "high"
                
                memory_rec = next((r for r in recommendations if "memory" in r["issue"]), None)
                assert memory_rec is not None
                assert memory_rec["priority"] == "high"


@pytest.mark.asyncio
async def test_integration_performance_optimization():
    """Integration test for performance optimization components."""
    # Test that all components work together
    optimizer = PerformanceOptimizer()
    
    # Test database optimization
    async with optimizer.db_optimizer.profile_query("test", "find", {"test": "query"}):
        await asyncio.sleep(0.01)
    
    # Test LLM optimization
    prompt = "Please help me with this task."
    optimized, metrics = optimizer.llm_optimizer.optimize_prompt("test_agent", prompt)
    assert len(optimized) <= len(prompt)
    
    # Test cache operations
    with patch('src.infra_mind.core.cache.cache_manager._connected', True):
        with patch('src.infra_mind.core.cache.cache_manager.redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock(return_value=True)
            
            result = await optimizer.cache_manager.intelligent_get("aws", "ec2", "us-east-1")
            assert result is None
            
            success = await optimizer.cache_manager.intelligent_set("aws", "ec2", "us-east-1", {"test": "data"})
            assert success is True
    
    # Test scaling manager
    def mock_factory():
        return Mock(is_busy=False)
    
    optimizer.scaling_manager.register_agent_type("test_agent", mock_factory)
    agent = await optimizer.scaling_manager.get_available_agent("test_agent")
    assert agent is not None


if __name__ == "__main__":
    pytest.main([__file__])