"""
Conversation models for Infra Mind chatbot system.

Provides database models for chat conversations, messages, and history management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, BaseModel
import uuid


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Conversation status types."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class ConversationContext(str, Enum):
    """Conversation context types."""
    GENERAL_INQUIRY = "general_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    ASSESSMENT_HELP = "assessment_help"
    PLATFORM_GUIDANCE = "platform_guidance"
    BILLING_SUPPORT = "billing_support"
    REPORT_ANALYSIS = "report_analysis"
    DECISION_MAKING = "decision_making"


class MessageMetadata(BaseModel):
    """Metadata for chat messages."""
    intent: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[str] = None
    knowledge_source: Optional[str] = None
    response_time: Optional[float] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    escalation_triggered: bool = False


class ChatMessage(BaseModel):
    """Individual chat message model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[MessageMetadata] = None
    edited: bool = False
    edited_at: Optional[datetime] = None


class Conversation(Document):
    """
    Main conversation document for storing chat sessions.
    
    Stores complete conversation threads with metadata, participants,
    and session information for the chatbot system.
    """
    
    # Basic conversation info
    title: str = Field(description="Conversation title or summary")
    user_id: str = Indexed()
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Conversation metadata
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE)
    context: ConversationContext = Field(default=ConversationContext.GENERAL_INQUIRY)
    
    # Messages
    messages: List[ChatMessage] = Field(default_factory=list)
    message_count: int = Field(default=0)
    
    # Conversation analysis
    primary_intent: Optional[str] = None
    topics_discussed: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    satisfaction_rating: Optional[int] = None
    
    # Related data
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None
    related_documents: List[str] = Field(default_factory=list)
    
    # Support escalation
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    support_ticket_id: Optional[str] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # AI/LLM usage tracking
    total_tokens_used: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    
    class Settings:
        """Beanie document settings."""
        name = "conversations"
        indexes = [
            [("user_id", 1), ("started_at", -1)],  # User conversations by date
            [("status", 1), ("last_activity", -1)],  # Active conversations
            [("context", 1), ("started_at", -1)],  # By context type
            [("assessment_id", 1)],  # Related to assessments
            [("report_id", 1)],  # Related to reports
            [("escalated", 1), ("escalated_at", -1)],  # Escalated conversations
        ]
    
    def add_message(
        self, 
        role: MessageRole, 
        content: str, 
        metadata: Optional[MessageMetadata] = None
    ) -> ChatMessage:
        """
        Add a new message to the conversation.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata
        )
        
        self.messages.append(message)
        self.message_count = len(self.messages)
        self.last_activity = datetime.utcnow()
        
        # Update token usage if provided
        if metadata and metadata.tokens_used:
            self.total_tokens_used += metadata.tokens_used
        
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """
        Get recent messages from the conversation.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent ChatMessages
        """
        return self.messages[-limit:] if self.messages else []
    
    def get_message_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Message ID to find
            
        Returns:
            ChatMessage if found, None otherwise
        """
        for message in self.messages:
            if message.id == message_id:
                return message
        return None
    
    def update_context(self, new_context: ConversationContext) -> None:
        """
        Update conversation context.
        
        Args:
            new_context: New conversation context
        """
        self.context = new_context
        self.last_activity = datetime.utcnow()
    
    def escalate_conversation(self, support_ticket_id: str) -> None:
        """
        Mark conversation as escalated to human support.
        
        Args:
            support_ticket_id: ID of the created support ticket
        """
        self.escalated = True
        self.escalated_at = datetime.utcnow()
        self.support_ticket_id = support_ticket_id
        self.status = ConversationStatus.ESCALATED
        self.last_activity = datetime.utcnow()
    
    def end_conversation(self, satisfaction_rating: Optional[int] = None) -> None:
        """
        End the conversation.
        
        Args:
            satisfaction_rating: Optional user satisfaction rating (1-5)
        """
        self.ended_at = datetime.utcnow()
        self.status = ConversationStatus.RESOLVED
        self.last_activity = datetime.utcnow()
        
        if satisfaction_rating:
            self.satisfaction_rating = satisfaction_rating
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation.
        
        Returns:
            Dictionary with conversation summary
        """
        duration = None
        if self.ended_at:
            duration = (self.ended_at - self.started_at).total_seconds()
        
        return {
            "id": str(self.id),
            "title": self.title,
            "user_id": self.user_id,
            "status": self.status.value,
            "context": self.context.value,
            "message_count": self.message_count,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "ended_at": self.ended_at,
            "duration_seconds": duration,
            "escalated": self.escalated,
            "assessment_id": self.assessment_id,
            "report_id": self.report_id,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "satisfaction_rating": self.satisfaction_rating,
            "topics_discussed": self.topics_discussed
        }


class ConversationSummary(Document):
    """
    Conversation summary for analytics and search.
    
    Stores processed summaries of conversations for quick access
    and analytics without loading full conversation data.
    """
    
    conversation_id: str = Indexed(unique=True)
    user_id: str = Indexed()
    
    # Summary data
    title: str
    summary: str
    key_topics: List[str] = Field(default_factory=list)
    resolution_status: str
    
    # Metrics
    duration_minutes: Optional[float] = None
    message_count: int
    user_satisfaction: Optional[int] = None
    
    # Context
    context: ConversationContext
    primary_intent: Optional[str] = None
    
    # Related entities
    assessment_id: Optional[str] = None
    report_id: Optional[str] = None
    
    # Timestamps
    conversation_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "conversation_summaries"
        indexes = [
            [("user_id", 1), ("conversation_date", -1)],
            [("context", 1), ("conversation_date", -1)],
            [("key_topics", 1)],
            [("assessment_id", 1)],
            [("report_id", 1)],
        ]


class ChatAnalytics(Document):
    """
    Analytics data for chat system.
    
    Stores aggregated analytics data for monitoring
    chatbot performance and user engagement.
    """
    
    # Time period
    date: datetime = Indexed()
    period_type: str  # daily, weekly, monthly
    
    # User metrics
    total_conversations: int = 0
    unique_users: int = 0
    returning_users: int = 0
    
    # Conversation metrics
    avg_conversation_length: float = 0.0
    avg_messages_per_conversation: float = 0.0
    total_messages: int = 0
    
    # Context distribution
    context_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Resolution metrics
    escalation_rate: float = 0.0
    resolution_rate: float = 0.0
    avg_satisfaction_score: Optional[float] = None
    
    # AI/LLM metrics
    total_tokens_used: int = 0
    total_ai_cost: float = 0.0
    avg_response_time: float = 0.0
    
    # Popular topics
    top_topics: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "chat_analytics"
        indexes = [
            [("date", -1), ("period_type", 1)],
            [("period_type", 1), ("date", -1)],
        ]