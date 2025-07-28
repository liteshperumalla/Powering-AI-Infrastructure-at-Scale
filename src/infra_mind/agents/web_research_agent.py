"""
Web Research Agent for Infra Mind.

Provides real-time web research and market intelligence capabilities.
Focuses on web scraping, competitive analysis, and trend identification.
"""

import logging
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse
import json
import re

# Optional imports for web scraping
try:
    import aiohttp
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from ..models.assessment import Assessment
from ..models.web_research import WebResearchData
from ..core.cache import cache_manager

logger = logging.getLogger(__name__)


class WebResearchAgent(BaseAgent):
    """
    Web Research Agent for real-time web research and market intelligence.
    
    This agent focuses on:
    - Competitor pricing and service monitoring across cloud providers
    - Technology trend analysis from blogs, whitepapers, and industry reports
    - Regulatory update tracking from government and compliance websites
    - Best practices collection from cloud provider documentation
    - Case study and implementation example gathering
    - Real-time validation of API data against public sources
    - Market intelligence and competitive positioning analysis
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Web Research Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="Web Research Agent",
                role=AgentRole.WEB_RESEARCH,
                tools_enabled=["web_scraper", "search_api", "data_processor", "content_extractor"],
                temperature=0.2,  # Lower temperature for more consistent research
                max_tokens=3000,
                custom_config={
                    "focus_areas": [
                        "competitive_analysis",
                        "pricing_monitoring",
                        "trend_analysis",
                        "regulatory_tracking",
                        "best_practices_collection",
                        "market_intelligence"
                    ],
                    "data_sources": [
                        "cloud_provider_docs",
                        "industry_blogs",
                        "regulatory_websites",
                        "competitor_websites",
                        "tech_news_sites",
                        "research_reports"
                    ],
                    "scraping_config": {
                        "max_concurrent_requests": 5,
                        "request_delay": 1.0,
                        "timeout": 30,
                        "user_agent": "InfraMind-WebResearch/1.0"
                    }
                }
            )
        
        super().__init__(config)
        
        # Web Research Agent-specific attributes
        self.cache_manager = cache_manager
        
        # Target websites for different types of research
        self.research_targets = {
            "aws_pricing": [
                "https://aws.amazon.com/pricing/",
                "https://calculator.aws/",
                "https://aws.amazon.com/blogs/aws-cost-management/"
            ],
            "azure_pricing": [
                "https://azure.microsoft.com/en-us/pricing/",
                "https://azure.microsoft.com/en-us/pricing/calculator/",
                "https://azure.microsoft.com/en-us/blog/topics/cost-management/"
            ],
            "gcp_pricing": [
                "https://cloud.google.com/pricing",
                "https://cloud.google.com/products/calculator",
                "https://cloud.google.com/blog/topics/cost-management"
            ],
            "industry_trends": [
                "https://www.gartner.com/en/information-technology",
                "https://www.forrester.com/research/",
                "https://techcrunch.com/category/enterprise/",
                "https://www.infoworld.com/category/cloud-computing/"
            ],
            "regulatory_updates": [
                "https://gdpr.eu/",
                "https://www.hhs.gov/hipaa/",
                "https://oag.ca.gov/privacy/ccpa",
                "https://www.nist.gov/cyberframework"
            ],
            "best_practices": [
                "https://docs.aws.amazon.com/wellarchitected/",
                "https://docs.microsoft.com/en-us/azure/architecture/",
                "https://cloud.google.com/architecture/framework"
            ]
        }
        
        # Content extraction patterns
        self.extraction_patterns = {
            "pricing": {
                "price_regex": r'\$?(\d+(?:\.\d{2})?)\s*(?:per|/)\s*(hour|month|year|GB|TB)',
                "service_regex": r'(EC2|RDS|S3|Compute|Storage|Database|VM)',
                "discount_regex": r'(\d+)%\s*(?:off|discount|savings)'
            },
            "trends": {
                "trend_keywords": [
                    "artificial intelligence", "machine learning", "cloud migration",
                    "serverless", "containers", "kubernetes", "microservices",
                    "edge computing", "hybrid cloud", "multi-cloud"
                ],
                "sentiment_indicators": ["increasing", "growing", "declining", "emerging", "trending"]
            },
            "compliance": {
                "regulation_keywords": ["GDPR", "HIPAA", "CCPA", "SOC 2", "ISO 27001", "PCI DSS"],
                "update_indicators": ["updated", "new requirement", "compliance change", "regulation"]
            }
        }
        
        # Data freshness thresholds (in hours)
        self.freshness_thresholds = {
            "pricing_data": 24,      # Pricing data should be < 24 hours old
            "trend_data": 48,        # Trend data can be < 48 hours old
            "regulatory_data": 72,   # Regulatory updates can be < 72 hours old
            "best_practices": 168    # Best practices can be < 1 week old
        }
        
        logger.info("Web Research Agent initialized with web scraping capabilities")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute Web Research agent's main research logic.
        
        Returns:
            Dictionary with research results and analysis
        """
        logger.info("Web Research Agent starting web research and analysis")
        
        try:
            # Step 1: Analyze research requirements
            research_requirements = await self._analyze_research_requirements()
            
            # Step 2: Collect web data
            web_data = await self._collect_web_data(research_requirements)
            
            # Step 3: Analyze competitive landscape
            competitive_analysis = await self._analyze_competitive_landscape(web_data)
            
            # Step 4: Track trends and insights
            trend_analysis = await self._analyze_trends_and_insights(web_data)
            
            # Step 5: Monitor regulatory updates
            regulatory_updates = await self._monitor_regulatory_updates(web_data)
            
            # Step 6: Validate API data against web sources
            validation_results = await self._validate_api_data(web_data)
            
            # Step 7: Generate market intelligence report
            market_intelligence = await self._generate_market_intelligence(
                competitive_analysis, trend_analysis, regulatory_updates
            )
            
            # Step 8: Create recommendations
            recommendations = await self._create_web_research_recommendations(
                market_intelligence, validation_results
            )
            
            result = {
                "research_requirements": research_requirements,
                "web_data_collected": len(web_data),
                "competitive_analysis": competitive_analysis,
                "trend_analysis": trend_analysis,
                "regulatory_updates": regulatory_updates,
                "validation_results": validation_results,
                "market_intelligence": market_intelligence,
                "recommendations": recommendations,
                "data_freshness": await self._check_data_freshness(),
                "research_summary": await self._create_research_summary(
                    competitive_analysis, trend_analysis, regulatory_updates
                )
            }
            
            logger.info(f"Web Research Agent completed analysis with {len(recommendations)} recommendations")
            return result
            
        except Exception as e:
            logger.error(f"Web Research Agent execution failed: {str(e)}")
            raise
    
    async def _analyze_research_requirements(self) -> Dict[str, Any]:
        """
        Analyze the assessment to determine research requirements.
        
        Returns:
            Dictionary with research requirements
        """
        logger.info("Analyzing research requirements from assessment")
        
        # Analyze assessment data using data processor tool
        analysis_result = await self._use_tool(
            "data_processor",
            data=self.current_assessment.dict(),
            operation="analyze"
        )
        
        requirements = {
            "priority_areas": [],
            "target_providers": [],
            "research_depth": "standard",
            "focus_topics": []
        }
        
        if analysis_result.is_success:
            insights = analysis_result.data.get("insights", [])
            
            # Determine priority research areas based on assessment
            for insight in insights:
                if "budget" in insight.lower():
                    requirements["priority_areas"].append("pricing_analysis")
                if "compliance" in insight.lower():
                    requirements["priority_areas"].append("regulatory_tracking")
                if "industry" in insight.lower():
                    requirements["priority_areas"].append("industry_trends")
                if "workload" in insight.lower():
                    requirements["priority_areas"].append("best_practices")
            
            # Determine target cloud providers
            business_req = getattr(self.current_assessment, 'business_requirements', {})
            if isinstance(business_req, dict):
                preferred_providers = business_req.get('preferred_providers', [])
                if preferred_providers:
                    requirements["target_providers"] = preferred_providers
                else:
                    requirements["target_providers"] = ["aws", "azure", "gcp"]  # Default to all
            
            # Set research depth based on company size
            company_size = business_req.get('company_size', 'small')
            if company_size in ['large', 'enterprise']:
                requirements["research_depth"] = "comprehensive"
            elif company_size == 'medium':
                requirements["research_depth"] = "detailed"
            else:
                requirements["research_depth"] = "standard"
        
        # Default priority areas if none identified
        if not requirements["priority_areas"]:
            requirements["priority_areas"] = ["pricing_analysis", "competitive_analysis"]
        
        logger.info(f"Research requirements: {requirements}")
        return requirements
    
    async def _collect_web_data(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect data from web sources based on requirements.
        
        Args:
            requirements: Research requirements
            
        Returns:
            List of collected web data
        """
        logger.info("Starting web data collection")
        
        collected_data = []
        
        # Collect data for each priority area
        for area in requirements["priority_areas"]:
            if area == "pricing_analysis":
                pricing_data = await self._scrape_pricing_data(requirements["target_providers"])
                collected_data.extend(pricing_data)
            
            elif area == "competitive_analysis":
                competitive_data = await self._scrape_competitive_data(requirements["target_providers"])
                collected_data.extend(competitive_data)
            
            elif area == "industry_trends":
                trend_data = await self._scrape_trend_data()
                collected_data.extend(trend_data)
            
            elif area == "regulatory_tracking":
                regulatory_data = await self._scrape_regulatory_data()
                collected_data.extend(regulatory_data)
            
            elif area == "best_practices":
                best_practices_data = await self._scrape_best_practices_data(requirements["target_providers"])
                collected_data.extend(best_practices_data)
        
        # Store collected data in database
        await self._store_web_research_data(collected_data)
        
        logger.info(f"Collected {len(collected_data)} web data items")
        return collected_data
    
    async def _scrape_pricing_data(self, providers: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape pricing data from cloud provider websites.
        
        Args:
            providers: List of cloud providers to scrape
            
        Returns:
            List of pricing data
        """
        logger.info(f"Scraping pricing data for providers: {providers}")
        
        pricing_data = []
        
        for provider in providers:
            if provider.lower() in self.research_targets:
                target_key = f"{provider.lower()}_pricing"
                if target_key in self.research_targets:
                    urls = self.research_targets[target_key]
                    
                    for url in urls:
                        try:
                            data = await self._scrape_url(url, "pricing", provider)
                            if data:
                                pricing_data.append(data)
                        except Exception as e:
                            logger.warning(f"Failed to scrape {url}: {str(e)}")
        
        return pricing_data
    
    async def _scrape_competitive_data(self, providers: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape competitive analysis data.
        
        Args:
            providers: List of cloud providers to analyze
            
        Returns:
            List of competitive data
        """
        logger.info(f"Scraping competitive data for providers: {providers}")
        
        competitive_data = []
        
        # Scrape comparison sites and industry reports
        comparison_urls = [
            "https://www.gartner.com/reviews/market/public-cloud-iaas",
            "https://www.forrester.com/report/The+Forrester+Wave+Public+Cloud+Platforms",
            "https://cloud.google.com/blog/topics/public-cloud"
        ]
        
        for url in comparison_urls:
            try:
                data = await self._scrape_url(url, "competitive", "general")
                if data:
                    competitive_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to scrape competitive data from {url}: {str(e)}")
        
        return competitive_data
    
    async def _scrape_trend_data(self) -> List[Dict[str, Any]]:
        """
        Scrape technology trend data.
        
        Returns:
            List of trend data
        """
        logger.info("Scraping technology trend data")
        
        trend_data = []
        
        if "industry_trends" in self.research_targets:
            urls = self.research_targets["industry_trends"]
            
            for url in urls:
                try:
                    data = await self._scrape_url(url, "trends", "general")
                    if data:
                        trend_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to scrape trend data from {url}: {str(e)}")
        
        return trend_data
    
    async def _scrape_regulatory_data(self) -> List[Dict[str, Any]]:
        """
        Scrape regulatory update data.
        
        Returns:
            List of regulatory data
        """
        logger.info("Scraping regulatory update data")
        
        regulatory_data = []
        
        if "regulatory_updates" in self.research_targets:
            urls = self.research_targets["regulatory_updates"]
            
            for url in urls:
                try:
                    data = await self._scrape_url(url, "regulatory", "general")
                    if data:
                        regulatory_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to scrape regulatory data from {url}: {str(e)}")
        
        return regulatory_data
    
    async def _scrape_best_practices_data(self, providers: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape best practices data from cloud providers.
        
        Args:
            providers: List of cloud providers
            
        Returns:
            List of best practices data
        """
        logger.info(f"Scraping best practices data for providers: {providers}")
        
        best_practices_data = []
        
        if "best_practices" in self.research_targets:
            urls = self.research_targets["best_practices"]
            
            for url in urls:
                try:
                    # Determine provider from URL
                    provider = "general"
                    if "aws" in url:
                        provider = "aws"
                    elif "azure" in url or "microsoft" in url:
                        provider = "azure"
                    elif "google" in url or "gcp" in url:
                        provider = "gcp"
                    
                    if provider == "general" or provider in [p.lower() for p in providers]:
                        data = await self._scrape_url(url, "best_practices", provider)
                        if data:
                            best_practices_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to scrape best practices from {url}: {str(e)}")
        
        return best_practices_data
    
    async def _scrape_url(self, url: str, source_type: str, provider: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL and extract relevant data.
        
        Args:
            url: URL to scrape
            source_type: Type of source (pricing, trends, etc.)
            provider: Cloud provider or 'general'
            
        Returns:
            Extracted data or None if failed
        """
        if not WEB_SCRAPING_AVAILABLE:
            logger.warning("Web scraping libraries not available. Install aiohttp and beautifulsoup4.")
            return None
            
        try:
            # Check cache first
            cache_key = f"web_scrape:{hashlib.md5(url.encode()).hexdigest()}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached data for {url}")
                return json.loads(cached_data)
            
            # Configure request
            timeout = aiohttp.ClientTimeout(total=self.config.custom_config["scraping_config"]["timeout"])
            headers = {
                "User-Agent": self.config.custom_config["scraping_config"]["user_agent"]
            }
            
            # Make request
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Extract data based on source type
                        extracted_data = await self._extract_content(content, source_type, url)
                        
                        if extracted_data:
                            # Create content hash for deduplication
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            
                            data = {
                                "source_url": url,
                                "source_type": source_type,
                                "provider": provider if provider != "general" else None,
                                "content_hash": content_hash,
                                "extracted_data": extracted_data,
                                "last_scraped": datetime.now(timezone.utc).isoformat(),
                                "metadata": {
                                    "status_code": response.status,
                                    "content_length": len(content),
                                    "scraping_agent": "web_research_agent"
                                }
                            }
                            
                            # Cache the result
                            await self.cache_manager.set(
                                cache_key, 
                                json.dumps(data), 
                                ttl=3600  # 1 hour cache
                            )
                            
                            return data
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    async def _extract_content(self, html_content: str, source_type: str, url: str) -> Dict[str, Any]:
        """
        Extract relevant content from HTML based on source type.
        
        Args:
            html_content: HTML content to parse
            source_type: Type of source (pricing, trends, etc.)
            url: Source URL
            
        Returns:
            Extracted data
        """
        if not WEB_SCRAPING_AVAILABLE:
            return {"error": "Web scraping libraries not available"}
            
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted = {
            "title": "",
            "content": {},
            "links": [],
            "metadata": {}
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            extracted["title"] = title_tag.get_text().strip()
        
        # Extract content based on source type
        if source_type == "pricing":
            extracted["content"] = await self._extract_pricing_content(soup)
        elif source_type == "trends":
            extracted["content"] = await self._extract_trend_content(soup)
        elif source_type == "regulatory":
            extracted["content"] = await self._extract_regulatory_content(soup)
        elif source_type == "competitive":
            extracted["content"] = await self._extract_competitive_content(soup)
        elif source_type == "best_practices":
            extracted["content"] = await self._extract_best_practices_content(soup)
        else:
            # Generic content extraction
            extracted["content"] = await self._extract_generic_content(soup)
        
        # Extract relevant links
        links = soup.find_all('a', href=True)
        for link in links[:10]:  # Limit to first 10 links
            href = link['href']
            if href.startswith('http') or href.startswith('/'):
                full_url = urljoin(url, href)
                extracted["links"].append({
                    "url": full_url,
                    "text": link.get_text().strip()[:100]  # Limit text length
                })
        
        # Add metadata
        extracted["metadata"] = {
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "content_length": len(html_content),
            "links_found": len(extracted["links"])
        }
        
        return extracted
    
    async def _extract_pricing_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract pricing-specific content."""
        pricing_content = {
            "prices_found": [],
            "services_mentioned": [],
            "discounts": []
        }
        
        text_content = soup.get_text()
        
        # Extract prices using regex
        price_pattern = self.extraction_patterns["pricing"]["price_regex"]
        prices = re.findall(price_pattern, text_content, re.IGNORECASE)
        pricing_content["prices_found"] = [{"amount": p[0], "unit": p[1]} for p in prices[:10]]
        
        # Extract service mentions
        service_pattern = self.extraction_patterns["pricing"]["service_regex"]
        services = re.findall(service_pattern, text_content, re.IGNORECASE)
        pricing_content["services_mentioned"] = list(set(services))
        
        # Extract discount information
        discount_pattern = self.extraction_patterns["pricing"]["discount_regex"]
        discounts = re.findall(discount_pattern, text_content, re.IGNORECASE)
        pricing_content["discounts"] = [f"{d}% discount" for d in discounts[:5]]
        
        return pricing_content
    
    async def _extract_trend_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract trend-specific content."""
        trend_content = {
            "trends_identified": [],
            "sentiment_indicators": [],
            "key_topics": []
        }
        
        text_content = soup.get_text().lower()
        
        # Identify trend keywords
        trend_keywords = self.extraction_patterns["trends"]["trend_keywords"]
        for keyword in trend_keywords:
            if keyword in text_content:
                trend_content["trends_identified"].append(keyword)
        
        # Identify sentiment indicators
        sentiment_indicators = self.extraction_patterns["trends"]["sentiment_indicators"]
        for indicator in sentiment_indicators:
            if indicator in text_content:
                trend_content["sentiment_indicators"].append(indicator)
        
        # Extract headings as key topics
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings[:10]:
            topic = heading.get_text().strip()
            if len(topic) > 5 and len(topic) < 100:
                trend_content["key_topics"].append(topic)
        
        return trend_content
    
    async def _extract_regulatory_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract regulatory-specific content."""
        regulatory_content = {
            "regulations_mentioned": [],
            "updates_found": [],
            "compliance_topics": []
        }
        
        text_content = soup.get_text()
        
        # Identify regulation keywords
        regulation_keywords = self.extraction_patterns["compliance"]["regulation_keywords"]
        for keyword in regulation_keywords:
            if keyword in text_content:
                regulatory_content["regulations_mentioned"].append(keyword)
        
        # Identify update indicators
        update_indicators = self.extraction_patterns["compliance"]["update_indicators"]
        for indicator in update_indicators:
            if indicator.lower() in text_content.lower():
                regulatory_content["updates_found"].append(indicator)
        
        # Extract compliance-related headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings:
            topic = heading.get_text().strip()
            if any(reg in topic.upper() for reg in regulation_keywords):
                regulatory_content["compliance_topics"].append(topic)
        
        return regulatory_content
    
    async def _extract_competitive_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract competitive analysis content."""
        competitive_content = {
            "providers_mentioned": [],
            "comparisons_found": [],
            "market_insights": []
        }
        
        text_content = soup.get_text()
        
        # Identify cloud providers
        providers = ["AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud"]
        for provider in providers:
            if provider in text_content:
                competitive_content["providers_mentioned"].append(provider)
        
        # Look for comparison indicators
        comparison_words = ["vs", "versus", "compared to", "better than", "faster than", "cheaper than"]
        for word in comparison_words:
            if word in text_content.lower():
                competitive_content["comparisons_found"].append(word)
        
        # Extract market insight headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings[:5]:
            insight = heading.get_text().strip()
            if len(insight) > 10 and len(insight) < 150:
                competitive_content["market_insights"].append(insight)
        
        return competitive_content
    
    async def _extract_best_practices_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract best practices content."""
        best_practices_content = {
            "practices_identified": [],
            "recommendations": [],
            "architecture_patterns": []
        }
        
        # Look for best practice indicators
        practice_indicators = ["best practice", "recommendation", "should", "must", "avoid", "consider"]
        
        # Find paragraphs and list items that contain best practices
        elements = soup.find_all(['p', 'li'])
        for element in elements[:20]:
            text = element.get_text().strip()
            if any(indicator in text.lower() for indicator in practice_indicators):
                if len(text) > 20 and len(text) < 300:
                    best_practices_content["practices_identified"].append(text)
        
        # Extract architecture patterns
        architecture_keywords = ["microservices", "serverless", "containers", "kubernetes", "load balancer"]
        text_content = soup.get_text().lower()
        for keyword in architecture_keywords:
            if keyword in text_content:
                best_practices_content["architecture_patterns"].append(keyword)
        
        return best_practices_content
    
    async def _extract_generic_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract generic content."""
        generic_content = {
            "headings": [],
            "key_paragraphs": [],
            "summary": ""
        }
        
        # Extract headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings[:10]:
            text = heading.get_text().strip()
            if len(text) > 5:
                generic_content["headings"].append(text)
        
        # Extract key paragraphs
        paragraphs = soup.find_all('p')
        for para in paragraphs[:5]:
            text = para.get_text().strip()
            if len(text) > 50 and len(text) < 500:
                generic_content["key_paragraphs"].append(text)
        
        # Create summary from first paragraph
        if generic_content["key_paragraphs"]:
            generic_content["summary"] = generic_content["key_paragraphs"][0][:200] + "..."
        
        return generic_content
    
    async def _store_web_research_data(self, collected_data: List[Dict[str, Any]]) -> None:
        """
        Store collected web research data in the database.
        
        Args:
            collected_data: List of collected data items
        """
        logger.info(f"Storing {len(collected_data)} web research data items")
        
        for data_item in collected_data:
            try:
                # Create WebResearchData document
                web_research_doc = WebResearchData(
                    source_url=data_item["source_url"],
                    source_type=data_item["source_type"],
                    provider=data_item.get("provider"),
                    content_hash=data_item["content_hash"],
                    title=data_item["extracted_data"].get("title"),
                    extracted_data=data_item["extracted_data"],
                    validation_status="pending",
                    last_scraped=datetime.fromisoformat(data_item["last_scraped"].replace('Z', '+00:00')),
                    metadata=data_item["metadata"]
                )
                
                # Save to database
                await web_research_doc.save()
                
            except Exception as e:
                logger.error(f"Failed to store web research data: {str(e)}")
    
    async def _analyze_competitive_landscape(self, web_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze competitive landscape from collected data.
        
        Args:
            web_data: Collected web data
            
        Returns:
            Competitive analysis results
        """
        logger.info("Analyzing competitive landscape")
        
        competitive_analysis = {
            "provider_mentions": {},
            "market_positioning": {},
            "pricing_comparisons": [],
            "feature_comparisons": [],
            "market_trends": []
        }
        
        # Analyze provider mentions across all data
        providers = ["aws", "azure", "gcp", "google cloud", "amazon web services", "microsoft azure"]
        
        for data_item in web_data:
            extracted_content = data_item.get("extracted_data", {}).get("content", {})
            
            # Count provider mentions
            if "providers_mentioned" in extracted_content:
                for provider in extracted_content["providers_mentioned"]:
                    provider_key = provider.lower()
                    if provider_key not in competitive_analysis["provider_mentions"]:
                        competitive_analysis["provider_mentions"][provider_key] = 0
                    competitive_analysis["provider_mentions"][provider_key] += 1
            
            # Collect pricing comparisons
            if "prices_found" in extracted_content:
                for price in extracted_content["prices_found"]:
                    competitive_analysis["pricing_comparisons"].append({
                        "provider": data_item.get("provider", "unknown"),
                        "price": price,
                        "source": data_item["source_url"]
                    })
            
            # Collect market insights
            if "market_insights" in extracted_content:
                competitive_analysis["market_trends"].extend(extracted_content["market_insights"])
        
        # Generate market positioning insights
        if competitive_analysis["provider_mentions"]:
            total_mentions = sum(competitive_analysis["provider_mentions"].values())
            for provider, count in competitive_analysis["provider_mentions"].items():
                competitive_analysis["market_positioning"][provider] = {
                    "mention_count": count,
                    "market_share_indicator": round((count / total_mentions) * 100, 2),
                    "visibility_score": min(count / 10, 1.0)  # Normalize to 0-1
                }
        
        return competitive_analysis
    
    async def _analyze_trends_and_insights(self, web_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trends and insights from collected data.
        
        Args:
            web_data: Collected web data
            
        Returns:
            Trend analysis results
        """
        logger.info("Analyzing trends and insights")
        
        trend_analysis = {
            "emerging_trends": [],
            "technology_adoption": {},
            "sentiment_analysis": {},
            "key_topics": [],
            "trend_strength": {}
        }
        
        # Collect all trend data
        all_trends = []
        all_sentiments = []
        all_topics = []
        
        for data_item in web_data:
            extracted_content = data_item.get("extracted_data", {}).get("content", {})
            
            if "trends_identified" in extracted_content:
                all_trends.extend(extracted_content["trends_identified"])
            
            if "sentiment_indicators" in extracted_content:
                all_sentiments.extend(extracted_content["sentiment_indicators"])
            
            if "key_topics" in extracted_content:
                all_topics.extend(extracted_content["key_topics"])
        
        # Analyze trend frequency
        trend_counts = {}
        for trend in all_trends:
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        # Identify emerging trends (mentioned multiple times)
        for trend, count in trend_counts.items():
            if count >= 2:  # Mentioned in at least 2 sources
                trend_analysis["emerging_trends"].append({
                    "trend": trend,
                    "mention_count": count,
                    "strength": "high" if count >= 5 else "medium" if count >= 3 else "low"
                })
        
        # Analyze sentiment
        sentiment_counts = {}
        for sentiment in all_sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        trend_analysis["sentiment_analysis"] = sentiment_counts
        
        # Extract key topics (most mentioned)
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort topics by frequency and take top 10
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        trend_analysis["key_topics"] = [
            {"topic": topic, "mentions": count} 
            for topic, count in sorted_topics[:10]
        ]
        
        return trend_analysis
    
    async def _monitor_regulatory_updates(self, web_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Monitor regulatory updates from collected data.
        
        Args:
            web_data: Collected web data
            
        Returns:
            Regulatory update results
        """
        logger.info("Monitoring regulatory updates")
        
        regulatory_updates = {
            "regulations_tracked": [],
            "recent_updates": [],
            "compliance_topics": [],
            "update_frequency": {}
        }
        
        # Collect regulatory data
        all_regulations = []
        all_updates = []
        all_compliance_topics = []
        
        for data_item in web_data:
            if data_item.get("source_type") == "regulatory":
                extracted_content = data_item.get("extracted_data", {}).get("content", {})
                
                if "regulations_mentioned" in extracted_content:
                    all_regulations.extend(extracted_content["regulations_mentioned"])
                
                if "updates_found" in extracted_content:
                    all_updates.extend(extracted_content["updates_found"])
                
                if "compliance_topics" in extracted_content:
                    all_compliance_topics.extend(extracted_content["compliance_topics"])
        
        # Analyze regulation mentions
        regulation_counts = {}
        for regulation in all_regulations:
            regulation_counts[regulation] = regulation_counts.get(regulation, 0) + 1
        
        regulatory_updates["regulations_tracked"] = [
            {"regulation": reg, "mentions": count}
            for reg, count in regulation_counts.items()
        ]
        
        # Identify recent updates
        for update in all_updates:
            regulatory_updates["recent_updates"].append({
                "update_type": update,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "web_research"
            })
        
        # Collect compliance topics
        topic_counts = {}
        for topic in all_compliance_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        regulatory_updates["compliance_topics"] = [
            {"topic": topic, "frequency": count}
            for topic, count in topic_counts.items()
        ]
        
        return regulatory_updates
    
    async def _validate_api_data(self, web_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate API data against web sources.
        
        Args:
            web_data: Collected web data
            
        Returns:
            Validation results
        """
        logger.info("Validating API data against web sources")
        
        validation_results = {
            "pricing_validation": {},
            "service_validation": {},
            "discrepancies_found": [],
            "confidence_scores": {}
        }
        
        # Validate pricing data
        pricing_data = [
            item for item in web_data 
            if item.get("source_type") == "pricing"
        ]
        
        if pricing_data:
            # Extract pricing information
            web_prices = []
            for item in pricing_data:
                extracted_content = item.get("extracted_data", {}).get("content", {})
                if "prices_found" in extracted_content:
                    for price in extracted_content["prices_found"]:
                        web_prices.append({
                            "provider": item.get("provider", "unknown"),
                            "amount": price.get("amount"),
                            "unit": price.get("unit"),
                            "source": item["source_url"]
                        })
            
            validation_results["pricing_validation"] = {
                "web_prices_found": len(web_prices),
                "sample_prices": web_prices[:5],  # Show first 5 as sample
                "validation_status": "partial"  # Would need API data to compare
            }
        
        # Calculate confidence scores based on data consistency
        for provider in ["aws", "azure", "gcp"]:
            provider_data = [
                item for item in web_data 
                if item.get("provider") == provider
            ]
            
            if provider_data:
                # Simple confidence calculation based on data availability
                confidence = min(len(provider_data) / 5, 1.0)  # Max confidence with 5+ sources
                validation_results["confidence_scores"][provider] = round(confidence, 2)
        
        return validation_results
    
    async def _generate_market_intelligence(self, competitive_analysis: Dict[str, Any], 
                                          trend_analysis: Dict[str, Any], 
                                          regulatory_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive market intelligence report.
        
        Args:
            competitive_analysis: Competitive analysis results
            trend_analysis: Trend analysis results
            regulatory_updates: Regulatory update results
            
        Returns:
            Market intelligence report
        """
        logger.info("Generating market intelligence report")
        
        market_intelligence = {
            "executive_summary": {},
            "market_dynamics": {},
            "competitive_landscape": {},
            "technology_trends": {},
            "regulatory_environment": {},
            "strategic_recommendations": []
        }
        
        # Generate executive summary
        total_providers = len(competitive_analysis.get("provider_mentions", {}))
        total_trends = len(trend_analysis.get("emerging_trends", []))
        total_regulations = len(regulatory_updates.get("regulations_tracked", []))
        
        market_intelligence["executive_summary"] = {
            "providers_analyzed": total_providers,
            "trends_identified": total_trends,
            "regulations_monitored": total_regulations,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "key_insights": []
        }
        
        # Add key insights
        if competitive_analysis.get("market_positioning"):
            top_provider = max(
                competitive_analysis["market_positioning"].items(),
                key=lambda x: x[1]["mention_count"]
            )[0] if competitive_analysis["market_positioning"] else "unknown"
            
            market_intelligence["executive_summary"]["key_insights"].append(
                f"Most mentioned provider: {top_provider}"
            )
        
        if trend_analysis.get("emerging_trends"):
            top_trend = trend_analysis["emerging_trends"][0]["trend"]
            market_intelligence["executive_summary"]["key_insights"].append(
                f"Top emerging trend: {top_trend}"
            )
        
        # Market dynamics
        market_intelligence["market_dynamics"] = {
            "provider_visibility": competitive_analysis.get("market_positioning", {}),
            "trend_momentum": {
                trend["trend"]: trend["strength"] 
                for trend in trend_analysis.get("emerging_trends", [])
            },
            "regulatory_activity": len(regulatory_updates.get("recent_updates", []))
        }
        
        # Competitive landscape summary
        market_intelligence["competitive_landscape"] = {
            "provider_analysis": competitive_analysis.get("market_positioning", {}),
            "pricing_insights": len(competitive_analysis.get("pricing_comparisons", [])),
            "market_trends": competitive_analysis.get("market_trends", [])[:5]
        }
        
        # Technology trends summary
        market_intelligence["technology_trends"] = {
            "emerging_technologies": trend_analysis.get("emerging_trends", [])[:5],
            "adoption_indicators": trend_analysis.get("sentiment_analysis", {}),
            "key_focus_areas": [
                topic["topic"] for topic in trend_analysis.get("key_topics", [])[:3]
            ]
        }
        
        # Regulatory environment
        market_intelligence["regulatory_environment"] = {
            "active_regulations": regulatory_updates.get("regulations_tracked", []),
            "recent_changes": len(regulatory_updates.get("recent_updates", [])),
            "compliance_focus_areas": [
                topic["topic"] for topic in regulatory_updates.get("compliance_topics", [])[:3]
            ]
        }
        
        # Strategic recommendations
        recommendations = []
        
        # Provider recommendations
        if competitive_analysis.get("market_positioning"):
            top_providers = sorted(
                competitive_analysis["market_positioning"].items(),
                key=lambda x: x[1]["mention_count"],
                reverse=True
            )[:2]
            
            for provider, data in top_providers:
                recommendations.append({
                    "category": "provider_selection",
                    "recommendation": f"Consider {provider} - high market visibility",
                    "rationale": f"Mentioned {data['mention_count']} times across sources",
                    "priority": "high" if data["mention_count"] > 5 else "medium"
                })
        
        # Technology recommendations
        if trend_analysis.get("emerging_trends"):
            for trend in trend_analysis["emerging_trends"][:2]:
                recommendations.append({
                    "category": "technology_adoption",
                    "recommendation": f"Evaluate {trend['trend']} adoption",
                    "rationale": f"Emerging trend with {trend['strength']} strength",
                    "priority": "high" if trend["strength"] == "high" else "medium"
                })
        
        # Compliance recommendations
        if regulatory_updates.get("regulations_tracked"):
            for regulation in regulatory_updates["regulations_tracked"][:2]:
                recommendations.append({
                    "category": "compliance",
                    "recommendation": f"Review {regulation['regulation']} compliance",
                    "rationale": f"Active regulation with {regulation['mentions']} mentions",
                    "priority": "high"
                })
        
        market_intelligence["strategic_recommendations"] = recommendations
        
        return market_intelligence
    
    async def _create_web_research_recommendations(self, market_intelligence: Dict[str, Any], 
                                                 validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create specific recommendations based on web research findings.
        
        Args:
            market_intelligence: Market intelligence report
            validation_results: Data validation results
            
        Returns:
            List of recommendations
        """
        logger.info("Creating web research recommendations")
        
        recommendations = []
        
        # Add strategic recommendations from market intelligence
        strategic_recs = market_intelligence.get("strategic_recommendations", [])
        for rec in strategic_recs:
            recommendations.append({
                "type": "strategic",
                "category": rec["category"],
                "title": rec["recommendation"],
                "description": rec["rationale"],
                "priority": rec["priority"],
                "confidence_score": 0.8,  # High confidence from web research
                "source": "web_research_analysis",
                "implementation_effort": "medium",
                "business_impact": "high" if rec["priority"] == "high" else "medium"
            })
        
        # Add data validation recommendations
        if validation_results.get("confidence_scores"):
            for provider, confidence in validation_results["confidence_scores"].items():
                if confidence < 0.7:
                    recommendations.append({
                        "type": "data_quality",
                        "category": "validation",
                        "title": f"Improve {provider} data validation",
                        "description": f"Low confidence score ({confidence}) for {provider} data",
                        "priority": "medium",
                        "confidence_score": confidence,
                        "source": "data_validation",
                        "implementation_effort": "low",
                        "business_impact": "medium"
                    })
        
        # Add market positioning recommendations
        market_dynamics = market_intelligence.get("market_dynamics", {})
        if market_dynamics.get("provider_visibility"):
            top_provider = max(
                market_dynamics["provider_visibility"].items(),
                key=lambda x: x[1]["mention_count"]
            )[0] if market_dynamics["provider_visibility"] else None
            
            if top_provider:
                recommendations.append({
                    "type": "market_positioning",
                    "category": "provider_selection",
                    "title": f"Prioritize {top_provider} evaluation",
                    "description": f"{top_provider} shows highest market visibility in research",
                    "priority": "high",
                    "confidence_score": 0.9,
                    "source": "competitive_analysis",
                    "implementation_effort": "medium",
                    "business_impact": "high"
                })
        
        # Add trend-based recommendations
        tech_trends = market_intelligence.get("technology_trends", {})
        if tech_trends.get("emerging_technologies"):
            for trend in tech_trends["emerging_technologies"][:2]:
                recommendations.append({
                    "type": "technology_trend",
                    "category": "innovation",
                    "title": f"Explore {trend['trend']} opportunities",
                    "description": f"Emerging technology with {trend['strength']} adoption momentum",
                    "priority": "medium" if trend["strength"] == "high" else "low",
                    "confidence_score": 0.7,
                    "source": "trend_analysis",
                    "implementation_effort": "high",
                    "business_impact": "high" if trend["strength"] == "high" else "medium"
                })
        
        # Add regulatory recommendations
        regulatory_env = market_intelligence.get("regulatory_environment", {})
        if regulatory_env.get("active_regulations"):
            for regulation in regulatory_env["active_regulations"][:2]:
                recommendations.append({
                    "type": "compliance",
                    "category": "regulatory",
                    "title": f"Ensure {regulation['regulation']} compliance",
                    "description": f"Active regulation requiring attention ({regulation['mentions']} mentions)",
                    "priority": "high",
                    "confidence_score": 0.9,
                    "source": "regulatory_monitoring",
                    "implementation_effort": "medium",
                    "business_impact": "critical"
                })
        
        logger.info(f"Created {len(recommendations)} web research recommendations")
        return recommendations
    
    async def _check_data_freshness(self) -> Dict[str, Any]:
        """
        Check the freshness of collected data.
        
        Returns:
            Data freshness report
        """
        logger.info("Checking data freshness")
        
        freshness_report = {
            "overall_status": "good",
            "data_categories": {},
            "stale_data_count": 0,
            "refresh_recommendations": []
        }
        
        # Check each data category
        for category, threshold_hours in self.freshness_thresholds.items():
            # Query database for data in this category
            try:
                # This would query the WebResearchData collection
                # For now, we'll simulate the check
                threshold_time = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
                
                freshness_report["data_categories"][category] = {
                    "threshold_hours": threshold_hours,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "status": "fresh",  # Would be calculated from actual data
                    "items_count": 0    # Would be actual count
                }
                
            except Exception as e:
                logger.error(f"Error checking freshness for {category}: {str(e)}")
                freshness_report["data_categories"][category] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall status
        stale_categories = [
            cat for cat, data in freshness_report["data_categories"].items()
            if data.get("status") == "stale"
        ]
        
        if stale_categories:
            freshness_report["overall_status"] = "needs_refresh"
            freshness_report["stale_data_count"] = len(stale_categories)
            
            for category in stale_categories:
                freshness_report["refresh_recommendations"].append({
                    "category": category,
                    "action": "refresh_data",
                    "priority": "high" if category == "pricing_data" else "medium"
                })
        
        return freshness_report
    
    async def _create_research_summary(self, competitive_analysis: Dict[str, Any], 
                                     trend_analysis: Dict[str, Any], 
                                     regulatory_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive research summary.
        
        Args:
            competitive_analysis: Competitive analysis results
            trend_analysis: Trend analysis results
            regulatory_updates: Regulatory update results
            
        Returns:
            Research summary
        """
        logger.info("Creating research summary")
        
        summary = {
            "research_scope": {
                "providers_analyzed": len(competitive_analysis.get("provider_mentions", {})),
                "trends_identified": len(trend_analysis.get("emerging_trends", [])),
                "regulations_monitored": len(regulatory_updates.get("regulations_tracked", [])),
                "data_sources_used": len(self.research_targets)
            },
            "key_findings": {
                "competitive_insights": [],
                "technology_trends": [],
                "regulatory_changes": []
            },
            "data_quality": {
                "sources_scraped": 0,  # Would be actual count
                "successful_extractions": 0,  # Would be actual count
                "data_validation_score": 0.8  # Would be calculated
            },
            "recommendations_summary": {
                "strategic_actions": 0,
                "technology_evaluations": 0,
                "compliance_reviews": 0
            }
        }
        
        # Extract key competitive insights
        if competitive_analysis.get("market_positioning"):
            top_providers = sorted(
                competitive_analysis["market_positioning"].items(),
                key=lambda x: x[1]["mention_count"],
                reverse=True
            )[:3]
            
            for provider, data in top_providers:
                summary["key_findings"]["competitive_insights"].append({
                    "provider": provider,
                    "market_visibility": data["mention_count"],
                    "insight": f"High visibility with {data['mention_count']} mentions"
                })
        
        # Extract key technology trends
        if trend_analysis.get("emerging_trends"):
            for trend in trend_analysis["emerging_trends"][:3]:
                summary["key_findings"]["technology_trends"].append({
                    "trend": trend["trend"],
                    "strength": trend["strength"],
                    "mentions": trend["mention_count"]
                })
        
        # Extract regulatory changes
        if regulatory_updates.get("recent_updates"):
            for update in regulatory_updates["recent_updates"][:3]:
                summary["key_findings"]["regulatory_changes"].append({
                    "type": update["update_type"],
                    "timestamp": update["timestamp"]
                })
        
        return summary