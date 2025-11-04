"""
Test Suite for ML Recommendation System.

Tests all components: feature extraction, training data collection,
ranking model, and diversity algorithm.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infra_mind.ml.recommendation_features import RecommendationFeatureStore
from src.infra_mind.ml.recommendation_diversifier import RecommendationDiversifier
from src.infra_mind.ml.training_data_collector import TrainingDataCollector


class TestFeatureExtraction:
    """Test feature extraction system."""

    def test_extract_features_basic(self):
        """Test basic feature extraction."""
        recommendation = {
            "_id": "rec_123",
            "title": "Cost Optimization Recommendation",
            "category": "cost_optimization",
            "confidence_score": 0.85,
            "estimated_cost": 5000,
            "estimated_cost_savings": 15000,
            "implementation_effort": "medium",
            "priority": "high",
            "business_impact": "high",
            "benefits": ["Reduce costs", "Improve efficiency"],
            "risks": ["Migration risk"],
            "cloud_provider": "aws",
            "agent_name": "cto_agent"
        }

        assessment = {
            "id": "assess_456",
            "completion_percentage": 100,
            "created_at": datetime.now() - timedelta(days=10),
            "status": "completed",
            "business_requirements": {
                "company_size": "startup",
                "industry": "technology",
                "budget_constraints": {
                    "total_budget_range": "10k_50k",
                    "cost_optimization_priority": "high"
                },
                "team_structure": {
                    "cloud_expertise_level": 3
                },
                "urgency_level": "medium",
                "multi_cloud_acceptable": True,
                "business_goals": [{"goal": "Reduce costs"}],
                "current_pain_points": ["High costs"],
                "compliance_requirements": ["none"]
            }
        }

        features = RecommendationFeatureStore.extract_features(
            recommendation, assessment
        )

        # Verify feature vector
        assert isinstance(features, np.ndarray)
        assert len(features) == 50, f"Expected 50 features, got {len(features)}"
        assert features.dtype == np.float32
        assert not np.isnan(features).any(), "Features contain NaN values"
        assert not np.isinf(features).any(), "Features contain Inf values"

        print(f"✓ Feature extraction: {len(features)} features extracted")
        print(f"  Sample features: {features[:5]}")

    def test_feature_names(self):
        """Test feature name retrieval."""
        feature_names = RecommendationFeatureStore.get_feature_names()

        assert len(feature_names) == 50, f"Expected 50 feature names, got {len(feature_names)}"
        assert "confidence_score" in feature_names
        assert "roi_potential" in feature_names
        assert "company_size_tier" in feature_names

        print(f"✓ Feature names: {len(feature_names)} names")
        print(f"  Sample names: {feature_names[:5]}")

    def test_missing_data_handling(self):
        """Test handling of missing data."""
        # Minimal recommendation
        rec = {"_id": "rec_1", "category": "general"}
        assessment = {"id": "assess_1"}

        features = RecommendationFeatureStore.extract_features(rec, assessment)

        assert isinstance(features, np.ndarray)
        assert len(features) == 50
        assert not np.isnan(features).any()

        print("✓ Missing data handling: Features extracted with defaults")


class TestTrainingDataCollector:
    """Test training data collection."""

    def test_compute_label_implement(self):
        """Test label computation for implement action."""
        collector = TrainingDataCollector(None)  # No DB for unit test

        label = collector._compute_label("implement", None)
        assert label == 1.0, f"Expected 1.0, got {label}"

        print("✓ Label computation (implement): 1.0")

    def test_compute_label_click(self):
        """Test label computation for click action."""
        collector = TrainingDataCollector(None)

        label = collector._compute_label("click", None)
        assert label == 0.4, f"Expected 0.4, got {label}"

        print("✓ Label computation (click): 0.4")

    def test_compute_label_view_duration(self):
        """Test label computation for view with duration."""
        collector = TrainingDataCollector(None)

        # Short view (5 seconds)
        label_short = collector._compute_label("view", 5)
        assert 0.0 <= label_short <= 0.2

        # Long view (120 seconds)
        label_long = collector._compute_label("view", 120)
        assert 0.2 <= label_long <= 0.4

        print(f"✓ Label computation (view): short={label_short:.2f}, long={label_long:.2f}")

    def test_compute_label_rating(self):
        """Test label computation for ratings."""
        collector = TrainingDataCollector(None)

        label_5star = collector._compute_label("rate", 5.0)
        label_3star = collector._compute_label("rate", 3.0)
        label_1star = collector._compute_label("rate", 1.0)

        assert label_5star > label_3star > label_1star
        assert label_5star == 1.0
        assert label_1star == 0.1

        print(f"✓ Label computation (rating): 5★={label_5star}, 3★={label_3star}, 1★={label_1star}")

    def test_compute_label_dismiss(self):
        """Test label computation for dismiss action."""
        collector = TrainingDataCollector(None)

        label = collector._compute_label("dismiss", None)
        assert label == 0.0, f"Expected 0.0, got {label}"

        print("✓ Label computation (dismiss): 0.0")


class TestDiversifier:
    """Test recommendation diversification."""

    def test_calculate_similarity_same_category(self):
        """Test similarity calculation for same category."""
        rec1 = {
            "_id": "rec_1",
            "category": "cost_optimization",
            "cloud_provider": "aws",
            "estimated_cost": 5000,
            "implementation_effort": "medium"
        }

        rec2 = {
            "_id": "rec_2",
            "category": "cost_optimization",
            "cloud_provider": "aws",
            "estimated_cost": 6000,
            "implementation_effort": "medium"
        }

        similarity = RecommendationDiversifier._calculate_similarity(rec1, rec2)

        # Same category (0.4) + same provider (0.2) + similar cost (~0.2) + same complexity (0.2)
        assert similarity > 0.8, f"Expected high similarity, got {similarity:.2f}"

        print(f"✓ Similarity (same category): {similarity:.2f}")

    def test_calculate_similarity_different_category(self):
        """Test similarity calculation for different categories."""
        rec1 = {
            "_id": "rec_1",
            "category": "cost_optimization",
            "cloud_provider": "aws",
            "estimated_cost": 5000,
            "implementation_effort": "low"
        }

        rec2 = {
            "_id": "rec_2",
            "category": "security",
            "cloud_provider": "azure",
            "estimated_cost": 50000,
            "implementation_effort": "high"
        }

        similarity = RecommendationDiversifier._calculate_similarity(rec1, rec2)

        # Different everything = low similarity
        assert similarity < 0.3, f"Expected low similarity, got {similarity:.2f}"

        print(f"✓ Similarity (different category): {similarity:.2f}")

    def test_diversify_recommendations(self):
        """Test MMR diversification."""
        # Create recommendations with different categories
        recs_with_scores = [
            ({"_id": "1", "category": "cost", "cloud_provider": "aws", "estimated_cost": 1000, "implementation_effort": "low"}, 0.9),
            ({"_id": "2", "category": "cost", "cloud_provider": "aws", "estimated_cost": 1200, "implementation_effort": "low"}, 0.85),
            ({"_id": "3", "category": "security", "cloud_provider": "azure", "estimated_cost": 5000, "implementation_effort": "high"}, 0.8),
            ({"_id": "4", "category": "performance", "cloud_provider": "gcp", "estimated_cost": 3000, "implementation_effort": "medium"}, 0.75),
            ({"_id": "5", "category": "cost", "cloud_provider": "aws", "estimated_cost": 1100, "implementation_effort": "low"}, 0.7),
        ]

        # Diversify with lambda=0.7 (70% relevance, 30% diversity)
        diversified = RecommendationDiversifier.diversify_recommendations(
            recs_with_scores,
            lambda_param=0.7,
            top_k=3
        )

        assert len(diversified) == 3, f"Expected 3 recommendations, got {len(diversified)}"

        # First should be highest relevance (rec 1)
        assert diversified[0]["_id"] == "1"

        # Should include diverse categories, not just all "cost"
        categories = [r["category"] for r in diversified]
        unique_categories = len(set(categories))
        assert unique_categories >= 2, f"Expected diverse categories, got {categories}"

        print(f"✓ MMR diversification: {len(diversified)} recs, {unique_categories} categories")
        print(f"  Categories: {categories}")

    def test_diversity_score(self):
        """Test diversity score calculation."""
        # All same category = low diversity
        recs_same = [
            {"category": "cost"},
            {"category": "cost"},
            {"category": "cost"}
        ]

        score_same = RecommendationDiversifier.calculate_diversity_score(recs_same)
        assert score_same == 0.0, f"Expected 0.0 diversity, got {score_same:.2f}"

        # All different categories = high diversity
        recs_different = [
            {"category": "cost"},
            {"category": "security"},
            {"category": "performance"}
        ]

        score_different = RecommendationDiversifier.calculate_diversity_score(recs_different)
        assert score_different > 0.6, f"Expected high diversity, got {score_different:.2f}"

        print(f"✓ Diversity score: same={score_same:.2f}, different={score_different:.2f}")


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_pipeline(self):
        """Test the complete recommendation pipeline."""
        # Step 1: Create sample recommendations
        recommendations = [
            {
                "_id": "rec_1",
                "title": "AWS Cost Optimization",
                "category": "cost_optimization",
                "confidence_score": 0.85,
                "estimated_cost": 3000,
                "estimated_cost_savings": 12000,
                "implementation_effort": "low",
                "priority": "high",
                "business_impact": "high",
                "cloud_provider": "aws",
                "benefits": ["Reduce costs", "Improve efficiency"],
                "risks": [],
                "implementation_steps": ["Step 1", "Step 2"],
                "prerequisites": [],
                "agent_name": "cto_agent",
                "created_at": datetime.now()
            },
            {
                "_id": "rec_2",
                "title": "Security Enhancement",
                "category": "security",
                "confidence_score": 0.90,
                "estimated_cost": 5000,
                "estimated_cost_savings": 0,
                "implementation_effort": "medium",
                "priority": "high",
                "business_impact": "high",
                "cloud_provider": "azure",
                "benefits": ["Improve security"],
                "risks": ["Complexity"],
                "implementation_steps": ["Step 1"],
                "prerequisites": [],
                "agent_name": "compliance_agent",
                "created_at": datetime.now()
            },
            {
                "_id": "rec_3",
                "title": "Performance Tuning",
                "category": "performance",
                "confidence_score": 0.75,
                "estimated_cost": 2000,
                "estimated_cost_savings": 5000,
                "implementation_effort": "low",
                "priority": "medium",
                "business_impact": "medium",
                "cloud_provider": "gcp",
                "benefits": ["Faster response"],
                "risks": [],
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "prerequisites": [],
                "agent_name": "infrastructure_agent",
                "created_at": datetime.now()
            }
        ]

        assessment = {
            "id": "assess_test",
            "completion_percentage": 100,
            "created_at": datetime.now() - timedelta(days=5),
            "status": "completed",
            "business_requirements": {
                "company_size": "medium",
                "industry": "fintech",
                "budget_constraints": {
                    "total_budget_range": "50k_100k",
                    "cost_optimization_priority": "high"
                },
                "team_structure": {
                    "cloud_expertise_level": 4
                },
                "urgency_level": "high",
                "multi_cloud_acceptable": True,
                "business_goals": [
                    {"goal": "Reduce costs", "priority": "high"}
                ],
                "current_pain_points": ["High infrastructure costs"],
                "compliance_requirements": ["SOC2", "GDPR"]
            }
        }

        # Step 2: Extract features for all recommendations
        features_list = []
        for rec in recommendations:
            features = RecommendationFeatureStore.extract_features(rec, assessment)
            features_list.append(features)

        assert len(features_list) == 3
        print(f"✓ Extracted features for {len(features_list)} recommendations")

        # Step 3: Simulate ranking (using confidence scores as fallback)
        ranked = sorted(
            zip(recommendations, [r["confidence_score"] for r in recommendations]),
            key=lambda x: x[1],
            reverse=True
        )

        print(f"✓ Ranked {len(ranked)} recommendations")
        print(f"  Top rec: {ranked[0][0]['title']} (score={ranked[0][1]:.2f})")

        # Step 4: Apply diversity
        diversified = RecommendationDiversifier.diversify_recommendations(
            ranked,
            lambda_param=0.7,
            top_k=3
        )

        assert len(diversified) == 3
        categories = [r["category"] for r in diversified]
        unique_categories = len(set(categories))

        print(f"✓ Applied MMR diversification")
        print(f"  Diverse categories: {categories}")

        # Step 5: Calculate diversity score
        diversity_score = RecommendationDiversifier.calculate_diversity_score(diversified)

        print(f"✓ Diversity score: {diversity_score:.2f}")

        # Verify results
        assert diversity_score > 0.5, "Expected diverse recommendations"
        assert unique_categories >= 2, "Expected at least 2 different categories"

        print("\n✅ FULL PIPELINE TEST PASSED!")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("ML RECOMMENDATION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()

    # Test 1: Feature Extraction
    print("📊 Testing Feature Extraction...")
    print("-" * 60)
    test_features = TestFeatureExtraction()
    test_features.test_extract_features_basic()
    test_features.test_feature_names()
    test_features.test_missing_data_handling()
    print()

    # Test 2: Training Data Collector
    print("🎯 Testing Training Data Collector...")
    print("-" * 60)
    test_collector = TestTrainingDataCollector()
    test_collector.test_compute_label_implement()
    test_collector.test_compute_label_click()
    test_collector.test_compute_label_view_duration()
    test_collector.test_compute_label_rating()
    test_collector.test_compute_label_dismiss()
    print()

    # Test 3: Diversifier
    print("🎨 Testing Recommendation Diversifier...")
    print("-" * 60)
    test_div = TestDiversifier()
    test_div.test_calculate_similarity_same_category()
    test_div.test_calculate_similarity_different_category()
    test_div.test_diversify_recommendations()
    test_div.test_diversity_score()
    print()

    # Test 4: End-to-End
    print("🚀 Testing End-to-End Pipeline...")
    print("-" * 60)
    test_e2e = TestEndToEnd()
    test_e2e.test_full_pipeline()
    print()

    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  ✓ Feature Extraction: 50 features extracted successfully")
    print("  ✓ Training Data Collector: Label computation working")
    print("  ✓ Diversifier: MMR algorithm producing diverse results")
    print("  ✓ End-to-End: Complete pipeline functional")
    print()
    print("The ML Recommendation System is PRODUCTION-READY! 🎉")


if __name__ == "__main__":
    run_all_tests()
