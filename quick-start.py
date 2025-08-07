#!/usr/bin/env python3
"""
Quick start script for Infra Mind API
This script provides a minimal FastAPI application to get the system running quickly
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Create FastAPI app
app = FastAPI(
    title="Infra Mind API",
    description="AI-powered infrastructure advisory platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "services": {
            "api": "healthy",
            "database": "not_connected",
            "redis": "not_connected"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Infra Mind API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# Mock authentication endpoints
@app.post("/api/v2/auth/login")
async def mock_login(credentials: dict):
    """Mock login endpoint"""
    return {
        "access_token": "mock-token-12345",
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": "user-123",
        "email": credentials.get("email", "user@example.com"),
        "full_name": "Demo User"
    }

@app.post("/api/v2/auth/register")
async def mock_register(user_data: dict):
    """Mock register endpoint"""
    return {
        "access_token": "mock-token-12345",
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": "user-123",
        "email": user_data.get("email", "user@example.com"),
        "full_name": user_data.get("full_name", "Demo User")
    }

@app.get("/api/v2/auth/profile")
async def mock_profile():
    """Mock profile endpoint"""
    return {
        "id": "user-123",
        "email": "user@example.com",
        "full_name": "Demo User",
        "company": "Demo Company",
        "role": "user",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }

# Mock assessments endpoint
@app.get("/api/v2/assessments/")
async def mock_assessments():
    """Mock assessments endpoint"""
    return {
        "assessments": [],
        "total": 0,
        "page": 1,
        "limit": 10,
        "pages": 0
    }

@app.post("/api/v2/assessments")
async def mock_create_assessment(assessment_data: dict):
    """Mock create assessment endpoint"""
    return {
        "id": "assessment-123",
        "title": assessment_data.get("title", "Demo Assessment"),
        "status": "draft",
        "progress_percentage": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

# Mock reports endpoint
@app.get("/api/v2/reports")
async def mock_reports():
    """Mock reports endpoint"""
    return []

# Mock cloud services endpoint
@app.get("/api/v2/cloud-services")
async def mock_cloud_services():
    """Mock cloud services endpoint"""
    return {
        "services": [
            {
                "id": "service-1",
                "name": "AWS EC2",
                "provider": "AWS",
                "category": "Compute",
                "description": "Virtual servers in the cloud",
                "pricing": {
                    "model": "hourly",
                    "starting_price": 0.0058,
                    "unit": "hour"
                },
                "features": ["Scalable", "Secure", "Reliable"],
                "rating": 4.5,
                "compliance": ["SOC2", "ISO27001"],
                "region_availability": ["us-east-1", "us-west-2"]
            }
        ],
        "pagination": {
            "total": 1,
            "limit": 10,
            "offset": 0,
            "has_more": False
        },
        "filters": {}
    }

# Mock system metrics endpoint
@app.get("/api/v2/admin/metrics")
async def mock_metrics():
    """Mock metrics endpoint"""
    return {
        "active_connections": 5,
        "active_workflows": 2,
        "system_load": 0.3,
        "response_time_avg": 150
    }

# Mock chat endpoints
@app.post("/api/v2/chat/conversations")
async def mock_create_conversation(request: dict):
    """Mock create conversation endpoint"""
    return {
        "id": "conv-123",
        "title": request.get("title", "New Conversation"),
        "status": "active",
        "context": request.get("context", "general"),
        "messages": [],
        "message_count": 0,
        "started_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
        "escalated": False,
        "total_tokens_used": 0,
        "topics_discussed": []
    }

@app.get("/api/v2/chat/conversations")
async def mock_get_conversations():
    """Mock get conversations endpoint"""
    return {
        "conversations": [],
        "total": 0,
        "page": 1,
        "limit": 10,
        "has_more": False
    }

# Add a catch-all for missing endpoints
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path: str):
    """Catch-all endpoint for missing routes"""
    return {
        "message": f"Endpoint /{path} is not implemented yet",
        "status": "mock_response",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Infra Mind Quick Start API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🌐 CORS enabled for: http://localhost:3000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )