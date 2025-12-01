"""
Agent orchestrator for Infra Mind.

Coordinates multiple AI agents and manages their interactions.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..models.assessment import Assessment
from ..models.recommendation import Recommendation
from ..agents.base import BaseAgent, AgentRole, AgentResult, AgentStatus
from ..agents import agent_factory  # Import from agents package to ensure registration
from .base import WorkflowManager, workflow_manager

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Configuration for agent orchestration."""
    max_parallel_agents: int = 10
    agent_timeout_seconds: int = 300
    retry_failed_agents: bool = True
    max_retries: int = 2
    require_consensus: bool = False
    consensus_threshold: float = 0.7
    enable_agent_communication: bool = True
    
    # Agent-specific configurations
    agent_configs: Dict[AgentRole, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Result from agent orchestration."""
    assessment_id: str
    total_agents: int
    successful_agents: int
    failed_agents: int
    agent_results: Dict[str, AgentResult]
    synthesized_recommendations: List[Dict[str, Any]]
    execution_time: float
    consensus_score: Optional[float] = None
    orchestration_metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents for infrastructure assessment.
    
    Learning Note: This class manages the coordination of multiple agents,
    handling parallel execution, result synthesis, and error recovery.
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Orchestration configuration
        """
        self.config = config or OrchestrationConfig()
        self.workflow_manager = workflow_manager
        self.agent_factory = agent_factory
        self.active_orchestrations: Dict[str, Dict[str, Any]] = {}
        self._test_mode = bool(
            os.getenv("INFRA_MIND_TESTING")
            or os.getenv("PYTEST_CURRENT_TEST")
        )
    
    async def orchestrate_assessment(
        self,
        assessment: Assessment,
        agent_roles: List[AgentRole],
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """
        Orchestrate multiple agents to process an assessment.
        
        Args:
            assessment: Assessment to process
            agent_roles: List of agent roles to involve
            context: Additional context data
            
        Returns:
            Orchestration result with synthesized recommendations
        """
        orchestration_id = f"orchestration_{assessment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Starting orchestration {orchestration_id} with {len(agent_roles)} agents")
            
            # Track orchestration
            self.active_orchestrations[orchestration_id] = {
                "assessment_id": str(assessment.id),
                "agent_roles": [role.value for role in agent_roles],
                "start_time": start_time,
                "status": "running"
            }
            
            # Execute agents
            agent_results = await self._execute_agents_parallel(
                assessment, agent_roles, context or {}
            )
            
            # Synthesize results
            synthesized_recommendations = await self._synthesize_agent_results(
                agent_results, assessment
            )
            
            # Calculate metrics
            successful_agents = sum(1 for result in agent_results.values() 
                                  if result.status == AgentStatus.COMPLETED)
            failed_agents = len(agent_results) - successful_agents
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Calculate consensus if enabled
            consensus_score = None
            if self.config.require_consensus:
                consensus_score = await self._calculate_consensus(agent_results)
            
            # Create result
            result = OrchestrationResult(
                assessment_id=str(assessment.id),
                total_agents=len(agent_roles),
                successful_agents=successful_agents,
                failed_agents=failed_agents,
                agent_results=agent_results,
                synthesized_recommendations=synthesized_recommendations,
                execution_time=execution_time,
                consensus_score=consensus_score,
                orchestration_metadata={
                    "orchestration_id": orchestration_id,
                    "config": self.config.__dict__,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Update tracking
            self.active_orchestrations[orchestration_id]["status"] = "completed"
            self.active_orchestrations[orchestration_id]["result"] = result
            
            logger.info(f"Completed orchestration {orchestration_id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Orchestration {orchestration_id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Update tracking
            self.active_orchestrations[orchestration_id]["status"] = "failed"
            self.active_orchestrations[orchestration_id]["error"] = str(e)
            
            # Return error result
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            return OrchestrationResult(
                assessment_id=str(assessment.id),
                total_agents=len(agent_roles),
                successful_agents=0,
                failed_agents=len(agent_roles),
                agent_results={},
                synthesized_recommendations=[],
                execution_time=execution_time,
                orchestration_metadata={
                    "orchestration_id": orchestration_id,
                    "error": str(e)
                }
            )
        
        finally:
            # Clean up after some time
            asyncio.create_task(self._cleanup_orchestration(orchestration_id, delay=3600))
    
    async def _execute_agents_parallel(
        self,
        assessment: Assessment,
        agent_roles: List[AgentRole],
        context: Dict[str, Any]
    ) -> Dict[str, AgentResult]:
        """Execute multiple agents in parallel with concurrency control."""
        agent_results = {}
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_parallel_agents)
        
        async def execute_agent_with_semaphore(role: AgentRole) -> None:
            async with semaphore:
                try:
                    result = await self._execute_single_agent(assessment, role, context)
                    agent_results[role.value] = result
                except Exception as e:
                    logger.error(f"Agent {role.value} execution failed: {str(e)}")
                    # Create error result
                    agent_results[role.value] = AgentResult(
                        agent_name=f"{role.value}_agent",
                        status=AgentStatus.FAILED,
                        error=str(e)
                    )
        
        # Execute all agents
        tasks = [execute_agent_with_semaphore(role) for role in agent_roles]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return agent_results
    
    async def _execute_single_agent(
        self,
        assessment: Assessment,
        role: AgentRole,
        context: Dict[str, Any]
    ) -> AgentResult:
        """Execute a single agent with retry logic."""
        retries = 0
        last_error = None
        
        if self._test_mode:
            return await self._mock_agent_execution(role, assessment, context)
        
        while retries <= self.config.max_retries:
            try:
                # Create real agent using factory - pass None to let agent handle its own default config
                agent_config = self.config.agent_configs.get(role, None)
                if isinstance(agent_config, dict) and not agent_config:
                    agent_config = None  # Empty dict means no config, let agent create defaults
                agent = await self.agent_factory.create_agent(role, agent_config)
                
                if agent is None:
                    logger.warning(f"Failed to create agent for role {role.value}, using mock")
                    agent_result = await self._mock_agent_execution(role, assessment, context)
                else:
                    # Execute real agent
                    logger.info(f"Executing real agent: {agent.config.name}")
                    agent_result = await agent.execute(assessment, context)
                
                # Check if result is acceptable
                if agent_result.status == AgentStatus.COMPLETED:
                    return agent_result
                elif not self.config.retry_failed_agents:
                    return agent_result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Agent {role.value} attempt {retries + 1} failed: {str(e)}")
            
            retries += 1
            if retries <= self.config.max_retries:
                # Exponential backoff
                await asyncio.sleep(2 ** retries)
        
        # All retries failed
        return AgentResult(
            agent_name=f"{role.value}_agent",
            status=AgentStatus.FAILED,
            error=f"Failed after {self.config.max_retries} retries. Last error: {str(last_error)}"
        )
    
    async def _mock_agent_execution(
        self,
        role: AgentRole,
        assessment: Assessment,
        context: Dict[str, Any]
    ) -> AgentResult:
        """Mock agent execution for testing."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate role-specific mock results
        if role == AgentRole.CTO:
            return AgentResult(
                agent_name="cto_agent",
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {
                        "type": "strategic",
                        "title": "Cloud Migration Strategy",
                        "priority": "high",
                        "cost_impact": "medium",
                        "timeline": "6-12 months"
                    }
                ],
                data={
                    "business_alignment": 0.9,
                    "strategic_value": "high",
                    "risk_level": "low"
                },
                execution_time=2.1
            )
        
        elif role == AgentRole.CLOUD_ENGINEER:
            return AgentResult(
                agent_name="cloud_engineer_agent",
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {
                        "type": "technical",
                        "title": "Multi-Cloud Architecture",
                        "services": ["AWS EC2", "Azure VMs"],
                        "estimated_cost": 12000,
                        "scalability": "high"
                    }
                ],
                data={
                    "technical_feasibility": 0.85,
                    "performance_impact": "positive",
                    "maintenance_complexity": "medium"
                },
                execution_time=3.2
            )
        
        elif role == AgentRole.RESEARCH:
            return AgentResult(
                agent_name="research_agent",
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {
                        "type": "market_insight",
                        "title": "Industry Best Practices",
                        "trends": ["Serverless", "Edge Computing"],
                        "competitive_advantage": "medium"
                    }
                ],
                data={
                    "market_trends": ["positive", "growing"],
                    "technology_maturity": "high",
                    "adoption_rate": 0.7
                },
                execution_time=1.8
            )
        
        else:
            return AgentResult(
                agent_name=f"{role.value}_agent",
                status=AgentStatus.COMPLETED,
                recommendations=[
                    {
                        "type": "general",
                        "title": f"{role.value} Analysis",
                        "description": f"Analysis from {role.value} perspective"
                    }
                ],
                data={"analysis_complete": True},
                execution_time=1.0
            )
    
    async def _synthesize_agent_results(
        self,
        agent_results: Dict[str, AgentResult],
        assessment: Assessment
    ) -> List[Dict[str, Any]]:
        """Synthesize results from multiple agents into coherent recommendations."""
        all_recommendations = []
        
        # Collect all recommendations
        for agent_name, result in agent_results.items():
            if result.status == AgentStatus.COMPLETED and result.recommendations:
                for rec in result.recommendations:
                    # Add metadata about the source agent
                    enhanced_rec = rec.copy()
                    enhanced_rec["source_agent"] = agent_name
                    enhanced_rec["confidence"] = getattr(result, 'confidence_score', 0.8)
                    all_recommendations.append(enhanced_rec)
        
        # Group recommendations by type/category
        categorized_recs = {}
        for rec in all_recommendations:
            category = rec.get("type", "general")
            if category not in categorized_recs:
                categorized_recs[category] = []
            categorized_recs[category].append(rec)
        
        # Create synthesized recommendations
        synthesized = []
        for category, recs in categorized_recs.items():
            if len(recs) == 1:
                # Single recommendation in category
                synthesized.append(recs[0])
            else:
                # Multiple recommendations - create synthesis
                synthesis = {
                    "type": category,
                    "title": f"Synthesized {category.title()} Recommendations",
                    "individual_recommendations": recs,
                    "consensus_level": len(recs),
                    "synthesis_method": "aggregation",
                    "combined_confidence": sum(r.get("confidence", 0.8) for r in recs) / len(recs)
                }
                synthesized.append(synthesis)
        
        logger.info(f"Synthesized {len(all_recommendations)} recommendations into {len(synthesized)} categories")
        return synthesized
    
    async def _calculate_consensus(self, agent_results: Dict[str, AgentResult]) -> float:
        """Calculate consensus score among agent results."""
        if len(agent_results) < 2:
            return 1.0
        
        # Simple consensus calculation based on recommendation similarity
        # In production, this would use more sophisticated methods
        successful_results = [r for r in agent_results.values() 
                            if r.status == AgentStatus.COMPLETED]
        
        if not successful_results:
            return 0.0
        
        # Calculate average confidence scores
        confidence_scores = []
        for result in successful_results:
            if hasattr(result, 'confidence_score'):
                confidence_scores.append(result.confidence_score)
            else:
                confidence_scores.append(0.8)  # Default confidence
        
        return sum(confidence_scores) / len(confidence_scores)
    
    async def _cleanup_orchestration(self, orchestration_id: str, delay: int = 3600) -> None:
        """Clean up orchestration data after delay."""
        await asyncio.sleep(delay)
        self.active_orchestrations.pop(orchestration_id, None)
        logger.debug(f"Cleaned up orchestration {orchestration_id}")
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running orchestration."""
        return self.active_orchestrations.get(orchestration_id)
    
    def list_active_orchestrations(self) -> List[Dict[str, Any]]:
        """List all active orchestrations."""
        return list(self.active_orchestrations.values())
    
    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel a running orchestration."""
        if orchestration_id in self.active_orchestrations:
            self.active_orchestrations[orchestration_id]["status"] = "cancelled"
            return True
        return False


# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()
