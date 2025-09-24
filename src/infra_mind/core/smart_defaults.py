"""
Smart Defaults Module for Infra Mind.

Provides intelligent fallback handling to replace generic "unknown", "", and default values
with contextually appropriate alternatives based on available data.
"""

import logging
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class SmartDefaults:
    """
    Smart defaults provider that generates contextually appropriate fallback values
    instead of generic ones like "unknown", "", or "default".
    """

    @staticmethod
    def get_company_size(context: Dict[str, Any]) -> str:
        """Get intelligent company size fallback."""
        # Try to infer from other context
        if "expected_users" in context:
            users = context.get("expected_users", 0)
            if isinstance(users, str):
                try:
                    users = int(users.replace(",", "").replace("+", ""))
                except:
                    users = 0

            if users < 50:
                return "small"
            elif users < 500:
                return "medium"
            elif users < 5000:
                return "large"
            else:
                return "enterprise"

        # Check budget indicators
        budget = context.get("monthly_budget", context.get("budget_range"))
        if isinstance(budget, str):
            budget_lower = budget.lower()
            if any(x in budget_lower for x in ["million", "enterprise", "enterprise-scale"]):
                return "enterprise"
            elif any(x in budget_lower for x in ["100k", "large", "corp"]):
                return "large"
            elif any(x in budget_lower for x in ["10k", "50k", "medium"]):
                return "medium"
            else:
                return "small"

        return "medium"  # Most common size

    @staticmethod
    def get_industry(context: Dict[str, Any]) -> str:
        """Get intelligent industry fallback."""
        # Check for industry indicators in other fields
        workloads = context.get("workloads", [])
        tech_req = context.get("technical_requirements", [])

        # Combine all text for analysis
        text_indicators = []
        if isinstance(workloads, list):
            text_indicators.extend([str(w).lower() for w in workloads])
        if isinstance(tech_req, list):
            text_indicators.extend([str(t).lower() for t in tech_req])

        combined_text = " ".join(text_indicators)

        # Industry detection patterns
        if any(x in combined_text for x in ["payment", "financial", "banking", "fintech", "trading"]):
            return "financial-services"
        elif any(x in combined_text for x in ["health", "medical", "patient", "clinical", "hipaa"]):
            return "healthcare"
        elif any(x in combined_text for x in ["retail", "ecommerce", "shopping", "inventory", "pos"]):
            return "retail"
        elif any(x in combined_text for x in ["education", "student", "learning", "university", "school"]):
            return "education"
        elif any(x in combined_text for x in ["government", "public", "citizen", "compliance", "regulation"]):
            return "government"
        elif any(x in combined_text for x in ["manufacturing", "factory", "production", "supply"]):
            return "manufacturing"
        elif any(x in combined_text for x in ["media", "content", "streaming", "entertainment"]):
            return "media"
        else:
            return "technology"  # Default for tech companies

    @staticmethod
    def get_provider(context: Dict[str, Any]) -> str:
        """Get intelligent cloud provider fallback."""
        # Check for provider indicators in context
        services = context.get("recommended_services", context.get("services", []))
        tech_req = context.get("technical_requirements", [])

        text_indicators = []
        if isinstance(services, list):
            text_indicators.extend([str(s).lower() for s in services])
        if isinstance(tech_req, list):
            text_indicators.extend([str(t).lower() for t in tech_req])

        combined_text = " ".join(text_indicators)

        # Provider detection
        aws_indicators = ["ec2", "s3", "lambda", "rds", "eks", "fargate", "cloudfront"]
        azure_indicators = ["vm", "blob", "functions", "sql database", "aks", "app service"]
        gcp_indicators = ["compute engine", "cloud storage", "cloud functions", "cloud sql", "gke"]

        if any(x in combined_text for x in aws_indicators):
            return "AWS"
        elif any(x in combined_text for x in azure_indicators):
            return "Azure"
        elif any(x in combined_text for x in gcp_indicators):
            return "GCP"
        else:
            return "Multi-Cloud"

    @staticmethod
    def get_budget_range(context: Dict[str, Any]) -> str:
        """Get intelligent budget range fallback."""
        company_size = SmartDefaults.get_company_size(context)

        # Estimate based on company size
        if company_size == "enterprise":
            return "$100K+ monthly"
        elif company_size == "large":
            return "$25K-100K monthly"
        elif company_size == "medium":
            return "$5K-25K monthly"
        else:
            return "$1K-5K monthly"

    @staticmethod
    def get_service_name(context: Dict[str, Any], category: str = "") -> str:
        """Get intelligent service name fallback."""
        provider = SmartDefaults.get_provider(context)

        if category:
            category_clean = category.replace("_", " ").title()
            return f"{provider} {category_clean} Service"

        # Use provider-specific defaults
        if provider == "AWS":
            return "AWS Cloud Infrastructure"
        elif provider == "Azure":
            return "Azure Cloud Platform"
        elif provider == "GCP":
            return "Google Cloud Platform"
        else:
            return "Multi-Cloud Infrastructure"

    @staticmethod
    def get_status(context: Dict[str, Any]) -> str:
        """Get intelligent status fallback."""
        # Check for status indicators
        if "created_at" in context:
            created_at = context.get("created_at")
            if isinstance(created_at, datetime):
                # If recently created, likely in progress
                if (datetime.now() - created_at).days < 1:
                    return "initializing"
                else:
                    return "active"

        # Check for progress indicators
        if "progress" in context:
            progress = context.get("progress", {})
            if isinstance(progress, dict):
                if progress.get("percentage", 0) == 100:
                    return "completed"
                elif progress.get("percentage", 0) > 0:
                    return "in_progress"

        return "pending"

    @staticmethod
    def get_current_step(context: Dict[str, Any]) -> str:
        """Get intelligent current step fallback."""
        # Check for step indicators
        if "status" in context:
            status = context.get("status")
            if status in ["completed", "done"]:
                return "completed"
            elif status in ["running", "in_progress"]:
                return "processing"
            elif status in ["failed", "error"]:
                return "failed"

        # Check for progress indicators
        progress = context.get("progress", {})
        if isinstance(progress, dict):
            percentage = progress.get("percentage", 0)
            if percentage == 0:
                return "initialization"
            elif percentage < 25:
                return "analysis"
            elif percentage < 50:
                return "evaluation"
            elif percentage < 75:
                return "recommendation_generation"
            elif percentage < 100:
                return "finalization"
            else:
                return "completed"

        return "initialization"

    @staticmethod
    def get_user_identifier(context: Dict[str, Any]) -> str:
        """Get intelligent user identifier fallback."""
        # Try various user identification methods
        for field in ["email", "user_email", "requester", "created_by"]:
            if field in context and context[field]:
                return str(context[field])

        # Generate a meaningful identifier
        company_name = context.get("company_name")
        if company_name:
            company_slug = company_name.lower().replace(" ").replace(".", "")
            return f"user@{company_slug}.com"

        industry = SmartDefaults.get_industry(context)
        return f"user@{industry.replace('-', '')}.com"

    @staticmethod
    def get_smart_fallback(field_name: str, context: Dict[str, Any], current_value: Any = None) -> Any:
        """
        Get intelligent fallback for any field based on context.

        Args:
            field_name: Name of the field needing a fallback
            context: Available context data
            current_value: Current value (if it's "unknown", "", etc.)

        Returns:
            Intelligent fallback value
        """
        # Skip if current value is already good
        if current_value and current_value not in ["unknown", "", "default", "N/A", None]:
            return current_value

        # Field-specific intelligent fallbacks
        field_handlers = {
            "company_size": SmartDefaults.get_company_size,
            "industry": SmartDefaults.get_industry,
            "provider": SmartDefaults.get_provider,
            "budget_range": SmartDefaults.get_budget_range,
            "status": SmartDefaults.get_status,
            "current_step": SmartDefaults.get_current_step,
            "requester": SmartDefaults.get_user_identifier,
            "created_by": SmartDefaults.get_user_identifier,
            "email": SmartDefaults.get_user_identifier,
        }

        # Try specific handler
        if field_name in field_handlers:
            try:
                return field_handlers[field_name](context)
            except Exception as e:
                logger.warning(f"Smart fallback failed for {field_name}: {e}")

        # Service name patterns
        if "service" in field_name.lower():
            category = context.get("category", context.get("service_type"))
            return SmartDefaults.get_service_name(context, category)

        # Version patterns
        if "version" in field_name.lower():
            return "v1.0.0"

        # ID patterns
        if field_name.endswith("_id") or field_name == "id":
            return str(uuid.uuid4())

        # Name patterns
        if "name" in field_name.lower() and "service" not in field_name.lower():
            prefix = field_name.replace("_name", "").replace("name", "").replace("_", " ").title()
            if not prefix:
                prefix = "Resource"
            timestamp = datetime.now().strftime("%Y%m%d")
            return f"{prefix} {timestamp}"

        # Default based on field type inference
        if field_name.lower() in ["category", "type"]:
            return "infrastructure"
        elif field_name.lower() in ["priority"]:
            return "medium"
        elif field_name.lower() in ["environment", "env"]:
            return "production"

        # Last resort: descriptive unknown
        return f"unspecified_{field_name.lower()}"

    @staticmethod
    def enhance_context(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a data dictionary by replacing all fallback values with smart defaults.

        Args:
            data: Dictionary to enhance

        Returns:
            Enhanced dictionary with smart fallbacks
        """
        enhanced = data.copy()

        # Fields that commonly have fallback issues
        fallback_fields = [
            "company_size", "industry", "provider", "budget_range", "status",
            "current_step", "requester", "created_by", "email", "service_name",
            "category", "priority", "environment", "version"
        ]

        for field in fallback_fields:
            if field in enhanced:
                current_value = enhanced[field]
                if current_value in ["unknown", "", "default", "N/A", None]:
                    enhanced[field] = SmartDefaults.get_smart_fallback(field, enhanced, current_value)

        return enhanced


# Convenient aliases for common operations
def smart_get(data: Dict[str, Any], key: str, fallback_context: Optional[Dict[str, Any]] = None) -> Any:
    """
    Smart version of dict.get() that provides intelligent fallbacks.

    Args:
        data: Dictionary to get value from
        key: Key to retrieve
        fallback_context: Context for generating smart fallback (defaults to data itself)

    Returns:
        Value with intelligent fallback if needed
    """
    value = data.get(key)
    if value and value not in ["unknown", "", "default", "N/A"]:
        return value

    context = fallback_context or data
    return SmartDefaults.get_smart_fallback(key, context, value)


def enhance_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenient function to enhance a dictionary with smart defaults."""
    return SmartDefaults.enhance_context(data)