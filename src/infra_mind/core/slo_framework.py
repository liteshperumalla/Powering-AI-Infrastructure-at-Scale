"""
Service Level Objectives (SLO) Framework.

Implements Google's SRE approach to SLOs and error budgets:
- Define SLIs (Service Level Indicators)
- Track SLOs (Service Level Objectives)
- Calculate error budgets
- Alert on budget exhaustion
- Historical SLO compliance tracking
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class SLIType(Enum):
    """Types of Service Level Indicators."""
    AVAILABILITY = "availability"  # Uptime percentage
    LATENCY = "latency"  # Response time percentiles
    ERROR_RATE = "error_rate"  # Error percentage
    THROUGHPUT = "throughput"  # Requests per second
    DATA_FRESHNESS = "data_freshness"  # Data staleness
    COMPLETION_RATE = "completion_rate"  # Task success rate


class SLOPeriod(Enum):
    """SLO measurement periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class SLI:
    """Service Level Indicator - what we measure."""
    name: str
    sli_type: SLIType
    description: str
    measurement_query: str  # How to measure this SLI
    unit: str  # e.g., "ms", "%", "req/s"
    good_threshold: float  # What constitutes a "good" event
    total_events_query: str  # How to count total events


@dataclass
class SLO:
    """Service Level Objective - target for SLI."""
    name: str
    sli: SLI
    target_percentage: float  # e.g., 99.9% for availability
    period: SLOPeriod
    description: str
    owner: str
    severity: str = "critical"  # critical, high, medium, low


@dataclass
class ErrorBudget:
    """Error budget tracking."""
    slo: SLO
    total_budget: float  # Total allowed failures
    consumed: float  # Failures so far
    remaining: float  # Remaining budget
    percentage_remaining: float
    period_start: datetime
    period_end: datetime
    is_exhausted: bool = False


@dataclass
class SLOCompliance:
    """SLO compliance measurement."""
    slo: SLO
    actual_percentage: float
    target_percentage: float
    is_compliant: bool
    margin: float  # How much above/below target
    measurement_period: Dict[str, datetime]
    sample_size: int


class SLOFramework:
    """
    Manages SLOs, tracks compliance, and calculates error budgets.

    Features:
    - Pre-defined SLOs for common service metrics
    - Real-time compliance tracking
    - Error budget calculations
    - Alert generation
    - Historical trending
    """

    # Standard SLOs for the platform
    STANDARD_SLOS = {
        "api_availability": SLO(
            name="API Availability",
            sli=SLI(
                name="api_uptime",
                sli_type=SLIType.AVAILABILITY,
                description="Percentage of successful API requests",
                measurement_query="http_requests_total{status!~'5..'}",
                unit="%",
                good_threshold=1.0,  # Non-5xx is good
                total_events_query="http_requests_total"
            ),
            target_percentage=99.9,  # 99.9% uptime
            period=SLOPeriod.MONTHLY,
            description="API should be available 99.9% of the time",
            owner="platform-team"
        ),

        "api_latency_p95": SLO(
            name="API Latency (P95)",
            sli=SLI(
                name="api_response_time_p95",
                sli_type=SLIType.LATENCY,
                description="95th percentile API response time",
                measurement_query="histogram_quantile(0.95, http_request_duration_seconds)",
                unit="ms",
                good_threshold=500.0,  # <500ms is good
                total_events_query="http_requests_total"
            ),
            target_percentage=95.0,  # 95% of requests <500ms
            period=SLOPeriod.DAILY,
            description="95% of API requests complete in <500ms",
            owner="backend-team"
        ),

        "api_latency_p99": SLO(
            name="API Latency (P99)",
            sli=SLI(
                name="api_response_time_p99",
                sli_type=SLIType.LATENCY,
                description="99th percentile API response time",
                measurement_query="histogram_quantile(0.99, http_request_duration_seconds)",
                unit="ms",
                good_threshold=2000.0,  # <2s is good
                total_events_query="http_requests_total"
            ),
            target_percentage=99.0,  # 99% of requests <2s
            period=SLOPeriod.DAILY,
            description="99% of API requests complete in <2s",
            owner="backend-team",
            severity="high"
        ),

        "dashboard_load_time": SLO(
            name="Dashboard Load Time",
            sli=SLI(
                name="dashboard_load_duration",
                sli_type=SLIType.LATENCY,
                description="Dashboard page load time",
                measurement_query="dashboard_load_duration_seconds",
                unit="s",
                good_threshold=3.0,  # <3s is good
                total_events_query="dashboard_loads_total"
            ),
            target_percentage=90.0,  # 90% load in <3s
            period=SLOPeriod.WEEKLY,
            description="90% of dashboard loads complete in <3 seconds",
            owner="frontend-team"
        ),

        "llm_api_success_rate": SLO(
            name="LLM API Success Rate",
            sli=SLI(
                name="llm_success_rate",
                sli_type=SLIType.COMPLETION_RATE,
                description="Percentage of successful LLM API calls",
                measurement_query="llm_requests_total{status='success'}",
                unit="%",
                good_threshold=1.0,
                total_events_query="llm_requests_total"
            ),
            target_percentage=99.0,  # 99% success
            period=SLOPeriod.DAILY,
            description="99% of LLM API calls succeed",
            owner="ai-team"
        ),

        "assessment_completion_rate": SLO(
            name="Assessment Completion Rate",
            sli=SLI(
                name="assessment_completion",
                sli_type=SLIType.COMPLETION_RATE,
                description="Percentage of assessments that complete successfully",
                measurement_query="assessments_completed_total",
                unit="%",
                good_threshold=1.0,
                total_events_query="assessments_started_total"
            ),
            target_percentage=95.0,  # 95% completion
            period=SLOPeriod.WEEKLY,
            description="95% of started assessments complete successfully",
            owner="product-team"
        ),

        "database_query_latency": SLO(
            name="Database Query Latency",
            sli=SLI(
                name="db_query_duration_p95",
                sli_type=SLIType.LATENCY,
                description="95th percentile database query time",
                measurement_query="histogram_quantile(0.95, database_query_duration_seconds)",
                unit="ms",
                good_threshold=100.0,  # <100ms is good
                total_events_query="database_queries_total"
            ),
            target_percentage=99.0,  # 99% of queries <100ms
            period=SLOPeriod.DAILY,
            description="99% of database queries complete in <100ms",
            owner="platform-team",
            severity="high"
        ),

        "cache_hit_rate": SLO(
            name="Cache Hit Rate",
            sli=SLI(
                name="cache_hit_ratio",
                sli_type=SLIType.THROUGHPUT,
                description="Percentage of cache hits vs misses",
                measurement_query="cache_hits_total / (cache_hits_total + cache_misses_total)",
                unit="%",
                good_threshold=0.8,  # >80% hit rate is good
                total_events_query="cache_requests_total"
            ),
            target_percentage=80.0,  # 80% hit rate
            period=SLOPeriod.DAILY,
            description="Cache hit rate above 80%",
            owner="platform-team",
            severity="medium"
        ),

        "websocket_connection_success": SLO(
            name="WebSocket Connection Success",
            sli=SLI(
                name="websocket_connect_success",
                sli_type=SLIType.COMPLETION_RATE,
                description="Percentage of successful WebSocket connections",
                measurement_query="websocket_connections_successful_total",
                unit="%",
                good_threshold=1.0,
                total_events_query="websocket_connections_attempted_total"
            ),
            target_percentage=99.5,  # 99.5% success
            period=SLOPeriod.DAILY,
            description="99.5% of WebSocket connections succeed",
            owner="realtime-team"
        )
    }

    def __init__(self, prometheus_client=None):
        """
        Initialize SLO framework.

        Args:
            prometheus_client: Prometheus client for metric queries (optional)
        """
        self.prometheus_client = prometheus_client
        self.custom_slos: Dict[str, SLO] = {}

        logger.info(f"SLOFramework initialized with {len(self.STANDARD_SLOS)} standard SLOs")

    def get_slo(self, slo_name: str) -> Optional[SLO]:
        """Get SLO by name."""
        return self.STANDARD_SLOS.get(slo_name) or self.custom_slos.get(slo_name)

    def register_custom_slo(self, slo: SLO):
        """Register a custom SLO."""
        self.custom_slos[slo.name] = slo
        logger.info(f"Registered custom SLO: {slo.name}")

    def calculate_error_budget(
        self,
        slo: SLO,
        actual_percentage: float,
        total_events: int,
        period_start: datetime,
        period_end: datetime
    ) -> ErrorBudget:
        """
        Calculate error budget for an SLO.

        Args:
            slo: Service Level Objective
            actual_percentage: Actual measured percentage
            total_events: Total number of events in period
            period_start: Start of measurement period
            period_end: End of measurement period

        Returns:
            Error budget calculation
        """
        # Calculate allowed failures
        total_budget = total_events * (1 - (slo.target_percentage / 100))

        # Calculate actual failures
        actual_failures = total_events * (1 - (actual_percentage / 100))

        # Calculate remaining budget
        consumed = actual_failures
        remaining = max(0, total_budget - consumed)
        percentage_remaining = (remaining / total_budget * 100) if total_budget > 0 else 0

        # Check if budget exhausted
        is_exhausted = remaining <= 0

        budget = ErrorBudget(
            slo=slo,
            total_budget=total_budget,
            consumed=consumed,
            remaining=remaining,
            percentage_remaining=percentage_remaining,
            period_start=period_start,
            period_end=period_end,
            is_exhausted=is_exhausted
        )

        if is_exhausted:
            logger.warning(
                f"⚠️  Error budget EXHAUSTED for {slo.name}: "
                f"{consumed:.2f}/{total_budget:.2f} failures"
            )

        return budget

    def check_slo_compliance(
        self,
        slo: SLO,
        good_events: int,
        total_events: int,
        period_start: datetime,
        period_end: datetime
    ) -> SLOCompliance:
        """
        Check if SLO is being met.

        Args:
            slo: Service Level Objective
            good_events: Number of "good" events
            total_events: Total number of events
            period_start: Start of measurement period
            period_end: End of measurement period

        Returns:
            SLO compliance status
        """
        if total_events == 0:
            actual_percentage = 100.0
        else:
            actual_percentage = (good_events / total_events) * 100

        is_compliant = actual_percentage >= slo.target_percentage
        margin = actual_percentage - slo.target_percentage

        compliance = SLOCompliance(
            slo=slo,
            actual_percentage=actual_percentage,
            target_percentage=slo.target_percentage,
            is_compliant=is_compliant,
            margin=margin,
            measurement_period={
                "start": period_start,
                "end": period_end
            },
            sample_size=total_events
        )

        if not is_compliant:
            logger.warning(
                f"⚠️  SLO VIOLATION: {slo.name} - "
                f"Actual: {actual_percentage:.2f}%, Target: {slo.target_percentage}%"
            )

        return compliance

    def get_all_slos(self) -> Dict[str, SLO]:
        """Get all registered SLOs (standard + custom)."""
        return {**self.STANDARD_SLOS, **self.custom_slos}

    def generate_slo_report(
        self,
        slo_measurements: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive SLO report.

        Args:
            slo_measurements: Dict of {slo_name: {good_events, total_events}}

        Returns:
            SLO report with compliance and budgets
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=30)  # Last 30 days

        report = {
            "generated_at": now.isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": now.isoformat()
            },
            "slos": {},
            "summary": {
                "total_slos": 0,
                "compliant": 0,
                "violated": 0,
                "budgets_exhausted": 0
            }
        }

        for slo_name, measurements in slo_measurements.items():
            slo = self.get_slo(slo_name)
            if not slo:
                continue

            good_events = measurements.get("good_events", 0)
            total_events = measurements.get("total_events", 0)

            # Check compliance
            compliance = self.check_slo_compliance(
                slo, good_events, total_events, period_start, now
            )

            # Calculate error budget
            budget = self.calculate_error_budget(
                slo, compliance.actual_percentage, total_events, period_start, now
            )

            # Add to report
            report["slos"][slo_name] = {
                "target": slo.target_percentage,
                "actual": compliance.actual_percentage,
                "is_compliant": compliance.is_compliant,
                "margin": compliance.margin,
                "error_budget": {
                    "total": budget.total_budget,
                    "consumed": budget.consumed,
                    "remaining": budget.remaining,
                    "percentage_remaining": budget.percentage_remaining,
                    "is_exhausted": budget.is_exhausted
                },
                "sample_size": total_events
            }

            # Update summary
            report["summary"]["total_slos"] += 1
            if compliance.is_compliant:
                report["summary"]["compliant"] += 1
            else:
                report["summary"]["violated"] += 1
            if budget.is_exhausted:
                report["summary"]["budgets_exhausted"] += 1

        return report


# Singleton instance
_slo_framework_instance = None

def get_slo_framework(prometheus_client=None) -> SLOFramework:
    """Get or create SLO framework instance."""
    global _slo_framework_instance

    if _slo_framework_instance is None:
        _slo_framework_instance = SLOFramework(prometheus_client)

    return _slo_framework_instance
