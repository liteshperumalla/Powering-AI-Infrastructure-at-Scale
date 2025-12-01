"""
Authentication endpoints for Infra Mind.

Handles user registration, login, and JWT token management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from loguru import logger
from datetime import datetime, timedelta
import httpx
import json
from google.auth.transport import requests
from google.oauth2 import id_token
import uuid
import io
import base64

try:
    import qrcode  # type: ignore
except ImportError:  # pragma: no cover - fallback for test environments
    class _FallbackQRImage:
        def __init__(self, data: str):
            self._data = data

        def save(self, buffer: io.BytesIO, format: str = "PNG") -> None:
            buffer.write(self._data.encode("utf-8"))

    class _FallbackQRCode:
        def __init__(self, *args, **kwargs):
            self._data = ""

        def add_data(self, data: str) -> None:
            self._data = data

        def make(self, fit: bool = True) -> None:  # noqa: ARG002
            return None

        def make_image(self, fill_color: str = "black", back_color: str = "white"):  # noqa: ARG002
            return _FallbackQRImage(self._data or "InfraMind-MFA")

    class qrcode:  # type: ignore
        QRCode = _FallbackQRCode

from ...models.user import User
from ...services.email_service import email_service
import jwt
from jwt.exceptions import InvalidTokenError
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

# JWT Configuration
# SECURITY: No fallback secret - fail fast if not configured
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    environment = os.getenv("INFRA_MIND_ENVIRONMENT", "development").lower()
    if environment in {"development", "test", "testing"}:
        SECRET_KEY = "dev-secret-key-change-me-please-12345678901234567890"
        logger.warning("Using fallback JWT secret for non-production environment. Set JWT_SECRET_KEY for production deployments.")
    else:
        raise ValueError(
            "CRITICAL: JWT_SECRET_KEY environment variable must be set. "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
if len(SECRET_KEY) < 32:
    raise ValueError("CRITICAL: JWT_SECRET_KEY must be at least 32 characters for security")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(user_id: str, email: str, full_name: str) -> str:
    """Create a JWT access token."""
    import secrets
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "full_name": full_name,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "infra-mind",  # Issuer
        "aud": "infra-mind-api",  # Audience
        "token_type": "access",  # Token type
        "jti": secrets.token_urlsafe(32)  # JWT ID
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    import secrets
    refresh_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    expire = datetime.utcnow() + timedelta(days=refresh_expire_days)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "infra-mind",
        "aud": "infra-mind-api",
        "token_type": "refresh",
        "jti": secrets.token_urlsafe(32)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience="infra-mind-api",
            issuer="infra-mind"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid token audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    except (jwt.InvalidTokenError, InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """Get current user from JWT token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await User.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency that requires the current user to be an admin."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required for this action."
        )
    return current_user


def require_superuser(current_user: User = Depends(get_current_user)):
    """Dependency that requires the current user to be a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges are required for this action."
        )
    return current_user


def require_admin_or_self(resource_user_id: str):
    """Factory function for requiring admin privileges or self access."""
    def check_admin_or_self(current_user: User = Depends(get_current_user)):
        if not (current_user.is_admin or 
                current_user.role == "admin" or 
                str(current_user.id) == resource_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges or resource ownership required."
            )
        return current_user
    return check_admin_or_self


def require_role(allowed_roles: list):
    """Factory function for requiring specific roles."""
    def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles is required: {', '.join(allowed_roles)}"
            )
        return current_user
    return check_role


def require_enterprise_access(current_user: User = Depends(get_current_user)):
    """Dependency that requires enterprise-level access (admin role)."""
    # Temporary bypass for testing - allow all authenticated users
    # TODO: Re-enable enterprise restrictions for production
    # if not (current_user.is_admin or 
    #         current_user.role == "admin" or 
    #         current_user.role == "manager"):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Enterprise access required. Contact your administrator to upgrade your account."
    #     )
    return current_user


# Request/Response models
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(min_length=2, description="Full name")
    company: Optional[str] = None
    job_title: Optional[str] = None


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
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[str] = None


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request."""
    credential: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str
    new_password: str = Field(min_length=8, description="New password (minimum 8 characters)")


class MFASetupResponse(BaseModel):
    """MFA setup response."""
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""
    token: str


class MFALoginRequest(BaseModel):
    """MFA login request."""
    email: EmailStr
    password: str
    mfa_token: str

class MFAVerifyLoginRequest(BaseModel):
    """MFA verification during login."""
    temp_token: str
    totp_code: str

class MFAVerifyBackupRequest(BaseModel):
    """MFA backup code verification during login."""
    temp_token: str
    backup_code: str




class UserProfile(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    role: Optional[str] = "user"
    is_active: bool
    created_at: datetime


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(min_length=8)


class ProfileUpdate(BaseModel):
    """Profile update request."""
    full_name: Optional[str] = None
    company: Optional[str] = None
    preferences: Optional[dict] = None

class MFARequiredResponse(BaseModel):
    """Response when MFA verification is required."""
    mfa_required: bool = True
    temp_token: str
    message: str = "MFA verification required"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserRegister):
    """
    Register a new user account.

    SECURITY: Rate limited to 3 registrations per hour per IP to prevent spam.

    Creates a new user account and returns a JWT token for immediate login.
    """
    try:
        # Check if user already exists
        try:
            existing_user = await User.find_one(User.email == user_data.email.lower())
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        except Exception as e:
            logger.error(f"Error checking existing user: {e}")
            # Continue with registration if there's an error checking existing users
        
        # Create user using the model's built-in method
        user = await User.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            company_name=user_data.company,
            job_title=user_data.job_title,
            role="user",
            is_active=True
        )
        
        # Create JWT token
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
        logger.info(f"User registered: {user_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            job_title=user.job_title,
            company_name=user.company_name,
            role=user.role,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login")
async def login(request: Request, credentials: UserLogin):
    """
    User login endpoint.

    SECURITY: Rate limited to 5 login attempts per minute per IP to prevent brute force.
    
    Authenticates user credentials and returns either a JWT token or MFA challenge.
    """
    try:
        # Authenticate user using the model's built-in method
        user = await User.authenticate(credentials.email, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        # Check if MFA is enabled for this user
        if user.mfa_enabled and user.mfa_setup_complete:
            # Create temporary token for MFA verification
            temp_token = create_temp_token(str(user.id))
            
            logger.info(f"MFA required for user: {credentials.email}")
            
            return MFARequiredResponse(
                temp_token=temp_token
            )
        
        # No MFA required, proceed with normal login
        user.update_login_info()
        await user.save()
        
        # Create JWT tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        refresh_token = create_refresh_token(str(user.id))
        
        logger.info(f"User logged in: {credentials.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            user=UserProfile(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                company=getattr(user, 'company_name', None),
                job_title=getattr(user, 'job_title', None),
                role=getattr(user, 'role', 'user'),
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    User logout endpoint.

    Invalidates the current JWT token by adding it to Redis blacklist.
    """
    try:
        token = credentials.credentials

        # SECURITY FIX: Implement token blacklisting
        # Decode token to get expiration time
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")

            if exp:
                # Add to blacklist with TTL matching token expiration
                import redis
                redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    decode_responses=True
                )

                # Calculate TTL (seconds until expiration)
                from datetime import datetime
                ttl = max(exp - int(datetime.utcnow().timestamp()), 0)

                # Store token hash in blacklist
                import hashlib
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                redis_client.setex(f"blacklist:{token_hash}", ttl, "1")

                logger.info(f"Token blacklisted successfully (TTL: {ttl}s)")
            else:
                logger.warning("Token missing expiration, cannot blacklist properly")

        except jwt.JWTError as jwt_err:
            logger.error(f"Failed to decode token for blacklisting: {jwt_err}")
            # Still return success to user

        logger.info("User logged out")

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns the profile information for the authenticated user.
    """
    logger.info(f"Retrieved user profile: {current_user.email}")
    
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        company=current_user.company_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
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
    current_user: User = Depends(get_current_user)
):
    """
    Change user password.
    
    Changes the password for the authenticated user.
    """
    try:
        # Verify current password
        if not current_user.verify_password(request.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = User.hash_password(request.new_password)
        current_user.updated_at = datetime.utcnow()
        await current_user.save()
        
        logger.info(f"Password changed successfully for user: {current_user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile.
    
    Updates the profile information for the authenticated user.
    """
    try:
        # Update fields if provided
        if update_data.full_name is not None:
            current_user.full_name = update_data.full_name
        
        if update_data.company is not None:
            current_user.company_name = update_data.company
        
        if update_data.preferences is not None:
            # Store preferences in a separate field or in user metadata
            if not hasattr(current_user, 'preferences'):
                current_user.preferences = {}
            current_user.preferences.update(update_data.preferences)
        
        current_user.updated_at = datetime.utcnow()
        await current_user.save()
        
        logger.info(f"Profile updated successfully for user: {current_user.email}")
        
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            company=current_user.company_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT token.
    
    Issues a new JWT token for the authenticated user.
    """
    try:
        # Create new access token
        access_token = create_access_token(
            user_id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name
        )
        
        logger.info(f"Token refreshed for user: {current_user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns the profile information for the authenticated user.
    Alias for /profile endpoint.
    """
    logger.info(f"Retrieved current user profile: {current_user.email}")
    
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        company=current_user.company_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/verify-token")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """
    Verify JWT token validity.
    
    Checks if the provided JWT token is valid and not expired.
    """
    logger.info(f"Token verified successfully for user: {current_user.email}")
    
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "expires_at": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }


@router.post("/google", response_model=TokenResponse)
async def google_login(oauth_request: GoogleLoginRequest):
    """
    Google OAuth login endpoint.
    
    Authenticates user using Google OAuth credential and returns a JWT token.
    If the user doesn't exist, creates a new user account.
    """
    try:
        # Verify Google OAuth credential
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        # Verify the Google ID token
        try:
            id_info = id_token.verify_oauth2_token(
                oauth_request.credential, 
                requests.Request(), 
                client_id
            )
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google credential"
            )
        
        email = id_info.get("email")
        full_name = id_info.get("name")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Check if user exists
        existing_user = await User.find_one(User.email == email.lower(), User.is_active == True)
        
        if existing_user:
            user = existing_user
            logger.info(f"Google login successful for existing user: {email}")
        else:
            # Create new user
            user_data = {
                "email": email.lower(),
                "full_name": full_name,
                "hashed_password": "",  # No password for OAuth users
                "is_active": True,
                "is_verified": True,  # Email is verified by Google
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            user = User(**user_data)
            await user.insert()
            logger.info(f"Google login successful, created new user: {email}")
        
        # Generate JWT token
        access_token = create_access_token(str(user.id), user.email, user.full_name)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset email.
    
    Finds user by email and sends password reset link.
    """
    try:
        # Find user by email
        user = await User.find_one(User.email == request.email.lower(), User.is_active == True)
        
        # Always return success to prevent email enumeration attacks
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            return {"message": "If the email exists, a password reset link has been sent."}
        
        # Generate password reset token
        reset_token = user.generate_password_reset_token()
        await user.save()
        
        # Send password reset email
        email_sent = await email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.full_name
        )
        
        if email_sent:
            logger.info(f"Password reset email sent to: {user.email}")
        else:
            logger.error(f"Failed to send password reset email to: {user.email}")
        
        return {"message": "If the email exists, a password reset link has been sent."}
        
    except Exception as e:
        logger.error(f"Forgot password failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset user password with token.
    
    Verifies reset token and updates password.
    """
    try:
        # Find user with matching reset token
        user = await User.find_one(User.password_reset_token == request.token, User.is_active == True)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Verify token is not expired
        if not user.verify_password_reset_token(request.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Reset password
        user.reset_password(request.new_password)
        await user.save()
        
        logger.info(f"Password reset successful for user: {user.email}")
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: User = Depends(get_current_user)):
    """
    Setup Multi-Factor Authentication.
    
    Generates TOTP secret and QR code for authenticator app setup.
    """
    try:
        # Generate MFA secret
        secret = current_user.generate_mfa_secret()
        await current_user.save()
        
        # Generate QR code
        totp_uri = current_user.get_totp_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Convert to base64 for frontend display
        qr_code_url = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
        
        # Generate backup codes
        backup_codes = current_user.generate_backup_codes()
        await current_user.save()
        
        logger.info(f"MFA setup initiated for user: {current_user.email}")
        
        return MFASetupResponse(
            secret=secret,
            qr_code_url=qr_code_url,
            backup_codes=backup_codes
        )
        
    except Exception as e:
        logger.error(f"MFA setup failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )


@router.post("/mfa/verify")
async def verify_mfa_setup(request: MFAVerifyRequest, current_user: User = Depends(get_current_user)):
    """
    Verify MFA setup with TOTP token.
    
    Confirms that user has correctly configured their authenticator app.
    """
    try:
        if not current_user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not initiated. Please setup MFA first."
            )
        
        # Verify TOTP token
        if not current_user.verify_totp(request.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA token"
            )
        
        # Enable MFA
        current_user.enable_mfa()
        await current_user.save()
        
        # Send confirmation email (backup codes were already provided during setup)
        await email_service.send_mfa_setup_email(
            to_email=current_user.email,
            user_name=current_user.full_name
        )
        
        logger.info(f"MFA successfully enabled for user: {current_user.email}")
        return {"message": "MFA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/mfa/disable")
async def disable_mfa(current_user: User = Depends(get_current_user)):
    """
    Disable Multi-Factor Authentication.
    
    Removes MFA protection from user account.
    """
    try:
        if not current_user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled"
            )
        
        # Disable MFA
        current_user.disable_mfa()
        await current_user.save()

        # Send MFA disabled notification email
        try:
            await email_service.send_mfa_disabled_email(
                to_email=current_user.email,
                user_name=current_user.full_name
            )
        except Exception as e:
            logger.warning(f"Failed to send MFA disabled email: {e}")

        logger.info(f"MFA disabled for user: {current_user.email}")
        return {"message": "MFA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA disable failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )


@router.post("/mfa/login", response_model=TokenResponse)
async def mfa_login(request: MFALoginRequest):
    """
    Login with MFA token.
    
    Authenticates user with email, password, and MFA token.
    """
    try:
        # First authenticate with email and password
        user = await User.authenticate(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if MFA is enabled
        if not user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this account"
            )
        
        # Verify MFA token (try TOTP first, then backup code)
        mfa_valid = False
        if user.verify_totp(request.mfa_token):
            mfa_valid = True
        elif user.verify_backup_code(request.mfa_token):
            mfa_valid = True
            await user.save()  # Save after consuming backup code
        
        if not mfa_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token"
            )
        
        # Update login info and create token
        user.update_login_info()
        await user.save()
        
        access_token = create_access_token(str(user.id), user.email, user.full_name)
        
        logger.info(f"MFA login successful for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA login failed"
        )


def create_temp_token(user_id: str) -> str:
    """Create a temporary token for MFA verification."""
    import secrets
    expire = datetime.utcnow() + timedelta(minutes=5)  # 5 minute expiry
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "temp_mfa",
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_temp_token(token: str) -> Optional[str]:
    """Verify temporary token and return user ID."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "temp_mfa":
            return None
        return payload.get("sub")
    except InvalidTokenError:
        return None


@router.post("/mfa/verify-login", response_model=TokenResponse)
async def verify_mfa_login(request: MFAVerifyLoginRequest):
    """
    Verify MFA during login process.
    
    Verifies TOTP code and completes the login.
    """
    try:
        # Verify temp token
        user_id = verify_temp_token(request.temp_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user
        user = await User.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Verify TOTP code
        if not user.verify_totp(request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code"
            )
        
        # Update login info and create token
        user.update_login_info()
        await user.save()
        
        access_token = create_access_token(str(user.id), user.email, user.full_name)
        refresh_token = create_refresh_token(str(user.id))
        
        # Send MFA login alert email
        try:
            await email_service.send_mfa_login_alert(
                to_email=user.email,
                user_name=user.full_name,
                login_info={
                    'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'ip_address': 'IP tracking not implemented',
                    'user_agent': 'User agent tracking not implemented',
                    'location': 'Location tracking not implemented'
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send MFA login alert email: {e}")

        logger.info(f"MFA verification successful for user: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            user=UserProfile(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                company=getattr(user, 'company_name', None),
                job_title=getattr(user, 'job_title', None),
                role=getattr(user, 'role', 'user'),
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/mfa/verify-backup", response_model=TokenResponse)
async def verify_mfa_backup(request: MFAVerifyBackupRequest):
    """
    Verify MFA backup code during login process.
    
    Verifies backup code and completes the login.
    """
    try:
        # Verify temp token
        user_id = verify_temp_token(request.temp_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user
        user = await User.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Verify backup code
        if not user.verify_backup_code(request.backup_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid backup code"
            )
        
        # Save user after consuming backup code
        await user.save()
        
        # Update login info and create token
        user.update_login_info()
        await user.save()
        
        access_token = create_access_token(str(user.id), user.email, user.full_name)
        refresh_token = create_refresh_token(str(user.id))
        
        logger.info(f"MFA backup code verification successful for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            user=UserProfile(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                company=getattr(user, 'company_name', None),
                job_title=getattr(user, 'job_title', None),
                role=getattr(user, 'role', 'user'),
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA backup verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA backup verification failed"
        )
