"""
Assessment Context Cache for Chatbot.

Caches assessment data to avoid expensive database queries on every message.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.cache import get_cache_manager

logger = logging.getLogger(__name__)


class AssessmentContextCache:
    """
    Caches assessment context data for chatbot conversations.

    Dramatically reduces database load by caching comprehensive assessment
    data including recommendations, analytics, and quality metrics.
    """

    def __init__(self, cache_ttl: int = 600):
        """
        Initialize assessment context cache.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 10 minutes)
        """
        self.cache_ttl = cache_ttl
        self.cache_key_prefix = "chatbot:assessment_context:"

    def _get_cache_key(self, assessment_id: str) -> str:
        """Get cache key for assessment."""
        return f"{self.cache_key_prefix}{assessment_id}"

    def _safe_float_convert(self, value: Any) -> float:
        """Safely convert value to float, handling None, 'None', and invalid strings."""
        if value is None or value == 'None' or value == '':
            return 0.0

        try:
            # Handle string values with $ and commas
            if isinstance(value, str):
                cleaned = value.replace('$', '').replace(',', '').strip()
                if cleaned.lower() == 'none' or cleaned == '':
                    return 0.0
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    async def get_assessment_context(
        self,
        assessment_id: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached assessment context or load from database.

        Args:
            assessment_id: Assessment ID
            force_refresh: Force refresh from database

        Returns:
            Assessment context dictionary or None if not found
        """
        try:
            # Try to get cache manager (may be None if not initialized)
            cache_manager = await get_cache_manager()
            cache_key = self._get_cache_key(assessment_id)

            # Try to get from cache first (if cache manager is available)
            if cache_manager and not force_refresh:
                try:
                    cached_context = await cache_manager.get(cache_key)
                    if cached_context:
                        logger.debug(f"Retrieved assessment context from cache: {assessment_id}")
                        return cached_context
                except Exception as cache_error:
                    logger.warning(f"Cache retrieval failed, loading from DB: {cache_error}")

            # Load from database
            logger.debug(f"Loading assessment context from database: {assessment_id}")
            context = await self._load_assessment_context_from_db(assessment_id)

            # Try to cache the context (if cache manager is available)
            if context and cache_manager:
                try:
                    await cache_manager.set(cache_key, context, ttl=self.cache_ttl)
                    logger.info(f"Cached assessment context: {assessment_id}")
                except Exception as cache_error:
                    logger.warning(f"Failed to cache context: {cache_error}")

            return context

        except Exception as e:
            import traceback
            logger.error(f"Failed to get assessment context: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _load_assessment_context_from_db(
        self,
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load comprehensive assessment context from database.

        Args:
            assessment_id: Assessment ID

        Returns:
            Comprehensive assessment context
        """
        try:
            from ..models.assessment import Assessment
            from ..core.database import get_database

            # Get assessment
            assessment = await Assessment.get(assessment_id)
            if not assessment:
                return None

            db = await get_database()

            # Get recommendations (as raw dicts to avoid validation issues)
            recommendations_collection = db.get_collection("recommendations")
            recommendations = await recommendations_collection.find(
                {"assessment_id": str(assessment.id)}
            ).to_list(length=None)

            # Normalize provider names
            for rec in recommendations:
                if 'recommended_services' in rec:
                    for service in rec['recommended_services']:
                        if 'provider' in service and isinstance(service['provider'], str):
                            service['provider'] = service['provider'].lower()

            # Get advanced analytics
            analytics_collection = db.get_collection("advanced_analytics")
            advanced_analytics = await analytics_collection.find_one(
                {"assessment_id": str(assessment.id)}
            )

            # Get quality metrics
            quality_collection = db.get_collection("quality_metrics")
            quality_metrics = await quality_collection.find_one(
                {"assessment_id": str(assessment.id)}
            )

            # Get reports (using raw collection to avoid validation errors)
            reports_collection = db.get_collection("reports")
            reports_raw = await reports_collection.find(
                {"assessment_id": str(assessment.id)}
            ).to_list(length=None)

            # Extract just the report types we need
            reports = []
            for report in reports_raw:
                reports.append({
                    "report_type": report.get("report_type", "unknown"),
                    "title": report.get("title", ""),
                    "id": str(report.get("_id", ""))
                })

            # Build comprehensive context (same structure as chat.py but cached)
            # Handle both dict and object formats for requirements
            biz_reqs = assessment.business_requirements if hasattr(assessment, 'business_requirements') else {}
            if isinstance(biz_reqs, dict):
                business_reqs_dict = biz_reqs
            else:
                business_reqs_dict = {
                    "company_name": getattr(biz_reqs, 'company_name', None),
                    "industry": getattr(biz_reqs, 'industry', None),
                    "company_size": getattr(biz_reqs, 'company_size', None),
                    "business_goals": getattr(biz_reqs, 'business_goals', []),
                    "budget_range": getattr(biz_reqs, 'budget_range', None),
                    "timeline": getattr(biz_reqs, 'timeline', None)
                }

            tech_reqs = assessment.technical_requirements if hasattr(assessment, 'technical_requirements') else {}
            if isinstance(tech_reqs, dict):
                technical_reqs_dict = tech_reqs
            else:
                technical_reqs_dict = {
                    "workload_types": getattr(tech_reqs, 'workload_types', []),
                    "cloud_preference": getattr(tech_reqs, 'cloud_preference', None),
                    "scalability_requirements": getattr(tech_reqs, 'scalability_requirements', {}),
                    "performance_requirements": getattr(tech_reqs, 'performance_requirements', {})
                }

            context = {
                "id": str(assessment.id),
                "title": assessment.title,
                "status": str(assessment.status),
                "completion_percentage": assessment.completion_percentage,
                "business_requirements": business_reqs_dict,
                "technical_requirements": technical_reqs_dict,
                "recommendations": {
                    "count": len(recommendations),
                    "summary": [
                        {
                            "title": rec.get("title"),
                            "category": rec.get("category"),
                            "confidence_score": rec.get("confidence_score"),
                            "benefits": rec.get("benefits", []),
                            "risks": rec.get("risks", rec.get("risks_and_considerations", [])),
                            "implementation_steps": rec.get("implementation_steps", []),
                            "cloud_provider": rec.get("cloud_provider"),
                            "estimated_cost": rec.get("total_estimated_monthly_cost"),
                            "business_impact": rec.get("business_impact")
                        }
                        for rec in recommendations[:10]  # Limit to top 10
                    ]
                },
                "analytics": {
                    "cost_analysis": advanced_analytics.get("cost_analysis") if advanced_analytics else None,
                    "performance_analysis": advanced_analytics.get("performance_analysis") if advanced_analytics else None,
                    "risk_assessment": advanced_analytics.get("risk_assessment") if advanced_analytics else None,
                    "optimization_opportunities": advanced_analytics.get("optimization_opportunities", []) if advanced_analytics else []
                },
                "quality_metrics": {
                    "overall_score": quality_metrics.get("value") if quality_metrics else None,
                    "completeness": quality_metrics.get("details", {}).get("completeness") if quality_metrics else None,
                    "accuracy": quality_metrics.get("details", {}).get("accuracy") if quality_metrics else None,
                    "confidence": quality_metrics.get("details", {}).get("confidence") if quality_metrics else None
                },
                "reports": {
                    "count": len(reports),
                    "available_types": [report.get("report_type", "unknown") for report in reports]
                },
                "agents_involved": list(set([rec.get("agent_name") for rec in recommendations if rec.get("agent_name")])),
                "decision_factors": {
                    "total_estimated_cost": sum([
                        self._safe_float_convert(rec.get("total_estimated_monthly_cost"))
                        for rec in recommendations
                    ]) if recommendations else 0,
                    "average_confidence": sum([rec.get("confidence_score", 0) for rec in recommendations]) / len(recommendations) if recommendations else 0,
                    "high_priority_items": len([rec for rec in recommendations if rec.get("priority") == "high"]),
                    "implementation_complexity": [rec.get("implementation_effort") for rec in recommendations if rec.get("implementation_effort")]
                },
                "_cached_at": datetime.utcnow().isoformat()
            }

            return context

        except Exception as e:
            import traceback
            logger.error(f"Failed to load assessment context from DB: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def invalidate_assessment_context(self, assessment_id: str) -> bool:
        """
        Invalidate cached assessment context.

        Args:
            assessment_id: Assessment ID

        Returns:
            True if invalidated successfully
        """
        try:
            cache_manager = await get_cache_manager()
            cache_key = self._get_cache_key(assessment_id)

            await cache_manager.delete(cache_key)
            logger.info(f"Invalidated assessment context cache: {assessment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate assessment context: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_manager = await get_cache_manager()

            # Get all cache keys for assessments
            # Note: This is a simplified version - production should use Redis SCAN
            return {
                "cache_ttl": self.cache_ttl,
                "cache_key_prefix": self.cache_key_prefix
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Global instance
_assessment_context_cache: Optional[AssessmentContextCache] = None


def get_assessment_context_cache() -> AssessmentContextCache:
    """Get or create global assessment context cache instance."""
    global _assessment_context_cache

    if _assessment_context_cache is None:
        _assessment_context_cache = AssessmentContextCache()
        logger.info("Initialized assessment context cache")

    return _assessment_context_cache
