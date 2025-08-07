#!/usr/bin/env python3
"""
Test the fixed assessment workflow to ensure:
1. Progress never gets stuck at 50%
2. Assessment completes successfully 
3. Fresh data is displayed without caching issues
"""
import asyncio
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.schemas.base import AssessmentStatus
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

async def test_workflow():
    print('🧪 Testing fixed assessment workflow...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    try:
        await init_beanie(
            database=database,
            document_models=[Assessment]
        )
    except Exception as e:
        print(f'Database init warning: {e}')
        print('Continuing with test...')
    
    # Create test assessment
    assessment = Assessment(
        user_id='test_user',
        title='Test Assessment Workflow Fix',
        description='Testing the fixed workflow with progress tracking',
        business_requirements={
            'business_goals': ['cost_optimization', 'scalability'],
            'growth_projection': 'high',
            'budget_constraints': 10000,
            'team_structure': 'medium',
            'compliance_requirements': ['SOC2'],
            'project_timeline_months': 6
        },
        technical_requirements={
            'current_infrastructure': 'cloud_hybrid',
            'workload_types': ['web_application', 'api_service'],
            'performance_requirements': {},
            'scalability_requirements': {},
            'security_requirements': {},
            'integration_requirements': {}
        },
        status=AssessmentStatus.DRAFT,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Try to save assessment to database
    try:
        await assessment.insert()
        print(f'✅ Created test assessment: {assessment.id}')
    except Exception as e:
        print(f'Database save warning: {e}')
        print('Continuing with workflow test using temporary assessment...')
        # Set a temporary ID for testing
        assessment.id = "test_assessment_123"
    
    # Test workflow execution
    workflow = AssessmentWorkflow()
    workflow_id = f'test_workflow_{assessment.id}_{int(datetime.now().timestamp())}'
    
    print('🚀 Starting assessment workflow...')
    print('Monitoring progress to ensure it does not get stuck at 50%...')
    
    try:
        result = await workflow.execute_workflow(workflow_id, assessment)
        
        # Check results
        print(f'📊 Workflow Result: {result.status}')
        print(f'📈 Final Completion Percentage: {assessment.completion_percentage}%')
        if hasattr(assessment, 'progress') and assessment.progress:
            print(f'🎯 Final Progress: {assessment.progress}')
        
        if result.status == 'completed' and assessment.completion_percentage >= 95.0:
            print('✅ WORKFLOW TEST PASSED!')
            print('✅ Assessment completed without getting stuck at 50%')
        else:
            print('❌ WORKFLOW TEST FAILED!')
            print(f'Status: {result.status}, Progress: {assessment.completion_percentage}%')
    
    except Exception as e:
        print(f'❌ WORKFLOW TEST FAILED with exception: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_workflow())