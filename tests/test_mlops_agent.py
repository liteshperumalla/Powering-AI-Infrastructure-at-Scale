"""
Tests for MLOps Agent.

This module contains comprehensive tests for the MLOps Agent functionality,
including ML pipeline optimization, platform recommendations, and CI/CD design.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.infra_mind.agents.mlops_agent import MLOpsAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestMLOpsAgent:
    """Test cases for MLOps Agent."""
    
    @pytest.fixture
    def mlops_agent(self):
        """Create MLOps Agent for testing."""
        config = AgentConfig(
            name="Test MLOps Agent",
            role=AgentRole.MLOPS,
            tools_enabled=["cloud_api", "calculator", "data_processor"],
            metrics_enabled=False  # Disable metrics for testing
        )
        return MLOpsAgent(config)
    
    @pytest.fixture
    def sample_assessment(self):
        """Create sample assessment for testing."""
        # Create a mock assessment object for testing
        assessment = Mock()
        assessment.user_id = "test_user_123"
        assessment.title = "Test MLOps Assessment"
        assessment.description = "Test assessment for MLOps agent testing"
        assessment.business_requirements = {
            "company_size": "medium",
            "industry": "technology",
            "budget_range": "$50k-100k",
            "primary_goals": ["innovation", "scalability"]
        }
        assessment.technical_requirements = {
            "workload_types": ["ai_ml", "machine_learning"],
            "expected_users": 5000,
            "performance_requirements": {
                "latency": "low",
                "throughput": "high"
            }
        }
        assessment.id = "test_assessment_id"
        
        # Mock the dict() method
        assessment.dict.return_value = {
            "user_id": assessment.user_id,
            "title": assessment.title,
            "description": assessment.description,
            "business_requirements": assessment.business_requirements,
            "technical_requirements": assessment.technical_requirements
        }
        
        return assessment
    
    def test_mlops_agent_initialization(self, mlops_agent):
        """Test MLOps Agent initialization."""
        assert mlops_agent.name == "Test MLOps Agent"
        assert mlops_agent.role == AgentRole.MLOPS
        assert mlops_agent.status == AgentStatus.IDLE
        assert "kubeflow" in mlops_agent.mlops_platforms
        assert "real_time_serving" in mlops_agent.deployment_patterns
        assert "model_training" in mlops_agent.ml_lifecycle_stages
    
    def test_mlops_agent_capabilities(self, mlops_agent):
        """Test MLOps Agent capabilities."""
        capabilities = mlops_agent.get_capabilities()
        
        assert any("mlops" in cap.lower() for cap in capabilities)
        assert any("model" in cap.lower() for cap in capabilities)
        assert len(capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_mlops_agent_execution(self, mlops_agent, sample_assessment):
        """Test MLOps Agent execution."""
        # Mock tool responses
        with patch.object(mlops_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {
                "insights": ["ML workloads detected", "High performance requirements"],
                "monthly_cost": 5000,
                "roi_percentage": 150
            }
            
            result = await mlops_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert result.agent_name == "Test MLOps Agent"
            assert len(result.recommendations) > 0
            assert result.execution_time is not None
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_analyze_ml_requirements(self, mlops_agent, sample_assessment):
        """Test ML requirements analysis."""
        await mlops_agent.initialize(sample_assessment)
        
        with patch.object(mlops_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = AsyncMock()
            mock_tool.return_value.is_success = True
            mock_tool.return_value.data = {"insights": ["ML workloads identified"]}
            
            analysis = await mlops_agent._analyze_ml_requirements()
            
            assert "ml_workloads" in analysis
            assert "ml_use_cases" in analysis
            assert "model_complexity" in analysis
            assert "performance_requirements" in analysis
            
            # Check ML workloads detection
            ml_workloads = analysis["ml_workloads"]
            assert any("ml" in workload.lower() for workload in ml_workloads)
    
    @pytest.mark.asyncio
    async def test_assess_ml_maturity(self, mlops_agent, sample_assessment):
        """Test ML maturity assessment."""
        await mlops_agent.initialize(sample_assessment)
        
        maturity = await mlops_agent._assess_ml_maturity()
        
        assert "overall_maturity_score" in maturity
        assert "maturity_level" in maturity
        assert "maturity_indicators" in maturity
        assert "key_gaps" in maturity
        
        # Check maturity score is valid
        score = maturity["overall_maturity_score"]
        assert 0 <= score <= 1
        
        # Check maturity level categorization
        level = maturity["maturity_level"]
        assert level in ["basic", "developing", "intermediate", "advanced"]
    
    @pytest.mark.asyncio
    async def test_recommend_mlops_platforms(self, mlops_agent, sample_assessment):
        """Test MLOps platform recommendations."""
        await mlops_agent.initialize(sample_assessment)
        
        ml_analysis = {
            "ml_use_cases": [{"type": "predictive_analytics", "complexity": "medium"}],
            "model_complexity": {"overall_complexity": "medium"},
            "expected_users": 5000
        }
        
        recommendations = await mlops_agent._recommend_mlops_platforms(ml_analysis)
        
        assert "platform_evaluations" in recommendations
        assert "ranked_platforms" in recommendations
        assert "recommendations" in recommendations
        
        # Check platform evaluations
        evaluations = recommendations["platform_evaluations"]
        assert len(evaluations) > 0
        
        # Check each platform has required fields
        for platform, evaluation in evaluations.items():
            assert "suitability_score" in evaluation
            assert "characteristics" in evaluation
            assert 0 <= evaluation["suitability_score"] <= 1
        
        # Check recommendations are properly ranked
        platform_recs = recommendations["recommendations"]
        if len(platform_recs) > 1:
            assert platform_recs[0]["suitability_score"] >= platform_recs[1]["suitability_score"]
    
    @pytest.mark.asyncio
    async def test_design_ml_cicd_pipeline(self, mlops_agent, sample_assessment):
        """Test ML CI/CD pipeline design."""
        await mlops_agent.initialize(sample_assessment)
        
        ml_analysis = {
            "ml_use_cases": [{"type": "predictive_analytics"}],
            "expected_users": 5000
        }
        platform_recommendations = {
            "recommendations": [{"platform": "mlflow"}]
        }
        
        cicd_design = await mlops_agent._design_ml_cicd_pipeline(ml_analysis, platform_recommendations)
        
        assert "pipeline_stages" in cicd_design
        assert "automation_strategies" in cicd_design
        assert "testing_strategy" in cicd_design
        assert "deployment_pipeline" in cicd_design
        
        # Check pipeline stages
        stages = cicd_design["pipeline_stages"]
        assert len(stages) > 0
        
        stage_names = [stage["stage"] for stage in stages]
        assert "data_validation" in stage_names
        assert "model_training" in stage_names
        assert "model_deployment" in stage_names
        
        # Check testing strategy
        testing = cicd_design["testing_strategy"]
        assert "data_testing" in testing
        assert "model_testing" in testing
        assert "integration_testing" in testing
    
    @pytest.mark.asyncio
    async def test_create_deployment_strategy(self, mlops_agent, sample_assessment):
        """Test deployment strategy creation."""
        await mlops_agent.initialize(sample_assessment)
        
        ml_analysis = {
            "ml_use_cases": [{"type": "predictive_analytics"}],
            "performance_requirements": {"latency_requirement": "low"},
            "expected_users": 5000
        }
        
        deployment = await mlops_agent._create_deployment_strategy(ml_analysis)
        
        assert "deployment_patterns" in deployment
        assert "serving_infrastructure" in deployment
        assert "scaling_strategy" in deployment
        assert "rollout_strategy" in deployment
        
        # Check deployment patterns
        patterns = deployment["deployment_patterns"]
        assert len(patterns) > 0
        
        for pattern in patterns:
            assert "pattern" in pattern
            assert "description" in pattern
            assert "use_case" in pattern
        
        # Check scaling strategy
        scaling = deployment["scaling_strategy"]
        assert "horizontal_scaling" in scaling
        assert "vertical_scaling" in scaling
    
    @pytest.mark.asyncio
    async def test_create_monitoring_plan(self, mlops_agent, sample_assessment):
        """Test monitoring plan creation."""
        await mlops_agent.initialize(sample_assessment)
        
        deployment_strategy = {
            "deployment_patterns": [{"pattern": "real_time_serving"}]
        }
        
        monitoring = await mlops_agent._create_monitoring_plan(deployment_strategy)
        
        assert "monitoring_metrics" in monitoring
        assert "alerting_strategy" in monitoring
        assert "performance_tracking" in monitoring
        assert "drift_detection" in monitoring
        
        # Check monitoring metrics
        metrics = monitoring["monitoring_metrics"]
        assert "model_performance" in metrics
        assert "system_performance" in metrics
        assert "data_quality" in metrics
        assert "business_metrics" in metrics
        
        # Check alerting strategy
        alerting = monitoring["alerting_strategy"]
        assert "critical_alerts" in alerting
        assert "warning_alerts" in alerting
        
        # Verify alert structure
        for alert in alerting["critical_alerts"]:
            assert "metric" in alert
            assert "threshold" in alert
            assert "action" in alert
    
    def test_identify_ml_use_cases(self, mlops_agent):
        """Test ML use case identification."""
        technical_req = {
            "workload_types": ["ai_ml", "machine_learning"],
            "expected_users": 5000
        }
        business_req = {
            "industry": "healthcare"
        }
        
        use_cases = mlops_agent._identify_ml_use_cases(technical_req, business_req)
        
        assert len(use_cases) > 0
        
        for use_case in use_cases:
            assert "type" in use_case
            assert "description" in use_case
            assert "complexity" in use_case
            assert "data_requirements" in use_case
        
        # Check healthcare-specific use case
        use_case_types = [uc["type"] for uc in use_cases]
        assert "medical_diagnosis" in use_case_types or "predictive_analytics" in use_case_types
    
    def test_assess_data_characteristics(self, mlops_agent):
        """Test data characteristics assessment."""
        technical_req = {
            "expected_users": 15000
        }
        
        characteristics = mlops_agent._assess_data_characteristics(technical_req)
        
        assert "volume" in characteristics
        assert "velocity" in characteristics
        assert "variety" in characteristics
        assert "quality_requirements" in characteristics
        
        # Check volume assessment for high user count
        assert characteristics["volume"] == "large"
        assert characteristics["velocity"] == "streaming"
    
    def test_assess_model_complexity(self, mlops_agent):
        """Test model complexity assessment."""
        ml_use_cases = [
            {"complexity": "high"},
            {"complexity": "medium"}
        ]
        data_characteristics = {"volume": "large"}
        
        complexity = mlops_agent._assess_model_complexity(ml_use_cases, data_characteristics)
        
        assert "overall_complexity" in complexity
        assert "compute_requirements" in complexity
        assert "training_time_estimate" in complexity
        assert "model_size_estimate" in complexity
        
        # Check complexity categorization
        assert complexity["overall_complexity"] in ["low", "medium", "high"]
        assert complexity["compute_requirements"] in ["cpu_light", "cpu_intensive", "gpu_required"]
    
    def test_categorize_maturity_level(self, mlops_agent):
        """Test maturity level categorization."""
        assert mlops_agent._categorize_maturity_level(0.9) == "advanced"
        assert mlops_agent._categorize_maturity_level(0.7) == "intermediate"
        assert mlops_agent._categorize_maturity_level(0.5) == "developing"
        assert mlops_agent._categorize_maturity_level(0.2) == "basic"
    
    def test_select_deployment_patterns(self, mlops_agent):
        """Test deployment pattern selection."""
        ml_use_cases = [{"data_requirements": "batch_data"}]
        performance_req = {"latency_requirement": "low"}
        expected_users = 15000
        
        patterns = mlops_agent._select_deployment_patterns(ml_use_cases, performance_req, expected_users)
        
        assert len(patterns) > 0
        
        for pattern in patterns:
            assert "pattern" in pattern
            assert "description" in pattern
            assert "use_case" in pattern
            assert "infrastructure" in pattern
            assert "rationale" in pattern
        
        # Check real-time serving is selected for low latency + high users
        pattern_names = [p["pattern"] for p in patterns]
        assert "real_time_serving" in pattern_names
    
    def test_platform_evaluation_scoring(self, mlops_agent):
        """Test platform evaluation scoring."""
        # Test different platforms get different scores
        platforms = ["kubeflow", "mlflow", "sagemaker"]
        ml_use_cases = [{"type": "predictive_analytics"}]
        model_complexity = {"overall_complexity": "medium"}
        expected_users = 5000
        
        scores = []
        for platform in platforms:
            evaluation = asyncio.run(
                mlops_agent._evaluate_mlops_platform(platform, ml_use_cases, model_complexity, expected_users)
            )
            scores.append(evaluation["suitability_score"])
        
        # Scores should be different and within valid range
        assert len(set(scores)) > 1  # Different scores
        assert all(0 <= score <= 1 for score in scores)  # Valid range
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mlops_agent, sample_assessment):
        """Test error handling in MLOps Agent."""
        # Test with tool failure
        with patch.object(mlops_agent, '_use_tool') as mock_tool:
            mock_tool.side_effect = Exception("Tool failure")
            
            result = await mlops_agent.execute(sample_assessment)
            
            assert result.status == AgentStatus.FAILED
            assert result.error is not None
            assert "Tool failure" in result.error
    
    @pytest.mark.asyncio
    async def test_health_check(self, mlops_agent):
        """Test MLOps Agent health check."""
        health = await mlops_agent.health_check()
        
        assert "agent_name" in health
        assert "status" in health
        assert "role" in health
        assert health["agent_name"] == "Test MLOps Agent"
        assert health["role"] == "mlops"
        assert health["status"] == "idle"
    
    def test_mlops_best_practices_included(self, mlops_agent):
        """Test that MLOps best practices are included."""
        best_practices = mlops_agent.best_practices
        
        assert len(best_practices) > 0
        assert "version_control_for_data_and_models" in best_practices
        assert "automated_testing_for_ml_code" in best_practices
        assert "model_versioning_and_registry" in best_practices
        assert "monitoring_and_alerting" in best_practices
    
    def test_ml_lifecycle_stages_coverage(self, mlops_agent):
        """Test that all ML lifecycle stages are covered."""
        stages = mlops_agent.ml_lifecycle_stages
        
        expected_stages = [
            "data_ingestion", "data_preprocessing", "feature_engineering",
            "model_training", "model_validation", "model_deployment",
            "model_monitoring", "model_retraining"
        ]
        
        for stage in expected_stages:
            assert stage in stages
    
    @pytest.mark.asyncio
    async def test_recommendation_generation(self, mlops_agent, sample_assessment):
        """Test recommendation generation produces valid recommendations."""
        await mlops_agent.initialize(sample_assessment)
        
        # Mock all required data
        ml_analysis = {"ml_use_cases": [{"type": "predictive_analytics"}]}
        maturity_assessment = {"maturity_level": "developing", "key_gaps": ["gap1", "gap2"]}
        platform_recommendations = {"recommendations": [{"platform": "mlflow", "rationale": "test"}]}
        cicd_design = {"pipeline_stages": [{"stage": "training"}]}
        deployment_strategy = {"deployment_patterns": [{"pattern": "real_time_serving", "rationale": "test"}]}
        monitoring_plan = {"monitoring_metrics": {"model_performance": ["accuracy"]}}
        
        recommendations = await mlops_agent._generate_mlops_recommendations(
            ml_analysis, maturity_assessment, platform_recommendations,
            cicd_design, deployment_strategy, monitoring_plan
        )
        
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec
            assert "rationale" in rec
            assert "business_impact" in rec
            assert "timeline" in rec
            assert "investment_required" in rec
            
            # Check priority is valid
            assert rec["priority"] in ["high", "medium", "low"]
            
            # Check category is valid
            assert rec["category"] in [
                "mlops_platform", "cicd_pipeline", "deployment_strategy",
                "monitoring_observability", "maturity_improvement"
            ]


if __name__ == "__main__":
    pytest.main([__file__])