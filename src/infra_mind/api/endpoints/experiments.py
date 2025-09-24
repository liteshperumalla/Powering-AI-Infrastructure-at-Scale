"""
A/B testing and experimentation API endpoints with real database functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import uuid

from .auth import get_current_user, require_enterprise_access
from ...models.user import User
from ...models.experiment import (
    Experiment, ExperimentVariant, ExperimentResult, ExperimentEvent,
    ExperimentStatus, VariantType
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["experiments"])


# Pydantic models for request/response
class CreateExperimentRequest(BaseModel):
    """Request model for creating experiment."""
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description") 
    feature_flag: str = Field(..., description="Feature flag identifier")
    target_metric: str = Field(..., description="Primary metric to optimize")
    variants: List[Dict[str, Any]] = Field(..., min_items=2, description="Experiment variants")


class ExperimentResponse(BaseModel):
    """Response model for experiment."""
    id: str
    name: str
    description: str
    feature_flag: str
    status: str
    created_at: str
    created_by: str
    variants: List[Dict[str, Any]]
    target_metric: str


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(require_enterprise_access)
):
    """List all experiments (admin only)."""
    try:
        # Build query
        query = {}
        if status_filter:
            try:
                query["status"] = ExperimentStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )
        
        # Fetch experiments from database
        experiments = await Experiment.find(query).sort(-Experiment.created_at).to_list()
        
        # Convert to response format
        result = []
        for exp in experiments:
            # Get variant details
            variant_details = []
            for variant_id in exp.variants:
                variant = await ExperimentVariant.get(variant_id)
                if variant:
                    variant_details.append({
                        "id": str(variant.id),
                        "name": variant.name,
                        "type": variant.type.value,
                        "traffic_percentage": variant.traffic_percentage
                    })
            
            result.append(ExperimentResponse(
                id=str(exp.id),
                name=exp.name,
                description=exp.description,
                feature_flag=exp.feature_flag,
                status=exp.status.value,
                created_at=exp.created_at.isoformat(),
                created_by=exp.created_by,
                variants=variant_details,
                target_metric=exp.target_metric
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list experiments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list experiments: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: CreateExperimentRequest,
    current_user: User = Depends(require_enterprise_access)
):
    """Create a new A/B test experiment (admin only)."""
    try:
        # Create experiment variants first
        variant_ids = []
        for i, variant_data in enumerate(request.variants):
            variant = ExperimentVariant(
                name=variant_data.get("name", f"Variant {i+1}"),
                type=VariantType(variant_data.get("type", "treatment" if i > 0 else "control")),
                traffic_percentage=variant_data.get("traffic_percentage", 100 / len(request.variants)),
                configuration=variant_data.get("configuration", {}),
                description=variant_data.get("description")
            )
            await variant.insert()
            variant_ids.append(str(variant.id))
        
        # Create experiment
        experiment = Experiment(
            name=request.name,
            description=request.description,
            feature_flag=request.feature_flag,
            variants=variant_ids,
            target_metric=request.target_metric,
            created_by=current_user.email,
            status=ExperimentStatus.DRAFT
        )
        await experiment.insert()
        
        return {
            "experiment_id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status.value,
            "created_at": experiment.created_at.isoformat(),
            "created_by": current_user.email,
            "variants_created": len(variant_ids),
            "message": "Experiment created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}"
        )


@router.get("/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    current_user: User = Depends(require_enterprise_access)
):
    """Get experiment details (admin only)."""
    try:
        experiment = await Experiment.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Get variant details
        variant_details = []
        for variant_id in experiment.variants:
            variant = await ExperimentVariant.get(variant_id)
            if variant:
                variant_details.append({
                    "id": str(variant.id),
                    "name": variant.name,
                    "type": variant.type.value,
                    "traffic_percentage": variant.traffic_percentage,
                    "configuration": variant.configuration,
                    "description": variant.description
                })
        
        # Get latest results
        results = await ExperimentResult.find(
            ExperimentResult.experiment_id == experiment_id
        ).sort(-ExperimentResult.calculated_at).limit(10).to_list()
        
        return {
            "id": str(experiment.id),
            "name": experiment.name,
            "description": experiment.description,
            "feature_flag": experiment.feature_flag,
            "status": experiment.status.value,
            "created_at": experiment.created_at.isoformat(),
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "ended_at": experiment.ended_at.isoformat() if experiment.ended_at else None,
            "created_by": experiment.created_by,
            "variants": variant_details,
            "target_metric": experiment.target_metric,
            "secondary_metrics": experiment.secondary_metrics,
            "minimum_sample_size": experiment.minimum_sample_size,
            "confidence_level": experiment.confidence_level,
            "latest_results": [
                {
                    "variant_name": result.variant_name,
                    "participants": result.participants,
                    "conversions": result.conversions,
                    "conversion_rate": result.conversion_rate,
                    "statistical_significance": result.statistical_significance,
                    "calculated_at": result.calculated_at.isoformat()
                }
                for result in results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment: {str(e)}"
        )


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    current_user: User = Depends(require_enterprise_access)
):
    """Start an experiment (admin only)."""
    try:
        experiment = await Experiment.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start experiment in {experiment.status.value} status"
            )
        
        # Update experiment status
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
        experiment.updated_at = datetime.utcnow()
        await experiment.save()
        
        return {
            "experiment_id": str(experiment.id),
            "status": experiment.status.value,
            "started_at": experiment.started_at.isoformat(),
            "message": "Experiment started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start experiment: {str(e)}"
        )


@router.get("/feature/{feature_flag}/variant")
async def get_user_variant(
    feature_flag: str,
    user_id: str = Query(..., description="User identifier")
):
    """Get variant assignment for a user (accessible to all authenticated users)."""
    try:
        # Find running experiment for this feature flag
        experiment = await Experiment.find_one(
            Experiment.feature_flag == feature_flag,
            Experiment.status == ExperimentStatus.RUNNING
        )
        
        if not experiment:
            # No active experiment, return default
            return {
                "feature_flag": feature_flag,
                "user_id": user_id,
                "variant": "control",
                "assigned_at": datetime.utcnow().isoformat(),
                "experiment_id": None
            }
        
        # Simple hash-based assignment (in production, use proper assignment logic)
        hash_input = f"{user_id}_{experiment.id}"
        hash_value = hash(hash_input) % 100
        
        # Get variants and assign based on traffic percentage
        cumulative_percentage = 0
        assigned_variant = "control"
        
        for variant_id in experiment.variants:
            variant = await ExperimentVariant.get(variant_id)
            if variant:
                cumulative_percentage += variant.traffic_percentage
                if hash_value < cumulative_percentage:
                    assigned_variant = variant.name
                    break
        
        # Record the assignment
        event = ExperimentEvent(
            experiment_id=str(experiment.id),
            feature_flag=feature_flag,
            user_id=user_id,
            variant_name=assigned_variant,
            event_type="assignment",
            user_attributes={}
        )
        await event.insert()
        
        return {
            "feature_flag": feature_flag,
            "user_id": user_id,
            "variant": assigned_variant,
            "assigned_at": datetime.utcnow().isoformat(),
            "experiment_id": str(experiment.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user variant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user variant: {str(e)}"
        )


@router.post("/feature/{feature_flag}/track")
async def track_experiment_event(
    feature_flag: str,
    event_data: Dict[str, Any]
):
    """Track an event for experiment analysis (accessible to all users)."""
    try:
        # Find experiment for this feature flag
        experiment = await Experiment.find_one(
            Experiment.feature_flag == feature_flag,
            Experiment.status == ExperimentStatus.RUNNING
        )
        
        if not experiment:
            return {
                "feature_flag": feature_flag,
                "status": "no_active_experiment",
                "message": "No active experiment for this feature flag"
            }
        
        # Create event record
        event = ExperimentEvent(
            experiment_id=str(experiment.id),
            feature_flag=feature_flag,
            user_id=event_data.get("user_id", "anonymous"),
            variant_name=event_data.get("variant"),
            event_type=event_data.get("event_type", "conversion"),
            event_value=event_data.get("value"),
            custom_metrics=event_data.get("custom_metrics", {}),
            user_attributes=event_data.get("user_attributes", {}),
            session_id=event_data.get("session_id")
        )
        await event.insert()
        
        return {
            "feature_flag": feature_flag,
            "experiment_id": str(experiment.id),
            "event_id": str(event.id),
            "tracked_at": event.timestamp.isoformat(),
            "status": "recorded",
            "message": "Event tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to track event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track event: {str(e)}"
        )


@router.get("/dashboard/data")
async def get_dashboard_data(
    current_user: User = Depends(require_enterprise_access)
):
    """Get A/B testing dashboard data (admin only)."""
    try:
        # Get experiment counts by status
        total_experiments = await Experiment.count()
        active_experiments = await Experiment.count(Experiment.status == ExperimentStatus.RUNNING)
        completed_experiments = await Experiment.count(Experiment.status == ExperimentStatus.COMPLETED)
        
        # Get recent experiments
        recent_experiments = await Experiment.find().sort(-Experiment.created_at).limit(5).to_list()
        
        # Get total participants (events)
        total_events = await ExperimentEvent.count()
        
        experiment_summaries = []
        for exp in recent_experiments:
            # Get participant count for this experiment
            participant_count = await ExperimentEvent.count(
                ExperimentEvent.experiment_id == str(exp.id)
            )
            
            experiment_summaries.append({
                "id": str(exp.id),
                "name": exp.name,
                "status": exp.status.value,
                "participants": participant_count,
                "created_at": exp.created_at.isoformat()
            })
        
        return {
            "total_experiments": total_experiments,
            "active_experiments": active_experiments,
            "completed_experiments": completed_experiments,
            "total_participants": total_events,
            "recent_experiments": experiment_summaries,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )