"""
Token Budget Manager for LLM Prompts.

Manages token budgets, truncation strategies, and context window optimization
for different LLM models with varying context limits.
"""

import tiktoken
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TruncationStrategy(Enum):
    """Strategies for truncating content when exceeding token budget."""
    HEAD = "head"  # Keep start, truncate end
    TAIL = "tail"  # Keep end, truncate start
    MIDDLE = "middle"  # Keep start and end, truncate middle
    SMART = "smart"  # Intelligently preserve important content
    SUMMARIZE = "summarize"  # Use LLM to summarize content


@dataclass
class ModelConfig:
    """Configuration for LLM model token limits."""
    model_name: str
    context_window: int  # Total context window
    max_output_tokens: int  # Reserved for output
    system_prompt_budget: int  # Reserved for system prompt
    available_for_context: int  # Calculated available tokens


# Model configurations with actual limits
MODEL_CONFIGS = {
    # OpenAI GPT-4
    "gpt-4": ModelConfig(
        model_name="gpt-4",
        context_window=8192,
        max_output_tokens=2048,
        system_prompt_budget=1500,
        available_for_context=4644  # 8192 - 2048 - 1500
    ),
    "gpt-4-32k": ModelConfig(
        model_name="gpt-4-32k",
        context_window=32768,
        max_output_tokens=4096,
        system_prompt_budget=2000,
        available_for_context=26672
    ),
    "gpt-4-turbo": ModelConfig(
        model_name="gpt-4-turbo",
        context_window=128000,
        max_output_tokens=4096,
        system_prompt_budget=2000,
        available_for_context=121904
    ),

    # OpenAI GPT-3.5
    "gpt-3.5-turbo": ModelConfig(
        model_name="gpt-3.5-turbo",
        context_window=16385,
        max_output_tokens=4096,
        system_prompt_budget=1500,
        available_for_context=10789
    ),
    "gpt-3.5-turbo-16k": ModelConfig(
        model_name="gpt-3.5-turbo-16k",
        context_window=16385,
        max_output_tokens=4096,
        system_prompt_budget=1500,
        available_for_context=10789
    ),

    # Anthropic Claude
    "claude-3-opus": ModelConfig(
        model_name="claude-3-opus",
        context_window=200000,
        max_output_tokens=4096,
        system_prompt_budget=2000,
        available_for_context=193904
    ),
    "claude-3-sonnet": ModelConfig(
        model_name="claude-3-sonnet",
        context_window=200000,
        max_output_tokens=4096,
        system_prompt_budget=2000,
        available_for_context=193904
    ),

    # Default fallback
    "default": ModelConfig(
        model_name="default",
        context_window=8192,
        max_output_tokens=2048,
        system_prompt_budget=1500,
        available_for_context=4644
    )
}


class TokenBudgetManager:
    """
    Manages token budgets for LLM prompts with model-aware truncation.

    Features:
    - Accurate token counting using tiktoken
    - Model-aware context window management
    - Multiple truncation strategies
    - Priority-based content preservation
    - Intelligent summarization when needed
    """

    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize token budget manager.

        Args:
            model_name: LLM model name for configuration
        """
        self.model_config = self._get_model_config(model_name)
        self.encoder = self._get_encoder(model_name)

        logger.info(
            f"TokenBudgetManager initialized for {model_name}: "
            f"{self.model_config.available_for_context} tokens available for context"
        )

    def _get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for model, with fallback to default."""
        # Normalize model name
        model_key = model_name.lower()

        # Check exact match first
        if model_key in MODEL_CONFIGS:
            return MODEL_CONFIGS[model_key]

        # Check partial matches
        for key in MODEL_CONFIGS:
            if key in model_key or model_key in key:
                return MODEL_CONFIGS[key]

        # Fallback to default
        logger.warning(f"Unknown model {model_name}, using default config")
        return MODEL_CONFIGS["default"]

    def _get_encoder(self, model_name: str):
        """Get tiktoken encoder for model."""
        try:
            # Try model-specific encoding
            if "gpt-4" in model_name.lower():
                return tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model_name.lower():
                return tiktoken.encoding_for_model("gpt-3.5-turbo")
            elif "claude" in model_name.lower():
                # Claude uses similar tokenization to GPT-4
                return tiktoken.encoding_for_model("gpt-4")
            else:
                return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to get encoder for {model_name}: {e}")
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.error(f"Token counting failed: {e}")
            # Fallback to rough estimate
            return len(text) // 4

    def check_budget(
        self,
        system_prompt: str,
        user_messages: List[str],
        raise_on_exceed: bool = False
    ) -> Tuple[bool, int, int]:
        """
        Check if messages fit within token budget.

        Args:
            system_prompt: System prompt text
            user_messages: List of user message texts
            raise_on_exceed: Raise exception if budget exceeded

        Returns:
            Tuple of (fits_budget, total_tokens, available_tokens)
        """
        system_tokens = self.count_tokens(system_prompt)
        message_tokens = sum(self.count_tokens(msg) for msg in user_messages)
        total_tokens = system_tokens + message_tokens

        available = self.model_config.available_for_context
        fits = total_tokens <= available

        if not fits:
            logger.warning(
                f"Token budget exceeded: {total_tokens} > {available} "
                f"(system: {system_tokens}, messages: {message_tokens})"
            )

            if raise_on_exceed:
                raise ValueError(
                    f"Token budget exceeded: {total_tokens} tokens > {available} available"
                )

        return fits, total_tokens, available

    def truncate_text(
        self,
        text: str,
        max_tokens: int,
        strategy: TruncationStrategy = TruncationStrategy.TAIL,
        preserve_markers: Optional[List[str]] = None
    ) -> str:
        """
        Truncate text to fit within token budget.

        Args:
            text: Text to truncate
            max_tokens: Maximum allowed tokens
            strategy: Truncation strategy to use
            preserve_markers: Important text markers to preserve

        Returns:
            Truncated text
        """
        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text

        logger.info(f"Truncating text: {current_tokens} -> {max_tokens} tokens using {strategy.value}")

        if strategy == TruncationStrategy.HEAD:
            return self._truncate_head(text, max_tokens)

        elif strategy == TruncationStrategy.TAIL:
            return self._truncate_tail(text, max_tokens)

        elif strategy == TruncationStrategy.MIDDLE:
            return self._truncate_middle(text, max_tokens)

        elif strategy == TruncationStrategy.SMART:
            return self._truncate_smart(text, max_tokens, preserve_markers)

        else:
            # Default to tail
            return self._truncate_tail(text, max_tokens)

    def _truncate_head(self, text: str, max_tokens: int) -> str:
        """Keep start of text, truncate end."""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        result = self.encoder.decode(truncated_tokens)
        return result + "\n\n[... content truncated ...]"

    def _truncate_tail(self, text: str, max_tokens: int) -> str:
        """Keep end of text, truncate start."""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[-max_tokens:]
        result = self.encoder.decode(truncated_tokens)
        return "[... earlier content truncated ...]\n\n" + result

    def _truncate_middle(self, text: str, max_tokens: int) -> str:
        """Keep start and end, truncate middle."""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Keep first 40% and last 40%
        keep_start = int(max_tokens * 0.4)
        keep_end = max_tokens - keep_start

        start_tokens = tokens[:keep_start]
        end_tokens = tokens[-keep_end:]

        start_text = self.encoder.decode(start_tokens)
        end_text = self.encoder.decode(end_tokens)

        return start_text + "\n\n[... middle content truncated ...]\n\n" + end_text

    def _truncate_smart(
        self,
        text: str,
        max_tokens: int,
        preserve_markers: Optional[List[str]] = None
    ) -> str:
        """
        Intelligently truncate while preserving important sections.

        Preserves:
        - Sections marked with preserve_markers
        - Headers and structure
        - Key metrics and numbers
        """
        if preserve_markers is None:
            preserve_markers = [
                "IMPORTANT:",
                "Key Metrics:",
                "Summary:",
                "Recommendations:",
                "Critical:"
            ]

        # Split into sections
        sections = text.split("\n\n")
        preserved_sections = []
        optional_sections = []

        for section in sections:
            # Check if section should be preserved
            is_preserved = any(marker in section for marker in preserve_markers)
            is_header = section.strip().startswith("#") or section.strip().isupper()
            has_numbers = any(char.isdigit() for char in section)

            if is_preserved or is_header or (has_numbers and len(section) < 200):
                preserved_sections.append(section)
            else:
                optional_sections.append(section)

        # Build result with preserved sections first
        result = "\n\n".join(preserved_sections)
        current_tokens = self.count_tokens(result)

        # Add optional sections until budget exhausted
        for section in optional_sections:
            section_tokens = self.count_tokens(section)
            if current_tokens + section_tokens <= max_tokens:
                result += "\n\n" + section
                current_tokens += section_tokens
            else:
                # Add truncation marker
                result += "\n\n[... additional content omitted due to length ...]"
                break

        return result

    def optimize_context(
        self,
        system_prompt: str,
        context_data: Dict[str, Any],
        max_context_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Optimize context data to fit within token budget.

        Args:
            system_prompt: System prompt (for budget calculation)
            context_data: Dictionary of context data to optimize
            max_context_tokens: Maximum tokens for context (None = use model limit)

        Returns:
            Optimized context dictionary
        """
        if max_context_tokens is None:
            # Reserve space for system prompt
            system_tokens = self.count_tokens(system_prompt)
            max_context_tokens = self.model_config.available_for_context - system_tokens

        optimized = {}
        priority_keys = [
            "summary",
            "key_metrics",
            "recommendations",
            "assessment_data",
            "business_requirements"
        ]

        # Add high-priority keys first
        tokens_used = 0
        for key in priority_keys:
            if key in context_data:
                value_str = str(context_data[key])
                value_tokens = self.count_tokens(value_str)

                if tokens_used + value_tokens <= max_context_tokens:
                    optimized[key] = context_data[key]
                    tokens_used += value_tokens
                else:
                    # Truncate this value
                    remaining = max_context_tokens - tokens_used
                    if remaining > 100:  # Only include if we have meaningful space
                        truncated = self.truncate_text(
                            value_str,
                            remaining,
                            TruncationStrategy.SMART
                        )
                        optimized[key] = truncated
                        tokens_used += self.count_tokens(truncated)
                    break

        # Add remaining keys if space available
        for key, value in context_data.items():
            if key not in optimized:
                value_str = str(value)
                value_tokens = self.count_tokens(value_str)

                if tokens_used + value_tokens <= max_context_tokens:
                    optimized[key] = value
                    tokens_used += value_tokens

        logger.info(
            f"Context optimization: {len(context_data)} -> {len(optimized)} keys, "
            f"{tokens_used} tokens used of {max_context_tokens} available"
        )

        return optimized


# Singleton instance
_budget_manager_instances = {}

def get_token_budget_manager(model_name: str = "gpt-4") -> TokenBudgetManager:
    """Get or create token budget manager for model."""
    if model_name not in _budget_manager_instances:
        _budget_manager_instances[model_name] = TokenBudgetManager(model_name)
    return _budget_manager_instances[model_name]
