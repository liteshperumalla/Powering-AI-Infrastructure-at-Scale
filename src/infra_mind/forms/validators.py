"""
Form validation utilities and custom validators.

Provides validation rules and utilities for form field validation.
"""

import re
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation messages."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    
    def __bool__(self) -> bool:
        return self.is_valid


class ValidationRule(ABC):
    """Base class for validation rules."""
    
    def __init__(self, message: str = "", severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.message = message
        self.severity = severity
    
    @abstractmethod
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a value and return the result."""
        pass
    
    def __call__(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Make the rule callable."""
        return self.validate(value, context)


class RequiredRule(ValidationRule):
    """Rule to check if a value is required."""
    
    def __init__(self, message: str = "This field is required"):
        super().__init__(message)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        is_valid = value is not None and value != ""
        if isinstance(value, (list, dict)):
            is_valid = len(value) > 0
        
        return ValidationResult(
            is_valid=is_valid,
            message=self.message if not is_valid else "",
            severity=self.severity
        )


class EmailRule(ValidationRule):
    """Rule to validate email addresses."""
    
    def __init__(self, message: str = "Invalid email format"):
        super().__init__(message)
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult(is_valid=True)  # Let RequiredRule handle empty values
        
        is_valid = bool(self.email_pattern.match(str(value)))
        return ValidationResult(
            is_valid=is_valid,
            message=self.message if not is_valid else "",
            severity=self.severity
        )


class RangeRule(ValidationRule):
    """Rule to validate numeric ranges."""
    
    def __init__(self, min_value: Optional[Union[int, float]] = None, 
                 max_value: Optional[Union[int, float]] = None,
                 message: str = ""):
        self.min_value = min_value
        self.max_value = max_value
        
        if not message:
            if min_value is not None and max_value is not None:
                message = f"Value must be between {min_value} and {max_value}"
            elif min_value is not None:
                message = f"Value must be at least {min_value}"
            elif max_value is not None:
                message = f"Value must be at most {max_value}"
            else:
                message = "Invalid range"
        
        super().__init__(message)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult(is_valid=True)
        
        try:
            num_value = float(value)
            is_valid = True
            
            if self.min_value is not None and num_value < self.min_value:
                is_valid = False
            if self.max_value is not None and num_value > self.max_value:
                is_valid = False
            
            return ValidationResult(
                is_valid=is_valid,
                message=self.message if not is_valid else "",
                severity=self.severity
            )
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                message="Invalid number format",
                severity=self.severity
            )


class LengthRule(ValidationRule):
    """Rule to validate string length."""
    
    def __init__(self, min_length: Optional[int] = None, 
                 max_length: Optional[int] = None,
                 message: str = ""):
        self.min_length = min_length
        self.max_length = max_length
        
        if not message:
            if min_length is not None and max_length is not None:
                message = f"Must be between {min_length} and {max_length} characters"
            elif min_length is not None:
                message = f"Must be at least {min_length} characters"
            elif max_length is not None:
                message = f"Must be at most {max_length} characters"
            else:
                message = "Invalid length"
        
        super().__init__(message)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult(is_valid=True)
        
        str_value = str(value)
        length = len(str_value)
        is_valid = True
        
        if self.min_length is not None and length < self.min_length:
            is_valid = False
        if self.max_length is not None and length > self.max_length:
            is_valid = False
        
        return ValidationResult(
            is_valid=is_valid,
            message=self.message if not is_valid else "",
            severity=self.severity
        )


class PatternRule(ValidationRule):
    """Rule to validate against a regex pattern."""
    
    def __init__(self, pattern: str, message: str = "Invalid format"):
        super().__init__(message)
        self.pattern = re.compile(pattern)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult(is_valid=True)
        
        is_valid = bool(self.pattern.match(str(value)))
        return ValidationResult(
            is_valid=is_valid,
            message=self.message if not is_valid else "",
            severity=self.severity
        )


class ChoiceRule(ValidationRule):
    """Rule to validate against a list of valid choices."""
    
    def __init__(self, choices: List[Any], message: str = ""):
        self.choices = choices
        if not message:
            message = f"Must be one of: {', '.join(str(c) for c in choices)}"
        super().__init__(message)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult(is_valid=True)
        
        is_valid = value in self.choices
        return ValidationResult(
            is_valid=is_valid,
            message=self.message if not is_valid else "",
            severity=self.severity
        )


class MultiChoiceRule(ValidationRule):
    """Rule to validate multiple choices against a list of valid options."""
    
    def __init__(self, choices: List[Any], min_selections: int = 0, max_selections: Optional[int] = None, message: str = ""):
        self.choices = choices
        self.min_selections = min_selections
        self.max_selections = max_selections
        
        if not message:
            message = f"Must select from: {', '.join(str(c) for c in choices)}"
            if min_selections > 0:
                message += f" (minimum {min_selections})"
            if max_selections is not None:
                message += f" (maximum {max_selections})"
        
        super().__init__(message)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if value is None:
            value = []
        
        if not isinstance(value, list):
            return ValidationResult(
                is_valid=False,
                message="Must be a list of values",
                severity=self.severity
            )
        
        # Check if all values are valid choices
        for v in value:
            if v not in self.choices:
                return ValidationResult(
                    is_valid=False,
                    message=f"Invalid choice: {v}",
                    severity=self.severity
                )
        
        # Check selection count
        count = len(value)
        if count < self.min_selections:
            return ValidationResult(
                is_valid=False,
                message=f"Must select at least {self.min_selections} options",
                severity=self.severity
            )
        
        if self.max_selections is not None and count > self.max_selections:
            return ValidationResult(
                is_valid=False,
                message=f"Must select at most {self.max_selections} options",
                severity=self.severity
            )
        
        return ValidationResult(is_valid=True)


class CustomRule(ValidationRule):
    """Rule that uses a custom validation function."""
    
    def __init__(self, validator_func: Callable[[Any, Optional[Dict[str, Any]]], bool], 
                 message: str = "Validation failed"):
        super().__init__(message)
        self.validator_func = validator_func
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        try:
            is_valid = self.validator_func(value, context)
            return ValidationResult(
                is_valid=is_valid,
                message=self.message if not is_valid else "",
                severity=self.severity
            )
        except Exception as e:
            logger.error(f"Error in custom validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                message=f"Validation error: {str(e)}",
                severity=self.severity
            )


class FormValidator:
    """
    Form validator that applies multiple validation rules.
    
    Provides a centralized way to validate form fields with multiple rules.
    """
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
    
    def add_rule(self, field_name: str, rule: ValidationRule) -> None:
        """Add a validation rule for a field."""
        if field_name not in self.rules:
            self.rules[field_name] = []
        self.rules[field_name].append(rule)
    
    def add_rules(self, field_name: str, rules: List[ValidationRule]) -> None:
        """Add multiple validation rules for a field."""
        for rule in rules:
            self.add_rule(field_name, rule)
    
    def validate_field(self, field_name: str, value: Any, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """
        Validate a single field.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
            context: Additional context for validation
            
        Returns:
            List of validation results
        """
        results = []
        field_rules = self.rules.get(field_name, [])
        
        for rule in field_rules:
            result = rule.validate(value, context)
            if not result.is_valid or result.message:  # Include warnings and info messages
                results.append(result)
        
        return results
    
    def validate_form(self, form_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, List[ValidationResult]]:
        """
        Validate entire form data.
        
        Args:
            form_data: Dictionary of field names to values
            context: Additional context for validation
            
        Returns:
            Dictionary of field names to list of validation results
        """
        results = {}
        
        # Validate fields that have data
        for field_name, value in form_data.items():
            field_results = self.validate_field(field_name, value, context)
            if field_results:
                results[field_name] = field_results
        
        # Check for required fields that are missing
        for field_name, rules in self.rules.items():
            if field_name not in form_data:
                # Check if any rule is a required rule
                for rule in rules:
                    if isinstance(rule, RequiredRule):
                        result = rule.validate(None, context)
                        if not result.is_valid:
                            if field_name not in results:
                                results[field_name] = []
                            results[field_name].append(result)
                        break
        
        return results
    
    def is_valid(self, form_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if form data is valid.
        
        Args:
            form_data: Dictionary of field names to values
            context: Additional context for validation
            
        Returns:
            True if all validations pass, False otherwise
        """
        results = self.validate_form(form_data, context)
        
        # Check if there are any error-level validation failures
        for field_results in results.values():
            for result in field_results:
                if not result.is_valid and result.severity == ValidationSeverity.ERROR:
                    return False
        
        return True
    
    def get_error_messages(self, form_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Get error messages for form validation.
        
        Args:
            form_data: Dictionary of field names to values
            context: Additional context for validation
            
        Returns:
            Dictionary of field names to list of error messages
        """
        results = self.validate_form(form_data, context)
        error_messages = {}
        
        for field_name, field_results in results.items():
            errors = [result.message for result in field_results 
                     if not result.is_valid and result.severity == ValidationSeverity.ERROR and result.message]
            if errors:
                error_messages[field_name] = errors
        
        return error_messages


# Predefined validators for common use cases
def create_business_validator() -> FormValidator:
    """Create a validator for business requirements."""
    validator = FormValidator()
    
    # Company name validation
    validator.add_rules("company_name", [
        RequiredRule("Company name is required"),
        LengthRule(min_length=2, max_length=100, message="Company name must be between 2 and 100 characters")
    ])
    
    # Industry validation
    validator.add_rule("industry", RequiredRule("Industry selection is required"))
    
    # Company size validation
    validator.add_rule("company_size", RequiredRule("Company size is required"))
    
    # Budget validation
    validator.add_rules("budget_range", [
        RequiredRule("Budget range is required"),
        ChoiceRule(["under_10k", "10k_50k", "50k_100k", "100k_500k", "500k_1m", "over_1m"])
    ])
    
    # Timeline validation
    validator.add_rule("timeline", RequiredRule("Timeline is required"))
    
    # Contact email validation
    validator.add_rules("contact_email", [
        RequiredRule("Contact email is required"),
        EmailRule("Please enter a valid email address")
    ])
    
    return validator


def create_technical_validator() -> FormValidator:
    """Create a validator for technical requirements."""
    validator = FormValidator()
    
    # Current infrastructure validation
    validator.add_rule("current_infrastructure", RequiredRule("Current infrastructure information is required"))
    
    # Cloud providers validation
    validator.add_rule("preferred_cloud_providers", 
                      MultiChoiceRule(["aws", "azure", "gcp", "other"], min_selections=1, 
                                    message="Please select at least one cloud provider"))
    
    # Workload types validation
    validator.add_rule("workload_types", 
                      MultiChoiceRule(["web_applications", "data_processing", "machine_learning", 
                                     "databases", "apis", "batch_processing", "real_time_processing"], 
                                    min_selections=1, message="Please select at least one workload type"))
    
    # Performance requirements validation
    validator.add_rules("expected_users", [
        RequiredRule("Expected number of users is required"),
        RangeRule(min_value=1, max_value=10000000, message="Expected users must be between 1 and 10,000,000")
    ])
    
    # Data volume validation
    validator.add_rule("data_volume", RequiredRule("Data volume estimate is required"))
    
    # Compliance requirements validation (optional)
    validator.add_rule("compliance_requirements", 
                      MultiChoiceRule(["gdpr", "hipaa", "sox", "pci_dss", "iso_27001", "none"], 
                                    min_selections=0, max_selections=None))
    
    return validator