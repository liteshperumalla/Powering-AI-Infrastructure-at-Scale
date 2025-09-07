"""
Production Terraform API integration for Infra Mind.

Provides real clients for Terraform Cloud API and Terraform Registry API
with production-ready authentication, error handling, and workspace management.

This implementation replaces all mock Terraform clients with real API integrations:
- Terraform Cloud API for cost estimation and workspace management
- Terraform Registry API for provider and module information
- Production-ready authentication and error handling
- Real workspace operations and plan execution
"""

import asyncio
import json
import logging
import os
import time
import hashlib
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import httpx
from urllib.parse import urljoin
import tarfile
import tempfile
from pathlib import Path

from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, RateLimitError, AuthenticationError
)

logger = logging.getLogger(__name__)


class TerraformProvider(str):
    """Terraform provider enum-like class."""
    TERRAFORM_CLOUD = "terraform_cloud"
    TERRAFORM_REGISTRY = "terraform_registry"


class TerraformClient(BaseCloudClient):
    """
    Production Terraform client that coordinates Terraform Cloud and Registry APIs.
    
    This client provides unified access to:
    - Terraform Cloud API for cost estimation and workspace management
    - Terraform Registry API for provider and module information
    - Real authentication and error handling
    - Production-ready workspace operations
    """
    
    def __init__(self, terraform_token: Optional[str] = None, organization: Optional[str] = None):
        """
        Initialize production Terraform client.
        
        Args:
            terraform_token: Terraform Cloud API token (from env or parameter)
            organization: Terraform Cloud organization name (from env or parameter)
            
        Raises:
            AuthenticationError: If required credentials are missing for Terraform Cloud operations
        """
        super().__init__(CloudProvider.AWS, "global")  # Using AWS as base, region is global for Terraform
        
        # Get credentials from environment if not provided
        self.terraform_token = terraform_token or os.getenv('INFRA_MIND_TERRAFORM_TOKEN')
        self.organization = organization or os.getenv('INFRA_MIND_TERRAFORM_ORG')
        
        # Initialize service clients with real authentication
        self.cloud_client = TerraformCloudClient(self.terraform_token, self.organization)
        self.registry_client = TerraformRegistryClient()
        
        # Track API usage for cost optimization
        self.api_calls_count = 0
        self.last_api_call = None
    
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Terraform compute-related modules and providers."""
        return await self._get_cached_or_fetch(
            service="compute_modules",
            region="global",
            fetch_func=lambda: self.registry_client.get_compute_modules(),
            cache_ttl=3600  # 1 hour cache for modules
        )
    
    async def get_storage_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Terraform storage-related modules and providers."""
        return await self._get_cached_or_fetch(
            service="storage_modules",
            region="global",
            fetch_func=lambda: self.registry_client.get_storage_modules(),
            cache_ttl=3600  # 1 hour cache for modules
        )
    
    async def get_database_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Terraform database-related modules and providers."""
        return await self._get_cached_or_fetch(
            service="database_modules",
            region="global",
            fetch_func=lambda: self.registry_client.get_database_modules(),
            cache_ttl=3600  # 1 hour cache for modules
        )
    
    async def get_ai_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get Terraform AI/ML-related modules and providers."""
        return await self._get_cached_or_fetch(
            service="ai_modules",
            region="global",
            fetch_func=lambda: self.registry_client.get_ai_modules(),
            cache_ttl=3600  # 1 hour cache for modules
        )
    
    async def get_service_pricing(self, service_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get cost estimation for Terraform configuration."""
        if not self.terraform_token:
            raise AuthenticationError(
                "Terraform Cloud API token required for cost estimation",
                CloudProvider.AWS,  # Using AWS as base provider
                "MISSING_TOKEN"
            )
        
        return await self._get_cached_or_fetch(
            service="cost_estimation",
            region="global",
            fetch_func=lambda: self.cloud_client.get_cost_estimation(service_id),
            params={"service_id": service_id},
            cache_ttl=1800  # 30 minutes cache for cost estimates
        )
    
    async def get_providers(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get Terraform providers from registry."""
        return await self._get_cached_or_fetch(
            service="providers",
            region="global",
            fetch_func=lambda: self.registry_client.get_providers(namespace),
            params={"namespace": namespace},
            cache_ttl=3600  # 1 hour cache for providers
        )
    
    async def get_modules(self, namespace: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get Terraform modules from registry."""
        return await self._get_cached_or_fetch(
            service="modules",
            region="global",
            fetch_func=lambda: self.registry_client.get_modules(namespace, provider),
            params={"namespace": namespace, "provider": provider},
            cache_ttl=3600  # 1 hour cache for modules
        )
    
    async def create_workspace(self, workspace_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Terraform Cloud workspace."""
        if not self.terraform_token:
            raise AuthenticationError(
                "Terraform Cloud API token required for workspace operations",
                CloudProvider.AWS,
                "MISSING_TOKEN"
            )
        
        return await self.cloud_client.create_workspace(workspace_config)
    
    async def run_plan(self, workspace_id: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Run a Terraform plan with cost estimation."""
        if not self.terraform_token:
            raise AuthenticationError(
                "Terraform Cloud API token required for plan operations",
                CloudProvider.AWS,
                "MISSING_TOKEN"
            )
        
        return await self.cloud_client.run_plan(workspace_id, configuration)


class TerraformCloudClient:
    """
    Production Terraform Cloud API client for cost estimation and workspace management.
    
    This client provides:
    - Real authentication with Terraform Cloud
    - Workspace creation and management
    - Cost estimation for infrastructure changes
    - Plan execution and monitoring
    - Proper error handling and rate limiting
    """
    
    def __init__(self, terraform_token: Optional[str] = None, organization: Optional[str] = None):
        """
        Initialize production Terraform Cloud client.
        
        Args:
            terraform_token: Terraform Cloud API token
            organization: Terraform Cloud organization name
            
        Raises:
            AuthenticationError: If token is invalid or missing for authenticated operations
        """
        self.terraform_token = terraform_token
        self.organization = organization
        self.base_url = "https://app.terraform.io/api/v2"
        self.session = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
        # Only show token format message if we'll be using Terraform Cloud operations
        if self.terraform_token and self.organization and not self.terraform_token.startswith(('at-', 'user-')):
            logger.debug("Terraform token format: expected 'at-' (team token) or 'user-' (user token) for Terraform Cloud operations.")
        
        # Validate organization name
        if self.organization and not self.organization.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Invalid organization name format")
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session with authentication."""
        if not self.session:
            headers = {
                "Content-Type": "application/vnd.api+json",
                "User-Agent": "InfraMind/1.0"
            }
            
            if self.terraform_token:
                headers["Authorization"] = f"Bearer {self.terraform_token}"
            
            self.session = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        
        return self.session
    
    async def get_cost_estimation(self, run_id: str) -> Dict[str, Any]:
        """
        Get cost estimation for a Terraform run.
        
        Args:
            run_id: Terraform Cloud run ID
            
        Returns:
            Cost estimation data
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            session = await self._get_session()
            
            # Get cost estimation for the run
            url = f"{self.base_url}/runs/{run_id}/cost-estimate"
            response = await session.get(url)
            
            if response.status_code == 404:
                # Cost estimation might not be available for this run
                return {
                    "cost_estimate": None,
                    "message": "Cost estimation not available for this run",
                    "run_id": run_id
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Process cost estimation data
            cost_estimate = data.get("data", {})
            attributes = cost_estimate.get("attributes", {})
            
            return {
                "run_id": run_id,
                "status": attributes.get("status"),
                "monthly_cost": attributes.get("monthly-cost"),
                "prior_monthly_cost": attributes.get("prior-monthly-cost"),
                "delta_monthly_cost": attributes.get("delta-monthly-cost"),
                "currency": attributes.get("currency", "USD"),
                "resources": attributes.get("resources", []),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Terraform Cloud API token",
                    CloudProvider.AWS,
                    "INVALID_TOKEN"
                )
            elif e.response.status_code == 429:
                raise RateLimitError(
                    "Terraform Cloud API rate limit exceeded",
                    CloudProvider.AWS,
                    "RATE_LIMIT_EXCEEDED"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Cloud API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting cost estimation: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def create_workspace(self, workspace_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Terraform Cloud workspace.
        
        Args:
            workspace_config: Workspace configuration
            
        Returns:
            Created workspace data
        """
        try:
            if not self.organization:
                raise CloudServiceError(
                    "Organization name required for workspace operations",
                    CloudProvider.AWS,
                    "MISSING_ORGANIZATION"
                )
            
            session = await self._get_session()
            
            # Prepare workspace payload
            payload = {
                "data": {
                    "type": "workspaces",
                    "attributes": {
                        "name": workspace_config.get("name"),
                        "description": workspace_config.get("description", ""),
                        "terraform-version": workspace_config.get("terraform_version", "latest"),
                        "working-directory": workspace_config.get("working_directory", ""),
                        "auto-apply": workspace_config.get("auto_apply", False),
                        "queue-all-runs": workspace_config.get("queue_all_runs", False)
                    }
                }
            }
            
            url = f"{self.base_url}/organizations/{self.organization}/workspaces"
            response = await session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            workspace = data.get("data", {})
            attributes = workspace.get("attributes", {})
            
            return {
                "id": workspace.get("id"),
                "name": attributes.get("name"),
                "description": attributes.get("description"),
                "terraform_version": attributes.get("terraform-version"),
                "created_at": attributes.get("created-at"),
                "updated_at": attributes.get("updated-at"),
                "organization": self.organization
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Terraform Cloud API token",
                    CloudProvider.AWS,
                    "INVALID_TOKEN"
                )
            elif e.response.status_code == 422:
                raise CloudServiceError(
                    f"Invalid workspace configuration: {e.response.text}",
                    CloudProvider.AWS,
                    "INVALID_CONFIG"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Cloud API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error creating workspace: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def run_plan(self, workspace_id: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a Terraform plan with cost estimation.
        
        Args:
            workspace_id: Terraform Cloud workspace ID
            configuration: Terraform configuration with optional files
            
        Returns:
            Plan run data with cost estimation
        """
        try:
            session = await self._get_session()
            
            # Create a configuration version first
            config_version_payload = {
                "data": {
                    "type": "configuration-versions",
                    "attributes": {
                        "auto-queue-runs": True,
                        "speculative": configuration.get("speculative", False)
                    }
                }
            }
            
            config_url = f"{self.base_url}/workspaces/{workspace_id}/configuration-versions"
            config_response = await session.post(config_url, json=config_version_payload)
            config_response.raise_for_status()
            
            config_data = config_response.json()
            config_version = config_data.get("data", {})
            upload_url = config_version.get("attributes", {}).get("upload-url")
            
            # Upload configuration if provided
            if upload_url and configuration.get("terraform_files"):
                await self._upload_configuration(upload_url, configuration["terraform_files"])
            elif upload_url:
                # Create a minimal configuration for testing
                await self._upload_minimal_configuration(upload_url)
            
            # Create a run
            run_payload = {
                "data": {
                    "type": "runs",
                    "attributes": {
                        "message": configuration.get("message", "Plan run from InfraMind"),
                        "is-destroy": configuration.get("is_destroy", False),
                        "refresh": configuration.get("refresh", True),
                        "refresh-only": configuration.get("refresh_only", False)
                    },
                    "relationships": {
                        "workspace": {
                            "data": {
                                "type": "workspaces",
                                "id": workspace_id
                            }
                        },
                        "configuration-version": {
                            "data": {
                                "type": "configuration-versions",
                                "id": config_version.get("id")
                            }
                        }
                    }
                }
            }
            
            run_url = f"{self.base_url}/runs"
            run_response = await session.post(run_url, json=run_payload)
            run_response.raise_for_status()
            
            run_data = run_response.json()
            run = run_data.get("data", {})
            run_attributes = run.get("attributes", {})
            
            # Wait for the run to initialize
            await asyncio.sleep(3)
            
            # Get updated run status
            run_status = await self._get_run_status(run.get("id"))
            
            # Try to get cost estimation
            try:
                cost_estimation = await self.get_cost_estimation(run.get("id"))
            except Exception as e:
                logger.warning(f"Could not get cost estimation: {e}")
                cost_estimation = {"cost_estimate": None, "error": str(e)}
            
            return {
                "run_id": run.get("id"),
                "status": run_status.get("status", run_attributes.get("status")),
                "message": run_attributes.get("message"),
                "created_at": run_attributes.get("created-at"),
                "workspace_id": workspace_id,
                "configuration_version_id": config_version.get("id"),
                "cost_estimation": cost_estimation,
                "plan_url": f"https://app.terraform.io/app/{self.organization}/workspaces/{workspace_id}/runs/{run.get('id')}",
                "speculative": configuration.get("speculative", False)
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Terraform Cloud API token",
                    CloudProvider.AWS,
                    "INVALID_TOKEN"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Cloud API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error running plan: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def _upload_configuration(self, upload_url: str, terraform_files: Dict[str, str]) -> None:
        """
        Upload Terraform configuration files to Terraform Cloud.
        
        Args:
            upload_url: Upload URL from configuration version
            terraform_files: Dictionary of filename -> content
        """
        try:
            # Create a tar.gz file with the configuration
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
                with tarfile.open(temp_file.name, 'w:gz') as tar:
                    for filename, content in terraform_files.items():
                        # Create a temporary file for each Terraform file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as tf_file:
                            tf_file.write(content)
                            tf_file.flush()
                            tar.add(tf_file.name, arcname=filename)
                            os.unlink(tf_file.name)
                
                # Upload the tar.gz file
                with open(temp_file.name, 'rb') as upload_file:
                    upload_response = await httpx.AsyncClient().put(
                        upload_url,
                        content=upload_file.read(),
                        headers={'Content-Type': 'application/octet-stream'}
                    )
                    upload_response.raise_for_status()
                
                # Clean up
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"Failed to upload configuration: {e}")
            raise CloudServiceError(
                f"Configuration upload failed: {str(e)}",
                CloudProvider.AWS,
                "UPLOAD_ERROR"
            )
    
    async def _upload_minimal_configuration(self, upload_url: str) -> None:
        """
        Upload a minimal Terraform configuration for testing.
        
        Args:
            upload_url: Upload URL from configuration version
        """
        minimal_config = {
            "main.tf": '''
# Minimal Terraform configuration for InfraMind testing
terraform {
  required_version = ">= 1.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Null resource for testing - no actual infrastructure created
resource "null_resource" "infra_mind_test" {
  triggers = {
    timestamp = timestamp()
  }
}

output "test_output" {
  value = "InfraMind Terraform integration test successful"
}
'''
        }
        
        await self._upload_configuration(upload_url, minimal_config)
    
    async def _get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the current status of a Terraform run.
        
        Args:
            run_id: Terraform Cloud run ID
            
        Returns:
            Run status information
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/runs/{run_id}"
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            run = data.get("data", {})
            attributes = run.get("attributes", {})
            
            return {
                "id": run.get("id"),
                "status": attributes.get("status"),
                "status_timestamps": attributes.get("status-timestamps", {}),
                "has_changes": attributes.get("has-changes"),
                "is_destroy": attributes.get("is-destroy"),
                "message": attributes.get("message"),
                "plan_only": attributes.get("plan-only"),
                "source": attributes.get("source"),
                "terraform_version": attributes.get("terraform-version")
            }
            
        except Exception as e:
            logger.warning(f"Could not get run status: {e}")
            return {"status": "unknown", "error": str(e)}
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspaces in the organization.
        
        Returns:
            List of workspace information
        """
        try:
            if not self.organization:
                raise CloudServiceError(
                    "Organization name required for workspace listing",
                    CloudProvider.AWS,
                    "MISSING_ORGANIZATION"
                )
            
            session = await self._get_session()
            
            url = f"{self.base_url}/organizations/{self.organization}/workspaces"
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            workspaces = []
            
            for workspace in data.get("data", []):
                attributes = workspace.get("attributes", {})
                workspaces.append({
                    "id": workspace.get("id"),
                    "name": attributes.get("name"),
                    "description": attributes.get("description"),
                    "terraform_version": attributes.get("terraform-version"),
                    "working_directory": attributes.get("working-directory"),
                    "auto_apply": attributes.get("auto-apply"),
                    "locked": attributes.get("locked"),
                    "created_at": attributes.get("created-at"),
                    "updated_at": attributes.get("updated-at"),
                    "resource_count": attributes.get("resource-count", 0),
                    "latest_change_at": attributes.get("latest-change-at")
                })
            
            return workspaces
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Terraform Cloud API token",
                    CloudProvider.AWS,
                    "INVALID_TOKEN"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Cloud API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error listing workspaces: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace (for cleanup in development/testing).
        
        Args:
            workspace_id: Terraform Cloud workspace ID
            
        Returns:
            True if deletion was successful
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/workspaces/{workspace_id}"
            response = await session.delete(url)
            response.raise_for_status()
            
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Terraform Cloud API token",
                    CloudProvider.AWS,
                    "INVALID_TOKEN"
                )
            elif e.response.status_code == 404:
                logger.warning(f"Workspace {workspace_id} not found for deletion")
                return True  # Already deleted
            else:
                raise CloudServiceError(
                    f"Terraform Cloud API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error deleting workspace: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None


class TerraformRegistryClient:
    """
    Terraform Registry API client for provider and module information.
    
    Learning Note: The Terraform Registry is a public repository of
    Terraform providers and modules that can be used in configurations.
    """
    
    def __init__(self):
        """Initialize Terraform Registry client."""
        self.base_url = "https://registry.terraform.io/v1"
        self.session = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if not self.session:
            headers = {
                "Accept": "application/json",
                "User-Agent": "InfraMind/1.0"
            }
            
            self.session = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        
        return self.session
    
    async def get_providers(self, namespace: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get Terraform providers from registry.
        
        Args:
            namespace: Provider namespace (e.g., 'hashicorp', 'aws')
            limit: Maximum number of providers to return
            
        Returns:
            Provider information with version details
        """
        try:
            session = await self._get_session()
            
            if namespace:
                url = f"{self.base_url}/providers/{namespace}"
            else:
                url = f"{self.base_url}/providers"
                if limit:
                    url += f"?limit={limit}"
            
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Process provider data - API returns providers directly
            providers = []
            
            # Both namespace and general queries return providers in the same format
            for provider in data.get("providers", []):
                providers.append({
                    "namespace": provider.get("namespace"),
                    "name": provider.get("name"),
                    "full_name": f"{provider.get('namespace')}/{provider.get('name')}",
                    "description": provider.get("description"),
                    "source": provider.get("source"),
                    "downloads": provider.get("downloads", 0),
                    "published_at": provider.get("published_at"),
                    "tier": provider.get("tier", "community"),
                    "featured": provider.get("featured", False),
                    "version": provider.get("version")
                })
            
            return {
                "providers": providers,
                "total_count": len(providers),
                "namespace": namespace,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    "Terraform Registry API rate limit exceeded",
                    CloudProvider.AWS,
                    "RATE_LIMIT_EXCEEDED"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Registry API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting providers: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def _get_provider_details(self, namespace: str, provider_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific provider including versions.
        
        Args:
            namespace: Provider namespace
            provider_name: Provider name
            
        Returns:
            Detailed provider information
        """
        try:
            session = await self._get_session()
            
            # Get provider versions
            versions_url = f"{self.base_url}/providers/{namespace}/{provider_name}/versions"
            versions_response = await session.get(versions_url)
            
            versions = []
            if versions_response.status_code == 200:
                versions_data = versions_response.json()
                for version in versions_data.get("data", []):
                    version_attrs = version.get("attributes", {})
                    versions.append({
                        "version": version_attrs.get("version"),
                        "published_at": version_attrs.get("published-at"),
                        "protocols": version_attrs.get("protocols", []),
                        "platforms": version_attrs.get("shasums-url", "").split("/")[-2:] if version_attrs.get("shasums-url") else []
                    })
            
            # Get basic provider info
            provider_url = f"{self.base_url}/providers/{namespace}/{provider_name}"
            provider_response = await session.get(provider_url)
            provider_response.raise_for_status()
            
            provider_data = provider_response.json()
            attributes = provider_data.get("data", {}).get("attributes", {})
            
            return {
                "namespace": namespace,
                "name": provider_name,
                "full_name": attributes.get("full-name"),
                "description": attributes.get("description"),
                "source": attributes.get("source"),
                "downloads": attributes.get("downloads"),
                "published_at": attributes.get("published-at"),
                "tier": attributes.get("tier", "community"),
                "featured": attributes.get("featured", False),
                "versions": versions[:10],  # Latest 10 versions
                "latest_version": versions[0]["version"] if versions else None
            }
            
        except Exception as e:
            logger.warning(f"Could not get provider details for {namespace}/{provider_name}: {e}")
            return {
                "namespace": namespace,
                "name": provider_name,
                "full_name": f"{namespace}/{provider_name}",
                "description": "Provider details unavailable",
                "versions": [],
                "latest_version": None
            }
    
    async def get_modules(self, namespace: Optional[str] = None, provider: Optional[str] = None, 
                         search: Optional[str] = None, limit: int = 50, verified_only: bool = False) -> Dict[str, Any]:
        """
        Get Terraform modules from registry with enhanced filtering.
        
        Args:
            namespace: Module namespace
            provider: Provider name (e.g., 'aws', 'azure', 'google')
            search: Search term for module names/descriptions
            limit: Maximum number of modules to return
            verified_only: Only return verified modules
            
        Returns:
            Module information with enhanced metadata
        """
        try:
            session = await self._get_session()
            
            # Build URL based on parameters
            if namespace and provider:
                url = f"{self.base_url}/modules/{namespace}/{provider}"
            elif namespace:
                url = f"{self.base_url}/modules/{namespace}"
            else:
                url = f"{self.base_url}/modules"
            
            # Add query parameters
            params = []
            if limit:
                params.append(f"limit={limit}")
            if search:
                params.append(f"q={search}")
            if verified_only:
                params.append("verified=true")
            # Add provider filter if not already in URL path
            if provider and not namespace:
                params.append(f"provider={provider}")
            
            if params:
                url += "?" + "&".join(params)
            
            logger.debug(f"Modules API URL: {url}")
            
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Process module data with enhanced information
            modules = []
            for module in data.get("modules", []):
                module_info = {
                    "namespace": module.get("namespace"),
                    "name": module.get("name"),
                    "provider": module.get("provider"),
                    "description": module.get("description"),
                    "source": module.get("source"),
                    "downloads": module.get("downloads", 0),
                    "published_at": module.get("published_at"),
                    "verified": module.get("verified", False),
                    "version": module.get("version"),
                    "full_name": f"{module.get('namespace', '')}/{module.get('name', '')}/{module.get('provider', '')}",
                    "registry_url": f"https://registry.terraform.io/modules/{module.get('namespace', '')}/{module.get('name', '')}/{module.get('provider', '')}"
                }
                
                # Add category classification based on module name and description
                module_info["category"] = self._classify_module_category(module_info)
                
                # Add popularity score based on downloads and verification
                module_info["popularity_score"] = self._calculate_popularity_score(module_info)
                
                modules.append(module_info)
            
            # Sort by popularity score if no specific ordering requested
            if not namespace or not provider:
                modules.sort(key=lambda x: x["popularity_score"], reverse=True)
            
            return {
                "modules": modules,
                "total_count": len(modules),
                "namespace": namespace,
                "provider": provider,
                "search": search,
                "verified_only": verified_only,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    "Terraform Registry API rate limit exceeded",
                    CloudProvider.AWS,
                    "RATE_LIMIT_EXCEEDED"
                )
            else:
                raise CloudServiceError(
                    f"Terraform Registry API error: {e.response.status_code} - {e.response.text}",
                    CloudProvider.AWS,
                    "API_ERROR"
                )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting modules: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _classify_module_category(self, module_info: Dict[str, Any]) -> str:
        """
        Classify a module into a category based on its name and description.
        
        Args:
            module_info: Module information dictionary
            
        Returns:
            Category string
        """
        name = module_info.get("name", "").lower()
        description = module_info.get("description", "").lower()
        text = f"{name} {description}"
        
        # Define category keywords
        categories = {
            "compute": ["ec2", "instance", "vm", "compute", "server", "autoscaling", "ecs", "fargate", "lambda"],
            "storage": ["s3", "storage", "bucket", "disk", "volume", "blob", "file", "backup"],
            "database": ["rds", "database", "db", "sql", "mysql", "postgres", "mongodb", "dynamodb", "cosmos"],
            "networking": ["vpc", "network", "subnet", "route", "gateway", "load", "balancer", "cdn", "dns"],
            "security": ["iam", "security", "auth", "certificate", "ssl", "tls", "firewall", "waf", "vault"],
            "monitoring": ["cloudwatch", "monitor", "log", "metric", "alert", "dashboard", "observability"],
            "ai_ml": ["sagemaker", "ml", "ai", "machine", "learning", "cognitive", "vertex", "automl"],
            "container": ["kubernetes", "k8s", "docker", "container", "aks", "eks", "gke", "registry"],
            "devops": ["ci", "cd", "pipeline", "build", "deploy", "terraform", "ansible", "jenkins"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "other"
    
    def _calculate_popularity_score(self, module_info: Dict[str, Any]) -> float:
        """
        Calculate a popularity score for a module.
        
        Args:
            module_info: Module information dictionary
            
        Returns:
            Popularity score (higher is more popular)
        """
        downloads = module_info.get("downloads", 0)
        verified = module_info.get("verified", False)
        
        # Base score from downloads (log scale to prevent extreme values)
        import math
        score = math.log10(max(downloads, 1))
        
        # Bonus for verified modules
        if verified:
            score *= 1.5
        
        # Bonus for official/popular namespaces
        namespace = module_info.get("namespace", "").lower()
        if namespace in ["terraform-aws-modules", "azure", "terraform-google-modules", "hashicorp"]:
            score *= 1.3
        
        return round(score, 2)
    
    async def get_compute_modules(self) -> CloudServiceResponse:
        """Get compute-related Terraform modules."""
        try:
            # Get compute modules from major providers
            aws_compute = await self.get_modules(provider="aws")
            azure_compute = await self.get_modules(provider="azurerm")
            gcp_compute = await self.get_modules(provider="google")
            
            services = []
            
            # Process AWS compute modules
            for module in aws_compute.get("modules", []):
                if any(keyword in module.get("name", "").lower() for keyword in ["ec2", "compute", "instance", "autoscaling"]):
                    service = CloudService(
                        provider=CloudProvider.AWS,
                        service_name=f"Terraform Module: {module.get('name')}",
                        service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                        category=ServiceCategory.COMPUTE,
                        region="global",
                        description=module.get("description", "Terraform compute module"),
                        specifications={
                            "namespace": module.get("namespace"),
                            "provider": module.get("provider"),
                            "version": module.get("version"),
                            "verified": module.get("verified", False),
                            "downloads": module.get("downloads", 0)
                        },
                        features=["infrastructure_as_code", "version_controlled", "reusable"]
                    )
                    services.append(service)
            
            # Process Azure compute modules
            for module in azure_compute.get("modules", []):
                if any(keyword in module.get("name", "").lower() for keyword in ["vm", "compute", "instance", "scale"]):
                    service = CloudService(
                        provider=CloudProvider.AZURE,
                        service_name=f"Terraform Module: {module.get('name')}",
                        service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                        category=ServiceCategory.COMPUTE,
                        region="global",
                        description=module.get("description", "Terraform compute module"),
                        specifications={
                            "namespace": module.get("namespace"),
                            "provider": module.get("provider"),
                            "version": module.get("version"),
                            "verified": module.get("verified", False),
                            "downloads": module.get("downloads", 0)
                        },
                        features=["infrastructure_as_code", "version_controlled", "reusable"]
                    )
                    services.append(service)
            
            # Process GCP compute modules
            for module in gcp_compute.get("modules", []):
                if any(keyword in module.get("name", "").lower() for keyword in ["compute", "instance", "vm", "gce"]):
                    service = CloudService(
                        provider=CloudProvider.GCP,
                        service_name=f"Terraform Module: {module.get('name')}",
                        service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                        category=ServiceCategory.COMPUTE,
                        region="global",
                        description=module.get("description", "Terraform compute module"),
                        specifications={
                            "namespace": module.get("namespace"),
                            "provider": module.get("provider"),
                            "version": module.get("version"),
                            "verified": module.get("verified", False),
                            "downloads": module.get("downloads", 0)
                        },
                        features=["infrastructure_as_code", "version_controlled", "reusable"]
                    )
                    services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,  # Using AWS as base
                service_category=ServiceCategory.COMPUTE,
                region="global",
                services=services,
                metadata={"source": "terraform_registry", "module_type": "compute"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Error getting compute modules: {str(e)}",
                CloudProvider.AWS,
                "MODULE_ERROR"
            )
    
    async def get_storage_modules(self) -> CloudServiceResponse:
        """Get storage-related Terraform modules."""
        try:
            # Get storage modules from major providers
            aws_storage = await self.get_modules(provider="aws")
            azure_storage = await self.get_modules(provider="azurerm")
            gcp_storage = await self.get_modules(provider="google")
            
            services = []
            
            # Process storage modules from all providers
            for provider_data, cloud_provider in [
                (aws_storage, CloudProvider.AWS),
                (azure_storage, CloudProvider.AZURE),
                (gcp_storage, CloudProvider.GCP)
            ]:
                for module in provider_data.get("modules", []):
                    if any(keyword in module.get("name", "").lower() for keyword in ["s3", "storage", "bucket", "blob", "disk"]):
                        service = CloudService(
                            provider=cloud_provider,
                            service_name=f"Terraform Module: {module.get('name')}",
                            service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                            category=ServiceCategory.STORAGE,
                            region="global",
                            description=module.get("description", "Terraform storage module"),
                            specifications={
                                "namespace": module.get("namespace"),
                                "provider": module.get("provider"),
                                "version": module.get("version"),
                                "verified": module.get("verified", False),
                                "downloads": module.get("downloads", 0)
                            },
                            features=["infrastructure_as_code", "version_controlled", "reusable"]
                        )
                        services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,  # Using AWS as base
                service_category=ServiceCategory.STORAGE,
                region="global",
                services=services,
                metadata={"source": "terraform_registry", "module_type": "storage"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Error getting storage modules: {str(e)}",
                CloudProvider.AWS,
                "MODULE_ERROR"
            )
    
    async def get_database_modules(self) -> CloudServiceResponse:
        """Get database-related Terraform modules."""
        try:
            # Get database modules from major providers
            aws_db = await self.get_modules(provider="aws")
            azure_db = await self.get_modules(provider="azurerm")
            gcp_db = await self.get_modules(provider="google")
            
            services = []
            
            # Process database modules from all providers
            for provider_data, cloud_provider in [
                (aws_db, CloudProvider.AWS),
                (azure_db, CloudProvider.AZURE),
                (gcp_db, CloudProvider.GCP)
            ]:
                for module in provider_data.get("modules", []):
                    if any(keyword in module.get("name", "").lower() for keyword in ["rds", "database", "db", "sql", "mysql", "postgres", "mongodb"]):
                        service = CloudService(
                            provider=cloud_provider,
                            service_name=f"Terraform Module: {module.get('name')}",
                            service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                            category=ServiceCategory.DATABASE,
                            region="global",
                            description=module.get("description", "Terraform database module"),
                            specifications={
                                "namespace": module.get("namespace"),
                                "provider": module.get("provider"),
                                "version": module.get("version"),
                                "verified": module.get("verified", False),
                                "downloads": module.get("downloads", 0)
                            },
                            features=["infrastructure_as_code", "version_controlled", "reusable"]
                        )
                        services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,  # Using AWS as base
                service_category=ServiceCategory.DATABASE,
                region="global",
                services=services,
                metadata={"source": "terraform_registry", "module_type": "database"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Error getting database modules: {str(e)}",
                CloudProvider.AWS,
                "MODULE_ERROR"
            )
    
    async def get_ai_modules(self) -> CloudServiceResponse:
        """Get AI/ML-related Terraform modules."""
        try:
            # Get AI/ML modules from major providers
            aws_ai = await self.get_modules(provider="aws")
            azure_ai = await self.get_modules(provider="azurerm")
            gcp_ai = await self.get_modules(provider="google")
            
            services = []
            
            # Process AI/ML modules from all providers
            for provider_data, cloud_provider in [
                (aws_ai, CloudProvider.AWS),
                (azure_ai, CloudProvider.AZURE),
                (gcp_ai, CloudProvider.GCP)
            ]:
                for module in provider_data.get("modules", []):
                    if any(keyword in module.get("name", "").lower() for keyword in ["sagemaker", "ml", "ai", "machine", "learning", "cognitive", "vertex"]):
                        service = CloudService(
                            provider=cloud_provider,
                            service_name=f"Terraform Module: {module.get('name')}",
                            service_id=f"terraform_module_{module.get('namespace')}_{module.get('name')}_{module.get('provider')}",
                            category=ServiceCategory.AI_ML,
                            region="global",
                            description=module.get("description", "Terraform AI/ML module"),
                            specifications={
                                "namespace": module.get("namespace"),
                                "provider": module.get("provider"),
                                "version": module.get("version"),
                                "verified": module.get("verified", False),
                                "downloads": module.get("downloads", 0)
                            },
                            features=["infrastructure_as_code", "version_controlled", "reusable"]
                        )
                        services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,  # Using AWS as base
                service_category=ServiceCategory.AI_ML,
                region="global",
                services=services,
                metadata={"source": "terraform_registry", "module_type": "ai_ml"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Error getting AI/ML modules: {str(e)}",
                CloudProvider.AWS,
                "MODULE_ERROR"
            )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None