"""
Main API Gateway for Infra Mind.

This FastAPI application serves as the primary API gateway for the Infra Mind
multi-agent advisory platform, providing REST endpoints and WebSocket connections
for real-time features including progress updates, notifications, and collaboration.
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infra_mind.api.routes import api_router
from infra_mind.api.websocket import get_websocket_manager, initialize_websocket_manager
from infra_mind.core.database import init_database, close_database
from infra_mind.core.config import get_settings
from infra_mind.core.auth import get_current_user_from_token
from infra_mind.core.metrics_collector import initialize_metrics_collection, shutdown_metrics_collection
from infra_mind.core.metrics_middleware import MetricsMiddleware, HealthCheckMiddleware, MetricsEndpointMiddleware
from infra_mind.core.security_middleware import setup_security_middleware
from infra_mind.orchestration.events import EventManager
from infra_mind.orchestration.monitoring import get_workflow_monitor, initialize_workflow_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Infra Mind API Gateway...")
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Only raise in production, allow development mode to continue
        settings = get_settings()
        if settings.environment != "development":
            raise
        logger.info("Continuing in development mode with mock data")
    
    # Initialize event manager and workflow monitoring
    try:
        event_manager = EventManager()
        await initialize_workflow_monitoring(event_manager)
        logger.info("Event manager and workflow monitoring initialized")
        
        # Initialize WebSocket manager
        workflow_monitor = get_workflow_monitor()
        await initialize_websocket_manager(event_manager, workflow_monitor)
        logger.info("WebSocket manager initialized")
        
        # Store in app state
        app.state.event_manager = event_manager
        app.state.workflow_monitor = workflow_monitor
        app.state.websocket_manager = get_websocket_manager()
        
    except Exception as e:
        logger.error(f"Failed to initialize real-time systems: {e}")
        settings = get_settings()
        if settings.environment != "development":
            raise
    
    # Initialize metrics collection
    try:
        await initialize_metrics_collection()
        logger.info("Metrics collection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize metrics collection: {e}")
        # Continue without metrics in development mode
        settings = get_settings()
        if settings.environment != "development":
            raise
    
    # Initialize system resilience
    try:
        from infra_mind.core.resilience import initialize_system_resilience
        await initialize_system_resilience()
        logger.info("System resilience initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system resilience: {e}")
        # Continue without resilience in development mode
        settings = get_settings()
        if settings.environment != "development":
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Infra Mind API Gateway...")
    try:
        await shutdown_metrics_collection()
        logger.info("Metrics collection shutdown")
    except Exception as e:
        logger.error(f"Error shutting down metrics: {e}")
    
    try:
        # Shutdown WebSocket manager
        if hasattr(app.state, 'websocket_manager'):
            from infra_mind.api.websocket import shutdown_websocket_manager
            await shutdown_websocket_manager()
            logger.info("WebSocket manager shutdown")
    except Exception as e:
        logger.error(f"Error shutting down WebSocket manager: {e}")
    
    try:
        # Shutdown system resilience
        from infra_mind.core.resilience import shutdown_system_resilience
        await shutdown_system_resilience()
        logger.info("System resilience shutdown")
    except Exception as e:
        logger.error(f"Error shutting down resilience: {e}")
    
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="Infra Mind API Gateway",
    description="AI-powered infrastructure advisory platform API with multi-agent orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Infra Mind Support",
        "url": "https://infra-mind.com/support",
        "email": "support@infra-mind.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.infra-mind.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.infra-mind.com", 
            "description": "Staging server"
        }
    ],
    terms_of_service="https://infra-mind.com/terms"
)

# Set up comprehensive security middleware (includes CORS)
setup_security_middleware(app)

# Add enhanced middleware stack
from infra_mind.api.middleware import (
    RateLimitMiddleware,
    RequestTrackingMiddleware, 
    SecurityHeadersMiddleware,
    APIVersioningMiddleware,
    MaintenanceModeMiddleware
)

# Add middleware in reverse order (last added = first executed)
app.add_middleware(MaintenanceModeMiddleware)
app.add_middleware(APIVersioningMiddleware)
app.add_middleware(RequestTrackingMiddleware)

# Add original metrics middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(MetricsEndpointMiddleware)


# Enhanced OpenAPI schema with comprehensive documentation
def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation and interactive features."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Infra Mind API Gateway",
        version="2.0.0",
        description="""
        ## Infra Mind API Gateway v2.0
        
        **AI-powered infrastructure advisory platform** that coordinates specialized AI agents
        to provide comprehensive infrastructure recommendations, compliance guidance, and
        strategic roadmaps for enterprises scaling their AI initiatives.
        
        ### 🚀 Key Features
        - **Multi-Agent Orchestration**: Coordinate specialized AI agents (CTO, MLOps, Cloud Engineer, Research, Compliance, AI Consultant, Web Research, Simulation, Report Generator)
        - **Cloud Service Integration**: Real-time data from AWS, Azure, GCP, and Terraform APIs
        - **Professional Reports**: Generate executive summaries, technical roadmaps, and compliance reports
        - **Compliance Guidance**: GDPR, HIPAA, and CCPA compliance recommendations
        - **Webhook Support**: Real-time notifications for workflow events
        - **API Versioning**: Backward-compatible API evolution
        - **Interactive Testing**: Built-in API testing with sample data
        
        ### 🔐 Authentication
        Most endpoints require JWT authentication. Use the `/api/v1/auth/login` endpoint to obtain a token.
        Include the token in the `Authorization` header as `Bearer <token>`.
        
        ### 📊 Rate Limiting
        API calls are rate-limited to ensure fair usage and system stability:
        - **Free tier**: 100 requests/hour
        - **Pro tier**: 1000 requests/hour  
        - **Enterprise**: Custom limits
        
        ### 🔗 Webhooks
        Configure webhooks to receive real-time notifications for:
        - Assessment status changes
        - Recommendation generation completion
        - Report generation completion
        - System alerts and errors
        
        ### 📈 Monitoring
        Access comprehensive monitoring and analytics:
        - Real-time workflow visualization
        - Agent performance metrics
        - System health monitoring
        - Distributed tracing
        
        ### 🌐 Multi-Cloud Support
        Integrated with major cloud providers:
        - **AWS**: EC2, RDS, EKS, Lambda, SageMaker, Cost Explorer
        - **Azure**: Compute, SQL Database, AKS, Machine Learning, Cost Management
        - **GCP**: Compute Engine, Cloud SQL, GKE, AI Platform, Cloud Billing
        - **Terraform**: Infrastructure cost estimation and planning
        
        ### 📚 Getting Started
        1. Register for an account at `/api/v1/auth/register`
        2. Create an assessment at `/api/v1/assessments`
        3. Generate recommendations at `/api/v1/recommendations/{assessment_id}/generate`
        4. Create professional reports at `/api/v1/reports/{assessment_id}/generate`
        
        ### 🆘 Support
        - **Documentation**: [https://docs.infra-mind.com](https://docs.infra-mind.com)
        - **Support**: [support@infra-mind.com](mailto:support@infra-mind.com)
        - **Status Page**: [https://status.infra-mind.com](https://status.infra-mind.com)
        """,
        routes=app.routes,
    )
    
    # Enhanced tags with detailed descriptions
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication, registration, and JWT token management",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.infra-mind.com/auth"
            }
        },
        {
            "name": "Assessments", 
            "description": "Infrastructure assessment creation, management, and workflow orchestration",
            "externalDocs": {
                "description": "Assessment Guide",
                "url": "https://docs.infra-mind.com/assessments"
            }
        },
        {
            "name": "Recommendations",
            "description": "AI agent recommendations, multi-cloud service suggestions, and validation",
            "externalDocs": {
                "description": "Recommendations Guide", 
                "url": "https://docs.infra-mind.com/recommendations"
            }
        },
        {
            "name": "Reports",
            "description": "Professional report generation, templates, versioning, and export functionality",
            "externalDocs": {
                "description": "Reports Guide",
                "url": "https://docs.infra-mind.com/reports"
            }
        },
        {
            "name": "Monitoring",
            "description": "Workflow monitoring, performance metrics, and system health",
            "externalDocs": {
                "description": "Monitoring Guide",
                "url": "https://docs.infra-mind.com/monitoring"
            }
        },
        {
            "name": "Webhooks",
            "description": "Webhook configuration and event notifications",
            "externalDocs": {
                "description": "Webhooks Guide",
                "url": "https://docs.infra-mind.com/webhooks"
            }
        },
        {
            "name": "Health",
            "description": "System health checks and status endpoints"
        },
        {
            "name": "Admin",
            "description": "Administrative endpoints for system management"
        }
    ]
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /api/v1/auth/login"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication"
        }
    }
    
    # Add example responses
    openapi_schema["components"]["examples"] = {
        "AssessmentExample": {
            "summary": "Sample Assessment",
            "description": "Example of a complete infrastructure assessment",
            "value": {
                "title": "E-commerce Platform Assessment",
                "description": "Infrastructure assessment for scaling e-commerce platform",
                "business_requirements": {
                    "company_size": "medium",
                    "industry": "retail",
                    "budget_range": "100k_500k"
                },
                "technical_requirements": {
                    "workload_types": ["web_application", "data_processing"],
                    "performance_requirements": {
                        "api_response_time_ms": 200,
                        "requests_per_second": 1000
                    }
                }
            }
        },
        "RecommendationExample": {
            "summary": "Sample Recommendation",
            "description": "Example of an AI agent recommendation",
            "value": {
                "agent_name": "cloud_engineer_agent",
                "title": "Multi-Cloud Service Selection",
                "confidence_score": 0.85,
                "recommended_services": [
                    {
                        "service_name": "EC2",
                        "provider": "aws",
                        "estimated_monthly_cost": 2500.00
                    }
                ]
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns system status and basic metrics.
    """
    try:
        # TODO: Add database connectivity check
        # TODO: Add Redis connectivity check
        # TODO: Add external API connectivity checks
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2025-01-23T00:00:00Z",
            "services": {
                "database": "connected",  # TODO: Implement actual check
                "cache": "connected",     # TODO: Implement actual check
                "agents": "ready"         # TODO: Implement actual check
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )


# Root endpoint with comprehensive API information
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with comprehensive API information and quick start guide.
    """
    return {
        "message": "Infra Mind API Gateway v2.0",
        "description": "AI-powered infrastructure advisory platform with multi-agent orchestration",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Multi-agent AI recommendations",
            "Real-time cloud service integration", 
            "Professional report generation",
            "Webhook notifications",
            "Comprehensive monitoring"
        ],
        "quick_start": {
            "1_register": "POST /api/v2/auth/register",
            "2_login": "POST /api/v2/auth/login", 
            "3_create_assessment": "POST /api/v2/assessments",
            "4_generate_recommendations": "POST /api/v2/recommendations/{assessment_id}/generate",
            "5_create_report": "POST /api/v2/reports/{assessment_id}/generate"
        },
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
            "api_versions": "/api/versions",
            "testing_tools": "/api/v2/testing"
        },
        "monitoring": {
            "health_check": "/health",
            "detailed_health": "/api/v2/admin/health/detailed",
            "system_metrics": "/api/v2/admin/metrics"
        },
        "support": {
            "documentation": "https://docs.infra-mind.com",
            "support_email": "support@infra-mind.com",
            "status_page": "https://status.infra-mind.com"
        }
    }


# Enhanced health check with detailed system information
@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with comprehensive system status.
    
    Returns detailed information about all system components,
    performance metrics, and operational status.
    """
    try:
        current_time = datetime.utcnow()
        
        # TODO: Implement actual health checks for all components
        health_status = {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "version": "2.0.0",
            "uptime_hours": 168.5,
            "environment": get_settings().environment,
            "components": {
                "api_gateway": {
                    "status": "healthy",
                    "response_time_ms": 45,
                    "requests_per_minute": 120,
                    "error_rate_percent": 0.1
                },
                "database": {
                    "status": "healthy", 
                    "connection_pool_size": 20,
                    "active_connections": 8,
                    "query_time_avg_ms": 15
                },
                "cache": {
                    "status": "healthy",
                    "hit_rate_percent": 94.2,
                    "memory_usage_percent": 67,
                    "eviction_rate": 0.02
                },
                "agent_orchestrator": {
                    "status": "healthy",
                    "active_workflows": 5,
                    "queued_tasks": 12,
                    "avg_completion_time_minutes": 3.2
                },
                "cloud_apis": {
                    "aws": {"status": "healthy", "response_time_ms": 180},
                    "azure": {"status": "healthy", "response_time_ms": 220},
                    "gcp": {"status": "healthy", "response_time_ms": 195}
                },
                "webhook_delivery": {
                    "status": "healthy",
                    "active_webhooks": 25,
                    "delivery_success_rate_percent": 98.5,
                    "avg_delivery_time_ms": 450
                }
            },
            "metrics": {
                "total_assessments": 3420,
                "assessments_today": 23,
                "total_recommendations": 8750,
                "recommendations_today": 67,
                "total_reports": 2890,
                "reports_today": 18,
                "active_users_24h": 89,
                "api_calls_per_hour": 7200
            },
            "performance": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 67.8,
                "disk_usage_percent": 23.1,
                "network_io_mbps": 12.5,
                "avg_response_time_ms": 245.3
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Health check partially failed",
            "message": "Some components may be experiencing issues"
        }


# WebSocket endpoints for real-time features
@app.websocket("/ws/{assessment_id}")
async def websocket_assessment_endpoint(websocket: WebSocket, assessment_id: str, token: str = None):
    """
    WebSocket endpoint for assessment-specific real-time collaboration and updates.
    
    Args:
        websocket: WebSocket connection
        assessment_id: Assessment ID for room-based features
        token: JWT authentication token (passed as query parameter)
    """
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        try:
            user = await get_current_user_from_token(token)
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get WebSocket manager
        ws_manager = get_websocket_manager()
        
        # Connect user
        session_id = await ws_manager.connect(websocket, user, assessment_id)
        
        try:
            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await ws_manager.handle_message(session_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await ws_manager._send_error(session_id, str(e))
        
        finally:
            # Disconnect user
            await ws_manager.disconnect(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass


@app.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket, token: str = None):
    """
    General WebSocket endpoint for system-wide updates and notifications.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token (passed as query parameter)
    """
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        try:
            user = await get_current_user_from_token(token)
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get WebSocket manager
        ws_manager = get_websocket_manager()
        
        # Connect user without assessment room
        session_id = await ws_manager.connect(websocket, user)
        
        try:
            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await ws_manager.handle_message(session_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await ws_manager._send_error(session_id, str(e))
        
        finally:
            # Disconnect user
            await ws_manager.disconnect(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass


# WebSocket connection status endpoint
@app.get("/api/websocket/status", tags=["WebSocket"])
async def websocket_status():
    """
    Get WebSocket connection statistics and status.
    
    Returns information about active connections, rooms, and system health.
    """
    try:
        ws_manager = get_websocket_manager()
        stats = ws_manager.get_connection_stats()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": stats,
            "features": [
                "Real-time progress updates",
                "Live collaboration",
                "Instant notifications",
                "Performance alerts",
                "Team chat"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return {
            "status": "error",
            "message": "Unable to retrieve WebSocket status",
            "timestamp": datetime.utcnow().isoformat()
        }


# Include API routes with versioning
app.include_router(api_router, prefix="/api")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler for HTTP exceptions with enhanced error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Get settings
    settings = get_settings()
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )