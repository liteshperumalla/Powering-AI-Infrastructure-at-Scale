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
from ...services.report_service import ReportService
from ...schemas.base import Priority

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
async def get_reports(assessment_id: str):
    """
    Get all reports for a specific assessment.
    
    Returns a list of all generated reports for the assessment,
    including their status, metadata, and download information.
    """
    try:
        # TODO: Query database for reports
        # reports = await Report.find({"assessment_id": assessment_id}).to_list()
        
        logger.info(f"Retrieved reports for assessment: {assessment_id}")
        
        # Mock reports for now
        mock_reports = [
            ReportResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                user_id="current_user",
                title="Executive Summary Report",
                description="High-level strategic recommendations for executives",
                report_type=ReportType.EXECUTIVE_SUMMARY,
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=["executive_summary", "key_recommendations", "cost_analysis"],
                total_pages=8,
                word_count=2500,
                file_path="/reports/exec_summary_123.pdf",
                file_size_bytes=1024000,
                generated_by=["cto_agent", "report_generator_agent"],
                generation_time_seconds=45.2,
                completeness_score=0.95,
                confidence_score=0.88,
                priority=Priority.HIGH,
                tags=["executive", "summary", "strategic"],
                error_message=None,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            ),
            ReportResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                user_id="current_user",
                title="Technical Implementation Roadmap",
                description="Detailed technical implementation guide",
                report_type=ReportType.TECHNICAL_ROADMAP,
                format=ReportFormat.PDF,
                status=ReportStatus.GENERATING,
                progress_percentage=65.0,
                sections=["architecture", "implementation_steps", "timeline"],
                total_pages=None,
                word_count=None,
                file_path=None,
                file_size_bytes=None,
                generated_by=["cloud_engineer_agent", "report_generator_agent"],
                generation_time_seconds=None,
                completeness_score=None,
                confidence_score=None,
                priority=Priority.MEDIUM,
                tags=["technical", "roadmap", "implementation"],
                error_message=None,
                retry_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=None
            )
        ]
        
        return ReportListResponse(
            reports=mock_reports,
            total=len(mock_reports),
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
async def get_report(assessment_id: str, report_id: str):
    """
    Get a specific report by ID.
    
    Returns detailed information about a specific report including
    generation status, metadata, and download information.
    """
    try:
        # TODO: Query database for specific report
        # report = await Report.find_one({"id": report_id, "assessment_id": assessment_id})
        # if not report:
        #     raise HTTPException(status_code=404, detail="Report not found")
        
        logger.info(f"Retrieved report: {report_id} for assessment: {assessment_id}")
        
        # Mock report response
        return ReportResponse(
            id=report_id,
            assessment_id=assessment_id,
            user_id="current_user",
            title="Executive Summary Report",
            description="High-level strategic recommendations",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
            progress_percentage=100.0,
            sections=["executive_summary", "recommendations", "cost_analysis"],
            total_pages=12,
            word_count=3500,
            file_path=f"/reports/{report_id}.pdf",
            file_size_bytes=1536000,
            generated_by=["cto_agent", "report_generator_agent"],
            generation_time_seconds=67.8,
            completeness_score=0.92,
            confidence_score=0.85,
            priority=Priority.HIGH,
            tags=["executive", "summary"],
            error_message=None,
            retry_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
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
async def download_report(assessment_id: str, report_id: str):
    """
    Download a completed report file.
    
    Returns the generated report file for download.
    Supports PDF, HTML, JSON, and Markdown formats.
    """
    try:
        # TODO: Check if report exists and is completed
        # report = await Report.find_one({"id": report_id, "assessment_id": assessment_id})
        # if not report:
        #     raise HTTPException(status_code=404, detail="Report not found")
        # if report.status != ReportStatus.COMPLETED:
        #     raise HTTPException(status_code=400, detail="Report not ready for download")
        # 
        # return FileResponse(
        #     path=report.file_path,
        #     filename=f"report_{report_id}.{report.format.value}",
        #     media_type=get_media_type(report.format)
        # )
        
        logger.info(f"Downloaded report: {report_id}")
        
        # Mock file download
        mock_content = f"Mock report content for {report_id}"
        return StreamingResponse(
            io.BytesIO(mock_content.encode()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
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
    current_user: str = "current_user"  # TODO: Add proper auth dependency
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
            user_id=current_user
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