"""
Audit logging model for Infra Mind.

Tracks all system actions for compliance, security, and debugging.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from beanie import Document, Indexed
from pydantic import Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Document):
    """
    Audit log document model for tracking system actions.

    Learning Note: Essential for compliance (SOC 2, ISO 27001), security auditing,
    and debugging production issues. Provides complete audit trail.
    """

    # Action details
    action: str = Indexed()  # Action performed (e.g., "assessment_created", "recommendation_generated")
    resource_type: str = Indexed()  # Type of resource affected (e.g., "assessment", "user")
    resource_id: str = Indexed()  # ID of the resource

    # User context
    user_id: Optional[str] = Field(default=None, description="User who performed the action")
    user_agent: Optional[str] = Field(default=None, description="User agent string")
    ip_address: Optional[str] = Field(default=None, description="IP address of the request")

    # Additional context
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the action"
    )

    # Outcome
    status: str = Field(default="success", description="Status: success, failure, warning")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    # Timestamps
    timestamp: datetime = Field(default_factory=_utcnow, description="When action occurred")

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    severity: str = Field(default="info", description="Severity: info, warning, error, critical")

    class Settings:
        """Beanie document settings."""
        name = "audit_logs"
        indexes = [
            [("timestamp", -1)],  # Time-based queries
            [("action", 1), ("timestamp", -1)],  # Action-based queries with time
            [("resource_id", 1), ("timestamp", -1)],  # Resource audit trail
            [("user_id", 1), ("timestamp", -1)],  # User activity tracking
            [("severity", 1), ("timestamp", -1)],  # Severity-based filtering
        ]

    def __str__(self) -> str:
        """String representation of audit log."""
        return f"AuditLog(action={self.action}, resource={self.resource_type}:{self.resource_id})"
