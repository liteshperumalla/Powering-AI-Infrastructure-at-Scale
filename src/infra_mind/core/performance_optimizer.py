"""
Performance Optimization Service for Infra Mind.

Implements database query optimization, advanced caching strategies,
LLM prompt engineering optimization, and horizontal scaling capabilities.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import hashlib
import json
from collections import defaultdict, deque
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ..models.metrics import Metric, MetricType, MetricCategory
from ..core.config import get_settings
from ..core.cache import cache_manager
from ..core.database import db
from ..core.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Database query performance metrics."""
    query_hash: str
    collection: str
    operation: str
    execution_time_ms: float
    documents_examined: int
    documents_returned: int
    index_used: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics."""
    cache_key: str
    operation: str  # get, set, delete
    hit: bool
    execution_time_ms: float
    data_size_bytes: int
    ttl_seconds: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LLMOptimizationMetrics:
    """LLM optimization metrics."""
    prompt_hash: str
    agent_name: str
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    response_quality_score: float
    cost_savings_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DatabaseQueryOptimizer:
    """
    Database query optimization service.
    
    Profiles and optimizes MongoDB queries for better performance.
    """
    
    def __init__(self):
        """Initialize database query optimizer."""
        self.query_metrics: Dict[str, List[QueryPerformanceMetrics]] = defaultdict(list)
        self.slow_query_threshold_ms = 1000  # 1 second
        self.optimization_suggestions: Dict[str, List[str]] = defaultdict(list)
        self.metrics_collector = get_metrics_collector()
    
    def _generate_query_hash(self, collection: str, operation: str, 
                           query: Dict[str, Any]) -> str:
        """Generate hash for query identification."""
        query_str = json.dumps({
            "collection": collection,
            "operation": operation,
            "query": query
        }, sort_keys=True, default=str)
        return hashlib.md5(query_str.encode()).hexdigest()[:12]
    
    @asynccontextmanager
    async def profile_query(self, collection: str, operation: str, 
                          query: Dict[str, Any]):
        """Context manager to profile database queries."""
        query_hash = self._generate_query_hash(collection, operation, query)
        start_time = time.time()
        
        # Enable profiling for this query
        if db.database is not None:
            await db.database.command("profile", 2)  # Profile all operations
        
        try:
            yield query_hash
        finally:
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Collect query metrics
            if db.database is not None:
                try:
                    # Get profiling data
                    profiling_data = await db.database.system.profile.find_one(
                        {"ts": {"$gte": datetime.utcnow() - timedelta(seconds=5)}},
                        sort=[("ts", -1)]
                    )
                    
                    docs_examined = profiling_data.get("totalDocsExamined", 0) if profiling_data else 0
                    docs_returned = profiling_data.get("docsReturned", 0) if profiling_data else 0
                    index_used = bool(profiling_data.get("planSummary", "").startswith("IXSCAN")) if profiling_data else False
                    
                except Exception as e:
                    logger.debug(f"Could not get profiling data: {e}")
                    docs_examined = 0
                    docs_returned = 0
                    index_used = False
            else:
                docs_examined = 0
                docs_returned = 0
                index_used = False
            
            # Record metrics
            metrics = QueryPerformanceMetrics(
                query_hash=query_hash,
                collection=collection,
                operation=operation,
                execution_time_ms=execution_time,
                documents_examined=docs_examined,
                documents_returned=docs_returned,
                index_used=index_used
            )
            
            self.query_metrics[query_hash].append(metrics)
            
            # Record in metrics collector
            await self.metrics_collector.record_monitoring_metric(
                f"database.query.{operation}.execution_time",
                execution_time,
                "ms"
            )
            
            # Check for slow queries
            if execution_time > self.slow_query_threshold_ms:
                await self._analyze_slow_query(metrics, query)
            
            # Disable profiling to avoid overhead
            if db.database is not None:
                await db.database.command("profile", 0)
    
    async def _analyze_slow_query(self, metrics: QueryPerformanceMetrics, 
                                query: Dict[str, Any]) -> None:
        """Analyze slow query and generate optimization suggestions."""
        suggestions = []
        
        # Check if index is being used
        if not metrics.index_used and metrics.documents_examined > 100:
            suggestions.append(f"Consider adding index for collection {metrics.collection}")
        
        # Check for full collection scans
        if metrics.documents_examined > metrics.documents_returned * 10:
            suggestions.append("Query is examining too many documents - consider more selective criteria")
        
        # Check for large result sets
        if metrics.documents_returned > 1000:
            suggestions.append("Consider using pagination for large result sets")
        
        # Store suggestions
        if suggestions:
            self.optimization_suggestions[metrics.query_hash].extend(suggestions)
            
            # Log slow query
            logger.warning(
                f"Slow query detected: {metrics.collection}.{metrics.operation} "
                f"({metrics.execution_time_ms:.2f}ms, {metrics.documents_examined} examined, "
                f"{metrics.documents_returned} returned)"
            )
    
    async def get_query_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive query performance report."""
        total_queries = sum(len(queries) for queries in self.query_metrics.values())
        
        if total_queries == 0:
            return {"message": "No query metrics available"}
        
        # Calculate statistics
        all_metrics = []
        for queries in self.query_metrics.values():
            all_metrics.extend(queries)
        
        avg_execution_time = sum(m.execution_time_ms for m in all_metrics) / len(all_metrics)
        slow_queries = [m for m in all_metrics if m.execution_time_ms > self.slow_query_threshold_ms]
        
        # Group by collection
        collection_stats = defaultdict(list)
        for metric in all_metrics:
            collection_stats[metric.collection].append(metric)
        
        collection_summary = {}
        for collection, metrics in collection_stats.items():
            collection_summary[collection] = {
                "total_queries": len(metrics),
                "avg_execution_time_ms": sum(m.execution_time_ms for m in metrics) / len(metrics),
                "slow_queries": len([m for m in metrics if m.execution_time_ms > self.slow_query_threshold_ms]),
                "index_usage_rate": sum(1 for m in metrics if m.index_used) / len(metrics) * 100
            }
        
        return {
            "summary": {
                "total_queries": total_queries,
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "slow_queries_count": len(slow_queries),
                "slow_query_rate": len(slow_queries) / total_queries * 100
            },
            "collection_stats": collection_summary,
            "optimization_suggestions": dict(self.optimization_suggestions),
            "top_slow_queries": [
                {
                    "query_hash": m.query_hash,
                    "collection": m.collection,
                    "operation": m.operation,
                    "execution_time_ms": m.execution_time_ms,
                    "documents_examined": m.documents_examined,
                    "index_used": m.index_used
                }
                for m in sorted(all_metrics, key=lambda x: x.execution_time_ms, reverse=True)[:10]
            ]
        }
    
    async def optimize_indexes(self) -> Dict[str, Any]:
        """Analyze and suggest index optimizations."""
        if db.database is None:
            return {"error": "Database not available"}
        
        suggestions = []
        
        try:
            # Analyze each collection
            collections = await db.database.list_collection_names()
            
            for collection_name in collections:
                if collection_name.startswith("system."):
                    continue
                
                collection = db.database[collection_name]
                
                # Get current indexes
                indexes = await collection.list_indexes().to_list(None)
                current_indexes = [idx.get("key", {}) for idx in indexes]
                
                # Analyze query patterns for this collection
                collection_metrics = []
                for queries in self.query_metrics.values():
                    collection_metrics.extend([q for q in queries if q.collection == collection_name])
                
                if not collection_metrics:
                    continue
                
                # Find queries without index usage
                no_index_queries = [m for m in collection_metrics if not m.index_used]
                
                if no_index_queries:
                    suggestions.append({
                        "collection": collection_name,
                        "issue": "Queries without index usage",
                        "count": len(no_index_queries),
                        "suggestion": f"Consider adding indexes for {collection_name}",
                        "current_indexes": current_indexes
                    })
            
            return {
                "suggestions": suggestions,
                "total_collections_analyzed": len(collections)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            return {"error": str(e)}


class AdvancedCacheManager:
    """
    Advanced caching strategies for frequently accessed data.
    
    Implements multi-tier caching, intelligent prefetching, and cache warming.
    """
    
    def __init__(self):
        """Initialize advanced cache manager."""
        self.cache_metrics: Dict[str, List[CachePerformanceMetrics]] = defaultdict(list)
        self.access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.prefetch_queue: asyncio.Queue = asyncio.Queue()
        self.cache_warming_enabled = True
        self.metrics_collector = get_metrics_collector()
        
        # Cache tiers with different TTLs
        self.cache_tiers = {
            "hot": {"ttl": 300, "max_size": 1000},      # 5 minutes, frequently accessed
            "warm": {"ttl": 1800, "max_size": 5000},    # 30 minutes, moderately accessed
            "cold": {"ttl": 3600, "max_size": 10000}    # 1 hour, rarely accessed
        }
    
    def _determine_cache_tier(self, cache_key: str) -> str:
        """Determine appropriate cache tier based on access patterns."""
        access_history = self.access_patterns[cache_key]
        
        if len(access_history) < 5:
            return "cold"
        
        # Calculate access frequency (accesses per hour)
        now = time.time()
        recent_accesses = sum(1 for access_time in access_history if now - access_time < 3600)
        
        if recent_accesses >= 10:
            return "hot"
        elif recent_accesses >= 3:
            return "warm"
        else:
            return "cold"
    
    @asynccontextmanager
    async def track_cache_operation(self, cache_key: str, operation: str):
        """Context manager to track cache operations."""
        start_time = time.time()
        hit = False
        data_size = 0
        
        try:
            yield
            hit = True  # If no exception, it's a hit
        except Exception:
            hit = False
        finally:
            execution_time = (time.time() - start_time) * 1000
            
            # Record access pattern
            self.access_patterns[cache_key].append(time.time())
            
            # Record metrics
            metrics = CachePerformanceMetrics(
                cache_key=cache_key,
                operation=operation,
                hit=hit,
                execution_time_ms=execution_time,
                data_size_bytes=data_size
            )
            
            self.cache_metrics[cache_key].append(metrics)
            
            # Record in metrics collector
            await self.metrics_collector.record_monitoring_metric(
                f"cache.{operation}.execution_time",
                execution_time,
                "ms"
            )
    
    async def intelligent_get(self, provider: str, service: str, region: str,
                            params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Intelligent cache get with tier management and prefetching."""
        cache_key = f"{provider}:{service}:{region}"
        if params:
            cache_key += f":{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]}"
        
        async with self.track_cache_operation(cache_key, "get"):
            # Try to get from cache
            data = await cache_manager.get(provider, service, region, params)
            
            if data:
                # Schedule prefetch of related data
                await self._schedule_prefetch(provider, service, region, params)
                return data
            
            return None
    
    async def intelligent_set(self, provider: str, service: str, region: str,
                            data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Intelligent cache set with tier-based TTL."""
        cache_key = f"{provider}:{service}:{region}"
        if params:
            cache_key += f":{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]}"
        
        # Determine appropriate cache tier
        tier = self._determine_cache_tier(cache_key)
        ttl = self.cache_tiers[tier]["ttl"]
        
        async with self.track_cache_operation(cache_key, "set"):
            return await cache_manager.set(provider, service, region, data, ttl, params)
    
    async def _schedule_prefetch(self, provider: str, service: str, region: str,
                               params: Optional[Dict[str, Any]] = None) -> None:
        """Schedule prefetching of related data."""
        if not self.cache_warming_enabled:
            return
        
        # Prefetch related services in the same region
        related_services = self._get_related_services(service)
        
        for related_service in related_services:
            prefetch_item = {
                "provider": provider,
                "service": related_service,
                "region": region,
                "params": params,
                "priority": "low"
            }
            
            try:
                self.prefetch_queue.put_nowait(prefetch_item)
            except asyncio.QueueFull:
                logger.debug("Prefetch queue full, skipping prefetch")
    
    def _get_related_services(self, service: str) -> List[str]:
        """Get list of related services for prefetching."""
        service_relationships = {
            "ec2": ["ebs", "vpc", "elb"],
            "rds": ["ec2", "vpc", "backup"],
            "lambda": ["api-gateway", "cloudwatch", "iam"],
            "compute": ["storage", "network", "monitoring"],
            "sql": ["compute", "storage", "backup"]
        }
        
        return service_relationships.get(service, [])
    
    async def start_prefetch_worker(self) -> None:
        """Start background prefetch worker."""
        while True:
            try:
                # Get prefetch item with timeout
                prefetch_item = await asyncio.wait_for(
                    self.prefetch_queue.get(),
                    timeout=10.0
                )
                
                # Perform prefetch (this would call the actual API)
                logger.debug(f"Prefetching: {prefetch_item}")
                
                # Mark task as done
                self.prefetch_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in prefetch worker: {e}")
    
    async def warm_cache(self, warmup_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Warm cache with frequently accessed data."""
        warmed_count = 0
        failed_count = 0
        
        for item in warmup_data:
            try:
                provider = item["provider"]
                service = item["service"]
                region = item["region"]
                data = item["data"]
                params = item.get("params")
                
                success = await self.intelligent_set(provider, service, region, data, params)
                if success:
                    warmed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error warming cache item: {e}")
                failed_count += 1
        
        return {
            "warmed_count": warmed_count,
            "failed_count": failed_count,
            "total_items": len(warmup_data)
        }
    
    async def get_cache_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive cache performance report."""
        total_operations = sum(len(metrics) for metrics in self.cache_metrics.values())
        
        if total_operations == 0:
            return {"message": "No cache metrics available"}
        
        # Calculate statistics
        all_metrics = []
        for metrics in self.cache_metrics.values():
            all_metrics.extend(metrics)
        
        hit_rate = sum(1 for m in all_metrics if m.hit) / len(all_metrics) * 100
        avg_response_time = sum(m.execution_time_ms for m in all_metrics) / len(all_metrics)
        
        # Tier distribution
        tier_distribution = {"hot": 0, "warm": 0, "cold": 0}
        for cache_key in self.cache_metrics.keys():
            tier = self._determine_cache_tier(cache_key)
            tier_distribution[tier] += 1
        
        return {
            "summary": {
                "total_operations": total_operations,
                "hit_rate_percent": round(hit_rate, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "prefetch_queue_size": self.prefetch_queue.qsize()
            },
            "tier_distribution": tier_distribution,
            "top_accessed_keys": [
                {
                    "cache_key": key,
                    "access_count": len(self.access_patterns[key]),
                    "tier": self._determine_cache_tier(key)
                }
                for key in sorted(self.access_patterns.keys(), 
                                key=lambda k: len(self.access_patterns[k]), reverse=True)[:10]
            ]
        }


class LLMPromptOptimizer:
    """
    LLM prompt engineering optimization to reduce costs.
    
    Optimizes prompts for token efficiency while maintaining quality.
    """
    
    def __init__(self):
        """Initialize LLM prompt optimizer."""
        self.optimization_metrics: Dict[str, List[LLMOptimizationMetrics]] = defaultdict(list)
        self.prompt_templates: Dict[str, str] = {}
        self.optimization_rules: List[Callable[[str], str]] = []
        self.metrics_collector = get_metrics_collector()
        
        # Load optimization rules
        self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> None:
        """Load prompt optimization rules."""
        
        def remove_redundant_words(prompt: str) -> str:
            """Remove redundant words and phrases."""
            redundant_phrases = [
                "please", "kindly", "if you would", "I would like you to",
                "could you", "would you mind", "it would be great if"
            ]
            
            optimized = prompt
            for phrase in redundant_phrases:
                optimized = optimized.replace(phrase, "")
            
            return optimized.strip()
        
        def compress_examples(prompt: str) -> str:
            """Compress examples while maintaining clarity."""
            # This is a simplified version - in practice, you'd use more sophisticated NLP
            if "for example" in prompt.lower():
                # Reduce verbose examples
                optimized = prompt.replace("For example, ", "E.g., ")
                optimized = optimized.replace("for example, ", "e.g., ")
                return optimized
            return prompt
        
        def optimize_structure(prompt: str) -> str:
            """Optimize prompt structure for efficiency."""
            # Use bullet points instead of verbose descriptions
            if "\n- " in prompt:
                return prompt  # Already optimized
            
            # Convert numbered lists to bullet points (shorter)
            import re
            optimized = re.sub(r'\n\d+\.\s+', '\n- ', prompt)
            return optimized
        
        self.optimization_rules = [
            remove_redundant_words,
            compress_examples,
            optimize_structure
        ]
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simplified)."""
        # This is a rough approximation - in practice, use tiktoken or similar
        return len(text.split()) + len(text) // 4
    
    def optimize_prompt(self, agent_name: str, original_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Optimize a prompt for token efficiency.
        
        Args:
            agent_name: Name of the agent using the prompt
            original_prompt: Original prompt text
            
        Returns:
            Tuple of (optimized_prompt, optimization_metrics)
        """
        original_tokens = self._count_tokens(original_prompt)
        optimized_prompt = original_prompt
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            try:
                optimized_prompt = rule(optimized_prompt)
            except Exception as e:
                logger.warning(f"Optimization rule failed: {e}")
        
        optimized_tokens = self._count_tokens(optimized_prompt)
        compression_ratio = (original_tokens - optimized_tokens) / original_tokens * 100
        
        # Estimate cost savings (assuming $0.002 per 1K tokens)
        cost_per_token = 0.000002
        cost_savings = (original_tokens - optimized_tokens) * cost_per_token
        cost_savings_percent = compression_ratio
        
        # Generate prompt hash for tracking
        prompt_hash = hashlib.md5(original_prompt.encode()).hexdigest()[:12]
        
        # Record metrics
        metrics = LLMOptimizationMetrics(
            prompt_hash=prompt_hash,
            agent_name=agent_name,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            compression_ratio=compression_ratio,
            response_quality_score=0.95,  # Would be measured in practice
            cost_savings_percent=cost_savings_percent
        )
        
        self.optimization_metrics[agent_name].append(metrics)
        
        # Record in metrics collector
        asyncio.create_task(self.metrics_collector.record_monitoring_metric(
            f"llm.optimization.token_reduction.{agent_name}",
            compression_ratio,
            "percent"
        ))
        
        return optimized_prompt, {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "compression_ratio": compression_ratio,
            "cost_savings_percent": cost_savings_percent,
            "estimated_cost_savings": cost_savings
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get LLM optimization performance report."""
        total_optimizations = sum(len(metrics) for metrics in self.optimization_metrics.values())
        
        if total_optimizations == 0:
            return {"message": "No optimization metrics available"}
        
        # Calculate statistics
        all_metrics = []
        for metrics in self.optimization_metrics.values():
            all_metrics.extend(metrics)
        
        total_original_tokens = sum(m.original_tokens for m in all_metrics)
        total_optimized_tokens = sum(m.optimized_tokens for m in all_metrics)
        total_compression = (total_original_tokens - total_optimized_tokens) / total_original_tokens * 100
        
        avg_quality_score = sum(m.response_quality_score for m in all_metrics) / len(all_metrics)
        
        # Agent-specific stats
        agent_stats = {}
        for agent_name, metrics in self.optimization_metrics.items():
            agent_original = sum(m.original_tokens for m in metrics)
            agent_optimized = sum(m.optimized_tokens for m in metrics)
            agent_compression = (agent_original - agent_optimized) / agent_original * 100 if agent_original > 0 else 0
            
            agent_stats[agent_name] = {
                "optimizations_count": len(metrics),
                "total_original_tokens": agent_original,
                "total_optimized_tokens": agent_optimized,
                "compression_ratio": round(agent_compression, 2),
                "avg_quality_score": sum(m.response_quality_score for m in metrics) / len(metrics)
            }
        
        return {
            "summary": {
                "total_optimizations": total_optimizations,
                "total_original_tokens": total_original_tokens,
                "total_optimized_tokens": total_optimized_tokens,
                "overall_compression_ratio": round(total_compression, 2),
                "avg_quality_score": round(avg_quality_score, 2),
                "estimated_total_cost_savings": (total_original_tokens - total_optimized_tokens) * 0.000002
            },
            "agent_stats": agent_stats
        }


class HorizontalScalingManager:
    """
    Horizontal scaling capabilities for agent instances.
    
    Manages dynamic scaling of agent instances based on load.
    """
    
    def __init__(self):
        """Initialize horizontal scaling manager."""
        self.agent_pools: Dict[str, List[Any]] = defaultdict(list)
        self.load_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        self.executor_pool = ThreadPoolExecutor(max_workers=10)
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        self.metrics_collector = get_metrics_collector()
        
        # Default scaling policies
        self.default_scaling_policy = {
            "min_instances": 1,
            "max_instances": 10,
            "target_cpu_percent": 70,
            "scale_up_threshold": 80,
            "scale_down_threshold": 30,
            "cooldown_seconds": 300
        }
    
    def register_agent_type(self, agent_name: str, agent_factory: Callable,
                          scaling_policy: Optional[Dict[str, Any]] = None) -> None:
        """
        Register an agent type for horizontal scaling.
        
        Args:
            agent_name: Name of the agent type
            agent_factory: Factory function to create agent instances
            scaling_policy: Custom scaling policy
        """
        self.scaling_policies[agent_name] = scaling_policy or self.default_scaling_policy.copy()
        
        # Initialize with minimum instances
        min_instances = self.scaling_policies[agent_name]["min_instances"]
        for _ in range(min_instances):
            try:
                agent_instance = agent_factory()
                self.agent_pools[agent_name].append(agent_instance)
            except Exception as e:
                logger.error(f"Failed to create initial agent instance for {agent_name}: {e}")
        
        logger.info(f"Registered agent type {agent_name} with {len(self.agent_pools[agent_name])} instances")
    
    async def get_available_agent(self, agent_name: str) -> Optional[Any]:
        """
        Get an available agent instance from the pool.
        
        Args:
            agent_name: Name of the agent type
            
        Returns:
            Available agent instance or None
        """
        if agent_name not in self.agent_pools:
            logger.error(f"Agent type {agent_name} not registered")
            return None
        
        pool = self.agent_pools[agent_name]
        
        # Find available agent
        for agent in pool:
            if not getattr(agent, 'is_busy', False):
                return agent
        
        # No available agents, check if we can scale up
        if await self._should_scale_up(agent_name):
            new_agent = await self._scale_up(agent_name)
            if new_agent:
                return new_agent
        
        # Return None if no agents available and can't scale
        return None
    
    def return_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Return an agent instance to the pool.
        
        Args:
            agent_name: Name of the agent type
            agent_instance: Agent instance to return
        """
        if hasattr(agent_instance, 'is_busy'):
            agent_instance.is_busy = False
        
        # Record load metrics
        self._record_load_metric(agent_name)
    
    def _record_load_metric(self, agent_name: str) -> None:
        """Record load metrics for scaling decisions."""
        if agent_name not in self.agent_pools:
            return
        
        pool = self.agent_pools[agent_name]
        busy_count = sum(1 for agent in pool if getattr(agent, 'is_busy', False))
        load_percent = (busy_count / len(pool)) * 100 if pool else 0
        
        self.load_metrics[agent_name].append({
            "timestamp": time.time(),
            "load_percent": load_percent,
            "total_instances": len(pool),
            "busy_instances": busy_count
        })
        
        # Record in metrics collector
        asyncio.create_task(self.metrics_collector.record_monitoring_metric(
            f"scaling.{agent_name}.load_percent",
            load_percent,
            "percent"
        ))
    
    async def _should_scale_up(self, agent_name: str) -> bool:
        """Check if agent pool should scale up."""
        if agent_name not in self.scaling_policies:
            return False
        
        policy = self.scaling_policies[agent_name]
        current_instances = len(self.agent_pools[agent_name])
        
        # Check max instances limit
        if current_instances >= policy["max_instances"]:
            return False
        
        # Check load metrics
        recent_metrics = list(self.load_metrics[agent_name])[-10:]  # Last 10 measurements
        if not recent_metrics:
            return False
        
        avg_load = sum(m["load_percent"] for m in recent_metrics) / len(recent_metrics)
        
        return avg_load > policy["scale_up_threshold"]
    
    async def _should_scale_down(self, agent_name: str) -> bool:
        """Check if agent pool should scale down."""
        if agent_name not in self.scaling_policies:
            return False
        
        policy = self.scaling_policies[agent_name]
        current_instances = len(self.agent_pools[agent_name])
        
        # Check min instances limit
        if current_instances <= policy["min_instances"]:
            return False
        
        # Check load metrics
        recent_metrics = list(self.load_metrics[agent_name])[-20:]  # Last 20 measurements
        if not recent_metrics:
            return False
        
        avg_load = sum(m["load_percent"] for m in recent_metrics) / len(recent_metrics)
        
        return avg_load < policy["scale_down_threshold"]
    
    async def _scale_up(self, agent_name: str) -> Optional[Any]:
        """Scale up agent pool by adding new instance."""
        try:
            # This would create a new agent instance
            # For now, we'll simulate it
            logger.info(f"Scaling up {agent_name} agent pool")
            
            # In practice, you would:
            # 1. Create new agent instance
            # 2. Initialize it
            # 3. Add to pool
            
            # Record scaling event
            await self.metrics_collector.record_monitoring_metric(
                f"scaling.{agent_name}.scale_up_events",
                1,
                "count"
            )
            
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Failed to scale up {agent_name}: {e}")
            return None
    
    async def _scale_down(self, agent_name: str) -> bool:
        """Scale down agent pool by removing instance."""
        try:
            pool = self.agent_pools[agent_name]
            
            # Find idle agent to remove
            for i, agent in enumerate(pool):
                if not getattr(agent, 'is_busy', False):
                    # Remove agent
                    removed_agent = pool.pop(i)
                    
                    # Cleanup agent resources
                    if hasattr(removed_agent, 'cleanup'):
                        await removed_agent.cleanup()
                    
                    logger.info(f"Scaled down {agent_name} agent pool")
                    
                    # Record scaling event
                    await self.metrics_collector.record_monitoring_metric(
                        f"scaling.{agent_name}.scale_down_events",
                        1,
                        "count"
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to scale down {agent_name}: {e}")
            return False
    
    async def auto_scale_all(self) -> Dict[str, Any]:
        """Perform auto-scaling for all registered agent types."""
        scaling_actions = {}
        
        for agent_name in self.agent_pools.keys():
            actions = []
            
            # Check for scale up
            if await self._should_scale_up(agent_name):
                new_agent = await self._scale_up(agent_name)
                if new_agent:
                    actions.append("scaled_up")
            
            # Check for scale down
            elif await self._should_scale_down(agent_name):
                if await self._scale_down(agent_name):
                    actions.append("scaled_down")
            
            if not actions:
                actions.append("no_action")
            
            scaling_actions[agent_name] = {
                "actions": actions,
                "current_instances": len(self.agent_pools[agent_name]),
                "current_load": self._get_current_load(agent_name)
            }
        
        return scaling_actions
    
    def _get_current_load(self, agent_name: str) -> float:
        """Get current load percentage for agent type."""
        recent_metrics = list(self.load_metrics[agent_name])[-1:]
        if recent_metrics:
            return recent_metrics[0]["load_percent"]
        return 0.0
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status for all agent types."""
        status = {}
        
        for agent_name, pool in self.agent_pools.items():
            policy = self.scaling_policies.get(agent_name, {})
            recent_metrics = list(self.load_metrics[agent_name])[-5:]
            
            avg_load = 0.0
            if recent_metrics:
                avg_load = sum(m["load_percent"] for m in recent_metrics) / len(recent_metrics)
            
            status[agent_name] = {
                "current_instances": len(pool),
                "min_instances": policy.get("min_instances", 1),
                "max_instances": policy.get("max_instances", 10),
                "current_load_percent": round(avg_load, 2),
                "busy_instances": sum(1 for agent in pool if getattr(agent, 'is_busy', False)),
                "scaling_policy": policy
            }
        
        return status


class PerformanceOptimizer:
    """
    Main performance optimization service that coordinates all optimization components.
    """
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.db_optimizer = DatabaseQueryOptimizer()
        self.cache_manager = AdvancedCacheManager()
        self.llm_optimizer = LLMPromptOptimizer()
        self.scaling_manager = HorizontalScalingManager()
        self.metrics_collector = get_metrics_collector()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
    
    async def start_optimization_services(self) -> None:
        """Start all optimization background services."""
        # Start cache prefetch worker
        prefetch_task = asyncio.create_task(self.cache_manager.start_prefetch_worker())
        self._background_tasks.append(prefetch_task)
        
        # Start auto-scaling worker
        scaling_task = asyncio.create_task(self._auto_scaling_worker())
        self._background_tasks.append(scaling_task)
        
        logger.info("Performance optimization services started")
    
    async def stop_optimization_services(self) -> None:
        """Stop all optimization background services."""
        for task in self._background_tasks:
            task.cancel()
        
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        logger.info("Performance optimization services stopped")
    
    async def _auto_scaling_worker(self) -> None:
        """Background worker for auto-scaling."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.scaling_manager.auto_scale_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-scaling worker: {e}")
    
    async def get_comprehensive_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report from all optimization components."""
        try:
            # Get reports from all components
            db_report = await self.db_optimizer.get_query_performance_report()
            cache_report = await self.cache_manager.get_cache_performance_report()
            llm_report = self.llm_optimizer.get_optimization_report()
            scaling_status = self.scaling_manager.get_scaling_status()
            
            # System resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system_resources": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": (disk.used / disk.total) * 100,
                    "available_memory_gb": round(memory.available / (1024**3), 2)
                },
                "database_performance": db_report,
                "cache_performance": cache_report,
                "llm_optimization": llm_report,
                "scaling_status": scaling_status,
                "optimization_recommendations": await self._generate_optimization_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}
    
    async def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on current metrics."""
        recommendations = []
        
        # System resource recommendations
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80:
            recommendations.append({
                "category": "system_resources",
                "priority": "high",
                "issue": "High CPU usage",
                "recommendation": "Consider scaling up compute resources or optimizing CPU-intensive operations",
                "current_value": cpu_percent,
                "threshold": 80
            })
        
        if memory_percent > 85:
            recommendations.append({
                "category": "system_resources",
                "priority": "high",
                "issue": "High memory usage",
                "recommendation": "Consider increasing memory allocation or optimizing memory usage",
                "current_value": memory_percent,
                "threshold": 85
            })
        
        # Database recommendations
        db_report = await self.db_optimizer.get_query_performance_report()
        if isinstance(db_report, dict) and "summary" in db_report:
            slow_query_rate = db_report["summary"].get("slow_query_rate", 0)
            if slow_query_rate > 10:
                recommendations.append({
                    "category": "database",
                    "priority": "medium",
                    "issue": "High slow query rate",
                    "recommendation": "Review and optimize slow database queries, consider adding indexes",
                    "current_value": slow_query_rate,
                    "threshold": 10
                })
        
        # Cache recommendations
        cache_report = await self.cache_manager.get_cache_performance_report()
        if isinstance(cache_report, dict) and "summary" in cache_report:
            hit_rate = cache_report["summary"].get("hit_rate_percent", 0)
            if hit_rate < 70:
                recommendations.append({
                    "category": "cache",
                    "priority": "medium",
                    "issue": "Low cache hit rate",
                    "recommendation": "Review caching strategy and consider warming cache with frequently accessed data",
                    "current_value": hit_rate,
                    "threshold": 70
                })
        
        return recommendations


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()