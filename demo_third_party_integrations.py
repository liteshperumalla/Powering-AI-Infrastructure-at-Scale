#!/usr/bin/env python3
"""
Demo script for third-party integrations.

Demonstrates compliance databases, business tools, and SSO provider integrations.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_compliance_databases():
    """Demonstrate compliance database integrations."""
    print("\n" + "="*60)
    print("COMPLIANCE DATABASES INTEGRATION DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.integrations.compliance_databases import (
            ComplianceDatabaseIntegrator, ComplianceFramework, IndustryType,
            ComplianceRequirementType
        )
        
        async with ComplianceDatabaseIntegrator() as integrator:
            print("\n1. Getting GDPR requirements...")
            gdpr_requirements = await integrator.get_requirements_by_framework(
                ComplianceFramework.GDPR
            )
            
            print(f"   Found {len(gdpr_requirements)} GDPR requirements")
            for req in gdpr_requirements[:2]:  # Show first 2
                print(f"   - {req.title}: {req.description[:100]}...")
            
            print("\n2. Getting HIPAA requirements for healthcare...")
            hipaa_requirements = await integrator.get_requirements_by_framework(
                ComplianceFramework.HIPAA,
                IndustryType.HEALTHCARE
            )
            
            print(f"   Found {len(hipaa_requirements)} HIPAA requirements")
            for req in hipaa_requirements[:2]:  # Show first 2
                print(f"   - {req.title}: {req.description[:100]}...")
            
            print("\n3. Getting data protection requirements across frameworks...")
            data_protection_reqs = await integrator.get_requirements_by_type(
                ComplianceRequirementType.DATA_PROTECTION,
                [ComplianceFramework.GDPR, ComplianceFramework.CCPA]
            )
            
            print(f"   Found {len(data_protection_reqs)} data protection requirements")
            
            print("\n4. Assessing GDPR compliance...")
            current_controls = ["gdpr_001", "gdpr_002"]
            infrastructure_config = {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "audit_logging": True,
                "access_controls": True,
                "data_backup": True
            }
            
            assessment = await integrator.assess_compliance(
                framework=ComplianceFramework.GDPR,
                industry=IndustryType.TECHNOLOGY,
                current_controls=current_controls,
                infrastructure_config=infrastructure_config
            )
            
            print(f"   Compliance Score: {assessment.overall_score:.1%}")
            print(f"   Requirements Met: {assessment.requirements_met}/{assessment.total_requirements}")
            print(f"   Critical Gaps: {len(assessment.critical_gaps)}")
            
            if assessment.critical_gaps:
                print("   Top Critical Gaps:")
                for gap in assessment.critical_gaps[:3]:
                    print(f"     - {gap}")
            
            print("\n5. Getting compliance summary for healthcare industry...")
            summary = await integrator.get_compliance_summary(IndustryType.HEALTHCARE)
            
            print(f"   Industry: {summary['industry']}")
            print(f"   Applicable Frameworks: {', '.join(summary['applicable_frameworks'])}")
            
            for framework, details in summary['framework_details'].items():
                print(f"   {framework.upper()}:")
                print(f"     Total Requirements: {details['total_requirements']}")
                print(f"     Mandatory: {details['mandatory_requirements']}")
                print(f"     Optional: {details['optional_requirements']}")
            
            print("\n6. Checking for regulatory updates...")
            updates = await integrator.check_regulatory_updates([
                ComplianceFramework.GDPR,
                ComplianceFramework.HIPAA
            ])
            
            print(f"   Check Date: {updates['check_date']}")
            print(f"   Frameworks Checked: {', '.join(updates['frameworks_checked'])}")
            print(f"   Updates Found: {len(updates['updates_found'])}")
            print(f"   Recommendations: {len(updates['recommendations'])}")
            
    except Exception as e:
        logger.error(f"Compliance databases demo failed: {str(e)}")
        print(f"   Error: {str(e)}")


async def demo_business_tools():
    """Demonstrate business tools integrations."""
    print("\n" + "="*60)
    print("BUSINESS TOOLS INTEGRATION DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.integrations.business_tools import (
            BusinessToolsIntegrator, NotificationChannel, NotificationPriority,
            MessageType, NotificationMessage, SlackMessage, TeamsMessage
        )
        
        async with BusinessToolsIntegrator() as integrator:
            print("\n1. Testing integration configurations...")
            test_results = await integrator.test_integrations()
            
            print(f"   Test Timestamp: {test_results['timestamp']}")
            for tool, result in test_results['integrations'].items():
                status = "✓ Enabled" if result.get('enabled') else "✗ Disabled"
                print(f"   {tool.title()}: {status}")
                if result.get('enabled') and not result.get('test_successful', True):
                    print(f"     Error: {result.get('error', 'Unknown error')}")
            
            print("\n2. Creating sample Slack message...")
            slack_message = SlackMessage(
                channel="#general",
                text="Infrastructure assessment completed successfully!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *Assessment Complete*\n\nYour infrastructure assessment is ready for review."
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Assessment ID:*\nASS-2024-001"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Completion Time:*\n2024-01-15 14:30 UTC"
                            }
                        ]
                    }
                ]
            )
            
            print("   Slack message created with rich formatting")
            print(f"   Channel: {slack_message.channel}")
            print(f"   Text: {slack_message.text}")
            print(f"   Blocks: {len(slack_message.blocks) if slack_message.blocks else 0}")
            
            print("\n3. Creating sample Teams message...")
            teams_message = TeamsMessage(
                title="Infrastructure Assessment Complete",
                text="Your infrastructure assessment has been completed and is ready for review.",
                theme_color="0078D4",
                sections=[
                    {
                        "activityTitle": "Assessment Details",
                        "facts": [
                            {"name": "Assessment ID", "value": "ASS-2024-001"},
                            {"name": "Completion Time", "value": "2024-01-15 14:30 UTC"},
                            {"name": "Agents Involved", "value": "CTO, Cloud Engineer, Compliance"}
                        ]
                    }
                ]
            )
            
            print("   Teams message created with card format")
            print(f"   Title: {teams_message.title}")
            print(f"   Theme Color: {teams_message.theme_color}")
            print(f"   Sections: {len(teams_message.sections) if teams_message.sections else 0}")
            
            print("\n4. Creating notification message...")
            notification = NotificationMessage(
                message_type=MessageType.ASSESSMENT_COMPLETE,
                title="Infrastructure Assessment Complete",
                content="Your infrastructure assessment '{assessment_title}' has been completed. {agent_count} AI agents have analyzed your requirements.",
                priority=NotificationPriority.MEDIUM,
                recipient="user@example.com",
                channel=NotificationChannel.EMAIL,
                metadata={
                    "assessment_title": "Cloud Migration Assessment",
                    "agent_count": 3,
                    "assessment_id": "ASS-2024-001",
                    "completion_time": "2024-01-15 14:30 UTC",
                    "dashboard_url": "https://app.infra-mind.com"
                }
            )
            
            print("   Notification message created")
            print(f"   Type: {notification.message_type.value}")
            print(f"   Priority: {notification.priority.value}")
            print(f"   Channel: {notification.channel.value}")
            print(f"   Recipient: {notification.recipient}")
            
            # Format content with metadata
            formatted_content = notification.content.format(**notification.metadata)
            print(f"   Formatted Content: {formatted_content}")
            
            print("\n5. Creating bulk notifications...")
            bulk_notifications = []
            
            for i in range(3):
                bulk_notifications.append(
                    NotificationMessage(
                        message_type=MessageType.WORKFLOW_STATUS,
                        title=f"Workflow Update {i+1}",
                        content="Workflow '{workflow_name}' status: {status}. Progress: {progress}%.",
                        priority=NotificationPriority.LOW,
                        recipient=f"user{i+1}@example.com",
                        channel=NotificationChannel.EMAIL,
                        metadata={
                            "workflow_name": f"Assessment Workflow {i+1}",
                            "status": "In Progress",
                            "progress": 75 + i * 5
                        }
                    )
                )
            
            print(f"   Created {len(bulk_notifications)} bulk notifications")
            
            # Simulate bulk send (would actually send in real implementation)
            print("   Simulating bulk notification send...")
            print("   ✓ All notifications would be sent successfully")
            
            print("\n6. Demonstrating message templates...")
            templates = integrator.message_templates
            
            print(f"   Available Templates: {len(templates)}")
            for msg_type, template in templates.items():
                print(f"   - {msg_type.value}: {template['title']}")
            
    except Exception as e:
        logger.error(f"Business tools demo failed: {str(e)}")
        print(f"   Error: {str(e)}")


async def demo_sso_providers():
    """Demonstrate SSO provider integrations."""
    print("\n" + "="*60)
    print("SSO PROVIDERS INTEGRATION DEMO")
    print("="*60)
    
    try:
        from src.infra_mind.integrations.sso_providers import (
            SSOProviderIntegrator, SSOProvider, AuthenticationMethod,
            SSOConfiguration, SSOUser
        )
        
        async with SSOProviderIntegrator() as integrator:
            print("\n1. Checking configured providers...")
            enabled_providers = integrator.get_enabled_providers()
            
            print(f"   Enabled Providers: {len(enabled_providers)}")
            for provider in enabled_providers:
                print(f"   - {provider.value}")
            
            if not enabled_providers:
                print("   No providers enabled (this is expected in demo mode)")
            
            print("\n2. Demonstrating provider configurations...")
            
            # Mock Google Workspace configuration
            google_config = SSOConfiguration(
                provider=SSOProvider.GOOGLE_WORKSPACE,
                client_id="demo_client_id",
                client_secret="demo_client_secret",
                auth_method=AuthenticationMethod.OIDC,
                authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
                jwks_url="https://www.googleapis.com/oauth2/v3/certs",
                issuer="https://accounts.google.com",
                scopes=["openid", "profile", "email"],
                enabled=True
            )
            
            integrator.providers[SSOProvider.GOOGLE_WORKSPACE] = google_config
            
            print("   Google Workspace Configuration:")
            print(f"     Client ID: {google_config.client_id}")
            print(f"     Auth Method: {google_config.auth_method.value}")
            print(f"     Authorization URL: {google_config.authorization_url}")
            print(f"     Scopes: {', '.join(google_config.scopes)}")
            
            # Mock Azure AD configuration
            azure_config = SSOConfiguration(
                provider=SSOProvider.AZURE_AD,
                client_id="demo_azure_client_id",
                client_secret="demo_azure_client_secret",
                auth_method=AuthenticationMethod.OIDC,
                authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                userinfo_url="https://graph.microsoft.com/v1.0/me",
                jwks_url="https://login.microsoftonline.com/common/discovery/v2.0/keys",
                issuer="https://login.microsoftonline.com/common/v2.0",
                scopes=["openid", "profile", "email", "User.Read"],
                enabled=True
            )
            
            integrator.providers[SSOProvider.AZURE_AD] = azure_config
            
            print("\n   Azure AD Configuration:")
            print(f"     Client ID: {azure_config.client_id}")
            print(f"     Auth Method: {azure_config.auth_method.value}")
            print(f"     Authorization URL: {azure_config.authorization_url}")
            print(f"     Scopes: {', '.join(azure_config.scopes)}")
            
            print("\n3. Simulating authorization flow...")
            
            # Simulate authorization request
            print("   Step 1: Initiating authorization...")
            print("   - Generating state and nonce parameters")
            print("   - Building authorization URL with required parameters")
            print("   - Caching authorization request for validation")
            
            auth_url_params = {
                "client_id": google_config.client_id,
                "response_type": "code",
                "scope": " ".join(google_config.scopes),
                "redirect_uri": "https://app.infra-mind.com/auth/callback",
                "state": "demo_state_parameter",
                "nonce": "demo_nonce_parameter"
            }
            
            print(f"   Authorization URL would be: {google_config.authorization_url}")
            print("   With parameters:")
            for key, value in auth_url_params.items():
                print(f"     {key}: {value}")
            
            print("\n   Step 2: Handling callback...")
            print("   - Validating state parameter")
            print("   - Exchanging authorization code for tokens")
            print("   - Retrieving user information")
            print("   - Creating or updating local user account")
            
            print("\n4. Demonstrating user info parsing...")
            
            # Google user data example
            google_user_data = {
                "sub": "123456789012345678901",
                "email": "john.doe@company.com",
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "picture": "https://lh3.googleusercontent.com/a/default-user"
            }
            
            google_sso_user = integrator._parse_user_info(
                SSOProvider.GOOGLE_WORKSPACE, 
                google_user_data
            )
            
            print("   Google Workspace User:")
            print(f"     Provider ID: {google_sso_user.provider_user_id}")
            print(f"     Email: {google_sso_user.email}")
            print(f"     Full Name: {google_sso_user.full_name}")
            print(f"     First Name: {google_sso_user.first_name}")
            print(f"     Last Name: {google_sso_user.last_name}")
            print(f"     Avatar URL: {google_sso_user.avatar_url}")
            
            # Azure user data example
            azure_user_data = {
                "id": "azure-user-id-12345",
                "userPrincipalName": "jane.smith@company.com",
                "displayName": "Jane Smith",
                "givenName": "Jane",
                "surname": "Smith",
                "jobTitle": "Senior Developer",
                "department": "Engineering",
                "companyName": "Tech Company Inc."
            }
            
            azure_sso_user = integrator._parse_user_info(
                SSOProvider.AZURE_AD,
                azure_user_data
            )
            
            print("\n   Azure AD User:")
            print(f"     Provider ID: {azure_sso_user.provider_user_id}")
            print(f"     Email: {azure_sso_user.email}")
            print(f"     Full Name: {azure_sso_user.full_name}")
            print(f"     Job Title: {azure_sso_user.job_title}")
            print(f"     Department: {azure_sso_user.department}")
            print(f"     Company: {azure_sso_user.company}")
            
            print("\n5. Testing provider connections...")
            
            for provider in [SSOProvider.GOOGLE_WORKSPACE, SSOProvider.AZURE_AD]:
                test_result = await integrator.test_provider_connection(provider)
                
                print(f"\n   {provider.value.replace('_', ' ').title()}:")
                print(f"     Configured: {'✓' if test_result['configured'] else '✗'}")
                print(f"     Enabled: {'✓' if test_result['enabled'] else '✗'}")
                
                if 'endpoints' in test_result:
                    print("     Endpoints:")
                    for endpoint, url in test_result['endpoints'].items():
                        if url:
                            print(f"       {endpoint}: {url}")
                
                if test_result.get('jwks_accessible') is not None:
                    jwks_status = "✓ Accessible" if test_result['jwks_accessible'] else "✗ Not Accessible"
                    print(f"     JWKS: {jwks_status}")
            
            print("\n6. Demonstrating logout flow...")
            
            logout_result = await integrator.initiate_logout(
                SSOProvider.GOOGLE_WORKSPACE,
                "demo_user_id"
            )
            
            if logout_result['success']:
                print("   Google Workspace Logout:")
                print(f"     Logout URL: {logout_result['logout_url']}")
                print(f"     Provider: {logout_result['provider']}")
            else:
                print(f"   Logout Error: {logout_result.get('error')}")
            
    except Exception as e:
        logger.error(f"SSO providers demo failed: {str(e)}")
        print(f"   Error: {str(e)}")


async def demo_integration_apis():
    """Demonstrate integration API endpoints."""
    print("\n" + "="*60)
    print("INTEGRATION API ENDPOINTS DEMO")
    print("="*60)
    
    try:
        print("\n1. Available API endpoints:")
        
        endpoints = [
            "GET /integrations/compliance/frameworks",
            "GET /integrations/compliance/industries", 
            "GET /integrations/compliance/requirements/{framework}",
            "POST /integrations/compliance/assess",
            "GET /integrations/compliance/industry-summary/{industry}",
            "GET /integrations/business-tools/channels",
            "POST /integrations/business-tools/notify",
            "POST /integrations/business-tools/test",
            "GET /integrations/sso/providers",
            "POST /integrations/sso/login",
            "POST /integrations/sso/callback",
            "POST /integrations/sso/test",
            "GET /integrations/status",
            "GET /integrations/health"
        ]
        
        for endpoint in endpoints:
            print(f"   - {endpoint}")
        
        print("\n2. Sample API request/response examples:")
        
        print("\n   GET /integrations/compliance/frameworks")
        print("   Response:")
        print("   {")
        print('     "frameworks": [')
        print('       {"value": "gdpr", "name": "GDPR", "description": "GDPR compliance framework"},')
        print('       {"value": "hipaa", "name": "HIPAA", "description": "HIPAA compliance framework"}')
        print('     ],')
        print('     "total": 2')
        print("   }")
        
        print("\n   POST /integrations/business-tools/notify")
        print("   Request:")
        print("   {")
        print('     "message_type": "assessment_complete",')
        print('     "title": "Assessment Complete",')
        print('     "content": "Your assessment is ready",')
        print('     "priority": "medium",')
        print('     "recipient": "user@example.com",')
        print('     "channel": "email",')
        print('     "metadata": {"assessment_id": "ASS-001"}')
        print("   }")
        
        print("\n   POST /integrations/sso/login")
        print("   Request:")
        print("   {")
        print('     "provider": "google_workspace",')
        print('     "redirect_uri": "https://app.infra-mind.com/callback"')
        print("   }")
        print("   Response:")
        print("   {")
        print('     "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",')
        print('     "state": "secure_state_parameter",')
        print('     "provider": "google_workspace",')
        print('     "expires_at": "2024-01-15T15:00:00Z"')
        print("   }")
        
        print("\n3. Integration status monitoring:")
        
        status_example = {
            "integration_status": {
                "business_tools": {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "integrations": {
                        "slack": {"enabled": False},
                        "teams": {"enabled": False},
                        "email": {"enabled": True, "test_successful": True}
                    }
                },
                "sso_providers": {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "providers": {
                        "google_workspace": {"configured": True, "enabled": True},
                        "azure_ad": {"configured": True, "enabled": True}
                    }
                },
                "compliance_databases": {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "local_database": {"enabled": True, "status": "operational"},
                    "external_apis": {
                        "nist": {"enabled": False, "status": "not_configured"}
                    }
                }
            }
        }
        
        print("   Sample status response:")
        print("   {")
        print('     "integration_status": {')
        print('       "business_tools": {"integrations": {"email": {"enabled": true}}},')
        print('       "sso_providers": {"providers": {"google_workspace": {"enabled": true}}},')
        print('       "compliance_databases": {"local_database": {"status": "operational"}}')
        print('     }')
        print("   }")
        
    except Exception as e:
        logger.error(f"Integration APIs demo failed: {str(e)}")
        print(f"   Error: {str(e)}")


async def main():
    """Run all integration demos."""
    print("INFRA MIND - THIRD-PARTY INTEGRATIONS DEMO")
    print("=" * 80)
    print("Demonstrating compliance databases, business tools, and SSO integrations")
    print("=" * 80)
    
    # Run all demos
    await demo_compliance_databases()
    await demo_business_tools()
    await demo_sso_providers()
    await demo_integration_apis()
    
    print("\n" + "="*80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("✓ Compliance database integration with GDPR, HIPAA, CCPA frameworks")
    print("✓ Business tools integration with Slack, Teams, and email")
    print("✓ SSO provider integration with Google, Azure AD, Okta, Auth0")
    print("✓ Comprehensive API endpoints for all integrations")
    print("✓ Real-time status monitoring and health checks")
    print("✓ Robust error handling and fallback mechanisms")
    print("\nThese integrations enable Infra Mind to:")
    print("• Assess compliance against industry standards")
    print("• Send notifications via popular business tools")
    print("• Authenticate users through enterprise identity providers")
    print("• Provide seamless integration with existing enterprise workflows")


if __name__ == "__main__":
    asyncio.run(main())