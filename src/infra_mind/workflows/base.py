"""
Base workflow system for Infra Mind.

Provides the foundation for LangGraph-based workflow orchestration.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field
import uuid
import yaml

from ..models.assessment import Assessment
from ..agents.base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """Individual node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """
    Individual node in a workflow.
    
    Learning Note: Each node represents a step in the workflow,
    typically corresponding to an agent execution or decision point.
    """
    id: str
    name: str
    node_type: str  # "agent", "decision", "parallel", "sequential"
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def mark_started(self) -> None:
        """Mark node as started."""
        self.status = NodeStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Mark node as completed."""
        self.status = NodeStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error: str) -> None:
        """Mark node as failed."""
        self.status = NodeStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)


@dataclass
class WorkflowState:
    """
    State container for workflow execution.
    
    Learning Note: This maintains the shared state across all
    workflow nodes and provides context for agent execution.
    """
    workflow_id: str
    assessment_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_node: Optional[str] = None
    
    # Shared data across workflow
    shared_data: Dict[str, Any] = field(default_factory=dict)
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    node_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Execution tracking
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate workflow progress percentage."""
        if not self.nodes:
            return 0.0
        
        completed_nodes = sum(1 for node in self.nodes.values() 
                            if node.status == NodeStatus.COMPLETED)
        return (completed_nodes / len(self.nodes)) * 100.0
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a workflow node by ID."""
        return self.nodes.get(node_id)
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the workflow."""
        self.nodes[node.id] = node
    
    def get_ready_nodes(self) -> List[WorkflowNode]:
        """Get nodes that are ready to execute (dependencies satisfied)."""
        ready_nodes = []
        
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = all(
                self.nodes.get(dep_id, WorkflowNode("", "", "")).status == NodeStatus.COMPLETED
                for dep_id in node.dependencies
            )
            
            if dependencies_met:
                ready_nodes.append(node)
        
        return ready_nodes
    
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return all(node.status in [NodeStatus.COMPLETED, NodeStatus.SKIPPED] 
                  for node in self.nodes.values())
    
    def has_failed_nodes(self) -> bool:
        """Check if any nodes have failed."""
        return any(node.status == NodeStatus.FAILED for node in self.nodes.values())


@dataclass
class WorkflowResult:
    """Result from workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    assessment_id: str
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    final_data: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    error: Optional[str] = None
    node_count: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of nodes."""
        if self.node_count == 0:
            return 0.0
        return (self.completed_nodes / self.node_count) * 100.0


class BaseWorkflow(ABC):
    """
    Base class for workflow definitions.
    
    Learning Note: This provides the interface that all workflows
    must implement, ensuring consistency across different workflow types.
    """
    
    def __init__(self, workflow_id: str, name: str):
        """
        Initialize the workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            name: Human-readable workflow name
        """
        self.workflow_id = workflow_id
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.execution_hooks: Dict[str, List[Callable]] = {
            "before_start": [],
            "after_complete": [],
            "on_node_start": [],
            "on_node_complete": [],
            "on_error": []
        }
    
    @abstractmethod
    async def define_workflow(self, assessment: Assessment) -> WorkflowState:
        """
        Define the workflow structure.
        
        Args:
            assessment: Assessment to process
            
        Returns:
            Initial workflow state
        """
        pass
    
    @abstractmethod
    async def execute_node(self, node: WorkflowNode, state: WorkflowState) -> Dict[str, Any]:
        """
        Execute a specific workflow node.
        
        Args:
            node: Node to execute
            state: Current workflow state
            
        Returns:
            Node execution result
        """
        pass
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the workflow definition."""
        self.nodes[node.id] = node
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """Add an execution hook."""
        if event in self.execution_hooks:
            self.execution_hooks[event].append(callback)
    
    async def _trigger_hooks(self, event: str, **kwargs) -> None:
        """Trigger execution hooks."""
        for callback in self.execution_hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(**kwargs)
                else:
                    callback(**kwargs)
            except Exception as e:
                logger.error(f"Hook execution failed for {event}: {str(e)}")


class WorkflowManager:
    """
    Manager for workflow execution and orchestration.
    
    Learning Note: This class handles the actual execution of workflows,
    managing state, dependencies, and error handling.
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_definitions: Dict[str, BaseWorkflow] = {}
    
    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """
        Register a workflow definition.
        
        Args:
            workflow: Workflow to register
        """
        self.workflow_definitions[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.name} ({workflow.workflow_id})")
    
    async def start_workflow(
        self, 
        workflow_id: str, 
        assessment: Assessment,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Start a workflow execution.
        
        Args:
            workflow_id: ID of the workflow to start
            assessment: Assessment to process
            context: Additional context data
            
        Returns:
            Initial workflow state
            
        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self.workflow_definitions[workflow_id]
        
        # Create workflow state
        state = await workflow.define_workflow(assessment)
        state.shared_data.update(context or {})
        state.status = WorkflowStatus.RUNNING
        state.started_at = datetime.now(timezone.utc)
        
        # Store active workflow
        self.active_workflows[state.workflow_id] = state
        
        # Trigger hooks
        await workflow._trigger_hooks("before_start", state=state, assessment=assessment)
        
        logger.info(f"Started workflow {workflow.name} for assessment {assessment.id}")
        return state
    
    async def execute_workflow(
        self,
        workflow_id: str,
        assessment: Assessment,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute a complete workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            assessment: Assessment to process
            context: Additional context data
            
        Returns:
            Workflow execution result
        """
        try:
            # Start workflow
            state = await self.start_workflow(workflow_id, assessment, context)
            workflow = self.workflow_definitions[workflow_id]
            
            # Execute workflow nodes
            while not state.is_complete() and not state.has_failed_nodes():
                ready_nodes = state.get_ready_nodes()
                
                if not ready_nodes:
                    # No ready nodes - check for deadlock
                    pending_nodes = [n for n in state.nodes.values() 
                                   if n.status == NodeStatus.PENDING]
                    if pending_nodes:
                        error_msg = f"Workflow deadlock detected. Pending nodes: {[n.id for n in pending_nodes]}"
                        logger.error(error_msg)
                        state.status = WorkflowStatus.FAILED
                        break
                    else:
                        # All nodes processed
                        break
                
                # Execute ready nodes (can be parallel)
                tasks = []
                for node in ready_nodes:
                    task = self._execute_node_with_tracking(workflow, node, state)
                    tasks.append(task)
                
                # Wait for all nodes to complete
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Complete workflow
            if state.has_failed_nodes():
                state.status = WorkflowStatus.FAILED
            else:
                state.status = WorkflowStatus.COMPLETED
            
            state.completed_at = datetime.now(timezone.utc)
            
            # Trigger completion hooks
            await workflow._trigger_hooks("after_complete", state=state, assessment=assessment)
            
            # Create result
            result = WorkflowResult(
                workflow_id=state.workflow_id,
                status=state.status,
                assessment_id=state.assessment_id,
                agent_results=state.agent_results,
                final_data=state.shared_data,
                execution_time=state.execution_time,
                node_count=len(state.nodes),
                completed_nodes=sum(1 for n in state.nodes.values() if n.status == NodeStatus.COMPLETED),
                failed_nodes=sum(1 for n in state.nodes.values() if n.status == NodeStatus.FAILED)
            )
            
            # Clean up
            self.active_workflows.pop(state.workflow_id, None)
            
            logger.info(f"Completed workflow {workflow.name} in {state.execution_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                assessment_id=str(assessment.id),
                error=error_msg
            )
    
    async def _execute_node_with_tracking(
        self,
        workflow: BaseWorkflow,
        node: WorkflowNode,
        state: WorkflowState
    ) -> None:
        """Execute a node with proper tracking and error handling."""
        try:
            # Mark node as started
            node.mark_started()
            state.current_node = node.id
            
            # Trigger hooks
            await workflow._trigger_hooks("on_node_start", node=node, state=state)
            
            logger.debug(f"Executing node {node.id} ({node.name})")
            
            # Execute node
            result = await workflow.execute_node(node, state)
            
            # Mark as completed
            node.mark_completed(result)
            state.node_results[node.id] = result
            state.execution_order.append(node.id)
            
            # Trigger hooks
            await workflow._trigger_hooks("on_node_complete", node=node, state=state, result=result)
            
            logger.debug(f"Completed node {node.id} in {node.execution_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Node {node.id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            node.mark_failed(error_msg)
            
            # Trigger error hooks
            await workflow._trigger_hooks("on_error", node=node, state=state, error=e)
    
    def get_workflow_status(self, workflow_instance_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running workflow."""
        state = self.active_workflows.get(workflow_instance_id)
        if not state:
            return None
        
        return {
            "workflow_id": state.workflow_id,
            "assessment_id": state.assessment_id,
            "status": state.status.value,
            "current_node": state.current_node,
            "progress_percentage": state.progress_percentage,
            "execution_time": state.execution_time,
            "node_count": len(state.nodes),
            "completed_nodes": sum(1 for n in state.nodes.values() if n.status == NodeStatus.COMPLETED),
            "failed_nodes": sum(1 for n in state.nodes.values() if n.status == NodeStatus.FAILED)
        }
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows."""
        return [
            self.get_workflow_status(workflow_id)
            for workflow_id in self.active_workflows.keys()
        ]
    
    async def cancel_workflow(self, workflow_instance_id: str) -> bool:
        """Cancel a running workflow."""
        state = self.active_workflows.get(workflow_instance_id)
        if not state:
            return False
        
        state.status = WorkflowStatus.CANCELLED
        state.completed_at = datetime.now(timezone.utc)
        
        # Clean up
        self.active_workflows.pop(workflow_instance_id, None)
        
        logger.info(f"Cancelled workflow {workflow_instance_id}")
        return True


# Global workflow manager instance
workflow_manager = WorkflowManager()