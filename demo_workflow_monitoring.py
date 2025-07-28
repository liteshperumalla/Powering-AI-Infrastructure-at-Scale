"""
Demo script for advanced workflow monitoring and debugging system.

Demonstrates comprehensive logging, distributed tracing, performance monitoring,
and real-time dashboard capabilities.
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.orchestration.events import EventManager
from src.infra_mind.orchestration.monitoring import (
    WorkflowMonitor, initialize_workflow_monitoring, get_workflow_monitor
)
from src.infra_mind.orchestration.dashboard import (
    WorkflowDashboard, DashboardView, initialize_workflow_dashboard, get_workflow_dashboard
)
from src.infra_mind.core.advanced_logging import (
    setup_advanced_logging, get_agent_logger, get_workflow_logger,
    log_context, log_async_performance
)
from src.infra_mind.core.metrics_collector import initialize_metrics_collection
from src.infra_mind.models.assessment import Assessment


# Set up logging
setup_advanced_logging(
    log_level="INFO",
    log_file="logs/monitoring_demo.log",
    enable_console=True,
    enable_structured=True
)

logger = logging.getLogger(__name__)


class MockAgent:
    """Mock agent for demonstration purposes."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_agent_logger(name)
    
    @log_async_performance("agent_execution")
    async def execute(self, assessment: Assessment, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock agent logic."""
        with log_context(agent_name=self.name, workflow_id=context.get("workflow_id")):
            logger.info(f"Starting {self.name} execution")
            
            # Simulate agent decision making
            await self._analyze_requirements(assessment)
            
            # Simulate tool usage
            await self._use_tools(context)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(assessment, context)
            
            # Simulate LLM interaction
            await self._llm_interaction(recommendations)
            
            logger.info(f"Completed {self.name} execution")
            
            return {
                "agent": self.name,
                "recommendations": recommendations,
                "confidence": 0.85,
                "execution_time": time.time() - context.get("start_time", time.time())
            }
    
    async def _analyze_requirements(self, assessment: Assessment):
        """Simulate requirement analysis."""
        await asyncio.sleep(0.5)  # Simulate processing time
        
        self.logger.log_decision(
            decision=f"Focus on {assessment.business_requirements.get('industry', 'general')} requirements",
            reasoning="Industry-specific compliance and performance needs identified",
            confidence=0.9,
            alternatives=["Generic approach", "Cost-only optimization"],
            context={"assessment_id": assessment.id if hasattr(assessment, 'id') else 'demo'}
        )
    
    async def _use_tools(self, context: Dict[str, Any]):
        """Simulate tool usage."""
        await asyncio.sleep(0.3)
        
        self.logger.log_tool_usage(
            tool_name="cloud_pricing_api",
            input_data={"service": "compute", "region": "us-east-1"},
            output_data={"price_per_hour": 0.096, "availability": "high"},
            execution_time=0.3
        )
    
    async def _generate_recommendations(self, assessment: Assessment, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock recommendations."""
        await asyncio.sleep(0.4)
        
        recommendations = {
            "primary_recommendation": f"{self.name} suggests cloud migration",
            "cost_estimate": 5000,
            "timeline": "3 months",
            "risk_level": "medium"
        }
        
        self.logger.log_recommendation(
            recommendation_type="infrastructure",
            recommendation=recommendations,
            supporting_data={
                "cost_analysis": {"current": 8000, "projected": 5000},
                "performance_metrics": {"latency": "50ms", "throughput": "1000 req/s"}
            }
        )
        
        return recommendations
    
    async def _llm_interaction(self, recommendations: Dict[str, Any]):
        """Simulate LLM interaction."""
        await asyncio.sleep(0.6)
        
        prompt = f"Generate executive summary for: {recommendations}"
        response = "Based on the analysis, I recommend proceeding with cloud migration..."
        
        self.logger.log_llm_interaction(
            prompt=prompt,
            response=response,
            model="gpt-4",
            tokens_used=250,
            response_time=0.6
        )


async def simulate_workflow_execution(event_manager: EventManager, assessment: Assessment):
    """Simulate a complete workflow execution."""
    workflow_logger = get_workflow_logger()
    workflow_id = f"demo_workflow_{int(time.time())}"
    
    agents = [
        MockAgent("cto_agent"),
        MockAgent("cloud_engineer_agent"),
        MockAgent("research_agent")
    ]
    
    with log_context(workflow_id=workflow_id):
        logger.info(f"Starting workflow simulation: {workflow_id}")
        
        # Log workflow start
        workflow_logger.log_workflow_started(
            workflow_id=workflow_id,
            workflow_name="Demo Multi-Agent Workflow",
            steps=[agent.name for agent in agents],
            context={"demo": True, "assessment_type": "infrastructure"}
        )
        
        # Publish workflow started event
        await event_manager.publish_workflow_started(
            workflow_id,
            {
                "name": "Demo Multi-Agent Workflow",
                "total_steps": len(agents),
                "assessment_id": getattr(assessment, 'id', 'demo')
            }
        )
        
        workflow_start_time = time.time()
        results = {}
        
        # Execute agents sequentially
        for i, agent in enumerate(agents):
            step_id = f"step_{i+1}"
            
            with log_context(step_id=step_id, agent_name=agent.name):
                # Log step start
                workflow_logger.log_step_started(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    step_name=f"{agent.name} Analysis",
                    agent_name=agent.name
                )
                
                # Publish agent started event
                await event_manager.publish_agent_started(
                    agent.name,
                    {"workflow_id": workflow_id, "step_id": step_id}
                )
                
                step_start_time = time.time()
                
                try:
                    # Execute agent
                    result = await agent.execute(assessment, {
                        "workflow_id": workflow_id,
                        "step_id": step_id,
                        "start_time": step_start_time
                    })
                    
                    execution_time = time.time() - step_start_time
                    results[agent.name] = result
                    
                    # Log step completion
                    workflow_logger.log_step_completed(
                        workflow_id=workflow_id,
                        step_id=step_id,
                        step_name=f"{agent.name} Analysis",
                        agent_name=agent.name,
                        execution_time=execution_time,
                        result=result
                    )
                    
                    # Publish agent completed event
                    await event_manager.publish_agent_completed(
                        agent.name,
                        {
                            "workflow_id": workflow_id,
                            "step_id": step_id,
                            "execution_time": execution_time,
                            "recommendations_count": len(result.get("recommendations", {}))
                        }
                    )
                    
                    logger.info(f"Agent {agent.name} completed successfully")
                    
                except Exception as e:
                    # Simulate occasional failures
                    if i == 1 and time.time() % 10 < 2:  # 20% chance of failure for demo
                        error_msg = f"Simulated failure in {agent.name}: {str(e)}"
                        
                        workflow_logger.log_workflow_failed(
                            workflow_id=workflow_id,
                            workflow_name="Demo Multi-Agent Workflow",
                            error=error_msg,
                            failed_step=step_id
                        )
                        
                        await event_manager.publish_agent_failed(
                            agent.name,
                            error_msg,
                            {"workflow_id": workflow_id, "step_id": step_id}
                        )
                        
                        await event_manager.publish_workflow_failed(
                            workflow_id,
                            error_msg
                        )
                        
                        logger.error(f"Workflow failed: {error_msg}")
                        return
                    else:
                        raise
        
        # Complete workflow
        total_execution_time = time.time() - workflow_start_time
        
        workflow_logger.log_workflow_completed(
            workflow_id=workflow_id,
            workflow_name="Demo Multi-Agent Workflow",
            execution_time=total_execution_time,
            results=results
        )
        
        await event_manager.publish_workflow_completed(
            workflow_id,
            {
                "completed_steps": len(agents),
                "total_execution_time": total_execution_time,
                "results_summary": {
                    "total_recommendations": sum(
                        len(result.get("recommendations", {})) for result in results.values()
                    ),
                    "avg_confidence": sum(
                        result.get("confidence", 0) for result in results.values()
                    ) / len(results) if results else 0
                }
            }
        )
        
        logger.info(f"Workflow completed successfully in {total_execution_time:.2f}s")


async def demonstrate_monitoring_features():
    """Demonstrate monitoring and dashboard features."""
    logger.info("Starting workflow monitoring demonstration")
    
    # Initialize components
    event_manager = EventManager()
    await initialize_metrics_collection()
    await initialize_workflow_monitoring(event_manager)
    
    monitor = get_workflow_monitor()
    await initialize_workflow_dashboard(monitor)
    dashboard = get_workflow_dashboard()
    
    # Create sample assessment
    assessment = Assessment(
        title="Demo Infrastructure Assessment",
        user_id="demo_user",
        business_requirements={
            "company_size": "mid-size",
            "industry": "healthcare",
            "budget_range": "100k-500k",
            "compliance_needs": ["HIPAA", "SOC2"]
        },
        technical_requirements={
            "current_infrastructure": "on-premise",
            "workload_type": "ml_training",
            "performance_requirements": {"latency": "low", "throughput": "high"}
        },
        compliance_requirements={
            "regulations": ["HIPAA"],
            "data_residency": "US"
        }
    )
    
    print("\n" + "="*60)
    print("WORKFLOW MONITORING DEMONSTRATION")
    print("="*60)
    
    # Run multiple workflows to generate data
    print("\n1. Executing multiple workflows to generate monitoring data...")
    
    workflow_tasks = []
    for i in range(3):
        task = asyncio.create_task(simulate_workflow_execution(event_manager, assessment))
        workflow_tasks.append(task)
        await asyncio.sleep(1)  # Stagger workflow starts
    
    # Wait for workflows to complete
    await asyncio.gather(*workflow_tasks, return_exceptions=True)
    
    # Allow time for monitoring data to be processed
    await asyncio.sleep(2)
    
    # Demonstrate dashboard views
    print("\n2. Dashboard Views:")
    print("-" * 30)
    
    # Overview
    overview_data = dashboard.get_dashboard_data(DashboardView.OVERVIEW)
    print(f"\nOVERVIEW:")
    print(f"  Active Workflows: {overview_data.get('metrics', {}).get('active_workflows', 0)}")
    print(f"  Completed Workflows: {overview_data.get('metrics', {}).get('completed_workflows', 0)}")
    print(f"  Active Alerts: {overview_data.get('active_alerts', 0)}")
    print(f"  System Health: {overview_data.get('system_health', {}).get('overall_status', 'unknown')}")
    
    # Workflows
    workflows_data = dashboard.get_dashboard_data(DashboardView.WORKFLOWS)
    print(f"\nWORKFLOWS:")
    for workflow in workflows_data.get('workflows', [])[:3]:
        print(f"  {workflow['workflow_id'][:20]}... - {workflow['status']} - {workflow['progress_percent']:.1f}%")
    
    # Agents
    agents_data = dashboard.get_dashboard_data(DashboardView.AGENTS)
    print(f"\nAGENTS:")
    for agent in agents_data.get('agents', []):
        print(f"  {agent['agent_name']} - {agent['status']} - Success Rate: {agent['success_rate_percent']:.1f}%")
    
    # Performance
    performance_data = dashboard.get_dashboard_data(DashboardView.PERFORMANCE)
    print(f"\nPERFORMANCE:")
    perf_metrics = performance_data.get('performance_metrics', {})
    print(f"  Avg Workflow Duration: {perf_metrics.get('avg_workflow_duration', 0):.2f} minutes")
    print(f"  Avg Agent Response Time: {perf_metrics.get('avg_agent_response_time', 0):.2f} seconds")
    
    # Alerts
    alerts_data = dashboard.get_dashboard_data(DashboardView.ALERTS)
    active_alerts = alerts_data.get('active_alerts', [])
    print(f"\nALERTS:")
    print(f"  Active Alerts: {len(active_alerts)}")
    for alert in active_alerts[:3]:
        print(f"    {alert['alert_type']} - {alert['severity']} - {alert['message'][:50]}...")
    
    # Traces
    traces_data = dashboard.get_dashboard_data(DashboardView.TRACES)
    print(f"\nTRACES:")
    print(f"  Active Traces: {traces_data.get('trace_stats', {}).get('active_count', 0)}")
    print(f"  Total Spans: {traces_data.get('trace_stats', {}).get('total_spans', 0)}")
    
    # Demonstrate detailed views
    print("\n3. Detailed Views:")
    print("-" * 30)
    
    # Get a completed workflow for detail view
    completed_traces = monitor.get_completed_traces(limit=1)
    if completed_traces:
        trace = completed_traces[0]
        workflow_detail = dashboard.get_workflow_detail(trace.workflow_id)
        
        if workflow_detail:
            print(f"\nWORKFLOW DETAIL ({trace.workflow_id[:20]}...):")
            summary = workflow_detail['summary']
            print(f"  Name: {summary['name']}")
            print(f"  Status: {summary['status']}")
            print(f"  Duration: {summary.get('duration_minutes', 0):.2f} minutes")
            print(f"  Steps: {summary['completed_steps']}/{summary['total_steps']}")
            
            print(f"  Steps Detail:")
            for step in workflow_detail.get('steps', []):
                print(f"    {step['agent_name']} - {step['status']} - {step.get('execution_time', 0):.2f}s")
    
    # Demonstrate monitoring statistics
    print("\n4. Monitoring Statistics:")
    print("-" * 30)
    
    stats = monitor.get_monitoring_stats()
    print(f"  Active Traces: {stats['active_traces']}")
    print(f"  Completed Traces: {stats['completed_traces']}")
    print(f"  Active Spans: {stats['active_spans']}")
    print(f"  Active Alerts: {stats['active_alerts']}")
    print(f"  Alert Breakdown: {stats['alert_breakdown']}")
    
    # Demonstrate export functionality
    print("\n5. Data Export:")
    print("-" * 30)
    
    exported_data = dashboard.export_dashboard_data("json")
    export_summary = json.loads(exported_data)
    print(f"  Export Size: {len(exported_data)} characters")
    print(f"  Export Timestamp: {export_summary['export_timestamp']}")
    print(f"  Workflows Exported: {len(export_summary.get('workflows', []))}")
    print(f"  Agents Exported: {len(export_summary.get('agents', []))}")
    
    # Demonstrate real-time features
    print("\n6. Real-time Monitoring:")
    print("-" * 30)
    print("  Starting background workflow for real-time demonstration...")
    
    # Start a long-running workflow in background
    background_task = asyncio.create_task(simulate_workflow_execution(event_manager, assessment))
    
    # Monitor in real-time for a few seconds
    for i in range(5):
        await asyncio.sleep(1)
        current_data = dashboard.get_dashboard_data(DashboardView.OVERVIEW)
        active_workflows = current_data.get('metrics', {}).get('active_workflows', 0)
        print(f"    Time {i+1}s: Active Workflows = {active_workflows}")
    
    # Wait for background task to complete
    await background_task
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETED")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("✓ Comprehensive workflow tracing")
    print("✓ Real-time performance monitoring")
    print("✓ Multi-view dashboard system")
    print("✓ Distributed tracing across agents")
    print("✓ Performance alerting system")
    print("✓ Structured logging with correlation")
    print("✓ Data export capabilities")
    print("✓ Real-time monitoring updates")
    
    print(f"\nLog files generated:")
    print(f"  - logs/monitoring_demo.log (structured JSON logs)")
    print(f"  - Console output (human-readable)")
    
    print(f"\nMonitoring data available via API endpoints:")
    print(f"  - GET /monitoring/dashboard")
    print(f"  - GET /monitoring/workflows")
    print(f"  - GET /monitoring/agents")
    print(f"  - GET /monitoring/performance")
    print(f"  - GET /monitoring/alerts")
    print(f"  - GET /monitoring/traces")


async def main():
    """Main demonstration function."""
    try:
        await demonstrate_monitoring_features()
    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user")
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        print(f"\nError: {e}")
    finally:
        # Cleanup
        from src.infra_mind.orchestration.monitoring import shutdown_workflow_monitoring
        from src.infra_mind.orchestration.dashboard import shutdown_workflow_dashboard
        from src.infra_mind.core.metrics_collector import shutdown_metrics_collection
        
        await shutdown_workflow_dashboard()
        await shutdown_workflow_monitoring()
        await shutdown_metrics_collection()
        
        print("\nCleanup completed")


if __name__ == "__main__":
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Run demonstration
    asyncio.run(main())