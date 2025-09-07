"""
Advanced Predictive Cost Modeling and Financial Analytics.

This module provides sophisticated cost analysis, forecasting, and optimization
capabilities for infrastructure planning and budget management.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
import math
import json

logger = logging.getLogger(__name__)


class CostCategory(str, Enum):
    """Infrastructure cost categories."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"
    DATABASE = "database"
    SECURITY = "security"
    MONITORING = "monitoring"
    BACKUP = "backup"
    SUPPORT = "support"
    LICENSING = "licensing"
    PROFESSIONAL_SERVICES = "professional_services"


class CostModel(str, Enum):
    """Cost modeling approaches."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    STEP_FUNCTION = "step_function"
    SEASONAL = "seasonal"


@dataclass
class CostDriver:
    """Individual cost driver definition."""
    name: str
    category: CostCategory
    unit_cost: float
    scaling_factor: float
    minimum_units: int = 0
    maximum_units: Optional[int] = None
    cost_model: CostModel = CostModel.LINEAR
    seasonality_factor: float = 1.0
    growth_rate: float = 0.0  # Annual growth rate
    optimization_potential: float = 0.0  # % savings potential


@dataclass 
class CostScenario:
    """Cost modeling scenario."""
    name: str
    description: str
    growth_rate: float
    usage_pattern: str  # "steady", "growth", "seasonal", "spiky"
    optimization_level: str  # "none", "basic", "advanced", "aggressive"
    risk_factor: float = 1.0
    confidence_level: float = 0.8


@dataclass
class CostProjection:
    """Cost projection results."""
    scenario: CostScenario
    time_horizon: int  # months
    monthly_costs: List[float]
    annual_costs: List[float]
    total_cost: float
    savings_opportunities: Dict[str, float]
    risk_adjusted_cost: float
    confidence_intervals: Dict[str, Tuple[float, float]]


class PredictiveCostModeling:
    """
    Advanced predictive cost modeling system.
    
    Features:
    - Multi-scenario cost forecasting
    - Machine learning-based predictions
    - Risk-adjusted financial modeling
    - Optimization opportunity identification
    - Real-time cost tracking
    - Budget variance analysis
    """
    
    def __init__(self):
        """Initialize the cost modeling system."""
        self.cost_drivers = self._initialize_cost_drivers()
        self.pricing_models = self._initialize_pricing_models()
        self.optimization_strategies = self._initialize_optimization_strategies()
        self.historical_data = {}
        
        logger.info("Predictive Cost Modeling system initialized")
    
    def _initialize_cost_drivers(self) -> Dict[str, CostDriver]:
        """Initialize infrastructure cost driver definitions."""
        return {
            "ec2_instances": CostDriver(
                name="EC2 Compute Instances",
                category=CostCategory.COMPUTE,
                unit_cost=0.10,  # per hour
                scaling_factor=0.85,  # volume discounts
                minimum_units=1,
                maximum_units=1000,
                cost_model=CostModel.STEP_FUNCTION,
                growth_rate=0.05,  # 5% annual growth
                optimization_potential=0.30  # 30% savings potential
            ),
            "rds_instances": CostDriver(
                name="RDS Database Instances",
                category=CostCategory.DATABASE,
                unit_cost=0.25,  # per hour
                scaling_factor=0.90,
                minimum_units=1,
                maximum_units=50,
                cost_model=CostModel.LINEAR,
                growth_rate=0.03,
                optimization_potential=0.20
            ),
            "s3_storage": CostDriver(
                name="S3 Storage",
                category=CostCategory.STORAGE,
                unit_cost=0.023,  # per GB per month
                scaling_factor=0.95,
                minimum_units=0,
                cost_model=CostModel.LINEAR,
                growth_rate=0.15,  # 15% data growth
                optimization_potential=0.40
            ),
            "data_transfer": CostDriver(
                name="Data Transfer",
                category=CostCategory.NETWORKING,
                unit_cost=0.09,  # per GB
                scaling_factor=0.80,
                minimum_units=0,
                cost_model=CostModel.EXPONENTIAL,
                growth_rate=0.20,
                optimization_potential=0.25
            ),
            "cloudwatch": CostDriver(
                name="CloudWatch Monitoring",
                category=CostCategory.MONITORING,
                unit_cost=0.30,  # per metric per month
                scaling_factor=0.95,
                minimum_units=10,
                cost_model=CostModel.LINEAR,
                growth_rate=0.10,
                optimization_potential=0.15
            )
        }
    
    def _initialize_pricing_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cloud provider pricing models."""
        return {
            "aws": {
                "compute_discount_tiers": [
                    {"threshold": 0, "discount": 0.0},
                    {"threshold": 100, "discount": 0.05},
                    {"threshold": 500, "discount": 0.10},
                    {"threshold": 1000, "discount": 0.15}
                ],
                "reserved_instance_discounts": {
                    "1_year": 0.30,
                    "3_year": 0.50
                },
                "spot_instance_discounts": 0.70,
                "enterprise_discount": 0.10
            },
            "azure": {
                "compute_discount_tiers": [
                    {"threshold": 0, "discount": 0.0},
                    {"threshold": 75, "discount": 0.05},
                    {"threshold": 400, "discount": 0.12},
                    {"threshold": 800, "discount": 0.18}
                ],
                "reserved_instance_discounts": {
                    "1_year": 0.25,
                    "3_year": 0.45
                }
            },
            "gcp": {
                "sustained_use_discounts": {
                    "25_percent_usage": 0.10,
                    "50_percent_usage": 0.20,
                    "75_percent_usage": 0.30
                },
                "committed_use_discounts": {
                    "1_year": 0.30,
                    "3_year": 0.50
                }
            }
        }
    
    def _initialize_optimization_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cost optimization strategies."""
        return {
            "rightsizing": {
                "description": "Optimize instance sizes based on actual utilization",
                "typical_savings": 0.20,
                "implementation_effort": "medium",
                "risk_level": "low"
            },
            "reserved_instances": {
                "description": "Purchase reserved instances for predictable workloads",
                "typical_savings": 0.30,
                "implementation_effort": "low",
                "risk_level": "medium"
            },
            "spot_instances": {
                "description": "Use spot instances for non-critical workloads",
                "typical_savings": 0.70,
                "implementation_effort": "high",
                "risk_level": "high"
            },
            "auto_scaling": {
                "description": "Implement auto-scaling to match demand",
                "typical_savings": 0.25,
                "implementation_effort": "medium",
                "risk_level": "low"
            },
            "storage_optimization": {
                "description": "Optimize storage classes and lifecycle policies",
                "typical_savings": 0.40,
                "implementation_effort": "medium",
                "risk_level": "low"
            },
            "network_optimization": {
                "description": "Optimize data transfer and CDN usage",
                "typical_savings": 0.30,
                "implementation_effort": "high",
                "risk_level": "medium"
            }
        }
    
    async def generate_cost_projections(
        self,
        infrastructure_data: Dict[str, Any],
        scenarios: List[CostScenario],
        time_horizon_months: int = 36
    ) -> Dict[str, CostProjection]:
        """
        Generate comprehensive cost projections for multiple scenarios.
        
        Args:
            infrastructure_data: Current infrastructure configuration and usage
            scenarios: List of scenarios to model
            time_horizon_months: Projection time horizon in months
            
        Returns:
            Cost projections for each scenario
        """
        projections = {}
        
        for scenario in scenarios:
            try:
                logger.info(f"Generating cost projection for scenario: {scenario.name}")
                
                projection = await self._calculate_scenario_projection(
                    infrastructure_data, scenario, time_horizon_months
                )
                
                projections[scenario.name] = projection
                
            except Exception as e:
                logger.error(f"Error generating projection for {scenario.name}: {e}")
                projections[scenario.name] = self._create_error_projection(scenario, str(e))
        
        return projections
    
    async def _calculate_scenario_projection(
        self,
        infrastructure_data: Dict[str, Any],
        scenario: CostScenario,
        time_horizon: int
    ) -> CostProjection:
        """Calculate cost projection for a specific scenario."""
        monthly_costs = []
        current_usage = infrastructure_data.get("current_usage", {})
        
        # Base monthly cost calculation
        base_monthly_cost = await self._calculate_base_monthly_cost(current_usage)
        
        # Apply scenario-specific modeling
        for month in range(time_horizon):
            # Calculate growth factor
            growth_factor = self._calculate_growth_factor(scenario, month)
            
            # Calculate seasonal factor
            seasonal_factor = self._calculate_seasonal_factor(scenario, month)
            
            # Calculate optimization factor
            optimization_factor = self._calculate_optimization_factor(scenario, month)
            
            # Calculate monthly cost
            monthly_cost = (
                base_monthly_cost * 
                growth_factor * 
                seasonal_factor * 
                optimization_factor
            )
            
            monthly_costs.append(monthly_cost)
        
        # Calculate annual costs
        annual_costs = []
        for year in range(0, time_horizon, 12):
            year_end = min(year + 12, len(monthly_costs))
            annual_cost = sum(monthly_costs[year:year_end])
            annual_costs.append(annual_cost)
        
        # Calculate savings opportunities
        savings_opportunities = await self._identify_savings_opportunities(
            infrastructure_data, scenario, sum(monthly_costs)
        )
        
        # Calculate risk-adjusted costs
        risk_factor = scenario.risk_factor
        risk_adjusted_cost = sum(monthly_costs) * risk_factor
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            monthly_costs, scenario.confidence_level
        )
        
        return CostProjection(
            scenario=scenario,
            time_horizon=time_horizon,
            monthly_costs=monthly_costs,
            annual_costs=annual_costs,
            total_cost=sum(monthly_costs),
            savings_opportunities=savings_opportunities,
            risk_adjusted_cost=risk_adjusted_cost,
            confidence_intervals=confidence_intervals
        )
    
    async def _calculate_base_monthly_cost(self, current_usage: Dict[str, Any]) -> float:
        """Calculate base monthly cost from current usage."""
        total_cost = 0.0
        
        for driver_name, driver in self.cost_drivers.items():
            usage = current_usage.get(driver_name, 0)
            
            if driver.cost_model == CostModel.LINEAR:
                cost = usage * driver.unit_cost
            elif driver.cost_model == CostModel.STEP_FUNCTION:
                # Volume discounts
                if usage > 500:
                    cost = usage * driver.unit_cost * 0.85
                elif usage > 100:
                    cost = usage * driver.unit_cost * 0.90
                else:
                    cost = usage * driver.unit_cost
            elif driver.cost_model == CostModel.EXPONENTIAL:
                cost = driver.unit_cost * (usage ** 1.2)  # Exponential scaling
            else:
                cost = usage * driver.unit_cost
            
            total_cost += cost
        
        return total_cost
    
    def _calculate_growth_factor(self, scenario: CostScenario, month: int) -> float:
        """Calculate growth factor for a given month."""
        annual_growth = scenario.growth_rate
        monthly_growth = annual_growth / 12
        
        if scenario.usage_pattern == "linear":
            return 1 + (monthly_growth * month)
        elif scenario.usage_pattern == "exponential":
            return (1 + monthly_growth) ** month
        elif scenario.usage_pattern == "seasonal":
            # Add seasonal variation
            seasonal_component = 0.1 * math.sin(2 * math.pi * month / 12)
            return (1 + monthly_growth * month) * (1 + seasonal_component)
        else:
            return 1 + (monthly_growth * month)
    
    def _calculate_seasonal_factor(self, scenario: CostScenario, month: int) -> float:
        """Calculate seasonal adjustment factor."""
        if scenario.usage_pattern == "seasonal":
            # Peak in Q4, trough in Q2
            seasonal_cycle = 0.15 * math.sin(2 * math.pi * (month - 3) / 12)
            return 1 + seasonal_cycle
        return 1.0
    
    def _calculate_optimization_factor(self, scenario: CostScenario, month: int) -> float:
        """Calculate cost optimization factor over time."""
        if scenario.optimization_level == "none":
            return 1.0
        elif scenario.optimization_level == "basic":
            # Gradual 10% optimization over 12 months
            max_optimization = 0.10
            optimization_rate = max_optimization * min(month / 12, 1.0)
            return 1 - optimization_rate
        elif scenario.optimization_level == "advanced":
            # Gradual 25% optimization over 18 months
            max_optimization = 0.25
            optimization_rate = max_optimization * min(month / 18, 1.0)
            return 1 - optimization_rate
        elif scenario.optimization_level == "aggressive":
            # Gradual 40% optimization over 24 months
            max_optimization = 0.40
            optimization_rate = max_optimization * min(month / 24, 1.0)
            return 1 - optimization_rate
        return 1.0
    
    async def _identify_savings_opportunities(
        self,
        infrastructure_data: Dict[str, Any],
        scenario: CostScenario,
        total_projected_cost: float
    ) -> Dict[str, float]:
        """Identify specific savings opportunities."""
        savings = {}
        
        for strategy_name, strategy in self.optimization_strategies.items():
            if scenario.optimization_level != "none":
                applicable_cost = total_projected_cost * 0.7  # Assume 70% of costs are optimizable
                potential_savings = applicable_cost * strategy["typical_savings"]
                
                # Adjust based on optimization level
                if scenario.optimization_level == "basic":
                    savings[strategy_name] = potential_savings * 0.4
                elif scenario.optimization_level == "advanced":
                    savings[strategy_name] = potential_savings * 0.7
                elif scenario.optimization_level == "aggressive":
                    savings[strategy_name] = potential_savings * 1.0
        
        return savings
    
    def _calculate_confidence_intervals(
        self,
        monthly_costs: List[float],
        confidence_level: float
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for cost projections."""
        total_cost = sum(monthly_costs)
        
        # Simplified confidence interval calculation
        # In practice, this would use more sophisticated statistical methods
        variance_factor = 1 - confidence_level
        lower_bound = total_cost * (1 - variance_factor)
        upper_bound = total_cost * (1 + variance_factor)
        
        return {
            "total_cost": (lower_bound, upper_bound),
            "annual_cost": (lower_bound / 3, upper_bound / 3),  # Assuming 3-year projection
            "monthly_average": (lower_bound / len(monthly_costs), upper_bound / len(monthly_costs))
        }
    
    def _create_error_projection(self, scenario: CostScenario, error_message: str) -> CostProjection:
        """Create error projection when calculation fails."""
        return CostProjection(
            scenario=scenario,
            time_horizon=0,
            monthly_costs=[],
            annual_costs=[],
            total_cost=0.0,
            savings_opportunities={},
            risk_adjusted_cost=0.0,
            confidence_intervals={"error": error_message}
        )
    
    async def generate_cost_optimization_recommendations(
        self,
        infrastructure_data: Dict[str, Any],
        current_costs: Dict[str, float],
        target_savings: float = 0.20
    ) -> Dict[str, Any]:
        """
        Generate specific cost optimization recommendations.
        
        Args:
            infrastructure_data: Current infrastructure setup
            current_costs: Current cost breakdown
            target_savings: Target savings percentage (default 20%)
            
        Returns:
            Detailed optimization recommendations
        """
        recommendations = {
            "target_savings_percentage": target_savings,
            "current_annual_cost": sum(current_costs.values()),
            "target_annual_savings": sum(current_costs.values()) * target_savings,
            "optimization_strategies": [],
            "implementation_roadmap": {},
            "risk_assessment": {}
        }
        
        # Analyze each optimization strategy
        for strategy_name, strategy in self.optimization_strategies.items():
            applicable_cost = self._calculate_applicable_cost(
                strategy_name, current_costs, infrastructure_data
            )
            
            potential_savings = applicable_cost * strategy["typical_savings"]
            
            if potential_savings > 1000:  # Only recommend if savings > $1000
                strategy_rec = {
                    "strategy": strategy_name,
                    "description": strategy["description"],
                    "applicable_cost": applicable_cost,
                    "potential_annual_savings": potential_savings,
                    "implementation_effort": strategy["implementation_effort"],
                    "risk_level": strategy["risk_level"],
                    "payback_period_months": self._calculate_payback_period(
                        strategy_name, potential_savings
                    ),
                    "specific_actions": await self._generate_specific_actions(
                        strategy_name, infrastructure_data
                    )
                }
                
                recommendations["optimization_strategies"].append(strategy_rec)
        
        # Sort by potential savings
        recommendations["optimization_strategies"].sort(
            key=lambda x: x["potential_annual_savings"], reverse=True
        )
        
        # Generate implementation roadmap
        recommendations["implementation_roadmap"] = await self._generate_implementation_roadmap(
            recommendations["optimization_strategies"]
        )
        
        return recommendations
    
    def _calculate_applicable_cost(
        self,
        strategy_name: str,
        current_costs: Dict[str, float],
        infrastructure_data: Dict[str, Any]
    ) -> float:
        """Calculate what portion of costs this optimization strategy applies to."""
        total_cost = sum(current_costs.values())
        
        # Strategy-specific applicability
        if strategy_name == "rightsizing":
            return current_costs.get("compute", 0) * 0.8  # 80% of compute costs
        elif strategy_name == "reserved_instances":
            return current_costs.get("compute", 0) * 0.6  # 60% of compute suitable for RI
        elif strategy_name == "spot_instances":
            return current_costs.get("compute", 0) * 0.3  # 30% suitable for spot
        elif strategy_name == "storage_optimization":
            return current_costs.get("storage", 0)
        elif strategy_name == "network_optimization":
            return current_costs.get("networking", 0)
        else:
            return total_cost * 0.5  # Default 50% applicability
    
    def _calculate_payback_period(self, strategy_name: str, annual_savings: float) -> int:
        """Calculate payback period in months for optimization strategy."""
        # Estimated implementation costs
        implementation_costs = {
            "rightsizing": 5000,
            "reserved_instances": 1000,
            "spot_instances": 10000,
            "auto_scaling": 8000,
            "storage_optimization": 3000,
            "network_optimization": 15000
        }
        
        impl_cost = implementation_costs.get(strategy_name, 5000)
        monthly_savings = annual_savings / 12
        
        if monthly_savings > 0:
            return math.ceil(impl_cost / monthly_savings)
        return 12  # Default 12 months if calculation fails
    
    async def _generate_specific_actions(
        self,
        strategy_name: str,
        infrastructure_data: Dict[str, Any]
    ) -> List[str]:
        """Generate specific actionable steps for each optimization strategy."""
        actions = {
            "rightsizing": [
                "Analyze CPU and memory utilization over past 30 days",
                "Identify over-provisioned instances (< 40% utilization)",
                "Create rightsizing recommendations with cost impact",
                "Implement gradual downsizing with monitoring",
                "Set up automated alerting for performance impacts"
            ],
            "reserved_instances": [
                "Analyze instance usage patterns for past 12 months",
                "Identify steady-state workloads suitable for RIs",
                "Calculate optimal RI mix (1-year vs 3-year)",
                "Purchase RIs for high-utilization instances",
                "Monitor RI utilization and coverage monthly"
            ],
            "spot_instances": [
                "Identify fault-tolerant workloads suitable for Spot",
                "Implement Spot instance request strategies",
                "Set up automated failover to On-Demand instances",
                "Configure diversified Spot fleet across AZs",
                "Monitor Spot interruption rates and adjust strategies"
            ],
            "auto_scaling": [
                "Implement Auto Scaling Groups for variable workloads",
                "Configure scaling policies based on CPU/memory metrics",
                "Set up predictive scaling for known patterns",
                "Test scaling policies under load conditions",
                "Monitor scaling events and optimize thresholds"
            ],
            "storage_optimization": [
                "Analyze storage access patterns and lifecycle",
                "Implement S3 Intelligent Tiering for frequently accessed data",
                "Move infrequently accessed data to IA/Glacier",
                "Set up automated lifecycle policies",
                "Review and optimize backup retention policies"
            ]
        }
        
        return actions.get(strategy_name, [])
    
    async def _generate_implementation_roadmap(
        self,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate implementation roadmap for optimization strategies."""
        # Sort strategies by effort and potential savings
        quick_wins = [s for s in strategies if s["implementation_effort"] == "low" and s["potential_annual_savings"] > 5000]
        medium_term = [s for s in strategies if s["implementation_effort"] == "medium"]
        long_term = [s for s in strategies if s["implementation_effort"] == "high"]
        
        return {
            "phase_1_quick_wins": {
                "timeline": "0-3 months",
                "strategies": [s["strategy"] for s in quick_wins],
                "expected_savings": sum(s["potential_annual_savings"] for s in quick_wins),
                "implementation_cost": sum(1000 for _ in quick_wins),  # Estimated
                "roi": "High"
            },
            "phase_2_medium_term": {
                "timeline": "3-9 months",
                "strategies": [s["strategy"] for s in medium_term],
                "expected_savings": sum(s["potential_annual_savings"] for s in medium_term),
                "implementation_cost": sum(5000 for _ in medium_term),  # Estimated
                "roi": "Medium-High"
            },
            "phase_3_long_term": {
                "timeline": "9-18 months",
                "strategies": [s["strategy"] for s in long_term],
                "expected_savings": sum(s["potential_annual_savings"] for s in long_term),
                "implementation_cost": sum(15000 for _ in long_term),  # Estimated
                "roi": "Medium"
            }
        }
    
    async def generate_finops_dashboard_data(
        self,
        projections: Dict[str, CostProjection],
        current_costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate data for FinOps dashboard visualization."""
        dashboard_data = {
            "cost_overview": {
                "current_monthly_cost": sum(current_costs.values()),
                "projected_annual_cost": {},
                "cost_trends": {},
                "savings_potential": {}
            },
            "scenario_comparison": {},
            "optimization_opportunities": {},
            "budget_alerts": [],
            "cost_allocation": current_costs
        }
        
        # Process each projection
        for scenario_name, projection in projections.items():
            annual_cost = projection.total_cost / (projection.time_horizon / 12) if projection.time_horizon > 0 else 0
            
            dashboard_data["cost_overview"]["projected_annual_cost"][scenario_name] = annual_cost
            dashboard_data["scenario_comparison"][scenario_name] = {
                "total_cost": projection.total_cost,
                "monthly_average": projection.total_cost / max(projection.time_horizon, 1),
                "savings_potential": sum(projection.savings_opportunities.values()),
                "confidence_level": projection.scenario.confidence_level
            }
        
        return dashboard_data