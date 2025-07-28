"""
Tests for third-party integrations.

Tests compliance databases, business tools, and SSO provider integrations.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.infra_mind.integrations.compliance_databases import (
    ComplianceDatabaseIntegrator, ComplianceFramework, IndustryType,
    ComplianceRequirementType, ComplianceRequirement, ComplianceAssessment
)
from src.infra_mind.integrations.business_tools import (
    BusinessToolsIntegrator, NotificationChannel, NotificationPriority,
    MessageType, NotificationMessage, SlackMessage, TeamsMessage
)
from src.infra_mind.integrations.sso_providers import (
    SSOProviderIntegrator, SSOProvider, AuthenticationMethod,
    SSOConfiguration, SSOUser, AuthorizationRequest
)


class TestComplianceDatabaseIntegrator:
    """Test compliance database integrations."""
    
    @pytest.fixture
    def integrator(self):
        """Create compliance database integrator instance."""
        return ComplianceDatabaseIntegrator()
    
    def test_initialization(self, integrator):
        """Test integrator initialization."""
        assert integrator is not None
        assert len(integrator.local_requirements) > 0
        assert ComplianceFramework.GDPR in integrator.local_requirements
        assert ComplianceFramework.HIPAA in integrator.local_requirements
    
    @pytest.mark.asyncio
    async def test_get_requirements_by_framework(self, integrator):
        """Test getting requirements by framework."""
        async with integrator:
            # Test GDPR requirements
            gdpr_requirements = await integrator.get_requirements_by_framework(
                ComplianceFramework.GDPR
            )
            
            assert len(gdpr_requirements) > 0
            assert all(req.framework == ComplianceFramework.GDPR for req in gdpr_requirements)
            
            # Test HIPAA requirements
            hipaa_requirements = await integrator.get_requirements_by_framework(
                ComplianceFramework.HIPAA,
                IndustryType.HEALTHCARE
            )
            
            assert len(hipaa_requirements) > 0
            assert all(req.framework == ComplianceFramework.HIPAA for req in hipaa_requirements)
    
    @pytest.mark.asyncio
    async def test_get_requirements_by_type(self, integrator):
        """Test getting requirements by type."""
        async with integrator:
            data_protection_reqs = await integrator.get_requirements_by_type(
                ComplianceRequirementType.DATA_PROTECTION,
                [ComplianceFramework.GDPR, ComplianceFramework.CCPA]
            )
            
            assert len(data_protection_reqs) > 0
            assert all(
                req.requirement_type == ComplianceRequirementType.DATA_PROTECTION
                for req in data_protection_reqs
            )
    
    @pytest.mark.asyncio
    async def test_assess_compliance(self, integrator):
        """Test compliance assessment."""
        async with integrator:
            current_controls = ["gdpr_001", "gdpr_002"]
            infrastructure_config = {"encryption": True, "audit_logging": True}
            
            assessment = await integrator.assess_compliance(
                framework=ComplianceFramework.GDPR,
                industry=IndustryType.TECHNOLOGY,
                current_controls=current_controls,
                infrastructure_config=infrastructure_config
            )
            
            assert isinstance(assessment, ComplianceAssessment)
            assert assessment.framework == ComplianceFramework.GDPR
            assert assessment.industry == IndustryType.TECHNOLOGY
            assert 0 <= assessment.overall_score <= 1
            assert assessment.requirements_met >= 0
            assert assessment.total_requirements > 0
    
    @pytest.mark.asyncio
    async def test_get_compliance_summary(self, integrator):
        """Test getting compliance summary for industry."""
        async with integrator:
            summary = await integrator.get_compliance_summary(IndustryType.HEALTHCARE)
            
            assert "industry" in summary
            assert summary["industry"] == IndustryType.HEALTHCARE.value
            assert "applicable_frameworks" in summary
            assert "framework_details" in summary
            assert len(summary["applicable_frameworks"]) > 0
    
    @pytest.mark.asyncio
    async def test_check_regulatory_updates(self, integrator):
        """Test checking for regulatory updates."""
        async with integrator:
            updates = await integrator.check_regulatory_updates([
                ComplianceFramework.GDPR,
                ComplianceFramework.HIPAA
            ])
            
            assert "check_date" in updates
            assert "frameworks_checked" in updates
            assert "updates_found" in updates
            assert "recommendations" in updates


class TestBusinessToolsIntegrator:
    """Test business tools integrations."""
    
    @pytest.fixture
    def integrator(self):
        """Create business tools integrator instance."""
        return BusinessToolsIntegrator()
    
    def test_initialization(self, integrator):
        """Test integrator initialization."""
        assert integrator is not None
        assert integrator.slack_config is not None
        assert integrator.teams_config is not None
        assert integrator.email_config is not None
        assert len(integrator.message_templates) > 0
    
    @pytest.mark.asyncio
    async def test_send_slack_message_webhook(self, integrator):
        """Test sending Slack message via webhook."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Enable Slack integration for test
            integrator.slack_config["enabled"] = True
            integrator.slack_config["webhook_url"] = "https://hooks.slack.com/test"
            
            async with integrator:
                message = SlackMessage(
                    channel="#general",
                    text="Test message"
                )
                
                result = await integrator.send_slack_message(message)
                
                assert result["success"] is True
                assert result["method"] == "webhook"
    
    @pytest.mark.asyncio
    async def test_send_teams_message(self, integrator):
        """Test sending Teams message."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Enable Teams integration for test
            integrator.teams_config["enabled"] = True
            integrator.teams_config["webhook_url"] = "https://outlook.office.com/webhook/test"
            
            async with integrator:
                message = TeamsMessage(
                    title="Test Message",
                    text="This is a test message"
                )
                
                result = await integrator.send_teams_message(message)
                
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_send_email(self, integrator):
        """Test sending email."""
        with patch('smtplib.SMTP') as mock_smtp:
            # Mock SMTP server
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Enable email integration for test
            integrator.email_config["enabled"] = True
            
            async with integrator:
                result = await integrator.send_email(
                    to_email="test@example.com",
                    subject="Test Subject",
                    content="Test content"
                )
                
                assert result["success"] is True
                mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification(self, integrator):
        """Test sending notification."""
        with patch.object(integrator, '_send_email_notification') as mock_email:
            mock_email.return_value = {"success": True}
            
            async with integrator:
                notification = NotificationMessage(
                    message_type=MessageType.SYSTEM_NOTIFICATION,
                    title="Test Notification",
                    content="Test content with {test_param}",
                    priority=NotificationPriority.MEDIUM,
                    recipient="test@example.com",
                    channel=NotificationChannel.EMAIL,
                    metadata={"test_param": "test_value"}
                )
                
                result = await integrator.send_notification(notification)
                
                assert result["success"] is True
                mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_bulk_notifications(self, integrator):
        """Test sending bulk notifications."""
        with patch.object(integrator, 'send_notification') as mock_send:
            mock_send.return_value = {"success": True}
            
            notifications = [
                NotificationMessage(
                    message_type=MessageType.SYSTEM_NOTIFICATION,
                    title=f"Test Notification {i}",
                    content="Test content",
                    priority=NotificationPriority.MEDIUM,
                    recipient=f"test{i}@example.com",
                    channel=NotificationChannel.EMAIL,
                    metadata={}
                )
                for i in range(3)
            ]
            
            async with integrator:
                result = await integrator.send_bulk_notifications(notifications)
                
                assert result["total"] == 3
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert mock_send.call_count == 3
    
    @pytest.mark.asyncio
    async def test_test_integrations(self, integrator):
        """Test integration testing functionality."""
        async with integrator:
            test_results = await integrator.test_integrations()
            
            assert "timestamp" in test_results
            assert "integrations" in test_results
            assert "slack" in test_results["integrations"]
            assert "teams" in test_results["integrations"]
            assert "email" in test_results["integrations"]


class TestSSOProviderIntegrator:
    """Test SSO provider integrations."""
    
    @pytest.fixture
    def integrator(self):
        """Create SSO provider integrator instance."""
        return SSOProviderIntegrator()
    
    def test_initialization(self, integrator):
        """Test integrator initialization."""
        assert integrator is not None
        assert isinstance(integrator.providers, dict)
    
    @pytest.mark.asyncio
    async def test_initiate_authorization(self, integrator):
        """Test initiating OAuth2 authorization."""
        # Mock provider configuration
        integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
            provider=SSOProvider.GOOGLE_WORKSPACE,
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            enabled=True
        )
        
        with patch('src.infra_mind.core.cache.cache_manager.set') as mock_cache:
            mock_cache.return_value = None
            
            async with integrator:
                auth_request = await integrator.initiate_authorization(
                    provider=SSOProvider.GOOGLE_WORKSPACE,
                    redirect_uri="https://app.example.com/callback"
                )
                
                assert isinstance(auth_request, AuthorizationRequest)
                assert auth_request.provider == SSOProvider.GOOGLE_WORKSPACE
                assert auth_request.state is not None
                assert auth_request.nonce is not None
                assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_request.authorization_url
    
    @pytest.mark.asyncio
    async def test_exchange_authorization_code(self, integrator):
        """Test exchanging authorization code for tokens."""
        # Mock provider configuration
        integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
            provider=SSOProvider.GOOGLE_WORKSPACE,
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            enabled=True
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful token response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "access_token": "test_access_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with integrator:
                tokens = await integrator._exchange_authorization_code(
                    provider=SSOProvider.GOOGLE_WORKSPACE,
                    authorization_code="test_code",
                    redirect_uri="https://app.example.com/callback"
                )
                
                assert "access_token" in tokens
                assert tokens["access_token"] == "test_access_token"
    
    @pytest.mark.asyncio
    async def test_get_user_info(self, integrator):
        """Test getting user info from SSO provider."""
        # Mock provider configuration
        integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
            provider=SSOProvider.GOOGLE_WORKSPACE,
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            enabled=True
        )
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful userinfo response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "sub": "123456789",
                "email": "test@example.com",
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "picture": "https://example.com/avatar.jpg"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with integrator:
                sso_user = await integrator._get_user_info(
                    provider=SSOProvider.GOOGLE_WORKSPACE,
                    access_token="test_access_token"
                )
                
                assert isinstance(sso_user, SSOUser)
                assert sso_user.provider == SSOProvider.GOOGLE_WORKSPACE
                assert sso_user.email == "test@example.com"
                assert sso_user.full_name == "Test User"
    
    def test_parse_user_info_google(self, integrator):
        """Test parsing Google user info."""
        user_data = {
            "sub": "123456789",
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg"
        }
        
        sso_user = integrator._parse_user_info(SSOProvider.GOOGLE_WORKSPACE, user_data)
        
        assert sso_user.provider == SSOProvider.GOOGLE_WORKSPACE
        assert sso_user.provider_user_id == "123456789"
        assert sso_user.email == "test@example.com"
        assert sso_user.full_name == "Test User"
        assert sso_user.first_name == "Test"
        assert sso_user.last_name == "User"
        assert sso_user.avatar_url == "https://example.com/avatar.jpg"
    
    def test_parse_user_info_azure(self, integrator):
        """Test parsing Azure AD user info."""
        user_data = {
            "id": "azure-user-id",
            "userPrincipalName": "test@company.com",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User",
            "jobTitle": "Developer",
            "department": "Engineering",
            "companyName": "Test Company"
        }
        
        sso_user = integrator._parse_user_info(SSOProvider.AZURE_AD, user_data)
        
        assert sso_user.provider == SSOProvider.AZURE_AD
        assert sso_user.provider_user_id == "azure-user-id"
        assert sso_user.email == "test@company.com"
        assert sso_user.full_name == "Test User"
        assert sso_user.job_title == "Developer"
        assert sso_user.department == "Engineering"
        assert sso_user.company == "Test Company"
    
    def test_get_enabled_providers(self, integrator):
        """Test getting enabled providers."""
        # Mock some enabled providers
        integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
            provider=SSOProvider.GOOGLE_WORKSPACE,
            client_id="test",
            client_secret="test",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="test",
            token_url="test",
            enabled=True
        )
        
        integrator.providers[SSOProvider.AZURE_AD] = SSOConfiguration(
            provider=SSOProvider.AZURE_AD,
            client_id="test",
            client_secret="test",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="test",
            token_url="test",
            enabled=False
        )
        
        enabled_providers = integrator.get_enabled_providers()
        
        assert SSOProvider.GOOGLE_WORKSPACE in enabled_providers
        assert SSOProvider.AZURE_AD not in enabled_providers
    
    @pytest.mark.asyncio
    async def test_test_provider_connection(self, integrator):
        """Test provider connection testing."""
        # Mock provider configuration
        integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = SSOConfiguration(
            provider=SSOProvider.GOOGLE_WORKSPACE,
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_method=AuthenticationMethod.OIDC,
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            jwks_url="https://www.googleapis.com/oauth2/v3/certs",
            enabled=True
        )
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful JWKS response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with integrator:
                test_result = await integrator.test_provider_connection(
                    SSOProvider.GOOGLE_WORKSPACE
                )
                
                assert test_result["provider"] == SSOProvider.GOOGLE_WORKSPACE.value
                assert test_result["configured"] is True
                assert test_result["enabled"] is True
                assert test_result["jwks_accessible"] is True


class TestIntegrationEndpoints:
    """Test integration API endpoints."""
    
    @pytest.mark.asyncio
    async def test_compliance_frameworks_endpoint(self):
        """Test compliance frameworks endpoint."""
        from src.infra_mind.api.endpoints.integrations import get_compliance_frameworks
        from src.infra_mind.models.user import User
        
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        
        result = await get_compliance_frameworks(mock_user)
        
        assert "frameworks" in result
        assert "total" in result
        assert len(result["frameworks"]) > 0
        assert result["total"] == len(result["frameworks"])
    
    @pytest.mark.asyncio
    async def test_industry_types_endpoint(self):
        """Test industry types endpoint."""
        from src.infra_mind.api.endpoints.integrations import get_industry_types
        from src.infra_mind.models.user import User
        
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        
        result = await get_industry_types(mock_user)
        
        assert "industries" in result
        assert "total" in result
        assert len(result["industries"]) > 0
        assert result["total"] == len(result["industries"])
    
    @pytest.mark.asyncio
    async def test_notification_channels_endpoint(self):
        """Test notification channels endpoint."""
        from src.infra_mind.api.endpoints.integrations import get_notification_channels
        from src.infra_mind.models.user import User
        
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        
        result = await get_notification_channels(mock_user)
        
        assert "channels" in result
        assert "total" in result
        assert len(result["channels"]) > 0
        assert result["total"] == len(result["channels"])


# Integration test fixtures and utilities

@pytest.fixture
def mock_assessment():
    """Create mock assessment for testing."""
    from src.infra_mind.models.assessment import Assessment
    
    assessment = Mock(spec=Assessment)
    assessment.id = "test_assessment_id"
    assessment.title = "Test Assessment"
    assessment.completed_at = datetime.now(timezone.utc)
    assessment.agent_states = {"cto": {}, "cloud_engineer": {}}
    
    return assessment


@pytest.fixture
def mock_report():
    """Create mock report for testing."""
    from src.infra_mind.models.report import Report
    
    report = Mock(spec=Report)
    report.id = "test_report_id"
    report.report_type = "executive_summary"
    report.content = {"title": "Test Report"}
    report.created_at = datetime.now(timezone.utc)
    
    return report


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])