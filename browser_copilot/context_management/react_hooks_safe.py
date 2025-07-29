"""
Safe pre-model hooks with robust tool pair handling for small windows
"""

from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.messages.utils import trim_messages

from .base import ContextConfig


def create_safe_trim_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a safe pre-model hook for small context windows
    
    This hook ensures that even with very small windows:
    1. Tool call pairs are preserved
    2. At least some context is maintained
    3. No invalid message sequences are created
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def safe_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safe trimming that handles small windows gracefully
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Safe Trim Hook] Processing {len(messages)} messages")
            print(f"[Safe Trim Hook] Target window: {config.window_size} tokens")
        
        # For very small windows, use a simple approach
        if config.window_size < 5000:
            # Just keep the original prompt and the most recent complete interaction
            result = []
            
            # Always include the first message
            if messages:
                result.append(messages[0])
            
            # Work backwards to find the most recent complete interaction
            # (HumanMessage -> AIMessage -> ToolMessage sequence)
            i = len(messages) - 1
            temp_messages = []
            
            while i > 0:  # Skip first message (already included)
                msg = messages[i]
                temp_messages.insert(0, msg)
                
                # If we have a human message, we've found a complete interaction
                if isinstance(msg, HumanMessage):
                    result.extend(temp_messages)
                    break
                
                # If we have an AIMessage with tool calls, ensure we have all ToolMessages
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Collect all tool call IDs
                    needed_tool_ids = set()
                    for tc in msg.tool_calls:
                        tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                        if tc_id:
                            needed_tool_ids.add(tc_id)
                    
                    # Look forward to ensure we have all corresponding ToolMessages
                    j = i + 1
                    while j < len(messages) and needed_tool_ids:
                        if isinstance(messages[j], ToolMessage):
                            tool_id = getattr(messages[j], 'tool_call_id', None)
                            if tool_id in needed_tool_ids:
                                if messages[j] not in temp_messages:
                                    temp_messages.append(messages[j])
                                needed_tool_ids.remove(tool_id)
                        j += 1
                
                i -= 1
            
            # If we didn't find a complete interaction, just keep the last few messages
            if len(result) == 1 and len(messages) > 1:
                # Keep last 3-5 messages, ensuring tool pairs
                keep_count = min(5, len(messages) - 1)
                result.extend(messages[-keep_count:])
            
            if verbose:
                print(f"[Safe Trim Hook] Kept {len(result)} messages for small window")
            
            return {"llm_input_messages": result}
        
        # For larger windows, use standard trim_messages
        def token_counter(msgs):
            return sum(len(str(msg.content)) for msg in msgs) // 4
        
        try:
            trimmed_messages = trim_messages(
                messages,
                strategy="last",
                max_tokens=config.window_size,
                token_counter=token_counter,
                start_on="human",
                end_on=("human", "tool"),
            )
            
            # Ensure we have at least some messages
            if not trimmed_messages and messages:
                trimmed_messages = [messages[0]]
                if len(messages) > 1:
                    trimmed_messages.append(messages[-1])
            
        except Exception as e:
            if verbose:
                print(f"[Safe Trim Hook] trim_messages failed: {e}")
            # Fallback to simple last N messages
            trimmed_messages = messages[-10:] if len(messages) > 10 else messages
        
        if verbose:
            print(f"[Safe Trim Hook] Reduced to {len(trimmed_messages)} messages")
            reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            print(f"[Safe Trim Hook] Message reduction: {reduction:.1f}%")
        
        return {"llm_input_messages": trimmed_messages}
    
    return safe_trim_hook


def create_last_n_hook(
    n: int = 5,
    verbose: bool = False
) -> callable:
    """
    Create a hook that keeps exactly the last N messages
    
    This is the simplest approach for when you want exactly N recent messages.
    
    Args:
        n: Number of messages to keep
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def last_n_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Keep exactly the last N messages
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Last N Hook] Processing {len(messages)} messages")
            print(f"[Last N Hook] Keeping last {n} messages")
        
        # Always include the first message (original prompt)
        result = []
        if messages:
            result.append(messages[0])
        
        # Add the last N-1 messages (since we already have the first)
        if len(messages) > 1:
            last_messages = messages[-(n-1):] if len(messages) > n else messages[1:]
            result.extend(last_messages)
        
        if verbose:
            print(f"[Last N Hook] Kept {len(result)} messages")
        
        return {"llm_input_messages": result}
    
    return last_n_hook