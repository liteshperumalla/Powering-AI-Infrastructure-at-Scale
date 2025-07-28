"""
Intelligent form features for enhanced user experience.

Provides smart defaults, auto-completion, contextual help, and progressive disclosure
functionality for assessment forms.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class IndustryType(str, Enum):
    """Industry types for smart defaults."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    CONSULTING = "consulting"
    MEDIA = "media"
    OTHER = "other"


class CompanySize(str, Enum):
    """Company size categories."""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


@dataclass
class SmartDefault:
    """Smart default value with confidence score."""
    value: Any
    confidence: float  # 0.0 to 1.0
    reason: str
    source: str = "pattern_analysis"


@dataclass
class Suggestion:
    """Auto-completion suggestion."""
    value: str
    label: str
    description: str
    confidence: float
    category: Optional[str] = None


@dataclass
class ContextualHelp:
    """Contextual help information."""
    title: str
    content: str
    examples: List[str]
    tips: List[str]
    related_fields: List[str]
    help_type: str = "tooltip"  # tooltip, modal, inline


class IntelligentFormService:
    """Service providing intelligent form features."""
    
    def __init__(self):
        """Initialize the intelligent form service."""
        self._industry_patterns = self._load_industry_patterns()
        self._company_size_patterns = self._load_company_size_patterns()
        self._common_suggestions = self._load_common_suggestions()
        self._contextual_help = self._load_contextual_help()
        
        logger.info("Initialized intelligent form service")
    
    def _load_industry_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load industry-specific patterns for smart defaults."""
        return {
            IndustryType.TECHNOLOGY: {
                "typical_budget_ranges": ["100k_500k", "500k_1m", "over_1m"],
                "common_cloud_providers": ["aws", "gcp", "azure"],
                "typical_team_sizes": [5, 15, 25],
                "common_ai_use_cases": ["machine_learning", "data_analytics", "automation"],
                "compliance_requirements": ["gdpr", "ccpa"],
                "security_level": "enhanced",
                "performance_requirements": "high",
                "scaling_timeline": "short_term"
            },
            IndustryType.HEALTHCARE: {
                "typical_budget_ranges": ["50k_100k", "100k_500k"],
                "common_cloud_providers": ["aws", "azure"],
                "typical_team_sizes": [3, 8, 15],
                "common_ai_use_cases": ["predictive_analytics", "nlp", "computer_vision"],
                "compliance_requirements": ["hipaa", "gdpr"],
                "security_level": "enterprise",
                "performance_requirements": "high",
                "scaling_timeline": "medium_term"
            },
            IndustryType.FINANCE: {
                "typical_budget_ranges": ["500k_1m", "over_1m"],
                "common_cloud_providers": ["aws", "azure"],
                "typical_team_sizes": [10, 20, 40],
                "common_ai_use_cases": ["fraud_detection", "risk_analysis", "algorithmic_trading"],
                "compliance_requirements": ["sox", "pci_dss", "gdpr"],
                "security_level": "enterprise",
                "performance_requirements": "real_time",
                "scaling_timeline": "long_term"
            },
            IndustryType.RETAIL: {
                "typical_budget_ranges": ["10k_50k", "50k_100k", "100k_500k"],
                "common_cloud_providers": ["aws", "gcp", "azure"],
                "typical_team_sizes": [2, 8, 20],
                "common_ai_use_cases": ["recommendation_systems", "inventory_optimization", "customer_analytics"],
                "compliance_requirements": ["gdpr", "ccpa", "pci_dss"],
                "security_level": "enhanced",
                "performance_requirements": "standard",
                "scaling_timeline": "short_term"
            },
            IndustryType.MANUFACTURING: {
                "typical_budget_ranges": ["100k_500k", "500k_1m"],
                "common_cloud_providers": ["azure", "aws"],
                "typical_team_sizes": [5, 12, 25],
                "common_ai_use_cases": ["predictive_maintenance", "quality_control", "supply_chain"],
                "compliance_requirements": ["iso_27001"],
                "security_level": "enhanced",
                "performance_requirements": "high",
                "scaling_timeline": "medium_term"
            }
        }
    
    def _load_company_size_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load company size-specific patterns."""
        return {
            CompanySize.STARTUP: {
                "typical_budgets": ["under_10k", "10k_50k"],
                "team_size_range": (1, 10),
                "infrastructure_maturity": "basic",
                "preferred_timeline": "immediate",
                "common_challenges": ["lack_expertise", "high_costs"],
                "typical_data_volume": "small"
            },
            CompanySize.SMALL: {
                "typical_budgets": ["10k_50k", "50k_100k"],
                "team_size_range": (2, 15),
                "infrastructure_maturity": "intermediate",
                "preferred_timeline": "short_term",
                "common_challenges": ["scalability_issues", "lack_expertise"],
                "typical_data_volume": "medium"
            },
            CompanySize.MEDIUM: {
                "typical_budgets": ["50k_100k", "100k_500k"],
                "team_size_range": (5, 50),
                "infrastructure_maturity": "intermediate",
                "preferred_timeline": "medium_term",
                "common_challenges": ["scalability_issues", "compliance_gaps"],
                "typical_data_volume": "medium"
            },
            CompanySize.LARGE: {
                "typical_budgets": ["100k_500k", "500k_1m"],
                "team_size_range": (10, 100),
                "infrastructure_maturity": "advanced",
                "preferred_timeline": "long_term",
                "common_challenges": ["legacy_systems", "vendor_lock_in"],
                "typical_data_volume": "large"
            },
            CompanySize.ENTERPRISE: {
                "typical_budgets": ["500k_1m", "over_1m"],
                "team_size_range": (20, 200),
                "infrastructure_maturity": "expert",
                "preferred_timeline": "long_term",
                "common_challenges": ["legacy_systems", "compliance_gaps"],
                "typical_data_volume": "very_large"
            }
        }
    
    def _load_common_suggestions(self) -> Dict[str, List[Suggestion]]:
        """Load common auto-completion suggestions."""
        return {
            "company_name": [
                Suggestion("Acme Corp", "Acme Corp", "Technology company", 0.8),
                Suggestion("TechStart Inc", "TechStart Inc", "Startup technology company", 0.7),
                Suggestion("Global Solutions LLC", "Global Solutions LLC", "Consulting company", 0.6),
            ],
            "ai_use_cases": [
                Suggestion("customer_support_chatbot", "Customer Support Chatbot", 
                          "AI-powered customer service automation", 0.9, "customer_service"),
                Suggestion("predictive_analytics", "Predictive Analytics", 
                          "Forecast trends and outcomes", 0.8, "analytics"),
                Suggestion("recommendation_engine", "Recommendation Engine", 
                          "Personalized product/content recommendations", 0.8, "personalization"),
                Suggestion("fraud_detection", "Fraud Detection", 
                          "Identify suspicious activities and transactions", 0.7, "security"),
                Suggestion("inventory_optimization", "Inventory Optimization", 
                          "Optimize stock levels and supply chain", 0.7, "operations"),
            ],
            "cloud_services": [
                Suggestion("compute_instances", "Compute Instances", 
                          "Virtual machines for general workloads", 0.9, "compute"),
                Suggestion("managed_databases", "Managed Databases", 
                          "Fully managed database services", 0.8, "database"),
                Suggestion("ml_platforms", "ML Platforms", 
                          "Machine learning model training and deployment", 0.8, "ai_ml"),
                Suggestion("api_gateway", "API Gateway", 
                          "Manage and secure API endpoints", 0.7, "networking"),
                Suggestion("container_orchestration", "Container Orchestration", 
                          "Kubernetes and container management", 0.7, "containers"),
            ]
        }
    
    def _load_contextual_help(self) -> Dict[str, ContextualHelp]:
        """Load contextual help information."""
        return {
            "company_size": ContextualHelp(
                title="Company Size",
                content="Select the size category that best matches your organization. This helps us provide more accurate recommendations.",
                examples=[
                    "Startup: 1-50 employees, early stage, limited resources",
                    "Small: 51-200 employees, established but growing",
                    "Medium: 201-1000 employees, multiple departments",
                    "Large: 1000+ employees, complex organizational structure"
                ],
                tips=[
                    "Consider your total employee count, not just technical team",
                    "Choose based on current size, not projected growth",
                    "This affects budget recommendations and complexity levels"
                ],
                related_fields=["budget_range", "team_expertise", "infrastructure_maturity"]
            ),
            "budget_range": ContextualHelp(
                title="Annual Budget Range",
                content="Estimate your annual budget for AI infrastructure including cloud services, tools, and platforms.",
                examples=[
                    "Include: Cloud services, AI/ML platforms, monitoring tools",
                    "Exclude: Personnel costs, hardware purchases",
                    "Consider: Growth over the next 12 months"
                ],
                tips=[
                    "Be realistic about your actual available budget",
                    "Consider both initial setup and ongoing operational costs",
                    "Budget affects service tier and feature recommendations"
                ],
                related_fields=["company_size", "scaling_timeline", "performance_requirements"]
            ),
            "compliance_requirements": ContextualHelp(
                title="Compliance Requirements",
                content="Select all regulatory standards your organization must comply with.",
                examples=[
                    "GDPR: European data protection regulation",
                    "HIPAA: US healthcare data protection",
                    "SOX: US financial reporting requirements",
                    "PCI DSS: Payment card industry security standards"
                ],
                tips=[
                    "Check with your legal/compliance team if unsure",
                    "Multiple compliance requirements may limit cloud options",
                    "Compliance affects data location and security requirements"
                ],
                related_fields=["industry", "data_location", "security_level"]
            ),
            "ai_use_cases": ContextualHelp(
                title="AI Use Cases",
                content="Select the AI applications you plan to implement or are currently using.",
                examples=[
                    "Machine Learning: Predictive models, classification",
                    "NLP: Text analysis, chatbots, sentiment analysis",
                    "Computer Vision: Image recognition, object detection",
                    "Recommendation Systems: Personalized suggestions"
                ],
                tips=[
                    "Select current and planned use cases",
                    "Different use cases have different infrastructure needs",
                    "This affects compute, storage, and service recommendations"
                ],
                related_fields=["expected_data_volume", "performance_requirements", "scaling_timeline"]
            ),
            "data_volume": ContextualHelp(
                title="Expected Data Volume",
                content="Estimate the amount of data you'll be processing and storing for AI workloads.",
                examples=[
                    "Small: < 1TB - Basic analytics, small datasets",
                    "Medium: 1TB-100TB - Standard ML workloads",
                    "Large: 100TB-1PB - Big data analytics, large ML models",
                    "Very Large: > 1PB - Enterprise-scale data processing"
                ],
                tips=[
                    "Include both training and inference data",
                    "Consider data growth over time",
                    "Affects storage, compute, and network requirements"
                ],
                related_fields=["ai_use_cases", "performance_requirements", "budget_range"]
            )
        }
    
    def get_smart_defaults(self, field_name: str, context: Dict[str, Any]) -> List[SmartDefault]:
        """
        Get smart default values for a field based on context.
        
        Args:
            field_name: Name of the field
            context: Current form context (industry, company size, etc.)
            
        Returns:
            List of smart default suggestions
        """
        defaults = []
        
        industry = context.get("industry")
        company_size = context.get("company_size")
        
        try:
            # Industry-based defaults
            if industry and industry in self._industry_patterns:
                industry_data = self._industry_patterns[industry]
                
                if field_name == "budget_range" and "typical_budget_ranges" in industry_data:
                    for budget in industry_data["typical_budget_ranges"][:2]:  # Top 2 suggestions
                        defaults.append(SmartDefault(
                            value=budget,
                            confidence=0.8,
                            reason=f"Common budget range for {industry} companies",
                            source="industry_patterns"
                        ))
                
                elif field_name == "preferred_cloud_providers" and "common_cloud_providers" in industry_data:
                    for provider in industry_data["common_cloud_providers"][:2]:
                        defaults.append(SmartDefault(
                            value=provider,
                            confidence=0.7,
                            reason=f"Popular choice in {industry} industry",
                            source="industry_patterns"
                        ))
                
                elif field_name == "compliance_requirements" and "compliance_requirements" in industry_data:
                    for compliance in industry_data["compliance_requirements"]:
                        defaults.append(SmartDefault(
                            value=compliance,
                            confidence=0.9,
                            reason=f"Required for {industry} industry",
                            source="industry_patterns"
                        ))
                
                elif field_name == "security_level" and "security_level" in industry_data:
                    defaults.append(SmartDefault(
                        value=industry_data["security_level"],
                        confidence=0.8,
                        reason=f"Recommended for {industry} industry",
                        source="industry_patterns"
                    ))
            
            # Company size-based defaults
            if company_size and company_size in self._company_size_patterns:
                size_data = self._company_size_patterns[company_size]
                
                if field_name == "budget_range" and "typical_budgets" in size_data:
                    for budget in size_data["typical_budgets"]:
                        defaults.append(SmartDefault(
                            value=budget,
                            confidence=0.7,
                            reason=f"Typical for {company_size} companies",
                            source="company_size_patterns"
                        ))
                
                elif field_name == "infrastructure_maturity" and "infrastructure_maturity" in size_data:
                    defaults.append(SmartDefault(
                        value=size_data["infrastructure_maturity"],
                        confidence=0.8,
                        reason=f"Common maturity level for {company_size} companies",
                        source="company_size_patterns"
                    ))
                
                elif field_name == "timeline" and "preferred_timeline" in size_data:
                    defaults.append(SmartDefault(
                        value=size_data["preferred_timeline"],
                        confidence=0.7,
                        reason=f"Typical timeline for {company_size} companies",
                        source="company_size_patterns"
                    ))
                
                elif field_name == "expected_data_volume" and "typical_data_volume" in size_data:
                    defaults.append(SmartDefault(
                        value=size_data["typical_data_volume"],
                        confidence=0.6,
                        reason=f"Common data volume for {company_size} companies",
                        source="company_size_patterns"
                    ))
            
            # Combined industry + company size defaults
            if industry and company_size:
                if field_name == "technical_team_size":
                    if industry in self._industry_patterns and company_size in self._company_size_patterns:
                        industry_sizes = self._industry_patterns[industry].get("typical_team_sizes", [])
                        size_range = self._company_size_patterns[company_size].get("team_size_range", (1, 10))
                        
                        # Find intersection of industry typical sizes and company size range
                        for size in industry_sizes:
                            if size_range[0] <= size <= size_range[1]:
                                defaults.append(SmartDefault(
                                    value=str(size),
                                    confidence=0.8,
                                    reason=f"Typical team size for {company_size} {industry} companies",
                                    source="combined_patterns"
                                ))
                                break
        
        except Exception as e:
            logger.error(f"Error generating smart defaults for {field_name}: {str(e)}")
        
        # Sort by confidence and return top suggestions
        defaults.sort(key=lambda x: x.confidence, reverse=True)
        return defaults[:3]  # Return top 3 suggestions
    
    def get_suggestions(self, field_name: str, query: str, context: Dict[str, Any]) -> List[Suggestion]:
        """
        Get auto-completion suggestions for a field.
        
        Args:
            field_name: Name of the field
            query: Current user input
            context: Current form context
            
        Returns:
            List of matching suggestions
        """
        suggestions = []
        
        try:
            # Get base suggestions for the field
            base_suggestions = self._common_suggestions.get(field_name, [])
            
            # Filter suggestions based on query
            if query:
                query_lower = query.lower()
                for suggestion in base_suggestions:
                    if (query_lower in suggestion.value.lower() or 
                        query_lower in suggestion.label.lower() or
                        query_lower in suggestion.description.lower()):
                        # Adjust confidence based on match quality
                        if suggestion.value.lower().startswith(query_lower):
                            suggestion.confidence *= 1.2  # Boost for prefix match
                        suggestions.append(suggestion)
            else:
                suggestions = base_suggestions.copy()
            
            # Add context-aware suggestions
            industry = context.get("industry")
            if industry and field_name == "ai_use_cases":
                industry_use_cases = self._industry_patterns.get(industry, {}).get("common_ai_use_cases", [])
                for use_case in industry_use_cases:
                    # Create suggestion if not already present
                    if not any(s.value == use_case for s in suggestions):
                        suggestions.append(Suggestion(
                            value=use_case,
                            label=use_case.replace("_", " ").title(),
                            description=f"Common in {industry} industry",
                            confidence=0.9,
                            category="industry_specific"
                        ))
            
            # Sort by confidence and relevance
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating suggestions for {field_name}: {str(e)}")
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def get_contextual_help(self, field_name: str, context: Dict[str, Any]) -> Optional[ContextualHelp]:
        """
        Get contextual help for a field.
        
        Args:
            field_name: Name of the field
            context: Current form context
            
        Returns:
            Contextual help information if available
        """
        help_info = self._contextual_help.get(field_name)
        
        if help_info and context:
            # Customize help based on context
            industry = context.get("industry")
            company_size = context.get("company_size")
            
            # Create a copy to avoid modifying the original
            customized_help = ContextualHelp(
                title=help_info.title,
                content=help_info.content,
                examples=help_info.examples.copy(),
                tips=help_info.tips.copy(),
                related_fields=help_info.related_fields.copy(),
                help_type=help_info.help_type
            )
            
            # Add context-specific tips
            if industry and field_name == "compliance_requirements":
                if industry == IndustryType.HEALTHCARE:
                    customized_help.tips.append("Healthcare companies typically need HIPAA compliance")
                elif industry == IndustryType.FINANCE:
                    customized_help.tips.append("Financial services often require SOX and PCI DSS compliance")
            
            if company_size and field_name == "budget_range":
                size_data = self._company_size_patterns.get(company_size, {})
                typical_budgets = size_data.get("typical_budgets", [])
                if typical_budgets:
                    budget_labels = {
                        "under_10k": "Under $10,000",
                        "10k_50k": "$10,000 - $50,000",
                        "50k_100k": "$50,000 - $100,000",
                        "100k_500k": "$100,000 - $500,000",
                        "500k_1m": "$500,000 - $1,000,000",
                        "over_1m": "Over $1,000,000"
                    }
                    budget_range = " or ".join([budget_labels.get(b, b) for b in typical_budgets])
                    customized_help.tips.append(f"Companies of your size typically budget {budget_range}")
            
            return customized_help
        
        return help_info
    
    def should_show_field(self, field_name: str, context: Dict[str, Any]) -> bool:
        """
        Determine if a field should be shown based on progressive disclosure rules.
        
        Args:
            field_name: Name of the field
            context: Current form context
            
        Returns:
            True if field should be shown
        """
        # Basic progressive disclosure rules
        industry = context.get("industry")
        company_size = context.get("company_size")
        current_ai_maturity = context.get("current_ai_maturity")
        
        # Show compliance fields only for certain industries
        if field_name == "compliance_requirements":
            return industry in [IndustryType.HEALTHCARE, IndustryType.FINANCE, IndustryType.GOVERNMENT]
        
        # Show advanced fields only for mature companies
        if field_name in ["advanced_security_features", "custom_integrations"]:
            return (company_size in [CompanySize.LARGE, CompanySize.ENTERPRISE] or 
                   current_ai_maturity in ["production", "advanced"])
        
        # Show team size field only after company size is selected
        if field_name == "technical_team_size":
            return company_size is not None
        
        # Show budget-related fields only after company info is complete
        if field_name in ["budget_range", "cost_optimization_priority"]:
            return industry is not None and company_size is not None
        
        # Default: show all other fields
        return True
    
    def get_field_priority(self, field_name: str, context: Dict[str, Any]) -> int:
        """
        Get field priority for progressive disclosure ordering.
        
        Args:
            field_name: Name of the field
            context: Current form context
            
        Returns:
            Priority score (lower = higher priority)
        """
        # Core business fields have highest priority
        core_fields = {
            "company_name": 1,
            "industry": 2,
            "company_size": 3,
            "contact_email": 4
        }
        
        # Secondary business fields
        secondary_fields = {
            "budget_range": 10,
            "timeline": 11,
            "primary_goals": 12
        }
        
        # Technical fields
        technical_fields = {
            "current_hosting": 20,
            "team_expertise": 21,
            "workload_types": 22
        }
        
        # Advanced/optional fields
        advanced_fields = {
            "compliance_requirements": 30,
            "security_requirements": 31,
            "additional_context": 40
        }
        
        # Return priority or default
        for field_group in [core_fields, secondary_fields, technical_fields, advanced_fields]:
            if field_name in field_group:
                return field_group[field_name]
        
        return 50  # Default priority for unlisted fields


class FormStateManager:
    """Manages form state for save and resume functionality."""
    
    def __init__(self):
        """Initialize the form state manager."""
        self._saved_states: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized form state manager")
    
    def save_form_state(self, form_id: str, user_id: str, form_data: Dict[str, Any], 
                       current_step: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save form state for later resumption.
        
        Args:
            form_id: Unique form identifier
            user_id: User identifier
            form_data: Current form data
            current_step: Current step index
            metadata: Additional metadata
            
        Returns:
            True if save was successful
        """
        try:
            state_key = f"{user_id}:{form_id}"
            
            state = {
                "form_id": form_id,
                "user_id": user_id,
                "form_data": form_data,
                "current_step": current_step,
                "metadata": metadata or {},
                "saved_at": "2024-01-01T00:00:00Z",  # Would use datetime.utcnow().isoformat()
                "version": "1.0"
            }
            
            self._saved_states[state_key] = state
            logger.info(f"Saved form state for {state_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving form state: {str(e)}")
            return False
    
    def load_form_state(self, form_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load saved form state.
        
        Args:
            form_id: Unique form identifier
            user_id: User identifier
            
        Returns:
            Saved form state if available
        """
        try:
            state_key = f"{user_id}:{form_id}"
            state = self._saved_states.get(state_key)
            
            if state:
                logger.info(f"Loaded form state for {state_key}")
                return state
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading form state: {str(e)}")
            return None
    
    def delete_form_state(self, form_id: str, user_id: str) -> bool:
        """
        Delete saved form state.
        
        Args:
            form_id: Unique form identifier
            user_id: User identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            state_key = f"{user_id}:{form_id}"
            
            if state_key in self._saved_states:
                del self._saved_states[state_key]
                logger.info(f"Deleted form state for {state_key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting form state: {str(e)}")
            return False
    
    def list_saved_forms(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all saved forms for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of saved form summaries
        """
        try:
            user_forms = []
            
            for state_key, state in self._saved_states.items():
                if state["user_id"] == user_id:
                    summary = {
                        "form_id": state["form_id"],
                        "current_step": state["current_step"],
                        "saved_at": state["saved_at"],
                        "completion_percentage": self._calculate_completion_percentage(state["form_data"]),
                        "metadata": state.get("metadata", {})
                    }
                    user_forms.append(summary)
            
            # Sort by saved_at descending
            user_forms.sort(key=lambda x: x["saved_at"], reverse=True)
            return user_forms
            
        except Exception as e:
            logger.error(f"Error listing saved forms: {str(e)}")
            return []
    
    def _calculate_completion_percentage(self, form_data: Dict[str, Any]) -> float:
        """Calculate form completion percentage."""
        # Simple calculation based on filled fields
        # In a real implementation, this would be more sophisticated
        total_fields = 20  # Approximate total fields in assessment form
        filled_fields = len([v for v in form_data.values() if v])
        return min(100.0, (filled_fields / total_fields) * 100.0)