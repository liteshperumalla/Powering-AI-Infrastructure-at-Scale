"""
LLM Service for generating intelligent suggestions and content using Azure OpenAI.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncAzureOpenAI
import asyncio
from infra_mind.schemas.forms import SuggestionItem, SmartDefaultItem

logger = logging.getLogger(__name__)

class LLMService:
    """Service for generating intelligent suggestions using Azure OpenAI"""

    def __init__(self):
        self.client = None

        # Azure OpenAI configuration - try both naming conventions
        self.azure_endpoint = (
            os.getenv("AZURE_OPENAI_ENDPOINT") or
            os.getenv("INFRA_MIND_AZURE_OPENAI_ENDPOINT")
        )
        self.azure_api_key = (
            os.getenv("AZURE_OPENAI_API_KEY") or
            os.getenv("INFRA_MIND_AZURE_OPENAI_API_KEY")
        )
        self.azure_api_version = (
            os.getenv("AZURE_OPENAI_API_VERSION") or
            os.getenv("INFRA_MIND_AZURE_OPENAI_API_VERSION") or
            "2024-02-15-preview"
        )
        self.deployment_name = (
            os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or
            os.getenv("INFRA_MIND_AZURE_OPENAI_DEPLOYMENT") or
            "gpt-35-turbo"
        )

        if self.azure_endpoint and self.azure_api_key:
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version=self.azure_api_version
            )
            logger.info(f"✅ Azure OpenAI client initialized successfully with endpoint: {self.azure_endpoint}")
            logger.info(f"🚀 Using deployment: {self.deployment_name}")
        else:
            logger.warning("⚠️ Azure OpenAI credentials not found. LLM suggestions will use fallback logic.")
            logger.warning("💡 Required environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")

    async def generate_field_suggestions(
        self,
        field_name: str,
        query: str,
        context: Dict[str, Any],
        num_suggestions: int = 6
    ) -> List[SuggestionItem]:
        """
        Generate intelligent field suggestions using LLM (fast mode)
        """
        if not self.client:
            return self._get_fallback_suggestions(field_name, query, context)

        try:
            # Create context-aware prompt
            prompt = self._create_suggestions_prompt(field_name, query, context, num_suggestions)

            # Call Azure OpenAI API with fast timeout for UI suggestions
            response = await self._call_azure_openai_with_retry(
                prompt=prompt,
                max_retries=2,
                timeout=10.0,  # Fast timeout for UI responsiveness
                max_tokens=800,
                use_case="suggestions"
            )

            # Parse response
            suggestions_text = response.choices[0].message.content
            suggestions = self._parse_suggestions_response(suggestions_text)

            logger.info(f"✅ Generated {len(suggestions)} LLM suggestions for field '{field_name}'")
            return suggestions

        except asyncio.TimeoutError:
            logger.error(f"⏰ LLM suggestion generation timed out for field '{field_name}' after retries")
            return self._get_fallback_suggestions(field_name, query, context)
        except Exception as e:
            logger.error(f"❌ LLM suggestion generation failed for field '{field_name}': {e}")
            return self._get_fallback_suggestions(field_name, query, context)

    async def generate_workflow_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.3
    ) -> str:
        """
        Generate workflow/agent responses using LLM (extended mode for complex processing)
        """
        if not self.client:
            raise Exception("Azure OpenAI client not available for workflow processing")

        try:
            # Call Azure OpenAI API with extended timeout for workflow processing
            response = await self._call_azure_openai_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_retries=3,
                timeout=120.0,  # Extended timeout for complex workflow processing
                max_tokens=max_tokens,
                temperature=temperature,
                use_case="workflow"
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Workflow LLM generation failed: {e}")
            raise

    async def _call_azure_openai_with_retry(
        self,
        prompt: str,
        system_prompt: str = None,
        max_retries: int = 2,
        timeout: float = 10.0,
        max_tokens: int = 800,
        temperature: float = 0.3,
        use_case: str = "suggestions"
    ):
        """Call Azure OpenAI with retry logic and exponential backoff"""

        # Use provided system prompt or default suggestions prompt
        if system_prompt is None:
            system_prompt = self._get_system_prompt()

        logger.info(f"🤖 Azure OpenAI {use_case} request (attempt 1/{max_retries + 1}, timeout: {timeout}s)")

        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    ),
                    timeout=timeout
                )

                # Success - return response
                if attempt > 0:
                    logger.info(f"✅ Azure OpenAI call succeeded on attempt {attempt + 1}")
                return response

            except asyncio.TimeoutError:
                if attempt < max_retries:
                    # Longer wait times for workflow processing
                    wait_time = (attempt + 1) * (5 if use_case == "workflow" else 2)
                    logger.warning(f"⏰ Azure OpenAI {use_case} timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"⏰ Azure OpenAI {use_case} failed after {max_retries + 1} attempts")
                    raise

            except Exception as e:
                if attempt < max_retries and "rate" in str(e).lower():
                    # Longer wait for rate limits, especially for workflow
                    wait_time = (attempt + 1) * (8 if use_case == "workflow" else 3)
                    logger.warning(f"🚫 Rate limit on {use_case} attempt {attempt + 1}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Azure OpenAI {use_case} error on attempt {attempt + 1}: {e}")
                    raise

    def _get_system_prompt(self) -> str:
        """Get the optimized system prompt for faster LLM responses"""
        return """You are an AI consultant. Provide 6 relevant suggestions for form fields.

Return JSON array with format:
[{"value": "suggestion-value", "label": "Display Name", "description": "Brief explanation", "confidence": 0.95}]

Consider user context (industry, company size) and make suggestions specific and actionable. Return ONLY the JSON array."""

    def _create_suggestions_prompt(
        self,
        field_name: str,
        query: str,
        context: Dict[str, Any],
        num_suggestions: int
    ) -> str:
        """Create a context-aware prompt for generating suggestions"""

        # Extract key context information
        industry = context.get("industry")
        company_size = context.get("companySize")
        company_name = context.get("companyName")
        monthly_budget = context.get("monthlyBudget")

        prompt = f"""Field: {field_name}
Query: "{query}"
Industry: {industry}
Size: {company_size}

Generate {num_suggestions} suggestions as JSON array:"""

        return prompt

    def _get_field_guidance(self, field_name: str, context: Dict[str, Any]) -> str:
        """Get specific guidance for different field types"""

        field_guidance = {
            "workloads": """
            Suggest specific types of applications/services they might be running.
            Consider their industry - e.g., e-commerce needs payment processing, healthcare needs patient data systems.
            Include both common workloads and industry-specific ones.
            """,

            "technicalRequirements": """
            Suggest infrastructure requirements based on their workloads and industry.
            Consider compliance needs for regulated industries.
            Include performance, security, and scalability requirements.
            """,

            "businessRequirements": """
            Focus on business outcomes and goals.
            Consider cost optimization, reliability, performance, and growth needs.
            Align with their company size and budget constraints.
            """,

            "currentChallenges": """
            Suggest common infrastructure pain points for their industry and company size.
            Consider typical challenges like high costs, performance issues, scalability problems.
            Be specific to their context.
            """,

            "goals": """
            Suggest realistic infrastructure goals based on their current challenges and context.
            Focus on measurable outcomes like cost reduction, performance improvement, reliability.
            Align with business priorities for their industry.
            """,

            "companyName": """
            If they have an industry context, suggest naming patterns common in that industry.
            Keep suggestions professional and industry-appropriate.
            """,

            "timeline": """
            Suggest realistic implementation timelines based on their requirements complexity.
            Consider their company size - larger companies typically need longer implementation times.
            """,
        }

        return field_guidance.get(field_name, "Provide contextually relevant suggestions for this field.")

    def _parse_suggestions_response(self, response_text: str) -> List[SuggestionItem]:
        """Parse the LLM response into validated SuggestionItem objects"""
        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()

            # Find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1

            if start_idx != -1 and end_idx != 0:
                json_text = response_text[start_idx:end_idx]
                suggestions_data = json.loads(json_text)

                # Validate and create SuggestionItem objects
                valid_suggestions = []
                for suggestion_data in suggestions_data:
                    try:
                        # Create SuggestionItem with Pydantic validation
                        suggestion = SuggestionItem(
                            label=suggestion_data.get('label'),
                            value=suggestion_data.get('value'),
                            description=suggestion_data.get('description'),
                            confidence=suggestion_data.get('confidence', 0.7)
                        )
                        valid_suggestions.append(suggestion)
                    except Exception as validation_error:
                        logger.warning(f"Skipping invalid suggestion due to validation error: {validation_error}")
                        continue

                if valid_suggestions:
                    return valid_suggestions

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse LLM suggestions response: {e}")

        # Return empty list if parsing fails
        return []

    def _get_fallback_suggestions(self, field_name: str, query: str, context: Dict[str, Any]) -> List[SuggestionItem]:
        """Fallback suggestions when LLM is not available"""
        if not query or len(query) < 2:
            return []

        # Very basic fallback - return validated SuggestionItem objects
        fallback_suggestions = []

        try:
            # Primary suggestion
            primary = SuggestionItem(
                value=query.lower().replace(" ", "-"),
                label=query.title(),
                description=f"Use '{query}' as specified",
                confidence=0.6
            )
            fallback_suggestions.append(primary)

            # Alternative suggestion if query has spaces
            if " " in query:
                alternative = SuggestionItem(
                    value=query.lower(),
                    label=query.lower(),
                    description=f"Lowercase version of '{query}'",
                    confidence=0.5
                )
                fallback_suggestions.append(alternative)

        except Exception as e:
            logger.warning(f"Failed to create fallback suggestions: {e}")
            return []

        return fallback_suggestions

# Global instance
llm_service = LLMService()


async def get_smart_suggestions(
    field_name: str,
    query: str,
    context: Dict[str, Any]
) -> List[SuggestionItem]:
    """
    Main function to get smart suggestions for a field
    """
    return await llm_service.generate_field_suggestions(field_name, query, context)