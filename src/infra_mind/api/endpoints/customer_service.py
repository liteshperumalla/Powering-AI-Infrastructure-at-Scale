"""
Customer Service API endpoints for Infra Mind.

Provides REST API for basic customer service operations and management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from ...services.customer_service import customer_service_manager
from ...core.auth import get_current_user, require_admin
from ...models.user import User

router = APIRouter(prefix="/customer-service", tags=["Customer Service"])


# Pydantic models for request/response
class CustomerInquiryRequest(BaseModel):
    """Customer inquiry request model."""
    subject: str = Field(min_length=5, max_length=200, description="Inquiry subject")
    message: str = Field(min_length=10, description="Inquiry message")
    customer_email: Optional[EmailStr] = Field(default=None, description="Customer email")
    customer_name: Optional[str] = Field(default=None, description="Customer name")
    category: str = Field(default="general", description="Inquiry category")


class ServiceStatusResponse(BaseModel):
    """Service status response model."""
    status: str = Field(description="Service status")
    message: str = Field(description="Status message")
    timestamp: datetime = Field(description="Status timestamp")


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """Get customer service status."""
    return ServiceStatusResponse(
        status="active",
        message="Customer service is operational",
        timestamp=datetime.now()
    )


@router.post("/inquiry")
async def submit_inquiry(
    inquiry: CustomerInquiryRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Submit a customer inquiry."""
    try:
        # Use customer service manager to handle the inquiry
        result = await customer_service_manager.handle_inquiry(
            subject=inquiry.subject,
            message=inquiry.message,
            customer_email=inquiry.customer_email or (current_user.email if current_user else None),
            customer_name=inquiry.customer_name or (current_user.name if current_user else None),
            category=inquiry.category
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Inquiry submitted successfully",
                "inquiry_id": result.get("inquiry_id"),
                "status": "received"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit inquiry: {str(e)}")


@router.get("/inquiries")
async def get_customer_inquiries(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, ge=1, le=100)
):
    """Get customer inquiries for the current user."""
    try:
        inquiries = await customer_service_manager.get_customer_inquiries(
            customer_email=current_user.email,
            limit=limit
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "inquiries": inquiries,
                "total": len(inquiries)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve inquiries: {str(e)}")


@router.get("/analytics")
async def get_service_analytics(
    admin_user: User = Depends(require_admin)
):
    """Get customer service analytics (admin only)."""
    try:
        analytics = await customer_service_manager.get_analytics()
        
        return JSONResponse(
            status_code=200,
            content=analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")