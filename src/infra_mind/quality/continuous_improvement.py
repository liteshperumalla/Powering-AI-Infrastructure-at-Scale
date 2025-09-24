"""
Continuous monitoring and quality improvement processes.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

from .validation import RecommendationValidator, ValidationResult, ValidationStatus
from .feedback import FeedbackCollector, QualityScoreManager, AgentPerformanceMetrics
from .ab_testing import ABTestingFramework, Experiment, ExperimentType, ExperimentStatus
from ..models.recommendation import Recommendation
from ..models.assessment import Assessment
from ..core.database import get_database
from ..core.cache import CacheManager
from ..core.metrics_collector import MetricsCollector


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImprovementActionType(Enum):
    RETRAIN_AGENT = "retrain_agent"
    UPDATE_PROMPT = "update_prompt"
    ADJUST_PARAMETERS = "adjust_parameters"
    CREATE_EXPERIMENT = "create_experiment"
    MANUAL_REVIEW = "manual_review"
    UPDATE_KNOWLEDGE_BASE = "update_knowledge_base"


@dataclass
class QualityAlert:
    """Alert for quality issues."""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    description: str
    affected_component: str
    metrics: Dict[str, Any]
    threshold_breached: Dict[str, Any]
    suggested_actions: List[str]
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class ImprovementAction:
    """Action to improve system quality."""
    action_id: str
    action_type: ImprovementActionType
    title: str
    description: str
    priority: int  # 1-5, 5 being highest
    affected_agents: List[str]
    expected_impact: str
    implementation_effort: str  # "low", "medium", "high"
    status: str = "pending"  # pending, in_progress, completed, cancelled
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityTrend:
    """Quality trend analysis."""
    metric_name: str
    time_period: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # "improving", "declining", "stable"
    confidence: float
    data_points: List[Tuple[datetime, float]]


class ContinuousImprovementSystem:
    """System for continuous monitoring and quality improvement."""
    
    def __init__(self, cache_manager: CacheManager, metrics_collector: MetricsCollector):
        self.cache_manager = cache_manager
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        self.db = None
        
        # Initialize components
        self.validator = None
        self.feedback_collector = None
        self.quality_manager = None
        self.ab_testing = None
        
        # Quality thresholds
        self.quality_thresholds = {
            "overall_quality_score": {"min": 0.7, "target": 0.85},
            "accuracy_score": {"min": 0.75, "target": 0.9},
            "user_satisfaction": {"min": 3.5, "target": 4.2},
            "implementation_success_rate": {"min": 0.8, "target": 0.9},
            "response_time": {"max": 300, "target": 120},  # seconds
            "error_rate": {"max": 0.05, "target": 0.01}
        }
        
        # Monitoring intervals
        self.monitoring_intervals = {
            "real_time": 60,      # 1 minute
            "short_term": 300,    # 5 minutes
            "medium_term": 3600,  # 1 hour
            "long_term": 86400    # 24 hours
        }
    
    async def initialize(self):
        """Initialize the continuous improvement system."""
        self.db = await get_database()
        
        # Initialize components
        from ..cloud.unified import UnifiedCloudClient
        cloud_service = UnifiedCloudClient()
        
        self.validator = RecommendationValidator(cloud_service, self.cache_manager)
        self.feedback_collector = FeedbackCollector(self.cache_manager)
        self.quality_manager = QualityScoreManager(self.cache_manager)
        self.ab_testing = ABTestingFramework(self.cache_manager)
        
        await self.feedback_collector.initialize()
        await self.quality_manager.initialize()
        await self.ab_testing.initialize()
        
        # Start monitoring tasks
        asyncio.create_task(self._start_continuous_monitoring())
        
        self.logger.info("Continuous improvement system initialized")
    
    async def _start_continuous_monitoring(self):
        """Start continuous monitoring tasks."""
        # Start different monitoring intervals
        asyncio.create_task(self._real_time_monitoring())
        asyncio.create_task(self._short_term_monitoring())
        asyncio.create_task(self._medium_term_monitoring())
        asyncio.create_task(self._long_term_monitoring())
    
    async def _real_time_monitoring(self):
        """Real-time monitoring (every minute)."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_intervals["real_time"])
                
                # Monitor system health
                await self._monitor_system_health()
                
                # Check for critical errors
                await self._check_critical_errors()
                
            except Exception as e:
                self.logger.error(f"Real-time monitoring error: {e}")
    
    async def _short_term_monitoring(self):
        """Short-term monitoring (every 5 minutes)."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_intervals["short_term"])
                
                # Monitor recommendation quality
                await self._monitor_recommendation_quality()
                
                # Check response times
                await self._monitor_response_times()
                
            except Exception as e:
                self.logger.error(f"Short-term monitoring error: {e}")
    
    async def _medium_term_monitoring(self):
        """Medium-term monitoring (every hour)."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_intervals["medium_term"])
                
                # Analyze user feedback trends
                await self._analyze_feedback_trends()
                
                # Monitor agent performance
                await self._monitor_agent_performance()
                
                # Check experiment progress
                await self._monitor_experiment_progress()
                
            except Exception as e:
                self.logger.error(f"Medium-term monitoring error: {e}")
    
    async def _long_term_monitoring(self):
        """Long-term monitoring (daily)."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_intervals["long_term"])
                
                # Generate quality reports
                await self._generate_quality_reports()
                
                # Analyze long-term trends
                await self._analyze_long_term_trends()
                
                # Suggest improvements
                await self._suggest_improvements()
                
                # Clean up old data
                await self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Long-term monitoring error: {e}")
    
    async def _monitor_system_health(self):
        """Monitor overall system health."""
        try:
            # Check database connectivity
            await self.db.command("ping")
            
            # Check cache connectivity
            await self.cache_manager.ping()
            
            # Monitor memory usage
            import psutil
            memory_usage = psutil.virtual_memory().percent
            
            if memory_usage > 90:
                await self._create_alert(
                    alert_type="system_health",
                    severity=AlertSeverity.HIGH,
                    title="High Memory Usage",
                    description=f"System memory usage is at {memory_usage}%",
                    affected_component="system",
                    metrics={"memory_usage": memory_usage},
                    threshold_breached={"memory_usage": {"value": memory_usage, "threshold": 90}},
                    suggested_actions=["Scale up system resources", "Investigate memory leaks"]
                )
            
            # Record health metrics
            await self.metrics_collector.record_metric(
                "system_health.memory_usage", memory_usage
            )
            
        except Exception as e:
            await self._create_alert(
                alert_type="system_health",
                severity=AlertSeverity.CRITICAL,
                title="System Health Check Failed",
                description=f"System health monitoring failed: {str(e)}",
                affected_component="system",
                metrics={},
                threshold_breached={},
                suggested_actions=["Check system logs", "Restart services if necessary"]
            )
    
    async def _check_critical_errors(self):
        """Check for critical errors in the system."""
        try:
            # Check error rates from metrics
            error_rate = await self.metrics_collector.get_metric_value(
                "system.error_rate", timedelta(minutes=5)
            )
            
            if error_rate and error_rate > self.quality_thresholds["error_rate"]["max"]:
                await self._create_alert(
                    alert_type="error_rate",
                    severity=AlertSeverity.HIGH,
                    title="High Error Rate Detected",
                    description=f"Error rate is {error_rate:.2%}, above threshold of {self.quality_thresholds['error_rate']['max']:.2%}",
                    affected_component="system",
                    metrics={"error_rate": error_rate},
                    threshold_breached={"error_rate": {"value": error_rate, "threshold": self.quality_thresholds["error_rate"]["max"]}},
                    suggested_actions=["Check system logs", "Investigate recent changes", "Scale resources if needed"]
                )
            
        except Exception as e:
            self.logger.error(f"Error checking critical errors: {e}")
    
    async def _monitor_recommendation_quality(self):
        """Monitor recommendation quality metrics."""
        try:
            # Get recent quality scores
            recent_scores = await self.db.quality_scores.find({
                "last_updated": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            }).to_list(length=None)
            
            if recent_scores:
                avg_quality = statistics.mean([score["overall_score"] for score in recent_scores])
                avg_accuracy = statistics.mean([score["accuracy_score"] for score in recent_scores])
                
                # Check quality thresholds
                if avg_quality < self.quality_thresholds["overall_quality_score"]["min"]:
                    await self._create_alert(
                        alert_type="quality_score",
                        severity=AlertSeverity.MEDIUM,
                        title="Low Recommendation Quality",
                        description=f"Average quality score is {avg_quality:.2f}, below threshold of {self.quality_thresholds['overall_quality_score']['min']}",
                        affected_component="recommendations",
                        metrics={"avg_quality": avg_quality, "sample_size": len(recent_scores)},
                        threshold_breached={"overall_quality_score": {"value": avg_quality, "threshold": self.quality_thresholds["overall_quality_score"]["min"]}},
                        suggested_actions=["Review recent recommendations", "Check agent configurations", "Analyze user feedback"]
                    )
                
                if avg_accuracy < self.quality_thresholds["accuracy_score"]["min"]:
                    await self._create_alert(
                        alert_type="accuracy_score",
                        severity=AlertSeverity.MEDIUM,
                        title="Low Recommendation Accuracy",
                        description=f"Average accuracy score is {avg_accuracy:.2f}, below threshold of {self.quality_thresholds['accuracy_score']['min']}",
                        affected_component="recommendations",
                        metrics={"avg_accuracy": avg_accuracy, "sample_size": len(recent_scores)},
                        threshold_breached={"accuracy_score": {"value": avg_accuracy, "threshold": self.quality_thresholds["accuracy_score"]["min"]}},
                        suggested_actions=["Update knowledge bases", "Retrain agents", "Validate data sources"]
                    )
                
                # Record metrics
                await self.metrics_collector.record_metric("quality.overall_score", avg_quality)
                await self.metrics_collector.record_metric("quality.accuracy_score", avg_accuracy)
            
        except Exception as e:
            self.logger.error(f"Error monitoring recommendation quality: {e}")
    
    async def _monitor_response_times(self):
        """Monitor system response times."""
        try:
            # Get recent response time metrics
            avg_response_time = await self.metrics_collector.get_metric_value(
                "system.response_time", timedelta(minutes=5)
            )
            
            if avg_response_time and avg_response_time > self.quality_thresholds["response_time"]["max"]:
                await self._create_alert(
                    alert_type="response_time",
                    severity=AlertSeverity.MEDIUM,
                    title="Slow Response Times",
                    description=f"Average response time is {avg_response_time:.1f}s, above threshold of {self.quality_thresholds['response_time']['max']}s",
                    affected_component="system",
                    metrics={"avg_response_time": avg_response_time},
                    threshold_breached={"response_time": {"value": avg_response_time, "threshold": self.quality_thresholds["response_time"]["max"]}},
                    suggested_actions=["Check system load", "Optimize database queries", "Scale resources"]
                )
            
        except Exception as e:
            self.logger.error(f"Error monitoring response times: {e}")
    
    async def _analyze_feedback_trends(self):
        """Analyze user feedback trends."""
        try:
            # Get recent feedback
            recent_feedback = await self.db.feedback.find({
                "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            }).to_list(length=None)
            
            if recent_feedback:
                # Calculate average rating
                ratings = [f["rating"] for f in recent_feedback if f.get("rating")]
                if ratings:
                    avg_rating = statistics.mean(ratings)
                    
                    if avg_rating < self.quality_thresholds["user_satisfaction"]["min"]:
                        await self._create_alert(
                            alert_type="user_satisfaction",
                            severity=AlertSeverity.MEDIUM,
                            title="Low User Satisfaction",
                            description=f"Average user rating is {avg_rating:.2f}, below threshold of {self.quality_thresholds['user_satisfaction']['min']}",
                            affected_component="user_experience",
                            metrics={"avg_rating": avg_rating, "sample_size": len(ratings)},
                            threshold_breached={"user_satisfaction": {"value": avg_rating, "threshold": self.quality_thresholds["user_satisfaction"]["min"]}},
                            suggested_actions=["Review recent feedback comments", "Analyze common complaints", "Improve user experience"]
                        )
                    
                    await self.metrics_collector.record_metric("feedback.average_rating", avg_rating)
                
                # Analyze implementation success rate
                implementation_results = [f["implementation_success"] for f in recent_feedback 
                                        if f.get("implementation_success") is not None]
                if implementation_results:
                    success_rate = sum(implementation_results) / len(implementation_results)
                    
                    if success_rate < self.quality_thresholds["implementation_success_rate"]["min"]:
                        await self._create_alert(
                            alert_type="implementation_success",
                            severity=AlertSeverity.HIGH,
                            title="Low Implementation Success Rate",
                            description=f"Implementation success rate is {success_rate:.2%}, below threshold of {self.quality_thresholds['implementation_success_rate']['min']:.2%}",
                            affected_component="recommendations",
                            metrics={"success_rate": success_rate, "sample_size": len(implementation_results)},
                            threshold_breached={"implementation_success_rate": {"value": success_rate, "threshold": self.quality_thresholds["implementation_success_rate"]["min"]}},
                            suggested_actions=["Review failed implementations", "Improve recommendation accuracy", "Provide better implementation guidance"]
                        )
                    
                    await self.metrics_collector.record_metric("feedback.implementation_success_rate", success_rate)
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback trends: {e}")
    
    async def _monitor_agent_performance(self):
        """Monitor individual agent performance."""
        try:
            # Get all agent metrics
            agent_metrics = await self.db.agent_metrics.find().to_list(length=None)
            
            for metrics in agent_metrics:
                agent_name = metrics["agent_name"]
                
                # Check if agent performance is declining
                if metrics["improvement_trend"] < -0.2:  # 20% decline
                    await self._create_alert(
                        alert_type="agent_performance",
                        severity=AlertSeverity.MEDIUM,
                        title=f"Declining Performance: {agent_name}",
                        description=f"Agent {agent_name} shows declining performance trend of {metrics['improvement_trend']:.1%}",
                        affected_component=f"agent_{agent_name}",
                        metrics={"improvement_trend": metrics["improvement_trend"], "average_rating": metrics["average_rating"]},
                        threshold_breached={"improvement_trend": {"value": metrics["improvement_trend"], "threshold": -0.2}},
                        suggested_actions=[f"Review {agent_name} configuration", f"Analyze {agent_name} feedback", f"Consider retraining {agent_name}"]
                    )
                
                # Check if agent has low satisfaction
                if metrics["user_satisfaction_score"] < 0.6:  # Below 60%
                    await self._create_alert(
                        alert_type="agent_satisfaction",
                        severity=AlertSeverity.HIGH,
                        title=f"Low User Satisfaction: {agent_name}",
                        description=f"Agent {agent_name} has low user satisfaction score of {metrics['user_satisfaction_score']:.2f}",
                        affected_component=f"agent_{agent_name}",
                        metrics={"user_satisfaction_score": metrics["user_satisfaction_score"]},
                        threshold_breached={"user_satisfaction_score": {"value": metrics["user_satisfaction_score"], "threshold": 0.6}},
                        suggested_actions=[f"Urgent review of {agent_name}", f"Analyze user complaints about {agent_name}", f"Consider disabling {agent_name} temporarily"]
                    )
            
        except Exception as e:
            self.logger.error(f"Error monitoring agent performance: {e}")
    
    async def _monitor_experiment_progress(self):
        """Monitor A/B test experiment progress."""
        try:
            # Get active experiments
            active_experiments = await self.db.experiments.find({
                "status": ExperimentStatus.ACTIVE.value
            }).to_list(length=None)
            
            for experiment in active_experiments:
                # Check if experiment has enough participants
                assignments = await self.db.experiment_assignments.count_documents({
                    "experiment_id": experiment["experiment_id"]
                })
                
                target_sample_size = experiment.get("target_sample_size", 1000)
                
                if assignments < target_sample_size * 0.1:  # Less than 10% of target
                    await self._create_alert(
                        alert_type="experiment_progress",
                        severity=AlertSeverity.LOW,
                        title=f"Slow Experiment Progress: {experiment['name']}",
                        description=f"Experiment has only {assignments} participants, target is {target_sample_size}",
                        affected_component="experiments",
                        metrics={"current_participants": assignments, "target_participants": target_sample_size},
                        threshold_breached={"participation_rate": {"value": assignments/target_sample_size, "threshold": 0.1}},
                        suggested_actions=["Increase traffic allocation", "Review experiment targeting", "Extend experiment duration"]
                    )
                
                # Check if experiment should be analyzed
                if assignments >= target_sample_size:
                    # Trigger experiment analysis
                    analysis = await self.ab_testing.analyze_experiment(experiment["experiment_id"])
                    
                    # Check for significant results
                    if "statistical_significance" in analysis:
                        significant_variants = [
                            variant_id for variant_id, sig in analysis["statistical_significance"].items()
                            if sig.get("significance") in ["significant", "highly_significant"]
                        ]
                        
                        if significant_variants:
                            await self._create_improvement_action(
                                action_type=ImprovementActionType.CREATE_EXPERIMENT,
                                title=f"Implement Winning Variant: {experiment['name']}",
                                description=f"Experiment shows significant results for variants: {', '.join(significant_variants)}",
                                priority=4,
                                affected_agents=[],
                                expected_impact="Improved recommendation quality based on A/B test results",
                                implementation_effort="medium"
                            )
            
        except Exception as e:
            self.logger.error(f"Error monitoring experiment progress: {e}")
    
    async def _generate_quality_reports(self):
        """Generate daily quality reports."""
        try:
            # Get system quality overview
            quality_overview = await self.quality_manager.get_system_quality_overview()
            
            # Generate report
            report = {
                "report_id": f"quality_report_{datetime.utcnow().strftime('%Y%m%d')}",
                "generated_at": datetime.utcnow(),
                "period": "24_hours",
                "quality_overview": quality_overview,
                "alerts_summary": await self._get_alerts_summary(),
                "improvement_actions": await self._get_improvement_actions_summary(),
                "trends": await self._get_quality_trends()
            }
            
            # Store report
            await self.db.quality_reports.insert_one(report)
            
            self.logger.info(f"Generated quality report: {report['report_id']}")
            
        except Exception as e:
            self.logger.error(f"Error generating quality reports: {e}")
    
    async def _analyze_long_term_trends(self):
        """Analyze long-term quality trends."""
        try:
            # Analyze trends over different time periods
            time_periods = [
                ("7_days", timedelta(days=7)),
                ("30_days", timedelta(days=30)),
                ("90_days", timedelta(days=90))
            ]
            
            trends = {}
            
            for period_name, period_delta in time_periods:
                period_start = datetime.utcnow() - period_delta
                
                # Get quality scores for the period
                quality_scores = await self.db.quality_scores.find({
                    "last_updated": {"$gte": period_start}
                }).to_list(length=None)
                
                if quality_scores:
                    # Calculate trend
                    scores_by_date = {}
                    for score in quality_scores:
                        date_key = score["last_updated"].date()
                        if date_key not in scores_by_date:
                            scores_by_date[date_key] = []
                        scores_by_date[date_key].append(score["overall_score"])
                    
                    # Calculate daily averages
                    daily_averages = [
                        (date, statistics.mean(scores))
                        for date, scores in sorted(scores_by_date.items())
                    ]
                    
                    if len(daily_averages) >= 2:
                        # Calculate trend
                        first_week = daily_averages[:len(daily_averages)//2]
                        second_week = daily_averages[len(daily_averages)//2:]
                        
                        first_avg = statistics.mean([score for _, score in first_week])
                        second_avg = statistics.mean([score for _, score in second_week])
                        
                        change_percentage = (second_avg - first_avg) / first_avg if first_avg > 0 else 0
                        
                        trend_direction = "improving" if change_percentage > 0.02 else \
                                        "declining" if change_percentage < -0.02 else "stable"
                        
                        trends[period_name] = QualityTrend(
                            metric_name="overall_quality_score",
                            time_period=period_name,
                            current_value=second_avg,
                            previous_value=first_avg,
                            change_percentage=change_percentage,
                            trend_direction=trend_direction,
                            confidence=0.8,  # Simplified confidence calculation
                            data_points=[(datetime.combine(date, datetime.min.time()), score) 
                                       for date, score in daily_averages]
                        )
            
            # Store trends
            for period, trend in trends.items():
                await self.db.quality_trends.replace_one(
                    {"metric_name": trend.metric_name, "time_period": period},
                    trend.__dict__,
                    upsert=True
                )
            
        except Exception as e:
            self.logger.error(f"Error analyzing long-term trends: {e}")
    
    async def _suggest_improvements(self):
        """Suggest improvements based on analysis."""
        try:
            # Get recent alerts
            recent_alerts = await self.db.quality_alerts.find({
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
                "resolved": False
            }).to_list(length=None)
            
            # Group alerts by type
            alert_types = {}
            for alert in recent_alerts:
                alert_type = alert["alert_type"]
                if alert_type not in alert_types:
                    alert_types[alert_type] = []
                alert_types[alert_type].append(alert)
            
            # Generate improvement actions based on alert patterns
            for alert_type, alerts in alert_types.items():
                if len(alerts) >= 3:  # Multiple alerts of same type
                    await self._create_improvement_action_from_alerts(alert_type, alerts)
            
            # Analyze agent performance for improvement opportunities
            await self._suggest_agent_improvements()
            
        except Exception as e:
            self.logger.error(f"Error suggesting improvements: {e}")
    
    async def _create_alert(self, alert_type: str, severity: AlertSeverity, title: str,
                          description: str, affected_component: str, metrics: Dict[str, Any],
                          threshold_breached: Dict[str, Any], suggested_actions: List[str]):
        """Create a quality alert."""
        try:
            alert = QualityAlert(
                alert_id=f"{alert_type}_{datetime.utcnow().timestamp()}",
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                affected_component=affected_component,
                metrics=metrics,
                threshold_breached=threshold_breached,
                suggested_actions=suggested_actions,
                created_at=datetime.utcnow()
            )
            
            await self.db.quality_alerts.insert_one(alert.__dict__)
            
            # Log alert
            self.logger.warning(f"Quality alert created: {title} ({severity.value})")
            
            # Send notifications for high/critical alerts
            if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                await self._send_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
    
    async def _create_improvement_action(self, action_type: ImprovementActionType, title: str,
                                       description: str, priority: int, affected_agents: List[str],
                                       expected_impact: str, implementation_effort: str):
        """Create an improvement action."""
        try:
            action = ImprovementAction(
                action_id=f"{action_type.value}_{datetime.utcnow().timestamp()}",
                action_type=action_type,
                title=title,
                description=description,
                priority=priority,
                affected_agents=affected_agents,
                expected_impact=expected_impact,
                implementation_effort=implementation_effort
            )
            
            await self.db.improvement_actions.insert_one(action.__dict__)
            
            self.logger.info(f"Improvement action created: {title} (Priority: {priority})")
            
        except Exception as e:
            self.logger.error(f"Error creating improvement action: {e}")
    
    async def _send_alert_notification(self, alert: QualityAlert):
        """Send notification for high-priority alerts."""
        # This would integrate with notification systems (email, Slack, etc.)
        self.logger.critical(f"HIGH PRIORITY ALERT: {alert.title} - {alert.description}")
    
    async def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        try:
            recent_alerts = await self.db.quality_alerts.find({
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}
            }).to_list(length=None)
            
            return {
                "total_alerts": len(recent_alerts),
                "by_severity": {
                    severity.value: len([a for a in recent_alerts if a["severity"] == severity.value])
                    for severity in AlertSeverity
                },
                "unresolved_alerts": len([a for a in recent_alerts if not a.get("resolved", False)])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alerts summary: {e}")
            return {}
    
    async def _get_improvement_actions_summary(self) -> Dict[str, Any]:
        """Get summary of improvement actions."""
        try:
            actions = await self.db.improvement_actions.find().to_list(length=None)
            
            return {
                "total_actions": len(actions),
                "by_status": {
                    status: len([a for a in actions if a["status"] == status])
                    for status in ["pending", "in_progress", "completed", "cancelled"]
                },
                "high_priority_pending": len([
                    a for a in actions 
                    if a["priority"] >= 4 and a["status"] == "pending"
                ])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting improvement actions summary: {e}")
            return {}
    
    async def _get_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends summary."""
        try:
            trends = await self.db.quality_trends.find().to_list(length=None)
            
            return {
                "total_trends": len(trends),
                "improving_metrics": len([t for t in trends if t["trend_direction"] == "improving"]),
                "declining_metrics": len([t for t in trends if t["trend_direction"] == "declining"]),
                "stable_metrics": len([t for t in trends if t["trend_direction"] == "stable"])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting quality trends: {e}")
            return {}
    
    async def _create_improvement_action_from_alerts(self, alert_type: str, alerts: List[Dict]):
        """Create improvement action based on alert patterns."""
        if alert_type == "quality_score":
            await self._create_improvement_action(
                action_type=ImprovementActionType.RETRAIN_AGENT,
                title="Improve Recommendation Quality",
                description=f"Multiple quality alerts detected ({len(alerts)} alerts). Consider retraining agents or updating knowledge bases.",
                priority=3,
                affected_agents=list(set([alert.get("affected_component").replace("agent_", "") 
                                        for alert in alerts if "agent_" in alert.get("affected_component")])),
                expected_impact="Improved recommendation quality and user satisfaction",
                implementation_effort="high"
            )
        elif alert_type == "response_time":
            await self._create_improvement_action(
                action_type=ImprovementActionType.ADJUST_PARAMETERS,
                title="Optimize System Performance",
                description=f"Multiple response time alerts detected ({len(alerts)} alerts). System optimization needed.",
                priority=4,
                affected_agents=[],
                expected_impact="Faster response times and better user experience",
                implementation_effort="medium"
            )
    
    async def _suggest_agent_improvements(self):
        """Suggest improvements for individual agents."""
        try:
            agent_metrics = await self.db.agent_metrics.find().to_list(length=None)
            
            for metrics in agent_metrics:
                agent_name = metrics["agent_name"]
                
                # Check for improvement opportunities
                if metrics["accuracy_score"] < 0.8:
                    await self._create_improvement_action(
                        action_type=ImprovementActionType.UPDATE_KNOWLEDGE_BASE,
                        title=f"Improve {agent_name} Accuracy",
                        description=f"Agent {agent_name} has accuracy score of {metrics['accuracy_score']:.2f}, below target of 0.8",
                        priority=3,
                        affected_agents=[agent_name],
                        expected_impact="Improved recommendation accuracy",
                        implementation_effort="medium"
                    )
                
                if len(metrics.get("improvement_areas", [])) > 0:
                    await self._create_improvement_action(
                        action_type=ImprovementActionType.UPDATE_PROMPT,
                        title=f"Address {agent_name} Improvement Areas",
                        description=f"Agent {agent_name} has improvement areas: {', '.join(metrics['improvement_areas'])}",
                        priority=2,
                        affected_agents=[agent_name],
                        expected_impact="Better performance in identified weak areas",
                        implementation_effort="low"
                    )
            
        except Exception as e:
            self.logger.error(f"Error suggesting agent improvements: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        try:
            # Clean up old alerts (keep for 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            await self.db.quality_alerts.delete_many({
                "created_at": {"$lt": cutoff_date},
                "resolved": True
            })
            
            # Clean up old experiment events (keep for 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            await self.db.experiment_events.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            # Clean up old quality reports (keep for 180 days)
            cutoff_date = datetime.utcnow() - timedelta(days=180)
            await self.db.quality_reports.delete_many({
                "generated_at": {"$lt": cutoff_date}
            })
            
            self.logger.info("Completed data cleanup")
            
        except Exception as e:
            self.logger.error(f"Error during data cleanup: {e}")