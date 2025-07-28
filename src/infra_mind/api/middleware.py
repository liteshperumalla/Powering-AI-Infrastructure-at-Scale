"""
Enhanced API middleware for Infra Mind.

Provides comprehensive middleware for rate limiting, request tracking,
security headers, and API versioning support.
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import Callable, Dict, Any, Optional
from loguru import logger
import time
import uuid
import json
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with multiple strategies.
    
    Supports per-user, per-IP, and per-endpoint rate limiting with
    different time windows and burst allowances.
    """
    
    def __init__(self, app, default_rate_limit: int = 1000):
        super().__init__(app)
        self.default_rate_limit = default_rate_limit
        self.rate_limits = {
            # Per-hour limits by endpoint pattern
            "/api/v1/auth/login": 10,
            "/api/v1/auth/register": 5,
            "/api/v2/auth/login": 10,
            "/api/v2/auth/register": 5,
            "/api/v1/assessments": 100,
            "/api/v2/assessments": 100,
            "/api/v1/recommendations": 50,
            "/api/v2/recommendations": 50,
            "/api/v1/reports": 20,
            "/api/v2/reports": 20,
            "/api/v2/webhooks": 50,
            "/api/v2/admin": 200,
        }
        
        # Storage for rate limit tracking
        self.request_counts = defaultdict(lambda: defaultdict(deque))
        self.cleanup_interval = 3600  # Clean up old entries every hour
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        try:
            # Get client identifier (IP or user ID)
            client_id = self._get_client_id(request)
            endpoint = self._get_endpoint_pattern(request.url.path)
            
            # Check rate limit
            if not self._check_rate_limit(client_id, endpoint):
                logger.warning(f"Rate limit exceeded for {client_id} on {endpoint}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 3600,
                        "limit": self._get_rate_limit(endpoint),
                        "window": "1 hour"
                    },
                    headers={
                        "Retry-After": "3600",
                        "X-RateLimit-Limit": str(self._get_rate_limit(endpoint)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 3600)
                    }
                )
            
            # Record request
            self._record_request(client_id, endpoint)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = self._get_remaining_requests(client_id, endpoint)
            response.headers["X-RateLimit-Limit"] = str(self._get_rate_limit(endpoint))
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 3600)
            
            # Cleanup old entries periodically
            if time.time() - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_entries()
                self.last_cleanup = time.time()
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Continue processing if rate limiting fails
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # TODO: Decode JWT and extract user ID
            # For now, use a mock user ID
            return f"user_{hash(auth_header) % 10000}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """Get endpoint pattern for rate limiting."""
        # Match specific patterns first
        for pattern in self.rate_limits.keys():
            if path.startswith(pattern):
                return pattern
        
        # Default pattern
        return "default"
    
    def _get_rate_limit(self, endpoint: str) -> int:
        """Get rate limit for endpoint."""
        return self.rate_limits.get(endpoint, self.default_rate_limit)
    
    def _check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check if request is within rate limit."""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Get request history for this client and endpoint
        requests = self.request_counts[client_id][endpoint]
        
        # Remove requests older than 1 hour
        while requests and requests[0] < hour_ago:
            requests.popleft()
        
        # Check if under limit
        limit = self._get_rate_limit(endpoint)
        return len(requests) < limit
    
    def _record_request(self, client_id: str, endpoint: str):
        """Record a request for rate limiting."""
        current_time = time.time()
        self.request_counts[client_id][endpoint].append(current_time)
    
    def _get_remaining_requests(self, client_id: str, endpoint: str) -> int:
        """Get remaining requests for client and endpoint."""
        limit = self._get_rate_limit(endpoint)
        current_count = len(self.request_counts[client_id][endpoint])
        return max(0, limit - current_count)
    
    def _cleanup_old_entries(self):
        """Clean up old rate limiting entries."""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        for client_id in list(self.request_counts.keys()):
            for endpoint in list(self.request_counts[client_id].keys()):
                requests = self.request_counts[client_id][endpoint]
                
                # Remove old requests
                while requests and requests[0] < hour_ago:
                    requests.popleft()
                
                # Remove empty endpoint entries
                if not requests:
                    del self.request_counts[client_id][endpoint]
            
            # Remove empty client entries
            if not self.request_counts[client_id]:
                del self.request_counts[client_id]


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Request tracking middleware for monitoring and analytics.
    
    Tracks request metrics, response times, and error rates.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_metrics = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracking."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record request start
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Record metrics
            self._record_metrics(request, response, response_time, request_id)
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            
            return response
            
        except Exception as e:
            # Record error metrics
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            self._record_error_metrics(request, e, response_time, request_id)
            
            # Re-raise the exception
            raise
    
    def _record_metrics(self, request: Request, response: Response, response_time: float, request_id: str):
        """Record request metrics."""
        try:
            metric = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "timestamp": datetime.utcnow(),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": self._get_client_ip(request),
                "success": 200 <= response.status_code < 400
            }
            
            # Store metric (in production, send to monitoring system)
            endpoint = request.url.path
            self.request_metrics[endpoint].append(metric)
            
            # Keep only recent metrics (last 1000 per endpoint)
            if len(self.request_metrics[endpoint]) > 1000:
                self.request_metrics[endpoint] = self.request_metrics[endpoint][-1000:]
            
            # Log slow requests
            if response_time > 5000:  # 5 seconds
                logger.warning(f"Slow request: {request.method} {request.url.path} took {response_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def _record_error_metrics(self, request: Request, error: Exception, response_time: float, request_id: str):
        """Record error metrics."""
        try:
            metric = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(error),
                "error_type": type(error).__name__,
                "response_time_ms": response_time,
                "timestamp": datetime.utcnow(),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": self._get_client_ip(request),
                "success": False
            }
            
            # Store error metric
            endpoint = f"ERROR_{request.url.path}"
            self.request_metrics[endpoint].append(metric)
            
            logger.error(f"Request error: {request.method} {request.url.path} - {error}")
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for enhanced API security.
    
    Adds security headers and performs basic security checks.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "X-API-Version": "2.0.0"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security headers."""
        try:
            # Basic security checks
            self._check_request_security(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # Continue processing if security checks fail
            return await call_next(request)
    
    def _check_request_security(self, request: Request):
        """Perform basic security checks."""
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan"]
        
        if any(agent in user_agent for agent in suspicious_agents):
            logger.warning(f"Suspicious user agent detected: {user_agent}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"Large request detected: {content_length} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """
    API versioning middleware for backward compatibility.
    
    Handles API version detection and routing.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.supported_versions = ["v1", "v2"]
        self.default_version = "v2"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with version handling."""
        try:
            # Detect API version
            version = self._detect_version(request)
            
            # Add version to request state
            request.state.api_version = version
            
            # Process request
            response = await call_next(request)
            
            # Add version headers
            response.headers["X-API-Version"] = version
            response.headers["X-Supported-Versions"] = ",".join(self.supported_versions)
            
            return response
            
        except Exception as e:
            logger.error(f"Versioning middleware error: {e}")
            return await call_next(request)
    
    def _detect_version(self, request: Request) -> str:
        """Detect API version from request."""
        # Check URL path
        path = request.url.path
        for version in self.supported_versions:
            if f"/api/{version}/" in path:
                return version
        
        # Check Accept header
        accept_header = request.headers.get("accept", "")
        for version in self.supported_versions:
            if f"application/vnd.infra-mind.{version}+json" in accept_header:
                return version
        
        # Check custom header
        version_header = request.headers.get("x-api-version")
        if version_header in self.supported_versions:
            return version_header
        
        # Default version
        return self.default_version


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """
    Maintenance mode middleware.
    
    Blocks requests during maintenance mode with appropriate responses.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.maintenance_mode = False
        self.maintenance_message = "System is under maintenance"
        self.allowed_paths = ["/health", "/api/v1/health", "/api/v2/health"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with maintenance mode check."""
        try:
            # Check if maintenance mode is enabled
            if self.maintenance_mode and request.url.path not in self.allowed_paths:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "Service Unavailable",
                        "message": self.maintenance_message,
                        "maintenance_mode": True,
                        "retry_after": 3600
                    },
                    headers={
                        "Retry-After": "3600",
                        "X-Maintenance-Mode": "true"
                    }
                )
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Maintenance middleware error: {e}")
            return await call_next(request)
    
    def enable_maintenance(self, message: str = None):
        """Enable maintenance mode."""
        self.maintenance_mode = True
        if message:
            self.maintenance_message = message
        logger.warning("Maintenance mode enabled")
    
    def disable_maintenance(self):
        """Disable maintenance mode."""
        self.maintenance_mode = False
        logger.info("Maintenance mode disabled")


# Middleware factory function
def create_middleware_stack(app):
    """Create and configure the complete middleware stack."""
    
    # Add middleware in reverse order (last added = first executed)
    
    # Maintenance mode (should be first to block requests if needed)
    maintenance_middleware = MaintenanceModeMiddleware(app)
    app.add_middleware(MaintenanceModeMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # API versioning
    app.add_middleware(APIVersioningMiddleware)
    
    # Request tracking
    app.add_middleware(RequestTrackingMiddleware)
    
    # Rate limiting (should be early to prevent abuse)
    app.add_middleware(RateLimitMiddleware, default_rate_limit=1000)
    
    return app