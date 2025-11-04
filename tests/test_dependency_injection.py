"""
Unit tests for Dependency Injection implementation.

Tests the new dependency injection pattern for:
- LLM managers
- Database connections
- Event managers

Demonstrates how to mock dependencies for testing.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra_mind.main import create_app
from src.infra_mind.core.dependencies import (
    get_llm_manager,
    get_database,
    get_event_manager,
    clear_dependency_cache
)
from src.infra_mind.llm.enhanced_llm_manager import EnhancedLLMManager, LLMResponse
from src.infra_mind.orchestration.events import EventManager, AgentEvent, EventType


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_dependencies():
    """Clear dependency cache before each test."""
    clear_dependency_cache()
    yield
    clear_dependency_cache()


# =============================================================================
# LLM Manager Dependency Injection Tests
# =============================================================================

def test_llm_manager_injection(app, client):
    """Test that LLM manager can be injected and mocked."""

    # Create mock LLM manager
    mock_llm = AsyncMock(spec=EnhancedLLMManager)
    mock_llm.generate.return_value = LLMResponse(
        content="Dependency injection is working perfectly!",
        tokens_used=8,
        model_used="gpt-4",
        sanitization_applied=True,
        budget_validated=True,
        json_validated=False,
        warnings=[],
        success=True
    )

    # Override dependency
    app.dependency_overrides[get_llm_manager] = lambda: mock_llm

    # Mock authentication
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.id = "test_user_123"

    from src.infra_mind.api.endpoints.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Test endpoint
    response = client.post("/api/v1/di-example/test-llm")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"] == "test@example.com"
    assert "Dependency injection" in data["llm_response"]["content"]
    assert data["injection_method"] == "LLMManagerDep (FastAPI Depends)"

    # Verify mock was called
    assert mock_llm.generate.called

    # Cleanup
    app.dependency_overrides.clear()


def test_llm_manager_real_instance():
    """Test that real LLM manager instance can be created."""
    manager = get_llm_manager()

    assert isinstance(manager, EnhancedLLMManager)
    assert manager.default_model in ["gpt-4", "gpt-3.5-turbo"]
    assert manager.strict_mode is True


# =============================================================================
# Database Dependency Injection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_database_injection(app, client):
    """Test that database can be injected and mocked."""

    # Create mock database
    mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
    mock_db.list_collection_names.return_value = [
        "assessments", "users", "recommendations"
    ]
    mock_db.assessments.count_documents.return_value = 5
    mock_db.assessments.find.return_value.limit.return_value.to_list.return_value = []

    # Override dependency
    app.dependency_overrides[get_database] = lambda: mock_db

    # Mock authentication
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.id = "test_user_123"

    from src.infra_mind.api.endpoints.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Test endpoint
    response = client.get("/api/v1/di-example/test-database")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["database_stats"]["total_collections"] == 3
    assert data["database_stats"]["user_assessments"] == 5
    assert data["injection_method"] == "DatabaseDep (FastAPI Depends)"

    # Verify mock was called
    assert mock_db.list_collection_names.called
    assert mock_db.assessments.count_documents.called

    # Cleanup
    app.dependency_overrides.clear()


def test_database_health_check(app, client):
    """Test database health check endpoint."""

    # Create mock database
    mock_db = AsyncMock()
    mock_db.list_collection_names.return_value = ["test1", "test2", "test3"]

    # Create mock event manager
    mock_event_manager = MagicMock()

    # Override dependencies
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_event_manager] = lambda: mock_event_manager

    # Test endpoint
    response = client.get("/api/v1/di-example/health")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dependencies"]["database"]["status"] == "connected"
    assert data["dependencies"]["database"]["collections"] == 3

    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Event Manager Dependency Injection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_event_manager_injection(app, client):
    """Test that event manager can be injected and mocked."""

    # Create mock event manager
    mock_event_manager = AsyncMock(spec=EventManager)
    mock_event_manager.publish = AsyncMock()
    mock_event_manager.get_event_history = AsyncMock(return_value=[])
    mock_event_manager.__class__.__name__ = "MockEventManager"

    # Override dependency
    app.dependency_overrides[get_event_manager] = lambda: mock_event_manager

    # Mock authentication
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.id = "test_user_123"

    from src.infra_mind.api.endpoints.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Test endpoint
    response = client.post("/api/v1/di-example/test-events")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event_published"]["broadcast"] == "ALL API instances received this event!"
    assert data["event_manager_type"] == "MockEventManager"

    # Verify mock was called
    assert mock_event_manager.publish.called

    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Comprehensive Tests with Multiple Dependencies
# =============================================================================

@pytest.mark.asyncio
async def test_all_dependencies_injection(app, client):
    """Test endpoint using all three dependency types."""

    # Create mocks for all dependencies
    mock_llm = AsyncMock(spec=EnhancedLLMManager)
    mock_llm.generate.return_value = LLMResponse(
        content="User has good assessment activity!",
        tokens_used=10,
        model_used="gpt-4",
        sanitization_applied=True,
        budget_validated=True,
        json_validated=False,
        warnings=[],
        success=True
    )

    mock_db = AsyncMock()
    mock_db.assessments.count_documents.return_value = 10

    mock_event_manager = AsyncMock(spec=EventManager)
    mock_event_manager.publish = AsyncMock()
    mock_event_manager.__class__.__name__ = "EventManager"

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.id = "test_user_123"

    # Override all dependencies
    app.dependency_overrides[get_llm_manager] = lambda: mock_llm
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_event_manager] = lambda: mock_event_manager

    from src.infra_mind.api.endpoints.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Test endpoint
    response = client.post("/api/v1/di-example/test-all-dependencies")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["workflow_steps"]["1_database_query"]["assessment_count"] == 10
    assert data["workflow_steps"]["2_llm_analysis"]["injection"] == "LLMManagerDep"
    assert data["workflow_steps"]["3_event_published"]["injection"] == "EventManagerDep"

    # Verify all mocks were called
    assert mock_db.assessments.count_documents.called
    assert mock_llm.generate.called
    assert mock_event_manager.publish.called

    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Migration Guide Tests
# =============================================================================

def test_migration_guide_endpoint(client):
    """Test migration guide endpoint."""
    response = client.get("/api/v1/di-example/migration-guide")

    assert response.status_code == 200
    data = response.json()
    assert "old_pattern" in data
    assert "new_pattern" in data
    assert "migration_steps" in data
    assert "testing_pattern" in data
    assert len(data["benefits"]) > 0
    assert "references" in data


# =============================================================================
# Dependency Cache Tests
# =============================================================================

def test_dependency_cache_clear():
    """Test that dependency cache can be cleared."""
    from src.infra_mind.core.dependencies import get_cached_llm_manager

    # Get instance (cached)
    instance1 = get_cached_llm_manager()

    # Get again (should be same instance)
    instance2 = get_cached_llm_manager()
    assert instance1 is instance2  # Same instance (cached)

    # Clear cache
    clear_dependency_cache()

    # Get again (should be new instance)
    instance3 = get_cached_llm_manager()
    assert instance1 is not instance3  # Different instance (cache cleared)


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_dependency_injection_with_authentication_failure(app, client):
    """Test that authentication is still enforced with DI."""

    # Don't override authentication - should fail

    response = client.post("/api/v1/di-example/test-llm")

    # Should return 401 Unauthorized (authentication required)
    assert response.status_code == 401


# =============================================================================
# Integration Tests (requires actual services)
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_database_connection():
    """Test real database connection (integration test)."""
    # This test requires MongoDB to be running
    db = await get_database()

    assert db is not None
    assert db.name == "infra_mind" or db.name.startswith("test")

    # Test basic operation
    collections = await db.list_collection_names()
    assert isinstance(collections, list)


@pytest.mark.integration
def test_real_llm_manager():
    """Test real LLM manager instance (integration test)."""
    manager = get_llm_manager()

    assert manager is not None
    assert isinstance(manager, EnhancedLLMManager)
    assert manager.default_model is not None


# =============================================================================
# Performance Tests
# =============================================================================

def test_dependency_injection_overhead():
    """Test that DI doesn't add significant overhead."""
    import time

    # Test uncached instance creation
    start = time.time()
    for _ in range(100):
        manager = get_llm_manager()
    uncached_time = time.time() - start

    # Should be fast (< 1 second for 100 instantiations)
    assert uncached_time < 1.0

    # Test cached instance retrieval
    from src.infra_mind.core.dependencies import get_cached_llm_manager

    start = time.time()
    for _ in range(100):
        manager = get_cached_llm_manager()
    cached_time = time.time() - start

    # Should be very fast (< 0.01 seconds for 100 retrievals)
    assert cached_time < 0.01

    # Cached should be significantly faster
    assert cached_time < uncached_time / 10


# =============================================================================
# Documentation Tests
# =============================================================================

def test_dependency_types_have_annotations():
    """Test that dependency types are properly annotated."""
    from src.infra_mind.core.dependencies import (
        LLMManagerDep,
        DatabaseDep,
        EventManagerDep
    )

    # These should be type aliases (Annotated types)
    assert LLMManagerDep is not None
    assert DatabaseDep is not None
    assert EventManagerDep is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
