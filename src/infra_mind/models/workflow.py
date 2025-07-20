"""
Workflow state model for Infra Mind.

Defines the LangGraph workflow state document structure.
"""

from datetime import datetime
from typing import Dict, List, Optional
from beanie import Document, Indexed
from pydantic import Field


class WorkflowState(Document):
    """
    LangGraph workflow state document model.
    
    Learning Note: This model stores the state of LangGraph workflows,
    allowing for persistence and recovery of agent orchestration.
    """
    
    # Workflow identification
    assessment_id: str = Indexed()
    workflow_id: str = Indexed()
    workflow_type: str = Field(description="Type of workflow: assessment, recommendation, etc.")
    
    # Current state
    current_step: str = Field(description="Current workflow step/node")
    status: str = Field(
        default="running",
        description="Workflow status: running, completed, failed, paused"
    )
    
    # Agent states
    agent_states: Dict = Field(
        default_factory=dict,
        description="Current state of each agent in the workflow"
    )
    
    # Execution history
    execution_history: List[Dict] = Field(
        default_factory=list,
        description="History of workflow execution steps"
    )
    
    # Workflow configuration
    config: Dict = Field(
        default_factory=dict,
        description="Workflow configuration and parameters"
    )
    
    # Progress tracking
    total_steps: int = Field(default=0, description="Total number of workflow steps")
    completed_steps: int = Field(default=0, description="Number of completed steps")
    progress_percentage: float = Field(default=0.0, description="Workflow progress (0-100)")
    
    # Error handling
    errors: List[Dict] = Field(
        default_factory=list,
        description="List of errors encountered during execution"
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Settings:
        """Beanie document settings."""
        name = "workflow_states"
        indexes = [
            [("assessment_id", 1), ("workflow_id", 1)],  # Unique workflow identification
            [("status", 1)],  # Query by status
            [("created_at", -1)],  # Sort by creation date
        ]
    
    def __str__(self) -> str:
        """String representation of the workflow state."""
        return f"WorkflowState(id={self.workflow_id}, step={self.current_step}, status={self.status})"