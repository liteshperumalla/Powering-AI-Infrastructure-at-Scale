"""
Main API Gateway for Infra Mind.

This FastAPI application serves as the primary API gateway for the Infra Mind
multi-agent advisory platform, providing REST endpoints for frontend integration.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infra_mind.api.routes import api_router
from infra_mind.core.database import init_database, close_database
from infra_mind.core.config import get_settings


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
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Infra Mind API Gateway...")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Infra Mind API",
    description="AI-powered infrastructure advisory platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Infra Mind API",
        version="1.0.0",
        description="""
        ## Infra Mind API Gateway
        
        AI-powered infrastructure advisory platform that coordinates specialized AI agents
        to provide comprehensive infrastructure recommendations, compliance guidance, and
        strategic roadmaps for enterprises scaling their AI initiatives.
        
        ### Key Features
        - **Multi-Agent Orchestration**: Coordinate specialized AI agents (CTO, Cloud Engineer, Research)
        - **Cloud Service Integration**: Real-time data from AWS, Azure, and GCP APIs
        - **Professional Reports**: Generate executive summaries and technical roadmaps
        - **Compliance Guidance**: GDPR, HIPAA, and CCPA compliance recommendations
        
        ### Authentication
        Most endpoints require JWT authentication. Use the `/auth/login` endpoint to obtain a token.
        
        ### Rate Limiting
        API calls are rate-limited to ensure fair usage and system stability.
        """,
        routes=app.routes,
    )
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "Assessments", 
            "description": "Infrastructure assessment management"
        },
        {
            "name": "Recommendations",
            "description": "AI agent recommendations and multi-cloud suggestions"
        },
        {
            "name": "Reports",
            "description": "Report generation and export functionality"
        },
        {
            "name": "Health",
            "description": "System health and monitoring endpoints"
        }
    ]
    
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


# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Infra Mind API Gateway",
        "version": "1.0.0",
        "description": "AI-powered infrastructure advisory platform",
        "docs_url": "/docs",
        "health_url": "/health"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


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