"""
Terraform API integration for Infra Mind.

Provides clients for Terraform Cloud API and Terraform Registry API.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
from urllib.parse import urljoin

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
    Main Terraform client that coordinates Terraform Cloud and Registry APIs.
    
    Learning Note: This acts as a facade for Terraform services,
    providing unified access to cost estimation and provider information.
    """
    
    def __init__(self, terraform_token: Optional[str] = None, organization: Optional[str] = None):
        """
        Initialize Terraform client.
        
        Args:
            terraform_token: Terraform Cloud API token (optional for registry access)
            organization: Terraform Cloud organization name
            
        Raises:
            AuthenticationError: If required credentials are missing for Terraform Cloud operations
        """
        super().__init__(CloudProvider.AWS, "global")  # Using AWS as base, region is global for Terraform
        
        self.terraform_token = terraform_token
        self.organization = organization
        
        # Initialize service clients
        self.cloud_client = TerraformCloudClient(terraform_token, organization)
        self.registry_client = TerraformRegistryClient()
    
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
    Terraform Cloud API client for cost estimation and workspace management.
    
    Learning Note: Terraform Cloud provides cost estimation for infrastructure
    changes before they are applied, helping with budget planning.
    """
    
    def __init__(self, terraform_token: Optional[str] = None, organization: Optional[str] = None):
        """
        Initialize Terraform Cloud client.
        
        Args:
            terraform_token: Terraform Cloud API token
            organization: Terraform Cloud organization name
        """
        self.terraform_token = terraform_token
        self.organization = organization
        self.base_url = "https://app.terraform.io/api/v2"
        self.session = None
    
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
            configuration: Terraform configuration
            
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
                        "auto-queue-runs": True
                    }
                }
            }
            
            config_url = f"{self.base_url}/workspaces/{workspace_id}/configuration-versions"
            config_response = await session.post(config_url, json=config_version_payload)
            config_response.raise_for_status()
            
            config_data = config_response.json()
            config_version = config_data.get("data", {})
            upload_url = config_version.get("attributes", {}).get("upload-url")
            
            # Upload configuration (simplified - in practice would upload tar.gz)
            if upload_url:
                # This would typically involve creating and uploading a tar.gz file
                # For now, we'll simulate this step
                logger.info(f"Configuration upload URL: {upload_url}")
            
            # Create a run
            run_payload = {
                "data": {
                    "type": "runs",
                    "attributes": {
                        "message": configuration.get("message", "Plan run from InfraMind"),
                        "is-destroy": configuration.get("is_destroy", False)
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
            
            # Wait a moment for the run to initialize, then get cost estimation
            await asyncio.sleep(2)
            
            try:
                cost_estimation = await self.get_cost_estimation(run.get("id"))
            except Exception as e:
                logger.warning(f"Could not get cost estimation: {e}")
                cost_estimation = {"cost_estimate": None, "error": str(e)}
            
            return {
                "run_id": run.get("id"),
                "status": run_attributes.get("status"),
                "message": run_attributes.get("message"),
                "created_at": run_attributes.get("created-at"),
                "workspace_id": workspace_id,
                "cost_estimation": cost_estimation,
                "plan_url": f"https://app.terraform.io/app/{self.organization}/workspaces/{workspace_id}/runs/{run.get('id')}"
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
    
    async def get_providers(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Terraform providers from registry.
        
        Args:
            namespace: Provider namespace (e.g., 'hashicorp', 'aws')
            
        Returns:
            Provider information
        """
        try:
            session = await self._get_session()
            
            if namespace:
                url = f"{self.base_url}/providers/{namespace}"
            else:
                url = f"{self.base_url}/providers"
            
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Process provider data
            providers = []
            if namespace:
                # Single namespace response
                provider_data = data.get("data", {})
                providers.append({
                    "namespace": provider_data.get("attributes", {}).get("namespace"),
                    "name": provider_data.get("attributes", {}).get("name"),
                    "full_name": provider_data.get("attributes", {}).get("full-name"),
                    "description": provider_data.get("attributes", {}).get("description"),
                    "source": provider_data.get("attributes", {}).get("source"),
                    "downloads": provider_data.get("attributes", {}).get("downloads"),
                    "published_at": provider_data.get("attributes", {}).get("published-at")
                })
            else:
                # Multiple providers response
                for provider in data.get("data", []):
                    attributes = provider.get("attributes", {})
                    providers.append({
                        "namespace": attributes.get("namespace"),
                        "name": attributes.get("name"),
                        "full_name": attributes.get("full-name"),
                        "description": attributes.get("description"),
                        "source": attributes.get("source"),
                        "downloads": attributes.get("downloads"),
                        "published_at": attributes.get("published-at")
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
    
    async def get_modules(self, namespace: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Terraform modules from registry.
        
        Args:
            namespace: Module namespace
            provider: Provider name (e.g., 'aws', 'azure', 'google')
            
        Returns:
            Module information
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
            
            response = await session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Process module data
            modules = []
            for module in data.get("modules", []):
                modules.append({
                    "namespace": module.get("namespace"),
                    "name": module.get("name"),
                    "provider": module.get("provider"),
                    "description": module.get("description"),
                    "source": module.get("source"),
                    "downloads": module.get("downloads"),
                    "published_at": module.get("published_at"),
                    "verified": module.get("verified", False),
                    "version": module.get("version")
                })
            
            return {
                "modules": modules,
                "total_count": len(modules),
                "namespace": namespace,
                "provider": provider,
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