"""
AI Agents package for Infra Mind.

Contains all AI agent implementations for infrastructure assessment and recommendations.
"""

from .base import BaseAgent, AgentRegistry, AgentFactory, AgentRole, agent_registry
from .memory import AgentMemory, ConversationMemory
from .tools import AgentToolkit, ToolResult
from .cto_agent import CTOAgent
from .cloud_engineer_agent import CloudEngineerAgent
from .research_agent import ResearchAgent
from .report_generator_agent import ReportGeneratorAgent, Report, ReportSection

# Register agent types
agent_registry.register_agent_type(AgentRole.CTO, CTOAgent)
agent_registry.register_agent_type(AgentRole.CLOUD_ENGINEER, CloudEngineerAgent)
agent_registry.register_agent_type(AgentRole.RESEARCH, ResearchAgent)
agent_registry.register_agent_type(AgentRole.REPORT_GENERATOR, ReportGeneratorAgent)

__all__ = [
    "BaseAgent",
    "AgentRegistry", 
    "AgentFactory",
    "AgentRole",
    "AgentMemory",
    "ConversationMemory",
    "AgentToolkit",
    "ToolResult",
    "CTOAgent",
    "CloudEngineerAgent",
    "ResearchAgent",
    "ReportGeneratorAgent",
    "Report",
    "ReportSection",
    "agent_registry"
]