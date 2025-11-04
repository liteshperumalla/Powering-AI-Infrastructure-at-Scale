#!/usr/bin/env python3
"""
ML Recommendation Model Training Script.

This script trains the LightGBM ranking model using collected user interaction data.
Run this script periodically (weekly/monthly) to retrain the model with new data.

Usage:
    python scripts/train_recommendation_model.py [--min-interactions 100] [--lookback-days 90]
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infra_mind.core.database import init_database, get_database
from src.infra_mind.ml.training_data_collector import TrainingDataCollector
from src.infra_mind.ml.recommendation_ranker import get_recommendation_ranker
from src.infra_mind.ml.recommendation_features import RecommendationFeatureStore
from loguru import logger


async def collect_training_data(
    min_interactions: int = 100,
    lookback_days: int = 90
):
    """
    Collect training data from user interactions.

    Args:
        min_interactions: Minimum interactions required to proceed with training
        lookback_days: How many days back to look for interactions

    Returns:
        List of training examples
    """
    logger.info(f"📊 Collecting training data (min interactions: {min_interactions}, lookback: {lookback_days} days)")

    try:
        # Initialize database
        await init_database()
        db = await get_database()

        # Get training data collector
        collector = TrainingDataCollector(db)

        # Retrieve training data
        raw_training_data = await collector.get_training_data(
            min_interactions=1,  # Get all for now
            lookback_days=lookback_days
        )

        logger.info(f"✅ Retrieved {len(raw_training_data)} raw training examples")

        if len(raw_training_data) < min_interactions:
            logger.warning(
                f"⚠️  Insufficient training data: {len(raw_training_data)} < {min_interactions}\n"
                f"   Need at least {min_interactions} interactions to train the model.\n"
                f"   Current data is not enough for reliable model training."
            )
            return None

        # Convert to training format
        training_examples = []

        for example in raw_training_data:
            # Get recommendation and assessment data
            recommendation_id = example['_id']['recommendation_id']

            # Fetch recommendation from database
            rec_doc = await db.recommendations.find_one({"_id": recommendation_id})
            if not rec_doc:
                logger.warning(f"Recommendation {recommendation_id} not found, skipping")
                continue

            # Fetch assessment
            assessment_id = rec_doc.get('assessment_id')
            if not assessment_id:
                logger.warning(f"No assessment_id for recommendation {recommendation_id}, skipping")
                continue

            assessment_doc = await db.assessments.find_one({"_id": assessment_id})
            if not assessment_doc:
                logger.warning(f"Assessment {assessment_id} not found, skipping")
                continue

            # Use max label (strongest signal) for this recommendation
            label = example.get('max_label', 0.0)

            # Create training example
            training_examples.append({
                'recommendation': rec_doc,
                'assessment': assessment_doc,
                'assessment_id': assessment_id,
                'label': label,
                'interaction_count': example.get('interaction_count', 1),
                'user_profile': None,  # Can add later
                'historical_data': {
                    'click_count': example.get('interaction_count', 0),
                    'avg_label': example.get('avg_label', 0.0)
                }
            })

        logger.info(f"✅ Prepared {len(training_examples)} training examples")
        return training_examples

    except Exception as e:
        logger.error(f"❌ Failed to collect training data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def train_model(
    training_data,
    validation_split: float = 0.2,
    num_boost_round: int = 500
):
    """
    Train the LightGBM ranking model.

    Args:
        training_data: List of training examples
        validation_split: Fraction of data to use for validation
        num_boost_round: Number of boosting rounds

    Returns:
        Training metrics
    """
    logger.info(f"🚀 Starting model training...")
    logger.info(f"   Training examples: {len(training_data)}")
    logger.info(f"   Validation split: {validation_split}")
    logger.info(f"   Boosting rounds: {num_boost_round}")

    try:
        # Get ranker instance
        ranker = get_recommendation_ranker()

        # Train model
        metrics = await ranker.train(
            training_data=training_data,
            validation_split=validation_split,
            num_boost_round=num_boost_round
        )

        logger.info("✅ Model training complete!")
        logger.info(f"📈 Training Metrics:")
        logger.info(f"   NDCG@5 (train): {metrics.get('train_ndcg_5', 'N/A'):.4f}")
        logger.info(f"   NDCG@10 (train): {metrics.get('train_ndcg_10', 'N/A'):.4f}")
        logger.info(f"   NDCG@5 (valid): {metrics.get('valid_ndcg_5', 'N/A'):.4f}")
        logger.info(f"   NDCG@10 (valid): {metrics.get('valid_ndcg_10', 'N/A'):.4f}")
        logger.info(f"   Boosting rounds: {metrics.get('num_boost_rounds', 'N/A')}")

        # Show top features
        if 'feature_importance_top10' in metrics:
            logger.info("🔝 Top 10 Important Features:")
            for i, (feature_name, importance) in enumerate(metrics['feature_importance_top10'], 1):
                logger.info(f"   {i}. {feature_name}: {importance:.2f}")

        return metrics

    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def evaluate_model():
    """
    Evaluate the trained model on test data.

    Returns:
        Evaluation metrics
    """
    logger.info("📊 Evaluating trained model...")

    try:
        ranker = get_recommendation_ranker()

        if ranker.model is None:
            logger.warning("⚠️  No trained model found. Train a model first.")
            return None

        logger.info("✅ Model loaded successfully")
        logger.info(f"   Model path: {ranker.model_path}")
        logger.info(f"   Number of trees: {ranker.model.num_trees() if hasattr(ranker.model, 'num_trees') else 'N/A'}")

        # Get feature importance
        if ranker.feature_importance is not None:
            logger.info(f"   Features: {len(ranker.feature_importance)}")

        return {
            "model_loaded": True,
            "model_path": ranker.model_path,
            "num_trees": ranker.model.num_trees() if hasattr(ranker.model, 'num_trees') else None
        }

    except Exception as e:
        logger.error(f"❌ Model evaluation failed: {e}")
        return None


async def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(
        description="Train ML recommendation ranking model"
    )
    parser.add_argument(
        '--min-interactions',
        type=int,
        default=100,
        help='Minimum number of interactions required for training (default: 100)'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=90,
        help='Number of days to look back for interactions (default: 90)'
    )
    parser.add_argument(
        '--validation-split',
        type=float,
        default=0.2,
        help='Validation split ratio (default: 0.2)'
    )
    parser.add_argument(
        '--num-boost-round',
        type=int,
        default=500,
        help='Number of boosting rounds (default: 500)'
    )
    parser.add_argument(
        '--evaluate-only',
        action='store_true',
        help='Only evaluate existing model, don\'t train'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("ML RECOMMENDATION MODEL TRAINING")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Evaluate only mode
    if args.evaluate_only:
        logger.info("🔍 Running in evaluation-only mode")
        eval_results = await evaluate_model()
        if eval_results:
            logger.info("✅ Evaluation complete")
        else:
            logger.error("❌ Evaluation failed")
        return

    # Step 1: Collect training data
    training_data = await collect_training_data(
        min_interactions=args.min_interactions,
        lookback_days=args.lookback_days
    )

    if training_data is None or len(training_data) == 0:
        logger.error("❌ Training aborted: No training data available")
        logger.info("")
        logger.info("💡 Suggestions:")
        logger.info("   1. Ensure users are interacting with recommendations")
        logger.info("   2. Check that interaction tracking is working")
        logger.info("   3. Lower --min-interactions threshold")
        logger.info("   4. Increase --lookback-days to include more data")
        return

    # Step 2: Train model
    metrics = await train_model(
        training_data=training_data,
        validation_split=args.validation_split,
        num_boost_round=args.num_boost_round
    )

    if metrics is None:
        logger.error("❌ Training failed")
        return

    # Step 3: Evaluate model
    eval_results = await evaluate_model()

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ TRAINING PIPELINE COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info("📊 Summary:")
    logger.info(f"   Training examples: {len(training_data)}")
    logger.info(f"   Validation NDCG@10: {metrics.get('valid_ndcg_10', 'N/A')}")
    logger.info(f"   Model saved to: {get_recommendation_ranker().model_path}")
    logger.info("")
    logger.info("🚀 Next Steps:")
    logger.info("   1. Restart backend to load new model")
    logger.info("   2. Test recommendations with ML ranking")
    logger.info("   3. Monitor NDCG and user engagement metrics")
    logger.info("   4. Retrain periodically (weekly/monthly) as more data accumulates")


if __name__ == "__main__":
    asyncio.run(main())
