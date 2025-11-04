"""
Feature Engineering for Recommendation Ranking.

Extracts 50+ features from recommendations, assessments, and user interactions
for ML-based ranking models.
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from decimal import Decimal

logger = logging.getLogger(__name__)


class RecommendationFeatureStore:
    """
    Feature engineering for learning-to-rank recommendations.

    Extracts features across multiple categories:
    - Recommendation intrinsic features (15)
    - User/company profile features (10)
    - Context features (10)
    - Interaction/historical features (15)
    """

    @staticmethod
    def extract_features(
        recommendation: Dict[str, Any],
        assessment: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Extract comprehensive feature vector for ranking.

        Args:
            recommendation: Recommendation document
            assessment: Assessment document
            user_profile: User profile (optional)
            historical_data: Historical interaction data (optional)

        Returns:
            Feature vector (50+ dimensions)
        """
        features = []

        try:
            # === RECOMMENDATION INTRINSIC FEATURES (15) ===
            features.extend(RecommendationFeatureStore._extract_recommendation_features(recommendation))

            # === USER/COMPANY PROFILE FEATURES (10) ===
            features.extend(RecommendationFeatureStore._extract_user_features(assessment, user_profile))

            # === CONTEXT FEATURES (10) ===
            features.extend(RecommendationFeatureStore._extract_context_features(recommendation, assessment))

            # === INTERACTION/HISTORICAL FEATURES (15) ===
            features.extend(RecommendationFeatureStore._extract_historical_features(
                recommendation, historical_data or {}
            ))

            return np.array(features, dtype=np.float32)

        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            # Return default feature vector
            return np.zeros(50, dtype=np.float32)

    @staticmethod
    def _extract_recommendation_features(rec: Dict[str, Any]) -> List[float]:
        """Extract intrinsic recommendation features."""
        features = []

        # 1. Confidence score (0-1)
        features.append(float(rec.get('confidence_score', 0.5)))

        # 2. Normalized cost (log scale)
        cost = float(rec.get('estimated_cost', 0) or 0)
        features.append(np.log1p(cost) / 10.0)  # Normalize to ~0-1

        # 3. Implementation complexity (0-1)
        complexity_map = {'low': 0.33, 'medium': 0.66, 'high': 1.0}
        complexity = rec.get('implementation_effort', 'medium')
        features.append(complexity_map.get(complexity, 0.66))

        # 4. ROI potential (cost savings / cost)
        savings = float(rec.get('estimated_cost_savings', 0) or 0)
        roi = savings / (cost + 1) if cost > 0 else 0
        features.append(min(roi, 5.0) / 5.0)  # Cap at 5x, normalize

        # 5. Priority score (0-1)
        priority_map = {'low': 0.33, 'medium': 0.66, 'high': 1.0}
        priority = rec.get('priority', 'medium')
        features.append(priority_map.get(priority, 0.66))

        # 6. Business impact score (0-1)
        impact_map = {
            'low': 0.2,
            'medium': 0.4,
            'moderate': 0.6,
            'high': 0.8,
            'transformational': 1.0
        }
        impact = rec.get('business_impact', 'medium')
        features.append(impact_map.get(impact, 0.5))

        # 7-9. Category one-hot encoding (simplified)
        category = rec.get('category', '').lower()
        features.append(1.0 if 'cost' in category else 0.0)
        features.append(1.0 if 'security' in category else 0.0)
        features.append(1.0 if 'performance' in category else 0.0)

        # 10. Cloud provider preference alignment
        provider = rec.get('cloud_provider', '').lower()
        features.append(1.0 if provider in ['aws', 'azure', 'gcp'] else 0.0)

        # 11. Number of benefits (normalized)
        benefits = rec.get('benefits', [])
        features.append(min(len(benefits), 10) / 10.0)

        # 12. Number of risks (inverse, normalized)
        risks = rec.get('risks', [])
        features.append(1.0 - min(len(risks), 10) / 10.0)

        # 13. Implementation steps count (complexity indicator)
        steps = rec.get('implementation_steps', [])
        features.append(min(len(steps), 20) / 20.0)

        # 14. Has prerequisites (binary)
        prerequisites = rec.get('prerequisites', [])
        features.append(1.0 if len(prerequisites) > 0 else 0.0)

        # 15. Agent reliability (based on agent name)
        agent_reliability = RecommendationFeatureStore._get_agent_reliability(
            rec.get('agent_name', '')
        )
        features.append(agent_reliability)

        return features

    @staticmethod
    def _extract_user_features(
        assessment: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]]
    ) -> List[float]:
        """Extract user/company profile features."""
        features = []

        biz_req = assessment.get('business_requirements', {}) or {}

        # 1. Company size tier (0-1)
        size_map = {
            'startup': 0.2,
            'small': 0.4,
            'medium': 0.6,
            'large': 0.8,
            'enterprise': 1.0
        }
        company_size = biz_req.get('company_size', 'medium')
        features.append(size_map.get(company_size, 0.5))

        # 2. Industry hash (for embeddings)
        industry = biz_req.get('industry', 'technology')
        industry_hash = int(hashlib.md5(industry.encode()).hexdigest(), 16) % 100
        features.append(industry_hash / 100.0)

        # 3. Technical maturity (0-1)
        team = biz_req.get('team_structure', {}) or {}
        cloud_expertise = team.get('cloud_expertise_level', 3)
        features.append(cloud_expertise / 5.0)

        # 4. Budget tier (0-1)
        budget_range = biz_req.get('budget_constraints', {}) or {}
        budget_tier_map = {
            '0_10k': 0.2,
            '10k_50k': 0.4,
            '50k_100k': 0.6,
            '100k_500k': 0.8,
            '500k_plus': 1.0
        }
        budget = budget_range.get('total_budget_range', '10k_50k')
        features.append(budget_tier_map.get(budget, 0.4))

        # 5. Risk tolerance (based on urgency and maturity)
        urgency = biz_req.get('urgency_level', 'medium')
        urgency_map = {'low': 0.8, 'medium': 0.5, 'high': 0.2}  # High urgency = low risk tolerance
        features.append(urgency_map.get(urgency, 0.5))

        # 6. Cost optimization priority (0-1)
        cost_priority = budget_range.get('cost_optimization_priority', 'medium')
        priority_map = {'low': 0.33, 'medium': 0.66, 'high': 1.0}
        features.append(priority_map.get(cost_priority, 0.66))

        # 7. Multi-cloud preference
        multi_cloud = biz_req.get('multi_cloud_acceptable', False)
        features.append(1.0 if multi_cloud else 0.0)

        # 8. Number of business goals (normalized)
        goals = biz_req.get('business_goals', [])
        features.append(min(len(goals), 10) / 10.0)

        # 9. Number of pain points (urgency indicator)
        pain_points = biz_req.get('current_pain_points', [])
        features.append(min(len(pain_points), 10) / 10.0)

        # 10. Compliance requirements count
        compliance = biz_req.get('compliance_requirements', [])
        features.append(min(len([c for c in compliance if c != 'none']), 5) / 5.0)

        return features

    @staticmethod
    def _extract_context_features(
        rec: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> List[float]:
        """Extract contextual features."""
        features = []

        # 1. Assessment completeness (0-1)
        completeness = assessment.get('completion_percentage', 0) / 100.0
        features.append(completeness)

        # 2. Assessment age (days since creation, normalized)
        created_at = assessment.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_dt = created_at
            age_days = (datetime.now() - created_dt.replace(tzinfo=None)).days
            features.append(min(age_days, 365) / 365.0)
        else:
            features.append(0.0)

        # 3. Recommendation recency (0-1, newer is better)
        rec_created = rec.get('created_at')
        if rec_created:
            if isinstance(rec_created, str):
                rec_dt = datetime.fromisoformat(rec_created.replace('Z', '+00:00'))
            else:
                rec_dt = rec_created
            rec_age_days = (datetime.now() - rec_dt.replace(tzinfo=None)).days
            features.append(1.0 - min(rec_age_days, 90) / 90.0)
        else:
            features.append(0.5)

        # 4-6. Market trend alignment (mock - would use real trend data)
        category = rec.get('category', '').lower()
        features.append(0.9 if 'cost' in category else 0.5)  # Cost optimization is trending
        features.append(0.85 if 'security' in category else 0.5)  # Security always important
        features.append(0.75 if 'ai' in category or 'ml' in category else 0.5)  # AI/ML trending

        # 7. Technology recency (newer tech = higher score)
        # Based on cloud provider and service type
        provider = rec.get('cloud_provider', '').lower()
        features.append(0.9 if provider in ['aws', 'azure', 'gcp'] else 0.5)

        # 8. Assessment status alignment
        status = assessment.get('status', '').lower()
        status_map = {
            'draft': 0.3,
            'in_progress': 0.6,
            'completed': 1.0
        }
        features.append(status_map.get(status, 0.5))

        # 9. Recommendation-assessment category alignment
        tech_req = assessment.get('technical_requirements', {}) or {}
        # Simple heuristic: does rec category match assessment needs?
        features.append(0.8)  # Placeholder - would use semantic similarity

        # 10. Seasonal/time-based factor (e.g., end-of-year budget considerations)
        current_month = datetime.now().month
        # Q4 = budget planning, higher weight for cost optimization
        q4_factor = 1.2 if current_month in [10, 11, 12] else 1.0
        features.append(q4_factor)

        return features

    @staticmethod
    def _extract_historical_features(
        rec: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[float]:
        """Extract historical interaction features."""
        features = []

        # 1. Historical click-through rate for similar recs
        ctr = historical_data.get('click_through_rate', 0.1)
        features.append(min(ctr, 1.0))

        # 2. Implementation rate for similar recs
        impl_rate = historical_data.get('implementation_rate', 0.05)
        features.append(min(impl_rate, 1.0))

        # 3. Average rating for similar recs
        avg_rating = historical_data.get('average_rating', 3.0)
        features.append(avg_rating / 5.0)

        # 4. Share rate
        share_rate = historical_data.get('share_rate', 0.02)
        features.append(min(share_rate, 1.0))

        # 5. Save/favorite rate
        save_rate = historical_data.get('save_rate', 0.03)
        features.append(min(save_rate, 1.0))

        # 6. Average time spent viewing (normalized)
        avg_time = historical_data.get('avg_view_time_seconds', 30)
        features.append(min(avg_time, 300) / 300.0)

        # 7. Similar user acceptance rate
        similar_user_rate = historical_data.get('similar_user_acceptance', 0.15)
        features.append(min(similar_user_rate, 1.0))

        # 8. Time decay factor (how long since last similar rec)
        last_similar_time = historical_data.get('last_similar_rec_time')
        if last_similar_time:
            hours_since = (datetime.now() - last_similar_time).total_seconds() / 3600
            decay = np.exp(-hours_since / 168)  # 1 week half-life
            features.append(decay)
        else:
            features.append(0.5)

        # 9. Agent historical accuracy
        agent_name = rec.get('agent_name', '')
        agent_accuracy = historical_data.get(f'agent_{agent_name}_accuracy', 0.7)
        features.append(min(agent_accuracy, 1.0))

        # 10. Category popularity (% of implemented recs in this category)
        category = rec.get('category', '')
        category_popularity = historical_data.get(f'category_{category}_popularity', 0.2)
        features.append(min(category_popularity, 1.0))

        # 11. Complementarity score (how well it works with already accepted recs)
        complementarity = historical_data.get('complementarity_score', 0.5)
        features.append(complementarity)

        # 12. Diversity bonus (novelty score)
        novelty = historical_data.get('novelty_score', 0.5)
        features.append(novelty)

        # 13. Recency bias (prefer newer recommendations)
        features.append(0.8)  # Placeholder

        # 14. Conversion funnel position (where users typically convert)
        funnel_position = historical_data.get('funnel_position_score', 0.5)
        features.append(funnel_position)

        # 15. Global popularity score
        global_popularity = historical_data.get('global_popularity', 0.3)
        features.append(min(global_popularity, 1.0))

        return features

    @staticmethod
    def _get_agent_reliability(agent_name: str) -> float:
        """
        Get agent reliability score based on historical performance.

        In production, this would query a metrics database.
        For now, use heuristic scores.
        """
        reliability_map = {
            'cto_agent': 0.85,
            'cloud_engineer_agent': 0.90,
            'infrastructure_agent': 0.88,
            'mlops_agent': 0.82,
            'compliance_agent': 0.92,
            'research_agent': 0.75,
            'ai_consultant_agent': 0.80,
            'report_generator_agent': 0.78
        }

        return reliability_map.get(agent_name.lower(), 0.75)

    @staticmethod
    def get_feature_names() -> List[str]:
        """
        Get feature names for interpretability.

        Returns:
            List of feature names corresponding to feature vector positions
        """
        names = []

        # Recommendation features
        names.extend([
            'confidence_score', 'log_cost_normalized', 'implementation_complexity',
            'roi_potential', 'priority_score', 'business_impact',
            'is_cost_category', 'is_security_category', 'is_performance_category',
            'cloud_provider_preference', 'num_benefits_norm', 'inverse_risks_norm',
            'implementation_steps_norm', 'has_prerequisites', 'agent_reliability'
        ])

        # User features
        names.extend([
            'company_size_tier', 'industry_hash', 'technical_maturity',
            'budget_tier', 'risk_tolerance', 'cost_optimization_priority',
            'multi_cloud_preference', 'num_business_goals', 'num_pain_points',
            'compliance_requirements_count'
        ])

        # Context features
        names.extend([
            'assessment_completeness', 'assessment_age_norm', 'rec_recency',
            'cost_trend_alignment', 'security_trend_alignment', 'ai_trend_alignment',
            'technology_recency', 'assessment_status', 'category_alignment',
            'seasonal_factor'
        ])

        # Historical features
        names.extend([
            'historical_ctr', 'implementation_rate', 'avg_rating_norm',
            'share_rate', 'save_rate', 'avg_view_time_norm',
            'similar_user_acceptance', 'time_decay', 'agent_accuracy',
            'category_popularity', 'complementarity', 'novelty',
            'recency_bias', 'funnel_position', 'global_popularity'
        ])

        return names
