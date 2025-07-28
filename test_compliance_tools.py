#!/usr/bin/env python3
"""
Test compliance-specific tools.

This test verifies the compliance checker and security analyzer tools.
"""

import asyncio
import logging
from src.infra_mind.agents.tools import ComplianceCheckerTool, SecurityAnalyzerTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_compliance_checker_tool():
    """Test compliance checker tool."""
    print("Testing compliance checker tool...")
    
    tool = ComplianceCheckerTool()
    
    # Test GDPR compliance check
    gdpr_requirements = {
        "encryption_at_rest": True,
        "data_retention_policy": True,
        "consent_management": True,
        "data_subject_rights": True,
        "breach_notification": True
    }
    
    result = await tool.execute(
        regulation="GDPR",
        requirements=gdpr_requirements,
        operation="check"
    )
    
    assert result.is_success
    assert result.data["regulation"] == "GDPR"
    assert result.data["compliance_score"] == 1.0  # Perfect score
    assert result.data["overall_status"] == "COMPLIANT"
    
    print("✅ GDPR compliance check passed")
    
    # Test HIPAA compliance check
    hipaa_requirements = {
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "access_controls": True,
        "audit_logging": True,
        "business_associate_agreements": True
    }
    
    result = await tool.execute(
        regulation="HIPAA",
        requirements=hipaa_requirements,
        operation="check"
    )
    
    assert result.is_success
    assert result.data["regulation"] == "HIPAA"
    assert result.data["compliance_score"] == 1.0  # Perfect score
    assert result.data["overall_status"] == "COMPLIANT"
    
    print("✅ HIPAA compliance check passed")
    
    # Test CCPA compliance check
    ccpa_requirements = {
        "data_inventory": True,
        "privacy_policy": True,
        "opt_out_mechanism": True,
        "data_deletion": True
    }
    
    result = await tool.execute(
        regulation="CCPA",
        requirements=ccpa_requirements,
        operation="check"
    )
    
    assert result.is_success
    assert result.data["regulation"] == "CCPA"
    assert result.data["compliance_score"] == 1.0  # Perfect score
    assert result.data["overall_status"] == "COMPLIANT"
    
    print("✅ CCPA compliance check passed")


async def test_compliance_gap_analysis():
    """Test compliance gap analysis."""
    print("Testing compliance gap analysis...")
    
    tool = ComplianceCheckerTool()
    
    # Test with poor GDPR compliance
    poor_gdpr_requirements = {
        "encryption_at_rest": False,
        "data_retention_policy": False,
        "consent_management": False,
        "data_subject_rights": False,
        "breach_notification": False
    }
    
    result = await tool.execute(
        regulation="GDPR",
        requirements=poor_gdpr_requirements,
        operation="gap_analysis"
    )
    
    assert result.is_success
    assert result.data["regulation"] == "GDPR"
    assert result.data["total_gaps"] == 5  # All requirements missing
    assert result.data["compliance_score"] == 0.0
    assert result.data["remediation_priority"] == "critical"
    
    print("✅ GDPR gap analysis passed")


async def test_compliance_recommendations():
    """Test compliance recommendations."""
    print("Testing compliance recommendations...")
    
    tool = ComplianceCheckerTool()
    
    # Test recommendations for poor HIPAA compliance
    poor_hipaa_requirements = {
        "encryption_at_rest": False,
        "encryption_in_transit": False,
        "access_controls": False,
        "audit_logging": False,
        "business_associate_agreements": False
    }
    
    result = await tool.execute(
        regulation="HIPAA",
        requirements=poor_hipaa_requirements,
        operation="recommendations"
    )
    
    assert result.is_success
    assert result.data["regulation"] == "HIPAA"
    assert len(result.data["recommendations"]) > 0
    
    # Check recommendation structure
    for rec in result.data["recommendations"]:
        assert "requirement" in rec
        assert "recommendation" in rec
        assert "priority" in rec
        assert "effort" in rec
    
    print("✅ HIPAA recommendations passed")


async def test_security_analyzer_tool():
    """Test security analyzer tool."""
    print("Testing security analyzer tool...")
    
    tool = SecurityAnalyzerTool()
    
    # Test comprehensive security analysis with good config
    good_security_config = {
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "key_management": True,
        "multi_factor_auth": True,
        "role_based_access": True,
        "access_monitoring": True,
        "firewall_configured": True,
        "vpc_isolation": True,
        "intrusion_detection": True,
        "centralized_logging": True,
        "security_monitoring": True,
        "audit_trails": True
    }
    
    result = await tool.execute(
        security_config=good_security_config,
        analysis_type="comprehensive"
    )
    
    assert result.is_success
    assert "overall_score" in result.data
    assert "categories" in result.data
    assert "recommendations" in result.data
    assert "critical_issues" in result.data
    
    # Should have high overall score with good config
    assert result.data["overall_score"] > 0.8
    
    # Check categories
    categories = result.data["categories"]
    assert "encryption" in categories
    assert "access_control" in categories
    assert "network_security" in categories
    assert "monitoring" in categories
    
    # All categories should have good scores
    for category, details in categories.items():
        assert details["score"] > 0.7
        assert details["status"] == "good"
    
    print("✅ Comprehensive security analysis passed")
    
    # Test with poor security config
    poor_security_config = {
        "encryption_at_rest": False,
        "encryption_in_transit": False,
        "key_management": False,
        "multi_factor_auth": False,
        "role_based_access": False,
        "access_monitoring": False,
        "firewall_configured": False,
        "vpc_isolation": False,
        "centralized_logging": False,
        "security_monitoring": False,
        "audit_trails": False
    }
    
    result = await tool.execute(
        security_config=poor_security_config,
        analysis_type="comprehensive"
    )
    
    assert result.is_success
    assert result.data["overall_score"] < 0.5  # Poor score
    assert len(result.data["recommendations"]) > 0  # Should have recommendations
    assert len(result.data["critical_issues"]) > 0  # Should have critical issues
    
    print("✅ Poor security analysis passed")


async def test_vulnerability_scan():
    """Test vulnerability scan simulation."""
    print("Testing vulnerability scan...")
    
    tool = SecurityAnalyzerTool()
    
    # Test vulnerability scan with insecure config
    insecure_config = {
        "encryption_at_rest": False,
        "multi_factor_auth": False
    }
    
    result = await tool.execute(
        security_config=insecure_config,
        analysis_type="vulnerability_scan"
    )
    
    assert result.is_success
    assert "scan_date" in result.data
    assert "vulnerabilities_found" in result.data
    assert "vulnerabilities" in result.data
    assert "risk_score" in result.data
    
    # Should find vulnerabilities
    assert result.data["vulnerabilities_found"] > 0
    assert result.data["risk_score"] > 0
    
    # Check vulnerability structure
    for vuln in result.data["vulnerabilities"]:
        assert "severity" in vuln
        assert "type" in vuln
        assert "description" in vuln
        assert "remediation" in vuln
    
    print("✅ Vulnerability scan passed")


async def test_risk_assessment():
    """Test security risk assessment."""
    print("Testing security risk assessment...")
    
    tool = SecurityAnalyzerTool()
    
    # Test risk assessment with poor security
    risky_config = {
        "encryption_at_rest": False,
        "access_controls": False,
        "access_monitoring": False,
        "role_based_access": False
    }
    
    result = await tool.execute(
        security_config=risky_config,
        analysis_type="risk_assessment"
    )
    
    assert result.is_success
    assert "assessment_date" in result.data
    assert "total_risks" in result.data
    assert "risks" in result.data
    assert "overall_risk_level" in result.data
    
    # Should identify risks
    assert result.data["total_risks"] > 0
    assert result.data["overall_risk_level"] in ["high", "medium"]
    
    # Check risk structure
    for risk in result.data["risks"]:
        assert "risk_type" in risk
        assert "probability" in risk
        assert "impact" in risk
        assert "description" in risk
        assert "mitigation" in risk
    
    print("✅ Risk assessment passed")


async def test_tool_error_handling():
    """Test tool error handling."""
    print("Testing tool error handling...")
    
    compliance_tool = ComplianceCheckerTool()
    
    # Test with invalid regulation
    result = await compliance_tool.execute(
        regulation="INVALID_REG",
        requirements={},
        operation="check"
    )
    
    # Should handle gracefully (return empty/default results)
    assert result.is_success
    assert result.data["compliance_score"] == 0.0
    
    # Test with invalid operation
    result = await compliance_tool.execute(
        regulation="GDPR",
        requirements={},
        operation="invalid_operation"
    )
    
    # Should return error
    assert not result.is_success
    assert result.error is not None
    
    print("✅ Error handling passed")


async def main():
    """Run all compliance tool tests."""
    print("🚀 Starting Compliance Tools Tests")
    
    try:
        await test_compliance_checker_tool()
        await test_compliance_gap_analysis()
        await test_compliance_recommendations()
        await test_security_analyzer_tool()
        await test_vulnerability_scan()
        await test_risk_assessment()
        await test_tool_error_handling()
        
        print("\n✅ All compliance tool tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())