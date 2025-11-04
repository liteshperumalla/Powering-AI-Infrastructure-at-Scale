"""
Compliance Agent for Infra Mind.

Provides regulatory expertise for GDPR, HIPAA, CCPA compliance,
security best practices, and data residency recommendations.
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from .web_search import WebSearchClient, get_web_search_client
from ..models.assessment import Assessment
from ..llm.prompt_sanitizer import PromptSanitizer
from ..llm.manager import LLMManager

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """
    Compliance Agent for regulatory expertise and security guidance.
    
    This agent focuses on:
    - GDPR, HIPAA, CCPA regulatory compliance
    - Security best practices and recommendations
    - Data residency and sovereignty requirements
    - Compliance framework mapping
    - Risk assessment and mitigation strategies
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Compliance Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="Compliance Agent",
                role=AgentRole.COMPLIANCE,
                tools_enabled=["data_processor", "compliance_checker", "security_analyzer"],
                temperature=0.1,  # Lower temperature for consistent compliance advice
                max_tokens=2500,
                custom_config={
                    "supported_regulations": [
                        "GDPR",
                        "HIPAA", 
                        "CCPA",
                        "SOX",
                        "PCI_DSS",
                        "ISO_27001",
                        "SOC_2"
                    ],
                    "security_frameworks": [
                        "NIST_Cybersecurity_Framework",
                        "CIS_Controls",
                        "OWASP_Top_10",
                        "Cloud_Security_Alliance"
                    ],
                    "data_residency_regions": [
                        "US",
                        "EU",
                        "UK", 
                        "Canada",
                        "Australia",
                        "Japan"
                    ]
                }
            )
        
        super().__init__(config)
        

        # Initialize prompt sanitizer for security
        self.prompt_sanitizer = PromptSanitizer(security_level="balanced")
        # Compliance-specific knowledge base
        self.regulatory_frameworks = {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "jurisdiction": "European Union",
                "key_requirements": [
                    "Data minimization",
                    "Purpose limitation", 
                    "Storage limitation",
                    "Data subject rights",
                    "Privacy by design",
                    "Data breach notification"
                ],
                "data_residency": "EU/EEA or adequate countries",
                "penalties": "Up to 4% of annual revenue or €20M"
            },
            "HIPAA": {
                "name": "Health Insurance Portability and Accountability Act",
                "jurisdiction": "United States",
                "key_requirements": [
                    "Administrative safeguards",
                    "Physical safeguards",
                    "Technical safeguards",
                    "Business associate agreements",
                    "Risk assessments",
                    "Audit controls"
                ],
                "data_residency": "US preferred, strict controls for international",
                "penalties": "Up to $1.5M per incident"
            },
            "CCPA": {
                "name": "California Consumer Privacy Act",
                "jurisdiction": "California, United States",
                "key_requirements": [
                    "Right to know",
                    "Right to delete",
                    "Right to opt-out",
                    "Non-discrimination",
                    "Data inventory",
                    "Privacy policy updates"
                ],
                "data_residency": "No specific requirements",
                "penalties": "Up to $7,500 per violation"
            }
        }
        
        self.security_controls = {
            "encryption": {
                "at_rest": ["AES-256", "RSA-2048"],
                "in_transit": ["TLS 1.3", "IPSec"],
                "key_management": ["HSM", "Key rotation", "Separation of duties"]
            },
            "access_control": {
                "authentication": ["Multi-factor authentication", "Strong passwords"],
                "authorization": ["Role-based access", "Principle of least privilege"],
                "monitoring": ["Access logging", "Anomaly detection"]
            },
            "data_protection": {
                "backup": ["Regular backups", "Backup encryption", "Recovery testing"],
                "retention": ["Data retention policies", "Secure deletion"],
                "classification": ["Data classification", "Handling procedures"]
            }
        }
        
        # Initialize web search for real-time regulatory updates
        self.web_search_client = None
        self.llm_client = None
        
        logger.info("Compliance Agent initialized with regulatory expertise")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute Compliance agent's main regulatory analysis logic.
        
        Returns:
            Dictionary with compliance recommendations and analysis
        """
        logger.info("Compliance Agent starting regulatory analysis")
        
        try:
            # Initialize clients for real data collection
            if not self.web_search_client:
                self.web_search_client = await get_web_search_client()
            if not self.llm_client:
                self.llm_client = LLMManager()
            
            # Step 1: Collect real-time regulatory updates
            regulatory_updates = await self._collect_regulatory_updates()
            
            # Step 2: Identify applicable regulations with real data
            applicable_regulations = await self._identify_applicable_regulations_with_research(regulatory_updates)
            
            # Step 3: Assess current compliance posture with real data
            compliance_assessment = await self._assess_compliance_posture_with_real_data(applicable_regulations)
            
            # Step 4: Analyze data residency requirements with current regulations
            data_residency_analysis = await self._analyze_data_residency_requirements(applicable_regulations)
            
            # Step 5: Evaluate security controls with real benchmarks
            security_controls_assessment = await self._assess_security_controls_with_benchmarks()
            
            # Step 6: Identify compliance gaps using real compliance data
            compliance_gaps = await self._identify_compliance_gaps_with_real_data(
                applicable_regulations, compliance_assessment, security_controls_assessment, regulatory_updates
            )
            
            # Step 7: Generate compliance recommendations with real market data
            compliance_recommendations = await self._generate_compliance_recommendations_with_research(
                applicable_regulations, compliance_gaps, data_residency_analysis, regulatory_updates
            )
            
            # Step 8: Create compliance roadmap with real-world timelines
            compliance_roadmap = await self._create_compliance_roadmap_with_real_data(compliance_recommendations)
            
            result = {
                "recommendations": compliance_recommendations,
                "data": {
                    "regulatory_updates": regulatory_updates,
                    "applicable_regulations": applicable_regulations,
                    "compliance_assessment": compliance_assessment,
                    "data_residency_analysis": data_residency_analysis,
                    "security_controls_assessment": security_controls_assessment,
                    "compliance_gaps": compliance_gaps,
                    "compliance_roadmap": compliance_roadmap,
                    "regulatory_frameworks": self.regulatory_frameworks,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("Compliance Agent completed regulatory analysis successfully")
            return result
            
        except Exception as e:
            logger.error(f"Compliance Agent analysis failed: {str(e)}")
            raise
    
    async def _identify_applicable_regulations(self) -> Dict[str, Any]:
        """Identify which regulations apply to the organization."""
        logger.debug("Identifying applicable regulations")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        
        applicable_regs = []
        regulation_reasons = {}
        
        # Analyze business context to determine applicable regulations
        industry = business_req.get("industry").lower()
        company_location = business_req.get("company_location").lower()
        data_types = business_req.get("data_types", [])
        target_markets = business_req.get("target_markets", [])
        
        # GDPR applicability
        if (any(market in ["eu", "europe", "european_union"] for market in target_markets) or
            "eu" in company_location or "europe" in company_location or
            any("personal" in str(data_type).lower() for data_type in data_types)):
            applicable_regs.append("GDPR")
            regulation_reasons["GDPR"] = [
                "Processing personal data of EU residents",
                "Company operates in EU market",
                "Data subjects in EU/EEA"
            ]
        
        # HIPAA applicability
        if (industry in ["healthcare", "medical", "health"] or
            any("health" in str(data_type).lower() or "medical" in str(data_type).lower() 
                for data_type in data_types)):
            applicable_regs.append("HIPAA")
            regulation_reasons["HIPAA"] = [
                "Healthcare industry operations",
                "Processing protected health information (PHI)",
                "Healthcare service provider"
            ]
        
        # CCPA applicability
        if (any(market in ["california", "ca", "us", "united_states"] for market in target_markets) or
            "california" in company_location or "ca" in company_location):
            applicable_regs.append("CCPA")
            regulation_reasons["CCPA"] = [
                "California residents as customers",
                "Company operates in California",
                "Processing California consumer data"
            ]
        
        # Default regulations for general business
        if not applicable_regs:
            applicable_regs.extend(["GDPR", "SOC_2"])  # Common baseline
            regulation_reasons["GDPR"] = ["Best practice for data protection"]
            regulation_reasons["SOC_2"] = ["Industry standard for service organizations"]
        
        return {
            "applicable_regulations": applicable_regs,
            "regulation_details": {
                reg: self.regulatory_frameworks.get(reg, {})
                for reg in applicable_regs if reg in self.regulatory_frameworks
            },
            "applicability_reasons": regulation_reasons,
            "compliance_priority": self._prioritize_regulations(applicable_regs)
        }
    
    async def _assess_compliance_posture(self, applicable_regulations: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current compliance posture against applicable regulations."""
        logger.debug("Assessing compliance posture")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Use data processing tool to analyze current state
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        compliance_scores = {}
        compliance_status = {}
        
        for regulation in applicable_regulations.get("applicable_regulations", []):
            score, status = await self._evaluate_regulation_compliance(regulation, technical_req)
            compliance_scores[regulation] = score
            compliance_status[regulation] = status
        
        overall_score = sum(compliance_scores.values()) / len(compliance_scores) if compliance_scores else 0.0
        
        return {
            "overall_compliance_score": round(overall_score, 2),
            "regulation_scores": compliance_scores,
            "compliance_status": compliance_status,
            "maturity_level": self._determine_compliance_maturity(overall_score),
            "assessment_summary": analysis_result.data if analysis_result.is_success else {}
        }
    
    async def _analyze_data_residency_requirements(self, applicable_regulations: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data residency and sovereignty requirements."""
        logger.debug("Analyzing data residency requirements")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        
        residency_requirements = {}
        recommended_regions = []
        restrictions = []
        
        for regulation in applicable_regulations.get("applicable_regulations", []):
            if regulation in self.regulatory_frameworks:
                framework = self.regulatory_frameworks[regulation]
                residency_req = framework.get("data_residency")
                
                residency_requirements[regulation] = residency_req
                
                if regulation == "GDPR":
                    recommended_regions.extend(["eu-west-1", "eu-central-1", "eu-north-1"])
                    restrictions.append("Data must remain in EU/EEA or adequate countries")
                elif regulation == "HIPAA":
                    recommended_regions.extend(["us-east-1", "us-west-2"])
                    restrictions.append("PHI should remain in US with strict international controls")
                elif regulation == "CCPA":
                    recommended_regions.extend(["us-west-1", "us-west-2"])
        
        # Remove duplicates
        recommended_regions = list(set(recommended_regions))
        
        # Analyze current infrastructure location
        current_regions = business_req.get("preferred_regions", [])
        compliance_conflicts = []
        
        for region in current_regions:
            if region.startswith("us-") and "GDPR" in applicable_regulations.get("applicable_regulations", []):
                compliance_conflicts.append(f"US region {region} may conflict with GDPR requirements")
            elif region.startswith("eu-") and "HIPAA" in applicable_regulations.get("applicable_regulations", []):
                compliance_conflicts.append(f"EU region {region} may require additional controls for HIPAA")
        
        return {
            "residency_requirements": residency_requirements,
            "recommended_regions": recommended_regions,
            "current_regions": current_regions,
            "compliance_conflicts": compliance_conflicts,
            "data_sovereignty_restrictions": restrictions,
            "cross_border_considerations": self._analyze_cross_border_transfers(applicable_regulations)
        }
    
    async def _assess_security_controls(self) -> Dict[str, Any]:
        """Assess security controls and best practices."""
        logger.debug("Assessing security controls")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Analyze current security posture
        current_security = technical_req.get("security_requirements", {})
        
        security_assessment = {
            "encryption_status": self._assess_encryption_controls(current_security),
            "access_control_status": self._assess_access_controls(current_security),
            "data_protection_status": self._assess_data_protection(current_security),
            "monitoring_status": self._assess_monitoring_controls(current_security),
            "overall_security_score": 0.0
        }
        
        # Calculate overall security score
        scores = []
        for category, status in security_assessment.items():
            if isinstance(status, dict) and "score" in status:
                scores.append(status["score"])
        
        security_assessment["overall_security_score"] = sum(scores) / len(scores) if scores else 0.0
        
        return security_assessment
    
    async def _identify_compliance_gaps(self, applicable_regulations: Dict[str, Any],
                                      compliance_assessment: Dict[str, Any],
                                      security_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Identify compliance gaps and risks."""
        logger.debug("Identifying compliance gaps")
        
        gaps = []
        high_risk_gaps = []
        medium_risk_gaps = []
        low_risk_gaps = []
        
        # Analyze regulation-specific gaps
        for regulation in applicable_regulations.get("applicable_regulations", []):
            reg_score = compliance_assessment.get("regulation_scores", {}).get(regulation, 0.0)
            
            if reg_score < 0.7:  # Below acceptable threshold
                gap = {
                    "regulation": regulation,
                    "current_score": reg_score,
                    "gap_severity": "high" if reg_score < 0.4 else "medium",
                    "required_improvements": self._get_regulation_requirements(regulation),
                    "potential_penalties": self.regulatory_frameworks.get(regulation, {}).get("penalties")
                }
                gaps.append(gap)
                
                if gap["gap_severity"] == "high":
                    high_risk_gaps.append(gap)
                else:
                    medium_risk_gaps.append(gap)
        
        # Analyze security control gaps
        security_score = security_assessment.get("overall_security_score", 0.0)
        if security_score < 0.8:
            security_gap = {
                "category": "security_controls",
                "current_score": security_score,
                "gap_severity": "high" if security_score < 0.5 else "medium",
                "required_improvements": self._get_security_improvements(security_assessment)
            }
            gaps.append(security_gap)
            
            if security_gap["gap_severity"] == "high":
                high_risk_gaps.append(security_gap)
            else:
                medium_risk_gaps.append(security_gap)
        
        return {
            "total_gaps": len(gaps),
            "high_risk_gaps": high_risk_gaps,
            "medium_risk_gaps": medium_risk_gaps,
            "low_risk_gaps": low_risk_gaps,
            "gap_summary": gaps,
            "overall_risk_level": self._calculate_overall_risk_level(high_risk_gaps, medium_risk_gaps)
        }
    
    async def _generate_compliance_recommendations(self, applicable_regulations: Dict[str, Any],
                                                 compliance_gaps: Dict[str, Any],
                                                 data_residency_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate compliance recommendations."""
        logger.debug("Generating compliance recommendations")
        
        recommendations = []
        
        # High-priority gap recommendations
        for gap in compliance_gaps.get("high_risk_gaps", []):
            if gap.get("regulation"):
                recommendations.append({
                    "category": "regulatory_compliance",
                    "priority": "critical",
                    "title": f"Address {gap['regulation']} Compliance Gaps",
                    "description": f"Critical compliance gaps identified for {gap['regulation']} regulation",
                    "rationale": f"Current compliance score of {gap['current_score']:.1f} is below acceptable threshold",
                    "actions": gap.get("required_improvements", []),
                    "business_impact": f"Avoid potential penalties: {gap.get('potential_penalties', 'Significant fines')}",
                    "timeline": "Immediate - 3 months",
                    "investment_required": "High (compliance infrastructure and processes)"
                })
        
        # Data residency recommendations
        if data_residency_analysis.get("compliance_conflicts"):
            recommendations.append({
                "category": "data_residency",
                "priority": "high",
                "title": "Resolve Data Residency Conflicts",
                "description": "Current infrastructure regions conflict with regulatory requirements",
                "rationale": "Data residency violations can result in significant penalties",
                "actions": [
                    f"Migrate to compliant regions: {', '.join(data_residency_analysis.get('recommended_regions', []))}",
                    "Implement data localization controls",
                    "Review cross-border data transfer mechanisms"
                ],
                "business_impact": "Ensures regulatory compliance and reduces legal risk",
                "timeline": "3-6 months",
                "investment_required": "Medium to High (migration and infrastructure)"
            })
        
        # Security controls recommendations
        for gap in compliance_gaps.get("high_risk_gaps", []):
            if gap.get("category") == "security_controls":
                recommendations.append({
                    "category": "security_controls",
                    "priority": "high",
                    "title": "Strengthen Security Controls",
                    "description": "Security controls below compliance requirements",
                    "rationale": f"Security score of {gap['current_score']:.1f} indicates significant vulnerabilities",
                    "actions": gap.get("required_improvements", []),
                    "business_impact": "Reduces security risk and ensures compliance",
                    "timeline": "2-4 months",
                    "investment_required": "Medium (security tools and processes)"
                })
        
        # Encryption recommendations
        recommendations.append({
            "category": "data_protection",
            "priority": "high",
            "title": "Implement Comprehensive Encryption",
            "description": "Ensure data is encrypted at rest and in transit",
            "rationale": "Encryption is fundamental requirement for most regulations",
            "actions": [
                "Implement AES-256 encryption for data at rest",
                "Use TLS 1.3 for data in transit",
                "Implement proper key management with HSM",
                "Regular key rotation policies"
            ],
            "business_impact": "Meets regulatory requirements and protects sensitive data",
            "timeline": "1-3 months",
            "investment_required": "Medium (encryption infrastructure)"
        })
        
        # Access control recommendations
        recommendations.append({
            "category": "access_control",
            "priority": "medium",
            "title": "Implement Strong Access Controls",
            "description": "Establish robust authentication and authorization mechanisms",
            "rationale": "Access controls are critical for compliance and security",
            "actions": [
                "Implement multi-factor authentication (MFA)",
                "Establish role-based access control (RBAC)",
                "Apply principle of least privilege",
                "Regular access reviews and audits"
            ],
            "business_impact": "Reduces unauthorized access risk and meets compliance requirements",
            "timeline": "2-4 months",
            "investment_required": "Medium (identity management systems)"
        })
        
        # Monitoring and auditing recommendations
        recommendations.append({
            "category": "monitoring_auditing",
            "priority": "medium",
            "title": "Establish Comprehensive Monitoring",
            "description": "Implement logging, monitoring, and audit capabilities",
            "rationale": "Audit trails are required for most compliance frameworks",
            "actions": [
                "Implement centralized logging",
                "Set up security monitoring and alerting",
                "Establish audit trail capabilities",
                "Regular compliance assessments"
            ],
            "business_impact": "Enables compliance reporting and incident response",
            "timeline": "2-3 months",
            "investment_required": "Medium (monitoring and SIEM tools)"
        })
        
        return recommendations
    
    async def _create_compliance_roadmap(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create compliance implementation roadmap."""
        logger.debug("Creating compliance roadmap")
        
        # Organize recommendations by priority and timeline
        critical_items = [r for r in recommendations if r.get("priority") == "critical"]
        high_priority_items = [r for r in recommendations if r.get("priority") == "high"]
        medium_priority_items = [r for r in recommendations if r.get("priority") == "medium"]
        
        roadmap = {
            "phase_1_immediate": {
                "timeline": "0-3 months",
                "focus": "Critical compliance gaps and high-risk items",
                "items": critical_items + high_priority_items[:2],
                "success_criteria": [
                    "Critical compliance gaps addressed",
                    "High-risk vulnerabilities mitigated",
                    "Basic security controls implemented"
                ]
            },
            "phase_2_foundation": {
                "timeline": "3-6 months", 
                "focus": "Core security and compliance infrastructure",
                "items": high_priority_items[2:] + medium_priority_items[:2],
                "success_criteria": [
                    "Comprehensive encryption implemented",
                    "Access controls established",
                    "Data residency compliance achieved"
                ]
            },
            "phase_3_optimization": {
                "timeline": "6-12 months",
                "focus": "Advanced controls and continuous improvement",
                "items": medium_priority_items[2:],
                "success_criteria": [
                    "Advanced monitoring implemented",
                    "Compliance automation established",
                    "Regular audit processes in place"
                ]
            },
            "ongoing_activities": [
                "Regular compliance assessments",
                "Security monitoring and incident response",
                "Policy updates and training",
                "Vendor security assessments"
            ]
        }
        
        return roadmap
    
    # Helper methods
    
    def _prioritize_regulations(self, regulations: List[str]) -> List[str]:
        """Prioritize regulations by risk and impact."""
        priority_order = ["HIPAA", "GDPR", "CCPA", "SOX", "PCI_DSS", "ISO_27001", "SOC_2"]
        return sorted(regulations, key=lambda x: priority_order.index(x) if x in priority_order else 999)
    
    async def _evaluate_regulation_compliance(self, regulation: str, technical_req: Dict[str, Any]) -> tuple[float, str]:
        """Evaluate compliance with a specific regulation."""
        score = 0.5  # Default baseline score
        status = "partial"
        
        # Simple scoring logic based on technical requirements
        security_req = technical_req.get("security_requirements", {})
        
        if regulation == "GDPR":
            if security_req.get("encryption_at_rest"):
                score += 0.2
            if security_req.get("access_controls"):
                score += 0.2
            if security_req.get("audit_logging"):
                score += 0.1
        elif regulation == "HIPAA":
            if security_req.get("encryption_at_rest") and security_req.get("encryption_in_transit"):
                score += 0.3
            if security_req.get("access_controls"):
                score += 0.2
        elif regulation == "CCPA":
            if security_req.get("data_inventory"):
                score += 0.2
            if security_req.get("privacy_controls"):
                score += 0.3
        
        # Determine status
        if score >= 0.8:
            status = "compliant"
        elif score >= 0.6:
            status = "mostly_compliant"
        elif score >= 0.4:
            status = "partial"
        else:
            status = "non_compliant"
        
        return min(score, 1.0), status
    
    def _determine_compliance_maturity(self, score: float) -> str:
        """Determine compliance maturity level."""
        if score >= 0.9:
            return "optimized"
        elif score >= 0.7:
            return "managed"
        elif score >= 0.5:
            return "defined"
        elif score >= 0.3:
            return "repeatable"
        else:
            return "initial"
    
    def _analyze_cross_border_transfers(self, applicable_regulations: Dict[str, Any]) -> List[str]:
        """Analyze cross-border data transfer considerations."""
        considerations = []
        
        regulations = applicable_regulations.get("applicable_regulations", [])
        
        if "GDPR" in regulations:
            considerations.extend([
                "Standard Contractual Clauses (SCCs) required for non-EU transfers",
                "Adequacy decisions for approved countries",
                "Binding Corporate Rules (BCRs) for multinational organizations"
            ])
        
        if "HIPAA" in regulations:
            considerations.extend([
                "Business Associate Agreements required for third parties",
                "Additional safeguards for international PHI transfers"
            ])
        
        return considerations
    
    def _assess_encryption_controls(self, security_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess encryption controls."""
        score = 0.0
        status = []
        
        if security_req.get("encryption_at_rest"):
            score += 0.4
            status.append("Encryption at rest configured")
        else:
            status.append("Missing encryption at rest")
        
        if security_req.get("encryption_in_transit"):
            score += 0.4
            status.append("Encryption in transit configured")
        else:
            status.append("Missing encryption in transit")
        
        if security_req.get("key_management"):
            score += 0.2
            status.append("Key management implemented")
        else:
            status.append("Key management needs improvement")
        
        return {
            "score": score,
            "status": status,
            "recommendations": self._get_encryption_recommendations(score)
        }
    
    def _assess_access_controls(self, security_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess access control mechanisms."""
        score = 0.0
        status = []
        
        if security_req.get("multi_factor_auth"):
            score += 0.3
            status.append("Multi-factor authentication enabled")
        else:
            status.append("Multi-factor authentication missing")
        
        if security_req.get("role_based_access"):
            score += 0.4
            status.append("Role-based access control implemented")
        else:
            status.append("Role-based access control needed")
        
        if security_req.get("access_monitoring"):
            score += 0.3
            status.append("Access monitoring configured")
        else:
            status.append("Access monitoring required")
        
        return {
            "score": score,
            "status": status,
            "recommendations": self._get_access_control_recommendations(score)
        }
    
    def _assess_data_protection(self, security_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data protection measures."""
        score = 0.0
        status = []
        
        if security_req.get("backup_encryption"):
            score += 0.3
            status.append("Backup encryption implemented")
        else:
            status.append("Backup encryption needed")
        
        if security_req.get("data_retention_policy"):
            score += 0.4
            status.append("Data retention policy defined")
        else:
            status.append("Data retention policy missing")
        
        if security_req.get("secure_deletion"):
            score += 0.3
            status.append("Secure deletion procedures implemented")
        else:
            status.append("Secure deletion procedures needed")
        
        return {
            "score": score,
            "status": status,
            "recommendations": self._get_data_protection_recommendations(score)
        }
    
    def _assess_monitoring_controls(self, security_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess monitoring and logging controls."""
        score = 0.0
        status = []
        
        if security_req.get("centralized_logging"):
            score += 0.4
            status.append("Centralized logging implemented")
        else:
            status.append("Centralized logging needed")
        
        if security_req.get("security_monitoring"):
            score += 0.3
            status.append("Security monitoring configured")
        else:
            status.append("Security monitoring required")
        
        if security_req.get("audit_trails"):
            score += 0.3
            status.append("Audit trails maintained")
        else:
            status.append("Audit trails missing")
        
        return {
            "score": score,
            "status": status,
            "recommendations": self._get_monitoring_recommendations(score)
        }
    
    def _get_regulation_requirements(self, regulation: str) -> List[str]:
        """Get specific requirements for a regulation."""
        if regulation in self.regulatory_frameworks:
            return self.regulatory_frameworks[regulation].get("key_requirements", [])
        return ["Review regulatory requirements", "Implement compliance controls"]
    
    def _get_security_improvements(self, security_assessment: Dict[str, Any]) -> List[str]:
        """Get security improvement recommendations."""
        improvements = []
        
        for category, status in security_assessment.items():
            if isinstance(status, dict) and status.get("score", 0) < 0.7:
                improvements.extend(status.get("recommendations", []))
        
        return improvements or ["Implement comprehensive security controls"]
    
    def _get_encryption_recommendations(self, score: float) -> List[str]:
        """Get encryption-specific recommendations."""
        if score < 0.5:
            return [
                "Implement AES-256 encryption for data at rest",
                "Configure TLS 1.3 for data in transit",
                "Set up proper key management system"
            ]
        elif score < 0.8:
            return [
                "Enhance key management with HSM",
                "Implement key rotation policies",
                "Add encryption monitoring"
            ]
        else:
            return ["Maintain current encryption standards"]
    
    def _get_access_control_recommendations(self, score: float) -> List[str]:
        """Get access control recommendations."""
        if score < 0.5:
            return [
                "Implement multi-factor authentication",
                "Establish role-based access control",
                "Set up access monitoring and logging"
            ]
        elif score < 0.8:
            return [
                "Enhance access monitoring",
                "Implement privileged access management",
                "Regular access reviews"
            ]
        else:
            return ["Maintain current access controls"]
    
    def _get_data_protection_recommendations(self, score: float) -> List[str]:
        """Get data protection recommendations."""
        if score < 0.5:
            return [
                "Implement encrypted backup systems",
                "Define data retention policies",
                "Establish secure deletion procedures"
            ]
        elif score < 0.8:
            return [
                "Enhance backup monitoring",
                "Automate retention policy enforcement",
                "Implement data classification"
            ]
        else:
            return ["Maintain current data protection measures"]
    
    def _get_monitoring_recommendations(self, score: float) -> List[str]:
        """Get monitoring recommendations."""
        if score < 0.5:
            return [
                "Implement centralized logging system",
                "Set up security monitoring and alerting",
                "Establish comprehensive audit trails"
            ]
        elif score < 0.8:
            return [
                "Enhance security monitoring with SIEM",
                "Implement automated incident response",
                "Add compliance reporting automation"
            ]
        else:
            return ["Maintain current monitoring capabilities"]
    
    def _calculate_overall_risk_level(self, high_risk_gaps: List[Dict[str, Any]], 
                                    medium_risk_gaps: List[Dict[str, Any]]) -> str:
        """Calculate overall compliance risk level."""
        if len(high_risk_gaps) >= 3:
            return "critical"
        elif len(high_risk_gaps) >= 1:
            return "high"
        elif len(medium_risk_gaps) >= 3:
            return "medium"
        else:
            return "low"
    
    # Enhanced methods with real data integration
    
    async def _collect_regulatory_updates(self) -> Dict[str, Any]:
        """Collect real-time regulatory updates and compliance news."""
        logger.debug("Collecting real-time regulatory updates")
        
        regulatory_updates = {
            "gdpr_updates": [],
            "hipaa_updates": [],
            "ccpa_updates": [],
            "general_compliance_news": [],
            "security_advisories": [],
            "data_breach_incidents": []
        }
        
        try:
            # Search for recent GDPR updates
            gdpr_search = await self.web_search_client.search(
                "GDPR General Data Protection Regulation updates 2024 2025 compliance requirements",
                max_results=5
            )
            regulatory_updates["gdpr_updates"] = gdpr_search.get("results", [])
            
            # Search for HIPAA updates
            hipaa_search = await self.web_search_client.search(
                "HIPAA Health Insurance Portability Accountability Act updates 2024 2025 compliance",
                max_results=5
            )
            regulatory_updates["hipaa_updates"] = hipaa_search.get("results", [])
            
            # Search for CCPA updates
            ccpa_search = await self.web_search_client.search(
                "CCPA California Consumer Privacy Act updates 2024 2025 compliance requirements",
                max_results=5
            )
            regulatory_updates["ccpa_updates"] = ccpa_search.get("results", [])
            
            # Search for general compliance news
            compliance_search = await self.web_search_client.search(
                "data privacy compliance regulations 2024 2025 enterprise security requirements",
                max_results=5
            )
            regulatory_updates["general_compliance_news"] = compliance_search.get("results", [])
            
            # Search for security advisories
            security_search = await self.web_search_client.search(
                "cybersecurity advisories data breach compliance 2024 2025 enterprise security",
                max_results=5
            )
            regulatory_updates["security_advisories"] = security_search.get("results", [])
            
            # Search for recent data breach incidents for learning
            breach_search = await self.web_search_client.search(
                "data breach incidents 2024 2025 compliance lessons learned enterprise security",
                max_results=3
            )
            regulatory_updates["data_breach_incidents"] = breach_search.get("results", [])
            
            logger.info(f"Collected regulatory updates: {sum(len(v) for v in regulatory_updates.values())} articles")
            
        except Exception as e:
            logger.warning(f"Failed to collect some regulatory updates: {str(e)}")
        
        return regulatory_updates
    
    def _prepare_regulatory_context(self, regulatory_updates: Dict[str, Any]) -> str:
        """Prepare regulatory context for LLM analysis."""
        context_parts = []
        
        for category, updates in regulatory_updates.items():
            if updates:
                context_parts.append(f"{category.replace('_', ' ').title()}:")
                for update in updates[:3]:  # Limit to top 3 per category
                    title = update.get("title")
                    snippet = update.get("snippet")
                    context_parts.append(f"- {title}: {snippet[:200]}...")
        
        return "\n".join(context_parts)
    
    def _summarize_regulatory_updates(self, regulatory_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize regulatory updates for analysis."""
        summary = {
            "total_updates": sum(len(v) for v in regulatory_updates.values()),
            "categories": list(regulatory_updates.keys()),
            "key_topics": []
        }
        
        # Extract key topics from titles
        for updates in regulatory_updates.values():
            for update in updates:
                title = update.get("title")
                if title:
                    summary["key_topics"].append(title)
        
        return summary
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response, handling both JSON and text formats with robust error handling."""
        import re
        
        try:
            # Clean the response
            response = response.strip()
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            # Try to parse as JSON first
            result = json.loads(response)
            
            # Validate result is a dictionary
            if not isinstance(result, dict):
                return self._extract_structured_data_from_text(str(response))
                
            return result
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fallback to extracting structured information from text
            return self._extract_structured_data_from_text(response)
    
    def _extract_structured_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from text when JSON parsing fails."""
        # Simple extraction logic for common patterns
        result = {
            "analysis": text,
            "extracted_points": []
        }
        
        # Extract numbered points
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•'))):
                result["extracted_points"].append(line)
        
        return result
    
    async def _identify_applicable_regulations_with_research(self, regulatory_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify applicable regulations using LLM analysis and real regulatory data.
        
        Args:
            regulatory_updates: Current regulatory updates from web search
            
        Returns:
            Dictionary containing applicable regulations with research backing
        """
        try:
            assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
            business_req = assessment_data.get("business_requirements", {})
            
            # Prepare context for LLM analysis
            regulatory_context = self._prepare_regulatory_context(regulatory_updates)
            
            analysis_prompt = f"""
            Analyze the following business requirements and determine applicable regulations based on current regulatory landscape:
            
            BUSINESS CONTEXT:
            - Industry: {business_req.get('industry', 'Not specified')}
            - Company Location: {business_req.get('company_location', 'Not specified')}
            - Target Markets: {business_req.get('target_markets', [])}
            - Data Types: {business_req.get('data_types', [])}
            - Company Size: {business_req.get('company_size', 'Not specified')}
            - Annual Revenue: {business_req.get('annual_revenue', 'Not specified')}
            
            CURRENT REGULATORY LANDSCAPE:
            {regulatory_context}
            
            Based on this information, identify:
            1. All applicable regulations (GDPR, HIPAA, CCPA, SOX, PCI_DSS, ISO_27001, SOC_2)
            2. Priority level for each regulation (Critical, High, Medium, Low)
            3. Specific requirements that apply
            4. Risk of non-compliance
            5. Implementation timeline recommendations
            
            Return response in JSON format with: applicable_regulations, priority_mapping, specific_requirements, compliance_risks, implementation_timeline.
            """
            
            llm_response = await self._call_llm(
                prompt=analysis_prompt,
                system_prompt="You are a compliance expert with deep knowledge of global data protection and industry regulations.",
                temperature=0.1,
                max_tokens=2000
            )
            
            analysis_result = self._parse_llm_response(llm_response)
            
            # Enhance with existing logic for validation
            base_analysis = await self._identify_applicable_regulations()
            
            # Merge LLM insights with base analysis
            enhanced_result = {
                "applicable_regulations": analysis_result.get("applicable_regulations", base_analysis["applicable_regulations"]),
                "priority_mapping": analysis_result.get("priority_mapping", {}),
                "specific_requirements": analysis_result.get("specific_requirements", {}),
                "compliance_risks": analysis_result.get("compliance_risks", {}),
                "implementation_timeline": analysis_result.get("implementation_timeline", {}),
                "regulation_details": base_analysis["regulation_details"],
                "applicability_reasons": base_analysis["applicability_reasons"],
                "llm_analysis": analysis_result.get("analysis"),
                "regulatory_update_summary": self._summarize_regulatory_updates(regulatory_updates)
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"LLM-enhanced regulation identification failed, using fallback: {str(e)}")
            return await self._identify_applicable_regulations()
    
    async def _assess_compliance_posture_with_real_data(self, applicable_regulations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess compliance posture using LLM analysis and real compliance benchmarks.
        
        Args:
            applicable_regulations: Result from regulation identification
            
        Returns:
            Dictionary containing detailed compliance assessment
        """
        try:
            assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
            technical_req = assessment_data.get("technical_requirements", {})
            
            # Prepare technical context for analysis
            tech_context = f"""
            Current Technical Configuration:
            - Cloud Provider: {technical_req.get('cloud_provider', 'Not specified')}
            - Data Processing: {technical_req.get('data_processing_requirements', [])}
            - Security Requirements: {technical_req.get('security_requirements', [])}
            - Encryption: {technical_req.get('encryption_requirements', 'Not specified')}
            - Access Control: {technical_req.get('access_control', 'Not specified')}
            - Data Backup: {technical_req.get('backup_requirements', 'Not specified')}
            - Monitoring: {technical_req.get('monitoring_requirements', [])}
            """
            
            regulations_list = applicable_regulations.get("applicable_regulations", [])
            
            assessment_prompt = f"""
            Assess the current compliance posture for the following regulations based on technical configuration:
            
            APPLICABLE REGULATIONS: {', '.join(regulations_list)}
            
            {tech_context}
            
            For each regulation, assess:
            1. Current compliance level (0-100%)
            2. Critical gaps in current setup
            3. Security control adequacy
            4. Data handling compliance
            5. Documentation and audit trail status
            6. Risk exposure level
            7. Immediate action items
            
            Provide specific, actionable insights based on current technical requirements.
            Return in JSON format with regulation_scores, critical_gaps, security_adequacy, data_handling_compliance, documentation_status, risk_levels, action_items.
            """
            
            llm_response = await self._call_llm(
                prompt=assessment_prompt,
                system_prompt="You are a compliance auditor with expertise in technical compliance assessment across multiple regulatory frameworks.",
                temperature=0.1,
                max_tokens=2500
            )
            
            llm_analysis = self._parse_llm_response(llm_response)
            
            # Enhance with base assessment
            base_assessment = await self._assess_compliance_posture(applicable_regulations)
            
            # Create comprehensive assessment
            enhanced_assessment = {
                "regulation_scores": llm_analysis.get("regulation_scores", base_assessment.get("compliance_scores", {})),
                "compliance_status": base_assessment.get("compliance_status", {}),
                "critical_gaps": llm_analysis.get("critical_gaps", {}),
                "security_adequacy": llm_analysis.get("security_adequacy", {}),
                "data_handling_compliance": llm_analysis.get("data_handling_compliance", {}),
                "documentation_status": llm_analysis.get("documentation_status", {}),
                "risk_levels": llm_analysis.get("risk_levels", {}),
                "action_items": llm_analysis.get("action_items", {}),
                "overall_compliance_score": self._calculate_overall_compliance_score(llm_analysis.get("regulation_scores", {})),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                "llm_insights": llm_analysis.get("analysis")
            }
            
            return enhanced_assessment
            
        except Exception as e:
            logger.warning(f"Enhanced compliance assessment failed, using fallback: {str(e)}")
            return await self._assess_compliance_posture(applicable_regulations)
    
    async def _assess_security_controls_with_benchmarks(self) -> Dict[str, Any]:
        """
        Assess security controls against industry benchmarks using real data.
        
        Returns:
            Dictionary containing security controls assessment
        """
        try:
            # Search for current security benchmarks and standards
            security_research = await self.web_search_client.search(
                "enterprise security controls benchmarks 2024 2025 NIST CIS OWASP best practices",
                max_results=5
            )
            
            assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
            technical_req = assessment_data.get("technical_requirements", {})
            
            security_context = f"""
            Current Security Setup:
            - Security Requirements: {technical_req.get('security_requirements', [])}
            - Encryption: {technical_req.get('encryption_requirements', 'Not specified')}
            - Access Control: {technical_req.get('access_control', 'Not specified')}
            - Network Security: {technical_req.get('network_security', 'Not specified')}
            - Monitoring: {technical_req.get('monitoring_requirements', [])}
            
            Current Security Benchmarks (2024-2025):
            """
            
            for result in security_research.get("results", [])[:3]:
                security_context += f"- {result.get('title')}: {result.get('snippet')[:200]}...\n"
            
            security_prompt = f"""
            Assess security controls against current industry benchmarks and standards:
            
            {security_context}
            
            Evaluate against major frameworks:
            1. NIST Cybersecurity Framework
            2. CIS Controls
            3. OWASP Top 10
            4. ISO 27001 controls
            5. Cloud Security Alliance guidelines
            
            For each framework, assess:
            - Current implementation level (0-100%)
            - Critical control gaps
            - Priority improvements needed
            - Implementation complexity
            - Cost implications
            - Timeline for full compliance
            
            Return in JSON format with framework_scores, control_gaps, priority_improvements, implementation_complexity, cost_estimates, compliance_timeline.
            """
            
            llm_response = await self._call_llm(
                prompt=security_prompt,
                system_prompt="You are a cybersecurity expert specializing in enterprise security frameworks and compliance benchmarking.",
                temperature=0.1,
                max_tokens=2000
            )
            
            analysis_result = self._parse_llm_response(llm_response)
            
            return {
                "framework_scores": analysis_result.get("framework_scores", {}),
                "control_gaps": analysis_result.get("control_gaps", {}),
                "priority_improvements": analysis_result.get("priority_improvements", []),
                "implementation_complexity": analysis_result.get("implementation_complexity", {}),
                "cost_estimates": analysis_result.get("cost_estimates", {}),
                "compliance_timeline": analysis_result.get("compliance_timeline", {}),
                "security_research_data": security_research.get("results", []),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                "benchmarking_insights": analysis_result.get("analysis")
            }
            
        except Exception as e:
            logger.warning(f"Security controls benchmarking failed: {str(e)}")
            return {
                "framework_scores": {},
                "control_gaps": ["Security assessment unavailable"],
                "priority_improvements": ["Conduct manual security review"],
                "implementation_complexity": "medium",
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    async def _identify_compliance_gaps_with_real_data(
        self, 
        applicable_regulations: Dict[str, Any], 
        compliance_assessment: Dict[str, Any],
        security_assessment: Dict[str, Any],
        regulatory_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify compliance gaps using comprehensive real data analysis.
        
        Args:
            applicable_regulations: Applicable regulations analysis
            compliance_assessment: Current compliance posture
            security_assessment: Security controls assessment
            regulatory_updates: Latest regulatory updates
            
        Returns:
            Dictionary containing identified compliance gaps
        """
        try:
            gap_analysis_prompt = f"""
            Analyze compliance gaps based on comprehensive assessment data:
            
            APPLICABLE REGULATIONS:
            {json.dumps(applicable_regulations, indent=2)}
            
            CURRENT COMPLIANCE SCORES:
            {json.dumps(compliance_assessment.get('regulation_scores', {}), indent=2)}
            
            SECURITY CONTROL GAPS:
            {json.dumps(security_assessment.get('control_gaps', {}), indent=2)}
            
            RECENT REGULATORY CHANGES:
            {self._prepare_regulatory_context(regulatory_updates)}
            
            Identify and prioritize compliance gaps:
            1. Critical gaps requiring immediate attention
            2. High-priority gaps for next quarter
            3. Medium-priority gaps for 6-month timeline
            4. Long-term strategic gaps
            5. Resource requirements for each gap
            6. Business impact of leaving gaps unaddressed
            7. Implementation complexity and dependencies
            
            Return in JSON format with critical_gaps, high_priority_gaps, medium_priority_gaps, long_term_gaps, resource_requirements, business_impact, implementation_plan.
            """
            
            llm_response = await self._call_llm(
                prompt=gap_analysis_prompt,
                system_prompt="You are a compliance strategist expert at identifying and prioritizing regulatory gaps for enterprise organizations.",
                temperature=0.1,
                max_tokens=2500
            )
            
            gap_analysis = self._parse_llm_response(llm_response)
            
            return {
                "critical_gaps": gap_analysis.get("critical_gaps", []),
                "high_priority_gaps": gap_analysis.get("high_priority_gaps", []),
                "medium_priority_gaps": gap_analysis.get("medium_priority_gaps", []),
                "long_term_gaps": gap_analysis.get("long_term_gaps", []),
                "resource_requirements": gap_analysis.get("resource_requirements", {}),
                "business_impact": gap_analysis.get("business_impact", {}),
                "implementation_plan": gap_analysis.get("implementation_plan", {}),
                "gap_analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "strategic_insights": gap_analysis.get("analysis")
            }
            
        except Exception as e:
            logger.warning(f"Compliance gap analysis failed: {str(e)}")
            return {
                "critical_gaps": ["Unable to perform automated gap analysis"],
                "high_priority_gaps": ["Manual compliance review required"],
                "error": str(e),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _generate_compliance_recommendations_with_research(
        self,
        applicable_regulations: Dict[str, Any],
        compliance_gaps: Dict[str, Any],
        data_residency_analysis: Dict[str, Any],
        regulatory_updates: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate compliance recommendations using LLM analysis and market research.
        
        Args:
            applicable_regulations: Applicable regulations
            compliance_gaps: Identified compliance gaps
            data_residency_analysis: Data residency requirements
            regulatory_updates: Latest regulatory updates
            
        Returns:
            List of detailed compliance recommendations
        """
        try:
            # Research compliance solutions and best practices
            solutions_research = await self.web_search_client.search(
                "enterprise compliance solutions 2024 2025 data protection GDPR HIPAA implementation",
                max_results=5
            )
            
            recommendations_prompt = f"""
            Generate comprehensive compliance recommendations based on analysis:
            
            COMPLIANCE GAPS TO ADDRESS:
            Critical: {compliance_gaps.get('critical_gaps', [])}
            High Priority: {compliance_gaps.get('high_priority_gaps', [])}
            Medium Priority: {compliance_gaps.get('medium_priority_gaps', [])}
            
            DATA RESIDENCY REQUIREMENTS:
            {json.dumps(data_residency_analysis, indent=2)}
            
            CURRENT COMPLIANCE SOLUTIONS (2024-2025):
            """
            
            for result in solutions_research.get("results", [])[:3]:
                recommendations_prompt += f"- {result.get('title')}: {result.get('snippet')[:200]}...\n"
            
            recommendations_prompt += f"""
            
            Generate specific, actionable recommendations:
            1. Immediate actions (0-30 days)
            2. Short-term implementations (1-3 months)
            3. Medium-term projects (3-6 months)
            4. Long-term strategic initiatives (6-12 months)
            
            For each recommendation include:
            - Specific implementation steps
            - Required resources and budget estimates
            - Expected compliance improvement
            - Business benefits
            - Risk mitigation value
            - Implementation complexity
            - Vendor/solution recommendations
            
            Return in JSON format with immediate_actions, short_term_implementations, medium_term_projects, long_term_initiatives.
            """
            
            llm_response = await self._call_llm(
                prompt=recommendations_prompt,
                system_prompt="You are a compliance consultant specializing in practical implementation of enterprise regulatory compliance programs.",
                temperature=0.2,
                max_tokens=3000
            )
            
            recommendations_data = self._parse_llm_response(llm_response)
            
            # Structure recommendations as a list
            recommendations = []
            
            # Process immediate actions
            for action in recommendations_data.get("immediate_actions", []):
                recommendations.append({
                    "title": f"Critical Compliance Action: {action.get('title', 'Immediate Action Required')}",
                    "description": action.get("description", str(action)),
                    "priority": "critical",
                    "timeline": "0-30 days",
                    "category": "immediate_action",
                    "implementation_steps": action.get("implementation_steps", []),
                    "resources_required": action.get("resources_required", "To be determined"),
                    "compliance_impact": action.get("compliance_impact", "High"),
                    "business_benefits": action.get("business_benefits", []),
                    "estimated_cost": action.get("estimated_cost", "Variable")
                })
            
            # Process short-term implementations
            for implementation in recommendations_data.get("short_term_implementations", []):
                recommendations.append({
                    "title": f"Short-term Implementation: {implementation.get('title', 'Compliance Implementation')}",
                    "description": implementation.get("description", str(implementation)),
                    "priority": "high",
                    "timeline": "1-3 months",
                    "category": "short_term",
                    "implementation_steps": implementation.get("implementation_steps", []),
                    "resources_required": implementation.get("resources_required", "Dedicated team"),
                    "compliance_impact": implementation.get("compliance_impact", "Medium-High"),
                    "business_benefits": implementation.get("business_benefits", []),
                    "estimated_cost": implementation.get("estimated_cost", "Moderate")
                })
            
            # Process medium-term projects
            for project in recommendations_data.get("medium_term_projects", []):
                recommendations.append({
                    "title": f"Medium-term Project: {project.get('title', 'Compliance Project')}",
                    "description": project.get("description", str(project)),
                    "priority": "medium",
                    "timeline": "3-6 months",
                    "category": "medium_term",
                    "implementation_steps": project.get("implementation_steps", []),
                    "resources_required": project.get("resources_required", "Project team"),
                    "compliance_impact": project.get("compliance_impact", "Medium"),
                    "business_benefits": project.get("business_benefits", []),
                    "estimated_cost": project.get("estimated_cost", "Significant")
                })
            
            # Process long-term initiatives
            for initiative in recommendations_data.get("long_term_initiatives", []):
                recommendations.append({
                    "title": f"Strategic Initiative: {initiative.get('title', 'Long-term Compliance Strategy')}",
                    "description": initiative.get("description", str(initiative)),
                    "priority": "low",
                    "timeline": "6-12 months",
                    "category": "strategic",
                    "implementation_steps": initiative.get("implementation_steps", []),
                    "resources_required": initiative.get("resources_required", "Strategic investment"),
                    "compliance_impact": initiative.get("compliance_impact", "Strategic"),
                    "business_benefits": initiative.get("business_benefits", []),
                    "estimated_cost": initiative.get("estimated_cost", "High")
                })
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Enhanced recommendations generation failed: {str(e)}")
            return [{
                "title": "Manual Compliance Review Required",
                "description": "Automated recommendation generation failed. Manual review by compliance expert needed.",
                "priority": "high",
                "timeline": "Immediate",
                "category": "fallback",
                "error": str(e)
            }]
    
    async def _create_compliance_roadmap_with_real_data(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a compliance roadmap using real implementation data and timelines.
        
        Args:
            recommendations: List of compliance recommendations
            
        Returns:
            Dictionary containing detailed compliance roadmap
        """
        try:
            roadmap_prompt = f"""
            Create a comprehensive compliance roadmap based on recommendations:
            
            RECOMMENDATIONS TO IMPLEMENT:
            {json.dumps(recommendations, indent=2)}
            
            Create a strategic roadmap including:
            1. Phase-based implementation plan
            2. Resource allocation timeline
            3. Budget planning and cost distribution
            4. Risk mitigation milestones
            5. Compliance metric targets
            6. Dependencies and critical path
            7. Success criteria and KPIs
            8. Quarterly review checkpoints
            
            Return in JSON format with implementation_phases, resource_timeline, budget_plan, risk_milestones, compliance_targets, dependencies, success_criteria, review_schedule.
            """
            
            llm_response = await self._call_llm(
                prompt=roadmap_prompt,
                system_prompt="You are a compliance program manager expert at creating strategic implementation roadmaps for enterprise compliance initiatives.",
                temperature=0.1,
                max_tokens=2500
            )
            
            roadmap_data = self._parse_llm_response(llm_response)
            
            # Organize recommendations by timeline
            timeline_organization = {
                "0-30_days": [r for r in recommendations if "0-30 days" in r.get("timeline")],
                "1-3_months": [r for r in recommendations if "1-3 months" in r.get("timeline")],
                "3-6_months": [r for r in recommendations if "3-6 months" in r.get("timeline")],
                "6-12_months": [r for r in recommendations if "6-12 months" in r.get("timeline")]
            }
            
            return {
                "implementation_phases": roadmap_data.get("implementation_phases", {}),
                "resource_timeline": roadmap_data.get("resource_timeline", {}),
                "budget_plan": roadmap_data.get("budget_plan", {}),
                "risk_milestones": roadmap_data.get("risk_milestones", {}),
                "compliance_targets": roadmap_data.get("compliance_targets", {}),
                "dependencies": roadmap_data.get("dependencies", {}),
                "success_criteria": roadmap_data.get("success_criteria", {}),
                "review_schedule": roadmap_data.get("review_schedule", {}),
                "timeline_organization": timeline_organization,
                "total_recommendations": len(recommendations),
                "estimated_completion": "12 months",
                "roadmap_created": datetime.now(timezone.utc).isoformat(),
                "strategic_insights": roadmap_data.get("analysis")
            }
            
        except Exception as e:
            logger.warning(f"Compliance roadmap generation failed: {str(e)}")
            return {
                "implementation_phases": {"phase_1": "Manual planning required"},
                "timeline_organization": {
                    "immediate": [r for r in recommendations if r.get("priority") == "critical"],
                    "short_term": [r for r in recommendations if r.get("priority") == "high"],
                    "medium_term": [r for r in recommendations if r.get("priority") == "medium"],
                    "long_term": [r for r in recommendations if r.get("priority") == "low"]
                },
                "total_recommendations": len(recommendations),
                "error": str(e),
                "roadmap_created": datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_overall_compliance_score(self, regulation_scores: Dict[str, Any]) -> float:
        """Calculate overall compliance score from individual regulation scores."""
        if not regulation_scores:
            return 0.0
        
        scores = []
        for score in regulation_scores.values():
            if isinstance(score, (int, float)):
                scores.append(float(score))
            elif isinstance(score, dict) and "score" in score:
                scores.append(float(score["score"]))
        
        return sum(scores) / len(scores) if scores else 0.0