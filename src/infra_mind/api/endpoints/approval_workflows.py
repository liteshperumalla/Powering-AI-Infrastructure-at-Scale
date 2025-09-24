"""
Approval Workflows endpoints for Infra Mind.

Handles approval processes, workflow management, request routing, and governance automation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from enum import Enum

router = APIRouter()
security = HTTPBearer()

# Data Models
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RequestType(str, Enum):
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    ACCESS = "access"
    BUDGET = "budget"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_type: RequestType = RequestType.DEPLOYMENT
    title: str
    description: str = ""
    requester: str
    priority: Priority = Priority.MEDIUM
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    approved_by: List[str] = []
    rejected_by: List[str] = []
    required_approvers: List[str] = []
    approval_count: int = 0
    rejection_count: int = 0
    comments: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    workflow_id: Optional[str] = None

class ApprovalRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str
    request_type: RequestType = RequestType.DEPLOYMENT
    conditions: List[Dict[str, Any]] = []
    required_approvers: List[str] = []
    minimum_approvals: int = 1
    auto_approve_conditions: List[Dict[str, Any]] = []
    escalation_rules: List[Dict[str, Any]] = []
    timeout_hours: int = 24
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class WorkflowTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    description: str = ""
    request_types: List[RequestType] = []
    steps: List[Dict[str, Any]] = []
    parallel_approval: bool = False
    auto_escalation: bool = True
    sla_hours: int = 24
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# Endpoints

@router.get("/requests")
async def get_approval_requests(
    status: Optional[ApprovalStatus] = None,
    request_type: Optional[RequestType] = None,
    priority: Optional[Priority] = None,
    requester: Optional[str] = None,
    limit: int = 50
) -> List[ApprovalRequest]:
    """Get approval requests with optional filters."""
    logger.info(f"Fetching approval requests with filters: status={status}, type={request_type}")
    
    # Sample data for demonstration
    requests = [
        ApprovalRequest(
            request_type=RequestType.DEPLOYMENT,
            title="Production Deployment - User Service v2.1.0",
            description="Deploy new user service version with authentication improvements",
            requester="dev-team@company.com",
            priority=Priority.HIGH,
            status=ApprovalStatus.PENDING,
            due_date=(datetime.now() + timedelta(hours=4)).isoformat(),
            required_approvers=["ops-manager@company.com", "security-lead@company.com"],
            approval_count=1,
            approved_by=["ops-manager@company.com"],
            comments=[
                {
                    "author": "ops-manager@company.com",
                    "message": "Looks good from ops perspective. Security review needed.",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
                }
            ],
            metadata={
                "service": "user-service",
                "version": "v2.1.0",
                "environment": "production",
                "impact_level": "medium"
            }
        ),
        ApprovalRequest(
            request_type=RequestType.BUDGET,
            title="Additional Cloud Resources - Q1 2024",
            description="Request for $50K additional budget for scaling infrastructure",
            requester="infrastructure@company.com",
            priority=Priority.MEDIUM,
            status=ApprovalStatus.APPROVED,
            approved_by=["finance-director@company.com", "cto@company.com"],
            approval_count=2,
            comments=[
                {
                    "author": "finance-director@company.com",
                    "message": "Approved. Budget available in Q1 allocation.",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
                }
            ],
            metadata={
                "amount": 50000,
                "category": "infrastructure",
                "quarter": "Q1_2024"
            }
        ),
        ApprovalRequest(
            request_type=RequestType.EMERGENCY,
            title="Emergency Security Patch Deployment",
            description="Critical security vulnerability fix deployment",
            requester="security@company.com",
            priority=Priority.CRITICAL,
            status=ApprovalStatus.APPROVED,
            approved_by=["security-lead@company.com", "ops-director@company.com"],
            approval_count=2,
            metadata={
                "vulnerability": "CVE-2024-12345",
                "severity": "critical",
                "affected_services": ["api-gateway", "auth-service"]
            }
        ),
        ApprovalRequest(
            request_type=RequestType.ACCESS,
            title="Database Access Request - Analytics Team",
            description="Read-only access to production analytics database",
            requester="analytics@company.com",
            priority=Priority.LOW,
            status=ApprovalStatus.PENDING,
            required_approvers=["data-security@company.com", "dba@company.com"],
            due_date=(datetime.now() + timedelta(days=2)).isoformat(),
            metadata={
                "database": "analytics_prod",
                "access_level": "read_only",
                "duration": "6_months"
            }
        )
    ]
    
    # Apply filters
    if status:
        requests = [r for r in requests if r.status == status]
    if request_type:
        requests = [r for r in requests if r.request_type == request_type]
    if priority:
        requests = [r for r in requests if r.priority == priority]
    if requester:
        requests = [r for r in requests if requester.lower() in r.requester.lower()]
    
    return requests[:limit]

@router.post("/requests")
async def create_approval_request(request_data: Dict[str, Any]) -> ApprovalRequest:
    """Create a new approval request."""
    logger.info(f"Creating approval request: {request_data.get('title')}")
    
    request = ApprovalRequest(
        request_type=RequestType(request_data.get("request_type", "deployment")),
        title=request_data.get("title", "New Request"),
        description=request_data.get("description"),
        requester=request_data.get("requester", "unknown@company.com"),
        priority=Priority(request_data.get("priority", "medium")),
        required_approvers=request_data.get("required_approvers", []),
        due_date=request_data.get("due_date"),
        metadata=request_data.get("metadata", {})
    )
    
    logger.success(f"Created approval request with ID: {request.id}")
    return request

@router.get("/requests/{request_id}")
async def get_approval_request_details(request_id: str) -> ApprovalRequest:
    """Get detailed information about a specific approval request."""
    logger.info(f"Fetching approval request details for ID: {request_id}")
    
    return ApprovalRequest(
        id=request_id,
        request_type=RequestType.DEPLOYMENT,
        title="Production Deployment - User Service v2.1.0",
        description="Deploy new user service version with authentication improvements and security patches",
        requester="dev-team@company.com",
        priority=Priority.HIGH,
        status=ApprovalStatus.PENDING,
        due_date=(datetime.now() + timedelta(hours=4)).isoformat(),
        required_approvers=["ops-manager@company.com", "security-lead@company.com"],
        approval_count=1,
        approved_by=["ops-manager@company.com"],
        comments=[
            {
                "id": str(uuid.uuid4()),
                "author": "ops-manager@company.com",
                "author_name": "Operations Manager",
                "message": "Looks good from ops perspective. All infrastructure checks passed. Security review needed before final approval.",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "type": "approval"
            },
            {
                "id": str(uuid.uuid4()),
                "author": "dev-team@company.com",
                "author_name": "Development Team",
                "message": "Added comprehensive test results and deployment plan documentation.",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "comment"
            }
        ],
        metadata={
            "service": "user-service",
            "version": "v2.1.0",
            "environment": "production",
            "impact_level": "medium",
            "deployment_method": "blue_green",
            "rollback_plan": "automated",
            "test_coverage": "95%",
            "performance_impact": "minimal"
        }
    )

@router.post("/requests/{request_id}/approve")
async def approve_request(request_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
    """Approve an approval request."""
    logger.info(f"Approving request: {request_id}")
    
    approver = approval_data.get("approver", "unknown@company.com")
    comment = approval_data.get("comment")
    
    return {
        "request_id": request_id,
        "status": "approved",
        "approver": approver,
        "approved_at": datetime.now().isoformat(),
        "comment": comment,
        "next_actions": [
            "Request approved by " + approver,
            "Waiting for additional approvers" if approval_data.get("requires_more", True) else "Ready for execution"
        ]
    }

@router.post("/requests/{request_id}/reject")
async def reject_request(request_id: str, rejection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Reject an approval request."""
    logger.info(f"Rejecting request: {request_id}")
    
    rejector = rejection_data.get("rejector", "unknown@company.com")
    reason = rejection_data.get("reason")
    
    return {
        "request_id": request_id,
        "status": "rejected",
        "rejected_by": rejector,
        "rejected_at": datetime.now().isoformat(),
        "reason": reason,
        "next_actions": [
            "Request rejected",
            "Requester notified",
            "Review and resubmit if needed"
        ]
    }

@router.get("/rules")
async def get_approval_rules(
    request_type: Optional[RequestType] = None,
    enabled: Optional[bool] = None
) -> List[ApprovalRule]:
    """Get approval rules with optional filters."""
    logger.info(f"Fetching approval rules with filters: type={request_type}, enabled={enabled}")
    
    rules = [
        ApprovalRule(
            rule_name="Production Deployment Approval",
            request_type=RequestType.DEPLOYMENT,
            conditions=[
                {"field": "environment", "operator": "equals", "value": "production"},
                {"field": "service_tier", "operator": "in", "value": ["critical", "important"]}
            ],
            required_approvers=["ops-manager@company.com", "security-lead@company.com"],
            minimum_approvals=2,
            auto_approve_conditions=[
                {"field": "requester_role", "operator": "in", "value": ["ops_director", "cto"]}
            ],
            escalation_rules=[
                {
                    "trigger": "timeout_50_percent",
                    "action": "notify_manager",
                    "escalate_to": ["ops-director@company.com"]
                }
            ],
            timeout_hours=8,
            enabled=True
        ),
        ApprovalRule(
            rule_name="Budget Request Approval",
            request_type=RequestType.BUDGET,
            conditions=[
                {"field": "amount", "operator": "greater_than", "value": 10000}
            ],
            required_approvers=["finance-director@company.com"],
            minimum_approvals=1,
            escalation_rules=[
                {
                    "trigger": "amount_greater_than_50000",
                    "action": "require_additional_approval",
                    "escalate_to": ["cfo@company.com"]
                }
            ],
            timeout_hours=48,
            enabled=True
        ),
        ApprovalRule(
            rule_name="Emergency Change Approval",
            request_type=RequestType.EMERGENCY,
            conditions=[
                {"field": "priority", "operator": "equals", "value": "critical"}
            ],
            required_approvers=["security-lead@company.com", "ops-director@company.com"],
            minimum_approvals=1,
            auto_approve_conditions=[
                {"field": "security_verified", "operator": "equals", "value": True}
            ],
            timeout_hours=2,
            enabled=True
        )
    ]
    
    # Apply filters
    if request_type:
        rules = [r for r in rules if r.request_type == request_type]
    if enabled is not None:
        rules = [r for r in rules if r.enabled == enabled]
    
    return rules

@router.post("/rules")
async def create_approval_rule(rule_data: Dict[str, Any]) -> ApprovalRule:
    """Create a new approval rule."""
    logger.info(f"Creating approval rule: {rule_data.get('rule_name')}")
    
    rule = ApprovalRule(
        rule_name=rule_data.get("rule_name", "New Rule"),
        request_type=RequestType(rule_data.get("request_type", "deployment")),
        conditions=rule_data.get("conditions", []),
        required_approvers=rule_data.get("required_approvers", []),
        minimum_approvals=rule_data.get("minimum_approvals", 1),
        timeout_hours=rule_data.get("timeout_hours", 24),
        enabled=rule_data.get("enabled", True)
    )
    
    return rule

@router.get("/templates")
async def get_workflow_templates() -> List[WorkflowTemplate]:
    """Get workflow templates."""
    logger.info("Fetching workflow templates")
    
    templates = [
        WorkflowTemplate(
            template_name="Standard Deployment Workflow",
            description="Standard workflow for production deployments",
            request_types=[RequestType.DEPLOYMENT],
            steps=[
                {
                    "step": "code_review",
                    "required": True,
                    "approvers": ["senior_dev@company.com"],
                    "parallel": False
                },
                {
                    "step": "security_review", 
                    "required": True,
                    "approvers": ["security-lead@company.com"],
                    "parallel": True
                },
                {
                    "step": "ops_approval",
                    "required": True,
                    "approvers": ["ops-manager@company.com"],
                    "parallel": True
                },
                {
                    "step": "final_approval",
                    "required": True,
                    "approvers": ["ops-director@company.com"],
                    "parallel": False
                }
            ],
            parallel_approval=True,
            sla_hours=8
        ),
        WorkflowTemplate(
            template_name="Budget Approval Workflow",
            description="Workflow for budget and financial requests",
            request_types=[RequestType.BUDGET],
            steps=[
                {
                    "step": "manager_approval",
                    "required": True,
                    "approvers": ["finance-manager@company.com"]
                },
                {
                    "step": "director_approval",
                    "required": True,
                    "approvers": ["finance-director@company.com"],
                    "condition": {"amount": {"greater_than": 25000}}
                }
            ],
            sla_hours=48
        )
    ]
    
    return templates

@router.get("/dashboard")
async def get_approval_dashboard() -> Dict[str, Any]:
    """Get approval dashboard data and metrics."""
    logger.info("Fetching approval dashboard data")
    
    return {
        "summary": {
            "pending_requests": 12,
            "approved_today": 8,
            "rejected_today": 1,
            "overdue_requests": 3,
            "average_approval_time": "4.2_hours",
            "approval_rate": 94.2,
            "total_requests_this_month": 156
        },
        "pending_by_type": [
            {"type": "deployment", "count": 5},
            {"type": "budget", "count": 3},
            {"type": "access", "count": 2},
            {"type": "maintenance", "count": 2}
        ],
        "pending_by_priority": [
            {"priority": "critical", "count": 1},
            {"priority": "high", "count": 4},
            {"priority": "medium", "count": 6},
            {"priority": "low", "count": 1}
        ],
        "approval_trends": [
            {"date": "2024-01-01", "approved": 12, "rejected": 2, "pending": 8},
            {"date": "2024-01-02", "approved": 15, "rejected": 1, "pending": 6},
            {"date": "2024-01-03", "approved": 18, "rejected": 0, "pending": 9},
            {"date": "2024-01-04", "approved": 14, "rejected": 3, "pending": 12},
            {"date": "2024-01-05", "approved": 16, "rejected": 1, "pending": 8}
        ],
        "top_requesters": [
            {"requester": "dev-team@company.com", "requests": 45, "approval_rate": 95.6},
            {"requester": "infrastructure@company.com", "requests": 32, "approval_rate": 96.9},
            {"requester": "security@company.com", "requests": 28, "approval_rate": 100.0}
        ],
        "bottlenecks": [
            {
                "approver": "security-lead@company.com",
                "pending_count": 6,
                "avg_response_time": "8.4_hours"
            },
            {
                "approver": "finance-director@company.com",
                "pending_count": 3,
                "avg_response_time": "12.1_hours"
            }
        ],
        "recent_activity": [
            {
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "action": "approved",
                "request_title": "Security patch deployment",
                "approver": "security-lead@company.com"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "action": "submitted",
                "request_title": "Database access request",
                "requester": "analytics@company.com"
            }
        ]
    }

@router.get("/analytics")
async def get_approval_analytics(timeframe: str = "30d") -> Dict[str, Any]:
    """Get approval analytics and reporting data."""
    logger.info(f"Fetching approval analytics for timeframe: {timeframe}")
    
    return {
        "performance_metrics": {
            "average_approval_time": "4.2_hours",
            "median_approval_time": "2.8_hours", 
            "approval_rate": 94.2,
            "sla_compliance": 89.5,
            "escalation_rate": 8.3
        },
        "volume_analysis": {
            "total_requests": 156,
            "daily_average": 5.2,
            "peak_day": "Tuesday",
            "peak_hour": "10:00",
            "growth_rate": 12.5
        },
        "approver_performance": [
            {
                "approver": "ops-manager@company.com",
                "requests_handled": 45,
                "avg_response_time": "2.1_hours",
                "approval_rate": 91.1
            },
            {
                "approver": "security-lead@company.com", 
                "requests_handled": 38,
                "avg_response_time": "6.8_hours",
                "approval_rate": 100.0
            }
        ],
        "workflow_efficiency": {
            "parallel_processing_benefit": "35%_time_saved",
            "automation_rate": 23.1,
            "manual_intervention_required": 76.9
        },
        "compliance_metrics": {
            "audit_trail_completeness": 100.0,
            "policy_adherence": 96.8,
            "segregation_of_duties": 100.0
        }
    }