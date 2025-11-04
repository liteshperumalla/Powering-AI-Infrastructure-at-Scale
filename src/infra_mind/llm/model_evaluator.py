"""
Model Performance Evaluator - Track and compare LLM model performance.

Provides comprehensive model evaluation including:
- Real-time performance tracking
- Multi-model comparison
- Automated recommendations
- Cost-quality analysis
- Degradation detection
"""

import logging
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json

from .interface import LLMProvider

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""
    QUALITY = "quality"
    LATENCY = "latency"
    COST = "cost"
    RELIABILITY = "reliability"
    TOKENS = "tokens"


@dataclass
class ModelMetric:
    """Single metric data point for a model."""
    model_name: str
    provider: str
    timestamp: datetime

    # Quality metrics
    quality_score: Optional[float] = None
    validation_passed: bool = True

    # Performance metrics
    response_time: float = 0.0
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Cost metrics
    cost: float = 0.0

    # Reliability metrics
    success: bool = True
    error: Optional[str] = None
    timeout: bool = False

    # Context
    agent_name: Optional[str] = None
    request_id: str = ""
    from_cache: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['provider'] = self.provider if isinstance(self.provider, str) else self.provider.value
        return data


@dataclass
class ModelPerformanceReport:
    """Comprehensive performance report for a model."""
    model_name: str
    provider: str
    evaluation_period: str
    period_start: datetime
    period_end: datetime

    # Sample size
    total_requests: int
    successful_requests: int
    failed_requests: int

    # Quality metrics
    avg_quality_score: float
    median_quality_score: float
    quality_score_std: float
    min_quality_score: float
    max_quality_score: float

    # Performance metrics
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float

    # Cost metrics
    total_cost: float
    avg_cost_per_request: float
    total_tokens: int
    avg_tokens_per_request: float
    cost_per_quality_point: float

    # Reliability metrics
    success_rate: float
    error_rate: float
    timeout_rate: float
    cache_hit_rate: float

    # Comparison to baseline (if available)
    vs_baseline: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['period_start'] = self.period_start.isoformat()
        data['period_end'] = self.period_end.isoformat()
        return data


@dataclass
class ModelRecommendation:
    """Model selection recommendation."""
    recommendation_type: str  # switch_model, optimize_usage, etc.
    priority: str  # critical, high, medium, low
    title: str
    rationale: str
    current_model: str
    suggested_model: Optional[str]
    estimated_savings: Optional[str]
    impact: Dict[str, str]
    actions: List[str]


class MetricsStorage:
    """Abstract base for metrics storage."""

    async def record_metric(self, metric: ModelMetric) -> None:
        """Record a metric."""
        raise NotImplementedError

    async def get_metrics(
        self,
        model_name: str,
        provider: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[ModelMetric]:
        """Get metrics for time range."""
        raise NotImplementedError


class InMemoryMetricsStorage(MetricsStorage):
    """In-memory metrics storage for development."""

    def __init__(self):
        self.metrics: List[ModelMetric] = []

    async def record_metric(self, metric: ModelMetric) -> None:
        """Record metric in memory."""
        self.metrics.append(metric)

    async def get_metrics(
        self,
        model_name: str,
        provider: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[ModelMetric]:
        """Get metrics from memory."""
        return [
            m for m in self.metrics
            if m.model_name == model_name
            and m.provider == provider
            and start_time <= m.timestamp <= end_time
        ]


class ModelEvaluator:
    """
    Comprehensive model performance evaluation and monitoring.

    Features:
    - Real-time performance tracking
    - Multi-model comparison
    - Statistical analysis
    - Automated recommendations
    - Degradation detection
    - Cost-quality optimization
    """

    def __init__(
        self,
        storage_backend: Optional[MetricsStorage] = None,
        baseline_model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize model evaluator.

        Args:
            storage_backend: Metrics storage (defaults to in-memory)
            baseline_model: Model to use as baseline for comparisons
        """
        self.storage = storage_backend or InMemoryMetricsStorage()
        self.baseline_model = baseline_model

        logger.info(f"ModelEvaluator initialized with baseline: {baseline_model}")

    async def record_model_usage(
        self,
        model_name: str,
        provider: str,
        quality_score: Optional[float],
        response_time: float,
        cost: float,
        tokens_used: int,
        prompt_tokens: int,
        completion_tokens: int,
        success: bool,
        error: Optional[str] = None,
        timeout: bool = False,
        agent_name: Optional[str] = None,
        request_id: str = "",
        from_cache: bool = False,
        validation_passed: bool = True
    ) -> None:
        """
        Record model usage metrics.

        Args:
            model_name: Model that was used
            provider: LLM provider
            quality_score: Quality score (0.0-1.0) if available
            response_time: Response time in seconds
            cost: Cost in USD
            tokens_used: Total tokens used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            success: Whether request succeeded
            error: Error message if failed
            timeout: Whether request timed out
            agent_name: Agent that made request
            request_id: Request identifier
            from_cache: Whether response was cached
            validation_passed: Whether response passed validation
        """
        metric = ModelMetric(
            model_name=model_name,
            provider=provider,
            timestamp=datetime.now(timezone.utc),
            quality_score=quality_score,
            validation_passed=validation_passed,
            response_time=response_time,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            success=success,
            error=error,
            timeout=timeout,
            agent_name=agent_name,
            request_id=request_id,
            from_cache=from_cache
        )

        await self.storage.record_metric(metric)

        logger.debug(
            f"Recorded metric for {model_name}: "
            f"quality={quality_score:.3f if quality_score else 'N/A'}, "
            f"latency={response_time:.2f}s, cost=${cost:.4f}"
        )

    async def evaluate_model_performance(
        self,
        model_name: str,
        provider: str,
        time_period: timedelta = timedelta(days=7)
    ) -> ModelPerformanceReport:
        """
        Evaluate model performance over time period.

        Args:
            model_name: Model to evaluate
            provider: LLM provider
            time_period: Evaluation period

        Returns:
            Performance report

        Raises:
            ValueError: If no metrics found
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - time_period

        # Fetch metrics
        metrics = await self.storage.get_metrics(model_name, provider, start_time, end_time)

        if not metrics:
            raise ValueError(f"No metrics found for {model_name} ({provider})")

        # Extract data
        quality_scores = [m.quality_score for m in metrics if m.quality_score is not None and m.success]
        response_times = [m.response_time for m in metrics]
        costs = [m.cost for m in metrics]
        tokens = [m.tokens_used for m in metrics]

        successful = [m for m in metrics if m.success]
        failed = [m for m in metrics if not m.success]
        timeouts = [m for m in metrics if m.timeout]
        cached = [m for m in metrics if m.from_cache]

        # Calculate statistics
        report = ModelPerformanceReport(
            model_name=model_name,
            provider=provider,
            evaluation_period=f"{time_period.days} days",
            period_start=start_time,
            period_end=end_time,

            # Sample size
            total_requests=len(metrics),
            successful_requests=len(successful),
            failed_requests=len(failed),

            # Quality metrics
            avg_quality_score=statistics.mean(quality_scores) if quality_scores else 0.0,
            median_quality_score=statistics.median(quality_scores) if quality_scores else 0.0,
            quality_score_std=statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0.0,
            min_quality_score=min(quality_scores) if quality_scores else 0.0,
            max_quality_score=max(quality_scores) if quality_scores else 0.0,

            # Performance metrics
            avg_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=self._percentile(response_times, 95),
            p99_response_time=self._percentile(response_times, 99),

            # Cost metrics
            total_cost=sum(costs),
            avg_cost_per_request=statistics.mean(costs),
            total_tokens=sum(tokens),
            avg_tokens_per_request=statistics.mean(tokens),
            cost_per_quality_point=(
                sum(costs) / sum(quality_scores) if quality_scores and sum(quality_scores) > 0 else 0.0
            ),

            # Reliability metrics
            success_rate=len(successful) / len(metrics),
            error_rate=len(failed) / len(metrics),
            timeout_rate=len(timeouts) / len(metrics),
            cache_hit_rate=len(cached) / len(metrics)
        )

        # Compare to baseline if requested
        if model_name != self.baseline_model:
            try:
                baseline_report = await self.evaluate_model_performance(
                    self.baseline_model, provider, time_period
                )
                report.vs_baseline = self._compare_to_baseline(report, baseline_report)
            except ValueError:
                # Baseline not available
                pass

        return report

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * len(sorted_data)

        if index.is_integer():
            return sorted_data[int(index) - 1]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[min(int(index) + 1, len(sorted_data) - 1)]
            return (lower + upper) / 2

    def _compare_to_baseline(
        self,
        current: ModelPerformanceReport,
        baseline: ModelPerformanceReport
    ) -> Dict[str, float]:
        """
        Compare current model to baseline.

        Args:
            current: Current model report
            baseline: Baseline model report

        Returns:
            Dictionary of percentage differences
        """
        def pct_diff(current_val: float, baseline_val: float) -> float:
            if baseline_val == 0:
                return 0.0
            return ((current_val - baseline_val) / baseline_val) * 100

        return {
            "quality_diff": pct_diff(
                current.avg_quality_score,
                baseline.avg_quality_score
            ),
            "latency_diff": pct_diff(
                current.avg_response_time,
                baseline.avg_response_time
            ),
            "cost_diff": pct_diff(
                current.avg_cost_per_request,
                baseline.avg_cost_per_request
            ),
            "success_rate_diff": pct_diff(
                current.success_rate,
                baseline.success_rate
            ),
            "cost_per_quality_diff": pct_diff(
                current.cost_per_quality_point,
                baseline.cost_per_quality_point
            )
        }

    async def compare_models(
        self,
        models: List[Tuple[str, str]],  # List of (model_name, provider)
        time_period: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """
        Compare multiple models.

        Args:
            models: List of (model_name, provider) tuples
            time_period: Evaluation period

        Returns:
            Comparison report
        """
        reports = []

        for model_name, provider in models:
            try:
                report = await self.evaluate_model_performance(
                    model_name, provider, time_period
                )
                reports.append(report)
            except ValueError as e:
                logger.warning(f"Skipping {model_name}: {e}")

        if not reports:
            return {"error": "No models with sufficient data"}

        # Find best in each category
        best_quality = max(reports, key=lambda r: r.avg_quality_score)
        best_latency = min(reports, key=lambda r: r.avg_response_time)
        best_cost = min(reports, key=lambda r: r.avg_cost_per_request)
        best_value = min(reports, key=lambda r: r.cost_per_quality_point)
        best_reliability = max(reports, key=lambda r: r.success_rate)

        return {
            "evaluation_period": f"{time_period.days} days",
            "models_evaluated": len(reports),
            "best_quality": {
                "model": best_quality.model_name,
                "score": round(best_quality.avg_quality_score, 3)
            },
            "best_latency": {
                "model": best_latency.model_name,
                "avg_ms": round(best_latency.avg_response_time * 1000, 1)
            },
            "best_cost": {
                "model": best_cost.model_name,
                "avg_cost": round(best_cost.avg_cost_per_request, 4)
            },
            "best_value": {
                "model": best_value.model_name,
                "cost_per_quality": round(best_value.cost_per_quality_point, 4)
            },
            "best_reliability": {
                "model": best_reliability.model_name,
                "success_rate": round(best_reliability.success_rate * 100, 1)
            },
            "detailed_reports": [r.to_dict() for r in reports]
        }

    async def get_model_recommendations(
        self,
        time_period: timedelta = timedelta(days=7)
    ) -> List[ModelRecommendation]:
        """
        Get automated model selection recommendations.

        Args:
            time_period: Period to analyze

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get all models with data
        # Note: In production, you'd query storage for available models
        # For now, we'll analyze common models
        common_models = [
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"),
            ("gpt-4-turbo", "openai")
        ]

        reports = {}
        for model, provider in common_models:
            try:
                report = await self.evaluate_model_performance(model, provider, time_period)
                reports[(model, provider)] = report
            except ValueError:
                continue

        if not reports:
            return []

        # Recommendation 1: Switch to better value model
        if len(reports) >= 2:
            best_value = min(reports.items(), key=lambda x: x[1].cost_per_quality_point)
            current = reports.get((self.baseline_model, "openai"))

            if current and best_value[0] != (self.baseline_model, "openai"):
                value_improvement = (
                    (current.cost_per_quality_point - best_value[1].cost_per_quality_point) /
                    current.cost_per_quality_point * 100
                )

                if value_improvement > 15:  # 15%+ improvement
                    recommendations.append(ModelRecommendation(
                        recommendation_type="switch_model",
                        priority="high",
                        title=f"Switch to {best_value[0][0]} for better value",
                        rationale=(
                            f"{best_value[0][0]} provides {value_improvement:.1f}% better "
                            f"cost-per-quality compared to {self.baseline_model}"
                        ),
                        current_model=self.baseline_model,
                        suggested_model=best_value[0][0],
                        estimated_savings=f"${(current.total_cost - best_value[1].total_cost):.2f}/week",
                        impact={
                            "quality": f"{best_value[1].avg_quality_score / current.avg_quality_score * 100 - 100:+.1f}%",
                            "cost": f"{(best_value[1].avg_cost_per_request / current.avg_cost_per_request - 1) * 100:+.1f}%",
                            "latency": f"{(best_value[1].avg_response_time / current.avg_response_time - 1) * 100:+.1f}%"
                        },
                        actions=[
                            f"Test {best_value[0][0]} with A/B experiment",
                            "Monitor quality metrics for 1 week",
                            f"Migrate to {best_value[0][0]} if successful"
                        ]
                    ))

        # Recommendation 2: Address poor reliability
        for (model, provider), report in reports.items():
            if report.success_rate < 0.95:
                recommendations.append(ModelRecommendation(
                    recommendation_type="reliability_issue",
                    priority="critical",
                    title=f"{model} has low success rate",
                    rationale=(
                        f"Success rate of {report.success_rate*100:.1f}% is below "
                        f"acceptable threshold of 95%"
                    ),
                    current_model=model,
                    suggested_model=None,
                    estimated_savings=None,
                    impact={
                        "reliability": f"{report.success_rate*100:.1f}%",
                        "error_rate": f"{report.error_rate*100:.1f}%"
                    },
                    actions=[
                        "Investigate error patterns",
                        "Check API quotas and limits",
                        "Consider alternative model or provider"
                    ]
                ))

        # Recommendation 3: Optimize high-cost models
        for (model, provider), report in reports.items():
            if report.avg_cost_per_request > 0.02:  # > $0.02 per request
                # Find cheaper alternative
                cheaper_models = [
                    (m, r) for (m, p), r in reports.items()
                    if r.avg_quality_score >= report.avg_quality_score * 0.9  # 90% of quality
                    and r.avg_cost_per_request < report.avg_cost_per_request * 0.5  # < 50% of cost
                ]

                if cheaper_models:
                    best_alternative = min(cheaper_models, key=lambda x: x[1].avg_cost_per_request)

                    recommendations.append(ModelRecommendation(
                        recommendation_type="cost_optimization",
                        priority="medium",
                        title=f"Reduce costs by switching from {model}",
                        rationale=(
                            f"{best_alternative[0]} provides comparable quality "
                            f"({best_alternative[1].avg_quality_score:.2f} vs {report.avg_quality_score:.2f}) "
                            f"at significantly lower cost"
                        ),
                        current_model=model,
                        suggested_model=best_alternative[0],
                        estimated_savings=(
                            f"${(report.avg_cost_per_request - best_alternative[1].avg_cost_per_request) * report.total_requests:.2f}/week"
                        ),
                        impact={
                            "cost_savings": f"{(1 - best_alternative[1].avg_cost_per_request / report.avg_cost_per_request) * 100:.0f}%",
                            "quality_impact": f"{(best_alternative[1].avg_quality_score / report.avg_quality_score - 1) * 100:+.1f}%"
                        },
                        actions=[
                            f"A/B test {best_alternative[0]} for non-critical tasks",
                            "Route simple queries to cheaper model",
                            f"Reserve {model} for complex tasks only"
                        ]
                    ))

        return recommendations

    async def detect_performance_degradation(
        self,
        model_name: str,
        provider: str,
        threshold: float = 0.15  # 15% degradation
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if model performance has degraded recently.

        Args:
            model_name: Model to check
            provider: Provider
            threshold: Degradation threshold (0.0-1.0)

        Returns:
            Degradation report if detected, None otherwise
        """
        # Compare recent performance (last 24h) to historical (last 7 days)
        try:
            recent = await self.evaluate_model_performance(
                model_name, provider, timedelta(days=1)
            )
            historical = await self.evaluate_model_performance(
                model_name, provider, timedelta(days=7)
            )
        except ValueError:
            return None

        # Calculate degradation
        quality_degradation = (
            (historical.avg_quality_score - recent.avg_quality_score) /
            historical.avg_quality_score
        )

        latency_increase = (
            (recent.avg_response_time - historical.avg_response_time) /
            historical.avg_response_time
        )

        error_rate_increase = recent.error_rate - historical.error_rate

        # Check if any metric degraded significantly
        degraded = (
            quality_degradation > threshold or
            latency_increase > threshold or
            error_rate_increase > threshold
        )

        if degraded:
            return {
                "model": model_name,
                "provider": provider,
                "degradation_detected": True,
                "quality_degradation": f"{quality_degradation*100:.1f}%",
                "latency_increase": f"{latency_increase*100:.1f}%",
                "error_rate_increase": f"{error_rate_increase*100:.1f}%",
                "recent_quality": round(recent.avg_quality_score, 3),
                "historical_quality": round(historical.avg_quality_score, 3),
                "recommendation": "Investigate model issues or switch to backup model"
            }

        return None
