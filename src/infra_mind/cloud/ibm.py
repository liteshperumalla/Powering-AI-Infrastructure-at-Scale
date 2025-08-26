"""
IBM Cloud integration for Infra Mind.

Provides comprehensive integration with IBM Cloud services including
Virtual Servers, Databases, Cloud Object Storage, Watson AI services,
and Red Hat OpenShift for cost analysis and recommendations.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import asyncio
import aiohttp
import base64
import json
from dataclasses import dataclass

from .base import CloudProvider, CloudService, CloudServiceResponse, CloudServiceError, ServiceCategory
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class IBMCloudCredentials:
    """IBM Cloud authentication credentials."""
    api_key: str
    account_id: str
    region: str = "us-south"
    resource_group_id: Optional[str] = None


class IBMCloudClient:
    """
    IBM Cloud API client for service discovery and cost analysis.
    
    Provides integration with IBM Cloud services including:
    - Virtual Server Instances (VSI)
    - Cloud Databases
    - Cloud Object Storage (COS)
    - Watson AI services
    - Red Hat OpenShift on IBM Cloud
    - Container Registry
    """
    
    def __init__(self, credentials: Optional[IBMCloudCredentials] = None):
        """Initialize IBM Cloud client with credentials."""
        self.credentials = credentials or self._get_credentials_from_config()
        self.base_url = "https://resource-controller.cloud.ibm.com"
        self.iam_url = "https://iam.cloud.ibm.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    def _get_credentials_from_config(self) -> IBMCloudCredentials:
        """Get credentials from application configuration."""
        if not settings.ibm_api_key or not settings.ibm_account_id:
            raise CloudServiceError(
                "IBM Cloud credentials not configured. Please set INFRA_MIND_IBM_API_KEY and INFRA_MIND_IBM_ACCOUNT_ID",
                CloudProvider.IBM
            )
        
        return IBMCloudCredentials(
            api_key=settings.ibm_api_key.get_secret_value(),
            account_id=settings.ibm_account_id,
            region=settings.ibm_region,
            resource_group_id=settings.ibm_resource_group_id
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _get_access_token(self) -> str:
        """Get IAM access token for authentication."""
        # Check if token is still valid
        if (self._access_token and self._token_expires_at and 
            datetime.now(timezone.utc) < self._token_expires_at):
            return self._access_token
        
        session = await self._get_session()
        
        # Prepare IAM token request
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "urn:iam:params:oauth:grant-type:apikey",
            "apikey": self.credentials.api_key
        }
        
        try:
            async with session.post(f"{self.iam_url}/identity/token", 
                                  headers=headers, data=data) as response:
                response.raise_for_status()
                token_data = await response.json()
                
                self._access_token = token_data["access_token"]
                # Set expiration 5 minutes before actual expiry for safety
                expires_in = token_data.get("expires_in", 3600) - 300
                self._token_expires_at = datetime.now(timezone.utc).replace(
                    second=0, microsecond=0
                ) + timedelta(seconds=expires_in)
                
                return self._access_token
                
        except aiohttp.ClientError as e:
            logger.error(f"IBM Cloud IAM token request failed: {e}")
            raise CloudServiceError(f"IBM Cloud authentication failed: {str(e)}", CloudProvider.IBM)
    
    async def _make_request(self, method: str, url: str, params: Dict[str, Any] = None, 
                           data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to IBM Cloud API."""
        session = await self._get_session()
        access_token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with session.request(method, url, headers=headers, 
                                         params=params, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"IBM Cloud API request failed: {e}")
            raise CloudServiceError(f"IBM Cloud API error: {str(e)}", CloudProvider.IBM)
    
    async def get_virtual_servers(self) -> List[Dict[str, Any]]:
        """Get Virtual Server Instances in the account."""
        try:
            url = f"https://{self.credentials.region}.iaas.cloud.ibm.com/v1/instances"
            params = {
                "version": "2023-12-19",
                "generation": "2"
            }
            
            response = await self._make_request("GET", url, params=params)
            return response.get("instances", [])
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud virtual servers: {e}")
            return []
    
    async def get_databases(self) -> List[Dict[str, Any]]:
        """Get Cloud Database instances."""
        try:
            url = f"https://resource-controller.cloud.ibm.com/v2/resource_instances"
            params = {
                "account_id": self.credentials.account_id,
                "resource_group_id": self.credentials.resource_group_id,
                "type": "service_instance"
            }
            
            response = await self._make_request("GET", url, params=params)
            
            # Filter for database services
            databases = []
            for resource in response.get("resources", []):
                resource_plan = resource.get("resource_plan_id", "")
                if "database" in resource_plan.lower() or "mongo" in resource_plan.lower():
                    databases.append(resource)
            
            return databases
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud databases: {e}")
            return []
    
    async def get_object_storage(self) -> List[Dict[str, Any]]:
        """Get Cloud Object Storage instances."""
        try:
            url = f"https://resource-controller.cloud.ibm.com/v2/resource_instances"
            params = {
                "account_id": self.credentials.account_id,
                "resource_group_id": self.credentials.resource_group_id,
                "type": "service_instance"
            }
            
            response = await self._make_request("GET", url, params=params)
            
            # Filter for Cloud Object Storage
            storage_instances = []
            for resource in response.get("resources", []):
                if "cloud-object-storage" in resource.get("resource_id", ""):
                    storage_instances.append(resource)
            
            return storage_instances
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud Object Storage: {e}")
            return []
    
    async def get_openshift_clusters(self) -> List[Dict[str, Any]]:
        """Get Red Hat OpenShift clusters."""
        try:
            url = f"https://containers.cloud.ibm.com/global/v1/clusters"
            response = await self._make_request("GET", url)
            
            # Filter for OpenShift clusters
            openshift_clusters = []
            for cluster in response:
                if cluster.get("type") == "openshift":
                    openshift_clusters.append(cluster)
            
            return openshift_clusters
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud OpenShift clusters: {e}")
            return []
    
    async def get_watson_services(self) -> List[Dict[str, Any]]:
        """Get Watson AI services."""
        try:
            url = f"https://resource-controller.cloud.ibm.com/v2/resource_instances"
            params = {
                "account_id": self.credentials.account_id,
                "resource_group_id": self.credentials.resource_group_id,
                "type": "service_instance"
            }
            
            response = await self._make_request("GET", url, params=params)
            
            # Filter for Watson services
            watson_services = []
            watson_service_ids = [
                "watson-assistant", "watson-discovery", "watson-language-translator",
                "watson-natural-language-understanding", "watson-speech-to-text",
                "watson-text-to-speech", "watson-tone-analyzer", "watson-visual-recognition"
            ]
            
            for resource in response.get("resources", []):
                resource_id = resource.get("resource_id", "")
                if any(service_id in resource_id for service_id in watson_service_ids):
                    watson_services.append(resource)
            
            return watson_services
        except Exception as e:
            logger.error(f"Failed to get IBM Watson services: {e}")
            return []
    
    async def get_services(self) -> CloudServiceResponse:
        """Get available IBM Cloud services with real data."""
        try:
            # Get actual service instances
            virtual_servers = await self.get_virtual_servers()
            databases = await self.get_databases()
            storage_instances = await self.get_object_storage()
            openshift_clusters = await self.get_openshift_clusters()
            watson_services = await self.get_watson_services()
            
            services = []
            
            # IBM Cloud Services
            services.extend([
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Virtual Server for VPC",
                    service_id="vpc-virtual-server",
                    category=ServiceCategory.COMPUTE,
                    region=self.credentials.region,
                    description="Scalable virtual servers on IBM Cloud VPC",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.0464,
                    pricing_unit="hour",
                    features=["Auto-scaling", "Load balancing", "Security groups", "Snapshots"],
                    specifications={
                        "instances_running": len(virtual_servers),
                        "min_vcpu": 1,
                        "max_vcpu": 80,
                        "min_memory_gb": 1,
                        "max_memory_gb": 640
                    }
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Databases for MongoDB",
                    service_id="databases-for-mongodb",
                    category=ServiceCategory.DATABASE,
                    region=self.credentials.region,
                    description="Managed MongoDB database service",
                    pricing_model="subscription",
                    hourly_price=0.058,
                    pricing_unit="hour",
                    features=["Auto-scaling", "Backup", "Monitoring", "High availability"],
                    specifications={"instances_running": len(databases)}
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Cloud Object Storage",
                    service_id="cloud-object-storage",
                    category=ServiceCategory.STORAGE,
                    region=self.credentials.region,
                    description="Scalable and secure object storage",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.023,
                    pricing_unit="GB/month",
                    features=["Cross-region replication", "Lifecycle policies", "Encryption"],
                    specifications={"instances_running": len(storage_instances)}
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Red Hat OpenShift on IBM Cloud",
                    service_id="openshift",
                    category=ServiceCategory.CONTAINERS,
                    region=self.credentials.region,
                    description="Managed OpenShift Kubernetes platform",
                    pricing_model="pay_for_nodes",
                    hourly_price=0.08,
                    pricing_unit="node/hour",
                    features=["Managed control plane", "Auto-scaling", "Service mesh", "GitOps"],
                    specifications={"clusters_running": len(openshift_clusters)}
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Watson Assistant",
                    service_id="watson-assistant",
                    category=ServiceCategory.AI_ML,
                    region=self.credentials.region,
                    description="AI-powered virtual assistant",
                    pricing_model="pay_per_use",
                    hourly_price=0.0025,
                    pricing_unit="API call",
                    features=["Natural language processing", "Voice integration", "Analytics"],
                    specifications={"watson_services": len(watson_services)}
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Watson Discovery",
                    service_id="watson-discovery",
                    category=ServiceCategory.AI_ML,
                    region=self.credentials.region,
                    description="AI-powered search and text analytics",
                    pricing_model="pay_per_use",
                    hourly_price=0.001,
                    pricing_unit="document",
                    features=["Document understanding", "Query building", "Smart search"],
                    specifications={"watson_services": len(watson_services)}
                ),
                CloudService(
                    provider=CloudProvider.IBM,
                    service_name="Code Engine",
                    service_id="code-engine",
                    category=ServiceCategory.SERVERLESS,
                    region=self.credentials.region,
                    description="Serverless platform for containerized applications",
                    pricing_model="pay_per_use",
                    hourly_price=0.000024,
                    pricing_unit="vCPU-second",
                    features=["Auto-scaling", "Event-driven", "No infrastructure management"],
                    specifications={}
                )
            ])
            
            return CloudServiceResponse(
                provider=CloudProvider.IBM,
                service_category=ServiceCategory.COMPUTE,  # Default category
                region=self.credentials.region,
                services=services,
                metadata={
                    "total_virtual_servers": len(virtual_servers),
                    "total_databases": len(databases),
                    "total_storage_instances": len(storage_instances),
                    "total_openshift_clusters": len(openshift_clusters),
                    "total_watson_services": len(watson_services)
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.IBM,
                service_category=ServiceCategory.COMPUTE,
                region=self.credentials.region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_cost_data(self, days: int = 30) -> Dict[str, Any]:
        """Get cost data for the account."""
        try:
            url = f"https://partner.cloud.ibm.com/v1/billing/usage"
            
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(day=1)  # First day of current month
            
            params = {
                "account_id": self.credentials.account_id,
                "year": start_time.year,
                "month": start_time.month
            }
            
            response = await self._make_request("GET", url, params=params)
            
            return {
                "total_cost": response.get("billable_cost", 0),
                "currency": response.get("currency_code", "USD"),
                "billing_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "services": response.get("offers", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get IBM Cloud cost data: {e}")
            return {"total_cost": 0, "currency": "USD", "services": []}
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()


class IBMPricingClient:
    """Client for IBM Cloud pricing information."""
    
    def __init__(self, credentials: Optional[IBMCloudCredentials] = None):
        self.credentials = credentials or IBMCloudClient()._get_credentials_from_config()
    
    async def get_pricing(self, service_id: str, region: str = None) -> Dict[str, Any]:
        """Get pricing information for a specific service."""
        region = region or self.credentials.region
        
        # IBM Cloud pricing data
        pricing_data = {
            "vpc-virtual-server": {
                "compute": {"price": 0.0464, "unit": "per hour", "instance_type": "bx2-2x8"},
                "storage": {"price": 0.00014, "unit": "per GB/hour"},
                "network": {"price": 0.09, "unit": "per GB"}
            },
            "databases-for-mongodb": {
                "instance": {"price": 0.058, "unit": "per hour", "plan": "standard"},
                "storage": {"price": 0.00035, "unit": "per GB/hour"},
                "backup": {"price": 0.00007, "unit": "per GB/hour"}
            },
            "cloud-object-storage": {
                "storage": {"price": 0.023, "unit": "per GB/month"},
                "requests": {"price": 0.0004, "unit": "per 1,000 requests"},
                "data_transfer": {"price": 0.09, "unit": "per GB"}
            },
            "openshift": {
                "worker_node": {"price": 0.08, "unit": "per node/hour", "flavor": "b3c.4x16"},
                "storage": {"price": 0.00014, "unit": "per GB/hour"},
                "load_balancer": {"price": 0.025, "unit": "per hour"}
            }
        }
        
        return pricing_data.get(service_id, {})


# Convenience function to create authenticated client
def create_ibm_client() -> IBMCloudClient:
    """Create an authenticated IBM Cloud client using configuration."""
    return IBMCloudClient()