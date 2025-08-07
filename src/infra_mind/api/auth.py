"""
Production-grade authentication API endpoints for Infra Mind.

Handles user registration, login, token refresh, password management,
and comprehensive security features.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import logging
from datetime import datetime

from ..core.auth import (
    auth_service, AuthenticationError, security, get_current_active_user,
    log_authentication_event, log_security_event, AuditEventType, AuditSeverity
)
from ..models.user import User
from ..schemas.base import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models with enhanced validation
class LoginRequest(BaseModel):
    """Production-grade login request model."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=1, max_length=128)
    remember_me: bool = Field(default=False, description="Extend token expiration")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()


class RegisterRequest(BaseModel):
    """Production-grade user registration request model."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=8, max_length=128)
    full_name: str = Field(description="User's full name", min_length=2, max_length=100)
    company_name: Optional[str] = Field(default=None, description="Company name", max_length=200)
    job_title: Optional[str] = Field(default=None, description="Job title", max_length=100)
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        return v.strip()
    
    @validator('company_name')
    def validate_company_name(cls, v):
        return v.strip() if v else None


class TokenResponse(BaseModel):
    """Enhanced token response model."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(description="Token type (bearer)")
    expires_in: int = Field(description="Token expiration time in seconds")
    session_id: str = Field(description="Session identifier")
    user: dict = Field(description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(description="Valid refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr = Field(description="User email address")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str = Field(description="Password reset token")
    new_password: str = Field(description="New password", min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str = Field(description="Current password")
    new_password: str = Field(description="New password", min_length=8, max_length=128)


class UserInfoResponse(BaseModel):
    """User information response model."""
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


class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""
    full_name: Optional[str] = Field(default=None, description="User's full name", max_length=100)
    company: Optional[str] = Field(default=None, description="Company name", max_length=200)
    preferences: Optional[dict] = Field(default=None, description="User preferences")

    @validator('full_name')
    def validate_full_name(cls, v):
        return v.strip() if v else None
    
    @validator('company')
    def validate_company(cls, v):
        return v.strip() if v else None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, http_request: Request):
    """
    Register a new user account with comprehensive validation.
    
    Creates a new user account and returns authentication tokens.
    Includes security monitoring and audit logging.
    """
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    try:
        # Create user with enhanced validation
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company_name=request.company_name,
            job_title=request.job_title,
            ip_address=client_ip
        )
        
        # Create tokens
        tokens = await auth_service.create_tokens_for_user(user, client_ip)
        
        logger.info(f"New user registered: {user.email}")
        
        return TokenResponse(**tokens)
        
    except ValueError as e:
        logger.warning(f"Registration failed for {request.email}: {str(e)}")
        
        # Log registration failure
        log_security_event(
            AuditEventType.USER_CREATED,
            ip_address=client_ip,
            details={
                "email": request.email,
                "reason": str(e),
                "user_agent": user_agent
            },
            severity=AuditSeverity.MEDIUM
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {request.email}: {str(e)}")
        
        # Log system error
        log_security_event(
            AuditEventType.USER_CREATED,
            ip_address=client_ip,
            details={
                "email": request.email,
                "error": str(e),
                "user_agent": user_agent
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    Authenticate user with comprehensive security checks.
    
    Validates user credentials and returns JWT tokens for API access.
    Includes rate limiting, account lockout, and audit logging.
    """
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    try:
        # Authenticate user with security checks
        user = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not user:
            # Generic error message to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = await auth_service.create_tokens_for_user(user, client_ip)
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {str(e)}")
        
        # Log system error
        log_security_event(
            AuditEventType.LOGIN_FAILURE,
            ip_address=client_ip,
            details={
                "email": request.email,
                "error": str(e),
                "user_agent": user_agent
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, http_request: Request):
    """
    Refresh access token using refresh token with security validation.
    
    Generates a new access token from a valid refresh token.
    Includes comprehensive validation and audit logging.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Refresh access token with validation
        new_access_token, user = await auth_service.token_manager.refresh_access_token(
            request.refresh_token
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": auth_service.token_manager.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        
        # Log refresh failure
        log_security_event(
            AuditEventType.TOKEN_REFRESH,
            ip_address=client_ip,
            details={
                "error": str(e),
                "action": "refresh_failed"
            },
            severity=AuditSeverity.MEDIUM
        )
        
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
async def logout(
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user with token blacklisting for enhanced security.
    
    Revokes the current token and logs the logout event.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Logout user with token revocation
        await auth_service.logout_user(
            token=credentials.credentials,
            ip_address=client_ip
        )
        
        return SuccessResponse(
            message="Successfully logged out",
            data={"instruction": "Token has been revoked"}
        )
        
    except AuthenticationError as e:
        logger.warning(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information with comprehensive profile data.
    
    Returns the profile information of the currently authenticated user.
    """
    return UserInfoResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        job_title=current_user.job_title,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        login_count=current_user.login_count,
        assessments_created=current_user.assessments_created
    )


@router.get("/profile", response_model=UserInfoResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile (alias for /me endpoint).
    
    Returns the profile information of the currently authenticated user.
    """
    return UserInfoResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        job_title=current_user.job_title,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        login_count=current_user.login_count,
        assessments_created=current_user.assessments_created
    )


@router.put("/profile", response_model=UserInfoResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user profile with comprehensive validation.
    
    Updates the profile information for the authenticated user.
    Includes audit logging and validation.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Update fields if provided
        if request.full_name is not None:
            current_user.full_name = request.full_name
        
        if request.company is not None:
            current_user.company_name = request.company
        
        if request.preferences is not None:
            # Update preferences
            if not hasattr(current_user, 'preferences') or current_user.preferences is None:
                current_user.preferences = {}
            current_user.preferences.update(request.preferences)
        
        current_user.updated_at = datetime.utcnow()
        await current_user.save()
        
        logger.info(f"Profile updated successfully for user: {current_user.email}")
        
        # Log profile update
        log_security_event(
            AuditEventType.USER_UPDATED,
            user=current_user,
            ip_address=client_ip,
            details={
                "updated_fields": [
                    field for field, value in request.dict(exclude_unset=True).items()
                    if value is not None
                ]
            },
            severity=AuditSeverity.LOW
        )
        
        return UserInfoResponse(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            company_name=current_user.company_name,
            job_title=current_user.job_title,
            role=current_user.role,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            login_count=current_user.login_count,
            assessments_created=current_user.assessments_created
        )
        
    except Exception as e:
        logger.error(f"Failed to update profile for {current_user.email}: {str(e)}")
        
        # Log system error
        log_security_event(
            AuditEventType.USER_UPDATED,
            user=current_user,
            ip_address=client_ip,
            details={
                "error": str(e),
                "action": "profile_update_failed"
            },
            severity=AuditSeverity.MEDIUM
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/change-password", response_model=SuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Change user password with comprehensive validation.
    
    Allows authenticated users to change their password with
    strength validation and audit logging.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    try:
        # Change password with validation
        await auth_service.change_password(
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
            ip_address=client_ip
        )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return SuccessResponse(
            message="Password changed successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Change password error for {current_user.email}: {str(e)}")
        
        # Log system error
        log_security_event(
            AuditEventType.PASSWORD_CHANGE,
            user=current_user,
            ip_address=client_ip,
            details={"error": str(e)},
            severity=AuditSeverity.HIGH
        )
        
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
    Verify if a token is valid with comprehensive validation.
    
    Checks if the provided JWT token is valid and returns token info.
    """
    if not credentials:
        return {
            "valid": False,
            "error": "No token provided"
        }
    
    try:
        token = credentials.credentials
        claims = await auth_service.token_manager.verify_token(token)
        
        return {
            "valid": True,
            "user_id": claims.sub,
            "email": claims.email,
            "role": claims.role,
            "expires_at": claims.exp,
            "session_id": claims.session_id
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


@router.post("/revoke-token", response_model=SuccessResponse)
async def revoke_token(
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Revoke a specific token.
    
    Adds the token to the blacklist to prevent further use.
    """
    client_ip = http_request.client.host if http_request.client else None
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Revoke the token
        await auth_service.token_manager.revoke_token(credentials.credentials)
        
        return SuccessResponse(
            message="Token revoked successfully"
        )
        
    except AuthenticationError as e:
        logger.warning(f"Token revocation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token revocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed"
        )


# Dependency for getting current user (alias for compatibility)
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

# Dependency for getting current admin user
async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user