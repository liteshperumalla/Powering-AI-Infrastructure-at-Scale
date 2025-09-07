"""
Prompt Formatter for consistent prompt formatting across LLM providers.

Ensures consistent prompt structure and formatting regardless of the underlying
LLM provider (OpenAI, Gemini, Anthropic, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .interface import LLMProvider, LLMRequest

logger = logging.getLogger(__name__)


class PromptRole(str, Enum):
    """Standard prompt roles across providers."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class PromptMessage:
    """Standardized prompt message structure."""
    role: PromptRole
    content: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PromptFormatter:
    """
    Universal prompt formatter for consistent formatting across LLM providers.
    
    Features:
    - Provider-specific prompt formatting
    - Consistent message structure
    - Template management
    - Context injection
    - Token optimization
    """
    
    # Provider-specific formatting templates
    PROVIDER_TEMPLATES = {
        LLMProvider.OPENAI: {
            "system_prefix": "",
            "user_prefix": "",
            "assistant_prefix": "",
            "message_separator": "",
            "supports_system_role": True,
            "supports_message_format": True
        },
        LLMProvider.GEMINI: {
            "system_prefix": "System: ",
            "user_prefix": "User: ",
            "assistant_prefix": "Assistant: ",
            "message_separator": "\n\n",
            "supports_system_role": False,  # Gemini doesn't have explicit system role
            "supports_message_format": False
        },
        LLMProvider.ANTHROPIC: {
            "system_prefix": "",
            "user_prefix": "Human: ",
            "assistant_prefix": "Assistant: ",
            "message_separator": "\n\n",
            "supports_system_role": True,
            "supports_message_format": True
        }
    }
    
    def __init__(self):
        """Initialize prompt formatter."""
        self.templates = self.PROVIDER_TEMPLATES.copy()
        logger.debug("Prompt formatter initialized")
    
    def format_request_for_provider(
        self, 
        request: LLMRequest, 
        provider: LLMProvider
    ) -> LLMRequest:
        """
        Format LLM request for specific provider.
        
        Args:
            request: Original LLM request
            provider: Target LLM provider
            
        Returns:
            Formatted LLM request optimized for the provider
        """
        # Create a copy of the request
        formatted_request = LLMRequest(
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
        
        # Get provider template
        template = self.templates.get(provider, self.templates[LLMProvider.OPENAI])
        
        # Format based on provider capabilities
        if provider == LLMProvider.GEMINI:
            # Gemini needs special formatting
            formatted_request = self._format_for_gemini(formatted_request, template)
        elif provider == LLMProvider.ANTHROPIC:
            # Anthropic has specific formatting requirements
            formatted_request = self._format_for_anthropic(formatted_request, template)
        elif provider == LLMProvider.OPENAI:
            # OpenAI uses standard format (no changes needed)
            pass
        
        # Add provider-specific context
        provider_name = provider.value if hasattr(provider, 'value') else str(provider)
        formatted_request.context["formatted_for_provider"] = provider_name
        formatted_request.context["original_prompt"] = request.prompt
        formatted_request.context["original_system_prompt"] = request.system_prompt
        
        logger.debug(f"Formatted request for {provider_name} provider")
        return formatted_request
    
    def _format_for_gemini(self, request: LLMRequest, template: Dict[str, Any]) -> LLMRequest:
        """
        Format request specifically for Gemini provider.
        
        Args:
            request: LLM request
            template: Provider template
            
        Returns:
            Formatted request for Gemini
        """
        parts = []
        
        # Add system prompt as part of user message (Gemini doesn't support system role)
        if request.system_prompt:
            parts.append(f"{template['system_prefix']}{request.system_prompt}")
        
        # Add main prompt
        parts.append(f"{template['user_prefix']}{request.prompt}")
        
        # Combine with separator
        formatted_prompt = template['message_separator'].join(parts)
        
        # Update request
        request.prompt = formatted_prompt
        request.system_prompt = None  # Clear system prompt as it's now part of main prompt
        
        return request
    
    def _format_for_anthropic(self, request: LLMRequest, template: Dict[str, Any]) -> LLMRequest:
        """
        Format request specifically for Anthropic provider.
        
        Args:
            request: LLM request
            template: Provider template
            
        Returns:
            Formatted request for Anthropic
        """
        # Anthropic prefers Human/Assistant format
        formatted_prompt = f"{template['user_prefix']}{request.prompt}"
        
        # Update request
        request.prompt = formatted_prompt
        
        return request
    
    def create_messages_format(
        self, 
        request: LLMRequest, 
        provider: LLMProvider
    ) -> List[Dict[str, str]]:
        """
        Create messages format for providers that support it.
        
        Args:
            request: LLM request
            provider: Target provider
            
        Returns:
            List of message dictionaries
        """
        template = self.templates.get(provider, self.templates[LLMProvider.OPENAI])
        messages = []
        
        # Add system message if supported and provided
        if template["supports_system_role"] and request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    def optimize_prompt_for_tokens(
        self, 
        request: LLMRequest, 
        provider: LLMProvider,
        max_tokens: Optional[int] = None
    ) -> LLMRequest:
        """
        Optimize prompt to fit within token limits.
        
        Args:
            request: LLM request
            provider: Target provider
            max_tokens: Maximum tokens allowed
            
        Returns:
            Optimized request
        """
        if not max_tokens:
            return request
        
        # Estimate current token usage (rough approximation)
        current_tokens = self._estimate_tokens(request.prompt)
        if request.system_prompt:
            current_tokens += self._estimate_tokens(request.system_prompt)
        
        # If within limits, return as-is
        if current_tokens <= max_tokens * 0.8:  # Leave 20% buffer for completion
            return request
        
        # Truncate prompt if necessary
        logger.warning(f"Prompt too long ({current_tokens} tokens), truncating for {provider.value}")
        
        # Calculate available tokens for prompt (leaving space for completion)
        available_tokens = int(max_tokens * 0.6)  # Use 60% for prompt, 40% for completion
        
        # Truncate main prompt first
        if current_tokens > available_tokens:
            # Simple truncation - in production, use more sophisticated methods
            target_chars = int(len(request.prompt) * (available_tokens / current_tokens))
            request.prompt = request.prompt[:target_chars] + "..."
        
        return request
    
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
    
    def add_context_to_prompt(
        self, 
        request: LLMRequest, 
        context: Dict[str, Any]
    ) -> LLMRequest:
        """
        Add contextual information to prompt.
        
        Args:
            request: LLM request
            context: Context to add
            
        Returns:
            Request with added context
        """
        context_parts = []
        
        # Add agent context
        if request.agent_name:
            context_parts.append(f"Agent: {request.agent_name}")
        
        # Add business context
        if context.get("business_context"):
            context_parts.append(f"Business Context: {context['business_context']}")
        
        # Add technical context
        if context.get("technical_context"):
            context_parts.append(f"Technical Context: {context['technical_context']}")
        
        # Add expected format
        if context.get("expected_format"):
            context_parts.append(f"Expected Format: {context['expected_format']}")
        
        # Prepend context to prompt if any context exists
        if context_parts:
            context_str = "\n".join(context_parts)
            request.prompt = f"{context_str}\n\n{request.prompt}"
        
        return request
    
    def create_agent_specific_prompt(
        self, 
        base_prompt: str,
        agent_name: str,
        agent_context: Dict[str, Any]
    ) -> str:
        """
        Create agent-specific prompt with role and context.
        
        Args:
            base_prompt: Base prompt text
            agent_name: Name of the agent
            agent_context: Agent-specific context
            
        Returns:
            Agent-specific formatted prompt
        """
        # Agent role definitions
        agent_roles = {
            "cto_agent": "You are a Chief Technology Officer (CTO) AI agent specializing in strategic technology decisions and infrastructure planning.",
            "cloud_engineer_agent": "You are a Cloud Engineer AI agent specializing in cloud infrastructure design, optimization, and best practices.",
            "research_agent": "You are a Research AI agent specializing in gathering and analyzing technical information and market intelligence.",
            "compliance_agent": "You are a Compliance AI agent specializing in regulatory requirements and security compliance frameworks.",
            "infrastructure_agent": "You are an Infrastructure AI agent specializing in system architecture and infrastructure management.",
            "mlops_agent": "You are an MLOps AI agent specializing in machine learning operations and AI infrastructure.",
            "simulation_agent": "You are a Simulation AI agent specializing in infrastructure modeling and scenario analysis."
        }
        
        # Get agent role
        role = agent_roles.get((agent_name or "").lower(), f"You are an AI agent named {agent_name or 'Assistant'}.")
        
        # Build prompt parts
        prompt_parts = [role]
        
        # Add agent-specific context
        if agent_context.get("expertise_areas"):
            expertise = ", ".join(agent_context["expertise_areas"])
            prompt_parts.append(f"Your areas of expertise include: {expertise}")
        
        if agent_context.get("response_style"):
            prompt_parts.append(f"Response style: {agent_context['response_style']}")
        
        if agent_context.get("constraints"):
            constraints = "\n".join(f"- {constraint}" for constraint in agent_context["constraints"])
            prompt_parts.append(f"Constraints:\n{constraints}")
        
        # Add base prompt
        prompt_parts.append(base_prompt)
        
        return "\n\n".join(prompt_parts)
    
    def get_provider_capabilities(self, provider: LLMProvider) -> Dict[str, Any]:
        """
        Get capabilities for a specific provider.
        
        Args:
            provider: LLM provider
            
        Returns:
            Provider capabilities dictionary
        """
        template = self.templates.get(provider, self.templates[LLMProvider.OPENAI])
        
        return {
            "provider": provider.value,
            "supports_system_role": template["supports_system_role"],
            "supports_message_format": template["supports_message_format"],
            "message_separator": template["message_separator"],
            "formatting_style": {
                "system_prefix": template["system_prefix"],
                "user_prefix": template["user_prefix"],
                "assistant_prefix": template["assistant_prefix"]
            }
        }
    
    def validate_prompt_for_provider(
        self, 
        request: LLMRequest, 
        provider: LLMProvider
    ) -> Dict[str, Any]:
        """
        Validate prompt compatibility with provider.
        
        Args:
            request: LLM request
            provider: Target provider
            
        Returns:
            Validation results
        """
        template = self.templates.get(provider, self.templates[LLMProvider.OPENAI])
        issues = []
        warnings = []
        
        # Check system prompt support
        if request.system_prompt and not template["supports_system_role"]:
            warnings.append(f"{provider.value} doesn't support system role - will be merged with user prompt")
        
        # Check prompt length
        estimated_tokens = self._estimate_tokens(request.prompt)
        if request.system_prompt:
            estimated_tokens += self._estimate_tokens(request.system_prompt)
        
        if estimated_tokens > 32000:  # Conservative limit
            issues.append(f"Prompt may be too long ({estimated_tokens} estimated tokens)")
        
        # Check for provider-specific issues
        if provider == LLMProvider.GEMINI:
            if "```" in request.prompt and request.prompt.count("```") % 2 != 0:
                issues.append("Unmatched code blocks may cause issues with Gemini")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "estimated_tokens": estimated_tokens,
            "provider": provider.value
        }


# Global prompt formatter instance
prompt_formatter = PromptFormatter()