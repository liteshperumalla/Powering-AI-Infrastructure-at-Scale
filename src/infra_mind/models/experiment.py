"""
Experiment model for A/B testing framework.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field
from enum import Enum


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(str, Enum):
    CONTROL = "control"
    TREATMENT = "treatment"


class ExperimentVariant(Document):
    """Experiment variant configuration."""
    
    name: str = Field(description="Variant name")
    type: VariantType = Field(description="Variant type")
    traffic_percentage: float = Field(ge=0, le=100, description="Traffic percentage")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Variant configuration")
    description: Optional[str] = Field(default=None, description="Variant description")
    
    class Settings:
        name = "experiment_variants"


class Experiment(Document):
    """A/B test experiment model."""
    
    # Basic info
    name: str = Field(description="Experiment name")
    description: str = Field(description="Experiment description")
    feature_flag: str = Field(description="Feature flag identifier")
    
    # Status and timing
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    
    # Configuration
    variants: List[str] = Field(default_factory=list, description="Variant IDs")
    target_metric: str = Field(description="Primary metric to optimize")
    secondary_metrics: List[str] = Field(default_factory=list, description="Secondary metrics")
    
    # Targeting and segmentation
    segment_filters: Dict[str, Any] = Field(default_factory=dict, description="User segmentation")
    
    # Statistics
    minimum_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    statistical_power: float = Field(default=0.8, ge=0.5, le=0.99)
    minimum_detectable_effect: float = Field(default=0.05, ge=0.01)
    max_duration_days: int = Field(default=30, ge=1)
    
    # Metadata
    created_by: str = Field(description="User who created the experiment")
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)
    
    class Settings:
        name = "experiments"
        indexes = [
            "feature_flag",
            "status",
            "created_by",
            [("status", 1), ("created_at", -1)],
            [("feature_flag", 1), ("status", 1)],
        ]


class ExperimentResult(Document):
    """Experiment results and analytics."""
    
    experiment_id: str = Field(description="Associated experiment ID")
    variant_name: str = Field(description="Variant name")
    
    # Metrics
    participants: int = Field(default=0, description="Total participants")
    conversions: int = Field(default=0, description="Total conversions")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")
    
    # Statistical analysis
    confidence_interval_lower: Optional[float] = Field(default=None)
    confidence_interval_upper: Optional[float] = Field(default=None)
    statistical_significance: Optional[float] = Field(default=None)
    p_value: Optional[float] = Field(default=None)
    
    # Custom metrics
    custom_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "experiment_results"
        indexes = [
            "experiment_id",
            [("experiment_id", 1), ("variant_name", 1)],
            [("experiment_id", 1), ("calculated_at", -1)],
        ]


class ExperimentEvent(Document):
    """Individual experiment events for tracking."""
    
    experiment_id: str = Field(description="Associated experiment ID")
    feature_flag: str = Field(description="Feature flag")
    user_id: str = Field(description="User identifier")
    variant_name: str = Field(description="Assigned variant")
    
    # Event details
    event_type: str = Field(description="Type of event")
    event_value: Optional[float] = Field(default=None, description="Event value")
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    user_attributes: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = Field(default=None)
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "experiment_events"
        indexes = [
            "experiment_id",
            "feature_flag", 
            "user_id",
            [("experiment_id", 1), ("timestamp", -1)],
            [("feature_flag", 1), ("user_id", 1)],
            [("user_id", 1), ("timestamp", -1)],
        ]