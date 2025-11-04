"""
JSON Schema Manager for Structured LLM Outputs.

Provides JSON schemas, few-shot examples, and validation for LLM responses
to ensure consistent structured outputs.
"""

import json
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchemaExample:
    """Example for few-shot prompting with JSON schema."""
    input: str
    output: Dict[str, Any]
    explanation: Optional[str] = None


class JSONSchemaManager:
    """
    Manages JSON schemas and examples for structured LLM outputs.

    Features:
    - Pydantic schema generation
    - Few-shot example templates
    - Response validation
    - Error recovery strategies
    """

    # Common JSON schemas
    SCHEMAS = {
        "strategic_fit": {
            "type": "object",
            "required": ["score", "reasoning", "key_factors"],
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "description": "Strategic alignment score from 0-10"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed explanation of the score"
                },
                "key_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key factors influencing the score"
                },
                "risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Potential strategic risks"
                }
            }
        },

        "financial_analysis": {
            "type": "object",
            "required": ["total_cost", "cost_breakdown", "roi_estimate"],
            "properties": {
                "total_cost": {
                    "type": "number",
                    "description": "Total estimated cost in USD"
                },
                "cost_breakdown": {
                    "type": "object",
                    "description": "Breakdown by category",
                    "additionalProperties": {"type": "number"}
                },
                "roi_estimate": {
                    "type": "number",
                    "description": "Return on investment multiplier"
                },
                "payback_period_months": {
                    "type": "number",
                    "description": "Payback period in months"
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key assumptions for the analysis"
                }
            }
        },

        "risk_assessment": {
            "type": "object",
            "required": ["overall_risk_level", "risks"],
            "properties": {
                "overall_risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Overall risk classification"
                },
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["category", "severity", "description", "mitigation"],
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["technical", "financial", "operational", "strategic"]
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            },
                            "description": {"type": "string"},
                            "mitigation": {"type": "string"},
                            "probability": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1
                            }
                        }
                    }
                },
                "confidence_level": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            }
        },

        "recommendation": {
            "type": "object",
            "required": ["title", "category", "priority", "implementation_effort"],
            "properties": {
                "title": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["cost_optimization", "security", "performance", "architecture", "general"]
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "implementation_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high"]
                },
                "estimated_cost": {"type": "number"},
                "estimated_savings": {"type": "number"},
                "timeline_weeks": {"type": "number"},
                "benefits": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "risks": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "implementation_steps": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }

    # Few-shot examples for each schema
    FEW_SHOT_EXAMPLES = {
        "strategic_fit": [
            SchemaExample(
                input="Assess strategic fit for migrating to Kubernetes for a startup",
                output={
                    "score": 7.5,
                    "reasoning": "Kubernetes provides strong alignment with startup's growth trajectory and modern infrastructure needs. While there's an initial learning curve, the long-term benefits of scalability and containerization align well with anticipated growth.",
                    "key_factors": [
                        "Scalability aligns with growth plans",
                        "Modern DevOps practices support",
                        "Container orchestration capabilities",
                        "Active community and ecosystem"
                    ],
                    "risks": [
                        "Learning curve for team",
                        "Initial complexity overhead",
                        "Cost of managed Kubernetes service"
                    ]
                },
                explanation="Provides balanced assessment with specific factors"
            )
        ],

        "financial_analysis": [
            SchemaExample(
                input="Analyze costs for AWS infrastructure with 3 EC2 instances and RDS",
                output={
                    "total_cost": 2500.00,
                    "cost_breakdown": {
                        "compute": 1200.00,
                        "database": 800.00,
                        "networking": 300.00,
                        "storage": 200.00
                    },
                    "roi_estimate": 2.5,
                    "payback_period_months": 8,
                    "assumptions": [
                        "24/7 operation of all instances",
                        "Standard RDS instance size",
                        "US-East-1 region pricing",
                        "No reserved instance discounts"
                    ]
                }
            )
        ],

        "risk_assessment": [
            SchemaExample(
                input="Assess risks for migrating production database to cloud",
                output={
                    "overall_risk_level": "medium",
                    "risks": [
                        {
                            "category": "technical",
                            "severity": "high",
                            "description": "Potential data loss during migration",
                            "mitigation": "Use parallel run with data validation and rollback plan",
                            "probability": 0.2
                        },
                        {
                            "category": "operational",
                            "severity": "medium",
                            "description": "Service downtime during cutover",
                            "mitigation": "Schedule migration during low-traffic window with blue-green deployment",
                            "probability": 0.5
                        }
                    ],
                    "confidence_level": 0.85
                }
            )
        ]
    }

    @staticmethod
    def get_schema(schema_name: str) -> Dict[str, Any]:
        """
        Get JSON schema by name.

        Args:
            schema_name: Name of the schema

        Returns:
            JSON schema dictionary
        """
        if schema_name not in JSONSchemaManager.SCHEMAS:
            raise ValueError(f"Unknown schema: {schema_name}")

        return JSONSchemaManager.SCHEMAS[schema_name]

    @staticmethod
    def get_schema_prompt(schema_name: str, include_examples: bool = True) -> str:
        """
        Generate prompt text with schema and examples.

        Args:
            schema_name: Name of the schema
            include_examples: Whether to include few-shot examples

        Returns:
            Formatted prompt text
        """
        schema = JSONSchemaManager.get_schema(schema_name)

        prompt = "You MUST respond with valid JSON that matches this exact schema:\n\n"
        prompt += "```json\n"
        prompt += json.dumps(schema, indent=2)
        prompt += "\n```\n\n"

        prompt += "IMPORTANT RULES:\n"
        prompt += "1. Your response must be ONLY valid JSON - no explanatory text before or after\n"
        prompt += "2. All required fields must be present\n"
        prompt += "3. Field types must match the schema exactly\n"
        prompt += "4. Enum values must be one of the specified options\n"
        prompt += "5. Do NOT include any markdown formatting or code blocks\n"
        prompt += "6. Start your response with '{' and end with '}'\n\n"

        if include_examples and schema_name in JSONSchemaManager.FEW_SHOT_EXAMPLES:
            examples = JSONSchemaManager.FEW_SHOT_EXAMPLES[schema_name]
            prompt += "EXAMPLES:\n\n"

            for i, example in enumerate(examples, 1):
                prompt += f"Example {i}:\n"
                prompt += f"Input: {example.input}\n"
                prompt += f"Output:\n```json\n{json.dumps(example.output, indent=2)}\n```\n"
                if example.explanation:
                    prompt += f"Why this works: {example.explanation}\n"
                prompt += "\n"

        prompt += "Now, respond with JSON following this exact schema:"

        return prompt

    @staticmethod
    def validate_response(
        response: str,
        schema_name: str,
        auto_fix: bool = True
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate LLM response against schema.

        Args:
            response: LLM response text
            schema_name: Schema to validate against
            auto_fix: Attempt to fix common issues

        Returns:
            Tuple of (is_valid, parsed_json, error_message)
        """
        try:
            # Clean response
            cleaned = JSONSchemaManager._clean_response(response)

            # Parse JSON
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                if auto_fix:
                    # Try to extract JSON from response
                    data = JSONSchemaManager._extract_json(response)
                    if data is None:
                        return False, None, f"JSON parsing failed: {str(e)}"
                else:
                    return False, None, f"JSON parsing failed: {str(e)}"

            # Validate against schema
            schema = JSONSchemaManager.get_schema(schema_name)
            errors = JSONSchemaManager._validate_against_schema(data, schema)

            if errors:
                return False, data, f"Schema validation failed: {'; '.join(errors)}"

            return True, data, None

        except Exception as e:
            return False, None, f"Validation error: {str(e)}"

    @staticmethod
    def _clean_response(response: str) -> str:
        """Clean common formatting issues from LLM responses."""
        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        # Remove any leading/trailing text before first { and after last }
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')

        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]

        return cleaned.strip()

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text with various strategies."""
        # Strategy 1: Look for first { to last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')

        if first_brace != -1 and last_brace != -1:
            json_str = text[first_brace:last_brace + 1]
            try:
                return json.loads(json_str)
            except:
                pass

        # Strategy 2: Try each line that starts with {
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('{'):
                try:
                    return json.loads(line)
                except:
                    continue

        return None

    @staticmethod
    def _validate_against_schema(
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> List[str]:
        """
        Validate data against JSON schema.

        Args:
            data: Data to validate
            schema: JSON schema

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check properties
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in data:
                continue  # Skip optional fields

            value = data[field]
            field_type = field_schema.get("type")

            # Type validation
            if field_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif field_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif field_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field}' must be array, got {type(value).__name__}")
            elif field_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be object, got {type(value).__name__}")

            # Enum validation
            if "enum" in field_schema:
                if value not in field_schema["enum"]:
                    errors.append(
                        f"Field '{field}' must be one of {field_schema['enum']}, got '{value}'"
                    )

            # Range validation for numbers
            if field_type == "number":
                if "minimum" in field_schema and value < field_schema["minimum"]:
                    errors.append(f"Field '{field}' must be >= {field_schema['minimum']}")
                if "maximum" in field_schema and value > field_schema["maximum"]:
                    errors.append(f"Field '{field}' must be <= {field_schema['maximum']}")

        return errors

    @staticmethod
    def create_custom_schema(
        schema_name: str,
        properties: Dict[str, Any],
        required: List[str],
        examples: Optional[List[SchemaExample]] = None
    ):
        """
        Create and register a custom schema.

        Args:
            schema_name: Unique name for the schema
            properties: JSON schema properties
            required: List of required field names
            examples: Optional few-shot examples
        """
        schema = {
            "type": "object",
            "required": required,
            "properties": properties
        }

        JSONSchemaManager.SCHEMAS[schema_name] = schema

        if examples:
            JSONSchemaManager.FEW_SHOT_EXAMPLES[schema_name] = examples

        logger.info(f"Registered custom schema: {schema_name}")


# Example usage helper
def get_json_prompt(schema_name: str, task_description: str) -> str:
    """
    Generate complete JSON prompt for LLM.

    Args:
        schema_name: Name of the schema to use
        task_description: Description of the task

    Returns:
        Complete prompt text
    """
    schema_prompt = JSONSchemaManager.get_schema_prompt(schema_name)

    full_prompt = f"{task_description}\n\n{schema_prompt}"

    return full_prompt
