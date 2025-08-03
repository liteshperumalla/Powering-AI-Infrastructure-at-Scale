"""
Data migration utilities for transitioning from demo to real data structures.

This module provides comprehensive data migration capabilities including:
- Migration from demo/mock data to production data structures
- Data validation and integrity checks
- Backup and rollback procedures
- Migration progress tracking and logging
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import shutil
import tempfile
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import BulkWriteError, DuplicateKeyError
from beanie import Document
import bson

from .database import db, init_database
from .config import settings
from ..models import (
    Assessment, User, Report, ReportSection, 
    Recommendation, ServiceRecommendation, 
    Metric, AgentMetrics
)


class MigrationStatus(str, Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationStep(str, Enum):
    """Migration step enumeration."""
    BACKUP = "backup"
    VALIDATE_SOURCE = "validate_source"
    TRANSFORM_DATA = "transform_data"
    VALIDATE_TARGET = "validate_target"
    MIGRATE_DATA = "migrate_data"
    VERIFY_MIGRATION = "verify_migration"
    CLEANUP = "cleanup"


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    message: str
    records_processed: int = 0
    records_migrated: int = 0
    records_failed: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class MigrationConfig:
    """Configuration for data migration."""
    source_database: str
    target_database: str
    backup_enabled: bool = True
    backup_path: Optional[str] = None
    batch_size: int = 1000
    validate_data: bool = True
    dry_run: bool = False
    preserve_ids: bool = False
    skip_existing: bool = True
    rollback_on_error: bool = True
    
    def __post_init__(self):
        if self.backup_path is None:
            self.backup_path = f"./backups/migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


class DataMigrationManager:
    """
    Comprehensive data migration manager for transitioning from demo to production data.
    
    Features:
    - Automated backup and rollback procedures
    - Data validation and integrity checks
    - Batch processing for large datasets
    - Progress tracking and detailed logging
    - Error handling and recovery
    """
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.source_client: Optional[AsyncIOMotorClient] = None
        self.target_client: Optional[AsyncIOMotorClient] = None
        self.source_db = None
        self.target_db = None
        self.migration_log: List[Dict[str, Any]] = []
        self.backup_metadata: Dict[str, Any] = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_connections()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_connections()
    
    async def initialize_connections(self):
        """Initialize database connections for migration."""
        try:
            logger.info("🔌 Initializing migration database connections...")
            
            # Initialize source database connection
            if self.config.source_database != settings.mongodb_database:
                source_url = settings.get_database_url().replace(
                    settings.mongodb_database, 
                    self.config.source_database
                )
                self.source_client = AsyncIOMotorClient(source_url)
                self.source_db = self.source_client[self.config.source_database]
            else:
                # Use existing connection if same database
                await init_database()
                self.source_client = db.client
                self.source_db = db.database
            
            # Initialize target database connection
            if self.config.target_database != settings.mongodb_database:
                target_url = settings.get_database_url().replace(
                    settings.mongodb_database, 
                    self.config.target_database
                )
                self.target_client = AsyncIOMotorClient(target_url)
                self.target_db = self.target_client[self.config.target_database]
            else:
                # Use existing connection if same database
                if not db.client:
                    await init_database()
                self.target_client = db.client
                self.target_db = db.database
            
            # Test connections
            await self.source_client.admin.command('ping')
            await self.target_client.admin.command('ping')
            
            logger.success("✅ Migration database connections established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize migration connections: {e}")
            raise
    
    async def cleanup_connections(self):
        """Clean up database connections."""
        try:
            if self.source_client and self.source_client != db.client:
                self.source_client.close()
            if self.target_client and self.target_client != db.client:
                self.target_client.close()
            logger.info("🔌 Migration connections cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up migration connections: {e}")
    
    def log_migration_step(self, step: MigrationStep, status: str, details: Dict[str, Any] = None):
        """Log migration step with details."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step.value,
            "status": status,
            "details": details or {}
        }
        self.migration_log.append(log_entry)
        logger.info(f"📝 Migration step: {step.value} - {status}")
    
    async def create_backup(self) -> MigrationResult:
        """Create backup of source data before migration."""
        start_time = datetime.utcnow()
        
        try:
            self.log_migration_step(MigrationStep.BACKUP, "started")
            
            if not self.config.backup_enabled:
                logger.info("📦 Backup disabled, skipping...")
                return MigrationResult(
                    success=True,
                    message="Backup skipped (disabled in config)",
                    duration_seconds=0.0
                )
            
            # Create backup directory
            backup_path = Path(self.config.backup_path)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 Creating backup at: {backup_path}")
            
            # Get all collections to backup
            collections = await self.source_db.list_collection_names()
            total_records = 0
            
            self.backup_metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "source_database": self.config.source_database,
                "collections": {},
                "total_records": 0
            }
            
            # Backup each collection
            for collection_name in collections:
                collection = self.source_db[collection_name]
                
                # Count documents
                doc_count = await collection.count_documents({})
                if doc_count == 0:
                    continue
                
                logger.info(f"📦 Backing up collection '{collection_name}' ({doc_count} documents)")
                
                # Export collection data
                backup_file = backup_path / f"{collection_name}.json"
                documents = []
                
                async for doc in collection.find():
                    # Convert ObjectId to string for JSON serialization
                    doc = self._serialize_document(doc)
                    documents.append(doc)
                
                # Write to backup file
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, indent=2, default=str)
                
                # Calculate file hash for integrity
                file_hash = self._calculate_file_hash(backup_file)
                
                self.backup_metadata["collections"][collection_name] = {
                    "document_count": doc_count,
                    "file_path": str(backup_file),
                    "file_hash": file_hash,
                    "backup_time": datetime.utcnow().isoformat()
                }
                
                total_records += doc_count
            
            self.backup_metadata["total_records"] = total_records
            
            # Save backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_metadata, f, indent=2)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.log_migration_step(
                MigrationStep.BACKUP, 
                "completed",
                {"records_backed_up": total_records, "collections": len(collections)}
            )
            
            logger.success(f"✅ Backup completed: {total_records} records from {len(collections)} collections")
            
            return MigrationResult(
                success=True,
                message=f"Backup completed successfully",
                records_processed=total_records,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Backup failed: {str(e)}"
            
            self.log_migration_step(MigrationStep.BACKUP, "failed", {"error": error_msg})
            logger.error(f"❌ {error_msg}")
            
            return MigrationResult(
                success=False,
                message=error_msg,
                duration_seconds=duration,
                errors=[error_msg]
            )
    
    async def validate_source_data(self) -> MigrationResult:
        """Validate source data structure and integrity."""
        start_time = datetime.utcnow()
        
        try:
            self.log_migration_step(MigrationStep.VALIDATE_SOURCE, "started")
            
            logger.info("🔍 Validating source data structure...")
            
            validation_errors = []
            validation_warnings = []
            total_records = 0
            
            # Define expected collections and their validation rules
            collection_validators = {
                "users": self._validate_user_collection,
                "assessments": self._validate_assessment_collection,
                "recommendations": self._validate_recommendation_collection,
                "reports": self._validate_report_collection,
                "metrics": self._validate_metrics_collection
            }
            
            # Validate each collection
            for collection_name, validator in collection_validators.items():
                try:
                    if collection_name in await self.source_db.list_collection_names():
                        collection = self.source_db[collection_name]
                        doc_count = await collection.count_documents({})
                        
                        if doc_count > 0:
                            logger.info(f"🔍 Validating {collection_name} collection ({doc_count} documents)")
                            
                            # Run collection-specific validation
                            result = await validator(collection)
                            validation_errors.extend(result.errors)
                            validation_warnings.extend(result.warnings)
                            total_records += doc_count
                        else:
                            validation_warnings.append(f"Collection '{collection_name}' is empty")
                    else:
                        validation_warnings.append(f"Collection '{collection_name}' not found")
                        
                except Exception as e:
                    validation_errors.append(f"Error validating {collection_name}: {str(e)}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            if validation_errors:
                self.log_migration_step(
                    MigrationStep.VALIDATE_SOURCE, 
                    "failed",
                    {"errors": len(validation_errors), "warnings": len(validation_warnings)}
                )
                
                return MigrationResult(
                    success=False,
                    message=f"Source data validation failed with {len(validation_errors)} errors",
                    records_processed=total_records,
                    errors=validation_errors,
                    warnings=validation_warnings,
                    duration_seconds=duration
                )
            else:
                self.log_migration_step(
                    MigrationStep.VALIDATE_SOURCE, 
                    "completed",
                    {"warnings": len(validation_warnings), "records_validated": total_records}
                )
                
                logger.success(f"✅ Source data validation completed: {total_records} records validated")
                
                return MigrationResult(
                    success=True,
                    message="Source data validation completed successfully",
                    records_processed=total_records,
                    warnings=validation_warnings,
                    duration_seconds=duration
                )
                
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Source data validation failed: {str(e)}"
            
            self.log_migration_step(MigrationStep.VALIDATE_SOURCE, "failed", {"error": error_msg})
            logger.error(f"❌ {error_msg}")
            
            return MigrationResult(
                success=False,
                message=error_msg,
                duration_seconds=duration,
                errors=[error_msg]
            )
    
    async def migrate_collection(
        self, 
        collection_name: str, 
        transformer_func: callable,
        target_model: Document = None
    ) -> MigrationResult:
        """
        Migrate a specific collection with data transformation.
        
        Args:
            collection_name: Name of the collection to migrate
            transformer_func: Function to transform documents
            target_model: Beanie document model for validation
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔄 Migrating collection: {collection_name}")
            
            source_collection = self.source_db[collection_name]
            target_collection = self.target_db[collection_name]
            
            # Count source documents
            total_docs = await source_collection.count_documents({})
            if total_docs == 0:
                logger.info(f"📝 Collection '{collection_name}' is empty, skipping...")
                return MigrationResult(
                    success=True,
                    message=f"Collection '{collection_name}' is empty",
                    duration_seconds=0.0
                )
            
            logger.info(f"📊 Processing {total_docs} documents in batches of {self.config.batch_size}")
            
            processed = 0
            migrated = 0
            failed = 0
            errors = []
            
            # Process documents in batches
            async for batch in self._get_document_batches(source_collection, self.config.batch_size):
                try:
                    transformed_batch = []
                    
                    for doc in batch:
                        try:
                            # Transform document
                            transformed_doc = await transformer_func(doc)
                            
                            if transformed_doc:
                                # Validate with target model if provided
                                if target_model and self.config.validate_data:
                                    try:
                                        # Create model instance for validation
                                        model_instance = target_model(**transformed_doc)
                                        transformed_doc = model_instance.model_dump()
                                    except Exception as validation_error:
                                        errors.append(f"Validation failed for document {doc.get('_id')}: {validation_error}")
                                        failed += 1
                                        continue
                                
                                transformed_batch.append(transformed_doc)
                            
                        except Exception as transform_error:
                            errors.append(f"Transform failed for document {doc.get('_id')}: {transform_error}")
                            failed += 1
                    
                    # Insert transformed batch
                    if transformed_batch and not self.config.dry_run:
                        try:
                            if self.config.skip_existing:
                                # Use upsert to skip existing documents
                                for doc in transformed_batch:
                                    await target_collection.replace_one(
                                        {"_id": doc["_id"]},
                                        doc,
                                        upsert=True
                                    )
                            else:
                                # Insert all documents
                                await target_collection.insert_many(transformed_batch, ordered=False)
                            
                            migrated += len(transformed_batch)
                            
                        except BulkWriteError as bulk_error:
                            # Handle partial failures in bulk operations
                            migrated += bulk_error.details.get("nInserted", 0)
                            failed += len(bulk_error.details.get("writeErrors", []))
                            
                            for error in bulk_error.details.get("writeErrors", []):
                                errors.append(f"Bulk write error: {error.get('errmsg', 'Unknown error')}")
                    
                    processed += len(batch)
                    
                    # Log progress
                    if processed % (self.config.batch_size * 10) == 0:
                        logger.info(f"📊 Progress: {processed}/{total_docs} processed, {migrated} migrated, {failed} failed")
                
                except Exception as batch_error:
                    errors.append(f"Batch processing error: {str(batch_error)}")
                    failed += len(batch)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            if self.config.dry_run:
                logger.info(f"🧪 Dry run completed for {collection_name}: {processed} documents would be processed")
                migrated = processed - failed  # Estimate for dry run
            
            success = failed == 0 or (migrated > 0 and failed < processed * 0.1)  # Allow up to 10% failure rate
            
            result = MigrationResult(
                success=success,
                message=f"Migration {'completed' if success else 'completed with errors'} for {collection_name}",
                records_processed=processed,
                records_migrated=migrated,
                records_failed=failed,
                errors=errors[:100],  # Limit error list size
                duration_seconds=duration
            )
            
            if success:
                logger.success(f"✅ Collection '{collection_name}' migrated: {migrated}/{processed} documents")
            else:
                logger.warning(f"⚠️ Collection '{collection_name}' migration completed with errors: {failed} failed")
            
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Migration failed for collection '{collection_name}': {str(e)}"
            
            logger.error(f"❌ {error_msg}")
            
            return MigrationResult(
                success=False,
                message=error_msg,
                duration_seconds=duration,
                errors=[error_msg]
            )
    
    async def rollback_migration(self) -> MigrationResult:
        """Rollback migration using backup data."""
        start_time = datetime.utcnow()
        
        try:
            logger.info("🔄 Starting migration rollback...")
            
            if not self.backup_metadata:
                # Try to load backup metadata
                backup_path = Path(self.config.backup_path)
                metadata_file = backup_path / "backup_metadata.json"
                
                if not metadata_file.exists():
                    return MigrationResult(
                        success=False,
                        message="No backup metadata found for rollback",
                        errors=["Backup metadata file not found"]
                    )
                
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.backup_metadata = json.load(f)
            
            total_restored = 0
            errors = []
            
            # Restore each collection from backup
            for collection_name, metadata in self.backup_metadata["collections"].items():
                try:
                    logger.info(f"🔄 Restoring collection: {collection_name}")
                    
                    backup_file = Path(metadata["file_path"])
                    if not backup_file.exists():
                        errors.append(f"Backup file not found for collection '{collection_name}'")
                        continue
                    
                    # Verify backup file integrity
                    current_hash = self._calculate_file_hash(backup_file)
                    if current_hash != metadata["file_hash"]:
                        errors.append(f"Backup file integrity check failed for '{collection_name}'")
                        continue
                    
                    # Load backup data
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        documents = json.load(f)
                    
                    # Clear target collection
                    target_collection = self.target_db[collection_name]
                    await target_collection.delete_many({})
                    
                    # Restore documents
                    if documents:
                        # Deserialize documents
                        restored_docs = [self._deserialize_document(doc) for doc in documents]
                        
                        # Insert in batches
                        for i in range(0, len(restored_docs), self.config.batch_size):
                            batch = restored_docs[i:i + self.config.batch_size]
                            await target_collection.insert_many(batch)
                        
                        total_restored += len(restored_docs)
                        logger.info(f"✅ Restored {len(restored_docs)} documents to '{collection_name}'")
                
                except Exception as e:
                    errors.append(f"Error restoring collection '{collection_name}': {str(e)}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            if errors:
                return MigrationResult(
                    success=False,
                    message=f"Rollback completed with {len(errors)} errors",
                    records_migrated=total_restored,
                    errors=errors,
                    duration_seconds=duration
                )
            else:
                logger.success(f"✅ Migration rollback completed: {total_restored} records restored")
                
                return MigrationResult(
                    success=True,
                    message="Migration rollback completed successfully",
                    records_migrated=total_restored,
                    duration_seconds=duration
                )
                
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Rollback failed: {str(e)}"
            
            logger.error(f"❌ {error_msg}")
            
            return MigrationResult(
                success=False,
                message=error_msg,
                duration_seconds=duration,
                errors=[error_msg]
            )
    
    # Helper methods for data transformation and validation
    
    async def _get_document_batches(self, collection, batch_size: int):
        """Generator to yield document batches."""
        cursor = collection.find()
        batch = []
        
        async for doc in cursor:
            batch.append(doc)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        if batch:
            yield batch
    
    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize document for JSON storage."""
        serialized = {}
        
        for key, value in doc.items():
            if isinstance(value, bson.ObjectId):
                serialized[key] = {"$oid": str(value)}
            elif isinstance(value, datetime):
                serialized[key] = {"$date": value.isoformat()}
            elif isinstance(value, dict):
                serialized[key] = self._serialize_document(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize document from JSON storage."""
        deserialized = {}
        
        for key, value in doc.items():
            if isinstance(value, dict):
                if "$oid" in value:
                    deserialized[key] = bson.ObjectId(value["$oid"])
                elif "$date" in value:
                    deserialized[key] = datetime.fromisoformat(value["$date"])
                else:
                    deserialized[key] = self._deserialize_document(value)
            elif isinstance(value, list):
                deserialized[key] = [
                    self._deserialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                deserialized[key] = value
        
        return deserialized
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    # Collection-specific validation methods
    
    async def _validate_user_collection(self, collection) -> MigrationResult:
        """Validate user collection structure."""
        errors = []
        warnings = []
        
        # Sample a few documents for validation
        sample_docs = await collection.find().limit(10).to_list(length=10)
        
        for doc in sample_docs:
            # Check required fields
            required_fields = ["email", "full_name", "created_at"]
            for field in required_fields:
                if field not in doc:
                    errors.append(f"User document missing required field: {field}")
            
            # Validate email format
            if "email" in doc and "@" not in str(doc["email"]):
                errors.append(f"Invalid email format: {doc.get('email')}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message="User collection validation completed",
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_assessment_collection(self, collection) -> MigrationResult:
        """Validate assessment collection structure."""
        errors = []
        warnings = []
        
        sample_docs = await collection.find().limit(10).to_list(length=10)
        
        for doc in sample_docs:
            required_fields = ["user_id", "title", "status", "created_at"]
            for field in required_fields:
                if field not in doc:
                    errors.append(f"Assessment document missing required field: {field}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message="Assessment collection validation completed",
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_recommendation_collection(self, collection) -> MigrationResult:
        """Validate recommendation collection structure."""
        errors = []
        warnings = []
        
        sample_docs = await collection.find().limit(10).to_list(length=10)
        
        for doc in sample_docs:
            required_fields = ["assessment_id", "title", "description", "created_at"]
            for field in required_fields:
                if field not in doc:
                    errors.append(f"Recommendation document missing required field: {field}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message="Recommendation collection validation completed",
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_report_collection(self, collection) -> MigrationResult:
        """Validate report collection structure."""
        errors = []
        warnings = []
        
        sample_docs = await collection.find().limit(10).to_list(length=10)
        
        for doc in sample_docs:
            required_fields = ["assessment_id", "user_id", "title", "report_type", "created_at"]
            for field in required_fields:
                if field not in doc:
                    errors.append(f"Report document missing required field: {field}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message="Report collection validation completed",
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_metrics_collection(self, collection) -> MigrationResult:
        """Validate metrics collection structure."""
        errors = []
        warnings = []
        
        sample_docs = await collection.find().limit(10).to_list(length=10)
        
        for doc in sample_docs:
            required_fields = ["metric_name", "value", "timestamp"]
            for field in required_fields:
                if field not in doc:
                    errors.append(f"Metrics document missing required field: {field}")
        
        return MigrationResult(
            success=len(errors) == 0,
            message="Metrics collection validation completed",
            errors=errors,
            warnings=warnings
        )


# Data transformation functions for specific collections

async def transform_user_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform user document from demo to production format."""
    transformed = {
        "_id": doc.get("_id"),
        "email": doc.get("email", "").lower(),
        "hashed_password": doc.get("hashed_password", ""),
        "is_active": doc.get("is_active", True),
        "is_verified": doc.get("is_verified", False),
        "full_name": doc.get("full_name", ""),
        "company_name": doc.get("company_name"),
        "company_size": doc.get("company_size"),
        "industry": doc.get("industry"),
        "job_title": doc.get("job_title"),
        "role": doc.get("role", "user"),
        "preferred_cloud_providers": doc.get("preferred_cloud_providers", []),
        "notification_preferences": doc.get("notification_preferences", {
            "email_reports": True,
            "assessment_updates": True,
            "marketing": False
        }),
        "last_login": doc.get("last_login"),
        "login_count": doc.get("login_count", 0),
        "assessments_created": doc.get("assessments_created", 0),
        "created_at": doc.get("created_at", datetime.utcnow()),
        "updated_at": doc.get("updated_at", datetime.utcnow())
    }
    
    # Remove None values
    return {k: v for k, v in transformed.items() if v is not None}


async def transform_assessment_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform assessment document from demo to production format."""
    transformed = {
        "_id": doc.get("_id"),
        "user_id": doc.get("user_id", ""),
        "title": doc.get("title", ""),
        "description": doc.get("description"),
        "business_requirements": doc.get("business_requirements", {}),
        "technical_requirements": doc.get("technical_requirements", {}),
        "status": doc.get("status", "draft"),
        "priority": doc.get("priority", "medium"),
        "completion_percentage": doc.get("completion_percentage", 0.0),
        "workflow_id": doc.get("workflow_id"),
        "agent_states": doc.get("agent_states", {}),
        "workflow_progress": doc.get("workflow_progress", {}),
        "recommendations_generated": doc.get("recommendations_generated", False),
        "reports_generated": doc.get("reports_generated", False),
        "tags": doc.get("tags", []),
        "source": doc.get("source", "web_form"),
        "created_at": doc.get("created_at", datetime.utcnow()),
        "updated_at": doc.get("updated_at", datetime.utcnow()),
        "started_at": doc.get("started_at"),
        "completed_at": doc.get("completed_at")
    }
    
    return {k: v for k, v in transformed.items() if v is not None}


async def transform_recommendation_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform recommendation document from demo to production format."""
    transformed = {
        "_id": doc.get("_id"),
        "assessment_id": doc.get("assessment_id", ""),
        "agent_name": doc.get("agent_name", ""),
        "title": doc.get("title", ""),
        "description": doc.get("description", ""),
        "category": doc.get("category", "general"),
        "priority": doc.get("priority", "medium"),
        "confidence_score": doc.get("confidence_score", 0.5),
        "business_impact": doc.get("business_impact", "medium"),
        "implementation_complexity": doc.get("implementation_complexity", "medium"),
        "estimated_cost_monthly": doc.get("estimated_cost_monthly", 0.0),
        "estimated_savings_monthly": doc.get("estimated_savings_monthly", 0.0),
        "implementation_time_weeks": doc.get("implementation_time_weeks", 1),
        "cloud_provider": doc.get("cloud_provider"),
        "service_category": doc.get("service_category"),
        "rationale": doc.get("rationale", ""),
        "implementation_steps": doc.get("implementation_steps", []),
        "risks": doc.get("risks", []),
        "benefits": doc.get("benefits", []),
        "alternatives": doc.get("alternatives", []),
        "created_at": doc.get("created_at", datetime.utcnow()),
        "updated_at": doc.get("updated_at", datetime.utcnow())
    }
    
    return {k: v for k, v in transformed.items() if v is not None}


async def transform_report_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform report document from demo to production format."""
    transformed = {
        "_id": doc.get("_id"),
        "assessment_id": doc.get("assessment_id", ""),
        "user_id": doc.get("user_id", ""),
        "title": doc.get("title", ""),
        "description": doc.get("description"),
        "version": doc.get("version", "1.0"),
        "parent_report_id": doc.get("parent_report_id"),
        "is_template": doc.get("is_template", False),
        "template_id": doc.get("template_id"),
        "shared_with": doc.get("shared_with", []),
        "sharing_permissions": doc.get("sharing_permissions", {}),
        "is_public": doc.get("is_public", False),
        "public_link_token": doc.get("public_link_token"),
        "branding_config": doc.get("branding_config", {}),
        "custom_css": doc.get("custom_css"),
        "logo_url": doc.get("logo_url"),
        "report_type": doc.get("report_type", "full_assessment"),
        "format": doc.get("format", "pdf"),
        "template_version": doc.get("template_version", "1.0"),
        "status": doc.get("status", "pending"),
        "progress_percentage": doc.get("progress_percentage", 0.0),
        "sections": doc.get("sections", []),
        "total_pages": doc.get("total_pages"),
        "word_count": doc.get("word_count"),
        "file_path": doc.get("file_path"),
        "file_size_bytes": doc.get("file_size_bytes"),
        "file_hash": doc.get("file_hash"),
        "generated_by": doc.get("generated_by", []),
        "generation_time_seconds": doc.get("generation_time_seconds"),
        "completeness_score": doc.get("completeness_score"),
        "confidence_score": doc.get("confidence_score"),
        "priority": doc.get("priority", "medium"),
        "tags": doc.get("tags", []),
        "error_message": doc.get("error_message"),
        "retry_count": doc.get("retry_count", 0),
        "created_at": doc.get("created_at", datetime.utcnow()),
        "updated_at": doc.get("updated_at", datetime.utcnow()),
        "completed_at": doc.get("completed_at")
    }
    
    return {k: v for k, v in transformed.items() if v is not None}


async def transform_metrics_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform metrics document from demo to production format."""
    transformed = {
        "_id": doc.get("_id"),
        "metric_name": doc.get("metric_name", ""),
        "metric_type": doc.get("metric_type", "counter"),
        "value": doc.get("value", 0),
        "unit": doc.get("unit", "count"),
        "source": doc.get("source", "system"),
        "category": doc.get("category", "general"),
        "tags": doc.get("tags", {}),
        "metadata": doc.get("metadata", {}),
        "timestamp": doc.get("timestamp", datetime.utcnow())
    }
    
    return {k: v for k, v in transformed.items() if v is not None}

# Document transformation functions for production migration

async def transform_user_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform user document from demo to production format."""
    try:
        # Map demo values to production enum values
        industry_mapping = {
            "Technology": "technology",
            "Healthcare": "healthcare", 
            "Financial Services": "finance",
            "Finance": "finance",
            "Education": "education",
            "Retail": "retail",
            "Manufacturing": "manufacturing",
            "Government": "government",
            "Media": "other",
            "Transportation": "other",
            "Energy": "other",
            "Real Estate": "other",
            "E-commerce": "retail"
        }
        
        company_size_mapping = {
            "Startup": "startup",
            "Small Business": "small",
            "Mid-Market": "medium",
            "Enterprise": "enterprise"
        }
        
        # Basic user data transformation
        transformed = {
            "_id": doc.get("_id"),
            "email": doc.get("email", "").lower().strip(),
            "full_name": doc.get("full_name", ""),
            "hashed_password": doc.get("hashed_password", ""),
            "is_active": doc.get("is_active", True),
            "is_verified": doc.get("is_verified", False),
            "role": doc.get("role", "user"),
            "company_name": doc.get("company_name", ""),
            "industry": industry_mapping.get(doc.get("industry", ""), "other"),
            "company_size": company_size_mapping.get(doc.get("company_size", ""), "medium"),
            "job_title": doc.get("job_title", ""),
            "phone": doc.get("phone", ""),
            "timezone": doc.get("timezone", "UTC"),
            "preferred_cloud_providers": [],
            "notification_preferences": {
                "email_reports": True,
                "assessment_updates": True,
                "marketing": False
            },
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "last_login": doc.get("last_login"),
            "login_count": doc.get("login_count", 0)
        }
        
        # Ensure email is valid
        if not transformed["email"] or "@" not in transformed["email"]:
            transformed["email"] = f"user_{str(transformed['_id'])}@example.com"
        
        return {k: v for k, v in transformed.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming user document {doc.get('_id')}: {e}")
        return None


async def transform_assessment_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform assessment document from demo to production format."""
    try:
        transformed = {
            "_id": doc.get("_id"),
            "user_id": doc.get("user_id"),
            "title": doc.get("title", ""),
            "description": doc.get("description", ""),
            "status": doc.get("status", "draft"),
            "completion_percentage": float(doc.get("completion_percentage", 0.0)),
            "business_requirements": doc.get("business_requirements", {}),
            "technical_requirements": doc.get("technical_requirements", {}),
            "risk_assessment": doc.get("risk_assessment", {}),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "completed_at": doc.get("completed_at"),
            "metadata": doc.get("metadata", {})
        }
        
        # Ensure completion percentage is valid
        if transformed["completion_percentage"] > 100:
            transformed["completion_percentage"] = 100.0
        elif transformed["completion_percentage"] < 0:
            transformed["completion_percentage"] = 0.0
        
        return {k: v for k, v in transformed.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming assessment document {doc.get('_id')}: {e}")
        return None


async def transform_recommendation_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform recommendation document from demo to production format."""
    try:
        transformed = {
            "_id": doc.get("_id"),
            "assessment_id": doc.get("assessment_id"),
            "agent_name": doc.get("agent_name", ""),
            "agent_version": doc.get("agent_version", "1.0.0"),
            "recommendation_type": doc.get("recommendation_type", ""),
            "title": doc.get("title", ""),
            "description": doc.get("description", ""),
            "priority": doc.get("priority", "Medium"),
            "confidence_score": float(doc.get("confidence_score", 0.5)),
            "estimated_cost_monthly": float(doc.get("estimated_cost_monthly", 0.0)),
            "estimated_implementation_time": doc.get("estimated_implementation_time", ""),
            "cloud_provider": doc.get("cloud_provider", "AWS"),
            "services": doc.get("services", []),
            "benefits": doc.get("benefits", []),
            "risks": doc.get("risks", []),
            "implementation_steps": doc.get("implementation_steps", []),
            "metrics": doc.get("metrics", {}),
            "status": doc.get("status", "pending"),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow())
        }
        
        # Ensure confidence score is valid (0-1)
        if transformed["confidence_score"] > 1.0:
            transformed["confidence_score"] = 1.0
        elif transformed["confidence_score"] < 0.0:
            transformed["confidence_score"] = 0.0
        
        # Ensure cost is non-negative
        if transformed["estimated_cost_monthly"] < 0:
            transformed["estimated_cost_monthly"] = 0.0
        
        return {k: v for k, v in transformed.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming recommendation document {doc.get('_id')}: {e}")
        return None


async def transform_report_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform report document from demo to production format."""
    try:
        transformed = {
            "_id": doc.get("_id"),
            "assessment_id": doc.get("assessment_id"),
            "user_id": doc.get("user_id"),
            "title": doc.get("title", ""),
            "description": doc.get("description"),
            "report_type": doc.get("report_type", "full_assessment"),
            "format": doc.get("format", "PDF"),
            "status": doc.get("status", "pending"),
            "progress_percentage": float(doc.get("progress_percentage", 0.0)),
            "sections": doc.get("sections", []),
            "file_path": doc.get("file_path"),
            "file_size_bytes": doc.get("file_size_bytes"),
            "generated_by": doc.get("generated_by", []),
            "sharing": doc.get("sharing", {"is_public": False, "shared_with": [], "access_level": "private"}),
            "metadata": doc.get("metadata", {}),
            "created_at": doc.get("created_at", datetime.utcnow()),
            "updated_at": doc.get("updated_at", datetime.utcnow()),
            "completed_at": doc.get("completed_at")
        }
        
        # Ensure progress percentage is valid
        if transformed["progress_percentage"] > 100:
            transformed["progress_percentage"] = 100.0
        elif transformed["progress_percentage"] < 0:
            transformed["progress_percentage"] = 0.0
        
        # Ensure required fields are present
        if not transformed["user_id"]:
            logger.warning(f"Report {doc.get('_id')} missing user_id")
            return None
        
        return {k: v for k, v in transformed.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming report document {doc.get('_id')}: {e}")
        return None


async def transform_metrics_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform metrics document from demo to production format."""
    try:
        transformed = {
            "_id": doc.get("_id"),
            "metric_type": doc.get("metric_type", "system"),
            "metric_name": doc.get("metric_name", ""),
            "value": float(doc.get("value", 0.0)),
            "unit": doc.get("unit", "count"),
            "timestamp": doc.get("timestamp", datetime.utcnow()),
            "source": doc.get("source", "system"),
            "tags": doc.get("tags", {})
        }
        
        return {k: v for k, v in transformed.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error transforming metrics document {doc.get('_id')}: {e}")
        return None