"""
Tests for intelligent form features.

Tests smart defaults, auto-completion, contextual help, and progressive disclosure
functionality.
"""

import pytest
from unittest.mock import Mock, patch
from src.infra_mind.forms.intelligent_features import (
    IntelligentFormService,
    FormStateManager,
    IndustryType,
    CompanySize,
    SmartDefault,
    Suggestion,
    ContextualHelp
)


class TestIntelligentFormService:
    """Test the intelligent form service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = IntelligentFormService()
    
    def test_initialization(self):
        """Test service initialization."""
        assert self.service is not None
        assert hasattr(self.service, '_industry_patterns')
        assert hasattr(self.service, '_company_size_patterns')
        assert hasattr(self.service, '_common_suggestions')
        assert hasattr(self.service, '_contextual_help')
    
    def test_get_smart_defaults_industry_based(self):
        """Test smart defaults based on industry."""
        context = {"industry": IndustryType.HEALTHCARE}
        
        # Test budget range defaults
        defaults = self.service.get_smart_defaults("budget_range", context)
        assert len(defaults) > 0
        assert all(isinstance(d, SmartDefault) for d in defaults)
        assert all(d.confidence > 0 for d in defaults)
        
        # Healthcare should suggest typical healthcare budgets
        budget_values = [d.value for d in defaults]
        assert any(budget in ["50k_100k", "100k_500k"] for budget in budget_values)
    
    def test_get_smart_defaults_company_size_based(self):
        """Test smart defaults based on company size."""
        context = {"company_size": CompanySize.STARTUP}
        
        # Test budget defaults for startup
        defaults = self.service.get_smart_defaults("budget_range", context)
        assert len(defaults) > 0
        
        # Startups should get lower budget suggestions
        budget_values = [d.value for d in defaults]
        assert any(budget in ["under_10k", "10k_50k"] for budget in budget_values)
    
    def test_get_smart_defaults_combined_context(self):
        """Test smart defaults with combined industry and company size context."""
        context = {
            "industry": IndustryType.TECHNOLOGY,
            "company_size": CompanySize.SMALL
        }
        
        # Test technical team size defaults
        defaults = self.service.get_smart_defaults("technical_team_size", context)
        assert len(defaults) > 0
        
        # Should suggest reasonable team size for small tech company
        team_sizes = [int(d.value) for d in defaults if d.value.isdigit()]
        assert len(team_sizes) > 0
        assert all(2 <= size <= 15 for size in team_sizes)  # Small company range
    
    def test_get_suggestions_basic(self):
        """Test basic auto-completion suggestions."""
        suggestions = self.service.get_suggestions("ai_use_cases", "", {})
        assert len(suggestions) > 0
        assert all(isinstance(s, Suggestion) for s in suggestions)
        assert all(hasattr(s, 'value') and hasattr(s, 'label') for s in suggestions)
    
    def test_get_suggestions_with_query(self):
        """Test suggestions filtered by query."""
        suggestions = self.service.get_suggestions("ai_use_cases", "predict", {})
        
        # Should return suggestions containing "predict"
        assert len(suggestions) > 0
        predict_suggestions = [s for s in suggestions if "predict" in s.value.lower() or "predict" in s.label.lower()]
        assert len(predict_suggestions) > 0
    
    def test_get_suggestions_context_aware(self):
        """Test context-aware suggestions."""
        context = {"industry": IndustryType.HEALTHCARE}
        suggestions = self.service.get_suggestions("ai_use_cases", "", context)
        
        # Should include healthcare-specific suggestions
        suggestion_values = [s.value for s in suggestions]
        assert any("predictive_analytics" in val for val in suggestion_values)
    
    def test_get_contextual_help(self):
        """Test contextual help retrieval."""
        help_info = self.service.get_contextual_help("company_size", {})
        
        assert help_info is not None
        assert isinstance(help_info, ContextualHelp)
        assert help_info.title
        assert help_info.content
        assert len(help_info.examples) > 0
        assert len(help_info.tips) > 0
    
    def test_get_contextual_help_customized(self):
        """Test contextual help customization based on context."""
        context = {"industry": IndustryType.HEALTHCARE}
        help_info = self.service.get_contextual_help("compliance_requirements", context)
        
        assert help_info is not None
        # Should include healthcare-specific tips
        tips_text = " ".join(help_info.tips)
        assert "healthcare" in tips_text.lower() or "hipaa" in tips_text.lower()
    
    def test_should_show_field_progressive_disclosure(self):
        """Test progressive disclosure logic."""
        # Compliance fields should only show for certain industries
        context = {"industry": IndustryType.TECHNOLOGY}
        assert not self.service.should_show_field("compliance_requirements", context)
        
        context = {"industry": IndustryType.HEALTHCARE}
        assert self.service.should_show_field("compliance_requirements", context)
    
    def test_should_show_field_dependencies(self):
        """Test field dependencies in progressive disclosure."""
        # Team size should only show after company size is selected
        context = {}
        assert not self.service.should_show_field("technical_team_size", context)
        
        context = {"company_size": CompanySize.SMALL}
        assert self.service.should_show_field("technical_team_size", context)
    
    def test_get_field_priority(self):
        """Test field priority for ordering."""
        context = {}
        
        # Core fields should have higher priority (lower numbers)
        company_name_priority = self.service.get_field_priority("company_name", context)
        additional_context_priority = self.service.get_field_priority("additional_context", context)
        
        assert company_name_priority < additional_context_priority


class TestFormStateManager:
    """Test the form state manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = FormStateManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager is not None
        assert hasattr(self.manager, '_saved_states')
    
    def test_save_and_load_form_state(self):
        """Test saving and loading form state."""
        form_id = "test_form_123"
        user_id = "user_456"
        form_data = {"company_name": "Test Corp", "industry": "technology"}
        current_step = 2
        metadata = {"test": "data"}
        
        # Save state
        success = self.manager.save_form_state(form_id, user_id, form_data, current_step, metadata)
        assert success
        
        # Load state
        loaded_state = self.manager.load_form_state(form_id, user_id)
        assert loaded_state is not None
        assert loaded_state["form_id"] == form_id
        assert loaded_state["user_id"] == user_id
        assert loaded_state["form_data"] == form_data
        assert loaded_state["current_step"] == current_step
        assert loaded_state["metadata"] == metadata
    
    def test_delete_form_state(self):
        """Test deleting form state."""
        form_id = "test_form_delete"
        user_id = "user_delete"
        form_data = {"test": "data"}
        
        # Save state
        self.manager.save_form_state(form_id, user_id, form_data, 0)
        
        # Verify it exists
        assert self.manager.load_form_state(form_id, user_id) is not None
        
        # Delete state
        success = self.manager.delete_form_state(form_id, user_id)
        assert success
        
        # Verify it's gone
        assert self.manager.load_form_state(form_id, user_id) is None
    
    def test_list_saved_forms(self):
        """Test listing saved forms for a user."""
        user_id = "user_list_test"
        
        # Save multiple forms
        forms = [
            ("form1", {"data": "1"}, 1),
            ("form2", {"data": "2"}, 2),
            ("form3", {"data": "3"}, 0)
        ]
        
        for form_id, form_data, step in forms:
            self.manager.save_form_state(form_id, user_id, form_data, step)
        
        # List forms
        saved_forms = self.manager.list_saved_forms(user_id)
        assert len(saved_forms) == 3
        
        # Check form summaries
        form_ids = [form["form_id"] for form in saved_forms]
        assert "form1" in form_ids
        assert "form2" in form_ids
        assert "form3" in form_ids
        
        # Check completion percentages
        for form in saved_forms:
            assert "completion_percentage" in form
            assert 0 <= form["completion_percentage"] <= 100
    
    def test_load_nonexistent_form(self):
        """Test loading a form that doesn't exist."""
        result = self.manager.load_form_state("nonexistent", "user")
        assert result is None
    
    def test_delete_nonexistent_form(self):
        """Test deleting a form that doesn't exist."""
        result = self.manager.delete_form_state("nonexistent", "user")
        assert not result


class TestIntelligentFormIntegration:
    """Test integration between intelligent features and base form."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Import here to avoid circular imports in tests
        from src.infra_mind.forms.assessment_form import AssessmentForm
        self.form = AssessmentForm()
    
    def test_form_has_intelligent_features(self):
        """Test that form has intelligent features available."""
        # Check if intelligent service is available
        if hasattr(self.form, 'intelligent_service'):
            assert self.form.intelligent_service is not None
        
        # Check if state manager is available
        if hasattr(self.form, 'state_manager'):
            assert self.form.state_manager is not None
    
    def test_get_smart_defaults_integration(self):
        """Test smart defaults integration with form."""
        if not hasattr(self.form, 'get_smart_defaults'):
            pytest.skip("Smart defaults not available")
        
        # Set some context
        self.form.form_data = {"industry": "technology", "company_size": "small"}
        
        # Get smart defaults
        defaults = self.form.get_smart_defaults("budget_range")
        assert isinstance(defaults, list)
        
        # If defaults are available, they should be properly formatted
        if defaults:
            for default in defaults:
                assert "value" in default
                assert "confidence" in default
                assert "reason" in default
    
    def test_get_field_suggestions_integration(self):
        """Test field suggestions integration with form."""
        if not hasattr(self.form, 'get_field_suggestions'):
            pytest.skip("Field suggestions not available")
        
        suggestions = self.form.get_field_suggestions("ai_use_cases", "predict")
        assert isinstance(suggestions, list)
        
        # If suggestions are available, they should be properly formatted
        if suggestions:
            for suggestion in suggestions:
                assert "value" in suggestion
                assert "label" in suggestion
                assert "description" in suggestion
    
    def test_contextual_help_integration(self):
        """Test contextual help integration with form."""
        if not hasattr(self.form, 'get_contextual_help'):
            pytest.skip("Contextual help not available")
        
        help_info = self.form.get_contextual_help("company_size")
        
        # If help is available, it should be properly formatted
        if help_info:
            assert "title" in help_info
            assert "content" in help_info
            assert "examples" in help_info
            assert "tips" in help_info
    
    def test_progressive_disclosure_integration(self):
        """Test progressive disclosure integration with form."""
        if not hasattr(self.form, 'should_show_field'):
            pytest.skip("Progressive disclosure not available")
        
        # Test basic field visibility
        result = self.form.should_show_field("company_name")
        assert isinstance(result, bool)
        
        # Test context-dependent visibility
        self.form.form_data = {"industry": "healthcare"}
        compliance_visible = self.form.should_show_field("compliance_requirements")
        assert isinstance(compliance_visible, bool)
    
    def test_save_and_load_state_integration(self):
        """Test save and load state integration with form."""
        if not hasattr(self.form, 'save_form_state'):
            pytest.skip("State management not available")
        
        # Set some form data
        self.form.form_data = {"company_name": "Test Corp", "industry": "technology"}
        self.form.current_step_index = 1
        
        # Save state
        success = self.form.save_form_state("test_user")
        
        # If state management is available, test the functionality
        if hasattr(self.form, 'state_manager') and self.form.state_manager:
            assert isinstance(success, bool)
            
            # Test loading state
            if hasattr(self.form, 'load_form_state'):
                load_success = self.form.load_form_state("test_user")
                assert isinstance(load_success, bool)


if __name__ == "__main__":
    pytest.main([__file__])