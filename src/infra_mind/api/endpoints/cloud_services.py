"""
Cloud Services endpoints for Infra Mind.

Provides comprehensive cloud services catalog and comparison functionality.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter()


class CloudProvider(str, Enum):
    AWS = "AWS"
    AZURE = "Azure"
    GCP = "GCP"
    ALIBABA = "Alibaba"
    IBM = "IBM"


class ServiceCategory(str, Enum):
    COMPUTE = "Compute"
    DATABASE = "Database"
    STORAGE = "Storage"
    NETWORKING = "Networking"
    SECURITY = "Security"
    AI_ML = "AI/ML"
    ANALYTICS = "Analytics"
    CONTAINERS = "Containers"
    SERVERLESS = "Serverless"
    MANAGEMENT = "Management"


# Comprehensive cloud services database
CLOUD_SERVICES_DB = [
    # AWS Compute Services
    {
        "id": "aws-ec2",
        "name": "Amazon EC2",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.COMPUTE,
        "description": "Scalable virtual servers in the cloud with flexible configurations",
        "pricing": {"model": "On-Demand", "starting_price": 0.0116, "unit": "per hour"},
        "features": ["Auto Scaling", "Load Balancing", "Security Groups", "Spot Instances", "Reserved Instances"],
        "rating": 4.5,
        "compliance": ["SOC 2", "HIPAA", "PCI DSS", "FedRAMP", "ISO 27001"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ca-central-1"],
        "use_cases": ["Web applications", "High-performance computing", "Enterprise applications"],
        "integration": ["CloudWatch", "ELB", "Auto Scaling", "VPC"],
        "managed": False
    },
    {
        "id": "aws-lambda",
        "name": "AWS Lambda",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.SERVERLESS,
        "description": "Run code without thinking about servers, pay only for compute time consumed",
        "pricing": {"model": "Pay-per-request", "starting_price": 0.0000002, "unit": "per request"},
        "features": ["Event-driven", "Auto-scaling", "Built-in fault tolerance", "No server management"],
        "rating": 4.6,
        "compliance": ["SOC 2", "HIPAA", "PCI DSS", "FedRAMP"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "use_cases": ["API backends", "Data processing", "Real-time file processing"],
        "integration": ["API Gateway", "DynamoDB", "S3", "CloudWatch"],
        "managed": True
    },
    {
        "id": "aws-ecs",
        "name": "Amazon ECS",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.CONTAINERS,
        "description": "Highly scalable, high-performance container orchestration service",
        "pricing": {"model": "EC2 pricing", "starting_price": 0.0, "unit": "no additional charges"},
        "features": ["Docker support", "Service discovery", "Load balancing", "Task placement"],
        "rating": 4.4,
        "compliance": ["SOC 2", "HIPAA", "PCI DSS"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "use_cases": ["Microservices", "Batch processing", "Web applications"],
        "integration": ["ECR", "ELB", "CloudWatch", "IAM"],
        "managed": True
    },
    
    # AWS Database Services
    {
        "id": "aws-rds",
        "name": "Amazon RDS",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.DATABASE,
        "description": "Managed relational database service supporting multiple engines",
        "pricing": {"model": "On-Demand", "starting_price": 0.025, "unit": "per hour"},
        "features": ["Automated Backups", "Multi-AZ", "Read Replicas", "Point-in-time recovery"],
        "rating": 4.6,
        "compliance": ["HIPAA", "PCI DSS", "SOC 2", "FedRAMP"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "use_cases": ["Web applications", "E-commerce", "Enterprise applications"],
        "integration": ["CloudWatch", "IAM", "VPC", "KMS"],
        "managed": True
    },
    {
        "id": "aws-dynamodb",
        "name": "Amazon DynamoDB",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.DATABASE,
        "description": "Fast and flexible NoSQL database service for any scale",
        "pricing": {"model": "On-Demand", "starting_price": 1.25, "unit": "per million requests"},
        "features": ["Global Tables", "Auto Scaling", "Point-in-time recovery", "Encryption at rest"],
        "rating": 4.5,
        "compliance": ["HIPAA", "PCI DSS", "SOC 2", "FedRAMP"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "use_cases": ["Mobile apps", "Gaming", "IoT", "Real-time analytics"],
        "integration": ["Lambda", "API Gateway", "CloudWatch", "IAM"],
        "managed": True
    },
    
    # AWS Storage Services
    {
        "id": "aws-s3",
        "name": "Amazon S3",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.STORAGE,
        "description": "Scalable object storage with 99.999999999% durability",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.023, "unit": "per GB/month"},
        "features": ["Intelligent Tiering", "Lifecycle policies", "Cross-region replication", "Event notifications"],
        "rating": 4.7,
        "compliance": ["HIPAA", "PCI DSS", "SOC 2", "FedRAMP", "GDPR"],
        "region_availability": ["Global"],
        "use_cases": ["Data backup", "Static websites", "Data archiving", "Content distribution"],
        "integration": ["CloudFront", "Lambda", "CloudWatch", "IAM"],
        "managed": True
    },
    
    # Azure Services
    {
        "id": "azure-vm",
        "name": "Azure Virtual Machines",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.COMPUTE,
        "description": "On-demand, scalable computing resources with Azure infrastructure",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.012, "unit": "per hour"},
        "features": ["Hybrid Cloud", "Azure AD Integration", "Backup", "Site Recovery"],
        "rating": 4.3,
        "compliance": ["ISO 27001", "GDPR", "HIPAA", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia", "Australia East"],
        "use_cases": ["Enterprise applications", "Development and testing", "Disaster recovery"],
        "integration": ["Azure Monitor", "Azure AD", "Azure Backup"],
        "managed": False
    },
    {
        "id": "azure-functions",
        "name": "Azure Functions",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.SERVERLESS,
        "description": "Event-driven serverless compute platform",
        "pricing": {"model": "Consumption", "starting_price": 0.000016, "unit": "per execution"},
        "features": ["Event-driven", "Multiple languages", "Integrated security", "DevOps integration"],
        "rating": 4.4,
        "compliance": ["ISO 27001", "GDPR", "HIPAA", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia"],
        "use_cases": ["API backends", "Data processing", "IoT data processing"],
        "integration": ["Logic Apps", "Event Grid", "Service Bus"],
        "managed": True
    },
    {
        "id": "azure-sql",
        "name": "Azure SQL Database",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.DATABASE,
        "description": "Fully managed SQL database with AI-powered performance optimization",
        "pricing": {"model": "vCore-based", "starting_price": 0.52, "unit": "per vCore/hour"},
        "features": ["Auto-tuning", "Threat Detection", "Geo-replication", "Elastic pools"],
        "rating": 4.4,
        "compliance": ["GDPR", "HIPAA", "ISO 27001", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia"],
        "use_cases": ["Web applications", "SaaS applications", "Data warehousing"],
        "integration": ["Azure Monitor", "Azure AD", "Power BI"],
        "managed": True
    },
    {
        "id": "azure-storage",
        "name": "Azure Blob Storage",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.STORAGE,
        "description": "Massively scalable object storage for unstructured data",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.018, "unit": "per GB/month"},
        "features": ["Hot/Cool/Archive tiers", "Lifecycle management", "Geo-redundancy", "Encryption"],
        "rating": 4.3,
        "compliance": ["GDPR", "HIPAA", "ISO 27001", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia"],
        "use_cases": ["Data backup", "Content storage", "Data archiving"],
        "integration": ["Azure CDN", "Azure Search", "Power BI"],
        "managed": True
    },
    
    # Google Cloud Services
    {
        "id": "gcp-compute-engine",
        "name": "Google Compute Engine",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.COMPUTE,
        "description": "High-performance virtual machines with live migration and custom machine types",
        "pricing": {"model": "Per-second billing", "starting_price": 0.010, "unit": "per hour"},
        "features": ["Live Migration", "Custom Machine Types", "Preemptible VMs", "Sustained use discounts"],
        "rating": 4.4,
        "compliance": ["ISO 27001", "SOC 2", "PCI DSS", "HIPAA"],
        "region_availability": ["us-central1", "europe-west1", "asia-east1", "australia-southeast1"],
        "use_cases": ["General computing", "High-performance computing", "Machine learning"],
        "integration": ["Cloud Monitoring", "Cloud IAM", "VPC"],
        "managed": False
    },
    {
        "id": "gcp-cloud-functions",
        "name": "Google Cloud Functions",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.SERVERLESS,
        "description": "Event-driven serverless compute platform",
        "pricing": {"model": "Pay-per-use", "starting_price": 0.0000004, "unit": "per invocation"},
        "features": ["Event-driven", "Auto-scaling", "No server management", "Integrated monitoring"],
        "rating": 4.3,
        "compliance": ["ISO 27001", "SOC 2", "PCI DSS"],
        "region_availability": ["us-central1", "europe-west1", "asia-east1"],
        "use_cases": ["API backends", "Data processing", "Mobile backends"],
        "integration": ["Cloud Pub/Sub", "Cloud Storage", "Firestore"],
        "managed": True
    },
    {
        "id": "gcp-cloud-sql",
        "name": "Google Cloud SQL",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.DATABASE,
        "description": "Fully managed relational database service for MySQL, PostgreSQL, and SQL Server",
        "pricing": {"model": "Per-minute billing", "starting_price": 0.0275, "unit": "per hour"},
        "features": ["Automatic Scaling", "High Availability", "Point-in-time Recovery", "Automated backups"],
        "rating": 4.3,
        "compliance": ["ISO 27001", "SOC 2", "HIPAA", "PCI DSS"],
        "region_availability": ["us-central1", "europe-west1", "asia-east1"],
        "use_cases": ["Web applications", "E-commerce", "Content management"],
        "integration": ["Cloud Monitoring", "Cloud IAM", "App Engine"],
        "managed": True
    },
    {
        "id": "gcp-cloud-storage",
        "name": "Google Cloud Storage",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.STORAGE,
        "description": "Unified object storage for developers and enterprises",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.020, "unit": "per GB/month"},
        "features": ["Multi-regional", "Lifecycle management", "Object versioning", "IAM integration"],
        "rating": 4.5,
        "compliance": ["ISO 27001", "SOC 2", "HIPAA", "PCI DSS"],
        "region_availability": ["Global"],
        "use_cases": ["Data backup", "Content delivery", "Data analytics"],
        "integration": ["BigQuery", "Cloud CDN", "Cloud AI"],
        "managed": True
    },
    
    # AI/ML Services
    {
        "id": "aws-sagemaker",
        "name": "Amazon SageMaker",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.AI_ML,
        "description": "Fully managed machine learning service",
        "pricing": {"model": "Pay-per-use", "starting_price": 0.0464, "unit": "per hour"},
        "features": ["Built-in algorithms", "Model hosting", "Auto ML", "Model monitoring"],
        "rating": 4.4,
        "compliance": ["HIPAA", "SOC 2", "PCI DSS"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1"],
        "use_cases": ["Machine learning", "Data science", "Predictive analytics"],
        "integration": ["S3", "EC2", "Lambda", "CloudWatch"],
        "managed": True
    },
    {
        "id": "azure-ml",
        "name": "Azure Machine Learning",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.AI_ML,
        "description": "Cloud-based machine learning service",
        "pricing": {"model": "Pay-per-use", "starting_price": 0.10, "unit": "per hour"},
        "features": ["AutoML", "Designer", "MLOps", "Model deployment"],
        "rating": 4.2,
        "compliance": ["ISO 27001", "HIPAA", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia"],
        "use_cases": ["Machine learning", "Data science", "AI applications"],
        "integration": ["Azure Databricks", "Power BI", "Azure Synapse"],
        "managed": True
    },
    {
        "id": "gcp-ai-platform",
        "name": "Google AI Platform",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.AI_ML,
        "description": "Managed machine learning platform",
        "pricing": {"model": "Pay-per-use", "starting_price": 0.054, "unit": "per hour"},
        "features": ["AutoML", "Custom training", "Prediction serving", "Hyperparameter tuning"],
        "rating": 4.3,
        "compliance": ["ISO 27001", "SOC 2", "HIPAA"],
        "region_availability": ["us-central1", "europe-west1", "asia-east1"],
        "use_cases": ["Machine learning", "Deep learning", "AI applications"],
        "integration": ["BigQuery", "Cloud Storage", "TensorFlow"],
        "managed": True
    },
    
    # Container Services
    {
        "id": "aws-eks",
        "name": "Amazon EKS",
        "provider": CloudProvider.AWS,
        "category": ServiceCategory.CONTAINERS,
        "description": "Managed Kubernetes service",
        "pricing": {"model": "Cluster pricing", "starting_price": 0.10, "unit": "per cluster/hour"},
        "features": ["Managed control plane", "Auto-scaling", "Security", "Monitoring"],
        "rating": 4.3,
        "compliance": ["SOC 2", "HIPAA", "PCI DSS"],
        "region_availability": ["us-east-1", "us-west-2", "eu-west-1"],
        "use_cases": ["Microservices", "Container orchestration", "Cloud-native apps"],
        "integration": ["ECR", "CloudWatch", "IAM", "VPC"],
        "managed": True
    },
    {
        "id": "azure-aks",
        "name": "Azure Kubernetes Service",
        "provider": CloudProvider.AZURE,
        "category": ServiceCategory.CONTAINERS,
        "description": "Managed Kubernetes service",
        "pricing": {"model": "Node pricing", "starting_price": 0.0, "unit": "management free"},
        "features": ["Managed control plane", "Azure AD integration", "DevOps integration", "Monitoring"],
        "rating": 4.2,
        "compliance": ["ISO 27001", "HIPAA", "SOC 2"],
        "region_availability": ["East US", "West Europe", "Southeast Asia"],
        "use_cases": ["Microservices", "Container orchestration", "DevOps"],
        "integration": ["Azure Container Registry", "Azure Monitor", "Azure DevOps"],
        "managed": True
    },
    {
        "id": "gcp-gke",
        "name": "Google Kubernetes Engine",
        "provider": CloudProvider.GCP,
        "category": ServiceCategory.CONTAINERS,
        "description": "Managed Kubernetes service",
        "pricing": {"model": "Cluster pricing", "starting_price": 0.10, "unit": "per cluster/hour"},
        "features": ["Auto-scaling", "Auto-repair", "Release channels", "Workload identity"],
        "rating": 4.4,
        "compliance": ["ISO 27001", "SOC 2", "HIPAA"],
        "region_availability": ["us-central1", "europe-west1", "asia-east1"],
        "use_cases": ["Microservices", "Container orchestration", "Cloud-native apps"],
        "integration": ["Container Registry", "Cloud Monitoring", "Cloud Build"],
        "managed": True
    },
    
    # Alibaba Cloud Services
    {
        "id": "alibaba-ecs",
        "name": "Alibaba Elastic Compute Service",
        "provider": CloudProvider.ALIBABA,
        "category": ServiceCategory.COMPUTE,
        "description": "Scalable cloud computing service with flexible billing",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.009, "unit": "per hour"},
        "features": ["Auto Scaling", "Load Balancing", "Security Groups", "Spot Instances", "Preemptible Instances"],
        "rating": 4.2,
        "compliance": ["ISO 27001", "SOC 2", "CSA STAR", "GDPR"],
        "region_availability": ["cn-beijing", "cn-shanghai", "ap-southeast-1", "us-west-1", "eu-central-1"],
        "use_cases": ["Web applications", "Big data processing", "Enterprise applications"],
        "integration": ["CloudMonitor", "Server Load Balancer", "VPC", "RAM"],
        "managed": False
    },
    {
        "id": "alibaba-fc",
        "name": "Alibaba Function Compute",
        "provider": CloudProvider.ALIBABA,
        "category": ServiceCategory.SERVERLESS,
        "description": "Event-driven serverless compute platform",
        "pricing": {"model": "Pay-per-execution", "starting_price": 0.0000017, "unit": "per GB-second"},
        "features": ["Event-driven", "Auto-scaling", "Multi-language support", "Integrated monitoring"],
        "rating": 4.1,
        "compliance": ["ISO 27001", "SOC 2", "CSA STAR"],
        "region_availability": ["cn-beijing", "cn-shanghai", "ap-southeast-1", "us-west-1"],
        "use_cases": ["API backends", "Data processing", "IoT data processing"],
        "integration": ["Object Storage Service", "Message Service", "CloudMonitor"],
        "managed": True
    },
    {
        "id": "alibaba-rds",
        "name": "Alibaba ApsaraDB for RDS",
        "provider": CloudProvider.ALIBABA,
        "category": ServiceCategory.DATABASE,
        "description": "Managed relational database service supporting MySQL, PostgreSQL, SQL Server",
        "pricing": {"model": "Subscription/Pay-as-you-go", "starting_price": 0.028, "unit": "per hour"},
        "features": ["Automated Backup", "High Availability", "Read Replicas", "Performance Insight"],
        "rating": 4.0,
        "compliance": ["ISO 27001", "SOC 2", "GDPR", "CSA STAR"],
        "region_availability": ["cn-beijing", "cn-shanghai", "ap-southeast-1", "us-west-1"],
        "use_cases": ["Web applications", "E-commerce", "Enterprise systems"],
        "integration": ["CloudMonitor", "RAM", "VPC", "DTS"],
        "managed": True
    },
    {
        "id": "alibaba-oss",
        "name": "Alibaba Object Storage Service",
        "provider": CloudProvider.ALIBABA,
        "category": ServiceCategory.STORAGE,
        "description": "Secure, durable, and scalable cloud storage service",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.020, "unit": "per GB/month"},
        "features": ["Multi-tier storage", "Cross-region replication", "Lifecycle management", "Data encryption"],
        "rating": 4.2,
        "compliance": ["ISO 27001", "SOC 2", "GDPR", "CSA STAR"],
        "region_availability": ["Global"],
        "use_cases": ["Data backup", "Static websites", "Big data analytics", "Content distribution"],
        "integration": ["CDN", "Media Processing", "CloudMonitor", "RAM"],
        "managed": True
    },
    {
        "id": "alibaba-ack",
        "name": "Alibaba Container Service for Kubernetes",
        "provider": CloudProvider.ALIBABA,
        "category": ServiceCategory.CONTAINERS,
        "description": "Managed Kubernetes service with enterprise-grade security",
        "pricing": {"model": "Cluster pricing", "starting_price": 0.09, "unit": "per cluster/hour"},
        "features": ["Auto-scaling", "Security management", "Multi-cluster management", "Service mesh"],
        "rating": 4.1,
        "compliance": ["ISO 27001", "SOC 2", "CSA STAR"],
        "region_availability": ["cn-beijing", "cn-shanghai", "ap-southeast-1", "us-west-1"],
        "use_cases": ["Microservices", "DevOps", "Cloud-native applications"],
        "integration": ["Container Registry", "CloudMonitor", "VPC", "RAM"],
        "managed": True
    },
    
    # IBM Cloud Services
    {
        "id": "ibm-virtual-servers",
        "name": "IBM Virtual Servers",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.COMPUTE,
        "description": "Flexible virtual servers with enterprise-grade security",
        "pricing": {"model": "Hourly/Monthly", "starting_price": 0.013, "unit": "per hour"},
        "features": ["Bare Metal options", "VLAN isolation", "Security groups", "Auto-scaling"],
        "rating": 4.0,
        "compliance": ["SOC 2", "HIPAA", "PCI DSS", "ISO 27001", "FedRAMP"],
        "region_availability": ["us-south", "us-east", "eu-gb", "eu-de", "ap-south", "ap-north"],
        "use_cases": ["Enterprise applications", "High-performance computing", "Disaster recovery"],
        "integration": ["IBM Cloud Monitoring", "Identity and Access Management", "VPC"],
        "managed": False
    },
    {
        "id": "ibm-cloud-functions",
        "name": "IBM Cloud Functions",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.SERVERLESS,
        "description": "Event-driven serverless platform based on Apache OpenWhisk",
        "pricing": {"model": "Pay-per-execution", "starting_price": 0.000017, "unit": "per GB-second"},
        "features": ["Event-driven", "Multi-language support", "API Gateway integration", "Triggers and rules"],
        "rating": 3.9,
        "compliance": ["SOC 2", "HIPAA", "ISO 27001", "PCI DSS"],
        "region_availability": ["us-south", "us-east", "eu-gb", "eu-de"],
        "use_cases": ["API backends", "Data processing", "IoT applications"],
        "integration": ["API Gateway", "Cloudant", "Object Storage", "Event Streams"],
        "managed": True
    },
    {
        "id": "ibm-cloudant",
        "name": "IBM Cloudant",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.DATABASE,
        "description": "Distributed NoSQL database based on Apache CouchDB",
        "pricing": {"model": "Provisioned throughput", "starting_price": 1.00, "unit": "per lookup/second"},
        "features": ["Global distribution", "Multi-master replication", "Full-text search", "Mobile sync"],
        "rating": 4.1,
        "compliance": ["SOC 2", "HIPAA", "ISO 27001", "PCI DSS", "GDPR"],
        "region_availability": ["us-south", "us-east", "eu-gb", "eu-de", "ap-south"],
        "use_cases": ["Mobile applications", "Web applications", "IoT data storage"],
        "integration": ["Cloud Functions", "Watson", "Analytics Engine"],
        "managed": True
    },
    {
        "id": "ibm-object-storage",
        "name": "IBM Cloud Object Storage",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.STORAGE,
        "description": "Highly scalable and durable object storage with flexible pricing",
        "pricing": {"model": "Pay-as-you-go", "starting_price": 0.021, "unit": "per GB/month"},
        "features": ["Cross-region resiliency", "Immutable object storage", "Archive tiers", "Encryption"],
        "rating": 4.2,
        "compliance": ["SOC 2", "HIPAA", "ISO 27001", "PCI DSS", "GDPR", "FedRAMP"],
        "region_availability": ["Global"],
        "use_cases": ["Data backup", "Archive storage", "Content distribution", "Analytics"],
        "integration": ["Analytics Engine", "Watson", "Cloud Functions"],
        "managed": True
    },
    {
        "id": "ibm-kubernetes",
        "name": "IBM Cloud Kubernetes Service",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.CONTAINERS,
        "description": "Managed Kubernetes service with enterprise security",
        "pricing": {"model": "Worker node pricing", "starting_price": 0.11, "unit": "per worker node/hour"},
        "features": ["Managed control plane", "Built-in security", "Cluster autoscaler", "Service mesh"],
        "rating": 4.0,
        "compliance": ["SOC 2", "HIPAA", "ISO 27001", "PCI DSS", "FedRAMP"],
        "region_availability": ["us-south", "us-east", "eu-gb", "eu-de", "ap-south"],
        "use_cases": ["Enterprise applications", "Microservices", "DevOps"],
        "integration": ["Container Registry", "LogDNA", "SysDig", "VPC"],
        "managed": True
    },
    {
        "id": "ibm-watson-ml",
        "name": "IBM Watson Machine Learning",
        "provider": CloudProvider.IBM,
        "category": ServiceCategory.AI_ML,
        "description": "Enterprise machine learning platform with AutoAI",
        "pricing": {"model": "Capacity unit hours", "starting_price": 0.50, "unit": "per CUH"},
        "features": ["AutoAI", "Model deployment", "Federated learning", "Explainable AI"],
        "rating": 4.1,
        "compliance": ["SOC 2", "HIPAA", "ISO 27001", "GDPR"],
        "region_availability": ["us-south", "eu-gb", "eu-de", "ap-south"],
        "use_cases": ["Enterprise AI", "Predictive analytics", "Decision optimization"],
        "integration": ["Watson Studio", "Cloudant", "Object Storage", "Analytics Engine"],
        "managed": True
    }
]


@router.get("/", summary="List all cloud services")
async def list_cloud_services(
    provider: Optional[CloudProvider] = Query(None, description="Filter by cloud provider"),
    category: Optional[ServiceCategory] = Query(None, description="Filter by service category"),
    search: Optional[str] = Query(None, description="Search in service names and descriptions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of services to return"),
    offset: int = Query(0, ge=0, description="Number of services to skip")
) -> Dict[str, Any]:
    """
    Get a comprehensive list of cloud services with filtering options.
    
    Returns cloud services from major providers (AWS, Azure, GCP) with detailed
    information including pricing, features, compliance, and availability.
    """
    try:
        # Start with all services and convert to safe format immediately
        filtered_services = []
        for service in CLOUD_SERVICES_DB:
            service_copy = service.copy()
            service_copy["provider"] = service_copy["provider"].value
            service_copy["category"] = service_copy["category"].value
            filtered_services.append(service_copy)
        
        # Apply provider filter (now comparing strings)
        if provider:
            provider_str = provider.value if hasattr(provider, 'value') else str(provider)
            filtered_services = [s for s in filtered_services if s["provider"] == provider_str]
        
        # Apply category filter (now comparing strings)
        if category:
            category_str = category.value if hasattr(category, 'value') else str(category)
            filtered_services = [s for s in filtered_services if s["category"] == category_str]
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            filtered_services = [
                s for s in filtered_services 
                if search_lower in s["name"].lower() or search_lower in s["description"].lower()
            ]
        
        # Apply pagination
        total_count = len(filtered_services)
        paginated_services = filtered_services[offset:offset + limit]
        
        logger.info(f"Retrieved {len(paginated_services)} cloud services (total: {total_count})")
        
        return {
            "services": paginated_services,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters": {
                "provider": provider_str if provider else None,
                "category": category_str if category else None,
                "search": search
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list cloud services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cloud services"
        )


@router.get("/providers", summary="List all cloud providers")
async def list_providers() -> Dict[str, Any]:
    """Get list of all supported cloud providers."""
    providers = {}
    
    for service in CLOUD_SERVICES_DB:
        provider = service["provider"].value if hasattr(service["provider"], 'value') else str(service["provider"])
        if provider not in providers:
            providers[provider] = {
                "name": provider,
                "service_count": 0,
                "categories": set()
            }
        
        providers[provider]["service_count"] += 1
        category = service["category"].value if hasattr(service["category"], 'value') else str(service["category"])
        providers[provider]["categories"].add(category)
    
    # Convert sets to lists for JSON serialization
    for provider_data in providers.values():
        provider_data["categories"] = sorted(list(provider_data["categories"]))
    
    return {
        "providers": list(providers.values()),
        "total_providers": len(providers)
    }


@router.get("/categories", summary="List all service categories")
async def list_categories() -> Dict[str, Any]:
    """Get list of all service categories."""
    categories = {}
    
    for service in CLOUD_SERVICES_DB:
        category = service["category"].value if hasattr(service["category"], 'value') else str(service["category"])
        if category not in categories:
            categories[category] = {
                "name": category,
                "service_count": 0,
                "providers": set()
            }
        
        categories[category]["service_count"] += 1
        provider = service["provider"].value if hasattr(service["provider"], 'value') else str(service["provider"])
        categories[category]["providers"].add(provider)
    
    # Convert sets to lists for JSON serialization
    for category_data in categories.values():
        category_data["providers"] = sorted(list(category_data["providers"]))
    
    return {
        "categories": list(categories.values()),
        "total_categories": len(categories)
    }


@router.get("/{service_id}", summary="Get service details")
async def get_service_details(service_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific cloud service.
    
    Args:
        service_id: Unique identifier of the service
        
    Returns:
        Detailed service information including features, pricing, and compliance
    """
    try:
        # Find the service
        service = next((s for s in CLOUD_SERVICES_DB if s["id"] == service_id), None)
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
        
        # Convert enum values to strings
        service_copy = service.copy()
        service_copy["provider"] = service_copy["provider"].value if hasattr(service_copy["provider"], 'value') else str(service_copy["provider"])
        service_copy["category"] = service_copy["category"].value if hasattr(service_copy["category"], 'value') else str(service_copy["category"])
        
        logger.info(f"Retrieved details for service: {service_id}")
        
        return service_copy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service details for {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service details"
        )


@router.get("/compare/{service_ids}", summary="Compare multiple services")
async def compare_services(service_ids: str) -> Dict[str, Any]:
    """
    Compare multiple cloud services side by side.
    
    Args:
        service_ids: Comma-separated list of service IDs to compare
        
    Returns:
        Comparison data for the requested services
    """
    try:
        # Parse service IDs
        ids = [id.strip() for id in service_ids.split(",") if id.strip()]
        
        if len(ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 services are required for comparison"
            )
        
        if len(ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 services can be compared at once"
            )
        
        # Find the services
        services = []
        for service_id in ids:
            service = next((s for s in CLOUD_SERVICES_DB if s["id"] == service_id), None)
            if service:
                # Convert enum values to strings
                service_copy = service.copy()
                service_copy["provider"] = service_copy["provider"].value if hasattr(service_copy["provider"], 'value') else str(service_copy["provider"])
                service_copy["category"] = service_copy["category"].value if hasattr(service_copy["category"], 'value') else str(service_copy["category"])
                services.append(service_copy)
        
        if not services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid services found for comparison"
            )
        
        # Generate comparison insights
        comparison_insights = {
            "price_comparison": _compare_pricing(services),
            "feature_overlap": _analyze_feature_overlap(services),
            "compliance_comparison": _compare_compliance(services),
            "recommendations": _generate_comparison_recommendations(services)
        }
        
        logger.info(f"Compared {len(services)} services: {[s['name'] for s in services]}")
        
        return {
            "services": services,
            "comparison": comparison_insights,
            "compared_count": len(services)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare services {service_ids}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare services"
        )


def _compare_pricing(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare pricing across services."""
    prices = [s["pricing"]["starting_price"] for s in services]
    
    return {
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "average_price": sum(prices) / len(prices),
        "cheapest_service": min(services, key=lambda s: s["pricing"]["starting_price"])["name"],
        "most_expensive_service": max(services, key=lambda s: s["pricing"]["starting_price"])["name"]
    }


def _analyze_feature_overlap(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze feature overlap between services."""
    all_features = set()
    service_features = {}
    
    for service in services:
        features = set(service["features"])
        all_features.update(features)
        service_features[service["name"]] = features
    
    # Find common features
    common_features = all_features.copy()
    for features in service_features.values():
        common_features.intersection_update(features)
    
    return {
        "total_unique_features": len(all_features),
        "common_features": list(common_features),
        "common_feature_count": len(common_features),
        "feature_coverage": {
            name: len(features) / len(all_features) * 100 
            for name, features in service_features.items()
        }
    }


def _compare_compliance(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare compliance certifications across services."""
    all_compliance = set()
    service_compliance = {}
    
    for service in services:
        compliance = set(service["compliance"])
        all_compliance.update(compliance)
        service_compliance[service["name"]] = compliance
    
    # Find common compliance standards
    common_compliance = all_compliance.copy()
    for compliance in service_compliance.values():
        common_compliance.intersection_update(compliance)
    
    return {
        "total_compliance_standards": len(all_compliance),
        "common_compliance": list(common_compliance),
        "compliance_coverage": {
            name: len(compliance) / len(all_compliance) * 100 
            for name, compliance in service_compliance.items()
        }
    }


def _generate_comparison_recommendations(services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommendations based on service comparison."""
    recommendations = []
    
    # Price-based recommendation
    cheapest = min(services, key=lambda s: s["pricing"]["starting_price"])
    recommendations.append({
        "type": "cost_optimization",
        "title": "Most Cost-Effective Option",
        "description": f"{cheapest['name']} offers the lowest starting price at ${cheapest['pricing']['starting_price']} {cheapest['pricing']['unit']}",
        "service": cheapest["name"],
        "priority": "high"
    })
    
    # Feature-based recommendation
    most_featured = max(services, key=lambda s: len(s["features"]))
    recommendations.append({
        "type": "feature_rich",
        "title": "Most Feature-Rich Service",
        "description": f"{most_featured['name']} offers the most features with {len(most_featured['features'])} capabilities",
        "service": most_featured["name"],
        "priority": "medium"
    })
    
    # Compliance recommendation
    most_compliant = max(services, key=lambda s: len(s["compliance"]))
    recommendations.append({
        "type": "compliance",
        "title": "Best Compliance Coverage",
        "description": f"{most_compliant['name']} supports {len(most_compliant['compliance'])} compliance standards",
        "service": most_compliant["name"],
        "priority": "high" if len(most_compliant["compliance"]) > 3 else "medium"
    })
    
    return recommendations


@router.get("/stats", summary="Get service statistics")
async def get_service_statistics() -> Dict[str, Any]:
    """Get comprehensive statistics about the cloud services catalog."""
    try:
        # Provider statistics
        provider_stats = {}
        category_stats = {}
        pricing_stats = []
        compliance_stats = {}
        
        for service in CLOUD_SERVICES_DB:
            provider = service["provider"].value if hasattr(service["provider"], 'value') else str(service["provider"])
            category = service["category"].value if hasattr(service["category"], 'value') else str(service["category"])
            
            # Provider stats
            if provider not in provider_stats:
                provider_stats[provider] = {"count": 0, "avg_rating": 0, "total_rating": 0}
            provider_stats[provider]["count"] += 1
            provider_stats[provider]["total_rating"] += service["rating"]
            provider_stats[provider]["avg_rating"] = provider_stats[provider]["total_rating"] / provider_stats[provider]["count"]
            
            # Category stats
            if category not in category_stats:
                category_stats[category] = {"count": 0, "providers": set()}
            category_stats[category]["count"] += 1
            category_stats[category]["providers"].add(provider)
            
            # Pricing stats
            pricing_stats.append(service["pricing"]["starting_price"])
            
            # Compliance stats
            for compliance in service["compliance"]:
                if compliance not in compliance_stats:
                    compliance_stats[compliance] = 0
                compliance_stats[compliance] += 1
        
        # Convert sets to lists for JSON serialization
        for cat_data in category_stats.values():
            cat_data["providers"] = list(cat_data["providers"])
        
        return {
            "total_services": len(CLOUD_SERVICES_DB),
            "providers": provider_stats,
            "categories": category_stats,
            "pricing": {
                "min_price": min(pricing_stats),
                "max_price": max(pricing_stats),
                "avg_price": sum(pricing_stats) / len(pricing_stats)
            },
            "compliance_standards": compliance_stats,
            "most_common_compliance": max(compliance_stats.items(), key=lambda x: x[1])[0]
        }
        
    except Exception as e:
        logger.error(f"Failed to get service statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service statistics"
        )