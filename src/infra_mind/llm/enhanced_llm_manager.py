"""
Enhanced LLM Manager with Global Security and Token Budget Enforcement.

Wraps the existing LLM manager with additional safety layers:
- Mandatory prompt sanitization
- Token budget validation
- JSON schema enforcement
- Response validation
- Automatic retry with fixes
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Enhanced LLM request with validation."""
    model: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    json_schema: Optional[str] = None
    require_json: bool = False
    sanitize: bool = True
    validate_budget: bool = True


@dataclass
class LLMResponse:
    """Enhanced LLM response with metadata."""
    content: str
    tokens_used: int
    model_used: str
    sanitization_applied: bool
    budget_validated: bool
    json_validated: bool
    warnings: List[str]
    success: bool


class EnhancedLLMManager:
    """
    Enhanced LLM Manager with comprehensive safety and quality controls.

    Features:
    - Automatic prompt sanitization (enforced globally)
    - Token budget validation before requests
    - JSON schema enforcement with validation
    - Automatic retry with fixes on failure
    - Response quality validation
    - Comprehensive logging and monitoring
    """

    def __init__(
        self,
        base_manager=None,
        default_model: str = "gpt-4",
        strict_mode: bool = True
    ):
        """
        Initialize enhanced LLM manager.

        Args:
            base_manager: Existing LLM manager instance (optional)
            default_model: Default model to use
            strict_mode: Enable strict validation and enforcement
        """
        self.default_model = default_model
        self.strict_mode = strict_mode
        self.base_manager = base_manager

        # Lazy import to avoid circular dependencies
        from .prompt_sanitizer import PromptSanitizer, SecurityLevel
        from .token_budget_manager import get_token_budget_manager
        from .json_schema_manager import JSONSchemaManager

        self.sanitizer = PromptSanitizer(security_level=SecurityLevel.BALANCED)
        self.budget_manager = get_token_budget_manager(default_model)
        self.schema_manager = JSONSchemaManager

        logger.info(
            f"EnhancedLLMManager initialized (strict_mode={strict_mode}, "
            f"model={default_model})"
        )

    async def generate(
        self,
        request: LLMRequest,
        retry_on_failure: bool = True,
        max_retries: int = 2
    ) -> LLMResponse:
        """
        Generate LLM response with comprehensive validation and safety.

        Args:
            request: LLM request with prompts and parameters
            retry_on_failure: Retry with fixes on validation failures
            max_retries: Maximum retry attempts

        Returns:
            Enhanced LLM response with metadata
        """
        warnings = []
        sanitization_applied = False
        budget_validated = False

        try:
            # Step 1: Sanitize prompts (ENFORCED)
            if request.sanitize or self.strict_mode:
                sanitized_system = self._sanitize_prompt(
                    request.system_prompt,
                    context="system_prompt"
                )
                sanitized_user = self._sanitize_prompt(
                    request.user_prompt,
                    context="user_prompt"
                )

                if sanitized_system != request.system_prompt:
                    warnings.append("System prompt was sanitized")
                    request.system_prompt = sanitized_system

                if sanitized_user != request.user_prompt:
                    warnings.append("User prompt was sanitized")
                    request.user_prompt = sanitized_user

                sanitization_applied = True
                logger.debug("Prompts sanitized successfully")

            # Step 2: Validate token budget
            if request.validate_budget or self.strict_mode:
                budget_ok, total_tokens, available = self.budget_manager.check_budget(
                    system_prompt=request.system_prompt,
                    user_messages=[request.user_prompt],
                    raise_on_exceed=False
                )

                budget_validated = True

                if not budget_ok:
                    if self.strict_mode:
                        # Truncate user prompt to fit
                        max_user_tokens = available - self.budget_manager.count_tokens(
                            request.system_prompt
                        ) - 100  # Safety margin

                        request.user_prompt = self.budget_manager.truncate_text(
                            request.user_prompt,
                            max_user_tokens,
                            strategy=TruncationStrategy.SMART
                        )

                        warnings.append(
                            f"User prompt truncated from {total_tokens} to fit budget"
                        )
                        logger.warning(f"Token budget exceeded, truncated to fit")
                    else:
                        warnings.append(f"Token budget exceeded: {total_tokens} > {available}")

            # Step 3: Add JSON schema if required
            if request.json_schema:
                schema_prompt = self.schema_manager.get_schema_prompt(
                    request.json_schema,
                    include_examples=True
                )

                # Prepend schema to user prompt
                request.user_prompt = schema_prompt + "\n\n" + request.user_prompt

                logger.debug(f"Added JSON schema: {request.json_schema}")

            # Step 4: Call base LLM manager
            if self.base_manager:
                response_text = await self._call_base_manager(request)
            else:
                # Fallback to direct LLM call
                response_text = await self._call_llm_direct(request)

            # Step 5: Validate JSON response if required
            json_validated = False
            if request.require_json and request.json_schema:
                is_valid, parsed_data, error = self.schema_manager.validate_response(
                    response_text,
                    request.json_schema,
                    auto_fix=True
                )

                json_validated = is_valid

                if not is_valid:
                    if retry_on_failure and max_retries > 0:
                        warnings.append(f"JSON validation failed: {error}, retrying...")
                        logger.warning(f"JSON validation failed, retrying: {error}")

                        # Retry with enhanced prompt
                        enhanced_request = self._enhance_json_request(request, error)
                        return await self.generate(
                            enhanced_request,
                            retry_on_failure=retry_on_failure,
                            max_retries=max_retries - 1
                        )
                    else:
                        warnings.append(f"JSON validation failed: {error}")
                        logger.error(f"JSON validation failed: {error}")

                else:
                    # Replace response with parsed JSON
                    import json
                    response_text = json.dumps(parsed_data, indent=2)

            # Estimate tokens used
            tokens_used = self.budget_manager.count_tokens(
                request.system_prompt + request.user_prompt + response_text
            )

            return LLMResponse(
                content=response_text,
                tokens_used=tokens_used,
                model_used=request.model,
                sanitization_applied=sanitization_applied,
                budget_validated=budget_validated,
                json_validated=json_validated,
                warnings=warnings,
                success=True
            )

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")

            return LLMResponse(
                content="",
                tokens_used=0,
                model_used=request.model,
                sanitization_applied=sanitization_applied,
                budget_validated=budget_validated,
                json_validated=False,
                warnings=warnings + [f"Generation failed: {str(e)}"],
                success=False
            )

    def _sanitize_prompt(self, prompt: str, context: str) -> str:
        """Sanitize prompt using PromptSanitizer."""
        try:
            result = self.sanitizer.sanitize(prompt)

            if not result.is_safe and self.strict_mode:
                logger.warning(
                    f"Prompt safety issues detected in {context}: "
                    f"{result.violations}"
                )

            return result.sanitized_content

        except Exception as e:
            logger.error(f"Sanitization failed for {context}: {e}")
            return prompt  # Return original if sanitization fails

    async def _call_base_manager(self, request: LLMRequest) -> str:
        """Call existing LLM manager."""
        try:
            # Assuming base manager has generate method
            response = await self.base_manager.generate(
                model=request.model,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            return response

        except Exception as e:
            logger.error(f"Base manager call failed: {e}")
            raise

    async def _call_llm_direct(self, request: LLMRequest) -> str:
        """Direct LLM call (fallback)."""
        # This would integrate with OpenAI/Anthropic API directly
        # For now, just raise error
        raise NotImplementedError(
            "Direct LLM calls not implemented. Provide base_manager instance."
        )

    def _enhance_json_request(self, request: LLMRequest, error: str) -> LLMRequest:
        """Enhance request after JSON validation failure."""
        # Add explicit instructions based on error
        enhancement = "\n\n" + "CRITICAL: Your previous response had JSON errors. "

        if "parsing" in error.lower():
            enhancement += "Ensure you return ONLY valid JSON with no extra text. "
        if "missing" in error.lower():
            enhancement += "Include ALL required fields in your response. "
        if "type" in error.lower():
            enhancement += "Ensure all field types match the schema exactly. "

        enhancement += "Start with '{' and end with '}'. No markdown formatting."

        request.user_prompt += enhancement

        return request


# REMOVED SINGLETON PATTERN (Week 3-4 Refactoring)
# Use dependency injection instead: from core.dependencies import LLMManagerDep
#
# Migration Note:
# The global singleton pattern has been removed to enable:
# - Horizontal scaling (multiple API instances)
# - Better testability (can mock dependencies)
# - No memory leaks (instances can be garbage collected)
# - Thread safety (no shared global state)
#
# Old usage:
#   manager = get_enhanced_llm_manager()  # ❌ REMOVED
#
# New usage:
#   from ..core.dependencies import LLMManagerDep
#
#   @router.post("/endpoint")
#   async def endpoint(llm_manager: LLMManagerDep):
#       result = await llm_manager.generate(...)


# Import fix
from .token_budget_manager import TruncationStrategy
