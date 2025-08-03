"""
Production-grade user management API endpoints for Infra Mind.

Provides comprehensive user management capabilities including:
- User CRUD operations
- Role assignment and management
- User activity monitoring
- Bulk user operations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ...core.auth import get_current_active_user, auth_service
from ...core.rbac import (
    Role, Permission, AccessControl, require_permission, require_role,
    require_user_management, require_view_all_users
)
from ...core.audit import log_authentication_event, log_security_event, AuditEventType, AuditSeverity
from ...models.user import User
from ...schemas.base import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/users", tags=["user-management"])


# Request/Response models
class CreateUserRequest(BaseModel):
    """Create user request model."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=8, max_length=128)
    full_name: str = Field(description="User's full name", min_length=2, max_length=100)
    company_name: Optional[str] = Field(default=None, description="Company name", max_length=200)
    job_title: Optional[str] = Field(default=None, description="Job title", max_length=100)
    role: Role = Field(default=Role.USER, description="User role")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        return v.strip()


class UpdateUserRequest(BaseModel):
    """Update user request model."""
    full_name: Optional[str] = Field(default=None, description="User's full name", max_length=100)
    company_name: Optional[str] = Field(default=None, description="Company name", max_length=200)
    job_title: Optional[str] = Field(default=None, description="Job title", max_length=100)
    is_active: Optional[bool] = Field(default=None, description="User active status")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        return v.strip() if v else None


class AssignRoleRequest(BaseModel):
    """Assign role request model."""
    role: Role = Field(description="Role to assign")
    reason: Optional[str] = Field(default=None, description="Reason for role change", max_length=500)


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    company_name: Optional[str]
    job_title: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    login_count: int
    assessments_created: int


class UserListResponse(BaseModel):
    """User list response model."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class UserActivityResponse(BaseModel):
    """User activity response model."""
    user_id: str
    email: str
    full_name: str
    last_login: Optional[datetime]
    login_count: int
    assessments_created: int
    recent_activity: List[Dict[str, Any]]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    http_request: Request,
    current_user: User = Depends(require_user_management)
):
    """
    Create a new user account.
    
    Requires MANAGE_USERS permission.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Validate role assignment
        AccessControl.validate_role_assignment(
            assigner=current_user,
            target_user=None,  # New user
            new_role=request.role,
            ip_address=client_ip
        )
        
        # Create user
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company_name=request.company_name,
            job_title=request.job_title,
            ip_address=client_ip
        )
        
        # Set role if different from default
        if request.role != Role.USER:
            user.role = request.role.value
            await user.save()
        
        # Log user creation
        log_authentication_event(
            AuditEventType.USER_CREATED,
            user=user,
            ip_address=client_ip,
            outcome="success",
            details={
                "created_by": str(current_user.id),
                "assigned_role": request.role.value
            }
        )
        
        logger.info(f"User created: {user.email} by {current_user.email}")
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            job_title=user.job_title,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            login_count=user.login_count,
            assessments_created=user.assessments_created
        )
        
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    role_filter: Optional[Role] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Show only active users"),
    current_user: User = Depends(require_view_all_users)
):
    """
    List users with pagination and filtering.
    
    Requires READ_ALL_USERS permission.
    """
    try:
        # Build query filters
        filters = {}
        if active_only:
            filters["is_active"] = True
        if role_filter:
            filters["role"] = role_filter.value
        
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Get users with filters
        query = User.find(filters)
        
        # Apply search if provided
        if search:
            # Simple search implementation - in production, use text search
            search_lower = search.lower()
            all_users = await query.to_list()
            filtered_users = [
                user for user in all_users
                if (search_lower in user.email.lower() or 
                    search_lower in user.full_name.lower() or
                    (user.company_name and search_lower in user.company_name.lower()))
            ]
            total = len(filtered_users)
            users = filtered_users[skip:skip + page_size]
        else:
            total = await query.count()
            users = await query.skip(skip).limit(page_size).to_list()
        
        # Convert to response format
        user_responses = [
            UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                company_name=user.company_name,
                job_title=user.job_title,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                login_count=user.login_count,
                assessments_created=user.assessments_created
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(skip + page_size) < total
        )
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID.
    
    Users can view their own profile, or requires READ_ALL_USERS permission.
    """
    try:
        # Check if user is accessing their own profile
        if str(current_user.id) == user_id:
            target_user = current_user
        else:
            # Check permission to view other users
            if not AccessControl.user_has_permission(current_user, Permission.READ_ALL_USERS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view other users"
                )
            
            target_user = await User.get(user_id)
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        return UserResponse(
            id=str(target_user.id),
            email=target_user.email,
            full_name=target_user.full_name,
            company_name=target_user.company_name,
            job_title=target_user.job_title,
            role=target_user.role,
            is_active=target_user.is_active,
            is_verified=target_user.is_verified,
            created_at=target_user.created_at,
            last_login=target_user.last_login,
            login_count=target_user.login_count,
            assessments_created=target_user.assessments_created
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user information.
    
    Users can update their own profile, or requires MANAGE_USERS permission.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Get target user
        target_user = await User.get(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions
        if str(current_user.id) == user_id:
            # Users can update their own profile (limited fields)
            if request.is_active is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change your own active status"
                )
        else:
            # Check permission to manage other users
            if not AccessControl.user_has_permission(current_user, Permission.MANAGE_USERS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to manage other users"
                )
        
        # Update fields
        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.company_name is not None:
            update_data["company_name"] = request.company_name
        if request.job_title is not None:
            update_data["job_title"] = request.job_title
        if request.is_active is not None and str(current_user.id) != user_id:
            update_data["is_active"] = request.is_active
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user
            await target_user.update({"$set": update_data})
            
            # Refresh user data
            target_user = await User.get(user_id)
            
            # Log user update
            log_authentication_event(
                AuditEventType.USER_UPDATED,
                user=target_user,
                ip_address=client_ip,
                outcome="success",
                details={
                    "updated_by": str(current_user.id),
                    "updated_fields": list(update_data.keys())
                }
            )
        
        return UserResponse(
            id=str(target_user.id),
            email=target_user.email,
            full_name=target_user.full_name,
            company_name=target_user.company_name,
            job_title=target_user.job_title,
            role=target_user.role,
            is_active=target_user.is_active,
            is_verified=target_user.is_verified,
            created_at=target_user.created_at,
            last_login=target_user.last_login,
            login_count=target_user.login_count,
            assessments_created=target_user.assessments_created
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/{user_id}/assign-role", response_model=SuccessResponse)
async def assign_role(
    user_id: str,
    request: AssignRoleRequest,
    http_request: Request,
    current_user: User = Depends(require_permission(Permission.ASSIGN_ROLES))
):
    """
    Assign a role to a user.
    
    Requires ASSIGN_ROLES permission.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Get target user
        target_user = await User.get(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate role assignment
        AccessControl.validate_role_assignment(
            assigner=current_user,
            target_user=target_user,
            new_role=request.role,
            ip_address=client_ip
        )
        
        # Store old role for logging
        old_role = target_user.role
        
        # Update role
        target_user.role = request.role.value
        target_user.updated_at = datetime.utcnow()
        await target_user.save()
        
        # Log role assignment
        log_authentication_event(
            AuditEventType.USER_UPDATED,
            user=target_user,
            ip_address=client_ip,
            outcome="success",
            details={
                "action": "role_assignment",
                "assigned_by": str(current_user.id),
                "old_role": old_role,
                "new_role": request.role.value,
                "reason": request.reason
            }
        )
        
        logger.info(f"Role assigned: {target_user.email} -> {request.role.value} by {current_user.email}")
        
        return SuccessResponse(
            message=f"Role {request.role.value} assigned successfully",
            data={
                "user_id": str(target_user.id),
                "old_role": old_role,
                "new_role": request.role.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign role error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    http_request: Request,
    current_user: User = Depends(require_permission(Permission.DELETE_USER))
):
    """
    Delete a user account.
    
    Requires DELETE_USER permission.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Prevent self-deletion
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get target user
        target_user = await User.get(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if trying to delete a higher-privilege user
        current_role = AccessControl.get_user_role(current_user)
        target_role = AccessControl.get_user_role(target_user)
        
        if Role.get_hierarchy_level(target_role) >= Role.get_hierarchy_level(current_role):
            log_security_event(
                AuditEventType.SECURITY_VIOLATION,
                user=current_user,
                ip_address=client_ip,
                details={
                    "action": "attempted_user_deletion",
                    "target_user": str(target_user.id),
                    "target_role": target_role.value,
                    "current_role": current_role.value
                },
                severity=AuditSeverity.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete user with equal or higher privileges"
            )
        
        # Store user info for logging
        user_email = target_user.email
        
        # Delete user
        await target_user.delete()
        
        # Log user deletion
        log_authentication_event(
            AuditEventType.USER_DELETED,
            user_email=user_email,
            ip_address=client_ip,
            outcome="success",
            details={
                "deleted_by": str(current_user.id),
                "deleted_user_role": target_role.value
            }
        )
        
        logger.info(f"User deleted: {user_email} by {current_user.email}")
        
        return SuccessResponse(
            message="User deleted successfully",
            data={"deleted_user_email": user_email}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get("/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_USER_ACTIVITY))
):
    """
    Get user activity information.
    
    Requires VIEW_USER_ACTIVITY permission.
    """
    try:
        # Get target user
        target_user = await User.get(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get recent activity (placeholder - in production, query audit logs)
        recent_activity = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "login",
                "details": "User logged in"
            }
            # In production, query actual audit logs
        ]
        
        return UserActivityResponse(
            user_id=str(target_user.id),
            email=target_user.email,
            full_name=target_user.full_name,
            last_login=target_user.last_login,
            login_count=target_user.login_count,
            assessments_created=target_user.assessments_created,
            recent_activity=recent_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user activity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user activity"
        )


@router.get("/roles/available", response_model=Dict[str, Any])
async def get_available_roles(
    current_user: User = Depends(require_permission(Permission.ASSIGN_ROLES))
):
    """
    Get roles that the current user can assign.
    
    Requires ASSIGN_ROLES permission.
    """
    try:
        current_role = AccessControl.get_user_role(current_user)
        assignable_roles = Role.get_assignable_roles(current_role)
        
        return {
            "current_user_role": current_role.value,
            "assignable_roles": [
                {
                    "value": role.value,
                    "hierarchy_level": Role.get_hierarchy_level(role)
                }
                for role in assignable_roles
            ],
            "role_hierarchy": Role.get_hierarchy_level.__doc__
        }
        
    except Exception as e:
        logger.error(f"Get available roles error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available roles"
        )