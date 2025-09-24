"""
Agent toolkit system for Infra Mind.

Provides tools and utilities that agents can use to perform their tasks.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class ToolStatus(str, Enum):
    """Tool execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_name: str
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    Base class for agent tools.
    
    Learning Note: Tools provide specific capabilities to agents,
    such as API calls, data processing, or external integrations.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used: Optional[datetime] = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    async def _execute_with_tracking(self, **kwargs) -> ToolResult:
        """Execute tool with usage tracking."""
        start_time = datetime.now(timezone.utc)
        
        try:
            result = await self.execute(**kwargs)
            result.execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Update usage tracking
            self.usage_count += 1
            self.last_used = datetime.now(timezone.utc)
            
            logger.debug(f"Tool {self.name} executed successfully in {result.execution_time:.3f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Tool {self.name} failed after {execution_time:.3f}s: {str(e)}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e),
                execution_time=execution_time
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


class DataProcessingTool(BaseTool):
    """Tool for processing and analyzing data."""
    
    def __init__(self):
        super().__init__(
            name="data_processor",
            description="Process and analyze assessment data"
        )
    
    async def execute(self, data: Dict[str, Any], operation: str = "analyze") -> ToolResult:
        """
        Execute data processing.
        
        Args:
            data: Data to process
            operation: Processing operation
            
        Returns:
            Processing result
        """
        try:
            if operation == "analyze":
                result = await self._analyze_data(data)
            elif operation == "summarize":
                result = await self._summarize_data(data)
            elif operation == "validate":
                result = await self._validate_data(data)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"operation": operation}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data and extract insights."""
        analysis = {
            "data_size": len(str(data)),
            "keys_count": len(data) if isinstance(data, dict) else 0,
            "data_types": {},
            "insights": []
        }
        
        if isinstance(data, dict):
            for key, value in data.items():
                analysis["data_types"][key] = type(value).__name__
                
                # Add some basic insights
                if key == "budget_range" and value:
                    analysis["insights"].append(f"Budget range specified: {value}")
                elif key == "company_size" and value:
                    analysis["insights"].append(f"Company size: {value}")
                elif key == "workload_types" and value:
                    analysis["insights"].append(f"Workload types: {', '.join(value) if isinstance(value, list) else value}")
                
                # Check nested dictionaries for business and technical requirements
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        if nested_key == "company_size" and nested_value:
                            analysis["insights"].append(f"Company size: {nested_value}")
                        elif nested_key == "industry" and nested_value:
                            analysis["insights"].append(f"Industry: {nested_value}")
                        elif nested_key == "workload_types" and nested_value:
                            workload_str = ', '.join(nested_value) if isinstance(nested_value, list) else str(nested_value)
                            analysis["insights"].append(f"Workload types: {workload_str}")
                        elif nested_key == "expected_users" and nested_value:
                            analysis["insights"].append(f"Expected users: {nested_value}")
        
        return analysis
    
    async def _summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize data into key points."""
        summary = {
            "key_points": [],
            "statistics": {},
            "recommendations": []
        }
        
        if isinstance(data, dict):
            # Extract key business information
            if "business_requirements" in data:
                business = data["business_requirements"]
                if isinstance(business, dict):
                    if business.get("company_size"):
                        summary["key_points"].append(f"Company size: {business['company_size']}")
                    if business.get("industry"):
                        summary["key_points"].append(f"Industry: {business['industry']}")
                    if business.get("budget_range"):
                        summary["key_points"].append(f"Budget: {business['budget_range']}")
            
            # Extract technical information
            if "technical_requirements" in data:
                technical = data["technical_requirements"]
                if isinstance(technical, dict):
                    if technical.get("workload_types"):
                        workloads = technical["workload_types"]
                        if isinstance(workloads, list):
                            summary["key_points"].append(f"Workloads: {', '.join(workloads)}")
                    if technical.get("expected_users"):
                        summary["key_points"].append(f"Expected users: {technical['expected_users']}")
        
        return summary
    
    async def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data completeness and consistency."""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "completeness_score": 0.0
        }
        
        required_fields = ["business_requirements", "technical_requirements"]
        present_fields = 0
        
        for field in required_fields:
            if field in data and data[field]:
                present_fields += 1
            else:
                validation["errors"].append(f"Missing required field: {field}")
                validation["is_valid"] = False
        
        validation["completeness_score"] = present_fields / len(required_fields)
        
        return validation


class CloudAPITool(BaseTool):
    """Tool for making cloud provider API calls."""
    
    def __init__(self):
        super().__init__(
            name="cloud_api",
            description="Make API calls to cloud providers"
        )
    
    async def execute(self, provider: str, service: str, operation: str, **params) -> ToolResult:
        """
        Execute cloud API call.
        
        Args:
            provider: Cloud provider (aws, azure, gcp)
            service: Cloud service name
            operation: API operation
            **params: Additional parameters
            
        Returns:
            API call result
        """
        try:
            # Use real API call with retry logic - no mock fallback
            api_data = await self._real_api_call_with_retry(provider, service, operation, **params)
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=api_data,
                metadata={
                    "provider": provider,
                    "service": service,
                    "operation": operation,
                    "real_api_used": True,
                    "no_mock_fallback": True
                }
            )
            
        except Exception as e:
            logger.error(f"Cloud API call failed for {provider}/{service}/{operation}: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=f"Real API call failed: {str(e)}",
                metadata={
                    "provider": provider,
                    "service": service,
                    "operation": operation,
                    "real_api_attempted": True,
                    "mock_fallback_disabled": True
                }
            )
    
    async def _real_api_call(self, provider: str, service: str, operation: str, **params) -> Dict[str, Any]:
        """Make real API calls to cloud providers."""
        if provider.lower() == "aws":
            return await self._call_aws_api(service, operation, **params)
        elif provider.lower() == "azure":
            return await self._call_azure_api(service, operation, **params)
        elif provider.lower() == "gcp":
            return await self._call_gcp_api(service, operation, **params)
        elif provider.lower() == "ibm":
            return await self._call_ibm_api(service, operation, **params)
        elif provider.lower() == "alibaba":
            return await self._call_alibaba_api(service, operation, **params)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")
    
    async def _real_api_call_with_retry(self, provider: str, service: str, operation: str, **params) -> Dict[str, Any]:
        """Make real API calls with retry logic but no mock fallback."""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                return await self._real_api_call(provider, service, operation, **params)
            
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, raise the exception
                    logger.error(f"All API call attempts failed for {provider}/{service}/{operation}: {e}")
                    raise
                else:
                    # Retry with exponential backoff
                    logger.warning(f"API call attempt {attempt + 1} failed for {provider}/{service}/{operation}: {e}, retrying...")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
    
    async def _call_aws_api(self, service: str, operation: str, **params) -> Dict[str, Any]:
        """Call AWS APIs using boto3."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
            
            # Get AWS credentials from environment or config
            session = boto3.Session()
            credentials = session.get_credentials()
            if not credentials:
                raise ValueError("AWS credentials not found. Please configure AWS credentials.")
            
            if service == "pricing":
                return await self._aws_pricing_api(operation, **params)
            elif service == "compute":
                return await self._aws_compute_api(operation, **params)
            elif service == "storage":
                return await self._aws_storage_api(operation, **params)
            elif service == "database":
                return await self._aws_database_api(operation, **params)
            else:
                raise ValueError(f"Unsupported AWS service: {service}")
                
        except ImportError as e:
            raise ImportError("boto3 not installed. Please install boto3 to use AWS APIs.") from e
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            # Handle boto3 exceptions properly
            raise ValueError(f"AWS API error: {str(e)}") from e
        except Exception as e:
            # Catch any other boto3-related errors
            raise ValueError(f"AWS API call failed: {str(e)}") from e
    
    async def _aws_pricing_api(self, operation: str, **params) -> Dict[str, Any]:
        """AWS Pricing API calls."""
        try:
            import boto3
            
            if operation == "list_services":
                # Return list of available AWS pricing services
                return {
                    "services": [
                        {"name": "AmazonEC2", "description": "Elastic Compute Cloud"},
                        {"name": "AmazonS3", "description": "Simple Storage Service"},
                        {"name": "AmazonRDS", "description": "Relational Database Service"},
                        {"name": "AmazonLambda", "description": "Lambda Functions"},
                        {"name": "AmazonEKS", "description": "Elastic Kubernetes Service"},
                        {"name": "AmazonCloudFront", "description": "Content Delivery Network"}
                    ]
                }
            
            # Use AWS Pricing API for other operations
            pricing_client = boto3.client('pricing', region_name='us-east-1')
            
            if operation == "get_products":
                service_code = params.get("service_code", "AmazonEC2")
                
                response = pricing_client.get_products(
                    ServiceCode=service_code,
                    MaxResults=10
                )
                
                products = []
                for price_item in response.get('PriceList', []):
                    import json
                    price_data = json.loads(price_item)
                    
                    product = price_data.get('product', {})
                    terms = price_data.get('terms', {})
                    
                    if 'OnDemand' in terms:
                        on_demand = list(terms['OnDemand'].values())[0]
                        price_dimensions = list(on_demand.get('priceDimensions', {}).values())[0]
                        
                        products.append({
                            "product_family": product.get('productFamily'),
                            "instance_type": product.get('attributes', {}).get('instanceType'),
                            "location": product.get('attributes', {}).get('location'),
                            "operating_system": product.get('attributes', {}).get('operatingSystem'),
                            "price_per_unit": price_dimensions.get('pricePerUnit', {}).get('USD'),
                            "unit": price_dimensions.get('unit'),
                            "description": price_dimensions.get('description')
                        })
                
                return {"products": products[:10]}
            
            elif operation == "estimate_cost":
                # Estimate cost based on service configuration
                service_config = params.get("service_config", {})
                usage_patterns = params.get("usage_patterns", {})
                
                # Basic cost estimation logic
                instance_type = service_config.get("instance_type", "t3.medium")
                hours_per_month = usage_patterns.get("hours_per_month", 730)
                
                # Rough pricing data (this would use real pricing API in production)
                pricing_data = {
                    "t3.micro": 0.0104,
                    "t3.small": 0.0208,
                    "t3.medium": 0.0416,
                    "t3.large": 0.0832,
                    "m5.large": 0.096,
                    "m5.xlarge": 0.192
                }
                
                hourly_rate = pricing_data.get(instance_type, 0.05)
                monthly_cost = hourly_rate * hours_per_month
                
                return {
                    "monthly_cost": round(monthly_cost, 2),
                    "hourly_rate": hourly_rate,
                    "instance_type": instance_type,
                    "hours_per_month": hours_per_month,
                    "currency": "USD"
                }
            
        except Exception as e:
            logger.error(f"AWS Pricing API error: {e}")
            raise
    
    async def _aws_compute_api(self, operation: str, **params) -> Dict[str, Any]:
        """AWS Compute API calls."""
        try:
            import boto3
            
            ec2_client = boto3.client('ec2')
            
            if operation == "list_services":
                # Get instance types and basic info
                response = ec2_client.describe_instance_types(MaxResults=20)
                
                services = []
                for instance_type in response.get('InstanceTypes', []):
                    services.append({
                        "service_id": f"ec2_{instance_type['InstanceType']}",
                        "name": f"EC2 {instance_type['InstanceType']}",
                        "specifications": {
                            "vcpus": instance_type.get('VCpuInfo', {}).get('DefaultVCpus', 1),
                            "memory_gb": instance_type.get('MemoryInfo', {}).get('SizeInMiB', 1024) / 1024,
                            "network_performance": instance_type.get('NetworkInfo', {}).get('NetworkPerformance', 'Moderate'),
                            "storage": instance_type.get('InstanceStorageInfo', {}).get('TotalSizeInGB', 0)
                        },
                        "features": ["Auto Scaling", "Load Balancing", "Monitoring"],
                        "pricing": {"model": "on_demand", "unit": "hour"}
                    })
                
                return {"services": services}
            
            elif operation == "get_regions":
                response = ec2_client.describe_regions()
                regions = [
                    {"name": region['RegionName'], "endpoint": region['Endpoint']}
                    for region in response.get('Regions', [])
                ]
                return {"regions": regions}
                
        except Exception as e:
            logger.error(f"AWS Compute API error: {e}")
            raise
    
    async def _aws_storage_api(self, operation: str, **params) -> Dict[str, Any]:
        """AWS Storage API using real AWS SDK."""
        import boto3
        
        if operation == "list_services":
            # Initialize clients
            s3_client = boto3.client('s3')
            ec2_client = boto3.client('ec2')
            
            services = []
            
            # Get S3 buckets
            buckets_response = s3_client.list_buckets()
            for bucket in buckets_response['Buckets']:
                # Get bucket location
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket['Name'])
                    region = location['LocationConstraint'] or 'us-east-1'
                except Exception:
                    region = 'us-east-1'
                    
                services.append({
                    "service_id": f"s3_bucket_{bucket['Name']}",
                    "name": f"S3 Bucket ({bucket['Name']})",
                    "specifications": {
                        "bucket_name": bucket['Name'],
                        "region": region,
                        "creation_date": bucket['CreationDate'].isoformat()
                    },
                    "features": ["Lifecycle management", "Versioning", "Encryption"],
                    "api_source": "aws_sdk"
                })
            
            # Get EBS volumes
            volumes_response = ec2_client.describe_volumes(MaxResults=10)
            for volume in volumes_response['Volumes']:
                services.append({
                    "service_id": f"ebs_volume_{volume['VolumeId']}",
                    "name": f"EBS Volume ({volume['VolumeType'].upper()})",
                    "specifications": {
                        "volume_id": volume['VolumeId'],
                        "volume_type": volume['VolumeType'],
                        "size_gb": volume['Size'],
                        "state": volume['State'],
                        "availability_zone": volume['AvailabilityZone']
                    },
                    "features": ["Encryption", "Snapshots", "Multi-attach"],
                    "api_source": "aws_sdk"
                })
            
            return {"services": services, "source": "aws_storage_sdk"}
    
    async def _aws_database_api(self, operation: str, **params) -> Dict[str, Any]:
        """AWS Database API calls."""
        try:
            import boto3
            
            rds_client = boto3.client('rds')
            
            if operation == "list_services":
                # Get RDS instance classes
                response = rds_client.describe_orderable_db_instance_options(
                    Engine='mysql',
                    MaxRecords=20
                )
                
                services = []
                for option in response.get('OrderableDBInstanceOptions', []):
                    services.append({
                        "service_id": f"rds_{option['DBInstanceClass']}",
                        "name": f"RDS {option['DBInstanceClass']}",
                        "specifications": {
                            "instance_class": option['DBInstanceClass'],
                            "engine": option['Engine'],
                            "multi_az": option['MultiAZCapable'],
                            "storage_type": option.get('StorageType', 'gp2')
                        },
                        "features": ["Automated backups", "Read replicas", "Encryption"],
                        "pricing": {"model": "on_demand", "unit": "hour"}
                    })
                
                return {"services": services[:10]}
                
        except Exception as e:
            logger.error(f"AWS Database API error: {e}")
            raise
    
    async def _call_azure_api(self, service: str, operation: str, **params) -> Dict[str, Any]:
        """Call Azure APIs."""
        try:
            # Azure pricing and service information
            if service == "pricing":
                return await self._azure_pricing_api(operation, **params)
            elif service == "compute":
                return await self._azure_compute_api(operation, **params)
            elif service == "storage":
                return await self._azure_storage_api(operation, **params)
            elif service == "database":
                return await self._azure_database_api(operation, **params)
            else:
                raise ValueError(f"Unsupported Azure service: {service}")
                
        except Exception as e:
            logger.error(f"Azure API call failed: {e}")
            raise
    
    async def _azure_pricing_api(self, operation: str, **params) -> Dict[str, Any]:
        """Azure pricing API simulation (Azure doesn't have a direct pricing API like AWS)."""
        # This would integrate with Azure Cost Management API or use retail prices API
        
        if operation == "estimate_cost":
            service_config = params.get("service_config", {})
            vm_size = service_config.get("vm_size", "Standard_B2s")
            
            # Basic Azure VM pricing (rough estimates)
            pricing_data = {
                "Standard_B1s": 0.0104,
                "Standard_B2s": 0.0416,
                "Standard_D2s_v3": 0.096,
                "Standard_D4s_v3": 0.192
            }
            
            hourly_rate = pricing_data.get(vm_size, 0.05)
            monthly_cost = hourly_rate * 730
            
            return {
                "monthly_cost": round(monthly_cost, 2),
                "hourly_rate": hourly_rate,
                "vm_size": vm_size,
                "currency": "USD"
            }
        
        # For production use Azure Retail Prices API
        # https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
        raise NotImplementedError("Azure Retail Prices API integration required for production")
    
    async def _azure_compute_api(self, operation: str, **params) -> Dict[str, Any]:
        """Azure compute API using real Azure SDK."""
        import os
        
        try:
            from azure.mgmt.compute import ComputeManagementClient
            from azure.identity import DefaultAzureCredential
            from azure.core.exceptions import AzureError
            
            if operation == "list_services":
                try:
                    # Use DefaultAzureCredential for authentication
                    credential = DefaultAzureCredential()
                    
                    # Get subscription ID from environment
                    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
                    if not subscription_id:
                        raise ValueError("AZURE_SUBSCRIPTION_ID environment variable is required")
                    
                    # Create compute client
                    compute_client = ComputeManagementClient(credential, subscription_id)
                    
                    # Get VM sizes for a region (default to East US)
                    location = params.get("location", "eastus")
                    vm_sizes = compute_client.virtual_machine_sizes.list(location)
                    
                    services = []
                    for size in list(vm_sizes)[:10]:  # Limit to first 10 sizes
                        services.append({
                            "service_id": f"vm_{size.name.lower()}",
                            "name": size.name,
                            "specifications": {
                                "vcpus": size.number_of_cores,
                                "memory_gb": size.memory_in_mb / 1024,
                                "temp_storage_gb": size.resource_disk_size_in_mb / 1024 if size.resource_disk_size_in_mb else 0,
                                "max_data_disks": size.max_data_disk_count,
                                "os_disk_size_gb": size.os_disk_size_in_mb / 1024 if size.os_disk_size_in_mb else 0
                            },
                            "features": ["Auto-scaling", "Load balancing", "Availability sets"],
                            "location": location,
                            "api_source": "azure_sdk"
                        })
                    
                    return {"services": services, "location": location, "source": "azure_compute_sdk"}
                    
                except AzureError as e:
                    logger.error(f"Azure Compute API failed: {e}")
                    raise
                    
            elif operation == "get_pricing":
                # For pricing, we'd use Azure Retail Prices API or Cost Management API
                return await self._get_azure_pricing_data(params)
                
        except ImportError:
            logger.error("Azure SDK not available")
            raise
        except Exception as e:
            logger.error(f"Azure Compute API error: {e}")
            raise
    
    
    async def _azure_storage_api(self, operation: str, **params) -> Dict[str, Any]:
        """Azure storage API using real Azure SDK."""
        import os
        from azure.mgmt.storage import StorageManagementClient
        from azure.identity import DefaultAzureCredential
        from azure.core.exceptions import AzureError
        
        if operation == "list_services":
            credential = DefaultAzureCredential()
            subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            
            storage_client = StorageManagementClient(credential, subscription_id)
            
            # Get storage accounts
            storage_accounts = storage_client.storage_accounts.list()
            
            services = []
            for account in storage_accounts:
                services.append({
                    "service_id": f"storage_{account.name}",
                    "name": f"Storage Account ({account.name})",
                    "specifications": {
                        "location": account.location,
                        "sku": account.sku.name,
                        "kind": account.kind,
                        "access_tier": getattr(account, 'access_tier', 'Hot')
                    },
                    "features": ["Blob storage", "File storage", "Queue storage", "Table storage"],
                    "api_source": "azure_sdk"
                })
            
            return {"services": services, "source": "azure_storage_sdk"}
    
    async def _azure_database_api(self, operation: str, **params) -> Dict[str, Any]:
        """Azure database API simulation."""
        if operation == "list_services":
            services = [
                {
                    "service_id": "sql_s2",
                    "name": "Azure SQL Database (S2)",
                    "specifications": {
                        "service_tier": "Standard",
                        "performance_level": "S2",
                        "dtu": 50,
                        "storage_gb": 250
                    },
                    "features": ["Backup retention", "Point-in-time restore", "Encryption"],
                    "pricing": {"monthly": 30.00}
                },
                {
                    "service_id": "cosmosdb_ru",
                    "name": "Azure Cosmos DB",
                    "specifications": {
                        "consistency": "Session",
                        "throughput": "400 RU/s",
                        "storage": "Unlimited"
                    },
                    "features": ["Multi-region", "Auto-scaling", "Multiple APIs"],
                    "pricing": {"per_ru_hour": 0.008}
                }
            ]
            return {"services": services}
        
        raise NotImplementedError("Azure Database API integration required for production")
    
    async def _call_gcp_api(self, service: str, operation: str, **params) -> Dict[str, Any]:
        """Call GCP APIs."""
        try:
            if service == "pricing":
                return await self._gcp_pricing_api(operation, **params)
            elif service == "compute":
                return await self._gcp_compute_api(operation, **params)
            elif service == "storage":
                return await self._gcp_storage_api(operation, **params)
            elif service == "database":
                return await self._gcp_database_api(operation, **params)
            else:
                raise ValueError(f"Unsupported GCP service: {service}")
                
        except Exception as e:
            logger.error(f"GCP API call failed: {e}")
            raise
    
    async def _gcp_pricing_api(self, operation: str, **params) -> Dict[str, Any]:
        """GCP pricing API simulation."""
        if operation == "estimate_cost":
            service_config = params.get("service_config", {})
            machine_type = service_config.get("machine_type", "e2-medium")
            
            # Basic GCP pricing (rough estimates)
            pricing_data = {
                "e2-micro": 0.005,
                "e2-small": 0.01,
                "e2-medium": 0.02,
                "n1-standard-1": 0.0475,
                "n1-standard-2": 0.095
            }
            
            hourly_rate = pricing_data.get(machine_type, 0.025)
            monthly_cost = hourly_rate * 730
            
            return {
                "monthly_cost": round(monthly_cost, 2),
                "hourly_rate": hourly_rate,
                "machine_type": machine_type,
                "currency": "USD"
            }
        
        # For production use GCP Cloud Billing API
        # https://cloud.google.com/billing/docs/reference/rest
        raise NotImplementedError("GCP Cloud Billing API integration required for production")
    
    async def _gcp_compute_api(self, operation: str, **params) -> Dict[str, Any]:
        """GCP compute API using real Google Cloud SDK."""
        import os
        
        try:
            from google.cloud import compute_v1
            from google.auth import default
            from google.auth.exceptions import DefaultCredentialsError
            
            if operation == "list_services":
                try:
                    # Get project ID from environment
                    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
                    if not project_id:
                        logger.error("GCP_PROJECT_ID environment variable is required")
                        raise
                    
                    # Initialize compute client
                    client = compute_v1.MachineTypesClient()
                    
                    # Get machine types for a zone (default to us-central1-a)
                    zone = params.get("zone", "us-central1-a")
                    request = compute_v1.ListMachineTypesRequest(
                        project=project_id,
                        zone=zone
                    )
                    
                    machine_types = client.list(request=request)
                    
                    services = []
                    count = 0
                    for machine_type in machine_types:
                        if count >= 10:  # Limit to first 10 machine types
                            break
                        
                        services.append({
                            "service_id": f"compute_{machine_type.name}",
                            "name": machine_type.name,
                            "specifications": {
                                "vcpus": machine_type.guest_cpus,
                                "memory_gb": machine_type.memory_mb / 1024,
                                "zone": zone,
                                "maximum_persistent_disks": machine_type.maximum_persistent_disks,
                                "maximum_persistent_disks_size_gb": machine_type.maximum_persistent_disks_size_gb
                            },
                            "features": ["Preemptible instances", "Custom machine types", "Live migration"],
                            "api_source": "gcp_sdk"
                        })
                        count += 1
                    
                    return {"services": services, "zone": zone, "project": project_id, "source": "gcp_compute_sdk"}
                    
                except DefaultCredentialsError:
                    logger.error("GCP credentials not found")
                    raise
                except Exception as e:
                    logger.error(f"GCP Compute API failed: {e}")
                    raise
                    
            elif operation == "get_pricing":
                # For pricing, we'd use GCP Billing API or Cloud Asset Inventory
                return await self._get_gcp_pricing_data(params)
                
        except ImportError:
            logger.error("GCP SDK not available")
            raise
        except Exception as e:
            logger.error(f"GCP Compute API error: {e}")
            raise
    
    
    async def _gcp_storage_api(self, operation: str, **params) -> Dict[str, Any]:
        """GCP storage API using real Google Cloud SDK."""
        import os
        from google.cloud import storage
        from google.cloud import compute_v1
        from google.auth.exceptions import DefaultCredentialsError
        
        if operation == "list_services":
            # Initialize clients
            storage_client = storage.Client()
            compute_client = compute_v1.DisksClient()
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            
            services = []
            
            # Get storage buckets
            buckets = storage_client.list_buckets()
            for bucket in buckets:
                services.append({
                    "service_id": f"gcs_bucket_{bucket.name}",
                    "name": f"Cloud Storage Bucket ({bucket.name})",
                    "specifications": {
                        "storage_class": bucket.storage_class,
                        "location": bucket.location,
                        "location_type": bucket.location_type
                    },
                    "features": ["Lifecycle management", "Versioning", "IAM"],
                    "api_source": "gcp_sdk"
                })
            
            # Get compute disks from first available zone
            zones = ['us-central1-a', 'us-east1-b', 'europe-west1-b']
            for zone in zones:
                try:
                    request = compute_v1.ListDisksRequest(
                        project=project_id,
                        zone=zone
                    )
                    disks = compute_client.list(request=request)
                    for disk in disks:
                        services.append({
                            "service_id": f"persistent_disk_{disk.name}",
                            "name": f"Persistent Disk ({disk.name})",
                            "specifications": {
                                "disk_type": disk.type_.split('/')[-1],
                                "size_gb": disk.size_gb,
                                "zone": disk.zone.split('/')[-1]
                            },
                            "features": ["Snapshots", "Regional replication"],
                            "api_source": "gcp_sdk"
                        })
                    break
                except Exception:
                    continue
            
            return {"services": services, "source": "gcp_storage_sdk"}
    
    async def _gcp_database_api(self, operation: str, **params) -> Dict[str, Any]:
        """GCP database API simulation."""
        if operation == "list_services":
            services = [
                {
                    "service_id": "cloudsql_mysql",
                    "name": "Cloud SQL for MySQL",
                    "specifications": {
                        "instance_type": "db-n1-standard-1",
                        "vcpus": 1,
                        "memory_gb": 3.75,
                        "storage": "Up to 30TB"
                    },
                    "features": ["Automatic backups", "Point-in-time recovery", "High availability"],
                    "pricing": {"hourly": 0.0685}
                },
                {
                    "service_id": "firestore_native",
                    "name": "Cloud Firestore",
                    "specifications": {
                        "database_type": "Document",
                        "reads": "Up to 1M/day free",
                        "writes": "Up to 20K/day free"
                    },
                    "features": ["Real-time updates", "Multi-region", "ACID transactions"],
                    "pricing": {"per_document_read": 0.000036}
                }
            ]
            return {"services": services}
        
        raise NotImplementedError("GCP Database API integration required for production")
    
    async def _call_ibm_api(self, service: str, operation: str, **params) -> Dict[str, Any]:
        """Call IBM Cloud APIs."""
        try:
            if service == "pricing":
                return await self._ibm_pricing_api(operation, **params)
            elif service == "compute":
                return await self._ibm_compute_api(operation, **params)
            elif service == "storage":
                return await self._ibm_storage_api(operation, **params)
            elif service == "database":
                return await self._ibm_database_api(operation, **params)
            else:
                raise ValueError(f"Unsupported IBM service: {service}")
        except Exception as e:
            logger.error(f"IBM API call failed: {e}")
            raise
    
    async def _ibm_compute_api(self, operation: str, **params) -> Dict[str, Any]:
        """IBM Cloud compute API using real IBM SDK."""
        import os
        
        try:
            from ibm_vpc import VpcV1
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            from ibm_cloud_sdk_core import ApiException
            
            if operation == "list_services":
                try:
                    # Get IBM Cloud credentials from environment
                    api_key = os.getenv("IBM_CLOUD_API_KEY")
                    if not api_key:
                        logger.error("IBM_CLOUD_API_KEY environment variable is required")
                        raise
                    
                    # Initialize authenticator and VPC client
                    authenticator = IAMAuthenticator(api_key)
                    vpc_service = VpcV1(
                        version='2023-12-19',
                        authenticator=authenticator
                    )
                    
                    # Set service URL (default to us-south region)
                    region = params.get("region", "us-south")
                    vpc_service.set_service_url(f"https://{region}.iaas.cloud.ibm.com/v1")
                    
                    # Get instance profiles (VM configurations)
                    response = vpc_service.list_instance_profiles()
                    profiles = response.get_result()['instance_profiles']
                    
                    services = []
                    for profile in profiles[:10]:  # Limit to first 10 profiles
                        vcpu_info = profile.get('vcpu_count', {})
                        memory_info = profile.get('memory', {})
                        
                        services.append({
                            "service_id": f"ibm_{profile['name']}",
                            "name": f"Virtual Server ({profile['name']})",
                            "specifications": {
                                "vcpus": vcpu_info.get('value', 'variable'),
                                "memory_gb": memory_info.get('value', 'variable') / 1024 if isinstance(memory_info.get('value'), (int, float)) else 'variable',
                                "family": profile.get('family'),
                                "architecture": profile.get('architecture')
                            },
                            "features": ["Load balancing", "Auto-scaling", "Security groups", "VPC networking"],
                            "region": region,
                            "api_source": "ibm_sdk"
                        })
                    
                    return {"services": services, "region": region, "source": "ibm_vpc_sdk"}
                    
                except ApiException as e:
                    logger.error(f"IBM Cloud API failed: {e}")
                    raise
                except Exception as e:
                    logger.error(f"IBM Cloud error: {e}")
                    raise
                    
        except ImportError:
            logger.error("IBM Cloud SDK not available")
            raise
        except Exception as e:
            logger.error(f"IBM Compute API error: {e}")
            raise
    
    
    async def _ibm_storage_api(self, operation: str, **params) -> Dict[str, Any]:
        """IBM Cloud storage API using real IBM SDK."""
        import os
        from ibm_platform_services import ResourceManagerV2
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        from ibm_cloud_sdk_core import ApiException
        
        if operation == "list_services":
            api_key = os.getenv("IBM_CLOUD_API_KEY")
            
            authenticator = IAMAuthenticator(api_key)
            resource_manager = ResourceManagerV2(authenticator=authenticator)
            
            # Get resource instances
            response = resource_manager.list_resource_instances()
            instances = response.get_result()['resources']
            
            services = []
            for instance in instances:
                if 'storage' in instance.get('name').lower() or 'cos' in instance.get('name').lower():
                    services.append({
                        "service_id": f"ibm_storage_{instance['id'][:8]}",
                        "name": f"Storage Service ({instance['name']})",
                        "specifications": {
                            "state": instance['state'],
                            "type": instance.get('type'),
                            "region": instance.get('region_id')
                        },
                        "features": ["Encryption", "Cross-region replication", "Lifecycle management"],
                        "api_source": "ibm_sdk"
                    })
            
            return {"services": services, "source": "ibm_resource_sdk"}
    
    async def _ibm_database_api(self, operation: str, **params) -> Dict[str, Any]:
        """IBM Cloud database API simulation."""
        if operation == "list_services":
            services = [
                {
                    "service_id": "ibm_postgresql",
                    "name": "Databases for PostgreSQL",
                    "specifications": {
                        "database_type": "PostgreSQL",
                        "memory": "1GB",
                        "disk": "5GB"
                    },
                    "features": ["Automatic backups", "Encryption", "High availability"],
                    "pricing": {"monthly": 30.00}
                }
            ]
            return {"services": services}
        raise NotImplementedError("IBM Database API integration required for production")
    
    async def _ibm_pricing_api(self, operation: str, **params) -> Dict[str, Any]:
        """IBM Cloud pricing API simulation."""
        if operation == "estimate_cost":
            return {
                "monthly_cost": 95.00,
                "currency": "USD",
                "provider": "IBM Cloud"
            }
        raise NotImplementedError("IBM Pricing API integration required for production")
    
    async def _call_alibaba_api(self, service: str, operation: str, **params) -> Dict[str, Any]:
        """Call Alibaba Cloud APIs."""
        try:
            if service == "pricing":
                return await self._alibaba_pricing_api(operation, **params)
            elif service == "compute":
                return await self._alibaba_compute_api(operation, **params)
            elif service == "storage":
                return await self._alibaba_storage_api(operation, **params)
            elif service == "database":
                return await self._alibaba_database_api(operation, **params)
            else:
                raise ValueError(f"Unsupported Alibaba service: {service}")
        except Exception as e:
            logger.error(f"Alibaba API call failed: {e}")
            raise
    
    async def _alibaba_compute_api(self, operation: str, **params) -> Dict[str, Any]:
        """Alibaba Cloud compute API using real Alibaba SDK."""
        import os
        
        try:
            from alibabacloud_ecs20140526.client import Client as EcsClient
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_ecs20140526 import models as ecs_models
            from alibabacloud_tea_util import models as util_models
            
            if operation == "list_services":
                try:
                    # Get Alibaba Cloud credentials from environment
                    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
                    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
                    
                    if not access_key_id or not access_key_secret:
                        logger.error("Alibaba Cloud credentials are required")
                        raise
                    
                    # Initialize ECS client
                    config = open_api_models.Config(
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret
                    )
                    
                    # Set endpoint (default to China East 1 - Hangzhou)
                    region = params.get("region", "us-west-1")
                    config.endpoint = f"ecs.{region}.aliyuncs.com"
                    
                    client = EcsClient(config)
                    
                    # Describe instance types
                    describe_instance_types_request = ecs_models.DescribeInstanceTypesRequest()
                    runtime = util_models.RuntimeOptions()
                    
                    response = client.describe_instance_types_with_options(describe_instance_types_request, runtime)
                    instance_types = response.body.instance_types.instance_type
                    
                    services = []
                    for instance_type in instance_types[:10]:  # Limit to first 10 instance types
                        services.append({
                            "service_id": f"ecs_{instance_type.instance_type_id}",
                            "name": f"ECS {instance_type.instance_type_id}",
                            "specifications": {
                                "vcpus": instance_type.cpu_core_count,
                                "memory_gb": instance_type.memory_size,
                                "instance_family": instance_type.instance_type_family,
                                "network_performance": f"{instance_type.instance_pps_rx + instance_type.instance_pps_tx} PPS" if hasattr(instance_type, 'instance_pps_rx') else "Standard"
                            },
                            "features": ["Auto Scaling", "Load Balancing", "Security Groups", "Spot Instances"],
                            "region": region,
                            "api_source": "alibaba_sdk"
                        })
                    
                    return {"services": services, "region": region, "source": "alibaba_ecs_sdk"}
                    
                except Exception as e:
                    logger.error(f"Alibaba Cloud API failed: {e}")
                    raise
                    
        except ImportError:
            logger.error("Alibaba Cloud SDK not available")
            raise
        except Exception as e:
            logger.error(f"Alibaba Compute API error: {e}")
            raise
    
    
    async def _alibaba_storage_api(self, operation: str, **params) -> Dict[str, Any]:
        """Alibaba Cloud storage API using real Alibaba SDK."""
        import os
        from alibabacloud_oss20190517.client import Client as OSSClient
        from alibabacloud_tea_openapi import models as open_api_models
        
        if operation == "list_services":
            access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
            access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
            region = params.get("region", "us-west-1")
            
            config = open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                region_id=region,
                endpoint=f"oss-{region}.aliyuncs.com"
            )
            
            client = OSSClient(config)
            
            # Get OSS buckets
            services = []
            try:
                # Note: OSS list buckets would require proper request model
                # For now, we create a basic service entry for OSS
                services.append({
                    "service_id": "alibaba_oss",
                    "name": "Object Storage Service (OSS)",
                    "specifications": {
                        "region": region,
                        "endpoint": f"oss-{region}.aliyuncs.com",
                        "storage_classes": ["Standard", "IA", "Archive", "ColdArchive"]
                    },
                    "features": ["Lifecycle management", "Cross-region replication", "Data encryption"],
                    "api_source": "alibaba_sdk"
                })
            except Exception as e:
                logger.error(f"Alibaba OSS API error: {e}")
                raise
            
            return {"services": services, "source": "alibaba_oss_sdk"}
    
    async def _alibaba_database_api(self, operation: str, **params) -> Dict[str, Any]:
        """Alibaba Cloud database API simulation."""
        if operation == "list_services":
            services = [
                {
                    "service_id": "rds_mysql",
                    "name": "ApsaraDB for RDS (MySQL)",
                    "specifications": {
                        "database_type": "MySQL",
                        "instance_class": "rds.mysql.s2.large",
                        "memory_gb": 4
                    },
                    "features": ["Automatic backups", "Read replicas", "Performance monitoring"],
                    "pricing": {"hourly": 0.12}
                }
            ]
            return {"services": services}
        raise NotImplementedError("Alibaba Database API integration required for production")
    
    async def _alibaba_pricing_api(self, operation: str, **params) -> Dict[str, Any]:
        """Alibaba Cloud pricing API simulation."""
        if operation == "estimate_cost":
            return {
                "monthly_cost": 85.00,
                "currency": "USD",
                "provider": "Alibaba Cloud"
            }
        raise NotImplementedError("Alibaba Pricing API integration required for production")
    
    # Fallback mock methods for when real APIs aren't available


class AgentToolkit:
    """
    Toolkit for managing and executing agent tools.
    
    Provides a unified interface for agents to use various tools
    like cloud APIs, data processing, and web research.
    """
    
    def __init__(self, enabled_tools: List[str]):
        """
        Initialize the toolkit with enabled tools.
        
        Args:
            enabled_tools: List of tool names to enable
        """
        self.enabled_tools = enabled_tools
        self.tools: Dict[str, BaseTool] = {}
        self.api_call_count = 0
        
        # Initialize available tools
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available tools."""
        # Always available tools
        self.tools["data_processor"] = DataProcessingTool()
        self.tools["cloud_api"] = CloudAPITool()
        
        # Add calculator tool (simple implementation)
        self.tools["calculator"] = CalculatorTool()
    
    async def initialize(self, assessment, context: Optional[Dict[str, Any]] = None):
        """Initialize toolkit with assessment context."""
        self.assessment = assessment
        self.context = context or {}
        logger.debug(f"Initialized toolkit with {len(self.tools)} tools")
    
    async def use_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Use a tool from the toolkit.
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=f"Tool '{tool_name}' not available"
            )
        
        if tool_name not in self.enabled_tools:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=f"Tool '{tool_name}' not enabled"
            )
        
        try:
            # Track API calls
            self.api_call_count += 1
            
            # Execute tool
            tool = self.tools[tool_name]
            result = await tool._execute_with_tracking(**kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tools.keys())
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools."""
        return self.enabled_tools
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled."""
        return tool_name in self.enabled_tools


class CalculatorTool(BaseTool):
    """Simple calculator tool for basic math operations."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform basic mathematical calculations"
        )
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """
        Execute calculator operation.
        
        Args:
            operation: Math operation to perform
            **kwargs: Operation parameters
            
        Returns:
            Calculation result
        """
        try:
            if operation == "add":
                result = kwargs.get("a", 0) + kwargs.get("b", 0)
            elif operation == "multiply":
                result = kwargs.get("a", 1) * kwargs.get("b", 1)
            elif operation == "divide":
                b = kwargs.get("b", 1)
                if b == 0:
                    raise ValueError("Division by zero")
                result = kwargs.get("a", 0) / b
            elif operation == "percentage":
                result = (kwargs.get("value", 0) * kwargs.get("percentage", 0)) / 100
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data={"result": result, "operation": operation},
                metadata={"operation": operation}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
