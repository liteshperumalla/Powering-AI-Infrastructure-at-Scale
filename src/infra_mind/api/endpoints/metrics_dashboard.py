"""
Metrics Dashboard API Endpoints.

Provides comprehensive metrics API for system administrators
and real-time monitoring dashboards.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import JSONResponse

from ...core.metrics_collector import get_metrics_collector
from .auth import get_current_user
from ...models.user import User


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/dashboard")
async def get_metrics_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive metrics dashboard data.
    
    Requires admin privileges.
    """
    try:
        collector = get_metrics_collector()
        dashboard_data = await collector.get_metrics_dashboard_data()
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current system health status."""
    try:
        collector = get_metrics_collector()
        health_status = await collector.get_system_health()
        
        return {
            "success": True,
            "data": {
                "status": health_status.status,
                "cpu_usage_percent": health_status.cpu_usage_percent,
                "memory_usage_percent": health_status.memory_usage_percent,
                "disk_usage_percent": health_status.disk_usage_percent,
                "active_connections": health_status.active_connections,
                "response_time_ms": health_status.response_time_ms,
                "error_rate_percent": health_status.error_rate_percent,
                "uptime_seconds": health_status.uptime_seconds,
                "timestamp": health_status.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-engagement")
async def get_user_engagement_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user engagement metrics."""
    try:
        collector = get_metrics_collector()
        engagement_metrics = await collector.get_user_engagement_summary()
        
        return {
            "success": True,
            "data": {
                "active_users_count": engagement_metrics.active_users_count,
                "new_users_count": engagement_metrics.new_users_count,
                "assessments_started": engagement_metrics.assessments_started,
                "assessments_completed": engagement_metrics.assessments_completed,
                "reports_generated": engagement_metrics.reports_generated,
                "average_session_duration_minutes": engagement_metrics.average_session_duration_minutes,
                "bounce_rate_percent": engagement_metrics.bounce_rate_percent,
                "page_views": engagement_metrics.page_views,
                "unique_visitors": engagement_metrics.unique_visitors,
                "conversion_rate": engagement_metrics.conversion_rate,
                "timestamp": engagement_metrics.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user engagement metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business-metrics")
async def get_business_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get business metrics."""
    try:
        collector = get_metrics_collector()
        business_metrics = await collector.get_business_metrics_summary()
        
        return {
            "success": True,
            "data": {
                "total_assessments": business_metrics.total_assessments,
                "completed_assessments": business_metrics.completed_assessments,
                "total_reports": business_metrics.total_reports,
                "total_recommendations": business_metrics.total_recommendations,
                "user_satisfaction_score": business_metrics.user_satisfaction_score,
                "revenue_impact": business_metrics.revenue_impact,
                "cost_savings_identified": business_metrics.cost_savings_identified,
                "compliance_score": business_metrics.compliance_score,
                "agent_efficiency_score": business_metrics.agent_efficiency_score,
                "timestamp": business_metrics.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting business metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real-time")
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get real-time metrics."""
    try:
        collector = get_metrics_collector()
        real_time_metrics = collector.get_real_time_metrics()
        
        return {
            "success": True,
            "data": {
                "requests_per_second": real_time_metrics.requests_per_second,
                "active_connections": real_time_metrics.active_connections,
                "queue_depth": real_time_metrics.queue_depth,
                "cache_hit_rate": real_time_metrics.cache_hit_rate,
                "database_connections": real_time_metrics.database_connections,
                "llm_requests_per_minute": real_time_metrics.llm_requests_per_minute,
                "cloud_api_calls_per_minute": real_time_metrics.cloud_api_calls_per_minute,
                "error_rate_last_minute": real_time_metrics.error_rate_last_minute,
                "timestamp": real_time_metrics.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_metrics(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    metric_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get historical metrics data."""
    try:
        collector = get_metrics_collector()
        
        # Get historical data from Redis if available
        if collector.redis_client:
            try:
                cutoff_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
                historical_data = collector.redis_client.zrangebyscore(
                    'infra_mind:metrics:timeseries',
                    cutoff_time,
                    '+inf',
                    withscores=True
                )
                
                metrics_history = []
                for data, timestamp in historical_data:
                    try:
                        metrics_point = json.loads(data.decode('utf-8'))
                        metrics_point['timestamp'] = datetime.fromtimestamp(timestamp).isoformat()
                        
                        # Filter by metric type if specified
                        if metric_type:
                            if metric_type in metrics_point:
                                metrics_history.append({
                                    'timestamp': metrics_point['timestamp'],
                                    'data': metrics_point[metric_type]
                                })
                        else:
                            metrics_history.append(metrics_point)
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                return {
                    "success": True,
                    "data": {
                        "metrics": metrics_history,
                        "time_range_hours": hours,
                        "metric_type": metric_type,
                        "total_points": len(metrics_history)
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting historical data from Redis: {e}")
        
        # Fallback to current metrics if Redis not available
        current_metrics = await collector.get_metrics_dashboard_data()
        return {
            "success": True,
            "data": {
                "metrics": [current_metrics],
                "time_range_hours": hours,
                "metric_type": metric_type,
                "total_points": 1,
                "note": "Historical data not available, showing current metrics only"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting historical metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-user-action")
async def track_user_action(
    action_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Track user action for engagement metrics."""
    try:
        collector = get_metrics_collector()
        
        action_type = action_data.get('action_type')
        metadata = action_data.get('metadata', {})
        
        if not action_type:
            raise HTTPException(status_code=400, detail="action_type is required")
        
        collector.track_user_action(
            user_id=str(current_user.id),
            action_type=action_type,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "User action tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking user action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-page-view")
async def track_page_view(
    page_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Track page view for engagement metrics."""
    try:
        collector = get_metrics_collector()
        
        page_path = page_data.get('page_path')
        metadata = page_data.get('metadata', {})
        
        if not page_path:
            raise HTTPException(status_code=400, detail="page_path is required")
        
        collector.track_page_view(
            user_id=str(current_user.id),
            page_path=page_path,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "Page view tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking page view: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-feedback")
async def track_user_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Track user feedback for satisfaction metrics."""
    try:
        collector = get_metrics_collector()
        
        score = feedback_data.get('score')
        feedback_type = feedback_data.get('feedback_type', 'general')
        comments = feedback_data.get('comments')
        
        if score is None:
            raise HTTPException(status_code=400, detail="score is required")
        
        if not isinstance(score, (int, float)) or not (0 <= score <= 10):
            raise HTTPException(status_code=400, detail="score must be a number between 0 and 10")
        
        collector.track_user_feedback(
            user_id=str(current_user.id),
            score=float(score),
            feedback_type=feedback_type,
            comments=comments
        )
        
        return {
            "success": True,
            "message": "User feedback tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking user feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/real-time-stream")
async def real_time_metrics_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming."""
    await websocket.accept()
    
    collector = get_metrics_collector()
    collector.add_websocket_client(websocket)
    
    try:
        # Send initial metrics
        initial_metrics = await collector.get_metrics_dashboard_data()
        await websocket.send_text(json.dumps({
            'type': 'initial_metrics',
            'data': initial_metrics
        }, default=str))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client message or timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client requests
                try:
                    request = json.loads(message)
                    if request.get('type') == 'get_current_metrics':
                        current_metrics = await collector.get_metrics_dashboard_data()
                        await websocket.send_text(json.dumps({
                            'type': 'current_metrics',
                            'data': current_metrics
                        }, default=str))
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON in request'
                    }))
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({
                    'type': 'ping',
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from metrics stream")
    except Exception as e:
        logger.error(f"Error in metrics WebSocket: {e}")
    finally:
        collector.remove_websocket_client(websocket)


@router.get("/export")
async def export_metrics(
    format: str = Query("json", regex="^(json|csv)$"),
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Export metrics data in specified format."""
    try:
        collector = get_metrics_collector()
        
        # Get comprehensive metrics data
        dashboard_data = await collector.get_metrics_dashboard_data()
        
        if format == "json":
            return JSONResponse(
                content={
                    "success": True,
                    "data": dashboard_data,
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "time_range_hours": hours
                },
                headers={
                    "Content-Disposition": f"attachment; filename=infra_mind_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                "timestamp", "metric_category", "metric_name", "value", "unit"
            ])
            
            # Flatten metrics data for CSV
            timestamp = dashboard_data.get('timestamp', datetime.utcnow().isoformat())
            
            for category, metrics in dashboard_data.items():
                if isinstance(metrics, dict) and category != 'timestamp':
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            writer.writerow([timestamp, category, metric_name, value, ""])
            
            csv_content = output.getvalue()
            output.close()
            
            return JSONResponse(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=infra_mind_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_metrics_alerts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current metrics-based alerts."""
    try:
        collector = get_metrics_collector()
        
        # Get current metrics
        health_status = await collector.get_system_health()
        real_time_metrics = collector.get_real_time_metrics()
        
        alerts = []
        
        # Check for system health alerts
        if health_status.cpu_usage_percent > 80:
            alerts.append({
                "type": "system",
                "severity": "critical" if health_status.cpu_usage_percent > 90 else "warning",
                "message": f"High CPU usage: {health_status.cpu_usage_percent:.1f}%",
                "metric": "cpu_usage_percent",
                "value": health_status.cpu_usage_percent,
                "threshold": 80
            })
        
        if health_status.memory_usage_percent > 85:
            alerts.append({
                "type": "system",
                "severity": "critical" if health_status.memory_usage_percent > 95 else "warning",
                "message": f"High memory usage: {health_status.memory_usage_percent:.1f}%",
                "metric": "memory_usage_percent",
                "value": health_status.memory_usage_percent,
                "threshold": 85
            })
        
        if health_status.error_rate_percent > 5:
            alerts.append({
                "type": "performance",
                "severity": "critical" if health_status.error_rate_percent > 10 else "warning",
                "message": f"High error rate: {health_status.error_rate_percent:.1f}%",
                "metric": "error_rate_percent",
                "value": health_status.error_rate_percent,
                "threshold": 5
            })
        
        if real_time_metrics.error_rate_last_minute > 10:
            alerts.append({
                "type": "performance",
                "severity": "critical",
                "message": f"High error rate in last minute: {real_time_metrics.error_rate_last_minute:.1f}%",
                "metric": "error_rate_last_minute",
                "value": real_time_metrics.error_rate_last_minute,
                "threshold": 10
            })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
                "warning_alerts": len([a for a in alerts if a["severity"] == "warning"]),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))