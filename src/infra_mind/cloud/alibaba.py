"""
Alibaba Cloud integration for Infra Mind.

Provides comprehensive integration with Alibaba Cloud services including
ECS, RDS, OSS, and AI services for cost analysis and recommendations.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import asyncio
import aiohttp
import hashlib
import hmac
import base64
import urllib.parse
from dataclasses import dataclass

from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse, 
    CloudServiceError, ServiceCategory
)
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AlibabaCloudCredentials:
    """Alibaba Cloud authentication credentials."""
    access_key_id: str
    access_key_secret: str
    region: str = "us-west-1"
    security_token: Optional[str] = None


class AlibabaCloudClient(BaseCloudClient):
    """
    Alibaba Cloud API client for service discovery and cost analysis.
    
    Provides integration with Alibaba Cloud services including:
    - ECS (Elastic Compute Service)
    - RDS (Relational Database Service) 
    - OSS (Object Storage Service)
    - Function Compute
    - Container Service
    - AI services
    """
    
    def __init__(self, access_key_id: Optional[str] = None, access_key_secret: Optional[str] = None, region: str = "us-west-1"):
        """Initialize Alibaba Cloud client with credentials."""
        super().__init__(CloudProvider.ALIBABA, region)
        
        # Use provided credentials or get from environment
        if access_key_id and access_key_secret:
            self.credentials = AlibabaCloudCredentials(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                region=region
            )
        else:
            self.credentials = self._get_credentials_from_config()
            
        self.base_url = f"https://ecs.{self.credentials.region}.aliyuncs.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
    def _get_credentials_from_config(self) -> AlibabaCloudCredentials:
        """Get credentials from application configuration."""
        import os
        
        access_key_id = os.getenv('INFRA_MIND_ALIBABA_ACCESS_KEY_ID')
        access_key_secret = os.getenv('INFRA_MIND_ALIBABA_ACCESS_KEY_SECRET')
        region = os.getenv('INFRA_MIND_ALIBABA_REGION', 'us-west-1')
        security_token = os.getenv('INFRA_MIND_ALIBABA_SECURITY_TOKEN')
        
        if not access_key_id or not access_key_secret:
            raise CloudServiceError(
                "Alibaba Cloud credentials not configured. Please set INFRA_MIND_ALIBABA_ACCESS_KEY_ID and INFRA_MIND_ALIBABA_ACCESS_KEY_SECRET",
                CloudProvider.ALIBABA
            )
        
        return AlibabaCloudCredentials(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region=region,
            security_token=security_token
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _generate_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate Alibaba Cloud API signature."""
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Create canonical query string
        query_string = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
        
        # Create string to sign
        string_to_sign = f"{method}&{urllib.parse.quote('/', safe='')}&{urllib.parse.quote(query_string, safe='')}"
        
        # Generate signature
        key = f"{self.credentials.access_key_secret}&"
        signature = base64.b64encode(
            hmac.new(key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature
    
    async def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Alibaba Cloud API."""
        session = await self._get_session()
        
        # Prepare common parameters
        common_params = {
            "AccessKeyId": self.credentials.access_key_id,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(datetime.now().timestamp()),
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Version": "2014-05-26",
            "Format": "JSON"
        }
        
        if self.credentials.security_token:
            common_params["SecurityToken"] = self.credentials.security_token
        
        # Merge with request parameters
        all_params = {**common_params, **(params or {})}
        
        # Generate signature
        signature = self._generate_signature(method, endpoint, all_params)
        all_params["Signature"] = signature
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with session.get(url, params=all_params) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with session.post(url, data=all_params) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Alibaba Cloud API request failed: {e}")
            raise CloudServiceError(f"Alibaba Cloud API error: {str(e)}", CloudProvider.ALIBABA)
    
    async def get_ecs_instances(self) -> List[Dict[str, Any]]:
        """Get ECS instances in the region."""
        try:
            response = await self._make_request("GET", "/", {
                "Action": "DescribeInstances",
                "RegionId": self.credentials.region
            })
            
            instances = response.get("Instances", {}).get("Instance", [])
            return instances
        except Exception as e:
            logger.error(f"Failed to get ECS instances: {e}")
            return []
    
    async def get_rds_instances(self) -> List[Dict[str, Any]]:
        """Get RDS instances in the region."""
        try:
            # Switch to RDS endpoint
            original_url = self.base_url
            self.base_url = f"https://rds.{self.credentials.region}.aliyuncs.com"
            
            response = await self._make_request("GET", "/", {
                "Action": "DescribeDBInstances",
                "RegionId": self.credentials.region
            })
            
            # Restore original URL
            self.base_url = original_url
            
            instances = response.get("Items", {}).get("DBInstance", [])
            return instances
        except Exception as e:
            logger.error(f"Failed to get RDS instances: {e}")
            return []
    
    async def get_oss_buckets(self) -> List[Dict[str, Any]]:
        """Get OSS buckets in the account."""
        try:
            # Switch to OSS endpoint
            original_url = self.base_url
            self.base_url = f"https://oss-{self.credentials.region}.aliyuncs.com"
            
            response = await self._make_request("GET", "/", {
                "Action": "GetService"
            })
            
            # Restore original URL
            self.base_url = original_url
            
            buckets = response.get("Buckets", {}).get("Bucket", [])
            return buckets
        except Exception as e:
            logger.error(f"Failed to get OSS buckets: {e}")
            return []
    
    async def get_compute_services(self, region: str = None) -> CloudServiceResponse:
        """Get compute services from Alibaba Cloud."""
        region = region or self.region
        
        try:
            ecs_instances = await self.get_ecs_instances()
            
            services = [
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Elastic Compute Service",
                    service_id="ecs",
                    category=ServiceCategory.COMPUTE,
                    region=region,
                    description="Scalable cloud computing service",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.008,
                    pricing_unit="hour",
                    features=["Auto Scaling", "Load Balancing", "Security Groups", "Snapshots"],
                    specifications={"instances_running": len(ecs_instances)}
                )
            ]
            
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.COMPUTE,
                region=region,
                services=services,
                metadata={"total_ecs_instances": len(ecs_instances)},
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud compute services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.COMPUTE,
                region=region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_storage_services(self, region: str = None) -> CloudServiceResponse:
        """Get storage services from Alibaba Cloud."""
        region = region or self.region
        
        try:
            oss_buckets = await self.get_oss_buckets()
            
            services = [
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Object Storage Service",
                    service_id="oss",
                    category=ServiceCategory.STORAGE,
                    region=region,
                    description="Scalable object storage service",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.0099,
                    pricing_unit="GB/month",
                    features=["CDN Integration", "Lifecycle Management", "Cross-Region Replication"],
                    specifications={"buckets_count": len(oss_buckets)}
                )
            ]
            
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.STORAGE,
                region=region,
                services=services,
                metadata={"total_oss_buckets": len(oss_buckets)},
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud storage services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.STORAGE,
                region=region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_database_services(self, region: str = None) -> CloudServiceResponse:
        """Get database services from Alibaba Cloud."""
        region = region or self.region
        
        try:
            rds_instances = await self.get_rds_instances()
            
            services = [
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="ApsaraDB RDS",
                    service_id="rds",
                    category=ServiceCategory.DATABASE,
                    region=region,
                    description="Managed relational database service",
                    pricing_model="subscription",
                    hourly_price=0.02,
                    pricing_unit="hour",
                    features=["Multi-AZ", "Backup", "Performance Monitoring", "Read Replicas"],
                    specifications={"instances_running": len(rds_instances)}
                )
            ]
            
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.DATABASE,
                region=region,
                services=services,
                metadata={"total_rds_instances": len(rds_instances)},
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud database services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.DATABASE,
                region=region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_ai_services(self, region: str = None) -> CloudServiceResponse:
        """Get AI/ML services from Alibaba Cloud."""
        region = region or self.region
        
        try:
            services = [
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Machine Learning Platform for AI",
                    service_id="pai",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description="Comprehensive machine learning platform",
                    pricing_model="pay_per_use",
                    hourly_price=0.15,
                    pricing_unit="compute unit hour",
                    features=["AutoML", "Model Training", "Model Deployment", "Feature Store"],
                    specifications={}
                )
            ]
            
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                services=services,
                metadata={},
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud AI services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_service_pricing(self, service_id: str, region: str = None) -> Dict[str, Any]:
        """Get pricing information for a service."""
        pricing_client = AlibabaPricingClient(self.credentials)
        return await pricing_client.get_pricing(service_id, region)
    
    async def get_services(self) -> CloudServiceResponse:
        """Get available Alibaba Cloud services with real data."""
        try:
            # Get actual service instances
            ecs_instances = await self.get_ecs_instances()
            rds_instances = await self.get_rds_instances()
            oss_buckets = await self.get_oss_buckets()
            
            services = []
            
            # ECS Services
            services.extend([
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Elastic Compute Service",
                    service_id="ecs",
                    category=ServiceCategory.COMPUTE,
                    region=self.credentials.region,
                    description="Scalable cloud computing service",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.008,
                    pricing_unit="hour",
                    features=["Auto Scaling", "Load Balancing", "Security Groups", "Snapshots"],
                    specifications={"instances_running": len(ecs_instances)}
                ),
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="ApsaraDB RDS",
                    service_id="rds",
                    category=ServiceCategory.DATABASE,
                    region=self.credentials.region,
                    description="Managed relational database service",
                    pricing_model="subscription",
                    hourly_price=0.02,
                    pricing_unit="hour",
                    features=["Multi-AZ", "Backup", "Performance Monitoring", "Read Replicas"],
                    specifications={"instances_running": len(rds_instances)}
                ),
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Object Storage Service",
                    service_id="oss",
                    category=ServiceCategory.STORAGE,
                    region=self.credentials.region,
                    description="Scalable object storage service",
                    pricing_model="pay_as_you_go",
                    hourly_price=0.0099,
                    pricing_unit="GB/month",
                    features=["CDN Integration", "Lifecycle Management", "Cross-Region Replication"],
                    specifications={"buckets_count": len(oss_buckets)}
                ),
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Function Compute",
                    service_id="fc",
                    category=ServiceCategory.SERVERLESS,
                    region=self.credentials.region,
                    description="Event-driven serverless computing",
                    pricing_model="pay_per_request",
                    hourly_price=0.0000002,
                    pricing_unit="request",
                    features=["Event Triggers", "Auto Scaling", "Built-in Monitoring"],
                    specifications={}
                ),
                CloudService(
                    provider=CloudProvider.ALIBABA,
                    service_name="Container Service for Kubernetes",
                    service_id="ack",
                    category=ServiceCategory.CONTAINERS,
                    region=self.credentials.region,
                    description="Managed Kubernetes service",
                    pricing_model="pay_for_nodes",
                    hourly_price=0.05,
                    pricing_unit="node/hour",
                    features=["Managed Control Plane", "Auto Scaling", "Service Mesh"],
                    specifications={}
                )
            ])
            
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.COMPUTE,
                region=self.credentials.region,
                services=services,
                metadata={"total_services": len(services)},
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud services: {e}")
            return CloudServiceResponse(
                provider=CloudProvider.ALIBABA,
                service_category=ServiceCategory.COMPUTE,
                region=self.credentials.region,
                services=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_cost_data(self, days: int = 30) -> Dict[str, Any]:
        """Get cost data for the account."""
        try:
            # Switch to Billing endpoint
            original_url = self.base_url
            self.base_url = f"https://business.{self.credentials.region}.aliyuncs.com"
            
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(day=1)  # First day of current month
            
            response = await self._make_request("GET", "/", {
                "Action": "QueryBill",
                "BillingCycle": start_time.strftime("%Y-%m"),
                "ProductCode": "",
                "ProductType": "",
                "SubscriptionType": ""
            })
            
            # Restore original URL
            self.base_url = original_url
            
            return {
                "total_cost": response.get("Data", {}).get("TotalCount", 0),
                "currency": "USD",
                "billing_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "services": response.get("Data", {}).get("Items", {}).get("Item", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get Alibaba Cloud cost data: {e}")
            return {"total_cost": 0, "currency": "USD", "services": []}
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()


class AlibabaPricingClient:
    """Client for Alibaba Cloud pricing information."""
    
    def __init__(self, credentials: Optional[AlibabaCloudCredentials] = None):
        self.credentials = credentials or AlibabaCloudClient()._get_credentials_from_config()
    
    async def get_pricing(self, service_id: str, region: str = None) -> Dict[str, Any]:
        """Get pricing information for a specific service."""
        # Alibaba Cloud pricing is typically region-specific
        region = region or self.credentials.region
        
        # Mock pricing data - in production, this would query the actual Alibaba Cloud Pricing API
        pricing_data = {
            "ecs": {
                "compute": {"price": 0.008, "unit": "per hour", "instance_type": "ecs.t5-lc1m1.small"},
                "storage": {"price": 0.0001, "unit": "per GB/hour"},
                "network": {"price": 0.01, "unit": "per GB"}
            },
            "rds": {
                "instance": {"price": 0.02, "unit": "per hour", "instance_class": "rds.mysql.t1.small"},
                "storage": {"price": 0.0002, "unit": "per GB/hour"},
                "backup": {"price": 0.00005, "unit": "per GB/hour"}
            },
            "oss": {
                "storage": {"price": 0.0099, "unit": "per GB/month"},
                "requests": {"price": 0.0004, "unit": "per 10,000 requests"},
                "data_transfer": {"price": 0.08, "unit": "per GB"}
            }
        }
        
        return pricing_data.get(service_id, {})


# Convenience function to create authenticated client
def create_alibaba_client() -> AlibabaCloudClient:
    """Create an authenticated Alibaba Cloud client using configuration."""
    return AlibabaCloudClient()