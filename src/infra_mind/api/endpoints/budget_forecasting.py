"""
Budget Forecasting endpoints for Infra Mind.

Handles cost predictions, budget planning, resource optimization, and financial analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from enum import Enum

router = APIRouter()
security = HTTPBearer()

# Data Models
class ForecastAccuracy(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BudgetStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OVER_BUDGET = "over_budget"
    UNDER_BUDGET = "under_budget"

class CostForecast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    forecast_name: str
    service_category: str = "all"
    forecast_period: str = "monthly"
    start_date: str
    end_date: str
    predicted_cost: float
    confidence_interval: Dict[str, float] = {"lower": 0.0, "upper": 0.0}
    accuracy: ForecastAccuracy = ForecastAccuracy.MEDIUM
    cost_breakdown: Dict[str, float] = {}
    growth_factors: List[Dict[str, Any]] = []
    assumptions: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class BudgetPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_name: str
    fiscal_year: str
    total_budget: float
    allocated_budget: float = 0.0
    spent_budget: float = 0.0
    remaining_budget: float = 0.0
    status: BudgetStatus = BudgetStatus.ON_TRACK
    service_allocations: Dict[str, float] = {}
    monthly_targets: List[Dict[str, Any]] = []
    approval_status: str = "draft"
    approved_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class OptimizationRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_type: str = "cost_optimization"
    service_name: str
    current_cost: float
    optimized_cost: float
    potential_savings: float
    savings_percentage: float
    optimization_actions: List[Dict[str, Any]] = []
    implementation_effort: str = "medium"
    risk_level: str = "low"
    timeframe: str = "30_days"
    impact_analysis: Dict[str, Any] = {}

# Endpoints

@router.get("/forecasts")
async def get_cost_forecasts(
    service_category: Optional[str] = None,
    period: Optional[str] = None,
    accuracy: Optional[ForecastAccuracy] = None
) -> List[CostForecast]:
    """Get cost forecasts with optional filters."""
    logger.info(f"Fetching cost forecasts with filters: category={service_category}, period={period}")
    
    # Sample data for demonstration
    forecasts = [
        CostForecast(
            forecast_name="AWS Infrastructure - Q1 2024",
            service_category="compute",
            forecast_period="quarterly",
            start_date="2024-01-01",
            end_date="2024-03-31",
            predicted_cost=125000.0,
            confidence_interval={"lower": 115000.0, "upper": 140000.0},
            accuracy=ForecastAccuracy.HIGH,
            cost_breakdown={
                "ec2": 75000.0,
                "ebs": 25000.0,
                "elb": 15000.0,
                "cloudwatch": 10000.0
            },
            growth_factors=[
                {"factor": "traffic_growth", "impact": 15.0, "description": "Expected 15% traffic increase"},
                {"factor": "new_features", "impact": 8.0, "description": "New ML features deployment"}
            ],
            assumptions=[
                "Current usage patterns continue",
                "No major architectural changes",
                "Reserved instance renewals at current rates"
            ]
        ),
        CostForecast(
            forecast_name="Storage and Database Costs",
            service_category="storage",
            forecast_period="monthly",
            start_date="2024-02-01",
            end_date="2024-02-29",
            predicted_cost=45000.0,
            confidence_interval={"lower": 42000.0, "upper": 50000.0},
            accuracy=ForecastAccuracy.MEDIUM,
            cost_breakdown={
                "rds": 25000.0,
                "s3": 15000.0,
                "dynamodb": 5000.0
            },
            growth_factors=[
                {"factor": "data_retention", "impact": 5.0, "description": "Extended data retention policy"}
            ],
            assumptions=[
                "Current data growth rate of 10% monthly",
                "No storage optimization initiatives"
            ]
        ),
        CostForecast(
            forecast_name="Multi-Cloud Networking",
            service_category="networking",
            forecast_period="annual",
            start_date="2024-01-01",
            end_date="2024-12-31",
            predicted_cost=180000.0,
            confidence_interval={"lower": 165000.0, "upper": 200000.0},
            accuracy=ForecastAccuracy.MEDIUM,
            cost_breakdown={
                "data_transfer": 100000.0,
                "load_balancers": 50000.0,
                "vpn_connections": 30000.0
            },
            growth_factors=[
                {"factor": "global_expansion", "impact": 25.0, "description": "New regions deployment"}
            ]
        )
    ]
    
    # Apply filters
    if service_category:
        forecasts = [f for f in forecasts if f.service_category.lower() == service_category.lower()]
    if period:
        forecasts = [f for f in forecasts if f.forecast_period.lower() == period.lower()]
    if accuracy:
        forecasts = [f for f in forecasts if f.accuracy == accuracy]
    
    return forecasts

@router.post("/forecasts")
async def create_cost_forecast(forecast_data: Dict[str, Any]) -> CostForecast:
    """Create a new cost forecast."""
    logger.info(f"Creating cost forecast: {forecast_data.get('forecast_name')}")
    
    forecast = CostForecast(
        forecast_name=forecast_data.get("forecast_name", "New Forecast"),
        service_category=forecast_data.get("service_category", "all"),
        forecast_period=forecast_data.get("forecast_period", "monthly"),
        start_date=forecast_data.get("start_date", datetime.now().strftime("%Y-%m-%d")),
        end_date=forecast_data.get("end_date", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")),
        predicted_cost=forecast_data.get("predicted_cost", 0.0),
        cost_breakdown=forecast_data.get("cost_breakdown", {}),
        assumptions=forecast_data.get("assumptions", [])
    )
    
    logger.success(f"Created cost forecast with ID: {forecast.id}")
    return forecast

@router.get("/forecasts/{forecast_id}")
async def get_forecast_details(forecast_id: str) -> CostForecast:
    """Get detailed information about a specific cost forecast."""
    logger.info(f"Fetching forecast details for ID: {forecast_id}")
    
    return CostForecast(
        id=forecast_id,
        forecast_name="Detailed AWS Infrastructure Forecast",
        service_category="compute",
        forecast_period="quarterly",
        start_date="2024-01-01",
        end_date="2024-03-31",
        predicted_cost=125000.0,
        confidence_interval={"lower": 115000.0, "upper": 140000.0},
        accuracy=ForecastAccuracy.HIGH,
        cost_breakdown={
            "ec2_instances": 45000.0,
            "ec2_reserved": 30000.0,
            "ebs_storage": 25000.0,
            "load_balancers": 15000.0,
            "cloudwatch": 10000.0
        },
        growth_factors=[
            {
                "factor": "user_growth",
                "impact": 15.0,
                "description": "Expected 15% user base growth",
                "confidence": "high",
                "data_source": "marketing_projections"
            },
            {
                "factor": "feature_rollout", 
                "impact": 8.0,
                "description": "New ML recommendation engine",
                "confidence": "medium",
                "data_source": "engineering_estimates"
            }
        ],
        assumptions=[
            "Current usage patterns continue with seasonal adjustments",
            "No major architectural changes or migrations",
            "Reserved instance renewals at current committed rates",
            "Average 10% monthly traffic growth",
            "No significant changes in service pricing"
        ]
    )

@router.get("/budget-plans")
async def get_budget_plans(
    fiscal_year: Optional[str] = None,
    status: Optional[BudgetStatus] = None,
    approved_only: Optional[bool] = None
) -> List[BudgetPlan]:
    """Get budget plans with optional filters."""
    logger.info(f"Fetching budget plans with filters: fiscal_year={fiscal_year}, status={status}")
    
    plans = [
        BudgetPlan(
            plan_name="FY2024 Infrastructure Budget",
            fiscal_year="2024",
            total_budget=2000000.0,
            allocated_budget=1800000.0,
            spent_budget=450000.0,
            remaining_budget=1550000.0,
            status=BudgetStatus.ON_TRACK,
            service_allocations={
                "compute": 800000.0,
                "storage": 400000.0,
                "networking": 300000.0,
                "security": 200000.0,
                "monitoring": 100000.0,
                "contingency": 200000.0
            },
            monthly_targets=[
                {"month": "2024-01", "target": 150000.0, "actual": 148000.0, "variance": -2000.0},
                {"month": "2024-02", "target": 155000.0, "actual": 162000.0, "variance": 7000.0},
                {"month": "2024-03", "target": 160000.0, "actual": 140000.0, "variance": -20000.0}
            ],
            approval_status="approved",
            approved_by="cfo@company.com"
        ),
        BudgetPlan(
            plan_name="Cloud Migration Budget - Phase 2",
            fiscal_year="2024",
            total_budget=500000.0,
            allocated_budget=450000.0,
            spent_budget=180000.0,
            remaining_budget=320000.0,
            status=BudgetStatus.AT_RISK,
            service_allocations={
                "migration_services": 200000.0,
                "new_infrastructure": 180000.0,
                "training": 50000.0,
                "consulting": 70000.0
            },
            approval_status="approved",
            approved_by="cto@company.com"
        ),
        BudgetPlan(
            plan_name="Q1 2024 Emergency Fund",
            fiscal_year="2024",
            total_budget=100000.0,
            allocated_budget=0.0,
            spent_budget=0.0,
            remaining_budget=100000.0,
            status=BudgetStatus.UNDER_BUDGET,
            service_allocations={
                "emergency_scaling": 60000.0,
                "incident_response": 40000.0
            },
            approval_status="pending"
        )
    ]
    
    # Apply filters
    if fiscal_year:
        plans = [p for p in plans if p.fiscal_year == fiscal_year]
    if status:
        plans = [p for p in plans if p.status == status]
    if approved_only:
        plans = [p for p in plans if p.approval_status == "approved"]
    
    return plans

@router.post("/budget-plans")
async def create_budget_plan(plan_data: Dict[str, Any]) -> BudgetPlan:
    """Create a new budget plan."""
    logger.info(f"Creating budget plan: {plan_data.get('plan_name')}")
    
    plan = BudgetPlan(
        plan_name=plan_data.get("plan_name", "New Budget Plan"),
        fiscal_year=plan_data.get("fiscal_year", "2024"),
        total_budget=plan_data.get("total_budget", 0.0),
        service_allocations=plan_data.get("service_allocations", {}),
        approval_status=plan_data.get("approval_status", "draft")
    )
    
    # Calculate remaining budget
    plan.remaining_budget = plan.total_budget - plan.spent_budget
    
    return plan

@router.get("/optimization")
async def get_optimization_recommendations(
    service_name: Optional[str] = None,
    min_savings: Optional[float] = None,
    implementation_effort: Optional[str] = None
) -> List[OptimizationRecommendation]:
    """Get cost optimization recommendations."""
    logger.info(f"Fetching optimization recommendations with filters: service={service_name}")
    
    recommendations = [
        OptimizationRecommendation(
            recommendation_type="rightsizing",
            service_name="ec2-instances",
            current_cost=45000.0,
            optimized_cost=32000.0,
            potential_savings=13000.0,
            savings_percentage=28.9,
            optimization_actions=[
                {
                    "action": "downsize_instances",
                    "description": "Reduce 15 m5.xlarge instances to m5.large",
                    "impact": "8000.0"
                },
                {
                    "action": "terminate_unused",
                    "description": "Remove 5 unused development instances",
                    "impact": "5000.0"
                }
            ],
            implementation_effort="low",
            risk_level="low",
            timeframe="7_days",
            impact_analysis={
                "performance_impact": "minimal",
                "availability_impact": "none",
                "user_impact": "none"
            }
        ),
        OptimizationRecommendation(
            recommendation_type="reserved_instances",
            service_name="database-servers",
            current_cost=25000.0,
            optimized_cost=17000.0,
            potential_savings=8000.0,
            savings_percentage=32.0,
            optimization_actions=[
                {
                    "action": "purchase_reserved_instances",
                    "description": "Convert 8 on-demand RDS instances to 1-year reserved",
                    "impact": "8000.0"
                }
            ],
            implementation_effort="medium",
            risk_level="low",
            timeframe="30_days",
            impact_analysis={
                "commitment_required": "1_year",
                "upfront_payment": "15000.0",
                "monthly_savings": "667.0"
            }
        ),
        OptimizationRecommendation(
            recommendation_type="storage_optimization",
            service_name="s3-storage",
            current_cost=15000.0,
            optimized_cost=9000.0,
            potential_savings=6000.0,
            savings_percentage=40.0,
            optimization_actions=[
                {
                    "action": "lifecycle_policies",
                    "description": "Implement intelligent tiering for infrequently accessed data",
                    "impact": "4000.0"
                },
                {
                    "action": "compression",
                    "description": "Enable compression for log files",
                    "impact": "2000.0"
                }
            ],
            implementation_effort="medium",
            risk_level="low",
            timeframe="14_days"
        ),
        OptimizationRecommendation(
            recommendation_type="scheduling",
            service_name="development-environment",
            current_cost=12000.0,
            optimized_cost=6000.0,
            potential_savings=6000.0,
            savings_percentage=50.0,
            optimization_actions=[
                {
                    "action": "auto_shutdown",
                    "description": "Implement automated start/stop for dev environments",
                    "impact": "6000.0"
                }
            ],
            implementation_effort="high",
            risk_level="medium",
            timeframe="45_days",
            impact_analysis={
                "developer_impact": "requires schedule coordination",
                "automation_required": True,
                "monitoring_needed": True
            }
        )
    ]
    
    # Apply filters
    if service_name:
        recommendations = [r for r in recommendations if service_name.lower() in r.service_name.lower()]
    if min_savings:
        recommendations = [r for r in recommendations if r.potential_savings >= min_savings]
    if implementation_effort:
        recommendations = [r for r in recommendations if r.implementation_effort.lower() == implementation_effort.lower()]
    
    return recommendations

@router.get("/analytics")
async def get_budget_analytics(timeframe: str = "12m") -> Dict[str, Any]:
    """Get budget and cost analytics."""
    logger.info(f"Fetching budget analytics for timeframe: {timeframe}")
    
    return {
        "cost_trends": {
            "monthly_costs": [
                {"month": "2023-01", "cost": 142000.0, "budget": 150000.0, "variance": -8000.0},
                {"month": "2023-02", "cost": 158000.0, "budget": 155000.0, "variance": 3000.0},
                {"month": "2023-03", "cost": 145000.0, "budget": 160000.0, "variance": -15000.0},
                {"month": "2023-04", "cost": 167000.0, "budget": 165000.0, "variance": 2000.0},
                {"month": "2023-05", "cost": 172000.0, "budget": 170000.0, "variance": 2000.0},
                {"month": "2023-06", "cost": 165000.0, "budget": 175000.0, "variance": -10000.0}
            ],
            "growth_rate": {
                "monthly_average": 2.3,
                "quarterly_average": 7.1,
                "annual_projected": 28.5
            }
        },
        "cost_breakdown": {
            "by_service": [
                {"service": "compute", "cost": 450000.0, "percentage": 45.0},
                {"service": "storage", "cost": 250000.0, "percentage": 25.0},
                {"service": "networking", "cost": 150000.0, "percentage": 15.0},
                {"service": "security", "cost": 100000.0, "percentage": 10.0},
                {"service": "monitoring", "cost": 50000.0, "percentage": 5.0}
            ],
            "by_environment": [
                {"environment": "production", "cost": 700000.0, "percentage": 70.0},
                {"environment": "staging", "cost": 200000.0, "percentage": 20.0},
                {"environment": "development", "cost": 100000.0, "percentage": 10.0}
            ]
        },
        "forecast_accuracy": {
            "last_quarter": {
                "predicted": 450000.0,
                "actual": 465000.0,
                "accuracy": 96.8,
                "variance": 15000.0
            },
            "historical_accuracy": [
                {"period": "Q1_2023", "accuracy": 94.2},
                {"period": "Q2_2023", "accuracy": 96.8},
                {"period": "Q3_2023", "accuracy": 91.5},
                {"period": "Q4_2023", "accuracy": 97.1}
            ]
        },
        "optimization_impact": {
            "total_identified_savings": 85000.0,
            "implemented_savings": 42000.0,
            "pending_implementation": 28000.0,
            "rejected_recommendations": 15000.0,
            "roi_percentage": 340.0
        },
        "budget_health": {
            "overall_status": "on_track",
            "burn_rate": {
                "current": 165000.0,
                "target": 170000.0,
                "variance_percentage": -2.9
            },
            "runway_months": 9.8,
            "budget_utilization": 67.5
        },
        "alerts_and_thresholds": [
            {
                "alert_type": "budget_threshold",
                "threshold": 80.0,
                "current": 67.5,
                "status": "ok"
            },
            {
                "alert_type": "cost_spike",
                "threshold": 20.0,
                "current": 8.5,
                "status": "ok"
            },
            {
                "alert_type": "forecast_accuracy",
                "threshold": 90.0,
                "current": 96.8,
                "status": "healthy"
            }
        ]
    }

@router.get("/reports/executive-summary")
async def get_executive_budget_summary() -> Dict[str, Any]:
    """Get executive budget summary report."""
    logger.info("Generating executive budget summary")
    
    return {
        "report_date": datetime.now().isoformat(),
        "reporting_period": "Q1 2024",
        "executive_summary": {
            "total_budget": 2000000.0,
            "spent_to_date": 675000.0,
            "remaining_budget": 1325000.0,
            "budget_utilization": 33.8,
            "projected_annual_spend": 2150000.0,
            "budget_variance": 150000.0,
            "variance_percentage": 7.5
        },
        "key_metrics": {
            "monthly_burn_rate": 165000.0,
            "cost_per_user": 12.50,
            "infrastructure_efficiency": 87.3,
            "roi_on_optimization": 340.0
        },
        "highlights": [
            "Successfully reduced compute costs by 15% through rightsizing initiative",
            "Identified $85k in additional optimization opportunities",
            "On track to meet annual budget with 7.5% positive variance",
            "Implemented automated cost monitoring and alerting"
        ],
        "risks_and_concerns": [
            "Q4 scaling requirements may exceed current projections",
            "Cloud provider pricing changes could impact forecasts",
            "New compliance requirements may require additional security investments"
        ],
        "recommendations": [
            "Accelerate implementation of pending optimization recommendations",
            "Negotiate multi-year discounts with primary cloud providers",
            "Establish contingency budget for compliance initiatives",
            "Implement cost allocation tags for better visibility"
        ],
        "next_actions": [
            {
                "action": "Optimize development environment scheduling",
                "owner": "DevOps Team",
                "due_date": "2024-02-15",
                "expected_savings": 6000.0
            },
            {
                "action": "Purchase reserved instances for stable workloads",
                "owner": "Cloud Architecture Team", 
                "due_date": "2024-02-28",
                "expected_savings": 8000.0
            }
        ]
    }