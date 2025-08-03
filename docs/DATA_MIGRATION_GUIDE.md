# Data Migration Guide

## Overview

This guide provides comprehensive procedures for migrating data in the Infra Mind platform, including transitions from demo data to production data, database schema updates, and system upgrades. It covers all aspects of data migration with safety procedures and rollback mechanisms.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Pre-Migration Preparation](#pre-migration-preparation)
3. [Demo to Production Migration](#demo-to-production-migration)
4. [Schema Migration Procedures](#schema-migration-procedures)
5. [Data Validation and Integrity](#data-validation-and-integrity)
6. [Rollback Procedures](#rollback-procedures)
7. [Performance Considerations](#performance-considerations)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Post-Migration Procedures](#post-migration-procedures)
10. [Troubleshooting](#troubleshooting)

## Migration Overview

### Migration Types

#### 1. Demo to Production Migration
- **Purpose**: Transition from demo/mock data to real production data
- **Scope**: Replace all demo data with production-ready structures
- **Impact**: System-wide data transformation
- **Downtime**: Planned maintenance window required

#### 2. Schema Migration
- **Purpose**: Update database schema for new features or improvements
- **Scope**: Database structure changes
- **Impact**: Application compatibility updates required
- **Downtime**: Minimal with proper planning

#### 3. Data Format Migration
- **Purpose**: Update data formats or structures
- **Scope**: Data transformation without schema changes
- **Impact**: Data consistency and format updates
- **Downtime**: Can often be done online

#### 4. System Upgrade Migration
- **Purpose**: Migrate data during major system upgrades
- **Scope**: Complete system data migration
- **Impact**: Full system transformation
- **Downtime**: Extended maintenance window

### Migration Principles

1. **Safety First**: Always backup before migration
2. **Validation**: Verify data integrity at every step
3. **Rollback Ready**: Maintain ability to rollback at any point
4. **Monitoring**: Track migration progress and performance
5. **Testing**: Test migration procedures in staging first

## Pre-Migration Preparation

### Assessment and Planning

#### 1. Data Assessment
```bash
# Analyze current data structure
python scripts/analyze_data_structure.py

# Check data volumes
python scripts/check_data_volumes.py

# Identify data dependencies
python scripts/map_data_dependencies.py

# Assess migration complexity
python scripts/assess_migration_complexity.py
```

#### 2. Migration Planning
```bash
# Create migration plan
python scripts/create_migration_plan.py --type=demo-to-prod

# Estimate migration time
python scripts/estimate_migration_time.py

# Plan resource requirements
python scripts/plan_migration_resources.py

# Schedule maintenance window
python scripts/schedule_maintenance.py --duration=4h
```

### Environment Preparation

#### 1. Backup Creation
```bash
# Create full system backup
python scripts/backup_restore.py --full-backup --tag="pre-migration-$(date +%Y%m%d-%H%M)"

# Verify backup integrity
python scripts/verify_backup.py --tag="pre-migration-$(date +%Y%m%d-%H%M)"

# Create additional safety backups
mongodump --uri="mongodb://mongodb:27017/infra_mind_prod" --out="/backups/safety/$(date +%Y%m%d)"
```

#### 2. System Health Check
```bash
# Verify system health
./scripts/health-check.sh

# Check resource availability
kubectl top nodes
kubectl top pods -n infra-mind-prod

# Verify external dependencies
python scripts/check_external_dependencies.py

# Test rollback procedures
python scripts/test_rollback_procedures.py --dry-run
```

#### 3. Migration Environment Setup
```bash
# Create migration namespace
kubectl create namespace infra-mind-migration

# Deploy migration tools
kubectl apply -f k8s/migration-tools.yaml

# Set up migration monitoring
python scripts/setup_migration_monitoring.py

# Prepare migration scripts
python scripts/prepare_migration_scripts.py
```

## Demo to Production Migration

### Phase 1: Data Structure Analysis

#### 1. Analyze Demo Data
```bash
# Identify demo data patterns
python scripts/identify_demo_data.py

# Map demo to production schema
python scripts/map_demo_to_prod.py

# Generate transformation rules
python scripts/generate_transformation_rules.py

# Validate transformation logic
python scripts/validate_transformations.py --dry-run
```

#### 2. Production Schema Preparation
```bash
# Create production schema
python scripts/create_production_schema.py

# Set up indexes for production
python scripts/create_production_indexes.py

# Configure constraints and validations
python scripts/setup_production_constraints.py

# Prepare reference data
python scripts/prepare_reference_data.py
```

### Phase 2: Data Transformation

#### 1. User Data Migration
```python
# User data transformation script
def migrate_user_data():
    """
    Migrate user data from demo to production format
    """
    # Connect to databases
    demo_db = connect_to_demo_db()
    prod_db = connect_to_prod_db()
    
    # Get demo users
    demo_users = demo_db.users.find({})
    
    for demo_user in demo_users:
        # Transform demo user to production format
        prod_user = {
            'email': demo_user.get('email', '').lower(),
            'password_hash': hash_password(demo_user.get('password', '')),
            'profile': {
                'full_name': demo_user.get('name', ''),
                'company': demo_user.get('company', ''),
                'role': demo_user.get('role', 'user')
            },
            'created_at': demo_user.get('created_at', datetime.utcnow()),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'email_verified': False  # Require re-verification
        }
        
        # Validate production user data
        if validate_user_data(prod_user):
            prod_db.users.insert_one(prod_user)
            log_migration_success('user', demo_user['_id'], prod_user['_id'])
        else:
            log_migration_error('user', demo_user['_id'], 'validation_failed')

# Execute user migration
migrate_user_data()
```

#### 2. Assessment Data Migration
```python
# Assessment data transformation script
def migrate_assessment_data():
    """
    Migrate assessment data from demo to production format
    """
    demo_db = connect_to_demo_db()
    prod_db = connect_to_prod_db()
    
    # Get demo assessments
    demo_assessments = demo_db.assessments.find({})
    
    for demo_assessment in demo_assessments:
        # Transform demo assessment to production format
        prod_assessment = {
            'user_id': get_production_user_id(demo_assessment['user_id']),
            'name': demo_assessment.get('name', ''),
            'description': demo_assessment.get('description', ''),
            'business_requirements': transform_business_requirements(
                demo_assessment.get('business_requirements', {})
            ),
            'technical_requirements': transform_technical_requirements(
                demo_assessment.get('technical_requirements', {})
            ),
            'compliance_requirements': transform_compliance_requirements(
                demo_assessment.get('compliance_requirements', {})
            ),
            'status': 'draft',  # Reset status for production
            'created_at': demo_assessment.get('created_at', datetime.utcnow()),
            'updated_at': datetime.utcnow(),
            'version': 1
        }
        
        # Validate and insert
        if validate_assessment_data(prod_assessment):
            result = prod_db.assessments.insert_one(prod_assessment)
            
            # Migrate related data
            migrate_assessment_reports(demo_assessment['_id'], result.inserted_id)
            migrate_assessment_metrics(demo_assessment['_id'], result.inserted_id)
            
            log_migration_success('assessment', demo_assessment['_id'], result.inserted_id)
        else:
            log_migration_error('assessment', demo_assessment['_id'], 'validation_failed')

# Execute assessment migration
migrate_assessment_data()
```

#### 3. Configuration Data Migration
```python
# Configuration data transformation script
def migrate_configuration_data():
    """
    Migrate system configuration from demo to production
    """
    demo_config = load_demo_configuration()
    
    # Transform configuration for production
    prod_config = {
        'llm_providers': {
            'openai': {
                'model': 'gpt-4',
                'max_tokens': 4000,
                'temperature': 0.7,
                'rate_limits': {
                    'requests_per_minute': 3000,
                    'tokens_per_minute': 250000
                }
            },
            'anthropic': {
                'model': 'claude-3-opus-20240229',
                'max_tokens': 4000,
                'rate_limits': {
                    'requests_per_minute': 1000,
                    'tokens_per_minute': 100000
                }
            }
        },
        'cloud_providers': {
            'aws': {
                'regions': ['us-east-1', 'us-west-2', 'eu-west-1'],
                'rate_limits': {
                    'requests_per_second': 100
                }
            },
            'azure': {
                'regions': ['eastus', 'westus2', 'westeurope'],
                'rate_limits': {
                    'requests_per_second': 100
                }
            },
            'gcp': {
                'regions': ['us-central1', 'us-east1', 'europe-west1'],
                'rate_limits': {
                    'requests_per_second': 100
                }
            }
        },
        'cache_settings': {
            'default_ttl': 3600,
            'pricing_ttl': 7200,
            'services_ttl': 14400
        }
    }
    
    # Save production configuration
    save_production_configuration(prod_config)
    log_migration_success('configuration', 'demo_config', 'prod_config')

# Execute configuration migration
migrate_configuration_data()
```

### Phase 3: Data Validation

#### 1. Integrity Validation
```bash
# Run comprehensive data validation
python scripts/validate_migrated_data.py --comprehensive

# Check referential integrity
python scripts/check_referential_integrity.py

# Validate data consistency
python scripts/validate_data_consistency.py

# Check for data loss
python scripts/check_data_completeness.py
```

#### 2. Functional Validation
```bash
# Test user authentication
python scripts/test_user_authentication.py

# Test assessment creation
python scripts/test_assessment_creation.py

# Test report generation
python scripts/test_report_generation.py

# Test agent orchestration
python scripts/test_agent_orchestration.py
```

## Schema Migration Procedures

### Schema Version Management

#### 1. Version Control System
```python
# Schema version tracking
class SchemaMigration:
    def __init__(self, version, description, up_script, down_script):
        self.version = version
        self.description = description
        self.up_script = up_script
        self.down_script = down_script
        self.timestamp = datetime.utcnow()
    
    def apply(self):
        """Apply the migration"""
        try:
            exec(self.up_script)
            self.record_migration()
            return True
        except Exception as e:
            log_migration_error(self.version, str(e))
            return False
    
    def rollback(self):
        """Rollback the migration"""
        try:
            exec(self.down_script)
            self.remove_migration_record()
            return True
        except Exception as e:
            log_rollback_error(self.version, str(e))
            return False

# Migration registry
MIGRATIONS = [
    SchemaMigration(
        version="001",
        description="Add user profile fields",
        up_script="""
        db.users.updateMany(
            {},
            {
                $set: {
                    "profile.timezone": "UTC",
                    "profile.language": "en",
                    "profile.notifications": {
                        "email": True,
                        "push": True,
                        "sms": False
                    }
                }
            }
        )
        """,
        down_script="""
        db.users.updateMany(
            {},
            {
                $unset: {
                    "profile.timezone": "",
                    "profile.language": "",
                    "profile.notifications": ""
                }
            }
        )
        """
    ),
    SchemaMigration(
        version="002",
        description="Add assessment versioning",
        up_script="""
        db.assessments.updateMany(
            {},
            {
                $set: {
                    "version": 1,
                    "version_history": []
                }
            }
        )
        """,
        down_script="""
        db.assessments.updateMany(
            {},
            {
                $unset: {
                    "version": "",
                    "version_history": ""
                }
            }
        )
        """
    )
]
```

#### 2. Migration Execution
```bash
# Check current schema version
python scripts/check_schema_version.py

# List pending migrations
python scripts/list_pending_migrations.py

# Apply specific migration
python scripts/apply_migration.py --version=001

# Apply all pending migrations
python scripts/apply_all_migrations.py

# Rollback specific migration
python scripts/rollback_migration.py --version=001
```

### Index Management

#### 1. Index Creation Strategy
```python
# Index migration script
def migrate_indexes():
    """
    Create or update database indexes
    """
    db = get_database_connection()
    
    # Define new indexes
    new_indexes = [
        {
            'collection': 'assessments',
            'index': [('user_id', 1), ('created_at', -1)],
            'options': {'background': True, 'name': 'user_created_idx'}
        },
        {
            'collection': 'reports',
            'index': [('assessment_id', 1), ('status', 1)],
            'options': {'background': True, 'name': 'assessment_status_idx'}
        },
        {
            'collection': 'agent_metrics',
            'index': [('agent_type', 1), ('timestamp', -1)],
            'options': {'background': True, 'name': 'agent_time_idx'}
        }
    ]
    
    # Create indexes
    for index_def in new_indexes:
        collection = db[index_def['collection']]
        try:
            collection.create_index(
                index_def['index'],
                **index_def['options']
            )
            log_index_creation_success(index_def)
        except Exception as e:
            log_index_creation_error(index_def, str(e))

# Execute index migration
migrate_indexes()
```

#### 2. Index Optimization
```bash
# Analyze index usage
python scripts/analyze_index_usage.py

# Identify unused indexes
python scripts/find_unused_indexes.py

# Optimize existing indexes
python scripts/optimize_indexes.py

# Monitor index performance
python scripts/monitor_index_performance.py
```

## Data Validation and Integrity

### Validation Framework

#### 1. Data Validation Rules
```python
# Data validation framework
class DataValidator:
    def __init__(self):
        self.validation_rules = {}
        self.errors = []
    
    def add_rule(self, collection, field, validator):
        """Add validation rule for a field"""
        if collection not in self.validation_rules:
            self.validation_rules[collection] = {}
        self.validation_rules[collection][field] = validator
    
    def validate_document(self, collection, document):
        """Validate a single document"""
        if collection not in self.validation_rules:
            return True
        
        for field, validator in self.validation_rules[collection].items():
            if not validator(document.get(field)):
                self.errors.append({
                    'collection': collection,
                    'document_id': document.get('_id'),
                    'field': field,
                    'value': document.get(field),
                    'error': 'validation_failed'
                })
                return False
        return True
    
    def validate_collection(self, collection):
        """Validate entire collection"""
        db = get_database_connection()
        documents = db[collection].find({})
        
        valid_count = 0
        invalid_count = 0
        
        for document in documents:
            if self.validate_document(collection, document):
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            'collection': collection,
            'valid_documents': valid_count,
            'invalid_documents': invalid_count,
            'errors': self.errors
        }

# Set up validation rules
validator = DataValidator()

# User validation rules
validator.add_rule('users', 'email', lambda x: x and '@' in x)
validator.add_rule('users', 'password_hash', lambda x: x and len(x) > 10)
validator.add_rule('users', 'created_at', lambda x: isinstance(x, datetime))

# Assessment validation rules
validator.add_rule('assessments', 'user_id', lambda x: x is not None)
validator.add_rule('assessments', 'name', lambda x: x and len(x.strip()) > 0)
validator.add_rule('assessments', 'status', lambda x: x in ['draft', 'processing', 'completed'])

# Run validation
results = validator.validate_collection('users')
print(f"User validation: {results}")
```

#### 2. Referential Integrity Checks
```python
# Referential integrity checker
def check_referential_integrity():
    """
    Check referential integrity across collections
    """
    db = get_database_connection()
    integrity_errors = []
    
    # Check assessment -> user references
    assessments = db.assessments.find({})
    for assessment in assessments:
        user_id = assessment.get('user_id')
        if user_id:
            user = db.users.find_one({'_id': user_id})
            if not user:
                integrity_errors.append({
                    'type': 'orphaned_assessment',
                    'assessment_id': assessment['_id'],
                    'missing_user_id': user_id
                })
    
    # Check report -> assessment references
    reports = db.reports.find({})
    for report in reports:
        assessment_id = report.get('assessment_id')
        if assessment_id:
            assessment = db.assessments.find_one({'_id': assessment_id})
            if not assessment:
                integrity_errors.append({
                    'type': 'orphaned_report',
                    'report_id': report['_id'],
                    'missing_assessment_id': assessment_id
                })
    
    # Check workflow_states -> assessment references
    workflow_states = db.workflow_states.find({})
    for state in workflow_states:
        assessment_id = state.get('assessment_id')
        if assessment_id:
            assessment = db.assessments.find_one({'_id': assessment_id})
            if not assessment:
                integrity_errors.append({
                    'type': 'orphaned_workflow_state',
                    'state_id': state['_id'],
                    'missing_assessment_id': assessment_id
                })
    
    return integrity_errors

# Run integrity check
integrity_errors = check_referential_integrity()
if integrity_errors:
    print(f"Found {len(integrity_errors)} referential integrity errors")
    for error in integrity_errors:
        print(f"Error: {error}")
else:
    print("No referential integrity errors found")
```

### Data Quality Checks

#### 1. Data Completeness
```python
# Data completeness checker
def check_data_completeness():
    """
    Check for missing required data
    """
    db = get_database_connection()
    completeness_issues = []
    
    # Check required user fields
    users_missing_email = db.users.count_documents({'email': {'$exists': False}})
    if users_missing_email > 0:
        completeness_issues.append({
            'collection': 'users',
            'field': 'email',
            'missing_count': users_missing_email
        })
    
    # Check required assessment fields
    assessments_missing_name = db.assessments.count_documents({'name': {'$exists': False}})
    if assessments_missing_name > 0:
        completeness_issues.append({
            'collection': 'assessments',
            'field': 'name',
            'missing_count': assessments_missing_name
        })
    
    # Check for empty business requirements
    assessments_empty_requirements = db.assessments.count_documents({
        'business_requirements': {'$exists': True, '$eq': {}}
    })
    if assessments_empty_requirements > 0:
        completeness_issues.append({
            'collection': 'assessments',
            'field': 'business_requirements',
            'empty_count': assessments_empty_requirements
        })
    
    return completeness_issues

# Run completeness check
completeness_issues = check_data_completeness()
for issue in completeness_issues:
    print(f"Completeness issue: {issue}")
```

#### 2. Data Consistency
```python
# Data consistency checker
def check_data_consistency():
    """
    Check for data consistency issues
    """
    db = get_database_connection()
    consistency_issues = []
    
    # Check for duplicate emails
    duplicate_emails = db.users.aggregate([
        {'$group': {'_id': '$email', 'count': {'$sum': 1}}},
        {'$match': {'count': {'$gt': 1}}}
    ])
    
    for duplicate in duplicate_emails:
        consistency_issues.append({
            'type': 'duplicate_email',
            'email': duplicate['_id'],
            'count': duplicate['count']
        })
    
    # Check for assessments with invalid status
    invalid_status_assessments = db.assessments.find({
        'status': {'$nin': ['draft', 'processing', 'completed', 'archived']}
    })
    
    for assessment in invalid_status_assessments:
        consistency_issues.append({
            'type': 'invalid_status',
            'assessment_id': assessment['_id'],
            'status': assessment.get('status')
        })
    
    # Check for future created_at dates
    future_dates = db.assessments.find({
        'created_at': {'$gt': datetime.utcnow()}
    })
    
    for assessment in future_dates:
        consistency_issues.append({
            'type': 'future_date',
            'assessment_id': assessment['_id'],
            'created_at': assessment.get('created_at')
        })
    
    return consistency_issues

# Run consistency check
consistency_issues = check_data_consistency()
for issue in consistency_issues:
    print(f"Consistency issue: {issue}")
```

## Rollback Procedures

### Rollback Strategy

#### 1. Automatic Rollback Triggers
```python
# Automatic rollback system
class MigrationRollback:
    def __init__(self):
        self.rollback_triggers = []
        self.rollback_threshold = {
            'error_rate': 0.05,  # 5% error rate
            'data_loss': 0.01,   # 1% data loss
            'performance_degradation': 0.20  # 20% performance drop
        }
    
    def check_rollback_conditions(self):
        """Check if rollback conditions are met"""
        # Check error rate
        error_rate = self.calculate_error_rate()
        if error_rate > self.rollback_threshold['error_rate']:
            return True, f"Error rate {error_rate} exceeds threshold"
        
        # Check data loss
        data_loss_rate = self.calculate_data_loss_rate()
        if data_loss_rate > self.rollback_threshold['data_loss']:
            return True, f"Data loss rate {data_loss_rate} exceeds threshold"
        
        # Check performance
        performance_drop = self.calculate_performance_drop()
        if performance_drop > self.rollback_threshold['performance_degradation']:
            return True, f"Performance drop {performance_drop} exceeds threshold"
        
        return False, "All conditions within acceptable limits"
    
    def execute_rollback(self, reason):
        """Execute automatic rollback"""
        print(f"Executing automatic rollback: {reason}")
        
        # Stop migration process
        self.stop_migration()
        
        # Restore from backup
        self.restore_from_backup()
        
        # Verify rollback success
        if self.verify_rollback():
            print("Rollback completed successfully")
            return True
        else:
            print("Rollback failed - manual intervention required")
            return False

# Set up rollback monitoring
rollback_system = MigrationRollback()
```

#### 2. Manual Rollback Procedures
```bash
# Manual rollback script
#!/bin/bash

echo "Starting manual rollback procedure..."

# Step 1: Stop application
echo "Stopping application..."
kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind-prod

# Step 2: Restore database from backup
echo "Restoring database from backup..."
BACKUP_TAG="pre-migration-$(date +%Y%m%d)"
python scripts/backup_restore.py --restore --tag="$BACKUP_TAG"

# Step 3: Verify data integrity
echo "Verifying data integrity..."
python scripts/verify_data_integrity.py

# Step 4: Restart application
echo "Restarting application..."
kubectl scale deployment infra-mind-api --replicas=3 -n infra-mind-prod

# Step 5: Run health checks
echo "Running health checks..."
./scripts/health-check.sh

echo "Manual rollback completed"
```

### Rollback Validation

#### 1. Post-Rollback Verification
```python
# Rollback verification script
def verify_rollback_success():
    """
    Verify that rollback was successful
    """
    verification_results = {}
    
    # Check data counts
    db = get_database_connection()
    
    # Compare record counts with pre-migration baseline
    baseline_counts = load_baseline_counts()
    current_counts = {
        'users': db.users.count_documents({}),
        'assessments': db.assessments.count_documents({}),
        'reports': db.reports.count_documents({}),
        'workflow_states': db.workflow_states.count_documents({})
    }
    
    for collection, current_count in current_counts.items():
        baseline_count = baseline_counts.get(collection, 0)
        if current_count != baseline_count:
            verification_results[collection] = {
                'status': 'mismatch',
                'baseline': baseline_count,
                'current': current_count,
                'difference': current_count - baseline_count
            }
        else:
            verification_results[collection] = {
                'status': 'match',
                'count': current_count
            }
    
    # Check data integrity
    integrity_errors = check_referential_integrity()
    verification_results['integrity'] = {
        'status': 'pass' if not integrity_errors else 'fail',
        'errors': integrity_errors
    }
    
    # Check application functionality
    functionality_tests = run_functionality_tests()
    verification_results['functionality'] = functionality_tests
    
    return verification_results

# Run rollback verification
verification_results = verify_rollback_success()
print(f"Rollback verification results: {verification_results}")
```

## Performance Considerations

### Migration Performance Optimization

#### 1. Batch Processing
```python
# Batch processing for large migrations
def migrate_data_in_batches(collection_name, transformation_func, batch_size=1000):
    """
    Migrate data in batches to optimize performance
    """
    db = get_database_connection()
    collection = db[collection_name]
    
    # Get total document count
    total_docs = collection.count_documents({})
    processed_docs = 0
    
    print(f"Starting migration of {total_docs} documents in {collection_name}")
    
    # Process in batches
    skip = 0
    while skip < total_docs:
        # Get batch of documents
        batch = list(collection.find({}).skip(skip).limit(batch_size))
        
        if not batch:
            break
        
        # Transform batch
        transformed_batch = []
        for doc in batch:
            try:
                transformed_doc = transformation_func(doc)
                if transformed_doc:
                    transformed_batch.append(transformed_doc)
            except Exception as e:
                log_transformation_error(doc['_id'], str(e))
        
        # Insert transformed batch
        if transformed_batch:
            try:
                result = db[f"{collection_name}_new"].insert_many(transformed_batch)
                processed_docs += len(result.inserted_ids)
                print(f"Processed {processed_docs}/{total_docs} documents")
            except Exception as e:
                log_batch_error(skip, batch_size, str(e))
        
        skip += batch_size
        
        # Optional: Add delay to reduce system load
        time.sleep(0.1)
    
    print(f"Migration completed: {processed_docs}/{total_docs} documents processed")

# Example usage
def transform_user_document(user_doc):
    """Transform user document for production"""
    return {
        'email': user_doc.get('email', '').lower(),
        'password_hash': hash_password(user_doc.get('password', '')),
        'profile': transform_user_profile(user_doc.get('profile', {})),
        'created_at': user_doc.get('created_at', datetime.utcnow()),
        'updated_at': datetime.utcnow(),
        'is_active': True
    }

# Execute batch migration
migrate_data_in_batches('users', transform_user_document, batch_size=500)
```

#### 2. Parallel Processing
```python
# Parallel migration processing
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

def migrate_collection_parallel(collection_name, num_workers=4):
    """
    Migrate collection using parallel processing
    """
    db = get_database_connection()
    collection = db[collection_name]
    
    # Get total document count
    total_docs = collection.count_documents({})
    docs_per_worker = total_docs // num_workers
    
    # Create work chunks
    work_chunks = []
    for i in range(num_workers):
        skip = i * docs_per_worker
        limit = docs_per_worker if i < num_workers - 1 else total_docs - skip
        work_chunks.append((collection_name, skip, limit))
    
    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_chunk = {
            executor.submit(process_migration_chunk, chunk): chunk 
            for chunk in work_chunks
        }
        
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                print(f"Chunk {chunk} completed: {result}")
            except Exception as e:
                print(f"Chunk {chunk} failed: {e}")

def process_migration_chunk(chunk_info):
    """Process a chunk of migration work"""
    collection_name, skip, limit = chunk_info
    
    # Connect to database (each process needs its own connection)
    db = get_database_connection()
    collection = db[collection_name]
    
    # Process documents in chunk
    documents = collection.find({}).skip(skip).limit(limit)
    processed_count = 0
    
    for doc in documents:
        try:
            # Transform and migrate document
            transformed_doc = transform_document(doc)
            if transformed_doc:
                db[f"{collection_name}_new"].insert_one(transformed_doc)
                processed_count += 1
        except Exception as e:
            log_migration_error(doc['_id'], str(e))
    
    return processed_count

# Execute parallel migration
migrate_collection_parallel('assessments', num_workers=4)
```

### Resource Management

#### 1. Memory Management
```python
# Memory-efficient migration
def migrate_with_memory_management(collection_name, batch_size=100):
    """
    Migrate data with careful memory management
    """
    db = get_database_connection()
    collection = db[collection_name]
    
    # Use cursor with no timeout to handle large datasets
    cursor = collection.find({}, no_cursor_timeout=True)
    
    try:
        batch = []
        processed_count = 0
        
        for document in cursor:
            # Transform document
            transformed_doc = transform_document(document)
            if transformed_doc:
                batch.append(transformed_doc)
            
            # Process batch when full
            if len(batch) >= batch_size:
                process_batch(batch, f"{collection_name}_new")
                processed_count += len(batch)
                batch = []  # Clear batch to free memory
                
                # Force garbage collection
                import gc
                gc.collect()
                
                print(f"Processed {processed_count} documents")
        
        # Process remaining documents
        if batch:
            process_batch(batch, f"{collection_name}_new")
            processed_count += len(batch)
        
        print(f"Migration completed: {processed_count} documents processed")
        
    finally:
        cursor.close()

def process_batch(batch, target_collection):
    """Process a batch of documents"""
    db = get_database_connection()
    if batch:
        db[target_collection].insert_many(batch)
```

#### 2. Connection Pool Management
```python
# Connection pool optimization for migration
from pymongo import MongoClient
from pymongo.pool import Pool

class MigrationConnectionManager:
    def __init__(self, connection_string, pool_size=50):
        self.client = MongoClient(
            connection_string,
            maxPoolSize=pool_size,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000
        )
        self.db = self.client.get_default_database()
    
    def get_connection(self):
        """Get database connection from pool"""
        return self.db
    
    def close_connections(self):
        """Close all connections"""
        self.client.close()

# Use connection manager for migration
connection_manager = MigrationConnectionManager(
    "mongodb://mongodb:27017/infra_mind_prod",
    pool_size=100
)

# Perform migration with optimized connections
db = connection_manager.get_connection()
# ... migration code ...

# Clean up connections
connection_manager.close_connections()
```

## Monitoring and Alerting

### Migration Monitoring

#### 1. Progress Tracking
```python
# Migration progress tracker
class MigrationProgressTracker:
    def __init__(self, migration_id):
        self.migration_id = migration_id
        self.start_time = datetime.utcnow()
        self.progress_data = {
            'migration_id': migration_id,
            'start_time': self.start_time,
            'status': 'running',
            'collections': {},
            'errors': [],
            'performance_metrics': {}
        }
    
    def update_collection_progress(self, collection, processed, total):
        """Update progress for a collection"""
        self.progress_data['collections'][collection] = {
            'processed': processed,
            'total': total,
            'percentage': (processed / total) * 100 if total > 0 else 0,
            'last_updated': datetime.utcnow()
        }
        
        # Save progress to database
        self.save_progress()
    
    def add_error(self, error_info):
        """Add error to tracking"""
        self.progress_data['errors'].append({
            'timestamp': datetime.utcnow(),
            'error': error_info
        })
        
        # Save progress to database
        self.save_progress()
    
    def update_performance_metrics(self, metrics):
        """Update performance metrics"""
        self.progress_data['performance_metrics'].update(metrics)
        self.save_progress()
    
    def complete_migration(self, status='completed'):
        """Mark migration as completed"""
        self.progress_data['status'] = status
        self.progress_data['end_time'] = datetime.utcnow()
        self.progress_data['duration'] = (
            self.progress_data['end_time'] - self.start_time
        ).total_seconds()
        
        self.save_progress()
    
    def save_progress(self):
        """Save progress to database"""
        db = get_database_connection()
        db.migration_progress.replace_one(
            {'migration_id': self.migration_id},
            self.progress_data,
            upsert=True
        )

# Use progress tracker
tracker = MigrationProgressTracker('demo-to-prod-20240101')
tracker.update_collection_progress('users', 500, 1000)
tracker.update_performance_metrics({'documents_per_second': 50})
```

#### 2. Real-time Monitoring
```python
# Real-time migration monitoring
import threading
import time

class MigrationMonitor:
    def __init__(self, migration_id):
        self.migration_id = migration_id
        self.monitoring = True
        self.metrics = {}
        
    def start_monitoring(self):
        """Start monitoring thread"""
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect metrics
                self.metrics = {
                    'timestamp': datetime.utcnow(),
                    'memory_usage': self._get_memory_usage(),
                    'cpu_usage': self._get_cpu_usage(),
                    'database_connections': self._get_db_connections(),
                    'migration_rate': self._get_migration_rate(),
                    'error_rate': self._get_error_rate()
                }
                
                # Check for issues
                self._check_for_issues()
                
                # Send metrics to monitoring system
                self._send_metrics()
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
    
    def _check_for_issues(self):
        """Check for migration issues"""
        # Check memory usage
        if self.metrics['memory_usage'] > 0.9:
            self._send_alert('high_memory_usage', self.metrics['memory_usage'])
        
        # Check error rate
        if self.metrics['error_rate'] > 0.05:
            self._send_alert('high_error_rate', self.metrics['error_rate'])
        
        # Check migration rate
        if self.metrics['migration_rate'] < 10:
            self._send_alert('slow_migration', self.metrics['migration_rate'])
    
    def _send_alert(self, alert_type, value):
        """Send alert to monitoring system"""
        alert = {
            'migration_id': self.migration_id,
            'alert_type': alert_type,
            'value': value,
            'timestamp': datetime.utcnow()
        }
        
        # Send to alerting system (Slack, email, etc.)
        send_migration_alert(alert)

# Start monitoring
monitor = MigrationMonitor('demo-to-prod-20240101')
monitor.start_monitoring()
```

### Alerting Configuration

#### 1. Alert Rules
```yaml
# migration-alerts.yml
groups:
- name: migration_alerts
  rules:
  - alert: MigrationHighErrorRate
    expr: migration_error_rate > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Migration error rate is high"
      description: "Migration {{ $labels.migration_id }} has error rate of {{ $value }}"

  - alert: MigrationSlowProgress
    expr: migration_documents_per_second < 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Migration progress is slow"
      description: "Migration {{ $labels.migration_id }} is processing only {{ $value }} documents per second"

  - alert: MigrationHighMemoryUsage
    expr: migration_memory_usage > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Migration using high memory"
      description: "Migration {{ $labels.migration_id }} is using {{ $value }}% of available memory"

  - alert: MigrationStalled
    expr: increase(migration_processed_documents[10m]) == 0
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Migration appears to be stalled"
      description: "Migration {{ $labels.migration_id }} has not processed any documents in the last 10 minutes"
```

#### 2. Notification Channels
```python
# Migration notification system
class MigrationNotifier:
    def __init__(self):
        self.channels = {
            'slack': SlackNotifier(),
            'email': EmailNotifier(),
            'pagerduty': PagerDutyNotifier()
        }
    
    def send_migration_start_notification(self, migration_info):
        """Notify about migration start"""
        message = f"Migration {migration_info['id']} started at {migration_info['start_time']}"
        
        self.channels['slack'].send_message(message)
        self.channels['email'].send_notification(
            subject="Migration Started",
            body=message,
            recipients=['devops@infra-mind.com']
        )
    
    def send_migration_complete_notification(self, migration_info):
        """Notify about migration completion"""
        message = f"Migration {migration_info['id']} completed successfully in {migration_info['duration']} seconds"
        
        self.channels['slack'].send_message(message)
        self.channels['email'].send_notification(
            subject="Migration Completed",
            body=message,
            recipients=['devops@infra-mind.com']
        )
    
    def send_migration_error_notification(self, migration_info, error):
        """Notify about migration errors"""
        message = f"Migration {migration_info['id']} encountered error: {error}"
        
        self.channels['slack'].send_urgent_message(message)
        self.channels['email'].send_notification(
            subject="Migration Error - Immediate Attention Required",
            body=message,
            recipients=['devops@infra-mind.com', 'engineering@infra-mind.com']
        )
        self.channels['pagerduty'].trigger_incident(
            title="Migration Error",
            description=message,
            severity="high"
        )

# Use notification system
notifier = MigrationNotifier()
notifier.send_migration_start_notification({
    'id': 'demo-to-prod-20240101',
    'start_time': datetime.utcnow()
})
```

## Post-Migration Procedures

### Cleanup and Optimization

#### 1. Data Cleanup
```bash
# Post-migration cleanup script
#!/bin/bash

echo "Starting post-migration cleanup..."

# Remove temporary migration collections
python scripts/cleanup_migration_temp_data.py

# Remove old demo data
python scripts/remove_demo_data.py --confirm

# Clean up migration logs older than 30 days
find /var/log/migration -name "*.log" -mtime +30 -delete

# Optimize database after migration
python scripts/optimize_database_post_migration.py

echo "Post-migration cleanup completed"
```

#### 2. Performance Optimization
```python
# Post-migration optimization
def optimize_post_migration():
    """
    Optimize system performance after migration
    """
    db = get_database_connection()
    
    # Rebuild indexes for optimal performance
    collections_to_optimize = ['users', 'assessments', 'reports', 'workflow_states']
    
    for collection_name in collections_to_optimize:
        collection = db[collection_name]
        
        # Get current indexes
        indexes = collection.list_indexes()
        
        # Rebuild indexes
        for index in indexes:
            if index['name'] != '_id_':
                try:
                    collection.reindex(index['name'])
                    print(f"Rebuilt index {index['name']} on {collection_name}")
                except Exception as e:
                    print(f"Failed to rebuild index {index['name']}: {e}")
    
    # Update collection statistics
    db.command('collStats', 'users')
    db.command('collStats', 'assessments')
    db.command('collStats', 'reports')
    
    # Compact collections if needed
    for collection_name in collections_to_optimize:
        try:
            db.command('compact', collection_name)
            print(f"Compacted collection {collection_name}")
        except Exception as e:
            print(f"Failed to compact {collection_name}: {e}")

# Run post-migration optimization
optimize_post_migration()
```

### Documentation Updates

#### 1. Migration Report Generation
```python
# Migration report generator
def generate_migration_report(migration_id):
    """
    Generate comprehensive migration report
    """
    db = get_database_connection()
    
    # Get migration progress data
    migration_data = db.migration_progress.find_one({'migration_id': migration_id})
    
    if not migration_data:
        return None
    
    # Calculate statistics
    total_processed = sum(
        collection['processed'] 
        for collection in migration_data['collections'].values()
    )
    
    total_documents = sum(
        collection['total'] 
        for collection in migration_data['collections'].values()
    )
    
    error_count = len(migration_data.get('errors', []))
    
    # Generate report
    report = {
        'migration_id': migration_id,
        'start_time': migration_data['start_time'],
        'end_time': migration_data.get('end_time'),
        'duration': migration_data.get('duration'),
        'status': migration_data['status'],
        'statistics': {
            'total_documents': total_documents,
            'processed_documents': total_processed,
            'success_rate': (total_processed / total_documents) * 100 if total_documents > 0 else 0,
            'error_count': error_count,
            'error_rate': (error_count / total_documents) * 100 if total_documents > 0 else 0
        },
        'collection_details': migration_data['collections'],
        'performance_metrics': migration_data.get('performance_metrics', {}),
        'errors': migration_data.get('errors', [])
    }
    
    return report

# Generate and save report
migration_report = generate_migration_report('demo-to-prod-20240101')
if migration_report:
    # Save report to file
    with open(f"migration_report_{migration_report['migration_id']}.json", 'w') as f:
        json.dump(migration_report, f, indent=2, default=str)
    
    print(f"Migration report generated: {migration_report}")
```

## Troubleshooting

### Common Migration Issues

#### 1. Memory Issues
```python
# Memory issue troubleshooting
def troubleshoot_memory_issues():
    """
    Troubleshoot and resolve memory issues during migration
    """
    import psutil
    
    # Check current memory usage
    memory = psutil.virtual_memory()
    print(f"Memory usage: {memory.percent}%")
    print(f"Available memory: {memory.available / (1024**3):.2f} GB")
    
    if memory.percent > 85:
        print("High memory usage detected. Recommendations:")
        print("1. Reduce batch size")
        print("2. Implement memory cleanup between batches")
        print("3. Use streaming processing instead of loading all data")
        print("4. Consider parallel processing with smaller chunks")
        
        # Implement memory cleanup
        import gc
        gc.collect()
        
        # Reduce batch size
        return {
            'recommended_batch_size': 100,
            'enable_memory_cleanup': True,
            'use_streaming': True
        }
    
    return {'status': 'memory_ok'}

# Run memory troubleshooting
memory_recommendations = troubleshoot_memory_issues()
print(f"Memory recommendations: {memory_recommendations}")
```

#### 2. Performance Issues
```python
# Performance issue troubleshooting
def troubleshoot_performance_issues():
    """
    Identify and resolve performance bottlenecks
    """
    db = get_database_connection()
    
    # Check database performance
    db_stats = db.command('dbStats')
    print(f"Database size: {db_stats['dataSize'] / (1024**3):.2f} GB")
    print(f"Index size: {db_stats['indexSize'] / (1024**3):.2f} GB")
    
    # Check slow operations
    current_ops = db.command('currentOp')
    slow_ops = [
        op for op in current_ops.get('inprog', [])
        if op.get('secs_running', 0) > 30
    ]
    
    if slow_ops:
        print(f"Found {len(slow_ops)} slow operations")
        for op in slow_ops:
            print(f"Slow operation: {op}")
    
    # Check index usage
    for collection_name in ['users', 'assessments', 'reports']:
        collection = db[collection_name]
        index_stats = collection.aggregate([{'$indexStats': {}}])
        
        for stat in index_stats:
            if stat['accesses']['ops'] == 0:
                print(f"Unused index in {collection_name}: {stat['name']}")
    
    # Performance recommendations
    recommendations = []
    
    if db_stats['indexSize'] > db_stats['dataSize']:
        recommendations.append("Consider removing unused indexes")
    
    if slow_ops:
        recommendations.append("Optimize slow queries")
        recommendations.append("Consider adding appropriate indexes")
    
    return recommendations

# Run performance troubleshooting
performance_recommendations = troubleshoot_performance_issues()
for rec in performance_recommendations:
    print(f"Recommendation: {rec}")
```

#### 3. Data Integrity Issues
```python
# Data integrity troubleshooting
def troubleshoot_data_integrity():
    """
    Identify and resolve data integrity issues
    """
    integrity_issues = []
    
    # Check for orphaned records
    orphaned_reports = check_orphaned_reports()
    if orphaned_reports:
        integrity_issues.append({
            'type': 'orphaned_reports',
            'count': len(orphaned_reports),
            'fix': 'Remove orphaned reports or restore missing assessments'
        })
    
    # Check for duplicate records
    duplicate_users = check_duplicate_users()
    if duplicate_users:
        integrity_issues.append({
            'type': 'duplicate_users',
            'count': len(duplicate_users),
            'fix': 'Merge duplicate user accounts'
        })
    
    # Check for invalid references
    invalid_refs = check_invalid_references()
    if invalid_refs:
        integrity_issues.append({
            'type': 'invalid_references',
            'count': len(invalid_refs),
            'fix': 'Update references or remove invalid records'
        })
    
    return integrity_issues

def fix_data_integrity_issues(issues):
    """
    Automatically fix common data integrity issues
    """
    db = get_database_connection()
    
    for issue in issues:
        if issue['type'] == 'orphaned_reports':
            # Remove orphaned reports
            orphaned_reports = check_orphaned_reports()
            for report in orphaned_reports:
                db.reports.delete_one({'_id': report['_id']})
            print(f"Removed {len(orphaned_reports)} orphaned reports")
        
        elif issue['type'] == 'duplicate_users':
            # Merge duplicate users
            duplicate_users = check_duplicate_users()
            for duplicate_group in duplicate_users:
                merge_duplicate_users(duplicate_group)
            print(f"Merged {len(duplicate_users)} duplicate user groups")
        
        elif issue['type'] == 'invalid_references':
            # Fix invalid references
            invalid_refs = check_invalid_references()
            for ref in invalid_refs:
                fix_invalid_reference(ref)
            print(f"Fixed {len(invalid_refs)} invalid references")

# Run integrity troubleshooting
integrity_issues = troubleshoot_data_integrity()
if integrity_issues:
    print("Data integrity issues found:")
    for issue in integrity_issues:
        print(f"- {issue}")
    
    # Attempt automatic fixes
    fix_data_integrity_issues(integrity_issues)
else:
    print("No data integrity issues found")
```

### Emergency Procedures

#### 1. Emergency Stop
```bash
# Emergency migration stop script
#!/bin/bash

echo "EMERGENCY STOP: Halting migration immediately"

# Kill migration processes
pkill -f "migration"
pkill -f "migrate_data"

# Stop application to prevent further changes
kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind-prod

# Create emergency backup
python scripts/backup_restore.py --emergency-backup --tag="emergency-stop-$(date +%Y%m%d-%H%M)"

# Log emergency stop
echo "$(date): Emergency migration stop executed" >> /var/log/migration/emergency.log

echo "Emergency stop completed. System is in safe state."
echo "Manual intervention required before resuming operations."
```

#### 2. Emergency Recovery
```bash
# Emergency recovery script
#!/bin/bash

echo "Starting emergency recovery procedure..."

# Restore from last known good backup
BACKUP_TAG=$(python scripts/find_last_good_backup.py)
echo "Restoring from backup: $BACKUP_TAG"

python scripts/backup_restore.py --restore --tag="$BACKUP_TAG"

# Verify data integrity
python scripts/verify_data_integrity.py --emergency

# Restart application with limited capacity
kubectl scale deployment infra-mind-api --replicas=1 -n infra-mind-prod

# Run basic health checks
./scripts/health-check.sh --basic

echo "Emergency recovery completed"
echo "System restored to last known good state"
echo "Full system verification recommended before normal operations"
```

---

*This data migration guide should be reviewed and updated before each major migration to ensure all procedures are current and tested.*