"""
Database Query Optimization and Batching System.

Solves the N+1 query problem by batching database queries and implementing
smart data loading strategies.

Features:
- Automatic query batching (DataLoader pattern)
- Relationship preloading (eager loading)
- Query result caching
- Performance monitoring
- Batch size optimization

Problem Solved:
```python
# BEFORE - N+1 Query Problem L
assessments = await Assessment.find_all().to_list()  # 1 query
for assessment in assessments:
    user = await User.get(assessment.user_id)  # N queries!
    recommendations = await Recommendation.find(
        Recommendation.assessment_id == assessment.id
    ).to_list()  # N more queries!
# Total: 1 + N + N = 2N+1 queries

# AFTER - Batched Queries 
assessments = await load_assessments_with_relations(
    include=['user', 'recommendations']
)  # Total: 3 queries (assessments, users batch, recommendations batch)
```

Usage:
```python
from infra_mind.core.query_optimizer import (
    batch_loader,
    preload_relations,
    QueryBatcher
)

# Use batch loader for single items
user_loader = batch_loader(User, key_field="id")
user = await user_loader.load(user_id)

# Preload relationships
assessments = await preload_relations(
    Assessment.find_all(),
    relations={
        'user': (User, 'user_id'),
        'recommendations': (Recommendation, 'assessment_id', 'many')
    }
)
```
"""

import asyncio
from typing import (
    Dict,
    List,
    Optional,
    Any,
    Callable,
    TypeVar,
    Generic,
    Set,
    Tuple
)
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import time
from loguru import logger


T = TypeVar('T')


@dataclass
class BatchMetrics:
    """Metrics for query batching performance."""
    total_batches: int = 0
    total_items_loaded: int = 0
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_batch_size: float = 0.0
    total_time_seconds: float = 0.0
    queries_saved: int = 0  # N+1 queries prevented

    def record_batch(self, batch_size: int, execution_time: float, cached: int = 0):
        """Record batch execution metrics."""
        self.total_batches += 1
        self.total_items_loaded += batch_size
        self.total_queries += 1
        self.cache_hits += cached
        self.cache_misses += (batch_size - cached)
        self.total_time_seconds += execution_time

        # Calculate average batch size
        self.average_batch_size = self.total_items_loaded / self.total_batches

        # Estimate queries saved (N+1 problem)
        self.queries_saved = self.total_items_loaded - self.total_queries

    def get_stats(self) -> Dict[str, Any]:
        """Get batch metrics statistics."""
        return {
            "total_batches": self.total_batches,
            "total_items_loaded": self.total_items_loaded,
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "average_batch_size": round(self.average_batch_size, 2),
            "total_time_seconds": round(self.total_time_seconds, 3),
            "queries_saved": self.queries_saved,
            "efficiency_ratio": round(
                self.total_items_loaded / self.total_queries
                if self.total_queries > 0 else 0,
                2
            )
        }


class DataLoader(Generic[T]):
    """
    DataLoader pattern implementation for batching database queries.

    Collects multiple load requests and executes them in a single batch,
    solving the N+1 query problem.
    """

    def __init__(
        self,
        batch_load_fn: Callable[[List[Any]], List[T]],
        max_batch_size: int = 100,
        cache: bool = True,
    ):
        """
        Initialize DataLoader.

        Args:
            batch_load_fn: Async function that loads items in batch
            max_batch_size: Maximum items per batch
            cache: Enable caching of loaded items
        """
        self.batch_load_fn = batch_load_fn
        self.max_batch_size = max_batch_size
        self.cache_enabled = cache

        # Batching state
        self._queue: List[Tuple[Any, asyncio.Future]] = []
        self._cache: Dict[Any, T] = {}
        self._batch_scheduled = False
        self.metrics = BatchMetrics()

    async def load(self, key: Any) -> Optional[T]:
        """
        Load a single item by key.

        Args:
            key: Item key (e.g., user ID)

        Returns:
            Loaded item or None
        """
        # Check cache first
        if self.cache_enabled and key in self._cache:
            self.metrics.cache_hits += 1
            return self._cache[key]

        # Create future for this load request
        future = asyncio.Future()
        self._queue.append((key, future))

        # Schedule batch if not already scheduled
        if not self._batch_scheduled:
            self._batch_scheduled = True
            asyncio.create_task(self._dispatch_batch())

        # Wait for result
        return await future

    async def load_many(self, keys: List[Any]) -> List[Optional[T]]:
        """
        Load multiple items by keys.

        Args:
            keys: List of item keys

        Returns:
            List of loaded items (None for missing items)
        """
        # Load concurrently
        results = await asyncio.gather(*[self.load(key) for key in keys])
        return list(results)

    async def _dispatch_batch(self):
        """Execute batched queries."""
        # Small delay to collect more requests
        await asyncio.sleep(0.001)  # 1ms window for batching

        self._batch_scheduled = False

        if not self._queue:
            return

        # Get current batch (up to max_batch_size)
        batch = self._queue[:self.max_batch_size]
        self._queue = self._queue[self.max_batch_size:]

        # Schedule next batch if queue not empty
        if self._queue:
            self._batch_scheduled = True
            asyncio.create_task(self._dispatch_batch())

        # Extract keys and futures
        keys = [item[0] for item in batch]
        futures = [item[1] for item in batch]

        try:
            # Execute batch query
            start_time = time.time()
            results = await self.batch_load_fn(keys)
            execution_time = time.time() - start_time

            # Create result map
            result_map = {
                getattr(item, 'id', None) or key: item
                for key, item in zip(keys, results)
            }

            # Cache results
            cached_count = 0
            if self.cache_enabled:
                for key, result in result_map.items():
                    if result is not None:
                        self._cache[key] = result
                        cached_count += 1

            # Resolve futures
            for key, future in batch:
                result = result_map.get(key)
                if not future.done():
                    future.set_result(result)

            # Record metrics
            self.metrics.record_batch(
                batch_size=len(keys),
                execution_time=execution_time,
                cached=cached_count
            )

            logger.debug(
                f"Batch loaded {len(keys)} items in {execution_time*1000:.1f}ms "
                f"(cached: {cached_count})"
            )

        except Exception as e:
            logger.error(f"Batch load error: {e}")
            # Reject all futures
            for _, future in batch:
                if not future.done():
                    future.set_exception(e)

    def clear_cache(self):
        """Clear the DataLoader cache."""
        self._cache.clear()
        logger.debug("DataLoader cache cleared")

    def get_metrics(self) -> Dict[str, Any]:
        """Get batching metrics."""
        return self.metrics.get_stats()


class QueryBatcher:
    """
    Manages multiple DataLoaders for different model types.

    Provides a centralized way to batch queries across the application.
    """

    def __init__(self):
        """Initialize query batcher."""
        self.loaders: Dict[str, DataLoader] = {}
        self.metrics = BatchMetrics()

    def create_loader(
        self,
        name: str,
        batch_load_fn: Callable,
        max_batch_size: int = 100,
        cache: bool = True,
    ) -> DataLoader:
        """
        Create or get a DataLoader.

        Args:
            name: Loader name (e.g., "user", "assessment")
            batch_load_fn: Batch loading function
            max_batch_size: Maximum batch size
            cache: Enable caching

        Returns:
            DataLoader instance
        """
        if name not in self.loaders:
            self.loaders[name] = DataLoader(
                batch_load_fn=batch_load_fn,
                max_batch_size=max_batch_size,
                cache=cache,
            )
            logger.info(f"Created DataLoader: {name}")

        return self.loaders[name]

    def get_loader(self, name: str) -> Optional[DataLoader]:
        """Get DataLoader by name."""
        return self.loaders.get(name)

    def clear_all_caches(self):
        """Clear all DataLoader caches."""
        for loader in self.loaders.values():
            loader.clear_cache()
        logger.info("Cleared all DataLoader caches")

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all loaders."""
        return {
            name: loader.get_metrics()
            for name, loader in self.loaders.items()
        }


# Global query batcher instance
query_batcher = QueryBatcher()


def batch_loader(
    model_class: Any,
    key_field: str = "id",
    max_batch_size: int = 100,
    cache: bool = True,
) -> DataLoader:
    """
    Create a batch loader for a model class.

    Args:
        model_class: Model class (e.g., User, Assessment)
        key_field: Field to use as key
        max_batch_size: Maximum batch size
        cache: Enable caching

    Returns:
        DataLoader instance

    Usage:
        user_loader = batch_loader(User, key_field="id")
        user = await user_loader.load(user_id)
    """
    async def batch_load_fn(keys: List[Any]) -> List[Any]:
        """Batch load function for model."""
        # Query all items with keys
        items = await model_class.find(
            getattr(model_class, key_field).in_(keys)
        ).to_list()

        # Create map for fast lookup
        item_map = {getattr(item, key_field): item for item in items}

        # Return in same order as keys
        return [item_map.get(key) for key in keys]

    loader_name = f"{model_class.__name__}_{key_field}"
    return query_batcher.create_loader(
        name=loader_name,
        batch_load_fn=batch_load_fn,
        max_batch_size=max_batch_size,
        cache=cache,
    )


async def preload_relations(
    query_result: Any,
    relations: Dict[str, Tuple[Any, str, str]],
) -> List[Any]:
    """
    Preload relationships to avoid N+1 queries.

    Args:
        query_result: Beanie query result
        relations: Dict of {attr_name: (Model, foreign_key, relation_type)}
            relation_type: 'one' (default) or 'many'

    Returns:
        List of items with preloaded relationships

    Usage:
        assessments = await preload_relations(
            Assessment.find_all(),
            relations={
                'user': (User, 'user_id', 'one'),
                'recommendations': (Recommendation, 'assessment_id', 'many')
            }
        )

        # Now you can access without additional queries:
        for assessment in assessments:
            print(assessment.user.name)  # No query!
            print(len(assessment.recommendations))  # No query!
    """
    start_time = time.time()

    # Get all items
    items = await query_result.to_list() if hasattr(query_result, 'to_list') else query_result

    if not items:
        return []

    # Preload each relation
    for attr_name, (model_class, foreign_key, *relation_type) in relations.items():
        relation_type = relation_type[0] if relation_type else 'one'

        if relation_type == 'one':
            # One-to-one or many-to-one relationship
            # Collect all foreign key values
            foreign_keys = [
                getattr(item, foreign_key)
                for item in items
                if hasattr(item, foreign_key) and getattr(item, foreign_key)
            ]

            if not foreign_keys:
                continue

            # Batch load related items
            related_items = await model_class.find(
                model_class.id.in_(foreign_keys)
            ).to_list()

            # Create lookup map
            related_map = {str(item.id): item for item in related_items}

            # Attach to items
            for item in items:
                fk_value = getattr(item, foreign_key, None)
                if fk_value:
                    setattr(item, attr_name, related_map.get(str(fk_value)))

        elif relation_type == 'many':
            # One-to-many relationship
            # Collect all IDs
            item_ids = [str(item.id) for item in items]

            # Batch load related items
            related_items = await model_class.find(
                getattr(model_class, foreign_key).in_(item_ids)
            ).to_list()

            # Group by foreign key
            related_groups = defaultdict(list)
            for related_item in related_items:
                fk_value = getattr(related_item, foreign_key)
                related_groups[str(fk_value)].append(related_item)

            # Attach to items
            for item in items:
                setattr(item, attr_name, related_groups.get(str(item.id), []))

    execution_time = time.time() - start_time
    logger.info(
        f"Preloaded {len(relations)} relations for {len(items)} items "
        f"in {execution_time*1000:.1f}ms"
    )

    return items


async def get_batching_stats() -> Dict[str, Any]:
    """Get query batching statistics."""
    return query_batcher.get_all_metrics()


# Example usage:
"""
# === Example 1: Basic DataLoader ===

from infra_mind.models.user import User
from infra_mind.core.query_optimizer import batch_loader

# Create loader
user_loader = batch_loader(User, key_field="id")

# Load users (batched automatically)
users = await asyncio.gather(
    user_loader.load(user_id_1),
    user_loader.load(user_id_2),
    user_loader.load(user_id_3),
)
# Only 1 query executed instead of 3!


# === Example 2: Preloading Relations ===

from infra_mind.models.assessment import Assessment
from infra_mind.models.user import User
from infra_mind.models.recommendation import Recommendation
from infra_mind.core.query_optimizer import preload_relations

# Load assessments with related data
assessments = await preload_relations(
    Assessment.find_all(),
    relations={
        'user': (User, 'user_id', 'one'),
        'recommendations': (Recommendation, 'assessment_id', 'many')
    }
)

# Access without N+1 queries
for assessment in assessments:
    print(f"Assessment by {assessment.user.name}")
    print(f"Has {len(assessment.recommendations)} recommendations")
# Total: 3 queries instead of 1 + N + N


# === Example 3: API Endpoint Optimization ===

from fastapi import APIRouter
from infra_mind.core.query_optimizer import preload_relations

router = APIRouter()

@router.get("/api/assessments")
async def list_assessments():
    # BEFORE: N+1 query problem
    # assessments = await Assessment.find_all().to_list()
    # for a in assessments:
    #     a.user = await User.get(a.user_id)  # N queries!

    # AFTER: Optimized with batching
    assessments = await preload_relations(
        Assessment.find_all(),
        relations={'user': (User, 'user_id')}
    )

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "user": {
                "id": str(a.user.id),
                "name": a.user.full_name
            } if a.user else None
        }
        for a in assessments
    ]


# === Example 4: Get Metrics ===

from infra_mind.core.query_optimizer import get_batching_stats

stats = await get_batching_stats()
# {
#     "User_id": {
#         "total_batches": 10,
#         "total_items_loaded": 150,
#         "queries_saved": 140,
#         "efficiency_ratio": 15.0
#     }
# }
"""
