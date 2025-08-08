"""
Production-ready configuration management for Infra Mind.

Enhanced configuration system with:
- Secure secrets management
- Environment-specific configurations
- Comprehensive validation
- Production security features
"""

import os
import secrets
from functools import lru_cache
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    """
    Production-ready application settings with comprehensive security and validation.
    
    Features:
    - Secure secret handling with SecretStr
    - Environment-specific configurations
    - Comprehensive validation
    - Production security defaults
    """
    
    # Application Configuration
    app_name: str = "Infra Mind"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Security Configuration
    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        description="JWT secret key - auto-generated if not provided"
    )
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # Password Security
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    
    # Database Configuration
    mongodb_url: SecretStr = Field(
        default=SecretStr("mongodb://admin:password@mongodb:27017/infra_mind?authSource=admin"),
        description="MongoDB connection URL"
    )
    mongodb_database: str = Field(
        default="infra_mind",
        description="MongoDB database name"
    )
    mongodb_max_connections: int = 100
    mongodb_min_connections: int = 10
    
    # Redis Configuration
    redis_url: SecretStr = Field(
        default=SecretStr("redis://localhost:6379"),
        description="Redis connection URL"
    )
    redis_cache_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds (1 hour)"
    )
    redis_max_connections: int = 20
    
    # LLM Configuration
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key for LLM agents"
    )
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google Gemini API key for Gemini models"
    )
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Anthropic API key for Claude models"
    )
    azure_openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Azure OpenAI API key"
    )
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = Field(
        default="2024-10-21",
        description="Azure OpenAI API version"
    )
    
    llm_model: str = Field(
        default="gpt-4",
        description="Default LLM model for agents"
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for consistent responses"
    )
    llm_max_tokens: int = Field(
        default=4000,
        ge=1,
        le=32000,
        description="Maximum tokens per LLM request"
    )
    llm_timeout: int = Field(
        default=60,
        description="LLM request timeout in seconds"
    )
    
    # AWS Configuration
    aws_access_key_id: Optional[SecretStr] = None
    aws_secret_access_key: Optional[SecretStr] = None
    aws_session_token: Optional[SecretStr] = None
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    
    # Azure Configuration
    azure_client_id: Optional[SecretStr] = None
    azure_client_secret: Optional[SecretStr] = None
    azure_tenant_id: Optional[SecretStr] = None
    azure_subscription_id: Optional[SecretStr] = None
    
    # GCP Configuration
    gcp_service_account_path: Optional[str] = None
    gcp_service_account_json: Optional[SecretStr] = None
    gcp_project_id: Optional[str] = None
    gcp_region: str = "us-central1"
    google_application_credentials: Optional[str] = None
    
    # Terraform Cloud Configuration
    tf_cloud_token: Optional[SecretStr] = None
    tf_cloud_organization: Optional[str] = None
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(
        default=100,
        description="Requests per minute per user"
    )
    rate_limit_burst: int = Field(
        default=200,
        description="Burst limit for rate limiting"
    )
    
    # Cloud API Rate Limits (per minute)
    aws_rate_limit: int = Field(
        default=100,
        description="AWS API requests per minute"
    )
    azure_rate_limit: int = Field(
        default=1000,
        description="Azure API requests per minute"
    )
    gcp_rate_limit: int = Field(
        default=100,
        description="GCP API requests per minute"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable Redis caching for API responses"
    )
    cache_default_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )
    cache_pricing_ttl: int = Field(
        default=86400,  # 24 hours
        description="Cache TTL for pricing data in seconds"
    )
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None
    
    # Monitoring and Observability
    sentry_dsn: Optional[SecretStr] = None
    metrics_enabled: bool = True
    health_check_interval: int = 30
    
    # Security Headers
    security_headers_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    
    # File Upload Configuration
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file upload size in bytes"
    )
    allowed_file_types: List[str] = [".json", ".yaml", ".yml", ".txt", ".csv"]
    
    # External Services
    google_search_api_key: Optional[SecretStr] = None
    google_search_engine_id: Optional[str] = None
    bing_search_api_key: Optional[SecretStr] = None
    
    # Webhook Configuration
    webhook_secret: Optional[SecretStr] = None
    webhook_timeout: int = 30
    
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
        """Enhanced MongoDB URL validation."""
        if isinstance(v, SecretStr):
            url = v.get_secret_value()
        else:
            url = v
        
        if not url.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        
        # In production, require authentication
        if os.getenv("INFRA_MIND_ENVIRONMENT") == "production":
            if "@" not in url:
                raise ValueError("Production MongoDB URL must include authentication")
        
        return v
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v):
        """Enhanced Redis URL validation."""
        if isinstance(v, SecretStr):
            url = v.get_secret_value()
        else:
            url = v
        
        if not url.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate JWT secret key strength."""
        if isinstance(v, SecretStr):
            key = v.get_secret_value()
        else:
            key = v
        
        if len(key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # In production, require strong secret key
        if os.getenv("INFRA_MIND_ENVIRONMENT") == "production":
            if key == "your-secret-key-change-in-production":
                raise ValueError("Must change default secret key in production")
        
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate logging level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()
    
    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins for production security."""
        if os.getenv("INFRA_MIND_ENVIRONMENT") == "production":
            # In production, don't allow wildcard origins
            if "*" in v:
                raise ValueError("Wildcard CORS origins not allowed in production")
            
            # Ensure all origins use HTTPS in production
            for origin in v:
                if not origin.startswith("https://") and not origin.startswith("http://localhost"):
                    raise ValueError(f"Production CORS origin must use HTTPS: {origin}")
        
        return v
    
    def __init__(self, **kwargs):
        """Initialize settings with environment-specific configuration."""
        super().__init__(**kwargs)
        self._validate_production_requirements()
    
    def _validate_production_requirements(self):
        """Validate production-specific requirements."""
        if self.environment == "production":
            # Require essential production configurations
            required_secrets = [
                ("openai_api_key", "OpenAI API key"),
                ("mongodb_url", "MongoDB URL"),
                ("redis_url", "Redis URL"),
            ]
            
            for attr, name in required_secrets:
                value = getattr(self, attr)
                if not value or (isinstance(value, SecretStr) and not value.get_secret_value()):
                    logging.warning(f"Production deployment missing {name}")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_database_url(self) -> str:
        """Get database URL as string."""
        if isinstance(self.mongodb_url, SecretStr):
            return self.mongodb_url.get_secret_value()
        return self.mongodb_url
    
    def get_redis_url(self) -> str:
        """Get Redis URL as string."""
        if isinstance(self.redis_url, SecretStr):
            return self.redis_url.get_secret_value()
        return self.redis_url
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key as string."""
        if self.openai_api_key and isinstance(self.openai_api_key, SecretStr):
            return self.openai_api_key.get_secret_value()
        return self.openai_api_key
    
    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key as string."""
        if self.gemini_api_key and isinstance(self.gemini_api_key, SecretStr):
            return self.gemini_api_key.get_secret_value()
        return self.gemini_api_key
    
    def get_aws_credentials(self) -> Dict[str, Optional[str]]:
        """Get AWS credentials as dictionary."""
        return {
            "access_key_id": self.aws_access_key_id.get_secret_value() if self.aws_access_key_id else None,
            "secret_access_key": self.aws_secret_access_key.get_secret_value() if self.aws_secret_access_key else None,
            "session_token": self.aws_session_token.get_secret_value() if self.aws_session_token else None,
            "region": self.aws_region,
            "profile": self.aws_profile
        }
    
    def get_azure_credentials(self) -> Dict[str, Optional[str]]:
        """Get Azure credentials as dictionary."""
        return {
            "client_id": self.azure_client_id.get_secret_value() if self.azure_client_id else None,
            "client_secret": self.azure_client_secret.get_secret_value() if self.azure_client_secret else None,
            "tenant_id": self.azure_tenant_id.get_secret_value() if self.azure_tenant_id else None,
            "subscription_id": self.azure_subscription_id.get_secret_value() if self.azure_subscription_id else None
        }
    
    def get_gcp_credentials(self) -> Dict[str, Optional[str]]:
        """Get GCP credentials as dictionary."""
        return {
            "service_account_path": self.gcp_service_account_path,
            "service_account_json": self.gcp_service_account_json.get_secret_value() if self.gcp_service_account_json else None,
            "project_id": self.gcp_project_id,
            "region": self.gcp_region
        }
    
    model_config = {
        "env_file": [".env.local", ".env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "env_prefix": "INFRA_MIND_",
        "validate_assignment": True,
        "use_enum_values": True
    }


class SecretsManager:
    """
    Production-ready secrets management with multiple backends.
    
    Supports:
    - Environment variables (default)
    - HashiCorp Vault (future)
    - AWS Secrets Manager (future)
    - Azure Key Vault (future)
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value from configured backend."""
        # For now, use environment variables
        # Future: Add support for external secret managers
        return os.getenv(f"INFRA_MIND_{key.upper()}", default)
    
    def validate_secrets(self) -> Dict[str, bool]:
        """Validate that all required secrets are available."""
        required_secrets = {
            "openai_api_key": bool(self.settings.get_openai_api_key()),
            "mongodb_url": bool(self.settings.get_database_url()),
            "redis_url": bool(self.settings.get_redis_url()),
            "secret_key": bool(self.settings.secret_key),
        }
        
        # Add cloud provider secrets if configured
        aws_creds = self.settings.get_aws_credentials()
        if aws_creds["access_key_id"]:
            required_secrets["aws_credentials"] = bool(aws_creds["secret_access_key"])
        
        azure_creds = self.settings.get_azure_credentials()
        if azure_creds["client_id"]:
            required_secrets["azure_credentials"] = bool(
                azure_creds["client_secret"] and azure_creds["tenant_id"]
            )
        
        gcp_creds = self.settings.get_gcp_credentials()
        if gcp_creds["project_id"]:
            required_secrets["gcp_credentials"] = bool(
                gcp_creds["service_account_path"] or gcp_creds["service_account_json"]
            )
        
        return required_secrets


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance with environment-specific configuration.
    
    Automatically loads the appropriate .env file based on environment.
    """
    return Settings()


# Global settings instance
settings = get_settings()

# Global secrets manager
secrets_manager = SecretsManager(settings)


def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return {
        "url": settings.get_database_url(),
        "database": settings.mongodb_database,
        "max_connections": settings.mongodb_max_connections,
        "min_connections": settings.mongodb_min_connections
    }


def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration."""
    return {
        "redis_url": settings.get_redis_url(),
        "cache_ttl": settings.cache_default_ttl,
        "pricing_ttl": settings.cache_pricing_ttl,
        "enabled": settings.cache_enabled,
        "max_connections": settings.redis_max_connections
    }


def get_rate_limit_config() -> Dict[str, int]:
    """Get rate limiting configuration."""
    return {
        "requests_per_minute": settings.rate_limit_requests,
        "burst_limit": settings.rate_limit_burst,
        "aws_limit": settings.aws_rate_limit,
        "azure_limit": settings.azure_rate_limit,
        "gcp_limit": settings.gcp_rate_limit
    }


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return {
        "secret_key": settings.secret_key.get_secret_value(),
        "algorithm": settings.algorithm,
        "access_token_expire_minutes": settings.access_token_expire_minutes,
        "refresh_token_expire_days": settings.refresh_token_expire_days,
        "password_min_length": settings.password_min_length,
        "password_require_special": settings.password_require_special,
        "password_require_numbers": settings.password_require_numbers,
        "password_require_uppercase": settings.password_require_uppercase
    }


def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration."""
    return {
        "origins": settings.cors_origins,
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers
    }


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return {
        "level": settings.log_level,
        "format": settings.log_format,
        "file": settings.log_file
    }


def validate_production_config() -> Dict[str, Any]:
    """Validate production configuration and return status."""
    if not settings.is_production:
        return {"valid": True, "warnings": [], "errors": []}
    
    warnings = []
    errors = []
    
    # Validate secrets
    secret_status = secrets_manager.validate_secrets()
    for secret, is_valid in secret_status.items():
        if not is_valid:
            errors.append(f"Missing required secret: {secret}")
    
    # Validate security settings
    if settings.debug:
        warnings.append("Debug mode is enabled in production")
    
    if "localhost" in settings.cors_origins:
        warnings.append("Localhost CORS origin allowed in production")
    
    # Validate database security
    db_url = settings.get_database_url()
    if "localhost" in db_url:
        warnings.append("Using localhost database in production")
    
    return {
        "valid": len(errors) == 0,
        "warnings": warnings,
        "errors": errors
    }


def setup_logging():
    """Setup logging configuration based on settings."""
    log_config = get_logging_config()
    
    # Configure logging format
    if log_config["format"] == "json":
        import json
        import datetime
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry)
        
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure handler
    if log_config["file"]:
        handler = logging.FileHandler(log_config["file"])
    else:
        handler = logging.StreamHandler()
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_config["level"]))
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    logging.getLogger("infra_mind").setLevel(getattr(logging, log_config["level"]))
    
    return root_logger