"""
Agent resource management system for production orchestration.

Manages resource allocation, queue management, and load balancing
for concurrent agent execution in multi-agent workflows.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import uuid
import psutil

from ..core.metrics_collector import get_metrics_collector
from ..agents.base import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Types of resources managed by the system."""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    LLM_TOKENS = "llm_tokens"
    CLOUD_API_CALLS = "cloud_api_calls"


@dataclass
class ResourceLimits:
    """Resource limits for agent execution."""
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 1024
    max_concurrent_agents: int = 5
    max_llm_tokens_per_minute: int = 10000
    max_cloud_api_calls_per_minute: int = 100


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    cpu_percent: float = 0.0
    memory_mb: int = 0
    active_agents: int = 0
    llm_tokens_used: int = 0
    cloud_api_calls_used: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentResourceRequest:
    """Resource request for agent execution."""
    agent_id: str
    agent_name: str
    workflow_id: str
    estimated_cpu_percent: float = 10.0
    estimated_memory_mb: int = 256
    estimated_llm_tokens: int = 1000
    estimated_cloud_api_calls: int = 10
    priority: int = 1  # 1 = highest, 5 = lowest
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResourceManager:
    """
    Resource manager for agent execution.
    
    Provides resource allocation, queue management, and load balancing
    for concurrent agent execution in production environments.
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        Initialize resource manager.
        
        Args:
            limits: Resource limits configuration
        """
        self.limits = limits or ResourceLimits()
        self.current_usage = ResourceUsage()
        self.metrics_collector = get_metrics_collector()
        
        # Resource tracking
        self.active_agents: Dict[str, AgentResourceRequest] = {}
        self.resource_queue: List[AgentResourceRequest] = []
        self.completed_agents: Set[str] = set()
        
        # Performance monitoring
        self.resource_history: List[ResourceUsage] = []
        self.max_history_size = 1000
        
        # Locks for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("Agent resource manager initialized")
    
    async def request_resources(self, request: AgentResourceRequest) -> bool:
        """
        Request resources for agent execution.
        
        Args:
            request: Resource request details
            
        Returns:
            True if resources allocated immediately, False if queued
        """
        async with self._lock:
            logger.info(f"Resource request from agent {request.agent_name} (workflow: {request.workflow_id})")
            
            # Check if resources are available
            if await self._can_allocate_resources(request):
                # Allocate resources immediately
                await self._allocate_resources(request)
                logger.info(f"Resources allocated immediately for agent {request.agent_name}")
                return True
            else:
                # Add to queue
                self._add_to_queue(request)
                logger.info(f"Agent {request.agent_name} queued for resources (position: {len(self.resource_queue)})")
                return False
    
    async def release_resources(self, agent_id: str) -> None:
        """
        Release resources after agent completion.
        
        Args:
            agent_id: ID of the agent releasing resources
        """
        async with self._lock:
            if agent_id in self.active_agents:
                request = self.active_agents.pop(agent_id)
                
                # Update resource usage
                self.current_usage.cpu_percent -= request.estimated_cpu_percent
                self.current_usage.memory_mb -= request.estimated_memory_mb
                self.current_usage.active_agents -= 1
                
                # Mark as completed
                self.completed_agents.add(agent_id)
                
                logger.info(f"Resources released for agent {request.agent_name}")
                
                # Try to allocate resources to queued agents
                await self._process_queue()
                
                # Record metrics
                await self._record_resource_metrics()
    
    async def _can_allocate_resources(self, request: AgentResourceRequest) -> bool:
        """Check if resources can be allocated for the request."""
        # Update current system usage
        await self._update_system_usage()
        
        # Check CPU limit
        if (self.current_usage.cpu_percent + request.estimated_cpu_percent) > self.limits.max_cpu_percent:
            return False
        
        # Check memory limit
        if (self.current_usage.memory_mb + request.estimated_memory_mb) > self.limits.max_memory_mb:
            return False
        
        # Check concurrent agents limit
        if self.current_usage.active_agents >= self.limits.max_concurrent_agents:
            return False
        
        # Check LLM token rate limit
        if self._check_rate_limit(ResourceType.LLM_TOKENS, request.estimated_llm_tokens):
            return False
        
        # Check cloud API rate limit
        if self._check_rate_limit(ResourceType.CLOUD_API_CALLS, request.estimated_cloud_api_calls):
            return False
        
        return True
    
    async def _allocate_resources(self, request: AgentResourceRequest) -> None:
        """Allocate resources for the request."""
        # Update resource usage
        self.current_usage.cpu_percent += request.estimated_cpu_percent
        self.current_usage.memory_mb += request.estimated_memory_mb
        self.current_usage.active_agents += 1
        self.current_usage.llm_tokens_used += request.estimated_llm_tokens
        self.current_usage.cloud_api_calls_used += request.estimated_cloud_api_calls
        self.current_usage.last_updated = datetime.now(timezone.utc)
        
        # Track active agent
        self.active_agents[request.agent_id] = request
        
        # Record allocation
        await self._record_resource_allocation(request)
    
    def _add_to_queue(self, request: AgentResourceRequest) -> None:
        """Add request to the resource queue with priority ordering."""
        # Insert based on priority (lower number = higher priority)
        inserted = False
        for i, queued_request in enumerate(self.resource_queue):
            if request.priority < queued_request.priority:
                self.resource_queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            self.resource_queue.append(request)
    
    async def _process_queue(self) -> None:
        """Process queued resource requests."""
        if not self.resource_queue:
            return
        
        # Try to allocate resources to queued requests
        allocated_requests = []
        
        for request in self.resource_queue[:]:  # Copy to avoid modification during iteration
            if await self._can_allocate_resources(request):
                await self._allocate_resources(request)
                allocated_requests.append(request)
                logger.info(f"Queued agent {request.agent_name} allocated resources")
        
        # Remove allocated requests from queue
        for request in allocated_requests:
            self.resource_queue.remove(request)
    
    async def _update_system_usage(self) -> None:
        """Update current system resource usage."""
        try:
            # Get system CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_mb = (memory.total - memory.available) // (1024 * 1024)
            
            # Update usage (blend with estimated usage)
            self.current_usage.cpu_percent = max(cpu_percent, self.current_usage.cpu_percent)
            self.current_usage.memory_mb = max(memory_mb, self.current_usage.memory_mb)
            
        except Exception as e:
            logger.warning(f"Error updating system usage: {str(e)}")
    
    def _check_rate_limit(self, resource_type: ResourceType, requested_amount: int) -> bool:
        """Check if rate limit would be exceeded."""
        # Simple rate limiting - in production, use more sophisticated algorithms
        current_time = datetime.now(timezone.utc)
        
        if resource_type == ResourceType.LLM_TOKENS:
            # Check tokens per minute
            if self.current_usage.llm_tokens_used + requested_amount > self.limits.max_llm_tokens_per_minute:
                return True
        
        elif resource_type == ResourceType.CLOUD_API_CALLS:
            # Check API calls per minute
            if self.current_usage.cloud_api_calls_used + requested_amount > self.limits.max_cloud_api_calls_per_minute:
                return True
        
        return False
    
    async def _record_resource_allocation(self, request: AgentResourceRequest) -> None:
        """Record resource allocation metrics."""
        try:
            await self.metrics_collector.record_resource_allocation(
                agent_name=request.agent_name,
                workflow_id=request.workflow_id,
                cpu_allocated=request.estimated_cpu_percent,
                memory_allocated=request.estimated_memory_mb,
                tokens_allocated=request.estimated_llm_tokens,
                api_calls_allocated=request.estimated_cloud_api_calls
            )
        except Exception as e:
            logger.warning(f"Error recording resource allocation metrics: {str(e)}")
    
    async def _record_resource_metrics(self) -> None:
        """Record current resource usage metrics."""
        try:
            await self.metrics_collector.record_resource_usage(
                cpu_percent=self.current_usage.cpu_percent,
                memory_mb=self.current_usage.memory_mb,
                active_agents=self.current_usage.active_agents,
                queued_agents=len(self.resource_queue),
                llm_tokens_used=self.current_usage.llm_tokens_used,
                cloud_api_calls_used=self.current_usage.cloud_api_calls_used
            )
            
            # Store in history
            self.resource_history.append(ResourceUsage(
                cpu_percent=self.current_usage.cpu_percent,
                memory_mb=self.current_usage.memory_mb,
                active_agents=self.current_usage.active_agents,
                llm_tokens_used=self.current_usage.llm_tokens_used,
                cloud_api_calls_used=self.current_usage.cloud_api_calls_used,
                last_updated=datetime.now(timezone.utc)
            ))
            
            # Limit history size
            if len(self.resource_history) > self.max_history_size:
                self.resource_history = self.resource_history[-self.max_history_size:]
                
        except Exception as e:
            logger.warning(f"Error recording resource metrics: {str(e)}")
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status."""
        await self._update_system_usage()
        
        return {
            "current_usage": {
                "cpu_percent": self.current_usage.cpu_percent,
                "memory_mb": self.current_usage.memory_mb,
                "active_agents": self.current_usage.active_agents,
                "llm_tokens_used": self.current_usage.llm_tokens_used,
                "cloud_api_calls_used": self.current_usage.cloud_api_calls_used,
                "last_updated": self.current_usage.last_updated.isoformat()
            },
            "limits": {
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_memory_mb": self.limits.max_memory_mb,
                "max_concurrent_agents": self.limits.max_concurrent_agents,
                "max_llm_tokens_per_minute": self.limits.max_llm_tokens_per_minute,
                "max_cloud_api_calls_per_minute": self.limits.max_cloud_api_calls_per_minute
            },
            "queue": {
                "queued_requests": len(self.resource_queue),
                "queue_details": [
                    {
                        "agent_name": req.agent_name,
                        "workflow_id": req.workflow_id,
                        "priority": req.priority,
                        "wait_time": (datetime.now(timezone.utc) - req.created_at).total_seconds()
                    }
                    for req in self.resource_queue
                ]
            },
            "active_agents": [
                {
                    "agent_name": req.agent_name,
                    "workflow_id": req.workflow_id,
                    "cpu_allocated": req.estimated_cpu_percent,
                    "memory_allocated": req.estimated_memory_mb,
                    "execution_time": (datetime.now(timezone.utc) - req.created_at).total_seconds()
                }
                for req in self.active_agents.values()
            ],
            "performance": {
                "total_completed": len(self.completed_agents),
                "utilization": {
                    "cpu": (self.current_usage.cpu_percent / self.limits.max_cpu_percent) * 100,
                    "memory": (self.current_usage.memory_mb / self.limits.max_memory_mb) * 100,
                    "agents": (self.current_usage.active_agents / self.limits.max_concurrent_agents) * 100
                }
            }
        }
    
    async def optimize_resource_allocation(self) -> Dict[str, Any]:
        """Optimize resource allocation based on current usage patterns."""
        optimization_results = {
            "recommendations": [],
            "adjustments_made": [],
            "performance_impact": {}
        }
        
        # Analyze resource usage patterns
        if len(self.resource_history) > 10:
            recent_usage = self.resource_history[-10:]
            avg_cpu = sum(usage.cpu_percent for usage in recent_usage) / len(recent_usage)
            avg_memory = sum(usage.memory_mb for usage in recent_usage) / len(recent_usage)
            
            # CPU optimization
            if avg_cpu < self.limits.max_cpu_percent * 0.5:
                optimization_results["recommendations"].append({
                    "type": "increase_concurrent_agents",
                    "current": self.limits.max_concurrent_agents,
                    "recommended": min(self.limits.max_concurrent_agents + 2, 10),
                    "reason": f"CPU utilization is low ({avg_cpu:.1f}%), can handle more concurrent agents"
                })
            elif avg_cpu > self.limits.max_cpu_percent * 0.9:
                optimization_results["recommendations"].append({
                    "type": "decrease_concurrent_agents",
                    "current": self.limits.max_concurrent_agents,
                    "recommended": max(self.limits.max_concurrent_agents - 1, 1),
                    "reason": f"CPU utilization is high ({avg_cpu:.1f}%), should reduce concurrent agents"
                })
            
            # Memory optimization
            if avg_memory > self.limits.max_memory_mb * 0.8:
                optimization_results["recommendations"].append({
                    "type": "increase_memory_limit",
                    "current": self.limits.max_memory_mb,
                    "recommended": int(self.limits.max_memory_mb * 1.2),
                    "reason": f"Memory usage is high ({avg_memory:.0f}MB), consider increasing limit"
                })
        
        # Queue analysis
        if len(self.resource_queue) > 5:
            optimization_results["recommendations"].append({
                "type": "scale_resources",
                "reason": f"Queue has {len(self.resource_queue)} waiting agents, consider scaling resources"
            })
        
        return optimization_results
    
    async def cleanup_completed_agents(self, max_age_hours: int = 1) -> int:
        """Clean up old completed agent records."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        # Clean up completed agents (in production, this would be more sophisticated)
        initial_count = len(self.completed_agents)
        # For now, just clear all completed agents older than max_age_hours
        # In production, you'd track completion times
        
        cleaned_count = 0
        if initial_count > 100:  # Only clean if we have many completed agents
            self.completed_agents.clear()
            cleaned_count = initial_count
            logger.info(f"Cleaned up {cleaned_count} completed agent records")
        
        return cleaned_count


# Global resource manager instance
_resource_manager: Optional[AgentResourceManager] = None


def get_resource_manager() -> AgentResourceManager:
    """Get the global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = AgentResourceManager()
    return _resource_manager


def initialize_resource_manager(limits: Optional[ResourceLimits] = None) -> AgentResourceManager:
    """Initialize the global resource manager."""
    global _resource_manager
    _resource_manager = AgentResourceManager(limits)
    return _resource_manager