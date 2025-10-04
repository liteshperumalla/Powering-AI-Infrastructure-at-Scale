"""
Comprehensive Smart Suggestions Fix for forms.py
This script creates a robust smart suggestions system with extensive field coverage.
"""

comprehensive_smart_defaults_function = '''
async def _generate_smart_defaults_for_field(field_name: str, context: Dict[str, Any]) -> List[SmartDefaultItem]:
    """Generate intelligent default values for specific fields based on context"""

    # Extract context information
    industry = context.get("industry", "").lower()
    company_size = context.get("companySize", "").lower()

    # Comprehensive field mappings - handles both frontend and backend field names
    field_mappings = {
        # Company fields
        "companyName": "company_name", "company_name": "company_name",

        # Business fields
        "businessGoal": "business_goals", "businessGoals": "business_goals",
        "currentChallenges": "current_challenges", "challenges": "current_challenges",

        # Technical fields
        "currentCloudProvider": "cloud_providers", "cloudProvider": "cloud_providers",
        "currentServices": "cloud_services", "services": "cloud_services",
        "workloadTypes": "workload_types", "workloads": "workload_types",
        "aiUseCases": "ai_use_cases", "ai_use_cases": "ai_use_cases",

        # Infrastructure fields
        "technicalTeamSize": "team_size", "teamSize": "team_size",
        "infrastructureAge": "infra_age", "currentArchitecture": "architecture",
        "dataStorageSolution": "storage", "networkSetup": "network",

        # Performance fields
        "monthlyBudget": "budget", "budget": "budget"
    }

    # Normalize field name
    normalized_field = field_mappings.get(field_name, field_name)

    # Industry-specific suggestions
    industry_suggestions = {
        "e-commerce": {
            "company_name": ["ShopTech Solutions", "RetailCloud Systems", "EcommerceHub"],
            "business_goals": ["Increase conversion rates", "Reduce cart abandonment", "Improve customer retention"],
            "current_challenges": ["High cart abandonment", "Slow page load times", "Inventory management"],
            "cloud_providers": ["AWS", "Google Cloud", "Microsoft Azure"],
            "workload_types": ["Web applications", "Real-time analytics", "Recommendation engines"],
            "ai_use_cases": ["Personalized recommendations", "Dynamic pricing", "Fraud detection"]
        },
        "retail": {
            "company_name": ["RetailTech Corp", "Commerce Solutions", "ShopSphere"],
            "business_goals": ["Optimize supply chain", "Enhance customer experience", "Reduce operational costs"],
            "current_challenges": ["Inventory optimization", "Customer personalization", "Supply chain visibility"],
            "cloud_providers": ["AWS", "Microsoft Azure", "Google Cloud"],
            "workload_types": ["E-commerce platforms", "Analytics dashboards", "Mobile applications"],
            "ai_use_cases": ["Demand forecasting", "Customer segmentation", "Price optimization"]
        },
        "technology": {
            "company_name": ["TechCorp Solutions", "InnovateTech", "DataStream Systems"],
            "business_goals": ["Scale development operations", "Improve system reliability", "Reduce infrastructure costs"],
            "current_challenges": ["High cloud costs", "Scaling issues", "Security vulnerabilities"],
            "cloud_providers": ["AWS", "Google Cloud", "Microsoft Azure"],
            "workload_types": ["Microservices", "Data processing", "Machine learning"],
            "ai_use_cases": ["Automated testing", "Code analysis", "Performance optimization"]
        },
        "healthcare": {
            "company_name": ["HealthTech Systems", "MediCare Solutions", "Wellness Platform"],
            "business_goals": ["Ensure HIPAA compliance", "Improve patient outcomes", "Reduce operational costs"],
            "current_challenges": ["Compliance requirements", "Data security", "Legacy system integration"],
            "cloud_providers": ["Microsoft Azure", "AWS", "Google Cloud"],
            "workload_types": ["Patient management", "Medical imaging", "Telemedicine"],
            "ai_use_cases": ["Diagnostic assistance", "Drug discovery", "Patient monitoring"]
        },
        "finance": {
            "company_name": ["FinTech Solutions", "Capital Systems", "Investment Platform"],
            "business_goals": ["Meet regulatory compliance", "Enhance transaction security", "Improve system performance"],
            "current_challenges": ["Regulatory compliance", "Data security", "Real-time processing"],
            "cloud_providers": ["Microsoft Azure", "AWS", "IBM Cloud"],
            "workload_types": ["Trading systems", "Risk analysis", "Payment processing"],
            "ai_use_cases": ["Fraud detection", "Risk assessment", "Algorithmic trading"]
        }
    }

    # Default/generic suggestions
    default_suggestions = {
        "company_name": ["Enterprise Solutions", "Business Systems Inc", "Global Corp"],
        "business_goals": ["Reduce operational costs", "Improve system reliability", "Scale business operations"],
        "current_challenges": ["High operational costs", "System reliability issues", "Security concerns"],
        "cloud_providers": ["AWS", "Microsoft Azure", "Google Cloud"],
        "cloud_services": ["Compute instances", "Managed databases", "Object storage"],
        "workload_types": ["Web applications", "Database systems", "File storage"],
        "ai_use_cases": ["Data analytics", "Process automation", "Customer insights"],
        "team_size": ["5-10", "10-25", "25-50"],
        "architecture": ["Microservices", "Event-driven", "Serverless"],
        "storage": ["Cloud databases", "Object storage", "Data lakes"],
        "network": ["VPC with subnets", "Global CDN", "Load balancers"],
        "budget": ["$10k-25k", "$25k-50k", "$50k-100k"],
        "infra_age": ["1-2 years", "2-4 years", "4+ years"]
    }

    # Get industry-specific suggestions or fall back to defaults
    suggestions_source = industry_suggestions.get(industry, {})
    base_suggestions = suggestions_source.get(normalized_field, default_suggestions.get(normalized_field, []))

    # Convert to SmartDefaultItem objects
    defaults = []
    for i, suggestion in enumerate(base_suggestions[:5]):  # Limit to 5 suggestions
        confidence = max(0.3, 0.9 - (i * 0.15))  # Decreasing confidence
        reason = f"Common {industry} {normalized_field.replace('_', ' ')}" if industry else f"Recommended {normalized_field.replace('_', ' ')}"

        defaults.append(SmartDefaultItem(
            value=suggestion,
            confidence=confidence,
            reason=reason,
            source="ai_analysis"
        ))

    return defaults
'''

print("Smart suggestions fix prepared")