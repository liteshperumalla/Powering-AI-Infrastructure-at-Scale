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
from ...core.audit import audit_logger, AuditEventType, AuditSeverity

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