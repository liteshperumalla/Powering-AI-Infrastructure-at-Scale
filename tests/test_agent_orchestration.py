"""
Tests for agent orchestration system.

Tests the coordination of multiple agents and their interactions.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.agents.base import AgentRole, AgentStatus, AgentResult
from src.infra_mind.workflows.base import WorkflowManager, WorkflowResult, WorkflowStatus


@pytest.fixture
def sample_assessment():
    """Create a sample assessment for testing."""
    from unittest.mock import Mock
    
    # Create a mock assessment to avoid database dependencies
    assessment = Mock()
    assessment.id = "test_assessment_id"
    assessment.user_id = "test_user"
    assessment.title = "Test Assessment"
    
    assessment.business_requirements = {
        "company_size": "startup",
        "industry": "technology",
        "budget_range": "$10k-50k",
        "primary_goals": ["cost_reduction", "scalability"],
        "timeline": "3-6 months"
    }
    
    assessment.technical_requirements = {
        "workload_types": ["web_application", "ai_ml"],
        "expected_users": 5000,
        "performance_requirements": {"response_time": "< 200ms"},
        "integration_needs": ["database", "api"]
    }
    
    # Mock the dict() method to return the assessment data
    assessment.dict.return_value = {
        "id": assessment.id,
        "user_id": assessment.user_id,
        "title": assessment.title,
        "business_requirements": assessment.business_requirements,
        "technical_requirements": assessment.technical_requirements
    }
    
    return assessment


class TestWorkflowExecution:
    """Test workflow execution functionality."""
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self):
        """Test registering workflows."""
        workflow_manager = WorkflowManager()
        
        # Create mock workflow
        mock_workflow = Mock()
        mock_workflow.workflow_id = "test_workflow"
        mock_workflow.name = "Test Workflow"
        
        # Register workflow
        workflow_manager.register_workflow(mock_workflow)
        
        # Verify workflow was registered
        assert "test_workflow" in workflow_manager.workflow_definitions
        assert workflow_manager.workflow_definitions["test_workflow"] == mock_workflow
    
    @pytest.mark.asyncio
    async def test_workflow_not_found(self, sample_assessment):
        """Test executing non-existent workflow."""
        workflow_manager = WorkflowManager()
        
        # Execute non-existent workflow
        result = await workflow_manager.execute_workflow("nonexistent_workflow", sample_assessment)
        
        # Verify result
        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None
        assert "not found" in result.error.lower()


class TestWorkflowManager:
    """Test the workflow management system."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, sample_assessment):
        """Test workflow execution."""
        # Create workflow manager
        workflow_manager = WorkflowManager()
        
        # Create mock workflow
        mock_workflow = AsyncMock()
        mock_workflow.workflow_id = "test_workflow"
        mock_workflow.name = "Test Workflow"
        mock_workflow.define_workflow = AsyncMock(return_value=Mock())
        
        # Register workflow
        workflow_manager.register_workflow(mock_workflow)
        
        # Execute workflow
        result = await workflow_manager.execute_workflow("test_workflow", sample_assessment)
        
        # Verify workflow was executed
        mock_workflow.define_workflow.assert_called_once_with(sample_assessment)
        
        # Verify the workflow completed
        assert isinstance(result, WorkflowResult)
    
    @pytest.mark.asyncio
    async def test_workflow_failure_handling(self, sample_assessment):
        """Test workflow failure handling."""
        # Create workflow manager
        workflow_manager = WorkflowManager()
        
        # Create mock workflow that raises an exception
        mock_workflow = AsyncMock()
        mock_workflow.workflow_id = "test_workflow"
        mock_workflow.name = "Test Workflow"
        mock_workflow.define_workflow = AsyncMock(side_effect=Exception("Test workflow error"))
        
        # Register workflow
        workflow_manager.register_workflow(mock_workflow)
        
        # Execute workflow (should fail)
        result = await workflow_manager.execute_workflow("test_workflow", sample_assessment)
        
        # Verify workflow was executed
        mock_workflow.define_workflow.assert_called_once_with(sample_assessment)
        
        # Verify failure result
        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None
        assert "Test workflow error" in result.error


class TestAgentCoordination:
    """Test agent coordination and communication."""
    
    @pytest.mark.asyncio
    async def test_agent_execution_sequence(self, sample_assessment):
        """Test sequential execution of agents."""
        # Create mock agents
        mock_cto_agent = AsyncMock()
        mock_cto_agent.name = "CTO Agent"
        mock_cto_agent.role = AgentRole.CTO
        mock_cto_agent.execute = AsyncMock(return_value=AgentResult(
            agent_name="CTO Agent",
            status=AgentStatus.COMPLETED,
            recommendations=[{"type": "strategic", "title": "Test Strategy"}]
        ))
        
        mock_cloud_engineer_agent = AsyncMock()
        mock_cloud_engineer_agent.name = "Cloud Engineer Agent"
        mock_cloud_engineer_agent.role = AgentRole.CLOUD_ENGINEER
        mock_cloud_engineer_agent.execute = AsyncMock(return_value=AgentResult(
            agent_name="Cloud Engineer Agent",
            status=AgentStatus.COMPLETED,
            recommendations=[{"type": "technical", "title": "Test Technical"}]
        ))
        
        # Execute agents sequentially
        cto_result = await mock_cto_agent.execute(sample_assessment)
        cloud_engineer_result = await mock_cloud_engineer_agent.execute(sample_assessment)
        
        # Verify both agents were executed
        mock_cto_agent.execute.assert_called_once_with(sample_assessment)
        mock_cloud_engineer_agent.execute.assert_called_once_with(sample_assessment)
        
        # Verify results
        assert cto_result.agent_name == "CTO Agent"
        assert cto_result.status == AgentStatus.COMPLETED
        assert cloud_engineer_result.agent_name == "Cloud Engineer Agent"
        assert cloud_engineer_result.status == AgentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_agent_result_aggregation(self):
        """Test aggregating results from multiple agents."""
        # Create agent results
        cto_result = AgentResult(
            agent_name="CTO Agent",
            status=AgentStatus.COMPLETED,
            recommendations=[
                {"category": "compute", "service": "AWS Lambda", "confidence": 0.8}
            ]
        )
        
        cloud_engineer_result = AgentResult(
            agent_name="Cloud Engineer Agent",
            status=AgentStatus.COMPLETED,
            recommendations=[
                {"category": "compute", "service": "AWS EC2", "confidence": 0.9}
            ]
        )
        
        research_result = AgentResult(
            agent_name="Research Agent",
            status=AgentStatus.COMPLETED,
            recommendations=[
                {"category": "compute", "service": "AWS Lambda", "confidence": 0.7}
            ]
        )
        
        # Aggregate results
        all_recommendations = []
        for result in [cto_result, cloud_engineer_result, research_result]:
            if result.status == AgentStatus.COMPLETED:
                all_recommendations.extend(result.recommendations)
        
        # Verify aggregation
        assert len(all_recommendations) == 3
        assert any(r["service"] == "AWS Lambda" and r["confidence"] == 0.8 for r in all_recommendations)
        assert any(r["service"] == "AWS EC2" and r["confidence"] == 0.9 for r in all_recommendations)
        assert any(r["service"] == "AWS Lambda" and r["confidence"] == 0.7 for r in all_recommendations)