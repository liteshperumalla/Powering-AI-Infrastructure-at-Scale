"""
Kubernetes Deployment Management System

Provides automated Kubernetes deployment generation, management,
and orchestration capabilities for multi-cloud environments.
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import base64
from pathlib import Path

from ..models.assessment import Assessment
from ..schemas.base import CloudProvider
from loguru import logger


class KubernetesResourceType(Enum):
    """Kubernetes resource types."""
    DEPLOYMENT = "Deployment"
    SERVICE = "Service"
    INGRESS = "Ingress"
    CONFIGMAP = "ConfigMap"
    SECRET = "Secret"
    PERSISTENT_VOLUME_CLAIM = "PersistentVolumeClaim"
    HORIZONTAL_POD_AUTOSCALER = "HorizontalPodAutoscaler"
    NETWORK_POLICY = "NetworkPolicy"
    SERVICE_ACCOUNT = "ServiceAccount"
    ROLE = "Role"
    ROLE_BINDING = "RoleBinding"
    NAMESPACE = "Namespace"


@dataclass
class KubernetesResource:
    """Kubernetes resource configuration."""
    api_version: str
    kind: KubernetesResourceType
    metadata: Dict[str, Any]
    spec: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None


@dataclass
class ApplicationConfig:
    """Application configuration for Kubernetes deployment."""
    name: str
    image: str
    port: int
    replicas: int = 3
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"
    environment_variables: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    health_check_path: str = "/health"
    service_type: str = "ClusterIP"
    autoscaling: bool = False
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_percentage: int = 70


class KubernetesManager:
    """
    Manages Kubernetes deployments and configurations.
    
    Provides automated generation of Kubernetes manifests from assessment data
    and manages deployment lifecycles across different cloud providers.
    """
    
    def __init__(self):
        self.api_versions = {
            KubernetesResourceType.DEPLOYMENT: "apps/v1",
            KubernetesResourceType.SERVICE: "v1",
            KubernetesResourceType.INGRESS: "networking.k8s.io/v1",
            KubernetesResourceType.CONFIGMAP: "v1",
            KubernetesResourceType.SECRET: "v1",
            KubernetesResourceType.PERSISTENT_VOLUME_CLAIM: "v1",
            KubernetesResourceType.HORIZONTAL_POD_AUTOSCALER: "autoscaling/v2",
            KubernetesResourceType.NETWORK_POLICY: "networking.k8s.io/v1",
            KubernetesResourceType.SERVICE_ACCOUNT: "v1",
            KubernetesResourceType.ROLE: "rbac.authorization.k8s.io/v1",
            KubernetesResourceType.ROLE_BINDING: "rbac.authorization.k8s.io/v1",
            KubernetesResourceType.NAMESPACE: "v1"
        }
    
    def generate_kubernetes_manifests(self, assessment: Assessment, app_configs: List[ApplicationConfig]) -> Dict[str, str]:
        """
        Generate complete Kubernetes manifests from assessment and application configurations.
        
        Args:
            assessment: Assessment with infrastructure requirements
            app_configs: List of application configurations
            
        Returns:
            Dictionary with filename -> YAML manifest content
        """
        try:
            logger.info(f"Generating Kubernetes manifests for assessment {assessment.id}")
            
            manifests = {}
            
            # Generate namespace
            namespace_name = f"{assessment.title.lower().replace(' ', '-')}-{assessment.id[:8]}"
            namespace_manifest = self._generate_namespace(namespace_name)
            manifests["00-namespace.yaml"] = namespace_manifest
            
            # Generate application manifests for each app
            for i, app_config in enumerate(app_configs):
                app_manifests = self._generate_application_manifests(
                    app_config, 
                    namespace_name, 
                    assessment
                )
                
                for resource_type, manifest in app_manifests.items():
                    filename = f"{i+1:02d}-{app_config.name}-{resource_type.lower()}.yaml"
                    manifests[filename] = manifest
            
            # Generate shared resources
            shared_manifests = self._generate_shared_resources(assessment, namespace_name)
            for resource_name, manifest in shared_manifests.items():
                manifests[f"90-{resource_name}.yaml"] = manifest
            
            # Generate ingress controller and monitoring if required
            if self._requires_ingress(app_configs):
                ingress_manifest = self._generate_ingress_controller(app_configs, namespace_name)
                manifests["95-ingress.yaml"] = ingress_manifest
            
            monitoring_manifests = self._generate_monitoring_stack(namespace_name)
            manifests.update(monitoring_manifests)
            
            logger.info(f"Generated {len(manifests)} Kubernetes manifest files")
            return manifests
            
        except Exception as e:
            logger.error(f"Failed to generate Kubernetes manifests: {e}")
            raise
    
    def _generate_namespace(self, name: str) -> str:
        """Generate namespace manifest."""
        
        resource = KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.NAMESPACE],
            kind=KubernetesResourceType.NAMESPACE,
            metadata={
                "name": name,
                "labels": {
                    "app.kubernetes.io/managed-by": "infra-mind",
                    "app.kubernetes.io/part-of": "infrastructure-platform"
                }
            },
            spec={}
        )
        
        return self._resource_to_yaml(resource)
    
    def _generate_application_manifests(self, app_config: ApplicationConfig, namespace: str, assessment: Assessment) -> Dict[str, str]:
        """Generate all manifests for a single application."""
        
        manifests = {}
        
        # Deployment
        deployment = self._generate_deployment(app_config, namespace, assessment)
        manifests["deployment"] = self._resource_to_yaml(deployment)
        
        # Service
        service = self._generate_service(app_config, namespace)
        manifests["service"] = self._resource_to_yaml(service)
        
        # ConfigMap (if environment variables exist)
        if app_config.environment_variables:
            configmap = self._generate_configmap(app_config, namespace)
            manifests["configmap"] = self._resource_to_yaml(configmap)
        
        # PersistentVolumeClaim (if volumes are configured)
        if app_config.volumes:
            for volume in app_config.volumes:
                if volume.get("type") == "persistent":
                    pvc = self._generate_pvc(app_config, namespace, volume)
                    manifests[f"pvc-{volume['name']}"] = self._resource_to_yaml(pvc)
        
        # HorizontalPodAutoscaler (if autoscaling is enabled)
        if app_config.autoscaling:
            hpa = self._generate_hpa(app_config, namespace)
            manifests["hpa"] = self._resource_to_yaml(hpa)
        
        return manifests
    
    def _generate_deployment(self, app_config: ApplicationConfig, namespace: str, assessment: Assessment) -> KubernetesResource:
        """Generate Deployment resource."""
        
        # Determine replica count based on assessment requirements
        performance_reqs = assessment.technical_requirements.get("performance_requirements", {})
        availability_percent = performance_reqs.get("availability_percent", 99.0)
        
        # Adjust replicas based on availability requirements
        if availability_percent >= 99.9:
            replicas = max(app_config.replicas, 5)  # High availability
        elif availability_percent >= 99.5:
            replicas = max(app_config.replicas, 3)  # Standard availability
        else:
            replicas = app_config.replicas
        
        # Build container spec
        container_spec = {
            "name": app_config.name,
            "image": app_config.image,
            "ports": [{
                "containerPort": app_config.port,
                "name": "http"
            }],
            "resources": {
                "requests": {
                    "cpu": app_config.cpu_request,
                    "memory": app_config.memory_request
                },
                "limits": {
                    "cpu": app_config.cpu_limit,
                    "memory": app_config.memory_limit
                }
            },
            "livenessProbe": {
                "httpGet": {
                    "path": app_config.health_check_path,
                    "port": "http"
                },
                "initialDelaySeconds": 30,
                "periodSeconds": 10
            },
            "readinessProbe": {
                "httpGet": {
                    "path": app_config.health_check_path,
                    "port": "http"
                },
                "initialDelaySeconds": 5,
                "periodSeconds": 5
            }
        }
        
        # Add environment variables
        if app_config.environment_variables:
            env_vars = []
            for key, value in app_config.environment_variables.items():
                env_vars.append({
                    "name": key,
                    "valueFrom": {
                        "configMapKeyRef": {
                            "name": f"{app_config.name}-config",
                            "key": key
                        }
                    }
                })
            container_spec["env"] = env_vars
        
        # Add volume mounts
        if app_config.volumes:
            volume_mounts = []
            for volume in app_config.volumes:
                volume_mounts.append({
                    "name": volume["name"],
                    "mountPath": volume["mount_path"]
                })
            container_spec["volumeMounts"] = volume_mounts
        
        # Build pod template spec
        pod_template_spec = {
            "metadata": {
                "labels": {
                    "app": app_config.name,
                    "version": "v1",
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/instance": f"{app_config.name}-instance",
                    "app.kubernetes.io/version": "1.0.0",
                    "app.kubernetes.io/component": "backend",
                    "app.kubernetes.io/part-of": "infrastructure-platform",
                    "app.kubernetes.io/managed-by": "infra-mind"
                }
            },
            "spec": {
                "containers": [container_spec],
                "restartPolicy": "Always"
            }
        }
        
        # Add volumes to pod spec
        if app_config.volumes:
            volumes = []
            for volume in app_config.volumes:
                if volume.get("type") == "persistent":
                    volumes.append({
                        "name": volume["name"],
                        "persistentVolumeClaim": {
                            "claimName": f"{app_config.name}-{volume['name']}-pvc"
                        }
                    })
                elif volume.get("type") == "configmap":
                    volumes.append({
                        "name": volume["name"],
                        "configMap": {
                            "name": volume["configmap_name"]
                        }
                    })
            pod_template_spec["spec"]["volumes"] = volumes
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.DEPLOYMENT],
            kind=KubernetesResourceType.DEPLOYMENT,
            metadata={
                "name": app_config.name,
                "namespace": namespace,
                "labels": {
                    "app": app_config.name,
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/instance": f"{app_config.name}-instance",
                    "app.kubernetes.io/version": "1.0.0",
                    "app.kubernetes.io/component": "backend",
                    "app.kubernetes.io/part-of": "infrastructure-platform",
                    "app.kubernetes.io/managed-by": "infra-mind"
                }
            },
            spec={
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": app_config.name
                    }
                },
                "template": pod_template_spec,
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxSurge": 1,
                        "maxUnavailable": 0
                    }
                }
            }
        )
    
    def _generate_service(self, app_config: ApplicationConfig, namespace: str) -> KubernetesResource:
        """Generate Service resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.SERVICE],
            kind=KubernetesResourceType.SERVICE,
            metadata={
                "name": f"{app_config.name}-service",
                "namespace": namespace,
                "labels": {
                    "app": app_config.name,
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/component": "service"
                }
            },
            spec={
                "type": app_config.service_type,
                "ports": [{
                    "port": 80,
                    "targetPort": app_config.port,
                    "protocol": "TCP",
                    "name": "http"
                }],
                "selector": {
                    "app": app_config.name
                }
            }
        )
    
    def _generate_configmap(self, app_config: ApplicationConfig, namespace: str) -> KubernetesResource:
        """Generate ConfigMap resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.CONFIGMAP],
            kind=KubernetesResourceType.CONFIGMAP,
            metadata={
                "name": f"{app_config.name}-config",
                "namespace": namespace,
                "labels": {
                    "app": app_config.name,
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/component": "config"
                }
            },
            spec={},
            data=app_config.environment_variables
        )
    
    def _generate_pvc(self, app_config: ApplicationConfig, namespace: str, volume: Dict[str, Any]) -> KubernetesResource:
        """Generate PersistentVolumeClaim resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.PERSISTENT_VOLUME_CLAIM],
            kind=KubernetesResourceType.PERSISTENT_VOLUME_CLAIM,
            metadata={
                "name": f"{app_config.name}-{volume['name']}-pvc",
                "namespace": namespace,
                "labels": {
                    "app": app_config.name,
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/component": "storage"
                }
            },
            spec={
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": volume.get("size", "10Gi")
                    }
                },
                "storageClassName": volume.get("storage_class", "standard")
            }
        )
    
    def _generate_hpa(self, app_config: ApplicationConfig, namespace: str) -> KubernetesResource:
        """Generate HorizontalPodAutoscaler resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.HORIZONTAL_POD_AUTOSCALER],
            kind=KubernetesResourceType.HORIZONTAL_POD_AUTOSCALER,
            metadata={
                "name": f"{app_config.name}-hpa",
                "namespace": namespace,
                "labels": {
                    "app": app_config.name,
                    "app.kubernetes.io/name": app_config.name,
                    "app.kubernetes.io/component": "autoscaler"
                }
            },
            spec={
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app_config.name
                },
                "minReplicas": app_config.min_replicas,
                "maxReplicas": app_config.max_replicas,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": app_config.target_cpu_percentage
                        }
                    }
                }],
                "behavior": {
                    "scaleUp": {
                        "stabilizationWindowSeconds": 60,
                        "policies": [{
                            "type": "Percent",
                            "value": 50,
                            "periodSeconds": 60
                        }]
                    },
                    "scaleDown": {
                        "stabilizationWindowSeconds": 300,
                        "policies": [{
                            "type": "Percent", 
                            "value": 25,
                            "periodSeconds": 60
                        }]
                    }
                }
            }
        )
    
    def _generate_shared_resources(self, assessment: Assessment, namespace: str) -> Dict[str, str]:
        """Generate shared resources like NetworkPolicies, RBAC, etc."""
        
        manifests = {}
        
        # Network Policy for security
        security_reqs = assessment.technical_requirements.get("security_requirements", {})
        if security_reqs.get("vpc") or security_reqs.get("monitoring"):
            network_policy = self._generate_network_policy(namespace)
            manifests["network-policy"] = self._resource_to_yaml(network_policy)
        
        # Service Account and RBAC
        service_account = self._generate_service_account(namespace)
        manifests["service-account"] = self._resource_to_yaml(service_account)
        
        role = self._generate_role(namespace)
        manifests["role"] = self._resource_to_yaml(role)
        
        role_binding = self._generate_role_binding(namespace)
        manifests["role-binding"] = self._resource_to_yaml(role_binding)
        
        return manifests
    
    def _generate_network_policy(self, namespace: str) -> KubernetesResource:
        """Generate NetworkPolicy for pod-to-pod communication."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.NETWORK_POLICY],
            kind=KubernetesResourceType.NETWORK_POLICY,
            metadata={
                "name": "default-deny-all",
                "namespace": namespace
            },
            spec={
                "podSelector": {},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [{
                        "namespaceSelector": {
                            "matchLabels": {
                                "name": namespace
                            }
                        }
                    }]
                }],
                "egress": [{
                    "to": [{
                        "namespaceSelector": {
                            "matchLabels": {
                                "name": namespace
                            }
                        }
                    }]
                }, {
                    "to": [],
                    "ports": [{
                        "protocol": "TCP",
                        "port": 53
                    }, {
                        "protocol": "UDP", 
                        "port": 53
                    }]
                }]
            }
        )
    
    def _generate_service_account(self, namespace: str) -> KubernetesResource:
        """Generate ServiceAccount resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.SERVICE_ACCOUNT],
            kind=KubernetesResourceType.SERVICE_ACCOUNT,
            metadata={
                "name": "infra-mind-service-account",
                "namespace": namespace
            },
            spec={}
        )
    
    def _generate_role(self, namespace: str) -> KubernetesResource:
        """Generate Role resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.ROLE],
            kind=KubernetesResourceType.ROLE,
            metadata={
                "name": "infra-mind-role",
                "namespace": namespace
            },
            spec={},
            # Note: 'rules' should be in spec, but pydantic might not like the structure
        )
        
        # Manually add rules after creation
        role = KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.ROLE],
            kind=KubernetesResourceType.ROLE,
            metadata={
                "name": "infra-mind-role", 
                "namespace": namespace
            },
            spec={}
        )
        
        # Add rules directly to spec
        role.spec["rules"] = [
            {
                "apiGroups": [""],
                "resources": ["pods", "services", "configmaps"],
                "verbs": ["get", "list", "watch"]
            },
            {
                "apiGroups": ["apps"],
                "resources": ["deployments"],
                "verbs": ["get", "list", "watch"]
            }
        ]
        
        return role
    
    def _generate_role_binding(self, namespace: str) -> KubernetesResource:
        """Generate RoleBinding resource."""
        
        return KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.ROLE_BINDING],
            kind=KubernetesResourceType.ROLE_BINDING,
            metadata={
                "name": "infra-mind-role-binding",
                "namespace": namespace
            },
            spec={
                "subjects": [{
                    "kind": "ServiceAccount",
                    "name": "infra-mind-service-account",
                    "namespace": namespace
                }],
                "roleRef": {
                    "kind": "Role",
                    "name": "infra-mind-role",
                    "apiGroup": "rbac.authorization.k8s.io"
                }
            }
        )
    
    def _requires_ingress(self, app_configs: List[ApplicationConfig]) -> bool:
        """Check if ingress controller is needed."""
        return any(app.service_type == "LoadBalancer" for app in app_configs)
    
    def _generate_ingress_controller(self, app_configs: List[ApplicationConfig], namespace: str) -> str:
        """Generate Ingress controller configuration."""
        
        ingress_rules = []
        for app_config in app_configs:
            if app_config.service_type in ["LoadBalancer", "ClusterIP"]:
                ingress_rules.append({
                    "host": f"{app_config.name}.local",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": f"{app_config.name}-service",
                                    "port": {
                                        "number": 80
                                    }
                                }
                            }
                        }]
                    }
                })
        
        ingress = KubernetesResource(
            api_version=self.api_versions[KubernetesResourceType.INGRESS],
            kind=KubernetesResourceType.INGRESS,
            metadata={
                "name": "infra-mind-ingress",
                "namespace": namespace,
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                }
            },
            spec={
                "rules": ingress_rules,
                "tls": [{
                    "hosts": [rule["host"] for rule in ingress_rules],
                    "secretName": "infra-mind-tls"
                }]
            }
        )
        
        return self._resource_to_yaml(ingress)
    
    def _generate_monitoring_stack(self, namespace: str) -> Dict[str, str]:
        """Generate monitoring stack (Prometheus, Grafana, etc.)."""
        
        manifests = {}
        
        # ServiceMonitor for Prometheus
        service_monitor = KubernetesResource(
            api_version="monitoring.coreos.com/v1",
            kind="ServiceMonitor",
            metadata={
                "name": "infra-mind-monitor",
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/name": "infra-mind-monitor",
                    "app.kubernetes.io/part-of": "monitoring"
                }
            },
            spec={
                "selector": {
                    "matchLabels": {
                        "app.kubernetes.io/component": "service"
                    }
                },
                "endpoints": [{
                    "port": "http",
                    "interval": "30s",
                    "path": "/metrics"
                }]
            }
        )
        
        manifests["99-monitoring-servicemonitor"] = self._resource_to_yaml(service_monitor)
        
        return manifests
    
    def _resource_to_yaml(self, resource: KubernetesResource) -> str:
        """Convert KubernetesResource to YAML string."""
        
        # Build the complete resource dictionary
        resource_dict = {
            "apiVersion": resource.api_version,
            "kind": resource.kind.value,
            "metadata": resource.metadata,
            "spec": resource.spec
        }
        
        # Add data field if it exists (for ConfigMaps and Secrets)
        if resource.data is not None:
            resource_dict["data"] = resource.data
        
        return yaml.dump(resource_dict, default_flow_style=False, sort_keys=False)
    
    def generate_helm_chart(self, assessment: Assessment, app_configs: List[ApplicationConfig]) -> Dict[str, str]:
        """
        Generate a Helm chart from assessment and application configurations.
        
        Args:
            assessment: Assessment with infrastructure requirements
            app_configs: List of application configurations
            
        Returns:
            Dictionary with filename -> content for Helm chart
        """
        try:
            logger.info(f"Generating Helm chart for assessment {assessment.id}")
            
            chart_files = {}
            
            # Chart.yaml
            chart_files["Chart.yaml"] = self._generate_chart_yaml(assessment)
            
            # values.yaml
            chart_files["values.yaml"] = self._generate_values_yaml(app_configs, assessment)
            
            # Templates
            templates = self._generate_helm_templates(app_configs, assessment)
            for template_name, template_content in templates.items():
                chart_files[f"templates/{template_name}"] = template_content
            
            # helpers.tpl
            chart_files["templates/_helpers.tpl"] = self._generate_helpers_tpl()
            
            logger.info(f"Generated Helm chart with {len(chart_files)} files")
            return chart_files
            
        except Exception as e:
            logger.error(f"Failed to generate Helm chart: {e}")
            raise
    
    def _generate_chart_yaml(self, assessment: Assessment) -> str:
        """Generate Chart.yaml for Helm chart."""
        
        chart_info = {
            "apiVersion": "v2",
            "name": assessment.title.lower().replace(' ', '-'),
            "description": f"Helm chart for {assessment.title}",
            "version": "0.1.0",
            "appVersion": "1.0.0",
            "type": "application",
            "keywords": ["infrastructure", "microservices", "kubernetes"],
            "maintainers": [{
                "name": "Infra Mind",
                "email": "support@infra-mind.com"
            }]
        }
        
        return yaml.dump(chart_info, default_flow_style=False)
    
    def _generate_values_yaml(self, app_configs: List[ApplicationConfig], assessment: Assessment) -> str:
        """Generate values.yaml for Helm chart."""
        
        values = {
            "global": {
                "namespace": f"{assessment.title.lower().replace(' ', '-')}-{assessment.id[:8]}",
                "labels": {
                    "app.kubernetes.io/managed-by": "infra-mind",
                    "app.kubernetes.io/part-of": assessment.title.lower().replace(' ', '-')
                }
            },
            "applications": {}
        }
        
        for app_config in app_configs:
            values["applications"][app_config.name] = {
                "enabled": True,
                "image": {
                    "repository": app_config.image.split(':')[0] if ':' in app_config.image else app_config.image,
                    "tag": app_config.image.split(':')[1] if ':' in app_config.image else "latest",
                    "pullPolicy": "IfNotPresent"
                },
                "replicaCount": app_config.replicas,
                "service": {
                    "type": app_config.service_type,
                    "port": 80,
                    "targetPort": app_config.port
                },
                "resources": {
                    "limits": {
                        "cpu": app_config.cpu_limit,
                        "memory": app_config.memory_limit
                    },
                    "requests": {
                        "cpu": app_config.cpu_request,
                        "memory": app_config.memory_request
                    }
                },
                "autoscaling": {
                    "enabled": app_config.autoscaling,
                    "minReplicas": app_config.min_replicas,
                    "maxReplicas": app_config.max_replicas,
                    "targetCPUUtilizationPercentage": app_config.target_cpu_percentage
                },
                "env": app_config.environment_variables,
                "volumes": app_config.volumes,
                "healthCheck": {
                    "path": app_config.health_check_path
                }
            }
        
        return yaml.dump(values, default_flow_style=False)
    
    def _generate_helm_templates(self, app_configs: List[ApplicationConfig], assessment: Assessment) -> Dict[str, str]:
        """Generate Helm template files."""
        
        templates = {}
        
        for app_config in app_configs:
            # Deployment template
            templates[f"{app_config.name}-deployment.yaml"] = self._generate_helm_deployment_template(app_config)
            
            # Service template
            templates[f"{app_config.name}-service.yaml"] = self._generate_helm_service_template(app_config)
            
            # HPA template (if autoscaling enabled)
            if app_config.autoscaling:
                templates[f"{app_config.name}-hpa.yaml"] = self._generate_helm_hpa_template(app_config)
        
        # Shared templates
        templates["configmap.yaml"] = self._generate_helm_configmap_template()
        templates["ingress.yaml"] = self._generate_helm_ingress_template()
        
        return templates
    
    def _generate_helm_deployment_template(self, app_config: ApplicationConfig) -> str:
        """Generate Helm deployment template."""
        
        template = f'''{{{{- if .Values.applications.{app_config.name}.enabled }}}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "{app_config.name}.fullname" . }}}}
  labels:
    {{{{- include "{app_config.name}.labels" . | nindent 4 }}}}
spec:
  replicas: {{{{ .Values.applications.{app_config.name}.replicaCount }}}}
  selector:
    matchLabels:
      {{{{- include "{app_config.name}.selectorLabels" . | nindent 6 }}}}
  template:
    metadata:
      labels:
        {{{{- include "{app_config.name}.selectorLabels" . | nindent 8 }}}}
    spec:
      containers:
        - name: {{{{ .Chart.Name }}}}
          image: "{{{{ .Values.applications.{app_config.name}.image.repository }}}}:{{{{ .Values.applications.{app_config.name}.image.tag | default .Chart.AppVersion }}}}"
          imagePullPolicy: {{{{ .Values.applications.{app_config.name}.image.pullPolicy }}}}
          ports:
            - name: http
              containerPort: {{{{ .Values.applications.{app_config.name}.service.targetPort }}}}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: {{{{ .Values.applications.{app_config.name}.healthCheck.path }}}}
              port: http
          readinessProbe:
            httpGet:
              path: {{{{ .Values.applications.{app_config.name}.healthCheck.path }}}}
              port: http
          resources:
            {{{{- toYaml .Values.applications.{app_config.name}.resources | nindent 12 }}}}
          {{{{- if .Values.applications.{app_config.name}.env }}}}
          env:
            {{{{- range $key, $value := .Values.applications.{app_config.name}.env }}}}
            - name: {{{{ $key }}}}
              value: "{{{{ $value }}}}"
            {{{{- end }}}}
          {{{{- end }}}}
{{{{- end }}}}'''
        
        return template
    
    def _generate_helm_service_template(self, app_config: ApplicationConfig) -> str:
        """Generate Helm service template."""
        
        template = f'''{{{{- if .Values.applications.{app_config.name}.enabled }}}}
apiVersion: v1
kind: Service
metadata:
  name: {{{{ include "{app_config.name}.fullname" . }}}}
  labels:
    {{{{- include "{app_config.name}.labels" . | nindent 4 }}}}
spec:
  type: {{{{ .Values.applications.{app_config.name}.service.type }}}}
  ports:
    - port: {{{{ .Values.applications.{app_config.name}.service.port }}}}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{{{- include "{app_config.name}.selectorLabels" . | nindent 4 }}}}
{{{{- end }}}}'''
        
        return template
    
    def _generate_helm_hpa_template(self, app_config: ApplicationConfig) -> str:
        """Generate Helm HPA template."""
        
        template = f'''{{{{- if and .Values.applications.{app_config.name}.enabled .Values.applications.{app_config.name}.autoscaling.enabled }}}}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{{{ include "{app_config.name}.fullname" . }}}}
  labels:
    {{{{- include "{app_config.name}.labels" . | nindent 4 }}}}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{{{ include "{app_config.name}.fullname" . }}}}
  minReplicas: {{{{ .Values.applications.{app_config.name}.autoscaling.minReplicas }}}}
  maxReplicas: {{{{ .Values.applications.{app_config.name}.autoscaling.maxReplicas }}}}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{{{ .Values.applications.{app_config.name}.autoscaling.targetCPUUtilizationPercentage }}}}
{{{{- end }}}}'''
        
        return template
    
    def _generate_helm_configmap_template(self) -> str:
        """Generate Helm ConfigMap template."""
        
        return '''apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "chart.fullname" . }}-config
  labels:
    {{- include "chart.labels" . | nindent 4 }}
data:
  {{- range $app, $config := .Values.applications }}
  {{- if $config.enabled }}
  {{- range $key, $value := $config.env }}
  {{ $app }}_{{ $key }}: "{{ $value }}"
  {{- end }}
  {{- end }}
  {{- end }}'''
    
    def _generate_helm_ingress_template(self) -> str:
        """Generate Helm Ingress template."""
        
        return '''{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ .service.name }}
                port:
                  number: {{ .service.port }}
          {{- end }}
    {{- end }}
{{- end }}'''
    
    def _generate_helpers_tpl(self) -> str:
        """Generate _helpers.tpl for Helm chart."""
        
        return '''{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "chart.labels" -}}
helm.sh/chart: {{ include "chart.chart" . }}
{{ include "chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}'''
    
    def generate_kustomization(self, assessment: Assessment, app_configs: List[ApplicationConfig]) -> Dict[str, str]:
        """
        Generate Kustomize configuration files.
        
        Args:
            assessment: Assessment with infrastructure requirements
            app_configs: List of application configurations
            
        Returns:
            Dictionary with filename -> content for Kustomize files
        """
        try:
            logger.info(f"Generating Kustomization files for assessment {assessment.id}")
            
            kustomize_files = {}
            
            # Base kustomization.yaml
            kustomize_files["base/kustomization.yaml"] = self._generate_base_kustomization(app_configs)
            
            # Environment overlays
            for env in ["dev", "staging", "prod"]:
                kustomize_files[f"overlays/{env}/kustomization.yaml"] = self._generate_env_kustomization(env, app_configs)
                kustomize_files[f"overlays/{env}/namespace.yaml"] = self._generate_env_namespace(env, assessment)
                
                # Environment-specific patches
                for app_config in app_configs:
                    patch_content = self._generate_env_patch(app_config, env)
                    kustomize_files[f"overlays/{env}/patches/{app_config.name}.yaml"] = patch_content
            
            logger.info(f"Generated Kustomization with {len(kustomize_files)} files")
            return kustomize_files
            
        except Exception as e:
            logger.error(f"Failed to generate Kustomization: {e}")
            raise
    
    def _generate_base_kustomization(self, app_configs: List[ApplicationConfig]) -> str:
        """Generate base kustomization.yaml."""
        
        resources = []
        for app_config in app_configs:
            resources.extend([
                f"{app_config.name}-deployment.yaml",
                f"{app_config.name}-service.yaml"
            ])
            if app_config.autoscaling:
                resources.append(f"{app_config.name}-hpa.yaml")
        
        kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "resources": resources,
            "commonLabels": {
                "app.kubernetes.io/managed-by": "infra-mind"
            }
        }
        
        return yaml.dump(kustomization, default_flow_style=False)
    
    def _generate_env_kustomization(self, env: str, app_configs: List[ApplicationConfig]) -> str:
        """Generate environment-specific kustomization.yaml."""
        
        patches = []
        for app_config in app_configs:
            patches.append({
                "path": f"patches/{app_config.name}.yaml",
                "target": {
                    "kind": "Deployment",
                    "name": app_config.name
                }
            })
        
        kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": f"infra-mind-{env}",
            "resources": [
                "../../base",
                "namespace.yaml"
            ],
            "patches": patches,
            "commonLabels": {
                "environment": env
            },
            "namePrefix": f"{env}-",
            "nameSuffix": f"-{env}"
        }
        
        return yaml.dump(kustomization, default_flow_style=False)
    
    def _generate_env_namespace(self, env: str, assessment: Assessment) -> str:
        """Generate environment-specific namespace."""
        
        namespace = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"infra-mind-{env}",
                "labels": {
                    "environment": env,
                    "assessment-id": assessment.id
                }
            }
        }
        
        return yaml.dump(namespace, default_flow_style=False)
    
    def _generate_env_patch(self, app_config: ApplicationConfig, env: str) -> str:
        """Generate environment-specific patches."""
        
        # Environment-specific configurations
        env_configs = {
            "dev": {"replicas": 1, "resources_multiplier": 0.5},
            "staging": {"replicas": 2, "resources_multiplier": 1.0},
            "prod": {"replicas": max(3, app_config.replicas), "resources_multiplier": 1.5}
        }
        
        config = env_configs.get(env, env_configs["dev"])
        
        patch = [{
            "op": "replace",
            "path": "/spec/replicas", 
            "value": config["replicas"]
        }]
        
        return yaml.dump(patch, default_flow_style=False)