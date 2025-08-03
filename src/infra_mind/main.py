"""
Main FastAPI application for Infra Mind.

This is the entry point for the web API, showcasing modern FastAPI patterns
including async operations, dependency injection, and automatic documentation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import json
from loguru import logger

from .core.config import settings
from .core.database import init_database, close_database
from .core.logging import setup_logging
from .api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Learning Note: This is the modern way to handle startup/shutdown events
    in FastAPI. It replaces the old @app.on_event decorators.
    """
    # Startup
    logger.info("🚀 Starting Infra Mind application...")
    
    # Initialize logging
    setup_logging()
    
    # Initialize database
    await init_database()
    
    logger.success("✅ Application startup complete")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down Infra Mind application...")
    await close_database()
    logger.success("✅ Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Learning Note: Factory pattern for creating the app allows for
    better testing and configuration management.
    """
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered infrastructure advisory platform with multi-agent recommendations",
        docs_url="/docs" if settings.debug else None,  # Disable docs in production
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    app.include_router(api_router, prefix=settings.api_prefix)
    
    # Add WebSocket endpoint
    setup_websocket(app)
    
    # Add custom exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_websocket(app: FastAPI) -> None:
    """
    Configure WebSocket endpoints.
    """
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, token: str = None):
        """
        General WebSocket endpoint for real-time updates.
        """
        try:
            await websocket.accept()
            logger.info(f"WebSocket connection accepted with token: {token[:20] if token else 'None'}...")
            
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "message": "Connected to Infra Mind WebSocket",
                "authenticated": token is not None,
                "timestamp": time.time()
            }))
            
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Echo back for now - this can be extended with proper message handling
                    response = {
                        "type": "echo",
                        "received": message,
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(response))
                    
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected")
                    break
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": time.time()
                    }))
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time()
                    }))
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.
    
    Learning Note: Middleware runs for every request/response.
    Order matters - they execute in the order they're added.
    """
    
    # CORS middleware - must be added before other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.inframind.ai", "inframind.ai"]
        )
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add request processing time to response headers."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
            )
        
        return response


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure custom exception handlers.
    
    Learning Note: Custom exception handlers provide consistent
    error responses and better user experience.
    """
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors."""
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation Error",
                "message": str(exc),
                "type": "validation_error"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        
        if settings.debug:
            # In debug mode, return detailed error information
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc),
                    "type": type(exc).__name__
                }
            )
        else:
            # In production, return generic error message
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": "internal_error"
                }
            )


# Create the application instance
app = create_app()


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Learning Note: Health checks are essential for production deployments.
    They allow load balancers and monitoring systems to check if the app is running.
    """
    from .core.database import get_database_info
    
    db_info = await get_database_info()
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_info,
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }