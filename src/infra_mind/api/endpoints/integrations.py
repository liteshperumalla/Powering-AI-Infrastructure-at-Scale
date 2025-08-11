"""
API endpoints for third-party integrations.

Provides REST API endpoints for compliance databases, business tools,
and SSO provider integrations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field

from .auth import get_current_user
from ...models.user import User
from ...integrations.compliance_databases import (
    ComplianceFramework, IndustryType, ComplianceRequirementType,
    get_compliance_requirements, assess_framework_compliance,
    get_industry_compliance_summary
)
from ...integrations.business_tools import (
    NotificationChannel, NotificationPriority, MessageType,
    send_assessment_notification, send_report_notification,
    send_compliance_notification, business_tools_integrator
)
from ...integrations.sso_providers import (
    SSOProvider, initiate_sso_login, handle_sso_callback,
    get_available_sso_providers, test_sso_providers
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# Pydantic models for request/response

class ComplianceAssessmentRequest(BaseModel):
    """Request model for compliance assessment."""
    framework: ComplianceFramework
    industry: IndustryType
    current_controls: List[str] = Field(default_factory=list)
    infrastructure_config: Dict[str, Any] = Field(default_factory=dict)


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""
    message_type: MessageType
    title: str
    content: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    recipient: str
    channel: NotificationChannel
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SSOLoginRequest(BaseModel):
    """Request model for SSO login initiation."""
    provider: SSOProvider
    redirect_uri: str


class SSOCallbackRequest(BaseModel):
    """Request model for SSO callback handling."""
    provider: SSOProvider
    authorization_code: str
    state: str
    redirect_uri: str


# Compliance Database Endpoints

@router.get("/compliance/frameworks")
async def get_compliance_frameworks(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of supported compliance frameworks."""
    frameworks = [
        {
            "value": framework.value,
            "name": framework.value.upper().replace("_", " "),
            "description": f"{framework.value.upper()} compliance framework"
        }
        for framework in ComplianceFramework
    ]
    
    return {
        "frameworks": frameworks,
        "total": len(frameworks)
    }


@router.get("/compliance/industries")
async def get_industry_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of supported industry types."""
    industries = [
        {
            "value": industry.value,
            "name": industry.value.replace("_", " ").title(),
            "description": f"{industry.value.replace('_', ' ').title()} industry"
        }
        for industry in IndustryType
    ]
    
    return {
        "industries": industries,
        "total": len(industries)
    }


@router.get("/compliance/requirements/{framework}")
async def get_framework_requirements(
    framework: ComplianceFramework,
    industry: Optional[IndustryType] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get compliance requirements for a specific framework."""
    try:
        requirements = await get_compliance_requirements(framework, industry)
        
        return {
            "framework": framework.value,
            "industry": industry.value if industry else None,
            "requirements": [req.to_dict() for req in requirements],
            "total": len(requirements)
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance requirements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance requirements: {str(e)}"
        )


@router.post("/compliance/assess")
async def assess_compliance(
    request: ComplianceAssessmentRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Assess compliance against a specific framework."""
    try:
        assessment = await assess_framework_compliance(
            framework=request.framework,
            industry=request.industry,
            current_controls=request.current_controls,
            infrastructure_config=request.infrastructure_config
        )
        
        return {
            "assessment": assessment.to_dict(),
            "assessed_by": current_user.email,
            "assessed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to assess compliance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess compliance: {str(e)}"
        )


@router.get("/compliance/industry-summary/{industry}")
async def get_compliance_summary(
    industry: IndustryType,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get compliance summary for an industry."""
    try:
        summary = await get_industry_compliance_summary(industry)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get compliance summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance summary: {str(e)}"
        )


# Business Tools Integration Endpoints

@router.get("/business-tools/channels")
async def get_notification_channels(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of supported notification channels."""
    channels = [
        {
            "value": channel.value,
            "name": channel.value.replace("_", " ").title(),
            "description": f"{channel.value.replace('_', ' ').title()} notifications"
        }
        for channel in NotificationChannel
    ]
    
    return {
        "channels": channels,
        "total": len(channels)
    }


@router.post("/business-tools/notify")
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send notification via specified channel."""
    try:
        async with business_tools_integrator as integrator:
            from ...integrations.business_tools import NotificationMessage
            
            notification = NotificationMessage(
                message_type=request.message_type,
                title=request.title,
                content=request.content,
                priority=request.priority,
                recipient=request.recipient,
                channel=request.channel,
                metadata=request.metadata
            )
            
            result = await integrator.send_notification(notification)
            
            return {
                "success": result.get("success", False),
                "channel": request.channel.value,
                "recipient": request.recipient,
                "sent_by": current_user.email,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "details": result
            }
            
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/business-tools/test")
async def test_business_tools(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test business tools integrations."""
    try:
        async with business_tools_integrator as integrator:
            test_results = await integrator.test_integrations()
            
            return {
                "test_results": test_results,
                "tested_by": current_user.email,
                "tested_at": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to test business tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test business tools: {str(e)}"
        )


# SSO Provider Endpoints

@router.get("/sso/providers")
async def get_sso_providers() -> Dict[str, Any]:
    """Get list of available SSO providers."""
    try:
        providers = await get_available_sso_providers()
        
        return {
            "providers": providers,
            "total": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Failed to get SSO providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SSO providers: {str(e)}"
        )


@router.post("/sso/login")
async def initiate_sso_login_endpoint(
    request: SSOLoginRequest
) -> Dict[str, Any]:
    """Initiate SSO login flow."""
    try:
        auth_request = await initiate_sso_login(
            provider=request.provider,
            redirect_uri=request.redirect_uri
        )
        
        return {
            "authorization_url": auth_request.authorization_url,
            "state": auth_request.state,
            "provider": request.provider.value,
            "expires_at": auth_request.expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate SSO login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SSO login: {str(e)}"
        )


@router.post("/sso/callback")
async def handle_sso_callback_endpoint(
    request: SSOCallbackRequest
) -> Dict[str, Any]:
    """Handle SSO callback and create user session."""
    try:
        result = await handle_sso_callback(
            provider=request.provider,
            authorization_code=request.authorization_code,
            state=request.state,
            redirect_uri=request.redirect_uri
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to handle SSO callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle SSO callback: {str(e)}"
        )


@router.post("/sso/test")
async def test_sso_providers_endpoint(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test SSO provider configurations."""
    try:
        test_results = await test_sso_providers()
        
        return {
            "test_results": test_results,
            "tested_by": current_user.email,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test SSO providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test SSO providers: {str(e)}"
        )


# Integration Status and Health Endpoints

@router.get("/status")
async def get_integration_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of all third-party integrations."""
    try:
        # Test business tools
        async with business_tools_integrator as integrator:
            business_tools_status = await integrator.test_integrations()
        
        # Test SSO providers
        sso_status = await test_sso_providers()
        
        # Compliance databases status (simplified)
        compliance_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "local_database": {"enabled": True, "status": "operational"},
            "external_apis": {
                "nist": {"enabled": False, "status": "not_configured"},
                "gdpr": {"enabled": False, "status": "not_configured"},
                "iso": {"enabled": False, "status": "not_configured"}
            }
        }
        
        return {
            "integration_status": {
                "business_tools": business_tools_status,
                "sso_providers": sso_status,
                "compliance_databases": compliance_status
            },
            "checked_by": current_user.email,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration status: {str(e)}"
        )


@router.get("/health")
async def integration_health_check() -> Dict[str, Any]:
    """Health check endpoint for integrations."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrations": {
            "compliance_databases": "operational",
            "business_tools": "operational", 
            "sso_providers": "operational"
        }
    }