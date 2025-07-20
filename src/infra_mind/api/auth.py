"""
Authentication API endpoints for Infra Mind.

Handles user registration, login, token refresh, and password management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from ..core.auth import AuthService, TokenManager, AuthenticationError, security
from ..models.user import User
from ..schemas.base import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=1)
    remember_me: bool = Field(default=False, description="Extend token expiration")


class RegisterRequest(BaseModel):
    """User registration request model."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=8)
    full_name: str = Field(description="User's full name", min_length=1, max_length=100)
    company_name: Optional[str] = Field(default=None, description="Company name")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(description="Token type (bearer)")
    expires_in: int = Field(description="Token expiration time in seconds")
    user: dict = Field(description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(description="Valid refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr = Field(description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str = Field(description="Password reset token")
    new_password: str = Field(description="New password", min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str = Field(description="Current password")
    new_password: str = Field(description="New password", min_length=8)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    Creates a new user account and returns authentication tokens.
    """
    try:
        # Create user
        user = await AuthService.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company_name=request.company_name
        )
        
        # Create tokens
        tokens = AuthService.create_tokens_for_user(user)
        
        logger.info(f"New user registered: {user.email}")
        
        return TokenResponse(**tokens)
        
    except ValueError as e:
        logger.warning(f"Registration failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return tokens.
    
    Validates user credentials and returns JWT tokens for API access.
    """
    try:
        # Authenticate user
        user = await AuthService.authenticate_user(request.email, request.password)
        
        if not user:
            logger.warning(f"Failed login attempt for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = AuthService.create_tokens_for_user(user)
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Generates a new access token from a valid refresh token.
    """
    try:
        # Refresh access token
        new_access_token = TokenManager.refresh_access_token(request.refresh_token)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes in seconds
        }
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (client-side token invalidation).
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. In production, you might want to implement
    a token blacklist for enhanced security.
    """
    # In a stateless JWT system, logout is primarily client-side
    # The client should remove the tokens from storage
    
    # For enhanced security, you could implement token blacklisting here
    # by storing invalidated tokens in Redis with their expiration time
    
    logger.info("User logged out")
    
    return SuccessResponse(
        message="Successfully logged out",
        data={"instruction": "Remove tokens from client storage"}
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current user information.
    
    Returns the profile information of the currently authenticated user.
    """
    try:
        token = credentials.credentials
        user = await AuthService.get_current_user(token)
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "company_name": user.company_name,
            "company_size": user.company_size,
            "industry": user.industry,
            "job_title": user.job_title,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "login_count": user.login_count,
            "assessments_created": user.assessments_created
        }
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.put("/change-password", response_model=SuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Change user password.
    
    Allows authenticated users to change their password.
    """
    try:
        token = credentials.credentials
        user = await AuthService.get_current_user(token)
        
        # Verify current password
        if not user.verify_password(request.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        from ..core.auth import PasswordManager
        user.hashed_password = PasswordManager.hash_password(request.new_password)
        user.updated_at = user.created_at.__class__.utcnow()
        await user.save()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return SuccessResponse(
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/request-password-reset", response_model=SuccessResponse)
async def request_password_reset(request: PasswordResetRequest):
    """
    Request password reset.
    
    Sends a password reset token to the user's email.
    Note: In production, this would send an actual email.
    """
    try:
        user = await User.find_one(User.email == request.email.lower())
        
        if user:
            # Generate reset token
            from ..core.auth import PasswordManager
            from datetime import datetime, timedelta
            
            reset_token = PasswordManager.generate_password_reset_token()
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            await user.save()
            
            # In production, send email with reset link
            logger.info(f"Password reset requested for: {user.email}")
            
            # For development, return the token (remove in production!)
            return SuccessResponse(
                message="Password reset instructions sent to your email",
                data={"reset_token": reset_token}  # Remove in production!
            )
        else:
            # Don't reveal if email exists or not for security
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            
        return SuccessResponse(
            message="If the email exists, password reset instructions have been sent"
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(request: PasswordResetConfirm):
    """
    Reset password using reset token.
    
    Resets user password using a valid reset token.
    """
    try:
        from datetime import datetime
        
        # Find user with valid reset token
        user = await User.find_one(
            User.password_reset_token == request.token,
            User.password_reset_expires > datetime.utcnow()
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        from ..core.auth import PasswordManager
        user.hashed_password = PasswordManager.hash_password(request.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.updated_at = datetime.utcnow()
        await user.save()
        
        logger.info(f"Password reset completed for user: {user.email}")
        
        return SuccessResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/verify-token", response_model=dict)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify if a token is valid.
    
    Checks if the provided JWT token is valid and returns token info.
    """
    try:
        token = credentials.credentials
        payload = TokenManager.verify_token(token, "access")
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "expires_at": payload.get("exp")
        }
        
    except AuthenticationError as e:
        return {
            "valid": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return {
            "valid": False,
            "error": "Token verification failed"
        }