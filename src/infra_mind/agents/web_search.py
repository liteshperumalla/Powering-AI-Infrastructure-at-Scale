"""
Web Search Module for Real-time Information Retrieval.

Provides integration with multiple search APIs including DuckDuckGo, Google Custom Search,
and Tavily for comprehensive web research capabilities.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import json

# Optional imports - will use graceful fallbacks
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebSearchClient:
    """
    Unified web search client supporting multiple search APIs.
    
    Supports:
    - DuckDuckGo Search (free, no API key required)
    - Google Custom Search via SerpAPI (requires API key)
    - Tavily Search (requires API key)
    - Direct web scraping as fallback
    """
    
    def __init__(self):
        """Initialize the web search client with available APIs."""
        self.ddgs_available = DDGS_AVAILABLE
        self.serpapi_available = SERPAPI_AVAILABLE and bool(os.getenv("SERPAPI_API_KEY"))
        self.tavily_available = TAVILY_AVAILABLE and bool(os.getenv("TAVILY_API_KEY"))
        
        # Initialize clients
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.tavily_client = None
        
        if self.tavily_available:
            try:
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily client: {e}")
                self.tavily_available = False
        
        # HTTP client for direct scraping
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        logger.info(f"WebSearchClient initialized - DDG: {self.ddgs_available}, SerpAPI: {self.serpapi_available}, Tavily: {self.tavily_available}")
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "general",
        prefer_recent: bool = True
    ) -> Dict[str, Any]:
        """
        Perform web search using the best available method.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_type: Type of search ('general', 'news', 'academic', 'technical')
            prefer_recent: Whether to prefer recent results
            
        Returns:
            Dictionary containing search results and metadata
        """
        logger.info(f"Performing web search for: '{query}'")
        
        search_results = {
            "query": query,
            "results": [],
            "metadata": {
                "search_timestamp": datetime.now(timezone.utc).isoformat(),
                "search_method": "unknown",
                "total_results": 0,
                "search_type": search_type
            }
        }
        
        # Try search methods in order of preference
        search_methods = self._get_search_methods_priority(search_type)
        
        for method in search_methods:
            try:
                if method == "tavily" and self.tavily_available:
                    results = await self._search_tavily(query, max_results, search_type)
                elif method == "ddgs" and self.ddgs_available:
                    results = await self._search_duckduckgo(query, max_results, search_type)
                elif method == "serpapi" and self.serpapi_available:
                    results = await self._search_serpapi(query, max_results, search_type)
                else:
                    continue
                
                if results and len(results) > 0:
                    search_results["results"] = results
                    search_results["metadata"]["search_method"] = method
                    search_results["metadata"]["total_results"] = len(results)
                    logger.info(f"Successfully retrieved {len(results)} results using {method}")
                    break
                    
            except Exception as e:
                logger.warning(f"Search method {method} failed: {e}")
                continue
        
        # If no results found, try basic web scraping
        if not search_results["results"]:
            logger.info("Attempting fallback web scraping")
            try:
                results = await self._fallback_web_search(query, max_results)
                search_results["results"] = results
                search_results["metadata"]["search_method"] = "web_scraping"
                search_results["metadata"]["total_results"] = len(results)
            except Exception as e:
                logger.error(f"Fallback web search failed: {e}")
        
        return search_results
    
    def _get_search_methods_priority(self, search_type: str) -> List[str]:
        """Get search methods in order of preference based on search type."""
        if search_type == "technical":
            # For technical searches, prefer specialized APIs
            return ["tavily", "serpapi", "ddgs"]
        elif search_type == "news":
            # For news, prefer real-time capable APIs
            return ["tavily", "ddgs", "serpapi"]
        else:
            # General search - balance quality and availability
            return ["ddgs", "tavily", "serpapi"]
    
    async def _search_duckduckgo(self, query: str, max_results: int, search_type: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API."""
        results = []
        
        try:
            # Run DuckDuckGo search in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ddgs_results = await loop.run_in_executor(
                None, 
                self._ddgs_search_sync, 
                query, 
                max_results, 
                search_type
            )
            
            for result in ddgs_results:
                processed_result = {
                    "title": result.get("title"),
                    "url": result.get("href"),
                    "snippet": result.get("body"),
                    "published_date": result.get("published"),
                    "source": "duckduckgo",
                    "relevance_score": 0.8  # Default score for DDG
                }
                results.append(processed_result)
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            raise
        
        return results
    
    def _ddgs_search_sync(self, query: str, max_results: int, search_type: str) -> List[Dict[str, Any]]:
        """Synchronous DuckDuckGo search to run in thread pool."""
        try:
            with DDGS() as ddgs:
                if search_type == "news":
                    # Use news search for recent information
                    results = list(ddgs.news(query, max_results=max_results))
                else:
                    # Use general text search
                    results = list(ddgs.text(query, max_results=max_results))
            
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo sync search failed: {e}")
            return []
    
    async def _search_serpapi(self, query: str, max_results: int, search_type: str) -> List[Dict[str, Any]]:
        """Search using Google Custom Search via SerpAPI."""
        results = []
        
        try:
            search_params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": min(max_results, 10)  # Google limits to 10 per request
            }
            
            if search_type == "news":
                search_params["tbm"] = "nws"  # News search
            elif search_type == "academic":
                search_params["as_sitesearch"] = "scholar.google.com OR arxiv.org OR pubmed.ncbi.nlm.nih.gov"
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                lambda: GoogleSearch(search_params).get_dict()
            )
            
            organic_results = search_result.get("organic_results", [])
            
            for result in organic_results:
                processed_result = {
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "snippet": result.get("snippet"),
                    "published_date": result.get("date"),
                    "source": "google",
                    "relevance_score": 0.9  # Higher score for Google results
                }
                results.append(processed_result)
        
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            raise
        
        return results
    
    async def _search_tavily(self, query: str, max_results: int, search_type: str) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        results = []
        
        try:
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced" if search_type == "technical" else "basic",
                "include_answer": True,
                "include_raw_content": False
            }
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            tavily_results = await loop.run_in_executor(
                None,
                lambda: self.tavily_client.search(**search_params)
            )
            
            for result in tavily_results.get("results", []):
                processed_result = {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "snippet": result.get("content"),
                    "published_date": result.get("published_date"),
                    "source": "tavily",
                    "relevance_score": result.get("score", 0.7)
                }
                results.append(processed_result)
        
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise
        
        return results
    
    async def _fallback_web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback web search using direct HTTP requests."""
        results = []
        
        # Create a simple search using common search engines
        search_urls = [
            f"https://html.duckduckgo.com/html/?q={query}",
        ]
        
        for search_url in search_urls:
            try:
                response = await self.http_client.get(search_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse DuckDuckGo HTML results
                    search_results = soup.find_all('div', class_='result')
                    
                    for result in search_results[:max_results]:
                        title_elem = result.find('a', class_='result__a')
                        snippet_elem = result.find('a', class_='result__snippet')
                        
                        if title_elem:
                            processed_result = {
                                "title": title_elem.text.strip(),
                                "url": title_elem.get('href'),
                                "snippet": snippet_elem.text.strip() if snippet_elem else "",
                                "published_date": "",
                                "source": "web_scraping",
                                "relevance_score": 0.6
                            }
                            results.append(processed_result)
                    
                    break  # Stop after first successful search
                    
            except Exception as e:
                logger.warning(f"Fallback search failed for {search_url}: {e}")
                continue
        
        return results
    
    async def search_specific_topics(self, topics: List[str], context: str = "") -> Dict[str, Any]:
        """
        Search for multiple specific topics with context.
        
        Args:
            topics: List of topics to search for
            context: Additional context to improve search relevance
            
        Returns:
            Dictionary with results for each topic
        """
        all_results = {
            "context": context,
            "topics": {},
            "search_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for topic in topics:
            # Enhance query with context
            enhanced_query = f"{topic} {context}".strip()
            
            try:
                topic_results = await self.search(
                    query=enhanced_query,
                    max_results=5,
                    search_type="technical" if "cloud" in context.lower() or "infrastructure" in context.lower() else "general"
                )
                
                all_results["topics"][topic] = {
                    "results": topic_results["results"],
                    "query_used": enhanced_query,
                    "result_count": len(topic_results["results"])
                }
                
            except Exception as e:
                logger.error(f"Failed to search for topic '{topic}': {e}")
                all_results["topics"][topic] = {
                    "results": [],
                    "query_used": enhanced_query,
                    "result_count": 0,
                    "error": str(e)
                }
        
        return all_results
    
    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a specific URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary with extracted content
        """
        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text content
                text_content = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                
                return {
                    "url": url,
                    "title": soup.title.string if soup.title else "",
                    "content": clean_text[:5000],  # Limit content length
                    "word_count": len(clean_text.split()),
                    "extracted_timestamp": datetime.now(timezone.utc).isoformat(),
                    "success": True
                }
            else:
                return {
                    "url": url,
                    "error": f"HTTP {response.status_code}",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()


# Singleton instance
_web_search_client = None


async def get_web_search_client() -> WebSearchClient:
    """Get or create the global web search client instance."""
    global _web_search_client
    if _web_search_client is None:
        _web_search_client = WebSearchClient()
    return _web_search_client


async def search_web(
    query: str,
    max_results: int = 10,
    search_type: str = "general"
) -> Dict[str, Any]:
    """
    Convenience function for web search.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        search_type: Type of search
        
    Returns:
        Search results dictionary
    """
    client = await get_web_search_client()
    return await client.search(query, max_results, search_type)


async def search_cloud_infrastructure_topics(topics: List[str]) -> Dict[str, Any]:
    """
    Search for cloud infrastructure specific topics.
    
    Args:
        topics: List of infrastructure topics to search
        
    Returns:
        Search results for each topic
    """
    client = await get_web_search_client()
    return await client.search_specific_topics(
        topics, 
        context="cloud infrastructure technology trends pricing"
    )