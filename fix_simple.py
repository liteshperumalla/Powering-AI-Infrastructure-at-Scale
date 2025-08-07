#!/usr/bin/env python3
"""
Simple fix - clear all data and create fresh validated data without complex structures
"""
import asyncio
import os
from datetime import datetime, timezone
from decimal import Decimal

from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report, ReportType, ReportFormat, ReportStatus
from src.infra_mind.schemas.base import AssessmentStatus, Priority, CloudProvider, RecommendationConfidence
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_simple():
    print('🧹 Simple fix - clearing all and creating fresh data...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    await init_beanie(
        database=database,
        document_models=[User, Assessment, Recommendation, Report]
    )
    print('✅ Connected to database')
    
    # Get the test user and assessment
    user = await User.find_one(User.email == 'test@inframind.ai')
    if not user:
        print('❌ No test user found')
        return
        
    # Clear ALL data for fresh start - get assessments first
    user_assessments = await Assessment.find(Assessment.user_id == str(user.id)).to_list()
    for assess in user_assessments:
        await Recommendation.find(Recommendation.assessment_id == str(assess.id)).delete()
        await Report.find(Report.assessment_id == str(assess.id)).delete()
    await Assessment.find(Assessment.user_id == str(user.id)).delete()
    print('🧹 Cleared all existing data')
    
    # Create fresh assessment
    assessment = Assessment(
        user_id=str(user.id),
        title='Test Infrastructure Assessment',
        description='Fresh assessment with proper data',
        business_requirements={
            'business_goals': ['cost_optimization', 'scalability'],
            'budget_constraints': 25000
        },
        technical_requirements={
            'current_infrastructure': 'cloud',
            'workload_types': ['web_application', 'api_service']
        },
        status=AssessmentStatus.COMPLETED,
        completion_percentage=100.0,
        recommendations_generated=True,
        reports_generated=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    
    await assessment.insert()
    assessment_id = str(assessment.id)
    print(f'✅ Created assessment: {assessment_id}')
    
    # Create simple recommendations - avoid complex fields
    rec_data = [
        {
            'agent_name': 'cto_agent',
            'title': 'Cloud Infrastructure Optimization',
            'summary': 'Optimize cloud infrastructure for better performance and cost efficiency',
            'confidence_level': RecommendationConfidence.HIGH,
            'confidence_score': 0.88,
            'alignment_score': 0.85,
            'total_cost': 1200.00,
            'category': 'architecture'
        },
        {
            'agent_name': 'cost_agent', 
            'title': 'Cost Reduction Strategy',
            'summary': 'Implement cost reduction measures across cloud services',
            'confidence_level': RecommendationConfidence.HIGH,
            'confidence_score': 0.92,
            'alignment_score': 0.90,
            'total_cost': 800.00,
            'category': 'cost_optimization'
        },
        {
            'agent_name': 'security_agent',
            'title': 'Security Enhancement',
            'summary': 'Enhance security controls and compliance measures',
            'confidence_level': RecommendationConfidence.VERY_HIGH,
            'confidence_score': 0.95,
            'alignment_score': 0.93,
            'total_cost': 600.00,
            'category': 'security'
        }
    ]
    
    for i, data in enumerate(rec_data):
        rec = Recommendation(
            assessment_id=assessment_id,
            user_id=str(user.id),
            agent_name=data['agent_name'],
            agent_version='2.0',
            title=data['title'], 
            summary=data['summary'],
            confidence_level=data['confidence_level'],
            confidence_score=data['confidence_score'],
            recommendation_data={
                'analysis': f'Strategic analysis from {data["agent_name"]}',
                'methodology': 'AI-driven assessment with validation'
            },
            cost_estimates={
                'total_monthly': data['total_cost'],
                'annual_projection': data['total_cost'] * 12
            },
            total_estimated_monthly_cost=Decimal(str(data['total_cost'])),
            implementation_steps=[
                f'Review {data["title"]} recommendations',
                'Plan implementation approach',
                'Execute in development environment',
                'Deploy to production with monitoring'
            ],
            business_impact='high',
            alignment_score=data['alignment_score'],
            tags=[data['agent_name'], data['category'], 'validated'],
            priority=Priority.HIGH,
            category=data['category'],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        await rec.insert()
        print(f'  ✅ {data["title"]}')
    
    print(f'✅ Created {len(rec_data)} recommendations')
    
    # Create simple reports
    report_types = [
        (ReportType.EXECUTIVE_SUMMARY, 'Executive Summary Report'),
        (ReportType.TECHNICAL_ROADMAP, 'Technical Implementation Roadmap'),
        (ReportType.COST_ANALYSIS, 'Cost Analysis Report')
    ]
    
    for i, (report_type, title) in enumerate(report_types):
        report = Report(
            assessment_id=assessment_id,
            user_id=str(user.id),
            title=title,
            description=f'Comprehensive {title.lower()} with analysis and recommendations',
            report_type=report_type,
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
            progress_percentage=100.0,
            sections=['executive_summary', 'key_findings', 'recommendations', 'implementation_plan'],
            total_pages=10 + (i * 2),
            word_count=2500 + (i * 500),
            file_path=f'/reports/{report_type.value}_{assessment_id}.pdf',
            file_size_bytes=2000000 + (i * 300000),
            generated_by=['report_generator_v2'],
            generation_time_seconds=3.5 + (i * 0.8),
            completeness_score=0.95,
            confidence_score=0.92,
            priority=Priority.HIGH,
            tags=[report_type.value, 'production_ready'],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        await report.insert()
        print(f'  ✅ {title}')
    
    print(f'✅ Created {len(report_types)} reports')
    
    # Verify data
    recs_count = await Recommendation.find(Recommendation.assessment_id == assessment_id).count()
    reports_count = await Report.find(Report.assessment_id == assessment_id).count()
    
    print(f'\n✅ Verification:')
    print(f'   - Assessment: {assessment.status} ({assessment.completion_percentage}%)')
    print(f'   - Recommendations: {recs_count}')
    print(f'   - Reports: {reports_count}')
    
    client.close()
    
    return {
        'assessment_id': assessment_id,
        'recommendations_count': recs_count,
        'reports_count': reports_count,
        'status': assessment.status
    }

if __name__ == "__main__":
    result = asyncio.run(fix_simple())
    if result:
        print(f'\n🎉 SIMPLE FIX COMPLETED!')
        print(f'📋 Assessment ID: {result["assessment_id"]}')
        print(f'💡 Recommendations: {result["recommendations_count"]}')
        print(f'📄 Reports: {result["reports_count"]}')
        print(f'✅ Status: {result["status"]}')
        print(f'\n🔗 Frontend should now show:')
        print(f'   • Dashboard with completed assessment')
        print(f'   • Varied recommendation scores')
        print(f'   • Working reports page')
        print(f'   • 100% completion (not stuck at 50%)')
    else:
        print('❌ Simple fix failed')