"""
Sliding window context management strategy

This strategy maintains a sliding window of messages, preserving
important context while removing older, less relevant messages.
"""

from datetime import datetime, UTC
from typing import Any

from ..base import ContextConfig, ContextStrategy, Message, MessageImportance, MessageType
from ..metrics import ContextMetrics


class SlidingWindowStrategy(ContextStrategy):
    """
    Sliding window strategy that maintains a fixed-size context window.
    
    Features:
    - Preserves recent messages within window size
    - Always keeps critical messages (errors, screenshots)
    - Maintains first N and last N messages for context
    - Merges similar consecutive messages
    """
    
    def __init__(self):
        self.metrics = ContextMetrics(strategy_name="sliding-window")
    
    def process_messages(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """
        Process messages using sliding window approach.
        
        Args:
            messages: List of messages to process
            config: Context configuration
            
        Returns:
            Processed list of messages within token budget
        """
        start_time = datetime.now(UTC)
        
        # Record original metrics
        self.metrics.original_messages = len(messages)
        self.metrics.original_tokens = sum(msg.token_count for msg in messages)
        
        if not messages:
            return messages
        
        # If we're under the window size, return all messages
        total_tokens = sum(msg.token_count for msg in messages)
        if total_tokens <= config.window_size:
            self.metrics.processed_messages = len(messages)
            self.metrics.processed_tokens = total_tokens
            self.metrics.calculate_savings()
            return messages
        
        # Apply sliding window logic
        processed_messages = self._apply_sliding_window(messages, config)
        
        # Update metrics
        self.metrics.processed_messages = len(processed_messages)
        self.metrics.processed_tokens = sum(msg.token_count for msg in processed_messages)
        self.metrics.processing_time_ms = (
            (datetime.now(UTC) - start_time).total_seconds() * 1000
        )
        self.metrics.calculate_savings()
        
        return processed_messages
    
    def _apply_sliding_window(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """Apply the sliding window algorithm"""
        result = []
        
        # Step 1: Always preserve first N messages
        preserved_first = messages[:config.preserve_first_n]
        result.extend(preserved_first)
        self.metrics.messages_preserved += len(preserved_first)
        
        # Step 2: Always preserve last N messages
        preserved_last = messages[-config.preserve_last_n:]
        self.metrics.messages_preserved += len(preserved_last)
        
        # Step 3: Find critical messages to preserve (excluding already preserved ones)
        critical_messages = []
        for i, msg in enumerate(messages):
            # Skip if already in preserved first/last
            if i < config.preserve_first_n or i >= len(messages) - config.preserve_last_n:
                continue
            if self._should_preserve(msg, config):
                critical_messages.append((i, msg))
                self.metrics.critical_messages_kept += 1
        
        # Step 4: Build the window
        window_messages = []
        
        # IMPORTANT: Add ALL critical messages regardless of window size
        # This ensures tool call pairs are never broken
        for idx, msg in critical_messages:
            window_messages.append((idx, msg))
        
        # Calculate remaining budget after critical messages
        current_tokens = sum(msg.token_count for msg in result)
        current_tokens += sum(msg.token_count for msg in preserved_last)
        current_tokens += sum(msg.token_count for _, msg in critical_messages)
        
        # Fill remaining window with recent messages if we have budget
        middle_start = config.preserve_first_n
        middle_end = len(messages) - config.preserve_last_n
        
        # Get indices already in window
        window_indices = {idx for idx, _ in window_messages}
        
        if current_tokens < config.window_size:
            for i in range(middle_end - 1, middle_start - 1, -1):
                if i not in window_indices:
                    msg = messages[i]
                    if current_tokens + msg.token_count <= config.window_size:
                        window_messages.append((i, msg))
                        current_tokens += msg.token_count
                    else:
                        break
        
        # Sort window messages by original order
        window_messages.sort(key=lambda x: x[0])
        result.extend([msg for _, msg in window_messages])
        
        # Add preserved last messages
        result.extend(preserved_last)
        
        # Remove duplicates while preserving order
        seen = set()
        final_result = []
        for msg in result:
            msg_id = (msg.timestamp, msg.content[:50])  # Simple dedup key
            if msg_id not in seen:
                seen.add(msg_id)
                final_result.append(msg)
        
        self.metrics.windows_created = 1
        self.metrics.window_size = config.window_size
        
        return final_result
    
    def _should_preserve(self, message: Message, config: ContextConfig) -> bool:
        """Determine if a message should be preserved"""
        # Always preserve if explicitly marked
        if message.preserve:
            return True
        
        # Preserve errors
        if config.preserve_errors and message.importance == MessageImportance.CRITICAL:
            return True
        
        # Preserve screenshots
        if config.preserve_screenshots and message.tool_name == "browser_take_screenshot":
            return True
        
        # Preserve tool call pairs (AIMessage with tool_calls and corresponding ToolMessages)
        # This is handled by the preserve flag set in react_hooks.py
        
        # Preserve based on importance threshold
        importance_weight = config.importance_weights.get(
            message.importance, 0.5
        )
        return importance_weight >= 0.8
    
    def get_metrics(self) -> dict[str, Any]:
        """Get strategy metrics"""
        return self.metrics.to_dict()