"""
API package for Infra Mind.

Contains all FastAPI routers and API-related functionality.
"""

from fastapi import APIRouter
from .auth import router as auth_router

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router)

__all__ = ["api_router"]