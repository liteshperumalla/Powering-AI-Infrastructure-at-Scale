#!/usr/bin/env python3
"""
Configuration validation script for Infra Mind production deployment.

This script validates:
- Environment configuration
- Secret availability
- Database connectivity
- Cloud provider credentials
- Security settings
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.config import get_settings, validate_production_config, setup_logging
from infra_mind.core.secrets import validate_production_secrets, secrets_manager


class ConfigValidator:
    """Configuration validation utility."""
    
    def __init__(self):
        self.settings = get_settings()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Validating Infra Mind Configuration...")
        print("=" * 50)
        
        # Basic configuration validation
        self._validate_basic_config()
        
        # Secrets validation
        self._validate_secrets()
        
        # Database validation
        self._validate_database_config()
        
        # Cloud provider validation
        self._validate_cloud_providers()
        
        # Security validation
        self._validate_security_config()
        
        # LLM validation
        self._validate_llm_config()
        
        # Production-specific validation
        if self.settings.is_production:
            self._validate_production_specific()
        
        return self._generate_report()
    
    def _validate_basic_config(self):
        """Validate basic application configuration."""
        print("📋 Validating basic configuration...")
        
        # Environment validation
        if self.settings.environment not in ["development", "staging", "production"]:
            self.errors.append(f"Invalid environment: {self.settings.environment}")
        else:
            self.info.append(f"Environment: {self.settings.environment}")
        
        # API configuration
        if not (1 <= self.settings.api_port <= 65535):
            self.errors.append(f"Invalid API port: {self.settings.api_port}")
        
        # Debug mode check
        if self.settings.is_production and self.settings.debug:
            self.warnings.append("Debug mode is enabled in production")
        
        print(f"   ✓ Environment: {self.settings.environment}")
        print(f"   ✓ API Port: {self.settings.api_port}")
        print(f"   ✓ Debug Mode: {self.settings.debug}")
    
    def _validate_secrets(self):
        """Validate secrets availability."""
        print("\n🔐 Validating secrets...")
        
        secret_validation = validate_production_secrets()
        
        if secret_validation["valid"]:
            print(f"   ✓ All {secret_validation['total_secrets']} required secrets are available")
        else:
            print(f"   ❌ {len(secret_validation['missing_secrets'])} secrets missing:")
            for secret in secret_validation["missing_secrets"]:
                print(f"      - {secret}")
                self.errors.append(f"Missing required secret: {secret}")
        
        # Health check on secret backends
        health = secrets_manager.health_check()
        if health["healthy"]:
            print("   ✓ Secret backends are healthy")
        else:
            print("   ❌ Secret backend issues:")
            for error in health["errors"]:
                print(f"      - {error}")
                self.errors.append(f"Secret backend error: {error}")
    
    def _validate_database_config(self):
        """Validate database configuration."""
        print("\n🗄️  Validating database configuration...")
        
        # MongoDB URL validation
        mongodb_url = self.settings.get_database_url()
        if not mongodb_url:
            self.errors.append("MongoDB URL is not configured")
        elif self.settings.is_production and "localhost" in mongodb_url:
            self.warnings.append("Using localhost MongoDB in production")
        
        # Redis URL validation
        redis_url = self.settings.get_redis_url()
        if not redis_url:
            self.errors.append("Redis URL is not configured")
        elif self.settings.is_production and "localhost" in redis_url:
            self.warnings.append("Using localhost Redis in production")
        
        print(f"   ✓ MongoDB configured: {bool(mongodb_url)}")
        print(f"   ✓ Redis configured: {bool(redis_url)}")
        
        # Connection pool settings
        if self.settings.mongodb_max_connections < self.settings.mongodb_min_connections:
            self.errors.append("MongoDB max_connections must be >= min_connections")
    
    def _validate_cloud_providers(self):
        """Validate cloud provider configurations."""
        print("\n☁️  Validating cloud provider configurations...")
        
        # AWS validation
        aws_creds = self.settings.get_aws_credentials()
        aws_configured = bool(aws_creds["access_key_id"] and aws_creds["secret_access_key"])
        print(f"   AWS: {'✓' if aws_configured else '⚠️'} {'Configured' if aws_configured else 'Not configured'}")
        
        if aws_configured and self.settings.is_production:
            if not aws_creds["region"]:
                self.warnings.append("AWS region not specified")
        
        # Azure validation
        azure_creds = self.settings.get_azure_credentials()
        azure_configured = bool(
            azure_creds["client_id"] and 
            azure_creds["client_secret"] and 
            azure_creds["tenant_id"]
        )
        print(f"   Azure: {'✓' if azure_configured else '⚠️'} {'Configured' if azure_configured else 'Not configured'}")
        
        # GCP validation
        gcp_creds = self.settings.get_gcp_credentials()
        gcp_configured = bool(
            gcp_creds["project_id"] and 
            (gcp_creds["service_account_path"] or gcp_creds["service_account_json"])
        )
        print(f"   GCP: {'✓' if gcp_configured else '⚠️'} {'Configured' if gcp_configured else 'Not configured'}")
        
        if not (aws_configured or azure_configured or gcp_configured):
            self.warnings.append("No cloud providers configured - limited functionality")
    
    def _validate_security_config(self):
        """Validate security configuration."""
        print("\n🔒 Validating security configuration...")
        
        # Secret key validation
        secret_key = self.settings.secret_key.get_secret_value()
        if len(secret_key) < 32:
            self.errors.append("Secret key must be at least 32 characters long")
        elif secret_key == "your-secret-key-change-in-production":
            self.errors.append("Must change default secret key")
        else:
            print("   ✓ Secret key is properly configured")
        
        # CORS validation
        if self.settings.is_production:
            if "localhost" in self.settings.cors_origins:
                self.warnings.append("Localhost CORS origin allowed in production")
            
            for origin in self.settings.cors_origins:
                if not origin.startswith("https://") and not origin.startswith("http://localhost"):
                    self.warnings.append(f"Non-HTTPS CORS origin in production: {origin}")
        
        print(f"   ✓ CORS origins: {len(self.settings.cors_origins)} configured")
        
        # Rate limiting
        if self.settings.rate_limit_requests < 10:
            self.warnings.append("Very low rate limit may impact usability")
        
        print(f"   ✓ Rate limiting: {self.settings.rate_limit_requests} requests/minute")
    
    def _validate_llm_config(self):
        """Validate LLM configuration."""
        print("\n🤖 Validating LLM configuration...")
        
        # OpenAI API key
        openai_key = self.settings.get_openai_api_key()
        if not openai_key:
            self.errors.append("OpenAI API key is required")
        elif not openai_key.startswith("sk-"):
            self.warnings.append("OpenAI API key format may be incorrect")
        else:
            print("   ✓ OpenAI API key configured")
        
        # Model configuration
        if self.settings.llm_temperature < 0 or self.settings.llm_temperature > 2:
            self.errors.append("LLM temperature must be between 0 and 2")
        
        if self.settings.llm_max_tokens < 100 or self.settings.llm_max_tokens > 32000:
            self.warnings.append("LLM max_tokens may be outside optimal range")
        
        print(f"   ✓ Model: {self.settings.llm_model}")
        print(f"   ✓ Temperature: {self.settings.llm_temperature}")
        print(f"   ✓ Max tokens: {self.settings.llm_max_tokens}")
    
    def _validate_production_specific(self):
        """Validate production-specific requirements."""
        print("\n🏭 Validating production-specific configuration...")
        
        prod_validation = validate_production_config()
        
        if prod_validation["valid"]:
            print("   ✓ Production configuration is valid")
        else:
            print("   ❌ Production configuration issues:")
            for error in prod_validation["errors"]:
                print(f"      - {error}")
                self.errors.append(error)
        
        for warning in prod_validation["warnings"]:
            print(f"   ⚠️  {warning}")
            self.warnings.append(warning)
        
        # Additional production checks
        if not self.settings.log_file and self.settings.is_production:
            self.warnings.append("No log file configured for production")
        
        if self.settings.cache_enabled and not self.settings.get_redis_url():
            self.errors.append("Caching enabled but Redis not configured")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION REPORT")
        print("=" * 50)
        
        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            print("🎉 Configuration validation PASSED!")
            print("   All checks completed successfully.")
        else:
            print(f"⚠️  Configuration validation completed with {total_issues} issues:")
            print(f"   - {len(self.errors)} errors")
            print(f"   - {len(self.warnings)} warnings")
        
        # Errors
        if self.errors:
            print("\n❌ ERRORS (must be fixed):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS (should be reviewed):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        # Info
        if self.info:
            print("\nℹ️  INFORMATION:")
            for info in self.info:
                print(f"   - {info}")
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "total_issues": total_issues
        }


async def test_database_connectivity():
    """Test database connectivity."""
    print("\n🔌 Testing database connectivity...")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        settings = get_settings()
        
        # Test MongoDB
        client = AsyncIOMotorClient(settings.get_database_url())
        await client.admin.command('ping')
        print("   ✓ MongoDB connection successful")
        client.close()
        
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        return False
    
    try:
        import redis.asyncio as redis
        
        # Test Redis
        redis_client = redis.from_url(settings.get_redis_url())
        await redis_client.ping()
        print("   ✓ Redis connection successful")
        await redis_client.close()
        
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        return False
    
    return True


def main():
    """Main validation function."""
    # Setup logging
    setup_logging()
    
    # Run validation
    validator = ConfigValidator()
    report = validator.validate_all()
    
    # Test database connectivity if basic config is valid
    if not report["errors"]:
        try:
            asyncio.run(test_database_connectivity())
        except Exception as e:
            print(f"   ❌ Database connectivity test failed: {e}")
    
    # Exit with appropriate code
    if report["errors"]:
        print(f"\n❌ Validation failed with {len(report['errors'])} errors.")
        sys.exit(1)
    elif report["warnings"]:
        print(f"\n⚠️  Validation completed with {len(report['warnings'])} warnings.")
        sys.exit(0)
    else:
        print("\n✅ All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()