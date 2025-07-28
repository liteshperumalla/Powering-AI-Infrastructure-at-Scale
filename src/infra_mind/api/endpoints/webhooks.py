"""
Webhook endpoints for Infra Mind.

Handles webhook configuration, event notifications, and real-time updates.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
import uuid
import hmac
import hashlib
import json
import httpx
from enum import Enum

router = APIRouter()
security = HTTPBearer()


# Enums and Models
class WebhookEvent(str, Enum):
    """Webhook event types."""
    ASSESSMENT_CREATED = "assessment.created"
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_COMPLETED = "assessment.completed"
    ASSESSMENT_FAILED = "assessment.failed"
    RECOMMENDATION_GENERATED = "recommendation.generated"
    REPORT_GENERATED = "report.generated"
    REPORT_COMPLETED = "report.completed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    SYSTEM_ALERT = "system.alert"
    SYSTEM_ERROR = "system.error"


class WebhookStatus(str, Enum):
    """Webhook status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class WebhookRequest(BaseModel):
    """Webhook creation/update request."""
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[WebhookEvent] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for signature verification")
    description: Optional[str] = Field(None, description="Webhook description")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom headers")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    is_active: bool = Field(default=True, description="Whether webhook is active")


class WebhookResponse(BaseModel):
    """Webhook response model."""
    id: str
    user_id: str
    url: str
    events: List[WebhookEvent]
    secret_set: bool
    description: Optional[str]
    headers: Dict[str, str]
    timeout_seconds: int
    retry_attempts: int
    status: WebhookStatus
    is_active: bool
    last_triggered: Optional[datetime]
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime


class WebhookListResponse(BaseModel):
    """Webhook list response."""
    webhooks: List[WebhookResponse]
    total: int
    page: int
    limit: int


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    id: str
    webhook_id: str
    event_type: WebhookEvent
    payload: Dict[str, Any]
    response_status: Optional[int]
    response_body: Optional[str]
    response_time_ms: Optional[int]
    attempt_number: int
    delivered_at: datetime
    success: bool
    error_message: Optional[str]


class WebhookDeliveryListResponse(BaseModel):
    """Webhook delivery list response."""
    deliveries: List[WebhookDelivery]
    total: int
    webhook_id: str


class WebhookTestRequest(BaseModel):
    """Webhook test request."""
    event_type: WebhookEvent = Field(default=WebhookEvent.SYSTEM_ALERT)
    test_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Mock webhook storage (replace with database in production)
webhooks_db = {}
deliveries_db = {}


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookRequest,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Create a new webhook endpoint.
    
    Creates a webhook that will receive HTTP POST requests when specified events occur.
    The webhook URL must be publicly accessible and return a 2xx status code.
    """
    try:
        webhook_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Validate webhook URL by sending a test request
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                test_payload = {
                    "event": "webhook.test",
                    "webhook_id": webhook_id,
                    "timestamp": current_time.isoformat()
                }
                response = await client.post(
                    str(webhook_data.url),
                    json=test_payload,
                    headers=webhook_data.headers
                )
                if response.status_code >= 400:
                    logger.warning(f"Webhook URL validation returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Webhook URL validation failed: {e}")
            # Continue anyway - URL might be valid but temporarily unavailable
        
        webhook = {
            "id": webhook_id,
            "user_id": current_user,
            "url": str(webhook_data.url),
            "events": webhook_data.events,
            "secret": webhook_data.secret,
            "description": webhook_data.description,
            "headers": webhook_data.headers,
            "timeout_seconds": webhook_data.timeout_seconds,
            "retry_attempts": webhook_data.retry_attempts,
            "status": WebhookStatus.ACTIVE,
            "is_active": webhook_data.is_active,
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        webhooks_db[webhook_id] = webhook
        logger.info(f"Created webhook: {webhook_id} for user: {current_user}")
        
        return WebhookResponse(
            id=webhook["id"],
            user_id=webhook["user_id"],
            url=webhook["url"],
            events=webhook["events"],
            secret_set=bool(webhook["secret"]),
            description=webhook["description"],
            headers=webhook["headers"],
            timeout_seconds=webhook["timeout_seconds"],
            retry_attempts=webhook["retry_attempts"],
            status=webhook["status"],
            is_active=webhook["is_active"],
            last_triggered=webhook["last_triggered"],
            success_count=webhook["success_count"],
            failure_count=webhook["failure_count"],
            created_at=webhook["created_at"],
            updated_at=webhook["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook"
        )


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[WebhookStatus] = Query(None, description="Filter by status"),
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    List all webhooks for the current user.
    
    Returns a paginated list of webhooks with filtering options.
    """
    try:
        # Filter webhooks by user
        user_webhooks = [w for w in webhooks_db.values() if w["user_id"] == current_user]
        
        # Apply status filter
        if status_filter:
            user_webhooks = [w for w in user_webhooks if w["status"] == status_filter]
        
        # Apply pagination
        total = len(user_webhooks)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_webhooks = user_webhooks[start_idx:end_idx]
        
        # Convert to response format
        webhook_responses = [
            WebhookResponse(
                id=w["id"],
                user_id=w["user_id"],
                url=w["url"],
                events=w["events"],
                secret_set=bool(w["secret"]),
                description=w["description"],
                headers=w["headers"],
                timeout_seconds=w["timeout_seconds"],
                retry_attempts=w["retry_attempts"],
                status=w["status"],
                is_active=w["is_active"],
                last_triggered=w["last_triggered"],
                success_count=w["success_count"],
                failure_count=w["failure_count"],
                created_at=w["created_at"],
                updated_at=w["updated_at"]
            )
            for w in paginated_webhooks
        ]
        
        logger.info(f"Listed {len(webhook_responses)} webhooks for user: {current_user}")
        
        return WebhookListResponse(
            webhooks=webhook_responses,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks"
        )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Get a specific webhook by ID.
    
    Returns detailed information about a webhook including delivery statistics.
    """
    try:
        webhook = webhooks_db.get(webhook_id)
        if not webhook or webhook["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        logger.info(f"Retrieved webhook: {webhook_id}")
        
        return WebhookResponse(
            id=webhook["id"],
            user_id=webhook["user_id"],
            url=webhook["url"],
            events=webhook["events"],
            secret_set=bool(webhook["secret"]),
            description=webhook["description"],
            headers=webhook["headers"],
            timeout_seconds=webhook["timeout_seconds"],
            retry_attempts=webhook["retry_attempts"],
            status=webhook["status"],
            is_active=webhook["is_active"],
            last_triggered=webhook["last_triggered"],
            success_count=webhook["success_count"],
            failure_count=webhook["failure_count"],
            created_at=webhook["created_at"],
            updated_at=webhook["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook"
        )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookRequest,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Update an existing webhook.
    
    Updates webhook configuration including URL, events, and settings.
    """
    try:
        webhook = webhooks_db.get(webhook_id)
        if not webhook or webhook["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Update webhook data
        webhook.update({
            "url": str(webhook_data.url),
            "events": webhook_data.events,
            "secret": webhook_data.secret,
            "description": webhook_data.description,
            "headers": webhook_data.headers,
            "timeout_seconds": webhook_data.timeout_seconds,
            "retry_attempts": webhook_data.retry_attempts,
            "is_active": webhook_data.is_active,
            "updated_at": datetime.utcnow()
        })
        
        webhooks_db[webhook_id] = webhook
        logger.info(f"Updated webhook: {webhook_id}")
        
        return WebhookResponse(
            id=webhook["id"],
            user_id=webhook["user_id"],
            url=webhook["url"],
            events=webhook["events"],
            secret_set=bool(webhook["secret"]),
            description=webhook["description"],
            headers=webhook["headers"],
            timeout_seconds=webhook["timeout_seconds"],
            retry_attempts=webhook["retry_attempts"],
            status=webhook["status"],
            is_active=webhook["is_active"],
            last_triggered=webhook["last_triggered"],
            success_count=webhook["success_count"],
            failure_count=webhook["failure_count"],
            created_at=webhook["created_at"],
            updated_at=webhook["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook"
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Delete a webhook.
    
    Permanently removes the webhook and stops all future deliveries.
    """
    try:
        webhook = webhooks_db.get(webhook_id)
        if not webhook or webhook["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        del webhooks_db[webhook_id]
        
        # Also delete delivery records
        deliveries_to_delete = [
            d_id for d_id, delivery in deliveries_db.items()
            if delivery["webhook_id"] == webhook_id
        ]
        for d_id in deliveries_to_delete:
            del deliveries_db[d_id]
        
        logger.info(f"Deleted webhook: {webhook_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook"
        )


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    test_request: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Test a webhook endpoint.
    
    Sends a test event to the webhook URL to verify it's working correctly.
    """
    try:
        webhook = webhooks_db.get(webhook_id)
        if not webhook or webhook["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Create test payload
        test_payload = {
            "event": test_request.event_type,
            "webhook_id": webhook_id,
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": test_request.test_payload
        }
        
        # Send webhook in background
        background_tasks.add_task(
            send_webhook,
            webhook,
            test_request.event_type,
            test_payload,
            is_test=True
        )
        
        logger.info(f"Triggered test webhook: {webhook_id}")
        
        return {
            "message": "Test webhook triggered successfully",
            "webhook_id": webhook_id,
            "event_type": test_request.event_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test webhook"
        )


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def get_webhook_deliveries(
    webhook_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    success_only: Optional[bool] = Query(None, description="Filter by success status"),
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Get delivery history for a webhook.
    
    Returns a paginated list of webhook delivery attempts with status and response details.
    """
    try:
        webhook = webhooks_db.get(webhook_id)
        if not webhook or webhook["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Filter deliveries by webhook_id
        webhook_deliveries = [
            d for d in deliveries_db.values()
            if d["webhook_id"] == webhook_id
        ]
        
        # Apply success filter
        if success_only is not None:
            webhook_deliveries = [
                d for d in webhook_deliveries
                if d["success"] == success_only
            ]
        
        # Sort by delivered_at descending
        webhook_deliveries.sort(key=lambda x: x["delivered_at"], reverse=True)
        
        # Apply pagination
        total = len(webhook_deliveries)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_deliveries = webhook_deliveries[start_idx:end_idx]
        
        # Convert to response format
        delivery_responses = [
            WebhookDelivery(
                id=d["id"],
                webhook_id=d["webhook_id"],
                event_type=d["event_type"],
                payload=d["payload"],
                response_status=d["response_status"],
                response_body=d["response_body"],
                response_time_ms=d["response_time_ms"],
                attempt_number=d["attempt_number"],
                delivered_at=d["delivered_at"],
                success=d["success"],
                error_message=d["error_message"]
            )
            for d in paginated_deliveries
        ]
        
        logger.info(f"Retrieved {len(delivery_responses)} deliveries for webhook: {webhook_id}")
        
        return WebhookDeliveryListResponse(
            deliveries=delivery_responses,
            total=total,
            webhook_id=webhook_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deliveries for webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook deliveries"
        )


# Webhook delivery function
async def send_webhook(
    webhook: Dict[str, Any],
    event_type: WebhookEvent,
    payload: Dict[str, Any],
    is_test: bool = False
):
    """Send webhook with retry logic and delivery tracking."""
    webhook_id = webhook["id"]
    max_attempts = webhook["retry_attempts"] + 1
    
    for attempt in range(1, max_attempts + 1):
        delivery_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Prepare headers
            headers = webhook["headers"].copy()
            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = "Infra-Mind-Webhook/2.0"
            headers["X-Webhook-Event"] = event_type
            headers["X-Webhook-Delivery"] = delivery_id
            headers["X-Webhook-Attempt"] = str(attempt)
            
            # Add signature if secret is configured
            if webhook["secret"]:
                payload_str = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    webhook["secret"].encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Send webhook
            async with httpx.AsyncClient(timeout=webhook["timeout_seconds"]) as client:
                response = await client.post(
                    webhook["url"],
                    json=payload,
                    headers=headers
                )
                
                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Record delivery
                delivery = {
                    "id": delivery_id,
                    "webhook_id": webhook_id,
                    "event_type": event_type,
                    "payload": payload,
                    "response_status": response.status_code,
                    "response_body": response.text[:1000],  # Truncate response
                    "response_time_ms": response_time_ms,
                    "attempt_number": attempt,
                    "delivered_at": end_time,
                    "success": 200 <= response.status_code < 300,
                    "error_message": None
                }
                
                deliveries_db[delivery_id] = delivery
                
                # Update webhook stats
                if delivery["success"]:
                    webhook["success_count"] += 1
                    webhook["last_triggered"] = end_time
                    webhook["status"] = WebhookStatus.ACTIVE
                    webhooks_db[webhook_id] = webhook
                    logger.info(f"Webhook delivered successfully: {webhook_id} (attempt {attempt})")
                    return
                else:
                    webhook["failure_count"] += 1
                    logger.warning(f"Webhook delivery failed: {webhook_id} (attempt {attempt}, status {response.status_code})")
                    
        except Exception as e:
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Record failed delivery
            delivery = {
                "id": delivery_id,
                "webhook_id": webhook_id,
                "event_type": event_type,
                "payload": payload,
                "response_status": None,
                "response_body": None,
                "response_time_ms": response_time_ms,
                "attempt_number": attempt,
                "delivered_at": end_time,
                "success": False,
                "error_message": str(e)
            }
            
            deliveries_db[delivery_id] = delivery
            webhook["failure_count"] += 1
            
            logger.error(f"Webhook delivery error: {webhook_id} (attempt {attempt}): {e}")
    
    # All attempts failed
    webhook["status"] = WebhookStatus.FAILED
    webhooks_db[webhook_id] = webhook
    logger.error(f"Webhook delivery failed after {max_attempts} attempts: {webhook_id}")


# Function to trigger webhooks for events (to be called from other parts of the system)
async def trigger_webhooks(event_type: WebhookEvent, payload: Dict[str, Any], user_id: str = None):
    """Trigger all webhooks subscribed to a specific event type."""
    try:
        # Find all active webhooks subscribed to this event
        relevant_webhooks = [
            webhook for webhook in webhooks_db.values()
            if (webhook["is_active"] and 
                webhook["status"] == WebhookStatus.ACTIVE and
                event_type in webhook["events"] and
                (user_id is None or webhook["user_id"] == user_id))
        ]
        
        logger.info(f"Triggering {len(relevant_webhooks)} webhooks for event: {event_type}")
        
        # Send webhooks asynchronously
        import asyncio
        tasks = [
            send_webhook(webhook, event_type, payload)
            for webhook in relevant_webhooks
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    except Exception as e:
        logger.error(f"Failed to trigger webhooks for event {event_type}: {e}")