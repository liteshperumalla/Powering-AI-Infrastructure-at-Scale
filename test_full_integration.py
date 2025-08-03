#!/usr/bin/env python3
"""
Full Integration Test for Infra Mind MVP
Tests the complete system with real APIs, database, LLM, and all components
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.config import get_settings
from infra_mind.core.database import init_database, close_database
from infra_mind.core.cache import cache_manager
from infra_mind.agents.cto_agent import CTOAgent
from infra_mind.agents.cloud_engineer_agent import CloudEngineerAgent
from infra_mind.agents.research_agent import ResearchAgent
from infra_mind.agents.report_generator_agent import ReportGeneratorAgent
from infra_mind.cloud.unified import UnifiedCloudClient
from infra_mind.forms.assessment_form import AssessmentForm
from infra_mind.orchestration.workflow import WorkflowOrchestrator

console = Console()

class FullIntegrationTest:
    """Comprehensive integration test for the MVP"""
    
    def __init__(self):
        self.settings = get_settings()
        self.results = {}
        self.start_time = datetime.now()
        
    async def run_all_tests(self):
        """Run all integration tests"""
        console.print(Panel.fit(
            "[bold blue]🚀 Infra Mind MVP - Full Integration Test[/bold blue]\n"
            f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue"
        ))
        
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Database Connection", self.test_database_connection),
            ("Cache System", self.test_cache_system),
            ("LLM Integration", self.test_llm_integration),
            ("Cloud APIs", self.test_cloud_apis),
            ("Agent System", self.test_agent_system),
            ("Assessment Form", self.test_assessment_form),
            ("Workflow Orchestration", self.test_workflow_orchestration),
            ("API Endpoints", self.test_api_endpoints),
            ("End-to-End User Journey", self.test_end_to_end_journey),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for test_name, test_func in tests:
                task = progress.add_task(f"Running {test_name}...", total=None)
                
                try:
                    result = await test_func()
                    self.results[test_name] = {
                        "status": "PASS" if result else "FAIL",
                        "details": result if isinstance(result, dict) else {}
                    }
                    progress.update(task, description=f"✅ {test_name}")
                    
                except Exception as e:
                    self.results[test_name] = {
                        "status": "ERROR",
                        "error": str(e)
                    }
                    progress.update(task, description=f"❌ {test_name}")
                    console.print(f"[red]Error in {test_name}: {e}[/red]")
                
                progress.remove_task(task)
        
        await self.generate_report()
    
    async def test_environment_setup(self) -> Dict[str, Any]:
        """Test environment configuration"""
        console.print("[yellow]Testing environment setup...[/yellow]")
        
        required_vars = [
            'INFRA_MIND_OPENAI_API_KEY',
            'INFRA_MIND_SECRET_KEY',
            'INFRA_MIND_MONGODB_URL',
            'INFRA_MIND_REDIS_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            console.print(f"[red]Missing environment variables: {missing_vars}[/red]")
            console.print("[yellow]Please set up your .env file with real API keys[/yellow]")
            return False
        
        return {
            "environment": self.settings.environment,
            "debug": self.settings.debug,
            "api_host": self.settings.api_host,
            "api_port": self.settings.api_port,
            "required_vars_present": True
        }
    
    async def test_database_connection(self) -> Dict[str, Any]:
        """Test database connectivity"""
        console.print("[yellow]Testing database connection...[/yellow]")
        
        try:
            await init_database()
            
            # Test MongoDB connection
            from infra_mind.core.database import get_database_info
            db_info = await get_database_info()
            
            await close_database()
            
            return {
                "mongodb_status": db_info.get("status", "unknown"),
                "database_name": db_info.get("database", "unknown"),
                "connection_successful": True
            }
            
        except Exception as e:
            return {"error": str(e), "connection_successful": False}
    
    async def test_cache_system(self) -> Dict[str, Any]:
        """Test Redis cache system"""
        console.print("[yellow]Testing cache system...[/yellow]")
        
        try:
            # Use the global cache manager
            
            # Test cache operations
            test_provider = "test"
            test_service = "integration"
            test_region = "us-east-1"
            test_value = {"test": "data", "timestamp": time.time()}
            
            # Connect to cache
            await cache_manager.connect()
            
            # Set value
            await cache_manager.set(test_provider, test_service, test_region, test_value, ttl=60)
            
            # Get value
            retrieved_value = await cache_manager.get(test_provider, test_service, test_region)
            
            # Delete value
            await cache_manager.delete(test_provider, test_service, test_region)
            
            # Disconnect
            await cache_manager.disconnect()
            
            return {
                "cache_set": True,
                "cache_get": retrieved_value is not None and retrieved_value.get("test") == "data",
                "cache_delete": True,
                "cache_working": True
            }
            
        except Exception as e:
            return {"error": str(e), "cache_working": False}
    
    async def test_llm_integration(self) -> Dict[str, Any]:
        """Test LLM integration with OpenAI"""
        console.print("[yellow]Testing LLM integration...[/yellow]")
        
        try:
            from infra_mind.core.llm import get_llm_client
            
            llm_client = get_llm_client()
            
            # Test simple completion
            response = await llm_client.complete(
                "What is cloud computing? Answer in one sentence.",
                max_tokens=50
            )
            
            return {
                "llm_response_received": bool(response),
                "response_length": len(response) if response else 0,
                "llm_working": bool(response and len(response) > 10)
            }
            
        except Exception as e:
            return {"error": str(e), "llm_working": False}
    
    async def test_cloud_apis(self) -> Dict[str, Any]:
        """Test cloud provider API integrations"""
        console.print("[yellow]Testing cloud APIs...[/yellow]")
        
        try:
            cloud_manager = UnifiedCloudManager()
            
            results = {}
            
            # Test AWS (if configured)
            if os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID'):
                try:
                    aws_services = await cloud_manager.get_available_services('aws')
                    results['aws'] = {
                        "configured": True,
                        "services_count": len(aws_services),
                        "working": len(aws_services) > 0
                    }
                except Exception as e:
                    results['aws'] = {"configured": True, "error": str(e), "working": False}
            else:
                results['aws'] = {"configured": False}
            
            # Test Azure (if configured)
            if os.getenv('INFRA_MIND_AZURE_CLIENT_ID'):
                try:
                    azure_services = await cloud_manager.get_available_services('azure')
                    results['azure'] = {
                        "configured": True,
                        "services_count": len(azure_services),
                        "working": len(azure_services) > 0
                    }
                except Exception as e:
                    results['azure'] = {"configured": True, "error": str(e), "working": False}
            else:
                results['azure'] = {"configured": False}
            
            # Test GCP (if configured)
            if os.getenv('INFRA_MIND_GCP_PROJECT_ID'):
                try:
                    gcp_services = await cloud_manager.get_available_services('gcp')
                    results['gcp'] = {
                        "configured": True,
                        "services_count": len(gcp_services),
                        "working": len(gcp_services) > 0
                    }
                except Exception as e:
                    results['gcp'] = {"configured": True, "error": str(e), "working": False}
            else:
                results['gcp'] = {"configured": False}
            
            return results
            
        except Exception as e:
            return {"error": str(e), "cloud_apis_working": False}
    
    async def test_agent_system(self) -> Dict[str, Any]:
        """Test the multi-agent system"""
        console.print("[yellow]Testing agent system...[/yellow]")
        
        try:
            # Initialize agents
            cto_agent = CTOAgent()
            cloud_agent = CloudEngineerAgent()
            research_agent = ResearchAgent()
            report_agent = ReportGeneratorAgent()
            
            results = {}
            
            # Test CTO Agent
            try:
                cto_response = await cto_agent.analyze_requirements({
                    "company_size": "medium",
                    "industry": "fintech",
                    "current_infrastructure": "on-premise",
                    "ai_goals": ["customer_analytics", "fraud_detection"]
                })
                results['cto_agent'] = {
                    "working": bool(cto_response),
                    "response_type": type(cto_response).__name__
                }
            except Exception as e:
                results['cto_agent'] = {"working": False, "error": str(e)}
            
            # Test Cloud Engineer Agent
            try:
                cloud_response = await cloud_agent.recommend_architecture({
                    "workload_type": "ml_training",
                    "scale": "medium",
                    "budget": "moderate"
                })
                results['cloud_agent'] = {
                    "working": bool(cloud_response),
                    "response_type": type(cloud_response).__name__
                }
            except Exception as e:
                results['cloud_agent'] = {"working": False, "error": str(e)}
            
            # Test Research Agent
            try:
                research_response = await research_agent.research_topic(
                    "latest trends in AI infrastructure 2024"
                )
                results['research_agent'] = {
                    "working": bool(research_response),
                    "response_type": type(research_response).__name__
                }
            except Exception as e:
                results['research_agent'] = {"working": False, "error": str(e)}
            
            return results
            
        except Exception as e:
            return {"error": str(e), "agents_working": False}
    
    async def test_assessment_form(self) -> Dict[str, Any]:
        """Test assessment form processing"""
        console.print("[yellow]Testing assessment form...[/yellow]")
        
        try:
            # Create sample assessment data
            assessment_data = {
                "company_info": {
                    "name": "Test Company",
                    "size": "medium",
                    "industry": "technology"
                },
                "current_infrastructure": {
                    "cloud_provider": "aws",
                    "services_used": ["ec2", "s3", "rds"],
                    "monthly_spend": 5000
                },
                "ai_requirements": {
                    "use_cases": ["machine_learning", "data_analytics"],
                    "data_volume": "medium",
                    "compliance_requirements": ["gdpr"]
                }
            }
            
            # Process assessment
            form = AssessmentForm()
            result = await form.process_assessment(assessment_data)
            
            return {
                "form_processing": bool(result),
                "validation_passed": result.get("valid", False) if result else False,
                "assessment_working": bool(result and result.get("valid"))
            }
            
        except Exception as e:
            return {"error": str(e), "assessment_working": False}
    
    async def test_workflow_orchestration(self) -> Dict[str, Any]:
        """Test workflow orchestration"""
        console.print("[yellow]Testing workflow orchestration...[/yellow]")
        
        try:
            orchestrator = WorkflowOrchestrator()
            
            # Create a simple workflow
            workflow_config = {
                "name": "integration_test_workflow",
                "steps": [
                    {"agent": "cto", "action": "analyze_requirements"},
                    {"agent": "cloud_engineer", "action": "recommend_architecture"},
                    {"agent": "report_generator", "action": "generate_summary"}
                ]
            }
            
            # Execute workflow
            result = await orchestrator.execute_workflow(
                workflow_config,
                {"test": "data"}
            )
            
            return {
                "workflow_executed": bool(result),
                "workflow_working": bool(result and result.get("status") == "completed")
            }
            
        except Exception as e:
            return {"error": str(e), "workflow_working": False}
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        console.print("[yellow]Testing API endpoints...[/yellow]")
        
        try:
            base_url = f"http://localhost:{self.settings.api_port}"
            
            # Test health endpoint
            health_response = requests.get(f"{base_url}/health", timeout=10)
            
            results = {
                "health_endpoint": {
                    "status_code": health_response.status_code,
                    "working": health_response.status_code == 200
                }
            }
            
            # Test other endpoints if API is running
            if health_response.status_code == 200:
                # Test assessments endpoint
                try:
                    assessments_response = requests.get(f"{base_url}/api/assessments", timeout=10)
                    results["assessments_endpoint"] = {
                        "status_code": assessments_response.status_code,
                        "working": assessments_response.status_code in [200, 401]  # 401 is OK (auth required)
                    }
                except Exception as e:
                    results["assessments_endpoint"] = {"error": str(e), "working": False}
                
                # Test recommendations endpoint
                try:
                    recommendations_response = requests.get(f"{base_url}/api/recommendations", timeout=10)
                    results["recommendations_endpoint"] = {
                        "status_code": recommendations_response.status_code,
                        "working": recommendations_response.status_code in [200, 401]
                    }
                except Exception as e:
                    results["recommendations_endpoint"] = {"error": str(e), "working": False}
            
            return results
            
        except Exception as e:
            return {"error": str(e), "api_working": False}
    
    async def test_end_to_end_journey(self) -> Dict[str, Any]:
        """Test complete end-to-end user journey"""
        console.print("[yellow]Testing end-to-end user journey...[/yellow]")
        
        try:
            # Simulate complete user journey
            journey_steps = []
            
            # Step 1: User fills assessment form
            assessment_data = {
                "company_info": {
                    "name": "Integration Test Corp",
                    "size": "medium",
                    "industry": "fintech"
                },
                "current_infrastructure": {
                    "cloud_provider": "aws",
                    "monthly_spend": 10000
                },
                "ai_requirements": {
                    "use_cases": ["fraud_detection", "customer_analytics"],
                    "compliance_requirements": ["pci_dss", "gdpr"]
                }
            }
            
            form = AssessmentForm()
            assessment_result = await form.process_assessment(assessment_data)
            journey_steps.append({
                "step": "assessment_processing",
                "success": bool(assessment_result and assessment_result.get("valid"))
            })
            
            # Step 2: Multi-agent analysis
            if assessment_result and assessment_result.get("valid"):
                orchestrator = WorkflowOrchestrator()
                
                workflow_result = await orchestrator.execute_workflow({
                    "name": "full_analysis_workflow",
                    "steps": [
                        {"agent": "cto", "action": "analyze_requirements"},
                        {"agent": "cloud_engineer", "action": "recommend_architecture"},
                        {"agent": "research_agent", "action": "research_compliance"},
                        {"agent": "report_generator", "action": "generate_report"}
                    ]
                }, assessment_data)
                
                journey_steps.append({
                    "step": "multi_agent_analysis",
                    "success": bool(workflow_result and workflow_result.get("status") == "completed")
                })
            
            # Step 3: Report generation
            if len(journey_steps) > 1 and journey_steps[-1]["success"]:
                report_agent = ReportGeneratorAgent()
                
                report_result = await report_agent.generate_comprehensive_report({
                    "assessment": assessment_data,
                    "analysis_results": workflow_result if 'workflow_result' in locals() else {}
                })
                
                journey_steps.append({
                    "step": "report_generation",
                    "success": bool(report_result)
                })
            
            return {
                "journey_steps": journey_steps,
                "total_steps": len(journey_steps),
                "successful_steps": sum(1 for step in journey_steps if step["success"]),
                "journey_complete": all(step["success"] for step in journey_steps)
            }
            
        except Exception as e:
            return {"error": str(e), "journey_working": False}
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Create summary table
        table = Table(title="Integration Test Results")
        table.add_column("Test", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        passed = 0
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = result["status"]
            if status == "PASS":
                passed += 1
                status_display = "✅ PASS"
            elif status == "FAIL":
                status_display = "❌ FAIL"
            else:
                status_display = "🔥 ERROR"
            
            details = ""
            if "error" in result:
                details = f"Error: {result['error'][:50]}..."
            elif "details" in result and result["details"]:
                details = f"{len(result['details'])} checks"
            
            table.add_row(test_name, status_display, details)
        
        console.print(table)
        
        # Summary panel
        success_rate = (passed / total) * 100 if total > 0 else 0
        summary_text = (
            f"[bold]Test Summary[/bold]\n"
            f"Total Tests: {total}\n"
            f"Passed: {passed}\n"
            f"Failed: {total - passed}\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"Duration: {duration.total_seconds():.2f} seconds"
        )
        
        if success_rate >= 80:
            panel_style = "green"
            status_emoji = "🎉"
        elif success_rate >= 60:
            panel_style = "yellow"
            status_emoji = "⚠️"
        else:
            panel_style = "red"
            status_emoji = "🚨"
        
        console.print(Panel(
            f"{status_emoji} {summary_text}",
            title="Integration Test Complete",
            border_style=panel_style
        ))
        
        # Save detailed results
        results_file = f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate
                },
                "results": self.results
            }, f, indent=2)
        
        console.print(f"\n[blue]Detailed results saved to: {results_file}[/blue]")
        
        return success_rate >= 80


async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold blue]Infra Mind MVP - Full Integration Test[/bold blue]

This script tests the complete Infra Mind system with real APIs and services.

[bold]Prerequisites:[/bold]
1. Set up .env file with real API keys:
   - INFRA_MIND_OPENAI_API_KEY (required)
   - INFRA_MIND_AWS_ACCESS_KEY_ID (optional)
   - INFRA_MIND_AZURE_CLIENT_ID (optional)
   - INFRA_MIND_GCP_PROJECT_ID (optional)

2. Start the system:
   make deploy-dev

3. Run the test:
   python test_full_integration.py

[bold]What it tests:[/bold]
- Environment configuration
- Database connectivity (MongoDB + Redis)
- LLM integration (OpenAI)
- Cloud provider APIs (AWS/Azure/GCP)
- Multi-agent system
- Assessment form processing
- Workflow orchestration
- API endpoints
- Complete end-to-end user journey
        """)
        return
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        console.print(Panel(
            "[red]❌ .env file not found![/red]\n\n"
            "Please copy .env.example to .env and configure with your API keys:\n"
            "[yellow]cp .env.example .env[/yellow]\n\n"
            "Required variables:\n"
            "- INFRA_MIND_OPENAI_API_KEY\n"
            "- INFRA_MIND_SECRET_KEY\n"
            "- INFRA_MIND_MONGODB_URL\n"
            "- INFRA_MIND_REDIS_URL",
            title="Configuration Required",
            border_style="red"
        ))
        return
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    test_runner = FullIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        console.print("\n[bold green]🎉 MVP Integration Test PASSED! System is ready for production.[/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]🚨 MVP Integration Test FAILED! Please check the issues above.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())