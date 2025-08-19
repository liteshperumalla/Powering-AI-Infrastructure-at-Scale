#!/usr/bin/env python3
"""
Comprehensive Database Audit for Infra Mind System

This script performs a thorough audit of:
- Database collections and indexes
- Query performance analysis
- Data integrity checks
- Frontend-backend database integration
- Error detection and optimization recommendations

Run with: python database_audit.py
"""

import asyncio
import os
import sys
import traceback
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from loguru import logger
import json

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

class DatabaseAuditor:
    def __init__(self):
        self.client = None
        self.db = None
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "database_health": {},
            "collections_analysis": {},
            "indexes_analysis": {},
            "query_performance": {},
            "data_integrity": {},
            "integration_tests": {},
            "errors_found": [],
            "recommendations": [],
            "summary": {}
        }
        
    async def connect_database(self):
        """Connect to MongoDB database."""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client.get_database("infra_mind")
            
            # Test connection
            await self.client.admin.command('ping')
            logger.success("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.add_error("Connection", f"Failed to connect to database: {e}", "HIGH")
            return False
    
    def add_error(self, category: str, error: str, severity: str = "MEDIUM"):
        """Add an error to the audit results."""
        self.audit_results["errors_found"].append({
            "category": category,
            "error": error,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_recommendation(self, category: str, recommendation: str):
        """Add a recommendation to the audit results."""
        self.audit_results["recommendations"].append({
            "category": category,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })

    async def audit_database_health(self):
        """Audit overall database health and status."""
        logger.info("🔍 Auditing database health...")
        
        try:
            # Server status
            server_status = await self.client.admin.command('serverStatus')
            db_stats = await self.db.command('dbStats')
            
            # Connection info
            connection_info = {
                "host": server_status.get('host', 'unknown'),
                "version": server_status.get('version', 'unknown'),
                "uptime": server_status.get('uptime', 0),
                "connections": server_status.get('connections', {}),
                "memory": server_status.get('mem', {}),
                "locks": server_status.get('locks', {}),
                "network": server_status.get('network', {})
            }
            
            # Database stats
            database_info = {
                "name": db_stats.get('db', 'unknown'),
                "collections": db_stats.get('collections', 0),
                "objects": db_stats.get('objects', 0),
                "data_size": db_stats.get('dataSize', 0),
                "storage_size": db_stats.get('storageSize', 0),
                "indexes": db_stats.get('indexes', 0),
                "index_size": db_stats.get('indexSize', 0),
                "file_size": db_stats.get('fileSize', 0)
            }
            
            self.audit_results["database_health"] = {
                "connection_info": connection_info,
                "database_info": database_info,
                "health_status": "healthy"
            }
            
            # Check for potential issues
            memory_used = server_status.get('mem', {}).get('resident', 0)
            if memory_used > 1000:  # More than 1GB
                self.add_recommendation("Performance", f"High memory usage detected: {memory_used}MB")
            
            connections_current = server_status.get('connections', {}).get('current', 0)
            connections_available = server_status.get('connections', {}).get('available', 0)
            if connections_current > connections_available * 0.8:
                self.add_error("Performance", f"High connection usage: {connections_current}/{connections_available}", "MEDIUM")
            
            logger.success(f"✅ Database health check complete - {database_info['collections']} collections, {database_info['objects']} documents")
            
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            self.add_error("Health", f"Health check failed: {e}", "HIGH")

    async def audit_collections(self):
        """Audit all collections for structure and data quality."""
        logger.info("📊 Auditing database collections...")
        
        try:
            collections = await self.db.list_collection_names()
            collections_analysis = {}
            
            for collection_name in collections:
                logger.info(f"  Analyzing collection: {collection_name}")
                collection = self.db[collection_name]
                
                # Basic collection stats
                stats = await self.db.command("collStats", collection_name)
                doc_count = await collection.count_documents({})
                
                # Sample document for schema analysis
                sample_doc = await collection.find_one({})
                schema_info = {}
                if sample_doc:
                    schema_info = {
                        "fields": list(sample_doc.keys()),
                        "field_count": len(sample_doc.keys()),
                        "has_id_field": "_id" in sample_doc,
                        "has_timestamps": any(field in sample_doc for field in ["created_at", "updated_at", "timestamp"])
                    }
                
                # Data quality checks
                data_quality = await self.check_data_quality(collection)
                
                collections_analysis[collection_name] = {
                    "document_count": doc_count,
                    "avg_obj_size": stats.get('avgObjSize', 0),
                    "total_size": stats.get('size', 0),
                    "storage_size": stats.get('storageSize', 0),
                    "total_indexes": stats.get('nindexes', 0),
                    "index_sizes": stats.get('totalIndexSize', 0),
                    "schema_info": schema_info,
                    "data_quality": data_quality
                }
                
                # Check for issues
                if doc_count == 0:
                    self.add_error("Data", f"Collection '{collection_name}' is empty", "LOW")
                elif doc_count < 5 and collection_name not in ["health_checks", "cache"]:
                    self.add_error("Data", f"Collection '{collection_name}' has very few documents ({doc_count})", "MEDIUM")
                
                if stats.get('nindexes', 0) <= 1:  # Only _id index
                    self.add_recommendation("Performance", f"Consider adding indexes to collection '{collection_name}'")
            
            self.audit_results["collections_analysis"] = collections_analysis
            logger.success(f"✅ Collections audit complete - {len(collections)} collections analyzed")
            
        except Exception as e:
            logger.error(f"❌ Collections audit failed: {e}")
            self.add_error("Collections", f"Collections audit failed: {e}", "HIGH")

    async def check_data_quality(self, collection) -> Dict[str, Any]:
        """Check data quality for a specific collection."""
        try:
            # Check for null/missing required fields
            total_docs = await collection.count_documents({})
            if total_docs == 0:
                return {"total_documents": 0, "quality_score": 100}
            
            quality_issues = []
            
            # Check for documents missing _id
            missing_id = await collection.count_documents({"_id": {"$exists": False}})
            if missing_id > 0:
                quality_issues.append(f"{missing_id} documents missing _id field")
            
            # Check for very old documents (potential stale data)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            old_docs = 0
            try:
                old_docs = await collection.count_documents({
                    "$or": [
                        {"created_at": {"$lt": thirty_days_ago.isoformat()}},
                        {"timestamp": {"$lt": thirty_days_ago}}
                    ]
                })
            except:
                pass  # No timestamp fields
            
            # Check for duplicate documents (same title/name)
            duplicates = 0
            try:
                pipeline = [
                    {"$group": {
                        "_id": {"$ifNull": ["$title", "$name"]},
                        "count": {"$sum": 1}
                    }},
                    {"$match": {"count": {"$gt": 1}, "_id": {"$ne": None}}}
                ]
                duplicate_groups = await collection.aggregate(pipeline).to_list(None)
                duplicates = len(duplicate_groups)
            except:
                pass  # No title/name fields
            
            # Calculate quality score
            issues_count = len(quality_issues) + (1 if old_docs > total_docs * 0.5 else 0) + (1 if duplicates > 0 else 0)
            quality_score = max(0, 100 - (issues_count * 20))
            
            return {
                "total_documents": total_docs,
                "missing_id_count": missing_id,
                "old_documents": old_docs,
                "potential_duplicates": duplicates,
                "quality_issues": quality_issues,
                "quality_score": quality_score
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "quality_score": 0
            }

    async def audit_indexes(self):
        """Audit database indexes for performance optimization."""
        logger.info("🔍 Auditing database indexes...")
        
        try:
            collections = await self.db.list_collection_names()
            indexes_analysis = {}
            
            total_indexes = 0
            unused_indexes = []
            
            for collection_name in collections:
                collection = self.db[collection_name]
                
                # Get all indexes
                indexes = await collection.index_information()
                
                # Get index stats
                index_stats = []
                try:
                    stats_result = await self.db.command("collStats", collection_name, indexDetails=True)
                    index_stats = stats_result.get('indexSizes', {})
                except:
                    pass
                
                collection_indexes = {}
                for index_name, index_info in indexes.items():
                    total_indexes += 1
                    
                    # Analyze index usage
                    index_size = index_stats.get(index_name, 0)
                    
                    # Check if index might be unused (basic heuristic)
                    is_likely_unused = False
                    if index_name != "_id_" and index_size > 0:
                        # For now, we'll mark compound indexes on rarely used fields as potentially unused
                        key_fields = [field[0] for field in index_info.get('key', [])]
                        if any(field.startswith('temp_') or field.startswith('draft_') for field in key_fields):
                            is_likely_unused = True
                    
                    collection_indexes[index_name] = {
                        "key": index_info.get('key', []),
                        "unique": index_info.get('unique', False),
                        "sparse": index_info.get('sparse', False),
                        "background": index_info.get('background', False),
                        "size_bytes": index_size,
                        "likely_unused": is_likely_unused
                    }
                    
                    if is_likely_unused:
                        unused_indexes.append(f"{collection_name}.{index_name}")
                
                indexes_analysis[collection_name] = {
                    "total_indexes": len(indexes),
                    "indexes": collection_indexes
                }
                
                # Recommendations for missing indexes
                doc_count = await collection.count_documents({})
                if doc_count > 1000 and len(indexes) <= 1:
                    self.add_recommendation("Performance", f"Collection '{collection_name}' with {doc_count} documents should have additional indexes")
            
            self.audit_results["indexes_analysis"] = {
                "total_indexes": total_indexes,
                "collections": indexes_analysis,
                "potentially_unused": unused_indexes
            }
            
            if unused_indexes:
                self.add_recommendation("Performance", f"Consider reviewing {len(unused_indexes)} potentially unused indexes")
            
            logger.success(f"✅ Indexes audit complete - {total_indexes} indexes analyzed")
            
        except Exception as e:
            logger.error(f"❌ Indexes audit failed: {e}")
            self.add_error("Indexes", f"Indexes audit failed: {e}", "HIGH")

    async def audit_query_performance(self):
        """Audit query performance and identify slow operations."""
        logger.info("⚡ Auditing query performance...")
        
        try:
            # Enable profiling temporarily
            await self.db.command("profile", 2, slowms=100)
            
            # Test common queries
            performance_tests = []
            
            # Test 1: Assessments query
            start_time = time.time()
            assessments = await self.db.assessments.find({}).limit(10).to_list(None)
            assessments_time = (time.time() - start_time) * 1000
            performance_tests.append({
                "query": "assessments.find().limit(10)",
                "execution_time_ms": assessments_time,
                "documents_returned": len(assessments),
                "status": "fast" if assessments_time < 100 else "slow"
            })
            
            # Test 2: Recommendations by assessment_id
            if assessments:
                assessment_id = str(assessments[0]["_id"])
                start_time = time.time()
                recommendations = await self.db.recommendations.find({"assessment_id": assessment_id}).to_list(None)
                recommendations_time = (time.time() - start_time) * 1000
                performance_tests.append({
                    "query": f"recommendations.find(assessment_id={assessment_id})",
                    "execution_time_ms": recommendations_time,
                    "documents_returned": len(recommendations),
                    "status": "fast" if recommendations_time < 50 else "slow"
                })
            
            # Test 3: Users lookup
            start_time = time.time()
            users = await self.db.users.find({}).limit(5).to_list(None)
            users_time = (time.time() - start_time) * 1000
            performance_tests.append({
                "query": "users.find().limit(5)",
                "execution_time_ms": users_time,
                "documents_returned": len(users),
                "status": "fast" if users_time < 50 else "slow"
            })
            
            # Test 4: Agent metrics aggregation
            start_time = time.time()
            try:
                pipeline = [
                    {"$group": {
                        "_id": "$agent_name",
                        "avg_execution_time": {"$avg": "$execution_time_seconds"},
                        "total_executions": {"$sum": 1}
                    }},
                    {"$limit": 10}
                ]
                metrics = await self.db.agent_metrics.aggregate(pipeline).to_list(None)
                metrics_time = (time.time() - start_time) * 1000
                performance_tests.append({
                    "query": "agent_metrics.aggregate(group_by_agent)",
                    "execution_time_ms": metrics_time,
                    "documents_returned": len(metrics),
                    "status": "fast" if metrics_time < 200 else "slow"
                })
            except Exception as e:
                performance_tests.append({
                    "query": "agent_metrics.aggregate(group_by_agent)",
                    "execution_time_ms": 0,
                    "documents_returned": 0,
                    "status": "error",
                    "error": str(e)
                })
            
            # Check profiler data
            profiler_data = []
            try:
                profile_collection = self.db["system.profile"]
                slow_queries = await profile_collection.find({}).sort("ts", -1).limit(10).to_list(None)
                for query in slow_queries:
                    profiler_data.append({
                        "namespace": query.get("ns", "unknown"),
                        "operation": query.get("op", "unknown"),
                        "duration_ms": query.get("millis", 0),
                        "timestamp": query.get("ts", "").isoformat() if hasattr(query.get("ts", ""), "isoformat") else str(query.get("ts", ""))
                    })
            except:
                pass
            
            # Disable profiling
            await self.db.command("profile", 0)
            
            self.audit_results["query_performance"] = {
                "performance_tests": performance_tests,
                "slow_queries": profiler_data,
                "average_query_time": sum(test["execution_time_ms"] for test in performance_tests if test.get("execution_time_ms")) / len([t for t in performance_tests if t.get("execution_time_ms")]) if performance_tests else 0
            }
            
            # Add recommendations based on performance
            slow_queries_count = len([test for test in performance_tests if test.get("status") == "slow"])
            if slow_queries_count > 0:
                self.add_error("Performance", f"{slow_queries_count} slow queries detected", "MEDIUM")
                self.add_recommendation("Performance", "Consider adding indexes for slow queries")
            
            logger.success(f"✅ Query performance audit complete - {len(performance_tests)} tests run")
            
        except Exception as e:
            logger.error(f"❌ Query performance audit failed: {e}")
            self.add_error("Performance", f"Query performance audit failed: {e}", "HIGH")

    async def audit_data_integrity(self):
        """Audit data integrity and relationships."""
        logger.info("🔗 Auditing data integrity...")
        
        try:
            integrity_results = {}
            
            # Test 1: Assessment-Recommendation relationships
            assessments_count = await self.db.assessments.count_documents({})
            recommendations_count = await self.db.recommendations.count_documents({})
            
            # Find assessments without recommendations
            assessments_with_recs = await self.db.recommendations.distinct("assessment_id")
            assessments_without_recs = await self.db.assessments.count_documents({
                "_id": {"$nin": [assessment_id for assessment_id in assessments_with_recs]}
            })
            
            # Find orphaned recommendations
            assessment_ids = await self.db.assessments.distinct("_id")
            orphaned_recs = await self.db.recommendations.count_documents({
                "assessment_id": {"$nin": [str(aid) for aid in assessment_ids]}
            })
            
            integrity_results["assessment_recommendation_integrity"] = {
                "total_assessments": assessments_count,
                "total_recommendations": recommendations_count,
                "assessments_without_recommendations": assessments_without_recs,
                "orphaned_recommendations": orphaned_recs,
                "integrity_score": max(0, 100 - (assessments_without_recs * 20) - (orphaned_recs * 10))
            }
            
            # Test 2: User-Assessment relationships
            users_count = await self.db.users.count_documents({})
            user_ids = await self.db.users.distinct("_id")
            orphaned_assessments = await self.db.assessments.count_documents({
                "user_id": {"$nin": [str(uid) for uid in user_ids]}
            })
            
            integrity_results["user_assessment_integrity"] = {
                "total_users": users_count,
                "orphaned_assessments": orphaned_assessments,
                "integrity_score": max(0, 100 - (orphaned_assessments * 15))
            }
            
            # Test 3: Required fields validation
            required_fields_issues = []
            
            # Check assessments for required fields
            assessments_missing_title = await self.db.assessments.count_documents({
                "$or": [
                    {"title": {"$exists": False}},
                    {"title": ""},
                    {"title": None}
                ]
            })
            if assessments_missing_title > 0:
                required_fields_issues.append(f"{assessments_missing_title} assessments missing title")
            
            # Check users for required fields
            users_missing_email = await self.db.users.count_documents({
                "$or": [
                    {"email": {"$exists": False}},
                    {"email": ""},
                    {"email": None}
                ]
            })
            if users_missing_email > 0:
                required_fields_issues.append(f"{users_missing_email} users missing email")
            
            integrity_results["required_fields"] = {
                "issues": required_fields_issues,
                "issues_count": len(required_fields_issues)
            }
            
            # Test 4: Data consistency checks
            consistency_issues = []
            
            # Check for recommendations with invalid confidence scores
            invalid_confidence = await self.db.recommendations.count_documents({
                "$or": [
                    {"confidence_score": {"$lt": 0}},
                    {"confidence_score": {"$gt": 1}},
                    {"confidence_score": {"$exists": False}}
                ]
            })
            if invalid_confidence > 0:
                consistency_issues.append(f"{invalid_confidence} recommendations with invalid confidence scores")
            
            # Check for assessments with invalid status
            valid_statuses = ["draft", "in_progress", "completed", "failed"]
            invalid_status = await self.db.assessments.count_documents({
                "status": {"$nin": valid_statuses}
            })
            if invalid_status > 0:
                consistency_issues.append(f"{invalid_status} assessments with invalid status")
            
            integrity_results["data_consistency"] = {
                "issues": consistency_issues,
                "issues_count": len(consistency_issues)
            }
            
            self.audit_results["data_integrity"] = integrity_results
            
            # Add errors and recommendations
            if orphaned_recs > 0:
                self.add_error("Integrity", f"{orphaned_recs} orphaned recommendations found", "MEDIUM")
            if orphaned_assessments > 0:
                self.add_error("Integrity", f"{orphaned_assessments} orphaned assessments found", "MEDIUM")
            if required_fields_issues:
                self.add_error("Integrity", f"Required fields missing in {len(required_fields_issues)} collections", "HIGH")
            if consistency_issues:
                self.add_error("Integrity", f"Data consistency issues found in {len(consistency_issues)} areas", "MEDIUM")
            
            logger.success("✅ Data integrity audit complete")
            
        except Exception as e:
            logger.error(f"❌ Data integrity audit failed: {e}")
            self.add_error("Integrity", f"Data integrity audit failed: {e}", "HIGH")

    async def test_frontend_backend_integration(self):
        """Test database integration with frontend and backend."""
        logger.info("🔄 Testing frontend-backend database integration...")
        
        try:
            integration_results = {}
            
            # Test 1: API endpoint data consistency
            api_tests = []
            
            # Check if data structure matches expected API response format
            sample_assessment = await self.db.assessments.find_one({})
            if sample_assessment:
                required_fields = ["_id", "title", "status", "created_at", "updated_at"]
                missing_fields = [field for field in required_fields if field not in sample_assessment]
                api_tests.append({
                    "test": "assessment_api_fields",
                    "status": "pass" if not missing_fields else "fail",
                    "missing_fields": missing_fields,
                    "description": "Assessment document matches API expectations"
                })
            
            # Test 2: Recommendation data structure
            sample_recommendation = await self.db.recommendations.find_one({})
            if sample_recommendation:
                required_rec_fields = ["_id", "assessment_id", "agent_name", "confidence_score", "created_at"]
                missing_rec_fields = [field for field in required_rec_fields if field not in sample_recommendation]
                api_tests.append({
                    "test": "recommendation_api_fields",
                    "status": "pass" if not missing_rec_fields else "fail",
                    "missing_fields": missing_rec_fields,
                    "description": "Recommendation document matches API expectations"
                })
            
            # Test 3: User authentication data
            sample_user = await self.db.users.find_one({})
            if sample_user:
                required_user_fields = ["_id", "email", "hashed_password", "is_active", "created_at"]
                missing_user_fields = [field for field in required_user_fields if field not in sample_user]
                api_tests.append({
                    "test": "user_api_fields",
                    "status": "pass" if not missing_user_fields else "fail",
                    "missing_fields": missing_user_fields,
                    "description": "User document matches authentication expectations"
                })
            
            integration_results["api_compatibility"] = api_tests
            
            # Test 4: Frontend data requirements
            frontend_tests = []
            
            # Check visualization data availability
            viz_data = await self.db.visualization_data.find_one({})
            frontend_tests.append({
                "test": "visualization_data_available",
                "status": "pass" if viz_data else "fail",
                "description": "Visualization data available for frontend charts"
            })
            
            # Check metrics data for dashboard
            metrics_count = await self.db.metrics.count_documents({})
            frontend_tests.append({
                "test": "metrics_data_sufficient",
                "status": "pass" if metrics_count > 10 else "fail",
                "metrics_count": metrics_count,
                "description": "Sufficient metrics data for dashboard"
            })
            
            integration_results["frontend_compatibility"] = frontend_tests
            
            # Test 5: Real-time data flow
            realtime_tests = []
            
            # Check for recent data (indicates active system)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_assessments = await self.db.assessments.count_documents({
                "created_at": {"$gte": recent_cutoff.isoformat()}
            })
            recent_metrics = await self.db.agent_metrics.count_documents({
                "created_at": {"$gte": recent_cutoff.isoformat()}
            })
            
            realtime_tests.append({
                "test": "recent_data_flow",
                "status": "pass" if (recent_assessments > 0 or recent_metrics > 0) else "warning",
                "recent_assessments": recent_assessments,
                "recent_metrics": recent_metrics,
                "description": "Recent data indicates active system"
            })
            
            integration_results["realtime_data"] = realtime_tests
            
            self.audit_results["integration_tests"] = integration_results
            
            # Add errors based on test results
            failed_api_tests = [test for test in api_tests if test["status"] == "fail"]
            failed_frontend_tests = [test for test in frontend_tests if test["status"] == "fail"]
            
            if failed_api_tests:
                self.add_error("Integration", f"{len(failed_api_tests)} API compatibility tests failed", "HIGH")
            if failed_frontend_tests:
                self.add_error("Integration", f"{len(failed_frontend_tests)} frontend compatibility tests failed", "MEDIUM")
            
            logger.success("✅ Frontend-backend integration tests complete")
            
        except Exception as e:
            logger.error(f"❌ Integration tests failed: {e}")
            self.add_error("Integration", f"Integration tests failed: {e}", "HIGH")

    async def generate_optimization_recommendations(self):
        """Generate specific recommendations for database optimization."""
        logger.info("💡 Generating optimization recommendations...")
        
        try:
            # Analyze results and generate recommendations
            collections_analysis = self.audit_results.get("collections_analysis", {})
            indexes_analysis = self.audit_results.get("indexes_analysis", {})
            query_performance = self.audit_results.get("query_performance", {})
            
            # Index recommendations
            for collection_name, analysis in collections_analysis.items():
                doc_count = analysis.get("document_count", 0)
                index_count = analysis.get("total_indexes", 0)
                
                if doc_count > 1000 and index_count <= 1:
                    self.add_recommendation("Indexes", f"Add performance indexes to '{collection_name}' collection with {doc_count} documents")
                
                if collection_name == "assessments" and index_count < 3:
                    self.add_recommendation("Indexes", "Add indexes on 'user_id', 'status', and 'created_at' fields for assessments")
                
                if collection_name == "recommendations" and index_count < 3:
                    self.add_recommendation("Indexes", "Add indexes on 'assessment_id', 'agent_name', and 'confidence_score' fields for recommendations")
                
                if collection_name == "users" and index_count < 2:
                    self.add_recommendation("Indexes", "Add unique index on 'email' field for users")
            
            # Performance recommendations
            avg_query_time = query_performance.get("average_query_time", 0)
            if avg_query_time > 100:
                self.add_recommendation("Performance", f"Optimize queries - average execution time is {avg_query_time:.1f}ms")
            
            # Storage recommendations
            total_storage = sum(analysis.get("storage_size", 0) for analysis in collections_analysis.values())
            total_index_size = sum(analysis.get("index_sizes", 0) for analysis in collections_analysis.values())
            
            if total_index_size > total_storage * 0.5:
                self.add_recommendation("Storage", "Index size is high relative to data size - review index necessity")
            
            # Data integrity recommendations
            integrity_data = self.audit_results.get("data_integrity", {})
            assessment_integrity = integrity_data.get("assessment_recommendation_integrity", {})
            
            if assessment_integrity.get("assessments_without_recommendations", 0) > 0:
                self.add_recommendation("Data", "Generate recommendations for assessments that lack them")
            
            if assessment_integrity.get("orphaned_recommendations", 0) > 0:
                self.add_recommendation("Data", "Clean up orphaned recommendations that reference non-existent assessments")
            
            logger.success("✅ Optimization recommendations generated")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")

    async def create_missing_indexes(self):
        """Create essential indexes that are missing."""
        logger.info("🔧 Creating missing essential indexes...")
        
        try:
            indexes_created = []
            
            # Essential indexes for each collection
            essential_indexes = {
                "assessments": [
                    [("user_id", 1)],
                    [("status", 1)],
                    [("created_at", -1)],
                    [("user_id", 1), ("status", 1)]
                ],
                "recommendations": [
                    [("assessment_id", 1)],
                    [("agent_name", 1)],
                    [("confidence_score", -1)],
                    [("assessment_id", 1), ("agent_name", 1)]
                ],
                "users": [
                    [("email", 1)],
                    [("is_active", 1)],
                    [("created_at", -1)]
                ],
                "agent_metrics": [
                    [("agent_name", 1)],
                    [("assessment_id", 1)],
                    [("created_at", -1)],
                    [("agent_name", 1), ("created_at", -1)]
                ],
                "reports": [
                    [("assessment_id", 1)],
                    [("status", 1)],
                    [("created_at", -1)]
                ]
            }
            
            for collection_name, indexes in essential_indexes.items():
                if collection_name not in await self.db.list_collection_names():
                    continue
                
                collection = self.db[collection_name]
                existing_indexes = await collection.index_information()
                
                for index_spec in indexes:
                    # Create index name
                    index_name = "_".join([f"{field}_{direction}" for field, direction in index_spec])
                    
                    # Check if index already exists
                    exists = any(
                        existing_info.get("key") == index_spec 
                        for existing_info in existing_indexes.values()
                    )
                    
                    if not exists:
                        try:
                            await collection.create_index(index_spec, background=True)
                            indexes_created.append(f"{collection_name}.{index_name}")
                            logger.info(f"  ✅ Created index: {collection_name}.{index_name}")
                        except Exception as e:
                            logger.warning(f"  ⚠️ Failed to create index {collection_name}.{index_name}: {e}")
            
            # Create unique index on users.email if it doesn't exist
            users_collection = self.db["users"]
            if "users" in await self.db.list_collection_names():
                try:
                    existing_indexes = await users_collection.index_information()
                    email_unique_exists = any(
                        info.get("key") == [("email", 1)] and info.get("unique", False)
                        for info in existing_indexes.values()
                    )
                    
                    if not email_unique_exists:
                        await users_collection.create_index([("email", 1)], unique=True, background=True)
                        indexes_created.append("users.email_unique")
                        logger.info("  ✅ Created unique index: users.email_unique")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to create unique email index: {e}")
            
            self.audit_results["indexes_created"] = indexes_created
            
            if indexes_created:
                logger.success(f"✅ Created {len(indexes_created)} missing indexes")
            else:
                logger.success("✅ All essential indexes already exist")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            self.add_error("Optimization", f"Failed to create indexes: {e}", "MEDIUM")

    async def generate_summary(self):
        """Generate audit summary and overall health score."""
        logger.info("📋 Generating audit summary...")
        
        try:
            # Count errors by severity
            errors = self.audit_results.get("errors_found", [])
            error_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for error in errors:
                severity = error.get("severity", "MEDIUM")
                error_counts[severity] += 1
            
            # Calculate health score
            total_errors = sum(error_counts.values())
            health_score = max(0, 100 - (error_counts["HIGH"] * 25) - (error_counts["MEDIUM"] * 10) - (error_counts["LOW"] * 5))
            
            # Database statistics
            collections_analysis = self.audit_results.get("collections_analysis", {})
            total_documents = sum(analysis.get("document_count", 0) for analysis in collections_analysis.values())
            total_collections = len(collections_analysis)
            
            indexes_analysis = self.audit_results.get("indexes_analysis", {})
            total_indexes = indexes_analysis.get("total_indexes", 0)
            
            # Performance metrics
            query_performance = self.audit_results.get("query_performance", {})
            avg_query_time = query_performance.get("average_query_time", 0)
            
            # Integration test results
            integration_tests = self.audit_results.get("integration_tests", {})
            api_tests = integration_tests.get("api_compatibility", [])
            frontend_tests = integration_tests.get("frontend_compatibility", [])
            
            passed_api_tests = len([test for test in api_tests if test.get("status") == "pass"])
            passed_frontend_tests = len([test for test in frontend_tests if test.get("status") == "pass"])
            
            # Generate status
            if health_score >= 90:
                status = "EXCELLENT"
            elif health_score >= 75:
                status = "GOOD"
            elif health_score >= 50:
                status = "FAIR"
            else:
                status = "NEEDS_ATTENTION"
            
            summary = {
                "health_score": health_score,
                "status": status,
                "total_errors": total_errors,
                "error_breakdown": error_counts,
                "database_stats": {
                    "total_collections": total_collections,
                    "total_documents": total_documents,
                    "total_indexes": total_indexes,
                    "average_query_time_ms": round(avg_query_time, 2)
                },
                "integration_health": {
                    "api_tests_passed": f"{passed_api_tests}/{len(api_tests)}",
                    "frontend_tests_passed": f"{passed_frontend_tests}/{len(frontend_tests)}"
                },
                "recommendations_count": len(self.audit_results.get("recommendations", [])),
                "audit_timestamp": self.audit_results["timestamp"]
            }
            
            self.audit_results["summary"] = summary
            
            logger.success(f"✅ Audit summary complete - Health Score: {health_score}/100 ({status})")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {e}")
            self.add_error("Summary", f"Failed to generate summary: {e}", "LOW")

    def print_detailed_report(self):
        """Print detailed audit report."""
        print("\n" + "=" * 80)
        print("DATABASE AUDIT REPORT")
        print("=" * 80)
        print(f"Audit Timestamp: {self.audit_results['timestamp']}")
        
        summary = self.audit_results.get("summary", {})
        print(f"Health Score: {summary.get('health_score', 0)}/100")
        print(f"Overall Status: {summary.get('status', 'UNKNOWN')}")
        print(f"Total Issues: {summary.get('total_errors', 0)}")
        
        # Database statistics
        db_stats = summary.get("database_stats", {})
        print(f"\n📊 DATABASE STATISTICS:")
        print(f"  Collections: {db_stats.get('total_collections', 0)}")
        print(f"  Documents: {db_stats.get('total_documents', 0)}")
        print(f"  Indexes: {db_stats.get('total_indexes', 0)}")
        print(f"  Average Query Time: {db_stats.get('average_query_time_ms', 0)}ms")
        
        # Integration health
        integration = summary.get("integration_health", {})
        print(f"\n🔗 INTEGRATION HEALTH:")
        print(f"  API Tests Passed: {integration.get('api_tests_passed', '0/0')}")
        print(f"  Frontend Tests Passed: {integration.get('frontend_tests_passed', '0/0')}")
        
        # Issues found
        errors = self.audit_results.get("errors_found", [])
        if errors:
            print(f"\n🚨 ISSUES FOUND ({len(errors)}):")
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            for error in errors:
                emoji = severity_emoji.get(error.get("severity", "MEDIUM"), "•")
                print(f"  {emoji} [{error.get('category', 'Unknown')}] {error.get('error', 'Unknown error')}")
        
        # Recommendations
        recommendations = self.audit_results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations:
                print(f"  • [{rec.get('category', 'General')}] {rec.get('recommendation', 'No recommendation')}")
        
        # Indexes created
        indexes_created = self.audit_results.get("indexes_created", [])
        if indexes_created:
            print(f"\n🔧 INDEXES CREATED ({len(indexes_created)}):")
            for index in indexes_created:
                print(f"  ✅ {index}")
        
        print("=" * 80)

    async def save_report(self, filename: str = None):
        """Save the audit report to a file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"database_audit_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            logger.success(f"✅ Audit report saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

    async def run_comprehensive_audit(self):
        """Run the complete database audit."""
        logger.info("🚀 Starting comprehensive database audit...")
        
        try:
            # Connect to database
            if not await self.connect_database():
                return False
            
            # Run all audit sections
            await self.audit_database_health()
            await self.audit_collections()
            await self.audit_indexes()
            await self.audit_query_performance()
            await self.audit_data_integrity()
            await self.test_frontend_backend_integration()
            await self.generate_optimization_recommendations()
            await self.create_missing_indexes()
            await self.generate_summary()
            
            # Generate reports
            self.print_detailed_report()
            await self.save_report()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database audit failed: {e}")
            traceback.print_exc()
            return False
        finally:
            if self.client:
                self.client.close()

async def main():
    """Main function."""
    print("🔍 Database Auditor - Comprehensive Database Analysis")
    print("=" * 60)
    
    auditor = DatabaseAuditor()
    success = await auditor.run_comprehensive_audit()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)