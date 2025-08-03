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
from ..core.llm_client import get_llm_client

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
                self.llm_client = await get_llm_client()
            
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
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        
        applicable_regs = []
        regulation_reasons = {}
        
        # Analyze business context to determine applicable regulations
        industry = business_req.get("industry", "").lower()
        company_location = business_req.get("company_location", "").lower()
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
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
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
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        
        residency_requirements = {}
        recommended_regions = []
        restrictions = []
        
        for regulation in applicable_regulations.get("applicable_regulations", []):
            if regulation in self.regulatory_frameworks:
                framework = self.regulatory_frameworks[regulation]
                residency_req = framework.get("data_residency", "")
                
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
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
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
                    "potential_penalties": self.regulatory_frameworks.get(regulation, {}).get("penalties", "Unknown")
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
                num_results=5
            )
            regulatory_updates["gdpr_updates"] = gdpr_search.get("results", [])
            
            # Search for HIPAA updates
            hipaa_search = await self.web_search_client.search(
                "HIPAA Health Insurance Portability Accountability Act updates 2024 2025 compliance",
                num_results=5
            )
            regulatory_updates["hipaa_updates"] = hipaa_search.get("results", [])
            
            # Search for CCPA updates
            ccpa_search = await self.web_search_client.search(
                "CCPA California Consumer Privacy Act updates 2024 2025 compliance requirements",
                num_results=5
            )
            regulatory_updates["ccpa_updates"] = ccpa_search.get("results", [])
            
            # Search for general compliance news
            compliance_search = await self.web_search_client.search(
                "data privacy compliance regulations 2024 2025 enterprise security requirements",
                num_results=5
            )
            regulatory_updates["general_compliance_news"] = compliance_search.get("results", [])
            
            # Search for security advisories
            security_search = await self.web_search_client.search(
                "cybersecurity advisories data breach compliance 2024 2025 enterprise security",
                num_results=5
            )
            regulatory_updates["security_advisories"] = security_search.get("results", [])
            
            # Search for recent data breach incidents for learning
            breach_search = await self.web_search_client.search(
                "data breach incidents 2024 2025 compliance lessons learned enterprise security",
                num_results=3
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
                    title = update.get("title", "")
                    snippet = update.get("snippet", "")
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
                title = update.get("title", "")
                if title:
                    summary["key_topics"].append(title)
        
        return summary
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response, handling both JSON and text formats."""
        try:
            # Try to parse as JSON first
            return json.loads(response)
        except json.JSONDecodeError:
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