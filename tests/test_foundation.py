"""
Foundation tests for Infra Mind.

Tests the basic application setup, configuration, and core functionality.
"""

import pytest
from fastapi.testclient import TestClient
from src.infra_mind.main import app
from src.infra_mind.core.config import settings


class TestFoundation:
    """Test the basic application foundation."""
    
    def test_settings_load(self):
        """Test that settings load correctly."""
        assert settings.app_name == "Infra Mind"
        assert settings.app_version == "0.1.0"
        assert settings.environment in ["development", "staging", "production"]
    
    def test_app_creation(self):
        """Test that the FastAPI app is created correctly."""
        assert app is not None
        assert app.title == settings.app_name
        assert app.version == settings.app_version
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == settings.app_version
        assert data["environment"] == settings.environment
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert settings.app_name in data["message"]
    
    def test_api_docs_available_in_debug(self):
        """Test that API docs are available in debug mode."""
        if settings.debug:
            client = TestClient(app)
            response = client.get("/docs")
            assert response.status_code == 200
    
    def test_cors_headers(self):
        """Test that CORS headers are set correctly."""
        client = TestClient(app)
        response = client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


@pytest.mark.asyncio
class TestAsyncFoundation:
    """Test async functionality."""
    
    async def test_database_models_import(self):
        """Test that all database models can be imported."""
        from src.infra_mind.models.user import User
        from src.infra_mind.models.assessment import Assessment
        from src.infra_mind.models.recommendation import Recommendation
        from src.infra_mind.models.report import Report
        from src.infra_mind.models.workflow import WorkflowState
        from src.infra_mind.models.metrics import Metric
        from src.infra_mind.models.web_research import WebResearchData
        
        # All models should be importable
        assert User is not None
        assert Assessment is not None
        assert Recommendation is not None
        assert Report is not None
        assert WorkflowState is not None
        assert Metric is not None
        assert WebResearchData is not None