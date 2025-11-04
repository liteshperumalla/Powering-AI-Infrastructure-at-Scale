"""
Recommendation Diversity using Maximal Marginal Relevance (MMR).

Ensures recommendation diversity to avoid redundancy and improve user experience.
"""

import logging
from typing import List, Tuple, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class RecommendationDiversifier:
    """
    Ensure recommendation diversity using Maximal Marginal Relevance (MMR).

    MMR balances relevance and diversity:
    MMR = λ * Relevance(rec) - (1-λ) * max Similarity(rec, selected)
    """

    @staticmethod
    def diversify_recommendations(
        ranked_recommendations: List[Tuple[Dict[str, Any], float]],
        lambda_param: float = 0.7,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Apply MMR to select diverse top-K recommendations.

        Args:
            ranked_recommendations: List of (recommendation, relevance_score) tuples
            lambda_param: Trade-off between relevance and diversity (0-1)
                         0 = max diversity, 1 = max relevance
            top_k: Number of recommendations to return

        Returns:
            Diverse list of top-K recommendations
        """
        if not ranked_recommendations:
            return []

        if len(ranked_recommendations) <= top_k:
            # Not enough recommendations to diversify
            return [rec for rec, _ in ranked_recommendations]

        selected = []
        remaining = list(ranked_recommendations)

        # Step 1: Select the most relevant recommendation first
        first_rec, first_score = remaining.pop(0)
        selected.append((first_rec, first_score))

        logger.debug(f"MMR: Selected first recommendation (highest relevance): {first_rec.get('title', 'Unknown')}")

        # Step 2: Iteratively select recommendations with highest MMR score
        iteration = 1
        while len(selected) < top_k and remaining:
            mmr_scores = []

            for rec, relevance in remaining:
                # Calculate max similarity to already selected recommendations
                max_similarity = max([
                    RecommendationDiversifier._calculate_similarity(rec, sel_rec)
                    for sel_rec, _ in selected
                ])

                # MMR formula
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                mmr_scores.append((rec, relevance, mmr_score))

            # Select recommendation with highest MMR score
            best_rec, best_relevance, best_mmr = max(mmr_scores, key=lambda x: x[2])
            selected.append((best_rec, best_relevance))

            # Remove from remaining
            remaining = [
                (r, s) for r, s in remaining
                if r.get('_id') != best_rec.get('_id') or r.get('id') != best_rec.get('id')
            ]

            logger.debug(
                f"MMR iteration {iteration}: Selected '{best_rec.get('title', 'Unknown')}' "
                f"(relevance={best_relevance:.3f}, MMR={best_mmr:.3f})"
            )
            iteration += 1

        # Return only the recommendations (without scores)
        result = [rec for rec, _ in selected]

        logger.info(
            f"MMR diversification complete: selected {len(result)} from {len(ranked_recommendations)} "
            f"recommendations (lambda={lambda_param})"
        )

        return result

    @staticmethod
    def _calculate_similarity(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two recommendations.

        Uses weighted similarity across multiple dimensions:
        - Category similarity (40%)
        - Cloud provider similarity (20%)
        - Cost similarity (20%)
        - Implementation complexity similarity (20%)

        Args:
            rec1: First recommendation
            rec2: Second recommendation

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        similarity = 0.0

        # 1. Category similarity (40% weight)
        cat1 = str(rec1.get('category', '')).lower()
        cat2 = str(rec2.get('category', '')).lower()

        if cat1 == cat2:
            similarity += 0.4
        elif RecommendationDiversifier._categories_related(cat1, cat2):
            similarity += 0.2  # Partial match for related categories

        # 2. Cloud provider similarity (20% weight)
        provider1 = str(rec1.get('cloud_provider', '')).lower()
        provider2 = str(rec2.get('cloud_provider', '')).lower()

        if provider1 and provider2 and provider1 == provider2:
            similarity += 0.2
        elif not provider1 or not provider2:
            similarity += 0.05  # Slight penalty for missing provider

        # 3. Cost similarity (20% weight)
        cost1 = float(rec1.get('estimated_cost', 0) or 0)
        cost2 = float(rec2.get('estimated_cost', 0) or 0)

        if cost1 > 0 and cost2 > 0:
            # Calculate relative cost difference
            max_cost = max(cost1, cost2)
            min_cost = min(cost1, cost2)
            cost_ratio = min_cost / max_cost if max_cost > 0 else 0

            # Similar costs (within 2x) = high similarity
            if cost_ratio > 0.5:
                similarity += 0.2 * cost_ratio
            else:
                similarity += 0.05  # Very different costs = low similarity
        elif cost1 == 0 and cost2 == 0:
            similarity += 0.1  # Both have no cost info

        # 4. Implementation complexity similarity (20% weight)
        complexity_map = {'low': 0, 'medium': 1, 'high': 2}
        comp1 = complexity_map.get(str(rec1.get('implementation_effort', 'medium')).lower(), 1)
        comp2 = complexity_map.get(str(rec2.get('implementation_effort', 'medium')).lower(), 1)

        comp_diff = abs(comp1 - comp2)
        if comp_diff == 0:
            similarity += 0.2
        elif comp_diff == 1:
            similarity += 0.1
        else:
            similarity += 0.0

        return min(similarity, 1.0)  # Ensure max is 1.0

    @staticmethod
    def _categories_related(cat1: str, cat2: str) -> bool:
        """
        Check if two categories are related.

        Args:
            cat1: First category
            cat2: Second category

        Returns:
            True if categories are related
        """
        # Define related category groups
        related_groups = [
            {'cost', 'optimization', 'cost_optimization', 'budget'},
            {'security', 'compliance', 'governance'},
            {'performance', 'scalability', 'availability'},
            {'infrastructure', 'architecture', 'design'},
            {'ai', 'ml', 'machine_learning', 'artificial_intelligence'},
            {'database', 'storage', 'data'},
            {'networking', 'network', 'connectivity'}
        ]

        for group in related_groups:
            if cat1 in group and cat2 in group:
                return True

        return False

    @staticmethod
    def calculate_diversity_score(recommendations: List[Dict[str, Any]]) -> float:
        """
        Calculate diversity score for a set of recommendations.

        Uses Simpson's Diversity Index:
        D = 1 - Σ(p_i)^2

        where p_i is the proportion of recommendations in category i.

        Args:
            recommendations: List of recommendations

        Returns:
            Diversity score (0-1, higher = more diverse)
        """
        if not recommendations or len(recommendations) <= 1:
            return 0.0

        # Count by category
        category_counts = {}
        for rec in recommendations:
            category = str(rec.get('category', 'unknown')).lower()
            category_counts[category] = category_counts.get(category, 0) + 1

        # Calculate Simpson's Diversity Index
        n = len(recommendations)
        simpson_sum = sum((count / n) ** 2 for count in category_counts.values())
        diversity = 1 - simpson_sum

        logger.debug(f"Diversity score: {diversity:.3f} for {len(recommendations)} recommendations across {len(category_counts)} categories")

        return diversity

    @staticmethod
    def rerank_with_diversity(
        recommendations: List[Dict[str, Any]],
        scores: List[float],
        diversity_weight: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Re-rank recommendations balancing relevance and diversity.

        Args:
            recommendations: List of recommendations
            scores: List of relevance scores (parallel to recommendations)
            diversity_weight: Weight for diversity (0-1)

        Returns:
            List of (recommendation, adjusted_score) tuples, sorted by adjusted score
        """
        if len(recommendations) != len(scores):
            logger.error("Recommendations and scores must have same length")
            return list(zip(recommendations, scores))

        # Pair recommendations with scores
        rec_score_pairs = list(zip(recommendations, scores))

        # Sort by relevance first
        rec_score_pairs.sort(key=lambda x: x[1], reverse=True)

        # Apply MMR with diversity weight
        relevance_weight = 1.0 - diversity_weight
        diversified = RecommendationDiversifier.diversify_recommendations(
            rec_score_pairs,
            lambda_param=relevance_weight,
            top_k=len(recommendations)
        )

        # Create new scores that reflect diversity-adjusted ranking
        adjusted_pairs = []
        for idx, rec in enumerate(diversified):
            # Score decreases with rank, but preserves relative ordering
            original_score = next((s for r, s in rec_score_pairs if r.get('_id') == rec.get('_id')), 0)
            position_penalty = idx * 0.01  # Small penalty for lower positions
            adjusted_score = original_score - position_penalty
            adjusted_pairs.append((rec, adjusted_score))

        return adjusted_pairs
