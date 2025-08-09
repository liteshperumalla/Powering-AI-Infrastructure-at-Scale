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


class ReportTemplate(Document):
    """
    Report template model for customizable report generation.
    
    Learning Note: Templates allow organizations to standardize their
    report formats and branding across all generated reports.
    """
    
    # Template identification
    name: str = Field(description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    version: str = Field(default="1.0", description="Template version")
    
    # Template configuration
    report_type: ReportType = Field(description="Type of report this template generates")
    sections_config: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Configuration for report sections"
    )
    
    # Branding and styling
    branding_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default branding configuration"
    )
    css_template: Optional[str] = Field(default=None, description="CSS template for styling")
    html_template: Optional[str] = Field(default=None, description="HTML template structure")
    
    # Access control
    created_by: str = Field(description="User ID who created the template")
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    organization_id: Optional[str] = Field(default=None, description="Organization that owns this template")
    
    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times template has been used")
    last_used: Optional[datetime] = Field(default=None, description="When template was last used")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "report_templates"
        indexes = [
            [("report_type", 1)],  # Query templates by report type
            [("created_by", 1)],  # Query templates by creator
            [("organization_id", 1)],  # Query templates by organization
            [("is_public", 1)],  # Query public templates
            [("usage_count", -1)],  # Sort by popularity
        ]
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def can_user_access(self, user_id: str, organization_id: Optional[str] = None) -> bool:
        """Check if user can access this template."""
        if self.created_by == user_id:
            return True
        if self.is_public:
            return True
        if self.organization_id and self.organization_id == organization_id:
            return True
        return False


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
    
    # Interactive features
    is_interactive: bool = Field(default=False, description="Whether section supports drill-down")
    drill_down_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data for interactive drill-down features"
    )
    charts_config: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Configuration for interactive charts"
    )
    
    # Metadata
    generated_by: str = Field(description="Agent or system that generated this section")
    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used for this section"
    )
    
    # Versioning
    version: str = Field(default="1.0", description="Section version")
    parent_section_id: Optional[str] = Field(default=None, description="Parent section for versioning")
    
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
    report_id: str = Field(default_factory=lambda: f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000:04d}", description="Unique report identifier")
    assessment_id: str = Indexed()
    user_id: str = Indexed()
    title: str = Field(description="Report title")
    description: Optional[str] = Field(default=None, description="Report description")
    
    # Versioning and collaboration
    version: str = Field(default="1.0", description="Report version")
    parent_report_id: Optional[str] = Field(default=None, description="Parent report ID for versioning")
    is_template: bool = Field(default=False, description="Whether this is a template")
    template_id: Optional[str] = Field(default=None, description="Template used to generate this report")
    
    # Sharing and collaboration
    shared_with: List[str] = Field(default_factory=list, description="User IDs with access to this report")
    sharing_permissions: Dict[str, str] = Field(
        default_factory=dict, 
        description="User permissions (view, edit, admin)"
    )
    is_public: bool = Field(default=False, description="Whether report is publicly accessible")
    public_link_token: Optional[str] = Field(default=None, description="Token for public access")
    
    # Branding and customization
    branding_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom branding configuration"
    )
    custom_css: Optional[str] = Field(default=None, description="Custom CSS for report styling")
    logo_url: Optional[str] = Field(default=None, description="Custom logo URL")
    
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
            [("report_id", 1)],  # Query reports by report ID (unique)
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
    
    def create_new_version(self, new_version: str) -> "Report":
        """Create a new version of this report."""
        new_report = Report(
            assessment_id=self.assessment_id,
            user_id=self.user_id,
            title=self.title,
            description=self.description,
            report_type=self.report_type,
            format=self.format,
            template_version=self.template_version,
            version=new_version,
            parent_report_id=str(self.id),
            template_id=self.template_id,
            branding_config=self.branding_config.copy(),
            custom_css=self.custom_css,
            logo_url=self.logo_url
        )
        return new_report
    
    def share_with_user(self, user_id: str, permission: str = "view") -> None:
        """Share report with a user."""
        if user_id not in self.shared_with:
            self.shared_with.append(user_id)
        self.sharing_permissions[user_id] = permission
        self.updated_at = datetime.utcnow()
    
    def revoke_access(self, user_id: str) -> None:
        """Revoke user access to the report."""
        if user_id in self.shared_with:
            self.shared_with.remove(user_id)
        if user_id in self.sharing_permissions:
            del self.sharing_permissions[user_id]
        self.updated_at = datetime.utcnow()
    
    def can_user_access(self, user_id: str, required_permission: str = "view") -> bool:
        """Check if user can access the report with required permission."""
        if self.user_id == user_id:  # Owner has all permissions
            return True
        if self.is_public and required_permission == "view":
            return True
        
        user_permission = self.sharing_permissions.get(user_id)
        if not user_permission:
            return False
        
        permission_levels = {"view": 1, "edit": 2, "admin": 3}
        return permission_levels.get(user_permission, 0) >= permission_levels.get(required_permission, 0)
    
    def apply_branding(self, branding_config: Dict[str, Any]) -> None:
        """Apply custom branding configuration."""
        self.branding_config.update(branding_config)
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        """String representation of the report."""
        return f"Report(type={self.report_type.value}, status={self.status.value}, version={self.version})"