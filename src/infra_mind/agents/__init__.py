"""
AI Agents package for Infra Mind.

Contains all AI agent implementations for infrastructure assessment and recommendations.
"""

from .base import BaseAgent, AgentRegistry, AgentFactory, AgentRole, agent_registry, agent_factory
from .memory import AgentMemory, ConversationMemory
from .tools import AgentToolkit, ToolResult
from .cto_agent import CTOAgent
from .cloud_engineer_agent import CloudEngineerAgent
from .research_agent import ResearchAgent
from .report_generator_agent import ReportGeneratorAgent
from .mlops_agent import MLOpsAgent
from .infrastructure_agent import InfrastructureAgent
from .compliance_agent import ComplianceAgent
from .web_research_agent import WebResearchAgent
from .simulation_agent import SimulationAgent
from .chatbot_agent import ChatbotAgent
from .ai_consultant_agent import AIConsultantAgent

# Register agent types
agent_registry.register_agent_type(AgentRole.CTO, CTOAgent)
agent_registry.register_agent_type(AgentRole.CLOUD_ENGINEER, CloudEngineerAgent)
agent_registry.register_agent_type(AgentRole.RESEARCH, ResearchAgent)
agent_registry.register_agent_type(AgentRole.REPORT_GENERATOR, ReportGeneratorAgent)
agent_registry.register_agent_type(AgentRole.MLOPS, MLOpsAgent)
agent_registry.register_agent_type(AgentRole.INFRASTRUCTURE, InfrastructureAgent)
agent_registry.register_agent_type(AgentRole.COMPLIANCE, ComplianceAgent)
agent_registry.register_agent_type(AgentRole.WEB_RESEARCH, WebResearchAgent)
agent_registry.register_agent_type(AgentRole.SIMULATION, SimulationAgent)
agent_registry.register_agent_type(AgentRole.CHATBOT, ChatbotAgent)
agent_registry.register_agent_type(AgentRole.AI_CONSULTANT, AIConsultantAgent)

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
    "MLOpsAgent",
    "InfrastructureAgent",
    "ComplianceAgent",
    "WebResearchAgent",
    "SimulationAgent",
    "ChatbotAgent",
    # "AIConsultantAgent",
    "Report",
    "ReportSection",
    "agent_registry",
    "agent_factory"
]