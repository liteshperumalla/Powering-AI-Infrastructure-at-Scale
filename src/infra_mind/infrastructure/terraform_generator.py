"""
Terraform Infrastructure as Code Generator

Generates Terraform configuration files based on assessment requirements
and recommendations for multi-cloud deployments.
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import subprocess
from dataclasses import dataclass
from enum import Enum

from ..models.assessment import Assessment
from ..schemas.base import CloudProvider
from loguru import logger


class ResourceType(Enum):
    """Terraform resource types."""
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORKING = "networking"
    SECURITY = "security"
    MONITORING = "monitoring"
    LOAD_BALANCER = "load_balancer"


@dataclass
class TerraformResource:
    """Terraform resource configuration."""
    resource_type: str
    name: str
    config: Dict[str, Any]
    provider: CloudProvider
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class TerraformModule:
    """Terraform module configuration."""
    name: str
    source: str
    version: Optional[str] = None
    variables: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


class TerraformGenerator:
    """
    Generates Terraform Infrastructure as Code from assessment data.
    
    Supports multi-cloud deployments with AWS, Azure, GCP, IBM, and Alibaba Cloud providers.
    """
    
    def __init__(self):
        self.providers_config = {
            CloudProvider.AWS: {
                "required_providers": {
                    "aws": {
                        "source": "hashicorp/aws",
                        "version": "~> 5.0"
                    }
                }
            },
            CloudProvider.AZURE: {
                "required_providers": {
                    "azurerm": {
                        "source": "hashicorp/azurerm", 
                        "version": "~> 3.0"
                    }
                }
            },
            CloudProvider.GCP: {
                "required_providers": {
                    "google": {
                        "source": "hashicorp/google",
                        "version": "~> 4.0"
                    }
                }
            },
            CloudProvider.IBM: {
                "required_providers": {
                    "ibm": {
                        "source": "IBM-Cloud/ibm",
                        "version": "~> 1.0"
                    }
                }
            },
            CloudProvider.ALIBABA: {
                "required_providers": {
                    "alicloud": {
                        "source": "aliyun/alicloud",
                        "version": "~> 1.0"
                    }
                }
            }
        }
        
        self.resource_templates = self._load_resource_templates()
    
    def generate_infrastructure(self, assessment: Assessment) -> Dict[str, str]:
        """
        Generate complete Terraform infrastructure from assessment.
        
        Args:
            assessment: Assessment with requirements and recommendations
            
        Returns:
            Dictionary with filename -> terraform content mapping
        """
        try:
            logger.info(f"Generating Terraform infrastructure for assessment {assessment.id}")
            
            # Analyze assessment requirements
            infrastructure_plan = self._analyze_requirements(assessment)
            
            # Generate Terraform files
            terraform_files = {}
            
            # Main configuration
            terraform_files["main.tf"] = self._generate_main_tf(infrastructure_plan)
            
            # Variables
            terraform_files["variables.tf"] = self._generate_variables_tf(infrastructure_plan)
            
            # Outputs
            terraform_files["outputs.tf"] = self._generate_outputs_tf(infrastructure_plan)
            
            # Provider configurations
            terraform_files["providers.tf"] = self._generate_providers_tf(infrastructure_plan["providers"])
            
            # Modules (if any)
            if infrastructure_plan.get("modules"):
                terraform_files["modules.tf"] = self._generate_modules_tf(infrastructure_plan["modules"])
            
            # Environment-specific configurations
            for env in ["dev", "staging", "prod"]:
                terraform_files[f"terraform.{env}.tfvars"] = self._generate_tfvars(infrastructure_plan, env)
            
            logger.info(f"Generated {len(terraform_files)} Terraform files")
            return terraform_files
            
        except Exception as e:
            logger.error(f"Failed to generate Terraform infrastructure: {e}")
            raise
    
    def _analyze_requirements(self, assessment: Assessment) -> Dict[str, Any]:
        """Analyze assessment requirements and generate infrastructure plan."""
        
        business_reqs = assessment.business_requirements
        technical_reqs = assessment.technical_requirements
        
        # Determine primary cloud provider
        workload_types = technical_reqs.get("workload_types", [])
        primary_provider = self._determine_provider(business_reqs, workload_types)
        
        # Generate resource requirements
        resources = []
        
        # Compute resources
        if "web_application" in workload_types or "api_service" in workload_types:
            resources.extend(self._generate_compute_resources(technical_reqs, primary_provider))
        
        # Database resources
        databases = technical_reqs.get("integration_requirements", {}).get("databases", [])
        if databases:
            resources.extend(self._generate_database_resources(databases, primary_provider))
        
        # Storage resources
        resources.extend(self._generate_storage_resources(technical_reqs, primary_provider))
        
        # Networking resources
        resources.extend(self._generate_networking_resources(technical_reqs, primary_provider))
        
        # Security resources
        security_reqs = technical_reqs.get("security_requirements", {})
        if security_reqs:
            resources.extend(self._generate_security_resources(security_reqs, primary_provider))
        
        # Monitoring resources
        resources.extend(self._generate_monitoring_resources(primary_provider))
        
        return {
            "providers": [primary_provider],
            "resources": resources,
            "variables": self._generate_variable_definitions(business_reqs, technical_reqs),
            "outputs": self._generate_output_definitions(resources),
            "modules": self._suggest_modules(resources, primary_provider)
        }
    
    def _determine_provider(self, business_reqs: Dict, workload_types: List[str]) -> CloudProvider:
        """Determine the best cloud provider based on requirements."""
        
        # Simple logic - can be enhanced with ML-based recommendations
        budget = business_reqs.get("budget_constraints", 0)
        company_size = business_reqs.get("company_size", "small")
        
        if company_size == "enterprise" or budget > 100000:
            return CloudProvider.AWS  # AWS for large enterprises
        elif "microsoft" in str(business_reqs).lower() or company_size == "medium":
            return CloudProvider.AZURE  # Azure for medium businesses
        else:
            return CloudProvider.GCP  # GCP for startups and cost-conscious
    
    def _generate_compute_resources(self, technical_reqs: Dict, provider: CloudProvider) -> List[TerraformResource]:
        """Generate compute resources (VMs, containers, etc.)."""
        
        resources = []
        performance_reqs = technical_reqs.get("performance_requirements", {})
        
        if provider == CloudProvider.AWS:
            # EC2 instances
            instance_type = self._determine_instance_type(performance_reqs, "aws")
            
            resources.append(TerraformResource(
                resource_type="aws_instance",
                name="web_server",
                config={
                    "ami": "${data.aws_ami.ubuntu.id}",
                    "instance_type": instance_type,
                    "key_name": "${var.key_name}",
                    "vpc_security_group_ids": ["${aws_security_group.web.id}"],
                    "subnet_id": "${aws_subnet.public.id}",
                    "associate_public_ip_address": True,
                    "user_data": "${file('user_data.sh')}",
                    "tags": {
                        "Name": "${var.project_name}-web-server",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_security_group.web", "aws_subnet.public"]
            ))
            
            # Auto Scaling Group
            if technical_reqs.get("scalability_requirements", {}).get("auto_scaling"):
                resources.append(TerraformResource(
                    resource_type="aws_autoscaling_group",
                    name="web_asg",
                    config={
                        "name": "${var.project_name}-web-asg",
                        "vpc_zone_identifier": ["${aws_subnet.public.id}"],
                        "target_group_arns": ["${aws_lb_target_group.web.arn}"],
                        "health_check_type": "ELB",
                        "min_size": 1,
                        "max_size": "${var.max_instances}",
                        "desired_capacity": 2,
                        "launch_template": {
                            "id": "${aws_launch_template.web.id}",
                            "version": "$Latest"
                        }
                    },
                    provider=provider
                ))
        
        elif provider == CloudProvider.AZURE:
            # Virtual Machines
            vm_size = self._determine_instance_type(performance_reqs, "azure")
            
            resources.append(TerraformResource(
                resource_type="azurerm_linux_virtual_machine",
                name="web_vm",
                config={
                    "name": "${var.project_name}-web-vm",
                    "resource_group_name": "${azurerm_resource_group.main.name}",
                    "location": "${azurerm_resource_group.main.location}",
                    "size": vm_size,
                    "admin_username": "adminuser",
                    "network_interface_ids": ["${azurerm_network_interface.web.id}"],
                    "os_disk": {
                        "caching": "ReadWrite",
                        "storage_account_type": "Premium_LRS"
                    },
                    "source_image_reference": {
                        "publisher": "Canonical",
                        "offer": "0001-com-ubuntu-server-focal",
                        "sku": "20_04-lts-gen2",
                        "version": "latest"
                    }
                },
                provider=provider
            ))
        
        elif provider == CloudProvider.GCP:
            # Compute Engine instances
            machine_type = self._determine_instance_type(performance_reqs, "gcp")
            
            resources.append(TerraformResource(
                resource_type="google_compute_instance",
                name="web_instance",
                config={
                    "name": "${var.project_name}-web-instance",
                    "machine_type": machine_type,
                    "zone": "${var.zone}",
                    "boot_disk": {
                        "initialize_params": {
                            "image": "ubuntu-os-cloud/ubuntu-2004-lts"
                        }
                    },
                    "network_interface": {
                        "network": "${google_compute_network.vpc.id}",
                        "subnetwork": "${google_compute_subnetwork.subnet.id}",
                        "access_config": {}
                    },
                    "metadata_startup_script": "${file('startup-script.sh')}"
                },
                provider=provider
            ))
        
        return resources
    
    def _generate_database_resources(self, databases: List[str], provider: CloudProvider) -> List[TerraformResource]:
        """Generate database resources based on requirements."""
        
        resources = []
        
        for db_type in databases:
            if provider == CloudProvider.AWS:
                if db_type.lower() in ["postgresql", "mysql"]:
                    resources.append(TerraformResource(
                        resource_type="aws_db_instance",
                        name=f"{db_type}_db",
                        config={
                            "identifier": "${var.project_name}-${var.environment}-db",
                            "engine": db_type.lower(),
                            "engine_version": "13.7" if db_type.lower() == "postgresql" else "8.0",
                            "instance_class": "db.t3.micro",
                            "allocated_storage": 20,
                            "storage_type": "gp2",
                            "db_name": "${var.db_name}",
                            "username": "${var.db_username}",
                            "password": "${var.db_password}",
                            "vpc_security_group_ids": ["${aws_security_group.db.id}"],
                            "db_subnet_group_name": "${aws_db_subnet_group.main.name}",
                            "backup_retention_period": 7,
                            "multi_az": "${var.environment == 'prod' ? true : false}",
                            "storage_encrypted": True,
                            "skip_final_snapshot": "${var.environment != 'prod'}",
                            "tags": {
                                "Name": "${var.project_name}-database",
                                "Environment": "${var.environment}"
                            }
                        },
                        provider=provider,
                        dependencies=["aws_security_group.db", "aws_db_subnet_group.main"]
                    ))
            
            # Add similar configurations for Azure and GCP
        
        return resources
    
    def _generate_storage_resources(self, technical_reqs: Dict, provider: CloudProvider) -> List[TerraformResource]:
        """Generate storage resources."""
        
        resources = []
        
        if provider == CloudProvider.AWS:
            # S3 bucket for application storage
            resources.append(TerraformResource(
                resource_type="aws_s3_bucket",
                name="app_storage",
                config={
                    "bucket": "${var.project_name}-${var.environment}-storage-${random_id.bucket_suffix.hex}",
                    "tags": {
                        "Name": "${var.project_name}-storage",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider
            ))
            
            # S3 bucket versioning
            resources.append(TerraformResource(
                resource_type="aws_s3_bucket_versioning",
                name="app_storage_versioning",
                config={
                    "bucket": "${aws_s3_bucket.app_storage.id}",
                    "versioning_configuration": {
                        "status": "Enabled"
                    }
                },
                provider=provider,
                dependencies=["aws_s3_bucket.app_storage"]
            ))
            
            # S3 bucket encryption
            resources.append(TerraformResource(
                resource_type="aws_s3_bucket_server_side_encryption_configuration",
                name="app_storage_encryption",
                config={
                    "bucket": "${aws_s3_bucket.app_storage.id}",
                    "rule": {
                        "apply_server_side_encryption_by_default": {
                            "sse_algorithm": "AES256"
                        }
                    }
                },
                provider=provider,
                dependencies=["aws_s3_bucket.app_storage"]
            ))
        
        return resources
    
    def _generate_networking_resources(self, technical_reqs: Dict, provider: CloudProvider) -> List[TerraformResource]:
        """Generate networking resources (VPC, subnets, load balancers)."""
        
        resources = []
        
        if provider == CloudProvider.AWS:
            # VPC
            resources.append(TerraformResource(
                resource_type="aws_vpc",
                name="main",
                config={
                    "cidr_block": "${var.vpc_cidr}",
                    "enable_dns_hostnames": True,
                    "enable_dns_support": True,
                    "tags": {
                        "Name": "${var.project_name}-vpc",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider
            ))
            
            # Internet Gateway
            resources.append(TerraformResource(
                resource_type="aws_internet_gateway",
                name="main",
                config={
                    "vpc_id": "${aws_vpc.main.id}",
                    "tags": {
                        "Name": "${var.project_name}-igw",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main"]
            ))
            
            # Public Subnet
            resources.append(TerraformResource(
                resource_type="aws_subnet",
                name="public",
                config={
                    "vpc_id": "${aws_vpc.main.id}",
                    "cidr_block": "${var.public_subnet_cidr}",
                    "availability_zone": "${data.aws_availability_zones.available.names[0]}",
                    "map_public_ip_on_launch": True,
                    "tags": {
                        "Name": "${var.project_name}-public-subnet",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main"]
            ))
            
            # Private Subnet
            resources.append(TerraformResource(
                resource_type="aws_subnet",
                name="private",
                config={
                    "vpc_id": "${aws_vpc.main.id}",
                    "cidr_block": "${var.private_subnet_cidr}",
                    "availability_zone": "${data.aws_availability_zones.available.names[1]}",
                    "tags": {
                        "Name": "${var.project_name}-private-subnet",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main"]
            ))
            
            # Route Table
            resources.append(TerraformResource(
                resource_type="aws_route_table",
                name="public",
                config={
                    "vpc_id": "${aws_vpc.main.id}",
                    "route": {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": "${aws_internet_gateway.main.id}"
                    },
                    "tags": {
                        "Name": "${var.project_name}-public-rt",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main", "aws_internet_gateway.main"]
            ))
            
            # Load Balancer (if required)
            if technical_reqs.get("scalability_requirements", {}).get("load_balancing"):
                resources.append(TerraformResource(
                    resource_type="aws_lb",
                    name="web",
                    config={
                        "name": "${var.project_name}-web-lb",
                        "load_balancer_type": "application",
                        "subnets": ["${aws_subnet.public.id}"],
                        "security_groups": ["${aws_security_group.lb.id}"],
                        "tags": {
                            "Name": "${var.project_name}-web-lb",
                            "Environment": "${var.environment}"
                        }
                    },
                    provider=provider,
                    dependencies=["aws_subnet.public", "aws_security_group.lb"]
                ))
        
        return resources
    
    def _generate_security_resources(self, security_reqs: Dict, provider: CloudProvider) -> List[TerraformResource]:
        """Generate security resources (security groups, IAM roles, etc.)."""
        
        resources = []
        
        if provider == CloudProvider.AWS:
            # Security Group for web servers
            resources.append(TerraformResource(
                resource_type="aws_security_group",
                name="web",
                config={
                    "name_prefix": "${var.project_name}-web-",
                    "vpc_id": "${aws_vpc.main.id}",
                    "description": "Security group for web servers",
                    "ingress": [
                        {
                            "from_port": 80,
                            "to_port": 80,
                            "protocol": "tcp",
                            "cidr_blocks": ["0.0.0.0/0"]
                        },
                        {
                            "from_port": 443,
                            "to_port": 443,
                            "protocol": "tcp",
                            "cidr_blocks": ["0.0.0.0/0"]
                        },
                        {
                            "from_port": 22,
                            "to_port": 22,
                            "protocol": "tcp",
                            "cidr_blocks": ["${var.admin_cidr}"]
                        }
                    ],
                    "egress": [
                        {
                            "from_port": 0,
                            "to_port": 0,
                            "protocol": "-1",
                            "cidr_blocks": ["0.0.0.0/0"]
                        }
                    ],
                    "tags": {
                        "Name": "${var.project_name}-web-sg",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main"]
            ))
            
            # Security Group for database
            resources.append(TerraformResource(
                resource_type="aws_security_group",
                name="db",
                config={
                    "name_prefix": "${var.project_name}-db-",
                    "vpc_id": "${aws_vpc.main.id}",
                    "description": "Security group for database",
                    "ingress": [
                        {
                            "from_port": 5432,
                            "to_port": 5432,
                            "protocol": "tcp",
                            "security_groups": ["${aws_security_group.web.id}"]
                        }
                    ],
                    "egress": [],
                    "tags": {
                        "Name": "${var.project_name}-db-sg",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider,
                dependencies=["aws_vpc.main", "aws_security_group.web"]
            ))
            
            # IAM Role for EC2 instances
            if security_reqs.get("monitoring"):
                resources.append(TerraformResource(
                    resource_type="aws_iam_role",
                    name="ec2_role",
                    config={
                        "name": "${var.project_name}-ec2-role",
                        "assume_role_policy": json.dumps({
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Action": "sts:AssumeRole",
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "ec2.amazonaws.com"
                                }
                            }]
                        })
                    },
                    provider=provider
                ))
        
        return resources
    
    def _generate_monitoring_resources(self, provider: CloudProvider) -> List[TerraformResource]:
        """Generate monitoring and logging resources."""
        
        resources = []
        
        if provider == CloudProvider.AWS:
            # CloudWatch Log Group
            resources.append(TerraformResource(
                resource_type="aws_cloudwatch_log_group",
                name="app_logs",
                config={
                    "name": "/aws/ec2/${var.project_name}",
                    "retention_in_days": "${var.log_retention_days}",
                    "tags": {
                        "Name": "${var.project_name}-logs",
                        "Environment": "${var.environment}"
                    }
                },
                provider=provider
            ))
            
            # CloudWatch Dashboard
            resources.append(TerraformResource(
                resource_type="aws_cloudwatch_dashboard",
                name="main",
                config={
                    "dashboard_name": "${var.project_name}-dashboard",
                    "dashboard_body": json.dumps({
                        "widgets": [
                            {
                                "type": "metric",
                                "properties": {
                                    "metrics": [
                                        ["AWS/EC2", "CPUUtilization", "InstanceId", "${aws_instance.web_server.id}"]
                                    ],
                                    "period": 300,
                                    "stat": "Average",
                                    "region": "${var.aws_region}",
                                    "title": "EC2 Instance CPU"
                                }
                            }
                        ]
                    })
                },
                provider=provider,
                dependencies=["aws_instance.web_server"]
            ))
        
        return resources
    
    def _determine_instance_type(self, performance_reqs: Dict, provider_type: str) -> str:
        """Determine appropriate instance type based on performance requirements."""
        
        latency_ms = performance_reqs.get("latency_ms", 200)
        throughput_rps = performance_reqs.get("throughput_rps", 100)
        
        if provider_type == "aws":
            if throughput_rps > 1000:
                return "t3.large"
            elif throughput_rps > 500:
                return "t3.medium"
            else:
                return "t3.micro"
        elif provider_type == "azure":
            if throughput_rps > 1000:
                return "Standard_B2s"
            elif throughput_rps > 500:
                return "Standard_B1s"
            else:
                return "Standard_B1ls"
        elif provider_type == "gcp":
            if throughput_rps > 1000:
                return "n1-standard-2"
            elif throughput_rps > 500:
                return "n1-standard-1"
            else:
                return "f1-micro"
    
    def _generate_variable_definitions(self, business_reqs: Dict, technical_reqs: Dict) -> Dict[str, Dict]:
        """Generate Terraform variable definitions."""
        
        return {
            "project_name": {
                "description": "Name of the project",
                "type": "string",
                "default": "infra-mind-project"
            },
            "environment": {
                "description": "Environment (dev/staging/prod)",
                "type": "string",
                "default": "dev"
            },
            "aws_region": {
                "description": "AWS region",
                "type": "string", 
                "default": "us-west-2"
            },
            "vpc_cidr": {
                "description": "CIDR block for VPC",
                "type": "string",
                "default": "10.0.0.0/16"
            },
            "public_subnet_cidr": {
                "description": "CIDR block for public subnet",
                "type": "string",
                "default": "10.0.1.0/24"
            },
            "private_subnet_cidr": {
                "description": "CIDR block for private subnet",
                "type": "string",
                "default": "10.0.2.0/24"
            },
            "key_name": {
                "description": "AWS EC2 Key Pair name",
                "type": "string"
            },
            "admin_cidr": {
                "description": "CIDR block for admin access",
                "type": "string",
                "default": "0.0.0.0/0"
            },
            "db_name": {
                "description": "Database name",
                "type": "string",
                "default": "appdb"
            },
            "db_username": {
                "description": "Database username",
                "type": "string",
                "default": "dbadmin"
            },
            "db_password": {
                "description": "Database password",
                "type": "string",
                "sensitive": True
            },
            "max_instances": {
                "description": "Maximum number of instances in ASG",
                "type": "number",
                "default": technical_reqs.get("scalability_requirements", {}).get("max_instances", 5)
            },
            "log_retention_days": {
                "description": "CloudWatch log retention in days",
                "type": "number",
                "default": 30
            }
        }
    
    def _generate_output_definitions(self, resources: List[TerraformResource]) -> Dict[str, Dict]:
        """Generate Terraform output definitions."""
        
        outputs = {}
        
        for resource in resources:
            if resource.resource_type == "aws_instance" and resource.name == "web_server":
                outputs["web_server_public_ip"] = {
                    "description": "Public IP of web server",
                    "value": "${aws_instance.web_server.public_ip}"
                }
            elif resource.resource_type == "aws_lb" and resource.name == "web":
                outputs["load_balancer_dns"] = {
                    "description": "Load balancer DNS name",
                    "value": "${aws_lb.web.dns_name}"
                }
            elif resource.resource_type == "aws_db_instance":
                outputs["database_endpoint"] = {
                    "description": "Database endpoint",
                    "value": "${aws_db_instance." + resource.name + "_db.endpoint}",
                    "sensitive": True
                }
        
        return outputs
    
    def _suggest_modules(self, resources: List[TerraformResource], provider: CloudProvider) -> List[TerraformModule]:
        """Suggest Terraform modules based on resources."""
        
        modules = []
        
        # If we have many networking resources, suggest VPC module
        networking_resources = [r for r in resources if "vpc" in r.resource_type or "subnet" in r.resource_type]
        if len(networking_resources) > 3:
            modules.append(TerraformModule(
                name="vpc",
                source="terraform-aws-modules/vpc/aws",
                version="~> 3.0",
                variables={
                    "name": "${var.project_name}",
                    "cidr": "${var.vpc_cidr}",
                    "azs": "${data.aws_availability_zones.available.names}",
                    "public_subnets": ["${var.public_subnet_cidr}"],
                    "private_subnets": ["${var.private_subnet_cidr}"],
                    "enable_nat_gateway": True,
                    "enable_vpn_gateway": True,
                    "tags": {
                        "Terraform": "true",
                        "Environment": "${var.environment}"
                    }
                }
            ))
        
        return modules
    
    def _generate_main_tf(self, infrastructure_plan: Dict) -> str:
        """Generate main.tf content."""
        
        content = []
        
        # Add data sources
        content.append("# Data Sources")
        content.append("data \"aws_availability_zones\" \"available\" {\n  state = \"available\"\n}")
        content.append("data \"aws_ami\" \"ubuntu\" {\n  most_recent = true\n  owners      = [\"099720109477\"]\n  filter {\n    name   = \"name\"\n    values = [\"ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*\"]\n  }\n}")
        content.append("resource \"random_id\" \"bucket_suffix\" {\n  byte_length = 8\n}")
        content.append("")
        
        # Add resources
        for resource in infrastructure_plan["resources"]:
            content.append(f"resource \"{resource.resource_type}\" \"{resource.name}\" {{")
            
            for key, value in resource.config.items():
                if isinstance(value, dict):
                    content.append(f"  {key} {{")
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, str):
                            content.append(f"    {subkey} = \"{subvalue}\"")
                        else:
                            content.append(f"    {subkey} = {json.dumps(subvalue)}")
                    content.append("  }")
                elif isinstance(value, list):
                    if len(value) > 0 and isinstance(value[0], dict):
                        for item in value:
                            content.append(f"  {key} {{")
                            for subkey, subvalue in item.items():
                                if isinstance(subvalue, str):
                                    content.append(f"    {subkey} = \"{subvalue}\"")
                                else:
                                    content.append(f"    {subkey} = {json.dumps(subvalue)}")
                            content.append("  }")
                    else:
                        content.append(f"  {key} = {json.dumps(value)}")
                elif isinstance(value, str):
                    content.append(f"  {key} = \"{value}\"")
                else:
                    content.append(f"  {key} = {json.dumps(value)}")
            
            content.append("}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_variables_tf(self, infrastructure_plan: Dict) -> str:
        """Generate variables.tf content."""
        
        content = []
        
        for var_name, var_config in infrastructure_plan["variables"].items():
            content.append(f"variable \"{var_name}\" {{")
            content.append(f"  description = \"{var_config['description']}\"")
            content.append(f"  type        = {var_config['type']}")
            
            if "default" in var_config:
                if isinstance(var_config["default"], str):
                    content.append(f"  default     = \"{var_config['default']}\"")
                else:
                    content.append(f"  default     = {var_config['default']}")
            
            if var_config.get("sensitive"):
                content.append("  sensitive   = true")
            
            content.append("}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_outputs_tf(self, infrastructure_plan: Dict) -> str:
        """Generate outputs.tf content."""
        
        content = []
        
        for output_name, output_config in infrastructure_plan["outputs"].items():
            content.append(f"output \"{output_name}\" {{")
            content.append(f"  description = \"{output_config['description']}\"")
            content.append(f"  value       = {output_config['value']}")
            
            if output_config.get("sensitive"):
                content.append("  sensitive   = true")
            
            content.append("}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_providers_tf(self, providers: List[CloudProvider]) -> str:
        """Generate providers.tf content."""
        
        content = ["terraform {"]
        
        # Required providers
        content.append("  required_providers {")
        for provider in providers:
            if provider in self.providers_config:
                provider_config = self.providers_config[provider]["required_providers"]
                for provider_name, provider_spec in provider_config.items():
                    content.append(f"    {provider_name} = {{")
                    content.append(f"      source  = \"{provider_spec['source']}\"")
                    content.append(f"      version = \"{provider_spec['version']}\"")
                    content.append("    }")
        content.append("  }")
        
        content.append("  required_version = \">= 1.0\"")
        content.append("}")
        content.append("")
        
        # Provider configurations
        for provider in providers:
            if provider == CloudProvider.AWS:
                content.extend([
                    "provider \"aws\" {",
                    "  region = var.aws_region",
                    "  ",
                    "  default_tags {",
                    "    tags = {",
                    "      Project     = var.project_name",
                    "      Environment = var.environment",
                    "      ManagedBy   = \"Terraform\"",
                    "    }",
                    "  }",
                    "}",
                    ""
                ])
        
        return "\n".join(content)
    
    def _generate_modules_tf(self, modules: List[TerraformModule]) -> str:
        """Generate modules.tf content."""
        
        content = []
        
        for module in modules:
            content.append(f"module \"{module.name}\" {{")
            content.append(f"  source  = \"{module.source}\"")
            if module.version:
                content.append(f"  version = \"{module.version}\"")
            content.append("")
            
            for var_name, var_value in module.variables.items():
                if isinstance(var_value, str):
                    content.append(f"  {var_name} = \"{var_value}\"")
                else:
                    content.append(f"  {var_name} = {json.dumps(var_value)}")
            
            content.append("}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_tfvars(self, infrastructure_plan: Dict, environment: str) -> str:
        """Generate environment-specific .tfvars file."""
        
        content = [f"# {environment.upper()} Environment Variables"]
        content.append("")
        
        # Environment-specific values
        env_config = {
            "dev": {
                "environment": "dev",
                "max_instances": 2,
                "log_retention_days": 7
            },
            "staging": {
                "environment": "staging", 
                "max_instances": 3,
                "log_retention_days": 14
            },
            "prod": {
                "environment": "prod",
                "max_instances": 10,
                "log_retention_days": 90
            }
        }
        
        if environment in env_config:
            for key, value in env_config[environment].items():
                if isinstance(value, str):
                    content.append(f"{key} = \"{value}\"")
                else:
                    content.append(f"{key} = {value}")
        
        content.append("")
        content.append("# Override these values as needed")
        content.append("# key_name = \"your-key-name\"")
        content.append("# db_password = \"your-secure-password\"")
        
        return "\n".join(content)
    
    def _load_resource_templates(self) -> Dict:
        """Load resource templates for different providers."""
        return {}
    
    def validate_terraform(self, terraform_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate generated Terraform configuration.
        
        Args:
            terraform_files: Dictionary of filename -> content
            
        Returns:
            Validation results
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write files to temp directory
                for filename, content in terraform_files.items():
                    (temp_path / filename).write_text(content)
                
                # Run terraform validate
                result = subprocess.run(
                    ["terraform", "validate"],
                    cwd=temp_path,
                    capture_output=True,
                    text=True
                )
                
                return {
                    "valid": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to validate Terraform: {e}")
            return {
                "valid": False,
                "output": "",
                "errors": str(e)
            }
    
    async def plan_terraform(self, terraform_files: Dict[str, str], variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate Terraform plan.
        
        Args:
            terraform_files: Dictionary of filename -> content
            variables: Variable values for planning
            
        Returns:
            Plan results
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write files to temp directory
                for filename, content in terraform_files.items():
                    (temp_path / filename).write_text(content)
                
                # Initialize Terraform
                init_result = subprocess.run(
                    ["terraform", "init"],
                    cwd=temp_path,
                    capture_output=True,
                    text=True
                )
                
                if init_result.returncode != 0:
                    return {
                        "success": False,
                        "error": init_result.stderr
                    }
                
                # Generate plan
                plan_cmd = ["terraform", "plan", "-out=tfplan"]
                if variables:
                    for key, value in variables.items():
                        plan_cmd.extend(["-var", f"{key}={value}"])
                
                plan_result = subprocess.run(
                    plan_cmd,
                    cwd=temp_path,
                    capture_output=True,
                    text=True
                )
                
                return {
                    "success": plan_result.returncode == 0,
                    "output": plan_result.stdout,
                    "error": plan_result.stderr if plan_result.returncode != 0 else None
                }
                
        except Exception as e:
            logger.error(f"Failed to generate Terraform plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }