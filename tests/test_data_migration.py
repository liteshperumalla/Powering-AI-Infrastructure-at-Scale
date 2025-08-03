"""
Comprehensive tests for data migration utilities.

Tests cover:
- Migration manager functionality
- Data transformation accuracy
- Backup and rollback procedures
- Data validation and integrity checks
- Error handling and recovery
"""

import pytest
import asyncio
import tempfile
import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import bson

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.data_migration import (
    DataMigrationManager,
    MigrationConfig,
    MigrationResult,
    MigrationStatus,
    MigrationStep,
    transform_user_document,
    transform_assessment_document,
    transform_recommendation_document,
    transform_report_document,
    transform_metrics_document
)
from infra_mind.models import User, Assessment, Recommendation, Report, Metric


class TestDataMigrationManager:
    """Test suite for DataMigrationManager."""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def migration_config(self, temp_backup_dir):
        """Create test migration configuration."""
        return MigrationConfig(
            source_database="test_source",
            target_database="test_target",
            backup_path=temp_backup_dir,
            batch_size=10,
            dry_run=True
        )
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database for testing."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        
        # Mock collection methods
        mock_collection.count_documents = AsyncMock(return_value=5)
        mock_collection.find = MagicMock()
        mock_collection.insert_many = AsyncMock()
        mock_collection.replace_one = AsyncMock()
        mock_collection.delete_many = AsyncMock()
        
        # Mock database methods
        mock_db.list_collection_names = AsyncMock(return_value=["users", "assessments"])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        
        return mock_db
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return {
            "users": [
                {
                    "_id": bson.ObjectId(),
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "hashed_password": "hashed_password_123",
                    "is_active": True,
                    "created_at": datetime.utcnow()
                },
                {
                    "_id": bson.ObjectId(),
                    "email": "user2@example.com",
                    "full_name": "User Two",
                    "hashed_password": "hashed_password_456",
                    "is_active": True,
                    "created_at": datetime.utcnow()
                }
            ],
            "assessments": [
                {
                    "_id": bson.ObjectId(),
                    "user_id": "user123",
                    "title": "Test Assessment",
                    "status": "completed",
                    "business_requirements": {"industry": "technology"},
                    "technical_requirements": {"cloud_provider": "aws"},
                    "created_at": datetime.utcnow()
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_migration_manager_initialization(self, migration_config):
        """Test migration manager initialization."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient') as mock_client:
            mock_client.return_value.admin.command = AsyncMock()
            
            async with DataMigrationManager(migration_config) as manager:
                assert manager.config == migration_config
                assert manager.migration_log == []
                assert manager.backup_metadata == {}
    
    @pytest.mark.asyncio
    async def test_create_backup_success(self, migration_config, mock_database, sample_documents):
        """Test successful backup creation."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.source_db = mock_database
            
            # Mock document iteration
            async def mock_find():
                for doc in sample_documents["users"]:
                    yield doc
            
            mock_database["users"].find.return_value.__aiter__ = mock_find
            mock_database["assessments"].find.return_value.__aiter__ = lambda: iter([])
            
            result = await manager.create_backup()
            
            assert result.success
            assert result.records_processed > 0
            assert "Backup completed successfully" in result.message
            
            # Check backup files were created
            backup_path = Path(migration_config.backup_path)
            assert (backup_path / "backup_metadata.json").exists()
    
    @pytest.mark.asyncio
    async def test_create_backup_disabled(self, temp_backup_dir):
        """Test backup creation when disabled."""
        config = MigrationConfig(
            source_database="test",
            target_database="test",
            backup_enabled=False
        )
        
        manager = DataMigrationManager(config)
        result = await manager.create_backup()
        
        assert result.success
        assert "Backup skipped" in result.message
        assert result.duration_seconds == 0.0
    
    @pytest.mark.asyncio
    async def test_validate_source_data_success(self, migration_config, mock_database, sample_documents):
        """Test successful source data validation."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.source_db = mock_database
            
            # Mock validation methods
            manager._validate_user_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Users valid", records_processed=2
            ))
            manager._validate_assessment_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Assessments valid", records_processed=1
            ))
            manager._validate_recommendation_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Recommendations valid", records_processed=0
            ))
            manager._validate_report_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Reports valid", records_processed=0
            ))
            manager._validate_metrics_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Metrics valid", records_processed=0
            ))
            
            result = await manager.validate_source_data()
            
            assert result.success
            assert "validation completed successfully" in result.message
            assert result.records_processed >= 0
    
    @pytest.mark.asyncio
    async def test_validate_source_data_with_errors(self, migration_config, mock_database):
        """Test source data validation with errors."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.source_db = mock_database
            
            # Mock validation with errors
            manager._validate_user_collection = AsyncMock(return_value=MigrationResult(
                success=False, 
                message="Users invalid", 
                errors=["Missing email field", "Invalid password hash"]
            ))
            manager._validate_assessment_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Assessments valid"
            ))
            manager._validate_recommendation_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Recommendations valid"
            ))
            manager._validate_report_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Reports valid"
            ))
            manager._validate_metrics_collection = AsyncMock(return_value=MigrationResult(
                success=True, message="Metrics valid"
            ))
            
            result = await manager.validate_source_data()
            
            assert not result.success
            assert "validation failed" in result.message
            assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_migrate_collection_success(self, migration_config, mock_database, sample_documents):
        """Test successful collection migration."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.source_db = mock_database
            manager.target_db = mock_database
            
            # Mock document batches
            async def mock_get_batches(collection, batch_size):
                yield sample_documents["users"]
            
            manager._get_document_batches = mock_get_batches
            
            # Mock transformer
            async def mock_transformer(doc):
                return doc  # Return document unchanged
            
            result = await manager.migrate_collection(
                collection_name="users",
                transformer_func=mock_transformer,
                target_model=User
            )
            
            assert result.success
            assert result.records_processed == len(sample_documents["users"])
    
    @pytest.mark.asyncio
    async def test_migrate_collection_with_validation_errors(self, migration_config, mock_database, sample_documents):
        """Test collection migration with validation errors."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.source_db = mock_database
            manager.target_db = mock_database
            
            # Mock document batches
            async def mock_get_batches(collection, batch_size):
                yield sample_documents["users"]
            
            manager._get_document_batches = mock_get_batches
            
            # Mock transformer that returns invalid data
            async def mock_transformer(doc):
                return {"invalid": "data"}  # Missing required fields
            
            result = await manager.migrate_collection(
                collection_name="users",
                transformer_func=mock_transformer,
                target_model=User
            )
            
            # Should have validation errors but still be considered successful if some records processed
            assert result.records_failed > 0
            assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_rollback_migration_success(self, migration_config, mock_database, temp_backup_dir):
        """Test successful migration rollback."""
        # Create mock backup files
        backup_path = Path(temp_backup_dir)
        
        # Create sample backup data
        users_backup = [
            {
                "_id": {"$oid": str(bson.ObjectId())},
                "email": "test@example.com",
                "full_name": "Test User"
            }
        ]
        
        with open(backup_path / "users.json", 'w') as f:
            json.dump(users_backup, f)
        
        # Create backup metadata
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "source_database": "test_source",
            "collections": {
                "users": {
                    "document_count": 1,
                    "file_path": str(backup_path / "users.json"),
                    "file_hash": "dummy_hash",
                    "backup_time": datetime.utcnow().isoformat()
                }
            },
            "total_records": 1
        }
        
        with open(backup_path / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            manager.target_db = mock_database
            
            # Mock file hash calculation
            manager._calculate_file_hash = MagicMock(return_value="dummy_hash")
            
            result = await manager.rollback_migration()
            
            assert result.success
            assert "rollback completed successfully" in result.message
            assert result.records_migrated > 0
    
    @pytest.mark.asyncio
    async def test_rollback_migration_no_backup(self, migration_config):
        """Test rollback when no backup exists."""
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            manager = DataMigrationManager(migration_config)
            
            result = await manager.rollback_migration()
            
            assert not result.success
            assert "No backup metadata found" in result.message
    
    def test_serialize_deserialize_document(self, migration_config):
        """Test document serialization and deserialization."""
        manager = DataMigrationManager(migration_config)
        
        # Test document with various data types
        original_doc = {
            "_id": bson.ObjectId(),
            "name": "Test",
            "created_at": datetime.utcnow(),
            "nested": {
                "id": bson.ObjectId(),
                "date": datetime.utcnow()
            },
            "list": [
                {"id": bson.ObjectId()},
                "string_item"
            ]
        }
        
        # Serialize and deserialize
        serialized = manager._serialize_document(original_doc)
        deserialized = manager._deserialize_document(serialized)
        
        # Check that ObjectIds and datetimes are properly handled
        assert isinstance(deserialized["_id"], bson.ObjectId)
        assert isinstance(deserialized["created_at"], datetime)
        assert isinstance(deserialized["nested"]["id"], bson.ObjectId)
        assert isinstance(deserialized["nested"]["date"], datetime)
        assert isinstance(deserialized["list"][0]["id"], bson.ObjectId)
    
    def test_log_migration_step(self, migration_config):
        """Test migration step logging."""
        manager = DataMigrationManager(migration_config)
        
        manager.log_migration_step(
            MigrationStep.BACKUP,
            "started",
            {"detail": "test"}
        )
        
        assert len(manager.migration_log) == 1
        log_entry = manager.migration_log[0]
        assert log_entry["step"] == "backup"
        assert log_entry["status"] == "started"
        assert log_entry["details"]["detail"] == "test"


class TestDataTransformers:
    """Test suite for data transformation functions."""
    
    @pytest.mark.asyncio
    async def test_transform_user_document(self):
        """Test user document transformation."""
        source_doc = {
            "_id": bson.ObjectId(),
            "email": "TEST@EXAMPLE.COM",
            "full_name": "Test User",
            "hashed_password": "hashed123",
            "is_active": True,
            "company_name": "Test Corp",
            "created_at": datetime.utcnow()
        }
        
        transformed = await transform_user_document(source_doc)
        
        assert transformed["email"] == "test@example.com"  # Should be lowercase
        assert transformed["full_name"] == "Test User"
        assert transformed["is_active"] is True
        assert transformed["company_name"] == "Test Corp"
        assert "created_at" in transformed
        assert "updated_at" in transformed
    
    @pytest.mark.asyncio
    async def test_transform_user_document_with_defaults(self):
        """Test user document transformation with default values."""
        source_doc = {
            "_id": bson.ObjectId(),
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        transformed = await transform_user_document(source_doc)
        
        assert transformed["email"] == "test@example.com"
        assert transformed["role"] == "user"  # Default role
        assert transformed["login_count"] == 0  # Default login count
        assert transformed["assessments_created"] == 0  # Default assessments
        assert "notification_preferences" in transformed
    
    @pytest.mark.asyncio
    async def test_transform_assessment_document(self):
        """Test assessment document transformation."""
        source_doc = {
            "_id": bson.ObjectId(),
            "user_id": "user123",
            "title": "Test Assessment",
            "status": "completed",
            "business_requirements": {"industry": "tech"},
            "technical_requirements": {"cloud": "aws"},
            "created_at": datetime.utcnow()
        }
        
        transformed = await transform_assessment_document(source_doc)
        
        assert transformed["user_id"] == "user123"
        assert transformed["title"] == "Test Assessment"
        assert transformed["status"] == "completed"
        assert transformed["business_requirements"]["industry"] == "tech"
        assert transformed["priority"] == "medium"  # Default priority
        assert transformed["completion_percentage"] == 0.0  # Default completion
    
    @pytest.mark.asyncio
    async def test_transform_recommendation_document(self):
        """Test recommendation document transformation."""
        source_doc = {
            "_id": bson.ObjectId(),
            "assessment_id": "assessment123",
            "agent_name": "cto_agent",
            "title": "Test Recommendation",
            "description": "Test description",
            "confidence_score": 0.8,
            "created_at": datetime.utcnow()
        }
        
        transformed = await transform_recommendation_document(source_doc)
        
        assert transformed["assessment_id"] == "assessment123"
        assert transformed["agent_name"] == "cto_agent"
        assert transformed["title"] == "Test Recommendation"
        assert transformed["confidence_score"] == 0.8
        assert transformed["category"] == "general"  # Default category
        assert transformed["priority"] == "medium"  # Default priority
    
    @pytest.mark.asyncio
    async def test_transform_report_document(self):
        """Test report document transformation."""
        source_doc = {
            "_id": bson.ObjectId(),
            "assessment_id": "assessment123",
            "user_id": "user123",
            "title": "Test Report",
            "report_type": "executive_summary",
            "status": "completed",
            "created_at": datetime.utcnow()
        }
        
        transformed = await transform_report_document(source_doc)
        
        assert transformed["assessment_id"] == "assessment123"
        assert transformed["user_id"] == "user123"
        assert transformed["title"] == "Test Report"
        assert transformed["report_type"] == "executive_summary"
        assert transformed["version"] == "1.0"  # Default version
        assert transformed["format"] == "pdf"  # Default format
    
    @pytest.mark.asyncio
    async def test_transform_metrics_document(self):
        """Test metrics document transformation."""
        source_doc = {
            "_id": bson.ObjectId(),
            "metric_name": "api_requests",
            "value": 100,
            "timestamp": datetime.utcnow()
        }
        
        transformed = await transform_metrics_document(source_doc)
        
        assert transformed["metric_name"] == "api_requests"
        assert transformed["value"] == 100
        assert transformed["metric_type"] == "counter"  # Default type
        assert transformed["unit"] == "count"  # Default unit
        assert transformed["source"] == "system"  # Default source
    
    @pytest.mark.asyncio
    async def test_transform_document_removes_none_values(self):
        """Test that transformation removes None values."""
        source_doc = {
            "_id": bson.ObjectId(),
            "email": "test@example.com",
            "full_name": "Test User",
            "company_name": None,
            "job_title": None
        }
        
        transformed = await transform_user_document(source_doc)
        
        assert "company_name" not in transformed
        assert "job_title" not in transformed
        assert "email" in transformed
        assert "full_name" in transformed


class TestMigrationConfig:
    """Test suite for MigrationConfig."""
    
    def test_migration_config_defaults(self):
        """Test migration config default values."""
        config = MigrationConfig(
            source_database="source",
            target_database="target"
        )
        
        assert config.backup_enabled is True
        assert config.batch_size == 1000
        assert config.validate_data is True
        assert config.dry_run is False
        assert config.preserve_ids is False
        assert config.skip_existing is True
        assert config.rollback_on_error is True
        assert config.backup_path is not None
    
    def test_migration_config_custom_backup_path(self):
        """Test migration config with custom backup path."""
        custom_path = "/custom/backup/path"
        config = MigrationConfig(
            source_database="source",
            target_database="target",
            backup_path=custom_path
        )
        
        assert config.backup_path == custom_path


class TestMigrationResult:
    """Test suite for MigrationResult."""
    
    def test_migration_result_defaults(self):
        """Test migration result default values."""
        result = MigrationResult(
            success=True,
            message="Test message"
        )
        
        assert result.success is True
        assert result.message == "Test message"
        assert result.records_processed == 0
        assert result.records_migrated == 0
        assert result.records_failed == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.duration_seconds == 0.0
    
    def test_migration_result_with_errors(self):
        """Test migration result with errors and warnings."""
        result = MigrationResult(
            success=False,
            message="Failed",
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        assert result.success is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


@pytest.mark.integration
class TestMigrationIntegration:
    """Integration tests for migration functionality."""
    
    @pytest.mark.asyncio
    async def test_full_migration_workflow(self):
        """Test complete migration workflow."""
        # This would require actual database connections
        # For now, we'll test the workflow structure
        
        config = MigrationConfig(
            source_database="test_source",
            target_database="test_target",
            dry_run=True
        )
        
        # Test that the workflow can be instantiated
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient'):
            async with DataMigrationManager(config) as manager:
                assert manager is not None
                assert manager.config == config
    
    @pytest.mark.asyncio
    async def test_migration_error_handling(self):
        """Test migration error handling and recovery."""
        config = MigrationConfig(
            source_database="nonexistent",
            target_database="nonexistent",
            rollback_on_error=True
        )
        
        # Test that errors are properly handled
        with patch('infra_mind.core.data_migration.AsyncIOMotorClient') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                async with DataMigrationManager(config) as manager:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])