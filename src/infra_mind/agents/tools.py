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
            "calculator": CalculationTool()
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