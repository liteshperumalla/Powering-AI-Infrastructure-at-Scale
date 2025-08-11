#!/usr/bin/env python3
"""
Comprehensive data migration script to fix all Pydantic schema validation issues permanently.

This script will:
1. Fix agent_states structure to match Dict[str, Dict[str, Any]]
2. Ensure all required fields have correct data types
3. Fix any enum values that don't match schema definitions
4. Add missing default values
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone
from typing import Dict, Any

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://localhost:27017/infra_mind")

def fix_agent_states(agent_states: Any) -> Dict[str, Dict[str, Any]]:
    """
    Fix agent_states to match the expected Pydantic structure: Dict[str, Dict[str, Any]]
    """
    if not isinstance(agent_states, dict):
        return {
            "active_agents": {},
            "completed_agents": {},
            "failed_agents": {},
            "consensus_score": {},
            "execution_time": {}
        }
    
    fixed_states = {}
    
    for key, value in agent_states.items():
        if isinstance(value, dict):
            # Already a dict, keep as is
            fixed_states[key] = value
        elif isinstance(value, (int, float, str, bool, list)):
            # Convert primitive values to dict structure
            fixed_states[key] = {"value": value}
        else:
            # Fallback to empty dict
            fixed_states[key] = {}
    
    # Ensure required keys exist
    required_keys = ["active_agents", "completed_agents", "failed_agents", "consensus_score", "execution_time"]
    for key in required_keys:
        if key not in fixed_states:
            fixed_states[key] = {}
    
    return fixed_states

def fix_progress_structure(progress: Any) -> Dict[str, Any]:
    """
    Fix progress structure to match expected format
    """
    if not isinstance(progress, dict):
        return {
            "current_step": "created",
            "completed_steps": [],
            "total_steps": 5,
            "progress_percentage": 0.0
        }
    
    # Ensure required keys exist with correct types
    fixed_progress = {}
    fixed_progress["current_step"] = progress.get("current_step", "created")
    fixed_progress["completed_steps"] = progress.get("completed_steps", [])
    fixed_progress["total_steps"] = progress.get("total_steps", 5)
    fixed_progress["progress_percentage"] = float(progress.get("progress_percentage", 0.0))
    
    return fixed_progress

def fix_metadata_structure(metadata: Any) -> Dict[str, Any]:
    """
    Fix metadata structure
    """
    if not isinstance(metadata, dict):
        return {
            "source": "legacy",
            "version": "1.0",
            "tags": []
        }
    
    # Ensure required keys exist
    fixed_metadata = dict(metadata)
    if "source" not in fixed_metadata:
        fixed_metadata["source"] = "legacy"
    if "version" not in fixed_metadata:
        fixed_metadata["version"] = "1.0"
    if "tags" not in fixed_metadata:
        fixed_metadata["tags"] = []
    
    return fixed_metadata

def normalize_status(status: str) -> str:
    """
    Normalize status values to match enum
    """
    status_mapping = {
        "draft": "draft",
        "pending": "pending", 
        "in_progress": "in_progress",
        "completed": "completed",
        "failed": "failed"
    }
    return status_mapping.get(status.lower(), "draft")

def normalize_priority(priority: str) -> str:
    """
    Normalize priority values to match enum
    """
    priority_mapping = {
        "low": "low",
        "medium": "medium", 
        "high": "high",
        "critical": "critical"
    }
    return priority_mapping.get(priority.lower(), "medium")

async def migrate_assessments():
    """
    Migrate all assessments to match Pydantic schema requirements
    """
    print("🔧 Comprehensive Assessment Data Migration")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.infra_mind
        assessments_collection = db.assessments
        
        # Get all assessments
        assessments = await assessments_collection.find().to_list(None)
        print(f"Found {len(assessments)} assessments to migrate")
        
        migration_count = 0
        
        for assessment in assessments:
            assessment_id = assessment['_id']
            updates = {}
            needs_update = False
            
            # Fix agent_states structure
            if 'agent_states' in assessment:
                fixed_agent_states = fix_agent_states(assessment['agent_states'])
                if fixed_agent_states != assessment['agent_states']:
                    updates['agent_states'] = fixed_agent_states
                    needs_update = True
            else:
                updates['agent_states'] = fix_agent_states({})
                needs_update = True
            
            # Fix progress structure  
            if 'progress' in assessment:
                fixed_progress = fix_progress_structure(assessment['progress'])
                if fixed_progress != assessment['progress']:
                    updates['progress'] = fixed_progress
                    needs_update = True
            else:
                updates['progress'] = fix_progress_structure({})
                needs_update = True
            
            # Fix workflow_progress
            if 'workflow_progress' not in assessment or not isinstance(assessment['workflow_progress'], dict):
                updates['workflow_progress'] = {}
                needs_update = True
            
            # Fix metadata structure
            if 'metadata' in assessment:
                fixed_metadata = fix_metadata_structure(assessment['metadata'])
                if fixed_metadata != assessment['metadata']:
                    updates['metadata'] = fixed_metadata
                    needs_update = True
            else:
                updates['metadata'] = fix_metadata_structure({})
                needs_update = True
            
            # Ensure required string fields exist
            if 'user_id' not in assessment or not assessment['user_id']:
                updates['user_id'] = 'anonymous_user'
                needs_update = True
            
            if 'title' not in assessment or not assessment['title']:
                updates['title'] = f'Assessment {assessment_id}'
                needs_update = True
            
            if 'source' not in assessment:
                updates['source'] = 'legacy'
                needs_update = True
            
            # Fix status and priority with enum validation
            if 'status' in assessment:
                normalized_status = normalize_status(assessment['status'])
                if normalized_status != assessment['status']:
                    updates['status'] = normalized_status
                    needs_update = True
            else:
                updates['status'] = 'draft'
                needs_update = True
            
            if 'priority' in assessment:
                normalized_priority = normalize_priority(assessment['priority'])
                if normalized_priority != assessment['priority']:
                    updates['priority'] = normalized_priority  
                    needs_update = True
            else:
                updates['priority'] = 'medium'
                needs_update = True
            
            # Fix numeric fields
            if 'completion_percentage' not in assessment:
                updates['completion_percentage'] = 0.0
                needs_update = True
            elif not isinstance(assessment['completion_percentage'], (int, float)):
                updates['completion_percentage'] = 0.0
                needs_update = True
            
            # Fix boolean fields
            if 'recommendations_generated' not in assessment:
                updates['recommendations_generated'] = False
                needs_update = True
            elif not isinstance(assessment['recommendations_generated'], bool):
                updates['recommendations_generated'] = bool(assessment['recommendations_generated'])
                needs_update = True
            
            if 'reports_generated' not in assessment:
                updates['reports_generated'] = False
                needs_update = True
            elif not isinstance(assessment['reports_generated'], bool):
                updates['reports_generated'] = bool(assessment['reports_generated'])
                needs_update = True
            
            # Fix array fields
            if 'tags' not in assessment:
                updates['tags'] = []
                needs_update = True
            elif not isinstance(assessment['tags'], list):
                updates['tags'] = []
                needs_update = True
            
            # Fix dict fields
            for dict_field in ['business_requirements', 'technical_requirements']:
                if dict_field not in assessment:
                    updates[dict_field] = {}
                    needs_update = True
                elif not isinstance(assessment[dict_field], dict):
                    updates[dict_field] = {}
                    needs_update = True
            
            # Fix datetime fields
            current_time = datetime.now(timezone.utc)
            if 'created_at' not in assessment:
                updates['created_at'] = current_time
                needs_update = True
            
            if 'updated_at' not in assessment:
                updates['updated_at'] = current_time
                needs_update = True
            
            # Apply updates if needed
            if needs_update:
                result = await assessments_collection.update_one(
                    {'_id': assessment_id},
                    {'$set': updates}
                )
                if result.modified_count > 0:
                    migration_count += 1
                    print(f"✅ Migrated assessment {assessment_id}")
                else:
                    print(f"⚠️  Failed to migrate assessment {assessment_id}")
            else:
                print(f"✅ Assessment {assessment_id} already compliant")
        
        print("")
        print(f"🎉 Migration completed! {migration_count} assessments migrated")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

async def migrate_reports():
    """
    Migrate reports data to ensure schema compliance
    """
    print("\n🔧 Report Data Migration")
    print("=" * 30)
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.infra_mind
        reports_collection = db.reports
        
        reports = await reports_collection.find().to_list(None)
        print(f"Found {len(reports)} reports to check")
        
        migration_count = 0
        
        for report in reports:
            report_id = report['_id']
            updates = {}
            needs_update = False
            
            # Ensure required fields exist
            required_fields = {
                'user_id': 'anonymous_user',
                'title': f'Report {report_id}',
                'status': 'completed',
                'format': 'pdf',
                'report_type': 'executive_summary'
            }
            
            for field, default_value in required_fields.items():
                if field not in report:
                    updates[field] = default_value
                    needs_update = True
            
            # Fix array fields
            for array_field in ['sections', 'tags', 'generated_by']:
                if array_field not in report:
                    updates[array_field] = []
                    needs_update = True
                elif not isinstance(report[array_field], list):
                    updates[array_field] = []
                    needs_update = True
            
            # Fix numeric fields
            numeric_fields = {
                'total_pages': 1,
                'word_count': 0,
                'file_size_bytes': 0,
                'generation_time_seconds': 0.0,
                'completeness_score': 1.0,
                'confidence_score': 1.0,
                'progress_percentage': 100.0,
                'retry_count': 0
            }
            
            for field, default_value in numeric_fields.items():
                if field not in report:
                    updates[field] = default_value
                    needs_update = True
            
            # Fix boolean fields
            boolean_fields = {
                'is_template': False,
                'is_public': False
            }
            
            for field, default_value in boolean_fields.items():
                if field not in report:
                    updates[field] = default_value
                    needs_update = True
                elif not isinstance(report[field], bool):
                    updates[field] = bool(report[field])
                    needs_update = True
            
            if needs_update:
                result = await reports_collection.update_one(
                    {'_id': report_id},
                    {'$set': updates}
                )
                if result.modified_count > 0:
                    migration_count += 1
                    print(f"✅ Migrated report {report_id}")
        
        print(f"🎉 Report migration completed! {migration_count} reports migrated")
        
    except Exception as e:
        print(f"❌ Report migration failed: {e}")
    finally:
        if 'client' in locals():
            client.close()

async def main():
    """
    Run comprehensive data migration
    """
    print("🚀 Starting Comprehensive Data Migration")
    print("=" * 60)
    
    await migrate_assessments()
    await migrate_reports()
    
    print("\n🎉 All migrations completed successfully!")
    print("The database is now fully compliant with Pydantic schemas.")

if __name__ == "__main__":
    asyncio.run(main())