"""
Tests for security incident response system.

Tests automated incident detection, response workflows, and forensic capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from src.infra_mind.core.incident_response import (
    SecurityIncident, IncidentDetector, IncidentResponder, IncidentManager,
    IncidentSeverity, IncidentStatus, IncidentType,
    report_security_event, create_incident
)


class TestSecurityIncident:
    """Test SecurityIncident data structure."""
    
    def test_incident_creation(self):
        """Test creating a security incident."""
        incident = SecurityIncident(
            incident_id="test_incident_001",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Test Incident",
            description="Test incident description",
            affected_systems=["Web Server", "Database"],
            indicators={"ip_address": "192.168.1.100"},
            timeline=[]
        )
        
        assert incident.incident_id == "test_incident_001"
        assert incident.incident_type == IncidentType.UNAUTHORIZED_ACCESS
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.OPEN
        assert incident.created_at is not None
        assert incident.updated_at is not None
        assert incident.resolved_at is None
        assert len(incident.timeline) == 0
    
    def test_add_timeline_entry(self):
        """Test adding timeline entries."""
        incident = SecurityIncident(
            incident_id="test_incident_002",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            title="Data Breach",
            description="Potential data breach detected",
            affected_systems=["Database"],
            indicators={"user_id": "user123"},
            timeline=[]
        )
        
        # Add timeline entry
        incident.add_timeline_entry(
            action="incident_detected",
            details={"detection_method": "automated"},
            user="system"
        )
        
        assert len(incident.timeline) == 1
        entry = incident.timeline[0]
        assert entry["action"] == "incident_detected"
        assert entry["user"] == "system"
        assert "timestamp" in entry
        assert entry["details"]["detection_method"] == "automated"
    
    def test_update_status(self):
        """Test updating incident status."""
        incident = SecurityIncident(
            incident_id="test_incident_003",
            incident_type=IncidentType.SYSTEM_COMPROMISE,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="System Compromise",
            description="System compromise detected",
            affected_systems=["Web Server"],
            indicators={"malware_detected": True},
            timeline=[]
        )
        
        # Update status
        incident.update_status(
            IncidentStatus.INVESTIGATING,
            user="analyst1",
            notes="Starting investigation"
        )
        
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.timeline) == 1
        
        entry = incident.timeline[0]
        assert entry["action"] == "status_change"
        assert entry["user"] == "analyst1"
        assert entry["details"]["old_status"] == IncidentStatus.OPEN
        assert entry["details"]["new_status"] == IncidentStatus.INVESTIGATING
        assert entry["details"]["notes"] == "Starting investigation"
    
    def test_resolve_incident(self):
        """Test resolving an incident."""
        incident = SecurityIncident(
            incident_id="test_incident_004",
            incident_type=IncidentType.SUSPICIOUS_ACTIVITY,
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.INVESTIGATING,
            title="Suspicious Activity",
            description="Suspicious user activity",
            affected_systems=["User Management"],
            indicators={"user_id": "user456"},
            timeline=[]
        )
        
        # Resolve incident
        incident.update_status(
            IncidentStatus.RESOLVED,
            user="analyst2",
            notes="False positive - legitimate activity"
        )
        
        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolved_at is not None
        assert len(incident.timeline) == 1


class TestIncidentDetector:
    """Test IncidentDetector functionality."""
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = IncidentDetector()
        
        assert detector.detection_rules is not None
        assert "failed_login_threshold" in detector.detection_rules
        assert "sql_injection_attempt" in detector.detection_rules
        assert len(detector.active_incidents) == 0
        assert len(detector.detection_callbacks) == 0
    
    def test_add_detection_callback(self):
        """Test adding detection callbacks."""
        detector = IncidentDetector()
        
        def test_callback(incident):
            pass
        
        detector.add_detection_callback(test_callback)
        assert len(detector.detection_callbacks) == 1
        assert detector.detection_callbacks[0] == test_callback
    
    @pytest.mark.asyncio
    async def test_failed_login_threshold_detection(self):
        """Test failed login threshold detection."""
        detector = IncidentDetector()
        
        # Mock event data for failed login
        event_data = {
            "event_type": "login_failure",
            "ip_address": "192.168.1.100",
            "user_id": "user123",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should detect incident (mocked to always trigger)
        assert incident is not None
        assert incident.incident_type == IncidentType.UNAUTHORIZED_ACCESS
        assert incident.severity == IncidentSeverity.HIGH
        assert "192.168.1.100" in incident.title
        assert incident.indicators["ip_address"] == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_admin_access_anomaly_detection(self):
        """Test admin access anomaly detection."""
        detector = IncidentDetector()
        
        # Mock event data for admin access outside business hours
        event_data = {
            "event_type": "login_success",
            "user_role": "admin",
            "user_id": "admin123",
            "ip_address": "10.0.0.50",
            "timestamp": datetime.now(timezone.utc).replace(hour=2).isoformat()  # 2 AM
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should detect anomaly
        assert incident is not None
        assert incident.incident_type == IncidentType.SUSPICIOUS_ACTIVITY
        assert incident.severity == IncidentSeverity.HIGH
        assert "Admin Access Outside Business Hours" in incident.title
        assert incident.indicators["user_id"] == "admin123"
        assert incident.indicators["hour"] == 2
    
    @pytest.mark.asyncio
    async def test_data_export_volume_detection(self):
        """Test large data export detection."""
        detector = IncidentDetector()
        
        # Mock event data for large data export
        event_data = {
            "action": "data_export",
            "user_id": "user789",
            "export_size_mb": 2000,  # Above threshold
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should detect large export
        assert incident is not None
        assert incident.incident_type == IncidentType.DATA_BREACH
        assert incident.severity == IncidentSeverity.CRITICAL
        assert "Large Data Export Detected" in incident.title
        assert incident.indicators["export_size_mb"] == 2000
        assert incident.indicators["user_id"] == "user789"
    
    @pytest.mark.asyncio
    async def test_sql_injection_detection(self):
        """Test SQL injection attempt detection."""
        detector = IncidentDetector()
        
        # Mock event data with SQL injection payload
        event_data = {
            "event_type": "web_request",
            "request_data": "username=admin' OR '1'='1&password=test",
            "ip_address": "203.0.113.10",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should detect SQL injection
        assert incident is not None
        assert incident.incident_type == IncidentType.SYSTEM_COMPROMISE
        assert incident.severity == IncidentSeverity.CRITICAL
        assert "SQL Injection Attempt Detected" in incident.title
        assert incident.indicators["ip_address"] == "203.0.113.10"
        assert "' or '1'='1" in incident.indicators["detected_patterns"]
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_detection(self):
        """Test privilege escalation detection."""
        detector = IncidentDetector()
        
        # Mock event data for privilege escalation attempt
        event_data = {
            "event_type": "permission_denied",
            "user_id": "user456",
            "user_role": "user",
            "attempted_action": "delete_user",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should detect privilege escalation
        assert incident is not None
        assert incident.incident_type == IncidentType.SYSTEM_COMPROMISE
        assert incident.severity == IncidentSeverity.CRITICAL
        assert "Privilege Escalation Attempt" in incident.title
        assert incident.indicators["user_id"] == "user456"
        assert incident.indicators["attempted_action"] == "delete_user"
    
    @pytest.mark.asyncio
    async def test_no_incident_detection(self):
        """Test normal events don't trigger incidents."""
        detector = IncidentDetector()
        
        # Mock normal event data
        event_data = {
            "event_type": "login_success",
            "user_id": "user123",
            "ip_address": "192.168.1.50",
            "timestamp": datetime.now(timezone.utc).replace(hour=10).isoformat()  # Business hours
        }
        
        # Analyze event
        incident = await detector.analyze_event(event_data)
        
        # Should not detect incident
        assert incident is None
    
    @pytest.mark.asyncio
    async def test_error_handling_in_detection(self):
        """Test error handling during detection."""
        detector = IncidentDetector()
        
        # Mock invalid event data
        event_data = {
            "invalid_field": "invalid_value"
        }
        
        # Should handle gracefully
        incident = await detector.analyze_event(event_data)
        assert incident is None


class TestIncidentResponder:
    """Test IncidentResponder functionality."""
    
    def test_responder_initialization(self):
        """Test responder initialization."""
        responder = IncidentResponder()
        
        assert responder.response_actions is not None
        assert IncidentType.UNAUTHORIZED_ACCESS in responder.response_actions
        assert responder.notification_config is not None
    
    @pytest.mark.asyncio
    async def test_respond_to_unauthorized_access(self):
        """Test response to unauthorized access incident."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_response_001",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Unauthorized Access Attempt",
            description="Multiple failed login attempts",
            affected_systems=["Authentication System"],
            indicators={"ip_address": "192.168.1.100"},
            timeline=[]
        )
        
        # Mock security monitor
        with patch.object(responder.security_monitor, 'block_ip') as mock_block_ip:
            mock_block_ip.return_value = None
            
            # Mock email sending
            with patch.object(responder, '_send_email') as mock_send_email:
                mock_send_email.return_value = None
                
                # Execute response
                result = await responder.respond_to_incident(incident)
        
        # Verify response
        assert result["incident_id"] == "test_response_001"
        assert len(result["actions_taken"]) > 0
        assert len(result["errors"]) == 0
        
        # Check that IP was blocked
        action_names = [action["action"] for action in result["actions_taken"]]
        assert "block_ip" in action_names
        assert "notify_security_team" in action_names
        
        # Verify incident status updated
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.timeline) > 0
    
    @pytest.mark.asyncio
    async def test_respond_to_data_breach(self):
        """Test response to data breach incident."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_response_002",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            title="Data Breach Detected",
            description="Large data export detected",
            affected_systems=["Database", "Export System"],
            indicators={"user_id": "user123", "export_size_mb": 2000},
            timeline=[]
        )
        
        # Mock email sending
        with patch.object(responder, '_send_email') as mock_send_email:
            mock_send_email.return_value = None
            
            # Mock evidence preservation
            with patch.object(responder, '_preserve_evidence') as mock_preserve:
                mock_preserve.return_value = {"status": "success", "message": "Evidence preserved"}
                
                # Execute response
                result = await responder.respond_to_incident(incident)
        
        # Verify response
        assert result["incident_id"] == "test_response_002"
        assert len(result["actions_taken"]) > 0
        
        # Check that management was notified for critical incident
        action_names = [action["action"] for action in result["actions_taken"]]
        assert "notify_security_team" in action_names
        assert "notify_management" in action_names
        assert "preserve_evidence" in action_names
    
    @pytest.mark.asyncio
    async def test_block_ip_action(self):
        """Test IP blocking action."""
        responder = IncidentResponder()
        
        # Create incident with IP address
        incident = SecurityIncident(
            incident_id="test_block_ip",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Block IP Test",
            description="Test IP blocking",
            affected_systems=["Web Server"],
            indicators={"ip_address": "192.168.1.200"},
            timeline=[]
        )
        
        # Mock security monitor
        with patch.object(responder.security_monitor, 'block_ip') as mock_block_ip:
            mock_block_ip.return_value = None
            
            # Execute block IP action
            result = await responder._block_ip(incident)
        
        # Verify result
        assert result["status"] == "success"
        assert result["ip_address"] == "192.168.1.200"
        mock_block_ip.assert_called_once_with("192.168.1.200", "Incident test_block_ip")
    
    @pytest.mark.asyncio
    async def test_block_ip_no_address(self):
        """Test IP blocking when no IP address available."""
        responder = IncidentResponder()
        
        # Create incident without IP address
        incident = SecurityIncident(
            incident_id="test_no_ip",
            incident_type=IncidentType.SUSPICIOUS_ACTIVITY,
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.OPEN,
            title="No IP Test",
            description="Test without IP",
            affected_systems=["System"],
            indicators={},
            timeline=[]
        )
        
        # Execute block IP action
        result = await responder._block_ip(incident)
        
        # Should return error
        assert result["status"] == "error"
        assert "No IP address to block" in result["message"]
    
    @pytest.mark.asyncio
    async def test_collect_logs_action(self):
        """Test log collection action."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_logs",
            incident_type=IncidentType.SYSTEM_COMPROMISE,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Log Collection Test",
            description="Test log collection",
            affected_systems=["Web Server"],
            indicators={},
            timeline=[]
        )
        
        # Mock subprocess and file operations
        with patch('subprocess.run') as mock_subprocess:
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = True
                mock_subprocess.return_value = None
                
                # Execute log collection
                result = await responder._collect_logs(incident)
        
        # Verify result
        assert result["status"] == "success"
        assert "logs_directory" in result
        assert "collected_files" in result
    
    @pytest.mark.asyncio
    async def test_preserve_evidence_action(self):
        """Test evidence preservation action."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_evidence",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            title="Evidence Test",
            description="Test evidence preservation",
            affected_systems=["Database"],
            indicators={"user_id": "user123"},
            timeline=[]
        )
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                mock_mkdir.return_value = None
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                # Execute evidence preservation
                result = await responder._preserve_evidence(incident)
        
        # Verify result
        assert result["status"] == "success"
        assert "evidence_directory" in result
        assert "file_hash" in result
    
    def test_generate_incident_email(self):
        """Test incident email generation."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_email",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Email Test",
            description="Test email generation",
            affected_systems=["Web Server"],
            indicators={"ip_address": "192.168.1.100"},
            timeline=[{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "incident_created",
                "details": {"trigger": "test"},
                "user": "system"
            }]
        )
        
        # Generate email
        email_body = responder._generate_incident_email(incident)
        
        # Verify email content
        assert "SECURITY INCIDENT ALERT" in email_body
        assert incident.incident_id in email_body
        assert incident.title in email_body
        assert incident.description in email_body
        assert "192.168.1.100" in email_body
    
    def test_generate_management_email(self):
        """Test management email generation."""
        responder = IncidentResponder()
        
        # Create critical incident
        incident = SecurityIncident(
            incident_id="test_mgmt_email",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            title="Critical Breach",
            description="Critical data breach",
            affected_systems=["Database"],
            indicators={"affected_records": 10000},
            timeline=[]
        )
        
        # Generate management email
        email_body = responder._generate_management_email(incident)
        
        # Verify email content
        assert "CRITICAL SECURITY INCIDENT" in email_body
        assert incident.incident_id in email_body
        assert incident.description in email_body
        assert "Next Steps:" in email_body


class TestIncidentManager:
    """Test IncidentManager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = IncidentManager()
        
        assert manager.detector is not None
        assert manager.responder is not None
        assert len(manager.incidents) == 0
        assert manager.running is False
    
    @pytest.mark.asyncio
    async def test_create_manual_incident(self):
        """Test creating manual incident."""
        manager = IncidentManager()
        
        # Create manual incident
        incident = await manager.create_manual_incident(
            incident_type=IncidentType.SUSPICIOUS_ACTIVITY,
            severity=IncidentSeverity.MEDIUM,
            title="Manual Test Incident",
            description="Manually created test incident",
            affected_systems=["Test System"],
            indicators={"test_indicator": "test_value"},
            created_by="test_user"
        )
        
        # Verify incident
        assert incident.incident_id.startswith("manual_")
        assert incident.incident_type == IncidentType.SUSPICIOUS_ACTIVITY
        assert incident.severity == IncidentSeverity.MEDIUM
        assert incident.title == "Manual Test Incident"
        assert len(incident.timeline) == 1
        assert incident.timeline[0]["action"] == "manual_creation"
        assert incident.timeline[0]["user"] == "test_user"
        
        # Verify incident stored
        assert incident.incident_id in manager.incidents
    
    @pytest.mark.asyncio
    async def test_create_critical_manual_incident_triggers_response(self):
        """Test that critical manual incidents trigger automated response."""
        manager = IncidentManager()
        
        # Mock responder
        with patch.object(manager.responder, 'respond_to_incident') as mock_respond:
            mock_respond.return_value = {"actions_taken": [], "errors": []}
            
            # Create critical incident
            incident = await manager.create_manual_incident(
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.CRITICAL,
                title="Critical Manual Incident",
                description="Critical incident requiring immediate response",
                affected_systems=["Database"],
                indicators={"severity": "critical"},
                created_by="security_analyst"
            )
        
        # Verify response was triggered
        mock_respond.assert_called_once_with(incident)
    
    def test_get_incident(self):
        """Test getting incident by ID."""
        manager = IncidentManager()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_get_incident",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Get Test",
            description="Test getting incident",
            affected_systems=["System"],
            indicators={},
            timeline=[]
        )
        
        # Store incident
        manager.incidents[incident.incident_id] = incident
        
        # Get incident
        retrieved = manager.get_incident("test_get_incident")
        assert retrieved == incident
        
        # Get non-existent incident
        not_found = manager.get_incident("non_existent")
        assert not_found is None
    
    def test_list_incidents(self):
        """Test listing incidents with filters."""
        manager = IncidentManager()
        
        # Create test incidents
        incidents = [
            SecurityIncident(
                incident_id="incident_1",
                incident_type=IncidentType.UNAUTHORIZED_ACCESS,
                severity=IncidentSeverity.HIGH,
                status=IncidentStatus.OPEN,
                title="Incident 1",
                description="First incident",
                affected_systems=["System1"],
                indicators={},
                timeline=[]
            ),
            SecurityIncident(
                incident_id="incident_2",
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.CRITICAL,
                status=IncidentStatus.INVESTIGATING,
                title="Incident 2",
                description="Second incident",
                affected_systems=["System2"],
                indicators={},
                timeline=[]
            ),
            SecurityIncident(
                incident_id="incident_3",
                incident_type=IncidentType.UNAUTHORIZED_ACCESS,
                severity=IncidentSeverity.MEDIUM,
                status=IncidentStatus.RESOLVED,
                title="Incident 3",
                description="Third incident",
                affected_systems=["System3"],
                indicators={},
                timeline=[]
            )
        ]
        
        # Store incidents
        for incident in incidents:
            manager.incidents[incident.incident_id] = incident
        
        # Test listing all incidents
        all_incidents = manager.list_incidents()
        assert len(all_incidents) == 3
        
        # Test filtering by status
        open_incidents = manager.list_incidents(status=IncidentStatus.OPEN)
        assert len(open_incidents) == 1
        assert open_incidents[0].incident_id == "incident_1"
        
        # Test filtering by severity
        critical_incidents = manager.list_incidents(severity=IncidentSeverity.CRITICAL)
        assert len(critical_incidents) == 1
        assert critical_incidents[0].incident_id == "incident_2"
        
        # Test filtering by type
        access_incidents = manager.list_incidents(incident_type=IncidentType.UNAUTHORIZED_ACCESS)
        assert len(access_incidents) == 2
        
        # Test multiple filters
        high_open = manager.list_incidents(
            status=IncidentStatus.OPEN,
            severity=IncidentSeverity.HIGH
        )
        assert len(high_open) == 1
        assert high_open[0].incident_id == "incident_1"
    
    @pytest.mark.asyncio
    async def test_update_incident_status(self):
        """Test updating incident status."""
        manager = IncidentManager()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_update_status",
            incident_type=IncidentType.SUSPICIOUS_ACTIVITY,
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.OPEN,
            title="Status Update Test",
            description="Test status update",
            affected_systems=["System"],
            indicators={},
            timeline=[]
        )
        
        # Store incident
        manager.incidents[incident.incident_id] = incident
        
        # Update status
        success = await manager.update_incident_status(
            "test_update_status",
            IncidentStatus.INVESTIGATING,
            "analyst1",
            "Starting investigation"
        )
        
        # Verify update
        assert success is True
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.timeline) == 1
        assert incident.timeline[0]["user"] == "analyst1"
        
        # Test updating non-existent incident
        not_found = await manager.update_incident_status(
            "non_existent",
            IncidentStatus.RESOLVED,
            "analyst1"
        )
        assert not_found is False
    
    def test_get_incident_statistics(self):
        """Test incident statistics generation."""
        manager = IncidentManager()
        
        # Create test incidents with different properties
        incidents = [
            SecurityIncident(
                incident_id="stats_1",
                incident_type=IncidentType.UNAUTHORIZED_ACCESS,
                severity=IncidentSeverity.HIGH,
                status=IncidentStatus.OPEN,
                title="Stats 1",
                description="Stats incident 1",
                affected_systems=["System1"],
                indicators={},
                timeline=[],
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
                resolved_at=datetime.now(timezone.utc) - timedelta(hours=1)
            ),
            SecurityIncident(
                incident_id="stats_2",
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.CRITICAL,
                status=IncidentStatus.INVESTIGATING,
                title="Stats 2",
                description="Stats incident 2",
                affected_systems=["System2"],
                indicators={},
                timeline=[]
            ),
            SecurityIncident(
                incident_id="stats_3",
                incident_type=IncidentType.UNAUTHORIZED_ACCESS,
                severity=IncidentSeverity.MEDIUM,
                status=IncidentStatus.RESOLVED,
                title="Stats 3",
                description="Stats incident 3",
                affected_systems=["System3"],
                indicators={},
                timeline=[],
                created_at=datetime.now(timezone.utc) - timedelta(hours=4),
                resolved_at=datetime.now(timezone.utc) - timedelta(hours=2)
            )
        ]
        
        # Store incidents
        for incident in incidents:
            manager.incidents[incident.incident_id] = incident
        
        # Get statistics
        stats = manager.get_incident_statistics()
        
        # Verify statistics
        assert stats["total_incidents"] == 3
        assert stats["by_status"]["open"] == 1
        assert stats["by_status"]["investigating"] == 1
        assert stats["by_status"]["resolved"] == 1
        assert stats["by_severity"]["high"] == 1
        assert stats["by_severity"]["critical"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_type"]["unauthorized_access"] == 2
        assert stats["by_type"]["data_breach"] == 1
        assert stats["open_incidents"] == 2  # Open + Investigating
        assert stats["avg_resolution_time_hours"] > 0  # Should have calculated average


class TestIncidentResponseIntegration:
    """Test incident response integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_incident_workflow(self):
        """Test complete incident detection and response workflow."""
        manager = IncidentManager()
        
        # Mock responder to avoid actual actions
        with patch.object(manager.responder, 'respond_to_incident') as mock_respond:
            mock_respond.return_value = {
                "incident_id": "test_workflow",
                "actions_taken": [
                    {"action": "block_ip", "result": {"status": "success"}},
                    {"action": "notify_security_team", "result": {"status": "success"}}
                ],
                "errors": []
            }
            
            # Simulate event that triggers incident
            event_data = {
                "event_type": "login_failure",
                "ip_address": "192.168.1.100",
                "user_id": "user123",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Detect incident
            incident = await manager.detector.analyze_event(event_data)
            
            # Verify incident detected
            assert incident is not None
            assert incident.incident_type == IncidentType.UNAUTHORIZED_ACCESS
            
            # Manually trigger response (in real system, this would be automatic)
            await manager._handle_new_incident(incident)
            
            # Verify incident stored and response triggered
            assert incident.incident_id in manager.incidents
            mock_respond.assert_called_once_with(incident)
    
    @pytest.mark.asyncio
    async def test_report_security_event_convenience_function(self):
        """Test convenience function for reporting security events."""
        # Mock the global incident manager
        with patch('src.infra_mind.core.incident_response.incident_manager') as mock_manager:
            mock_detector = AsyncMock()
            mock_incident = SecurityIncident(
                incident_id="convenience_test",
                incident_type=IncidentType.SUSPICIOUS_ACTIVITY,
                severity=IncidentSeverity.MEDIUM,
                status=IncidentStatus.OPEN,
                title="Convenience Test",
                description="Test convenience function",
                affected_systems=["System"],
                indicators={},
                timeline=[]
            )
            mock_detector.analyze_event.return_value = mock_incident
            mock_manager.detector = mock_detector
            
            # Use convenience function
            event_data = {"event_type": "test_event"}
            result = await report_security_event(event_data)
            
            # Verify function worked
            mock_detector.analyze_event.assert_called_once_with(event_data)
            assert result == mock_incident
    
    @pytest.mark.asyncio
    async def test_create_incident_convenience_function(self):
        """Test convenience function for creating incidents."""
        # Mock the global incident manager
        with patch('src.infra_mind.core.incident_response.incident_manager') as mock_manager:
            mock_incident = SecurityIncident(
                incident_id="convenience_create",
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.HIGH,
                status=IncidentStatus.OPEN,
                title="Convenience Create",
                description="Test convenience create",
                affected_systems=["Database"],
                indicators={"test": "data"},
                timeline=[]
            )
            mock_manager.create_manual_incident.return_value = mock_incident
            
            # Use convenience function
            result = await create_incident(
                incident_type=IncidentType.DATA_BREACH,
                severity=IncidentSeverity.HIGH,
                title="Convenience Create",
                description="Test convenience create",
                affected_systems=["Database"],
                indicators={"test": "data"},
                created_by="test_user"
            )
            
            # Verify function worked
            mock_manager.create_manual_incident.assert_called_once()
            assert result == mock_incident
    
    def test_incident_enums(self):
        """Test incident enum values."""
        # Test IncidentSeverity
        assert IncidentSeverity.CRITICAL == "critical"
        assert IncidentSeverity.HIGH == "high"
        assert IncidentSeverity.MEDIUM == "medium"
        assert IncidentSeverity.LOW == "low"
        
        # Test IncidentStatus
        assert IncidentStatus.OPEN == "open"
        assert IncidentStatus.INVESTIGATING == "investigating"
        assert IncidentStatus.CONTAINED == "contained"
        assert IncidentStatus.RESOLVED == "resolved"
        assert IncidentStatus.CLOSED == "closed"
        
        # Test IncidentType
        assert IncidentType.UNAUTHORIZED_ACCESS == "unauthorized_access"
        assert IncidentType.DATA_BREACH == "data_breach"
        assert IncidentType.MALWARE_DETECTION == "malware_detection"
        assert IncidentType.DDOS_ATTACK == "ddos_attack"
        assert IncidentType.INSIDER_THREAT == "insider_threat"
        assert IncidentType.SYSTEM_COMPROMISE == "system_compromise"
        assert IncidentType.COMPLIANCE_VIOLATION == "compliance_violation"
        assert IncidentType.SUSPICIOUS_ACTIVITY == "suspicious_activity"


class TestIncidentResponseErrorHandling:
    """Test error handling in incident response system."""
    
    @pytest.mark.asyncio
    async def test_detector_error_handling(self):
        """Test detector handles errors gracefully."""
        detector = IncidentDetector()
        
        # Test with malformed event data
        malformed_data = {"invalid": "data", "timestamp": "not_a_date"}
        
        # Should not raise exception
        incident = await detector.analyze_event(malformed_data)
        assert incident is None
    
    @pytest.mark.asyncio
    async def test_responder_action_failure(self):
        """Test responder handles action failures."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_failure",
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            title="Failure Test",
            description="Test action failure",
            affected_systems=["System"],
            indicators={"ip_address": "192.168.1.100"},
            timeline=[]
        )
        
        # Mock security monitor to raise exception
        with patch.object(responder.security_monitor, 'block_ip') as mock_block_ip:
            mock_block_ip.side_effect = Exception("Network error")
            
            # Execute response
            result = await responder.respond_to_incident(incident)
        
        # Should handle error gracefully
        assert result["incident_id"] == "test_failure"
        assert len(result["errors"]) > 0
        assert "Failed to execute action block_ip" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_email_notification_failure(self):
        """Test email notification failure handling."""
        responder = IncidentResponder()
        
        # Create test incident
        incident = SecurityIncident(
            incident_id="test_email_failure",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            title="Email Failure Test",
            description="Test email failure",
            affected_systems=["System"],
            indicators={},
            timeline=[]
        )
        
        # Mock email sending to fail
        with patch.object(responder, '_send_email') as mock_send_email:
            mock_send_email.side_effect = Exception("SMTP server unavailable")
            
            # Execute notification
            result = await responder._notify_security_team(incident)
        
        # Should return error status
        assert result["status"] == "error"
        assert "SMTP server unavailable" in result["message"]