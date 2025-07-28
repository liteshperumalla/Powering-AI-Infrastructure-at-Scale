#!/usr/bin/env python3
"""
Simple test script to verify the quality assurance system is working.
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock

from src.infra_mind.quality.validation import RecommendationValidator, ValidationStatus
from src.infra_mind.quality.feedback import FeedbackCollector, UserFeedback, FeedbackType
from src.infra_mind.quality.ab_testing import ABTestingFramework, Experiment, ExperimentVariant, ExperimentMetric, ExperimentType, ExperimentStatus
from src.infra_mind.models.simple_recommendation import Recommendation, Assessment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_recommendation_validation():
    """Test recommendation validation system."""
    logger.info("🔍 Testing Recommendation Validation...")
    
    # Create mock dependencies
    mock_cloud_service = Mock()
    mock_cloud_service.get_service_pricing = AsyncMock(return_value={"monthly_cost": 95.0})
    mock_cloud_service.check_service_availability = AsyncMock(return_value=True)
    mock_cloud_service.get_alternative_services = AsyncMock(return_value=[
        {"cost": 90.0, "service": "t3.small"}
    ])
    
    mock_cache_manager = Mock()
    mock_cache_manager.get = AsyncMock(return_value=None)
    mock_cache_manager.set = AsyncMock()
    
    # Create validator
    validator = RecommendationValidator(mock_cloud_service, mock_cache_manager)
    
    # Create test data
    recommendation = Recommendation(
        recommendation_id="test_rec_1",
        service_name="EC2",
        provider="AWS",
        cost_estimate=100.0,
        configuration={"instance_type": "t3.medium"},
        features=["Auto Scaling", "Load Balancing"]
    )
    
    assessment = Assessment(
        assessment_id="test_assessment_1",
        business_requirements={"budget_range": "1000-5000"},
        technical_requirements={"compute": {"cpu": 4, "memory": 8}},
        compliance_requirements={"regulations": ["GDPR"]}
    )
    
    # Run validation
    results = await validator.validate_recommendation(recommendation, assessment)
    
    # Verify results
    assert len(results) > 0, "Should have validation results"
    
    pricing_results = [r for r in results if r.check_name == "pricing_accuracy"]
    assert len(pricing_results) > 0, "Should have pricing validation"
    
    availability_results = [r for r in results if "service_availability" in r.check_name]
    assert len(availability_results) > 0, "Should have availability validation"
    
    logger.info(f"✅ Validation completed with {len(results)} checks")
    for result in results:
        status_emoji = "✅" if result.status == ValidationStatus.VALIDATED else "⚠️"
        logger.info(f"  {status_emoji} {result.check_name}: {result.status.value} (confidence: {result.confidence_score:.2f})")
    
    return True


async def test_feedback_collection():
    """Test feedback collection system."""
    logger.info("💬 Testing Feedback Collection...")
    
    # Create mock dependencies
    mock_cache_manager = Mock()
    
    # Create feedback collector
    collector = FeedbackCollector(mock_cache_manager)
    
    # Mock database
    collector.db = Mock()
    collector.db.feedback = Mock()
    collector.db.feedback.insert_one = AsyncMock()
    
    # Create test feedback
    feedback = UserFeedback(
        feedback_id="test_feedback_1",
        user_id="user_123",
        assessment_id="assessment_123",
        recommendation_id="rec_123",
        agent_name="CTO Agent",
        feedback_type=FeedbackType.RATING,
        rating=4,
        comment="Good recommendation",
        implementation_success=True,
        technical_accuracy=4,
        business_value_realized=4
    )
    
    # Submit feedback
    success = await collector.collect_feedback(feedback)
    
    # Verify
    assert success, "Feedback collection should succeed"
    collector.db.feedback.insert_one.assert_called_once()
    
    logger.info("✅ Feedback collection working correctly")
    return True


async def test_ab_testing():
    """Test A/B testing framework."""
    logger.info("🧪 Testing A/B Testing Framework...")
    
    # Create mock dependencies
    mock_cache_manager = Mock()
    mock_cache_manager.get = AsyncMock(return_value=None)
    mock_cache_manager.set = AsyncMock()
    
    # Create A/B testing framework
    ab_testing = ABTestingFramework(mock_cache_manager)
    
    # Create test variants
    variants = [
        ExperimentVariant(
            variant_id="control",
            name="Control",
            description="Current approach",
            configuration={"strategy": "default"},
            traffic_allocation=0.5,
            is_control=True
        ),
        ExperimentVariant(
            variant_id="treatment",
            name="Treatment",
            description="New approach",
            configuration={"strategy": "enhanced"},
            traffic_allocation=0.5,
            is_control=False
        )
    ]
    
    # Test variant assignment
    variant_assignments = {}
    for i in range(10):
        user_id = f"user_{i}"
        variant_id = ab_testing._assign_variant(user_id, [v.__dict__ for v in variants])
        variant_assignments[user_id] = variant_id
    
    # Verify assignments
    control_count = sum(1 for v in variant_assignments.values() if v == "control")
    treatment_count = sum(1 for v in variant_assignments.values() if v == "treatment")
    
    logger.info(f"✅ A/B testing assignments: {control_count} control, {treatment_count} treatment")
    
    # Test consistency (same user should get same variant)
    variant1 = ab_testing._assign_variant("test_user", [v.__dict__ for v in variants])
    variant2 = ab_testing._assign_variant("test_user", [v.__dict__ for v in variants])
    assert variant1 == variant2, "Assignment should be consistent"
    
    logger.info("✅ A/B testing framework working correctly")
    return True


async def main():
    """Run all tests."""
    logger.info("🎯 Testing Quality Assurance System")
    logger.info("=" * 50)
    
    try:
        # Run tests
        await test_recommendation_validation()
        await test_feedback_collection()
        await test_ab_testing()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 All Quality Assurance Tests Passed!")
        logger.info("=" * 50)
        
        logger.info("\n📋 Test Summary:")
        logger.info("✅ Recommendation validation with multiple checks")
        logger.info("✅ User feedback collection and processing")
        logger.info("✅ A/B testing framework with consistent assignment")
        logger.info("✅ Confidence scoring and validation status")
        logger.info("✅ Mock integration with cloud services")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())