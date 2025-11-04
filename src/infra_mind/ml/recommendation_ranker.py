"""
LightGBM-based Learning-to-Rank Model for Recommendations.

Uses LambdaRank objective to train a ranking model that predicts
recommendation relevance based on user interactions.
"""

import logging
import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional: LightGBM import (will use fallback if not available)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not installed. Using fallback ranking.")
    LIGHTGBM_AVAILABLE = False


class RecommendationRanker:
    """
    LightGBM-based Learning-to-Rank model for recommendations.

    Uses LambdaRank objective optimized for NDCG@K.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize recommendation ranker.

        Args:
            model_path: Path to saved model file (optional)
        """
        self.model = None
        self.model_path = model_path or "models/recommendation_ranker.txt"
        self.feature_importance = None

        # Try to load existing model
        if os.path.exists(self.model_path) and LIGHTGBM_AVAILABLE:
            try:
                self.load_model()
                logger.info(f"Loaded existing model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

    async def train(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2,
        num_boost_round: int = 500
    ) -> Dict[str, Any]:
        """
        Train LambdaRank model on historical interaction data.

        Args:
            training_data: List of training examples with features and labels
            validation_split: Fraction of data to use for validation
            num_boost_round: Number of boosting rounds

        Returns:
            Training metrics (NDCG, etc.)
        """
        if not LIGHTGBM_AVAILABLE:
            logger.warning("LightGBM not available. Skipping training.")
            return {"error": "LightGBM not installed"}

        try:
            from .recommendation_features import RecommendationFeatureStore

            # Prepare feature matrix and labels
            X = []
            y = []
            groups = []  # For group-wise ranking (assessments)

            current_assessment = None
            group_size = 0

            for example in training_data:
                # Extract features
                rec = example.get('recommendation', {})
                assessment = example.get('assessment', {})
                user_profile = example.get('user_profile')
                historical = example.get('historical_data', {})

                features = RecommendationFeatureStore.extract_features(
                    rec, assessment, user_profile, historical
                )

                X.append(features)
                y.append(example.get('label', 0.0))

                # Track groups (recommendations for same assessment)
                assessment_id = example.get('assessment_id')
                if current_assessment != assessment_id:
                    if group_size > 0:
                        groups.append(group_size)
                    current_assessment = assessment_id
                    group_size = 1
                else:
                    group_size += 1

            # Add last group
            if group_size > 0:
                groups.append(group_size)

            X = np.array(X)
            y = np.array(y)

            logger.info(f"Training data: {len(X)} examples, {len(groups)} groups")

            # Split into train/validation
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Adjust groups for split
            groups_train = groups[:int(len(groups) * (1 - validation_split))]
            groups_val = groups[int(len(groups) * (1 - validation_split)):]

            # Create LightGBM datasets
            train_data = lgb.Dataset(X_train, label=y_train, group=groups_train)
            val_data = lgb.Dataset(X_val, label=y_val, group=groups_val, reference=train_data)

            # LambdaRank parameters
            params = {
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [5, 10, 20],
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': 0,
                'seed': 42
            }

            # Train model
            logger.info("Starting LightGBM training...")
            evals_result = {}
            self.model = lgb.train(
                params,
                train_data,
                valid_sets=[train_data, val_data],
                valid_names=['train', 'valid'],
                num_boost_round=num_boost_round,
                callbacks=[
                    lgb.early_stopping(stopping_rounds=50),
                    lgb.record_evaluation(evals_result)
                ]
            )

            # Save model
            self._save_model()

            # Get feature importance
            self.feature_importance = self.model.feature_importance(importance_type='gain')

            metrics = {
                'train_ndcg_5': evals_result['train']['ndcg@5'][-1],
                'train_ndcg_10': evals_result['train']['ndcg@10'][-1],
                'valid_ndcg_5': evals_result['valid']['ndcg@5'][-1],
                'valid_ndcg_10': evals_result['valid']['ndcg@10'][-1],
                'num_boost_rounds': self.model.num_trees(),
                'feature_importance_top10': self._get_top_features(10)
            }

            logger.info(f"Training complete. Validation NDCG@10: {metrics['valid_ndcg_10']:.4f}")

            return metrics

        except Exception as e:
            logger.error(f"Training failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    async def rank_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        assessment: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank recommendations using trained model.

        Args:
            recommendations: List of recommendations to rank
            assessment: Assessment document
            user_profile: Optional user profile

        Returns:
            List of (recommendation, score) tuples sorted by score (descending)
        """
        if not recommendations:
            return []

        try:
            from .recommendation_features import RecommendationFeatureStore

            # Extract features for each recommendation
            features = []
            for rec in recommendations:
                feat = RecommendationFeatureStore.extract_features(
                    rec, assessment, user_profile, {}
                )
                features.append(feat)

            X = np.array(features)

            # Predict scores
            if self.model and LIGHTGBM_AVAILABLE:
                scores = self.model.predict(X)
            else:
                # Fallback: use confidence scores
                logger.warning("Using fallback ranking (no trained model)")
                scores = np.array([rec.get('confidence_score', 0.5) for rec in recommendations])

            # Pair recommendations with scores and sort
            ranked = sorted(
                zip(recommendations, scores),
                key=lambda x: x[1],
                reverse=True
            )

            logger.info(f"Ranked {len(recommendations)} recommendations")

            return ranked

        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            # Fallback: return recommendations with confidence scores
            return [(rec, rec.get('confidence_score', 0.5)) for rec in recommendations]

    def _save_model(self):
        """Save model to disk."""
        if self.model and LIGHTGBM_AVAILABLE:
            try:
                # Create directory if it doesn't exist
                Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
                self.model.save_model(self.model_path)
                logger.info(f"Model saved to {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to save model: {e}")

    def load_model(self):
        """Load model from disk."""
        if LIGHTGBM_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = lgb.Booster(model_file=self.model_path)
                logger.info(f"Model loaded from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise

    def _get_top_features(self, top_k: int = 10) -> List[Tuple[str, float]]:
        """Get top K important features."""
        if self.feature_importance is None:
            return []

        from .recommendation_features import RecommendationFeatureStore
        feature_names = RecommendationFeatureStore.get_feature_names()

        if len(feature_names) != len(self.feature_importance):
            logger.warning("Feature names and importance arrays have different lengths")
            return []

        # Sort by importance
        feature_imp_pairs = list(zip(feature_names, self.feature_importance))
        feature_imp_pairs.sort(key=lambda x: x[1], reverse=True)

        return feature_imp_pairs[:top_k]

    def explain_prediction(
        self,
        recommendation: Dict[str, Any],
        assessment: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain why a recommendation was ranked high/low.

        Args:
            recommendation: Recommendation document
            assessment: Assessment document
            user_profile: Optional user profile

        Returns:
            Explanation with top contributing features
        """
        try:
            from .recommendation_features import RecommendationFeatureStore

            # Extract features
            features = RecommendationFeatureStore.extract_features(
                recommendation, assessment, user_profile, {}
            )

            # Get feature names
            feature_names = RecommendationFeatureStore.get_feature_names()

            # Get prediction
            if self.model and LIGHTGBM_AVAILABLE:
                score = self.model.predict([features])[0]
            else:
                score = recommendation.get('confidence_score', 0.5)

            # Get feature contributions (SHAP-style)
            # For now, use feature importance as proxy
            top_features = self._get_top_features(5)

            explanation = {
                "score": float(score),
                "top_contributing_features": [
                    {
                        "feature": name,
                        "importance": float(imp),
                        "value": float(features[feature_names.index(name)])
                    }
                    for name, imp in top_features
                ],
                "recommendation_id": recommendation.get('_id') or recommendation.get('id'),
                "recommendation_title": recommendation.get('title')
            }

            return explanation

        except Exception as e:
            logger.error(f"Failed to explain prediction: {e}")
            return {"error": str(e)}


# Singleton instance
_ranker_instance = None

def get_recommendation_ranker(model_path: Optional[str] = None):
    """Get or create recommendation ranker instance."""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = RecommendationRanker(model_path)
    return _ranker_instance
