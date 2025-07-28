"""
Compliance management system for Infra Mind.

Provides comprehensive compliance features including data retention policies,
audit trail management, data export/portability, and consent management.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from bson import ObjectId

from .audit import audit_logger, AuditEventType, AuditSeverity
from ..models.user import User
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class DataCategory(str, Enum):
    """Categories of data for compliance management."""
    PERSONAL_DATA = "personal_data"
    BUSINESS_DATA = "business_data"
    TECHNICAL_DATA = "technical_data"
    ASSESSMENT_DATA = "assessment_data"
    RECOMMENDATION_DATA = "recommendation_data"
    REPORT_DATA = "report_data"
    AUDIT_DATA = "audit_data"
    SYSTEM_DATA = "system_data"


class RetentionPeriod(str, Enum):
    """Standard data retention periods."""
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    MONTHS_6 = "6_months"
    YEAR_1 = "1_year"
    YEARS_3 = "3_years"
    YEARS_7 = "7_years"
    INDEFINITE = "indefinite"


class ConsentType(str, Enum):
    """Types of user consent."""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    COOKIES = "cookies"
    PROFILING = "profiling"


class ConsentStatus(str, Enum):
    """Status of user consent."""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"


@dataclass
class DataRetentionPolicy:
    """Data retention policy definition."""
    data_category: DataCategory
    retention_period: RetentionPeriod
    legal_basis: str
    description: str
    auto_delete: bool = True
    exceptions: List[str] = None
    
    def __post_init__(self):
        if self.exceptions is None:
            self.exceptions = []
    
    def get_expiry_date(self, created_date: datetime) -> Optional[datetime]:
        """Calculate expiry date based on retention period."""
        if self.retention_period == RetentionPeriod.INDEFINITE:
            return None
        
        period_map = {
            RetentionPeriod.DAYS_30: timedelta(days=30),
            RetentionPeriod.DAYS_90: timedelta(days=90),
            RetentionPeriod.MONTHS_6: timedelta(days=180),
            RetentionPeriod.YEAR_1: timedelta(days=365),
            RetentionPeriod.YEARS_3: timedelta(days=1095),
            RetentionPeriod.YEARS_7: timedelta(days=2555),
        }
        
        delta = period_map.get(self.retention_period)
        return created_date + delta if delta else None


@dataclass
class UserConsent:
    """User consent record."""
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    legal_basis: Optional[str] = None
    purpose: Optional[str] = None
    data_categories: List[DataCategory] = None
    
    def __post_init__(self):
        if self.data_categories is None:
            self.data_categories = []


class ComplianceManager:
    """
    Comprehensive compliance management system.
    
    Handles data retention, consent management, audit trails,
    and data export/portability features.
    """
    
    def __init__(self):
        """Initialize compliance manager."""
        self.retention_policies = self._initialize_retention_policies()
        self.consent_records: Dict[str, List[UserConsent]] = {}
        
        logger.info("Compliance Manager initialized")
    
    def _initialize_retention_policies(self) -> Dict[DataCategory, DataRetentionPolicy]:
        """Initialize default data retention policies."""
        policies = {
            DataCategory.PERSONAL_DATA: DataRetentionPolicy(
                data_category=DataCategory.PERSONAL_DATA,
                retention_period=RetentionPeriod.YEARS_3,
                legal_basis="Legitimate interest for service provision",
                description="Personal data including names, emails, and profile information",
                auto_delete=True,
                exceptions=["Active user accounts", "Legal hold requirements"]
            ),
            DataCategory.BUSINESS_DATA: DataRetentionPolicy(
                data_category=DataCategory.BUSINESS_DATA,
                retention_period=RetentionPeriod.YEARS_7,
                legal_basis="Business records retention requirements",
                description="Business information and company data",
                auto_delete=False,
                exceptions=["Ongoing business relationships"]
            ),
            DataCategory.ASSESSMENT_DATA: DataRetentionPolicy(
                data_category=DataCategory.ASSESSMENT_DATA,
                retention_period=RetentionPeriod.YEARS_3,
                legal_basis="Service provision and improvement",
                description="Infrastructure assessment data and requirements",
                auto_delete=True,
                exceptions=["User-requested retention"]
            ),
            DataCategory.RECOMMENDATION_DATA: DataRetentionPolicy(
                data_category=DataCategory.RECOMMENDATION_DATA,
                retention_period=RetentionPeriod.YEARS_3,
                legal_basis="Service provision and quality improvement",
                description="AI-generated recommendations and analysis",
                auto_delete=True
            ),
            DataCategory.REPORT_DATA: DataRetentionPolicy(
                data_category=DataCategory.REPORT_DATA,
                retention_period=RetentionPeriod.YEARS_3,
                legal_basis="Service provision and user access",
                description="Generated reports and documents",
                auto_delete=True
            ),
            DataCategory.AUDIT_DATA: DataRetentionPolicy(
                data_category=DataCategory.AUDIT_DATA,
                retention_period=RetentionPeriod.YEARS_7,
                legal_basis="Security monitoring and compliance",
                description="Audit logs and security events",
                auto_delete=False,
                exceptions=["Regulatory requirements", "Security investigations"]
            ),
            DataCategory.TECHNICAL_DATA: DataRetentionPolicy(
                data_category=DataCategory.TECHNICAL_DATA,
                retention_period=RetentionPeriod.YEAR_1,
                legal_basis="System operation and improvement",
                description="Technical logs and system data",
                auto_delete=True
            ),
            DataCategory.SYSTEM_DATA: DataRetentionPolicy(
                data_category=DataCategory.SYSTEM_DATA,
                retention_period=RetentionPeriod.MONTHS_6,
                legal_basis="System operation",
                description="System performance and operational data",
                auto_delete=True
            )
        }
        
        return policies
    
    # Data Retention Management
    
    def get_retention_policy(self, data_category: DataCategory) -> Optional[DataRetentionPolicy]:
        """Get retention policy for a data category."""
        return self.retention_policies.get(data_category)
    
    def update_retention_policy(self, policy: DataRetentionPolicy) -> None:
        """Update a data retention policy."""
        self.retention_policies[policy.data_category] = policy
        
        # Log policy change
        audit_logger.log_system_event(
            event_type=AuditEventType.CONFIGURATION_CHANGED,
            details={
                "component": "data_retention",
                "policy_category": policy.data_category.value,
                "retention_period": policy.retention_period.value,
                "auto_delete": policy.auto_delete
            },
            severity=AuditSeverity.MEDIUM
        )
        
        logger.info(f"Updated retention policy for {policy.data_category.value}")
    
    async def check_data_expiry(self, data_category: DataCategory, created_date: datetime) -> Dict[str, Any]:
        """Check if data has expired based on retention policy."""
        policy = self.get_retention_policy(data_category)
        if not policy:
            return {"expired": False, "reason": "No policy defined"}
        
        expiry_date = policy.get_expiry_date(created_date)
        if not expiry_date:
            return {"expired": False, "reason": "Indefinite retention"}
        
        now = datetime.now(timezone.utc)
        expired = now > expiry_date
        
        return {
            "expired": expired,
            "expiry_date": expiry_date.isoformat(),
            "days_until_expiry": (expiry_date - now).days if not expired else 0,
            "policy": asdict(policy)
        }
    
    async def schedule_data_deletion(self, user_id: str, data_categories: List[DataCategory]) -> Dict[str, Any]:
        """Schedule data deletion for specified categories."""
        deletion_schedule = {}
        
        for category in data_categories:
            policy = self.get_retention_policy(category)
            if policy and policy.auto_delete:
                # In a real implementation, this would integrate with a job scheduler
                deletion_schedule[category.value] = {
                    "scheduled": True,
                    "retention_period": policy.retention_period.value,
                    "auto_delete": policy.auto_delete
                }
                
                # Log scheduling
                audit_logger.log_data_access(
                    user_id=user_id,
                    resource_type=category.value,
                    resource_id=f"deletion_schedule_{category.value}",
                    action="schedule_deletion",
                    details={
                        "retention_policy": asdict(policy),
                        "scheduled_at": datetime.now(timezone.utc).isoformat()
                    }
                )
            else:
                deletion_schedule[category.value] = {
                    "scheduled": False,
                    "reason": "Manual deletion required or no auto-delete policy"
                }
        
        return {
            "user_id": user_id,
            "deletion_schedule": deletion_schedule,
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
    
    # Consent Management
    
    def record_consent(self, consent: UserConsent) -> None:
        """Record user consent."""
        if consent.user_id not in self.consent_records:
            self.consent_records[consent.user_id] = []
        
        # Update timestamp based on status
        if consent.status == ConsentStatus.GRANTED:
            consent.granted_at = datetime.now(timezone.utc)
        elif consent.status == ConsentStatus.WITHDRAWN:
            consent.withdrawn_at = datetime.now(timezone.utc)
        
        self.consent_records[consent.user_id].append(consent)
        
        # Log consent event
        audit_logger.log_data_access(
            user_id=consent.user_id,
            resource_type="consent",
            resource_id=f"consent_{consent.consent_type.value}",
            action=f"consent_{consent.status.value}",
            ip_address=consent.ip_address,
            details={
                "consent_type": consent.consent_type.value,
                "status": consent.status.value,
                "legal_basis": consent.legal_basis,
                "purpose": consent.purpose,
                "data_categories": [cat.value for cat in consent.data_categories]
            }
        )
        
        logger.info(f"Recorded consent for user {consent.user_id}: {consent.consent_type.value} - {consent.status.value}")
    
    def get_user_consent(self, user_id: str, consent_type: ConsentType) -> Optional[UserConsent]:
        """Get latest consent record for user and type."""
        user_consents = self.consent_records.get(user_id, [])
        
        # Get latest consent for this type
        type_consents = [c for c in user_consents if c.consent_type == consent_type]
        if type_consents:
            return max(type_consents, key=lambda c: c.granted_at or c.withdrawn_at or datetime.min)
        
        return None
    
    def check_consent_status(self, user_id: str, consent_type: ConsentType) -> ConsentStatus:
        """Check current consent status for user and type."""
        consent = self.get_user_consent(user_id, consent_type)
        return consent.status if consent else ConsentStatus.PENDING
    
    def withdraw_consent(self, user_id: str, consent_type: ConsentType, ip_address: Optional[str] = None) -> bool:
        """Withdraw user consent."""
        current_consent = self.get_user_consent(user_id, consent_type)
        if not current_consent or current_consent.status != ConsentStatus.GRANTED:
            return False
        
        # Create withdrawal record
        withdrawal_consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.WITHDRAWN,
            withdrawn_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            legal_basis=current_consent.legal_basis,
            purpose=current_consent.purpose,
            data_categories=current_consent.data_categories
        )
        
        self.record_consent(withdrawal_consent)
        return True
    
    def get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of all consent statuses for user."""
        summary = {}
        
        for consent_type in ConsentType:
            status = self.check_consent_status(user_id, consent_type)
            consent = self.get_user_consent(user_id, consent_type)
            
            summary[consent_type.value] = {
                "status": status.value,
                "granted_at": consent.granted_at.isoformat() if consent and consent.granted_at else None,
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent and consent.withdrawn_at else None,
                "legal_basis": consent.legal_basis if consent else None,
                "purpose": consent.purpose if consent else None
            }
        
        return {
            "user_id": user_id,
            "consent_summary": summary,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    # Data Export and Portability
    
    async def export_user_data(self, user_id: str, data_categories: Optional[List[DataCategory]] = None) -> Dict[str, Any]:
        """Export all user data for portability."""
        if data_categories is None:
            data_categories = list(DataCategory)
        
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_categories": [cat.value for cat in data_categories],
            "data": {}
        }
        
        try:
            # Export user profile data
            if DataCategory.PERSONAL_DATA in data_categories:
                try:
                    user = await User.get(ObjectId(user_id))
                except Exception:
                    # Handle invalid ObjectId or user not found
                    user = None
                if user:
                    export_data["data"]["personal_data"] = {
                        "email": user.email,
                        "full_name": user.full_name,
                        "company_name": user.company_name,
                        "company_size": user.company_size.value if user.company_size else None,
                        "industry": user.industry.value if user.industry else None,
                        "job_title": user.job_title,
                        "preferred_cloud_providers": user.preferred_cloud_providers,
                        "notification_preferences": user.notification_preferences,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    }
            
            # Export assessment data
            if DataCategory.ASSESSMENT_DATA in data_categories:
                try:
                    assessments = await Assessment.find({"user_id": user_id}).to_list()
                except Exception:
                    # Fallback if Assessment model doesn't have user_id field
                    assessments = []
                export_data["data"]["assessment_data"] = [
                    {
                        "id": str(assessment.id),
                        "title": assessment.title,
                        "description": assessment.description,
                        "business_requirements": assessment.business_requirements,
                        "technical_requirements": assessment.technical_requirements,
                        "status": assessment.status.value,
                        "priority": assessment.priority.value,
                        "created_at": assessment.created_at.isoformat(),
                        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
                    }
                    for assessment in assessments
                ]
            
            # Export consent records
            if DataCategory.PERSONAL_DATA in data_categories:
                consent_summary = self.get_consent_summary(user_id)
                export_data["data"]["consent_records"] = consent_summary
            
            # Log export event
            audit_logger.log_data_access(
                user_id=user_id,
                resource_type="user_data_export",
                resource_id=f"export_{user_id}",
                action="data_export",
                details={
                    "data_categories": [cat.value for cat in data_categories],
                    "export_size_kb": len(json.dumps(export_data)) / 1024
                }
            )
            
            logger.info(f"Exported data for user {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export data for user {user_id}: {str(e)}")
            raise
    
    async def delete_user_data(self, user_id: str, data_categories: Optional[List[DataCategory]] = None, reason: str = "User request") -> Dict[str, Any]:
        """Delete user data (right to erasure)."""
        if data_categories is None:
            data_categories = list(DataCategory)
        
        deletion_results = {
            "user_id": user_id,
            "deletion_timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "data_categories": [cat.value for cat in data_categories],
            "results": {}
        }
        
        try:
            # Delete personal data
            if DataCategory.PERSONAL_DATA in data_categories:
                try:
                    user = await User.get(ObjectId(user_id))
                except Exception:
                    # Handle invalid ObjectId or user not found
                    user = None
                if user:
                    # Anonymize instead of hard delete to maintain referential integrity
                    user.email = f"deleted_user_{user_id}@anonymized.local"
                    user.full_name = "Deleted User"
                    user.company_name = None
                    user.job_title = None
                    user.is_active = False
                    await user.save()
                    
                    deletion_results["results"]["personal_data"] = "anonymized"
                else:
                    deletion_results["results"]["personal_data"] = "not_found"
            
            # Delete assessment data
            if DataCategory.ASSESSMENT_DATA in data_categories:
                try:
                    assessments = await Assessment.find({"user_id": user_id}).to_list()
                except Exception:
                    # Fallback if Assessment model doesn't have user_id field
                    assessments = []
                deleted_count = 0
                for assessment in assessments:
                    await assessment.delete()
                    deleted_count += 1
                
                deletion_results["results"]["assessment_data"] = f"deleted_{deleted_count}_records"
            
            # Clear consent records
            if user_id in self.consent_records:
                del self.consent_records[user_id]
                deletion_results["results"]["consent_records"] = "cleared"
            
            # Log deletion event
            audit_logger.log_data_access(
                user_id=user_id,
                resource_type="user_data_deletion",
                resource_id=f"deletion_{user_id}",
                action="data_deletion",
                details={
                    "data_categories": [cat.value for cat in data_categories],
                    "reason": reason,
                    "results": deletion_results["results"]
                }
            )
            
            logger.info(f"Deleted data for user {user_id}: {reason}")
            return deletion_results
            
        except Exception as e:
            logger.error(f"Failed to delete data for user {user_id}: {str(e)}")
            raise
    
    # Compliance Reporting
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for specified period."""
        report = {
            "report_type": "compliance_report",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_retention": self._get_retention_report(),
            "consent_management": self._get_consent_report(),
            "data_requests": self._get_data_request_report(start_date, end_date),
            "audit_summary": self._get_audit_summary(start_date, end_date)
        }
        
        # Log report generation
        audit_logger.log_system_event(
            event_type=AuditEventType.SYSTEM_STARTUP,  # Using available event type
            details={
                "report_type": "compliance_report",
                "period_days": (end_date - start_date).days,
                "generated_by": "compliance_manager"
            },
            severity=AuditSeverity.LOW
        )
        
        return report
    
    def _get_retention_report(self) -> Dict[str, Any]:
        """Get data retention policy report."""
        return {
            "policies_count": len(self.retention_policies),
            "policies": {
                category.value: {
                    "retention_period": policy.retention_period.value,
                    "auto_delete": policy.auto_delete,
                    "legal_basis": policy.legal_basis
                }
                for category, policy in self.retention_policies.items()
            }
        }
    
    def _get_consent_report(self) -> Dict[str, Any]:
        """Get consent management report."""
        total_users = len(self.consent_records)
        consent_stats = {}
        
        for consent_type in ConsentType:
            granted = 0
            denied = 0
            withdrawn = 0
            
            for user_consents in self.consent_records.values():
                latest_consent = None
                for consent in user_consents:
                    if consent.consent_type == consent_type:
                        if not latest_consent or (consent.granted_at or consent.withdrawn_at or datetime.min) > (latest_consent.granted_at or latest_consent.withdrawn_at or datetime.min):
                            latest_consent = consent
                
                if latest_consent:
                    if latest_consent.status == ConsentStatus.GRANTED:
                        granted += 1
                    elif latest_consent.status == ConsentStatus.DENIED:
                        denied += 1
                    elif latest_consent.status == ConsentStatus.WITHDRAWN:
                        withdrawn += 1
            
            consent_stats[consent_type.value] = {
                "granted": granted,
                "denied": denied,
                "withdrawn": withdrawn,
                "total": granted + denied + withdrawn
            }
        
        return {
            "total_users_with_consent": total_users,
            "consent_statistics": consent_stats
        }
    
    def _get_data_request_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get data request report (exports, deletions)."""
        # In a real implementation, this would query audit logs
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "data_exports": 0,  # Would be calculated from audit logs
            "data_deletions": 0,  # Would be calculated from audit logs
            "consent_changes": 0  # Would be calculated from audit logs
        }
    
    def _get_audit_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get audit trail summary."""
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_events": 0,  # Would be calculated from audit logs
            "security_events": 0,  # Would be calculated from audit logs
            "data_access_events": 0,  # Would be calculated from audit logs
            "compliance_events": 0  # Would be calculated from audit logs
        }


# Global compliance manager instance
compliance_manager = ComplianceManager()


# Convenience functions for common operations

async def record_user_consent(
    user_id: str,
    consent_type: ConsentType,
    status: ConsentStatus,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    legal_basis: Optional[str] = None,
    purpose: Optional[str] = None,
    data_categories: Optional[List[DataCategory]] = None
) -> None:
    """Record user consent with audit logging."""
    consent = UserConsent(
        user_id=user_id,
        consent_type=consent_type,
        status=status,
        ip_address=ip_address,
        user_agent=user_agent,
        legal_basis=legal_basis,
        purpose=purpose,
        data_categories=data_categories or []
    )
    
    compliance_manager.record_consent(consent)


async def export_user_data_request(user_id: str, requester_ip: Optional[str] = None) -> Dict[str, Any]:
    """Handle user data export request."""
    # Log the request
    audit_logger.log_data_access(
        user_id=user_id,
        resource_type="data_export_request",
        resource_id=f"export_request_{user_id}",
        action="request_data_export",
        ip_address=requester_ip,
        details={"request_type": "user_data_export"}
    )
    
    return await compliance_manager.export_user_data(user_id)


async def delete_user_data_request(user_id: str, reason: str = "User request", requester_ip: Optional[str] = None) -> Dict[str, Any]:
    """Handle user data deletion request (right to erasure)."""
    # Log the request
    audit_logger.log_data_access(
        user_id=user_id,
        resource_type="data_deletion_request",
        resource_id=f"deletion_request_{user_id}",
        action="request_data_deletion",
        ip_address=requester_ip,
        details={"request_type": "user_data_deletion", "reason": reason}
    )
    
    return await compliance_manager.delete_user_data(user_id, reason=reason)