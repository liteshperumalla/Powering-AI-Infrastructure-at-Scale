"""
Production Data Validation Service.

Ensures that no mock or placeholder data is saved to production database.
Validates data quality and completeness for reports and recommendations.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from ..models.report import Report, ReportSection
from ..models.recommendation import Recommendation
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    quality_score: float  # 0-100

class ProductionDataValidator:
    """
    Validates data to prevent mock/placeholder content in production.
    
    Ensures all reports, recommendations, and assessments contain
    real, meaningful data before saving to database.
    """
    
    # Patterns that indicate mock/placeholder data
    MOCK_PATTERNS = [
        r"mock|placeholder|test|debug|sample|dummy|fake|lorem ipsum",
        r"TODO|FIXME|TBD|coming soon|under development",
        r"report generation in progress|being generated",
        r"unknown company|example|template|prototype",
        r"\$\d+,?\d*\.?\d*\s*(placeholder|mock|test)",
        r"(0+|1234|9999)\s*(cost|price|budget)"
    ]
    
    # Minimum content requirements
    MIN_DESCRIPTION_LENGTH = 50
    MIN_RECOMMENDATION_COUNT = 3
    MIN_SECTION_CONTENT_LENGTH = 100
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.MOCK_PATTERNS]
    
    def validate_report(self, report: Report) -> ValidationResult:
        """
        Validate a report for production readiness.
        
        Args:
            report: Report to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        quality_score = 100.0
        
        try:
            # Check title
            if self._contains_mock_content(report.title):
                errors.append(f"Report title contains mock/placeholder content: {report.title}")
                quality_score -= 20
            
            # Check description
            if self._contains_mock_content(report.description):
                errors.append(f"Report description contains mock content: {report.description}")
                quality_score -= 15
            
            # Validate sections
            if not report.sections or len(report.sections) == 0:
                errors.append("Report has no sections")
                quality_score -= 30
            else:
                section_issues = self._validate_sections(report.sections)
                errors.extend(section_issues["errors"])
                warnings.extend(section_issues["warnings"])
                quality_score -= section_issues["quality_penalty"]
            
            # Check recommendations
            if not report.recommendations or len(report.recommendations) == 0:
                errors.append("Report has no recommendations")
                quality_score -= 25
            elif len(report.recommendations) < self.MIN_RECOMMENDATION_COUNT:
                warnings.append(f"Report has only {len(report.recommendations)} recommendations (minimum: {self.MIN_RECOMMENDATION_COUNT})")
                quality_score -= 10
            
            # Validate recommendations content
            if report.recommendations:
                rec_issues = self._validate_recommendations_content(report.recommendations)
                errors.extend(rec_issues["errors"])
                warnings.extend(rec_issues["warnings"])
                quality_score -= rec_issues["quality_penalty"]
            
            # Check cost analysis
            if hasattr(report, 'cost_analysis') and report.cost_analysis:
                cost_issues = self._validate_cost_analysis(report.cost_analysis)
                errors.extend(cost_issues["errors"])
                warnings.extend(cost_issues["warnings"])
                quality_score -= cost_issues["quality_penalty"]
            else:
                warnings.append("Report missing cost analysis")
                quality_score -= 10
            
            # Check generated_by field
            if not report.generated_by or "mock" in str(report.generated_by).lower():
                errors.append("Report has invalid generated_by field")
                quality_score -= 15
            
            # Ensure quality_score doesn't go below 0
            quality_score = max(0.0, quality_score)
            
            is_valid = len(errors) == 0 and quality_score >= 70.0
            
            if not is_valid:
                logger.warning(f"Report {report.id} failed validation: {len(errors)} errors, quality score: {quality_score}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Error validating report {report.id}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                quality_score=0.0
            )
    
    def validate_recommendation(self, recommendation: Recommendation) -> ValidationResult:
        """
        Validate a recommendation for production readiness.
        
        Args:
            recommendation: Recommendation to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        quality_score = 100.0
        
        try:
            # Check title
            if self._contains_mock_content(recommendation.title):
                errors.append(f"Recommendation title contains mock content: {recommendation.title}")
                quality_score -= 25
            
            # Check description
            if not recommendation.description or len(recommendation.description) < self.MIN_DESCRIPTION_LENGTH:
                errors.append(f"Recommendation description too short or missing (minimum: {self.MIN_DESCRIPTION_LENGTH} chars)")
                quality_score -= 30
            elif self._contains_mock_content(recommendation.description):
                errors.append(f"Recommendation description contains mock content")
                quality_score -= 20
            
            # Check cost
            if recommendation.estimated_cost == 0:
                warnings.append("Recommendation has no estimated cost")
                quality_score -= 10
            elif recommendation.estimated_cost in [1234, 9999, 75000]:  # Common mock values
                errors.append(f"Recommendation has mock cost value: ${recommendation.estimated_cost}")
                quality_score -= 15
            
            # Check implementation time
            if not recommendation.implementation_time or recommendation.implementation_time in ["TBD", "TODO", "Unknown"]:
                warnings.append("Recommendation missing implementation time")
                quality_score -= 10
            
            # Check agent name
            if not recommendation.agent_name or "mock" in recommendation.agent_name.lower():
                errors.append("Recommendation has invalid agent_name")
                quality_score -= 15
            
            # Ensure quality_score doesn't go below 0
            quality_score = max(0.0, quality_score)
            
            is_valid = len(errors) == 0 and quality_score >= 60.0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Error validating recommendation {recommendation.id}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                quality_score=0.0
            )
    
    def _contains_mock_content(self, text: str) -> bool:
        """Check if text contains mock/placeholder patterns."""
        if not text:
            return False
        
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _validate_sections(self, sections: List[ReportSection]) -> Dict[str, Any]:
        """Validate report sections."""
        errors = []
        warnings = []
        quality_penalty = 0.0
        
        for section in sections:
            if self._contains_mock_content(section.title):
                errors.append(f"Section title contains mock content: {section.title}")
                quality_penalty += 10
            
            if not section.content or len(section.content) < self.MIN_SECTION_CONTENT_LENGTH:
                errors.append(f"Section '{section.title}' content too short or missing")
                quality_penalty += 15
            elif self._contains_mock_content(section.content):
                errors.append(f"Section '{section.title}' contains mock content")
                quality_penalty += 10
        
        return {
            "errors": errors,
            "warnings": warnings,
            "quality_penalty": quality_penalty
        }
    
    def _validate_recommendations_content(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate recommendations content."""
        errors = []
        warnings = []
        quality_penalty = 0.0
        
        for i, rec in enumerate(recommendations):
            if self._contains_mock_content(rec.get("title", "")):
                errors.append(f"Recommendation {i+1} title contains mock content")
                quality_penalty += 8
            
            if self._contains_mock_content(rec.get("description", "")):
                errors.append(f"Recommendation {i+1} description contains mock content")
                quality_penalty += 8
            
            cost = rec.get("estimated_cost", 0)
            if cost in [75000, 1234, 9999, 0]:
                errors.append(f"Recommendation {i+1} has mock cost value: ${cost}")
                quality_penalty += 5
        
        return {
            "errors": errors,
            "warnings": warnings,
            "quality_penalty": quality_penalty
        }
    
    def _validate_cost_analysis(self, cost_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cost analysis data."""
        errors = []
        warnings = []
        quality_penalty = 0.0
        
        total_cost = cost_analysis.get("total_cost", 0)
        if total_cost in [75000, 1234, 9999, 0]:
            errors.append(f"Cost analysis has mock total_cost value: ${total_cost}")
            quality_penalty += 15
        
        # Check for mock savings values
        savings = cost_analysis.get("projected_savings", 0)
        if savings in [75000, 25000, 1234, 9999]:
            errors.append(f"Cost analysis has mock savings value: ${savings}")
            quality_penalty += 10
        
        return {
            "errors": errors,
            "warnings": warnings,
            "quality_penalty": quality_penalty
        }


# Global validator instance
production_validator = ProductionDataValidator(strict_mode=True)


async def validate_before_save(data: Union[Report, Recommendation]) -> ValidationResult:
    """
    Validate data before saving to database.
    
    This function should be called before any Report or Recommendation
    is saved to prevent mock data from entering production.
    
    Args:
        data: Report or Recommendation to validate
        
    Returns:
        ValidationResult with validation status
    """
    if isinstance(data, Report):
        result = production_validator.validate_report(data)
    elif isinstance(data, Recommendation):
        result = production_validator.validate_recommendation(data)
    else:
        logger.error(f"Unknown data type for validation: {type(data)}")
        return ValidationResult(
            is_valid=False,
            errors=[f"Unknown data type: {type(data)}"],
            warnings=[],
            quality_score=0.0
        )
    
    if not result.is_valid:
        logger.error(f"Data validation failed for {type(data).__name__} {getattr(data, 'id', 'unknown')}")
        logger.error(f"Errors: {result.errors}")
        logger.warning(f"Warnings: {result.warnings}")
        logger.info(f"Quality score: {result.quality_score}")
    
    return result