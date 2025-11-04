"""
Conversation State Manager for Chatbot.

Manages conversation context, memory, and summarization to prevent
unbounded growth and improve response quality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..core.cache import get_cache_manager

logger = logging.getLogger(__name__)


class ConversationStateManager:
    """
    Manages conversation state and context for chatbot sessions.

    Prevents memory leaks by implementing:
    - Sliding window context (keep last N turns)
    - Automatic summarization of old turns
    - State persistence in cache
    """

    def __init__(
        self,
        max_context_turns: int = 10,
        summarize_after_turns: int = 15,
        cache_ttl: int = 3600
    ):
        """
        Initialize conversation state manager.

        Args:
            max_context_turns: Maximum turns to keep in active context
            summarize_after_turns: Summarize conversation after this many turns
            cache_ttl: Cache time-to-live in seconds (1 hour default)
        """
        self.max_context_turns = max_context_turns
        self.summarize_after_turns = summarize_after_turns
        self.cache_ttl = cache_ttl
        self.cache_key_prefix = "chatbot:conversation_state:"

    def _get_cache_key(self, conversation_id: str) -> str:
        """Get cache key for conversation state."""
        return f"{self.cache_key_prefix}{conversation_id}"

    async def get_conversation_context(
        self,
        conversation_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get optimized conversation context for LLM.

        Args:
            conversation_id: Conversation ID
            conversation_history: Full conversation history

        Returns:
            Optimized context with summary and recent turns
        """
        try:
            # Get cached state
            state = await self._load_state(conversation_id)

            # Update state with new history
            total_turns = len(conversation_history) // 2  # User + assistant = 1 turn

            # Check if we need to summarize
            if total_turns > self.summarize_after_turns and not state.get("summary"):
                # Summarize old turns
                state["summary"] = await self._summarize_conversation(
                    conversation_history[:-self.max_context_turns]
                )
                state["summarized_up_to_turn"] = total_turns - self.max_context_turns
                state["last_summarized"] = datetime.utcnow().isoformat()

                # Save updated state
                await self._save_state(conversation_id, state)

            # Build optimized context
            context = {
                "summary": state.get("summary"),
                "recent_turns": conversation_history[-self.max_context_turns:],
                "total_turns": total_turns,
                "context_window": {
                    "start_turn": max(0, total_turns - self.max_context_turns),
                    "end_turn": total_turns,
                    "summarized_turns": state.get("summarized_up_to_turn", 0)
                }
            }

            return context

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            # Fallback to recent turns only
            return {
                "summary": None,
                "recent_turns": conversation_history[-self.max_context_turns:],
                "total_turns": len(conversation_history) // 2,
                "context_window": {
                    "start_turn": 0,
                    "end_turn": len(conversation_history) // 2,
                    "summarized_turns": 0
                }
            }

    async def _summarize_conversation(
        self,
        conversation_turns: List[Dict[str, Any]]
    ) -> str:
        """
        Summarize conversation turns using LLM.

        Args:
            conversation_turns: Turns to summarize

        Returns:
            Summary text
        """
        try:
            from ..llm.manager import LLMManager
            from ..llm.interface import LLMRequest

            # Build conversation text
            conversation_text = "\n\n".join([
                f"{msg['role'].title()}: {msg['content']}"
                for msg in conversation_turns
            ])

            # Create summarization prompt
            summary_prompt = f"""
            Summarize the following conversation between a user and an AI infrastructure assistant.
            Focus on key topics discussed, decisions made, and important context that should be
            remembered for the rest of the conversation.

            Conversation:
            {conversation_text}

            Provide a concise summary in 3-4 sentences covering the main points.
            """

            # Generate summary
            llm_manager = LLMManager()
            llm_request = LLMRequest(
                prompt=summary_prompt,
                model="gpt-4",
                temperature=0.3,
                max_tokens=300
            )

            response = await llm_manager.generate_response(llm_request)
            summary = response.content.strip()

            logger.info(f"Generated conversation summary: {len(conversation_turns)} turns")
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            # Fallback summary
            return "Previous conversation covered infrastructure planning and technical requirements."

    async def _load_state(self, conversation_id: str) -> Dict[str, Any]:
        """Load conversation state from cache."""
        try:
            cache_manager = await get_cache_manager()
            cache_key = self._get_cache_key(conversation_id)

            state = await cache_manager.get(cache_key)
            if state:
                return state

            # Initialize new state
            return {
                "summary": None,
                "summarized_up_to_turn": 0,
                "last_summarized": None,
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to load conversation state: {e}")
            return {}

    async def _save_state(self, conversation_id: str, state: Dict[str, Any]) -> bool:
        """Save conversation state to cache."""
        try:
            cache_manager = await get_cache_manager()
            cache_key = self._get_cache_key(conversation_id)

            state["updated_at"] = datetime.utcnow().isoformat()
            await cache_manager.set(cache_key, state, ttl=self.cache_ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to save conversation state: {e}")
            return False

    async def clear_state(self, conversation_id: str) -> bool:
        """Clear conversation state from cache."""
        try:
            cache_manager = await get_cache_manager()
            cache_key = self._get_cache_key(conversation_id)

            await cache_manager.delete(cache_key)
            logger.info(f"Cleared conversation state: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear conversation state: {e}")
            return False

    def get_context_for_llm(self, context: Dict[str, Any]) -> str:
        """
        Format conversation context for LLM prompt.

        Args:
            context: Context from get_conversation_context()

        Returns:
            Formatted context string
        """
        parts = []

        # Add summary if available
        if context.get("summary"):
            parts.append(f"Previous conversation summary:\n{context['summary']}\n")

        # Add recent turns
        if context.get("recent_turns"):
            parts.append("Recent conversation:")
            for msg in context["recent_turns"]:
                role = msg.get("role", "unknown").title()
                content = msg.get("content", "")
                parts.append(f"{role}: {content}")

        # Add context info
        window = context.get("context_window", {})
        if window.get("summarized_turns", 0) > 0:
            parts.append(
                f"\n(Showing turns {window['start_turn']}-{window['end_turn']} "
                f"of {context['total_turns']} total, with {window['summarized_turns']} "
                f"earlier turns summarized above)"
            )

        return "\n".join(parts)


# Global instance
_conversation_state_manager: Optional[ConversationStateManager] = None


def get_conversation_state_manager() -> ConversationStateManager:
    """Get or create global conversation state manager instance."""
    global _conversation_state_manager

    if _conversation_state_manager is None:
        _conversation_state_manager = ConversationStateManager()
        logger.info("Initialized conversation state manager")

    return _conversation_state_manager
