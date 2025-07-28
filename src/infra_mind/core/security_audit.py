"""
Security audit and penetration testing framework for Infra Mind.

Provides automated security scanning, vulnerability assessment, and compliance validation.
"""

import asyncio
import json
import hashlib
import secrets
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import ssl
import socket
from urllib.parse import urlparse
import logging

from .audit import AuditLogger, AuditEventType, AuditSeverity
from .security import SecurityMonitor, InputValidator
from .auth import TokenManager
from .encryption import DataEncryption

logger = logging.getLogger(__name__)


class VulnerabilityLevel(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityTestType(str, Enum):
    """Types of security tests."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    ENCRYPTION = "encryption"
    NETWORK_SECURITY = "network_security"
    API_SECURITY = "api_security"
    COMPLIANCE = "compliance"
    CONFIGURATION = "configuration"


@dataclass
class SecurityFinding:
    """Security audit finding."""
    test_type: SecurityTestType
    vulnerability_level: VulnerabilityLevel
    title: str
    description: str
    affected_component: str
    evidence: Dict[str, Any]
    remediation: str
    cve_references: List[str] = None
    compliance_impact: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.cve_references is None:
            self.cve_references = []
        if self.compliance_impact is None:
            self.compliance_impact = []


@dataclass
class SecurityAuditReport:
    """Complete security audit report."""
    audit_id: str
    start_time: datetime
    end_time: datetime
    findings: List[SecurityFinding]
    summary: Dict[str, Any]
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    
    def get_findings_by_level(self, level: VulnerabilityLevel) -> List[SecurityFinding]:
        """Get findings by vulnerability level."""
        return [f for f in self.findings if f.vulnerability_level == level]
    
    def get_critical_findings(self) -> List[SecurityFinding]:
        """Get critical findings."""
        return self.get_findings_by_level(VulnerabilityLevel.CRITICAL)
    
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score (0-100)."""
        weights = {
            VulnerabilityLevel.CRITICAL: 25,
            VulnerabilityLevel.HIGH: 10,
            VulnerabilityLevel.MEDIUM: 5,
            VulnerabilityLevel.LOW: 2,
            VulnerabilityLevel.INFO: 0
        }
        
        total_score = sum(
            weights[finding.vulnerability_level] 
            for finding in self.findings
        )
        
        # Cap at 100
        return min(total_score, 100.0)


class SecurityAuditor:
    """
    Comprehensive security auditor for the Infra Mind platform.
    
    Performs automated security testing including:
    - Authentication and authorization testing
    - Input validation testing
    - Encryption verification
    - Network security assessment
    - API security testing
    - Compliance validation
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.audit_logger = AuditLogger()
        self.security_monitor = SecurityMonitor()
        self.findings: List[SecurityFinding] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def run_full_audit(self) -> SecurityAuditReport:
        """
        Run complete security audit.
        
        Returns:
            SecurityAuditReport with all findings
        """
        audit_id = f"audit_{secrets.token_hex(8)}"
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"Starting security audit {audit_id}")
        
        try:
            # Run all security tests
            await self._test_authentication_security()
            await self._test_authorization_security()
            await self._test_input_validation()
            await self._test_encryption_security()
            await self._test_network_security()
            await self._test_api_security()
            await self._test_configuration_security()
            await self._test_compliance()
            
            end_time = datetime.now(timezone.utc)
            
            # Generate summary
            summary = self._generate_summary()
            compliance_status = self._check_compliance_status()
            recommendations = self._generate_recommendations()
            
            report = SecurityAuditReport(
                audit_id=audit_id,
                start_time=start_time,
                end_time=end_time,
                findings=self.findings.copy(),
                summary=summary,
                compliance_status=compliance_status,
                recommendations=recommendations
            )
            
            # Log audit completion
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                details={
                    "audit_id": audit_id,
                    "findings_count": len(self.findings),
                    "critical_findings": len(report.get_critical_findings()),
                    "risk_score": report.calculate_risk_score()
                },
                severity=AuditSeverity.HIGH if report.get_critical_findings() else AuditSeverity.MEDIUM
            )
            
            logger.info(f"Security audit {audit_id} completed with {len(self.findings)} findings")
            
            return report
            
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            raise
    
    async def _test_authentication_security(self):
        """Test authentication security."""
        logger.info("Testing authentication security...")
        
        # Test 1: Weak password acceptance
        await self._test_weak_passwords()
        
        # Test 2: JWT token security
        await self._test_jwt_security()
        
        # Test 3: Session management
        await self._test_session_security()
        
        # Test 4: Brute force protection
        await self._test_brute_force_protection()
    
    async def _test_weak_passwords(self):
        """Test if system accepts weak passwords."""
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "test",
            "qwerty",
            "12345678",
            "abc123"
        ]
        
        for password in weak_passwords:
            try:
                # Attempt to register with weak password
                if self.session:
                    async with self.session.post(
                        f"{self.base_url}/api/v2/auth/register",
                        json={
                            "email": f"test_{secrets.token_hex(4)}@example.com",
                            "password": password,
                            "full_name": "Test User"
                        }
                    ) as response:
                        if response.status == 201:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.AUTHENTICATION,
                                vulnerability_level=VulnerabilityLevel.HIGH,
                                title="Weak Password Accepted",
                                description=f"System accepts weak password: {password}",
                                affected_component="Authentication System",
                                evidence={"weak_password": password, "status_code": response.status},
                                remediation="Implement strong password policy with minimum complexity requirements",
                                compliance_impact=["NIST", "ISO27001"]
                            ))
            except Exception as e:
                logger.debug(f"Error testing weak password {password}: {e}")
    
    async def _test_jwt_security(self):
        """Test JWT token security."""
        # Test 1: Token algorithm confusion
        try:
            # Create a token with 'none' algorithm
            import jwt
            malicious_payload = {
                "sub": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }
            
            # Try to create token with no signature
            none_token = jwt.encode(malicious_payload, "", algorithm="none")
            
            # Test if system accepts it
            if self.session:
                async with self.session.get(
                    f"{self.base_url}/api/v2/auth/me",
                    headers={"Authorization": f"Bearer {none_token}"}
                ) as response:
                    if response.status == 200:
                        self.findings.append(SecurityFinding(
                            test_type=SecurityTestType.AUTHENTICATION,
                            vulnerability_level=VulnerabilityLevel.CRITICAL,
                            title="JWT Algorithm Confusion Vulnerability",
                            description="System accepts JWT tokens with 'none' algorithm",
                            affected_component="JWT Token Validation",
                            evidence={"token": none_token, "status_code": response.status},
                            remediation="Explicitly validate JWT algorithm and reject 'none' algorithm",
                            cve_references=["CVE-2015-9235"],
                            compliance_impact=["OWASP", "NIST"]
                        ))
        except Exception as e:
            logger.debug(f"Error testing JWT security: {e}")
    
    async def _test_session_security(self):
        """Test session management security."""
        # Test session fixation
        try:
            if self.session:
                # Get initial session
                async with self.session.get(f"{self.base_url}/api/v2/health") as response:
                    initial_cookies = response.cookies
                
                # Login and check if session ID changes
                async with self.session.post(
                    f"{self.base_url}/api/v2/auth/login",
                    json={"email": "test@example.com", "password": "testpassword"}
                ) as response:
                    if response.status == 200:
                        login_cookies = response.cookies
                        
                        # Check if session ID is the same (vulnerability)
                        if initial_cookies and login_cookies:
                            for cookie_name in initial_cookies:
                                if (cookie_name in login_cookies and 
                                    initial_cookies[cookie_name].value == login_cookies[cookie_name].value):
                                    self.findings.append(SecurityFinding(
                                        test_type=SecurityTestType.AUTHENTICATION,
                                        vulnerability_level=VulnerabilityLevel.MEDIUM,
                                        title="Session Fixation Vulnerability",
                                        description="Session ID does not change after authentication",
                                        affected_component="Session Management",
                                        evidence={"cookie_name": cookie_name},
                                        remediation="Regenerate session ID after successful authentication",
                                        compliance_impact=["OWASP"]
                                    ))
        except Exception as e:
            logger.debug(f"Error testing session security: {e}")
    
    async def _test_brute_force_protection(self):
        """Test brute force protection."""
        try:
            if self.session:
                # Attempt multiple failed logins
                failed_attempts = 0
                for i in range(10):
                    async with self.session.post(
                        f"{self.base_url}/api/v2/auth/login",
                        json={"email": "test@example.com", "password": f"wrong_password_{i}"}
                    ) as response:
                        if response.status == 401:
                            failed_attempts += 1
                        elif response.status == 429:
                            # Rate limiting detected - good!
                            break
                
                # If we made too many attempts without rate limiting
                if failed_attempts >= 5:
                    self.findings.append(SecurityFinding(
                        test_type=SecurityTestType.AUTHENTICATION,
                        vulnerability_level=VulnerabilityLevel.HIGH,
                        title="Insufficient Brute Force Protection",
                        description=f"System allowed {failed_attempts} failed login attempts without rate limiting",
                        affected_component="Authentication Rate Limiting",
                        evidence={"failed_attempts": failed_attempts},
                        remediation="Implement account lockout or rate limiting after failed attempts",
                        compliance_impact=["OWASP", "NIST"]
                    ))
        except Exception as e:
            logger.debug(f"Error testing brute force protection: {e}")
    
    async def _test_authorization_security(self):
        """Test authorization and access control."""
        logger.info("Testing authorization security...")
        
        # Test privilege escalation
        await self._test_privilege_escalation()
        
        # Test IDOR (Insecure Direct Object References)
        await self._test_idor_vulnerabilities()
        
        # Test role-based access control
        await self._test_rbac_enforcement()
    
    async def _test_privilege_escalation(self):
        """Test for privilege escalation vulnerabilities."""
        try:
            if self.session:
                # Try to access admin endpoints without proper authorization
                admin_endpoints = [
                    "/api/v2/admin/users",
                    "/api/v2/admin/system",
                    "/api/v2/admin/metrics",
                    "/api/v2/admin/logs"
                ]
                
                for endpoint in admin_endpoints:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.AUTHORIZATION,
                                vulnerability_level=VulnerabilityLevel.CRITICAL,
                                title="Unauthorized Admin Access",
                                description=f"Admin endpoint {endpoint} accessible without authentication",
                                affected_component="Authorization System",
                                evidence={"endpoint": endpoint, "status_code": response.status},
                                remediation="Implement proper authentication and authorization checks",
                                compliance_impact=["OWASP", "NIST"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing privilege escalation: {e}")
    
    async def _test_idor_vulnerabilities(self):
        """Test for Insecure Direct Object Reference vulnerabilities."""
        try:
            if self.session:
                # Test accessing other users' resources
                test_endpoints = [
                    "/api/v2/assessments/1",
                    "/api/v2/assessments/2",
                    "/api/v2/reports/1",
                    "/api/v2/reports/2",
                    "/api/v2/users/1",
                    "/api/v2/users/2"
                ]
                
                for endpoint in test_endpoints:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            # This might be an IDOR if we can access without proper authorization
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.AUTHORIZATION,
                                vulnerability_level=VulnerabilityLevel.HIGH,
                                title="Potential IDOR Vulnerability",
                                description=f"Resource {endpoint} accessible without proper authorization check",
                                affected_component="Resource Access Control",
                                evidence={"endpoint": endpoint, "status_code": response.status},
                                remediation="Implement proper resource ownership validation",
                                compliance_impact=["OWASP"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing IDOR vulnerabilities: {e}")
    
    async def _test_rbac_enforcement(self):
        """Test role-based access control enforcement."""
        # This would require creating test users with different roles
        # For now, we'll check if RBAC is properly configured
        try:
            from .rbac import RolePermissions, Role, Permission
            
            # Verify role permissions are properly defined
            admin_perms = RolePermissions.get_permissions(Role.ADMIN)
            user_perms = RolePermissions.get_permissions(Role.USER)
            viewer_perms = RolePermissions.get_permissions(Role.VIEWER)
            
            # Check if admin has more permissions than user
            if not (admin_perms > user_perms):
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.AUTHORIZATION,
                    vulnerability_level=VulnerabilityLevel.MEDIUM,
                    title="RBAC Configuration Issue",
                    description="Admin role does not have more permissions than user role",
                    affected_component="Role-Based Access Control",
                    evidence={"admin_perms": len(admin_perms), "user_perms": len(user_perms)},
                    remediation="Review and fix role permission hierarchy",
                    compliance_impact=["NIST"]
                ))
            
            # Check if viewer has minimal permissions
            if Permission.DELETE_USER in viewer_perms:
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.AUTHORIZATION,
                    vulnerability_level=VulnerabilityLevel.HIGH,
                    title="Excessive Viewer Permissions",
                    description="Viewer role has dangerous permissions like DELETE_USER",
                    affected_component="Role-Based Access Control",
                    evidence={"viewer_permissions": list(viewer_perms)},
                    remediation="Remove excessive permissions from viewer role",
                    compliance_impact=["NIST", "ISO27001"]
                ))
                
        except Exception as e:
            logger.debug(f"Error testing RBAC enforcement: {e}")
    
    async def _test_input_validation(self):
        """Test input validation security."""
        logger.info("Testing input validation...")
        
        # Test SQL injection
        await self._test_sql_injection()
        
        # Test XSS vulnerabilities
        await self._test_xss_vulnerabilities()
        
        # Test command injection
        await self._test_command_injection()
        
        # Test file upload vulnerabilities
        await self._test_file_upload_security()
    
    async def _test_sql_injection(self):
        """Test for SQL injection vulnerabilities."""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT password FROM users --",
            "1' OR '1'='1' --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        test_endpoints = [
            "/api/v2/assessments",
            "/api/v2/users",
            "/api/v2/reports"
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    if self.session:
                        # Test in query parameters
                        async with self.session.get(
                            f"{self.base_url}{endpoint}?id={payload}"
                        ) as response:
                            response_text = await response.text()
                            
                            # Look for SQL error messages
                            sql_errors = [
                                "sql syntax",
                                "mysql_fetch",
                                "ora-",
                                "postgresql",
                                "sqlite",
                                "syntax error"
                            ]
                            
                            if any(error in response_text.lower() for error in sql_errors):
                                self.findings.append(SecurityFinding(
                                    test_type=SecurityTestType.INPUT_VALIDATION,
                                    vulnerability_level=VulnerabilityLevel.CRITICAL,
                                    title="SQL Injection Vulnerability",
                                    description=f"SQL injection detected in {endpoint}",
                                    affected_component=f"Endpoint: {endpoint}",
                                    evidence={"payload": payload, "response": response_text[:500]},
                                    remediation="Use parameterized queries and input validation",
                                    cve_references=["CWE-89"],
                                    compliance_impact=["OWASP", "NIST"]
                                ))
                except Exception as e:
                    logger.debug(f"Error testing SQL injection on {endpoint}: {e}")
    
    async def _test_xss_vulnerabilities(self):
        """Test for XSS vulnerabilities."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        test_endpoints = [
            "/api/v2/assessments",
            "/api/v2/reports"
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                try:
                    if self.session:
                        # Test in POST data
                        async with self.session.post(
                            f"{self.base_url}{endpoint}",
                            json={"name": payload, "description": payload}
                        ) as response:
                            response_text = await response.text()
                            
                            # Check if payload is reflected without encoding
                            if payload in response_text:
                                self.findings.append(SecurityFinding(
                                    test_type=SecurityTestType.INPUT_VALIDATION,
                                    vulnerability_level=VulnerabilityLevel.HIGH,
                                    title="Cross-Site Scripting (XSS) Vulnerability",
                                    description=f"XSS vulnerability detected in {endpoint}",
                                    affected_component=f"Endpoint: {endpoint}",
                                    evidence={"payload": payload},
                                    remediation="Implement proper input validation and output encoding",
                                    cve_references=["CWE-79"],
                                    compliance_impact=["OWASP"]
                                ))
                except Exception as e:
                    logger.debug(f"Error testing XSS on {endpoint}: {e}")
    
    async def _test_command_injection(self):
        """Test for command injection vulnerabilities."""
        command_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`id`",
            "$(whoami)"
        ]
        
        # Test endpoints that might process system commands
        test_endpoints = [
            "/api/v2/reports/export",
            "/api/v2/assessments/analyze"
        ]
        
        for endpoint in test_endpoints:
            for payload in command_payloads:
                try:
                    if self.session:
                        async with self.session.post(
                            f"{self.base_url}{endpoint}",
                            json={"command": payload, "filename": payload}
                        ) as response:
                            response_text = await response.text()
                            
                            # Look for command execution indicators
                            if any(indicator in response_text.lower() for indicator in 
                                  ["root:", "uid=", "gid=", "total ", "drwx"]):
                                self.findings.append(SecurityFinding(
                                    test_type=SecurityTestType.INPUT_VALIDATION,
                                    vulnerability_level=VulnerabilityLevel.CRITICAL,
                                    title="Command Injection Vulnerability",
                                    description=f"Command injection detected in {endpoint}",
                                    affected_component=f"Endpoint: {endpoint}",
                                    evidence={"payload": payload, "response": response_text[:500]},
                                    remediation="Avoid system command execution or use proper input validation",
                                    cve_references=["CWE-78"],
                                    compliance_impact=["OWASP", "NIST"]
                                ))
                except Exception as e:
                    logger.debug(f"Error testing command injection on {endpoint}: {e}")
    
    async def _test_file_upload_security(self):
        """Test file upload security."""
        # Test malicious file uploads
        malicious_files = [
            ("shell.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("test.jsp", "<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "application/x-jsp"),
            ("script.js", "alert('XSS')", "application/javascript"),
            ("large.txt", "A" * (10 * 1024 * 1024), "text/plain")  # 10MB file
        ]
        
        upload_endpoints = [
            "/api/v2/reports/upload",
            "/api/v2/assessments/import"
        ]
        
        for endpoint in upload_endpoints:
            for filename, content, content_type in malicious_files:
                try:
                    if self.session:
                        data = aiohttp.FormData()
                        data.add_field('file', content, filename=filename, content_type=content_type)
                        
                        async with self.session.post(
                            f"{self.base_url}{endpoint}",
                            data=data
                        ) as response:
                            if response.status == 200:
                                self.findings.append(SecurityFinding(
                                    test_type=SecurityTestType.INPUT_VALIDATION,
                                    vulnerability_level=VulnerabilityLevel.HIGH,
                                    title="Insecure File Upload",
                                    description=f"Malicious file {filename} was accepted",
                                    affected_component=f"File Upload: {endpoint}",
                                    evidence={"filename": filename, "content_type": content_type},
                                    remediation="Implement file type validation and size limits",
                                    compliance_impact=["OWASP"]
                                ))
                except Exception as e:
                    logger.debug(f"Error testing file upload on {endpoint}: {e}")
    
    async def _test_encryption_security(self):
        """Test encryption implementation."""
        logger.info("Testing encryption security...")
        
        # Test encryption strength
        try:
            encryption = DataEncryption()
            
            # Test with known plaintext
            test_data = "sensitive_test_data_12345"
            encrypted = encryption.encrypt(test_data)
            decrypted = encryption.decrypt(encrypted)
            
            if decrypted != test_data:
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.ENCRYPTION,
                    vulnerability_level=VulnerabilityLevel.CRITICAL,
                    title="Encryption/Decryption Failure",
                    description="Data encryption/decryption process is not working correctly",
                    affected_component="Data Encryption",
                    evidence={"original": test_data, "decrypted": decrypted},
                    remediation="Fix encryption implementation",
                    compliance_impact=["GDPR", "HIPAA", "NIST"]
                ))
            
            # Test encryption randomness
            encrypted1 = encryption.encrypt(test_data)
            encrypted2 = encryption.encrypt(test_data)
            
            if encrypted1 == encrypted2:
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.ENCRYPTION,
                    vulnerability_level=VulnerabilityLevel.HIGH,
                    title="Deterministic Encryption",
                    description="Encryption produces identical output for identical input",
                    affected_component="Data Encryption",
                    evidence={"encrypted1": encrypted1, "encrypted2": encrypted2},
                    remediation="Use random IV/nonce for each encryption operation",
                    compliance_impact=["NIST"]
                ))
                
        except Exception as e:
            self.findings.append(SecurityFinding(
                test_type=SecurityTestType.ENCRYPTION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Encryption System Failure",
                description=f"Encryption system failed with error: {str(e)}",
                affected_component="Data Encryption",
                evidence={"error": str(e)},
                remediation="Fix encryption system implementation",
                compliance_impact=["GDPR", "HIPAA", "NIST"]
            ))
    
    async def _test_network_security(self):
        """Test network security configuration."""
        logger.info("Testing network security...")
        
        # Test SSL/TLS configuration
        await self._test_ssl_configuration()
        
        # Test for open ports
        await self._test_open_ports()
    
    async def _test_ssl_configuration(self):
        """Test SSL/TLS configuration."""
        try:
            parsed_url = urlparse(self.base_url)
            if parsed_url.scheme == 'https':
                hostname = parsed_url.hostname
                port = parsed_url.port or 443
                
                # Test SSL certificate
                context = ssl.create_default_context()
                
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Check certificate expiration
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (not_after - datetime.now()).days
                        
                        if days_until_expiry < 30:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.NETWORK_SECURITY,
                                vulnerability_level=VulnerabilityLevel.HIGH,
                                title="SSL Certificate Expiring Soon",
                                description=f"SSL certificate expires in {days_until_expiry} days",
                                affected_component="SSL Certificate",
                                evidence={"expiry_date": cert['notAfter'], "days_remaining": days_until_expiry},
                                remediation="Renew SSL certificate before expiration",
                                compliance_impact=["NIST"]
                            ))
                        
                        # Check for weak cipher suites (simplified check)
                        cipher = ssock.cipher()
                        if cipher and 'RC4' in cipher[0] or 'DES' in cipher[0]:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.NETWORK_SECURITY,
                                vulnerability_level=VulnerabilityLevel.HIGH,
                                title="Weak SSL Cipher Suite",
                                description=f"Weak cipher suite detected: {cipher[0]}",
                                affected_component="SSL Configuration",
                                evidence={"cipher": cipher[0]},
                                remediation="Configure strong cipher suites only",
                                compliance_impact=["NIST", "PCI-DSS"]
                            ))
            else:
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.NETWORK_SECURITY,
                    vulnerability_level=VulnerabilityLevel.HIGH,
                    title="Unencrypted HTTP Connection",
                    description="Application is accessible over unencrypted HTTP",
                    affected_component="Network Transport",
                    evidence={"scheme": parsed_url.scheme},
                    remediation="Enforce HTTPS for all connections",
                    compliance_impact=["GDPR", "HIPAA", "NIST"]
                ))
                
        except Exception as e:
            logger.debug(f"Error testing SSL configuration: {e}")
    
    async def _test_open_ports(self):
        """Test for unnecessary open ports."""
        try:
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname or 'localhost'
            
            # Common ports to check
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 6379, 27017]
            
            open_ports = []
            for port in common_ports:
                try:
                    with socket.create_connection((hostname, port), timeout=1):
                        open_ports.append(port)
                except (socket.timeout, ConnectionRefusedError, OSError):
                    pass
            
            # Check for potentially dangerous open ports
            dangerous_ports = {
                21: "FTP",
                23: "Telnet", 
                25: "SMTP",
                3306: "MySQL",
                5432: "PostgreSQL",
                6379: "Redis",
                27017: "MongoDB"
            }
            
            for port in open_ports:
                if port in dangerous_ports:
                    self.findings.append(SecurityFinding(
                        test_type=SecurityTestType.NETWORK_SECURITY,
                        vulnerability_level=VulnerabilityLevel.MEDIUM,
                        title=f"Potentially Dangerous Open Port",
                        description=f"{dangerous_ports[port]} service on port {port} is accessible",
                        affected_component="Network Services",
                        evidence={"port": port, "service": dangerous_ports[port]},
                        remediation="Secure or close unnecessary network services",
                        compliance_impact=["NIST"]
                    ))
                    
        except Exception as e:
            logger.debug(f"Error testing open ports: {e}")
    
    async def _test_api_security(self):
        """Test API-specific security."""
        logger.info("Testing API security...")
        
        # Test API versioning
        await self._test_api_versioning()
        
        # Test rate limiting
        await self._test_rate_limiting()
        
        # Test CORS configuration
        await self._test_cors_configuration()
    
    async def _test_api_versioning(self):
        """Test API versioning security."""
        try:
            if self.session:
                # Test if old API versions are still accessible
                old_versions = ["/api/v1/", "/api/v0/"]
                
                for version_path in old_versions:
                    async with self.session.get(f"{self.base_url}{version_path}health") as response:
                        if response.status == 200:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.API_SECURITY,
                                vulnerability_level=VulnerabilityLevel.MEDIUM,
                                title="Deprecated API Version Accessible",
                                description=f"Old API version {version_path} is still accessible",
                                affected_component="API Versioning",
                                evidence={"version_path": version_path, "status_code": response.status},
                                remediation="Disable or secure deprecated API versions",
                                compliance_impact=["OWASP"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing API versioning: {e}")
    
    async def _test_rate_limiting(self):
        """Test rate limiting implementation."""
        try:
            if self.session:
                # Make rapid requests to test rate limiting
                responses = []
                for i in range(20):
                    async with self.session.get(f"{self.base_url}/api/v2/health") as response:
                        responses.append(response.status)
                
                # Check if any requests were rate limited
                rate_limited = any(status == 429 for status in responses)
                
                if not rate_limited and len(responses) >= 15:
                    self.findings.append(SecurityFinding(
                        test_type=SecurityTestType.API_SECURITY,
                        vulnerability_level=VulnerabilityLevel.MEDIUM,
                        title="Insufficient Rate Limiting",
                        description=f"Made {len(responses)} requests without rate limiting",
                        affected_component="Rate Limiting",
                        evidence={"requests_made": len(responses), "rate_limited": rate_limited},
                        remediation="Implement proper rate limiting for API endpoints",
                        compliance_impact=["OWASP"]
                    ))
        except Exception as e:
            logger.debug(f"Error testing rate limiting: {e}")
    
    async def _test_cors_configuration(self):
        """Test CORS configuration."""
        try:
            if self.session:
                # Test CORS with various origins
                test_origins = [
                    "http://evil.com",
                    "https://attacker.com",
                    "null"
                ]
                
                for origin in test_origins:
                    headers = {"Origin": origin}
                    async with self.session.options(
                        f"{self.base_url}/api/v2/health",
                        headers=headers
                    ) as response:
                        cors_origin = response.headers.get("Access-Control-Allow-Origin")
                        
                        if cors_origin == "*" or cors_origin == origin:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.API_SECURITY,
                                vulnerability_level=VulnerabilityLevel.MEDIUM,
                                title="Permissive CORS Configuration",
                                description=f"CORS allows requests from {origin}",
                                affected_component="CORS Configuration",
                                evidence={"origin": origin, "cors_header": cors_origin},
                                remediation="Configure CORS to allow only trusted origins",
                                compliance_impact=["OWASP"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing CORS configuration: {e}")
    
    async def _test_configuration_security(self):
        """Test security configuration."""
        logger.info("Testing configuration security...")
        
        # Test for exposed configuration files
        await self._test_exposed_config_files()
        
        # Test security headers
        await self._test_security_headers()
    
    async def _test_exposed_config_files(self):
        """Test for exposed configuration files."""
        config_files = [
            "/.env",
            "/config.json",
            "/config.yaml",
            "/settings.py",
            "/.git/config",
            "/docker-compose.yml",
            "/Dockerfile"
        ]
        
        try:
            if self.session:
                for config_file in config_files:
                    async with self.session.get(f"{self.base_url}{config_file}") as response:
                        if response.status == 200:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.CONFIGURATION,
                                vulnerability_level=VulnerabilityLevel.HIGH,
                                title="Exposed Configuration File",
                                description=f"Configuration file {config_file} is publicly accessible",
                                affected_component="Web Server Configuration",
                                evidence={"file": config_file, "status_code": response.status},
                                remediation="Block access to configuration files",
                                compliance_impact=["OWASP", "NIST"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing exposed config files: {e}")
    
    async def _test_security_headers(self):
        """Test security headers."""
        try:
            if self.session:
                async with self.session.get(f"{self.base_url}/api/v2/health") as response:
                    headers = response.headers
                    
                    # Required security headers
                    required_headers = {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                        "X-XSS-Protection": "1; mode=block",
                        "Strict-Transport-Security": None,  # Should exist for HTTPS
                        "Content-Security-Policy": None
                    }
                    
                    for header, expected_value in required_headers.items():
                        if header not in headers:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.CONFIGURATION,
                                vulnerability_level=VulnerabilityLevel.MEDIUM,
                                title=f"Missing Security Header: {header}",
                                description=f"Security header {header} is not set",
                                affected_component="HTTP Security Headers",
                                evidence={"missing_header": header},
                                remediation=f"Add {header} security header",
                                compliance_impact=["OWASP"]
                            ))
                        elif expected_value and isinstance(expected_value, list):
                            if headers[header] not in expected_value:
                                self.findings.append(SecurityFinding(
                                    test_type=SecurityTestType.CONFIGURATION,
                                    vulnerability_level=VulnerabilityLevel.LOW,
                                    title=f"Suboptimal Security Header: {header}",
                                    description=f"Security header {header} has value '{headers[header]}', expected one of {expected_value}",
                                    affected_component="HTTP Security Headers",
                                    evidence={"header": header, "value": headers[header], "expected": expected_value},
                                    remediation=f"Set {header} to appropriate value",
                                    compliance_impact=["OWASP"]
                                ))
                        elif expected_value and headers[header] != expected_value:
                            self.findings.append(SecurityFinding(
                                test_type=SecurityTestType.CONFIGURATION,
                                vulnerability_level=VulnerabilityLevel.LOW,
                                title=f"Incorrect Security Header: {header}",
                                description=f"Security header {header} has value '{headers[header]}', expected '{expected_value}'",
                                affected_component="HTTP Security Headers",
                                evidence={"header": header, "value": headers[header], "expected": expected_value},
                                remediation=f"Set {header} to '{expected_value}'",
                                compliance_impact=["OWASP"]
                            ))
        except Exception as e:
            logger.debug(f"Error testing security headers: {e}")
    
    async def _test_compliance(self):
        """Test compliance with security standards."""
        logger.info("Testing compliance...")
        
        # Test GDPR compliance
        await self._test_gdpr_compliance()
        
        # Test OWASP compliance
        await self._test_owasp_compliance()
    
    async def _test_gdpr_compliance(self):
        """Test GDPR compliance."""
        # Check for privacy policy endpoint
        try:
            if self.session:
                async with self.session.get(f"{self.base_url}/privacy-policy") as response:
                    if response.status != 200:
                        self.findings.append(SecurityFinding(
                            test_type=SecurityTestType.COMPLIANCE,
                            vulnerability_level=VulnerabilityLevel.MEDIUM,
                            title="Missing Privacy Policy",
                            description="Privacy policy is not accessible",
                            affected_component="GDPR Compliance",
                            evidence={"status_code": response.status},
                            remediation="Provide accessible privacy policy",
                            compliance_impact=["GDPR"]
                        ))
                
                # Check for data deletion endpoint
                async with self.session.delete(f"{self.base_url}/api/v2/users/me/data") as response:
                    if response.status == 404:
                        self.findings.append(SecurityFinding(
                            test_type=SecurityTestType.COMPLIANCE,
                            vulnerability_level=VulnerabilityLevel.MEDIUM,
                            title="Missing Data Deletion Capability",
                            description="No endpoint for users to delete their data",
                            affected_component="GDPR Compliance",
                            evidence={"status_code": response.status},
                            remediation="Implement user data deletion functionality",
                            compliance_impact=["GDPR"]
                        ))
        except Exception as e:
            logger.debug(f"Error testing GDPR compliance: {e}")
    
    async def _test_owasp_compliance(self):
        """Test OWASP Top 10 compliance."""
        # This is a summary check based on other tests
        owasp_categories = {
            "A01:2021 – Broken Access Control": ["AUTHORIZATION"],
            "A02:2021 – Cryptographic Failures": ["ENCRYPTION"],
            "A03:2021 – Injection": ["INPUT_VALIDATION"],
            "A04:2021 – Insecure Design": ["CONFIGURATION"],
            "A05:2021 – Security Misconfiguration": ["CONFIGURATION"],
            "A06:2021 – Vulnerable Components": ["CONFIGURATION"],
            "A07:2021 – Identification and Authentication Failures": ["AUTHENTICATION"],
            "A08:2021 – Software and Data Integrity Failures": ["ENCRYPTION"],
            "A09:2021 – Security Logging and Monitoring Failures": ["CONFIGURATION"],
            "A10:2021 – Server-Side Request Forgery": ["INPUT_VALIDATION"]
        }
        
        for category, test_types in owasp_categories.items():
            category_findings = [
                f for f in self.findings 
                if f.test_type.value.upper() in test_types and 
                f.vulnerability_level in [VulnerabilityLevel.CRITICAL, VulnerabilityLevel.HIGH]
            ]
            
            if category_findings:
                self.findings.append(SecurityFinding(
                    test_type=SecurityTestType.COMPLIANCE,
                    vulnerability_level=VulnerabilityLevel.HIGH,
                    title=f"OWASP Top 10 Violation: {category}",
                    description=f"Found {len(category_findings)} high/critical issues in {category}",
                    affected_component="OWASP Compliance",
                    evidence={"category": category, "findings_count": len(category_findings)},
                    remediation=f"Address {category} vulnerabilities",
                    compliance_impact=["OWASP"]
                ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary."""
        summary = {
            "total_findings": len(self.findings),
            "findings_by_level": {
                level.value: len([f for f in self.findings if f.vulnerability_level == level])
                for level in VulnerabilityLevel
            },
            "findings_by_type": {
                test_type.value: len([f for f in self.findings if f.test_type == test_type])
                for test_type in SecurityTestType
            },
            "critical_components": [
                f.affected_component for f in self.findings 
                if f.vulnerability_level == VulnerabilityLevel.CRITICAL
            ]
        }
        return summary
    
    def _check_compliance_status(self) -> Dict[str, bool]:
        """Check compliance status."""
        compliance_standards = ["OWASP", "GDPR", "NIST", "HIPAA", "ISO27001"]
        
        compliance_status = {}
        for standard in compliance_standards:
            # Check if there are any findings that impact this standard
            impacting_findings = [
                f for f in self.findings 
                if standard in f.compliance_impact and 
                f.vulnerability_level in [VulnerabilityLevel.CRITICAL, VulnerabilityLevel.HIGH]
            ]
            compliance_status[standard] = len(impacting_findings) == 0
        
        return compliance_status
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Critical findings recommendations
        critical_findings = self.get_findings_by_level(VulnerabilityLevel.CRITICAL)
        if critical_findings:
            recommendations.append(
                f"URGENT: Address {len(critical_findings)} critical security vulnerabilities immediately"
            )
        
        # High findings recommendations
        high_findings = self.get_findings_by_level(VulnerabilityLevel.HIGH)
        if high_findings:
            recommendations.append(
                f"HIGH PRIORITY: Address {len(high_findings)} high-severity security issues"
            )
        
        # Component-specific recommendations
        component_issues = {}
        for finding in self.findings:
            if finding.vulnerability_level in [VulnerabilityLevel.CRITICAL, VulnerabilityLevel.HIGH]:
                component = finding.affected_component
                if component not in component_issues:
                    component_issues[component] = 0
                component_issues[component] += 1
        
        for component, count in sorted(component_issues.items(), key=lambda x: x[1], reverse=True):
            if count > 1:
                recommendations.append(f"Review and harden {component} ({count} issues found)")
        
        # Compliance recommendations
        compliance_status = self._check_compliance_status()
        for standard, compliant in compliance_status.items():
            if not compliant:
                recommendations.append(f"Address {standard} compliance violations")
        
        # General recommendations
        if len(self.findings) > 10:
            recommendations.append("Implement regular security auditing and monitoring")
        
        recommendations.append("Establish incident response procedures")
        recommendations.append("Provide security training for development team")
        
        return recommendations
    
    def get_findings_by_level(self, level: VulnerabilityLevel) -> List[SecurityFinding]:
        """Get findings by vulnerability level."""
        return [f for f in self.findings if f.vulnerability_level == level]


# Convenience function for running security audit
async def run_security_audit(base_url: str = "http://localhost:8000") -> SecurityAuditReport:
    """
    Run a complete security audit.
    
    Args:
        base_url: Base URL of the application to audit
        
    Returns:
        SecurityAuditReport with findings and recommendations
    """
    async with SecurityAuditor(base_url) as auditor:
        return await auditor.run_full_audit()