"""
Scalability Management Service for Infra Mind.

Implements load balancing for agent distribution, auto-scaling policies,
resource monitoring and capacity planning, and cost optimization features.
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ..models.metrics import Metric, MetricType, MetricCategory
from ..core.config import get_settings
from ..core.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESOURCE_BASED = "resource_based"
    RESPONSE_TIME_BASED = "response_time_based"


class ScalingDirection(str, Enum):
    """Scaling directions."""
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class AgentInstance:
    """Represents an agent instance in the load balancer."""
    instance_id: str
    agent_type: str
    is_busy: bool = False
    current_load: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    weight: float = 1.0
    health_score: float = 1.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def utilization(self) -> float:
        """Calculate utilization score."""
        base_score = self.current_load
        if self.avg_response_time > 0:
            # Penalize slow response times
            time_penalty = min(self.avg_response_time / 1000, 0.5)  # Max 50% penalty
            base_score += time_penalty
        return min(base_score, 1.0)


@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration."""
    agent_type: str
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 70.0
    target_utilization_percent: float = 70.0
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    scale_up_cooldown_seconds: int = 300  # 5 minutes
    scale_down_cooldown_seconds: int = 600  # 10 minutes
    scale_up_increment: int = 1
    scale_down_increment: int = 1
    evaluation_periods: int = 3
    datapoints_to_alarm: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_type": self.agent_type,
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "target_cpu_percent": self.target_cpu_percent,
            "target_memory_percent": self.target_memory_percent,
            "target_utilization_percent": self.target_utilization_percent,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "scale_up_cooldown_seconds": self.scale_up_cooldown_seconds,
            "scale_down_cooldown_seconds": self.scale_down_cooldown_seconds,
            "scale_up_increment": self.scale_up_increment,
            "scale_down_increment": self.scale_down_increment,
            "evaluation_periods": self.evaluation_periods,
            "datapoints_to_alarm": self.datapoints_to_alarm
        }


@dataclass
class ResourceMetrics:
    """System resource metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_bytes: int
    active_connections: int
    load_average: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "network_io_bytes": self.network_io_bytes,
            "active_connections": self.active_connections,
            "load_average": self.load_average
        }


@dataclass
class CostMetrics:
    """Cost optimization metrics."""
    timestamp: datetime
    total_instances: int
    instance_costs: Dict[str, float]
    total_hourly_cost: float
    utilization_efficiency: float
    cost_per_request: float
    projected_monthly_cost: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_instances": self.total_instances,
            "instance_costs": self.instance_costs,
            "total_hourly_cost": self.total_hourly_cost,
            "utilization_efficiency": self.utilization_efficiency,
            "cost_per_request": self.cost_per_request,
            "projected_monthly_cost": self.projected_monthly_cost
        }


class LoadBalancer:
    """
    Load balancer for distributing requests across agent instances.
    
    Supports multiple load balancing strategies and health monitoring.
    """
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        """
        Initialize load balancer.
        
        Args:
            strategy: Load balancing strategy to use
        """
        self.strategy = strategy
        self.agent_pools: Dict[str, List[AgentInstance]] = defaultdict(list)
        self.round_robin_counters: Dict[str, int] = defaultdict(int)
        self.metrics_collector = get_metrics_collector()
        
        logger.info(f"Load balancer initialized with strategy: {strategy.value}")
    
    def register_agent_instance(self, instance: AgentInstance) -> None:
        """
        Register an agent instance with the load balancer.
        
        Args:
            instance: Agent instance to register
        """
        self.agent_pools[instance.agent_type].append(instance)
        logger.info(f"Registered agent instance: {instance.instance_id} ({instance.agent_type})")
    
    def unregister_agent_instance(self, agent_type: str, instance_id: str) -> bool:
        """
        Unregister an agent instance from the load balancer.
        
        Args:
            agent_type: Type of agent
            instance_id: Instance ID to unregister
            
        Returns:
            True if instance was found and removed
        """
        pool = self.agent_pools[agent_type]
        for i, instance in enumerate(pool):
            if instance.instance_id == instance_id:
                pool.pop(i)
                logger.info(f"Unregistered agent instance: {instance_id}")
                return True
        return False
    
    async def get_next_agent(self, agent_type: str) -> Optional[AgentInstance]:
        """
        Get the next available agent instance based on load balancing strategy.
        
        Args:
            agent_type: Type of agent needed
            
        Returns:
            Selected agent instance or None if none available
        """
        pool = self.agent_pools.get(agent_type, [])
        if not pool:
            return None
        
        # Filter healthy and available instances
        available_instances = [
            instance for instance in pool
            if not instance.is_busy and instance.health_score > 0.5
        ]
        
        if not available_instances:
            return None
        
        # Select instance based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected = self._round_robin_selection(agent_type, available_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            selected = self._least_connections_selection(available_instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            selected = self._weighted_round_robin_selection(available_instances)
        elif self.strategy == LoadBalancingStrategy.RESOURCE_BASED:
            selected = self._resource_based_selection(available_instances)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME_BASED:
            selected = self._response_time_based_selection(available_instances)
        else:
            selected = available_instances[0]  # Fallback
        
        if selected:
            selected.is_busy = True
            selected.last_request_time = datetime.utcnow()
            
            # Record load balancing metrics
            await self.metrics_collector.record_monitoring_metric(
                f"load_balancer.{agent_type}.requests_distributed",
                1,
                "count"
            )
        
        return selected
    
    def _round_robin_selection(self, agent_type: str, instances: List[AgentInstance]) -> AgentInstance:
        """Round robin selection strategy."""
        counter = self.round_robin_counters[agent_type]
        selected = instances[counter % len(instances)]
        self.round_robin_counters[agent_type] = (counter + 1) % len(instances)
        return selected
    
    def _least_connections_selection(self, instances: List[AgentInstance]) -> AgentInstance:
        """Least connections selection strategy."""
        return min(instances, key=lambda x: x.total_requests)
    
    def _weighted_round_robin_selection(self, instances: List[AgentInstance]) -> AgentInstance:
        """Weighted round robin selection strategy."""
        # Calculate weighted selection based on instance weights
        total_weight = sum(instance.weight for instance in instances)
        if total_weight == 0:
            return instances[0]
        
        # Simple weighted selection (could be improved with proper weighted round robin)
        weights = [instance.weight / total_weight for instance in instances]
        import random
        return random.choices(instances, weights=weights)[0]
    
    def _resource_based_selection(self, instances: List[AgentInstance]) -> AgentInstance:
        """Resource-based selection strategy."""
        return min(instances, key=lambda x: x.utilization)
    
    def _response_time_based_selection(self, instances: List[AgentInstance]) -> AgentInstance:
        """Response time-based selection strategy."""
        return min(instances, key=lambda x: x.avg_response_time or 0)
    
    def release_agent(self, instance: AgentInstance, success: bool, response_time: float) -> None:
        """
        Release an agent instance back to the pool.
        
        Args:
            instance: Agent instance to release
            success: Whether the request was successful
            response_time: Response time in milliseconds
        """
        instance.is_busy = False
        instance.total_requests += 1
        if success:
            instance.successful_requests += 1
        
        # Update average response time
        if instance.avg_response_time == 0:
            instance.avg_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            instance.avg_response_time = (alpha * response_time + 
                                        (1 - alpha) * instance.avg_response_time)
        
        # Update health score based on recent performance
        instance.health_score = min(1.0, instance.success_rate * 
                                  (1000 / max(instance.avg_response_time, 100)))
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        stats = {
            "strategy": self.strategy.value,
            "agent_pools": {}
        }
        
        for agent_type, pool in self.agent_pools.items():
            pool_stats = {
                "total_instances": len(pool),
                "available_instances": len([i for i in pool if not i.is_busy]),
                "busy_instances": len([i for i in pool if i.is_busy]),
                "avg_health_score": statistics.mean([i.health_score for i in pool]) if pool else 0,
                "avg_response_time": statistics.mean([i.avg_response_time for i in pool if i.avg_response_time > 0]) if [i.avg_response_time for i in pool if i.avg_response_time > 0] else 0,
                "total_requests": sum(i.total_requests for i in pool),
                "success_rate": statistics.mean([i.success_rate for i in pool]) if pool else 0
            }
            stats["agent_pools"][agent_type] = pool_stats
        
        return stats


class AutoScaler:
    """
    Auto-scaling service for dynamic instance management.
    
    Monitors metrics and automatically scales agent instances up or down.
    """
    
    def __init__(self, load_balancer: LoadBalancer):
        """
        Initialize auto-scaler.
        
        Args:
            load_balancer: Load balancer instance
        """
        self.load_balancer = load_balancer
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.scaling_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.last_scaling_action: Dict[str, datetime] = {}
        self.metrics_collector = get_metrics_collector()
        self.agent_factories: Dict[str, Callable] = {}
        
        logger.info("Auto-scaler initialized")
    
    def register_scaling_policy(self, policy: ScalingPolicy) -> None:
        """
        Register a scaling policy for an agent type.
        
        Args:
            policy: Scaling policy to register
        """
        self.scaling_policies[policy.agent_type] = policy
        logger.info(f"Registered scaling policy for {policy.agent_type}")
    
    def register_agent_factory(self, agent_type: str, factory: Callable) -> None:
        """
        Register an agent factory function.
        
        Args:
            agent_type: Type of agent
            factory: Factory function to create new instances
        """
        self.agent_factories[agent_type] = factory
        logger.info(f"Registered agent factory for {agent_type}")
    
    async def evaluate_scaling_decisions(self) -> Dict[str, ScalingDirection]:
        """
        Evaluate scaling decisions for all registered agent types.
        
        Returns:
            Dictionary mapping agent types to scaling decisions
        """
        decisions = {}
        
        for agent_type, policy in self.scaling_policies.items():
            decision = await self._evaluate_agent_scaling(agent_type, policy)
            decisions[agent_type] = decision
        
        return decisions
    
    async def _evaluate_agent_scaling(self, agent_type: str, policy: ScalingPolicy) -> ScalingDirection:
        """
        Evaluate scaling decision for a specific agent type.
        
        Args:
            agent_type: Type of agent to evaluate
            policy: Scaling policy for the agent type
            
        Returns:
            Scaling decision
        """
        # Get current instances
        current_instances = len(self.load_balancer.agent_pools.get(agent_type, []))
        
        # Check cooldown periods
        last_action_time = self.last_scaling_action.get(agent_type)
        if last_action_time:
            time_since_last_action = (datetime.utcnow() - last_action_time).total_seconds()
            if time_since_last_action < policy.scale_up_cooldown_seconds:
                return ScalingDirection.NONE
        
        # Get metrics for evaluation
        metrics = await self._get_scaling_metrics(agent_type, policy)
        
        # Evaluate scale up conditions
        if current_instances < policy.max_instances:
            if self._should_scale_up(metrics, policy):
                return ScalingDirection.UP
        
        # Evaluate scale down conditions
        if current_instances > policy.min_instances:
            if self._should_scale_down(metrics, policy):
                return ScalingDirection.DOWN
        
        return ScalingDirection.NONE
    
    async def _get_scaling_metrics(self, agent_type: str, policy: ScalingPolicy) -> Dict[str, float]:
        """
        Get metrics for scaling evaluation.
        
        Args:
            agent_type: Type of agent
            policy: Scaling policy
            
        Returns:
            Dictionary of metrics
        """
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # Get agent-specific metrics
        pool = self.load_balancer.agent_pools.get(agent_type, [])
        if pool:
            avg_utilization = statistics.mean([instance.utilization for instance in pool])
            response_times = [instance.avg_response_time for instance in pool if instance.avg_response_time > 0]
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            busy_ratio = len([i for i in pool if i.is_busy]) / len(pool)
        else:
            avg_utilization = 0.0
            avg_response_time = 0.0
            busy_ratio = 0.0
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "avg_utilization": avg_utilization,
            "avg_response_time": avg_response_time or 0.0,
            "busy_ratio": busy_ratio * 100
        }
    
    def _should_scale_up(self, metrics: Dict[str, float], policy: ScalingPolicy) -> bool:
        """
        Determine if scaling up is needed.
        
        Args:
            metrics: Current metrics
            policy: Scaling policy
            
        Returns:
            True if should scale up
        """
        conditions_met = 0
        
        # Check CPU threshold
        if metrics["cpu_percent"] > policy.scale_up_threshold:
            conditions_met += 1
        
        # Check memory threshold
        if metrics["memory_percent"] > policy.scale_up_threshold:
            conditions_met += 1
        
        # Check utilization threshold
        if metrics["avg_utilization"] * 100 > policy.scale_up_threshold:
            conditions_met += 1
        
        # Check busy ratio
        if metrics["busy_ratio"] > policy.scale_up_threshold:
            conditions_met += 1
        
        # Need at least datapoints_to_alarm conditions to trigger scaling
        return conditions_met >= policy.datapoints_to_alarm
    
    def _should_scale_down(self, metrics: Dict[str, float], policy: ScalingPolicy) -> bool:
        """
        Determine if scaling down is needed.
        
        Args:
            metrics: Current metrics
            policy: Scaling policy
            
        Returns:
            True if should scale down
        """
        conditions_met = 0
        
        # Check CPU threshold
        if metrics["cpu_percent"] < policy.scale_down_threshold:
            conditions_met += 1
        
        # Check memory threshold
        if metrics["memory_percent"] < policy.scale_down_threshold:
            conditions_met += 1
        
        # Check utilization threshold
        if metrics["avg_utilization"] * 100 < policy.scale_down_threshold:
            conditions_met += 1
        
        # Check busy ratio
        if metrics["busy_ratio"] < policy.scale_down_threshold:
            conditions_met += 1
        
        # Need at least datapoints_to_alarm conditions to trigger scaling
        return conditions_met >= policy.datapoints_to_alarm
    
    async def execute_scaling_action(self, agent_type: str, direction: ScalingDirection) -> bool:
        """
        Execute a scaling action.
        
        Args:
            agent_type: Type of agent to scale
            direction: Scaling direction
            
        Returns:
            True if scaling action was successful
        """
        if direction == ScalingDirection.NONE:
            return True
        
        policy = self.scaling_policies.get(agent_type)
        if not policy:
            logger.error(f"No scaling policy found for {agent_type}")
            return False
        
        try:
            if direction == ScalingDirection.UP:
                success = await self._scale_up(agent_type, policy)
            else:  # ScalingDirection.DOWN
                success = await self._scale_down(agent_type, policy)
            
            if success:
                # Record scaling action
                self.last_scaling_action[agent_type] = datetime.utcnow()
                self.scaling_history[agent_type].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "direction": direction.value,
                    "instances_before": len(self.load_balancer.agent_pools.get(agent_type, [])),
                    "instances_after": len(self.load_balancer.agent_pools.get(agent_type, [])),
                    "success": success
                })
                
                # Record metrics
                await self.metrics_collector.record_monitoring_metric(
                    f"autoscaler.{agent_type}.scaling_actions",
                    1,
                    "count"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Scaling action failed for {agent_type}: {e}")
            return False
    
    async def _scale_up(self, agent_type: str, policy: ScalingPolicy) -> bool:
        """Scale up agent instances."""
        factory = self.agent_factories.get(agent_type)
        if not factory:
            logger.error(f"No factory registered for {agent_type}")
            return False
        
        current_count = len(self.load_balancer.agent_pools.get(agent_type, []))
        target_count = min(current_count + policy.scale_up_increment, policy.max_instances)
        
        for _ in range(target_count - current_count):
            try:
                # Create new instance
                new_instance = factory()
                
                # Convert to AgentInstance if needed
                if not isinstance(new_instance, AgentInstance):
                    agent_instance = AgentInstance(
                        instance_id=f"{agent_type}_{int(time.time())}_{id(new_instance)}",
                        agent_type=agent_type
                    )
                    # Store reference to actual agent
                    agent_instance._agent_ref = new_instance
                else:
                    agent_instance = new_instance
                
                # Register with load balancer
                self.load_balancer.register_agent_instance(agent_instance)
                
                logger.info(f"Scaled up {agent_type}: added instance {agent_instance.instance_id}")
                
            except Exception as e:
                logger.error(f"Failed to create new {agent_type} instance: {e}")
                return False
        
        return True
    
    async def _scale_down(self, agent_type: str, policy: ScalingPolicy) -> bool:
        """Scale down agent instances."""
        pool = self.load_balancer.agent_pools.get(agent_type, [])
        if not pool:
            return True
        
        current_count = len(pool)
        target_count = max(current_count - policy.scale_down_increment, policy.min_instances)
        
        instances_to_remove = current_count - target_count
        
        # Find idle instances to remove
        idle_instances = [instance for instance in pool if not instance.is_busy]
        
        if len(idle_instances) < instances_to_remove:
            logger.warning(f"Not enough idle instances to scale down {agent_type}")
            instances_to_remove = len(idle_instances)
        
        # Remove instances with lowest health scores first
        instances_to_remove_list = sorted(idle_instances, key=lambda x: x.health_score)[:instances_to_remove]
        
        for instance in instances_to_remove_list:
            # Cleanup instance if it has cleanup method
            if hasattr(instance, '_agent_ref') and hasattr(instance._agent_ref, 'cleanup'):
                try:
                    await instance._agent_ref.cleanup()
                except Exception as e:
                    logger.warning(f"Instance cleanup failed: {e}")
            
            # Unregister from load balancer
            self.load_balancer.unregister_agent_instance(agent_type, instance.instance_id)
            
            logger.info(f"Scaled down {agent_type}: removed instance {instance.instance_id}")
        
        return True
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status."""
        status = {}
        
        for agent_type, policy in self.scaling_policies.items():
            current_instances = len(self.load_balancer.agent_pools.get(agent_type, []))
            last_action = self.last_scaling_action.get(agent_type)
            recent_history = self.scaling_history[agent_type][-5:]  # Last 5 actions
            
            status[agent_type] = {
                "current_instances": current_instances,
                "min_instances": policy.min_instances,
                "max_instances": policy.max_instances,
                "scaling_policy": policy.to_dict(),
                "last_scaling_action": last_action.isoformat() if last_action else None,
                "recent_scaling_history": recent_history,
                "can_scale_up": current_instances < policy.max_instances,
                "can_scale_down": current_instances > policy.min_instances
            }
        
        return status


class ResourceMonitor:
    """
    Resource monitoring and capacity planning service.
    
    Monitors system resources and provides capacity planning insights.
    """
    
    def __init__(self):
        """Initialize resource monitor."""
        self.resource_history: deque = deque(maxlen=1440)  # 24 hours of minute-level data
        self.metrics_collector = get_metrics_collector()
        self.monitoring_enabled = True
        
        logger.info("Resource monitor initialized")
    
    async def collect_resource_metrics(self) -> ResourceMetrics:
        """
        Collect current resource metrics.
        
        Returns:
            Current resource metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io_bytes = network.bytes_sent + network.bytes_recv
            
            # Connection metrics
            connections = len(psutil.net_connections())
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
            except (AttributeError, OSError):
                load_avg = 0.0  # Windows doesn't have load average
            
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_bytes=network_io_bytes,
                active_connections=connections,
                load_average=load_avg
            )
            
            # Store in history
            self.resource_history.append(metrics)
            
            # Record in metrics collector
            await self.metrics_collector.record_monitoring_metric("resource.cpu_percent", cpu_percent, "percent")
            await self.metrics_collector.record_monitoring_metric("resource.memory_percent", memory_percent, "percent")
            await self.metrics_collector.record_monitoring_metric("resource.disk_percent", disk_percent, "percent")
            await self.metrics_collector.record_monitoring_metric("resource.active_connections", connections, "count")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect resource metrics: {e}")
            raise
    
    def get_resource_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get resource usage trends over specified time period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Resource trend analysis
        """
        if not self.resource_history:
            return {"error": "No resource history available"}
        
        # Filter data for specified time period
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.resource_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"error": f"No data available for last {hours} hours"}
        
        # Calculate trends
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]
        
        return {
            "time_period_hours": hours,
            "data_points": len(recent_metrics),
            "cpu_usage": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": statistics.mean(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "trend": self._calculate_trend(cpu_values)
            },
            "memory_usage": {
                "current": memory_values[-1] if memory_values else 0,
                "average": statistics.mean(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "trend": self._calculate_trend(memory_values)
            },
            "disk_usage": {
                "current": disk_values[-1] if disk_values else 0,
                "average": statistics.mean(disk_values),
                "min": min(disk_values),
                "max": max(disk_values),
                "trend": self._calculate_trend(disk_values)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction from a series of values.
        
        Args:
            values: List of values to analyze
            
        Returns:
            Trend direction: "increasing", "decreasing", or "stable"
        """
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def predict_capacity_needs(self, forecast_hours: int = 168) -> Dict[str, Any]:
        """
        Predict future capacity needs based on historical trends.
        
        Args:
            forecast_hours: Hours to forecast (default: 1 week)
            
        Returns:
            Capacity predictions and recommendations
        """
        if len(self.resource_history) < 24:  # Need at least 24 data points
            return {"error": "Insufficient historical data for prediction"}
        
        # Get recent trends
        trends = self.get_resource_trends(24)  # Last 24 hours
        
        predictions = {}
        recommendations = []
        
        for resource in ["cpu_usage", "memory_usage", "disk_usage"]:
            if resource in trends:
                current = trends[resource]["current"]
                trend = trends[resource]["trend"]
                avg_rate = (trends[resource]["max"] - trends[resource]["min"]) / 24  # Per hour
                
                # Simple linear projection
                if trend == "increasing":
                    predicted = current + (avg_rate * forecast_hours)
                elif trend == "decreasing":
                    predicted = max(0, current - (avg_rate * forecast_hours))
                else:
                    predicted = current
                
                predictions[resource] = {
                    "current": current,
                    "predicted": min(100, max(0, predicted)),
                    "trend": trend,
                    "confidence": "medium"  # Would be calculated based on data quality
                }
                
                # Generate recommendations
                if predicted > 80:
                    recommendations.append({
                        "resource": resource,
                        "issue": f"High {resource.replace('_', ' ')} predicted",
                        "recommendation": f"Consider scaling up {resource.replace('_usage', '')} resources",
                        "priority": "high" if predicted > 90 else "medium",
                        "predicted_value": predicted
                    })
        
        return {
            "forecast_hours": forecast_hours,
            "predictions": predictions,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }


class CostOptimizer:
    """
    Cost optimization and budget management service.
    
    Monitors costs and provides optimization recommendations.
    """
    
    def __init__(self):
        """Initialize cost optimizer."""
        self.cost_history: deque = deque(maxlen=720)  # 30 days of hourly data
        self.instance_costs = {
            "cto_agent": 0.05,      # $0.05 per hour
            "research_agent": 0.03,  # $0.03 per hour
            "cloud_engineer_agent": 0.04,  # $0.04 per hour
            "mlops_agent": 0.06,    # $0.06 per hour
            "compliance_agent": 0.04,  # $0.04 per hour
            "ai_consultant_agent": 0.05,  # $0.05 per hour
            "web_research_agent": 0.03,  # $0.03 per hour
            "simulation_agent": 0.07,  # $0.07 per hour
            "report_generator_agent": 0.02  # $0.02 per hour
        }
        self.metrics_collector = get_metrics_collector()
        
        logger.info("Cost optimizer initialized")
    
    async def calculate_current_costs(self, load_balancer: LoadBalancer) -> CostMetrics:
        """
        Calculate current cost metrics.
        
        Args:
            load_balancer: Load balancer instance
            
        Returns:
            Current cost metrics
        """
        total_instances = 0
        instance_costs = {}
        total_hourly_cost = 0.0
        total_requests = 0
        total_utilization = 0.0
        
        for agent_type, pool in load_balancer.agent_pools.items():
            instance_count = len(pool)
            cost_per_hour = self.instance_costs.get(agent_type, 0.05)
            type_cost = instance_count * cost_per_hour
            
            total_instances += instance_count
            instance_costs[agent_type] = type_cost
            total_hourly_cost += type_cost
            
            # Calculate utilization for this agent type
            if pool:
                type_requests = sum(instance.total_requests for instance in pool)
                type_utilization = statistics.mean([instance.utilization for instance in pool])
                total_requests += type_requests
                total_utilization += type_utilization
        
        # Calculate efficiency metrics
        avg_utilization = total_utilization / len(load_balancer.agent_pools) if load_balancer.agent_pools else 0
        utilization_efficiency = min(1.0, avg_utilization / 0.7)  # Target 70% utilization
        
        cost_per_request = total_hourly_cost / max(total_requests, 1)
        projected_monthly_cost = total_hourly_cost * 24 * 30  # 30 days
        
        metrics = CostMetrics(
            timestamp=datetime.utcnow(),
            total_instances=total_instances,
            instance_costs=instance_costs,
            total_hourly_cost=total_hourly_cost,
            utilization_efficiency=utilization_efficiency,
            cost_per_request=cost_per_request,
            projected_monthly_cost=projected_monthly_cost
        )
        
        # Store in history
        self.cost_history.append(metrics)
        
        # Record metrics
        await self.metrics_collector.record_monitoring_metric("cost.total_hourly", total_hourly_cost, "dollars")
        await self.metrics_collector.record_monitoring_metric("cost.utilization_efficiency", utilization_efficiency, "ratio")
        await self.metrics_collector.record_monitoring_metric("cost.cost_per_request", cost_per_request, "dollars")
        
        return metrics
    
    def get_cost_optimization_recommendations(self, load_balancer: LoadBalancer) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations.
        
        Args:
            load_balancer: Load balancer instance
            
        Returns:
            List of cost optimization recommendations
        """
        recommendations = []
        
        for agent_type, pool in load_balancer.agent_pools.items():
            if not pool:
                continue
            
            # Calculate utilization metrics
            avg_utilization = statistics.mean([instance.utilization for instance in pool])
            idle_instances = len([instance for instance in pool if not instance.is_busy])
            total_instances = len(pool)
            
            # Low utilization recommendation
            if avg_utilization < 0.3 and total_instances > 1:
                potential_savings = (idle_instances * self.instance_costs.get(agent_type, 0.05) * 24 * 30)
                recommendations.append({
                    "agent_type": agent_type,
                    "issue": "Low utilization detected",
                    "recommendation": f"Consider reducing {agent_type} instances from {total_instances} to {total_instances - idle_instances}",
                    "potential_monthly_savings": potential_savings,
                    "priority": "medium",
                    "current_utilization": avg_utilization * 100
                })
            
            # High cost per request recommendation
            if pool:
                total_requests = sum(instance.total_requests for instance in pool)
                if total_requests > 0:
                    cost_per_request = (total_instances * self.instance_costs.get(agent_type, 0.05)) / total_requests
                    if cost_per_request > 0.01:  # $0.01 per request threshold
                        recommendations.append({
                            "agent_type": agent_type,
                            "issue": "High cost per request",
                            "recommendation": f"Optimize {agent_type} performance or consider instance right-sizing",
                            "current_cost_per_request": cost_per_request,
                            "priority": "low",
                            "total_requests": total_requests
                        })
        
        # Overall cost recommendations
        if self.cost_history:
            latest_metrics = self.cost_history[-1]
            
            if latest_metrics.utilization_efficiency < 0.6:
                recommendations.append({
                    "agent_type": "system",
                    "issue": "Overall low utilization efficiency",
                    "recommendation": "Review scaling policies and consider reducing minimum instance counts",
                    "current_efficiency": latest_metrics.utilization_efficiency,
                    "priority": "high",
                    "potential_monthly_savings": latest_metrics.projected_monthly_cost * 0.2
                })
        
        return recommendations
    
    def get_cost_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive cost report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Cost analysis report
        """
        if not self.cost_history:
            return {"error": "No cost history available"}
        
        # Filter data for specified period
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        recent_metrics = [m for m in self.cost_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"error": f"No cost data available for last {days} days"}
        
        # Calculate cost trends
        total_costs = [m.total_hourly_cost for m in recent_metrics]
        efficiency_scores = [m.utilization_efficiency for m in recent_metrics]
        
        # Aggregate instance costs
        aggregated_costs = defaultdict(list)
        for metrics in recent_metrics:
            for agent_type, cost in metrics.instance_costs.items():
                aggregated_costs[agent_type].append(cost)
        
        agent_cost_summary = {}
        for agent_type, costs in aggregated_costs.items():
            agent_cost_summary[agent_type] = {
                "average_hourly_cost": statistics.mean(costs),
                "total_cost_period": sum(costs),
                "min_cost": min(costs),
                "max_cost": max(costs)
            }
        
        return {
            "analysis_period_days": days,
            "data_points": len(recent_metrics),
            "cost_summary": {
                "current_hourly_cost": total_costs[-1] if total_costs else 0,
                "average_hourly_cost": statistics.mean(total_costs),
                "total_cost_period": sum(total_costs),
                "projected_monthly_cost": recent_metrics[-1].projected_monthly_cost if recent_metrics else 0
            },
            "efficiency_summary": {
                "current_efficiency": efficiency_scores[-1] if efficiency_scores else 0,
                "average_efficiency": statistics.mean(efficiency_scores),
                "efficiency_trend": self._calculate_trend(efficiency_scores)
            },
            "agent_costs": agent_cost_summary,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction (same as ResourceMonitor)."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"


class ScalabilityManager:
    """
    Main scalability management service that coordinates all scalability components.
    """
    
    def __init__(self):
        """Initialize scalability manager."""
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler(self.load_balancer)
        self.resource_monitor = ResourceMonitor()
        self.cost_optimizer = CostOptimizer()
        self.metrics_collector = get_metrics_collector()
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._monitoring_enabled = False
        
        logger.info("Scalability manager initialized")
    
    async def start_monitoring(self) -> None:
        """Start all monitoring and scaling services."""
        if self._monitoring_enabled:
            logger.warning("Monitoring already started")
            return
        
        self._monitoring_enabled = True
        
        # Start resource monitoring
        resource_task = asyncio.create_task(self._resource_monitoring_loop())
        self._background_tasks.append(resource_task)
        
        # Start auto-scaling
        scaling_task = asyncio.create_task(self._auto_scaling_loop())
        self._background_tasks.append(scaling_task)
        
        # Start cost monitoring
        cost_task = asyncio.create_task(self._cost_monitoring_loop())
        self._background_tasks.append(cost_task)
        
        logger.info("Scalability monitoring services started")
    
    async def stop_monitoring(self) -> None:
        """Stop all monitoring and scaling services."""
        if not self._monitoring_enabled:
            return
        
        self._monitoring_enabled = False
        
        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        logger.info("Scalability monitoring services stopped")
    
    async def _resource_monitoring_loop(self) -> None:
        """Background loop for resource monitoring."""
        while self._monitoring_enabled:
            try:
                await self.resource_monitor.collect_resource_metrics()
                await asyncio.sleep(60)  # Collect every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _auto_scaling_loop(self) -> None:
        """Background loop for auto-scaling."""
        while self._monitoring_enabled:
            try:
                # Evaluate scaling decisions
                decisions = await self.auto_scaler.evaluate_scaling_decisions()
                
                # Execute scaling actions
                for agent_type, direction in decisions.items():
                    if direction != ScalingDirection.NONE:
                        await self.auto_scaler.execute_scaling_action(agent_type, direction)
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(300)
    
    async def _cost_monitoring_loop(self) -> None:
        """Background loop for cost monitoring."""
        while self._monitoring_enabled:
            try:
                await self.cost_optimizer.calculate_current_costs(self.load_balancer)
                await asyncio.sleep(3600)  # Calculate every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cost monitoring error: {e}")
                await asyncio.sleep(3600)
    
    def register_agent_type(self, agent_type: str, factory: Callable, 
                          scaling_policy: Optional[ScalingPolicy] = None) -> None:
        """
        Register an agent type with the scalability manager.
        
        Args:
            agent_type: Type of agent
            factory: Factory function to create instances
            scaling_policy: Custom scaling policy
        """
        # Register with auto-scaler
        self.auto_scaler.register_agent_factory(agent_type, factory)
        
        if scaling_policy:
            self.auto_scaler.register_scaling_policy(scaling_policy)
        else:
            # Use default policy
            default_policy = ScalingPolicy(agent_type=agent_type)
            self.auto_scaler.register_scaling_policy(default_policy)
        
        logger.info(f"Registered agent type {agent_type} with scalability manager")
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive scalability status."""
        try:
            # Get status from all components
            load_balancer_stats = self.load_balancer.get_load_balancer_stats()
            scaling_status = self.auto_scaler.get_scaling_status()
            resource_trends = self.resource_monitor.get_resource_trends(24)
            capacity_predictions = self.resource_monitor.predict_capacity_needs(168)
            cost_report = self.cost_optimizer.get_cost_report(30)
            cost_recommendations = self.cost_optimizer.get_cost_optimization_recommendations(self.load_balancer)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_enabled": self._monitoring_enabled,
                "load_balancer": load_balancer_stats,
                "auto_scaling": scaling_status,
                "resource_trends": resource_trends,
                "capacity_predictions": capacity_predictions,
                "cost_analysis": cost_report,
                "cost_recommendations": cost_recommendations,
                "system_health": {
                    "total_agent_instances": sum(len(pool) for pool in self.load_balancer.agent_pools.values()),
                    "active_agent_types": len(self.load_balancer.agent_pools),
                    "background_tasks_running": len(self._background_tasks)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive status: {e}")
            return {"error": str(e)}


# Global scalability manager instance
scalability_manager = ScalabilityManager()