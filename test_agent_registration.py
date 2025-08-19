#!/usr/bin/env python3
"""
Test script to verify agent registration is working.
"""

import asyncio
import logging
from src.infra_mind.agents import agent_factory, agent_registry
from src.infra_mind.agents.base import AgentRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_registration():
    """Test if agents are properly registered and can be created."""
    
    logger.info("🧪 Testing agent registration...")
    
    # List all registered agent types
    registered_types = agent_registry.list_agent_types()
    logger.info(f"📋 Registered agent types: {[str(role) for role in registered_types]}")
    
    # Test creating each agent type
    test_roles = [
        AgentRole.CTO,
        AgentRole.CLOUD_ENGINEER,
        AgentRole.RESEARCH,
        AgentRole.INFRASTRUCTURE,
        AgentRole.COMPLIANCE,
        AgentRole.MLOPS
    ]
    
    created_agents = []
    failed_agents = []
    
    for role in test_roles:
        try:
            logger.info(f"🔧 Creating {role.value} agent...")
            agent = await agent_factory.create_agent(role)
            if agent:
                logger.info(f"✅ Successfully created {role.value} agent: {agent.name}")
                created_agents.append(role.value)
            else:
                logger.error(f"❌ Failed to create {role.value} agent (returned None)")
                failed_agents.append(role.value)
        except Exception as e:
            logger.error(f"❌ Error creating {role.value} agent: {e}")
            failed_agents.append(role.value)
    
    logger.info(f"📊 Results:")
    logger.info(f"  ✅ Successfully created: {len(created_agents)} agents")
    logger.info(f"  ❌ Failed to create: {len(failed_agents)} agents")
    
    if created_agents:
        logger.info(f"  Created agents: {created_agents}")
    if failed_agents:
        logger.info(f"  Failed agents: {failed_agents}")
    
    return len(created_agents) > 0

if __name__ == "__main__":
    success = asyncio.run(test_agent_registration())
    if success:
        print("🎉 Agent registration test PASSED!")
    else:
        print("💥 Agent registration test FAILED!")