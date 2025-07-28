#!/usr/bin/env python3
"""
Demo script for intelligent form features.

Demonstrates smart defaults, auto-completion, contextual help, and progressive disclosure
functionality in the assessment forms.
"""

import asyncio
import json
from typing import Dict, Any
from src.infra_mind.forms.intelligent_features import (
    IntelligentFormService,
    FormStateManager,
    IndustryType,
    CompanySize
)
from src.infra_mind.forms.assessment_form import AssessmentForm


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def demo_smart_defaults():
    """Demonstrate smart defaults functionality."""
    print_section("SMART DEFAULTS DEMO")
    
    service = IntelligentFormService()
    
    # Demo 1: Industry-based defaults
    print_subsection("Industry-based Smart Defaults")
    
    contexts = [
        {"industry": IndustryType.HEALTHCARE},
        {"industry": IndustryType.FINANCE},
        {"industry": IndustryType.TECHNOLOGY}
    ]
    
    for context in contexts:
        print(f"\nContext: {context}")
        
        # Get budget range defaults
        budget_defaults = service.get_smart_defaults("budget_range", context)
        print(f"Budget Range Suggestions:")
        for default in budget_defaults:
            print(f"  • {default.value} (confidence: {default.confidence:.1%})")
            print(f"    Reason: {default.reason}")
        
        # Get compliance defaults
        compliance_defaults = service.get_smart_defaults("compliance_requirements", context)
        if compliance_defaults:
            print(f"Compliance Suggestions:")
            for default in compliance_defaults:
                print(f"  • {default.value} (confidence: {default.confidence:.1%})")
                print(f"    Reason: {default.reason}")
    
    # Demo 2: Company size-based defaults
    print_subsection("Company Size-based Smart Defaults")
    
    size_contexts = [
        {"company_size": CompanySize.STARTUP},
        {"company_size": CompanySize.SMALL},
        {"company_size": CompanySize.ENTERPRISE}
    ]
    
    for context in size_contexts:
        print(f"\nContext: {context}")
        
        # Get budget defaults
        budget_defaults = service.get_smart_defaults("budget_range", context)
        print(f"Budget Suggestions:")
        for default in budget_defaults:
            print(f"  • {default.value} (confidence: {default.confidence:.1%})")
        
        # Get infrastructure maturity defaults
        maturity_defaults = service.get_smart_defaults("infrastructure_maturity", context)
        if maturity_defaults:
            print(f"Infrastructure Maturity:")
            for default in maturity_defaults:
                print(f"  • {default.value} (confidence: {default.confidence:.1%})")
    
    # Demo 3: Combined context defaults
    print_subsection("Combined Context Smart Defaults")
    
    combined_context = {
        "industry": IndustryType.TECHNOLOGY,
        "company_size": CompanySize.SMALL
    }
    
    print(f"Context: {combined_context}")
    
    team_size_defaults = service.get_smart_defaults("technical_team_size", combined_context)
    if team_size_defaults:
        print(f"Technical Team Size Suggestions:")
        for default in team_size_defaults:
            print(f"  • {default.value} people (confidence: {default.confidence:.1%})")
            print(f"    Reason: {default.reason}")


def demo_auto_completion():
    """Demonstrate auto-completion functionality."""
    print_section("AUTO-COMPLETION DEMO")
    
    service = IntelligentFormService()
    
    # Demo 1: Basic suggestions
    print_subsection("Basic Auto-completion")
    
    fields_to_test = ["ai_use_cases", "cloud_services", "company_name"]
    
    for field in fields_to_test:
        print(f"\nField: {field}")
        suggestions = service.get_suggestions(field, "", {})
        
        print(f"Available suggestions:")
        for suggestion in suggestions[:5]:  # Show top 5
            print(f"  • {suggestion.label}")
            print(f"    Description: {suggestion.description}")
            print(f"    Confidence: {suggestion.confidence:.1%}")
            if suggestion.category:
                print(f"    Category: {suggestion.category}")
    
    # Demo 2: Query-filtered suggestions
    print_subsection("Query-filtered Suggestions")
    
    queries = [
        ("ai_use_cases", "predict"),
        ("cloud_services", "database"),
        ("company_name", "tech")
    ]
    
    for field, query in queries:
        print(f"\nField: {field}, Query: '{query}'")
        suggestions = service.get_suggestions(field, query, {})
        
        if suggestions:
            print(f"Matching suggestions:")
            for suggestion in suggestions:
                print(f"  • {suggestion.label}")
                print(f"    Value: {suggestion.value}")
        else:
            print("  No matching suggestions found")
    
    # Demo 3: Context-aware suggestions
    print_subsection("Context-aware Suggestions")
    
    context = {"industry": IndustryType.HEALTHCARE}
    print(f"Context: {context}")
    
    suggestions = service.get_suggestions("ai_use_cases", "", context)
    print(f"AI Use Cases for Healthcare:")
    for suggestion in suggestions:
        if suggestion.category == "industry_specific":
            print(f"  • {suggestion.label} (Industry-specific)")
            print(f"    Description: {suggestion.description}")


def demo_contextual_help():
    """Demonstrate contextual help functionality."""
    print_section("CONTEXTUAL HELP DEMO")
    
    service = IntelligentFormService()
    
    # Demo 1: Basic contextual help
    print_subsection("Basic Contextual Help")
    
    fields_with_help = ["company_size", "budget_range", "compliance_requirements", 
                       "ai_use_cases", "data_volume"]
    
    for field in fields_with_help:
        help_info = service.get_contextual_help(field, {})
        if help_info:
            print(f"\nField: {field}")
            print(f"Title: {help_info.title}")
            print(f"Content: {help_info.content}")
            
            if help_info.examples:
                print("Examples:")
                for example in help_info.examples[:3]:  # Show first 3
                    print(f"  • {example}")
            
            if help_info.tips:
                print("Tips:")
                for tip in help_info.tips[:2]:  # Show first 2
                    print(f"  • {tip}")
    
    # Demo 2: Context-customized help
    print_subsection("Context-customized Help")
    
    contexts = [
        {"industry": IndustryType.HEALTHCARE},
        {"company_size": CompanySize.STARTUP}
    ]
    
    for context in contexts:
        print(f"\nContext: {context}")
        
        # Get help for compliance requirements
        help_info = service.get_contextual_help("compliance_requirements", context)
        if help_info:
            print(f"Compliance Help (customized):")
            print(f"  Content: {help_info.content}")
            if help_info.tips:
                print("  Context-specific tips:")
                for tip in help_info.tips[-2:]:  # Show last 2 (likely context-specific)
                    print(f"    • {tip}")
        
        # Get help for budget range
        help_info = service.get_contextual_help("budget_range", context)
        if help_info:
            print(f"Budget Help (customized):")
            if help_info.tips:
                print("  Context-specific tips:")
                for tip in help_info.tips[-1:]:  # Show last tip (likely context-specific)
                    print(f"    • {tip}")


def demo_progressive_disclosure():
    """Demonstrate progressive disclosure functionality."""
    print_section("PROGRESSIVE DISCLOSURE DEMO")
    
    service = IntelligentFormService()
    
    # Demo 1: Basic field visibility
    print_subsection("Basic Field Visibility")
    
    test_fields = [
        "company_name",
        "compliance_requirements", 
        "advanced_security_features",
        "technical_team_size",
        "budget_range"
    ]
    
    empty_context = {}
    print(f"Context: {empty_context}")
    
    for field in test_fields:
        visible = service.should_show_field(field, empty_context)
        print(f"  {field}: {'✓ Show' if visible else '✗ Hide'}")
    
    # Demo 2: Context-dependent visibility
    print_subsection("Context-dependent Visibility")
    
    contexts = [
        {"industry": IndustryType.HEALTHCARE},
        {"industry": IndustryType.TECHNOLOGY},
        {"company_size": CompanySize.ENTERPRISE},
        {"current_ai_maturity": "advanced"}
    ]
    
    for context in contexts:
        print(f"\nContext: {context}")
        
        for field in test_fields:
            visible = service.should_show_field(field, context)
            status = "✓ Show" if visible else "✗ Hide"
            print(f"  {field}: {status}")
    
    # Demo 3: Field priority ordering
    print_subsection("Field Priority Ordering")
    
    context = {"industry": IndustryType.TECHNOLOGY, "company_size": CompanySize.SMALL}
    print(f"Context: {context}")
    
    fields_with_priority = [
        ("company_name", service.get_field_priority("company_name", context)),
        ("industry", service.get_field_priority("industry", context)),
        ("budget_range", service.get_field_priority("budget_range", context)),
        ("compliance_requirements", service.get_field_priority("compliance_requirements", context)),
        ("additional_context", service.get_field_priority("additional_context", context))
    ]
    
    # Sort by priority (lower number = higher priority)
    fields_with_priority.sort(key=lambda x: x[1])
    
    print("Field display order (by priority):")
    for i, (field, priority) in enumerate(fields_with_priority, 1):
        print(f"  {i}. {field} (priority: {priority})")


def demo_save_resume_functionality():
    """Demonstrate save and resume functionality."""
    print_section("SAVE & RESUME FUNCTIONALITY DEMO")
    
    state_manager = FormStateManager()
    
    # Demo 1: Save form state
    print_subsection("Saving Form State")
    
    form_id = "demo_assessment_123"
    user_id = "demo_user"
    
    form_data = {
        "company_name": "TechCorp Inc",
        "industry": "technology",
        "company_size": "small",
        "budget_range": "50k_100k",
        "ai_use_cases": ["machine_learning", "predictive_analytics"]
    }
    current_step = 2
    metadata = {
        "started_at": "2024-01-01T10:00:00Z",
        "user_agent": "Demo Script"
    }
    
    print(f"Saving form state:")
    print(f"  Form ID: {form_id}")
    print(f"  User ID: {user_id}")
    print(f"  Current Step: {current_step}")
    print(f"  Form Data: {json.dumps(form_data, indent=2)}")
    
    success = state_manager.save_form_state(form_id, user_id, form_data, current_step, metadata)
    print(f"  Save Result: {'✓ Success' if success else '✗ Failed'}")
    
    # Demo 2: Load form state
    print_subsection("Loading Form State")
    
    loaded_state = state_manager.load_form_state(form_id, user_id)
    if loaded_state:
        print(f"Loaded form state:")
        print(f"  Form ID: {loaded_state['form_id']}")
        print(f"  Current Step: {loaded_state['current_step']}")
        print(f"  Saved At: {loaded_state['saved_at']}")
        print(f"  Form Data Keys: {list(loaded_state['form_data'].keys())}")
    else:
        print("  ✗ No saved state found")
    
    # Demo 3: Save multiple forms and list them
    print_subsection("Multiple Saved Forms")
    
    # Save additional forms
    additional_forms = [
        ("assessment_456", {"company_name": "HealthTech", "industry": "healthcare"}, 1),
        ("assessment_789", {"company_name": "FinanceAI", "industry": "finance"}, 3)
    ]
    
    for form_id, data, step in additional_forms:
        state_manager.save_form_state(form_id, user_id, data, step)
    
    # List all saved forms
    saved_forms = state_manager.list_saved_forms(user_id)
    print(f"Saved forms for user {user_id}:")
    
    for form in saved_forms:
        print(f"  • Form ID: {form['form_id']}")
        print(f"    Step: {form['current_step']}")
        print(f"    Completion: {form['completion_percentage']:.1f}%")
        print(f"    Saved: {form['saved_at']}")
    
    # Demo 4: Delete form state
    print_subsection("Deleting Form State")
    
    delete_form_id = "assessment_456"
    print(f"Deleting form: {delete_form_id}")
    
    success = state_manager.delete_form_state(delete_form_id, user_id)
    print(f"  Delete Result: {'✓ Success' if success else '✗ Failed'}")
    
    # Verify deletion
    remaining_forms = state_manager.list_saved_forms(user_id)
    print(f"Remaining forms: {len(remaining_forms)}")


def demo_form_integration():
    """Demonstrate integration with assessment form."""
    print_section("FORM INTEGRATION DEMO")
    
    # Create assessment form
    form = AssessmentForm()
    
    print_subsection("Form with Intelligent Features")
    
    print(f"Form ID: {form.form_id}")
    print(f"Total Steps: {len(form.steps)}")
    print(f"Intelligent Service Available: {form.intelligent_service is not None}")
    print(f"State Manager Available: {form.state_manager is not None}")
    
    # Demo smart defaults integration
    if form.intelligent_service:
        print_subsection("Smart Defaults Integration")
        
        # Set some context
        form.form_data = {"industry": "technology", "company_size": "small"}
        
        defaults = form.get_smart_defaults("budget_range")
        print(f"Smart defaults for budget_range:")
        for default in defaults:
            print(f"  • {default['value']} (confidence: {default['confidence']:.1%})")
            print(f"    Reason: {default['reason']}")
    
    # Demo progressive disclosure
    if form.intelligent_service:
        print_subsection("Progressive Disclosure Integration")
        
        # Get first step fields with progressive disclosure
        first_step = form.steps[0]
        visible_fields = form.get_progressive_fields(first_step.id)
        
        print(f"Step: {first_step.title}")
        print(f"Total fields: {len(first_step.fields)}")
        print(f"Visible fields: {len(visible_fields)}")
        
        for field in visible_fields:
            print(f"  • {field.name}: {field.label}")
    
    # Demo state management
    if form.state_manager:
        print_subsection("State Management Integration")
        
        # Set some form data
        form.form_data = {
            "company_name": "Demo Corp",
            "industry": "technology",
            "company_size": "medium"
        }
        form.current_step_index = 1
        
        # Save state
        save_success = form.save_form_state("demo_user")
        print(f"Save form state: {'✓ Success' if save_success else '✗ Failed'}")
        
        # Load state (simulate new form instance)
        new_form = AssessmentForm(form_id=form.form_id)
        load_success = new_form.load_form_state("demo_user")
        print(f"Load form state: {'✓ Success' if load_success else '✗ Failed'}")
        
        if load_success:
            print(f"Loaded data keys: {list(new_form.form_data.keys())}")
            print(f"Loaded step: {new_form.current_step_index}")


def main():
    """Run all demos."""
    print("🚀 INTELLIGENT FORM FEATURES DEMO")
    print("This demo showcases the enhanced form capabilities including:")
    print("• Smart defaults based on industry patterns and company size")
    print("• Auto-completion and suggestion features")
    print("• Contextual help and guidance system")
    print("• Progressive disclosure and save-and-resume functionality")
    
    try:
        demo_smart_defaults()
        demo_auto_completion()
        demo_contextual_help()
        demo_progressive_disclosure()
        demo_save_resume_functionality()
        demo_form_integration()
        
        print_section("DEMO COMPLETED SUCCESSFULLY")
        print("✅ All intelligent form features demonstrated successfully!")
        print("\nKey Benefits:")
        print("• Improved user experience with smart suggestions")
        print("• Reduced form abandonment with contextual help")
        print("• Faster form completion with auto-completion")
        print("• Better data quality with progressive disclosure")
        print("• Enhanced usability with save-and-resume functionality")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()