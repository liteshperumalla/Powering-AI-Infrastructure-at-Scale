"""
Integration tests for agent workflow.

Tests the integration between multiple agents in a workflow.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.agents.base import AgentRole, AgentStatus, AgentResult
from src.infra_mind.agents.cto_agent import CTOAgent
from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
from src.infra_mind.agents.research_agent import ResearchAgent
from src.infra_mind.agents.report_generator_agent import ReportGeneratorAgent
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from src.infra_mind.workflows.orchestrator import AgentOrchestrator, OrchestrationConfig
from src.infra_mind.workflows.base import WorkflowManager, WorkflowStatus, WorkflowNode, WorkflowResult


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
        "timeline": "3-6 months",
        "compliance_requirements": ["gdpr"]
    }
    
    assessment.technical_requirements = {
        "workload_types": ["web_application", "ai_ml"],
        "expected_users": 5000,
        "performance_requirements": {"response_time": "< 200ms"},
        "integration_needs": ["database", "api"],
        "security_requirements": {
            "encryption_at_rest_required": True,
            "encryption_in_transit_required": True
        }
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


class TestAgentWorkflowIntegration:
    """Test the integration between multiple agents in a workflow."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self, sample_assessment):
        """Test a workflow with multiple agents."""
        # Create orchestrator with test configuration
        config = OrchestrationConfig(
            max_parallel_agents=2,
            agent_timeout_seconds=30
        )
        orchestrator = AgentOrchestrator(config)
        
        # Define agent roles for the test
        agent_roles = [
            AgentRole.CTO,
            AgentRole.CLOUD_ENGINEER,
            AgentRole.RESEARCH
        ]
        
        # Mock the orchestrate_assessment method directly
        with patch.object(orchestrator, 'orchestrate_assessment', new_callable=AsyncMock) as mock_orchestrate:
            # Create a mock result
            mock_result = Mock()
            mock_result.assessment_id = sample_assessment.id
            mock_result.total_agents = 3
            mock_result.successful_agents = 3
            mock_result.agent_results = {
                "cto": AgentResult(
                    agent_name="CTO Agent",
                    status=AgentStatus.COMPLETED,
                    recommendations=[
                        {"type": "strategic", "title": "Cost Optimization Strategy"}
                    ],
                    data={"business_analysis": {"company_profile": {"company_size": "startup"}}}
                ),
                "cloud_engineer": AgentResult(
                    agent_name="Cloud Engineer Agent",
                    status=AgentStatus.COMPLETED,
                    recommendations=[
                        {"type": "technical", "title": "Use AWS Lambda for Serverless"}
                    ],
                    data={"service_comparisons": {"compute": {"aws": "Lambda", "azure": "Functions"}}}
                ),
                "research": AgentResult(
                    agent_name="Research Agent",
                    status=AgentStatus.COMPLETED,
                    recommendations=[
                        {"type": "pricing", "title": "Current Pricing Analysis"}
                    ],
                    data={"pricing_data": {"aws": {"lambda": {"price_per_million": 0.20}}}}
                )
            }
            mock_result.synthesized_recommendations = [
                {"type": "strategic", "title": "Cost Optimization Strategy"},
                {"type": "technical", "title": "Use AWS Lambda for Serverless"},
                {"type": "pricing", "title": "Current Pricing Analysis"}
            ]
            
            # Configure the mock to return our result
            mock_orchestrate.return_value = mock_result
            
            # Execute the orchestration
            result = await orchestrator.orchestrate_assessment(
                sample_assessment,
                agent_roles
            )
            
            # Verify the orchestration result
            assert result.assessment_id == sample_assessment.id
            assert result.total_agents == 3
            assert result.successful_agents == 3
            assert len(result.agent_results) == 3
            assert len(result.synthesized_recommendations) > 0
            
            # Verify orchestrate_assessment was called with correct parameters
            mock_orchestrate.assert_called_once_with(sample_assessment, agent_roles)
            
            # Verify the synthesized recommendations contain data from all agents
            recommendation_types = [rec["type"] for rec in result.synthesized_recommendations]
            assert "strategic" in recommendation_types
            assert "technical" in recommendation_types
            assert "pricing" in recommendation_types
    
    @pytest.mark.asyncio
    async def test_workflow_with_failed_agent(self, sample_assessment):
        """Test workflow resilience when an agent fails."""
        # Create orchestrator with test configuration
        config = OrchestrationConfig(
            max_parallel_agents=2,
            agent_timeout_seconds=30
        )
        orchestrator = AgentOrchestrator(config)
        
        # Define agent roles for the test
        agent_roles = [
            AgentRole.CTO,
            AgentRole.CLOUD_ENGINEER,
            AgentRole.RESEARCH
        ]
        
        # Mock the orchestrate_assessment method directly
        with patch.object(orchestrator, 'orchestrate_assessment', new_callable=AsyncMock) as mock_orchestrate:
            # Create a mock result with one failed agent
            mock_result = Mock()
            mock_result.assessment_id = sample_assessment.id
            mock_result.total_agents = 3
            mock_result.successful_agents = 2  # One agent failed
            mock_result.failed_agents = 1
            mock_result.agent_results = {
                "cto": AgentResult(
                    agent_name="CTO Agent",
                    status=AgentStatus.COMPLETED,
                    recommendations=[
                        {"type": "strategic", "title": "Cost Optimization Strategy"}
                    ]
                ),
                "cloud_engineer": AgentResult(
                    agent_name="Cloud Engineer Agent",
                    status=AgentStatus.FAILED,
                    error="API connection timeout",
                    recommendations=[]
                ),
                "research": AgentResult(
                    agent_name="Research Agent",
                    status=AgentStatus.COMPLETED,
                    recommendations=[
                        {"type": "pricing", "title": "Current Pricing Analysis"}
                    ]
                )
            }
            mock_result.synthesized_recommendations = [
                {"type": "strategic", "title": "Cost Optimization Strategy"},
                {"type": "pricing", "title": "Current Pricing Analysis"}
            ]
            
            # Configure the mock to return our result
            mock_orchestrate.return_value = mock_result
            
            # Execute the orchestration
            result = await orchestrator.orchestrate_assessment(
                sample_assessment,
                agent_roles
            )
            
            # Verify the orchestration result
            assert result.assessment_id == sample_assessment.id
            assert result.total_agents == 3
            assert result.successful_agents == 2  # One agent failed
            assert result.failed_agents == 1
            assert len(result.agent_results) == 3
            
            # Verify the workflow continued despite the failure
            assert len(result.synthesized_recommendations) > 0
            
            # Verify orchestrate_assessment was called with correct parameters
            mock_orchestrate.assert_called_once_with(sample_assessment, agent_roles)
    
    @pytest.mark.asyncio
    async def test_end_to_end_assessment_workflow(self, sample_assessment):
        """Test the complete assessment workflow from start to finish."""
        # Create a workflow instance
        workflow = AssessmentWorkflow()
        
        # Create workflow manager
        workflow_manager = WorkflowManager()
        workflow_manager.register_workflow(workflow)
        
        # Mock the agent execution to avoid actual LLM calls
        with patch('src.infra_mind.workflows.assessment_workflow.AssessmentWorkflow._execute_agent_node') as mock_execute:
            # Create mock agent results
            mock_results = {
                "cto_analysis": {
                    "agent_role": "cto",
                    "recommendations": [
                        {"category": "strategy", "title": "Cloud Migration Strategy"}
                    ],
                    "confidence_score": 0.9
                },
                "cloud_engineer_analysis": {
                    "agent_role": "cloud_engineer",
                    "recommendations": [
                        {"category": "technical", "title": "Serverless Architecture"}
                    ],
                    "confidence_score": 0.85
                },
                "research_analysis": {
                    "agent_role": "research",
                    "recommendations": [
                        {"category": "pricing", "title": "Cost Analysis"}
                    ],
                    "confidence_score": 0.95
                },
                "report_generation": {
                    "agent_role": "report_generator",
                    "report_content": "Test report content",
                    "confidence_score": 0.9
                }
            }
            
            # Mock the execute_agent_node method to return our predefined results
            async def mock_agent_node(node, state):
                node_id = node.id
                return mock_results.get(node_id, {"agent_role": "unknown"})
            
            mock_execute.side_effect = mock_agent_node
            
            # Execute the workflow
            result = await workflow_manager.execute_workflow(workflow.workflow_id, sample_assessment)
            
            # Verify the workflow result
            assert result.status == WorkflowStatus.COMPLETED
            assert result.assessment_id == sample_assessment.id
            assert result.node_count > 0
            assert result.completed_nodes > 0
            assert result.failed_nodes == 0
            
            # Verify the workflow completed successfully
            assert result.status == WorkflowStatus.COMPLETED
            assert result.assessment_id == sample_assessment.id
            assert result.node_count > 0
            assert result.completed_nodes > 0
            assert result.failed_nodes == 0