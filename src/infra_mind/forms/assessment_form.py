"""
Assessment form implementation for collecting business and technical requirements.

Provides multi-step forms for gathering comprehensive requirements from users.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseForm, FormStep, FormField, FormFieldType
from .validators import FormValidator, create_business_validator, create_technical_validator
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class BusinessRequirementsForm(BaseForm):
    """Form for collecting business requirements."""
    
    def _initialize_form(self) -> None:
        """Initialize the business requirements form structure."""
        # Step 1: Company Information
        company_step = FormStep(
            id="company_info",
            title="Company Information",
            description="Tell us about your company and business context",
            order=1
        )
        
        # Company name field
        company_step.add_field(FormField(
            name="company_name",
            label="Company Name",
            field_type=FormFieldType.TEXT,
            required=True,
            placeholder="Enter your company name",
            help_text="The legal name of your organization",
            min_length=2,
            max_length=100
        ))
        
        # Industry field
        company_step.add_field(FormField(
            name="industry",
            label="Industry",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="Select the industry that best describes your business",
            options=[
                {"value": "technology", "label": "Technology"},
                {"value": "healthcare", "label": "Healthcare"},
                {"value": "finance", "label": "Financial Services"},
                {"value": "retail", "label": "Retail & E-commerce"},
                {"value": "manufacturing", "label": "Manufacturing"},
                {"value": "education", "label": "Education"},
                {"value": "government", "label": "Government"},
                {"value": "nonprofit", "label": "Non-profit"},
                {"value": "consulting", "label": "Consulting"},
                {"value": "media", "label": "Media & Entertainment"},
                {"value": "other", "label": "Other"}
            ]
        ))
        
        # Company size field
        company_step.add_field(FormField(
            name="company_size",
            label="Company Size",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="Number of employees in your organization",
            options=[
                {"value": "startup", "label": "Startup (1-10 employees)"},
                {"value": "small", "label": "Small (11-50 employees)"},
                {"value": "medium", "label": "Medium (51-200 employees)"},
                {"value": "large", "label": "Large (201-1000 employees)"},
                {"value": "enterprise", "label": "Enterprise (1000+ employees)"}
            ]
        ))
        
        # Contact email field
        company_step.add_field(FormField(
            name="contact_email",
            label="Contact Email",
            field_type=FormFieldType.EMAIL,
            required=True,
            placeholder="your.email@company.com",
            help_text="Primary contact email for this assessment"
        ))
        
        self.add_step(company_step)
        
        # Step 2: Business Goals and Budget
        goals_step = FormStep(
            id="business_goals",
            title="Business Goals & Budget",
            description="Help us understand your objectives and budget constraints",
            order=2
        )
        
        # Primary business goals
        goals_step.add_field(FormField(
            name="primary_goals",
            label="Primary Business Goals",
            field_type=FormFieldType.MULTISELECT,
            required=True,
            help_text="Select all goals that apply to your AI infrastructure initiative",
            options=[
                {"value": "cost_reduction", "label": "Reduce operational costs"},
                {"value": "scalability", "label": "Improve scalability"},
                {"value": "performance", "label": "Enhance performance"},
                {"value": "reliability", "label": "Increase reliability"},
                {"value": "security", "label": "Strengthen security"},
                {"value": "compliance", "label": "Meet compliance requirements"},
                {"value": "innovation", "label": "Enable innovation"},
                {"value": "time_to_market", "label": "Reduce time to market"},
                {"value": "automation", "label": "Increase automation"},
                {"value": "data_insights", "label": "Improve data insights"}
            ]
        ))
        
        # Budget range
        goals_step.add_field(FormField(
            name="budget_range",
            label="Annual Budget Range",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="Estimated annual budget for AI infrastructure",
            options=[
                {"value": "under_10k", "label": "Under $10,000"},
                {"value": "10k_50k", "label": "$10,000 - $50,000"},
                {"value": "50k_100k", "label": "$50,000 - $100,000"},
                {"value": "100k_500k", "label": "$100,000 - $500,000"},
                {"value": "500k_1m", "label": "$500,000 - $1,000,000"},
                {"value": "over_1m", "label": "Over $1,000,000"}
            ]
        ))
        
        # Timeline
        goals_step.add_field(FormField(
            name="timeline",
            label="Implementation Timeline",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="When do you need the infrastructure to be operational?",
            options=[
                {"value": "immediate", "label": "Immediate (within 1 month)"},
                {"value": "short_term", "label": "Short-term (1-3 months)"},
                {"value": "medium_term", "label": "Medium-term (3-6 months)"},
                {"value": "long_term", "label": "Long-term (6+ months)"},
                {"value": "flexible", "label": "Flexible timeline"}
            ]
        ))
        
        # Success metrics
        goals_step.add_field(FormField(
            name="success_metrics",
            label="Success Metrics",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="How will you measure the success of this initiative?",
            options=[
                {"value": "cost_savings", "label": "Cost savings percentage"},
                {"value": "performance_improvement", "label": "Performance improvement"},
                {"value": "uptime_sla", "label": "Uptime/SLA metrics"},
                {"value": "user_satisfaction", "label": "User satisfaction scores"},
                {"value": "time_to_deployment", "label": "Time to deployment"},
                {"value": "roi", "label": "Return on investment"},
                {"value": "compliance_score", "label": "Compliance score"},
                {"value": "security_incidents", "label": "Security incident reduction"}
            ]
        ))
        
        self.add_step(goals_step)
        
        # Step 3: Current State and Challenges
        current_state_step = FormStep(
            id="current_state",
            title="Current State & Challenges",
            description="Tell us about your current situation and main challenges",
            order=3
        )
        
        # Current infrastructure maturity
        current_state_step.add_field(FormField(
            name="infrastructure_maturity",
            label="Current Infrastructure Maturity",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="How would you describe your current infrastructure?",
            options=[
                {"value": "none", "label": "No cloud infrastructure"},
                {"value": "basic", "label": "Basic cloud usage"},
                {"value": "intermediate", "label": "Intermediate cloud adoption"},
                {"value": "advanced", "label": "Advanced cloud-native"},
                {"value": "expert", "label": "Expert/Multi-cloud"}
            ]
        ))
        
        # Main challenges
        current_state_step.add_field(FormField(
            name="main_challenges",
            label="Main Challenges",
            field_type=FormFieldType.MULTISELECT,
            required=True,
            help_text="What are your biggest challenges with current infrastructure?",
            options=[
                {"value": "high_costs", "label": "High operational costs"},
                {"value": "poor_performance", "label": "Poor performance"},
                {"value": "scalability_issues", "label": "Scalability limitations"},
                {"value": "reliability_problems", "label": "Reliability issues"},
                {"value": "security_concerns", "label": "Security vulnerabilities"},
                {"value": "compliance_gaps", "label": "Compliance gaps"},
                {"value": "lack_expertise", "label": "Lack of technical expertise"},
                {"value": "legacy_systems", "label": "Legacy system constraints"},
                {"value": "vendor_lock_in", "label": "Vendor lock-in concerns"},
                {"value": "data_silos", "label": "Data silos and integration issues"}
            ]
        ))
        
        # Additional context
        current_state_step.add_field(FormField(
            name="additional_context",
            label="Additional Context",
            field_type=FormFieldType.TEXTAREA,
            required=False,
            placeholder="Any additional information that would help us understand your situation...",
            help_text="Optional: Provide any additional context about your business needs or constraints",
            max_length=1000
        ))
        
        self.add_step(current_state_step)


class TechnicalRequirementsForm(BaseForm):
    """Form for collecting technical requirements."""
    
    def _initialize_form(self) -> None:
        """Initialize the technical requirements form structure."""
        # Step 1: Current Infrastructure
        current_infra_step = FormStep(
            id="current_infrastructure",
            title="Current Infrastructure",
            description="Tell us about your existing technical setup",
            order=1
        )
        
        # Current hosting
        current_infra_step.add_field(FormField(
            name="current_hosting",
            label="Current Hosting Environment",
            field_type=FormFieldType.MULTISELECT,
            required=True,
            help_text="Where is your infrastructure currently hosted?",
            options=[
                {"value": "on_premises", "label": "On-premises data center"},
                {"value": "aws", "label": "Amazon Web Services (AWS)"},
                {"value": "azure", "label": "Microsoft Azure"},
                {"value": "gcp", "label": "Google Cloud Platform (GCP)"},
                {"value": "other_cloud", "label": "Other cloud provider"},
                {"value": "hybrid", "label": "Hybrid (mix of on-premises and cloud)"},
                {"value": "none", "label": "No existing infrastructure"}
            ]
        ))
        
        # Current technologies
        current_infra_step.add_field(FormField(
            name="current_technologies",
            label="Current Technologies",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="What technologies are you currently using?",
            options=[
                {"value": "containers", "label": "Containers (Docker)"},
                {"value": "kubernetes", "label": "Kubernetes"},
                {"value": "serverless", "label": "Serverless functions"},
                {"value": "microservices", "label": "Microservices architecture"},
                {"value": "databases", "label": "Managed databases"},
                {"value": "message_queues", "label": "Message queues"},
                {"value": "load_balancers", "label": "Load balancers"},
                {"value": "cdn", "label": "Content Delivery Network (CDN)"},
                {"value": "monitoring", "label": "Monitoring and logging"},
                {"value": "ci_cd", "label": "CI/CD pipelines"}
            ]
        ))
        
        # Team expertise
        current_infra_step.add_field(FormField(
            name="team_expertise",
            label="Team Technical Expertise",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="What's the technical expertise level of your team?",
            options=[
                {"value": "beginner", "label": "Beginner (limited cloud experience)"},
                {"value": "intermediate", "label": "Intermediate (some cloud experience)"},
                {"value": "advanced", "label": "Advanced (extensive cloud experience)"},
                {"value": "expert", "label": "Expert (cloud architects/specialists)"},
                {"value": "mixed", "label": "Mixed (varying levels of expertise)"}
            ]
        ))
        
        self.add_step(current_infra_step)
        
        # Step 2: Workload Requirements
        workload_step = FormStep(
            id="workload_requirements",
            title="Workload Requirements",
            description="Describe your application workloads and requirements",
            order=2
        )
        
        # Workload types
        workload_step.add_field(FormField(
            name="workload_types",
            label="Workload Types",
            field_type=FormFieldType.MULTISELECT,
            required=True,
            help_text="What types of workloads will you be running?",
            options=[
                {"value": "web_applications", "label": "Web applications"},
                {"value": "apis", "label": "REST/GraphQL APIs"},
                {"value": "databases", "label": "Databases"},
                {"value": "data_processing", "label": "Data processing/ETL"},
                {"value": "machine_learning", "label": "Machine learning/AI"},
                {"value": "batch_processing", "label": "Batch processing"},
                {"value": "real_time_processing", "label": "Real-time/streaming processing"},
                {"value": "file_storage", "label": "File storage and sharing"},
                {"value": "backup_archive", "label": "Backup and archival"},
                {"value": "development_testing", "label": "Development and testing"}
            ]
        ))
        
        # Expected users
        workload_step.add_field(FormField(
            name="expected_users",
            label="Expected Number of Users",
            field_type=FormFieldType.NUMBER,
            required=True,
            help_text="Estimated number of concurrent users",
            min_value=1,
            max_value=10000000,
            placeholder="e.g., 1000"
        ))
        
        # Data volume
        workload_step.add_field(FormField(
            name="data_volume",
            label="Data Volume",
            field_type=FormFieldType.SELECT,
            required=True,
            help_text="Estimated amount of data you'll be processing/storing",
            options=[
                {"value": "under_1gb", "label": "Under 1 GB"},
                {"value": "1gb_10gb", "label": "1 GB - 10 GB"},
                {"value": "10gb_100gb", "label": "10 GB - 100 GB"},
                {"value": "100gb_1tb", "label": "100 GB - 1 TB"},
                {"value": "1tb_10tb", "label": "1 TB - 10 TB"},
                {"value": "over_10tb", "label": "Over 10 TB"}
            ]
        ))
        
        # Performance requirements
        workload_step.add_field(FormField(
            name="performance_requirements",
            label="Performance Requirements",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="What performance characteristics are important?",
            options=[
                {"value": "low_latency", "label": "Low latency (< 100ms)"},
                {"value": "high_throughput", "label": "High throughput"},
                {"value": "high_availability", "label": "High availability (99.9%+)"},
                {"value": "auto_scaling", "label": "Auto-scaling capabilities"},
                {"value": "global_distribution", "label": "Global distribution"},
                {"value": "disaster_recovery", "label": "Disaster recovery"},
                {"value": "backup_restore", "label": "Backup and restore"},
                {"value": "monitoring_alerting", "label": "Monitoring and alerting"}
            ]
        ))
        
        self.add_step(workload_step)
        
        # Step 3: Cloud Preferences and Compliance
        preferences_step = FormStep(
            id="cloud_preferences",
            title="Cloud Preferences & Compliance",
            description="Specify your cloud provider preferences and compliance needs",
            order=3
        )
        
        # Preferred cloud providers
        preferences_step.add_field(FormField(
            name="preferred_cloud_providers",
            label="Preferred Cloud Providers",
            field_type=FormFieldType.MULTISELECT,
            required=True,
            help_text="Which cloud providers would you like to consider?",
            options=[
                {"value": "aws", "label": "Amazon Web Services (AWS)"},
                {"value": "azure", "label": "Microsoft Azure"},
                {"value": "gcp", "label": "Google Cloud Platform (GCP)"},
                {"value": "multi_cloud", "label": "Multi-cloud approach"},
                {"value": "no_preference", "label": "No preference"}
            ]
        ))
        
        # Geographic requirements
        preferences_step.add_field(FormField(
            name="geographic_requirements",
            label="Geographic Requirements",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="Where do you need your infrastructure to be located?",
            options=[
                {"value": "north_america", "label": "North America"},
                {"value": "europe", "label": "Europe"},
                {"value": "asia_pacific", "label": "Asia Pacific"},
                {"value": "south_america", "label": "South America"},
                {"value": "africa", "label": "Africa"},
                {"value": "middle_east", "label": "Middle East"},
                {"value": "global", "label": "Global presence needed"},
                {"value": "no_requirement", "label": "No specific requirement"}
            ]
        ))
        
        # Compliance requirements
        preferences_step.add_field(FormField(
            name="compliance_requirements",
            label="Compliance Requirements",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="What compliance standards do you need to meet?",
            options=[
                {"value": "gdpr", "label": "GDPR (General Data Protection Regulation)"},
                {"value": "hipaa", "label": "HIPAA (Health Insurance Portability)"},
                {"value": "sox", "label": "SOX (Sarbanes-Oxley Act)"},
                {"value": "pci_dss", "label": "PCI DSS (Payment Card Industry)"},
                {"value": "iso_27001", "label": "ISO 27001 (Information Security)"},
                {"value": "fips_140_2", "label": "FIPS 140-2 (Cryptographic Standards)"},
                {"value": "fedramp", "label": "FedRAMP (Federal Risk Authorization)"},
                {"value": "other", "label": "Other compliance requirements"},
                {"value": "none", "label": "No specific compliance requirements"}
            ]
        ))
        
        # Security requirements
        preferences_step.add_field(FormField(
            name="security_requirements",
            label="Security Requirements",
            field_type=FormFieldType.MULTISELECT,
            required=False,
            help_text="What security features are important to you?",
            options=[
                {"value": "encryption_at_rest", "label": "Encryption at rest"},
                {"value": "encryption_in_transit", "label": "Encryption in transit"},
                {"value": "network_isolation", "label": "Network isolation (VPC)"},
                {"value": "access_control", "label": "Identity and access management"},
                {"value": "audit_logging", "label": "Audit logging"},
                {"value": "vulnerability_scanning", "label": "Vulnerability scanning"},
                {"value": "ddos_protection", "label": "DDoS protection"},
                {"value": "waf", "label": "Web Application Firewall (WAF)"},
                {"value": "secrets_management", "label": "Secrets management"},
                {"value": "certificate_management", "label": "Certificate management"}
            ]
        ))
        
        self.add_step(preferences_step)


class AssessmentForm(BaseForm):
    """Complete assessment form combining business and technical requirements."""
    
    def __init__(self, form_id: Optional[str] = None):
        """Initialize the assessment form."""
        super().__init__(form_id)
        self.business_validator = create_business_validator()
        self.technical_validator = create_technical_validator()
    
    def _initialize_form(self) -> None:
        """Initialize the complete assessment form structure."""
        # Create business requirements form and copy its steps
        business_form = BusinessRequirementsForm()
        for step in business_form.steps:
            # Adjust step IDs to avoid conflicts
            step.id = f"business_{step.id}"
            step.metadata["section"] = "business"
            self.add_step(step)
        
        # Create technical requirements form and copy its steps
        technical_form = TechnicalRequirementsForm()
        for step in technical_form.steps:
            # Adjust step IDs and order to come after business steps
            step.id = f"technical_{step.id}"
            step.order += len(business_form.steps)
            step.metadata["section"] = "technical"
            self.add_step(step)
    
    def validate_step(self, step_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate step data using appropriate validator."""
        # Get base validation from parent class
        errors = super().validate_step(step_id, data)
        
        # Apply additional validation based on step section
        step = self.get_step(step_id)
        if step and step.metadata.get("section") == "business":
            # Use business validator
            validation_errors = self.business_validator.get_error_messages(data, self.form_data)
            for field_name, field_errors in validation_errors.items():
                if field_name in errors:
                    errors[field_name].extend(field_errors)
                else:
                    errors[field_name] = field_errors
        
        elif step and step.metadata.get("section") == "technical":
            # Use technical validator
            validation_errors = self.technical_validator.get_error_messages(data, self.form_data)
            for field_name, field_errors in validation_errors.items():
                if field_name in errors:
                    errors[field_name].extend(field_errors)
                else:
                    errors[field_name] = field_errors
        
        return errors
    
    def create_assessment(self) -> Optional[Assessment]:
        """
        Create an Assessment object from the completed form data.
        
        Returns:
            Assessment object if form is complete and valid, None otherwise
        """
        if not self.is_form_complete():
            logger.warning(f"Cannot create assessment from incomplete form {self.form_id}")
            return None
        
        try:
            # Extract business and technical requirements
            business_data = {}
            technical_data = {}
            
            for field_name, value in self.form_data.items():
                # Categorize data based on field names and step metadata
                if field_name in ["company_name", "industry", "company_size", "contact_email", 
                                "primary_goals", "budget_range", "timeline", "success_metrics",
                                "infrastructure_maturity", "main_challenges", "additional_context"]:
                    business_data[field_name] = value
                else:
                    technical_data[field_name] = value
            
            # Create assessment with form data
            assessment = Assessment(
                title=f"Assessment for {business_data.get('company_name', 'Unknown Company')}",
                description=f"Generated from form {self.form_id}",
                user_id="form_user",  # This would come from authentication in real app
                business_requirements=business_data,
                technical_requirements=technical_data,
                source="web_form",
                tags=["form_generated"],
                completion_percentage=100.0
            )
            
            logger.info(f"Created assessment from form {self.form_id}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error creating assessment from form {self.form_id}: {str(e)}", exc_info=True)
            return None