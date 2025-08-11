"""
Chat API endpoints for Infra Mind chatbot system.

Provides REST API endpoints for managing conversations, sending messages,
and accessing chat history with full ChatGPT-like functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uuid

from ...models.conversation import (
    Conversation, ConversationSummary, ChatAnalytics,
    MessageRole, ConversationStatus, ConversationContext,
    ChatMessage, MessageMetadata
)
from ...models.user import User
from ...models.assessment import Assessment
from ...models.report import Report
from ...agents.chatbot_agent import ChatbotAgent
from ...agents.base import AgentConfig, AgentRole
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class SimpleChatRequest(BaseModel):
    """Simple chat request without authentication."""
    message: str = Field(description="User message", min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")


class SimpleChatResponse(BaseModel):
    """Simple chat response."""
    response: str = Field(description="AI assistant response")
    session_id: str = Field(description="Session identifier for conversation continuity")
    timestamp: datetime = Field(description="Response timestamp")


# Simple Chat Endpoints (No Authentication Required)

@router.post("/simple", response_model=SimpleChatResponse)
async def simple_chat(request: SimpleChatRequest):
    """
    Simple chat endpoint without authentication using LLM.
    
    Provides dynamic AI assistant functionality powered by LLM without requiring user authentication.
    Perfect for testing and public-facing chat interfaces.
    """
    try:
        from infra_mind.llm.manager import LLMManager
        from infra_mind.llm.interface import LLMRequest
        
        # Generate or use provided session ID
        session_id = request.session_id or f"session_{uuid.uuid4()}"
        
        # Initialize LLM manager
        llm_manager = LLMManager()
        
        # Create LLM request with infrastructure-focused system prompt
        llm_request = LLMRequest(
            prompt=request.message,
            model="gpt-3.5-turbo",  # Use standard OpenAI model
            system_prompt="""You are an expert AI infrastructure consultant and cloud architect with deep expertise in:

• Cloud platforms (AWS, Azure, GCP)
• Infrastructure as Code (Terraform, CloudFormation, ARM templates)
• Container orchestration (Kubernetes, Docker, EKS, AKS, GKE)
• DevOps and CI/CD pipelines
• Database technologies (SQL, NoSQL, data warehousing)
• Monitoring, logging, and observability
• Security best practices and compliance
• Cost optimization strategies
• Network architecture and design
• Serverless and microservices architectures

You provide practical, actionable advice with specific recommendations, best practices, and real-world examples. Always consider scalability, security, cost-effectiveness, and operational simplicity in your responses.

Keep responses concise but comprehensive, focusing on practical implementation details when appropriate.""",
            max_tokens=1000,
            temperature=0.7,
            context={
                "agent_name": "infrastructure_assistant",
                "session_id": session_id,
                "domain": "cloud_infrastructure"
            }
        )
        
        # Generate response using LLM
        llm_response = await llm_manager.generate_response(
            llm_request,
            validate_response=True,
            agent_name="infrastructure_assistant"
        )
        
        response = llm_response.content
        
        return SimpleChatResponse(
            response=response,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Simple chat error: {str(e)}")
        return SimpleChatResponse(
            response="I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
            session_id=request.session_id or f"session_{uuid.uuid4()}",
            timestamp=datetime.utcnow()
        )


# Authenticated Chat Endpoints

class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    content: str = Field(description="Message content", min_length=1, max_length=4000)
    context: Optional[ConversationContext] = None
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None


class MessageResponse(BaseModel):
    """Response model for chat messages."""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response model for conversations."""
    id: str
    title: str
    status: ConversationStatus
    context: ConversationContext
    message_count: int
    started_at: datetime
    last_activity: datetime
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None
    escalated: bool = False


class ConversationDetailResponse(BaseModel):
    """Detailed response model for conversations with messages."""
    id: str
    title: str
    status: ConversationStatus
    context: ConversationContext
    messages: List[MessageResponse]
    message_count: int
    started_at: datetime
    last_activity: datetime
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None
    escalated: bool = False
    total_tokens_used: int = 0
    topics_discussed: List[str] = []


class StartConversationRequest(BaseModel):
    """Request model for starting a new conversation."""
    title: Optional[str] = Field(default="New Chat", description="Conversation title")
    context: ConversationContext = Field(default=ConversationContext.GENERAL_INQUIRY)
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None
    initial_message: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response model for conversation lists."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ChatAnalyticsResponse(BaseModel):
    """Response model for chat analytics."""
    total_conversations: int
    total_messages: int
    avg_conversation_length: float
    escalation_rate: float
    satisfaction_score: Optional[float] = None
    top_contexts: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# Global chatbot agent instance
_chatbot_agent: Optional[ChatbotAgent] = None


async def get_chatbot_agent() -> ChatbotAgent:
    """Get or create the chatbot agent instance."""
    global _chatbot_agent
    
    if _chatbot_agent is None:
        # Create chatbot agent configuration
        config = AgentConfig(
            name="main_chatbot",
            role=AgentRole.CHATBOT,
            custom_config={
                "max_conversation_turns": 50,
                "escalation_threshold": 3,
                "enable_faq_integration": True,
                "enable_context_memory": True,
                "enable_real_time_search": True,
                "search_cache_ttl": 3600
            }
        )
        
        _chatbot_agent = ChatbotAgent(config)
        await _chatbot_agent._execute_main_logic()  # Initialize the agent
        
        logger.info("Chatbot agent initialized")
    
    return _chatbot_agent


# API Endpoints

@router.post("/conversations", response_model=ConversationDetailResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a new conversation.
    
    Creates a new conversation session and optionally sends an initial message.
    """
    try:
        # Create new conversation
        conversation = Conversation(
            title=request.title or "New Chat",
            user_id=str(current_user.id),
            context=request.context,
            assessment_id=request.assessment_id,
            report_id=request.report_id
        )
        
        # Save conversation to database
        await conversation.insert()
        
        # If initial message provided, process it
        if request.initial_message:
            # Get chatbot agent
            chatbot = await get_chatbot_agent()
            
            # Add user message
            user_message = conversation.add_message(
                role=MessageRole.USER,
                content=request.initial_message
            )
            
            # Generate bot response
            bot_response = await chatbot.handle_message(
                message=request.initial_message,
                user_id=str(current_user.id),
                conversation_id=str(conversation.id),
                context={
                    "assessment_id": request.assessment_id,
                    "report_id": request.report_id,
                    "conversation_context": request.context.value
                }
            )
            
            # Add bot response
            bot_metadata = MessageMetadata(
                intent=bot_response.get("intent"),
                confidence=bot_response.get("confidence"),
                context=bot_response.get("context"),
                knowledge_source=bot_response.get("metadata", {}).get("knowledge_source"),
                response_time=bot_response.get("metadata", {}).get("response_time"),
                escalation_triggered=bot_response.get("requires_escalation", False)
            )
            
            conversation.add_message(
                role=MessageRole.ASSISTANT,
                content=bot_response["content"],
                metadata=bot_metadata
            )
            
            # Update conversation context if needed
            if bot_response.get("context") and bot_response["context"] != request.context.value:
                try:
                    new_context = ConversationContext(bot_response["context"])
                    conversation.update_context(new_context)
                except ValueError:
                    pass  # Keep original context if invalid
        
        # Save updated conversation
        await conversation.save()
        
        logger.info(f"Started conversation {conversation.id} for user {current_user.id}")
        
        # Convert messages to response format
        message_responses = [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata.dict() if msg.metadata else None
            )
            for msg in conversation.messages
        ]
        
        return ConversationDetailResponse(
            id=str(conversation.id),
            title=conversation.title,
            status=conversation.status,
            context=conversation.context,
            messages=message_responses,
            message_count=conversation.message_count,
            started_at=conversation.started_at,
            last_activity=conversation.last_activity,
            assessment_id=conversation.assessment_id,
            report_id=conversation.report_id,
            escalated=conversation.escalated,
            total_tokens_used=conversation.total_tokens_used,
            topics_discussed=conversation.topics_discussed
        )
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start conversation"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    http_request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ConversationStatus] = Query(None, description="Filter by status"),
    context_filter: Optional[ConversationContext] = Query(None, description="Filter by context"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's conversations with pagination and filtering.
    
    Returns a paginated list of conversations for the current user.
    """
    try:
        # Build query filters
        query_filters = {"user_id": str(current_user.id)}
        
        if status_filter:
            query_filters["status"] = status_filter
        if context_filter:
            query_filters["context"] = context_filter
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get conversations with pagination
        conversations_docs = await Conversation.find(query_filters)\
            .sort([("last_activity", -1)])\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Get total count
        total_count = await Conversation.find(query_filters).count()
        
        # Convert to response format
        conversations = [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                status=conv.status,
                context=conv.context,
                message_count=conv.message_count,
                started_at=conv.started_at,
                last_activity=conv.last_activity,
                assessment_id=conv.assessment_id,
                report_id=conv.report_id,
                escalated=conv.escalated
            )
            for conv in conversations_docs
        ]
        
        has_more = (skip + limit) < total_count
        
        logger.debug(f"Retrieved {len(conversations)} conversations for user {current_user.id}")
        
        return ConversationListResponse(
            conversations=conversations,
            total=total_count,
            page=page,
            limit=limit,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation with all messages.
    
    Returns complete conversation details including message history.
    """
    try:
        # Get conversation from database
        conversation = await Conversation.get(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check ownership
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert messages to response format
        message_responses = [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata.dict() if msg.metadata else None
            )
            for msg in conversation.messages
        ]
        
        return ConversationDetailResponse(
            id=str(conversation.id),
            title=conversation.title,
            status=conversation.status,
            context=conversation.context,
            messages=message_responses,
            message_count=conversation.message_count,
            started_at=conversation.started_at,
            last_activity=conversation.last_activity,
            assessment_id=conversation.assessment_id,
            report_id=conversation.report_id,
            escalated=conversation.escalated,
            total_tokens_used=conversation.total_tokens_used,
            topics_discussed=conversation.topics_discussed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message in a conversation.
    
    Processes the user message and generates an AI response.
    """
    try:
        # Get conversation from database
        conversation = await Conversation.get(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check ownership
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Add user message
        user_message = conversation.add_message(
            role=MessageRole.USER,
            content=request.content
        )
        
        # Update context if provided
        if request.context:
            conversation.update_context(request.context)
        
        # Update related IDs if provided
        if request.assessment_id:
            conversation.assessment_id = request.assessment_id
        if request.report_id:
            conversation.report_id = request.report_id
        
        # Save conversation with user message
        await conversation.save()
        
        # Get chatbot agent
        chatbot = await get_chatbot_agent()
        
        # Prepare context for bot
        bot_context = {
            "assessment_id": request.assessment_id or conversation.assessment_id,
            "report_id": request.report_id or conversation.report_id,
            "conversation_context": conversation.context.value
        }
        
        # Load report data if available for context
        if bot_context.get("report_id"):
            try:
                report = await Report.get(bot_context["report_id"])
                if report:
                    bot_context["report_data"] = {
                        "title": report.title,
                        "key_findings": report.key_findings,
                        "recommendations": report.recommendations[:3],  # Top 3 recommendations
                        "compliance_score": report.compliance_score,
                        "estimated_savings": report.estimated_savings
                    }
            except Exception as e:
                logger.warning(f"Failed to load report data: {str(e)}")
        
        # Load assessment data if available for context
        if bot_context.get("assessment_id"):
            try:
                assessment = await Assessment.get(bot_context["assessment_id"])
                if assessment:
                    bot_context["assessment_data"] = {
                        "title": assessment.title,
                        "status": assessment.status,
                        "business_goals": assessment.business_requirements.business_goals,
                        "cloud_providers": getattr(assessment.technical_requirements, 'preferred_cloud_providers', [])
                    }
            except Exception as e:
                logger.warning(f"Failed to load assessment data: {str(e)}")
        
        # Generate bot response
        bot_response = await chatbot.handle_message(
            message=request.content,
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            context=bot_context
        )
        
        # Add bot response to conversation
        bot_metadata = MessageMetadata(
            intent=bot_response.get("intent"),
            confidence=bot_response.get("confidence"),
            context=bot_response.get("context"),
            knowledge_source=bot_response.get("metadata", {}).get("knowledge_source"),
            response_time=bot_response.get("metadata", {}).get("response_time"),
            escalation_triggered=bot_response.get("requires_escalation", False)
        )
        
        bot_message = conversation.add_message(
            role=MessageRole.ASSISTANT,
            content=bot_response["content"],
            metadata=bot_metadata
        )
        
        # Handle escalation if needed
        if bot_response.get("requires_escalation"):
            conversation.escalate_conversation(
                bot_response.get("ticket_id", f"CHAT-{uuid.uuid4().hex[:8].upper()}")
            )
        
        # Save updated conversation
        await conversation.save()
        
        # Schedule background tasks
        background_tasks.add_task(
            _update_conversation_analytics,
            conversation_id,
            str(current_user.id)
        )
        
        logger.info(f"Processed message in conversation {conversation_id}")
        
        # Return the bot's response
        return MessageResponse(
            id=bot_message.id,
            role=bot_message.role,
            content=bot_message.content,
            timestamp=bot_message.timestamp,
            metadata=bot_message.metadata.dict() if bot_message.metadata else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


class UpdateTitleRequest(BaseModel):
    title: str = Field(description="New conversation title")

@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: UpdateTitleRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """Update conversation title."""
    try:
        conversation = await Conversation.get(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        conversation.title = request.title
        conversation.last_activity = datetime.utcnow()
        await conversation.save()
        
        return {"message": "Title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation title: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update title"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation."""
    try:
        conversation = await Conversation.get(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        await conversation.delete()
        
        logger.info(f"Deleted conversation {conversation_id}")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: str,
    http_request: Request,
    satisfaction_rating: Optional[int] = Query(None, ge=1, le=5, description="Satisfaction rating"),
    current_user: User = Depends(get_current_user)
):
    """End a conversation with optional satisfaction rating."""
    try:
        conversation = await Conversation.get(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if conversation.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        conversation.end_conversation(satisfaction_rating)
        await conversation.save()
        
        return {"message": "Conversation ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end conversation"
        )


@router.get("/analytics", response_model=ChatAnalyticsResponse)
async def get_chat_analytics(
    http_request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get chat analytics for the current user."""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's conversations in date range
        conversations = await Conversation.find({
            "user_id": str(current_user.id),
            "started_at": {"$gte": start_date, "$lte": end_date}
        }).to_list()
        
        if not conversations:
            return ChatAnalyticsResponse(
                total_conversations=0,
                total_messages=0,
                avg_conversation_length=0.0,
                escalation_rate=0.0,
                top_contexts=[],
                recent_activity=[]
            )
        
        # Calculate analytics
        total_conversations = len(conversations)
        total_messages = sum(conv.message_count for conv in conversations)
        escalated_count = sum(1 for conv in conversations if conv.escalated)
        
        # Calculate average conversation length
        completed_conversations = [conv for conv in conversations if conv.ended_at]
        avg_length = 0.0
        if completed_conversations:
            total_duration = sum(
                (conv.ended_at - conv.started_at).total_seconds() / 60  # in minutes
                for conv in completed_conversations
            )
            avg_length = total_duration / len(completed_conversations)
        
        # Calculate escalation rate
        escalation_rate = (escalated_count / total_conversations) * 100 if total_conversations > 0 else 0.0
        
        # Calculate satisfaction score
        rated_conversations = [conv for conv in conversations if conv.satisfaction_rating]
        satisfaction_score = None
        if rated_conversations:
            satisfaction_score = sum(conv.satisfaction_rating for conv in rated_conversations) / len(rated_conversations)
        
        # Context distribution
        context_counts = {}
        for conv in conversations:
            context = conv.context.value
            context_counts[context] = context_counts.get(context, 0) + 1
        
        top_contexts = [
            {"context": context, "count": count}
            for context, count in sorted(context_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Recent activity (last 7 days)
        recent_date = end_date - timedelta(days=7)
        recent_conversations = [conv for conv in conversations if conv.started_at >= recent_date]
        recent_activity = []
        
        for conv in recent_conversations[-10:]:  # Last 10 recent conversations
            recent_activity.append({
                "date": conv.started_at.isoformat(),
                "title": conv.title,
                "context": conv.context.value,
                "message_count": conv.message_count,
                "escalated": conv.escalated
            })
        
        return ChatAnalyticsResponse(
            total_conversations=total_conversations,
            total_messages=total_messages,
            avg_conversation_length=avg_length,
            escalation_rate=escalation_rate,
            satisfaction_score=satisfaction_score,
            top_contexts=top_contexts,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Failed to get chat analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


# Background task functions

async def _update_conversation_analytics(conversation_id: str, user_id: str):
    """Background task to update conversation analytics."""
    try:
        # This would update daily/weekly/monthly analytics
        # For now, just log the activity
        logger.debug(f"Updated analytics for conversation {conversation_id}")
        
    except Exception as e:
        logger.warning(f"Failed to update conversation analytics: {str(e)}")


# Health check endpoint

@router.get("/health")
async def chat_health_check():
    """Health check for chat system."""
    try:
        # Check if chatbot agent is available
        chatbot = await get_chatbot_agent()
        
        # Test database connectivity by counting conversations
        conversation_count = await Conversation.count()
        
        return {
            "status": "healthy",
            "chatbot_ready": chatbot is not None,
            "total_conversations": conversation_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }