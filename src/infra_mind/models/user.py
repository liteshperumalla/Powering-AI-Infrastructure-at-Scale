"""
User model for Infra Mind.

Defines user authentication and profile data structure.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed
from pydantic import Field, EmailStr, field_validator
import bcrypt

from ..schemas.base import CompanySize, Industry


class User(Document):
    """
    User document model for authentication and profile management.
    
    Learning Note: This model handles user authentication, profile data,
    and tracks user activity for analytics and personalization.
    """
    
    # Authentication
    email: EmailStr = Indexed(unique=True)
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
        user = await cls.find_one(cls.email == email.lower(), cls.is_active == True)
        if user and user.verify_password(password):
            user.update_login_info()
            await user.save()
            return user
        return None
    
    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(email={self.email}, name={self.full_name})"