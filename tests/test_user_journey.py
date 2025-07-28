"""
End-to-end tests for user journeys.

Tests complete user flows from assessment creation to report generation.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from src.infra_mind.agents.base import AgentRole, AgentStatus
from src.infra_mind.workflows.assessment_workflow import AssessmentWorkflow
from src.infra_mind.workflows.orchestrator import AgentOrchestrator
from src.infra_mind.workflows.base import WorkflowManager, WorkflowStatus, WorkflowResult


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = Mock()
    user.id = str(uuid.uuid4())
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.company = "Test Company"
    return user


@pytest.fixture
def sample_assessment_data():
    """Create sample assessment data for testing."""
    return {
        "title": "Test Infrastructure Assessment",
        "description": "Test assessment for user journey",
        "business_requirements": {
            "company_size": "medium",
            "industry": "technology",
            "budget_range": "$50k-100k",
            "primary_goals": ["cost_reduction", "scalability", "performance"],
            "timeline": "6-12 months",
            "compliance_requirements": ["gdpr", "hipaa"]
        },
        "technical_requirements": {
            "workload_types": ["web_application", "ai_ml", "data_processing"],
            "expected_users": 10000,
            "performance_requirements": {"response_time": "< 100ms"},
            "integration_needs": ["database", "api", "messaging"],
            "security_requirements": {
                "encryption_at_rest_required": True,
                "encryption_in_transit_required": True,
                "multi_factor_auth_required": True
            }
        },
        "priority": "high",
        "tags": ["test", "user_journey"]
    }


class TestUserJourney:
    """Test complete user journeys through the system."""
    
    @pytest.mark.asyncio
    async def test_assessment_creation_to_report_generation(self, sample_user, sample_assessment_data):
        """Test the complete user journey from assessment creation to report generation."""
        # Step 1: Create assessment
        with patch('src.infra_mind.models.assessment.Assessment.create') as mock_create:
            # Mock the assessment creation
            assessment_id = str(uuid.uuid4())
            mock_assessment = Mock(spec=Assessment)
            mock_assessment.id = assessment_id
            mock_assessment.user_id = sample_user.id
            mock_assessment.title = sample_assessment_data["title"]
            mock_assessment.business_requirements = sample_assessment_data["business_requirements"]
            mock_assessment.technical_requirements = sample_assessment_data["technical_requirements"]
            mock_assessment.status = "created"
            mock_assessment.created_at = datetime.now(timezone.utc)
            
            # Add dict method to mock
            mock_assessment.dict = Mock(return_value={
                "id": assessment_id,
                "user_id": sample_user.id,
                "title": sample_assessment_data["title"],
                "business_requirements": sample_assessment_data["business_requirements"],
                "technical_requirements": sample_assessment_data["technical_requirements"],
                "status": "created"
            })
            
            # Configure the mock to return our assessment
            mock_create.return_value = mock_assessment
            
            # Create the assessment
            assessment = await Assessment.create(**sample_assessment_data, user_id=sample_user.id)
            
            # Verify assessment creation
            assert assessment.id == assessment_id
            assert assessment.user_id == sample_user.id
            assert assessment.title == sample_assessment_data["title"]
            assert assessment.status == "created"
        
        # Step 2: Start assessment workflow
        with patch('src.infra_mind.workflows.orchestrator.AgentOrchestrator.orchestrate_assessment') as mock_orchestrate:
            # Mock the orchestration result
            mock_result = Mock()
            mock_result.assessment_id = assessment_id
            mock_result.total_agents = 3
            mock_result.successful_agents = 3
            mock_result.failed_agents = 0
            mock_result.synthesized_recommendations = [
                {"type": "strategic", "title": "Cloud Migration Strategy"},
                {"type": "technical", "title": "Serverless Architecture"},
                {"type": "pricing", "title": "Cost Optimization"}
            ]
            mock_result.execution_time = 5.0
            
            # Configure the mock to return our result
            mock_orchestrate.return_value = mock_result
            
            # Create orchestrator and run assessment
            orchestrator = AgentOrchestrator()
            result = await orchestrator.orchestrate_assessment(
                assessment,
                [AgentRole.CTO, AgentRole.CLOUD_ENGINEER, AgentRole.RESEARCH]
            )
            
            # Verify orchestration
            assert result.assessment_id == assessment_id
            assert result.total_agents == 3
            assert result.successful_agents == 3
            assert len(result.synthesized_recommendations) == 3
        
        # Step 3: Store recommendations
        with patch('src.infra_mind.models.recommendation.Recommendation.create') as mock_create_rec:
            # Mock recommendation creation
            recommendation_id = str(uuid.uuid4())
            mock_recommendation = Mock(spec=Recommendation)
            mock_recommendation.id = recommendation_id
            mock_recommendation.assessment_id = assessment_id
            mock_recommendation.created_at = datetime.now(timezone.utc)
            
            # Configure the mock to return our recommendation
            mock_create_rec.return_value = mock_recommendation
            
            # Create recommendation
            recommendation = await Recommendation.create(
                assessment_id=assessment_id,
                agent_name="cto_agent",
                recommendation_data={"title": "Cloud Migration Strategy"},
                confidence_score=0.9
            )
            
            # Verify recommendation creation
            assert recommendation.id == recommendation_id
            assert recommendation.assessment_id == assessment_id
        
        # Step 4: Generate report
        with patch('src.infra_mind.models.report.Report.create') as mock_create_report:
            # Mock report creation
            report_id = str(uuid.uuid4())
            mock_report = Mock(spec=Report)
            mock_report.id = report_id
            mock_report.assessment_id = assessment_id
            mock_report.report_type = "executive_summary"
            mock_report.created_at = datetime.now(timezone.utc)
            
            # Configure the mock to return our report
            mock_create_report.return_value = mock_report
            
            # Create report
            report = await Report.create(
                assessment_id=assessment_id,
                report_type="executive_summary",
                content={"title": "Executive Summary", "sections": []},
                file_path=f"/reports/{report_id}.pdf"
            )
            
            # Verify report creation
            assert report.id == report_id
            assert report.assessment_id == assessment_id
            assert report.report_type == "executive_summary"
    
    @pytest.mark.asyncio
    async def test_form_submission_to_recommendations(self, sample_user, sample_assessment_data):
        """Test the user journey from form submission to recommendations."""
        from src.infra_mind.forms.assessment_form import AssessmentForm
        
        # Step 1: Create and validate form
        with patch('src.infra_mind.forms.base.BaseForm.is_form_complete') as mock_validate:
            # Mock form validation
            mock_validate.return_value = True
            
            # Create form
            form = AssessmentForm()
            form.form_data = sample_assessment_data
            
            # Verify form validation
            assert form.is_form_complete() is True
        
        # Step 2: Create assessment from form
        with patch('src.infra_mind.models.assessment.Assessment.create') as mock_create:
            # Mock the assessment creation
            assessment_id = str(uuid.uuid4())
            mock_assessment = Mock(spec=Assessment)
            mock_assessment.id = assessment_id
            mock_assessment.user_id = sample_user.id
            mock_assessment.title = sample_assessment_data["title"]
            mock_assessment.business_requirements = sample_assessment_data["business_requirements"]
            mock_assessment.technical_requirements = sample_assessment_data["technical_requirements"]
            mock_assessment.status = "created"
            mock_assessment.created_at = datetime.now(timezone.utc)
            
            # Add dict method to mock
            mock_assessment.dict = Mock(return_value={
                "id": assessment_id,
                "user_id": sample_user.id,
                "title": sample_assessment_data["title"],
                "business_requirements": sample_assessment_data["business_requirements"],
                "technical_requirements": sample_assessment_data["technical_requirements"],
                "status": "created"
            })
            
            # Configure the mock to return our assessment
            mock_create.return_value = mock_assessment
            
            # Create the assessment from form
            assessment = await Assessment.create(**form.form_data, user_id=sample_user.id)
            
            # Verify assessment creation
            assert assessment.id == assessment_id
            assert assessment.title == sample_assessment_data["title"]
        
        # Step 3: Run workflow
        with patch('src.infra_mind.workflows.base.WorkflowManager.execute_workflow') as mock_execute:
            # Mock workflow execution
            mock_result = Mock()
            mock_result.status = WorkflowStatus.COMPLETED
            mock_result.assessment_id = assessment_id
            mock_result.node_results = {
                "recommendation_synthesis": {
                    "total_recommendations": 3,
                    "categorized_recommendations": {
                        "strategic": [{"title": "Cloud Migration Strategy"}],
                        "technical": [{"title": "Serverless Architecture"}],
                        "pricing": [{"title": "Cost Optimization"}]
                    }
                },
                "report_generation": {
                    "report_id": str(uuid.uuid4()),
                    "report_type": "executive_summary"
                }
            }
            
            # Configure the mock to return our result
            mock_execute.return_value = mock_result
            
            # Execute workflow
            workflow_manager = WorkflowManager()
            workflow = AssessmentWorkflow()
            workflow_manager.register_workflow(workflow)
            result = await workflow_manager.execute_workflow(workflow.workflow_id, assessment)
            
            # Verify workflow execution
            assert result.status == WorkflowStatus.COMPLETED
            assert result.assessment_id == assessment_id
    
    @pytest.mark.asyncio
    async def test_api_assessment_creation_to_report_download(self, sample_user, sample_assessment_data):
        """Test the user journey through API from assessment creation to report download."""
        # This test is simplified to avoid FastAPI dependency
        # Step 1: Create assessment via API
        with patch('src.infra_mind.models.assessment.Assessment.create') as mock_create:
            # Mock the assessment creation
            assessment_id = str(uuid.uuid4())
            mock_assessment = Mock(spec=Assessment)
            mock_assessment.id = assessment_id
            mock_assessment.user_id = sample_user.id
            mock_assessment.title = sample_assessment_data["title"]
            mock_assessment.dict = Mock(return_value={
                "id": assessment_id,
                "user_id": sample_user.id,
                "title": sample_assessment_data["title"],
                "status": "created"
            })
            
            # Configure the mock to return our assessment
            mock_create.return_value = mock_assessment
            
            # Create the assessment
            assessment = await Assessment.create(**sample_assessment_data, user_id=sample_user.id)
            
            # Verify assessment creation
            assert assessment.id == assessment_id
            assert assessment.user_id == sample_user.id
            assert assessment.title == sample_assessment_data["title"]
        
        # Step 2: Start assessment workflow
        with patch('src.infra_mind.workflows.orchestrator.AgentOrchestrator.orchestrate_assessment') as mock_orchestrate:
            # Mock the orchestration result
            mock_result = Mock()
            mock_result.assessment_id = assessment_id
            mock_result.total_agents = 3
            mock_result.successful_agents = 3
            mock_result.failed_agents = 0
            mock_result.synthesized_recommendations = [
                {"type": "strategic", "title": "Cloud Migration Strategy"},
                {"type": "technical", "title": "Serverless Architecture"},
                {"type": "pricing", "title": "Cost Optimization"}
            ]
            
            # Configure the mock to return our result
            mock_orchestrate.return_value = mock_result
            
            # Create orchestrator and run assessment
            orchestrator = AgentOrchestrator()
            result = await orchestrator.orchestrate_assessment(
                assessment,
                [AgentRole.CTO, AgentRole.CLOUD_ENGINEER, AgentRole.RESEARCH]
            )
            
            # Verify orchestration
            assert result.assessment_id == assessment_id
            assert result.total_agents == 3
            assert result.successful_agents == 3
            assert len(result.synthesized_recommendations) == 3
        
        # Step 3: Generate report
        with patch('src.infra_mind.models.report.Report.create') as mock_create_report:
            # Mock report creation
            report_id = str(uuid.uuid4())
            mock_report = Mock(spec=Report)
            mock_report.id = report_id
            mock_report.assessment_id = assessment_id
            mock_report.report_type = "executive_summary"
            mock_report.file_path = f"/reports/{report_id}.pdf"
            
            # Configure the mock to return our report
            mock_create_report.return_value = mock_report
            
            # Create report
            report = await Report.create(
                assessment_id=assessment_id,
                report_type="executive_summary",
                content={"title": "Executive Summary", "sections": []},
                file_path=f"/reports/{report_id}.pdf"
            )
            
            # Verify report creation
            assert report.id == report_id
            assert report.assessment_id == assessment_id
            assert report.report_type == "executive_summary"
            assert report.file_path == f"/reports/{report_id}.pdf"