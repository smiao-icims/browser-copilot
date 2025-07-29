"""
Pre-model hooks for ReAct agents to manage message history (v2)

This implementation follows the official LangGraph pattern for managing
message history using RemoveMessage objects.
"""

from typing import Any, Dict, List, Union
from datetime import datetime, UTC

from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage, RemoveMessage
)

from .base import Message, MessageType, ContextConfig
from .manager import BrowserCopilotContextManager


def create_sliding_window_hook_v2(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook that manages message history using RemoveMessage
    
    This follows the pattern from:
    https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    # Create context manager
    manager = BrowserCopilotContextManager(
        config=config,
        strategy="sliding-window"
    )
    
    def sliding_window_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-model hook that manages message history by returning RemoveMessage objects
        
        Args:
            state: Current graph state with messages
            
        Returns:
            Dict with messages including RemoveMessage objects
        """
        messages = state.get("messages", [])
        
        if verbose:
            print(f"\n[Sliding Window Hook V2] Processing {len(messages)} messages")
        
        # If we're under the window size, don't remove anything
        total_tokens = _estimate_tokens(messages)
        if total_tokens <= config.window_size:
            if verbose:
                print(f"[Sliding Window Hook V2] Under window size ({total_tokens} <= {config.window_size}), no removal needed")
            return {}
        
        # Determine which messages to keep
        messages_to_keep = _select_messages_to_keep(messages, config, verbose)
        
        # Create RemoveMessage objects for messages to remove
        remove_messages = []
        for i, msg in enumerate(messages):
            if i not in messages_to_keep:
                # Get the message ID
                msg_id = getattr(msg, 'id', None)
                if msg_id:
                    remove_messages.append(RemoveMessage(id=msg_id))
                    if verbose:
                        print(f"[Sliding Window Hook V2] Removing message {i} (id={msg_id})")
        
        if verbose:
            print(f"[Sliding Window Hook V2] Removing {len(remove_messages)} messages")
            print(f"[Sliding Window Hook V2] Keeping {len(messages_to_keep)} messages")
        
        # Return the RemoveMessage objects to actually remove from state
        return {"messages": remove_messages}
    
    # Store manager reference for metrics access
    sliding_window_pre_model_hook.context_manager = manager
    
    return sliding_window_pre_model_hook


def _estimate_tokens(messages: List[BaseMessage]) -> int:
    """Estimate token count for messages"""
    # Simple estimation: ~4 chars per token
    total_chars = sum(len(str(msg.content)) for msg in messages)
    return total_chars // 4


def _select_messages_to_keep(
    messages: List[BaseMessage], 
    config: ContextConfig,
    verbose: bool = False
) -> set[int]:
    """
    Select which message indices to keep based on sliding window logic
    
    Returns:
        Set of message indices to keep
    """
    if not messages:
        return set()
    
    keep_indices = set()
    
    # Always keep first N messages
    for i in range(min(config.preserve_first_n, len(messages))):
        keep_indices.add(i)
    
    # Always keep last N messages
    start_last = max(0, len(messages) - config.preserve_last_n)
    for i in range(start_last, len(messages)):
        keep_indices.add(i)
    
    # Keep critical messages (errors, tool responses with screenshots)
    for i, msg in enumerate(messages):
        if _is_critical_message(msg, config):
            keep_indices.add(i)
            if verbose:
                print(f"[Sliding Window Hook V2] Keeping critical message {i}")
    
    # Fill remaining budget with recent messages
    remaining_budget = config.window_size
    for idx in sorted(keep_indices):
        msg = messages[idx]
        remaining_budget -= _estimate_tokens([msg])
    
    # Add recent messages until we hit the budget
    for i in range(len(messages) - 1, -1, -1):
        if i not in keep_indices:
            msg_tokens = _estimate_tokens([messages[i]])
            if msg_tokens <= remaining_budget:
                keep_indices.add(i)
                remaining_budget -= msg_tokens
    
    return keep_indices


def _is_critical_message(msg: BaseMessage, config: ContextConfig) -> bool:
    """Check if a message is critical and should be preserved"""
    # Keep tool messages that might have screenshots or errors
    if isinstance(msg, ToolMessage):
        content_lower = str(msg.content).lower()
        if config.preserve_screenshots and "screenshot" in content_lower:
            return True
        if config.preserve_errors and "error" in content_lower:
            return True
    
    # Keep AI messages that reference errors
    if isinstance(msg, AIMessage):
        content_lower = str(msg.content).lower()
        if config.preserve_errors and "error" in content_lower:
            return True
    
    return False


def create_no_op_hook_v2() -> callable:
    """
    Create a no-op pre-model hook that doesn't modify messages
    
    Returns:
        Pre-model hook function that returns empty dict
    """
    def no_op_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """No-op hook that doesn't modify messages"""
        # Return empty dict to keep messages unchanged
        return {}
    
    return no_op_pre_model_hook