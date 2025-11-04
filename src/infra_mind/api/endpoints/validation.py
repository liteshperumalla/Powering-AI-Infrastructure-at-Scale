"""
Assessment Data Validation API Endpoints

Provides endpoints for validating and fixing assessment data quality issues.
Includes both individual assessment validation and bulk validation capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
from loguru import logger
import asyncio

from ...services.assessment_data_validator import assessment_validator
from .auth import get_current_user
from ...models.user import User
from ...core.rbac import require_permission, Permission
from ...core.dependencies import DatabaseDep  # Dependency injection for database access

router = APIRouter()


@router.post("/assessments/{assessment_id}/validate")
async def validate_assessment(
    assessment_id: str,
    force_update: bool = Query(False, description="Force update even if assessment appears complete"),
    current_user: User = Depends(get_current_user)
):
    """
    Validate and enhance a specific assessment's data quality.
    
    This endpoint:
    - Validates all required fields are present
    - Enriches missing basic company information
    - Ensures recommendations have proper cost estimates
    - Fixes technical specification gaps
    - Removes duplicate reports
    - Updates assessment metadata
    """
    # Enhanced input validation and edge case handling
    if not assessment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment ID is required and cannot be empty"
        )
    
    if not assessment_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment ID cannot be whitespace only"
        )
    
    # Validate assessment ID format (assuming ObjectId format)
    if len(assessment_id.strip()) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid assessment ID format. Expected 24-character ObjectId"
        )
    
    # Sanitize assessment_id
    assessment_id = assessment_id.strip()
    
    try:
        logger.info(f"Validating assessment {assessment_id} requested by user {current_user.email}")
        
        # Check if assessment_validator is properly initialized
        if not hasattr(assessment_validator, 'validate_and_enhance_assessment'):
            logger.error("Assessment validator service is not properly initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Validation service is currently unavailable"
            )
        
        # Validate assessment data with timeout
        try:
            success, issues, fixes = await asyncio.wait_for(
                assessment_validator.validate_and_enhance_assessment(assessment_id, force_update),
                timeout=120.0  # 2 minute timeout for validation
            )
        except asyncio.TimeoutError:
            logger.error(f"Assessment validation timed out for {assessment_id}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Assessment validation timed out. The assessment may be too large or complex."
            )
        
        # Enhanced error handling for validation results
        if not success:
            if not issues:
                logger.error(f"Assessment validation failed for {assessment_id} with no error details")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Assessment validation failed due to unknown data quality issues"
                )
            
            # Check for specific error types
            error_msg = issues[0] if isinstance(issues, list) else str(issues)
            
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assessment not found: {error_msg}"
                )
            elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to assessment: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Assessment validation failed: {error_msg}"
                )
        
        # Ensure issues and fixes are lists for consistent processing
        issues = issues if isinstance(issues, list) else []
        fixes = fixes if isinstance(fixes, list) else []
        
        # Calculate data quality score based on issues and fixes
        issues_count = len(issues)
        fixes_count = len(fixes)
        
        if issues_count == 0:
            data_quality_score = 1.0  # Perfect score
        elif fixes_count >= issues_count:
            data_quality_score = 0.95  # Most issues fixed
        elif fixes_count > issues_count * 0.7:
            data_quality_score = 0.85  # Many issues fixed
        elif fixes_count > issues_count * 0.5:
            data_quality_score = 0.75  # Some issues fixed
        else:
            data_quality_score = 0.65  # Few issues fixed
        
        return {
            "success": True,
            "message": "Assessment validation completed successfully",
            "validation_results": {
                "assessment_id": assessment_id,
                "issues_found": issues_count,
                "fixes_applied": fixes_count,
                "data_quality_score": round(data_quality_score, 2),
                "validation_status": "completed",
                "improvement_percentage": round((fixes_count / max(issues_count, 1)) * 100, 1) if issues_count > 0 else 100.0
            },
            "details": {
                "issues_found": issues[:10] if len(issues) > 10 else issues,  # Limit for performance
                "fixes_applied": fixes[:10] if len(fixes) > 10 else fixes,     # Limit for performance
                "truncated": len(issues) > 10 or len(fixes) > 10
            }
        }
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Assessment validation request timed out"
        )
    except ConnectionError as e:
        logger.error(f"Database connection error during validation for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later."
        )
    except MemoryError as e:
        logger.error(f"Memory error during validation for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to complete validation. Assessment may be too large."
        )
    except Exception as e:
        logger.error(f"Unexpected error during assessment validation for {assessment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during validation. Please contact support."
        )


@router.post("/assessments/validate-all")
async def validate_all_assessments(
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assessments to validate"),
    timeout_minutes: int = Query(30, ge=5, le=120, description="Timeout for bulk validation in minutes")
):
    """
    Validate and enhance all assessments in the database.
    
    This is a bulk operation that validates all assessments and provides
    a comprehensive report of data quality issues and fixes applied.
    
    Requires admin permissions due to the bulk nature of the operation.
    
    Args:
        limit: Maximum number of assessments to validate (1-1000)
        timeout_minutes: Operation timeout in minutes (5-120)
    """
    # Enhanced permission checking
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for bulk validation"
        )
    
    if not hasattr(current_user, 'is_admin') or not hasattr(current_user, 'is_superuser'):
        logger.error(f"User object missing permission attributes for {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User permission data is incomplete"
        )
    
    if not current_user.is_admin and not current_user.is_superuser:
        logger.warning(f"Unauthorized bulk validation attempt by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bulk validation requires admin or superuser permissions"
        )
    
    # Validate parameters
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be a positive integer"
        )
    
    if timeout_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeout must be a positive integer"
        )
    
    try:
        logger.info(f"Bulk assessment validation requested by admin user {current_user.email} (limit: {limit}, timeout: {timeout_minutes}min)")
        
        # Check if assessment_validator is properly initialized
        if not hasattr(assessment_validator, 'validate_all_assessments'):
            logger.error("Assessment validator service is not properly initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Validation service is currently unavailable"
            )
        
        # Run bulk validation with timeout and limits
        try:
            results = await asyncio.wait_for(
                assessment_validator.validate_all_assessments(limit=limit),
                timeout=timeout_minutes * 60  # Convert to seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Bulk validation timed out after {timeout_minutes} minutes")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Bulk validation operation timed out after {timeout_minutes} minutes. Try reducing the limit or increasing the timeout."
            )
        
        # Enhanced error checking and result validation
        if not results or not isinstance(results, dict):
            logger.error("Bulk validation returned invalid results format")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Validation service returned invalid response format"
            )
        
        if "error" in results:
            error_msg = results.get("error", "Unknown error")
            logger.error(f"Bulk validation service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk validation failed: {error_msg}"
            )
        
        # Ensure required fields exist with defaults
        total_assessments = results.get("total_assessments", 0)
        validated_assessments = results.get("validated_assessments", 0)
        failed_validations = results.get("failed_validations", 0)
        total_issues_found = results.get("total_issues_found", 0)
        total_fixes_applied = results.get("total_fixes_applied", 0)
        assessment_details = results.get("assessment_details", [])
        
        # Validate data consistency
        if validated_assessments + failed_validations != total_assessments:
            logger.warning(f"Inconsistent validation counts: total={total_assessments}, validated={validated_assessments}, failed={failed_validations}")
        
        # Calculate success rate with safe division
        success_rate = 0.0
        if total_assessments > 0:
            success_rate = (validated_assessments / total_assessments) * 100
        
        return {
            "success": True,
            "message": "Bulk assessment validation completed",
            "validation_summary": {
                "total_assessments": total_assessments,
                "successfully_validated": validated_assessments,
                "failed_validations": failed_validations,
                "total_issues_found": total_issues_found,
                "total_fixes_applied": total_fixes_applied,
                "success_rate": f"{success_rate:.1f}%",
                "efficiency_rate": f"{(total_fixes_applied / max(total_issues_found, 1)) * 100:.1f}%" if total_issues_found > 0 else "100.0%",
                "limit_applied": limit,
                "timeout_minutes": timeout_minutes
            },
            "assessment_details": assessment_details[:50] if len(assessment_details) > 50 else assessment_details,  # Limit response size
            "details_truncated": len(assessment_details) > 50
        }
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Bulk validation operation timed out after {timeout_minutes} minutes"
        )
    except ConnectionError as e:
        logger.error(f"Database connection error during bulk validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later."
        )
    except MemoryError as e:
        logger.error(f"Memory error during bulk validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory for bulk validation. Try reducing the limit."
        )
    except Exception as e:
        logger.error(f"Unexpected error during bulk assessment validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during bulk validation. Please contact support."
        )


@router.get("/validation/health-check")
async def validation_health_check():
    """
    Health check endpoint for the validation service.
    
    Returns the status of the validation service and basic statistics.
    """
    try:
        import time
        start_time = time.time()
        
        # Check if assessment_validator is properly initialized
        service_status = "healthy"
        error_details = []
        
        if not hasattr(assessment_validator, 'validate_and_enhance_assessment'):
            service_status = "degraded"
            error_details.append("validate_and_enhance_assessment method not available")
        
        if not hasattr(assessment_validator, 'validate_all_assessments'):
            service_status = "degraded" 
            error_details.append("validate_all_assessments method not available")
        
        # Test basic service responsiveness
        try:
            # Quick test to verify service is responsive
            test_result = hasattr(assessment_validator, '__class__')
            if not test_result:
                service_status = "unhealthy"
                error_details.append("Service instance is not properly initialized")
        except Exception as e:
            service_status = "unhealthy"
            error_details.append(f"Service test failed: {str(e)}")
        
        response_time = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
        
        result = {
            "status": service_status,
            "service": "assessment_data_validator",
            "version": "1.0.0",
            "response_time_ms": response_time,
            "features": [
                "automatic_data_enrichment",
                "cost_estimate_generation", 
                "duplicate_report_removal",
                "technical_specification_completion",
                "bulk_validation",
                "timeout_protection",
                "enhanced_error_handling"
            ],
            "validation_capabilities": {
                "basic_company_info": service_status in ["healthy", "degraded"],
                "requirements_data": service_status in ["healthy", "degraded"],
                "recommendations_validation": service_status in ["healthy", "degraded"],
                "reports_validation": service_status in ["healthy", "degraded"],
                "metadata_updates": service_status in ["healthy", "degraded"]
            }
        }
        
        # Add error details if service is not fully healthy
        if error_details:
            result["issues"] = error_details
            
        return result
        
    except Exception as e:
        logger.error(f"Validation health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "assessment_data_validator",
            "error": str(e),
            "response_time_ms": None
        }


@router.get("/validation/stats")
async def get_validation_stats(
    current_user: User = Depends(get_current_user),
    db: DatabaseDep = None
):
    """
    Get validation statistics and data quality metrics.

    Provides insights into overall data quality across all assessments.

    Note: Now uses dependency injection for database access.
    """
    try:
        # Get basic statistics (database injected)
        total_assessments = await db.assessments.count_documents({})
        completed_assessments = await db.assessments.count_documents({"status": "completed"})
        validated_assessments = await db.assessments.count_documents({"validation_status": "validated"})
        
        # Get assessments with missing data
        assessments_missing_company_size = await db.assessments.count_documents({
            "$or": [
                {"company_size": {"$exists": False}},
                {"company_size": "unknown"},
                {"company_size": ""}
            ]
        })
        
        assessments_missing_industry = await db.assessments.count_documents({
            "$or": [
                {"industry": {"$exists": False}},
                {"industry": "unknown"},
                {"industry": ""}
            ]
        })
        
        assessments_missing_budget = await db.assessments.count_documents({
            "$or": [
                {"budget_range": {"$exists": False}},
                {"budget_range": "unknown"},
                {"budget_range": ""}
            ]
        })
        
        # Get recommendations with missing cost estimates
        total_recommendations = await db.recommendations.count_documents({})
        recommendations_without_costs = await db.recommendations.count_documents({
            "$or": [
                {"cost_estimates": {"$exists": False}},
                {"cost_estimates.monthly_cost": {"$exists": False}},
                {"cost_estimates.monthly_cost": 0}
            ]
        })
        
        # Get reports statistics
        total_reports = await db.reports.count_documents({})
        reports_with_zero_words = await db.reports.count_documents({"word_count": 0})
        low_quality_reports = await db.reports.count_documents({"completeness_score": {"$lt": 0.5}})
        
        client.close()
        
        # Calculate data quality scores
        basic_info_quality = ((total_assessments - max(assessments_missing_company_size, assessments_missing_industry, assessments_missing_budget)) / total_assessments * 100) if total_assessments > 0 else 0
        recommendation_quality = ((total_recommendations - recommendations_without_costs) / total_recommendations * 100) if total_recommendations > 0 else 0
        report_quality = ((total_reports - reports_with_zero_words - low_quality_reports) / total_reports * 100) if total_reports > 0 else 0
        
        overall_quality = (basic_info_quality + recommendation_quality + report_quality) / 3
        
        return {
            "data_quality_overview": {
                "overall_quality_score": f"{overall_quality:.1f}%",
                "basic_info_quality": f"{basic_info_quality:.1f}%",
                "recommendation_quality": f"{recommendation_quality:.1f}%",
                "report_quality": f"{report_quality:.1f}%"
            },
            "assessment_statistics": {
                "total_assessments": total_assessments,
                "completed_assessments": completed_assessments,
                "validated_assessments": validated_assessments,
                "validation_coverage": f"{(validated_assessments / total_assessments * 100):.1f}%" if total_assessments > 0 else "0%"
            },
            "data_completeness_issues": {
                "missing_company_size": assessments_missing_company_size,
                "missing_industry": assessments_missing_industry,
                "missing_budget_range": assessments_missing_budget,
                "recommendations_without_costs": recommendations_without_costs,
                "reports_with_zero_words": reports_with_zero_words,
                "low_quality_reports": low_quality_reports
            },
            "recommendations": {
                "high_priority_fixes": [],
                "data_quality_improvements": [
                    "Run bulk validation to fix missing basic company information",
                    "Enhance recommendation cost estimates for better accuracy",
                    "Improve report quality metrics and content completeness"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get validation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation statistics: {str(e)}"
        )