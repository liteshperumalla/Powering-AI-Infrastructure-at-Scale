"""
Assessment endpoints for Infra Mind.

Handles infrastructure assessment creation, management, and retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from typing import List, Optional, Dict, Any
from loguru import logger
import uuid
import asyncio
from datetime import datetime
from decimal import Decimal
from bson import Decimal128
from beanie import PydanticObjectId

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
from ...models.recommendation import Recommendation, ServiceRecommendation
from ...models.report import Report, ReportSection
from ...schemas.base import AssessmentStatus, Priority, CloudProvider, RecommendationConfidence, ReportType, ReportFormat, ReportStatus
from .auth import get_current_user
from ...models.user import User
from ...workflows.orchestrator import agent_orchestrator, OrchestrationConfig
from ...agents.base import AgentRole
from ...core.rbac import (
    require_permission, 
    require_role, 
    Permission, 
    Role, 
    AccessControl,
    require_resource_access
)

router = APIRouter()


async def store_progress_update_in_db(assessment_id, update_data):
    """Store progress update in database for polling fallback"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", 
                             "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.get_database("infra_mind")
        
        # Store in assessment_progress collection for polling
        progress_doc = {
            "assessment_id": str(assessment_id),
            "timestamp": datetime.utcnow(),
            "progress_data": update_data,
            "type": "progress_update"
        }
        
        await db.assessment_progress.insert_one(progress_doc)
        
        # Clean up old progress updates (keep last 100 per assessment)
        old_updates = await db.assessment_progress.find({
            "assessment_id": str(assessment_id)
        }).sort("timestamp", -1).skip(100).to_list(length=None)
        
        if old_updates:
            old_ids = [doc["_id"] for doc in old_updates]
            await db.assessment_progress.delete_many({"_id": {"$in": old_ids}})
            
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to store progress update in DB: {e}")
        raise


def convert_mongodb_data(data):
    """Convert MongoDB specific types to Python types for Pydantic serialization."""
    if isinstance(data, dict):
        return {key: convert_mongodb_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_mongodb_data(item) for item in data]
    elif isinstance(data, Decimal128):
        return str(data.to_decimal())
    else:
        return data


async def start_assessment_workflow(assessment: Assessment, app_state=None):
    """
    Start the assessment workflow to generate recommendations and reports.
    
    This function runs the complete workflow asynchronously to generate
    recommendations and reports for the assessment.
    """
    logger.info(f"Starting assessment workflow for assessment {assessment.id}")
    
    # Helper function to broadcast updates
    async def broadcast_update(step: str, progress: float, message: str = ""):
        """Enhanced broadcast function with error handling and fallback"""
        try:
            # Primary: Try WebSocket broadcast
            if app_state and hasattr(app_state, 'broadcast_workflow_update'):
                update_data = {
                    "assessment_id": str(assessment.id),
                    "status": assessment.status,
                    "current_step": step,
                    "progress_percentage": progress,
                    "message": message,
                    "workflow_id": assessment.workflow_id or f"workflow_{assessment.id}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "steps": [
                        {"name": "Created", "status": "completed"},
                        {"name": "Initializing", "status": "completed" if progress > 5 else "pending"},
                        {"name": "CTO Agent", "status": "completed" if progress > 15 else "running" if progress > 5 else "pending"},
                        {"name": "Cloud Engineer Agent", "status": "completed" if progress > 25 else "running" if progress > 15 else "pending"},
                        {"name": "Infrastructure Agent", "status": "completed" if progress > 35 else "running" if progress > 25 else "pending"},
                        {"name": "AI Consultant Agent", "status": "completed" if progress > 45 else "running" if progress > 35 else "pending"},
                        {"name": "MLOps Agent", "status": "completed" if progress > 55 else "running" if progress > 45 else "pending"},
                        {"name": "Compliance Agent", "status": "completed" if progress > 65 else "running" if progress > 55 else "pending"},
                        {"name": "Research Agent", "status": "completed" if progress > 70 else "running" if progress > 65 else "pending"},
                        {"name": "Web Research Agent", "status": "completed" if progress > 75 else "running" if progress > 70 else "pending"},
                        {"name": "Simulation Agent", "status": "completed" if progress > 80 else "running" if progress > 75 else "pending"},
                        {"name": "Chatbot Agent", "status": "completed" if progress > 85 else "running" if progress > 80 else "pending"},
                        {"name": "Report Generator", "status": "completed" if progress > 95 else "running" if progress > 85 else "pending"},
                        {"name": "Completed", "status": "completed" if progress >= 100 else "pending"}
                    ]
                }
                
                try:
                    await app_state.broadcast_workflow_update(str(assessment.id), update_data)
                    logger.debug(f"✅ WebSocket update sent - Step: {step}, Progress: {progress}%")
                except Exception as ws_error:
                    logger.warning(f"⚠️ WebSocket broadcast failed: {ws_error}")
                    
                    # Fallback 1: Store update in database for polling
                    try:
                        await store_progress_update_in_db(assessment.id, update_data)
                        logger.info(f"📊 Progress stored in DB as fallback - Step: {step}")
                    except Exception as db_error:
                        logger.error(f"❌ Fallback DB storage failed: {db_error}")
                    
                    # Fallback 2: Update assessment record directly
                    try:
                        assessment.progress = {
                            "current_step": step,
                            "progress_percentage": progress,
                            "message": message,
                            "last_update": datetime.utcnow(),
                            "websocket_failed": True
                        }
                        assessment.progress_percentage = progress
                        await assessment.save()
                        logger.info(f"💾 Assessment progress updated directly in DB")
                    except Exception as save_error:
                        logger.error(f"❌ Direct assessment update failed: {save_error}")
            else:
                # No WebSocket available - use database polling fallback
                logger.info(f"🔄 No WebSocket - using DB polling fallback for {step}")
                try:
                    await store_progress_update_in_db(assessment.id, {
                        "current_step": step,
                        "progress_percentage": progress,
                        "message": message,
                        "websocket_available": False
                    })
                except:
                    pass  # Non-critical fallback
                
                # Also update assessment directly
                try:
                    assessment.progress = {
                        "current_step": step,
                        "progress_percentage": progress,
                        "message": message,
                        "last_update": datetime.utcnow(),
                        "websocket_available": False
                    }
                    assessment.progress_percentage = progress
                    await assessment.save()
                except Exception as save_error:
                    logger.error(f"❌ Assessment update failed: {save_error}")
                
        except Exception as e:
            logger.error(f"❌ Critical error in broadcast_update: {e}")
            # Emergency fallback - just update the assessment
            try:
                assessment.progress = {
                    "current_step": step,
                    "progress_percentage": progress,
                    "message": f"Update failed, step: {step}",
                    "emergency_fallback": True
                }
                assessment.progress_percentage = progress
                await assessment.save()
                logger.info(f"🚑 Emergency fallback applied for step: {step}")
            except:
                logger.critical(f"🚨 Complete fallback failure for assessment {assessment.id}")
                pass  # Last resort - don't fail the workflow
    
    try:
        # Step 1: Initialize workflow with 11 agents
        assessment.progress = {
            "current_step": "initializing", 
            "completed_steps": ["created"], 
            "total_steps": 13,  # Updated to include all 11 agents + initialization + completion
            "progress_percentage": 5.0
        }
        await assessment.save()
        await broadcast_update("initializing", 20.0, "Initializing workflow...")
        
        # Simulate some processing time
        await asyncio.sleep(2)
        
        # Step 2: Analysis phase
        assessment.progress = {
            "current_step": "analysis", 
            "completed_steps": ["created", "initializing"], 
            "total_steps": 5, 
            "progress_percentage": 40.0
        }
        await assessment.save()
        await broadcast_update("analysis", 40.0, "Analyzing requirements...")
        
        # Generate actual recommendations using multi-agent orchestrator
        await generate_orchestrated_recommendations(assessment, app_state, broadcast_update)
        
        # Step 3: Generating recommendations
        assessment.progress = {
            "current_step": "recommendations", 
            "completed_steps": ["created", "initializing", "analysis"], 
            "total_steps": 5, 
            "progress_percentage": 60.0
        }
        await assessment.save()
        await broadcast_update("recommendations", 60.0, "AI agents generating recommendations...")
        
        await asyncio.sleep(2)
        
        # Step 4: Report generation
        assessment.progress = {
            "current_step": "report_generation", 
            "completed_steps": ["created", "initializing", "analysis", "recommendations"], 
            "total_steps": 5, 
            "progress_percentage": 80.0
        }
        await assessment.save()
        await broadcast_update("report_generation", 80.0, "Generating comprehensive reports...")
        
        # Generate actual reports
        await generate_actual_reports(assessment, app_state, broadcast_update)
        
        await asyncio.sleep(1)
        
        # Step 5: Complete
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completion_percentage = 100.0
        assessment.completed_at = datetime.utcnow()
        assessment.recommendations_generated = True
        assessment.reports_generated = True
        assessment.progress = {
            "current_step": "completed", 
            "completed_steps": ["created", "initializing", "analysis", "recommendations", "report_generation"], 
            "total_steps": 5, 
            "progress_percentage": 100.0
        }
        assessment.workflow_id = f"workflow_{assessment.id}_{int(datetime.utcnow().timestamp())}"
        
        await assessment.save()
        await broadcast_update("completed", 100.0, "Assessment completed successfully!")
        
        # Broadcast dashboard update for completed assessment
        try:
            if app_state and hasattr(app_state, 'broadcast_dashboard_update'):
                await app_state.broadcast_dashboard_update({
                    "type": "assessment_completed",
                    "assessment_id": str(assessment.id),
                    "assessment_data": {
                        "id": str(assessment.id),
                        "title": assessment.title,
                        "status": assessment.status,
                        "completion_percentage": assessment.completion_percentage,
                        "completed_at": assessment.completed_at.isoformat(),
                        "recommendations_generated": assessment.recommendations_generated,
                        "reports_generated": assessment.reports_generated
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Assessment '{assessment.title}' has been completed successfully!"
                })
                
            # Invalidate dashboard cache for refresh
            if app_state and hasattr(app_state, 'invalidate_dashboard_cache'):
                await app_state.invalidate_dashboard_cache()
                
        except Exception as e:
            logger.warning(f"Failed to broadcast dashboard update for completed assessment: {e}")
        
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
        await broadcast_update("failed", 20.0, f"Workflow failed: {str(e)}")


async def generate_orchestrated_recommendations(assessment: Assessment, app_state=None, broadcast_update=None):
    """Generate recommendations using the multi-agent orchestrator."""
    logger.info(f"Starting multi-agent orchestrated recommendations for assessment {assessment.id}")
    
    try:
        if broadcast_update:
            await broadcast_update("multi_agent_orchestration", 15.0, "Orchestrating AI agents for comprehensive analysis...")
        
        # Define the agents to use for this assessment
        agent_roles = [
            AgentRole.CTO,              # Strategic planning
            AgentRole.CLOUD_ENGINEER,   # Technical implementation  
            AgentRole.INFRASTRUCTURE,   # Infrastructure design
            AgentRole.RESEARCH,         # Market analysis
            AgentRole.COMPLIANCE,       # Security and compliance
            AgentRole.MLOPS,           # AI/ML operations
        ]
        
        # Configure orchestrator for assessment
        orchestration_config = OrchestrationConfig(
            max_parallel_agents=3,
            agent_timeout_seconds=300,
            retry_failed_agents=True,
            max_retries=1,
            require_consensus=True,
            consensus_threshold=0.7,
            enable_agent_communication=True
        )
        
        # Update orchestrator config
        agent_orchestrator.config = orchestration_config
        
        # Execute orchestration
        if broadcast_update:
            await broadcast_update("agent_coordination", 25.0, f"Coordinating {len(agent_roles)} specialized agents...")
            
        orchestration_result = await agent_orchestrator.orchestrate_assessment(
            assessment=assessment,
            agent_roles=agent_roles,
            context={
                "assessment_id": str(assessment.id),
                "orchestration_mode": "comprehensive",
                "priority": "high"
            }
        )
        
        if broadcast_update:
            await broadcast_update("processing_results", 70.0, f"Processing recommendations from {orchestration_result.successful_agents} agents...")
        
        # Convert orchestrated results to Recommendation objects
        recommendations = []
        for synthesized_rec in orchestration_result.synthesized_recommendations:
            try:
                # Create service recommendations from orchestrated results  
                service_recommendations = []
                if "services" in synthesized_rec:
                    for service in synthesized_rec["services"][:3]:  # Max 3 services per recommendation
                        service_rec = ServiceRecommendation(
                            service_name=service.get("name", "Cloud Service"),
                            provider=CloudProvider.AWS,  # Default to AWS, can be enhanced
                            service_category=service.get("category", "compute"),
                            estimated_monthly_cost=Decimal(str(service.get("cost", "500.00"))),
                            cost_model="subscription",
                            configuration=service.get("config", {}),
                            reasons=service.get("reasons", ["Orchestrated recommendation"]),
                            alternatives=service.get("alternatives", []),
                            setup_complexity="medium",
                            implementation_time_hours=service.get("implementation_hours", 40)
                        )
                        service_recommendations.append(service_rec)
                
                # Create main recommendation
                recommendation = Recommendation(
                    assessment_id=str(assessment.id),
                    user_id=assessment.user_id,
                    agent_name=synthesized_rec.get("source_agent", "multi_agent_orchestrator"),
                    title=synthesized_rec.get("title", "Multi-Agent Recommendation"),
                    summary=synthesized_rec.get("description", "Comprehensive recommendation from multiple AI agents"),
                    confidence_level=RecommendationConfidence.HIGH,
                    confidence_score=synthesized_rec.get("combined_confidence", 0.85),
                    business_alignment=synthesized_rec.get("business_alignment", 0.9),
                    recommendation_data=synthesized_rec,  # Add the required field
                    recommended_services=service_recommendations,
                    cost_estimates=synthesized_rec.get("cost_estimates", {}),
                    total_estimated_monthly_cost=Decimal(str(synthesized_rec.get("total_cost", "1500.00"))),
                    implementation_steps=synthesized_rec.get("implementation_steps", [
                        "Review orchestrated recommendations",
                        "Implement prioritized solutions",
                        "Monitor and optimize"
                    ]),
                    prerequisites=synthesized_rec.get("prerequisites", []),
                    risks_and_considerations=synthesized_rec.get("risks", [
                        "Coordinate implementation across multiple areas"
                    ]),
                    business_impact="high",
                    alignment_score=synthesized_rec.get("business_alignment", 0.9),
                    tags=["orchestrated", "multi-agent", synthesized_rec.get("type", "comprehensive")],
                    priority=Priority.HIGH,
                    category=synthesized_rec.get("type", "strategic")
                )
                
                recommendations.append(recommendation)
                
            except Exception as e:
                logger.error(f"Failed to create recommendation from orchestrated result: {e}")
                continue
        
        # Save recommendations to database
        saved_count = 0
        for recommendation in recommendations:
            try:
                if broadcast_update:
                    await broadcast_update(
                        "saving_recommendations",
                        70.0 + (saved_count * 15.0 / len(recommendations)),
                        f"Saving orchestrated recommendation: {recommendation.title[:50]}..."
                    )
                
                await recommendation.insert()
                saved_count += 1
                logger.info(f"Saved orchestrated recommendation: {recommendation.title}")
                
            except Exception as e:
                logger.error(f"Failed to save orchestrated recommendation {recommendation.title}: {e}")
        
        # Update assessment with orchestration results
        assessment.recommendations_generated = True
        assessment.agent_states = {
            "orchestration": {
                "orchestration_id": orchestration_result.orchestration_metadata.get("orchestration_id"),
                "total_agents": orchestration_result.total_agents,
                "successful_agents": orchestration_result.successful_agents,
                "failed_agents": orchestration_result.failed_agents,
                "consensus_score": orchestration_result.consensus_score,
                "execution_time": orchestration_result.execution_time
            }
        }
        assessment.progress = {
            "current_step": "orchestrated_recommendations_generated",
            "completed_steps": ["created", "analyzing", "multi_agent_orchestration"],
            "total_steps": 5,
            "progress_percentage": 85.0
        }
        await assessment.save()
        
        if broadcast_update:
            await broadcast_update("orchestration_complete", 85.0, 
                                   f"Multi-agent orchestration complete! Generated {saved_count} recommendations from {orchestration_result.successful_agents} agents")
        
        logger.info(f"Successfully completed multi-agent orchestration for assessment {assessment.id}")
        logger.info(f"Orchestration stats: {orchestration_result.successful_agents}/{orchestration_result.total_agents} agents successful, {saved_count} recommendations saved")
    
    except Exception as e:
        assessment.recommendations_generated = False
        assessment.status = AssessmentStatus.FAILED
        
        # Safely update agent_states
        if not isinstance(assessment.agent_states, dict):
            assessment.agent_states = {}
            
        assessment.agent_states['orchestration'] = {
            "status": "failed",
            "error": str(e),
            "execution_time": orchestration_result.execution_time if 'orchestration_result' in locals() else 0
        }
        
        assessment.progress = {
            "current_step": "orchestration_failed",
            "completed_steps": assessment.progress.get("completed_steps", ["created", "analyzing"]),
            "total_steps": 5,
            "progress_percentage": 75.0,
            "error": f"Multi-agent orchestration failed: {str(e)}"
        }
        await assessment.save()
        
        if broadcast_update:
            await broadcast_update("orchestration_failed", 75.0, f"Multi-agent orchestration failed: {str(e)}")
        
        logger.error(f"Multi-agent orchestration failed for assessment {assessment.id}: {e}")
        raise


async def generate_actual_recommendations(assessment: Assessment, app_state=None, broadcast_update=None):
    """Generate dynamic AI recommendations using LLM with real cloud services API."""
    logger.info(f"Generating LLM-powered recommendations with cloud services API for assessment {assessment.id}")
    
    try:
        if broadcast_update:
            await broadcast_update("llm_cloud_agent", 15.0, "LLM analyzing requirements with cloud services API...")
        
        # Generate recommendations using new LLM-powered function
        recommendations = await generate_llm_powered_recommendations(assessment)
        
        if not recommendations:
            logger.warning(f"No recommendations generated for assessment {assessment.id}")
            return
            
        logger.info(f"Generated {len(recommendations)} LLM-powered recommendations for assessment {assessment.id}")
        
        # Save recommendations to database
        saved_count = 0
        for recommendation in recommendations:
            try:
                if broadcast_update:
                    await broadcast_update(
                        recommendation.agent_name, 
                        15.0 + (saved_count * 70.0 / len(recommendations)), 
                        f"Saving recommendation: {recommendation.title[:50]}..."
                    )
                
                await recommendation.insert()
                saved_count += 1
                logger.info(f"Saved recommendation: {recommendation.title}")
                
            except Exception as e:
                logger.error(f"Failed to save recommendation {recommendation.title}: {e}")
        
        # Update assessment status
        assessment.recommendations_generated = True
        assessment.progress = {
            "current_step": "recommendations_generated",
            "completed_steps": ["created", "analyzing", "generating_recommendations"],
            "total_steps": 5,
            "progress_percentage": 85.0
        }
        await assessment.save()
        
        if broadcast_update:
            await broadcast_update("completion", 85.0, f"Generated {saved_count} recommendations successfully!")
        
        logger.info(f"Successfully generated and saved {saved_count} LLM-powered recommendations for assessment {assessment.id}")
    
    except Exception as e:
        logger.error(f"Failed to generate LLM-powered recommendations for assessment {assessment.id}: {e}")
        raise


async def generate_actual_reports(assessment: Assessment, app_state=None, broadcast_update=None):
    """Generate actual reports using Report Generator Agent with LLM."""
    logger.info(f"Starting LLM-powered report generation for assessment {assessment.id}")
    
    try:
        if broadcast_update:
            await broadcast_update("report_generator_agent", 90.0, "Report Generator Agent creating comprehensive reports using AI...")
        
        # Create Report Generator Agent
        from ...agents import agent_factory  # Import from agents package to ensure registration
        from ...agents.base import AgentRole
        from ...agents.report_generator_agent import ReportGeneratorAgent
        
        report_agent = await agent_factory.create_agent(AgentRole.REPORT_GENERATOR)
        if not report_agent:
            logger.error("Failed to create Report Generator Agent")
            return
        
        # Generate Executive Report using AI
        if broadcast_update:
            await broadcast_update("executive_report", 92.0, "Generating executive summary report...")
            
        executive_result = await report_agent.process_assessment(assessment, {
            "report_type": "executive_summary",
            "target_audience": "C-level executives",
            "focus_areas": ["strategic_planning", "investment_analysis", "risk_assessment", "roi_projections"]
        })
        
        if executive_result.status.value == "completed":
            executive_report = Report(
                assessment_id=str(assessment.id),
                user_id=assessment.user_id,
                title="Executive Infrastructure Assessment Report",
                description="AI-generated strategic report for executive decision-making",
                report_type="executive_summary",
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=executive_result.data.get("sections", ["executive_summary", "recommendations", "investment_analysis"]),
                total_pages=executive_result.data.get("page_count", 12),
                word_count=executive_result.data.get("word_count", 3500),
                file_path=f"/reports/{assessment.id}/executive_summary.pdf",
                file_size_bytes=executive_result.data.get("file_size", 2400000),
                generated_by=["report_generator_agent"],
                generation_time_seconds=executive_result.execution_time or 45.0,
                completeness_score=executive_result.data.get("completeness_score", 0.95),
                confidence_score=executive_result.data.get("confidence_score", 0.89),
                priority=Priority.HIGH,
                tags=["executive", "strategic", "ai_generated"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                content=executive_result.data.get("content", {})
            )
            await executive_report.insert()
            logger.info(f"Saved AI-generated Executive Report for assessment {assessment.id}")
        
        # Generate Technical Report using AI
        if broadcast_update:
            await broadcast_update("technical_report", 95.0, "Generating technical implementation report...")
            
        technical_result = await report_agent.process_assessment(assessment, {
            "report_type": "technical_roadmap", 
            "target_audience": "technical_teams",
            "focus_areas": ["architecture", "implementation", "operations", "security", "monitoring"]
        })
        
        if technical_result.status.value == "completed":
            technical_report = Report(
                assessment_id=str(assessment.id),
                user_id=assessment.user_id,
                title="Technical Infrastructure Implementation Guide",
                description="AI-generated technical implementation guide with detailed procedures",
                report_type="technical_roadmap",
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=technical_result.data.get("sections", ["architecture", "implementation", "operations"]),
                total_pages=technical_result.data.get("page_count", 28),
                word_count=technical_result.data.get("word_count", 8200),
                file_path=f"/reports/{assessment.id}/technical_implementation.pdf",
                file_size_bytes=technical_result.data.get("file_size", 5800000),
                generated_by=["report_generator_agent"],
                generation_time_seconds=technical_result.execution_time or 78.0,
                completeness_score=technical_result.data.get("completeness_score", 0.92),
                confidence_score=technical_result.data.get("confidence_score", 0.85),
                priority=Priority.HIGH,
                tags=["technical", "implementation", "ai_generated"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                content=technical_result.data.get("content", {})
            )
            await technical_report.insert()
            logger.info(f"Saved AI-generated Technical Report for assessment {assessment.id}")
        
        # Generate Cost Analysis Report using AI
        if broadcast_update:
            await broadcast_update("cost_analysis", 97.0, "Generating cost analysis report...")
            
        cost_result = await report_agent.process_assessment(assessment, {
            "report_type": "cost_analysis",
            "target_audience": "financial_teams",
            "focus_areas": ["cost_breakdown", "optimization_opportunities", "budget_projections", "roi_analysis"]
        })
        
        if cost_result.status.value == "completed":
            cost_report = Report(
                assessment_id=str(assessment.id),
                user_id=assessment.user_id,
                title="Infrastructure Cost Analysis and Optimization",
                description="AI-generated cost analysis with optimization recommendations",
                report_type="cost_analysis",
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
                progress_percentage=100.0,
                sections=cost_result.data.get("sections", ["cost_analysis", "optimization", "projections"]),
                total_pages=cost_result.data.get("page_count", 16),
                word_count=cost_result.data.get("word_count", 4800),
                file_path=f"/reports/{assessment.id}/cost_analysis.pdf",
                file_size_bytes=cost_result.data.get("file_size", 3200000),
                generated_by=["report_generator_agent"],
                generation_time_seconds=cost_result.execution_time or 52.0,
                completeness_score=cost_result.data.get("completeness_score", 0.90),
                confidence_score=cost_result.data.get("confidence_score", 0.88),
                priority=Priority.MEDIUM,
                tags=["financial", "cost_analysis", "ai_generated"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                content=cost_result.data.get("content", {})
            )
            await cost_report.insert()
            logger.info(f"Saved AI-generated Cost Analysis Report for assessment {assessment.id}")
        
        if broadcast_update:
            await broadcast_update("reports_completed", 100.0, "All reports generated successfully!")
            
        logger.info(f"Successfully generated and saved AI-powered reports for assessment {assessment.id}")
        
    except Exception as e:
        logger.error(f"Failed to generate reports for assessment {assessment.id}: {e}")
        raise



@router.post("/simple", status_code=status.HTTP_201_CREATED)
async def create_simple_assessment(data: dict, current_user: User = Depends(get_current_user)):
    """
    Create a simple assessment for testing with all required fields populated.
    """
    try:
        current_time = datetime.utcnow()
        user_id = str(current_user.id)
        
        # Create complete business requirements with defaults
        business_requirements = {
            "company_size": data.get("company_size", "startup"),
            "industry": data.get("industry", "technology"), 
            "business_goals": data.get("business_goals", ["scalability", "cost_optimization"]),
            "growth_projection": data.get("growth_projection", "medium"),
            "budget_constraints": data.get("budget_constraints", 25000),
            "team_structure": data.get("team_structure", "small"),
            "project_timeline_months": data.get("project_timeline_months", 6),
            **data.get("business_requirements", {})
        }
        
        # Create complete technical requirements with defaults
        technical_requirements = {
            "current_infrastructure": data.get("current_infrastructure", "cloud"),
            "workload_types": data.get("workload_types", ["web_application"]),
            "performance_requirements": {
                "latency_ms": 200,
                "throughput_rps": 1000,
                "availability_percent": 99.5
            },
            "scalability_requirements": {
                "auto_scaling": True,
                "max_instances": 50,
                "load_balancing": True
            },
            "security_requirements": {
                "encryption": True,
                "vpc": True,
                "waf": False,
                "monitoring": True
            },
            "integration_requirements": {
                "third_party_apis": [],
                "databases": ["postgresql"],
                "message_queues": []
            },
            **data.get("technical_requirements", {})
        }
        
        # Create and save Assessment document with complete data
        assessment = Assessment(
            user_id=user_id,
            title=data.get("title", "Test Assessment"),
            description=data.get("description", "Test Description"),
            business_requirements=business_requirements,
            technical_requirements=technical_requirements,
            status=AssessmentStatus.DRAFT,
            priority=Priority.MEDIUM,
            completion_percentage=0.0,
            metadata={
                "source": "api_simple", 
                "version": "1.0", 
                "tags": ["simple_creation"]
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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment_data: dict, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new infrastructure assessment.
    
    Creates a new assessment with the provided business and technical requirements.
    The assessment will be in DRAFT status and ready for AI agent analysis.
    """
    try:
        current_time = datetime.utcnow()
        
        # Extract data from the frontend payload
        title = assessment_data.get('title', 'Infrastructure Assessment')
        description = assessment_data.get('description', 'AI infrastructure assessment')
        business_goal = assessment_data.get('business_goal', 'Improve infrastructure')
        
        # Use enhanced business_requirements - preserve ALL fields from frontend
        frontend_business_req = assessment_data.get('business_requirements', {})
        
        # DEBUG: Log what we received
        logger.info(f"FRONTEND BUSINESS REQ KEYS: {list(frontend_business_req.keys())}")
        logger.info(f"COMPANY NAME RECEIVED: {frontend_business_req.get('company_name', 'MISSING')}")
        
        # Start with all frontend data and add defaults only for missing fields
        business_requirements = dict(frontend_business_req)  # Copy all fields from frontend
        
        # DEBUG: Log what we're storing
        logger.info(f"BUSINESS REQ AFTER COPY: {list(business_requirements.keys())}")
        logger.info(f"COMPANY NAME TO STORE: {business_requirements.get('company_name', 'MISSING')}")
        
        # Add default values only for missing core fields
        if 'company_size' not in business_requirements:
            business_requirements['company_size'] = 'startup'
        if 'industry' not in business_requirements:
            business_requirements['industry'] = 'technology'
        if 'business_goals' not in business_requirements:
            business_requirements['business_goals'] = [{
                "goal": business_goal,
                "priority": "high",
                "timeline_months": 6,
                "success_metrics": ["Performance improvement", "Cost optimization"]
            }]
        if 'growth_projection' not in business_requirements:
            business_requirements['growth_projection'] = {
                "current_users": 1000,
                "projected_users_6m": 2000,
                "projected_users_12m": 5000,
                "current_revenue": "500000",
                "projected_revenue_12m": "1000000"
            }
        if 'budget_constraints' not in business_requirements:
            business_requirements['budget_constraints'] = {
                "total_budget_range": "10k_50k",
                "monthly_budget_limit": 25000,
                "cost_optimization_priority": "high"
            }
        if 'team_structure' not in business_requirements:
            business_requirements['team_structure'] = {
                "total_developers": 5,
                "senior_developers": 2,
                "devops_engineers": 1,
                "data_engineers": 1,
                "cloud_expertise_level": 3,
                "kubernetes_expertise": 2,
                "database_expertise": 3
            }
        if 'compliance_requirements' not in business_requirements:
            business_requirements['compliance_requirements'] = ["none"]
        if 'project_timeline_months' not in business_requirements:
            business_requirements['project_timeline_months'] = 6
        if 'urgency_level' not in business_requirements:
            business_requirements['urgency_level'] = "medium"
        if 'current_pain_points' not in business_requirements:
            business_requirements['current_pain_points'] = ["Scalability challenges"]
        if 'success_criteria' not in business_requirements:
            business_requirements['success_criteria'] = ["Improved performance", "Cost reduction"]
        if 'multi_cloud_acceptable' not in business_requirements:
            business_requirements['multi_cloud_acceptable'] = True
        
        # Use enhanced technical_requirements - preserve ALL fields from frontend
        frontend_technical_req = assessment_data.get('technical_requirements', {})
        
        # Start with all frontend data and add defaults only for missing fields
        technical_requirements = dict(frontend_technical_req)  # Copy all fields from frontend
        
        # Add default values only for missing core fields
        if 'workload_types' not in technical_requirements:
            technical_requirements['workload_types'] = ["web_application", "api_service"]
        if 'performance_requirements' not in technical_requirements:
            technical_requirements['performance_requirements'] = {
                "api_response_time_ms": 200,
                "requests_per_second": 1000,
                "concurrent_users": 500,
                "uptime_percentage": 99.9
            }
        if 'scalability_requirements' not in technical_requirements:
            technical_requirements['scalability_requirements'] = {
                "current_data_size_gb": 100,
                "current_daily_transactions": 10000,
                "expected_data_growth_rate": "20% monthly",
                "peak_load_multiplier": 3.0,
                "auto_scaling_required": True,
                "global_distribution_required": False,
                "cdn_required": True,
                "planned_regions": ["us-east-1"]
            }
        if 'security_requirements' not in technical_requirements:
            technical_requirements['security_requirements'] = {
                "encryption_at_rest_required": True,
                "encryption_in_transit_required": True,
                "multi_factor_auth_required": False,
                "single_sign_on_required": False,
                "role_based_access_control": True,
                "vpc_isolation_required": True,
                "firewall_required": True,
                "ddos_protection_required": False,
                "security_monitoring_required": True,
                "audit_logging_required": False,
                "vulnerability_scanning_required": False,
                "data_loss_prevention_required": False,
                "backup_encryption_required": True
            }
        if 'integration_requirements' not in technical_requirements:
            technical_requirements['integration_requirements'] = {
                "existing_databases": [],
                "existing_apis": [],
                "legacy_systems": [],
                "payment_processors": [],
                "analytics_platforms": [],
                "marketing_tools": [],
                "rest_api_required": True,
                "graphql_api_required": False,
                "websocket_support_required": False,
                "real_time_sync_required": False,
                "batch_sync_acceptable": True
            }
        if 'preferred_programming_languages' not in technical_requirements:
            technical_requirements['preferred_programming_languages'] = ["Python", "JavaScript"]
        if 'monitoring_requirements' not in technical_requirements:
            technical_requirements['monitoring_requirements'] = ["Performance monitoring", "Error tracking"]
        if 'backup_requirements' not in technical_requirements:
            technical_requirements['backup_requirements'] = ["Daily backups", "Point-in-time recovery"]
        if 'ci_cd_requirements' not in technical_requirements:
            technical_requirements['ci_cd_requirements'] = ["Automated deployment", "Testing pipeline"]
        
        # Create and save Assessment document
        assessment = Assessment(
            user_id=str(current_user.id),
            title=title,
            description=description,
            business_requirements=business_requirements,
            technical_requirements=technical_requirements,
            business_goal=business_goal,
            status=AssessmentStatus.DRAFT,
            priority=Priority.MEDIUM,
            completion_percentage=0.0,
            source=assessment_data.get('source', 'web_form'),
            tags=assessment_data.get('tags', []),
            metadata={
                "source": assessment_data.get('source', 'web_form'), 
                "version": "1.0", 
                "tags": assessment_data.get('tags', [])
            },
            created_at=current_time,
            updated_at=current_time
        )
        
        # Save to database using insert to avoid revision tracking issues
        await assessment.insert()
        logger.info(f"Created assessment: {assessment.id}")
        
        # Clear any cached visualization data to ensure fresh dashboard display
        try:
            # Invalidate dashboard cache for real-time updates
            if hasattr(request.app, 'state') and hasattr(request.app.state, 'invalidate_dashboard_cache'):
                await request.app.state.invalidate_dashboard_cache()
                
            # Broadcast new assessment creation to all connected clients via WebSocket
            if hasattr(request.app, 'state') and hasattr(request.app.state, 'broadcast_dashboard_update'):
                await request.app.state.broadcast_dashboard_update({
                    "type": "new_assessment",
                    "assessment_id": str(assessment.id), 
                    "assessment_data": {
                        "id": str(assessment.id),
                        "title": assessment.title,
                        "status": assessment.status,
                        "created_at": assessment.created_at.isoformat(),
                        "user_id": assessment.user_id,
                        "priority": assessment.priority
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"New assessment '{assessment.title}' has been created"
                })
                logger.info(f"Broadcasted new assessment creation via WebSocket: {assessment.id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache or broadcast dashboard update: {e}")
        
        # Automatically start the workflow to generate recommendations and reports
        logger.info(f"Starting workflow for assessment: {assessment.id}")
        try:
            # Start workflow asynchronously (fire and forget)
            import asyncio
            asyncio.create_task(start_assessment_workflow(assessment, getattr(request.app, 'state', None)))
            
            # Update assessment status to indicate workflow started
            assessment.status = AssessmentStatus.IN_PROGRESS
            assessment.started_at = current_time
            assessment.workflow_id = f"workflow_{assessment.id}"  # Set workflow ID
            assessment.progress = {
                "current_step": "initializing_workflow", 
                "completed_steps": ["created"], 
                "total_steps": 5, 
                "progress_percentage": 10.0
            }
            await assessment.save()
            
            # Broadcast dashboard update for workflow start
            try:
                if hasattr(request.app, 'state') and hasattr(request.app.state, 'broadcast_dashboard_update'):
                    await request.app.state.broadcast_dashboard_update({
                        "type": "assessment_progress",
                        "assessment_id": str(assessment.id),
                        "assessment_data": {
                            "id": str(assessment.id),
                            "title": assessment.title,
                            "status": assessment.status,
                            "progress": assessment.progress,
                            "workflow_id": assessment.workflow_id
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Workflow started for assessment '{assessment.title}'"
                    })
            except Exception as e:
                logger.warning(f"Failed to broadcast dashboard update for workflow start: {e}")
                
            logger.info(f"Successfully started workflow for assessment: {assessment.id}")
        except Exception as workflow_error:
            logger.error(f"Failed to start workflow for assessment {assessment.id}: {workflow_error}")
            import traceback
            logger.error(f"Workflow error traceback: {traceback.format_exc()}")
            
            # Update assessment to show workflow start failed, but don't fail the creation
            assessment.status = AssessmentStatus.DRAFT  # Keep it in draft state
            assessment.progress = {
                "current_step": "workflow_failed", 
                "completed_steps": ["created"], 
                "total_steps": 5, 
                "progress_percentage": 5.0,
                "error": "Workflow initialization failed - assessment can be manually processed"
            }
            try:
                await assessment.save()
            except Exception as save_error:
                logger.error(f"Failed to save assessment after workflow error: {save_error}")
            
            # Don't fail assessment creation - allow manual processing
        
        # Return response
        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "description": assessment.description,
            "status": assessment.status,
            "priority": assessment.priority,
            "progress": assessment.progress,
            "workflow_id": assessment.workflow_id,
            "recommendations_generated": assessment.recommendations_generated,
            "reports_generated": assessment.reports_generated,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at,
            "started_at": assessment.started_at,
            "completed_at": assessment.completed_at
        }
        
    except Exception as e:
        logger.error(f"Failed to create assessment: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    current_user: User = Depends(require_permission(Permission.READ_ASSESSMENT))
):
    """
    Get a specific assessment by ID.
    
    Returns the complete assessment data including current status,
    progress, and any generated recommendations or reports.
    """
    try:
        # Retrieve from database using proper ObjectId
        try:
            assessment = await Assessment.get(PydanticObjectId(assessment_id))
        except Exception as e:
            logger.error(f"Error retrieving assessment {assessment_id}: {e}")
            assessment = None
            
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Assessment {assessment_id} not found"
            )
        
        # Check if user has access to this specific assessment
        if not AccessControl.user_can_access_resource(
            current_user, 
            assessment.user_id, 
            Permission.READ_ASSESSMENT,
            "assessment"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Access denied to this assessment"
            )
        
        logger.info(f"Retrieved assessment: {assessment_id}")
        
        # Convert MongoDB data types for Pydantic compatibility
        converted_business_req = convert_mongodb_data(assessment.business_requirements) if assessment.business_requirements else {}
        converted_technical_req = convert_mongodb_data(assessment.technical_requirements) if assessment.technical_requirements else {}
        
        # Handle progress data safely - remove invalid fields
        progress_data = assessment.progress or {}
        if isinstance(progress_data, dict):
            # Remove fields that cause validation errors
            progress_data = {k: v for k, v in progress_data.items() if k != "error"}
        
        # Return simplified response to avoid Pydantic validation issues
        # TODO: Fix the schema mismatch between storage and API response models
        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "description": assessment.description,
            "business_requirements": converted_business_req,
            "technical_requirements": converted_technical_req,
            "status": assessment.status,
            "priority": assessment.priority,
            "progress": progress_data,
            "workflow_id": assessment.workflow_id,
            "agent_states": assessment.agent_states or {},
            "recommendations_generated": assessment.recommendations_generated or False,
            "reports_generated": assessment.reports_generated or False,
            "metadata": assessment.metadata or {},
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "updated_at": assessment.updated_at.isoformat() if assessment.updated_at else None,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assessment: {str(e)}"
        )


@router.get("/{assessment_id}/test-mock", response_model=AssessmentResponse)
async def get_assessment_test_mock(assessment_id: str):
    """
    Get a mock assessment response for development testing only.
    DO NOT USE IN PRODUCTION - This returns hardcoded mock data.
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
    priority_filter: Optional[Priority] = Query(None, description="Filter by priority"),
    current_user: User = Depends(get_current_user)
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
        
        # Users can only see their own assessments
        query_filter["user_id"] = str(current_user.id)
        
        # Get total count and paginated results
        total = await Assessment.find(query_filter).count()
        assessments = await Assessment.find(query_filter).skip((page - 1) * limit).limit(limit).to_list()
        
        logger.info(f"Listed {len(assessments)} assessments - page: {page}, limit: {limit}, total: {total}")
        
        # Convert assessments to summaries
        assessment_summaries = []
        for assessment in assessments:
            try:
                # Extract basic info from business requirements if available
                company_size = "unknown"
                industry = "unknown"
                budget_range = "unknown"
                workload_types = []
                
                # Safely extract business requirements data
                if hasattr(assessment, 'business_requirements') and assessment.business_requirements:
                    bus_req = assessment.business_requirements
                    if isinstance(bus_req, dict):
                        company_size = bus_req.get("company_size", "unknown")
                        industry = bus_req.get("industry", "unknown")
                        
                        # Handle budget constraints
                        budget_constraints = bus_req.get("budget_constraints", {})
                        if isinstance(budget_constraints, dict):
                            budget_range = budget_constraints.get("total_budget_range", "unknown")
                
                # Safely extract technical requirements data
                if hasattr(assessment, 'technical_requirements') and assessment.technical_requirements:
                    tech_req = assessment.technical_requirements
                    if isinstance(tech_req, dict):
                        tech_workload_types = tech_req.get("workload_types", [])
                        if isinstance(tech_workload_types, list):
                            workload_types = tech_workload_types
                
                # Calculate proper progress percentage from database fields
                progress_pct = 0.0
                if hasattr(assessment, 'completion_percentage') and assessment.completion_percentage is not None:
                    progress_pct = float(assessment.completion_percentage)
                elif hasattr(assessment, 'progress_percentage') and assessment.progress_percentage is not None:
                    progress_pct = float(assessment.progress_percentage)
                elif assessment.progress and isinstance(assessment.progress, dict):
                    progress_pct = assessment.progress.get("progress_percentage", 0.0)
                
                # Override progress if status is completed
                if assessment.status == "completed":
                    progress_pct = 100.0
                
                assessment_summaries.append(AssessmentSummary(
                    id=str(assessment.id),
                    title=assessment.title or "Untitled Assessment",
                    status=assessment.status,
                    priority=assessment.priority,
                    progress_percentage=progress_pct,
                    created_at=assessment.created_at,
                    updated_at=assessment.updated_at,
                    company_size=company_size,
                    industry=industry,
                    budget_range=budget_range,
                    workload_types=workload_types,
                    recommendations_generated=bool(assessment.recommendations_generated),
                    reports_generated=bool(assessment.reports_generated)
                ))
            except Exception as e:
                logger.error(f"Error processing assessment {assessment.id}: {e}")
                # Add minimal assessment summary on error
                assessment_summaries.append(AssessmentSummary(
                    id=str(assessment.id),
                    title=getattr(assessment, 'title', 'Error Loading Assessment'),
                    status=getattr(assessment, 'status', 'unknown'),
                    priority=getattr(assessment, 'priority', 'medium'),
                    progress_percentage=0.0,
                    created_at=getattr(assessment, 'created_at', datetime.utcnow()),
                    updated_at=getattr(assessment, 'updated_at', datetime.utcnow()),
                    company_size="unknown",
                    industry="unknown",
                    budget_range="unknown",
                    workload_types=[],
                    recommendations_generated=False,
                    reports_generated=False
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
        # Get the assessment from database
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Update fields that are provided
        update_fields = {}
        if update_data.title is not None:
            update_fields["title"] = update_data.title
        if update_data.description is not None:
            update_fields["description"] = update_data.description
        if update_data.business_goal is not None:
            update_fields["business_goal"] = update_data.business_goal
        if update_data.priority is not None:
            update_fields["priority"] = update_data.priority
        if update_data.status is not None:
            update_fields["status"] = update_data.status
        if update_data.business_requirements is not None:
            update_fields["business_requirements"] = update_data.business_requirements.model_dump()
        if update_data.technical_requirements is not None:
            update_fields["technical_requirements"] = update_data.technical_requirements.model_dump()
        if update_data.tags is not None:
            update_fields["metadata.tags"] = update_data.tags
        
        # Add updated timestamp
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update the assessment
        await assessment.set(update_fields)
        
        logger.info(f"Updated assessment: {assessment_id}")
        
        # Return updated assessment
        updated_assessment = await Assessment.get(assessment_id)
        return AssessmentResponse(**updated_assessment.model_dump(), id=str(updated_assessment.id))
        
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
        # Get the assessment from database
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Delete associated data first
        # Delete recommendations
        try:
            from ..models.recommendation import Recommendation
            recommendations = await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()
            for rec in recommendations:
                await rec.delete()
        except Exception as e:
            logger.warning(f"Failed to delete recommendations for assessment {assessment_id}: {e}")
        
        # Delete reports  
        try:
            from ..models.report import Report
            reports = await Report.find(Report.assessment_id == assessment_id).to_list()
            for report in reports:
                await report.delete()
        except Exception as e:
            logger.warning(f"Failed to delete reports for assessment {assessment_id}: {e}")
        
        # Delete the assessment
        await assessment.delete()
        
        logger.info(f"Deleted assessment and associated data: {assessment_id}")
        
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
        # Get the assessment
        assessment = await Assessment.get(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {assessment_id} not found"
            )
        
        # Check if assessment is in a state that can be started
        if assessment.status == AssessmentStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment is already in progress"
            )
        
        if assessment.status == AssessmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment is already completed"
            )
        
        # Start the workflow manually
        logger.info(f"Manually starting analysis for assessment: {assessment_id}")
        
        try:
            # Update status to in progress
            assessment.status = AssessmentStatus.IN_PROGRESS
            assessment.started_at = datetime.utcnow()
            assessment.workflow_id = f"manual_workflow_{assessment.id}_{int(datetime.utcnow().timestamp())}"
            assessment.progress = {
                "current_step": "manual_start",
                "completed_steps": ["created"],
                "total_steps": 5,
                "progress_percentage": 10.0
            }
            await assessment.save()
            
            # Start the workflow asynchronously
            import asyncio
            asyncio.create_task(start_assessment_workflow(assessment, None))
            
            logger.info(f"Successfully started manual analysis for assessment: {assessment_id}")
            
            return AssessmentStatusUpdate(
                assessment_id=assessment_id,
                status=AssessmentStatus.IN_PROGRESS,
                progress_percentage=10.0,
                current_step="initializing_agents",
                message="AI agent analysis started successfully"
            )
            
        except Exception as workflow_error:
            logger.error(f"Failed to start workflow for assessment {assessment_id}: {workflow_error}")
            
            # Reset assessment to draft state
            assessment.status = AssessmentStatus.DRAFT
            assessment.progress = {
                "current_step": "manual_start_failed",
                "completed_steps": ["created"],
                "total_steps": 5,
                "progress_percentage": 0.0,
                "error": f"Manual workflow start failed: {str(workflow_error)}"
            }
            await assessment.save()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start assessment analysis: {str(workflow_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start analysis for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start assessment analysis"
        )


@router.get("/{assessment_id}/visualization-data")
async def get_assessment_visualization_data(
    assessment_id: str,
    current_user: User = Depends(require_permission(Permission.READ_ASSESSMENT))
):
    """Get visualization data for assessment charts and graphs."""
    try:
        # Get assessment using MongoDB/Beanie
        try:
            assessment = await Assessment.get(PydanticObjectId(assessment_id))
        except Exception:
            assessment = None
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Check access permissions
        if not AccessControl.user_can_access_resource(
            current_user,
            assessment.user_id,
            Permission.READ_ASSESSMENT,
            "assessment"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this assessment"
            )
        
        # Check if visualization data exists in metadata
        visualization_data = assessment.metadata.get("visualization_data")
        
        if not visualization_data:
            # Generate fallback visualization data based on assessment results
            visualization_data = await _generate_fallback_visualization_data(assessment)
        
        # Generate assessment results structure that the frontend expects
        assessment_results = [
            {
                "category": "Strategic Planning",
                "currentScore": 88,
                "targetScore": 90,
                "improvement": 2,
                "color": "#1f77b4"
            },
            {
                "category": "Technical Architecture",
                "currentScore": 85,
                "targetScore": 88,
                "improvement": 3,
                "color": "#ff7f0e"
            },
            {
                "category": "Security & Compliance", 
                "currentScore": 92,
                "targetScore": 95,
                "improvement": 3,
                "color": "#2ca02c"
            },
            {
                "category": "Cost Optimization",
                "currentScore": 81,
                "targetScore": 85,
                "improvement": 4,
                "color": "#d62728"
            },
            {
                "category": "Performance & Reliability",
                "currentScore": 87,
                "targetScore": 92,
                "improvement": 5,
                "color": "#9467bd"
            }
        ]
        
        # Add assessment_results to the data structure
        enhanced_data = dict(visualization_data)
        enhanced_data["assessment_results"] = assessment_results
        
        return {
            "assessment_id": assessment_id,
            "data": enhanced_data,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "available"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get visualization data for assessment {assessment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve visualization data")


async def _generate_fallback_visualization_data(assessment) -> Dict[str, Any]:
    """Generate fresh visualization data based on assessment state and recommendations."""
    try:
        # Get actual recommendations if available to calculate real scores
        real_recommendations = []
        try:
            real_recommendations = await Recommendation.find({"assessment_id": str(assessment.id)}).to_list()
            logger.info(f"Found {len(real_recommendations)} recommendations for assessment {assessment.id}")
        except Exception as e:
            logger.warning(f"Could not fetch recommendations for visualization: {e}")
        
        # Generate dynamic visualization based on actual assessment data
        categories = ["Strategic", "Technical", "Security", "Cost", "Performance"]
        chart_data = []
        
        # Calculate base scores using real assessment data
        base_score = 70 if assessment.status == AssessmentStatus.DRAFT else 80
        
        # If we have recommendations, use them to calculate more accurate scores
        if real_recommendations:
            avg_confidence = sum(rec.confidence_score for rec in real_recommendations) / len(real_recommendations)
            avg_alignment = sum(rec.alignment_score for rec in real_recommendations) / len(real_recommendations)
            base_score = int((avg_confidence + avg_alignment) * 50)  # Scale to 0-100
        
        for i, category in enumerate(categories):
            # Calculate category-specific scores based on assessment progression
            category_modifier = 0
            if assessment.status == AssessmentStatus.IN_PROGRESS:
                category_modifier = min(assessment.completion_percentage / 10, 10)
            elif assessment.status == AssessmentStatus.COMPLETED:
                category_modifier = 15
            
            current_score = base_score + (i * 2) + category_modifier + (hash(str(assessment.id) + category) % 10)
            current_score = min(max(current_score, 60), 95)  # Keep in reasonable range
            
            target_score = min(current_score + (20 - category_modifier), 95)
            improvement = target_score - current_score
            
            chart_data.append({
                "category": category,
                "currentScore": current_score,
                "targetScore": target_score,
                "improvement": improvement,
                "color": _get_category_color(category)
            })
        
        overall_score = sum(item["currentScore"] for item in chart_data) / len(chart_data)
        
        # Use real data whenever possible
        recommendations_count = len(real_recommendations) if real_recommendations else 0
        completion_status = assessment.status.value if hasattr(assessment.status, 'value') else str(assessment.status)
        
        return {
            "assessment_results": chart_data,
            "overall_score": round(overall_score, 1),
            "recommendations_count": recommendations_count,
            "completion_status": completion_status,
            "generated_at": datetime.utcnow().isoformat(),
            "fallback_data": len(real_recommendations) == 0,
            "assessment_progress": assessment.completion_percentage if hasattr(assessment, 'completion_percentage') else 0,
            "workflow_status": assessment.progress.get("current_step", "unknown") if assessment.progress else "unknown"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate fallback visualization data: {e}")
        # Return minimal fallback data
        return {
            "assessment_results": [
                {"category": "Overall", "currentScore": 70, "targetScore": 85, "improvement": 15, "color": "#1f77b4"}
            ],
            "overall_score": 70.0,
            "recommendations_count": 0,
            "completion_status": assessment.status.value if hasattr(assessment.status, 'value') else str(assessment.status),
            "generated_at": datetime.utcnow().isoformat(),
            "fallback_data": True,
            "assessment_progress": 0,
            "workflow_status": "unknown"
        }


def _get_category_color(category: str) -> str:
    """Get color for category visualization."""
    colors = {
        "Strategic": "#1f77b4",
        "Technical": "#ff7f0e", 
        "Security": "#2ca02c",
        "Cost": "#d62728",
        "Performance": "#9467bd"
    }
    return colors.get(category, "#7f7f7f")


async def fetch_relevant_cloud_services(assessment: Assessment) -> Dict[str, Any]:
    """
    Fetch relevant cloud services from the cloud services API based on assessment requirements.
    
    Args:
        assessment: The assessment containing user requirements
        
    Returns:
        Dict containing relevant services by category and provider
    """
    try:
        from ...api.endpoints.cloud_services import list_cloud_services
        from fastapi import Request
        
        # Create a mock request for the cloud services API
        class MockRequest:
            def __init__(self):
                pass
        
        mock_request = MockRequest()
        
        # Extract requirements to determine relevant service categories
        tech_reqs = assessment.technical_requirements or {}
        business_reqs = assessment.business_requirements or {}
        
        workload_types = tech_reqs.get('workload_types', [])
        budget = business_reqs.get('monthly_budget', 10000)
        
        # Determine relevant service categories based on workload types
        relevant_categories = set()
        if 'web_application' in workload_types:
            relevant_categories.update(['compute', 'networking', 'monitoring'])
        if 'api_service' in workload_types:
            relevant_categories.update(['compute', 'database', 'caching'])
        if 'data_processing' in workload_types:
            relevant_categories.update(['analytics', 'storage', 'compute'])
        if 'machine_learning' in workload_types:
            relevant_categories.update(['ml_ai', 'compute', 'storage'])
        
        # Add essential categories
        relevant_categories.update(['security', 'monitoring'])
        
        # Fetch services for each relevant category
        services_by_category = {}
        
        for category in relevant_categories:
            try:
                # Get services for this category
                response = await list_cloud_services(
                    provider=None,  # Get from all providers
                    category=category,
                    limit=5,  # Top 5 services per category
                    offset=0,
                    search=None
                )
                
                services_by_category[category] = response.get('services', [])
                logger.info(f"Fetched {len(services_by_category[category])} services for category: {category}")
                
            except Exception as e:
                logger.warning(f"Failed to fetch services for category {category}: {e}")
                services_by_category[category] = []
        
        return {
            'services_by_category': services_by_category,
            'total_categories': len(relevant_categories),
            'budget_constraint': budget
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch cloud services: {e}")
        return {
            'services_by_category': {},
            'total_categories': 0,
            'budget_constraint': 10000
        }


async def generate_llm_powered_recommendations(assessment: Assessment) -> List[Recommendation]:
    """
    Generate comprehensive recommendations using LLM with real cloud services data.
    
    Args:
        assessment: The assessment object containing user requirements
        
    Returns:
        List of AI-generated recommendations with real cloud services
    """
    from ...llm.manager import LLMManager
    from ...llm.interface import LLMRequest
    import json
    
    logger.info(f"Generating LLM-powered recommendations with cloud services API for assessment {assessment.id}")
    
    # Initialize LLM Manager
    llm_manager = LLMManager()
    
    # Fetch relevant cloud services
    logger.info("Fetching relevant cloud services from API...")
    cloud_services_data = await fetch_relevant_cloud_services(assessment)
    
    # Extract assessment data
    tech_reqs = assessment.technical_requirements or {}
    business_reqs = assessment.business_requirements or {}
    
    # Build comprehensive context with real services
    services_context = ""
    for category, services in cloud_services_data['services_by_category'].items():
        if services:
            services_context += f"\n{category.title()} Services Available:\n"
            for service in services[:3]:  # Top 3 per category
                services_context += f"  - {service.get('name', 'Unknown')}: {service.get('description', '')}\n"
                services_context += f"    Provider: {service.get('provider', 'Unknown')}\n"
                services_context += f"    Starting Price: ${service.get('pricing', {}).get('starting_price', 0)}/{service.get('pricing', {}).get('unit', 'month')}\n"
                services_context += f"    Features: {', '.join(service.get('features', [])[:3])}\n\n"
    
    assessment_context = f"""
COMPREHENSIVE INFRASTRUCTURE ASSESSMENT ANALYSIS

Business Context:
- Company: {getattr(assessment, 'title', 'Unknown')}
- Industry: {business_reqs.get('industry', 'Not specified')}
- Company Size: {business_reqs.get('company_size', 'Not specified')}
- Monthly Budget: ${business_reqs.get('monthly_budget', 'Not specified')}
- Project Timeline: {business_reqs.get('project_timeline_months', 'Not specified')} months
- Business Goals: {business_reqs.get('business_goals', [])}
- Compliance Requirements: {business_reqs.get('compliance_requirements', [])}

Technical Requirements:
- Workload Types: {tech_reqs.get('workload_types', [])}
- Architecture Preference: {tech_reqs.get('architecture_preference', 'Not specified')}
- Programming Languages: {tech_reqs.get('preferred_programming_languages', [])}
- Performance Requirements:
  * API Response Time: {tech_reqs.get('performance_requirements', {}).get('api_response_time_ms', 'Not specified')}ms
  * Concurrent Users: {tech_reqs.get('performance_requirements', {}).get('concurrent_users', 'Not specified')}
  * Uptime Required: {tech_reqs.get('performance_requirements', {}).get('uptime_percentage', 'Not specified')}%
  * Requests/Second: {tech_reqs.get('performance_requirements', {}).get('requests_per_second', 'Not specified')}

Scalability & Growth:
- Current Data Size: {tech_reqs.get('scalability_requirements', {}).get('current_data_size_gb', 'Not specified')}GB
- Expected Growth Rate: {tech_reqs.get('scalability_requirements', {}).get('expected_data_growth_rate', 'Not specified')}
- Daily Transactions: {tech_reqs.get('scalability_requirements', {}).get('current_daily_transactions', 'Not specified')}
- Auto-scaling Required: {tech_reqs.get('scalability_requirements', {}).get('auto_scaling_required', False)}
- Global Distribution: {tech_reqs.get('scalability_requirements', {}).get('global_distribution_required', False)}
- Peak Load Multiplier: {tech_reqs.get('scalability_requirements', {}).get('peak_load_multiplier', 'Not specified')}

Security Requirements:
- Encryption at Rest: {tech_reqs.get('security_requirements', {}).get('encryption_at_rest_required', False)}
- Encryption in Transit: {tech_reqs.get('security_requirements', {}).get('encryption_in_transit_required', False)}
- VPC Isolation: {tech_reqs.get('security_requirements', {}).get('vpc_isolation_required', False)}
- Multi-Factor Auth: {tech_reqs.get('security_requirements', {}).get('multi_factor_auth_required', False)}
- Audit Logging: {tech_reqs.get('security_requirements', {}).get('audit_logging_required', False)}

Integration Requirements:
- Existing Databases: {tech_reqs.get('integration_requirements', {}).get('existing_databases', [])}
- Legacy Systems: {tech_reqs.get('integration_requirements', {}).get('legacy_systems', [])}
- REST API Required: {tech_reqs.get('integration_requirements', {}).get('rest_api_required', False)}
- Real-time Sync: {tech_reqs.get('integration_requirements', {}).get('real_time_sync_required', False)}

AVAILABLE CLOUD SERVICES (from API):
{services_context}

Service Preferences:
- Managed Services Preference: {tech_reqs.get('managed_services_preference', 'medium')}
- Open Source Preference: {tech_reqs.get('open_source_preference', 'medium')}
- Containerization Preference: {tech_reqs.get('containerization_preference', 'medium')}
"""

    prompt = f"""You are a senior multi-cloud architect with deep expertise in AWS, Microsoft Azure, Google Cloud Platform, Alibaba Cloud, and IBM Cloud. Based on the comprehensive assessment requirements and available cloud services, generate 4-6 specific, actionable infrastructure recommendations.

{assessment_context}

MULTI-CLOUD STRATEGY INSTRUCTIONS:
1. MUST include services from at least 3 different cloud providers (AWS, Azure, GCP minimum)
2. Use ONLY the cloud services listed in the "AVAILABLE CLOUD SERVICES" section above
3. Design for multi-cloud redundancy and avoid vendor lock-in
4. Consider cross-cloud networking and data replication requirements
5. Provide cost comparisons between cloud providers for similar services
6. Include disaster recovery and failover strategies across clouds
7. Focus on cloud-native and containerized solutions for portability
8. Consider regional availability and compliance requirements per cloud
9. Recommend hybrid and multi-cloud orchestration tools (Terraform, Kubernetes)
10. Include security considerations for cross-cloud identity and access management

For each recommendation, provide a JSON object with this EXACT structure:
{{
    "agent_name": "cloud_architect_agent_1",
    "title": "Specific Infrastructure Component Recommendation",
    "summary": "Clear 2-3 sentence summary explaining what this recommendation addresses and why it's important for this specific use case.",
    "confidence_level": "high|medium|low",
    "confidence_score": 85,
    "business_alignment": 90,
    "recommended_services": [
        {{
            "service_name": "Exact Service Name from Available Services",
            "provider": "aws|azure|gcp",
            "service_category": "compute|storage|database|networking|security|monitoring|analytics",
            "estimated_monthly_cost": "250.00",
            "cost_model": "pay_per_use|subscription|usage_based",
            "configuration": {{"instances": 2, "size": "medium", "region": "us-east-1"}},
            "reasons": [
                "Meets the {tech_reqs.get('performance_requirements', {}).get('api_response_time_ms', 200)}ms response time requirement",
                "Supports {tech_reqs.get('performance_requirements', {}).get('concurrent_users', 500)} concurrent users",
                "Fits within ${business_reqs.get('monthly_budget', 10000)} monthly budget"
            ],
            "alternatives": ["Alternative Service 1", "Alternative Service 2"],
            "setup_complexity": "low|medium|high",
            "implementation_time_hours": 24
        }}
    ],
    "cost_estimates": {{
        "total_monthly": 500,
        "annual_projection": 6000,
        "potential_savings": 2400
    }},
    "total_estimated_monthly_cost": "500.00",
    "implementation_steps": [
        "Step 1: Specific action",
        "Step 2: Specific action",
        "Step 3: Specific action"
    ],
    "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
    "risks_and_considerations": ["Risk 1 with mitigation", "Risk 2 with mitigation"],
    "business_impact": "high|medium|low",
    "alignment_score": 90,
    "tags": ["scalability", "cost-optimization", "performance"],
    "priority": "high|medium|low",
    "category": "compute|storage|networking|security|analytics"
}}

Generate recommendations that specifically address:
1. The workload types: {tech_reqs.get('workload_types', [])}
2. Performance requirements: {tech_reqs.get('performance_requirements', {}).get('api_response_time_ms', 'N/A')}ms response time, {tech_reqs.get('performance_requirements', {}).get('concurrent_users', 'N/A')} users
3. Budget constraint: ${business_reqs.get('monthly_budget', 10000)}/month
4. Scalability needs: {tech_reqs.get('scalability_requirements', {}).get('expected_data_growth_rate', 'stable growth')}

Return ONLY a valid JSON array of recommendations, no additional text or markdown."""

    try:
        # Make LLM request
        llm_request = LLMRequest(
            prompt=prompt,
            model="gpt-3.5-turbo",  # Use GPT-3.5-turbo for compatibility
            max_tokens=6000,
            temperature=0.1  # Very low temperature for consistent, accurate recommendations
        )
        
        logger.info("Sending comprehensive recommendation request to LLM...")
        llm_response = await llm_manager.generate_response(llm_request)
        
        if not llm_response or not llm_response.content:
            raise Exception("Empty response from LLM")
            
        logger.info(f"LLM Response received: {len(llm_response.content)} characters")
        
        # Parse JSON response with better error handling
        try:
            content = llm_response.content.strip()
            
            # Handle markdown-wrapped JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            
            recommendations_data = json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {llm_response.content}")
            return []
        
        # Convert to Recommendation objects
        recommendations = []
        for i, rec_data in enumerate(recommendations_data):
            try:
                # Parse service recommendations
                service_recommendations = []
                for service_data in rec_data.get("recommended_services", []):
                    service_rec = ServiceRecommendation(
                        service_name=service_data["service_name"],
                        provider=CloudProvider(service_data["provider"]),
                        service_category=service_data["service_category"],
                        estimated_monthly_cost=Decimal(str(service_data["estimated_monthly_cost"])),
                        cost_model=service_data["cost_model"],
                        configuration=service_data.get("configuration", {}),
                        reasons=service_data.get("reasons", []),
                        alternatives=service_data.get("alternatives", []),
                        setup_complexity=service_data.get("setup_complexity", "medium"),
                        implementation_time_hours=service_data.get("implementation_time_hours", 20)
                    )
                    service_recommendations.append(service_rec)
                
                # Create Recommendation object
                recommendation = Recommendation(
                    assessment_id=str(assessment.id),
                    user_id=assessment.user_id,
                    agent_name=rec_data.get("agent_name", f"llm_powered_agent_{i+1}"),
                    title=rec_data["title"],
                    summary=rec_data["summary"],
                    confidence_level=RecommendationConfidence(rec_data.get("confidence_level", "medium")),
                    confidence_score=rec_data.get("confidence_score", 75),
                    business_alignment=rec_data.get("business_alignment", 75),
                    recommended_services=service_recommendations,
                    cost_estimates=rec_data.get("cost_estimates", {}),
                    total_estimated_monthly_cost=Decimal(str(rec_data.get("total_estimated_monthly_cost", "0.00"))),
                    implementation_steps=rec_data.get("implementation_steps", []),
                    prerequisites=rec_data.get("prerequisites", []),
                    risks_and_considerations=rec_data.get("risks_and_considerations", []),
                    business_impact=rec_data.get("business_impact", "medium"),
                    alignment_score=rec_data.get("alignment_score", 75),
                    tags=rec_data.get("tags", []),
                    priority=Priority(rec_data.get("priority", "medium")),
                    category=rec_data.get("category", "technical")
                )
                
                recommendations.append(recommendation)
                
            except Exception as e:
                logger.error(f"Failed to parse recommendation {i}: {e}")
                logger.error(f"Recommendation data: {rec_data}")
                continue
        
        logger.info(f"Generated {len(recommendations)} LLM-powered recommendations with cloud services API for assessment {assessment.id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to generate LLM-powered recommendations: {e}")
        return []