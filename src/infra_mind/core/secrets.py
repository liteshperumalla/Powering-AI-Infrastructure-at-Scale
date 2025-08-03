"""
Production-ready secrets management system for Infra Mind.

Features:
- Multiple secret backends (environment, vault, cloud providers)
- Secret validation and rotation
- Secure secret handling
- Audit logging for secret access
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Supported secret backends."""
    ENVIRONMENT = "environment"
    FILE = "file"
    VAULT = "vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    AZURE_KEY_VAULT = "azure_key_vault"
    GCP_SECRET_MANAGER = "gcp_secret_manager"


@dataclass
class SecretMetadata:
    """Metadata for a secret."""
    name: str
    backend: SecretBackend
    created_at: Optional[str] = None
    last_accessed: Optional[str] = None
    rotation_required: bool = False
    expires_at: Optional[str] = None


class SecretBackendInterface(ABC):
    """Interface for secret backends."""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value."""
        pass
    
    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret value."""
        pass
    
    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete secret."""
        pass
    
    @abstractmethod
    def list_secrets(self) -> List[str]:
        """List available secrets."""
        pass


class EnvironmentSecretBackend(SecretBackendInterface):
    """Environment variable secret backend."""
    
    def __init__(self, prefix: str = "INFRA_MIND_"):
        self.prefix = prefix
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variables."""
        env_key = f"{self.prefix}{key.upper()}"
        value = os.getenv(env_key)
        
        if value:
            logger.debug(f"Retrieved secret: {key}")
        
        return value
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set environment variable (not persistent)."""
        env_key = f"{self.prefix}{key.upper()}"
        os.environ[env_key] = value
        logger.info(f"Set environment secret: {key}")
        return True
    
    def delete_secret(self, key: str) -> bool:
        """Delete environment variable."""
        env_key = f"{self.prefix}{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            logger.info(f"Deleted environment secret: {key}")
            return True
        return False
    
    def list_secrets(self) -> List[str]:
        """List environment variables with prefix."""
        return [
            key[len(self.prefix):].lower()
            for key in os.environ.keys()
            if key.startswith(self.prefix)
        ]


class FileSecretBackend(SecretBackendInterface):
    """File-based secret backend for development."""
    
    def __init__(self, secrets_dir: Optional[str] = None):
        if secrets_dir is None:
            # Use a development-friendly default
            secrets_dir = os.path.expanduser("~/.infra-mind/secrets")
        
        self.secrets_dir = Path(secrets_dir)
        
        try:
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot create secrets directory {secrets_dir}: {e}")
            # Fallback to temp directory
            import tempfile
            self.secrets_dir = Path(tempfile.gettempdir()) / "infra-mind-secrets"
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from file."""
        secret_file = self.secrets_dir / f"{key}.secret"
        
        if secret_file.exists():
            try:
                with open(secret_file, 'r') as f:
                    value = f.read().strip()
                logger.debug(f"Retrieved file secret: {key}")
                return value
            except Exception as e:
                logger.error(f"Error reading secret file {key}: {e}")
        
        return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret to file."""
        secret_file = self.secrets_dir / f"{key}.secret"
        
        try:
            with open(secret_file, 'w') as f:
                f.write(value)
            
            # Set restrictive permissions
            os.chmod(secret_file, 0o600)
            logger.info(f"Set file secret: {key}")
            return True
        except Exception as e:
            logger.error(f"Error writing secret file {key}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret file."""
        secret_file = self.secrets_dir / f"{key}.secret"
        
        if secret_file.exists():
            try:
                secret_file.unlink()
                logger.info(f"Deleted file secret: {key}")
                return True
            except Exception as e:
                logger.error(f"Error deleting secret file {key}: {e}")
        
        return False
    
    def list_secrets(self) -> List[str]:
        """List secret files."""
        return [
            f.stem for f in self.secrets_dir.glob("*.secret")
        ]


class SecretsManager:
    """
    Production-ready secrets manager with multiple backends.
    
    Features:
    - Multiple backend support
    - Secret validation
    - Audit logging
    - Rotation tracking
    """
    
    def __init__(self, primary_backend: SecretBackend = SecretBackend.ENVIRONMENT):
        self.backends: Dict[SecretBackend, SecretBackendInterface] = {}
        self.primary_backend = primary_backend
        self.secret_metadata: Dict[str, SecretMetadata] = {}
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize available secret backends."""
        # Always available: Environment backend
        self.backends[SecretBackend.ENVIRONMENT] = EnvironmentSecretBackend()
        
        # File backend for development
        if os.getenv("INFRA_MIND_ENVIRONMENT", "development") == "development":
            try:
                self.backends[SecretBackend.FILE] = FileSecretBackend()
            except Exception as e:
                logger.warning(f"Could not initialize file backend: {e}")
        
        # TODO: Add cloud provider backends
        # self._initialize_aws_secrets_manager()
        # self._initialize_azure_key_vault()
        # self._initialize_gcp_secret_manager()
        # self._initialize_vault()
    
    def get_secret(self, key: str, backend: Optional[SecretBackend] = None) -> Optional[str]:
        """
        Get secret value from specified or primary backend.
        
        Args:
            key: Secret key name
            backend: Specific backend to use (optional)
        
        Returns:
            Secret value or None if not found
        """
        target_backend = backend or self.primary_backend
        
        if target_backend not in self.backends:
            logger.error(f"Backend {target_backend} not available")
            return None
        
        try:
            value = self.backends[target_backend].get_secret(key)
            
            if value:
                # Update metadata
                if key in self.secret_metadata:
                    self.secret_metadata[key].last_accessed = self._get_timestamp()
                
                # Audit log (without value)
                logger.info(f"Secret accessed: {key} from {target_backend.value}")
            
            return value
        
        except Exception as e:
            logger.error(f"Error retrieving secret {key} from {target_backend}: {e}")
            return None
    
    def set_secret(self, key: str, value: str, backend: Optional[SecretBackend] = None) -> bool:
        """
        Set secret value in specified or primary backend.
        
        Args:
            key: Secret key name
            value: Secret value
            backend: Specific backend to use (optional)
        
        Returns:
            True if successful, False otherwise
        """
        target_backend = backend or self.primary_backend
        
        if target_backend not in self.backends:
            logger.error(f"Backend {target_backend} not available")
            return False
        
        try:
            success = self.backends[target_backend].set_secret(key, value)
            
            if success:
                # Update metadata
                self.secret_metadata[key] = SecretMetadata(
                    name=key,
                    backend=target_backend,
                    created_at=self._get_timestamp()
                )
                
                # Audit log (without value)
                logger.info(f"Secret set: {key} in {target_backend.value}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error setting secret {key} in {target_backend}: {e}")
            return False
    
    def delete_secret(self, key: str, backend: Optional[SecretBackend] = None) -> bool:
        """Delete secret from specified or primary backend."""
        target_backend = backend or self.primary_backend
        
        if target_backend not in self.backends:
            logger.error(f"Backend {target_backend} not available")
            return False
        
        try:
            success = self.backends[target_backend].delete_secret(key)
            
            if success:
                # Remove metadata
                if key in self.secret_metadata:
                    del self.secret_metadata[key]
                
                # Audit log
                logger.info(f"Secret deleted: {key} from {target_backend.value}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting secret {key} from {target_backend}: {e}")
            return False
    
    def validate_secrets(self, required_secrets: List[str]) -> Dict[str, bool]:
        """
        Validate that required secrets are available.
        
        Args:
            required_secrets: List of required secret keys
        
        Returns:
            Dictionary mapping secret names to availability status
        """
        validation_results = {}
        
        for secret_key in required_secrets:
            value = self.get_secret(secret_key)
            validation_results[secret_key] = bool(value and value.strip())
        
        return validation_results
    
    def get_secret_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret."""
        return self.secret_metadata.get(key)
    
    def list_secrets(self, backend: Optional[SecretBackend] = None) -> List[str]:
        """List available secrets in specified or primary backend."""
        target_backend = backend or self.primary_backend
        
        if target_backend not in self.backends:
            logger.error(f"Backend {target_backend} not available")
            return []
        
        try:
            return self.backends[target_backend].list_secrets()
        except Exception as e:
            logger.error(f"Error listing secrets from {target_backend}: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """
        Rotate a secret value.
        
        Args:
            key: Secret key name
            new_value: New secret value
        
        Returns:
            True if successful, False otherwise
        """
        # Set new value
        success = self.set_secret(key, new_value)
        
        if success:
            # Update metadata
            if key in self.secret_metadata:
                self.secret_metadata[key].rotation_required = False
                self.secret_metadata[key].created_at = self._get_timestamp()
            
            logger.info(f"Secret rotated: {key}")
        
        return success
    
    def check_rotation_required(self) -> List[str]:
        """Check which secrets require rotation."""
        return [
            key for key, metadata in self.secret_metadata.items()
            if metadata.rotation_required
        ]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on secret backends."""
        health_status = {
            "healthy": True,
            "backends": {},
            "errors": []
        }
        
        for backend_type, backend in self.backends.items():
            try:
                # Test backend by listing secrets
                secrets = backend.list_secrets()
                health_status["backends"][backend_type.value] = {
                    "healthy": True,
                    "secret_count": len(secrets)
                }
            except Exception as e:
                health_status["healthy"] = False
                health_status["backends"][backend_type.value] = {
                    "healthy": False,
                    "error": str(e)
                }
                health_status["errors"].append(f"{backend_type.value}: {e}")
        
        return health_status


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_required_secrets() -> List[str]:
    """Get list of required secrets for production deployment."""
    return [
        "secret_key",
        "mongodb_url",
        "redis_url",
        "openai_api_key",
        "aws_access_key_id",
        "aws_secret_access_key",
        "azure_client_id",
        "azure_client_secret",
        "azure_tenant_id",
        "gcp_project_id"
    ]


def validate_production_secrets() -> Dict[str, Any]:
    """Validate all production secrets."""
    required_secrets = get_required_secrets()
    validation_results = secrets_manager.validate_secrets(required_secrets)
    
    missing_secrets = [
        key for key, is_valid in validation_results.items()
        if not is_valid
    ]
    
    return {
        "valid": len(missing_secrets) == 0,
        "missing_secrets": missing_secrets,
        "validation_results": validation_results,
        "total_secrets": len(required_secrets),
        "valid_secrets": len(required_secrets) - len(missing_secrets)
    }


def setup_development_secrets():
    """Setup development secrets for testing."""
    development_secrets = {
        "secret_key": "development-secret-key-not-for-production-use-only",
        "mongodb_url": "mongodb://localhost:27017",
        "redis_url": "redis://localhost:6379",
        "openai_api_key": "sk-development-key-replace-with-real-key"
    }
    
    for key, value in development_secrets.items():
        if not secrets_manager.get_secret(key):
            secrets_manager.set_secret(key, value)
            logger.info(f"Set development secret: {key}")