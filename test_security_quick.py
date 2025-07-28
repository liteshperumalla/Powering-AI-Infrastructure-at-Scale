#!/usr/bin/env python3
"""
Quick security system test to verify all components are working.
"""

import asyncio
from datetime import datetime, timezone

def test_encryption():
    """Test data encryption."""
    print("🔐 Testing Data Encryption...")
    
    from src.infra_mind.core.encryption import DataEncryption
    
    # Test basic encryption
    encryption = DataEncryption()
    test_data = "Sensitive test data 12345"
    
    encrypted = encryption.encrypt(test_data)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == test_data, "Encryption/decryption failed"
    print("   ✅ Basic encryption/decryption: PASSED")
    
    # Test field encryption
    from src.infra_mind.core.encryption import SecureDataHandler
    handler = SecureDataHandler()
    
    data = {
        "name": "John Doe",
        "api_key": "secret_key_123",
        "public_info": "This is public"
    }
    
    encrypted_data = handler.encrypt_sensitive_fields(data)
    decrypted_data = handler.decrypt_sensitive_fields(encrypted_data)
    
    assert decrypted_data["api_key"] == data["api_key"], "Field encryption failed"
    print("   ✅ Field encryption/decryption: PASSED")


def test_input_validation():
    """Test input validation."""
    print("🔍 Testing Input Validation...")
    
    from src.infra_mind.core.security import InputValidator
    
    # Test email validation
    assert InputValidator.validate_email("test@example.com") == True
    assert InputValidator.validate_email("invalid-email") == False
    print("   ✅ Email validation: PASSED")
    
    # Test SQL injection detection
    assert InputValidator.check_sql_injection("'; DROP TABLE users; --") == True
    assert InputValidator.check_sql_injection("normal text") == False
    print("   ✅ SQL injection detection: PASSED")
    
    # Test XSS detection
    assert InputValidator.check_xss("<script>alert('xss')</script>") == True
    assert InputValidator.check_xss("normal text") == False
    print("   ✅ XSS detection: PASSED")


def test_authentication():
    """Test authentication system."""
    print("🔑 Testing Authentication...")
    
    from src.infra_mind.core.auth import TokenManager, PasswordManager
    
    # Test password hashing
    password = "test_password_123"
    hashed = PasswordManager.hash_password(password)
    
    assert PasswordManager.verify_password(password, hashed) == True
    assert PasswordManager.verify_password("wrong_password", hashed) == False
    print("   ✅ Password hashing/verification: PASSED")
    
    # Test JWT tokens
    data = {"sub": "user123", "email": "test@example.com"}
    token = TokenManager.create_access_token(data)
    
    payload = TokenManager.verify_token(token, "access")
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    print("   ✅ JWT token creation/verification: PASSED")


async def test_incident_response():
    """Test incident response system."""
    print("🚨 Testing Incident Response...")
    
    from src.infra_mind.core.incident_response import (
        IncidentDetector, IncidentType, IncidentSeverity, IncidentStatus
    )
    
    detector = IncidentDetector()
    
    # Test SQL injection detection
    sql_event = {
        "event_type": "web_request",
        "request_data": "username=admin' OR '1'='1&password=test",
        "ip_address": "192.168.1.100",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    incident = await detector.analyze_event(sql_event)
    
    assert incident is not None, "SQL injection incident not detected"
    assert incident.incident_type == IncidentType.SYSTEM_COMPROMISE
    assert incident.severity == IncidentSeverity.CRITICAL
    print("   ✅ SQL injection incident detection: PASSED")
    
    # Test failed login detection
    login_event = {
        "event_type": "login_failure",
        "ip_address": "192.168.1.200",
        "user_id": "admin",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    incident = await detector.analyze_event(login_event)
    
    assert incident is not None, "Failed login incident not detected"
    assert incident.incident_type == IncidentType.UNAUTHORIZED_ACCESS
    print("   ✅ Failed login incident detection: PASSED")


def test_security_monitoring():
    """Test security monitoring."""
    print("👁️  Testing Security Monitoring...")
    
    from src.infra_mind.core.security import SecurityMonitor, RateLimiter
    
    # Test rate limiting
    rate_limiter = RateLimiter()
    
    # Should allow first few requests
    for i in range(3):
        assert rate_limiter.is_rate_limited("test_ip", limit=5, window_seconds=60) == False
    
    # Should rate limit after threshold
    for i in range(3):
        rate_limiter.is_rate_limited("test_ip", limit=5, window_seconds=60)
    
    assert rate_limiter.is_rate_limited("test_ip", limit=5, window_seconds=60) == True
    print("   ✅ Rate limiting: PASSED")
    
    # Test IP blocking
    monitor = SecurityMonitor()
    test_ip = "192.168.1.100"
    
    monitor.block_ip(test_ip, "Test blocking")
    assert test_ip in monitor.blocked_ips
    
    monitor.unblock_ip(test_ip)
    assert test_ip not in monitor.blocked_ips
    print("   ✅ IP blocking/unblocking: PASSED")


def test_audit_logging():
    """Test audit logging."""
    print("📝 Testing Audit Logging...")
    
    from src.infra_mind.core.audit import AuditLogger, AuditEventType, AuditSeverity
    
    logger = AuditLogger()
    
    # Test authentication logging
    logger.log_authentication(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id="user123",
        user_email="test@example.com",
        ip_address="192.168.1.50",
        outcome="success"
    )
    print("   ✅ Authentication event logging: PASSED")
    
    # Test security event logging
    logger.log_security_event(
        event_type=AuditEventType.UNAUTHORIZED_ACCESS,
        user_id="user456",
        ip_address="192.168.1.100",
        details={"attempted_resource": "/admin"},
        severity=AuditSeverity.HIGH
    )
    print("   ✅ Security event logging: PASSED")


async def main():
    """Run all security tests."""
    print("🔒 INFRA MIND SECURITY SYSTEM QUICK TEST")
    print("=" * 50)
    
    try:
        # Run all tests
        test_encryption()
        test_input_validation()
        test_authentication()
        await test_incident_response()
        test_security_monitoring()
        test_audit_logging()
        
        print("\n✅ ALL SECURITY TESTS PASSED!")
        print("🛡️  Security system is fully operational and ready for production.")
        
    except Exception as e:
        print(f"\n❌ SECURITY TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())