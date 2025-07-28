"""
Comprehensive tests for the quality assurance system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import statistics

from src.infra_mind.quality import (
    RecommendationValidator, FactChecker, FeedbackCollector,
    QualityScoreManager, ABTestingFramework, ContinuousImprovementSystem,
    UserFeedback, FeedbackType, QualityScore, Experiment, ExperimentVariant,
    ExperimentMetric, ExperimentType, ExperimentStatus, ValidationResult,
    ValidationStatus, ValidationSeverity, AlertSeverity, ImprovementActionType
)
from src.infra_mind.models.simple_recommendation import Recommendation, Assessment, User
from src.infra_mind.core.cache import CacheManager
from src.infra_mind.core.metrics_collector import MetricsCollector


class TestRecommendationValidator:
    """Test recommendation validation system."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        mock_cloud_service = Mock()
        mock_cache_manager = Mock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()
        
        validator = RecommendationValidator(mock_cloud_service, mock_cache_manager)
        return validator
    
    @pytest.fixture
    def sample_recommendation(self):
        """Create sample recommendation."""
        return Recommendation(
            recommendation_id="test_rec_1",
            service_name="EC2",
            provider="AWS",
            cost_estimate=100.0,
            configuration={"instance_type": "t3.medium"},
            features=["Auto Scaling", "Load Balancing"]
        )
    
    @pytest.fixture
    def sample_assessment(self):
        """Create sample assessment."""
        return Assessment(
            assessment_id="test_assessment_1",
            business_requirements={
                "budget_range": "1000-5000",
                "timeline": "3_months",
                "business_goals": ["cost_optimization", "scalability"]
            },
            technical_requirements={
                "compute": {"cpu": 4, "memory": 8},
                "storage": {"size": 100, "type": "SSD"}
            },
            compliance_requirements={
                "regulations": ["GDPR", "HIPAA"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_validate_recommendation(self, validator, sample_recommendation, sample_assessment):
        """Test comprehensive recommendation validation."""
        # Mock external API calls
        validator.cloud_service.get_service_pricing = AsyncMock(return_value={"monthly_cost": 95.0})
        validator.cloud_service.check_service_availability = AsyncMock(return_value=True)
        validator.cloud_service.get_alternative_services = AsyncMock(return_value=[
            {"cost": 90.0, "service": "t3.small"},
            {"cost": 110.0, "service": "t3.large"}
        ])
        
        results = await validator.validate_recommendation(sample_recommendation, sample_assessment)
        
        assert len(results) > 0
        assert all(isinstance(result, ValidationResult) for result in results)
        
        # Check that pricing validation was performed
        pricing_results = [r for r in results if r.check_name == "pricing_accuracy"]
        assert len(pricing_results) > 0
        assert pricing_results[0].status == ValidationStatus.VALIDATED
    
    @pytest.mark.asyncio
    async def test_pricing_accuracy_validation(self, validator, sample_recommendation, sample_assessment):
        """Test pricing accuracy validation."""
        # Mock pricing API to return different price
        validator.cloud_service.get_service_pricing = AsyncMock(return_value={"monthly_cost": 120.0})
        
        results = await validator._validate_pricing_accuracy(sample_recommendation)
        
        assert len(results) == 1
        result = results[0]
        assert result.check_name == "pricing_accuracy"
        assert result.status == ValidationStatus.NEEDS_REVIEW  # 20% difference should trigger review
        assert "recommended_cost" in result.details
        assert "current_cost" in result.details
    
    @pytest.mark.asyncio
    async def test_service_availability_validation(self, validator, sample_recommendation):
        """Test service availability validation."""
        # Mock availability check
        validator.cloud_service.check_service_availability = AsyncMock(return_value=True)
        
        results = await validator._validate_service_availability(sample_recommendation)
        
        assert len(results) > 0
        for result in results:
            assert result.check_name.startswith("service_availability_")
            assert result.status == ValidationStatus.VALIDATED
            assert result.details["available"] is True


class TestFactChecker:
    """Test fact-checking system."""
    
    @pytest.fixture
    def fact_checker(self):
        """Create fact checker instance."""
        mock_cloud_service = Mock()
        mock_cache_manager = Mock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()
        
        fact_checker = FactChecker(mock_cloud_service, mock_cache_manager)
        return fact_checker
    
    @pytest.fixture
    def sample_recommendation(self):
        """Create sample recommendation."""
        return Recommendation(
            recommendation_id="test_rec_1",
            service_name="EC2",
            provider="AWS",
            cost_estimate=100.0,
            configuration={"instance_type": "t3.medium"},
            features=["Auto Scaling", "Load Balancing"]
        )
    
    @pytest.mark.asyncio
    async def test_fact_check_recommendation(self, fact_checker, sample_recommendation):
        """Test fact-checking of recommendations."""
        # Mock verification
        fact_checker._verify_against_provider_docs = AsyncMock(return_value={
            'verified': True,
            'confidence': 0.9,
            'evidence': {'source_url': 'https://aws.com/docs/ec2'}
        })
        
        results = await fact_checker.fact_check_recommendation(sample_recommendation)
        
        assert len(results) > 0
        for result in results:
            assert result.verified is True
            assert result.confidence > 0.8
            assert "source_url" in result.evidence
    
    def test_extract_claims(self, fact_checker, sample_recommendation):
        """Test claim extraction from recommendations."""
        claims = fact_checker._extract_claims(sample_recommendation)
        
        assert len(claims) > 0
        assert any("costs $100.0/month" in claim for claim in claims)
        assert any("Auto Scaling" in claim for claim in claims)


class TestFeedbackCollector:
    """Test feedback collection system."""
    
    @pytest.fixture
    def feedback_collector(self):
        """Create feedback collector instance."""
        mock_cache_manager = Mock()
        collector = FeedbackCollector(mock_cache_manager)
        
        # Mock database
        collector.db = Mock()
        collector.db.feedback = Mock()
        collector.db.feedback.insert_one = AsyncMock()
        collector.db.feedback.find = Mock()
        collector.db.feedback.update_one = AsyncMock()
        
        return collector
    
    @pytest.fixture
    def sample_feedback(self):
        """Create sample feedback."""
        return UserFeedback(
            feedback_id="test_feedback_1",
            user_id="user_123",
            assessment_id="assessment_123",
            recommendation_id="rec_123",
            agent_name="CTO Agent",
            feedback_type=FeedbackType.RATING,
            rating=4,
            comment="Good recommendation, easy to implement",
            implementation_success=True,
            technical_accuracy=4,
            business_value_realized=4,
            would_recommend=True,
            tags=["helpful", "accurate"]
        )
    
    @pytest.mark.asyncio
    async def test_collect_feedback(self, feedback_collector, sample_feedback):
        """Test feedback collection."""
        success = await feedback_collector.collect_feedback(sample_feedback)
        
        assert success is True
        feedback_collector.db.feedback.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_feedback_summary(self, feedback_collector):
        """Test feedback summary generation."""
        # Mock database response
        mock_feedback = [
            {"rating": 4, "implementation_success": True, "tags": ["helpful"]},
            {"rating": 5, "implementation_success": True, "tags": ["accurate"]},
            {"rating": 3, "implementation_success": False, "tags": ["complex"]}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_feedback)
        feedback_collector.db.feedback.find.return_value = mock_cursor
        
        summary = await feedback_collector.get_feedback_summary("rec_123")
        
        assert summary["total_feedback"] == 3
        assert summary["average_rating"] == 4.0
        assert summary["implementation_success_rate"] == 2/3
        assert "rating_distribution" in summary


class TestQualityScoreManager:
    """Test quality score management."""
    
    @pytest.fixture
    def quality_manager(self):
        """Create quality score manager."""
        mock_cache_manager = Mock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()
        
        manager = QualityScoreManager(mock_cache_manager)
        
        # Mock database
        manager.db = Mock()
        manager.db.quality_scores = Mock()
        manager.db.agent_metrics = Mock()
        
        return manager
    
    @pytest.mark.asyncio
    async def test_get_quality_score(self, quality_manager):
        """Test quality score retrieval."""
        # Mock database response
        mock_score_data = {
            "recommendation_id": "rec_123",
            "agent_name": "CTO Agent",
            "overall_score": 0.85,
            "accuracy_score": 0.9,
            "usefulness_score": 0.8,
            "implementation_score": 0.85,
            "business_value_score": 0.9,
            "confidence_interval": (0.8, 0.9),
            "sample_size": 10,
            "last_updated": datetime.utcnow()
        }
        
        quality_manager.db.quality_scores.find_one = AsyncMock(return_value=mock_score_data)
        
        score = await quality_manager.get_quality_score("rec_123")
        
        assert score is not None
        assert score.overall_score == 0.85
        assert score.sample_size == 10
    
    @pytest.mark.asyncio
    async def test_get_system_quality_overview(self, quality_manager):
        """Test system quality overview."""
        # Mock database responses
        mock_quality_scores = [
            {"overall_score": 0.8, "accuracy_score": 0.85},
            {"overall_score": 0.9, "accuracy_score": 0.9},
            {"overall_score": 0.75, "accuracy_score": 0.8}
        ]
        
        mock_agent_metrics = [
            {"agent_name": "CTO Agent", "average_rating": 4.2, "improvement_trend": 0.1},
            {"agent_name": "MLOps Agent", "average_rating": 3.8, "improvement_trend": -0.05}
        ]
        
        quality_manager.db.quality_scores.find = Mock()
        quality_manager.db.quality_scores.find.return_value.to_list = AsyncMock(return_value=mock_quality_scores)
        quality_manager.db.agent_metrics.find = Mock()
        quality_manager.db.agent_metrics.find.return_value.to_list = AsyncMock(return_value=mock_agent_metrics)
        
        overview = await quality_manager.get_system_quality_overview()
        
        assert "system_metrics" in overview
        assert overview["system_metrics"]["total_recommendations"] == 3
        assert overview["system_metrics"]["average_quality_score"] == statistics.mean([0.8, 0.9, 0.75])
        assert "agent_performance" in overview


class TestABTestingFramework:
    """Test A/B testing framework."""
    
    @pytest.fixture
    def ab_testing(self):
        """Create A/B testing framework."""
        mock_cache_manager = Mock()
        mock_cache_manager.get = AsyncMock(return_value=None)
        mock_cache_manager.set = AsyncMock()
        
        framework = ABTestingFramework(mock_cache_manager)
        
        # Mock database
        framework.db = Mock()
        framework.db.experiments = Mock()
        framework.db.experiment_assignments = Mock()
        framework.db.experiment_events = Mock()
        
        return framework
    
    @pytest.fixture
    def sample_experiment(self):
        """Create sample experiment."""
        variants = [
            ExperimentVariant(
                variant_id="control",
                name="Control",
                description="Current recommendation strategy",
                configuration={"strategy_name": "default"},
                traffic_allocation=0.5,
                is_control=True
            ),
            ExperimentVariant(
                variant_id="treatment",
                name="Treatment",
                description="New recommendation strategy",
                configuration={"strategy_name": "enhanced"},
                traffic_allocation=0.5,
                is_control=False
            )
        ]
        
        metrics = [
            ExperimentMetric(
                metric_name="conversion_rate",
                metric_type="conversion",
                primary=True,
                description="User acceptance rate"
            )
        ]
        
        return Experiment(
            experiment_id="test_exp_1",
            name="Recommendation Strategy Test",
            description="Test new recommendation strategy",
            experiment_type=ExperimentType.RECOMMENDATION_STRATEGY,
            status=ExperimentStatus.ACTIVE,
            variants=variants,
            metrics=metrics,
            target_sample_size=1000
        )
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, ab_testing, sample_experiment):
        """Test experiment creation."""
        ab_testing.db.experiments.insert_one = AsyncMock()
        
        success = await ab_testing.create_experiment(sample_experiment)
        
        assert success is True
        ab_testing.db.experiments.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_user_to_experiment(self, ab_testing, sample_experiment):
        """Test user assignment to experiment."""
        # Mock database responses
        ab_testing.db.experiment_assignments.find_one = AsyncMock(return_value=None)
        ab_testing.db.experiment_assignments.insert_one = AsyncMock()
        ab_testing._get_experiment = AsyncMock(return_value={
            "experiment_id": "test_exp_1",
            "status": "active",
            "variants": [v.__dict__ for v in sample_experiment.variants]
        })
        ab_testing._is_user_eligible = AsyncMock(return_value=True)
        
        variant_id = await ab_testing.assign_user_to_experiment("test_exp_1", "user_123")
        
        assert variant_id in ["control", "treatment"]
        ab_testing.db.experiment_assignments.insert_one.assert_called_once()
    
    def test_assign_variant(self, ab_testing, sample_experiment):
        """Test variant assignment logic."""
        variants = [v.__dict__ for v in sample_experiment.variants]
        
        # Test consistent assignment
        variant1 = ab_testing._assign_variant("user_123", variants)
        variant2 = ab_testing._assign_variant("user_123", variants)
        
        assert variant1 == variant2  # Should be consistent
        assert variant1 in ["control", "treatment"]
    
    @pytest.mark.asyncio
    async def test_analyze_experiment(self, ab_testing):
        """Test experiment analysis."""
        # Mock database responses
        ab_testing._get_experiment = AsyncMock(return_value={
            "experiment_id": "test_exp_1",
            "name": "Test Experiment",
            "status": "active",
            "variants": [
                {"variant_id": "control", "is_control": True},
                {"variant_id": "treatment", "is_control": False}
            ],
            "metrics": [{"metric_name": "conversion_rate", "primary": True}],
            "target_sample_size": 1000
        })
        
        mock_assignments = [
            {"variant_id": "control", "user_id": f"user_{i}"} for i in range(50)
        ] + [
            {"variant_id": "treatment", "user_id": f"user_{i}"} for i in range(50, 100)
        ]
        
        mock_events = [
            {"variant_id": "control", "event_name": "conversion", "user_id": f"user_{i}"}
            for i in range(20)  # 20/50 = 40% conversion
        ] + [
            {"variant_id": "treatment", "event_name": "conversion", "user_id": f"user_{i}"}
            for i in range(50, 75)  # 25/50 = 50% conversion
        ]
        
        ab_testing.db.experiment_assignments.find = Mock()
        ab_testing.db.experiment_assignments.find.return_value.to_list = AsyncMock(return_value=mock_assignments)
        ab_testing.db.experiment_events.find = Mock()
        ab_testing.db.experiment_events.find.return_value.to_list = AsyncMock(return_value=mock_events)
        
        analysis = await ab_testing.analyze_experiment("test_exp_1")
        
        assert "variant_results" in analysis
        assert "control" in analysis["variant_results"]
        assert "treatment" in analysis["variant_results"]
        assert analysis["variant_results"]["control"].conversion_rate == 0.4
        assert analysis["variant_results"]["treatment"].conversion_rate == 0.5


class TestContinuousImprovementSystem:
    """Test continuous improvement system."""
    
    @pytest.fixture
    def improvement_system(self):
        """Create continuous improvement system."""
        mock_cache_manager = Mock()
        mock_metrics_collector = Mock()
        
        system = ContinuousImprovementSystem(mock_cache_manager, mock_metrics_collector)
        
        # Mock database
        system.db = Mock()
        system.db.quality_alerts = Mock()
        system.db.improvement_actions = Mock()
        system.db.quality_scores = Mock()
        system.db.agent_metrics = Mock()
        system.db.experiments = Mock()
        
        # Mock components
        system.validator = Mock()
        system.feedback_collector = Mock()
        system.quality_manager = Mock()
        system.ab_testing = Mock()
        
        return system
    
    @pytest.mark.asyncio
    async def test_monitor_recommendation_quality(self, improvement_system):
        """Test recommendation quality monitoring."""
        # Mock recent quality scores
        mock_scores = [
            {"overall_score": 0.6, "accuracy_score": 0.65},  # Below threshold
            {"overall_score": 0.8, "accuracy_score": 0.85},
            {"overall_score": 0.75, "accuracy_score": 0.8}
        ]
        
        improvement_system.db.quality_scores.find = Mock()
        improvement_system.db.quality_scores.find.return_value.to_list = AsyncMock(return_value=mock_scores)
        improvement_system._create_alert = AsyncMock()
        improvement_system.metrics_collector.record_metric = AsyncMock()
        
        await improvement_system._monitor_recommendation_quality()
        
        # Should create alert for low quality
        improvement_system._create_alert.assert_called()
        alert_call = improvement_system._create_alert.call_args
        assert alert_call[1]["alert_type"] == "quality_score"
        assert alert_call[1]["severity"] == AlertSeverity.MEDIUM
    
    @pytest.mark.asyncio
    async def test_analyze_feedback_trends(self, improvement_system):
        """Test feedback trend analysis."""
        # Mock recent feedback with low ratings
        mock_feedback = [
            {"rating": 2, "implementation_success": False},
            {"rating": 3, "implementation_success": True},
            {"rating": 2, "implementation_success": False}
        ]
        
        improvement_system.db.feedback.find = Mock()
        improvement_system.db.feedback.find.return_value.to_list = AsyncMock(return_value=mock_feedback)
        improvement_system._create_alert = AsyncMock()
        improvement_system.metrics_collector.record_metric = AsyncMock()
        
        await improvement_system._analyze_feedback_trends()
        
        # Should create alert for low satisfaction
        improvement_system._create_alert.assert_called()
        alert_calls = improvement_system._create_alert.call_args_list
        
        # Check for user satisfaction alert
        satisfaction_alerts = [call for call in alert_calls if call[1]["alert_type"] == "user_satisfaction"]
        assert len(satisfaction_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_create_alert(self, improvement_system):
        """Test alert creation."""
        improvement_system.db.quality_alerts.insert_one = AsyncMock()
        improvement_system._send_alert_notification = AsyncMock()
        
        await improvement_system._create_alert(
            alert_type="test_alert",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            affected_component="test_component",
            metrics={"test_metric": 1.0},
            threshold_breached={"test_metric": {"value": 1.0, "threshold": 0.5}},
            suggested_actions=["Test action"]
        )
        
        improvement_system.db.quality_alerts.insert_one.assert_called_once()
        improvement_system._send_alert_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_improvement_action(self, improvement_system):
        """Test improvement action creation."""
        improvement_system.db.improvement_actions.insert_one = AsyncMock()
        
        await improvement_system._create_improvement_action(
            action_type=ImprovementActionType.RETRAIN_AGENT,
            title="Test Action",
            description="Test action description",
            priority=3,
            affected_agents=["CTO Agent"],
            expected_impact="Improved performance",
            implementation_effort="medium"
        )
        
        improvement_system.db.improvement_actions.insert_one.assert_called_once()


class TestQualityIntegration:
    """Integration tests for quality assurance system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_quality_flow(self):
        """Test complete quality assurance flow."""
        # This would test the integration of all quality components
        # in a realistic scenario
        
        # Mock components
        mock_cache_manager = Mock()
        mock_metrics_collector = Mock()
        
        # Create system components
        feedback_collector = FeedbackCollector(mock_cache_manager)
        quality_manager = QualityScoreManager(mock_cache_manager)
        improvement_system = ContinuousImprovementSystem(mock_cache_manager, mock_metrics_collector)
        
        # Mock databases
        for component in [feedback_collector, quality_manager, improvement_system]:
            component.db = Mock()
            component.db.feedback = Mock()
            component.db.quality_scores = Mock()
            component.db.agent_metrics = Mock()
            component.db.quality_alerts = Mock()
            component.db.improvement_actions = Mock()
        
        # Simulate feedback submission
        feedback = UserFeedback(
            feedback_id="test_feedback",
            user_id="user_123",
            assessment_id="assessment_123",
            recommendation_id="rec_123",
            agent_name="CTO Agent",
            feedback_type=FeedbackType.RATING,
            rating=2,  # Poor rating
            comment="Recommendation was not accurate"
        )
        
        # Mock database operations
        feedback_collector.db.feedback.insert_one = AsyncMock()
        feedback_collector.db.feedback.update_one = AsyncMock()
        feedback_collector.db.quality_scores.replace_one = AsyncMock()
        feedback_collector.db.agent_metrics.replace_one = AsyncMock()
        feedback_collector.db.improvement_queue.insert_one = AsyncMock()
        
        # Submit feedback
        success = await feedback_collector.collect_feedback(feedback)
        assert success is True
        
        # Verify that poor feedback triggers improvement analysis
        feedback_collector.db.improvement_queue.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_quality_metrics_calculation(self):
        """Test quality metrics calculation accuracy."""
        # Test the mathematical accuracy of quality score calculations
        
        mock_feedback_data = [
            {"rating": 5, "technical_accuracy": 5, "business_value_realized": 4, "ease_of_implementation": 5},
            {"rating": 4, "technical_accuracy": 4, "business_value_realized": 4, "ease_of_implementation": 4},
            {"rating": 3, "technical_accuracy": 3, "business_value_realized": 3, "ease_of_implementation": 3}
        ]
        
        mock_cache_manager = Mock()
        feedback_collector = FeedbackCollector(mock_cache_manager)
        
        # Calculate expected scores
        expected_accuracy = statistics.mean([5, 4, 3]) / 5.0  # 0.8
        expected_usefulness = statistics.mean([5, 4, 3]) / 5.0  # 0.8
        expected_implementation = statistics.mean([5, 4, 3]) / 5.0  # 0.8
        expected_business_value = statistics.mean([4, 4, 3]) / 5.0  # 0.73
        
        # Calculate overall score with weights
        weights = {"accuracy": 0.3, "usefulness": 0.25, "implementation": 0.25, "business_value": 0.2}
        expected_overall = (
            expected_accuracy * weights["accuracy"] +
            expected_usefulness * weights["usefulness"] +
            expected_implementation * weights["implementation"] +
            expected_business_value * weights["business_value"]
        )
        
        quality_score = await feedback_collector._calculate_quality_score_from_feedback(
            "rec_123", mock_feedback_data
        )
        
        assert abs(quality_score.overall_score - expected_overall) < 0.01
        assert abs(quality_score.accuracy_score - expected_accuracy) < 0.01
        assert quality_score.sample_size == 3


if __name__ == "__main__":
    pytest.main([__file__])