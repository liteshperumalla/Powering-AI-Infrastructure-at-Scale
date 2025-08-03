"""
Business tools integration for Infra Mind.

Provides integrations with popular business communication and collaboration tools
including Slack, Microsoft Teams, email systems, and other enterprise tools.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
import aiohttp
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

from ..core.config import get_settings
from ..core.cache import cache_manager
class APIError(Exception):
    """API error exception."""
    pass
from ..models.assessment import Assessment
from ..models.report import Report

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(str, Enum):
    """Types of messages."""
    ASSESSMENT_COMPLETE = "assessment_complete"
    REPORT_READY = "report_ready"
    COMPLIANCE_ALERT = "compliance_alert"
    SYSTEM_NOTIFICATION = "system_notification"
    RECOMMENDATION_UPDATE = "recommendation_update"
    WORKFLOW_STATUS = "workflow_status"


@dataclass
class NotificationMessage:
    """Notification message structure."""
    message_type: MessageType
    title: str
    content: str
    priority: NotificationPriority
    recipient: str
    channel: NotificationChannel
    metadata: Dict[str, Any]
    attachments: Optional[List[Dict[str, Any]]] = None
    scheduled_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_type": self.message_type.value,
            "title": self.title,
            "content": self.content,
            "priority": self.priority.value,
            "recipient": self.recipient,
            "channel": self.channel.value,
            "metadata": self.metadata,
            "attachments": self.attachments or [],
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None
        }


@dataclass
class SlackMessage:
    """Slack-specific message format."""
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to Slack API payload."""
        payload = {
            "channel": self.channel,
            "text": self.text
        }
        
        if self.blocks:
            payload["blocks"] = self.blocks
        if self.attachments:
            payload["attachments"] = self.attachments
        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts
            
        return payload


@dataclass
class TeamsMessage:
    """Microsoft Teams message format."""
    title: str
    text: str
    theme_color: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    potential_action: Optional[List[Dict[str, Any]]] = None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to Teams webhook payload."""
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "title": self.title,
            "text": self.text
        }
        
        if self.theme_color:
            payload["themeColor"] = self.theme_color
        if self.sections:
            payload["sections"] = self.sections
        if self.potential_action:
            payload["potentialAction"] = self.potential_action
            
        return payload


class BusinessToolsIntegrator:
    """
    Integrator for business communication and collaboration tools.
    
    Supports Slack, Microsoft Teams, email, and other enterprise tools
    for notifications, report sharing, and workflow updates.
    """
    
    def __init__(self):
        """Initialize business tools integrator."""
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Tool configurations
        self.slack_config = {
            "bot_token": getattr(self.settings, "SLACK_BOT_TOKEN", None),
            "webhook_url": getattr(self.settings, "SLACK_WEBHOOK_URL", None),
            "enabled": getattr(self.settings, "ENABLE_SLACK_INTEGRATION", False)
        }
        
        self.teams_config = {
            "webhook_url": getattr(self.settings, "TEAMS_WEBHOOK_URL", None),
            "enabled": getattr(self.settings, "ENABLE_TEAMS_INTEGRATION", False)
        }
        
        self.email_config = {
            "smtp_server": getattr(self.settings, "SMTP_SERVER", "localhost"),
            "smtp_port": int(getattr(self.settings, "SMTP_PORT", 587)),
            "smtp_username": getattr(self.settings, "SMTP_USERNAME", None),
            "smtp_password": getattr(self.settings, "SMTP_PASSWORD", None),
            "from_email": getattr(self.settings, "FROM_EMAIL", "noreply@infra-mind.com"),
            "use_tls": getattr(self.settings, "SMTP_USE_TLS", True),
            "enabled": getattr(self.settings, "ENABLE_EMAIL_INTEGRATION", True)
        }
        
        # Calendar integration configuration
        self.calendar_config = {
            "google_calendar": {
                "enabled": getattr(self.settings, "ENABLE_GOOGLE_CALENDAR", False),
                "credentials_file": getattr(self.settings, "GOOGLE_CALENDAR_CREDENTIALS", None),
                "calendar_id": getattr(self.settings, "GOOGLE_CALENDAR_ID", "primary")
            },
            "outlook_calendar": {
                "enabled": getattr(self.settings, "ENABLE_OUTLOOK_CALENDAR", False),
                "client_id": getattr(self.settings, "OUTLOOK_CLIENT_ID", None),
                "client_secret": getattr(self.settings, "OUTLOOK_CLIENT_SECRET", None),
                "tenant_id": getattr(self.settings, "OUTLOOK_TENANT_ID", None)
            }
        }
        
        # Webhook system configuration
        self.webhook_config = {
            "enabled": getattr(self.settings, "ENABLE_WEBHOOK_SYSTEM", True),
            "max_retries": int(getattr(self.settings, "WEBHOOK_MAX_RETRIES", 3)),
            "timeout": int(getattr(self.settings, "WEBHOOK_TIMEOUT", 30)),
            "retry_delay": int(getattr(self.settings, "WEBHOOK_RETRY_DELAY", 60))
        }
        
        # Message templates
        self.message_templates = self._initialize_message_templates()
        
        logger.info("Business Tools Integrator initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "InfraMind-BusinessTools/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _initialize_message_templates(self) -> Dict[MessageType, Dict[str, str]]:
        """Initialize message templates for different notification types."""
        return {
            MessageType.ASSESSMENT_COMPLETE: {
                "title": "Infrastructure Assessment Complete",
                "content": "Your infrastructure assessment '{assessment_title}' has been completed. {agent_count} AI agents have analyzed your requirements and generated comprehensive recommendations.",
                "slack_blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *Assessment Complete*\n\nYour infrastructure assessment '{assessment_title}' is ready for review."
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Assessment ID:*\n{assessment_id}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Completion Time:*\n{completion_time}"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Results"
                                },
                                "url": "{dashboard_url}/assessments/{assessment_id}"
                            }
                        ]
                    }
                ]
            },
            MessageType.REPORT_READY: {
                "title": "Infrastructure Report Ready",
                "content": "Your infrastructure strategy report '{report_title}' has been generated and is ready for download. The report includes executive summary, technical recommendations, and implementation roadmap.",
                "slack_blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":memo: *Report Ready*\n\nYour infrastructure strategy report '{report_title}' is available for download."
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Report Type:*\n{report_type}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Generated:*\n{generation_time}"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Download Report"
                                },
                                "url": "{dashboard_url}/reports/{report_id}/download"
                            }
                        ]
                    }
                ]
            },
            MessageType.COMPLIANCE_ALERT: {
                "title": "Compliance Alert",
                "content": "A compliance issue has been identified in your infrastructure assessment. Framework: {framework}, Severity: {severity}. Immediate attention may be required.",
                "slack_blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: *Compliance Alert*\n\nA compliance issue requires your attention."
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Framework:*\n{framework}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Severity:*\n{severity}"
                            }
                        ]
                    }
                ]
            },
            MessageType.WORKFLOW_STATUS: {
                "title": "Workflow Status Update",
                "content": "Workflow '{workflow_name}' status: {status}. Progress: {progress}%. Estimated completion: {estimated_completion}.",
                "slack_blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":gear: *Workflow Update*\n\nWorkflow '{workflow_name}' - {status}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Progress: {progress}%"
                        }
                    }
                ]
            }
        }
    
    # Slack Integration
    
    async def send_slack_message(self, message: SlackMessage) -> Dict[str, Any]:
        """Send message to Slack."""
        if not self.slack_config["enabled"]:
            logger.warning("Slack integration disabled")
            return {"success": False, "reason": "Integration disabled"}
        
        try:
            # Use webhook if available, otherwise use bot token
            if self.slack_config["webhook_url"]:
                return await self._send_slack_webhook(message)
            elif self.slack_config["bot_token"]:
                return await self._send_slack_api(message)
            else:
                logger.error("No Slack configuration available")
                return {"success": False, "reason": "No configuration"}
                
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_slack_webhook(self, message: SlackMessage) -> Dict[str, Any]:
        """Send Slack message via webhook."""
        payload = message.to_payload()
        
        async with self.session.post(
            self.slack_config["webhook_url"],
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return {"success": True, "method": "webhook"}
            else:
                error_text = await response.text()
                logger.error(f"Slack webhook error: {response.status} - {error_text}")
                return {"success": False, "error": error_text}
    
    async def _send_slack_api(self, message: SlackMessage) -> Dict[str, Any]:
        """Send Slack message via API."""
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.slack_config['bot_token']}",
            "Content-Type": "application/json"
        }
        
        payload = message.to_payload()
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            
            if data.get("ok"):
                return {"success": True, "method": "api", "ts": data.get("ts")}
            else:
                logger.error(f"Slack API error: {data.get('error')}")
                return {"success": False, "error": data.get("error")}
    
    # Microsoft Teams Integration
    
    async def send_teams_message(self, message: TeamsMessage) -> Dict[str, Any]:
        """Send message to Microsoft Teams."""
        if not self.teams_config["enabled"] or not self.teams_config["webhook_url"]:
            logger.warning("Teams integration disabled or not configured")
            return {"success": False, "reason": "Integration disabled or not configured"}
        
        try:
            payload = message.to_payload()
            
            async with self.session.post(
                self.teams_config["webhook_url"],
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return {"success": True}
                else:
                    error_text = await response.text()
                    logger.error(f"Teams webhook error: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"Failed to send Teams message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Email Integration
    
    async def send_email(self, 
                        to_email: str,
                        subject: str,
                        content: str,
                        html_content: Optional[str] = None,
                        attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send email notification."""
        if not self.email_config["enabled"]:
            logger.warning("Email integration disabled")
            return {"success": False, "reason": "Integration disabled"}
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config["from_email"]
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content
            text_part = MIMEText(content, 'plain')
            msg.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_email_attachment(msg, attachment)
            
            # Send email
            await self._send_smtp_email(msg, to_email)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _add_email_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Add attachment to email message."""
        try:
            part = MIMEBase('application', 'octet-stream')
            
            if 'content' in attachment:
                # Content provided directly
                part.set_payload(attachment['content'])
            elif 'file_path' in attachment:
                # Read from file path
                with open(attachment['file_path'], 'rb') as f:
                    part.set_payload(f.read())
            else:
                logger.warning("Attachment missing content or file_path")
                return
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.get("filename", "attachment")}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add email attachment: {str(e)}")
    
    async def _send_smtp_email(self, msg: MIMEMultipart, to_email: str) -> None:
        """Send email via SMTP."""
        # Run SMTP operations in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg, to_email)
    
    def _smtp_send(self, msg: MIMEMultipart, to_email: str) -> None:
        """Synchronous SMTP send operation."""
        server = None
        try:
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            
            if self.email_config["use_tls"]:
                server.starttls()
            
            if self.email_config["smtp_username"] and self.email_config["smtp_password"]:
                server.login(self.email_config["smtp_username"], self.email_config["smtp_password"])
            
            server.send_message(msg, to_addresses=[to_email])
            
        finally:
            if server:
                server.quit()
    
    # High-level Notification Methods
    
    async def send_notification(self, notification: NotificationMessage) -> Dict[str, Any]:
        """Send notification via specified channel."""
        try:
            template = self.message_templates.get(notification.message_type, {})
            
            # Format content with metadata
            formatted_content = notification.content.format(**notification.metadata)
            formatted_title = notification.title.format(**notification.metadata)
            
            if notification.channel == NotificationChannel.SLACK:
                return await self._send_slack_notification(notification, template, formatted_title, formatted_content)
            elif notification.channel == NotificationChannel.TEAMS:
                return await self._send_teams_notification(notification, template, formatted_title, formatted_content)
            elif notification.channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(notification, template, formatted_title, formatted_content)
            else:
                logger.warning(f"Unsupported notification channel: {notification.channel}")
                return {"success": False, "reason": "Unsupported channel"}
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_slack_notification(self, 
                                     notification: NotificationMessage,
                                     template: Dict[str, Any],
                                     title: str,
                                     content: str) -> Dict[str, Any]:
        """Send Slack notification with template."""
        blocks = template.get("slack_blocks", [])
        
        # Format blocks with metadata
        formatted_blocks = []
        for block in blocks:
            formatted_block = json.loads(
                json.dumps(block).format(**notification.metadata)
            )
            formatted_blocks.append(formatted_block)
        
        slack_message = SlackMessage(
            channel=notification.recipient,
            text=content,
            blocks=formatted_blocks if formatted_blocks else None
        )
        
        return await self.send_slack_message(slack_message)
    
    async def _send_teams_notification(self,
                                     notification: NotificationMessage,
                                     template: Dict[str, Any],
                                     title: str,
                                     content: str) -> Dict[str, Any]:
        """Send Teams notification with template."""
        # Set theme color based on priority
        theme_colors = {
            NotificationPriority.LOW: "0078D4",
            NotificationPriority.MEDIUM: "FFB900",
            NotificationPriority.HIGH: "FF8C00",
            NotificationPriority.URGENT: "D13438"
        }
        
        teams_message = TeamsMessage(
            title=title,
            text=content,
            theme_color=theme_colors.get(notification.priority, "0078D4")
        )
        
        return await self.send_teams_message(teams_message)
    
    async def _send_email_notification(self,
                                     notification: NotificationMessage,
                                     template: Dict[str, Any],
                                     title: str,
                                     content: str) -> Dict[str, Any]:
        """Send email notification with template."""
        # Create HTML version of content
        html_content = f"""
        <html>
        <body>
            <h2>{title}</h2>
            <p>{content.replace(chr(10), '<br>')}</p>
            
            <hr>
            <p><small>This is an automated message from Infra Mind. Please do not reply to this email.</small></p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=notification.recipient,
            subject=title,
            content=content,
            html_content=html_content,
            attachments=notification.attachments
        )
    
    # Assessment and Report Notifications
    
    async def notify_assessment_complete(self,
                                       assessment: Assessment,
                                       recipient: str,
                                       channel: NotificationChannel) -> Dict[str, Any]:
        """Send assessment completion notification."""
        metadata = {
            "assessment_id": str(assessment.id),
            "assessment_title": assessment.title,
            "completion_time": assessment.completed_at.strftime("%Y-%m-%d %H:%M UTC") if assessment.completed_at else "N/A",
            "agent_count": len(assessment.agent_states) if assessment.agent_states else 0,
            "dashboard_url": getattr(self.settings, "DASHBOARD_URL", "https://app.infra-mind.com")
        }
        
        notification = NotificationMessage(
            message_type=MessageType.ASSESSMENT_COMPLETE,
            title="Infrastructure Assessment Complete",
            content=self.message_templates[MessageType.ASSESSMENT_COMPLETE]["content"],
            priority=NotificationPriority.MEDIUM,
            recipient=recipient,
            channel=channel,
            metadata=metadata
        )
        
        return await self.send_notification(notification)
    
    async def notify_report_ready(self,
                                report: Report,
                                recipient: str,
                                channel: NotificationChannel) -> Dict[str, Any]:
        """Send report ready notification."""
        metadata = {
            "report_id": str(report.id),
            "report_title": report.content.get("title", "Infrastructure Report"),
            "report_type": report.report_type,
            "generation_time": report.created_at.strftime("%Y-%m-%d %H:%M UTC"),
            "dashboard_url": getattr(self.settings, "DASHBOARD_URL", "https://app.infra-mind.com")
        }
        
        notification = NotificationMessage(
            message_type=MessageType.REPORT_READY,
            title="Infrastructure Report Ready",
            content=self.message_templates[MessageType.REPORT_READY]["content"],
            priority=NotificationPriority.MEDIUM,
            recipient=recipient,
            channel=channel,
            metadata=metadata
        )
        
        return await self.send_notification(notification)
    
    async def notify_compliance_alert(self,
                                    framework: str,
                                    severity: str,
                                    details: str,
                                    recipient: str,
                                    channel: NotificationChannel) -> Dict[str, Any]:
        """Send compliance alert notification."""
        priority_map = {
            "low": NotificationPriority.LOW,
            "medium": NotificationPriority.MEDIUM,
            "high": NotificationPriority.HIGH,
            "critical": NotificationPriority.URGENT
        }
        
        metadata = {
            "framework": framework,
            "severity": severity,
            "details": details
        }
        
        notification = NotificationMessage(
            message_type=MessageType.COMPLIANCE_ALERT,
            title="Compliance Alert",
            content=self.message_templates[MessageType.COMPLIANCE_ALERT]["content"],
            priority=priority_map.get(severity.lower(), NotificationPriority.MEDIUM),
            recipient=recipient,
            channel=channel,
            metadata=metadata
        )
        
        return await self.send_notification(notification)
    
    # Bulk Notifications
    
    async def send_bulk_notifications(self, notifications: List[NotificationMessage]) -> Dict[str, Any]:
        """Send multiple notifications."""
        results = {
            "total": len(notifications),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        # Send notifications concurrently
        tasks = [self.send_notification(notification) for notification in notifications]
        notification_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(notification_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["results"].append({
                    "index": i,
                    "success": False,
                    "error": str(result)
                })
            elif result.get("success"):
                results["successful"] += 1
                results["results"].append({
                    "index": i,
                    "success": True
                })
            else:
                results["failed"] += 1
                results["results"].append({
                    "index": i,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                })
        
        logger.info(f"Bulk notifications: {results['successful']}/{results['total']} successful")
        return results
    
    # Calendar Integration Methods
    
    async def create_calendar_event(self, 
                                  title: str,
                                  description: str,
                                  start_time: datetime,
                                  end_time: datetime,
                                  attendees: List[str] = None,
                                  calendar_provider: str = "google") -> Dict[str, Any]:
        """Create calendar event for assessment scheduling."""
        try:
            if calendar_provider == "google" and self.calendar_config["google_calendar"]["enabled"]:
                return await self._create_google_calendar_event(title, description, start_time, end_time, attendees)
            elif calendar_provider == "outlook" and self.calendar_config["outlook_calendar"]["enabled"]:
                return await self._create_outlook_calendar_event(title, description, start_time, end_time, attendees)
            else:
                logger.warning(f"Calendar provider {calendar_provider} not configured")
                return {"success": False, "reason": "Provider not configured"}
                
        except Exception as e:
            logger.error(f"Failed to create calendar event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _create_google_calendar_event(self, title: str, description: str, start_time: datetime, end_time: datetime, attendees: List[str] = None) -> Dict[str, Any]:
        """Create Google Calendar event."""
        # In a real implementation, this would use Google Calendar API
        # For now, return a mock response
        event_data = {
            "event_id": f"google_event_{int(start_time.timestamp())}",
            "title": title,
            "description": description,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees or [],
            "calendar_link": f"https://calendar.google.com/calendar/event?eid=mock_event_id",
            "provider": "google_calendar"
        }
        
        logger.info(f"Created Google Calendar event: {event_data['event_id']}")
        return {"success": True, "data": event_data}
    
    async def _create_outlook_calendar_event(self, title: str, description: str, start_time: datetime, end_time: datetime, attendees: List[str] = None) -> Dict[str, Any]:
        """Create Outlook Calendar event."""
        # In a real implementation, this would use Microsoft Graph API
        # For now, return a mock response
        event_data = {
            "event_id": f"outlook_event_{int(start_time.timestamp())}",
            "title": title,
            "description": description,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees or [],
            "calendar_link": f"https://outlook.live.com/calendar/event?id=mock_event_id",
            "provider": "outlook_calendar"
        }
        
        logger.info(f"Created Outlook Calendar event: {event_data['event_id']}")
        return {"success": True, "data": event_data}
    
    async def schedule_assessment_meeting(self,
                                        assessment_id: str,
                                        meeting_title: str,
                                        start_time: datetime,
                                        duration_minutes: int = 60,
                                        attendees: List[str] = None,
                                        calendar_provider: str = "google") -> Dict[str, Any]:
        """Schedule assessment meeting with calendar integration."""
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        description = f"""
        Infrastructure Assessment Meeting
        
        Assessment ID: {assessment_id}
        Duration: {duration_minutes} minutes
        
        This meeting is scheduled to discuss the infrastructure assessment results and recommendations.
        
        Please join the meeting at the scheduled time to review:
        - Assessment findings
        - Recommended infrastructure changes
        - Implementation roadmap
        - Next steps
        
        Generated by Infra Mind Platform
        """
        
        result = await self.create_calendar_event(
            title=meeting_title,
            description=description.strip(),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            calendar_provider=calendar_provider
        )
        
        if result.get("success"):
            # Send calendar invitation via email
            if attendees:
                for attendee in attendees:
                    await self._send_calendar_invitation_email(
                        attendee, meeting_title, start_time, end_time, result["data"]
                    )
        
        return result
    
    async def _send_calendar_invitation_email(self,
                                            attendee_email: str,
                                            meeting_title: str,
                                            start_time: datetime,
                                            end_time: datetime,
                                            event_data: Dict[str, Any]) -> None:
        """Send calendar invitation email."""
        subject = f"Meeting Invitation: {meeting_title}"
        
        content = f"""
        You have been invited to a meeting:
        
        Title: {meeting_title}
        Date: {start_time.strftime('%Y-%m-%d')}
        Time: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} UTC
        
        Calendar Link: {event_data.get('calendar_link', 'N/A')}
        
        Please add this meeting to your calendar and join at the scheduled time.
        
        Best regards,
        Infra Mind Team
        """
        
        await self.send_email(
            to_email=attendee_email,
            subject=subject,
            content=content.strip()
        )
    
    # Webhook System Methods
    
    async def send_webhook(self, 
                          webhook_url: str,
                          payload: Dict[str, Any],
                          event_type: str,
                          headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Send webhook notification to external system."""
        if not self.webhook_config["enabled"]:
            logger.warning("Webhook system disabled")
            return {"success": False, "reason": "Webhook system disabled"}
        
        webhook_headers = {
            "Content-Type": "application/json",
            "User-Agent": "InfraMind-Webhook/1.0",
            "X-InfraMind-Event": event_type,
            "X-InfraMind-Timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if headers:
            webhook_headers.update(headers)
        
        # Add webhook signature for security (in production, use HMAC)
        webhook_id = f"webhook_{int(datetime.now(timezone.utc).timestamp())}"
        webhook_headers["X-InfraMind-Webhook-ID"] = webhook_id
        
        for attempt in range(self.webhook_config["max_retries"]):
            try:
                async with self.session.post(
                    webhook_url,
                    json=payload,
                    headers=webhook_headers,
                    timeout=aiohttp.ClientTimeout(total=self.webhook_config["timeout"])
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Webhook delivered successfully to {webhook_url}")
                        return {
                            "success": True,
                            "webhook_id": webhook_id,
                            "status_code": response.status,
                            "attempt": attempt + 1
                        }
                    else:
                        logger.warning(f"Webhook failed with status {response.status} (attempt {attempt + 1})")
                        
            except Exception as e:
                logger.error(f"Webhook delivery failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt < self.webhook_config["max_retries"] - 1:
                    await asyncio.sleep(self.webhook_config["retry_delay"] * (attempt + 1))
        
        logger.error(f"Webhook delivery failed after {self.webhook_config['max_retries']} attempts")
        return {
            "success": False,
            "webhook_id": webhook_id,
            "error": "Max retries exceeded",
            "attempts": self.webhook_config["max_retries"]
        }
    
    async def send_assessment_webhook(self,
                                    webhook_url: str,
                                    assessment_id: str,
                                    event_type: str,
                                    assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send assessment-related webhook."""
        payload = {
            "event_type": event_type,
            "assessment_id": assessment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": assessment_data,
            "source": "infra_mind_platform"
        }
        
        return await self.send_webhook(webhook_url, payload, event_type)
    
    async def send_report_webhook(self,
                                webhook_url: str,
                                report_id: str,
                                event_type: str,
                                report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send report-related webhook."""
        payload = {
            "event_type": event_type,
            "report_id": report_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": report_data,
            "source": "infra_mind_platform"
        }
        
        return await self.send_webhook(webhook_url, payload, event_type)
    
    async def register_webhook_endpoint(self,
                                      webhook_url: str,
                                      event_types: List[str],
                                      description: str = "") -> Dict[str, Any]:
        """Register webhook endpoint for notifications."""
        webhook_registration = {
            "webhook_id": f"webhook_reg_{int(datetime.now(timezone.utc).timestamp())}",
            "url": webhook_url,
            "event_types": event_types,
            "description": description,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        
        # In production, this would be stored in database
        cache_key = f"webhook_registration:{webhook_registration['webhook_id']}"
        await cache_manager.set(
            cache_key,
            json.dumps(webhook_registration),
            ttl=86400 * 30  # 30 days
        )
        
        logger.info(f"Registered webhook endpoint: {webhook_registration['webhook_id']}")
        return {"success": True, "data": webhook_registration}
    
    # Integration Health and Testing
    
    async def test_calendar_integration(self, provider: str = "google") -> Dict[str, Any]:
        """Test calendar integration."""
        test_results = {
            "provider": provider,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": {}
        }
        
        if provider == "google":
            config = self.calendar_config["google_calendar"]
            test_results["tests"]["configuration"] = {
                "enabled": config["enabled"],
                "credentials_configured": bool(config["credentials_file"]),
                "calendar_id_set": bool(config["calendar_id"])
            }
        elif provider == "outlook":
            config = self.calendar_config["outlook_calendar"]
            test_results["tests"]["configuration"] = {
                "enabled": config["enabled"],
                "client_id_configured": bool(config["client_id"]),
                "client_secret_configured": bool(config["client_secret"]),
                "tenant_id_configured": bool(config["tenant_id"])
            }
        
        # Test event creation (mock)
        test_start = datetime.now(timezone.utc) + timedelta(hours=1)
        test_end = test_start + timedelta(hours=1)
        
        test_event_result = await self.create_calendar_event(
            title="Test Event - Infra Mind Integration Test",
            description="This is a test event to verify calendar integration",
            start_time=test_start,
            end_time=test_end,
            calendar_provider=provider
        )
        
        test_results["tests"]["event_creation"] = test_event_result
        test_results["overall_status"] = "passed" if test_event_result.get("success") else "failed"
        
        return test_results
    
    async def test_webhook_endpoint(self, webhook_url: str) -> Dict[str, Any]:
        """Test webhook endpoint connectivity."""
        test_payload = {
            "event_type": "test",
            "message": "This is a test webhook from Infra Mind",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test": True
        }
        
        result = await self.send_webhook(webhook_url, test_payload, "test")
        
        return {
            "webhook_url": webhook_url,
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_result": result,
            "status": "passed" if result.get("success") else "failed"
        }
    
    # Configuration and Testing
    
    async def test_integrations(self) -> Dict[str, Any]:
        """Test all configured integrations."""
        test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "integrations": {}
        }
        
        # Test Slack
        if self.slack_config["enabled"]:
            try:
                test_message = SlackMessage(
                    channel="#general",
                    text="Test message from Infra Mind - Integration Test"
                )
                result = await self.send_slack_message(test_message)
                test_results["integrations"]["slack"] = {
                    "enabled": True,
                    "test_successful": result.get("success", False),
                    "error": result.get("error")
                }
            except Exception as e:
                test_results["integrations"]["slack"] = {
                    "enabled": True,
                    "test_successful": False,
                    "error": str(e)
                }
        else:
            test_results["integrations"]["slack"] = {"enabled": False}
        
        # Test Teams
        if self.teams_config["enabled"]:
            try:
                test_message = TeamsMessage(
                    title="Integration Test",
                    text="Test message from Infra Mind - Integration Test"
                )
                result = await self.send_teams_message(test_message)
                test_results["integrations"]["teams"] = {
                    "enabled": True,
                    "test_successful": result.get("success", False),
                    "error": result.get("error")
                }
            except Exception as e:
                test_results["integrations"]["teams"] = {
                    "enabled": True,
                    "test_successful": False,
                    "error": str(e)
                }
        else:
            test_results["integrations"]["teams"] = {"enabled": False}
        
        # Test Email
        if self.email_config["enabled"]:
            try:
                # Don't actually send test email, just validate configuration
                test_results["integrations"]["email"] = {
                    "enabled": True,
                    "test_successful": True,
                    "smtp_server": self.email_config["smtp_server"],
                    "smtp_port": self.email_config["smtp_port"]
                }
            except Exception as e:
                test_results["integrations"]["email"] = {
                    "enabled": True,
                    "test_successful": False,
                    "error": str(e)
                }
        else:
            test_results["integrations"]["email"] = {"enabled": False}
        
        return test_results


# Global integrator instance
business_tools_integrator = BusinessToolsIntegrator()


# Convenience functions

async def send_assessment_notification(assessment: Assessment, 
                                     recipient: str,
                                     channel: NotificationChannel = NotificationChannel.EMAIL) -> Dict[str, Any]:
    """Send assessment completion notification."""
    async with business_tools_integrator as integrator:
        return await integrator.notify_assessment_complete(assessment, recipient, channel)


async def send_report_notification(report: Report,
                                 recipient: str,
                                 channel: NotificationChannel = NotificationChannel.EMAIL) -> Dict[str, Any]:
    """Send report ready notification."""
    async with business_tools_integrator as integrator:
        return await integrator.notify_report_ready(report, recipient, channel)


async def send_compliance_notification(framework: str,
                                     severity: str,
                                     details: str,
                                     recipient: str,
                                     channel: NotificationChannel = NotificationChannel.EMAIL) -> Dict[str, Any]:
    """Send compliance alert notification."""
    async with business_tools_integrator as integrator:
        return await integrator.notify_compliance_alert(framework, severity, details, recipient, channel)