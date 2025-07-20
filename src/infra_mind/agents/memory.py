"""
Agent memory system for Infra Mind.

Provides memory capabilities for agents to maintain context and learn from interactions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: str
    content: Dict[str, Any]
    timestamp: datetime
    entry_type: str = "general"
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "entry_type": self.entry_type,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            entry_type=data.get("entry_type", "general"),
            importance=data.get("importance", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


class BaseMemory(ABC):
    """Base class for agent memory systems."""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memory entries based on query."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries."""
        pass


class AgentMemory(BaseMemory):
    """
    In-memory storage for agent memory.
    
    Learning Note: This provides basic memory functionality.
    In production, you might want to use a vector database
    like Pinecone or Weaviate for semantic search.
    """
    
    def __init__(self, max_entries: int = 1000):
        """
        Initialize agent memory.
        
        Args:
            max_entries: Maximum number of entries to keep
        """
        self.max_entries = max_entries
        self.entries: List[MemoryEntry] = []
        self.context_cache: Dict[str, Any] = {}
    
    async def store(self, entry: MemoryEntry) -> None:
        """
        Store a memory entry.
        
        Args:
            entry: Memory entry to store
        """
        self.entries.append(entry)
        
        # Remove oldest entries if we exceed max_entries
        if len(self.entries) > self.max_entries:
            # Sort by importance and timestamp, keep most important/recent
            self.entries.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            self.entries = self.entries[:self.max_entries]
        
        logger.debug(f"Stored memory entry: {entry.id} ({entry.entry_type})")
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Retrieve memory entries based on query.
        
        Args:
            query: Search query
            limit: Maximum number of entries to return
            
        Returns:
            List of matching memory entries
        """
        # Simple keyword-based search
        # In production, use semantic search with embeddings
        query_lower = query.lower()
        matching_entries = []
        
        for entry in self.entries:
            # Check if query matches content, tags, or metadata
            content_str = json.dumps(entry.content).lower()
            tags_str = " ".join(entry.tags).lower()
            metadata_str = json.dumps(entry.metadata).lower()
            
            if (query_lower in content_str or 
                query_lower in tags_str or 
                query_lower in metadata_str):
                matching_entries.append(entry)
        
        # Sort by importance and recency
        matching_entries.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return matching_entries[:limit]
    
    async def retrieve_by_type(self, entry_type: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Retrieve memory entries by type.
        
        Args:
            entry_type: Type of entries to retrieve
            limit: Maximum number of entries to return
            
        Returns:
            List of matching memory entries
        """
        matching_entries = [e for e in self.entries if e.entry_type == entry_type]
        matching_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return matching_entries[:limit]
    
    async def retrieve_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryEntry]:
        """
        Retrieve memory entries by tags.
        
        Args:
            tags: List of tags to search for
            limit: Maximum number of entries to return
            
        Returns:
            List of matching memory entries
        """
        matching_entries = []
        
        for entry in self.entries:
            if any(tag in entry.tags for tag in tags):
                matching_entries.append(entry)
        
        matching_entries.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        return matching_entries[:limit]
    
    async def clear(self) -> None:
        """Clear all memory entries."""
        self.entries.clear()
        self.context_cache.clear()
        logger.info("Cleared agent memory")
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get memory summary statistics."""
        if not self.entries:
            return {"total_entries": 0}
        
        # Count by type
        type_counts = {}
        for entry in self.entries:
            type_counts[entry.entry_type] = type_counts.get(entry.entry_type, 0) + 1
        
        # Get date range
        timestamps = [e.timestamp for e in self.entries]
        oldest = min(timestamps)
        newest = max(timestamps)
        
        return {
            "total_entries": len(self.entries),
            "entry_types": type_counts,
            "oldest_entry": oldest.isoformat(),
            "newest_entry": newest.isoformat(),
            "average_importance": sum(e.importance for e in self.entries) / len(self.entries)
        }
    
    async def load_context(self, context_id: str) -> None:
        """
        Load context for a specific assessment or conversation.
        
        Args:
            context_id: Context identifier (e.g., assessment ID)
        """
        # In a real implementation, this would load from persistent storage
        # For now, we'll use in-memory cache
        if context_id in self.context_cache:
            context_data = self.context_cache[context_id]
            self.entries = [MemoryEntry.from_dict(entry) for entry in context_data.get("entries", [])]
            logger.info(f"Loaded {len(self.entries)} memory entries for context {context_id}")
        else:
            logger.info(f"No existing memory found for context {context_id}")
    
    async def save_context(self, context_id: str) -> None:
        """
        Save context for a specific assessment or conversation.
        
        Args:
            context_id: Context identifier (e.g., assessment ID)
        """
        # In a real implementation, this would save to persistent storage
        # For now, we'll use in-memory cache
        self.context_cache[context_id] = {
            "entries": [entry.to_dict() for entry in self.entries],
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Saved {len(self.entries)} memory entries for context {context_id}")


class ConversationMemory(AgentMemory):
    """
    Specialized memory for conversation context.
    
    Learning Note: This extends AgentMemory with conversation-specific
    functionality like turn tracking and context windows.
    """
    
    def __init__(self, max_entries: int = 100, context_window: int = 10):
        """
        Initialize conversation memory.
        
        Args:
            max_entries: Maximum number of entries to keep
            context_window: Number of recent entries to include in context
        """
        super().__init__(max_entries)
        self.context_window = context_window
        self.conversation_turns: List[Dict[str, Any]] = []
    
    async def add_user_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a user message to conversation memory.
        
        Args:
            message: User message
            metadata: Additional metadata
        """
        entry = MemoryEntry(
            id=f"user_{len(self.conversation_turns)}",
            content={"role": "user", "message": message},
            timestamp=datetime.now(timezone.utc),
            entry_type="conversation",
            importance=1.0,
            tags=["user", "conversation"],
            metadata=metadata or {}
        )
        
        await self.store(entry)
        self.conversation_turns.append({
            "role": "user",
            "message": message,
            "timestamp": entry.timestamp.isoformat()
        })
    
    async def add_agent_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an agent message to conversation memory.
        
        Args:
            message: Agent message
            metadata: Additional metadata
        """
        entry = MemoryEntry(
            id=f"agent_{len(self.conversation_turns)}",
            content={"role": "agent", "message": message},
            timestamp=datetime.now(timezone.utc),
            entry_type="conversation",
            importance=1.0,
            tags=["agent", "conversation"],
            metadata=metadata or {}
        )
        
        await self.store(entry)
        self.conversation_turns.append({
            "role": "agent",
            "message": message,
            "timestamp": entry.timestamp.isoformat()
        })
    
    async def get_conversation_context(self) -> List[Dict[str, Any]]:
        """
        Get recent conversation context.
        
        Returns:
            List of recent conversation turns
        """
        return self.conversation_turns[-self.context_window:]
    
    async def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation.
        
        Returns:
            Conversation summary
        """
        if not self.conversation_turns:
            return "No conversation history"
        
        total_turns = len(self.conversation_turns)
        user_turns = sum(1 for turn in self.conversation_turns if turn["role"] == "user")
        agent_turns = sum(1 for turn in self.conversation_turns if turn["role"] == "agent")
        
        return f"Conversation with {total_turns} turns ({user_turns} user, {agent_turns} agent)"


class WorkingMemory:
    """
    Working memory for temporary data during agent execution.
    
    Learning Note: Working memory is used for temporary storage
    during agent execution and is cleared between runs.
    """
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.scratch_pad: List[str] = []
        self.intermediate_results: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in working memory."""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from working memory."""
        return self.data.get(key, default)
    
    def add_note(self, note: str) -> None:
        """Add a note to the scratch pad."""
        self.scratch_pad.append(f"[{datetime.now(timezone.utc).isoformat()}] {note}")
    
    def set_intermediate_result(self, step: str, result: Any) -> None:
        """Set an intermediate result."""
        self.intermediate_results[step] = result
    
    def get_intermediate_result(self, step: str) -> Any:
        """Get an intermediate result."""
        return self.intermediate_results.get(step)
    
    def clear(self) -> None:
        """Clear working memory."""
        self.data.clear()
        self.scratch_pad.clear()
        self.intermediate_results.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get working memory summary."""
        return {
            "data_keys": list(self.data.keys()),
            "notes_count": len(self.scratch_pad),
            "intermediate_results": list(self.intermediate_results.keys())
        }