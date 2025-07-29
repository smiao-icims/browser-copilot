"""
Advanced pre-model hooks with better handling of edge cases

This module provides more sophisticated hooks that handle cases where
LangChain's trim_messages might return suboptimal results.
"""

from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.utils import trim_messages

from .base import ContextConfig


def create_smart_trim_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a smarter pre-model hook that handles edge cases better
    
    This hook:
    1. Tries LangChain's trim_messages first
    2. Falls back to custom logic if needed
    3. Always ensures some context is preserved
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def smart_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart trimming that handles edge cases
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Smart Trim Hook] Processing {len(messages)} messages")
            print(f"[Smart Trim Hook] Max tokens: {config.window_size}")
        
        # Simple token counter
        def token_counter(msgs):
            return sum(len(str(msg.content)) for msg in msgs) // 4
        
        # Try different strategies to get a good result
        trimmed_messages = []
        
        # Strategy 1: Try standard trim_messages
        try:
            trimmed_messages = trim_messages(
                messages,
                strategy="last",
                max_tokens=config.window_size,
                token_counter=token_counter,
                start_on="human",
                end_on=("human", "tool"),
            )
        except Exception as e:
            if verbose:
                print(f"[Smart Trim Hook] trim_messages failed: {e}")
        
        # Strategy 2: If we got too few messages, try without start_on constraint
        if len(trimmed_messages) < 3 and len(messages) > 3:
            try:
                trimmed_messages = trim_messages(
                    messages,
                    strategy="last",
                    max_tokens=config.window_size,
                    token_counter=token_counter,
                    # Remove start_on constraint
                    end_on=("human", "tool"),
                )
                if verbose:
                    print(f"[Smart Trim Hook] Retried without start_on constraint, got {len(trimmed_messages)} messages")
            except:
                pass
        
        # Strategy 3: If still empty or too few, use custom logic
        if len(trimmed_messages) < 2:
            if verbose:
                print(f"[Smart Trim Hook] Using custom fallback logic")
            
            # Always include the first message (original prompt)
            result = [messages[0]] if messages else []
            
            # Calculate how many recent messages we can fit
            remaining_budget = config.window_size - token_counter(result)
            
            # Add recent messages until we hit the budget
            for msg in reversed(messages[1:]):
                msg_tokens = token_counter([msg])
                if msg_tokens <= remaining_budget:
                    result.insert(1, msg)  # Insert after the first message
                    remaining_budget -= msg_tokens
                else:
                    break
            
            # Ensure we have at least the most recent message
            if len(result) == 1 and len(messages) > 1:
                result.append(messages[-1])
            
            trimmed_messages = result
        
        # Final check: Ensure tool call pairs are preserved
        trimmed_messages = _ensure_tool_pairs(trimmed_messages, messages, verbose)
        
        if verbose:
            print(f"[Smart Trim Hook] Final result: {len(trimmed_messages)} messages")
            reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            print(f"[Smart Trim Hook] Message reduction: {reduction:.1f}%")
        
        return {"llm_input_messages": trimmed_messages}
    
    return smart_trim_hook


def _ensure_tool_pairs(
    trimmed: List[BaseMessage], 
    original: List[BaseMessage],
    verbose: bool = False
) -> List[BaseMessage]:
    """
    Ensure AIMessage/ToolMessage pairs are preserved
    """
    # Build index of messages
    trimmed_indices = []
    for t_msg in trimmed:
        for i, o_msg in enumerate(original):
            if t_msg is o_msg or (
                type(t_msg) == type(o_msg) and 
                t_msg.content == o_msg.content
            ):
                trimmed_indices.append(i)
                break
    
    # Check for orphaned tool messages
    result = list(trimmed)
    added_count = 0
    
    for i, msg in enumerate(trimmed):
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            # Find the corresponding AIMessage
            tool_call_id = msg.tool_call_id
            ai_msg_idx = None
            
            # Look backwards in original messages
            orig_idx = trimmed_indices[i] if i < len(trimmed_indices) else -1
            for j in range(orig_idx - 1, -1, -1):
                if j not in trimmed_indices:
                    o_msg = original[j]
                    if isinstance(o_msg, AIMessage) and hasattr(o_msg, 'tool_calls'):
                        for tc in (o_msg.tool_calls or []):
                            tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                            if tc_id == tool_call_id:
                                ai_msg_idx = j
                                break
                    if ai_msg_idx is not None:
                        break
            
            # Add the AIMessage if missing
            if ai_msg_idx is not None and ai_msg_idx not in trimmed_indices:
                result.insert(i + added_count, original[ai_msg_idx])
                added_count += 1
                if verbose:
                    print(f"[Smart Trim Hook] Added missing AIMessage for tool_call_id: {tool_call_id}")
    
    return result


def create_adaptive_trim_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create an adaptive hook that adjusts strategy based on message patterns
    
    This hook analyzes the message pattern and chooses the best strategy:
    - For long conversations: aggressive trimming
    - For tool-heavy interactions: preserve tool context
    - For error scenarios: preserve error context
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def adaptive_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adaptive trimming based on conversation patterns
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # Analyze message patterns
        tool_message_count = sum(1 for m in messages if isinstance(m, ToolMessage))
        ai_message_count = sum(1 for m in messages if isinstance(m, AIMessage))
        error_count = sum(1 for m in messages if "error" in str(m.content).lower())
        
        tool_density = tool_message_count / len(messages) if messages else 0
        
        if verbose:
            print(f"\n[Adaptive Trim Hook] Analyzing {len(messages)} messages")
            print(f"[Adaptive Trim Hook] Tool density: {tool_density:.2%}, Errors: {error_count}")
        
        # Choose strategy based on patterns
        if error_count > 0:
            # Error scenario: preserve more context around errors
            strategy = "first"  # Keep older messages where error might have originated
            window_multiplier = 1.5  # Increase window size
        elif tool_density > 0.6:
            # Tool-heavy: ensure tool pairs are preserved
            strategy = "last"
            window_multiplier = 1.2
        else:
            # Normal conversation: standard trimming
            strategy = "last"
            window_multiplier = 1.0
        
        adjusted_window = int(config.window_size * window_multiplier)
        
        if verbose:
            print(f"[Adaptive Trim Hook] Using strategy: {strategy}, window: {adjusted_window}")
        
        # Apply trimming with chosen strategy
        def token_counter(msgs):
            return sum(len(str(msg.content)) for msg in msgs) // 4
        
        try:
            trimmed_messages = trim_messages(
                messages,
                strategy=strategy,
                max_tokens=adjusted_window,
                token_counter=token_counter,
            )
        except:
            # Fallback to last N messages
            budget = adjusted_window
            trimmed_messages = []
            for msg in reversed(messages):
                if token_counter(trimmed_messages + [msg]) <= budget:
                    trimmed_messages.insert(0, msg)
                else:
                    break
        
        # Ensure we have minimum context
        if len(trimmed_messages) < 2 and len(messages) >= 2:
            trimmed_messages = [messages[0], messages[-1]]
        
        if verbose:
            print(f"[Adaptive Trim Hook] Reduced to {len(trimmed_messages)} messages")
        
        return {"llm_input_messages": trimmed_messages}
    
    return adaptive_trim_hook