"""
Security management API endpoints for Infra Mind.

Provides endpoints for security auditing, incident management, and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from .auth import get_current_user
from ...core.rbac import require_permission, Permission
from ...core.security_audit import SecurityAuditor, run_security_audit, VulnerabilityLevel, SecurityTestType
from ...core.incident_response import (
    IncidentManager, SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus,
    report_security_event, create_incident
)
from ...core.audit import log_security_event, AuditEventType, AuditSeverity
from ...models.user import User
from ...schemas.base import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])

# Global incident manager
incident_manager = IncidentManager()


# Pydantic models for API
from pydantic import BaseModel, Field
from typing import Union

class SecurityAuditRequest(BaseModel):
    """Request model for security audit."""
    target_url: Optional[str] = Field(default="http://localhost:8000", description="Target URL to audit")
    test_types: Optional[List[SecurityTestType]] = Field(default=None, description="Specific test types to run")
    
class SecurityAuditResponse(BaseModel):
    """Response model for security audit."""
    audit_id: str
    start_time: datetime
    end_time: datetime
    total_findings: int
    critical_findings: int
    high_findings: int
    risk_score: float
    compliance_status: Dict[str, bool]
    findings_summary: Dict[str, int]
    recommendations: List[str]

class SecurityFindingResponse(BaseModel):
    """Response model for security finding."""
    test_type: SecurityTestType
    vulnerability_level: VulnerabilityLevel
    title: str
    description: str
    affected_component: str
    evidence: Dict[str, Any]
    remediation: str
    cve_references: List[str]
    compliance_impact: List[str]
    timestamp: datetime

class IncidentCreateRequest(BaseModel):
    """Request model for creating incident."""
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    affected_systems: List[str]
    indicators: Dict[str, Any]

class IncidentResponse(BaseModel):
    """Response model for incident."""
    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    title: str
    description: str
    affected_systems: List[str]
    indicators: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

class IncidentUpdateRequest(BaseModel):
    """Request model for updating incident."""
    status: IncidentStatus
    notes: Optional[str] = ""

class SecurityEventRequest(BaseModel):
    """Request model for reporting security event."""
    event_type: str
    event_data: Dict[str, Any]
    source: Optional[str] = "api"

class SecurityMetricsResponse(BaseModel):
    """Response model for security metrics."""
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    avg_resolution_time_hours: float
    incidents_by_type: Dict[str, int]
    incidents_by_severity: Dict[str, int]
    recent_audits: int
    compliance_status: Dict[str, bool]


@router.post("/audit/start", response_model=Dict[str, str])
async def start_security_audit(
    request: SecurityAuditRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Start a comprehensive security audit.
    
    Requires system management permissions.
    """
    try:
        # Log audit initiation
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "security_audit_started",
                "target_url": request.target_url,
                "test_types": request.test_types
            },
            severity=AuditSeverity.MEDIUM
        )
        
        # Start audit in background
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        async def run_audit():
            try:
                async with SecurityAuditor(request.target_url) as auditor:
                    if request.test_types:
                        # Run specific tests (simplified - would need more implementation)
                        report = await auditor.run_full_audit()
                    else:
                        # Run full audit
                        report = await auditor.run_full_audit()
                
                # Store audit results (in production, save to database)
                logger.info(f"Security audit {audit_id} completed with {len(report.findings)} findings")
                
            except Exception as e:
                logger.error(f"Security audit {audit_id} failed: {e}")
        
        background_tasks.add_task(run_audit)
        
        return {
            "audit_id": audit_id,
            "status": "started",
            "message": "Security audit started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to start security audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start security audit"
        )


@router.get("/audit/{audit_id}/status")
async def get_audit_status(
    audit_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get status of a security audit.
    
    Requires log viewing permissions.
    """
    try:
        # In production, this would query the database for audit status
        # For now, return mock status
        return {
            "audit_id": audit_id,
            "status": "completed",
            "progress": 100,
            "findings_count": 5,
            "estimated_completion": None
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit status"
        )


@router.get("/audit/{audit_id}/report", response_model=SecurityAuditResponse)
async def get_audit_report(
    audit_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get security audit report.
    
    Requires log viewing permissions.
    """
    try:
        # In production, this would retrieve the actual audit report from database
        # For now, return mock report
        mock_report = SecurityAuditResponse(
            audit_id=audit_id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_findings=5,
            critical_findings=1,
            high_findings=2,
            risk_score=35.0,
            compliance_status={
                "OWASP": False,
                "GDPR": True,
                "NIST": False,
                "HIPAA": True
            },
            findings_summary={
                "authentication": 2,
                "input_validation": 1,
                "configuration": 2
            },
            recommendations=[
                "Address critical authentication vulnerabilities immediately",
                "Implement proper input validation",
                "Review security configuration"
            ]
        )
        
        return mock_report
        
    except Exception as e:
        logger.error(f"Failed to get audit report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit report"
        )


@router.get("/audit/{audit_id}/findings", response_model=List[SecurityFindingResponse])
async def get_audit_findings(
    audit_id: str,
    severity: Optional[VulnerabilityLevel] = None,
    test_type: Optional[SecurityTestType] = None,
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get detailed security audit findings.
    
    Requires log viewing permissions.
    """
    try:
        # In production, this would retrieve findings from database with filters
        # For now, return mock findings
        mock_findings = [
            SecurityFindingResponse(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Weak Password Policy",
                description="System accepts weak passwords",
                affected_component="Authentication System",
                evidence={"weak_passwords_accepted": ["123456", "password"]},
                remediation="Implement strong password policy",
                cve_references=["CWE-521"],
                compliance_impact=["NIST", "OWASP"],
                timestamp=datetime.now(timezone.utc)
            ),
            SecurityFindingResponse(
                test_type=SecurityTestType.INPUT_VALIDATION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="SQL Injection Vulnerability",
                description="SQL injection detected in user input",
                affected_component="Database Interface",
                evidence={"payload": "' OR 1=1", "response": "SQL error"},
                remediation="Use parameterized queries",
                cve_references=["CWE-89"],
                compliance_impact=["OWASP"],
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        # Apply filters
        filtered_findings = mock_findings
        if severity:
            filtered_findings = [f for f in filtered_findings if f.vulnerability_level == severity]
        if test_type:
            filtered_findings = [f for f in filtered_findings if f.test_type == test_type]
        
        return filtered_findings
        
    except Exception as e:
        logger.error(f"Failed to get audit findings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit findings"
        )


@router.post("/incidents", response_model=IncidentResponse)
async def create_security_incident(
    request: IncidentCreateRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Create a new security incident.
    
    Requires system management permissions.
    """
    try:
        # Create incident
        incident = await create_incident(
            incident_type=request.incident_type,
            severity=request.severity,
            title=request.title,
            description=request.description,
            affected_systems=request.affected_systems,
            indicators=request.indicators,
            created_by=str(current_user.id)
        )
        
        # Log incident creation
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "incident_created",
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity
            },
            severity=AuditSeverity.HIGH
        )
        
        return IncidentResponse(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            severity=incident.severity,
            status=incident.status,
            title=incident.title,
            description=incident.description,
            affected_systems=incident.affected_systems,
            indicators=incident.indicators,
            timeline=incident.timeline,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create incident"
        )


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_security_incidents(
    status: Optional[IncidentStatus] = None,
    severity: Optional[IncidentSeverity] = None,
    incident_type: Optional[IncidentType] = None,
    limit: int = 50,
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    List security incidents with optional filters.
    
    Requires log viewing permissions.
    """
    try:
        # Get incidents from manager
        incidents = incident_manager.list_incidents(
            status=status,
            severity=severity,
            incident_type=incident_type
        )
        
        # Apply limit
        incidents = incidents[:limit]
        
        # Convert to response format
        response_incidents = []
        for incident in incidents:
            response_incidents.append(IncidentResponse(
                incident_id=incident.incident_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                title=incident.title,
                description=incident.description,
                affected_systems=incident.affected_systems,
                indicators=incident.indicators,
                timeline=incident.timeline,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
                resolved_at=incident.resolved_at
            ))
        
        return response_incidents
        
    except Exception as e:
        logger.error(f"Failed to list incidents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list incidents"
        )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_security_incident(
    incident_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get a specific security incident.
    
    Requires log viewing permissions.
    """
    try:
        # Get incident from manager
        incident = incident_manager.get_incident(incident_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        return IncidentResponse(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            severity=incident.severity,
            status=incident.status,
            title=incident.title,
            description=incident.description,
            affected_systems=incident.affected_systems,
            indicators=incident.indicators,
            timeline=incident.timeline,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get incident"
        )


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_security_incident(
    incident_id: str,
    request: IncidentUpdateRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Update a security incident status.
    
    Requires system management permissions.
    """
    try:
        # Update incident
        success = await incident_manager.update_incident_status(
            incident_id,
            request.status,
            str(current_user.id),
            request.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Get updated incident
        incident = incident_manager.get_incident(incident_id)
        
        # Log incident update
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "incident_updated",
                "incident_id": incident_id,
                "new_status": request.status,
                "notes": request.notes
            },
            severity=AuditSeverity.MEDIUM
        )
        
        return IncidentResponse(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            severity=incident.severity,
            status=incident.status,
            title=incident.title,
            description=incident.description,
            affected_systems=incident.affected_systems,
            indicators=incident.indicators,
            timeline=incident.timeline,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update incident"
        )


@router.post("/events/report")
async def report_security_event_endpoint(
    request: SecurityEventRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Report a security event for analysis.
    
    Requires system management permissions.
    """
    try:
        # Add user context to event data
        event_data = request.event_data.copy()
        event_data.update({
            "event_type": request.event_type,
            "source": request.source,
            "reported_by": str(current_user.id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Report event for analysis
        incident = await report_security_event(event_data)
        
        # Log event reporting
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "security_event_reported",
                "event_type": request.event_type,
                "incident_created": incident is not None,
                "incident_id": incident.incident_id if incident else None
            },
            severity=AuditSeverity.MEDIUM
        )
        
        if incident:
            return {
                "status": "incident_created",
                "incident_id": incident.incident_id,
                "message": "Security event triggered incident creation"
            }
        else:
            return {
                "status": "event_recorded",
                "message": "Security event recorded, no incident triggered"
            }
        
    except Exception as e:
        logger.error(f"Failed to report security event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report security event"
        )


@router.get("/metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    current_user: User = Depends(require_permission(Permission.VIEW_METRICS))
):
    """
    Get security metrics and statistics.
    
    Requires metrics viewing permissions.
    """
    try:
        # Get incident statistics
        incident_stats = incident_manager.get_incident_statistics()
        
        # Calculate additional metrics
        critical_incidents = incident_stats["by_severity"].get("critical", 0)
        recent_audits = 3  # Mock value - would query audit database
        
        # Mock compliance status - would be calculated from recent audits
        compliance_status = {
            "OWASP": True,
            "GDPR": True,
            "NIST": False,
            "HIPAA": True,
            "ISO27001": True
        }
        
        return SecurityMetricsResponse(
            total_incidents=incident_stats["total_incidents"],
            open_incidents=incident_stats["open_incidents"],
            critical_incidents=critical_incidents,
            avg_resolution_time_hours=incident_stats["avg_resolution_time_hours"],
            incidents_by_type=incident_stats["by_type"],
            incidents_by_severity=incident_stats["by_severity"],
            recent_audits=recent_audits,
            compliance_status=compliance_status
        )
        
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security metrics"
        )


@router.post("/block-ip")
async def block_ip_address(
    ip_address: str,
    reason: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Block an IP address.
    
    Requires system management permissions.
    """
    try:
        # Block IP using security monitor
        from ...core.security import security_monitor
        security_monitor.block_ip(ip_address, reason)
        
        # Log IP blocking
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "ip_blocked",
                "ip_address": ip_address,
                "reason": reason
            },
            severity=AuditSeverity.HIGH
        )
        
        return {
            "status": "success",
            "message": f"IP address {ip_address} has been blocked",
            "ip_address": ip_address,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Failed to block IP address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block IP address"
        )


@router.delete("/block-ip/{ip_address}")
async def unblock_ip_address(
    ip_address: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Unblock an IP address.
    
    Requires system management permissions.
    """
    try:
        # Unblock IP using security monitor
        from ...core.security import security_monitor
        security_monitor.unblock_ip(ip_address)
        
        # Log IP unblocking
        log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user=current_user,
            details={
                "action": "ip_unblocked",
                "ip_address": ip_address
            },
            severity=AuditSeverity.MEDIUM
        )
        
        return {
            "status": "success",
            "message": f"IP address {ip_address} has been unblocked",
            "ip_address": ip_address
        }
        
    except Exception as e:
        logger.error(f"Failed to unblock IP address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock IP address"
        )


@router.get("/blocked-ips")
async def list_blocked_ips(
    current_user: User = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    List blocked IP addresses.
    
    Requires log viewing permissions.
    """
    try:
        # Get blocked IPs from security monitor
        from ...core.security import security_monitor
        blocked_ips = list(security_monitor.blocked_ips)
        
        return {
            "blocked_ips": blocked_ips,
            "count": len(blocked_ips)
        }
        
    except Exception as e:
        logger.error(f"Failed to list blocked IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list blocked IPs"
        )


@router.get("/health")
async def security_health_check():
    """
    Security system health check.
    
    Public endpoint for monitoring.
    """
    try:
        # Check various security components
        health_status = {
            "security_monitor": "healthy",
            "incident_manager": "healthy" if incident_manager else "unhealthy",
            "audit_logger": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in health_status.values() if isinstance(status, str)
        ) else "degraded"
        
        health_status["overall_status"] = overall_status
        
        return health_status
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }