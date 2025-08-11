#!/usr/bin/env python3
"""
Quick test to identify web_search_client issue.
"""

import asyncio
import sys
import traceback
sys.path.append('src')

async def test_agent_creation():
    """Test agent creation to find web_search_client issue."""
    try:
        from infra_mind.agents.base import AgentRole, agent_factory
        
        print("🧪 Testing agent creation...")
        agent = await agent_factory.create_agent(AgentRole.INFRASTRUCTURE, None)
        
        if agent:
            print(f"✅ Agent created: {agent.name}")
            
            # Try to access web_search_client to trigger the error
            try:
                _ = agent.web_search_client
                print("✅ web_search_client accessible")
            except AttributeError as e:
                print(f"❌ Found web_search_client issue: {e}")
                return str(e)
        else:
            print("❌ Failed to create agent")
            
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return str(e)

if __name__ == "__main__":
    result = asyncio.run(test_agent_creation())
    if result and 'web_search_client' in result:
        print(f"\n🔍 IDENTIFIED ISSUE: {result}")