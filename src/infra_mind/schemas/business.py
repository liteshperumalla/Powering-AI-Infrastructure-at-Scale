"""
Business requirements schemas for Infra Mind.

Learning Note: These models capture the business context that drives
infrastructure recommendations. They're designed to be user-friendly
while providing rich data for AI agents.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import Field, field_validator, model_validator
from decimal import Decimal

from .base import (
    BaseSchema, 
    CompanySize, 
    Industry, 
    BudgetRange, 
    ComplianceRequirement,
    Priority
)


class BusinessGoal(BaseSchema):
    """
    Individual business goal with priority and timeline.
    
    Learning Note: Breaking down complex requirements into smaller,
    structured pieces makes them easier for AI agents to process.
    """
    goal: str = Field(description="Description of the business goal")
    priority: Priority = Field(description="Priority level of this goal")
    timeline_months: Optional[int] = Field(
        default=None, 
        ge=1, 
        le=60,
        description="Timeline to achieve this goal in months"
    )
    success_metrics: List[str] = Field(
        default_factory=list,
        description="How success will be measured"
    )


class GrowthProjection(BaseSchema):
    """
    Business growth projections for capacity planning.
    
    Learning Note: Infrastructure needs to scale with business growth.
    These projections help agents recommend scalable solutions.
    """
    current_users: int = Field(ge=0, description="Current number of users")
    projected_users_6m: Optional[int] = Field(
        default=None, 
        ge=0,
        description="Projected users in 6 months"
    )
    projected_users_12m: Optional[int] = Field(
        default=None, 
        ge=0,
        description="Projected users in 12 months"
    )
    projected_users_24m: Optional[int] = Field(
        default=None, 
        ge=0,
        description="Projected users in 24 months"
    )
    
    current_revenue: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Current annual revenue"
    )
    projected_revenue_12m: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Projected revenue in 12 months"
    )
    
    @field_validator('projected_users_6m', 'projected_users_12m', 'projected_users_24m')
    @classmethod
    def validate_user_growth(cls, v, info):
        """Ensure growth projections are realistic."""
        if v is not None and 'current_users' in info.data:
            current = info.data['current_users']
            if v < current:
                raise ValueError("Projected users cannot be less than current users")
            # Warn about unrealistic growth (more than 10x in any period)
            if v > current * 10:
                # In a real app, this might be a warning rather than an error
                pass
        return v


class BudgetConstraints(BaseSchema):
    """
    Budget constraints and preferences.
    
    Learning Note: Budget is often the primary constraint for infrastructure
    decisions. This model captures both hard limits and preferences.
    """
    total_budget_range: BudgetRange = Field(
        description="Overall budget range for infrastructure"
    )
    monthly_budget_limit: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Hard monthly spending limit"
    )
    
    # Budget allocation preferences (should sum to 100)
    compute_percentage: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of budget for compute resources"
    )
    storage_percentage: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of budget for storage"
    )
    networking_percentage: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of budget for networking"
    )
    security_percentage: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of budget for security tools"
    )
    
    cost_optimization_priority: Priority = Field(
        default=Priority.MEDIUM,
        description="How important is cost optimization"
    )
    
    @model_validator(mode='after')
    def validate_budget_allocation(self):
        """Ensure budget percentages don't exceed 100%."""
        percentages = [
            self.compute_percentage,
            self.storage_percentage,
            self.networking_percentage,
            self.security_percentage
        ]
        
        # Filter out None values
        valid_percentages = [p for p in percentages if p is not None]
        
        if valid_percentages and sum(valid_percentages) > 100:
            raise ValueError("Budget allocation percentages cannot exceed 100%")
        
        return self


class TeamStructure(BaseSchema):
    """
    Team structure and technical capabilities.
    
    Learning Note: The team's technical expertise affects what
    infrastructure solutions are appropriate.
    """
    total_developers: int = Field(ge=1, description="Total number of developers")
    senior_developers: int = Field(ge=0, description="Number of senior developers")
    devops_engineers: int = Field(ge=0, description="Number of DevOps engineers")
    data_engineers: int = Field(ge=0, description="Number of data engineers")
    
    # Technical expertise levels (1-5 scale)
    cloud_expertise_level: int = Field(
        ge=1, 
        le=5,
        description="Team's cloud expertise (1=beginner, 5=expert)"
    )
    kubernetes_expertise: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Kubernetes expertise level"
    )
    database_expertise: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Database management expertise"
    )
    
    preferred_technologies: List[str] = Field(
        default_factory=list,
        description="Technologies the team prefers to work with"
    )
    
    @field_validator('senior_developers')
    @classmethod
    def validate_senior_count(cls, v, info):
        """Ensure senior developers don't exceed total developers."""
        if 'total_developers' in info.data and v > info.data['total_developers']:
            raise ValueError("Senior developers cannot exceed total developers")
        return v


class BusinessRequirements(BaseSchema):
    """
    Complete business requirements for infrastructure assessment.
    
    Learning Note: This is the main model that captures all business
    context. It's designed to be filled out through a user-friendly
    form but provide rich data for AI analysis.
    """
    
    # Company Information (Enhanced)
    company_name: str = Field(description="Company name")
    company_size: CompanySize = Field(description="Size of the company")
    industry: Industry = Field(description="Primary industry")
    industry_other: Optional[str] = Field(default=None, description="Custom industry if 'other' selected")
    
    # Geographic and Market Context
    geographic_regions: List[str] = Field(
        default_factory=list,
        description="Geographic regions where company operates"
    )
    customer_base_size: Optional[str] = Field(
        default=None,
        description="Size of customer base (small, medium, large, enterprise)"
    )
    revenue_model: Optional[str] = Field(
        default=None,
        description="Primary revenue model (subscription, transaction, etc.)"
    )
    growth_stage: Optional[str] = Field(
        default=None,
        description="Company growth stage (pre-seed, seed, series-a, etc.)"
    )
    key_competitors: Optional[str] = Field(
        default=None,
        description="Key competitors in the market"
    )
    mission_critical_systems: List[str] = Field(
        default_factory=list,
        description="Systems that are mission-critical for business operations"
    )
    
    # Business Context
    business_goals: List[BusinessGoal] = Field(
        description="Primary business goals driving infrastructure needs"
    )
    growth_projection: GrowthProjection = Field(
        description="Expected business growth"
    )
    
    # Budget and Constraints
    budget_constraints: BudgetConstraints = Field(
        description="Budget limitations and preferences"
    )
    
    # Team and Capabilities
    team_structure: Union[str, TeamStructure] = Field(
        description="Team size and technical capabilities"
    )
    
    # Compliance and Regulatory
    compliance_requirements: List[ComplianceRequirement] = Field(
        default_factory=list,
        description="Required regulatory compliance"
    )
    data_residency_requirements: List[str] = Field(
        default_factory=list,
        description="Countries/regions where data must be stored"
    )
    
    # Timeline and Urgency
    project_timeline_months: int = Field(
        ge=1,
        le=36,
        description="Timeline for infrastructure implementation"
    )
    urgency_level: Priority = Field(
        default=Priority.MEDIUM,
        description="How urgent is this infrastructure project"
    )
    
    # Additional Context
    current_pain_points: List[str] = Field(
        default_factory=list,
        description="Current infrastructure problems to solve"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="How will success be measured"
    )
    
    # Flexibility and Preferences
    cloud_provider_preference: Optional[str] = Field(
        default=None,
        description="Preferred cloud provider (if any)"
    )
    multi_cloud_acceptable: bool = Field(
        default=True,
        description="Is a multi-cloud solution acceptable"
    )
    
    additional_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Any additional context or requirements"
    )

    @field_validator('team_structure')
    @classmethod
    def convert_legacy_team_structure_main(cls, v):
        """Convert legacy string team_structure to TeamStructure object."""
        if isinstance(v, str):
            # Convert legacy string values to TeamStructure object
            size_mapping = {
                'small': {'total_developers': 3, 'senior_developers': 1, 'devops_engineers': 0, 'data_engineers': 0},
                'medium': {'total_developers': 8, 'senior_developers': 3, 'devops_engineers': 1, 'data_engineers': 1},
                'large': {'total_developers': 20, 'senior_developers': 8, 'devops_engineers': 3, 'data_engineers': 2},
                'startup': {'total_developers': 5, 'senior_developers': 2, 'devops_engineers': 1, 'data_engineers': 1}
            }

            base_values = size_mapping.get(v, size_mapping['medium'])
            return TeamStructure(
                cloud_expertise_level=3,
                kubernetes_expertise=2,
                database_expertise=3,
                **base_values
            )
        return v
    
    @field_validator('business_goals')
    @classmethod
    def validate_business_goals(cls, v):
        """Ensure at least one business goal is provided."""
        if not v:
            raise ValueError("At least one business goal is required")
        return v
    
    @model_validator(mode='after')
    def validate_timeline_consistency(self):
        """Ensure timeline is consistent with urgency."""
        if self.urgency_level == Priority.CRITICAL and self.project_timeline_months > 6:
            raise ValueError("Critical projects should have timeline <= 6 months")
        return self


# Request/Response models for API
class BusinessRequirementsCreate(BusinessRequirements):
    """Schema for creating business requirements."""
    pass


class BusinessRequirementsUpdate(BaseSchema):
    """Schema for updating business requirements (all fields optional)."""
    company_size: Optional[CompanySize] = None
    industry: Optional[Industry] = None
    business_goals: Optional[List[BusinessGoal]] = None
    growth_projection: Optional[GrowthProjection] = None
    budget_constraints: Optional[BudgetConstraints] = None
    team_structure: Optional[Union[str, TeamStructure]] = None
    compliance_requirements: Optional[List[ComplianceRequirement]] = None
    data_residency_requirements: Optional[List[str]] = None
    project_timeline_months: Optional[int] = Field(default=None, ge=1, le=36)
    urgency_level: Optional[Priority] = None
    current_pain_points: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    cloud_provider_preference: Optional[str] = None
    multi_cloud_acceptable: Optional[bool] = None
    additional_notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('team_structure')
    @classmethod
    def convert_legacy_team_structure(cls, v):
        """Convert legacy string team_structure to TeamStructure object."""
        if isinstance(v, str):
            # Convert legacy string values to TeamStructure object
            size_mapping = {
                'small': {'total_developers': 3, 'senior_developers': 1, 'devops_engineers': 0, 'data_engineers': 0},
                'medium': {'total_developers': 8, 'senior_developers': 3, 'devops_engineers': 1, 'data_engineers': 1},
                'large': {'total_developers': 20, 'senior_developers': 8, 'devops_engineers': 3, 'data_engineers': 2},
                'startup': {'total_developers': 5, 'senior_developers': 2, 'devops_engineers': 1, 'data_engineers': 1}
            }

            base_values = size_mapping.get(v, size_mapping['medium'])
            return TeamStructure(
                cloud_expertise_level=3,
                kubernetes_expertise=2,
                database_expertise=3,
                **base_values
            )
        return v


class BusinessRequirementsResponse(BusinessRequirements):
    """Schema for business requirements API responses."""
    id: str = Field(description="Unique identifier")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")