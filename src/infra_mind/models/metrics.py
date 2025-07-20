"""
Metrics model for Infra Mind.

Defines system metrics and analytics data structure.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, field_validator


class MetricType(str, Enum):
    """Types of metrics collected."""
    SYSTEM_PERFORMANCE = "system_performance"
    USER_ENGAGEMENT = "user_engagement"
    AGENT_PERFORMANCE = "agent_performance"
    API_USAGE = "api_usage"
    COST_TRACKING = "cost_tracking"
    ERROR_TRACKING = "error_tracking"
    BUSINESS_KPI = "business_kpi"


class MetricCategory(str, Enum):
    """Categories for organizing metrics."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    USER_EXPERIENCE = "user_experience"
    OPERATIONAL = "operational"


class Metric(Document):
    """
    System metrics document model.
    
    Learning Note: This model captures various system metrics for monitoring,
    analytics, and performance optimization.
    """
    
    # Metric identification
    name: str = Indexed()
    metric_type: MetricType = Field(description="Type of metric")
    category: MetricCategory = Field(description="Metric category")
    
    # Metric data
    value: float = Field(description="Metric value")
    unit: str = Field(description="Unit of measurement (ms, count, percentage, etc.)")
    
    # Context and dimensions
    dimensions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metric dimensions for filtering and grouping"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    
    # Source information
    source: str = Field(description="Source of the metric (agent, api, system)")
    source_id: Optional[str] = Field(default=None, description="ID of the source entity")
    
    # Aggregation metadata
    aggregation_period: Optional[str] = Field(
        default=None,
        description="Aggregation period (1m, 5m, 1h, 1d)"
    )
    sample_count: Optional[int] = Field(
        default=None,
        description="Number of samples in aggregated metric"
    )
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "metrics"
        indexes = [
            [("name", 1), ("timestamp", -1)],  # Query metrics by name and time
            [("metric_type", 1), ("timestamp", -1)],  # Query by type and time
            [("source", 1), ("timestamp", -1)],  # Query by source and time
            [("timestamp", -1)],  # Time-series queries
            [("category", 1)],  # Query by category
        ]
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """Ensure metric value is finite."""
        if not isinstance(v, (int, float)) or not (-float('inf') < v < float('inf')):
            raise ValueError("Metric value must be a finite number")
        return float(v)
    
    @classmethod
    async def record_metric(
        cls,
        name: str,
        value: float,
        metric_type: MetricType,
        category: MetricCategory,
        unit: str = "count",
        source: str = "system",
        dimensions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None
    ) -> "Metric":
        """Record a new metric."""
        metric = cls(
            name=name,
            value=value,
            metric_type=metric_type,
            category=category,
            unit=unit,
            source=source,
            dimensions=dimensions or {},
            tags=tags or [],
            timestamp=timestamp or datetime.utcnow()
        )
        await metric.insert()
        return metric
    
    def __str__(self) -> str:
        """String representation of the metric."""
        return f"Metric(name={self.name}, value={self.value} {self.unit})"


class AgentMetrics(Document):
    """
    Agent-specific performance metrics.
    
    Learning Note: Specialized metrics for tracking AI agent performance
    and quality of recommendations.
    """
    
    # Agent identification
    agent_name: str = Indexed()
    agent_version: str = Field(description="Agent version")
    assessment_id: Optional[str] = Field(default=None, description="Related assessment ID")
    
    # Performance metrics
    execution_time_seconds: float = Field(default=0.0, description="Time taken to complete task")
    memory_usage_mb: Optional[float] = Field(default=None, description="Memory usage in MB")
    api_calls_made: int = Field(default=0, description="Number of API calls made")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Agent's confidence in its output"
    )
    validation_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Validation score from other agents"
    )
    user_feedback_score: Optional[float] = Field(
        default=None, ge=0.0, le=5.0,
        description="User feedback score (1-5)"
    )
    
    # Output metrics
    recommendations_generated: int = Field(default=0, description="Number of recommendations")
    services_recommended: int = Field(default=0, description="Number of services recommended")
    cost_estimates_provided: int = Field(default=0, description="Number of cost estimates")
    
    # Error tracking
    errors_encountered: int = Field(default=0, description="Number of errors")
    warnings_generated: int = Field(default=0, description="Number of warnings")
    
    # Business impact
    estimated_cost_savings: Optional[float] = Field(
        default=None,
        description="Estimated cost savings from recommendations"
    )
    business_value_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Estimated business value score"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Metric tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    # Timestamps
    started_at: datetime = Field(description="When agent started processing")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="When agent completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "agent_metrics"
        indexes = [
            [("agent_name", 1), ("completed_at", -1)],  # Query by agent and time
            [("assessment_id", 1)],  # Query by assessment
            [("confidence_score", -1)],  # Query by confidence
            [("execution_time_seconds", 1)],  # Query by performance
        ]
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total execution duration."""
        return (self.completed_at - self.started_at).total_seconds()
    
    @classmethod
    async def create_for_agent(
        cls,
        agent_name: str,
        agent_version: str,
        started_at: datetime,
        assessment_id: Optional[str] = None
    ) -> "AgentMetrics":
        """Create metrics record for an agent execution."""
        metrics = cls(
            agent_name=agent_name,
            agent_version=agent_version,
            assessment_id=assessment_id,
            started_at=started_at
        )
        await metrics.insert()
        return metrics
    
    def update_performance(
        self,
        execution_time: float,
        memory_usage: Optional[float] = None,
        api_calls: int = 0
    ) -> None:
        """Update performance metrics."""
        self.execution_time_seconds = execution_time
        if memory_usage is not None:
            self.memory_usage_mb = memory_usage
        self.api_calls_made = api_calls
    
    def update_quality(
        self,
        confidence_score: Optional[float] = None,
        validation_score: Optional[float] = None,
        user_feedback: Optional[float] = None
    ) -> None:
        """Update quality metrics."""
        if confidence_score is not None:
            self.confidence_score = confidence_score
        if validation_score is not None:
            self.validation_score = validation_score
        if user_feedback is not None:
            self.user_feedback_score = user_feedback
    
    def update_output(
        self,
        recommendations: int = 0,
        services: int = 0,
        cost_estimates: int = 0
    ) -> None:
        """Update output metrics."""
        self.recommendations_generated = recommendations
        self.services_recommended = services
        self.cost_estimates_provided = cost_estimates
    
    def record_error(self, error_count: int = 1, warning_count: int = 0) -> None:
        """Record errors and warnings."""
        self.errors_encountered += error_count
        self.warnings_generated += warning_count
    
    def __str__(self) -> str:
        """String representation of agent metrics."""
        return f"AgentMetrics(agent={self.agent_name}, duration={self.duration_seconds:.2f}s)"