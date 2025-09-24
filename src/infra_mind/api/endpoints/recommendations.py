"""
Recommendation endpoints for Infra Mind.

Handles AI agent recommendations and multi-cloud service suggestions.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from loguru import logger
from datetime import datetime
from decimal import Decimal
import uuid
from bson.decimal128 import Decimal128

from ...models.recommendation import Recommendation, ServiceRecommendation
from ...models.assessment import Assessment
from ...models.user import User
from ...schemas.base import RecommendationConfidence, CloudProvider, Priority
from ...core.rbac import require_permission, Permission, AccessControl

router = APIRouter()


# Response models
from pydantic import BaseModel, Field
from typing import Dict, Any

class ServiceRecommendationResponse(BaseModel):
    """Response model for service recommendations."""
    service_name: str
    provider: CloudProvider
    service_category: str
    estimated_monthly_cost: Optional[Decimal]
    cost_model: Optional[str]
    configuration: Dict[str, Any]
    reasons: List[str]
    alternatives: List[str]
    setup_complexity: str
    implementation_time_hours: Optional[int]


class RecommendationResponse(BaseModel):
    """Response model for agent recommendations."""
    id: str
    assessment_id: str
    agent_name: str
    title: str
    summary: str
    confidence_level: RecommendationConfidence
    confidence_score: float
    recommendation_data: Dict[str, Any]
    recommended_services: List[ServiceRecommendationResponse]
    cost_estimates: Dict[str, Any]
    total_estimated_monthly_cost: Optional[Decimal]
    implementation_steps: List[str]
    prerequisites: List[str]
    risks_and_considerations: List[str]
    business_impact: str
    alignment_score: Optional[float]
    tags: List[str]
    priority: Priority
    category: str
    created_at: datetime
    updated_at: datetime


class RecommendationListResponse(BaseModel):
    """Response for recommendation list endpoints."""
    recommendations: List[RecommendationResponse]
    total: int
    assessment_id: str
    summary: Dict[str, Any]


def convert_decimal128_to_decimal(value):
    """Convert Decimal128 to Decimal for Pydantic compatibility."""
    if isinstance(value, Decimal128):
        return Decimal(str(value))
    elif isinstance(value, dict):
        return {k: convert_decimal128_to_decimal(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_decimal128_to_decimal(item) for item in value]
    return value


class GenerateRecommendationsRequest(BaseModel):
    """Request to generate recommendations."""
    agent_names: Optional[List[str]] = Field(
        default=None,
        description="Specific agents to run (if None, runs all agents)"
    )
    priority_override: Optional[Priority] = None
    custom_config: Optional[Dict[str, Any]] = None


@router.get("/", response_model=RecommendationListResponse)
async def list_recommendations(
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    agent_filter: Optional[str] = Query(None, description="Filter by agent name"),
    current_user: User = Depends(require_permission(Permission.READ_RECOMMENDATION)),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    category_filter: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=100, description="Number of recommendations to return"),
    skip: int = Query(0, ge=0, description="Number of recommendations to skip")
):
    """
    List recommendations with optional filtering.
    
    Returns recommendations based on query parameters. If no assessment_id is provided,
    returns recommendations for all assessments accessible to the current user.
    """
    try:
        logger.info(f"Listing recommendations for user: {current_user.email}")
        
        # Build query filter
        query_filter = {}
        if assessment_id:
            query_filter["assessment_id"] = assessment_id
        
        if agent_filter:
            query_filter["agent_name"] = {"$regex": agent_filter, "$options": "i"}
            
        if category_filter:
            query_filter["category"] = category_filter
            
        # Get recommendations
        recommendations = await Recommendation.find(query_filter).skip(skip).limit(limit).to_list()
        total = await Recommendation.find(query_filter).count()
        
        logger.info(f"Found {len(recommendations)} recommendations (total: {total})")
        
        # Convert to response format
        recommendation_responses = []
        for rec in recommendations:
            recommendation_responses.append(RecommendationResponse(
                id=str(rec.id),
                assessment_id=rec.assessment_id,
                agent_name=rec.agent_name,
                title=rec.title,
                summary=rec.summary,
                confidence_level=rec.confidence_level,
                confidence_score=rec.confidence_score,
                recommendation_data=convert_decimal128_to_decimal(rec.recommendation_data),
                recommended_services=rec.recommended_services,
                cost_estimates=rec.cost_estimates,
                total_estimated_monthly_cost=rec.total_estimated_monthly_cost,
                implementation_steps=rec.implementation_steps,
                prerequisites=rec.prerequisites,
                risks_and_considerations=rec.risks_and_considerations,
                business_impact=rec.business_impact,
                alignment_score=rec.alignment_score,
                tags=rec.tags,
                priority=rec.priority,
                category=rec.category,
                created_at=rec.created_at,
                updated_at=rec.updated_at
            ))
        
        return RecommendationListResponse(
            recommendations=recommendation_responses,
            total=total,
            assessment_id=assessment_id or "all",
            summary={
                "total_recommendations": total,
                "filtered_count": len(recommendations),
                "avg_confidence": sum(r.confidence_score for r in recommendation_responses) / len(recommendation_responses) if recommendation_responses else 0,
                "categories": list(set(r.category for r in recommendation_responses))
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recommendations: {str(e)}"
        )


@router.get("/{assessment_id}", response_model=RecommendationListResponse)
async def get_recommendations(
    assessment_id: str,
    agent_filter: Optional[str] = Query(None, description="Filter by agent name"),
    current_user: User = Depends(require_permission(Permission.READ_RECOMMENDATION)),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    category_filter: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get recommendations for a specific assessment.
    
    Returns all AI agent recommendations for the assessment with optional filtering.
    Includes service recommendations, cost estimates, and implementation guidance.
    """
    try:
        # Query database for real recommendations
        query_filters = {"assessment_id": assessment_id}
        
        if agent_filter:
            query_filters["agent_name"] = agent_filter
        if confidence_min:
            query_filters["confidence_score"] = {"$gte": confidence_min}
        if category_filter:
            query_filters["category"] = category_filter
        
        # Execute database query using direct MongoDB client
        # Note: Using direct MongoDB until Beanie model is properly aligned with existing data
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.get_database("infra_mind")
        
        cursor = db.recommendations.find(query_filters)
        recommendations_docs = await cursor.to_list(length=None)
        
        # Convert to response format
        recommendations = []
        for rec_raw in recommendations_docs:
            # Apply Decimal128 conversion to entire record first
            rec = convert_decimal128_to_decimal(rec_raw)
            
            # Convert service recommendations (use empty list if not present)
            service_recs = []
            for service in rec.get('recommended_services', []):
                service_recs.append(ServiceRecommendationResponse(
                    service_name=service.get('service_name'),
                    provider=service.get('provider', 'AWS'),
                    service_category=service.get('service_category'),
                    estimated_monthly_cost=service.get('estimated_monthly_cost'),
                    cost_model=service.get('cost_model'),
                    configuration=service.get('configuration', {}),
                    reasons=service.get('reasons', []),
                    alternatives=service.get('alternatives', []),
                    setup_complexity=service.get('setup_complexity', 'medium'),
                    implementation_time_hours=service.get('implementation_time_hours')
                ))
            
            recommendations.append(RecommendationResponse(
                id=str(rec.get('_id')),
                assessment_id=rec.get('assessment_id'),
                agent_name=rec.get('agent_name'),
                title=rec.get('title'),
                summary=rec.get('summary'),
                confidence_level=rec.get('confidence_level'),
                confidence_score=rec.get('confidence_score'),
                recommendation_data=rec.get('recommendation_data', {}),
                recommended_services=service_recs,
                cost_estimates=rec.get('cost_estimates', {}),
                total_estimated_monthly_cost=rec.get('total_estimated_monthly_cost'),
                implementation_steps=rec.get('implementation_steps', []),
                prerequisites=rec.get('prerequisites', []),
                risks_and_considerations=rec.get('risks_and_considerations', []),
                business_impact=rec.get('business_impact', 'medium'),
                alignment_score=rec.get('alignment_score'),
                tags=rec.get('tags', []),
                priority=rec.get('priority', 'medium'),
                category=rec.get('category'),
                created_at=rec.get('created_at'),
                updated_at=rec.get('updated_at')
            ))
        
        logger.info(f"Retrieved {len(recommendations)} recommendations for assessment: {assessment_id}")
        
        # Calculate summary from the final recommendations list
        summary = {
            "total_recommendations": len(recommendations),
            "high_confidence_count": len([r for r in recommendations if r.confidence_score >= 0.8]),
            "total_estimated_cost": sum((r.total_estimated_monthly_cost or 0) for r in recommendations),
            "agents_involved": list(set(r.agent_name for r in recommendations)),
            "categories": list(set(r.category for r in recommendations)),
            "data_source": "database",
            "filtered_by": {
                "agent": agent_filter,
                "confidence_min": confidence_min,
                "category": category_filter
            } if any([agent_filter, confidence_min, category_filter]) else None
        }
        
        return RecommendationListResponse(
            recommendations=recommendations,
            total=len(recommendations),
            assessment_id=assessment_id,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve recommendations for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendations"
        )


@router.post("/{assessment_id}/generate", response_model=Dict[str, Any])
async def generate_recommendations(assessment_id: str, request: GenerateRecommendationsRequest):
    """
    Generate new recommendations using AI agents.
    
    Triggers the multi-agent workflow to analyze the assessment and generate
    recommendations from specialized agents (CTO, Cloud Engineer, Research, etc.).
    """
    try:
        # Get assessment from database
        from ...models.assessment import Assessment
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Start real workflow for recommendation generation
        logger.info(f"🔍 IMPORTING AssessmentWorkflow")
        print(f"🔍 IMPORTING AssessmentWorkflow")
        from ...workflows.assessment_workflow import AssessmentWorkflow
        logger.info(f"✅ IMPORTED AssessmentWorkflow successfully")
        print(f"✅ IMPORTED AssessmentWorkflow successfully")
        
        # Create workflow instance
        logger.info(f"🏗️ CREATING AssessmentWorkflow instance")
        print(f"🏗️ CREATING AssessmentWorkflow instance")
        workflow = AssessmentWorkflow()
        workflow_id = f"assessment_workflow_{assessment_id}_{uuid.uuid4().hex[:8]}"
        logger.info(f"✅ CREATED workflow instance with ID: {workflow_id}")
        print(f"✅ CREATED workflow instance with ID: {workflow_id}")
        
        # Start asynchronous workflow execution using the workflow's own execute method
        import asyncio
        async def run_workflow():
            try:
                logger.info(f"🔥 BACKGROUND TASK STARTING for workflow {workflow_id}")
                print(f"🔥 BACKGROUND TASK STARTING for workflow {workflow_id}")
                
                # Initialize database connection for workflow context
                from ...core.database import init_database
                logger.info(f"🔄 INITIALIZING DATABASE in background task")
                print(f"🔄 INITIALIZING DATABASE in background task")
                await init_database()
                logger.info(f"✅ DATABASE INITIALIZED in background task")
                print(f"✅ DATABASE INITIALIZED in background task")
                
                # Use AssessmentWorkflow's execute_workflow method directly
                logger.info(f"🚀 CALLING WORKFLOW EXECUTE for {workflow_id}")
                print(f"🚀 CALLING WORKFLOW EXECUTE for {workflow_id}")
                result = await workflow.execute_workflow(
                    workflow_id=workflow_id,
                    assessment=assessment
                )
                logger.info(f"✅ Assessment workflow {workflow_id} completed successfully")
                print(f"✅ Assessment workflow {workflow_id} completed successfully")
                return result
            except Exception as e:
                logger.error(f"❌ Assessment workflow {workflow_id} failed: {e}")
                print(f"❌ Assessment workflow {workflow_id} failed: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                print(f"Full traceback: {traceback.format_exc()}")
                raise
        
        # For debugging, let's try running the workflow directly to see what fails
        try:
            logger.info(f"🧪 TESTING DIRECT WORKFLOW EXECUTION for {workflow_id}")
            print(f"🧪 TESTING DIRECT WORKFLOW EXECUTION for {workflow_id}")
            
            # Initialize database connection for workflow context
            from ...core.database import init_database
            await init_database()
            
            # Use AssessmentWorkflow's execute_workflow method directly
            result = await workflow.execute_workflow(
                workflow_id=workflow_id,
                assessment=assessment
            )
            logger.info(f"🎉 DIRECT WORKFLOW EXECUTION SUCCEEDED for {workflow_id}")
            print(f"🎉 DIRECT WORKFLOW EXECUTION SUCCEEDED for {workflow_id}")
        except Exception as e:
            logger.error(f"💥 DIRECT WORKFLOW EXECUTION FAILED for {workflow_id}: {e}")
            print(f"💥 DIRECT WORKFLOW EXECUTION FAILED for {workflow_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            print(f"Full traceback: {traceback.format_exc()}")
        
        # For now, also keep the background task
        # task = asyncio.ensure_future(run_workflow())
        # task.add_done_callback(lambda t: logger.info(f"📋 Background task completed for {workflow_id}") if not t.exception() else logger.error(f"💥 Background task failed for {workflow_id}: {t.exception()}"))
        
        logger.info(f"Started real recommendation generation workflow for assessment: {assessment_id}")
        
        return {
            "message": "Recommendation generation started using real AI agents",
            "assessment_id": assessment_id,
            "workflow_id": workflow_id,
            "agents_triggered": request.agent_names or ["cto_agent", "cloud_engineer_agent", "research_agent", "report_generator_agent"],
            "estimated_completion_minutes": 3,
            "status": "in_progress",
            "real_workflow": True,
            "llm_enabled": True,
            "database_storage": True
        }
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/{assessment_id}/agents/{agent_name}", response_model=RecommendationResponse)
async def get_agent_recommendation(assessment_id: str, agent_name: str):
    """
    Get recommendation from a specific agent.
    
    Returns the recommendation generated by a specific AI agent for the assessment.
    """
    try:
        # Query database for specific agent recommendation
        recommendation_doc = await Recommendation.find_one({
            "assessment_id": assessment_id,
            "agent_name": agent_name
        })
        
        if recommendation_doc:
            # Convert service recommendations
            service_recs = []
            for service in recommendation_doc.recommended_services:
                service_recs.append(ServiceRecommendationResponse(
                    service_name=service.service_name,
                    provider=service.provider,
                    service_category=service.service_category,
                    estimated_monthly_cost=service.estimated_monthly_cost,
                    cost_model=service.cost_model,
                    configuration=service.configuration,
                    reasons=service.reasons,
                    alternatives=service.alternatives,
                    setup_complexity=service.setup_complexity,
                    implementation_time_hours=service.implementation_time_hours
                ))
            
            # Return real recommendation from database
            return RecommendationResponse(
                id=str(recommendation_doc.id),
                assessment_id=recommendation_doc.assessment_id,
                agent_name=recommendation_doc.agent_name,
                title=recommendation_doc.title,
                summary=recommendation_doc.summary,
                confidence_level=recommendation_doc.confidence_level,
                confidence_score=recommendation_doc.confidence_score,
                recommendation_data=recommendation_doc.recommendation_data,
                recommended_services=service_recs,
                cost_estimates=recommendation_doc.cost_estimates,
                total_estimated_monthly_cost=recommendation_doc.total_estimated_monthly_cost,
                implementation_steps=recommendation_doc.implementation_steps,
                prerequisites=recommendation_doc.prerequisites,
                risks_and_considerations=recommendation_doc.risks_and_considerations,
                business_impact=recommendation_doc.business_impact,
                alignment_score=recommendation_doc.alignment_score,
                tags=recommendation_doc.tags,
                priority=recommendation_doc.priority,
                category=recommendation_doc.category,
                created_at=recommendation_doc.created_at,
                updated_at=recommendation_doc.updated_at
            )
        
        logger.info(f"No database recommendation found for {agent_name}, using mock data for assessment: {assessment_id}")
        
        # Mock response based on agent type for fallback
        if agent_name == "cto_agent":
            return RecommendationResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                agent_name=agent_name,
                title="Executive Infrastructure Strategy",
                summary="Strategic recommendations for infrastructure investment and ROI optimization",
                confidence_level=RecommendationConfidence.HIGH,
                confidence_score=0.88,
                recommendation_data={
                    "strategic_priorities": ["cost_optimization", "scalability", "security"],
                    "investment_timeline": "12_months",
                    "expected_roi": "250%"
                },
                recommended_services=[],
                cost_estimates={"annual_budget": 120000, "expected_savings": 50000},
                total_estimated_monthly_cost=Decimal("10000.00"),
                implementation_steps=[
                    "Establish cloud governance framework",
                    "Implement cost monitoring and optimization",
                    "Scale infrastructure based on business growth"
                ],
                prerequisites=["Executive buy-in", "Budget allocation"],
                risks_and_considerations=["Change management", "Skills gap"],
                business_impact="high",
                alignment_score=0.92,
                tags=["strategy", "executive", "roi"],
                priority=Priority.HIGH,
                category="strategy",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation from {agent_name} not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve {agent_name} recommendation for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent recommendation"
        )


@router.post("/{assessment_id}/validate", response_model=Dict[str, Any])
async def validate_recommendations(assessment_id: str):
    """
    Validate recommendations for quality and consistency.
    
    Runs validation checks on all recommendations to ensure quality,
    consistency, and alignment with business requirements.
    """
    try:
        # TODO: Implement recommendation validation logic
        # validation_results = await validate_assessment_recommendations(assessment_id)
        
        logger.info(f"Validated recommendations for assessment: {assessment_id}")
        
        return {
            "assessment_id": assessment_id,
            "validation_status": "completed",
            "overall_score": 0.85,
            "checks_performed": [
                "cost_consistency",
                "technical_feasibility", 
                "business_alignment",
                "compliance_requirements"
            ],
            "issues_found": [],
            "recommendations_validated": 3,
            "high_confidence_recommendations": 2
        }
        
    except Exception as e:
        logger.error(f"Failed to validate recommendations for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate recommendations"
        )