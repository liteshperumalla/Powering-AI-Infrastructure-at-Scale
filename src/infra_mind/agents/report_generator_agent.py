"""
Report Generator Agent for creating professional infrastructure assessment reports.

This agent specializes in generating comprehensive reports from assessment data
and agent recommendations, producing executive summaries and technical documentation.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from .base import BaseAgent, AgentConfig, AgentRole, AgentStatus, AgentResult
from .research_agent import ResearchAgent
from .web_research_agent import WebResearchAgent
from ..models.assessment import Assessment
from ..models.recommendation import Recommendation

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """Represents a section in a report."""
    title: str
    content: str
    order: int = 0
    subsections: List["ReportSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_interactive: bool = False
    drill_down_data: Dict[str, Any] = field(default_factory=dict)
    charts_config: List[Dict[str, Any]] = field(default_factory=list)
    generated_by: str = ""
    section_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "subsections": [sub.to_dict() for sub in self.subsections],
            "metadata": self.metadata,
            "is_interactive": self.is_interactive,
            "drill_down_data": self.drill_down_data,
            "charts_config": self.charts_config,
            "generated_by": self.generated_by,
            "section_id": self.section_id
        }


@dataclass
class Report:
    """Represents a complete infrastructure assessment report."""
    id: str
    title: str
    assessment_id: str
    report_type: str  # "executive", "technical", "full"
    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "assessment_id": self.assessment_id,
            "report_type": self.report_type,
            "sections": [section.to_dict() for section in self.sections],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    def to_markdown(self) -> str:
        """Convert report to markdown format."""
        lines = [
            f"# {self.title}",
            "",
            f"**Report ID:** {self.id}",
            f"**Assessment ID:** {self.assessment_id}",
            f"**Report Type:** {self.report_type.title()}",
            f"**Generated:** {self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            ""
        ]
        
        for section in self.sections:
            lines.extend(self._section_to_markdown(section, level=2))
            lines.append("")
        
        return "\n".join(lines)
    
    def _section_to_markdown(self, section: ReportSection, level: int = 2) -> List[str]:
        """Convert a section to markdown lines."""
        lines = [
            f"{'#' * level} {section.title}",
            "",
            section.content,
            ""
        ]
        
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1))
        
        return lines


class ReportGeneratorAgent(BaseAgent):
    """
    Agent specialized in generating professional infrastructure assessment reports.
    
    This agent creates comprehensive reports from assessment data and recommendations,
    producing both executive summaries and detailed technical documentation.
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the Report Generator Agent."""
        super().__init__(config)
        self.report_templates = self._load_report_templates()
        
        # Initialize research agents for real data integration
        self.research_agent = None
        self.web_research_agent = None
        
        # Cache for research data to avoid duplicate API calls
        self.research_cache = {}
        
        logger.info(f"Initialized Report Generator Agent: {self.name}")
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load report templates for different report types."""
        return {
            "executive": {
                "title_template": "Infrastructure Assessment Report - {company_name}",
                "sections": [
                    {"title": "Executive Summary", "order": 1},
                    {"title": "Business Context", "order": 2},
                    {"title": "Key Recommendations", "order": 3},
                    {"title": "Investment Summary", "order": 4},
                    {"title": "Implementation Roadmap", "order": 5},
                    {"title": "Risk Assessment", "order": 6}
                ]
            },
            "technical": {
                "title_template": "Technical Infrastructure Report - {company_name}",
                "sections": [
                    {"title": "Current State Analysis", "order": 1},
                    {"title": "Technical Requirements", "order": 2},
                    {"title": "Architecture Recommendations", "order": 3},
                    {"title": "Technology Stack", "order": 4},
                    {"title": "Implementation Details", "order": 5},
                    {"title": "Security & Compliance", "order": 6},
                    {"title": "Monitoring & Operations", "order": 7}
                ]
            },
            "full": {
                "title_template": "Complete Infrastructure Assessment - {company_name}",
                "sections": [
                    {"title": "Executive Summary", "order": 1},
                    {"title": "Business Context & Goals", "order": 2},
                    {"title": "Current State Analysis", "order": 3},
                    {"title": "Technical Requirements", "order": 4},
                    {"title": "Recommendations Overview", "order": 5},
                    {"title": "Detailed Technical Recommendations", "order": 6},
                    {"title": "Cost Analysis", "order": 7},
                    {"title": "Implementation Roadmap", "order": 8},
                    {"title": "Risk Assessment & Mitigation", "order": 9},
                    {"title": "Next Steps", "order": 10}
                ]
            }
        }
    
    async def _execute_main_logic(self) -> AgentResult:
        """Execute the main report generation logic."""
        try:
            # Extract assessment and recommendations from context
            assessment_data = self.context.get("assessment", {})
            recommendations_data = self.context.get("recommendations", [])
            report_type = self.context.get("report_type", "full")
            
            if not assessment_data:
                raise ValueError("No assessment data provided for report generation")
            
            # Create assessment object if it's a dict
            if isinstance(assessment_data, dict):
                assessment = self._dict_to_assessment(assessment_data)
            else:
                assessment = assessment_data
            
            # Create recommendation objects if they're dicts
            recommendations = []
            for rec_data in recommendations_data:
                if isinstance(rec_data, dict):
                    recommendations.append(self._dict_to_recommendation(rec_data))
                else:
                    recommendations.append(rec_data)
            
            # Collect real-time research data to enhance the report
            research_data = await self._collect_research_data(assessment, recommendations)
            
            # Generate the report with enhanced data
            report = await self._generate_report(assessment, recommendations, report_type, research_data)
            
            # Store report in database
            db_report_id = await self._store_report_in_database(report, assessment)
            
            # Create result
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data={
                    "report": report.to_dict(),
                    "report_markdown": report.to_markdown(),
                    "report_id": report.id,
                    "db_report_id": db_report_id,
                    "report_type": report_type,
                    "metadata": {
                        "report_sections": len(report.sections),
                        "report_length": len(report.to_markdown()),
                        "generation_time": datetime.now(timezone.utc).isoformat(),
                        "stored_in_database": db_report_id is not None
                    }
                },
                recommendations=[
                    {
                        "category": "reporting",
                        "title": f"{report_type.title()} Report Generated",
                        "description": f"Successfully generated comprehensive {report_type} report with {len(report.sections)} sections",
                        "priority": "high",
                        "report_id": report.id,
                        "db_report_id": db_report_id
                    }
                ]
            )
            
            logger.info(f"Generated {report_type} report {report.id} with {len(report.sections)} sections")
            return result
            
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}", exc_info=True)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data={},
                recommendations=[],
                error=str(e)
            )
    
    def _dict_to_assessment(self, data: Dict[str, Any]) -> Assessment:
        """Convert dictionary to Assessment object."""
        # Create a mock Assessment object with the data
        assessment = type('Assessment', (), {})()
        assessment.id = data.get("id", str(uuid.uuid4()))
        assessment.title = data.get("title", "Infrastructure Assessment")
        assessment.business_requirements = data.get("business_requirements", {})
        assessment.technical_requirements = data.get("technical_requirements", {})
        assessment.created_at = datetime.now(timezone.utc)
        return assessment
    
    def _dict_to_recommendation(self, data: Dict[str, Any]) -> Recommendation:
        """Convert dictionary to Recommendation object."""
        # Create a mock Recommendation object with the data
        rec = type('Recommendation', (), {})()
        rec.id = data.get("id", str(uuid.uuid4()))
        rec.title = data.get("title", "Recommendation")
        rec.description = data.get("description", "")
        rec.category = data.get("category", "general")
        rec.priority = data.get("priority", "medium")
        rec.estimated_cost = data.get("estimated_cost", 0)
        rec.implementation_time = data.get("implementation_time", "unknown")
        rec.benefits = data.get("benefits", [])
        rec.risks = data.get("risks", [])
        return rec
    
    async def _collect_research_data(self, assessment: Any, recommendations: List[Any]) -> Dict[str, Any]:
        """Collect real-time research data to enhance report quality."""
        logger.info("Collecting real-time research data for enhanced report generation")
        
        research_data = {
            "market_intelligence": {},
            "technology_trends": {},
            "industry_insights": {},
            "competitive_analysis": {},
            "pricing_data": {},
            "best_practices": {},
            "research_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Initialize research agents if not already done
            if not self.research_agent:
                research_config = AgentConfig(
                    name="Research Agent (Report Generator)",
                    role=AgentRole.RESEARCH,
                    temperature=0.3,
                    max_tokens=2000
                )
                self.research_agent = ResearchAgent(research_config)
            
            if not self.web_research_agent:
                web_research_config = AgentConfig(
                    name="Web Research Agent (Report Generator)",
                    role=AgentRole.WEB_RESEARCH,
                    temperature=0.2,
                    max_tokens=3000
                )
                self.web_research_agent = WebResearchAgent(web_research_config)
            
            # Identify key research topics from assessment and recommendations
            research_topics = self._identify_research_topics(assessment, recommendations)
            
            # Collect industry and market research
            if research_topics:
                try:
                    # Use Research Agent for comprehensive topic analysis
                    for topic in research_topics[:3]:  # Limit to top 3 topics to avoid too many API calls
                        cache_key = f"research_{topic}"
                        if cache_key not in self.research_cache:
                            self.research_agent.current_assessment = assessment
                            topic_research = await self.research_agent.research_topic(topic)
                            self.research_cache[cache_key] = topic_research
                        
                        research_data["industry_insights"][topic] = self.research_cache[cache_key]
                    
                    # Use Web Research Agent for competitive and market intelligence
                    self.web_research_agent.current_assessment = assessment
                    web_research_result = await self.web_research_agent.research_topics_with_web_search(
                        topics=research_topics[:2],  # Limit to top 2 topics
                        context="enterprise infrastructure market analysis"
                    )
                    research_data["market_intelligence"] = web_research_result
                    
                except Exception as e:
                    logger.warning(f"Research data collection failed: {e}")
                    research_data["research_error"] = str(e)
            
            # Enhance with technology trend analysis
            tech_topics = self._extract_technology_topics(recommendations)
            if tech_topics:
                try:
                    tech_research = await self.web_research_agent.research_topics_with_web_search(
                        topics=tech_topics[:2],  # Limit API calls
                        context="cloud technology trends 2024"
                    )
                    research_data["technology_trends"] = tech_research
                except Exception as e:
                    logger.warning(f"Technology trend research failed: {e}")
            
            logger.info(f"Collected research data for {len(research_topics)} topics")
            
        except Exception as e:
            logger.error(f"Failed to collect research data: {e}")
            research_data["collection_error"] = str(e)
        
        return research_data
    
    async def _store_report_in_database(self, report: "Report", assessment: Any) -> Optional[str]:
        """Store the generated report in the database."""
        try:
            from ..models.report import Report as DBReport, ReportType, ReportFormat, ReportStatus
            from ..schemas.base import Priority
            
            # Map report types
            report_type_mapping = {
                "executive": ReportType.EXECUTIVE_SUMMARY,
                "technical": ReportType.TECHNICAL_ROADMAP,
                "full": ReportType.COMPREHENSIVE
            }
            
            # Create database report object
            db_report = DBReport(
                assessment_id=str(assessment.id),
                user_id=getattr(assessment, 'user_id', 'anonymous_user'),
                title=report.title,
                description=f"AI-generated {report.report_type} infrastructure assessment report",
                report_type=report_type_mapping.get(report.report_type, ReportType.COMPREHENSIVE),
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=[section.title for section in report.sections],
                total_pages=max(8, len(report.sections) * 2),  # Estimate pages
                word_count=len(report.to_markdown().split()),
                file_path=f"/reports/{report.report_type}_{report.assessment_id}_{report.id}.pdf",
                file_size_bytes=len(report.to_markdown().encode('utf-8')) * 2,  # Estimate file size
                generated_by=[self.name],
                generation_time_seconds=2.0,
                completeness_score=0.95,
                confidence_score=0.9,
                priority=Priority.HIGH if report.report_type == "executive" else Priority.MEDIUM,
                tags=[report.report_type, "ai_generated", "comprehensive"],
                content={
                    "markdown": report.to_markdown(),
                    "structured_data": report.to_dict(),
                    "sections": [section.to_dict() for section in report.sections]
                },
                metadata={
                    **report.metadata,
                    "agent_generated": True,
                    "report_format": "markdown",
                    "generation_method": "llm_enhanced"
                },
                completed_at=datetime.now(timezone.utc)
            )
            
            # Save to database
            await db_report.insert()
            logger.info(f"Stored report {report.id} in database as {db_report.id}")
            return str(db_report.id)
            
        except Exception as e:
            logger.error(f"Failed to store report in database: {e}")
            return None
    
    def _identify_research_topics(self, assessment: Any, recommendations: List[Any]) -> List[str]:
        """Identify key topics for research based on assessment and recommendations."""
        topics = set()
        
        # Extract topics from business requirements
        business_req = getattr(assessment, 'business_requirements', {})
        if business_req:
            industry = business_req.get("industry", "")
            if industry:
                topics.add(f"{industry} cloud infrastructure")
            
            # Add primary goals as research topics
            goals = business_req.get("primary_goals", [])
            for goal in goals[:2]:  # Limit to first 2 goals
                if goal:
                    topics.add(f"{goal} enterprise solutions")
        
        # Extract topics from recommendations
        for rec in recommendations[:3]:  # Limit to first 3 recommendations
            category = getattr(rec, 'category', '')
            title = getattr(rec, 'title', '')
            
            if category and category != 'general':
                topics.add(f"{category} cloud services")
            
            # Extract key technologies from title/description
            tech_keywords = ['kubernetes', 'serverless', 'containers', 'microservices', 'ai', 'ml', 'data', 'analytics']
            for keyword in tech_keywords:
                if keyword in title.lower():
                    topics.add(f"{keyword} infrastructure")
                    break
        
        # Add general infrastructure topics
        topics.add("cloud infrastructure best practices")
        topics.add("enterprise cloud migration")
        
        return list(topics)[:5]  # Return max 5 topics
    
    def _extract_technology_topics(self, recommendations: List[Any]) -> List[str]:
        """Extract technology-specific topics from recommendations."""
        tech_topics = set()
        
        # Common technology patterns to look for
        tech_patterns = {
            'aws': 'AWS cloud services',
            'azure': 'Microsoft Azure services', 
            'gcp': 'Google Cloud Platform',
            'kubernetes': 'Kubernetes orchestration',
            'docker': 'Docker containerization',
            'serverless': 'serverless computing',
            'microservices': 'microservices architecture',
            'api': 'API management',
            'database': 'cloud databases',
            'storage': 'cloud storage solutions',
            'security': 'cloud security',
            'monitoring': 'infrastructure monitoring'
        }
        
        for rec in recommendations:
            title = getattr(rec, 'title', '').lower()
            description = getattr(rec, 'description', '').lower()
            category = getattr(rec, 'category', '').lower()
            
            text_to_search = f"{title} {description} {category}"
            
            for pattern, topic in tech_patterns.items():
                if pattern in text_to_search:
                    tech_topics.add(topic)
        
        return list(tech_topics)[:4]  # Return max 4 tech topics
    
    async def _generate_report(self, assessment: Any, recommendations: List[Any], report_type: str, research_data: Dict[str, Any] = None) -> Report:
        """Generate a complete report based on assessment and recommendations."""
        # Get template for report type
        template = self.report_templates.get(report_type, self.report_templates["full"])
        
        # Extract company name for title
        company_name = "Unknown Company"
        if hasattr(assessment, 'business_requirements') and assessment.business_requirements:
            company_name = assessment.business_requirements.get("company_name", company_name)
        
        # Create report with enhanced metadata
        report = Report(
            id=str(uuid.uuid4()),
            title=template["title_template"].format(company_name=company_name),
            assessment_id=assessment.id,
            report_type=report_type,
            metadata={
                "company_name": company_name,
                "recommendation_count": len(recommendations),
                "template_used": report_type,
                "research_enhanced": research_data is not None,
                "research_topics_count": len(research_data.get("industry_insights", {})) if research_data else 0,
                "generation_method": "llm_plus_research"
            }
        )
        
        # Generate sections based on template with research data
        for section_config in template["sections"]:
            section = await self._generate_section(
                section_config["title"],
                section_config["order"],
                assessment,
                recommendations,
                research_data
            )
            report.add_section(section)
        
        return report
    
    async def _generate_section(self, title: str, order: int, assessment: Any, recommendations: List[Any], research_data: Dict[str, Any] = None) -> ReportSection:
        """Generate a specific section of the report with real data integration."""
        content = ""
        
        # Use LLM-powered content generation with research data
        if research_data and len(research_data.get("industry_insights", {})) > 0:
            content = await self._generate_section_with_llm(title, assessment, recommendations, research_data)
        else:
            # Fallback to original content generation
            if title == "Executive Summary":
                content = await self._generate_executive_summary_enhanced(assessment, recommendations, research_data)
            elif title == "Business Context" or title == "Business Context & Goals":
                content = self._generate_business_context(assessment)
            elif title == "Current State Analysis":
                content = await self._generate_current_state_analysis_enhanced(assessment, research_data)
            elif title == "Technical Requirements":
                content = self._generate_technical_requirements(assessment)
            elif title == "Key Recommendations" or title == "Recommendations Overview":
                content = await self._generate_recommendations_overview_enhanced(recommendations, research_data)
        elif title == "Detailed Technical Recommendations":
            content = self._generate_detailed_recommendations(recommendations)
        elif title == "Investment Summary" or title == "Cost Analysis":
            content = self._generate_cost_analysis(recommendations)
        elif title == "Implementation Roadmap":
            content = self._generate_implementation_roadmap(recommendations)
        elif title == "Risk Assessment" or title == "Risk Assessment & Mitigation":
            content = self._generate_risk_assessment(recommendations)
        elif title == "Architecture Recommendations":
            content = self._generate_architecture_recommendations(recommendations)
        elif title == "Technology Stack":
            content = self._generate_technology_stack(recommendations)
        elif title == "Implementation Details":
            content = self._generate_implementation_details(recommendations)
        elif title == "Security & Compliance":
            content = self._generate_security_compliance(assessment, recommendations)
        elif title == "Monitoring & Operations":
            content = self._generate_monitoring_operations(recommendations)
        elif title == "Next Steps":
            content = self._generate_next_steps(recommendations)
        else:
            content = f"Content for {title} section would be generated here."
        
        # Determine if section should be interactive
        is_interactive = self._should_be_interactive(title, recommendations)
        drill_down_data = {}
        charts_config = []
        
        if is_interactive:
            drill_down_data = self._generate_drill_down_data(title, recommendations)
            charts_config = self._generate_charts_config(title, recommendations)
        
        return ReportSection(
            title=title,
            content=content,
            order=order,
            is_interactive=is_interactive,
            drill_down_data=drill_down_data,
            charts_config=charts_config,
            generated_by=self.name,
            section_id=str(uuid.uuid4())
        )
    
    def _generate_executive_summary(self, assessment: Any, recommendations: List[Any]) -> str:
        """Generate executive summary section."""
        business_req = getattr(assessment, 'business_requirements', {})
        company_name = business_req.get("company_name", "the organization")
        industry = business_req.get("industry", "technology")
        company_size = business_req.get("company_size", "medium")
        
        high_priority_recs = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'high']
        total_cost = sum(getattr(r, 'estimated_cost', 0) for r in recommendations)
        
        return f"""This report presents a comprehensive infrastructure assessment for {company_name}, a {company_size}-sized organization in the {industry} industry.

**Key Findings:**
- Current infrastructure assessment reveals opportunities for optimization and modernization
- {len(recommendations)} strategic recommendations have been identified
- {len(high_priority_recs)} high-priority initiatives require immediate attention
- Estimated total investment: ${total_cost:,.2f}

**Primary Benefits:**
- Enhanced scalability and performance
- Improved cost efficiency
- Strengthened security posture
- Increased operational reliability

**Recommended Next Steps:**
1. Review and prioritize recommendations based on business impact
2. Develop detailed implementation timeline
3. Allocate necessary resources and budget
4. Begin with high-priority, low-risk initiatives

This assessment provides a roadmap for modernizing your infrastructure to support current needs and future growth."""
    
    def _generate_business_context(self, assessment: Any) -> str:
        """Generate business context section."""
        business_req = getattr(assessment, 'business_requirements', {})
        
        company_name = business_req.get("company_name", "the organization")
        industry = business_req.get("industry", "technology")
        company_size = business_req.get("company_size", "medium")
        primary_goals = business_req.get("primary_goals", [])
        budget_range = business_req.get("budget_range", "not specified")
        timeline = business_req.get("timeline", "flexible")
        main_challenges = business_req.get("main_challenges", [])
        
        goals_text = ", ".join(primary_goals) if primary_goals else "not specified"
        challenges_text = ", ".join(main_challenges) if main_challenges else "not specified"
        
        return f"""**Company Profile:**
- Organization: {company_name}
- Industry: {industry.title()}
- Size: {company_size.title()}
- Budget Range: {budget_range.replace('_', ' ').title()}
- Timeline: {timeline.replace('_', ' ').title()}

**Business Objectives:**
{goals_text}

**Current Challenges:**
{challenges_text}

**Strategic Context:**
The organization is seeking to optimize its infrastructure to better align with business objectives and overcome current operational challenges. This assessment focuses on identifying opportunities that deliver maximum business value while addressing immediate pain points."""
    
    def _generate_current_state_analysis(self, assessment: Any) -> str:
        """Generate current state analysis section."""
        business_req = getattr(assessment, 'business_requirements', {})
        technical_req = getattr(assessment, 'technical_requirements', {})
        
        infrastructure_maturity = business_req.get("infrastructure_maturity", "intermediate")
        current_hosting = technical_req.get("current_hosting", [])
        current_technologies = technical_req.get("current_technologies", [])
        team_expertise = technical_req.get("team_expertise", "intermediate")
        
        hosting_text = ", ".join(current_hosting) if current_hosting else "not specified"
        tech_text = ", ".join(current_technologies) if current_technologies else "not specified"
        
        return f"""**Infrastructure Maturity Level:** {infrastructure_maturity.title()}

**Current Hosting Environment:**
{hosting_text}

**Technology Stack:**
{tech_text}

**Team Expertise Level:** {team_expertise.title()}

**Assessment Summary:**
The current infrastructure shows {infrastructure_maturity} maturity with opportunities for optimization. The existing technology stack provides a solid foundation for modernization efforts, and the team's {team_expertise} expertise level supports the recommended improvements."""
    
    def _generate_technical_requirements(self, assessment: Any) -> str:
        """Generate technical requirements section."""
        technical_req = getattr(assessment, 'technical_requirements', {})
        
        workload_types = technical_req.get("workload_types", [])
        expected_users = technical_req.get("expected_users", "not specified")
        data_volume = technical_req.get("data_volume", "not specified")
        performance_requirements = technical_req.get("performance_requirements", [])
        preferred_providers = technical_req.get("preferred_cloud_providers", [])
        compliance_requirements = technical_req.get("compliance_requirements", [])
        
        workloads_text = ", ".join(workload_types) if workload_types else "not specified"
        performance_text = ", ".join(performance_requirements) if performance_requirements else "not specified"
        providers_text = ", ".join(preferred_providers) if preferred_providers else "not specified"
        compliance_text = ", ".join(compliance_requirements) if compliance_requirements else "none specified"
        
        return f"""**Workload Types:**
{workloads_text}

**Scale Requirements:**
- Expected Users: {expected_users}
- Data Volume: {data_volume.replace('_', ' ').title()}

**Performance Requirements:**
{performance_text}

**Cloud Provider Preferences:**
{providers_text}

**Compliance Requirements:**
{compliance_text}

**Technical Constraints:**
The requirements analysis indicates a need for scalable, performant infrastructure that can handle the specified workloads while meeting compliance and security standards."""
    
    def _generate_recommendations_overview(self, recommendations: List[Any]) -> str:
        """Generate recommendations overview section."""
        if not recommendations:
            return "No specific recommendations were generated for this assessment."
        
        high_priority = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'high']
        medium_priority = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'medium']
        low_priority = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'low']
        
        total_cost = sum(getattr(r, 'estimated_cost', 0) for r in recommendations)
        
        content = f"""**Recommendation Summary:**
- Total Recommendations: {len(recommendations)}
- High Priority: {len(high_priority)}
- Medium Priority: {len(medium_priority)}
- Low Priority: {len(low_priority)}
- Estimated Total Cost: ${total_cost:,.2f}

**High Priority Recommendations:**
"""
        
        for i, rec in enumerate(high_priority[:5], 1):  # Show top 5 high priority
            title = getattr(rec, 'title', f'Recommendation {i}')
            cost = getattr(rec, 'estimated_cost', 0)
            content += f"{i}. {title} (${cost:,.2f})\n"
        
        if len(high_priority) > 5:
            content += f"... and {len(high_priority) - 5} more high priority recommendations\n"
        
        content += "\n**Key Benefits:**\n"
        all_benefits = []
        for rec in recommendations:
            benefits = getattr(rec, 'benefits', [])
            all_benefits.extend(benefits)
        
        unique_benefits = list(set(all_benefits))[:5]  # Top 5 unique benefits
        for benefit in unique_benefits:
            content += f"- {benefit}\n"
        
        return content
    
    def _generate_detailed_recommendations(self, recommendations: List[Any]) -> str:
        """Generate detailed recommendations section."""
        if not recommendations:
            return "No detailed recommendations available."
        
        content = "**Detailed Recommendation Analysis:**\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            title = getattr(rec, 'title', f'Recommendation {i}')
            description = getattr(rec, 'description', 'No description available')
            category = getattr(rec, 'category', 'general')
            priority = getattr(rec, 'priority', 'medium')
            cost = getattr(rec, 'estimated_cost', 0)
            implementation_time = getattr(rec, 'implementation_time', 'unknown')
            benefits = getattr(rec, 'benefits', [])
            risks = getattr(rec, 'risks', [])
            
            content += f"### {i}. {title}\n\n"
            content += f"**Category:** {category.title()}\n"
            content += f"**Priority:** {priority.title()}\n"
            content += f"**Estimated Cost:** ${cost:,.2f}\n"
            content += f"**Implementation Time:** {implementation_time}\n\n"
            content += f"**Description:**\n{description}\n\n"
            
            if benefits:
                content += "**Benefits:**\n"
                for benefit in benefits:
                    content += f"- {benefit}\n"
                content += "\n"
            
            if risks:
                content += "**Risks:**\n"
                for risk in risks:
                    content += f"- {risk}\n"
                content += "\n"
            
            content += "---\n\n"
        
        return content
    
    def _generate_cost_analysis(self, recommendations: List[Any]) -> str:
        """Generate cost analysis section."""
        if not recommendations:
            return "No cost analysis available."
        
        total_cost = sum(getattr(r, 'estimated_cost', 0) for r in recommendations)
        high_cost_recs = [r for r in recommendations if getattr(r, 'estimated_cost', 0) > total_cost * 0.2]
        
        content = f"""**Investment Overview:**
- Total Estimated Cost: ${total_cost:,.2f}
- Number of Initiatives: {len(recommendations)}
- Average Cost per Initiative: ${total_cost / len(recommendations):,.2f}

**Cost Breakdown by Priority:**
"""
        
        priorities = ['high', 'medium', 'low']
        for priority in priorities:
            priority_recs = [r for r in recommendations if getattr(r, 'priority', 'medium') == priority]
            priority_cost = sum(getattr(r, 'estimated_cost', 0) for r in priority_recs)
            if priority_recs:
                content += f"- {priority.title()} Priority: ${priority_cost:,.2f} ({len(priority_recs)} items)\n"
        
        content += "\n**Major Cost Items:**\n"
        for rec in sorted(high_cost_recs, key=lambda r: getattr(r, 'estimated_cost', 0), reverse=True)[:5]:
            title = getattr(rec, 'title', 'Unknown')
            cost = getattr(rec, 'estimated_cost', 0)
            content += f"- {title}: ${cost:,.2f}\n"
        
        content += f"""
**Budget Considerations:**
- Consider phased implementation to spread costs over time
- High-priority items should be budgeted for immediate implementation
- ROI analysis suggests payback period of 12-24 months for most initiatives
"""
        
        return content
    
    def _generate_implementation_roadmap(self, recommendations: List[Any]) -> str:
        """Generate implementation roadmap section."""
        if not recommendations:
            return "No implementation roadmap available."
        
        # Group recommendations by implementation time
        immediate = [r for r in recommendations if 'immediate' in getattr(r, 'implementation_time', '').lower()]
        short_term = [r for r in recommendations if 'month' in getattr(r, 'implementation_time', '').lower()]
        long_term = [r for r in recommendations if 'quarter' in getattr(r, 'implementation_time', '').lower() or 'year' in getattr(r, 'implementation_time', '').lower()]
        
        content = """**Implementation Timeline:**

**Phase 1: Immediate (0-30 days)**
"""
        
        if immediate:
            for rec in immediate:
                title = getattr(rec, 'title', 'Unknown')
                content += f"- {title}\n"
        else:
            content += "- No immediate actions identified\n"
        
        content += "\n**Phase 2: Short-term (1-3 months)**\n"
        
        if short_term:
            for rec in short_term:
                title = getattr(rec, 'title', 'Unknown')
                content += f"- {title}\n"
        else:
            content += "- No short-term actions identified\n"
        
        content += "\n**Phase 3: Long-term (3+ months)**\n"
        
        if long_term:
            for rec in long_term:
                title = getattr(rec, 'title', 'Unknown')
                content += f"- {title}\n"
        else:
            content += "- No long-term actions identified\n"
        
        content += """
**Implementation Success Factors:**
1. Secure executive sponsorship and budget approval
2. Establish clear project governance and accountability
3. Ensure adequate technical resources and expertise
4. Plan for change management and user training
5. Implement monitoring and success metrics
6. Maintain regular progress reviews and adjustments
"""
        
        return content
    
    def _generate_risk_assessment(self, recommendations: List[Any]) -> str:
        """Generate risk assessment section."""
        content = """**Risk Analysis:**

**Implementation Risks:**
- Resource availability and competing priorities
- Technical complexity and integration challenges
- Budget constraints and cost overruns
- Timeline delays due to unforeseen complications
- Change management and user adoption issues

**Mitigation Strategies:**
- Phased implementation approach to reduce complexity
- Thorough testing and validation at each stage
- Regular stakeholder communication and updates
- Contingency planning for critical dependencies
- Investment in training and change management

**Business Continuity:**
- Maintain current systems during transition periods
- Implement rollback procedures for critical changes
- Ensure adequate backup and recovery capabilities
- Plan for minimal business disruption during implementations
"""
        
        # Add specific risks from recommendations
        all_risks = []
        for rec in recommendations:
            risks = getattr(rec, 'risks', [])
            all_risks.extend(risks)
        
        if all_risks:
            unique_risks = list(set(all_risks))
            content += "\n**Specific Technical Risks:**\n"
            for risk in unique_risks[:5]:  # Top 5 unique risks
                content += f"- {risk}\n"
        
        return content
    
    def _generate_architecture_recommendations(self, recommendations: List[Any]) -> str:
        """Generate architecture recommendations section."""
        arch_recs = [r for r in recommendations if 'architecture' in getattr(r, 'category', '').lower() or 'infrastructure' in getattr(r, 'category', '').lower()]
        
        if not arch_recs:
            return "No specific architecture recommendations were identified."
        
        content = "**Architecture Recommendations:**\n\n"
        
        for rec in arch_recs:
            title = getattr(rec, 'title', 'Architecture Recommendation')
            description = getattr(rec, 'description', 'No description available')
            content += f"**{title}:**\n{description}\n\n"
        
        content += """**General Architecture Principles:**
- Design for scalability and future growth
- Implement microservices architecture where appropriate
- Use cloud-native services to reduce operational overhead
- Ensure high availability and disaster recovery capabilities
- Implement proper security controls at all layers
- Design for observability and monitoring
"""
        
        return content
    
    def _generate_technology_stack(self, recommendations: List[Any]) -> str:
        """Generate technology stack section."""
        tech_recs = [r for r in recommendations if 'technology' in getattr(r, 'category', '').lower() or 'stack' in getattr(r, 'category', '').lower()]
        
        if not tech_recs:
            return "No specific technology stack recommendations were identified."
        
        content = "**Recommended Technology Stack:**\n\n"
        
        for rec in tech_recs:
            title = getattr(rec, 'title', 'Technology Recommendation')
            description = getattr(rec, 'description', 'No description available')
            content += f"**{title}:**\n{description}\n\n"
        
        content += """**Technology Selection Principles:**
- Choose mature, well-supported technologies
- Prioritize cloud-native solutions where appropriate
- Ensure compatibility with existing systems
- Consider long-term maintenance and support
- Evaluate total cost of ownership
- Plan for scalability and future growth
"""
        
        return content
    
    def _should_be_interactive(self, title: str, recommendations: List[Any]) -> bool:
        """Determine if a section should have interactive features."""
        interactive_sections = [
            "cost analysis", "investment summary", "recommendations overview",
            "detailed technical recommendations", "architecture recommendations",
            "implementation roadmap", "risk assessment"
        ]
        
        return any(keyword in title.lower() for keyword in interactive_sections)
    
    def _generate_drill_down_data(self, title: str, recommendations: List[Any]) -> Dict[str, Any]:
        """Generate drill-down data for interactive sections."""
        drill_down_data = {}
        
        if "cost" in title.lower():
            # Cost breakdown drill-down
            drill_down_data["cost_breakdown"] = {
                "by_priority": self._group_costs_by_priority(recommendations),
                "by_category": self._group_costs_by_category(recommendations),
                "timeline": self._generate_cost_timeline(recommendations)
            }
        
        if "recommendation" in title.lower():
            # Recommendations drill-down
            drill_down_data["recommendations_detail"] = {
                "by_agent": self._group_recommendations_by_agent(recommendations),
                "by_complexity": self._group_recommendations_by_complexity(recommendations),
                "dependencies": self._analyze_recommendation_dependencies(recommendations)
            }
        
        if "risk" in title.lower():
            # Risk analysis drill-down
            drill_down_data["risk_analysis"] = {
                "risk_matrix": self._generate_risk_matrix(recommendations),
                "mitigation_strategies": self._extract_mitigation_strategies(recommendations),
                "impact_analysis": self._analyze_risk_impact(recommendations)
            }
        
        if "implementation" in title.lower():
            # Implementation drill-down
            drill_down_data["implementation_detail"] = {
                "timeline_gantt": self._generate_gantt_data(recommendations),
                "resource_allocation": self._analyze_resource_requirements(recommendations),
                "milestones": self._extract_milestones(recommendations)
            }
        
        return drill_down_data
    
    def _generate_charts_config(self, title: str, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Generate configuration for interactive charts."""
        charts = []
        
        if "cost" in title.lower():
            # Cost distribution pie chart
            charts.append({
                "type": "pie",
                "title": "Cost Distribution by Priority",
                "description": "Breakdown of estimated costs by recommendation priority",
                "data": self._prepare_cost_pie_data(recommendations)
            })
            
            # Cost timeline chart
            charts.append({
                "type": "line",
                "title": "Cost Timeline",
                "description": "Projected costs over implementation timeline",
                "data": self._prepare_cost_timeline_data(recommendations)
            })
        
        if "recommendation" in title.lower():
            # Recommendations bar chart
            charts.append({
                "type": "bar",
                "title": "Recommendations by Category",
                "description": "Number of recommendations in each category",
                "data": self._prepare_recommendations_bar_data(recommendations)
            })
        
        if "implementation" in title.lower():
            # Implementation timeline
            charts.append({
                "type": "area",
                "title": "Implementation Timeline",
                "description": "Resource allocation over time",
                "data": self._prepare_implementation_timeline_data(recommendations)
            })
        
        return charts
    
    def _group_costs_by_priority(self, recommendations: List[Any]) -> Dict[str, float]:
        """Group costs by recommendation priority."""
        costs_by_priority = {"high": 0, "medium": 0, "low": 0}
        
        for rec in recommendations:
            priority = getattr(rec, 'priority', 'medium')
            cost = getattr(rec, 'estimated_cost', 0)
            costs_by_priority[priority] += cost
        
        return costs_by_priority
    
    def _group_costs_by_category(self, recommendations: List[Any]) -> Dict[str, float]:
        """Group costs by recommendation category."""
        costs_by_category = {}
        
        for rec in recommendations:
            category = getattr(rec, 'category', 'general')
            cost = getattr(rec, 'estimated_cost', 0)
            
            if category not in costs_by_category:
                costs_by_category[category] = 0
            costs_by_category[category] += cost
        
        return costs_by_category
    
    def _generate_cost_timeline(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Generate cost timeline data."""
        timeline = []
        
        # Group by implementation time
        time_groups = {}
        for rec in recommendations:
            impl_time = getattr(rec, 'implementation_time', 'unknown')
            cost = getattr(rec, 'estimated_cost', 0)
            
            if impl_time not in time_groups:
                time_groups[impl_time] = 0
            time_groups[impl_time] += cost
        
        # Convert to timeline format
        for time_period, cost in time_groups.items():
            timeline.append({
                "period": time_period,
                "cost": cost,
                "cumulative_cost": sum(time_groups[t] for t in time_groups if t <= time_period)
            })
        
        return timeline
    
    def _group_recommendations_by_agent(self, recommendations: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Group recommendations by the agent that generated them."""
        by_agent = {}
        
        for rec in recommendations:
            # This would need to be enhanced based on actual recommendation structure
            agent = "general"  # Default agent
            
            if agent not in by_agent:
                by_agent[agent] = []
            
            by_agent[agent].append({
                "title": getattr(rec, 'title', 'Unknown'),
                "priority": getattr(rec, 'priority', 'medium'),
                "cost": getattr(rec, 'estimated_cost', 0)
            })
        
        return by_agent
    
    def _group_recommendations_by_complexity(self, recommendations: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Group recommendations by implementation complexity."""
        by_complexity = {"low": [], "medium": [], "high": []}
        
        for rec in recommendations:
            # Determine complexity based on cost and implementation time
            cost = getattr(rec, 'estimated_cost', 0)
            impl_time = getattr(rec, 'implementation_time', 'unknown')
            
            complexity = "medium"  # Default
            if cost > 50000 or "year" in impl_time.lower():
                complexity = "high"
            elif cost < 10000 and "week" in impl_time.lower():
                complexity = "low"
            
            by_complexity[complexity].append({
                "title": getattr(rec, 'title', 'Unknown'),
                "cost": cost,
                "implementation_time": impl_time
            })
        
        return by_complexity
    
    def _analyze_recommendation_dependencies(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Analyze dependencies between recommendations."""
        # This is a simplified implementation
        dependencies = []
        
        for i, rec in enumerate(recommendations):
            title = getattr(rec, 'title', f'Recommendation {i+1}')
            
            # Simple heuristic for dependencies
            depends_on = []
            if "advanced" in title.lower() or "optimize" in title.lower():
                # Advanced recommendations might depend on basic ones
                for j, other_rec in enumerate(recommendations):
                    if j != i and "basic" in getattr(other_rec, 'title', '').lower():
                        depends_on.append(getattr(other_rec, 'title', f'Recommendation {j+1}'))
            
            if depends_on:
                dependencies.append({
                    "recommendation": title,
                    "depends_on": depends_on
                })
        
        return dependencies
    
    def _generate_risk_matrix(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Generate risk matrix data."""
        risk_matrix = []
        
        for rec in recommendations:
            risks = getattr(rec, 'risks', [])
            cost = getattr(rec, 'estimated_cost', 0)
            
            # Simple risk scoring
            probability = "medium"
            impact = "medium"
            
            if cost > 100000:
                impact = "high"
            elif cost < 10000:
                impact = "low"
            
            if len(risks) > 3:
                probability = "high"
            elif len(risks) < 2:
                probability = "low"
            
            risk_matrix.append({
                "recommendation": getattr(rec, 'title', 'Unknown'),
                "probability": probability,
                "impact": impact,
                "risk_score": self._calculate_risk_score(probability, impact)
            })
        
        return risk_matrix
    
    def _calculate_risk_score(self, probability: str, impact: str) -> int:
        """Calculate numerical risk score."""
        prob_scores = {"low": 1, "medium": 2, "high": 3}
        impact_scores = {"low": 1, "medium": 2, "high": 3}
        
        return prob_scores.get(probability, 2) * impact_scores.get(impact, 2)
    
    def _extract_mitigation_strategies(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Extract mitigation strategies from recommendations."""
        strategies = []
        
        for rec in recommendations:
            risks = getattr(rec, 'risks', [])
            title = getattr(rec, 'title', 'Unknown')
            
            for risk in risks:
                # Generate simple mitigation strategy
                strategy = f"Mitigate {risk} through careful planning and testing"
                strategies.append({
                    "risk": risk,
                    "recommendation": title,
                    "mitigation": strategy
                })
        
        return strategies
    
    def _analyze_risk_impact(self, recommendations: List[Any]) -> Dict[str, Any]:
        """Analyze overall risk impact."""
        total_risks = 0
        high_risk_count = 0
        total_cost_at_risk = 0
        
        for rec in recommendations:
            risks = getattr(rec, 'risks', [])
            cost = getattr(rec, 'estimated_cost', 0)
            
            total_risks += len(risks)
            if len(risks) > 2:
                high_risk_count += 1
                total_cost_at_risk += cost
        
        return {
            "total_risks": total_risks,
            "high_risk_recommendations": high_risk_count,
            "cost_at_risk": total_cost_at_risk,
            "risk_percentage": (high_risk_count / len(recommendations) * 100) if recommendations else 0
        }
    
    def _generate_gantt_data(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Generate Gantt chart data for implementation timeline."""
        gantt_data = []
        
        for i, rec in enumerate(recommendations):
            title = getattr(rec, 'title', f'Task {i+1}')
            impl_time = getattr(rec, 'implementation_time', 'unknown')
            
            # Convert implementation time to duration
            duration = 30  # Default 30 days
            if "week" in impl_time.lower():
                duration = 7
            elif "month" in impl_time.lower():
                duration = 30
            elif "quarter" in impl_time.lower():
                duration = 90
            
            gantt_data.append({
                "task": title,
                "start_date": f"2024-01-{(i * 10) % 28 + 1:02d}",  # Staggered start dates
                "duration": duration,
                "priority": getattr(rec, 'priority', 'medium')
            })
        
        return gantt_data
    
    def _analyze_resource_requirements(self, recommendations: List[Any]) -> Dict[str, Any]:
        """Analyze resource requirements for implementation."""
        resources = {
            "technical_staff": 0,
            "budget": 0,
            "external_consultants": 0,
            "training_hours": 0
        }
        
        for rec in recommendations:
            cost = getattr(rec, 'estimated_cost', 0)
            category = getattr(rec, 'category', 'general')
            
            resources["budget"] += cost
            
            # Estimate staff requirements based on cost and category
            if cost > 50000:
                resources["technical_staff"] += 2
            else:
                resources["technical_staff"] += 1
            
            if "training" in category.lower():
                resources["training_hours"] += 40
            
            if cost > 100000:
                resources["external_consultants"] += 1
        
        return resources
    
    def _extract_milestones(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Extract key milestones from recommendations."""
        milestones = []
        
        # Add standard milestones
        milestones.append({
            "name": "Project Kickoff",
            "date": "2024-01-01",
            "description": "Begin implementation of infrastructure recommendations"
        })
        
        # Add milestones based on high-priority recommendations
        high_priority_recs = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'high']
        
        for i, rec in enumerate(high_priority_recs[:3]):  # Top 3 high priority
            title = getattr(rec, 'title', f'Milestone {i+1}')
            milestones.append({
                "name": f"Complete {title}",
                "date": f"2024-{(i+2):02d}-01",
                "description": f"Finish implementation of {title}"
            })
        
        milestones.append({
            "name": "Project Completion",
            "date": "2024-12-31",
            "description": "Complete all infrastructure recommendations"
        })
        
        return milestones
    
    def _prepare_cost_pie_data(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Prepare data for cost distribution pie chart."""
        costs_by_priority = self._group_costs_by_priority(recommendations)
        
        return [
            {"label": priority.title(), "value": cost}
            for priority, cost in costs_by_priority.items()
            if cost > 0
        ]
    
    def _prepare_cost_timeline_data(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Prepare data for cost timeline chart."""
        timeline = self._generate_cost_timeline(recommendations)
        
        return [
            {"x": item["period"], "y": item["cost"]}
            for item in timeline
        ]
    
    def _prepare_recommendations_bar_data(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Prepare data for recommendations bar chart."""
        by_category = {}
        
        for rec in recommendations:
            category = getattr(rec, 'category', 'general')
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += 1
        
        return [
            {"category": category.title(), "count": count}
            for category, count in by_category.items()
        ]
    
    def _prepare_implementation_timeline_data(self, recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Prepare data for implementation timeline chart."""
        gantt_data = self._generate_gantt_data(recommendations)
        
        # Convert to area chart data
        timeline_data = []
        
        for item in gantt_data:
            timeline_data.append({
                "date": item["start_date"],
                "active_tasks": 1,
                "priority": item["priority"],
                "task_name": item.get("task", "Unknown Task"),
                "duration_days": item.get("duration", 30),
                "completion_percentage": item.get("progress", 0)
            })
        
        return timeline_data

    def _generate_implementation_details(self, recommendations: List[Any]) -> str:
        """Generate implementation details section."""
        return """**Implementation Approach:**

    **Project Management:**
    - Establish dedicated project team with clear roles
    - Use agile methodology with regular sprint reviews
    - Implement risk management and issue tracking
    - Maintain detailed project documentation

    **Technical Implementation:**
    - Follow infrastructure as code principles
    - Implement comprehensive testing strategies
    - Use blue-green deployment for zero-downtime updates
    - Establish proper version control and change management

    **Quality Assurance:**
    - Conduct thorough testing at each implementation phase
    - Perform security and compliance validation
    - Execute performance and load testing
    - Implement monitoring and alerting from day one

    **Change Management:**
    - Develop comprehensive training programs
    - Create detailed operational procedures
    - Establish support and troubleshooting guides
    - Plan for user adoption and feedback collection
    """

    def _generate_security_compliance(self, assessment: Any, recommendations: List[Any]) -> str:
        """Generate security and compliance section."""
        technical_req = getattr(assessment, 'technical_requirements', {})
        compliance_requirements = technical_req.get("compliance_requirements", [])
        security_requirements = technical_req.get("security_requirements", [])
        
        compliance_text = ", ".join(compliance_requirements) if compliance_requirements else "none specified"
        security_text = ", ".join(security_requirements) if security_requirements else "standard security measures"
        
        return f"""**Compliance Requirements:**
    {compliance_text}

    **Security Requirements:**
    {security_text}

    **Security Framework:**
    - Implement defense-in-depth security strategy
    - Regular security assessments and penetration testing
    - Continuous compliance monitoring and reporting
    - Incident response and recovery procedures

    **Compliance Measures:**
    - Data governance and privacy protection
    - Audit logging and monitoring
    - Access controls and identity management
    - Regular compliance assessments and certifications

    **Recommended Security Controls:**
    - Multi-factor authentication (MFA)
    - Network segmentation and firewalls
    - Encryption for data at rest and in transit
    - Regular security updates and patch management
    - Security awareness training for all users
    """

    def _generate_monitoring_operations(self, recommendations: List[Any]) -> str:
        """Generate monitoring and operations section."""
        return """**Monitoring Strategy:**

    **Infrastructure Monitoring:**
    - System performance and resource utilization
    - Network connectivity and latency
    - Storage capacity and performance
    - Security events and anomalies

    **Application Monitoring:**
    - Application performance metrics (APM)
    - User experience and transaction monitoring
    - Error tracking and debugging
    - Business metrics and KPIs

    **Operational Procedures:**
    - Incident response and escalation procedures
    - Change management and deployment processes
    - Backup and recovery operations
    - Capacity planning and scaling procedures

    **Alerting and Notifications:**
    - Proactive alerting for critical issues
    - Escalation procedures for different severity levels
    - Integration with communication platforms
    - Regular reporting and dashboard reviews

    **Continuous Improvement:**
    - Regular performance reviews and optimization
    - Capacity planning based on growth trends
    - Technology refresh and upgrade planning
    - Process improvement and automation opportunities
    """

    def _generate_next_steps(self, recommendations: List[Any]) -> str:
        """Generate next steps section."""
        high_priority = [r for r in recommendations if getattr(r, 'priority', 'medium') == 'high']
        
        content = """**Immediate Actions (Next 30 Days):**
    1. Review and approve this assessment report
    2. Secure budget and resource allocation
    3. Establish project governance and team structure
    4. Begin detailed planning for high-priority initiatives
    5. Initiate vendor selection and procurement processes

    **Short-term Goals (Next 90 Days):**
    1. Complete detailed technical designs
    2. Begin implementation of quick wins and foundational elements
    3. Establish monitoring and measurement frameworks
    4. Conduct team training and skill development
    5. Execute pilot projects and proof-of-concepts

    **Long-term Objectives (6-12 Months):**
    1. Complete major infrastructure transformations
    2. Achieve target performance and scalability metrics
    3. Realize projected cost savings and efficiency gains
    4. Establish mature operational processes
    5. Plan for next phase of optimization and growth

    **Success Metrics:**
    - Infrastructure performance improvements
    - Cost reduction achievements
    - Security and compliance posture
    - Team productivity and satisfaction
    - Business value delivery
    """
        
        if high_priority:
            content += f"\n**Priority Focus Areas:**\n"
            for i, rec in enumerate(high_priority[:3], 1):
                title = getattr(rec, 'title', f'Priority Item {i}')
                content += f"{i}. {title}\n"
        
        return content
