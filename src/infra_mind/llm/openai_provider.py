"""
OpenAI LLM Provider for Infra Mind.

Real OpenAI API integration with comprehensive error handling,
token usage tracking, and cost monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from .interface import (
    LLMProviderInterface, 
    LLMProvider, 
    LLMRequest, 
    LLMResponse, 
    TokenUsage,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMQuotaExceededError,
    LLMModelNotFoundError,
    LLMTimeoutError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProviderInterface):
    """
    OpenAI LLM provider with real API integration.
    
    Features:
    - Real OpenAI API calls
    - Token usage tracking and cost monitoring
    - Comprehensive error handling with retries
    - Response validation and quality checks
    - Rate limiting and quota management
    """
    
    # OpenAI model pricing (per 1K tokens) - Updated as of 2024
    MODEL_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
        "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    }
    
    # Model context limits
    MODEL_CONTEXT_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-4-turbo-preview": 128000,
        "gpt-4-1106-preview": 128000,
        "gpt-4-0125-preview": 128000,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-1106": 16385,
        "gpt-3.5-turbo-0125": 16385,
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Default model to use
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=kwargs.get("timeout", 60.0),
            max_retries=kwargs.get("max_retries", 3)
        )
        
        # Configuration
        self.default_temperature = kwargs.get("temperature", 0.7)
        self.default_max_tokens = kwargs.get("max_tokens", 2000)
        self.retry_delays = [1, 2, 4, 8]  # Exponential backoff
        
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    @property
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        return LLMProvider.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        return list(self.MODEL_PRICING.keys())
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from OpenAI API.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metadata
            
        Raises:
            LLMError: If request fails after retries
        """
        start_time = time.time()
        
        try:
            # Validate model
            model = request.model or self.model
            if model not in self.supported_models:
                raise LLMModelNotFoundError(
                    f"Model {model} not supported by OpenAI provider",
                    self.provider_name,
                    model
                )
            
            # Prepare messages
            messages = []
            
            # Add system prompt if provided
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            # Add main prompt
            messages.append({
                "role": "user", 
                "content": request.prompt
            })
            
            # Make API call with retries
            completion = await self._make_api_call_with_retries(
                model=model,
                messages=messages,
                temperature=request.temperature or self.default_temperature,
                max_tokens=min(
                    request.max_tokens or self.default_max_tokens,
                    self.MODEL_CONTEXT_LIMITS.get(model, 4096)
                ),
                request_id=request.request_id
            )
            
            # Extract response data
            response_content = completion.choices[0].message.content or ""
            usage = completion.usage
            
            # Calculate token usage and cost
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                estimated_cost=self.estimate_cost(
                    usage.prompt_tokens if usage else 0,
                    usage.completion_tokens if usage else 0,
                    model
                ),
                model=model,
                provider=self.provider_name
            )
            
            # Update usage statistics
            self._update_usage_stats(token_usage)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Create response
            response = LLMResponse(
                content=response_content,
                model=model,
                provider=self.provider_name,
                token_usage=token_usage,
                response_time=response_time,
                request_id=request.request_id,
                metadata={
                    "finish_reason": completion.choices[0].finish_reason,
                    "agent_name": request.agent_name,
                    "context": request.context
                }
            )
            
            logger.info(
                f"OpenAI API call successful - Model: {model}, "
                f"Tokens: {token_usage.total_tokens}, "
                f"Cost: ${token_usage.estimated_cost:.4f}, "
                f"Time: {response_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"OpenAI API call failed after {response_time:.2f}s: {str(e)}"
            )
            
            # Convert to appropriate LLM error
            error_str = str(e) if e is not None else ""
            if "authentication" in error_str.lower() or "api_key" in error_str.lower():
                raise LLMAuthenticationError(
                    f"OpenAI authentication failed: {str(e)}",
                    self.provider_name
                )
            elif "rate_limit" in error_str.lower():
                raise LLMRateLimitError(
                    f"OpenAI rate limit exceeded: {str(e)}",
                    self.provider_name
                )
            elif "quota" in error_str.lower() or "billing" in error_str.lower():
                raise LLMQuotaExceededError(
                    f"OpenAI quota exceeded: {str(e)}",
                    self.provider_name
                )
            elif "timeout" in error_str.lower():
                raise LLMTimeoutError(
                    f"OpenAI request timeout: {str(e)}",
                    self.provider_name
                )
            else:
                raise LLMError(
                    f"OpenAI API error: {str(e)}",
                    self.provider_name
                )
    
    async def _make_api_call_with_retries(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> ChatCompletion:
        """
        Make OpenAI API call with exponential backoff retries.
        
        Args:
            model: Model name
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            request_id: Request ID for tracking
            
        Returns:
            ChatCompletion response
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(len(self.retry_delays) + 1):
            try:
                logger.debug(f"OpenAI API call attempt {attempt + 1} for request {request_id}")
                
                completion = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    user=request_id  # For tracking
                )
                
                return completion
                
            except Exception as e:
                last_exception = e
                
                # Don't retry on authentication errors
                error_str = str(e) if e is not None else ""
                if "authentication" in error_str.lower() or "api_key" in error_str.lower():
                    raise e
                
                # Don't retry on quota exceeded
                if "quota" in error_str.lower() or "billing" in error_str.lower():
                    raise e
                
                # For rate limits and other errors, retry with backoff
                if attempt < len(self.retry_delays):
                    delay = self.retry_delays[attempt]
                    logger.warning(
                        f"OpenAI API call failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"OpenAI API call failed after all retries: {str(e)}")
        
        # If we get here, all retries failed
        raise last_exception
    
    async def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a minimal API call to test the key
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI API key validation failed: {str(e)}")
            return False
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        if model not in self.MODEL_PRICING:
            # Use GPT-4 pricing as default for unknown models
            pricing = self.MODEL_PRICING["gpt-4"]
        else:
            pricing = self.MODEL_PRICING[model]
        
        # Calculate cost (pricing is per 1K tokens)
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Model information dictionary
        """
        if model not in self.supported_models:
            return {"error": f"Model {model} not supported"}
        
        pricing = self.MODEL_PRICING.get(model, {})
        context_limit = self.MODEL_CONTEXT_LIMITS.get(model, 0)
        
        return {
            "name": model,
            "provider": self.provider_name.value,
            "context_limit": context_limit,
            "pricing": {
                "input_per_1k_tokens": pricing.get("input", 0),
                "output_per_1k_tokens": pricing.get("output", 0),
                "currency": "USD"
            },
            "capabilities": [
                "text_generation",
                "conversation",
                "code_generation",
                "analysis"
            ]
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenAI API.
        
        Returns:
            List of model information dictionaries
        """
        try:
            models = await self.client.models.list()
            available_models = []
            
            for model in models.data:
                if model.id in self.supported_models:
                    model_info = self.get_model_info(model.id)
                    model_info.update({
                        "created": model.created,
                        "owned_by": model.owned_by
                    })
                    available_models.append(model_info)
            
            return available_models
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {str(e)}")
            return [self.get_model_info(model) for model in self.supported_models]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this provider instance.
        
        Returns:
            Usage statistics dictionary
        """
        return {
            "provider": self.provider_name.value,
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost, 4),
            "average_tokens_per_request": (
                round(self.total_tokens_used / self.request_count, 2) 
                if self.request_count > 0 else 0
            ),
            "average_cost_per_request": (
                round(self.total_cost / self.request_count, 4) 
                if self.request_count > 0 else 0
            )
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to OpenAI API with detailed diagnostics.
        
        Returns:
            Connection test results
        """
        test_results = {
            "provider": self.provider_name.value,
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Test 1: API key validation
        try:
            api_key_valid = await self.validate_api_key()
            test_results["tests"]["api_key_validation"] = {
                "status": "pass" if api_key_valid else "fail",
                "message": "API key is valid" if api_key_valid else "API key is invalid"
            }
        except Exception as e:
            test_results["tests"]["api_key_validation"] = {
                "status": "error",
                "message": f"API key validation error: {str(e)}"
            }
        
        # Test 2: Model availability
        try:
            models = await self.get_available_models()
            test_results["tests"]["model_availability"] = {
                "status": "pass",
                "message": f"Found {len(models)} available models",
                "models": [m["name"] for m in models]
            }
        except Exception as e:
            test_results["tests"]["model_availability"] = {
                "status": "error",
                "message": f"Model availability check failed: {str(e)}"
            }
        
        # Test 3: Simple generation test
        try:
            test_request = LLMRequest(
                prompt="Say 'Hello, World!' in exactly those words.",
                model=self.model,
                temperature=0.0,
                max_tokens=10
            )
            
            response = await self.generate_response(test_request)
            
            test_results["tests"]["generation_test"] = {
                "status": "pass",
                "message": "Generation test successful",
                "response_length": len(response.content),
                "tokens_used": response.token_usage.total_tokens,
                "cost": response.token_usage.estimated_cost,
                "response_time": response.response_time
            }
        except Exception as e:
            test_results["tests"]["generation_test"] = {
                "status": "error",
                "message": f"Generation test failed: {str(e)}"
            }
        
        # Overall status
        all_tests_passed = all(
            test.get("status") == "pass" 
            for test in test_results["tests"].values()
        )
        
        test_results["overall_status"] = "healthy" if all_tests_passed else "unhealthy"
        
        return test_results