"""
LLM Provider Interface for Infra Mind.

Defines the abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"


@dataclass
class TokenUsage:
    """Token usage information for LLM requests."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float = 0.0
    model: str = ""
    provider: LLMProvider = LLMProvider.OPENAI
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    provider: LLMProvider
    token_usage: TokenUsage
    response_time: float
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_valid(self) -> bool:
        """Check if response is valid."""
        return bool(self.content and self.content.strip())
    
    @property
    def cost(self) -> float:
        """Get estimated cost of the request."""
        return self.token_usage.estimated_cost


@dataclass
class LLMRequest:
    """Request to LLM provider."""
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    agent_name: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LLMProviderInterface(ABC):
    """
    Abstract interface for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across different providers.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        """
        Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Default model to use
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self._total_tokens_used = 0
        self._total_cost = 0.0
        self._request_count = 0
    
    @property
    @abstractmethod
    def provider_name(self) -> LLMProvider:
        """Get provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from LLM.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metadata
            
        Raises:
            LLMError: If request fails
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate API key with provider.
        
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Model information dictionary
        """
        pass
    
    @property
    def total_tokens_used(self) -> int:
        """Get total tokens used by this provider instance."""
        return self._total_tokens_used
    
    @property
    def total_cost(self) -> float:
        """Get total cost for this provider instance."""
        return self._total_cost
    
    @property
    def request_count(self) -> int:
        """Get total number of requests made."""
        return self._request_count
    
    def _update_usage_stats(self, token_usage: TokenUsage) -> None:
        """Update internal usage statistics."""
        self._total_tokens_used += token_usage.total_tokens
        self._total_cost += token_usage.estimated_cost
        self._request_count += 1
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the provider.
        
        Returns:
            Health status information
        """
        try:
            is_valid = await self.validate_api_key()
            return {
                "provider": self.provider_name.value,
                "status": "healthy" if is_valid else "unhealthy",
                "api_key_valid": is_valid,
                "model": self.model,
                "total_requests": self.request_count,
                "total_tokens": self.total_tokens_used,
                "total_cost": round(self.total_cost, 4)
            }
        except Exception as e:
            return {
                "provider": self.provider_name.value,
                "status": "error",
                "error": str(e),
                "api_key_valid": False
            }


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    
    def __init__(self, message: str, provider: LLMProvider, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.timestamp = datetime.now(timezone.utc)


class LLMAuthenticationError(LLMError):
    """Authentication error with LLM provider."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, provider: LLMProvider, retry_after: Optional[int] = None):
        super().__init__(message, provider)
        self.retry_after = retry_after


class LLMQuotaExceededError(LLMError):
    """Quota exceeded error."""
    pass


class LLMModelNotFoundError(LLMError):
    """Model not found error."""
    
    def __init__(self, message: str, provider: LLMProvider, model: str):
        super().__init__(message, provider)
        self.model = model


class LLMTimeoutError(LLMError):
    """Request timeout error."""
    pass


class LLMValidationError(LLMError):
    """Response validation error."""
    pass