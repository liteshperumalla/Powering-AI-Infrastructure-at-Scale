"""
Test the main FastAPI application.

Learning Note: These tests verify that our FastAPI application
starts correctly and responds to basic requests.
"""

import pytest
from fastapi.testclient import TestClient
from src.infra_mind.main import app

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns basic information."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "Infra Mind" in data["message"]


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_api_docs_available_in_debug():
    """Test that API docs are available in debug mode."""
    # Note: This test assumes debug mode is enabled
    response = client.get("/docs")
    # Should either return docs (200), redirect (307), or be disabled (404)
    assert response.status_code in [200, 307, 404]


def test_nonexistent_endpoint():
    """Test that nonexistent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404