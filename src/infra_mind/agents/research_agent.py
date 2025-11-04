"""
Research Agent for Infra Mind.

Provides real-time data collection and market intelligence capabilities.
Focuses on cloud provider APIs, pricing data, and trend analysis.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import asyncio

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from .web_search import get_web_search_client, search_cloud_infrastructure_topics
from ..models.assessment import Assessment
from ..llm.prompt_sanitizer import PromptSanitizer

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent for real-time data collection and market intelligence.
    
    This agent focuses on:
    - Real-time data collection from cloud providers
    - Pricing data aggregation and analysis
    - Trend analysis and benchmark data collection
    - Data freshness validation
    - Market intelligence gathering
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Research Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="Research Agent",
                role=AgentRole.RESEARCH,
                tools_enabled=["cloud_api", "data_processor", "calculator"],
                temperature=0.1,  # Lower temperature for more consistent data collection
                max_tokens=2000,
                custom_config={
                    "focus_areas": [
                        "data_collection",
                        "pricing_analysis",
                        "trend_analysis",
                        "benchmark_collection",
                        "market_intelligence"
                    ],
                    "data_sources": [
                        "aws_pricing_api",
                        "azure_retail_api",
                        "gcp_billing_api",
                        "benchmark_repositories"
                    ]
                }
            )
        
        super().__init__(config)
        

        # Initialize prompt sanitizer for security
        self.prompt_sanitizer = PromptSanitizer(security_level="balanced")
        # Research Agent-specific attributes
        self.data_sources = [
            "aws_pricing_api",
            "azure_retail_api", 
            "gcp_billing_api"
        ]
        
        self.service_types = [
            "compute",
            "storage", 
            "database",
            "networking",
            "ai_ml"
        ]
        
        # Data freshness thresholds (in hours)
        self.freshness_thresholds = {
            "pricing_data": 24,      # Pricing data should be < 24 hours old
            "service_data": 48,      # Service info can be < 48 hours old
            "benchmark_data": 168    # Benchmarks can be < 1 week old
        }
        
        logger.info("Research Agent initialized with data collection capabilities")
    
    async def research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Research a specific topic using real web search and LLM analysis.
        
        Args:
            topic: The topic to research
            
        Returns:
            Dictionary containing research results
        """
        try:
            logger.info(f"Starting comprehensive research on topic: {topic}")
            
            # Step 1: Perform real web search for current information
            web_search_results = await self._perform_web_research(topic)
            
            # Step 2: Use LLM to analyze web search results and provide insights
            research_results = await self._analyze_web_research_with_llm(topic, web_search_results)
            
            # Step 3: Combine real data with LLM analysis
            comprehensive_results = {
                "topic": topic,
                "research_methodology": "web_search_plus_llm_analysis",
                "web_search_data": web_search_results,
                "analysis_results": research_results,
                "confidence_score": 0.9,  # Higher confidence with real data
                "research_timestamp": datetime.now(timezone.utc).isoformat(),
                "data_sources": web_search_results.get("sources_used", []),
                "llm_powered": True,
                "real_data": True
            }
            
            return {
                "status": "completed",
                "results": comprehensive_results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
                
        except Exception as e:
            logger.error(f"Web research failed for topic '{topic}': {str(e)}")
            # Fallback to LLM-only research
            return await self._fallback_llm_only_research(topic)
    
    async def _perform_web_research(self, topic: str) -> Dict[str, Any]:
        """
        Perform real web research on a topic using multiple search strategies.
        
        Args:
            topic: The topic to research
            
        Returns:
            Dictionary containing web search results and metadata
        """
        logger.info(f"Performing web research for topic: {topic}")
        
        web_search_results = {
            "topic": topic,
            "search_results": [],
            "sources_used": [],
            "search_metadata": {
                "search_timestamp": datetime.now(timezone.utc).isoformat(),
                "search_strategies": [],
                "total_results": 0
            }
        }
        
        try:
            # Get web search client
            search_client = await get_web_search_client()
            
            # Define search strategies for comprehensive research
            search_strategies = [
                {
                    "query": f"{topic} latest trends 2024",
                    "type": "general",
                    "focus": "trends"
                },
                {
                    "query": f"{topic} market analysis pricing",
                    "type": "general", 
                    "focus": "market"
                },
                {
                    "query": f"{topic} technical capabilities performance",
                    "type": "technical",
                    "focus": "technical"
                },
                {
                    "query": f"{topic} industry adoption case studies",
                    "type": "general",
                    "focus": "adoption"
                }
            ]
            
            # Perform searches for each strategy
            all_results = []
            for strategy in search_strategies:
                try:
                    search_result = await search_client.search(
                        query=strategy["query"],
                        max_results=5,
                        search_type=strategy["type"]
                    )
                    
                    if search_result.get("results"):
                        # Tag results with focus area
                        for result in search_result["results"]:
                            result["focus_area"] = strategy["focus"]
                            result["search_query"] = strategy["query"]
                        
                        all_results.extend(search_result["results"])
                        web_search_results["search_metadata"]["search_strategies"].append({
                            "strategy": strategy["focus"],
                            "query": strategy["query"],
                            "results_count": len(search_result["results"]),
                            "search_method": search_result["metadata"]["search_method"]
                        })
                        
                        # Track unique sources
                        for result in search_result["results"]:
                            source = result.get("source")
                            if source not in web_search_results["sources_used"]:
                                web_search_results["sources_used"].append(source)
                    
                    # Small delay between searches to be respectful to APIs
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Search strategy '{strategy['focus']}' failed: {e}")
                    continue
            
            # Remove duplicates and rank results
            unique_results = self._deduplicate_and_rank_results(all_results)
            web_search_results["search_results"] = unique_results[:15]  # Top 15 results
            web_search_results["search_metadata"]["total_results"] = len(unique_results)
            
            logger.info(f"Web research completed: {len(unique_results)} unique results from {len(web_search_results['sources_used'])} sources")
            
        except Exception as e:
            logger.error(f"Web research failed: {e}")
            web_search_results["error"] = str(e)
        
        return web_search_results
    
    async def _analyze_web_research_with_llm(self, topic: str, web_search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze web search results and extract insights.
        
        Args:
            topic: The research topic
            web_search_results: Results from web search
            
        Returns:
            Dictionary containing LLM analysis of web search data
        """
        logger.info(f"Analyzing web search results with LLM for topic: {topic}")
        
        # Prepare search results summary for LLM
        search_summary = self._prepare_search_results_for_llm(web_search_results)
        
        prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

As a Research Agent, analyze the following real web search results for the topic "{topic}" and provide comprehensive insights:

TOPIC: {topic}

WEB SEARCH RESULTS SUMMARY:
{search_summary}

SEARCH METADATA:
- Total Results Analyzed: {web_search_results['search_metadata']['total_results']}
- Sources Used: {', '.join(web_search_results['sources_used'])}
- Search Timestamp: {web_search_results['search_metadata']['search_timestamp']}

Based on this real, current web data, provide detailed analysis including:

1. **Key Market Findings** (based on real search data):
   - Current market trends and developments
   - Key players and competitive landscape
   - Recent announcements and innovations
   - Market size and growth indicators

2. **Technical Insights** (from technical search results):
   - Current technical capabilities and limitations
   - Performance benchmarks and comparisons
   - Integration patterns and best practices
   - Emerging technical standards

3. **Industry Adoption Patterns**:
   - Real-world implementation examples
   - Success stories and case studies
   - Common challenges and solutions
   - Adoption trends across industries

4. **Pricing and Cost Analysis**:
   - Current pricing models and trends
   - Cost comparison insights
   - Value proposition analysis
   - Budget planning considerations

5. **Strategic Recommendations**:
   - Actionable insights for decision-making
   - Risk assessment and mitigation
   - Implementation roadmap suggestions
   - Future outlook and predictions

6. **Data Quality Assessment**:
   - Reliability of the web search data
   - Areas where additional research is needed
   - Confidence levels for different insights

Ensure all insights are directly supported by the web search data provided. Cite specific sources where relevant.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "market_findings": {
    "trends": ["trend1", "trend2", "trend3"],
    "key_players": ["player1", "player2"],
    "innovations": ["innovation1", "innovation2"],
    "market_size": "size_info"
  },
  "technical_insights": {
    "capabilities": ["capability1", "capability2"],
    "limitations": ["limitation1", "limitation2"],
    "benchmarks": {{"metric1": "value1", "metric2": "value2"}},
    "best_practices": ["practice1", "practice2"]
  },
  "adoption_patterns": {
    "examples": ["example1", "example2"],
    "success_stories": ["story1", "story2"],
    "challenges": ["challenge1", "challenge2"],
    "trends": ["trend1", "trend2"]
  },
  "pricing_analysis": {
    "models": ["model1", "model2"],
    "trends": ["trend1", "trend2"],
    "comparisons": {{"provider1": "price1", "provider2": "price2"}},
    "considerations": ["consideration1", "consideration2"]
  },
  "recommendations": {
    "strategic": ["rec1", "rec2", "rec3"],
    "risks": ["risk1", "risk2"],
    "roadmap": ["step1", "step2", "step3"],
    "outlook": ["prediction1", "prediction2"]
  },
  "data_quality": {
    "reliability_score": 0.8,
    "research_gaps": ["gap1", "gap2"],
    "confidence_levels": {{"market": "high", "technical": "medium"}}
  }
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert Research Agent specializing in analyzing real-time web data to provide comprehensive market intelligence and technical insights. Base your analysis strictly on the provided web search results while applying your expertise to extract meaningful patterns and actionable insights. CRITICAL: You MUST respond with ONLY a valid JSON object. No text before or after the JSON. No explanations, no markdown formatting, no code blocks - just pure JSON.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Parse LLM response with enhanced error handling
            import json
            import re
            try:
                # Clean response - remove any potential markdown formatting or extra text
                cleaned_response = response.strip()
                
                # Try to extract JSON from response if it's wrapped in text
                if not cleaned_response.startswith('{'):
                    json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(1)
                
                analysis_results = json.loads(cleaned_response)
                
                # Validate that we have a proper dictionary structure
                if not isinstance(analysis_results, dict):
                    logger.warning("LLM response is not a dictionary, falling back to text parsing")
                    analysis_results = self._parse_web_analysis_text(response, topic)
                
                # Ensure nested structures exist with defaults
                if "market_findings" not in analysis_results:
                    analysis_results["market_findings"] = {"trends": [], "key_players": [], "innovations": [], "market_size": ""}
                if "technical_insights" not in analysis_results:
                    analysis_results["technical_insights"] = {"capabilities": [], "limitations": [], "benchmarks": {}, "best_practices": []}
                if "recommendations" not in analysis_results:
                    analysis_results["recommendations"] = {"strategic": [], "risks": [], "roadmap": [], "outlook": []}
                
                # Add metadata
                analysis_results.update({
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "web_data_analyzed": True,
                    "sources_count": len(web_search_results.get("sources_used", [])),
                    "results_analyzed": web_search_results["search_metadata"]["total_results"],
                    "llm_confidence": 0.9
                })
                
                return analysis_results
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM JSON response for web analysis")
                return self._parse_web_analysis_text(response, topic)
                
        except Exception as e:
            logger.error(f"LLM analysis of web results failed: {e}")
            return self._create_fallback_analysis(topic, web_search_results)
    
    async def _fallback_llm_only_research(self, topic: str) -> Dict[str, Any]:
        """
        Fallback to LLM-only research when web search fails.
        
        Args:
            topic: The topic to research
            
        Returns:
            Dictionary containing LLM-based research results
        """
        logger.info(f"Using LLM-only research fallback for topic: {topic}")
        
        prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

As a Research Agent specializing in cloud infrastructure and technology, conduct comprehensive research on the following topic:

TOPIC: {topic}

Since web search is unavailable, provide research results based on your knowledge including:

1. **Key Findings**:
   - Most important insights about {topic}
   - Current state of the technology/market
   - Recent developments and innovations
   - Industry adoption patterns

2. **Market Analysis**:
   - Market size and growth trends
   - Key players and competitive landscape
   - Pricing trends and cost considerations
   - Regional variations and preferences

3. **Technical Analysis**:
   - Technical capabilities and limitations
   - Performance characteristics and benchmarks
   - Integration requirements and dependencies
   - Scalability and reliability considerations

4. **Strategic Implications**:
   - Business impact and value proposition
   - Implementation considerations
   - Risk factors and mitigation strategies
   - Future outlook and recommendations

Provide specific, actionable insights based on your knowledge of the industry.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "research_results": {{
    "key_findings": ["finding1", "finding2", "finding3"],
    "recommendations": ["rec1", "rec2", "rec3"], 
    "market_trends": ["trend1", "trend2", "trend3"],
    "technology_insights": ["insight1", "insight2", "insight3"],
    "industry_benchmarks": {{"metric1": "value1", "metric2": "value2"}},
    "market_analysis": {{
      "size": "market_size_info",
      "growth": "growth_info",
      "key_players": ["player1", "player2"],
      "pricing_trends": ["trend1", "trend2"]
    }},
    "technical_analysis": {{
      "capabilities": ["capability1", "capability2"],
      "limitations": ["limitation1", "limitation2"],
      "performance": {{"benchmark1": "value1", "benchmark2": "value2"}},
      "scalability": ["factor1", "factor2"]
    }},
    "strategic_implications": {{
      "business_impact": ["impact1", "impact2"],
      "implementation": ["step1", "step2"],
      "risks": ["risk1", "risk2"],
      "future_outlook": ["prediction1", "prediction2"]
    }}
  }}
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert Research Agent with comprehensive knowledge of cloud infrastructure, emerging technologies, and market intelligence. Provide thorough, accurate, and actionable research insights based on your knowledge base. CRITICAL: You MUST respond with ONLY a valid JSON object. No text before or after the JSON. No explanations, no markdown formatting, no code blocks - just pure JSON.",
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse LLM response with enhanced error handling
            import json
            import re
            try:
                # Clean response - remove any potential markdown formatting or extra text
                cleaned_response = response.strip()
                
                # Try to extract JSON from response if it's wrapped in text
                if not cleaned_response.startswith('{'):
                    json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(1)
                
                research_results = json.loads(cleaned_response)
                
                # Validate that we have a proper dictionary structure
                if not isinstance(research_results, dict):
                    logger.warning("LLM response is not a dictionary, falling back to text parsing")
                    research_results = self._parse_research_topic_text(response, topic)
                
                # Ensure expected nested structure exists
                if "research_results" in research_results:
                    results_data = research_results["research_results"]
                else:
                    results_data = research_results
                    research_results = {"research_results": results_data}
                
                # Ensure nested structures exist with defaults
                if "key_findings" not in results_data:
                    results_data["key_findings"] = []
                if "recommendations" not in results_data:
                    results_data["recommendations"] = []
                if "market_analysis" not in results_data:
                    results_data["market_analysis"] = {"size": "", "growth": "", "key_players": [], "pricing_trends": []}
                if "technical_analysis" not in results_data:
                    results_data["technical_analysis"] = {"capabilities": [], "limitations": [], "performance": {}, "scalability": []}
                
                # Add metadata indicating this is LLM-only
                research_results.update({
                    "topic": topic,
                    "research_methodology": "llm_only_fallback",
                    "confidence_score": 0.7,  # Lower confidence without real data
                    "research_timestamp": datetime.now(timezone.utc).isoformat(),
                    "llm_powered": True,
                    "real_data": False,
                    "fallback_reason": "web_search_unavailable"
                })
                
                return {
                    "status": "completed",
                    "results": research_results,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM JSON response for fallback research")
                research_results = self._parse_research_topic_text(response, topic)
                
                return {
                    "status": "completed", 
                    "results": research_results,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"LLM fallback research failed for topic '{topic}': {str(e)}")
            # Final fallback to basic structured response
            return await self._final_fallback_research(topic)
    
    def _deduplicate_and_rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate results and rank by relevance.
        
        Args:
            results: List of search results
            
        Returns:
            Deduplicated and ranked results
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url")
            title = result.get("title")
            
            # Skip if we've seen this URL or very similar title
            if url in seen_urls:
                continue
            
            # Check for similar titles (basic deduplication)
            title_words = set(title.lower().split())
            is_duplicate = False
            
            for existing_result in unique_results:
                existing_title_words = set(existing_result.get("title").lower().split())
                if len(title_words & existing_title_words) > len(title_words) * 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Sort by relevance score (if available) and recency
        def sort_key(result):
            relevance = result.get("relevance_score", 0.5)
            has_date = 1 if result.get("published_date") else 0
            return (relevance, has_date)
        
        unique_results.sort(key=sort_key, reverse=True)
        return unique_results
    
    def _prepare_search_results_for_llm(self, web_search_results: Dict[str, Any]) -> str:
        """
        Prepare search results summary for LLM analysis.
        
        Args:
            web_search_results: Web search results
            
        Returns:
            Formatted string for LLM consumption
        """
        search_results = web_search_results.get("search_results", [])
        
        if not search_results:
            return "No search results available."
        
        formatted_results = []
        
        for i, result in enumerate(search_results[:10], 1):  # Top 10 results
            formatted_result = f"""
Result {i}:
- Title: {result.get('title')}
- URL: {result.get('url')}
- Source: {result.get('source')}
- Focus Area: {result.get('focus_area', 'general')}
- Published: {result.get('published_date')}
- Snippet: {result.get('snippet')[:200]}...
- Relevance Score: {result.get('relevance_score')}
"""
            formatted_results.append(formatted_result)
        
        return "\n".join(formatted_results)
    
    def _parse_web_analysis_text(self, response: str, topic: str) -> Dict[str, Any]:
        """Parse web analysis results from text response when JSON parsing fails."""
        return {
            "key_market_findings": self._extract_insights_from_text(response, "market")[:5],
            "technical_insights": self._extract_insights_from_text(response, "technical")[:4],
            "industry_adoption": self._extract_insights_from_text(response, "adoption")[:3],
            "pricing_analysis": self._extract_insights_from_text(response, "pricing")[:3],
            "strategic_recommendations": self._extract_insights_from_text(response, "recommend")[:4],
            "data_quality_assessment": "Parsed from text response",
            "analysis_summary": response[:500] + "..." if len(response) > 500 else response,
            "web_data_analyzed": True,
            "llm_confidence": 0.75
        }
    
    def _create_fallback_analysis(self, topic: str, web_search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic analysis when LLM analysis fails."""
        return {
            "key_market_findings": [
                f"Research conducted on {topic} using web search",
                f"Found {web_search_results['search_metadata']['total_results']} relevant results",
                f"Data collected from {len(web_search_results.get('sources_used', []))} different sources"
            ],
            "technical_insights": [f"Technical analysis of {topic} based on web research"],
            "industry_adoption": [f"Industry adoption patterns for {topic} identified"],
            "pricing_analysis": [f"Pricing information for {topic} collected"],
            "strategic_recommendations": [
                f"Consider the research findings for {topic} implementation",
                "Review the collected web data for detailed insights"
            ],
            "data_quality_assessment": "Basic analysis due to LLM processing limitations",
            "web_data_analyzed": True,
            "llm_confidence": 0.5,
            "fallback_analysis": True
        }
    
    async def _final_fallback_research(self, topic: str) -> Dict[str, Any]:
        """Final fallback when all other methods fail."""
        return {
            "status": "completed",
            "results": {
                "topic": topic,
                "research_methodology": "basic_fallback",
                "key_findings": [
                    f"Research initiated for topic: {topic}",
                    "Multiple research methods were attempted",
                    "Basic research structure provided as fallback"
                ],
                "market_analysis": {
                    "status": "limited_data_available"
                },
                "technical_analysis": {
                    "status": "requires_additional_research"
                },
                "confidence_score": 0.3,
                "research_timestamp": datetime.now(timezone.utc).isoformat(),
                "fallback_mode": True,
                "recommendation": f"Manual research recommended for {topic}"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _parse_research_topic_text(self, response: str, topic: str) -> Dict[str, Any]:
        """Parse research results from text response."""
        return {
            "topic": topic,
            "key_findings": self._extract_insights_from_text(response, "finding")[:5],
            "market_analysis": {
                "trends": self._extract_insights_from_text(response, "trend")[:3],
                "competitive_landscape": self._extract_insights_from_text(response, "competitive")[:3]
            },
            "technical_analysis": {
                "capabilities": self._extract_insights_from_text(response, "technical")[:3],
                "performance": self._extract_insights_from_text(response, "performance")[:2]
            },
            "strategic_implications": self._extract_insights_from_text(response, "strategic")[:4],
            "sources": ["LLM Analysis", "Industry Knowledge Base", "Best Practices"],
            "summary": response[:500] + "..." if len(response) > 500 else response,
            "confidence_score": 0.8,
            "llm_powered": True
        }
    
    # Note: _fallback_topic_research has been replaced with _fallback_llm_only_research 
    # which provides better LLM-based analysis instead of mock data
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute Research agent's main data collection logic.
        
        Returns:
            Dictionary with collected data and analysis
        """
        logger.info("Research Agent starting data collection and analysis")
        
        try:
            # Step 1: Analyze data requirements
            data_requirements = await self._analyze_data_requirements()
            
            # Step 2: Collect real-time data from cloud providers
            collected_data = await self._collect_realtime_data(data_requirements)
            
            # Step 3: Validate data freshness and quality
            data_validation = await self._validate_data_quality(collected_data)
            
            # Step 4: Perform trend analysis
            trend_analysis = await self._perform_trend_analysis(collected_data)
            
            # Step 5: Collect benchmark data
            benchmark_data = await self._collect_benchmark_data(data_requirements)
            
            # Step 6: Generate research insights
            research_insights = await self._generate_research_insights(
                collected_data, trend_analysis, benchmark_data, data_validation
            )
            
            result = {
                "recommendations": research_insights.get("recommendations", []),
                "data": {
                    "data_requirements": data_requirements,
                    "collected_data": collected_data,
                    "data_validation": data_validation,
                    "trend_analysis": trend_analysis,
                    "benchmark_data": benchmark_data,
                    "research_insights": research_insights,
                    "data_sources_used": self.data_sources,
                    "collection_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("Research Agent completed data collection successfully")
            return result
            
        except Exception as e:
            logger.error(f"Research Agent analysis failed: {str(e)}")
            raise   
 
    async def _analyze_data_requirements(self) -> Dict[str, Any]:
        """Analyze what data needs to be collected using real LLM analysis."""
        logger.debug("Analyzing data collection requirements with LLM")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        technical_req = assessment_data.get("technical_requirements", {})
        business_req = assessment_data.get("business_requirements", {})
        
        prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

As a Research Agent, analyze the following infrastructure assessment requirements and determine comprehensive data collection needs:

BUSINESS REQUIREMENTS:
{self._format_data_for_llm(business_req)}

TECHNICAL REQUIREMENTS:
{self._format_data_for_llm(technical_req)}

Determine optimal data collection strategy including:

1. **Workload Analysis**:
   - Workload types and their data requirements
   - User scale implications for data collection
   - Performance and capacity planning data needs
   - Compliance and security data requirements

2. **Required Service Categories**:
   - Essential cloud services to research
   - Service category priorities based on workload types
   - Cross-service dependencies and integrations
   - Specialized services for specific requirements

3. **Pricing Data Requirements**:
   - Cost optimization focus areas
   - Budget-appropriate service tiers to research
   - Pricing model comparison needs (on-demand, reserved, spot)
   - Total cost of ownership factors

4. **Benchmark Data Requirements**:
   - Performance benchmarks needed for workload types
   - Industry-specific benchmarks and standards
   - Scalability and reliability benchmarks
   - Security and compliance benchmarks

5. **Data Collection Priorities**:
   - High-priority data sources for immediate decisions
   - Medium-priority data for comprehensive analysis
   - Optional data for future planning
   - Data freshness and accuracy requirements

6. **Collection Scope**:
   - Cloud providers to include in research
   - Geographic regions for data collection
   - Service categories and subcategories
   - Depth of analysis required

Provide specific, actionable data collection requirements that will enable comprehensive infrastructure recommendations.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "data_requirements": {{
    "workload_analysis": {{
      "types": ["workload_type1", "workload_type2"],
      "scale_requirements": ["requirement1", "requirement2"],
      "performance_needs": ["need1", "need2"],
      "compliance_requirements": ["compliance1", "compliance2"]
    }},
    "required_services": ["service1", "service2", "service3"],
    "pricing_requirements": {{
      "budget_ranges": ["range1", "range2"],
      "cost_models": ["model1", "model2"],
      "optimization_areas": ["area1", "area2"],
      "tco_factors": ["factor1", "factor2"]
    }},
    "benchmark_requirements": {{
      "performance": ["benchmark1", "benchmark2"],
      "industry_standards": ["standard1", "standard2"],
      "scalability": ["metric1", "metric2"],
      "security": ["security1", "security2"]
    }},
    "collection_priorities": {{
      "high": ["priority1", "priority2"],
      "medium": ["priority3", "priority4"],
      "low": ["priority5", "priority6"],
      "freshness_requirements": ["fresh1", "fresh2"]
    }},
    "collection_scope": {{
      "providers": ["provider1", "provider2"],
      "regions": ["region1", "region2"],
      "categories": ["category1", "category2"],
      "analysis_depth": "depth_level"
    }}
  }}
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert Research Agent with deep knowledge of cloud infrastructure data sources, market intelligence requirements, and comprehensive analysis methodologies. Provide detailed, actionable data collection strategies that ensure thorough infrastructure assessment. CRITICAL: You MUST respond with ONLY a valid JSON object. No text before or after the JSON. No explanations, no markdown formatting, no code blocks - just pure JSON.",
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse LLM response with enhanced error handling
            import json
            import re
            try:
                # Clean response - remove any potential markdown formatting or extra text
                cleaned_response = response.strip()
                
                # Try to extract JSON from response if it's wrapped in text
                if not cleaned_response.startswith('{'):
                    json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(1)
                
                llm_requirements = json.loads(cleaned_response)
                
                # Validate that we have a proper dictionary structure
                if not isinstance(llm_requirements, dict):
                    logger.warning("LLM response is not a dictionary, falling back to text parsing")
                    llm_requirements = self._parse_data_requirements_text(response)
                
                # Handle nested data_requirements structure
                if "data_requirements" in llm_requirements:
                    requirements_data = llm_requirements["data_requirements"]
                else:
                    requirements_data = llm_requirements
                
                # Extract traditional requirements as fallback
                workload_types = technical_req.get("workload_types", [])
                expected_users = technical_req.get("expected_users", 1000)
                budget_range = business_req.get("budget_range", "$10k-50k")
                
                # Ensure nested structures exist with defaults
                if "workload_analysis" not in requirements_data:
                    requirements_data["workload_analysis"] = {}
                if "pricing_requirements" not in requirements_data:
                    requirements_data["pricing_requirements"] = {}
                if "benchmark_requirements" not in requirements_data:
                    requirements_data["benchmark_requirements"] = {}
                if "collection_priorities" not in requirements_data:
                    requirements_data["collection_priorities"] = {}
                if "collection_scope" not in requirements_data:
                    requirements_data["collection_scope"] = {}
                
                # Enhance with traditional analysis
                enhanced_requirements = {
                    "workload_analysis": requirements_data.get("workload_analysis", {
                        "types": workload_types,
                        "expected_users": expected_users,
                        "budget_range": budget_range
                    }),
                    "required_services": requirements_data.get("required_services", 
                                                           self._determine_required_services(workload_types)),
                    "pricing_requirements": requirements_data.get("pricing_requirements",
                                                               self._determine_pricing_requirements(budget_range, expected_users)),
                    "benchmark_requirements": requirements_data.get("benchmark_requirements",
                                                                 self._determine_benchmark_requirements(workload_types, expected_users)),
                    "data_priorities": requirements_data.get("collection_priorities", 
                                                          self._prioritize_data_collection(self._determine_required_services(workload_types))),
                    "collection_scope": requirements_data.get("collection_scope", {
                        "providers": ["aws", "azure", "gcp"],
                        "regions": ["us-east-1", "eastus", "us-central1"],
                        "service_categories": self._determine_required_services(workload_types)
                    }),
                    "llm_powered": True,
                    "analysis_confidence": 0.9
                }
                
                return enhanced_requirements
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM JSON response for data requirements")
                return self._parse_data_requirements_text(response)
                
        except Exception as e:
            logger.error(f"LLM data requirements analysis failed: {e}")
            return await self._fallback_data_requirements_analysis(assessment_data)
    
    def _parse_data_requirements_text(self, response: str) -> Dict[str, Any]:
        """Parse data requirements from text response."""
        # Extract key requirements from text
        return {
            "workload_analysis": {
                "insights": self._extract_insights_from_text(response, "workload")[:3],
                "data_needs": self._extract_insights_from_text(response, "data")[:3]
            },
            "required_services": self._extract_insights_from_text(response, "service")[:5],
            "pricing_requirements": {
                "focus_areas": self._extract_insights_from_text(response, "pricing")[:3],
                "cost_optimization": self._extract_insights_from_text(response, "cost")[:3]
            },
            "benchmark_requirements": {
                "performance": self._extract_insights_from_text(response, "performance")[:3],
                "industry": self._extract_insights_from_text(response, "benchmark")[:3]
            },
            "data_priorities": self._extract_insights_from_text(response, "priority")[:4],
            "collection_scope": {
                "providers": ["aws", "azure", "gcp"],
                "focus_areas": self._extract_insights_from_text(response, "collection")[:3]
            },
            "llm_powered": True,
            "analysis_confidence": 0.75
        }
    
    async def _fallback_data_requirements_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback data requirements analysis when LLM fails."""
        logger.info("Using fallback data requirements analysis")
        
        technical_req = assessment_data.get("technical_requirements", {})
        business_req = assessment_data.get("business_requirements", {})
        
        # Use data processing tool to analyze requirements
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        # Determine what data to collect
        workload_types = technical_req.get("workload_types", [])
        expected_users = technical_req.get("expected_users", 1000)
        budget_range = business_req.get("budget_range", "$10k-50k")
        
        # Determine required service categories
        required_services = self._determine_required_services(workload_types)
        
        # Determine pricing data needs
        pricing_requirements = self._determine_pricing_requirements(budget_range, expected_users)
        
        # Determine benchmark requirements
        benchmark_requirements = self._determine_benchmark_requirements(workload_types, expected_users)
        
        return {
            "workload_analysis": {
                "types": workload_types,
                "expected_users": expected_users,
                "budget_range": budget_range
            },
            "required_services": required_services,
            "pricing_requirements": pricing_requirements,
            "benchmark_requirements": benchmark_requirements,
            "data_priorities": self._prioritize_data_collection(required_services),
            "collection_scope": {
                "providers": ["aws", "azure", "gcp"],
                "regions": ["us-east-1", "eastus", "us-central1"],
                "service_categories": required_services
            },
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
    
    async def _collect_realtime_data(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Collect real-time data from cloud providers."""
        logger.debug("Collecting real-time data from cloud providers")
        
        collected_data = {
            "providers": {},
            "collection_metadata": {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "successful_collections": 0,
                "failed_collections": 0,
                "total_api_calls": 0
            }
        }
        
        providers = requirements.get("collection_scope", {}).get("providers", ["aws", "azure"])
        service_categories = requirements.get("required_services", ["compute", "storage"])
        
        # Collect data from each provider
        for provider in providers:
            provider_data = await self._collect_provider_data(provider, service_categories)
            collected_data["providers"][provider] = provider_data
            
            # Update metadata
            if "error" not in provider_data:
                collected_data["collection_metadata"]["successful_collections"] += 1
            else:
                collected_data["collection_metadata"]["failed_collections"] += 1
        
        collected_data["collection_metadata"]["end_time"] = datetime.now(timezone.utc).isoformat()
        collected_data["collection_metadata"]["total_providers"] = len(providers)
        
        return collected_data
    
    async def _collect_provider_data(self, provider: str, service_categories: List[str]) -> Dict[str, Any]:
        """Collect data from a specific cloud provider using real APIs."""
        provider_data = {
            "provider": provider,
            "services": {},
            "pricing_data": {},
            "collection_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Import cloud clients
            from ..cloud.unified import UnifiedCloudClient
            from ..cloud.base import CloudProvider, ServiceCategory
            
            # Initialize unified cloud client
            cloud_client = UnifiedCloudClient()
            
            # Map provider string to CloudProvider enum
            provider_map = {
                "aws": CloudProvider.AWS,
                "azure": CloudProvider.AZURE,
                "gcp": CloudProvider.GCP
            }
            
            cloud_provider = provider_map.get(provider.lower())
            if not cloud_provider:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Check if provider is available
            available_providers = cloud_client.get_available_providers()
            if cloud_provider not in available_providers:
                logger.warning(f"Provider {provider} not available (credentials not configured)")
                provider_data["error"] = f"Provider {provider} not available - credentials not configured"
                return provider_data
            
            # Map service categories to ServiceCategory enum
            category_map = {
                "compute": ServiceCategory.COMPUTE,
                "storage": ServiceCategory.STORAGE,
                "database": ServiceCategory.DATABASE,
                "ai_ml": ServiceCategory.MACHINE_LEARNING,
                "networking": ServiceCategory.NETWORKING
            }
            
            # Collect service data for each category
            for category in service_categories:
                try:
                    service_category = category_map.get(category)
                    if not service_category:
                        logger.warning(f"Unsupported service category: {category}")
                        continue
                    
                    # Get service information using real cloud APIs
                    if service_category == ServiceCategory.COMPUTE:
                        result = await cloud_client.get_compute_services(cloud_provider)
                    elif service_category == ServiceCategory.STORAGE:
                        result = await cloud_client.get_storage_services(cloud_provider)
                    elif service_category == ServiceCategory.DATABASE:
                        result = await cloud_client.get_database_services(cloud_provider)
                    elif service_category == ServiceCategory.MACHINE_LEARNING:
                        result = await cloud_client.get_ai_services(cloud_provider)
                    else:
                        logger.warning(f"Service category {category} not implemented yet")
                        continue
                    
                    # Extract service data from response
                    if cloud_provider in result:
                        service_response = result[cloud_provider]
                        
                        # Convert CloudService objects to dictionaries
                        services_data = []
                        for service in service_response.services:
                            service_dict = {
                                "name": service.service_name,
                                "service_id": service.service_id,
                                "category": service.category.value,
                                "region": service.region,
                                "description": service.description,
                                "hourly_price": service.hourly_price,
                                "pricing_model": service.pricing_model,
                                "pricing_unit": getattr(service, 'pricing_unit', 'hour'),
                                "specifications": service.specifications,
                                "features": service.features
                            }
                            services_data.append(service_dict)
                        
                        provider_data["services"][category] = {
                            "services": services_data,
                            "service_count": len(services_data),
                            "metadata": service_response.metadata
                        }
                        
                        # Extract pricing data
                        pricing_data = []
                        for service in service_response.services:
                            if service.hourly_price:
                                pricing_data.append({
                                    "service_id": service.service_id,
                                    "service_name": service.service_name,
                                    "hourly_price": service.hourly_price,
                                    "monthly_price": service.get_monthly_cost(),
                                    "pricing_unit": getattr(service, 'pricing_unit', 'hour'),
                                    "pricing_model": service.pricing_model
                                })
                        
                        provider_data["pricing_data"][category] = {
                            "pricing": pricing_data,
                            "pricing_count": len(pricing_data)
                        }
                        
                        logger.info(f"Collected {len(services_data)} {category} services from {provider}")
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"Failed to collect {category} data from {provider}: {e}")
                    provider_data["services"][category] = {"error": str(e)}
                    provider_data["pricing_data"][category] = {"error": str(e)}
            
            # Calculate data completeness
            provider_data["data_completeness"] = self._calculate_data_completeness(
                provider_data, service_categories
            )
            
        except Exception as e:
            logger.error(f"Failed to collect data from {provider}: {e}")
            provider_data["error"] = str(e)
        
        return provider_data
    
    async def _validate_data_quality(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data freshness and quality."""
        logger.debug("Validating data quality and freshness")
        
        validation_results = {
            "overall_quality": "unknown",
            "freshness_check": {},
            "completeness_check": {},
            "consistency_check": {},
            "accuracy_check": {},
            "quality_score": 0.0,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_staleness_warnings": []
        }
        
        providers_data = collected_data.get("providers", {})
        
        # Check data freshness
        freshness_results = []
        for provider, data in providers_data.items():
            if "error" not in data:
                freshness_score, staleness_warning = self._check_data_freshness_detailed(data)
                freshness_results.append(freshness_score)
                validation_results["freshness_check"][provider] = {
                    "score": freshness_score,
                    "collection_time": data.get("collection_timestamp"),
                    "age_hours": self._calculate_data_age_hours(data.get("collection_timestamp"))
                }
                
                if staleness_warning:
                    validation_results["data_staleness_warnings"].append(f"{provider}: {staleness_warning}")
        
        # Check data completeness
        completeness_results = []
        for provider, data in providers_data.items():
            if "error" not in data:
                completeness_score = data.get("data_completeness", 0.0)
                completeness_results.append(completeness_score)
                validation_results["completeness_check"][provider] = {
                    "score": completeness_score,
                    "services_collected": len(data.get("services", {})),
                    "pricing_data_collected": len(data.get("pricing_data", {}))
                }
        
        # Check data consistency across providers
        consistency_score = self._check_data_consistency(providers_data)
        validation_results["consistency_check"] = {
            "score": consistency_score,
            "issues": self._identify_consistency_issues(providers_data),
            "cross_provider_comparison": self._compare_providers_data(providers_data)
        }
        
        # Check data accuracy (validate pricing ranges, service specifications)
        accuracy_results = []
        for provider, data in providers_data.items():
            if "error" not in data:
                accuracy_score = self._check_data_accuracy(data)
                accuracy_results.append(accuracy_score)
                validation_results["accuracy_check"][provider] = accuracy_score
        
        # Calculate overall quality score
        if freshness_results and completeness_results and accuracy_results:
            avg_freshness = sum(freshness_results) / len(freshness_results)
            avg_completeness = sum(completeness_results) / len(completeness_results)
            avg_accuracy = sum(r["score"] for r in accuracy_results) / len(accuracy_results)
            
            # Weighted average: freshness 30%, completeness 30%, consistency 20%, accuracy 20%
            validation_results["quality_score"] = (
                avg_freshness * 0.3 + 
                avg_completeness * 0.3 + 
                consistency_score * 0.2 +
                avg_accuracy * 0.2
            )
        
        # Determine overall quality rating
        quality_score = validation_results["quality_score"]
        if quality_score >= 0.8:
            validation_results["overall_quality"] = "excellent"
        elif quality_score >= 0.6:
            validation_results["overall_quality"] = "good"
        elif quality_score >= 0.4:
            validation_results["overall_quality"] = "fair"
        else:
            validation_results["overall_quality"] = "poor"
        
        return validation_results
    
    async def _perform_trend_analysis(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trend analysis using real LLM analysis."""
        logger.debug("Performing trend analysis with LLM")
        
        providers_data = collected_data.get("providers", {})
        
        # Prepare data summary for LLM analysis
        data_summary = self._prepare_trend_analysis_summary(providers_data)
        
        prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

As a Research Agent specializing in cloud infrastructure market analysis, analyze the following real-time data to identify trends and patterns:

COLLECTED DATA SUMMARY:
{self._format_data_for_llm(data_summary)}

PROVIDER DATA OVERVIEW:
{self._format_providers_data_for_llm(providers_data)}

Perform comprehensive trend analysis including:

1. **Pricing Trends Analysis**:
   - Cost leadership patterns across providers
   - Price competitiveness by service category
   - Value proposition analysis
   - Cost optimization opportunities

2. **Service Availability Trends**:
   - Service portfolio comparison across providers
   - Emerging service categories and capabilities
   - Feature differentiation and maturity levels
   - Service gaps and opportunities

3. **Market Intelligence Insights**:
   - Competitive positioning and strategies
   - Innovation patterns and technology adoption
   - Market consolidation or fragmentation trends
   - Regional and vertical market preferences

4. **Emerging Patterns**:
   - New technology adoption (AI/ML, serverless, edge computing)
   - Pricing model evolution (reserved, spot, consumption-based)
   - Service bundling and platform strategies
   - Developer experience and tooling trends

5. **Strategic Implications**:
   - Impact on customer decision-making
   - Vendor selection criteria evolution
   - Future market direction predictions
   - Investment and partnership opportunities

Provide specific, data-driven insights with quantitative analysis where possible.

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "trend_analysis": {{
    "pricing_trends_analysis": {{
      "cost_leadership": ["pattern1", "pattern2"],
      "competitiveness": {{"provider1": "analysis1", "provider2": "analysis2"}},
      "optimization_opportunities": ["opportunity1", "opportunity2"]
    }},
    "service_availability_trends": {{
      "portfolio_comparison": ["comparison1", "comparison2"],
      "emerging_services": ["service1", "service2"],
      "feature_differentiation": ["feature1", "feature2"],
      "service_gaps": ["gap1", "gap2"]
    }},
    "market_intelligence_insights": {{
      "positioning": ["insight1", "insight2"],
      "innovation_patterns": ["pattern1", "pattern2"],
      "consolidation_trends": ["trend1", "trend2"],
      "regional_preferences": ["pref1", "pref2"]
    }},
    "emerging_patterns": {{
      "technology_adoption": ["tech1", "tech2"],
      "pricing_evolution": ["evolution1", "evolution2"],
      "bundling_strategies": ["strategy1", "strategy2"],
      "developer_trends": ["trend1", "trend2"]
    }},
    "strategic_implications": {{
      "decision_impact": ["impact1", "impact2"],
      "vendor_criteria": ["criteria1", "criteria2"],
      "market_predictions": ["prediction1", "prediction2"],
      "opportunities": ["opportunity1", "opportunity2"]
    }}
  }}
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert market analyst specializing in cloud infrastructure trends, competitive intelligence, and technology adoption patterns. Provide comprehensive, data-driven trend analysis that helps organizations understand market dynamics and make strategic decisions. CRITICAL: You MUST respond with ONLY a valid JSON object. No text before or after the JSON. No explanations, no markdown formatting, no code blocks - just pure JSON.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Parse LLM response with enhanced error handling
            import json
            import re
            try:
                # Clean response - remove any potential markdown formatting or extra text
                cleaned_response = response.strip()
                
                # Try to extract JSON from response if it's wrapped in text
                if not cleaned_response.startswith('{'):
                    json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(1)
                
                llm_trends = json.loads(cleaned_response)
                
                # Validate that we have a proper dictionary structure
                if not isinstance(llm_trends, dict):
                    logger.warning("LLM response is not a dictionary, falling back to text parsing")
                    llm_trends = self._parse_trend_analysis_text(response)
                
                # Handle nested trend_analysis structure
                if "trend_analysis" in llm_trends:
                    trends_data = llm_trends["trend_analysis"]
                else:
                    trends_data = llm_trends
                
                # Ensure nested structures exist with defaults
                if "pricing_trends_analysis" not in trends_data:
                    trends_data["pricing_trends_analysis"] = {}
                if "service_availability_trends" not in trends_data:
                    trends_data["service_availability_trends"] = {}
                if "market_intelligence_insights" not in trends_data:
                    trends_data["market_intelligence_insights"] = {}
                if "emerging_patterns" not in trends_data:
                    trends_data["emerging_patterns"] = {}
                if "strategic_implications" not in trends_data:
                    trends_data["strategic_implications"] = {}
                
                # Combine with traditional analysis
                traditional_trends = {
                    "pricing_trends": self._analyze_pricing_trends(providers_data),
                    "service_trends": self._analyze_service_trends(providers_data),
                    "emerging_patterns": self._identify_emerging_patterns(providers_data)
                }
                
                # Enhanced trend analysis
                enhanced_trends = {
                    "pricing_trends": trends_data.get("pricing_trends_analysis", traditional_trends["pricing_trends"]),
                    "service_trends": trends_data.get("service_availability_trends", traditional_trends["service_trends"]),
                    "market_insights": trends_data.get("market_intelligence_insights", []),
                    "emerging_patterns": trends_data.get("emerging_patterns", traditional_trends["emerging_patterns"]),
                    "strategic_implications": trends_data.get("strategic_implications", []),
                    "trend_timestamp": datetime.now(timezone.utc).isoformat(),
                    "llm_powered": True,
                    "analysis_confidence": 0.85
                }
                
                # Add traditional market insights as fallback
                if not enhanced_trends["market_insights"]:
                    enhanced_trends["market_insights"] = self._generate_market_insights(
                        traditional_trends["pricing_trends"], traditional_trends["service_trends"]
                    )
                
                return enhanced_trends
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM JSON response for trend analysis")
                return self._parse_trend_analysis_text(response)
                
        except Exception as e:
            logger.error(f"LLM trend analysis failed: {e}")
            return await self._fallback_trend_analysis(providers_data)
    
    def _prepare_trend_analysis_summary(self, providers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data summary for trend analysis."""
        summary = {
            "total_providers": len(providers_data),
            "successful_collections": len([p for p, d in providers_data.items() if "error" not in d]),
            "service_categories": set(),
            "pricing_data_available": 0,
            "total_services": 0
        }
        
        for provider, data in providers_data.items():
            if "error" not in data:
                services = data.get("services", {})
                summary["service_categories"].update(services.keys())
                summary["total_services"] += sum(
                    len(service_data.get("services", [])) 
                    for service_data in services.values() 
                    if isinstance(service_data, dict)
                )
                
                pricing_data = data.get("pricing_data", {})
                if pricing_data:
                    summary["pricing_data_available"] += 1
        
        summary["service_categories"] = list(summary["service_categories"])
        return summary
    
    def _format_providers_data_for_llm(self, providers_data: Dict[str, Any]) -> str:
        """Format provider data specifically for LLM analysis."""
        if not providers_data:
            return "No provider data available"
        
        formatted = []
        for provider, data in providers_data.items():
            if "error" in data:
                formatted.append(f"  {provider.upper()}: Data collection failed - {data['error']}")
                continue
            
            services = data.get("services", {})
            pricing_data = data.get("pricing_data", {})
            
            formatted.append(f"  {provider.upper()}:")
            formatted.append(f"    - Service Categories: {len(services)}")
            formatted.append(f"    - Total Services: {sum(len(s.get('services', [])) for s in services.values() if isinstance(s, dict))}")
            formatted.append(f"    - Pricing Data: {'Available' if pricing_data else 'Not Available'}")
            formatted.append(f"    - Data Completeness: {data.get('data_completeness', 0.0):.1%}")
        
        return "\n".join(formatted)
    
    def _parse_trend_analysis_text(self, response: str) -> Dict[str, Any]:
        """Parse trend analysis from text response."""
        return {
            "pricing_trends": {
                "insights": self._extract_insights_from_text(response, "pricing")[:4],
                "cost_leaders": {"analysis": "Cost leadership analysis from LLM response"}
            },
            "service_trends": {
                "insights": self._extract_insights_from_text(response, "service")[:4],
                "availability_patterns": self._extract_insights_from_text(response, "availability")[:3]
            },
            "market_insights": self._extract_insights_from_text(response, "market")[:5],
            "emerging_patterns": self._extract_insights_from_text(response, "emerging")[:4],
            "strategic_implications": self._extract_insights_from_text(response, "strategic")[:4],
            "trend_timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_powered": True,
            "analysis_confidence": 0.75
        }
    
    async def _fallback_trend_analysis(self, providers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback trend analysis when LLM fails."""
        logger.info("Using fallback trend analysis")
        
        trend_analysis = {
            "pricing_trends": {},
            "service_trends": {},
            "market_insights": [],
            "trend_timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
        
        # Analyze pricing trends
        pricing_trends = self._analyze_pricing_trends(providers_data)
        trend_analysis["pricing_trends"] = pricing_trends
        
        # Analyze service availability trends
        service_trends = self._analyze_service_trends(providers_data)
        trend_analysis["service_trends"] = service_trends
        
        # Generate market insights
        market_insights = self._generate_market_insights(pricing_trends, service_trends)
        trend_analysis["market_insights"] = market_insights
        
        # Identify emerging patterns
        emerging_patterns = self._identify_emerging_patterns(providers_data)
        trend_analysis["emerging_patterns"] = emerging_patterns
        
        return trend_analysis
    
    async def _collect_benchmark_data(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Collect benchmark data for comparison."""
        logger.debug("Collecting benchmark data")
        
        benchmark_data = {
            "performance_benchmarks": {},
            "cost_benchmarks": {},
            "industry_benchmarks": {},
            "benchmark_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        workload_types = requirements.get("workload_analysis", {}).get("types", [])
        expected_users = requirements.get("workload_analysis", {}).get("expected_users", 1000)
        
        # Collect performance benchmarks
        performance_benchmarks = await self._collect_performance_benchmarks(workload_types)
        benchmark_data["performance_benchmarks"] = performance_benchmarks
        
        # Collect cost benchmarks
        cost_benchmarks = await self._collect_cost_benchmarks(expected_users)
        benchmark_data["cost_benchmarks"] = cost_benchmarks
        
        # Collect industry benchmarks
        industry_benchmarks = await self._collect_industry_benchmarks(workload_types, expected_users)
        benchmark_data["industry_benchmarks"] = industry_benchmarks
        
        return benchmark_data
    
    async def _generate_research_insights(self, collected_data: Dict[str, Any], 
                                        trend_analysis: Dict[str, Any],
                                        benchmark_data: Dict[str, Any],
                                        data_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research insights using real LLM analysis."""
        logger.debug("Generating research insights with LLM")
        
        # Prepare comprehensive context for LLM analysis
        research_context = {
            "data_sources": list(collected_data.get("providers", {}).keys()),
            "data_quality_score": data_validation.get("quality_score", 0.0),
            "pricing_insights": len(trend_analysis.get("pricing_trends", {}).get("cost_leaders", {})),
            "service_categories_analyzed": len(trend_analysis.get("service_trends", {}).get("service_availability", {})),
            "benchmark_categories": list(benchmark_data.get("performance_benchmarks", {}).keys())
        }
        
        prompt = f"""CRITICAL: You must respond with ONLY a valid JSON object. No text before or after the JSON.

As a Research Agent specializing in cloud infrastructure market intelligence, analyze the following comprehensive data and generate strategic research insights:

DATA COLLECTION RESULTS:
{self._format_data_for_llm(collected_data)}

TREND ANALYSIS:
{self._format_data_for_llm(trend_analysis)}

BENCHMARK DATA:
{self._format_data_for_llm(benchmark_data)}

DATA VALIDATION:
- Overall Quality: {data_validation.get('overall_quality')}
- Quality Score: {data_validation.get('quality_score', 0.0):.2f}/1.0
- Data Freshness: {', '.join(data_validation.get('freshness_check', {}).keys())}

Generate comprehensive research insights including:

1. **Key Market Findings**:
   - Most significant discoveries from the data analysis
   - Competitive landscape insights
   - Pricing and cost optimization opportunities
   - Service availability and capability gaps

2. **Strategic Recommendations**:
   - Actionable recommendations based on data analysis
   - Provider selection guidance
   - Cost optimization strategies
   - Risk mitigation suggestions

3. **Market Intelligence**:
   - Industry trends and patterns
   - Emerging technologies and services
   - Competitive positioning insights
   - Future outlook and predictions

4. **Data Quality Assessment**:
   - Reliability of findings based on data quality
   - Confidence levels for different insights
   - Areas requiring additional research

5. **Research Summary**:
   - Executive overview of key insights
   - Methodology and data sources used
   - Limitations and caveats

Ensure insights are:
- Data-driven and evidence-based
- Actionable for infrastructure decision-making
- Specific and quantified where possible
- Clearly prioritized by business impact

CRITICAL: You must respond with ONLY a valid JSON object following this exact schema:
{{
  "research_insights": {{
    "key_market_findings": ["finding1", "finding2", "finding3"],
    "strategic_recommendations": {{
      "provider_selection": ["rec1", "rec2"],
      "cost_optimization": ["strategy1", "strategy2"],
      "risk_mitigation": ["risk1", "risk2"]
    }},
    "market_intelligence": {{
      "industry_trends": ["trend1", "trend2"],
      "emerging_technologies": ["tech1", "tech2"],
      "competitive_positioning": ["insight1", "insight2"],
      "future_outlook": ["prediction1", "prediction2"]
    }},
    "data_quality_assessment": {{
      "reliability": "assessment_level",
      "confidence_levels": {{"category1": "high", "category2": "medium"}},
      "research_gaps": ["gap1", "gap2"]
    }},
    "research_summary": {{
      "executive_overview": "summary_text",
      "methodology": ["method1", "method2"],
      "data_sources": ["source1", "source2"],
      "limitations": ["limitation1", "limitation2"]
    }}
  }}
}}

CRITICAL: Respond with ONLY the JSON object. No additional text."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert Research Agent with deep expertise in cloud infrastructure market analysis, competitive intelligence, and data-driven insights. Provide comprehensive, actionable research insights that help organizations make informed infrastructure decisions based on real market data. CRITICAL: You MUST respond with ONLY a valid JSON object. No text before or after the JSON. No explanations, no markdown formatting, no code blocks - just pure JSON.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Parse LLM response with enhanced error handling
            import json
            import re
            try:
                # Clean response - remove any potential markdown formatting or extra text
                cleaned_response = response.strip()
                
                # Try to extract JSON from response if it's wrapped in text
                if not cleaned_response.startswith('{'):
                    json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(1)
                
                llm_insights = json.loads(cleaned_response)
                
                # Validate that we have a proper dictionary structure
                if not isinstance(llm_insights, dict):
                    logger.warning("LLM response is not a dictionary, falling back to text parsing")
                    llm_insights = self._parse_insights_text(response)
                
                # Handle nested research_insights structure
                if "research_insights" in llm_insights:
                    insights_data = llm_insights["research_insights"]
                else:
                    insights_data = llm_insights
                
                # Ensure nested structures exist with defaults
                if "key_market_findings" not in insights_data:
                    insights_data["key_market_findings"] = []
                if "strategic_recommendations" not in insights_data:
                    insights_data["strategic_recommendations"] = {}
                if "market_intelligence" not in insights_data:
                    insights_data["market_intelligence"] = {}
                if "data_quality_assessment" not in insights_data:
                    insights_data["data_quality_assessment"] = {}
                if "research_summary" not in insights_data:
                    insights_data["research_summary"] = {}
                
                # Merge with traditional analysis
                enhanced_insights = {
                    "key_findings": insights_data.get("key_market_findings", [])[:8],  # Limit findings
                    "recommendations": self._enhance_llm_recommendations(insights_data.get("strategic_recommendations", [])),
                    "market_intelligence": insights_data.get("market_intelligence", {}),
                    "data_quality_assessment": data_validation.get("overall_quality"),
                    "confidence_level": self._assess_confidence_level(data_validation, collected_data),
                    "research_summary": insights_data.get("research_summary", {}),
                    "llm_powered": True,
                    "analysis_confidence": 0.9
                }
                
                # Add traditional findings as fallback
                traditional_findings = self._extract_key_findings(collected_data, trend_analysis, benchmark_data)
                if len(enhanced_insights["key_findings"]) < 3:
                    enhanced_insights["key_findings"].extend(traditional_findings[:5])
                
                return enhanced_insights
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM JSON response for research insights")
                return self._parse_insights_text(response)
                
        except Exception as e:
            logger.error(f"LLM research insights generation failed: {e}")
            return await self._fallback_research_insights(collected_data, trend_analysis, benchmark_data, data_validation)
    
    def _format_data_for_llm(self, data: Dict[str, Any]) -> str:
        """Format complex data structures for LLM consumption."""
        if not data:
            return "No data available"
        
        formatted_lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                formatted_lines.append(f"  {key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (dict, list)) and len(str(sub_value)) > 200:
                        formatted_lines.append(f"    - {sub_key.replace('_', ' ').title()}: [Complex data structure with {len(sub_value) if isinstance(sub_value, (dict, list)) else 'multiple'} items]")
                    else:
                        formatted_lines.append(f"    - {sub_key.replace('_', ' ').title()}: {sub_value}")
            elif isinstance(value, list):
                formatted_lines.append(f"  {key.replace('_', ' ').title()}: {len(value)} items")
                for item in value[:3]:  # Show first 3 items
                    formatted_lines.append(f"    - {item}")
                if len(value) > 3:
                    formatted_lines.append(f"    - ... and {len(value) - 3} more")
            else:
                formatted_lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted_lines)
    
    def _parse_insights_text(self, response: str) -> Dict[str, Any]:
        """Parse research insights from text response when JSON parsing fails."""
        insights = {
            "key_findings": [],
            "recommendations": [],
            "market_intelligence": {},
            "research_summary": {},
            "llm_powered": True,
            "analysis_confidence": 0.75
        }
        
        # Extract key findings from text
        findings = self._extract_insights_from_text(response, "finding")
        insights["key_findings"] = findings[:6]  # Limit to 6 findings
        
        # Extract recommendations
        recommendations_text = self._extract_insights_from_text(response, "recommend")
        insights["recommendations"] = [
            {
                "category": "research_insight",
                "priority": "medium",
                "title": rec[:100],  # Limit title length
                "description": rec,
                "data_source": "llm_analysis",
                "confidence": "medium"
            }
            for rec in recommendations_text[:4]
        ]
        
        # Extract market intelligence
        market_insights = self._extract_insights_from_text(response, "market")
        insights["market_intelligence"] = {
            "trends": market_insights[:3],
            "competitive_insights": self._extract_insights_from_text(response, "competitive")[:2],
            "future_outlook": self._extract_insights_from_text(response, "future")[:2]
        }
        
        return insights
    
    def _extract_insights_from_text(self, text: str, keyword: str) -> List[str]:
        """Extract insights from text based on keyword."""
        insights = []
        lines = text.split('\n')
        
        for line in lines:
            if keyword.lower() in line.lower() and len(line.strip()) > 15:
                clean_line = line.strip('- *').strip()
                if clean_line and len(clean_line) > 20:
                    insights.append(clean_line)
        
        # Fallback if no insights found
        if not insights:
            insights.append(f"Analysis indicates {keyword}-related considerations require further evaluation")
        
        return insights[:5]  # Limit to 5 insights
    
    def _enhance_llm_recommendations(self, llm_recommendations: List[Any]) -> List[Dict[str, Any]]:
        """Enhance LLM recommendations with standard structure."""
        enhanced = []
        
        for i, rec in enumerate(llm_recommendations):
            if isinstance(rec, dict):
                enhanced_rec = {
                    "category": rec.get("category", "research_insight"),
                    "priority": rec.get("priority", "medium"),
                    "title": rec.get("title", f"Research Recommendation {i+1}"),
                    "description": rec.get("description", str(rec)),
                    "data_source": "llm_analysis",
                    "confidence": rec.get("confidence", "medium"),
                    "supporting_data": rec.get("supporting_data", {}),
                    "llm_generated": True
                }
            elif isinstance(rec, str):
                enhanced_rec = {
                    "category": "research_insight",
                    "priority": "medium",
                    "title": rec[:80] if len(rec) > 80 else rec,
                    "description": rec,
                    "data_source": "llm_analysis",
                    "confidence": "medium",
                    "llm_generated": True
                }
            else:
                continue
            
            enhanced.append(enhanced_rec)
        
        return enhanced[:5]  # Limit to 5 recommendations
    
    async def _fallback_research_insights(self, collected_data: Dict[str, Any], 
                                        trend_analysis: Dict[str, Any],
                                        benchmark_data: Dict[str, Any],
                                        data_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback research insights when LLM fails."""
        logger.info("Using fallback research insights generation")
        
        insights = {
            "key_findings": [],
            "recommendations": [],
            "data_quality_assessment": data_validation.get("overall_quality"),
            "confidence_level": "medium",
            "research_summary": {},
            "llm_powered": False,
            "analysis_confidence": 0.6
        }
        
        # Generate key findings
        key_findings = self._extract_key_findings(collected_data, trend_analysis, benchmark_data)
        insights["key_findings"] = key_findings
        
        # Generate recommendations based on findings
        recommendations = self._generate_data_driven_recommendations(
            key_findings, collected_data, trend_analysis
        )
        insights["recommendations"] = recommendations
        
        # Assess confidence level
        confidence_level = self._assess_confidence_level(data_validation, collected_data)
        insights["confidence_level"] = confidence_level
        
        # Create research summary
        research_summary = self._create_research_summary(
            collected_data, trend_analysis, benchmark_data, key_findings
        )
        insights["research_summary"] = research_summary
        
        return insights    

    # Helper methods
    
    def _determine_required_services(self, workload_types: List[str]) -> List[str]:
        """Determine what services need data collection based on workloads."""
        required_services = set()
        
        # Always need compute for any workload
        if workload_types:
            required_services.add("compute")
        
        # Storage needs
        if any(wl in ["web_application", "data_processing", "ai_ml"] for wl in workload_types):
            required_services.add("storage")
        
        # Database needs
        if any(wl in ["web_application", "data_processing"] for wl in workload_types):
            required_services.add("database")
        
        # AI/ML services
        if any(wl in ["ai_ml", "machine_learning"] for wl in workload_types):
            required_services.add("ai_ml")
        
        # Networking (for high-scale applications)
        if workload_types:
            required_services.add("networking")
        
        return list(required_services)
    
    def _determine_pricing_requirements(self, budget_range: str, expected_users: int) -> Dict[str, Any]:
        """Determine pricing data collection requirements."""
        # Parse budget range
        budget_min, budget_max = self._parse_budget_range(budget_range)
        
        return {
            "budget_range": budget_range,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "expected_users": expected_users,
            "pricing_focus": "cost_optimization" if budget_max < 50000 else "performance_optimization",
            "comparison_needed": True,
            "historical_data_needed": False  # MVP: focus on current pricing
        }
    
    def _determine_benchmark_requirements(self, workload_types: List[str], expected_users: int) -> Dict[str, Any]:
        """Determine benchmark data collection requirements."""
        return {
            "workload_types": workload_types,
            "expected_users": expected_users,
            "performance_benchmarks_needed": True,
            "cost_benchmarks_needed": True,
            "industry_benchmarks_needed": len(workload_types) > 1,
            "benchmark_categories": [
                "compute_performance",
                "storage_performance", 
                "cost_per_user",
                "scalability_metrics"
            ]
        }
    
    def _prioritize_data_collection(self, required_services: List[str]) -> List[str]:
        """Prioritize data collection based on service importance."""
        priority_order = ["compute", "database", "storage", "ai_ml", "networking", "security"]
        
        # Sort required services by priority
        prioritized = []
        for service in priority_order:
            if service in required_services:
                prioritized.append(service)
        
        # Add any remaining services
        for service in required_services:
            if service not in prioritized:
                prioritized.append(service)
        
        return prioritized
    
    def _calculate_data_completeness(self, provider_data: Dict[str, Any], 
                                   expected_categories: List[str]) -> float:
        """Calculate data completeness score for a provider."""
        services = provider_data.get("services", {})
        pricing_data = provider_data.get("pricing_data", {})
        
        total_expected = len(expected_categories) * 2  # services + pricing for each category
        collected = 0
        
        for category in expected_categories:
            if category in services and "error" not in services[category]:
                collected += 1
            if category in pricing_data and "error" not in pricing_data[category]:
                collected += 1
        
        return collected / total_expected if total_expected > 0 else 0.0
    
    def _check_data_freshness(self, provider_data: Dict[str, Any]) -> float:
        """Check data freshness and return a score (0.0 to 1.0)."""
        collection_timestamp = provider_data.get("collection_timestamp")
        if not collection_timestamp:
            return 0.0
        
        try:
            collection_time = datetime.fromisoformat(collection_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            age_hours = (current_time - collection_time).total_seconds() / 3600
            
            # Score based on age (fresher = higher score)
            if age_hours < 1:
                return 1.0
            elif age_hours < 6:
                return 0.9
            elif age_hours < 24:
                return 0.7
            elif age_hours < 48:
                return 0.5
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _check_data_freshness_detailed(self, provider_data: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        """Check data freshness with detailed staleness warnings."""
        collection_timestamp = provider_data.get("collection_timestamp")
        if not collection_timestamp:
            return 0.0, "No collection timestamp available"
        
        try:
            collection_time = datetime.fromisoformat(collection_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            age_hours = (current_time - collection_time).total_seconds() / 3600
            
            staleness_warning = None
            
            # Score based on age and generate warnings
            if age_hours < 1:
                score = 1.0
            elif age_hours < 6:
                score = 0.9
            elif age_hours < 24:
                score = 0.7
                staleness_warning = f"Data is {age_hours:.1f} hours old"
            elif age_hours < 48:
                score = 0.5
                staleness_warning = f"Data is {age_hours:.1f} hours old - consider refreshing"
            else:
                score = 0.2
                staleness_warning = f"Data is {age_hours:.1f} hours old - refresh recommended"
            
            return score, staleness_warning
                
        except Exception as e:
            return 0.0, f"Error parsing timestamp: {str(e)}"
    
    def _calculate_data_age_hours(self, collection_timestamp: Optional[str]) -> Optional[float]:
        """Calculate data age in hours."""
        if not collection_timestamp:
            return None
        
        try:
            collection_time = datetime.fromisoformat(collection_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            return (current_time - collection_time).total_seconds() / 3600
        except Exception:
            return None
    
    def _check_data_accuracy(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data accuracy by validating pricing ranges and specifications."""
        accuracy_check = {
            "score": 1.0,
            "issues": [],
            "warnings": []
        }
        
        services_data = provider_data.get("services", {})
        pricing_data = provider_data.get("pricing_data", {})
        
        # Check pricing data accuracy
        for category, pricing_info in pricing_data.items():
            if isinstance(pricing_info, dict) and "pricing" in pricing_info:
                pricing_list = pricing_info["pricing"]
                if isinstance(pricing_list, list):
                    for pricing_item in pricing_list:
                        if isinstance(pricing_item, dict):
                            hourly_price = pricing_item.get("hourly_price")
                            
                            # Check for unreasonable pricing
                            if hourly_price is not None:
                                if hourly_price < 0:
                                    accuracy_check["issues"].append(f"Negative pricing found: {hourly_price}")
                                    accuracy_check["score"] -= 0.1
                                elif hourly_price > 1000:  # Extremely high pricing
                                    accuracy_check["warnings"].append(f"Very high pricing detected: ${hourly_price}/hour")
                                elif hourly_price == 0:
                                    accuracy_check["warnings"].append("Zero pricing detected - may be free tier or error")
        
        # Check service specifications accuracy
        for category, service_info in services_data.items():
            if isinstance(service_info, dict) and "services" in service_info:
                services_list = service_info["services"]
                if isinstance(services_list, list):
                    for service in services_list:
                        if isinstance(service, dict):
                            specs = service.get("specifications", {})
                            
                            # Check compute specifications
                            if "vcpus" in specs:
                                vcpus = specs["vcpus"]
                                if isinstance(vcpus, (int, float)) and vcpus <= 0:
                                    accuracy_check["issues"].append(f"Invalid vCPU count: {vcpus}")
                                    accuracy_check["score"] -= 0.05
                            
                            if "memory_gb" in specs:
                                memory = specs["memory_gb"]
                                if isinstance(memory, (int, float)) and memory <= 0:
                                    accuracy_check["issues"].append(f"Invalid memory size: {memory}GB")
                                    accuracy_check["score"] -= 0.05
        
        # Ensure score doesn't go below 0
        accuracy_check["score"] = max(0.0, accuracy_check["score"])
        
        return accuracy_check
    
    def _compare_providers_data(self, providers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare data across providers for consistency analysis."""
        comparison = {
            "service_overlap": {},
            "pricing_comparison": {},
            "specification_consistency": {}
        }
        
        # Collect all service categories across providers
        all_categories = set()
        provider_categories = {}
        
        for provider, data in providers_data.items():
            if "error" not in data:
                categories = set(data.get("services", {}).keys())
                provider_categories[provider] = categories
                all_categories.update(categories)
        
        # Calculate service overlap
        for category in all_categories:
            providers_with_category = [
                provider for provider, categories in provider_categories.items()
                if category in categories
            ]
            comparison["service_overlap"][category] = {
                "providers": providers_with_category,
                "coverage": len(providers_with_category) / len(provider_categories) if provider_categories else 0
            }
        
        # Compare pricing for common services
        for category in all_categories:
            category_pricing = {}
            for provider, data in providers_data.items():
                if "error" not in data:
                    pricing_data = data.get("pricing_data", {}).get(category, {})
                    if isinstance(pricing_data, dict) and "pricing" in pricing_data:
                        pricing_list = pricing_data["pricing"]
                        if pricing_list:
                            # Get average pricing for this provider/category
                            prices = [
                                item.get("hourly_price", 0) 
                                for item in pricing_list 
                                if isinstance(item, dict) and item.get("hourly_price")
                            ]
                            if prices:
                                category_pricing[provider] = {
                                    "avg_price": sum(prices) / len(prices),
                                    "min_price": min(prices),
                                    "max_price": max(prices),
                                    "service_count": len(prices)
                                }
            
            if len(category_pricing) > 1:
                comparison["pricing_comparison"][category] = category_pricing
        
        return comparison
    
    def _check_data_consistency(self, providers_data: Dict[str, Any]) -> float:
        """Check consistency across providers."""
        if len(providers_data) < 2:
            return 1.0  # Can't check consistency with less than 2 providers
        
        consistency_scores = []
        
        # Check if similar services exist across providers
        all_services = set()
        provider_services = {}
        
        for provider, data in providers_data.items():
            if "error" not in data:
                services = set(data.get("services", {}).keys())
                provider_services[provider] = services
                all_services.update(services)
        
        if len(provider_services) < 2:
            return 0.5
        
        # Calculate overlap between providers
        providers_list = list(provider_services.keys())
        for i in range(len(providers_list)):
            for j in range(i + 1, len(providers_list)):
                provider1_services = provider_services[providers_list[i]]
                provider2_services = provider_services[providers_list[j]]
                
                if provider1_services and provider2_services:
                    overlap = len(provider1_services & provider2_services)
                    total = len(provider1_services | provider2_services)
                    consistency_scores.append(overlap / total if total > 0 else 0)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _identify_consistency_issues(self, providers_data: Dict[str, Any]) -> List[str]:
        """Identify specific consistency issues."""
        issues = []
        
        # Check for missing data
        for provider, data in providers_data.items():
            if "error" in data:
                issues.append(f"Data collection failed for {provider}")
            elif not data.get("services"):
                issues.append(f"No service data available for {provider}")
            elif not data.get("pricing_data"):
                issues.append(f"No pricing data available for {provider}")
        
        return issues
    
    def _analyze_pricing_trends(self, providers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing trends across providers."""
        pricing_trends = {
            "cost_leaders": {},
            "price_ranges": {},
            "cost_comparison": {}
        }
        
        # Collect pricing data by service category
        service_pricing = {}
        
        for provider, data in providers_data.items():
            if "error" not in data:
                pricing_data = data.get("pricing_data", {})
                for service, pricing in pricing_data.items():
                    if service not in service_pricing:
                        service_pricing[service] = {}
                    service_pricing[service][provider] = pricing
        
        # Analyze each service category
        for service, provider_pricing in service_pricing.items():
            if len(provider_pricing) > 1:
                # Find cost leader
                cost_leader = self._find_cost_leader(provider_pricing)
                pricing_trends["cost_leaders"][service] = cost_leader
                
                # Calculate price ranges
                price_range = self._calculate_price_range(provider_pricing)
                pricing_trends["price_ranges"][service] = price_range
        
        return pricing_trends
    
    def _analyze_service_trends(self, providers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service availability and feature trends."""
        service_trends = {
            "service_availability": {},
            "feature_comparison": {},
            "service_maturity": {}
        }
        
        # Analyze service availability
        all_services = set()
        provider_services = {}
        
        for provider, data in providers_data.items():
            if "error" not in data:
                services = data.get("services", {})
                provider_services[provider] = services
                all_services.update(services.keys())
        
        # Check availability across providers
        for service in all_services:
            availability = []
            for provider, services in provider_services.items():
                if service in services and "error" not in services[service]:
                    availability.append(provider)
            
            service_trends["service_availability"][service] = {
                "available_providers": availability,
                "availability_score": len(availability) / len(provider_services) if provider_services else 0
            }
        
        return service_trends
    
    def _generate_market_insights(self, pricing_trends: Dict[str, Any], 
                                service_trends: Dict[str, Any]) -> List[str]:
        """Generate market insights from trend analysis."""
        insights = []
        
        # Pricing insights
        cost_leaders = pricing_trends.get("cost_leaders", {})
        if cost_leaders:
            for service, leader_info in cost_leaders.items():
                provider = leader_info.get("provider")
                if provider:
                    insights.append(f"{provider.upper()} offers the most cost-effective {service} services")
        
        # Service availability insights
        service_availability = service_trends.get("service_availability", {})
        for service, availability_info in service_availability.items():
            score = availability_info.get("availability_score", 0)
            if score == 1.0:
                insights.append(f"{service.title()} services are universally available across all providers")
            elif score < 0.5:
                insights.append(f"{service.title()} services have limited availability across providers")
        
        return insights
    
    def _identify_emerging_patterns(self, providers_data: Dict[str, Any]) -> List[str]:
        """Identify emerging patterns in the data."""
        patterns = []
        
        # Check for AI/ML service adoption
        ai_services_count = 0
        total_providers = 0
        
        for provider, data in providers_data.items():
            if "error" not in data:
                total_providers += 1
                services = data.get("services", {})
                if "ai_ml" in services and "error" not in services["ai_ml"]:
                    ai_services_count += 1
        
        if ai_services_count > 0:
            patterns.append(f"AI/ML services are available from {ai_services_count}/{total_providers} providers")
        
        # Check for serverless adoption
        serverless_indicators = ["lambda", "functions", "serverless"]
        serverless_count = 0
        
        for provider, data in providers_data.items():
            if "error" not in data:
                services = data.get("services", {})
                for service_category, service_data in services.items():
                    if isinstance(service_data, dict) and "services" in service_data:
                        for service in service_data["services"]:
                            service_name = service.get("name").lower()
                            if any(indicator in service_name for indicator in serverless_indicators):
                                serverless_count += 1
                                break
        
        if serverless_count > 0:
            patterns.append(f"Serverless computing adoption detected across {serverless_count} services")
        
        return patterns
    
    async def _collect_performance_benchmarks(self, workload_types: List[str]) -> Dict[str, Any]:
        """Collect performance benchmarks for workload types."""
        benchmarks = {}
        
        for workload in workload_types:
            if workload == "web_application":
                benchmarks[workload] = {
                    "response_time_ms": {"p50": 100, "p95": 500, "p99": 1000},
                    "throughput_rps": {"low": 100, "medium": 1000, "high": 10000},
                    "cpu_utilization": {"target": 70, "max": 85},
                    "memory_utilization": {"target": 75, "max": 90}
                }
            elif workload == "ai_ml":
                benchmarks[workload] = {
                    "training_time_hours": {"small": 1, "medium": 8, "large": 24},
                    "inference_latency_ms": {"real_time": 100, "batch": 1000},
                    "gpu_utilization": {"target": 80, "max": 95},
                    "memory_gb_per_model": {"small": 4, "medium": 16, "large": 64}
                }
            elif workload == "data_processing":
                benchmarks[workload] = {
                    "processing_time_minutes": {"1gb": 5, "10gb": 30, "100gb": 180},
                    "throughput_gbps": {"standard": 1, "high": 10, "ultra": 100},
                    "storage_iops": {"standard": 3000, "high": 16000, "ultra": 64000}
                }
        
        return benchmarks
    
    async def _collect_cost_benchmarks(self, expected_users: int) -> Dict[str, Any]:
        """Collect cost benchmarks based on user scale."""
        cost_benchmarks = {}
        
        if expected_users < 1000:
            cost_benchmarks["small_scale"] = {
                "monthly_cost_range": {"min": 100, "max": 1000},
                "cost_per_user": {"min": 0.10, "max": 1.00},
                "infrastructure_percentage": {"compute": 60, "storage": 20, "networking": 20}
            }
        elif expected_users < 10000:
            cost_benchmarks["medium_scale"] = {
                "monthly_cost_range": {"min": 1000, "max": 10000},
                "cost_per_user": {"min": 0.50, "max": 2.00},
                "infrastructure_percentage": {"compute": 50, "storage": 30, "networking": 20}
            }
        else:
            cost_benchmarks["large_scale"] = {
                "monthly_cost_range": {"min": 10000, "max": 100000},
                "cost_per_user": {"min": 1.00, "max": 5.00},
                "infrastructure_percentage": {"compute": 40, "storage": 35, "networking": 25}
            }
        
        return cost_benchmarks
    
    async def _collect_industry_benchmarks(self, workload_types: List[str], expected_users: int) -> Dict[str, Any]:
        """Collect industry-specific benchmarks."""
        industry_benchmarks = {
            "availability_targets": {
                "web_application": {"sla": 99.9, "downtime_minutes_month": 43.2},
                "ai_ml": {"sla": 99.5, "downtime_minutes_month": 216},
                "data_processing": {"sla": 99.0, "downtime_minutes_month": 432}
            },
            "security_standards": {
                "encryption_at_rest": "required",
                "encryption_in_transit": "required",
                "access_control": "rbac_required",
                "audit_logging": "required"
            },
            "scalability_patterns": {
                "auto_scaling": expected_users > 1000,
                "load_balancing": expected_users > 500,
                "cdn_usage": expected_users > 100,
                "multi_region": expected_users > 10000
            }
        }
        
        return industry_benchmarks
    
    def _get_typical_cost_for_scale(self, scale_category: str) -> float:
        """Get typical monthly cost for a scale category."""
        cost_mapping = {
            "small_scale": 500.0,
            "medium_scale": 5000.0,
            "large_scale": 50000.0,
            "enterprise_scale": 500000.0
        }
        return cost_mapping.get(scale_category, 1000.0)
    
    def _get_typical_architecture_for_scale(self, scale_category: str) -> List[str]:
        """Get typical architecture components for a scale category."""
        architecture_mapping = {
            "small_scale": ["single_server", "basic_database", "simple_storage"],
            "medium_scale": ["load_balancer", "multiple_servers", "managed_database", "cdn"],
            "large_scale": ["auto_scaling", "microservices", "distributed_database", "caching_layer"],
            "enterprise_scale": ["multi_region", "service_mesh", "data_lakes", "advanced_monitoring"]
        }
        return architecture_mapping.get(scale_category, ["basic_setup"])
    
    def _get_typical_services_for_workload(self, workload: str) -> List[str]:
        """Get typical services needed for a workload type."""
        service_mapping = {
            "web_application": ["compute", "database", "storage", "load_balancer", "cdn"],
            "ai_ml": ["compute", "gpu_compute", "storage", "ml_services", "data_processing"],
            "data_processing": ["compute", "storage", "database", "analytics", "streaming"],
            "mobile_backend": ["compute", "database", "storage", "push_notifications", "authentication"],
            "api_service": ["compute", "database", "caching", "monitoring", "security"]
        }
        return service_mapping.get(workload, ["compute", "storage"])
    
    def _extract_key_findings(self, collected_data: Dict[str, Any], 
                            trend_analysis: Dict[str, Any],
                            benchmark_data: Dict[str, Any]) -> List[str]:
        """Extract key findings from all collected data."""
        findings = []
        
        # Data collection findings
        providers_data = collected_data.get("providers", {})
        successful_providers = [p for p, data in providers_data.items() if "error" not in data]
        
        if successful_providers:
            findings.append(f"Successfully collected data from {len(successful_providers)} cloud providers: {', '.join(successful_providers)}")
        
        # Pricing findings
        pricing_trends = trend_analysis.get("pricing_trends", {})
        cost_leaders = pricing_trends.get("cost_leaders", {})
        
        for service, leader_info in cost_leaders.items():
            provider = leader_info.get("provider")
            if provider:
                findings.append(f"{provider.upper()} identified as cost leader for {service} services")
        
        # Service availability findings
        service_trends = trend_analysis.get("service_trends", {})
        service_availability = service_trends.get("service_availability", {})
        
        universal_services = [
            service for service, info in service_availability.items() 
            if info.get("availability_score", 0) == 1.0
        ]
        
        if universal_services:
            findings.append(f"Universal service availability: {', '.join(universal_services)}")
        
        # Market insights
        market_insights = trend_analysis.get("market_insights", [])
        findings.extend(market_insights[:3])  # Top 3 market insights
        
        return findings
    
    def _generate_data_driven_recommendations(self, key_findings: List[str],
                                            collected_data: Dict[str, Any],
                                            trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on collected data."""
        recommendations = []
        
        # Cost optimization recommendations
        pricing_trends = trend_analysis.get("pricing_trends", {})
        cost_leaders = pricing_trends.get("cost_leaders", {})
        
        if cost_leaders:
            for service, leader_info in cost_leaders.items():
                provider = leader_info.get("provider")
                if provider:
                    recommendations.append({
                        "category": "cost_optimization",
                        "priority": "high",
                        "title": f"Consider {provider.upper()} for {service.title()} Services",
                        "description": f"Data shows {provider.upper()} offers the most cost-effective {service} services",
                        "rationale": f"Real-time pricing analysis identifies {provider.upper()} as cost leader",
                        "data_source": "real_time_pricing_analysis",
                        "confidence": "high"
                    })
        
        # Service availability recommendations
        service_trends = trend_analysis.get("service_trends", {})
        service_availability = service_trends.get("service_availability", {})
        
        limited_services = [
            service for service, info in service_availability.items()
            if info.get("availability_score", 0) < 0.5
        ]
        
        if limited_services:
            recommendations.append({
                "category": "service_selection",
                "priority": "medium",
                "title": "Evaluate Alternative Services",
                "description": f"Limited availability detected for: {', '.join(limited_services)}",
                "rationale": "Some services have limited provider availability",
                "data_source": "service_availability_analysis",
                "confidence": "medium"
            })
        
        # Data quality recommendations
        providers_data = collected_data.get("providers", {})
        failed_providers = [p for p, data in providers_data.items() if "error" in data]
        
        if failed_providers:
            recommendations.append({
                "category": "data_quality",
                "priority": "low",
                "title": "Monitor Data Collection Issues",
                "description": f"Data collection failed for: {', '.join(failed_providers)}",
                "rationale": "Some providers had data collection issues",
                "data_source": "data_collection_monitoring",
                "confidence": "high"
            })
        
        return recommendations
    
    def _assess_confidence_level(self, data_validation: Dict[str, Any], 
                               collected_data: Dict[str, Any]) -> str:
        """Assess confidence level of research findings."""
        quality_score = data_validation.get("quality_score", 0.0)
        providers_data = collected_data.get("providers", {})
        successful_collections = len([p for p, data in providers_data.items() if "error" not in data])
        
        if quality_score >= 0.8 and successful_collections >= 2:
            return "high"
        elif quality_score >= 0.6 and successful_collections >= 1:
            return "medium"
        else:
            return "low"
    
    def _create_research_summary(self, collected_data: Dict[str, Any],
                               trend_analysis: Dict[str, Any],
                               benchmark_data: Dict[str, Any],
                               key_findings: List[str]) -> Dict[str, Any]:
        """Create comprehensive research summary."""
        providers_data = collected_data.get("providers", {})
        
        summary = {
            "data_collection_summary": {
                "providers_queried": list(providers_data.keys()),
                "successful_collections": len([p for p, data in providers_data.items() if "error" not in data]),
                "total_api_calls": collected_data.get("collection_metadata", {}).get("total_api_calls", 0),
                "collection_timestamp": collected_data.get("collection_metadata", {}).get("start_time")
            },
            "pricing_analysis_summary": {
                "cost_leaders_identified": len(trend_analysis.get("pricing_trends", {}).get("cost_leaders", {})),
                "price_ranges_analyzed": len(trend_analysis.get("pricing_trends", {}).get("price_ranges", {})),
                "market_insights_count": len(trend_analysis.get("market_insights", []))
            },
            "benchmark_analysis_summary": {
                "performance_benchmarks": len(benchmark_data.get("performance_benchmarks", {})),
                "cost_benchmarks": len(benchmark_data.get("cost_benchmarks", {})),
                "industry_benchmarks": len(benchmark_data.get("industry_benchmarks", {}))
            },
            "key_findings_count": len(key_findings),
            "research_completeness": self._calculate_research_completeness(
                collected_data, trend_analysis, benchmark_data
            )
        }
        
        return summary
    
    def _calculate_research_completeness(self, collected_data: Dict[str, Any],
                                       trend_analysis: Dict[str, Any],
                                       benchmark_data: Dict[str, Any]) -> float:
        """Calculate overall research completeness score."""
        scores = []
        
        # Data collection completeness
        providers_data = collected_data.get("providers", {})
        if providers_data:
            successful_rate = len([p for p, data in providers_data.items() if "error" not in data]) / len(providers_data)
            scores.append(successful_rate)
        
        # Trend analysis completeness
        pricing_trends = trend_analysis.get("pricing_trends", {})
        if pricing_trends.get("cost_leaders"):
            scores.append(1.0)
        else:
            scores.append(0.5)
        
        # Benchmark data completeness
        benchmark_categories = ["performance_benchmarks", "cost_benchmarks", "industry_benchmarks"]
        benchmark_score = sum(1 for cat in benchmark_categories if benchmark_data.get(cat)) / len(benchmark_categories)
        scores.append(benchmark_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _find_cost_leader(self, provider_pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Find the cost leader among providers for a service."""
        min_price = float('inf')
        cost_leader = None
        
        for provider, pricing_info in provider_pricing.items():
            if isinstance(pricing_info, dict) and "services" in pricing_info:
                services = pricing_info["services"]
                if isinstance(services, list) and services:
                    # Get the cheapest service from this provider
                    provider_min = min(
                        service.get("hourly_price", float('inf')) 
                        for service in services 
                        if isinstance(service, dict) and service.get("hourly_price")
                    )
                    
                    if provider_min < min_price:
                        min_price = provider_min
                        cost_leader = provider
        
        return {
            "provider": cost_leader,
            "min_price": min_price if min_price != float('inf') else None
        }
    
    def _calculate_price_range(self, provider_pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate price range across providers for a service."""
        all_prices = []
        
        for provider, pricing_info in provider_pricing.items():
            if isinstance(pricing_info, dict) and "services" in pricing_info:
                services = pricing_info["services"]
                if isinstance(services, list):
                    for service in services:
                        if isinstance(service, dict) and service.get("hourly_price"):
                            all_prices.append(service["hourly_price"])
        
        if all_prices:
            return {
                "min_price": min(all_prices),
                "max_price": max(all_prices),
                "avg_price": sum(all_prices) / len(all_prices),
                "price_spread": max(all_prices) - min(all_prices)
            }
        
        return {"min_price": None, "max_price": None, "avg_price": None, "price_spread": None}
    
    def _parse_budget_range(self, budget_range: str) -> tuple[float, float]:
        """Parse budget range string to numeric values."""
        budget_mapping = {
            "$1k-10k": (1000, 10000),
            "$10k-50k": (10000, 50000),
            "$50k-100k": (50000, 100000),
            "$100k+": (100000, 500000)
        }
        return budget_mapping.get(budget_range, (10000, 50000))
    
    async def _collect_performance_benchmarks(self, workload_types: List[str]) -> Dict[str, Any]:
        """Collect performance benchmark data."""
        benchmarks = {}
        
        for workload in workload_types:
            # Use calculator tool to generate benchmark estimates
            benchmark_result = await self._use_tool(
                "calculator",
                operation="resource_sizing",
                workload_type=workload,
                users=1000  # Standard benchmark
            )
            
            if benchmark_result.is_success:
                benchmarks[workload] = benchmark_result.data
        
        return benchmarks
    
    async def _collect_cost_benchmarks(self, expected_users: int) -> Dict[str, Any]:
        """Collect cost benchmark data."""
        # Use calculator tool to generate cost benchmarks
        cost_result = await self._use_tool(
            "calculator",
            operation="cost_estimate",
            base_cost=100,  # Base cost for comparison
            users=expected_users,
            scaling_factor=1.0
        )
        
        if cost_result.is_success:
            return {
                "cost_per_user": cost_result.data.get("cost_per_user", 0),
                "monthly_cost": cost_result.data.get("monthly_cost", 0),
                "annual_cost": cost_result.data.get("annual_cost", 0)
            }
        
        return {}
    
    async def _collect_industry_benchmarks(self, workload_types: List[str], 
                                         expected_users: int) -> Dict[str, Any]:
        """Collect industry benchmark data."""
        # Simple industry benchmarks based on workload types and scale
        benchmarks = {
            "industry_averages": {},
            "scale_benchmarks": {},
            "workload_benchmarks": {}
        }
        
        # Scale-based benchmarks
        if expected_users < 1000:
            scale_category = "small"
        elif expected_users < 10000:
            scale_category = "medium"
        else:
            scale_category = "large"
        
        benchmarks["scale_benchmarks"] = {
            "category": scale_category,
            "typical_monthly_cost": self._get_typical_cost_for_scale(scale_category),
            "typical_architecture": self._get_typical_architecture_for_scale(scale_category)
        }
        
        # Workload-specific benchmarks
        for workload in workload_types:
            benchmarks["workload_benchmarks"][workload] = {
                "typical_services": self._get_typical_services_for_workload(workload),
                "performance_expectations": self._get_performance_expectations(workload)
            }
        
        return benchmarks
    
    def _get_performance_expectations(self, workload: str) -> Dict[str, Any]:
        """Get performance expectations for a specific workload type."""
        expectations = {
            "web_application": {
                "response_time_ms": {"target": 200, "acceptable": 500},
                "throughput_rps": {"minimum": 100, "target": 1000},
                "availability": {"target": 99.9, "minimum": 99.0}
            },
            "api_service": {
                "response_time_ms": {"target": 100, "acceptable": 300},
                "throughput_rps": {"minimum": 500, "target": 5000},
                "availability": {"target": 99.95, "minimum": 99.5}
            },
            "data_processing": {
                "processing_time": {"acceptable": "minutes", "target": "seconds"},
                "throughput": {"minimum": "1GB/min", "target": "10GB/min"},
                "availability": {"target": 99.5, "minimum": 99.0}
            },
            "ml_workload": {
                "training_time": {"acceptable": "hours", "target": "minutes"},
                "inference_latency_ms": {"target": 50, "acceptable": 200},
                "availability": {"target": 99.9, "minimum": 99.0}
            }
        }
        
        return expectations.get(workload, {
            "response_time_ms": {"target": 500, "acceptable": 1000},
            "availability": {"target": 99.0, "minimum": 95.0}
        })
    
    def _extract_key_findings(self, collected_data: Dict[str, Any], 
                            trend_analysis: Dict[str, Any],
                            benchmark_data: Dict[str, Any]) -> List[str]:
        """Extract key findings from all collected data."""
        findings = []
        
        # Data collection findings
        providers_data = collected_data.get("providers", {})
        successful_providers = [p for p, d in providers_data.items() if "error" not in d]
        
        if successful_providers:
            findings.append(f"Successfully collected data from {len(successful_providers)} cloud provider(s): {', '.join(successful_providers)}")
        
        # Pricing findings
        pricing_trends = trend_analysis.get("pricing_trends", {})
        cost_leaders = pricing_trends.get("cost_leaders", {})
        
        if cost_leaders:
            findings.append(f"Identified cost leaders across {len(cost_leaders)} service categories")
        
        # Service availability findings
        service_trends = trend_analysis.get("service_trends", {})
        service_availability = service_trends.get("service_availability", {})
        
        universal_services = [s for s, info in service_availability.items() 
                            if info.get("availability_score", 0) == 1.0]
        if universal_services:
            findings.append(f"Universal service availability: {', '.join(universal_services)}")
        
        # Benchmark findings
        performance_benchmarks = benchmark_data.get("performance_benchmarks", {})
        if performance_benchmarks:
            findings.append(f"Collected performance benchmarks for {len(performance_benchmarks)} workload type(s)")
        
        return findings
    
    def _generate_data_driven_recommendations(self, key_findings: List[str],
                                            collected_data: Dict[str, Any],
                                            trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on research data."""
        recommendations = []
        
        # Cost optimization recommendations
        pricing_trends = trend_analysis.get("pricing_trends", {})
        cost_leaders = pricing_trends.get("cost_leaders", {})
        
        for service, leader_info in cost_leaders.items():
            provider = leader_info.get("provider")
            savings = leader_info.get("potential_savings", 0)
            
            if provider and savings > 0:
                recommendations.append({
                    "category": "cost_optimization",
                    "priority": "high" if savings > 100 else "medium",
                    "title": f"Consider {provider.upper()} for {service} services",
                    "description": f"{provider.upper()} offers the most cost-effective {service} services",
                    "rationale": f"Research shows potential monthly savings of ${savings:.2f}",
                    "data_confidence": "high",
                    "supporting_data": leader_info
                })
        
        # Service availability recommendations
        service_trends = trend_analysis.get("service_trends", {})
        service_availability = service_trends.get("service_availability", {})
        
        limited_services = [s for s, info in service_availability.items() 
                          if info.get("availability_score", 0) < 0.5]
        
        if limited_services:
            recommendations.append({
                "category": "service_availability",
                "priority": "medium",
                "title": "Consider alternative providers for specialized services",
                "description": f"Limited availability detected for: {', '.join(limited_services)}",
                "rationale": "Research indicates these services may require specific provider selection",
                "data_confidence": "medium",
                "supporting_data": {"limited_services": limited_services}
            })
        
        # Data quality recommendations
        providers_data = collected_data.get("providers", {})
        failed_providers = [p for p, d in providers_data.items() if "error" in d]
        
        if failed_providers:
            recommendations.append({
                "category": "data_quality",
                "priority": "low",
                "title": "Monitor data collection reliability",
                "description": f"Data collection failed for: {', '.join(failed_providers)}",
                "rationale": "Incomplete data may affect recommendation accuracy",
                "data_confidence": "low",
                "supporting_data": {"failed_providers": failed_providers}
            })
        
        return recommendations
    
    def _assess_confidence_level(self, data_validation: Dict[str, Any], 
                               collected_data: Dict[str, Any]) -> str:
        """Assess confidence level in research findings."""
        quality_score = data_validation.get("quality_score", 0.0)
        
        providers_data = collected_data.get("providers", {})
        successful_providers = len([p for p, d in providers_data.items() if "error" not in d])
        
        # Base confidence on data quality and provider coverage
        if quality_score >= 0.8 and successful_providers >= 2:
            return "high"
        elif quality_score >= 0.6 and successful_providers >= 1:
            return "medium"
        else:
            return "low"
    
    def _create_research_summary(self, collected_data: Dict[str, Any],
                               trend_analysis: Dict[str, Any],
                               benchmark_data: Dict[str, Any],
                               key_findings: List[str]) -> Dict[str, Any]:
        """Create a comprehensive research summary."""
        providers_data = collected_data.get("providers", {})
        
        return {
            "data_collection_summary": {
                "providers_analyzed": len(providers_data),
                "successful_collections": len([p for p, d in providers_data.items() if "error" not in d]),
                "total_api_calls": sum(1 for p, d in providers_data.items() if "error" not in d) * 2,  # Estimate
                "collection_duration": "< 1 minute"
            },
            "trend_analysis_summary": {
                "pricing_trends_identified": len(trend_analysis.get("pricing_trends", {}).get("cost_leaders", {})),
                "service_trends_analyzed": len(trend_analysis.get("service_trends", {}).get("service_availability", {})),
                "market_insights_generated": len(trend_analysis.get("market_insights", []))
            },
            "benchmark_summary": {
                "performance_benchmarks": len(benchmark_data.get("performance_benchmarks", {})),
                "cost_benchmarks_available": bool(benchmark_data.get("cost_benchmarks")),
                "industry_benchmarks": len(benchmark_data.get("industry_benchmarks", {}))
            },
            "key_findings_count": len(key_findings),
            "research_completeness": "comprehensive" if len(key_findings) >= 3 else "basic"
        }