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
    
    async def analyze_requirements(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze business requirements from a CTO perspective.
        
        Args:
            workflow_data: Dictionary containing assessment data and business requirements
            
        Returns:
            Dictionary containing CTO analysis results
        """
        try:
            business_requirements = workflow_data.get("business_requirements", {})
            
            # Perform strategic analysis
            analysis = {
                "strategic_alignment": self._assess_strategic_fit(business_requirements),
                "financial_impact": self._estimate_financial_impact(business_requirements),
                "risk_assessment": self._assess_business_risks_simple(business_requirements),
                "recommendations": self._generate_cto_recommendations(business_requirements)
            }
            
            return {
                "status": "completed",
                "analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"CTO requirements analysis failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _assess_strategic_fit(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess strategic fit of requirements."""
        industry = requirements.get("industry", "unknown")
        company_size = requirements.get("company_size", "unknown")
        
        return {
            "industry_alignment": "high" if industry in ["technology", "finance", "healthcare"] else "medium",
            "size_appropriateness": "high" if company_size in ["medium", "large"] else "medium",
            "strategic_score": 85
        }
    
    def _estimate_financial_impact(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate financial impact."""
        return {
            "estimated_roi": "150-200%",
            "payback_period": "12-18 months",
            "cost_savings": "$50,000-$100,000 annually"
        }
    
    def _assess_business_risks_simple(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business risks."""
        return {
            "overall_risk": "medium",
            "key_risks": ["implementation_complexity", "change_management", "integration_challenges"],
            "mitigation_strategies": ["phased_rollout", "training_programs", "pilot_testing"]
        }
    
    def _generate_cto_recommendations(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate CTO-level recommendations."""
        return [
            "Prioritize cloud-native architecture for scalability",
            "Implement robust monitoring and observability",
            "Focus on security and compliance from day one",
            "Plan for gradual migration to minimize business disruption"
        ]
    
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
        """Analyze business context using real LLM analysis."""
        logger.debug("Analyzing business context with LLM")
        
        # Prepare assessment data for LLM analysis
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        prompt = f"""As a CTO, analyze the following business context and infrastructure requirements:

BUSINESS REQUIREMENTS:
{self._format_requirements_for_llm(business_req)}

TECHNICAL REQUIREMENTS:
{self._format_requirements_for_llm(technical_req)}

Please provide a comprehensive business context analysis including:

1. **Company Profile Analysis**:
   - Industry classification and business model
   - Company size and maturity assessment
   - Market position and competitive landscape
   - Business model implications for infrastructure

2. **Business Drivers Identification**:
   - Primary business objectives and KPIs
   - Revenue drivers and cost centers
   - Strategic initiatives and priorities
   - Technology enablement requirements

3. **Current Challenges Assessment**:
   - Operational pain points and bottlenecks
   - Technology debt and limitations
   - Resource constraints and capability gaps
   - Market pressures and competitive threats

4. **Growth Trajectory Analysis**:
   - Growth rate and scaling projections
   - Market expansion plans
   - Technology scaling requirements
   - Infrastructure capacity planning needs

5. **Competitive Position**:
   - Technology differentiation opportunities
   - Industry benchmarking insights
   - Strategic technology investments
   - Innovation priorities

Provide actionable insights that will inform infrastructure investment decisions and strategic planning.

Respond in JSON format with structured analysis for each section."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an experienced CTO with deep knowledge of business strategy, technology investments, and infrastructure planning. Provide strategic, business-focused analysis that connects technology decisions to business outcomes.",
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse LLM response
            import json
            try:
                business_context = json.loads(response)
                
                # Add fallback data and validation
                if not isinstance(business_context, dict):
                    business_context = self._parse_business_context_text(response)
                
                # Enhance with additional computed insights
                business_context.update({
                    "company_profile": self._extract_company_profile(assessment_data),
                    "llm_powered": True,
                    "analysis_confidence": 0.85
                })
                
                return business_context
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response, using text parsing")
                return self._parse_business_context_text(response)
                
        except Exception as e:
            logger.error(f"LLM business context analysis failed: {e}")
            # Fallback to original logic
            return await self._fallback_business_context_analysis(assessment_data)
    
    def _format_requirements_for_llm(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for LLM prompt."""
        if not requirements:
            return "No specific requirements provided"
        
        formatted = []
        for key, value in requirements.items():
            if isinstance(value, dict):
                formatted.append(f"  {key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"    - {sub_key.replace('_', ' ').title()}: {sub_value}")
            elif isinstance(value, list):
                formatted.append(f"  {key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
            else:
                formatted.append(f"  {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted)
    
    def _parse_business_context_text(self, response: str) -> Dict[str, Any]:
        """Parse business context from text response when JSON parsing fails."""
        logger.debug("Parsing business context from text response")
        
        # Extract key sections from text response
        business_context = {
            "company_profile": {
                "analysis_source": "text_parsing",
                "key_insights": self._extract_insights_from_text(response, "company")
            },
            "business_drivers": self._extract_insights_from_text(response, "drivers"),
            "current_challenges": self._extract_insights_from_text(response, "challenges"),
            "growth_trajectory": {
                "analysis": self._extract_insights_from_text(response, "growth"),
                "growth_rate": "moderate"  # Default
            },
            "competitive_position": {
                "analysis": self._extract_insights_from_text(response, "competitive"),
                "strategic_position": "developing"
            },
            "llm_powered": True,
            "analysis_confidence": 0.7
        }
        
        return business_context
    
    def _extract_insights_from_text(self, text: str, keyword: str) -> List[str]:
        """Extract insights from text based on keyword."""
        insights = []
        lines = text.split('\n')
        
        # Simple keyword-based extraction
        for line in lines:
            if keyword.lower() in line.lower() and len(line.strip()) > 10:
                # Clean up the line and add as insight
                clean_line = line.strip('- *').strip()
                if clean_line and len(clean_line) > 20:
                    insights.append(clean_line)
        
        # Fallback if no insights found
        if not insights:
            insights.append(f"Analysis indicates {keyword}-related considerations require further evaluation")
        
        return insights[:3]  # Limit to 3 insights
    
    async def _fallback_business_context_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback business context analysis when LLM fails."""
        logger.info("Using fallback business context analysis")
        
        return {
            "company_profile": self._extract_company_profile(assessment_data),
            "business_drivers": self._identify_business_drivers(assessment_data),
            "current_challenges": self._identify_current_challenges(assessment_data),
            "growth_trajectory": self._assess_growth_trajectory(assessment_data),
            "competitive_position": self._assess_competitive_position(assessment_data),
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
    
    async def _assess_strategic_alignment(self) -> Dict[str, Any]:
        """Assess strategic alignment using real LLM analysis."""
        logger.debug("Assessing strategic alignment with LLM")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        prompt = f"""As a CTO, assess the strategic alignment between business goals and infrastructure requirements:

BUSINESS REQUIREMENTS:
{self._format_requirements_for_llm(business_req)}

TECHNICAL REQUIREMENTS:
{self._format_requirements_for_llm(technical_req)}

Provide a strategic alignment analysis including:

1. **Alignment Score Assessment** (0.0 to 1.0):
   - How well do technical requirements support business goals?
   - Are infrastructure investments aligned with business priorities?
   - Does the technology strategy support business strategy?

2. **Strategic Alignment Factors**:
   - Key areas where business and technical requirements align
   - Technology choices that support business objectives
   - Infrastructure capabilities that enable business growth

3. **Strategic Gaps Analysis**:
   - Misalignments between business goals and technical approach
   - Missing strategic considerations
   - Areas requiring better alignment

4. **Alignment Recommendations**:
   - Actions to improve strategic alignment
   - Technology decisions that better support business goals
   - Process improvements for ongoing alignment

Respond in JSON format with structured analysis for each section."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an experienced CTO skilled in aligning technology strategy with business strategy. Provide analytical, strategic assessments that help organizations optimize their infrastructure investments for business success.",
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parse LLM response
            import json
            try:
                alignment_result = json.loads(response)
                
                # Validate and enhance the result
                if not isinstance(alignment_result, dict):
                    alignment_result = self._parse_alignment_text(response)
                
                # Add computed metrics
                alignment_result.update({
                    "llm_powered": True,
                    "analysis_confidence": 0.85
                })
                
                return alignment_result
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response for strategic alignment")
                return self._parse_alignment_text(response)
                
        except Exception as e:
            logger.error(f"LLM strategic alignment analysis failed: {e}")
            return await self._fallback_strategic_alignment(assessment_data)
    
    def _parse_alignment_text(self, response: str) -> Dict[str, Any]:
        """Parse strategic alignment from text response."""
        # Extract alignment score from text
        alignment_score = 0.7  # Default
        
        # Simple score extraction
        import re
        score_match = re.search(r'(\d+\.\d+|\d+)(?:/10|%|\s*out of)', response.lower())
        if score_match:
            try:
                extracted_score = float(score_match.group(1))
                if extracted_score > 1.0:
                    extracted_score = extracted_score / 10  # Convert if out of 10
                alignment_score = min(extracted_score, 1.0)
            except ValueError:
                pass
        
        return {
            "alignment_score": alignment_score,
            "alignment_level": self._categorize_alignment(alignment_score),
            "alignment_factors": self._extract_insights_from_text(response, "align"),
            "strategic_gaps": self._extract_insights_from_text(response, "gap"),
            "recommendations": self._extract_insights_from_text(response, "recommend"),
            "llm_powered": True,
            "analysis_confidence": 0.75
        }
    
    async def _fallback_strategic_alignment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategic alignment analysis."""
        logger.info("Using fallback strategic alignment analysis")
        
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
            "recommendations": self._generate_alignment_recommendations(alignment_score),
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
    
    async def _perform_financial_analysis(self) -> Dict[str, Any]:
        """Perform ROI calculations and financial projections using real LLM analysis."""
        logger.debug("Performing financial analysis with LLM")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Extract financial parameters for LLM context
        budget_range = business_req.get("budget_range", "$10k-50k")
        company_size = business_req.get("company_size", "startup")
        expected_users = technical_req.get("expected_users", 1000)
        
        prompt = f"""As a CTO, perform a comprehensive financial analysis for this infrastructure investment:

BUSINESS CONTEXT:
{self._format_requirements_for_llm(business_req)}

TECHNICAL CONTEXT:
{self._format_requirements_for_llm(technical_req)}

KEY PARAMETERS:
- Budget Range: {budget_range}
- Company Size: {company_size}
- Expected Users: {expected_users:,}

Provide a detailed financial analysis including:

1. **Budget Analysis**:
   - Budget range assessment and recommendations
   - Cost breakdown by infrastructure components
   - Budget optimization opportunities

2. **ROI Calculations**:
   - Expected return on investment percentage
   - Payback period in months
   - Cost savings projections (annual and 3-year)
   - Business value metrics

3. **Cost Projections**:
   - Monthly operational costs by category
   - Annual cost trends and scaling projections
   - Hidden costs and risk factors

4. **Financial Metrics**:
   - Total cost of ownership (TCO) analysis
   - Cost per user/transaction efficiency
   - Budget utilization and optimization score

5. **Investment Priorities**:
   - Ranked list of infrastructure investments by business impact
   - Quick wins vs. strategic investments
   - Risk-adjusted investment recommendations

Use realistic industry benchmarks and provide specific numbers where possible.
Respond in JSON format with structured analysis for each section."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a financial-savvy CTO with extensive experience in infrastructure investments, ROI calculations, and budget optimization. Provide realistic, data-driven financial analysis that helps organizations make informed infrastructure investment decisions.",
                temperature=0.1,  # Lower temperature for financial accuracy
                max_tokens=2000
            )
            
            # Parse LLM response
            import json
            try:
                financial_result = json.loads(response)
                
                # Validate and enhance the result
                if not isinstance(financial_result, dict):
                    financial_result = self._parse_financial_text(response)
                
                # Add computed metrics and validation
                budget_min, budget_max = self._parse_budget_range(budget_range)
                financial_result.update({
                    "budget_validation": {
                        "min_budget": budget_min,
                        "max_budget": budget_max,
                        "recommended_budget": (budget_min + budget_max) / 2
                    },
                    "financial_metrics": self._calculate_financial_metrics(budget_min, budget_max, expected_users),
                    "llm_powered": True,
                    "analysis_confidence": 0.9
                })
                
                return financial_result
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response for financial analysis")
                return self._parse_financial_text(response)
                
        except Exception as e:
            logger.error(f"LLM financial analysis failed: {e}")
            return await self._fallback_financial_analysis(assessment_data)
    
    def _parse_financial_text(self, response: str) -> Dict[str, Any]:
        """Parse financial analysis from text response."""
        # Extract key financial metrics from text
        import re
        
        # Extract ROI percentage
        roi_percentage = 150  # Default
        roi_match = re.search(r'roi.*?(\d+(?:\.\d+)?)%', response.lower())
        if roi_match:
            try:
                roi_percentage = float(roi_match.group(1))
            except ValueError:
                pass
        
        # Extract payback period
        payback_months = 18  # Default
        payback_match = re.search(r'payback.*?(\d+).*?months?', response.lower())
        if payback_match:
            try:
                payback_months = int(payback_match.group(1))
            except ValueError:
                pass
        
        return {
            "budget_analysis": {
                "analysis": self._extract_insights_from_text(response, "budget"),
                "optimization_opportunities": self._extract_insights_from_text(response, "optimization")
            },
            "roi_analysis": {
                "roi_percentage": roi_percentage,
                "payback_period_months": payback_months,
                "annual_savings": roi_percentage * 1000,  # Rough estimate
                "business_value": self._extract_insights_from_text(response, "value")
            },
            "cost_projections": {
                "monthly_costs": self._extract_insights_from_text(response, "monthly"),
                "annual_trends": self._extract_insights_from_text(response, "annual")
            },
            "investment_priorities": self._extract_insights_from_text(response, "priority"),
            "llm_powered": True,
            "analysis_confidence": 0.75
        }
    
    async def _fallback_financial_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback financial analysis when LLM fails."""
        logger.info("Using fallback financial analysis")
        
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
            "investment_priorities": self._prioritize_investments(assessment_data),
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
        
        return financial_analysis
    
    async def _assess_business_risks(self) -> Dict[str, Any]:
        """Assess business risks using real LLM analysis."""
        logger.debug("Assessing business risks with LLM")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        compliance_req = assessment_data.get("compliance_requirements", {})
        
        prompt = f"""As a CTO, perform a comprehensive business risk assessment for this infrastructure project:

BUSINESS REQUIREMENTS:
{self._format_requirements_for_llm(business_req)}

TECHNICAL REQUIREMENTS:
{self._format_requirements_for_llm(technical_req)}

COMPLIANCE REQUIREMENTS:
{self._format_requirements_for_llm(compliance_req)}

Identify and analyze business risks across multiple categories:

1. **Technology Risks**:
   - Technical complexity and implementation challenges
   - Technology obsolescence and vendor dependencies
   - Integration risks with existing systems
   - Performance and scalability risks

2. **Financial Risks**:
   - Budget overruns and cost escalation
   - ROI realization risks
   - Hidden costs and unexpected expenses
   - Currency and pricing model risks

3. **Operational Risks**:
   - Service availability and reliability
   - Data loss and business continuity
   - Skills gaps and resource constraints
   - Change management and adoption risks

4. **Strategic Risks**:
   - Vendor lock-in and flexibility constraints
   - Market timing and competitive risks
   - Regulatory and compliance risks
   - Business model alignment risks

5. **Security and Compliance Risks**:
   - Data security and privacy breaches
   - Regulatory compliance failures
   - Access control and governance risks
   - Audit and monitoring gaps

For each risk, provide:
- Risk name and category
- Impact level (high/medium/low)
- Probability (high/medium/low)
- Detailed description
- Specific mitigation strategies
- Timeline for mitigation

Respond in JSON format with structured risk assessment."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an experienced CTO with deep expertise in risk management, infrastructure projects, and business continuity. Provide comprehensive, actionable risk assessments that help organizations proactively manage infrastructure project risks.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Parse LLM response
            import json
            try:
                risk_result = json.loads(response)
                
                # Validate and enhance the result
                if not isinstance(risk_result, dict):
                    risk_result = self._parse_risk_text(response)
                
                # Add computed analysis
                risks = risk_result.get("identified_risks", [])
                risk_result.update({
                    "risk_matrix": self._create_risk_matrix(risks),
                    "mitigation_priorities": self._prioritize_risk_mitigation(risks),
                    "overall_risk_level": self._calculate_overall_risk_level(risks),
                    "llm_powered": True,
                    "analysis_confidence": 0.85
                })
                
                return risk_result
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response for business risks")
                return self._parse_risk_text(response)
                
        except Exception as e:
            logger.error(f"LLM business risk analysis failed: {e}")
            return await self._fallback_business_risks(assessment_data)
    
    def _parse_risk_text(self, response: str) -> Dict[str, Any]:
        """Parse business risks from text response."""
        # Extract risks from text
        risks = []
        
        # Simple text parsing to extract risk information
        lines = response.split('\n')
        current_risk = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_risk:
                    risks.append(current_risk)
                    current_risk = {}
                continue
            
            # Try to extract risk components
            if 'risk' in line.lower() and len(line) > 20:
                current_risk = {
                    "category": "general",
                    "risk": line.strip('- *'),
                    "impact": "medium",
                    "probability": "medium",
                    "description": line,
                    "mitigation": "Implement appropriate controls and monitoring"
                }
        
        # Add final risk if exists
        if current_risk:
            risks.append(current_risk)
        
        # If no risks extracted, add generic ones
        if not risks:
            risks = [
                {
                    "category": "technology",
                    "risk": "Implementation Complexity",
                    "impact": "medium",
                    "probability": "medium",
                    "description": "Technical implementation may face unexpected challenges",
                    "mitigation": "Implement phased approach with regular checkpoints"
                },
                {
                    "category": "financial",
                    "risk": "Budget Management",
                    "impact": "medium",
                    "probability": "medium",
                    "description": "Project costs may exceed initial estimates",
                    "mitigation": "Implement cost monitoring and regular budget reviews"
                }
            ]
        
        return {
            "identified_risks": risks[:8],  # Limit to 8 risks
            "llm_powered": True,
            "analysis_confidence": 0.7
        }
    
    async def _fallback_business_risks(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback business risk analysis when LLM fails."""
        logger.info("Using fallback business risk analysis")
        
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
            "overall_risk_level": self._calculate_overall_risk_level(risks),
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
    
    async def _generate_strategic_recommendations(self, business_analysis: Dict[str, Any], 
                                                strategic_alignment: Dict[str, Any],
                                                financial_analysis: Dict[str, Any],
                                                risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations using real LLM analysis."""
        logger.debug("Generating strategic recommendations with LLM")
        
        # Prepare comprehensive context for LLM
        context_summary = {
            "business_insights": business_analysis.get("company_profile", {}),
            "alignment_score": strategic_alignment.get("alignment_score", 0.0),
            "financial_projections": financial_analysis.get("roi_analysis", {}),
            "identified_risks": len(risk_assessment.get("identified_risks", [])),
            "high_impact_risks": len([r for r in risk_assessment.get("identified_risks", []) if r.get("impact") == "high"])
        }
        
        prompt = f"""As a CTO, synthesize the following analysis into strategic recommendations for infrastructure investment:

BUSINESS ANALYSIS SUMMARY:
{self._format_requirements_for_llm(business_analysis)}

STRATEGIC ALIGNMENT:
- Alignment Score: {strategic_alignment.get('alignment_score', 0.0):.2f}/1.0
- Alignment Level: {strategic_alignment.get('alignment_level', 'Unknown')}
- Key Gaps: {', '.join(strategic_alignment.get('strategic_gaps', []))}

FINANCIAL ANALYSIS:
{self._format_requirements_for_llm(financial_analysis)}

RISK ASSESSMENT:
- Total Risks Identified: {len(risk_assessment.get('identified_risks', []))}
- High-Impact Risks: {len([r for r in risk_assessment.get('identified_risks', []) if r.get('impact') == 'high'])}
- Overall Risk Level: {risk_assessment.get('overall_risk_level', 'Medium')}

Generate strategic recommendations that address:

1. **Strategic Alignment Improvements**:
   - Actions to better align technology with business goals
   - Process improvements for ongoing alignment
   - Stakeholder engagement strategies

2. **Financial Optimization**:
   - ROI enhancement opportunities
   - Cost optimization strategies
   - Budget allocation recommendations

3. **Risk Mitigation**:
   - High-priority risk mitigation actions
   - Risk monitoring and governance
   - Contingency planning

4. **Technology Strategy**:
   - Architecture and technology choices
   - Vendor selection and management
   - Skills and capability development

5. **Implementation Roadmap**:
   - Phased implementation approach
   - Quick wins vs. strategic investments
   - Success metrics and monitoring

For each recommendation, provide:
- Category and priority (high/medium/low)
- Title and description
- Rationale and business case
- Specific action items
- Business impact
- Timeline
- Investment level required

Respond in JSON format with an array of strategic recommendations."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a strategic CTO consultant with extensive experience in infrastructure strategy, business alignment, and executive decision-making. Provide actionable, business-focused recommendations that drive organizational success through technology investments.",
                temperature=0.3,
                max_tokens=2500
            )
            
            # Parse LLM response
            import json
            try:
                recommendations_result = json.loads(response)
                
                # Validate and enhance the result
                if isinstance(recommendations_result, dict) and "recommendations" in recommendations_result:
                    recommendations = recommendations_result["recommendations"]
                elif isinstance(recommendations_result, list):
                    recommendations = recommendations_result
                else:
                    recommendations = self._parse_recommendations_text(response)
                
                # Ensure each recommendation has required fields
                enhanced_recommendations = []
                for rec in recommendations:
                    if isinstance(rec, dict):
                        enhanced_rec = {
                            "category": rec.get("category", "general"),
                            "priority": rec.get("priority", "medium"),
                            "title": rec.get("title", "Strategic Recommendation"),
                            "description": rec.get("description", ""),
                            "rationale": rec.get("rationale", "Based on comprehensive analysis"),
                            "actions": rec.get("actions", ["Review and implement"]),
                            "business_impact": rec.get("business_impact", "Positive impact on business operations"),
                            "timeline": rec.get("timeline", "3-6 months"),
                            "investment_required": rec.get("investment_required", "Medium"),
                            "llm_generated": True
                        }
                        enhanced_recommendations.append(enhanced_rec)
                
                return enhanced_recommendations[:6]  # Limit to 6 recommendations
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response for strategic recommendations")
                return self._parse_recommendations_text(response)
                
        except Exception as e:
            logger.error(f"LLM strategic recommendations generation failed: {e}")
            return await self._fallback_strategic_recommendations(business_analysis, strategic_alignment, financial_analysis, risk_assessment)
    
    def _parse_recommendations_text(self, response: str) -> List[Dict[str, Any]]:
        """Parse strategic recommendations from text response."""
        recommendations = []
        
        # Split response into sections
        sections = response.split('\n\n')
        
        for section in sections:
            if len(section.strip()) > 50:  # Meaningful content
                # Extract recommendation from section
                lines = section.split('\n')
                title = lines[0].strip('# -*').strip() if lines else "Strategic Recommendation"
                
                description = ""
                for line in lines[1:]:
                    if len(line.strip()) > 10:
                        description = line.strip()
                        break
                
                recommendation = {
                    "category": "strategic",
                    "priority": "medium",
                    "title": title[:100],  # Limit title length
                    "description": description[:500],  # Limit description length
                    "rationale": "Based on comprehensive analysis",
                    "actions": [
                        "Review current approach",
                        "Implement recommended changes",
                        "Monitor progress and outcomes"
                    ],
                    "business_impact": "Improves strategic alignment and operational efficiency",
                    "timeline": "3-6 months",
                    "investment_required": "Medium",
                    "llm_generated": True
                }
                recommendations.append(recommendation)
        
        # Ensure we have at least 3 recommendations
        while len(recommendations) < 3:
            recommendations.append({
                "category": "general",
                "priority": "medium",
                "title": f"Strategic Initiative {len(recommendations) + 1}",
                "description": "Additional strategic recommendation based on analysis",
                "rationale": "Supports overall infrastructure strategy",
                "actions": ["Evaluate options", "Plan implementation", "Execute strategy"],
                "business_impact": "Contributes to business objectives",
                "timeline": "3-6 months",
                "investment_required": "Medium",
                "llm_generated": True
            })
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    async def _fallback_strategic_recommendations(self, business_analysis: Dict[str, Any], 
                                                strategic_alignment: Dict[str, Any],
                                                financial_analysis: Dict[str, Any],
                                                risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback strategic recommendations when LLM fails."""
        logger.info("Using fallback strategic recommendations")
        
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