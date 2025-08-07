#!/usr/bin/env python3
"""
Create complete test setup with:
1. Test user with proper authentication
2. Complete assessment with full workflow
3. Recommendations and reports
4. Verify frontend can access all data
"""
import asyncio
import os
import json
from datetime import datetime, timezone
from typing import Optional

# Import all required models and services
from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from src.infra_mind.schemas.base import AssessmentStatus, Priority, CloudProvider
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from src.infra_mind.core.auth import PasswordManager
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def create_complete_test_setup():
    print('🏗️  Creating complete test setup with authentication...')
    
    # Connect to database with authentication
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    try:
        await init_beanie(
            database=database,
            document_models=[User, Assessment, Recommendation, Report]
        )
        print('✅ Connected to database with authentication')
    except Exception as e:
        print(f'Database connection error: {e}')
        return None, None
    
    # Step 1: Create test user
    print('👤 Creating test user...')
    test_user = User(
        email='test@inframind.ai',
        hashed_password=PasswordManager.hash_password('TestPassword123!'),
        full_name='Test User',
        company='Test Company',
        role='admin',
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Check if user already exists
    existing_user = await User.find_one(User.email == test_user.email)
    if existing_user:
        print('👤 Test user already exists, using existing user')
        test_user = existing_user
    else:
        await test_user.insert()
        print(f'✅ Created test user: {test_user.email}')
    
    # Step 2: Create comprehensive assessment
    print('📋 Creating comprehensive assessment...')
    assessment = Assessment(
        user_id=str(test_user.id),
        title='Production-Ready Infrastructure Assessment',
        description='Complete assessment for testing recommendations, reports, and visualizations',
        business_requirements={
            'business_goals': ['cost_optimization', 'scalability', 'performance', 'security'],
            'growth_projection': 'high',
            'budget_constraints': 50000,
            'team_structure': 'medium',
            'compliance_requirements': ['SOC2', 'GDPR', 'HIPAA'],
            'project_timeline_months': 12
        },
        technical_requirements={
            'current_infrastructure': 'cloud_hybrid',
            'workload_types': ['web_application', 'api_service', 'data_processing', 'machine_learning'],
            'performance_requirements': {
                'latency_ms': 100,
                'throughput_rps': 5000,
                'availability_percent': 99.9
            },
            'scalability_requirements': {
                'auto_scaling': True,
                'max_instances': 100,
                'load_balancing': True
            },
            'security_requirements': {
                'encryption': True,
                'vpc': True,
                'waf': True,
                'monitoring': True
            },
            'integration_requirements': {
                'third_party_apis': ['stripe', 'auth0', 'sendgrid'],
                'databases': ['postgresql', 'redis'],
                'message_queues': ['rabbitmq']
            }
        },
        status=AssessmentStatus.DRAFT,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await assessment.insert()
    assessment_id = str(assessment.id)
    print(f'✅ Created assessment: {assessment_id}')
    
    # Step 3: Execute complete workflow
    print('🚀 Executing complete assessment workflow...')
    workflow = AssessmentWorkflow()
    workflow_id = f'complete_test_workflow_{assessment_id}_{int(datetime.now().timestamp())}'
    
    try:
        result = await workflow.execute_workflow(workflow_id, assessment)
        print(f'📊 Workflow completed with status: {result.status}')
        print(f'📈 Final completion: {assessment.completion_percentage}%')
    except Exception as e:
        print(f'❌ Workflow execution failed: {e}')
        # Continue anyway to test manual creation
    
    # Step 4: Create comprehensive recommendations (if workflow didn't create them)
    recommendations = await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()
    if len(recommendations) == 0:
        print('💡 Creating comprehensive recommendations manually...')
        
        recommendation_data = [
            {
                'agent_name': 'cto_agent',
                'title': 'Strategic Cloud Architecture',
                'summary': 'Implement cloud-native architecture with Kubernetes orchestration for scalability and cost optimization',
                'services': [
                    {
                        'service_name': 'Amazon EKS',
                        'provider': 'AWS',
                        'service_category': 'container_orchestration',
                        'estimated_monthly_cost': 800,
                        'configuration': {'node_type': 'm5.large', 'min_nodes': 3, 'max_nodes': 20},
                        'reasons': ['Auto-scaling', 'High availability', 'Cost optimization'],
                        'setup_complexity': 'medium',
                        'implementation_time_hours': 60
                    }
                ],
                'cost_estimates': {'total_monthly': 2500, 'annual_savings': 30000},
                'confidence_score': 0.95
            },
            {
                'agent_name': 'cloud_engineer_agent', 
                'title': 'Infrastructure Optimization',
                'summary': 'Optimize infrastructure with serverless components and managed services',
                'services': [
                    {
                        'service_name': 'AWS Lambda',
                        'provider': 'AWS',
                        'service_category': 'serverless_compute',
                        'estimated_monthly_cost': 300,
                        'configuration': {'memory': '1024MB', 'timeout': '60s'},
                        'reasons': ['Cost-effective', 'Auto-scaling', 'Managed service'],
                        'setup_complexity': 'low',
                        'implementation_time_hours': 24
                    }
                ],
                'cost_estimates': {'total_monthly': 1200, 'annual_savings': 18000},
                'confidence_score': 0.92
            },
            {
                'agent_name': 'compliance_agent',
                'title': 'Security & Compliance Framework', 
                'summary': 'Implement comprehensive security controls for SOC2, GDPR, and HIPAA compliance',
                'services': [
                    {
                        'service_name': 'AWS Security Hub',
                        'provider': 'AWS',
                        'service_category': 'security',
                        'estimated_monthly_cost': 200,
                        'configuration': {'compliance_standards': ['SOC2', 'GDPR'], 'monitoring': 'enabled'},
                        'reasons': ['Compliance monitoring', 'Security insights', 'Centralized dashboard'],
                        'setup_complexity': 'high',
                        'implementation_time_hours': 80
                    }
                ],
                'cost_estimates': {'total_monthly': 600, 'compliance_score': 98},
                'confidence_score': 0.94
            }
        ]
        
        for rec_data in recommendation_data:
            rec = Recommendation(
                assessment_id=assessment_id,
                user_id=str(test_user.id),
                agent_name=rec_data['agent_name'],
                agent_version='1.0',
                title=rec_data['title'],
                summary=rec_data['summary'],
                confidence_level='high',
                confidence_score=rec_data['confidence_score'],
                business_alignment=92,
                recommended_services=rec_data['services'],
                cost_estimates=rec_data['cost_estimates'],
                total_estimated_monthly_cost=str(rec_data['cost_estimates']['total_monthly']),
                implementation_steps=[
                    'Review and approve recommendation',
                    'Set up development environment',
                    'Configure staging environment',
                    'Implement monitoring and logging',
                    'Deploy to production',
                    'Performance testing and optimization'
                ],
                prerequisites=['AWS account', 'IAM setup', 'Network configuration'],
                risks_and_considerations=['Migration complexity', 'Team training required', 'Initial costs'],
                business_impact='high',
                alignment_score=92,
                tags=[rec_data['agent_name'], 'production_ready', 'ai_generated'],
                priority=Priority.HIGH,
                category='infrastructure',
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            await rec.insert()
        
        print(f'✅ Created {len(recommendation_data)} recommendations')
    else:
        print(f'✅ Found {len(recommendations)} existing recommendations')
    
    # Step 5: Create comprehensive reports (if workflow didn't create them)
    reports = await Report.find(Report.assessment_id == assessment_id).to_list()
    if len(reports) == 0:
        print('📄 Creating comprehensive reports manually...')
        
        from src.infra_mind.models.report import ReportType, ReportFormat, ReportStatus
        
        report_data = [
            {
                'type': ReportType.EXECUTIVE_SUMMARY,
                'title': 'Executive Summary - Infrastructure Strategy',
                'content': 'Strategic overview of recommended infrastructure improvements with business impact analysis and ROI projections.',
                'sections': ['executive_overview', 'key_recommendations', 'business_impact', 'roi_analysis']
            },
            {
                'type': ReportType.TECHNICAL_ROADMAP,
                'title': 'Technical Implementation Roadmap',
                'content': 'Detailed technical implementation plan with phase-by-phase deployment strategy and resource allocation.',
                'sections': ['current_state', 'target_architecture', 'migration_plan', 'implementation_timeline']
            },
            {
                'type': ReportType.COST_ANALYSIS,
                'title': 'Cost Analysis & Optimization',
                'content': 'Comprehensive cost breakdown with optimization opportunities and long-term financial projections.',
                'sections': ['current_costs', 'projected_costs', 'optimization_opportunities', 'cost_savings']
            }
        ]
        
        for report_info in report_data:
            report = Report(
                assessment_id=assessment_id,
                user_id=str(test_user.id),
                title=report_info['title'],
                description=report_info['content'],
                report_type=report_info['type'],
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=report_info['sections'],
                total_pages=15,
                word_count=4500,
                file_path=f'/reports/{report_info["type"].value}_{assessment_id}.pdf',
                file_size_bytes=3145728,  # 3MB
                generated_by=['report_generator_agent'],
                generation_time_seconds=6.8,
                completeness_score=0.98,
                confidence_score=0.95,
                priority=Priority.HIGH,
                tags=[report_info['type'].value, 'comprehensive', 'production_ready'],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            
            await report.insert()
        
        print(f'✅ Created {len(report_data)} reports')
    else:
        print(f'✅ Found {len(reports)} existing reports')
    
    # Step 6: Update assessment to completed status
    assessment.status = AssessmentStatus.COMPLETED
    assessment.completion_percentage = 100.0
    assessment.recommendations_generated = True
    assessment.reports_generated = True
    assessment.completed_at = datetime.now(timezone.utc)
    assessment.updated_at = datetime.now(timezone.utc)
    await assessment.save()
    
    print(f'✅ Updated assessment to completed status')
    
    client.close()
    
    # Return data for testing
    return {
        'user_id': str(test_user.id),
        'user_email': test_user.email,
        'assessment_id': assessment_id,
        'assessment_title': assessment.title,
        'recommendations_count': len(await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()),
        'reports_count': len(await Report.find(Report.assessment_id == assessment_id).to_list())
    }

if __name__ == "__main__":
    result = asyncio.run(create_complete_test_setup())
    if result:
        print(f'\\n🎉 COMPLETE TEST SETUP READY!')
        print(f'📧 Test User: {result["user_email"]}')
        print(f'📋 Assessment: {result["assessment_title"]}')
        print(f'🆔 Assessment ID: {result["assessment_id"]}')
        print(f'💡 Recommendations: {result["recommendations_count"]}')
        print(f'📄 Reports: {result["reports_count"]}')
        print(f'\\n🔗 Frontend URLs to test:')
        print(f'   • Dashboard: http://localhost:3000/dashboard')
        print(f'   • Assessment: http://localhost:3000/assessment/{result["assessment_id"]}')
        print(f'   • Recommendations: http://localhost:3000/recommendations/{result["assessment_id"]}')
        print(f'\\n🧪 API Endpoints to test:')
        print(f'   • Login: POST /api/v2/auth/login')
        print(f'   • Assessments: GET /api/v2/assessments/')
        print(f'   • Assessment Detail: GET /api/v2/assessments/{result["assessment_id"]}')
        print(f'   • Recommendations: GET /api/v2/recommendations/{result["assessment_id"]}')
        print(f'   • Visualization: GET /api/v2/assessments/{result["assessment_id"]}/visualization-data')
    else:
        print('❌ Test setup failed')