"""
Forms module for user input collection and validation.

This module provides form handling, validation, and multi-step form management
for collecting business and technical requirements from users.
"""

from .base import (
    BaseForm, 
    FormField, 
    FormStep, 
    FormValidationError, 
    FormFieldType
)
from .assessment_form import (
    AssessmentForm, 
    BusinessRequirementsForm, 
    TechnicalRequirementsForm
)
from .validators import (
    FormValidator, 
    ValidationRule,
    RequiredRule,
    EmailRule,
    RangeRule,
    LengthRule,
    PatternRule,
    ChoiceRule,
    MultiChoiceRule,
    CustomRule,
    ValidationResult,
    ValidationSeverity,
    create_business_validator,
    create_technical_validator
)

__all__ = [
    "BaseForm",
    "FormField", 
    "FormStep",
    "FormValidationError",
    "FormFieldType",
    "AssessmentForm",
    "BusinessRequirementsForm",
    "TechnicalRequirementsForm",
    "FormValidator",
    "ValidationRule",
    "RequiredRule",
    "EmailRule",
    "RangeRule",
    "LengthRule",
    "PatternRule",
    "ChoiceRule",
    "MultiChoiceRule",
    "CustomRule",
    "ValidationResult",
    "ValidationSeverity",
    "create_business_validator",
    "create_technical_validator"
]