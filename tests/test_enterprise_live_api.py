"""
Live API tests for enterprise features using the running Docker containers.
These tests call the actual API endpoints to verify functionality.
"""

import os
import pytest
import requests
import json
from typing import Dict, Any

# Base URL for the running API
BASE_URL = os.getenv("LIVE_API_BASE_URL", "http://localhost:8000/api/v2")
RUN_LIVE_API_TESTS = os.getenv("RUN_LIVE_API_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_LIVE_API_TESTS,
    reason="Requires running enterprise API instance. Set RUN_LIVE_API_TESTS=1 to enable.",
)

class TestLiveExperimentsAPI:
    """Test suite for A/B testing and experiments endpoints using live API."""
    
    def test_get_user_variant_no_experiment(self):
        """Test getting user variant when no experiment exists."""
        url = f"{BASE_URL}/experiments/feature/nonexistent-flag/variant"
        params = {"user_id": "test123"}
        
        response = requests.get(url, params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feature_flag"] == "nonexistent-flag"
        assert data["user_id"] == "test123"
        assert data["variant"] == "control"
        assert data["experiment_id"] is None

    def test_track_experiment_event_no_experiment(self):
        """Test tracking event when no experiment exists."""
        url = f"{BASE_URL}/experiments/feature/nonexistent-flag/track"
        payload = {
            "user_id": "test123",
            "event_type": "conversion",
            "value": 1.0
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feature_flag"] == "nonexistent-flag"
        assert data["status"] == "no_active_experiment"

    def test_list_experiments_requires_admin(self):
        """Test that listing experiments requires admin access."""
        url = f"{BASE_URL}/experiments/"
        
        response = requests.get(url)
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_create_experiment_requires_admin(self):
        """Test that creating experiments requires admin access."""
        url = f"{BASE_URL}/experiments/"
        payload = {
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
        
        response = requests.post(url, json=payload)
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]


class TestLiveFeedbackAPI:
    """Test suite for feedback collection endpoints using live API."""
    
    def test_feedback_health_check(self):
        """Test feedback system health check."""
        url = f"{BASE_URL}/feedback/health"
        
        response = requests.get(url)
        # Feedback health check requires authentication
        assert response.status_code in [401, 403]

    def test_submit_feedback_requires_auth(self):
        """Test that submitting feedback requires authentication."""
        url = f"{BASE_URL}/feedback/"
        payload = {
            "feedback_type": "assessment_quality",
            "rating": 5,
            "comments": "Great assessment!"
        }
        
        response = requests.post(url, json=payload)
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_list_feedback_requires_admin(self):
        """Test that listing feedback requires admin access."""
        url = f"{BASE_URL}/feedback/"
        
        response = requests.get(url)
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]


class TestLiveQualityAPI:
    """Test suite for quality assurance endpoints using live API."""
    
    def test_quality_health_check(self):
        """Test quality system health check."""
        url = f"{BASE_URL}/quality/health"
        
        response = requests.get(url)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["quality_metrics"] == "operational"

    def test_submit_quality_metric_requires_admin(self):
        """Test that submitting quality metrics requires admin access."""
        url = f"{BASE_URL}/quality/metrics"
        payload = {
            "target_type": "assessment",
            "target_id": "test123",
            "metric_name": "completeness",
            "metric_value": 85.5,
            "quality_score": 85.5
        }
        
        response = requests.post(url, json=payload)
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]


class TestLiveIntegration:
    """Integration tests for enterprise features using live API."""
    
    def test_enterprise_features_in_api_versions(self):
        """Test that enterprise features are listed in API versions."""
        url = "http://localhost:8000/api/versions"
        
        response = requests.get(url)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that v2 API includes enterprise endpoints
        v2_api = next((api for api in data["supported_versions"] if api["version"] == "v2"), None)
        assert v2_api is not None
        
        endpoints = v2_api["endpoints"]
        assert "/experiments" in endpoints
        assert "/feedback" in endpoints
        assert "/quality" in endpoints

    def test_openapi_schema_includes_enterprise(self):
        """Test that OpenAPI schema includes enterprise endpoints."""
        url = "http://localhost:8000/openapi.json"
        
        response = requests.get(url)
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


class TestLiveRoleBasedAccess:
    """Test role-based access control for enterprise features using live API."""
    
    def test_admin_endpoints_reject_regular_users(self):
        """Test that admin endpoints properly reject regular users."""
        # List of admin-only endpoints to test
        admin_endpoints = [
            ("GET", f"{BASE_URL}/experiments/"),
            ("POST", f"{BASE_URL}/experiments/"),
            ("GET", f"{BASE_URL}/feedback/"),
            ("GET", f"{BASE_URL}/quality/overview"),
            ("POST", f"{BASE_URL}/quality/metrics")
        ]
        
        for method, url in admin_endpoints:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json={})
            
            # Should return 401 (not authenticated) or 403 (forbidden)
            assert response.status_code in [401, 403], f"Endpoint {method} {url} should require authentication"

    def test_user_endpoints_work_without_admin(self):
        """Test that user-level endpoints work without admin privileges."""
        # Endpoints that should work for regular users without authentication
        public_user_endpoints = [
            f"{BASE_URL}/experiments/feature/test-flag/variant?user_id=test123",
            f"{BASE_URL}/quality/health"
        ]
        
        for url in public_user_endpoints:
            response = requests.get(url)
            # These should work (200) without authentication
            assert response.status_code == 200, f"Endpoint {url} should be accessible without authentication"
        
        # Endpoints that require authentication but are not admin-only
        auth_user_endpoints = [
            f"{BASE_URL}/feedback/health"
        ]
        
        for url in auth_user_endpoints:
            response = requests.get(url)
            # These should require authentication (401/403)
            assert response.status_code in [401, 403], f"Endpoint {url} should require authentication"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
