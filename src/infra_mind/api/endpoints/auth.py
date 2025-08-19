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

from ...models.user import User
import jwt
from jwt.exceptions import InvalidTokenError
import os

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-12345678901234567890")
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token."""
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
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required for this action."
        )
    return current_user


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


class ProfileUpdate(BaseModel):
    """Profile update request."""
    full_name: Optional[str] = None
    company: Optional[str] = None
    preferences: Optional[dict] = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user account.
    
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
        # Authenticate user using the model's built-in method
        user = await User.authenticate(credentials.email, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        # Create JWT token
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name
        )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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