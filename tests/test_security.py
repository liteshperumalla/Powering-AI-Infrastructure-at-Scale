"""
Tests for security and encryption systems.

Tests encryption, input validation, audit logging, and security monitoring.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.infra_mind.core.encryption import (
    DataEncryption, FernetEncryption, SecureDataHandler, EncryptionError
)
from src.infra_mind.core.security import (
    InputValidator, SecurityHeaders, RateLimiter, SecurityMonitor, SecurityError
)
from src.infra_mind.core.audit import (
    AuditLogger, AuditEvent, AuditEventType, AuditSeverity, ComplianceLogger
)


class TestDataEncryption:
    """Test AES-256 encryption functionality."""
    
    def test_encryption_decryption(self):
        """Test basic encryption and decryption."""
        # Create encryption instance with test key
        test_key = b'0' * 32  # 32-byte key for AES-256
        encryption = DataEncryption(test_key)
        
        # Test data
        original_data = "This is sensitive data that needs encryption"
        
        # Encrypt
        encrypted = encryption.encrypt(original_data)
        assert isinstance(encrypted, str)
        assert encrypted != original_data
        assert len(encrypted) > len(original_data)  # Base64 encoding increases size
        
        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_bytes(self):
        """Test encryption of bytes data."""
        test_key = b'1' * 32
        encryption = DataEncryption(test_key)
        
        original_data = b"Binary data to encrypt"
        
        encrypted = encryption.encrypt(original_data)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original_data.decode('utf-8')
    
    def test_encrypt_dict_fields(self):
        """Test encrypting specific fields in a dictionary."""
        test_key = b'2' * 32
        encryption = DataEncryption(test_key)
        
        original_dict = {
            "name": "John Doe",
            "email": "john@example.com",
            "api_key": "secret_api_key_123",
            "public_info": "This is public"
        }
        
        # Encrypt sensitive fields
        encrypted_dict = encryption.encrypt_dict(original_dict, ["api_key"])
        
        # Check that sensitive field is encrypted
        assert encrypted_dict["api_key"] != original_dict["api_key"]
        assert encrypted_dict["api_key_encrypted"] is True
        
        # Check that other fields are unchanged
        assert encrypted_dict["name"] == original_dict["name"]
        assert encrypted_dict["email"] == original_dict["email"]
        
        # Decrypt
        decrypted_dict = encryption.decrypt_dict(encrypted_dict, ["api_key"])
        assert decrypted_dict["api_key"] == original_dict["api_key"]
        assert "api_key_encrypted" not in decrypted_dict
    
    def test_invalid_key_length(self):
        """Test that invalid key length raises error."""
        with pytest.raises(EncryptionError, match="must be 32 bytes"):
            DataEncryption(b'short_key')
    
    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data."""
        test_key = b'3' * 32
        encryption = DataEncryption(test_key)
        
        with pytest.raises(EncryptionError, match="Decryption failed"):
            encryption.decrypt("invalid_encrypted_data")


class TestFernetEncryption:
    """Test Fernet encryption functionality."""
    
    def test_fernet_encryption_decryption(self):
        """Test Fernet encryption and decryption."""
        from cryptography.fernet import Fernet
        
        # Create Fernet instance with test key
        test_key = Fernet.generate_key()
        fernet_encryption = FernetEncryption(test_key)
        
        original_data = "Test data for Fernet encryption"
        
        # Encrypt
        encrypted = fernet_encryption.encrypt(original_data)
        assert isinstance(encrypted, str)
        assert encrypted != original_data
        
        # Decrypt
        decrypted = fernet_encryption.decrypt(encrypted)
        assert decrypted == original_data


class TestSecureDataHandler:
    """Test secure data handling utilities."""
    
    def test_encrypt_sensitive_fields(self):
        """Test encryption of sensitive fields."""
        handler = SecureDataHandler()
        
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "api_key": "secret_key_123",
            "phone_number": "555-1234",
            "public_data": "This is public"
        }
        
        encrypted_data = handler.encrypt_sensitive_fields(data)
        
        # Sensitive fields should be encrypted
        assert encrypted_data["api_key"] != data["api_key"]
        assert encrypted_data["phone_number"] != data["phone_number"]
        assert encrypted_data["api_key_encrypted"] is True
        assert encrypted_data["phone_number_encrypted"] is True
        
        # Non-sensitive fields should be unchanged
        assert encrypted_data["name"] == data["name"]
        assert encrypted_data["email"] == data["email"]
        assert encrypted_data["public_data"] == data["public_data"]
    
    def test_secure_compare(self):
        """Test timing-safe string comparison."""
        handler = SecureDataHandler()
        
        # Same strings should match
        assert handler.secure_compare("test123", "test123") is True
        
        # Different strings should not match
        assert handler.secure_compare("test123", "test456") is False
        
        # Different lengths should not match
        assert handler.secure_compare("short", "much_longer_string") is False
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        handler = SecureDataHandler()
        
        token1 = handler.generate_secure_token()
        token2 = handler.generate_secure_token()
        
        # Tokens should be different
        assert token1 != token2
        
        # Tokens should be strings
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        
        # Tokens should have reasonable length
        assert len(token1) > 20
        assert len(token2) > 20
    
    def test_hash_sensitive_data(self):
        """Test sensitive data hashing."""
        handler = SecureDataHandler()
        
        data = "sensitive_information"
        hash1, salt1 = handler.hash_sensitive_data(data)
        hash2, salt2 = handler.hash_sensitive_data(data)
        
        # Different salts should produce different hashes
        assert hash1 != hash2
        assert salt1 != salt2
        
        # Same data with same salt should produce same hash
        hash3, _ = handler.hash_sensitive_data(data, salt=salt1.encode())
        # Note: We need to decode the base64 salt first
        import base64
        decoded_salt = base64.b64decode(salt1.encode())
        hash3, _ = handler.hash_sensitive_data(data, salt=decoded_salt)
        assert hash3 == hash1


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        assert InputValidator.validate_email("test@example.com") is True
        assert InputValidator.validate_email("user.name+tag@domain.co.uk") is True
        
        # Invalid emails
        assert InputValidator.validate_email("invalid-email") is False
        assert InputValidator.validate_email("@domain.com") is False
        assert InputValidator.validate_email("user@") is False
        assert InputValidator.validate_email("") is False
        assert InputValidator.validate_email("a" * 255 + "@domain.com") is False
    
    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        assert InputValidator.validate_url("https://example.com") is True
        assert InputValidator.validate_url("http://subdomain.example.com/path") is True
        
        # Invalid URLs
        assert InputValidator.validate_url("ftp://example.com") is False
        assert InputValidator.validate_url("javascript:alert('xss')") is False
        assert InputValidator.validate_url("http://localhost") is False
        assert InputValidator.validate_url("http://127.0.0.1") is False
        assert InputValidator.validate_url("") is False
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        # Suspicious patterns
        assert InputValidator.check_sql_injection("SELECT * FROM users") is True
        assert InputValidator.check_sql_injection("'; DROP TABLE users; --") is True
        assert InputValidator.check_sql_injection("1 OR 1=1") is True
        assert InputValidator.check_sql_injection("UNION SELECT password FROM users") is True
        
        # Safe strings
        assert InputValidator.check_sql_injection("Hello world") is False
        assert InputValidator.check_sql_injection("user@example.com") is False
        assert InputValidator.check_sql_injection("") is False
    
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        # Suspicious patterns
        assert InputValidator.check_xss("<script>alert('xss')</script>") is True
        assert InputValidator.check_xss("javascript:alert('xss')") is True
        assert InputValidator.check_xss("<img onload='alert(1)'>") is True
        assert InputValidator.check_xss("<iframe src='evil.com'></iframe>") is True
        
        # Safe strings
        assert InputValidator.check_xss("Hello <b>world</b>") is False
        assert InputValidator.check_xss("user@example.com") is False
        assert InputValidator.check_xss("") is False
    
    def test_string_sanitization(self):
        """Test string sanitization."""
        # HTML escaping
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
        
        # Length truncation
        long_string = "a" * 2000
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
        
        # Null byte removal
        result = InputValidator.sanitize_string("test\x00null")
        assert "\x00" not in result
        
        # Whitespace normalization
        result = InputValidator.sanitize_string("  multiple   spaces  ")
        assert result == "multiple spaces"
    
    def test_validate_and_sanitize_dict(self):
        """Test dictionary validation and sanitization."""
        schema = {
            "name": {"type": "string", "required": True, "max_length": 50},
            "email": {"type": "email", "required": True},
            "age": {"type": "integer", "required": False},
            "website": {"type": "url", "required": False},
            "active": {"type": "boolean", "required": False}
        }
        
        # Valid data
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": "30",
            "website": "https://johndoe.com",
            "active": "true"
        }
        
        result = InputValidator.validate_and_sanitize_dict(data, schema)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["age"] == 30
        assert result["website"] == "https://johndoe.com"
        assert result["active"] is True
        
        # Invalid data should raise SecurityError
        invalid_data = {
            "name": "<script>alert('xss')</script>",
            "email": "invalid-email"
        }
        
        with pytest.raises(SecurityError):
            InputValidator.validate_and_sanitize_dict(invalid_data, schema)


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiting(self):
        """Test basic rate limiting."""
        limiter = RateLimiter()
        
        # First few requests should be allowed
        for i in range(5):
            assert limiter.is_rate_limited("test_ip", limit=5, window_seconds=60) is False
        
        # Next request should be rate limited
        assert limiter.is_rate_limited("test_ip", limit=5, window_seconds=60) is True
    
    def test_rate_limit_window(self):
        """Test rate limiting time window."""
        limiter = RateLimiter()
        
        # Make requests at different times
        current_time = 1000.0
        
        # Fill up the limit
        for i in range(5):
            assert limiter.is_rate_limited(
                "test_ip", limit=5, window_seconds=60, current_time=current_time + i
            ) is False
        
        # Should be rate limited
        assert limiter.is_rate_limited(
            "test_ip", limit=5, window_seconds=60, current_time=current_time + 5
        ) is True
        
        # After window expires, should be allowed again
        assert limiter.is_rate_limited(
            "test_ip", limit=5, window_seconds=60, current_time=current_time + 70
        ) is False
    
    def test_rate_limit_info(self):
        """Test rate limit information."""
        limiter = RateLimiter()
        
        # Initial state
        info = limiter.get_rate_limit_info("test_ip", limit=10, window_seconds=60)
        assert info["limit"] == 10
        assert info["remaining"] == 10
        
        # After some requests
        for i in range(3):
            limiter.is_rate_limited("test_ip", limit=10, window_seconds=60)
        
        info = limiter.get_rate_limit_info("test_ip", limit=10, window_seconds=60)
        assert info["remaining"] == 7


class TestAuditLogger:
    """Test audit logging functionality."""
    
    def test_audit_event_creation(self):
        """Test audit event creation."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
            outcome="success",
            severity=AuditSeverity.MEDIUM
        )
        
        assert event.event_type == AuditEventType.LOGIN_SUCCESS
        assert event.user_id == "user123"
        assert event.outcome == "success"
        assert event.severity == AuditSeverity.MEDIUM
    
    def test_audit_event_serialization(self):
        """Test audit event serialization."""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESSED,
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            resource_type="assessment",
            resource_id="assessment456",
            action="read"
        )
        
        # Test to_dict
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict["event_type"] == "data_accessed"
        assert event_dict["user_id"] == "user123"
        assert isinstance(event_dict["timestamp"], str)
        
        # Test to_json
        event_json = event.to_json()
        assert isinstance(event_json, str)
        
        # Should be valid JSON
        parsed = json.loads(event_json)
        assert parsed["event_type"] == "data_accessed"
    
    def test_audit_logger_logging(self):
        """Test audit logger functionality."""
        # Create logger with no file handler for testing
        logger = AuditLogger()
        
        # Test authentication logging
        logger.log_authentication(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
            outcome="success"
        )
        
        # Test data access logging
        logger.log_data_access(
            user_id="user123",
            resource_type="assessment",
            resource_id="assessment456",
            action="read",
            ip_address="192.168.1.1"
        )
        
        # Test security event logging
        logger.log_security_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_id="user123",
            ip_address="192.168.1.1",
            details={"reason": "invalid_token"},
            severity=AuditSeverity.HIGH
        )
        
        # If we get here without exceptions, logging is working


class TestSecurityMonitor:
    """Test security monitoring functionality."""
    
    def test_suspicious_user_agent_detection(self):
        """Test suspicious user agent detection."""
        monitor = SecurityMonitor()
        
        # Suspicious user agents
        assert monitor.is_suspicious_user_agent("sqlmap/1.0") is True
        assert monitor.is_suspicious_user_agent("python-requests/2.25.1") is True
        assert monitor.is_suspicious_user_agent("curl/7.68.0") is True
        assert monitor.is_suspicious_user_agent("") is True
        
        # Normal user agents
        assert monitor.is_suspicious_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ) is False
    
    def test_suspicious_path_detection(self):
        """Test suspicious path detection."""
        monitor = SecurityMonitor()
        
        # Suspicious paths
        assert monitor.is_suspicious_path("/admin/login") is True
        assert monitor.is_suspicious_path("/wp-admin/") is True
        assert monitor.is_suspicious_path("/../../../etc/passwd") is True
        assert monitor.is_suspicious_path("/api/users?id=1' OR '1'='1") is True
        assert monitor.is_suspicious_path("/search?q=<script>alert(1)</script>") is True
        
        # Normal paths
        assert monitor.is_suspicious_path("/api/assessments") is False
        assert monitor.is_suspicious_path("/dashboard") is False
        assert monitor.is_suspicious_path("/") is False
    
    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        monitor = SecurityMonitor()
        
        test_ip = "192.168.1.100"
        
        # IP should not be blocked initially
        assert test_ip not in monitor.blocked_ips
        
        # Block IP
        monitor.block_ip(test_ip, "suspicious_activity")
        assert test_ip in monitor.blocked_ips
        
        # Unblock IP
        monitor.unblock_ip(test_ip)
        assert test_ip not in monitor.blocked_ips
    
    @patch('src.infra_mind.core.security.Request')
    def test_request_security_check(self, mock_request):
        """Test request security checking."""
        monitor = SecurityMonitor()
        
        # Mock request object
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        mock_request.url.path = "/api/assessments"
        
        # Should pass security checks
        result = monitor.check_request_security(mock_request)
        assert result["safe"] is True
        assert len(result["warnings"]) == 0
        
        # Test with suspicious user agent
        mock_request.headers = {"user-agent": "sqlmap/1.0"}
        result = monitor.check_request_security(mock_request)
        assert "Suspicious user agent" in result["warnings"]


class TestSecurityHeaders:
    """Test security headers functionality."""
    
    def test_security_headers(self):
        """Test security headers generation."""
        headers = SecurityHeaders.get_security_headers()
        
        # Check required security headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]
    
    def test_cors_headers(self):
        """Test CORS headers generation."""
        # Without origin
        headers = SecurityHeaders.get_cors_headers()
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        
        # With allowed origin
        headers = SecurityHeaders.get_cors_headers("http://localhost:3000")
        assert headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        
        # With disallowed origin
        headers = SecurityHeaders.get_cors_headers("http://evil.com")
        assert "Access-Control-Allow-Origin" not in headers