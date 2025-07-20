"""
Tests for authentication system.

Tests JWT token management, password hashing, and authentication flows.
"""

import pytest
from datetime import datetime, timedelta, timezone
import jwt
from unittest.mock import patch, AsyncMock

from src.infra_mind.core.auth import (
    TokenManager, PasswordManager, AuthService, AuthenticationError,
    SECRET_KEY, ALGORITHM
)
from src.infra_mind.core.rbac import Role, Permission, AccessControl, RolePermissions


class TestTokenManager:
    """Test JWT token management."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = TokenManager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = TokenManager.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = TokenManager.create_access_token(data)
        
        payload = TokenManager.verify_token(token, "access")
        
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "user123", "email": "test@example.com"}
        
        # Create token with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_token = jwt.encode(
            {**data, "exp": past_time, "type": "access"},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        with pytest.raises(AuthenticationError, match="Token has expired"):
            TokenManager.verify_token(expired_token, "access")
    
    def test_verify_wrong_token_type(self):
        """Test verification with wrong token type."""
        data = {"sub": "user123", "email": "test@example.com"}
        access_token = TokenManager.create_access_token(data)
        
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            TokenManager.verify_token(access_token, "refresh")
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(AuthenticationError, match="Token validation failed"):
            TokenManager.verify_token(invalid_token, "access")
    
    def test_refresh_access_token(self):
        """Test refreshing access token."""
        data = {"sub": "user123", "email": "test@example.com", "role": "user"}
        refresh_token = TokenManager.create_refresh_token(data)
        
        new_access_token = TokenManager.refresh_access_token(refresh_token)
        
        # Verify new access token
        payload = TokenManager.verify_token(new_access_token, "access")
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"


class TestPasswordManager:
    """Test password management."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")  # Bcrypt format
    
    def test_verify_password(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = PasswordManager.hash_password(password)
        
        # Correct password should verify
        assert PasswordManager.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert PasswordManager.verify_password("wrong_password", hashed) is False
    
    def test_generate_password_reset_token(self):
        """Test password reset token generation."""
        token = PasswordManager.generate_password_reset_token()
        
        assert isinstance(token, str)
        assert len(token) > 20  # Should be a long random string
        
        # Should generate different tokens each time
        token2 = PasswordManager.generate_password_reset_token()
        assert token != token2


class TestRolePermissions:
    """Test role-based access control."""
    
    def test_admin_permissions(self):
        """Test admin role has all permissions."""
        admin_permissions = RolePermissions.get_permissions(Role.ADMIN)
        
        # Admin should have all permissions
        assert Permission.CREATE_ASSESSMENT in admin_permissions
        assert Permission.DELETE_USER in admin_permissions
        assert Permission.MANAGE_SYSTEM in admin_permissions
        assert Permission.VIEW_LOGS in admin_permissions
    
    def test_user_permissions(self):
        """Test user role has basic permissions."""
        user_permissions = RolePermissions.get_permissions(Role.USER)
        
        # User should have basic permissions
        assert Permission.CREATE_ASSESSMENT in user_permissions
        assert Permission.READ_ASSESSMENT in user_permissions
        assert Permission.UPDATE_ASSESSMENT in user_permissions
        
        # User should not have admin permissions
        assert Permission.DELETE_USER not in user_permissions
        assert Permission.MANAGE_SYSTEM not in user_permissions
        assert Permission.READ_ALL_ASSESSMENTS not in user_permissions
    
    def test_viewer_permissions(self):
        """Test viewer role has read-only permissions."""
        viewer_permissions = RolePermissions.get_permissions(Role.VIEWER)
        
        # Viewer should have read permissions
        assert Permission.READ_ASSESSMENT in viewer_permissions
        assert Permission.READ_REPORT in viewer_permissions
        
        # Viewer should not have write permissions
        assert Permission.CREATE_ASSESSMENT not in viewer_permissions
        assert Permission.UPDATE_ASSESSMENT not in viewer_permissions
        assert Permission.DELETE_ASSESSMENT not in viewer_permissions
    
    def test_has_permission(self):
        """Test permission checking."""
        assert RolePermissions.has_permission(Role.ADMIN, Permission.MANAGE_SYSTEM) is True
        assert RolePermissions.has_permission(Role.USER, Permission.MANAGE_SYSTEM) is False
        assert RolePermissions.has_permission(Role.USER, Permission.CREATE_ASSESSMENT) is True


class TestAccessControl:
    """Test access control utilities."""
    
    def test_get_user_role_default(self):
        """Test getting user role with default."""
        # Mock user without role attribute
        class MockUser:
            pass
        
        user = MockUser()
        role = AccessControl.get_user_role(user)
        
        assert role == Role.USER  # Should default to USER
    
    def test_get_user_role_with_role(self):
        """Test getting user role when set."""
        class MockUser:
            role = "admin"
        
        user = MockUser()
        role = AccessControl.get_user_role(user)
        
        assert role == Role.ADMIN
    
    def test_user_has_permission(self):
        """Test user permission checking."""
        class MockUser:
            role = "admin"
        
        admin_user = MockUser()
        
        assert AccessControl.user_has_permission(admin_user, Permission.MANAGE_SYSTEM) is True
        
        # Test with regular user
        class MockRegularUser:
            role = "user"
        
        regular_user = MockRegularUser()
        assert AccessControl.user_has_permission(regular_user, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(regular_user, Permission.CREATE_ASSESSMENT) is True
    
    def test_user_can_access_own_resource(self):
        """Test user can access their own resources."""
        class MockUser:
            id = "user123"
            role = "user"
        
        user = MockUser()
        
        # User can access their own resource
        assert AccessControl.user_can_access_resource(
            user, "user123", Permission.READ_ASSESSMENT
        ) is True
        
        # User cannot access other's resource
        assert AccessControl.user_can_access_resource(
            user, "user456", Permission.READ_ASSESSMENT
        ) is False
    
    def test_admin_can_access_all_resources(self):
        """Test admin can access all resources."""
        class MockUser:
            id = "admin123"
            role = "admin"
        
        admin = MockUser()
        
        # Admin can access any resource
        assert AccessControl.user_can_access_resource(
            admin, "user456", Permission.READ_ASSESSMENT
        ) is True
        
        assert AccessControl.user_can_access_resource(
            admin, "user789", Permission.DELETE_ASSESSMENT
        ) is True


class TestAuthenticationIntegration:
    """Test authentication integration scenarios."""
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow."""
        # 1. Hash password
        password = "secure_password_123"
        hashed_password = PasswordManager.hash_password(password)
        
        # 2. Create tokens
        user_data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        access_token = TokenManager.create_access_token(user_data)
        refresh_token = TokenManager.create_refresh_token(user_data)
        
        # 3. Verify access token
        payload = TokenManager.verify_token(access_token, "access")
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        
        # 4. Refresh token
        new_access_token = TokenManager.refresh_access_token(refresh_token)
        new_payload = TokenManager.verify_token(new_access_token, "access")
        assert new_payload["sub"] == "user123"
        
        # 5. Verify password
        assert PasswordManager.verify_password(password, hashed_password) is True
    
    def test_token_expiration_handling(self):
        """Test handling of expired tokens."""
        # Create token with very short expiration
        data = {"sub": "user123", "email": "test@example.com"}
        short_expiry = timedelta(seconds=1)
        token = TokenManager.create_access_token(data, short_expiry)
        
        # Token should be valid immediately
        payload = TokenManager.verify_token(token, "access")
        assert payload["sub"] == "user123"
        
        # Wait for token to expire (in real test, you might mock time)
        import time
        time.sleep(2)
        
        # Token should now be expired
        with pytest.raises(AuthenticationError, match="Token has expired"):
            TokenManager.verify_token(token, "access")
    
    def test_role_hierarchy(self):
        """Test role hierarchy in access control."""
        # Create users with different roles
        class MockUser:
            def __init__(self, user_id, role):
                self.id = user_id
                self.role = role
        
        admin = MockUser("admin1", "admin")
        manager = MockUser("manager1", "manager")
        user = MockUser("user1", "user")
        viewer = MockUser("viewer1", "viewer")
        
        # Test permission hierarchy
        assert AccessControl.user_has_permission(admin, Permission.MANAGE_SYSTEM) is True
        assert AccessControl.user_has_permission(manager, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(user, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(viewer, Permission.MANAGE_SYSTEM) is False
        
        # Test read permissions
        assert AccessControl.user_has_permission(admin, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(manager, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(user, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(viewer, Permission.READ_ASSESSMENT) is True
        
        # Test write permissions
        assert AccessControl.user_has_permission(admin, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(manager, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(user, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(viewer, Permission.CREATE_ASSESSMENT) is False