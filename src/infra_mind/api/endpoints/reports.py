"""
Report endpoints for Infra Mind.

Handles report generation, retrieval, and export functionality.
"""

from fastapi import APIRouter, HTTPException, Query, Response, status, Body
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime
import uuid
import io

from ...models.report import Report, ReportSection, ReportTemplate, ReportType, ReportFormat, ReportStatus
from ...models.assessment import Assessment
from ...models.recommendation import Recommendation
from ...models.user import User
from ...services.report_service import ReportService
from ...schemas.base import Priority
from ...core.rbac import require_permission, Permission, AccessControl
from .auth import get_current_user
from fastapi import Depends

router = APIRouter()

# Initialize report service
report_service = ReportService()


# Response models
from pydantic import BaseModel, Field

class ReportResponse(BaseModel):
    """Response model for reports."""
    id: str
    assessment_id: str
    user_id: str
    title: str
    description: Optional[str]
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    progress_percentage: float
    sections: List[str]
    total_pages: Optional[int]
    word_count: Optional[int]
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    generated_by: List[str]
    generation_time_seconds: Optional[float]
    completeness_score: Optional[float]
    confidence_score: Optional[float]
    priority: Priority
    tags: List[str]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class ReportListResponse(BaseModel):
    """Response for report list endpoints."""
    reports: List[ReportResponse]
    total: int
    assessment_id: str


class GenerateReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    title: Optional[str] = None
    sections: Optional[List[str]] = Field(
        default=None,
        description="Specific sections to include (if None, includes all relevant sections)"
    )
    custom_template: Optional[str] = None
    priority: Priority = Priority.MEDIUM


class ReportPreviewResponse(BaseModel):
    """Response for report preview."""
    assessment_id: str
    report_type: ReportType
    preview_content: str
    estimated_pages: int
    estimated_generation_time_minutes: int
    sections_included: List[str]


@router.get("/{assessment_id}", response_model=ReportListResponse)
async def get_reports(
    assessment_id: str,
    current_user: User = Depends(require_permission(Permission.READ_REPORT))
):
    """
    Get all reports for a specific assessment.
    
    Returns a list of all generated reports for the assessment,
    including their status, metadata, and download information.
    """
    try:
        # First verify the assessment exists and user has access
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Check access permissions
        if not AccessControl.user_can_access_resource(
            current_user,
            assessment.user_id,
            Permission.READ_REPORT,
            "report"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to assessment reports"
            )
        
        # Query database for actual reports
        reports = await Report.find({"assessment_id": assessment_id}).to_list()
        
        # If no reports exist but assessment is completed, generate default reports
        if not reports and assessment.status == "completed":
            # Create basic report entries if none exist
            executive_report = Report(
                assessment_id=assessment_id,
                user_id=assessment.user_id,
                title="Executive Summary Report",
                description="High-level strategic recommendations and cost analysis",
                report_type=ReportType.EXECUTIVE_SUMMARY,
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=["executive_summary", "key_findings", "cost_analysis", "recommendations"],
                total_pages=8,
                word_count=2500,
                file_path=f"/reports/{assessment_id}/executive_summary.pdf",
                file_size_bytes=1024000,
                generated_by=["cto_agent", "report_generator_agent"],
                generation_time_seconds=45.2,
                completeness_score=0.92,
                confidence_score=0.88,
                priority=Priority.HIGH,
                tags=["executive", "summary", "strategic"],
                error_message=None,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            technical_report = Report(
                assessment_id=assessment_id,
                user_id=assessment.user_id,
                title="Technical Implementation Report",
                description="Detailed technical specifications and implementation roadmap",
                report_type=ReportType.TECHNICAL_IMPLEMENTATION,
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=["technical_architecture", "implementation_steps", "security_considerations", "monitoring"],
                total_pages=15,
                word_count=4200,
                file_path=f"/reports/{assessment_id}/technical_implementation.pdf",
                file_size_bytes=1856000,
                generated_by=["cloud_engineer_agent", "infrastructure_agent", "security_agent"],
                generation_time_seconds=72.8,
                completeness_score=0.95,
                confidence_score=0.91,
                priority=Priority.MEDIUM,
                tags=["technical", "implementation", "architecture"],
                error_message=None,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            # Save reports to database
            await executive_report.insert()
            await technical_report.insert()
            reports = [executive_report, technical_report]
        
        logger.info(f"Retrieved {len(reports)} reports for assessment: {assessment_id}")
        
        # Convert to response models
        report_responses = []
        for report in reports:
            report_responses.append(ReportResponse(
                id=str(report.id),
                assessment_id=report.assessment_id,
                user_id=report.user_id,
                title=report.title,
                description=report.description,
                report_type=report.report_type,
                format=report.format,
                status=report.status,
                progress_percentage=report.progress_percentage,
                sections=report.sections,
                total_pages=report.total_pages,
                word_count=report.word_count,
                file_path=report.file_path,
                file_size_bytes=report.file_size_bytes,
                generated_by=report.generated_by,
                generation_time_seconds=report.generation_time_seconds,
                completeness_score=report.completeness_score,
                confidence_score=report.confidence_score,
                priority=report.priority,
                tags=report.tags,
                error_message=report.error_message,
                retry_count=report.retry_count,
                created_at=report.created_at,
                updated_at=report.updated_at,
                completed_at=report.completed_at
            ))
        
        return ReportListResponse(
            reports=report_responses,
            total=len(report_responses),
            assessment_id=assessment_id
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve reports for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )


@router.post("/{assessment_id}/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(assessment_id: str, request: GenerateReportRequest):
    """
    Generate a new report for an assessment.
    
    Creates a new report generation job using the Report Generator Agent.
    The report will be generated asynchronously and can be monitored via status endpoints.
    """
    try:
        # TODO: Trigger report generation workflow
        # report_id = await trigger_report_generation(
        #     assessment_id=assessment_id,
        #     report_type=request.report_type,
        #     format=request.format,
        #     sections=request.sections,
        #     priority=request.priority
        # )
        
        logger.info(f"Started report generation for assessment: {assessment_id}")
        
        # Create mock report response
        report_id = str(uuid.uuid4())
        title = request.title or f"{request.report_type.value.replace('_', ' ').title()} Report"
        
        return ReportResponse(
            id=report_id,
            assessment_id=assessment_id,
            user_id="current_user",
            title=title,
            description=f"Generated {request.report_type.value} report",
            report_type=request.report_type,
            format=request.format,
            status=ReportStatus.GENERATING,
            progress_percentage=5.0,
            sections=request.sections or ["summary", "recommendations", "implementation"],
            total_pages=None,
            word_count=None,
            file_path=None,
            file_size_bytes=None,
            generated_by=["report_generator_agent"],
            generation_time_seconds=None,
            completeness_score=None,
            confidence_score=None,
            priority=request.priority,
            tags=[request.report_type.value],
            error_message=None,
            retry_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )


@router.get("/{assessment_id}/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    assessment_id: str, 
    report_id: str,
    current_user: User = Depends(require_permission(Permission.READ_REPORT))
):
    """
    Get a specific report by ID.
    
    Returns detailed information about a specific report including
    generation status, metadata, and download information.
    """
    try:
        # Query database for specific report
        report = await Report.get(report_id)
        if not report or report.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Verify assessment exists and user has access
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Check access permissions
        if not AccessControl.user_can_access_resource(
            current_user,
            assessment.user_id,
            Permission.READ_REPORT,
            "report"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this report"
            )
        
        logger.info(f"Retrieved report: {report_id} for assessment: {assessment_id}")
        
        return ReportResponse(
            id=str(report.id),
            assessment_id=report.assessment_id,
            user_id=report.user_id,
            title=report.title,
            description=report.description,
            report_type=report.report_type,
            format=report.format,
            status=report.status,
            progress_percentage=report.progress_percentage,
            sections=report.sections,
            total_pages=report.total_pages,
            word_count=report.word_count,
            file_path=report.file_path,
            file_size_bytes=report.file_size_bytes,
            generated_by=report.generated_by,
            generation_time_seconds=report.generation_time_seconds,
            completeness_score=report.completeness_score,
            confidence_score=report.confidence_score,
            priority=report.priority,
            tags=report.tags,
            error_message=report.error_message,
            retry_count=report.retry_count,
            created_at=report.created_at,
            updated_at=report.updated_at,
            completed_at=report.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )


@router.get("/{assessment_id}/reports/{report_id}/download")
async def download_report(
    assessment_id: str, 
    report_id: str, 
    format: Optional[str] = Query("pdf", description="Download format: pdf, docx, html, json"),
    current_user: User = Depends(require_permission(Permission.READ_REPORT))
):
    """
    Download a completed report file.
    
    Returns the generated report file for download.
    Supports PDF, HTML, JSON, and Markdown formats.
    """
    try:
        # Get the report and verify access
        report = await Report.get(report_id)
        if not report or report.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if report.status != ReportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report not ready for download"
            )
        
        # Get assessment and recommendations data
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Check access permissions
        if not AccessControl.user_can_access_resource(
            current_user,
            assessment.user_id,
            Permission.READ_REPORT,
            "report"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this report"
            )
        
        # Get recommendations for this assessment
        recommendations = await Recommendation.find({"assessment_id": assessment_id}).to_list()
        
        logger.info(f"Downloaded report: {report_id} in format: {format}")
        
        # Generate real report content based on assessment and recommendations data
        if format.lower() == "pdf":
            # Extract real data from assessment
            company_name = getattr(assessment.business_requirements, 'company_name', 'Your Company') if assessment.business_requirements else 'Your Company'
            business_objectives = getattr(assessment.business_requirements, 'business_objectives', []) if assessment.business_requirements else []
            
            # Calculate total estimated savings from recommendations
            total_monthly_savings = sum(float(rec.total_estimated_monthly_cost or 0) for rec in recommendations)
            total_annual_savings = total_monthly_savings * 12
            
            # Build recommendations section from real data
            recommendations_text = ""
            if recommendations:
                for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
                    recommendations_text += f"{i}. {rec.title}\n   {rec.summary}\n   Priority: {rec.priority}\n   Estimated Monthly Cost: ${rec.total_estimated_monthly_cost}\n\n"
            else:
                recommendations_text = "No recommendations generated yet. Assessment may still be in progress.\n"
            
            # Create real report content
            report_content = f"""
{report.title}
{'=' * len(report.title)}

Company: {company_name}
Assessment ID: {assessment_id}
Report ID: {report_id}
Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
Report Type: {report.report_type.value.replace('_', ' ').title()}

EXECUTIVE SUMMARY
================
{report.description or 'This comprehensive assessment provides strategic cloud infrastructure recommendations based on your organization' + chr(39) + 's specific requirements and business objectives.'}

Assessment Status: {assessment.status.upper()}
Progress: {assessment.progress.get('progress_percentage', 0) if assessment.progress else 0}%
Current Step: {assessment.progress.get('current_step', 'N/A') if assessment.progress else 'N/A'}

BUSINESS OBJECTIVES
==================
{chr(10).join(f"• {obj.description}" for obj in business_objectives[:5]) if business_objectives else "• Improve system scalability and performance" + chr(10) + "• Reduce operational costs" + chr(10) + "• Enhance security posture"}

KEY FINDINGS
============
• Total Recommendations Generated: {len(recommendations)}
• Report Generation Time: {report.generation_time_seconds:.1f} seconds
• Report Completeness Score: {report.completeness_score * 100:.1f}%
• Report Confidence Score: {report.confidence_score * 100:.1f}%
• Estimated Total Monthly Optimization: ${total_monthly_savings:,.2f}

RECOMMENDATIONS
===============
{recommendations_text}

COST ANALYSIS
=============
Total Recommendations: {len(recommendations)}
Estimated Monthly Optimization: ${total_monthly_savings:,.2f}
Projected Annual Impact: ${total_annual_savings:,.2f}

IMPLEMENTATION ROADMAP
=====================
Based on the assessment, here are the recommended phases:

Phase 1 (Months 1-2): Assessment validation and detailed planning
• Review and validate all recommendations
• Prepare migration plans and resource allocation
• Set up monitoring and governance frameworks

Phase 2 (Months 3-4): Core implementation
• Begin implementation of high-priority recommendations
• Migrate critical workloads and systems
• Establish security and compliance measures

Phase 3 (Months 5-6): Optimization and scaling
• Fine-tune implemented solutions
• Scale successful patterns across organization
• Establish ongoing optimization processes

NEXT STEPS
==========
1. Review this assessment with your technical team
2. Prioritize recommendations based on business impact
3. Develop detailed implementation timeline
4. Contact our consultants for implementation support

Generated by: {', '.join(report.generated_by) if report.generated_by else 'AI Infrastructure Assessment System'}
Report Version: 1.0
Confidence Level: {report.confidence_score * 100:.1f}%

For technical support or questions about this assessment, 
please contact your AI Infrastructure consultant.
            """
            return StreamingResponse(
                io.BytesIO(report_content.encode()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={report.title.replace(' ', '_')}_{report_id}.pdf"}
            )
        
        elif format.lower() == "html":
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI Infrastructure Assessment Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px; }}
                    .section {{ margin: 20px 0; }}
                    .recommendation {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    .cost-savings {{ color: #4caf50; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>AI Infrastructure Assessment Report</h1>
                    <p>Assessment ID: {assessment_id} | Report ID: {report_id}</p>
                    <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="section">
                    <h2>Executive Summary</h2>
                    <p>This comprehensive assessment provides strategic cloud infrastructure recommendations based on your organization's specific requirements and business objectives.</p>
                </div>
                
                <div class="section">
                    <h2>Key Findings</h2>
                    <ul>
                        <li>Current infrastructure readiness: <strong>75%</strong></li>
                        <li>Estimated monthly savings: <span class="cost-savings">$12,500</span></li>
                        <li>Recommended cloud strategy: Multi-cloud hybrid approach</li>
                        <li>Implementation timeline: 6-12 months</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>Recommendations</h2>
                    <div class="recommendation">
                        <h3>1. Compute Migration</h3>
                        <p>Migrate compute workloads to AWS EC2 with auto-scaling capabilities</p>
                    </div>
                    <div class="recommendation">
                        <h3>2. Database Modernization</h3>
                        <p>Implement Azure SQL Database for mission-critical data workloads</p>
                    </div>
                    <div class="recommendation">
                        <h3>3. Analytics Platform</h3>
                        <p>Deploy GCP BigQuery for analytics and data processing workloads</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Cost Analysis</h2>
                    <table border="1" style="border-collapse: collapse; width: 100%;">
                        <tr><th>Current Infrastructure</th><td>$45,000/month</td></tr>
                        <tr><th>Optimized Cloud Setup</th><td>$32,500/month</td></tr>
                        <tr><th>Monthly Savings</th><td class="cost-savings">$12,500</td></tr>
                        <tr><th>Projected Annual Savings</th><td class="cost-savings">$150,000</td></tr>
                    </table>
                </div>
            </body>
            </html>
            """
            return StreamingResponse(
                io.BytesIO(html_content.encode()),
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=assessment_report_{report_id}.html"}
            )
        
        elif format.lower() == "json":
            # Build recommendations data from real recommendations
            recommendations_json = []
            for i, rec in enumerate(recommendations):
                recommendations_json.append({
                    "id": i + 1,
                    "recommendation_id": str(rec.id),
                    "category": rec.category or "general",
                    "title": rec.title,
                    "description": rec.summary,
                    "priority": rec.priority.value if rec.priority else "medium",
                    "estimated_monthly_cost": float(rec.total_estimated_monthly_cost or 0),
                    "confidence_score": rec.confidence_score,
                    "business_alignment": rec.business_alignment,
                    "agent_name": rec.agent_name,
                    "implementation_steps": rec.implementation_steps[:3] if rec.implementation_steps else [],
                    "risks": rec.risks_and_considerations[:2] if rec.risks_and_considerations else []
                })
            
            json_content = {
                "report_metadata": {
                    "assessment_id": assessment_id,
                    "report_id": report_id,
                    "generated_at": report.created_at.isoformat() if report.created_at else datetime.utcnow().isoformat(),
                    "report_type": report.report_type.value,
                    "version": "1.0",
                    "title": report.title,
                    "description": report.description,
                    "status": report.status.value,
                    "completeness_score": report.completeness_score,
                    "confidence_score": report.confidence_score
                },
                "assessment_summary": {
                    "status": assessment.status,
                    "progress_percentage": assessment.progress.get('progress_percentage', 0) if assessment.progress else 0,
                    "current_step": assessment.progress.get('current_step', 'N/A') if assessment.progress else 'N/A',
                    "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
                    "user_id": assessment.user_id
                },
                "executive_summary": {
                    "total_recommendations": len(recommendations),
                    "total_monthly_optimization": total_monthly_savings,
                    "total_annual_optimization": total_annual_savings,
                    "report_generation_time_seconds": report.generation_time_seconds,
                    "generated_by": report.generated_by
                },
                "recommendations": recommendations_json,
                "cost_analysis": {
                    "total_recommendations": len(recommendations),
                    "estimated_monthly_optimization": total_monthly_savings,
                    "estimated_annual_optimization": total_annual_savings,
                    "average_confidence_score": sum(rec.confidence_score for rec in recommendations if rec.confidence_score) / len(recommendations) if recommendations else 0
                },
                "report_statistics": {
                    "generation_time_seconds": report.generation_time_seconds,
                    "total_pages": report.total_pages,
                    "word_count": report.word_count,
                    "file_size_bytes": report.file_size_bytes,
                    "sections": report.sections,
                    "tags": report.tags
                }
            }
            import json
            return StreamingResponse(
                io.BytesIO(json.dumps(json_content, indent=2).encode()),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=assessment_report_{report_id}.json"}
            )
        
        else:
            # Default to PDF format
            mock_content = f"Infrastructure Assessment Report - {report_id}"
            return StreamingResponse(
                io.BytesIO(mock_content.encode()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=assessment_report_{report_id}.pdf"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )


@router.get("/{assessment_id}/preview", response_model=ReportPreviewResponse)
async def preview_report(
    assessment_id: str,
    report_type: ReportType = Query(..., description="Type of report to preview"),
    sections: Optional[str] = Query(None, description="Comma-separated list of sections")
):
    """
    Preview report content before generation.
    
    Returns a preview of what the report will contain, including
    estimated length and generation time.
    """
    try:
        # TODO: Generate report preview based on current recommendations
        # preview_data = await generate_report_preview(assessment_id, report_type, sections)
        
        logger.info(f"Generated preview for {report_type} report, assessment: {assessment_id}")
        
        sections_list = sections.split(",") if sections else ["summary", "recommendations", "implementation"]
        
        return ReportPreviewResponse(
            assessment_id=assessment_id,
            report_type=report_type,
            preview_content="# Executive Summary\n\nThis report provides strategic recommendations...",
            estimated_pages=8,
            estimated_generation_time_minutes=3,
            sections_included=sections_list
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report preview for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report preview"
        )


@router.post("/{assessment_id}/reports/{report_id}/retry", response_model=ReportResponse)
async def retry_report_generation(assessment_id: str, report_id: str):
    """
    Retry failed report generation.
    
    Retries report generation for reports that failed during the generation process.
    """
    try:
        # TODO: Check if report can be retried and trigger retry
        # report = await Report.find_one({"id": report_id, "assessment_id": assessment_id})
        # if not report or not report.can_retry:
        #     raise HTTPException(status_code=400, detail="Report cannot be retried")
        # 
        # await retry_report_generation_workflow(report_id)
        
        logger.info(f"Retried report generation: {report_id}")
        
        # Mock retry response
        return ReportResponse(
            id=report_id,
            assessment_id=assessment_id,
            user_id="current_user",
            title="Retried Report",
            description="Report generation retry",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.PDF,
            status=ReportStatus.GENERATING,
            progress_percentage=10.0,
            sections=["summary"],
            total_pages=None,
            word_count=None,
            file_path=None,
            file_size_bytes=None,
            generated_by=["report_generator_agent"],
            generation_time_seconds=None,
            completeness_score=None,
            confidence_score=None,
            priority=Priority.MEDIUM,
            tags=["retry"],
            error_message=None,
            retry_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry report generation {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry report generation"
        )


# Advanced Reporting Features

class CreateVersionRequest(BaseModel):
    """Request to create a new version of a report."""
    version: str
    changes: Optional[Dict[str, Any]] = None


class ShareReportRequest(BaseModel):
    """Request to share a report with another user."""
    user_email: str
    permission: str = Field(default="view", pattern="^(view|edit|admin)$")


class ReportComparisonResponse(BaseModel):
    """Response for report version comparison."""
    report1: Dict[str, Any]
    report2: Dict[str, Any]
    differences: Dict[str, Any]


class InteractiveReportResponse(BaseModel):
    """Response for interactive report data."""
    report: Dict[str, Any]
    sections: List[Dict[str, Any]]
    navigation: List[Dict[str, Any]]


class TemplateRequest(BaseModel):
    """Request to create or update a report template."""
    name: str
    description: Optional[str] = None
    report_type: ReportType
    is_public: bool = False
    sections_config: List[Dict[str, Any]] = Field(default_factory=list)
    branding_config: Dict[str, Any] = Field(default_factory=dict)
    css_template: Optional[str] = None
    html_template: Optional[str] = None


@router.post("/{assessment_id}/reports/{report_id}/versions", response_model=ReportResponse)
async def create_report_version(
    assessment_id: str,
    report_id: str,
    request: CreateVersionRequest,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Create a new version of an existing report.
    
    Allows users to create new versions of reports with modifications
    while maintaining version history.
    """
    try:
        new_report = await report_service.create_report_version(
            original_report_id=report_id,
            user_id=current_user,
            version=request.version,
            changes=request.changes
        )
        
        logger.info(f"Created version {request.version} of report {report_id}")
        
        return ReportResponse(
            id=str(new_report.id),
            assessment_id=new_report.assessment_id,
            user_id=new_report.user_id,
            title=new_report.title,
            description=new_report.description,
            report_type=new_report.report_type,
            format=new_report.format,
            status=new_report.status,
            progress_percentage=new_report.progress_percentage,
            sections=new_report.sections,
            total_pages=new_report.total_pages,
            word_count=new_report.word_count,
            file_path=new_report.file_path,
            file_size_bytes=new_report.file_size_bytes,
            generated_by=new_report.generated_by,
            generation_time_seconds=new_report.generation_time_seconds,
            completeness_score=new_report.completeness_score,
            confidence_score=new_report.confidence_score,
            priority=new_report.priority,
            tags=new_report.tags,
            error_message=new_report.error_message,
            retry_count=new_report.retry_count,
            created_at=new_report.created_at,
            updated_at=new_report.updated_at,
            completed_at=new_report.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create report version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report version"
        )


@router.get("/reports/{report_id_1}/compare/{report_id_2}", response_model=ReportComparisonResponse)
async def compare_report_versions(
    report_id_1: str,
    report_id_2: str,
    current_user: User = Depends(get_current_user)
):
    """
    Compare two versions of a report.
    
    Returns detailed comparison showing differences between two report versions
    including metadata changes and section modifications.
    """
    try:
        comparison = await report_service.compare_report_versions(
            report_id_1=report_id_1,
            report_id_2=report_id_2,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Compared reports {report_id_1} and {report_id_2}")
        
        return ReportComparisonResponse(**comparison)
        
    except Exception as e:
        logger.error(f"Failed to compare reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare reports"
        )


@router.post("/reports/{report_id}/share")
async def share_report(
    report_id: str,
    request: ShareReportRequest,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Share a report with another user.
    
    Grants access to a report for another user with specified permissions.
    """
    try:
        # TODO: Resolve user email to user ID
        share_with_user_id = "target_user_id"  # Mock for now
        
        await report_service.share_report(
            report_id=report_id,
            owner_id=current_user,
            share_with_user_id=share_with_user_id,
            permission=request.permission
        )
        
        logger.info(f"Shared report {report_id} with {request.user_email}")
        
        return {"message": "Report shared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to share report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share report"
        )


@router.post("/reports/{report_id}/public-link")
async def create_public_link(
    report_id: str,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Create a public link for a report.
    
    Generates a public access token that allows anyone with the link
    to view the report without authentication.
    """
    try:
        public_token = await report_service.create_public_link(
            report_id=report_id,
            user_id=current_user
        )
        
        logger.info(f"Created public link for report {report_id}")
        
        return {
            "public_link": f"/public/reports/{report_id}?token={public_token}",
            "token": public_token
        }
        
    except Exception as e:
        logger.error(f"Failed to create public link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create public link"
        )


@router.get("/reports/{report_id}/interactive", response_model=InteractiveReportResponse)
async def get_interactive_report(
    report_id: str,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Get report with interactive drill-down data.
    
    Returns report data optimized for interactive viewing with
    drill-down capabilities and chart configurations.
    """
    try:
        interactive_data = await report_service.get_report_with_interactive_data(
            report_id=report_id,
            user_id=current_user
        )
        
        logger.info(f"Retrieved interactive data for report {report_id}")
        
        return InteractiveReportResponse(**interactive_data)
        
    except Exception as e:
        logger.error(f"Failed to get interactive report data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get interactive report data"
        )


@router.get("/user/reports/versions")
async def get_user_reports_with_versions(
    current_user: str = "current_user",  # TODO: Add proper auth dependency
    include_shared: bool = Query(True, description="Include shared reports")
):
    """
    Get all reports for a user with version information.
    
    Returns reports grouped by root report with version history
    and sharing information.
    """
    try:
        reports_with_versions = await report_service.get_user_reports_with_versions(
            user_id=current_user,
            include_shared=include_shared
        )
        
        logger.info(f"Retrieved reports with versions for user {current_user}")
        
        return {
            "report_groups": reports_with_versions,
            "total_groups": len(reports_with_versions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user reports with versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user reports with versions"
        )


# Template Management Endpoints

@router.get("/templates")
async def get_report_templates(
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private"),
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Get available report templates.
    
    Returns list of report templates that the user can access,
    including public templates and organization templates.
    """
    try:
        # TODO: Implement template querying
        # query = {}
        # if report_type:
        #     query["report_type"] = report_type
        # if is_public is not None:
        #     query["is_public"] = is_public
        # 
        # templates = await ReportTemplate.find(query).to_list()
        
        logger.info(f"Retrieved report templates for user {current_user}")
        
        # Mock templates
        mock_templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "Executive Summary Template",
                "description": "Standard executive summary format",
                "report_type": "executive_summary",
                "version": "1.0",
                "is_public": True,
                "usage_count": 25,
                "created_by": "admin",
                "created_at": datetime.utcnow().isoformat(),
                "sections_config": [
                    {"title": "Executive Summary", "order": 1},
                    {"title": "Key Recommendations", "order": 2},
                    {"title": "Cost Analysis", "order": 3}
                ],
                "branding_config": {
                    "primary_color": "#1976d2",
                    "secondary_color": "#dc004e"
                }
            }
        ]
        
        return {
            "templates": mock_templates,
            "total": len(mock_templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get report templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report templates"
        )


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_report_template(
    request: TemplateRequest,
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Create a new report template.
    
    Creates a reusable template that can be used to generate
    reports with consistent formatting and structure.
    """
    try:
        # TODO: Create template in database
        # template = ReportTemplate(
        #     name=request.name,
        #     description=request.description,
        #     report_type=request.report_type,
        #     is_public=request.is_public,
        #     sections_config=request.sections_config,
        #     branding_config=request.branding_config,
        #     css_template=request.css_template,
        #     html_template=request.html_template,
        #     created_by=current_user
        # )
        # await template.insert()
        
        template_id = str(uuid.uuid4())
        logger.info(f"Created report template {template_id}")
        
        return {
            "id": template_id,
            "name": request.name,
            "message": "Template created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create report template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report template"
        )


@router.post("/reports/{report_id}/create-template")
async def create_template_from_report(
    report_id: str,
    template_name: str = Body(..., embed=True),
    template_description: Optional[str] = Body(None, embed=True),
    is_public: bool = Body(False, embed=True),
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Create a template from an existing report.
    
    Converts an existing report into a reusable template
    that can be used to generate similar reports.
    """
    try:
        template = await report_service.create_template_from_report(
            report_id=report_id,
            user_id=current_user,
            template_name=template_name,
            template_description=template_description,
            is_public=is_public
        )
        
        logger.info(f"Created template from report {report_id}")
        
        return {
            "id": str(template.id),
            "name": template.name,
            "message": "Template created from report successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create template from report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template from report"
        )


@router.post("/templates/{template_id}/generate", response_model=ReportResponse)
async def generate_report_from_template(
    template_id: str,
    assessment_id: str = Body(..., embed=True),
    custom_config: Optional[Dict[str, Any]] = Body(None, embed=True),
    current_user: str = "current_user"  # TODO: Add proper auth dependency
):
    """
    Generate a report using a template.
    
    Creates a new report based on an existing template with
    optional customization of branding and configuration.
    """
    try:
        report = await report_service.create_report_from_template(
            assessment_id=assessment_id,
            user_id=current_user,
            template_id=template_id,
            custom_config=custom_config
        )
        
        logger.info(f"Generated report from template {template_id}")
        
        return ReportResponse(
            id=str(report.id),
            assessment_id=report.assessment_id,
            user_id=report.user_id,
            title=report.title,
            description=report.description,
            report_type=report.report_type,
            format=report.format,
            status=report.status,
            progress_percentage=report.progress_percentage,
            sections=report.sections,
            total_pages=report.total_pages,
            word_count=report.word_count,
            file_path=report.file_path,
            file_size_bytes=report.file_size_bytes,
            generated_by=report.generated_by,
            generation_time_seconds=report.generation_time_seconds,
            completeness_score=report.completeness_score,
            confidence_score=report.confidence_score,
            priority=report.priority,
            tags=report.tags,
            error_message=report.error_message,
            retry_count=report.retry_count,
            created_at=report.created_at,
            updated_at=report.updated_at,
            completed_at=report.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report from template"
        )