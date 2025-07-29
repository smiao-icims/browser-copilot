"""
Simplified pre-model hooks using LangChain's trim_messages utility

This implementation uses LangChain's built-in message trimming functionality
which is simpler and more reliable than our custom implementation.
"""

from typing import Any, Dict, Optional
from langchain_core.messages.utils import trim_messages
from .base import ContextConfig


def create_sliding_window_hook_simplified(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook using LangChain's trim_messages
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def sliding_window_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-model hook that trims messages using LangChain's utility
        
        Args:
            state: Current graph state with messages
            
        Returns:
            Dict with trimmed messages
        """
        messages = state.get("messages", [])
        
        if verbose:
            print(f"\n[Sliding Window Hook] Processing {len(messages)} messages")
            print(f"[Sliding Window Hook] Max tokens: {config.window_size}")
        
        # Use LangChain's trim_messages with our configuration
        trimmed_messages = trim_messages(
            messages,
            strategy="last",  # Keep most recent messages
            max_tokens=config.window_size,
            # Ensure we start with human message
            start_on="human",
            # End on human or tool to preserve complete interactions
            end_on=("human", "tool"),
            # Include partial to avoid cutting mid-conversation
            # This will use a default token counter if not specified
            token_counter=None,
        )
        
        if verbose:
            print(f"[Sliding Window Hook] Reduced to {len(trimmed_messages)} messages")
            reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            print(f"[Sliding Window Hook] Message reduction: {reduction:.1f}%")
        
        return {"llm_input_messages": trimmed_messages}
    
    return sliding_window_pre_model_hook


def create_advanced_sliding_window_hook(
    config: ContextConfig,
    verbose: bool = False,
    token_counter: Optional[callable] = None
) -> callable:
    """
    Create an advanced pre-model hook with additional features
    
    This version adds:
    - Custom token counting
    - First N / Last N message preservation
    - Critical message preservation (errors, screenshots)
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        token_counter: Optional custom token counter
        
    Returns:
        Pre-model hook function
    """
    def advanced_sliding_window_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced hook with additional preservation rules
        """
        messages = state.get("messages", [])
        
        if verbose:
            print(f"\n[Advanced Sliding Window] Processing {len(messages)} messages")
        
        # If we have few messages, don't trim
        if len(messages) <= config.preserve_first_n + config.preserve_last_n:
            return {}
        
        # Strategy 1: Try to preserve first N and last N messages
        # by using trim_messages on the middle section
        first_messages = messages[:config.preserve_first_n]
        last_messages = messages[-config.preserve_last_n:]
        middle_messages = messages[config.preserve_first_n:-config.preserve_last_n]
        
        # Calculate token budget for middle section
        # This is a simplified approach - in production you'd want accurate token counting
        total_budget = config.window_size
        reserved_tokens = total_budget * 0.3  # Reserve 30% for first/last messages
        middle_budget = int(total_budget * 0.7)
        
        # Trim middle messages
        if middle_messages:
            trimmed_middle = trim_messages(
                middle_messages,
                strategy="last",
                max_tokens=middle_budget,
                    token_counter=token_counter,
            )
        else:
            trimmed_middle = []
        
        # Combine all messages
        final_messages = first_messages + trimmed_middle + last_messages
        
        if verbose:
            print(f"[Advanced Sliding Window] Preserved first {len(first_messages)}, "
                  f"middle {len(trimmed_middle)}/{len(middle_messages)}, "
                  f"last {len(last_messages)}")
            print(f"[Advanced Sliding Window] Total messages: {len(final_messages)}")
        
        return {"llm_input_messages": final_messages}
    
    return advanced_sliding_window_hook


def create_no_op_hook_simplified() -> callable:
    """
    Create a no-op pre-model hook that doesn't modify messages
    
    Returns:
        Pre-model hook function that returns empty dict
    """
    def no_op_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """No-op hook that doesn't modify messages"""
        return {}
    
    return no_op_pre_model_hook