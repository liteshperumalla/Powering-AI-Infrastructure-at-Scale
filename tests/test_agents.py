"""
Tests for agent framework.

Tests base agent functionality, memory system, and toolkit.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from src.infra_mind.agents.base import (
    BaseAgent, AgentConfig, AgentRole, AgentStatus, AgentResult,
    AgentRegistry, AgentFactory
)
from src.infra_mind.agents.memory import (
    AgentMemory, ConversationMemory, MemoryEntry, WorkingMemory
)
from src.infra_mind.agents.tools import (
    AgentToolkit, ToolResult, ToolStatus, DataProcessingTool,
    CloudAPITool, CalculationTool
)


# Mock agent implementation for testing
class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    async def _execute_main_logic(self) -> dict:
        """Mock implementation."""
        return {
            "recommendations": [
                {"service": "EC2", "reason": "Cost effective"}
            ],
            "data": {"processed": True}
        }


class TestAgentConfig:
    """Test agent configuration."""
    
    def test_agent_config_creation(self):
        """Test creating agent configuration."""
        config = AgentConfig(
            name="test_agent",
            role=AgentRole.CTO,
            version="1.0",
            max_iterations=5,
            timeout_seconds=120,
            tools_enabled=["data_processor", "calculator"]
        )
        
        assert config.name == "test_agent"
        assert config.role == AgentRole.CTO
        assert config.version == "1.0"
        assert config.max_iterations == 5
        assert config.timeout_seconds == 120
        assert "data_processor" in config.tools_enabled
        assert config.memory_enabled is True  # Default
        assert config.metrics_enabled is True  # Default


class TestBaseAgent:
    """Test base agent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        config = AgentConfig(name="test_agent", role=AgentRole.CTO)
        agent = MockAgent(config)
        
        assert agent.name == "test_agent"
        assert agent.role == AgentRole.CTO
        assert agent.status == AgentStatus.IDLE
        assert agent.memory is not None  # Memory enabled by default
        assert agent.toolkit is not None
        assert not agent.is_running
    
    def test_agent_properties(self):
        """Test agent properties."""
        config = AgentConfig(name="test_agent", role=AgentRole.CLOUD_ENGINEER)
        agent = MockAgent(config)
        
        assert agent.name == "test_agent"
        assert agent.role == AgentRole.CLOUD_ENGINEER
        assert agent.execution_time is None  # Not started yet
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        assert any("Role: cloud_engineer" in cap for cap in capabilities)
        assert any("Model: gpt-4" in cap for cap in capabilities)
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self):
        """Test agent health check."""
        config = AgentConfig(name="test_agent", role=AgentRole.CTO)
        agent = MockAgent(config)
        
        health = await agent.health_check()
        
        assert health["agent_name"] == "test_agent"
        assert health["status"] == "idle"
        assert health["role"] == "cto"
        assert health["version"] == "1.0"
        assert health["memory_enabled"] is True
        assert health["current_assessment"] is None
    
    @pytest.mark.asyncio
    async def test_agent_execution_mock(self):
        """Test agent execution with mock assessment."""
        # Disable metrics for testing to avoid database dependency
        config = AgentConfig(name="test_agent", role=AgentRole.CTO, metrics_enabled=False)
        agent = MockAgent(config)
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment_123"
        
        # Execute agent
        result = await agent.execute(mock_assessment)
        
        assert isinstance(result, AgentResult)
        assert result.agent_name == "test_agent"
        assert result.status == AgentStatus.COMPLETED
        assert len(result.recommendations) == 1
        assert result.recommendations[0]["service"] == "EC2"
        assert result.data["processed"] is True
        assert result.execution_time is not None
        assert result.execution_time > 0


class TestAgentRegistry:
    """Test agent registry functionality."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = AgentRegistry()
        
        assert len(registry.list_agent_types()) == 0
        assert len(registry.list_agent_instances()) == 0
    
    def test_register_agent_type(self):
        """Test registering agent types."""
        registry = AgentRegistry()
        
        registry.register_agent_type(AgentRole.CTO, MockAgent)
        
        assert len(registry.list_agent_types()) == 1
        assert "cto" in registry.list_agent_types()
        assert registry.get_agent_type(AgentRole.CTO) == MockAgent
    
    def test_register_agent_instance(self):
        """Test registering agent instances."""
        registry = AgentRegistry()
        config = AgentConfig(name="test_agent", role=AgentRole.CTO)
        agent = MockAgent(config)
        
        registry.register_agent_instance(agent)
        
        assert len(registry.list_agent_instances()) == 1
        assert registry.get_agent_instance(agent.agent_id) == agent
        
        # Test removal
        registry.remove_agent_instance(agent.agent_id)
        assert len(registry.list_agent_instances()) == 0


class TestAgentFactory:
    """Test agent factory functionality."""
    
    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating agents."""
        registry = AgentRegistry()
        registry.register_agent_type(AgentRole.CTO, MockAgent)
        
        factory = AgentFactory(registry)
        
        agent = await factory.create_agent(AgentRole.CTO)
        
        assert agent is not None
        assert isinstance(agent, MockAgent)
        assert agent.role == AgentRole.CTO
        assert len(registry.list_agent_instances()) == 1
    
    @pytest.mark.asyncio
    async def test_create_agent_with_config(self):
        """Test creating agent with custom config."""
        registry = AgentRegistry()
        registry.register_agent_type(AgentRole.CLOUD_ENGINEER, MockAgent)
        
        factory = AgentFactory(registry)
        
        config = AgentConfig(
            name="custom_agent",
            role=AgentRole.CLOUD_ENGINEER,
            max_iterations=20
        )
        
        agent = await factory.create_agent(AgentRole.CLOUD_ENGINEER, config)
        
        assert agent is not None
        assert agent.name == "custom_agent"
        assert agent.config.max_iterations == 20
    
    @pytest.mark.asyncio
    async def test_create_agent_team(self):
        """Test creating agent team."""
        registry = AgentRegistry()
        registry.register_agent_type(AgentRole.CTO, MockAgent)
        registry.register_agent_type(AgentRole.CLOUD_ENGINEER, MockAgent)
        
        factory = AgentFactory(registry)
        
        team = await factory.create_agent_team([AgentRole.CTO, AgentRole.CLOUD_ENGINEER])
        
        assert len(team) == 2
        assert any(agent.role == AgentRole.CTO for agent in team)
        assert any(agent.role == AgentRole.CLOUD_ENGINEER for agent in team)
    
    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check for all agents."""
        registry = AgentRegistry()
        registry.register_agent_type(AgentRole.CTO, MockAgent)
        
        factory = AgentFactory(registry)
        
        # Create some agents
        await factory.create_agent(AgentRole.CTO)
        await factory.create_agent(AgentRole.CTO)
        
        health_status = await factory.health_check_all()
        
        assert health_status["total_agents"] == 2
        assert len(health_status["agents"]) == 2
        assert all(agent["status"] == "idle" for agent in health_status["agents"])


class TestAgentMemory:
    """Test agent memory functionality."""
    
    @pytest.mark.asyncio
    async def test_memory_store_retrieve(self):
        """Test storing and retrieving memory entries."""
        memory = AgentMemory()
        
        entry = MemoryEntry(
            id="test_entry",
            content={"message": "Test memory entry"},
            timestamp=datetime.now(timezone.utc),
            entry_type="test",
            tags=["test", "memory"]
        )
        
        await memory.store(entry)
        
        # Retrieve by query
        results = await memory.retrieve("test")
        assert len(results) == 1
        assert results[0].id == "test_entry"
        
        # Retrieve by type
        results = await memory.retrieve_by_type("test")
        assert len(results) == 1
        
        # Retrieve by tags
        results = await memory.retrieve_by_tags(["memory"])
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_memory_max_entries(self):
        """Test memory max entries limit."""
        memory = AgentMemory(max_entries=3)
        
        # Add more entries than the limit
        for i in range(5):
            entry = MemoryEntry(
                id=f"entry_{i}",
                content={"index": i},
                timestamp=datetime.now(timezone.utc),
                importance=float(i)  # Higher index = higher importance
            )
            await memory.store(entry)
        
        # Should only keep 3 most important entries
        assert len(memory.entries) == 3
        
        # Should keep the most important ones (highest indices)
        entry_ids = [entry.id for entry in memory.entries]
        assert "entry_4" in entry_ids  # Highest importance
        assert "entry_3" in entry_ids
        assert "entry_2" in entry_ids
    
    @pytest.mark.asyncio
    async def test_memory_summary(self):
        """Test memory summary."""
        memory = AgentMemory()
        
        # Add some entries
        for i in range(3):
            entry = MemoryEntry(
                id=f"entry_{i}",
                content={"index": i},
                timestamp=datetime.now(timezone.utc),
                entry_type="test" if i % 2 == 0 else "other"
            )
            await memory.store(entry)
        
        summary = await memory.get_summary()
        
        assert summary["total_entries"] == 3
        assert "test" in summary["entry_types"]
        assert "other" in summary["entry_types"]
        assert summary["entry_types"]["test"] == 2  # entries 0 and 2
        assert summary["entry_types"]["other"] == 1  # entry 1


class TestConversationMemory:
    """Test conversation memory functionality."""
    
    @pytest.mark.asyncio
    async def test_conversation_turns(self):
        """Test conversation turn tracking."""
        memory = ConversationMemory()
        
        await memory.add_user_message("Hello, I need help with infrastructure")
        await memory.add_agent_message("I'd be happy to help! What's your company size?")
        await memory.add_user_message("We're a medium-sized company")
        
        context = await memory.get_conversation_context()
        
        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "agent"
        assert context[2]["role"] == "user"
        assert "infrastructure" in context[0]["message"]
    
    @pytest.mark.asyncio
    async def test_conversation_context_window(self):
        """Test conversation context window."""
        memory = ConversationMemory(context_window=2)
        
        # Add more turns than the context window
        for i in range(5):
            await memory.add_user_message(f"Message {i}")
        
        context = await memory.get_conversation_context()
        
        # Should only return the last 2 turns
        assert len(context) == 2
        assert context[0]["message"] == "Message 3"
        assert context[1]["message"] == "Message 4"
    
    @pytest.mark.asyncio
    async def test_conversation_summary(self):
        """Test conversation summary."""
        memory = ConversationMemory()
        
        await memory.add_user_message("Hello")
        await memory.add_agent_message("Hi there!")
        await memory.add_user_message("How are you?")
        
        summary = await memory.get_conversation_summary()
        
        assert "3 turns" in summary
        assert "2 user" in summary
        assert "1 agent" in summary


class TestWorkingMemory:
    """Test working memory functionality."""
    
    def test_working_memory_operations(self):
        """Test working memory basic operations."""
        memory = WorkingMemory()
        
        # Test set/get
        memory.set("key1", "value1")
        assert memory.get("key1") == "value1"
        assert memory.get("nonexistent", "default") == "default"
        
        # Test notes
        memory.add_note("This is a test note")
        assert len(memory.scratch_pad) == 1
        assert "test note" in memory.scratch_pad[0]
        
        # Test intermediate results
        memory.set_intermediate_result("step1", {"result": "success"})
        result = memory.get_intermediate_result("step1")
        assert result["result"] == "success"
        
        # Test summary
        summary = memory.get_summary()
        assert "key1" in summary["data_keys"]
        assert summary["notes_count"] == 1
        assert "step1" in summary["intermediate_results"]
        
        # Test clear
        memory.clear()
        assert len(memory.data) == 0
        assert len(memory.scratch_pad) == 0
        assert len(memory.intermediate_results) == 0


class TestAgentToolkit:
    """Test agent toolkit functionality."""
    
    @pytest.mark.asyncio
    async def test_toolkit_initialization(self):
        """Test toolkit initialization."""
        toolkit = AgentToolkit(["data_processor", "calculator"])
        
        assert len(toolkit.tools) == 2
        assert "data_processor" in toolkit.tools
        assert "calculator" in toolkit.tools
        assert "cloud_api" not in toolkit.tools  # Not enabled
    
    @pytest.mark.asyncio
    async def test_use_data_processor_tool(self):
        """Test using data processor tool."""
        toolkit = AgentToolkit(["data_processor"])
        
        # Mock assessment for initialization
        mock_assessment = Mock()
        mock_assessment.id = "test_assessment"
        await toolkit.initialize(mock_assessment, {})
        
        # Test data analysis
        test_data = {
            "business_requirements": {
                "company_size": "medium",
                "industry": "technology"
            },
            "technical_requirements": {
                "workload_types": ["web_application"],
                "expected_users": 1000
            }
        }
        
        result = await toolkit.use_tool("data_processor", data=test_data, operation="analyze")
        
        assert result.is_success
        assert result.tool_name == "data_processor"
        assert "data_size" in result.data
        assert "insights" in result.data
        assert len(result.data["insights"]) > 0
    
    @pytest.mark.asyncio
    async def test_use_calculator_tool(self):
        """Test using calculator tool."""
        toolkit = AgentToolkit(["calculator"])
        
        # Mock assessment for initialization
        mock_assessment = Mock()
        await toolkit.initialize(mock_assessment, {})
        
        # Test cost estimation
        result = await toolkit.use_tool(
            "calculator",
            operation="cost_estimate",
            base_cost=200,
            users=2000,
            scaling_factor=1.5
        )
        
        assert result.is_success
        assert result.tool_name == "calculator"
        assert "monthly_cost" in result.data
        assert "annual_cost" in result.data
        assert result.data["monthly_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_use_cloud_api_tool(self):
        """Test using cloud API tool."""
        toolkit = AgentToolkit(["cloud_api"])
        
        # Mock assessment for initialization
        mock_assessment = Mock()
        await toolkit.initialize(mock_assessment, {})
        
        # Test AWS EC2 API call
        result = await toolkit.use_tool(
            "cloud_api",
            provider="aws",
            service="ec2",
            operation="describe_instances"
        )
        
        assert result.is_success
        assert result.tool_name == "cloud_api"
        assert "instances" in result.data
        assert toolkit.api_call_count == 1
    
    @pytest.mark.asyncio
    async def test_use_nonexistent_tool(self):
        """Test using a tool that doesn't exist."""
        toolkit = AgentToolkit([])
        
        result = await toolkit.use_tool("nonexistent_tool")
        
        assert not result.is_success
        assert result.status == ToolStatus.ERROR
        assert "not available" in result.error
    
    def test_toolkit_usage_stats(self):
        """Test toolkit usage statistics."""
        toolkit = AgentToolkit(["data_processor", "calculator"])
        
        stats = toolkit.get_usage_stats()
        
        assert "enabled_tools" in stats
        assert "api_calls_made" in stats
        assert "tool_usage" in stats
        assert len(stats["enabled_tools"]) == 2
        assert stats["api_calls_made"] == 0  # No API calls made yet
    
    def test_list_available_tools(self):
        """Test listing available tools."""
        toolkit = AgentToolkit(["data_processor"])
        
        tools = toolkit.list_available_tools()
        
        assert len(tools) == 1
        assert tools[0]["name"] == "data_processor"
        assert "description" in tools[0]
        assert "usage_count" in tools[0]