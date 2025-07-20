"""
Integration tests for Beanie document models.

Learning Note: These tests verify that our models work correctly
with the database and our Pydantic schemas integrate properly.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation, ServiceRecommendation
from src.infra_mind.schemas.business import (
    BusinessRequirements, BusinessGoal, GrowthProjection, 
    BudgetConstraints, TeamStructure
)
from src.infra_mind.schemas.technical import (
    TechnicalRequirements, PerformanceRequirement, 
    ScalabilityRequirement, SecurityRequirement, IntegrationRequirement
)
from src.infra_mind.schemas.base import (
    CompanySize, Industry, BudgetRange, WorkloadType, 
    AssessmentStatus, Priority, RecommendationConfidence, CloudProvider
)


class TestModelCreation:
    """Test creating models with our new schemas."""
    
    def test_assessment_creation_with_schemas(self):
        """Test creating an assessment with structured schemas."""
        # Create business requirements
        business_req = BusinessRequirements(
            company_size=CompanySize.MEDIUM,
            industry=Industry.TECHNOLOGY,
            business_goals=[
                BusinessGoal(
                    goal="Scale to handle 1M users",
                    priority=Priority.HIGH,
                    timeline_months=12,
                    success_metrics=["User growth", "System uptime"]
                )
            ],
            growth_projection=GrowthProjection(
                current_users=50000,
                projected_users_12m=1000000,
                current_revenue=Decimal("500000")
            ),
            budget_constraints=BudgetConstraints(
                total_budget_range=BudgetRange.RANGE_100K_500K,
                monthly_budget_limit=Decimal("25000"),
                compute_percentage=40,
                storage_percentage=20
            ),
            team_structure=TeamStructure(
                total_developers=15,
                senior_developers=5,
                devops_engineers=3,
                data_engineers=2,
                cloud_expertise_level=4
            ),
            project_timeline_months=12
        )
        
        # Create technical requirements
        tech_req = TechnicalRequirements(
            workload_types=[WorkloadType.WEB_APPLICATION, WorkloadType.API_SERVICE],
            performance_requirements=PerformanceRequirement(
                api_response_time_ms=200,
                requests_per_second=5000,
                uptime_percentage=Decimal("99.9"),
                concurrent_users=10000
            ),
            scalability_requirements=ScalabilityRequirement(
                current_data_size_gb=500,
                auto_scaling_required=True,
                global_distribution_required=True,
                planned_regions=["us-east-1", "eu-west-1", "ap-southeast-1"]
            ),
            security_requirements=SecurityRequirement(
                encryption_at_rest_required=True,
                multi_factor_auth_required=True,
                vpc_isolation_required=True
            ),
            integration_requirements=IntegrationRequirement(
                existing_databases=["PostgreSQL", "Redis"],
                rest_api_required=True,
                real_time_sync_required=True
            )
        )
        
        # Create assessment
        assessment = Assessment(
            user_id="user123",
            title="E-commerce Platform Scaling Assessment",
            description="Assessment for scaling our e-commerce platform to handle growth",
            business_requirements=business_req,
            technical_requirements=tech_req,
            priority=Priority.HIGH,
            tags=["e-commerce", "scaling", "high-priority"]
        )
        
        # Verify the assessment was created correctly
        assert assessment.title == "E-commerce Platform Scaling Assessment"
        assert assessment.status == AssessmentStatus.DRAFT
        assert assessment.priority == Priority.HIGH
        assert assessment.business_requirements.company_size == CompanySize.MEDIUM
        assert assessment.business_requirements.industry == Industry.TECHNOLOGY
        assert len(assessment.business_requirements.business_goals) == 1
        assert assessment.technical_requirements.performance_requirements.api_response_time_ms == 200
        assert len(assessment.technical_requirements.workload_types) == 2
        assert assessment.completion_percentage == 0.0
        assert not assessment.is_complete
    
    def test_service_recommendation_creation(self):
        """Test creating service recommendations."""
        service_rec = ServiceRecommendation(
            service_name="Amazon EC2",
            provider=CloudProvider.AWS,
            service_category="compute",
            estimated_monthly_cost=Decimal("1500.00"),
            cost_model="on-demand",
            configuration={
                "instance_type": "m5.xlarge",
                "vcpus": 4,
                "memory_gb": 16,
                "storage_gb": 100
            },
            reasons=[
                "Matches performance requirements",
                "Cost-effective for expected load",
                "Easy to scale horizontally"
            ],
            alternatives=["Azure Virtual Machines", "Google Compute Engine"],
            setup_complexity="medium",
            implementation_time_hours=8
        )
        
        assert service_rec.service_name == "Amazon EC2"
        assert service_rec.provider == CloudProvider.AWS
        assert service_rec.estimated_monthly_cost == Decimal("1500.00")
        assert len(service_rec.reasons) == 3
        assert service_rec.setup_complexity == "medium"
    
    def test_recommendation_creation_with_services(self):
        """Test creating recommendations with service recommendations."""
        # Create service recommendations
        ec2_service = ServiceRecommendation(
            service_name="Amazon EC2",
            provider=CloudProvider.AWS,
            service_category="compute",
            estimated_monthly_cost=Decimal("2000.00")
        )
        
        rds_service = ServiceRecommendation(
            service_name="Amazon RDS",
            provider=CloudProvider.AWS,
            service_category="database",
            estimated_monthly_cost=Decimal("800.00")
        )
        
        # Create recommendation
        recommendation = Recommendation(
            assessment_id="assessment123",
            agent_name="cloud_engineer",
            title="AWS Infrastructure Recommendation",
            summary="Recommended AWS services for scalable e-commerce platform",
            confidence_level=RecommendationConfidence.HIGH,
            confidence_score=0.85,
            recommendation_data={
                "architecture": "microservices",
                "deployment_strategy": "blue-green",
                "monitoring": "CloudWatch + custom metrics"
            },
            recommended_services=[ec2_service, rds_service],
            cost_estimates={
                "monthly_total": 2800.00,
                "yearly_projection": 33600.00,
                "cost_breakdown": {
                    "compute": 2000.00,
                    "database": 800.00
                }
            },
            implementation_steps=[
                "Set up VPC and security groups",
                "Launch EC2 instances with auto-scaling",
                "Configure RDS with Multi-AZ deployment",
                "Set up monitoring and alerting"
            ],
            prerequisites=[
                "AWS account with appropriate permissions",
                "Domain name and SSL certificates",
                "CI/CD pipeline setup"
            ],
            risks_and_considerations=[
                "Initial setup complexity",
                "Ongoing monitoring requirements",
                "Cost optimization needed as scale increases"
            ],
            category="infrastructure",
            priority=Priority.HIGH,
            business_impact="high"
        )
        
        # Verify recommendation
        assert recommendation.agent_name == "cloud_engineer"
        assert recommendation.confidence_level == RecommendationConfidence.HIGH
        assert recommendation.confidence_score == 0.85
        assert len(recommendation.recommended_services) == 2
        assert len(recommendation.implementation_steps) == 4
        assert recommendation.is_high_confidence
        
        # Test cost calculation
        total_cost = recommendation.calculate_total_cost()
        assert total_cost == Decimal("2800.00")
    
    def test_assessment_progress_tracking(self):
        """Test assessment progress tracking methods."""
        assessment = Assessment(
            user_id="user123",
            title="Test Assessment",
            business_requirements=BusinessRequirements(
                company_size=CompanySize.SMALL,
                industry=Industry.TECHNOLOGY,
                business_goals=[BusinessGoal(goal="Test goal")],
                growth_projection=GrowthProjection(current_users=1000),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.UNDER_10K
                ),
                team_structure=TeamStructure(
                    total_developers=3,
                    senior_developers=1,
                    devops_engineers=0,
                    data_engineers=0,
                    cloud_expertise_level=2
                ),
                project_timeline_months=6
            ),
            technical_requirements=TechnicalRequirements(
                workload_types=[WorkloadType.WEB_APPLICATION],
                performance_requirements=PerformanceRequirement(),
                scalability_requirements=ScalabilityRequirement(),
                security_requirements=SecurityRequirement(),
                integration_requirements=IntegrationRequirement()
            )
        )
        
        # Test initial state
        assert assessment.status == AssessmentStatus.DRAFT
        assert assessment.completion_percentage == 0.0
        assert not assessment.is_complete
        assert assessment.started_at is None
        
        # Update progress
        assessment.update_progress(25.0, "requirements_validation")
        assert assessment.completion_percentage == 25.0
        assert assessment.status == AssessmentStatus.IN_PROGRESS
        assert assessment.started_at is not None
        
        # Complete assessment
        assessment.update_progress(100.0, "completed")
        assert assessment.completion_percentage == 100.0
        assert assessment.status == AssessmentStatus.COMPLETED
        assert assessment.is_complete
        assert assessment.completed_at is not None
        
        # Test duration calculation
        duration = assessment.duration_minutes
        assert duration is not None
        assert duration >= 0
    
    def test_model_validation_errors(self):
        """Test that our models properly validate data."""
        # Test invalid confidence score vs level
        with pytest.raises(ValueError):
            Recommendation(
                assessment_id="test",
                agent_name="test_agent",
                title="Test",
                summary="Test summary",
                confidence_level=RecommendationConfidence.LOW,
                confidence_score=0.9,  # Too high for LOW confidence level
                category="test"
            )
    
    def test_model_string_representations(self):
        """Test string representations of models."""
        assessment = Assessment(
            user_id="user123",
            title="Test Assessment",
            business_requirements=BusinessRequirements(
                company_size=CompanySize.SMALL,
                industry=Industry.TECHNOLOGY,
                business_goals=[BusinessGoal(goal="Test goal")],
                growth_projection=GrowthProjection(current_users=1000),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.UNDER_10K
                ),
                team_structure=TeamStructure(
                    total_developers=3,
                    senior_developers=1,
                    devops_engineers=0,
                    data_engineers=0,
                    cloud_expertise_level=2
                ),
                project_timeline_months=6
            ),
            technical_requirements=TechnicalRequirements(
                workload_types=[WorkloadType.WEB_APPLICATION],
                performance_requirements=PerformanceRequirement(),
                scalability_requirements=ScalabilityRequirement(),
                security_requirements=SecurityRequirement(),
                integration_requirements=IntegrationRequirement()
            )
        )
        
        assessment_str = str(assessment)
        assert "Test Assessment" in assessment_str
        assert "draft" in assessment_str
        
        recommendation = Recommendation(
            assessment_id="test",
            agent_name="test_agent",
            title="Test Recommendation",
            summary="Test summary",
            confidence_level=RecommendationConfidence.MEDIUM,
            confidence_score=0.6,
            category="test"
        )
        
        rec_str = str(recommendation)
        assert "test_agent" in rec_str
        assert "medium" in rec_str