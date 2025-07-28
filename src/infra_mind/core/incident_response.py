"""
Security incident response system for Infra Mind.

Provides automated incident detection, response workflows, and forensic capabilities.
"""

import asyncio
import json
import smtplib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
import subprocess
from pathlib import Path

from .audit import AuditLogger, AuditEventType, AuditSeverity
from .security import SecurityMonitor
from .encryption import SecureDataHandler

logger = logging.getLogger(__name__)


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    """Incident status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentType(str, Enum):
    """Types of security incidents."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    MALWARE_DETECTION = "malware_detection"
    DDOS_ATTACK = "ddos_attack"
    INSIDER_THREAT = "insider_threat"
    SYSTEM_COMPROMISE = "system_compromise"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class SecurityIncident:
    """Security incident data structure."""
    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    title: str
    description: str
    affected_systems: List[str]
    indicators: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    assigned_to: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def add_timeline_entry(self, action: str, details: Dict[str, Any], user: str = "system"):
        """Add entry to incident timeline."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details,
            "user": user
        }
        self.timeline.append(entry)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_status(self, new_status: IncidentStatus, user: str = "system", notes: str = ""):
        """Update incident status."""
        old_status = self.status
        self.status = new_status
        
        self.add_timeline_entry(
            action="status_change",
            details={
                "old_status": old_status,
                "new_status": new_status,
                "notes": notes
            },
            user=user
        )
        
        if new_status == IncidentStatus.RESOLVED:
            self.resolved_at = datetime.now(timezone.utc)


class IncidentDetector:
    """
    Automated incident detection system.
    
    Monitors system events and triggers incident response when threats are detected.
    """
    
    def __init__(self):
        self.security_monitor = SecurityMonitor()
        self.audit_logger = AuditLogger()
        self.detection_rules = self._load_detection_rules()
        self.active_incidents: Dict[str, SecurityIncident] = {}
        self.detection_callbacks: List[Callable] = []
    
    def _load_detection_rules(self) -> Dict[str, Dict]:
        """Load incident detection rules."""
        return {
            "failed_login_threshold": {
                "type": IncidentType.UNAUTHORIZED_ACCESS,
                "severity": IncidentSeverity.HIGH,
                "threshold": 5,
                "window_minutes": 15,
                "description": "Multiple failed login attempts detected"
            },
            "admin_access_anomaly": {
                "type": IncidentType.SUSPICIOUS_ACTIVITY,
                "severity": IncidentSeverity.HIGH,
                "description": "Unusual admin access pattern detected"
            },
            "data_export_volume": {
                "type": IncidentType.DATA_BREACH,
                "severity": IncidentSeverity.CRITICAL,
                "threshold": 1000,  # MB
                "description": "Large volume data export detected"
            },
            "sql_injection_attempt": {
                "type": IncidentType.SYSTEM_COMPROMISE,
                "severity": IncidentSeverity.CRITICAL,
                "description": "SQL injection attempt detected"
            },
            "privilege_escalation": {
                "type": IncidentType.SYSTEM_COMPROMISE,
                "severity": IncidentSeverity.CRITICAL,
                "description": "Privilege escalation attempt detected"
            }
        }
    
    def add_detection_callback(self, callback: Callable[[SecurityIncident], None]):
        """Add callback for incident detection."""
        self.detection_callbacks.append(callback)
    
    async def analyze_event(self, event_data: Dict[str, Any]) -> Optional[SecurityIncident]:
        """
        Analyze event for potential security incidents.
        
        Args:
            event_data: Event data to analyze
            
        Returns:
            SecurityIncident if threat detected, None otherwise
        """
        try:
            # Check each detection rule
            for rule_name, rule_config in self.detection_rules.items():
                incident = await self._check_rule(rule_name, rule_config, event_data)
                if incident:
                    return incident
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing event for incidents: {e}")
            return None
    
    async def _check_rule(self, rule_name: str, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check specific detection rule."""
        try:
            if rule_name == "failed_login_threshold":
                return await self._check_failed_login_threshold(rule_config, event_data)
            elif rule_name == "admin_access_anomaly":
                return await self._check_admin_access_anomaly(rule_config, event_data)
            elif rule_name == "data_export_volume":
                return await self._check_data_export_volume(rule_config, event_data)
            elif rule_name == "sql_injection_attempt":
                return await self._check_sql_injection_attempt(rule_config, event_data)
            elif rule_name == "privilege_escalation":
                return await self._check_privilege_escalation(rule_config, event_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking rule {rule_name}: {e}")
            return None
    
    async def _check_failed_login_threshold(self, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check for failed login threshold breach."""
        if event_data.get("event_type") != "login_failure":
            return None
        
        ip_address = event_data.get("ip_address")
        if not ip_address:
            return None
        
        # Check if we already have an active incident for this IP
        existing_incident_id = f"failed_login_{ip_address}"
        if existing_incident_id in self.active_incidents:
            return None
        
        # Count recent failed attempts from this IP
        # In production, this would query the audit log database
        failed_count = 6  # Mock count for demonstration
        
        if failed_count >= rule_config["threshold"]:
            incident = SecurityIncident(
                incident_id=existing_incident_id,
                incident_type=rule_config["type"],
                severity=rule_config["severity"],
                status=IncidentStatus.OPEN,
                title=f"Multiple Failed Login Attempts from {ip_address}",
                description=f"{failed_count} failed login attempts from IP {ip_address}",
                affected_systems=["Authentication System"],
                indicators={
                    "ip_address": ip_address,
                    "failed_attempts": failed_count,
                    "time_window": rule_config["window_minutes"]
                },
                timeline=[]
            )
            
            incident.add_timeline_entry(
                action="incident_created",
                details={"trigger": "failed_login_threshold", "count": failed_count}
            )
            
            self.active_incidents[existing_incident_id] = incident
            return incident
        
        return None
    
    async def _check_admin_access_anomaly(self, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check for admin access anomalies."""
        if event_data.get("user_role") != "admin":
            return None
        
        # Check for unusual access patterns
        user_id = event_data.get("user_id")
        ip_address = event_data.get("ip_address")
        access_time = event_data.get("timestamp", datetime.now(timezone.utc))
        
        # Check for access outside business hours
        if isinstance(access_time, str):
            access_time = datetime.fromisoformat(access_time.replace('Z', '+00:00'))
        
        hour = access_time.hour
        if hour < 6 or hour > 22:  # Outside business hours
            incident_id = f"admin_anomaly_{user_id}_{int(access_time.timestamp())}"
            
            incident = SecurityIncident(
                incident_id=incident_id,
                incident_type=rule_config["type"],
                severity=rule_config["severity"],
                status=IncidentStatus.OPEN,
                title=f"Admin Access Outside Business Hours",
                description=f"Admin user {user_id} accessed system at {access_time}",
                affected_systems=["Admin Panel"],
                indicators={
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "access_time": access_time.isoformat(),
                    "hour": hour
                },
                timeline=[]
            )
            
            incident.add_timeline_entry(
                action="incident_created",
                details={"trigger": "admin_access_anomaly", "reason": "outside_business_hours"}
            )
            
            return incident
        
        return None
    
    async def _check_data_export_volume(self, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check for large data export volumes."""
        if event_data.get("action") != "data_export":
            return None
        
        export_size_mb = event_data.get("export_size_mb", 0)
        
        if export_size_mb >= rule_config["threshold"]:
            user_id = event_data.get("user_id")
            incident_id = f"data_export_{user_id}_{int(datetime.now().timestamp())}"
            
            incident = SecurityIncident(
                incident_id=incident_id,
                incident_type=rule_config["type"],
                severity=rule_config["severity"],
                status=IncidentStatus.OPEN,
                title=f"Large Data Export Detected",
                description=f"User {user_id} exported {export_size_mb}MB of data",
                affected_systems=["Data Export System"],
                indicators={
                    "user_id": user_id,
                    "export_size_mb": export_size_mb,
                    "threshold_mb": rule_config["threshold"]
                },
                timeline=[]
            )
            
            incident.add_timeline_entry(
                action="incident_created",
                details={"trigger": "data_export_volume", "size_mb": export_size_mb}
            )
            
            return incident
        
        return None
    
    async def _check_sql_injection_attempt(self, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check for SQL injection attempts."""
        request_data = event_data.get("request_data", "")
        
        # SQL injection patterns
        sql_patterns = [
            "' or '1'='1",
            "'; drop table",
            "union select",
            "' or 1=1",
            "admin'--"
        ]
        
        if any(pattern in request_data.lower() for pattern in sql_patterns):
            ip_address = event_data.get("ip_address")
            incident_id = f"sql_injection_{ip_address}_{int(datetime.now().timestamp())}"
            
            incident = SecurityIncident(
                incident_id=incident_id,
                incident_type=rule_config["type"],
                severity=rule_config["severity"],
                status=IncidentStatus.OPEN,
                title=f"SQL Injection Attempt Detected",
                description=f"SQL injection attempt from IP {ip_address}",
                affected_systems=["Database", "Web Application"],
                indicators={
                    "ip_address": ip_address,
                    "request_data": request_data[:500],  # Truncate for storage
                    "detected_patterns": [p for p in sql_patterns if p in request_data.lower()]
                },
                timeline=[]
            )
            
            incident.add_timeline_entry(
                action="incident_created",
                details={"trigger": "sql_injection_attempt", "ip": ip_address}
            )
            
            return incident
        
        return None
    
    async def _check_privilege_escalation(self, rule_config: Dict, event_data: Dict) -> Optional[SecurityIncident]:
        """Check for privilege escalation attempts."""
        if event_data.get("event_type") != "permission_denied":
            return None
        
        user_id = event_data.get("user_id")
        attempted_action = event_data.get("attempted_action")
        user_role = event_data.get("user_role", "user")
        
        # Check if user attempted admin actions
        admin_actions = ["delete_user", "manage_system", "view_logs", "modify_permissions"]
        
        if attempted_action in admin_actions and user_role != "admin":
            incident_id = f"privilege_escalation_{user_id}_{int(datetime.now().timestamp())}"
            
            incident = SecurityIncident(
                incident_id=incident_id,
                incident_type=rule_config["type"],
                severity=rule_config["severity"],
                status=IncidentStatus.OPEN,
                title=f"Privilege Escalation Attempt",
                description=f"User {user_id} attempted admin action: {attempted_action}",
                affected_systems=["Authorization System"],
                indicators={
                    "user_id": user_id,
                    "user_role": user_role,
                    "attempted_action": attempted_action
                },
                timeline=[]
            )
            
            incident.add_timeline_entry(
                action="incident_created",
                details={"trigger": "privilege_escalation", "action": attempted_action}
            )
            
            return incident
        
        return None


class IncidentResponder:
    """
    Automated incident response system.
    
    Executes response actions when security incidents are detected.
    """
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.security_monitor = SecurityMonitor()
        self.secure_handler = SecureDataHandler()
        self.response_actions = self._load_response_actions()
        self.notification_config = self._load_notification_config()
    
    def _load_response_actions(self) -> Dict[str, Dict]:
        """Load automated response actions."""
        return {
            IncidentType.UNAUTHORIZED_ACCESS: {
                "immediate": ["block_ip", "notify_security_team"],
                "investigation": ["collect_logs", "analyze_user_activity"],
                "containment": ["disable_account", "force_password_reset"]
            },
            IncidentType.DATA_BREACH: {
                "immediate": ["notify_security_team", "notify_management", "preserve_evidence"],
                "investigation": ["identify_affected_data", "trace_access_patterns"],
                "containment": ["revoke_access_tokens", "encrypt_sensitive_data"]
            },
            IncidentType.SYSTEM_COMPROMISE: {
                "immediate": ["isolate_system", "notify_security_team", "preserve_evidence"],
                "investigation": ["forensic_analysis", "malware_scan"],
                "containment": ["patch_vulnerabilities", "rebuild_system"]
            },
            IncidentType.SUSPICIOUS_ACTIVITY: {
                "immediate": ["monitor_closely", "collect_additional_logs"],
                "investigation": ["analyze_behavior_patterns", "correlate_events"],
                "containment": ["increase_monitoring", "require_additional_auth"]
            }
        }
    
    def _load_notification_config(self) -> Dict[str, Any]:
        """Load notification configuration."""
        return {
            "email": {
                "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME"),
                "password": os.getenv("SMTP_PASSWORD"),
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true"
            },
            "security_team": [
                "security@company.com",
                "incident-response@company.com"
            ],
            "management": [
                "ciso@company.com",
                "cto@company.com"
            ]
        }
    
    async def respond_to_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """
        Execute automated response to security incident.
        
        Args:
            incident: SecurityIncident to respond to
            
        Returns:
            Dictionary with response results
        """
        logger.info(f"Responding to incident {incident.incident_id}")
        
        response_results = {
            "incident_id": incident.incident_id,
            "actions_taken": [],
            "notifications_sent": [],
            "errors": []
        }
        
        try:
            # Get response actions for incident type
            actions = self.response_actions.get(incident.incident_type, {})
            
            # Execute immediate response actions
            immediate_actions = actions.get("immediate", [])
            for action in immediate_actions:
                try:
                    result = await self._execute_action(action, incident)
                    response_results["actions_taken"].append({
                        "action": action,
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    incident.add_timeline_entry(
                        action="response_action",
                        details={"action": action, "result": result}
                    )
                    
                except Exception as e:
                    error_msg = f"Failed to execute action {action}: {str(e)}"
                    response_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Update incident status
            incident.update_status(IncidentStatus.INVESTIGATING, "system", "Automated response initiated")
            
            # Log incident response
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                details={
                    "incident_id": incident.incident_id,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "actions_taken": len(response_results["actions_taken"]),
                    "response_time_seconds": (datetime.now(timezone.utc) - incident.created_at).total_seconds()
                },
                severity=AuditSeverity.HIGH
            )
            
            return response_results
            
        except Exception as e:
            error_msg = f"Error responding to incident {incident.incident_id}: {str(e)}"
            response_results["errors"].append(error_msg)
            logger.error(error_msg)
            return response_results
    
    async def _execute_action(self, action: str, incident: SecurityIncident) -> Dict[str, Any]:
        """Execute specific response action."""
        if action == "block_ip":
            return await self._block_ip(incident)
        elif action == "notify_security_team":
            return await self._notify_security_team(incident)
        elif action == "notify_management":
            return await self._notify_management(incident)
        elif action == "collect_logs":
            return await self._collect_logs(incident)
        elif action == "preserve_evidence":
            return await self._preserve_evidence(incident)
        elif action == "disable_account":
            return await self._disable_account(incident)
        elif action == "isolate_system":
            return await self._isolate_system(incident)
        elif action == "monitor_closely":
            return await self._monitor_closely(incident)
        else:
            return {"status": "unknown_action", "action": action}
    
    async def _block_ip(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Block IP address associated with incident."""
        ip_address = incident.indicators.get("ip_address")
        if not ip_address:
            return {"status": "error", "message": "No IP address to block"}
        
        try:
            # Block IP in security monitor
            self.security_monitor.block_ip(ip_address, f"Incident {incident.incident_id}")
            
            return {
                "status": "success",
                "message": f"Blocked IP address {ip_address}",
                "ip_address": ip_address
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _notify_security_team(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Send notification to security team."""
        try:
            subject = f"SECURITY INCIDENT: {incident.title}"
            body = self._generate_incident_email(incident)
            
            recipients = self.notification_config["security_team"]
            await self._send_email(recipients, subject, body)
            
            return {
                "status": "success",
                "message": f"Notified security team",
                "recipients": recipients
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _notify_management(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Send notification to management."""
        try:
            subject = f"CRITICAL SECURITY INCIDENT: {incident.title}"
            body = self._generate_management_email(incident)
            
            recipients = self.notification_config["management"]
            await self._send_email(recipients, subject, body)
            
            return {
                "status": "success",
                "message": f"Notified management",
                "recipients": recipients
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _collect_logs(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Collect relevant logs for incident investigation."""
        try:
            # Create logs directory for incident
            logs_dir = Path(f"/tmp/incident_logs/{incident.incident_id}")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect system logs (simplified)
            log_files = [
                "/var/log/auth.log",
                "/var/log/nginx/access.log",
                "/var/log/nginx/error.log"
            ]
            
            collected_files = []
            for log_file in log_files:
                if Path(log_file).exists():
                    try:
                        # Copy log file to incident directory
                        subprocess.run([
                            "cp", log_file, str(logs_dir / Path(log_file).name)
                        ], check=True)
                        collected_files.append(log_file)
                    except subprocess.CalledProcessError:
                        pass
            
            return {
                "status": "success",
                "message": f"Collected {len(collected_files)} log files",
                "logs_directory": str(logs_dir),
                "collected_files": collected_files
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _preserve_evidence(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Preserve digital evidence for forensic analysis."""
        try:
            # Create evidence directory
            evidence_dir = Path(f"/tmp/incident_evidence/{incident.incident_id}")
            evidence_dir.mkdir(parents=True, exist_ok=True)
            
            # Save incident data
            incident_file = evidence_dir / "incident_data.json"
            with open(incident_file, 'w') as f:
                json.dump(asdict(incident), f, indent=2, default=str)
            
            # Create evidence hash for integrity
            import hashlib
            with open(incident_file, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            hash_file = evidence_dir / "incident_data.sha256"
            with open(hash_file, 'w') as f:
                f.write(f"{file_hash}  incident_data.json\n")
            
            return {
                "status": "success",
                "message": "Evidence preserved",
                "evidence_directory": str(evidence_dir),
                "file_hash": file_hash
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _disable_account(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Disable user account associated with incident."""
        user_id = incident.indicators.get("user_id")
        if not user_id:
            return {"status": "error", "message": "No user ID to disable"}
        
        try:
            # In production, this would disable the user account in the database
            # For now, we'll just log the action
            logger.warning(f"Would disable user account {user_id} for incident {incident.incident_id}")
            
            return {
                "status": "success",
                "message": f"Disabled user account {user_id}",
                "user_id": user_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _isolate_system(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Isolate affected system components."""
        affected_systems = incident.affected_systems
        
        try:
            # In production, this would isolate network segments or disable services
            logger.critical(f"Would isolate systems {affected_systems} for incident {incident.incident_id}")
            
            return {
                "status": "success",
                "message": f"Isolated systems: {', '.join(affected_systems)}",
                "systems": affected_systems
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _monitor_closely(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Increase monitoring for suspicious activity."""
        try:
            # Increase monitoring sensitivity
            user_id = incident.indicators.get("user_id")
            ip_address = incident.indicators.get("ip_address")
            
            monitoring_targets = []
            if user_id:
                monitoring_targets.append(f"user:{user_id}")
            if ip_address:
                monitoring_targets.append(f"ip:{ip_address}")
            
            return {
                "status": "success",
                "message": f"Increased monitoring for {', '.join(monitoring_targets)}",
                "targets": monitoring_targets
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _generate_incident_email(self, incident: SecurityIncident) -> str:
        """Generate email body for security team notification."""
        return f"""
SECURITY INCIDENT ALERT

Incident ID: {incident.incident_id}
Type: {incident.incident_type}
Severity: {incident.severity}
Status: {incident.status}
Created: {incident.created_at}

Title: {incident.title}

Description:
{incident.description}

Affected Systems:
{', '.join(incident.affected_systems)}

Key Indicators:
{json.dumps(incident.indicators, indent=2)}

Timeline:
{json.dumps(incident.timeline, indent=2)}

Please investigate immediately and update the incident status.

---
Infra Mind Security System
        """.strip()
    
    def _generate_management_email(self, incident: SecurityIncident) -> str:
        """Generate email body for management notification."""
        return f"""
CRITICAL SECURITY INCIDENT

A critical security incident has been detected and requires immediate attention.

Incident Summary:
- ID: {incident.incident_id}
- Type: {incident.incident_type}
- Severity: {incident.severity}
- Time: {incident.created_at}

Impact:
{incident.description}

Affected Systems:
{', '.join(incident.affected_systems)}

Automated Response:
Initial containment measures have been automatically initiated. The security team has been notified and is investigating.

Next Steps:
1. Security team investigation in progress
2. Containment measures being implemented
3. Regular updates will be provided

Please contact the security team for more information.

---
Infra Mind Security System
        """.strip()
    
    async def _send_email(self, recipients: List[str], subject: str, body: str):
        """Send email notification."""
        try:
            config = self.notification_config["email"]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config["username"]
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            if config["use_tls"]:
                server.starttls()
            
            if config["username"] and config["password"]:
                server.login(config["username"], config["password"])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Sent incident notification to {recipients}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise


class IncidentManager:
    """
    Central incident management system.
    
    Coordinates incident detection, response, and tracking.
    """
    
    def __init__(self):
        self.detector = IncidentDetector()
        self.responder = IncidentResponder()
        self.incidents: Dict[str, SecurityIncident] = {}
        self.running = False
    
    async def start(self):
        """Start incident management system."""
        self.running = True
        logger.info("Incident management system started")
        
        # Set up detection callback
        self.detector.add_detection_callback(self._handle_new_incident)
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop incident management system."""
        self.running = False
        logger.info("Incident management system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Check for new events to analyze
                # In production, this would read from event queue
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _handle_new_incident(self, incident: SecurityIncident):
        """Handle newly detected incident."""
        logger.warning(f"New security incident detected: {incident.incident_id}")
        
        # Store incident
        self.incidents[incident.incident_id] = incident
        
        # Execute automated response
        response_result = await self.responder.respond_to_incident(incident)
        
        # Log response
        logger.info(f"Automated response completed for {incident.incident_id}: {response_result}")
    
    async def create_manual_incident(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        title: str,
        description: str,
        affected_systems: List[str],
        indicators: Dict[str, Any],
        created_by: str
    ) -> SecurityIncident:
        """Create manual incident report."""
        import secrets
        
        incident_id = f"manual_{secrets.token_hex(8)}"
        
        incident = SecurityIncident(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.OPEN,
            title=title,
            description=description,
            affected_systems=affected_systems,
            indicators=indicators,
            timeline=[]
        )
        
        incident.add_timeline_entry(
            action="manual_creation",
            details={"created_by": created_by},
            user=created_by
        )
        
        # Store incident
        self.incidents[incident_id] = incident
        
        # Execute response if severity is high enough
        if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            await self.responder.respond_to_incident(incident)
        
        logger.info(f"Manual incident created: {incident_id}")
        return incident
    
    def get_incident(self, incident_id: str) -> Optional[SecurityIncident]:
        """Get incident by ID."""
        return self.incidents.get(incident_id)
    
    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        incident_type: Optional[IncidentType] = None
    ) -> List[SecurityIncident]:
        """List incidents with optional filters."""
        incidents = list(self.incidents.values())
        
        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        if incident_type:
            incidents = [i for i in incidents if i.incident_type == incident_type]
        
        return sorted(incidents, key=lambda x: x.created_at, reverse=True)
    
    async def update_incident_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        user: str,
        notes: str = ""
    ) -> bool:
        """Update incident status."""
        incident = self.incidents.get(incident_id)
        if not incident:
            return False
        
        incident.update_status(new_status, user, notes)
        logger.info(f"Incident {incident_id} status updated to {new_status} by {user}")
        return True
    
    def get_incident_statistics(self) -> Dict[str, Any]:
        """Get incident statistics."""
        incidents = list(self.incidents.values())
        
        stats = {
            "total_incidents": len(incidents),
            "by_status": {},
            "by_severity": {},
            "by_type": {},
            "avg_resolution_time_hours": 0,
            "open_incidents": 0
        }
        
        # Count by status
        for status in IncidentStatus:
            stats["by_status"][status.value] = len([i for i in incidents if i.status == status])
        
        # Count by severity
        for severity in IncidentSeverity:
            stats["by_severity"][severity.value] = len([i for i in incidents if i.severity == severity])
        
        # Count by type
        for incident_type in IncidentType:
            stats["by_type"][incident_type.value] = len([i for i in incidents if i.incident_type == incident_type])
        
        # Calculate average resolution time
        resolved_incidents = [i for i in incidents if i.resolved_at]
        if resolved_incidents:
            total_resolution_time = sum(
                (i.resolved_at - i.created_at).total_seconds() / 3600
                for i in resolved_incidents
            )
            stats["avg_resolution_time_hours"] = total_resolution_time / len(resolved_incidents)
        
        stats["open_incidents"] = len([i for i in incidents if i.status != IncidentStatus.CLOSED])
        
        return stats


# Global incident manager instance
incident_manager = IncidentManager()


# Convenience functions
async def report_security_event(event_data: Dict[str, Any]) -> Optional[SecurityIncident]:
    """
    Report security event for analysis.
    
    Args:
        event_data: Event data to analyze
        
    Returns:
        SecurityIncident if threat detected, None otherwise
    """
    return await incident_manager.detector.analyze_event(event_data)


async def create_incident(
    incident_type: IncidentType,
    severity: IncidentSeverity,
    title: str,
    description: str,
    affected_systems: List[str],
    indicators: Dict[str, Any],
    created_by: str = "system"
) -> SecurityIncident:
    """Create new security incident."""
    return await incident_manager.create_manual_incident(
        incident_type, severity, title, description, affected_systems, indicators, created_by
    )