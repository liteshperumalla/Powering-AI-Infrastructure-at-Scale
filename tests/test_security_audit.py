"""
Tests for security audit and penetration testing framework.

Tests automated security scanning, vulnerability assessment, and compliance validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.core.security_audit import (
    SecurityAuditor, SecurityFinding, SecurityAuditReport,
    VulnerabilityLevel, SecurityTestType, run_security_audit
)


class TestSecurityFinding:
    """Test SecurityFinding data structure."""
    
    def test_security_finding_creation(self):
        """Test creating a security finding."""
        finding = SecurityFinding(
            test_type=SecurityTestType.AUTHENTICATION,
            vulnerability_level=VulnerabilityLevel.HIGH,
            title="Test Vulnerability",
            description="Test description",
            affected_component="Test Component",
            evidence={"test": "data"},
            remediation="Fix the issue"
        )
        
        assert finding.test_type == SecurityTestType.AUTHENTICATION
        assert finding.vulnerability_level == VulnerabilityLevel.HIGH
        assert finding.title == "Test Vulnerability"
        assert finding.timestamp is not None
        assert finding.cve_references == []
        assert finding.compliance_impact == []
    
    def test_security_finding_with_references(self):
        """Test security finding with CVE references."""
        finding = SecurityFinding(
            test_type=SecurityTestType.INPUT_VALIDATION,
            vulnerability_level=VulnerabilityLevel.CRITICAL,
            title="SQL Injection",
            description="SQL injection vulnerability",
            affected_component="Database",
            evidence={"payload": "' OR 1=1"},
            remediation="Use parameterized queries",
            cve_references=["CVE-2021-1234"],
            compliance_impact=["OWASP", "NIST"]
        )
        
        assert "CVE-2021-1234" in finding.cve_references
        assert "OWASP" in finding.compliance_impact
        assert "NIST" in finding.compliance_impact


class TestSecurityAuditReport:
    """Test SecurityAuditReport functionality."""
    
    def test_audit_report_creation(self):
        """Test creating an audit report."""
        findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Critical Issue",
                description="Critical security issue",
                affected_component="Auth",
                evidence={},
                remediation="Fix immediately"
            ),
            SecurityFinding(
                test_type=SecurityTestType.AUTHORIZATION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="High Issue",
                description="High security issue",
                affected_component="AuthZ",
                evidence={},
                remediation="Fix soon"
            )
        ]
        
        start_time = datetime.now(timezone.utc)
        end_time = start_time
        
        report = SecurityAuditReport(
            audit_id="test_audit",
            start_time=start_time,
            end_time=end_time,
            findings=findings,
            summary={"total": 2},
            compliance_status={"OWASP": False},
            recommendations=["Fix critical issues"]
        )
        
        assert report.audit_id == "test_audit"
        assert len(report.findings) == 2
        assert len(report.get_critical_findings()) == 1
        assert len(report.get_findings_by_level(VulnerabilityLevel.HIGH)) == 1
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Critical Issue",
                description="Critical security issue",
                affected_component="Auth",
                evidence={},
                remediation="Fix immediately"
            ),
            SecurityFinding(
                test_type=SecurityTestType.AUTHORIZATION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="High Issue",
                description="High security issue",
                affected_component="AuthZ",
                evidence={},
                remediation="Fix soon"
            ),
            SecurityFinding(
                test_type=SecurityTestType.INPUT_VALIDATION,
                vulnerability_level=VulnerabilityLevel.MEDIUM,
                title="Medium Issue",
                description="Medium security issue",
                affected_component="Input",
                evidence={},
                remediation="Fix when possible"
            )
        ]
        
        report = SecurityAuditReport(
            audit_id="test_audit",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            findings=findings,
            summary={},
            compliance_status={},
            recommendations=[]
        )
        
        # Risk score: 1 critical (25) + 1 high (10) + 1 medium (5) = 40
        assert report.calculate_risk_score() == 40.0
    
    def test_risk_score_cap(self):
        """Test risk score is capped at 100."""
        # Create many critical findings to exceed 100
        findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title=f"Critical Issue {i}",
                description="Critical security issue",
                affected_component="Auth",
                evidence={},
                remediation="Fix immediately"
            )
            for i in range(10)  # 10 critical = 250 points
        ]
        
        report = SecurityAuditReport(
            audit_id="test_audit",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            findings=findings,
            summary={},
            compliance_status={},
            recommendations=[]
        )
        
        # Should be capped at 100
        assert report.calculate_risk_score() == 100.0


class TestSecurityAuditor:
    """Test SecurityAuditor functionality."""
    
    @pytest.fixture
    def auditor(self):
        """Create SecurityAuditor instance for testing."""
        return SecurityAuditor("http://localhost:8000")
    
    def test_auditor_initialization(self, auditor):
        """Test auditor initialization."""
        assert auditor.base_url == "http://localhost:8000"
        assert auditor.findings == []
        assert auditor.session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test auditor as async context manager."""
        async with SecurityAuditor("http://localhost:8000") as auditor:
            assert auditor.session is not None
        # Session should be closed after context exit
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_weak_password_detection(self, mock_session_class):
        """Test weak password detection."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 201  # Password accepted
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_weak_passwords()
        
        # Should have findings for weak passwords
        weak_password_findings = [
            f for f in auditor.findings 
            if f.title == "Weak Password Accepted"
        ]
        assert len(weak_password_findings) > 0
        
        # Check finding details
        finding = weak_password_findings[0]
        assert finding.vulnerability_level == VulnerabilityLevel.HIGH
        assert finding.test_type == SecurityTestType.AUTHENTICATION
        assert "NIST" in finding.compliance_impact
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_sql_injection_detection(self, mock_session_class):
        """Test SQL injection detection."""
        # Mock HTTP response with SQL error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "SQL syntax error near 'OR'"
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_sql_injection()
        
        # Should have SQL injection findings
        sql_findings = [
            f for f in auditor.findings 
            if f.title == "SQL Injection Vulnerability"
        ]
        assert len(sql_findings) > 0
        
        # Check finding details
        finding = sql_findings[0]
        assert finding.vulnerability_level == VulnerabilityLevel.CRITICAL
        assert finding.test_type == SecurityTestType.INPUT_VALIDATION
        assert "CWE-89" in finding.cve_references
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_xss_detection(self, mock_session_class):
        """Test XSS vulnerability detection."""
        # Mock HTTP response that reflects XSS payload
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "<script>alert('XSS')</script>"
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_xss_vulnerabilities()
        
        # Should have XSS findings
        xss_findings = [
            f for f in auditor.findings 
            if f.title == "Cross-Site Scripting (XSS) Vulnerability"
        ]
        assert len(xss_findings) > 0
        
        # Check finding details
        finding = xss_findings[0]
        assert finding.vulnerability_level == VulnerabilityLevel.HIGH
        assert finding.test_type == SecurityTestType.INPUT_VALIDATION
        assert "CWE-79" in finding.cve_references
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_unauthorized_admin_access(self, mock_session_class):
        """Test unauthorized admin access detection."""
        # Mock HTTP response allowing admin access without auth
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_privilege_escalation()
        
        # Should have unauthorized access findings
        access_findings = [
            f for f in auditor.findings 
            if f.title == "Unauthorized Admin Access"
        ]
        assert len(access_findings) > 0
        
        # Check finding details
        finding = access_findings[0]
        assert finding.vulnerability_level == VulnerabilityLevel.CRITICAL
        assert finding.test_type == SecurityTestType.AUTHORIZATION
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_missing_security_headers(self, mock_session_class):
        """Test missing security headers detection."""
        # Mock HTTP response without security headers
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}  # No security headers
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_security_headers()
        
        # Should have missing header findings
        header_findings = [
            f for f in auditor.findings 
            if "Missing Security Header" in f.title
        ]
        assert len(header_findings) > 0
        
        # Check for specific headers
        header_names = [f.title.split(": ")[1] for f in header_findings]
        assert "X-Content-Type-Options" in header_names
        assert "X-Frame-Options" in header_names
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_rate_limiting_check(self, mock_session_class):
        """Test rate limiting detection."""
        # Mock HTTP responses - all successful (no rate limiting)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            await auditor._test_rate_limiting()
        
        # Should have rate limiting findings
        rate_findings = [
            f for f in auditor.findings 
            if f.title == "Insufficient Rate Limiting"
        ]
        assert len(rate_findings) > 0
        
        # Check finding details
        finding = rate_findings[0]
        assert finding.vulnerability_level == VulnerabilityLevel.MEDIUM
        assert finding.test_type == SecurityTestType.API_SECURITY
    
    def test_encryption_security_test(self, auditor):
        """Test encryption security validation."""
        # This test doesn't require mocking as it tests actual encryption
        asyncio.run(auditor._test_encryption_security())
        
        # Should not have encryption failures (assuming encryption works)
        encryption_failures = [
            f for f in auditor.findings 
            if f.title == "Encryption/Decryption Failure"
        ]
        assert len(encryption_failures) == 0
    
    def test_rbac_configuration_test(self, auditor):
        """Test RBAC configuration validation."""
        asyncio.run(auditor._test_rbac_enforcement())
        
        # Check if any RBAC issues were found
        rbac_findings = [
            f for f in auditor.findings 
            if "RBAC" in f.title
        ]
        
        # Findings depend on actual RBAC configuration
        # This test validates the test runs without errors
        assert isinstance(rbac_findings, list)
    
    def test_generate_summary(self, auditor):
        """Test audit summary generation."""
        # Add some test findings
        auditor.findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Critical Auth Issue",
                description="Critical issue",
                affected_component="Auth",
                evidence={},
                remediation="Fix now"
            ),
            SecurityFinding(
                test_type=SecurityTestType.INPUT_VALIDATION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="High Input Issue",
                description="High issue",
                affected_component="Input",
                evidence={},
                remediation="Fix soon"
            )
        ]
        
        summary = auditor._generate_summary()
        
        assert summary["total_findings"] == 2
        assert summary["findings_by_level"]["critical"] == 1
        assert summary["findings_by_level"]["high"] == 1
        assert summary["findings_by_type"]["authentication"] == 1
        assert summary["findings_by_type"]["input_validation"] == 1
        assert "Auth" in summary["critical_components"]
    
    def test_compliance_status_check(self, auditor):
        """Test compliance status checking."""
        # Add findings that impact compliance
        auditor.findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="OWASP Violation",
                description="OWASP issue",
                affected_component="Auth",
                evidence={},
                remediation="Fix now",
                compliance_impact=["OWASP", "NIST"]
            ),
            SecurityFinding(
                test_type=SecurityTestType.ENCRYPTION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="GDPR Violation",
                description="GDPR issue",
                affected_component="Encryption",
                evidence={},
                remediation="Fix soon",
                compliance_impact=["GDPR"]
            )
        ]
        
        compliance_status = auditor._check_compliance_status()
        
        # Should fail compliance for standards with high/critical findings
        assert compliance_status["OWASP"] is False
        assert compliance_status["NIST"] is False
        assert compliance_status["GDPR"] is False
        assert compliance_status["HIPAA"] is True  # No HIPAA findings
    
    def test_generate_recommendations(self, auditor):
        """Test recommendation generation."""
        # Add various findings
        auditor.findings = [
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.CRITICAL,
                title="Critical Auth Issue",
                description="Critical issue",
                affected_component="Authentication System",
                evidence={},
                remediation="Fix now"
            ),
            SecurityFinding(
                test_type=SecurityTestType.AUTHENTICATION,
                vulnerability_level=VulnerabilityLevel.HIGH,
                title="High Auth Issue",
                description="High issue",
                affected_component="Authentication System",
                evidence={},
                remediation="Fix soon"
            ),
            SecurityFinding(
                test_type=SecurityTestType.INPUT_VALIDATION,
                vulnerability_level=VulnerabilityLevel.MEDIUM,
                title="Medium Input Issue",
                description="Medium issue",
                affected_component="Input Validation",
                evidence={},
                remediation="Fix when possible"
            )
        ]
        
        recommendations = auditor._generate_recommendations()
        
        # Should have recommendations for critical and high issues
        critical_rec = next((r for r in recommendations if "critical" in r.lower()), None)
        assert critical_rec is not None
        
        high_rec = next((r for r in recommendations if "HIGH PRIORITY" in r), None)
        assert high_rec is not None
        
        # Should have component-specific recommendation
        auth_rec = next((r for r in recommendations if "Authentication System" in r), None)
        assert auth_rec is not None


class TestSecurityAuditIntegration:
    """Test security audit integration scenarios."""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_full_audit_workflow(self, mock_session_class):
        """Test complete audit workflow."""
        # Mock various responses for different tests
        mock_responses = {
            "weak_password": AsyncMock(status=201),
            "sql_injection": AsyncMock(status=500, text=AsyncMock(return_value="SQL error")),
            "security_headers": AsyncMock(status=200, headers={}),
            "default": AsyncMock(status=200, text=AsyncMock(return_value="OK"))
        }
        
        # Set up context managers
        for response in mock_responses.values():
            response.__aenter__.return_value = response
        
        mock_session = AsyncMock()
        
        # Configure different responses for different endpoints
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'register' in url:
                return mock_responses["weak_password"]
            elif 'health' in url:
                return mock_responses["security_headers"]
            else:
                return mock_responses["default"]
        
        mock_session.post.side_effect = side_effect
        mock_session.get.side_effect = side_effect
        mock_session.options.side_effect = side_effect
        mock_session_class.return_value = mock_session
        
        # Run full audit
        async with SecurityAuditor("http://localhost:8000") as auditor:
            auditor.session = mock_session
            report = await auditor.run_full_audit()
        
        # Verify report structure
        assert isinstance(report, SecurityAuditReport)
        assert report.audit_id.startswith("audit_")
        assert report.start_time <= report.end_time
        assert isinstance(report.findings, list)
        assert isinstance(report.summary, dict)
        assert isinstance(report.compliance_status, dict)
        assert isinstance(report.recommendations, list)
        
        # Verify summary contains expected keys
        assert "total_findings" in report.summary
        assert "findings_by_level" in report.summary
        assert "findings_by_type" in report.summary
        
        # Verify compliance status for known standards
        for standard in ["OWASP", "GDPR", "NIST", "HIPAA", "ISO27001"]:
            assert standard in report.compliance_status
            assert isinstance(report.compliance_status[standard], bool)
    
    @pytest.mark.asyncio
    async def test_run_security_audit_convenience_function(self):
        """Test convenience function for running security audit."""
        with patch('src.infra_mind.core.security_audit.SecurityAuditor') as mock_auditor_class:
            mock_auditor = AsyncMock()
            mock_report = SecurityAuditReport(
                audit_id="test_audit",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                findings=[],
                summary={},
                compliance_status={},
                recommendations=[]
            )
            mock_auditor.run_full_audit.return_value = mock_report
            mock_auditor.__aenter__.return_value = mock_auditor
            mock_auditor.__aexit__.return_value = None
            mock_auditor_class.return_value = mock_auditor
            
            # Run audit using convenience function
            report = await run_security_audit("http://test:8000")
            
            # Verify function was called correctly
            mock_auditor_class.assert_called_once_with("http://test:8000")
            mock_auditor.run_full_audit.assert_called_once()
            assert report == mock_report
    
    def test_vulnerability_level_enum(self):
        """Test VulnerabilityLevel enum values."""
        assert VulnerabilityLevel.CRITICAL == "critical"
        assert VulnerabilityLevel.HIGH == "high"
        assert VulnerabilityLevel.MEDIUM == "medium"
        assert VulnerabilityLevel.LOW == "low"
        assert VulnerabilityLevel.INFO == "info"
    
    def test_security_test_type_enum(self):
        """Test SecurityTestType enum values."""
        assert SecurityTestType.AUTHENTICATION == "authentication"
        assert SecurityTestType.AUTHORIZATION == "authorization"
        assert SecurityTestType.INPUT_VALIDATION == "input_validation"
        assert SecurityTestType.ENCRYPTION == "encryption"
        assert SecurityTestType.NETWORK_SECURITY == "network_security"
        assert SecurityTestType.API_SECURITY == "api_security"
        assert SecurityTestType.COMPLIANCE == "compliance"
        assert SecurityTestType.CONFIGURATION == "configuration"


class TestSecurityAuditErrorHandling:
    """Test error handling in security audit system."""
    
    @pytest.mark.asyncio
    async def test_audit_with_network_errors(self):
        """Test audit behavior with network errors."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = Exception("Network error")
            mock_session.get.side_effect = Exception("Network error")
            mock_session_class.return_value = mock_session
            
            async with SecurityAuditor("http://localhost:8000") as auditor:
                auditor.session = mock_session
                
                # Should not raise exception, but handle gracefully
                await auditor._test_weak_passwords()
                await auditor._test_sql_injection()
                
                # Should complete without findings due to errors
                assert len(auditor.findings) == 0
    
    @pytest.mark.asyncio
    async def test_audit_with_partial_failures(self):
        """Test audit with some tests failing."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            
            # Some requests succeed, others fail
            def side_effect(*args, **kwargs):
                url = args[0] if args else kwargs.get('url', '')
                if 'register' in url:
                    raise Exception("Registration endpoint down")
                else:
                    response = AsyncMock(status=200, headers={})
                    response.__aenter__.return_value = response
                    return response
            
            mock_session.post.side_effect = side_effect
            mock_session.get.side_effect = side_effect
            mock_session_class.return_value = mock_session
            
            async with SecurityAuditor("http://localhost:8000") as auditor:
                auditor.session = mock_session
                
                # Run tests - some will fail, others succeed
                await auditor._test_weak_passwords()  # Will fail
                await auditor._test_security_headers()  # Will succeed
                
                # Should have findings from successful tests only
                header_findings = [f for f in auditor.findings if "Security Header" in f.title]
                password_findings = [f for f in auditor.findings if "Password" in f.title]
                
                assert len(header_findings) > 0  # Security header test succeeded
                assert len(password_findings) == 0  # Password test failed
    
    def test_invalid_base_url(self):
        """Test auditor with invalid base URL."""
        # Should not raise exception during initialization
        auditor = SecurityAuditor("invalid-url")
        assert auditor.base_url == "invalid-url"
        
        # Actual network operations would fail, but that's handled gracefully
    
    @pytest.mark.asyncio
    async def test_encryption_test_with_broken_encryption(self):
        """Test encryption test with broken encryption system."""
        with patch('src.infra_mind.core.security_audit.DataEncryption') as mock_encryption:
            mock_encryption.side_effect = Exception("Encryption system broken")
            
            auditor = SecurityAuditor("http://localhost:8000")
            await auditor._test_encryption_security()
            
            # Should have critical finding about encryption failure
            encryption_failures = [
                f for f in auditor.findings 
                if f.title == "Encryption System Failure"
            ]
            assert len(encryption_failures) == 1
            assert encryption_failures[0].vulnerability_level == VulnerabilityLevel.CRITICAL