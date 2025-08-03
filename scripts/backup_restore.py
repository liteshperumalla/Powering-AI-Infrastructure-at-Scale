#!/usr/bin/env python3
"""
Database backup and restore utility for Infra Mind.

This script provides comprehensive backup and restore capabilities
for MongoDB databases with integrity verification and compression.

Usage:
    python scripts/backup_restore.py backup --database infra_mind --output ./backups/
    python scripts/backup_restore.py restore --database infra_mind --backup ./backups/backup_20240101_120000/
    python scripts/backup_restore.py verify --backup ./backups/backup_20240101_120000/
    python scripts/backup_restore.py list --directory ./backups/
"""

import asyncio
import argparse
import sys
import json
import gzip
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import tarfile
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.database import db, init_database
from infra_mind.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import bson


class BackupRestoreManager:
    """
    Comprehensive backup and restore manager for MongoDB databases.
    
    Features:
    - Full database backup with compression
    - Selective collection backup/restore
    - Integrity verification with checksums
    - Incremental backup support
    - Backup metadata and cataloging
    """
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
    
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
    
    async def create_backup(
        self, 
        output_path: str, 
        collections: Optional[List[str]] = None,
        compress: bool = True,
        include_indexes: bool = True
    ) -> Dict[str, Any]:
        """
        Create comprehensive database backup.
        
        Args:
            output_path: Directory to store backup
            collections: Specific collections to backup (None for all)
            compress: Whether to compress backup files
            include_indexes: Whether to include index definitions
        
        Returns:
            Backup metadata dictionary
        """
        start_time = datetime.utcnow()
        backup_id = f"backup_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"📦 Creating backup: {backup_id}")
            
            # Create backup directory
            backup_path = Path(output_path) / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Get collections to backup
            if collections is None:
                collections = await self.database.list_collection_names()
            
            logger.info(f"📊 Backing up {len(collections)} collections")
            
            backup_metadata = {
                "backup_id": backup_id,
                "database_name": self.database_name,
                "timestamp": start_time.isoformat(),
                "collections": {},
                "total_documents": 0,
                "total_size_bytes": 0,
                "compressed": compress,
                "includes_indexes": include_indexes,
                "version": "1.0"
            }
            
            total_documents = 0
            total_size = 0
            
            # Backup each collection
            for collection_name in collections:
                try:
                    collection_result = await self._backup_collection(
                        collection_name=collection_name,
                        backup_path=backup_path,
                        compress=compress,
                        include_indexes=include_indexes
                    )
                    
                    backup_metadata["collections"][collection_name] = collection_result
                    total_documents += collection_result["document_count"]
                    total_size += collection_result["file_size_bytes"]
                    
                    logger.info(f"✅ Backed up {collection_name}: {collection_result['document_count']} documents")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to backup collection {collection_name}: {e}")
                    backup_metadata["collections"][collection_name] = {
                        "error": str(e),
                        "document_count": 0,
                        "file_size_bytes": 0
                    }
            
            backup_metadata["total_documents"] = total_documents
            backup_metadata["total_size_bytes"] = total_size
            backup_metadata["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Save backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, indent=2, default=str)
            
            # Create backup archive if requested
            if compress:
                archive_path = await self._create_backup_archive(backup_path)
                backup_metadata["archive_path"] = str(archive_path)
                backup_metadata["archive_size_bytes"] = archive_path.stat().st_size
            
            logger.success(f"✅ Backup completed: {backup_id}")
            logger.info(f"📊 Total: {total_documents} documents, {total_size / 1024 / 1024:.2f} MB")
            
            return backup_metadata
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise
    
    async def _backup_collection(
        self, 
        collection_name: str, 
        backup_path: Path,
        compress: bool,
        include_indexes: bool
    ) -> Dict[str, Any]:
        """Backup a single collection."""
        collection = self.database[collection_name]
        
        # Count documents
        doc_count = await collection.count_documents({})
        if doc_count == 0:
            return {
                "document_count": 0,
                "file_size_bytes": 0,
                "file_path": None,
                "checksum": None
            }
        
        # Prepare output file
        if compress:
            output_file = backup_path / f"{collection_name}.json.gz"
            file_handle = gzip.open(output_file, 'wt', encoding='utf-8')
        else:
            output_file = backup_path / f"{collection_name}.json"
            file_handle = open(output_file, 'w', encoding='utf-8')
        
        try:
            documents = []
            
            # Export documents
            async for doc in collection.find():
                # Convert ObjectId and datetime for JSON serialization
                serialized_doc = self._serialize_document(doc)
                documents.append(serialized_doc)
            
            # Write documents to file
            json.dump(documents, file_handle, indent=2, default=str)
            
            # Backup indexes if requested
            if include_indexes:
                indexes = await collection.list_indexes().to_list(length=None)
                index_file = backup_path / f"{collection_name}_indexes.json"
                
                if compress:
                    with gzip.open(f"{index_file}.gz", 'wt', encoding='utf-8') as idx_f:
                        json.dump(indexes, idx_f, indent=2, default=str)
                else:
                    with open(index_file, 'w', encoding='utf-8') as idx_f:
                        json.dump(indexes, idx_f, indent=2, default=str)
        
        finally:
            file_handle.close()
        
        # Calculate file checksum
        checksum = self._calculate_file_checksum(output_file)
        file_size = output_file.stat().st_size
        
        return {
            "document_count": doc_count,
            "file_path": str(output_file),
            "file_size_bytes": file_size,
            "checksum": checksum,
            "compressed": compress,
            "backup_time": datetime.utcnow().isoformat()
        }
    
    async def restore_backup(
        self, 
        backup_path: str,
        collections: Optional[List[str]] = None,
        drop_existing: bool = False,
        verify_checksums: bool = True
    ) -> Dict[str, Any]:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup directory or archive
            collections: Specific collections to restore (None for all)
            drop_existing: Whether to drop existing collections before restore
            verify_checksums: Whether to verify file checksums before restore
        
        Returns:
            Restore result metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔄 Starting database restore from: {backup_path}")
            
            # Handle backup archive extraction
            backup_dir = Path(backup_path)
            if backup_dir.is_file() and backup_dir.suffix in ['.tar', '.gz', '.tgz']:
                backup_dir = await self._extract_backup_archive(backup_path)
            
            # Load backup metadata
            metadata_file = backup_dir / "backup_metadata.json"
            if not metadata_file.exists():
                raise FileNotFoundError("Backup metadata file not found")
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)
            
            logger.info(f"📋 Backup info: {backup_metadata['backup_id']} from {backup_metadata['timestamp']}")
            
            # Determine collections to restore
            available_collections = list(backup_metadata["collections"].keys())
            if collections is None:
                collections = available_collections
            else:
                # Validate requested collections exist in backup
                missing = set(collections) - set(available_collections)
                if missing:
                    logger.warning(f"⚠️ Collections not found in backup: {missing}")
                    collections = [c for c in collections if c in available_collections]
            
            logger.info(f"🔄 Restoring {len(collections)} collections")
            
            restore_results = {
                "restore_id": f"restore_{start_time.strftime('%Y%m%d_%H%M%S')}",
                "backup_id": backup_metadata["backup_id"],
                "database_name": self.database_name,
                "timestamp": start_time.isoformat(),
                "collections": {},
                "total_documents_restored": 0,
                "errors": []
            }
            
            total_restored = 0
            
            # Restore each collection
            for collection_name in collections:
                try:
                    if collection_name not in backup_metadata["collections"]:
                        logger.warning(f"⚠️ Collection {collection_name} not found in backup")
                        continue
                    
                    collection_metadata = backup_metadata["collections"][collection_name]
                    if "error" in collection_metadata:
                        logger.warning(f"⚠️ Skipping {collection_name} (backup error: {collection_metadata['error']})")
                        continue
                    
                    result = await self._restore_collection(
                        collection_name=collection_name,
                        backup_dir=backup_dir,
                        collection_metadata=collection_metadata,
                        drop_existing=drop_existing,
                        verify_checksum=verify_checksums
                    )
                    
                    restore_results["collections"][collection_name] = result
                    total_restored += result["documents_restored"]
                    
                    logger.info(f"✅ Restored {collection_name}: {result['documents_restored']} documents")
                    
                except Exception as e:
                    error_msg = f"Failed to restore collection {collection_name}: {e}"
                    logger.error(f"❌ {error_msg}")
                    restore_results["errors"].append(error_msg)
                    restore_results["collections"][collection_name] = {
                        "error": str(e),
                        "documents_restored": 0
                    }
            
            restore_results["total_documents_restored"] = total_restored
            restore_results["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.success(f"✅ Restore completed: {total_restored} documents restored")
            
            return restore_results
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            raise
    
    async def _restore_collection(
        self,
        collection_name: str,
        backup_dir: Path,
        collection_metadata: Dict[str, Any],
        drop_existing: bool,
        verify_checksum: bool
    ) -> Dict[str, Any]:
        """Restore a single collection."""
        collection = self.database[collection_name]
        
        # Determine backup file path
        backup_file = Path(collection_metadata["file_path"])
        if not backup_file.is_absolute():
            backup_file = backup_dir / backup_file.name
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Verify checksum if requested
        if verify_checksum and "checksum" in collection_metadata:
            current_checksum = self._calculate_file_checksum(backup_file)
            expected_checksum = collection_metadata["checksum"]
            
            if current_checksum != expected_checksum:
                raise ValueError(f"Checksum mismatch for {collection_name}: expected {expected_checksum}, got {current_checksum}")
        
        # Drop existing collection if requested
        if drop_existing:
            await collection.drop()
            logger.info(f"🗑️ Dropped existing collection: {collection_name}")
        
        # Load and restore documents
        if backup_file.suffix == '.gz':
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                documents = json.load(f)
        else:
            with open(backup_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
        
        if not documents:
            return {"documents_restored": 0}
        
        # Deserialize documents
        restored_docs = [self._deserialize_document(doc) for doc in documents]
        
        # Insert documents in batches
        batch_size = 1000
        documents_restored = 0
        
        for i in range(0, len(restored_docs), batch_size):
            batch = restored_docs[i:i + batch_size]
            try:
                await collection.insert_many(batch, ordered=False)
                documents_restored += len(batch)
            except Exception as e:
                logger.warning(f"⚠️ Batch insert error for {collection_name}: {e}")
                # Try individual inserts for failed batch
                for doc in batch:
                    try:
                        await collection.insert_one(doc)
                        documents_restored += 1
                    except Exception:
                        pass  # Skip failed documents
        
        # Restore indexes if available
        index_file = backup_dir / f"{collection_name}_indexes.json"
        if not index_file.exists():
            index_file = backup_dir / f"{collection_name}_indexes.json.gz"
        
        if index_file.exists():
            try:
                await self._restore_collection_indexes(collection, index_file)
                logger.info(f"📊 Restored indexes for {collection_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to restore indexes for {collection_name}: {e}")
        
        return {
            "documents_restored": documents_restored,
            "restore_time": datetime.utcnow().isoformat()
        }
    
    async def _restore_collection_indexes(self, collection, index_file: Path):
        """Restore collection indexes."""
        if index_file.suffix == '.gz':
            with gzip.open(index_file, 'rt', encoding='utf-8') as f:
                indexes = json.load(f)
        else:
            with open(index_file, 'r', encoding='utf-8') as f:
                indexes = json.load(f)
        
        for index in indexes:
            if index.get("name") == "_id_":
                continue  # Skip default _id index
            
            try:
                # Extract index specification
                key = index.get("key", {})
                options = {k: v for k, v in index.items() if k not in ["key", "v", "ns"]}
                
                await collection.create_index(list(key.items()), **options)
            except Exception as e:
                logger.warning(f"⚠️ Failed to create index {index.get('name', 'unknown')}: {e}")
    
    async def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup integrity and completeness."""
        try:
            logger.info(f"🔍 Verifying backup: {backup_path}")
            
            backup_dir = Path(backup_path)
            if backup_dir.is_file():
                backup_dir = await self._extract_backup_archive(backup_path)
            
            # Load metadata
            metadata_file = backup_dir / "backup_metadata.json"
            if not metadata_file.exists():
                return {"valid": False, "error": "Backup metadata file not found"}
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            verification_result = {
                "backup_id": metadata["backup_id"],
                "valid": True,
                "errors": [],
                "warnings": [],
                "collections_verified": 0,
                "total_collections": len(metadata["collections"])
            }
            
            # Verify each collection
            for collection_name, collection_metadata in metadata["collections"].items():
                if "error" in collection_metadata:
                    verification_result["warnings"].append(f"Collection {collection_name} has backup error")
                    continue
                
                # Check file exists
                backup_file = backup_dir / Path(collection_metadata["file_path"]).name
                if not backup_file.exists():
                    verification_result["errors"].append(f"Backup file missing for {collection_name}")
                    continue
                
                # Verify checksum
                if "checksum" in collection_metadata:
                    current_checksum = self._calculate_file_checksum(backup_file)
                    expected_checksum = collection_metadata["checksum"]
                    
                    if current_checksum != expected_checksum:
                        verification_result["errors"].append(f"Checksum mismatch for {collection_name}")
                        continue
                
                verification_result["collections_verified"] += 1
            
            verification_result["valid"] = len(verification_result["errors"]) == 0
            
            if verification_result["valid"]:
                logger.success(f"✅ Backup verification passed: {verification_result['collections_verified']} collections verified")
            else:
                logger.error(f"❌ Backup verification failed: {len(verification_result['errors'])} errors")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"❌ Backup verification failed: {e}")
            return {"valid": False, "error": str(e)}
    
    async def list_backups(self, backup_directory: str) -> List[Dict[str, Any]]:
        """List available backups in a directory."""
        try:
            backup_dir = Path(backup_directory)
            if not backup_dir.exists():
                return []
            
            backups = []
            
            # Find backup directories and archives
            for item in backup_dir.iterdir():
                if item.is_dir() and item.name.startswith("backup_"):
                    metadata_file = item / "backup_metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            backups.append({
                                "backup_id": metadata["backup_id"],
                                "database_name": metadata["database_name"],
                                "timestamp": metadata["timestamp"],
                                "total_documents": metadata["total_documents"],
                                "total_size_bytes": metadata["total_size_bytes"],
                                "path": str(item),
                                "type": "directory"
                            })
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to read backup metadata from {item}: {e}")
                
                elif item.is_file() and item.suffix in ['.tar', '.gz', '.tgz']:
                    # TODO: Extract metadata from archive without full extraction
                    backups.append({
                        "backup_id": item.stem,
                        "path": str(item),
                        "type": "archive",
                        "size_bytes": item.stat().st_size
                    })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"❌ Failed to list backups: {e}")
            return []
    
    # Helper methods
    
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
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def _create_backup_archive(self, backup_path: Path) -> Path:
        """Create compressed archive of backup directory."""
        archive_path = backup_path.parent / f"{backup_path.name}.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # Remove original directory after archiving
        shutil.rmtree(backup_path)
        
        return archive_path
    
    async def _extract_backup_archive(self, archive_path: str) -> Path:
        """Extract backup archive to temporary directory."""
        archive_file = Path(archive_path)
        temp_dir = Path(tempfile.mkdtemp())
        
        with tarfile.open(archive_file, "r:*") as tar:
            tar.extractall(temp_dir)
        
        # Find the extracted backup directory
        extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        if not extracted_dirs:
            raise ValueError("No backup directory found in archive")
        
        return extracted_dirs[0]


async def main():
    """Main entry point for backup/restore CLI."""
    parser = argparse.ArgumentParser(
        description="Database backup and restore utility for Infra Mind",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--database', required=True, help='Database name to backup')
    backup_parser.add_argument('--output', required=True, help='Output directory for backup')
    backup_parser.add_argument('--collections', nargs='*', help='Specific collections to backup')
    backup_parser.add_argument('--no-compress', action='store_true', help='Disable compression')
    backup_parser.add_argument('--no-indexes', action='store_true', help='Skip index backup')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('--database', required=True, help='Target database name')
    restore_parser.add_argument('--backup', required=True, help='Backup directory or archive path')
    restore_parser.add_argument('--collections', nargs='*', help='Specific collections to restore')
    restore_parser.add_argument('--drop-existing', action='store_true', help='Drop existing collections')
    restore_parser.add_argument('--no-verify', action='store_true', help='Skip checksum verification')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('--backup', required=True, help='Backup directory or archive path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--directory', required=True, help='Backup directory to scan')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    try:
        if args.command == 'backup':
            async with BackupRestoreManager(args.database) as manager:
                result = await manager.create_backup(
                    output_path=args.output,
                    collections=args.collections,
                    compress=not args.no_compress,
                    include_indexes=not args.no_indexes
                )
                logger.info(f"📄 Backup metadata: {json.dumps(result, indent=2, default=str)}")
        
        elif args.command == 'restore':
            async with BackupRestoreManager(args.database) as manager:
                result = await manager.restore_backup(
                    backup_path=args.backup,
                    collections=args.collections,
                    drop_existing=args.drop_existing,
                    verify_checksums=not args.no_verify
                )
                logger.info(f"📄 Restore result: {json.dumps(result, indent=2, default=str)}")
        
        elif args.command == 'verify':
            manager = BackupRestoreManager("dummy")  # Database connection not needed for verification
            result = await manager.verify_backup(args.backup)
            logger.info(f"📄 Verification result: {json.dumps(result, indent=2, default=str)}")
        
        elif args.command == 'list':
            manager = BackupRestoreManager("dummy")  # Database connection not needed for listing
            backups = await manager.list_backups(args.directory)
            
            if backups:
                logger.info(f"📋 Found {len(backups)} backups:")
                for backup in backups:
                    logger.info(f"  - {backup['backup_id']}: {backup.get('timestamp', 'unknown time')}")
            else:
                logger.info("📋 No backups found")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)