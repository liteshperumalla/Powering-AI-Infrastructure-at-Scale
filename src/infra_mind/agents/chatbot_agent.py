"""
Chatbot Agent for Infra Mind.

Provides intelligent conversational support for users, including customer service,
FAQ responses, and general platform guidance using real LLM providers.
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid

from .base import BaseAgent, AgentConfig, AgentRole
from .web_search import WebSearchClient, get_web_search_client
from ..models.user import User
from ..models.assessment import Assessment
from ..core.database import get_database
from ..core.cache import get_cache_manager
from ..core.llm_client import get_llm_client
from ..llm.interface import LLMRequest

logger = logging.getLogger(__name__)


class ConversationContext(str, Enum):
    """Types of conversation contexts."""
    GENERAL_INQUIRY = "general_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    ASSESSMENT_HELP = "assessment_help"
    PLATFORM_GUIDANCE = "platform_guidance"
    BILLING_SUPPORT = "billing_support"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    ESCALATION = "escalation"


class IntentType(str, Enum):
    """User intent types for routing."""
    GREETING = "greeting"
    QUESTION = "question"
    HELP_REQUEST = "help_request"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    GOODBYE = "goodbye"
    ESCALATION_REQUEST = "escalation_request"
    TECHNICAL_ISSUE = "technical_issue"
    FEATURE_INQUIRY = "feature_inquiry"
    PRICING_INQUIRY = "pricing_inquiry"


class ChatbotAgent(BaseAgent):
    """
    Intelligent chatbot agent for customer service and user support.
    
    Features:
    - Natural language understanding using real LLM
    - Intent recognition and response routing
    - Conversation memory and context management
    - FAQ integration and knowledge base access
    - Escalation procedures for complex queries
    - Multi-turn conversation support
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize chatbot agent."""
        super().__init__(config)
        
        # Chatbot-specific configuration
        self.max_conversation_turns = config.custom_config.get("max_conversation_turns", 20)
        self.escalation_threshold = config.custom_config.get("escalation_threshold", 3)
        self.enable_faq_integration = config.custom_config.get("enable_faq_integration", True)
        self.enable_context_memory = config.custom_config.get("enable_context_memory", True)
        
        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_context: Optional[ConversationContext] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self.escalation_count = 0
        
        # Knowledge base and FAQ integration
        self.faq_cache_key = "chatbot:faq_knowledge"
        self.knowledge_base: Dict[str, Any] = {}
        
        # Real-time knowledge integration
        self.web_search_client = None
        self.llm_client = None
        self.enable_real_time_search = config.custom_config.get("enable_real_time_search", True)
        self.search_cache_ttl = config.custom_config.get("search_cache_ttl", 3600)  # 1 hour
        
        logger.info(f"Chatbot agent initialized with max_turns={self.max_conversation_turns}")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute chatbot main logic - this is called by the base agent framework.
        For chatbots, this initializes the conversation system.
        """
        # Initialize clients for real-time knowledge
        if not self.web_search_client:
            self.web_search_client = await get_web_search_client()
        if not self.llm_client:
            self.llm_client = await get_llm_client()
        
        # Initialize knowledge base with real-time data
        await self._load_knowledge_base_with_real_time_data()
        
        # Initialize conversation context
        self.conversation_history = []
        self.current_context = ConversationContext.GENERAL_INQUIRY
        
        return {
            "recommendations": [{
                "type": "chatbot_ready",
                "message": "Chatbot agent is ready to handle conversations",
                "capabilities": [
                    "Natural language understanding",
                    "Intent recognition",
                    "FAQ integration",
                    "Conversation memory",
                    "Escalation handling"
                ]
            }],
            "data": {
                "agent_type": "chatbot",
                "status": "ready",
                "knowledge_base_loaded": len(self.knowledge_base) > 0,
                "faq_integration": self.enable_faq_integration
            }
        }
    
    async def handle_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a user message and generate appropriate response.
        
        Args:
            message: User message text
            user_id: Optional user ID for personalization
            conversation_id: Optional conversation ID for context
            context: Additional context information
            
        Returns:
            Response dictionary with chatbot reply and metadata
        """
        try:
            # Load user information if available
            if user_id:
                await self._load_user_info(user_id)
            
            # Add message to conversation history
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            self.conversation_history.append(user_message)
            
            # Recognize intent and determine context
            intent = await self._recognize_intent(message, context)
            conversation_context = await self._determine_context(message, intent, context)
            
            # Check if escalation is needed
            if await self._should_escalate(message, intent, conversation_context):
                return await self._handle_escalation(message, user_id, conversation_id)
            
            # Generate response based on context and intent
            response = await self._generate_response(
                message, 
                intent, 
                conversation_context,
                context
            )
            
            # Add response to conversation history
            bot_message = {
                "role": "assistant",
                "content": response["content"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "intent": intent.value,
                "context": conversation_context.value,
                "confidence": response.get("confidence", 0.8)
            }
            self.conversation_history.append(bot_message)
            
            # Store conversation if ID provided
            if conversation_id:
                await self._store_conversation_turn(conversation_id, user_message, bot_message)
            
            # Prepare response
            return {
                "content": response["content"],
                "intent": intent.value,
                "context": conversation_context.value,
                "confidence": response.get("confidence", 0.8),
                "suggestions": response.get("suggestions", []),
                "requires_escalation": False,
                "conversation_id": conversation_id,
                "metadata": {
                    "response_time": response.get("response_time", 0),
                    "knowledge_source": response.get("knowledge_source", "llm"),
                    "turn_count": len(self.conversation_history) // 2
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling chatbot message: {str(e)}")
            
            # Return fallback response
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or contact our support team if the issue persists.",
                "intent": "error",
                "context": "technical_issue",
                "confidence": 0.0,
                "requires_escalation": True,
                "error": str(e)
            }
    
    async def _recognize_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> IntentType:
        """
        Recognize user intent from message using LLM.
        
        Args:
            message: User message
            context: Additional context
            
        Returns:
            Recognized intent type
        """
        # Create intent recognition prompt
        intent_prompt = f"""
        Analyze the following user message and classify the intent. Consider the conversation context if provided.
        
        User message: "{message}"
        
        Available intent types:
        - greeting: User is greeting or starting conversation
        - question: User is asking a question about the platform or services
        - help_request: User needs help with a specific task or feature
        - complaint: User is expressing dissatisfaction or reporting a problem
        - compliment: User is expressing satisfaction or praise
        - goodbye: User is ending the conversation
        - escalation_request: User explicitly wants to speak to a human agent
        - technical_issue: User is reporting a technical problem or bug
        - feature_inquiry: User is asking about platform features or capabilities
        - pricing_inquiry: User is asking about pricing or billing
        
        Respond with only the intent type (e.g., "question", "help_request", etc.).
        """
        
        try:
            # Add conversation context if available
            if self.conversation_history:
                recent_context = self.conversation_history[-4:]  # Last 2 turns
                context_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in recent_context
                ])
                intent_prompt += f"\n\nRecent conversation context:\n{context_text}"
            
            # Call LLM for intent recognition
            response = await self._call_llm(
                intent_prompt,
                temperature=0.3,  # Lower temperature for classification
                max_tokens=50
            )
            
            # Parse response and map to enum
            intent_text = response.strip().lower()
            
            # Map common variations
            intent_mapping = {
                "greeting": IntentType.GREETING,
                "question": IntentType.QUESTION,
                "help_request": IntentType.HELP_REQUEST,
                "help": IntentType.HELP_REQUEST,
                "complaint": IntentType.COMPLAINT,
                "compliment": IntentType.COMPLIMENT,
                "goodbye": IntentType.GOODBYE,
                "escalation_request": IntentType.ESCALATION_REQUEST,
                "escalation": IntentType.ESCALATION_REQUEST,
                "technical_issue": IntentType.TECHNICAL_ISSUE,
                "technical": IntentType.TECHNICAL_ISSUE,
                "feature_inquiry": IntentType.FEATURE_INQUIRY,
                "feature": IntentType.FEATURE_INQUIRY,
                "pricing_inquiry": IntentType.PRICING_INQUIRY,
                "pricing": IntentType.PRICING_INQUIRY
            }
            
            return intent_mapping.get(intent_text, IntentType.QUESTION)
            
        except Exception as e:
            logger.warning(f"Intent recognition failed: {str(e)}")
            return IntentType.QUESTION  # Default fallback
    
    async def _determine_context(
        self, 
        message: str, 
        intent: IntentType, 
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        Determine conversation context based on message and intent.
        
        Args:
            message: User message
            intent: Recognized intent
            context: Additional context
            
        Returns:
            Conversation context
        """
        # Simple rule-based context determination
        message_lower = message.lower()
        
        # Technical support keywords
        technical_keywords = [
            "error", "bug", "broken", "not working", "issue", "problem",
            "crash", "slow", "timeout", "failed", "exception"
        ]
        
        # Assessment help keywords
        assessment_keywords = [
            "assessment", "evaluation", "recommendation", "analysis",
            "cloud", "infrastructure", "aws", "azure", "gcp"
        ]
        
        # Billing keywords
        billing_keywords = [
            "billing", "payment", "cost", "price", "subscription",
            "invoice", "charge", "refund"
        ]
        
        # Platform guidance keywords
        platform_keywords = [
            "how to", "tutorial", "guide", "getting started",
            "feature", "capability", "dashboard"
        ]
        
        # Check for specific contexts
        if intent == IntentType.TECHNICAL_ISSUE or any(kw in message_lower for kw in technical_keywords):
            return ConversationContext.TECHNICAL_SUPPORT
        
        elif any(kw in message_lower for kw in assessment_keywords):
            return ConversationContext.ASSESSMENT_HELP
        
        elif any(kw in message_lower for kw in billing_keywords):
            return ConversationContext.BILLING_SUPPORT
        
        elif any(kw in message_lower for kw in platform_keywords):
            return ConversationContext.PLATFORM_GUIDANCE
        
        elif intent == IntentType.ESCALATION_REQUEST:
            return ConversationContext.ESCALATION
        
        else:
            return ConversationContext.GENERAL_INQUIRY
    
    async def _should_escalate(
        self, 
        message: str, 
        intent: IntentType, 
        context: ConversationContext
    ) -> bool:
        """
        Determine if the conversation should be escalated to human support.
        
        Args:
            message: User message
            intent: Recognized intent
            context: Conversation context
            
        Returns:
            True if escalation is needed
        """
        # Explicit escalation request
        if intent == IntentType.ESCALATION_REQUEST:
            return True
        
        # Check for escalation keywords
        escalation_keywords = [
            "speak to human", "human agent", "representative", "manager",
            "supervisor", "escalate", "not helpful", "frustrated"
        ]
        
        if any(keyword in message.lower() for keyword in escalation_keywords):
            self.escalation_count += 1
            return True
        
        # Escalate after multiple failed attempts
        if self.escalation_count >= self.escalation_threshold:
            return True
        
        # Escalate for complex billing or technical issues
        if context in [ConversationContext.BILLING_SUPPORT, ConversationContext.TECHNICAL_SUPPORT]:
            # Check for complexity indicators
            complexity_indicators = [
                "urgent", "critical", "production", "outage", "security",
                "data loss", "cannot access", "account locked"
            ]
            
            if any(indicator in message.lower() for indicator in complexity_indicators):
                return True
        
        return False
    
    async def _generate_response(
        self, 
        message: str, 
        intent: IntentType, 
        context: ConversationContext,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate appropriate response based on message, intent, and context.
        
        Args:
            message: User message
            intent: Recognized intent
            context: Conversation context
            additional_context: Additional context information
            
        Returns:
            Response dictionary with content and metadata
        """
        start_time = datetime.now()
        
        # Check FAQ first if enabled
        if self.enable_faq_integration:
            faq_response = await self._check_faq(message, context)
            if faq_response:
                return {
                    "content": faq_response["answer"],
                    "confidence": faq_response["confidence"],
                    "knowledge_source": "faq",
                    "suggestions": faq_response.get("related_questions", []),
                    "response_time": (datetime.now() - start_time).total_seconds()
                }
        
        # Build system prompt based on context
        system_prompt = self._build_system_prompt(context, intent)
        
        # Build conversation context
        conversation_context = ""
        if self.conversation_history:
            recent_history = self.conversation_history[-6:]  # Last 3 turns
            conversation_context = "\n".join([
                f"{msg['role'].title()}: {msg['content']}"
                for msg in recent_history
            ])
        
        # Add user information if available
        user_context = ""
        if self.user_info:
            user_context = f"""
            User Information:
            - Name: {self.user_info.get('full_name', 'Unknown')}
            - Company: {self.user_info.get('company_name', 'Not specified')}
            - Role: {self.user_info.get('job_title', 'Not specified')}
            - Experience Level: {self.user_info.get('experience_level', 'Unknown')}
            """
        
        # Create comprehensive prompt
        prompt = f"""
        {system_prompt}
        
        {user_context}
        
        Current conversation context: {context.value}
        User intent: {intent.value}
        
        Recent conversation:
        {conversation_context}
        
        Current user message: "{message}"
        
        Please provide a helpful, professional, and contextually appropriate response.
        Keep responses concise but informative. If you don't know something specific
        about the platform, be honest and offer to help find the information or
        connect them with someone who can help.
        """
        
        try:
            # Generate response using LLM
            response_content = await self._call_llm(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # Generate suggestions based on context
            suggestions = await self._generate_suggestions(context, intent, message)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "content": response_content,
                "confidence": 0.8,  # Default confidence for LLM responses
                "knowledge_source": "llm",
                "suggestions": suggestions,
                "response_time": response_time
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            
            # Return fallback response
            return {
                "content": self._get_fallback_response(context, intent),
                "confidence": 0.3,
                "knowledge_source": "fallback",
                "suggestions": [],
                "response_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    def _build_system_prompt(self, context: ConversationContext, intent: IntentType) -> str:
        """
        Build system prompt based on conversation context and intent.
        
        Args:
            context: Conversation context
            intent: User intent
            
        Returns:
            System prompt string
        """
        base_prompt = """
        You are an intelligent customer service assistant for Infra Mind, an AI-powered 
        infrastructure advisory platform. You help businesses plan, simulate, and scale 
        their AI infrastructure across AWS, Azure, and GCP.
        
        Your role is to:
        - Provide helpful and accurate information about the platform
        - Guide users through features and capabilities
        - Assist with technical questions and troubleshooting
        - Offer professional customer service
        - Know when to escalate complex issues to human agents
        
        Platform capabilities include:
        - AI infrastructure assessments and recommendations
        - Multi-cloud cost analysis and optimization
        - Compliance mapping (GDPR, HIPAA, CCPA)
        - Infrastructure scaling simulations
        - Professional strategy reports
        - Multi-agent AI system for specialized expertise
        """
        
        # Add context-specific guidance
        context_prompts = {
            ConversationContext.TECHNICAL_SUPPORT: """
            Focus on technical troubleshooting and problem-solving. Be methodical
            in diagnosing issues and provide step-by-step solutions when possible.
            """,
            
            ConversationContext.ASSESSMENT_HELP: """
            Help users understand the assessment process, explain different types
            of requirements, and guide them through creating comprehensive evaluations.
            """,
            
            ConversationContext.PLATFORM_GUIDANCE: """
            Provide clear explanations of platform features, walk users through
            workflows, and help them understand how to get the most value from the system.
            """,
            
            ConversationContext.BILLING_SUPPORT: """
            Handle billing inquiries professionally and accurately. For complex
            billing issues, be prepared to escalate to the appropriate team.
            """,
            
            ConversationContext.GENERAL_INQUIRY: """
            Be welcoming and helpful for general questions. Provide overview
            information and guide users to more specific resources as needed.
            """
        }
        
        context_addition = context_prompts.get(context, "")
        
        return f"{base_prompt}\n\n{context_addition}"
    
    async def _check_faq(self, message: str, context: ConversationContext) -> Optional[Dict[str, Any]]:
        """
        Check FAQ knowledge base for relevant answers using the FAQ service.
        
        Args:
            message: User message
            context: Conversation context
            
        Returns:
            FAQ response if found, None otherwise
        """
        try:
            # Import FAQ service
            from ..services.faq_service import faq_service
            
            # Map conversation context to FAQ category
            category_mapping = {
                ConversationContext.TECHNICAL_SUPPORT: "technical",
                ConversationContext.ASSESSMENT_HELP: "assessments",
                ConversationContext.PLATFORM_GUIDANCE: "platform",
                ConversationContext.BILLING_SUPPORT: "billing",
                ConversationContext.GENERAL_INQUIRY: None
            }
            
            # Search FAQs using the service
            search_context = {
                "category": category_mapping.get(context)
            }
            
            # Use the chatbot-specific FAQ search endpoint logic
            from ..models.faq import FAQCategory
            from ..services.faq_service import SearchMode
            
            category = None
            if search_context.get("category"):
                try:
                    category = FAQCategory(search_context["category"])
                except ValueError:
                    pass
            
            results = await faq_service.search_faqs(
                query=message,
                category=category,
                mode=SearchMode.HYBRID,
                limit=3
            )
            
            # Check if we have a good match
            if results["results"]:
                best_match = results["results"][0]
                
                # Return best match if confidence is high enough
                if best_match["relevance_score"] > 0.7:
                    return {
                        "answer": best_match["short_answer"] or best_match["answer"],
                        "confidence": best_match["relevance_score"],
                        "related_questions": [
                            r["question"] for r in results["results"][1:3]
                        ],
                        "faq_id": best_match["id"]
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"FAQ check failed: {str(e)}")
            return None
    
    async def _generate_suggestions(
        self, 
        context: ConversationContext, 
        intent: IntentType, 
        message: str
    ) -> List[str]:
        """
        Generate helpful suggestions for the user.
        
        Args:
            context: Conversation context
            intent: User intent
            message: User message
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Context-based suggestions
        if context == ConversationContext.ASSESSMENT_HELP:
            suggestions.extend([
                "Would you like help creating a new assessment?",
                "Do you need guidance on technical requirements?",
                "Would you like to see example assessments?"
            ])
        
        elif context == ConversationContext.PLATFORM_GUIDANCE:
            suggestions.extend([
                "Would you like a platform tour?",
                "Do you need help with dashboard navigation?",
                "Would you like to see our getting started guide?"
            ])
        
        elif context == ConversationContext.TECHNICAL_SUPPORT:
            suggestions.extend([
                "Would you like to report a bug?",
                "Do you need help with account access?",
                "Would you like troubleshooting steps?"
            ])
        
        # Intent-based suggestions
        if intent == IntentType.GREETING:
            suggestions.extend([
                "How can I help you today?",
                "Would you like to learn about our platform?",
                "Do you have any questions about infrastructure planning?"
            ])
        
        # Limit to 3 suggestions
        return suggestions[:3]
    
    def _get_fallback_response(self, context: ConversationContext, intent: IntentType) -> str:
        """
        Get fallback response when LLM generation fails.
        
        Args:
            context: Conversation context
            intent: User intent
            
        Returns:
            Fallback response string
        """
        fallback_responses = {
            ConversationContext.TECHNICAL_SUPPORT: 
                "I'm experiencing technical difficulties right now. Please try again in a moment, or contact our support team directly for immediate assistance.",
            
            ConversationContext.BILLING_SUPPORT:
                "I'm unable to access billing information at the moment. Please contact our billing support team directly for assistance with your account.",
            
            ConversationContext.ASSESSMENT_HELP:
                "I'm having trouble accessing assessment guidance right now. You can find help documentation in the platform, or contact our support team.",
            
            ConversationContext.GENERAL_INQUIRY:
                "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or contact our support team if you need immediate assistance."
        }
        
        return fallback_responses.get(
            context, 
            "I'm sorry, but I'm experiencing technical difficulties. Please try again in a moment."
        )
    
    async def _handle_escalation(
        self, 
        message: str, 
        user_id: Optional[str], 
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handle escalation to human support.
        
        Args:
            message: User message
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            Escalation response
        """
        # Create support ticket
        ticket_id = await self._create_support_ticket(message, user_id, conversation_id)
        
        escalation_response = f"""
        I understand you'd like to speak with a human agent. I've created a support 
        ticket (#{ticket_id}) and our team will get back to you as soon as possible.
        
        In the meantime, is there anything else I can help you with?
        """
        
        return {
            "content": escalation_response,
            "intent": "escalation",
            "context": "escalation",
            "confidence": 1.0,
            "requires_escalation": True,
            "ticket_id": ticket_id,
            "metadata": {
                "escalation_reason": "user_request",
                "conversation_turns": len(self.conversation_history)
            }
        }
    
    async def _create_support_ticket(
        self, 
        message: str, 
        user_id: Optional[str], 
        conversation_id: Optional[str]
    ) -> str:
        """
        Create a support ticket for escalation using the customer service system.
        
        Args:
            message: User message
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            Ticket ID
        """
        try:
            # Import customer service manager
            from ..services.customer_service import customer_service_manager
            from ..models.support_ticket import TicketCategory, TicketPriority, TicketSource
            
            # Get user information if available
            customer_email = "unknown@example.com"
            customer_name = "Unknown Customer"
            
            if user_id:
                from ..models.user import User
                user = await User.get(user_id)
                if user:
                    customer_email = user.email
                    customer_name = user.full_name
            
            # Create ticket title and description
            title = f"Chatbot Escalation - {self.current_context.value if self.current_context else 'General Inquiry'}"
            
            # Build description from conversation history
            description = f"Escalated from chatbot conversation.\n\nUser Message: {message}\n\n"
            description += "Recent Conversation History:\n"
            
            for msg in self.conversation_history[-6:]:  # Last 3 turns
                role = msg.get("role", "unknown").title()
                content = msg.get("content", "")
                description += f"{role}: {content}\n"
            
            # Determine category based on context
            category_mapping = {
                ConversationContext.TECHNICAL_SUPPORT: TicketCategory.TECHNICAL_ISSUE,
                ConversationContext.BILLING_SUPPORT: TicketCategory.BILLING_INQUIRY,
                ConversationContext.ASSESSMENT_HELP: TicketCategory.ASSESSMENT_HELP,
                ConversationContext.PLATFORM_GUIDANCE: TicketCategory.PLATFORM_GUIDANCE,
                ConversationContext.GENERAL_INQUIRY: TicketCategory.GENERAL_INQUIRY
            }
            
            category = category_mapping.get(
                self.current_context, 
                TicketCategory.GENERAL_INQUIRY
            )
            
            # Create ticket using customer service manager
            ticket = await customer_service_manager.create_ticket(
                title=title,
                description=description,
                customer_email=customer_email,
                customer_name=customer_name,
                category=category,
                priority=TicketPriority.NORMAL,
                source=TicketSource.CHATBOT_ESCALATION,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            ticket_id = ticket["ticket_id"]
            logger.info(f"Created support ticket {ticket_id} for user {user_id}")
            
            return ticket_id
            
        except Exception as e:
            logger.error(f"Failed to create support ticket: {str(e)}")
            # Fallback to simple ticket ID
            return f"CHAT-{uuid.uuid4().hex[:8].upper()}"
    
    async def _load_knowledge_base(self) -> None:
        """Load FAQ and knowledge base data."""
        try:
            cache_manager = await get_cache_manager()
            
            # Try to load from cache first
            cached_kb = await cache_manager.get(self.faq_cache_key)
            if cached_kb:
                self.knowledge_base = cached_kb
                logger.info("Loaded knowledge base from cache")
                return
            
            # Load from database or file
            # For now, use a basic knowledge base
            self.knowledge_base = {
                "faq": [
                    {
                        "question": "What is Infra Mind?",
                        "answer": "Infra Mind is an AI-powered infrastructure advisory platform that helps businesses plan, simulate, and scale their AI infrastructure across AWS, Azure, and GCP.",
                        "keywords": ["what is", "infra mind", "platform", "about"],
                        "confidence": 0.95
                    },
                    {
                        "question": "How do I create an assessment?",
                        "answer": "To create an assessment, go to the Dashboard and click 'New Assessment'. Fill out your business and technical requirements, and our AI agents will analyze your needs.",
                        "keywords": ["create assessment", "new assessment", "how to assess"],
                        "confidence": 0.9
                    },
                    {
                        "question": "What cloud providers do you support?",
                        "answer": "We support AWS, Microsoft Azure, and Google Cloud Platform (GCP). Our platform provides comprehensive analysis and recommendations across all three providers.",
                        "keywords": ["cloud providers", "aws", "azure", "gcp", "google cloud"],
                        "confidence": 0.95
                    },
                    {
                        "question": "How much does it cost?",
                        "answer": "Our pricing varies based on your needs and usage. Please contact our sales team for detailed pricing information, or check our pricing page for current plans.",
                        "keywords": ["cost", "price", "pricing", "how much"],
                        "confidence": 0.8
                    }
                ]
            }
            
            # Cache the knowledge base
            await cache_manager.set(
                self.faq_cache_key, 
                self.knowledge_base, 
                ttl=3600  # 1 hour
            )
            
            logger.info("Loaded and cached knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {str(e)}")
            self.knowledge_base = {"faq": []}
    
    async def _load_user_info(self, user_id: str) -> None:
        """
        Load user information for personalization.
        
        Args:
            user_id: User ID to load
        """
        try:
            user = await User.get(user_id)
            if user:
                self.user_info = {
                    "full_name": user.full_name,
                    "company_name": user.company_name,
                    "job_title": user.job_title,
                    "company_size": user.company_size.value if user.company_size else None,
                    "industry": user.industry.value if user.industry else None,
                    "assessments_created": user.assessments_created
                }
                
                logger.debug(f"Loaded user info for {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to load user info for {user_id}: {str(e)}")
            self.user_info = None
    
    async def _store_conversation_turn(
        self, 
        conversation_id: str, 
        user_message: Dict[str, Any], 
        bot_message: Dict[str, Any]
    ) -> None:
        """
        Store conversation turn in database.
        
        Args:
            conversation_id: Conversation ID
            user_message: User message data
            bot_message: Bot response data
        """
        try:
            db = await get_database()
            
            conversation_turn = {
                "conversation_id": conversation_id,
                "turn_number": len(self.conversation_history) // 2,
                "user_message": user_message,
                "bot_message": bot_message,
                "timestamp": datetime.now(timezone.utc)
            }
            
            await db.conversation_history.insert_one(conversation_turn)
            
        except Exception as e:
            logger.warning(f"Failed to store conversation turn: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a given conversation ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of conversation turns
        """
        try:
            db = await get_database()
            
            cursor = db.conversation_history.find(
                {"conversation_id": conversation_id}
            ).sort("turn_number", 1)
            
            history = await cursor.to_list(length=None)
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    async def clear_conversation_context(self) -> None:
        """Clear conversation context and history."""
        self.conversation_history = []
        self.current_context = ConversationContext.GENERAL_INQUIRY
        self.escalation_count = 0
        self.user_info = None
        
        logger.debug("Cleared conversation context")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Returns:
            Conversation statistics
        """
        return {
            "total_turns": len(self.conversation_history),
            "user_turns": len([msg for msg in self.conversation_history if msg["role"] == "user"]),
            "bot_turns": len([msg for msg in self.conversation_history if msg["role"] == "assistant"]),
            "current_context": self.current_context.value if self.current_context else None,
            "escalation_count": self.escalation_count,
            "has_user_info": self.user_info is not None,
            "knowledge_base_loaded": len(self.knowledge_base.get("faq", [])) > 0
        }
    
    # Enhanced methods with real-time knowledge integration
    
    async def _load_knowledge_base_with_real_time_data(self) -> None:
        """Load knowledge base with real-time data from web search."""
        logger.debug("Loading knowledge base with real-time data")
        
        try:
            # Load base knowledge base first
            await self._load_knowledge_base()
            
            # Collect real-time knowledge updates
            real_time_knowledge = await self._collect_real_time_knowledge()
            
            # Integrate real-time data into knowledge base
            if real_time_knowledge:
                self.knowledge_base["real_time_updates"] = real_time_knowledge
                self.knowledge_base["last_update"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(f"Enhanced knowledge base with {len(real_time_knowledge)} real-time sources")
            
        except Exception as e:
            logger.warning(f"Failed to load real-time knowledge data: {str(e)}")
            # Fall back to base knowledge base
            await self._load_knowledge_base()
    
    async def _collect_real_time_knowledge(self) -> Dict[str, Any]:
        """Collect real-time knowledge from various sources."""
        logger.debug("Collecting real-time knowledge")
        
        real_time_knowledge = {
            "platform_updates": [],
            "service_status": [],
            "common_issues": [],
            "feature_announcements": [],
            "troubleshooting_guides": []
        }
        
        try:
            # Search for platform updates and news
            platform_search = await self.web_search_client.search(
                "infrastructure platform updates cloud services 2024 2025 enterprise announcements",
                num_results=3
            )
            real_time_knowledge["platform_updates"] = platform_search.get("results", [])
            
            # Search for service status and outages
            status_search = await self.web_search_client.search(
                "cloud service status outages infrastructure issues enterprise support 2024",
                num_results=3
            )
            real_time_knowledge["service_status"] = status_search.get("results", [])
            
            # Search for common technical issues
            issues_search = await self.web_search_client.search(
                "common infrastructure problems troubleshooting enterprise cloud support 2024",
                num_results=3
            )
            real_time_knowledge["common_issues"] = issues_search.get("results", [])
            
            # Search for feature announcements
            features_search = await self.web_search_client.search(
                "cloud infrastructure new features enterprise platform capabilities 2024 2025",
                num_results=3
            )
            real_time_knowledge["feature_announcements"] = features_search.get("results", [])
            
            # Search for troubleshooting guides
            guides_search = await self.web_search_client.search(
                "infrastructure troubleshooting guides enterprise support documentation 2024",
                num_results=3
            )
            real_time_knowledge["troubleshooting_guides"] = guides_search.get("results", [])
            
            logger.info(f"Collected real-time knowledge from {sum(len(v) for v in real_time_knowledge.values())} sources")
            
        except Exception as e:
            logger.warning(f"Failed to collect some real-time knowledge: {str(e)}")
        
        return real_time_knowledge
    
    async def _should_use_real_time_knowledge(self, message: str, intent: IntentType, context: ConversationContext) -> bool:
        """Determine if real-time knowledge should be used for this query."""
        # Use real-time knowledge for these intent types
        real_time_intents = {
            IntentType.TECHNICAL_ISSUE,
            IntentType.FEATURE_INQUIRY,
            IntentType.QUESTION,
            IntentType.HELP_REQUEST
        }
        
        # Use real-time knowledge for these contexts
        real_time_contexts = {
            ConversationContext.TECHNICAL_SUPPORT,
            ConversationContext.PLATFORM_GUIDANCE,
            ConversationContext.GENERAL_INQUIRY
        }
        
        # Check for keywords that suggest need for current information
        current_info_keywords = [
            "latest", "current", "recent", "new", "updated", "status", 
            "outage", "issue", "problem", "feature", "announcement"
        ]
        
        message_lower = message.lower()
        has_current_keywords = any(keyword in message_lower for keyword in current_info_keywords)
        
        return (
            intent in real_time_intents or 
            context in real_time_contexts or 
            has_current_keywords
        )
    
    async def _search_real_time_knowledge(self, message: str, intent: IntentType, context: ConversationContext) -> Dict[str, Any]:
        """Search for relevant real-time knowledge based on the message."""
        logger.debug("Searching real-time knowledge")
        
        try:
            # Create search query based on message and context
            search_query = await self._create_contextual_search_query(message, intent, context)
            
            # Search for relevant real-time information
            search_results = await self.web_search_client.search(search_query, num_results=3)
            
            # Process and structure the results
            real_time_info = {
                "query": search_query,
                "sources": search_results.get("results", []),
                "summary": await self._summarize_search_results(search_results.get("results", []), message)
            }
            
            return real_time_info
            
        except Exception as e:
            logger.warning(f"Failed to search real-time knowledge: {str(e)}")
            return {}
    
    async def _create_contextual_search_query(self, message: str, intent: IntentType, context: ConversationContext) -> str:
        """Create a contextual search query based on the user message."""
        base_terms = "enterprise infrastructure cloud platform support"
        
        # Add context-specific terms
        if context == ConversationContext.TECHNICAL_SUPPORT:
            context_terms = "troubleshooting technical issues problems solutions"
        elif context == ConversationContext.PLATFORM_GUIDANCE:
            context_terms = "features capabilities documentation guides"
        elif intent == IntentType.FEATURE_INQUIRY:
            context_terms = "new features updates announcements capabilities"
        else:
            context_terms = "help support documentation"
        
        # Extract key terms from message
        message_terms = await self._extract_key_terms(message)
        
        # Combine terms
        search_query = f"{message_terms} {context_terms} {base_terms} 2024 2025"
        
        return search_query
    
    async def _extract_key_terms(self, message: str) -> str:
        """Extract key terms from user message using LLM."""
        try:
            extract_prompt = f"""
            Extract the key technical terms and concepts from this user message.
            Focus on infrastructure, platform, and technical terms.
            
            Message: "{message}"
            
            Respond with only the key terms separated by spaces.
            """
            
            response = await self.llm_client.generate_completion(extract_prompt)
            return response.strip()
            
        except Exception as e:
            logger.warning(f"Failed to extract key terms: {str(e)}")
            # Fallback to simple keyword extraction
            keywords = [word for word in message.split() if len(word) > 3]
            return " ".join(keywords[:5])
    
    async def _summarize_search_results(self, search_results: List[Dict[str, Any]], original_message: str) -> str:
        """Summarize search results relevant to the user's message."""
        if not search_results:
            return "No relevant information found."
        
        try:
            # Prepare search results context
            results_context = ""
            for i, result in enumerate(search_results[:3]):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                results_context += f"{i+1}. {title}: {snippet}\n"
            
            summary_prompt = f"""
            Based on the following search results, provide a brief summary that answers or relates to the user's question.
            Focus on the most relevant and current information.
            
            User question: "{original_message}"
            
            Search results:
            {results_context}
            
            Provide a concise summary in 2-3 sentences.
            """
            
            summary = await self.llm_client.generate_completion(summary_prompt)
            return summary.strip()
            
        except Exception as e:
            logger.warning(f"Failed to summarize search results: {str(e)}")
            return "Found some relevant information, but unable to summarize at this time."