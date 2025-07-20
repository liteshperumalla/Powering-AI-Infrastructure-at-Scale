"""
Recommendation model for Infra Mind.

Defines the AI agent recommendation document structure with enhanced validation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from beanie import Document, Indexed
from pydantic import Field, field_validator

from ..schemas.base import Priority, RecommendationConfidence, CloudProvider


class ServiceRecommendation(Document):
    """
    Individual cloud service recommendation.
    
    Learning Note: Breaking service recommendations into a separate model
    allows for better querying and analysis of recommended services.
    """
    service_name: str = Field(description="Name of the cloud service")
    provider: CloudProvider = Field(description="Cloud provider (AWS, Azure, GCP)")
    service_category: str = Field(description="Category (compute, storage, database, etc.)")
    
    # Cost information
    estimated_monthly_cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Estimated monthly cost in USD"
    )
    cost_model: Optional[str] = Field(
        default=None,
        description="Pricing model (pay-as-you-go, reserved, spot, etc.)"
    )
    
    # Service details
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Recommended service configuration"
    )
    
    # Justification
    reasons: List[str] = Field(
        default_factory=list,
        description="Why this service was recommended"
    )
    alternatives: List[str] = Field(
        default_factory=list,
        description="Alternative services considered"
    )
    
    # Implementation
    setup_complexity: str = Field(
        default="medium",
        description="Setup complexity: low, medium, high"
    )
    implementation_time_hours: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated implementation time in hours"
    )
    
    class Settings:
        name = "service_recommendations"
        indexes = [
            [("provider", 1), ("service_category", 1)],
            [("estimated_monthly_cost", 1)],
        ]


class Recommendation(Document):
    """
    AI agent recommendation document model.
    
    Learning Note: Enhanced model with structured data and better validation
    for more reliable agent recommendations.
    """
    
    # Assessment and agent identification
    assessment_id: str = Indexed()
    agent_name: str = Indexed()  # cto, cloud_engineer, research, etc.
    agent_version: str = Field(default="1.0", description="Agent version for tracking changes")
    
    # Recommendation metadata
    title: str = Field(description="Brief title of the recommendation")
    summary: str = Field(
        max_length=500,
        description="Executive summary of the recommendation"
    )
    
    # Quality and confidence metrics
    confidence_level: RecommendationConfidence = Field(
        description="Agent's confidence level in this recommendation"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Numerical confidence score (0-1)"
    )
    
    # Structured recommendation data
    recommendation_data: Dict[str, Any] = Field(
        description="Detailed recommendation content from the agent"
    )
    
    # Service recommendations
    recommended_services: List[ServiceRecommendation] = Field(
        default_factory=list,
        description="Specific cloud services recommended"
    )
    
    # Cost analysis
    cost_estimates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cost estimates and financial projections"
    )
    total_estimated_monthly_cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Total estimated monthly cost for all recommendations"
    )
    
    # Implementation guidance
    implementation_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step implementation guidance"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites before implementation"
    )
    risks_and_considerations: List[str] = Field(
        default_factory=list,
        description="Potential risks and important considerations"
    )
    
    # Validation and quality assurance
    validation_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from recommendation validation checks"
    )
    peer_review_score: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Score from other agents reviewing this recommendation"
    )
    
    # Business alignment
    business_impact: str = Field(
        default="medium",
        description="Expected business impact: low, medium, high"
    )
    alignment_score: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="How well this aligns with business requirements"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Recommendation tags")
    priority: Priority = Field(default=Priority.MEDIUM, description="Recommendation priority")
    category: str = Field(description="Recommendation category (architecture, security, cost, etc.)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_consistency(cls, v, info):
        """Ensure confidence score matches confidence level."""
        if 'confidence_level' in info.data:
            level = info.data['confidence_level']
            if level == RecommendationConfidence.LOW and v > 0.4:
                raise ValueError("Low confidence level should have score <= 0.4")
            elif level == RecommendationConfidence.HIGH and v < 0.7:
                raise ValueError("High confidence level should have score >= 0.7")
        return v
    
    class Settings:
        """Beanie document settings."""
        name = "recommendations"
        indexes = [
            [("assessment_id", 1), ("agent_name", 1)],  # Query by assessment and agent
            [("confidence_score", -1)],  # Sort by confidence
            [("created_at", -1)],  # Sort by creation date
            [("category", 1), ("priority", 1)],  # Query by category and priority
            [("business_impact", 1)],  # Query by business impact
            [("total_estimated_monthly_cost", 1)],  # Query by cost
        ]
    
    def __str__(self) -> str:
        """String representation of the recommendation."""
        return f"Recommendation(agent={self.agent_name}, confidence={self.confidence_level.value})"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence recommendation."""
        return self.confidence_level in [RecommendationConfidence.HIGH, RecommendationConfidence.VERY_HIGH]
    
    def calculate_total_cost(self) -> Decimal:
        """Calculate total monthly cost from all service recommendations."""
        total = Decimal('0')
        for service in self.recommended_services:
            if service.estimated_monthly_cost:
                total += service.estimated_monthly_cost
        return total
    
    def update_cost_estimate(self) -> None:
        """Update the total cost estimate based on service recommendations."""
        self.total_estimated_monthly_cost = self.calculate_total_cost()
        self.updated_at = datetime.utcnow()