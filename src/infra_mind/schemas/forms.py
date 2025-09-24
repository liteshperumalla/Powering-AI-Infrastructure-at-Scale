"""
Form-related schemas for Infra Mind.

These models ensure proper validation for AI suggestions and form interactions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

class SuggestionRequest(BaseModel):
    """Request model for AI suggestions"""
    field_name: str = Field(..., min_length=1, description="Name of the form field")
    query: str = Field(default="", description="User's query or partial input")
    context: Dict[str, Any] = Field(default_factory=dict, description="Form context data")

class SmartDefaultRequest(BaseModel):
    """Request model for smart defaults"""
    field_name: str = Field(..., min_length=1, description="Name of the form field")
    context: Dict[str, Any] = Field(default_factory=dict, description="Form context data")

class ContextualHelpRequest(BaseModel):
    """Request model for contextual help"""
    field_name: str = Field(..., min_length=1, description="Name of the form field")
    context: Dict[str, Any] = Field(default_factory=dict, description="Form context data")

class SuggestionItem(BaseModel):
    """Individual suggestion item with validation"""
    label: str = Field(..., min_length=1, max_length=200, description="Display label for the suggestion")
    value: str = Field(..., min_length=1, max_length=500, description="Actual value of the suggestion")
    description: Optional[str] = Field(default=None, max_length=1000, description="Optional description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is a valid percentage"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 3)  # Round to 3 decimal places

class SmartDefaultItem(BaseModel):
    """Smart default item with validation"""
    value: str = Field(..., min_length=1, max_length=500, description="Default value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for this default")
    source: str = Field(default="ai_generated", max_length=100, description="Source of the suggestion")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is a valid percentage"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 3)

class ContextualHelp(BaseModel):
    """Contextual help item with validation"""
    title: str = Field(..., min_length=1, max_length=200, description="Help title")
    content: str = Field(..., min_length=10, max_length=2000, description="Help content")
    help_type: str = Field(default="tooltip", description="Type of help display")
    tips: Optional[List[str]] = Field(default_factory=list, description="Additional tips")

class SuggestionsResponse(BaseModel):
    """Response model for suggestions"""
    suggestions: List[SuggestionItem] = Field(..., description="List of AI suggestions")
    total: int = Field(..., ge=0, description="Total number of suggestions")
    field_name: str = Field(..., description="Field name for which suggestions were generated")

class SmartDefaultsResponse(BaseModel):
    """Response model for smart defaults"""
    defaults: List[SmartDefaultItem] = Field(..., description="List of smart defaults")
    total: int = Field(..., ge=0, description="Total number of defaults")
    field_name: str = Field(..., description="Field name for which defaults were generated")

class FormProgressSaveRequest(BaseModel):
    """Request to save form progress"""
    formId: str = Field(..., min_length=1, description="Unique form identifier")
    formData: Dict[str, Any] = Field(..., description="Form data to save")
    currentStep: int = Field(..., ge=0, description="Current step in the form")

class FormProgressResponse(BaseModel):
    """Response for form progress operations"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Human-readable message")
    formId: Optional[str] = Field(default=None, description="Form identifier")