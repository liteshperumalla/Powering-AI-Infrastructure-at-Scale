"""
AI Consultant Agent for Infra Mind.

Provides generative AI business integration and strategy consulting.
Focuses on business process analysis, AI opportunity identification, and AI transformation strategies.
"""

import logging
import json
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from .web_search import WebSearchClient, get_web_search_client
from ..models.assessment import Assessment
from ..llm.manager import LLMManager

logger = logging.getLogger(__name__)


class AIConsultantAgent(BaseAgent):
    """
    AI Consultant Agent for generative AI business integration and strategy consulting.
    
    This agent focuses on:
    - Business process mapping and AI opportunity identification
    - Industry-specific AI use case recommendations
    - Change management strategies for AI adoption
    - AI ethics and responsible AI implementation guidance
    - Custom AI solution architecture recommendations
    - Training and upskilling program suggestions
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize AI Consultant Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="AI Consultant Agent",
                role=AgentRole.AI_CONSULTANT,
                tools_enabled=["data_processor", "calculator", "cloud_api"],
                temperature=0.3,  # Balanced creativity for strategic recommendations
                max_tokens=2500,
                custom_config={
                    "focus_areas": [
                        "business_process_analysis",
                        "ai_opportunity_identification",
                        "transformation_strategy",
                        "change_management",
                        "ai_ethics",
                        "solution_architecture"
                    ],
                    "ai_domains": [
                        "natural_language_processing",
                        "computer_vision",
                        "machine_learning",
                        "generative_ai",
                        "automation",
                        "predictive_analytics"
                    ],
                    "industry_expertise": [
                        "healthcare",
                        "finance",
                        "retail",
                        "manufacturing",
                        "technology",
                        "education"
                    ]
                }
            )
        
        super().__init__(config)
        
        # AI Consultant-specific attributes
        self.ai_use_cases = {
            "customer_service": {
                "description": "AI-powered chatbots and virtual assistants",
                "technologies": ["NLP", "conversational_ai", "sentiment_analysis"],
                "roi_potential": "high",
                "implementation_complexity": "medium"
            },
            "content_generation": {
                "description": "Automated content creation and optimization",
                "technologies": ["generative_ai", "nlp", "content_optimization"],
                "roi_potential": "high",
                "implementation_complexity": "low"
            },
            "predictive_analytics": {
                "description": "Forecasting and trend analysis",
                "technologies": ["machine_learning", "time_series", "statistical_modeling"],
                "roi_potential": "very_high",
                "implementation_complexity": "high"
            },
            "process_automation": {
                "description": "Intelligent process automation and optimization",
                "technologies": ["rpa", "machine_learning", "workflow_automation"],
                "roi_potential": "high",
                "implementation_complexity": "medium"
            },
            "document_processing": {
                "description": "Automated document analysis and extraction",
                "technologies": ["ocr", "nlp", "computer_vision"],
                "roi_potential": "medium",
                "implementation_complexity": "medium"
            },
            "recommendation_systems": {
                "description": "Personalized recommendations and matching",
                "technologies": ["collaborative_filtering", "deep_learning", "embeddings"],
                "roi_potential": "high",
                "implementation_complexity": "high"
            }
        }
        
        self.transformation_frameworks = [
            "AI Readiness Assessment",
            "Business Process Mapping",
            "AI Opportunity Matrix",
            "Change Management Strategy",
            "Ethics and Governance Framework",
            "Implementation Roadmap"
        ]
        
        # Initialize web search for real-time market data
        self.web_search_client = None
        self.llm_client = None
        
        logger.info("AI Consultant Agent initialized with generative AI expertise")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute AI Consultant agent's main analysis logic.
        
        Returns:
            Dictionary with AI transformation recommendations and strategy
        """
        logger.info("AI Consultant Agent starting AI transformation analysis")
        
        try:
            # Initialize clients for real data collection
            if not self.web_search_client:
                self.web_search_client = await get_web_search_client()
            if not self.llm_client:
                self.llm_client = LLMManager()
            
            # Step 1: Collect real-time AI market intelligence
            market_intelligence = await self._collect_ai_market_intelligence()
            
            # Step 2: Analyze current business processes with market context
            business_process_analysis = await self._analyze_business_processes_with_market_data(market_intelligence)
            
            # Step 3: Identify AI opportunities using real market trends
            ai_opportunities = await self._identify_ai_opportunities_with_trends(market_intelligence)
            
            # Step 4: Assess AI readiness with industry benchmarks
            readiness_assessment = await self._assess_ai_readiness_with_benchmarks(market_intelligence)
            
            # Step 5: Generate AI use case recommendations with real success stories
            use_case_recommendations = await self._generate_use_case_recommendations(
                business_process_analysis, ai_opportunities
            )
            
            # Step 6: Create transformation strategy with market insights
            transformation_strategy = await self._create_transformation_strategy_with_market_data(
                readiness_assessment, use_case_recommendations, market_intelligence
            )
            
            # Step 7: Develop implementation roadmap with real timelines
            implementation_roadmap = await self._develop_implementation_roadmap_with_real_data(
                transformation_strategy, use_case_recommendations, market_intelligence
            )
            
            # Step 8: Address ethics and governance with current best practices
            ethics_governance = await self._address_ethics_and_governance_with_current_practices(market_intelligence)
            
            result = {
                "recommendations": use_case_recommendations,
                "data": {
                    "market_intelligence": market_intelligence,
                    "business_process_analysis": business_process_analysis,
                    "ai_opportunities": ai_opportunities,
                    "readiness_assessment": readiness_assessment,
                    "transformation_strategy": transformation_strategy,
                    "implementation_roadmap": implementation_roadmap,
                    "ethics_governance": ethics_governance,
                    "frameworks_used": self.transformation_frameworks,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("AI Consultant Agent completed AI transformation analysis successfully")
            return result
            
        except Exception as e:
            logger.error(f"AI Consultant Agent analysis failed: {str(e)}")
            raise
    
    async def _analyze_business_processes(self) -> Dict[str, Any]:
        """Analyze current business processes for AI integration opportunities."""
        logger.debug("Analyzing business processes")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        
        # Use data processing tool to analyze assessment data
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        # Extract business context
        industry = business_req.get("industry", "technology")
        company_size = business_req.get("company_size", "startup")
        primary_goals = business_req.get("primary_goals", [])
        
        # Identify key business processes based on industry and goals
        key_processes = self._identify_key_processes(industry, primary_goals)
        
        # Assess process maturity and automation potential
        process_assessment = self._assess_process_maturity(key_processes, company_size)
        
        return {
            "industry_context": {
                "industry": industry,
                "company_size": company_size,
                "primary_goals": primary_goals
            },
            "key_processes": key_processes,
            "process_assessment": process_assessment,
            "automation_potential": self._calculate_automation_potential(process_assessment),
            "data_insights": analysis_result.data if analysis_result.is_success else {}
        }
    
    async def _identify_ai_opportunities(self) -> Dict[str, Any]:
        """Identify specific AI opportunities based on business context."""
        logger.debug("Identifying AI opportunities")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        industry = business_req.get("industry", "technology")
        company_size = business_req.get("company_size", "startup")
        budget_range = business_req.get("budget_range", "$10k-50k")
        workload_types = technical_req.get("workload_types", [])
        
        # Identify relevant AI use cases for the industry
        relevant_use_cases = self._get_industry_specific_use_cases(industry)
        
        # Filter use cases by budget and complexity
        budget_min, budget_max = self._parse_budget_range(budget_range)
        feasible_use_cases = self._filter_use_cases_by_budget(relevant_use_cases, budget_max)
        
        # Prioritize use cases based on ROI and implementation complexity
        prioritized_opportunities = self._prioritize_ai_opportunities(
            feasible_use_cases, company_size, workload_types
        )
        
        return {
            "industry_context": industry,
            "budget_constraints": {"min": budget_min, "max": budget_max},
            "relevant_use_cases": relevant_use_cases,
            "feasible_use_cases": feasible_use_cases,
            "prioritized_opportunities": prioritized_opportunities,
            "quick_wins": [opp for opp in prioritized_opportunities if opp.get("implementation_time", "medium") == "short"],
            "strategic_initiatives": [opp for opp in prioritized_opportunities if opp.get("roi_potential") == "very_high"]
        }
    
    async def _assess_ai_readiness(self) -> Dict[str, Any]:
        """Assess organization's readiness for AI adoption."""
        logger.debug("Assessing AI readiness")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Assess different dimensions of AI readiness
        readiness_dimensions = {
            "data_readiness": self._assess_data_readiness(technical_req),
            "technical_readiness": self._assess_technical_readiness(technical_req),
            "organizational_readiness": self._assess_organizational_readiness(business_req),
            "cultural_readiness": self._assess_cultural_readiness(business_req),
            "governance_readiness": self._assess_governance_readiness(business_req)
        }
        
        # Calculate overall readiness score
        overall_score = sum(dim["score"] for dim in readiness_dimensions.values()) / len(readiness_dimensions)
        
        # Identify readiness gaps
        readiness_gaps = []
        for dimension, assessment in readiness_dimensions.items():
            if assessment["score"] < 0.6:
                readiness_gaps.extend(assessment.get("gaps", []))
        
        return {
            "overall_readiness_score": overall_score,
            "readiness_level": self._categorize_readiness(overall_score),
            "readiness_dimensions": readiness_dimensions,
            "readiness_gaps": readiness_gaps,
            "improvement_priorities": self._prioritize_readiness_improvements(readiness_dimensions)
        }
    
    async def _generate_use_case_recommendations(self, business_analysis: Dict[str, Any], 
                                               ai_opportunities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific AI use case recommendations."""
        logger.debug("Generating AI use case recommendations")
        
        recommendations = []
        
        # Get prioritized opportunities
        prioritized_opportunities = ai_opportunities.get("prioritized_opportunities", [])
        
        for opportunity in prioritized_opportunities[:3]:  # Top 3 opportunities
            use_case_name = opportunity.get("use_case")
            use_case_details = self.ai_use_cases.get(use_case_name, {})
            
            recommendation = {
                "category": "ai_use_case",
                "priority": self._determine_priority(opportunity),
                "title": f"Implement {use_case_details.get('description', use_case_name)}",
                "use_case": use_case_name,
                "description": use_case_details.get("description", "AI-powered solution"),
                "business_value": opportunity.get("business_value", "Improved efficiency and automation"),
                "technologies_required": use_case_details.get("technologies", []),
                "implementation_complexity": use_case_details.get("implementation_complexity", "medium"),
                "roi_potential": use_case_details.get("roi_potential", "medium"),
                "estimated_timeline": opportunity.get("implementation_time", "3-6 months"),
                "estimated_cost": opportunity.get("estimated_cost", "$25,000 - $75,000"),
                "success_metrics": self._define_success_metrics(use_case_name),
                "risks_and_mitigation": self._identify_risks_and_mitigation(use_case_name),
                "next_steps": self._define_next_steps(use_case_name)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _create_transformation_strategy(self, readiness_assessment: Dict[str, Any],
                                            use_case_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive AI transformation strategy."""
        logger.debug("Creating AI transformation strategy")
        
        readiness_score = readiness_assessment.get("overall_readiness_score", 0.5)
        
        # Define transformation phases based on readiness
        if readiness_score < 0.4:
            strategy_approach = "foundation_first"
            phases = ["Foundation Building", "Pilot Projects", "Scaling"]
        elif readiness_score < 0.7:
            strategy_approach = "pilot_driven"
            phases = ["Quick Wins", "Core Implementations", "Advanced Applications"]
        else:
            strategy_approach = "accelerated"
            phases = ["Immediate Implementations", "Strategic Initiatives", "Innovation Labs"]
        
        # Create phased recommendations
        phased_recommendations = self._create_phased_recommendations(phases, use_case_recommendations)
        
        # Develop change management strategy
        change_management_strategy = self._develop_change_management_strategy(readiness_assessment)
        
        # Create risk mitigation plan
        risk_mitigation_plan = self._create_risk_mitigation_plan(use_case_recommendations)
        
        return {
            "strategy_approach": strategy_approach,
            "transformation_phases": phases,
            "phased_recommendations": phased_recommendations,
            "success_criteria": self._define_transformation_success_criteria(use_case_recommendations),
            "investment_analysis": await self._calculate_transformation_investment(use_case_recommendations),
            "change_management_strategy": change_management_strategy,
            "risk_mitigation_plan": risk_mitigation_plan
        }
    
    async def _develop_implementation_roadmap(self, transformation_strategy: Dict[str, Any],
                                            use_case_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Develop detailed implementation roadmap."""
        logger.debug("Developing implementation roadmap")
        
        phases = transformation_strategy.get("transformation_phases", [])
        
        return {
            "timeline_overview": self._create_timeline_overview(phases),
            "resource_requirements": self._calculate_resource_requirements(use_case_recommendations),
            "governance_structure": self._define_governance_structure(),
            "milestone_tracking": self._define_milestone_tracking(phases),
            "success_metrics": self._define_implementation_success_metrics()
        }
    
    async def _address_ethics_and_governance(self) -> Dict[str, Any]:
        """Address AI ethics and governance considerations."""
        logger.debug("Addressing AI ethics and governance")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        compliance_req = business_req.get("compliance_requirements", {})
        
        # Identify applicable regulations
        regulations = compliance_req.get("regulations", [])
        
        return {
            "core_principles": [
                "Transparency and Explainability",
                "Fairness and Non-discrimination",
                "Privacy and Data Protection",
                "Accountability and Responsibility",
                "Human Oversight and Control"
            ],
            "governance_structure": {
                "ai_ethics_committee": "Cross-functional team to oversee AI initiatives",
                "data_governance_board": "Ensure data quality and compliance",
                "ai_risk_management": "Identify and mitigate AI-related risks"
            },
            "compliance_considerations": self._assess_ai_compliance_requirements(regulations),
            "risk_assessment": self._assess_ai_ethical_risks(),
            "monitoring_framework": self._create_monitoring_framework(),
            "training_requirements": self._define_training_requirements()
        }
    
    # Helper methods
    
    def _identify_key_processes(self, industry: str, goals: List[str]) -> List[Dict[str, Any]]:
        """Identify key business processes based on industry and goals."""
        industry_processes = {
            "healthcare": [
                {"name": "Patient Care Management", "automation_potential": "high"},
                {"name": "Medical Records Processing", "automation_potential": "very_high"},
                {"name": "Appointment Scheduling", "automation_potential": "high"},
                {"name": "Billing and Claims Processing", "automation_potential": "very_high"}
            ],
            "finance": [
                {"name": "Risk Assessment", "automation_potential": "very_high"},
                {"name": "Customer Service", "automation_potential": "high"},
                {"name": "Fraud Detection", "automation_potential": "very_high"},
                {"name": "Loan Processing", "automation_potential": "high"}
            ],
            "retail": [
                {"name": "Inventory Management", "automation_potential": "high"},
                {"name": "Customer Support", "automation_potential": "high"},
                {"name": "Recommendation Systems", "automation_potential": "very_high"},
                {"name": "Supply Chain Optimization", "automation_potential": "high"}
            ],
            "manufacturing": [
                {"name": "Quality Control", "automation_potential": "very_high"},
                {"name": "Predictive Maintenance", "automation_potential": "very_high"},
                {"name": "Supply Chain Management", "automation_potential": "high"},
                {"name": "Production Planning", "automation_potential": "high"}
            ],
            "technology": [
                {"name": "Software Development", "automation_potential": "medium"},
                {"name": "Customer Support", "automation_potential": "high"},
                {"name": "Data Analysis", "automation_potential": "very_high"},
                {"name": "DevOps and Monitoring", "automation_potential": "high"}
            ],
            "education": [
                {"name": "Student Assessment", "automation_potential": "high"},
                {"name": "Content Creation", "automation_potential": "high"},
                {"name": "Administrative Tasks", "automation_potential": "very_high"},
                {"name": "Personalized Learning", "automation_potential": "high"}
            ]
        }
        
        return industry_processes.get(industry, [
            {"name": "Customer Service", "automation_potential": "high"},
            {"name": "Data Processing", "automation_potential": "high"},
            {"name": "Document Management", "automation_potential": "medium"}
        ])
    
    def _assess_process_maturity(self, processes: List[Dict[str, Any]], company_size: str) -> Dict[str, Any]:
        """Assess the maturity of business processes."""
        base_maturity = {
            "startup": 0.3, "small": 0.5, "medium": 0.6, "large": 0.7, "enterprise": 0.8
        }.get(company_size, 0.5)
        
        maturity_scores = {process["name"]: base_maturity for process in processes}
        
        return {
            "process_scores": maturity_scores,
            "average_maturity": base_maturity
        }
    
    def _calculate_automation_potential(self, process_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall automation potential."""
        average_maturity = process_assessment.get("average_maturity", 0.5)
        overall_score = min(average_maturity + 0.2, 1.0)
        
        return {
            "overall_score": overall_score,
            "automation_readiness": "high" if overall_score > 0.7 else "medium" if overall_score > 0.4 else "low"
        }
    
    def _get_industry_specific_use_cases(self, industry: str) -> List[str]:
        """Get AI use cases relevant to specific industry."""
        industry_use_cases = {
            "healthcare": ["predictive_analytics", "document_processing", "customer_service"],
            "finance": ["predictive_analytics", "process_automation", "customer_service"],
            "retail": ["recommendation_systems", "customer_service", "predictive_analytics"],
            "manufacturing": ["predictive_analytics", "process_automation", "document_processing"],
            "technology": ["content_generation", "customer_service", "process_automation"],
            "education": ["content_generation", "customer_service", "predictive_analytics"]
        }
        
        return industry_use_cases.get(industry, ["customer_service", "content_generation"])
    
    def _parse_budget_range(self, budget_range: str) -> tuple[float, float]:
        """Parse budget range string to numeric values."""
        budget_mapping = {
            "$1k-10k": (1000, 10000),
            "$10k-50k": (10000, 50000),
            "$50k-100k": (50000, 100000),
            "$100k+": (100000, 500000)
        }
        return budget_mapping.get(budget_range, (10000, 50000))
    
    def _filter_use_cases_by_budget(self, use_cases: List[str], max_budget: float) -> List[str]:
        """Filter use cases based on budget constraints."""
        use_case_costs = {
            "customer_service": 25000,
            "content_generation": 15000,
            "predictive_analytics": 75000,
            "process_automation": 50000,
            "document_processing": 35000,
            "recommendation_systems": 60000
        }
        
        return [use_case for use_case in use_cases 
                if use_case_costs.get(use_case, 30000) <= max_budget]
    
    def _prioritize_ai_opportunities(self, use_cases: List[str], company_size: str, 
                                   workload_types: List[str]) -> List[Dict[str, Any]]:
        """Prioritize AI opportunities based on various factors."""
        opportunities = []
        
        for use_case in use_cases:
            use_case_details = self.ai_use_cases.get(use_case, {})
            
            # Calculate priority score
            priority_score = 0.5  # Base score
            
            # ROI potential weight
            roi_weights = {"very_high": 0.4, "high": 0.3, "medium": 0.2, "low": 0.1}
            priority_score += roi_weights.get(use_case_details.get("roi_potential", "medium"), 0.2)
            
            # Implementation complexity weight (lower complexity = higher priority)
            complexity_weights = {"low": 0.3, "medium": 0.2, "high": 0.1}
            priority_score += complexity_weights.get(use_case_details.get("implementation_complexity", "medium"), 0.2)
            
            opportunity = {
                "use_case": use_case,
                "priority_score": priority_score,
                "business_value": self._generate_business_value_description(use_case),
                "implementation_time": self._estimate_implementation_time(use_case, company_size),
                "estimated_cost": self._estimate_implementation_cost(use_case, company_size)
            }
            
            opportunities.append(opportunity)
        
        # Sort by priority score
        return sorted(opportunities, key=lambda x: x["priority_score"], reverse=True)
    
    def _assess_data_readiness(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data readiness for AI implementation."""
        score = 0.5  # Base score
        gaps = []
        
        workload_types = technical_req.get("workload_types", [])
        if isinstance(workload_types, list):
            if "database" in workload_types:
                score += 0.2
            else:
                gaps.append("Limited data infrastructure")
            
            if "analytics" in workload_types:
                score += 0.1
        
        return {"score": min(score, 1.0), "level": "medium", "gaps": gaps}
    
    def _assess_technical_readiness(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical readiness for AI implementation."""
        score = 0.5  # Base score
        gaps = []
        
        workload_types = technical_req.get("workload_types", [])
        if isinstance(workload_types, list):
            if "web_application" in workload_types:
                score += 0.2
            if "ai_ml" in workload_types:
                score += 0.3
            else:
                gaps.append("No existing AI/ML infrastructure")
        
        expected_users = technical_req.get("expected_users", 0)
        if expected_users > 1000:
            score += 0.1
        
        return {"score": min(score, 1.0), "level": "medium", "gaps": gaps}
    
    def _assess_organizational_readiness(self, business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess organizational readiness for AI adoption."""
        company_size = business_req.get("company_size", "startup")
        size_scores = {"startup": 0.3, "small": 0.4, "medium": 0.6, "large": 0.7, "enterprise": 0.8}
        score = size_scores.get(company_size, 0.4)
        
        primary_goals = business_req.get("primary_goals", [])
        if "innovation" in primary_goals:
            score += 0.1
        if "efficiency" in primary_goals:
            score += 0.1
        
        return {"score": min(score, 1.0), "level": "medium", "gaps": []}
    
    def _assess_cultural_readiness(self, business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess cultural readiness for AI adoption."""
        industry = business_req.get("industry", "technology")
        score = 0.7 if industry in ["technology", "finance"] else 0.5
        
        company_size = business_req.get("company_size", "startup")
        if company_size in ["startup", "small"]:
            score += 0.1  # Smaller companies are often more agile
        
        return {"score": min(score, 1.0), "level": "medium", "gaps": []}
    
    def _assess_governance_readiness(self, business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess governance readiness for AI implementation."""
        company_size = business_req.get("company_size", "startup")
        size_scores = {"startup": 0.2, "small": 0.3, "medium": 0.5, "large": 0.7, "enterprise": 0.8}
        score = size_scores.get(company_size, 0.3)
        
        return {"score": score, "level": "medium", "gaps": []}
    
    def _categorize_readiness(self, score: float) -> str:
        """Categorize overall readiness score."""
        if score >= 0.8:
            return "Excellent - Ready for advanced AI implementations"
        elif score >= 0.6:
            return "Good - Ready for pilot projects and gradual rollout"
        elif score >= 0.4:
            return "Fair - Needs foundation building before major AI initiatives"
        else:
            return "Poor - Requires significant preparation for AI adoption"
    
    def _prioritize_readiness_improvements(self, readiness_dimensions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize readiness improvement areas."""
        improvements = []
        
        for dimension, assessment in readiness_dimensions.items():
            if assessment["score"] < 0.6:
                improvements.append({
                    "dimension": dimension,
                    "current_score": assessment["score"],
                    "priority": "high" if assessment["score"] < 0.4 else "medium",
                    "gaps": assessment.get("gaps", [])
                })
        
        return sorted(improvements, key=lambda x: x["current_score"])
    
    def _determine_priority(self, opportunity: Dict[str, Any]) -> str:
        """Determine priority level for an opportunity."""
        priority_score = opportunity.get("priority_score", 0.5)
        return "high" if priority_score >= 0.7 else "medium" if priority_score >= 0.4 else "low"
    
    def _define_success_metrics(self, use_case: str) -> List[str]:
        """Define success metrics for a specific use case."""
        metrics_map = {
            "customer_service": ["Customer satisfaction score > 85%", "Response time reduction > 50%", "Support ticket resolution rate > 90%"],
            "content_generation": ["Content production increase > 200%", "Content quality score > 80%", "Time to publish reduction > 60%"],
            "predictive_analytics": ["Prediction accuracy > 85%", "Decision-making speed improvement > 40%", "Cost reduction > 20%"],
            "process_automation": ["Process completion time reduction > 50%", "Error rate reduction > 80%", "Employee satisfaction increase > 30%"],
            "document_processing": ["Processing time reduction > 70%", "Accuracy improvement > 95%", "Manual effort reduction > 80%"],
            "recommendation_systems": ["Click-through rate improvement > 25%", "Conversion rate increase > 15%", "User engagement increase > 30%"]
        }
        
        return metrics_map.get(use_case, ["User adoption rate > 70%", "ROI > 150% within 12 months", "Process efficiency improvement > 25%"])
    
    def _identify_risks_and_mitigation(self, use_case: str) -> List[str]:
        """Identify risks and mitigation strategies for a use case."""
        risks_map = {
            "customer_service": [
                "Risk: Customer resistance to AI. Mitigation: Gradual rollout with human oversight",
                "Risk: Misunderstanding customer queries. Mitigation: Continuous training and feedback loops"
            ],
            "content_generation": [
                "Risk: Generated content quality issues. Mitigation: Human review process and quality gates",
                "Risk: Brand voice inconsistency. Mitigation: Fine-tuned models and style guidelines"
            ],
            "predictive_analytics": [
                "Risk: Model bias and fairness issues. Mitigation: Regular bias testing and monitoring",
                "Risk: Data quality problems. Mitigation: Robust data validation and cleaning processes"
            ],
            "process_automation": [
                "Risk: Job displacement concerns. Mitigation: Reskilling programs and change management",
                "Risk: Process failures. Mitigation: Fallback procedures and monitoring systems"
            ],
            "document_processing": [
                "Risk: Accuracy issues with complex documents. Mitigation: Human validation for critical documents",
                "Risk: Privacy and security concerns. Mitigation: Encryption and access controls"
            ],
            "recommendation_systems": [
                "Risk: Filter bubbles and bias. Mitigation: Diversity algorithms and bias monitoring",
                "Risk: Privacy concerns. Mitigation: Anonymization and consent management"
            ]
        }
        
        return risks_map.get(use_case, ["Risk: User adoption challenges. Mitigation: Comprehensive training program"])
    
    def _define_next_steps(self, use_case: str) -> List[str]:
        """Define next steps for implementing a use case."""
        steps_map = {
            "customer_service": [
                "Conduct customer service process audit",
                "Select chatbot platform and NLP provider",
                "Design conversation flows and training data"
            ],
            "content_generation": [
                "Audit existing content and define requirements",
                "Select generative AI platform and tools",
                "Create content templates and style guides"
            ],
            "predictive_analytics": [
                "Assess data quality and availability",
                "Define prediction use cases and success metrics",
                "Select ML platform and modeling approach"
            ],
            "process_automation": [
                "Map current processes and identify automation opportunities",
                "Select RPA and AI tools",
                "Design automated workflows and exception handling"
            ],
            "document_processing": [
                "Analyze document types and processing requirements",
                "Select OCR and NLP technologies",
                "Design document processing pipeline"
            ],
            "recommendation_systems": [
                "Analyze user behavior and preferences data",
                "Select recommendation algorithms and platform",
                "Design A/B testing framework"
            ]
        }
        
        return steps_map.get(use_case, [
            "Conduct detailed requirements analysis",
            "Select technology platform and vendors",
            "Create implementation plan and timeline"
        ])
    
    def _create_phased_recommendations(self, phases: List[str], recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create phased recommendations based on transformation phases."""
        phased_recs = {}
        
        for i, phase in enumerate(phases):
            phase_recs = []
            start_idx = i * len(recommendations) // len(phases)
            end_idx = (i + 1) * len(recommendations) // len(phases)
            
            for rec in recommendations[start_idx:end_idx]:
                phase_recs.append({
                    "title": rec.get("title", "Unknown"),
                    "priority": rec.get("priority", "medium"),
                    "timeline": rec.get("estimated_timeline", "3-6 months"),
                    "cost": rec.get("estimated_cost", "$25,000 - $75,000")
                })
            
            phased_recs[phase] = phase_recs
        
        return phased_recs
    
    def _develop_change_management_strategy(self, readiness_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Develop change management strategy based on readiness assessment."""
        cultural_score = readiness_assessment.get("readiness_dimensions", {}).get("cultural_readiness", {}).get("score", 0.5)
        
        if cultural_score < 0.4:
            approach = "intensive_change_management"
            activities = [
                "Executive sponsorship and communication",
                "Comprehensive training programs",
                "Change champion network",
                "Regular feedback and adjustment sessions"
            ]
        elif cultural_score < 0.7:
            approach = "moderate_change_management"
            activities = [
                "Leadership alignment sessions",
                "Targeted training programs",
                "Pilot project showcases",
                "Regular progress communications"
            ]
        else:
            approach = "light_change_management"
            activities = [
                "Kick-off communications",
                "Just-in-time training",
                "Success story sharing",
                "Feedback collection"
            ]
        
        return {
            "approach": approach,
            "key_activities": activities,
            "communication_plan": [
                "Monthly all-hands updates on AI transformation progress",
                "Quarterly success story presentations",
                "Bi-annual strategy review sessions"
            ],
            "training_plan": [
                "AI literacy training for all employees",
                "Technical training for IT staff",
                "Leadership training for managers"
            ]
        }
    
    def _create_risk_mitigation_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive risk mitigation plan."""
        all_risks = []
        for rec in recommendations:
            risks = rec.get("risks_and_mitigation", [])
            all_risks.extend(risks)
        
        return {
            "technical_risks": [
                "Risk: AI model performance degradation. Mitigation: Continuous monitoring and retraining",
                "Risk: Integration challenges. Mitigation: Phased rollout and extensive testing"
            ],
            "business_risks": [
                "Risk: ROI not achieved. Mitigation: Clear success metrics and regular reviews",
                "Risk: User adoption issues. Mitigation: Change management and training programs"
            ],
            "compliance_risks": [
                "Risk: Regulatory non-compliance. Mitigation: Legal review and compliance monitoring",
                "Risk: Data privacy violations. Mitigation: Privacy by design and regular audits"
            ],
            "mitigation_timeline": "Ongoing throughout implementation",
            "risk_monitoring": "Monthly risk assessment reviews"
        }
    
    def _define_transformation_success_criteria(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Define overall transformation success criteria."""
        return [
            "AI adoption rate across business units > 60%",
            "Overall operational efficiency improvement > 25%",
            "ROI from AI initiatives > 200% within 18 months",
            f"Successful implementation of at least {min(3, len(recommendations))} AI use cases",
            "Employee satisfaction with AI tools > 75%",
            "Customer satisfaction improvement > 15%"
        ]
    
    async def _calculate_transformation_investment(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total investment required for transformation."""
        total_cost = len(recommendations) * 50000  # Rough estimate
        
        return {
            "total_investment": total_cost,
            "investment_timeline": "12-18 months",
            "expected_roi": f"{(total_cost * 2.5):,.0f}",
            "payback_period": "18-24 months",
            "cost_breakdown": {
                "technology_platforms": f"${total_cost * 0.4:,.0f}",
                "implementation_services": f"${total_cost * 0.3:,.0f}",
                "training_and_change_management": f"${total_cost * 0.2:,.0f}",
                "ongoing_support": f"${total_cost * 0.1:,.0f}"
            }
        }
    
    def _create_timeline_overview(self, phases: List[str]) -> Dict[str, str]:
        """Create high-level timeline overview."""
        timeline = {}
        cumulative_months = 0
        
        phase_durations = {
            "Foundation Building": 3, "Pilot Projects": 4, "Scaling": 6,
            "Quick Wins": 2, "Core Implementations": 5, "Advanced Applications": 6,
            "Immediate Implementations": 3, "Strategic Initiatives": 5, "Innovation Labs": 4
        }
        
        for phase in phases:
            duration = phase_durations.get(phase, 4)
            start_month = cumulative_months + 1
            end_month = cumulative_months + duration
            timeline[phase] = f"Months {start_month}-{end_month}"
            cumulative_months += duration
        
        return timeline
    
    def _calculate_resource_requirements(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate resource requirements for implementation."""
        return {
            "team_composition": {
                "AI/ML Engineers": "2-3 FTE",
                "Data Scientists": "1-2 FTE",
                "Software Engineers": "3-4 FTE",
                "Product Managers": "1-2 FTE",
                "Change Management Specialists": "1 FTE"
            },
            "infrastructure_requirements": {
                "Cloud Computing": "Scalable compute and storage resources",
                "AI/ML Platforms": "MLOps and model deployment infrastructure",
                "Data Infrastructure": "Data lakes, warehouses, and processing pipelines",
                "Security Tools": "AI governance and monitoring solutions"
            },
            "external_support": {
                "AI Consultants": "Strategic guidance and best practices",
                "Technology Vendors": "Platform implementation and support",
                "Training Providers": "AI literacy and technical training"
            }
        }
    
    def _define_governance_structure(self) -> Dict[str, Any]:
        """Define governance structure for AI transformation."""
        return {
            "steering_committee": {
                "composition": ["CTO", "Head of Data", "Business Unit Leaders", "Legal/Compliance"],
                "responsibilities": ["Strategic oversight", "Resource allocation", "Risk management", "Policy approval"],
                "meeting_frequency": "Monthly"
            },
            "ai_center_of_excellence": {
                "composition": ["AI/ML Engineers", "Data Scientists", "Product Managers", "Ethics Officer"],
                "responsibilities": ["Technical standards", "Best practices", "Knowledge sharing", "Ethics oversight"],
                "meeting_frequency": "Weekly"
            },
            "working_groups": {
                "composition": ["Subject matter experts", "End users", "IT support"],
                "responsibilities": ["Use case development", "Testing and validation", "User feedback"],
                "meeting_frequency": "Bi-weekly"
            }
        }
    
    def _define_milestone_tracking(self, phases: List[str]) -> Dict[str, List[str]]:
        """Define milestone tracking for each phase."""
        milestone_map = {
            "Foundation Building": [
                "AI strategy document approved",
                "Governance structure established",
                "Initial team hired and trained"
            ],
            "Pilot Projects": [
                "First pilot project launched",
                "Success metrics defined and tracked",
                "Lessons learned documented"
            ],
            "Scaling": [
                "Multiple use cases in production",
                "ROI targets achieved",
                "Organization-wide adoption metrics met"
            ],
            "Quick Wins": [
                "First quick win delivered",
                "User feedback collected",
                "Success communicated organization-wide"
            ],
            "Core Implementations": [
                "Core AI systems deployed",
                "Integration with existing systems complete",
                "Performance targets achieved"
            ],
            "Advanced Applications": [
                "Advanced AI capabilities deployed",
                "Innovation metrics achieved",
                "Competitive advantage realized"
            ]
        }
        
        return {phase: milestone_map.get(phase, ["Phase objectives achieved"]) for phase in phases}
    
    def _define_implementation_success_metrics(self) -> List[str]:
        """Define success metrics for implementation roadmap."""
        return [
            "On-time delivery of milestones > 90%",
            "Budget adherence within 10% variance",
            "User acceptance rate > 80%",
            "System uptime > 99.5%",
            "Security incidents = 0",
            "Compliance audit pass rate = 100%"
        ]
    
    def _assess_ai_compliance_requirements(self, regulations: List[str]) -> Dict[str, Any]:
        """Assess AI-specific compliance requirements."""
        compliance_map = {
            "GDPR": [
                "Right to explanation for automated decisions",
                "Data minimization for AI training",
                "Consent for AI processing",
                "Data portability for AI-generated insights"
            ],
            "HIPAA": [
                "PHI protection in AI models",
                "Audit trails for AI decisions",
                "Access controls for AI systems",
                "Business associate agreements for AI vendors"
            ],
            "CCPA": [
                "Disclosure of AI decision-making",
                "Opt-out rights for AI processing",
                "Data deletion rights including AI models",
                "Third-party AI vendor disclosures"
            ],
            "SOX": [
                "AI system controls and documentation",
                "Financial reporting AI accuracy",
                "Change management for AI systems",
                "AI audit trails for financial processes"
            ]
        }
        
        applicable_requirements = {}
        for regulation in regulations:
            if regulation in compliance_map:
                applicable_requirements[regulation] = compliance_map[regulation]
        
        return {
            "applicable_regulations": regulations,
            "specific_requirements": applicable_requirements,
            "compliance_priority": "high" if regulations else "medium",
            "recommended_actions": [
                "Conduct AI compliance assessment",
                "Implement AI governance framework",
                "Regular compliance monitoring and reporting"
            ]
        }
    
    def _assess_ai_ethical_risks(self) -> List[Dict[str, Any]]:
        """Assess AI-specific ethical risks."""
        return [
            {
                "risk": "Algorithmic Bias",
                "impact": "high",
                "probability": "medium",
                "mitigation": "Diverse training data, bias testing, fairness metrics",
                "monitoring": "Regular bias audits and fairness assessments"
            },
            {
                "risk": "Lack of Transparency",
                "impact": "medium",
                "probability": "high",
                "mitigation": "Explainable AI, decision audit trails, user education",
                "monitoring": "Explainability metrics and user feedback"
            },
            {
                "risk": "Privacy Violations",
                "impact": "high",
                "probability": "low",
                "mitigation": "Privacy-preserving AI, data anonymization, consent management",
                "monitoring": "Privacy impact assessments and data audits"
            },
            {
                "risk": "Job Displacement",
                "impact": "medium",
                "probability": "medium",
                "mitigation": "Reskilling programs, human-AI collaboration, gradual transition",
                "monitoring": "Employee satisfaction surveys and retention metrics"
            }
        ]
    
    def _create_monitoring_framework(self) -> Dict[str, Any]:
        """Create monitoring framework for AI ethics and governance."""
        return {
            "performance_monitoring": {
                "metrics": ["Accuracy", "Precision", "Recall", "F1-score"],
                "frequency": "Daily",
                "alerts": "Performance degradation > 5%"
            },
            "bias_monitoring": {
                "metrics": ["Demographic parity", "Equal opportunity", "Calibration"],
                "frequency": "Weekly",
                "alerts": "Bias metrics exceed threshold"
            },
            "explainability_monitoring": {
                "metrics": ["Feature importance", "Decision paths", "Confidence scores"],
                "frequency": "Per prediction",
                "alerts": "Low confidence predictions"
            },
            "compliance_monitoring": {
                "metrics": ["Audit trail completeness", "Access control violations", "Data retention compliance"],
                "frequency": "Daily",
                "alerts": "Compliance violations detected"
            }
        }
    
    def _define_training_requirements(self) -> List[Dict[str, Any]]:
        """Define training requirements for AI transformation."""
        return [
            {
                "audience": "All Employees",
                "training": "AI Literacy and Ethics",
                "duration": "4 hours",
                "frequency": "Annual",
                "delivery": "Online modules and workshops"
            },
            {
                "audience": "Managers and Leaders",
                "training": "AI Leadership and Strategy",
                "duration": "8 hours",
                "frequency": "Bi-annual",
                "delivery": "Executive workshops and case studies"
            },
            {
                "audience": "Technical Staff",
                "training": "AI Implementation and Best Practices",
                "duration": "16 hours",
                "frequency": "Quarterly",
                "delivery": "Hands-on workshops and certification programs"
            },
            {
                "audience": "Data and AI Teams",
                "training": "Advanced AI Techniques and Ethics",
                "duration": "40 hours",
                "frequency": "Ongoing",
                "delivery": "Technical training and conference attendance"
            }
        ]
    
    def _generate_business_value_description(self, use_case: str) -> str:
        """Generate business value description for a use case."""
        value_map = {
            "customer_service": "Improved customer satisfaction, reduced response times, and lower support costs through 24/7 AI-powered assistance",
            "content_generation": "Increased content production efficiency, consistent brand voice, and reduced content creation costs",
            "predictive_analytics": "Better decision-making, risk reduction, and revenue optimization through data-driven insights",
            "process_automation": "Streamlined operations, reduced manual errors, and improved employee productivity",
            "document_processing": "Faster document processing, improved accuracy, and reduced manual effort",
            "recommendation_systems": "Enhanced user experience, increased engagement, and improved conversion rates"
        }
        
        return value_map.get(use_case, "Improved operational efficiency and competitive advantage through AI-powered automation")
    
    def _estimate_implementation_time(self, use_case: str, company_size: str) -> str:
        """Estimate implementation time for a use case."""
        base_times = {
            "customer_service": 3,
            "content_generation": 2,
            "predictive_analytics": 6,
            "process_automation": 4,
            "document_processing": 3,
            "recommendation_systems": 5
        }
        base_time = base_times.get(use_case, 3)
        
        size_multipliers = {"startup": 0.8, "small": 0.9, "medium": 1.0, "large": 1.2, "enterprise": 1.5}
        multiplier = size_multipliers.get(company_size, 1.0)
        
        adjusted_time = int(base_time * multiplier)
        return f"{adjusted_time}-{adjusted_time + 2} months"
    
    def _estimate_implementation_cost(self, use_case: str, company_size: str) -> str:
        """Estimate implementation cost for a use case."""
        base_costs = {
            "customer_service": 25000,
            "content_generation": 15000,
            "predictive_analytics": 75000,
            "process_automation": 50000,
            "document_processing": 35000,
            "recommendation_systems": 60000
        }
        base_cost = base_costs.get(use_case, 30000)
        
        size_multipliers = {"startup": 0.7, "small": 0.8, "medium": 1.0, "large": 1.3, "enterprise": 1.8}
        multiplier = size_multipliers.get(company_size, 1.0)
        
        min_cost = int(base_cost * multiplier * 0.8)
        max_cost = int(base_cost * multiplier * 1.5)
        
        return f"${min_cost:,} - ${max_cost:,}"
    
    # Enhanced methods with real market data integration
    
    async def _collect_ai_market_intelligence(self) -> Dict[str, Any]:
        """Collect real-time AI market intelligence and trends."""
        logger.debug("Collecting AI market intelligence")
        
        market_intelligence = {
            "ai_trends": [],
            "success_stories": [],
            "industry_adoption": [],
            "technology_developments": [],
            "market_analysis": [],
            "roi_studies": []
        }
        
        try:
            # Search for AI trends and developments
            trends_search = await self.web_search_client.search(
                "artificial intelligence trends 2024 2025 enterprise adoption generative AI business applications",
                max_results=5
            )
            market_intelligence["ai_trends"] = trends_search.get("results", [])
            
            # Search for AI success stories and case studies
            success_search = await self.web_search_client.search(
                "AI implementation success stories case studies enterprise 2024 ROI business transformation",
                max_results=5
            )
            market_intelligence["success_stories"] = success_search.get("results", [])
            
            # Search for industry-specific AI adoption
            industry_search = await self.web_search_client.search(
                "AI adoption by industry enterprise artificial intelligence implementation rates 2024 2025",
                max_results=5
            )
            market_intelligence["industry_adoption"] = industry_search.get("results", [])
            
            # Search for technology developments
            tech_search = await self.web_search_client.search(
                "AI technology developments machine learning platforms 2024 2025 enterprise solutions",
                max_results=5
            )
            market_intelligence["technology_developments"] = tech_search.get("results", [])
            
            # Search for market analysis
            market_search = await self.web_search_client.search(
                "AI market analysis enterprise spending artificial intelligence investment 2024 2025",
                max_results=5
            )
            market_intelligence["market_analysis"] = market_search.get("results", [])
            
            # Search for ROI studies
            roi_search = await self.web_search_client.search(
                "AI ROI studies return on investment artificial intelligence enterprise business value 2024",
                max_results=3
            )
            market_intelligence["roi_studies"] = roi_search.get("results", [])
            
            logger.info(f"Collected AI market intelligence: {sum(len(v) for v in market_intelligence.values())} sources")
            
        except Exception as e:
            logger.warning(f"Failed to collect some AI market intelligence: {str(e)}")
        
        return market_intelligence
    
    def _prepare_market_context(self, market_intelligence: Dict[str, Any]) -> str:
        """Prepare market intelligence context for LLM analysis."""
        context_parts = []
        
        for category, sources in market_intelligence.items():
            if sources:
                context_parts.append(f"{category.replace('_', ' ').title()}:")
                for source in sources[:3]:  # Limit to top 3 per category
                    title = source.get("title", "")
                    snippet = source.get("snippet", "")
                    context_parts.append(f"- {title}: {snippet[:200]}...")
        
        return "\n".join(context_parts)
    
    def _parse_llm_response(self, response: str, fallback_structure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse LLM response with robust JSON extraction and error handling.
        
        Args:
            response: The raw LLM response
            fallback_structure: Optional fallback structure if parsing fails
            
        Returns:
            Dictionary with parsed response data
        """
        if not response or not response.strip():
            logger.warning("Empty or null LLM response received")
            return fallback_structure or {"error": "Empty response", "analysis": "No data available"}
        
        # Clean the response
        cleaned_response = response.strip()
        
        try:
            # First attempt: direct JSON parsing
            parsed_response = json.loads(cleaned_response)
            
            # Validate that we have a proper dictionary structure
            if not isinstance(parsed_response, dict):
                logger.warning(f"LLM response is not a dictionary: {type(parsed_response)}")
                if fallback_structure:
                    return fallback_structure
                return {"error": "Invalid response format", "raw_response": str(parsed_response)}
            
            return parsed_response
            
        except json.JSONDecodeError:
            logger.warning("Direct JSON parsing failed, attempting regex extraction")
            
            # Second attempt: Extract JSON from markdown or text wrapper
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
                r'(\{.*\})',                   # Any JSON-like structure
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(1).strip()
                        parsed_response = json.loads(json_content)
                        
                        if isinstance(parsed_response, dict):
                            logger.info("Successfully extracted JSON from wrapped response")
                            return parsed_response
                            
                    except json.JSONDecodeError:
                        continue
            
            # Third attempt: Handle nested JSON structures
            try:
                # Look for response wrapper patterns
                if 'response' in cleaned_response.lower():
                    lines = cleaned_response.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            parsed_response = json.loads(line)
                            if isinstance(parsed_response, dict):
                                return parsed_response
                                
            except json.JSONDecodeError:
                pass
            
            # Final attempt: Extract structured data from text
            logger.warning("All JSON parsing attempts failed, falling back to text extraction")
            return self._extract_structured_data_from_text(cleaned_response, fallback_structure)
            
        except Exception as e:
            logger.error(f"Unexpected error during JSON parsing: {str(e)}")
            return fallback_structure or {"error": f"Parsing error: {str(e)}", "raw_response": cleaned_response}
    
    def _extract_structured_data_from_text(self, text: str, fallback_structure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract structured data from text when JSON parsing fails.
        
        Args:
            text: Raw text to extract data from
            fallback_structure: Optional fallback structure if extraction fails
            
        Returns:
            Dictionary with extracted structured data
        """
        # Start with fallback structure if provided
        result = fallback_structure.copy() if fallback_structure else {}
        
        # Always include the raw text for reference
        result["raw_analysis"] = text
        result["extracted_points"] = []
        result["parsing_fallback"] = True
        
        try:
            # Extract numbered points and bullet points
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '-', '•', '*'))):
                    result["extracted_points"].append(line)
            
            # Try to identify key sections
            sections = {}
            current_section = None
            section_content = []
            
            for line in lines:
                line = line.strip()
                if line.endswith(':') and len(line.split()) <= 4:
                    # Likely a section header
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                    current_section = line.rstrip(':').lower().replace(' ', '_')
                    section_content = []
                elif current_section and line:
                    section_content.append(line)
            
            # Add final section
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content)
            
            if sections:
                result["extracted_sections"] = sections
            
            # Set analysis field if not in fallback structure
            if "analysis" not in result:
                result["analysis"] = text[:500] + "..." if len(text) > 500 else text
                
        except Exception as e:
            logger.error(f"Error in text extraction: {str(e)}")
            result["extraction_error"] = str(e)
        
        return result
    
    async def _analyze_business_processes_with_market_data(self, market_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze business processes with real market data and trends.
        
        Args:
            market_intelligence: Current AI market intelligence data
            
        Returns:
            Dictionary containing enhanced business process analysis
        """
        try:
            # Get base business process analysis
            base_analysis = await self._analyze_business_processes()
            
            assessment_data = self.current_assessment.dict() if self.current_assessment else {}
            business_req = assessment_data.get("business_requirements", {})
            
            # Prepare market context for analysis
            market_context = self._prepare_market_context(market_intelligence)
            
            analysis_prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

Analyze business processes and identify AI transformation opportunities based on current market trends:

BUSINESS CONTEXT:
- Industry: {business_req.get('industry', 'Not specified')}
- Company Size: {business_req.get('company_size', 'Not specified')}
- Current Processes: {business_req.get('current_processes', [])}
- Pain Points: {business_req.get('pain_points', [])}
- Goals: {business_req.get('goals', [])}

CURRENT AI MARKET INTELLIGENCE:
{market_context}

Based on this information, provide comprehensive analysis across all dimensions.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "process_efficiency": {{
    "current_maturity_score": 0-100,
    "identified_bottlenecks": ["bottleneck1", "bottleneck2"],
    "efficiency_gaps": ["gap1", "gap2"],
    "improvement_potential": "high/medium/low"
  }},
  "ai_ready_processes": [
    {{
      "process_name": "Process Name",
      "readiness_score": 0-100,
      "ai_applications": ["application1", "application2"],
      "implementation_priority": "high/medium/low"
    }}
  ],
  "automation_opportunities": [
    {{
      "opportunity_name": "Opportunity Name",
      "impact_level": "high/medium/low",
      "complexity": "low/medium/high",
      "estimated_savings": "Savings estimate",
      "timeline": "Implementation timeline"
    }}
  ],
  "data_readiness": {{
    "quality_score": 0-100,
    "availability": "excellent/good/fair/poor",
    "gaps": ["gap1", "gap2"],
    "preparation_needed": ["requirement1", "requirement2"]
  }},
  "standardization_needs": [
    {{
      "area": "Area name",
      "priority": "high/medium/low",
      "effort_required": "low/medium/high",
      "expected_timeline": "Timeline estimate"
    }}
  ],
  "change_management": {{
    "resistance_level": "high/medium/low",
    "key_stakeholders": ["stakeholder1", "stakeholder2"],
    "training_needs": ["need1", "need2"],
    "communication_strategy": "Strategy description"
  }},
  "roi_analysis": {{
    "quick_wins": [
      {{
        "initiative": "Initiative name",
        "investment": "Investment estimate",
        "payback_period": "Timeline",
        "expected_roi": "ROI percentage"
      }}
    ],
    "strategic_investments": [
      {{
        "initiative": "Initiative name", 
        "investment": "Investment estimate",
        "payback_period": "Timeline",
        "expected_roi": "ROI percentage"
      }}
    ]
  }},
  "implementation_timeline": {{
    "phase_1_quick_wins": {{
      "duration": "Timeline",
      "key_activities": ["activity1", "activity2"],
      "success_metrics": ["metric1", "metric2"]
    }},
    "phase_2_core_implementations": {{
      "duration": "Timeline",
      "key_activities": ["activity1", "activity2"],
      "success_metrics": ["metric1", "metric2"]
    }},
    "phase_3_advanced_ai": {{
      "duration": "Timeline", 
      "key_activities": ["activity1", "activity2"],
      "success_metrics": ["metric1", "metric2"]
    }}
  }}
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""
            
            llm_response = await self._call_llm(
                prompt=analysis_prompt,
                system_prompt="You are a business process analyst and AI transformation consultant with expertise in identifying AI opportunities across various industries. You MUST respond with ONLY valid JSON. Do not include any text before, after, or around the JSON. Only return the JSON object.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Create fallback structure for business process analysis
            fallback_structure = {
                "process_efficiency": {"current_maturity_score": 50, "identified_bottlenecks": [], "efficiency_gaps": [], "improvement_potential": "medium"},
                "ai_ready_processes": [],
                "automation_opportunities": [],
                "data_readiness": {"quality_score": 50, "availability": "fair", "gaps": [], "preparation_needed": []},
                "standardization_needs": [],
                "change_management": {"resistance_level": "medium", "key_stakeholders": [], "training_needs": [], "communication_strategy": "Standard change management approach"},
                "roi_analysis": {"quick_wins": [], "strategic_investments": []},
                "implementation_timeline": {
                    "phase_1_quick_wins": {"duration": "3-6 months", "key_activities": [], "success_metrics": []},
                    "phase_2_core_implementations": {"duration": "6-12 months", "key_activities": [], "success_metrics": []},
                    "phase_3_advanced_ai": {"duration": "12-18 months", "key_activities": [], "success_metrics": []}
                }
            }
            
            llm_analysis = self._parse_llm_response(llm_response, fallback_structure)
            
            # Enhance base analysis with market insights
            enhanced_analysis = {
                **base_analysis,
                "process_efficiency": llm_analysis.get("process_efficiency", {}),
                "ai_ready_processes": llm_analysis.get("ai_ready_processes", []),
                "automation_opportunities": llm_analysis.get("automation_opportunities", []),
                "data_readiness": llm_analysis.get("data_readiness", {}),
                "standardization_needs": llm_analysis.get("standardization_needs", []),
                "change_management": llm_analysis.get("change_management", {}),
                "roi_analysis": llm_analysis.get("roi_analysis", {}),
                "implementation_timeline": llm_analysis.get("implementation_timeline", {}),
                "market_insights": llm_analysis.get("analysis", ""),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.warning(f"Enhanced business process analysis failed: {str(e)}")
            return await self._analyze_business_processes()
    
    async def _identify_ai_opportunities_with_trends(self, market_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify AI opportunities using current market trends and success stories.
        
        Args:
            market_intelligence: Current AI market intelligence data
            
        Returns:
            Dictionary containing AI opportunities with market validation
        """
        try:
            assessment_data = self.current_assessment.dict() if self.current_assessment else {}
            business_req = assessment_data.get("business_requirements", {})
            
            # Prepare market context
            market_context = self._prepare_market_context(market_intelligence)
            
            opportunities_prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

Identify AI opportunities based on business context and current market trends:

BUSINESS PROFILE:
- Industry: {business_req.get('industry', 'Not specified')}
- Company Size: {business_req.get('company_size', 'Not specified')}
- Budget Range: {business_req.get('budget_range', 'Not specified')}
- Technical Maturity: {business_req.get('technical_maturity', 'Not specified')}
- Goals: {business_req.get('goals', [])}
- Current Challenges: {business_req.get('pain_points', [])}

CURRENT AI MARKET TRENDS:
{market_context}

Identify specific AI opportunities across all categories with detailed analysis.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "quick_wins": [
    {{
      "opportunity_name": "Opportunity Name",
      "business_value": "Value description",
      "implementation_complexity": "low/medium/high",
      "resource_requirements": "Resource description",
      "estimated_timeline": "Timeline",
      "estimated_cost": "Cost range",
      "success_metrics": ["metric1", "metric2"],
      "market_validation": "Validation example"
    }}
  ],
  "strategic_initiatives": [
    {{
      "initiative_name": "Initiative Name",
      "business_value": "Value description",
      "implementation_complexity": "low/medium/high",
      "resource_requirements": "Resource description",
      "estimated_timeline": "Timeline",
      "estimated_cost": "Cost range",
      "success_metrics": ["metric1", "metric2"],
      "competitive_advantage": "Advantage description"
    }}
  ],
  "industry_specific": [
    {{
      "application_name": "Application Name",
      "industry_relevance": "Relevance description",
      "business_impact": "high/medium/low",
      "implementation_approach": "Approach description",
      "success_examples": ["example1", "example2"]
    }}
  ],
  "competitive_advantage": [
    {{
      "advantage_area": "Area description",
      "differentiation_factor": "Factor description",
      "market_positioning": "Positioning description",
      "implementation_priority": "high/medium/low"
    }}
  ],
  "cost_reduction": [
    {{
      "cost_area": "Cost area",
      "reduction_potential": "Percentage or amount",
      "implementation_effort": "Effort description",
      "payback_period": "Timeline",
      "automation_scope": "Scope description"
    }}
  ],
  "revenue_generation": [
    {{
      "revenue_opportunity": "Opportunity description",
      "revenue_potential": "Amount or percentage",
      "market_size": "Market description",
      "implementation_requirements": "Requirements description",
      "go_to_market_strategy": "Strategy description"
    }}
  ],
  "customer_experience": [
    {{
      "enhancement_area": "Area description",
      "customer_impact": "Impact description",
      "implementation_approach": "Approach description",
      "success_metrics": ["metric1", "metric2"],
      "differentiation_value": "Value description"
    }}
  ],
  "operational_efficiency": [
    {{
      "efficiency_area": "Area description",
      "improvement_potential": "Percentage or description",
      "automation_level": "Level description",
      "resource_impact": "Impact description",
      "scalability_factor": "Factor description"
    }}
  ]
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""
            
            llm_response = await self._call_llm(
                prompt=opportunities_prompt,
                system_prompt="You are an AI strategy consultant with expertise in identifying high-value AI opportunities across various industries and business models. You MUST respond with ONLY valid JSON. Do not include any text before, after, or around the JSON. Only return the JSON object.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Create fallback structure for AI opportunities
            fallback_structure = {
                "quick_wins": [],
                "strategic_initiatives": [],
                "industry_specific": [],
                "competitive_advantage": [],
                "cost_reduction": [],
                "revenue_generation": [],
                "customer_experience": [],
                "operational_efficiency": []
            }
            
            opportunities_analysis = self._parse_llm_response(llm_response, fallback_structure)
            
            return {
                "quick_wins": opportunities_analysis.get("quick_wins", []),
                "strategic_initiatives": opportunities_analysis.get("strategic_initiatives", []),
                "industry_specific": opportunities_analysis.get("industry_specific", []),
                "competitive_advantage": opportunities_analysis.get("competitive_advantage", []),
                "cost_reduction": opportunities_analysis.get("cost_reduction", []),
                "revenue_generation": opportunities_analysis.get("revenue_generation", []),
                "customer_experience": opportunities_analysis.get("customer_experience", []),
                "operational_efficiency": opportunities_analysis.get("operational_efficiency", []),
                "market_validation": market_intelligence.get("success_stories", []),
                "trends_context": market_intelligence.get("trends", []),
                "opportunities_insights": opportunities_analysis.get("analysis", ""),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.warning(f"AI opportunities identification failed: {str(e)}")
            return {
                "quick_wins": ["Chatbot implementation", "Process automation"],
                "strategic_initiatives": ["Predictive analytics platform"],
                "error": str(e),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _assess_ai_readiness_with_benchmarks(self, market_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess AI readiness using industry benchmarks and market data.
        
        Args:
            market_intelligence: Current AI market intelligence data
            
        Returns:
            Dictionary containing AI readiness assessment with benchmarks
        """
        try:
            assessment_data = self.current_assessment.dict() if self.current_assessment else {}
            business_req = assessment_data.get("business_requirements", {})
            technical_req = assessment_data.get("technical_requirements", {})
            
            # Prepare benchmark context
            benchmark_context = self._prepare_benchmark_context(market_intelligence)
            
            readiness_prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

Assess AI readiness against industry benchmarks and best practices:

CURRENT STATE:
- Industry: {business_req.get('industry', 'Not specified')}
- Company Size: {business_req.get('company_size', 'Not specified')}
- Technical Infrastructure: {technical_req.get('existing_infrastructure', 'Not specified')}
- Data Maturity: {business_req.get('data_maturity', 'Not specified')}
- Team Skills: {business_req.get('technical_expertise', 'Not specified')}
- Budget Allocation: {business_req.get('budget_range', 'Not specified')}

INDUSTRY BENCHMARKS:
{benchmark_context}

Assess readiness across all dimensions with specific scores and detailed analysis.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "data_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "technical_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "team_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "culture_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "governance_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "budget_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "leadership_readiness": {{
    "score": 0-100,
    "level": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "improvement_actions": ["action1", "action2"]
  }},
  "overall_score": 0-100,
  "gap_analysis": {{
    "critical_gaps": ["gap1", "gap2"],
    "moderate_gaps": ["gap1", "gap2"],
    "minor_gaps": ["gap1", "gap2"],
    "priorities": ["priority1", "priority2"]
  }},
  "improvement_plan": [
    {{
      "area": "Area name",
      "priority": "high/medium/low",
      "timeline": "Timeline estimate",
      "effort": "low/medium/high",
      "expected_impact": "Impact description"
    }}
  ]
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""
            
            llm_response = await self._call_llm(
                prompt=readiness_prompt,
                system_prompt="You are an AI transformation consultant expert at assessing organizational readiness for AI initiatives using industry benchmarks. You MUST respond with ONLY valid JSON. Do not include any text before, after, or around the JSON. Only return the JSON object.",
                temperature=0.1,
                max_tokens=2500
            )
            
            # Create fallback structure for AI readiness assessment
            fallback_structure = {
                "data_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "technical_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "team_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "culture_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "governance_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "budget_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "leadership_readiness": {"score": 50, "level": "fair", "strengths": [], "gaps": [], "improvement_actions": []},
                "overall_score": 50,
                "gap_analysis": {"critical_gaps": [], "moderate_gaps": [], "minor_gaps": [], "priorities": []},
                "improvement_plan": []
            }
            
            readiness_analysis = self._parse_llm_response(llm_response, fallback_structure)
            
            return {
                "data_readiness": readiness_analysis.get("data_readiness", {}),
                "technical_readiness": readiness_analysis.get("technical_readiness", {}),
                "team_readiness": readiness_analysis.get("team_readiness", {}),
                "culture_readiness": readiness_analysis.get("culture_readiness", {}),
                "governance_readiness": readiness_analysis.get("governance_readiness", {}),
                "budget_readiness": readiness_analysis.get("budget_readiness", {}),
                "leadership_readiness": readiness_analysis.get("leadership_readiness", {}),
                "overall_score": readiness_analysis.get("overall_score", 0),
                "gap_analysis": readiness_analysis.get("gap_analysis", {}),
                "improvement_plan": readiness_analysis.get("improvement_plan", []),
                "benchmark_data": market_intelligence.get("benchmarks", {}),
                "readiness_insights": readiness_analysis.get("analysis", ""),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.warning(f"AI readiness assessment failed: {str(e)}")
            return {
                "overall_score": 0,
                "gap_analysis": {"error": "Assessment unavailable"},
                "improvement_plan": ["Conduct manual readiness assessment"],
                "error": str(e),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _prepare_market_context(self, market_intelligence: Dict[str, Any]) -> str:
        """Prepare market context for LLM analysis."""
        context_parts = []
        
        # Add AI trends
        trends = market_intelligence.get("ai_trends", [])
        if trends:
            context_parts.append("Current AI Trends:")
            for trend in trends[:5]:  # Limit to top 5
                title = trend.get("title", "")
                snippet = trend.get("snippet", "")
                context_parts.append(f"- {title}: {snippet[:150]}...")
        
        # Add success stories
        success_stories = market_intelligence.get("success_stories", [])
        if success_stories:
            context_parts.append("\nAI Success Stories:")
            for story in success_stories[:3]:  # Limit to top 3
                title = story.get("title", "")
                snippet = story.get("snippet", "")
                context_parts.append(f"- {title}: {snippet[:150]}...")
        
        return "\n".join(context_parts)
    
    def _prepare_benchmark_context(self, market_intelligence: Dict[str, Any]) -> str:
        """Prepare benchmark context for LLM analysis."""
        context_parts = []
        
        # Add industry benchmarks
        benchmarks = market_intelligence.get("industry_benchmarks", [])
        if benchmarks:
            context_parts.append("Industry AI Benchmarks:")
            for benchmark in benchmarks[:3]:
                title = benchmark.get("title", "")
                snippet = benchmark.get("snippet", "")
                context_parts.append(f"- {title}: {snippet[:150]}...")
        
        return "\n".join(context_parts)
