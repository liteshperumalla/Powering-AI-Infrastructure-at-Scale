"""
Base Pydantic models and common schemas for Infra Mind.

Learning Note: Base models provide common functionality and ensure
consistency across all our data models.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TimestampMixin(BaseModel):
    """
    Mixin for models that need timestamp fields.
    
    Learning Note: Mixins allow us to share common functionality
    across multiple models without inheritance complexity.
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.
    
    Learning Note: This ensures all our models have consistent
    behavior for JSON serialization and validation.
    """
    model_config = ConfigDict(
        # Allow extra fields for flexibility
        extra="forbid",
        # Use enum values instead of names
        use_enum_values=True,
        # Validate assignment after model creation
        validate_assignment=True,
        # Allow population by field name or alias
        populate_by_name=True,
    )


class CompanySize(str, Enum):
    """Company size categories for business requirements."""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class Industry(str, Enum):
    """Industry categories for compliance and recommendations."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    OTHER = "other"


class BudgetRange(str, Enum):
    """Budget ranges for cost optimization."""
    UNDER_10K = "under_10k"
    RANGE_10K_50K = "10k_50k"
    RANGE_50K_100K = "50k_100k"
    RANGE_100K_500K = "100k_500k"
    RANGE_500K_1M = "500k_1m"
    OVER_1M = "over_1m"


class ComplianceRequirement(str, Enum):
    """Regulatory compliance requirements."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    NONE = "none"


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"


class WorkloadType(str, Enum):
    """Types of workloads for technical requirements."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DATA_PROCESSING = "data_processing"
    MACHINE_LEARNING = "machine_learning"
    DATABASE = "database"
    ANALYTICS = "analytics"
    IOT = "iot"
    MOBILE_BACKEND = "mobile_backend"
    MICROSERVICES = "microservices"


class Priority(str, Enum):
    """Priority levels for assessments and recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssessmentStatus(str, Enum):
    """Status of infrastructure assessments."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    AGENT_ANALYSIS = "agent_analysis"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class RecommendationConfidence(str, Enum):
    """Confidence levels for AI recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Common response models
class SuccessResponse(BaseSchema):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseSchema):
    """Standard error response."""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, pagination: PaginationParams):
        """Create paginated response from items and pagination params."""
        pages = (total + pagination.limit - 1) // pagination.limit
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages
        )