"""
Pytest configuration for Infra Mind tests.

Provides shared fixtures and skips integration tests unless
RUN_INTEGRATION_TESTS=1 is set.
"""

import os

# Ensure the application knows we're running under tests before any app imports
os.environ.setdefault("INFRA_MIND_TESTING", "1")

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra_mind.main import create_app
from src.infra_mind.core.dependencies import (
    get_database,
    get_event_manager,
    get_llm_manager,
)
from src.infra_mind.api.endpoints.auth import get_current_user
from src.infra_mind.orchestration.events import EventManager


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_INTEGRATION_TESTS") in {"1", "true", "True"}:
        return

    skip_integration = pytest.mark.skip(
        reason="integration test skipped (set RUN_INTEGRATION_TESTS=1 to run)"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncIOMotorDatabase)
    db.list_collection_names.return_value = ["assessments", "users"]
    db.command.return_value = {"ok": 1}
    assessments = AsyncMock()
    assessments.count_documents.return_value = 0
    find_cursor = AsyncMock()
    find_cursor.limit.return_value.to_list.return_value = []
    assessments.find.return_value = find_cursor
    db.assessments = assessments
    return db


@pytest.fixture
def mock_event_manager():
    manager = AsyncMock(spec=EventManager)
    manager.publish = AsyncMock()
    manager.get_event_history = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_llm_manager():
    manager = AsyncMock()
    manager.generate.return_value = AsyncMock()
    return manager


@pytest.fixture
def client(app, mock_db, mock_event_manager, mock_llm_manager):
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_event_manager] = lambda: mock_event_manager
    app.dependency_overrides[get_llm_manager] = lambda: mock_llm_manager
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    user = MagicMock()
    user.id = "admin-user"
    user.email = "admin@example.com"
    user.is_admin = True
    user.is_superuser = True
    user.role = "admin"
    return user


@pytest.fixture
def authenticated_client(client, app, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
