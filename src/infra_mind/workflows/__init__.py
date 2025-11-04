"""
Workflow orchestration package for Infra Mind.

Contains LangGraph-based workflow definitions and orchestration logic.
"""

from .base import WorkflowManager, WorkflowState, WorkflowResult
from .parallel_assessment_workflow import ParallelAssessmentWorkflow as AssessmentWorkflow  # 10x faster parallel execution
from .orchestrator import AgentOrchestrator

# Legacy import for backwards compatibility
from .assessment_workflow import AssessmentWorkflow as SequentialAssessmentWorkflow

__all__ = [
    "WorkflowManager",
    "WorkflowState",
    "WorkflowResult",
    "AssessmentWorkflow",  # Now points to parallel implementation
    "SequentialAssessmentWorkflow",  # Legacy sequential version (backup)
    "AgentOrchestrator"
]