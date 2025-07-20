"""
Configuration management for Infra Mind.

Uses Pydantic Settings for type-safe configuration with environment variable support.
This is a modern approach that provides validation, type hints, and easy testing.
"""

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Learning Note: Pydantic Settings automatically loads from environment variables
    and provides type validation. This is much better than manual os.environ access.
    """
    
    # Application
    app_name: str = "Infra Mind"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL"
    )
    mongodb_database: str = Field(
        default="infra_mind",
        description="MongoDB database name"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    redis_cache_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds (1 hour)"
    )
    
    # Authentication
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for LLM agents"
    )
    llm_model: str = Field(
        default="gpt-4",
        description="Default LLM model for agents"
    )
    llm_temperature: float = Field(
        default=0.1,
        description="LLM temperature for consistent responses"
    )
    
    # Cloud Provider APIs
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    
    gcp_service_account_path: Optional[str] = None
    gcp_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Terraform Cloud
    tf_cloud_token: Optional[str] = None
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Requests per minute per user"
    )
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v):
        """Basic MongoDB URL validation."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v):
        """Basic Redis URL validation."""
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra environment variables
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Learning Note: @lru_cache ensures we only create one Settings instance,
    which is important for performance and consistency.
    """
    return Settings()


# Global settings instance
settings = get_settings()