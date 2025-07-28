#!/usr/bin/env python3
"""
Demo script for the comprehensive quality assurance system.

This script demonstrates:
1. Advanced recommendation validation and fact-checking
2. User feedback collection and quality scoring
3. A/B testing framework for recommendation strategies
4. Continuous monitoring and quality improvement processes
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock

from src.infra_mind.quality import (
    RecommendationValidator, FactChecker, FeedbackCollector,
    QualityScoreManager, ABTestingFramework, ContinuousImprovementSystem,
    UserFeedback, FeedbackType, QualityScore, Experiment, ExperimentVariant,
    ExperimentMetric, ExperimentType, ExperimentStatus, ValidationResult,
    ValidationStatus, ValidationSeverity, AlertSeverity, ImprovementActionType
)
from src.infra_mind.models.simple_recommendation import Recommendation, Assessment
from src.infra_mind.core.cache import CacheManager
from src.infra_mind.core.metrics_collector import MetricsCollector
from src.infra_mind.cloud.unified import UnifiedCloudClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityAssuranceDemo:
    """Demo class for quality assurance system."""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.metrics_collector = MetricsCollector()
        self.cloud_service = UnifiedCloudClient()
        
        # Initialize quality components
        self.validator = None
        self.fact_checker = None
        self.feedback_collector = None
        self.quality_manager = None
        self.ab_testing = None
        self.improvement_system = None
    
    async def initialize(self):
        """Initialize all quality assurance components."""
        logger.info("🚀 Initializing Quality Assurance System...")
        
        # Initialize cache and metrics
        try:
            await self.cache_manager.connect()
        except Exception as e:
            logger.warning(f"Cache connection failed: {e}, using mock cache")
            # Create mock cache methods
            self.cache_manager.get = AsyncMock(return_value=None)
            self.cache_manager.set = AsyncMock()
            self.cache_manager.ping = AsyncMock()
        
        # Mock metrics collector for demo
        self.metrics_collector.record_metric = AsyncMock()
        self.metrics_collector.get_metric_value = AsyncMock(return_value=0.02)
        
        # Add mock methods to cloud service for demo
        self.cloud_service.get_service_pricing = self._mock_get_service_pricing
        self.cloud_service.check_service_availability = self._mock_check_service_availability
        self.cloud_service.get_alternative_services = self._mock_get_alternative_services
        
        # Initialize quality components
        self.validator = RecommendationValidator(self.cloud_service, self.cache_manager)
        self.fact_checker = FactChecker(self.cloud_service, self.cache_manager)
        self.feedback_collector = FeedbackCollector(self.cache_manager)
        self.quality_manager = QualityScoreManager(self.cache_manager)
        self.ab_testing = ABTestingFramework(self.cache_manager)
        self.improvement_system = ContinuousImprovementSystem(self.cache_manager, self.metrics_collector)
        
        # Initialize components
        await self.feedback_collector.initialize()
        await self.quality_manager.initialize()
        await self.ab_testing.initialize()
        await self.improvement_system.initialize()
        
        logger.info("✅ Quality Assurance System initialized successfully!")
    
    async def _mock_get_service_pricing(self, provider, service_name, configuration):
        """Mock service pricing API."""
        return {"monthly_cost": 145.0}
    
    async def _mock_check_service_availability(self, provider, service_name, region):
        """Mock service availability check."""
        return True
    
    async def _mock_get_alternative_services(self, provider, service_name, requirements):
        """Mock alternative services API."""
        return [
            {"cost": 120.0, "service": "t3.small"},
            {"cost": 180.0, "service": "t3.large"}
        ]
    
    async def demo_recommendation_validation(self):
        """Demonstrate recommendation validation and fact-checking."""
        logger.info("\n" + "="*60)
        logger.info("📋 RECOMMENDATION VALIDATION DEMO")
        logger.info("="*60)
        
        # Create sample recommendation
        recommendation = Recommendation(
            recommendation_id="demo_rec_001",
            service_name="EC2",
            provider="AWS",
            cost_estimate=150.0,
            configuration={
                "instance_type": "t3.medium",
                "region": "us-east-1",
                "storage": "20GB SSD"
            },
            features=["Auto Scaling", "Load Balancing", "Monitoring"],
            confidence_score=0.85
        )
        
        # Create sample assessment
        assessment = Assessment(
            assessment_id="demo_assessment_001",
            business_requirements={
                "budget_range": "1000-5000",
                "timeline": "3_months",
                "business_goals": ["cost_optimization", "scalability", "reliability"]
            },
            technical_requirements={
                "compute": {"cpu": 4, "memory": 8, "storage": 100},
                "network": {"bandwidth": "1Gbps"},
                "availability": "99.9%"
            },
            compliance_requirements={
                "regulations": ["GDPR", "SOC2"],
                "data_residency": "US"
            }
        )
        
        logger.info(f"🔍 Validating recommendation: {recommendation.service_name} ({recommendation.provider})")
        logger.info(f"💰 Estimated cost: ${recommendation.cost_estimate}/month")
        
        # Perform validation
        try:
            validation_results = await self.validator.validate_recommendation(recommendation, assessment)
            
            logger.info(f"📊 Validation completed with {len(validation_results)} checks")
            
            # Display validation results
            for result in validation_results:
                status_emoji = {
                    ValidationStatus.VALIDATED: "✅",
                    ValidationStatus.NEEDS_REVIEW: "⚠️",
                    ValidationStatus.FAILED: "❌",
                    ValidationStatus.PENDING: "⏳"
                }[result.status]
                
                severity_emoji = {
                    ValidationSeverity.LOW: "🟢",
                    ValidationSeverity.MEDIUM: "🟡",
                    ValidationSeverity.HIGH: "🟠",
                    ValidationSeverity.CRITICAL: "🔴"
                }[result.severity]
                
                logger.info(f"  {status_emoji} {severity_emoji} {result.check_name}: {result.status.value}")
                logger.info(f"    Confidence: {result.confidence_score:.2f}")
                
                if result.error_message:
                    logger.info(f"    Error: {result.error_message}")
            
            # Calculate overall validation score
            overall_score = sum(r.confidence_score for r in validation_results) / len(validation_results)
            logger.info(f"🎯 Overall validation score: {overall_score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
        
        # Demonstrate fact-checking
        logger.info(f"\n🔍 Fact-checking recommendation claims...")
        
        try:
            fact_check_results = await self.fact_checker.fact_check_recommendation(recommendation)
            
            for result in fact_check_results:
                verified_emoji = "✅" if result.verified else "❌"
                logger.info(f"  {verified_emoji} {result.claim}")
                logger.info(f"    Source: {result.source}")
                logger.info(f"    Confidence: {result.confidence:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Fact-checking failed: {e}")
    
    async def demo_feedback_collection(self):
        """Demonstrate feedback collection and quality scoring."""
        logger.info("\n" + "="*60)
        logger.info("💬 FEEDBACK COLLECTION DEMO")
        logger.info("="*60)
        
        # Simulate multiple user feedback submissions
        feedback_scenarios = [
            {
                "user_id": "user_001",
                "rating": 5,
                "comment": "Excellent recommendation! Easy to implement and cost-effective.",
                "implementation_success": True,
                "technical_accuracy": 5,
                "business_value_realized": 5,
                "ease_of_implementation": 5,
                "would_recommend": True,
                "tags": ["excellent", "cost-effective", "easy"]
            },
            {
                "user_id": "user_002",
                "rating": 4,
                "comment": "Good recommendation, but took longer to implement than expected.",
                "implementation_success": True,
                "technical_accuracy": 4,
                "business_value_realized": 4,
                "ease_of_implementation": 3,
                "would_recommend": True,
                "tags": ["good", "slow-implementation"]
            },
            {
                "user_id": "user_003",
                "rating": 2,
                "comment": "Recommendation was not accurate. Costs were much higher than estimated.",
                "implementation_success": False,
                "technical_accuracy": 2,
                "business_value_realized": 2,
                "ease_of_implementation": 3,
                "would_recommend": False,
                "tags": ["inaccurate", "expensive", "disappointing"]
            },
            {
                "user_id": "user_004",
                "rating": 4,
                "comment": "Solid recommendation with good business value.",
                "implementation_success": True,
                "technical_accuracy": 4,
                "business_value_realized": 5,
                "ease_of_implementation": 4,
                "would_recommend": True,
                "tags": ["solid", "business-value"]
            }
        ]
        
        recommendation_id = "demo_rec_001"
        
        logger.info(f"📝 Collecting feedback for recommendation: {recommendation_id}")
        
        # Submit feedback
        for i, scenario in enumerate(feedback_scenarios):
            feedback = UserFeedback(
                feedback_id=f"demo_feedback_{i+1}",
                user_id=scenario["user_id"],
                assessment_id="demo_assessment_001",
                recommendation_id=recommendation_id,
                agent_name="CTO Agent",
                feedback_type=FeedbackType.RATING,
                rating=scenario["rating"],
                comment=scenario["comment"],
                implementation_success=scenario["implementation_success"],
                technical_accuracy=scenario["technical_accuracy"],
                business_value_realized=scenario["business_value_realized"],
                ease_of_implementation=scenario["ease_of_implementation"],
                would_recommend=scenario["would_recommend"],
                tags=scenario["tags"]
            )
            
            try:
                success = await self.feedback_collector.collect_feedback(feedback)
                if success:
                    logger.info(f"  ✅ Feedback from {scenario['user_id']}: {scenario['rating']}/5 stars")
                else:
                    logger.error(f"  ❌ Failed to collect feedback from {scenario['user_id']}")
            except Exception as e:
                logger.error(f"  ❌ Error collecting feedback: {e}")
        
        # Get feedback summary
        logger.info(f"\n📊 Generating feedback summary...")
        
        try:
            summary = await self.feedback_collector.get_feedback_summary(recommendation_id)
            
            logger.info(f"  Total feedback: {summary.get('total_feedback', 0)}")
            logger.info(f"  Average rating: {summary.get('average_rating', 0):.2f}/5")
            logger.info(f"  Implementation success rate: {summary.get('implementation_success_rate', 0):.1%}")
            
            if 'rating_distribution' in summary:
                logger.info("  Rating distribution:")
                for rating, count in summary['rating_distribution'].items():
                    logger.info(f"    {rating} stars: {count} users")
            
            if 'sentiment_analysis' in summary:
                sentiment = summary['sentiment_analysis']
                logger.info(f"  Sentiment: {sentiment['sentiment']} (confidence: {sentiment['confidence']:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Failed to get feedback summary: {e}")
        
        # Get quality score
        logger.info(f"\n🎯 Calculating quality score...")
        
        try:
            # Wait a moment for processing
            await asyncio.sleep(1)
            
            quality_score = await self.quality_manager.get_quality_score(recommendation_id)
            
            if quality_score:
                logger.info(f"  Overall score: {quality_score.overall_score:.2f}")
                logger.info(f"  Accuracy score: {quality_score.accuracy_score:.2f}")
                logger.info(f"  Usefulness score: {quality_score.usefulness_score:.2f}")
                logger.info(f"  Implementation score: {quality_score.implementation_score:.2f}")
                logger.info(f"  Business value score: {quality_score.business_value_score:.2f}")
                logger.info(f"  Sample size: {quality_score.sample_size}")
                logger.info(f"  Confidence interval: {quality_score.confidence_interval}")
            else:
                logger.info("  No quality score available yet (processing in background)")
            
        except Exception as e:
            logger.error(f"❌ Failed to get quality score: {e}")
    
    async def demo_ab_testing(self):
        """Demonstrate A/B testing framework."""
        logger.info("\n" + "="*60)
        logger.info("🧪 A/B TESTING FRAMEWORK DEMO")
        logger.info("="*60)
        
        # Create experiment variants
        variants = [
            ExperimentVariant(
                variant_id="control",
                name="Current Strategy",
                description="Current recommendation algorithm",
                configuration={"strategy_name": "default", "weight_cost": 0.4, "weight_performance": 0.6},
                traffic_allocation=0.5,
                is_control=True
            ),
            ExperimentVariant(
                variant_id="treatment",
                name="Enhanced Strategy",
                description="Enhanced recommendation algorithm with ML optimization",
                configuration={"strategy_name": "ml_enhanced", "weight_cost": 0.3, "weight_performance": 0.7},
                traffic_allocation=0.5,
                is_control=False
            )
        ]
        
        # Create experiment metrics
        metrics = [
            ExperimentMetric(
                metric_name="user_satisfaction",
                metric_type="continuous",
                primary=True,
                description="Average user satisfaction rating",
                target_improvement=0.15
            ),
            ExperimentMetric(
                metric_name="implementation_success",
                metric_type="conversion",
                primary=False,
                description="Percentage of successful implementations"
            )
        ]
        
        # Create experiment
        experiment = Experiment(
            experiment_id="demo_experiment_001",
            name="Recommendation Strategy Optimization",
            description="Test enhanced recommendation strategy vs current approach",
            experiment_type=ExperimentType.RECOMMENDATION_STRATEGY,
            status=ExperimentStatus.ACTIVE,
            variants=variants,
            metrics=metrics,
            target_sample_size=100,
            confidence_level=0.95,
            minimum_detectable_effect=0.1,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            created_by="demo_admin"
        )
        
        logger.info(f"🧪 Creating experiment: {experiment.name}")
        
        try:
            success = await self.ab_testing.create_experiment(experiment)
            
            if success:
                logger.info("  ✅ Experiment created successfully")
                
                # Simulate user assignments
                logger.info(f"\n👥 Simulating user assignments...")
                
                assignments = {}
                for i in range(20):  # Simulate 20 users
                    user_id = f"demo_user_{i+1:03d}"
                    
                    variant_id = await self.ab_testing.assign_user_to_experiment(
                        experiment.experiment_id, user_id
                    )
                    
                    if variant_id:
                        assignments[user_id] = variant_id
                        logger.info(f"  👤 {user_id} → {variant_id}")
                
                # Show assignment distribution
                control_count = sum(1 for v in assignments.values() if v == "control")
                treatment_count = sum(1 for v in assignments.values() if v == "treatment")
                
                logger.info(f"\n📊 Assignment distribution:")
                logger.info(f"  Control: {control_count} users ({control_count/len(assignments):.1%})")
                logger.info(f"  Treatment: {treatment_count} users ({treatment_count/len(assignments):.1%})")
                
                # Simulate experiment events
                logger.info(f"\n📈 Simulating experiment events...")
                
                for user_id, variant_id in assignments.items():
                    # Simulate different success rates for variants
                    if variant_id == "control":
                        satisfaction = 3.5 + (hash(user_id) % 100) / 100 * 1.5  # 3.5-5.0
                        success = (hash(user_id) % 100) < 75  # 75% success rate
                    else:  # treatment
                        satisfaction = 4.0 + (hash(user_id) % 100) / 100 * 1.0  # 4.0-5.0
                        success = (hash(user_id) % 100) < 85  # 85% success rate
                    
                    # Record satisfaction event
                    await self.ab_testing.record_experiment_event(
                        user_id, "satisfaction_rating", {"rating": satisfaction}
                    )
                    
                    # Record implementation success event
                    if success:
                        await self.ab_testing.record_experiment_event(
                            user_id, "implementation_success", {"success": True}
                        )
                
                logger.info("  ✅ Events recorded successfully")
                
                # Analyze experiment results
                logger.info(f"\n📊 Analyzing experiment results...")
                
                try:
                    analysis = await self.ab_testing.analyze_experiment(experiment.experiment_id)
                    
                    logger.info(f"  Experiment: {analysis['experiment_name']}")
                    logger.info(f"  Total participants: {analysis['total_participants']}")
                    
                    if 'variant_results' in analysis:
                        for variant_id, result in analysis['variant_results'].items():
                            logger.info(f"\n  📈 {variant_id.upper()} Results:")
                            logger.info(f"    Sample size: {result.sample_size}")
                            if result.conversion_rate is not None:
                                logger.info(f"    Success rate: {result.conversion_rate:.1%}")
                            if result.average_value is not None:
                                logger.info(f"    Average satisfaction: {result.average_value:.2f}")
                    
                    if 'statistical_significance' in analysis:
                        logger.info(f"\n  🔬 Statistical Analysis:")
                        for variant_id, sig in analysis['statistical_significance'].items():
                            logger.info(f"    {variant_id}: {sig['significance']} (p={sig['p_value']:.4f})")
                    
                    if 'recommendations' in analysis:
                        logger.info(f"\n  💡 Recommendations:")
                        for rec in analysis['recommendations']:
                            logger.info(f"    • {rec}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Analysis failed: {e}")
                
            else:
                logger.error("  ❌ Failed to create experiment")
                
        except Exception as e:
            logger.error(f"❌ Experiment creation failed: {e}")
    
    async def demo_continuous_improvement(self):
        """Demonstrate continuous monitoring and improvement."""
        logger.info("\n" + "="*60)
        logger.info("🔄 CONTINUOUS IMPROVEMENT DEMO")
        logger.info("="*60)
        
        logger.info("🔍 Simulating quality monitoring...")
        
        # Simulate quality monitoring scenarios
        try:
            # Simulate low quality scores to trigger alerts
            await self.improvement_system._monitor_recommendation_quality()
            logger.info("  ✅ Recommendation quality monitoring completed")
            
            # Simulate feedback trend analysis
            await self.improvement_system._analyze_feedback_trends()
            logger.info("  ✅ Feedback trend analysis completed")
            
            # Simulate agent performance monitoring
            await self.improvement_system._monitor_agent_performance()
            logger.info("  ✅ Agent performance monitoring completed")
            
        except Exception as e:
            logger.error(f"  ❌ Monitoring failed: {e}")
        
        # Demonstrate alert creation
        logger.info(f"\n🚨 Creating sample quality alert...")
        
        try:
            await self.improvement_system._create_alert(
                alert_type="demo_alert",
                severity=AlertSeverity.MEDIUM,
                title="Demo Quality Alert",
                description="This is a demonstration of the quality alert system",
                affected_component="demo_component",
                metrics={"demo_metric": 0.65},
                threshold_breached={"demo_metric": {"value": 0.65, "threshold": 0.7}},
                suggested_actions=[
                    "Review demo component configuration",
                    "Analyze recent demo data",
                    "Consider demo improvements"
                ]
            )
            logger.info("  ✅ Alert created successfully")
            
        except Exception as e:
            logger.error(f"  ❌ Alert creation failed: {e}")
        
        # Demonstrate improvement action creation
        logger.info(f"\n💡 Creating sample improvement action...")
        
        try:
            await self.improvement_system._create_improvement_action(
                action_type=ImprovementActionType.UPDATE_PROMPT,
                title="Improve Demo Agent Prompts",
                description="Update agent prompts based on user feedback analysis",
                priority=3,
                affected_agents=["Demo Agent"],
                expected_impact="Improved recommendation accuracy and user satisfaction",
                implementation_effort="medium"
            )
            logger.info("  ✅ Improvement action created successfully")
            
        except Exception as e:
            logger.error(f"  ❌ Improvement action creation failed: {e}")
        
        # Get system quality overview
        logger.info(f"\n📊 Generating system quality overview...")
        
        try:
            overview = await self.quality_manager.get_system_quality_overview()
            
            if 'system_metrics' in overview:
                metrics = overview['system_metrics']
                logger.info(f"  Total recommendations: {metrics.get('total_recommendations', 0)}")
                logger.info(f"  Average quality score: {metrics.get('average_quality_score', 0):.2f}")
                logger.info(f"  Average accuracy score: {metrics.get('average_accuracy_score', 0):.2f}")
            
            if 'agent_performance' in overview:
                perf = overview['agent_performance']
                logger.info(f"  Total agents: {perf.get('total_agents', 0)}")
                
                top_agents = perf.get('top_performing_agents', [])
                if top_agents:
                    logger.info("  Top performing agents:")
                    for agent in top_agents[:3]:
                        logger.info(f"    • {agent.get('agent_name', 'Unknown')}: {agent.get('average_rating', 0):.2f}/5")
            
        except Exception as e:
            logger.error(f"  ❌ Overview generation failed: {e}")
    
    async def run_demo(self):
        """Run the complete quality assurance demo."""
        logger.info("🎯 Starting Comprehensive Quality Assurance Demo")
        logger.info("=" * 80)
        
        try:
            # Initialize system
            await self.initialize()
            
            # Run demo sections
            await self.demo_recommendation_validation()
            await self.demo_feedback_collection()
            await self.demo_ab_testing()
            await self.demo_continuous_improvement()
            
            logger.info("\n" + "="*80)
            logger.info("🎉 Quality Assurance Demo completed successfully!")
            logger.info("="*80)
            
            # Summary
            logger.info("\n📋 DEMO SUMMARY:")
            logger.info("✅ Recommendation validation and fact-checking")
            logger.info("✅ User feedback collection and quality scoring")
            logger.info("✅ A/B testing framework for recommendation strategies")
            logger.info("✅ Continuous monitoring and quality improvement")
            
            logger.info("\n💡 Key Features Demonstrated:")
            logger.info("• Advanced validation with multiple checks and confidence scoring")
            logger.info("• Comprehensive feedback analysis with sentiment detection")
            logger.info("• Statistical A/B testing with significance analysis")
            logger.info("• Automated quality monitoring with alert generation")
            logger.info("• Improvement action tracking and management")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise


async def main():
    """Main demo function."""
    demo = QualityAssuranceDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())