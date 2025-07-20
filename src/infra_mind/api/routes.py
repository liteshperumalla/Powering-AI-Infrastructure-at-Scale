"""
Main API router for Infra Mind.

Combines all API routes into a single router for the main application.
"""

from fastapi import APIRouter
from .endpoints import auth, assessments, recommendations, reports

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    assessments.router,
    prefix="/assessments",
    tags=["Assessments"]
)

api_router.include_router(
    recommendations.router,
    prefix="/recommendations", 
    tags=["Recommendations"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)