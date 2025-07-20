"""
Audit logging system for Infra Mind.

Provides comprehensive audit logging for security, compliance, and monitoring.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

from ..models.user import User


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TOKEN_REFRESH = "token_refresh"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # Assessment events
    ASSESSMENT_CREATED = "assessment_created"
    ASSESSMENT_UPDATED = "assessment_updated"
    ASSESSMENT_DELETED = "assessment_deleted"
    ASSESSMENT_VIEWED = "assessment_viewed"
    ASSESSMENT_SHARED = "assessment_shared"
    
    # Recommendation events
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_VIEWED = "recommendation_viewed"
    RECOMMENDATION_EXPORTED = "recommendation_exported"
    
    # Report events
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"
    REPORT_SHARED = "report_shared"
    
    # Data access events
    DATA_ACCESSED = "data_accessed"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    
    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    ENCRYPTION_KEY_USED = "encryption_key_used"
    SECURITY_VIOLATION = "security_violation"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGED = "configuration_changed"
    ERROR_OCCURRED = "error_occurred"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Audit event data structure.
    
    Learning Note: Using dataclass for structured audit events
    makes it easier to serialize and analyze audit data.
    """
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    outcome: str = "success"  # success, failure, error
    severity: AuditSeverity = AuditSeverity.LOW
    details: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO string
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Learning Note: This system provides structured audit logging
    for security compliance and forensic analysis.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to audit log file (optional)
        """
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for audit logs
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.
        
        Args:
            event: AuditEvent to log
        """
        # Determine log level based on severity
        level_map = {
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }
        
        level = level_map.get(event.severity, logging.INFO)
        
        # Log the event
        self.logger.log(level, event.to_json())
    
    def log_authentication(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        outcome: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log authentication events."""
        severity = AuditSeverity.HIGH if outcome == "failure" else AuditSeverity.MEDIUM
        
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            severity=severity,
            details=details
        )
        
        self.log_event(event)
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        outcome: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log data access events."""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESSED,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            outcome=outcome,
            severity=AuditSeverity.MEDIUM,
            details=details
        )
        
        self.log_event(event)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.HIGH
    ) -> None:
        """Log security events."""
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            outcome="security_event",
            severity=severity,
            details=details
        )
        
        self.log_event(event)
    
    def log_system_event(
        self,
        event_type: AuditEventType,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.LOW
    ) -> None:
        """Log system events."""
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            outcome="system_event",
            severity=severity,
            details=details
        )
        
        self.log_event(event)


class ComplianceLogger:
    """
    Specialized logger for compliance requirements.
    
    Learning Note: Compliance logging requires specific data retention
    and audit trail requirements for regulations like GDPR, HIPAA, etc.
    """
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    def log_gdpr_event(
        self,
        event_type: str,
        user_id: str,
        data_type: str,
        action: str,
        legal_basis: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log GDPR compliance events."""
        compliance_details = {
            "regulation": "GDPR",
            "data_type": data_type,
            "legal_basis": legal_basis,
            "retention_period": "as_per_policy",
            **(details or {})
        }
        
        self.audit_logger.log_data_access(
            user_id=user_id,
            resource_type="personal_data",
            resource_id=f"gdpr_{data_type}",
            action=action,
            details=compliance_details
        )
    
    def log_hipaa_event(
        self,
        event_type: str,
        user_id: str,
        phi_type: str,
        action: str,
        purpose: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log HIPAA compliance events."""
        compliance_details = {
            "regulation": "HIPAA",
            "phi_type": phi_type,
            "purpose": purpose,
            "minimum_necessary": True,
            **(details or {})
        }
        
        self.audit_logger.log_data_access(
            user_id=user_id,
            resource_type="phi",
            resource_id=f"hipaa_{phi_type}",
            action=action,
            details=compliance_details
        )
    
    def log_data_retention_event(
        self,
        data_type: str,
        action: str,
        retention_period: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log data retention events."""
        retention_details = {
            "data_type": data_type,
            "retention_period": retention_period,
            "reason": reason,
            "compliance_requirement": True,
            **(details or {})
        }
        
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESSED,
            timestamp=datetime.now(timezone.utc),
            action=action,
            outcome="retention_policy",
            severity=AuditSeverity.MEDIUM,
            details=retention_details
        )
        
        self.audit_logger.log_event(event)


class AuditAnalyzer:
    """
    Analyzer for audit logs to detect patterns and anomalies.
    
    Learning Note: Automated analysis of audit logs can help
    detect security threats and compliance violations.
    """
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.events: List[AuditEvent] = []
    
    def add_event(self, event: AuditEvent) -> None:
        """Add event for analysis."""
        self.events.append(event)
    
    def detect_failed_login_attempts(self, threshold: int = 5, window_minutes: int = 15) -> List[str]:
        """
        Detect multiple failed login attempts.
        
        Args:
            threshold: Number of failed attempts to trigger alert
            window_minutes: Time window to check
            
        Returns:
            List of IP addresses with suspicious activity
        """
        from collections import defaultdict
        
        suspicious_ips = []
        ip_failures = defaultdict(list)
        
        # Group failed login attempts by IP
        for event in self.events:
            if (event.event_type == AuditEventType.LOGIN_FAILURE and 
                event.outcome == "failure" and 
                event.ip_address):
                ip_failures[event.ip_address].append(event.timestamp)
        
        # Check each IP for threshold violations
        for ip, timestamps in ip_failures.items():
            # Sort timestamps
            timestamps.sort()
            
            # Check sliding window
            for i in range(len(timestamps)):
                window_start = timestamps[i]
                window_end = window_start + timedelta(minutes=window_minutes)
                
                # Count failures in window
                failures_in_window = sum(
                    1 for ts in timestamps[i:] 
                    if ts <= window_end
                )
                
                if failures_in_window >= threshold:
                    suspicious_ips.append(ip)
                    break
        
        return suspicious_ips
    
    def detect_unusual_access_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Detect unusual access patterns for a user.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Dictionary with analysis results
        """
        user_events = [e for e in self.events if e.user_id == user_id]
        
        if not user_events:
            return {"status": "no_data"}
        
        # Analyze access times
        access_hours = [e.timestamp.hour for e in user_events]
        unusual_hours = [h for h in access_hours if h < 6 or h > 22]  # Outside business hours
        
        # Analyze IP addresses
        ip_addresses = list(set(e.ip_address for e in user_events if e.ip_address))
        
        # Analyze resource access
        resources = [e.resource_type for e in user_events if e.resource_type]
        resource_counts = {}
        for resource in resources:
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
        
        return {
            "status": "analyzed",
            "total_events": len(user_events),
            "unusual_hour_access": len(unusual_hours),
            "unique_ip_addresses": len(ip_addresses),
            "resource_access_counts": resource_counts,
            "risk_score": self._calculate_risk_score(user_events)
        }
    
    def _calculate_risk_score(self, events: List[AuditEvent]) -> float:
        """Calculate risk score based on event patterns."""
        if not events:
            return 0.0
        
        risk_score = 0.0
        
        # Failed events increase risk
        failed_events = sum(1 for e in events if e.outcome == "failure")
        risk_score += (failed_events / len(events)) * 30
        
        # High severity events increase risk
        high_severity_events = sum(1 for e in events if e.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL])
        risk_score += (high_severity_events / len(events)) * 40
        
        # Multiple IP addresses increase risk
        unique_ips = len(set(e.ip_address for e in events if e.ip_address))
        if unique_ips > 3:
            risk_score += min(unique_ips * 5, 30)
        
        return min(risk_score, 100.0)  # Cap at 100


# Global audit logger instance
audit_logger = AuditLogger()
compliance_logger = ComplianceLogger(audit_logger)


# Convenience functions
def log_authentication_event(
    event_type: AuditEventType,
    user: Optional[User] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    outcome: str = "success",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Convenience function for logging authentication events."""
    audit_logger.log_authentication(
        event_type=event_type,
        user_id=str(user.id) if user else None,
        user_email=user.email if user else None,
        ip_address=ip_address,
        user_agent=user_agent,
        outcome=outcome,
        details=details
    )


def log_data_access_event(
    user: User,
    resource_type: str,
    resource_id: str,
    action: str,
    ip_address: Optional[str] = None,
    outcome: str = "success",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Convenience function for logging data access events."""
    audit_logger.log_data_access(
        user_id=str(user.id),
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        ip_address=ip_address,
        outcome=outcome,
        details=details
    )


def log_security_event(
    event_type: AuditEventType,
    user: Optional[User] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: AuditSeverity = AuditSeverity.HIGH
) -> None:
    """Convenience function for logging security events."""
    audit_logger.log_security_event(
        event_type=event_type,
        user_id=str(user.id) if user else None,
        ip_address=ip_address,
        details=details,
        severity=severity
    )