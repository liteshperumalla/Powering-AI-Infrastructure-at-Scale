"""
Conversation Memory Management for Chatbot Agent.

Provides persistent conversation memory, context management, and
conversation analytics for the chatbot system.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid

from ..core.database import get_database
from ..core.cache import get_cache_manager
from ..models.user import User

logger = logging.getLogger(__name__)


class ConversationStatus(str, Enum):
    """Conversation status types."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


class MessageType(str, Enum):
    """Message types in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ESCALATION = "escalation"


class ConversationMemory:
    """
    Manages conversation memory and context for chatbot interactions.
    
    Features:
    - Persistent conversation storage
    - Context-aware memory retrieval
    - Conversation analytics and insights
    - Memory optimization and cleanup
    - Multi-session conversation tracking
    """
    
    def __init__(self, max_memory_turns: int = 50, cache_ttl: int = 3600):
        """
        Initialize conversation memory manager.
        
        Args:
            max_memory_turns: Maximum number of turns to keep in memory
            cache_ttl: Cache TTL in seconds
        """
        self.max_memory_turns = max_memory_turns
        self.cache_ttl = cache_ttl
        self.cache_prefix = "chatbot:conversation:"
        
        logger.info(f"ConversationMemory initialized with max_turns={max_memory_turns}")
    
    async def create_conversation(
        self, 
        user_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
        conversation_type: str = "general"
    ) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user ID
            initial_context: Initial conversation context
            conversation_type: Type of conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        try:
            db = await get_database()
            
            conversation_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "conversation_type": conversation_type,
                "status": ConversationStatus.ACTIVE.value,
                "context": initial_context or {},
                "metadata": {
                    "created_at": datetime.now(timezone.utc),
                    "last_activity": datetime.now(timezone.utc),
                    "turn_count": 0,
                    "escalation_count": 0,
                    "user_satisfaction": None
                },
                "messages": [],
                "summary": None
            }
            
            await db.conversations.insert_one(conversation_data)
            
            # Cache the conversation
            await self._cache_conversation(conversation_id, conversation_data)
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        message_type: MessageType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation.
        
        Args:
            conversation_id: Conversation ID
            message_type: Type of message
            content: Message content
            metadata: Additional message metadata
        """
        try:
            message_data = {
                "message_id": str(uuid.uuid4()),
                "type": message_type.value,
                "content": content,
                "timestamp": datetime.now(timezone.utc),
                "metadata": metadata or {}
            }
            
            # Update database
            db = await get_database()
            
            await db.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": message_data},
                    "$inc": {"metadata.turn_count": 1 if message_type == MessageType.USER else 0},
                    "$set": {"metadata.last_activity": datetime.now(timezone.utc)}
                }
            )
            
            # Update cache
            await self._update_conversation_cache(conversation_id, message_data)
            
            logger.debug(f"Added {message_type.value} message to conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        max_turns: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get conversation context with recent messages.
        
        Args:
            conversation_id: Conversation ID
            max_turns: Maximum number of turns to retrieve
            
        Returns:
            Conversation context
        """
        try:
            # Try cache first
            cache_manager = await get_cache_manager()
            cache_key = f"{self.cache_prefix}{conversation_id}"
            
            cached_conversation = await cache_manager.get(cache_key)
            if cached_conversation:
                return self._format_conversation_context(cached_conversation, max_turns)
            
            # Load from database
            db = await get_database()
            conversation = await db.conversations.find_one(
                {"conversation_id": conversation_id}
            )
            
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Cache the conversation
            await self._cache_conversation(conversation_id, conversation)
            
            return self._format_conversation_context(conversation, max_turns)
            
        except Exception as e:
            logger.error(f"Failed to get conversation context for {conversation_id}: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "messages": [],
                "context": {},
                "metadata": {},
                "error": str(e)
            }
    
    async def update_conversation_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update conversation status.
        
        Args:
            conversation_id: Conversation ID
            status: New status
            metadata: Additional metadata to update
        """
        try:
            db = await get_database()
            
            update_data = {
                "status": status.value,
                "metadata.last_activity": datetime.now(timezone.utc)
            }
            
            if metadata:
                for key, value in metadata.items():
                    update_data[f"metadata.{key}"] = value
            
            await db.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": update_data}
            )
            
            # Update cache
            cache_manager = await get_cache_manager()
            cache_key = f"{self.cache_prefix}{conversation_id}"
            await cache_manager.delete(cache_key)  # Invalidate cache
            
            logger.info(f"Updated conversation {conversation_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update conversation status: {str(e)}")
            raise
    
    async def get_user_conversation_history(
        self,
        user_id: str,
        limit: int = 10,
        status_filter: Optional[ConversationStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            status_filter: Optional status filter
            
        Returns:
            List of conversation summaries
        """
        try:
            db = await get_database()
            
            query = {"user_id": user_id}
            if status_filter:
                query["status"] = status_filter.value
            
            cursor = db.conversations.find(
                query,
                {
                    "conversation_id": 1,
                    "conversation_type": 1,
                    "status": 1,
                    "metadata": 1,
                    "summary": 1,
                    "messages": {"$slice": -2}  # Last 2 messages for preview
                }
            ).sort("metadata.created_at", -1).limit(limit)
            
            conversations = await cursor.to_list(length=None)
            
            # Format for response
            formatted_conversations = []
            for conv in conversations:
                formatted_conversations.append({
                    "conversation_id": conv["conversation_id"],
                    "type": conv["conversation_type"],
                    "status": conv["status"],
                    "created_at": conv["metadata"]["created_at"],
                    "last_activity": conv["metadata"]["last_activity"],
                    "turn_count": conv["metadata"]["turn_count"],
                    "summary": conv.get("summary"),
                    "preview": conv["messages"][-1]["content"] if conv["messages"] else None
                })
            
            return formatted_conversations
            
        except Exception as e:
            logger.error(f"Failed to get user conversation history: {str(e)}")
            return []
    
    async def generate_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """
        Generate a summary of the conversation using LLM.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation summary or None if failed
        """
        try:
            # Get full conversation context
            context = await self.get_conversation_context(conversation_id)
            
            if not context["messages"]:
                return None
            
            # Import LLM manager here to avoid circular imports
            from ..llm.manager import LLMManager
            from ..llm.interface import LLMRequest
            
            llm_manager = LLMManager()
            
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['type'].title()}: {msg['content']}"
                for msg in context["messages"]
            ])
            
            # Create summary prompt
            summary_prompt = f"""
            Please provide a concise summary of this customer service conversation.
            Focus on the main topics discussed, issues raised, and any resolutions provided.
            
            Conversation:
            {conversation_text}
            
            Summary (2-3 sentences):
            """
            
            request = LLMRequest(
                prompt=summary_prompt,
                model="gpt-3.5-turbo",  # Use cheaper model for summaries
                temperature=0.3,
                max_tokens=150
            )
            
            response = await llm_manager.generate_response(request)
            summary = response.content.strip()
            
            # Store summary in database
            db = await get_database()
            await db.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": {"summary": summary}}
            )
            
            logger.info(f"Generated summary for conversation {conversation_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {str(e)}")
            return None
    
    async def get_conversation_analytics(
        self,
        user_id: Optional[str] = None,
        date_range: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get conversation analytics and insights.
        
        Args:
            user_id: Optional user ID filter
            date_range: Optional date range filter
            
        Returns:
            Analytics data
        """
        try:
            db = await get_database()
            
            # Build query
            query = {}
            if user_id:
                query["user_id"] = user_id
            
            if date_range:
                query["metadata.created_at"] = {
                    "$gte": date_range.get("start", datetime.now(timezone.utc) - timedelta(days=30)),
                    "$lte": date_range.get("end", datetime.now(timezone.utc))
                }
            
            # Aggregation pipeline
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_conversations": {"$sum": 1},
                        "avg_turn_count": {"$avg": "$metadata.turn_count"},
                        "status_breakdown": {
                            "$push": "$status"
                        },
                        "conversation_types": {
                            "$push": "$conversation_type"
                        },
                        "escalation_count": {"$sum": "$metadata.escalation_count"}
                    }
                }
            ]
            
            result = await db.conversations.aggregate(pipeline).to_list(length=1)
            
            if not result:
                return {
                    "total_conversations": 0,
                    "avg_turn_count": 0,
                    "status_breakdown": {},
                    "conversation_types": {},
                    "escalation_rate": 0
                }
            
            data = result[0]
            
            # Process status breakdown
            status_counts = {}
            for status in data["status_breakdown"]:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Process conversation types
            type_counts = {}
            for conv_type in data["conversation_types"]:
                type_counts[conv_type] = type_counts.get(conv_type, 0) + 1
            
            # Calculate escalation rate
            escalation_rate = (data["escalation_count"] / data["total_conversations"]) * 100 if data["total_conversations"] > 0 else 0
            
            return {
                "total_conversations": data["total_conversations"],
                "avg_turn_count": round(data["avg_turn_count"], 2),
                "status_breakdown": status_counts,
                "conversation_types": type_counts,
                "escalation_rate": round(escalation_rate, 2),
                "total_escalations": data["escalation_count"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation analytics: {str(e)}")
            return {}
    
    async def cleanup_old_conversations(self, days_old: int = 90) -> int:
        """
        Clean up old conversations to manage storage.
        
        Args:
            days_old: Number of days old to consider for cleanup
            
        Returns:
            Number of conversations cleaned up
        """
        try:
            db = await get_database()
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Only clean up completed or abandoned conversations
            query = {
                "metadata.created_at": {"$lt": cutoff_date},
                "status": {"$in": [ConversationStatus.COMPLETED.value, ConversationStatus.ABANDONED.value]}
            }
            
            # Archive conversations before deletion (optional)
            conversations_to_archive = await db.conversations.find(query).to_list(length=None)
            
            if conversations_to_archive:
                # Move to archive collection
                await db.conversation_archive.insert_many(conversations_to_archive)
                
                # Delete from main collection
                result = await db.conversations.delete_many(query)
                
                # Clear related cache entries
                cache_manager = await get_cache_manager()
                for conv in conversations_to_archive:
                    cache_key = f"{self.cache_prefix}{conv['conversation_id']}"
                    await cache_manager.delete(cache_key)
                
                logger.info(f"Cleaned up {result.deleted_count} old conversations")
                return result.deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {str(e)}")
            return 0
    
    async def _cache_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> None:
        """
        Cache conversation data.
        
        Args:
            conversation_id: Conversation ID
            conversation_data: Conversation data to cache
        """
        try:
            cache_manager = await get_cache_manager()
            cache_key = f"{self.cache_prefix}{conversation_id}"
            
            # Only cache recent messages to save memory
            cached_data = conversation_data.copy()
            if len(cached_data.get("messages", [])) > self.max_memory_turns:
                cached_data["messages"] = cached_data["messages"][-self.max_memory_turns:]
            
            await cache_manager.set(cache_key, cached_data, ttl=self.cache_ttl)
            
        except Exception as e:
            logger.warning(f"Failed to cache conversation {conversation_id}: {str(e)}")
    
    async def _update_conversation_cache(self, conversation_id: str, new_message: Dict[str, Any]) -> None:
        """
        Update cached conversation with new message.
        
        Args:
            conversation_id: Conversation ID
            new_message: New message to add
        """
        try:
            cache_manager = await get_cache_manager()
            cache_key = f"{self.cache_prefix}{conversation_id}"
            
            cached_conversation = await cache_manager.get(cache_key)
            if cached_conversation:
                cached_conversation["messages"].append(new_message)
                cached_conversation["metadata"]["last_activity"] = datetime.now(timezone.utc)
                
                # Trim messages if too many
                if len(cached_conversation["messages"]) > self.max_memory_turns:
                    cached_conversation["messages"] = cached_conversation["messages"][-self.max_memory_turns:]
                
                await cache_manager.set(cache_key, cached_conversation, ttl=self.cache_ttl)
            
        except Exception as e:
            logger.warning(f"Failed to update conversation cache: {str(e)}")
    
    def _format_conversation_context(
        self, 
        conversation: Dict[str, Any], 
        max_turns: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format conversation data for context.
        
        Args:
            conversation: Raw conversation data
            max_turns: Maximum number of turns to include
            
        Returns:
            Formatted conversation context
        """
        messages = conversation.get("messages", [])
        
        if max_turns and len(messages) > max_turns:
            messages = messages[-max_turns:]
        
        return {
            "conversation_id": conversation["conversation_id"],
            "user_id": conversation.get("user_id"),
            "status": conversation["status"],
            "context": conversation.get("context", {}),
            "metadata": conversation.get("metadata", {}),
            "messages": messages,
            "summary": conversation.get("summary")
        }


# Global conversation memory instance
conversation_memory = ConversationMemory()