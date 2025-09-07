"""
Integration registry for managing third-party service configurations.

This module provides centralized management of all integration configurations
and provides factory methods for creating integration instances.
"""

import logging
from typing import Dict, Any, List, Optional, Type, Union
from dataclasses import dataclass, field
import json
from pathlib import Path

from .base import BaseIntegration, IntegrationConfig, IntegrationType

logger = logging.getLogger(__name__)


@dataclass
class IntegrationTemplate:
    """Template for creating integration configurations."""
    name: str
    type: IntegrationType
    display_name: str
    description: str
    required_config: List[str]
    optional_config: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    documentation_url: Optional[str] = None
    integration_class: Optional[str] = None


class IntegrationRegistry:
    """
    Registry for managing integration templates and configurations.
    
    Provides centralized configuration management, validation,
    and factory methods for creating integrations.
    """
    
    def __init__(self):
        """Initialize the integration registry."""
        self.templates: Dict[str, IntegrationTemplate] = {}
        self.integration_classes: Dict[str, Type[BaseIntegration]] = {}
        self.configurations: Dict[str, IntegrationConfig] = {}
        
        # Initialize with built-in templates
        self._register_builtin_templates()
        
        logger.info("Integration registry initialized")
    
    def _register_builtin_templates(self) -> None:
        """Register built-in integration templates."""
        
        # Slack Integration
        self.register_template(IntegrationTemplate(
            name="slack",
            type=IntegrationType.NOTIFICATION,
            display_name="Slack",
            description="Send notifications and messages to Slack channels",
            required_config=["webhook_url"],
            optional_config=["channel", "username", "icon_emoji"],
            default_values={
                "channel": "#general",
                "username": "InfraMind Bot",
                "icon_emoji": ":robot_face:"
            },
            documentation_url="https://api.slack.com/messaging/webhooks"
        ))
        
        # Microsoft Teams Integration
        self.register_template(IntegrationTemplate(
            name="teams",
            type=IntegrationType.NOTIFICATION,
            display_name="Microsoft Teams",
            description="Send notifications to Microsoft Teams channels",
            required_config=["webhook_url"],
            optional_config=["theme_color"],
            default_values={
                "theme_color": "0076D7"
            },
            documentation_url="https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/"
        ))
        
        # DataDog Integration
        self.register_template(IntegrationTemplate(
            name="datadog",
            type=IntegrationType.MONITORING,
            display_name="DataDog",
            description="Send metrics and events to DataDog",
            required_config=["api_key", "app_key"],
            optional_config=["host", "tags", "service"],
            default_values={
                "host": "api.datadoghq.com",
                "service": "infra-mind"
            },
            documentation_url="https://docs.datadoghq.com/api/"
        ))
        
        # New Relic Integration
        self.register_template(IntegrationTemplate(
            name="newrelic",
            type=IntegrationType.MONITORING,
            display_name="New Relic",
            description="Send custom events and metrics to New Relic",
            required_config=["api_key", "account_id"],
            optional_config=["region", "app_name"],
            default_values={
                "region": "US",
                "app_name": "InfraMind"
            },
            documentation_url="https://docs.newrelic.com/docs/apis/"
        ))
        
        # PagerDuty Integration
        self.register_template(IntegrationTemplate(
            name="pagerduty",
            type=IntegrationType.NOTIFICATION,
            display_name="PagerDuty",
            description="Create incidents and alerts in PagerDuty",
            required_config=["integration_key"],
            optional_config=["severity", "component", "group"],
            default_values={
                "severity": "warning"
            },
            documentation_url="https://developer.pagerduty.com/api-reference/"
        ))
        
        # Jira Integration
        self.register_template(IntegrationTemplate(
            name="jira",
            type=IntegrationType.API,
            display_name="Atlassian Jira",
            description="Create tickets and track issues in Jira",
            required_config=["base_url", "username", "api_token"],
            optional_config=["project_key", "issue_type"],
            default_values={
                "issue_type": "Task"
            },
            documentation_url="https://developer.atlassian.com/cloud/jira/platform/rest/v3/"
        ))
        
        # GitHub Integration
        self.register_template(IntegrationTemplate(
            name="github",
            type=IntegrationType.API,
            display_name="GitHub",
            description="Interact with GitHub repositories and issues",
            required_config=["api_token"],
            optional_config=["base_url", "organization", "repository"],
            default_values={
                "base_url": "https://api.github.com"
            },
            documentation_url="https://docs.github.com/en/rest"
        ))
        
        # AWS CloudWatch Integration
        self.register_template(IntegrationTemplate(
            name="cloudwatch",
            type=IntegrationType.MONITORING,
            display_name="AWS CloudWatch",
            description="Send custom metrics to AWS CloudWatch",
            required_config=["aws_access_key", "aws_secret_key", "region"],
            optional_config=["namespace", "dimensions"],
            default_values={
                "namespace": "InfraMind/Assessments",
                "region": "us-east-1"
            },
            documentation_url="https://docs.aws.amazon.com/cloudwatch/"
        ))
        
        # Elasticsearch Integration
        self.register_template(IntegrationTemplate(
            name="elasticsearch",
            type=IntegrationType.DATABASE,
            display_name="Elasticsearch",
            description="Index documents and search data in Elasticsearch",
            required_config=["host", "port"],
            optional_config=["username", "password", "use_ssl", "index_prefix"],
            default_values={
                "port": 9200,
                "use_ssl": False,
                "index_prefix": "infra-mind"
            },
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/"
        ))
        
        # Webhook Integration
        self.register_template(IntegrationTemplate(
            name="webhook",
            type=IntegrationType.WEBHOOK,
            display_name="Generic Webhook",
            description="Send HTTP requests to custom webhook endpoints",
            required_config=["url"],
            optional_config=["method", "headers", "timeout", "auth_type", "auth_token"],
            default_values={
                "method": "POST",
                "timeout": 30
            },
            documentation_url="https://en.wikipedia.org/wiki/Webhook"
        ))
    
    def register_template(self, template: IntegrationTemplate) -> None:
        """
        Register an integration template.
        
        Args:
            template: Integration template to register
        """
        self.templates[template.name] = template
        logger.info(f"Registered integration template: {template.name}")
    
    def register_integration_class(self, name: str, integration_class: Type[BaseIntegration]) -> None:
        """
        Register an integration class.
        
        Args:
            name: Integration name
            integration_class: Integration class
        """
        self.integration_classes[name] = integration_class
        logger.info(f"Registered integration class: {name}")
    
    def get_template(self, name: str) -> Optional[IntegrationTemplate]:
        """
        Get integration template by name.
        
        Args:
            name: Template name
            
        Returns:
            Integration template or None if not found
        """
        return self.templates.get(name)
    
    def list_templates(self) -> List[IntegrationTemplate]:
        """List all available integration templates."""
        return list(self.templates.values())
    
    def get_templates_by_type(self, integration_type: IntegrationType) -> List[IntegrationTemplate]:
        """
        Get templates by integration type.
        
        Args:
            integration_type: Type of integration
            
        Returns:
            List of matching templates
        """
        return [
            template for template in self.templates.values()
            if template.type == integration_type
        ]
    
    def create_configuration(
        self,
        template_name: str,
        config_data: Dict[str, Any],
        name: Optional[str] = None
    ) -> IntegrationConfig:
        """
        Create integration configuration from template.
        
        Args:
            template_name: Name of template to use
            config_data: Configuration data
            name: Optional custom name for the configuration
            
        Returns:
            Integration configuration
            
        Raises:
            ValueError: If template not found or required config missing
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate required configuration
        missing_required = [
            key for key in template.required_config
            if key not in config_data
        ]
        if missing_required:
            raise ValueError(f"Missing required configuration: {missing_required}")
        
        # Merge with default values
        merged_config = template.default_values.copy()
        merged_config.update(config_data)
        
        # Create configuration
        config_name = name or f"{template_name}_{len(self.configurations)}"
        
        config = IntegrationConfig(
            name=config_name,
            type=template.type,
            **merged_config
        )
        
        # Store configuration
        self.configurations[config_name] = config
        
        logger.info(f"Created integration configuration: {config_name}")
        return config
    
    def validate_configuration(self, template_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration data against template.
        
        Args:
            template_name: Name of template
            config_data: Configuration data to validate
            
        Returns:
            Dict with validation results
        """
        template = self.get_template(template_name)
        if not template:
            return {
                "valid": False,
                "errors": [f"Template '{template_name}' not found"]
            }
        
        errors = []
        warnings = []
        
        # Check required fields
        missing_required = [
            key for key in template.required_config
            if key not in config_data
        ]
        if missing_required:
            errors.append(f"Missing required fields: {missing_required}")
        
        # Check for unknown fields
        all_known_fields = set(template.required_config + template.optional_config)
        unknown_fields = [
            key for key in config_data.keys()
            if key not in all_known_fields
        ]
        if unknown_fields:
            warnings.append(f"Unknown fields (will be ignored): {unknown_fields}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def create_integration(self, config_name: str) -> Optional[BaseIntegration]:
        """
        Create integration instance from stored configuration.
        
        Args:
            config_name: Name of stored configuration
            
        Returns:
            Integration instance or None if not possible
        """
        config = self.configurations.get(config_name)
        if not config:
            logger.error(f"Configuration '{config_name}' not found")
            return None
        
        # Try to find integration class
        integration_class = self.integration_classes.get(config_name)
        if not integration_class:
            # Try to find by type
            type_name = config.type.value
            integration_class = self.integration_classes.get(type_name)
        
        if not integration_class:
            logger.error(f"No integration class found for '{config_name}'")
            return None
        
        try:
            return integration_class(config)
        except Exception as e:
            logger.error(f"Failed to create integration '{config_name}': {e}")
            return None
    
    def save_configurations(self, filepath: str) -> None:
        """
        Save configurations to file.
        
        Args:
            filepath: Path to save configurations
        """
        try:
            config_data = {
                name: config.to_dict()
                for name, config in self.configurations.items()
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.configurations)} configurations to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save configurations: {e}")
    
    def load_configurations(self, filepath: str) -> int:
        """
        Load configurations from file.
        
        Args:
            filepath: Path to load configurations from
            
        Returns:
            Number of configurations loaded
        """
        try:
            if not Path(filepath).exists():
                logger.warning(f"Configuration file not found: {filepath}")
                return 0
            
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            loaded_count = 0
            for name, data in config_data.items():
                try:
                    # Convert type string back to enum
                    data['type'] = IntegrationType(data['type'])
                    
                    config = IntegrationConfig(**data)
                    self.configurations[name] = config
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to load configuration '{name}': {e}")
            
            logger.info(f"Loaded {loaded_count} configurations from {filepath}")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            return 0
    
    def get_configuration(self, name: str) -> Optional[IntegrationConfig]:
        """Get stored configuration by name."""
        return self.configurations.get(name)
    
    def list_configurations(self) -> List[str]:
        """List all stored configuration names."""
        return list(self.configurations.keys())
    
    def delete_configuration(self, name: str) -> bool:
        """
        Delete stored configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            True if deleted, False if not found
        """
        if name in self.configurations:
            del self.configurations[name]
            logger.info(f"Deleted configuration: {name}")
            return True
        return False


# Global registry instance
integration_registry = IntegrationRegistry()