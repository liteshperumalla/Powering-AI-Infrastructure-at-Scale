"""
A/B Testing Framework for infrastructure assessment platform.

This module provides comprehensive A/B testing capabilities including experiment
management, user segmentation, traffic splitting, and statistical analysis.
"""

import asyncio
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import random
from collections import defaultdict

from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Status of an A/B test experiment."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(str, Enum):
    """Type of experiment variant."""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class ExperimentVariant:
    """Configuration for an experiment variant."""
    name: str
    type: VariantType
    traffic_percentage: float
    configuration: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "traffic_percentage": self.traffic_percentage,
            "configuration": self.configuration,
            "description": self.description
        }


@dataclass
class ExperimentConfig:
    """Configuration for an A/B test experiment."""
    name: str
    description: str
    feature_flag: str
    variants: List[ExperimentVariant]
    target_metric: str
    secondary_metrics: List[str] = field(default_factory=list)
    segment_filters: Dict[str, Any] = field(default_factory=dict)
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95
    statistical_power: float = 0.8
    minimum_detectable_effect: float = 0.05
    max_duration_days: int = 30
    auto_stop_on_significance: bool = True
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate experiment configuration."""
        # Check traffic percentages sum to 100%
        total_traffic = sum(v.traffic_percentage for v in self.variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Variant traffic percentages must sum to 100%, got {total_traffic}%")
        
        # Check for control variant
        control_variants = [v for v in self.variants if v.type == VariantType.CONTROL]
        if len(control_variants) != 1:
            raise ValueError("Experiment must have exactly one control variant")
        
        # Check confidence level
        if not 0.5 <= self.confidence_level <= 0.99:
            raise ValueError("Confidence level must be between 0.5 and 0.99")
        
        # Check statistical power
        if not 0.5 <= self.statistical_power <= 0.99:
            raise ValueError("Statistical power must be between 0.5 and 0.99")


@dataclass
class ExperimentMetrics:
    """Metrics for an experiment."""
    experiment_id: str
    variant_name: str
    participants: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update(self, conversions: int = None, revenue: float = None, 
               custom_metrics: Dict[str, float] = None):
        """Update metrics."""
        if conversions is not None:
            self.conversions += conversions
        if revenue is not None:
            self.revenue += revenue
        if custom_metrics:
            for key, value in custom_metrics.items():
                self.custom_metrics[key] = self.custom_metrics.get(key, 0) + value
        
        # Recalculate conversion rate
        if self.participants > 0:
            self.conversion_rate = self.conversions / self.participants
        
        self.last_updated = datetime.now(timezone.utc)


class Experiment:
    """
    Represents an A/B test experiment.
    
    Manages experiment lifecycle, user assignment, and metric collection.
    """
    
    def __init__(self, config: ExperimentConfig):
        """Initialize experiment."""
        self.config = config
        self.id = self._generate_id()
        self.status = ExperimentStatus.DRAFT
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        
        # Metrics tracking
        self.variant_metrics: Dict[str, ExperimentMetrics] = {}
        for variant in config.variants:
            self.variant_metrics[variant.name] = ExperimentMetrics(
                experiment_id=self.id,
                variant_name=variant.name
            )
        
        # User assignments
        self.user_assignments: Dict[str, str] = {}
        
        logger.info(f"Created experiment: {self.config.name} ({self.id})")
    
    def _generate_id(self) -> str:
        """Generate unique experiment ID."""
        content = f"{self.config.name}_{self.config.feature_flag}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def start(self) -> None:
        """Start the experiment."""
        if self.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Cannot start experiment in status: {self.status}")
        
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        
        logger.info(f"Started experiment: {self.config.name}")
    
    def pause(self) -> None:
        """Pause the experiment."""
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Cannot pause experiment in status: {self.status}")
        
        self.status = ExperimentStatus.PAUSED
        logger.info(f"Paused experiment: {self.config.name}")
    
    def resume(self) -> None:
        """Resume the experiment."""
        if self.status != ExperimentStatus.PAUSED:
            raise ValueError(f"Cannot resume experiment in status: {self.status}")
        
        self.status = ExperimentStatus.RUNNING
        logger.info(f"Resumed experiment: {self.config.name}")
    
    def stop(self, reason: str = "Manual stop") -> None:
        """Stop the experiment."""
        if self.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
            raise ValueError(f"Cannot stop experiment in status: {self.status}")
        
        self.status = ExperimentStatus.COMPLETED
        self.ended_at = datetime.now(timezone.utc)
        
        logger.info(f"Stopped experiment: {self.config.name} - {reason}")
    
    def get_variant_for_user(self, user_id: str, user_attributes: Dict[str, Any] = None) -> str:
        """
        Get variant assignment for a user.
        
        Args:
            user_id: Unique user identifier
            user_attributes: User attributes for segmentation
            
        Returns:
            Variant name assigned to the user
        """
        if self.status != ExperimentStatus.RUNNING:
            # Return control variant if experiment not running
            control_variant = next(v for v in self.config.variants if v.type == VariantType.CONTROL)
            return control_variant.name
        
        # Check if user already assigned
        if user_id in self.user_assignments:
            return self.user_assignments[user_id]
        
        # Check segment filters
        if not self._user_matches_segments(user_attributes or {}):
            control_variant = next(v for v in self.config.variants if v.type == VariantType.CONTROL)
            return control_variant.name
        
        # Assign variant based on consistent hashing
        variant_name = self._assign_variant(user_id)
        
        # Track assignment
        self.user_assignments[user_id] = variant_name
        self.variant_metrics[variant_name].participants += 1
        
        logger.debug(f"Assigned user {user_id} to variant {variant_name}")
        return variant_name
    
    def _user_matches_segments(self, user_attributes: Dict[str, Any]) -> bool:
        """Check if user matches segment filters."""
        if not self.config.segment_filters:
            return True
        
        for key, expected_value in self.config.segment_filters.items():
            user_value = user_attributes.get(key)
            
            if isinstance(expected_value, list):
                if user_value not in expected_value:
                    return False
            elif user_value != expected_value:
                return False
        
        return True
    
    def _assign_variant(self, user_id: str) -> str:
        """Assign variant using consistent hashing."""
        # Create deterministic hash for user
        hash_input = f"{self.id}:{user_id}"
        user_hash = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (user_hash % 10000) / 100.0  # 0-99.99%
        
        # Find variant based on traffic allocation
        cumulative_percentage = 0.0
        for variant in self.config.variants:
            cumulative_percentage += variant.traffic_percentage
            if bucket < cumulative_percentage:
                return variant.name
        
        # Fallback to control
        control_variant = next(v for v in self.config.variants if v.type == VariantType.CONTROL)
        return control_variant.name
    
    def track_event(self, user_id: str, event_type: str, 
                   value: float = 1.0, custom_metrics: Dict[str, float] = None) -> None:
        """
        Track an event for experiment analysis.
        
        Args:
            user_id: User who performed the event
            event_type: Type of event (conversion, revenue, etc.)
            value: Event value
            custom_metrics: Additional custom metrics
        """
        variant_name = self.user_assignments.get(user_id)
        if not variant_name:
            return  # User not in experiment
        
        metrics = self.variant_metrics[variant_name]
        
        if event_type == "conversion":
            metrics.update(conversions=int(value))
        elif event_type == "revenue":
            metrics.update(revenue=value)
        
        if custom_metrics:
            metrics.update(custom_metrics=custom_metrics)
        
        logger.debug(f"Tracked {event_type} event for user {user_id} in variant {variant_name}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get experiment results and metrics."""
        return {
            "experiment_id": self.id,
            "name": self.config.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_days": self._get_duration_days(),
            "total_participants": sum(m.participants for m in self.variant_metrics.values()),
            "variants": {
                name: {
                    "participants": metrics.participants,
                    "conversions": metrics.conversions,
                    "conversion_rate": metrics.conversion_rate,
                    "revenue": metrics.revenue,
                    "custom_metrics": metrics.custom_metrics
                }
                for name, metrics in self.variant_metrics.items()
            }
        }
    
    def _get_duration_days(self) -> Optional[float]:
        """Get experiment duration in days."""
        if not self.started_at:
            return None
        
        end_time = self.ended_at or datetime.now(timezone.utc)
        duration = end_time - self.started_at
        return duration.total_seconds() / (24 * 3600)
    
    def should_auto_stop(self) -> Dict[str, Any]:
        """Check if experiment should auto-stop based on significance."""
        if not self.config.auto_stop_on_significance:
            return {"should_stop": False, "reason": "Auto-stop disabled"}
        
        # Check minimum sample size
        total_participants = sum(m.participants for m in self.variant_metrics.values())
        if total_participants < self.config.minimum_sample_size:
            return {"should_stop": False, "reason": "Minimum sample size not reached"}
        
        # Check duration
        duration_days = self._get_duration_days()
        if duration_days and duration_days >= self.config.max_duration_days:
            return {"should_stop": True, "reason": "Maximum duration reached"}
        
        # Statistical significance check would go here
        # For now, return False (simplified implementation)
        return {"should_stop": False, "reason": "No significant difference detected"}


class ABTestingFramework:
    """
    A/B Testing Framework for managing experiments.
    
    Provides centralized management of all A/B tests including experiment
    creation, user assignment, metric collection, and analysis.
    """
    
    def __init__(self):
        """Initialize A/B testing framework."""
        self.experiments: Dict[str, Experiment] = {}
        self.feature_flags: Dict[str, str] = {}  # feature_flag -> experiment_id
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("A/B Testing Framework initialized")
    
    def create_experiment(self, config: ExperimentConfig) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            config: Experiment configuration
            
        Returns:
            Created experiment
            
        Raises:
            ValueError: If feature flag already in use
        """
        # Check if feature flag already in use
        if config.feature_flag in self.feature_flags:
            existing_exp_id = self.feature_flags[config.feature_flag]
            existing_exp = self.experiments[existing_exp_id]
            if existing_exp.status in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
                raise ValueError(f"Feature flag '{config.feature_flag}' already in use")
        
        # Create experiment
        experiment = Experiment(config)
        
        # Register experiment
        self.experiments[experiment.id] = experiment
        self.feature_flags[config.feature_flag] = experiment.id
        
        logger.info(f"Created experiment: {config.name} ({experiment.id})")
        return experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self.experiments.get(experiment_id)
    
    def get_experiment_by_flag(self, feature_flag: str) -> Optional[Experiment]:
        """Get experiment by feature flag."""
        experiment_id = self.feature_flags.get(feature_flag)
        if experiment_id:
            return self.experiments.get(experiment_id)
        return None
    
    def list_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Experiment]:
        """
        List experiments, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of matching experiments
        """
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [exp for exp in experiments if exp.status == status]
        
        return sorted(experiments, key=lambda x: x.created_at, reverse=True)
    
    def get_variant_for_user(self, feature_flag: str, user_id: str, 
                           user_attributes: Dict[str, Any] = None) -> Optional[str]:
        """
        Get variant for user for a specific feature flag.
        
        Args:
            feature_flag: Feature flag name
            user_id: User ID
            user_attributes: User attributes for segmentation
            
        Returns:
            Variant name or None if no active experiment
        """
        experiment = self.get_experiment_by_flag(feature_flag)
        if not experiment:
            return None
        
        return experiment.get_variant_for_user(user_id, user_attributes)
    
    def track_event(self, feature_flag: str, user_id: str, event_type: str,
                   value: float = 1.0, custom_metrics: Dict[str, float] = None) -> bool:
        """
        Track event for experiment analysis.
        
        Args:
            feature_flag: Feature flag name
            user_id: User ID
            event_type: Event type
            value: Event value
            custom_metrics: Custom metrics
            
        Returns:
            True if event was tracked, False otherwise
        """
        experiment = self.get_experiment_by_flag(feature_flag)
        if not experiment:
            return False
        
        experiment.track_event(user_id, event_type, value, custom_metrics)
        return True
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False
        
        try:
            experiment.start()
            return True
        except ValueError as e:
            logger.error(f"Failed to start experiment {experiment_id}: {e}")
            return False
    
    def stop_experiment(self, experiment_id: str, reason: str = "Manual stop") -> bool:
        """Stop an experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False
        
        try:
            experiment.stop(reason)
            return True
        except ValueError as e:
            logger.error(f"Failed to stop experiment {experiment_id}: {e}")
            return False
    
    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment results."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None
        
        return experiment.get_results()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for all experiments."""
        active_experiments = self.list_experiments(ExperimentStatus.RUNNING)
        completed_experiments = self.list_experiments(ExperimentStatus.COMPLETED)
        
        total_participants = sum(
            sum(m.participants for m in exp.variant_metrics.values())
            for exp in active_experiments
        )
        
        return {
            "summary": {
                "total_experiments": len(self.experiments),
                "active_experiments": len(active_experiments),
                "completed_experiments": len(completed_experiments),
                "total_participants": total_participants
            },
            "active_experiments": [
                {
                    "id": exp.id,
                    "name": exp.config.name,
                    "feature_flag": exp.config.feature_flag,
                    "status": exp.status.value,
                    "participants": sum(m.participants for m in exp.variant_metrics.values()),
                    "started_at": exp.started_at.isoformat() if exp.started_at else None,
                    "duration_days": exp._get_duration_days()
                }
                for exp in active_experiments
            ],
            "recent_results": [
                exp.get_results()
                for exp in completed_experiments[:5]  # Last 5 completed
            ]
        }
    
    async def start_monitoring(self, check_interval: int = 3600) -> None:
        """
        Start automated experiment monitoring.
        
        Args:
            check_interval: Check interval in seconds (default 1 hour)
        """
        if self.monitoring_task and not self.monitoring_task.done():
            return
        
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(check_interval)
        )
        logger.info("Started A/B testing monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop experiment monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped A/B testing monitoring")
    
    async def _monitoring_loop(self, check_interval: int) -> None:
        """Monitoring loop for automatic experiment management."""
        while True:
            try:
                await asyncio.sleep(check_interval)
                
                # Check all running experiments
                running_experiments = self.list_experiments(ExperimentStatus.RUNNING)
                
                for experiment in running_experiments:
                    # Check if experiment should auto-stop
                    stop_check = experiment.should_auto_stop()
                    
                    if stop_check["should_stop"]:
                        experiment.stop(stop_check["reason"])
                        logger.info(f"Auto-stopped experiment {experiment.config.name}: {stop_check['reason']}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in A/B testing monitoring loop: {e}")


class ExperimentManager:
    """
    High-level manager for A/B testing operations.
    
    Provides convenient methods for common A/B testing workflows.
    """
    
    def __init__(self, framework: ABTestingFramework):
        """Initialize experiment manager."""
        self.framework = framework
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default experiment templates."""
        
        # UI/UX Experiment Template
        self.templates["ui_test"] = {
            "description": "Template for UI/UX A/B tests",
            "target_metric": "conversion_rate",
            "secondary_metrics": ["engagement_time", "bounce_rate"],
            "minimum_sample_size": 1000,
            "confidence_level": 0.95,
            "max_duration_days": 14,
            "auto_stop_on_significance": True
        }
        
        # Feature Rollout Template
        self.templates["feature_rollout"] = {
            "description": "Template for gradual feature rollouts",
            "target_metric": "user_satisfaction",
            "secondary_metrics": ["error_rate", "performance"],
            "minimum_sample_size": 500,
            "confidence_level": 0.90,
            "max_duration_days": 30,
            "auto_stop_on_significance": False
        }
        
        # Algorithm Test Template
        self.templates["algorithm_test"] = {
            "description": "Template for algorithm/model A/B tests",
            "target_metric": "accuracy",
            "secondary_metrics": ["response_time", "user_feedback"],
            "minimum_sample_size": 2000,
            "confidence_level": 0.95,
            "max_duration_days": 21,
            "auto_stop_on_significance": True
        }
    
    def create_ui_experiment(self, name: str, feature_flag: str, 
                           control_config: Dict[str, Any],
                           treatment_config: Dict[str, Any],
                           traffic_split: float = 50.0) -> Experiment:
        """
        Create a UI A/B test experiment.
        
        Args:
            name: Experiment name
            feature_flag: Feature flag identifier
            control_config: Control variant configuration
            treatment_config: Treatment variant configuration
            traffic_split: Percentage of traffic for treatment (default 50%)
            
        Returns:
            Created experiment
        """
        template = self.templates["ui_test"]
        
        variants = [
            ExperimentVariant(
                name="control",
                type=VariantType.CONTROL,
                traffic_percentage=100.0 - traffic_split,
                configuration=control_config,
                description="Original UI/UX"
            ),
            ExperimentVariant(
                name="treatment",
                type=VariantType.TREATMENT,
                traffic_percentage=traffic_split,
                configuration=treatment_config,
                description="New UI/UX variant"
            )
        ]
        
        config = ExperimentConfig(
            name=name,
            description=template["description"],
            feature_flag=feature_flag,
            variants=variants,
            **{k: v for k, v in template.items() if k != "description"}
        )
        
        return self.framework.create_experiment(config)
    
    def create_feature_rollout(self, name: str, feature_flag: str,
                             rollout_percentage: float = 10.0) -> Experiment:
        """
        Create a feature rollout experiment.
        
        Args:
            name: Experiment name
            feature_flag: Feature flag identifier
            rollout_percentage: Percentage of users to receive new feature
            
        Returns:
            Created experiment
        """
        template = self.templates["feature_rollout"]
        
        variants = [
            ExperimentVariant(
                name="control",
                type=VariantType.CONTROL,
                traffic_percentage=100.0 - rollout_percentage,
                configuration={"feature_enabled": False},
                description="Feature disabled"
            ),
            ExperimentVariant(
                name="rollout",
                type=VariantType.TREATMENT,
                traffic_percentage=rollout_percentage,
                configuration={"feature_enabled": True},
                description="Feature enabled"
            )
        ]
        
        config = ExperimentConfig(
            name=name,
            description=template["description"],
            feature_flag=feature_flag,
            variants=variants,
            **{k: v for k, v in template.items() if k != "description"}
        )
        
        return self.framework.create_experiment(config)
    
    def create_algorithm_test(self, name: str, feature_flag: str,
                            algorithm_configs: List[Dict[str, Any]]) -> Experiment:
        """
        Create an algorithm comparison experiment.
        
        Args:
            name: Experiment name
            feature_flag: Feature flag identifier
            algorithm_configs: List of algorithm configurations to test
            
        Returns:
            Created experiment
        """
        if len(algorithm_configs) < 2:
            raise ValueError("At least 2 algorithm configurations required")
        
        template = self.templates["algorithm_test"]
        
        # Split traffic evenly among all algorithms
        traffic_per_variant = 100.0 / len(algorithm_configs)
        
        variants = []
        for i, algo_config in enumerate(algorithm_configs):
            variant_type = VariantType.CONTROL if i == 0 else VariantType.TREATMENT
            variants.append(ExperimentVariant(
                name=f"algorithm_{i}",
                type=variant_type,
                traffic_percentage=traffic_per_variant,
                configuration=algo_config,
                description=f"Algorithm variant {i}"
            ))
        
        config = ExperimentConfig(
            name=name,
            description=template["description"],
            feature_flag=feature_flag,
            variants=variants,
            **{k: v for k, v in template.items() if k != "description"}
        )
        
        return self.framework.create_experiment(config)


# Global A/B testing framework instance
ab_testing_framework = ABTestingFramework()
experiment_manager = ExperimentManager(ab_testing_framework)