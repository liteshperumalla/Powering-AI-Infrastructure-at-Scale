"""
Workflow engine for multi-agent orchestration.

Manages the execution flow and coordination of multiple agents.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid

from .events import EventManager, AgentEvent, EventType
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Workflow step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    name: str
    agent_name: str
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "agent_name": self.agent_name,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "execution_time": self.execution_time
        }


@dataclass
class WorkflowState:
    """State of a workflow execution."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Multi-Agent Workflow"
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    assessment: Optional[Assessment] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def completed_steps(self) -> List[WorkflowStep]:
        """Get completed steps."""
        return [step for step in self.steps if step.status == StepStatus.COMPLETED]
    
    @property
    def failed_steps(self) -> List[WorkflowStep]:
        """Get failed steps."""
        return [step for step in self.steps if step.status == StepStatus.FAILED]
    
    @property
    def pending_steps(self) -> List[WorkflowStep]:
        """Get pending steps."""
        return [step for step in self.steps if step.status == StepStatus.PENDING]
    
    @property
    def running_steps(self) -> List[WorkflowStep]:
        """Get currently running steps."""
        return [step for step in self.steps if step.status == StepStatus.RUNNING]
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready_steps = []
        completed_step_ids = {step.step_id for step in self.completed_steps}
        
        for step in self.pending_steps:
            if all(dep_id in completed_step_ids for dep_id in step.dependencies):
                ready_steps.append(step)
        
        return ready_steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "shared_data": self.shared_data,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "context": self.context,
            "progress": {
                "total_steps": len(self.steps),
                "completed_steps": len(self.completed_steps),
                "failed_steps": len(self.failed_steps),
                "running_steps": len(self.running_steps),
                "pending_steps": len(self.pending_steps)
            }
        }


class WorkflowEngine:
    """
    Workflow engine for coordinating multi-agent execution.
    
    Manages the execution flow, dependencies, and state of agent workflows.
    """
    
    def __init__(self, event_manager: EventManager):
        """
        Initialize workflow engine.
        
        Args:
            event_manager: Event manager for coordination
        """
        self.event_manager = event_manager
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.agent_executors: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
        logger.info("Workflow engine initialized")
    
    def register_agent_executor(self, agent_name: str, executor: Callable) -> None:
        """
        Register an agent executor function.
        
        Args:
            agent_name: Name of the agent
            executor: Async function that executes the agent
        """
        self.agent_executors[agent_name] = executor
        logger.info(f"Registered executor for agent: {agent_name}")
    
    async def create_workflow(self, name: str, steps: List[WorkflowStep], 
                            assessment: Assessment,
                            context: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            steps: List of workflow steps
            assessment: Assessment to process
            context: Additional context data
            
        Returns:
            Created workflow state
        """
        workflow = WorkflowState(
            name=name,
            steps=steps,
            assessment=assessment,
            context=context or {}
        )
        
        async with self._lock:
            self.active_workflows[workflow.workflow_id] = workflow
        
        logger.info(f"Created workflow: {name} ({workflow.workflow_id})")
        return workflow
    
    async def execute_workflow(self, workflow_id: str) -> WorkflowState:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            
        Returns:
            Final workflow state
            
        Raises:
            ValueError: If workflow not found
        """
        async with self._lock:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = self.active_workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PENDING:
            logger.warning(f"Workflow {workflow_id} is not in pending state")
            return workflow
        
        # Start workflow
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now(timezone.utc)
        
        await self.event_manager.publish_workflow_started(
            workflow_id, 
            {"name": workflow.name, "total_steps": len(workflow.steps)}
        )
        
        logger.info(f"Starting workflow execution: {workflow.name}")
        
        try:
            # Execute workflow steps
            await self._execute_workflow_steps(workflow)
            
            # Check final status
            if workflow.failed_steps:
                workflow.status = WorkflowStatus.FAILED
                await self.event_manager.publish_workflow_failed(
                    workflow_id,
                    f"Workflow failed with {len(workflow.failed_steps)} failed steps"
                )
            else:
                workflow.status = WorkflowStatus.COMPLETED
                await self.event_manager.publish_workflow_completed(
                    workflow_id,
                    {"completed_steps": len(workflow.completed_steps)}
                )
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            await self.event_manager.publish_workflow_failed(workflow_id, error_msg)
        
        finally:
            workflow.end_time = datetime.now(timezone.utc)
            logger.info(f"Workflow {workflow.name} completed in {workflow.execution_time:.2f}s")
        
        return workflow
    
    async def _execute_workflow_steps(self, workflow: WorkflowState) -> None:
        """Execute workflow steps with dependency management."""
        max_parallel = 3  # Maximum parallel agent executions
        
        while workflow.pending_steps and workflow.status == WorkflowStatus.RUNNING:
            # Get steps ready to execute
            ready_steps = workflow.get_ready_steps()
            
            if not ready_steps:
                # Check if we're deadlocked
                if not workflow.running_steps:
                    logger.error("Workflow deadlock detected - no ready or running steps")
                    break
                
                # Wait for running steps to complete
                await asyncio.sleep(0.5)
                continue
            
            # Limit parallel execution
            available_slots = max_parallel - len(workflow.running_steps)
            steps_to_execute = ready_steps[:available_slots]
            
            # Execute steps in parallel
            tasks = []
            for step in steps_to_execute:
                task = asyncio.create_task(self._execute_step(workflow, step))
                tasks.append(task)
            
            if tasks:
                # Wait for at least one step to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Cancel remaining tasks if workflow failed
                if workflow.status == WorkflowStatus.FAILED:
                    for task in pending:
                        task.cancel()
    
    async def _execute_step(self, workflow: WorkflowState, step: WorkflowStep) -> None:
        """Execute a single workflow step."""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now(timezone.utc)
        
        await self.event_manager.publish_agent_started(
            step.agent_name,
            {"step_id": step.step_id, "workflow_id": workflow.workflow_id}
        )
        
        logger.info(f"Executing step: {step.name} ({step.agent_name})")
        
        try:
            # Get agent executor
            if step.agent_name not in self.agent_executors:
                raise ValueError(f"No executor registered for agent: {step.agent_name}")
            
            executor = self.agent_executors[step.agent_name]
            
            # Execute agent with retry logic
            for attempt in range(step.max_retries + 1):
                try:
                    step.retry_count = attempt
                    
                    # Execute agent
                    result = await executor(
                        assessment=workflow.assessment,
                        context={
                            **workflow.context,
                            "shared_data": workflow.shared_data,
                            "step_id": step.step_id,
                            "workflow_id": workflow.workflow_id
                        }
                    )
                    
                    # Store result
                    step.result = result
                    step.status = StepStatus.COMPLETED
                    step.end_time = datetime.now(timezone.utc)
                    
                    # Update shared data
                    if isinstance(result, dict) and "data" in result:
                        workflow.shared_data[step.agent_name] = result["data"]
                    
                    await self.event_manager.publish_agent_completed(
                        step.agent_name,
                        {
                            "step_id": step.step_id,
                            "workflow_id": workflow.workflow_id,
                            "execution_time": step.execution_time
                        }
                    )
                    
                    logger.info(f"Step completed: {step.name} in {step.execution_time:.2f}s")
                    return
                    
                except Exception as e:
                    error_msg = f"Step execution failed (attempt {attempt + 1}): {str(e)}"
                    logger.warning(error_msg)
                    
                    if attempt < step.max_retries:
                        # Wait before retry
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        # Final failure
                        step.error = error_msg
                        step.status = StepStatus.FAILED
                        step.end_time = datetime.now(timezone.utc)
                        
                        await self.event_manager.publish_agent_failed(
                            step.agent_name,
                            error_msg,
                            {"step_id": step.step_id, "workflow_id": workflow.workflow_id}
                        )
                        
                        logger.error(f"Step failed permanently: {step.name}")
                        return
        
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error in step execution: {str(e)}"
            step.error = error_msg
            step.status = StepStatus.FAILED
            step.end_time = datetime.now(timezone.utc)
            
            await self.event_manager.publish_agent_failed(
                step.agent_name,
                error_msg,
                {"step_id": step.step_id, "workflow_id": workflow.workflow_id}
            )
            
            logger.error(error_msg, exc_info=True)
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow status."""
        async with self._lock:
            return self.active_workflows.get(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        async with self._lock:
            if workflow_id not in self.active_workflows:
                return False
            
            workflow = self.active_workflows[workflow_id]
            
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.CANCELLED
                workflow.end_time = datetime.now(timezone.utc)
                
                # Mark running steps as cancelled
                for step in workflow.running_steps:
                    step.status = StepStatus.SKIPPED
                    step.end_time = datetime.now(timezone.utc)
                
                logger.info(f"Cancelled workflow: {workflow.name}")
                return True
        
        return False
    
    def get_active_workflows(self) -> List[WorkflowState]:
        """Get list of active workflows."""
        return [
            workflow for workflow in self.active_workflows.values()
            if workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]
        ]
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow engine statistics."""
        workflows = list(self.active_workflows.values())
        
        status_counts = {}
        for workflow in workflows:
            status = workflow.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_workflows": len(workflows),
            "status_counts": status_counts,
            "registered_agents": list(self.agent_executors.keys()),
            "active_workflows": len(self.get_active_workflows())
        }
    
    async def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed workflows.
        
        Args:
            max_age_hours: Maximum age in hours for completed workflows
            
        Returns:
            Number of workflows cleaned up
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        async with self._lock:
            workflows_to_remove = []
            
            for workflow_id, workflow in self.active_workflows.items():
                if (workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                    workflow.end_time and workflow.end_time.timestamp() < cutoff_time):
                    workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                del self.active_workflows[workflow_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old workflows")
        
        return cleaned_count