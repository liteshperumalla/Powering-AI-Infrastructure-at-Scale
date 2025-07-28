"""
Resilience API endpoints for system health, failover, and recovery management.

Provides REST API endpoints for monitoring system resilience,
managing failover configurations, and controlling recovery operations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ...core.health_checks import get_health_manager, HealthStatus
from ...core.failover import get_failover_orchestrator, FailoverStrategy
from ...core.resilience import get_system_recovery_manager, resilience_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resilience"])


# Request/Response Models
class HealthCheckResponse(BaseModel):
    """Response model for health check data."""
    overall_status: str
    total_components: int
    healthy_components: int
    degraded_components: int
    unhealthy_components: int
    unknown_components: int
    components: Dict[str, Any]
    timestamp: str


class ComponentHealthResponse(BaseModel):
    """Response model for individual component health."""
    component_name: str
    status: str
    response_time_ms: float
    last_check: str
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    recovery_actions: List[str] = Field(default_factory=list)


class FailoverStatusResponse(BaseModel):
    """Response model for failover status."""
    is_monitoring: bool
    total_services: int
    healthy_services: int
    degraded_services: int
    services: Dict[str, Any]
    timestamp: str


class RecoveryStatsResponse(BaseModel):
    """Response model for recovery statistics."""
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    success_rate_percent: float
    avg_recovery_time_seconds: float
    components_recovered: List[str]


class ManualFailoverRequest(BaseModel):
    """Request model for manual failover."""
    target_endpoint: Optional[str] = None
    reason: str = "Manual failover requested"


class RecoveryRequest(BaseModel):
    """Request model for manual recovery."""
    component_name: str
    force: bool = False
    custom_context: Dict[str, Any] = Field(default_factory=dict)


# Health Check Endpoints
@router.get("/health/system", response_model=HealthCheckResponse)
async def get_system_health(
    current_user: str = Depends(get_current_user)
):
    """
    Get overall system health status.
    
    Returns comprehensive health information for all monitored components
    including databases, caches, external APIs, and agents.
    """
    try:
        health_manager = get_health_manager()
        health_summary = health_manager.get_system_health_summary()
        
        return HealthCheckResponse(**health_summary)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/component/{component_name}", response_model=ComponentHealthResponse)
async def get_component_health(
    component_name: str = Path(..., description="Name of the component to check"),
    current_user: str = Depends(get_current_user)
):
    """
    Get health status for a specific component.
    
    Returns detailed health information including response times,
    error messages, and recent recovery actions.
    """
    try:
        health_manager = get_health_manager()
        health_result = await health_manager.check_component(component_name)
        
        if not health_result:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{component_name}' not found"
            )
        
        return ComponentHealthResponse(
            component_name=health_result.component_name,
            status=health_result.status,
            response_time_ms=health_result.response_time_ms,
            last_check=health_result.timestamp.isoformat(),
            error_message=health_result.error_message,
            details=health_result.details,
            recovery_actions=health_result.recovery_actions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting component health for {component_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/component/{component_name}/history")
async def get_component_health_history(
    component_name: str = Path(..., description="Name of the component"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    current_user: str = Depends(get_current_user)
):
    """
    Get health check history for a specific component.
    
    Returns historical health check data for trend analysis
    and performance monitoring.
    """
    try:
        health_manager = get_health_manager()
        history = health_manager.get_component_history(component_name, limit)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No health history found for component '{component_name}'"
            )
        
        return {
            "component_name": component_name,
            "history": history,
            "total_records": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health history for {component_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/component/{component_name}/check")
async def trigger_health_check(
    component_name: str = Path(..., description="Name of the component to check"),
    current_user: str = Depends(get_current_user)
):
    """
    Manually trigger a health check for a specific component.
    
    Useful for immediate health verification after maintenance
    or configuration changes.
    """
    try:
        health_manager = get_health_manager()
        health_result = await health_manager.check_component(component_name)
        
        if not health_result:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{component_name}' not found"
            )
        
        return {
            "message": f"Health check triggered for {component_name}",
            "result": {
                "status": health_result.status,
                "response_time_ms": health_result.response_time_ms,
                "timestamp": health_result.timestamp.isoformat(),
                "error_message": health_result.error_message,
                "recovery_actions": health_result.recovery_actions
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering health check for {component_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Failover Management Endpoints
@router.get("/failover/status", response_model=FailoverStatusResponse)
async def get_failover_status(
    current_user: str = Depends(get_current_user)
):
    """
    Get system-wide failover status.
    
    Returns information about all services configured for failover,
    their current endpoints, and health status.
    """
    try:
        orchestrator = get_failover_orchestrator()
        status = orchestrator.get_system_status()
        
        return FailoverStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting failover status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failover/service/{service_name}")
async def get_service_failover_status(
    service_name: str = Path(..., description="Name of the service"),
    current_user: str = Depends(get_current_user)
):
    """
    Get failover status for a specific service.
    
    Returns detailed information about service endpoints,
    current active endpoint, and failover history.
    """
    try:
        orchestrator = get_failover_orchestrator()
        manager = orchestrator.get_service_manager(service_name)
        
        if not manager:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found in failover configuration"
            )
        
        status = manager.get_service_status()
        
        return {
            "service_status": status,
            "failover_history": manager.failover_history[-10:],  # Last 10 events
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting failover status for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/failover/service/{service_name}/trigger")
async def trigger_manual_failover(
    service_name: str = Path(..., description="Name of the service"),
    request: ManualFailoverRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Manually trigger failover for a service.
    
    Allows administrators to force failover to a different endpoint
    for maintenance or testing purposes.
    """
    try:
        orchestrator = get_failover_orchestrator()
        
        success = await orchestrator.manual_failover(
            service_name,
            request.target_endpoint
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to trigger failover for service '{service_name}'"
            )
        
        return {
            "message": f"Manual failover triggered for {service_name}",
            "target_endpoint": request.target_endpoint,
            "reason": request.reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual failover for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Recovery Management Endpoints
@router.get("/recovery/stats", response_model=RecoveryStatsResponse)
async def get_recovery_stats(
    current_user: str = Depends(get_current_user)
):
    """
    Get system recovery statistics.
    
    Returns overall recovery performance metrics including
    success rates, average recovery times, and component statistics.
    """
    try:
        recovery_manager = get_system_recovery_manager()
        stats = recovery_manager.get_recovery_stats()
        
        return RecoveryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting recovery stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recovery/history")
async def get_recovery_history(
    component_name: Optional[str] = Query(None, description="Filter by component name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    current_user: str = Depends(get_current_user)
):
    """
    Get system recovery history.
    
    Returns historical recovery attempts with details about
    success/failure, actions taken, and recovery times.
    """
    try:
        recovery_manager = get_system_recovery_manager()
        history = recovery_manager.get_recovery_history(component_name, limit)
        
        return {
            "recovery_history": history,
            "component_filter": component_name,
            "total_records": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recovery history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/trigger")
async def trigger_manual_recovery(
    request: RecoveryRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Manually trigger recovery for a component.
    
    Allows administrators to force recovery attempts for
    failed components outside of automatic recovery cycles.
    """
    try:
        recovery_manager = get_system_recovery_manager()
        
        # Prepare error context
        error_context = {
            "manual_trigger": True,
            "user": current_user,
            "timestamp": datetime.utcnow().isoformat(),
            **request.custom_context
        }
        
        # Attempt recovery
        result = await recovery_manager.attempt_recovery(
            request.component_name,
            error_context
        )
        
        return {
            "message": f"Manual recovery triggered for {request.component_name}",
            "recovery_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering manual recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/enable")
async def enable_auto_recovery(
    current_user: str = Depends(get_current_user)
):
    """
    Enable automatic recovery system-wide.
    
    Enables automatic recovery attempts when components fail
    health checks or encounter errors.
    """
    try:
        recovery_manager = get_system_recovery_manager()
        recovery_manager.enable_auto_recovery()
        
        return {
            "message": "Auto-recovery enabled system-wide",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error enabling auto-recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/disable")
async def disable_auto_recovery(
    current_user: str = Depends(get_current_user)
):
    """
    Disable automatic recovery system-wide.
    
    Disables automatic recovery attempts, requiring manual
    intervention for component failures.
    """
    try:
        recovery_manager = get_system_recovery_manager()
        recovery_manager.disable_auto_recovery()
        
        return {
            "message": "Auto-recovery disabled system-wide",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error disabling auto-recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Circuit Breaker Management Endpoints
@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    current_user: str = Depends(get_current_user)
):
    """
    Get status of all circuit breakers.
    
    Returns current state, failure counts, and configuration
    for all registered circuit breakers.
    """
    try:
        health_status = resilience_manager.get_all_services_health()
        
        return {
            "circuit_breakers": health_status,
            "total_services": len(health_status),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuit-breakers/{service_name}")
async def get_service_circuit_breaker(
    service_name: str = Path(..., description="Name of the service"),
    current_user: str = Depends(get_current_user)
):
    """
    Get circuit breaker status for a specific service.
    
    Returns detailed circuit breaker information including
    state, failure counts, and recent state changes.
    """
    try:
        health_status = resilience_manager.get_service_health(service_name)
        
        if "error" in health_status:
            raise HTTPException(
                status_code=404,
                detail=health_status["error"]
            )
        
        return {
            "service_name": service_name,
            "circuit_breaker": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breaker for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/circuit-breakers/{service_name}/reset")
async def reset_circuit_breaker(
    service_name: str = Path(..., description="Name of the service"),
    current_user: str = Depends(get_current_user)
):
    """
    Reset circuit breaker for a service.
    
    Manually resets the circuit breaker to closed state,
    clearing failure counts and allowing requests to proceed.
    """
    try:
        success = resilience_manager.reset_service(service_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found"
            )
        
        return {
            "message": f"Circuit breaker reset for {service_name}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System Resilience Overview
@router.get("/overview")
async def get_resilience_overview(
    current_user: str = Depends(get_current_user)
):
    """
    Get comprehensive resilience system overview.
    
    Returns high-level status of all resilience components
    including health checks, failover, recovery, and circuit breakers.
    """
    try:
        # Get health manager status
        health_manager = get_health_manager()
        health_summary = health_manager.get_system_health_summary()
        
        # Get failover orchestrator status
        orchestrator = get_failover_orchestrator()
        failover_status = orchestrator.get_system_status()
        
        # Get recovery manager stats
        recovery_manager = get_system_recovery_manager()
        recovery_stats = recovery_manager.get_recovery_stats()
        
        # Get circuit breaker status
        circuit_breakers = resilience_manager.get_all_services_health()
        
        return {
            "overall_status": health_summary["overall_status"],
            "health_checks": {
                "total_components": health_summary["total_components"],
                "healthy_components": health_summary["healthy_components"],
                "degraded_components": health_summary["degraded_components"],
                "unhealthy_components": health_summary["unhealthy_components"]
            },
            "failover": {
                "is_monitoring": failover_status["is_monitoring"],
                "total_services": failover_status["total_services"],
                "healthy_services": failover_status["healthy_services"],
                "degraded_services": failover_status["degraded_services"]
            },
            "recovery": {
                "total_attempts": recovery_stats["total_attempts"],
                "success_rate_percent": recovery_stats["success_rate_percent"],
                "avg_recovery_time_seconds": recovery_stats["avg_recovery_time_seconds"]
            },
            "circuit_breakers": {
                "total_services": len(circuit_breakers),
                "services": list(circuit_breakers.keys())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting resilience overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))