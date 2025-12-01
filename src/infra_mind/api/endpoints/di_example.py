"""
Example endpoint demonstrating Dependency Injection usage.

This endpoint shows how to use the new dependency injection pattern
for LLM managers, database connections, and event managers.

This is a reference implementation for migrating other endpoints.
"""

import logging
import inspect
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone

from ...core.dependencies import LLMManagerDep, DatabaseDep, EventManagerDep
from ...models.user import User
from ..endpoints.auth import get_current_user
from ...orchestration.events import EventType, AgentEvent
from ...llm.enhanced_llm_manager import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/di-example", tags=["Dependency Injection Example"])


async def _maybe_await(result):
    """Utility to handle sync or async call results."""
    if inspect.isawaitable(result):
        return await result
    return result


@router.get("/health")
async def di_health_check(
    db: DatabaseDep,
    event_manager: EventManagerDep
):
    """
    Health check endpoint demonstrating dependency injection.

    Tests:
    - Database connection via dependency injection
    - Event manager availability via dependency injection

    No authentication required for health check.
    """
    try:
        # Test database connection
        db_status = "connected"
        collection_names = await _maybe_await(db.list_collection_names())
        collection_count = len(collection_names)

        # Test event manager
        event_manager_status = "connected" if hasattr(event_manager, 'is_connected') else "in-memory"

        return {
            "status": "healthy",
            "dependencies": {
                "database": {
                    "status": db_status,
                    "collections": collection_count
                },
                "event_manager": {
                    "status": event_manager_status,
                    "type": event_manager.__class__.__name__
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/test-llm")
async def test_llm_manager(
    llm_manager: LLMManagerDep,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for LLM manager dependency injection.

    Demonstrates:
    - LLM manager injection
    - User authentication with Depends()
    - Error handling

    Requires authentication.
    """
    try:
        # Create test request
        request = LLMRequest(
            model="gpt-4",
            system_prompt="You are a helpful assistant testing dependency injection.",
            user_prompt="Say 'Dependency injection is working!' in exactly 5 words.",
            temperature=0.1,
            max_tokens=50
        )

        # Generate response
        response = await llm_manager.generate(request)

        return {
            "status": "success",
            "user": current_user.email,
            "llm_response": {
                "content": response.content,
                "tokens_used": response.tokens_used,
                "model": response.model_used,
                "warnings": response.warnings
            },
            "injection_method": "LLMManagerDep (FastAPI Depends)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"LLM test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM test failed: {str(e)}"
        )


@router.get("/test-database")
async def test_database(
    db: DatabaseDep,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for database dependency injection.

    Demonstrates:
    - Database injection
    - Query execution
    - User-scoped data access

    Requires authentication.
    """
    try:
        # Query user's assessments
        assessments_query = db.assessments.find({
            "user_id": str(current_user.id)
        }).limit(5).to_list(5)
        assessments = await _maybe_await(assessments_query)

        # Get collection stats
        collection_names = await _maybe_await(db.list_collection_names())
        collection_count = len(collection_names)
        assessment_count = await _maybe_await(db.assessments.count_documents({
            "user_id": str(current_user.id)
        }))

        return {
            "status": "success",
            "user": current_user.email,
            "database_stats": {
                "total_collections": collection_count,
                "user_assessments": assessment_count,
                "sample_assessments": len(assessments)
            },
            "injection_method": "DatabaseDep (FastAPI Depends)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database test failed: {str(e)}"
        )


@router.post("/test-events")
async def test_event_manager(
    event_manager: EventManagerDep,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for event manager dependency injection.

    Demonstrates:
    - Event manager injection
    - Event publishing (broadcasts to ALL API instances)
    - Event history retrieval

    Requires authentication.
    """
    try:
        # Publish test event
        test_event = AgentEvent(
            event_type=EventType.AGENT_STARTED,
            agent_name="di_test_agent",
            data={
                "user_id": str(current_user.id),
                "test": "dependency_injection",
                "message": "This event is broadcast to ALL API instances via Redis!"
            }
        )

        await event_manager.publish(test_event)

        # Get event history (if available)
        event_history = []
        if hasattr(event_manager, 'get_event_history'):
            event_history = await event_manager.get_event_history(limit=5)

        return {
            "status": "success",
            "user": current_user.email,
            "event_published": {
                "event_id": test_event.event_id,
                "event_type": test_event.event_type.value,
                "agent_name": test_event.agent_name,
                "broadcast": "ALL API instances received this event!"
            },
            "event_history_count": len(event_history),
            "injection_method": "EventManagerDep (FastAPI Depends)",
            "event_manager_type": event_manager.__class__.__name__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Event test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event test failed: {str(e)}"
        )


@router.post("/test-all-dependencies")
async def test_all_dependencies(
    llm_manager: LLMManagerDep,
    db: DatabaseDep,
    event_manager: EventManagerDep,
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive test using ALL three dependency injection types.

    Demonstrates:
    - Multiple dependency injection in single endpoint
    - Coordinated use of LLM, database, and events
    - Complete workflow with DI

    Requires authentication.

    Workflow:
    1. Query database for user data
    2. Use LLM to generate analysis
    3. Publish event about the analysis
    4. Return comprehensive results
    """
    try:
        # Step 1: Get user data from database
        assessment_count = await db.assessments.count_documents({
            "user_id": str(current_user.id)
        })

        # Step 2: Use LLM to generate analysis
        llm_request = LLMRequest(
            model="gpt-4",
            system_prompt="You are an AI infrastructure analyst.",
            user_prompt=f"User has {assessment_count} assessments. In 10 words, provide a brief insight.",
            temperature=0.3,
            max_tokens=50
        )

        llm_response = await llm_manager.generate(llm_request)

        # Step 3: Publish event about the analysis
        analysis_event = AgentEvent(
            event_type=EventType.RECOMMENDATION_GENERATED,
            agent_name="di_comprehensive_test",
            data={
                "user_id": str(current_user.id),
                "assessment_count": assessment_count,
                "analysis": llm_response.content,
                "test_type": "comprehensive_di_test"
            }
        )

        await event_manager.publish(analysis_event)

        # Step 4: Return comprehensive results
        return {
            "status": "success",
            "user": current_user.email,
            "workflow_steps": {
                "1_database_query": {
                    "assessment_count": assessment_count,
                    "injection": "DatabaseDep"
                },
                "2_llm_analysis": {
                    "analysis": llm_response.content,
                    "tokens_used": llm_response.tokens_used,
                    "injection": "LLMManagerDep"
                },
                "3_event_published": {
                    "event_id": analysis_event.event_id,
                    "event_type": analysis_event.event_type.value,
                    "broadcast": "All API instances notified",
                    "injection": "EventManagerDep"
                }
            },
            "dependency_injection": {
                "pattern": "FastAPI Depends()",
                "benefits": [
                    "Testable (can mock all dependencies)",
                    "Scalable (no global singletons)",
                    "Type-safe (FastAPI validates types)",
                    "Maintainable (explicit dependencies)"
                ]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Comprehensive test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive test failed: {str(e)}"
        )


@router.get("/migration-guide")
async def get_migration_guide():
    """
    Endpoint providing migration guide for other endpoints.

    No authentication required - this is documentation.
    """
    return {
        "title": "Dependency Injection Migration Guide",
        "old_pattern": {
            "description": "Old way with global singletons",
            "code": """
@router.post("/endpoint")
async def endpoint(data: RequestData):
    # ❌ BAD: Direct instantiation or singleton access
    manager = get_enhanced_llm_manager()  # Global singleton
    db = await get_database()  # Legacy function

    result = await manager.generate(...)
    await db.collection.insert_one(result)
"""
        },
        "new_pattern": {
            "description": "New way with dependency injection",
            "code": """
from ...core.dependencies import LLMManagerDep, DatabaseDep, EventManagerDep

@router.post("/endpoint")
async def endpoint(
    data: RequestData,
    llm_manager: LLMManagerDep,  # ✅ GOOD: Injected
    db: DatabaseDep,  # ✅ GOOD: Injected
    event_manager: EventManagerDep,  # ✅ GOOD: Injected
    current_user: User = Depends(get_current_user)
):
    result = await llm_manager.generate(...)
    await db.collection.insert_one(result)
    await event_manager.publish(event)
"""
        },
        "migration_steps": [
            "1. Import dependency types from core.dependencies",
            "2. Add dependency parameters to function signature",
            "3. Remove direct instantiation or singleton calls",
            "4. Use injected dependencies instead",
            "5. Test with mocked dependencies"
        ],
        "testing_pattern": {
            "description": "Testing with mocked dependencies",
            "code": """
def test_endpoint():
    mock_llm = AsyncMock()
    mock_db = AsyncMock()

    # Override dependencies
    app.dependency_overrides[get_llm_manager] = lambda: mock_llm
    app.dependency_overrides[get_database] = lambda: mock_db

    response = client.post("/endpoint", json={...})

    assert mock_llm.generate.called
    assert mock_db.collection.insert_one.called
"""
        },
        "benefits": [
            "✅ Horizontal scaling (no global singletons)",
            "✅ Testability (easy to mock)",
            "✅ Type safety (FastAPI validates)",
            "✅ Maintainability (explicit dependencies)",
            "✅ No memory leaks (proper cleanup)"
        ],
        "references": {
            "dependencies_module": "src/infra_mind/core/dependencies.py",
            "redis_event_manager": "src/infra_mind/orchestration/redis_event_manager.py",
            "implementation_plan": "WEEK_3_4_SINGLETON_REMOVAL_PLAN.md"
        }
    }
