"""
Assessment schemas for Infra Mind.

Learning Note: Assessment schemas tie together business and technical
requirements and track the progress of AI agent analysis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field, field_validator

from .base import (
    BaseSchema, 
    TimestampMixin,
    AssessmentStatus,
    Priority
)
from .business import BusinessRequirements
from .technical import TechnicalRequirements


class AssessmentProgress(BaseSchema):
    """
    Progress tracking for assessment workflow.
    
    Learning Note: This helps users understand where their
    assessment is in the AI analysis pipeline.
    """
    current_step: str = Field(description="Current workflow step")
    completed_steps: List[str] = Field(
        default_factory=list,
        description="List of completed workflow steps"
    )
    total_steps: int = Field(description="Total number of steps in workflow")
    progress_percentage: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall progress percentage"
    )
    estimated_completion_minutes: Optional[int] = Field(
        default=None,
        description="Estimated minutes until completion"
    )
    
    # Error handling
    error: Optional[str] = Field(
        default=None,
        description="Error message if workflow failed"
    )
    
    # Agent-specific progress
    agent_progress: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Progress of individual agents"
    )


class AssessmentMetadata(BaseSchema):
    """
    Metadata about the assessment process.
    
    Learning Note: Metadata helps with debugging, analytics,
    and improving the assessment process.
    """
    source: str = Field(
        default="web_form",
        description="How the assessment was created (web_form, api, import)"
    )
    version: str = Field(
        default="1.0",
        description="Assessment schema version"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing assessments"
    )
    
    # Analytics data
    form_completion_time_minutes: Optional[int] = Field(
        default=None,
        description="Time taken to complete the assessment form"
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="User agent string (for web assessments)"
    )
    referrer: Optional[str] = Field(
        default=None,
        description="Referrer URL (for web assessments)"
    )


class Assessment(BaseSchema, TimestampMixin):
    """
    Complete infrastructure assessment.
    
    Learning Note: This is the main model that combines all
    requirements and tracks the assessment lifecycle.
    """
    model_config = {"extra": "allow"}
    # Basic information
    title: str = Field(description="Assessment title/name")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Assessment description"
    )
    
    # Requirements
    business_requirements: BusinessRequirements = Field(
        description="Business context and requirements"
    )
    technical_requirements: TechnicalRequirements = Field(
        description="Technical specifications and constraints"
    )
    business_goal: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Primary business goal or objective for the infrastructure assessment"
    )
    
    # Status and progress
    status: AssessmentStatus = Field(
        default=AssessmentStatus.DRAFT,
        description="Current assessment status"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Assessment priority level"
    )
    progress: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assessment progress tracking"
    )
    
    # Workflow state
    workflow_id: Optional[str] = Field(
        default=None,
        description="LangGraph workflow identifier"
    )
    agent_states: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Current state of each AI agent"
    )
    
    # Results
    recommendations_generated: bool = Field(
        default=False,
        description="Whether recommendations have been generated"
    )
    reports_generated: bool = Field(
        default=False,
        description="Whether reports have been generated"
    )
    
    # Metadata
    metadata: AssessmentMetadata = Field(
        default_factory=AssessmentMetadata,
        description="Assessment metadata and analytics"
    )
    
    # Timestamps for lifecycle tracking
    started_at: Optional[datetime] = Field(
        default=None,
        description="When agent analysis started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When assessment was completed"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Ensure title is meaningful."""
        if len(v.strip()) < 3:
            raise ValueError("Title must be at least 3 characters long")
        return v.strip()
    
    @property
    def is_complete(self) -> bool:
        """Check if assessment is complete."""
        return self.status == AssessmentStatus.COMPLETED
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate assessment duration in minutes."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None


# Request/Response models for API
class AssessmentCreate(BaseSchema):
    """Schema for creating a new assessment."""
    title: str = Field(description="Assessment title/name")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Assessment description"
    )
    business_requirements: BusinessRequirements
    technical_requirements: TechnicalRequirements
    priority: Priority = Field(default=Priority.MEDIUM)
    business_goal: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Primary business goal or objective for the infrastructure assessment"
    )
    
    # Optional metadata
    tags: List[str] = Field(default_factory=list)
    source: str = Field(default="web_form")


class AssessmentUpdate(BaseSchema):
    """Schema for updating an assessment."""
    title: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=1000)
    business_requirements: Optional[BusinessRequirements] = None
    technical_requirements: Optional[TechnicalRequirements] = None
    priority: Optional[Priority] = None
    status: Optional[AssessmentStatus] = None
    business_goal: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[List[str]] = None
    draft_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw form data for draft assessments")
    current_step: Optional[int] = Field(default=None, description="Current step in the assessment form")


class AssessmentSummary(BaseSchema):
    """Summary view of an assessment for list endpoints."""
    id: str
    title: str
    status: AssessmentStatus
    priority: Priority
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    
    # Key metrics
    company_name: str = Field(default="Unknown Company", description="Company name")
    company_size: str
    industry: str
    budget_range: str
    workload_types: List[str]
    
    # Status indicators
    recommendations_generated: bool
    reports_generated: bool


class AssessmentResponse(Assessment):
    """Complete assessment response with ID."""
    id: str = Field(description="Unique assessment identifier")


class AssessmentListResponse(BaseSchema):
    """Response for assessment list endpoints."""
    assessments: List[AssessmentSummary]
    total: int
    page: int
    limit: int
    pages: int


# Workflow-related schemas
class StartAssessmentRequest(BaseSchema):
    """Request to start AI agent analysis."""
    assessment_id: str
    priority_override: Optional[Priority] = None
    agent_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom configuration for agents"
    )


class AssessmentStatusUpdate(BaseSchema):
    """Status update for assessment progress."""
    assessment_id: str
    status: AssessmentStatus
    progress_percentage: float
    current_step: str
    message: Optional[str] = None
    agent_updates: Optional[Dict[str, Any]] = None