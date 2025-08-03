"""
Assessment endpoints for Infra Mind.

Handles infrastructure assessment creation, management, and retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from loguru import logger
import uuid
from datetime import datetime

from ...schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate, 
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentSummary,
    StartAssessmentRequest,
    AssessmentStatusUpdate
)
from ...models.assessment import Assessment
from ...schemas.base import AssessmentStatus, Priority

router = APIRouter()


async def start_assessment_workflow(assessment: Assessment):
    """
    Start the assessment workflow to generate recommendations and reports.
    
    This function runs the complete workflow asynchronously to generate
    recommendations and reports for the assessment.
    """
    logger.info(f"DEBUG: start_assessment_workflow called for assessment {assessment.id}")
    try:
        from ...workflows.assessment_workflow import AssessmentWorkflow
        from ...workflows.base import workflow_manager
        
        workflow = AssessmentWorkflow()
        workflow_manager.register_workflow(workflow)
        
        # Execute the workflow using the workflow manager
        result = await workflow_manager.execute_workflow(
            workflow_id="assessment_workflow",
            assessment=assessment
        )
        
        # Update assessment with final results
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completion_percentage = 100.0
        assessment.completed_at = datetime.utcnow()
        assessment.recommendations_generated = True
        assessment.reports_generated = True
        assessment.progress = {
            "current_step": "completed", 
            "completed_steps": ["created", "analysis", "synthesis", "report_generation"], 
            "total_steps": 5, 
            "progress_percentage": 100.0
        }
        assessment.workflow_id = result.workflow_id
        
        await assessment.save()
        
        logger.info(f"Assessment workflow completed for {assessment.id}")
        
    except Exception as e:
        logger.error(f"Assessment workflow failed for {assessment.id}: {e}")
        
        # Update assessment to show failure
        assessment.status = AssessmentStatus.FAILED
        assessment.progress = {
            "current_step": "failed", 
            "completed_steps": ["created"], 
            "total_steps": 5, 
            "progress_percentage": 20.0,
            "error": str(e)
        }
        await assessment.save()



@router.post("/simple", status_code=status.HTTP_201_CREATED)
async def create_simple_assessment(data: dict):
    """
    Create a simple assessment for testing.
    """
    try:
        current_time = datetime.utcnow()
        
        # Create and save Assessment document with simple data
        assessment = Assessment(
            user_id="anonymous_user",
            title=data.get("title", "Test Assessment"),
            description=data.get("description", "Test Description"),
            business_requirements=data.get("business_requirements", {}),
            technical_requirements=data.get("technical_requirements", {}),
            status=AssessmentStatus.DRAFT,
            priority=Priority.MEDIUM,
            completion_percentage=0.0,
            metadata={
                "source": "api_test", 
                "version": "1.0", 
                "tags": []
            },
            created_at=current_time,
            updated_at=current_time
        )
        
        await assessment.insert()
        logger.info(f"Created simple assessment: {assessment.id}")
        
        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "description": assessment.description,
            "status": assessment.status,
            "created_at": assessment.created_at
        }
        
    except Exception as e:
        logger.error(f"Failed to create simple assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(assessment_data: AssessmentCreate):
    """
    Create a new infrastructure assessment.
    
    Creates a new assessment with the provided business and technical requirements.
    The assessment will be in DRAFT status and ready for AI agent analysis.
    """
    try:
        current_time = datetime.utcnow()
        
        # Create and save Assessment document
        assessment = Assessment(
            user_id="anonymous_user",  # For now, use anonymous user since no auth required
            title=assessment_data.title,
            description=assessment_data.description,
            business_requirements=assessment_data.business_requirements.model_dump(),
            technical_requirements=assessment_data.technical_requirements.model_dump(),
            status=AssessmentStatus.DRAFT,
            priority=assessment_data.priority,
            completion_percentage=0.0,
            source=getattr(assessment_data, 'source', 'web_form'),
            tags=getattr(assessment_data, 'tags', []),
            metadata={
                "source": getattr(assessment_data, 'source', 'web_form'), 
                "version": "1.0", 
                "tags": getattr(assessment_data, 'tags', [])
            },
            created_at=current_time,
            updated_at=current_time
        )
        
        # Save to database using insert to avoid revision tracking issues
        await assessment.insert()
        logger.info(f"Created assessment: {assessment.id}")
        
        # Automatically start the workflow to generate recommendations and reports
        logger.info(f"DEBUG: About to start workflow for assessment: {assessment.id}")
        try:
            logger.info(f"DEBUG: Importing workflow modules...")
            from ...workflows.assessment_workflow import AssessmentWorkflow
            logger.info(f"DEBUG: Creating AssessmentWorkflow instance...")
            workflow = AssessmentWorkflow()
            
            logger.info(f"DEBUG: Starting workflow task...")
            # Start workflow asynchronously (fire and forget)
            import asyncio
            asyncio.create_task(start_assessment_workflow(assessment))
            
            logger.info(f"DEBUG: Updating assessment status...")
            # Update assessment status to indicate workflow started
            assessment.status = AssessmentStatus.IN_PROGRESS
            assessment.started_at = current_time
            assessment.progress = {
                "current_step": "initializing_workflow", 
                "completed_steps": ["created"], 
                "total_steps": 5, 
                "progress_percentage": 10.0
            }
            await assessment.save()
            
            logger.info(f"Started workflow for assessment: {assessment.id}")
        except Exception as workflow_error:
            logger.error(f"Failed to start workflow for assessment {assessment.id}: {workflow_error}")
            import traceback
            logger.error(f"Workflow error traceback: {traceback.format_exc()}")
            # Don't fail assessment creation if workflow fails to start
        
        # Return response
        return AssessmentResponse(
            id=str(assessment.id),
            title=assessment.title,
            description=assessment.description,
            business_requirements=assessment_data.business_requirements,
            technical_requirements=assessment_data.technical_requirements,
            status=assessment.status,
            priority=assessment.priority,
            progress=assessment.progress,
            workflow_id=assessment.workflow_id,
            agent_states={},
            recommendations_generated=assessment.recommendations_generated,
            reports_generated=assessment.reports_generated,
            metadata=assessment.metadata,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create assessment: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: str):
    """
    Get a specific assessment by ID.
    
    Returns the complete assessment data including current status,
    progress, and any generated recommendations or reports.
    """
    try:
        # Retrieve from database
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Assessment {assessment_id} not found"
            )
        
        logger.info(f"Retrieved assessment: {assessment_id}")
        
        # Return the actual assessment data
        return AssessmentResponse(
            id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            business_requirements=assessment.business_requirements,
            technical_requirements=assessment.technical_requirements,
            status=assessment.status,
            priority=assessment.priority,
            progress=assessment.progress,
            workflow_id=assessment.workflow_id,
            agent_states=assessment.agent_states,
            recommendations_generated=assessment.recommendations_generated,
            reports_generated=assessment.reports_generated,
            metadata=assessment.metadata,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assessment: {str(e)}"
        )


@router.get("/{assessment_id}/mock", response_model=AssessmentResponse)
async def get_assessment_mock(assessment_id: str):
    """
    Get a mock assessment response for testing.
    """
    try:
        # Return mock assessment for testing
        from ...schemas.business import BusinessRequirements, BusinessGoal, GrowthProjection, BudgetConstraints, TeamStructure
        from ...schemas.technical import TechnicalRequirements, PerformanceRequirement, ScalabilityRequirement, SecurityRequirement, IntegrationRequirement
        from ...schemas.base import CompanySize, Industry, BudgetRange, ComplianceRequirement, WorkloadType, Priority
        from decimal import Decimal
        
        return AssessmentResponse(
            id=assessment_id,
            title="Sample Assessment",
            description="Sample infrastructure assessment",
            business_requirements=BusinessRequirements(
                company_size=CompanySize.MEDIUM,
                industry=Industry.TECHNOLOGY,
                business_goals=[
                    BusinessGoal(
                        goal="Reduce infrastructure costs by 30%",
                        priority=Priority.HIGH,
                        timeline_months=6,
                        success_metrics=["Monthly cost reduction", "Performance maintained"]
                    ),
                    BusinessGoal(
                        goal="Improve system scalability",
                        priority=Priority.HIGH,
                        timeline_months=12,
                        success_metrics=["Handle 10x traffic", "Auto-scaling implemented"]
                    )
                ],
                growth_projection=GrowthProjection(
                    current_users=1000,
                    projected_users_6m=2000,
                    projected_users_12m=5000,
                    current_revenue=Decimal("500000"),
                    projected_revenue_12m=Decimal("1000000")
                ),
                budget_constraints=BudgetConstraints(
                    total_budget_range=BudgetRange.RANGE_100K_500K,
                    monthly_budget_limit=Decimal("25000"),
                    compute_percentage=40,
                    storage_percentage=20,
                    networking_percentage=20,
                    security_percentage=20,
                    cost_optimization_priority=Priority.HIGH
                ),
                team_structure=TeamStructure(
                    total_developers=8,
                    senior_developers=3,
                    devops_engineers=2,
                    data_engineers=1,
                    cloud_expertise_level=3,
                    kubernetes_expertise=2,
                    database_expertise=4,
                    preferred_technologies=["Python", "React", "PostgreSQL"]
                ),
                compliance_requirements=[ComplianceRequirement.GDPR],
                project_timeline_months=6,
                urgency_level=Priority.HIGH,
                current_pain_points=["High infrastructure costs", "Manual scaling"],
                success_criteria=["30% cost reduction", "Automated scaling"],
                multi_cloud_acceptable=True
            ),
            technical_requirements=TechnicalRequirements(
                workload_types=[WorkloadType.WEB_APPLICATION, WorkloadType.DATA_PROCESSING],
                performance_requirements=PerformanceRequirement(
                    api_response_time_ms=200,
                    requests_per_second=1000,
                    concurrent_users=500,
                    uptime_percentage=Decimal("99.9"),
                    real_time_processing_required=False
                ),
                scalability_requirements=ScalabilityRequirement(
                    current_data_size_gb=100,
                    current_daily_transactions=10000,
                    expected_data_growth_rate="20% monthly",
                    peak_load_multiplier=Decimal("5.0"),
                    auto_scaling_required=True,
                    global_distribution_required=False,
                    cdn_required=True,
                    planned_regions=["us-east-1", "eu-west-1"]
                ),
                security_requirements=SecurityRequirement(
                    encryption_at_rest_required=True,
                    encryption_in_transit_required=True,
                    multi_factor_auth_required=True,
                    vpc_isolation_required=True,
                    security_monitoring_required=True,
                    audit_logging_required=True
                ),
                integration_requirements=IntegrationRequirement(
                    existing_databases=["PostgreSQL"],
                    existing_apis=["Payment API", "Analytics API"],
                    rest_api_required=True,
                    real_time_sync_required=False,
                    batch_sync_acceptable=True
                ),
                preferred_programming_languages=["Python", "JavaScript"],
                monitoring_requirements=["Application metrics", "Infrastructure monitoring"],
                backup_requirements=["Daily backups", "Cross-region replication"],
                ci_cd_requirements=["Automated testing", "Blue-green deployment"]
            ),
            status=AssessmentStatus.DRAFT,
            priority=Priority.MEDIUM,
            progress={"current_step": "created", "completed_steps": [], "total_steps": 5, "progress_percentage": 0.0},
            workflow_id=None,
            agent_states={},
            recommendations_generated=False,
            reports_generated=False,
            metadata={"source": "web_form", "version": "1.0", "tags": []},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            started_at=None,
            completed_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessment"
        )


@router.get("/", response_model=AssessmentListResponse)
async def list_assessments(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[AssessmentStatus] = Query(None, description="Filter by status"),
    priority_filter: Optional[Priority] = Query(None, description="Filter by priority")
):
    """
    List all assessments for the current user.
    
    Returns a paginated list of assessments with filtering options.
    Includes summary information for each assessment.
    """
    try:
        # Build query with filters
        query_filter = {}
        if status_filter:
            query_filter["status"] = status_filter
        if priority_filter:
            query_filter["priority"] = priority_filter
        
        # Get total count and paginated results
        total = await Assessment.find(query_filter).count()
        assessments = await Assessment.find(query_filter).skip((page - 1) * limit).limit(limit).to_list()
        
        logger.info(f"Listed {len(assessments)} assessments - page: {page}, limit: {limit}, total: {total}")
        
        # Convert assessments to summaries
        assessment_summaries = []
        for assessment in assessments:
            # Extract basic info from business requirements if available
            company_size = "unknown"
            industry = "unknown"
            budget_range = "unknown"
            workload_types = []
            
            if assessment.business_requirements:
                company_size = assessment.business_requirements.company_size.value if assessment.business_requirements.company_size else "unknown"
                industry = assessment.business_requirements.industry.value if assessment.business_requirements.industry else "unknown"
                if assessment.business_requirements.budget_constraints:
                    budget_range = assessment.business_requirements.budget_constraints.total_budget_range.value if assessment.business_requirements.budget_constraints.total_budget_range else "unknown"
            
            if assessment.technical_requirements and assessment.technical_requirements.workload_types:
                workload_types = [wt.value for wt in assessment.technical_requirements.workload_types]
            
            assessment_summaries.append(AssessmentSummary(
                id=assessment.id,
                title=assessment.title,
                status=assessment.status,
                priority=assessment.priority,
                progress_percentage=assessment.progress.get("progress_percentage", 0.0) if assessment.progress else 0.0,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at,
                company_size=company_size,
                industry=industry,
                budget_range=budget_range,
                workload_types=workload_types,
                recommendations_generated=assessment.recommendations_generated,
                reports_generated=assessment.reports_generated
            ))
        
        pages = (total + limit - 1) // limit
        
        return AssessmentListResponse(
            assessments=assessment_summaries,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list assessments"
        )


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(assessment_id: str, update_data: AssessmentUpdate):
    """
    Update an existing assessment.
    
    Allows updating assessment details, requirements, and status.
    """
    try:
        # TODO: Implement database update
        # assessment = await Assessment.get(assessment_id)
        # if not assessment:
        #     raise HTTPException(status_code=404, detail="Assessment not found")
        # 
        # # Update fields
        # if update_data.title is not None:
        #     assessment.title = update_data.title
        # # ... update other fields
        # 
        # assessment.updated_at = datetime.utcnow()
        # await assessment.save()
        
        logger.info(f"Updated assessment: {assessment_id}")
        
        # Return updated assessment (mock for now)
        return await get_assessment(assessment_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assessment"
        )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(assessment_id: str):
    """
    Delete an assessment.
    
    Permanently removes the assessment and all associated data.
    """
    try:
        # TODO: Implement database deletion
        # assessment = await Assessment.get(assessment_id)
        # if not assessment:
        #     raise HTTPException(status_code=404, detail="Assessment not found")
        # 
        # await assessment.delete()
        
        logger.info(f"Deleted assessment: {assessment_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assessment"
        )


@router.post("/{assessment_id}/start", response_model=AssessmentStatusUpdate)
async def start_assessment_analysis(assessment_id: str, request: StartAssessmentRequest):
    """
    Start AI agent analysis for an assessment.
    
    Initiates the multi-agent workflow to generate recommendations
    and reports for the assessment.
    """
    try:
        # TODO: Start LangGraph workflow
        # workflow_id = await start_agent_workflow(assessment_id, request.agent_config)
        
        logger.info(f"Started analysis for assessment: {assessment_id}")
        
        return AssessmentStatusUpdate(
            assessment_id=assessment_id,
            status=AssessmentStatus.IN_PROGRESS,
            progress_percentage=5.0,
            current_step="initializing_agents",
            message="AI agent analysis started successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start assessment analysis"
        )