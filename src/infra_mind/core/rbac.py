"""
Role-Based Access Control (RBAC) for Infra Mind.

Defines user roles, permissions, and access control decorators.
"""

from enum import Enum
from typing import List, Set, Optional
from functools import wraps
from fastapi import HTTPException, status, Depends

from .auth import get_current_active_user
from ..models.user import User


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    ANALYST = "analyst"  # Can view all assessments and reports
    MANAGER = "manager"  # Can manage team assessments


class Permission(str, Enum):
    """System permissions."""
    # Assessment permissions
    CREATE_ASSESSMENT = "create_assessment"
    READ_ASSESSMENT = "read_assessment"
    UPDATE_ASSESSMENT = "update_assessment"
    DELETE_ASSESSMENT = "delete_assessment"
    READ_ALL_ASSESSMENTS = "read_all_assessments"
    
    # User permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    READ_ALL_USERS = "read_all_users"
    
    # Report permissions
    CREATE_REPORT = "create_report"
    READ_REPORT = "read_report"
    UPDATE_REPORT = "update_report"
    DELETE_REPORT = "delete_report"
    READ_ALL_REPORTS = "read_all_reports"
    
    # Recommendation permissions
    READ_RECOMMENDATION = "read_recommendation"
    CREATE_RECOMMENDATION = "create_recommendation"
    UPDATE_RECOMMENDATION = "update_recommendation"
    DELETE_RECOMMENDATION = "delete_recommendation"
    
    # System permissions
    VIEW_METRICS = "view_metrics"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"


class RolePermissions:
    """
    Define permissions for each role.
    
    Learning Note: This centralized permission mapping makes it easy
    to manage and audit access control across the system.
    """
    
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            # Full system access
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.READ_ALL_USERS,
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.DELETE_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            Permission.UPDATE_RECOMMENDATION,
            Permission.DELETE_RECOMMENDATION,
            Permission.VIEW_METRICS,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_LOGS,
        },
        
        Role.MANAGER: {
            # Team management capabilities
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,  # Can see team assessments
            Permission.READ_USER,
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            Permission.UPDATE_RECOMMENDATION,
            Permission.VIEW_METRICS,
        },
        
        Role.ANALYST: {
            # Analysis and reporting focus
            Permission.READ_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,
            Permission.READ_USER,
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.READ_RECOMMENDATION,
            Permission.VIEW_METRICS,
        },
        
        Role.USER: {
            # Standard user permissions
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            Permission.READ_USER,
            Permission.UPDATE_USER,  # Own profile only
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
        },
        
        Role.VIEWER: {
            # Read-only access
            Permission.READ_ASSESSMENT,
            Permission.READ_USER,
            Permission.READ_REPORT,
            Permission.READ_RECOMMENDATION,
        }
    }
    
    @classmethod
    def get_permissions(cls, role: Role) -> Set[Permission]:
        """Get permissions for a role."""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in cls.get_permissions(role)


class AccessControl:
    """
    Access control utilities.
    
    Learning Note: This class provides methods to check permissions
    and enforce access control throughout the application.
    """
    
    @staticmethod
    def get_user_role(user: User) -> Role:
        """
        Get user's role.
        
        Args:
            user: User object
            
        Returns:
            User's role (defaults to USER if not set)
        """
        # For now, we'll use a simple role field
        # In production, this might come from a separate roles table
        role_str = getattr(user, 'role', 'user')
        try:
            return Role(role_str)
        except ValueError:
            return Role.USER
    
    @staticmethod
    def user_has_permission(user: User, permission: Permission) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user: User object
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        user_role = AccessControl.get_user_role(user)
        return RolePermissions.has_permission(user_role, permission)
    
    @staticmethod
    def user_can_access_resource(user: User, resource_owner_id: str, permission: Permission) -> bool:
        """
        Check if user can access a specific resource.
        
        Args:
            user: User requesting access
            resource_owner_id: ID of the resource owner
            permission: Required permission
            
        Returns:
            True if access is allowed, False otherwise
        """
        user_role = AccessControl.get_user_role(user)
        
        # Admins can access everything
        if user_role == Role.ADMIN:
            return True
        
        # Users can access their own resources
        if str(user.id) == resource_owner_id:
            return AccessControl.user_has_permission(user, permission)
        
        # Managers and analysts can access team resources (if they have the permission)
        if user_role in [Role.MANAGER, Role.ANALYST]:
            # Check if they have the "read all" version of the permission
            all_permission_map = {
                Permission.READ_ASSESSMENT: Permission.READ_ALL_ASSESSMENTS,
                Permission.READ_REPORT: Permission.READ_ALL_REPORTS,
                Permission.READ_USER: Permission.READ_ALL_USERS,
            }
            
            all_permission = all_permission_map.get(permission)
            if all_permission and AccessControl.user_has_permission(user, all_permission):
                return True
        
        return False


# FastAPI dependencies for permission checking
def require_permission(permission: Permission):
    """
    FastAPI dependency factory for permission checking.
    
    Args:
        permission: Required permission
        
    Returns:
        FastAPI dependency function
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not AccessControl.user_has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    
    return permission_checker


def require_role(required_role: Role):
    """
    FastAPI dependency factory for role checking.
    
    Args:
        required_role: Required role
        
    Returns:
        FastAPI dependency function
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role = AccessControl.get_user_role(current_user)
        
        # Define role hierarchy (higher roles include lower role permissions)
        role_hierarchy = {
            Role.ADMIN: 4,
            Role.MANAGER: 3,
            Role.ANALYST: 2,
            Role.USER: 1,
            Role.VIEWER: 0
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value}, Current: {user_role.value}"
            )
        
        return current_user
    
    return role_checker


def require_resource_access(permission: Permission):
    """
    FastAPI dependency factory for resource-specific access checking.
    
    This is used for endpoints that access specific resources (like assessments)
    where users should only access their own resources unless they have special permissions.
    
    Args:
        permission: Required permission for the resource
        
    Returns:
        FastAPI dependency function
    """
    def resource_access_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # The actual resource ownership check will be done in the endpoint
        # This dependency just ensures the user has the base permission
        if not AccessControl.user_has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    
    return resource_access_checker


# Decorator for function-level permission checking
def requires_permission(permission: Permission):
    """
    Decorator for function-level permission checking.
    
    Args:
        permission: Required permission
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (assumes user is passed as parameter)
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not AccessControl.user_has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator