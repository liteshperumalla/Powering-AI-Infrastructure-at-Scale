"""
Quality assurance system API endpoints with real database functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timedelta, timezone
import uuid

from .auth import get_current_user, require_enterprise_access
from ...models.user import User
from ...models.feedback import QualityMetric
from ...models.assessment import Assessment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["quality"])


# Pydantic models for request/response
class QualityMetricRequest(BaseModel):
    """Request model for submitting quality metrics."""
    target_type: str = Field(..., description="Type of target (assessment, user, system)")
    target_id: str = Field(..., description="ID of the target")
    metric_name: str = Field(..., description="Name of the quality metric")
    metric_value: float = Field(..., description="Metric value")
    metric_unit: Optional[str] = Field(None, description="Unit of measurement")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Overall quality score")


class QualityScoreResponse(BaseModel):
    """Response model for quality scores."""
    target_id: str
    target_type: str
    overall_score: float
    metrics: Dict[str, float]
    calculated_at: str


@router.post("/metrics")
async def submit_quality_metric(
    request: QualityMetricRequest,
    current_user: User = Depends(require_enterprise_access)
):
    """Submit a quality metric (admin only)."""
    try:
        # Create quality metric record
        metric = QualityMetric(
            target_type=request.target_type,
            target_id=request.target_id,
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            metric_unit=request.metric_unit,
            quality_score=request.quality_score
        )
        await metric.insert()
        
        return {
            "metric_id": str(metric.id),
            "target_type": metric.target_type,
            "target_id": metric.target_id,
            "metric_name": metric.metric_name,
            "metric_value": metric.metric_value,
            "quality_score": metric.quality_score,
            "recorded_at": metric.measured_at.isoformat(),
            "message": "Quality metric recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit quality metric: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit quality metric: {str(e)}"
        )


@router.get("/metrics")
async def get_all_quality_metrics(
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    current_user: User = Depends(require_enterprise_access)
):
    """Get all quality metrics (admin only)."""
    try:
        # Build query
        query = {}
        if target_type:
            query["target_type"] = target_type
        if metric_name:
            query["metric_name"] = metric_name

        # Get metrics
        metrics = await QualityMetric.find(query).sort(-QualityMetric.measured_at).limit(limit).to_list()

        return [
            {
                "id": str(metric.id),
                "target_type": metric.target_type,
                "target_id": metric.target_id,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "quality_score": metric.quality_score,
                "created_at": metric.measured_at.isoformat() if metric.measured_at else None,
                "metadata": metric.metadata or {}
            }
            for metric in metrics
        ]

    except Exception as e:
        logger.error(f"Failed to get all quality metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metrics: {str(e)}"
        )


@router.get("/metrics/{target_id}")
async def get_quality_metrics(
    target_id: str,
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum results"),
    current_user: User = Depends(require_enterprise_access)
):
    """Get quality metrics for a target (admin only)."""
    try:
        # Build query
        query = {"target_id": target_id}
        if target_type:
            query["target_type"] = target_type
        if metric_name:
            query["metric_name"] = metric_name
        
        # Fetch metrics from database
        metrics = await QualityMetric.find(query).sort(-QualityMetric.measured_at).limit(limit).to_list()
        
        # Convert to response format
        result = []
        for metric in metrics:
            result.append({
                "id": str(metric.id),
                "target_type": metric.target_type,
                "target_id": metric.target_id,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "metric_unit": metric.metric_unit,
                "quality_score": metric.quality_score,
                "sub_scores": metric.sub_scores,
                "dimensions": metric.dimensions,
                "tags": metric.tags,
                "measured_at": metric.measured_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get quality metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metrics: {str(e)}"
        )


@router.get("/scores/{target_id}", response_model=QualityScoreResponse)
async def get_quality_score(
    target_id: str,
    target_type: str = Query(..., description="Type of target"),
    current_user: User = Depends(require_enterprise_access)
):
    """Get overall quality score for a target (admin only)."""
    try:
        # Get all metrics for this target
        metrics = await QualityMetric.find(
            QualityMetric.target_id == target_id,
            QualityMetric.target_type == target_type
        ).to_list()
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No quality metrics found for target")
        
        # Calculate overall score
        quality_scores = [m.quality_score for m in metrics if m.quality_score is not None]
        overall_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Create metrics summary
        metrics_summary = {}
        for metric in metrics:
            metrics_summary[metric.metric_name] = metric.metric_value
        
        return QualityScoreResponse(
            target_id=target_id,
            target_type=target_type,
            overall_score=round(overall_score, 2),
            metrics=metrics_summary,
            calculated_at=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality score: {str(e)}"
        )


@router.get("/overview")
async def get_quality_overview(
    current_user: User = Depends(require_enterprise_access)
):
    """Get quality overview dashboard (admin only)."""
    try:
        # Get total metrics count
        total_metrics = await QualityMetric.find().count()
        
        # Get recent metrics
        recent_metrics = await QualityMetric.find().sort(-QualityMetric.measured_at).limit(10).to_list()
        
        # Calculate average quality score
        all_scores = []
        for metric in recent_metrics:
            if metric.quality_score:
                all_scores.append(metric.quality_score)
        
        avg_quality_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Get metrics by target type
        target_type_stats = {}
        assessment_count = await QualityMetric.find(QualityMetric.target_type == "assessment").count()
        user_count = await QualityMetric.find(QualityMetric.target_type == "user").count()
        system_count = await QualityMetric.find(QualityMetric.target_type == "system").count()
        
        target_type_stats = {
            "assessment": assessment_count,
            "user": user_count,
            "system": system_count
        }
        
        # Get alerts (metrics below threshold)
        alerts = []
        for metric in recent_metrics:
            if metric.quality_score and metric.quality_score < 70:  # Below 70% threshold
                alerts.append({
                    "id": str(metric.id),
                    "target_type": metric.target_type,
                    "target_id": metric.target_id,
                    "metric_name": metric.metric_name,
                    "quality_score": metric.quality_score,
                    "measured_at": metric.measured_at.isoformat()
                })
        
        return {
            "total_metrics": total_metrics,
            "avg_quality_score": round(avg_quality_score, 2),
            "target_type_distribution": target_type_stats,
            "recent_metrics": [
                {
                    "id": str(m.id),
                    "target_type": m.target_type,
                    "target_id": m.target_id,
                    "metric_name": m.metric_name,
                    "quality_score": m.quality_score,
                    "measured_at": m.measured_at.isoformat()
                }
                for m in recent_metrics[:5]
            ],
            "alerts": alerts,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality overview: {str(e)}"
        )


@router.get("/trends")
async def get_quality_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    current_user: User = Depends(require_enterprise_access)
):
    """Get quality trends over time (admin only)."""
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = {
            "measured_at": {"$gte": start_date, "$lte": end_date}
        }
        if target_type:
            query["target_type"] = target_type
        
        # Get metrics within period
        period_metrics = await QualityMetric.find(query).sort(QualityMetric.measured_at).to_list()
        
        # Group by day and calculate average scores
        daily_scores = {}
        for metric in period_metrics:
            if metric.quality_score:
                day = metric.measured_at.date().isoformat()
                if day not in daily_scores:
                    daily_scores[day] = []
                daily_scores[day].append(metric.quality_score)
        
        # Calculate daily averages
        trend_data = []
        for day, scores in daily_scores.items():
            avg_score = sum(scores) / len(scores)
            trend_data.append({
                "date": day,
                "avg_quality_score": round(avg_score, 2),
                "metric_count": len(scores)
            })
        
        # Sort by date
        trend_data.sort(key=lambda x: x["date"])
        
        # Calculate overall trend direction
        trend_direction = "stable"
        if len(trend_data) >= 2:
            first_score = trend_data[0]["avg_quality_score"]
            last_score = trend_data[-1]["avg_quality_score"]
            if last_score > first_score + 2:
                trend_direction = "improving"
            elif last_score < first_score - 2:
                trend_direction = "declining"
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trend_direction": trend_direction,
            "total_metrics": len(period_metrics),
            "daily_data": trend_data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality trends: {str(e)}"
        )


@router.get("/health")
async def quality_health_check():
    """Health check endpoint for quality system."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "quality_metrics": "operational",
            "database": "operational",
            "analytics_engine": "operational"
        }
    }
