"""
Comprehensive Monitoring Dashboard API Endpoints.

Provides real-time monitoring, health checks, alerting, and system
administration capabilities for operations teams.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ...core.health_checks import get_health_manager, initialize_health_checks, setup_monitoring_dashboard
from ...core.metrics_collector import get_metrics_collector
from ...core.log_monitoring import RealTimeLogMonitor
from .auth import get_current_user, require_admin
from ...models.user import User


logger = logging.getLogger(__name__)
router = APIRouter(tags=["monitoring"])


@router.get("/")
async def get_monitoring_overview(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get monitoring system overview - main monitoring endpoint."""
    return await get_monitoring_dashboard(current_user)


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive monitoring dashboard data.
    
    Combines health checks, metrics, alerts, and system status.
    """
    try:
        health_manager = get_health_manager()
        metrics_collector = get_metrics_collector()
        
        # Get health status
        health_status = health_manager.get_system_health_summary()
        
        # Get metrics
        metrics_data = await metrics_collector.get_metrics_dashboard_data()
        
        # Combine data
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": health_status,
            "metrics": metrics_data,
            "monitoring_status": {
                "health_monitoring_active": health_manager.is_running,
                "metrics_collection_active": metrics_collector.is_collecting,
                "total_components_monitored": len(health_manager.health_checks),
                "active_alerts": len(health_status.get('alerts', {}).get('active_alerts', [])),
                "last_health_check": max([
                    result.get('last_check') for result in health_status.get('components', {}).values()
                    if result.get('last_check')
                ], default='')
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health(
    include_history: bool = Query(False),
    component: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system health status with optional history."""
    try:
        health_manager = get_health_manager()
        
        if component:
            # Get specific component health
            if component not in health_manager.health_checks:
                raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
            
            result = await health_manager.check_component(component)
            if not result:
                raise HTTPException(status_code=500, detail="Failed to check component health")
            
            response_data = {
                "component_name": result.component_name,
                "component_type": result.component_type,
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "error_message": result.error_message,
                "details": result.details,
                "recovery_actions": result.recovery_actions
            }
            
            if include_history:
                response_data["history"] = health_manager.get_component_history(component)
            
            return {
                "success": True,
                "data": response_data
            }
        
        else:
            # Get overall system health
            health_summary = health_manager.get_system_health_summary()
            
            return {
                "success": True,
                "data": health_summary
            }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check/{component_name}")
async def trigger_health_check(
    component_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger immediate health check for a specific component."""
    try:
        health_manager = get_health_manager()
        
        if component_name not in health_manager.health_checks:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
        
        result = await health_manager.check_component(component_name)
        if not result:
            raise HTTPException(status_code=500, detail="Health check failed")
        
        return {
            "success": True,
            "data": {
                "component_name": result.component_name,
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "error_message": result.error_message,
                "details": result.details
            }
        }
        
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check-all")
async def trigger_all_health_checks(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger immediate health check for all components."""
    try:
        health_manager = get_health_manager()
        results = await health_manager.check_all_components()
        
        formatted_results = {}
        for name, result in results.items():
            formatted_results[name] = {
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "error_message": result.error_message
            }
        
        return {
            "success": True,
            "data": {
                "results": formatted_results,
                "total_components": len(results),
                "healthy_components": sum(1 for r in results.values() if r.status == "healthy"),
                "unhealthy_components": sum(1 for r in results.values() if r.status == "unhealthy")
            }
        }
        
    except Exception as e:
        logger.error(f"Error triggering all health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, pattern="^(active|resolved)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system alerts with optional filtering."""
    try:
        health_manager = get_health_manager()
        
        if not health_manager.alerting_system:
            return {
                "success": True,
                "data": {
                    "alerts": [],
                    "total_alerts": 0,
                    "message": "Alerting system not initialized"
                }
            }
        
        # Get alerts based on status
        if status == "active":
            alerts = health_manager.alerting_system.get_active_alerts()
        else:
            alerts = health_manager.alerting_system.get_alert_history(limit)
            
            # Filter by status if specified
            if status == "resolved":
                alerts = [alert for alert in alerts if alert.get('status') == 'resolved']
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get('severity') == severity]
        
        # Apply limit
        alerts = alerts[:limit]
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "filters_applied": {
                    "status": status,
                    "severity": severity,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/{component_name}")
async def trigger_recovery(
    component_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger manual recovery for a specific component."""
    try:
        health_manager = get_health_manager()
        
        if component_name not in health_manager.health_checks:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
        
        # Trigger recovery in background
        recovery_result = await health_manager.force_recovery(component_name)
        
        return {
            "success": True,
            "data": {
                "component_name": component_name,
                "recovery_initiated": recovery_result.get('success', False),
                "message": recovery_result.get('message'),
                "strategies_attempted": recovery_result.get('strategies_attempted', [])
            }
        }
        
    except Exception as e:
        logger.error(f"Error triggering recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recovery/history")
async def get_recovery_history(
    component: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get recovery attempt history."""
    try:
        health_manager = get_health_manager()
        
        if not health_manager.recovery_system:
            return {
                "success": True,
                "data": {
                    "recovery_history": [],
                    "message": "Recovery system not initialized"
                }
            }
        
        history = health_manager.recovery_system.get_recovery_history(component, limit)
        
        return {
            "success": True,
            "data": {
                "recovery_history": history,
                "total_entries": len(history),
                "component_filter": component
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recovery history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/summary")
async def get_log_summary(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get log summary and analysis."""
    try:
        # This would integrate with the log monitoring system
        # For now, return basic structure
        
        log_summary = {
            "time_period_hours": hours,
            "total_logs": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "info_logs": 0,
            "top_errors": [],
            "error_rate_trend": [],
            "log_volume_trend": []
        }
        
        return {
            "success": True,
            "data": log_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting log summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        metrics_collector = get_metrics_collector()
        health_manager = get_health_manager()
        
        # Get current metrics
        system_health = await metrics_collector.get_system_health()
        real_time_metrics = metrics_collector.get_real_time_metrics()
        
        # Get health check response times
        health_summary = health_manager.get_system_health_summary()
        component_response_times = {}
        
        for component_name, component_data in health_summary.get('components', {}).items():
            component_response_times[component_name] = component_data.get('response_time_ms', 0)
        
        performance_data = {
            "system_resources": {
                "cpu_usage_percent": system_health.cpu_usage_percent,
                "memory_usage_percent": system_health.memory_usage_percent,
                "disk_usage_percent": system_health.disk_usage_percent,
                "active_connections": system_health.active_connections
            },
            "application_performance": {
                "avg_response_time_ms": system_health.response_time_ms,
                "requests_per_second": real_time_metrics.requests_per_second,
                "error_rate_percent": system_health.error_rate_percent,
                "cache_hit_rate": real_time_metrics.cache_hit_rate
            },
            "component_response_times": component_response_times,
            "database_metrics": {
                "connections": real_time_metrics.database_connections,
                "response_time_ms": component_response_times.get('mongodb', 0)
            },
            "external_services": {
                "llm_requests_per_minute": real_time_metrics.llm_requests_per_minute,
                "cloud_api_calls_per_minute": real_time_metrics.cloud_api_calls_per_minute
            }
        }
        
        return {
            "success": True,
            "data": performance_data
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/real-time")
async def monitoring_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates."""
    await websocket.accept()
    
    health_manager = get_health_manager()
    metrics_collector = get_metrics_collector()
    
    # Add WebSocket client to metrics collector for real-time updates
    metrics_collector.add_websocket_client(websocket)
    
    try:
        # Send initial data
        initial_data = {
            "type": "initial_data",
            "health_status": health_manager.get_system_health_summary(),
            "metrics": await metrics_collector.get_metrics_dashboard_data(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_text(json.dumps(initial_data, default=str))
        
        # Set up periodic updates
        async def send_periodic_updates():
            while True:
                try:
                    # Send health updates every 30 seconds
                    health_update = {
                        "type": "health_update",
                        "data": health_manager.get_system_health_summary(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(health_update, default=str))
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error sending periodic update: {e}")
                    break
        
        # Start periodic updates
        update_task = asyncio.create_task(send_periodic_updates())
        
        # Handle client messages
        while True:
            try:
                message = await websocket.receive_text()
                request = json.loads(message)
                
                if request.get('type') == 'get_alerts':
                    if health_manager.alerting_system:
                        alerts = health_manager.alerting_system.get_active_alerts()
                        response = {
                            "type": "alerts_response",
                            "data": alerts,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await websocket.send_text(json.dumps(response, default=str))
                
                elif request.get('type') == 'trigger_health_check':
                    component = request.get('component')
                    if component and component in health_manager.health_checks:
                        result = await health_manager.check_component(component)
                        response = {
                            "type": "health_check_result",
                            "component": component,
                            "data": {
                                "status": result.status,
                                "response_time_ms": result.response_time_ms,
                                "timestamp": result.timestamp.isoformat(),
                                "error_message": result.error_message
                            }
                        }
                        await websocket.send_text(json.dumps(response, default=str))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON in request"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
        
        # Cancel periodic updates
        update_task.cancel()
        
    except WebSocketDisconnect:
        logger.info("Monitoring WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in monitoring WebSocket: {e}")
    finally:
        metrics_collector.remove_websocket_client(websocket)


@router.post("/start")
async def start_monitoring(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start monitoring services."""
    try:
        health_manager = get_health_manager()
        metrics_collector = get_metrics_collector()
        
        # Start health monitoring
        if not health_manager.is_running:
            await health_manager.start_monitoring()
        
        # Start metrics collection
        if not metrics_collector.is_collecting:
            await metrics_collector.start_collection()
        
        return {
            "success": True,
            "message": "Monitoring services started",
            "status": {
                "health_monitoring": health_manager.is_running,
                "metrics_collection": metrics_collector.is_collecting
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_monitoring(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop monitoring services."""
    try:
        health_manager = get_health_manager()
        metrics_collector = get_metrics_collector()
        
        # Stop health monitoring
        if health_manager.is_running:
            await health_manager.stop_monitoring()
        
        # Stop metrics collection
        if metrics_collector.is_collecting:
            await metrics_collector.stop_collection()
        
        return {
            "success": True,
            "message": "Monitoring services stopped",
            "status": {
                "health_monitoring": health_manager.is_running,
                "metrics_collection": metrics_collector.is_collecting
            }
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get monitoring system status."""
    try:
        health_manager = get_health_manager()
        metrics_collector = get_metrics_collector()
        
        status_data = {
            "monitoring_services": {
                "health_monitoring": {
                    "active": health_manager.is_running,
                    "components_monitored": len(health_manager.health_checks),
                    "last_check": None  # Would get from actual last check time
                },
                "metrics_collection": {
                    "active": metrics_collector.is_collecting,
                    "uptime_seconds": (datetime.utcnow() - metrics_collector.start_time).total_seconds(),
                    "websocket_clients": len(metrics_collector._websocket_clients)
                },
                "alerting_system": {
                    "active": health_manager.alerting_system is not None,
                    "active_alerts": len(health_manager.alerting_system.get_active_alerts()) if health_manager.alerting_system else 0,
                    "alert_rules": len(health_manager.alerting_system.alert_rules) if health_manager.alerting_system else 0
                },
                "recovery_system": {
                    "active": health_manager.recovery_system is not None,
                    "recovery_strategies": len(health_manager.recovery_system.recovery_strategies) if health_manager.recovery_system else 0
                }
            },
            "system_overview": {
                "overall_health": "unknown",  # Would get from health manager
                "total_components": len(health_manager.health_checks),
                "active_alerts": len(health_manager.alerting_system.get_active_alerts()) if health_manager.alerting_system else 0
            }
        }
        
        return {
            "success": True,
            "data": status_data
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
