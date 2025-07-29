"""
Context management strategy using LangChain's trim_messages utility

This provides a simpler, battle-tested approach using LangChain's
built-in message trimming functionality.
"""

from datetime import datetime, UTC
from typing import Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.messages.utils import trim_messages

from ..base import ContextConfig, ContextStrategy, Message, MessageType
from ..metrics import ContextMetrics


class LangChainTrimStrategy(ContextStrategy):
    """
    Strategy that uses LangChain's trim_messages utility
    
    This is a simpler approach that leverages LangChain's built-in
    message trimming functionality which handles tool call pairs correctly.
    """
    
    def __init__(self):
        self.metrics = ContextMetrics(strategy_name="langchain-trim")
        self._original_langchain_messages: list[BaseMessage] = []
    
    def process_messages(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """
        Process messages using LangChain's trim_messages
        
        Args:
            messages: List of our Message objects
            config: Context configuration
            
        Returns:
            Processed list of messages
        """
        start_time = datetime.now(UTC)
        
        # Record original metrics
        self.metrics.original_messages = len(messages)
        self.metrics.original_tokens = sum(msg.token_count for msg in messages)
        
        if not messages:
            return messages
        
        # We need the original LangChain messages for trim_messages to work
        # This should be set by the hook before calling process_messages
        if not self._original_langchain_messages:
            # Fallback: return all messages if we don't have LangChain messages
            self.metrics.processed_messages = len(messages)
            self.metrics.processed_tokens = self.metrics.original_tokens
            return messages
        
        # Use LangChain's trim_messages
        trimmed_langchain = trim_messages(
            self._original_langchain_messages,
            strategy="last",  # Keep most recent messages
            max_tokens=config.window_size,
            # Ensure we start with human message
            start_on="human",
            # End on human or tool to preserve complete interactions
            end_on=("human", "tool"),
            # Don't include partial messages
        )
        
        # Find which of our messages correspond to the trimmed LangChain messages
        # We'll match by content since that's the most reliable
        trimmed_contents = {msg.content for msg in trimmed_langchain}
        
        # Filter our messages to match what trim_messages kept
        result = []
        for msg in messages:
            if msg.content in trimmed_contents:
                result.append(msg)
        
        # Update metrics
        self.metrics.processed_messages = len(result)
        self.metrics.processed_tokens = sum(msg.token_count for msg in result)
        self.metrics.processing_time_ms = (
            (datetime.now(UTC) - start_time).total_seconds() * 1000
        )
        self.metrics.calculate_savings()
        
        return result
    
    def set_langchain_messages(self, messages: list[BaseMessage]) -> None:
        """
        Set the original LangChain messages for processing
        
        This needs to be called before process_messages to provide
        the original LangChain message objects.
        """
        self._original_langchain_messages = messages
    
    def get_metrics(self) -> dict[str, Any]:
        """Get strategy metrics"""
        return self.metrics.to_dict()


class AdvancedLangChainTrimStrategy(ContextStrategy):
    """
    Advanced strategy using LangChain's trim_messages with custom rules
    
    This adds support for:
    - Preserving first N and last N messages
    - Custom token counting
    - Critical message preservation
    """
    
    def __init__(self, token_counter: Optional[callable] = None):
        self.metrics = ContextMetrics(strategy_name="langchain-trim-advanced")
        self._original_langchain_messages: list[BaseMessage] = []
        self.token_counter = token_counter
    
    def process_messages(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """
        Process messages with advanced trimming rules
        """
        start_time = datetime.now(UTC)
        
        # Record original metrics
        self.metrics.original_messages = len(messages)
        self.metrics.original_tokens = sum(msg.token_count for msg in messages)
        
        if not messages or not self._original_langchain_messages:
            return messages
        
        # If we have few messages, don't trim
        if len(messages) <= config.preserve_first_n + config.preserve_last_n:
            self.metrics.processed_messages = len(messages)
            self.metrics.processed_tokens = self.metrics.original_tokens
            return messages
        
        # Split messages into three sections
        first_lc = self._original_langchain_messages[:config.preserve_first_n]
        last_lc = self._original_langchain_messages[-config.preserve_last_n:]
        middle_lc = self._original_langchain_messages[config.preserve_first_n:-config.preserve_last_n]
        
        # Calculate token budget for middle section
        total_budget = config.window_size
        # Reserve some tokens for first/last messages (rough estimate)
        middle_budget = int(total_budget * 0.7)
        
        # Trim middle messages
        trimmed_middle = []
        if middle_lc:
            trimmed_middle = trim_messages(
                middle_lc,
                strategy="last",
                max_tokens=middle_budget,
                    token_counter=self.token_counter,
            )
        
        # Combine all LangChain messages
        final_langchain = first_lc + trimmed_middle + last_lc
        
        # Map back to our messages
        final_contents = {msg.content for msg in final_langchain}
        result = [msg for msg in messages if msg.content in final_contents]
        
        # Update metrics
        self.metrics.processed_messages = len(result)
        self.metrics.processed_tokens = sum(msg.token_count for msg in result)
        self.metrics.messages_preserved = len(first_lc) + len(last_lc)
        self.metrics.processing_time_ms = (
            (datetime.now(UTC) - start_time).total_seconds() * 1000
        )
        self.metrics.calculate_savings()
        
        return result
    
    def set_langchain_messages(self, messages: list[BaseMessage]) -> None:
        """Set the original LangChain messages"""
        self._original_langchain_messages = messages
    
    def get_metrics(self) -> dict[str, Any]:
        """Get strategy metrics"""
        return self.metrics.to_dict()