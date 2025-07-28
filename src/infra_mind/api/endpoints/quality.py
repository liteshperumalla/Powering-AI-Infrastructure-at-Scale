"""
API endpoints for quality assurance system.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from ...core.auth import get_current_user, require_admin
from ...models.user import User
from ...quality import (
    FeedbackCollector, QualityScoreManager, ABTestingFramework,
    ContinuousImprovementSystem, UserFeedback, FeedbackType,
    Experiment, ExperimentVariant, ExperimentMetric, ExperimentType,
    ExperimentStatus, ImprovementActionType
)
from ...core.cache import CacheManager
from ...core.metrics_collector import MetricsCollector

router = APIRouter(prefix="/quality", tags=["quality"])
logger = logging.getLogger(__name__)

# Initialize quality components (these would be dependency injected in production)
cache_manager = CacheManager()
metrics_collector = MetricsCollector()
feedback_collector = FeedbackCollector(cache_manager)
quality_manager = QualityScoreManager(cache_manager)
ab_testing = ABTestingFramework(cache_manager)
improvement_system = ContinuousImprovementSystem(cache_manager, metrics_collector)


@router.post("/feedback")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Submit user feedback on recommendations."""
    try:
        # Create feedback object
        feedback = UserFeedback(
            feedback_id=f"{current_user.user_id}_{feedback_data['recommendation_id']}_{datetime.utcnow().timestamp()}",
            user_id=current_user.user_id,
            assessment_id=feedback_data.get("assessment_id", ""),
            recommendation_id=feedback_data["recommendation_id"],
            agent_name=feedback_data.get("agent_name", ""),
            feedback_type=FeedbackType(feedback_data.get("feedback_type", "rating")),
            rating=feedback_data.get("rating"),
            comment=feedback_data.get("comment"),
            implementation_success=feedback_data.get("implementation_success"),
            cost_accuracy=feedback_data.get("cost_accuracy"),
            time_to_implement=feedback_data.get("time_to_implement"),
            business_value_realized=feedback_data.get("business_value_realized"),
            technical_accuracy=feedback_data.get("technical_accuracy"),
            ease_of_implementation=feedback_data.get("ease_of_implementation"),
            would_recommend=feedback_data.get("would_recommend"),
            tags=feedback_data.get("tags", []),
            metadata=feedback_data.get("metadata", {})
        )
        
        # Submit feedback
        success = await feedback_collector.collect_feedback(feedback)
        
        if success:
            return {"message": "Feedback submitted successfully", "feedback_id": feedback.feedback_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
            
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/{recommendation_id}")
async def get_feedback_summary(
    recommendation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get feedback summary for a recommendation."""
    try:
        summary = await feedback_collector.get_feedback_summary(recommendation_id)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/{recommendation_id}")
async def get_quality_score(
    recommendation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get quality score for a recommendation."""
    try:
        score = await quality_manager.get_quality_score(recommendation_id)
        
        if score:
            return score.__dict__
        else:
            return {"message": "No quality score available for this recommendation"}
            
    except Exception as e:
        logger.error(f"Error getting quality score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/performance")
async def get_agent_performance(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for an agent."""
    try:
        performance = await quality_manager.get_agent_performance(agent_name)
        
        if performance:
            return performance.__dict__
        else:
            return {"message": f"No performance data available for agent {agent_name}"}
            
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_quality_overview(
    current_user: User = Depends(require_admin)
):
    """Get system-wide quality overview (admin only)."""
    try:
        overview = await quality_manager.get_system_quality_overview()
        return overview
        
    except Exception as e:
        logger.error(f"Error getting quality overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments")
async def create_experiment(
    experiment_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Create a new A/B test experiment (admin only)."""
    try:
        # Create experiment object
        variants = [
            ExperimentVariant(
                variant_id=v["variant_id"],
                name=v["name"],
                description=v["description"],
                configuration=v["configuration"],
                traffic_allocation=v["traffic_allocation"],
                is_control=v.get("is_control", False),
                metadata=v.get("metadata", {})
            )
            for v in experiment_data["variants"]
        ]
        
        metrics = [
            ExperimentMetric(
                metric_name=m["metric_name"],
                metric_type=m["metric_type"],
                primary=m.get("primary", False),
                description=m.get("description", ""),
                target_improvement=m.get("target_improvement")
            )
            for m in experiment_data["metrics"]
        ]
        
        experiment = Experiment(
            experiment_id=experiment_data["experiment_id"],
            name=experiment_data["name"],
            description=experiment_data["description"],
            experiment_type=ExperimentType(experiment_data["experiment_type"]),
            status=ExperimentStatus(experiment_data.get("status", "draft")),
            variants=variants,
            metrics=metrics,
            target_sample_size=experiment_data["target_sample_size"],
            confidence_level=experiment_data.get("confidence_level", 0.95),
            minimum_detectable_effect=experiment_data.get("minimum_detectable_effect", 0.05),
            start_date=datetime.fromisoformat(experiment_data["start_date"]) if experiment_data.get("start_date") else None,
            end_date=datetime.fromisoformat(experiment_data["end_date"]) if experiment_data.get("end_date") else None,
            created_by=current_user.user_id,
            metadata=experiment_data.get("metadata", {})
        )
        
        success = await ab_testing.create_experiment(experiment)
        
        if success:
            return {"message": "Experiment created successfully", "experiment_id": experiment.experiment_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to create experiment")
            
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    current_user: User = Depends(require_admin)
):
    """Get experiment details (admin only)."""
    try:
        experiment = await ab_testing._get_experiment(experiment_id)
        
        if experiment:
            return experiment
        else:
            raise HTTPException(status_code=404, detail="Experiment not found")
            
    except Exception as e:
        logger.error(f"Error getting experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}/analysis")
async def analyze_experiment(
    experiment_id: str,
    current_user: User = Depends(require_admin)
):
    """Analyze experiment results (admin only)."""
    try:
        analysis = await ab_testing.analyze_experiment(experiment_id)
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_id}/assign")
async def assign_to_experiment(
    experiment_id: str,
    context: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Assign current user to experiment variant."""
    try:
        variant_id = await ab_testing.assign_user_to_experiment(
            experiment_id, current_user.user_id, context or {}
        )
        
        if variant_id:
            return {"variant_id": variant_id, "experiment_id": experiment_id}
        else:
            return {"message": "User not eligible for this experiment"}
            
    except Exception as e:
        logger.error(f"Error assigning to experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/events")
async def record_experiment_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Record an experiment event."""
    try:
        await ab_testing.record_experiment_event(
            current_user.user_id,
            event_data["event_name"],
            event_data.get("event_data", {})
        )
        
        return {"message": "Event recorded successfully"}
        
    except Exception as e:
        logger.error(f"Error recording experiment event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_quality_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(require_admin)
):
    """Get quality alerts (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        # Build query
        query = {}
        if severity:
            query["severity"] = severity
        if resolved is not None:
            query["resolved"] = resolved
        
        # Get alerts
        alerts = await improvement_system.db.quality_alerts.find(query).limit(limit).sort("created_at", -1).to_list(length=None)
        
        return {"alerts": alerts, "total": len(alerts)}
        
    except Exception as e:
        logger.error(f"Error getting quality alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
):
    """Acknowledge a quality alert (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        result = await improvement_system.db.quality_alerts.update_one(
            {"alert_id": alert_id},
            {"$set": {"acknowledged": True, "acknowledged_by": current_user.user_id, "acknowledged_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            return {"message": "Alert acknowledged successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: str,
    current_user: User = Depends(require_admin)
):
    """Resolve a quality alert (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        result = await improvement_system.db.quality_alerts.update_one(
            {"alert_id": alert_id},
            {"$set": {
                "resolved": True,
                "resolved_by": current_user.user_id,
                "resolved_at": datetime.utcnow(),
                "resolution_notes": resolution_notes
            }}
        )
        
        if result.modified_count > 0:
            return {"message": "Alert resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/improvement-actions")
async def get_improvement_actions(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(require_admin)
):
    """Get improvement actions (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        # Build query
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = {"$gte": priority}
        
        # Get actions
        actions = await improvement_system.db.improvement_actions.find(query).limit(limit).sort("priority", -1).to_list(length=None)
        
        return {"actions": actions, "total": len(actions)}
        
    except Exception as e:
        logger.error(f"Error getting improvement actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improvement-actions")
async def create_improvement_action(
    action_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Create a new improvement action (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        await improvement_system._create_improvement_action(
            action_type=ImprovementActionType(action_data["action_type"]),
            title=action_data["title"],
            description=action_data["description"],
            priority=action_data["priority"],
            affected_agents=action_data.get("affected_agents", []),
            expected_impact=action_data["expected_impact"],
            implementation_effort=action_data["implementation_effort"]
        )
        
        return {"message": "Improvement action created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating improvement action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improvement-actions/{action_id}/assign")
async def assign_improvement_action(
    action_id: str,
    assigned_to: str,
    due_date: Optional[str] = None,
    current_user: User = Depends(require_admin)
):
    """Assign an improvement action (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        update_data = {
            "assigned_to": assigned_to,
            "status": "in_progress"
        }
        
        if due_date:
            update_data["due_date"] = datetime.fromisoformat(due_date)
        
        result = await improvement_system.db.improvement_actions.update_one(
            {"action_id": action_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"message": "Improvement action assigned successfully"}
        else:
            raise HTTPException(status_code=404, detail="Improvement action not found")
            
    except Exception as e:
        logger.error(f"Error assigning improvement action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improvement-actions/{action_id}/complete")
async def complete_improvement_action(
    action_id: str,
    results: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Mark an improvement action as completed (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        result = await improvement_system.db.improvement_actions.update_one(
            {"action_id": action_id},
            {"$set": {
                "status": "completed",
                "completion_date": datetime.utcnow(),
                "results": results
            }}
        )
        
        if result.modified_count > 0:
            return {"message": "Improvement action completed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Improvement action not found")
            
    except Exception as e:
        logger.error(f"Error completing improvement action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def get_quality_reports(
    period: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(require_admin)
):
    """Get quality reports (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        # Build query
        query = {}
        if period:
            query["period"] = period
        
        # Get reports
        reports = await improvement_system.db.quality_reports.find(query).limit(limit).sort("generated_at", -1).to_list(length=None)
        
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        logger.error(f"Error getting quality reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_quality_trends(
    metric_name: Optional[str] = None,
    time_period: Optional[str] = None,
    current_user: User = Depends(require_admin)
):
    """Get quality trends (admin only)."""
    try:
        if not improvement_system.db:
            await improvement_system.initialize()
        
        # Build query
        query = {}
        if metric_name:
            query["metric_name"] = metric_name
        if time_period:
            query["time_period"] = time_period
        
        # Get trends
        trends = await improvement_system.db.quality_trends.find(query).to_list(length=None)
        
        return {"trends": trends, "total": len(trends)}
        
    except Exception as e:
        logger.error(f"Error getting quality trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_quality_system(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """Initialize the quality assurance system (admin only)."""
    try:
        # Initialize in background
        background_tasks.add_task(improvement_system.initialize)
        
        return {"message": "Quality system initialization started"}
        
    except Exception as e:
        logger.error(f"Error initializing quality system: {e}")
        raise HTTPException(status_code=500, detail=str(e))