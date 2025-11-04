"""
Compliance API endpoints for Infra Mind.

Provides REST API endpoints for compliance features including
data retention, consent management, data export, and audit trails.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field

from ..auth import get_current_user, get_current_admin_user
from ...models.user import User
from ...models.compliance import (
    ComplianceFramework,
    AutomatedCheck,
    CheckExecution,
    EvidenceRequirement,
    ComplianceEvidence,
    RemediationAction,
    ComplianceAudit,
    ComplianceAlert,
    ComplianceDashboardMetrics,
    ComplianceFrameworkType,
    ComplianceStatus,
    AuditFrequency,
    Priority,
    CheckStatus,
    CheckResult
)
from ...core.compliance import (
    compliance_manager,
    DataCategory,
    RetentionPeriod,
    ConsentType,
    ConsentStatus,
    DataRetentionPolicy,
    UserConsent,
    record_user_consent,
    export_user_data_request,
    delete_user_data_request
)
from ...core.audit import audit_logger, AuditEvent, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(tags=["compliance"])


# Request/Response Models

class ConsentRequest(BaseModel):
    """Request model for consent operations."""
    consent_type: ConsentType
    status: ConsentStatus
    legal_basis: Optional[str] = None
    purpose: Optional[str] = None
    data_categories: Optional[List[DataCategory]] = None


class ConsentResponse(BaseModel):
    """Response model for consent operations."""
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    legal_basis: Optional[str] = None
    purpose: Optional[str] = None


class DataExportRequest(BaseModel):
    """Request model for data export."""
    data_categories: Optional[List[DataCategory]] = None
    format: str = Field(default="json", description="Export format (json, csv)")


class DataDeletionRequest(BaseModel):
    """Request model for data deletion."""
    data_categories: Optional[List[DataCategory]] = None
    reason: str = Field(description="Reason for deletion request")
    confirm: bool = Field(description="Confirmation that user understands deletion is permanent")


class RetentionPolicyRequest(BaseModel):
    """Request model for updating retention policies."""
    data_category: DataCategory
    retention_period: RetentionPeriod
    legal_basis: str
    description: str
    auto_delete: bool = True
    exceptions: Optional[List[str]] = None


class ComplianceReportRequest(BaseModel):
    """Request model for compliance reports."""
    start_date: datetime
    end_date: datetime
    include_details: bool = Field(default=False, description="Include detailed audit information")


# Root Compliance Endpoint

@router.get("/", response_model=Dict[str, Any])
async def get_compliance_overview(
    current_user: User = Depends(get_current_user)
):
    """Get general compliance overview - main compliance endpoint."""
    try:
        # Get basic compliance status
        compliance_status = {
            "status": "compliant",
            "frameworks": ["GDPR", "SOC2", "HIPAA"],
            "active_policies": 5,
            "recent_audits": 2,
            "consent_status": "up_to_date",
            "data_retention": "configured",
            "user_id": str(current_user.id),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "success": True,
            "compliance_overview": compliance_status,
            "available_endpoints": [
                "/overview - Detailed compliance overview",
                "/frameworks - Compliance frameworks",
                "/consent - Consent management", 
                "/data/export - Data export requests",
                "/audit/summary - Audit information",
                "/dashboard - Compliance dashboard"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance overview"
        )


# Consent Management Endpoints

@router.post("/consent", response_model=Dict[str, Any])
async def record_consent(
    request: Request,
    consent_request: ConsentRequest,
    current_user: User = Depends(get_current_user)
):
    """Record user consent for data processing."""
    try:
        # Get client information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Record consent
        await record_user_consent(
            user_id=str(current_user.id),
            consent_type=consent_request.consent_type,
            status=consent_request.status,
            ip_address=client_ip,
            user_agent=user_agent,
            legal_basis=consent_request.legal_basis,
            purpose=consent_request.purpose,
            data_categories=consent_request.data_categories or []
        )
        
        return {
            "success": True,
            "message": f"Consent {consent_request.status.value} recorded for {consent_request.consent_type.value}",
            "user_id": str(current_user.id),
            "consent_type": consent_request.consent_type.value,
            "status": consent_request.status.value,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to record consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent"
        )


@router.get("/consent", response_model=Dict[str, Any])
async def get_consent_status(
    current_user: User = Depends(get_current_user)
):
    """Get current consent status for the user."""
    try:
        # Check if user is valid
        if not current_user or not hasattr(current_user, 'id'):
            logger.error("Invalid user object in get_consent_status")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        consent_summary = compliance_manager.get_consent_summary(str(current_user.id))
        
        # Log access
        try:
            audit_logger.log_data_access(
                user_id=str(current_user.id),
                resource_type="consent_status",
                resource_id=f"consent_{current_user.id}",
                action="view_consent_status"
            )
        except Exception as audit_error:
            logger.warning(f"Failed to log audit event: {audit_error}")
        
        return consent_summary
        
    except HTTPException:
        raise
    except Exception as e:
        user_id = getattr(current_user, 'id', 'unknown') if current_user else 'unknown'
        logger.error(f"Failed to get consent status for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consent status"
        )


@router.post("/consent/{consent_type}/withdraw", response_model=Dict[str, Any])
async def withdraw_consent(
    consent_type: ConsentType,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Withdraw consent for a specific type."""
    try:
        client_ip = request.client.host if request.client else None
        
        success = compliance_manager.withdraw_consent(
            user_id=str(current_user.id),
            consent_type=consent_type,
            ip_address=client_ip
        )
        
        if success:
            return {
                "success": True,
                "message": f"Consent withdrawn for {consent_type.value}",
                "user_id": str(current_user.id),
                "consent_type": consent_type.value,
                "withdrawn_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active consent found to withdraw"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to withdraw consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw consent"
        )


# Data Export and Portability Endpoints

@router.post("/data/export", response_model=Dict[str, Any])
async def export_user_data(
    export_request: DataExportRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Export user data for portability (GDPR Article 20)."""
    try:
        client_ip = request.client.host if request.client else None
        
        # Export data
        export_data = await export_user_data_request(
            user_id=str(current_user.id),
            requester_ip=client_ip
        )
        
        # Filter by requested categories if specified
        if export_request.data_categories:
            filtered_data = {
                "user_id": export_data["user_id"],
                "export_timestamp": export_data["export_timestamp"],
                "data_categories": [cat.value for cat in export_request.data_categories],
                "data": {}
            }
            
            for category in export_request.data_categories:
                category_key = category.value.replace("_data", "_data")  # Normalize key
                if category_key in export_data["data"]:
                    filtered_data["data"][category_key] = export_data["data"][category_key]
            
            export_data = filtered_data
        
        return {
            "success": True,
            "message": "Data export completed",
            "export_data": export_data,
            "format": export_request.format,
            "size_kb": len(str(export_data)) / 1024
        }
        
    except Exception as e:
        logger.error(f"Failed to export data for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )


@router.post("/data/delete", response_model=Dict[str, Any])
async def delete_user_data(
    deletion_request: DataDeletionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Delete user data (Right to Erasure - GDPR Article 17)."""
    try:
        if not deletion_request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deletion confirmation required"
            )
        
        client_ip = request.client.host if request.client else None
        
        # Schedule deletion in background
        background_tasks.add_task(
            _process_data_deletion,
            str(current_user.id),
            deletion_request.data_categories,
            deletion_request.reason,
            client_ip
        )
        
        return {
            "success": True,
            "message": "Data deletion request received and will be processed",
            "user_id": str(current_user.id),
            "data_categories": [cat.value for cat in deletion_request.data_categories] if deletion_request.data_categories else "all",
            "reason": deletion_request.reason,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "processing_status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process deletion request for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deletion request"
        )


async def _process_data_deletion(
    user_id: str,
    data_categories: Optional[List[DataCategory]],
    reason: str,
    client_ip: Optional[str]
):
    """Background task to process data deletion."""
    try:
        deletion_result = await delete_user_data_request(
            user_id=user_id,
            reason=reason,
            requester_ip=client_ip
        )
        
        logger.info(f"Completed data deletion for user {user_id}: {deletion_result}")
        
    except Exception as e:
        logger.error(f"Failed to complete data deletion for user {user_id}: {str(e)}")


# Data Retention Management Endpoints

@router.get("/retention/policies", response_model=Dict[str, Any])
async def get_retention_policies(
    current_user: User = Depends(get_current_admin_user)
):
    """Get all data retention policies (Admin only)."""
    try:
        policies = {}
        for category, policy in compliance_manager.retention_policies.items():
            policies[category.value] = {
                "data_category": policy.data_category.value,
                "retention_period": policy.retention_period.value,
                "legal_basis": policy.legal_basis,
                "description": policy.description,
                "auto_delete": policy.auto_delete,
                "exceptions": policy.exceptions
            }
        
        # Log access
        audit_logger.log_data_access(
            user_id=str(current_user.id),
            resource_type="retention_policies",
            resource_id="all_policies",
            action="view_retention_policies"
        )
        
        return {
            "success": True,
            "policies": policies,
            "total_policies": len(policies)
        }
        
    except Exception as e:
        logger.error(f"Failed to get retention policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve retention policies"
        )


@router.put("/retention/policies", response_model=Dict[str, Any])
async def update_retention_policy(
    policy_request: RetentionPolicyRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Update a data retention policy (Admin only)."""
    try:
        policy = DataRetentionPolicy(
            data_category=policy_request.data_category,
            retention_period=policy_request.retention_period,
            legal_basis=policy_request.legal_basis,
            description=policy_request.description,
            auto_delete=policy_request.auto_delete,
            exceptions=policy_request.exceptions or []
        )
        
        compliance_manager.update_retention_policy(policy)
        
        return {
            "success": True,
            "message": f"Retention policy updated for {policy_request.data_category.value}",
            "policy": {
                "data_category": policy.data_category.value,
                "retention_period": policy.retention_period.value,
                "legal_basis": policy.legal_basis,
                "description": policy.description,
                "auto_delete": policy.auto_delete,
                "exceptions": policy.exceptions
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update retention policy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update retention policy"
        )


@router.get("/retention/check/{data_category}", response_model=Dict[str, Any])
async def check_data_retention(
    data_category: DataCategory,
    created_date: datetime,
    current_user: User = Depends(get_current_admin_user)
):
    """Check data retention status for a category and date."""
    try:
        retention_check = await compliance_manager.check_data_expiry(
            data_category=data_category,
            created_date=created_date
        )
        
        return {
            "success": True,
            "data_category": data_category.value,
            "created_date": created_date.isoformat(),
            "retention_check": retention_check
        }
        
    except Exception as e:
        logger.error(f"Failed to check data retention: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check data retention"
        )


# Compliance Reporting Endpoints

@router.post("/reports/compliance", response_model=Dict[str, Any])
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Generate compliance report (Admin only)."""
    try:
        # Validate date range
        if report_request.end_date <= report_request.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        # Generate report
        report = compliance_manager.generate_compliance_report(
            start_date=report_request.start_date,
            end_date=report_request.end_date
        )
        
        # Log report generation
        audit_logger.log_data_access(
            user_id=str(current_user.id),
            resource_type="compliance_report",
            resource_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            action="generate_compliance_report",
            details={
                "start_date": report_request.start_date.isoformat(),
                "end_date": report_request.end_date.isoformat(),
                "include_details": report_request.include_details
            }
        )
        
        return {
            "success": True,
            "report": report,
            "generated_by": current_user.email,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


@router.get("/audit/summary", response_model=Dict[str, Any])
async def get_audit_summary(
    days: int = 30,
    current_user: User = Depends(get_current_admin_user)
):
    """Get audit trail summary for the last N days (Admin only)."""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # In a real implementation, this would query the audit log database
        summary = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_events": 0,  # Would be calculated from audit logs
                "authentication_events": 0,
                "data_access_events": 0,
                "security_events": 0,
                "compliance_events": 0,
                "system_events": 0
            },
            "top_users": [],  # Would be calculated from audit logs
            "top_resources": [],  # Would be calculated from audit logs
            "security_alerts": []  # Would be calculated from audit logs
        }
        
        # Log audit summary access
        audit_logger.log_data_access(
            user_id=str(current_user.id),
            resource_type="audit_summary",
            resource_id=f"summary_{days}days",
            action="view_audit_summary",
            details={"period_days": days}
        )
        
        return {
            "success": True,
            "audit_summary": summary,
            "requested_by": current_user.email,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit summary"
        )


# Privacy Controls Endpoints

@router.get("/privacy/settings", response_model=Dict[str, Any])
async def get_privacy_settings(
    current_user: User = Depends(get_current_user)
):
    """Get user's privacy settings and consent status."""
    try:
        consent_summary = compliance_manager.get_consent_summary(str(current_user.id))
        
        privacy_settings = {
            "user_id": str(current_user.id),
            "consent_status": consent_summary["consent_summary"],
            "data_retention": {
                "personal_data": "3 years",
                "assessment_data": "3 years",
                "audit_data": "7 years"
            },
            "data_portability": {
                "export_available": True,
                "formats": ["json", "csv"],
                "categories": [cat.value for cat in DataCategory]
            },
            "right_to_erasure": {
                "available": True,
                "categories": [cat.value for cat in DataCategory if cat != DataCategory.AUDIT_DATA],
                "exceptions": ["Audit data retained for compliance"]
            }
        }
        
        return {
            "success": True,
            "privacy_settings": privacy_settings
        }
        
    except Exception as e:
        logger.error(f"Failed to get privacy settings for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve privacy settings"
        )


@router.post("/privacy/consent-all", response_model=Dict[str, Any])
async def grant_all_consent(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Grant consent for all data processing types."""
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        consent_results = {}
        
        # Grant consent for all types
        for consent_type in ConsentType:
            await record_user_consent(
                user_id=str(current_user.id),
                consent_type=consent_type,
                status=ConsentStatus.GRANTED,
                ip_address=client_ip,
                user_agent=user_agent,
                legal_basis="User consent",
                purpose="Service provision and improvement"
            )
            consent_results[consent_type.value] = "granted"
        
        return {
            "success": True,
            "message": "All consent types granted",
            "user_id": str(current_user.id),
            "consent_results": consent_results,
            "granted_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to grant all consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant consent"
        )


# =============================================================================
# COMPLIANCE AUTOMATION ENDPOINTS
# =============================================================================

# Compliance Automation Request/Response Models

class ComplianceFrameworkRequest(BaseModel):
    """Request model for compliance framework creation."""
    name: str
    type: str
    version: str
    description: Optional[str] = None
    requirements_config: Optional[Dict[str, Any]] = None
    assessment_schedule: Optional[Dict[str, Any]] = None

class ComplianceFrameworkResponse(BaseModel):
    """Response model for compliance framework."""
    id: str
    name: str
    version: str
    type: str
    description: str
    audit_frequency: str
    last_assessment_date: Optional[str]
    next_assessment_date: Optional[str]
    overall_compliance_score: float
    status: str

class AutomatedCheckRequest(BaseModel):
    """Request model for automated check creation."""
    framework_id: str
    requirement_id: str
    check_name: str
    check_type: str
    check_logic: Dict[str, Any]
    frequency: str
    data_sources: List[str]

class ComplianceDashboardResponse(BaseModel):
    """Response model for compliance dashboard."""
    overall_compliance_score: float
    active_frameworks: int
    passed_checks: int
    failed_checks: int
    pending_actions: int
    recent_activities: List[Dict[str, Any]]


# Dashboard and Overview Endpoints

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_compliance_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get compliance automation dashboard overview."""
    try:
        # Get active frameworks
        frameworks = await ComplianceFramework.find().to_list()
        active_frameworks = len(frameworks)
        
        # Calculate overall compliance score
        total_score = sum(f.overall_compliance_score for f in frameworks)
        overall_compliance_score = total_score / active_frameworks if active_frameworks > 0 else 0.0
        
        # Get recent check executions
        recent_executions = await CheckExecution.find().sort(-CheckExecution.execution_time).limit(50).to_list()
        
        # Count check results
        passed_checks = len([e for e in recent_executions if e.result == CheckResult.PASSED])
        failed_checks = len([e for e in recent_executions if e.result == CheckResult.FAILED])
        
        # Get pending remediation actions
        pending_actions = await RemediationAction.find({"status": "open"}).count()
        
        # Build recent activities from various sources
        recent_activities = []
        
        # Add recent check executions
        for execution in recent_executions[:10]:
            framework = await ComplianceFramework.get(execution.framework_id)
            framework_name = framework.name if framework else "Unknown Framework"
            
            recent_activities.append({
                "id": str(execution.id),
                "type": "automated_check",
                "title": f"Automated Check Execution",
                "status": execution.result.value,
                "timestamp": execution.execution_time.isoformat(),
                "framework": framework_name
            })
        
        # Add recent remediation actions
        recent_remediation = await RemediationAction.find().sort(-RemediationAction.updated_at).limit(5).to_list()
        for action in recent_remediation:
            framework = await ComplianceFramework.get(action.framework_id)
            framework_name = framework.name if framework else "Unknown Framework"
            
            recent_activities.append({
                "id": str(action.id),
                "type": "remediation",
                "title": action.title,
                "status": action.status,
                "timestamp": action.updated_at.isoformat(),
                "framework": framework_name
            })
        
        # Sort activities by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activities = recent_activities[:15]  # Limit to 15 most recent
        
        # Build framework breakdown
        framework_breakdown = {}
        for framework in frameworks:
            framework_breakdown[framework.name] = {
                "score": framework.overall_compliance_score,
                "status": framework.status.value
            }
        
        # Get compliance trends (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_metrics = await ComplianceDashboardMetrics.find(
            ComplianceDashboardMetrics.snapshot_date >= thirty_days_ago
        ).sort(ComplianceDashboardMetrics.snapshot_date).to_list()
        
        compliance_trends = {
            "last_30_days": [
                {
                    "date": metric.snapshot_date.date().isoformat(),
                    "score": metric.overall_compliance_score
                }
                for metric in recent_metrics
            ]
        }
        
        # Build active findings breakdown (from failed checks and alerts)
        active_findings = {
            "critical": len([e for e in recent_executions if e.result == CheckResult.FAILED and getattr(e, 'severity', 'medium') == 'critical']),
            "high": len([e for e in recent_executions if e.result == CheckResult.FAILED and getattr(e, 'severity', 'medium') == 'high']),
            "medium": len([e for e in recent_executions if e.result == CheckResult.FAILED and getattr(e, 'severity', 'medium') == 'medium']),
            "low": len([e for e in recent_executions if e.result == CheckResult.FAILED and getattr(e, 'severity', 'medium') == 'low'])
        }
        
        # Build remediation progress
        completed_actions = await RemediationAction.find({"status": "completed"}).count()
        overdue_actions = await RemediationAction.find({
            "status": {"$in": ["open", "in_progress"]},
            "due_date": {"$lt": datetime.now()}
        }).count()
        total_actions = await RemediationAction.find().count()
        
        progress_percentage = (completed_actions / total_actions * 100) if total_actions > 0 else 0
        
        remediation_progress = {
            "total_actions": total_actions,
            "completed_actions": completed_actions,
            "overdue_actions": overdue_actions,
            "progress_percentage": round(progress_percentage, 1)
        }
        
        # Build automated monitoring stats
        total_checks = len(recent_executions)
        automated_monitoring = {
            "active_checks": total_checks,
            "passing_checks": passed_checks,
            "failing_checks": failed_checks,
            "last_execution": recent_executions[0].execution_time.isoformat() if recent_executions else datetime.now().isoformat()
        }
        
        # Build framework scores for chart
        framework_scores = []
        for framework in frameworks:
            framework_scores.append({
                "framework": framework.name,
                "score": framework.overall_compliance_score,
                "trend": "stable"  # Could be calculated from historical data
            })
        
        # Build upcoming deadlines (from audit dates and remediation due dates)
        upcoming_deadlines = []
        
        # Add framework assessment deadlines
        for framework in frameworks:
            if framework.next_assessment_date:
                upcoming_deadlines.append({
                    "item": f"{framework.name} Assessment",
                    "due_date": framework.next_assessment_date.isoformat(),
                    "type": "assessment",
                    "priority": "high"
                })
        
        # Add remediation action deadlines
        upcoming_remediation = await RemediationAction.find(
            {"status": {"$in": ["open", "in_progress"]}, "due_date": {"$exists": True}}
        ).sort(RemediationAction.due_date).limit(10).to_list()
        
        for action in upcoming_remediation:
            if action.due_date:
                upcoming_deadlines.append({
                    "item": action.title,
                    "due_date": action.due_date.isoformat(),
                    "type": "remediation",
                    "priority": action.priority.value
                })
        
        # Sort deadlines by due date
        upcoming_deadlines.sort(key=lambda x: x["due_date"])
        upcoming_deadlines = upcoming_deadlines[:10]  # Limit to 10 most urgent
        
        dashboard_data = {
            "overall_compliance_score": round(overall_compliance_score, 1),
            "active_findings": active_findings,
            "remediation_progress": remediation_progress,
            "automated_monitoring": automated_monitoring,
            "framework_scores": framework_scores,
            "upcoming_deadlines": upcoming_deadlines,
            # Keep original fields for backwards compatibility
            "active_frameworks": active_frameworks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "pending_actions": pending_actions,
            "recent_activities": recent_activities,
            "compliance_trends": compliance_trends,
            "framework_breakdown": framework_breakdown
        }
        
        try:
            audit_event = AuditEvent(
                event_type=AuditEventType.DATA_ACCESSED,
                user_id=str(current_user.id),
                user_email=current_user.email,
                severity=AuditSeverity.LOW,
                resource_type="compliance_dashboard",
                resource_id="dashboard_overview",
                action="Accessed compliance dashboard",
                timestamp=datetime.now(timezone.utc)
            )
            audit_logger.log_event(audit_event)
        except Exception as audit_error:
            logger.warning(f"Failed to log audit event: {audit_error}")
        
        return {"success": True, "data": dashboard_data}
        
    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance dashboard"
        )


@router.get("/overview", response_model=Dict[str, Any])
async def get_compliance_overview(
    timeframe: str = "30d",
    current_user: User = Depends(get_current_user)
):
    """Get compliance overview with trends."""
    try:
        # Sample compliance overview data
        overview_data = {
            "compliance_trends": [
                {"date": "2024-01-01", "score": 82.1, "frameworks_assessed": 3},
                {"date": "2024-01-08", "score": 83.5, "frameworks_assessed": 3},
                {"date": "2024-01-15", "score": 85.2, "frameworks_assessed": 3}
            ],
            "risk_trends": [
                {"date": "2024-01-01", "high_risk": 5, "medium_risk": 12, "low_risk": 8},
                {"date": "2024-01-08", "high_risk": 3, "medium_risk": 10, "low_risk": 12},
                {"date": "2024-01-15", "high_risk": 2, "medium_risk": 8, "low_risk": 15}
            ],
            "activity_summary": {
                "automated_checks_run": 1247,
                "manual_assessments_completed": 23,
                "remediation_actions_taken": 18,
                "evidence_collected": 156
            },
            "upcoming_milestones": [
                {
                    "id": "milestone_001",
                    "title": "SOC 2 Annual Assessment",
                    "due_date": "2024-03-15",
                    "framework": "SOC 2 Type II",
                    "priority": "high"
                },
                {
                    "id": "milestone_002",
                    "title": "GDPR Quarterly Review",
                    "due_date": "2024-02-28",
                    "framework": "GDPR",
                    "priority": "medium"
                }
            ]
        }
        
        return {"success": True, "data": overview_data}
        
    except Exception as e:
        logger.error(f"Failed to get compliance overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance overview"
        )


# Framework Management Endpoints

@router.get("/frameworks", response_model=Dict[str, Any])
async def get_compliance_frameworks(
    current_user: User = Depends(get_current_user)
):
    """Get all compliance frameworks."""
    try:
        # Get all frameworks from database
        frameworks_data = await ComplianceFramework.find().to_list()
        
        # Format frameworks for API response
        frameworks = []
        for framework in frameworks_data:
            # Count requirements and controls
            requirements_count = len(framework.requirements)
            controls_implemented = len([c for c in framework.controls if c.implementation_status == "implemented"])
            
            frameworks.append({
                "id": str(framework.id),
                "name": framework.name,
                "version": framework.version,
                "type": framework.framework_type.value,
                "description": framework.description or "",
                "audit_frequency": framework.audit_frequency.value,
                "last_assessment_date": framework.last_assessment_date.isoformat() if framework.last_assessment_date else None,
                "next_assessment_date": framework.next_assessment_date.isoformat() if framework.next_assessment_date else None,
                "overall_compliance_score": framework.overall_compliance_score,
                "status": framework.status.value,
                "requirements_count": requirements_count,
                "controls_implemented": controls_implemented,
                "created_at": framework.created_at.isoformat(),
                "created_by": framework.created_by
            })
        
        return {"success": True, "frameworks": frameworks}
        
    except Exception as e:
        logger.error(f"Failed to get compliance frameworks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance frameworks"
        )


@router.get("/frameworks/{framework_id}", response_model=Dict[str, Any])
async def get_framework_details(
    framework_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific framework."""
    try:
        # Get framework from database
        framework = await ComplianceFramework.get(framework_id)
        if not framework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Framework not found"
            )
        
        # Format detailed requirements
        detailed_requirements = []
        for req in framework.requirements:
            detailed_requirements.append({
                "id": req.requirement_id,
                "title": req.title,
                "category": req.category,
                "status": req.compliance_status.value,
                "priority": req.priority.value,
                "description": req.description,
                "last_assessed": req.last_verified.isoformat() if req.last_verified else None,
                "next_review": req.next_review_date.isoformat() if req.next_review_date else None,
                "responsible_party": req.responsible_party,
                "risk_if_non_compliant": req.risk_if_non_compliant
            })
        
        # Build control hierarchy from controls
        control_hierarchy = {}
        for control in framework.controls:
            category = control.control_type
            if category not in control_hierarchy:
                control_hierarchy[category] = {}
            
            control_id = control.control_id
            if control_id not in control_hierarchy[category]:
                control_hierarchy[category][control_id] = []
            
            control_hierarchy[category][control_id].append(control.name)
        
        # Get assessment history from audits
        audits = await ComplianceAudit.find(
            {"frameworks_in_scope": {"$in": [framework_id]}}
        ).sort(-ComplianceAudit.created_at).to_list()
        
        assessment_history = []
        for audit in audits:
            if audit.status == "completed":
                assessment_history.append({
                    "date": audit.end_date.isoformat() if audit.end_date else audit.created_at.isoformat(),
                    "score": framework.overall_compliance_score,  # Could be historical score from audit
                    "status": audit.overall_rating or "completed",
                    "auditor": audit.auditor_organization or "Internal"
                })
        
        framework_details = {
            "id": str(framework.id),
            "name": framework.name,
            "version": framework.version,
            "type": framework.framework_type.value,
            "description": framework.description or "",
            "audit_frequency": framework.audit_frequency.value,
            "last_assessment_date": framework.last_assessment_date.isoformat() if framework.last_assessment_date else None,
            "next_assessment_date": framework.next_assessment_date.isoformat() if framework.next_assessment_date else None,
            "overall_compliance_score": framework.overall_compliance_score,
            "status": framework.status.value,
            "detailed_requirements": detailed_requirements,
            "control_hierarchy": control_hierarchy,
            "assessment_history": assessment_history,
            "created_at": framework.created_at.isoformat(),
            "updated_at": framework.updated_at.isoformat(),
            "created_by": framework.created_by
        }
        
        return {"success": True, "framework": framework_details}
        
    except Exception as e:
        logger.error(f"Failed to get framework {framework_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve framework details"
        )


@router.post("/frameworks", response_model=Dict[str, Any])
async def add_compliance_framework(
    framework: ComplianceFrameworkRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a new compliance framework."""
    try:
        # Create new framework document
        new_framework = ComplianceFramework(
            name=framework.name,
            version=framework.version,
            framework_type=ComplianceFrameworkType(framework.type),
            description=framework.description or "",
            audit_frequency=AuditFrequency.ANNUAL,  # Default to annual
            overall_compliance_score=0.0,
            status=ComplianceStatus.ASSESSMENT_NEEDED,
            created_by=str(current_user.id)
        )
        
        # Save to database
        await new_framework.insert()
        
        audit_event = AuditEvent(
            event_type=AuditEventType.ASSESSMENT_CREATED,
            user_id=str(current_user.id),
            user_email=current_user.email,
            severity=AuditSeverity.MEDIUM,
            resource_type="compliance_framework",
            resource_id=str(new_framework.id),
            action=f"Added compliance framework: {framework.name}",
            timestamp=datetime.now(timezone.utc)
        )
        audit_logger.log_event(audit_event)
        
        # Format response
        framework_data = {
            "id": str(new_framework.id),
            "name": new_framework.name,
            "version": new_framework.version,
            "type": new_framework.framework_type.value,
            "description": new_framework.description or "",
            "audit_frequency": new_framework.audit_frequency.value,
            "overall_compliance_score": new_framework.overall_compliance_score,
            "status": new_framework.status.value,
            "created_at": new_framework.created_at.isoformat(),
            "created_by": new_framework.created_by
        }
        
        return {"success": True, "framework": framework_data}
        
    except Exception as e:
        logger.error(f"Failed to add compliance framework: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add compliance framework"
        )


# Automated Checks Endpoints

@router.get("/automated-checks", response_model=Dict[str, Any])
async def get_automated_checks(
    framework_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get automated compliance checks."""
    try:
        # Build query
        query = {}
        if framework_id:
            query["framework_id"] = framework_id
            
        # Get automated checks from database
        checks_data = await AutomatedCheck.find(query).to_list()
        
        # Format checks for API response
        checks = []
        for check in checks_data:
            checks.append({
                "id": str(check.id),
                "framework_id": check.framework_id,
                "requirement_id": check.requirement_id,
                "check_name": check.check_name,
                "check_type": check.check_type,
                "description": check.description,
                "frequency": check.frequency,
                "last_run": check.last_run.isoformat() if check.last_run else None,
                "next_run": check.next_run.isoformat() if check.next_run else None,
                "status": check.status.value,
                "last_result": check.last_result.value if check.last_result else None,
                "data_sources": check.data_sources,
                "created_at": check.created_at.isoformat(),
                "created_by": check.created_by
            })
            
        return {"success": True, "checks": checks}
        
    except Exception as e:
        logger.error(f"Failed to get automated checks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve automated checks"
        )


@router.post("/automated-checks", response_model=Dict[str, Any])
async def create_automated_check(
    check: AutomatedCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new automated compliance check."""
    try:
        # Verify framework exists
        framework = await ComplianceFramework.get(check.framework_id)
        if not framework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Framework not found"
            )
        
        # Create new automated check document
        new_check = AutomatedCheck(
            framework_id=check.framework_id,
            requirement_id=check.requirement_id,
            check_name=check.check_name,
            check_type=check.check_type,
            check_logic=check.check_logic,
            frequency=check.frequency,
            data_sources=check.data_sources,
            status=CheckStatus.ACTIVE,
            created_by=str(current_user.id)
        )
        
        # Save to database
        await new_check.insert()
        
        audit_event = AuditEvent(
            event_type=AuditEventType.ASSESSMENT_CREATED,
            user_id=str(current_user.id),
            user_email=current_user.email,
            severity=AuditSeverity.MEDIUM,
            resource_type="automated_check",
            resource_id=str(new_check.id),
            action=f"Created automated check: {check.check_name}",
            timestamp=datetime.now(timezone.utc)
        )
        audit_logger.log_event(audit_event)
        
        # Format response
        check_data = {
            "id": str(new_check.id),
            "framework_id": new_check.framework_id,
            "requirement_id": new_check.requirement_id,
            "check_name": new_check.check_name,
            "check_type": new_check.check_type,
            "frequency": new_check.frequency,
            "data_sources": new_check.data_sources,
            "status": new_check.status.value,
            "created_at": new_check.created_at.isoformat(),
            "created_by": new_check.created_by,
            "last_run": None,
            "next_run": None
        }
        
        return {"success": True, "check": check_data}
        
    except Exception as e:
        logger.error(f"Failed to create automated check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create automated check"
        )


# Additional endpoints for compliance automation

@router.get("/evidence/requirements", response_model=Dict[str, Any])
async def get_evidence_requirements(
    framework_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get evidence requirements for compliance frameworks."""
    try:
        # Build query
        query = {}
        if framework_id:
            query["framework_id"] = framework_id
            
        # Get evidence requirements from database
        requirements_data = await EvidenceRequirement.find(query).to_list()
        
        # Format requirements for API response
        requirements = []
        for req in requirements_data:
            requirements.append({
                "id": str(req.id),
                "framework_id": req.framework_id,
                "requirement_id": req.requirement_id,
                "evidence_type": req.evidence_type,
                "title": req.title,
                "description": req.description,
                "collection_method": req.collection_method,
                "frequency": req.frequency,
                "retention_period": req.retention_period,
                "current_status": req.current_status,
                "last_collected": req.last_collected.isoformat() if req.last_collected else None,
                "next_collection": req.next_collection.isoformat() if req.next_collection else None,
                "access_controls": req.access_controls,
                "created_at": req.created_at.isoformat()
            })
            
        return {"success": True, "requirements": requirements}
        
    except Exception as e:
        logger.error(f"Failed to get evidence requirements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evidence requirements"
        )


@router.get("/controls", response_model=Dict[str, Any])
async def get_compliance_controls(
    framework_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get compliance controls."""
    try:
        # Get frameworks and their controls
        if framework_id:
            framework = await ComplianceFramework.get(framework_id)
            if not framework:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Framework not found"
                )
            frameworks = [framework]
        else:
            frameworks = await ComplianceFramework.find().to_list()
        
        # Collect all controls from frameworks
        controls = []
        for framework in frameworks:
            for control in framework.controls:
                controls.append({
                    "id": control.control_id,
                    "framework_id": str(framework.id),
                    "name": control.name,
                    "description": control.description,
                    "control_type": control.control_type,
                    "implementation_status": control.implementation_status,
                    "effectiveness": control.effectiveness,
                    "owner": control.owner,
                    "test_frequency": control.test_frequency,
                    "last_tested": control.last_tested.isoformat() if control.last_tested else None
                })
        
        return {"success": True, "controls": controls}
        
    except Exception as e:
        logger.error(f"Failed to get compliance controls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance controls"
        )


@router.get("/remediation/actions", response_model=Dict[str, Any])
async def get_remediation_actions(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get remediation actions."""
    try:
        # Build query
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = Priority(priority)
            
        # Get remediation actions from database
        actions_data = await RemediationAction.find(query).to_list()
        
        # Format actions for API response
        actions = []
        for action in actions_data:
            actions.append({
                "id": str(action.id),
                "framework_id": action.framework_id,
                "requirement_id": action.requirement_id,
                "title": action.title,
                "description": action.description,
                "category": action.category,
                "priority": action.priority.value,
                "status": action.status,
                "assigned_to": action.assigned_to,
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "completion_date": action.completion_date.isoformat() if action.completion_date else None,
                "implementation_steps": action.implementation_steps,
                "success_criteria": action.success_criteria,
                "blockers": action.blockers,
                "created_at": action.created_at.isoformat(),
                "updated_at": action.updated_at.isoformat(),
                "created_by": action.created_by
            })
            
        return {"success": True, "actions": actions}
        
    except Exception as e:
        logger.error(f"Failed to get remediation actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve remediation actions"
        )


@router.get("/audits", response_model=Dict[str, Any])
async def get_compliance_audits(
    current_user: User = Depends(get_current_user)
):
    """Get compliance audits."""
    try:
        # Get audits from database
        audits_data = await ComplianceAudit.find().sort(-ComplianceAudit.created_at).to_list()
        
        # Format audits for API response
        audits = []
        for audit in audits_data:
            audits.append({
                "id": str(audit.id),
                "audit_name": audit.audit_name,
                "audit_type": audit.audit_type,
                "frameworks_in_scope": audit.frameworks_in_scope,
                "auditor_name": audit.auditor_name,
                "auditor_organization": audit.auditor_organization,
                "start_date": audit.start_date.isoformat() if audit.start_date else None,
                "end_date": audit.end_date.isoformat() if audit.end_date else None,
                "report_due_date": audit.report_due_date.isoformat() if audit.report_due_date else None,
                "status": audit.status,
                "overall_rating": audit.overall_rating,
                "scope_description": audit.scope_description,
                "findings_count": len(audit.findings),
                "recommendations_count": len(audit.recommendations),
                "created_at": audit.created_at.isoformat(),
                "updated_at": audit.updated_at.isoformat(),
                "created_by": audit.created_by
            })
            
        return {"success": True, "audits": audits}
        
    except Exception as e:
        logger.error(f"Failed to get compliance audits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance audits"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_compliance_alerts(
    current_user: User = Depends(get_current_user)
):
    """Get compliance alerts."""
    try:
        # Get alerts from database
        alerts_data = await ComplianceAlert.find().sort(-ComplianceAlert.created_at).limit(100).to_list()
        
        # Format alerts for API response
        alerts = []
        for alert in alerts_data:
            alerts.append({
                "id": str(alert.id),
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "framework_id": alert.framework_id,
                "affected_items": alert.affected_items,
                "status": alert.status,
                "action_required": alert.action_required,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "acknowledgment_notes": alert.acknowledgment_notes,
                "created_at": alert.created_at.isoformat()
            })
            
        return {"success": True, "alerts": alerts}
        
    except Exception as e:
        logger.error(f"Failed to get compliance alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance alerts"
        )