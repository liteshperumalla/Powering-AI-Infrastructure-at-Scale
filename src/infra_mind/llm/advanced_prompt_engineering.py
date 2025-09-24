"""
Advanced Prompt Engineering Framework for Professional-Grade Infrastructure Reports.

This module implements sophisticated prompt engineering techniques to maximize
agent performance and generate enterprise-quality reports with advanced features.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)


class PromptTemplate(str, Enum):
    """Advanced prompt template categories."""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    COST_ANALYSIS = "cost_analysis"
    COMPLIANCE_MAPPING = "compliance_mapping"
    RISK_ASSESSMENT = "risk_assessment"
    ROADMAP_PLANNING = "roadmap_planning"
    STAKEHOLDER_BRIEFING = "stakeholder_briefing"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_METRICS = "performance_metrics"
    PREDICTIVE_MODELING = "predictive_modeling"


@dataclass
class PromptContext:
    """Contextual information for prompt optimization."""
    audience_level: str  # "executive", "technical", "mixed"
    report_type: str
    business_domain: str
    complexity_level: str  # "basic", "intermediate", "advanced", "expert"
    output_format: str  # "narrative", "structured", "dashboard", "presentation"
    time_horizon: str  # "immediate", "quarterly", "annual", "strategic"
    data_sources: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)


class AdvancedPromptEngineer:
    """
    Advanced prompt engineering system for professional infrastructure reports.
    
    Features:
    - Context-aware prompt optimization
    - Multi-agent coordination
    - Dynamic prompt adaptation
    - Professional report formatting
    - Enterprise-grade analysis
    """
    
    def __init__(self):
        """Initialize the advanced prompt engineering system."""
        self.template_library = self._initialize_templates()
        self.prompt_strategies = self._initialize_strategies()
        self.quality_metrics = self._initialize_quality_metrics()
        
        logger.info("Advanced Prompt Engineering system initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize professional-grade prompt templates."""
        return {
            "executive_summary": {
                "system_prompt": """
You are a senior management consultant and infrastructure strategist with 20+ years of experience 
advising Fortune 500 companies on digital transformation and cloud infrastructure.

Your expertise includes:
- Strategic business alignment with technical initiatives  
- ROI optimization and cost-benefit analysis
- Risk assessment and mitigation strategies
- Executive communication and stakeholder management
- Enterprise architecture and scalability planning

Generate executive-level insights that are:
- Strategically aligned with business objectives
- Financially quantified with clear ROI projections
- Risk-aware with mitigation strategies
- Actionable with clear next steps
- Aligned with industry best practices and compliance requirements
""",
                "user_prompt_template": """
Based on the infrastructure assessment data provided, generate a comprehensive executive summary for {company_name} that includes:

1. **STRATEGIC OVERVIEW**
   - Business impact assessment
   - Alignment with organizational goals
   - Competitive advantage analysis
   - Market positioning implications

2. **FINANCIAL ANALYSIS** 
   - Total Cost of Ownership (TCO) projections
   - Return on Investment (ROI) calculations
   - Cost savings opportunities (immediate and projected)
   - Budget allocation recommendations
   - Financial risk assessment

3. **RISK & COMPLIANCE MATRIX**
   - Critical risk factors and probability analysis
   - Regulatory compliance status and requirements
   - Security posture assessment
   - Business continuity considerations
   - Mitigation strategies with timelines

4. **STRATEGIC ROADMAP**
   - Phase-based implementation timeline
   - Resource allocation requirements
   - Success metrics and KPIs
   - Milestone dependencies
   - Change management considerations

5. **EXECUTIVE RECOMMENDATIONS**
   - Top 3 critical actions (next 30 days)
   - Strategic initiatives (6-12 months) 
   - Long-term vision alignment (2-3 years)
   - Investment priorities and rationale

Assessment Data: {assessment_data}
Industry Context: {industry_context}
Compliance Requirements: {compliance_requirements}
Budget Constraints: {budget_constraints}

Format the output as a professional executive briefing document with clear sections, 
quantified metrics, and actionable recommendations suitable for C-level presentation.
"""
            },
            
            "technical_deep_dive": {
                "system_prompt": """
You are a Principal Cloud Architect and Site Reliability Engineer with deep expertise in:
- Enterprise cloud architecture (AWS, Azure, GCP, multi-cloud)
- Infrastructure as Code (Terraform, CloudFormation, Pulumi)
- Container orchestration (Kubernetes, Docker, service mesh)
- DevOps and CI/CD pipeline optimization
- Performance optimization and scalability engineering
- Security architecture and compliance frameworks
- Cost optimization and resource management

Your analysis should be:
- Technically precise with specific implementation details
- Performance-focused with quantifiable metrics
- Security-first with comprehensive threat modeling
- Scalable with consideration for future growth
- Cost-optimized with detailed resource analysis
""",
                "user_prompt_template": """
Conduct a comprehensive technical analysis of the infrastructure assessment for {company_name}:

1. **ARCHITECTURE ANALYSIS**
   - Current state architecture review
   - Performance bottlenecks and optimization opportunities
   - Scalability constraints and recommendations
   - Technology stack evaluation and modernization paths
   - Integration patterns and API design assessment

2. **SECURITY & COMPLIANCE DEEP DIVE**
   - Threat model analysis and attack surface review
   - Zero-trust architecture implementation roadmap
   - Identity and access management (IAM) optimization
   - Data protection and encryption strategies
   - Compliance framework mapping (SOC2, PCI-DSS, HIPAA, GDPR)

3. **PERFORMANCE & RELIABILITY**
   - SLA/SLO analysis and optimization recommendations
   - Disaster recovery and business continuity planning
   - Monitoring, alerting, and observability strategy
   - Capacity planning and auto-scaling configuration
   - Performance benchmarking and optimization

4. **INFRASTRUCTURE AS CODE**
   - Current IaC maturity assessment
   - Terraform/CloudFormation optimization recommendations
   - GitOps implementation strategy
   - Environment consistency and deployment automation
   - Configuration management and drift detection

5. **COST OPTIMIZATION**
   - Resource utilization analysis and rightsizing
   - Reserved instance and savings plan recommendations
   - Multi-cloud cost optimization strategies
   - FinOps implementation roadmap
   - Cost monitoring and governance framework

Assessment Data: {assessment_data}
Current Architecture: {current_architecture}
Performance Metrics: {performance_metrics}
Security Requirements: {security_requirements}

Generate a detailed technical report with specific implementation steps, 
code examples, configuration templates, and quantified performance improvements.
"""
            },
            
            "roadmap_planning": {
                "system_prompt": """
You are a Strategic Technology Planning Expert and Digital Transformation Leader with expertise in:
- Enterprise transformation roadmap development
- Technology portfolio management
- Strategic investment planning and prioritization
- Change management and organizational readiness
- Industry trend analysis and competitive intelligence
- Stakeholder alignment and communication strategies

Your roadmaps should be:
- Strategically aligned with business objectives
- Phased with clear dependencies and milestones
- Resource-optimized with realistic timelines
- Risk-aware with contingency planning
- Measurable with clear success criteria
""",
                "user_prompt_template": """
Develop a comprehensive strategic technology roadmap for {company_name} based on the assessment:

1. **STRATEGIC VISION & OBJECTIVES**
   - 3-year technology vision statement
   - Strategic business objectives alignment
   - Market positioning and competitive advantage goals
   - Innovation and transformation targets

2. **ROADMAP PHASES**
   Phase 1 (0-6 months) - Foundation & Quick Wins:
   - Critical infrastructure improvements
   - Low-hanging fruit optimizations
   - Risk mitigation priorities
   - Team skill development

   Phase 2 (6-18 months) - Transformation Core:
   - Major system modernizations
   - Process automation implementation
   - Advanced capability development
   - Integration and optimization

   Phase 3 (18-36 months) - Innovation & Scale:
   - Advanced technologies adoption
   - Strategic capability expansion
   - Market leadership positioning
   - Continuous innovation framework

3. **INVESTMENT PRIORITIZATION**
   - ROI-based project ranking and scoring
   - Resource allocation recommendations
   - Budget planning and cash flow analysis
   - Risk-adjusted investment strategies

4. **ORGANIZATIONAL READINESS**
   - Skills gap analysis and training requirements
   - Change management strategy
   - Organizational structure recommendations
   - Culture transformation initiatives

5. **SUCCESS METRICS & GOVERNANCE**
   - KPI framework and measurement strategy
   - Governance structure and decision rights
   - Progress tracking and reporting mechanisms
   - Risk monitoring and mitigation protocols

Assessment Data: {assessment_data}
Business Objectives: {business_objectives}
Industry Trends: {industry_trends}
Competitive Landscape: {competitive_landscape}

Create a detailed, executive-ready strategic roadmap with clear phases, 
timelines, resource requirements, and measurable success criteria.
"""
            },
            
            "strategic_roadmap": {
                "system_prompt": """
You are a Strategic Technology Planning Expert and Digital Transformation Leader with expertise in:
- Enterprise transformation roadmap development
- Technology portfolio management
- Strategic investment planning and prioritization
- Change management and organizational readiness
- Industry trend analysis and competitive intelligence
- Stakeholder alignment and communication strategies

Your roadmaps should be:
- Strategically aligned with business objectives
- Phased with clear dependencies and milestones
- Resource-optimized with realistic timelines
- Risk-aware with contingency planning
- Measurable with clear success criteria
""",
                "user_prompt_template": """
Develop a comprehensive strategic technology roadmap for {company_name} based on the assessment:

1. **STRATEGIC VISION & OBJECTIVES**
   - 3-year technology vision statement
   - Strategic business objectives alignment
   - Market positioning and competitive advantage goals
   - Innovation and transformation targets

2. **ROADMAP PHASES**
   Phase 1 (0-6 months) - Foundation & Quick Wins:
   - Critical infrastructure improvements
   - Low-hanging fruit optimizations
   - Risk mitigation priorities
   - Team skill development

   Phase 2 (6-18 months) - Transformation Core:
   - Major system modernizations
   - Process automation implementation
   - Advanced capability development
   - Integration and optimization

   Phase 3 (18-36 months) - Innovation & Scale:
   - Advanced technologies adoption
   - Strategic capability expansion
   - Market leadership positioning
   - Continuous innovation framework

3. **INVESTMENT PRIORITIZATION**
   - ROI-based project ranking and scoring
   - Resource allocation recommendations
   - Budget planning and cash flow analysis
   - Risk-adjusted investment strategies

4. **ORGANIZATIONAL READINESS**
   - Skills gap analysis and training requirements
   - Change management strategy
   - Organizational structure recommendations
   - Culture transformation initiatives

5. **SUCCESS METRICS & GOVERNANCE**
   - KPI framework and measurement strategy
   - Governance structure and decision rights
   - Progress tracking and reporting mechanisms
   - Risk monitoring and mitigation protocols

Assessment Data: {assessment_data}
Business Objectives: {business_objectives}
Industry Trends: {industry_trends}
Competitive Landscape: {competitive_landscape}

Create a detailed, executive-ready strategic roadmap with clear phases, 
timelines, resource requirements, and measurable success criteria.
"""
            },
            
            "cost_analysis": {
                "system_prompt": """
You are a Senior Financial Analyst and FinOps Expert specializing in cloud infrastructure cost optimization.

Your expertise includes:
- Total Cost of Ownership (TCO) analysis and modeling
- Cloud cost optimization strategies and implementation
- Financial planning and budget forecasting for technology initiatives
- ROI calculations and business case development
- Multi-cloud cost management and optimization
- FinOps best practices and governance frameworks

Generate cost analyses that are:
- Financially accurate with detailed cost breakdowns
- Forward-looking with predictive modeling
- Optimization-focused with actionable recommendations
- Risk-aware with scenario analysis
- Aligned with business objectives and budget constraints
""",
                "user_prompt_template": """
Generate a comprehensive cost analysis for the infrastructure transformation:

1. **CURRENT STATE COST ANALYSIS**
   - Existing infrastructure costs (detailed breakdown)
   - Hidden costs and inefficiencies
   - Cost trends and growth patterns
   - Benchmark against industry standards

2. **FUTURE STATE COST PROJECTIONS**
   - Year 1-3 cost projections with confidence intervals
   - Implementation costs and one-time investments
   - Operational cost changes and ongoing expenses
   - Total Cost of Ownership (TCO) calculations

3. **COST OPTIMIZATION OPPORTUNITIES**
   - Resource rightsizing recommendations
   - Reserved instance and savings plan strategies
   - Automation-driven cost reductions
   - Process optimization savings

4. **ROI ANALYSIS & BUSINESS CASE**
   - Return on Investment calculations
   - Payback period analysis
   - Net Present Value (NPV) assessments
   - Risk-adjusted financial metrics

5. **BUDGET PLANNING & GOVERNANCE**
   - Budget allocation recommendations
   - Cost governance framework
   - Monitoring and alerting strategies
   - FinOps implementation roadmap

Cost Data: {cost_data}
Assessment Data: {assessment_data}

Provide detailed financial analysis with specific dollar amounts, percentages, 
and clear recommendations for cost optimization and budget planning.
"""
            },
            
            "compliance_mapping": {
                "system_prompt": """
You are a Compliance and Risk Management Expert with deep expertise in:
- Regulatory frameworks (SOC 2, ISO 27001, PCI DSS, HIPAA, GDPR, FedRAMP)
- Risk assessment and compliance gap analysis
- Control implementation and audit preparation
- Governance, Risk, and Compliance (GRC) strategy
- Security compliance and regulatory alignment
- Compliance automation and continuous monitoring

Your compliance analyses should be:
- Framework-specific with detailed control mappings
- Risk-based with prioritized remediation plans
- Implementation-focused with clear action items
- Audit-ready with proper documentation
- Cost-effective with optimized compliance strategies
""",
                "user_prompt_template": """
Conduct comprehensive compliance mapping and gap analysis:

1. **COMPLIANCE FRAMEWORK ASSESSMENT**
   - Current compliance posture for {requirements}
   - Control coverage analysis and maturity assessment
   - Gap identification with severity ratings
   - Compliance score calculations and benchmarking

2. **RISK ASSESSMENT & IMPACT ANALYSIS**
   - Regulatory risk exposure and potential penalties
   - Business impact of non-compliance
   - Risk likelihood and severity scoring
   - Prioritized risk mitigation strategies

3. **CONTROL MAPPING & IMPLEMENTATION**
   - Detailed control requirements for each framework
   - Current control implementation status
   - Control effectiveness assessment
   - Technology and process control recommendations

4. **REMEDIATION ROADMAP**
   - Prioritized action plan for gap closure
   - Implementation timeline with milestones
   - Resource requirements and cost estimates
   - Success metrics and validation criteria

5. **CONTINUOUS COMPLIANCE STRATEGY**
   - Ongoing monitoring and assessment processes
   - Automation opportunities for compliance management
   - Regular review and update procedures
   - Audit preparation and documentation strategies

Requirements: {requirements}
Current State: {current_state}
Assessment Data: {assessment_data}

Generate a detailed compliance analysis with specific control mappings, 
gap remediation plans, and implementation roadmaps.
"""
            },
            
            "stakeholder_briefing": {
                "system_prompt": """
You are an Executive Communication Specialist with expertise in:
- Stakeholder-specific communication strategies
- Technical concept translation for business audiences
- Executive presentation and briefing development
- Change management communication
- Cross-functional alignment and messaging
- Business impact articulation and storytelling

Your briefings should be:
- Audience-appropriate with relevant language and depth
- Impact-focused with clear business value propositions
- Action-oriented with specific next steps
- Persuasive with compelling business cases
- Concise with key insights highlighted
""",
                "user_prompt_template": """
Create a targeted stakeholder briefing for {stakeholder_role}:

AUDIENCE: {stakeholder_role} ({audience_level} level)
FOCUS AREA: {stakeholder_focus}

1. **EXECUTIVE SUMMARY**
   - Key findings relevant to {stakeholder_role}
   - Primary impact on {stakeholder_focus}
   - Critical decisions required
   - Recommended immediate actions

2. **BUSINESS IMPACT ANALYSIS**
   - Financial implications and ROI projections
   - Operational efficiency improvements
   - Risk mitigation and compliance benefits
   - Competitive advantage opportunities

3. **STRATEGIC ALIGNMENT**
   - Alignment with organizational objectives
   - Support for {stakeholder_role} priorities
   - Cross-functional collaboration requirements
   - Resource and budget implications

4. **IMPLEMENTATION CONSIDERATIONS**
   - Timeline and milestone overview
   - Resource requirements and dependencies
   - Change management implications
   - Success metrics and KPIs

5. **NEXT STEPS & DECISIONS**
   - Immediate actions for {stakeholder_role}
   - Approval and sign-off requirements
   - Stakeholder coordination needs
   - Follow-up and review schedule

Assessment Data: {assessment_data}
Stakeholder Focus: {stakeholder_focus}
Stakeholder Role: {stakeholder_role}

Generate a concise, impactful briefing tailored specifically to the 
{stakeholder_role}'s responsibilities and decision-making needs.
"""
            }
        }
    
    def _initialize_strategies(self) -> Dict[str, Callable]:
        """Initialize prompt optimization strategies."""
        return {
            "context_injection": self._inject_context,
            "chain_of_thought": self._add_chain_of_thought,
            "role_playing": self._enhance_role_playing,
            "output_structuring": self._structure_output,
            "quality_assurance": self._add_quality_assurance
        }
    
    def _initialize_quality_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality assessment metrics."""
        return {
            "executive_summary": {
                "required_sections": [
                    "strategic_overview", "financial_analysis", "risk_assessment",
                    "roadmap", "recommendations"
                ],
                "quality_indicators": [
                    "quantified_metrics", "actionable_insights", "risk_awareness",
                    "strategic_alignment", "executive_language"
                ],
                "success_criteria": {
                    "clarity_score": 0.85,
                    "completeness_score": 0.90,
                    "actionability_score": 0.80
                }
            },
            "technical_analysis": {
                "required_sections": [
                    "architecture_analysis", "security_assessment", "performance_analysis",
                    "implementation_plan", "cost_optimization"
                ],
                "quality_indicators": [
                    "technical_depth", "specific_recommendations", "implementation_details",
                    "performance_metrics", "security_considerations"
                ],
                "success_criteria": {
                    "technical_accuracy": 0.95,
                    "implementation_readiness": 0.85,
                    "security_coverage": 0.90
                }
            }
        }
    
    def generate_advanced_prompt(
        self,
        template_type: PromptTemplate,
        context: PromptContext,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate an advanced, context-aware prompt.
        
        Args:
            template_type: Type of prompt template to use
            context: Contextual information for optimization
            data: Assessment and business data
            
        Returns:
            Dictionary containing system and user prompts
        """
        try:
            base_template = self.template_library.get(template_type.value, {})
            
            if not base_template:
                logger.error(f"Template not found for type: {template_type}")
                raise ValueError(f"Unsupported template type: {template_type}")
            
            # Apply optimization strategies
            optimized_prompt = self._apply_optimization_strategies(
                base_template, context, data
            )
            
            # Add quality assurance elements
            final_prompt = self._add_quality_assurance(
                optimized_prompt, template_type, context
            )
            
            logger.info(f"Generated advanced prompt for {template_type.value}")
            return final_prompt
            
        except Exception as e:
            logger.error(f"Error generating advanced prompt: {e}")
            raise
    
    def _apply_optimization_strategies(
        self, 
        template: Dict[str, str],
        context: PromptContext,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Apply various optimization strategies to the prompt."""
        optimized = template.copy()
        
        # Context injection
        optimized = self._inject_context(optimized, context, data)
        
        # Chain of thought reasoning
        if context.complexity_level in ["advanced", "expert"]:
            optimized = self._add_chain_of_thought(optimized, context)
        
        # Role-specific enhancement
        optimized = self._enhance_role_playing(optimized, context)
        
        # Output structuring
        optimized = self._structure_output(optimized, context)
        
        return optimized
    
    def _inject_context(
        self,
        template: Dict[str, str],
        context: PromptContext,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Inject contextual information into the prompt."""
        enhanced = template.copy()
        
        # Add audience-specific language
        if context.audience_level == "executive":
            enhanced["system_prompt"] += "\n\nFocus on strategic business impact, ROI, and executive-level insights. Use clear, concise language suitable for C-level presentation."
        elif context.audience_level == "technical":
            enhanced["system_prompt"] += "\n\nProvide deep technical analysis with specific implementation details, code examples, and architectural diagrams."
        
        # Add industry-specific context
        if context.business_domain:
            enhanced["system_prompt"] += f"\n\nConsider {context.business_domain} industry-specific requirements, regulations, and best practices."
        
        # Format template with actual data
        if "user_prompt_template" in enhanced:
            # Prepare comprehensive data dictionary with all possible template variables
            format_data = {
                # Basic company information
                "company_name": data.get("company_name", "Organization"),
                "assessment_data": json.dumps(data.get("assessment_data", {}), indent=2),
                "industry_context": data.get("industry_context", "General business context"),
                "compliance_requirements": data.get("compliance_requirements", "Standard compliance requirements"),
                "budget_constraints": data.get("budget_constraints", "Budget considerations"),
                "current_architecture": data.get("current_architecture", "Current system architecture"),
                "performance_metrics": data.get("performance_metrics", "Performance data"),
                "security_requirements": data.get("security_requirements", "Security requirements"),
                "business_objectives": data.get("business_objectives", "Business goals"),
                "industry_trends": data.get("industry_trends", "Industry trends"),
                "competitive_landscape": data.get("competitive_landscape", "Competitive analysis"),
                
                # Cost analysis specific variables
                "cost_data": json.dumps(data.get("cost_data", data.get("cost_projections", {})), indent=2),
                
                # Compliance specific variables  
                "requirements": ", ".join(data.get("requirements", data.get("compliance_requirements", ["Standard compliance"]))),
                "current_state": json.dumps(data.get("current_state", data.get("compliance_analysis", {})), indent=2),
                
                # Stakeholder specific variables
                "stakeholder_role": data.get("stakeholder_role", context.audience_level or "general"),
                "audience_level": context.audience_level or data.get("audience_level", "general"),
                "stakeholder_focus": data.get("stakeholder_focus", "general business impact"),
            }
            
            try:
                enhanced["user_prompt"] = enhanced["user_prompt_template"].format(**format_data)
            except KeyError as e:
                # Log missing key and use a safe fallback
                logger.warning(f"Missing template variable {e}, using fallback")
                # Create a safe formatter that ignores missing keys
                import string
                class SafeFormatter(string.Formatter):
                    def get_value(self, key, args, kwargs):
                        if isinstance(key, str):
                            try:
                                return kwargs[key]
                            except KeyError:
                                return f"[{key}]"
                        else:
                            return string.Formatter.get_value(key, args, kwargs)
                
                safe_formatter = SafeFormatter()
                enhanced["user_prompt"] = safe_formatter.format(enhanced["user_prompt_template"], **format_data)
                
            del enhanced["user_prompt_template"]
        
        return enhanced
    
    def _add_chain_of_thought(
        self,
        template: Dict[str, str],
        context: PromptContext
    ) -> Dict[str, str]:
        """Add chain-of-thought reasoning to complex prompts."""
        enhanced = template.copy()
        
        cot_instruction = """

Before providing your final response, please think through this step-by-step:

1. **Analysis Framework**: What analytical framework is most appropriate for this assessment?
2. **Data Evaluation**: What are the key insights from the provided data?
3. **Risk Assessment**: What are the primary risks and how should they be prioritized?
4. **Strategic Implications**: How do the technical findings translate to business impact?
5. **Recommendation Synthesis**: What are the most actionable recommendations based on this analysis?

Work through each step methodically, then provide your comprehensive response.
"""
        
        enhanced["user_prompt"] = enhanced.get("user_prompt") + cot_instruction
        
        return enhanced
    
    def _enhance_role_playing(
        self,
        template: Dict[str, str],
        context: PromptContext
    ) -> Dict[str, str]:
        """Enhance role-playing aspects for better persona adherence."""
        enhanced = template.copy()
        
        role_enhancement = f"""

Adopt the perspective of a senior professional who:
- Has successfully led {context.report_type} initiatives for similar organizations
- Understands the {context.audience_level}-level communication requirements
- Has deep expertise in {context.business_domain} industry challenges
- Can balance technical excellence with business pragmatism
- Provides insights that are immediately actionable and measurable

Your response should reflect this expertise and experience level.
"""
        
        enhanced["system_prompt"] += role_enhancement
        
        return enhanced
    
    def _structure_output(
        self,
        template: Dict[str, str],
        context: PromptContext
    ) -> Dict[str, str]:
        """Add specific output structure requirements."""
        enhanced = template.copy()
        
        if context.output_format == "structured":
            structure_instruction = """

IMPORTANT: Structure your response using the following format:

## Executive Summary
[2-3 sentences highlighting key findings and recommendations]

## Detailed Analysis
[Main content organized in clear sections with headers]

## Key Metrics & Quantifications
[Specific numbers, percentages, and measurable outcomes]

## Action Items
[Prioritized list of specific next steps with timelines]

## Appendices
[Supporting details, technical specifications, and reference materials]

Use clear markdown formatting with appropriate headers, bullet points, and emphasis.
"""
        elif context.output_format == "dashboard":
            structure_instruction = """

IMPORTANT: Format your response for dashboard consumption:

**KPIs & Metrics**: Provide quantifiable metrics that can be displayed as charts
**Status Indicators**: Use clear status indicators (Green/Yellow/Red)
**Trend Analysis**: Include directional indicators and growth projections
**Alert Items**: Highlight items requiring immediate attention
**Summary Cards**: Create concise summary cards for key findings

Structure data in a way that can be easily parsed for visualization.
"""
        else:
            structure_instruction = """

IMPORTANT: Present your analysis in a professional report format with:
- Clear executive summary
- Well-organized sections with descriptive headers
- Quantified findings where possible
- Specific, actionable recommendations
- Professional language appropriate for stakeholders
"""
        
        enhanced["user_prompt"] += structure_instruction
        
        return enhanced
    
    def _add_quality_assurance(
        self,
        prompt: Dict[str, str],
        template_type: PromptTemplate,
        context: PromptContext
    ) -> Dict[str, str]:
        """Add quality assurance requirements."""
        enhanced = prompt.copy()
        
        qa_requirements = f"""

QUALITY ASSURANCE REQUIREMENTS:
- Ensure all recommendations are specific and actionable
- Include quantified metrics wherever possible (costs, timelines, performance improvements)
- Validate that security and compliance considerations are addressed
- Confirm that the response is appropriate for {context.audience_level} audience
- Verify that all critical sections are covered comprehensively
- Double-check that formatting is professional and consistent

Before submitting your response, review it against these quality criteria.
"""
        
        enhanced["user_prompt"] += qa_requirements
        
        return enhanced
    
    def evaluate_prompt_quality(
        self,
        generated_content: str,
        template_type: PromptTemplate,
        context: PromptContext
    ) -> Dict[str, float]:
        """
        Evaluate the quality of generated content.
        
        Args:
            generated_content: The content generated from the prompt
            template_type: The type of template used
            context: The context used for generation
            
        Returns:
            Dictionary of quality scores
        """
        quality_metrics = self.quality_metrics.get(template_type.value, {})
        scores = {}
        
        try:
            # Check completeness
            required_sections = quality_metrics.get("required_sections", [])
            sections_found = 0
            for section in required_sections:
                if section.lower() in generated_content.lower():
                    sections_found += 1
            
            scores["completeness"] = sections_found / len(required_sections) if required_sections else 1.0
            
            # Check for quantified metrics
            numbers_pattern = r'\b\d+(?:\.\d+)?(?:%|\$|[KMB])\b'
            quantifications = len(re.findall(numbers_pattern, generated_content))
            scores["quantification"] = min(quantifications / 10, 1.0)  # Normalize to 0-1
            
            # Check structure and formatting
            headers_pattern = r'^#+\s+.+$'
            headers = len(re.findall(headers_pattern, generated_content, re.MULTILINE))
            scores["structure"] = min(headers / 5, 1.0)  # Normalize to 0-1
            
            # Overall quality score
            scores["overall"] = sum(scores.values()) / len(scores)
            
            logger.info(f"Quality evaluation completed for {template_type.value}: {scores}")
            
        except Exception as e:
            logger.error(f"Error evaluating prompt quality: {e}")
            scores = {"overall": 0.0, "error": str(e)}
        
        return scores


# Professional report templates for enhanced outputs
PROFESSIONAL_REPORT_TEMPLATES = {
    "executive_briefing": """
# EXECUTIVE BRIEFING: Infrastructure Assessment
**{company_name}** | **{date}** | **Prepared by: Infrastructure Advisory Team**

---

## 🎯 STRATEGIC OVERVIEW
{strategic_overview}

## 💰 FINANCIAL IMPACT ANALYSIS
{financial_analysis}

## ⚠️ RISK & COMPLIANCE MATRIX
{risk_assessment}

## 🗺️ STRATEGIC ROADMAP
{roadmap}

## ✅ EXECUTIVE RECOMMENDATIONS
{recommendations}

---
*This document contains confidential and proprietary information. Distribution is restricted to authorized stakeholders only.*
""",

    "technical_assessment": """
# TECHNICAL INFRASTRUCTURE ASSESSMENT
**{company_name}** | **Technical Deep Dive Report** | **{date}**

---

## 🏗️ ARCHITECTURE ANALYSIS
{architecture_analysis}

## 🔒 SECURITY & COMPLIANCE
{security_analysis}

## ⚡ PERFORMANCE & RELIABILITY
{performance_analysis}

## 📋 INFRASTRUCTURE AS CODE
{iac_analysis}

## 💸 COST OPTIMIZATION
{cost_analysis}

---
*Technical Assessment conducted by certified cloud architects and infrastructure specialists.*
""",

    "stakeholder_summary": """
# STAKEHOLDER BRIEFING: Infrastructure Modernization
**{company_name}** | **{stakeholder_group}** | **{date}**

---

## KEY HIGHLIGHTS
{key_highlights}

## BUSINESS IMPACT
{business_impact}

## INVESTMENT REQUIREMENTS
{investment_requirements}

## TIMELINE & MILESTONES
{timeline}

## NEXT STEPS
{next_steps}

---
*Prepared for {stakeholder_group} stakeholder review and approval.*
"""
}