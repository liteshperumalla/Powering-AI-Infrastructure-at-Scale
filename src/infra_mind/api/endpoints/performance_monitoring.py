"""
Performance monitoring API endpoints.

Provides REST API and WebSocket endpoints for real-time performance monitoring,
alerting, and system health status.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core.performance_monitoring import (
    performance_monitoring,
    Alert,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    PerformanceThreshold,
    ScalingPolicy
)
from ...core.production_performance_optimizer import performance_optimizer
from .auth import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["performance_monitoring"])


# Pydantic models for API requests/responses

class AlertRuleRequest(BaseModel):
    """Request model for creating alert rules."""
    name: str = Field(..., description="Alert rule name")
    description: str = Field(..., description="Alert rule description")
    metric_name: str = Field(..., description="Metric to monitor")
    warning_threshold: float = Field(..., description="Warning threshold value")
    critical_threshold: float = Field(..., description="Critical threshold value")
    emergency_threshold: Optional[float] = Field(None, description="Emergency threshold value")
    comparison_operator: str = Field(">", description="Comparison operator (>, <, >=, <=, ==, !=)")
    evaluation_window_seconds: int = Field(300, description="Evaluation window in seconds")
    min_data_points: int = Field(3, description="Minimum data points required")
    channels: List[str] = Field(["dashboard"], description="Notification channels")
    cooldown_seconds: int = Field(1800, description="Cooldown period in seconds")
    enabled: bool = Field(True, description="Whether rule is enabled")


class AlertResponse(BaseModel):
    """Response model for alerts."""
    id: str
    rule_name: str
    severity: str
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool
    acknowledged: bool
    acknowledged_by: Optional[str] = None


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    metrics: Dict[str, float]
    timestamp: datetime
    system_health: str
    active_alerts_count: int


class PerformanceSummaryResponse(BaseModel):
    """Response model for performance summary."""
    monitoring_active: bool
    active_alerts_count: int
    alert_rules_count: int
    scaling_policies_count: int
    websocket_clients_count: int
    performance_trends: Dict[str, Any]
    last_updated: str


# REST API Endpoints

@router.get("/")
async def get_performance_overview(current_user: User = Depends(get_current_user)):
    """Get performance monitoring overview - main performance endpoint."""
    return await get_system_health()


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health():
    """Get current system health status."""
    try:
        # Get performance optimizer metrics
        perf_report = await performance_optimizer.get_performance_report()
        
        # Get monitoring summary
        monitoring_summary = performance_monitoring.get_performance_summary()
        
        # Get active alerts
        active_alerts = performance_monitoring.get_active_alerts()
        
        # Determine overall health status
        critical_alerts = [a for a in active_alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]
        
        if critical_alerts:
            health_status = "critical"
        elif len(active_alerts) > 0:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": perf_report.get("overall_metrics", {}),
            "monitoring_summary": monitoring_summary,
            "active_alerts_count": len(active_alerts),
            "critical_alerts_count": len(critical_alerts)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_current_metrics():
    """Get current performance metrics."""
    try:
        # Get latest metrics from performance data
        latest_metrics = {}
        for metric_name, data in performance_monitoring.performance_data.items():
            if data:
                latest_metrics[metric_name] = data[-1]["value"]
        
        # Get active alerts
        active_alerts = performance_monitoring.get_active_alerts()
        
        # Determine system health
        critical_alerts = [a for a in active_alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]
        
        if critical_alerts:
            system_health = "critical"
        elif len(active_alerts) > 0:
            system_health = "warning"
        else:
            system_health = "healthy"
        
        return PerformanceMetricsResponse(
            metrics=latest_metrics,
            timestamp=datetime.utcnow(),
            system_health=system_health,
            active_alerts_count=len(active_alerts)
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary():
    """Get performance monitoring summary."""
    try:
        summary = performance_monitoring.get_performance_summary()
        return PerformanceSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance summary")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    active_only: bool = Query(True, description="Return only active alerts"),
    limit: int = Query(100, description="Maximum number of alerts to return")
):
    """Get alerts (active or historical)."""
    try:
        if active_only:
            alerts = performance_monitoring.get_active_alerts()
        else:
            alerts = performance_monitoring.get_alert_history(limit)
        
        return [
            AlertResponse(
                id=alert.id,
                rule_name=alert.rule_name,
                severity=alert.severity.value,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                message=alert.message,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                acknowledged=alert.acknowledged,
                acknowledged_by=alert.acknowledged_by
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    try:
        success = await performance_monitoring.acknowledge_alert(alert_id, current_user.email)
        
        if success:
            return {"message": "Alert acknowledged successfully", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.get("/alert-rules")
async def get_alert_rules():
    """Get all alert rules."""
    try:
        rules = []
        for rule_name, rule in performance_monitoring.alert_rules.items():
            rules.append({
                "name": rule.name,
                "description": rule.description,
                "metric_name": rule.threshold.metric_name,
                "warning_threshold": rule.threshold.warning_threshold,
                "critical_threshold": rule.threshold.critical_threshold,
                "emergency_threshold": rule.threshold.emergency_threshold,
                "comparison_operator": rule.threshold.comparison_operator,
                "evaluation_window_seconds": rule.threshold.evaluation_window_seconds,
                "channels": [channel.value for channel in rule.channels],
                "cooldown_seconds": rule.cooldown_seconds,
                "enabled": rule.enabled
            })
        
        return {"alert_rules": rules}
        
    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rules")


@router.post("/alert-rules")
async def create_alert_rule(
    rule_request: AlertRuleRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new alert rule."""
    try:
        # Convert channels to enum
        channels = []
        for channel_str in rule_request.channels:
            try:
                channels.append(AlertChannel(channel_str))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {channel_str}")
        
        # Create threshold
        threshold = PerformanceThreshold(
            metric_name=rule_request.metric_name,
            warning_threshold=rule_request.warning_threshold,
            critical_threshold=rule_request.critical_threshold,
            emergency_threshold=rule_request.emergency_threshold,
            comparison_operator=rule_request.comparison_operator,
            evaluation_window_seconds=rule_request.evaluation_window_seconds,
            min_data_points=rule_request.min_data_points,
            enabled=rule_request.enabled
        )
        
        # Create alert rule
        alert_rule = AlertRule(
            name=rule_request.name,
            description=rule_request.description,
            threshold=threshold,
            channels=channels,
            cooldown_seconds=rule_request.cooldown_seconds,
            enabled=rule_request.enabled
        )
        
        # Add to monitoring system
        performance_monitoring.add_alert_rule(alert_rule)
        
        return {"message": "Alert rule created successfully", "rule_name": rule_request.name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.delete("/alert-rules/{rule_name}")
async def delete_alert_rule(
    rule_name: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an alert rule."""
    try:
        success = performance_monitoring.remove_alert_rule(rule_name)
        
        if success:
            return {"message": "Alert rule deleted successfully", "rule_name": rule_name}
        else:
            raise HTTPException(status_code=404, detail="Alert rule not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")


@router.get("/scaling-policies")
async def get_scaling_policies():
    """Get all scaling policies."""
    try:
        policies = []
        for policy_name, policy in performance_monitoring.scaling_policies.items():
            policies.append({
                "name": policy.name,
                "description": policy.description,
                "trigger_metric": policy.trigger_metric,
                "scale_up_threshold": policy.scale_up_threshold,
                "scale_down_threshold": policy.scale_down_threshold,
                "cooldown_seconds": policy.cooldown_seconds,
                "min_instances": policy.min_instances,
                "max_instances": policy.max_instances,
                "enabled": policy.enabled
            })
        
        return {"scaling_policies": policies}
        
    except Exception as e:
        logger.error(f"Failed to get scaling policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scaling policies")


@router.get("/trends")
async def get_performance_trends(
    metric_name: Optional[str] = Query(None, description="Specific metric name"),
    hours: int = Query(24, description="Number of hours of trend data")
):
    """Get performance trends."""
    try:
        trends = performance_monitoring.performance_trends
        
        if metric_name:
            if metric_name in trends:
                return {"metric": metric_name, "trend": trends[metric_name]}
            else:
                raise HTTPException(status_code=404, detail="Metric not found")
        
        return {"trends": trends, "hours": hours}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance trends")


@router.get("/recommendations")
async def get_performance_recommendations():
    """Get performance optimization recommendations."""
    try:
        # This would retrieve recommendations from database
        # For now, return mock recommendations
        recommendations = [
            {
                "type": "performance_optimization",
                "priority": "high",
                "title": "High CPU Usage Detected",
                "description": "CPU usage has been consistently above 80% for the past hour",
                "recommendation": "Consider scaling up CPU resources or optimizing CPU-intensive operations",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "type": "cache_optimization",
                "priority": "medium",
                "title": "Low Cache Hit Rate",
                "description": "Cache hit rate has dropped below 70%",
                "recommendation": "Review cache TTL settings and cache warming strategies",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendations")


@router.post("/monitoring/start")
async def start_monitoring(current_user: User = Depends(get_current_user)):
    """Start performance monitoring."""
    try:
        await performance_monitoring.start_monitoring()
        return {"message": "Performance monitoring started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")


@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_user)):
    """Stop performance monitoring."""
    try:
        await performance_monitoring.stop_monitoring()
        return {"message": "Performance monitoring stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")


# WebSocket endpoint for real-time monitoring

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time performance monitoring."""
    await websocket.accept()
    
    # Add client to monitoring system
    performance_monitoring.add_websocket_client(websocket)
    
    try:
        # Send initial data
        initial_data = {
            "type": "connection",
            "message": "Connected to performance monitoring",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message.get("type") == "get_metrics":
                    # Send current metrics
                    latest_metrics = {}
                    for metric_name, data in performance_monitoring.performance_data.items():
                        if data:
                            latest_metrics[metric_name] = data[-1]["value"]
                    
                    response = {
                        "type": "metrics",
                        "data": latest_metrics,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif message.get("type") == "get_alerts":
                    # Send active alerts
                    active_alerts = performance_monitoring.get_active_alerts()
                    alerts_data = [
                        {
                            "id": alert.id,
                            "severity": alert.severity.value,
                            "metric": alert.metric_name,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat()
                        }
                        for alert in active_alerts
                    ]
                    
                    response = {
                        "type": "alerts",
                        "data": alerts_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Message processing failed",
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove client from monitoring system
        performance_monitoring.remove_websocket_client(websocket)


# Additional utility endpoints

@router.get("/metrics/history")
async def get_metrics_history(
    metric_name: str = Query(..., description="Metric name"),
    hours: int = Query(1, description="Number of hours of history"),
    resolution: int = Query(60, description="Resolution in seconds")
):
    """Get historical metrics data."""
    try:
        if metric_name not in performance_monitoring.performance_data:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        # Get data for specified time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        metric_data = performance_monitoring.performance_data[metric_name]
        
        # Filter data by time range
        filtered_data = [
            point for point in metric_data
            if point["timestamp"] > cutoff_time
        ]
        
        # Apply resolution (downsample if needed)
        if resolution > 60 and len(filtered_data) > 100:
            # Simple downsampling - take every nth point
            step = max(1, len(filtered_data) // 100)
            filtered_data = filtered_data[::step]
        
        return {
            "metric_name": metric_name,
            "data": [
                {
                    "value": point["value"],
                    "timestamp": point["timestamp"].isoformat()
                }
                for point in filtered_data
            ],
            "count": len(filtered_data),
            "time_range_hours": hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics history")


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        # Get current metrics
        latest_metrics = {}
        for metric_name, data in performance_monitoring.performance_data.items():
            if data:
                latest_metrics[metric_name] = data[-1]["value"]
        
        # Get active alerts
        active_alerts = performance_monitoring.get_active_alerts()
        
        # Get performance summary
        summary = performance_monitoring.get_performance_summary()
        
        # Get performance optimizer report
        perf_report = await performance_optimizer.get_performance_report()
        
        return {
            "current_metrics": latest_metrics,
            "active_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "metric": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            "monitoring_summary": summary,
            "performance_report": perf_report,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")