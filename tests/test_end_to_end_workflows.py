"""
End-to-end testing suite for complete user workflows.

Tests complete user journeys from initial assessment through report generation
using real services and realistic data scenarios.
"""

import pytest
import asyncio
import time
import json
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.infra_mind.core.database import db, init_database, close_database
    from src.infra_mind.core.cache import cache_manager
    from src.infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator
    from src.infra_mind.agents.cto_agent import CTOAgent
    from src.infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
    from src.infra_mind.agents.research_agent import ResearchAgent
    from src.infra_mind.agents.report_generator_agent import ReportGeneratorAgent
    from src.infra_mind.models.assessment import Assessment
    from src.infra_mind.models.recommendation import Recommendation
    from src.infra_mind.models.report import Report
    from src.infra_mind.forms.assessment_form import AssessmentForm
    from src.infra_mind.api.app import app
    INTEGRATION_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Some integration modules may not be available for testing")
    INTEGRATION_IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class E2ETestScenario:
    """End-to-end test scenario configuration."""
    name: str
    description: str
    user_profile: Dict[str, Any]
    business_requirements: Dict[str, Any]
    technical_requirements: Dict[str, Any]
    compliance_requirements: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    max_execution_time_seconds: int = 300  # 5 minutes


class EndToEndTestSuite:
    """Comprehensive end-to-end testing suite."""
    
    def __init__(self):
        self.test_scenarios = self._create_test_scenarios()
        self.test_results = {}
        self.orchestrator = None
    
    async def setup_test_environment(self):
        """Set up test environment for E2E testing."""
        try:
            if not INTEGRATION_IMPORTS_AVAILABLE:
                logger.warning("Integration modules not available - using mock setup")
                return
                
            # Initialize database
            await init_database()
            
            # Initialize cache
            await cache_manager.connect()
            
            # Initialize orchestrator
            self.orchestrator = LangGraphOrchestrator()
            
            logger.info("E2E test environment setup completed")
            
        except Exception as e:
            logger.error(f"E2E test environment setup failed: {e}")
            # Don't raise for testing purposes
            pass
    
    async def teardown_test_environment(self):
        """Clean up test environment."""
        try:
            if not INTEGRATION_IMPORTS_AVAILABLE:
                return
                
            # Clean up test data
            await self._cleanup_test_data()
            
            # Close database
            await close_database()
            
            # Disconnect cache
            await cache_manager.disconnect()
            
            logger.info("E2E test environment cleanup completed")
            
        except Exception as e:
            logger.error(f"E2E test environment cleanup failed: {e}")
    
    def _create_test_scenarios(self) -> Dict[str, E2ETestScenario]:
        """Create comprehensive test scenarios."""
        return {
            "small_tech_startup": E2ETestScenario(
                name="small_tech_startup",
                description="Small technology startup moving to cloud",
                user_profile={
                    "company_name": "TechStart Inc",
                    "role": "CTO",
                    "experience_level": "intermediate"
                },
                business_requirements={
                    "industry": "technology",
                    "company_size": "small",
                    "employee_count": 25,
                    "budget_range": "50000-100000",
                    "timeline": "3-6 months",
                    "growth_projection": "high",
                    "current_infrastructure": "on_premise_limited"
                },
                technical_requirements={
                    "workload_types": ["web_application", "api_services"],
                    "expected_users": 10000,
                    "data_volume_gb": 100,
                    "preferred_cloud": "aws",
                    "high_availability": True,
                    "auto_scaling": True,
                    "backup_requirements": "daily"
                },
                compliance_requirements={
                    "frameworks": ["gdpr"],
                    "data_residency": "us",
                    "audit_requirements": "basic"
                },
                expected_outcomes={
                    "min_recommendations": 5,
                    "max_monthly_cost": 5000,
                    "includes_security": True,
                    "includes_monitoring": True,
                    "report_sections": ["executive_summary", "technical_architecture", "cost_analysis"]
                }
            ),
            
            "medium_finance_company": E2ETestScenario(
                name="medium_finance_company",
                description="Medium-sized financial services company with strict compliance",
                user_profile={
                    "company_name": "FinServ Corp",
                    "role": "IT Director",
                    "experience_level": "advanced"
                },
                business_requirements={
                    "industry": "finance",
                    "company_size": "medium",
                    "employee_count": 500,
                    "budget_range": "500000-1000000",
                    "timeline": "6-12 months",
                    "growth_projection": "moderate",
                    "current_infrastructure": "hybrid"
                },
                technical_requirements={
                    "workload_types": ["web_application", "data_processing", "analytics"],
                    "expected_users": 100000,
                    "data_volume_gb": 10000,
                    "preferred_cloud": "azure",
                    "high_availability": True,
                    "disaster_recovery": True,
                    "performance_requirements": "high",
                    "integration_requirements": ["legacy_systems", "third_party_apis"]
                },
                compliance_requirements={
                    "frameworks": ["sox", "pci_dss", "gdpr"],
                    "data_residency": "us",
                    "audit_requirements": "comprehensive",
                    "encryption_requirements": "end_to_end"
                },
                expected_outcomes={
                    "min_recommendations": 10,
                    "max_monthly_cost": 50000,
                    "includes_security": True,
                    "includes_compliance": True,
                    "includes_disaster_recovery": True,
                    "report_sections": ["executive_summary", "technical_architecture", "compliance_analysis", "cost_analysis", "risk_assessment"]
                },
                max_execution_time_seconds=600  # 10 minutes for complex scenario
            ),
            
            "large_healthcare_enterprise": E2ETestScenario(
                name="large_healthcare_enterprise",
                description="Large healthcare enterprise with HIPAA compliance requirements",
                user_profile={
                    "company_name": "HealthCare Systems",
                    "role": "Chief Information Officer",
                    "experience_level": "expert"
                },
                business_requirements={
                    "industry": "healthcare",
                    "company_size": "large",
                    "employee_count": 5000,
                    "budget_range": "1000000-5000000",
                    "timeline": "12-18 months",
                    "growth_projection": "moderate",
                    "current_infrastructure": "on_premise_extensive",
                    "multi_location": True
                },
                technical_requirements={
                    "workload_types": ["web_application", "data_processing", "machine_learning", "iot"],
                    "expected_users": 500000,
                    "data_volume_gb": 100000,
                    "preferred_cloud": "multi_cloud",
                    "high_availability": True,
                    "disaster_recovery": True,
                    "performance_requirements": "critical",
                    "integration_requirements": ["ehr_systems", "medical_devices", "third_party_apis"],
                    "real_time_processing": True
                },
                compliance_requirements={
                    "frameworks": ["hipaa", "hitech", "gdpr"],
                    "data_residency": "us",
                    "audit_requirements": "comprehensive",
                    "encryption_requirements": "end_to_end",
                    "access_controls": "role_based",
                    "data_retention": "7_years"
                },
                expected_outcomes={
                    "min_recommendations": 15,
                    "max_monthly_cost": 200000,
                    "includes_security": True,
                    "includes_compliance": True,
                    "includes_disaster_recovery": True,
                    "includes_multi_cloud": True,
                    "report_sections": ["executive_summary", "technical_architecture", "compliance_analysis", "security_analysis", "cost_analysis", "risk_assessment", "implementation_roadmap"]
                },
                max_execution_time_seconds=900  # 15 minutes for complex scenario
            )
        }
    
    async def run_complete_workflow(self, scenario_name: str) -> Dict[str, Any]:
        """
        Run complete end-to-end workflow for a scenario.
        
        Args:
            scenario_name: Name of the test scenario
            
        Returns:
            Dictionary with test results and metrics
        """
        if scenario_name not in self.test_scenarios:
            raise ValueError(f"Unknown test scenario: {scenario_name}")
        
        scenario = self.test_scenarios[scenario_name]
        test_result = {
            "scenario": scenario_name,
            "start_time": datetime.now(timezone.utc),
            "end_time": None,
            "duration_seconds": 0,
            "success": False,
            "steps_completed": [],
            "steps_failed": [],
            "assessment_id": None,
            "recommendations_count": 0,
            "report_generated": False,
            "errors": [],
            "metrics": {}
        }
        
        logger.info(f"Starting E2E workflow: {scenario_name}")
        
        try:
            # Step 1: Create Assessment
            assessment_result = await self._create_assessment(scenario, test_result)
            if not assessment_result["success"]:
                return test_result
            
            # Step 2: Run Agent Orchestration
            orchestration_result = await self._run_agent_orchestration(scenario, test_result)
            if not orchestration_result["success"]:
                return test_result
            
            # Step 3: Generate Recommendations
            recommendations_result = await self._generate_recommendations(scenario, test_result)
            if not recommendations_result["success"]:
                return test_result
            
            # Step 4: Generate Report
            report_result = await self._generate_report(scenario, test_result)
            if not report_result["success"]:
                return test_result
            
            # Step 5: Validate Results
            validation_result = await self._validate_results(scenario, test_result)
            if not validation_result["success"]:
                return test_result
            
            test_result["success"] = True
            logger.info(f"E2E workflow completed successfully: {scenario_name}")
            
        except Exception as e:
            test_result["errors"].append(f"Workflow execution failed: {str(e)}")
            logger.error(f"E2E workflow failed: {scenario_name} - {e}")
        
        finally:
            test_result["end_time"] = datetime.now(timezone.utc)
            test_result["duration_seconds"] = (test_result["end_time"] - test_result["start_time"]).total_seconds()
            self.test_results[scenario_name] = test_result
        
        return test_result
    
    async def _create_assessment(self, scenario: E2ETestScenario, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create assessment from scenario data."""
        step_name = "create_assessment"
        step_start = time.time()
        
        try:
            # Create unique assessment ID
            assessment_id = f"e2e_test_{scenario.name}_{uuid.uuid4().hex[:8]}"
            
            # Prepare assessment data
            assessment_data = {
                "assessment_id": assessment_id,
                "user_id": f"e2e_user_{scenario.name}",
                "user_profile": scenario.user_profile,
                "business_requirements": scenario.business_requirements,
                "technical_requirements": scenario.technical_requirements,
                "compliance_requirements": scenario.compliance_requirements,
                "status": "in_progress",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Create assessment using form validation
            form = AssessmentForm(assessment_data)
            if not form.is_valid():
                test_result["errors"].append(f"Assessment form validation failed: {form.errors}")
                test_result["steps_failed"].append(step_name)
                return {"success": False}
            
            # Save assessment to database
            if db.database:
                await db.database.assessments.insert_one(assessment_data)
            
            test_result["assessment_id"] = assessment_id
            test_result["steps_completed"].append(step_name)
            test_result["metrics"][f"{step_name}_duration_ms"] = (time.time() - step_start) * 1000
            
            logger.info(f"Assessment created: {assessment_id}")
            return {"success": True, "assessment_id": assessment_id}
            
        except Exception as e:
            test_result["errors"].append(f"Assessment creation failed: {str(e)}")
            test_result["steps_failed"].append(step_name)
            return {"success": False}
    
    async def _run_agent_orchestration(self, scenario: E2ETestScenario, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent orchestration workflow."""
        step_name = "agent_orchestration"
        step_start = time.time()
        
        try:
            assessment_id = test_result["assessment_id"]
            
            # Prepare workflow data
            workflow_data = {
                "assessment_id": assessment_id,
                "business_requirements": scenario.business_requirements,
                "technical_requirements": scenario.technical_requirements,
                "compliance_requirements": scenario.compliance_requirements
            }
            
            # Run orchestration with timeout
            orchestration_timeout = scenario.max_execution_time_seconds - 60  # Reserve 60s for other steps
            
            try:
                result = await asyncio.wait_for(
                    self.orchestrator.run_assessment_workflow(workflow_data),
                    timeout=orchestration_timeout
                )
                
                if result and "agents_executed" in result:
                    test_result["metrics"]["agents_executed"] = len(result["agents_executed"])
                    test_result["metrics"]["agent_execution_times"] = result.get("execution_times", {})
                
                test_result["steps_completed"].append(step_name)
                test_result["metrics"][f"{step_name}_duration_ms"] = (time.time() - step_start) * 1000
                
                logger.info(f"Agent orchestration completed for: {assessment_id}")
                return {"success": True, "result": result}
                
            except asyncio.TimeoutError:
                test_result["errors"].append(f"Agent orchestration timed out after {orchestration_timeout}s")
                test_result["steps_failed"].append(step_name)
                return {"success": False}
            
        except Exception as e:
            test_result["errors"].append(f"Agent orchestration failed: {str(e)}")
            test_result["steps_failed"].append(step_name)
            return {"success": False}
    
    async def _generate_recommendations(self, scenario: E2ETestScenario, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on agent analysis."""
        step_name = "generate_recommendations"
        step_start = time.time()
        
        try:
            assessment_id = test_result["assessment_id"]
            
            # Initialize agents
            cto_agent = CTOAgent()
            cloud_engineer = CloudEngineerAgent()
            research_agent = ResearchAgent()
            
            # Generate recommendations from each agent
            recommendations = []
            
            # CTO recommendations
            try:
                cto_recommendations = await cto_agent.generate_recommendations({
                    "assessment_id": assessment_id,
                    "business_requirements": scenario.business_requirements
                })
                if cto_recommendations:
                    recommendations.extend(cto_recommendations)
            except Exception as e:
                test_result["errors"].append(f"CTO agent recommendations failed: {str(e)}")
            
            # Cloud Engineer recommendations
            try:
                ce_recommendations = await cloud_engineer.generate_recommendations({
                    "assessment_id": assessment_id,
                    "technical_requirements": scenario.technical_requirements
                })
                if ce_recommendations:
                    recommendations.extend(ce_recommendations)
            except Exception as e:
                test_result["errors"].append(f"Cloud Engineer recommendations failed: {str(e)}")
            
            # Research Agent recommendations
            try:
                research_recommendations = await research_agent.generate_recommendations({
                    "assessment_id": assessment_id,
                    "compliance_requirements": scenario.compliance_requirements
                })
                if research_recommendations:
                    recommendations.extend(research_recommendations)
            except Exception as e:
                test_result["errors"].append(f"Research agent recommendations failed: {str(e)}")
            
            # Save recommendations to database
            if db.database and recommendations:
                for rec in recommendations:
                    rec["assessment_id"] = assessment_id
                    rec["created_at"] = datetime.now(timezone.utc)
                
                await db.database.recommendations.insert_many(recommendations)
            
            test_result["recommendations_count"] = len(recommendations)
            test_result["steps_completed"].append(step_name)
            test_result["metrics"][f"{step_name}_duration_ms"] = (time.time() - step_start) * 1000
            test_result["metrics"]["recommendations_generated"] = len(recommendations)
            
            logger.info(f"Generated {len(recommendations)} recommendations for: {assessment_id}")
            return {"success": True, "recommendations": recommendations}
            
        except Exception as e:
            test_result["errors"].append(f"Recommendation generation failed: {str(e)}")
            test_result["steps_failed"].append(step_name)
            return {"success": False}
    
    async def _generate_report(self, scenario: E2ETestScenario, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report."""
        step_name = "generate_report"
        step_start = time.time()
        
        try:
            assessment_id = test_result["assessment_id"]
            
            # Initialize report generator
            report_generator = ReportGeneratorAgent()
            
            # Prepare report data
            report_data = {
                "assessment_id": assessment_id,
                "report_type": "comprehensive",
                "sections": scenario.expected_outcomes.get("report_sections", []),
                "business_requirements": scenario.business_requirements,
                "technical_requirements": scenario.technical_requirements,
                "compliance_requirements": scenario.compliance_requirements
            }
            
            # Generate report
            report_result = await report_generator.generate_report(report_data)
            
            if report_result and "report_id" in report_result:
                # Save report to database
                if db.database:
                    report_doc = {
                        "report_id": report_result["report_id"],
                        "assessment_id": assessment_id,
                        "report_type": "comprehensive",
                        "content": report_result.get("content", {}),
                        "sections": report_result.get("sections", []),
                        "generated_at": datetime.now(timezone.utc),
                        "status": "completed"
                    }
                    await db.database.reports.insert_one(report_doc)
                
                test_result["report_generated"] = True
                test_result["steps_completed"].append(step_name)
                test_result["metrics"][f"{step_name}_duration_ms"] = (time.time() - step_start) * 1000
                test_result["metrics"]["report_sections"] = len(report_result.get("sections", []))
                
                logger.info(f"Report generated for: {assessment_id}")
                return {"success": True, "report": report_result}
            else:
                test_result["errors"].append("Report generation returned no result")
                test_result["steps_failed"].append(step_name)
                return {"success": False}
            
        except Exception as e:
            test_result["errors"].append(f"Report generation failed: {str(e)}")
            test_result["steps_failed"].append(step_name)
            return {"success": False}
    
    async def _validate_results(self, scenario: E2ETestScenario, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that results meet expected outcomes."""
        step_name = "validate_results"
        step_start = time.time()
        
        try:
            expected = scenario.expected_outcomes
            validation_errors = []
            
            # Validate minimum recommendations
            if test_result["recommendations_count"] < expected.get("min_recommendations", 0):
                validation_errors.append(
                    f"Insufficient recommendations: {test_result['recommendations_count']} < {expected['min_recommendations']}"
                )
            
            # Validate report generation
            if expected.get("report_sections") and not test_result["report_generated"]:
                validation_errors.append("Report was not generated as expected")
            
            # Validate execution time
            if test_result["duration_seconds"] > scenario.max_execution_time_seconds:
                validation_errors.append(
                    f"Execution time exceeded limit: {test_result['duration_seconds']}s > {scenario.max_execution_time_seconds}s"
                )
            
            # Validate critical steps completed
            critical_steps = ["create_assessment", "agent_orchestration", "generate_recommendations"]
            missing_steps = [step for step in critical_steps if step not in test_result["steps_completed"]]
            if missing_steps:
                validation_errors.append(f"Critical steps not completed: {missing_steps}")
            
            if validation_errors:
                test_result["errors"].extend(validation_errors)
                test_result["steps_failed"].append(step_name)
                return {"success": False}
            
            test_result["steps_completed"].append(step_name)
            test_result["metrics"][f"{step_name}_duration_ms"] = (time.time() - step_start) * 1000
            
            logger.info(f"Results validation passed for: {scenario.name}")
            return {"success": True}
            
        except Exception as e:
            test_result["errors"].append(f"Results validation failed: {str(e)}")
            test_result["steps_failed"].append(step_name)
            return {"success": False}
    
    async def _cleanup_test_data(self):
        """Clean up test data from database."""
        try:
            if db.database:
                # Clean up test assessments
                await db.database.assessments.delete_many({"assessment_id": {"$regex": "^e2e_test_"}})
                
                # Clean up test recommendations
                await db.database.recommendations.delete_many({"assessment_id": {"$regex": "^e2e_test_"}})
                
                # Clean up test reports
                await db.database.reports.delete_many({"assessment_id": {"$regex": "^e2e_test_"}})
                
                logger.info("E2E test data cleanup completed")
                
        except Exception as e:
            logger.error(f"Test data cleanup failed: {e}")
    
    def generate_e2e_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive E2E test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        report = {
            "summary": {
                "total_scenarios": len(self.test_results),
                "successful_scenarios": len([r for r in self.test_results.values() if r["success"]]),
                "failed_scenarios": len([r for r in self.test_results.values() if not r["success"]]),
                "overall_success_rate": 0.0,
                "total_execution_time": sum(r["duration_seconds"] for r in self.test_results.values()),
                "avg_execution_time": 0.0
            },
            "scenario_results": [],
            "performance_metrics": {
                "avg_assessment_creation_time": 0.0,
                "avg_orchestration_time": 0.0,
                "avg_recommendation_generation_time": 0.0,
                "avg_report_generation_time": 0.0,
                "total_recommendations_generated": 0,
                "total_reports_generated": 0
            },
            "error_analysis": {
                "common_errors": [],
                "error_patterns": [],
                "failure_points": []
            },
            "recommendations": []
        }
        
        # Calculate summary metrics
        successful_count = report["summary"]["successful_scenarios"]
        total_count = report["summary"]["total_scenarios"]
        report["summary"]["overall_success_rate"] = (successful_count / total_count * 100) if total_count > 0 else 0
        report["summary"]["avg_execution_time"] = report["summary"]["total_execution_time"] / total_count if total_count > 0 else 0
        
        # Process scenario results
        all_errors = []
        performance_metrics = []
        
        for scenario_name, result in self.test_results.items():
            scenario_data = {
                "scenario": scenario_name,
                "success": result["success"],
                "duration_seconds": result["duration_seconds"],
                "steps_completed": result["steps_completed"],
                "steps_failed": result["steps_failed"],
                "recommendations_count": result["recommendations_count"],
                "report_generated": result["report_generated"],
                "error_count": len(result["errors"]),
                "metrics": result["metrics"]
            }
            
            report["scenario_results"].append(scenario_data)
            all_errors.extend(result["errors"])
            
            # Collect performance metrics
            for metric_name, value in result["metrics"].items():
                if "duration_ms" in metric_name:
                    performance_metrics.append({
                        "scenario": scenario_name,
                        "metric": metric_name,
                        "value": value
                    })
        
        # Calculate performance metrics
        orchestration_times = [m["value"] for m in performance_metrics if "agent_orchestration" in m["metric"]]
        if orchestration_times:
            report["performance_metrics"]["avg_orchestration_time"] = sum(orchestration_times) / len(orchestration_times)
        
        recommendation_times = [m["value"] for m in performance_metrics if "generate_recommendations" in m["metric"]]
        if recommendation_times:
            report["performance_metrics"]["avg_recommendation_generation_time"] = sum(recommendation_times) / len(recommendation_times)
        
        report_times = [m["value"] for m in performance_metrics if "generate_report" in m["metric"]]
        if report_times:
            report["performance_metrics"]["avg_report_generation_time"] = sum(report_times) / len(report_times)
        
        report["performance_metrics"]["total_recommendations_generated"] = sum(r["recommendations_count"] for r in self.test_results.values())
        report["performance_metrics"]["total_reports_generated"] = sum(1 for r in self.test_results.values() if r["report_generated"])
        
        # Analyze errors
        error_counts = {}
        for error in all_errors:
            error_type = error.split(":")[0] if ":" in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        report["error_analysis"]["common_errors"] = [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Generate recommendations
        if report["summary"]["overall_success_rate"] < 80:
            report["recommendations"].append("Overall success rate is below 80% - investigate common failure patterns")
        
        if report["summary"]["avg_execution_time"] > 300:  # 5 minutes
            report["recommendations"].append("Average execution time exceeds 5 minutes - consider performance optimizations")
        
        if len(error_counts) > 0:
            report["recommendations"].append("Multiple error types detected - review error handling and system reliability")
        
        return report


@pytest.fixture
async def e2e_test_suite():
    """Fixture for end-to-end test suite."""
    suite = EndToEndTestSuite()
    await suite.setup_test_environment()
    yield suite
    await suite.teardown_test_environment()


class TestEndToEndWorkflows:
    """End-to-end workflow test cases."""
    
    @pytest.mark.asyncio
    async def test_small_tech_startup_workflow(self, e2e_test_suite):
        """Test complete workflow for small tech startup scenario."""
        result = await e2e_test_suite.run_complete_workflow("small_tech_startup")
        
        # Assertions
        assert result["success"], f"Small tech startup workflow failed: {result['errors']}"
        assert result["recommendations_count"] >= 5, f"Insufficient recommendations: {result['recommendations_count']}"
        assert result["report_generated"], "Report was not generated"
        assert result["duration_seconds"] < 300, f"Workflow took too long: {result['duration_seconds']}s"
        
        logger.info(f"Small tech startup workflow: {result['duration_seconds']:.2f}s, {result['recommendations_count']} recommendations")
    
    @pytest.mark.asyncio
    async def test_medium_finance_company_workflow(self, e2e_test_suite):
        """Test complete workflow for medium finance company scenario."""
        result = await e2e_test_suite.run_complete_workflow("medium_finance_company")
        
        # Assertions
        assert result["success"], f"Medium finance company workflow failed: {result['errors']}"
        assert result["recommendations_count"] >= 10, f"Insufficient recommendations: {result['recommendations_count']}"
        assert result["report_generated"], "Report was not generated"
        assert result["duration_seconds"] < 600, f"Workflow took too long: {result['duration_seconds']}s"
        
        logger.info(f"Medium finance company workflow: {result['duration_seconds']:.2f}s, {result['recommendations_count']} recommendations")
    
    @pytest.mark.asyncio
    async def test_large_healthcare_enterprise_workflow(self, e2e_test_suite):
        """Test complete workflow for large healthcare enterprise scenario."""
        result = await e2e_test_suite.run_complete_workflow("large_healthcare_enterprise")
        
        # Assertions
        assert result["success"], f"Large healthcare enterprise workflow failed: {result['errors']}"
        assert result["recommendations_count"] >= 15, f"Insufficient recommendations: {result['recommendations_count']}"
        assert result["report_generated"], "Report was not generated"
        assert result["duration_seconds"] < 900, f"Workflow took too long: {result['duration_seconds']}s"
        
        logger.info(f"Large healthcare enterprise workflow: {result['duration_seconds']:.2f}s, {result['recommendations_count']} recommendations")
    
    @pytest.mark.asyncio
    async def test_generate_e2e_report(self, e2e_test_suite):
        """Test E2E report generation."""
        # Run at least one workflow
        await e2e_test_suite.run_complete_workflow("small_tech_startup")
        
        # Generate report
        report = e2e_test_suite.generate_e2e_test_report()
        
        # Assertions
        assert "summary" in report
        assert "scenario_results" in report
        assert "performance_metrics" in report
        assert report["summary"]["total_scenarios"] > 0
        
        # Save report
        with open("e2e_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("E2E test report generated: e2e_test_report.json")


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "--tb=short"])