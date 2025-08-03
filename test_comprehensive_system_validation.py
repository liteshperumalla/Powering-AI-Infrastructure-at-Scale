#!/usr/bin/env python3
"""
Comprehensive End-to-End System Validation Suite

This script implements task 13.2: Conduct end-to-end system validation
- Test complete user workflows with real services
- Validate all integrations are working correctly  
- Perform security testing and vulnerability assessment
- Conduct performance testing under realistic load conditions
"""

import asyncio
import aiohttp
import time
import json
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import statistics
import uuid
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database, close_database, db
from infra_mind.core.cache import init_cache, cache_manager
from infra_mind.core.config import get_settings
from infra_mind.core.security_audit import SecurityAuditor
from infra_mind.agents.cto_agent import CTOAgent
from infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
from infra_mind.agents.research_agent import ResearchAgent
from infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator
from infra_mind.cloud.unified import UnifiedCloudClient
from infra_mind.forms.assessment_form import AssessmentForm

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Results from system validation."""
    validation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Test results
    integration_tests: Dict[str, bool] = field(default_factory=dict)
    workflow_tests: Dict[str, bool] = field(default_factory=dict)
    security_tests: Dict[str, Any] = field(default_factory=dict)
    performance_tests: Dict[str, Any] = field(default_factory=dict)
    load_tests: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Final assessment
    system_ready: bool = False
    validation_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class ComprehensiveSystemValidator:
    """Comprehensive system validation orchestrator."""
    
    def __init__(self):
        self.settings = get_settings()
        self.validation_id = f"validation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.base_url = f"http://localhost:{self.settings.api_port}"
        
    async def run_validation(self) -> ValidationResult:
        """Run comprehensive system validation."""
        result = ValidationResult(
            validation_id=self.validation_id,
            start_time=datetime.now(timezone.utc)
        )
        
        console.print(Panel.fit(
            f"[bold blue]🔍 Comprehensive System Validation[/bold blue]\n"
            f"Validation ID: {self.validation_id}\n"
            f"Started: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue"
        ))
        
        validation_phases = [
            ("Environment Setup", self._setup_environment),
            ("Integration Testing", self._test_integrations),
            ("User Workflow Testing", self._test_user_workflows),
            ("Security Assessment", self._test_security),
            ("Performance Testing", self._test_performance),
            ("Load Testing", self._test_load),
            ("Final Analysis", self._analyze_results)
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for phase_name, phase_func in validation_phases:
                task = progress.add_task(f"Running {phase_name}...", total=None)
                
                try:
                    await phase_func(result)
                    progress.update(task, description=f"✅ {phase_name}")
                except Exception as e:
                    result.critical_issues.append(f"{phase_name} failed: {str(e)}")
                    progress.update(task, description=f"❌ {phase_name}")
                    console.print(f"[red]Error in {phase_name}: {e}[/red]")
                
                progress.remove_task(task)
        
        result.end_time = datetime.now(timezone.utc)
        await self._generate_report(result)
        
        return result  
  
    async def _setup_environment(self, result: ValidationResult):
        """Set up validation environment."""
        console.print("[yellow]Setting up validation environment...[/yellow]")
        
        try:
            # Initialize database
            await init_database()
            result.integration_tests["database_init"] = True
            
            # Initialize cache
            await init_cache()
            if cache_manager:
                result.integration_tests["cache_init"] = True
            else:
                result.integration_tests["cache_init"] = False
                result.warnings.append("Cache initialization failed - running without cache")
            
            # Check environment variables
            required_vars = [
                'INFRA_MIND_OPENAI_API_KEY',
                'INFRA_MIND_SECRET_KEY',
                'INFRA_MIND_MONGODB_URL',
                'INFRA_MIND_REDIS_URL'
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                result.critical_issues.append(f"Missing environment variables: {missing_vars}")
                result.integration_tests["environment_config"] = False
            else:
                result.integration_tests["environment_config"] = True
            
            console.print("[green]Environment setup completed[/green]")
            
        except Exception as e:
            result.critical_issues.append(f"Environment setup failed: {str(e)}")
            raise
    
    async def _test_integrations(self, result: ValidationResult):
        """Test all system integrations."""
        console.print("[yellow]Testing system integrations...[/yellow]")
        
        # Test database operations
        try:
            if db.database:
                # Test basic CRUD operations
                test_doc = {
                    "test_id": f"validation_{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.utcnow(),
                    "data": {"test": "validation"}
                }
                
                # Insert
                await db.database.test_collection.insert_one(test_doc)
                
                # Find
                found_doc = await db.database.test_collection.find_one({"test_id": test_doc["test_id"]})
                
                # Update
                await db.database.test_collection.update_one(
                    {"test_id": test_doc["test_id"]},
                    {"$set": {"updated": True}}
                )
                
                # Delete
                await db.database.test_collection.delete_one({"test_id": test_doc["test_id"]})
                
                result.integration_tests["database_operations"] = True
            else:
                result.integration_tests["database_operations"] = False
                result.critical_issues.append("Database not available")
                
        except Exception as e:
            result.integration_tests["database_operations"] = False
            result.critical_issues.append(f"Database operations failed: {str(e)}")
        
        # Test cache operations
        try:
            test_key = f"validation_test_{uuid.uuid4().hex[:8]}"
            test_value = {"test": "cache_validation", "timestamp": time.time()}
            
            # Set
            await cache_manager.set("test", "validation", "global", test_value, 60)
            
            # Get
            retrieved = await cache_manager.get("test", "validation", "global")
            
            # Delete
            await cache_manager.delete("test", "validation", "global")
            
            result.integration_tests["cache_operations"] = retrieved is not None
            
        except Exception as e:
            result.integration_tests["cache_operations"] = False
            result.critical_issues.append(f"Cache operations failed: {str(e)}")
        
        # Test cloud APIs
        try:
            cloud_manager = UnifiedCloudClient()
            
            # Test at least one cloud provider
            cloud_tests = {}
            
            if os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID'):
                try:
                    aws_services = await cloud_manager.get_available_services('aws')
                    cloud_tests['aws'] = len(aws_services) > 0
                except Exception as e:
                    cloud_tests['aws'] = False
                    result.warnings.append(f"AWS API test failed: {str(e)}")
            
            if os.getenv('INFRA_MIND_AZURE_CLIENT_ID'):
                try:
                    azure_services = await cloud_manager.get_available_services('azure')
                    cloud_tests['azure'] = len(azure_services) > 0
                except Exception as e:
                    cloud_tests['azure'] = False
                    result.warnings.append(f"Azure API test failed: {str(e)}")
            
            if os.getenv('INFRA_MIND_GCP_PROJECT_ID'):
                try:
                    gcp_services = await cloud_manager.get_available_services('gcp')
                    cloud_tests['gcp'] = len(gcp_services) > 0
                except Exception as e:
                    cloud_tests['gcp'] = False
                    result.warnings.append(f"GCP API test failed: {str(e)}")
            
            result.integration_tests["cloud_apis"] = any(cloud_tests.values()) if cloud_tests else False
            
        except Exception as e:
            result.integration_tests["cloud_apis"] = False
            result.warnings.append(f"Cloud API integration test failed: {str(e)}")
        
        # Test LLM integration
        try:
            from infra_mind.llm.openai_provider import OpenAIProvider
            
            llm_provider = OpenAIProvider()
            response = await llm_provider.generate_response(
                "Test prompt for validation", 
                {"max_tokens": 10}
            )
            
            result.integration_tests["llm_integration"] = bool(response)
            
        except Exception as e:
            result.integration_tests["llm_integration"] = False
            result.warnings.append(f"LLM integration test failed: {str(e)}")
        
        # Test agent initialization
        try:
            cto_agent = CTOAgent()
            cloud_agent = CloudEngineerAgent()
            research_agent = ResearchAgent()
            
            result.integration_tests["agent_initialization"] = True
            
        except Exception as e:
            result.integration_tests["agent_initialization"] = False
            result.critical_issues.append(f"Agent initialization failed: {str(e)}")
        
        console.print(f"[green]Integration tests completed: {sum(result.integration_tests.values())}/{len(result.integration_tests)} passed[/green]")
    
    async def _test_user_workflows(self, result: ValidationResult):
        """Test complete user workflows."""
        console.print("[yellow]Testing user workflows...[/yellow]")
        
        # Test assessment creation workflow
        try:
            assessment_data = {
                "user_id": f"validation_user_{uuid.uuid4().hex[:8]}",
                "company_info": {
                    "name": "Validation Test Corp",
                    "size": "medium",
                    "industry": "technology"
                },
                "business_requirements": {
                    "industry": "technology",
                    "company_size": "medium",
                    "budget_range": "100000-500000",
                    "timeline": "6-12 months"
                },
                "technical_requirements": {
                    "workload_types": ["web_application", "api_services"],
                    "expected_users": 10000,
                    "preferred_cloud": "aws"
                },
                "compliance_requirements": {
                    "frameworks": ["gdpr"],
                    "data_residency": "us"
                }
            }
            
            # Test form processing
            form = AssessmentForm()
            form_result = await form.process_assessment(assessment_data)
            
            result.workflow_tests["assessment_creation"] = bool(form_result and form_result.get("valid"))
            
        except Exception as e:
            result.workflow_tests["assessment_creation"] = False
            result.critical_issues.append(f"Assessment creation workflow failed: {str(e)}")
        
        # Test agent orchestration workflow
        try:
            orchestrator = LangGraphOrchestrator()
            
            workflow_data = {
                "assessment_id": f"validation_assessment_{uuid.uuid4().hex[:8]}",
                "business_requirements": assessment_data["business_requirements"],
                "technical_requirements": assessment_data["technical_requirements"]
            }
            
            # Run with timeout
            workflow_result = await asyncio.wait_for(
                orchestrator.run_assessment_workflow(workflow_data),
                timeout=120  # 2 minutes timeout
            )
            
            result.workflow_tests["agent_orchestration"] = bool(workflow_result)
            
        except asyncio.TimeoutError:
            result.workflow_tests["agent_orchestration"] = False
            result.warnings.append("Agent orchestration workflow timed out")
        except Exception as e:
            result.workflow_tests["agent_orchestration"] = False
            result.warnings.append(f"Agent orchestration workflow failed: {str(e)}")
        
        # Test individual agent workflows
        agent_tests = {}
        
        # CTO Agent
        try:
            cto_agent = CTOAgent()
            cto_result = await asyncio.wait_for(
                cto_agent.analyze_requirements(assessment_data),
                timeout=60
            )
            agent_tests["cto_agent"] = bool(cto_result)
        except Exception as e:
            agent_tests["cto_agent"] = False
            result.warnings.append(f"CTO agent test failed: {str(e)}")
        
        # Cloud Engineer Agent
        try:
            cloud_agent = CloudEngineerAgent()
            cloud_result = await asyncio.wait_for(
                cloud_agent.analyze_technical_requirements(assessment_data),
                timeout=60
            )
            agent_tests["cloud_engineer_agent"] = bool(cloud_result)
        except Exception as e:
            agent_tests["cloud_engineer_agent"] = False
            result.warnings.append(f"Cloud Engineer agent test failed: {str(e)}")
        
        # Research Agent
        try:
            research_agent = ResearchAgent()
            research_result = await asyncio.wait_for(
                research_agent.research_topic("cloud infrastructure best practices"),
                timeout=60
            )
            agent_tests["research_agent"] = bool(research_result)
        except Exception as e:
            agent_tests["research_agent"] = False
            result.warnings.append(f"Research agent test failed: {str(e)}")
        
        result.workflow_tests.update(agent_tests)
        
        console.print(f"[green]Workflow tests completed: {sum(result.workflow_tests.values())}/{len(result.workflow_tests)} passed[/green]")
    
    async def _test_security(self, result: ValidationResult):
        """Perform security testing and vulnerability assessment."""
        console.print("[yellow]Running security assessment...[/yellow]")
        
        try:
            # Run security audit
            security_auditor = SecurityAuditor(self.base_url)
            
            async with security_auditor:
                audit_report = await security_auditor.run_full_audit()
            
            # Analyze security results
            result.security_tests = {
                "audit_completed": True,
                "total_findings": len(audit_report.findings),
                "critical_findings": len(audit_report.get_critical_findings()),
                "high_findings": len(audit_report.get_findings_by_level("high")),
                "risk_score": audit_report.calculate_risk_score(),
                "compliance_status": audit_report.compliance_status
            }
            
            # Check for critical security issues
            if audit_report.calculate_risk_score() > 75:
                result.critical_issues.append(f"High security risk score: {audit_report.calculate_risk_score()}")
            
            if len(audit_report.get_critical_findings()) > 0:
                result.critical_issues.append(f"Critical security vulnerabilities found: {len(audit_report.get_critical_findings())}")
            
            # Check compliance status
            failed_compliance = [std for std, status in audit_report.compliance_status.items() if not status]
            if failed_compliance:
                result.warnings.append(f"Compliance failures: {failed_compliance}")
            
        except Exception as e:
            result.security_tests = {"audit_completed": False, "error": str(e)}
            result.critical_issues.append(f"Security assessment failed: {str(e)}")
        
        console.print("[green]Security assessment completed[/green]")
    
    async def _test_performance(self, result: ValidationResult):
        """Test system performance under normal conditions."""
        console.print("[yellow]Running performance tests...[/yellow]")
        
        performance_metrics = {}
        
        # Test database performance
        try:
            start_time = time.time()
            
            if db.database:
                # Simple query test
                await db.database.assessments.find_one({"status": "completed"})
                query_time = (time.time() - start_time) * 1000
                
                performance_metrics["database_query_ms"] = query_time
                performance_metrics["database_performance_ok"] = query_time < 1000  # < 1 second
            
        except Exception as e:
            performance_metrics["database_performance_ok"] = False
            result.warnings.append(f"Database performance test failed: {str(e)}")
        
        # Test cache performance
        try:
            start_time = time.time()
            
            test_data = {"test": "performance", "timestamp": time.time()}
            await cache_manager.set("perf", "test", "global", test_data, 60)
            
            cache_time = (time.time() - start_time) * 1000
            performance_metrics["cache_set_ms"] = cache_time
            performance_metrics["cache_performance_ok"] = cache_time < 100  # < 100ms
            
        except Exception as e:
            performance_metrics["cache_performance_ok"] = False
            result.warnings.append(f"Cache performance test failed: {str(e)}")
        
        # Test API response times
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.get(f"{self.base_url}/health") as response:
                    api_time = (time.time() - start_time) * 1000
                    
                    performance_metrics["api_response_ms"] = api_time
                    performance_metrics["api_performance_ok"] = api_time < 500 and response.status == 200
                    
        except Exception as e:
            performance_metrics["api_performance_ok"] = False
            result.warnings.append(f"API performance test failed: {str(e)}")
        
        # Test LLM performance
        try:
            from infra_mind.llm.openai_provider import OpenAIProvider
            
            llm_provider = OpenAIProvider()
            start_time = time.time()
            
            response = await llm_provider.generate_response(
                "Quick test prompt", 
                {"max_tokens": 10}
            )
            
            llm_time = (time.time() - start_time) * 1000
            performance_metrics["llm_response_ms"] = llm_time
            performance_metrics["llm_performance_ok"] = llm_time < 10000  # < 10 seconds
            
        except Exception as e:
            performance_metrics["llm_performance_ok"] = False
            result.warnings.append(f"LLM performance test failed: {str(e)}")
        
        result.performance_tests = performance_metrics
        
        console.print(f"[green]Performance tests completed[/green]")
    
    async def _test_load(self, result: ValidationResult):
        """Test system under load conditions."""
        console.print("[yellow]Running load tests...[/yellow]")
        
        load_metrics = {}
        
        # Concurrent API requests test
        try:
            async def make_request(session, request_id):
                try:
                    start_time = time.time()
                    async with session.get(f"{self.base_url}/health") as response:
                        response_time = (time.time() - start_time) * 1000
                        return {
                            "success": response.status == 200,
                            "response_time": response_time,
                            "request_id": request_id
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "response_time": 0,
                        "request_id": request_id,
                        "error": str(e)
                    }
            
            # Run 20 concurrent requests
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(20)]
                results = await asyncio.gather(*tasks)
            
            successful_requests = [r for r in results if r["success"]]
            success_rate = len(successful_requests) / len(results) * 100
            
            if successful_requests:
                avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
            else:
                avg_response_time = 0
            
            load_metrics["concurrent_requests_success_rate"] = success_rate
            load_metrics["concurrent_requests_avg_ms"] = avg_response_time
            load_metrics["load_test_passed"] = success_rate >= 90 and avg_response_time < 2000
            
        except Exception as e:
            load_metrics["load_test_passed"] = False
            result.warnings.append(f"Load test failed: {str(e)}")
        
        # Agent concurrency test
        try:
            async def test_agent_concurrency():
                cto_agent = CTOAgent()
                test_data = {
                    "user_id": f"load_test_{uuid.uuid4().hex[:8]}",
                    "business_requirements": {
                        "industry": "technology",
                        "company_size": "small"
                    }
                }
                
                try:
                    result = await asyncio.wait_for(
                        cto_agent.analyze_requirements(test_data),
                        timeout=30
                    )
                    return {"success": True}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            # Run 5 concurrent agent requests
            agent_tasks = [test_agent_concurrency() for _ in range(5)]
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            successful_agents = len([r for r in agent_results if isinstance(r, dict) and r.get("success")])
            agent_success_rate = successful_agents / len(agent_results) * 100
            
            load_metrics["agent_concurrency_success_rate"] = agent_success_rate
            load_metrics["agent_load_test_passed"] = agent_success_rate >= 60  # More lenient for agents
            
        except Exception as e:
            load_metrics["agent_load_test_passed"] = False
            result.warnings.append(f"Agent load test failed: {str(e)}")
        
        result.load_tests = load_metrics
        
        console.print("[green]Load tests completed[/green]")
    
    async def _analyze_results(self, result: ValidationResult):
        """Analyze all test results and determine system readiness."""
        console.print("[yellow]Analyzing validation results...[/yellow]")
        
        # Count total tests
        result.total_tests = (
            len(result.integration_tests) +
            len(result.workflow_tests) +
            (1 if result.security_tests.get("audit_completed") else 0) +
            len([k for k in result.performance_tests.keys() if k.endswith("_ok")]) +
            len([k for k in result.load_tests.keys() if k.endswith("_passed")])
        )
        
        # Count passed tests
        result.passed_tests = (
            sum(result.integration_tests.values()) +
            sum(result.workflow_tests.values()) +
            (1 if result.security_tests.get("audit_completed") and result.security_tests.get("risk_score", 100) < 50 else 0) +
            sum(1 for k, v in result.performance_tests.items() if k.endswith("_ok") and v) +
            sum(1 for k, v in result.load_tests.items() if k.endswith("_passed") and v)
        )
        
        result.failed_tests = result.total_tests - result.passed_tests
        
        # Calculate validation score
        if result.total_tests > 0:
            result.validation_score = (result.passed_tests / result.total_tests) * 100
        
        # Determine system readiness
        critical_systems_ok = all([
            result.integration_tests.get("database_operations", False),
            result.integration_tests.get("cache_operations", False),
            result.integration_tests.get("agent_initialization", False),
            len(result.critical_issues) == 0
        ])
        
        performance_ok = all([
            result.performance_tests.get("database_performance_ok", False),
            result.performance_tests.get("api_performance_ok", False)
        ])
        
        security_ok = (
            result.security_tests.get("audit_completed", False) and
            result.security_tests.get("risk_score", 100) < 75 and
            result.security_tests.get("critical_findings", 1) == 0
        )
        
        result.system_ready = (
            critical_systems_ok and
            performance_ok and
            security_ok and
            result.validation_score >= 80
        )
        
        console.print(f"[green]Analysis completed: {result.validation_score:.1f}% validation score[/green]")
    
    async def _generate_report(self, result: ValidationResult):
        """Generate comprehensive validation report."""
        console.print("[yellow]Generating validation report...[/yellow]")
        
        # Create summary table
        table = Table(title="System Validation Results")
        table.add_column("Test Category", style="cyan", no_wrap=True)
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Status", style="magenta")
        
        # Integration tests
        integration_passed = sum(result.integration_tests.values())
        integration_total = len(result.integration_tests)
        integration_status = "✅ PASS" if integration_passed == integration_total else "❌ FAIL"
        table.add_row("Integration Tests", str(integration_passed), str(integration_total - integration_passed), integration_status)
        
        # Workflow tests
        workflow_passed = sum(result.workflow_tests.values())
        workflow_total = len(result.workflow_tests)
        workflow_status = "✅ PASS" if workflow_passed >= workflow_total * 0.8 else "❌ FAIL"
        table.add_row("Workflow Tests", str(workflow_passed), str(workflow_total - workflow_passed), workflow_status)
        
        # Security tests
        security_status = "✅ PASS" if result.security_tests.get("risk_score", 100) < 50 else "❌ FAIL"
        security_findings = result.security_tests.get("total_findings", 0)
        table.add_row("Security Tests", "1" if security_status == "✅ PASS" else "0", str(security_findings), security_status)
        
        # Performance tests
        perf_passed = sum(1 for k, v in result.performance_tests.items() if k.endswith("_ok") and v)
        perf_total = len([k for k in result.performance_tests.keys() if k.endswith("_ok")])
        perf_status = "✅ PASS" if perf_passed >= perf_total * 0.8 else "❌ FAIL"
        table.add_row("Performance Tests", str(perf_passed), str(perf_total - perf_passed), perf_status)
        
        # Load tests
        load_passed = sum(1 for k, v in result.load_tests.items() if k.endswith("_passed") and v)
        load_total = len([k for k in result.load_tests.keys() if k.endswith("_passed")])
        load_status = "✅ PASS" if load_passed >= load_total * 0.7 else "❌ FAIL"
        table.add_row("Load Tests", str(load_passed), str(load_total - load_passed), load_status)
        
        console.print(table)
        
        # Summary panel
        duration = (result.end_time - result.start_time).total_seconds() / 60
        summary_text = (
            f"[bold]Validation Summary[/bold]\n"
            f"Validation ID: {result.validation_id}\n"
            f"Duration: {duration:.1f} minutes\n"
            f"Total Tests: {result.total_tests}\n"
            f"Passed: {result.passed_tests}\n"
            f"Failed: {result.failed_tests}\n"
            f"Success Rate: {result.success_rate:.1f}%\n"
            f"Validation Score: {result.validation_score:.1f}%\n"
            f"Critical Issues: {len(result.critical_issues)}\n"
            f"Warnings: {len(result.warnings)}"
        )
        
        if result.system_ready:
            panel_style = "green"
            status_emoji = "🎉"
            status_text = "SYSTEM READY FOR PRODUCTION"
        else:
            panel_style = "red"
            status_emoji = "🚨"
            status_text = "SYSTEM NOT READY - ISSUES FOUND"
        
        console.print(Panel(
            f"{status_emoji} {summary_text}\n\n[bold]{status_text}[/bold]",
            title="System Validation Complete",
            border_style=panel_style
        ))
        
        # Show critical issues
        if result.critical_issues:
            console.print("\n[bold red]Critical Issues:[/bold red]")
            for issue in result.critical_issues:
                console.print(f"  • {issue}")
        
        # Show warnings
        if result.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")
        
        # Save detailed report
        report_data = {
            "validation_id": result.validation_id,
            "timestamp": result.end_time.isoformat(),
            "duration_minutes": duration,
            "summary": {
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "success_rate": result.success_rate,
                "validation_score": result.validation_score,
                "system_ready": result.system_ready
            },
            "test_results": {
                "integration_tests": result.integration_tests,
                "workflow_tests": result.workflow_tests,
                "security_tests": result.security_tests,
                "performance_tests": result.performance_tests,
                "load_tests": result.load_tests
            },
            "issues": {
                "critical_issues": result.critical_issues,
                "warnings": result.warnings
            }
        }
        
        report_file = f"system_validation_report_{result.validation_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        console.print(f"\n[blue]Detailed report saved to: {report_file}[/blue]")
        
        return result.system_ready


async def main():
    """Main validation runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold blue]Comprehensive System Validation Suite[/bold blue]

This script implements task 13.2: Conduct end-to-end system validation

[bold]What it validates:[/bold]
• Complete user workflows with real services
• All system integrations working correctly
• Security vulnerabilities and compliance
• Performance under normal conditions
• System behavior under load

[bold]Prerequisites:[/bold]
1. System must be running (make deploy-dev)
2. Environment variables configured (.env file)
3. Real API keys for external services

[bold]Usage:[/bold]
python test_comprehensive_system_validation.py
        """)
        return
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run validation
    validator = ComprehensiveSystemValidator()
    result = await validator.run_validation()
    
    if result.system_ready:
        console.print("\n[bold green]🎉 SYSTEM VALIDATION PASSED - READY FOR PRODUCTION[/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]🚨 SYSTEM VALIDATION FAILED - CRITICAL ISSUES FOUND[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())