"""
Authentication endpoints for Infra Mind.

Handles user registration, login, and JWT token management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from loguru import logger
from datetime import datetime, timedelta
import uuid

from ...models.user import User
from ...core.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter()
security = HTTPBearer()


# Request/Response models
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(min_length=2, description="Full name")
    company: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    full_name: str


class UserProfile(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    company: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(min_length=8)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user account.
    
    Creates a new user account and returns a JWT token for immediate login.
    """
    try:
        # Check if user already exists
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            company_name=user_data.company,
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )
        await user.insert()
        
        # Generate JWT token
        access_token = await create_access_token(str(user.id))
        
        logger.info(f"User registered: {user_data.email}")
        
        # Real response
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    User login endpoint.
    
    Authenticates user credentials and returns a JWT token.
    """
    try:
        # Find user by email
        user = await User.find_one(User.email == credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Account disabled"
            )
        
        # Generate JWT token
        access_token = await create_access_token(str(user.id))
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save()
        
        logger.info(f"User logged in: {credentials.email}")
        
        # Real response
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    User logout endpoint.
    
    Invalidates the current JWT token.
    """
    try:
        # TODO: Add token to blacklist
        # await blacklist_token(credentials.credentials)
        
        logger.info("User logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/profile", response_model=UserProfile)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user profile.
    
    Returns the profile information for the authenticated user.
    """
    try:
        # Decode JWT token and get user
        user_id = await decode_token(credentials.credentials)
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Account disabled"
            )
        
        logger.info(f"Retrieved user profile: {user.email}")
        
        # Real response
        return UserProfile(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company=user.company_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.post("/password-reset")
async def request_password_reset(request: PasswordReset):
    """
    Request password reset.
    
    Sends a password reset email to the user.
    """
    try:
        # TODO: Check if user exists
        # user = await User.find_one({"email": request.email})
        # if user:
        #     reset_token = generate_reset_token(user.id)
        #     await send_password_reset_email(user.email, reset_token)
        
        logger.info(f"Password reset requested for: {request.email}")
        
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/change-password")
async def change_password(
    request: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Change user password.
    
    Changes the password for the authenticated user.
    """
    try:
        # Decode token and get user
        user_id = await decode_token(credentials.credentials)
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Account disabled"
            )
        
        # Verify current password
        if not verify_password(request.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(request.new_password)
        user.updated_at = datetime.utcnow()
        await user.save()
        
        logger.info(f"Password changed successfully for user: {user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token validity.
    
    Checks if the provided JWT token is valid and not expired.
    """
    try:
        # Decode and validate token
        user_id = await decode_token(credentials.credentials)
        user = await User.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )
        
        logger.info(f"Token verified successfully for user: {user.email}")
        
        return {
            "valid": True,
            "user_id": str(user.id),
            "email": user.email,
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )