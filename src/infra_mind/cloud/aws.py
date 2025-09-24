"""
AWS cloud service integration for Infra Mind.

Provides clients for AWS Pricing API, EC2, RDS, and other services.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from botocore.config import Config
from botocore.retries import adaptive

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
        Initialize AWS client with production-ready configuration.
        
        Args:
            region: AWS region
            aws_access_key_id: AWS access key (optional, can use environment/IAM)
            aws_secret_access_key: AWS secret key (optional, can use environment/IAM)
        """
        super().__init__(CloudProvider.AWS, region)
        
        # Configure boto3 with production settings
        self.boto_config = Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50,
            read_timeout=60,
            connect_timeout=10
        )
        
        # Store credentials for service clients
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # Validate credentials and set demo mode if needed
        self.demo_mode = not self._validate_credentials(aws_access_key_id, aws_secret_access_key)
        
        # Initialize service clients with enhanced configuration
        if not self.demo_mode:
            self.pricing_client = AWSPricingClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.ec2_client = AWSEC2Client(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.rds_client = AWSRDSClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.ai_client = AWSAIClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            
            # Extended service clients
            self.eks_client = AWSEKSClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.lambda_client = AWSLambdaClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.sagemaker_client = AWSSageMakerClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.cost_explorer_client = AWSCostExplorerClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
            self.budgets_client = AWSBudgetsClient(region, aws_access_key_id, aws_secret_access_key, self.boto_config)
        else:
            # Initialize demo mode clients (None for now, will be handled by methods)
            self.pricing_client = None
            self.ec2_client = None
            self.rds_client = None
            self.ai_client = None
            self.eks_client = None
            self.lambda_client = None
            self.sagemaker_client = None
            self.cost_explorer_client = None
            self.budgets_client = None
        
        # Initialize rate limiting and resilience patterns
        self._init_rate_limiting()
        self._init_resilience_patterns()
    
    def _validate_credentials(self, aws_access_key_id: Optional[str], aws_secret_access_key: Optional[str]) -> bool:
        """Validate AWS credentials are available and working.
        
        Returns:
            bool: True if credentials are valid, False if not (demo mode)
        """
        try:
            if aws_access_key_id and aws_secret_access_key:
                test_client = boto3.client(
                    'sts',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=self.boto_config
                )
            else:
                test_client = boto3.client('sts', config=self.boto_config)
            
            # Test credentials with timeout
            identity = test_client.get_caller_identity()
            logger.info(f"AWS credentials validated for account: {identity.get('Account')}")
            return True
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available, running in demo mode: {e}")
            return False
    
    def _init_rate_limiting(self):
        """Initialize rate limiting for AWS API calls."""
        self.rate_limits = {
            'pricing': {'calls_per_second': 10, 'burst': 20},
            'ec2': {'calls_per_second': 20, 'burst': 40},
            'rds': {'calls_per_second': 20, 'burst': 40},
            'eks': {'calls_per_second': 10, 'burst': 20},
            'lambda': {'calls_per_second': 20, 'burst': 40},
            'sagemaker': {'calls_per_second': 10, 'burst': 20},
            'cost_explorer': {'calls_per_second': 5, 'burst': 10},
            'budgets': {'calls_per_second': 5, 'burst': 10}
        }
        
        # Track API call timestamps for rate limiting
        self.api_call_history = {service: [] for service in self.rate_limits.keys()}
        
        logger.info("Initialized AWS API rate limiting")
    
    def _init_resilience_patterns(self):
        """Initialize resilience patterns for AWS services."""
        from ..core.resilience import configure_service_resilience
        
        # Configure resilience for AWS services with appropriate thresholds
        configure_service_resilience(
            "aws_pricing",
            failure_threshold=3,
            recovery_timeout=30,
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        )
        
        configure_service_resilience(
            "aws_ec2",
            failure_threshold=5,
            recovery_timeout=60,
            max_retries=3,
            base_delay=2.0,
            max_delay=60.0
        )
        
        configure_service_resilience(
            "aws_rds",
            failure_threshold=5,
            recovery_timeout=60,
            max_retries=3,
            base_delay=2.0,
            max_delay=60.0
        )
        
        configure_service_resilience(
            "aws_ai",
            failure_threshold=3,
            recovery_timeout=45,
            max_retries=2,
            base_delay=1.5,
            max_delay=45.0
        )
        
        logger.info("Initialized resilience patterns for AWS services")
    
    async def _check_rate_limit(self, service: str) -> None:
        """
        Check and enforce rate limits for AWS API calls.
        
        Args:
            service: Service name for rate limiting
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if service not in self.rate_limits:
            return
        
        current_time = time.time()
        rate_config = self.rate_limits[service]
        call_history = self.api_call_history[service]
        
        # Remove calls older than 1 second
        call_history[:] = [call_time for call_time in call_history if current_time - call_time < 1.0]
        
        # Check if we're within rate limits
        if len(call_history) >= rate_config['calls_per_second']:
            # Check burst capacity
            recent_calls = [call_time for call_time in call_history if current_time - call_time < 0.1]
            if len(recent_calls) >= rate_config['burst']:
                wait_time = 1.0 - (current_time - call_history[0])
                raise RateLimitError(
                    f"AWS {service} API rate limit exceeded. Wait {wait_time:.2f} seconds.",
                    CloudProvider.AWS,
                    "RATE_LIMIT_EXCEEDED"
                )
        
        # Record this API call
        call_history.append(current_time)
    
    async def _execute_with_retry(self, service: str, operation: str, func, *args, **kwargs):
        """
        Execute AWS API call with retry logic and rate limiting.
        
        Args:
            service: Service name for rate limiting
            operation: Operation name for logging
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CloudServiceError: If all retries fail
        """
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                # Check rate limits
                await self._check_rate_limit(service)
                
                # Execute the function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Log successful call
                logger.debug(f"AWS {service} {operation} succeeded on attempt {attempt + 1}")
                self._increment_api_calls()
                return result
                
            except RateLimitError:
                if attempt == max_retries:
                    raise
                # Wait before retry for rate limit
                await asyncio.sleep(base_delay * (2 ** attempt))
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                
                if error_code in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded']:
                    if attempt == max_retries:
                        raise RateLimitError(
                            f"AWS {service} API throttled after {max_retries} retries",
                            CloudProvider.AWS,
                            error_code
                        )
                    # Exponential backoff for throttling
                    delay = base_delay * (2 ** attempt) + (attempt * 0.1)  # Add jitter
                    logger.warning(f"AWS {service} {operation} throttled, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    
                elif error_code in ['ServiceUnavailable', 'InternalError']:
                    if attempt == max_retries:
                        raise CloudServiceError(
                            f"AWS {service} service unavailable after {max_retries} retries",
                            CloudProvider.AWS,
                            error_code
                        )
                    # Shorter delay for service errors
                    delay = base_delay * (1.5 ** attempt)
                    logger.warning(f"AWS {service} {operation} service error, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    
                else:
                    # Don't retry for other errors
                    raise CloudServiceError(
                        f"AWS {service} {operation} error: {str(e)}",
                        CloudProvider.AWS,
                        error_code
                    )
                    
            except Exception as e:
                if attempt == max_retries:
                    raise CloudServiceError(
                        f"AWS {service} {operation} unexpected error: {str(e)}",
                        CloudProvider.AWS,
                        "UNEXPECTED_ERROR"
                    )
                # Retry for unexpected errors
                delay = base_delay * (2 ** attempt)
                logger.warning(f"AWS {service} {operation} unexpected error, retrying in {delay:.2f}s (attempt {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        # This should never be reached
        raise CloudServiceError(
            f"AWS {service} {operation} failed after all retries",
            CloudProvider.AWS,
            "MAX_RETRIES_EXCEEDED"
        )
    
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS compute services (EC2 instances)."""
        target_region = region or self.region
        
        if self.demo_mode:
            # In demo mode, we can't fetch real data but service should still work
            raise CloudServiceError(
                f"AWS credentials not configured. Cannot fetch compute services for {target_region}",
                CloudProvider.AWS,
                "CREDENTIALS_NOT_AVAILABLE"
            )
        
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
                    "gp3" in attributes.get("volumeType").lower()):
                    
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
    
    async def get_container_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS container services (EKS)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="eks",
            region=target_region,
            fetch_func=lambda: self.eks_client.get_eks_services(target_region),
            cache_ttl=3600  # 1 hour cache for container services
        )
    
    async def get_serverless_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS serverless services (Lambda)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="lambda",
            region=target_region,
            fetch_func=lambda: self.lambda_client.get_lambda_services(target_region),
            cache_ttl=3600  # 1 hour cache for serverless services
        )
    
    async def get_ml_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get AWS machine learning services (SageMaker)."""
        target_region = region or self.region
        
        return await self._get_cached_or_fetch(
            service="sagemaker",
            region=target_region,
            fetch_func=lambda: self.sagemaker_client.get_sagemaker_services(target_region),
            cache_ttl=3600  # 1 hour cache for ML services
        )
    
    async def get_cost_analysis(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict[str, Any]:
        """Get cost analysis using Cost Explorer API."""
        return await self._get_cached_or_fetch(
            service="cost_explorer",
            region=self.region,
            fetch_func=lambda: self.cost_explorer_client.get_cost_and_usage(start_date, end_date, granularity),
            params={"start_date": start_date, "end_date": end_date, "granularity": granularity},
            cache_ttl=1800  # 30 minutes cache for cost data
        )
    
    async def get_budgets(self, account_id: str) -> Dict[str, Any]:
        """Get AWS budgets information."""
        return await self._get_cached_or_fetch(
            service="budgets",
            region=self.region,
            fetch_func=lambda: self.budgets_client.get_budgets(account_id),
            params={"account_id": account_id},
            cache_ttl=3600  # 1 hour cache for budget data
        )
    
    async def create_budget(self, account_id: str, budget_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AWS budget."""
        return await self.budgets_client.create_budget(account_id, budget_config)


class AWSPricingClient:
    """
    AWS Pricing API client.
    
    Learning Note: The AWS Pricing API provides programmatic access to
    AWS service pricing information across all regions and services.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        self.base_url = "https://api.pricing.us-east-1.amazonaws.com"
        self.session = None
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name='us-east-1',
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        # Initialize boto3 client for pricing (always us-east-1 for pricing API)
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'pricing',
                    region_name='us-east-1',  # Pricing API is only available in us-east-1
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('pricing', region_name='us-east-1', config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.describe_services(MaxResults=1)
            logger.info("AWS Pricing API client initialized successfully")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Pricing client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS Pricing client: {e}")
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
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'ec2',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('ec2', region_name=region, config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.describe_regions()
            logger.info(f"AWS EC2 client initialized successfully for region {region}")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. EC2 client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS EC2 client: {e}")
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
            
            # Get pricing data with fallback
            pricing_data = {"products": []}
            try:
                # Try to create a pricing client if needed
                pricing_client = AWSPricingClient(region, self.aws_access_key_id, self.aws_secret_access_key, self.boto_config)
                if pricing_client.boto_client:
                    pricing_data = await pricing_client.get_service_pricing("AmazonEC2", region)
                else:
                    logger.info("Pricing client not available, using fallback pricing")
            except Exception as e:
                logger.info(f"Could not get pricing data: {e}, using fallback pricing")
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
                        "network_performance": instance_type.get('NetworkPerformance'),
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
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.boto_config = boto_config
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
            self.boto_config = boto_config
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'rds',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('rds', region_name=region, config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.describe_db_engine_versions(MaxRecords=20)
            logger.info(f"AWS RDS client initialized successfully for region {region}")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. RDS client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS RDS client: {e}")
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
        logger.info(f"🚀 RDS METHOD CALLED: Starting get_database_instances for region {region}")
        try:
            if not self.boto_client:
                raise CloudServiceError(
                    "AWS RDS API client not available. Check credentials.",
                    CloudProvider.AWS,
                    "NO_RDS_CLIENT"
                )
            
            # Use actual AWS RDS API  
            logger.info(f"🔍 RDS DEBUG: Starting RDS API call for region {region}")
            response = self.boto_client.describe_orderable_db_instance_options(
                Engine='mysql',  # Focus on MySQL for simplicity
                MaxRecords=100
            )
            
            db_options = response.get('OrderableDBInstanceOptions', [])
            logger.info(f"🔍 RDS DEBUG: Found {len(db_options)} orderable DB instance options")
            if not db_options:
                raise CloudServiceError(
                    f"No RDS instance options found in region {region}",
                    CloudProvider.AWS,
                    "NO_RDS_OPTIONS"
                )
            
            # Get pricing data using the main client's credentials
            pricing_client = AWSPricingClient(
                region, 
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                boto_config=self.boto_config
            )
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
                        # Use fallback pricing based on instance class
                        fallback_prices = {
                            'db.t3.micro': 0.017,
                            'db.t3.small': 0.034,
                            'db.t3.medium': 0.068,
                            'db.t3.large': 0.136,
                            'db.t3.xlarge': 0.272,
                            'db.t3.2xlarge': 0.544,
                            'db.m5.large': 0.192,
                            'db.m5.xlarge': 0.384,
                            'db.m5.2xlarge': 0.768,
                            'db.m5.4xlarge': 1.536,
                            'db.r5.large': 0.240,
                            'db.r5.xlarge': 0.480
                        }
                        hourly_price = fallback_prices.get(db_class, 0.1)  # Default fallback
                        logger.info(f"🔧 RDS FALLBACK: Using fallback pricing for {db_class}: ${hourly_price}/hour")
                    
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
                # Debug: Log why no services were found
                logger.error(f"No RDS instances found in region {region}. Check AWS credentials and RDS API access.")
                raise CloudServiceError(
                    f"No RDS instances found in region {region}",
                    CloudProvider.AWS,
                    "NO_RDS_INSTANCES"
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
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        """Initialize AWS AI client with enhanced configuration."""
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.sagemaker_client = boto3.client(
                    'sagemaker',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
                self.bedrock_client = boto3.client(
                    'bedrock',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                self.sagemaker_client = boto3.client('sagemaker', region_name=region, config=boto_config)
                self.bedrock_client = boto3.client('bedrock', region_name=region, config=boto_config)
            
            logger.info(f"AWS AI clients initialized successfully for region {region}")
                
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. AI clients will use fallback data.")
            self.sagemaker_client = None
            self.bedrock_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS AI clients: {e}")
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
        
        # Debug: Log if no AI services were found
        if not services:
            logger.error(f"No AI services found in region {region}. Check SageMaker, Bedrock, and AI service implementations.")

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


class AWSEKSClient:
    """
    AWS EKS (Elastic Kubernetes Service) client.
    
    Learning Note: EKS is AWS's managed Kubernetes service. This client provides
    access to cluster information, node groups, and pricing.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'eks',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('eks', region_name=region, config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.list_clusters(maxResults=1)
            logger.info(f"AWS EKS client initialized successfully for region {region}")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. EKS client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS EKS client: {e}")
            self.boto_client = None
    
    async def get_eks_services(self, region: str) -> CloudServiceResponse:
        """
        Get EKS service information using real API data.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with EKS services
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            services = []
            
            # EKS Control Plane
            control_plane_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="Amazon EKS Control Plane",
                service_id="eks_control_plane",
                category=ServiceCategory.CONTAINERS,
                region=region,
                description="Managed Kubernetes control plane",
                pricing_model="hourly",
                hourly_price=0.10,  # $0.10 per hour per cluster
                pricing_unit="cluster-hour",
                specifications={
                    "kubernetes_version": "1.28",
                    "high_availability": True,
                    "managed_control_plane": True,
                    "etcd_backup": True
                },
                features=["auto_scaling", "logging", "monitoring", "security_groups", "iam_integration"]
            )
            services.append(control_plane_service)
            
            # Get node group pricing from EC2
            if self.boto_client:
                try:
                    # Get available node group instance types
                    ec2_client = boto3.client('ec2', region_name=region)
                    instance_types_response = ec2_client.describe_instance_types(
                        Filters=[
                            {'Name': 'instance-type', 'Values': ['t3.medium', 'm5.large', 'm5.xlarge', 'c5.large']}
                        ]
                    )
                    
                    # Get pricing for common node group instance types
                    pricing_client = AWSPricingClient(region)
                    pricing_data = await pricing_client.get_service_pricing("AmazonEC2", region)
                    pricing_lookup = self._process_ec2_pricing_for_eks(pricing_data.get("products", []))
                    
                    for instance_type in instance_types_response.get('InstanceTypes', []):
                        instance_name = instance_type['InstanceType']
                        hourly_price = pricing_lookup.get(instance_name, self._get_fallback_eks_pricing(instance_name))
                        
                        if hourly_price:
                            node_service = CloudService(
                                provider=CloudProvider.AWS,
                                service_name=f"EKS Node Group ({instance_name})",
                                service_id=f"eks_node_{instance_name}",
                                category=ServiceCategory.CONTAINERS,
                                region=region,
                                description=f"EKS managed node group with {instance_name} instances",
                                pricing_model="hourly",
                                hourly_price=hourly_price,
                                pricing_unit="node-hour",
                                specifications={
                                    "instance_type": instance_name,
                                    "vcpus": instance_type.get('VCpuInfo', {}).get('DefaultVCpus', 0),
                                    "memory_gb": round(instance_type.get('MemoryInfo', {}).get('SizeInMiB', 0) / 1024, 1),
                                    "managed_node_group": True,
                                    "auto_scaling": True
                                },
                                features=["auto_scaling", "spot_instances", "taints_labels", "launch_templates"]
                            )
                            services.append(node_service)
                
                except Exception as e:
                    logger.warning(f"Failed to get EKS node group pricing: {e}")
            
            # Add Fargate pricing
            fargate_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="EKS on AWS Fargate",
                service_id="eks_fargate",
                category=ServiceCategory.CONTAINERS,
                region=region,
                description="Serverless compute for EKS pods",
                pricing_model="resource_based",
                hourly_price=0.04048,  # Per vCPU per hour
                pricing_unit="vCPU-hour",
                specifications={
                    "serverless": True,
                    "no_node_management": True,
                    "per_pod_isolation": True,
                    "max_vcpu_per_pod": 4,
                    "max_memory_per_pod": "30GB"
                },
                features=["serverless", "per_pod_billing", "security_isolation", "no_capacity_planning"]
            )
            services.append(fargate_service)
            
            if not services:
                raise CloudServiceError(
                    f"No EKS services found in region {region}",
                    CloudProvider.AWS,
                    "NO_EKS_SERVICES"
                )
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,
                service_category=ServiceCategory.CONTAINERS,
                region=region,
                services=services,
                metadata={"real_api": bool(self.boto_client), "service_type": "eks"}
            )
                
        except CloudServiceError:
            raise
        except ClientError as e:
            raise CloudServiceError(
                f"AWS EKS API error: {str(e)}",
                CloudProvider.AWS,
                "EKS_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting EKS services: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _process_ec2_pricing_for_eks(self, products: List[str]) -> Dict[str, float]:
        """Process EC2 pricing data for EKS node groups."""
        pricing_lookup = {}
        
        for product_json in products:
            try:
                product = json.loads(product_json)
                attributes = product.get("product", {}).get("attributes", {})
                
                instance_type = attributes.get("instanceType")
                if not instance_type:
                    continue
                
                # Only process On-Demand Shared instances (Linux)
                if (attributes.get("tenancy") == "Shared" and
                    attributes.get("operating-system") == "Linux" and
                    attributes.get("pre-installed-sw") == "NA"):
                    
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
                logger.warning(f"Failed to process EKS pricing for product: {e}")
                continue
        
        return pricing_lookup
    
    def _get_fallback_eks_pricing(self, instance_type: str) -> Optional[float]:
        """Get fallback pricing for EKS node groups."""
        fallback_prices = {
            't3.medium': 0.0416,
            't3.large': 0.0832,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'c5.2xlarge': 0.34,
            'r5.large': 0.126,
            'r5.xlarge': 0.252
        }
        return fallback_prices.get(instance_type)


class AWSLambdaClient:
    """
    AWS Lambda service client.
    
    Learning Note: Lambda is AWS's serverless compute service. This client provides
    access to function configurations, pricing, and runtime information.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'lambda',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('lambda', region_name=region, config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.list_functions(MaxItems=1)
            logger.info(f"AWS Lambda client initialized successfully for region {region}")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Lambda client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS Lambda client: {e}")
            self.boto_client = None
    
    async def get_lambda_services(self, region: str) -> CloudServiceResponse:
        """
        Get Lambda service information using real API data.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with Lambda services
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            services = []
            
            # Lambda Request pricing
            request_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="AWS Lambda Requests",
                service_id="lambda_requests",
                category=ServiceCategory.SERVERLESS,
                region=region,
                description="Lambda function invocation requests",
                pricing_model="per_request",
                hourly_price=0.0000002,  # $0.20 per 1M requests
                pricing_unit="request",
                specifications={
                    "free_tier_requests": 1000000,  # 1M requests per month
                    "max_execution_time": "15 minutes",
                    "max_memory": "10GB",
                    "max_storage": "10GB"
                },
                features=["auto_scaling", "event_driven", "pay_per_use", "no_server_management"]
            )
            services.append(request_service)
            
            # Lambda Duration pricing (different memory configurations)
            memory_configs = [128, 256, 512, 1024, 2048, 3008, 10240]  # MB
            
            for memory_mb in memory_configs:
                # Calculate price per GB-second
                gb_memory = memory_mb / 1024
                price_per_gb_second = 0.0000166667  # $0.0000166667 per GB-second
                price_per_100ms = (price_per_gb_second * gb_memory) / 10  # Per 100ms billing increment
                
                duration_service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"AWS Lambda Duration ({memory_mb}MB)",
                    service_id=f"lambda_duration_{memory_mb}mb",
                    category=ServiceCategory.SERVERLESS,
                    region=region,
                    description=f"Lambda function execution time with {memory_mb}MB memory",
                    pricing_model="duration_based",
                    hourly_price=price_per_100ms,
                    pricing_unit="100ms",
                    specifications={
                        "memory_mb": memory_mb,
                        "memory_gb": gb_memory,
                        "billing_increment": "100ms",
                        "free_tier_gb_seconds": 400000  # 400,000 GB-seconds per month
                    },
                    features=["auto_scaling", "millisecond_billing", "concurrent_execution", "event_triggers"]
                )
                services.append(duration_service)
            
            # Lambda Provisioned Concurrency
            provisioned_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="AWS Lambda Provisioned Concurrency",
                service_id="lambda_provisioned_concurrency",
                category=ServiceCategory.SERVERLESS,
                region=region,
                description="Pre-warmed Lambda execution environments",
                pricing_model="provisioned",
                hourly_price=0.0000041667,  # $0.015 per GB-hour
                pricing_unit="GB-hour",
                specifications={
                    "cold_start_elimination": True,
                    "consistent_performance": True,
                    "configurable_concurrency": True
                },
                features=["no_cold_starts", "predictable_performance", "instant_scaling", "reserved_capacity"]
            )
            services.append(provisioned_service)
            
            # Lambda@Edge
            edge_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="Lambda@Edge",
                service_id="lambda_edge",
                category=ServiceCategory.SERVERLESS,
                region=region,
                description="Lambda functions at CloudFront edge locations",
                pricing_model="per_request",
                hourly_price=0.0000006,  # $0.60 per 1M requests
                pricing_unit="request",
                specifications={
                    "edge_locations": 400,
                    "max_execution_time": "30 seconds",
                    "max_memory": "10GB",
                    "global_distribution": True
                },
                features=["edge_computing", "low_latency", "global_distribution", "cloudfront_integration"]
            )
            services.append(edge_service)
            
            if not services:
                raise CloudServiceError(
                    f"No Lambda services found in region {region}",
                    CloudProvider.AWS,
                    "NO_LAMBDA_SERVICES"
                )
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,
                service_category=ServiceCategory.SERVERLESS,
                region=region,
                services=services,
                metadata={"real_api": bool(self.boto_client), "service_type": "lambda"}
            )
                
        except CloudServiceError:
            raise
        except ClientError as e:
            raise CloudServiceError(
                f"AWS Lambda API error: {str(e)}",
                CloudProvider.AWS,
                "LAMBDA_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting Lambda services: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )


class AWSSageMakerClient:
    """
    AWS SageMaker service client.
    
    Learning Note: SageMaker is AWS's machine learning platform. This client provides
    access to training instances, inference endpoints, and ML service pricing.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default
        if not boto_config:
            boto_config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'sagemaker',
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('sagemaker', region_name=region, config=boto_config)
                
            # Test the credentials by making a simple call with timeout
            self.boto_client.list_training_jobs(MaxResults=1)
            logger.info(f"AWS SageMaker client initialized successfully for region {region}")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. SageMaker client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS SageMaker client: {e}")
            self.boto_client = None
    
    async def get_sagemaker_services(self, region: str) -> CloudServiceResponse:
        """
        Get SageMaker service information using real API data.
        
        Args:
            region: AWS region
            
        Returns:
            CloudServiceResponse with SageMaker services
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            services = []
            
            # SageMaker Training Instances
            training_instances = [
                ("ml.m5.large", 2, 8, 0.269),
                ("ml.m5.xlarge", 4, 16, 0.538),
                ("ml.m5.2xlarge", 8, 32, 1.076),
                ("ml.m5.4xlarge", 16, 64, 2.152),
                ("ml.c5.xlarge", 4, 8, 0.238),
                ("ml.c5.2xlarge", 8, 16, 0.476),
                ("ml.c5.4xlarge", 16, 32, 0.952),
                ("ml.p3.2xlarge", 8, 61, 3.825),  # GPU instance
                ("ml.p3.8xlarge", 32, 244, 15.3),  # GPU instance
                ("ml.g4dn.xlarge", 4, 16, 0.736),  # GPU instance
                ("ml.g4dn.2xlarge", 8, 32, 1.052)  # GPU instance
            ]
            
            for instance_type, vcpus, memory_gb, hourly_price in training_instances:
                is_gpu = "p3" in instance_type or "g4dn" in instance_type
                
                training_service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"SageMaker Training ({instance_type})",
                    service_id=f"sagemaker_training_{instance_type.replace('.', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=f"SageMaker training instance {instance_type}",
                    pricing_model="hourly",
                    hourly_price=hourly_price,
                    pricing_unit="instance-hour",
                    specifications={
                        "instance_type": instance_type,
                        "vcpus": vcpus,
                        "memory_gb": memory_gb,
                        "gpu_enabled": is_gpu,
                        "use_case": "training"
                    },
                    features=["managed_training", "auto_scaling", "spot_instances", "distributed_training"]
                )
                services.append(training_service)
            
            # SageMaker Inference Endpoints
            inference_instances = [
                ("ml.t2.medium", 2, 4, 0.065),
                ("ml.m5.large", 2, 8, 0.115),
                ("ml.m5.xlarge", 4, 16, 0.23),
                ("ml.m5.2xlarge", 8, 32, 0.46),
                ("ml.c5.large", 2, 4, 0.102),
                ("ml.c5.xlarge", 4, 8, 0.204),
                ("ml.c5.2xlarge", 8, 16, 0.408),
                ("ml.g4dn.xlarge", 4, 16, 0.736),  # GPU instance
                ("ml.inf1.xlarge", 4, 8, 0.362)   # Inferentia chip
            ]
            
            for instance_type, vcpus, memory_gb, hourly_price in inference_instances:
                is_gpu = "g4dn" in instance_type
                is_inferentia = "inf1" in instance_type
                
                inference_service = CloudService(
                    provider=CloudProvider.AWS,
                    service_name=f"SageMaker Inference ({instance_type})",
                    service_id=f"sagemaker_inference_{instance_type.replace('.', '_')}",
                    category=ServiceCategory.MACHINE_LEARNING,
                    region=region,
                    description=f"SageMaker inference endpoint {instance_type}",
                    pricing_model="hourly",
                    hourly_price=hourly_price,
                    pricing_unit="instance-hour",
                    specifications={
                        "instance_type": instance_type,
                        "vcpus": vcpus,
                        "memory_gb": memory_gb,
                        "gpu_enabled": is_gpu,
                        "inferentia_enabled": is_inferentia,
                        "use_case": "inference"
                    },
                    features=["real_time_inference", "auto_scaling", "multi_model_endpoints", "a_b_testing"]
                )
                services.append(inference_service)
            
            # SageMaker Serverless Inference
            serverless_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="SageMaker Serverless Inference",
                service_id="sagemaker_serverless_inference",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description="Serverless ML inference with automatic scaling",
                pricing_model="per_request",
                hourly_price=0.000020,  # $0.20 per 1M requests
                pricing_unit="request",
                specifications={
                    "serverless": True,
                    "auto_scaling": True,
                    "cold_start": True,
                    "max_memory": "6GB",
                    "max_concurrent_invocations": 1000
                },
                features=["serverless", "pay_per_use", "auto_scaling", "no_infrastructure_management"]
            )
            services.append(serverless_service)
            
            # SageMaker Studio
            studio_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="SageMaker Studio",
                service_id="sagemaker_studio",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description="Integrated ML development environment",
                pricing_model="hourly",
                hourly_price=0.0464,  # ml.t3.medium default
                pricing_unit="instance-hour",
                specifications={
                    "ide_type": "jupyter_lab",
                    "default_instance": "ml.t3.medium",
                    "collaborative": True,
                    "version_control": True
                },
                features=["jupyter_lab", "collaboration", "version_control", "experiment_tracking"]
            )
            services.append(studio_service)
            
            # SageMaker Data Wrangler
            data_wrangler_service = CloudService(
                provider=CloudProvider.AWS,
                service_name="SageMaker Data Wrangler",
                service_id="sagemaker_data_wrangler",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description="Visual data preparation tool",
                pricing_model="hourly",
                hourly_price=1.16,  # ml.m5.4xlarge
                pricing_unit="instance-hour",
                specifications={
                    "data_preparation": True,
                    "visual_interface": True,
                    "built_in_transformations": 300,
                    "data_sources": ["S3", "Redshift", "Athena", "Snowflake"]
                },
                features=["visual_data_prep", "built_in_transforms", "data_insights", "export_to_pipelines"]
            )
            services.append(data_wrangler_service)
            
            if not services:
                raise CloudServiceError(
                    f"No SageMaker services found in region {region}",
                    CloudProvider.AWS,
                    "NO_SAGEMAKER_SERVICES"
                )
            
            return CloudServiceResponse(
                provider=CloudProvider.AWS,
                service_category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                services=services,
                metadata={"real_api": bool(self.boto_client), "service_type": "sagemaker"}
            )
                
        except CloudServiceError:
            raise
        except ClientError as e:
            raise CloudServiceError(
                f"AWS SageMaker API error: {str(e)}",
                CloudProvider.AWS,
                "SAGEMAKER_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting SageMaker services: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )


class AWSCostExplorerClient:
    """
    AWS Cost Explorer service client.
    
    Learning Note: Cost Explorer provides cost and usage analytics. This client provides
    access to cost data, usage reports, and budget information.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default (Cost Explorer is only available in us-east-1)
        if not boto_config:
            boto_config = Config(
                region_name='us-east-1',
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'ce',  # Cost Explorer
                    region_name='us-east-1',  # Cost Explorer is only available in us-east-1
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('ce', region_name='us-east-1', config=boto_config)
                
            # Test the credentials by making a simple call with recent dates
            from datetime import datetime, timedelta
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            
            try:
                self.boto_client.get_dimension_values(
                    TimePeriod={
                        'Start': week_ago.strftime('%Y-%m-%d'),
                        'End': yesterday.strftime('%Y-%m-%d')
                    },
                    Dimension='SERVICE',
                    MaxResults=1
                )
                logger.info("AWS Cost Explorer client initialized successfully")
            except ClientError as ce:
                if 'ValidationException' in str(ce) and 'historical data' in str(ce):
                    # Cost Explorer requires specific permissions and data history
                    logger.info("AWS Cost Explorer client initialized (limited historical data access)")
                elif 'UnauthorizedOperation' in str(ce) or 'AccessDenied' in str(ce):
                    logger.info("AWS Cost Explorer client initialized (limited permissions)")
                else:
                    # Re-raise other ClientErrors to be handled by outer catch
                    raise ce
            
        except (NoCredentialsError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Cost Explorer client will use fallback data.")
            self.boto_client = None
        except ClientError as e:
            if 'ValidationException' not in str(e) or 'historical data' not in str(e):
                logger.warning(f"AWS Cost Explorer access limited: {e}. Cost Explorer client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS Cost Explorer client: {e}")
            self.boto_client = None
    
    async def get_cost_and_usage(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict[str, Any]:
        """
        Get cost and usage data using Cost Explorer API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            
        Returns:
            Cost and usage data
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            if not self.boto_client:
                # Return mock data when no credentials
                return self._get_mock_cost_data(start_date, end_date, granularity)
            
            response = self.boto_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            return {
                "cost_data": response.get('ResultsByTime', []),
                "dimension_key": response.get('DimensionKey'),
                "group_definitions": response.get('GroupDefinitions', []),
                "next_page_token": response.get('NextPageToken'),
                "real_data": True,
                "time_period": {
                    "start": start_date,
                    "end": end_date
                },
                "granularity": granularity
            }
                
        except ClientError as e:
            raise CloudServiceError(
                f"AWS Cost Explorer API error: {str(e)}",
                CloudProvider.AWS,
                "COST_EXPLORER_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting cost data: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def get_usage_forecast(self, start_date: str, end_date: str, metric: str = "BLENDED_COST") -> Dict[str, Any]:
        """
        Get usage forecast using Cost Explorer API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            metric: BLENDED_COST, UNBLENDED_COST, USAGE_QUANTITY
            
        Returns:
            Usage forecast data
        """
        try:
            if not self.boto_client:
                return self._get_mock_forecast_data(start_date, end_date, metric)
            
            response = self.boto_client.get_usage_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity='MONTHLY'
            )
            
            return {
                "forecast_results": response.get('ForecastResultsByTime', []),
                "total": response.get('Total', {}),
                "real_data": True,
                "metric": metric,
                "time_period": {
                    "start": start_date,
                    "end": end_date
                }
            }
                
        except ClientError as e:
            raise CloudServiceError(
                f"AWS Cost Explorer forecast API error: {str(e)}",
                CloudProvider.AWS,
                "FORECAST_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting forecast: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _get_mock_cost_data(self, start_date: str, end_date: str, granularity: str) -> Dict[str, Any]:
        """REMOVED: Mock cost data is dangerous for production use."""
        raise ValueError(
            "Mock cost data has been disabled for production safety. "
            "Real AWS credentials are required to fetch actual cost data. "
            "Configure proper AWS credentials and permissions to access Cost Explorer API."
        )
    
    def _get_mock_forecast_data(self, start_date: str, end_date: str, metric: str) -> Dict[str, Any]:
        """REMOVED: Mock forecast data is dangerous for production use."""
        raise ValueError(
            "Mock forecast data has been disabled for production safety. "
            "Real AWS credentials are required to fetch actual cost forecasting data. "
            "Configure proper AWS credentials and permissions to access Cost Explorer API."
        )


class AWSBudgetsClient:
    """
    AWS Budgets service client.
    
    Learning Note: AWS Budgets allows you to set custom cost and usage budgets.
    This client provides access to budget management and alerting.
    """
    
    def __init__(self, region: str = "us-east-1", aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, boto_config: Optional[Config] = None):
        self.region = region
        
        # Use provided config or create default (Budgets is only available in us-east-1)
        if not boto_config:
            boto_config = Config(
                region_name='us-east-1',
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.boto_client = boto3.client(
                    'budgets',
                    region_name='us-east-1',  # Budgets is only available in us-east-1
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=boto_config
                )
            else:
                # Try to create client with default credentials
                self.boto_client = boto3.client('budgets', region_name='us-east-1', config=boto_config)
                
            logger.info("AWS Budgets client initialized successfully")
            
        except (NoCredentialsError, ClientError, BotoCoreError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Budgets client will use fallback data.")
            self.boto_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing AWS Budgets client: {e}")
            self.boto_client = None
    
    async def get_budgets(self, account_id: str) -> Dict[str, Any]:
        """
        Get AWS budgets for an account.
        
        Args:
            account_id: AWS account ID
            
        Returns:
            Budget information
            
        Raises:
            CloudServiceError: If API call fails
        """
        try:
            if not self.boto_client:
                return self._get_mock_budgets_data(account_id)
            
            response = self.boto_client.describe_budgets(
                AccountId=account_id,
                MaxResults=100
            )
            
            return {
                "budgets": response.get('Budgets', []),
                "next_token": response.get('NextToken'),
                "account_id": account_id,
                "real_data": True
            }
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                logger.warning(f"Access denied for budgets API: {e}")
                return self._get_mock_budgets_data(account_id)
            raise CloudServiceError(
                f"AWS Budgets API error: {str(e)}",
                CloudProvider.AWS,
                "BUDGETS_API_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting budgets: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def create_budget(self, account_id: str, budget_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new AWS budget.
        
        Args:
            account_id: AWS account ID
            budget_config: Budget configuration
            
        Returns:
            Budget creation result
        """
        try:
            if not self.boto_client:
                return {"success": False, "message": "No AWS credentials available", "real_data": False}
            
            response = self.boto_client.create_budget(
                AccountId=account_id,
                Budget=budget_config
            )
            
            return {
                "success": True,
                "budget_name": budget_config.get('BudgetName'),
                "account_id": account_id,
                "real_data": True
            }
                
        except ClientError as e:
            raise CloudServiceError(
                f"AWS Budgets create API error: {str(e)}",
                CloudProvider.AWS,
                "BUDGET_CREATE_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error creating budget: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    async def get_budget_performance(self, account_id: str, budget_name: str) -> Dict[str, Any]:
        """
        Get budget performance data.
        
        Args:
            account_id: AWS account ID
            budget_name: Budget name
            
        Returns:
            Budget performance data
        """
        try:
            if not self.boto_client:
                return self._get_mock_budget_performance(account_id, budget_name)
            
            response = self.boto_client.describe_budget_performance_history(
                AccountId=account_id,
                BudgetName=budget_name
            )
            
            return {
                "budget_performance_history": response.get('BudgetPerformanceHistory', {}),
                "next_token": response.get('NextToken'),
                "account_id": account_id,
                "budget_name": budget_name,
                "real_data": True
            }
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                return {"error": f"Budget {budget_name} not found", "real_data": True}
            raise CloudServiceError(
                f"AWS Budget performance API error: {str(e)}",
                CloudProvider.AWS,
                "BUDGET_PERFORMANCE_ERROR"
            )
        except Exception as e:
            raise CloudServiceError(
                f"Unexpected error getting budget performance: {str(e)}",
                CloudProvider.AWS,
                "UNEXPECTED_ERROR"
            )
    
    def _get_mock_budgets_data(self, account_id: str) -> Dict[str, Any]:
        """Generate mock budgets data for testing."""
        return {
            "budgets": [
                {
                    "BudgetName": "Monthly-Cost-Budget",
                    "BudgetLimit": {"Amount": "1000.00", "Unit": "USD"},
                    "TimeUnit": "MONTHLY",
                    "BudgetType": "COST",
                    "CostFilters": {},
                    "TimePeriod": {
                        "Start": datetime.now().strftime("%Y-%m-01"),
                        "End": "2087-06-15"
                    }
                },
                {
                    "BudgetName": "EC2-Usage-Budget",
                    "BudgetLimit": {"Amount": "500.00", "Unit": "USD"},
                    "TimeUnit": "MONTHLY",
                    "BudgetType": "COST",
                    "CostFilters": {"Service": ["Amazon Elastic Compute Cloud - Compute"]},
                    "TimePeriod": {
                        "Start": datetime.now().strftime("%Y-%m-01"),
                        "End": "2087-06-15"
                    }
                }
            ],
            "account_id": account_id,
            "real_data": False
        }
    
    def _get_mock_budget_performance(self, account_id: str, budget_name: str) -> Dict[str, Any]:
        """Generate mock budget performance data for testing."""
        return {
            "budget_performance_history": {
                "BudgetName": budget_name,
                "BudgetType": "COST",
                "BudgetedAndActualAmountsList": [
                    {
                        "BudgetedAmount": {"Amount": "1000.00", "Unit": "USD"},
                        "ActualAmount": {"Amount": "750.50", "Unit": "USD"},
                        "TimePeriod": {
                            "Start": datetime.now().strftime("%Y-%m-01"),
                            "End": datetime.now().strftime("%Y-%m-28")
                        }
                    }
                ]
            },
            "account_id": account_id,
            "budget_name": budget_name,
            "real_data": False
        }
    
    async def close(self):
        """Close AWS client connections to prevent memory leaks."""
        try:
            # Close any HTTP sessions if they exist
            if hasattr(self, 'session') and self.session:
                try:
                    await self.session.aclose()
                    logger.debug("Closed AWS client HTTP session")
                except Exception as e:
                    logger.warning(f"Error closing AWS HTTP session: {e}")
            
            # Close boto3 clients (they don't have explicit close but we clear references)
            if hasattr(self, 'boto_client') and self.boto_client:
                # Boto3 clients don't need explicit cleanup but we can clear the reference
                self.boto_client = None
                logger.debug("Cleared AWS boto3 client reference")
                
        except Exception as e:
            logger.error(f"Error closing AWS client: {e}")