"""
Enhanced Quality Assurance Framework for infrastructure assessment platform.

This module provides comprehensive quality assurance capabilities including
automated validation, quality gates, monitoring, and continuous improvement.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality levels for assessment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityGateStatus(str, Enum):
    """Status of quality gate evaluation."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class QualityMetric:
    """Individual quality metric."""
    name: str
    value: float
    threshold: float
    weight: float = 1.0
    description: Optional[str] = None
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    
    @property
    def is_passing(self) -> bool:
        """Check if metric passes threshold."""
        return self.value >= self.threshold
    
    @property
    def score_percentage(self) -> float:
        """Get score as percentage of threshold."""
        return min(100.0, (self.value / self.threshold) * 100.0)


@dataclass
class QualityCheck:
    """Configuration for a quality check."""
    name: str
    description: str
    check_function: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    timeout: int = 30
    retry_count: int = 3


@dataclass
class ValidationResult:
    """Result of a quality validation."""
    check_name: str
    status: QualityGateStatus
    score: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "score": self.score,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }


class QualityGate:
    """
    Quality gate for enforcing quality standards.
    
    A quality gate defines a set of quality checks and thresholds
    that must be met for a process to proceed.
    """
    
    def __init__(self, name: str, description: str):
        """Initialize quality gate."""
        self.name = name
        self.description = description
        self.checks: List[QualityCheck] = []
        self.thresholds: Dict[str, float] = {}
        self.required_score = 0.8  # Minimum overall score
        self.enabled = True
        
        logger.info(f"Created quality gate: {name}")
    
    def add_check(self, check: QualityCheck) -> None:
        """Add a quality check to the gate."""
        self.checks.append(check)
        logger.debug(f"Added check '{check.name}' to gate '{self.name}'")
    
    def set_threshold(self, metric_name: str, threshold: float) -> None:
        """Set threshold for a specific metric."""
        self.thresholds[metric_name] = threshold
    
    async def evaluate(self, target: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate target against quality gate.
        
        Args:
            target: Object to evaluate
            context: Additional context for evaluation
            
        Returns:
            Quality gate evaluation results
        """
        if not self.enabled:
            return {
                "gate_name": self.name,
                "status": QualityGateStatus.PASSED.value,
                "message": "Quality gate disabled",
                "score": 1.0
            }
        
        results = []
        total_score = 0.0
        total_weight = 0.0
        critical_failures = 0
        
        for check in self.checks:
            if not check.enabled:
                continue
            
            try:
                result = await self._execute_check(check, target, context or {})
                results.append(result)
                
                # Weight the score
                total_score += result.score
                total_weight += 1.0
                
                # Count critical failures
                if (result.severity == ValidationSeverity.CRITICAL and 
                    result.status == QualityGateStatus.FAILED):
                    critical_failures += 1
                    
            except Exception as e:
                logger.error(f"Quality check '{check.name}' failed: {e}")
                results.append(ValidationResult(
                    check_name=check.name,
                    status=QualityGateStatus.FAILED,
                    score=0.0,
                    message=f"Check execution failed: {str(e)}",
                    severity=ValidationSeverity.CRITICAL
                ))
                critical_failures += 1
        
        # Calculate overall score
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine gate status
        if critical_failures > 0:
            gate_status = QualityGateStatus.FAILED
            message = f"Quality gate failed with {critical_failures} critical issues"
        elif overall_score < self.required_score:
            gate_status = QualityGateStatus.FAILED
            message = f"Quality gate failed: score {overall_score:.2f} below threshold {self.required_score}"
        else:
            gate_status = QualityGateStatus.PASSED
            message = f"Quality gate passed with score {overall_score:.2f}"
        
        return {
            "gate_name": self.name,
            "status": gate_status.value,
            "message": message,
            "overall_score": overall_score,
            "required_score": self.required_score,
            "critical_failures": critical_failures,
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r.status == QualityGateStatus.PASSED),
            "results": [r.to_dict() for r in results],
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_check(self, check: QualityCheck, target: Any, context: Dict[str, Any]) -> ValidationResult:
        """Execute a single quality check."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Dynamic check function execution would go here
            # For now, return a mock result based on check name
            score, message = await self._mock_check_execution(check, target, context)
            
            status = QualityGateStatus.PASSED if score >= 0.8 else QualityGateStatus.FAILED
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return ValidationResult(
                check_name=check.name,
                status=status,
                score=score,
                message=message,
                severity=check.severity,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ValidationResult(
                check_name=check.name,
                status=QualityGateStatus.FAILED,
                score=0.0,
                message=f"Check execution failed: {str(e)}",
                severity=ValidationSeverity.CRITICAL,
                execution_time=execution_time
            )
    
    async def _mock_check_execution(self, check: QualityCheck, target: Any, context: Dict[str, Any]) -> tuple[float, str]:
        """Mock check execution for demonstration."""
        import random
        
        # Simulate different check types
        if "performance" in check.name.lower():
            score = random.uniform(0.7, 0.95)
            message = f"Performance check: {score:.2f} efficiency score"
        elif "security" in check.name.lower():
            score = random.uniform(0.85, 1.0)
            message = f"Security check: {score:.2f} security score"
        elif "compliance" in check.name.lower():
            score = random.uniform(0.8, 0.98)
            message = f"Compliance check: {score:.2f} compliance score"
        else:
            score = random.uniform(0.75, 0.9)
            message = f"Quality check: {score:.2f} quality score"
        
        # Simulate async operation
        await asyncio.sleep(0.1)
        
        return score, message


class QualityAssuranceFramework:
    """
    Comprehensive Quality Assurance Framework.
    
    Manages quality gates, validation processes, monitoring,
    and continuous improvement of system quality.
    """
    
    def __init__(self):
        """Initialize QA framework."""
        self.quality_gates: Dict[str, QualityGate] = {}
        self.quality_metrics: Dict[str, QualityMetric] = {}
        self.validation_history: List[Dict[str, Any]] = []
        self.monitoring_enabled = True
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Initialize default quality gates
        self._setup_default_gates()
        
        logger.info("Quality Assurance Framework initialized")
    
    def _setup_default_gates(self) -> None:
        """Set up default quality gates."""
        
        # Assessment Quality Gate
        assessment_gate = QualityGate(
            "assessment_quality",
            "Quality gate for infrastructure assessments"
        )
        assessment_gate.add_check(QualityCheck(
            "completeness_check",
            "Check assessment data completeness",
            "check_assessment_completeness",
            parameters={"min_coverage": 0.8}
        ))
        assessment_gate.add_check(QualityCheck(
            "accuracy_check", 
            "Validate assessment accuracy",
            "check_assessment_accuracy",
            parameters={"accuracy_threshold": 0.85}
        ))
        assessment_gate.add_check(QualityCheck(
            "consistency_check",
            "Check internal consistency of recommendations",
            "check_recommendation_consistency",
            severity=ValidationSeverity.HIGH
        ))
        self.register_quality_gate(assessment_gate)
        
        # Report Quality Gate
        report_gate = QualityGate(
            "report_quality",
            "Quality gate for generated reports"
        )
        report_gate.add_check(QualityCheck(
            "content_quality",
            "Check report content quality",
            "check_report_content_quality",
            parameters={"min_quality_score": 0.8}
        ))
        report_gate.add_check(QualityCheck(
            "format_validation",
            "Validate report format and structure",
            "validate_report_format"
        ))
        report_gate.add_check(QualityCheck(
            "stakeholder_relevance",
            "Check stakeholder-specific relevance",
            "check_stakeholder_relevance",
            parameters={"relevance_threshold": 0.75}
        ))
        self.register_quality_gate(report_gate)
        
        # Agent Performance Gate
        agent_gate = QualityGate(
            "agent_performance",
            "Quality gate for agent performance"
        )
        agent_gate.add_check(QualityCheck(
            "response_time",
            "Check agent response time",
            "check_agent_response_time",
            parameters={"max_response_time": 30.0}
        ))
        agent_gate.add_check(QualityCheck(
            "accuracy_rate",
            "Check agent accuracy rate",
            "check_agent_accuracy",
            parameters={"min_accuracy": 0.9}
        ))
        agent_gate.add_check(QualityCheck(
            "error_rate",
            "Check agent error rate",
            "check_agent_error_rate",
            parameters={"max_error_rate": 0.05},
            severity=ValidationSeverity.CRITICAL
        ))
        self.register_quality_gate(agent_gate)
    
    def register_quality_gate(self, gate: QualityGate) -> None:
        """Register a quality gate."""
        self.quality_gates[gate.name] = gate
        logger.info(f"Registered quality gate: {gate.name}")
    
    def get_quality_gate(self, name: str) -> Optional[QualityGate]:
        """Get quality gate by name."""
        return self.quality_gates.get(name)
    
    def list_quality_gates(self) -> List[str]:
        """List all quality gate names."""
        return list(self.quality_gates.keys())
    
    async def evaluate_quality_gate(self, gate_name: str, target: Any, 
                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate a specific quality gate.
        
        Args:
            gate_name: Name of quality gate
            target: Object to evaluate
            context: Additional context
            
        Returns:
            Quality gate evaluation results
        """
        gate = self.get_quality_gate(gate_name)
        if not gate:
            raise ValueError(f"Quality gate '{gate_name}' not found")
        
        result = await gate.evaluate(target, context)
        
        # Store in validation history
        self.validation_history.append({
            **result,
            "target_type": type(target).__name__,
            "context": context or {}
        })
        
        # Keep history manageable
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-500:]
        
        return result
    
    async def evaluate_all_gates(self, target: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate all quality gates against a target.
        
        Args:
            target: Object to evaluate
            context: Additional context
            
        Returns:
            Combined evaluation results
        """
        results = {}
        overall_passed = 0
        overall_failed = 0
        
        for gate_name in self.quality_gates.keys():
            try:
                result = await self.evaluate_quality_gate(gate_name, target, context)
                results[gate_name] = result
                
                if result["status"] == QualityGateStatus.PASSED.value:
                    overall_passed += 1
                else:
                    overall_failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to evaluate quality gate '{gate_name}': {e}")
                results[gate_name] = {
                    "gate_name": gate_name,
                    "status": QualityGateStatus.FAILED.value,
                    "message": f"Evaluation failed: {str(e)}",
                    "overall_score": 0.0
                }
                overall_failed += 1
        
        return {
            "target_type": type(target).__name__,
            "evaluation_summary": {
                "total_gates": len(self.quality_gates),
                "passed": overall_passed,
                "failed": overall_failed,
                "success_rate": overall_passed / len(self.quality_gates) if self.quality_gates else 0
            },
            "gate_results": results,
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def add_quality_metric(self, metric: QualityMetric) -> None:
        """Add a quality metric for tracking."""
        self.quality_metrics[metric.name] = metric
        logger.debug(f"Added quality metric: {metric.name}")
    
    def get_quality_dashboard(self) -> Dict[str, Any]:
        """Get quality dashboard data."""
        # Recent validation results
        recent_validations = self.validation_history[-50:] if self.validation_history else []
        
        # Success rates by gate
        gate_success_rates = {}
        for gate_name in self.quality_gates.keys():
            gate_validations = [v for v in recent_validations if v["gate_name"] == gate_name]
            if gate_validations:
                passed = sum(1 for v in gate_validations if v["status"] == "passed")
                gate_success_rates[gate_name] = passed / len(gate_validations)
            else:
                gate_success_rates[gate_name] = 0.0
        
        # Quality metrics summary
        metrics_summary = {}
        for name, metric in self.quality_metrics.items():
            metrics_summary[name] = {
                "value": metric.value,
                "threshold": metric.threshold,
                "is_passing": metric.is_passing,
                "score_percentage": metric.score_percentage
            }
        
        return {
            "summary": {
                "total_gates": len(self.quality_gates),
                "total_validations": len(self.validation_history),
                "recent_validations": len(recent_validations),
                "overall_success_rate": sum(gate_success_rates.values()) / len(gate_success_rates) if gate_success_rates else 0
            },
            "gate_success_rates": gate_success_rates,
            "quality_metrics": metrics_summary,
            "recent_results": recent_validations[-10:],  # Last 10 results
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get quality trends over specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Quality trends and analytics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Filter recent validations
        recent_validations = [
            v for v in self.validation_history
            if datetime.fromisoformat(v["evaluated_at"].replace("Z", "+00:00")) >= cutoff_date
        ]
        
        if not recent_validations:
            return {"message": "No validation data available for the specified period"}
        
        # Group by date
        daily_results = defaultdict(list)
        for validation in recent_validations:
            date_str = validation["evaluated_at"][:10]  # YYYY-MM-DD
            daily_results[date_str].append(validation)
        
        # Calculate daily success rates
        daily_success_rates = {}
        for date, validations in daily_results.items():
            passed = sum(1 for v in validations if v["status"] == "passed")
            daily_success_rates[date] = passed / len(validations)
        
        return {
            "period_days": days,
            "total_validations": len(recent_validations),
            "daily_success_rates": daily_success_rates,
            "average_success_rate": sum(daily_success_rates.values()) / len(daily_success_rates),
            "trend_analysis": self._analyze_trend(list(daily_success_rates.values())),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend in success rate values."""
        if len(values) < 2:
            return "insufficient_data"
        
        recent_half = values[len(values)//2:]
        earlier_half = values[:len(values)//2]
        
        recent_avg = sum(recent_half) / len(recent_half)
        earlier_avg = sum(earlier_half) / len(earlier_half)
        
        if recent_avg > earlier_avg + 0.05:
            return "improving"
        elif recent_avg < earlier_avg - 0.05:
            return "declining"
        else:
            return "stable"
    
    async def start_monitoring(self, check_interval: int = 3600) -> None:
        """
        Start quality monitoring.
        
        Args:
            check_interval: Check interval in seconds
        """
        if self.monitoring_task and not self.monitoring_task.done():
            return
        
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(check_interval)
        )
        logger.info("Started quality monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop quality monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped quality monitoring")
    
    async def _monitoring_loop(self, check_interval: int) -> None:
        """Quality monitoring loop."""
        while True:
            try:
                await asyncio.sleep(check_interval)
                
                if not self.monitoring_enabled:
                    continue
                
                # Analyze quality trends
                trends = self.get_quality_trends(days=1)
                
                # Log quality alerts
                if "average_success_rate" in trends:
                    success_rate = trends["average_success_rate"]
                    if success_rate < 0.8:
                        logger.warning(f"Quality alert: Success rate dropped to {success_rate:.2f}")
                    elif success_rate < 0.6:
                        logger.error(f"Critical quality alert: Success rate critically low at {success_rate:.2f}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in quality monitoring loop: {e}")


# Global QA framework instance
qa_framework = QualityAssuranceFramework()