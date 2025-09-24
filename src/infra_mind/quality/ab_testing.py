"""
A/B testing framework for recommendation strategies.
"""

import asyncio
import logging
import random
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

from ..models.recommendation import Recommendation
from ..models.assessment import Assessment
from ..models.user import User
from ..core.database import get_database
from ..core.cache import CacheManager


class ExperimentStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentType(Enum):
    RECOMMENDATION_STRATEGY = "recommendation_strategy"
    AGENT_CONFIGURATION = "agent_configuration"
    PROMPT_VARIATION = "prompt_variation"
    RANKING_ALGORITHM = "ranking_algorithm"
    UI_VARIATION = "ui_variation"


class StatisticalSignificance(Enum):
    NOT_SIGNIFICANT = "not_significant"
    MARGINALLY_SIGNIFICANT = "marginally_significant"
    SIGNIFICANT = "significant"
    HIGHLY_SIGNIFICANT = "highly_significant"


@dataclass
class ExperimentVariant:
    """A variant in an A/B test experiment."""
    variant_id: str
    name: str
    description: str
    configuration: Dict[str, Any]
    traffic_allocation: float  # Percentage of traffic (0.0-1.0)
    is_control: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentMetric:
    """Metric to track in an experiment."""
    metric_name: str
    metric_type: str  # "conversion", "continuous", "count"
    primary: bool = False  # Is this the primary metric?
    description: str = ""
    target_improvement: Optional[float] = None  # Expected improvement %


@dataclass
class ExperimentResult:
    """Result of an A/B test experiment."""
    variant_id: str
    sample_size: int
    conversion_rate: Optional[float] = None
    average_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    statistical_significance: StatisticalSignificance = StatisticalSignificance.NOT_SIGNIFICANT
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    """A/B test experiment definition."""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    variants: List[ExperimentVariant]
    metrics: List[ExperimentMetric]
    target_sample_size: int
    confidence_level: float = 0.95
    minimum_detectable_effect: float = 0.05  # 5% minimum effect size
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentAssignment:
    """User assignment to experiment variant."""
    assignment_id: str
    experiment_id: str
    user_id: str
    variant_id: str
    assigned_at: datetime
    context: Dict[str, Any] = field(default_factory=dict)


class ABTestingFramework:
    """A/B testing framework for recommendation strategies."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        self.db = None
        
        # Strategy registry for different recommendation approaches
        self.strategy_registry: Dict[str, Callable] = {}
    
    async def initialize(self):
        """Initialize database connection."""
        self.db = await get_database()
    
    def register_strategy(self, strategy_name: str, strategy_function: Callable):
        """Register a recommendation strategy for testing."""
        self.strategy_registry[strategy_name] = strategy_function
        self.logger.info(f"Registered strategy: {strategy_name}")
    
    async def create_experiment(self, experiment: Experiment) -> bool:
        """
        Create a new A/B test experiment.
        
        Args:
            experiment: Experiment configuration
            
        Returns:
            Success status
        """
        try:
            if not self.db:
                await self.initialize()
            
            # Validate experiment configuration
            validation_result = self._validate_experiment(experiment)
            if not validation_result["valid"]:
                self.logger.error(f"Invalid experiment: {validation_result['errors']}")
                return False
            
            # Store experiment in database
            experiment_doc = {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "description": experiment.description,
                "experiment_type": experiment.experiment_type.value,
                "status": experiment.status.value,
                "variants": [variant.__dict__ for variant in experiment.variants],
                "metrics": [metric.__dict__ for metric in experiment.metrics],
                "target_sample_size": experiment.target_sample_size,
                "confidence_level": experiment.confidence_level,
                "minimum_detectable_effect": experiment.minimum_detectable_effect,
                "start_date": experiment.start_date,
                "end_date": experiment.end_date,
                "created_by": experiment.created_by,
                "created_at": experiment.created_at,
                "updated_at": experiment.updated_at,
                "metadata": experiment.metadata
            }
            
            await self.db.experiments.insert_one(experiment_doc)
            
            # Cache experiment for quick access
            cache_key = f"experiment_{experiment.experiment_id}"
            await self.cache_manager.set(cache_key, experiment_doc, ttl=3600)
            
            self.logger.info(f"Created experiment: {experiment.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create experiment: {e}")
            return False
    
    async def assign_user_to_experiment(self, experiment_id: str, user_id: str, 
                                      context: Dict[str, Any] = None) -> Optional[str]:
        """
        Assign a user to an experiment variant.
        
        Args:
            experiment_id: ID of the experiment
            user_id: ID of the user
            context: Additional context for assignment
            
        Returns:
            Variant ID if assigned, None if not eligible
        """
        try:
            if not self.db:
                await self.initialize()
            
            # Check if user is already assigned
            existing_assignment = await self.db.experiment_assignments.find_one({
                "experiment_id": experiment_id,
                "user_id": user_id
            })
            
            if existing_assignment:
                return existing_assignment["variant_id"]
            
            # Get experiment configuration
            experiment = await self._get_experiment(experiment_id)
            if not experiment or experiment["status"] != ExperimentStatus.ACTIVE.value:
                return None
            
            # Check eligibility
            if not await self._is_user_eligible(user_id, experiment, context):
                return None
            
            # Assign to variant based on traffic allocation
            variant_id = self._assign_variant(user_id, experiment["variants"])
            
            if variant_id:
                # Store assignment
                assignment = ExperimentAssignment(
                    assignment_id=f"{experiment_id}_{user_id}",
                    experiment_id=experiment_id,
                    user_id=user_id,
                    variant_id=variant_id,
                    assigned_at=datetime.utcnow(),
                    context=context or {}
                )
                
                await self.db.experiment_assignments.insert_one(assignment.__dict__)
                
                self.logger.info(f"Assigned user {user_id} to variant {variant_id} in experiment {experiment_id}")
                return variant_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to assign user to experiment: {e}")
            return None
    
    async def get_recommendation_strategy(self, user_id: str, assessment: Assessment) -> str:
        """
        Get the recommendation strategy for a user based on active experiments.
        
        Args:
            user_id: ID of the user
            assessment: User assessment
            
        Returns:
            Strategy name to use
        """
        try:
            # Get active recommendation strategy experiments
            active_experiments = await self.db.experiments.find({
                "status": ExperimentStatus.ACTIVE.value,
                "experiment_type": ExperimentType.RECOMMENDATION_STRATEGY.value
            }).to_list(length=None)
            
            for experiment in active_experiments:
                # Check if user is assigned to this experiment
                assignment = await self.db.experiment_assignments.find_one({
                    "experiment_id": experiment["experiment_id"],
                    "user_id": user_id
                })
                
                if assignment:
                    # Get variant configuration
                    variant = next(
                        (v for v in experiment["variants"] if v["variant_id"] == assignment["variant_id"]),
                        None
                    )
                    
                    if variant:
                        strategy_name = variant["configuration"]smart_get("strategy_name")
                        self.logger.info(f"Using strategy {strategy_name} for user {user_id}")
                        return strategy_name
                else:
                    # Try to assign user to experiment
                    variant_id = await self.assign_user_to_experiment(
                        experiment["experiment_id"], 
                        user_id,
                        {"assessment_id": assessment.assessment_id}
                    )
                    
                    if variant_id:
                        variant = next(
                            (v for v in experiment["variants"] if v["variant_id"] == variant_id),
                            None
                        )
                        
                        if variant:
                            strategy_name = variant["configuration"]smart_get("strategy_name")
                            return strategy_name
            
            # Default strategy if no experiments apply
            return "default"
            
        except Exception as e:
            self.logger.error(f"Failed to get recommendation strategy: {e}")
            return "default"
    
    async def record_experiment_event(self, user_id: str, event_name: str, 
                                    event_data: Dict[str, Any]):
        """
        Record an event for experiment tracking.
        
        Args:
            user_id: ID of the user
            event_name: Name of the event
            event_data: Event data
        """
        try:
            if not self.db:
                await self.initialize()
            
            # Get user's active experiment assignments
            assignments = await self.db.experiment_assignments.find({
                "user_id": user_id
            }).to_list(length=None)
            
            for assignment in assignments:
                # Record event for each active experiment
                event_record = {
                    "event_id": f"{assignment['experiment_id']}_{user_id}_{event_name}_{datetime.utcnow().timestamp()}",
                    "experiment_id": assignment["experiment_id"],
                    "variant_id": assignment["variant_id"],
                    "user_id": user_id,
                    "event_name": event_name,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow()
                }
                
                await self.db.experiment_events.insert_one(event_record)
            
        except Exception as e:
            self.logger.error(f"Failed to record experiment event: {e}")
    
    async def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Analyze experiment results and calculate statistical significance.
        
        Args:
            experiment_id: ID of the experiment to analyze
            
        Returns:
            Analysis results
        """
        try:
            if not self.db:
                await self.initialize()
            
            # Get experiment configuration
            experiment = await self._get_experiment(experiment_id)
            if not experiment:
                return {"error": "Experiment not found"}
            
            # Get all assignments and events for this experiment
            assignments = await self.db.experiment_assignments.find({
                "experiment_id": experiment_id
            }).to_list(length=None)
            
            events = await self.db.experiment_events.find({
                "experiment_id": experiment_id
            }).to_list(length=None)
            
            # Analyze each variant
            variant_results = {}
            for variant in experiment["variants"]:
                variant_id = variant["variant_id"]
                
                # Get assignments for this variant
                variant_assignments = [a for a in assignments if a["variant_id"] == variant_id]
                
                # Get events for this variant
                variant_events = [e for e in events if e["variant_id"] == variant_id]
                
                # Calculate metrics
                result = await self._calculate_variant_metrics(
                    variant_id, variant_assignments, variant_events, experiment["metrics"]
                )
                
                variant_results[variant_id] = result
            
            # Calculate statistical significance
            significance_results = await self._calculate_statistical_significance(
                variant_results, experiment
            )
            
            # Generate recommendations
            recommendations = self._generate_experiment_recommendations(
                variant_results, significance_results, experiment
            )
            
            analysis = {
                "experiment_id": experiment_id,
                "experiment_name": experiment["name"],
                "status": experiment["status"],
                "start_date": experiment.get("start_date"),
                "analysis_date": datetime.utcnow(),
                "total_participants": len(assignments),
                "variant_results": variant_results,
                "statistical_significance": significance_results,
                "recommendations": recommendations,
                "summary": self._generate_experiment_summary(variant_results, significance_results)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze experiment: {e}")
            return {"error": str(e)}
    
    def _validate_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """Validate experiment configuration."""
        errors = []
        
        # Check traffic allocation sums to 1.0
        total_allocation = sum(variant.traffic_allocation for variant in experiment.variants)
        if abs(total_allocation - 1.0) > 0.01:
            errors.append(f"Traffic allocation sums to {total_allocation}, should be 1.0")
        
        # Check for control variant
        control_variants = [v for v in experiment.variants if v.is_control]
        if len(control_variants) != 1:
            errors.append("Experiment must have exactly one control variant")
        
        # Check variant IDs are unique
        variant_ids = [v.variant_id for v in experiment.variants]
        if len(variant_ids) != len(set(variant_ids)):
            errors.append("Variant IDs must be unique")
        
        # Check metrics
        primary_metrics = [m for m in experiment.metrics if m.primary]
        if len(primary_metrics) != 1:
            errors.append("Experiment must have exactly one primary metric")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment from cache or database."""
        # Check cache first
        cache_key = f"experiment_{experiment_id}"
        cached_experiment = await self.cache_manager.get(cache_key)
        if cached_experiment:
            return cached_experiment
        
        # Get from database
        experiment = await self.db.experiments.find_one({"experiment_id": experiment_id})
        if experiment:
            await self.cache_manager.set(cache_key, experiment, ttl=3600)
        
        return experiment
    
    async def _is_user_eligible(self, user_id: str, experiment: Dict, 
                              context: Dict[str, Any]) -> bool:
        """Check if user is eligible for experiment."""
        # Basic eligibility checks
        # This could be extended with more sophisticated targeting
        
        # Check if user is already in too many experiments
        active_assignments = await self.db.experiment_assignments.count_documents({
            "user_id": user_id
        })
        
        if active_assignments >= 3:  # Limit to 3 concurrent experiments
            return False
        
        # Add more eligibility criteria based on experiment metadata
        eligibility_criteria = experiment.get("metadata", {}).get("eligibility", {})
        
        # Example: Check user segment
        if "user_segment" in eligibility_criteria:
            # This would check user properties against criteria
            pass
        
        return True
    
    def _assign_variant(self, user_id: str, variants: List[Dict]) -> Optional[str]:
        """Assign user to variant based on traffic allocation."""
        # Use consistent hashing for stable assignments
        hash_input = f"{user_id}_variant_assignment"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0  # 0.0 to 1.0
        
        cumulative_allocation = 0.0
        for variant in variants:
            cumulative_allocation += variant["traffic_allocation"]
            if random_value <= cumulative_allocation:
                return variant["variant_id"]
        
        # Fallback to control variant
        control_variant = next((v for v in variants if v.get("is_control")), None)
        return control_variant["variant_id"] if control_variant else None
    
    async def _calculate_variant_metrics(self, variant_id: str, assignments: List[Dict], 
                                       events: List[Dict], metrics: List[Dict]) -> ExperimentResult:
        """Calculate metrics for a variant."""
        sample_size = len(assignments)
        
        if sample_size == 0:
            return ExperimentResult(
                variant_id=variant_id,
                sample_size=0
            )
        
        # Calculate conversion rate (example metric)
        conversion_events = [e for e in events if e["event_name"] == "conversion"]
        conversion_rate = len(conversion_events) / sample_size if sample_size > 0 else 0.0
        
        # Calculate average value (example metric)
        value_events = [e for e in events if e["event_name"] == "value" and "value" in e["event_data"]]
        values = [e["event_data"]["value"] for e in value_events]
        average_value = statistics.mean(values) if values else 0.0
        
        # Calculate confidence interval for conversion rate
        confidence_interval = self._calculate_confidence_interval(conversion_rate, sample_size)
        
        return ExperimentResult(
            variant_id=variant_id,
            sample_size=sample_size,
            conversion_rate=conversion_rate,
            average_value=average_value,
            confidence_interval=confidence_interval,
            metrics={
                "total_events": len(events),
                "conversion_events": len(conversion_events),
                "value_events": len(value_events)
            }
        )
    
    def _calculate_confidence_interval(self, rate: float, sample_size: int, 
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for conversion rate."""
        if sample_size == 0:
            return (0.0, 0.0)
        
        # Using normal approximation for binomial proportion
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        standard_error = (rate * (1 - rate) / sample_size) ** 0.5
        margin_of_error = z_score * standard_error
        
        lower_bound = max(0.0, rate - margin_of_error)
        upper_bound = min(1.0, rate + margin_of_error)
        
        return (lower_bound, upper_bound)
    
    async def _calculate_statistical_significance(self, variant_results: Dict[str, ExperimentResult], 
                                                experiment: Dict) -> Dict[str, Any]:
        """Calculate statistical significance between variants."""
        # Find control variant
        control_variant_id = None
        for variant in experiment["variants"]:
            if variant.get("is_control"):
                control_variant_id = variant["variant_id"]
                break
        
        if not control_variant_id or control_variant_id not in variant_results:
            return {"error": "Control variant not found"}
        
        control_result = variant_results[control_variant_id]
        significance_results = {}
        
        for variant_id, result in variant_results.items():
            if variant_id == control_variant_id:
                continue
            
            # Calculate statistical significance (simplified z-test)
            significance = self._calculate_z_test(control_result, result)
            significance_results[variant_id] = significance
        
        return significance_results
    
    def _calculate_z_test(self, control: ExperimentResult, 
                         treatment: ExperimentResult) -> Dict[str, Any]:
        """Calculate z-test for statistical significance."""
        if control.sample_size == 0 or treatment.sample_size == 0:
            return {
                "p_value": 1.0,
                "significance": StatisticalSignificance.NOT_SIGNIFICANT.value,
                "effect_size": 0.0
            }
        
        # Calculate pooled standard error
        p1 = control.conversion_rate or 0.0
        p2 = treatment.conversion_rate or 0.0
        n1 = control.sample_size
        n2 = treatment.sample_size
        
        pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)
        pooled_se = (pooled_p * (1 - pooled_p) * (1/n1 + 1/n2)) ** 0.5
        
        if pooled_se == 0:
            return {
                "p_value": 1.0,
                "significance": StatisticalSignificance.NOT_SIGNIFICANT.value,
                "effect_size": 0.0
            }
        
        # Calculate z-score
        z_score = (p2 - p1) / pooled_se
        
        # Calculate p-value (two-tailed test)
        # Simplified calculation - in practice, use scipy.stats
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
        
        # Determine significance level
        if p_value < 0.001:
            significance = StatisticalSignificance.HIGHLY_SIGNIFICANT
        elif p_value < 0.01:
            significance = StatisticalSignificance.SIGNIFICANT
        elif p_value < 0.05:
            significance = StatisticalSignificance.MARGINALLY_SIGNIFICANT
        else:
            significance = StatisticalSignificance.NOT_SIGNIFICANT
        
        # Calculate effect size (relative improvement)
        effect_size = (p2 - p1) / p1 if p1 > 0 else 0.0
        
        return {
            "p_value": p_value,
            "z_score": z_score,
            "significance": significance.value,
            "effect_size": effect_size
        }
    
    def _normal_cdf(self, x: float) -> float:
        """Simplified normal CDF approximation."""
        # Abramowitz and Stegun approximation
        if x < 0:
            return 1 - self._normal_cdf(-x)
        
        k = 1 / (1 + 0.2316419 * x)
        return 1 - (1 / (2.506628274631 ** 0.5)) * (2.718281828 ** (-x * x / 2)) * \
               (0.319381530 * k - 0.356563782 * k**2 + 1.781477937 * k**3 - 
                1.821255978 * k**4 + 1.330274429 * k**5)
    
    def _generate_experiment_recommendations(self, variant_results: Dict[str, ExperimentResult], 
                                           significance_results: Dict[str, Any], 
                                           experiment: Dict) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []
        
        # Find best performing variant
        best_variant = max(
            variant_results.items(), 
            key=lambda x: x[1].conversion_rate or 0.0
        )
        
        # Check if best variant is statistically significant
        if best_variant[0] in significance_results:
            significance = significance_results[best_variant[0]]
            
            if significance["significance"] in [
                StatisticalSignificance.SIGNIFICANT.value,
                StatisticalSignificance.HIGHLY_SIGNIFICANT.value
            ]:
                recommendations.append(
                    f"Implement variant {best_variant[0]} - shows {significance['effect_size']:.1%} improvement"
                )
            else:
                recommendations.append(
                    "No statistically significant winner found - consider running experiment longer"
                )
        
        # Check sample sizes
        min_sample_size = min(result.sample_size for result in variant_results.values())
        target_sample_size = experiment.get("target_sample_size", 1000)
        
        if min_sample_size < target_sample_size:
            recommendations.append(
                f"Increase sample size - current minimum is {min_sample_size}, target is {target_sample_size}"
            )
        
        return recommendations
    
    def _generate_experiment_summary(self, variant_results: Dict[str, ExperimentResult], 
                                   significance_results: Dict[str, Any]) -> str:
        """Generate experiment summary."""
        total_participants = sum(result.sample_size for result in variant_results.values())
        
        # Find best performing variant
        best_variant = max(
            variant_results.items(), 
            key=lambda x: x[1].conversion_rate or 0.0
        )
        
        summary = f"Experiment completed with {total_participants} total participants. "
        summary += f"Best performing variant: {best_variant[0]} with {best_variant[1].conversion_rate:.1%} conversion rate."
        
        # Check for statistical significance
        significant_variants = [
            variant_id for variant_id, sig in significance_results.items()
            if sig["significance"] in [
                StatisticalSignificance.SIGNIFICANT.value,
                StatisticalSignificance.HIGHLY_SIGNIFICANT.value
            ]
        ]
        
        if significant_variants:
            summary += f" Statistically significant improvements found in variants: {', '.join(significant_variants)}."
        else:
            summary += " No statistically significant differences found."
        
        return summary