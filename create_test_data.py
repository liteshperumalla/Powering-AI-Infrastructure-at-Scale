#!/usr/bin/env python3
"""
Create comprehensive test data with assessment, recommendations, and reports
to verify frontend displays everything correctly.
"""
import asyncio
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from src.infra_mind.schemas.base import AssessmentStatus, Priority, CloudProvider
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

async def create_comprehensive_test_data():
    print('🏗️  Creating comprehensive test data for frontend verification...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    try:
        await init_beanie(
            database=database,
            document_models=[Assessment, Recommendation, Report]
        )
    except Exception as e:
        print(f'Database init warning: {e}')
    
    # Create comprehensive test assessment
    assessment = Assessment(
        user_id='frontend_test_user',
        title='Frontend Integration Test Assessment',
        description='Complete test assessment with recommendations and reports for frontend verification',
        business_requirements={
            'business_goals': ['cost_optimization', 'scalability', 'performance'],
            'growth_projection': 'high',
            'budget_constraints': 25000,
            'team_structure': 'medium',
            'compliance_requirements': ['SOC2', 'GDPR'],
            'project_timeline_months': 9
        },
        technical_requirements={
            'current_infrastructure': 'cloud_hybrid',
            'workload_types': ['web_application', 'api_service', 'data_processing'],
            'performance_requirements': {'latency_ms': 200, 'throughput_rps': 1000},
            'scalability_requirements': {'auto_scaling': True, 'max_instances': 50},
            'security_requirements': {'encryption': True, 'vpc': True},
            'integration_requirements': {'third_party_apis': ['stripe', 'auth0']}
        },
        status=AssessmentStatus.COMPLETED,
        completion_percentage=100.0,
        recommendations_generated=True,
        reports_generated=True,
        progress={
            'current_step': 'completed',
            'completed_steps': ['created', 'analysis', 'recommendations', 'reports', 'visualization'],
            'total_steps': 5,
            'progress_percentage': 100.0
        },
        metadata={
            'workflow_completed_at': datetime.now(timezone.utc).isoformat(),
            'agents_executed': 5,
            'recommendations_generated': 8,
            'reports_generated': 3,
            'visualization_data_available': True
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    
    await assessment.insert()
    assessment_id = str(assessment.id)
    print(f'✅ Created test assessment: {assessment_id}')
    
    # Create comprehensive recommendations
    recommendations_data = [
        {
            'agent_name': 'cto_agent',
            'title': 'Strategic Cloud Migration',
            'summary': 'Implement comprehensive cloud-first strategy with multi-cloud flexibility for optimal cost and performance',
            'category': 'strategic',
            'services': [
                {
                    'service_name': 'Amazon EKS',
                    'provider': CloudProvider.AWS,
                    'service_category': 'container_orchestration',
                    'estimated_monthly_cost': 450,
                    'configuration': {'node_type': 't3.medium', 'min_nodes': 2, 'max_nodes': 10},
                    'reasons': ['Kubernetes orchestration', 'Auto-scaling capabilities', 'AWS integration'],
                    'setup_complexity': 'medium',
                    'implementation_time_hours': 40
                }
            ],
            'cost_estimates': {'total_monthly': 1200, 'annual_savings': 18000},
            'confidence_score': 0.92
        },
        {
            'agent_name': 'cloud_engineer_agent',
            'title': 'Infrastructure Architecture Optimization',
            'summary': 'Optimize current infrastructure with microservices architecture and serverless components',
            'category': 'infrastructure',
            'services': [
                {
                    'service_name': 'AWS Lambda',
                    'provider': CloudProvider.AWS,
                    'service_category': 'serverless_compute',
                    'estimated_monthly_cost': 180,
                    'configuration': {'memory': '512MB', 'timeout': '30s'},
                    'reasons': ['Cost-effective scaling', 'No server management', 'Event-driven architecture'],
                    'setup_complexity': 'low',
                    'implementation_time_hours': 20
                }
            ],
            'cost_estimates': {'total_monthly': 800, 'annual_savings': 12000},
            'confidence_score': 0.89
        },
        {
            'agent_name': 'compliance_agent',
            'title': 'Security and Compliance Framework',
            'summary': 'Implement comprehensive security controls and compliance monitoring for SOC2 and GDPR requirements',
            'category': 'security',
            'services': [
                {
                    'service_name': 'AWS WAF',
                    'provider': CloudProvider.AWS,
                    'service_category': 'security',
                    'estimated_monthly_cost': 120,
                    'configuration': {'rules': 'standard', 'monitoring': 'enabled'},
                    'reasons': ['Web application firewall', 'DDoS protection', 'Compliance ready'],
                    'setup_complexity': 'medium',
                    'implementation_time_hours': 30
                }
            ],
            'cost_estimates': {'total_monthly': 350, 'compliance_score': 95},
            'confidence_score': 0.94
        }
    ]
    
    created_recommendations = []
    for rec_data in recommendations_data:
        recommendation = Recommendation(
            assessment_id=assessment_id,
            user_id='frontend_test_user',
            agent_name=rec_data['agent_name'],
            agent_version='1.0',
            title=rec_data['title'],
            summary=rec_data['summary'],
            confidence_level='high',
            confidence_score=rec_data['confidence_score'],
            business_alignment=88,
            recommended_services=rec_data['services'],
            cost_estimates=rec_data['cost_estimates'],
            total_estimated_monthly_cost=str(rec_data['cost_estimates']['total_monthly']),
            implementation_steps=[
                'Review and approve recommendation',
                'Set up development environment',
                'Configure staging environment', 
                'Deploy to production',
                'Monitor and optimize'
            ],
            prerequisites=['Cloud account setup', 'IAM roles configuration', 'Network setup'],
            risks_and_considerations=['Initial migration complexity', 'Learning curve', 'Cost monitoring needed'],
            business_impact='high',
            alignment_score=88,
            tags=[rec_data['agent_name'], rec_data['category'], 'ai_generated'],
            priority=Priority.HIGH,
            category=rec_data['category'],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        await recommendation.insert()
        created_recommendations.append(str(recommendation.id))
    
    print(f'✅ Created {len(created_recommendations)} recommendations')
    
    # Create comprehensive reports
    from src.infra_mind.models.report import ReportType, ReportFormat, ReportStatus
    
    reports_data = [
        {
            'type': ReportType.EXECUTIVE_SUMMARY,
            'title': 'Executive Summary - Infrastructure Assessment',
            'description': 'High-level strategic recommendations and business impact analysis',
            'sections': ['executive_summary', 'key_recommendations', 'cost_analysis', 'risk_assessment']
        },
        {
            'type': ReportType.TECHNICAL_ROADMAP,
            'title': 'Technical Implementation Roadmap',
            'description': 'Detailed technical implementation plan with timelines and milestones',
            'sections': ['architecture_overview', 'implementation_phases', 'timeline', 'resource_requirements']
        },
        {
            'type': ReportType.COST_ANALYSIS,
            'title': 'Cost Analysis and Optimization',
            'description': 'Detailed cost breakdown, optimization opportunities, and ROI projections',
            'sections': ['current_costs', 'projected_costs', 'savings_opportunities', 'roi_analysis']
        }
    ]
    
    created_reports = []
    for report_data in reports_data:
        report = Report(
            assessment_id=assessment_id,
            user_id='frontend_test_user',
            title=report_data['title'],
            description=report_data['description'],
            report_type=report_data['type'],
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
            progress_percentage=100.0,
            sections=report_data['sections'],
            total_pages=12,
            word_count=3500,
            file_path=f'/reports/{report_data["type"].value}_{assessment_id}.pdf',
            file_size_bytes=2048000,
            generated_by=['report_generator_agent'],
            generation_time_seconds=4.2,
            completeness_score=0.96,
            confidence_score=0.91,
            priority=Priority.HIGH,
            tags=[report_data['type'].value, 'comprehensive', 'frontend_test'],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        await report.insert()
        created_reports.append(str(report.id))
    
    print(f'✅ Created {len(created_reports)} reports')
    
    client.close()
    
    print(f'🎯 Test data summary:')
    print(f'   Assessment ID: {assessment_id}')
    print(f'   Recommendations: {len(created_recommendations)}')
    print(f'   Reports: {len(created_reports)}')
    print(f'   Status: COMPLETED (100%)')
    
    return assessment_id

if __name__ == "__main__":
    assessment_id = asyncio.run(create_comprehensive_test_data())
    print(f'\\n🔍 Use this assessment ID for frontend testing: {assessment_id}')