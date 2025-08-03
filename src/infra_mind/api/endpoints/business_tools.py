"""
Business tools integration API endpoints.

Provides endpoints for Slack, Teams, email, calendar, and webhook integrations.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from ...integrations.business_tools import (
    BusinessToolsIntegrator,
    NotificationMessage,
    NotificationChannel,
    NotificationPriority,
    MessageType,
    SlackMessage,
    TeamsMessage
)
from ...core.auth import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-tools", tags=["business-tools"])


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""
    message_type: MessageType
    title: str
    content: str
    priority: NotificationPriority
    recipient: str
    channel: NotificationChannel
    metadata: Dict[str, Any] = {}


class SlackMessageRequest(BaseModel):
    """Request model for Slack messages."""
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None


class TeamsMessageRequest(BaseModel):
    """Request model for Teams messages."""
    title: str
    text: str
    theme_color: Optional[str] = None


class EmailRequest(BaseModel):
    """Request model for email notifications."""
    to_email: EmailStr
    subject: str
    content: str
    html_content: Optional[str] = None


class CalendarEventRequest(BaseModel):
    """Request model for calendar events."""
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    attendees: Optional[List[EmailStr]] = None
    calendar_provider: str = "google"


class WebhookRequest(BaseModel):
    """Request model for webhook notifications."""
    webhook_url: str
    payload: Dict[str, Any]
    event_type: str
    headers: Optional[Dict[str, str]] = None


class WebhookRegistrationRequest(BaseModel):
    """Request model for webhook registration."""
    webhook_url: str
    event_types: List[str]
    description: str = ""


@router.post("/notifications/send")
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send notification via specified channel."""
    try:
        notification = NotificationMessage(
            message_type=request.message_type,
            title=request.title,
            content=request.content,
            priority=request.priority,
            recipient=request.recipient,
            channel=request.channel,
            metadata=request.metadata
        )
        
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.send_notification(notification)
        
        logger.info(f"Sent notification via {request.channel.value}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/send")
async def send_slack_message(
    request: SlackMessageRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send message to Slack."""
    try:
        slack_message = SlackMessage(
            channel=request.channel,
            text=request.text,
            blocks=request.blocks
        )
        
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.send_slack_message(slack_message)
        
        logger.info(f"Sent Slack message to {request.channel}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send Slack message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/send")
async def send_teams_message(
    request: TeamsMessageRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send message to Microsoft Teams."""
    try:
        teams_message = TeamsMessage(
            title=request.title,
            text=request.text,
            theme_color=request.theme_color
        )
        
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.send_teams_message(teams_message)
        
        logger.info(f"Sent Teams message: {request.title}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send Teams message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/send")
async def send_email(
    request: EmailRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send email notification."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.send_email(
                to_email=request.to_email,
                subject=request.subject,
                content=request.content,
                html_content=request.html_content
            )
        
        logger.info(f"Sent email to {request.to_email}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/create-event")
async def create_calendar_event(
    request: CalendarEventRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create calendar event."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.create_calendar_event(
                title=request.title,
                description=request.description,
                start_time=request.start_time,
                end_time=request.end_time,
                attendees=request.attendees,
                calendar_provider=request.calendar_provider
            )
        
        logger.info(f"Created calendar event: {request.title}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create calendar event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/schedule-assessment")
async def schedule_assessment_meeting(
    assessment_id: str,
    meeting_title: str,
    start_time: datetime,
    duration_minutes: int = 60,
    attendees: Optional[List[EmailStr]] = None,
    calendar_provider: str = "google",
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Schedule assessment meeting with calendar integration."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.schedule_assessment_meeting(
                assessment_id=assessment_id,
                meeting_title=meeting_title,
                start_time=start_time,
                duration_minutes=duration_minutes,
                attendees=attendees,
                calendar_provider=calendar_provider
            )
        
        logger.info(f"Scheduled assessment meeting for {assessment_id}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule assessment meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/send")
async def send_webhook(
    request: WebhookRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send webhook notification."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.send_webhook(
                webhook_url=request.webhook_url,
                payload=request.payload,
                event_type=request.event_type,
                headers=request.headers
            )
        
        logger.info(f"Sent webhook to {request.webhook_url}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/register")
async def register_webhook(
    request: WebhookRegistrationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Register webhook endpoint."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.register_webhook_endpoint(
                webhook_url=request.webhook_url,
                event_types=request.event_types,
                description=request.description
            )
        
        logger.info(f"Registered webhook endpoint: {request.webhook_url}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to register webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/test")
async def test_webhook_endpoint(
    webhook_url: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test webhook endpoint connectivity."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.test_webhook_endpoint(webhook_url)
        
        logger.info(f"Tested webhook endpoint: {webhook_url}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to test webhook endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/test")
async def test_integrations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test all business tool integrations."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.test_integrations()
        
        logger.info("Tested all business tool integrations")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to test integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/test/{provider}")
async def test_calendar_integration(
    provider: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test calendar integration."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.test_calendar_integration(provider)
        
        logger.info(f"Tested {provider} calendar integration")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to test calendar integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_business_tools_health() -> Dict[str, Any]:
    """Get business tools integration health status."""
    try:
        health_status = {
            "service": "business_tools",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "integrations": {
                "slack": "available",
                "teams": "available",
                "email": "available",
                "calendar": "available",
                "webhooks": "available"
            },
            "features": {
                "notifications": "available",
                "calendar_scheduling": "available",
                "webhook_system": "available",
                "bulk_notifications": "available"
            }
        }
        
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get service health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Assessment and Report specific notification endpoints

@router.post("/notifications/assessment-complete")
async def notify_assessment_complete(
    assessment_id: str,
    recipient: str,
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send assessment completion notification."""
    try:
        # In a real implementation, this would fetch the assessment from database
        mock_assessment = type('Assessment', (), {
            'id': assessment_id,
            'title': 'Infrastructure Assessment',
            'completed_at': datetime.now(timezone.utc),
            'agent_states': ['cto', 'cloud_engineer', 'research']
        })()
        
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.notify_assessment_complete(
                assessment=mock_assessment,
                recipient=recipient,
                channel=channel
            )
        
        logger.info(f"Sent assessment completion notification for {assessment_id}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send assessment notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/report-ready")
async def notify_report_ready(
    report_id: str,
    recipient: str,
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send report ready notification."""
    try:
        # In a real implementation, this would fetch the report from database
        mock_report = type('Report', (), {
            'id': report_id,
            'report_type': 'infrastructure_strategy',
            'created_at': datetime.now(timezone.utc),
            'content': {'title': 'Infrastructure Strategy Report'}
        })()
        
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.notify_report_ready(
                report=mock_report,
                recipient=recipient,
                channel=channel
            )
        
        logger.info(f"Sent report ready notification for {report_id}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send report notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/compliance-alert")
async def notify_compliance_alert(
    framework: str,
    severity: str,
    details: str,
    recipient: str,
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send compliance alert notification."""
    try:
        async with BusinessToolsIntegrator() as integrator:
            result = await integrator.notify_compliance_alert(
                framework=framework,
                severity=severity,
                details=details,
                recipient=recipient,
                channel=channel
            )
        
        logger.info(f"Sent compliance alert for {framework}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send compliance alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))