"""
Base form classes and utilities for input collection.

Provides the foundation for multi-step forms with validation and error handling.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Callable, Type
from enum import Enum, auto
from dataclasses import dataclass, field
import uuid

from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)


class FormFieldType(str, Enum):
    """Types of form fields."""
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    SELECT = "select"
    MULTISELECT = "multiselect"
    BOOLEAN = "boolean"
    DATE = "date"
    TEXTAREA = "textarea"
    RANGE = "range"
    FILE = "file"


class FormValidationError(Exception):
    """Exception raised when form validation fails."""
    
    def __init__(self, field_name: str, message: str, value: Any = None):
        self.field_name = field_name
        self.message = message
        self.value = value
        super().__init__(f"Validation error for field '{field_name}': {message}")


@dataclass
class FormField:
    """Definition of a form field."""
    name: str
    label: str
    field_type: FormFieldType
    required: bool = False
    default_value: Any = None
    placeholder: str = ""
    help_text: str = ""
    options: List[Dict[str, Any]] = field(default_factory=list)  # For select/multiselect
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern for validation
    validation_rules: List[Callable[[Any], bool]] = field(default_factory=list)
    depends_on: Optional[str] = None  # Field dependency
    depends_on_value: Any = None  # Value that dependency must have
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value against this field's rules."""
        try:
            # Check required
            if self.required and (value is None or value == ""):
                raise FormValidationError(self.name, "This field is required")
            
            # Skip validation if field is not required and value is empty
            if not self.required and (value is None or value == ""):
                return True
            
            # Type-specific validation
            if self.field_type == FormFieldType.EMAIL:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    raise FormValidationError(self.name, "Invalid email format")
            
            elif self.field_type == FormFieldType.NUMBER:
                try:
                    num_value = float(value)
                    if self.min_value is not None and num_value < self.min_value:
                        raise FormValidationError(self.name, f"Value must be at least {self.min_value}")
                    if self.max_value is not None and num_value > self.max_value:
                        raise FormValidationError(self.name, f"Value must be at most {self.max_value}")
                except (ValueError, TypeError):
                    raise FormValidationError(self.name, "Invalid number format")
            
            elif self.field_type in [FormFieldType.TEXT, FormFieldType.TEXTAREA]:
                str_value = str(value)
                if self.min_length is not None and len(str_value) < self.min_length:
                    raise FormValidationError(self.name, f"Must be at least {self.min_length} characters")
                if self.max_length is not None and len(str_value) > self.max_length:
                    raise FormValidationError(self.name, f"Must be at most {self.max_length} characters")
                
                if self.pattern:
                    import re
                    if not re.match(self.pattern, str_value):
                        raise FormValidationError(self.name, "Invalid format")
            
            elif self.field_type == FormFieldType.SELECT:
                if self.options:
                    valid_values = [opt.get("value") for opt in self.options]
                    if value not in valid_values:
                        raise FormValidationError(self.name, f"Invalid selection. Must be one of: {valid_values}")
            
            elif self.field_type == FormFieldType.MULTISELECT:
                if not isinstance(value, list):
                    raise FormValidationError(self.name, "Must be a list of values")
                if self.options:
                    valid_values = [opt.get("value") for opt in self.options]
                    for v in value:
                        if v not in valid_values:
                            raise FormValidationError(self.name, f"Invalid selection '{v}'. Must be one of: {valid_values}")
            
            # Custom validation rules
            for rule in self.validation_rules:
                if not rule(value):
                    raise FormValidationError(self.name, "Custom validation failed")
            
            return True
            
        except FormValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating field {self.name}: {str(e)}")
            raise FormValidationError(self.name, f"Validation error: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary for serialization."""
        return {
            "name": self.name,
            "label": self.label,
            "field_type": self.field_type.value,
            "required": self.required,
            "default_value": self.default_value,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "options": self.options,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "depends_on": self.depends_on,
            "depends_on_value": self.depends_on_value,
            "metadata": self.metadata
        }


@dataclass
class FormStep:
    """Definition of a form step in a multi-step form."""
    id: str
    title: str
    description: str = ""
    fields: List[FormField] = field(default_factory=list)
    order: int = 0
    is_optional: bool = False
    completion_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_field(self, field: FormField) -> None:
        """Add a field to this step."""
        self.fields.append(field)
    
    def get_field(self, field_name: str) -> Optional[FormField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def validate_step_data(self, data: Dict[str, Any], all_form_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Validate data for this step.
        
        Args:
            data: Data for this step
            all_form_data: All form data (for dependency validation)
            
        Returns:
            Dictionary of field names to list of error messages
        """
        errors = {}
        all_data = all_form_data or {}
        
        for field in self.fields:
            # Check field dependencies
            if field.depends_on:
                dep_value = all_data.get(field.depends_on)
                if dep_value != field.depends_on_value:
                    continue  # Skip validation if dependency not met
            
            field_value = data.get(field.name)
            
            try:
                field.validate_value(field_value)
            except FormValidationError as e:
                if field.name not in errors:
                    errors[field.name] = []
                errors[field.name].append(e.message)
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "fields": [field.to_dict() for field in self.fields],
            "order": self.order,
            "is_optional": self.is_optional,
            "completion_message": self.completion_message,
            "metadata": self.metadata
        }


class BaseForm(ABC):
    """
    Base class for multi-step forms.
    
    Provides common functionality for form management, validation, and data handling.
    """
    
    def __init__(self, form_id: Optional[str] = None):
        """Initialize the form."""
        self.form_id = form_id or str(uuid.uuid4())
        self.steps: List[FormStep] = []
        self.current_step_index = 0
        self.form_data: Dict[str, Any] = {}
        self.step_completion: Dict[str, bool] = {}
        self.validation_errors: Dict[str, Dict[str, List[str]]] = {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.metadata: Dict[str, Any] = {}
        
        # Initialize form structure
        self._initialize_form()
        
        logger.info(f"Initialized form {self.form_id} with {len(self.steps)} steps")
    
    @abstractmethod
    def _initialize_form(self) -> None:
        """Initialize the form structure. Must be implemented by subclasses."""
        pass
    
    def add_step(self, step: FormStep) -> None:
        """Add a step to the form."""
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        self.step_completion[step.id] = False
    
    def get_step(self, step_id: str) -> Optional[FormStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_current_step(self) -> Optional[FormStep]:
        """Get the current step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_next_step(self) -> Optional[FormStep]:
        """Get the next step."""
        next_index = self.current_step_index + 1
        if next_index < len(self.steps):
            return self.steps[next_index]
        return None
    
    def get_previous_step(self) -> Optional[FormStep]:
        """Get the previous step."""
        prev_index = self.current_step_index - 1
        if prev_index >= 0:
            return self.steps[prev_index]
        return None
    
    def can_proceed_to_next_step(self) -> bool:
        """Check if we can proceed to the next step."""
        current_step = self.get_current_step()
        if not current_step:
            return False
        
        # Check if current step is completed
        return self.step_completion.get(current_step.id, False)
    
    def proceed_to_next_step(self) -> bool:
        """Move to the next step if possible."""
        if self.can_proceed_to_next_step() and self.get_next_step():
            self.current_step_index += 1
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False
    
    def go_to_previous_step(self) -> bool:
        """Move to the previous step if possible."""
        if self.get_previous_step():
            self.current_step_index -= 1
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False
    
    def go_to_step(self, step_id: str) -> bool:
        """Go to a specific step by ID."""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                self.current_step_index = i
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False
    
    def validate_step(self, step_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data for a specific step.
        
        Args:
            step_id: ID of the step to validate
            data: Data to validate
            
        Returns:
            Dictionary of field names to list of error messages
        """
        step = self.get_step(step_id)
        if not step:
            return {"form": ["Step not found"]}
        
        errors = step.validate_step_data(data, self.form_data)
        
        # Store validation errors
        self.validation_errors[step_id] = errors
        
        return errors
    
    def submit_step(self, step_id: str, data: Dict[str, Any]) -> bool:
        """
        Submit data for a specific step.
        
        Args:
            step_id: ID of the step
            data: Data to submit
            
        Returns:
            True if submission was successful, False otherwise
        """
        # Validate the step data
        errors = self.validate_step(step_id, data)
        
        if errors:
            logger.warning(f"Validation errors for step {step_id}: {errors}")
            return False
        
        # Update form data
        self.form_data.update(data)
        self.step_completion[step_id] = True
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Successfully submitted step {step_id}")
        return True
    
    def is_form_complete(self) -> bool:
        """Check if the entire form is complete."""
        for step in self.steps:
            if not step.is_optional and not self.step_completion.get(step.id, False):
                return False
        return True
    
    def get_completion_percentage(self) -> float:
        """Get the completion percentage of the form."""
        if not self.steps:
            return 0.0
        
        required_steps = [step for step in self.steps if not step.is_optional]
        if not required_steps:
            return 100.0
        
        completed_required = sum(1 for step in required_steps if self.step_completion.get(step.id, False))
        return (completed_required / len(required_steps)) * 100.0
    
    def get_form_summary(self) -> Dict[str, Any]:
        """Get a summary of the form state."""
        return {
            "form_id": self.form_id,
            "total_steps": len(self.steps),
            "current_step_index": self.current_step_index,
            "current_step_id": self.get_current_step().id if self.get_current_step() else None,
            "completion_percentage": self.get_completion_percentage(),
            "is_complete": self.is_form_complete(),
            "step_completion": self.step_completion.copy(),
            "has_errors": bool(self.validation_errors),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get all form data."""
        return self.form_data.copy()
    
    def clear_form_data(self) -> None:
        """Clear all form data and reset completion status."""
        self.form_data.clear()
        self.step_completion = {step.id: False for step in self.steps}
        self.validation_errors.clear()
        self.current_step_index = 0
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert form to dictionary for serialization."""
        return {
            "form_id": self.form_id,
            "steps": [step.to_dict() for step in self.steps],
            "current_step_index": self.current_step_index,
            "form_data": self.form_data,
            "step_completion": self.step_completion,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseForm":
        """Create form from dictionary."""
        # This is a basic implementation - subclasses should override if needed
        form = cls()
        form.form_id = data.get("form_id", form.form_id)
        form.current_step_index = data.get("current_step_index", 0)
        form.form_data = data.get("form_data", {})
        form.step_completion = data.get("step_completion", {})
        form.validation_errors = data.get("validation_errors", {})
        form.metadata = data.get("metadata", {})
        
        if data.get("created_at"):
            try:
                form.created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
        
        if data.get("updated_at"):
            try:
                form.updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                pass
        
        return form