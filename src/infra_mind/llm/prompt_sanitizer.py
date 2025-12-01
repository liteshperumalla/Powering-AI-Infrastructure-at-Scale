"""
Prompt Sanitizer - Protection against prompt injection attacks.

Provides comprehensive input sanitization to prevent malicious users from
manipulating LLM behavior through crafted inputs.
"""

import re
import logging
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Supported sanitization security levels."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


@dataclass
class SanitizationResult:
    """Result of sanitization operation."""
    sanitized_value: str
    was_modified: bool
    violations_found: List[str]
    original_length: int
    sanitized_length: int


class PromptInjectionError(ValueError):
    """Raised when prompt injection attempt is detected."""
    pass


class PromptSanitizer:
    """
    Sanitize user inputs to prevent prompt injection attacks.

    Features:
    - Pattern-based injection detection
    - Input length validation
    - Special character filtering
    - Whitespace normalization
    - Recursive sanitization for nested structures

    Security Levels:
    - STRICT: Maximum security, may reject legitimate inputs
    - BALANCED: Good security with minimal false positives (default)
    - PERMISSIVE: Minimal filtering, for trusted inputs only
    """

    # Dangerous patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        # Instruction manipulation
        (r'ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?',
         "instruction_override"),
        (r'new\s+instructions?:', "new_instructions"),
        (r'disregard\s+(all\s+)?(previous|prior|above)', "disregard_previous"),
        (r'forget\s+(all\s+)?(previous|prior|above)', "forget_previous"),

        # Role manipulation
        (r'you\s+are\s+now\s+(a|an)?', "role_change"),
        (r'act\s+as\s+(a|an)?', "role_assumption"),
        (r'pretend\s+(to\s+be|you\s+are)', "pretend_role"),
        (r'simulate\s+(a|an|being)', "simulate_role"),

        # System/Assistant injection
        (r'system\s*:', "system_prefix"),
        (r'assistant\s*:', "assistant_prefix"),
        (r'user\s*:', "user_prefix"),
        (r'human\s*:', "human_prefix"),

        # Delimiter injection
        (r'---+\s*end\s+of', "delimiter_injection"),
        (r'```\s*(system|assistant|user)', "markdown_injection"),
        (r'\[INST\]', "llama_instruction"),
        (r'<\|.*?\|>', "special_tokens"),
        (r'###\s*(System|Assistant|User)', "triple_hash_injection"),

        # Output manipulation
        (r'output\s+(only|just)\s*:', "output_manipulation"),
        (r'respond\s+with\s+(only|just)', "response_control"),
        (r'print\s+(only|just)', "print_control"),
        (r'return\s+(only|just)', "return_control"),

        # Context escape attempts
        (r'</prompt>', "prompt_close_tag"),
        (r'</system>', "system_close_tag"),
        (r'</context>', "context_close_tag"),
        (r'\[/INST\]', "llama_close"),
    ]

    # Maximum input lengths (characters)
    MAX_INPUT_LENGTH_STRICT = 2000
    MAX_INPUT_LENGTH_BALANCED = 5000
    MAX_INPUT_LENGTH_PERMISSIVE = 10000

    # Maximum token estimate (rough: 4 chars per token)
    MAX_TOKENS_STRICT = 500
    MAX_TOKENS_BALANCED = 1500
    MAX_TOKENS_PERMISSIVE = 3000

    def __init__(self, security_level: Union[str, SecurityLevel] = SecurityLevel.BALANCED):
        """
        Initialize prompt sanitizer.

        Args:
            security_level: "strict", "balanced", or "permissive"
        """
        self.security_level = (
            security_level.value if isinstance(security_level, SecurityLevel) else security_level
        ).lower()

        if self.security_level == "strict":
            self.max_length = self.MAX_INPUT_LENGTH_STRICT
            self.max_tokens = self.MAX_TOKENS_STRICT
            self.strict_mode = True
        elif self.security_level == "permissive":
            self.max_length = self.MAX_INPUT_LENGTH_PERMISSIVE
            self.max_tokens = self.MAX_TOKENS_PERMISSIVE
            self.strict_mode = False
        else:  # balanced (default)
            self.max_length = self.MAX_INPUT_LENGTH_BALANCED
            self.max_tokens = self.MAX_TOKENS_BALANCED
            self.strict_mode = False

        logger.info(f"PromptSanitizer initialized with {self.security_level} security level")

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        max_depth: int = 5,
        raise_on_violation: bool = True
    ) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            raise_on_violation: If True, raise exception on injection attempt

        Returns:
            Sanitized dictionary

        Raises:
            PromptInjectionError: If injection detected and raise_on_violation=True
        """
        if max_depth <= 0:
            logger.warning("Maximum recursion depth reached during sanitization")
            return {}

        if not isinstance(data, dict):
            return {}

        sanitized = {}
        violations = []

        for key, value in data.items():
            try:
                if isinstance(value, str):
                    result = self.sanitize_string(value, raise_on_violation=False)
                    sanitized[key] = result.sanitized_value
                    if result.violations_found:
                        violations.extend(result.violations_found)

                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_dict(
                        value, max_depth - 1, raise_on_violation=False
                    )

                elif isinstance(value, list):
                    sanitized[key] = self.sanitize_list(
                        value, max_depth - 1, raise_on_violation=False
                    )

                else:
                    # Non-string values pass through
                    sanitized[key] = value

            except Exception as e:
                logger.error(f"Error sanitizing key '{key}': {str(e)}")
                sanitized[key] = ""

        # If violations found and we should raise, do so
        if violations and raise_on_violation:
            raise PromptInjectionError(
                f"Prompt injection detected in dictionary: {', '.join(set(violations))}"
            )

        return sanitized

    def sanitize_list(
        self,
        data: List[Any],
        max_depth: int = 5,
        raise_on_violation: bool = True
    ) -> List[Any]:
        """
        Sanitize list items.

        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            raise_on_violation: If True, raise exception on injection attempt

        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            return []

        if not isinstance(data, list):
            return []

        sanitized = []
        violations = []

        for item in data:
            if isinstance(item, str):
                result = self.sanitize_string(item, raise_on_violation=False)
                sanitized.append(result.sanitized_value)
                if result.violations_found:
                    violations.extend(result.violations_found)

            elif isinstance(item, dict):
                sanitized.append(
                    self.sanitize_dict(item, max_depth - 1, raise_on_violation=False)
                )

            elif isinstance(item, list):
                sanitized.append(
                    self.sanitize_list(item, max_depth - 1, raise_on_violation=False)
                )

            else:
                sanitized.append(item)

        if violations and raise_on_violation:
            raise PromptInjectionError(
                f"Prompt injection detected in list: {', '.join(set(violations))}"
            )

        return sanitized

    def sanitize_string(
        self,
        text: str,
        raise_on_violation: bool = True
    ) -> SanitizationResult:
        """
        Sanitize a single string input.

        Args:
            text: String to sanitize
            raise_on_violation: If True, raise exception on injection attempt

        Returns:
            SanitizationResult with sanitized string and metadata

        Raises:
            PromptInjectionError: If injection detected and raise_on_violation=True
        """
        if not text or not isinstance(text, str):
            return SanitizationResult(
                sanitized_value="",
                was_modified=False,
                violations_found=[],
                original_length=0,
                sanitized_length=0
            )

        original_text = text
        original_length = len(text)
        violations = []

        # Step 1: Length validation
        if len(text) > self.max_length:
            violations.append(f"exceeds_max_length_{self.max_length}")
            text = text[:self.max_length] + "..."
            logger.warning(
                f"Input truncated: {original_length} chars → {len(text)} chars"
            )

        # Step 2: Token estimation
        estimated_tokens = self._estimate_tokens(text)
        if estimated_tokens > self.max_tokens:
            violations.append(f"exceeds_max_tokens_{self.max_tokens}")
            # Truncate to approximate token limit
            max_chars = self.max_tokens * 4
            text = text[:max_chars] + "..."

        # Step 3: Check for injection patterns
        text_lower = text.lower()
        for pattern, violation_type in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                violations.append(violation_type)
                logger.warning(
                    f"Potential prompt injection detected: {violation_type}"
                )

                if raise_on_violation:
                    raise PromptInjectionError(
                        f"Prompt injection detected: {violation_type}. "
                        f"Input contains suspicious pattern '{pattern}'"
                    )

        # Step 4: Remove or escape dangerous characters (strict mode only)
        if self.strict_mode:
            # Keep only alphanumeric, spaces, and basic punctuation
            text = re.sub(r'[^\w\s.,!?;:()\-\'"\/\\@#$%]', '', text)

        # Step 5: Normalize whitespace
        text = ' '.join(text.split())

        # Step 6: Remove multiple consecutive punctuation
        text = re.sub(r'([.!?])\1{2,}', r'\1\1', text)  # Max 2 consecutive
        text = re.sub(r'([-_])\1{3,}', r'\1\1\1', text)  # Max 3 consecutive

        # Step 7: Final length check after sanitization
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."

        was_modified = (text != original_text)

        result = SanitizationResult(
            sanitized_value=text,
            was_modified=was_modified,
            violations_found=violations,
            original_length=original_length,
            sanitized_length=len(text)
        )

        if was_modified:
            logger.info(
                f"Input sanitized: {original_length} → {len(text)} chars, "
                f"{len(violations)} violations"
            )

        return result

    def validate_and_sanitize(
        self,
        data: Union[str, Dict, List],
        raise_on_violation: bool = True
    ) -> Union[str, Dict, List]:
        """
        Main entry point for sanitization.

        Args:
            data: Data to sanitize (dict, list, or string)
            raise_on_violation: If True, raise exception on injection attempt

        Returns:
            Sanitized data

        Raises:
            PromptInjectionError: If injection detected and raise_on_violation=True
        """
        if isinstance(data, dict):
            return self.sanitize_dict(data, raise_on_violation=raise_on_violation)
        elif isinstance(data, list):
            return self.sanitize_list(data, raise_on_violation=raise_on_violation)
        elif isinstance(data, str):
            result = self.sanitize_string(data, raise_on_violation=raise_on_violation)
            return result.sanitized_value
        else:
            logger.warning(f"Unsupported data type for sanitization: {type(data)}")
            return data

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        # This is conservative; actual may be lower
        return len(text) // 4

    def check_for_violations(self, text: str) -> List[str]:
        """
        Check text for violations without modifying it.

        Args:
            text: Text to check

        Returns:
            List of violation types found
        """
        if not text:
            return []

        violations = []
        text_lower = text.lower()

        for pattern, violation_type in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                violations.append(violation_type)

        return violations


# Convenience functions for common use cases

def sanitize_user_input(
    data: Union[str, Dict, List],
    security_level: str = "balanced"
) -> Union[str, Dict, List]:
    """
    Sanitize user input with default settings.

    Args:
        data: Data to sanitize
        security_level: Security level ("strict", "balanced", "permissive")

    Returns:
        Sanitized data
    """
    sanitizer = PromptSanitizer(security_level=security_level)
    return sanitizer.validate_and_sanitize(data, raise_on_violation=False)


def validate_prompt_safety(text: str) -> bool:
    """
    Check if text is safe for use in prompts.

    Args:
        text: Text to validate

    Returns:
        True if safe, False if violations detected
    """
    sanitizer = PromptSanitizer(security_level="balanced")
    violations = sanitizer.check_for_violations(text)
    return len(violations) == 0


def sanitize_assessment_data(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize assessment data before using in prompts.

    Args:
        assessment_data: Assessment data dictionary

    Returns:
        Sanitized assessment data
    """
    sanitizer = PromptSanitizer(security_level="balanced")
    return sanitizer.sanitize_dict(assessment_data, raise_on_violation=False)
