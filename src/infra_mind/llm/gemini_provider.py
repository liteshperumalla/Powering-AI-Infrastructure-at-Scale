"""
Google Gemini LLM Provider for Infra Mind.

Real Google Gemini API integration with comprehensive error handling,
token usage tracking, and cost monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from google.api_core import exceptions as google_exceptions

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


class GeminiProvider(LLMProviderInterface):
    """
    Google Gemini LLM provider with real API integration.
    
    Features:
    - Real Google Gemini API calls
    - Token usage tracking and cost monitoring
    - Comprehensive error handling with retries
    - Response validation and quality checks
    - Rate limiting and quota management
    """
    
    # Gemini model pricing (per 1M tokens) - Updated as of 2024
    MODEL_PRICING = {
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        "gemini-1.5-pro-128k": {"input": 3.50, "output": 10.50},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},
        "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
        "gemini-pro": {"input": 0.50, "output": 1.50},  # Legacy name
    }
    
    # Model context limits (tokens)
    MODEL_CONTEXT_LIMITS = {
        "gemini-1.5-pro": 2097152,  # 2M tokens
        "gemini-1.5-pro-128k": 131072,  # 128K tokens
        "gemini-1.5-flash": 1048576,  # 1M tokens
        "gemini-1.5-flash-8b": 1048576,  # 1M tokens
        "gemini-1.0-pro": 32768,  # 32K tokens
        "gemini-pro": 32768,  # 32K tokens
    }
    
    # Model aliases for backward compatibility
    MODEL_ALIASES = {
        "gemini-2.5-pro": "gemini-1.5-pro",  # Map to latest available
        "gemini-pro": "gemini-1.0-pro"
    }
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", **kwargs):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key
            model: Default model to use
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Resolve model alias
        self.resolved_model = self.MODEL_ALIASES.get(model, model)
        
        # Configuration
        self.default_temperature = kwargs.get("temperature", 0.7)
        self.default_max_tokens = kwargs.get("max_tokens", 2000)
        self.retry_delays = [1, 2, 4, 8]  # Exponential backoff
        self.timeout = kwargs.get("timeout", 60.0)
        
        # Generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.default_temperature,
            max_output_tokens=self.default_max_tokens,
            top_p=kwargs.get("top_p", 0.95),
            top_k=kwargs.get("top_k", 64),
        )
        
        # Safety settings (allow most content for business use)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
        
        logger.info(f"Initialized Gemini provider with model: {self.resolved_model}")
    
    @property
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        return LLMProvider.GEMINI
    
    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        return list(self.MODEL_PRICING.keys()) + list(self.MODEL_ALIASES.keys())
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from Gemini API.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metadata
            
        Raises:
            LLMError: If request fails after retries
        """
        start_time = time.time()
        
        try:
            # Resolve model name
            model_name = request.model or self.model
            resolved_model = self.MODEL_ALIASES.get(model_name, model_name)
            
            if resolved_model not in self.MODEL_PRICING:
                raise LLMModelNotFoundError(
                    f"Model {model_name} not supported by Gemini provider",
                    self.provider_name,
                    model_name
                )
            
            # Create generation config for this request
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature or self.default_temperature,
                max_output_tokens=min(
                    request.max_tokens or self.default_max_tokens,
                    self.MODEL_CONTEXT_LIMITS.get(resolved_model, 32768)
                ),
                top_p=0.95,
                top_k=64,
            )
            
            # Prepare prompt
            full_prompt = self._prepare_prompt(request)
            
            # Make API call with retries
            response = await self._make_api_call_with_retries(
                model_name=resolved_model,
                prompt=full_prompt,
                generation_config=generation_config,
                request_id=request.request_id
            )
            
            # Extract response content
            response_content = response.text if response.text else ""
            
            # Estimate token usage (Gemini doesn't provide exact counts in all cases)
            estimated_prompt_tokens = self._estimate_tokens(full_prompt)
            estimated_completion_tokens = self._estimate_tokens(response_content)
            
            # Get actual usage if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                actual_prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', estimated_prompt_tokens)
                actual_completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', estimated_completion_tokens)
            else:
                actual_prompt_tokens = estimated_prompt_tokens
                actual_completion_tokens = estimated_completion_tokens
            
            # Calculate token usage and cost
            token_usage = TokenUsage(
                prompt_tokens=actual_prompt_tokens,
                completion_tokens=actual_completion_tokens,
                total_tokens=actual_prompt_tokens + actual_completion_tokens,
                estimated_cost=self.estimate_cost(
                    actual_prompt_tokens,
                    actual_completion_tokens,
                    resolved_model
                ),
                model=resolved_model,
                provider=self.provider_name
            )
            
            # Update usage statistics
            self._update_usage_stats(token_usage)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract finish reason
            finish_reason = "stop"  # Default
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason).lower()
            
            # Create response
            llm_response = LLMResponse(
                content=response_content,
                model=resolved_model,
                provider=self.provider_name,
                token_usage=token_usage,
                response_time=response_time,
                request_id=request.request_id,
                metadata={
                    "finish_reason": finish_reason,
                    "agent_name": request.agent_name,
                    "context": request.context,
                    "original_model": model_name,
                    "safety_ratings": self._extract_safety_ratings(response)
                }
            )
            
            logger.info(
                f"Gemini API call successful - Model: {resolved_model}, "
                f"Tokens: {token_usage.total_tokens}, "
                f"Cost: ${token_usage.estimated_cost:.4f}, "
                f"Time: {response_time:.2f}s"
            )
            
            return llm_response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"Gemini API call failed after {response_time:.2f}s: {str(e)}"
            )
            
            # Convert to appropriate LLM error
            if isinstance(e, google_exceptions.Unauthenticated):
                raise LLMAuthenticationError(
                    f"Gemini authentication failed: {str(e)}",
                    self.provider_name
                )
            elif isinstance(e, google_exceptions.ResourceExhausted):
                if "quota" in str(e).lower():
                    raise LLMQuotaExceededError(
                        f"Gemini quota exceeded: {str(e)}",
                        self.provider_name
                    )
                else:
                    raise LLMRateLimitError(
                        f"Gemini rate limit exceeded: {str(e)}",
                        self.provider_name
                    )
            elif isinstance(e, google_exceptions.NotFound):
                raise LLMModelNotFoundError(
                    f"Gemini model not found: {str(e)}",
                    self.provider_name,
                    request.model or self.model
                )
            elif isinstance(e, google_exceptions.DeadlineExceeded):
                raise LLMTimeoutError(
                    f"Gemini request timeout: {str(e)}",
                    self.provider_name
                )
            else:
                raise LLMError(
                    f"Gemini API error: {str(e)}",
                    self.provider_name
                )
    
    def _prepare_prompt(self, request: LLMRequest) -> str:
        """
        Prepare prompt for Gemini API.
        
        Args:
            request: LLM request
            
        Returns:
            Formatted prompt string
        """
        parts = []
        
        # Add system prompt if provided
        if request.system_prompt:
            parts.append(f"System: {request.system_prompt}")
        
        # Add main prompt
        parts.append(f"User: {request.prompt}")
        
        return "\n\n".join(parts)
    
    async def _make_api_call_with_retries(
        self, 
        model_name: str, 
        prompt: str, 
        generation_config: genai.types.GenerationConfig,
        request_id: str
    ) -> GenerateContentResponse:
        """
        Make Gemini API call with exponential backoff retries.
        
        Args:
            model_name: Model name
            prompt: Formatted prompt
            generation_config: Generation configuration
            request_id: Request ID for tracking
            
        Returns:
            GenerateContentResponse
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(len(self.retry_delays) + 1):
            try:
                logger.debug(f"Gemini API call attempt {attempt + 1} for request {request_id}")
                
                # Create model instance
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
                
                # Generate content
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt
                )
                
                # Check if response was blocked
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = str(candidate.finish_reason)
                        if finish_reason in ['SAFETY', 'RECITATION', 'OTHER']:
                            raise LLMError(
                                f"Response blocked due to: {finish_reason}",
                                self.provider_name
                            )
                
                return response
                
            except Exception as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if isinstance(e, google_exceptions.Unauthenticated):
                    raise e
                
                # Don't retry on quota exceeded
                if isinstance(e, google_exceptions.ResourceExhausted) and "quota" in str(e).lower():
                    raise e
                
                # For rate limits and other errors, retry with backoff
                if attempt < len(self.retry_delays):
                    delay = self.retry_delays[attempt]
                    logger.warning(
                        f"Gemini API call failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Gemini API call failed after all retries: {str(e)}")
        
        # If we get here, all retries failed
        raise last_exception
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    def _extract_safety_ratings(self, response: GenerateContentResponse) -> List[Dict[str, Any]]:
        """
        Extract safety ratings from response.
        
        Args:
            response: Gemini API response
            
        Returns:
            List of safety rating dictionaries
        """
        safety_ratings = []
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'safety_ratings'):
                for rating in candidate.safety_ratings:
                    safety_ratings.append({
                        "category": str(rating.category),
                        "probability": str(rating.probability)
                    })
        
        return safety_ratings
    
    async def validate_api_key(self) -> bool:
        """
        Validate Gemini API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a minimal API call to test the key
            model = genai.GenerativeModel(model_name="gemini-1.0-pro")
            response = await asyncio.to_thread(
                model.generate_content,
                "Hello",
                generation_config=genai.types.GenerationConfig(max_output_tokens=1)
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini API key validation failed: {str(e)}")
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
            # Use gemini-1.5-pro pricing as default for unknown models
            pricing = self.MODEL_PRICING["gemini-1.5-pro"]
        else:
            pricing = self.MODEL_PRICING[model]
        
        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Model information dictionary
        """
        resolved_model = self.MODEL_ALIASES.get(model, model)
        
        if resolved_model not in self.MODEL_PRICING:
            return {"error": f"Model {model} not supported"}
        
        pricing = self.MODEL_PRICING[resolved_model]
        context_limit = self.MODEL_CONTEXT_LIMITS.get(resolved_model, 0)
        
        return {
            "name": model,
            "resolved_name": resolved_model,
            "provider": self.provider_name.value,
            "context_limit": context_limit,
            "pricing": {
                "input_per_1m_tokens": pricing["input"],
                "output_per_1m_tokens": pricing["output"],
                "currency": "USD"
            },
            "capabilities": [
                "text_generation",
                "conversation",
                "code_generation",
                "analysis",
                "multimodal"  # Gemini supports images
            ]
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from Gemini API.
        
        Returns:
            List of model information dictionaries
        """
        try:
            # Get models from API
            models = genai.list_models()
            available_models = []
            
            for model in models:
                model_name = model.name.replace('models/', '')
                if model_name in self.supported_models:
                    model_info = self.get_model_info(model_name)
                    model_info.update({
                        "display_name": getattr(model, 'display_name', model_name),
                        "description": getattr(model, 'description', ''),
                        "supported_generation_methods": getattr(model, 'supported_generation_methods', [])
                    })
                    available_models.append(model_info)
            
            return available_models
            
        except Exception as e:
            logger.error(f"Failed to fetch Gemini models: {str(e)}")
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
        Test connection to Gemini API with detailed diagnostics.
        
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
                model=self.resolved_model,
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