#!/usr/bin/env python3
"""
Basic test for Compliance Agent functionality.

This test verifies the core compliance agent functionality without database dependencies.
"""

import asyncio
import logging
from src.infra_mind.agents.compliance_agent import ComplianceAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockAssessment:
    """Mock assessment for testing."""
    
    def __init__(self, business_req=None, technical_req=None):
        self.id = "test_assessment_id"
        self.user_id = "test_user"
        self.title = "Test Assessment"
        self.business_requirements = business_req or {}
        self.technical_requirements = technical_req or {}
    
    def dict(self):
        return {
            "user_id": self.user_id,
            "title": self.title,
            "business_requirements": self.business_requirements,
            "technical_requirements": self.technical_requirements
        }


async def test_compliance_agent_creation():
    """Test compliance agent creation and basic properties."""
    print("Testing compliance agent creation...")
    
    config = AgentConfig(
        name="Test Compliance Agent",
        role=AgentRole.COMPLIANCE,
        tools_enabled=["data_processor", "compliance_checker", "security_analyzer"]
    )
    
    agent = ComplianceAgent(config)
    
    # Test basic properties
    assert agent.name == "Test Compliance Agent"
    assert agent.role == AgentRole.COMPLIANCE
    assert "GDPR" in agent.regulatory_frameworks
    assert "HIPAA" in agent.regulatory_frameworks
    assert "CCPA" in agent.regulatory_frameworks
    
    print("✅ Agent creation test passed")


async def test_identify_applicable_regulations():
    """Test regulation identification logic."""
    print("Testing regulation identification...")
    
    agent = ComplianceAgent()
    
    # Test healthcare scenario
    healthcare_assessment = MockAssessment(
        business_req={
            "industry": "healthcare",
            "target_markets": ["us"],
            "data_types": ["health_data", "personal_data"]
        }
    )
    
    agent.current_assessment = healthcare_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    
    assert "HIPAA" in applicable_regs["applicable_regulations"]
    assert "healthcare" in str(applicable_regs["applicability_reasons"]["HIPAA"]).lower()
    
    print("✅ Healthcare regulation identification passed")
    
    # Test GDPR scenario
    gdpr_assessment = MockAssessment(
        business_req={
            "industry": "technology",
            "target_markets": ["eu", "uk"],
            "data_types": ["personal_data"]
        }
    )
    
    agent.current_assessment = gdpr_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    
    assert "GDPR" in applicable_regs["applicable_regulations"]
    
    print("✅ GDPR regulation identification passed")


async def test_compliance_assessment():
    """Test compliance posture assessment."""
    print("Testing compliance assessment...")
    
    agent = ComplianceAgent()
    
    # Test with good security requirements
    good_assessment = MockAssessment(
        business_req={"industry": "healthcare", "target_markets": ["us"]},
        technical_req={
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "multi_factor_auth": True,
                "role_based_access": True,
                "access_monitoring": True,
                "audit_logging": True,
                "business_associate_agreements": True
            }
        }
    )
    
    agent.current_assessment = good_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    compliance_assessment = await agent._assess_compliance_posture(applicable_regs)
    
    assert "overall_compliance_score" in compliance_assessment
    assert "regulation_scores" in compliance_assessment
    assert 0.0 <= compliance_assessment["overall_compliance_score"] <= 1.0
    
    # Should have decent score with good security
    assert compliance_assessment["overall_compliance_score"] > 0.5
    
    print("✅ Compliance assessment test passed")


async def test_security_controls_assessment():
    """Test security controls assessment."""
    print("Testing security controls assessment...")
    
    agent = ComplianceAgent()
    
    # Test with comprehensive security
    secure_assessment = MockAssessment(
        technical_req={
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "key_management": True,
                "multi_factor_auth": True,
                "role_based_access": True,
                "access_monitoring": True,
                "centralized_logging": True,
                "security_monitoring": True,
                "audit_trails": True
            }
        }
    )
    
    agent.current_assessment = secure_assessment
    security_assessment = await agent._assess_security_controls()
    
    assert "overall_security_score" in security_assessment
    assert "encryption_status" in security_assessment
    assert "access_control_status" in security_assessment
    
    # Should have good scores with comprehensive security
    assert security_assessment["overall_security_score"] > 0.7
    assert security_assessment["encryption_status"]["score"] > 0.8
    
    print("✅ Security controls assessment test passed")


async def test_data_residency_analysis():
    """Test data residency analysis."""
    print("Testing data residency analysis...")
    
    agent = ComplianceAgent()
    
    # Test GDPR data residency
    gdpr_assessment = MockAssessment(
        business_req={
            "target_markets": ["eu"],
            "preferred_regions": ["us-east-1"]  # Conflict
        }
    )
    
    agent.current_assessment = gdpr_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    data_residency = await agent._analyze_data_residency_requirements(applicable_regs)
    
    assert "residency_requirements" in data_residency
    assert "recommended_regions" in data_residency
    assert "compliance_conflicts" in data_residency
    
    # Should recommend EU regions for GDPR
    recommended_regions = data_residency["recommended_regions"]
    eu_regions = [r for r in recommended_regions if r.startswith("eu-")]
    assert len(eu_regions) > 0
    
    print("✅ Data residency analysis test passed")


async def test_compliance_gap_identification():
    """Test compliance gap identification."""
    print("Testing compliance gap identification...")
    
    agent = ComplianceAgent()
    
    # Test with poor security (should have gaps)
    poor_assessment = MockAssessment(
        business_req={"industry": "healthcare", "target_markets": ["us"]},
        technical_req={
            "security_requirements": {
                "encryption_at_rest": False,
                "encryption_in_transit": False,
                "multi_factor_auth": False,
                "access_monitoring": False
            }
        }
    )
    
    agent.current_assessment = poor_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    compliance_assessment = await agent._assess_compliance_posture(applicable_regs)
    security_assessment = await agent._assess_security_controls()
    
    gaps = await agent._identify_compliance_gaps(
        applicable_regs, compliance_assessment, security_assessment
    )
    
    assert "total_gaps" in gaps
    assert "high_risk_gaps" in gaps
    assert "overall_risk_level" in gaps
    
    # Should identify gaps with poor security
    assert gaps["total_gaps"] > 0
    assert gaps["overall_risk_level"] in ["high", "critical"]
    
    print("✅ Compliance gap identification test passed")


async def test_compliance_recommendations():
    """Test compliance recommendations generation."""
    print("Testing compliance recommendations...")
    
    agent = ComplianceAgent()
    
    healthcare_assessment = MockAssessment(
        business_req={"industry": "healthcare", "target_markets": ["us"]},
        technical_req={
            "security_requirements": {
                "encryption_at_rest": False,  # Gap
                "multi_factor_auth": False    # Gap
            }
        }
    )
    
    agent.current_assessment = healthcare_assessment
    applicable_regs = await agent._identify_applicable_regulations()
    compliance_assessment = await agent._assess_compliance_posture(applicable_regs)
    data_residency = await agent._analyze_data_residency_requirements(applicable_regs)
    security_assessment = await agent._assess_security_controls()
    gaps = await agent._identify_compliance_gaps(
        applicable_regs, compliance_assessment, security_assessment
    )
    
    recommendations = await agent._generate_compliance_recommendations(
        applicable_regs, gaps, data_residency
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    
    # Check recommendation structure
    for rec in recommendations:
        assert "category" in rec
        assert "priority" in rec
        assert "title" in rec
        assert "description" in rec
        assert "actions" in rec
        assert rec["priority"] in ["critical", "high", "medium", "low"]
    
    print("✅ Compliance recommendations test passed")


async def test_compliance_roadmap():
    """Test compliance roadmap creation."""
    print("Testing compliance roadmap...")
    
    agent = ComplianceAgent()
    
    # Sample recommendations
    recommendations = [
        {
            "category": "regulatory_compliance",
            "priority": "critical",
            "title": "Critical Issue",
            "timeline": "Immediate"
        },
        {
            "category": "security_controls",
            "priority": "high",
            "title": "High Priority",
            "timeline": "1-3 months"
        },
        {
            "category": "data_protection",
            "priority": "medium",
            "title": "Medium Priority",
            "timeline": "3-6 months"
        }
    ]
    
    roadmap = await agent._create_compliance_roadmap(recommendations)
    
    assert "phase_1_immediate" in roadmap
    assert "phase_2_foundation" in roadmap
    assert "phase_3_optimization" in roadmap
    assert "ongoing_activities" in roadmap
    
    # Check phase structure
    phase_1 = roadmap["phase_1_immediate"]
    assert "timeline" in phase_1
    assert "focus" in phase_1
    assert "items" in phase_1
    assert "success_criteria" in phase_1
    
    print("✅ Compliance roadmap test passed")


async def test_regulation_prioritization():
    """Test regulation prioritization."""
    print("Testing regulation prioritization...")
    
    agent = ComplianceAgent()
    
    regulations = ["SOC_2", "GDPR", "HIPAA", "CCPA", "ISO_27001"]
    prioritized = agent._prioritize_regulations(regulations)
    
    # HIPAA should come before GDPR, GDPR before CCPA
    hipaa_index = prioritized.index("HIPAA")
    gdpr_index = prioritized.index("GDPR")
    ccpa_index = prioritized.index("CCPA")
    
    assert hipaa_index < gdpr_index
    assert gdpr_index < ccpa_index
    
    print("✅ Regulation prioritization test passed")


async def main():
    """Run all basic compliance tests."""
    print("🚀 Starting Basic Compliance Agent Tests")
    
    try:
        await test_compliance_agent_creation()
        await test_identify_applicable_regulations()
        await test_compliance_assessment()
        await test_security_controls_assessment()
        await test_data_residency_analysis()
        await test_compliance_gap_identification()
        await test_compliance_recommendations()
        await test_compliance_roadmap()
        await test_regulation_prioritization()
        
        print("\n✅ All basic compliance tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())