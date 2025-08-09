"""
LLM Usage Optimizer for cost reduction and efficiency improvements.

Provides comprehensive optimization features including:
- Prompt engineering optimization for cost reduction
- Response caching for similar queries
- Token usage limits and budget controls
- Usage pattern analysis and recommendations
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re

from .interface import LLMRequest, LLMResponse, LLMProvider, TokenUsage
from .cost_tracker import CostTracker, BudgetAlert, CostPeriod
from ..core.cache import ProductionCacheManager, CacheConfig

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """LLM optimization strategies."""
    AGGRESSIVE = "aggressive"  # Maximum cost reduction
    BALANCED = "balanced"     # Balance cost and quality
    CONSERVATIVE = "conservative"  # Minimal optimization, preserve quality


class PromptComplexity(str, Enum):
    """Prompt complexity levels for optimization."""
    SIMPLE = "simple"      # Basic queries, can use cheaper models
    MODERATE = "moderate"  # Standard queries, balanced optimization
    COMPLEX = "complex"    # Complex queries, minimal optimization
    CRITICAL = "critical"  # Critical queries, no optimization


@dataclass
class OptimizationRule:
    """Rule for prompt optimization."""
    name: str
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement text
    token_savings: int  # Estimated token savings
    quality_impact: float  # Quality impact (0.0 to 1.0, lower is better)
    enabled: bool = True


@dataclass
class CacheEntry:
    """Cached LLM response entry."""
    request_hash: str
    response: LLMResponse
    cached_at: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)


@dataclass
class UsageLimits:
    """Token usage and budget limits."""
    daily_token_limit: Optional[int] = None
    monthly_token_limit: Optional[int] = None
    daily_budget_limit: Optional[float] = None
    monthly_budget_limit: Optional[float] = None
    per_request_token_limit: Optional[int] = None
    per_agent_daily_limit: Optional[int] = None
    cost_per_token_threshold: Optional[float] = None  # Alert if cost per token exceeds this


@dataclass
class OptimizationMetrics:
    """Metrics for optimization performance."""
    total_requests: int = 0
    optimized_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved: int = 0
    cost_saved: float = 0.0
    quality_score: float = 1.0
    optimization_time_ms: float = 0.0


class LLMUsageOptimizer:
    """
    Comprehensive LLM usage optimizer for cost reduction and efficiency.
    
    Features:
    - Intelligent prompt optimization based on complexity analysis
    - Semantic response caching with similarity matching
    - Dynamic token usage limits and budget controls
    - Real-time usage monitoring and alerting
    - Optimization recommendations based on usage patterns
    """
    
    def __init__(
        self,
        cost_tracker: CostTracker,
        cache_manager: Optional[ProductionCacheManager] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ):
        """
        Initialize LLM usage optimizer.
        
        Args:
            cost_tracker: Cost tracking instance
            cache_manager: Cache manager for response caching
            strategy: Optimization strategy to use
        """
        self.cost_tracker = cost_tracker
        self.cache_manager = cache_manager
        self.strategy = strategy
        
        # Optimization rules
        self.optimization_rules = self._initialize_optimization_rules()
        
        # Response cache
        self.response_cache: Dict[str, CacheEntry] = {}
        self.cache_max_size = 10000
        self.cache_ttl_hours = 24
        
        # Usage limits and controls
        self.usage_limits = UsageLimits()
        self.current_usage = {
            "daily_tokens": 0,
            "monthly_tokens": 0,
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "agent_usage": {}  # agent_name -> daily_tokens
        }
        
        # Metrics
        self.metrics = OptimizationMetrics()
        
        # Similarity threshold for cache matching
        self.similarity_threshold = 0.85
        
        logger.info(f"LLM Usage Optimizer initialized with {strategy.value} strategy")
    
    def _initialize_optimization_rules(self) -> List[OptimizationRule]:
        """Initialize prompt optimization rules based on strategy."""
        base_rules = [
            # Remove redundant phrases
            OptimizationRule(
                name="remove_redundant_please",
                pattern=r"\b(please|kindly)\s+",
                replacement="",
                token_savings=1,
                quality_impact=0.0
            ),
            OptimizationRule(
                name="remove_redundant_very",
                pattern=r"\bvery\s+",
                replacement="",
                token_savings=1,
                quality_impact=0.1
            ),
            # Simplify verbose expressions
            OptimizationRule(
                name="simplify_in_order_to",
                pattern=r"\bin order to\b",
                replacement="to",
                token_savings=2,
                quality_impact=0.0
            ),
            OptimizationRule(
                name="simplify_due_to_the_fact",
                pattern=r"\bdue to the fact that\b",
                replacement="because",
                token_savings=4,
                quality_impact=0.0
            ),
            # Remove filler words
            OptimizationRule(
                name="remove_actually",
                pattern=r"\bactually\s+",
                replacement="",
                token_savings=1,
                quality_impact=0.0
            ),
            OptimizationRule(
                name="remove_basically",
                pattern=r"\bbasically\s+",
                replacement="",
                token_savings=1,
                quality_impact=0.0
            ),
        ]
        
        # Add strategy-specific rules
        if self.strategy == OptimizationStrategy.AGGRESSIVE:
            base_rules.extend([
                OptimizationRule(
                    name="remove_articles",
                    pattern=r"\b(a|an|the)\s+",
                    replacement="",
                    token_savings=1,
                    quality_impact=0.3
                ),
                OptimizationRule(
                    name="abbreviate_and",
                    pattern=r"\band\b",
                    replacement="&",
                    token_savings=1,
                    quality_impact=0.1
                ),
            ])
        
        return base_rules
    
    async def optimize_request(self, request: LLMRequest) -> Tuple[LLMRequest, Dict[str, Any]]:
        """
        Optimize LLM request for cost and efficiency.
        
        Args:
            request: Original LLM request
            
        Returns:
            Tuple of (optimized_request, optimization_metadata)
        """
        start_time = datetime.now(timezone.utc)
        optimization_metadata = {
            "original_request": request,
            "optimizations_applied": [],
            "tokens_saved": 0,
            "estimated_cost_savings": 0.0,
            "cache_hit": False,
            "complexity": None,
            "strategy": self.strategy.value
        }
        
        try:
            # Check usage limits first
            if not await self._check_usage_limits(request):
                raise ValueError("Usage limits exceeded")
            
            # Check cache for similar requests
            cached_response = await self._check_response_cache(request)
            if cached_response:
                optimization_metadata["cache_hit"] = True
                optimization_metadata["cached_response"] = cached_response
                self.metrics.cache_hits += 1
                return request, optimization_metadata
            
            self.metrics.cache_misses += 1
            
            # Analyze prompt complexity
            complexity = self._analyze_prompt_complexity(request.prompt)
            optimization_metadata["complexity"] = complexity.value
            
            # Create optimized copy of request
            optimized_request = LLMRequest(
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt=request.system_prompt,
                context=request.context.copy(),
                agent_name=request.agent_name,
                request_id=request.request_id,
                timestamp=request.timestamp
            )
            
            # Apply optimizations based on complexity and strategy
            if complexity != PromptComplexity.CRITICAL:
                # Optimize prompt text
                optimized_prompt, prompt_optimizations = self._optimize_prompt_text(
                    optimized_request.prompt, complexity
                )
                optimized_request.prompt = optimized_prompt
                optimization_metadata["optimizations_applied"].extend(prompt_optimizations)
                
                # Optimize system prompt if present
                if optimized_request.system_prompt:
                    optimized_system, system_optimizations = self._optimize_prompt_text(
                        optimized_request.system_prompt, complexity
                    )
                    optimized_request.system_prompt = optimized_system
                    optimization_metadata["optimizations_applied"].extend(system_optimizations)
                
                # Optimize model selection
                model_optimization = self._optimize_model_selection(optimized_request, complexity)
                if model_optimization:
                    optimization_metadata["optimizations_applied"].append(model_optimization)
                
                # Optimize token limits
                token_optimization = self._optimize_token_limits(optimized_request, complexity)
                if token_optimization:
                    optimization_metadata["optimizations_applied"].append(token_optimization)
            
            # Calculate savings
            original_tokens = self._estimate_tokens(request.prompt + (request.system_prompt or ""))
            optimized_tokens = self._estimate_tokens(
                optimized_request.prompt + (optimized_request.system_prompt or "")
            )
            tokens_saved = original_tokens - optimized_tokens
            
            optimization_metadata["tokens_saved"] = tokens_saved
            optimization_metadata["estimated_cost_savings"] = tokens_saved * 0.00002  # Rough estimate
            
            # Update metrics
            self.metrics.total_requests += 1
            if tokens_saved > 0:
                self.metrics.optimized_requests += 1
                self.metrics.tokens_saved += tokens_saved
                self.metrics.cost_saved += optimization_metadata["estimated_cost_savings"]
            
            # Calculate optimization time
            optimization_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics.optimization_time_ms = (
                (self.metrics.optimization_time_ms + optimization_time) / 2
                if self.metrics.optimization_time_ms > 0 else optimization_time
            )
            
            logger.debug(
                f"Optimized request: {tokens_saved} tokens saved, "
                f"{len(optimization_metadata['optimizations_applied'])} optimizations applied"
            )
            
            return optimized_request, optimization_metadata
            
        except Exception as e:
            logger.error(f"Request optimization failed: {e}")
            return request, optimization_metadata
    
    def _analyze_prompt_complexity(self, prompt: str) -> PromptComplexity:
        """
        Analyze prompt complexity to determine optimization level.
        
        Args:
            prompt: Prompt text to analyze
            
        Returns:
            Prompt complexity level
        """
        # Critical indicators (no optimization)
        critical_patterns = [
            r"\b(critical|urgent|important|security|compliance|legal)\b",
            r"\b(production|live|customer|client)\b",
            r"\b(financial|payment|transaction|billing)\b"
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, prompt.lower()):
                return PromptComplexity.CRITICAL
        
        # Complex indicators (minimal optimization)
        complex_patterns = [
            r"\b(analyze|evaluate|assess|compare|detailed|comprehensive)\b",
            r"\b(algorithm|architecture|design|implementation)\b",
            r"\b(strategy|planning|roadmap|recommendation)\b"
        ]
        
        complex_matches = sum(1 for pattern in complex_patterns 
                            if re.search(pattern, prompt.lower()))
        
        if complex_matches >= 3:
            return PromptComplexity.COMPLEX
        
        # Simple indicators
        simple_patterns = [
            r"\b(list|show|display|what|how|when|where)\b",
            r"\b(yes|no|true|false|simple|basic)\b"
        ]
        
        simple_matches = sum(1 for pattern in simple_patterns 
                           if re.search(pattern, prompt.lower()))
        
        if simple_matches >= 2 and len(prompt.split()) < 50:
            return PromptComplexity.SIMPLE
        
        return PromptComplexity.MODERATE
    
    def _optimize_prompt_text(
        self, 
        prompt: str, 
        complexity: PromptComplexity
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Optimize prompt text using optimization rules.
        
        Args:
            prompt: Original prompt text
            complexity: Prompt complexity level
            
        Returns:
            Tuple of (optimized_prompt, applied_optimizations)
        """
        optimized_prompt = prompt
        applied_optimizations = []
        
        # Apply rules based on complexity and strategy
        for rule in self.optimization_rules:
            if not rule.enabled:
                continue
            
            # Skip aggressive optimizations for complex prompts
            if complexity == PromptComplexity.COMPLEX and rule.quality_impact > 0.2:
                continue
            
            # Skip all optimizations for critical prompts
            if complexity == PromptComplexity.CRITICAL:
                continue
            
            # Apply rule
            original_length = len(optimized_prompt)
            optimized_prompt = re.sub(rule.pattern, rule.replacement, optimized_prompt, flags=re.IGNORECASE)
            
            if len(optimized_prompt) != original_length:
                applied_optimizations.append({
                    "rule": rule.name,
                    "tokens_saved": rule.token_savings,
                    "quality_impact": rule.quality_impact,
                    "characters_removed": original_length - len(optimized_prompt)
                })
        
        return optimized_prompt, applied_optimizations
    
    def _optimize_model_selection(
        self, 
        request: LLMRequest, 
        complexity: PromptComplexity
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize model selection based on prompt complexity.
        
        Args:
            request: LLM request
            complexity: Prompt complexity level
            
        Returns:
            Model optimization metadata or None
        """
        if not request.model:
            return None
        
        current_model = (request.model or "").lower()
        suggested_model = None
        cost_savings = 0.0
        
        # Suggest cheaper models for simple prompts
        if complexity == PromptComplexity.SIMPLE:
            if "gpt-4" in current_model:
                suggested_model = "gpt-3.5-turbo"
                cost_savings = 0.85  # Rough estimate
            elif "gemini-1.5-pro" in current_model:
                suggested_model = "gemini-1.5-flash"
                cost_savings = 0.70
        
        elif complexity == PromptComplexity.MODERATE and self.strategy == OptimizationStrategy.AGGRESSIVE:
            if "gpt-4-turbo" in current_model:
                suggested_model = "gpt-4"
                cost_savings = 0.30
        
        if suggested_model:
            # Only apply if strategy allows
            if (self.strategy == OptimizationStrategy.AGGRESSIVE or 
                (self.strategy == OptimizationStrategy.BALANCED and complexity == PromptComplexity.SIMPLE)):
                
                request.model = suggested_model
                return {
                    "type": "model_optimization",
                    "original_model": current_model,
                    "optimized_model": suggested_model,
                    "estimated_cost_savings_percentage": cost_savings * 100,
                    "complexity": complexity.value
                }
        
        return None
    
    def _optimize_token_limits(
        self, 
        request: LLMRequest, 
        complexity: PromptComplexity
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize token limits based on prompt complexity and usage patterns.
        
        Args:
            request: LLM request
            complexity: Prompt complexity level
            
        Returns:
            Token optimization metadata or None
        """
        if not request.max_tokens:
            return None
        
        original_max_tokens = request.max_tokens
        optimized_max_tokens = original_max_tokens
        
        # Reduce token limits for simple prompts
        if complexity == PromptComplexity.SIMPLE:
            optimized_max_tokens = min(original_max_tokens, 500)
        elif complexity == PromptComplexity.MODERATE:
            optimized_max_tokens = min(original_max_tokens, 1500)
        
        # Apply per-request token limits
        if self.usage_limits.per_request_token_limit:
            optimized_max_tokens = min(optimized_max_tokens, self.usage_limits.per_request_token_limit)
        
        if optimized_max_tokens != original_max_tokens:
            request.max_tokens = optimized_max_tokens
            return {
                "type": "token_limit_optimization",
                "original_max_tokens": original_max_tokens,
                "optimized_max_tokens": optimized_max_tokens,
                "tokens_saved": original_max_tokens - optimized_max_tokens,
                "complexity": complexity.value
            }
        
        return None
    
    async def _check_response_cache(self, request: LLMRequest) -> Optional[LLMResponse]:
        """
        Check if a similar request exists in the response cache.
        
        Args:
            request: LLM request to check
            
        Returns:
            Cached response if found, None otherwise
        """
        try:
            # Generate request hash for exact matching
            request_hash = self._generate_request_hash(request)
            
            # Check exact match first
            if request_hash in self.response_cache:
                cache_entry = self.response_cache[request_hash]
                
                # Check if cache entry is still valid
                if self._is_cache_entry_valid(cache_entry):
                    cache_entry.hit_count += 1
                    cache_entry.last_accessed = datetime.now(timezone.utc)
                    logger.debug(f"Exact cache hit for request {request.request_id}")
                    return cache_entry.response
                else:
                    # Remove expired entry
                    del self.response_cache[request_hash]
            
            # Check for similar requests using semantic similarity
            similar_response = await self._find_similar_cached_response(request)
            if similar_response:
                logger.debug(f"Similar cache hit for request {request.request_id}")
                return similar_response
            
            return None
            
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None
    
    def _generate_request_hash(self, request: LLMRequest) -> str:
        """
        Generate a hash for the request to use as cache key.
        
        Args:
            request: LLM request
            
        Returns:
            Request hash string
        """
        # Create a normalized representation of the request
        cache_key_data = {
            "prompt": (request.prompt or "").strip().lower(),
            "system_prompt": (request.system_prompt or "").strip().lower(),
            "model": request.model or "",
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 2000,
            # Include relevant context that affects the response
            "agent_name": request.agent_name or "",
            "context_keys": sorted(request.context.keys()) if request.context else []
        }
        
        # Generate hash
        cache_key_str = json.dumps(cache_key_data, sort_keys=True)
        return hashlib.sha256(cache_key_str.encode()).hexdigest()[:16]
    
    def _is_cache_entry_valid(self, cache_entry: CacheEntry) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            cache_entry: Cache entry to check
            
        Returns:
            True if valid, False otherwise
        """
        age_hours = (datetime.now(timezone.utc) - cache_entry.cached_at).total_seconds() / 3600
        return age_hours < self.cache_ttl_hours
    
    async def _find_similar_cached_response(self, request: LLMRequest) -> Optional[LLMResponse]:
        """
        Find similar cached responses using semantic similarity.
        
        Args:
            request: LLM request
            
        Returns:
            Similar cached response or None
        """
        try:
            # Simple similarity check based on prompt text
            # In a production system, you might use embeddings for better similarity
            request_words = set((request.prompt or "").lower().split())
            
            best_similarity = 0.0
            best_response = None
            
            for cache_entry in self.response_cache.values():
                if not self._is_cache_entry_valid(cache_entry):
                    continue
                
                # Get original request from cache entry
                cached_prompt = cache_entry.response.metadata.get("original_prompt", "")
                cached_words = set((cached_prompt or "").lower().split())
                
                # Calculate Jaccard similarity
                if len(request_words) > 0 and len(cached_words) > 0:
                    intersection = len(request_words.intersection(cached_words))
                    union = len(request_words.union(cached_words))
                    similarity = intersection / union if union > 0 else 0.0
                    
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_response = cache_entry.response
                        cache_entry.hit_count += 1
                        cache_entry.last_accessed = datetime.now(timezone.utc)
            
            if best_response:
                logger.debug(f"Found similar cached response with {best_similarity:.2f} similarity")
                return best_response
            
            return None
            
        except Exception as e:
            logger.error(f"Similar cache lookup failed: {e}")
            return None
    
    async def cache_response(self, request: LLMRequest, response: LLMResponse) -> None:
        """
        Cache an LLM response for future use.
        
        Args:
            request: Original LLM request
            response: LLM response to cache
        """
        try:
            # Generate cache key
            request_hash = self._generate_request_hash(request)
            
            # Add original prompt to response metadata for similarity matching
            response.metadata["original_prompt"] = request.prompt
            response.metadata["original_system_prompt"] = request.system_prompt
            
            # Create cache entry
            cache_entry = CacheEntry(
                request_hash=request_hash,
                response=response,
                cached_at=datetime.now(timezone.utc),
                tags=[request.agent_name] if request.agent_name else []
            )
            
            # Store in cache
            self.response_cache[request_hash] = cache_entry
            
            # Clean up cache if it's getting too large
            if len(self.response_cache) > self.cache_max_size:
                await self._cleanup_cache()
            
            logger.debug(f"Cached response for request {request.request_id}")
            
        except Exception as e:
            logger.error(f"Response caching failed: {e}")
    
    async def _cleanup_cache(self) -> None:
        """Clean up old cache entries to maintain cache size limits."""
        try:
            # Remove expired entries first
            expired_keys = [
                key for key, entry in self.response_cache.items()
                if not self._is_cache_entry_valid(entry)
            ]
            
            for key in expired_keys:
                del self.response_cache[key]
            
            # If still over limit, remove least recently used entries
            if len(self.response_cache) > self.cache_max_size:
                # Sort by last accessed time
                sorted_entries = sorted(
                    self.response_cache.items(),
                    key=lambda x: x[1].last_accessed
                )
                
                # Remove oldest entries
                entries_to_remove = len(self.response_cache) - int(self.cache_max_size * 0.8)
                for key, _ in sorted_entries[:entries_to_remove]:
                    del self.response_cache[key]
            
            logger.debug(f"Cache cleanup completed, {len(self.response_cache)} entries remaining")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    async def _check_usage_limits(self, request: LLMRequest) -> bool:
        """
        Check if request is within usage limits.
        
        Args:
            request: LLM request to check
            
        Returns:
            True if within limits, False otherwise
        """
        try:
            # Update current usage from cost tracker
            await self._update_current_usage()
            
            # Check daily token limit
            if (self.usage_limits.daily_token_limit and 
                self.current_usage["daily_tokens"] >= self.usage_limits.daily_token_limit):
                logger.warning("Daily token limit exceeded")
                return False
            
            # Check monthly token limit
            if (self.usage_limits.monthly_token_limit and 
                self.current_usage["monthly_tokens"] >= self.usage_limits.monthly_token_limit):
                logger.warning("Monthly token limit exceeded")
                return False
            
            # Check daily budget limit
            if (self.usage_limits.daily_budget_limit and 
                self.current_usage["daily_cost"] >= self.usage_limits.daily_budget_limit):
                logger.warning("Daily budget limit exceeded")
                return False
            
            # Check monthly budget limit
            if (self.usage_limits.monthly_budget_limit and 
                self.current_usage["monthly_cost"] >= self.usage_limits.monthly_budget_limit):
                logger.warning("Monthly budget limit exceeded")
                return False
            
            # Check per-agent daily limit
            if (request.agent_name and self.usage_limits.per_agent_daily_limit):
                agent_usage = self.current_usage["agent_usage"].get(request.agent_name, 0)
                if agent_usage >= self.usage_limits.per_agent_daily_limit:
                    logger.warning(f"Daily limit exceeded for agent {request.agent_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Usage limit check failed: {e}")
            return True  # Allow request if check fails
    
    async def _update_current_usage(self) -> None:
        """Update current usage statistics from cost tracker."""
        try:
            # Get daily usage
            daily_summary = self.cost_tracker.get_cost_summary(CostPeriod.DAILY)
            self.current_usage["daily_tokens"] = daily_summary.total_tokens
            self.current_usage["daily_cost"] = daily_summary.total_cost
            
            # Get monthly usage
            monthly_summary = self.cost_tracker.get_cost_summary(CostPeriod.MONTHLY)
            self.current_usage["monthly_tokens"] = monthly_summary.total_tokens
            self.current_usage["monthly_cost"] = monthly_summary.total_cost
            
            # Update agent usage
            self.current_usage["agent_usage"] = daily_summary.agent_breakdown.copy()
            
        except Exception as e:
            logger.error(f"Failed to update current usage: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    def set_usage_limits(self, limits: UsageLimits) -> None:
        """
        Set usage limits and budget controls.
        
        Args:
            limits: Usage limits configuration
        """
        self.usage_limits = limits
        logger.info("Usage limits updated")
    
    def add_optimization_rule(self, rule: OptimizationRule) -> None:
        """
        Add a custom optimization rule.
        
        Args:
            rule: Optimization rule to add
        """
        self.optimization_rules.append(rule)
        logger.info(f"Added optimization rule: {rule.name}")
    
    def remove_optimization_rule(self, rule_name: str) -> bool:
        """
        Remove an optimization rule by name.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, rule in enumerate(self.optimization_rules):
            if rule.name == rule_name:
                del self.optimization_rules[i]
                logger.info(f"Removed optimization rule: {rule_name}")
                return True
        return False
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization statistics and performance metrics.
        
        Returns:
            Optimization statistics dictionary
        """
        cache_stats = {
            "total_entries": len(self.response_cache),
            "valid_entries": sum(1 for entry in self.response_cache.values() 
                               if self._is_cache_entry_valid(entry)),
            "total_hits": sum(entry.hit_count for entry in self.response_cache.values()),
            "cache_size_mb": len(json.dumps([{
                "content": entry.response.content,
                "model": entry.response.model,
                "provider": entry.response.provider.value,
                "token_usage": {
                    "total_tokens": entry.response.token_usage.total_tokens,
                    "estimated_cost": entry.response.token_usage.estimated_cost
                }
            } for entry in self.response_cache.values()])) / (1024 * 1024)
        }
        
        return {
            "strategy": self.strategy.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "optimized_requests": self.metrics.optimized_requests,
                "optimization_rate": (
                    self.metrics.optimized_requests / self.metrics.total_requests * 100
                    if self.metrics.total_requests > 0 else 0
                ),
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_rate": (
                    self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses) * 100
                    if (self.metrics.cache_hits + self.metrics.cache_misses) > 0 else 0
                ),
                "tokens_saved": self.metrics.tokens_saved,
                "cost_saved": round(self.metrics.cost_saved, 4),
                "avg_optimization_time_ms": round(self.metrics.optimization_time_ms, 2)
            },
            "cache_stats": cache_stats,
            "usage_limits": {
                "daily_token_limit": self.usage_limits.daily_token_limit,
                "monthly_token_limit": self.usage_limits.monthly_token_limit,
                "daily_budget_limit": self.usage_limits.daily_budget_limit,
                "monthly_budget_limit": self.usage_limits.monthly_budget_limit,
                "per_request_token_limit": self.usage_limits.per_request_token_limit,
                "per_agent_daily_limit": self.usage_limits.per_agent_daily_limit
            },
            "current_usage": self.current_usage.copy(),
            "optimization_rules": [
                {
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "token_savings": rule.token_savings,
                    "quality_impact": rule.quality_impact
                }
                for rule in self.optimization_rules
            ]
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations based on usage patterns.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # Cache performance recommendations
        if self.metrics.cache_hits + self.metrics.cache_misses > 100:
            cache_hit_rate = (
                self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses) * 100
            )
            
            if cache_hit_rate < 20:
                recommendations.append({
                    "type": "cache_optimization",
                    "priority": "medium",
                    "title": "Low cache hit rate detected",
                    "description": f"Cache hit rate is {cache_hit_rate:.1f}%, consider adjusting similarity threshold",
                    "actions": [
                        "Lower similarity threshold for more cache hits",
                        "Increase cache TTL for longer-lived entries",
                        "Review prompt patterns for better caching"
                    ]
                })
        
        # Token usage recommendations
        if self.metrics.total_requests > 50:
            avg_tokens_saved = self.metrics.tokens_saved / self.metrics.total_requests
            
            if avg_tokens_saved < 10:
                recommendations.append({
                    "type": "prompt_optimization",
                    "priority": "high",
                    "title": "Low token savings detected",
                    "description": f"Average {avg_tokens_saved:.1f} tokens saved per request",
                    "actions": [
                        "Enable more aggressive optimization strategy",
                        "Add custom optimization rules for your domain",
                        "Review prompts for redundant content"
                    ]
                })
        
        # Budget recommendations
        daily_usage_pct = 0
        if self.usage_limits.daily_budget_limit:
            daily_usage_pct = (self.current_usage["daily_cost"] / self.usage_limits.daily_budget_limit) * 100
        
        if daily_usage_pct > 80:
            recommendations.append({
                "type": "budget_management",
                "priority": "high",
                "title": "High daily budget utilization",
                "description": f"Using {daily_usage_pct:.1f}% of daily budget",
                "actions": [
                    "Enable more aggressive cost optimization",
                    "Implement stricter token limits",
                    "Review high-cost agents and models"
                ]
            })
        
        return recommendations
    
    async def clear_cache(self, agent_name: Optional[str] = None) -> int:
        """
        Clear response cache entries.
        
        Args:
            agent_name: Clear only entries for specific agent (optional)
            
        Returns:
            Number of entries cleared
        """
        try:
            if agent_name:
                # Clear entries for specific agent
                keys_to_remove = [
                    key for key, entry in self.response_cache.items()
                    if agent_name in entry.tags
                ]
            else:
                # Clear all entries
                keys_to_remove = list(self.response_cache.keys())
            
            for key in keys_to_remove:
                del self.response_cache[key]
            
            logger.info(f"Cleared {len(keys_to_remove)} cache entries")
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0