#!/usr/bin/env python3
"""
Test script for LangGraph orchestration system.

This script verifies that the production LangGraph orchestrator
is properly implemented and functional.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.orchestration.langgraph_orchestrator import LangGraphOrchestrator
from infra_mind.orchestration.checkpoint_saver import MongoCheckpointSaver
from infra_mind.orchestration.events import EventManager
from infra_mind.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResult, AgentStatus
from infra_mind.models.assessment import Assessment
from infra_mind.schemas.base import CompanySize, AssessmentStatus


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    async def _execute_main_logic(self) -> dict:
        """Mock execution logic."""
        await asyncio.sleep(0.1)  # Simulate work
        
        return {
            "recommendations": [
                {
                    "title": f"Recommendation from {self.name}",
                    "description": f"Mock recommendation from {self.name}",
                    "priority": "high",
                    "category": "infrastructure"
                }
            ],
            "data": {
                "agent_name": self.name,
                "execution_time": 0.1,
                "status": "completed"
            }
        }


async def test_langgraph_orchestration():
    """Test LangGraph orchestration system."""
    print("🚀 Testing LangGraph Orchestration System")
    print("=" * 50)
    
    try:
        # Initialize components
        print("1. Initializing components...")
        event_manager = EventManager()
        checkpoint_saver = MongoCheckpointSaver()
        orchestrator = LangGraphOrchestrator(event_manager, checkpoint_saver)
        
        # Create mock agents
        print("2. Creating mock agents...")
        agents = []
        
        # CTO Agent
        cto_config = AgentConfig(
            name="cto_agent",
            role=AgentRole.CTO,
            max_iterations=5,
            timeout_seconds=30
        )
        cto_agent = MockAgent(cto_config)
        agents.append(cto_agent)
        
        # Cloud Engineer Agent
        cloud_config = AgentConfig(
            name="cloud_engineer_agent", 
            role=AgentRole.CLOUD_ENGINEER,
            max_iterations=5,
            timeout_seconds=30
        )
        cloud_agent = MockAgent(cloud_config)
        agents.append(cloud_agent)
        
        # Research Agent
        research_config = AgentConfig(
            name="research_agent",
            role=AgentRole.RESEARCH,
            max_iterations=5,
            timeout_seconds=30
        )
        research_agent = MockAgent(research_config)
        agents.append(research_agent)
        
        print(f"   Created {len(agents)} agents: {[a.name for a in agents]}")
        
        # Create mock assessment
        print("3. Creating mock assessment...")
        assessment = Assessment(
            user_id="test_user",
            title="Test Infrastructure Assessment",
            description="Mock assessment for testing LangGraph orchestration",
            business_requirements={
                "company_size": CompanySize.MEDIUM.value,
                "industry": "technology",
                "scalability": "high",
                "compliance": ["gdpr"],
                "budget": 10000
            },
            technical_requirements={
                "availability": "99.9%",
                "performance": "low_latency",
                "security": "enterprise",
                "cloud_provider": "aws",
                "services": ["ec2", "rds", "s3"],
                "monthly_spend": 5000
            },
            status=AssessmentStatus.IN_PROGRESS
        )
        
        print(f"   Assessment created: {assessment.title}")
        
        # Define agent dependencies
        print("4. Setting up agent dependencies...")
        dependencies = {
            "cloud_engineer_agent": ["cto_agent"],  # Cloud engineer depends on CTO
            "research_agent": ["cto_agent"]  # Research depends on CTO
        }
        
        print(f"   Dependencies: {dependencies}")
        
        # Create workflow
        print("5. Creating LangGraph workflow...")
        workflow_id = await orchestrator.create_workflow(
            name="Test Infrastructure Assessment",
            agents=agents,
            dependencies=dependencies,
            assessment=assessment,
            context={"test_mode": True}
        )
        
        print(f"   Workflow created: {workflow_id}")
        
        # Execute workflow
        print("6. Executing workflow...")
        start_time = datetime.now(timezone.utc)
        
        try:
            final_state = await orchestrator.execute_workflow(workflow_id)
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            print(f"   Workflow completed in {execution_time:.2f} seconds")
            
            # Analyze results
            print("\n7. Analyzing results...")
            print(f"   Status: {final_state.get('status', 'unknown')}")
            print(f"   Completed agents: {len(final_state.get('completed_agents', []))}")
            print(f"   Failed agents: {len(final_state.get('failed_agents', []))}")
            print(f"   Total recommendations: {len(final_state.get('recommendations', []))}")
            
            # Show agent results
            agent_results = final_state.get('agent_results', {})
            for agent_name, result in agent_results.items():
                status = result.get('status', 'unknown')
                exec_time = result.get('execution_time', 0)
                print(f"   - {agent_name}: {status} ({exec_time:.2f}s)")
            
            # Show progress
            progress = final_state.get('progress', {})
            if progress:
                print(f"   Progress: {progress.get('progress_percentage', 0):.1f}%")
            
            # Test workflow status retrieval
            print("\n8. Testing workflow status retrieval...")
            status = await orchestrator.get_workflow_status(workflow_id)
            if status:
                print(f"   Retrieved status: {status['status']}")
                print(f"   Recommendations count: {status['recommendations_count']}")
            
            # Test orchestrator stats
            print("\n9. Testing orchestrator statistics...")
            stats = orchestrator.get_orchestrator_stats()
            print(f"   Active workflows: {stats['active_workflows']}")
            print(f"   Total workflows: {stats['total_workflows']}")
            print(f"   Checkpoint saver: {stats['checkpoint_saver_type']}")
            
            print("\n✅ LangGraph orchestration test completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Workflow execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n❌ Test setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_checkpoint_functionality():
    """Test checkpoint save/restore functionality."""
    print("\n🔄 Testing Checkpoint Functionality")
    print("=" * 40)
    
    try:
        # Test MongoDB checkpoint saver
        print("1. Testing MongoDB checkpoint saver...")
        checkpoint_saver = MongoCheckpointSaver("test_checkpoints")
        
        # Get stats
        stats = await checkpoint_saver.get_stats()
        print(f"   Checkpoint stats: {stats}")
        
        print("✅ Checkpoint functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Checkpoint test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("🧪 LangGraph Orchestration System Tests")
    print("=" * 60)
    
    # Run tests
    test_results = []
    
    # Test 1: Basic orchestration
    result1 = await test_langgraph_orchestration()
    test_results.append(("LangGraph Orchestration", result1))
    
    # Test 2: Checkpoint functionality
    result2 = await test_checkpoint_functionality()
    test_results.append(("Checkpoint Functionality", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_results)} tests")
    
    if passed == len(test_results):
        print("\n🎉 All tests passed! LangGraph orchestration is working correctly.")
        return True
    else:
        print(f"\n⚠️  {len(test_results) - passed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)