"""
Tests for Compliance Agent.

Tests the compliance agent's regulatory analysis, security assessment,
and data residency recommendation capabilities.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.infra_mind.agents.compliance_agent import ComplianceAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestComplianceAgent:
    """Test suite for Compliance Agent."""
    
    @pytest.fixture
    def compliance_agent(self):
        """Create a compliance agent for testing."""
        config = AgentConfig(
            name="Test Compliance Agent",
            role=AgentRole.COMPLIANCE,
            tools_enabled=["data_processor", "compliance_checker", "security_analyzer"]
        )
        return ComplianceAgent(config)
    
    @pytest.fixture
    def healthcare_assessment(self):
        """Create a healthcare assessment for testing."""
        # Create a mock assessment object instead of using Beanie
        class MockAssessment:
            def __init__(self):
                self.user_id = "test_user"
                self.title = "Healthcare Compliance Test"
                self.business_requirements = {
                    "company_size": "medium",
                    "industry": "healthcare",
                    "company_location": "united_states",
                    "target_markets": ["us"],
                    "data_types": ["health_data", "personal_data"],
                    "budget_range": "$100k+",
                    "primary_goals": ["compliance", "security"]
                }
                self.technical_requirements = {
                    "workload_types": ["web_application", "database"],
                    "expected_users": 1000,
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
                self.id = "test_assessment_id"
            
            def dict(self):
                return {
                    "user_id": self.user_id,
                    "title": self.title,
                    "business_requirements": self.business_requirements,
                    "technical_requirements": self.technical_requirements
                }
        
        return MockAssessment()
    
    @pytest.fixture
    def gdpr_assessment(self):
        """Create a GDPR assessment for testing."""
        class MockAssessment:
            def __init__(self):
                self.user_id = "test_user"
                self.title = "GDPR Compliance Test"
                self.business_requirements = {
                    "company_size": "small",
                    "industry": "technology",
                    "company_location": "germany",
                    "target_markets": ["eu", "uk"],
                    "data_types": ["personal_data", "user_data"],
                    "budget_range": "$50k-100k"
                }
                self.technical_requirements = {
                    "workload_types": ["web_application"],
                    "expected_users": 5000,
                    "security_requirements": {
                        "encryption_at_rest": True,
                        "encryption_in_transit": True,
                        "data_retention_policy": True,
                        "consent_management": True,
                        "data_subject_rights": True,
                        "breach_notification": True
                    }
                }
                self.id = "test_assessment_id"
            
            def dict(self):
                return {
                    "user_id": self.user_id,
                    "title": self.title,
                    "business_requirements": self.business_requirements,
                    "technical_requirements": self.technical_requirements
                }
        
        return MockAssessment()
    
    def test_agent_initialization(self, compliance_agent):
        """Test compliance agent initialization."""
        assert compliance_agent.name == "Test Compliance Agent"
        assert compliance_agent.role == AgentRole.COMPLIANCE
        assert compliance_agent.status == AgentStatus.IDLE
        
        # Check compliance-specific attributes
        assert "GDPR" in compliance_agent.regulatory_frameworks
        assert "HIPAA" in compliance_agent.regulatory_frameworks
        assert "CCPA" in compliance_agent.regulatory_frameworks
        
        # Check security controls knowledge
        assert "encryption" in compliance_agent.security_controls
        assert "access_control" in compliance_agent.security_controls
        assert "data_protection" in compliance_agent.security_controls
    
    @pytest.mark.asyncio
    async def test_identify_applicable_regulations_healthcare(self, compliance_agent, healthcare_assessment):
        """Test identification of applicable regulations for healthcare."""
        await compliance_agent.initialize(healthcare_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        
        assert "HIPAA" in applicable_regs["applicable_regulations"]
        assert "healthcare" in applicable_regs["applicability_reasons"]["HIPAA"][0].lower()
        assert len(applicable_regs["regulation_details"]) > 0
        
        # Check HIPAA details
        hipaa_details = applicable_regs["regulation_details"]["HIPAA"]
        assert hipaa_details["jurisdiction"] == "United States"
        assert "Administrative safeguards" in hipaa_details["key_requirements"]
    
    @pytest.mark.asyncio
    async def test_identify_applicable_regulations_gdpr(self, compliance_agent, gdpr_assessment):
        """Test identification of applicable regulations for GDPR."""
        await compliance_agent.initialize(gdpr_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        
        assert "GDPR" in applicable_regs["applicable_regulations"]
        assert len(applicable_regs["applicability_reasons"]["GDPR"]) > 0
        
        # Check GDPR details
        gdpr_details = applicable_regs["regulation_details"]["GDPR"]
        assert gdpr_details["jurisdiction"] == "European Union"
        assert "Data minimization" in gdpr_details["key_requirements"]
    
    @pytest.mark.asyncio
    async def test_assess_compliance_posture(self, compliance_agent, healthcare_assessment):
        """Test compliance posture assessment."""
        await compliance_agent.initialize(healthcare_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        compliance_assessment = await compliance_agent._assess_compliance_posture(applicable_regs)
        
        assert "overall_compliance_score" in compliance_assessment
        assert "regulation_scores" in compliance_assessment
        assert "compliance_status" in compliance_assessment
        assert "maturity_level" in compliance_assessment
        
        # Check score is reasonable
        assert 0.0 <= compliance_assessment["overall_compliance_score"] <= 1.0
        
        # Check HIPAA score (should be good due to comprehensive security requirements)
        if "HIPAA" in compliance_assessment["regulation_scores"]:
            hipaa_score = compliance_assessment["regulation_scores"]["HIPAA"]
            assert hipaa_score > 0.5  # Should be decent with good security requirements
    
    @pytest.mark.asyncio
    async def test_analyze_data_residency_requirements(self, compliance_agent, gdpr_assessment):
        """Test data residency analysis."""
        await compliance_agent.initialize(gdpr_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        data_residency = await compliance_agent._analyze_data_residency_requirements(applicable_regs)
        
        assert "residency_requirements" in data_residency
        assert "recommended_regions" in data_residency
        assert "data_sovereignty_restrictions" in data_residency
        
        # Check GDPR residency requirements
        if "GDPR" in data_residency["residency_requirements"]:
            gdpr_residency = data_residency["residency_requirements"]["GDPR"]
            assert "EU" in gdpr_residency or "adequate" in gdpr_residency
        
        # Check recommended regions include EU regions
        recommended_regions = data_residency["recommended_regions"]
        eu_regions = [r for r in recommended_regions if r.startswith("eu-")]
        assert len(eu_regions) > 0
    
    @pytest.mark.asyncio
    async def test_assess_security_controls(self, compliance_agent, healthcare_assessment):
        """Test security controls assessment."""
        await compliance_agent.initialize(healthcare_assessment)
        
        security_assessment = await compliance_agent._assess_security_controls()
        
        assert "overall_security_score" in security_assessment
        assert "encryption_status" in security_assessment
        assert "access_control_status" in security_assessment
        assert "data_protection_status" in security_assessment
        assert "monitoring_status" in security_assessment
        
        # Check encryption status (should be good)
        encryption_status = security_assessment["encryption_status"]
        assert encryption_status["score"] > 0.5  # Good encryption setup
        
        # Check access control status
        access_status = security_assessment["access_control_status"]
        assert access_status["score"] > 0.5  # Good access controls
    
    @pytest.mark.asyncio
    async def test_identify_compliance_gaps(self, compliance_agent):
        """Test compliance gap identification."""
        # Create assessment with poor security
        class MockPoorAssessment:
            def __init__(self):
                self.user_id = "test_user"
                self.title = "Poor Security Test"
                self.business_requirements = {
                    "industry": "healthcare",
                    "target_markets": ["us"]
                }
                self.technical_requirements = {
                    "security_requirements": {
                        "encryption_at_rest": False,
                        "encryption_in_transit": False,
                        "multi_factor_auth": False,
                        "access_monitoring": False
                    }
                }
                self.id = "test_assessment_id"
            
            def dict(self):
                return {
                    "user_id": self.user_id,
                    "title": self.title,
                    "business_requirements": self.business_requirements,
                    "technical_requirements": self.technical_requirements
                }
        
        poor_assessment = MockPoorAssessment()
        
        await compliance_agent.initialize(poor_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        compliance_assessment = await compliance_agent._assess_compliance_posture(applicable_regs)
        security_assessment = await compliance_agent._assess_security_controls()
        
        gaps = await compliance_agent._identify_compliance_gaps(
            applicable_regs, compliance_assessment, security_assessment
        )
        
        assert "total_gaps" in gaps
        assert "high_risk_gaps" in gaps
        assert "overall_risk_level" in gaps
        
        # Should have gaps due to poor security
        assert gaps["total_gaps"] > 0
        assert len(gaps["high_risk_gaps"]) > 0
        assert gaps["overall_risk_level"] in ["high", "critical"]
    
    @pytest.mark.asyncio
    async def test_generate_compliance_recommendations(self, compliance_agent, healthcare_assessment):
        """Test compliance recommendations generation."""
        await compliance_agent.initialize(healthcare_assessment)
        
        applicable_regs = await compliance_agent._identify_applicable_regulations()
        compliance_assessment = await compliance_agent._assess_compliance_posture(applicable_regs)
        data_residency = await compliance_agent._analyze_data_residency_requirements(applicable_regs)
        security_assessment = await compliance_agent._assess_security_controls()
        gaps = await compliance_agent._identify_compliance_gaps(
            applicable_regs, compliance_assessment, security_assessment
        )
        
        recommendations = await compliance_agent._generate_compliance_recommendations(
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
            assert "business_impact" in rec
            assert "timeline" in rec
            
            # Check priority is valid
            assert rec["priority"] in ["critical", "high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_create_compliance_roadmap(self, compliance_agent, healthcare_assessment):
        """Test compliance roadmap creation."""
        await compliance_agent.initialize(healthcare_assessment)
        
        # Create sample recommendations
        recommendations = [
            {
                "category": "regulatory_compliance",
                "priority": "critical",
                "title": "Critical Compliance Issue",
                "timeline": "Immediate"
            },
            {
                "category": "security_controls",
                "priority": "high",
                "title": "High Priority Security",
                "timeline": "1-3 months"
            },
            {
                "category": "data_protection",
                "priority": "medium",
                "title": "Medium Priority Protection",
                "timeline": "3-6 months"
            }
        ]
        
        roadmap = await compliance_agent._create_compliance_roadmap(recommendations)
        
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
        
        # Critical items should be in phase 1
        phase_1_titles = [item["title"] for item in phase_1["items"]]
        assert "Critical Compliance Issue" in phase_1_titles
    
    @pytest.mark.asyncio
    async def test_full_compliance_analysis(self, compliance_agent, healthcare_assessment):
        """Test full compliance analysis workflow."""
        result = await compliance_agent.execute(healthcare_assessment)
        
        assert result.status == AgentStatus.COMPLETED
        assert result.agent_name == compliance_agent.name
        assert len(result.recommendations) > 0
        
        # Check result data structure
        assert "applicable_regulations" in result.data
        assert "compliance_assessment" in result.data
        assert "data_residency_analysis" in result.data
        assert "security_controls_assessment" in result.data
        assert "compliance_gaps" in result.data
        assert "compliance_roadmap" in result.data
        
        # Check recommendations have proper structure
        for rec in result.recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec
    
    @pytest.mark.asyncio
    async def test_regulation_prioritization(self, compliance_agent):
        """Test regulation prioritization logic."""
        regulations = ["SOC_2", "GDPR", "HIPAA", "CCPA", "ISO_27001"]
        prioritized = compliance_agent._prioritize_regulations(regulations)
        
        # HIPAA should come before GDPR, GDPR before CCPA
        hipaa_index = prioritized.index("HIPAA")
        gdpr_index = prioritized.index("GDPR")
        ccpa_index = prioritized.index("CCPA")
        
        assert hipaa_index < gdpr_index
        assert gdpr_index < ccpa_index
    
    @pytest.mark.asyncio
    async def test_evaluate_regulation_compliance(self, compliance_agent):
        """Test individual regulation compliance evaluation."""
        # Test GDPR evaluation
        technical_req = {
            "security_requirements": {
                "encryption_at_rest": True,
                "access_controls": True,
                "audit_logging": True
            }
        }
        
        score, status = await compliance_agent._evaluate_regulation_compliance("GDPR", technical_req)
        
        assert 0.0 <= score <= 1.0
        assert status in ["compliant", "mostly_compliant", "partial", "non_compliant"]
        
        # With good security requirements, should have decent score
        assert score > 0.5
    
    @pytest.mark.asyncio
    async def test_compliance_maturity_determination(self, compliance_agent):
        """Test compliance maturity level determination."""
        assert compliance_agent._determine_compliance_maturity(0.95) == "optimized"
        assert compliance_agent._determine_compliance_maturity(0.75) == "managed"
        assert compliance_agent._determine_compliance_maturity(0.55) == "defined"
        assert compliance_agent._determine_compliance_maturity(0.35) == "repeatable"
        assert compliance_agent._determine_compliance_maturity(0.15) == "initial"
    
    @pytest.mark.asyncio
    async def test_cross_border_transfer_analysis(self, compliance_agent):
        """Test cross-border data transfer analysis."""
        applicable_regs = {
            "applicable_regulations": ["GDPR", "HIPAA"]
        }
        
        considerations = compliance_agent._analyze_cross_border_transfers(applicable_regs)
        
        assert isinstance(considerations, list)
        assert len(considerations) > 0
        
        # Should include GDPR-specific considerations
        gdpr_considerations = [c for c in considerations if "GDPR" in c or "SCC" in c or "adequacy" in c]
        assert len(gdpr_considerations) > 0
        
        # Should include HIPAA-specific considerations
        hipaa_considerations = [c for c in considerations if "HIPAA" in c or "Business Associate" in c]
        assert len(hipaa_considerations) > 0
    
    @pytest.mark.asyncio
    async def test_security_control_assessment_methods(self, compliance_agent):
        """Test individual security control assessment methods."""
        # Test encryption assessment
        good_encryption = {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "key_management": True
        }
        
        encryption_result = compliance_agent._assess_encryption_controls(good_encryption)
        assert encryption_result["score"] == 1.0
        assert "Encryption at rest configured" in encryption_result["status"]
        
        # Test poor encryption
        poor_encryption = {
            "encryption_at_rest": False,
            "encryption_in_transit": False,
            "key_management": False
        }
        
        poor_result = compliance_agent._assess_encryption_controls(poor_encryption)
        assert poor_result["score"] == 0.0
        assert "Missing encryption at rest" in poor_result["status"]
    
    @pytest.mark.asyncio
    async def test_overall_risk_calculation(self, compliance_agent):
        """Test overall risk level calculation."""
        # High risk scenario
        high_risk_gaps = [{"severity": "high"}, {"severity": "high"}, {"severity": "high"}]
        medium_risk_gaps = []
        
        risk_level = compliance_agent._calculate_overall_risk_level(high_risk_gaps, medium_risk_gaps)
        assert risk_level == "critical"
        
        # Medium risk scenario
        high_risk_gaps = [{"severity": "high"}]
        medium_risk_gaps = []
        
        risk_level = compliance_agent._calculate_overall_risk_level(high_risk_gaps, medium_risk_gaps)
        assert risk_level == "high"
        
        # Low risk scenario
        high_risk_gaps = []
        medium_risk_gaps = [{"severity": "medium"}]
        
        risk_level = compliance_agent._calculate_overall_risk_level(high_risk_gaps, medium_risk_gaps)
        assert risk_level == "low"
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, compliance_agent):
        """Test agent error handling."""
        # Create invalid assessment
        class MockInvalidAssessment:
            def __init__(self):
                self.user_id = "test_user"
                self.title = "Invalid Test"
                self.business_requirements = {}
                self.technical_requirements = {}
                self.id = "test_assessment_id"
            
            def dict(self):
                return {
                    "user_id": self.user_id,
                    "title": self.title,
                    "business_requirements": self.business_requirements,
                    "technical_requirements": self.technical_requirements
                }
        
        invalid_assessment = MockInvalidAssessment()
        
        # Should handle gracefully and not crash
        result = await compliance_agent.execute(invalid_assessment)
        
        # Should complete even with minimal data
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
        
        if result.status == AgentStatus.COMPLETED:
            # Should still provide some recommendations
            assert len(result.recommendations) > 0
        else:
            # Should have error information
            assert result.error is not None


@pytest.mark.asyncio
async def test_compliance_agent_integration():
    """Integration test for compliance agent with other system components."""
    # This would test integration with the broader system
    # For now, just ensure the agent can be created and used
    
    config = AgentConfig(
        name="Integration Test Agent",
        role=AgentRole.COMPLIANCE
    )
    
    agent = ComplianceAgent(config)
    
    # Test health check
    health = await agent.health_check()
    assert health["agent_name"] == "Integration Test Agent"
    assert health["role"] == "compliance"
    assert health["status"] == "idle"
    
    # Test capabilities
    capabilities = agent.get_capabilities()
    assert len(capabilities) > 0
    assert any("compliance" in cap.lower() for cap in capabilities)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])