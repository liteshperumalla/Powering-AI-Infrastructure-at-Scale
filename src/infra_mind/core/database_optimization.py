"""
Database optimization utilities for production scale.
Handles indexing, query optimization, and performance monitoring.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from loguru import logger
from datetime import datetime, timedelta
import asyncio
from beanie import Document
from ..models.assessment import Assessment
from ..models.user import User
from ..models.experiment import Experiment, ExperimentEvent
from ..models.feedback import UserFeedback, QualityMetric


class DatabaseOptimizer:
    """Handles database optimization tasks for production scale."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.optimization_log = []
    
    async def create_production_indexes(self) -> Dict[str, List[str]]:
        """Create optimized indexes for production workloads."""
        logger.info("Creating production database indexes...")
        
        created_indexes = {}
        
        try:
            # Assessment indexes for high-performance queries
            assessment_indexes = [
                # Primary queries
                IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)]),  # Latest assessments
                IndexModel([("updated_at", DESCENDING)]),  # Recent updates
                IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),  # Status filtering
                
                # Search and filtering
                IndexModel([("name", TEXT), ("description", TEXT)]),  # Text search
                IndexModel([("cloud_provider", ASCENDING), ("status", ASCENDING)]),
                IndexModel([("priority", ASCENDING), ("created_at", DESCENDING)]),
                
                # Performance optimization
                IndexModel([("user_id", ASCENDING), ("updated_at", DESCENDING)]),  # User's recent
                IndexModel([("completion_percentage", ASCENDING)]),  # Progress tracking
                
                # Compound indexes for complex queries
                IndexModel([
                    ("user_id", ASCENDING), 
                    ("status", ASCENDING),
                    ("created_at", DESCENDING)
                ])
            ]
            
            await self.database.assessments.create_indexes(assessment_indexes)
            created_indexes["assessments"] = [str(idx.document) for idx in assessment_indexes]
            
            # User indexes for authentication and access control
            user_indexes = [
                IndexModel([("email", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("is_active", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("role", ASCENDING)]),
                IndexModel([("company", ASCENDING), ("role", ASCENDING)])
            ]
            
            await self.database.users.create_indexes(user_indexes)
            created_indexes["users"] = [str(idx.document) for idx in user_indexes]
            
            # Experiment indexes for A/B testing performance
            experiment_indexes = [
                IndexModel([("feature_flag", ASCENDING)]),
                IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("created_by", ASCENDING), ("status", ASCENDING)])
            ]
            
            await self.database.experiments.create_indexes(experiment_indexes)
            created_indexes["experiments"] = [str(idx.document) for idx in experiment_indexes]
            
            # Experiment event indexes for analytics
            experiment_event_indexes = [
                IndexModel([("experiment_id", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("feature_flag", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("event_type", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("variant_name", ASCENDING), ("event_type", ASCENDING)])
            ]
            
            await self.database.experiment_events.create_indexes(experiment_event_indexes)
            created_indexes["experiment_events"] = [str(idx.document) for idx in experiment_event_indexes]
            
            # Feedback indexes for analytics and reporting
            feedback_indexes = [
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("feedback_type", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("channel", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("rating", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("sentiment", ASCENDING)]),
                IndexModel([("processed", ASCENDING), ("created_at", ASCENDING)])
            ]
            
            await self.database.user_feedback.create_indexes(feedback_indexes)
            created_indexes["user_feedback"] = [str(idx.document) for idx in feedback_indexes]
            
            # Quality metrics indexes
            quality_indexes = [
                IndexModel([("target_type", ASCENDING), ("target_id", ASCENDING)]),
                IndexModel([("metric_name", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("quality_score", DESCENDING), ("created_at", DESCENDING)])
            ]
            
            await self.database.quality_metrics.create_indexes(quality_indexes)
            created_indexes["quality_metrics"] = [str(idx.document) for idx in quality_indexes]
            
            # Recommendation indexes
            recommendation_indexes = [
                IndexModel([("assessment_id", ASCENDING), ("priority", DESCENDING)]),
                IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("category", ASCENDING), ("confidence", DESCENDING)])
            ]
            
            await self.database.recommendations.create_indexes(recommendation_indexes)
            created_indexes["recommendations"] = [str(idx.document) for idx in recommendation_indexes]
            
            # Report indexes
            report_indexes = [
                IndexModel([("assessment_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("type", ASCENDING), ("status", ASCENDING)]),
                IndexModel([("created_by", ASCENDING), ("created_at", DESCENDING)])
            ]
            
            await self.database.reports.create_indexes(report_indexes)
            created_indexes["reports"] = [str(idx.document) for idx in report_indexes]
            
            logger.success(f"Created indexes for {len(created_indexes)} collections")
            self.optimization_log.append({
                "timestamp": datetime.utcnow(),
                "action": "create_indexes",
                "collections": list(created_indexes.keys()),
                "status": "success"
            })
            
            return created_indexes
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            self.optimization_log.append({
                "timestamp": datetime.utcnow(),
                "action": "create_indexes",
                "status": "error",
                "error": str(e)
            })
            raise
    
    async def analyze_slow_queries(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Analyze slow queries from the database profiler."""
        try:
            # Enable profiling for slow operations (>100ms)
            await self.database.command("profile", 2, slowms=100)
            
            # Get profiling data
            profile_data = await self.database.system.profile.find({
                "ts": {"$gte": datetime.utcnow() - timedelta(minutes=duration_minutes)}
            }).sort("duration", -1).to_list(length=100)
            
            analysis = {
                "total_slow_queries": len(profile_data),
                "slowest_operations": [],
                "collections_affected": set(),
                "optimization_suggestions": []
            }
            
            for op in profile_data[:10]:  # Top 10 slowest
                analysis["slowest_operations"].append({
                    "namespace": op.get("ns", "unknown"),
                    "operation": op.get("op", "unknown"),
                    "duration_ms": op.get("duration", 0),
                    "timestamp": op.get("ts"),
                    "command": op.get("command", {})
                })
                
                if "ns" in op:
                    collection = op["ns"].split(".")[-1]
                    analysis["collections_affected"].add(collection)
            
            # Generate optimization suggestions
            for collection in analysis["collections_affected"]:
                analysis["optimization_suggestions"].append(
                    f"Consider adding indexes for frequent queries on {collection}"
                )
            
            logger.info(f"Analyzed {len(profile_data)} slow queries")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {str(e)}")
            return {"error": str(e)}
    
    async def optimize_aggregation_pipelines(self) -> Dict[str, Any]:
        """Optimize common aggregation pipelines used in the application."""
        optimizations = {}
        
        try:
            # Assessment analytics pipeline optimization
            assessment_pipeline = [
                # Use $match early to filter documents
                {"$match": {"status": {"$in": ["completed", "in_progress"]}}},
                
                # Add indexes hint for better performance
                {"$addFields": {"user_id_obj": {"$toObjectId": "$user_id"}}},
                
                # Efficient grouping
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_completion": {"$avg": "$completion_percentage"},
                    "latest_update": {"$max": "$updated_at"}
                }},
                
                # Sort by count descending
                {"$sort": {"count": -1}}
            ]
            
            optimizations["assessment_analytics"] = {
                "pipeline": assessment_pipeline,
                "indexes_used": ["status_1", "updated_at_-1"],
                "estimated_docs": "filtered early"
            }
            
            # User engagement pipeline
            user_engagement_pipeline = [
                {"$match": {"is_active": True}},
                {"$lookup": {
                    "from": "assessments",
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "assessments",
                    "pipeline": [
                        {"$match": {"created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}}},
                        {"$project": {"_id": 1, "status": 1, "created_at": 1}}
                    ]
                }},
                {"$addFields": {
                    "recent_assessments": {"$size": "$assessments"},
                    "completed_assessments": {
                        "$size": {"$filter": {
                            "input": "$assessments",
                            "cond": {"$eq": ["$$this.status", "completed"]}
                        }}
                    }
                }},
                {"$match": {"recent_assessments": {"$gt": 0}}},
                {"$project": {
                    "email": 1,
                    "company": 1,
                    "recent_assessments": 1,
                    "completed_assessments": 1,
                    "engagement_score": {
                        "$multiply": [
                            {"$divide": ["$completed_assessments", "$recent_assessments"]},
                            100
                        ]
                    }
                }},
                {"$sort": {"engagement_score": -1}}
            ]
            
            optimizations["user_engagement"] = {
                "pipeline": user_engagement_pipeline,
                "indexes_used": ["is_active_1_created_at_-1", "user_id_1_created_at_-1"],
                "optimization": "Uses efficient $lookup with pipeline"
            }
            
            logger.success("Created optimized aggregation pipelines")
            return optimizations
            
        except Exception as e:
            logger.error(f"Failed to optimize aggregation pipelines: {str(e)}")
            return {"error": str(e)}
    
    async def setup_query_optimization_hints(self) -> Dict[str, Any]:
        """Set up query optimization hints and best practices."""
        hints = {
            "assessment_queries": {
                "list_user_assessments": {
                    "hint": {"user_id": 1, "created_at": -1},
                    "projection": {"name": 1, "status": 1, "created_at": 1, "completion_percentage": 1}
                },
                "search_assessments": {
                    "hint": {"$text": {"$search": "query_text"}},
                    "projection": {"name": 1, "description": 1, "score": {"$meta": "textScore"}}
                }
            },
            "experiment_queries": {
                "active_experiments": {
                    "hint": {"feature_flag": 1},
                    "filter": {"status": "running"}
                },
                "user_variants": {
                    "hint": {"feature_flag": 1, "status": 1},
                    "cache_key": "experiment_variants_{feature_flag}"
                }
            },
            "feedback_queries": {
                "recent_feedback": {
                    "hint": {"created_at": -1},
                    "limit": 50,
                    "projection": {"feedback_type": 1, "rating": 1, "created_at": 1}
                },
                "feedback_analytics": {
                    "hint": {"feedback_type": 1, "created_at": -1},
                    "cache_key": "feedback_analytics_{date_range}"
                }
            }
        }
        
        return hints
    
    async def get_collection_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about collection sizes and performance."""
        stats = {}
        
        collections = [
            "assessments", "users", "experiments", "experiment_events",
            "user_feedback", "quality_metrics", "recommendations", "reports"
        ]
        
        for collection_name in collections:
            try:
                collection = self.database[collection_name]
                
                # Get collection stats
                collection_stats = await self.database.command("collStats", collection_name)
                
                # Get index information
                indexes = await collection.index_information()
                
                stats[collection_name] = {
                    "document_count": collection_stats.get("count", 0),
                    "size_bytes": collection_stats.get("size", 0),
                    "avg_document_size": collection_stats.get("avgObjSize", 0),
                    "storage_size": collection_stats.get("storageSize", 0),
                    "index_count": len(indexes),
                    "index_sizes": collection_stats.get("indexSizes", {}),
                    "total_index_size": collection_stats.get("totalIndexSize", 0)
                }
                
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    async def monitor_query_performance(self) -> Dict[str, Any]:
        """Monitor ongoing query performance and provide recommendations."""
        try:
            # Get current operations
            current_ops = await self.database.command("currentOp", {"active": True})
            
            performance_data = {
                "active_operations": len(current_ops.get("inprog", [])),
                "long_running_ops": [],
                "recommendations": [],
                "timestamp": datetime.utcnow()
            }
            
            # Analyze long-running operations
            for op in current_ops.get("inprog", []):
                if op.get("secs_running", 0) > 5:  # More than 5 seconds
                    performance_data["long_running_ops"].append({
                        "operation": op.get("op"),
                        "ns": op.get("ns"),
                        "duration_seconds": op.get("secs_running"),
                        "query": op.get("command", {})
                    })
            
            # Generate recommendations
            if performance_data["long_running_ops"]:
                performance_data["recommendations"].append(
                    "Consider adding indexes for long-running queries"
                )
            
            if performance_data["active_operations"] > 100:
                performance_data["recommendations"].append(
                    "High number of active operations - consider connection pooling optimization"
                )
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to monitor query performance: {str(e)}")
            return {"error": str(e)}
    
    async def optimize_for_production(self) -> Dict[str, Any]:
        """Run comprehensive optimization for production deployment."""
        logger.info("Starting comprehensive database optimization...")
        
        optimization_results = {
            "timestamp": datetime.utcnow(),
            "indexes_created": {},
            "aggregation_optimizations": {},
            "query_hints": {},
            "collection_stats": {},
            "performance_analysis": {},
            "status": "in_progress"
        }
        
        try:
            # Create production indexes
            optimization_results["indexes_created"] = await self.create_production_indexes()
            
            # Optimize aggregation pipelines
            optimization_results["aggregation_optimizations"] = await self.optimize_aggregation_pipelines()
            
            # Set up query hints
            optimization_results["query_hints"] = await self.setup_query_optimization_hints()
            
            # Get collection statistics
            optimization_results["collection_stats"] = await self.get_collection_statistics()
            
            # Monitor performance
            optimization_results["performance_analysis"] = await self.monitor_query_performance()
            
            optimization_results["status"] = "completed"
            logger.success("Database optimization completed successfully")
            
        except Exception as e:
            optimization_results["status"] = "error"
            optimization_results["error"] = str(e)
            logger.error(f"Database optimization failed: {str(e)}")
        
        return optimization_results


async def optimize_database_for_production(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Main function to optimize database for production deployment."""
    optimizer = DatabaseOptimizer(database)
    return await optimizer.optimize_for_production()