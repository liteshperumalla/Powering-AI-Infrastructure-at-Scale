"""
Authentication utilities for Infra Mind.

Handles JWT token generation, validation, and user authentication.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

from ..models.user import User
from ..schemas.base import ErrorResponse


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security scheme for FastAPI
security = HTTPBearer()


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class TokenManager:
    """
    JWT token management class.
    
    Learning Note: This class handles all JWT operations including
    token generation, validation, and refresh functionality.
    """
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: Data to encode in the token
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise AuthenticationError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                raise AuthenticationError("Token missing expiration")
            
            if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, timezone.utc):
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Create a new access token from a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            payload = TokenManager.verify_token(refresh_token, "refresh")
            
            # Create new access token with same user data
            new_token_data = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user")
            }
            
            return TokenManager.create_access_token(new_token_data)
            
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh token: {str(e)}")


class PasswordManager:
    """
    Password hashing and verification utilities.
    
    Learning Note: Using passlib for secure password hashing with bcrypt.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_password_reset_token() -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)


class AuthService:
    """
    Main authentication service.
    
    Learning Note: This service handles user authentication, registration,
    and token management operations.
    """
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            user = await User.find_one(
                User.email == email.lower(),
                User.is_active == True
            )
            
            if not user:
                return None
            
            if not PasswordManager.verify_password(password, user.hashed_password):
                return None
            
            # Update login info
            user.update_login_info()
            await user.save()
            
            return user
            
        except Exception:
            return None
    
    @staticmethod
    async def create_user(email: str, password: str, full_name: str, **kwargs) -> User:
        """
        Create a new user account.
        
        Args:
            email: User email
            password: Plain text password
            full_name: User's full name
            **kwargs: Additional user fields
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If user already exists or validation fails
        """
        # Check if user already exists
        existing_user = await User.find_one(User.email == email.lower())
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = PasswordManager.hash_password(password)
        
        # Create user
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            **kwargs
        )
        
        await user.insert()
        return user
    
    @staticmethod
    def create_tokens_for_user(user: User) -> Dict[str, Any]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": "user",  # Default role
            "full_name": user.full_name
        }
        
        access_token = TokenManager.create_access_token(token_data)
        refresh_token = TokenManager.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "company_name": user.company_name
            }
        }
    
    @staticmethod
    async def get_current_user(token: str) -> User:
        """
        Get current user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            Current user object
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        try:
            payload = TokenManager.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if user_id is None:
                raise AuthenticationError("Invalid token payload")
            
            user = await User.get(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to get current user: {str(e)}")


# FastAPI dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        user = await AuthService.get_current_user(token)
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Optional dependency for endpoints that work with or without authentication
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    FastAPI dependency to optionally get current user.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Current user object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = await AuthService.get_current_user(token)
        return user
    except:
        return None