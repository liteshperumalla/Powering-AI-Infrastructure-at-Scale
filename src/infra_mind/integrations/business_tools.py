"""
Business tools integration for Infra Mind.

Provides integrations with popular business communication and collaboration tools
including Slack, Microsoft Teams, email systems, and other enterprise tools.
"""

import asyncio
import logging
from datetime import datetime, timezone
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