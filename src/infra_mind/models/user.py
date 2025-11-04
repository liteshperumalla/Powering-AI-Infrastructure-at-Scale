"""
User model for Infra Mind.

Defines user authentication and profile data structure.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Annotated
from beanie import Document, Indexed
from pydantic import Field, EmailStr, field_validator
import bcrypt
import secrets
import pyotp
from cryptography.fernet import Fernet

from ..schemas.base import CompanySize, Industry


class User(Document):
    """
    User document model for authentication and profile management.

    Learning Note: This model handles user authentication, profile data,
    and tracks user activity for analytics and personalization.
    """

    # Authentication
    email: Annotated[EmailStr, Indexed(unique=True)] = Field(description="User email address")
    hashed_password: str = Field(description="Bcrypt hashed password")
    is_active: bool = Field(default=True, description="Whether user account is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    
    # Profile information
    full_name: str = Field(description="User's full name")
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_size: Optional[CompanySize] = Field(default=None, description="Company size")
    industry: Optional[Industry] = Field(default=None, description="Industry")
    job_title: Optional[str] = Field(default=None, description="Job title")
    
    # Role and permissions
    role: str = Field(default="user", description="User role (user, admin, manager, analyst, viewer)")
    is_admin: bool = Field(default=False, description="Whether user has admin privileges")
    is_superuser: bool = Field(default=False, description="Whether user has superuser privileges")
    
    # User preferences
    preferred_cloud_providers: List[str] = Field(
        default_factory=list,
        description="User's preferred cloud providers"
    )
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email_reports": True,
            "assessment_updates": True,
            "marketing": False
        },
        description="User notification preferences"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="General user preferences for UI, settings, etc."
    )
    
    # Activity tracking
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total number of logins")
    assessments_created: int = Field(default=0, description="Number of assessments created")
    
    # Account management
    password_reset_token: Optional[str] = Field(default=None, description="Password reset token")
    password_reset_expires: Optional[datetime] = Field(default=None, description="Password reset expiry")
    email_verification_token: Optional[str] = Field(default=None, description="Email verification token")
    
    # Multi-Factor Authentication
    mfa_enabled: bool = Field(default=False, description="Whether MFA is enabled")
    mfa_secret: Optional[str] = Field(default=None, description="TOTP secret key (encrypted)")
    mfa_backup_codes: List[str] = Field(default_factory=list, description="MFA backup codes (encrypted)")
    mfa_setup_complete: bool = Field(default=False, description="Whether MFA setup is complete")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "users"
        indexes = [
            [("email", 1)],  # Unique index for email
            [("is_active", 1)],  # Query active users
            [("company_size", 1), ("industry", 1)],  # Analytics queries
            [("created_at", -1)],  # Sort by registration date
        ]
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Additional email validation."""
        if not v or '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower()
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.hashed_password.encode('utf-8')
        )
    
    def update_login_info(self) -> None:
        """Update login tracking information."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.updated_at = datetime.utcnow()
    
    def increment_assessments(self) -> None:
        """Increment the assessments created counter."""
        self.assessments_created += 1
        self.updated_at = datetime.utcnow()
    
    @classmethod
    async def create_user(cls, email: str, password: str, full_name: str, **kwargs) -> "User":
        """Create a new user with hashed password."""
        user = cls(
            email=email.lower(),
            hashed_password=cls.hash_password(password),
            full_name=full_name,
            **kwargs
        )
        await user.insert()
        return user
    
    @classmethod
    async def authenticate(cls, email: str, password: str) -> Optional["User"]:
        """Authenticate a user by email and password."""
        # Use dictionary query syntax instead of class attribute syntax
        user = await cls.find_one({"email": email.lower(), "is_active": True})
        if user and user.verify_password(password):
            user.update_login_info()
            await user.save()
            return user
        return None
    
    def generate_password_reset_token(self) -> str:
        """Generate a secure password reset token."""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        self.updated_at = datetime.utcnow()
        return self.password_reset_token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token is valid and not expired."""
        return (
            self.password_reset_token == token and
            self.password_reset_expires and
            self.password_reset_expires > datetime.utcnow()
        )
    
    def reset_password(self, new_password: str) -> None:
        """Reset password and clear reset token."""
        self.hashed_password = self.hash_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
        self.updated_at = datetime.utcnow()
    
    def generate_mfa_secret(self) -> str:
        """Generate a new TOTP secret for MFA."""
        secret = pyotp.random_base32()
        # In production, encrypt this with proper key management
        self.mfa_secret = secret
        self.updated_at = datetime.utcnow()
        return secret
    
    def get_totp_uri(self, issuer_name: str = "Infra Mind") -> str:
        """Generate TOTP URI for QR code."""
        if not self.mfa_secret:
            raise ValueError("MFA secret not set")
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,
            issuer_name=issuer_name
        )
    
    def verify_totp(self, token: str) -> bool:
        """Verify TOTP token."""
        if not self.mfa_secret:
            return False
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)  # Allow 30s window
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate MFA backup codes."""
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        # In production, hash these codes before storing
        self.mfa_backup_codes = [self.hash_password(code) for code in codes]
        self.updated_at = datetime.utcnow()
        return codes  # Return unhashed codes for user to save
    
    def verify_backup_code(self, code: str) -> bool:
        """Verify and consume a backup code."""
        for i, hashed_code in enumerate(self.mfa_backup_codes):
            if bcrypt.checkpw(code.encode('utf-8'), hashed_code.encode('utf-8')):
                # Remove used backup code
                self.mfa_backup_codes.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def enable_mfa(self) -> None:
        """Enable MFA for the user."""
        self.mfa_enabled = True
        self.mfa_setup_complete = True
        self.updated_at = datetime.utcnow()
    
    def disable_mfa(self) -> None:
        """Disable MFA for the user."""
        self.mfa_enabled = False
        self.mfa_setup_complete = False
        self.mfa_secret = None
        self.mfa_backup_codes = []
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(email={self.email}, name={self.full_name})"