"""
Production-grade Role-Based Access Control (RBAC) for Infra Mind.

Defines user roles, permissions, access control decorators, and comprehensive
permission management with audit logging integration.
"""

from enum import Enum
from typing import List, Set, Optional, Dict, Any
from functools import wraps
from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status, Depends, Request

from .auth import get_current_active_user
from .audit import log_security_event, AuditEventType, AuditSeverity
from ..models.user import User

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """
    Production user roles with clear hierarchy and responsibilities.
    
    Roles are ordered by privilege level (highest to lowest):
    - SUPER_ADMIN: System administration and configuration
    - ADMIN: Full application administration
    - MANAGER: Team and resource management
    - ANALYST: Data analysis and reporting
    - USER: Standard user operations
    - VIEWER: Read-only access
    """
    SUPER_ADMIN = "super_admin"  # System-level administration
    ADMIN = "admin"              # Application administration
    MANAGER = "manager"          # Team and resource management
    ANALYST = "analyst"          # Analysis and reporting
    USER = "user"               # Standard user operations
    VIEWER = "viewer"           # Read-only access
    
    @classmethod
    def get_hierarchy_level(cls, role: 'Role') -> int:
        """Get numeric hierarchy level for role comparison."""
        hierarchy = {
            cls.SUPER_ADMIN: 5,
            cls.ADMIN: 4,
            cls.MANAGER: 3,
            cls.ANALYST: 2,
            cls.USER: 1,
            cls.VIEWER: 0
        }
        return hierarchy.get(role, 0)
    
    @classmethod
    def get_all_roles(cls) -> List['Role']:
        """Get all available roles."""
        return list(cls)
    
    @classmethod
    def get_assignable_roles(cls, current_user_role: 'Role') -> List['Role']:
        """Get roles that can be assigned by the current user role."""
        current_level = cls.get_hierarchy_level(current_user_role)
        
        # Users can only assign roles at their level or below
        assignable = []
        for role in cls.get_all_roles():
            if cls.get_hierarchy_level(role) <= current_level:
                assignable.append(role)
        
        return assignable


class Permission(str, Enum):
    """
    Comprehensive system permissions organized by functional area.
    
    Permissions follow a consistent naming pattern:
    - CREATE_* : Create new resources
    - READ_* : View resources
    - UPDATE_* : Modify existing resources
    - DELETE_* : Remove resources
    - MANAGE_* : Full management capabilities
    - *_ALL_* : Access to all resources of a type
    """
    
    # Assessment permissions
    CREATE_ASSESSMENT = "create_assessment"
    READ_ASSESSMENT = "read_assessment"
    UPDATE_ASSESSMENT = "update_assessment"
    DELETE_ASSESSMENT = "delete_assessment"
    READ_ALL_ASSESSMENTS = "read_all_assessments"
    MANAGE_ASSESSMENTS = "manage_assessments"
    
    # User management permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    READ_ALL_USERS = "read_all_users"
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"
    
    # Report permissions
    CREATE_REPORT = "create_report"
    READ_REPORT = "read_report"
    UPDATE_REPORT = "update_report"
    DELETE_REPORT = "delete_report"
    READ_ALL_REPORTS = "read_all_reports"
    MANAGE_REPORTS = "manage_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Recommendation permissions
    READ_RECOMMENDATION = "read_recommendation"
    CREATE_RECOMMENDATION = "create_recommendation"
    UPDATE_RECOMMENDATION = "update_recommendation"
    DELETE_RECOMMENDATION = "delete_recommendation"
    MANAGE_RECOMMENDATIONS = "manage_recommendations"
    
    # System administration permissions
    VIEW_METRICS = "view_metrics"
    VIEW_SYSTEM_METRICS = "view_system_metrics"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_CONFIGURATION = "manage_configuration"
    
    # Security permissions
    VIEW_SECURITY_EVENTS = "view_security_events"
    MANAGE_SECURITY = "manage_security"
    VIEW_USER_ACTIVITY = "view_user_activity"
    
    # API and integration permissions
    MANAGE_API_KEYS = "manage_api_keys"
    ACCESS_ADMIN_API = "access_admin_api"
    MANAGE_INTEGRATIONS = "manage_integrations"
    
    # Data permissions
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    MANAGE_DATA = "manage_data"
    
    @classmethod
    def get_all_permissions(cls) -> List['Permission']:
        """Get all available permissions."""
        return list(cls)
    
    @classmethod
    def get_permissions_by_category(cls) -> Dict[str, List['Permission']]:
        """Get permissions organized by category."""
        categories = {
            "Assessment": [],
            "User Management": [],
            "Reports": [],
            "Recommendations": [],
            "System": [],
            "Security": [],
            "API": [],
            "Data": []
        }
        
        for permission in cls.get_all_permissions():
            if "assessment" in permission.value.lower():
                categories["Assessment"].append(permission)
            elif "user" in permission.value.lower() or "role" in permission.value.lower():
                categories["User Management"].append(permission)
            elif "report" in permission.value.lower():
                categories["Reports"].append(permission)
            elif "recommendation" in permission.value.lower():
                categories["Recommendations"].append(permission)
            elif any(word in permission.value.lower() for word in ["system", "metric", "log", "config"]):
                categories["System"].append(permission)
            elif "security" in permission.value.lower():
                categories["Security"].append(permission)
            elif "api" in permission.value.lower() or "integration" in permission.value.lower():
                categories["API"].append(permission)
            elif "data" in permission.value.lower():
                categories["Data"].append(permission)
        
        return categories


class RolePermissions:
    """
    Production-grade permission mapping for each role.
    
    This centralized permission mapping provides:
    - Clear role definitions
    - Hierarchical permission inheritance
    - Easy permission auditing
    - Flexible role management
    """
    
    ROLE_PERMISSIONS = {
        Role.SUPER_ADMIN: {
            # Complete system access - all permissions
            *Permission.get_all_permissions()
        },
        
        Role.ADMIN: {
            # Full application administration (excluding system-level)
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,
            Permission.MANAGE_ASSESSMENTS,
            
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.READ_ALL_USERS,
            Permission.MANAGE_USERS,
            Permission.ASSIGN_ROLES,
            
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.DELETE_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.MANAGE_REPORTS,
            Permission.EXPORT_REPORTS,
            
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            Permission.UPDATE_RECOMMENDATION,
            Permission.DELETE_RECOMMENDATION,
            Permission.MANAGE_RECOMMENDATIONS,
            
            Permission.VIEW_METRICS,
            Permission.VIEW_SYSTEM_METRICS,
            Permission.VIEW_LOGS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.VIEW_SECURITY_EVENTS,
            Permission.VIEW_USER_ACTIVITY,
            
            Permission.MANAGE_API_KEYS,
            Permission.ACCESS_ADMIN_API,
            Permission.MANAGE_INTEGRATIONS,
            
            Permission.EXPORT_DATA,
            Permission.IMPORT_DATA,
            Permission.MANAGE_DATA,
        },
        
        Role.MANAGER: {
            # Team and resource management
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,
            
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.READ_ALL_USERS,
            
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.DELETE_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.EXPORT_REPORTS,
            
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            Permission.UPDATE_RECOMMENDATION,
            Permission.DELETE_RECOMMENDATION,
            
            Permission.VIEW_METRICS,
            Permission.VIEW_USER_ACTIVITY,
            
            Permission.EXPORT_DATA,
        },
        
        Role.ANALYST: {
            # Analysis and reporting focus
            Permission.READ_ASSESSMENT,
            Permission.READ_ALL_ASSESSMENTS,
            
            Permission.READ_USER,
            Permission.READ_ALL_USERS,
            
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.READ_ALL_REPORTS,
            Permission.EXPORT_REPORTS,
            
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            
            Permission.VIEW_METRICS,
            
            Permission.EXPORT_DATA,
        },
        
        Role.USER: {
            # Standard user operations
            Permission.CREATE_ASSESSMENT,
            Permission.READ_ASSESSMENT,
            Permission.UPDATE_ASSESSMENT,
            Permission.DELETE_ASSESSMENT,
            
            Permission.READ_USER,
            Permission.UPDATE_USER,  # Own profile only
            
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.DELETE_REPORT,
            
            Permission.READ_RECOMMENDATION,
            Permission.CREATE_RECOMMENDATION,
            Permission.UPDATE_RECOMMENDATION,
            Permission.DELETE_RECOMMENDATION,
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
    
    @classmethod
    def get_role_hierarchy(cls) -> Dict[Role, int]:
        """Get role hierarchy levels."""
        return {role: Role.get_hierarchy_level(role) for role in Role.get_all_roles()}
    
    @classmethod
    def can_assign_role(cls, assigner_role: Role, target_role: Role) -> bool:
        """Check if a role can assign another role."""
        assigner_level = Role.get_hierarchy_level(assigner_role)
        target_level = Role.get_hierarchy_level(target_role)
        
        # Can only assign roles at same level or below
        return assigner_level >= target_level
    
    @classmethod
    def get_permission_summary(cls) -> Dict[str, Any]:
        """Get a summary of all roles and their permissions."""
        summary = {}
        for role in Role.get_all_roles():
            permissions = cls.get_permissions(role)
            summary[role.value] = {
                "hierarchy_level": Role.get_hierarchy_level(role),
                "permission_count": len(permissions),
                "permissions": [p.value for p in permissions]
            }
        return summary


class AccessControl:
    """
    Production-grade access control utilities with comprehensive
    permission checking, resource ownership validation, and audit logging.
    """
    
    @staticmethod
    def get_user_role(user: User) -> Role:
        """
        Get user's role with validation.
        
        Args:
            user: User object
            
        Returns:
            User's role (defaults to USER if not set or invalid)
        """
        if not user:
            return Role.VIEWER
        
        role_str = getattr(user, 'role', 'user')
        try:
            return Role(role_str)
        except ValueError:
            logger.warning(f"Invalid role '{role_str}' for user {user.id}, defaulting to USER")
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
        if not user or not user.is_active:
            return False
        
        user_role = AccessControl.get_user_role(user)
        return RolePermissions.has_permission(user_role, permission)
    
    @staticmethod
    def user_can_access_resource(
        user: User, 
        resource_owner_id: str, 
        permission: Permission,
        resource_type: str = "resource"
    ) -> bool:
        """
        Check if user can access a specific resource with comprehensive validation.
        
        Args:
            user: User requesting access
            resource_owner_id: ID of the resource owner
            permission: Required permission
            resource_type: Type of resource for logging
            
        Returns:
            True if access is allowed, False otherwise
        """
        if not user or not user.is_active:
            return False
        
        user_role = AccessControl.get_user_role(user)
        
        # Super admins and admins can access everything
        if user_role in [Role.SUPER_ADMIN, Role.ADMIN]:
            return True
        
        # Users can access their own resources if they have the permission
        if str(user.id) == resource_owner_id:
            return AccessControl.user_has_permission(user, permission)
        
        # Check for "all" permissions for managers and analysts
        all_permission_map = {
            Permission.READ_ASSESSMENT: Permission.READ_ALL_ASSESSMENTS,
            Permission.UPDATE_ASSESSMENT: Permission.MANAGE_ASSESSMENTS,
            Permission.DELETE_ASSESSMENT: Permission.MANAGE_ASSESSMENTS,
            Permission.READ_REPORT: Permission.READ_ALL_REPORTS,
            Permission.UPDATE_REPORT: Permission.MANAGE_REPORTS,
            Permission.DELETE_REPORT: Permission.MANAGE_REPORTS,
            Permission.READ_USER: Permission.READ_ALL_USERS,
            Permission.UPDATE_USER: Permission.MANAGE_USERS,
            Permission.DELETE_USER: Permission.MANAGE_USERS,
        }
        
        all_permission = all_permission_map.get(permission)
        if all_permission and AccessControl.user_has_permission(user, all_permission):
            return True
        
        return False
    
    @staticmethod
    def validate_role_assignment(
        assigner: User,
        target_user: User,
        new_role: Role,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Validate if a user can assign a role to another user.
        
        Args:
            assigner: User attempting to assign the role
            target_user: User receiving the role
            new_role: Role being assigned
            ip_address: IP address for audit logging
            
        Returns:
            True if assignment is allowed
            
        Raises:
            HTTPException: If assignment is not allowed
        """
        if not AccessControl.user_has_permission(assigner, Permission.ASSIGN_ROLES):
            log_security_event(
                AuditEventType.PERMISSION_DENIED,
                user=assigner,
                ip_address=ip_address,
                details={
                    "action": "role_assignment",
                    "target_user": str(target_user.id),
                    "attempted_role": new_role.value,
                    "reason": "no_assign_permission"
                },
                severity=AuditSeverity.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to assign roles"
            )
        
        assigner_role = AccessControl.get_user_role(assigner)
        
        # Check if assigner can assign this role
        if not RolePermissions.can_assign_role(assigner_role, new_role):
            log_security_event(
                AuditEventType.PERMISSION_DENIED,
                user=assigner,
                ip_address=ip_address,
                details={
                    "action": "role_assignment",
                    "target_user": str(target_user.id),
                    "attempted_role": new_role.value,
                    "assigner_role": assigner_role.value,
                    "reason": "insufficient_role_level"
                },
                severity=AuditSeverity.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot assign role {new_role.value}. Insufficient privileges."
            )
        
        # Prevent self-role elevation beyond current level
        if str(assigner.id) == str(target_user.id):
            current_role = AccessControl.get_user_role(target_user)
            if Role.get_hierarchy_level(new_role) > Role.get_hierarchy_level(current_role):
                log_security_event(
                    AuditEventType.SECURITY_VIOLATION,
                    user=assigner,
                    ip_address=ip_address,
                    details={
                        "action": "self_role_elevation",
                        "current_role": current_role.value,
                        "attempted_role": new_role.value
                    },
                    severity=AuditSeverity.CRITICAL
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot elevate your own role privileges"
                )
        
        return True
    
    @staticmethod
    def get_accessible_resources(
        user: User,
        resource_type: str,
        permission: Permission
    ) -> Dict[str, Any]:
        """
        Get information about what resources a user can access.
        
        Args:
            user: User object
            resource_type: Type of resource
            permission: Required permission
            
        Returns:
            Dictionary with access information
        """
        if not user or not user.is_active:
            return {"can_access_own": False, "can_access_all": False}
        
        user_role = AccessControl.get_user_role(user)
        
        # Check if user can access their own resources
        can_access_own = AccessControl.user_has_permission(user, permission)
        
        # Check if user can access all resources
        all_permission_map = {
            Permission.READ_ASSESSMENT: Permission.READ_ALL_ASSESSMENTS,
            Permission.READ_REPORT: Permission.READ_ALL_REPORTS,
            Permission.READ_USER: Permission.READ_ALL_USERS,
        }
        
        all_permission = all_permission_map.get(permission)
        can_access_all = (
            user_role in [Role.SUPER_ADMIN, Role.ADMIN] or
            (all_permission and AccessControl.user_has_permission(user, all_permission))
        )
        
        return {
            "can_access_own": can_access_own,
            "can_access_all": can_access_all,
            "user_role": user_role.value,
            "resource_type": resource_type
        }
    
    @staticmethod
    def log_access_attempt(
        user: User,
        permission: Permission,
        resource_type: str,
        resource_id: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log access attempts for audit purposes.
        
        Args:
            user: User attempting access
            permission: Permission being checked
            resource_type: Type of resource
            resource_id: ID of specific resource
            success: Whether access was granted
            ip_address: IP address of request
        """
        from .audit import log_data_access_event
        
        log_data_access_event(
            user=user,
            resource_type=resource_type,
            resource_id=resource_id or "unknown",
            action=permission.value,
            ip_address=ip_address,
            outcome="success" if success else "failure"
        )


# Production-grade FastAPI dependencies for access control
def require_permission(permission: Permission, log_access: bool = True):
    """
    Production FastAPI dependency factory for permission checking.
    
    Args:
        permission: Required permission
        log_access: Whether to log access attempts
        
    Returns:
        FastAPI dependency function
    """
    def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        client_ip = request.client.host if request.client else None
        
        if not AccessControl.user_has_permission(current_user, permission):
            if log_access:
                log_security_event(
                    AuditEventType.PERMISSION_DENIED,
                    user=current_user,
                    ip_address=client_ip,
                    details={
                        "required_permission": permission.value,
                        "user_role": AccessControl.get_user_role(current_user).value,
                        "endpoint": str(request.url)
                    },
                    severity=AuditSeverity.HIGH
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        
        if log_access:
            AccessControl.log_access_attempt(
                user=current_user,
                permission=permission,
                resource_type="endpoint",
                success=True,
                ip_address=client_ip
            )
        
        return current_user
    
    return permission_checker


def require_role(required_role: Role, log_access: bool = True):
    """
    Production FastAPI dependency factory for role checking.
    
    Args:
        required_role: Required role
        log_access: Whether to log access attempts
        
    Returns:
        FastAPI dependency function
    """
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        client_ip = request.client.host if request.client else None
        user_role = AccessControl.get_user_role(current_user)
        
        user_level = Role.get_hierarchy_level(user_role)
        required_level = Role.get_hierarchy_level(required_role)
        
        if user_level < required_level:
            if log_access:
                log_security_event(
                    AuditEventType.PERMISSION_DENIED,
                    user=current_user,
                    ip_address=client_ip,
                    details={
                        "required_role": required_role.value,
                        "user_role": user_role.value,
                        "endpoint": str(request.url)
                    },
                    severity=AuditSeverity.HIGH
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value}, Current: {user_role.value}"
            )
        
        return current_user
    
    return role_checker


def require_any_role(allowed_roles: List[Role], log_access: bool = True):
    """
    FastAPI dependency factory for multiple role checking.
    
    Args:
        allowed_roles: List of allowed roles
        log_access: Whether to log access attempts
        
    Returns:
        FastAPI dependency function
    """
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        client_ip = request.client.host if request.client else None
        user_role = AccessControl.get_user_role(current_user)
        
        if user_role not in allowed_roles:
            if log_access:
                log_security_event(
                    AuditEventType.PERMISSION_DENIED,
                    user=current_user,
                    ip_address=client_ip,
                    details={
                        "allowed_roles": [role.value for role in allowed_roles],
                        "user_role": user_role.value,
                        "endpoint": str(request.url)
                    },
                    severity=AuditSeverity.HIGH
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required one of: {[r.value for r in allowed_roles]}, Current: {user_role.value}"
            )
        
        return current_user
    
    return role_checker


def require_resource_access(permission: Permission, resource_type: str = "resource"):
    """
    Production FastAPI dependency factory for resource-specific access checking.
    
    Args:
        permission: Required permission for the resource
        resource_type: Type of resource for logging
        
    Returns:
        FastAPI dependency function
    """
    def resource_access_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        client_ip = request.client.host if request.client else None
        
        if not AccessControl.user_has_permission(current_user, permission):
            log_security_event(
                AuditEventType.PERMISSION_DENIED,
                user=current_user,
                ip_address=client_ip,
                details={
                    "required_permission": permission.value,
                    "resource_type": resource_type,
                    "endpoint": str(request.url)
                },
                severity=AuditSeverity.HIGH
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        
        return current_user
    
    return resource_access_checker


# Common role-based dependencies
require_admin = require_role(Role.ADMIN)
require_manager_or_admin = require_any_role([Role.MANAGER, Role.ADMIN])
require_analyst_or_above = require_any_role([Role.ANALYST, Role.MANAGER, Role.ADMIN])

# Common permission-based dependencies
require_user_management = require_permission(Permission.MANAGE_USERS)
require_system_access = require_permission(Permission.MANAGE_SYSTEM)
require_view_all_users = require_permission(Permission.READ_ALL_USERS)


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