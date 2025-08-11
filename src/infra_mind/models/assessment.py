"""
Assessment model for Infra Mind.

Defines the infrastructure assessment document structure using our Pydantic schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from beanie import Document, Indexed
from pydantic import Field

# Schemas will be used later for validation when form collection is implemented
from ..schemas.base import AssessmentStatus, Priority


class Assessment(Document):
    """
    Infrastructure assessment document model.
    
    Learning Note: This model now uses our structured Pydantic schemas
    instead of generic Dict fields, providing better validation and type safety.
    """
    
    # User and identification
    user_id: str = Indexed()
    title: str = Field(description="Assessment title/name")
    description: Optional[str] = Field(default=None, description="Assessment description")
    
    # Requirements stored as flexible dictionaries for now
    # TODO: Convert to structured schemas once form collection is implemented
    business_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Business requirements and context"
    )
    technical_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Technical requirements and constraints"
    )
    business_goal: Optional[str] = Field(
        default=None,
        description="Primary business goal or objective for the infrastructure assessment"
    )
    
    # Assessment state
    status: AssessmentStatus = Field(
        default=AssessmentStatus.DRAFT,
        description="Current assessment status"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Assessment priority level"
    )
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Assessment completion percentage (0-100)"
    )
    
    # Agent workflow state
    workflow_id: Optional[str] = Field(
        default=None,
        description="LangGraph workflow identifier"
    )
    agent_states: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current state of each agent in the workflow"
    )
    workflow_progress: Dict[str, Any] = Field(
        default_factory=dict,
        description="Overall workflow progress and step tracking"
    )
    progress: Dict[str, Any] = Field(
        default_factory=lambda: {"current_step": "created", "completed_steps": [], "total_steps": 5, "progress_percentage": 0.0},
        description="Current progress state"
    )
    
    # Results tracking
    recommendations_generated: bool = Field(
        default=False,
        description="Whether recommendations have been generated"
    )
    reports_generated: bool = Field(
        default=False,
        description="Whether reports have been generated"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assessment metadata including source, version, tags"
    )
    tags: list[str] = Field(
        default_factory=list, 
        description="Assessment tags for organization"
    )
    source: str = Field(
        default="web_form",
        description="How the assessment was created"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(
        default=None,
        description="When agent analysis started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When assessment was completed"
    )
    
    class Settings:
        """Beanie document settings."""
        name = "assessments"
        use_revision = False  # Disable revision tracking to avoid RevisionIdWasChanged errors
    
    def __str__(self) -> str:
        """String representation of the assessment."""
        return f"Assessment(title={self.title}, status={self.status.value})"
    
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
    
    def update_progress(self, percentage: float, current_step: str) -> None:
        """Update assessment progress."""
        self.completion_percentage = max(0.0, min(100.0, percentage))
        self.workflow_progress["current_step"] = current_step
        self.updated_at = datetime.utcnow()
        
        # Auto-update status based on progress
        if percentage >= 100.0:
            self.status = AssessmentStatus.COMPLETED
            self.completed_at = datetime.utcnow()
        elif percentage > 0.0:
            self.status = AssessmentStatus.IN_PROGRESS
            if not self.started_at:
                self.started_at = datetime.utcnow()