"""
Environment configuration loader with support for multiple environments and secret backends.

Features:
- Multi-environment support (development, staging, production)
- File-based secret loading
- Environment variable override
- Configuration validation
- Hot reloading support
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConfigSource:
    """Configuration source metadata."""
    name: str
    path: Optional[str] = None
    priority: int = 0
    loaded: bool = False
    error: Optional[str] = None


class EnvironmentLoader:
    """
    Environment configuration loader with multiple source support.
    
    Load order (highest to lowest priority):
    1. Environment variables
    2. .env.local (local overrides)
    3. .env.{environment} (environment-specific)
    4. .env (default)
    5. Default values
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else self._find_project_root()
        self.environment = self._detect_environment()
        self.config_sources: List[ConfigSource] = []
        self.loaded_config: Dict[str, Any] = {}
        
        # Initialize configuration sources
        self._initialize_sources()
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).parent
        
        # Look for project markers
        markers = [".git", "pyproject.toml", "requirements.txt", ".env"]
        
        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        # Fallback to current directory
        return Path.cwd()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment."""
        env_name = os.getenv("INFRA_MIND_ENVIRONMENT", "development").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _initialize_sources(self):
        """Initialize configuration sources in priority order."""
        # Environment variables (highest priority)
        self.config_sources.append(ConfigSource(
            name="environment_variables",
            priority=100
        ))
        
        # Local overrides
        local_env = self.project_root / ".env.local"
        if local_env.exists():
            self.config_sources.append(ConfigSource(
                name="local_overrides",
                path=str(local_env),
                priority=90
            ))
        
        # Environment-specific configuration
        env_file = self.project_root / f".env.{self.environment.value}"
        if env_file.exists():
            self.config_sources.append(ConfigSource(
                name=f"environment_{self.environment.value}",
                path=str(env_file),
                priority=80
            ))
        
        # Default environment file
        default_env = self.project_root / ".env"
        if default_env.exists():
            self.config_sources.append(ConfigSource(
                name="default_env",
                path=str(default_env),
                priority=70
            ))
        
        # Sort by priority (highest first)
        self.config_sources.sort(key=lambda x: x.priority, reverse=True)
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        logger.info(f"Loading configuration for environment: {self.environment.value}")
        
        config = {}
        
        # Load from each source in priority order
        for source in reversed(self.config_sources):  # Reverse for lower priority first
            try:
                source_config = self._load_source(source)
                if source_config:  # Only update if we got config
                    config.update(source_config)
                    source.loaded = True
                    logger.debug(f"Loaded {len(source_config)} config items from {source.name}")
                else:
                    logger.debug(f"No configuration found in {source.name}")
            except Exception as e:
                source.error = str(e)
                logger.error(f"Failed to load configuration from {source.name}: {e}")
        
        self.loaded_config = config
        logger.info(f"Loaded total of {len(config)} configuration items")
        return config
    
    def _load_source(self, source: ConfigSource) -> Dict[str, Any]:
        """Load configuration from a specific source."""
        if source.name == "environment_variables":
            return self._load_environment_variables()
        elif source.path:
            return self._load_env_file(source.path)
        else:
            return {}
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        prefix = "INFRA_MIND_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = self._parse_env_value(value)
        
        return config
    
    def _load_env_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from .env file."""
        config = {}
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Convert to config key format
                        if key.startswith("INFRA_MIND_"):
                            config_key = key[len("INFRA_MIND_"):].lower()
                            config[config_key] = self._parse_env_value(value)
                    else:
                        logger.warning(f"Invalid line in {file_path}:{line_num}: {line}")
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            raise
        
        return config
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle JSON values
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.loaded_config.get(key, default)
    
    def get_secret_file_path(self, secret_name: str) -> Optional[str]:
        """Get path to secret file if it exists."""
        # Check for file-based secrets (Docker/Kubernetes style)
        file_key = f"{secret_name}_file"
        file_path = self.get_config_value(file_key)
        
        if file_path and os.path.exists(file_path):
            return file_path
        
        # Check default secret locations
        secret_dirs = [
            "/run/secrets",  # Docker secrets
            "/var/secrets",  # Custom secrets
            self.project_root / "secrets"  # Local secrets
        ]
        
        for secret_dir in secret_dirs:
            secret_file = Path(secret_dir) / secret_name
            if secret_file.exists():
                return str(secret_file)
        
        return None
    
    def load_secret_from_file(self, secret_name: str) -> Optional[str]:
        """Load secret value from file."""
        file_path = self.get_secret_file_path(secret_name)
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error reading secret file {file_path}: {e}")
        
        return None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration loading status."""
        return {
            "environment": self.environment.value,
            "project_root": str(self.project_root),
            "sources": [
                {
                    "name": source.name,
                    "path": source.path,
                    "priority": source.priority,
                    "loaded": source.loaded,
                    "error": source.error
                }
                for source in self.config_sources
            ],
            "loaded_keys": list(self.loaded_config.keys()),
            "total_config_items": len(self.loaded_config)
        }
    
    def validate_required_config(self, required_keys: List[str]) -> Dict[str, Any]:
        """Validate that required configuration keys are present."""
        missing_keys = []
        present_keys = []
        
        for key in required_keys:
            value = self.get_config_value(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_keys.append(key)
            else:
                present_keys.append(key)
        
        return {
            "valid": len(missing_keys) == 0,
            "missing_keys": missing_keys,
            "present_keys": present_keys,
            "total_required": len(required_keys),
            "total_present": len(present_keys)
        }
    
    def reload_configuration(self) -> Dict[str, Any]:
        """Reload configuration from all sources."""
        logger.info("Reloading configuration...")
        
        # Reset loaded status
        for source in self.config_sources:
            source.loaded = False
            source.error = None
        
        # Reload configuration
        return self.load_configuration()
    
    def export_configuration(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export current configuration (optionally including secrets)."""
        config = self.loaded_config.copy()
        
        if not include_secrets:
            # Remove sensitive keys
            sensitive_patterns = [
                'password', 'secret', 'key', 'token', 'credential',
                'api_key', 'private', 'auth'
            ]
            
            filtered_config = {}
            for key, value in config.items():
                is_sensitive = any(pattern in key.lower() for pattern in sensitive_patterns)
                if is_sensitive:
                    filtered_config[key] = "***REDACTED***"
                else:
                    filtered_config[key] = value
            
            config = filtered_config
        
        return {
            "environment": self.environment.value,
            "configuration": config,
            "metadata": self.get_configuration_status()
        }


# Global environment loader instance
env_loader = EnvironmentLoader()


def load_environment_config() -> Dict[str, Any]:
    """Load environment configuration."""
    return env_loader.load_configuration()


def get_environment() -> Environment:
    """Get current environment."""
    return env_loader.environment


def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return env_loader.get_config_value(key, default)


def validate_production_environment() -> Dict[str, Any]:
    """Validate production environment configuration."""
    if env_loader.environment != Environment.PRODUCTION:
        return {"valid": True, "message": "Not in production environment"}
    
    required_keys = [
        "secret_key",
        "mongodb_url",
        "redis_url",
        "openai_api_key"
    ]
    
    return env_loader.validate_required_config(required_keys)