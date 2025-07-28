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
            # This is a mock implementation
            # In production, you would integrate with actual cloud APIs
            
            mock_data = await self._mock_api_call(provider, service, operation, **params)
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=mock_data,
                metadata={
                    "provider": provider,
                    "service": service,
                    "operation": operation
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _mock_api_call(self, provider: str, service: str, operation: str, **params) -> Dict[str, Any]:
        """Mock API call for testing."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        if provider == "aws" and service == "ec2" and operation == "describe_instances":
            return {
                "instances": [
                    {
                        "instance_id": "i-1234567890abcdef0",
                        "instance_type": "t3.medium",
                        "state": "running",
                        "pricing": {"hourly": 0.0416, "monthly": 30.37}
                    }
                ]
            }
        elif provider == "azure" and service == "compute" and operation == "list_vm_sizes":
            return {
                "vm_sizes": [
                    {
                        "name": "Standard_B2s",
                        "cores": 2,
                        "memory_gb": 4,
                        "pricing": {"hourly": 0.0496, "monthly": 36.21}
                    }
                ]
            }
        else:
            return {
                "message": f"Mock response for {provider} {service} {operation}",
                "parameters": params
            }


class CalculationTool(BaseTool):
    """Tool for performing calculations and cost estimations."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform calculations and cost estimations"
        )
    
    async def execute(self, operation: str, **params) -> ToolResult:
        """
        Execute calculation.
        
        Args:
            operation: Calculation operation
            **params: Calculation parameters
            
        Returns:
            Calculation result
        """
        try:
            if operation == "cost_estimate":
                result = await self._calculate_cost_estimate(**params)
            elif operation == "resource_sizing":
                result = await self._calculate_resource_sizing(**params)
            elif operation == "roi_analysis":
                result = await self._calculate_roi(**params)
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
    
    async def _calculate_cost_estimate(self, **params) -> Dict[str, Any]:
        """Calculate cost estimates."""
        # Mock cost calculation
        base_cost = params.get("base_cost", 100)
        users = params.get("users", 1000)
        scaling_factor = params.get("scaling_factor", 1.2)
        
        estimated_cost = base_cost * (users / 1000) * scaling_factor
        
        return {
            "monthly_cost": round(estimated_cost, 2),
            "annual_cost": round(estimated_cost * 12, 2),
            "cost_per_user": round(estimated_cost / users, 4),
            "assumptions": {
                "base_cost": base_cost,
                "users": users,
                "scaling_factor": scaling_factor
            }
        }
    
    async def _calculate_resource_sizing(self, **params) -> Dict[str, Any]:
        """Calculate resource sizing recommendations."""
        users = params.get("users", 1000)
        workload_type = params.get("workload_type", "web_application")
        
        # Simple sizing logic
        if workload_type == "web_application":
            cpu_cores = max(2, users // 500)
            memory_gb = max(4, users // 250)
            storage_gb = max(20, users // 50)
        else:
            cpu_cores = max(1, users // 1000)
            memory_gb = max(2, users // 500)
            storage_gb = max(10, users // 100)
        
        return {
            "recommended_resources": {
                "cpu_cores": cpu_cores,
                "memory_gb": memory_gb,
                "storage_gb": storage_gb
            },
            "scaling_recommendations": {
                "auto_scaling": users > 1000,
                "load_balancer": users > 500,
                "cdn": users > 100
            }
        }
    
    async def _calculate_roi(self, **params) -> Dict[str, Any]:
        """Calculate ROI analysis."""
        investment = params.get("investment", 10000)
        annual_savings = params.get("annual_savings", 5000)
        time_horizon = params.get("time_horizon", 3)
        
        total_savings = annual_savings * time_horizon
        roi_percentage = ((total_savings - investment) / investment) * 100
        payback_period = investment / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            "roi_percentage": round(roi_percentage, 2),
            "payback_period_years": round(payback_period, 2),
            "total_savings": total_savings,
            "net_benefit": total_savings - investment
        }


class ComplianceCheckerTool(BaseTool):
    """Tool for compliance checking and regulatory analysis."""
    
    def __init__(self):
        super().__init__(
            name="compliance_checker",
            description="Check compliance against regulatory frameworks"
        )
    
    async def execute(self, regulation: str, requirements: Dict[str, Any], 
                     operation: str = "check") -> ToolResult:
        """
        Execute compliance check.
        
        Args:
            regulation: Regulation to check against (GDPR, HIPAA, CCPA)
            requirements: Current requirements/configuration
            operation: Check operation type
            
        Returns:
            Compliance check result
        """
        try:
            if operation == "check":
                result = await self._check_compliance(regulation, requirements)
            elif operation == "gap_analysis":
                result = await self._perform_gap_analysis(regulation, requirements)
            elif operation == "recommendations":
                result = await self._get_compliance_recommendations(regulation, requirements)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"regulation": regulation, "operation": operation}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _check_compliance(self, regulation: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance against specific regulation."""
        compliance_score = 0.0
        findings = []
        
        if regulation == "GDPR":
            # Check GDPR requirements
            if requirements.get("encryption_at_rest"):
                compliance_score += 0.2
                findings.append("Data encryption at rest: COMPLIANT")
            else:
                findings.append("Data encryption at rest: NON-COMPLIANT")
            
            if requirements.get("data_retention_policy"):
                compliance_score += 0.2
                findings.append("Data retention policy: COMPLIANT")
            else:
                findings.append("Data retention policy: NON-COMPLIANT")
            
            if requirements.get("consent_management"):
                compliance_score += 0.2
                findings.append("Consent management: COMPLIANT")
            else:
                findings.append("Consent management: NON-COMPLIANT")
            
            if requirements.get("data_subject_rights"):
                compliance_score += 0.2
                findings.append("Data subject rights: COMPLIANT")
            else:
                findings.append("Data subject rights: NON-COMPLIANT")
            
            if requirements.get("breach_notification"):
                compliance_score += 0.2
                findings.append("Breach notification: COMPLIANT")
            else:
                findings.append("Breach notification: NON-COMPLIANT")
        
        elif regulation == "HIPAA":
            # Check HIPAA requirements
            if requirements.get("encryption_at_rest") and requirements.get("encryption_in_transit"):
                compliance_score += 0.3
                findings.append("Encryption safeguards: COMPLIANT")
            else:
                findings.append("Encryption safeguards: NON-COMPLIANT")
            
            if requirements.get("access_controls"):
                compliance_score += 0.3
                findings.append("Access controls: COMPLIANT")
            else:
                findings.append("Access controls: NON-COMPLIANT")
            
            if requirements.get("audit_logging"):
                compliance_score += 0.2
                findings.append("Audit controls: COMPLIANT")
            else:
                findings.append("Audit controls: NON-COMPLIANT")
            
            if requirements.get("business_associate_agreements"):
                compliance_score += 0.2
                findings.append("Business associate agreements: COMPLIANT")
            else:
                findings.append("Business associate agreements: NON-COMPLIANT")
        
        elif regulation == "CCPA":
            # Check CCPA requirements
            if requirements.get("data_inventory"):
                compliance_score += 0.3
                findings.append("Data inventory: COMPLIANT")
            else:
                findings.append("Data inventory: NON-COMPLIANT")
            
            if requirements.get("privacy_policy"):
                compliance_score += 0.2
                findings.append("Privacy policy: COMPLIANT")
            else:
                findings.append("Privacy policy: NON-COMPLIANT")
            
            if requirements.get("opt_out_mechanism"):
                compliance_score += 0.3
                findings.append("Opt-out mechanism: COMPLIANT")
            else:
                findings.append("Opt-out mechanism: NON-COMPLIANT")
            
            if requirements.get("data_deletion"):
                compliance_score += 0.2
                findings.append("Data deletion capability: COMPLIANT")
            else:
                findings.append("Data deletion capability: NON-COMPLIANT")
        
        return {
            "regulation": regulation,
            "compliance_score": min(compliance_score, 1.0),
            "compliance_level": self._get_compliance_level(compliance_score),
            "findings": findings,
            "overall_status": "COMPLIANT" if compliance_score >= 0.8 else "NON-COMPLIANT"
        }
    
    async def _perform_gap_analysis(self, regulation: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform gap analysis for regulation."""
        compliance_result = await self._check_compliance(regulation, requirements)
        
        gaps = []
        for finding in compliance_result["findings"]:
            if "NON-COMPLIANT" in finding:
                requirement = finding.split(":")[0]
                gaps.append({
                    "requirement": requirement,
                    "status": "missing",
                    "priority": "high" if "encryption" in requirement.lower() else "medium"
                })
        
        return {
            "regulation": regulation,
            "total_gaps": len(gaps),
            "gaps": gaps,
            "compliance_score": compliance_result["compliance_score"],
            "remediation_priority": "critical" if len(gaps) > 3 else "high" if len(gaps) > 1 else "medium"
        }
    
    async def _get_compliance_recommendations(self, regulation: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Get compliance recommendations."""
        gap_analysis = await self._perform_gap_analysis(regulation, requirements)
        
        recommendations = []
        for gap in gap_analysis["gaps"]:
            if "encryption" in gap["requirement"].lower():
                recommendations.append({
                    "requirement": gap["requirement"],
                    "recommendation": "Implement AES-256 encryption for data at rest and TLS 1.3 for data in transit",
                    "priority": "critical",
                    "effort": "medium"
                })
            elif "access control" in gap["requirement"].lower():
                recommendations.append({
                    "requirement": gap["requirement"],
                    "recommendation": "Implement role-based access control with multi-factor authentication",
                    "priority": "high",
                    "effort": "medium"
                })
            elif "audit" in gap["requirement"].lower():
                recommendations.append({
                    "requirement": gap["requirement"],
                    "recommendation": "Set up centralized logging and audit trail system",
                    "priority": "high",
                    "effort": "low"
                })
        
        return {
            "regulation": regulation,
            "recommendations": recommendations,
            "implementation_timeline": "3-6 months" if len(recommendations) > 3 else "1-3 months"
        }
    
    def _get_compliance_level(self, score: float) -> str:
        """Get compliance level description."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Fair"
        else:
            return "Poor"


class SecurityAnalyzerTool(BaseTool):
    """Tool for security analysis and assessment."""
    
    def __init__(self):
        super().__init__(
            name="security_analyzer",
            description="Analyze security posture and controls"
        )
    
    async def execute(self, security_config: Dict[str, Any], 
                     analysis_type: str = "comprehensive") -> ToolResult:
        """
        Execute security analysis.
        
        Args:
            security_config: Current security configuration
            analysis_type: Type of analysis to perform
            
        Returns:
            Security analysis result
        """
        try:
            if analysis_type == "comprehensive":
                result = await self._comprehensive_security_analysis(security_config)
            elif analysis_type == "vulnerability_scan":
                result = await self._vulnerability_scan(security_config)
            elif analysis_type == "risk_assessment":
                result = await self._risk_assessment(security_config)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"analysis_type": analysis_type}
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _comprehensive_security_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security analysis."""
        analysis = {
            "overall_score": 0.0,
            "categories": {},
            "recommendations": [],
            "critical_issues": []
        }
        
        # Analyze encryption
        encryption_score = self._analyze_encryption(config)
        analysis["categories"]["encryption"] = encryption_score
        
        # Analyze access controls
        access_score = self._analyze_access_controls(config)
        analysis["categories"]["access_control"] = access_score
        
        # Analyze network security
        network_score = self._analyze_network_security(config)
        analysis["categories"]["network_security"] = network_score
        
        # Analyze monitoring
        monitoring_score = self._analyze_monitoring(config)
        analysis["categories"]["monitoring"] = monitoring_score
        
        # Calculate overall score
        scores = [score["score"] for score in analysis["categories"].values()]
        analysis["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        # Generate recommendations
        for category, details in analysis["categories"].items():
            if details["score"] < 0.7:
                analysis["recommendations"].extend(details.get("recommendations", []))
            if details["score"] < 0.4:
                analysis["critical_issues"].extend(details.get("issues", []))
        
        return analysis
    
    def _analyze_encryption(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze encryption configuration."""
        score = 0.0
        issues = []
        recommendations = []
        
        if config.get("encryption_at_rest"):
            score += 0.4
        else:
            issues.append("Missing encryption at rest")
            recommendations.append("Implement AES-256 encryption for data at rest")
        
        if config.get("encryption_in_transit"):
            score += 0.4
        else:
            issues.append("Missing encryption in transit")
            recommendations.append("Configure TLS 1.3 for all communications")
        
        if config.get("key_management"):
            score += 0.2
        else:
            issues.append("Inadequate key management")
            recommendations.append("Implement proper key management with HSM")
        
        return {
            "score": score,
            "status": "good" if score >= 0.7 else "needs_improvement",
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_access_controls(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze access control configuration."""
        score = 0.0
        issues = []
        recommendations = []
        
        if config.get("multi_factor_auth"):
            score += 0.3
        else:
            issues.append("Missing multi-factor authentication")
            recommendations.append("Implement MFA for all user accounts")
        
        if config.get("role_based_access"):
            score += 0.4
        else:
            issues.append("Missing role-based access control")
            recommendations.append("Implement RBAC with principle of least privilege")
        
        if config.get("access_monitoring"):
            score += 0.3
        else:
            issues.append("Insufficient access monitoring")
            recommendations.append("Set up access logging and monitoring")
        
        return {
            "score": score,
            "status": "good" if score >= 0.7 else "needs_improvement",
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_network_security(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network security configuration."""
        score = 0.5  # Baseline score
        issues = []
        recommendations = []
        
        if config.get("firewall_configured"):
            score += 0.2
        else:
            issues.append("Firewall not properly configured")
            recommendations.append("Configure network firewall with strict rules")
        
        if config.get("vpc_isolation"):
            score += 0.2
        else:
            issues.append("Missing network isolation")
            recommendations.append("Implement VPC with proper network segmentation")
        
        if config.get("intrusion_detection"):
            score += 0.1
        else:
            recommendations.append("Consider implementing intrusion detection system")
        
        return {
            "score": min(score, 1.0),
            "status": "good" if score >= 0.7 else "needs_improvement",
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monitoring and logging configuration."""
        score = 0.0
        issues = []
        recommendations = []
        
        if config.get("centralized_logging"):
            score += 0.4
        else:
            issues.append("Missing centralized logging")
            recommendations.append("Implement centralized logging system")
        
        if config.get("security_monitoring"):
            score += 0.3
        else:
            issues.append("Insufficient security monitoring")
            recommendations.append("Set up security monitoring and alerting")
        
        if config.get("audit_trails"):
            score += 0.3
        else:
            issues.append("Missing audit trails")
            recommendations.append("Implement comprehensive audit logging")
        
        return {
            "score": score,
            "status": "good" if score >= 0.7 else "needs_improvement",
            "issues": issues,
            "recommendations": recommendations
        }
    
    async def _vulnerability_scan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform vulnerability scan simulation."""
        # This would integrate with actual vulnerability scanners in production
        vulnerabilities = []
        
        if not config.get("encryption_at_rest"):
            vulnerabilities.append({
                "severity": "high",
                "type": "data_exposure",
                "description": "Unencrypted data at rest",
                "remediation": "Enable encryption for all data stores"
            })
        
        if not config.get("multi_factor_auth"):
            vulnerabilities.append({
                "severity": "medium",
                "type": "weak_authentication",
                "description": "Single-factor authentication",
                "remediation": "Implement multi-factor authentication"
            })
        
        return {
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "risk_score": len([v for v in vulnerabilities if v["severity"] == "high"]) * 3 + 
                         len([v for v in vulnerabilities if v["severity"] == "medium"]) * 2
        }
    
    async def _risk_assessment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security risk assessment."""
        risks = []
        
        # Data breach risk
        if not config.get("encryption_at_rest") or not config.get("access_controls"):
            risks.append({
                "risk_type": "data_breach",
                "probability": "high",
                "impact": "critical",
                "description": "High risk of data breach due to insufficient protection",
                "mitigation": "Implement encryption and strong access controls"
            })
        
        # Insider threat risk
        if not config.get("access_monitoring") or not config.get("role_based_access"):
            risks.append({
                "risk_type": "insider_threat",
                "probability": "medium",
                "impact": "high",
                "description": "Risk of insider threats due to inadequate access controls",
                "mitigation": "Implement RBAC and access monitoring"
            })
        
        return {
            "assessment_date": datetime.now(timezone.utc).isoformat(),
            "total_risks": len(risks),
            "risks": risks,
            "overall_risk_level": "high" if any(r["impact"] == "critical" for r in risks) else "medium"
        }


class AgentToolkit:
    """
    Toolkit that provides tools to agents.
    
    Learning Note: The toolkit pattern allows agents to access
    various tools in a consistent way.
    """
    
    def __init__(self, enabled_tools: List[str]):
        """
        Initialize the toolkit.
        
        Args:
            enabled_tools: List of enabled tool names
        """
        self.enabled_tools = set(enabled_tools)
        self.tools: Dict[str, BaseTool] = {}
        self.api_call_count = 0
        
        # Initialize available tools
        self._initialize_tools()
    
    def _initialize_tools(self) -> None:
        """Initialize available tools."""
        available_tools = {
            "data_processor": DataProcessingTool(),
            "cloud_api": CloudAPITool(),
            "calculator": CalculationTool(),
            "compliance_checker": ComplianceCheckerTool(),
            "security_analyzer": SecurityAnalyzerTool(),
            "web_scraper": WebScrapingTool(),
            "search_api": SearchAPITool(),
            "content_extractor": ContentExtractorTool()
        }
        
        # Only enable requested tools
        for tool_name, tool in available_tools.items():
            if not self.enabled_tools or tool_name in self.enabled_tools:
                self.tools[tool_name] = tool
                logger.debug(f"Enabled tool: {tool_name}")
    
    async def initialize(self, assessment: Assessment, context: Dict[str, Any]) -> None:
        """
        Initialize toolkit for a specific assessment.
        
        Args:
            assessment: Assessment being processed
            context: Additional context
        """
        # Store assessment and context for tools to use
        self.current_assessment = assessment
        self.context = context
        self.api_call_count = 0
        
        logger.info(f"Initialized toolkit with {len(self.tools)} tools")
    
    async def use_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Use a specific tool.
        
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
        
        tool = self.tools[tool_name]
        
        # Track API calls
        if tool_name == "cloud_api":
            self.api_call_count += 1
        
        result = await tool._execute_with_tracking(**kwargs)
        
        logger.debug(f"Used tool {tool_name}: {result.status.value}")
        return result
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.get_info() for tool in self.tools.values()]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if tool_name in self.tools:
            return self.tools[tool_name].get_info()
        return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get toolkit usage statistics."""
        return {
            "enabled_tools": list(self.tools.keys()),
            "api_calls_made": self.api_call_count,
            "tool_usage": {
                name: tool.usage_count 
                for name, tool in self.tools.items()
            }
        }

class WebScrapingTool(BaseTool):
    """Tool for web scraping and content extraction."""
    
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Scrape web content and extract relevant information"
        )
    
    async def execute(self, url: str, content_type: str = "generic", 
                     extraction_rules: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Execute web scraping.
        
        Args:
            url: URL to scrape
            content_type: Type of content to extract (pricing, trends, etc.)
            extraction_rules: Custom extraction rules
            
        Returns:
            Scraping result
        """
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            import hashlib
            
            # Configure request
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                "User-Agent": "InfraMind-WebResearch/1.0 (Educational Purpose)"
            }
            
            # Make request
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse content
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract data based on content type
                        extracted_data = await self._extract_content(soup, content_type, extraction_rules)
                        
                        return ToolResult(
                            tool_name=self.name,
                            status=ToolStatus.SUCCESS,
                            data={
                                "url": url,
                                "content_type": content_type,
                                "extracted_data": extracted_data,
                                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                                "status_code": response.status,
                                "content_length": len(content)
                            },
                            metadata={
                                "scraping_timestamp": datetime.now(timezone.utc).isoformat(),
                                "response_headers": dict(response.headers)
                            }
                        )
                    else:
                        return ToolResult(
                            tool_name=self.name,
                            status=ToolStatus.FAILURE,
                            error=f"HTTP {response.status} for {url}"
                        )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _extract_content(self, soup: "BeautifulSoup", content_type: str, 
                             extraction_rules: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract content based on type and rules."""
        extracted = {
            "title": "",
            "headings": [],
            "paragraphs": [],
            "links": [],
            "metadata": {}
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            extracted["title"] = title_tag.get_text().strip()
        
        # Extract headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        extracted["headings"] = [h.get_text().strip() for h in headings[:20]]
        
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        extracted["paragraphs"] = [p.get_text().strip() for p in paragraphs[:10] if len(p.get_text().strip()) > 20]
        
        # Extract links
        links = soup.find_all('a', href=True)
        for link in links[:10]:
            extracted["links"].append({
                "url": link['href'],
                "text": link.get_text().strip()[:100]
            })
        
        # Content-specific extraction
        if content_type == "pricing":
            extracted.update(await self._extract_pricing_content(soup))
        elif content_type == "trends":
            extracted.update(await self._extract_trend_content(soup))
        elif content_type == "regulatory":
            extracted.update(await self._extract_regulatory_content(soup))
        
        # Apply custom extraction rules if provided
        if extraction_rules:
            extracted.update(await self._apply_extraction_rules(soup, extraction_rules))
        
        return extracted
    
    async def _extract_pricing_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract pricing-specific content."""
        import re
        
        pricing_content = {
            "prices_found": [],
            "services_mentioned": [],
            "pricing_tables": []
        }
        
        text_content = soup.get_text()
        
        # Extract prices using regex
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)\s*(?:per|/)\s*(hour|month|year|GB|TB)',
            r'(\d+(?:\.\d{2})?)\s*cents?\s*(?:per|/)\s*(hour|month|year|GB|TB)',
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches[:10]:
                if isinstance(match, tuple):
                    pricing_content["prices_found"].append({
                        "amount": match[0],
                        "unit": match[1] if len(match) > 1 else "unknown"
                    })
                else:
                    pricing_content["prices_found"].append({
                        "amount": match,
                        "unit": "unknown"
                    })
        
        # Extract service mentions
        service_keywords = ["EC2", "RDS", "S3", "Lambda", "Azure VM", "Compute", "Storage", "Database"]
        for keyword in service_keywords:
            if keyword.lower() in text_content.lower():
                pricing_content["services_mentioned"].append(keyword)
        
        # Look for pricing tables
        tables = soup.find_all('table')
        for table in tables[:3]:
            rows = table.find_all('tr')
            if len(rows) > 1:  # Has header and data
                table_data = []
                for row in rows[:5]:  # Limit rows
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text().strip() for cell in cells]
                    if row_data:
                        table_data.append(row_data)
                
                if table_data:
                    pricing_content["pricing_tables"].append(table_data)
        
        return pricing_content
    
    async def _extract_trend_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract trend-specific content."""
        trend_content = {
            "trend_keywords": [],
            "sentiment_indicators": [],
            "statistics": []
        }
        
        text_content = soup.get_text().lower()
        
        # Look for trend keywords
        trend_keywords = [
            "artificial intelligence", "machine learning", "cloud migration",
            "serverless", "containers", "kubernetes", "microservices",
            "edge computing", "hybrid cloud", "multi-cloud", "devops"
        ]
        
        for keyword in trend_keywords:
            if keyword in text_content:
                trend_content["trend_keywords"].append(keyword)
        
        # Look for sentiment indicators
        sentiment_words = ["increasing", "growing", "declining", "emerging", "trending", "popular", "adoption"]
        for word in sentiment_words:
            if word in text_content:
                trend_content["sentiment_indicators"].append(word)
        
        # Extract statistics (numbers with %)
        import re
        stats = re.findall(r'(\d+(?:\.\d+)?)\s*%', text_content)
        trend_content["statistics"] = [f"{stat}%" for stat in stats[:10]]
        
        return trend_content
    
    async def _extract_regulatory_content(self, soup: "BeautifulSoup") -> Dict[str, Any]:
        """Extract regulatory-specific content."""
        regulatory_content = {
            "regulations_mentioned": [],
            "compliance_terms": [],
            "update_indicators": []
        }
        
        text_content = soup.get_text()
        
        # Look for regulation names
        regulations = ["GDPR", "HIPAA", "CCPA", "SOC 2", "ISO 27001", "PCI DSS", "NIST"]
        for regulation in regulations:
            if regulation in text_content:
                regulatory_content["regulations_mentioned"].append(regulation)
        
        # Look for compliance terms
        compliance_terms = ["compliance", "audit", "certification", "privacy", "security", "data protection"]
        for term in compliance_terms:
            if term.lower() in text_content.lower():
                regulatory_content["compliance_terms"].append(term)
        
        # Look for update indicators
        update_words = ["updated", "new requirement", "effective date", "amendment", "revision"]
        for word in update_words:
            if word.lower() in text_content.lower():
                regulatory_content["update_indicators"].append(word)
        
        return regulatory_content
    
    async def _apply_extraction_rules(self, soup: "BeautifulSoup", rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom extraction rules."""
        custom_data = {}
        
        # CSS selector rules
        if "css_selectors" in rules:
            for key, selector in rules["css_selectors"].items():
                elements = soup.select(selector)
                custom_data[key] = [elem.get_text().strip() for elem in elements[:10]]
        
        # Regex rules
        if "regex_patterns" in rules:
            text_content = soup.get_text()
            for key, pattern in rules["regex_patterns"].items():
                import re
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                custom_data[key] = matches[:10]
        
        return custom_data


class SearchAPITool(BaseTool):
    """Tool for using search APIs to find relevant content."""
    
    def __init__(self):
        super().__init__(
            name="search_api",
            description="Search the web using search APIs"
        )
    
    async def execute(self, query: str, search_type: str = "web", 
                     max_results: int = 10) -> ToolResult:
        """
        Execute search API call.
        
        Args:
            query: Search query
            search_type: Type of search (web, news, academic)
            max_results: Maximum number of results
            
        Returns:
            Search results
        """
        try:
            # This is a mock implementation
            # In production, you would integrate with Google Custom Search, Bing Search, etc.
            
            mock_results = await self._mock_search(query, search_type, max_results)
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data={
                    "query": query,
                    "search_type": search_type,
                    "results": mock_results,
                    "total_results": len(mock_results)
                },
                metadata={
                    "search_timestamp": datetime.now(timezone.utc).isoformat(),
                    "api_used": "mock_search_api"
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _mock_search(self, query: str, search_type: str, max_results: int) -> List[Dict[str, Any]]:
        """Mock search implementation."""
        # Simulate API delay
        await asyncio.sleep(0.2)
        
        # Generate mock results based on query
        results = []
        
        if "aws" in query.lower():
            results.extend([
                {
                    "title": "AWS Pricing - Amazon Web Services",
                    "url": "https://aws.amazon.com/pricing/",
                    "snippet": "AWS pricing information for all services including EC2, S3, RDS and more.",
                    "relevance_score": 0.95
                },
                {
                    "title": "AWS Well-Architected Framework",
                    "url": "https://docs.aws.amazon.com/wellarchitected/",
                    "snippet": "Best practices and architectural guidance for AWS workloads.",
                    "relevance_score": 0.88
                }
            ])
        
        if "azure" in query.lower():
            results.extend([
                {
                    "title": "Azure Pricing Calculator",
                    "url": "https://azure.microsoft.com/en-us/pricing/calculator/",
                    "snippet": "Estimate costs for Azure services and create custom pricing scenarios.",
                    "relevance_score": 0.92
                },
                {
                    "title": "Azure Architecture Center",
                    "url": "https://docs.microsoft.com/en-us/azure/architecture/",
                    "snippet": "Architecture guidance and best practices for Azure solutions.",
                    "relevance_score": 0.85
                }
            ])
        
        if "cloud" in query.lower() and "trends" in query.lower():
            results.extend([
                {
                    "title": "Cloud Computing Trends 2024",
                    "url": "https://www.gartner.com/en/information-technology/insights/cloud-strategy",
                    "snippet": "Latest trends in cloud computing including AI, edge computing, and hybrid cloud.",
                    "relevance_score": 0.90
                },
                {
                    "title": "State of Cloud Report",
                    "url": "https://www.flexera.com/about-us/press-center/flexera-releases-2024-state-of-the-cloud-report",
                    "snippet": "Annual report on cloud adoption, spending, and optimization trends.",
                    "relevance_score": 0.87
                }
            ])
        
        # Default results if no specific matches
        if not results:
            results = [
                {
                    "title": f"Search results for: {query}",
                    "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                    "snippet": f"Mock search result for query: {query}",
                    "relevance_score": 0.70
                }
            ]
        
        # Limit results and sort by relevance
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
        return results[:max_results]


class ContentExtractorTool(BaseTool):
    """Tool for extracting and processing content from various sources."""
    
    def __init__(self):
        super().__init__(
            name="content_extractor",
            description="Extract and process content from text, HTML, or documents"
        )
    
    async def execute(self, content: str, content_format: str = "html", 
                     extraction_type: str = "generic") -> ToolResult:
        """
        Execute content extraction.
        
        Args:
            content: Content to extract from
            content_format: Format of content (html, text, json)
            extraction_type: Type of extraction (generic, structured, semantic)
            
        Returns:
            Extraction result
        """
        try:
            if content_format == "html":
                result = await self._extract_from_html(content, extraction_type)
            elif content_format == "text":
                result = await self._extract_from_text(content, extraction_type)
            elif content_format == "json":
                result = await self._extract_from_json(content, extraction_type)
            else:
                raise ValueError(f"Unsupported content format: {content_format}")
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={
                    "content_format": content_format,
                    "extraction_type": extraction_type,
                    "content_length": len(content)
                }
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _extract_from_html(self, html_content: str, extraction_type: str) -> Dict[str, Any]:
        """Extract content from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        extracted = {
            "title": "",
            "headings": [],
            "paragraphs": [],
            "lists": [],
            "tables": [],
            "links": [],
            "images": []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            extracted["title"] = title_tag.get_text().strip()
        
        # Extract headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        extracted["headings"] = [
            {"level": h.name, "text": h.get_text().strip()}
            for h in headings
        ]
        
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        extracted["paragraphs"] = [
            p.get_text().strip() for p in paragraphs 
            if len(p.get_text().strip()) > 10
        ]
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            extracted["lists"].append({
                "type": list_elem.name,
                "items": [item.get_text().strip() for item in items]
            })
        
        # Extract tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                if row_data:
                    table_data.append(row_data)
            
            if table_data:
                extracted["tables"].append(table_data)
        
        # Extract links
        links = soup.find_all('a', href=True)
        extracted["links"] = [
            {"url": link['href'], "text": link.get_text().strip()}
            for link in links[:20]
        ]
        
        # Extract images
        images = soup.find_all('img', src=True)
        extracted["images"] = [
            {"src": img['src'], "alt": img.get('alt', '')}
            for img in images[:10]
        ]
        
        return extracted
    
    async def _extract_from_text(self, text_content: str, extraction_type: str) -> Dict[str, Any]:
        """Extract content from plain text."""
        import re
        
        extracted = {
            "sentences": [],
            "keywords": [],
            "entities": [],
            "statistics": [],
            "urls": [],
            "emails": []
        }
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text_content)
        extracted["sentences"] = [
            s.strip() for s in sentences 
            if len(s.strip()) > 10
        ][:20]
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text_content)
        extracted["urls"] = urls[:10]
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        extracted["emails"] = emails[:10]
        
        # Extract statistics (numbers with units)
        stats_pattern = r'(\d+(?:\.\d+)?)\s*(%|GB|TB|MB|hours?|days?|years?|months?)'
        stats = re.findall(stats_pattern, text_content, re.IGNORECASE)
        extracted["statistics"] = [f"{stat[0]} {stat[1]}" for stat in stats[:10]]
        
        # Simple keyword extraction (most frequent words)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        extracted["keywords"] = [word for word, freq in sorted_words[:20] if freq > 1]
        
        return extracted
    
    async def _extract_from_json(self, json_content: str, extraction_type: str) -> Dict[str, Any]:
        """Extract content from JSON."""
        import json
        
        try:
            data = json.loads(json_content)
            
            extracted = {
                "structure": self._analyze_json_structure(data),
                "keys": self._extract_json_keys(data),
                "values": self._extract_json_values(data),
                "arrays": self._extract_json_arrays(data)
            }
            
            return extracted
            
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
    
    def _analyze_json_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Analyze JSON structure."""
        if depth > 3:  # Limit recursion depth
            return {"type": "deep_structure"}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys())[:10],
                "nested": {
                    key: self._analyze_json_structure(value, depth + 1)
                    for key, value in list(data.items())[:5]
                }
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "sample_items": [
                    self._analyze_json_structure(item, depth + 1)
                    for item in data[:3]
                ]
            }
        else:
            return {
                "type": type(data).__name__,
                "sample_value": str(data)[:100]
            }
    
    def _extract_json_keys(self, data: Any, prefix: str = "") -> List[str]:
        """Extract all keys from JSON structure."""
        keys = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_json_keys(value, full_key))
        elif isinstance(data, list) and data:
            # Check first item for structure
            if isinstance(data[0], dict):
                keys.extend(self._extract_json_keys(data[0], f"{prefix}[0]"))
        
        return keys[:50]  # Limit number of keys
    
    def _extract_json_values(self, data: Any) -> List[str]:
        """Extract sample values from JSON."""
        values = []
        
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, (str, int, float, bool)):
                    values.append(str(value))
                elif isinstance(value, (dict, list)):
                    values.extend(self._extract_json_values(value))
        elif isinstance(data, list):
            for item in data[:5]:  # Sample first 5 items
                if isinstance(item, (str, int, float, bool)):
                    values.append(str(item))
                elif isinstance(item, (dict, list)):
                    values.extend(self._extract_json_values(item))
        
        return values[:20]  # Limit number of values
    
    def _extract_json_arrays(self, data: Any, path: str = "") -> List[Dict[str, Any]]:
        """Extract information about arrays in JSON."""
        arrays = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, list):
                    arrays.append({
                        "path": current_path,
                        "length": len(value),
                        "item_types": list(set(type(item).__name__ for item in value[:10]))
                    })
                elif isinstance(value, dict):
                    arrays.extend(self._extract_json_arrays(value, current_path))
        
        return arrays[:10]  # Limit number of arrays