from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging

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


@router.post("/smart-defaults")
async def get_smart_defaults(request: Dict[str, Any] = Body(...)):
    """
    Provides smart default values for form fields based on context.
    """
    field_name = request.get("field_name", "")
    context = request.get("context", {})
    
    # Default fallback values
    defaults = {
        "industry": [
            {"value": "technology", "confidence": 0.6, "reason": "Most common industry in our user base", "source": "usage_patterns"}
        ],
        "companySize": [
            {"value": "small", "confidence": 0.5, "reason": "Common starting point for assessments", "source": "industry_patterns"}
        ],
        "monthlyBudget": [
            {"value": "5k-25k", "confidence": 0.4, "reason": "Typical budget range for small to medium companies", "source": "size_patterns"}
        ]
    }
    
    return defaults.get(field_name, [{"value": "", "confidence": 0.1, "reason": "No specific defaults available", "source": "fallback"}])


@router.post("/contextual-help")
async def get_contextual_help(request: Dict[str, Any] = Body(...)):
    """
    Provides contextual help for form fields.
    """
    field_name = request.get("field_name", "")
    context = request.get("context", {})
    
    help_content = {
        "industry": {
            "title": "Industry Selection",
            "content": "Choose the industry that best represents your primary business focus. This helps us provide more relevant infrastructure recommendations.",
            "examples": ["Technology", "Healthcare", "Finance", "E-commerce"],
            "tips": ["Select the industry where you generate most revenue", "If unsure, choose the closest match"],
            "help_type": "tooltip"
        },
        "companySize": {
            "title": "Company Size",
            "content": "Indicate your company size to help us scale our recommendations appropriately.",
            "examples": ["1-10 employees", "11-50 employees", "51-200 employees", "200+ employees"],
            "tips": ["Include contractors and part-time employees", "Choose based on current headcount"],
            "help_type": "tooltip"
        },
        "monthlyBudget": {
            "title": "Monthly Infrastructure Budget",
            "content": "Provide your approximate monthly budget for cloud infrastructure and related services.",
            "examples": ["Under $1k", "$1k-5k", "$5k-25k", "$25k+"],
            "tips": ["Include all cloud-related costs", "Consider future growth needs"],
            "help_type": "modal"
        }
    }
    
    return help_content.get(field_name, {
        "title": "Help",
        "content": "No specific help available for this field.",
        "help_type": "tooltip"
    })


@router.post("/suggestions")
async def get_field_suggestions(request: Dict[str, Any] = Body(...)):
    """
    Provides field suggestions based on query and context.
    """
    field_name = request.get("field_name", "")
    query = request.get("query", "")
    context = request.get("context", {})
    
    # Simple substring matching for suggestions
    suggestions_db = {
        "industry": [
            {"value": "technology", "label": "Technology", "description": "Software, SaaS, IT services", "confidence": 0.9},
            {"value": "healthcare", "label": "Healthcare", "description": "Medical, pharmaceuticals, health tech", "confidence": 0.8},
            {"value": "finance", "label": "Finance", "description": "Banking, fintech, insurance", "confidence": 0.8},
            {"value": "ecommerce", "label": "E-commerce", "description": "Online retail, marketplaces", "confidence": 0.7},
            {"value": "manufacturing", "label": "Manufacturing", "description": "Production, industrial", "confidence": 0.6},
        ]
    }
    
    if field_name in suggestions_db:
        all_suggestions = suggestions_db[field_name]
        if query:
            # Filter suggestions based on query
            filtered = [s for s in all_suggestions if query.lower() in s["label"].lower() or query.lower() in s["value"].lower()]
            return filtered[:5]  # Return top 5 matches
        return all_suggestions[:5]
    
    return []


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
