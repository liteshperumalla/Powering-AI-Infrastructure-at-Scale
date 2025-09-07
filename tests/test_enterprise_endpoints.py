"""
Tests for enterprise features: experiments, feedback, and quality endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import asyncio
from datetime import datetime
import uuid
import os
from unittest.mock import patch, AsyncMock

# Import the main app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infra_mind.main import create_app
from src.infra_mind.models.experiment import Experiment, ExperimentVariant, ExperimentStatus, VariantType
from src.infra_mind.models.feedback import UserFeedback, FeedbackType, FeedbackChannel, SentimentScore
from src.infra_mind.models.feedback import QualityMetric
from src.infra_mind.models.user import User


class TestExperimentsEndpoints:
    """Test suite for A/B testing and experiments endpoints."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self):
        """Mock admin JWT token for testing."""
        # In a real test, you'd create a proper token
        return "mock-admin-token"
    
    @pytest.fixture
    def user_token(self):
        """Mock user JWT token for testing."""
        return "mock-user-token"

    @patch('src.infra_mind.models.experiment.Experiment.find_one', return_value=AsyncMock(return_value=None))
    def test_get_user_variant_no_experiment(self, mock_find_one, client):
        """Test getting user variant when no experiment exists."""
        response = client.get(
            "/api/v2/experiments/feature/nonexistent-flag/variant?user_id=test123"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feature_flag"] == "nonexistent-flag"
        assert data["user_id"] == "test123"
        assert data["variant"] == "control"
        assert data["experiment_id"] is None

    @patch('src.infra_mind.models.experiment.Experiment.find_one', return_value=AsyncMock(return_value=None))
    def test_track_experiment_event_no_experiment(self, mock_find_one, client):
        """Test tracking event when no experiment exists."""
        response = client.post(
            "/api/v2/experiments/feature/nonexistent-flag/track",
            json={
                "user_id": "test123",
                "event_type": "conversion",
                "value": 1.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feature_flag"] == "nonexistent-flag"
        assert data["status"] == "no_active_experiment"

    def test_list_experiments_requires_admin(self, client):
        """Test that listing experiments requires admin access."""
        response = client.get("/api/v2/experiments/")
        assert response.status_code == 401  # Not authenticated

    def test_create_experiment_requires_admin(self, client):
        """Test that creating experiments requires admin access."""
        response = client.post(
            "/api/v2/experiments/",
            json={
                "name": "Test Experiment",
                "description": "Test description",
                "feature_flag": "test-flag",
                "target_metric": "conversion_rate",
                "variants": [
                    {
                        "name": "control",
                        "type": "control",
                        "traffic_percentage": 50
                    },
                    {
                        "name": "treatment",
                        "type": "treatment", 
                        "traffic_percentage": 50
                    }
                ]
            }
        )
        assert response.status_code == 401  # Not authenticated

    def test_get_dashboard_data_requires_admin(self, client):
        """Test that dashboard data requires admin access."""
        response = client.get("/api/v2/experiments/dashboard/data")
        assert response.status_code == 401  # Not authenticated


class TestFeedbackEndpoints:
    """Test suite for feedback collection and analysis endpoints."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_feedback_health_check(self, client):
        """Test feedback system health check."""
        response = client.get("/api/v2/feedback/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["feedback_collection"] == "operational"

    def test_submit_feedback_requires_auth(self, client):
        """Test that submitting feedback requires authentication."""
        response = client.post(
            "/api/v2/feedback/",
            json={
                "feedback_type": "assessment_quality",
                "rating": 5,
                "comments": "Great assessment!"
            }
        )
        assert response.status_code == 401  # Not authenticated

    def test_list_feedback_requires_admin(self, client):
        """Test that listing feedback requires admin access."""
        response = client.get("/api/v2/feedback/")
        assert response.status_code == 401  # Not authenticated

    def test_feedback_analytics_requires_admin(self, client):
        """Test that feedback analytics require admin access."""
        response = client.get("/api/v2/feedback/analytics/dashboard")
        assert response.status_code == 401  # Not authenticated

    def test_feedback_summary_requires_admin(self, client):
        """Test that feedback summary requires admin access."""
        response = client.get("/api/v2/feedback/summary/period?days=7")
        assert response.status_code == 401  # Not authenticated


class TestQualityEndpoints:
    """Test suite for quality assurance endpoints."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_quality_health_check(self, client):
        """Test quality system health check."""
        response = client.get("/api/v2/quality/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["quality_metrics"] == "operational"

    def test_submit_quality_metric_requires_admin(self, client):
        """Test that submitting quality metrics requires admin access."""
        response = client.post(
            "/api/v2/quality/metrics",
            json={
                "target_type": "assessment",
                "target_id": "test123",
                "metric_name": "completeness",
                "metric_value": 85.5,
                "quality_score": 85.5
            }
        )
        assert response.status_code == 401  # Not authenticated

    def test_get_quality_metrics_requires_admin(self, client):
        """Test that getting quality metrics requires admin access."""
        response = client.get("/api/v2/quality/metrics/test123?target_type=assessment")
        assert response.status_code == 401  # Not authenticated

    def test_quality_overview_requires_admin(self, client):
        """Test that quality overview requires admin access."""
        response = client.get("/api/v2/quality/overview")
        assert response.status_code == 401  # Not authenticated

    def test_quality_trends_requires_admin(self, client):
        """Test that quality trends require admin access."""
        response = client.get("/api/v2/quality/trends?days=30")
        assert response.status_code == 401  # Not authenticated


class TestRoleBasedAccess:
    """Test role-based access control for enterprise features."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_admin_endpoints_reject_regular_users(self, client):
        """Test that admin endpoints properly reject regular users."""
        # List of admin-only endpoints to test
        admin_endpoints = [
            "GET /api/v2/experiments/",
            "POST /api/v2/experiments/",
            "GET /api/v2/experiments/dashboard/data",
            "GET /api/v2/feedback/",
            "GET /api/v2/feedback/analytics/dashboard",
            "GET /api/v2/quality/overview",
            "POST /api/v2/quality/metrics"
        ]
        
        for endpoint_info in admin_endpoints:
            method, url = endpoint_info.split(" ", 1)
            
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json={})
            
            # Should return 401 (not authenticated) since we're not providing tokens
            assert response.status_code == 401, f"Endpoint {endpoint_info} should require authentication"

    def test_user_endpoints_work_without_admin(self, client):
        """Test that user-level endpoints work without admin privileges."""
        # Endpoints that should work for regular users (though may require basic auth)
        user_endpoints = [
            "/api/v2/experiments/feature/test-flag/variant?user_id=test123",
            "/api/v2/quality/health",
            "/api/v2/feedback/health"
        ]
        
        for url in user_endpoints:
            response = client.get(url)
            # These should either work (200) or require basic auth (401), not forbidden (403)
            assert response.status_code in [200, 401], f"Endpoint {url} should be accessible to users"


class TestAssessmentLevelFeatures:
    """Test assessment-level enterprise features for general users."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_assessment_feedback_requires_auth(self, client):
        """Test that assessment feedback requires authentication."""
        response = client.post(
            "/api/v2/assessments/test123/feedback",
            json={
                "type": "general",
                "rating": 4,
                "comments": "Good assessment"
            }
        )
        assert response.status_code == 401  # Not authenticated

    def test_assessment_quality_score_requires_auth(self, client):
        """Test that assessment quality score requires authentication."""
        response = client.get("/api/v2/assessments/test123/quality-score")
        assert response.status_code == 401  # Not authenticated

    def test_assessment_export_requires_auth(self, client):
        """Test that assessment export requires authentication."""
        response = client.post(
            "/api/v2/assessments/test123/integrations/export",
            json={
                "service_type": "slack",
                "format": "summary"
            }
        )
        assert response.status_code == 401  # Not authenticated

    def test_assessment_experiment_insights_requires_auth(self, client):
        """Test that assessment experiment insights require authentication."""
        response = client.get("/api/v2/assessments/test123/experiment-insights")
        assert response.status_code == 401  # Not authenticated

    def test_assessment_quick_improvements_requires_auth(self, client):
        """Test that assessment quick improvements require authentication."""
        response = client.post(
            "/api/v2/assessments/test123/quick-improvements",
            json={
                "focus_area": "all",
                "urgency": "medium"
            }
        )
        assert response.status_code == 401  # Not authenticated


class TestEnterpriseIntegration:
    """Integration tests for enterprise features."""
    
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_enterprise_features_in_api_versions(self, client):
        """Test that enterprise features are listed in API versions."""
        response = client.get("/api/versions")
        assert response.status_code == 200
        data = response.json()
        
        # Check that v2 API includes enterprise endpoints
        v2_api = next((api for api in data["supported_versions"] if api["version"] == "v2"), None)
        assert v2_api is not None
        
        endpoints = v2_api["endpoints"]
        assert "/experiments" in endpoints
        assert "/feedback" in endpoints
        assert "/quality" in endpoints

    def test_openapi_schema_includes_enterprise(self, client):
        """Test that OpenAPI schema includes enterprise endpoints."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        
        # Check that enterprise endpoints are in the schema
        paths = schema.get("paths", {})
        experiment_paths = [path for path in paths.keys() if "/experiments" in path]
        feedback_paths = [path for path in paths.keys() if "/feedback" in path]
        quality_paths = [path for path in paths.keys() if "/quality" in path]
        
        assert len(experiment_paths) > 0, "Experiments endpoints should be in OpenAPI schema"
        assert len(feedback_paths) > 0, "Feedback endpoints should be in OpenAPI schema"
        assert len(quality_paths) > 0, "Quality endpoints should be in OpenAPI schema"


# Pytest configuration for running these tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])