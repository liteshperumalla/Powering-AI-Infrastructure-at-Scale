"""
Infrastructure as Code (IaC) Generator

Unified IaC generation system that supports multiple IaC tools and frameworks
including Terraform, Pulumi, AWS CDK, Azure ARM, and Google Cloud Deployment Manager.
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod

from ..models.assessment import Assessment
from ..schemas.base import CloudProvider
from .terraform_generator import TerraformGenerator
from .kubernetes_manager import KubernetesManager, ApplicationConfig
from loguru import logger


class IaCTool(Enum):
    """Infrastructure as Code tools."""
    TERRAFORM = "terraform"
    PULUMI = "pulumi"
    AWS_CDK = "aws_cdk"
    AZURE_ARM = "azure_arm"
    GCP_DEPLOYMENT_MANAGER = "gcp_dm"
    ANSIBLE = "ansible"
    CHEF = "chef"
    PUPPET = "puppet"


class IaCLanguage(Enum):
    """Programming languages for IaC."""
    HCL = "hcl"  # HashiCorp Configuration Language (Terraform)
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GOLANG = "golang"
    CSHARP = "csharp"
    JSON = "json"
    YAML = "yaml"


@dataclass
class IaCConfiguration:
    """Infrastructure as Code configuration."""
    tool: IaCTool
    language: IaCLanguage
    target_providers: List[CloudProvider]
    output_directory: str
    include_monitoring: bool = True
    include_security: bool = True
    include_networking: bool = True
    include_storage: bool = True
    include_databases: bool = True
    include_kubernetes: bool = True
    version_control_integration: bool = True
    ci_cd_integration: bool = True
    state_management: Dict[str, Any] = field(default_factory=dict)
    variables_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IaCOutput:
    """Generated IaC output."""
    tool: IaCTool
    language: IaCLanguage
    files: Dict[str, str]  # filename -> content
    metadata: Dict[str, Any]
    deployment_commands: List[str]
    validation_commands: List[str]
    cleanup_commands: List[str]


class BaseIaCGenerator(ABC):
    """Base class for IaC generators."""
    
    @abstractmethod
    def generate(self, assessment: Assessment, config: IaCConfiguration) -> IaCOutput:
        """Generate IaC files for the given assessment."""
        pass
    
    @abstractmethod
    def validate_config(self, config: IaCConfiguration) -> List[str]:
        """Validate IaC configuration."""
        pass


class TerraformIaCGenerator(BaseIaCGenerator):
    """Terraform IaC generator."""
    
    def __init__(self):
        self.terraform_generator = TerraformGenerator()
    
    def generate(self, assessment: Assessment, config: IaCConfiguration) -> IaCOutput:
        """Generate Terraform IaC files."""
        
        files = {}
        
        # Generate main Terraform files for each provider
        for provider in config.target_providers:
            terraform_config = self.terraform_generator.generate_terraform_config(
                assessment, provider
            )
            
            # Main configuration file
            files[f"main-{provider.value.lower()}.tf"] = self._dict_to_hcl(terraform_config)
            
            # Variables file
            variables = self._generate_variables(assessment, provider)
            files[f"variables-{provider.value.lower()}.tf"] = variables
            
            # Outputs file
            outputs = self._generate_outputs(provider)
            files[f"outputs-{provider.value.lower()}.tf"] = outputs
        
        # Generate shared files
        files["terraform.tf"] = self._generate_terraform_config()
        files["terraform.tfvars"] = self._generate_tfvars(assessment, config)
        files["versions.tf"] = self._generate_versions(config.target_providers)
        
        # Generate modules
        if config.include_kubernetes:
            files.update(self._generate_kubernetes_module(assessment))
        
        if config.include_monitoring:
            files.update(self._generate_monitoring_module())
        
        if config.include_security:
            files.update(self._generate_security_module())
        
        # Generate deployment scripts
        deployment_commands = [
            "terraform init",
            "terraform plan -out=tfplan",
            "terraform apply tfplan"
        ]
        
        validation_commands = [
            "terraform validate",
            "terraform plan -detailed-exitcode"
        ]
        
        cleanup_commands = [
            "terraform destroy -auto-approve"
        ]
        
        return IaCOutput(
            tool=IaCTool.TERRAFORM,
            language=IaCLanguage.HCL,
            files=files,
            metadata={
                "providers": [p.value for p in config.target_providers],
                "modules": ["kubernetes", "monitoring", "security"] if config.include_kubernetes else ["monitoring", "security"]
            },
            deployment_commands=deployment_commands,
            validation_commands=validation_commands,
            cleanup_commands=cleanup_commands
        )
    
    def validate_config(self, config: IaCConfiguration) -> List[str]:
        """Validate Terraform configuration."""
        errors = []
        
        if config.tool != IaCTool.TERRAFORM:
            errors.append("Configuration is not for Terraform")
        
        if config.language != IaCLanguage.HCL:
            errors.append("Terraform requires HCL language")
        
        if not config.target_providers:
            errors.append("No target providers specified")
        
        return errors
    
    def _dict_to_hcl(self, config_dict: Dict[str, Any]) -> str:
        """Convert dictionary to HCL format."""
        
        def format_value(value):
            if isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, list):
                items = [format_value(item) for item in value]
                return "[" + ", ".join(items) + "]"
            elif isinstance(value, dict):
                items = [f'{k} = {format_value(v)}' for k, v in value.items()]
                return "{\n  " + "\n  ".join(items) + "\n}"
            else:
                return f'"{str(value)}"'
        
        hcl_lines = []
        for block_type, blocks in config_dict.items():
            if isinstance(blocks, dict):
                for block_name, block_config in blocks.items():
                    hcl_lines.append(f'{block_type} "{block_name}" {{')
                    for key, value in block_config.items():
                        hcl_lines.append(f'  {key} = {format_value(value)}')
                    hcl_lines.append("}")
                    hcl_lines.append("")
        
        return "\n".join(hcl_lines)
    
    def _generate_variables(self, assessment: Assessment, provider: CloudProvider) -> str:
        """Generate Terraform variables file."""
        
        variables = {
            "project_name": {
                "description": "Name of the project",
                "type": "string",
                "default": assessment.title.lower().replace(' ', '-')
            },
            "environment": {
                "description": "Environment name",
                "type": "string",
                "default": "dev"
            },
            "region": {
                "description": "Cloud region",
                "type": "string",
                "default": self._get_default_region(provider)
            }
        }
        
        hcl_lines = []
        for var_name, var_config in variables.items():
            hcl_lines.append(f'variable "{var_name}" {{')
            for key, value in var_config.items():
                if isinstance(value, str):
                    hcl_lines.append(f'  {key} = "{value}"')
                else:
                    hcl_lines.append(f'  {key} = {value}')
            hcl_lines.append("}")
            hcl_lines.append("")
        
        return "\n".join(hcl_lines)
    
    def _generate_outputs(self, provider: CloudProvider) -> str:
        """Generate Terraform outputs file."""
        
        if provider == CloudProvider.AWS:
            outputs = {
                "vpc_id": {
                    "description": "ID of the VPC",
                    "value": "${aws_vpc.main.id}"
                },
                "instance_ids": {
                    "description": "IDs of the EC2 instances",
                    "value": "${aws_instance.web[*].id}"
                }
            }
        elif provider == CloudProvider.AZURE:
            outputs = {
                "resource_group_name": {
                    "description": "Name of the resource group",
                    "value": "${azurerm_resource_group.main.name}"
                },
                "vm_ids": {
                    "description": "IDs of the VMs",
                    "value": "${azurerm_linux_virtual_machine.main[*].id}"
                }
            }
        else:  # GCP
            outputs = {
                "project_id": {
                    "description": "GCP project ID",
                    "value": "${var.project_id}"
                },
                "instance_names": {
                    "description": "Names of the compute instances",
                    "value": "${google_compute_instance.default[*].name}"
                }
            }
        
        hcl_lines = []
        for output_name, output_config in outputs.items():
            hcl_lines.append(f'output "{output_name}" {{')
            for key, value in output_config.items():
                hcl_lines.append(f'  {key} = "{value}"')
            hcl_lines.append("}")
            hcl_lines.append("")
        
        return "\n".join(hcl_lines)
    
    def _generate_terraform_config(self) -> str:
        """Generate terraform configuration block."""
        
        return '''terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    bucket = "terraform-state-bucket"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}'''
    
    def _generate_tfvars(self, assessment: Assessment, config: IaCConfiguration) -> str:
        """Generate terraform.tfvars file."""
        
        tfvars = {
            "project_name": assessment.title.lower().replace(' ', '-'),
            "environment": "dev",
            "region": "us-west-2"
        }
        
        lines = []
        for key, value in tfvars.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f'{key} = {value}')
        
        return "\n".join(lines)
    
    def _generate_versions(self, providers: List[CloudProvider]) -> str:
        """Generate versions.tf file."""
        
        provider_configs = []
        
        if CloudProvider.AWS in providers:
            provider_configs.append('''provider "aws" {
  region = var.region
  
  default_tags {
    tags = {
      Environment   = var.environment
      Project      = var.project_name
      ManagedBy    = "terraform"
    }
  }
}''')
        
        if CloudProvider.AZURE in providers:
            provider_configs.append('''provider "azurerm" {
  features {}
}''')
        
        if CloudProvider.GCP in providers:
            provider_configs.append('''provider "google" {
  project = var.project_id
  region  = var.region
}''')
        
        return "\n\n".join(provider_configs)
    
    def _generate_kubernetes_module(self, assessment: Assessment) -> Dict[str, str]:
        """Generate Kubernetes Terraform module."""
        
        files = {}
        
        # Module main file
        files["modules/kubernetes/main.tf"] = '''resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace_name
  }
}

resource "kubernetes_deployment" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.app_name
        }
      }

      spec {
        container {
          image = var.app_image
          name  = var.app_name

          port {
            container_port = var.app_port
          }

          resources {
            limits = {
              cpu    = var.cpu_limit
              memory = var.memory_limit
            }
            requests = {
              cpu    = var.cpu_request
              memory = var.memory_request
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "app" {
  metadata {
    name      = "${var.app_name}-service"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    selector = {
      app = kubernetes_deployment.app.metadata[0].labels.app
    }

    port {
      port        = 80
      target_port = var.app_port
    }

    type = var.service_type
  }
}'''
        
        # Module variables
        files["modules/kubernetes/variables.tf"] = '''variable "namespace_name" {
  description = "Name of the Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
}

variable "app_port" {
  description = "Port the application listens on"
  type        = number
  default     = 8080
}

variable "replicas" {
  description = "Number of replicas"
  type        = number
  default     = 3
}

variable "cpu_limit" {
  description = "CPU limit"
  type        = string
  default     = "500m"
}

variable "memory_limit" {
  description = "Memory limit"
  type        = string
  default     = "512Mi"
}

variable "cpu_request" {
  description = "CPU request"
  type        = string
  default     = "100m"
}

variable "memory_request" {
  description = "Memory request"
  type        = string
  default     = "128Mi"
}

variable "service_type" {
  description = "Kubernetes service type"
  type        = string
  default     = "ClusterIP"
}'''
        
        # Module outputs
        files["modules/kubernetes/outputs.tf"] = '''output "namespace_name" {
  description = "Name of the created namespace"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "deployment_name" {
  description = "Name of the deployment"
  value       = kubernetes_deployment.app.metadata[0].name
}

output "service_name" {
  description = "Name of the service"
  value       = kubernetes_service.app.metadata[0].name
}'''
        
        return files
    
    def _generate_monitoring_module(self) -> Dict[str, str]:
        """Generate monitoring Terraform module."""
        
        files = {}
        
        files["modules/monitoring/main.tf"] = '''resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

resource "kubernetes_config_map" "prometheus_config" {
  metadata {
    name      = "prometheus-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }

  data = {
    "prometheus.yml" = file("${path.module}/configs/prometheus.yml")
  }
}

resource "kubernetes_deployment" "prometheus" {
  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "prometheus"
      }
    }

    template {
      metadata {
        labels = {
          app = "prometheus"
        }
      }

      spec {
        container {
          image = "prom/prometheus:latest"
          name  = "prometheus"

          port {
            container_port = 9090
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/prometheus"
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.prometheus_config.metadata[0].name
          }
        }
      }
    }
  }
}'''
        
        files["modules/monitoring/configs/prometheus.yml"] = '''global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)'''
        
        return files
    
    def _generate_security_module(self) -> Dict[str, str]:
        """Generate security Terraform module."""
        
        files = {}
        
        files["modules/security/main.tf"] = '''resource "kubernetes_network_policy" "deny_all" {
  metadata {
    name      = "deny-all"
    namespace = var.namespace
  }

  spec {
    pod_selector {}

    policy_types = ["Ingress", "Egress"]
  }
}

resource "kubernetes_network_policy" "allow_internal" {
  metadata {
    name      = "allow-internal"
    namespace = var.namespace
  }

  spec {
    pod_selector {}

    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = var.namespace
          }
        }
      }
    }

    egress {
      to {
        namespace_selector {
          match_labels = {
            name = var.namespace
          }
        }
      }
    }

    policy_types = ["Ingress", "Egress"]
  }
}'''
        
        files["modules/security/variables.tf"] = '''variable "namespace" {
  description = "Namespace to apply security policies"
  type        = string
}'''
        
        return files
    
    def _get_default_region(self, provider: CloudProvider) -> str:
        """Get default region for provider."""
        
        region_map = {
            CloudProvider.AWS: "us-west-2",
            CloudProvider.AZURE: "East US",
            CloudProvider.GCP: "us-central1"
        }
        
        return region_map.get(provider, "us-west-2")


class PulumiIaCGenerator(BaseIaCGenerator):
    """Pulumi IaC generator."""
    
    def generate(self, assessment: Assessment, config: IaCConfiguration) -> IaCOutput:
        """Generate Pulumi IaC files."""
        
        files = {}
        
        if config.language == IaCLanguage.PYTHON:
            files.update(self._generate_python_pulumi(assessment, config))
        elif config.language == IaCLanguage.TYPESCRIPT:
            files.update(self._generate_typescript_pulumi(assessment, config))
        else:
            raise ValueError(f"Unsupported language {config.language} for Pulumi")
        
        # Generate common files
        files["Pulumi.yaml"] = self._generate_pulumi_yaml(assessment)
        files["requirements.txt"] = self._generate_requirements()
        
        deployment_commands = [
            "pulumi stack init dev",
            "pulumi preview",
            "pulumi up"
        ]
        
        validation_commands = [
            "pulumi preview --diff"
        ]
        
        cleanup_commands = [
            "pulumi destroy"
        ]
        
        return IaCOutput(
            tool=IaCTool.PULUMI,
            language=config.language,
            files=files,
            metadata={
                "stack": "dev",
                "runtime": config.language.value
            },
            deployment_commands=deployment_commands,
            validation_commands=validation_commands,
            cleanup_commands=cleanup_commands
        )
    
    def validate_config(self, config: IaCConfiguration) -> List[str]:
        """Validate Pulumi configuration."""
        errors = []
        
        if config.tool != IaCTool.PULUMI:
            errors.append("Configuration is not for Pulumi")
        
        if config.language not in [IaCLanguage.PYTHON, IaCLanguage.TYPESCRIPT, IaCLanguage.GOLANG, IaCLanguage.CSHARP]:
            errors.append(f"Unsupported language {config.language} for Pulumi")
        
        return errors
    
    def _generate_python_pulumi(self, assessment: Assessment, config: IaCConfiguration) -> Dict[str, str]:
        """Generate Python Pulumi files."""
        
        files = {}
        
        # Main Python file
        main_content = '''import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
from typing import Dict, Any

# Configuration
config = pulumi.Config()
project_name = config.get("project_name", "''' + assessment.title.lower().replace(' ', '-') + '''")
environment = config.get("environment", "dev")

# Create VPC
vpc = aws.ec2.Vpc(
    "main-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{project_name}-vpc",
        "Environment": environment,
    }
)

# Create subnets
public_subnet = aws.ec2.Subnet(
    "public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{project_name}-public-subnet",
        "Environment": environment,
    }
)

# Create internet gateway
igw = aws.ec2.InternetGateway(
    "internet-gateway",
    vpc_id=vpc.id,
    tags={
        "Name": f"{project_name}-igw",
        "Environment": environment,
    }
)

# Create route table
route_table = aws.ec2.RouteTable(
    "public-route-table",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={
        "Name": f"{project_name}-public-rt",
        "Environment": environment,
    }
)

# Associate route table with subnet
route_table_association = aws.ec2.RouteTableAssociation(
    "public-route-table-association",
    subnet_id=public_subnet.id,
    route_table_id=route_table.id,
)

# Create security group
security_group = aws.ec2.SecurityGroup(
    "web-secgrp",
    description="Allow HTTP and SSH traffic",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={
        "Name": f"{project_name}-sg",
        "Environment": environment,
    }
)

# Create EC2 instances
instances = []
for i in range(3):
    instance = aws.ec2.Instance(
        f"web-server-{i}",
        ami="ami-0c02fb55956c7d316",  # Amazon Linux 2 AMI
        instance_type="t3.micro",
        vpc_security_group_ids=[security_group.id],
        subnet_id=public_subnet.id,
        tags={
            "Name": f"{project_name}-web-{i}",
            "Environment": environment,
        }
    )
    instances.append(instance)

# Export values
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("instance_ids", [instance.id for instance in instances])
pulumi.export("public_ips", [instance.public_ip for instance in instances])
'''
        
        files["__main__.py"] = main_content
        
        return files
    
    def _generate_typescript_pulumi(self, assessment: Assessment, config: IaCConfiguration) -> Dict[str, str]:
        """Generate TypeScript Pulumi files."""
        
        files = {}
        
        # Main TypeScript file
        main_content = '''import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as k8s from "@pulumi/kubernetes";

// Configuration
const config = new pulumi.Config();
const projectName = config.get("projectName") || "''' + assessment.title.lower().replace(' ', '-') + '''";
const environment = config.get("environment") || "dev";

// Create VPC
const vpc = new aws.ec2.Vpc("main-vpc", {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${projectName}-vpc`,
        Environment: environment,
    },
});

// Create public subnet
const publicSubnet = new aws.ec2.Subnet("public-subnet", {
    vpcId: vpc.id,
    cidrBlock: "10.0.1.0/24",
    availabilityZone: "us-west-2a",
    mapPublicIpOnLaunch: true,
    tags: {
        Name: `${projectName}-public-subnet`,
        Environment: environment,
    },
});

// Create Internet Gateway
const internetGateway = new aws.ec2.InternetGateway("internet-gateway", {
    vpcId: vpc.id,
    tags: {
        Name: `${projectName}-igw`,
        Environment: environment,
    },
});

// Create route table
const routeTable = new aws.ec2.RouteTable("public-route-table", {
    vpcId: vpc.id,
    routes: [
        {
            cidrBlock: "0.0.0.0/0",
            gatewayId: internetGateway.id,
        },
    ],
    tags: {
        Name: `${projectName}-public-rt`,
        Environment: environment,
    },
});

// Associate route table with subnet
const routeTableAssociation = new aws.ec2.RouteTableAssociation("public-route-table-association", {
    subnetId: publicSubnet.id,
    routeTableId: routeTable.id,
});

// Create security group
const securityGroup = new aws.ec2.SecurityGroup("web-secgrp", {
    description: "Allow HTTP and SSH traffic",
    vpcId: vpc.id,
    ingress: [
        { protocol: "tcp", fromPort: 22, toPort: 22, cidrBlocks: ["0.0.0.0/0"] },
        { protocol: "tcp", fromPort: 80, toPort: 80, cidrBlocks: ["0.0.0.0/0"] },
    ],
    egress: [
        { protocol: "-1", fromPort: 0, toPort: 0, cidrBlocks: ["0.0.0.0/0"] },
    ],
    tags: {
        Name: `${projectName}-sg`,
        Environment: environment,
    },
});

// Create EC2 instances
const instances: aws.ec2.Instance[] = [];
for (let i = 0; i < 3; i++) {
    const instance = new aws.ec2.Instance(`web-server-${i}`, {
        ami: "ami-0c02fb55956c7d316", // Amazon Linux 2 AMI
        instanceType: "t3.micro",
        vpcSecurityGroupIds: [securityGroup.id],
        subnetId: publicSubnet.id,
        tags: {
            Name: `${projectName}-web-${i}`,
            Environment: environment,
        },
    });
    instances.push(instance);
}

// Export values
export const vpcId = vpc.id;
export const publicSubnetId = publicSubnet.id;
export const securityGroupId = securityGroup.id;
export const instanceIds = instances.map(instance => instance.id);
export const publicIps = instances.map(instance => instance.publicIp);
'''
        
        files["index.ts"] = main_content
        files["package.json"] = self._generate_package_json(assessment)
        files["tsconfig.json"] = self._generate_tsconfig()
        
        return files
    
    def _generate_pulumi_yaml(self, assessment: Assessment) -> str:
        """Generate Pulumi.yaml file."""
        
        return f'''name: {assessment.title.lower().replace(' ', '-')}
runtime: python
description: Infrastructure for {assessment.title}
template:
  config:
    project_name:
      description: Name of the project
      default: {assessment.title.lower().replace(' ', '-')}
    environment:
      description: Environment name
      default: dev
'''
    
    def _generate_requirements(self) -> str:
        """Generate requirements.txt for Python."""
        
        return '''pulumi>=3.0.0,<4.0.0
pulumi-aws>=5.0.0,<6.0.0
pulumi-kubernetes>=3.0.0,<4.0.0
pulumi-random>=4.0.0,<5.0.0
'''
    
    def _generate_package_json(self, assessment: Assessment) -> str:
        """Generate package.json for TypeScript."""
        
        return f'''{{
    "name": "{assessment.title.lower().replace(' ', '-')}",
    "version": "1.0.0",
    "main": "index.ts",
    "scripts": {{
        "build": "tsc",
        "deploy": "pulumi up",
        "destroy": "pulumi destroy"
    }},
    "devDependencies": {{
        "@types/node": "^16",
        "typescript": "^4.0.0"
    }},
    "dependencies": {{
        "@pulumi/pulumi": "^3.0.0",
        "@pulumi/aws": "^5.0.0",
        "@pulumi/kubernetes": "^3.0.0"
    }}
}}'''
    
    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json."""
        
        return '''{
    "compilerOptions": {
        "target": "es2016",
        "module": "commonjs",
        "moduleResolution": "node",
        "declaration": true,
        "outDir": "./bin",
        "strict": true,
        "noUnusedLocals": true,
        "noUnusedParameters": true,
        "noImplicitReturns": true,
        "noFallthroughCasesInSwitch": true,
        "forceConsistentCasingInFileNames": true
    },
    "files": [
        "index.ts"
    ]
}'''


class IaCGenerator:
    """
    Main IaC Generator that orchestrates multiple IaC tools.
    
    Provides a unified interface for generating Infrastructure as Code
    using different tools and languages based on requirements.
    """
    
    def __init__(self):
        self.generators = {
            IaCTool.TERRAFORM: TerraformIaCGenerator(),
            IaCTool.PULUMI: PulumiIaCGenerator(),
        }
    
    def generate_iac(
        self,
        assessment: Assessment,
        config: IaCConfiguration,
        app_configs: Optional[List[ApplicationConfig]] = None
    ) -> IaCOutput:
        """
        Generate Infrastructure as Code based on configuration.
        
        Args:
            assessment: Assessment with infrastructure requirements
            config: IaC generation configuration
            app_configs: Optional application configurations
            
        Returns:
            IaCOutput with generated files and metadata
        """
        try:
            logger.info(f"Generating IaC using {config.tool.value} with {config.language.value}")
            
            # Validate configuration
            validation_errors = self.validate_configuration(config)
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {', '.join(validation_errors)}")
            
            # Get appropriate generator
            generator = self.generators.get(config.tool)
            if not generator:
                raise ValueError(f"Unsupported IaC tool: {config.tool}")
            
            # Generate IaC
            result = generator.generate(assessment, config)
            
            # Add common files
            result.files.update(self._generate_common_files(assessment, config))
            
            # Add CI/CD integration if requested
            if config.ci_cd_integration:
                result.files.update(self._generate_cicd_files(config))
            
            logger.info(f"Generated {len(result.files)} IaC files")
            return result
            
        except Exception as e:
            logger.error(f"IaC generation failed: {e}")
            raise
    
    def validate_configuration(self, config: IaCConfiguration) -> List[str]:
        """Validate IaC configuration."""
        
        errors = []
        
        # Basic validation
        if not config.target_providers:
            errors.append("No target cloud providers specified")
        
        if not config.output_directory:
            errors.append("No output directory specified")
        
        # Tool-specific validation
        generator = self.generators.get(config.tool)
        if generator:
            errors.extend(generator.validate_config(config))
        else:
            errors.append(f"Unsupported IaC tool: {config.tool}")
        
        return errors
    
    def list_supported_tools(self) -> List[IaCTool]:
        """List supported IaC tools."""
        return list(self.generators.keys())
    
    def list_supported_languages(self, tool: IaCTool) -> List[IaCLanguage]:
        """List supported languages for a specific tool."""
        
        language_map = {
            IaCTool.TERRAFORM: [IaCLanguage.HCL],
            IaCTool.PULUMI: [IaCLanguage.PYTHON, IaCLanguage.TYPESCRIPT, IaCLanguage.GOLANG, IaCLanguage.CSHARP],
            IaCTool.AWS_CDK: [IaCLanguage.PYTHON, IaCLanguage.TYPESCRIPT, IaCLanguage.JAVASCRIPT],
            IaCTool.AZURE_ARM: [IaCLanguage.JSON],
            IaCTool.GCP_DEPLOYMENT_MANAGER: [IaCLanguage.YAML]
        }
        
        return language_map.get(tool, [])
    
    def _generate_common_files(self, assessment: Assessment, config: IaCConfiguration) -> Dict[str, str]:
        """Generate common files for all IaC tools."""
        
        files = {}
        
        # README
        files["README.md"] = self._generate_readme(assessment, config)
        
        # .gitignore
        files[".gitignore"] = self._generate_gitignore(config.tool)
        
        # Makefile
        files["Makefile"] = self._generate_makefile(config.tool)
        
        return files
    
    def _generate_cicd_files(self, config: IaCConfiguration) -> Dict[str, str]:
        """Generate CI/CD pipeline files."""
        
        files = {}
        
        # GitHub Actions
        files[".github/workflows/infrastructure.yml"] = self._generate_github_actions(config)
        
        # GitLab CI
        files[".gitlab-ci.yml"] = self._generate_gitlab_ci(config)
        
        return files
    
    def _generate_readme(self, assessment: Assessment, config: IaCConfiguration) -> str:
        """Generate README.md file."""
        
        return f'''# {assessment.title} Infrastructure

Infrastructure as Code for {assessment.title} using {config.tool.value}.

## Overview

This repository contains the infrastructure code for deploying and managing the infrastructure for {assessment.title}.

## Prerequisites

- {config.tool.value.title()} installed
- Cloud provider CLI tools configured
- Appropriate permissions for resource creation

## Deployment

1. Initialize the infrastructure:
   ```bash
   make init
   ```

2. Plan the deployment:
   ```bash
   make plan
   ```

3. Apply the changes:
   ```bash
   make apply
   ```

## Cleanup

To destroy all resources:
```bash
make destroy
```

## Structure

- `main.*` - Main infrastructure configuration
- `variables.*` - Variable definitions
- `outputs.*` - Output definitions
- `modules/` - Reusable modules

## Target Providers

{', '.join([provider.value for provider in config.target_providers])}

## Generated by

Infra Mind AI Infrastructure Platform
'''
    
    def _generate_gitignore(self, tool: IaCTool) -> str:
        """Generate .gitignore file."""
        
        common_ignores = '''# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.log
'''
        
        if tool == IaCTool.TERRAFORM:
            return common_ignores + '''
# Terraform files
*.tfstate
*.tfstate.*
*.tfplan
.terraform/
.terraform.lock.hcl

# Variable files
*.tfvars
!example.tfvars
'''
        elif tool == IaCTool.PULUMI:
            return common_ignores + '''
# Pulumi files
.pulumi/

# Python
__pycache__/
*.pyc
venv/
.env

# Node.js
node_modules/
*.tgz
'''
        else:
            return common_ignores
    
    def _generate_makefile(self, tool: IaCTool) -> str:
        """Generate Makefile."""
        
        if tool == IaCTool.TERRAFORM:
            return '''.PHONY: init plan apply destroy clean validate fmt

init:
	terraform init

plan:
	terraform plan -out=tfplan

apply:
	terraform apply tfplan

destroy:
	terraform destroy -auto-approve

clean:
	rm -f tfplan
	rm -rf .terraform/

validate:
	terraform validate

fmt:
	terraform fmt -recursive

check: validate fmt
	terraform plan -detailed-exitcode

help:
	@echo "Available targets:"
	@echo "  init     - Initialize Terraform"
	@echo "  plan     - Create execution plan"
	@echo "  apply    - Apply changes"
	@echo "  destroy  - Destroy infrastructure"
	@echo "  clean    - Clean temporary files"
	@echo "  validate - Validate configuration"
	@echo "  fmt      - Format files"
	@echo "  check    - Run validation and formatting"
'''
        elif tool == IaCTool.PULUMI:
            return '''.PHONY: init preview up destroy clean

init:
	pulumi stack init dev

preview:
	pulumi preview

up:
	pulumi up

destroy:
	pulumi destroy

clean:
	pulumi stack rm dev --yes

check:
	pulumi preview --diff

help:
	@echo "Available targets:"
	@echo "  init     - Initialize Pulumi stack"
	@echo "  preview  - Preview changes"
	@echo "  up       - Deploy infrastructure"
	@echo "  destroy  - Destroy infrastructure"
	@echo "  clean    - Remove stack"
	@echo "  check    - Check for changes"
'''
        else:
            return '''# Generic Makefile
help:
	@echo "Available targets:"
	@echo "  help     - Show this help message"
'''
    
    def _generate_github_actions(self, config: IaCConfiguration) -> str:
        """Generate GitHub Actions workflow."""
        
        if config.tool == IaCTool.TERRAFORM:
            return '''name: 'Infrastructure'

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  terraform:
    name: 'Terraform'
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.0.0

    - name: Terraform Init
      run: terraform init

    - name: Terraform Format
      run: terraform fmt -check

    - name: Terraform Validate
      run: terraform validate

    - name: Terraform Plan
      run: terraform plan -no-color
      if: github.event_name == 'pull_request'

    - name: Terraform Apply
      run: terraform apply -auto-approve
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
'''
        elif config.tool == IaCTool.PULUMI:
            return '''name: 'Infrastructure'

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  pulumi:
    name: 'Pulumi'
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Pulumi Preview
      uses: pulumi/actions@v4
      with:
        command: preview
        stack-name: dev
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
      if: github.event_name == 'pull_request'

    - name: Pulumi Up
      uses: pulumi/actions@v4
      with:
        command: up
        stack-name: dev
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
'''
        else:
            return '''name: 'Infrastructure'

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  deploy:
    name: 'Deploy'
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
      
    - name: Deploy
      run: echo "Add deployment steps here"
'''
    
    def _generate_gitlab_ci(self, config: IaCConfiguration) -> str:
        """Generate GitLab CI configuration."""
        
        return '''stages:
  - validate
  - plan
  - deploy

variables:
  TF_ROOT: ${CI_PROJECT_DIR}

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - ${TF_ROOT}/.terraform

before_script:
  - cd ${TF_ROOT}

validate:
  stage: validate
  script:
    - terraform init -backend=false
    - terraform validate
    - terraform fmt -check
  only:
    - branches

plan:
  stage: plan
  script:
    - terraform init
    - terraform plan -out=tfplan
  artifacts:
    name: plan
    paths:
      - ${TF_ROOT}/tfplan
  only:
    - branches

deploy:
  stage: deploy
  script:
    - terraform init
    - terraform apply -auto-approve tfplan
  dependencies:
    - plan
  only:
    - main
'''