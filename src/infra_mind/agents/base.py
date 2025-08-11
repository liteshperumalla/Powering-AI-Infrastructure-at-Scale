"""
Base agent framework for Infra Mind.

Defines the base agent class and agent management utilities.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Type, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid

from ..models.assessment import Assessment
from ..models.recommendation import Recommendation
from ..models.metrics import AgentMetrics
from ..core.audit import log_data_access_event, AuditEventType
from ..core.metrics_collector import get_metrics_collector
from ..core.error_handling import error_handler, ErrorContext
from ..core.advanced_logging import get_agent_logger, log_context
from .memory import AgentMemory
from .tools import AgentToolkit, ToolResult

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentRole(str, Enum):
    """Agent roles in the system."""
    CTO = "cto"
    CLOUD_ENGINEER = "cloud_engineer"
    RESEARCH = "research"
    REPORT_GENERATOR = "report_generator"
    MLOPS = "mlops"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"
    AI_CONSULTANT = "ai_consultant"
    WEB_RESEARCH = "web_research"
    SIMULATION = "simulation"
    CHATBOT = "chatbot"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    role: AgentRole
    version: str = "1.0"
    max_iterations: int = 10
    timeout_seconds: int = 300
    temperature: float = 0.7
    max_tokens: int = 2000
    model_name: str = "gpt-4"
    tools_enabled: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    metrics_enabled: bool = True
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_name: str
    status: AgentStatus
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(ABC):
    """
    Base class for all AI agents.
    
    Learning Note: This abstract base class defines the common interface
    and functionality that all agents must implement.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory() if config.memory_enabled else None
        self.toolkit = AgentToolkit(config.tools_enabled)
        self.metrics: Optional[AgentMetrics] = None
        self.metrics_collector = get_metrics_collector()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Agent state
        self.current_assessment: Optional[Assessment] = None
        self.context: Dict[str, Any] = {}
        self.iteration_count = 0
        
        logger.info(f"Initialized agent {self.config.name} ({self.config.role.value})")
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name
    
    @property
    def role(self) -> AgentRole:
        """Get agent role."""
        return self.config.role
    
    @property
    def is_running(self) -> bool:
        """Check if agent is currently running."""
        return self.status == AgentStatus.RUNNING
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    async def initialize(self, assessment: Assessment, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize agent for execution.
        
        Args:
            assessment: Assessment to work on
            context: Additional context data
        """
        self.status = AgentStatus.INITIALIZING
        self.current_assessment = assessment
        self.context = context or {}
        self.iteration_count = 0
        
        # Initialize metrics if enabled
        if self.config.metrics_enabled:
            self.metrics = await AgentMetrics.create_for_agent(
                agent_name=self.config.name,
                agent_version=self.config.version,
                started_at=datetime.now(timezone.utc),
                assessment_id=str(assessment.id)
            )
        
        # Load memory if enabled
        if self.memory:
            await self.memory.load_context(str(assessment.id))
        
        # Initialize tools
        await self.toolkit.initialize(assessment, context)
        
        logger.info(f"Agent {self.name} initialized for assessment {assessment.id}")
    
    async def execute(self, assessment: Assessment, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute the agent's main logic with comprehensive error handling.
        
        Args:
            assessment: Assessment to process
            context: Additional context data
            
        Returns:
            AgentResult with execution results
        """
        workflow_id = context.get("workflow_id") if context else None
        
        # Set up logging context
        with log_context(
            agent_name=self.name,
            workflow_id=workflow_id
        ):
            # Use comprehensive error handling
            async with error_handler.handle_errors(
                operation="agent_execution",
                component="agent",
                agent_name=self.name,
                workflow_id=workflow_id,
                assessment_id=str(assessment.id) if assessment else None
            ) as handle_error:
                
                try:
                    # Initialize
                    await self.initialize(assessment, context)
                    
                    # Start execution
                    self.status = AgentStatus.RUNNING
                    self.start_time = datetime.now(timezone.utc)
                    
                    logger.info(f"Starting execution of agent {self.name}")
                    
                    # Execute main logic with error handling
                    result = await handle_error(self._execute_main_logic_with_recovery)
                    
                    # Mark as completed
                    self.status = AgentStatus.COMPLETED
                    self.end_time = datetime.now(timezone.utc)
                    
                    # Update metrics
                    if self.metrics:
                        self.metrics.update_performance(
                            execution_time=self.execution_time or 0,
                            api_calls=self.toolkit.api_call_count
                        )
                        await self.metrics.save()
                    
                    # Record performance in metrics collector
                    await self.metrics_collector.record_agent_performance(
                        agent_name=self.name,
                        execution_time=self.execution_time or 0,
                        success=True,
                        confidence_score=getattr(self.metrics, 'confidence_score', None),
                        recommendations_count=len(result.get("recommendations", [])),
                        assessment_id=str(assessment.id)
                    )
                    
                    # Save memory
                    if self.memory:
                        await self.memory.save_context(str(assessment.id))
                    
                    logger.info(f"Agent {self.name} completed successfully in {self.execution_time:.2f}s")
                    
                    return AgentResult(
                        agent_name=self.name,
                        status=self.status,
                        recommendations=result.get("recommendations", []),
                        data=result.get("data", {}),
                        metrics=self.metrics.dict() if self.metrics else None,
                        execution_time=self.execution_time
                    )
                    
                except Exception as e:
                    # Handle errors with comprehensive error handling
                    self.status = AgentStatus.FAILED
                    self.end_time = datetime.now(timezone.utc)
                    
                    # Try to recover from the error
                    recovery_result = await error_handler.handle_agent_error(
                        agent_name=self.name,
                        operation="agent_execution",
                        exception=e,
                        workflow_id=workflow_id,
                        fallback_data=self._get_fallback_data()
                    )
                    
                    # Update metrics with error
                    if self.metrics:
                        self.metrics.record_error(error_count=1)
                        await self.metrics.save()
                    
                    # Record failure in metrics collector
                    await self.metrics_collector.record_agent_performance(
                        agent_name=self.name,
                        execution_time=self.execution_time or 0,
                        success=False,
                        assessment_id=str(assessment.id) if assessment else None
                    )
                    
                    # If recovery was successful, return partial results
                    if recovery_result.success:
                        logger.warning(f"Agent {self.name} recovered from error using {recovery_result.strategy_used.value}")
                        
                        return AgentResult(
                            agent_name=self.name,
                            status=AgentStatus.COMPLETED,
                            recommendations=recovery_result.data.get("recommendations", []) if recovery_result.data else [],
                            data=recovery_result.data or {},
                            execution_time=self.execution_time,
                            error=f"Recovered from error: {str(e)}"
                        )
                    else:
                        # Recovery failed, return error result
                        error_msg = f"Agent {self.name} failed: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        
                        return AgentResult(
                            agent_name=self.name,
                            status=self.status,
                            error=error_msg,
                            execution_time=self.execution_time
                        )
    
    async def _execute_main_logic_with_recovery(self) -> Dict[str, Any]:
        """
        Execute main logic with built-in recovery mechanisms.
        
        Returns:
            Dictionary with execution results
        """
        try:
            return await self._execute_main_logic()
        except Exception as e:
            # Log the error and attempt graceful degradation
            logger.warning(f"Agent {self.name} main logic failed, attempting graceful degradation: {str(e)}")
            
            # Try to provide partial results
            partial_results = await self._get_partial_results()
            if partial_results:
                return {
                    "recommendations": partial_results.get("recommendations", []),
                    "data": partial_results.get("data", {}),
                    "degraded_mode": True,
                    "error": str(e)
                }
            
            # Re-raise if no partial results available
            raise
    
    def _get_fallback_data(self) -> Optional[Dict[str, Any]]:
        """
        Get fallback data for error recovery.
        
        Returns:
            Fallback data or None
        """
        return {
            "recommendations": [],
            "data": {},
            "fallback_mode": True,
            "message": f"Agent {self.name} is temporarily unavailable"
        }
    
    async def _get_partial_results(self) -> Optional[Dict[str, Any]]:
        """
        Get partial results when main logic fails.
        
        Returns:
            Partial results or None
        """
        # Default implementation returns None
        # Subclasses can override to provide meaningful partial results
        return None
    
    @abstractmethod
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        This method must be implemented by each specific agent.
        
        Returns:
            Dictionary with execution results
        """
        pass
    
    async def stop(self) -> None:
        """Stop agent execution."""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.STOPPED
            self.end_time = datetime.now(timezone.utc)
            logger.info(f"Agent {self.name} stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the agent.
        
        Returns:
            Health status information
        """
        return {
            "agent_name": self.name,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "role": self.role.value,
            "version": self.config.version,
            "memory_enabled": self.config.memory_enabled,
            "tools_count": len(self.config.tools_enabled),
            "current_assessment": str(self.current_assessment.id) if self.current_assessment else None,
            "iteration_count": self.iteration_count,
            "execution_time": self.execution_time
        }
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability descriptions
        """
        capabilities = [
            f"Role: {self.role.value}",
            f"Model: {self.config.model_name}",
            f"Temperature: {self.config.temperature}",
            f"Max iterations: {self.config.max_iterations}",
            f"Timeout: {self.config.timeout_seconds}s"
        ]
        
        if self.config.memory_enabled:
            capabilities.append("Memory enabled")
        
        if self.config.tools_enabled:
            capabilities.append(f"Tools: {', '.join(self.config.tools_enabled)}")
        
        return capabilities
    
    async def _call_llm(self, prompt: str, **kwargs) -> str:
        """
        Call the language model using the real LLM manager.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            LLM response content
        """
        from ..llm.manager import LLMManager
        from ..llm.interface import LLMRequest
        from ..core.config import get_settings
        
        # Get or create LLM manager instance with explicit configuration
        if not hasattr(self, '_llm_manager'):
            # Ensure we have fresh settings
            settings = get_settings()
            config = {
                "preferred_provider": "openai"  # Force OpenAI as requested
            }
            self._llm_manager = LLMManager(config=config)
        
        # Create LLM request
        request = LLMRequest(
            prompt=prompt,
            model=kwargs.get('model', self.config.model_name),
            temperature=kwargs.get('temperature', self.config.temperature),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            system_prompt=kwargs.get('system_prompt'),
            context=kwargs.get('context', {}),
            agent_name=self.name
        )
        
        try:
            # Generate response using LLM manager
            response = await self._llm_manager.generate_response(
                request, 
                validate_response=True,
                agent_name=self.name
            )
            
            # Log LLM usage for metrics
            if self.metrics:
                self.metrics.record_llm_usage(
                    tokens_used=response.token_usage.total_tokens,
                    cost=response.token_usage.estimated_cost,
                    model=response.model,
                    provider=response.provider.value
                )
            
            return response.content
            
        except Exception as e:
            logger.error(f"LLM call failed for agent {self.name}: {str(e)}")
            # Return a fallback response to prevent complete failure
            return f"I apologize, but I'm currently unable to process your request due to a technical issue. Please try again later."
    
    async def _use_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Use a tool from the toolkit.
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        return await self.toolkit.use_tool(tool_name, **kwargs)


class AgentRegistry:
    """
    Registry for managing agent types and instances.
    
    Learning Note: The registry pattern allows for dynamic agent
    discovery and instantiation.
    """
    
    def __init__(self):
        self._agent_types: Dict[str, Type[BaseAgent]] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
    
    def register_agent_type(self, role: AgentRole, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent type.
        
        Args:
            role: Agent role
            agent_class: Agent class to register
        """
        self._agent_types[role.value] = agent_class
        logger.info(f"Registered agent type: {role.value} -> {agent_class.__name__}")
    
    def get_agent_type(self, role: AgentRole) -> Optional[Type[BaseAgent]]:
        """
        Get agent type by role.
        
        Args:
            role: Agent role
            
        Returns:
            Agent class or None if not found
        """
        return self._agent_types.get(role.value)
    
    def list_agent_types(self) -> List[str]:
        """List all registered agent types."""
        return list(self._agent_types.keys())
    
    def register_agent_instance(self, agent: BaseAgent) -> None:
        """
        Register an agent instance.
        
        Args:
            agent: Agent instance to register
        """
        self._agent_instances[agent.agent_id] = agent
        logger.info(f"Registered agent instance: {agent.name} ({agent.agent_id})")
    
    def get_agent_instance(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent instance by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent instance or None if not found
        """
        return self._agent_instances.get(agent_id)
    
    def list_agent_instances(self) -> List[BaseAgent]:
        """List all registered agent instances."""
        return list(self._agent_instances.values())
    
    def remove_agent_instance(self, agent_id: str) -> None:
        """
        Remove agent instance from registry.
        
        Args:
            agent_id: Agent ID to remove
        """
        if agent_id in self._agent_instances:
            agent = self._agent_instances.pop(agent_id)
            logger.info(f"Removed agent instance: {agent.name} ({agent_id})")


class AgentFactory:
    """
    Factory for creating agent instances.
    
    Learning Note: The factory pattern provides a clean interface
    for creating agents with proper configuration.
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    async def create_agent(self, role: AgentRole, config: Optional[AgentConfig] = None) -> Optional[BaseAgent]:
        """
        Create an agent instance.
        
        Args:
            role: Agent role
            config: Agent configuration (uses defaults if None)
            
        Returns:
            Agent instance or None if role not found
        """
        agent_class = self.registry.get_agent_type(role)
        if not agent_class:
            logger.error(f"Agent type not found for role: {role.value}")
            return None
        
        try:
            # Create agent instance - let each agent handle its own default config
            agent = agent_class(config)
            
            # Register instance
            self.registry.register_agent_instance(agent)
            
            logger.info(f"Created agent: {agent.name} ({agent.role.value})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {role.value}: {str(e)}")
            return None
    
    async def create_agent_team(self, roles: List[AgentRole]) -> List[BaseAgent]:
        """
        Create a team of agents.
        
        Args:
            roles: List of agent roles to create
            
        Returns:
            List of created agent instances
        """
        agents = []
        
        for role in roles:
            agent = await self.create_agent(role)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Failed to create agent for role: {role.value}")
        
        logger.info(f"Created agent team with {len(agents)} agents")
        return agents
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all registered agents.
        
        Returns:
            Health status for all agents
        """
        agents = self.registry.list_agent_instances()
        health_status = {
            "total_agents": len(agents),
            "agents": []
        }
        
        for agent in agents:
            try:
                agent_health = await agent.health_check()
                health_status["agents"].append(agent_health)
            except Exception as e:
                health_status["agents"].append({
                    "agent_name": agent.name,
                    "status": "error",
                    "error": str(e)
                })
        
        return health_status


# Global registry and factory instances
agent_registry = AgentRegistry()
agent_factory = AgentFactory(agent_registry)