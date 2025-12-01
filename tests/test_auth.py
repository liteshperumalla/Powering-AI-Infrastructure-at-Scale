"""
Tests for authentication system.

Tests JWT token management, password hashing, and authentication flows.
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
import jwt
from unittest.mock import patch, AsyncMock

from src.infra_mind.core.auth import (
    TokenManager,
    PasswordManager,
    AuthService,
    AuthenticationError,
    TokenType,
    SECRET_KEY,
    ALGORITHM,
)
from src.infra_mind.core.rbac import Role, Permission, AccessControl, RolePermissions


class DummyUser:
    """Lightweight user object for token/access-control tests."""

    def __init__(
        self,
        user_id: str = "user123",
        email: str = "test@example.com",
        role: str = "user",
        full_name: str = "Test User",
        is_active: bool = True,
    ) -> None:
        self.id = user_id
        self.email = email
        self.role = role
        self.full_name = full_name
        self.is_active = is_active


@pytest.fixture
def token_manager() -> TokenManager:
    """Provide a TokenManager instance for tests."""
    return TokenManager()


@pytest.fixture
def sample_user() -> DummyUser:
    """Return an active sample user."""
    return DummyUser()


class TestTokenManager:
    """Test JWT token management."""
    
    def test_create_access_token(self, token_manager: TokenManager, sample_user: DummyUser):
        """Test access token creation."""
        token = token_manager.create_access_token(sample_user)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Decode and verify
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="infra-mind-api",
            issuer="infra-mind",
        )
        assert payload["sub"] == sample_user.id
        assert payload["email"] == sample_user.email
        assert payload["token_type"] == TokenType.ACCESS.value
        assert "exp" in payload
    
    def test_create_refresh_token(self, token_manager: TokenManager, sample_user: DummyUser):
        """Test refresh token creation."""
        token = token_manager.create_refresh_token(sample_user)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="infra-mind-api",
            issuer="infra-mind",
        )
        assert payload["sub"] == sample_user.id
        assert payload["token_type"] == TokenType.REFRESH.value
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, token_manager: TokenManager, sample_user: DummyUser):
        """Test verification of valid token."""
        token = token_manager.create_access_token(sample_user)
        
        claims = await token_manager.verify_token(token, TokenType.ACCESS)
        
        assert claims.sub == sample_user.id
        assert claims.email == sample_user.email
        assert claims.token_type == TokenType.ACCESS.value
    
    @pytest.mark.asyncio
    async def test_verify_expired_token(self, token_manager: TokenManager, sample_user: DummyUser):
        """Test verification of expired token."""
        expired_token = token_manager.create_access_token(
            sample_user, expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(AuthenticationError, match="Token has expired"):
            await token_manager.verify_token(expired_token, TokenType.ACCESS)
    
    @pytest.mark.asyncio
    async def test_verify_wrong_token_type(self, token_manager: TokenManager, sample_user: DummyUser):
        """Test verification with wrong token type."""
        access_token = token_manager.create_access_token(sample_user)
        
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            await token_manager.verify_token(access_token, TokenType.REFRESH)
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, token_manager: TokenManager):
        """Test verification of invalid token."""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(AuthenticationError, match="Token validation failed"):
            await token_manager.verify_token(invalid_token, TokenType.ACCESS)
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self, token_manager: TokenManager, sample_user: DummyUser, monkeypatch):
        """Test refreshing access token."""
        refresh_token = token_manager.create_refresh_token(sample_user)
        
        monkeypatch.setattr(
            "src.infra_mind.core.auth.User.get",
            AsyncMock(return_value=sample_user),
        )
        
        new_access_token, refreshed_user = await token_manager.refresh_access_token(refresh_token)
        
        assert refreshed_user is sample_user
        claims = await token_manager.verify_token(new_access_token, TokenType.ACCESS)
        assert claims.sub == sample_user.id
        assert claims.email == sample_user.email


class TestPasswordManager:
    """Test password management."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePass123!"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")  # Bcrypt format
    
    def test_verify_password(self):
        """Test password verification."""
        password = "SecurePass123!"
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
        assert Permission.ACCESS_ADMIN_API in admin_permissions
        assert Permission.VIEW_LOGS in admin_permissions
        assert Permission.MANAGE_SYSTEM not in admin_permissions
    
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
        assert RolePermissions.has_permission(Role.ADMIN, Permission.ACCESS_ADMIN_API) is True
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
        admin_user = DummyUser(role="admin")
        
        assert AccessControl.user_has_permission(admin_user, Permission.ACCESS_ADMIN_API) is True
        assert AccessControl.user_has_permission(admin_user, Permission.MANAGE_SYSTEM) is False
        
        # Test with regular user
        regular_user = DummyUser(role="user")
        assert AccessControl.user_has_permission(regular_user, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(regular_user, Permission.CREATE_ASSESSMENT) is True
    
    def test_user_can_access_own_resource(self):
        """Test user can access their own resources."""
        user = DummyUser(user_id="user123", role="user")
        
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
        admin = DummyUser(user_id="admin123", role="admin")
        
        # Admin can access any resource
        assert AccessControl.user_can_access_resource(
            admin, "user456", Permission.READ_ASSESSMENT
        ) is True
        
        assert AccessControl.user_can_access_resource(
            admin, "user789", Permission.DELETE_ASSESSMENT
        ) is True


class TestAuthenticationIntegration:
    """Test authentication integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(self, monkeypatch):
        """Test complete authentication flow."""
        password = "SecurePassword123!"
        hashed_password = PasswordManager.hash_password(password)
        
        token_manager = TokenManager()
        user = DummyUser(
            user_id="user123",
            email="test@example.com",
            role="user",
            full_name="Integration Tester",
        )
        
        access_token = token_manager.create_access_token(user)
        refresh_token = token_manager.create_refresh_token(user)
        
        claims = await token_manager.verify_token(access_token, TokenType.ACCESS)
        assert claims.sub == "user123"
        assert claims.email == "test@example.com"
        
        monkeypatch.setattr(
            "src.infra_mind.core.auth.User.get",
            AsyncMock(return_value=user),
        )
        new_access_token, refreshed_user = await token_manager.refresh_access_token(refresh_token)
        assert refreshed_user is user
        new_claims = await token_manager.verify_token(new_access_token, TokenType.ACCESS)
        assert new_claims.sub == "user123"
        
        assert PasswordManager.verify_password(password, hashed_password) is True
    
    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, monkeypatch):
        """Test handling of expired tokens."""
        token_manager = TokenManager()
        user = DummyUser(user_id="user123", email="test@example.com")
        monkeypatch.setattr(
            "src.infra_mind.core.auth.User.get",
            AsyncMock(return_value=user),
        )
        
        short_expiry = timedelta(seconds=1)
        token = token_manager.create_access_token(user, short_expiry)
        
        claims = await token_manager.verify_token(token, TokenType.ACCESS)
        assert claims.sub == "user123"
        
        await asyncio.sleep(2)
        
        with pytest.raises(AuthenticationError, match="Token has expired"):
            await token_manager.verify_token(token, TokenType.ACCESS)
    
    def test_role_hierarchy(self):
        """Test role hierarchy in access control."""
        super_admin = DummyUser(user_id="super1", role="super_admin")
        admin = DummyUser(user_id="admin1", role="admin")
        manager = DummyUser(user_id="manager1", role="manager")
        user = DummyUser(user_id="user1", role="user")
        viewer = DummyUser(user_id="viewer1", role="viewer")
        
        assert AccessControl.user_has_permission(super_admin, Permission.MANAGE_SYSTEM) is True
        assert AccessControl.user_has_permission(admin, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(manager, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(user, Permission.MANAGE_SYSTEM) is False
        assert AccessControl.user_has_permission(viewer, Permission.MANAGE_SYSTEM) is False
        
        assert AccessControl.user_has_permission(admin, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(manager, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(user, Permission.READ_ASSESSMENT) is True
        assert AccessControl.user_has_permission(viewer, Permission.READ_ASSESSMENT) is True
        
        assert AccessControl.user_has_permission(admin, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(manager, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(user, Permission.CREATE_ASSESSMENT) is True
        assert AccessControl.user_has_permission(viewer, Permission.CREATE_ASSESSMENT) is False
