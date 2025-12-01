"""
Test Pydantic schemas for Infra Mind.

Learning Note: These tests verify that our data models work correctly
with validation, serialization, and business logic.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from src.infra_mind.schemas.base import (
    CompanySize, Industry, BudgetRange, ComplianceRequirement,
    PaginationParams, PaginatedResponse
)
from src.infra_mind.schemas.business import (
    BusinessGoal, GrowthProjection, BudgetConstraints,
    TeamStructure, BusinessRequirements
)
from src.infra_mind.schemas.technical import (
    PerformanceRequirement, ScalabilityRequirement,
    SecurityRequirement, IntegrationRequirement,
    TechnicalRequirements, WorkloadType, DatabaseType
)
from src.infra_mind.schemas.assessment import (
    Assessment, AssessmentCreate, AssessmentProgress
)


class TestBusinessSchemas:
    """Test business requirement schemas."""
    
    def test_business_goal_creation(self):
        """Test creating a business goal with validation."""
        goal = BusinessGoal(
            goal="Increase user engagement by 50%",
            priority="high",
            timeline_months=6,
            success_metrics=["User retention rate", "Daily active users"]
        )
        
        assert goal.goal == "Increase user engagement by 50%"
        assert goal.priority == "high"
        assert goal.timeline_months == 6
        assert len(goal.success_metrics) == 2
    
    def test_business_goal_validation(self):
        """Test business goal validation rules."""
        # Timeline too long should fail
        with pytest.raises(ValidationError):
            BusinessGoal(
                goal="Long term goal",
                timeline_months=61  # Over 60 months limit
            )
        
        # Timeline too short should fail
        with pytest.raises(ValidationError):
            BusinessGoal(
                goal="Immediate goal",
                timeline_months=0  # Under 1 month minimum
            )
    
    def test_growth_projection_validation(self):
        """Test growth projection validation logic."""
        # Valid growth projection
        growth = GrowthProjection(
            current_users=1000,
            projected_users_6m=1500,
            projected_users_12m=2000,
            current_revenue=Decimal("100000"),
            projected_revenue_12m=Decimal("150000")
        )
        
        assert growth.current_users == 1000
        assert growth.projected_users_12m == 2000
    
    def test_growth_projection_invalid_decrease(self):
        """Test that projected users cannot decrease."""
        with pytest.raises(ValidationError):
            GrowthProjection(
                current_users=1000,
                projected_users_6m=800  # Less than current
            )
    
    def test_budget_constraints_validation(self):
        """Test budget allocation validation."""
        # Valid budget allocation
        budget = BudgetConstraints(
            total_budget_range=BudgetRange.RANGE_100K_500K,
            compute_percentage=40,
            storage_percentage=20,
            networking_percentage=15,
            security_percentage=10
            # Total: 85% (under 100%)
        )
        
        assert budget.total_budget_range == "100k_500k"
    
    def test_budget_constraints_over_allocation(self):
        """Test budget over-allocation validation."""
        with pytest.raises(ValidationError):
            BudgetConstraints(
                total_budget_range=BudgetRange.RANGE_100K_500K,
                compute_percentage=50,
                storage_percentage=30,
                networking_percentage=30,
                security_percentage=20
                # Total: 130% (over 100%)
            )
    
    def test_team_structure_validation(self):
        """Test team structure validation."""
        # Valid team structure
        team = TeamStructure(
            total_developers=10,
            senior_developers=3,
            devops_engineers=2,
            data_engineers=1,
            cloud_expertise_level=3
        )
        
        assert team.total_developers == 10
        assert team.senior_developers == 3
    
    def test_team_structure_invalid_senior_count(self):
        """Test senior developers cannot exceed total."""
        with pytest.raises(ValidationError):
            TeamStructure(
                total_developers=5,
                senior_developers=8,  # More than total
                cloud_expertise_level=3
            )
    
    def test_complete_business_requirements(self):
        """Test creating complete business requirements."""
        business_req = BusinessRequirements(
            company_name="Test Company",
            company_size=CompanySize.MEDIUM,
            industry=Industry.TECHNOLOGY,
            business_goals=[
                BusinessGoal(
                    goal="Scale to 1M users",
                    priority="high",
                    timeline_months=12
                )
            ],
            growth_projection=GrowthProjection(
                current_users=10000,
                projected_users_12m=100000
            ),
            budget_constraints=BudgetConstraints(
                total_budget_range=BudgetRange.RANGE_100K_500K
            ),
            team_structure=TeamStructure(
                total_developers=8,
                senior_developers=2,
                devops_engineers=1,
                data_engineers=0,
                cloud_expertise_level=3
            ),
            project_timeline_months=12
        )
        
        assert business_req.company_size == "medium"
        assert business_req.industry == "technology"
        assert len(business_req.business_goals) == 1
    
    def test_business_requirements_validation(self):
        """Test business requirements validation rules."""
        # Missing business goals should fail
        with pytest.raises(ValidationError):
            BusinessRequirements(
                company_name="Test Company",
                company_size=CompanySize.MEDIUM,
                industry=Industry.TECHNOLOGY,
                business_goals=[],  # Empty list
                growth_projection=GrowthProjection(current_users=1000),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.RANGE_100K_500K
                ),
                team_structure=TeamStructure(
                    total_developers=5,
                    cloud_expertise_level=3
                ),
                project_timeline_months=12
            )


class TestTechnicalSchemas:
    """Test technical requirement schemas."""
    
    def test_performance_requirements(self):
        """Test performance requirements validation."""
        perf = PerformanceRequirement(
            api_response_time_ms=200,
            requests_per_second=1000,
            uptime_percentage=Decimal("99.9"),
            concurrent_users=5000
        )
        
        assert perf.api_response_time_ms == 200
        assert perf.uptime_percentage == Decimal("99.9")
    
    def test_performance_requirements_validation(self):
        """Test performance requirements validation rules."""
        # Invalid response time (too high)
        with pytest.raises(ValidationError):
            PerformanceRequirement(
                api_response_time_ms=15000  # Over 10 second limit
            )
        
        # Invalid uptime (too low)
        with pytest.raises(ValidationError):
            PerformanceRequirement(
                uptime_percentage=Decimal("85.0")  # Under 90% minimum
            )
    
    def test_scalability_requirements(self):
        """Test scalability requirements."""
        scalability = ScalabilityRequirement(
            current_data_size_gb=100,
            auto_scaling_required=True,
            global_distribution_required=True,
            planned_regions=["us-east-1", "eu-west-1", "ap-southeast-1"]
        )
        
        assert scalability.auto_scaling_required is True
        assert len(scalability.planned_regions) == 3
    
    def test_security_requirements(self):
        """Test security requirements."""
        security = SecurityRequirement(
            encryption_at_rest_required=True,
            multi_factor_auth_required=True,
            vpc_isolation_required=True,
            audit_logging_required=True
        )
        
        assert security.encryption_at_rest_required is True
        assert security.multi_factor_auth_required is True
    
    def test_integration_requirements(self):
        """Test integration requirements."""
        integration = IntegrationRequirement(
            existing_databases=["PostgreSQL", "Redis"],
            rest_api_required=True,
            real_time_sync_required=False
        )
        
        assert len(integration.existing_databases) == 2
        assert integration.rest_api_required is True
    
    def test_complete_technical_requirements(self):
        """Test creating complete technical requirements."""
        tech_req = TechnicalRequirements(
            workload_types=[WorkloadType.WEB_APPLICATION, WorkloadType.API_SERVICE],
            database_preferences=[DatabaseType.RELATIONAL, DatabaseType.KEY_VALUE],
            performance_requirements=PerformanceRequirement(
                api_response_time_ms=500,
                uptime_percentage=Decimal("99.5")
            ),
            scalability_requirements=ScalabilityRequirement(
                auto_scaling_required=True,
                planned_regions=["us-east-1", "eu-west-1"]
            ),
            security_requirements=SecurityRequirement(),
            integration_requirements=IntegrationRequirement()
        )
        
        assert len(tech_req.workload_types) == 2
        assert len(tech_req.database_preferences) == 2
    
    def test_technical_requirements_validation(self):
        """Test technical requirements validation rules."""
        # Missing workload types should fail
        with pytest.raises(ValidationError):
            TechnicalRequirements(
                workload_types=[],  # Empty list
                performance_requirements=PerformanceRequirement(),
                scalability_requirements=ScalabilityRequirement(),
                security_requirements=SecurityRequirement(),
                integration_requirements=IntegrationRequirement()
            )
    
    def test_global_distribution_validation(self):
        """Test global distribution requires multiple regions."""
        with pytest.raises(ValidationError):
            TechnicalRequirements(
                workload_types=[WorkloadType.WEB_APPLICATION],
                performance_requirements=PerformanceRequirement(),
                scalability_requirements=ScalabilityRequirement(
                    global_distribution_required=True,
                    planned_regions=["us-east-1"]  # Only one region
                ),
                security_requirements=SecurityRequirement(),
                integration_requirements=IntegrationRequirement()
            )


class TestAssessmentSchemas:
    """Test assessment schemas."""
    
    def test_assessment_progress(self):
        """Test assessment progress tracking."""
        progress = AssessmentProgress(
            current_step="agent_analysis",
            completed_steps=["input_validation", "requirements_processing"],
            total_steps=5,
            progress_percentage=40.0
        )
        
        assert progress.current_step == "agent_analysis"
        assert progress.progress_percentage == 40.0
        assert len(progress.completed_steps) == 2
    
    def test_assessment_create(self):
        """Test creating an assessment."""
        assessment_data = AssessmentCreate(
            title="E-commerce Platform Assessment",
            description="Infrastructure assessment for scaling e-commerce platform",
            business_requirements=BusinessRequirements(
                company_name="Test Company",
                company_size=CompanySize.MEDIUM,
                industry=Industry.RETAIL,
                business_goals=[
                    BusinessGoal(
                        goal="Handle Black Friday traffic",
                        priority="critical",
                        timeline_months=3
                    )
                ],
                growth_projection=GrowthProjection(current_users=50000),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.RANGE_100K_500K
                ),
                team_structure=TeamStructure(
                    total_developers=12,
                    senior_developers=4,
                    devops_engineers=2,
                    data_engineers=1,
                    cloud_expertise_level=3
                ),
                project_timeline_months=6
            ),
            technical_requirements=TechnicalRequirements(
                workload_types=[WorkloadType.WEB_APPLICATION, WorkloadType.DATABASE],
                performance_requirements=PerformanceRequirement(
                    requests_per_second=10000,
                    uptime_percentage=Decimal("99.9")
                ),
                scalability_requirements=ScalabilityRequirement(
                    auto_scaling_required=True,
                    peak_load_multiplier=Decimal("10.0")
                ),
                security_requirements=SecurityRequirement(
                    encryption_at_rest_required=True,
                    ddos_protection_required=True
                ),
                integration_requirements=IntegrationRequirement(
                    payment_processors=["Stripe", "PayPal"]
                )
            )
        )
        
        assert assessment_data.title == "E-commerce Platform Assessment"
        assert assessment_data.business_requirements.industry == "retail"
        assert len(assessment_data.technical_requirements.workload_types) == 2
    
    def test_assessment_validation(self):
        """Test assessment validation rules."""
        # Title too short should fail
        with pytest.raises(ValidationError):
            AssessmentCreate(
                title="Hi",  # Too short
                business_requirements=BusinessRequirements(
                    company_name="Test Company",
                    company_size=CompanySize.SMALL,
                    industry=Industry.TECHNOLOGY,
                    business_goals=[BusinessGoal(goal="Test goal")],
                    growth_projection=GrowthProjection(current_users=100),
                    budget_constraints=BudgetConstraints(
                        total_budget_range=BudgetRange.UNDER_10K
                    ),
                    team_structure=TeamStructure(
                        total_developers=2,
                        senior_developers=0,
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


class TestBaseSchemas:
    """Test base schemas and utilities."""
    
    def test_pagination_params(self):
        """Test pagination parameter validation."""
        pagination = PaginationParams(page=2, limit=50)
        
        assert pagination.page == 2
        assert pagination.limit == 50
        assert pagination.skip == 50  # (2-1) * 50
    
    def test_pagination_validation(self):
        """Test pagination validation rules."""
        # Page must be >= 1
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
        
        # Limit must be <= 100
        with pytest.raises(ValidationError):
            PaginationParams(limit=150)
    
    def test_paginated_response(self):
        """Test paginated response creation."""
        items = ["item1", "item2", "item3"]
        pagination = PaginationParams(page=1, limit=10)
        
        response = PaginatedResponse.create(
            items=items,
            total=23,
            pagination=pagination
        )
        
        assert len(response.items) == 3
        assert response.total == 23
        assert response.page == 1
        assert response.pages == 3  # ceil(23/10)
    
    def test_enum_validation(self):
        """Test enum validation."""
        # Valid enum values
        assert CompanySize.MEDIUM == "medium"
        assert Industry.TECHNOLOGY == "technology"
        assert BudgetRange.RANGE_100K_500K == "100k_500k"
        
        # Invalid enum values should fail validation
        with pytest.raises(ValidationError):
            BusinessRequirements(
                company_name="Test Company",
                company_size="invalid_size",  # Not a valid CompanySize
                industry=Industry.TECHNOLOGY,
                business_goals=[BusinessGoal(goal="Test")],
                growth_projection=GrowthProjection(current_users=100),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.UNDER_10K
                ),
                team_structure=TeamStructure(
                    total_developers=2,
                    senior_developers=0,
                    devops_engineers=0,
                    data_engineers=0,
                    cloud_expertise_level=2
                ),
                project_timeline_months=6
            )
