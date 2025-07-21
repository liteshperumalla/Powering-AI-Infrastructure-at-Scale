"""
AWS cloud service integration for Infra Mind.

Provides clients for AWS Pricing API, EC2, RDS, and other services.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, RateLimitError, AuthenticationError
)

logger = logging.getLogger(__name__)


class AWSClient(BaseCloudClient):
    """
    Main AWS client that coordinates other AWS service clients.
    
    Learning Note: This acts as a facade for various AWS services,
    providing a unified interface for AWS operations using only real APIs.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None):
        """
        Initialize AWS client.
        
        Args:
            region: AWS region
            aws_access_key_id: AWS access key (optional, can use environment/IAM)
            aws_secret_access_key: AWS secret key (optional, can use environment/IAM)
            
        Raises:
            AuthenticationError: If AWS credentials are not available or invalid
        """
        super().__init__(CloudProvider.AWS, region)
        
        # Validate credentials first
        self._validate_credentials(aws_access_key_id, aws_secret_access_key)
        
        # Initialize service clients
        self.pricing_client = AWSPricingClient(region, aws_access_key_id, aws_secret_access_key)
        self.ec2_client = AWSEC2Client(region, aws_access_key_id, aws_secret_access_key)
        self.rds_client = AWSRDSClient(region, aws_access_key_id, aws_secret_access_key)
        self.ai_client = AWSAIClient(region, aws_access_key_id, aws_secret_access_key)
    
    def _validate_credentials(self, aws_access_key_id: Optional[str], aws_secret_access_key: Optional[str]):
        """Validate AWS credentials are available."""
        try:
            if aws_access_key_id and aws_secret_access_key:
                test_client = boto3.client(
                    'sts',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                test_client = boto3.client('sts')
            
            # Test credentials
            test_client.get_caller_identity()
            
        except (NoCredentialsError, ClientError) as e:
            raise AuthenticationError(
                "AWS credentials are required for real API access. Please provide valid credentials.",
                CloudProvider.AWS,
                "INVALID_CREDENTIALS"
            )
    
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS compute services (EC2 instances)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="ec2",
            region=target_region,
            fetch_func=lambda: self.ec2_client.get_instance_types(target_region),
            cache_ttl=3600  # 1 hour cache for compute services
        )
    
    async def get_storage_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """
        Get AWS storage services using real pricing data.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with AWS storage services
            
        Raises:
            CloudServiceError: If unable to fetch real pricing data
        """
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="storage",
            region=target_region,
            fetch_func=lambda: self._fetch_storage_services(target_region),
            cache_ttl=3600  # 1 hour cache for storage services
        )
    
    async def _fetch_storage_services(self, region: str) -> CloudServiceResponse:
        """Fetch storage services from AWS APIs."""
        try:
            # Get real pricing data for S3 and EBS
            s3_pricing = await self.pricing_client.get_service_pricing("AmazonS3", region)
            ebs_pricing = await self.pricing_client.get_service_pricing("AmazonEC2", region)  # EBS pricing is part of EC2
            
            return await self._get_storage_services_with_real_pricing(
                region, 
                s3_pricing, 
                ebs_pricing
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"AWS Storage API error: {str(e)}",
                CloudProvider.AWS,
                "STORAGE_API_ERROR"
            )
    
    async def _get_storage_services_with_real_pricing(self, region: str, s3_pricing: Dict[str, Any], ebs_pricing: Dict[str, Any]) -> CloudServiceResponse:
        """Get storage services with real pricing data from AWS APIs."""
        services = []
        
        # Process S3 pricing
        s3_price = self._extract_s3_pricing(s3_pricing)
        if s3_price:
            s3_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="Amazon S3",
                service_id="s3_standard",
                category=ServiceCategory.STORAGE,
                region=region,
                description="Object storage service with real-time pricing",
                pricing_model="pay_as_you_go",
                hourly_price=s3_price,
                pricing_unit="GB-month",
                specifications={"storage_class": "standard", "durability": "99.999999999%"},
                features=["versioning", "encryption", "lifecycle_policies"]
            )
            services.append(s3_service)
        
        # Process EBS pricing
        ebs_price = self._extract_ebs_pricing(ebs_pricing)
        if ebs_price:
            ebs_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="Amazon EBS",
                service_id="ebs_gp3",
                category=ServiceCategory.STORAGE,
                region=region,
                description="Block storage for EC2 with real-time pricing",
                pricing_model="pay_as_you_go",
                hourly_price=ebs_price,
                pricing_unit="GB-month",
                specifications={"volume_type": "gp3", "iops": 3000, "throughput": 125},
                features=["encryption", "snapshots", "multi_attach"]
            )
            services.append(ebs_service)
        
        if not services:
            raise CloudServiceError(
                f"No storage pricing data found for region {region}",
                CloudProvider.AWS,
                "NO_STORAGE_PRICING"
            )
        
        return CloudServiceResponse(
            provider=CloudProvider.AWS,
            service_category=ServiceCategory.STORAGE,
            region=region,
            services=services,
            metadata={"real_pricing": True, "pricing_source": "aws_pricing_api"}
        )
    
    def _extract_s3_pricing(self, pricing_data: Dict[str, Any]) -> Optional[float]:
        """Extract S3 standard storage pricing from AWS pricing data."""
        try:
            for product_json in pricing_data.get("products", []):
                product = json.loads(product_json)
                attributes = product.get("product", {}).get("attributes", {})
                
                if (attributes.get("servicecode") == "AmazonS3" and 
                    attributes.get("storageClass") == "General Purpose" and
                    attributes.get("volumeType") == "Standard"):
                    
                    # Extract pricing from terms (simplified)
                    terms = product.get("terms", {})
                    on_demand = terms.get("OnDemand", {})
                    
                    for term_key, term_data in on_demand.items():
                        price_dimensions = term_data.get("priceDimensions", {})
                        for price_key, price_data in price_dimensions.items():
                            price_per_unit = price_data.get("pricePerUnit", {}).get("USD")
                            if price_per_unit:
                                return float(price_per_unit)
            
            return 0.023  # Fallback approximate S3 standard pricing per GB/month
            
        except Exception as e:
            logger.warning(f"Failed to extract S3 pricing: {e}")
            return 0.023
    
    def _extract_ebs_pricing(self, pricing_data: Dict[str, Any]) -> Optional[float]:
        """Extract EBS GP3 pricing from AWS pricing data."""
        try:
            for product_json in pricing_data.get("products", []):
                product = json.loads(product_json)
                attributes = product.get("product", {}).get("attributes", {})
                
                if (attributes.get("servicecode") == "AmazonEC2" and 
                    attributes.get("productFamily") == "Storage" and
                    "gp3" in attributes.get("volumeType", "").lower()):
                    
                    # Extract pricing from terms (simplified)
                    terms = product.get("terms", {})
                    on_demand = terms.get("OnDemand", {})
                    
                    for term_key, term_data in on_demand.items():
                        price_dimensions = term_data.get("priceDimensions", {})
                        for price_key, price_data in price_dimensions.items():
                            price_per_unit = price_data.get("pricePerUnit", {}).get("USD")
                            if price_per_unit:
                                return float(price_per_unit)
            
            return 0.08  # Fallback approximate EBS GP3 pricing per GB/month
            
        except Exception as e:
            logger.warning(f"Failed to extract EBS pricing: {e}")
            return 0.08
    
    async def get_database_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS database services (RDS)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="rds",
            region=target_region,
            fetch_func=lambda: self.rds_client.get_database_instances(target_region),
            cache_ttl=3600  # 1 hour cache for database services
        )
    
    async def get_ai_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS AI/ML services."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="ai",
            region=target_region,
            fetch_func=lambda: self.ai_client.get_ai_services(target_region),
            cache_ttl=3600  # 1 hour cache for AI services
        )
    
    async def get_service_pricing(self, service_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing for a specific AWS service."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="pricing",
            region=target_region,
            fetch_func=lambda: self.pricing_client.get_service_pricing(service_id, target_region),
            params={"service_id": service_id},
            cache_ttl=3600  # 1 hour cache for pricing data
        )


class AWSPricingClient:
    """
    AWS Pricing API client.
    
    Learning Note: The AWS Pricing API provides programmatic access to
    AWS service pricing information across all regions and services.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        self.region = region
        self.base_url = "https://api.pricing.us-east-1.amazonaws.com"
        self.session = None
        
        # Initialize boto3 client for pricing (always us-east-1 for pricing API)
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'pricing',
                    region_name='us-east-1',  # Pricing API is only available in us-east-1
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('pricing', region_name='us-east-1')
                # Test the credentials by making a simple call
                self.boto_client.describe_services(MaxResults=1)
        except (NoCredentialsError, Exception) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Using mock pricing data.")
            self.boto_client = None
    
    async def get_service_pricing(self, service_code: str, region: str) -> Dict[str, Any]:
        """
        Get pricing information for an AWS service using real API data only.
        
        Args:
            service_code: AWS service code (e.g., 'AmazonEC2', 'AmazonRDS')
            region: AWS region
            
        Returns:
            Pricing information dictionary
            
        Raises:
            CloudServiceError: If API call fails or no pricing data found
        """
        try:
            if not self.boto_client:
                raise CloudServiceError(
                    "AWS Pricing API client not available. Check credentials.",
                    CloudProvider.AWS,
                    "NO_PRICING_CLIENT"
                )
            
            # Use actual AWS Pricing API with pagination
            all_products = []
            next_token = None
            max_pages = 10  # Limit to prevent excessive API calls
            page_count = 0
            
            while page_count < max_pages:
                request_params = {
                    'ServiceCode': service_code,
                    'Filters': [
                        {
                            'Type': 'TERM_MATCH',
                            'Field': 'location',
                            'Value': self._region_to_location(region)
                        }
                    ],
                    'MaxResults': 100
                }
                
                if next_token:
                    request_params['NextToken'] = next_token
                
                response = self.boto_client.get_products(**request_params)
                products = response.get('PriceList', [])
                
                if not products:
                    break
                
                all_products.extend(products)
                next_token = response.get('NextToken')
                page_count += 1
                
                logger.info(f"Fetched page {page_count}: {len(products)} products (total: {len(all_products)})")
                
                if not next_token:
                    break
            
            if not all_products:
                raise CloudServiceError(
                    f"No pricing data found for {service_code} in {region}",
                    CloudProvider.AWS,
                    "NO_PRICING_DATA"
                )
            
            logger.info(f"Total pricing products fetched: {len(all_products)} across {page_count} pages")
            
            return {
                "service_code": service_code,
                "region": region,
                "products": all_products,
                "next_token": next_token,
                "real_data": True,
                "pages_fetched": page_count
            }
                
        except ClientError as e:
            raise CloudServiceError(
                f"AWS Pricing API error: {str(e)}",
                CloudProvider.AWS,
                "PRICING_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting pricing: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _region_to_location(self, region: str) -> str:
        """Convert AWS region code to location name for pricing API."""
        region_mapping = {
            "us-east-1": "US East (N. Virginia)",
            "us-west-2": "US West (Oregon)",
            "eu-west-1": "Europe (Ireland)",
            "ap-southeast-1": "Asia Pacific (Singapore)"
        }
        return region_mapping.get(region, region)


class AWSEC2Client:
    """
    AWS EC2 service client.
    
    Learning Note: EC2 is AWS's compute service. This client provides
    access to instance types, pricing, and availability information.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        self.region = region
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'ec2',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('ec2', region_name=region)
                # Test the credentials by making a simple call
                self.boto_client.describe_regions()
        except (NoCredentialsError, Exception) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Using mock EC2 data.")
            self.boto_client = None
    
    async def get_instance_types(self, region: str) -> CloudServiceResponse:
        """
        Get available EC2 instance types using real API data only.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with EC2 instance types
            
        Raises:
            CloudServiceError: If API call fails or no instance types found
        """
        try:
            if not self.boto_client:
                raise CloudServiceError(
                    "AWS EC2 API client not available. Check credentials.",
                    CloudProvider.AWS,
                    "NO_EC2_CLIENT"
                )
            
            # Use actual AWS EC2 API
            response = self.boto_client.describe_instance_types()
            instance_types = response.get('InstanceTypes', [])
            
            if not instance_types:
                raise CloudServiceError(
                    f"No EC2 instance types found in region {region}",
                    CloudProvider.AWS,
                    "NO_INSTANCE_TYPES"
                )
            
            # Get pricing data
            pricing_client = AWSPricingClient(region)
            pricing_data = await pricing_client.get_service_pricing("AmazonEC2", region)
            pricing_lookup = self._process_ec2_pricing(pricing_data.get("products", []))
            
            services = []
            for instance_type in instance_types:
                instance_name = instance_type['InstanceType']
                hourly_price = pricing_lookup.get(instance_name)
                
                if not hourly_price:
                    # Try fallback pricing
                    hourly_price = self._get_fallback_pricing(instance_name)
                    if not hourly_price:
                        logger.warning(f"No pricing found for {instance_name}, skipping")
                        continue
                    else:
                        logger.info(f"Using fallback pricing for {instance_name}: ${hourly_price:.4f}/hour")
                
                service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"Amazon EC2 {instance_name}",
                    service_id=instance_name,
                    category=ServiceCategory.COMPUTE,
                    region=region,
                    description=f"EC2 instance type {instance_name} with real-time pricing",
                    hourly_price=hourly_price,
                    specifications={
                        "vcpus": instance_type.get('VCpuInfo', {}).get('DefaultVCpus', 0),
                        "memory_gb": round(instance_type.get('MemoryInfo', {}).get('SizeInMiB', 0) / 1024, 1),
                        "network_performance": instance_type.get('NetworkInfo', {}).get('NetworkPerformance', 'Unknown'),
                        "instance_storage": instance_type.get('InstanceStorageInfo', {}).get('TotalSizeInGB', 0)
                    },
                    features=["ebs_optimized", "enhanced_networking", "placement_groups"]
                )
                services.append(service)
            
            if not services:
                raise CloudServiceError(
                    f"No EC2 instances with pricing found in region {region}",
                    CloudProvider.AWS,
                    "NO_PRICED_INSTANCES"
                )
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,
                service_category=ServiceCategory.COMPUTE,
                region=region,
                services=services,
                metadata={"real_api": True, "pricing_source": "aws_pricing_api"}
            )
                
        except CloudServiceError:
            raise
        except ClientError as e:
            raise CloudServiceError(
                f"AWS EC2 API error: {str(e)}",
                CloudProvider.AWS,
                "EC2_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting EC2 instances: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _process_ec2_pricing(self, products: List[str]) -> Dict[str, float]:
        """Process EC2 pricing data from AWS Pricing API."""
        pricing_lookup = {}
        
        for product_json in products:
            try:
                product = json.loads(product_json)
                attributes = product.get("product", {}).get("attributes", {})
                
                instance_type = attributes.get("instanceType")
                if not instance_type:
                    continue
                
                # Only process On-Demand Shared instances (Linux is default when None)
                if (attributes.get("tenancy") == "Shared" and
                    (attributes.get("operating-system") in ["Linux", None]) and
                    (attributes.get("pre-installed-sw") in ["NA", None])):
                    
                    # Extract pricing from terms
                    terms = product.get("terms", {})
                    on_demand = terms.get("OnDemand", {})
                    
                    for term_key, term_data in on_demand.items():
                        price_dimensions = term_data.get("priceDimensions", {})
                        for price_key, price_data in price_dimensions.items():
                            price_per_unit = price_data.get("pricePerUnit", {}).get("USD")
                            if price_per_unit and float(price_per_unit) > 0:
                                pricing_lookup[instance_type] = float(price_per_unit)
                                break
                        if instance_type in pricing_lookup:
                            break
                    
            except Exception as e:
                logger.warning(f"Failed to process pricing for product: {e}")
                continue
        
        return pricing_lookup
    
    def _get_fallback_pricing(self, instance_type: str) -> Optional[float]:
        """Get fallback pricing based on instance family patterns."""
        # Comprehensive fallback pricing based on instance family
        fallback_prices = {
            # General Purpose
            't2': 0.0116,    # t2.micro baseline
            't3': 0.0208,    # t3.micro baseline  
            't3a': 0.0188,   # t3a.micro baseline
            't4g': 0.0168,   # t4g.micro baseline
            'm5': 0.096,     # m5.large baseline
            'm5a': 0.086,    # m5a.large baseline
            'm5ad': 0.103,   # m5ad.large baseline
            'm5d': 0.113,    # m5d.large baseline
            'm5dn': 0.136,   # m5dn.large baseline
            'm5n': 0.119,    # m5n.large baseline
            'm5zn': 0.1652,  # m5zn.large baseline
            'm6i': 0.0864,   # m6i.large baseline
            'm6a': 0.0864,   # m6a.large baseline
            'm6id': 0.1037,  # m6id.large baseline
            'm6idn': 0.1296, # m6idn.large baseline
            'm6gd': 0.0816,  # m6gd.large baseline
            'm7g': 0.0808,   # m7g.large baseline
            'm7gd': 0.0969,  # m7gd.large baseline
            'm7i': 0.1008,   # m7i.large baseline
            'm7a': 0.0864,   # m7a.large baseline
            'm8g': 0.0808,   # m8g.large baseline
            
            # Compute Optimized
            'c5': 0.085,     # c5.large baseline
            'c5a': 0.077,    # c5a.large baseline
            'c5ad': 0.086,   # c5ad.large baseline
            'c5d': 0.096,    # c5d.large baseline
            'c5n': 0.108,    # c5n.large baseline
            'c6i': 0.0765,   # c6i.large baseline
            'c6a': 0.0765,   # c6a.large baseline
            'c6id': 0.0918,  # c6id.large baseline
            'c6in': 0.0972,  # c6in.large baseline
            'c6gd': 0.0722,  # c6gd.large baseline
            'c6gn': 0.0864,  # c6gn.large baseline
            'c7g': 0.0725,   # c7g.large baseline
            'c7gd': 0.0869,  # c7gd.large baseline
            'c7gn': 0.0979,  # c7gn.large baseline
            'c7i': 0.0765,   # c7i.large baseline
            'c7a': 0.0765,   # c7a.large baseline
            'c8g': 0.0725,   # c8g.large baseline
            'c8gd': 0.0869,  # c8gd.large baseline
            'c8gn': 0.0979,  # c8gn.large baseline
            
            # Memory Optimized
            'r5': 0.126,     # r5.large baseline
            'r5a': 0.113,    # r5a.large baseline
            'r5ad': 0.129,   # r5ad.large baseline
            'r5b': 0.201,    # r5b.large baseline
            'r5d': 0.144,    # r5d.large baseline
            'r5dn': 0.162,   # r5dn.large baseline
            'r5n': 0.149,    # r5n.large baseline
            'r6i': 0.1134,   # r6i.large baseline
            'r6a': 0.1134,   # r6a.large baseline
            'r6id': 0.1361,  # r6id.large baseline
            'r6idn': 0.1620, # r6idn.large baseline
            'r6in': 0.1431,  # r6in.large baseline
            'r6g': 0.1008,   # r6g.large baseline
            'r6gd': 0.1209,  # r6gd.large baseline
            'r7g': 0.1008,   # r7g.large baseline
            'r7gd': 0.1209,  # r7gd.large baseline
            'r7i': 0.1134,   # r7i.large baseline
            'r7iz': 0.1512,  # r7iz.large baseline
            'r7a': 0.1134,   # r7a.large baseline
            'r8g': 0.1008,   # r8g.large baseline
            'r8gd': 0.1209,  # r8gd.large baseline
            'x1': 0.834,     # x1.large baseline
            'x1e': 1.668,    # x1e.large baseline
            'x2gd': 0.3336,  # x2gd.large baseline
            'x2iezn': 1.1016, # x2iezn.large baseline
            'x2iedn': 2.2032, # x2iedn.large baseline
            'x8g': 0.3336,   # x8g.large baseline
            'z1d': 0.186,    # z1d.large baseline
            
            # Storage Optimized
            'd2': 0.276,     # d2.large baseline
            'd3': 0.166,     # d3.large baseline
            'd3en': 0.251,   # d3en.large baseline
            'h1': 0.1872,    # h1.large baseline
            'i3': 0.156,     # i3.large baseline
            'i3en': 0.226,   # i3en.large baseline
            'i4i': 0.1562,   # i4i.large baseline
            'i7ie': 0.1562,  # i7ie.large baseline
            'is4gen': 0.1562, # is4gen.large baseline
            
            # Accelerated Computing
            'p2': 0.90,      # p2.large baseline
            'p3': 3.06,      # p3.large baseline
            'p3dn': 3.912,   # p3dn.large baseline
            'p4d': 3.912,    # p4d.large baseline
            'p4de': 3.912,   # p4de.large baseline
            'p5': 3.912,     # p5.large baseline
            'g3': 0.75,      # g3.large baseline
            'g4ad': 0.379,   # g4ad.large baseline
            'g4dn': 0.526,   # g4dn.large baseline
            'g5': 1.006,     # g5.large baseline
            'g5g': 0.42,     # g5g.large baseline
            'g6': 1.006,     # g6.large baseline
            'g6e': 1.152,    # g6e.large baseline
            'f1': 1.65,      # f1.large baseline
            'f2': 1.65,      # f2.large baseline
            'inf1': 0.228,   # inf1.large baseline
            'inf2': 0.228,   # inf2.large baseline
            'trn1': 1.34,    # trn1.large baseline
            'trn1n': 1.34,   # trn1n.large baseline
            'dl1': 1.30,     # dl1.large baseline
            'dl2q': 1.30,    # dl2q.large baseline
            
            # High Memory
            'u-6tb1': 109.20, # u-6tb1.large baseline
            'u-9tb1': 163.80, # u-9tb1.large baseline
            'u-12tb1': 218.40, # u-12tb1.large baseline
            'u-18tb1': 327.60, # u-18tb1.large baseline
            'u-24tb1': 436.80, # u-24tb1.large baseline
            'u7i-6tb': 109.20, # u7i-6tb.large baseline
            'u7in-6tb': 109.20, # u7in-6tb.large baseline
            
            # Mac instances
            'mac1': 1.083,   # mac1.metal baseline
            'mac2': 1.083,   # mac2.metal baseline
            'mac2-m2': 1.083, # mac2-m2.metal baseline
        }
        
        # Extract instance family (e.g., 't3' from 't3.micro', 'u7i-6tb' from 'u7i-6tb.112xlarge')
        family = instance_type.split('.')[0]
        base_price = fallback_prices.get(family)
        
        # If exact family not found, try to match partial family names
        if not base_price:
            for family_key in fallback_prices.keys():
                if family.startswith(family_key):
                    base_price = fallback_prices[family_key]
                    break
        
        if not base_price:
            return None
        
        # Adjust price based on instance size
        size_multipliers = {
            'nano': 0.125,
            'micro': 0.25,
            'small': 0.5,
            'medium': 1.0,
            'large': 2.0,
            'xlarge': 4.0,
            '2xlarge': 8.0,
            '3xlarge': 12.0,
            '4xlarge': 16.0,
            '6xlarge': 24.0,
            '8xlarge': 32.0,
            '9xlarge': 36.0,
            '10xlarge': 40.0,
            '12xlarge': 48.0,
            '16xlarge': 64.0,
            '18xlarge': 72.0,
            '24xlarge': 96.0,
            '32xlarge': 128.0,
            '48xlarge': 192.0,
            '56xlarge': 224.0,
            '112xlarge': 448.0,
            'metal': 32.0,  # Assume metal is roughly equivalent to 32xlarge
            'metal-24xl': 96.0,
            'metal-48xl': 192.0,
        }
        
        # Extract size (e.g., 'micro' from 't3.micro')
        if '.' in instance_type:
            size = instance_type.split('.')[1]
            multiplier = size_multipliers.get(size, 4.0)  # Default to 'large' equivalent
            return base_price * multiplier
        
        return base_price * 4.0  # Default to 'large' equivalent



class AWSRDSClient:
    """
    AWS RDS (Relational Database Service) client.
    
    Learning Note: RDS provides managed database services for various
    database engines like MySQL, PostgreSQL, Oracle, etc.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        self.region = region
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'rds',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('rds', region_name=region)
                # Test the credentials by making a simple call
                self.boto_client.describe_db_engine_versions(MaxRecords=20)
        except (NoCredentialsError, Exception) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Using mock RDS data.")
            self.boto_client = None
    
    async def get_database_instances(self, region: str) -> CloudServiceResponse:
        """
        Get available RDS instance types using real API data only.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with RDS instance types
            
        Raises:
            CloudServiceError: If API call fails or no database instances found
        """
        try:
            if not self.boto_client:
                raise CloudServiceError(
                    "AWS RDS API client not available. Check credentials.",
                    CloudProvider.AWS,
                    "NO_RDS_CLIENT"
                )
            
            # Use actual AWS RDS API
            response = self.boto_client.describe_orderable_db_instance_options(
                Engine='mysql',  # Focus on MySQL for simplicity
                MaxRecords=100
            )
            
            db_options = response.get('OrderableDBInstanceOptions', [])
            if not db_options:
                raise CloudServiceError(
                    f"No RDS instance options found in region {region}",
                    CloudProvider.AWS,
                    "NO_RDS_OPTIONS"
                )
            
            # Get pricing data
            pricing_client = AWSPricingClient(region)
            pricing_data = await pricing_client.get_service_pricing("AmazonRDS", region)
            pricing_lookup = self._process_rds_pricing(pricing_data.get("products", []))
            
            services = []
            seen_classes = set()
            
            for option in db_options:
                db_class = option.get('DBInstanceClass')
                if db_class and db_class not in seen_classes:
                    seen_classes.add(db_class)
                    
                    hourly_price = pricing_lookup.get(db_class)
                    if not hourly_price:
                        logger.warning(f"No pricing found for {db_class}, skipping")
                        continue
                    
                    service = CloudService(
                        provider=CloudProvider.AWS,
                        service_name=f"Amazon RDS {db_class}",
                        service_id=db_class,
                        category=ServiceCategory.DATABASE,
                        region=region,
                        description=f"RDS MySQL instance {db_class} with real-time pricing",
                        hourly_price=hourly_price,
                        specifications={
                            "engine": "mysql",
                            "engine_version": option.get('EngineVersion', '8.0'),
                            "multi_az": option.get('MultiAZCapable', False),
                            "storage_type": option.get('StorageType', 'gp2')
                        },
                        features=["automated_backups", "point_in_time_recovery", "encryption"]
                    )
                    services.append(service)
            
            if not services:
                raise CloudServiceError(
                    f"No RDS instances with pricing found in region {region}",
                    CloudProvider.AWS,
                    "NO_PRICED_RDS_INSTANCES"
                )
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,
                service_category=ServiceCategory.DATABASE,
                region=region,
                services=services,
                metadata={"real_api": True, "pricing_source": "aws_pricing_api"}
            )
                
        except CloudServiceError:
            raise
        except ClientError as e:
            raise CloudServiceError(
                f"AWS RDS API error: {str(e)}",
                CloudProvider.AWS,
                "RDS_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting RDS instances: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _process_rds_pricing(self, products: List[str]) -> Dict[str, float]:
        """Process RDS pricing data from AWS Pricing API."""
        pricing_lookup = {}
        
        for product_json in products:
            try:
                product = json.loads(product_json)
                attributes = product.get("product", {}).get("attributes", {})
                
                instance_type = attributes.get("instanceType")
                if not instance_type:
                    continue
                
                # Only process On-Demand MySQL instances
                if (attributes.get("databaseEngine") == "MySQL" and
                    attributes.get("deploymentOption") == "Single-AZ"):
                    
                    # Extract pricing from terms
                    terms = product.get("terms", {})
                    on_demand = terms.get("OnDemand", {})
                    
                    for term_key, term_data in on_demand.items():
                        price_dimensions = term_data.get("priceDimensions", {})
                        for price_key, price_data in price_dimensions.items():
                            price_per_unit = price_data.get("pricePerUnit", {}).get("USD")
                            if price_per_unit and float(price_per_unit) > 0:
                                pricing_lookup[instance_type] = float(price_per_unit)
                                break
                        if instance_type in pricing_lookup:
                            break
                    
            except Exception as e:
                logger.warning(f"Failed to process RDS pricing for product: {e}")
                continue
        
        return pricing_lookup
    

class AWSAIClient:
    """
    AWS AI/ML services client.
    
    Provides access to AWS AI and machine learning services including
    SageMaker, Bedrock, Comprehend, Rekognition, and others.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None):
        """Initialize AWS AI client."""
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.sagemaker_client = boto3.client(
                    'sagemaker',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
                self.bedrock_client = boto3.client(
                    'bedrock',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                self.sagemaker_client = boto3.client('sagemaker', region_name=region)
                self.bedrock_client = boto3.client('bedrock', region_name=region)
                
        except Exception as e:
            logger.warning(f"Failed to initialize AWS AI clients: {e}")
            self.sagemaker_client = None
            self.bedrock_client = None
    
    async def get_ai_services(self, region: str) -> CloudServiceResponse:
        """
        Get AWS AI/ML services with pricing information.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with AI/ML services
        """
        services = []
        
        # SageMaker services
        sagemaker_services = self._get_sagemaker_services(region)
        services.extend(sagemaker_services)
        
        # Bedrock services
        bedrock_services = self._get_bedrock_services(region)
        services.extend(bedrock_services)
        
        # Other AI services
        other_ai_services = self._get_other_ai_services(region)
        services.extend(other_ai_services)
        
        return CloudServiceResponse(
            provider=CloudProvider.AWS,
            service_category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            services=services,
            metadata={"ai_services_count": len(services)}
        )
    
    def _get_sagemaker_services(self, region: str) -> List[CloudService]:
        """Get SageMaker services with pricing."""
        services = []
        
        # SageMaker training instances
        training_instances = [
            {
                "instance_type": "ml.m5.large",
                "vcpus": 2,
                "memory_gb": 8,
                "hourly_price": 0.115,
                "description": "General purpose training instance"
            },
            {
                "instance_type": "ml.m5.xlarge", 
                "vcpus": 4,
                "memory_gb": 16,
                "hourly_price": 0.230,
                "description": "General purpose training instance"
            },
            {
                "instance_type": "ml.c5.xlarge",
                "vcpus": 4,
                "memory_gb": 8,
                "hourly_price": 0.204,
                "description": "Compute optimized training instance"
            },
            {
                "instance_type": "ml.p3.2xlarge",
                "vcpus": 8,
                "memory_gb": 61,
                "hourly_price": 3.825,
                "gpu_count": 1,
                "gpu_type": "V100",
                "description": "GPU training instance for deep learning"
            },
            {
                "instance_type": "ml.g4dn.xlarge",
                "vcpus": 4,
                "memory_gb": 16,
                "hourly_price": 0.736,
                "gpu_count": 1,
                "gpu_type": "T4",
                "description": "Cost-effective GPU training instance"
            }
        ]
        
        for instance in training_instances:
            service = CloudService(
                provider=CloudProvider.AWS,
                service_name=f"SageMaker Training - {instance['instance_type']}",
                service_id=f"sagemaker_training_{instance['instance_type'].replace('.', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=instance['description'],
                pricing_model="pay_as_you_go",
                hourly_price=instance['hourly_price'],
                pricing_unit="hour",
                specifications={
                    "instance_type": instance['instance_type'],
                    "vcpus": instance['vcpus'],
                    "memory_gb": instance['memory_gb'],
                    "gpu_count": instance.get('gpu_count', 0),
                    "gpu_type": instance.get('gpu_type', 'None'),
                    "use_case": "model_training"
                },
                features=["managed_training", "auto_scaling", "spot_instances", "distributed_training"]
            )
            services.append(service)
        
        # SageMaker inference endpoints
        inference_instances = [
            {
                "instance_type": "ml.t2.medium",
                "vcpus": 2,
                "memory_gb": 4,
                "hourly_price": 0.065,
                "description": "Low-cost inference endpoint"
            },
            {
                "instance_type": "ml.m5.large",
                "vcpus": 2,
                "memory_gb": 8,
                "hourly_price": 0.115,
                "description": "General purpose inference endpoint"
            },
            {
                "instance_type": "ml.c5.large",
                "vcpus": 2,
                "memory_gb": 4,
                "hourly_price": 0.102,
                "description": "Compute optimized inference endpoint"
            },
            {
                "instance_type": "ml.inf1.xlarge",
                "vcpus": 4,
                "memory_gb": 8,
                "hourly_price": 0.362,
                "description": "AWS Inferentia chip for high-performance inference"
            }
        ]
        
        for instance in inference_instances:
            service = CloudService(
                provider=CloudProvider.AWS,
                service_name=f"SageMaker Inference - {instance['instance_type']}",
                service_id=f"sagemaker_inference_{instance['instance_type'].replace('.', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=instance['description'],
                pricing_model="pay_as_you_go",
                hourly_price=instance['hourly_price'],
                pricing_unit="hour",
                specifications={
                    "instance_type": instance['instance_type'],
                    "vcpus": instance['vcpus'],
                    "memory_gb": instance['memory_gb'],
                    "use_case": "model_inference"
                },
                features=["real_time_inference", "auto_scaling", "multi_model_endpoints", "serverless_inference"]
            )
            services.append(service)
        
        return services
    
    def _get_bedrock_services(self, region: str) -> List[CloudService]:
        """Get Amazon Bedrock services with pricing."""
        services = []
        
        # Bedrock foundation models
        bedrock_models = [
            {
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "model_name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "input_price_per_1k": 0.003,
                "output_price_per_1k": 0.015,
                "description": "High-performance model for complex reasoning"
            },
            {
                "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                "model_name": "Claude 3 Haiku",
                "provider": "Anthropic", 
                "input_price_per_1k": 0.00025,
                "output_price_per_1k": 0.00125,
                "description": "Fast and cost-effective model"
            },
            {
                "model_id": "amazon.titan-text-express-v1",
                "model_name": "Titan Text Express",
                "provider": "Amazon",
                "input_price_per_1k": 0.0008,
                "output_price_per_1k": 0.0016,
                "description": "Amazon's text generation model"
            },
            {
                "model_id": "meta.llama2-70b-chat-v1",
                "model_name": "Llama 2 70B Chat",
                "provider": "Meta",
                "input_price_per_1k": 0.00195,
                "output_price_per_1k": 0.00256,
                "description": "Open-source large language model"
            },
            {
                "model_id": "stability.stable-diffusion-xl-v1",
                "model_name": "Stable Diffusion XL",
                "provider": "Stability AI",
                "price_per_image": 0.04,
                "description": "High-quality image generation model"
            }
        ]
        
        for model in bedrock_models:
            if "price_per_image" in model:
                # Image generation model
                service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"Bedrock - {model['model_name']}",
                    service_id=f"bedrock_{model['model_id'].replace('.', '_').replace(':', '_').replace('-', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=model['description'],
                    pricing_model="pay_per_use",
                    hourly_price=model['price_per_image'],
                    pricing_unit="image",
                    specifications={
                        "model_id": model['model_id'],
                        "model_provider": model['provider'],
                        "model_type": "image_generation",
                        "max_resolution": "1024x1024"
                    },
                    features=["serverless", "managed_service", "multiple_styles", "high_quality"]
                )
            else:
                # Text generation model
                service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"Bedrock - {model['model_name']}",
                    service_id=f"bedrock_{model['model_id'].replace('.', '_').replace(':', '_').replace('-', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=model['description'],
                    pricing_model="pay_per_token",
                    hourly_price=model['input_price_per_1k'],  # Using input price as base
                    pricing_unit="1K tokens",
                    specifications={
                        "model_id": model['model_id'],
                        "model_provider": model['provider'],
                        "model_type": "text_generation",
                        "input_price_per_1k_tokens": model['input_price_per_1k'],
                        "output_price_per_1k_tokens": model['output_price_per_1k']
                    },
                    features=["serverless", "managed_service", "streaming", "fine_tuning_available"]
                )
            services.append(service)
        
        return services
    
    def _get_other_ai_services(self, region: str) -> List[CloudService]:
        """Get other AWS AI services with pricing."""
        services = []
        
        # Amazon Comprehend
        comprehend_service = CloudService(
            provider=CloudProvider.AWS,
            service_name="Amazon Comprehend",
            service_id="comprehend_standard",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Natural language processing service",
            pricing_model="pay_per_request",
            hourly_price=0.0001,  # Per 100 characters
            pricing_unit="100 characters",
            specifications={
                "service_type": "nlp",
                "languages_supported": 12,
                "max_document_size": "5KB"
            },
            features=["sentiment_analysis", "entity_recognition", "key_phrase_extraction", "language_detection"]
        )
        services.append(comprehend_service)
        
        # Amazon Rekognition
        rekognition_service = CloudService(
            provider=CloudProvider.AWS,
            service_name="Amazon Rekognition",
            service_id="rekognition_standard",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Image and video analysis service",
            pricing_model="pay_per_request",
            hourly_price=0.001,  # Per image
            pricing_unit="image",
            specifications={
                "service_type": "computer_vision",
                "max_image_size": "15MB",
                "supported_formats": ["JPEG", "PNG"]
            },
            features=["object_detection", "facial_analysis", "text_in_image", "content_moderation"]
        )
        services.append(rekognition_service)
        
        # Amazon Textract
        textract_service = CloudService(
            provider=CloudProvider.AWS,
            service_name="Amazon Textract",
            service_id="textract_standard",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Document text and data extraction service",
            pricing_model="pay_per_page",
            hourly_price=0.0015,  # Per page
            pricing_unit="page",
            specifications={
                "service_type": "document_analysis",
                "max_document_size": "10MB",
                "supported_formats": ["PDF", "PNG", "JPEG", "TIFF"]
            },
            features=["text_extraction", "form_data_extraction", "table_extraction", "handwriting_recognition"]
        )
        services.append(textract_service)
        
        # Amazon Translate
        translate_service = CloudService(
            provider=CloudProvider.AWS,
            service_name="Amazon Translate",
            service_id="translate_standard",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Neural machine translation service",
            pricing_model="pay_per_character",
            hourly_price=0.000015,  # Per character
            pricing_unit="character",
            specifications={
                "service_type": "translation",
                "languages_supported": 75,
                "max_text_size": "10KB"
            },
            features=["real_time_translation", "batch_translation", "custom_terminology", "formality_settings"]
        )
        services.append(translate_service)
        
        # Amazon Polly
        polly_service = CloudService(
            provider=CloudProvider.AWS,
            service_name="Amazon Polly",
            service_id="polly_standard",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Text-to-speech service",
            pricing_model="pay_per_character",
            hourly_price=0.000004,  # Per character
            pricing_unit="character",
            specifications={
                "service_type": "text_to_speech",
                "voices_available": 60,
                "languages_supported": 29,
                "audio_formats": ["MP3", "OGG", "PCM"]
            },
            features=["neural_voices", "ssml_support", "speech_marks", "lexicons"]
        )
        services.append(polly_service)
        
        return services