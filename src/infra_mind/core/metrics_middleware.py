"""
Metrics Middleware for FastAPI.

Automatically tracks API request metrics, response times, and user engagement.
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics_collector import get_metrics_collector


logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect API metrics.
    
    Tracks:
    - Request/response times
    - HTTP status codes
    - Error rates
    - User engagement actions
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        """Initialize metrics middleware."""
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Skip metrics collection for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract user information if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'id', None)
        
        # Track user action based on request
        if user_id:
            action_type = self._determine_action_type(request)
            if action_type:
                self.metrics_collector.track_user_action(
                    user_id=str(user_id),
                    action_type=action_type,
                    metadata={
                        'method': request.method,
                        'path': request.url.path,
                        'user_agent': request.headers.get('user-agent'),
                        'ip_address': request.client.host if request.client else None
                    }
                )
        
        # Process request
        response = None
        success = True
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            success = status_code < 400
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            success = False
            status_code = 500
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Track request metrics
        self.metrics_collector.track_request(response_time_ms, success)
        
        # Add metrics headers to response
        if response:
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            response.headers["X-Request-ID"] = getattr(request.state, 'request_id', 'unknown')
        
        return response
    
    def _determine_action_type(self, request: Request) -> Optional[str]:
        """Determine user action type based on request."""
        method = request.method.lower()
        path = request.url.path.lower()
        
        # Map common API endpoints to action types
        action_mappings = {
            ('post', '/api/assessments'): 'assessment_started',
            ('put', '/api/assessments'): 'assessment_updated',
            ('get', '/api/assessments'): 'assessment_viewed',
            ('post', '/api/reports'): 'report_generated',
            ('get', '/api/reports'): 'report_viewed',
            ('post', '/api/recommendations'): 'recommendations_requested',
            ('get', '/api/recommendations'): 'recommendations_viewed',
            ('post', '/api/auth/login'): 'user_login',
            ('post', '/api/auth/register'): 'user_register',
            ('post', '/api/auth/logout'): 'user_logout',
        }
        
        # Check for exact matches
        for (req_method, req_path), action in action_mappings.items():
            if method == req_method and path.startswith(req_path):
                return action
        
        # Check for pattern matches
        if method == 'get' and '/dashboard' in path:
            return 'dashboard_viewed'
        elif method == 'get' and '/assessment' in path:
            return 'assessment_form_viewed'
        elif method == 'post' and '/assessment' in path:
            return 'assessment_submitted'
        elif method == 'get' and path.endswith('.pdf'):
            return 'report_downloaded'
        
        return None


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to provide health check endpoint.
    """
    
    def __init__(self, app):
        """Initialize health check middleware."""
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle health check requests."""
        if request.url.path == "/health":
            try:
                health_status = await self.metrics_collector.get_system_health()
                
                return JSONResponse(
                    status_code=200 if health_status.status == "healthy" else 503,
                    content={
                        "status": health_status.status,
                        "timestamp": health_status.timestamp.isoformat(),
                        "uptime_seconds": health_status.uptime_seconds,
                        "system": {
                            "cpu_usage_percent": health_status.cpu_usage_percent,
                            "memory_usage_percent": health_status.memory_usage_percent,
                            "disk_usage_percent": health_status.disk_usage_percent,
                            "active_connections": health_status.active_connections
                        },
                        "performance": {
                            "avg_response_time_ms": health_status.response_time_ms,
                            "error_rate_percent": health_status.error_rate_percent
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": time.time()
                    }
                )
        
        return await call_next(request)


class MetricsEndpointMiddleware(BaseHTTPMiddleware):
    """
    Middleware to provide metrics endpoint.
    """
    
    def __init__(self, app):
        """Initialize metrics endpoint middleware."""
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle metrics requests."""
        if request.url.path == "/metrics":
            try:
                # Get system health
                health_status = await self.metrics_collector.get_system_health()
                
                # Get user engagement metrics
                engagement_metrics = await self.metrics_collector.get_user_engagement_summary()
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "timestamp": time.time(),
                        "system_health": {
                            "status": health_status.status,
                            "cpu_usage_percent": health_status.cpu_usage_percent,
                            "memory_usage_percent": health_status.memory_usage_percent,
                            "disk_usage_percent": health_status.disk_usage_percent,
                            "active_connections": health_status.active_connections,
                            "uptime_seconds": health_status.uptime_seconds,
                            "avg_response_time_ms": health_status.response_time_ms,
                            "error_rate_percent": health_status.error_rate_percent
                        },
                        "user_engagement": {
                            "active_users_count": engagement_metrics.active_users_count,
                            "assessments_started": engagement_metrics.assessments_started,
                            "assessments_completed": engagement_metrics.assessments_completed,
                            "reports_generated": engagement_metrics.reports_generated,
                            "average_session_duration_minutes": engagement_metrics.average_session_duration_minutes
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Metrics endpoint failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": str(e),
                        "timestamp": time.time()
                    }
                )
        
        return await call_next(request)