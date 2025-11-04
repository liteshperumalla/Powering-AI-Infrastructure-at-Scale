"""
Training Data Collection for Recommendation Ranking.

Tracks user interactions with recommendations to build training datasets
for Learning-to-Rank models.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)


class TrainingDataCollector:
    """
    Collects implicit and explicit feedback for training ranking models.

    Tracks interactions like clicks, views, implementations, dismissals,
    and converts them to training labels for supervised learning.
    """

    def __init__(self, db):
        """
        Initialize training data collector.

        Args:
            db: MongoDB database instance (can be None for testing)
        """
        self.db = db
        self.interactions_collection = db.get_collection('recommendation_interactions') if db is not None else None

    async def record_interaction(
        self,
        user_id: str,
        recommendation_id: str,
        interaction_type: str,
        interaction_value: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record user interaction with a recommendation.

        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            interaction_type: Type of interaction (click, view, implement, dismiss, save, share, rate)
            interaction_value: Optional value (e.g., view duration in seconds, rating 1-5)
            context: Optional context data (assessment_id, session_id, etc.)

        Returns:
            True if recorded successfully
        """
        try:
            # Compute training label from interaction
            label = self._compute_label(interaction_type, interaction_value)

            interaction_doc = {
                "user_id": user_id,
                "recommendation_id": recommendation_id,
                "interaction_type": interaction_type,
                "interaction_value": interaction_value,
                "label": label,
                "timestamp": datetime.utcnow(),
                "context": context or {},
                "created_at": datetime.utcnow()
            }

            # Insert into database
            await self.interactions_collection.insert_one(interaction_doc)

            logger.info(
                f"Recorded {interaction_type} interaction for user {user_id}, "
                f"recommendation {recommendation_id}, label={label:.2f}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
            return False

    def _compute_label(self, interaction_type: str, value: Optional[float]) -> float:
        """
        Compute training label from interaction type and value.

        Labels are on a 0-1 scale representing relevance/quality:
        - 1.0: Implemented (strongest positive signal)
        - 0.8: Saved/Favorited (strong positive signal)
        - 0.7: Rated highly (4-5 stars)
        - 0.6: Shared (moderate positive signal)
        - 0.5: Rated moderately (3 stars)
        - 0.4: Clicked (weak positive signal)
        - 0.2-0.4: Viewed (scaled by time spent)
        - 0.1: Rated low (1-2 stars)
        - 0.0: Dismissed/Hidden (negative signal)

        Args:
            interaction_type: Type of interaction
            value: Optional interaction value

        Returns:
            Label score (0-1)
        """
        interaction_type = interaction_type.lower()

        if interaction_type == 'implement' or interaction_type == 'implemented':
            return 1.0

        elif interaction_type == 'save' or interaction_type == 'favorite':
            return 0.8

        elif interaction_type == 'rate' or interaction_type == 'rating':
            if value is not None:
                # Convert 1-5 star rating to 0-1 label
                # 5 stars -> 1.0, 4 stars -> 0.7, 3 stars -> 0.5, 2 stars -> 0.2, 1 star -> 0.1
                rating = float(value)
                if rating >= 4.5:
                    return 1.0
                elif rating >= 3.5:
                    return 0.7
                elif rating >= 2.5:
                    return 0.5
                elif rating >= 1.5:
                    return 0.2
                else:
                    return 0.1
            return 0.5  # Default if no value

        elif interaction_type == 'share' or interaction_type == 'shared':
            return 0.6

        elif interaction_type == 'click' or interaction_type == 'clicked':
            return 0.4

        elif interaction_type == 'view' or interaction_type == 'viewed':
            # Scale by time spent viewing (in seconds)
            if value is not None:
                # 0-30 seconds -> 0.1-0.2
                # 30-60 seconds -> 0.2-0.3
                # 60+ seconds -> 0.3-0.4
                time_seconds = float(value)
                if time_seconds < 10:
                    return 0.1
                elif time_seconds < 30:
                    return 0.15
                elif time_seconds < 60:
                    return 0.25
                else:
                    return min(0.4, 0.25 + (time_seconds - 60) / 300)
            return 0.2  # Default view without time

        elif interaction_type == 'dismiss' or interaction_type == 'dismissed' or interaction_type == 'hide':
            return 0.0

        elif interaction_type == 'thumbs_up':
            return 0.7

        elif interaction_type == 'thumbs_down':
            return 0.1

        else:
            # Unknown interaction type, default to neutral
            logger.warning(f"Unknown interaction type: {interaction_type}, using default label 0.3")
            return 0.3

    async def get_training_data(
        self,
        min_interactions: int = 10,
        lookback_days: int = 90
    ) -> list:
        """
        Retrieve training data for model training.

        Args:
            min_interactions: Minimum interactions per recommendation to include
            lookback_days: How many days back to look for interactions

        Returns:
            List of training examples with features and labels
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

            # Aggregate interactions to get training examples
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "user_id": "$user_id",
                            "recommendation_id": "$recommendation_id"
                        },
                        "interactions": {"$push": "$$ROOT"},
                        "max_label": {"$max": "$label"},
                        "avg_label": {"$avg": "$label"},
                        "interaction_count": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "interaction_count": {"$gte": 1}  # At least 1 interaction
                    }
                }
            ]

            results = await self.interactions_collection.aggregate(pipeline).to_list(length=None)

            logger.info(f"Retrieved {len(results)} training examples from interactions")

            return results

        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            return []

    async def get_user_interaction_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user's interaction history for personalization.

        Args:
            user_id: User ID
            limit: Maximum number of interactions to return

        Returns:
            Dictionary with interaction statistics and history
        """
        try:
            # Get recent interactions
            interactions = await self.interactions_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)

            # Compute statistics
            total_interactions = len(interactions)

            if total_interactions == 0:
                return {
                    "total_interactions": 0,
                    "preferences": {},
                    "recent_interactions": []
                }

            # Count by type
            type_counts = {}
            category_preferences = {}
            provider_preferences = {}

            for interaction in interactions:
                itype = interaction.get('interaction_type', 'unknown')
                type_counts[itype] = type_counts.get(itype, 0) + 1

                # Extract category/provider from context if available
                context = interaction.get('context', {})
                category = context.get('category')
                if category:
                    category_preferences[category] = category_preferences.get(category, 0) + 1

                provider = context.get('cloud_provider')
                if provider:
                    provider_preferences[provider] = provider_preferences.get(provider, 0) + 1

            # Calculate average label (indicates overall preference strength)
            avg_label = sum(i.get('label', 0) for i in interactions) / total_interactions

            # Implementation rate (% of recommendations that got implemented)
            implementation_count = type_counts.get('implement', 0) + type_counts.get('implemented', 0)
            implementation_rate = implementation_count / total_interactions if total_interactions > 0 else 0

            return {
                "total_interactions": total_interactions,
                "type_counts": type_counts,
                "category_preferences": category_preferences,
                "provider_preferences": provider_preferences,
                "avg_engagement": avg_label,
                "implementation_rate": implementation_rate,
                "recent_interactions": interactions[:10]  # Last 10
            }

        except Exception as e:
            logger.error(f"Failed to get user interaction history: {e}")
            return {"total_interactions": 0, "preferences": {}, "recent_interactions": []}

    async def get_recommendation_stats(
        self,
        recommendation_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific recommendation.

        Args:
            recommendation_id: Recommendation ID

        Returns:
            Dictionary with interaction statistics
        """
        try:
            interactions = await self.interactions_collection.find(
                {"recommendation_id": recommendation_id}
            ).to_list(length=None)

            if not interactions:
                return {
                    "total_interactions": 0,
                    "avg_label": 0.0,
                    "implementation_count": 0
                }

            total = len(interactions)
            avg_label = sum(i.get('label', 0) for i in interactions) / total

            implementation_count = sum(
                1 for i in interactions
                if i.get('interaction_type', '').lower() in ['implement', 'implemented']
            )

            click_count = sum(
                1 for i in interactions
                if i.get('interaction_type', '').lower() == 'click'
            )

            view_count = sum(
                1 for i in interactions
                if i.get('interaction_type', '').lower() == 'view'
            )

            # Click-through rate (clicks / views)
            ctr = click_count / view_count if view_count > 0 else 0

            # Implementation rate (implementations / clicks)
            impl_rate = implementation_count / click_count if click_count > 0 else 0

            return {
                "total_interactions": total,
                "avg_label": avg_label,
                "implementation_count": implementation_count,
                "click_count": click_count,
                "view_count": view_count,
                "click_through_rate": ctr,
                "implementation_rate": impl_rate
            }

        except Exception as e:
            logger.error(f"Failed to get recommendation stats: {e}")
            return {"total_interactions": 0}


# Helper function to get collector instance
_collector_instance = None

async def get_training_data_collector(db):
    """Get or create training data collector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = TrainingDataCollector(db)
    return _collector_instance
