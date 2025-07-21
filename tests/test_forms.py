"""
Tests for the form system.

Tests form creation, validation, multi-step functionality, and assessment generation.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.infra_mind.forms import (
    BaseForm,
    FormField,
    FormStep,
    FormFieldType,
    FormValidationError,
    AssessmentForm,
    BusinessRequirementsForm,
    TechnicalRequirementsForm,
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


class TestFormField:
    """Test suite for FormField."""
    
    def test_form_field_creation(self):
        """Test creating a form field."""
        field = FormField(
            name="test_field",
            label="Test Field",
            field_type=FormFieldType.TEXT,
            required=True,
            placeholder="Enter text"
        )
        
        assert field.name == "test_field"
        assert field.label == "Test Field"
        assert field.field_type == FormFieldType.TEXT
        assert field.required is True
        assert field.placeholder == "Enter text"
    
    def test_field_validation_required(self):
        """Test required field validation."""
        field = FormField(
            name="required_field",
            label="Required Field",
            field_type=FormFieldType.TEXT,
            required=True
        )
        
        # Test empty value
        with pytest.raises(FormValidationError) as exc_info:
            field.validate_value("")
        assert "required" in str(exc_info.value).lower()
        
        # Test valid value
        assert field.validate_value("valid text") is True
    
    def test_field_validation_email(self):
        """Test email field validation."""
        field = FormField(
            name="email_field",
            label="Email Field",
            field_type=FormFieldType.EMAIL,
            required=True
        )
        
        # Test valid email
        assert field.validate_value("test@example.com") is True
        
        # Test invalid email
        with pytest.raises(FormValidationError) as exc_info:
            field.validate_value("invalid-email")
        assert "email" in str(exc_info.value).lower()
    
    def test_field_validation_number(self):
        """Test number field validation."""
        field = FormField(
            name="number_field",
            label="Number Field",
            field_type=FormFieldType.NUMBER,
            min_value=1,
            max_value=100
        )
        
        # Test valid number
        assert field.validate_value(50) is True
        assert field.validate_value("25") is True
        
        # Test out of range
        with pytest.raises(FormValidationError):
            field.validate_value(150)
        
        with pytest.raises(FormValidationError):
            field.validate_value(-5)
        
        # Test invalid number
        with pytest.raises(FormValidationError):
            field.validate_value("not a number")
    
    def test_field_validation_select(self):
        """Test select field validation."""
        field = FormField(
            name="select_field",
            label="Select Field",
            field_type=FormFieldType.SELECT,
            options=[
                {"value": "option1", "label": "Option 1"},
                {"value": "option2", "label": "Option 2"}
            ]
        )
        
        # Test valid selection
        assert field.validate_value("option1") is True
        
        # Test invalid selection
        with pytest.raises(FormValidationError):
            field.validate_value("invalid_option")
    
    def test_field_validation_multiselect(self):
        """Test multiselect field validation."""
        field = FormField(
            name="multiselect_field",
            label="Multiselect Field",
            field_type=FormFieldType.MULTISELECT,
            options=[
                {"value": "option1", "label": "Option 1"},
                {"value": "option2", "label": "Option 2"},
                {"value": "option3", "label": "Option 3"}
            ]
        )
        
        # Test valid selections
        assert field.validate_value(["option1", "option2"]) is True
        assert field.validate_value([]) is True
        
        # Test invalid selection
        with pytest.raises(FormValidationError):
            field.validate_value(["option1", "invalid_option"])
        
        # Test non-list value
        with pytest.raises(FormValidationError):
            field.validate_value("not a list")
    
    def test_field_to_dict(self):
        """Test field serialization."""
        field = FormField(
            name="test_field",
            label="Test Field",
            field_type=FormFieldType.TEXT,
            required=True,
            min_length=5,
            max_length=50
        )
        
        field_dict = field.to_dict()
        
        assert field_dict["name"] == "test_field"
        assert field_dict["label"] == "Test Field"
        assert field_dict["field_type"] == "text"
        assert field_dict["required"] is True
        assert field_dict["min_length"] == 5
        assert field_dict["max_length"] == 50


class TestFormStep:
    """Test suite for FormStep."""
    
    def test_form_step_creation(self):
        """Test creating a form step."""
        step = FormStep(
            id="test_step",
            title="Test Step",
            description="Test step description",
            order=1
        )
        
        assert step.id == "test_step"
        assert step.title == "Test Step"
        assert step.description == "Test step description"
        assert step.order == 1
        assert len(step.fields) == 0
    
    def test_add_field(self):
        """Test adding fields to a step."""
        step = FormStep(id="test_step", title="Test Step")
        
        field = FormField(
            name="test_field",
            label="Test Field",
            field_type=FormFieldType.TEXT
        )
        
        step.add_field(field)
        
        assert len(step.fields) == 1
        assert step.fields[0] == field
    
    def test_get_field(self):
        """Test getting a field by name."""
        step = FormStep(id="test_step", title="Test Step")
        
        field = FormField(
            name="test_field",
            label="Test Field",
            field_type=FormFieldType.TEXT
        )
        
        step.add_field(field)
        
        retrieved_field = step.get_field("test_field")
        assert retrieved_field == field
        
        missing_field = step.get_field("missing_field")
        assert missing_field is None
    
    def test_validate_step_data(self):
        """Test step data validation."""
        step = FormStep(id="test_step", title="Test Step")
        
        # Add required field
        required_field = FormField(
            name="required_field",
            label="Required Field",
            field_type=FormFieldType.TEXT,
            required=True
        )
        step.add_field(required_field)
        
        # Add email field
        email_field = FormField(
            name="email_field",
            label="Email Field",
            field_type=FormFieldType.EMAIL
        )
        step.add_field(email_field)
        
        # Test valid data
        valid_data = {
            "required_field": "valid text",
            "email_field": "test@example.com"
        }
        errors = step.validate_step_data(valid_data)
        assert len(errors) == 0
        
        # Test invalid data
        invalid_data = {
            "required_field": "",  # Required field empty
            "email_field": "invalid-email"  # Invalid email
        }
        errors = step.validate_step_data(invalid_data)
        assert "required_field" in errors
        assert "email_field" in errors
    
    def test_step_to_dict(self):
        """Test step serialization."""
        step = FormStep(
            id="test_step",
            title="Test Step",
            description="Test description",
            order=1
        )
        
        field = FormField(
            name="test_field",
            label="Test Field",
            field_type=FormFieldType.TEXT
        )
        step.add_field(field)
        
        step_dict = step.to_dict()
        
        assert step_dict["id"] == "test_step"
        assert step_dict["title"] == "Test Step"
        assert step_dict["description"] == "Test description"
        assert step_dict["order"] == 1
        assert len(step_dict["fields"]) == 1
        assert step_dict["fields"][0]["name"] == "test_field"


class MockForm(BaseForm):
    """Mock form for testing BaseForm functionality."""
    
    def _initialize_form(self):
        """Initialize a simple test form."""
        step1 = FormStep(id="step1", title="Step 1", order=1)
        step1.add_field(FormField(
            name="field1",
            label="Field 1",
            field_type=FormFieldType.TEXT,
            required=True
        ))
        self.add_step(step1)
        
        step2 = FormStep(id="step2", title="Step 2", order=2)
        step2.add_field(FormField(
            name="field2",
            label="Field 2",
            field_type=FormFieldType.NUMBER
        ))
        self.add_step(step2)


class TestBaseForm:
    """Test suite for BaseForm."""
    
    def test_form_creation(self):
        """Test creating a form."""
        form = MockForm()
        
        assert form.form_id is not None
        assert len(form.steps) == 2
        assert form.current_step_index == 0
        assert len(form.form_data) == 0
    
    def test_get_current_step(self):
        """Test getting the current step."""
        form = MockForm()
        
        current_step = form.get_current_step()
        assert current_step is not None
        assert current_step.id == "step1"
    
    def test_step_navigation(self):
        """Test step navigation."""
        form = MockForm()
        
        # Initially on step 1
        assert form.current_step_index == 0
        assert form.get_current_step().id == "step1"
        
        # Cannot proceed without completing current step
        assert form.can_proceed_to_next_step() is False
        assert form.proceed_to_next_step() is False
        
        # Complete step 1
        form.submit_step("step1", {"field1": "test value"})
        
        # Now can proceed
        assert form.can_proceed_to_next_step() is True
        assert form.proceed_to_next_step() is True
        assert form.current_step_index == 1
        assert form.get_current_step().id == "step2"
        
        # Can go back
        assert form.go_to_previous_step() is True
        assert form.current_step_index == 0
    
    def test_submit_step(self):
        """Test submitting step data."""
        form = MockForm()
        
        # Submit valid data
        success = form.submit_step("step1", {"field1": "test value"})
        assert success is True
        assert form.form_data["field1"] == "test value"
        assert form.step_completion["step1"] is True
        
        # Submit invalid data
        success = form.submit_step("step2", {"field2": "not a number"})
        assert success is False
        assert form.step_completion.get("step2", False) is False
    
    def test_form_completion(self):
        """Test form completion tracking."""
        form = MockForm()
        
        # Initially not complete
        assert form.is_form_complete() is False
        assert form.get_completion_percentage() == 0.0
        
        # Complete step 1
        form.submit_step("step1", {"field1": "test value"})
        assert form.get_completion_percentage() == 50.0
        
        # Complete step 2
        form.submit_step("step2", {"field2": 42})
        assert form.is_form_complete() is True
        assert form.get_completion_percentage() == 100.0
    
    def test_form_summary(self):
        """Test getting form summary."""
        form = MockForm()
        
        summary = form.get_form_summary()
        
        assert summary["form_id"] == form.form_id
        assert summary["total_steps"] == 2
        assert summary["current_step_index"] == 0
        assert summary["completion_percentage"] == 0.0
        assert summary["is_complete"] is False
        assert summary["has_errors"] is False
    
    def test_clear_form_data(self):
        """Test clearing form data."""
        form = MockForm()
        
        # Add some data
        form.submit_step("step1", {"field1": "test value"})
        form.proceed_to_next_step()
        
        assert len(form.form_data) > 0
        assert form.current_step_index == 1
        
        # Clear data
        form.clear_form_data()
        
        assert len(form.form_data) == 0
        assert form.current_step_index == 0
        assert all(not completed for completed in form.step_completion.values())


class TestValidationRules:
    """Test suite for validation rules."""
    
    def test_required_rule(self):
        """Test required validation rule."""
        rule = RequiredRule("Field is required")
        
        # Test valid values
        result = rule.validate("valid value")
        assert result.is_valid is True
        
        result = rule.validate(42)
        assert result.is_valid is True
        
        result = rule.validate([1, 2, 3])
        assert result.is_valid is True
        
        # Test invalid values
        result = rule.validate("")
        assert result.is_valid is False
        assert "required" in result.message.lower()
        
        result = rule.validate(None)
        assert result.is_valid is False
        
        result = rule.validate([])
        assert result.is_valid is False
    
    def test_email_rule(self):
        """Test email validation rule."""
        rule = EmailRule("Invalid email")
        
        # Test valid emails
        result = rule.validate("test@example.com")
        assert result.is_valid is True
        
        result = rule.validate("user.name+tag@domain.co.uk")
        assert result.is_valid is True
        
        # Test invalid emails
        result = rule.validate("invalid-email")
        assert result.is_valid is False
        
        result = rule.validate("@domain.com")
        assert result.is_valid is False
        
        result = rule.validate("user@")
        assert result.is_valid is False
        
        # Test empty value (should be valid - let RequiredRule handle)
        result = rule.validate("")
        assert result.is_valid is True
    
    def test_range_rule(self):
        """Test range validation rule."""
        rule = RangeRule(min_value=1, max_value=100)
        
        # Test valid values
        result = rule.validate(50)
        assert result.is_valid is True
        
        result = rule.validate("25")
        assert result.is_valid is True
        
        result = rule.validate(1)  # Min boundary
        assert result.is_valid is True
        
        result = rule.validate(100)  # Max boundary
        assert result.is_valid is True
        
        # Test invalid values
        result = rule.validate(0)
        assert result.is_valid is False
        
        result = rule.validate(101)
        assert result.is_valid is False
        
        result = rule.validate("not a number")
        assert result.is_valid is False
    
    def test_length_rule(self):
        """Test length validation rule."""
        rule = LengthRule(min_length=3, max_length=10)
        
        # Test valid values
        result = rule.validate("hello")
        assert result.is_valid is True
        
        result = rule.validate("abc")  # Min boundary
        assert result.is_valid is True
        
        result = rule.validate("1234567890")  # Max boundary
        assert result.is_valid is True
        
        # Test invalid values
        result = rule.validate("ab")  # Too short
        assert result.is_valid is False
        
        result = rule.validate("12345678901")  # Too long
        assert result.is_valid is False
    
    def test_choice_rule(self):
        """Test choice validation rule."""
        rule = ChoiceRule(["option1", "option2", "option3"])
        
        # Test valid choices
        result = rule.validate("option1")
        assert result.is_valid is True
        
        result = rule.validate("option2")
        assert result.is_valid is True
        
        # Test invalid choice
        result = rule.validate("invalid_option")
        assert result.is_valid is False
        
        # Test empty value
        result = rule.validate("")
        assert result.is_valid is True
    
    def test_multi_choice_rule(self):
        """Test multi-choice validation rule."""
        rule = MultiChoiceRule(["option1", "option2", "option3"], min_selections=1, max_selections=2)
        
        # Test valid selections
        result = rule.validate(["option1"])
        assert result.is_valid is True
        
        result = rule.validate(["option1", "option2"])
        assert result.is_valid is True
        
        # Test invalid selections
        result = rule.validate([])  # Too few
        assert result.is_valid is False
        
        result = rule.validate(["option1", "option2", "option3"])  # Too many
        assert result.is_valid is False
        
        result = rule.validate(["option1", "invalid_option"])  # Invalid choice
        assert result.is_valid is False
        
        result = rule.validate("not a list")  # Not a list
        assert result.is_valid is False
    
    def test_custom_rule(self):
        """Test custom validation rule."""
        def is_even(value, context=None):
            try:
                return int(value) % 2 == 0
            except (ValueError, TypeError):
                return False
        
        rule = CustomRule(is_even, "Must be an even number")
        
        # Test valid values
        result = rule.validate(2)
        assert result.is_valid is True
        
        result = rule.validate("4")
        assert result.is_valid is True
        
        # Test invalid values
        result = rule.validate(3)
        assert result.is_valid is False
        
        result = rule.validate("not a number")
        assert result.is_valid is False


class TestFormValidator:
    """Test suite for FormValidator."""
    
    def test_add_rules(self):
        """Test adding validation rules."""
        validator = FormValidator()
        
        validator.add_rule("field1", RequiredRule())
        validator.add_rule("field1", LengthRule(min_length=3))
        
        assert len(validator.rules["field1"]) == 2
    
    def test_validate_field(self):
        """Test field validation."""
        validator = FormValidator()
        validator.add_rule("test_field", RequiredRule("Field is required"))
        validator.add_rule("test_field", LengthRule(min_length=3, message="Too short"))
        
        # Test valid value
        results = validator.validate_field("test_field", "valid")
        assert len(results) == 0  # No errors
        
        # Test invalid value
        results = validator.validate_field("test_field", "ab")
        assert len(results) == 1
        assert not results[0].is_valid
        assert "short" in results[0].message.lower()
        
        # Test empty value
        results = validator.validate_field("test_field", "")
        assert len(results) == 1
        assert not results[0].is_valid
        assert "required" in results[0].message.lower()
    
    def test_validate_form(self):
        """Test form validation."""
        validator = FormValidator()
        validator.add_rule("field1", RequiredRule())
        validator.add_rule("field2", EmailRule())
        
        # Test valid form data
        form_data = {
            "field1": "valid value",
            "field2": "test@example.com"
        }
        results = validator.validate_form(form_data)
        assert len(results) == 0
        
        # Test invalid form data
        form_data = {
            "field1": "",  # Required field empty
            "field2": "invalid-email"  # Invalid email
        }
        results = validator.validate_form(form_data)
        assert "field1" in results
        assert "field2" in results
    
    def test_is_valid(self):
        """Test form validity check."""
        validator = FormValidator()
        validator.add_rule("field1", RequiredRule())
        validator.add_rule("field2", EmailRule())
        
        # Test valid data
        valid_data = {
            "field1": "valid value",
            "field2": "test@example.com"
        }
        assert validator.is_valid(valid_data) is True
        
        # Test invalid data
        invalid_data = {
            "field1": "",
            "field2": "invalid-email"
        }
        assert validator.is_valid(invalid_data) is False


class TestBusinessRequirementsForm:
    """Test suite for BusinessRequirementsForm."""
    
    def test_form_creation(self):
        """Test creating business requirements form."""
        form = BusinessRequirementsForm()
        
        assert len(form.steps) == 3
        assert form.steps[0].id == "company_info"
        assert form.steps[1].id == "business_goals"
        assert form.steps[2].id == "current_state"
    
    def test_company_info_step(self):
        """Test company info step."""
        form = BusinessRequirementsForm()
        
        # Get company info step
        step = form.get_step("company_info")
        assert step is not None
        assert step.title == "Company Information"
        
        # Check required fields
        company_name_field = step.get_field("company_name")
        assert company_name_field is not None
        assert company_name_field.required is True
        
        industry_field = step.get_field("industry")
        assert industry_field is not None
        assert industry_field.field_type == FormFieldType.SELECT
        assert len(industry_field.options) > 0
    
    def test_submit_valid_data(self):
        """Test submitting valid business data."""
        form = BusinessRequirementsForm()
        
        # Submit company info
        company_data = {
            "company_name": "Test Company",
            "industry": "technology",
            "company_size": "medium",
            "contact_email": "test@company.com"
        }
        
        success = form.submit_step("company_info", company_data)
        assert success is True
        assert form.step_completion["company_info"] is True


class TestTechnicalRequirementsForm:
    """Test suite for TechnicalRequirementsForm."""
    
    def test_form_creation(self):
        """Test creating technical requirements form."""
        form = TechnicalRequirementsForm()
        
        assert len(form.steps) == 3
        assert form.steps[0].id == "current_infrastructure"
        assert form.steps[1].id == "workload_requirements"
        assert form.steps[2].id == "cloud_preferences"
    
    def test_workload_requirements_step(self):
        """Test workload requirements step."""
        form = TechnicalRequirementsForm()
        
        # Get workload step
        step = form.get_step("workload_requirements")
        assert step is not None
        
        # Check expected users field
        users_field = step.get_field("expected_users")
        assert users_field is not None
        assert users_field.field_type == FormFieldType.NUMBER
        assert users_field.required is True


class TestAssessmentForm:
    """Test suite for AssessmentForm."""
    
    def test_form_creation(self):
        """Test creating complete assessment form."""
        form = AssessmentForm()
        
        # Should have both business and technical steps
        assert len(form.steps) == 6  # 3 business + 3 technical
        
        # Check step IDs
        step_ids = [step.id for step in form.steps]
        assert "business_company_info" in step_ids
        assert "technical_current_infrastructure" in step_ids
    
    def test_create_assessment_incomplete(self):
        """Test creating assessment from incomplete form."""
        form = AssessmentForm()
        
        # Try to create assessment without completing form
        assessment = form.create_assessment()
        assert assessment is None
    
    @patch('src.infra_mind.models.assessment.Assessment')
    @patch('src.infra_mind.models.assessment.BusinessRequirements')
    @patch('src.infra_mind.models.assessment.TechnicalRequirements')
    @patch('src.infra_mind.models.assessment.ComplianceRequirements')
    def test_create_assessment_complete(self, mock_compliance, mock_technical, mock_business, mock_assessment):
        """Test creating assessment from complete form."""
        form = AssessmentForm()
        
        # Mock the form as complete
        form.step_completion = {step.id: True for step in form.steps}
        form.form_data = {
            "company_name": "Test Company",
            "industry": "technology",
            "workload_types": ["web_applications"],
            "compliance_requirements": ["gdpr"]
        }
        
        # Mock the model constructors
        mock_business.return_value = Mock()
        mock_technical.return_value = Mock()
        mock_compliance.return_value = Mock()
        mock_assessment_instance = Mock()
        mock_assessment_instance.id = "test_assessment_id"
        mock_assessment.return_value = mock_assessment_instance
        
        # Create assessment
        assessment = form.create_assessment()
        
        # Verify assessment was created
        assert assessment is not None
        mock_assessment.assert_called_once()


class TestValidatorCreation:
    """Test suite for validator creation functions."""
    
    def test_create_business_validator(self):
        """Test creating business validator."""
        validator = create_business_validator()
        
        assert isinstance(validator, FormValidator)
        assert "company_name" in validator.rules
        assert "industry" in validator.rules
        assert "budget_range" in validator.rules
    
    def test_create_technical_validator(self):
        """Test creating technical validator."""
        validator = create_technical_validator()
        
        assert isinstance(validator, FormValidator)
        assert "current_infrastructure" in validator.rules
        assert "preferred_cloud_providers" in validator.rules
        assert "workload_types" in validator.rules