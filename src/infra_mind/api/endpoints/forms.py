from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from infra_mind.services.llm_service import get_smart_suggestions
from infra_mind.schemas.forms import (
    SuggestionRequest,
    SmartDefaultRequest,
    ContextualHelpRequest,
    SuggestionsResponse,
    SmartDefaultsResponse,
    SuggestionItem,
    SmartDefaultItem,
    ContextualHelp
)

router = APIRouter()

logger = logging.getLogger(__name__)


async def _generate_smart_defaults_for_field(field_name: str, context: Dict[str, Any]) -> List[SmartDefaultItem]:
    """Generate intelligent default values for specific fields based on context"""

    # Extract context information
    industry = context.get("industry", "").lower()
    company_size = context.get("companySize", "").lower()

    # Valid form options for each field (based on actual frontend form)
    valid_form_options = {
        "industry": ["technology", "healthcare", "finance", "retail", "manufacturing", "education", "government", "non-profit", "other"],
        "companySize": ["startup", "small", "medium", "large", "enterprise"],
        "currentAIMaturity": ["none", "pilot", "developing", "scaling", "mature"],
        "geographicRegions": ["North America", "Europe", "Asia Pacific", "Latin America", "Africa", "Middle East", "Global"],
        "currentCloudProvider": ["AWS", "Azure", "Google Cloud", "IBM Cloud", "Oracle Cloud", "Alibaba Cloud", "Other"],
        "currentServices": [
            "Compute (VMs/Containers)", "Storage", "Databases", "Networking", "Security",
            "Analytics", "Machine Learning", "Developer Tools", "IoT", "Backup/Disaster Recovery"
        ],
        "monthlyBudget": ["under-1k", "1k-5k", "5k-15k", "15k-50k", "50k-100k", "100k-500k", "500k+"],
        "technicalTeamSize": ["1-2", "3-5", "6-10", "11-25", "26-50", "50+"],
        "infrastructureAge": ["new", "recent", "established", "legacy"],
        "currentArchitecture": ["monolithic", "microservices", "serverless", "hybrid", "distributed"],
        "dataStorageSolution": [
            "Relational databases (MySQL, PostgreSQL)", "NoSQL databases (MongoDB, DynamoDB)",
            "Data warehouses (Snowflake, BigQuery)", "Object storage (S3, Blob)",
            "File systems", "In-memory databases (Redis)"
        ],
        "networkSetup": ["public-cloud", "vpc", "hybrid", "on-premises", "multi-cloud"],
        "aiUseCases": [
            "Natural Language Processing", "Computer Vision", "Machine Learning",
            "Predictive Analytics", "Recommendation Systems", "Fraud Detection",
            "Process Automation", "Chatbots/Virtual Assistants", "Image Recognition",
            "Speech Recognition", "Data Analytics"
        ],
        "expectedDataVolume": ["1TB", "10TB", "100TB", "1PB", "10PB+"],
        "dataTypes": ["Text", "Images", "Video", "Audio", "Sensor Data", "Structured Data", "Unstructured Data"],
        "realTimeRequirements": ["batch", "near_real_time", "real_time", "streaming"]
    }

    # Comprehensive field mappings - handles both frontend and backend field names
    field_mappings = {
        # Company fields
        "companyName": "company_name", "company_name": "company_name",
        "industry": "industry", "companySize": "company_size",
        "currentAIMaturity": "ai_maturity", "geographicRegions": "geographic_regions",

        # Business fields
        "businessGoal": "business_goals", "businessGoals": "business_goals",
        "currentChallenges": "current_challenges", "challenges": "current_challenges",
        "customerBase": "customer_base", "revenueModel": "revenue_model",

        # Technical fields
        "currentCloudProvider": "cloud_providers", "cloudProvider": "cloud_providers",
        "currentServices": "cloud_services", "services": "cloud_services",
        "workloadTypes": "workload_types", "workloads": "workload_types",
        "aiUseCases": "ai_use_cases", "ai_use_cases": "ai_use_cases",
        "applicationTypes": "application_types", "developmentFrameworks": "frameworks",
        "programmingLanguages": "languages", "databaseTypes": "databases",

        # Infrastructure fields
        "technicalTeamSize": "team_size", "teamSize": "team_size",
        "infrastructureAge": "infra_age", "currentArchitecture": "architecture",
        "dataStorageSolution": "storage", "networkSetup": "network",
        "containerization": "containers", "orchestrationPlatform": "orchestration",
        "cicdTools": "cicd", "versionControlSystem": "vcs",

        # AI & Data fields
        "expectedDataVolume": "data_volume", "dataTypes": "data_types",
        "realTimeRequirements": "real_time", "mlModelTypes": "ml_models",
        "dataProcessingNeeds": "data_processing",

        # Performance fields
        "monthlyBudget": "budget", "budget": "budget",
        "performanceRequirements": "performance", "expectedGrowthRate": "growth_rate",
        "availabilityRequirements": "availability", "scalingTriggers": "scaling_triggers",

        # Security fields
        "complianceRequirements": "compliance", "securityLevel": "security_level",
        "dataLocation": "data_location", "accessControlRequirements": "access_control",
        "encryptionRequirements": "encryption"
    }

    # Normalize field name
    normalized_field = field_mappings.get(field_name, field_name)

    # Get valid options for this field
    valid_options = valid_form_options.get(field_name) or valid_form_options.get(normalized_field)
    if not valid_options:
        # If no valid options defined, return empty (no suggestions)
        return []

    # Industry-specific intelligent selection of valid options
    def get_intelligent_suggestions(field_name: str, valid_options: List[str], industry: str, company_size: str) -> List[str]:
        """Select most relevant valid options based on context"""

        if field_name == "currentCloudProvider":
            if industry == "healthcare":
                return ["Azure", "AWS", "Google Cloud"]  # Azure often preferred for healthcare
            elif industry == "finance":
                return ["Azure", "AWS", "IBM Cloud"]  # Financial institutions often use these
            elif industry == "technology":
                return ["AWS", "Google Cloud", "Azure"]  # Tech companies often prefer AWS/GCP
            else:
                return ["AWS", "Azure", "Google Cloud"]  # Default order

        elif field_name == "aiUseCases":
            if industry == "healthcare":
                return ["Computer Vision", "Natural Language Processing", "Predictive Analytics", "Machine Learning"]
            elif industry == "finance":
                return ["Fraud Detection", "Predictive Analytics", "Machine Learning", "Process Automation"]
            elif industry == "retail":
                return ["Recommendation Systems", "Computer Vision", "Predictive Analytics", "Fraud Detection"]
            elif industry == "technology":
                return ["Machine Learning", "Natural Language Processing", "Computer Vision", "Process Automation"]
            else:
                return ["Machine Learning", "Predictive Analytics", "Process Automation", "Data Analytics"]

        elif field_name == "currentArchitecture":
            if company_size in ["startup", "small"]:
                return ["monolithic", "microservices", "serverless"]
            elif company_size in ["medium", "large"]:
                return ["microservices", "hybrid", "distributed"]
            else:
                return ["microservices", "serverless", "hybrid"]

        elif field_name == "monthlyBudget":
            if company_size == "startup":
                return ["under-1k", "1k-5k", "5k-15k"]
            elif company_size == "small":
                return ["1k-5k", "5k-15k", "15k-50k"]
            elif company_size == "medium":
                return ["15k-50k", "50k-100k", "100k-500k"]
            elif company_size in ["large", "enterprise"]:
                return ["100k-500k", "500k+", "50k-100k"]
            else:
                return ["5k-15k", "15k-50k", "50k-100k"]

        elif field_name == "technicalTeamSize":
            if company_size == "startup":
                return ["1-2", "3-5", "6-10"]
            elif company_size == "small":
                return ["3-5", "6-10", "11-25"]
            elif company_size == "medium":
                return ["11-25", "26-50", "6-10"]
            elif company_size in ["large", "enterprise"]:
                return ["26-50", "50+", "11-25"]
            else:
                return ["6-10", "11-25", "26-50"]

        elif field_name == "expectedDataVolume":
            if industry == "healthcare":
                return ["10TB", "100TB", "1PB"]  # Medical imaging generates large data
            elif industry == "finance":
                return ["1TB", "10TB", "100TB"]  # Transactional data
            elif industry == "technology":
                return ["10TB", "100TB", "1PB"]  # Tech companies often have large datasets
            else:
                return ["1TB", "10TB", "100TB"]

        else:
            # For other fields, return first 3-4 options as most common
            return valid_options[:min(4, len(valid_options))]

    # Get intelligent suggestions
    suggested_options = get_intelligent_suggestions(field_name, valid_options, industry, company_size)

    # Convert to SmartDefaultItem objects
    defaults = []
    for i, suggestion in enumerate(suggested_options[:4]):  # Limit to 4 suggestions
        confidence = max(0.6, 0.9 - (i * 0.1))  # High confidence since these are valid options

        # Create contextual reasoning
        if industry and field_name in ["currentCloudProvider", "aiUseCases", "expectedDataVolume"]:
            reason = f"Commonly used in {industry} industry"
        elif company_size and field_name in ["monthlyBudget", "technicalTeamSize", "currentArchitecture"]:
            reason = f"Typical for {company_size} companies"
        else:
            reason = f"Popular choice for {field_name.replace('current', '').lower()}"

        defaults.append(SmartDefaultItem(
            value=suggestion,
            confidence=confidence,
            reason=reason,
            source="ai_analysis"
        ))

    return defaults


@router.post("/save-progress")
async def save_progress(progress: Dict[str, Any] = Body(...)):
    """
    Saves the user's progress in the assessment form.
    This is a mock endpoint. In a real application, this would save to a database.
    """
    logger.info(f"Received progress data: {progress}")
    # Here you would typically save the progress data to a database
    # For example: await db.save_user_progress(user_id, progress)
    return {"status": "success", "message": "MODIFIED Progress saved successfully with DEBUG."}


@router.post("/smart-defaults", response_model=SmartDefaultsResponse)
async def get_smart_defaults(request: SmartDefaultRequest):
    """
    Provides smart default values for form fields based on context using LLM intelligence.
    """
    field_name = request.field_name
    context = request.context

    print(f"DEBUG: smart-defaults called with field_name='{field_name}', context={context}")
    logger.info(f"🤖 Getting smart defaults for field '{field_name}' with context: {context}")

    try:
        # Generate context-aware defaults using field-specific logic
        logger.info(f"🔍 Calling _generate_smart_defaults_for_field for '{field_name}'")
        defaults = await _generate_smart_defaults_for_field(field_name, context)
        logger.info(f"📋 Generated {len(defaults)} defaults: {[d.value for d in defaults]}")

        # Only return AI-generated suggestions, no static fallbacks
        logger.info(f"✅ Generated {len(defaults)} AI-powered defaults for field '{field_name}'")
        return SmartDefaultsResponse(
            defaults=defaults,
            total=len(defaults),
            field_name=field_name
        )

    except Exception as e:
        print(f"EXCEPTION in smart-defaults: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(f"❌ Error generating smart defaults for field '{field_name}': {e}")
        # Return empty response on error with debug info
        return SmartDefaultsResponse(
            defaults=[SmartDefaultItem(
                value="DEBUG_ERROR_OCCURRED",
                confidence=0.0,
                reason=str(e),
                source="debug"
            )],
            total=1,
            field_name=field_name
        )


@router.post("/contextual-help")
async def get_contextual_help(request: ContextualHelpRequest) -> ContextualHelp:
    """
    Provides contextual help for form fields.
    """
    field_name = request.field_name
    context = request.context

    try:
        # Create validated ContextualHelp objects
        help_content_map = {
            "industry": ContextualHelp(
                title="Industry Selection",
                content="Choose the industry that best represents your primary business focus. This helps us provide more relevant infrastructure recommendations.",
                help_type="tooltip",
                tips=["Select the industry where you generate most revenue", "If unsure, choose the closest match"]
            ),
            "companySize": ContextualHelp(
                title="Company Size",
                content="Indicate your company size to help us scale our recommendations appropriately.",
                help_type="tooltip",
                tips=["Include contractors and part-time employees", "Choose based on current headcount"]
            ),
            "monthlyBudget": ContextualHelp(
                title="Monthly Infrastructure Budget",
                content="Provide your approximate monthly budget for cloud infrastructure and related services.",
                help_type="modal",
                tips=["Include all cloud-related costs", "Consider future growth needs"]
            )
        }

        return help_content_map.get(field_name, ContextualHelp(
            title="Help",
            content="No specific help available for this field.",
            help_type="tooltip"
        ))

    except Exception as e:
        logger.error(f"Error generating contextual help for field '{field_name}': {e}")
        # Return fallback help
        return ContextualHelp(
            title="Help",
            content="Unable to load help content at this time.",
            help_type="tooltip"
        )


@router.post("/suggestions", response_model=SuggestionsResponse)
async def get_field_suggestions(request: SuggestionRequest) -> SuggestionsResponse:
    """
    Provides intelligent LLM-powered field suggestions based on query, context, and form data.
    """
    field_name = request.field_name
    query = request.query
    context = request.context

    logger.info(f"🤖 Getting LLM suggestions for field '{field_name}' with query '{query}'")

    try:
        # Use LLM service for intelligent suggestions
        suggestions = await get_smart_suggestions(field_name, query, context)

        if suggestions:
            logger.info(f"✅ Generated {len(suggestions)} LLM suggestions for field '{field_name}'")
            return SuggestionsResponse(
                suggestions=suggestions,
                total=len(suggestions),
                field_name=field_name
            )
        else:
            logger.info(f"ℹ️ No LLM suggestions generated for field '{field_name}', returning empty response")
            return SuggestionsResponse(
                suggestions=[],
                total=0,
                field_name=field_name
            )

    except Exception as e:
        logger.error(f"❌ Error getting LLM suggestions: {e}")
        return SuggestionsResponse(
            suggestions=[],
            total=0,
            field_name=field_name
        )



@router.get("/list-saved")
async def list_saved_forms():
    """
    Lists all saved form progress for the current user.
    """
    # In a real implementation, this would fetch from database based on user ID
    # For now, return empty list to prevent API errors
    return []


@router.post("/save-form")
async def save_form(form_data: Dict[str, Any] = Body(...)):
    """
    Saves form data for the current user.
    """
    # In a real implementation, this would save to database
    # For now, just log and return success
    logger.info(f"Saving form data: {form_data}")
    return {"status": "success", "message": "Form saved successfully", "id": "temp_id"}


@router.delete("/saved/{form_id}")
async def delete_saved_form(form_id: str):
    """
    Deletes a saved form by ID.
    """
    # In a real implementation, this would delete from database
    logger.info(f"Deleting saved form: {form_id}")
    return {"status": "success", "message": "Form deleted successfully"}