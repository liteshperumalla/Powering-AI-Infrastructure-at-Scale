"""
Cost tracking and monitoring for LLM usage.

Provides comprehensive cost tracking, budgeting, and optimization
features for LLM API usage across different providers.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

from .interface import LLMProvider, TokenUsage

logger = logging.getLogger(__name__)


class CostPeriod(str, Enum):
    """Cost tracking periods."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class CostEntry:
    """Individual cost entry."""
    timestamp: datetime
    provider: LLMProvider
    model: str
    agent_name: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    request_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider.value,
            "model": self.model,
            "agent_name": self.agent_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "request_id": self.request_id
        }


@dataclass
class CostSummary:
    """Cost summary for a specific period."""
    period: CostPeriod
    start_time: datetime
    end_time: datetime
    total_cost: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    provider_breakdown: Dict[str, float] = field(default_factory=dict)
    model_breakdown: Dict[str, float] = field(default_factory=dict)
    agent_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period": self.period.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "average_cost_per_request": (
                round(self.total_cost / self.total_requests, 4) 
                if self.total_requests > 0 else 0
            ),
            "average_tokens_per_request": (
                round(self.total_tokens / self.total_requests, 2) 
                if self.total_requests > 0 else 0
            ),
            "provider_breakdown": {
                k: round(v, 4) for k, v in self.provider_breakdown.items()
            },
            "model_breakdown": {
                k: round(v, 4) for k, v in self.model_breakdown.items()
            },
            "agent_breakdown": {
                k: round(v, 4) for k, v in self.agent_breakdown.items()
            }
        }


@dataclass
class BudgetAlert:
    """Budget alert configuration."""
    name: str
    threshold_percentage: float  # 0.0 to 1.0
    period: CostPeriod
    budget_amount: float
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, current_cost: float) -> bool:
        """Check if alert should trigger."""
        if not self.enabled:
            return False
        
        threshold_amount = self.budget_amount * self.threshold_percentage
        return current_cost >= threshold_amount


class CostTracker:
    """
    Comprehensive cost tracking and monitoring for LLM usage.
    
    Features:
    - Real-time cost tracking across providers
    - Budget monitoring and alerts
    - Cost optimization recommendations
    - Usage analytics and reporting
    - Export capabilities
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize cost tracker.
        
        Args:
            storage_path: Path to store cost data (optional)
        """
        self.storage_path = storage_path
        self.cost_entries: List[CostEntry] = []
        self.budget_alerts: List[BudgetAlert] = []
        self._daily_budgets: Dict[str, float] = {}  # date -> budget
        self._monthly_budgets: Dict[str, float] = {}  # month -> budget
        
        logger.info("Cost tracker initialized")
    
    def track_usage(self, token_usage: TokenUsage, agent_name: Optional[str] = None, request_id: str = "") -> None:
        """
        Track LLM usage and cost.
        
        Args:
            token_usage: Token usage information
            agent_name: Name of the agent making the request
            request_id: Request ID for tracking
        """
        entry = CostEntry(
            timestamp=token_usage.timestamp,
            provider=token_usage.provider,
            model=token_usage.model,
            agent_name=agent_name,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            total_tokens=token_usage.total_tokens,
            cost=token_usage.estimated_cost,
            request_id=request_id
        )
        
        self.cost_entries.append(entry)
        
        # Check budget alerts
        self._check_budget_alerts()
        
        logger.debug(
            f"Tracked usage: {token_usage.total_tokens} tokens, "
            f"${token_usage.estimated_cost:.4f} cost for {agent_name or 'unknown'}"
        )
    
    def get_cost_summary(
        self, 
        period: CostPeriod, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CostSummary:
        """
        Get cost summary for a specific period.
        
        Args:
            period: Cost period to summarize
            start_time: Start time (optional, defaults to period start)
            end_time: End time (optional, defaults to now)
            
        Returns:
            Cost summary for the period
        """
        now = datetime.now(timezone.utc)
        
        # Set default time range based on period
        if start_time is None:
            if period == CostPeriod.HOURLY:
                start_time = now - timedelta(hours=1)
            elif period == CostPeriod.DAILY:
                start_time = now - timedelta(days=1)
            elif period == CostPeriod.WEEKLY:
                start_time = now - timedelta(weeks=1)
            elif period == CostPeriod.MONTHLY:
                start_time = now - timedelta(days=30)
        
        if end_time is None:
            end_time = now
        
        # Filter entries for the period
        period_entries = [
            entry for entry in self.cost_entries
            if start_time <= entry.timestamp <= end_time
        ]
        
        # Calculate summary
        summary = CostSummary(
            period=period,
            start_time=start_time,
            end_time=end_time
        )
        
        for entry in period_entries:
            summary.total_cost += entry.cost
            summary.total_tokens += entry.total_tokens
            summary.total_requests += 1
            
            # Provider breakdown
            provider_key = entry.provider.value
            summary.provider_breakdown[provider_key] = (
                summary.provider_breakdown.get(provider_key, 0) + entry.cost
            )
            
            # Model breakdown
            model_key = f"{entry.provider.value}:{entry.model}"
            summary.model_breakdown[model_key] = (
                summary.model_breakdown.get(model_key, 0) + entry.cost
            )
            
            # Agent breakdown
            if entry.agent_name:
                summary.agent_breakdown[entry.agent_name] = (
                    summary.agent_breakdown.get(entry.agent_name, 0) + entry.cost
                )
        
        return summary
    
    def get_top_cost_drivers(self, period: CostPeriod, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get top cost drivers for a period.
        
        Args:
            period: Cost period to analyze
            limit: Maximum number of items to return
            
        Returns:
            Dictionary with top providers, models, and agents by cost
        """
        summary = self.get_cost_summary(period)
        
        # Sort by cost (descending)
        top_providers = sorted(
            summary.provider_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        top_models = sorted(
            summary.model_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        top_agents = sorted(
            summary.agent_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return {
            "providers": [{"name": name, "cost": cost} for name, cost in top_providers],
            "models": [{"name": name, "cost": cost} for name, cost in top_models],
            "agents": [{"name": name, "cost": cost} for name, cost in top_agents]
        }
    
    def set_budget(self, period: CostPeriod, amount: float, date_key: Optional[str] = None) -> None:
        """
        Set budget for a specific period.
        
        Args:
            period: Budget period
            amount: Budget amount in USD
            date_key: Specific date key (optional, defaults to current)
        """
        if date_key is None:
            now = datetime.now(timezone.utc)
            if period == CostPeriod.DAILY:
                date_key = now.strftime("%Y-%m-%d")
            elif period == CostPeriod.MONTHLY:
                date_key = now.strftime("%Y-%m")
        
        if period == CostPeriod.DAILY:
            self._daily_budgets[date_key] = amount
        elif period == CostPeriod.MONTHLY:
            self._monthly_budgets[date_key] = amount
        
        logger.info(f"Set {period.value} budget to ${amount:.2f} for {date_key}")
    
    def add_budget_alert(self, alert: BudgetAlert) -> None:
        """
        Add budget alert.
        
        Args:
            alert: Budget alert configuration
        """
        self.budget_alerts.append(alert)
        logger.info(f"Added budget alert: {alert.name} at {alert.threshold_percentage*100}%")
    
    def _check_budget_alerts(self) -> None:
        """Check and trigger budget alerts if necessary."""
        now = datetime.now(timezone.utc)
        
        for alert in self.budget_alerts:
            if not alert.enabled:
                continue
            
            # Get current cost for the alert period
            current_cost = self.get_cost_summary(alert.period).total_cost
            
            # Check if alert should trigger
            if alert.should_trigger(current_cost):
                # Avoid triggering the same alert multiple times in a short period
                if (alert.last_triggered and 
                    now - alert.last_triggered < timedelta(hours=1)):
                    continue
                
                alert.last_triggered = now
                
                logger.warning(
                    f"Budget alert triggered: {alert.name} - "
                    f"Current cost ${current_cost:.2f} exceeds "
                    f"{alert.threshold_percentage*100}% of ${alert.budget_amount:.2f} budget"
                )
                
                # Here you could send notifications, emails, etc.
                self._send_budget_alert_notification(alert, current_cost)
    
    def _send_budget_alert_notification(self, alert: BudgetAlert, current_cost: float) -> None:
        """
        Send budget alert notification.
        
        Args:
            alert: Budget alert that was triggered
            current_cost: Current cost that triggered the alert
        """
        # Placeholder for notification logic
        # In a real implementation, you might send emails, Slack messages, etc.
        logger.warning(
            f"BUDGET ALERT: {alert.name} - "
            f"Spent ${current_cost:.2f} of ${alert.budget_amount:.2f} "
            f"({alert.threshold_percentage*100}% threshold exceeded)"
        )
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations based on usage patterns.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # Analyze recent usage
        weekly_summary = self.get_cost_summary(CostPeriod.WEEKLY)
        monthly_summary = self.get_cost_summary(CostPeriod.MONTHLY)
        
        # Recommendation 1: High-cost models
        expensive_models = [
            model for model, cost in weekly_summary.model_breakdown.items()
            if cost > weekly_summary.total_cost * 0.3  # More than 30% of total cost
        ]
        
        if expensive_models:
            recommendations.append({
                "type": "model_optimization",
                "priority": "high",
                "title": "Consider using more cost-effective models",
                "description": f"Models {', '.join(expensive_models)} account for significant costs",
                "potential_savings": "20-50%",
                "actions": [
                    "Evaluate if GPT-3.5-turbo can replace GPT-4 for some use cases",
                    "Use lower temperature settings for more consistent outputs",
                    "Implement response caching for similar queries"
                ]
            })
        
        # Recommendation 2: High token usage agents
        high_usage_agents = [
            agent for agent, cost in weekly_summary.agent_breakdown.items()
            if cost > weekly_summary.total_cost * 0.4  # More than 40% of total cost
        ]
        
        if high_usage_agents:
            recommendations.append({
                "type": "agent_optimization",
                "priority": "medium",
                "title": "Optimize high-usage agents",
                "description": f"Agents {', '.join(high_usage_agents)} have high token usage",
                "potential_savings": "10-30%",
                "actions": [
                    "Review and optimize prompts for efficiency",
                    "Implement prompt templates to reduce token usage",
                    "Add response length limits where appropriate"
                ]
            })
        
        # Recommendation 3: Usage patterns
        if weekly_summary.total_requests > 0:
            avg_tokens_per_request = weekly_summary.total_tokens / weekly_summary.total_requests
            if avg_tokens_per_request > 3000:  # High average token usage
                recommendations.append({
                    "type": "usage_optimization",
                    "priority": "medium",
                    "title": "Reduce average token usage per request",
                    "description": f"Average {avg_tokens_per_request:.0f} tokens per request is high",
                    "potential_savings": "15-25%",
                    "actions": [
                        "Implement more specific prompts to reduce response length",
                        "Use system prompts to set response format expectations",
                        "Consider breaking complex requests into smaller parts"
                    ]
                })
        
        # Recommendation 4: Budget utilization
        if monthly_summary.total_cost > 0:
            monthly_budget = sum(self._monthly_budgets.values()) or 1000  # Default budget
            utilization = monthly_summary.total_cost / monthly_budget
            
            if utilization > 0.8:  # High budget utilization
                recommendations.append({
                    "type": "budget_management",
                    "priority": "high",
                    "title": "High budget utilization detected",
                    "description": f"Using {utilization*100:.1f}% of monthly budget",
                    "potential_savings": "Variable",
                    "actions": [
                        "Review and adjust budget allocations",
                        "Implement stricter rate limiting",
                        "Consider usage-based scaling for agents"
                    ]
                })
        
        return recommendations
    
    def export_cost_data(self, format: str = "json", start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> str:
        """
        Export cost data in specified format.
        
        Args:
            format: Export format ("json" or "csv")
            start_time: Start time for export (optional)
            end_time: End time for export (optional)
            
        Returns:
            Exported data as string
        """
        # Filter entries by time range if specified
        entries_to_export = self.cost_entries
        
        if start_time or end_time:
            entries_to_export = [
                entry for entry in self.cost_entries
                if (not start_time or entry.timestamp >= start_time) and
                   (not end_time or entry.timestamp <= end_time)
            ]
        
        if (format or "").lower() == "json":
            return json.dumps([entry.to_dict() for entry in entries_to_export], indent=2)
        elif (format or "").lower() == "csv":
            if not entries_to_export:
                return "No data to export"
            
            # CSV header
            csv_lines = [
                "timestamp,provider,model,agent_name,prompt_tokens,completion_tokens,total_tokens,cost,request_id"
            ]
            
            # CSV data
            for entry in entries_to_export:
                csv_lines.append(
                    f"{entry.timestamp.isoformat()},{entry.provider.value},{entry.model},"
                    f"{entry.agent_name or ''},{entry.prompt_tokens},{entry.completion_tokens},"
                    f"{entry.total_tokens},{entry.cost},{entry.request_id}"
                )
            
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.
        
        Returns:
            Usage statistics dictionary
        """
        if not self.cost_entries:
            return {"message": "No usage data available"}
        
        total_cost = sum(entry.cost for entry in self.cost_entries)
        total_tokens = sum(entry.total_tokens for entry in self.cost_entries)
        total_requests = len(self.cost_entries)
        
        # Time range
        earliest_entry = min(self.cost_entries, key=lambda x: x.timestamp)
        latest_entry = max(self.cost_entries, key=lambda x: x.timestamp)
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "average_cost_per_request": round(total_cost / total_requests, 4) if total_requests > 0 else 0,
            "average_tokens_per_request": round(total_tokens / total_requests, 2) if total_requests > 0 else 0,
            "time_range": {
                "start": earliest_entry.timestamp.isoformat(),
                "end": latest_entry.timestamp.isoformat(),
                "duration_hours": (latest_entry.timestamp - earliest_entry.timestamp).total_seconds() / 3600
            },
            "provider_distribution": self._get_provider_distribution(),
            "model_distribution": self._get_model_distribution(),
            "agent_distribution": self._get_agent_distribution()
        }
    
    def _get_provider_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get provider usage distribution."""
        provider_stats = {}
        
        for entry in self.cost_entries:
            provider = entry.provider.value
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            provider_stats[provider]["requests"] += 1
            provider_stats[provider]["tokens"] += entry.total_tokens
            provider_stats[provider]["cost"] += entry.cost
        
        # Round costs
        for stats in provider_stats.values():
            stats["cost"] = round(stats["cost"], 4)
        
        return provider_stats
    
    def _get_model_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get model usage distribution."""
        model_stats = {}
        
        for entry in self.cost_entries:
            model_key = f"{entry.provider.value}:{entry.model}"
            if model_key not in model_stats:
                model_stats[model_key] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            model_stats[model_key]["requests"] += 1
            model_stats[model_key]["tokens"] += entry.total_tokens
            model_stats[model_key]["cost"] += entry.cost
        
        # Round costs
        for stats in model_stats.values():
            stats["cost"] = round(stats["cost"], 4)
        
        return model_stats
    
    def _get_agent_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get agent usage distribution."""
        agent_stats = {}
        
        for entry in self.cost_entries:
            agent = entry.agent_name or "unknown"
            if agent not in agent_stats:
                agent_stats[agent] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            agent_stats[agent]["requests"] += 1
            agent_stats[agent]["tokens"] += entry.total_tokens
            agent_stats[agent]["cost"] += entry.cost
        
        # Round costs
        for stats in agent_stats.values():
            stats["cost"] = round(stats["cost"], 4)
        
        return agent_stats