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
import asyncio
from loguru import logger

from .core.config import settings
from .core.database import init_database, close_database
from .core.logging import setup_logging
from .api.routes import api_router
from .orchestration.events import EventManager
from .orchestration.monitoring import initialize_workflow_monitoring


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
    
    # Initialize EventManager and workflow monitoring
    logger.info("📡 Initializing EventManager and workflow monitoring...")
    event_manager = EventManager()
    await initialize_workflow_monitoring(event_manager)
    logger.success("✅ EventManager and workflow monitoring initialized")
    
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
    app.include_router(api_router, prefix="/api")
    
    # Add WebSocket endpoint
    setup_websocket(app)
    
    # Add custom exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_websocket(app: FastAPI) -> None:
    """
    Configure WebSocket endpoints.
    """
    
    # Store active WebSocket connections
    websocket_connections = {}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, token: str = None):
        """
        General WebSocket endpoint for real-time updates.
        """
        connection_id = f"conn_{int(time.time())}_{id(websocket)}"
        
        try:
            await websocket.accept()
            logger.info(f"WebSocket connection accepted with token: {token[:20] if token else 'None'}...")
            
            # Store connection for broadcasting
            websocket_connections[connection_id] = {
                "websocket": websocket,
                "token": token,
                "connected_at": time.time()
            }
            
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "message": "Connected to Infra Mind WebSocket",
                "authenticated": token is not None,
                "connection_id": connection_id,
                "timestamp": time.time()
            }))
            
            try:
                while True:
                    # Wait for messages from client with timeout to prevent hanging
                    try:
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        message = json.loads(data)
                        
                        logger.info(f"Received WebSocket message: {message}")
                        
                        # Handle different message types
                        if message.get("type") == "heartbeat":
                            await websocket.send_text(json.dumps({
                                "type": "heartbeat_response",
                                "timestamp": time.time()
                            }))
                        elif message.get("type") == "subscribe":
                            # Handle workflow/assessment subscription
                            data = message.get("data", {})
                            workflow_id = data.get("workflow_id")
                            assessment_id = data.get("assessment_id")
                            
                            if workflow_id:
                                websocket_connections[connection_id]["subscribed_workflow"] = workflow_id
                                await websocket.send_text(json.dumps({
                                    "type": "subscription_confirmed",
                                    "workflow_id": workflow_id,
                                    "timestamp": time.time()
                                }))
                            elif assessment_id:
                                websocket_connections[connection_id]["subscribed_assessment"] = assessment_id
                                await websocket.send_text(json.dumps({
                                    "type": "subscription_confirmed",
                                    "assessment_id": assessment_id,
                                    "timestamp": time.time()
                                }))
                        else:
                            # Echo back other messages
                            response = {
                                "type": "echo",
                                "received": message,
                                "timestamp": time.time()
                            }
                            await websocket.send_text(json.dumps(response))
                            
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send_text(json.dumps({
                            "type": "ping",
                            "timestamp": time.time()
                        }))
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
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
        finally:
            # Clean up connection
            if connection_id in websocket_connections:
                del websocket_connections[connection_id]
                logger.info(f"Cleaned up WebSocket connection: {connection_id}")
    
    # Helper function to broadcast workflow updates
    async def broadcast_workflow_update(assessment_id: str, update_data: dict):
        """Broadcast workflow updates to subscribed clients."""
        if not websocket_connections:
            return
            
        message = json.dumps({
            "type": "workflow_progress",
            "assessment_id": assessment_id,
            "data": update_data,
            "timestamp": time.time()
        })
        
        # Send to all subscribed connections
        disconnected = []
        for conn_id, conn_info in websocket_connections.items():
            try:
                # Send to connections subscribed to this assessment or workflow
                subscribed_assessment = conn_info.get("subscribed_assessment")
                subscribed_workflow = conn_info.get("subscribed_workflow")
                workflow_id = update_data.get("workflow_id")
                
                if (subscribed_assessment == assessment_id or 
                    (workflow_id and subscribed_workflow == workflow_id)):
                    await conn_info["websocket"].send_text(message)
            except Exception as e:
                logger.error(f"Failed to send to WebSocket {conn_id}: {e}")
                disconnected.append(conn_id)
        
        # Clean up disconnected connections
        for conn_id in disconnected:
            websocket_connections.pop(conn_id, None)
    
    # Make broadcast function available to other modules
    app.state.broadcast_workflow_update = broadcast_workflow_update


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