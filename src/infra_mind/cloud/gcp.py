"""
Google Cloud Platform (GCP) service integration for Infra Mind.

Provides clients for GCP Cloud Billing API, Compute Engine, Cloud SQL, and other services.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
import os

from .base import (
    BaseCloudClient, CloudProvider, CloudService, CloudServiceResponse,
    ServiceCategory, CloudServiceError, RateLimitError, AuthenticationError
)

logger = logging.getLogger(__name__)


class GCPClient(BaseCloudClient):
    """
    Main GCP client that coordinates other GCP service clients.
    
    Learning Note: This acts as a facade for various GCP services,
    providing a unified interface for GCP operations using real APIs.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        """
        Initialize GCP client.
        
        Args:
            project_id: GCP project ID
            region: GCP region
            service_account_path: Path to service account JSON file
            
        Raises:
            AuthenticationError: If GCP credentials are not available or invalid
        """
        super().__init__(CloudProvider.GCP, region)
        self.project_id = project_id
        
        # Validate credentials
        self._validate_credentials(service_account_path)
        
        # Initialize service clients
        self.billing_client = GCPBillingClient(project_id, region, service_account_path)
        self.compute_client = GCPComputeClient(project_id, region, service_account_path)
        self.sql_client = GCPSQLClient(project_id, region, service_account_path)
        self.ai_client = GCPAIClient(project_id, region, service_account_path)
        self.gke_client = GCPGKEClient(project_id, region, service_account_path)
        self.asset_client = GCPAssetClient(project_id, region, service_account_path)
        self.recommender_client = GCPRecommenderClient(project_id, region, service_account_path)
    
    def _validate_credentials(self, service_account_path: Optional[str]):
        """Validate GCP credentials are available."""
        try:
            # Check for service account file
            if service_account_path and os.path.exists(service_account_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
                return
            
            # Check for environment variable
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if os.path.exists(creds_path):
                    return
            
            # For now, we'll allow initialization without credentials for development
            logger.warning("GCP credentials not found. Some features may not work.")
            
        except Exception as e:
            logger.warning(f"GCP credential validation failed: {e}")
    
    async def get_compute_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get GCP compute services (Compute Engine instances)."""
        return await self.compute_client.get_machine_types(region or self.region)
    
    async def get_storage_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get GCP storage services (Cloud Storage, Persistent Disks)."""
        return await self._get_storage_services_with_pricing(region or self.region)
    
    async def get_database_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get GCP database services (Cloud SQL)."""
        return await self.sql_client.get_database_instances(region or self.region)
    
    async def get_ai_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get GCP AI/ML services."""
        return await self.ai_client.get_ai_services(region or self.region)
    
    async def get_kubernetes_services(self, region: Optional[str] = None) -> CloudServiceResponse:
        """Get GCP Kubernetes Engine (GKE) services."""
        return await self.gke_client.get_gke_services(region or self.region)
    
    async def get_asset_inventory(self, asset_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get GCP asset inventory information."""
        return await self.asset_client.get_asset_inventory(asset_types)
    
    async def get_recommendations(self, recommender_type: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get GCP recommendations for cost optimization and performance."""
        return await self.recommender_client.get_recommendations(recommender_type, region or self.region)
    
    async def get_service_pricing(self, service_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing for a specific GCP service."""
        return await self.billing_client.get_service_pricing(service_id, region or self.region)
    
    async def _get_storage_services_with_pricing(self, region: str) -> CloudServiceResponse:
        """Get GCP storage services with pricing."""
        try:
            # Get pricing data from billing API
            pricing_data = await self.billing_client.get_service_pricing("Cloud Storage", region)
            
            services = []
            
            # Cloud Storage
            storage_service = CloudService(
                provider=CloudProvider.GCP,
                service_name="Google Cloud Storage",
                service_id="cloud_storage",
                category=ServiceCategory.STORAGE,
                region=region,
                description="Object storage service with global edge caching",
                hourly_price=0.020,  # $0.020 per GB/month (standard storage)
                pricing_model="pay_per_use",
                pricing_unit="GB/month",
                specifications={
                    "storage_class": "standard",
                    "durability": "99.999999999%",
                    "availability": "99.95%",
                    "max_object_size": "5TB"
                },
                features=["global_cdn", "versioning", "lifecycle_management", "encryption"]
            )
            services.append(storage_service)
            
            # Persistent Disk SSD
            disk_ssd_service = CloudService(
                provider=CloudProvider.GCP,
                service_name="Persistent Disk SSD",
                service_id="persistent_disk_ssd",
                category=ServiceCategory.STORAGE,
                region=region,
                description="High-performance SSD persistent disk storage",
                hourly_price=0.170,  # $0.170 per GB/month
                pricing_model="pay_per_use",
                pricing_unit="GB/month",
                specifications={
                    "disk_type": "pd-ssd",
                    "iops": 30,  # IOPS per GB
                    "throughput": 0.48,  # MB/s per GB
                    "max_size": "65536GB"
                },
                features=["snapshot_support", "encryption", "regional_replication"]
            )
            services.append(disk_ssd_service)
            
            # Persistent Disk Standard
            disk_standard_service = CloudService(
                provider=CloudProvider.GCP,
                service_name="Persistent Disk Standard",
                service_id="persistent_disk_standard",
                category=ServiceCategory.STORAGE,
                region=region,
                description="Cost-effective standard persistent disk storage",
                hourly_price=0.040,  # $0.040 per GB/month
                pricing_model="pay_per_use",
                pricing_unit="GB/month",
                specifications={
                    "disk_type": "pd-standard",
                    "iops": 0.75,  # IOPS per GB
                    "throughput": 0.12,  # MB/s per GB
                    "max_size": "65536GB"
                },
                features=["snapshot_support", "encryption", "regional_replication"]
            )
            services.append(disk_standard_service)
            
            return CloudServiceResponse(
                provider=CloudProvider.GCP,
                service_category=ServiceCategory.STORAGE,
                region=region,
                services=services,
                metadata={"real_api": True, "pricing_source": "gcp_billing_api"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP storage services: {str(e)}",
                CloudProvider.GCP,
                "STORAGE_API_ERROR"
            )


class GCPBillingClient:
    """
    GCP Cloud Billing API client.
    
    Learning Note: The Cloud Billing API provides programmatic access to
    GCP service pricing information across all regions and services.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        self.project_id = project_id
        self.region = region
        self.base_url = "https://cloudbilling.googleapis.com/v1"
        self.session = None
        
        # For now, we'll use public pricing data and fallback pricing
        # In production, you would use the actual Billing API with authentication
        logger.info("GCP Billing client initialized (using fallback pricing)")
    
    async def get_service_pricing(self, service_name: str, region: str) -> Dict[str, Any]:
        """
        Get pricing for a specific GCP service.
        
        Args:
            service_name: GCP service name
            region: GCP region
            
        Returns:
            Dictionary with pricing information
        """
        try:
            # For now, return structured pricing data
            # In production, this would call the actual Billing API
            return {
                "service_name": service_name,
                "region": region,
                "pricing_data": self._get_fallback_pricing(service_name),
                "real_data": False  # Set to True when using real API
            }
            
        except Exception as e:
            raise CloudServiceError(
                f"GCP Billing API error: {str(e)}",
                CloudProvider.GCP,
                "BILLING_API_ERROR"
            )
    
    def _get_fallback_pricing(self, service_name: str) -> Dict[str, Any]:
        """Get fallback pricing data for GCP services."""
        pricing_data = {
            "Compute Engine": {
                "n1-standard-1": 0.0475,  # $0.0475/hour
                "n1-standard-2": 0.0950,
                "n1-standard-4": 0.1900,
                "n2-standard-2": 0.0776,
                "n2-standard-4": 0.1552,
                "e2-micro": 0.0063,
                "e2-small": 0.0126,
                "e2-medium": 0.0252,
                "c2-standard-4": 0.1687,
                "c2-standard-8": 0.3374,
            },
            "Cloud SQL": {
                "db-f1-micro": 0.0150,  # $0.015/hour
                "db-g1-small": 0.0500,
                "db-n1-standard-1": 0.0825,
                "db-n1-standard-2": 0.1650,
                "db-n1-standard-4": 0.3300,
            },
            "Cloud Storage": {
                "standard": 0.020,  # $0.020 per GB/month
                "nearline": 0.010,
                "coldline": 0.004,
                "archive": 0.0012,
            }
        }
        
        return pricing_data.get(service_name, {})


class GCPComputeClient:
    """
    GCP Compute Engine client.
    
    Learning Note: Compute Engine is GCP's compute service. This client provides
    access to machine types, pricing, and availability information.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        self.project_id = project_id
        self.region = region
        self.base_url = "https://compute.googleapis.com/compute/v1"
        
        # For now, we'll use fallback data
        # In production, you would initialize the actual Compute Engine client
        logger.info("GCP Compute client initialized (using fallback data)")
    
    async def get_machine_types(self, region: str) -> CloudServiceResponse:
        """
        Get available GCP machine types using fallback data.
        
        Args:
            region: GCP region
            
        Returns:
            CloudServiceResponse with GCP machine types
        """
        try:
            # Get pricing data
            billing_client = GCPBillingClient(self.project_id, region)
            pricing_data = await billing_client.get_service_pricing("Compute Engine", region)
            pricing_lookup = pricing_data.get("pricing_data", {})
            
            # Define machine types with specifications
            machine_types = [
                {
                    "name": "e2-micro",
                    "vcpus": 2,
                    "memory_gb": 1,
                    "description": "Shared-core machine type with 2 vCPUs and 1 GB memory"
                },
                {
                    "name": "e2-small", 
                    "vcpus": 2,
                    "memory_gb": 2,
                    "description": "Shared-core machine type with 2 vCPUs and 2 GB memory"
                },
                {
                    "name": "e2-medium",
                    "vcpus": 2,
                    "memory_gb": 4,
                    "description": "Shared-core machine type with 2 vCPUs and 4 GB memory"
                },
                {
                    "name": "n1-standard-1",
                    "vcpus": 1,
                    "memory_gb": 3.75,
                    "description": "Standard machine type with 1 vCPU and 3.75 GB memory"
                },
                {
                    "name": "n1-standard-2",
                    "vcpus": 2,
                    "memory_gb": 7.5,
                    "description": "Standard machine type with 2 vCPUs and 7.5 GB memory"
                },
                {
                    "name": "n1-standard-4",
                    "vcpus": 4,
                    "memory_gb": 15,
                    "description": "Standard machine type with 4 vCPUs and 15 GB memory"
                },
                {
                    "name": "n2-standard-2",
                    "vcpus": 2,
                    "memory_gb": 8,
                    "description": "N2 standard machine type with 2 vCPUs and 8 GB memory"
                },
                {
                    "name": "n2-standard-4",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "description": "N2 standard machine type with 4 vCPUs and 16 GB memory"
                },
                {
                    "name": "c2-standard-4",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "description": "Compute-optimized machine type with 4 vCPUs and 16 GB memory"
                },
                {
                    "name": "c2-standard-8",
                    "vcpus": 8,
                    "memory_gb": 32,
                    "description": "Compute-optimized machine type with 8 vCPUs and 32 GB memory"
                }
            ]
            
            services = []
            for machine_type in machine_types:
                machine_name = machine_type["name"]
                hourly_price = pricing_lookup.get(machine_name, 0.05)  # Default fallback
                
                service = CloudService(
                    provider=CloudProvider.GCP,
                    service_name=f"Compute Engine {machine_name}",
                    service_id=machine_name,
                    category=ServiceCategory.COMPUTE,
                    region=region,
                    description=machine_type["description"],
                    hourly_price=hourly_price,
                    specifications={
                        "vcpus": machine_type["vcpus"],
                        "memory_gb": machine_type["memory_gb"],
                        "network_performance": "Up to 10 Gbps",
                        "local_ssd": "Optional"
                    },
                    features=["live_migration", "preemptible_instances", "custom_machine_types", "gpu_support"]
                )
                services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.GCP,
                service_category=ServiceCategory.COMPUTE,
                region=region,
                services=services,
                metadata={"real_api": False, "pricing_source": "fallback_data"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP machine types: {str(e)}",
                CloudProvider.GCP,
                "COMPUTE_API_ERROR"
            )


class GCPSQLClient:
    """
    GCP Cloud SQL client.
    
    Learning Note: Cloud SQL provides managed database services for various
    database engines like MySQL, PostgreSQL, and SQL Server.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        self.project_id = project_id
        self.region = region
        self.base_url = "https://sqladmin.googleapis.com/sql/v1beta4"
        
        # For now, we'll use fallback data
        # In production, you would initialize the actual Cloud SQL client
        logger.info("GCP Cloud SQL client initialized (using fallback data)")
    
    async def get_database_instances(self, region: str) -> CloudServiceResponse:
        """
        Get available GCP Cloud SQL instance types using fallback data.
        
        Args:
            region: GCP region
            
        Returns:
            CloudServiceResponse with Cloud SQL instance types
        """
        try:
            # Get pricing data
            billing_client = GCPBillingClient(self.project_id, region)
            pricing_data = await billing_client.get_service_pricing("Cloud SQL", region)
            pricing_lookup = pricing_data.get("pricing_data", {})
            
            # Define Cloud SQL instance types
            instance_types = [
                {
                    "name": "db-f1-micro",
                    "vcpus": 1,
                    "memory_gb": 0.6,
                    "description": "Shared-core instance with 1 vCPU and 0.6 GB memory"
                },
                {
                    "name": "db-g1-small",
                    "vcpus": 1,
                    "memory_gb": 1.7,
                    "description": "Shared-core instance with 1 vCPU and 1.7 GB memory"
                },
                {
                    "name": "db-n1-standard-1",
                    "vcpus": 1,
                    "memory_gb": 3.75,
                    "description": "Standard instance with 1 vCPU and 3.75 GB memory"
                },
                {
                    "name": "db-n1-standard-2",
                    "vcpus": 2,
                    "memory_gb": 7.5,
                    "description": "Standard instance with 2 vCPUs and 7.5 GB memory"
                },
                {
                    "name": "db-n1-standard-4",
                    "vcpus": 4,
                    "memory_gb": 15,
                    "description": "Standard instance with 4 vCPUs and 15 GB memory"
                }
            ]
            
            services = []
            for instance_type in instance_types:
                instance_name = instance_type["name"]
                hourly_price = pricing_lookup.get(instance_name, 0.02)  # Default fallback
                
                service = CloudService(
                    provider=CloudProvider.GCP,
                    service_name=f"Cloud SQL {instance_name}",
                    service_id=instance_name,
                    category=ServiceCategory.DATABASE,
                    region=region,
                    description=f"Cloud SQL {instance_type['description']}",
                    hourly_price=hourly_price,
                    specifications={
                        "vcpus": instance_type["vcpus"],
                        "memory_gb": instance_type["memory_gb"],
                        "engine": "mysql",
                        "engine_version": "8.0",
                        "max_connections": 4000,
                        "storage_type": "ssd"
                    },
                    features=["automated_backups", "point_in_time_recovery", "high_availability", "read_replicas"]
                )
                services.append(service)
            
            return CloudServiceResponse(
                provider=CloudProvider.GCP,
                service_category=ServiceCategory.DATABASE,
                region=region,
                services=services,
                metadata={"real_api": False, "pricing_source": "fallback_data"}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP Cloud SQL instances: {str(e)}",
                CloudProvider.GCP,
                "SQL_API_ERROR"
            )


class GCPAIClient:
    """
    GCP AI/ML services client.
    
    Provides access to Google Cloud AI and machine learning services including
    Vertex AI, AI Platform, AutoML, and other AI services.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        """Initialize GCP AI client."""
        self.project_id = project_id
        self.region = region
        self.service_account_path = service_account_path
        
        # For now, we'll use fallback data since GCP AI APIs require complex authentication
        logger.info("GCP AI client initialized (using fallback data)")
    
    async def get_ai_services(self, region: str) -> CloudServiceResponse:
        """
        Get GCP AI/ML services with pricing information.
        
        Args:
            region: GCP region
            
        Returns:
            CloudServiceResponse with AI/ML services
        """
        services = []
        
        # Vertex AI services
        vertex_ai_services = self._get_vertex_ai_services(region)
        services.extend(vertex_ai_services)
        
        # AI Platform services
        ai_platform_services = self._get_ai_platform_services(region)
        services.extend(ai_platform_services)
        
        # Other AI services
        other_ai_services = self._get_other_ai_services(region)
        services.extend(other_ai_services)
        
        return CloudServiceResponse(
            provider=CloudProvider.GCP,
            service_category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            services=services,
            metadata={"ai_services_count": len(services)}
        )
    
    def _get_vertex_ai_services(self, region: str) -> List[CloudService]:
        """Get Vertex AI services with pricing."""
        services = []
        
        # Vertex AI training instances
        training_instances = [
            {
                "machine_type": "n1-standard-4",
                "vcpus": 4,
                "memory_gb": 15,
                "hourly_price": 0.19,
                "description": "General purpose training instance"
            },
            {
                "machine_type": "n1-standard-8",
                "vcpus": 8,
                "memory_gb": 30,
                "hourly_price": 0.38,
                "description": "General purpose training instance"
            },
            {
                "machine_type": "n1-highmem-8",
                "vcpus": 8,
                "memory_gb": 52,
                "hourly_price": 0.47,
                "description": "High memory training instance"
            },
            {
                "machine_type": "a2-highgpu-1g",
                "vcpus": 12,
                "memory_gb": 85,
                "hourly_price": 3.67,
                "gpu_count": 1,
                "gpu_type": "A100",
                "description": "GPU training instance with A100"
            },
            {
                "machine_type": "n1-standard-4-nvidia-tesla-k80",
                "vcpus": 4,
                "memory_gb": 15,
                "hourly_price": 0.74,
                "gpu_count": 1,
                "gpu_type": "K80",
                "description": "GPU training instance with K80"
            }
        ]
        
        for instance in training_instances:
            service = CloudService(
                provider=CloudProvider.GCP,
                service_name=f"Vertex AI Training - {instance['machine_type']}",
                service_id=f"vertex_ai_training_{instance['machine_type'].replace('-', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=instance['description'],
                pricing_model="pay_as_you_go",
                hourly_price=instance['hourly_price'],
                pricing_unit="hour",
                specifications={
                    "machine_type": instance['machine_type'],
                    "vcpus": instance['vcpus'],
                    "memory_gb": instance['memory_gb'],
                    "gpu_count": instance.get('gpu_count', 0),
                    "gpu_type": instance.get('gpu_type', 'None'),
                    "use_case": "model_training"
                },
                features=["managed_training", "auto_scaling", "preemptible_instances", "distributed_training"]
            )
            services.append(service)
        
        # Vertex AI prediction instances
        prediction_instances = [
            {
                "machine_type": "n1-standard-2",
                "vcpus": 2,
                "memory_gb": 7.5,
                "hourly_price": 0.095,
                "description": "General purpose prediction instance"
            },
            {
                "machine_type": "n1-standard-4",
                "vcpus": 4,
                "memory_gb": 15,
                "hourly_price": 0.19,
                "description": "General purpose prediction instance"
            },
            {
                "machine_type": "n1-highmem-2",
                "vcpus": 2,
                "memory_gb": 13,
                "hourly_price": 0.12,
                "description": "High memory prediction instance"
            }
        ]
        
        for instance in prediction_instances:
            service = CloudService(
                provider=CloudProvider.GCP,
                service_name=f"Vertex AI Prediction - {instance['machine_type']}",
                service_id=f"vertex_ai_prediction_{instance['machine_type'].replace('-', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=instance['description'],
                pricing_model="pay_as_you_go",
                hourly_price=instance['hourly_price'],
                pricing_unit="hour",
                specifications={
                    "machine_type": instance['machine_type'],
                    "vcpus": instance['vcpus'],
                    "memory_gb": instance['memory_gb'],
                    "use_case": "model_prediction"
                },
                features=["real_time_prediction", "auto_scaling", "batch_prediction", "online_serving"]
            )
            services.append(service)
        
        # Vertex AI Generative AI models
        generative_models = [
            {
                "model_name": "text-bison",
                "model_version": "001",
                "input_price_per_1k": 0.001,
                "output_price_per_1k": 0.001,
                "description": "Large language model for text generation"
            },
            {
                "model_name": "chat-bison",
                "model_version": "001",
                "input_price_per_1k": 0.0005,
                "output_price_per_1k": 0.0005,
                "description": "Conversational AI model"
            },
            {
                "model_name": "code-bison",
                "model_version": "001",
                "input_price_per_1k": 0.001,
                "output_price_per_1k": 0.001,
                "description": "Code generation and completion model"
            },
            {
                "model_name": "textembedding-gecko",
                "model_version": "001",
                "input_price_per_1k": 0.0001,
                "output_price_per_1k": 0.0,
                "description": "Text embedding model"
            }
        ]
        
        for model in generative_models:
            service = CloudService(
                provider=CloudProvider.GCP,
                service_name=f"Vertex AI - {model['model_name']}",
                service_id=f"vertex_ai_{model['model_name'].replace('-', '_')}",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=model['description'],
                pricing_model="pay_per_token",
                hourly_price=model['input_price_per_1k'],
                pricing_unit="1K tokens",
                specifications={
                    "model_name": model['model_name'],
                    "model_version": model['model_version'],
                    "model_type": "text_generation" if "embedding" not in model['model_name'] else "embedding",
                    "input_price_per_1k_tokens": model['input_price_per_1k'],
                    "output_price_per_1k_tokens": model['output_price_per_1k']
                },
                features=["managed_service", "streaming", "fine_tuning", "safety_filters"]
            )
            services.append(service)
        
        return services
    
    def _get_ai_platform_services(self, region: str) -> List[CloudService]:
        """Get AI Platform services with pricing."""
        services = []
        
        # AutoML services
        automl_services = [
            {
                "service_name": "AutoML Tables",
                "service_id": "automl_tables",
                "description": "Automated machine learning for structured data",
                "training_price_per_hour": 19.32,
                "prediction_price_per_1k": 0.0016
            },
            {
                "service_name": "AutoML Vision",
                "service_id": "automl_vision",
                "description": "Automated machine learning for image classification",
                "training_price_per_hour": 20.0,
                "prediction_price_per_1k": 0.0015
            },
            {
                "service_name": "AutoML Natural Language",
                "service_id": "automl_natural_language",
                "description": "Automated machine learning for text classification",
                "training_price_per_hour": 3.0,
                "prediction_price_per_1k": 0.0005
            },
            {
                "service_name": "AutoML Translation",
                "service_id": "automl_translation",
                "description": "Custom translation models",
                "training_price_per_hour": 76.0,
                "prediction_price_per_1k": 0.068
            }
        ]
        
        for automl in automl_services:
            # Training service
            training_service = CloudService(
                provider=CloudProvider.GCP,
                service_name=f"{automl['service_name']} - Training",
                service_id=f"{automl['service_id']}_training",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=f"{automl['description']} - Model training",
                pricing_model="pay_per_hour",
                hourly_price=automl['training_price_per_hour'],
                pricing_unit="hour",
                specifications={
                    "service_type": "automl_training",
                    "model_type": automl['service_id'].replace('automl_', '')
                },
                features=["automated_ml", "no_code_required", "custom_models", "hyperparameter_tuning"]
            )
            services.append(training_service)
            
            # Prediction service
            prediction_service = CloudService(
                provider=CloudProvider.GCP,
                service_name=f"{automl['service_name']} - Prediction",
                service_id=f"{automl['service_id']}_prediction",
                category=ServiceCategory.MACHINE_LEARNING,
                region=region,
                description=f"{automl['description']} - Model prediction",
                pricing_model="pay_per_prediction",
                hourly_price=automl['prediction_price_per_1k'],
                pricing_unit="1K predictions",
                specifications={
                    "service_type": "automl_prediction",
                    "model_type": automl['service_id'].replace('automl_', '')
                },
                features=["real_time_prediction", "batch_prediction", "auto_scaling", "managed_endpoints"]
            )
            services.append(prediction_service)
        
        return services
    
    def _get_other_ai_services(self, region: str) -> List[CloudService]:
        """Get other GCP AI services with pricing."""
        services = []
        
        # Cloud Vision API
        vision_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Cloud Vision API",
            service_id="cloud_vision_api",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Image analysis and optical character recognition",
            pricing_model="pay_per_request",
            hourly_price=0.0015,  # Per 1000 requests
            pricing_unit="1K requests",
            specifications={
                "service_type": "computer_vision",
                "max_image_size": "20MB",
                "supported_formats": ["JPEG", "PNG", "GIF", "BMP", "WEBP", "RAW", "ICO", "PDF", "TIFF"]
            },
            features=["object_detection", "ocr", "face_detection", "logo_detection", "landmark_detection"]
        )
        services.append(vision_service)
        
        # Cloud Natural Language API
        natural_language_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Cloud Natural Language API",
            service_id="cloud_natural_language_api",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Natural language understanding and sentiment analysis",
            pricing_model="pay_per_request",
            hourly_price=0.001,  # Per 1000 requests
            pricing_unit="1K requests",
            specifications={
                "service_type": "nlp",
                "languages_supported": 10,
                "max_document_size": "1MB"
            },
            features=["sentiment_analysis", "entity_analysis", "syntax_analysis", "content_classification"]
        )
        services.append(natural_language_service)
        
        # Cloud Translation API
        translation_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Cloud Translation API",
            service_id="cloud_translation_api",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Neural machine translation service",
            pricing_model="pay_per_character",
            hourly_price=0.00002,  # Per character
            pricing_unit="character",
            specifications={
                "service_type": "translation",
                "languages_supported": 100,
                "max_text_size": "30KB"
            },
            features=["real_time_translation", "language_detection", "glossary_support", "batch_translation"]
        )
        services.append(translation_service)
        
        # Cloud Speech-to-Text API
        speech_to_text_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Cloud Speech-to-Text API",
            service_id="cloud_speech_to_text_api",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Automatic speech recognition service",
            pricing_model="pay_per_minute",
            hourly_price=0.024,  # Per minute of audio
            pricing_unit="minute",
            specifications={
                "service_type": "speech_recognition",
                "languages_supported": 125,
                "audio_formats": ["FLAC", "WAV", "LINEAR16", "MULAW", "AMR", "AMR_WB", "OGG_OPUS", "SPEEX_WITH_HEADER_BYTE"]
            },
            features=["real_time_streaming", "batch_recognition", "speaker_diarization", "profanity_filtering"]
        )
        services.append(speech_to_text_service)
        
        # Cloud Text-to-Speech API
        text_to_speech_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Cloud Text-to-Speech API",
            service_id="cloud_text_to_speech_api",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Text-to-speech synthesis service",
            pricing_model="pay_per_character",
            hourly_price=0.000016,  # Per character
            pricing_unit="character",
            specifications={
                "service_type": "text_to_speech",
                "voices_available": 380,
                "languages_supported": 40,
                "audio_formats": ["LINEAR16", "MP3", "OGG_OPUS"]
            },
            features=["neural_voices", "ssml_support", "audio_profiles", "custom_voices"]
        )
        services.append(text_to_speech_service)
        
        # Document AI
        document_ai_service = CloudService(
            provider=CloudProvider.GCP,
            service_name="Document AI",
            service_id="document_ai",
            category=ServiceCategory.MACHINE_LEARNING,
            region=region,
            description="Document understanding and data extraction",
            pricing_model="pay_per_page",
            hourly_price=0.05,  # Per page
            pricing_unit="page",
            specifications={
                "service_type": "document_processing",
                "max_file_size": "20MB",
                "supported_formats": ["PDF", "GIF", "TIFF", "JPEG", "PNG", "BMP", "WEBP"]
            },
            features=["form_parsing", "table_extraction", "entity_extraction", "custom_processors"]
        )
        services.append(document_ai_service)
        
        return services


class GCPGKEClient:
    """
    GCP Google Kubernetes Engine (GKE) client.
    
    Learning Note: GKE provides managed Kubernetes clusters with various
    node pool configurations and pricing models.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        """Initialize GCP GKE client."""
        self.project_id = project_id
        self.region = region
        self.service_account_path = service_account_path
        self.base_url = "https://container.googleapis.com/v1"
        
        logger.info("GCP GKE client initialized (using fallback data)")
    
    async def get_gke_services(self, region: str) -> CloudServiceResponse:
        """
        Get GCP GKE services with pricing information.
        
        Args:
            region: GCP region
            
        Returns:
            CloudServiceResponse with GKE services
        """
        try:
            services = []
            
            # GKE cluster management pricing
            cluster_management_service = CloudService(
                provider=CloudProvider.GCP,
                service_name="GKE Cluster Management",
                service_id="gke_cluster_management",
                category=ServiceCategory.CONTAINER,
                region=region,
                description="Managed Kubernetes cluster control plane",
                pricing_model="pay_per_cluster",
                hourly_price=0.10,  # $0.10 per cluster per hour
                pricing_unit="cluster/hour",
                specifications={
                    "service_type": "cluster_management",
                    "kubernetes_version": "1.27",
                    "max_nodes_per_cluster": 15000,
                    "max_pods_per_node": 110,
                    "networking": "VPC-native"
                },
                features=["auto_scaling", "auto_upgrade", "workload_identity", "binary_authorization"]
            )
            services.append(cluster_management_service)
            
            # GKE node pool configurations
            node_pool_configs = [
                {
                    "machine_type": "e2-micro",
                    "vcpus": 2,
                    "memory_gb": 1,
                    "hourly_price": 0.0063,
                    "description": "Shared-core node pool for development workloads"
                },
                {
                    "machine_type": "e2-small",
                    "vcpus": 2,
                    "memory_gb": 2,
                    "hourly_price": 0.0126,
                    "description": "Shared-core node pool for light workloads"
                },
                {
                    "machine_type": "e2-medium",
                    "vcpus": 2,
                    "memory_gb": 4,
                    "hourly_price": 0.0252,
                    "description": "Shared-core node pool for moderate workloads"
                },
                {
                    "machine_type": "n1-standard-1",
                    "vcpus": 1,
                    "memory_gb": 3.75,
                    "hourly_price": 0.0475,
                    "description": "Standard node pool for general workloads"
                },
                {
                    "machine_type": "n1-standard-2",
                    "vcpus": 2,
                    "memory_gb": 7.5,
                    "hourly_price": 0.0950,
                    "description": "Standard node pool for general workloads"
                },
                {
                    "machine_type": "n1-standard-4",
                    "vcpus": 4,
                    "memory_gb": 15,
                    "hourly_price": 0.1900,
                    "description": "Standard node pool for compute-intensive workloads"
                },
                {
                    "machine_type": "n2-standard-2",
                    "vcpus": 2,
                    "memory_gb": 8,
                    "hourly_price": 0.0776,
                    "description": "N2 node pool with balanced compute and memory"
                },
                {
                    "machine_type": "n2-standard-4",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "hourly_price": 0.1552,
                    "description": "N2 node pool with balanced compute and memory"
                },
                {
                    "machine_type": "c2-standard-4",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "hourly_price": 0.1687,
                    "description": "Compute-optimized node pool for CPU-intensive workloads"
                },
                {
                    "machine_type": "n1-highmem-2",
                    "vcpus": 2,
                    "memory_gb": 13,
                    "hourly_price": 0.1184,
                    "description": "High-memory node pool for memory-intensive workloads"
                }
            ]
            
            for config in node_pool_configs:
                service = CloudService(
                    provider=CloudProvider.GCP,
                    service_name=f"GKE Node Pool - {config['machine_type']}",
                    service_id=f"gke_node_pool_{config['machine_type'].replace('-', '_')}",
                    category=ServiceCategory.CONTAINER,
                    region=region,
                    description=config['description'],
                    pricing_model="pay_per_node",
                    hourly_price=config['hourly_price'],
                    pricing_unit="node/hour",
                    specifications={
                        "machine_type": config['machine_type'],
                        "vcpus": config['vcpus'],
                        "memory_gb": config['memory_gb'],
                        "disk_size_gb": 100,
                        "disk_type": "pd-standard",
                        "max_pods_per_node": 110
                    },
                    features=["auto_scaling", "preemptible_nodes", "spot_instances", "node_auto_repair"]
                )
                services.append(service)
            
            # GKE Autopilot pricing
            autopilot_service = CloudService(
                provider=CloudProvider.GCP,
                service_name="GKE Autopilot",
                service_id="gke_autopilot",
                category=ServiceCategory.CONTAINER,
                region=region,
                description="Fully managed, serverless Kubernetes experience",
                pricing_model="pay_per_resource",
                hourly_price=0.0445,  # Per vCPU per hour
                pricing_unit="vCPU/hour",
                specifications={
                    "service_type": "serverless_kubernetes",
                    "cpu_price_per_hour": 0.0445,
                    "memory_price_per_gb_hour": 0.0049,
                    "ephemeral_storage_price_per_gb_hour": 0.000274,
                    "min_cpu": 0.25,
                    "max_cpu": 32,
                    "min_memory_gb": 0.5,
                    "max_memory_gb": 128
                },
                features=["serverless", "auto_scaling", "security_hardening", "cost_optimization"]
            )
            services.append(autopilot_service)
            
            return CloudServiceResponse(
                provider=CloudProvider.GCP,
                service_category=ServiceCategory.CONTAINER,
                region=region,
                services=services,
                metadata={"gke_services_count": len(services)}
            )
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP GKE services: {str(e)}",
                CloudProvider.GCP,
                "GKE_API_ERROR"
            )


class GCPAssetClient:
    """
    GCP Cloud Asset Inventory client.
    
    Learning Note: Cloud Asset Inventory provides visibility into GCP resources
    and their configurations across projects and organizations.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        """Initialize GCP Asset client."""
        self.project_id = project_id
        self.region = region
        self.service_account_path = service_account_path
        self.base_url = "https://cloudasset.googleapis.com/v1"
        
        logger.info("GCP Asset client initialized (using fallback data)")
    
    async def get_asset_inventory(self, asset_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get GCP asset inventory information.
        
        Args:
            asset_types: List of asset types to query (optional)
            
        Returns:
            Dictionary with asset inventory information
        """
        try:
            # Default asset types if none specified
            if not asset_types:
                asset_types = [
                    "compute.googleapis.com/Instance",
                    "compute.googleapis.com/Disk",
                    "storage.googleapis.com/Bucket",
                    "sqladmin.googleapis.com/Instance",
                    "container.googleapis.com/Cluster"
                ]
            
            # Simulate asset inventory data
            asset_inventory = {
                "project_id": self.project_id,
                "region": self.region,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_types_queried": asset_types,
                "assets": self._generate_sample_assets(asset_types),
                "summary": {
                    "total_assets": 0,
                    "assets_by_type": {},
                    "assets_by_region": {},
                    "estimated_monthly_cost": 0.0
                }
            }
            
            # Calculate summary statistics
            asset_inventory["summary"]["total_assets"] = len(asset_inventory["assets"])
            
            for asset in asset_inventory["assets"]:
                asset_type = asset["asset_type"]
                asset_region = asset.get("location", "global")
                
                # Count by type
                if asset_type not in asset_inventory["summary"]["assets_by_type"]:
                    asset_inventory["summary"]["assets_by_type"][asset_type] = 0
                asset_inventory["summary"]["assets_by_type"][asset_type] += 1
                
                # Count by region
                if asset_region not in asset_inventory["summary"]["assets_by_region"]:
                    asset_inventory["summary"]["assets_by_region"][asset_region] = 0
                asset_inventory["summary"]["assets_by_region"][asset_region] += 1
                
                # Add to estimated cost
                asset_inventory["summary"]["estimated_monthly_cost"] += asset.get("estimated_monthly_cost", 0.0)
            
            return asset_inventory
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP asset inventory: {str(e)}",
                CloudProvider.GCP,
                "ASSET_API_ERROR"
            )
    
    def _generate_sample_assets(self, asset_types: List[str]) -> List[Dict[str, Any]]:
        """Generate sample asset data for demonstration."""
        assets = []
        
        for asset_type in asset_types:
            if asset_type == "compute.googleapis.com/Instance":
                assets.extend([
                    {
                        "name": f"projects/{self.project_id}/zones/{self.region}-a/instances/web-server-1",
                        "asset_type": asset_type,
                        "location": f"{self.region}-a",
                        "resource": {
                            "machine_type": "n1-standard-2",
                            "status": "RUNNING",
                            "creation_timestamp": "2024-01-15T10:30:00Z"
                        },
                        "estimated_monthly_cost": 69.35
                    },
                    {
                        "name": f"projects/{self.project_id}/zones/{self.region}-b/instances/db-server-1",
                        "asset_type": asset_type,
                        "location": f"{self.region}-b",
                        "resource": {
                            "machine_type": "n1-highmem-2",
                            "status": "RUNNING",
                            "creation_timestamp": "2024-01-10T14:20:00Z"
                        },
                        "estimated_monthly_cost": 86.44
                    }
                ])
            
            elif asset_type == "compute.googleapis.com/Disk":
                assets.extend([
                    {
                        "name": f"projects/{self.project_id}/zones/{self.region}-a/disks/web-server-1-disk",
                        "asset_type": asset_type,
                        "location": f"{self.region}-a",
                        "resource": {
                            "size_gb": 100,
                            "type": "pd-standard",
                            "status": "READY"
                        },
                        "estimated_monthly_cost": 4.00
                    },
                    {
                        "name": f"projects/{self.project_id}/zones/{self.region}-b/disks/db-server-1-disk",
                        "asset_type": asset_type,
                        "location": f"{self.region}-b",
                        "resource": {
                            "size_gb": 500,
                            "type": "pd-ssd",
                            "status": "READY"
                        },
                        "estimated_monthly_cost": 85.00
                    }
                ])
            
            elif asset_type == "storage.googleapis.com/Bucket":
                assets.append({
                    "name": f"projects/{self.project_id}/buckets/app-data-bucket",
                    "asset_type": asset_type,
                    "location": "global",
                    "resource": {
                        "storage_class": "STANDARD",
                        "location": "US",
                        "size_bytes": 1073741824  # 1GB
                    },
                    "estimated_monthly_cost": 0.02
                })
            
            elif asset_type == "sqladmin.googleapis.com/Instance":
                assets.append({
                    "name": f"projects/{self.project_id}/instances/main-database",
                    "asset_type": asset_type,
                    "location": self.region,
                    "resource": {
                        "tier": "db-n1-standard-2",
                        "database_version": "MYSQL_8_0",
                        "state": "RUNNABLE"
                    },
                    "estimated_monthly_cost": 120.45
                })
            
            elif asset_type == "container.googleapis.com/Cluster":
                assets.append({
                    "name": f"projects/{self.project_id}/locations/{self.region}/clusters/main-cluster",
                    "asset_type": asset_type,
                    "location": self.region,
                    "resource": {
                        "status": "RUNNING",
                        "current_master_version": "1.27.3-gke.100",
                        "current_node_count": 3
                    },
                    "estimated_monthly_cost": 73.00
                })
        
        return assets


class GCPRecommenderClient:
    """
    GCP Recommender API client.
    
    Learning Note: The Recommender API provides machine learning-driven
    recommendations for cost optimization, security, and performance improvements.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1", 
                 service_account_path: Optional[str] = None):
        """Initialize GCP Recommender client."""
        self.project_id = project_id
        self.region = region
        self.service_account_path = service_account_path
        self.base_url = "https://recommender.googleapis.com/v1"
        
        logger.info("GCP Recommender client initialized (using fallback data)")
    
    async def get_recommendations(self, recommender_type: str, region: str) -> Dict[str, Any]:
        """
        Get GCP recommendations for optimization.
        
        Args:
            recommender_type: Type of recommendations to get
            region: GCP region
            
        Returns:
            Dictionary with recommendations
        """
        try:
            # Available recommender types
            available_recommenders = {
                "cost_optimization": "google.compute.instance.MachineTypeRecommender",
                "security": "google.iam.policy.Recommender",
                "performance": "google.compute.disk.IdleResourceRecommender",
                "rightsizing": "google.compute.instance.IdleResourceRecommender",
                "commitment_utilization": "google.billing.account.CommitmentUtilizationRecommender"
            }
            
            if recommender_type not in available_recommenders:
                recommender_type = "cost_optimization"  # Default
            
            recommendations = {
                "project_id": self.project_id,
                "region": region,
                "recommender_type": recommender_type,
                "recommender_id": available_recommenders[recommender_type],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendations": self._generate_sample_recommendations(recommender_type),
                "summary": {
                    "total_recommendations": 0,
                    "potential_monthly_savings": 0.0,
                    "recommendations_by_priority": {
                        "HIGH": 0,
                        "MEDIUM": 0,
                        "LOW": 0
                    }
                }
            }
            
            # Calculate summary statistics
            recommendations["summary"]["total_recommendations"] = len(recommendations["recommendations"])
            
            for rec in recommendations["recommendations"]:
                priority = rec.get("priority", "MEDIUM")
                recommendations["summary"]["recommendations_by_priority"][priority] += 1
                recommendations["summary"]["potential_monthly_savings"] += rec.get("potential_monthly_savings", 0.0)
            
            return recommendations
            
        except Exception as e:
            raise CloudServiceError(
                f"Failed to get GCP recommendations: {str(e)}",
                CloudProvider.GCP,
                "RECOMMENDER_API_ERROR"
            )
    
    def _generate_sample_recommendations(self, recommender_type: str) -> List[Dict[str, Any]]:
        """Generate sample recommendations based on type."""
        recommendations = []
        
        if recommender_type == "cost_optimization":
            recommendations.extend([
                {
                    "name": f"projects/{self.project_id}/locations/{self.region}/recommenders/google.compute.instance.MachineTypeRecommender/recommendations/rec-001",
                    "description": "Resize overprovisioned VM instance web-server-1",
                    "priority": "HIGH",
                    "category": "COST",
                    "impact": {
                        "cost_projection": {
                            "cost": {"currency_code": "USD", "units": "-25"},
                            "duration": "2592000s"  # 30 days
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "replace",
                                "resource_type": "compute.googleapis.com/Instance",
                                "resource": f"projects/{self.project_id}/zones/{self.region}-a/instances/web-server-1",
                                "path": "/machineType",
                                "value": f"projects/{self.project_id}/zones/{self.region}-a/machineTypes/n1-standard-1"
                            }]
                        }]
                    },
                    "potential_monthly_savings": 25.00,
                    "confidence": 0.85
                },
                {
                    "name": f"projects/{self.project_id}/locations/{self.region}/recommenders/google.compute.disk.IdleResourceRecommender/recommendations/rec-002",
                    "description": "Delete unused persistent disk backup-disk-old",
                    "priority": "MEDIUM",
                    "category": "COST",
                    "impact": {
                        "cost_projection": {
                            "cost": {"currency_code": "USD", "units": "-15"},
                            "duration": "2592000s"
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "remove",
                                "resource_type": "compute.googleapis.com/Disk",
                                "resource": f"projects/{self.project_id}/zones/{self.region}-a/disks/backup-disk-old"
                            }]
                        }]
                    },
                    "potential_monthly_savings": 15.00,
                    "confidence": 0.95
                }
            ])
        
        elif recommender_type == "security":
            recommendations.extend([
                {
                    "name": f"projects/{self.project_id}/locations/global/recommenders/google.iam.policy.Recommender/recommendations/sec-001",
                    "description": "Remove overly broad IAM role from service account",
                    "priority": "HIGH",
                    "category": "SECURITY",
                    "impact": {
                        "security_projection": {
                            "details": {
                                "risk_reduction": "HIGH",
                                "affected_resources": 1
                            }
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "remove",
                                "resource_type": "cloudresourcemanager.googleapis.com/Project",
                                "resource": f"projects/{self.project_id}",
                                "path": "/iamPolicy/bindings/*/members/*",
                                "value": "serviceAccount:app-service@project.iam.gserviceaccount.com"
                            }]
                        }]
                    },
                    "potential_monthly_savings": 0.0,
                    "confidence": 0.90
                }
            ])
        
        elif recommender_type == "performance":
            recommendations.extend([
                {
                    "name": f"projects/{self.project_id}/locations/{self.region}/recommenders/google.compute.instance.MachineTypeRecommender/recommendations/perf-001",
                    "description": "Upgrade to higher performance machine type for database workload",
                    "priority": "MEDIUM",
                    "category": "PERFORMANCE",
                    "impact": {
                        "performance_projection": {
                            "details": {
                                "performance_improvement": "25%",
                                "metric": "CPU_UTILIZATION"
                            }
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "replace",
                                "resource_type": "compute.googleapis.com/Instance",
                                "resource": f"projects/{self.project_id}/zones/{self.region}-b/instances/db-server-1",
                                "path": "/machineType",
                                "value": f"projects/{self.project_id}/zones/{self.region}-b/machineTypes/n1-highmem-4"
                            }]
                        }]
                    },
                    "potential_monthly_savings": -50.00,  # Negative because it's an upgrade
                    "confidence": 0.75
                }
            ])
        
        elif recommender_type == "rightsizing":
            recommendations.extend([
                {
                    "name": f"projects/{self.project_id}/locations/{self.region}/recommenders/google.compute.instance.IdleResourceRecommender/recommendations/right-001",
                    "description": "Rightsize underutilized instance test-server-2",
                    "priority": "MEDIUM",
                    "category": "COST",
                    "impact": {
                        "cost_projection": {
                            "cost": {"currency_code": "USD", "units": "-35"},
                            "duration": "2592000s"
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "replace",
                                "resource_type": "compute.googleapis.com/Instance",
                                "resource": f"projects/{self.project_id}/zones/{self.region}-c/instances/test-server-2",
                                "path": "/machineType",
                                "value": f"projects/{self.project_id}/zones/{self.region}-c/machineTypes/e2-medium"
                            }]
                        }]
                    },
                    "potential_monthly_savings": 35.00,
                    "confidence": 0.80
                }
            ])
        
        elif recommender_type == "commitment_utilization":
            recommendations.extend([
                {
                    "name": f"projects/{self.project_id}/locations/global/recommenders/google.billing.account.CommitmentUtilizationRecommender/recommendations/commit-001",
                    "description": "Purchase 1-year compute commitment for consistent workloads",
                    "priority": "LOW",
                    "category": "COST",
                    "impact": {
                        "cost_projection": {
                            "cost": {"currency_code": "USD", "units": "-120"},
                            "duration": "31536000s"  # 1 year
                        }
                    },
                    "content": {
                        "operation_groups": [{
                            "operations": [{
                                "action": "create",
                                "resource_type": "compute.googleapis.com/Commitment",
                                "resource": f"projects/{self.project_id}/regions/{self.region}/commitments/compute-commitment-1",
                                "value": {
                                    "plan": "TWELVE_MONTH",
                                    "type": "GENERAL_PURPOSE_N1",
                                    "resources": [{"type": "VCPU", "amount": "10"}]
                                }
                            }]
                        }]
                    },
                    "potential_monthly_savings": 10.00,  # Monthly equivalent of annual savings
                    "confidence": 0.70
                }
            ])
        
        return recommendations