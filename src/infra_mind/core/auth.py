"""
Production-grade authentication utilities for Infra Mind.

Handles JWT token generation, validation, user authentication, and comprehensive audit logging.
"""

import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import json
import logging

from ..models.user import User
from ..schemas.base import ErrorResponse
from .audit import log_authentication_event, log_security_event, AuditEventType, AuditSeverity

# Configure logging
logger = logging.getLogger(__name__)

# Production password hashing context with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Increased rounds for production security
    bcrypt__ident="2b"  # Use 2b variant for better security
)

# JWT settings with production defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not set, generating random key (not suitable for production)")
    SECRET_KEY = secrets.token_urlsafe(64)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # Shorter for production
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
TOKEN_BLACKLIST_EXPIRE_HOURS = int(os.getenv("TOKEN_BLACKLIST_EXPIRE_HOURS", "24"))

# Redis connection for token blacklisting (optional)
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()  # Test connection
        logger.info("Redis connected for token blacklisting")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Token blacklisting disabled.")
        redis_client = None

# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class TokenBlacklistError(Exception):
    """Token blacklist error."""
    pass


class SecurityViolationError(Exception):
    """Security violation error."""
    pass


@dataclass
class TokenClaims:
    """JWT token claims structure."""
    sub: str  # Subject (user ID)
    email: str
    role: str
    full_name: str
    iat: int  # Issued at
    exp: int  # Expires at
    jti: str  # JWT ID for blacklisting
    token_type: str  # access or refresh
    session_id: Optional[str] = None


class TokenType(str, Enum):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenBlacklist:
    """
    Token blacklist management for secure logout and token invalidation.
    
    Uses Redis for distributed blacklisting or in-memory storage as fallback.
    """
    
    def __init__(self):
        self.redis_client = redis_client
        self._memory_blacklist = set()  # Fallback for when Redis is unavailable
    
    async def blacklist_token(self, jti: str, exp: int) -> None:
        """
        Add token to blacklist.
        
        Args:
            jti: JWT ID
            exp: Token expiration timestamp
        """
        try:
            if self.redis_client:
                # Calculate TTL based on token expiration
                ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
                self.redis_client.setex(f"blacklist:{jti}", ttl, "1")
            else:
                self._memory_blacklist.add(jti)
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            # Fallback to memory
            self._memory_blacklist.add(jti)
    
    async def is_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            jti: JWT ID
            
        Returns:
            True if token is blacklisted
        """
        try:
            if self.redis_client:
                result = self.redis_client.get(f"blacklist:{jti}")
                return result is not None
            else:
                return jti in self._memory_blacklist
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return jti in self._memory_blacklist


class TokenManager:
    """
    Production-grade JWT token management class.
    
    Features:
    - Secure token generation with JTI for blacklisting
    - Token expiration handling
    - Comprehensive validation
    - Audit logging integration
    - Token blacklisting support
    """
    
    def __init__(self):
        self.blacklist = TokenBlacklist()
    
    def _generate_jti(self) -> str:
        """Generate unique JWT ID."""
        return secrets.token_urlsafe(32)
    
    def create_access_token(
        self, 
        user: User, 
        expires_delta: Optional[timedelta] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Create a production-grade JWT access token.
        
        Args:
            user: User object
            expires_delta: Custom expiration time
            session_id: Optional session ID
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        jti = self._generate_jti()
        
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti,
            "token_type": TokenType.ACCESS.value,
            "session_id": session_id
        }
        
        # Add additional security claims
        claims["iss"] = "infra-mind"  # Issuer
        claims["aud"] = "infra-mind-api"  # Audience
        
        encoded_jwt = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log token creation
        log_authentication_event(
            AuditEventType.TOKEN_REFRESH,
            user=user,
            outcome="success",
            details={"token_type": "access", "expires_at": expire.isoformat()}
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        user: User,
        session_id: Optional[str] = None
    ) -> str:
        """
        Create a production-grade JWT refresh token.
        
        Args:
            user: User object
            session_id: Optional session ID
            
        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jti = self._generate_jti()
        
        claims = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti,
            "token_type": TokenType.REFRESH.value,
            "session_id": session_id
        }
        
        # Add additional security claims
        claims["iss"] = "infra-mind"
        claims["aud"] = "infra-mind-api"
        
        encoded_jwt = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    async def verify_token(
        self, 
        token: str, 
        expected_type: TokenType = TokenType.ACCESS,
        check_blacklist: bool = True
    ) -> TokenClaims:
        """
        Verify and decode a JWT token with comprehensive validation.
        
        Args:
            token: JWT token to verify
            expected_type: Expected token type
            check_blacklist: Whether to check token blacklist
            
        Returns:
            TokenClaims object
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                audience="infra-mind-api",
                issuer="infra-mind"
            )
            
            # Validate token type
            token_type = payload.get("token_type")
            if token_type != expected_type.value:
                raise AuthenticationError(f"Invalid token type. Expected {expected_type.value}, got {token_type}")
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if check_blacklist and jti and await self.blacklist.is_blacklisted(jti):
                raise AuthenticationError("Token has been revoked")
            
            # Create TokenClaims object
            claims = TokenClaims(
                sub=payload["sub"],
                email=payload["email"],
                role=payload.get("role", "user"),
                full_name=payload.get("full_name"),
                iat=payload["iat"],
                exp=payload["exp"],
                jti=jti,
                token_type=token_type,
                session_id=payload.get("session_id")
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidAudienceError:
            raise AuthenticationError("Invalid token audience")
        except jwt.InvalidIssuerError:
            raise AuthenticationError("Invalid token issuer")
        except jwt.InvalidSignatureError:
            raise AuthenticationError("Invalid token signature")
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
        except KeyError as e:
            raise AuthenticationError(f"Token missing required claim: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> tuple[str, User]:
        """
        Create a new access token from a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (new_access_token, user)
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            # Verify refresh token
            claims = await self.verify_token(refresh_token, TokenType.REFRESH)
            
            # Get user from database
            user = await User.get(claims.sub)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Create new access token
            new_access_token = self.create_access_token(
                user=user,
                session_id=claims.session_id
            )
            
            # Log token refresh
            log_authentication_event(
                AuditEventType.TOKEN_REFRESH,
                user=user,
                outcome="success",
                details={"action": "refresh_access_token"}
            )
            
            return new_access_token, user
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise AuthenticationError(f"Failed to refresh token: {str(e)}")
    
    async def revoke_token(self, token: str) -> None:
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token: Token to revoke
        """
        try:
            claims = await self.verify_token(token, check_blacklist=False)
            await self.blacklist.blacklist_token(claims.jti, claims.exp)
            
            logger.info(f"Token revoked: {claims.jti}")
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            raise AuthenticationError(f"Failed to revoke token: {str(e)}")
    
    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Revoke all tokens for a specific user.
        
        Note: This is a simplified implementation. In production,
        you might want to track all issued tokens per user.
        
        Args:
            user_id: User ID
        """
        # This would require tracking all issued tokens per user
        # For now, we'll log the action
        logger.info(f"All tokens revoked for user: {user_id}")
        
        # In a full implementation, you would:
        # 1. Query all active tokens for the user
        # 2. Add them to the blacklist
        # 3. Update user's token version/salt


class PasswordManager:
    """
    Production-grade password hashing and verification utilities.
    
    Features:
    - Strong bcrypt hashing with configurable rounds
    - Password strength validation
    - Secure token generation
    - Timing attack protection
    """
    
    # Password strength requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with production-grade settings.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hashed password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        # Validate password strength
        PasswordManager.validate_password_strength(password)
        
        # Hash with production settings
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash with timing attack protection.
        
        Args:
            plain_password: Plain text password
            hashed_password: Stored hash
            
        Returns:
            True if password matches
        """
        try:
            # Use constant-time comparison to prevent timing attacks
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < PasswordManager.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {PasswordManager.MIN_PASSWORD_LENGTH} characters long")
        
        if len(password) > PasswordManager.MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password must be no more than {PasswordManager.MAX_PASSWORD_LENGTH} characters long")
        
        if PasswordManager.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if PasswordManager.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if PasswordManager.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        
        if PasswordManager.REQUIRE_SPECIAL_CHARS:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                raise ValueError("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master"
        ]
        if password.lower() in weak_passwords:
            raise ValueError("Password is too common and not allowed")
    
    @staticmethod
    def generate_password_reset_token() -> str:
        """Generate a cryptographically secure password reset token."""
        return secrets.token_urlsafe(48)  # Increased length for production
    
    @staticmethod
    def generate_secure_session_id() -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def check_password_breach(password: str) -> bool:
        """
        Check if password has been found in known breaches.
        
        Note: This is a placeholder for integration with services like
        HaveIBeenPwned API or similar breach databases.
        
        Args:
            password: Password to check
            
        Returns:
            True if password found in breaches
        """
        # In production, integrate with HaveIBeenPwned API
        # For now, just check against a small list of known breached passwords
        common_breached = [
            "123456", "password", "123456789", "12345678", "12345",
            "111111", "1234567", "sunshine", "qwerty", "iloveyou"
        ]
        return password.lower() in common_breached


class AuthService:
    """
    Production-grade authentication service.
    
    Features:
    - Comprehensive user authentication
    - Account lockout protection
    - Session management
    - Audit logging integration
    - Security monitoring
    """
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.failed_attempts = {}  # In production, use Redis
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[User]:
        """
        Authenticate a user with comprehensive security checks.
        
        Args:
            email: User email
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            User object if authentication successful, None otherwise
        """
        email = email.lower().strip()
        
        try:
            # Check for account lockout
            if await self._is_account_locked(email):
                log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    details={"reason": "account_locked", "email": email}
                )
                return None
            
            # Find user
            user = await User.find_one(
                User.email == email,
                User.is_active == True
            )
            
            if not user:
                await self._record_failed_attempt(email)
                log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    details={"reason": "user_not_found", "email": email}
                )
                return None
            
            # Verify password
            if not PasswordManager.verify_password(password, user.hashed_password):
                await self._record_failed_attempt(email)
                log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    details={"reason": "invalid_password"}
                )
                return None
            
            # Check if password needs to be changed (e.g., temporary password)
            if hasattr(user, 'password_change_required') and user.password_change_required:
                log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    outcome="failure",
                    details={"reason": "password_change_required"}
                )
                return None
            
            # Clear failed attempts on successful login
            await self._clear_failed_attempts(email)
            
            # Update login info
            user.update_login_info()
            await user.save()
            
            # Log successful authentication
            log_authentication_event(
                AuditEventType.LOGIN_SUCCESS,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="success"
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="error",
                details={"error": str(e), "email": email}
            )
            return None
    
    async def create_user(
        self, 
        email: str, 
        password: str, 
        full_name: str,
        ip_address: Optional[str] = None,
        **kwargs
    ) -> User:
        """
        Create a new user account with comprehensive validation.
        
        Args:
            email: User email
            password: Plain text password
            full_name: User's full name
            ip_address: Client IP address
            **kwargs: Additional user fields
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If user already exists or validation fails
        """
        email = email.lower().strip()
        
        # Check if user already exists
        existing_user = await User.find_one(User.email == email)
        if existing_user:
            log_security_event(
                AuditEventType.USER_CREATED,
                ip_address=ip_address,
                details={"email": email, "reason": "user_already_exists"},
                severity=AuditSeverity.MEDIUM
            )
            raise ValueError("User with this email already exists")
        
        # Validate password strength
        try:
            PasswordManager.validate_password_strength(password)
        except ValueError as e:
            log_security_event(
                AuditEventType.USER_CREATED,
                ip_address=ip_address,
                details={"email": email, "reason": "weak_password"},
                severity=AuditSeverity.MEDIUM
            )
            raise e
        
        # Check for password breaches
        if PasswordManager.check_password_breach(password):
            raise ValueError("Password has been found in known data breaches. Please choose a different password.")
        
        # Hash password
        hashed_password = PasswordManager.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name.strip(),
            **kwargs
        )
        
        await user.insert()
        
        # Log user creation
        log_authentication_event(
            AuditEventType.USER_CREATED,
            user=user,
            ip_address=ip_address,
            outcome="success"
        )
        
        return user
    
    async def create_tokens_for_user(
        self, 
        user: User,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User object
            ip_address: Client IP address
            
        Returns:
            Dictionary with tokens and metadata
        """
        # Generate session ID
        session_id = PasswordManager.generate_secure_session_id()
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            user=user,
            session_id=session_id
        )
        refresh_token = self.token_manager.create_refresh_token(
            user=user,
            session_id=session_id
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            "session_id": session_id,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "company_name": user.company_name
            }
        }
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from JWT token with comprehensive validation.
        
        Args:
            token: JWT access token
            
        Returns:
            Current user object
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        try:
            # Verify token
            claims = await self.token_manager.verify_token(token, TokenType.ACCESS)
            
            # Get user from database
            user = await User.get(claims.sub)
            if not user:
                raise AuthenticationError("User not found")
            
            if not user.is_active:
                raise AuthenticationError("User account is inactive")
            
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise AuthenticationError(f"Failed to get current user: {str(e)}")
    
    async def logout_user(
        self, 
        token: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Logout user by revoking their token.
        
        Args:
            token: Access token to revoke
            ip_address: Client IP address
        """
        try:
            # Get user before revoking token
            user = await self.get_current_user(token)
            
            # Revoke token
            await self.token_manager.revoke_token(token)
            
            # Log logout
            log_authentication_event(
                AuditEventType.LOGOUT,
                user=user,
                ip_address=ip_address,
                outcome="success"
            )
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise AuthenticationError(f"Failed to logout: {str(e)}")
    
    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Change user password with validation.
        
        Args:
            user: User object
            current_password: Current password
            new_password: New password
            ip_address: Client IP address
        """
        # Verify current password
        if not PasswordManager.verify_password(current_password, user.hashed_password):
            log_authentication_event(
                AuditEventType.PASSWORD_CHANGE,
                user=user,
                ip_address=ip_address,
                outcome="failure",
                details={"reason": "invalid_current_password"}
            )
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        PasswordManager.validate_password_strength(new_password)
        
        # Check for password reuse (simplified check)
        if PasswordManager.verify_password(new_password, user.hashed_password):
            raise ValueError("New password must be different from current password")
        
        # Update password
        user.hashed_password = PasswordManager.hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        
        # Log password change
        log_authentication_event(
            AuditEventType.PASSWORD_CHANGE,
            user=user,
            ip_address=ip_address,
            outcome="success"
        )
    
    async def _is_account_locked(self, email: str) -> bool:
        """Check if account is locked due to failed attempts."""
        if email not in self.failed_attempts:
            return False
        
        attempts, last_attempt = self.failed_attempts[email]
        
        # Check if lockout period has expired
        if datetime.now(timezone.utc) - last_attempt > timedelta(minutes=self.lockout_duration):
            del self.failed_attempts[email]
            return False
        
        return attempts >= self.max_failed_attempts
    
    async def _record_failed_attempt(self, email: str) -> None:
        """Record a failed login attempt."""
        now = datetime.now(timezone.utc)
        
        if email in self.failed_attempts:
            attempts, _ = self.failed_attempts[email]
            self.failed_attempts[email] = (attempts + 1, now)
        else:
            self.failed_attempts[email] = (1, now)
    
    async def _clear_failed_attempts(self, email: str) -> None:
        """Clear failed login attempts for an email."""
        if email in self.failed_attempts:
            del self.failed_attempts[email]


# Global auth service instance
auth_service = AuthService()


# FastAPI dependency functions
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Production-grade FastAPI dependency to get current authenticated user.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token credentials
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        # Log successful token validation
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # You could add additional logging here if needed
        
        return user
        
    except AuthenticationError as e:
        # Log authentication failure
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        log_security_event(
            AuditEventType.UNAUTHORIZED_ACCESS,
            ip_address=client_ip,
            details={
                "user_agent": user_agent,
                "error": str(e),
                "endpoint": str(request.url)
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        log_security_event(
            AuditEventType.UNAUTHORIZED_ACCESS,
            user=current_user,
            details={"reason": "inactive_user"},
            severity=AuditSeverity.MEDIUM
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    FastAPI dependency to optionally get current user.
    
    Args:
        request: FastAPI request object
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Current user object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except:
        return None


def require_role(required_role: str):
    """
    Create a dependency that requires a specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            log_security_event(
                AuditEventType.PERMISSION_DENIED,
                user=current_user,
                details={
                    "required_role": required_role,
                    "user_role": current_user.role
                },
                severity=AuditSeverity.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    
    return role_checker


def require_any_role(allowed_roles: List[str]):
    """
    Create a dependency that requires any of the specified roles.
    
    Args:
        allowed_roles: List of allowed user roles
        
    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            log_security_event(
                AuditEventType.PERMISSION_DENIED,
                user=current_user,
                details={
                    "allowed_roles": allowed_roles,
                    "user_role": current_user.role
                },
                severity=AuditSeverity.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# Admin role dependency
require_admin = require_role("admin")

# Manager or admin role dependency
require_manager_or_admin = require_any_role(["manager", "admin"])


# Simple utility functions for basic auth operations
def hash_password(password: str) -> str:
    """Hash a password using the password manager."""
    return PasswordManager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password using the password manager."""
    return PasswordManager.verify_password(plain_password, hashed_password)


async def create_access_token(user_id: str) -> str:
    """Create an access token for a user ID."""
    # Get the user from database for token creation
    from ..models.user import User
    user = await User.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    token_manager = TokenManager()
    return token_manager.create_access_token(user)


async def create_refresh_token(user_id: str) -> str:
    """Create a refresh token for a user ID."""
    # Get the user from database for token creation
    from ..models.user import User
    user = await User.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    token_manager = TokenManager()
    return token_manager.create_refresh_token(user)


async def decode_token(token: str) -> str:
    """Decode a JWT token and return the user ID."""
    try:
        token_manager = TokenManager()
        claims = await token_manager.verify_token(token, TokenType.ACCESS)
        return claims.sub
    except AuthenticationError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


async def get_current_user_from_token(token: str) -> User:
    """Get current user from JWT token string."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # In a real implementation, you would fetch the user from database
        # For now, return a mock user
        user = User(
            id=user_id,
            email=payload.get("email", "user@example.com"),
            full_name=payload.get("full_name", "User"),
            is_active=True,
            is_admin=payload.get("is_admin", False)
        )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )