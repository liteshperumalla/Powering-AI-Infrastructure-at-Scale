"""
Compliance models for Infra Mind.

Defines comprehensive compliance framework, automated checks, evidence,
and audit management document structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# Enums for compliance
class ComplianceFrameworkType(str, Enum):
    SOC2 = "soc2"
    GDPR = "gdpr" 
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    NIST = "nist"
    CUSTOM = "custom"


class AuditFrequency(str, Enum):
    CONTINUOUS = "continuous"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    ASSESSMENT_NEEDED = "assessment_needed"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"


class CheckResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


# Embedded models
class ComplianceRequirement(BaseModel):
    """Individual compliance requirement within a framework."""
    requirement_id: str
    title: str
    description: str
    category: str
    priority: Priority
    compliance_status: ComplianceStatus
    last_verified: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    responsible_party: Optional[str] = None
    risk_if_non_compliant: Optional[str] = None
    evidence_required: List[str] = Field(default_factory=list)
    automated_checks: List[str] = Field(default_factory=list)


class ComplianceControl(BaseModel):
    """Control implementation for compliance requirements."""
    control_id: str
    name: str
    description: str
    control_type: str  # preventive, detective, corrective
    implementation_status: str  # implemented, planned, not_applicable
    effectiveness: str  # effective, needs_improvement, ineffective
    owner: Optional[str] = None
    test_frequency: Optional[str] = None
    last_tested: Optional[datetime] = None


# Main Document Models

class ComplianceFramework(Document):
    """Compliance framework document model."""
    
    # Basic information
    name: str = Indexed()
    version: str
    framework_type: ComplianceFrameworkType
    description: Optional[str] = None
    
    # Assessment configuration
    audit_frequency: AuditFrequency
    last_assessment_date: Optional[datetime] = None
    next_assessment_date: Optional[datetime] = None
    
    # Compliance metrics
    overall_compliance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: ComplianceStatus = Field(default=ComplianceStatus.ASSESSMENT_NEEDED)
    
    # Requirements and controls
    requirements: List[ComplianceRequirement] = Field(default_factory=list)
    controls: List[ComplianceControl] = Field(default_factory=list)
    
    # Metadata
    created_by: str = Indexed()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "compliance_frameworks"


class AutomatedCheck(Document):
    """Automated compliance check document model."""
    
    # Basic information
    framework_id: str = Indexed()
    requirement_id: str
    check_name: str
    check_type: str  # access_control, encryption, logging, etc.
    description: Optional[str] = None
    
    # Check configuration
    check_logic: Dict[str, Any] = Field(default_factory=dict)
    frequency: str  # daily, weekly, monthly, etc.
    data_sources: List[str] = Field(default_factory=list)
    
    # Status and scheduling
    status: CheckStatus = Field(default=CheckStatus.ACTIVE)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_result: Optional[CheckResult] = None
    
    # Metadata
    created_by: str = Indexed()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "automated_checks"


class CheckExecution(Document):
    """Individual check execution result."""
    
    check_id: str = Indexed()
    framework_id: str = Indexed()
    execution_time: datetime = Field(default_factory=datetime.utcnow)
    
    result: CheckResult
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    
    # Results details
    details: Dict[str, Any] = Field(default_factory=dict)
    evidence_collected: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Performance metrics
    execution_duration: Optional[float] = None  # seconds
    
    class Settings:
        collection = "check_executions"


class EvidenceRequirement(Document):
    """Evidence requirement document model."""
    
    framework_id: str = Indexed()
    requirement_id: str
    
    # Evidence details
    evidence_type: str  # document, screenshot, log, certificate, etc.
    title: str
    description: str
    collection_method: str  # manual, automated, semi_automated
    
    # Collection configuration
    frequency: str  # daily, weekly, monthly, on_demand
    retention_period: str
    storage_location: Optional[str] = None
    
    # Status
    current_status: str  # collected, missing, expired, insufficient
    last_collected: Optional[datetime] = None
    next_collection: Optional[datetime] = None
    
    # Access controls
    access_controls: List[str] = Field(default_factory=list)
    
    # Metadata
    created_by: str = Indexed()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "evidence_requirements"


class ComplianceEvidence(Document):
    """Collected compliance evidence."""
    
    evidence_requirement_id: str = Indexed()
    framework_id: str = Indexed()
    
    # Evidence details
    title: str
    description: Optional[str] = None
    evidence_type: str
    
    # File information
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    
    # Collection information
    collected_by: str = Indexed()
    collection_date: datetime = Field(default_factory=datetime.utcnow)
    collection_method: str
    
    # Validation
    validation_status: str = Field(default="pending")  # pending, valid, invalid, incomplete
    validation_notes: List[str] = Field(default_factory=list)
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    
    class Settings:
        collection = "compliance_evidence"


class RemediationAction(Document):
    """Remediation action for compliance issues."""
    
    framework_id: str = Indexed()
    requirement_id: str
    
    # Action details
    title: str
    description: str
    category: str  # security, process, documentation, etc.
    priority: Priority
    
    # Implementation
    implementation_steps: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    
    # Assignment and tracking
    assigned_to: str = Indexed()
    status: str = Field(default="open")  # open, in_progress, completed, cancelled
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    
    # Progress tracking
    progress_notes: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    
    # Metadata
    created_by: str = Indexed()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "remediation_actions"


class ComplianceAudit(Document):
    """Compliance audit document model."""
    
    # Basic information
    audit_name: str
    audit_type: str  # internal, external, self_assessment
    frameworks_in_scope: List[str] = Field(default_factory=list)
    
    # Auditor information
    auditor_name: Optional[str] = None
    auditor_organization: Optional[str] = None
    auditor_contact: Optional[str] = None
    
    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    report_due_date: Optional[datetime] = None
    
    # Scope and findings
    scope_description: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Status
    status: str = Field(default="planning")  # planning, in_progress, completed, cancelled
    overall_rating: Optional[str] = None
    
    # Metadata
    created_by: str = Indexed()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "compliance_audits"


class ComplianceAlert(Document):
    """Compliance alert and notification."""
    
    # Alert details
    alert_type: str  # deadline, failure, threshold, etc.
    severity: str  # low, medium, high, critical
    title: str
    message: str
    
    # Context
    framework_id: Optional[str] = Indexed()
    affected_items: List[str] = Field(default_factory=list)
    
    # Status
    status: str = Field(default="active")  # active, acknowledged, resolved
    action_required: bool = Field(default=False)
    
    # Response tracking
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledgment_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "compliance_alerts"


class ComplianceDashboardMetrics(Document):
    """Dashboard metrics snapshot for compliance."""
    
    # Overall metrics
    overall_compliance_score: float
    active_frameworks: int
    passed_checks: int
    failed_checks: int
    pending_actions: int
    
    # Framework breakdown
    framework_scores: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Trends data
    compliance_trends: List[Dict[str, Any]] = Field(default_factory=list)
    risk_trends: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Activity summary
    activity_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Snapshot metadata
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    calculated_by: Optional[str] = None
    
    class Settings:
        collection = "compliance_dashboard_metrics"