"""
Unified Additional Features API Endpoints.

Provides all additional features for assessments:
- Performance Monitoring
- Compliance
- Experiments
- Quality Metrics
- Approval Workflows
- Budget Forecasting
- Executive Dashboard
- Impact Analysis
- Rollback Plans
- Vendor Lock-in Analysis
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId

from ...models.assessment import Assessment
from ...models.recommendation import Recommendation
from ...models.user import User
from ...core.database import get_database
from ..auth import get_current_user
from ...services.features_generator import (
    generate_performance_monitoring,
    generate_compliance_dashboard,
    generate_experiments,
    generate_quality_metrics,
    generate_approval_workflows,
    generate_budget_forecast,
    generate_executive_dashboard,
    generate_impact_analysis,
    generate_rollback_plans,
    generate_vendor_lockin_analysis
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assessment-features"])


async def get_normalized_recommendations(assessment_id: str) -> List[Dict[str, Any]]:
    """Get recommendations with normalized provider fields."""
    db = await get_database()
    recommendations_raw = await db.recommendations.find({"assessment_id": assessment_id}).to_list(length=None)

    # Normalize provider fields to lowercase
    recommendations = []
    for rec in recommendations_raw:
        if 'recommended_services' in rec:
            for service in rec['recommended_services']:
                if 'provider' in service and isinstance(service['provider'], str):
                    service['provider'] = service['provider'].lower()
        recommendations.append(rec)

    return recommendations


@router.get("/assessment/{assessment_id}/performance")
async def get_performance_monitoring(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get performance monitoring data for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)
        data = await generate_performance_monitoring(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/compliance")
async def get_compliance_dashboard(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get compliance dashboard for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        data = await generate_compliance_dashboard(assessment)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/experiments")
async def get_experiments(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get experiments for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        data = await generate_experiments(assessment)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/quality")
async def get_quality_metrics(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get quality metrics for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_quality_metrics(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/approvals")
async def get_approval_workflows(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get approval workflows for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_approval_workflows(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get approval workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/budget")
async def get_budget_forecast(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get budget forecast for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_budget_forecast(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get budget forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/executive")
async def get_executive_dashboard(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get executive dashboard for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        # Get analytics if available
        db = await get_database()
        analytics_collection = db.get_collection("advanced_analytics")
        analytics = await analytics_collection.find_one({"assessment_id": assessment_id})

        data = await generate_executive_dashboard(assessment, recommendations, analytics)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get executive dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/impact")
async def get_impact_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get impact analysis for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_impact_analysis(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/rollback")
async def get_rollback_plans(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get rollback plans for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_rollback_plans(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rollback plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/vendor-lockin")
async def get_vendor_lockin_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get vendor lock-in analysis for an assessment."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        data = await generate_vendor_lockin_analysis(assessment, recommendations)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vendor lock-in analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{assessment_id}/all-features")
async def get_all_features(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all additional features for an assessment in one call."""
    try:
        assessment = await Assessment.get(ObjectId(assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if str(assessment.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        recommendations = await get_normalized_recommendations(assessment_id)

        # Get analytics
        db = await get_database()
        analytics_collection = db.get_collection("advanced_analytics")
        analytics = await analytics_collection.find_one({"assessment_id": assessment_id})

        # Generate all features
        return {
            "assessment_id": assessment_id,
            "performance": await generate_performance_monitoring(assessment, recommendations),
            "compliance": await generate_compliance_dashboard(assessment),
            "experiments": await generate_experiments(assessment),
            "quality": await generate_quality_metrics(assessment, recommendations),
            "approvals": await generate_approval_workflows(assessment, recommendations),
            "budget": await generate_budget_forecast(assessment, recommendations),
            "executive": await generate_executive_dashboard(assessment, recommendations, analytics),
            "impact": await generate_impact_analysis(assessment, recommendations),
            "rollback": await generate_rollback_plans(assessment, recommendations),
            "vendor_lockin": await generate_vendor_lockin_analysis(assessment, recommendations),
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime
