#!/usr/bin/env python3
"""
Production Data Migration Execution Script

This script executes the complete production data migration process including:
- Pre-migration validation and backup
- Data transformation from demo to production structures
- Post-migration validation and verification
- Rollback procedures if needed
- Comprehensive reporting and logging

Usage:
    python scripts/execute_production_migration.py --config migration_config.json
    python scripts/execute_production_migration.py --interactive
    python scripts/execute_production_migration.py --rollback --backup-path ./backups/migration_20240101_120000
"""

import asyncio
import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import shutil
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.data_migration import (
    DataMigrationManager,
    MigrationConfig,
    MigrationResult,
    MigrationStatus,
    MigrationStep
)
from infra_mind.core.config import settings
from infra_mind.core.database import init_database
from infra_mind.models import User, Assessment, Recommendation, Report, Metric
from loguru import logger
import motor.motor_asyncio


@dataclass
class ProductionMigrationConfig:
    """Configuration for production migration execution."""
    source_database: str = "infra_mind_demo"
    target_database: str = "infra_mind_production"
    backup_base_path: str = "./backups"
    migration_name: str = "production_migration"
    
    # Migration settings
    batch_size: int = 500
    validate_data: bool = True
    create_backup: bool = True
    rollback_on_error: bool = True
    
    # Safety settings
    require_confirmation: bool = True
    max_failure_rate: float = 0.05  # 5% max failure rate
    timeout_minutes: int = 120
    
    # Notification settings
    notify_on_completion: bool = True
    notification_email: Optional[str] = None
    
    def to_migration_config(self, backup_path: str) -> MigrationConfig:
        """Convert to MigrationConfig for the migration manager."""
        return MigrationConfig(
            source_database=self.source_database,
            target_database=self.target_database,
            backup_enabled=self.create_backup,
            backup_path=backup_path,
            batch_size=self.batch_size,
            validate_data=self.validate_data,
            dry_run=False,
            preserve_ids=True,
            skip_existing=True,
            rollback_on_error=self.rollback_on_error
        )


class ProductionMigrationExecutor:
    """
    Production data migration executor with comprehensive safety checks and monitoring.
    
    Features:
    - Pre-migration validation and safety checks
    - Automated backup and rollback procedures
    - Real-time progress monitoring
    - Comprehensive error handling and recovery
    - Detailed reporting and logging
    """
    
    def __init__(self, config: ProductionMigrationConfig):
        self.config = config
        self.migration_id = f"{config.migration_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.backup_path = Path(config.backup_base_path) / self.migration_id
        self.log_file = f"production_migration_{self.migration_id}.log"
        
        # Migration state
        self.migration_results: List[Tuple[str, MigrationResult]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = MigrationStatus.PENDING
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure comprehensive logging for migration."""
        logger.remove()  # Remove default handler
        
        # Console logging with colors
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO",
            colorize=True
        )
        
        # File logging with detailed information
        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="50 MB",
            retention="30 days"
        )
        
        logger.info(f"📝 Migration logging initialized: {self.log_file}")
    
    async def execute_migration(self) -> bool:
        """Execute the complete production migration process."""
        try:
            self.start_time = datetime.utcnow()
            self.status = MigrationStatus.RUNNING
            
            logger.info("🚀 Starting production data migration...")
            logger.info(f"📋 Migration ID: {self.migration_id}")
            logger.info(f"📊 Configuration: {self.config.source_database} → {self.config.target_database}")
            
            # Step 1: Pre-migration checks
            if not await self._pre_migration_checks():
                logger.error("❌ Pre-migration checks failed")
                self.status = MigrationStatus.FAILED
                return False
            
            # Step 2: User confirmation (if required)
            if self.config.require_confirmation:
                if not await self._get_user_confirmation():
                    logger.info("🛑 Migration cancelled by user")
                    self.status = MigrationStatus.PENDING
                    return False
            
            # Step 3: Execute migration
            success = await self._execute_migration_steps()
            
            # Step 4: Post-migration validation
            if success:
                success = await self._post_migration_validation()
            
            # Step 5: Generate final report
            await self._generate_final_report()
            
            # Step 6: Cleanup and notifications
            await self._cleanup_and_notify(success)
            
            self.end_time = datetime.utcnow()
            self.status = MigrationStatus.COMPLETED if success else MigrationStatus.FAILED
            
            if success:
                logger.success("✅ Production migration completed successfully!")
            else:
                logger.error("❌ Production migration failed")
            
            return success
            
        except Exception as e:
            self.end_time = datetime.utcnow()
            self.status = MigrationStatus.FAILED
            logger.error(f"❌ Migration failed with unexpected error: {e}")
            await self._handle_critical_failure(e)
            return False
    
    async def _pre_migration_checks(self) -> bool:
        """Perform comprehensive pre-migration safety checks."""
        logger.info("🔍 Performing pre-migration safety checks...")
        
        try:
            # Check 1: Database connectivity
            logger.info("🔌 Checking database connectivity...")
            if not await self._check_database_connectivity():
                return False
            
            # Check 2: Source data validation
            logger.info("📊 Validating source data structure...")
            if not await self._validate_source_data():
                return False
            
            # Check 3: Target database preparation
            logger.info("🎯 Preparing target database...")
            if not await self._prepare_target_database():
                return False
            
            # Check 4: Disk space and resources
            logger.info("💾 Checking system resources...")
            if not await self._check_system_resources():
                return False
            
            # Check 5: Backup space availability
            if self.config.create_backup:
                logger.info("📦 Checking backup storage availability...")
                if not await self._check_backup_storage():
                    return False
            
            logger.success("✅ All pre-migration checks passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-migration checks failed: {e}")
            return False
    
    async def _check_database_connectivity(self) -> bool:
        """Check connectivity to source and target databases."""
        try:
            # Test source database
            source_url = settings.get_database_url().replace(
                settings.mongodb_database, 
                self.config.source_database
            )
            source_client = motor.motor_asyncio.AsyncIOMotorClient(source_url)
            await source_client.admin.command('ping')
            source_client.close()
            
            # Test target database
            target_url = settings.get_database_url().replace(
                settings.mongodb_database, 
                self.config.target_database
            )
            target_client = motor.motor_asyncio.AsyncIOMotorClient(target_url)
            await target_client.admin.command('ping')
            target_client.close()
            
            logger.success("✅ Database connectivity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connectivity check failed: {e}")
            return False
    
    async def _validate_source_data(self) -> bool:
        """Validate source data structure and integrity."""
        try:
            migration_config = self.config.to_migration_config(str(self.backup_path))
            
            async with DataMigrationManager(migration_config) as migration_manager:
                result = await migration_manager.validate_source_data()
                
                if result.success:
                    logger.success(f"✅ Source data validation passed: {result.records_processed} records")
                    if result.warnings:
                        logger.warning(f"⚠️ {len(result.warnings)} warnings found")
                        for warning in result.warnings[:5]:  # Show first 5 warnings
                            logger.warning(f"  - {warning}")
                    return True
                else:
                    logger.error(f"❌ Source data validation failed: {len(result.errors)} errors")
                    for error in result.errors[:5]:  # Show first 5 errors
                        logger.error(f"  - {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Source data validation error: {e}")
            return False
    
    async def _prepare_target_database(self) -> bool:
        """Prepare target database for migration."""
        try:
            target_url = settings.get_database_url().replace(
                settings.mongodb_database, 
                self.config.target_database
            )
            target_client = motor.motor_asyncio.AsyncIOMotorClient(target_url)
            target_db = target_client[self.config.target_database]
            
            # Check if target database exists and has data
            collections = await target_db.list_collection_names()
            if collections:
                total_docs = 0
                for collection_name in collections:
                    doc_count = await target_db[collection_name].count_documents({})
                    total_docs += doc_count
                
                if total_docs > 0:
                    logger.warning(f"⚠️ Target database contains {total_docs} documents in {len(collections)} collections")
                    logger.warning("⚠️ Migration will overwrite existing data")
            
            # Create indexes for optimal performance
            await self._create_target_indexes(target_db)
            
            target_client.close()
            logger.success("✅ Target database prepared")
            return True
            
        except Exception as e:
            logger.error(f"❌ Target database preparation failed: {e}")
            return False
    
    async def _create_target_indexes(self, target_db):
        """Create indexes on target database for optimal performance."""
        try:
            # User collection indexes
            users_collection = target_db["users"]
            await users_collection.create_index("email", unique=True)
            await users_collection.create_index("created_at")
            await users_collection.create_index("last_login")
            
            # Assessment collection indexes
            assessments_collection = target_db["assessments"]
            await assessments_collection.create_index("user_id")
            await assessments_collection.create_index("status")
            await assessments_collection.create_index("created_at")
            await assessments_collection.create_index([("user_id", 1), ("created_at", -1)])
            
            # Recommendation collection indexes
            recommendations_collection = target_db["recommendations"]
            await recommendations_collection.create_index("assessment_id")
            await recommendations_collection.create_index("confidence_score")
            await recommendations_collection.create_index("created_at")
            
            # Report collection indexes
            reports_collection = target_db["reports"]
            await reports_collection.create_index("assessment_id")
            await reports_collection.create_index("status")
            await reports_collection.create_index("created_at")
            
            # Metrics collection indexes
            metrics_collection = target_db["metrics"]
            await metrics_collection.create_index("timestamp")
            await metrics_collection.create_index("metric_type")
            await metrics_collection.create_index([("metric_type", 1), ("timestamp", -1)])
            
            logger.info("📊 Target database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    async def _check_system_resources(self) -> bool:
        """Check available system resources."""
        try:
            # Check available disk space
            backup_path = Path(self.config.backup_base_path)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            disk_usage = shutil.disk_usage(backup_path)
            available_gb = disk_usage.free / (1024**3)
            
            if available_gb < 10:  # Require at least 10GB free space
                logger.error(f"❌ Insufficient disk space: {available_gb:.1f}GB available (minimum 10GB required)")
                return False
            
            logger.info(f"💾 Available disk space: {available_gb:.1f}GB")
            
            # Check memory usage (basic check)
            try:
                import psutil
                memory = psutil.virtual_memory()
                available_memory_gb = memory.available / (1024**3)
                
                if available_memory_gb < 2:  # Require at least 2GB available memory
                    logger.warning(f"⚠️ Low available memory: {available_memory_gb:.1f}GB")
                else:
                    logger.info(f"🧠 Available memory: {available_memory_gb:.1f}GB")
                    
            except ImportError:
                logger.warning("⚠️ psutil not available, skipping memory check")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System resource check failed: {e}")
            return False
    
    async def _check_backup_storage(self) -> bool:
        """Check backup storage availability and permissions."""
        try:
            # Create backup directory
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = self.backup_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.success(f"✅ Backup storage ready: {self.backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup storage check failed: {e}")
            return False
    
    async def _get_user_confirmation(self) -> bool:
        """Get user confirmation for migration execution."""
        try:
            print("\n" + "="*80)
            print("🚨 PRODUCTION DATA MIGRATION CONFIRMATION")
            print("="*80)
            print(f"Source Database: {self.config.source_database}")
            print(f"Target Database: {self.config.target_database}")
            print(f"Migration ID: {self.migration_id}")
            print(f"Backup Path: {self.backup_path}")
            print(f"Backup Enabled: {'Yes' if self.config.create_backup else 'No'}")
            print(f"Rollback on Error: {'Yes' if self.config.rollback_on_error else 'No'}")
            print("\n⚠️  WARNING: This will modify production data!")
            print("⚠️  Ensure you have verified all pre-migration checks.")
            print("⚠️  Have a recovery plan ready in case of issues.")
            print("\n" + "="*80)
            
            while True:
                response = input("\nDo you want to proceed with the migration? (yes/no): ").strip().lower()
                
                if response in ['yes', 'y']:
                    logger.info("✅ User confirmed migration execution")
                    return True
                elif response in ['no', 'n']:
                    logger.info("🛑 User cancelled migration")
                    return False
                else:
                    print("Please enter 'yes' or 'no'")
                    
        except KeyboardInterrupt:
            logger.info("🛑 Migration cancelled by user (Ctrl+C)")
            return False
        except Exception as e:
            logger.error(f"❌ Error getting user confirmation: {e}")
            return False
    
    async def _execute_migration_steps(self) -> bool:
        """Execute the main migration steps."""
        try:
            migration_config = self.config.to_migration_config(str(self.backup_path))
            
            async with DataMigrationManager(migration_config) as migration_manager:
                # Step 1: Create backup
                if self.config.create_backup:
                    logger.info("📦 Creating pre-migration backup...")
                    backup_result = await migration_manager.create_backup()
                    self.migration_results.append(("backup", backup_result))
                    
                    if not backup_result.success:
                        logger.error("❌ Backup creation failed")
                        return False
                    
                    logger.success(f"✅ Backup created: {backup_result.records_processed} records")
                
                # Step 2: Execute collection migrations
                collections_to_migrate = [
                    ("users", User),
                    ("assessments", Assessment),
                    ("recommendations", Recommendation),
                    ("reports", Report),
                    ("metrics", Metric)
                ]
                
                total_migrated = 0
                total_failed = 0
                
                for collection_name, model_class in collections_to_migrate:
                    logger.info(f"🔄 Migrating collection: {collection_name}")
                    
                    # Get transformer function
                    transformer_func = self._get_transformer_function(collection_name)
                    
                    result = await migration_manager.migrate_collection(
                        collection_name=collection_name,
                        transformer_func=transformer_func,
                        target_model=model_class
                    )
                    
                    self.migration_results.append((f"migrate_{collection_name}", result))
                    total_migrated += result.records_migrated
                    total_failed += result.records_failed
                    
                    if result.success:
                        logger.success(f"✅ {collection_name}: {result.records_migrated} documents migrated")
                    else:
                        logger.error(f"❌ {collection_name}: {result.records_failed} documents failed")
                        
                        # Check failure rate
                        failure_rate = result.records_failed / max(result.records_processed, 1)
                        if failure_rate > self.config.max_failure_rate:
                            logger.error(f"❌ Failure rate ({failure_rate:.1%}) exceeds maximum ({self.config.max_failure_rate:.1%})")
                            
                            if self.config.rollback_on_error:
                                logger.info("🔄 Initiating rollback due to high failure rate...")
                                rollback_result = await migration_manager.rollback_migration()
                                self.migration_results.append(("rollback", rollback_result))
                                return False
                
                # Check overall success
                overall_failure_rate = total_failed / max(total_migrated + total_failed, 1)
                if overall_failure_rate > self.config.max_failure_rate:
                    logger.error(f"❌ Overall failure rate ({overall_failure_rate:.1%}) too high")
                    return False
                
                logger.success(f"✅ Migration completed: {total_migrated} migrated, {total_failed} failed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Migration execution failed: {e}")
            return False
    
    def _get_transformer_function(self, collection_name: str):
        """Get the appropriate transformer function for a collection."""
        # Import transformer functions
        from infra_mind.core.data_migration import (
            transform_user_document,
            transform_assessment_document,
            transform_recommendation_document,
            transform_report_document,
            transform_metrics_document
        )
        
        transformers = {
            "users": transform_user_document,
            "assessments": transform_assessment_document,
            "recommendations": transform_recommendation_document,
            "reports": transform_report_document,
            "metrics": transform_metrics_document
        }
        
        return transformers.get(collection_name, lambda doc: doc)
    
    async def _post_migration_validation(self) -> bool:
        """Perform comprehensive post-migration validation."""
        logger.info("🔍 Performing post-migration validation...")
        
        try:
            # Import validation utilities
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from validate_data import DataValidator
            
            async with DataValidator(self.config.target_database) as validator:
                validation_results = await validator.validate_all_collections()
                
                # Check validation results
                total_issues = sum(len(result.issues) for result in validation_results.values())
                critical_issues = sum(
                    sum(1 for issue in result.issues if issue.severity == "critical")
                    for result in validation_results.values()
                )
                
                if critical_issues > 0:
                    logger.error(f"❌ Post-migration validation found {critical_issues} critical issues")
                    
                    # Log critical issues
                    for collection_name, result in validation_results.items():
                        critical_collection_issues = [
                            issue for issue in result.issues 
                            if issue.severity == "critical"
                        ]
                        if critical_collection_issues:
                            logger.error(f"❌ {collection_name}: {len(critical_collection_issues)} critical issues")
                            for issue in critical_collection_issues[:3]:  # Show first 3
                                logger.error(f"  - {issue.message}")
                    
                    return False
                else:
                    logger.success(f"✅ Post-migration validation passed: {total_issues} total issues ({critical_issues} critical)")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Post-migration validation failed: {e}")
            return False
    
    async def _generate_final_report(self):
        """Generate comprehensive migration report."""
        try:
            logger.info("📄 Generating migration report...")
            
            # Calculate totals
            total_duration = (self.end_time or datetime.utcnow()) - (self.start_time or datetime.utcnow())
            total_records_processed = sum(result.records_processed for _, result in self.migration_results)
            total_records_migrated = sum(result.records_migrated for _, result in self.migration_results)
            total_records_failed = sum(result.records_failed for _, result in self.migration_results)
            
            # Create report
            report = {
                "migration_id": self.migration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "configuration": asdict(self.config),
                "status": self.status.value,
                "duration_seconds": total_duration.total_seconds(),
                "summary": {
                    "total_steps": len(self.migration_results),
                    "successful_steps": sum(1 for _, result in self.migration_results if result.success),
                    "failed_steps": sum(1 for _, result in self.migration_results if not result.success),
                    "total_records_processed": total_records_processed,
                    "total_records_migrated": total_records_migrated,
                    "total_records_failed": total_records_failed,
                    "success_rate": (total_records_migrated / max(total_records_processed, 1)) * 100
                },
                "steps": []
            }
            
            # Add step details
            for step_name, result in self.migration_results:
                step_report = {
                    "step": step_name,
                    "success": result.success,
                    "message": result.message,
                    "records_processed": result.records_processed,
                    "records_migrated": result.records_migrated,
                    "records_failed": result.records_failed,
                    "duration_seconds": result.duration_seconds,
                    "error_count": len(result.errors) if result.errors else 0,
                    "warning_count": len(result.warnings) if result.warnings else 0
                }
                report["steps"].append(step_report)
            
            # Save report
            report_file = f"production_migration_report_{self.migration_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.success(f"✅ Migration report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate migration report: {e}")
    
    async def _cleanup_and_notify(self, success: bool):
        """Cleanup temporary files and send notifications."""
        try:
            # Cleanup temporary files (if any)
            # Keep backups and logs for troubleshooting
            
            # Send notifications if configured
            if self.config.notify_on_completion and self.config.notification_email:
                await self._send_notification(success)
            
            # Log final status
            if success:
                logger.success("🎉 Production migration completed successfully!")
                logger.info(f"📦 Backup available at: {self.backup_path}")
                logger.info(f"📝 Detailed logs: {self.log_file}")
            else:
                logger.error("💥 Production migration failed!")
                logger.info(f"📦 Backup available for rollback: {self.backup_path}")
                logger.info(f"📝 Error logs: {self.log_file}")
                
        except Exception as e:
            logger.warning(f"⚠️ Cleanup/notification error: {e}")
    
    async def _send_notification(self, success: bool):
        """Send notification about migration completion."""
        try:
            # This would integrate with your notification system
            # For now, just log the notification
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"📧 Notification: Migration {status} - {self.migration_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send notification: {e}")
    
    async def _handle_critical_failure(self, error: Exception):
        """Handle critical migration failures."""
        try:
            logger.error("💥 Critical migration failure detected!")
            logger.error(f"💥 Error: {error}")
            
            # Attempt emergency rollback if backup exists
            if self.config.create_backup and self.backup_path.exists():
                logger.info("🚨 Attempting emergency rollback...")
                
                try:
                    migration_config = self.config.to_migration_config(str(self.backup_path))
                    async with DataMigrationManager(migration_config) as migration_manager:
                        rollback_result = await migration_manager.rollback_migration()
                        
                        if rollback_result.success:
                            logger.success("✅ Emergency rollback completed")
                        else:
                            logger.error("❌ Emergency rollback failed")
                            
                except Exception as rollback_error:
                    logger.error(f"❌ Emergency rollback error: {rollback_error}")
            
            # Generate emergency report
            await self._generate_emergency_report(error)
            
        except Exception as e:
            logger.error(f"❌ Critical failure handler error: {e}")
    
    async def _generate_emergency_report(self, error: Exception):
        """Generate emergency report for critical failures."""
        try:
            emergency_report = {
                "migration_id": self.migration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "CRITICAL_FAILURE",
                "error": str(error),
                "backup_path": str(self.backup_path) if self.backup_path else None,
                "log_file": self.log_file,
                "completed_steps": len(self.migration_results),
                "last_successful_step": None
            }
            
            # Find last successful step
            for step_name, result in reversed(self.migration_results):
                if result.success:
                    emergency_report["last_successful_step"] = step_name
                    break
            
            # Save emergency report
            emergency_file = f"EMERGENCY_migration_report_{self.migration_id}.json"
            with open(emergency_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_report, f, indent=2)
            
            logger.error(f"🚨 Emergency report saved: {emergency_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate emergency report: {e}")


async def execute_rollback(backup_path: str, target_database: str) -> bool:
    """Execute migration rollback from backup."""
    try:
        logger.info(f"🔄 Starting migration rollback...")
        logger.info(f"📦 Backup path: {backup_path}")
        logger.info(f"🎯 Target database: {target_database}")
        
        config = MigrationConfig(
            source_database="",  # Not used for rollback
            target_database=target_database,
            backup_enabled=True,
            backup_path=backup_path
        )
        
        async with DataMigrationManager(config) as migration_manager:
            result = await migration_manager.rollback_migration()
            
            if result.success:
                logger.success(f"✅ Rollback completed: {result.records_migrated} records restored")
                return True
            else:
                logger.error(f"❌ Rollback failed: {result.message}")
                for error in result.errors[:10]:
                    logger.error(f"  - {error}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Rollback execution failed: {e}")
        return False


def load_config_from_file(config_file: str) -> ProductionMigrationConfig:
    """Load migration configuration from JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return ProductionMigrationConfig(**config_data)
        
    except Exception as e:
        logger.error(f"❌ Failed to load config from {config_file}: {e}")
        raise


def create_interactive_config() -> ProductionMigrationConfig:
    """Create migration configuration interactively."""
    print("\n🔧 Interactive Migration Configuration")
    print("="*50)
    
    config = ProductionMigrationConfig()
    
    # Source database
    source = input(f"Source database [{config.source_database}]: ").strip()
    if source:
        config.source_database = source
    
    # Target database
    target = input(f"Target database [{config.target_database}]: ").strip()
    if target:
        config.target_database = target
    
    # Backup settings
    backup = input(f"Create backup? [{'yes' if config.create_backup else 'no'}]: ").strip().lower()
    if backup in ['no', 'n', 'false']:
        config.create_backup = False
    
    # Batch size
    batch_size = input(f"Batch size [{config.batch_size}]: ").strip()
    if batch_size.isdigit():
        config.batch_size = int(batch_size)
    
    # Confirmation requirement
    confirm = input(f"Require confirmation? [{'yes' if config.require_confirmation else 'no'}]: ").strip().lower()
    if confirm in ['no', 'n', 'false']:
        config.require_confirmation = False
    
    return config


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Production Data Migration Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute migration with config file
  python scripts/execute_production_migration.py --config migration_config.json
  
  # Interactive migration setup
  python scripts/execute_production_migration.py --interactive
  
  # Execute rollback
  python scripts/execute_production_migration.py --rollback --backup-path ./backups/migration_20240101_120000 --target infra_mind_production
  
  # Quick migration with defaults
  python scripts/execute_production_migration.py --source infra_mind_demo --target infra_mind_production
        """
    )
    
    # Configuration options
    parser.add_argument('--config', help='JSON configuration file path')
    parser.add_argument('--interactive', action='store_true', help='Interactive configuration mode')
    
    # Quick setup options
    parser.add_argument('--source', help='Source database name')
    parser.add_argument('--target', help='Target database name')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--no-confirmation', action='store_true', help='Skip user confirmation')
    parser.add_argument('--batch-size', type=int, default=500, help='Migration batch size')
    
    # Rollback options
    parser.add_argument('--rollback', action='store_true', help='Execute rollback instead of migration')
    parser.add_argument('--backup-path', help='Backup path for rollback')
    
    return parser


async def main():
    """Main entry point for production migration executor."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Handle rollback
        if args.rollback:
            if not args.backup_path or not args.target:
                logger.error("❌ Rollback requires --backup-path and --target arguments")
                return 1
            
            success = await execute_rollback(args.backup_path, args.target)
            return 0 if success else 1
        
        # Load or create configuration
        if args.config:
            config = load_config_from_file(args.config)
        elif args.interactive:
            config = create_interactive_config()
        else:
            # Use command line arguments or defaults
            config = ProductionMigrationConfig()
            
            if args.source:
                config.source_database = args.source
            if args.target:
                config.target_database = args.target
            if args.no_backup:
                config.create_backup = False
            if args.no_confirmation:
                config.require_confirmation = False
            if args.batch_size:
                config.batch_size = args.batch_size
        
        # Execute migration
        executor = ProductionMigrationExecutor(config)
        success = await executor.execute_migration()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)