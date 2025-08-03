#!/usr/bin/env python3
"""
Production Database Initialization Script for Infra Mind

This script initializes the production database with:
- Proper collections and indexes
- User authentication and roles
- Performance optimization settings
- Data validation rules
- Backup configuration
"""

import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import WriteConcern, ReadPreference
from pymongo.errors import ConnectionFailure, OperationFailure
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.config import settings


class ProductionDatabaseInitializer:
    """Initialize production database with all required configurations."""
    
    def __init__(self):
        self.client = None
        self.database = None
        
    async def connect(self):
        """Establish connection to production database."""
        try:
            # Production MongoDB connection with SSL and authentication
            connection_options = {
                'maxPoolSize': settings.mongodb_max_connections,
                'minPoolSize': settings.mongodb_min_connections,
                'maxIdleTimeMS': 45000,
                'serverSelectionTimeoutMS': 10000,
                'socketTimeoutMS': 30000,
                'connectTimeoutMS': 10000,
                'heartbeatFrequencyMS': 10000,
                'retryWrites': True,
                'retryReads': True,
                'readPreference': ReadPreference.PRIMARY_PREFERRED,
                'w': 'majority',
                'j': True,
                'wtimeoutMS': 10000
            }
            
            # Add SSL configuration for production
            if settings.environment == 'production':
                connection_options.update({
                    'ssl': True,
                    'ssl_cert_reqs': 'CERT_REQUIRED',
                    'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt',
                    'authSource': 'admin'
                })
            
            logger.info("🔌 Connecting to production MongoDB...")
            # Handle SecretStr properly
            mongodb_url = str(settings.mongodb_url) if hasattr(settings.mongodb_url, 'get_secret_value') else settings.mongodb_url
            self.client = AsyncIOMotorClient(mongodb_url, **connection_options)
            
            # Test connection
            await asyncio.wait_for(
                self.client.admin.command('ping'),
                timeout=10.0
            )
            
            # Get database with write concern
            write_concern = WriteConcern(w="majority", j=True, wtimeout=10000)
            self.database = self.client.get_database(
                settings.mongodb_database,
                write_concern=write_concern
            )
            
            logger.success("✅ Successfully connected to production database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    async def create_collections(self):
        """Create all required collections with proper configuration."""
        collections = [
            {
                'name': 'assessments',
                'options': {
                    'validator': {
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'required': ['user_id', 'created_at', 'status'],
                            'properties': {
                                'user_id': {'bsonType': 'string'},
                                'created_at': {'bsonType': 'date'},
                                'status': {'enum': ['draft', 'in_progress', 'completed', 'archived']},
                                'assessment_data': {'bsonType': 'object'},
                                'recommendations': {'bsonType': 'array'}
                            }
                        }
                    }
                }
            },
            {
                'name': 'reports',
                'options': {
                    'validator': {
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'required': ['assessment_id', 'created_at', 'report_type'],
                            'properties': {
                                'assessment_id': {'bsonType': 'objectId'},
                                'created_at': {'bsonType': 'date'},
                                'report_type': {'enum': ['technical', 'executive', 'compliance']},
                                'content': {'bsonType': 'object'},
                                'metadata': {'bsonType': 'object'}
                            }
                        }
                    }
                }
            },
            {
                'name': 'users',
                'options': {
                    'validator': {
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'required': ['email', 'created_at', 'role'],
                            'properties': {
                                'email': {'bsonType': 'string'},
                                'created_at': {'bsonType': 'date'},
                                'role': {'enum': ['user', 'admin', 'analyst']},
                                'profile': {'bsonType': 'object'},
                                'preferences': {'bsonType': 'object'}
                            }
                        }
                    }
                }
            },
            {
                'name': 'agent_executions',
                'options': {
                    'validator': {
                        '$jsonSchema': {
                            'bsonType': 'object',
                            'required': ['agent_type', 'started_at', 'status'],
                            'properties': {
                                'agent_type': {'enum': ['cto', 'cloud_engineer', 'research', 'compliance', 'mlops']},
                                'started_at': {'bsonType': 'date'},
                                'status': {'enum': ['running', 'completed', 'failed', 'cancelled']},
                                'execution_data': {'bsonType': 'object'},
                                'results': {'bsonType': 'object'}
                            }
                        }
                    }
                }
            },
            {
                'name': 'audit_logs',
                'options': {
                    'capped': True,
                    'size': 100000000,  # 100MB
                    'max': 1000000      # 1M documents
                }
            }
        ]
        
        for collection_config in collections:
            try:
                collection_name = collection_config['name']
                options = collection_config.get('options', {})
                
                # Check if collection exists
                existing_collections = await self.database.list_collection_names()
                
                if collection_name not in existing_collections:
                    await self.database.create_collection(collection_name, **options)
                    logger.success(f"✅ Created collection: {collection_name}")
                else:
                    logger.info(f"📋 Collection already exists: {collection_name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to create collection {collection_name}: {e}")
    
    async def create_indexes(self):
        """Create optimized indexes for production performance."""
        index_configs = [
            # Assessments indexes
            {
                'collection': 'assessments',
                'indexes': [
                    {'keys': [('user_id', 1), ('created_at', -1)], 'name': 'user_assessments'},
                    {'keys': [('status', 1), ('created_at', -1)], 'name': 'status_timeline'},
                    {'keys': [('created_at', -1)], 'name': 'recent_assessments'},
                    {'keys': [('assessment_data.company_size', 1)], 'name': 'company_size_filter'},
                    {'keys': [('assessment_data.industry', 1)], 'name': 'industry_filter'}
                ]
            },
            # Reports indexes
            {
                'collection': 'reports',
                'indexes': [
                    {'keys': [('assessment_id', 1)], 'name': 'assessment_reports'},
                    {'keys': [('report_type', 1), ('created_at', -1)], 'name': 'report_type_timeline'},
                    {'keys': [('created_at', -1)], 'name': 'recent_reports'},
                    {'keys': [('metadata.tags', 1)], 'name': 'report_tags'}
                ]
            },
            # Users indexes
            {
                'collection': 'users',
                'indexes': [
                    {'keys': [('email', 1)], 'name': 'user_email', 'unique': True},
                    {'keys': [('role', 1), ('created_at', -1)], 'name': 'user_roles'},
                    {'keys': [('created_at', -1)], 'name': 'user_registration'}
                ]
            },
            # Agent executions indexes
            {
                'collection': 'agent_executions',
                'indexes': [
                    {'keys': [('agent_type', 1), ('started_at', -1)], 'name': 'agent_timeline'},
                    {'keys': [('status', 1), ('started_at', -1)], 'name': 'execution_status'},
                    {'keys': [('started_at', -1)], 'name': 'recent_executions'},
                    {'keys': [('execution_data.assessment_id', 1)], 'name': 'assessment_executions'}
                ]
            },
            # Audit logs indexes
            {
                'collection': 'audit_logs',
                'indexes': [
                    {'keys': [('timestamp', -1)], 'name': 'audit_timeline'},
                    {'keys': [('user_id', 1), ('timestamp', -1)], 'name': 'user_audit'},
                    {'keys': [('action', 1), ('timestamp', -1)], 'name': 'action_audit'}
                ]
            }
        ]
        
        for config in index_configs:
            collection_name = config['collection']
            collection = self.database[collection_name]
            
            for index_config in config['indexes']:
                try:
                    keys = index_config['keys']
                    options = {k: v for k, v in index_config.items() if k != 'keys'}
                    
                    await collection.create_index(keys, **options)
                    logger.success(f"✅ Created index {options.get('name', 'unnamed')} on {collection_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create index on {collection_name}: {e}")
    
    async def setup_database_users(self):
        """Set up database users and roles for production."""
        try:
            # Create application user with limited permissions
            app_user = {
                'user': 'infra_mind_app',
                'pwd': os.getenv('INFRA_MIND_DB_APP_PASSWORD', 'secure_app_password'),
                'roles': [
                    {'role': 'readWrite', 'db': settings.mongodb_database}
                ]
            }
            
            # Create read-only user for analytics
            readonly_user = {
                'user': 'infra_mind_readonly',
                'pwd': os.getenv('INFRA_MIND_DB_READONLY_PASSWORD', 'secure_readonly_password'),
                'roles': [
                    {'role': 'read', 'db': settings.mongodb_database}
                ]
            }
            
            # Create backup user
            backup_user = {
                'user': 'infra_mind_backup',
                'pwd': os.getenv('INFRA_MIND_DB_BACKUP_PASSWORD', 'secure_backup_password'),
                'roles': [
                    {'role': 'backup', 'db': 'admin'},
                    {'role': 'read', 'db': settings.mongodb_database}
                ]
            }
            
            users = [app_user, readonly_user, backup_user]
            
            for user_config in users:
                try:
                    await self.database.command('createUser', **user_config)
                    logger.success(f"✅ Created database user: {user_config['user']}")
                except OperationFailure as e:
                    if 'already exists' in str(e):
                        logger.info(f"👤 User already exists: {user_config['user']}")
                    else:
                        logger.error(f"❌ Failed to create user {user_config['user']}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to setup database users: {e}")
    
    async def configure_database_settings(self):
        """Configure production database settings."""
        try:
            # Set profiling level for performance monitoring
            await self.database.command('profile', 2, slowms=100)
            logger.success("✅ Enabled database profiling for slow queries")
            
            # Configure write concern
            await self.database.command('setDefaultRWConcern', {
                'defaultWriteConcern': {
                    'w': 'majority',
                    'j': True,
                    'wtimeout': 10000
                },
                'defaultReadConcern': {
                    'level': 'majority'
                }
            })
            logger.success("✅ Configured default read/write concerns")
            
        except Exception as e:
            logger.error(f"❌ Failed to configure database settings: {e}")
    
    async def verify_setup(self):
        """Verify that the database setup is correct."""
        try:
            # Check collections
            collections = await self.database.list_collection_names()
            expected_collections = ['assessments', 'reports', 'users', 'agent_executions', 'audit_logs']
            
            for collection in expected_collections:
                if collection in collections:
                    logger.success(f"✅ Collection verified: {collection}")
                else:
                    logger.error(f"❌ Missing collection: {collection}")
            
            # Check indexes
            for collection_name in expected_collections:
                collection = self.database[collection_name]
                indexes = await collection.list_indexes().to_list(length=None)
                logger.info(f"📊 {collection_name} has {len(indexes)} indexes")
            
            # Test write operation
            test_doc = {
                'test': True,
                'timestamp': datetime.utcnow(),
                'message': 'Database initialization test'
            }
            
            result = await self.database.test_collection.insert_one(test_doc)
            await self.database.test_collection.delete_one({'_id': result.inserted_id})
            logger.success("✅ Database write/read test passed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")
            return False
    
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("🔌 Database connection closed")


async def main():
    """Main initialization function."""
    logger.info("🚀 Starting production database initialization...")
    
    initializer = ProductionDatabaseInitializer()
    
    try:
        # Connect to database
        if not await initializer.connect():
            logger.error("❌ Failed to connect to database. Exiting.")
            sys.exit(1)
        
        # Create collections
        logger.info("📋 Creating collections...")
        await initializer.create_collections()
        
        # Create indexes
        logger.info("📊 Creating indexes...")
        await initializer.create_indexes()
        
        # Setup database users (only in production)
        if settings.environment == 'production':
            logger.info("👤 Setting up database users...")
            await initializer.setup_database_users()
        
        # Configure database settings
        logger.info("⚙️ Configuring database settings...")
        await initializer.configure_database_settings()
        
        # Verify setup
        logger.info("🔍 Verifying database setup...")
        if await initializer.verify_setup():
            logger.success("🎉 Production database initialization completed successfully!")
        else:
            logger.error("❌ Database verification failed!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    finally:
        await initializer.close()


if __name__ == "__main__":
    asyncio.run(main())