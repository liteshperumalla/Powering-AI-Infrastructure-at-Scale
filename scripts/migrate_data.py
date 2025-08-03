#!/usr/bin/env python3
"""
Data migration script for transitioning from demo to production data structures.

This script provides a command-line interface for executing data migrations
with comprehensive backup, validation, and rollback capabilities.

Usage:
    python scripts/migrate_data.py --help
    python scripts/migrate_data.py migrate --source demo_db --target prod_db
    python scripts/migrate_data.py validate --database demo_db
    python scripts/migrate_data.py rollback --backup-path ./backups/migration_20240101_120000
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.data_migration import (
    DataMigrationManager,
    MigrationConfig,
    MigrationResult,
    transform_user_document,
    transform_assessment_document,
    transform_recommendation_document,
    transform_report_document,
    transform_metrics_document
)
from infra_mind.core.config import settings
from infra_mind.models import User, Assessment, Recommendation, Report, Metric
from loguru import logger


class MigrationCLI:
    """Command-line interface for data migration operations."""
    
    def __init__(self):
        self.migration_transformers = {
            "users": (transform_user_document, User),
            "assessments": (transform_assessment_document, Assessment),
            "recommendations": (transform_recommendation_document, Recommendation),
            "reports": (transform_report_document, Report),
            "metrics": (transform_metrics_document, Metric)
        }
    
    async def migrate_data(self, args) -> bool:
        """Execute full data migration."""
        try:
            logger.info("🚀 Starting data migration process...")
            
            # Create migration configuration
            config = MigrationConfig(
                source_database=args.source,
                target_database=args.target,
                backup_enabled=not args.no_backup,
                backup_path=args.backup_path,
                batch_size=args.batch_size,
                validate_data=not args.no_validation,
                dry_run=args.dry_run,
                preserve_ids=args.preserve_ids,
                skip_existing=args.skip_existing,
                rollback_on_error=args.rollback_on_error
            )
            
            logger.info(f"📋 Migration configuration:")
            logger.info(f"  Source: {config.source_database}")
            logger.info(f"  Target: {config.target_database}")
            logger.info(f"  Backup: {'enabled' if config.backup_enabled else 'disabled'}")
            logger.info(f"  Batch size: {config.batch_size}")
            logger.info(f"  Dry run: {'yes' if config.dry_run else 'no'}")
            
            # Execute migration
            async with DataMigrationManager(config) as migration_manager:
                migration_results = []
                
                # Step 1: Create backup
                if config.backup_enabled:
                    backup_result = await migration_manager.create_backup()
                    migration_results.append(("backup", backup_result))
                    
                    if not backup_result.success:
                        logger.error("❌ Backup failed, aborting migration")
                        return False
                
                # Step 2: Validate source data
                if config.validate_data:
                    validation_result = await migration_manager.validate_source_data()
                    migration_results.append(("validation", validation_result))
                    
                    if not validation_result.success:
                        logger.error("❌ Source data validation failed")
                        if config.rollback_on_error:
                            logger.info("🔄 Rolling back due to validation failure...")
                            return False
                
                # Step 3: Migrate each collection
                total_migrated = 0
                total_failed = 0
                
                for collection_name, (transformer, model) in self.migration_transformers.items():
                    logger.info(f"🔄 Migrating collection: {collection_name}")
                    
                    result = await migration_manager.migrate_collection(
                        collection_name=collection_name,
                        transformer_func=transformer,
                        target_model=model
                    )
                    
                    migration_results.append((f"migrate_{collection_name}", result))
                    total_migrated += result.records_migrated
                    total_failed += result.records_failed
                    
                    if not result.success and config.rollback_on_error:
                        logger.error(f"❌ Migration failed for {collection_name}, initiating rollback...")
                        rollback_result = await migration_manager.rollback_migration()
                        migration_results.append(("rollback", rollback_result))
                        return False
                
                # Generate migration report
                await self._generate_migration_report(migration_results, args.output_report)
                
                # Summary
                if config.dry_run:
                    logger.info(f"🧪 Dry run completed: {total_migrated} documents would be migrated")
                else:
                    logger.success(f"✅ Migration completed: {total_migrated} documents migrated, {total_failed} failed")
                
                return total_failed == 0 or total_failed < total_migrated * 0.1  # Allow up to 10% failure
                
        except Exception as e:
            logger.error(f"❌ Migration failed with error: {e}")
            return False
    
    async def validate_data(self, args) -> bool:
        """Validate data structure without migration."""
        try:
            logger.info(f"🔍 Validating data in database: {args.database}")
            
            config = MigrationConfig(
                source_database=args.database,
                target_database=args.database,  # Same database for validation
                backup_enabled=False,
                validate_data=True
            )
            
            async with DataMigrationManager(config) as migration_manager:
                result = await migration_manager.validate_source_data()
                
                if result.success:
                    logger.success(f"✅ Data validation completed: {result.records_processed} records validated")
                    if result.warnings:
                        logger.warning(f"⚠️ Validation warnings: {len(result.warnings)}")
                        for warning in result.warnings[:10]:  # Show first 10 warnings
                            logger.warning(f"  - {warning}")
                else:
                    logger.error(f"❌ Data validation failed: {len(result.errors)} errors")
                    for error in result.errors[:10]:  # Show first 10 errors
                        logger.error(f"  - {error}")
                
                return result.success
                
        except Exception as e:
            logger.error(f"❌ Validation failed with error: {e}")
            return False
    
    async def rollback_migration(self, args) -> bool:
        """Rollback migration using backup data."""
        try:
            logger.info(f"🔄 Rolling back migration from backup: {args.backup_path}")
            
            config = MigrationConfig(
                source_database="",  # Not used for rollback
                target_database=args.target,
                backup_enabled=True,
                backup_path=args.backup_path
            )
            
            async with DataMigrationManager(config) as migration_manager:
                result = await migration_manager.rollback_migration()
                
                if result.success:
                    logger.success(f"✅ Rollback completed: {result.records_migrated} records restored")
                else:
                    logger.error(f"❌ Rollback failed: {result.message}")
                    for error in result.errors[:10]:
                        logger.error(f"  - {error}")
                
                return result.success
                
        except Exception as e:
            logger.error(f"❌ Rollback failed with error: {e}")
            return False
    
    async def list_collections(self, args) -> bool:
        """List collections in a database."""
        try:
            logger.info(f"📋 Listing collections in database: {args.database}")
            
            config = MigrationConfig(
                source_database=args.database,
                target_database=args.database
            )
            
            async with DataMigrationManager(config) as migration_manager:
                collections = await migration_manager.source_db.list_collection_names()
                
                logger.info(f"📊 Found {len(collections)} collections:")
                
                for collection_name in sorted(collections):
                    collection = migration_manager.source_db[collection_name]
                    doc_count = await collection.count_documents({})
                    logger.info(f"  - {collection_name}: {doc_count} documents")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return False
    
    async def _generate_migration_report(self, results: list, output_path: str = None):
        """Generate detailed migration report."""
        try:
            report = {
                "migration_timestamp": datetime.utcnow().isoformat(),
                "total_steps": len(results),
                "successful_steps": sum(1 for _, result in results if result.success),
                "failed_steps": sum(1 for _, result in results if not result.success),
                "total_records_processed": sum(result.records_processed for _, result in results),
                "total_records_migrated": sum(result.records_migrated for _, result in results),
                "total_records_failed": sum(result.records_failed for _, result in results),
                "total_duration_seconds": sum(result.duration_seconds for _, result in results),
                "steps": []
            }
            
            for step_name, result in results:
                step_report = {
                    "step": step_name,
                    "success": result.success,
                    "message": result.message,
                    "records_processed": result.records_processed,
                    "records_migrated": result.records_migrated,
                    "records_failed": result.records_failed,
                    "duration_seconds": result.duration_seconds,
                    "errors": result.errors[:50] if result.errors else [],  # Limit errors
                    "warnings": result.warnings[:50] if result.warnings else []  # Limit warnings
                }
                report["steps"].append(step_report)
            
            # Save report
            if output_path:
                report_path = Path(output_path)
            else:
                report_path = Path(f"migration_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📄 Migration report saved to: {report_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate migration report: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Data migration utility for Infra Mind",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate from demo to production database
  python scripts/migrate_data.py migrate --source infra_mind_demo --target infra_mind_prod
  
  # Dry run migration to test without changes
  python scripts/migrate_data.py migrate --source demo_db --target prod_db --dry-run
  
  # Validate data structure
  python scripts/migrate_data.py validate --database infra_mind_demo
  
  # Rollback migration
  python scripts/migrate_data.py rollback --target infra_mind_prod --backup-path ./backups/migration_20240101_120000
  
  # List collections in database
  python scripts/migrate_data.py list --database infra_mind_demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Execute data migration')
    migrate_parser.add_argument('--source', required=True, help='Source database name')
    migrate_parser.add_argument('--target', required=True, help='Target database name')
    migrate_parser.add_argument('--backup-path', help='Custom backup directory path')
    migrate_parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    migrate_parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    migrate_parser.add_argument('--no-validation', action='store_true', help='Skip data validation')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Test migration without changes')
    migrate_parser.add_argument('--preserve-ids', action='store_true', help='Preserve document IDs')
    migrate_parser.add_argument('--skip-existing', action='store_true', default=True, help='Skip existing documents')
    migrate_parser.add_argument('--rollback-on-error', action='store_true', default=True, help='Rollback on error')
    migrate_parser.add_argument('--output-report', help='Output path for migration report')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate data structure')
    validate_parser.add_argument('--database', required=True, help='Database name to validate')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migration')
    rollback_parser.add_argument('--target', required=True, help='Target database to rollback')
    rollback_parser.add_argument('--backup-path', required=True, help='Backup directory path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List collections in database')
    list_parser.add_argument('--database', required=True, help='Database name to list')
    
    return parser


async def main():
    """Main entry point for migration CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    # Add file logging for migration operations
    if args.command in ['migrate', 'rollback']:
        log_file = f"migration_{args.command}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        logger.add(log_file, level="DEBUG", rotation="10 MB")
        logger.info(f"📝 Detailed logs will be saved to: {log_file}")
    
    cli = MigrationCLI()
    
    try:
        if args.command == 'migrate':
            success = await cli.migrate_data(args)
        elif args.command == 'validate':
            success = await cli.validate_data(args)
        elif args.command == 'rollback':
            success = await cli.rollback_migration(args)
        elif args.command == 'list':
            success = await cli.list_collections(args)
        else:
            logger.error(f"❌ Unknown command: {args.command}")
            return 1
        
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