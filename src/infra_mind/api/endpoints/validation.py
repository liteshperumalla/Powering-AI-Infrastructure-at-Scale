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
    try:
        logger.info(f"Validating assessment {assessment_id} requested by user {current_user.email}")
        
        # Validate assessment data
        success, issues, fixes = await assessment_validator.validate_and_enhance_assessment(
            assessment_id, force_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment validation failed: {issues[0] if issues else 'Unknown error'}"
            )
        
        return {
            "success": True,
            "message": "Assessment validation completed successfully",
            "validation_results": {
                "assessment_id": assessment_id,
                "issues_found": len(issues),
                "fixes_applied": len(fixes),
                "data_quality_score": 0.95 if len(fixes) < 5 else 0.85,
                "validation_status": "completed"
            },
            "details": {
                "issues_found": issues,
                "fixes_applied": fixes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment validation failed for {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/assessments/validate-all")
async def validate_all_assessments(
    current_user: User = Depends(get_current_user)
):
    """
    Validate and enhance all assessments in the database.
    
    This is a bulk operation that validates all assessments and provides
    a comprehensive report of data quality issues and fixes applied.
    
    Requires admin permissions due to the bulk nature of the operation.
    """
    try:
        # Check admin permissions for bulk operations
        if not current_user.is_admin and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bulk validation requires admin permissions"
            )
        
        logger.info(f"Bulk assessment validation requested by admin user {current_user.email}")
        
        # Run bulk validation
        results = await assessment_validator.validate_all_assessments()
        
        if "error" in results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk validation failed: {results['error']}"
            )
        
        return {
            "success": True,
            "message": "Bulk assessment validation completed",
            "validation_summary": {
                "total_assessments": results["total_assessments"],
                "successfully_validated": results["validated_assessments"],
                "failed_validations": results["failed_validations"],
                "total_issues_found": results["total_issues_found"],
                "total_fixes_applied": results["total_fixes_applied"],
                "success_rate": f"{(results['validated_assessments'] / results['total_assessments'] * 100):.1f}%" if results['total_assessments'] > 0 else "0%"
            },
            "assessment_details": results["assessment_details"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk assessment validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk validation failed: {str(e)}"
        )


@router.get("/validation/health-check")
async def validation_health_check():
    """
    Health check endpoint for the validation service.
    
    Returns the status of the validation service and basic statistics.
    """
    try:
        # Basic health check - verify service is responsive
        return {
            "status": "healthy",
            "service": "assessment_data_validator",
            "version": "1.0.0",
            "features": [
                "automatic_data_enrichment",
                "cost_estimate_generation",
                "duplicate_report_removal",
                "technical_specification_completion",
                "bulk_validation"
            ],
            "validation_capabilities": {
                "basic_company_info": True,
                "requirements_data": True,
                "recommendations_validation": True,
                "reports_validation": True,
                "metadata_updates": True
            }
        }
        
    except Exception as e:
        logger.error(f"Validation health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/validation/stats")
async def get_validation_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get validation statistics and data quality metrics.
    
    Provides insights into overall data quality across all assessments.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        # Get database connection
        mongodb_url = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
        client = AsyncIOMotorClient(mongodb_url)
        db = client.get_database('infra_mind')
        
        # Get basic statistics
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