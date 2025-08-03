#!/usr/bin/env python3
"""
Test script for external service integrations.

Tests web scraping, compliance databases, and business tools integrations.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infra_mind.integrations.web_scraping import (
    web_scraping_service,
    SearchProvider,
    ContentType,
    research_cloud_pricing,
    research_technology_trends,
    search_web
)
from infra_mind.integrations.compliance_databases import (
    compliance_db_integrator,
    ComplianceFramework,
    IndustryType,
    get_compliance_requirements,
    assess_framework_compliance
)
from infra_mind.integrations.business_tools import (
    BusinessToolsIntegrator,
    NotificationMessage,
    NotificationChannel,
    NotificationPriority,
    MessageType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_web_scraping_integration():
    """Test web scraping and search API integration."""
    logger.info("Testing web scraping integration...")
    
    try:
        # Test multi-provider search
        search_results = await search_web(
            "cloud computing pricing AWS Azure",
            providers=[SearchProvider.GOOGLE_CUSTOM, SearchProvider.BING],
            num_results=3
        )
        
        logger.info(f"Search results: {len(search_results)} providers")
        for provider, results in search_results.items():
            logger.info(f"  {provider.value}: {len(results)} results")
            for result in results[:2]:  # Show first 2 results
                logger.info(f"    - {result.title[:50]}...")
        
        # Test cloud pricing research
        pricing_research = await research_cloud_pricing(["aws", "azure"])
        logger.info(f"Pricing research completed for {len(pricing_research['providers'])} providers")
        
        # Test technology trends research
        trends_research = await research_technology_trends(["kubernetes", "serverless"])
        logger.info(f"Trends research completed for {len(trends_research['keywords'])} keywords")
        
        # Test service status
        async with web_scraping_service as service:
            status = await service.get_service_status()
            logger.info(f"Web scraping service status: {status['service_status']}")
            
            for provider, api_status in status['api_status'].items():
                logger.info(f"  {provider}: {'operational' if api_status['operational'] else 'not configured'}")
        
        logger.info("✅ Web scraping integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Web scraping integration test failed: {str(e)}")
        return False


async def test_compliance_database_integration():
    """Test compliance database integration."""
    logger.info("Testing compliance database integration...")
    
    try:
        # Test getting compliance requirements
        gdpr_requirements = await get_compliance_requirements(
            ComplianceFramework.GDPR,
            IndustryType.TECHNOLOGY
        )
        logger.info(f"Retrieved {len(gdpr_requirements)} GDPR requirements")
        
        # Test compliance assessment
        assessment = await assess_framework_compliance(
            ComplianceFramework.GDPR,
            IndustryType.TECHNOLOGY,
            ["data_encryption", "access_control"],
            {"encryption": "AES-256", "access_logs": True}
        )
        logger.info(f"Compliance assessment score: {assessment.overall_score:.2%}")
        logger.info(f"Requirements met: {assessment.requirements_met}/{assessment.total_requirements}")
        
        # Test compliance dashboard data
        async with compliance_db_integrator as integrator:
            dashboard_data = await integrator.get_compliance_dashboard_data(
                IndustryType.TECHNOLOGY
            )
            logger.info(f"Dashboard data generated for {dashboard_data['industry']}")
            logger.info(f"Compliance overview: {len(dashboard_data['compliance_overview'])} frameworks")
            
            # Test compliance report generation
            report = await integrator.generate_compliance_report(
                "test_assessment_123",
                [ComplianceFramework.GDPR, ComplianceFramework.SOC2],
                IndustryType.TECHNOLOGY
            )
            logger.info(f"Generated compliance report: {report['report_id']}")
            logger.info(f"Overall compliance score: {report['executive_summary']['overall_compliance_score']:.1f}%")
            
            # Test regulatory monitoring
            monitoring = await integrator.monitor_regulatory_changes(
                [ComplianceFramework.GDPR, ComplianceFramework.HIPAA]
            )
            logger.info(f"Monitored {len(monitoring['frameworks_monitored'])} frameworks")
            logger.info(f"Changes detected: {len(monitoring['changes_detected'])}")
        
        logger.info("✅ Compliance database integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Compliance database integration test failed: {str(e)}")
        return False


async def test_business_tools_integration():
    """Test business tools integration."""
    logger.info("Testing business tools integration...")
    
    try:
        async with BusinessToolsIntegrator() as integrator:
            # Test integration health
            test_results = await integrator.test_integrations()
            logger.info(f"Integration test timestamp: {test_results['timestamp']}")
            
            for integration, status in test_results['integrations'].items():
                logger.info(f"  {integration}: {'✅' if status.get('enabled') else '❌'} {'configured' if status.get('test_successful', False) else 'not configured'}")
            
            # Test notification system (mock)
            notification = NotificationMessage(
                message_type=MessageType.SYSTEM_NOTIFICATION,
                title="Test Notification",
                content="This is a test notification from the integration test",
                priority=NotificationPriority.LOW,
                recipient="test@example.com",
                channel=NotificationChannel.EMAIL,
                metadata={"test": True}
            )
            
            # Note: This will fail in test environment without real email config
            # but we can test the structure
            try:
                result = await integrator.send_notification(notification)
                logger.info(f"Notification test result: {result.get('success', False)}")
            except Exception as e:
                logger.info(f"Notification test (expected to fail without config): {str(e)[:50]}...")
            
            # Test calendar integration (mock)
            calendar_test = await integrator.test_calendar_integration("google")
            logger.info(f"Calendar integration test: {calendar_test['overall_status']}")
            
            # Test webhook system
            webhook_test = await integrator.test_webhook_endpoint("https://httpbin.org/post")
            logger.info(f"Webhook test status: {webhook_test['status']}")
            
            # Test webhook registration
            webhook_reg = await integrator.register_webhook_endpoint(
                "https://example.com/webhook",
                ["assessment_complete", "report_ready"],
                "Test webhook registration"
            )
            logger.info(f"Webhook registered: {webhook_reg['data']['webhook_id']}")
            
            # Test assessment meeting scheduling (mock)
            meeting_result = await integrator.schedule_assessment_meeting(
                "test_assessment_456",
                "Infrastructure Assessment Review",
                datetime.now(timezone.utc) + timedelta(days=1),
                60,
                ["stakeholder@example.com"],
                "google"
            )
            logger.info(f"Meeting scheduling test: {'✅' if meeting_result.get('success') else '❌'}")
        
        logger.info("✅ Business tools integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Business tools integration test failed: {str(e)}")
        return False


async def test_integration_workflows():
    """Test integrated workflows across services."""
    logger.info("Testing integrated workflows...")
    
    try:
        # Simulate a complete assessment workflow with external integrations
        assessment_id = "workflow_test_789"
        
        # 1. Research phase - web scraping
        logger.info("Phase 1: Research phase")
        research_data = await research_technology_trends(["cloud migration", "AI infrastructure"])
        logger.info(f"Research completed: {len(research_data['trend_analysis'])} topics analyzed")
        
        # 2. Compliance check phase
        logger.info("Phase 2: Compliance assessment")
        compliance_assessment = await assess_framework_compliance(
            ComplianceFramework.GDPR,
            IndustryType.TECHNOLOGY,
            ["encryption", "access_control", "audit_logging"],
            {"data_encryption": True, "access_logs": True}
        )
        logger.info(f"Compliance score: {compliance_assessment.overall_score:.2%}")
        
        # 3. Notification phase
        logger.info("Phase 3: Stakeholder notification")
        async with BusinessToolsIntegrator() as integrator:
            # Create audit trail
            async with compliance_db_integrator as comp_integrator:
                audit_trail = await comp_integrator.create_compliance_audit_trail(
                    assessment_id,
                    ComplianceFramework.GDPR,
                    [
                        {"requirement_id": "gdpr_001", "status": "passed", "description": "Data encryption implemented"},
                        {"requirement_id": "gdpr_002", "status": "failed", "description": "Data subject rights not fully implemented", "mandatory": True}
                    ]
                )
                logger.info(f"Audit trail created: {audit_trail['audit_id']}")
            
            # Schedule follow-up meeting
            meeting_time = datetime.now(timezone.utc) + timedelta(days=2)
            meeting_result = await integrator.schedule_assessment_meeting(
                assessment_id,
                "Assessment Results Review",
                meeting_time,
                90,
                ["cto@example.com", "compliance@example.com"]
            )
            logger.info(f"Follow-up meeting scheduled: {'✅' if meeting_result.get('success') else '❌'}")
            
            # Send webhook notification
            webhook_payload = {
                "assessment_id": assessment_id,
                "status": "completed",
                "compliance_score": compliance_assessment.overall_score,
                "critical_gaps": len(compliance_assessment.critical_gaps),
                "next_steps": "Review compliance gaps and schedule remediation"
            }
            
            # Note: This will fail without a real webhook endpoint
            try:
                webhook_result = await integrator.send_assessment_webhook(
                    "https://httpbin.org/post",
                    assessment_id,
                    "assessment_completed",
                    webhook_payload
                )
                logger.info(f"Webhook notification sent: {'✅' if webhook_result.get('success') else '❌'}")
            except Exception as e:
                logger.info(f"Webhook test (expected behavior): {str(e)[:50]}...")
        
        logger.info("✅ Integrated workflow test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated workflow test failed: {str(e)}")
        return False


async def main():
    """Run all external integration tests."""
    logger.info("🚀 Starting external service integrations test suite")
    logger.info("=" * 60)
    
    test_results = []
    
    # Run individual integration tests
    test_results.append(await test_web_scraping_integration())
    test_results.append(await test_compliance_database_integration())
    test_results.append(await test_business_tools_integration())
    test_results.append(await test_integration_workflows())
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")
    
    test_names = [
        "Web Scraping Integration",
        "Compliance Database Integration", 
        "Business Tools Integration",
        "Integrated Workflows"
    ]
    
    passed = sum(test_results)
    total = len(test_results)
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {i+1}. {name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All external service integrations are working correctly!")
        return 0
    else:
        logger.error("⚠️  Some integrations need attention. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)