#!/usr/bin/env python3
"""
Demo script for the form system.

This script demonstrates the multi-step form functionality including:
- Form creation and initialization
- Step-by-step data collection
- Validation and error handling
- Assessment creation from form data
"""

import asyncio
import json
import logging
from typing import Dict, Any

from src.infra_mind.forms import (
    AssessmentForm, 
    BusinessRequirementsForm, 
    TechnicalRequirementsForm,
    FormValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(title: str) -> None:
    """Print a section separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_form_summary(form) -> None:
    """Print a summary of the form state."""
    summary = form.get_form_summary()
    print(f"Form ID: {summary['form_id']}")
    print(f"Total Steps: {summary['total_steps']}")
    print(f"Current Step: {summary['current_step_index'] + 1}")
    print(f"Completion: {summary['completion_percentage']:.1f}%")
    print(f"Complete: {summary['is_complete']}")
    print(f"Has Errors: {summary['has_errors']}")


def demo_business_form():
    """Demonstrate the business requirements form."""
    print_separator("Business Requirements Form Demo")
    
    # Create business form
    form = BusinessRequirementsForm()
    print(f"Created business form with {len(form.steps)} steps")
    
    # Print form structure
    print("\nForm Structure:")
    for i, step in enumerate(form.steps):
        print(f"  Step {i+1}: {step.title} ({step.id})")
        print(f"    Fields: {', '.join(field.name for field in step.fields)}")
    
    print_form_summary(form)
    
    # Simulate filling out the form
    print("\n--- Filling out Step 1: Company Information ---")
    step1_data = {
        "company_name": "TechCorp Solutions",
        "industry": "technology",
        "company_size": "medium",
        "contact_email": "cto@techcorp.com"
    }
    
    # Submit step 1
    success = form.submit_step("company_info", step1_data)
    print(f"Step 1 submission: {'Success' if success else 'Failed'}")
    
    if success:
        form.proceed_to_next_step()
        print_form_summary(form)
    
    # Fill out step 2
    print("\n--- Filling out Step 2: Business Goals & Budget ---")
    step2_data = {
        "primary_goals": ["cost_reduction", "scalability", "performance"],
        "budget_range": "100k_500k",
        "timeline": "medium_term",
        "success_metrics": ["cost_savings", "performance_improvement", "roi"]
    }
    
    success = form.submit_step("business_goals", step2_data)
    print(f"Step 2 submission: {'Success' if success else 'Failed'}")
    
    if success:
        form.proceed_to_next_step()
        print_form_summary(form)
    
    # Fill out step 3
    print("\n--- Filling out Step 3: Current State & Challenges ---")
    step3_data = {
        "infrastructure_maturity": "intermediate",
        "main_challenges": ["high_costs", "scalability_issues", "lack_expertise"],
        "additional_context": "We're looking to modernize our infrastructure to support rapid growth."
    }
    
    success = form.submit_step("current_state", step3_data)
    print(f"Step 3 submission: {'Success' if success else 'Failed'}")
    
    print_form_summary(form)
    
    # Show final form data
    print("\nFinal Form Data:")
    print(json.dumps(form.get_form_data(), indent=2))
    
    return form


def demo_technical_form():
    """Demonstrate the technical requirements form."""
    print_separator("Technical Requirements Form Demo")
    
    # Create technical form
    form = TechnicalRequirementsForm()
    print(f"Created technical form with {len(form.steps)} steps")
    
    # Print form structure
    print("\nForm Structure:")
    for i, step in enumerate(form.steps):
        print(f"  Step {i+1}: {step.title} ({step.id})")
        print(f"    Fields: {', '.join(field.name for field in step.fields)}")
    
    # Simulate filling out the form
    print("\n--- Filling out Step 1: Current Infrastructure ---")
    step1_data = {
        "current_hosting": ["aws", "on_premises"],
        "current_technologies": ["containers", "databases", "load_balancers"],
        "team_expertise": "intermediate"
    }
    
    success = form.submit_step("current_infrastructure", step1_data)
    print(f"Step 1 submission: {'Success' if success else 'Failed'}")
    
    if success:
        form.proceed_to_next_step()
    
    # Fill out step 2
    print("\n--- Filling out Step 2: Workload Requirements ---")
    step2_data = {
        "workload_types": ["web_applications", "apis", "databases", "machine_learning"],
        "expected_users": 5000,
        "data_volume": "100gb_1tb",
        "performance_requirements": ["high_availability", "auto_scaling", "monitoring_alerting"]
    }
    
    success = form.submit_step("workload_requirements", step2_data)
    print(f"Step 2 submission: {'Success' if success else 'Failed'}")
    
    if success:
        form.proceed_to_next_step()
    
    # Fill out step 3
    print("\n--- Filling out Step 3: Cloud Preferences & Compliance ---")
    step3_data = {
        "preferred_cloud_providers": ["aws", "azure"],
        "geographic_requirements": ["north_america", "europe"],
        "compliance_requirements": ["gdpr", "iso_27001"],
        "security_requirements": ["encryption_at_rest", "encryption_in_transit", "network_isolation", "access_control"]
    }
    
    success = form.submit_step("cloud_preferences", step3_data)
    print(f"Step 3 submission: {'Success' if success else 'Failed'}")
    
    print_form_summary(form)
    
    # Show final form data
    print("\nFinal Form Data:")
    print(json.dumps(form.get_form_data(), indent=2))
    
    return form


def demo_validation_errors():
    """Demonstrate form validation and error handling."""
    print_separator("Form Validation Demo")
    
    form = BusinessRequirementsForm()
    
    # Try to submit invalid data
    print("--- Testing validation with invalid data ---")
    invalid_data = {
        "company_name": "",  # Required field empty
        "industry": "invalid_industry",  # Invalid choice
        "company_size": "large",  # Valid
        "contact_email": "invalid-email"  # Invalid email format
    }
    
    # Validate step
    errors = form.validate_step("company_info", invalid_data)
    print(f"Validation errors: {errors}")
    
    # Try to submit (should fail)
    success = form.submit_step("company_info", invalid_data)
    print(f"Submission result: {'Success' if success else 'Failed'}")
    
    # Now submit valid data
    print("\n--- Testing with valid data ---")
    valid_data = {
        "company_name": "Valid Company",
        "industry": "technology",
        "company_size": "large",
        "contact_email": "valid@email.com"
    }
    
    errors = form.validate_step("company_info", valid_data)
    print(f"Validation errors: {errors}")
    
    success = form.submit_step("company_info", valid_data)
    print(f"Submission result: {'Success' if success else 'Failed'}")


def demo_complete_assessment_form():
    """Demonstrate the complete assessment form."""
    print_separator("Complete Assessment Form Demo")
    
    # Create complete assessment form
    form = AssessmentForm()
    print(f"Created assessment form with {len(form.steps)} steps")
    
    # Print form structure
    print("\nForm Structure:")
    for i, step in enumerate(form.steps):
        section = step.metadata.get("section", "unknown")
        print(f"  Step {i+1}: {step.title} ({step.id}) - {section}")
    
    # Fill out all steps with sample data
    sample_data = {
        # Business steps
        "business_company_info": {
            "company_name": "InnovateTech Inc",
            "industry": "technology",
            "company_size": "medium",
            "contact_email": "cto@innovatetech.com"
        },
        "business_business_goals": {
            "primary_goals": ["scalability", "performance", "innovation"],
            "budget_range": "100k_500k",
            "timeline": "medium_term",
            "success_metrics": ["performance_improvement", "roi"]
        },
        "business_current_state": {
            "infrastructure_maturity": "intermediate",
            "main_challenges": ["scalability_issues", "high_costs"],
            "additional_context": "Growing startup needing to scale infrastructure"
        },
        # Technical steps
        "technical_current_infrastructure": {
            "current_hosting": ["aws"],
            "current_technologies": ["containers", "databases"],
            "team_expertise": "intermediate"
        },
        "technical_workload_requirements": {
            "workload_types": ["web_applications", "apis", "machine_learning"],
            "expected_users": 10000,
            "data_volume": "1tb_10tb",
            "performance_requirements": ["high_availability", "auto_scaling"]
        },
        "technical_cloud_preferences": {
            "preferred_cloud_providers": ["aws", "azure"],
            "geographic_requirements": ["north_america"],
            "compliance_requirements": ["gdpr"],
            "security_requirements": ["encryption_at_rest", "network_isolation"]
        }
    }
    
    # Submit all steps
    for step_id, data in sample_data.items():
        print(f"\n--- Submitting {step_id} ---")
        success = form.submit_step(step_id, data)
        print(f"Submission: {'Success' if success else 'Failed'}")
        
        if success and form.can_proceed_to_next_step():
            form.proceed_to_next_step()
    
    print_form_summary(form)
    
    # Try to create assessment
    if form.is_form_complete():
        print("\n--- Creating Assessment ---")
        assessment = form.create_assessment()
        if assessment:
            print(f"Created assessment: {assessment.id}")
            print(f"Business requirements: {assessment.business_requirements.company_name}")
            print(f"Technical workloads: {assessment.technical_requirements.workload_types}")
            print(f"Compliance needs: {assessment.compliance_requirements.compliance_requirements}")
        else:
            print("Failed to create assessment")
    else:
        print("Form is not complete - cannot create assessment")


def demo_form_serialization():
    """Demonstrate form serialization and deserialization."""
    print_separator("Form Serialization Demo")
    
    # Create and fill a form
    form = BusinessRequirementsForm()
    
    # Fill first step
    step1_data = {
        "company_name": "SerializationTest Corp",
        "industry": "technology",
        "company_size": "small",
        "contact_email": "test@serialization.com"
    }
    form.submit_step("company_info", step1_data)
    form.proceed_to_next_step()
    
    # Serialize form
    form_dict = form.to_dict()
    print("Form serialized to dictionary")
    print(f"Form ID: {form_dict['form_id']}")
    print(f"Current step: {form_dict['current_step_index']}")
    print(f"Form data keys: {list(form_dict['form_data'].keys())}")
    
    # Convert to JSON
    form_json = json.dumps(form_dict, indent=2)
    print(f"\nForm JSON size: {len(form_json)} characters")
    
    # Deserialize (basic implementation)
    print("\nForm serialization completed successfully")


def main():
    """Run all form demos."""
    print("Starting Form System Demo")
    
    try:
        # Run individual demos
        demo_business_form()
        demo_technical_form()
        demo_validation_errors()
        demo_complete_assessment_form()
        demo_form_serialization()
        
        print_separator("Demo Completed Successfully")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\nDemo failed with error: {str(e)}")


if __name__ == "__main__":
    main()