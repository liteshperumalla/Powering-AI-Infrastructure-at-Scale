"""
Enhanced Workflow Manager with Production-Grade Reliability.

Addresses critical issues identified in workflow analysis:
1. Workflow timeout handling with configurable limits
2. Deadlock detection and recovery with root cause analysis
3. Circuit breaker pattern for agent execution
4. Checkpoint recovery mechanism
5. Enhanced error propagation to dependent nodes
6. Graceful degradation support

Author: AI Workflow Specialist
Date: 2025-11-04
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import traceback

from .base import (
    BaseWorkflow, WorkflowState, WorkflowNode, WorkflowResult,
    WorkflowStatus, NodeStatus
)
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 3  # Open after N failures
    success_threshold: int = 2  # Close after N successes in half-open
    timeout: int = 60  # Seconds before trying half-open


@dataclass
class CircuitBreaker:
    """Circuit breaker for agent execution."""
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_success(self) -> None:
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed execution."""
        self.last_failure_time = datetime.now(timezone.utc)

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open goes back to open
            self._transition_to_open()

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.last_failure_time:
                elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
                if elapsed >= self.config.timeout:
                    self._transition_to_half_open()
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        logger.warning(f"Circuit breaker {self.name} transitioning to OPEN (failing)")
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now(timezone.utc)

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN (testing)")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.now(timezone.utc)

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        logger.info(f"Circuit breaker {self.name} transitioning to CLOSED (healthy)")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now(timezone.utc)


@dataclass
class DeadlockAnalysis:
    """Analysis of workflow deadlock."""
    deadlocked_nodes: List[str]
    missing_dependencies: Dict[str, List[str]]
    circular_dependencies: List[List[str]]
    failed_upstream: Dict[str, List[str]]
    root_causes: List[str]
    recoverable: bool
    recovery_strategy: Optional[str] = None


@dataclass
class WorkflowTimeoutConfig:
    """Timeout configuration for workflows."""
    workflow_timeout: int = 1800  # 30 minutes default
    node_timeout: int = 300  # 5 minutes default per node
    enable_timeout: bool = True
    timeout_strategy: str = "graceful"  # "graceful" or "abort"


class EnhancedWorkflowManager:
    """
    Enhanced workflow manager with production-grade reliability.

    Key Improvements:
    1. Configurable workflow and node timeouts
    2. Intelligent deadlock detection and recovery
    3. Circuit breakers for agent execution
    4. Checkpoint-based recovery
    5. Enhanced error propagation
    6. Graceful degradation
    """

    def __init__(
        self,
        timeout_config: Optional[WorkflowTimeoutConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """Initialize enhanced workflow manager."""
        self.workflow_definitions: Dict[str, BaseWorkflow] = {}
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.timeout_config = timeout_config or WorkflowTimeoutConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()

        # Circuit breakers per node type
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Checkpoint storage
        self.checkpoints: Dict[str, List[WorkflowState]] = defaultdict(list)

        # Metrics
        self.metrics = {
            "workflows_completed": 0,
            "workflows_failed": 0,
            "workflows_timeout": 0,
            "deadlocks_detected": 0,
            "deadlocks_recovered": 0,
            "circuit_breaks": 0
        }

        logger.info("Enhanced workflow manager initialized with timeout and circuit breaker support")

    def register_workflow(self, workflow_id: str, workflow: BaseWorkflow) -> None:
        """Register a workflow definition."""
        self.workflow_definitions[workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow_id}")

    async def execute_workflow(
        self,
        workflow_id: str,
        assessment: Assessment,
        context: Optional[Dict[str, Any]] = None,
        resume_from_checkpoint: bool = False
    ) -> WorkflowResult:
        """
        Execute workflow with enhanced reliability features.

        Features:
        - Configurable timeouts
        - Deadlock detection and recovery
        - Circuit breaker protection
        - Checkpoint recovery
        - Graceful degradation
        """
        workflow = self.workflow_definitions.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not registered")

        # Check for checkpoint if resuming
        state = None
        if resume_from_checkpoint:
            state = self._get_latest_checkpoint(workflow_id, str(assessment.id))
            if state:
                logger.info(f"Resuming workflow from checkpoint: {len(state.nodes)} nodes")

        # Start fresh if no checkpoint
        if not state:
            state = await self._start_workflow(workflow_id, assessment, context)

        # Execute with timeout wrapper
        try:
            if self.timeout_config.enable_timeout:
                result = await asyncio.wait_for(
                    self._execute_workflow_with_recovery(workflow, state, assessment),
                    timeout=self.timeout_config.workflow_timeout
                )
            else:
                result = await self._execute_workflow_with_recovery(workflow, state, assessment)

            self.metrics["workflows_completed"] += 1
            return result

        except asyncio.TimeoutError:
            logger.error(f"Workflow {workflow_id} timed out after {self.timeout_config.workflow_timeout}s")
            self.metrics["workflows_timeout"] += 1

            # Handle timeout based on strategy
            if self.timeout_config.timeout_strategy == "graceful":
                # Return partial results
                return await self._handle_timeout_gracefully(workflow, state, assessment)
            else:
                # Abort workflow
                return WorkflowResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.FAILED,
                    assessment_id=str(assessment.id),
                    error=f"Workflow timeout after {self.timeout_config.workflow_timeout}s"
                )

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            self.metrics["workflows_failed"] += 1

            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                assessment_id=str(assessment.id),
                error=str(e)
            )

    async def _execute_workflow_with_recovery(
        self,
        workflow: BaseWorkflow,
        state: WorkflowState,
        assessment: Assessment
    ) -> WorkflowResult:
        """Execute workflow with recovery mechanisms."""
        try:
            # Track execution start
            self.active_workflows[state.workflow_id] = state

            # Execute workflow nodes
            iteration = 0
            max_iterations = len(state.nodes) * 2  # Prevent infinite loops

            while not state.is_complete() and not state.has_failed_nodes() and iteration < max_iterations:
                ready_nodes = state.get_ready_nodes()

                if not ready_nodes:
                    # Check for deadlock
                    deadlock_analysis = await self._analyze_deadlock(state)

                    if deadlock_analysis.deadlocked_nodes:
                        self.metrics["deadlocks_detected"] += 1
                        logger.error(f"Deadlock detected: {deadlock_analysis.root_causes}")

                        # Attempt recovery
                        if deadlock_analysis.recoverable:
                            recovered = await self._recover_from_deadlock(
                                workflow, state, deadlock_analysis, assessment
                            )
                            if recovered:
                                self.metrics["deadlocks_recovered"] += 1
                                continue

                        # Recovery failed
                        state.status = WorkflowStatus.FAILED
                        state.metadata["deadlock_analysis"] = {
                            "nodes": deadlock_analysis.deadlocked_nodes,
                            "root_causes": deadlock_analysis.root_causes,
                            "recoverable": deadlock_analysis.recoverable
                        }
                        break
                    else:
                        # All nodes processed
                        break

                # Save checkpoint before executing nodes
                self._save_checkpoint(state)

                # Execute ready nodes with circuit breaker protection
                tasks = []
                for node in ready_nodes:
                    task = self._execute_node_with_circuit_breaker(workflow, node, state, assessment)
                    tasks.append(task)

                # Wait for all nodes with individual timeouts
                await asyncio.gather(*tasks, return_exceptions=True)

                iteration += 1

            # Check for max iterations exceeded
            if iteration >= max_iterations:
                logger.error(f"Workflow exceeded max iterations: {max_iterations}")
                state.status = WorkflowStatus.FAILED
                state.metadata["error"] = "Max iterations exceeded - possible circular dependency"

            # Complete workflow
            return await self._finalize_workflow(workflow, state, assessment)

        finally:
            # Cleanup
            self.active_workflows.pop(state.workflow_id, None)

    async def _execute_node_with_circuit_breaker(
        self,
        workflow: BaseWorkflow,
        node: WorkflowNode,
        state: WorkflowState,
        assessment: Assessment
    ) -> None:
        """Execute node with circuit breaker protection."""
        # Get or create circuit breaker for this node type
        circuit_breaker = self.circuit_breakers.get(node.node_type)
        if not circuit_breaker:
            circuit_breaker = CircuitBreaker(
                name=node.node_type,
                config=self.circuit_breaker_config
            )
            self.circuit_breakers[node.node_type] = circuit_breaker

        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for {node.node_type}, skipping node {node.id}")
            self.metrics["circuit_breaks"] += 1

            # Mark node as failed with circuit breaker reason
            node.mark_failed(f"Circuit breaker open for {node.node_type}")
            state.metadata.setdefault("circuit_breaker_skips", []).append(node.id)

            # Propagate failure to dependent nodes
            await self._propagate_failure_to_dependents(node, state)
            return

        try:
            # Execute with node-level timeout
            if self.timeout_config.enable_timeout:
                node_timeout = node.config.get("timeout", self.timeout_config.node_timeout)
                await asyncio.wait_for(
                    self._execute_node_with_tracking(workflow, node, state, assessment),
                    timeout=node_timeout
                )
            else:
                await self._execute_node_with_tracking(workflow, node, state, assessment)

            # Record success in circuit breaker
            circuit_breaker.record_success()

        except asyncio.TimeoutError:
            logger.error(f"Node {node.id} timed out")
            node.mark_failed(f"Node timeout after {node_timeout}s")
            circuit_breaker.record_failure()
            await self._propagate_failure_to_dependents(node, state)

        except Exception as e:
            logger.error(f"Node {node.id} failed: {str(e)}")
            node.mark_failed(str(e))
            circuit_breaker.record_failure()
            await self._propagate_failure_to_dependents(node, state)

    async def _execute_node_with_tracking(
        self,
        workflow: BaseWorkflow,
        node: WorkflowNode,
        state: WorkflowState,
        assessment: Assessment
    ) -> None:
        """Execute a node with proper tracking."""
        try:
            node.mark_started()
            state.current_node = node.id

            await workflow._trigger_hooks("on_node_start", node=node, state=state)

            logger.debug(f"Executing node {node.id} ({node.name})")

            # Execute node
            result = await workflow.execute_node(node, state)

            # Mark as completed
            node.mark_completed(result)
            state.node_results[node.id] = result

            await workflow._trigger_hooks("on_node_complete", node=node, state=state, result=result)

        except Exception as e:
            error_msg = f"Node {node.id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            node.mark_failed(error_msg)
            node.metadata["error"] = str(e)
            node.metadata["traceback"] = traceback.format_exc()

            await workflow._trigger_hooks("on_error", node=node, state=state, error=e)
            raise

    async def _analyze_deadlock(self, state: WorkflowState) -> DeadlockAnalysis:
        """
        Analyze workflow deadlock and identify root causes.

        Checks for:
        1. Missing dependencies (nodes waiting for non-existent nodes)
        2. Circular dependencies
        3. Failed upstream nodes blocking progress
        """
        pending_nodes = [n for n in state.nodes.values() if n.status == NodeStatus.PENDING]

        if not pending_nodes:
            return DeadlockAnalysis(
                deadlocked_nodes=[],
                missing_dependencies={},
                circular_dependencies=[],
                failed_upstream={},
                root_causes=[],
                recoverable=False
            )

        # Check for missing dependencies
        missing_deps = {}
        for node in pending_nodes:
            missing = [dep for dep in node.dependencies if dep not in state.nodes]
            if missing:
                missing_deps[node.id] = missing

        # Check for failed upstream dependencies
        failed_upstream = {}
        for node in pending_nodes:
            failed_deps = [
                dep for dep in node.dependencies
                if dep in state.nodes and state.nodes[dep].status == NodeStatus.FAILED
            ]
            if failed_deps:
                failed_upstream[node.id] = failed_deps

        # Detect circular dependencies (simplified check)
        circular_deps = self._detect_circular_dependencies(pending_nodes, state)

        # Determine root causes
        root_causes = []
        if missing_deps:
            root_causes.append(f"Missing dependencies: {missing_deps}")
        if failed_upstream:
            root_causes.append(f"Failed upstream nodes blocking progress: {failed_upstream}")
        if circular_deps:
            root_causes.append(f"Circular dependencies detected: {circular_deps}")

        if not root_causes:
            root_causes.append("Unknown deadlock cause - all dependencies exist and are not failed")

        # Determine if recoverable
        recoverable = bool(failed_upstream) and not missing_deps and not circular_deps
        recovery_strategy = "skip_failed_nodes" if recoverable else None

        return DeadlockAnalysis(
            deadlocked_nodes=[n.id for n in pending_nodes],
            missing_dependencies=missing_deps,
            circular_dependencies=circular_deps,
            failed_upstream=failed_upstream,
            root_causes=root_causes,
            recoverable=recoverable,
            recovery_strategy=recovery_strategy
        )

    def _detect_circular_dependencies(
        self,
        pending_nodes: List[WorkflowNode],
        state: WorkflowState
    ) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        # Build adjacency list for pending nodes
        graph = {node.id: node.dependencies for node in pending_nodes}

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node_id: str, path: List[str]) -> None:
            if node_id in rec_stack:
                # Found cycle
                cycle_start = path.index(node_id)
                cycles.append(path[cycle_start:] + [node_id])
                return

            if node_id in visited:
                return

            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for dep in graph.get(node_id, []):
                if dep in graph:  # Only check pending nodes
                    dfs(dep, path[:])

            rec_stack.remove(node_id)

        for node_id in graph:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles

    async def _recover_from_deadlock(
        self,
        workflow: BaseWorkflow,
        state: WorkflowState,
        analysis: DeadlockAnalysis,
        assessment: Assessment
    ) -> bool:
        """
        Attempt to recover from deadlock.

        Recovery strategies:
        1. Skip nodes blocked by failed upstream (get partial results)
        2. Mark unrecoverable nodes as skipped
        """
        if analysis.recovery_strategy == "skip_failed_nodes":
            logger.info(f"Attempting deadlock recovery: skipping nodes blocked by failures")

            # Mark blocked nodes as skipped with metadata
            for node_id, failed_deps in analysis.failed_upstream.items():
                if node_id in state.nodes:
                    node = state.nodes[node_id]
                    node.status = NodeStatus.FAILED
                    node.metadata["skipped_reason"] = f"Blocked by failed dependencies: {failed_deps}"
                    node.metadata["recoverable_failure"] = True

                    logger.info(f"Skipped node {node_id} (blocked by {failed_deps})")

            return True

        return False

    async def _propagate_failure_to_dependents(
        self,
        failed_node: WorkflowNode,
        state: WorkflowState
    ) -> None:
        """Propagate failure information to dependent nodes."""
        # Find all nodes that depend on this node
        dependent_nodes = [
            node for node in state.nodes.values()
            if failed_node.id in node.dependencies
        ]

        for node in dependent_nodes:
            if node.status == NodeStatus.PENDING:
                # Add metadata about upstream failure
                node.metadata.setdefault("upstream_failures", []).append({
                    "node_id": failed_node.id,
                    "error": failed_node.metadata.get("error", "Unknown error"),
                    "failed_at": failed_node.ended_at.isoformat() if failed_node.ended_at else None
                })

                logger.debug(f"Propagated failure from {failed_node.id} to {node.id}")

    def _save_checkpoint(self, state: WorkflowState) -> None:
        """Save workflow checkpoint for recovery."""
        # Deep copy state for checkpoint
        import copy
        checkpoint = copy.deepcopy(state)

        # Keep only last 10 checkpoints per workflow
        workflow_checkpoints = self.checkpoints[state.workflow_id]
        workflow_checkpoints.append(checkpoint)

        if len(workflow_checkpoints) > 10:
            workflow_checkpoints.pop(0)

        logger.debug(f"Saved checkpoint for workflow {state.workflow_id}")

    def _get_latest_checkpoint(self, workflow_id: str, assessment_id: str) -> Optional[WorkflowState]:
        """Get latest checkpoint for workflow recovery."""
        checkpoints = self.checkpoints.get(workflow_id, [])

        # Find checkpoints for this assessment
        matching_checkpoints = [
            cp for cp in checkpoints
            if cp.assessment_id == assessment_id
        ]

        if matching_checkpoints:
            return matching_checkpoints[-1]

        return None

    async def _handle_timeout_gracefully(
        self,
        workflow: BaseWorkflow,
        state: WorkflowState,
        assessment: Assessment
    ) -> WorkflowResult:
        """Handle workflow timeout with graceful degradation."""
        logger.info(f"Handling timeout gracefully, preserving partial results")

        # Mark incomplete nodes as timed out
        for node in state.nodes.values():
            if node.status == NodeStatus.RUNNING:
                node.status = NodeStatus.FAILED
                node.metadata["timeout"] = True
            elif node.status == NodeStatus.PENDING:
                node.status = NodeStatus.FAILED
                node.metadata["not_started"] = True

        state.status = WorkflowStatus.FAILED
        state.completed_at = datetime.now(timezone.utc)
        state.metadata["timeout"] = True
        state.metadata["partial_results"] = True

        # Create result with partial data
        completed_count = sum(1 for n in state.nodes.values() if n.status == NodeStatus.COMPLETED)

        return WorkflowResult(
            workflow_id=state.workflow_id,
            status=WorkflowStatus.FAILED,
            assessment_id=state.assessment_id,
            agent_results=state.agent_results,
            final_data=state.shared_data,
            execution_time=state.execution_time,
            node_count=len(state.nodes),
            completed_nodes=completed_count,
            failed_nodes=len(state.nodes) - completed_count,
            error=f"Workflow timeout - {completed_count}/{len(state.nodes)} nodes completed",
            metadata={"partial_results": True, "timeout": True}
        )

    async def _finalize_workflow(
        self,
        workflow: BaseWorkflow,
        state: WorkflowState,
        assessment: Assessment
    ) -> WorkflowResult:
        """Finalize workflow execution."""
        # Determine final status
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
            failed_nodes=sum(1 for n in state.nodes.values() if n.status == NodeStatus.FAILED),
            metadata=state.metadata
        )

        logger.info(
            f"Workflow {workflow.name} completed in {state.execution_time:.2f}s "
            f"({result.completed_nodes}/{result.node_count} nodes successful)"
        )

        return result

    async def _start_workflow(
        self,
        workflow_id: str,
        assessment: Assessment,
        context: Optional[Dict[str, Any]]
    ) -> WorkflowState:
        """Start a new workflow."""
        workflow = self.workflow_definitions[workflow_id]

        # Initialize state
        state = WorkflowState(
            workflow_id=workflow_id,
            assessment_id=str(assessment.id),
            status=WorkflowStatus.RUNNING
        )

        # Add workflow nodes
        for node in workflow.get_nodes():
            state.add_node(node)

        # Initialize shared data
        if context:
            state.shared_data.update(context)

        # Trigger start hooks
        await workflow._trigger_hooks("before_start", state=state, assessment=assessment)

        logger.info(f"Started workflow {workflow.name} for assessment {assessment.id}")

        return state

    def get_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics."""
        # Add circuit breaker states
        circuit_states = {
            name: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count
            }
            for name, breaker in self.circuit_breakers.items()
        }

        return {
            **self.metrics,
            "circuit_breakers": circuit_states,
            "active_workflows": len(self.active_workflows),
            "registered_workflows": len(self.workflow_definitions)
        }


# Global singleton
_enhanced_workflow_manager = None

def get_enhanced_workflow_manager(
    timeout_config: Optional[WorkflowTimeoutConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
) -> EnhancedWorkflowManager:
    """Get or create enhanced workflow manager singleton."""
    global _enhanced_workflow_manager

    if _enhanced_workflow_manager is None:
        _enhanced_workflow_manager = EnhancedWorkflowManager(
            timeout_config, circuit_breaker_config
        )

    return _enhanced_workflow_manager
