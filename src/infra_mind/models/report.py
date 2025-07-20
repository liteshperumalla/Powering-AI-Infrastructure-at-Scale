"""
Report model for Infra Mind.

Defines generated report document structure and metadata.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, field_validator

from ..schemas.base import Priority


class ReportType(str, Enum):
    """Types of reports that can be generated."""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_ROADMAP = "technical_roadmap"
    COST_ANALYSIS = "cost_analysis"
    COMPLIANCE_REPORT = "compliance_report"
    ARCHITECTURE_OVERVIEW = "architecture_overview"
    FULL_ASSESSMENT = "full_assessment"


class ReportFormat(str, Enum):
    """Available report formats."""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"


class ReportStatus(str, Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportSection(Document):
    """
    Individual report section model.
    
    Learning Note: Separating sections allows for modular report generation
    and easier customization of report content.
    """
    
    # Section identification
    report_id: str = Indexed()
    section_id: str = Field(description="Unique section identifier")
    title: str = Field(description="Section title")
    order: int = Field(description="Section order in the report")
    
    # Content
    content: str = Field(description="Section content (HTML/Markdown)")
    content_type: str = Field(default="markdown", description="Content format")
    
    # Metadata
    generated_by: str = Field(description="Agent or system that generated this section")
    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used for this section"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "report_sections"
        indexes = [
            [("report_id", 1), ("order", 1)],  # Query sections by report and order
        ]


class Report(Document):
    """
    Generated report document model.
    
    Learning Note: This model tracks report generation, stores metadata,
    and provides access to generated report files.
    """
    
    # Report identification
    assessment_id: str = Indexed()
    user_id: str = Indexed()
    title: str = Field(description="Report title")
    description: Optional[str] = Field(default=None, description="Report description")
    
    # Report configuration
    report_type: ReportType = Field(description="Type of report")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Report format")
    template_version: str = Field(default="1.0", description="Template version used")
    
    # Generation metadata
    status: ReportStatus = Field(default=ReportStatus.PENDING, description="Generation status")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Generation progress")
    
    # Content metadata
    sections: List[str] = Field(
        default_factory=list,
        description="List of section IDs included in this report"
    )
    total_pages: Optional[int] = Field(default=None, description="Total number of pages")
    word_count: Optional[int] = Field(default=None, description="Approximate word count")
    
    # File information
    file_path: Optional[str] = Field(default=None, description="Path to generated report file")
    file_size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    file_hash: Optional[str] = Field(default=None, description="File hash for integrity")
    
    # Generation details
    generated_by: List[str] = Field(
        default_factory=list,
        description="List of agents that contributed to this report"
    )
    generation_time_seconds: Optional[float] = Field(
        default=None,
        description="Time taken to generate the report"
    )
    
    # Quality metrics
    completeness_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="How complete the report is (0-1)"
    )
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Overall confidence in report recommendations (0-1)"
    )
    
    # Business context
    priority: Priority = Field(default=Priority.MEDIUM, description="Report priority")
    tags: List[str] = Field(default_factory=list, description="Report tags")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    retry_count: int = Field(default=0, description="Number of generation retries")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, description="When generation completed")
    
    class Settings:
        """Beanie document settings."""
        name = "reports"
        indexes = [
            [("assessment_id", 1)],  # Query reports by assessment
            [("user_id", 1), ("status", 1)],  # Query user reports by status
            [("report_type", 1)],  # Query by report type
            [("created_at", -1)],  # Sort by creation date
            [("status", 1), ("priority", 1)],  # Query by status and priority
        ]
    
    @field_validator('progress_percentage')
    @classmethod
    def validate_progress(cls, v):
        """Ensure progress is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v
    
    def mark_as_generating(self) -> None:
        """Mark report as currently being generated."""
        self.status = ReportStatus.GENERATING
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self, file_path: str, file_size: int) -> None:
        """Mark report as completed with file information."""
        self.status = ReportStatus.COMPLETED
        self.progress_percentage = 100.0
        self.file_path = file_path
        self.file_size_bytes = file_size
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark report generation as failed."""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, percentage: float) -> None:
        """Update generation progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        self.updated_at = datetime.utcnow()
    
    @property
    def is_completed(self) -> bool:
        """Check if report generation is completed."""
        return self.status == ReportStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if report generation failed."""
        return self.status == ReportStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """Check if report generation can be retried."""
        return self.is_failed and self.retry_count < 3
    
    def __str__(self) -> str:
        """String representation of the report."""
        return f"Report(type={self.report_type.value}, status={self.status.value})"