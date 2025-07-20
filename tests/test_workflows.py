"""
Tests for workflow orchestration system.

Tests workflow execution, agent orchestration, and LangGraph integration.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.infra_mind.workflows.base import (
    WorkflowManager, WorkflowState, WorkflowNode, WorkflowResult,
    WorkflowStatus, NodeStatus, BaseWorkflow
)
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from src.infra_mind.workflows.orchestrator import (
    AgentOrchestrator, OrchestrationConfig, OrchestrationResult
)
from src.infra_mind.agents.base import AgentRole, AgentResult, AgentStatus


# Mock workflow for testing
class MockWorkflow(BaseWorkflow):
    """Mock workflow for testing."""
    
    def __init__(self):
        super().__init__(
            workflow_id="mock_workflow",
            name="Mock Workflow"
        )
    
    async def define_workflow(self, assessment):
        """Define a simple test workflow."""
        state = WorkflowState(
            workflow_id=f"test_{assessment.id}",
            assessment_id=str(assessment.id)
        )
        
        # Add simple nodes
        nodes = [
            WorkflowNode(
                id="node1",
                name="First Node",
                node_type="test",
                dependencies=[]
            ),
            WorkflowNode(
                id="node2", 
                name="Second Node",
                node_type="test",
                dependencies=["node1"]
            )
        ]
        
        for node in nodes:
            state.add_node(node)
        
        return state
    
    async def execute_node(self, node, state):
        """Execute a test node."""
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "node_id": node.id,
            "result": f"Completed {node.name}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class TestWorkflowState:
    """Test workflow state functionality."""
    
    def test_workflow_state_creation(self):
        """Test creating workflow state."""
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        assert state.workflow_id == "test_workflow"
        assert state.assessment_id == "test_assessment"
        assert state.status == WorkflowStatus.PENDING
        assert state.progress_percentage == 0.0
        assert len(state.nodes) == 0
    
    def test_add_nodes(self):
        """Test adding nodes to workflow state."""
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        node = WorkflowNode(
            id="test_node",
            name="Test Node",
            node_type="test"
        )
        
        state.add_node(node)
        
        assert len(state.nodes) == 1
        assert state.get_node("test_node") == node
    
    def test_get_ready_nodes(self):
        """Test getting ready nodes."""
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        # Add nodes with dependencies
        node1 = WorkflowNode(id="node1", name="Node 1", node_type="test")
        node2 = WorkflowNode(id="node2", name="Node 2", node_type="test", dependencies=["node1"])
        node3 = WorkflowNode(id="node3", name="Node 3", node_type="test", dependencies=["node1", "node2"])
        
        state.add_node(node1)
        state.add_node(node2)
        state.add_node(node3)
        
        # Initially, only node1 should be ready
        ready_nodes = state.get_ready_nodes()
        assert len(ready_nodes) == 1
        assert ready_nodes[0].id == "node1"
        
        # Complete node1
        node1.status = NodeStatus.COMPLETED
        ready_nodes = state.get_ready_nodes()
        assert len(ready_nodes) == 1
        assert ready_nodes[0].id == "node2"
        
        # Complete node2
        node2.status = NodeStatus.COMPLETED
        ready_nodes = state.get_ready_nodes()
        assert len(ready_nodes) == 1
        assert ready_nodes[0].id == "node3"
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        # Add 4 nodes
        for i in range(4):
            node = WorkflowNode(id=f"node{i}", name=f"Node {i}", node_type="test")
            state.add_node(node)
        
        # Initially 0% progress
        assert state.progress_percentage == 0.0
        
        # Complete 2 nodes (50%)
        state.nodes["node0"].status = NodeStatus.COMPLETED
        state.nodes["node1"].status = NodeStatus.COMPLETED
        assert state.progress_percentage == 50.0
        
        # Complete all nodes (100%)
        state.nodes["node2"].status = NodeStatus.COMPLETED
        state.nodes["node3"].status = NodeStatus.COMPLETED
        assert state.progress_percentage == 100.0
        assert state.is_complete() is True


class TestWorkflowNode:
    """Test workflow node functionality."""
    
    def test_node_creation(self):
        """Test creating workflow node."""
        node = WorkflowNode(
            id="test_node",
            name="Test Node",
            node_type="agent",
            config={"timeout": 300},
            dependencies=["dep1", "dep2"]
        )
        
        assert node.id == "test_node"
        assert node.name == "Test Node"
        assert node.node_type == "agent"
        assert node.config["timeout"] == 300
        assert len(node.dependencies) == 2
        assert node.status == NodeStatus.PENDING
    
    def test_node_lifecycle(self):
        """Test node execution lifecycle."""
        node = WorkflowNode(
            id="test_node",
            name="Test Node",
            node_type="test"
        )
        
        # Initially pending
        assert node.status == NodeStatus.PENDING
        assert node.started_at is None
        assert node.completed_at is None
        
        # Mark as started
        node.mark_started()
        assert node.status == NodeStatus.RUNNING
        assert node.started_at is not None
        
        # Mark as completed
        result = {"success": True}
        node.mark_completed(result)
        assert node.status == NodeStatus.COMPLETED
        assert node.result == result
        assert node.completed_at is not None
        assert node.execution_time is not None
        assert node.execution_time > 0
    
    def test_node_failure(self):
        """Test node failure handling."""
        node = WorkflowNode(
            id="test_node",
            name="Test Node",
            node_type="test"
        )
        
        node.mark_started()
        node.mark_failed("Test error")
        
        assert node.status == NodeStatus.FAILED
        assert node.error == "Test error"
        assert node.completed_at is not None


class TestWorkflowManager:
    """Test workflow manager functionality."""
    
    @pytest.mark.asyncio
    async def test_register_workflow(self):
        """Test registering workflows."""
        manager = WorkflowManager()
        workflow = MockWorkflow()
        
        manager.register_workflow(workflow)
        
        assert workflow.workflow_id in manager.workflow_definitions
        assert manager.workflow_definitions[workflow.workflow_id] == workflow
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing a complete workflow."""
        manager = WorkflowManager()
        workflow = MockWorkflow()
        manager.register_workflow(workflow)
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment_123"
        
        # Execute workflow
        result = await manager.execute_workflow(
            workflow.workflow_id,
            mock_assessment
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.assessment_id == "test_assessment_123"
        assert result.node_count == 2
        assert result.completed_nodes == 2
        assert result.failed_nodes == 0
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_workflow_not_found(self):
        """Test executing non-existent workflow."""
        manager = WorkflowManager()
        
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment"
        
        result = await manager.execute_workflow(
            "nonexistent_workflow",
            mock_assessment
        )
        
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error.lower()


class TestAssessmentWorkflow:
    """Test assessment workflow functionality."""
    
    @pytest.mark.asyncio
    async def test_workflow_definition(self):
        """Test assessment workflow definition."""
        workflow = AssessmentWorkflow()
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment_123"
        mock_assessment.dict = Mock(return_value={"id": "test_assessment_123"})
        
        # Define workflow
        state = await workflow.define_workflow(mock_assessment)
        
        assert isinstance(state, WorkflowState)
        assert state.assessment_id == "test_assessment_123"
        assert len(state.nodes) > 0
        
        # Check that we have expected nodes
        node_ids = list(state.nodes.keys())
        assert "data_validation" in node_ids
        assert "cto_analysis" in node_ids
        assert "cloud_engineer_analysis" in node_ids
        assert "research_analysis" in node_ids
        assert "recommendation_synthesis" in node_ids
        assert "report_generation" in node_ids
    
    @pytest.mark.asyncio
    async def test_agent_node_execution(self):
        """Test executing agent nodes."""
        workflow = AssessmentWorkflow()
        
        # Create mock state
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        # Create agent node
        node = WorkflowNode(
            id="test_agent_node",
            name="Test Agent Node",
            node_type="agent",
            config={
                "agent_role": AgentRole.CTO,
                "operation": "analyze",
                "timeout": 60
            }
        )
        
        # Execute node
        result = await workflow.execute_node(node, state)
        
        assert isinstance(result, dict)
        assert "agent_role" in result
        assert result["agent_role"] == "cto"
        assert "recommendations" in result
        assert "confidence_score" in result
    
    @pytest.mark.asyncio
    async def test_synthesis_node_execution(self):
        """Test executing synthesis nodes."""
        workflow = AssessmentWorkflow()
        
        # Create mock state with agent results
        state = WorkflowState(
            workflow_id="test_workflow",
            assessment_id="test_assessment"
        )
        
        # Add mock node results
        state.node_results["cto_analysis"] = {
            "recommendations": [{"category": "strategy", "title": "Test Strategy"}],
            "confidence_score": 0.9
        }
        state.node_results["cloud_engineer_analysis"] = {
            "recommendations": [{"category": "technical", "title": "Test Technical"}],
            "confidence_score": 0.8
        }
        
        # Create synthesis node
        node = WorkflowNode(
            id="synthesis_node",
            name="Synthesis Node",
            node_type="synthesis",
            config={"operation": "synthesize_recommendations"},
            dependencies=["cto_analysis", "cloud_engineer_analysis"]
        )
        
        # Execute node
        result = await workflow.execute_node(node, state)
        
        assert isinstance(result, dict)
        assert "total_recommendations" in result
        assert "categorized_recommendations" in result
        assert "overall_confidence" in result
        assert result["total_recommendations"] == 2


class TestAgentOrchestrator:
    """Test agent orchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        config = OrchestrationConfig(
            max_parallel_agents=2,
            agent_timeout_seconds=120
        )
        
        orchestrator = AgentOrchestrator(config)
        
        assert orchestrator.config.max_parallel_agents == 2
        assert orchestrator.config.agent_timeout_seconds == 120
    
    @pytest.mark.asyncio
    async def test_orchestrate_assessment(self):
        """Test orchestrating multiple agents."""
        orchestrator = AgentOrchestrator()
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment_123"
        
        # Define agent roles
        agent_roles = [AgentRole.CTO, AgentRole.CLOUD_ENGINEER, AgentRole.RESEARCH]
        
        # Orchestrate assessment
        result = await orchestrator.orchestrate_assessment(
            mock_assessment,
            agent_roles
        )
        
        assert isinstance(result, OrchestrationResult)
        assert result.assessment_id == "test_assessment_123"
        assert result.total_agents == 3
        assert result.successful_agents > 0
        assert len(result.agent_results) == 3
        assert len(result.synthesized_recommendations) > 0
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_parallel_execution_limit(self):
        """Test parallel execution limits."""
        config = OrchestrationConfig(max_parallel_agents=2)
        orchestrator = AgentOrchestrator(config)
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment"
        
        # Test with more agents than the limit
        agent_roles = [
            AgentRole.CTO,
            AgentRole.CLOUD_ENGINEER,
            AgentRole.RESEARCH,
            AgentRole.MLOPS
        ]
        
        start_time = datetime.now()
        result = await orchestrator.orchestrate_assessment(
            mock_assessment,
            agent_roles
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Should complete successfully
        assert result.total_agents == 4
        assert result.successful_agents == 4
        
        # Should take longer due to concurrency limit
        # (This is a rough check - in practice you'd need more precise timing)
        assert execution_time > 1.0  # Should take at least 1 second due to batching
    
    @pytest.mark.asyncio
    async def test_result_synthesis(self):
        """Test synthesizing agent results."""
        orchestrator = AgentOrchestrator()
        
        # Create mock agent results
        agent_results = {
            "cto": AgentResult(
                agent_name="cto_agent",
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {"type": "strategic", "title": "Strategy 1"},
                    {"type": "strategic", "title": "Strategy 2"}
                ]
            ),
            "cloud_engineer": AgentResult(
                agent_name="cloud_engineer_agent", 
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {"type": "technical", "title": "Technical 1"}
                ]
            )
        }
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment"
        
        # Synthesize results
        synthesized = await orchestrator._synthesize_agent_results(
            agent_results,
            mock_assessment
        )
        
        assert len(synthesized) == 2  # Two categories: strategic and technical
        
        # Check strategic category (should be synthesized due to multiple recs)
        strategic_rec = next(r for r in synthesized if r["type"] == "strategic")
        assert "individual_recommendations" in strategic_rec
        assert len(strategic_rec["individual_recommendations"]) == 2
        
        # Check technical category (single recommendation)
        technical_rec = next(r for r in synthesized if r["type"] == "technical")
        assert technical_rec["title"] == "Technical 1"
    
    def test_orchestration_tracking(self):
        """Test orchestration tracking."""
        orchestrator = AgentOrchestrator()
        
        # Initially no active orchestrations
        assert len(orchestrator.list_active_orchestrations()) == 0
        
        # Add mock orchestration
        orchestration_id = "test_orchestration"
        orchestrator.active_orchestrations[orchestration_id] = {
            "assessment_id": "test_assessment",
            "status": "running",
            "start_time": datetime.now(timezone.utc)
        }
        
        # Should show active orchestration
        active = orchestrator.list_active_orchestrations()
        assert len(active) == 1
        assert active[0]["status"] == "running"
        
        # Get specific orchestration status
        status = orchestrator.get_orchestration_status(orchestration_id)
        assert status is not None
        assert status["status"] == "running"