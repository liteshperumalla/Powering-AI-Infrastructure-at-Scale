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


@router.post("/save-progress")
async def save_progress(progress: Dict[str, Any] = Body(...)):
    """
    Saves the user's progress in the assessment form.
    This is a mock endpoint. In a real application, this would save to a database.
    """
    logger.info(f"Received progress data: {progress}")
    # Here you would typically save the progress data to a database
    # For example: await db.save_user_progress(user_id, progress)
    return {"status": "success", "message": "Progress saved successfully."}


@router.post("/smart-defaults", response_model=SmartDefaultsResponse)
async def get_smart_defaults(request: SmartDefaultRequest):
    """
    Provides smart default values for form fields based on context.
    """
    field_name = request.field_name
    context = request.context

    try:
        # Create validated SmartDefaultItem objects
        defaults_map = {
            "industry": [
                SmartDefaultItem(
                    value="technology",
                    confidence=0.6,
                    reason="Most common industry in our user base",
                    source="usage_patterns"
                )
            ],
            "companySize": [
                SmartDefaultItem(
                    value="small",
                    confidence=0.5,
                    reason="Common starting point for assessments",
                    source="industry_patterns"
                )
            ],
            "monthlyBudget": [
                SmartDefaultItem(
                    value="5k-25k",
                    confidence=0.4,
                    reason="Typical budget range for small to medium companies",
                    source="size_patterns"
                )
            ]
        }

        defaults = defaults_map.get(field_name, [
            SmartDefaultItem(
                value="",
                confidence=0.1,
                reason="No specific defaults available",
                source="fallback"
            )
        ])

        return SmartDefaultsResponse(
            defaults=defaults,
            total=len(defaults),
            field_name=field_name
        )

    except Exception as e:
        logger.error(f"Error generating smart defaults for field '{field_name}': {e}")
        # Return fallback response
        fallback_default = SmartDefaultItem(
            value="",
            confidence=0.1,
            reason="Error generating defaults",
            source="error_fallback"
        )
        return SmartDefaultsResponse(
            defaults=[fallback_default],
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
            logger.warning(f"⚠️ No LLM suggestions generated for field '{field_name}', using enhanced fallback")
            fallback_suggestions = _get_enhanced_fallback_suggestions(field_name, query, context)
            return SuggestionsResponse(
                suggestions=fallback_suggestions,
                total=len(fallback_suggestions),
                field_name=field_name
            )

    except Exception as e:
        logger.error(f"❌ Error getting LLM suggestions: {e}")
        fallback_suggestions = _get_enhanced_fallback_suggestions(field_name, query, context)
        return SuggestionsResponse(
            suggestions=fallback_suggestions,
            total=len(fallback_suggestions),
            field_name=field_name
        )


def _get_enhanced_fallback_suggestions(field_name: str, query: str, context: Dict[str, Any]) -> List[SuggestionItem]:
    """Enhanced fallback suggestions when LLM is not available"""

    # Only provide suggestions if there's a meaningful query
    if not query or len(query.strip()) < 2:
        return []

    industry = context.get("industry").lower()

    # Enhanced fallback with some intelligence
    suggestions = []

    try:
        # For specific fields, provide intelligent fallbacks
        if field_name == "industry" and query:
            industry_matches = {
                "tech": {"value": "technology", "label": "Technology", "description": "Software, IT services, and technology companies"},
                "health": {"value": "healthcare", "label": "Healthcare", "description": "Medical, pharmaceutical, and health technology"},
                "finance": {"value": "finance", "label": "Finance", "description": "Banking, financial services, and fintech"},
                "retail": {"value": "retail", "label": "Retail", "description": "E-commerce and retail businesses"},
                "edu": {"value": "education", "label": "Education", "description": "Educational institutions and EdTech"}
            }

            for key, suggestion_data in industry_matches.items():
                if key in query.lower():
                    suggestion = SuggestionItem(
                        value=suggestion_data["value"],
                        label=suggestion_data["label"],
                        description=suggestion_data["description"],
                        confidence=0.8
                    )
                    suggestions.append(suggestion)

        elif field_name == "workloads" and query:
            workload_keywords = {
                "web": {"value": "web-applications", "label": "Web Applications", "description": "Frontend and backend web services"},
                "api": {"value": "apis", "label": "APIs & Microservices", "description": "REST APIs and microservice architecture"},
                "database": {"value": "databases", "label": "Databases", "description": "SQL and NoSQL database systems"},
                "data": {"value": "data-processing", "label": "Data Processing", "description": "ETL pipelines and data analytics"},
                "ml": {"value": "machine-learning", "label": "Machine Learning", "description": "ML model training and inference"},
                "ai": {"value": "machine-learning", "label": "AI/ML Workloads", "description": "Artificial intelligence and machine learning"}
            }

            for key, suggestion_data in workload_keywords.items():
                if key in query.lower():
                    suggestion = SuggestionItem(
                        value=suggestion_data["value"],
                        label=suggestion_data["label"],
                        description=suggestion_data["description"],
                        confidence=0.7
                    )
                    suggestions.append(suggestion)

        # If no specific matches, provide generic but useful suggestions
        if not suggestions:
            query_clean = query.strip()
            primary_suggestion = SuggestionItem(
                value=query_clean.lower().replace(" ", "-"),
                label=query_clean.title(),
                description=f"Custom entry: {query_clean}",
                confidence=0.6
            )
            suggestions.append(primary_suggestion)

            # Add a variation if query has spaces
            if " " in query_clean:
                alternative_suggestion = SuggestionItem(
                    value=query_clean.lower(),
                    label=query_clean.title(),
                    description=f"Alternative format: {query_clean}",
                    confidence=0.5
                )
                suggestions.append(alternative_suggestion)

    except Exception as e:
        logger.warning(f"Error creating fallback suggestions: {e}")
        # Return empty list if validation fails
        return []

    return suggestions[:5]  # Limit to 5 fallback suggestions


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