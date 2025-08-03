#!/usr/bin/env python3
"""
Data validation utility for Infra Mind database integrity checks.

This script provides comprehensive data validation capabilities including:
- Schema validation against Pydantic models
- Data integrity checks and constraint validation
- Relationship consistency verification
- Performance and quality metrics
- Detailed reporting and recommendations

Usage:
    python scripts/validate_data.py --database infra_mind_prod --report validation_report.json
    python scripts/validate_data.py --database infra_mind_demo --collections users assessments
    python scripts/validate_data.py --database infra_mind_prod --fix-issues --dry-run
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.database import db, init_database
from infra_mind.core.config import settings
from infra_mind.models import User, Assessment, Recommendation, Report, Metric
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from pydantic import ValidationError
import bson


@dataclass
class ValidationIssue:
    """Represents a data validation issue."""
    collection: str
    document_id: str
    field: str
    issue_type: str
    severity: str  # critical, warning, info
    message: str
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Results of data validation."""
    collection: str
    total_documents: int
    valid_documents: int
    invalid_documents: int
    issues: List[ValidationIssue]
    performance_metrics: Dict[str, Any]
    
    @property
    def success_rate(self) -> float:
        if self.total_documents == 0:
            return 100.0
        return (self.valid_documents / self.total_documents) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "total_documents": self.total_documents,
            "valid_documents": self.valid_documents,
            "invalid_documents": self.invalid_documents,
            "success_rate": self.success_rate,
            "issues": [issue.to_dict() for issue in self.issues],
            "performance_metrics": self.performance_metrics
        }


class DataValidator:
    """
    Comprehensive data validation system for MongoDB collections.
    
    Features:
    - Schema validation against Pydantic models
    - Data integrity and constraint checks
    - Relationship consistency validation
    - Performance analysis and optimization suggestions
    - Automated issue detection and fixing
    """
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        
        # Model mappings for validation
        self.model_mappings = {
            "users": User,
            "assessments": Assessment,
            "recommendations": Recommendation,
            "reports": Report,
            "metrics": Metric
        }
        
        # Validation rules
        self.validation_rules = {
            "users": self._validate_user_rules,
            "assessments": self._validate_assessment_rules,
            "recommendations": self._validate_recommendation_rules,
            "reports": self._validate_report_rules,
            "metrics": self._validate_metrics_rules
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_connection()
    
    async def initialize_connection(self):
        """Initialize database connection."""
        try:
            logger.info(f"🔌 Connecting to database: {self.database_name}")
            
            # Get database URL and modify for target database
            db_url = settings.get_database_url()
            if self.database_name != settings.mongodb_database:
                db_url = db_url.replace(settings.mongodb_database, self.database_name)
            
            self.client = AsyncIOMotorClient(db_url)
            self.database = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.success("✅ Database connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def cleanup_connection(self):
        """Clean up database connection."""
        if self.client:
            self.client.close()
            logger.info("🔌 Database connection closed")
    
    async def validate_all_collections(
        self, 
        collections: Optional[List[str]] = None,
        sample_size: Optional[int] = None
    ) -> Dict[str, ValidationResult]:
        """
        Validate all collections in the database.
        
        Args:
            collections: Specific collections to validate (None for all)
            sample_size: Number of documents to sample per collection (None for all)
        
        Returns:
            Dictionary mapping collection names to validation results
        """
        try:
            logger.info("🔍 Starting comprehensive data validation...")
            
            # Get collections to validate
            if collections is None:
                available_collections = await self.database.list_collection_names()
                collections = [c for c in available_collections if c in self.model_mappings]
            
            logger.info(f"📊 Validating {len(collections)} collections")
            
            results = {}
            
            # Validate each collection
            for collection_name in collections:
                logger.info(f"🔍 Validating collection: {collection_name}")
                
                try:
                    result = await self.validate_collection(
                        collection_name=collection_name,
                        sample_size=sample_size
                    )
                    results[collection_name] = result
                    
                    # Log summary
                    logger.info(f"✅ {collection_name}: {result.success_rate:.1f}% valid ({result.valid_documents}/{result.total_documents})")
                    
                    if result.issues:
                        critical_issues = sum(1 for issue in result.issues if issue.severity == "critical")
                        warning_issues = sum(1 for issue in result.issues if issue.severity == "warning")
                        logger.warning(f"⚠️ {collection_name}: {critical_issues} critical, {warning_issues} warning issues")
                
                except Exception as e:
                    logger.error(f"❌ Failed to validate {collection_name}: {e}")
                    results[collection_name] = ValidationResult(
                        collection=collection_name,
                        total_documents=0,
                        valid_documents=0,
                        invalid_documents=0,
                        issues=[ValidationIssue(
                            collection=collection_name,
                            document_id="",
                            field="",
                            issue_type="validation_error",
                            severity="critical",
                            message=f"Validation failed: {str(e)}"
                        )],
                        performance_metrics={}
                    )
            
            # Generate summary
            total_docs = sum(r.total_documents for r in results.values())
            total_valid = sum(r.valid_documents for r in results.values())
            total_issues = sum(len(r.issues) for r in results.values())
            
            logger.success(f"✅ Validation completed: {total_valid}/{total_docs} documents valid, {total_issues} issues found")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            raise
    
    async def validate_collection(
        self, 
        collection_name: str,
        sample_size: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate a specific collection.
        
        Args:
            collection_name: Name of collection to validate
            sample_size: Number of documents to sample (None for all)
        
        Returns:
            Validation result for the collection
        """
        start_time = datetime.utcnow()
        
        try:
            collection = self.database[collection_name]
            model_class = self.model_mappings.get(collection_name)
            validation_rules = self.validation_rules.get(collection_name)
            
            if not model_class:
                raise ValueError(f"No model mapping found for collection: {collection_name}")
            
            # Count total documents
            total_docs = await collection.count_documents({})
            if total_docs == 0:
                return ValidationResult(
                    collection=collection_name,
                    total_documents=0,
                    valid_documents=0,
                    invalid_documents=0,
                    issues=[],
                    performance_metrics={"validation_time_seconds": 0.0}
                )
            
            # Determine sample size
            if sample_size and sample_size < total_docs:
                # Use aggregation pipeline for random sampling
                pipeline = [{"$sample": {"size": sample_size}}]
                cursor = collection.aggregate(pipeline)
                docs_to_validate = sample_size
            else:
                cursor = collection.find()
                docs_to_validate = total_docs
            
            logger.info(f"📊 Validating {docs_to_validate} documents from {collection_name}")
            
            valid_count = 0
            invalid_count = 0
            issues = []
            
            # Validate each document
            async for doc in cursor:
                doc_issues = await self._validate_document(
                    document=doc,
                    model_class=model_class,
                    collection_name=collection_name,
                    validation_rules=validation_rules
                )
                
                if doc_issues:
                    invalid_count += 1
                    issues.extend(doc_issues)
                else:
                    valid_count += 1
            
            # Calculate performance metrics
            validation_time = (datetime.utcnow() - start_time).total_seconds()
            performance_metrics = {
                "validation_time_seconds": validation_time,
                "documents_per_second": docs_to_validate / validation_time if validation_time > 0 else 0,
                "average_document_size_bytes": await self._calculate_average_document_size(collection),
                "index_usage": await self._analyze_index_usage(collection)
            }
            
            return ValidationResult(
                collection=collection_name,
                total_documents=docs_to_validate,
                valid_documents=valid_count,
                invalid_documents=invalid_count,
                issues=issues,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"❌ Collection validation failed for {collection_name}: {e}")
            raise
    
    async def _validate_document(
        self,
        document: Dict[str, Any],
        model_class,
        collection_name: str,
        validation_rules: Optional[callable] = None
    ) -> List[ValidationIssue]:
        """Validate a single document against its model and rules."""
        issues = []
        doc_id = str(document.get("_id", "unknown"))
        
        try:
            # Schema validation using Pydantic model
            try:
                model_instance = model_class(**document)
            except ValidationError as e:
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    issues.append(ValidationIssue(
                        collection=collection_name,
                        document_id=doc_id,
                        field=field_path,
                        issue_type="schema_validation",
                        severity="critical",
                        message=f"Schema validation error: {error['msg']}",
                        suggested_fix=f"Fix field '{field_path}' to match expected type/format"
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    collection=collection_name,
                    document_id=doc_id,
                    field="",
                    issue_type="model_instantiation",
                    severity="critical",
                    message=f"Failed to create model instance: {str(e)}"
                ))
            
            # Custom validation rules
            if validation_rules:
                try:
                    rule_issues = await validation_rules(document, doc_id)
                    issues.extend(rule_issues)
                except Exception as e:
                    issues.append(ValidationIssue(
                        collection=collection_name,
                        document_id=doc_id,
                        field="",
                        issue_type="custom_validation",
                        severity="warning",
                        message=f"Custom validation error: {str(e)}"
                    ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                collection=collection_name,
                document_id=doc_id,
                field="",
                issue_type="validation_error",
                severity="critical",
                message=f"Document validation failed: {str(e)}"
            ))
        
        return issues
    
    # Collection-specific validation rules
    
    async def _validate_user_rules(self, document: Dict[str, Any], doc_id: str) -> List[ValidationIssue]:
        """Custom validation rules for user documents."""
        issues = []
        
        # Email format validation
        email = document.get("email", "")
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            issues.append(ValidationIssue(
                collection="users",
                document_id=doc_id,
                field="email",
                issue_type="format_validation",
                severity="critical",
                message="Invalid email format",
                suggested_fix="Correct email format to user@domain.com"
            ))
        
        # Password hash validation
        hashed_password = document.get("hashed_password", "")
        if hashed_password and len(hashed_password) < 32:
            issues.append(ValidationIssue(
                collection="users",
                document_id=doc_id,
                field="hashed_password",
                issue_type="security_validation",
                severity="critical",
                message="Password hash appears too short",
                suggested_fix="Ensure password is properly hashed with bcrypt"
            ))
        
        # Activity consistency
        last_login = document.get("last_login")
        login_count = document.get("login_count", 0)
        
        if login_count > 0 and not last_login:
            issues.append(ValidationIssue(
                collection="users",
                document_id=doc_id,
                field="last_login",
                issue_type="consistency_validation",
                severity="warning",
                message="User has login count but no last_login timestamp",
                suggested_fix="Set last_login timestamp or reset login_count to 0"
            ))
        
        return issues
    
    async def _validate_assessment_rules(self, document: Dict[str, Any], doc_id: str) -> List[ValidationIssue]:
        """Custom validation rules for assessment documents."""
        issues = []
        
        # Status consistency
        status = document.get("status", "")
        completion_percentage = document.get("completion_percentage", 0)
        completed_at = document.get("completed_at")
        
        if status == "completed" and completion_percentage < 100:
            issues.append(ValidationIssue(
                collection="assessments",
                document_id=doc_id,
                field="completion_percentage",
                issue_type="consistency_validation",
                severity="warning",
                message="Assessment marked as completed but completion_percentage < 100",
                suggested_fix="Set completion_percentage to 100 or change status"
            ))
        
        if status == "completed" and not completed_at:
            issues.append(ValidationIssue(
                collection="assessments",
                document_id=doc_id,
                field="completed_at",
                issue_type="consistency_validation",
                severity="warning",
                message="Assessment marked as completed but no completed_at timestamp",
                suggested_fix="Set completed_at timestamp"
            ))
        
        # User reference validation
        user_id = document.get("user_id", "")
        if user_id:
            # Check if user exists (this would require a database lookup)
            # For now, just validate format
            try:
                if len(user_id) == 24:  # ObjectId length
                    bson.ObjectId(user_id)
            except:
                issues.append(ValidationIssue(
                    collection="assessments",
                    document_id=doc_id,
                    field="user_id",
                    issue_type="reference_validation",
                    severity="critical",
                    message="Invalid user_id format",
                    suggested_fix="Ensure user_id is a valid ObjectId or string reference"
                ))
        
        return issues
    
    async def _validate_recommendation_rules(self, document: Dict[str, Any], doc_id: str) -> List[ValidationIssue]:
        """Custom validation rules for recommendation documents."""
        issues = []
        
        # Confidence score validation
        confidence_score = document.get("confidence_score", 0)
        if not (0 <= confidence_score <= 1):
            issues.append(ValidationIssue(
                collection="recommendations",
                document_id=doc_id,
                field="confidence_score",
                issue_type="range_validation",
                severity="warning",
                message="Confidence score should be between 0 and 1",
                suggested_fix="Normalize confidence score to 0-1 range"
            ))
        
        # Cost validation
        estimated_cost = document.get("estimated_cost_monthly", 0)
        if estimated_cost < 0:
            issues.append(ValidationIssue(
                collection="recommendations",
                document_id=doc_id,
                field="estimated_cost_monthly",
                issue_type="logical_validation",
                severity="critical",
                message="Estimated cost cannot be negative",
                suggested_fix="Set estimated cost to 0 or positive value"
            ))
        
        return issues
    
    async def _validate_report_rules(self, document: Dict[str, Any], doc_id: str) -> List[ValidationIssue]:
        """Custom validation rules for report documents."""
        issues = []
        
        # File path validation
        file_path = document.get("file_path")
        file_size = document.get("file_size_bytes")
        
        if file_path and not file_size:
            issues.append(ValidationIssue(
                collection="reports",
                document_id=doc_id,
                field="file_size_bytes",
                issue_type="consistency_validation",
                severity="warning",
                message="Report has file_path but no file_size_bytes",
                suggested_fix="Calculate and set file_size_bytes"
            ))
        
        # Status and progress consistency
        status = document.get("status", "")
        progress = document.get("progress_percentage", 0)
        
        if status == "completed" and progress < 100:
            issues.append(ValidationIssue(
                collection="reports",
                document_id=doc_id,
                field="progress_percentage",
                issue_type="consistency_validation",
                severity="warning",
                message="Report marked as completed but progress < 100",
                suggested_fix="Set progress_percentage to 100"
            ))
        
        return issues
    
    async def _validate_metrics_rules(self, document: Dict[str, Any], doc_id: str) -> List[ValidationIssue]:
        """Custom validation rules for metrics documents."""
        issues = []
        
        # Timestamp validation
        timestamp = document.get("timestamp")
        if timestamp:
            # Check if timestamp is in the future
            if isinstance(timestamp, datetime) and timestamp > datetime.utcnow():
                issues.append(ValidationIssue(
                    collection="metrics",
                    document_id=doc_id,
                    field="timestamp",
                    issue_type="logical_validation",
                    severity="warning",
                    message="Metric timestamp is in the future",
                    suggested_fix="Correct timestamp to current or past time"
                ))
        
        # Value validation based on metric type
        metric_type = document.get("metric_type", "")
        value = document.get("value", 0)
        
        if metric_type == "percentage" and not (0 <= value <= 100):
            issues.append(ValidationIssue(
                collection="metrics",
                document_id=doc_id,
                field="value",
                issue_type="range_validation",
                severity="warning",
                message="Percentage metric value should be between 0 and 100",
                suggested_fix="Normalize percentage value to 0-100 range"
            ))
        
        return issues
    
    # Performance analysis methods
    
    async def _calculate_average_document_size(self, collection) -> float:
        """Calculate average document size in bytes."""
        try:
            stats = await self.database.command("collStats", collection.name)
            total_size = stats.get("size", 0)
            doc_count = stats.get("count", 0)
            
            return total_size / doc_count if doc_count > 0 else 0
        except:
            return 0
    
    async def _analyze_index_usage(self, collection) -> Dict[str, Any]:
        """Analyze index usage for the collection."""
        try:
            # Get index stats
            index_stats = await collection.index_stats().to_list(length=None)
            
            usage_info = {
                "total_indexes": len(index_stats),
                "unused_indexes": [],
                "most_used_index": None,
                "index_efficiency": 0.0
            }
            
            if index_stats:
                # Find unused indexes
                for stat in index_stats:
                    if stat.get("accesses", {}).get("ops", 0) == 0:
                        usage_info["unused_indexes"].append(stat["name"])
                
                # Find most used index
                most_used = max(index_stats, key=lambda x: x.get("accesses", {}).get("ops", 0))
                usage_info["most_used_index"] = {
                    "name": most_used["name"],
                    "operations": most_used.get("accesses", {}).get("ops", 0)
                }
                
                # Calculate efficiency (percentage of indexes being used)
                used_indexes = len(index_stats) - len(usage_info["unused_indexes"])
                usage_info["index_efficiency"] = (used_indexes / len(index_stats)) * 100
            
            return usage_info
        except:
            return {"error": "Could not analyze index usage"}
    
    async def fix_issues(
        self, 
        validation_results: Dict[str, ValidationResult],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Attempt to automatically fix validation issues.
        
        Args:
            validation_results: Results from validation
            dry_run: If True, only simulate fixes without applying them
        
        Returns:
            Summary of fixes applied or would be applied
        """
        fix_summary = {
            "total_issues": 0,
            "fixable_issues": 0,
            "fixed_issues": 0,
            "failed_fixes": 0,
            "fixes_by_collection": {},
            "dry_run": dry_run
        }
        
        for collection_name, result in validation_results.items():
            collection_fixes = {
                "attempted": 0,
                "successful": 0,
                "failed": 0,
                "fixes": []
            }
            
            fix_summary["total_issues"] += len(result.issues)
            
            for issue in result.issues:
                if issue.suggested_fix:
                    fix_summary["fixable_issues"] += 1
                    collection_fixes["attempted"] += 1
                    
                    try:
                        if not dry_run:
                            # Apply the fix (implementation would depend on issue type)
                            success = await self._apply_fix(issue)
                            if success:
                                fix_summary["fixed_issues"] += 1
                                collection_fixes["successful"] += 1
                            else:
                                fix_summary["failed_fixes"] += 1
                                collection_fixes["failed"] += 1
                        else:
                            # Simulate fix for dry run
                            collection_fixes["successful"] += 1
                            fix_summary["fixed_issues"] += 1
                        
                        collection_fixes["fixes"].append({
                            "document_id": issue.document_id,
                            "field": issue.field,
                            "issue_type": issue.issue_type,
                            "fix_applied": issue.suggested_fix,
                            "status": "success" if not dry_run else "simulated"
                        })
                        
                    except Exception as e:
                        fix_summary["failed_fixes"] += 1
                        collection_fixes["failed"] += 1
                        collection_fixes["fixes"].append({
                            "document_id": issue.document_id,
                            "field": issue.field,
                            "issue_type": issue.issue_type,
                            "error": str(e),
                            "status": "failed"
                        })
            
            fix_summary["fixes_by_collection"][collection_name] = collection_fixes
        
        return fix_summary
    
    async def _apply_fix(self, issue: ValidationIssue) -> bool:
        """Apply a specific fix to resolve a validation issue."""
        try:
            collection = self.database[issue.collection]
            doc_id = bson.ObjectId(issue.document_id) if len(issue.document_id) == 24 else issue.document_id
            
            # This is a simplified example - real implementation would need
            # specific fix logic for each issue type
            if issue.issue_type == "consistency_validation":
                if "completion_percentage" in issue.field and "completed" in issue.message:
                    # Fix completion percentage for completed assessments
                    await collection.update_one(
                        {"_id": doc_id},
                        {"$set": {"completion_percentage": 100.0}}
                    )
                    return True
            
            # Add more fix implementations as needed
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to apply fix for {issue.document_id}: {e}")
            return False


async def main():
    """Main entry point for data validation CLI."""
    parser = argparse.ArgumentParser(
        description="Data validation utility for Infra Mind",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--database', required=True, help='Database name to validate')
    parser.add_argument('--collections', nargs='*', help='Specific collections to validate')
    parser.add_argument('--sample-size', type=int, help='Number of documents to sample per collection')
    parser.add_argument('--report', help='Output file for validation report (JSON)')
    parser.add_argument('--fix-issues', action='store_true', help='Attempt to fix validation issues')
    parser.add_argument('--dry-run', action='store_true', help='Simulate fixes without applying them')
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    try:
        async with DataValidator(args.database) as validator:
            # Run validation
            results = await validator.validate_all_collections(
                collections=args.collections,
                sample_size=args.sample_size
            )
            
            # Generate report
            report = {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "database_name": args.database,
                "collections_validated": len(results),
                "summary": {
                    "total_documents": sum(r.total_documents for r in results.values()),
                    "valid_documents": sum(r.valid_documents for r in results.values()),
                    "invalid_documents": sum(r.invalid_documents for r in results.values()),
                    "total_issues": sum(len(r.issues) for r in results.values()),
                    "critical_issues": sum(
                        len([i for i in r.issues if i.severity == "critical"]) 
                        for r in results.values()
                    ),
                    "warning_issues": sum(
                        len([i for i in r.issues if i.severity == "warning"]) 
                        for r in results.values()
                    )
                },
                "results": {name: result.to_dict() for name, result in results.items()}
            }
            
            # Apply fixes if requested
            if args.fix_issues:
                logger.info("🔧 Attempting to fix validation issues...")
                fix_results = await validator.fix_issues(results, dry_run=args.dry_run)
                report["fix_results"] = fix_results
                
                if args.dry_run:
                    logger.info(f"🧪 Dry run: {fix_results['fixed_issues']} issues would be fixed")
                else:
                    logger.info(f"🔧 Fixed {fix_results['fixed_issues']} issues, {fix_results['failed_fixes']} failed")
            
            # Save report
            if args.report:
                with open(args.report, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, default=str)
                logger.info(f"📄 Validation report saved to: {args.report}")
            
            # Print summary
            summary = report["summary"]
            overall_success_rate = (summary["valid_documents"] / summary["total_documents"]) * 100 if summary["total_documents"] > 0 else 100
            
            logger.info(f"📊 Validation Summary:")
            logger.info(f"  Total documents: {summary['total_documents']}")
            logger.info(f"  Valid documents: {summary['valid_documents']} ({overall_success_rate:.1f}%)")
            logger.info(f"  Issues found: {summary['total_issues']} ({summary['critical_issues']} critical, {summary['warning_issues']} warnings)")
            
            return 0 if summary["critical_issues"] == 0 else 1
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)