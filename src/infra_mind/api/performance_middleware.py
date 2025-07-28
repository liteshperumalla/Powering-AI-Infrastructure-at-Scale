"""
Performance optimization middleware for FastAPI.

Implements response time optimization, request caching, and performance monitoring.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json
import hashlib
from collections import defaultdict, deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.cache import cache_manager
from ..core.metrics_collector import get_metrics_collector
from ..core.performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API performance optimization.
    
    Features:
    - Response time monitoring
    - Request/response caching
    - Slow endpoint detection
    - Performance metrics collection
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize performance middleware."""
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.slow_endpoint_threshold = 2000  # 2 seconds in ms
        self.cache_enabled_endpoints = {
            "/api/v1/cloud/services",
            "/api/v1/cloud/pricing",
            "/api/v1/recommendations/templates",
            "/api/v1/compliance/frameworks"
        }
        self.cache_ttl = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance optimization."""
        start_time = time.time()
        endpoint = f"{request.method} {request.url.path}"
        
        # Check for cached response
        if request.method == "GET" and request.url.path in self.cache_enabled_endpoints:
            cached_response = await self._get_cached_response(request)
            if cached_response:
                # Record cache hit
                response_time = (time.time() - start_time) * 1000
                self.metrics_collector.track_request(response_time, True)
                
                # Add performance headers
                cached_response.headers["X-Cache"] = "HIT"
                cached_response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
                
                return cached_response
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Record metrics
            self.metrics_collector.track_request(response_time, response.status_code < 400)
            self._record_endpoint_performance(endpoint, response_time)
            
            # Cache successful GET responses
            if (request.method == "GET" and 
                response.status_code == 200 and 
                request.url.path in self.cache_enabled_endpoints):
                await self._cache_response(request, response)
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            response.headers["X-Cache"] = "MISS"
            
            # Log slow requests
            if response_time > self.slow_endpoint_threshold:
                logger.warning(
                    f"Slow endpoint detected: {endpoint} "
                    f"({response_time:.2f}ms) - Status: {response.status_code}"
                )
            
            return response
            
        except Exception as e:
            # Record error
            response_time = (time.time() - start_time) * 1000
            self.metrics_collector.track_request(response_time, False)
            
            logger.error(f"Request failed: {endpoint} - {str(e)}")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers={"X-Response-Time": f"{response_time:.2f}ms"}
            )
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include path, query parameters, and relevant headers
        key_data = {
            "path": request.url.path,
            "query": str(request.query_params),
            "method": request.method
        }
        
        # Include user context if available
        if hasattr(request.state, "user_id"):
            key_data["user_id"] = request.state.user_id
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"api_response:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _get_cached_response(self, request: Request) -> Optional[Response]:
        """Get cached response if available."""
        try:
            cache_key = self._generate_cache_key(request)
            
            # Try to get from cache
            cached_data = await cache_manager.redis_client.get(cache_key) if cache_manager._connected else None
            
            if cached_data:
                data = json.loads(cached_data)
                
                # Check if cache is still valid
                cached_at = datetime.fromisoformat(data.get("cached_at", ""))
                if datetime.utcnow() - cached_at < timedelta(seconds=self.cache_ttl):
                    return JSONResponse(
                        content=data["content"],
                        status_code=data["status_code"],
                        headers=data.get("headers", {})
                    )
            
            return None
            
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None
    
    async def _cache_response(self, request: Request, response: Response) -> None:
        """Cache response for future requests."""
        try:
            cache_key = self._generate_cache_key(request)
            
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse response content
            try:
                content = json.loads(response_body.decode())
            except json.JSONDecodeError:
                content = response_body.decode()
            
            # Prepare cache data
            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Store in cache
            if cache_manager._connected:
                await cache_manager.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(cache_data, default=str)
                )
            
            # Recreate response with same body
            response.body_iterator = self._create_body_iterator(response_body)
            
        except Exception as e:
            logger.debug(f"Response caching failed: {e}")
    
    def _create_body_iterator(self, body: bytes):
        """Create body iterator for response."""
        async def body_iterator():
            yield body
        return body_iterator()
    
    def _record_endpoint_performance(self, endpoint: str, response_time: float) -> None:
        """Record endpoint performance metrics."""
        self.response_times[endpoint].append({
            "timestamp": time.time(),
            "response_time": response_time
        })
        
        # Record in metrics collector
        asyncio.create_task(
            self.metrics_collector.record_monitoring_metric(
                f"api.endpoint.response_time",
                response_time,
                "ms"
            )
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all endpoints."""
        stats = {}
        
        for endpoint, times in self.response_times.items():
            if not times:
                continue
            
            response_times = [t["response_time"] for t in times]
            
            stats[endpoint] = {
                "request_count": len(response_times),
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "slow_requests": len([t for t in response_times if t > self.slow_endpoint_threshold])
            }
        
        return stats


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for response compression to improve API performance.
    """
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024):
        """
        Initialize compression middleware.
        
        Args:
            app: ASGI application
            minimum_size: Minimum response size to compress (bytes)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = {
            "application/json",
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with compression."""
        response = await call_next(request)
        
        # Check if compression is supported and beneficial
        if (self._should_compress(request, response) and 
            hasattr(response, 'body') and 
            len(response.body) >= self.minimum_size):
            
            # Compress response body
            compressed_body = await self._compress_response(response.body)
            
            if compressed_body and len(compressed_body) < len(response.body):
                # Update response with compressed body
                response.body = compressed_body
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Length"] = str(len(compressed_body))
                response.headers["Vary"] = "Accept-Encoding"
        
        return response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed."""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False
        
        # Don't compress if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        return True
    
    async def _compress_response(self, body: bytes) -> Optional[bytes]:
        """Compress response body using gzip."""
        try:
            import gzip
            return gzip.compress(body)
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API rate limiting to prevent abuse and ensure fair usage.
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute per client
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=requests_per_minute))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_id, current_time)
        
        # Check rate limit
        if len(self.client_requests[client_id]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 60))
                }
            )
        
        # Record request
        self.client_requests[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.client_requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from request state
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _clean_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove requests older than 1 minute."""
        cutoff_time = current_time - 60  # 1 minute ago
        
        requests = self.client_requests[client_id]
        while requests and requests[0] < cutoff_time:
            requests.popleft()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed request logging and monitoring.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize request logging middleware."""
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with detailed logging."""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # Log request start
        logger.info(
            f"Request started: {request_id} - {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            response_time = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                f"Request completed: {request_id} - Status: {response.status_code} "
                f"Time: {response_time:.2f}ms"
            )
            
            # Add request ID header
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log request error
            response_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request_id} - Error: {str(e)} "
                f"Time: {response_time:.2f}ms"
            )
            
            # Return error response with request ID
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# Middleware factory functions
def create_performance_middleware() -> PerformanceMiddleware:
    """Create performance middleware instance."""
    return PerformanceMiddleware


def create_compression_middleware(minimum_size: int = 1024) -> CompressionMiddleware:
    """Create compression middleware instance."""
    def middleware_factory(app: ASGIApp) -> CompressionMiddleware:
        return CompressionMiddleware(app, minimum_size)
    return middleware_factory


def create_rate_limiting_middleware(requests_per_minute: int = 100) -> RateLimitingMiddleware:
    """Create rate limiting middleware instance."""
    def middleware_factory(app: ASGIApp) -> RateLimitingMiddleware:
        return RateLimitingMiddleware(app, requests_per_minute)
    return middleware_factory


def create_request_logging_middleware() -> RequestLoggingMiddleware:
    """Create request logging middleware instance."""
    return RequestLoggingMiddleware