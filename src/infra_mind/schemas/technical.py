"""
Technical requirements schemas for Infra Mind.

Learning Note: These models capture the technical specifications and
constraints that drive infrastructure architecture decisions.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import Field, field_validator, model_validator
from decimal import Decimal
from enum import Enum

from .base import (
    BaseSchema, 
    WorkloadType, 
    CloudProvider,
    Priority
)


class DatabaseType(str, Enum):
    """Database technology preferences."""
    RELATIONAL = "relational"  # PostgreSQL, MySQL
    DOCUMENT = "document"      # MongoDB, DynamoDB
    KEY_VALUE = "key_value"    # Redis, DynamoDB
    GRAPH = "graph"           # Neo4j, Amazon Neptune
    TIME_SERIES = "time_series"  # InfluxDB, TimescaleDB
    SEARCH = "search"         # Elasticsearch, OpenSearch
    NO_PREFERENCE = "no_preference"


class ArchitecturePattern(str, Enum):
    """Preferred architecture patterns."""
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"
    SERVERLESS = "serverless"
    HYBRID = "hybrid"
    NO_PREFERENCE = "no_preference"


class DeploymentModel(str, Enum):
    """Deployment model preferences."""
    CONTAINERS = "containers"
    VIRTUAL_MACHINES = "virtual_machines"
    SERVERLESS = "serverless"
    BARE_METAL = "bare_metal"
    HYBRID = "hybrid"
    NO_PREFERENCE = "no_preference"


class PerformanceRequirement(BaseSchema):
    """
    Performance requirements and SLA expectations.
    
    Learning Note: Performance requirements directly impact
    infrastructure choices and costs.
    """
    # Response time requirements
    api_response_time_ms: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum acceptable API response time in milliseconds"
    )
    page_load_time_ms: Optional[int] = Field(
        default=None,
        ge=100,
        le=30000,
        description="Maximum acceptable page load time in milliseconds"
    )
    
    # Throughput requirements
    requests_per_second: Optional[int] = Field(
        default=None,
        ge=1,
        description="Expected requests per second at peak"
    )
    concurrent_users: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum concurrent users"
    )
    
    # Availability requirements
    uptime_percentage: Optional[Decimal] = Field(
        default=None,
        ge=90.0,
        le=99.999,
        description="Required uptime percentage (SLA)"
    )
    max_downtime_minutes_per_month: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum acceptable downtime per month in minutes"
    )
    
    # Data processing requirements
    batch_processing_time_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=168,  # 1 week
        description="Maximum time for batch processing jobs"
    )
    real_time_processing_required: bool = Field(
        default=False,
        description="Is real-time data processing required"
    )
    
    @field_validator('uptime_percentage')
    @classmethod
    def validate_uptime(cls, v):
        """Convert uptime percentage to appropriate SLA tier."""
        if v is not None:
            if v >= 99.99:
                # This will require expensive high-availability setup
                pass
            elif v >= 99.9:
                # Standard production setup
                pass
            elif v >= 99.0:
                # Basic production setup
                pass
        return v


class ScalabilityRequirement(BaseSchema):
    """
    Scalability requirements and growth expectations.
    
    Learning Note: Scalability requirements determine whether we need
    auto-scaling, load balancers, and distributed architectures.
    """
    # Current scale
    current_data_size_gb: Optional[int] = Field(
        default=None,
        ge=0,
        description="Current data size in GB"
    )
    current_daily_transactions: Optional[int] = Field(
        default=None,
        ge=0,
        description="Current daily transaction volume"
    )
    
    # Growth projections
    expected_data_growth_rate: Optional[str] = Field(
        default=None,
        description="Expected data growth rate (e.g., '10% monthly', '2x yearly')"
    )
    peak_load_multiplier: Optional[Decimal] = Field(
        default=None,
        ge=1.0,
        le=100.0,
        description="Peak load as multiplier of average load"
    )
    
    # Scaling preferences
    auto_scaling_required: bool = Field(
        default=False,
        description="Is automatic scaling required"
    )
    global_distribution_required: bool = Field(
        default=False,
        description="Does the application need global distribution"
    )
    cdn_required: bool = Field(
        default=False,
        description="Is a Content Delivery Network required"
    )
    
    # Capacity planning
    planned_regions: List[str] = Field(
        default_factory=list,
        description="Geographic regions where service will be deployed"
    )
    disaster_recovery_regions: List[str] = Field(
        default_factory=list,
        description="Regions for disaster recovery"
    )


class SecurityRequirement(BaseSchema):
    """
    Security requirements and constraints.
    
    Learning Note: Security requirements often drive compliance
    and architecture decisions.
    """
    # Data protection
    encryption_at_rest_required: bool = Field(
        default=True,
        description="Is encryption at rest required"
    )
    encryption_in_transit_required: bool = Field(
        default=True,
        description="Is encryption in transit required"
    )
    
    # Access control
    multi_factor_auth_required: bool = Field(
        default=False,
        description="Is multi-factor authentication required"
    )
    single_sign_on_required: bool = Field(
        default=False,
        description="Is single sign-on integration required"
    )
    role_based_access_control: bool = Field(
        default=True,
        description="Is role-based access control required"
    )
    
    # Network security
    vpc_isolation_required: bool = Field(
        default=True,
        description="Is VPC/network isolation required"
    )
    firewall_required: bool = Field(
        default=True,
        description="Are firewall rules required"
    )
    ddos_protection_required: bool = Field(
        default=False,
        description="Is DDoS protection required"
    )
    
    # Monitoring and auditing
    security_monitoring_required: bool = Field(
        default=True,
        description="Is security monitoring required"
    )
    audit_logging_required: bool = Field(
        default=True,
        description="Is audit logging required"
    )
    vulnerability_scanning_required: bool = Field(
        default=False,
        description="Is automated vulnerability scanning required"
    )
    
    # Compliance-specific requirements
    data_loss_prevention_required: bool = Field(
        default=False,
        description="Is data loss prevention required"
    )
    backup_encryption_required: bool = Field(
        default=True,
        description="Is backup encryption required"
    )


class IntegrationRequirement(BaseSchema):
    """
    Integration requirements with existing systems.
    
    Learning Note: Integration requirements often constrain
    technology choices and architecture patterns.
    """
    # Existing systems
    existing_databases: List[str] = Field(
        default_factory=list,
        description="Existing databases that need integration"
    )
    existing_apis: List[str] = Field(
        default_factory=list,
        description="Existing APIs that need integration"
    )
    legacy_systems: List[str] = Field(
        default_factory=list,
        description="Legacy systems requiring integration"
    )
    
    # Third-party services
    payment_processors: List[str] = Field(
        default_factory=list,
        description="Payment processors to integrate"
    )
    analytics_platforms: List[str] = Field(
        default_factory=list,
        description="Analytics platforms to integrate"
    )
    marketing_tools: List[str] = Field(
        default_factory=list,
        description="Marketing tools requiring integration"
    )
    
    # API requirements
    rest_api_required: bool = Field(default=True, description="REST API required")
    graphql_api_required: bool = Field(default=False, description="GraphQL API required")
    websocket_support_required: bool = Field(default=False, description="WebSocket support required")
    
    # Data synchronization
    real_time_sync_required: bool = Field(
        default=False,
        description="Real-time data synchronization required"
    )
    batch_sync_acceptable: bool = Field(
        default=True,
        description="Batch data synchronization acceptable"
    )


class TechnicalRequirements(BaseSchema):
    """
    Complete technical requirements for infrastructure assessment.
    
    Learning Note: This model captures all technical constraints
    and preferences that will guide infrastructure recommendations.
    """
    
    # Application characteristics
    workload_types: List[WorkloadType] = Field(
        description="Types of workloads to support"
    )
    architecture_preference: ArchitecturePattern = Field(
        default=ArchitecturePattern.NO_PREFERENCE,
        description="Preferred architecture pattern"
    )
    deployment_model: DeploymentModel = Field(
        default=DeploymentModel.NO_PREFERENCE,
        description="Preferred deployment model"
    )
    
    # Technology preferences
    preferred_programming_languages: List[str] = Field(
        default_factory=list,
        description="Programming languages used by the team"
    )
    database_preferences: List[DatabaseType] = Field(
        default_factory=list,
        description="Preferred database technologies"
    )
    preferred_cloud_services: List[str] = Field(
        default_factory=list,
        description="Specific cloud services the team prefers"
    )
    
    # Requirements
    performance_requirements: PerformanceRequirement = Field(
        description="Performance and SLA requirements"
    )
    scalability_requirements: ScalabilityRequirement = Field(
        description="Scalability and growth requirements"
    )
    security_requirements: SecurityRequirement = Field(
        description="Security and compliance requirements"
    )
    integration_requirements: IntegrationRequirement = Field(
        description="Integration with existing systems"
    )
    
    # Infrastructure preferences
    containerization_preference: Priority = Field(
        default=Priority.MEDIUM,
        description="Preference for containerized deployment"
    )
    managed_services_preference: Priority = Field(
        default=Priority.HIGH,
        description="Preference for managed cloud services"
    )
    open_source_preference: Priority = Field(
        default=Priority.MEDIUM,
        description="Preference for open source solutions"
    )
    
    # Operational requirements
    monitoring_requirements: List[str] = Field(
        default_factory=list,
        description="Specific monitoring and observability requirements"
    )
    backup_requirements: List[str] = Field(
        default_factory=list,
        description="Backup and disaster recovery requirements"
    )
    maintenance_window_hours: Optional[str] = Field(
        default=None,
        description="Acceptable maintenance window (e.g., 'Sunday 2-4 AM UTC')"
    )
    
    # Development and deployment
    ci_cd_requirements: List[str] = Field(
        default_factory=list,
        description="CI/CD pipeline requirements"
    )
    testing_environment_requirements: List[str] = Field(
        default_factory=list,
        description="Testing environment requirements"
    )
    
    # Additional technical context
    current_infrastructure: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Description of current infrastructure setup"
    )
    technical_constraints: List[str] = Field(
        default_factory=list,
        description="Technical constraints or limitations"
    )
    
    @field_validator('workload_types')
    @classmethod
    def validate_workload_types(cls, v):
        """Ensure at least one workload type is specified."""
        if not v:
            raise ValueError("At least one workload type must be specified")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self):
        """Validate consistency between different requirements."""
        # Check if real-time requirements are consistent
        if (self.performance_requirements.real_time_processing_required and 
            not self.integration_requirements.real_time_sync_required):
            # This might be a warning rather than an error
            pass
        
        # Check if global distribution is consistent with regions
        if (self.scalability_requirements.global_distribution_required and 
            len(self.scalability_requirements.planned_regions) < 2):
            raise ValueError("Global distribution requires multiple regions")
        
        return self


# Request/Response models for API
class TechnicalRequirementsCreate(TechnicalRequirements):
    """Schema for creating technical requirements."""
    pass


class TechnicalRequirementsUpdate(BaseSchema):
    """Schema for updating technical requirements (all fields optional)."""
    workload_types: Optional[List[WorkloadType]] = None
    architecture_preference: Optional[ArchitecturePattern] = None
    deployment_model: Optional[DeploymentModel] = None
    preferred_programming_languages: Optional[List[str]] = None
    database_preferences: Optional[List[DatabaseType]] = None
    preferred_cloud_services: Optional[List[str]] = None
    performance_requirements: Optional[PerformanceRequirement] = None
    scalability_requirements: Optional[ScalabilityRequirement] = None
    security_requirements: Optional[SecurityRequirement] = None
    integration_requirements: Optional[IntegrationRequirement] = None
    containerization_preference: Optional[Priority] = None
    managed_services_preference: Optional[Priority] = None
    open_source_preference: Optional[Priority] = None
    monitoring_requirements: Optional[List[str]] = None
    backup_requirements: Optional[List[str]] = None
    maintenance_window_hours: Optional[str] = None
    ci_cd_requirements: Optional[List[str]] = None
    testing_environment_requirements: Optional[List[str]] = None
    current_infrastructure: Optional[str] = Field(default=None, max_length=2000)
    technical_constraints: Optional[List[str]] = None


class TechnicalRequirementsResponse(TechnicalRequirements):
    """Schema for technical requirements API responses."""
    id: str = Field(description="Unique identifier")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")