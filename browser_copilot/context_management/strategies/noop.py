"""
No-op context management strategy - baseline for comparison

This strategy does nothing and returns all messages as-is,
serving as a baseline to measure the effectiveness of other strategies.
"""

from typing import Any

from ..base import ContextConfig, ContextStrategy, Message


class NoOpStrategy(ContextStrategy):
    """
    No-operation strategy that returns all messages unchanged.
    
    This serves as a baseline for comparing the effectiveness
    of other context management strategies.
    """
    
    def __init__(self):
        self._call_count = 0
        self._total_messages_processed = 0
        self._total_tokens_processed = 0
    
    def process_messages(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """
        Return all messages unchanged.
        
        Args:
            messages: List of messages to process
            config: Context configuration (ignored)
            
        Returns:
            The same list of messages, unmodified
        """
        self._call_count += 1
        self._total_messages_processed += len(messages)
        self._total_tokens_processed += sum(msg.token_count for msg in messages)
        
        # Return messages as-is - no processing
        return messages
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get metrics about the no-op strategy.
        
        Returns:
            Dictionary with strategy metrics
        """
        return {
            "strategy": "no-op",
            "call_count": self._call_count,
            "total_messages_processed": self._total_messages_processed,
            "total_tokens_processed": self._total_tokens_processed,
            "reduction_percentage": 0.0,  # No reduction
            "messages_removed": 0,
            "tokens_saved": 0,
        }