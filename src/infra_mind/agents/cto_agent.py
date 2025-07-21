"""
CTO Agent for Infra Mind.

Provides strategic business alignment and high-level architecture decisions.
Focuses on ROI calculations, budget optimization, and executive communication.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class CTOAgent(BaseAgent):
    """
    CTO Agent for strategic planning and business alignment.
    
    This agent focuses on:
    - Strategic business alignment
    - ROI calculations and budget optimization
    - Executive-level recommendations
    - High-level architecture decisions
    - Business risk assessment
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize CTO Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="CTO Agent",
                role=AgentRole.CTO,
                tools_enabled=["data_processor", "calculator", "cloud_api"],
                temperature=0.1,  # Lower temperature for more consistent strategic advice
                max_tokens=2000,
                custom_config={
                    "focus_areas": [
                        "strategic_alignment",
                        "roi_optimization", 
                        "budget_planning",
                        "risk_assessment",
                        "executive_communication"
                    ],
                    "business_frameworks": [
                        "cost_benefit_analysis",
                        "risk_matrix",
                        "strategic_roadmap",
                        "investment_prioritization"
                    ]
                }
            )
        
        super().__init__(config)
        
        # CTO-specific attributes
        self.strategic_frameworks = [
            "Total Cost of Ownership (TCO)",
            "Return on Investment (ROI)",
            "Business Value Assessment",
            "Risk-Adjusted Returns",
            "Strategic Alignment Matrix"
        ]
        
        self.business_priorities = [
            "cost_optimization",
            "scalability",
            "reliability",
            "security",
            "time_to_market",
            "competitive_advantage"
        ]
        
        logger.info("CTO Agent initialized with strategic planning capabilities")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute CTO agent's main strategic analysis logic.
        
        Returns:
            Dictionary with strategic recommendations and analysis
        """
        logger.info("CTO Agent starting strategic analysis")
        
        try:
            # Step 1: Analyze business context and requirements
            business_analysis = await self._analyze_business_context()
            
            # Step 2: Perform strategic alignment assessment
            strategic_alignment = await self._assess_strategic_alignment()
            
            # Step 3: Calculate ROI and financial projections
            financial_analysis = await self._perform_financial_analysis()
            
            # Step 4: Assess business risks and mitigation strategies
            risk_assessment = await self._assess_business_risks()
            
            # Step 5: Generate strategic recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(
                business_analysis, strategic_alignment, financial_analysis, risk_assessment
            )
            
            # Step 6: Create executive summary
            executive_summary = await self._create_executive_summary(strategic_recommendations)
            
            result = {
                "recommendations": strategic_recommendations,
                "data": {
                    "business_analysis": business_analysis,
                    "strategic_alignment": strategic_alignment,
                    "financial_analysis": financial_analysis,
                    "risk_assessment": risk_assessment,
                    "executive_summary": executive_summary,
                    "frameworks_used": self.strategic_frameworks,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("CTO Agent completed strategic analysis successfully")
            return result
            
        except Exception as e:
            logger.error(f"CTO Agent analysis failed: {str(e)}")
            raise
    
    async def _analyze_business_context(self) -> Dict[str, Any]:
        """Analyze business context and requirements."""
        logger.debug("Analyzing business context")
        
        # Use data processing tool to analyze assessment data
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        if not analysis_result.is_success:
            logger.warning(f"Data analysis failed: {analysis_result.error}")
            return {"error": "Failed to analyze business context"}
        
        business_context = {
            "company_profile": self._extract_company_profile(assessment_data),
            "business_drivers": self._identify_business_drivers(assessment_data),
            "current_challenges": self._identify_current_challenges(assessment_data),
            "growth_trajectory": self._assess_growth_trajectory(assessment_data),
            "competitive_position": self._assess_competitive_position(assessment_data),
            "data_insights": analysis_result.data
        }
        
        return business_context
    
    async def _assess_strategic_alignment(self) -> Dict[str, Any]:
        """Assess strategic alignment of infrastructure needs with business goals."""
        logger.debug("Assessing strategic alignment")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        
        # Extract business and technical requirements
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        alignment_score = 0.0
        alignment_factors = []
        
        # Assess alignment factors
        if business_req.get("primary_goals"):
            goals = business_req["primary_goals"]
            if isinstance(goals, list):
                for goal in goals:
                    if goal in ["cost_reduction", "efficiency", "scalability"]:
                        alignment_score += 0.2
                        alignment_factors.append(f"Business goal '{goal}' aligns with infrastructure optimization")
        
        if technical_req.get("workload_types"):
            workloads = technical_req["workload_types"]
            if isinstance(workloads, list):
                if "ai_ml" in workloads or "machine_learning" in workloads:
                    alignment_score += 0.3
                    alignment_factors.append("AI/ML workloads indicate strategic technology investment")
                if "web_application" in workloads:
                    alignment_score += 0.1
                    alignment_factors.append("Web applications support digital transformation")
        
        # Assess budget alignment
        if business_req.get("budget_range"):
            budget = business_req["budget_range"]
            if budget in ["$10k-50k", "$50k-100k", "$100k+"]:
                alignment_score += 0.2
                alignment_factors.append("Budget range indicates serious infrastructure investment")
        
        # Cap alignment score at 1.0
        alignment_score = min(alignment_score, 1.0)
        
        return {
            "alignment_score": alignment_score,
            "alignment_level": self._categorize_alignment(alignment_score),
            "alignment_factors": alignment_factors,
            "strategic_gaps": self._identify_strategic_gaps(assessment_data),
            "recommendations": self._generate_alignment_recommendations(alignment_score)
        }
    
    async def _perform_financial_analysis(self) -> Dict[str, Any]:
        """Perform ROI calculations and financial projections."""
        logger.debug("Performing financial analysis")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Extract financial parameters
        budget_range = business_req.get("budget_range", "$10k-50k")
        company_size = business_req.get("company_size", "startup")
        expected_users = technical_req.get("expected_users", 1000)
        
        # Convert budget range to numeric values
        budget_min, budget_max = self._parse_budget_range(budget_range)
        
        # Calculate cost estimates using calculator tool
        cost_result = await self._use_tool(
            "calculator",
            operation="cost_estimate",
            base_cost=budget_min,
            users=expected_users,
            scaling_factor=self._get_scaling_factor(company_size)
        )
        
        # Calculate ROI analysis
        roi_result = await self._use_tool(
            "calculator",
            operation="roi_analysis",
            investment=budget_max,
            annual_savings=self._estimate_annual_savings(company_size, expected_users),
            time_horizon=3
        )
        
        financial_analysis = {
            "budget_analysis": {
                "requested_range": budget_range,
                "min_budget": budget_min,
                "max_budget": budget_max,
                "recommended_budget": (budget_min + budget_max) / 2
            },
            "cost_projections": cost_result.data if cost_result.is_success else {},
            "roi_analysis": roi_result.data if roi_result.is_success else {},
            "financial_metrics": self._calculate_financial_metrics(budget_min, budget_max, expected_users),
            "investment_priorities": self._prioritize_investments(assessment_data)
        }
        
        return financial_analysis
    
    async def _assess_business_risks(self) -> Dict[str, Any]:
        """Assess business risks and mitigation strategies."""
        logger.debug("Assessing business risks")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        compliance_req = assessment_data.get("compliance_requirements", {})
        
        risks = []
        
        # Technology risks
        workload_types = technical_req.get("workload_types", [])
        if isinstance(workload_types, list):
            if "ai_ml" in workload_types or "machine_learning" in workload_types:
                risks.append({
                    "category": "technology",
                    "risk": "AI/ML Technology Complexity",
                    "impact": "high",
                    "probability": "medium",
                    "description": "AI/ML workloads require specialized expertise and infrastructure",
                    "mitigation": "Partner with cloud providers' managed AI services, invest in team training"
                })
        
        # Scalability risks
        expected_users = technical_req.get("expected_users", 0)
        if expected_users > 10000:
            risks.append({
                "category": "scalability",
                "risk": "High User Load Risk",
                "impact": "high",
                "probability": "medium",
                "description": "High user expectations may exceed infrastructure capacity",
                "mitigation": "Implement auto-scaling, load balancing, and performance monitoring"
            })
        
        # Budget risks
        budget_range = business_req.get("budget_range", "")
        if budget_range in ["$1k-10k", "$10k-50k"]:
            risks.append({
                "category": "financial",
                "risk": "Budget Constraints",
                "impact": "medium",
                "probability": "high",
                "description": "Limited budget may restrict infrastructure options",
                "mitigation": "Prioritize MVP features, use cost-effective cloud services, implement gradual scaling"
            })
        
        # Compliance risks
        if compliance_req.get("regulations"):
            regulations = compliance_req["regulations"]
            if isinstance(regulations, list) and len(regulations) > 0:
                risks.append({
                    "category": "compliance",
                    "risk": "Regulatory Compliance",
                    "impact": "high",
                    "probability": "medium",
                    "description": f"Must comply with {', '.join(regulations)} regulations",
                    "mitigation": "Use compliant cloud services, implement proper data governance, regular audits"
                })
        
        # Vendor lock-in risks
        risks.append({
            "category": "strategic",
            "risk": "Vendor Lock-in",
            "impact": "medium",
            "probability": "medium",
            "description": "Over-reliance on single cloud provider may limit flexibility",
            "mitigation": "Consider multi-cloud strategy, use containerization, maintain portability"
        })
        
        return {
            "identified_risks": risks,
            "risk_matrix": self._create_risk_matrix(risks),
            "mitigation_priorities": self._prioritize_risk_mitigation(risks),
            "overall_risk_level": self._calculate_overall_risk_level(risks)
        }
    
    async def _generate_strategic_recommendations(self, business_analysis: Dict[str, Any], 
                                                strategic_alignment: Dict[str, Any],
                                                financial_analysis: Dict[str, Any],
                                                risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on analysis."""
        logger.debug("Generating strategic recommendations")
        
        recommendations = []
        
        # Strategic alignment recommendations
        alignment_score = strategic_alignment.get("alignment_score", 0.0)
        if alignment_score < 0.7:
            recommendations.append({
                "category": "strategic_alignment",
                "priority": "high",
                "title": "Improve Strategic Alignment",
                "description": "Current infrastructure plans show limited alignment with business goals",
                "rationale": f"Alignment score of {alignment_score:.1f} indicates strategic gaps",
                "actions": [
                    "Conduct stakeholder alignment workshop",
                    "Revise infrastructure priorities to match business objectives",
                    "Establish clear success metrics tied to business outcomes"
                ],
                "business_impact": "Ensures infrastructure investments drive business value",
                "timeline": "2-4 weeks",
                "investment_required": "Low (internal resources)"
            })
        
        # Financial optimization recommendations
        roi_data = financial_analysis.get("roi_analysis", {})
        roi_percentage = roi_data.get("roi_percentage", 0)
        if roi_percentage < 50:
            recommendations.append({
                "category": "financial_optimization",
                "priority": "high",
                "title": "Optimize Investment Returns",
                "description": "Current investment projections show suboptimal ROI",
                "rationale": f"Projected ROI of {roi_percentage}% is below industry benchmarks",
                "actions": [
                    "Focus on high-impact, low-cost infrastructure improvements",
                    "Implement phased rollout to validate assumptions",
                    "Negotiate better pricing with cloud providers"
                ],
                "business_impact": "Maximizes return on infrastructure investment",
                "timeline": "1-3 months",
                "investment_required": "Medium (optimization efforts)"
            })
        
        # Risk mitigation recommendations
        high_risks = [r for r in risk_assessment.get("identified_risks", []) if r.get("impact") == "high"]
        if high_risks:
            recommendations.append({
                "category": "risk_management",
                "priority": "high",
                "title": "Address High-Impact Risks",
                "description": f"Identified {len(high_risks)} high-impact risks requiring immediate attention",
                "rationale": "High-impact risks could significantly affect project success",
                "actions": [risk["mitigation"] for risk in high_risks[:3]],  # Top 3 mitigations
                "business_impact": "Reduces project risk and increases success probability",
                "timeline": "Immediate - 2 months",
                "investment_required": "Variable (depends on specific risks)"
            })
        
        # Technology strategy recommendations
        company_profile = business_analysis.get("company_profile", {})
        if company_profile.get("company_size") in ["startup", "small"]:
            recommendations.append({
                "category": "technology_strategy",
                "priority": "medium",
                "title": "Adopt Cloud-Native Approach",
                "description": "Leverage managed cloud services to reduce operational overhead",
                "rationale": "Small teams benefit from reduced infrastructure management burden",
                "actions": [
                    "Prioritize managed services over self-hosted solutions",
                    "Implement Infrastructure as Code for consistency",
                    "Use serverless computing where appropriate"
                ],
                "business_impact": "Reduces operational complexity and accelerates development",
                "timeline": "3-6 months",
                "investment_required": "Medium (migration and training)"
            })
        
        # Scalability recommendations
        growth_trajectory = business_analysis.get("growth_trajectory", {})
        if growth_trajectory.get("growth_rate", "moderate") in ["high", "aggressive"]:
            recommendations.append({
                "category": "scalability",
                "priority": "high",
                "title": "Implement Scalable Architecture",
                "description": "Prepare infrastructure for rapid growth and scaling demands",
                "rationale": "High growth rate requires proactive scalability planning",
                "actions": [
                    "Design for horizontal scaling from the start",
                    "Implement auto-scaling and load balancing",
                    "Use microservices architecture for flexibility"
                ],
                "business_impact": "Enables rapid scaling without infrastructure bottlenecks",
                "timeline": "3-6 months",
                "investment_required": "High (architecture redesign)"
            })
        
        return recommendations
    
    async def _create_executive_summary(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create executive summary for leadership."""
        logger.debug("Creating executive summary")
        
        high_priority_recs = [r for r in recommendations if r.get("priority") == "high"]
        total_investment = len(recommendations) * 50000  # Rough estimate
        
        summary = {
            "key_findings": [
                f"Identified {len(recommendations)} strategic recommendations",
                f"{len(high_priority_recs)} high-priority actions require immediate attention",
                "Infrastructure alignment with business goals needs improvement",
                "ROI optimization opportunities identified"
            ],
            "strategic_priorities": [
                rec["title"] for rec in high_priority_recs[:3]
            ],
            "investment_summary": {
                "total_recommendations": len(recommendations),
                "high_priority_count": len(high_priority_recs),
                "estimated_investment": f"${total_investment:,}",
                "expected_timeline": "3-6 months for core implementations"
            },
            "business_impact": [
                "Improved infrastructure ROI",
                "Reduced operational risks",
                "Enhanced scalability for growth",
                "Better alignment with business objectives"
            ],
            "next_steps": [
                "Review and prioritize recommendations with stakeholders",
                "Develop detailed implementation roadmap",
                "Secure budget approval for high-priority initiatives",
                "Establish success metrics and monitoring"
            ]
        }
        
        return summary
    
    # Helper methods
    
    def _extract_company_profile(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company profile from assessment data."""
        business_req = assessment_data.get("business_requirements", {})
        
        return {
            "company_size": business_req.get("company_size", "unknown"),
            "industry": business_req.get("industry", "unknown"),
            "budget_range": business_req.get("budget_range", "unknown"),
            "primary_goals": business_req.get("primary_goals", [])
        }
    
    def _identify_business_drivers(self, assessment_data: Dict[str, Any]) -> List[str]:
        """Identify key business drivers."""
        business_req = assessment_data.get("business_requirements", {})
        drivers = []
        
        goals = business_req.get("primary_goals", [])
        if isinstance(goals, list):
            for goal in goals:
                if goal == "cost_reduction":
                    drivers.append("Cost optimization and efficiency")
                elif goal == "scalability":
                    drivers.append("Business growth and scaling")
                elif goal == "innovation":
                    drivers.append("Technology innovation and competitive advantage")
                elif goal == "compliance":
                    drivers.append("Regulatory compliance and risk management")
        
        return drivers or ["General infrastructure improvement"]
    
    def _identify_current_challenges(self, assessment_data: Dict[str, Any]) -> List[str]:
        """Identify current business challenges."""
        challenges = []
        
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Infer challenges from requirements
        if business_req.get("budget_range") in ["$1k-10k", "$10k-50k"]:
            challenges.append("Limited budget for infrastructure investment")
        
        if technical_req.get("expected_users", 0) > 10000:
            challenges.append("High scalability requirements")
        
        workloads = technical_req.get("workload_types", [])
        if isinstance(workloads, list) and "ai_ml" in workloads:
            challenges.append("Complex AI/ML infrastructure requirements")
        
        return challenges or ["Standard infrastructure scaling challenges"]
    
    def _assess_growth_trajectory(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess company growth trajectory."""
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        company_size = business_req.get("company_size", "startup")
        expected_users = technical_req.get("expected_users", 1000)
        
        # Simple growth assessment logic
        if company_size == "startup" and expected_users > 10000:
            growth_rate = "aggressive"
        elif company_size in ["small", "medium"] and expected_users > 5000:
            growth_rate = "high"
        elif company_size == "enterprise":
            growth_rate = "moderate"
        else:
            growth_rate = "steady"
        
        return {
            "growth_rate": growth_rate,
            "growth_indicators": [
                f"Company size: {company_size}",
                f"Expected users: {expected_users:,}"
            ]
        }
    
    def _assess_competitive_position(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess competitive position."""
        business_req = assessment_data.get("business_requirements", {})
        
        industry = business_req.get("industry", "technology")
        goals = business_req.get("primary_goals", [])
        
        competitive_factors = []
        if isinstance(goals, list):
            if "innovation" in goals:
                competitive_factors.append("Innovation-focused strategy")
            if "cost_reduction" in goals:
                competitive_factors.append("Cost leadership approach")
        
        return {
            "industry": industry,
            "competitive_factors": competitive_factors,
            "strategic_position": "Technology-forward" if "innovation" in str(goals) else "Cost-conscious"
        }
    
    def _categorize_alignment(self, score: float) -> str:
        """Categorize alignment score."""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _identify_strategic_gaps(self, assessment_data: Dict[str, Any]) -> List[str]:
        """Identify strategic gaps."""
        gaps = []
        
        business_req = assessment_data.get("business_requirements", {})
        
        if not business_req.get("primary_goals"):
            gaps.append("Unclear business objectives")
        
        if not business_req.get("success_metrics"):
            gaps.append("Missing success metrics")
        
        if not business_req.get("timeline"):
            gaps.append("Undefined project timeline")
        
        return gaps
    
    def _generate_alignment_recommendations(self, score: float) -> List[str]:
        """Generate alignment recommendations."""
        if score < 0.5:
            return [
                "Conduct strategic alignment workshop",
                "Define clear business objectives",
                "Establish measurable success criteria"
            ]
        elif score < 0.7:
            return [
                "Refine infrastructure priorities",
                "Improve stakeholder communication",
                "Validate business case assumptions"
            ]
        else:
            return [
                "Maintain current strategic direction",
                "Monitor alignment metrics regularly",
                "Communicate success to stakeholders"
            ]
    
    def _parse_budget_range(self, budget_range: str) -> tuple[float, float]:
        """Parse budget range string to numeric values."""
        budget_mapping = {
            "$1k-10k": (1000, 10000),
            "$10k-50k": (10000, 50000),
            "$50k-100k": (50000, 100000),
            "$100k+": (100000, 500000)
        }
        return budget_mapping.get(budget_range, (10000, 50000))
    
    def _get_scaling_factor(self, company_size: str) -> float:
        """Get scaling factor based on company size."""
        scaling_factors = {
            "startup": 1.5,
            "small": 1.3,
            "medium": 1.2,
            "large": 1.1,
            "enterprise": 1.0
        }
        return scaling_factors.get(company_size, 1.2)
    
    def _estimate_annual_savings(self, company_size: str, expected_users: int) -> float:
        """Estimate annual savings from infrastructure optimization."""
        base_savings = {
            "startup": 5000,
            "small": 15000,
            "medium": 50000,
            "large": 150000,
            "enterprise": 500000
        }
        
        base = base_savings.get(company_size, 15000)
        user_factor = max(1.0, expected_users / 1000)
        
        return base * user_factor
    
    def _calculate_financial_metrics(self, budget_min: float, budget_max: float, expected_users: int) -> Dict[str, Any]:
        """Calculate additional financial metrics."""
        avg_budget = (budget_min + budget_max) / 2
        cost_per_user = avg_budget / max(expected_users, 1)
        
        return {
            "average_budget": avg_budget,
            "cost_per_user": round(cost_per_user, 2),
            "budget_efficiency": "high" if cost_per_user < 50 else "medium" if cost_per_user < 100 else "low"
        }
    
    def _prioritize_investments(self, assessment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize infrastructure investments."""
        priorities = [
            {
                "category": "Core Infrastructure",
                "priority": 1,
                "description": "Essential compute, storage, and networking",
                "rationale": "Foundation for all other services"
            },
            {
                "category": "Security & Compliance",
                "priority": 2,
                "description": "Security controls and compliance measures",
                "rationale": "Risk mitigation and regulatory requirements"
            },
            {
                "category": "Monitoring & Observability",
                "priority": 3,
                "description": "System monitoring and performance tracking",
                "rationale": "Operational visibility and optimization"
            },
            {
                "category": "Scalability Features",
                "priority": 4,
                "description": "Auto-scaling and load balancing",
                "rationale": "Support for growth and traffic spikes"
            }
        ]
        
        return priorities
    
    def _create_risk_matrix(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create risk assessment matrix."""
        matrix = {
            "high_impact_high_prob": [],
            "high_impact_low_prob": [],
            "low_impact_high_prob": [],
            "low_impact_low_prob": []
        }
        
        for risk in risks:
            impact = risk.get("impact", "medium")
            probability = risk.get("probability", "medium")
            
            if impact == "high" and probability in ["high", "medium"]:
                matrix["high_impact_high_prob"].append(risk["risk"])
            elif impact == "high" and probability == "low":
                matrix["high_impact_low_prob"].append(risk["risk"])
            elif impact in ["medium", "low"] and probability in ["high", "medium"]:
                matrix["low_impact_high_prob"].append(risk["risk"])
            else:
                matrix["low_impact_low_prob"].append(risk["risk"])
        
        return matrix
    
    def _prioritize_risk_mitigation(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Prioritize risk mitigation efforts."""
        # Sort risks by impact and probability
        high_priority = [r for r in risks if r.get("impact") == "high"]
        medium_priority = [r for r in risks if r.get("impact") == "medium"]
        
        priorities = []
        for risk in high_priority[:3]:  # Top 3 high-impact risks
            priorities.append(f"Address {risk['risk']}: {risk['mitigation']}")
        
        for risk in medium_priority[:2]:  # Top 2 medium-impact risks
            priorities.append(f"Monitor {risk['risk']}: {risk['mitigation']}")
        
        return priorities
    
    def _calculate_overall_risk_level(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level."""
        high_risks = len([r for r in risks if r.get("impact") == "high"])
        total_risks = len(risks)
        
        if high_risks >= 3:
            return "High"
        elif high_risks >= 1 or total_risks >= 5:
            return "Medium"
        else:
            return "Low"