"""
Optimized database query patterns for high-performance operations.
Provides cached, indexed, and batched query methods.
"""

from typing import List, Dict, Any, Optional, Union
from beanie import Document, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from functools import wraps
from ..models.assessment import Assessment
from ..models.user import User  
from ..models.experiment import Experiment, ExperimentEvent
from ..models.feedback import UserFeedback, QualityMetric
from ..models.recommendation import Recommendation
from ..models.report import Report


class OptimizedQueryCache:
    """Simple in-memory cache for frequently accessed data."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.utcnow() - timestamp > timedelta(seconds=self.ttl)
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, datetime.utcnow())
    
    def clear(self) -> None:
        self.cache.clear()


# Global cache instance
query_cache = OptimizedQueryCache()


def cache_result(ttl_seconds: int = 300):
    """Decorator to cache query results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            query_cache.set(cache_key, result)
            logger.debug(f"Cache miss, stored result for {func.__name__}")
            return result
        
        return wrapper
    return decorator


class OptimizedAssessmentQueries:
    """Optimized queries for Assessment operations."""
    
    @staticmethod
    @cache_result(ttl_seconds=60)
    async def get_user_assessments_paginated(
        user_id: str, 
        page: int = 1, 
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user assessments with optimized pagination."""
        skip = (page - 1) * limit
        
        # Build optimized query
        query = {"user_id": user_id}
        if status_filter:
            query["status"] = status_filter
        
        # Use projection to only fetch needed fields
        projection = {
            "name": 1,
            "description": 1, 
            "status": 1,
            "completion_percentage": 1,
            "created_at": 1,
            "updated_at": 1,
            "priority": 1,
            "cloud_provider": 1
        }
        
        # Execute optimized queries in parallel
        total_task = Assessment.find(query).count()
        assessments_task = Assessment.find(
            query, 
            projection=projection
        ).sort([("updated_at", -1)]).skip(skip).limit(limit).to_list()
        
        total, assessments = await asyncio.gather(total_task, assessments_task)
        
        return {
            "assessments": assessments,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    @cache_result(ttl_seconds=300)
    async def get_assessment_analytics(user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get optimized assessment analytics."""
        match_stage = {}
        if user_id:
            match_stage["user_id"] = user_id
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_completion": {"$avg": "$completion_percentage"},
                "latest_update": {"$max": "$updated_at"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        result = await Assessment.aggregate(pipeline).to_list()
        
        # Transform to more usable format
        analytics = {
            "total_assessments": sum(item["count"] for item in result),
            "by_status": {item["_id"]: item for item in result},
            "completion_stats": {
                "average": sum(item["avg_completion"] or 0 for item in result) / len(result) if result else 0
            }
        }
        
        return analytics
    
    @staticmethod
    async def batch_update_assessments(
        assessment_ids: List[str], 
        update_data: Dict[str, Any]
    ) -> int:
        """Batch update multiple assessments efficiently."""
        object_ids = [PydanticObjectId(aid) for aid in assessment_ids]
        
        result = await Assessment.find(
            {"_id": {"$in": object_ids}}
        ).update_many({"$set": update_data})
        
        # Clear related cache
        query_cache.clear()
        
        return result.modified_count


class OptimizedExperimentQueries:
    """Optimized queries for A/B testing operations."""
    
    @staticmethod
    @cache_result(ttl_seconds=30)  # Short cache for real-time experiments
    async def get_active_experiment(feature_flag: str) -> Optional[Dict[str, Any]]:
        """Get active experiment for feature flag with minimal latency."""
        projection = {
            "name": 1,
            "feature_flag": 1,
            "status": 1,
            "variants": 1,
            "target_metric": 1,
            "created_at": 1
        }
        
        experiment = await Experiment.find_one(
            {
                "feature_flag": feature_flag,
                "status": "running"
            },
            projection=projection
        )
        
        return experiment.dict() if experiment else None
    
    @staticmethod
    async def batch_track_events(events: List[Dict[str, Any]]) -> int:
        """Batch insert experiment events for better performance."""
        if not events:
            return 0
        
        # Prepare event documents
        event_docs = []
        for event_data in events:
            event = ExperimentEvent(
                experiment_id=event_data["experiment_id"],
                feature_flag=event_data["feature_flag"],
                user_id=event_data["user_id"],
                variant_name=event_data.get("variant_name"),
                event_type=event_data.get("event_type", "conversion"),
                event_value=event_data.get("event_value"),
                custom_metrics=event_data.get("custom_metrics", {}),
                user_attributes=event_data.get("user_attributes", {}),
                session_id=event_data.get("session_id")
            )
            event_docs.append(event)
        
        # Batch insert
        await ExperimentEvent.insert_many(event_docs)
        
        return len(event_docs)
    
    @staticmethod
    @cache_result(ttl_seconds=60)
    async def get_experiment_performance(experiment_id: str) -> Dict[str, Any]:
        """Get experiment performance metrics with aggregation."""
        pipeline = [
            {"$match": {"experiment_id": experiment_id}},
            {"$group": {
                "_id": "$variant_name",
                "total_events": {"$sum": 1},
                "conversions": {
                    "$sum": {"$cond": [{"$eq": ["$event_type", "conversion"]}, 1, 0]}
                },
                "avg_value": {"$avg": "$event_value"},
                "unique_users": {"$addToSet": "$user_id"}
            }},
            {"$addFields": {
                "conversion_rate": {
                    "$divide": ["$conversions", "$total_events"]
                },
                "unique_user_count": {"$size": "$unique_users"}
            }},
            {"$project": {
                "unique_users": 0  # Remove the array to save memory
            }}
        ]
        
        results = await ExperimentEvent.aggregate(pipeline).to_list()
        
        return {
            "variants": results,
            "calculated_at": datetime.utcnow()
        }


class OptimizedFeedbackQueries:
    """Optimized queries for feedback operations."""
    
    @staticmethod
    @cache_result(ttl_seconds=120)
    async def get_feedback_analytics(
        days: int = 30,
        feedback_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive feedback analytics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        match_stage = {"created_at": {"$gte": start_date}}
        if feedback_type:
            match_stage["feedback_type"] = feedback_type
        
        pipeline = [
            {"$match": match_stage},
            {"$facet": {
                "by_type": [
                    {"$group": {
                        "_id": "$feedback_type",
                        "count": {"$sum": 1},
                        "avg_rating": {"$avg": "$rating"}
                    }}
                ],
                "by_channel": [
                    {"$group": {
                        "_id": "$channel", 
                        "count": {"$sum": 1}
                    }}
                ],
                "by_sentiment": [
                    {"$group": {
                        "_id": "$sentiment",
                        "count": {"$sum": 1}
                    }}
                ],
                "rating_distribution": [
                    {"$match": {"rating": {"$exists": True}}},
                    {"$group": {
                        "_id": "$rating",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"_id": 1}}
                ]
            }}
        ]
        
        result = await UserFeedback.aggregate(pipeline).to_list()
        
        if result:
            analytics = result[0]
            analytics["period_days"] = days
            analytics["generated_at"] = datetime.utcnow()
            return analytics
        
        return {"error": "No data found"}
    
    @staticmethod
    async def get_recent_feedback_stream(
        limit: int = 50,
        feedback_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent feedback with minimal fields for real-time display."""
        query = {}
        if feedback_type:
            query["feedback_type"] = feedback_type
        
        projection = {
            "feedback_type": 1,
            "rating": 1,
            "sentiment": 1,
            "created_at": 1,
            "channel": 1,
            "user_id": 1
        }
        
        feedback = await UserFeedback.find(
            query,
            projection=projection
        ).sort([("created_at", -1)]).limit(limit).to_list()
        
        return feedback


class OptimizedQualityQueries:
    """Optimized queries for quality metrics."""
    
    @staticmethod
    @cache_result(ttl_seconds=180)
    async def get_quality_overview(target_type: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive quality metrics overview."""
        match_stage = {}
        if target_type:
            match_stage["target_type"] = target_type
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": {
                    "target_type": "$target_type",
                    "metric_name": "$metric_name"
                },
                "avg_score": {"$avg": "$quality_score"},
                "min_score": {"$min": "$quality_score"},
                "max_score": {"$max": "$quality_score"},
                "count": {"$sum": 1},
                "latest_update": {"$max": "$created_at"}
            }},
            {"$group": {
                "_id": "$_id.target_type",
                "metrics": {
                    "$push": {
                        "metric_name": "$_id.metric_name",
                        "avg_score": "$avg_score",
                        "min_score": "$min_score", 
                        "max_score": "$max_score",
                        "count": "$count",
                        "latest_update": "$latest_update"
                    }
                }
            }}
        ]
        
        results = await QualityMetric.aggregate(pipeline).to_list()
        
        overview = {
            "by_target_type": {item["_id"]: item["metrics"] for item in results},
            "generated_at": datetime.utcnow()
        }
        
        return overview


class OptimizedRecommendationQueries:
    """Optimized queries for recommendations."""
    
    @staticmethod
    @cache_result(ttl_seconds=240)
    async def get_assessment_recommendations(
        assessment_id: str,
        priority_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations for an assessment with optimized query."""
        query = {"assessment_id": assessment_id}
        if priority_filter:
            query["priority"] = priority_filter
        
        projection = {
            "title": 1,
            "description": 1,
            "priority": 1,
            "category": 1,
            "confidence": 1,
            "estimated_impact": 1,
            "implementation_effort": 1,
            "created_at": 1
        }
        
        recommendations = await Recommendation.find(
            query,
            projection=projection
        ).sort([("priority", 1), ("confidence", -1)]).to_list()
        
        return recommendations


# Helper functions for batch operations
async def batch_operation_with_progress(
    items: List[Any],
    operation_func,
    batch_size: int = 100,
    progress_callback: Optional[callable] = None
) -> List[Any]:
    """Execute batch operations with progress tracking."""
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await operation_func(batch)
        results.extend(batch_results)
        
        if progress_callback:
            current_batch = (i // batch_size) + 1
            progress_callback(current_batch, total_batches)
        
        # Small delay to prevent overwhelming the database
        await asyncio.sleep(0.01)
    
    return results


# Export the main query classes
__all__ = [
    "OptimizedAssessmentQueries",
    "OptimizedExperimentQueries", 
    "OptimizedFeedbackQueries",
    "OptimizedQualityQueries",
    "OptimizedRecommendationQueries",
    "batch_operation_with_progress",
    "query_cache"
]