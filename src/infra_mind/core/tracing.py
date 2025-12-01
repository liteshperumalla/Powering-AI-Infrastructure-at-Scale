"""
OpenTelemetry distributed tracing setup for Infra Mind.

Provides comprehensive request tracing across services for better observability.
"""

from typing import Optional, Any
import os
from loguru import logger

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi")


def setup_tracing(app_name: str = "infra-mind", app_version: str = "2.0.0") -> Optional[Any]:
    """
    Setup OpenTelemetry distributed tracing.
    
    Args:
        app_name: Application name for tracing
        app_version: Application version
    
    Returns:
        Tracer instance or None if OpenTelemetry is not available
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, tracing disabled")
        return None
    
    # Check if tracing is enabled
    tracing_enabled = os.getenv("INFRA_MIND_TRACING_ENABLED", "false").lower() == "true"
    if not tracing_enabled:
        logger.info("Distributed tracing is disabled. Set INFRA_MIND_TRACING_ENABLED=true to enable")
        return None
    
    try:
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: app_name,
            SERVICE_VERSION: app_version,
            "deployment.environment": os.getenv("INFRA_MIND_ENVIRONMENT", "development")
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure exporters
        exporter_type = os.getenv("INFRA_MIND_TRACING_EXPORTER", "console").lower()
        
        if exporter_type == "otlp":
            # OTLP exporter for Jaeger, Zipkin, or other OTLP-compatible backends
            otlp_endpoint = os.getenv("INFRA_MIND_OTLP_ENDPOINT", "http://localhost:4317")
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            logger.info(f"Using OTLP exporter: {otlp_endpoint}")
        else:
            # Console exporter for development
            exporter = ConsoleSpanExporter()
            logger.info("Using console exporter for traces")
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        logger.success(f"Distributed tracing initialized for {app_name} v{app_version}")
        
        # Return tracer
        return trace.get_tracer(__name__)
    
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return None


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        return
    
    tracing_enabled = os.getenv("INFRA_MIND_TRACING_ENABLED", "false").lower() == "true"
    if not tracing_enabled:
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def instrument_httpx():
    """Instrument HTTPX client with OpenTelemetry."""
    if not OTEL_AVAILABLE:
        return
    
    tracing_enabled = os.getenv("INFRA_MIND_TRACING_ENABLED", "false").lower() == "true"
    if not tracing_enabled:
        return
    
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX client instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument HTTPX: {e}")


def instrument_redis():
    """Instrument Redis client with OpenTelemetry."""
    if not OTEL_AVAILABLE:
        return
    
    tracing_enabled = os.getenv("INFRA_MIND_TRACING_ENABLED", "false").lower() == "true"
    if not tracing_enabled:
        return
    
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis client instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument Redis: {e}")


def get_tracer(name: str = __name__) -> Optional[Any]:
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name (usually __name__)
    
    Returns:
        Tracer instance or None if tracing is disabled
    """
    if not OTEL_AVAILABLE:
        return None
    
    tracing_enabled = os.getenv("INFRA_MIND_TRACING_ENABLED", "false").lower() == "true"
    if not tracing_enabled:
        return None
    
    return trace.get_tracer(name)


# Example usage in endpoints:
"""
from infra_mind.core.tracing import get_tracer

tracer = get_tracer(__name__)

@router.get("/example")
async def example_endpoint():
    if tracer:
        with tracer.start_as_current_span("example_operation"):
            # Your code here
            result = await some_operation()
            return result
    else:
        result = await some_operation()
        return result
"""
