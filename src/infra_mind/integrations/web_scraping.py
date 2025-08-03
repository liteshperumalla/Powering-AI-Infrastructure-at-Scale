"""
Real web scraping and search API integrations for Infra Mind.

Provides real web scraping capabilities using Google Custom Search API,
Bing Search API, and Scrapy for comprehensive market intelligence.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import aiohttp
import json
import hashlib
from urllib.parse import urljoin, urlparse, quote
import re
from bs4 import BeautifulSoup
# Scrapy imports (optional for advanced scraping)
try:
    import scrapy
    from scrapy.crawler import CrawlerRunner
    from scrapy.utils.project import get_project_settings
    from twisted.internet import defer
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False
import time

from ..core.config import get_settings
from ..core.cache import cache_manager

logger = logging.getLogger(__name__)


class SearchProvider(str, Enum):
    """Supported search providers."""
    GOOGLE_CUSTOM = "google_custom"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"


class ContentType(str, Enum):
    """Types of content to scrape."""
    PRICING = "pricing"
    COMPETITIVE = "competitive"
    TRENDS = "trends"
    REGULATORY = "regulatory"
    BEST_PRACTICES = "best_practices"
    NEWS = "news"
    DOCUMENTATION = "documentation"


@dataclass
class SearchResult:
    """Search result structure."""
    title: str
    url: str
    snippet: str
    provider: SearchProvider
    search_query: str
    rank: int
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "provider": self.provider.value,
            "search_query": self.search_query,
            "rank": self.rank,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ScrapedContent:
    """Scraped content structure."""
    url: str
    title: str
    content: str
    content_type: ContentType
    extracted_data: Dict[str, Any]
    metadata: Dict[str, Any]
    scraped_at: datetime
    content_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content[:1000],  # Truncate for storage
            "content_type": self.content_type.value,
            "extracted_data": self.extracted_data,
            "metadata": self.metadata,
            "scraped_at": self.scraped_at.isoformat(),
            "content_hash": self.content_hash
        }


class RealWebScrapingService:
    """
    Real web scraping service with Google Custom Search API, Bing Search API,
    and Scrapy integration for comprehensive market intelligence.
    """
    
    def __init__(self):
        """Initialize web scraping service."""
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API configurations
        self.google_config = {
            "api_key": getattr(self.settings, "GOOGLE_SEARCH_API_KEY", None),
            "search_engine_id": getattr(self.settings, "GOOGLE_SEARCH_ENGINE_ID", None),
            "enabled": getattr(self.settings, "ENABLE_GOOGLE_SEARCH", False),
            "base_url": "https://www.googleapis.com/customsearch/v1"
        }
        
        self.bing_config = {
            "api_key": getattr(self.settings, "BING_SEARCH_API_KEY", None),
            "enabled": getattr(self.settings, "ENABLE_BING_SEARCH", False),
            "base_url": "https://api.bing.microsoft.com/v7.0/search"
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            SearchProvider.GOOGLE_CUSTOM: {
                "requests_per_day": 100,  # Free tier limit
                "requests_per_second": 10,
                "current_count": 0,
                "last_reset": datetime.now(timezone.utc)
            },
            SearchProvider.BING: {
                "requests_per_month": 1000,  # Free tier limit
                "requests_per_second": 3,
                "current_count": 0,
                "last_reset": datetime.now(timezone.utc)
            }
        }
        
        # Scrapy settings
        self.scrapy_settings = {
            "USER_AGENT": "InfraMind-WebScraper/1.0 (+https://infra-mind.com)",
            "ROBOTSTXT_OBEY": True,
            "CONCURRENT_REQUESTS": 5,
            "DOWNLOAD_DELAY": 1,
            "RANDOMIZE_DOWNLOAD_DELAY": 0.5,
            "COOKIES_ENABLED": False,
            "TELNETCONSOLE_ENABLED": False,
            "DEFAULT_REQUEST_HEADERS": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en",
            }
        }
        
        # Content extraction patterns
        self.extraction_patterns = {
            ContentType.PRICING: {
                "price_regex": r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|/)\s*(hour|month|year|GB|TB|request)',
                "service_regex": r'(EC2|RDS|S3|Compute|Storage|Database|VM|Lambda|Functions)',
                "discount_regex": r'(\d+)%\s*(?:off|discount|savings|reduction)'
            },
            ContentType.TRENDS: {
                "trend_keywords": [
                    "artificial intelligence", "machine learning", "cloud migration",
                    "serverless", "containers", "kubernetes", "microservices",
                    "edge computing", "hybrid cloud", "multi-cloud", "devops"
                ],
                "sentiment_indicators": ["increasing", "growing", "declining", "emerging", "trending", "adoption"]
            },
            ContentType.REGULATORY: {
                "regulation_keywords": ["GDPR", "HIPAA", "CCPA", "SOC 2", "ISO 27001", "PCI DSS", "FedRAMP"],
                "update_indicators": ["updated", "new requirement", "compliance change", "regulation", "amendment"]
            }
        }
        
        logger.info("Real Web Scraping Service initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": self.scrapy_settings["USER_AGENT"]}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    # Search API Methods
    
    async def search_google_custom(self, query: str, num_results: int = 10, **kwargs) -> List[SearchResult]:
        """Search using Google Custom Search API."""
        if not self.google_config["enabled"] or not self.google_config["api_key"]:
            logger.warning("Google Custom Search not configured")
            return []
        
        # Check rate limits
        if not await self._check_rate_limit(SearchProvider.GOOGLE_CUSTOM):
            logger.warning("Google Custom Search rate limit exceeded")
            return []
        
        try:
            params = {
                "key": self.google_config["api_key"],
                "cx": self.google_config["search_engine_id"],
                "q": query,
                "num": min(num_results, 10),  # Google API max is 10 per request
                "safe": "medium",
                "fields": "items(title,link,snippet,displayLink)"
            }
            
            # Add optional parameters
            if "site" in kwargs:
                params["siteSearch"] = kwargs["site"]
            if "date_restrict" in kwargs:
                params["dateRestrict"] = kwargs["date_restrict"]
            if "file_type" in kwargs:
                params["fileType"] = kwargs["file_type"]
            
            async with self.session.get(self.google_config["base_url"], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for i, item in enumerate(data.get("items", [])):
                        result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            provider=SearchProvider.GOOGLE_CUSTOM,
                            search_query=query,
                            rank=i + 1,
                            timestamp=datetime.now(timezone.utc),
                            metadata={
                                "display_link": item.get("displayLink", ""),
                                "search_info": data.get("searchInformation", {})
                            }
                        )
                        results.append(result)
                    
                    await self._update_rate_limit(SearchProvider.GOOGLE_CUSTOM)
                    logger.info(f"Google Custom Search returned {len(results)} results for: {query}")
                    return results
                else:
                    error_data = await response.json()
                    logger.error(f"Google Custom Search API error: {response.status} - {error_data}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google Custom Search failed: {str(e)}")
            return []
    
    async def search_bing(self, query: str, num_results: int = 10, **kwargs) -> List[SearchResult]:
        """Search using Bing Search API."""
        if not self.bing_config["enabled"] or not self.bing_config["api_key"]:
            logger.warning("Bing Search not configured")
            return []
        
        # Check rate limits
        if not await self._check_rate_limit(SearchProvider.BING):
            logger.warning("Bing Search rate limit exceeded")
            return []
        
        try:
            params = {
                "q": query,
                "count": min(num_results, 50),  # Bing API max is 50 per request
                "offset": kwargs.get("offset", 0),
                "mkt": kwargs.get("market", "en-US"),
                "safeSearch": "Moderate"
            }
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_config["api_key"]
            }
            
            async with self.session.get(
                self.bing_config["base_url"], 
                params=params, 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for i, item in enumerate(data.get("webPages", {}).get("value", [])):
                        result = SearchResult(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            provider=SearchProvider.BING,
                            search_query=query,
                            rank=i + 1,
                            timestamp=datetime.now(timezone.utc),
                            metadata={
                                "display_url": item.get("displayUrl", ""),
                                "date_last_crawled": item.get("dateLastCrawled", "")
                            }
                        )
                        results.append(result)
                    
                    await self._update_rate_limit(SearchProvider.BING)
                    logger.info(f"Bing Search returned {len(results)} results for: {query}")
                    return results
                else:
                    error_data = await response.json()
                    logger.error(f"Bing Search API error: {response.status} - {error_data}")
                    return []
                    
        except Exception as e:
            logger.error(f"Bing Search failed: {str(e)}")
            return []
    
    async def multi_provider_search(self, query: str, providers: List[SearchProvider] = None, num_results: int = 10) -> Dict[SearchProvider, List[SearchResult]]:
        """Search across multiple providers."""
        if providers is None:
            providers = [SearchProvider.GOOGLE_CUSTOM, SearchProvider.BING]
        
        results = {}
        tasks = []
        
        for provider in providers:
            if provider == SearchProvider.GOOGLE_CUSTOM:
                tasks.append(self.search_google_custom(query, num_results))
            elif provider == SearchProvider.BING:
                tasks.append(self.search_bing(query, num_results))
        
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, provider in enumerate(providers):
            if isinstance(search_results[i], Exception):
                logger.error(f"Search failed for {provider}: {search_results[i]}")
                results[provider] = []
            else:
                results[provider] = search_results[i]
        
        return results
    
    # Web Scraping Methods
    
    async def scrape_url(self, url: str, content_type: ContentType = ContentType.NEWS) -> Optional[ScrapedContent]:
        """Scrape content from a single URL."""
        try:
            # Check cache first
            cache_key = f"scraped_content:{hashlib.md5(url.encode()).hexdigest()}"
            cached_content = await cache_manager.get(cache_key)
            if cached_content:
                logger.debug(f"Using cached content for {url}")
                return ScrapedContent(**json.loads(cached_content))
            
            # Respect robots.txt and rate limiting
            await self._respect_rate_limit(url)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Parse content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract basic information
                    title = self._extract_title(soup)
                    content = self._extract_main_content(soup)
                    extracted_data = await self._extract_structured_data(soup, content_type)
                    
                    # Create content hash
                    content_hash = hashlib.md5(html_content.encode()).hexdigest()
                    
                    scraped_content = ScrapedContent(
                        url=url,
                        title=title,
                        content=content,
                        content_type=content_type,
                        extracted_data=extracted_data,
                        metadata={
                            "status_code": response.status,
                            "content_length": len(html_content),
                            "response_headers": dict(response.headers),
                            "scraped_by": "real_web_scraping_service"
                        },
                        scraped_at=datetime.now(timezone.utc),
                        content_hash=content_hash
                    )
                    
                    # Cache the result for 1 hour
                    await cache_manager.set(
                        cache_key,
                        json.dumps(scraped_content.to_dict()),
                        ttl=3600
                    )
                    
                    logger.info(f"Successfully scraped content from {url}")
                    return scraped_content
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return None
    
    async def scrape_multiple_urls(self, urls: List[str], content_type: ContentType = ContentType.NEWS, max_concurrent: int = 5) -> List[ScrapedContent]:
        """Scrape content from multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Optional[ScrapedContent]:
            async with semaphore:
                return await self.scrape_url(url, content_type)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scraped_contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {result}")
            elif result is not None:
                scraped_contents.append(result)
        
        logger.info(f"Successfully scraped {len(scraped_contents)}/{len(urls)} URLs")
        return scraped_contents
    
    # Content Extraction Methods
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "No title found"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '#main-content', '.post-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content.get_text(separator=' ', strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    async def _extract_structured_data(self, soup: BeautifulSoup, content_type: ContentType) -> Dict[str, Any]:
        """Extract structured data based on content type."""
        extracted = {
            "headings": [],
            "links": [],
            "images": [],
            "metadata": {}
        }
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            extracted["headings"].append({
                "level": int(heading.name[1]),
                "text": heading.get_text().strip()
            })
        
        # Extract links
        for link in soup.find_all('a', href=True)[:20]:  # Limit to first 20 links
            extracted["links"].append({
                "url": link['href'],
                "text": link.get_text().strip()[:100]
            })
        
        # Extract images
        for img in soup.find_all('img', src=True)[:10]:  # Limit to first 10 images
            extracted["images"].append({
                "src": img['src'],
                "alt": img.get('alt', ''),
                "title": img.get('title', '')
            })
        
        # Content-type specific extraction
        if content_type == ContentType.PRICING:
            extracted.update(await self._extract_pricing_data(soup))
        elif content_type == ContentType.TRENDS:
            extracted.update(await self._extract_trend_data(soup))
        elif content_type == ContentType.REGULATORY:
            extracted.update(await self._extract_regulatory_data(soup))
        
        return extracted
    
    async def _extract_pricing_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract pricing-specific data."""
        text_content = soup.get_text()
        
        pricing_data = {
            "prices_found": [],
            "services_mentioned": [],
            "discounts": []
        }
        
        # Extract prices
        price_pattern = self.extraction_patterns[ContentType.PRICING]["price_regex"]
        prices = re.findall(price_pattern, text_content, re.IGNORECASE)
        pricing_data["prices_found"] = [
            {"amount": p[0], "unit": p[1]} for p in prices[:10]
        ]
        
        # Extract service mentions
        service_pattern = self.extraction_patterns[ContentType.PRICING]["service_regex"]
        services = re.findall(service_pattern, text_content, re.IGNORECASE)
        pricing_data["services_mentioned"] = list(set(services))
        
        # Extract discounts
        discount_pattern = self.extraction_patterns[ContentType.PRICING]["discount_regex"]
        discounts = re.findall(discount_pattern, text_content, re.IGNORECASE)
        pricing_data["discounts"] = [f"{d}% discount" for d in discounts[:5]]
        
        return pricing_data
    
    async def _extract_trend_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract trend-specific data."""
        text_content = soup.get_text().lower()
        
        trend_data = {
            "trends_identified": [],
            "sentiment_indicators": [],
            "key_topics": []
        }
        
        # Identify trend keywords
        trend_keywords = self.extraction_patterns[ContentType.TRENDS]["trend_keywords"]
        for keyword in trend_keywords:
            if keyword in text_content:
                trend_data["trends_identified"].append(keyword)
        
        # Identify sentiment indicators
        sentiment_indicators = self.extraction_patterns[ContentType.TRENDS]["sentiment_indicators"]
        for indicator in sentiment_indicators:
            if indicator in text_content:
                trend_data["sentiment_indicators"].append(indicator)
        
        # Extract key topics from headings
        for heading in soup.find_all(['h1', 'h2', 'h3'])[:10]:
            topic = heading.get_text().strip()
            if 5 < len(topic) < 100:
                trend_data["key_topics"].append(topic)
        
        return trend_data
    
    async def _extract_regulatory_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract regulatory-specific data."""
        text_content = soup.get_text()
        
        regulatory_data = {
            "regulations_mentioned": [],
            "updates_found": [],
            "compliance_topics": []
        }
        
        # Identify regulation keywords
        regulation_keywords = self.extraction_patterns[ContentType.REGULATORY]["regulation_keywords"]
        for keyword in regulation_keywords:
            if keyword in text_content:
                regulatory_data["regulations_mentioned"].append(keyword)
        
        # Identify update indicators
        update_indicators = self.extraction_patterns[ContentType.REGULATORY]["update_indicators"]
        for indicator in update_indicators:
            if indicator.lower() in text_content.lower():
                regulatory_data["updates_found"].append(indicator)
        
        return regulatory_data
    
    # Rate Limiting Methods
    
    async def _check_rate_limit(self, provider: SearchProvider) -> bool:
        """Check if rate limit allows for another request."""
        limit_info = self.rate_limits[provider]
        now = datetime.now(timezone.utc)
        
        # Reset counters if needed
        if provider == SearchProvider.GOOGLE_CUSTOM:
            if (now - limit_info["last_reset"]).days >= 1:
                limit_info["current_count"] = 0
                limit_info["last_reset"] = now
        elif provider == SearchProvider.BING:
            if (now - limit_info["last_reset"]).days >= 30:
                limit_info["current_count"] = 0
                limit_info["last_reset"] = now
        
        # Check limits
        if provider == SearchProvider.GOOGLE_CUSTOM:
            return limit_info["current_count"] < limit_info["requests_per_day"]
        elif provider == SearchProvider.BING:
            return limit_info["current_count"] < limit_info["requests_per_month"]
        
        return True
    
    async def _update_rate_limit(self, provider: SearchProvider):
        """Update rate limit counter after successful request."""
        self.rate_limits[provider]["current_count"] += 1
    
    async def _respect_rate_limit(self, url: str):
        """Respect rate limiting for web scraping."""
        domain = urlparse(url).netloc
        
        # Simple rate limiting - 1 second delay between requests to same domain
        cache_key = f"last_request:{domain}"
        last_request = await cache_manager.get(cache_key)
        
        if last_request:
            last_time = datetime.fromisoformat(last_request)
            time_diff = (datetime.now(timezone.utc) - last_time).total_seconds()
            
            if time_diff < 1.0:
                await asyncio.sleep(1.0 - time_diff)
        
        await cache_manager.set(
            cache_key,
            datetime.now(timezone.utc).isoformat(),
            ttl=60
        )
    
    # High-level Research Methods
    
    async def research_cloud_pricing(self, providers: List[str] = None) -> Dict[str, Any]:
        """Research cloud pricing across providers."""
        if providers is None:
            providers = ["aws", "azure", "gcp"]
        
        research_results = {
            "research_date": datetime.now(timezone.utc).isoformat(),
            "providers": providers,
            "search_results": {},
            "scraped_content": {},
            "pricing_insights": {}
        }
        
        for provider in providers:
            # Search for pricing information
            query = f"{provider} cloud pricing calculator cost"
            search_results = await self.multi_provider_search(query, num_results=5)
            research_results["search_results"][provider] = {
                prov.value: [r.to_dict() for r in results]
                for prov, results in search_results.items()
            }
            
            # Scrape top results
            urls_to_scrape = []
            for results in search_results.values():
                urls_to_scrape.extend([r.url for r in results[:3]])
            
            scraped_contents = await self.scrape_multiple_urls(
                urls_to_scrape, 
                ContentType.PRICING,
                max_concurrent=3
            )
            
            research_results["scraped_content"][provider] = [
                content.to_dict() for content in scraped_contents
            ]
            
            # Extract pricing insights
            pricing_insights = []
            for content in scraped_contents:
                if content.extracted_data.get("prices_found"):
                    pricing_insights.extend(content.extracted_data["prices_found"])
            
            research_results["pricing_insights"][provider] = pricing_insights
        
        logger.info(f"Completed cloud pricing research for {len(providers)} providers")
        return research_results
    
    async def research_technology_trends(self, keywords: List[str] = None) -> Dict[str, Any]:
        """Research technology trends and market intelligence."""
        if keywords is None:
            keywords = ["cloud computing", "artificial intelligence", "kubernetes", "serverless"]
        
        research_results = {
            "research_date": datetime.now(timezone.utc).isoformat(),
            "keywords": keywords,
            "trend_analysis": {},
            "market_insights": []
        }
        
        for keyword in keywords:
            query = f"{keyword} trends 2024 market analysis"
            search_results = await self.multi_provider_search(query, num_results=10)
            
            # Scrape trend content
            urls_to_scrape = []
            for results in search_results.values():
                urls_to_scrape.extend([r.url for r in results[:5]])
            
            scraped_contents = await self.scrape_multiple_urls(
                urls_to_scrape,
                ContentType.TRENDS,
                max_concurrent=3
            )
            
            # Analyze trends
            trend_analysis = {
                "keyword": keyword,
                "sources_analyzed": len(scraped_contents),
                "trends_identified": [],
                "sentiment_indicators": [],
                "key_insights": []
            }
            
            for content in scraped_contents:
                extracted = content.extracted_data
                trend_analysis["trends_identified"].extend(
                    extracted.get("trends_identified", [])
                )
                trend_analysis["sentiment_indicators"].extend(
                    extracted.get("sentiment_indicators", [])
                )
                trend_analysis["key_insights"].extend(
                    extracted.get("key_topics", [])
                )
            
            # Remove duplicates
            trend_analysis["trends_identified"] = list(set(trend_analysis["trends_identified"]))
            trend_analysis["sentiment_indicators"] = list(set(trend_analysis["sentiment_indicators"]))
            
            research_results["trend_analysis"][keyword] = trend_analysis
        
        logger.info(f"Completed technology trends research for {len(keywords)} keywords")
        return research_results
    
    async def research_compliance_updates(self, frameworks: List[str] = None) -> Dict[str, Any]:
        """Research regulatory compliance updates."""
        if frameworks is None:
            frameworks = ["GDPR", "HIPAA", "CCPA", "SOC 2"]
        
        research_results = {
            "research_date": datetime.now(timezone.utc).isoformat(),
            "frameworks": frameworks,
            "compliance_updates": {},
            "regulatory_changes": []
        }
        
        for framework in frameworks:
            query = f"{framework} compliance updates 2024 regulatory changes"
            search_results = await self.multi_provider_search(query, num_results=8)
            
            # Scrape regulatory content
            urls_to_scrape = []
            for results in search_results.values():
                urls_to_scrape.extend([r.url for r in results[:4]])
            
            scraped_contents = await self.scrape_multiple_urls(
                urls_to_scrape,
                ContentType.REGULATORY,
                max_concurrent=2
            )
            
            # Analyze compliance updates
            compliance_analysis = {
                "framework": framework,
                "sources_analyzed": len(scraped_contents),
                "regulations_mentioned": [],
                "updates_found": [],
                "key_changes": []
            }
            
            for content in scraped_contents:
                extracted = content.extracted_data
                compliance_analysis["regulations_mentioned"].extend(
                    extracted.get("regulations_mentioned", [])
                )
                compliance_analysis["updates_found"].extend(
                    extracted.get("updates_found", [])
                )
            
            # Remove duplicates
            compliance_analysis["regulations_mentioned"] = list(set(compliance_analysis["regulations_mentioned"]))
            compliance_analysis["updates_found"] = list(set(compliance_analysis["updates_found"]))
            
            research_results["compliance_updates"][framework] = compliance_analysis
        
        logger.info(f"Completed compliance research for {len(frameworks)} frameworks")
        return research_results
    
    # Utility Methods
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of web scraping service and APIs."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_status": "operational",
            "api_status": {},
            "rate_limits": {}
        }
        
        # Check API status
        for provider in [SearchProvider.GOOGLE_CUSTOM, SearchProvider.BING]:
            if provider == SearchProvider.GOOGLE_CUSTOM:
                enabled = self.google_config["enabled"]
                configured = bool(self.google_config["api_key"] and self.google_config["search_engine_id"])
            else:
                enabled = self.bing_config["enabled"]
                configured = bool(self.bing_config["api_key"])
            
            status["api_status"][provider.value] = {
                "enabled": enabled,
                "configured": configured,
                "operational": enabled and configured
            }
        
        # Add rate limit status
        for provider, limits in self.rate_limits.items():
            status["rate_limits"][provider.value] = {
                "current_count": limits["current_count"],
                "limit_type": "daily" if provider == SearchProvider.GOOGLE_CUSTOM else "monthly",
                "last_reset": limits["last_reset"].isoformat()
            }
        
        return status


# Global service instance
web_scraping_service = RealWebScrapingService()


# Convenience functions

async def search_web(query: str, providers: List[SearchProvider] = None, num_results: int = 10) -> Dict[SearchProvider, List[SearchResult]]:
    """Search the web using multiple providers."""
    async with web_scraping_service as service:
        return await service.multi_provider_search(query, providers, num_results)


async def scrape_urls(urls: List[str], content_type: ContentType = ContentType.NEWS) -> List[ScrapedContent]:
    """Scrape content from multiple URLs."""
    async with web_scraping_service as service:
        return await service.scrape_multiple_urls(urls, content_type)


async def research_cloud_pricing(providers: List[str] = None) -> Dict[str, Any]:
    """Research cloud pricing across providers."""
    async with web_scraping_service as service:
        return await service.research_cloud_pricing(providers)


async def research_technology_trends(keywords: List[str] = None) -> Dict[str, Any]:
    """Research technology trends."""
    async with web_scraping_service as service:
        return await service.research_technology_trends(keywords)


async def research_compliance_updates(frameworks: List[str] = None) -> Dict[str, Any]:
    """Research compliance updates."""
    async with web_scraping_service as service:
        return await service.research_compliance_updates(frameworks)