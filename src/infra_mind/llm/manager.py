"""
LLM Manager for coordinating multiple LLM providers.

Provides unified interface for managing multiple LLM providers,
load balancing, failover, and cost optimization.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timezone
from enum import Enum

from .interface import (
    LLMProviderInterface, 
    LLMProvider, 
    LLMRequest, 
    LLMResponse,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMQuotaExceededError
)
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .cost_tracker import CostTracker
from .response_validator import ResponseValidator, ValidationResult
from .prompt_formatter import prompt_formatter
from .usage_optimizer import LLMUsageOptimizer, OptimizationStrategy, UsageLimits
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for multiple providers."""
    ROUND_ROBIN = "round_robin"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    RANDOM = "random"


class FailoverStrategy(str, Enum):
    """Failover strategies when primary provider fails."""
    IMMEDIATE = "immediate"
    RETRY_THEN_FAILOVER = "retry_then_failover"
    COST_AWARE = "cost_aware"


class LLMManager:
    """
    Comprehensive LLM manager for multiple providers.
    
    Features:
    - Multiple provider support with unified interface
    - Load balancing and failover strategies
    - Cost tracking and optimization
    - Response validation and quality assurance
    - Usage analytics and monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM manager.
        
        Args:
            config: Manager configuration
        """
        self.config = config or {}
        self.settings = get_settings()
        
        # Initialize components
        self.providers: Dict[LLMProvider, LLMProviderInterface] = {}
        self.cost_tracker = CostTracker()
        self.response_validator = ResponseValidator(
            self.config.get("validation", {})
        )
        
        # Initialize usage optimizer
        optimization_strategy = OptimizationStrategy(
            self.config.get("optimization_strategy", OptimizationStrategy.BALANCED.value)
        )
        self.usage_optimizer = LLMUsageOptimizer(
            cost_tracker=self.cost_tracker,
            strategy=optimization_strategy
        )
        
        # Set usage limits if configured
        usage_limits_config = self.config.get("usage_limits", {})
        if usage_limits_config:
            usage_limits = UsageLimits(
                daily_token_limit=usage_limits_config.get("daily_token_limit"),
                monthly_token_limit=usage_limits_config.get("monthly_token_limit"),
                daily_budget_limit=usage_limits_config.get("daily_budget_limit"),
                monthly_budget_limit=usage_limits_config.get("monthly_budget_limit"),
                per_request_token_limit=usage_limits_config.get("per_request_token_limit"),
                per_agent_daily_limit=usage_limits_config.get("per_agent_daily_limit"),
                cost_per_token_threshold=usage_limits_config.get("cost_per_token_threshold")
            )
            self.usage_optimizer.set_usage_limits(usage_limits)
        
        # Load balancing and failover
        self.load_balancing_strategy = LoadBalancingStrategy(
            self.config.get("load_balancing", LoadBalancingStrategy.COST_OPTIMIZED.value)
        )
        self.failover_strategy = FailoverStrategy(
            self.config.get("failover", FailoverStrategy.RETRY_THEN_FAILOVER.value)
        )
        
        # Provider selection state
        self._current_provider_index = 0
        self._provider_health: Dict[LLMProvider, bool] = {}
        self._provider_performance: Dict[LLMProvider, float] = {}
        
        # Initialize providers
        self._initialize_providers()
        
        logger.info(f"LLM Manager initialized with {len(self.providers)} providers")
    
    def _initialize_providers(self) -> None:
        """Initialize LLM providers based on configuration - prioritize specified provider."""
        # Get preferred provider from multiple sources
        preferred_provider = None
        
        # 1. Check config passed to manager
        if self.config and "preferred_provider" in self.config:
            preferred_provider = self.config["preferred_provider"]
        
        # 2. Check settings llm_provider
        if not preferred_provider:
            preferred_provider = getattr(self.settings, 'llm_provider', None)
        
        # 3. Default to openai
        if not preferred_provider:
            preferred_provider = 'openai'
        
        # Ensure it's a string and lowercase
        if preferred_provider is None:
            preferred_provider = 'openai'
        preferred_provider = str(preferred_provider).lower()
        
        # Initialize only OpenAI provider for this system
        if preferred_provider == 'openai':
            openai_key = self.settings.get_openai_api_key()
            if openai_key:
                try:
                    openai_provider = OpenAIProvider(
                        api_key=openai_key,
                        model=self.settings.llm_model,
                        temperature=self.settings.llm_temperature,
                        max_tokens=self.settings.llm_max_tokens,
                        timeout=self.settings.llm_timeout
                    )
                    self.providers[LLMProvider.OPENAI] = openai_provider
                    self._provider_health[LLMProvider.OPENAI] = True
                    self._provider_performance[LLMProvider.OPENAI] = 1.0
                    logger.info("OpenAI provider initialized as primary")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI provider: {str(e)}")
            else:
                logger.error("OpenAI API key not found - cannot initialize OpenAI provider")
        else:
            logger.warning(f"Unsupported LLM provider: {preferred_provider}. Only OpenAI is supported.")
        
        if not self.providers:
            logger.error("No LLM providers initialized - check API key configuration")
    
    async def generate_response(
        self, 
        request: LLMRequest, 
        validate_response: bool = True,
        agent_name: Optional[str] = None,
        enable_optimization: bool = True
    ) -> LLMResponse:
        """
        Generate response using the best available provider.
        
        Args:
            request: LLM request
            validate_response: Whether to validate the response
            agent_name: Name of the requesting agent
            
        Returns:
            LLM response
            
        Raises:
            LLMError: If all providers fail
        """
        if not self.providers:
            raise LLMError("No LLM providers available", LLMProvider.OPENAI)
        
        # Update request with agent name
        if agent_name:
            request.agent_name = agent_name
        
        # Optimize request if enabled
        optimization_metadata = {}
        if enable_optimization:
            try:
                request, optimization_metadata = await self.usage_optimizer.optimize_request(request)
                
                # Check if we got a cached response
                if optimization_metadata.get("cache_hit") and optimization_metadata.get("cached_response"):
                    cached_response = optimization_metadata["cached_response"]
                    cached_response.metadata.update({
                        "optimization": optimization_metadata,
                        "cache_hit": True
                    })
                    return cached_response
                    
            except Exception as e:
                logger.warning(f"Request optimization failed: {e}")
        
        # Select provider based on strategy
        provider_order = self._get_provider_order(request)
        
        last_exception = None
        
        for provider_type in provider_order:
            provider = self.providers.get(provider_type)
            if not provider or not self._provider_health.get(provider_type, False):
                continue
            
            try:
                logger.debug(f"Attempting request with {provider_type.value} provider")
                
                # Format request for the specific provider
                formatted_request = prompt_formatter.format_request_for_provider(request, provider_type)
                
                # Generate response
                response = await provider.generate_response(formatted_request)
                
                # Track cost
                self.cost_tracker.track_usage(
                    response.token_usage, 
                    agent_name, 
                    request.request_id
                )
                
                # Validate response if requested
                if validate_response:
                    validation_result = self.response_validator.validate_response(
                        response,
                        context={
                            "agent_name": agent_name,
                            "expected_format": request.context.get("expected_format")
                        }
                    )
                    
                    # Add validation metadata to response
                    response.metadata.update({
                        "validation": validation_result.to_dict()
                    })
                    
                    # Log validation issues
                    if validation_result.has_errors:
                        logger.warning(
                            f"Response validation errors for {agent_name}: "
                            f"{len([i for i in validation_result.issues if i.severity.value in ['error', 'critical']])} issues"
                        )
                    
                    # Optionally reject responses with critical issues
                    if (validation_result.has_errors and 
                        self.config.get("reject_invalid_responses", False)):
                        raise LLMError(
                            f"Response validation failed: {validation_result.issues[0].message}",
                            provider_type
                        )
                
                # Update provider performance
                self._update_provider_performance(provider_type, response.response_time, True)
                
                # Add optimization metadata to response
                if enable_optimization:
                    response.metadata.update({
                        "optimization": optimization_metadata,
                        "cache_hit": False
                    })
                    
                    # Cache the response for future use
                    try:
                        await self.usage_optimizer.cache_response(request, response)
                    except Exception as e:
                        logger.warning(f"Response caching failed: {e}")
                
                logger.info(
                    f"Successfully generated response using {provider_type.value} - "
                    f"Tokens: {response.token_usage.total_tokens}, "
                    f"Cost: ${response.token_usage.estimated_cost:.4f}"
                )
                
                return response
                
            except LLMAuthenticationError as e:
                logger.error(f"{provider_type.value} authentication failed: {str(e)}")
                self._provider_health[provider_type] = False
                last_exception = e
                continue
                
            except LLMRateLimitError as e:
                logger.warning(f"{provider_type.value} rate limited: {str(e)}")
                # Don't mark as unhealthy for rate limits, just try next provider
                last_exception = e
                continue
                
            except LLMQuotaExceededError as e:
                logger.error(f"{provider_type.value} quota exceeded: {str(e)}")
                self._provider_health[provider_type] = False
                last_exception = e
                continue
                
            except Exception as e:
                import traceback
                logger.error(f"{provider_type.value} request failed: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                self._update_provider_performance(provider_type, 0, False)
                last_exception = e
                continue
        
        # If we get here, all providers failed
        error_msg = f"All LLM providers failed. Last error: {str(last_exception)}"
        logger.error(error_msg)
        raise LLMError(error_msg, list(self.providers.keys())[0] if self.providers else LLMProvider.OPENAI)
    
    def _get_provider_order(self, request: LLMRequest) -> List[LLMProvider]:
        """
        Get provider order based on load balancing strategy.
        
        Args:
            request: LLM request
            
        Returns:
            List of providers in order of preference
        """
        available_providers = [
            provider_type for provider_type, provider in self.providers.items()
            if self._provider_health.get(provider_type, False)
        ]
        
        if not available_providers:
            return list(self.providers.keys())
        
        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            # Round robin selection
            self._current_provider_index = (self._current_provider_index + 1) % len(available_providers)
            selected = available_providers[self._current_provider_index]
            return [selected] + [p for p in available_providers if p != selected]
        
        elif self.load_balancing_strategy == LoadBalancingStrategy.COST_OPTIMIZED:
            # Sort by estimated cost (lower first)
            def get_estimated_cost(provider_type: LLMProvider) -> float:
                provider = self.providers[provider_type]
                # Format request for provider to get accurate cost estimate
                formatted_request = prompt_formatter.format_request_for_provider(request, provider_type)
                
                # Estimate tokens more accurately
                prompt_text = formatted_request.prompt
                if formatted_request.system_prompt:
                    prompt_text = f"{formatted_request.system_prompt}\n{prompt_text}"
                
                estimated_prompt_tokens = len(prompt_text.split()) * 1.3
                estimated_completion_tokens = min(request.max_tokens or 2000, estimated_prompt_tokens * 0.5)
                
                return provider.estimate_cost(
                    int(estimated_prompt_tokens),
                    int(estimated_completion_tokens),
                    request.model or provider.model
                )
            
            return sorted(available_providers, key=get_estimated_cost)
        
        elif self.load_balancing_strategy == LoadBalancingStrategy.PERFORMANCE_OPTIMIZED:
            # Sort by performance (higher performance first)
            return sorted(
                available_providers,
                key=lambda p: self._provider_performance.get(p, 0.5),
                reverse=True
            )
        
        elif self.load_balancing_strategy == LoadBalancingStrategy.RANDOM:
            import random
            random.shuffle(available_providers)
            return available_providers
        
        else:
            return available_providers
    
    def _update_provider_performance(self, provider_type: LLMProvider, response_time: float, success: bool) -> None:
        """
        Update provider performance metrics.
        
        Args:
            provider_type: Provider type
            response_time: Response time in seconds
            success: Whether the request was successful
        """
        current_performance = self._provider_performance.get(provider_type, 0.5)
        
        if success:
            # Factor in response time (faster is better)
            time_score = max(0.1, min(1.0, 10.0 / max(response_time, 0.1)))
            new_performance = (current_performance * 0.8) + (time_score * 0.2)
        else:
            # Penalize failures
            new_performance = current_performance * 0.9
        
        self._provider_performance[provider_type] = max(0.1, min(1.0, new_performance))
    
    async def validate_all_providers(self) -> Dict[str, Any]:
        """
        Validate all configured providers.
        
        Returns:
            Validation results for all providers
        """
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                health_status = await provider.health_check()
                results[provider_type.value] = health_status
                
                # Update health status
                self._provider_health[provider_type] = health_status.get("status") == "healthy"
                
            except Exception as e:
                results[provider_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
                self._provider_health[provider_type] = False
        
        return results
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all providers.
        
        Returns:
            Provider statistics
        """
        stats = {
            "total_providers": len(self.providers),
            "healthy_providers": sum(1 for healthy in self._provider_health.values() if healthy),
            "load_balancing_strategy": self.load_balancing_strategy.value,
            "failover_strategy": self.failover_strategy.value,
            "providers": {}
        }
        
        for provider_type, provider in self.providers.items():
            provider_stats = {
                "type": provider_type.value,
                "healthy": self._provider_health.get(provider_type, False),
                "performance_score": round(self._provider_performance.get(provider_type, 0.5), 3),
                "supported_models": provider.supported_models,
                "usage": {
                    "total_requests": provider.request_count,
                    "total_tokens": provider.total_tokens_used,
                    "total_cost": round(provider.total_cost, 4)
                }
            }
            
            stats["providers"][provider_type.value] = provider_stats
        
        return stats
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary across all providers.
        
        Returns:
            Cost summary
        """
        return {
            "cost_tracker": self.cost_tracker.get_usage_statistics(),
            "daily_summary": self.cost_tracker.get_cost_summary("daily").to_dict(),
            "weekly_summary": self.cost_tracker.get_cost_summary("weekly").to_dict(),
            "optimization_recommendations": self.cost_tracker.get_cost_optimization_recommendations()
        }
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get response validation statistics.
        
        Returns:
            Validation statistics
        """
        return self.response_validator.get_validation_stats()
    
    async def compare_provider_costs(self, request: LLMRequest) -> Dict[str, Any]:
        """
        Compare costs across all available providers for a given request.
        
        Args:
            request: LLM request to estimate costs for
            
        Returns:
            Cost comparison across providers
        """
        cost_comparison = {
            "request_id": request.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers": {},
            "recommendations": {}
        }
        
        provider_costs = []
        
        for provider_type, provider in self.providers.items():
            if not self._provider_health.get(provider_type, False):
                continue
            
            try:
                # Format request for provider
                formatted_request = prompt_formatter.format_request_for_provider(request, provider_type)
                
                # Estimate tokens
                prompt_text = formatted_request.prompt
                if formatted_request.system_prompt:
                    prompt_text = f"{formatted_request.system_prompt}\n{prompt_text}"
                
                estimated_prompt_tokens = len(prompt_text.split()) * 1.3
                estimated_completion_tokens = min(request.max_tokens or 2000, estimated_prompt_tokens * 0.5)
                
                # Get cost estimate
                estimated_cost = provider.estimate_cost(
                    int(estimated_prompt_tokens),
                    int(estimated_completion_tokens),
                    request.model or provider.model
                )
                
                # Get model info
                model_info = provider.get_model_info(request.model or provider.model)
                
                provider_data = {
                    "provider": provider_type.value,
                    "model": request.model or provider.model,
                    "estimated_cost": round(estimated_cost, 6),
                    "estimated_prompt_tokens": int(estimated_prompt_tokens),
                    "estimated_completion_tokens": int(estimated_completion_tokens),
                    "estimated_total_tokens": int(estimated_prompt_tokens + estimated_completion_tokens),
                    "pricing": model_info.get("pricing", {}),
                    "performance_score": self._provider_performance.get(provider_type, 0.5),
                    "health_status": "healthy" if self._provider_health.get(provider_type, False) else "unhealthy"
                }
                
                cost_comparison["providers"][provider_type.value] = provider_data
                provider_costs.append((provider_type, estimated_cost, provider_data))
                
            except Exception as e:
                logger.warning(f"Failed to estimate cost for {provider_type.value}: {str(e)}")
                cost_comparison["providers"][provider_type.value] = {
                    "provider": provider_type.value,
                    "error": str(e),
                    "health_status": "error"
                }
        
        # Generate recommendations
        if provider_costs:
            # Sort by cost (lowest first)
            provider_costs.sort(key=lambda x: x[1])
            
            cheapest_provider, cheapest_cost, cheapest_data = provider_costs[0]
            
            cost_comparison["recommendations"] = {
                "cheapest_provider": cheapest_provider.value,
                "cheapest_cost": round(cheapest_cost, 6),
                "cost_savings": {},
                "performance_vs_cost": []
            }
            
            # Calculate savings compared to other providers
            for provider_type, cost, data in provider_costs[1:]:
                savings = cost - cheapest_cost
                savings_percentage = (savings / cost) * 100 if cost > 0 else 0
                
                cost_comparison["recommendations"]["cost_savings"][provider_type.value] = {
                    "absolute_savings": round(savings, 6),
                    "percentage_savings": round(savings_percentage, 2)
                }
            
            # Performance vs cost analysis
            for provider_type, cost, data in provider_costs:
                performance_score = data["performance_score"]
                cost_performance_ratio = performance_score / cost if cost > 0 else 0
                
                cost_comparison["recommendations"]["performance_vs_cost"].append({
                    "provider": provider_type.value,
                    "cost": round(cost, 6),
                    "performance_score": round(performance_score, 3),
                    "cost_performance_ratio": round(cost_performance_ratio, 2)
                })
            
            # Sort by cost-performance ratio (higher is better)
            cost_comparison["recommendations"]["performance_vs_cost"].sort(
                key=lambda x: x["cost_performance_ratio"], reverse=True
            )
            
            best_value = cost_comparison["recommendations"]["performance_vs_cost"][0]
            cost_comparison["recommendations"]["best_value_provider"] = best_value["provider"]
        
        return cost_comparison
    
    def get_cost_optimization_recommendations(self) -> Dict[str, Any]:
        """
        Get cost optimization recommendations based on usage patterns.
        
        Returns:
            Cost optimization recommendations
        """
        recommendations = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider_recommendations": [],
            "usage_optimization": [],
            "model_recommendations": [],
            "estimated_savings": 0.0
        }
        
        # Get usage statistics
        usage_stats = self.cost_tracker.get_usage_statistics()
        
        # Provider-level recommendations
        total_cost_by_provider = {}
        total_requests_by_provider = {}
        
        for provider_type, provider in self.providers.items():
            provider_cost = provider.total_cost
            provider_requests = provider.request_count
            
            total_cost_by_provider[provider_type.value] = provider_cost
            total_requests_by_provider[provider_type.value] = provider_requests
            
            # Check if provider is cost-effective
            if provider_requests > 0:
                avg_cost_per_request = provider_cost / provider_requests
                performance_score = self._provider_performance.get(provider_type, 0.5)
                
                if avg_cost_per_request > 0.01 and performance_score < 0.7:  # High cost, low performance
                    recommendations["provider_recommendations"].append({
                        "type": "switch_provider",
                        "current_provider": provider_type.value,
                        "issue": "High cost with low performance",
                        "avg_cost_per_request": round(avg_cost_per_request, 4),
                        "performance_score": round(performance_score, 3),
                        "recommendation": "Consider switching to a more cost-effective provider"
                    })
        
        # Usage pattern optimization
        if usage_stats.get("total_requests", 0) > 100:
            avg_tokens_per_request = usage_stats.get("total_tokens", 0) / usage_stats.get("total_requests", 1)
            
            if avg_tokens_per_request > 3000:
                recommendations["usage_optimization"].append({
                    "type": "reduce_token_usage",
                    "current_avg_tokens": int(avg_tokens_per_request),
                    "recommendation": "Consider reducing prompt length or max_tokens to lower costs",
                    "potential_savings_percentage": 20
                })
            
            # Check for high-frequency, low-complexity requests
            if usage_stats.get("total_requests", 0) > 1000:
                recommendations["usage_optimization"].append({
                    "type": "batch_processing",
                    "recommendation": "Consider batching similar requests to reduce API overhead",
                    "potential_savings_percentage": 10
                })
        
        # Model recommendations
        for provider_type, provider in self.providers.items():
            if provider.request_count > 50:
                # Suggest cheaper models for simple tasks
                supported_models = provider.supported_models
                current_model = provider.model
                
                # Check if using expensive models for potentially simple tasks
                current_model_lower = (current_model or "").lower()
                if "gpt-4" in current_model_lower or "gemini-1.5-pro" in current_model_lower:
                    recommendations["model_recommendations"].append({
                        "type": "model_downgrade",
                        "provider": provider_type.value,
                        "current_model": current_model,
                        "recommendation": "Consider using cheaper models for simple tasks",
                        "suggested_models": [
                            model for model in supported_models 
                            if "3.5" in model or "flash" in (model or "").lower()
                        ][:3],
                        "potential_savings_percentage": 50
                    })
        
        # Calculate estimated savings
        total_cost = sum(total_cost_by_provider.values())
        if total_cost > 0:
            # Estimate potential savings from all recommendations
            potential_savings = 0
            
            for rec in recommendations["usage_optimization"]:
                potential_savings += total_cost * (rec.get("potential_savings_percentage", 0) / 100)
            
            for rec in recommendations["model_recommendations"]:
                provider_cost = total_cost_by_provider.get(rec["provider"], 0)
                potential_savings += provider_cost * (rec.get("potential_savings_percentage", 0) / 100)
            
            recommendations["estimated_savings"] = round(potential_savings, 4)
        
        return recommendations
    
    def set_usage_limits(self, limits: Dict[str, Any]) -> None:
        """
        Set usage limits and budget controls.
        
        Args:
            limits: Usage limits configuration dictionary
        """
        usage_limits = UsageLimits(
            daily_token_limit=limits.get("daily_token_limit"),
            monthly_token_limit=limits.get("monthly_token_limit"),
            daily_budget_limit=limits.get("daily_budget_limit"),
            monthly_budget_limit=limits.get("monthly_budget_limit"),
            per_request_token_limit=limits.get("per_request_token_limit"),
            per_agent_daily_limit=limits.get("per_agent_daily_limit"),
            cost_per_token_threshold=limits.get("cost_per_token_threshold")
        )
        self.usage_optimizer.set_usage_limits(usage_limits)
        logger.info("Usage limits updated")
    
    def set_optimization_strategy(self, strategy: str) -> None:
        """
        Set optimization strategy.
        
        Args:
            strategy: Optimization strategy ("aggressive", "balanced", "conservative")
        """
        try:
            optimization_strategy = OptimizationStrategy(strategy)
            self.usage_optimizer.strategy = optimization_strategy
            logger.info(f"Optimization strategy set to {strategy}")
        except ValueError:
            logger.error(f"Invalid optimization strategy: {strategy}")
            raise ValueError(f"Invalid optimization strategy. Must be one of: {[s.value for s in OptimizationStrategy]}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization statistics and performance metrics.
        
        Returns:
            Optimization statistics dictionary
        """
        return self.usage_optimizer.get_optimization_stats()
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations based on usage patterns.
        
        Returns:
            List of optimization recommendations
        """
        return self.usage_optimizer.get_optimization_recommendations()
    
    async def clear_response_cache(self, agent_name: Optional[str] = None) -> int:
        """
        Clear response cache entries.
        
        Args:
            agent_name: Clear only entries for specific agent (optional)
            
        Returns:
            Number of entries cleared
        """
        return await self.usage_optimizer.clear_cache(agent_name)
    
    def add_optimization_rule(self, rule_config: Dict[str, Any]) -> None:
        """
        Add a custom optimization rule.
        
        Args:
            rule_config: Rule configuration dictionary
        """
        from .usage_optimizer import OptimizationRule
        
        rule = OptimizationRule(
            name=rule_config["name"],
            pattern=rule_config["pattern"],
            replacement=rule_config["replacement"],
            token_savings=rule_config.get("token_savings", 1),
            quality_impact=rule_config.get("quality_impact", 0.0),
            enabled=rule_config.get("enabled", True)
        )
        
        self.usage_optimizer.add_optimization_rule(rule)
        logger.info(f"Added optimization rule: {rule.name}")
    
    def remove_optimization_rule(self, rule_name: str) -> bool:
        """
        Remove an optimization rule by name.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if removed, False if not found
        """
        return self.usage_optimizer.remove_optimization_rule(rule_name)
    
    async def optimize_provider_selection(self, request: LLMRequest) -> LLMProvider:
        """
        Optimize provider selection for a specific request.
        
        Args:
            request: LLM request
            
        Returns:
            Optimal provider for the request
        """
        # Get cost comparison
        cost_comparison = await self.compare_provider_costs(request)
        
        # Extract available providers with their metrics
        available_providers = []
        for provider_name, data in cost_comparison["providers"].items():
            if data.get("health_status") == "healthy":
                provider_type = LLMProvider(provider_name)
                available_providers.append({
                    "provider": provider_type,
                    "cost": data["estimated_cost"],
                    "performance": data["performance_score"],
                    "cost_performance_ratio": data["performance_score"] / data["estimated_cost"] if data["estimated_cost"] > 0 else 0
                })
        
        if not available_providers:
            # Fallback to first available provider
            return list(self.providers.keys())[0] if self.providers else LLMProvider.OPENAI
        
        # Apply optimization strategy
        if self.load_balancing_strategy == LoadBalancingStrategy.COST_OPTIMIZED:
            # Choose cheapest provider
            optimal = min(available_providers, key=lambda x: x["cost"])
        elif self.load_balancing_strategy == LoadBalancingStrategy.PERFORMANCE_OPTIMIZED:
            # Choose highest performance provider
            optimal = max(available_providers, key=lambda x: x["performance"])
        else:
            # Choose best cost-performance ratio
            optimal = max(available_providers, key=lambda x: x["cost_performance_ratio"])
        
        logger.info(
            f"Optimized provider selection: {optimal['provider'].value} "
            f"(cost: ${optimal['cost']:.6f}, performance: {optimal['performance']:.3f})"
        )
        
        return optimal["provider"]
    
    async def test_all_providers(self) -> Dict[str, Any]:
        """
        Test all providers with comprehensive diagnostics.
        
        Returns:
            Test results for all providers
        """
        test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers": {}
        }
        
        for provider_type, provider in self.providers.items():
            try:
                if hasattr(provider, 'test_connection'):
                    provider_test = await provider.test_connection()
                else:
                    provider_test = await provider.health_check()
                
                test_results["providers"][provider_type.value] = provider_test
                
            except Exception as e:
                test_results["providers"][provider_type.value] = {
                    "overall_status": "error",
                    "error": str(e)
                }
        
        # Overall system status
        all_healthy = all(
            result.get("overall_status") == "healthy" 
            for result in test_results["providers"].values()
        )
        
        test_results["system_status"] = "healthy" if all_healthy else "degraded"
        
        return test_results
    
    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """
        Set load balancing strategy.
        
        Args:
            strategy: Load balancing strategy
        """
        self.load_balancing_strategy = strategy
        logger.info(f"Load balancing strategy set to: {strategy.value}")
    
    def set_failover_strategy(self, strategy: FailoverStrategy) -> None:
        """
        Set failover strategy.
        
        Args:
            strategy: Failover strategy
        """
        self.failover_strategy = strategy
        logger.info(f"Failover strategy set to: {strategy.value}")
    
    def add_provider(self, provider_type: LLMProvider, provider: LLMProviderInterface) -> None:
        """
        Add a new provider to the manager.
        
        Args:
            provider_type: Provider type
            provider: Provider instance
        """
        self.providers[provider_type] = provider
        self._provider_health[provider_type] = True
        self._provider_performance[provider_type] = 1.0
        logger.info(f"Added provider: {provider_type.value}")
    
    def remove_provider(self, provider_type: LLMProvider) -> None:
        """
        Remove a provider from the manager.
        
        Args:
            provider_type: Provider type to remove
        """
        if provider_type in self.providers:
            del self.providers[provider_type]
            self._provider_health.pop(provider_type, None)
            self._provider_performance.pop(provider_type, None)
            logger.info(f"Removed provider: {provider_type.value}")
    
    async def shutdown(self) -> None:
        """Shutdown the LLM manager and cleanup resources."""
        logger.info("Shutting down LLM manager")
        
        # Close provider connections if needed
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except Exception as e:
                    logger.warning(f"Error closing provider: {str(e)}")
        
        # Export final cost data if configured
        if self.config.get("export_cost_data_on_shutdown", False):
            try:
                cost_data = self.cost_tracker.export_cost_data("json")
                # Save to file or send to monitoring system
                logger.info("Exported final cost data")
            except Exception as e:
                logger.warning(f"Failed to export cost data: {str(e)}")
        
        logger.info("LLM manager shutdown complete")