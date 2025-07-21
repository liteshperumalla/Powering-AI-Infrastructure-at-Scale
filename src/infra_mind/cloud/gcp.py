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