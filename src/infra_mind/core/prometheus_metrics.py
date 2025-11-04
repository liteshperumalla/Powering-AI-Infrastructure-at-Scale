"""
Prometheus Metrics Collection for Infra Mind.

Provides comprehensive application monitoring with Prometheus:
- Request metrics (count, duration, status codes)
- Database query metrics
- LLM API usage tracking
- Cache performance
- Business metrics (assessments, users, recommendations)
- Custom application metrics

Integration:
```python
from fastapi import FastAPI
from infra_mind.core.prometheus_metrics import setup_metrics, metrics_middleware

app = FastAPI()

# Setup metrics endpoint
setup_metrics(app)

# Add middleware
app.middleware("http")(metrics_middleware)

# Custom metrics
from infra_mind.core.prometheus_metrics import (
    assessment_created,
    llm_api_call,
    cache_operation
)

@app.post("/api/assessments")
async def create_assessment():
    assessment_created.inc()
    # ...
```

Grafana Dashboard: Import dashboard ID 1860 for FastAPI metrics
"""

from typing import Callable, Dict, Any
from datetime import datetime
import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
)
from prometheus_client.exposition import make_asgi_app
from fastapi import FastAPI, Request, Response
from fastapi.responses import Response as FastAPIResponse
from loguru import logger


# ==================== HTTP METRICS ====================

# HTTP request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# HTTP request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Active requests
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Request size
http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# Response size
http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


# ==================== DATABASE METRICS ====================

# Database queries
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['collection', 'operation']
)

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['collection', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Database connection pool
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections'
)

# Database errors
db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['collection', 'error_type']
)


# ==================== CACHE METRICS ====================

# Cache operations
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

# Cache hit ratio
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')

# Cache operation duration
cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)

# Cache size
cache_entries = Gauge('cache_entries', 'Number of entries in cache')
cache_memory_bytes = Gauge('cache_memory_bytes', 'Cache memory usage in bytes')


# ==================== LLM API METRICS ====================

# LLM API calls
llm_api_calls_total = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['provider', 'model', 'status']
)

# LLM API duration
llm_api_duration_seconds = Histogram(
    'llm_api_duration_seconds',
    'LLM API call duration in seconds',
    ['provider', 'model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0)
)

# LLM tokens used
llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'Total LLM tokens used',
    ['provider', 'model', 'token_type']
)

# LLM API cost
llm_api_cost_usd_total = Counter(
    'llm_api_cost_usd_total',
    'Total LLM API cost in USD',
    ['provider', 'model']
)

# LLM API errors
llm_api_errors_total = Counter(
    'llm_api_errors_total',
    'Total LLM API errors',
    ['provider', 'model', 'error_type']
)


# ==================== BUSINESS METRICS ====================

# Users
users_total = Gauge('users_total', 'Total number of users')
users_active = Gauge('users_active', 'Number of active users')
users_created_total = Counter(
    'users_created_total',
    'Total users created',
    ['subscription_tier']
)

# Assessments
assessments_total = Gauge('assessments_total', 'Total number of assessments')
assessments_created_total = Counter(
    'assessments_created_total',
    'Total assessments created',
    ['status']
)
assessments_completed_total = Counter(
    'assessments_completed_total',
    'Total completed assessments'
)
assessment_duration_seconds = Histogram(
    'assessment_duration_seconds',
    'Assessment processing duration in seconds',
    buckets=(30, 60, 120, 300, 600, 1200, 1800, 3600)
)

# Recommendations
recommendations_generated_total = Counter(
    'recommendations_generated_total',
    'Total recommendations generated',
    ['category', 'priority']
)
recommendation_confidence = Histogram(
    'recommendation_confidence_score',
    'Recommendation confidence scores',
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0)
)

# Reports
reports_generated_total = Counter(
    'reports_generated_total',
    'Total reports generated',
    ['report_type', 'format']
)
report_generation_duration_seconds = Histogram(
    'report_generation_duration_seconds',
    'Report generation duration in seconds',
    buckets=(1, 5, 10, 30, 60, 120)
)


# ==================== AI AGENT METRICS ====================

# Agent executions
agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_name', 'status']
)

# Agent duration
agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_name'],
    buckets=(5, 10, 30, 60, 120, 300, 600)
)

# Agent errors
agent_errors_total = Counter(
    'agent_errors_total',
    'Total agent errors',
    ['agent_name', 'error_type']
)

# Agent confidence
agent_confidence_score = Histogram(
    'agent_confidence_score',
    'Agent confidence scores',
    ['agent_name'],
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0)
)


# ==================== SYSTEM METRICS ====================

# Application info
app_info = Info('app_info', 'Application information')

# Application version
app_version = Gauge('app_version', 'Application version', ['version'])

# Uptime
app_uptime_seconds = Gauge('app_uptime_seconds', 'Application uptime in seconds')

# Python info
python_info = Info('python_info', 'Python runtime information')


# ==================== CUSTOM METRICS TRACKING ====================

class MetricsCollector:
    """Utility class for collecting custom metrics."""

    def __init__(self):
        self.start_time = time.time()

    def track_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """Track HTTP request metrics."""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        if request_size:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

        if response_size:
            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)

    def track_db_query(
        self,
        collection: str,
        operation: str,
        duration: float,
        error: str = None
    ):
        """Track database query metrics."""
        db_queries_total.labels(
            collection=collection,
            operation=operation
        ).inc()

        db_query_duration_seconds.labels(
            collection=collection,
            operation=operation
        ).observe(duration)

        if error:
            db_errors_total.labels(
                collection=collection,
                error_type=error
            ).inc()

    def track_cache_operation(
        self,
        operation: str,
        hit: bool = None,
        duration: float = None
    ):
        """Track cache operation metrics."""
        if hit is not None:
            result = 'hit' if hit else 'miss'
            cache_operations_total.labels(
                operation=operation,
                result=result
            ).inc()

            if hit:
                cache_hits.inc()
            else:
                cache_misses.inc()

        if duration is not None:
            cache_operation_duration_seconds.labels(
                operation=operation
            ).observe(duration)

    def track_llm_call(
        self,
        provider: str,
        model: str,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        error: str = None
    ):
        """Track LLM API call metrics."""
        llm_api_calls_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()

        llm_api_duration_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration)

        if prompt_tokens:
            llm_tokens_used_total.labels(
                provider=provider,
                model=model,
                token_type='prompt'
            ).inc(prompt_tokens)

        if completion_tokens:
            llm_tokens_used_total.labels(
                provider=provider,
                model=model,
                token_type='completion'
            ).inc(completion_tokens)

        if cost:
            llm_api_cost_usd_total.labels(
                provider=provider,
                model=model
            ).inc(cost)

        if error:
            llm_api_errors_total.labels(
                provider=provider,
                model=model,
                error_type=error
            ).inc()

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


# Global metrics collector instance
metrics_collector = MetricsCollector()


# ==================== MIDDLEWARE ====================

async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to collect HTTP request metrics.

    Automatically tracks:
    - Request count
    - Request duration
    - Request/response sizes
    - Status codes
    """
    # Skip metrics endpoint
    if request.url.path == "/metrics":
        return await call_next(request)

    # Extract endpoint pattern (remove IDs for better aggregation)
    endpoint = request.url.path
    for pattern in ['/assessments/', '/users/', '/reports/']:
        if pattern in endpoint:
            parts = endpoint.split('/')
            endpoint = '/'.join(parts[:3]) + '/{id}'
            break

    method = request.method

    # Track in-progress requests
    http_requests_in_progress.labels(
        method=method,
        endpoint=endpoint
    ).inc()

    # Track request
    start_time = time.time()
    request_size = int(request.headers.get('content-length', 0))

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        response_size = int(response.headers.get('content-length', 0))

        # Track metrics
        metrics_collector.track_http_request(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code,
            duration=duration,
            request_size=request_size,
            response_size=response_size
        )

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Track error
        metrics_collector.track_http_request(
            method=method,
            endpoint=endpoint,
            status_code=500,
            duration=duration,
            request_size=request_size
        )

        raise

    finally:
        # Decrement in-progress counter
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()


# ==================== SETUP FUNCTIONS ====================

def setup_metrics(app: FastAPI, endpoint: str = "/metrics"):
    """
    Setup Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance
        endpoint: Metrics endpoint path (default: /metrics)

    Example:
        app = FastAPI()
        setup_metrics(app)
    """
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount(endpoint, metrics_app)

    # Set application info
    app_info.info({
        'name': 'Infra Mind',
        'description': 'AI Infrastructure Advisory Platform',
        'version': '1.0.0'
    })

    # Set Python info
    import sys
    python_info.info({
        'version': sys.version,
        'implementation': sys.implementation.name
    })

    logger.info(f" Prometheus metrics available at {endpoint}")


def update_business_metrics(
    users_count: int = None,
    assessments_count: int = None,
    active_users_count: int = None
):
    """
    Update business metrics.

    Should be called periodically (e.g., every minute) to keep metrics fresh.

    Args:
        users_count: Total number of users
        assessments_count: Total number of assessments
        active_users_count: Number of active users
    """
    if users_count is not None:
        users_total.set(users_count)

    if assessments_count is not None:
        assessments_total.set(assessments_count)

    if active_users_count is not None:
        users_active.set(active_users_count)

    # Update uptime
    app_uptime_seconds.set(metrics_collector.get_uptime())


# ==================== DECORATOR FOR TRACKING ====================

def track_execution_time(metric_name: str, labels: Dict[str, str] = None):
    """
    Decorator to track execution time of functions.

    Example:
        @track_execution_time('assessment_processing', {'type': 'full'})
        async def process_assessment(assessment_id: str):
            # ... processing logic
            pass
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # Log duration
                logger.debug(f"{metric_name} took {duration:.3f}s")
        return wrapper
    return decorator


# Example usage:
"""
from fastapi import FastAPI, Request
from infra_mind.core.prometheus_metrics import (
    setup_metrics,
    metrics_middleware,
    metrics_collector,
    assessments_created_total,
    agent_executions_total
)

app = FastAPI()

# Setup metrics endpoint
setup_metrics(app)

# Add metrics middleware
@app.middleware("http")
async def add_metrics(request: Request, call_next):
    return await metrics_middleware(request, call_next)

# Use in endpoints
@app.post("/api/assessments")
async def create_assessment(data: AssessmentCreate):
    assessments_created_total.labels(status="pending").inc()

    # ... create assessment logic

    return assessment

# Track LLM calls
async def call_openai(prompt: str):
    start_time = time.time()
    try:
        response = await openai.ChatCompletion.create(...)
        duration = time.time() - start_time

        metrics_collector.track_llm_call(
            provider="openai",
            model="gpt-4",
            status="success",
            duration=duration,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            cost=0.03 * (response.usage.total_tokens / 1000)
        )

        return response
    except Exception as e:
        metrics_collector.track_llm_call(
            provider="openai",
            model="gpt-4",
            status="error",
            duration=time.time() - start_time,
            error=type(e).__name__
        )
        raise

# Update business metrics periodically
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=1)
async def update_metrics():
    users_count = await User.count()
    assessments_count = await Assessment.count()
    active_users = await User.find(User.last_login > datetime.now() - timedelta(days=7)).count()

    update_business_metrics(
        users_count=users_count,
        assessments_count=assessments_count,
        active_users_count=active_users
    )

scheduler.start()
"""
