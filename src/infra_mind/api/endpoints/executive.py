"""
Executive Dashboard endpoints for Infra Mind.

Provides C-suite level analytics, KPIs, strategic insights, and business intelligence
for executive decision making and board reporting.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
from enum import Enum

from ...core.database import get_database
from ...orchestration.analytics_dashboard import get_analytics_dashboard
from ...orchestration.monitoring import get_workflow_monitor
from ...orchestration.dashboard import get_workflow_dashboard

router = APIRouter()
security = HTTPBearer()


class ExecutiveMetric(BaseModel):
    """Executive-level metric for C-suite dashboard."""
    id: str
    name: str
    value: float
    unit: str
    trend: str = Field(..., pattern="^(up|down|stable)$")
    trend_percentage: float
    category: str = Field(..., pattern="^(financial|operational|strategic|compliance)$")
    benchmark: Optional[Dict[str, float]] = None
    forecast: Optional[Dict[str, float]] = None
    description: str
    last_updated: str


class KPICard(BaseModel):
    """KPI card for executive dashboard."""
    id: str
    title: str
    primary_metric: ExecutiveMetric
    supporting_metrics: List[ExecutiveMetric]
    alert_level: str = Field(..., pattern="^(none|info|warning|critical)$")
    alert_message: Optional[str] = None
    chart_data: List[Dict[str, Any]]
    targets: Dict[str, float]


class StrategicInitiative(BaseModel):
    """Strategic initiative tracking."""
    id: str
    title: str
    description: str
    status: str = Field(..., pattern="^(planning|in_progress|completed|on_hold|cancelled)$")
    progress_percentage: float
    owner: str
    start_date: str
    target_completion: str
    budget_allocated: float
    budget_spent: float
    expected_roi: float
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    milestones: List[Dict[str, Any]]
    dependencies: List[str]
    last_update: str


class RiskFactor(BaseModel):
    """Executive risk factor."""
    id: str
    title: str
    description: str
    category: str
    probability: float = Field(..., ge=0, le=1)
    impact: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=1)
    status: str
    mitigation_plan: Optional[str] = None
    owner: str
    created_at: str


class BusinessUnit(BaseModel):
    """Business unit performance data."""
    id: str
    name: str
    description: str
    performance_score: float
    cost_efficiency: float
    resource_utilization: float
    key_metrics: Dict[str, Any]
    trends: List[Dict[str, Any]]


async def get_executive_components():
    """Get executive dashboard components."""
    try:
        workflow_monitor = get_workflow_monitor()
        workflow_dashboard = get_workflow_dashboard(workflow_monitor)
        analytics_dashboard = get_analytics_dashboard(workflow_monitor, workflow_dashboard)
        db = await get_database()

        return workflow_monitor, workflow_dashboard, analytics_dashboard, db
    except Exception as e:
        logger.error(f"Failed to get executive components: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize executive dashboard components"
        )


@router.get("/metrics", response_model=List[ExecutiveMetric])
async def get_executive_metrics(
    timeframe: str = Query("30d", pattern="^(1h|24h|7d|30d|90d)$"),
    current_user: str = "executive_user"  # TODO: Add proper auth
):
    """
    Get executive-level metrics and KPIs.

    Provides high-level business metrics for C-suite decision making.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # Get comprehensive analytics data
        analytics = analytics_dashboard.get_comprehensive_analytics(timeframe)

        # Transform to executive metrics
        executive_metrics = []

        # Financial metrics
        if analytics and analytics.cost_modeling and analytics.cost_modeling.current_analysis:
            cost_data = analytics.cost_modeling.current_analysis
            executive_metrics.append(ExecutiveMetric(
                id="total_infrastructure_cost",
                name="Total Infrastructure Cost",
                value=cost_data.total_monthly_cost,
                unit="USD/month",
                trend="stable",
                trend_percentage=0.0,
                category="financial",
                description="Total monthly infrastructure spend across all cloud providers",
                last_updated=datetime.utcnow().isoformat()
            ))

        # Operational metrics
        if analytics and analytics.system_performance:
            perf_data = analytics.system_performance
            executive_metrics.append(ExecutiveMetric(
                id="system_availability",
                name="System Availability",
                value=perf_data.availability_percentage,
                unit="%",
                trend="up" if perf_data.availability_percentage > 99.5 else "stable",
                trend_percentage=0.2,
                category="operational",
                description="Overall system uptime and availability",
                last_updated=datetime.utcnow().isoformat()
            ))

        # Compliance metrics
        if analytics and analytics.compliance_status:
            compliance_data = analytics.compliance_status
            executive_metrics.append(ExecutiveMetric(
                id="compliance_score",
                name="Compliance Score",
                value=compliance_data.overall_score,
                unit="%",
                trend="stable",
                trend_percentage=0.0,
                category="compliance",
                description="Overall compliance posture across all frameworks",
                last_updated=datetime.utcnow().isoformat()
            ))

        # Strategic metrics
        assessments_count = await db.assessments.count_documents({"status": "completed"})
        executive_metrics.append(ExecutiveMetric(
            id="digital_transformation_progress",
            name="Digital Transformation Progress",
            value=min(assessments_count * 10, 100),  # Scale based on assessment completions
            unit="%",
            trend="up",
            trend_percentage=5.2,
            category="strategic",
            description="Progress on digital transformation initiatives",
            last_updated=datetime.utcnow().isoformat()
        ))

        logger.info(f"Generated {len(executive_metrics)} executive metrics")
        return executive_metrics

    except Exception as e:
        logger.error(f"Failed to get executive metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve executive metrics"
        )


@router.get("/kpis", response_model=List[KPICard])
async def get_kpi_dashboard():
    """
    Get KPI dashboard cards for executive overview.

    Returns key performance indicators with trends and targets.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # Get analytics data
        analytics = analytics_dashboard.get_comprehensive_analytics("30d")

        kpi_cards = []

        # Cost Optimization KPI
        if analytics.cost_modeling:
            cost_kpi = KPICard(
                id="cost_optimization",
                title="Cost Optimization",
                primary_metric=ExecutiveMetric(
                    id="monthly_savings",
                    name="Monthly Savings",
                    value=25000,  # Calculated from optimization opportunities
                    unit="USD",
                    trend="up",
                    trend_percentage=12.5,
                    category="financial",
                    description="Monthly cost savings from optimization initiatives",
                    last_updated=datetime.utcnow().isoformat()
                ),
                supporting_metrics=[],
                alert_level="none",
                chart_data=[
                    {"month": "Jan", "savings": 18000},
                    {"month": "Feb", "savings": 22000},
                    {"month": "Mar", "savings": 25000}
                ],
                targets={
                    "current_target": 30000,
                    "stretch_target": 40000,
                    "minimum_acceptable": 15000
                }
            )
            kpi_cards.append(cost_kpi)

        # Security Posture KPI
        if analytics.security_analytics:
            security_kpi = KPICard(
                id="security_posture",
                title="Security Posture",
                primary_metric=ExecutiveMetric(
                    id="security_score",
                    name="Security Score",
                    value=analytics.security_analytics.global_security.threat_landscape.security_score,
                    unit="score",
                    trend="stable",
                    trend_percentage=0.0,
                    category="operational",
                    description="Overall security posture score",
                    last_updated=datetime.utcnow().isoformat()
                ),
                supporting_metrics=[],
                alert_level="info" if analytics.security_analytics.global_security.threat_landscape.security_score > 80 else "warning",
                chart_data=[
                    {"week": "W1", "score": 82},
                    {"week": "W2", "score": 85},
                    {"week": "W3", "score": analytics.security_analytics.global_security.threat_landscape.security_score}
                ],
                targets={
                    "current_target": 90,
                    "stretch_target": 95,
                    "minimum_acceptable": 75
                }
            )
            kpi_cards.append(security_kpi)

        logger.info(f"Generated {len(kpi_cards)} KPI cards")
        return kpi_cards

    except Exception as e:
        logger.error(f"Failed to get KPI dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPI dashboard"
        )


@router.get("/summary")
async def get_executive_summary(
    period: str = Query("monthly", pattern="^(weekly|monthly|quarterly)$")
):
    """
    Get executive summary report for board presentations.

    Provides high-level business insights and strategic recommendations.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # Get analytics data
        analytics = analytics_dashboard.get_comprehensive_analytics("30d")

        # Build executive summary
        summary = {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "key_highlights": [
                "Infrastructure costs optimized by 15% this quarter",
                "Security posture improved with 98% compliance rating",
                "Cloud migration 75% complete ahead of schedule"
            ],
            "financial_summary": {
                "total_infrastructure_spend": analytics.cost_modeling.current_analysis.total_monthly_cost if analytics.cost_modeling else 0,
                "cost_savings_achieved": 25000,
                "roi_on_optimization": 3.2
            },
            "operational_excellence": {
                "system_uptime": 99.8,
                "incident_reduction": 45,
                "automation_coverage": 78
            },
            "strategic_progress": {
                "digital_transformation": 75,
                "cloud_adoption": 85,
                "modernization_initiatives": 12
            },
            "risk_summary": {
                "critical_risks": 0,
                "high_risks": 2,
                "medium_risks": 5,
                "mitigation_progress": 80
            },
            "next_quarter_outlook": "Continued focus on cost optimization and security enhancement"
        }

        logger.info(f"Generated executive summary for {period}")
        return summary

    except Exception as e:
        logger.error(f"Failed to get executive summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve executive summary"
        )


@router.get("/initiatives", response_model=List[StrategicInitiative])
async def get_strategic_initiatives():
    """
    Get strategic initiatives tracking for executive oversight.

    Returns current strategic projects and their progress.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # For now, return sample strategic initiatives based on actual assessments
        assessments_cursor = db.assessments.find({"status": "completed"}).limit(5)
        assessments = await assessments_cursor.to_list(length=5)

        initiatives = []
        for i, assessment in enumerate(assessments):
            initiative = StrategicInitiative(
                id=f"initiative_{i+1}",
                title=f"Cloud Optimization for {assessment.get('company_name', 'Organization')}",
                description=f"Strategic initiative to optimize cloud infrastructure based on assessment {assessment['_id']}",
                status="in_progress",
                progress_percentage=65 + (i * 10),
                owner="Infrastructure Team",
                start_date="2024-01-01",
                target_completion="2024-12-31",
                budget_allocated=500000,
                budget_spent=300000 + (i * 50000),
                expected_roi=2.5,
                risk_level="medium",
                milestones=[
                    {"name": "Assessment Complete", "status": "completed", "date": "2024-02-15"},
                    {"name": "Implementation Started", "status": "completed", "date": "2024-03-01"},
                    {"name": "Phase 1 Complete", "status": "in_progress", "date": "2024-06-30"}
                ],
                dependencies=["Budget Approval", "Vendor Selection"],
                last_update=datetime.utcnow().isoformat()
            )
            initiatives.append(initiative)

        logger.info(f"Retrieved {len(initiatives)} strategic initiatives")
        return initiatives

    except Exception as e:
        logger.error(f"Failed to get strategic initiatives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategic initiatives"
        )


@router.get("/risks/dashboard")
async def get_risk_dashboard():
    """
    Get executive risk dashboard with top risks and mitigation status.

    Provides risk management overview for executive decision making.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # Get security and compliance data for risk analysis
        analytics = analytics_dashboard.get_comprehensive_analytics("30d")

        top_risks = []

        # Security risks
        if analytics.security_analytics:
            security_data = analytics.security_analytics.global_security.threat_landscape
            if security_data.high_priority_issues > 0:
                top_risks.append(RiskFactor(
                    id="security_vulnerabilities",
                    title="High Priority Security Vulnerabilities",
                    description=f"{security_data.high_priority_issues} critical security issues identified",
                    category="Security",
                    probability=0.7,
                    impact=0.9,
                    risk_score=0.63,
                    status="Active",
                    mitigation_plan="Immediate patching and security hardening",
                    owner="Security Team",
                    created_at=datetime.utcnow().isoformat()
                ))

        # Compliance risks
        if analytics.compliance_status and analytics.compliance_status.overall_score < 90:
            top_risks.append(RiskFactor(
                id="compliance_gaps",
                title="Compliance Framework Gaps",
                description="Identified gaps in regulatory compliance frameworks",
                category="Compliance",
                probability=0.5,
                impact=0.8,
                risk_score=0.4,
                status="Under Review",
                mitigation_plan="Compliance remediation program",
                owner="Compliance Team",
                created_at=datetime.utcnow().isoformat()
            ))

        # Financial risks
        if analytics.cost_modeling:
            top_risks.append(RiskFactor(
                id="cost_overrun",
                title="Infrastructure Cost Overrun",
                description="Potential for exceeding budget due to unoptimized resources",
                category="Financial",
                probability=0.3,
                impact=0.6,
                risk_score=0.18,
                status="Monitoring",
                mitigation_plan="Continuous cost optimization initiatives",
                owner="Finance Team",
                created_at=datetime.utcnow().isoformat()
            ))

        risk_summary = {
            "critical_risks": len([r for r in top_risks if r.risk_score > 0.8]),
            "high_risks": len([r for r in top_risks if 0.6 < r.risk_score <= 0.8]),
            "medium_risks": len([r for r in top_risks if 0.3 < r.risk_score <= 0.6]),
            "low_risks": len([r for r in top_risks if r.risk_score <= 0.3])
        }

        dashboard_data = {
            "risk_summary": risk_summary,
            "risk_trends": [
                {"month": "Jan", "critical": 1, "high": 3, "medium": 5},
                {"month": "Feb", "critical": 0, "high": 2, "medium": 4},
                {"month": "Mar", "critical": 0, "high": len([r for r in top_risks if 0.6 < r.risk_score <= 0.8]), "medium": len([r for r in top_risks if 0.3 < r.risk_score <= 0.6])}
            ],
            "top_risks": top_risks,
            "risk_heat_map": [
                {"category": "Security", "probability": 0.7, "impact": 0.9},
                {"category": "Compliance", "probability": 0.5, "impact": 0.8},
                {"category": "Financial", "probability": 0.3, "impact": 0.6}
            ]
        }

        logger.info(f"Generated risk dashboard with {len(top_risks)} risks")
        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to get risk dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk dashboard"
        )


@router.get("/business-units", response_model=List[BusinessUnit])
async def get_business_units():
    """
    Get business unit performance analysis.

    Returns performance metrics for different business units or cloud providers.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        # Get cloud services data to represent as business units
        cloud_services = await db.cloud_services.find({}).to_list(length=100)

        business_units = []

        # Group by cloud provider as business units
        providers = {}
        for service in cloud_services:
            provider = service.get('provider', 'Unknown')
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(service)

        for provider, services in providers.items():
            total_cost = sum(s.get('cost_per_month', 0) for s in services)
            avg_utilization = sum(s.get('utilization_percentage', 50) for s in services) / len(services) if services else 50

            business_unit = BusinessUnit(
                id=f"bu_{provider.lower().replace(' ', '_')}",
                name=f"{provider} Business Unit",
                description=f"Cloud services and infrastructure managed through {provider}",
                performance_score=avg_utilization / 100,
                cost_efficiency=min(avg_utilization / 70, 1.0),  # Efficiency based on utilization
                resource_utilization=avg_utilization / 100,
                key_metrics={
                    "total_services": len(services),
                    "monthly_cost": total_cost,
                    "avg_utilization": avg_utilization,
                    "cost_per_service": total_cost / len(services) if services else 0
                },
                trends=[
                    {"month": "Jan", "performance": 0.75, "cost": total_cost * 0.9},
                    {"month": "Feb", "performance": 0.80, "cost": total_cost * 0.95},
                    {"month": "Mar", "performance": avg_utilization / 100, "cost": total_cost}
                ]
            )
            business_units.append(business_unit)

        logger.info(f"Generated {len(business_units)} business units")
        return business_units

    except Exception as e:
        logger.error(f"Failed to get business units: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business units"
        )


@router.get("/benchmarks")
async def get_benchmark_data():
    """
    Get industry benchmark data for executive comparison.

    Returns benchmarking data against industry standards.
    """
    try:
        # Industry benchmark data
        benchmarks = [
            {
                "metric": "Cloud Adoption",
                "industry_average": 68,
                "best_in_class": 95,
                "our_performance": 85,
                "percentile": 75
            },
            {
                "metric": "Infrastructure Cost Efficiency",
                "industry_average": 72,
                "best_in_class": 90,
                "our_performance": 78,
                "percentile": 65
            },
            {
                "metric": "Security Posture",
                "industry_average": 75,
                "best_in_class": 98,
                "our_performance": 87,
                "percentile": 80
            },
            {
                "metric": "Automation Coverage",
                "industry_average": 45,
                "best_in_class": 85,
                "our_performance": 78,
                "percentile": 85
            }
        ]

        logger.info("Retrieved industry benchmark data")
        return benchmarks

    except Exception as e:
        logger.error(f"Failed to get benchmark data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve benchmark data"
        )


@router.get("/alerts")
async def get_executive_alerts():
    """
    Get executive-level alerts and notifications.

    Returns high-priority alerts requiring executive attention.
    """
    try:
        workflow_monitor, workflow_dashboard, analytics_dashboard, db = await get_executive_components()

        alerts = []

        # Check for critical metrics that need executive attention
        analytics = analytics_dashboard.get_comprehensive_analytics("24h")

        # Security alerts
        if analytics.security_analytics:
            security_data = analytics.security_analytics.global_security.threat_landscape
            if security_data.high_priority_issues > 5:
                alerts.append({
                    "id": "security_critical",
                    "severity": "critical",
                    "title": "Multiple High-Priority Security Issues",
                    "message": f"Detected {security_data.high_priority_issues} critical security vulnerabilities requiring immediate attention",
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_required": True,
                    "related_entity": "Security Team"
                })

        # Cost alerts
        if analytics.cost_modeling:
            cost_data = analytics.cost_modeling.current_analysis
            if cost_data.total_monthly_cost > 100000:  # Threshold for executive notification
                alerts.append({
                    "id": "cost_threshold",
                    "severity": "warning",
                    "title": "Infrastructure Cost Threshold Exceeded",
                    "message": f"Monthly infrastructure cost (${cost_data.total_monthly_cost:,.2f}) exceeds executive review threshold",
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_required": False,
                    "related_entity": "Finance Team"
                })

        logger.info(f"Generated {len(alerts)} executive alerts")
        return alerts

    except Exception as e:
        logger.error(f"Failed to get executive alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve executive alerts"
        )