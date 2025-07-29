"""
Fixed pre-model hooks for ReAct agents with proper sliding window

This implementation directly processes messages without a persistent manager.
"""

from typing import Any, Dict, List, Set, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from .base import ContextConfig


def create_sliding_window_hook_fixed(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook that properly applies sliding window trimming
    
    This version:
    1. Calculates tokens correctly for all messages
    2. Actually trims when exceeding window size
    3. Preserves tool pairs
    4. Works with the stateless nature of hooks
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def sliding_window_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sliding window directly to messages"""
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # Calculate total tokens
        def count_tokens(msg: BaseMessage) -> int:
            """Count tokens in a message"""
            if hasattr(msg, 'content') and msg.content:
                return len(str(msg.content)) // 4
            return 0
        
        total_tokens = sum(count_tokens(msg) for msg in messages)
        
        if verbose:
            print(f"\n[Sliding Window Hook FIXED] Processing {len(messages)} messages")
            print(f"[Sliding Window Hook FIXED] Total tokens: {total_tokens:,}")
            print(f"[Sliding Window Hook FIXED] Window size: {config.window_size:,}")
        
        # If under window size, return all
        if total_tokens <= config.window_size:
            if verbose:
                print(f"[Sliding Window Hook FIXED] Under window size, keeping all messages")
            return {}  # Return empty dict to keep original messages
        
        # Need to trim - build tool dependency map first
        tool_pairs = {}  # tool_call_id -> (ai_msg_idx, tool_msg_idx)
        
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id:
                        tool_pairs[tc_id] = (i, None)
            elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                tc_id = msg.tool_call_id
                if tc_id in tool_pairs:
                    ai_idx, _ = tool_pairs[tc_id]
                    tool_pairs[tc_id] = (ai_idx, i)
        
        # Build groups of messages that must stay together
        groups = []
        processed_indices = set()
        
        for i, msg in enumerate(messages):
            if i in processed_indices:
                continue
            
            group = [i]
            processed_indices.add(i)
            
            # If it's an AIMessage with tool calls, add all its tool responses
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id and tc_id in tool_pairs:
                        _, tool_idx = tool_pairs[tc_id]
                        if tool_idx is not None and tool_idx not in processed_indices:
                            group.append(tool_idx)
                            processed_indices.add(tool_idx)
            
            # If it's a ToolMessage, ensure its AIMessage is in the same group
            elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                tc_id = msg.tool_call_id
                if tc_id in tool_pairs:
                    ai_idx, _ = tool_pairs[tc_id]
                    if ai_idx not in processed_indices:
                        group.insert(0, ai_idx)  # AI message should come first
                        processed_indices.add(ai_idx)
            
            groups.append(sorted(group))  # Keep indices in order within group
        
        # Calculate group sizes
        group_sizes = []
        for group in groups:
            size = sum(count_tokens(messages[idx]) for idx in group)
            group_sizes.append((group, size))
        
        if verbose:
            print(f"[Sliding Window Hook FIXED] Created {len(groups)} message groups")
        
        # Always keep first and last N groups
        selected_indices = set()
        current_tokens = 0
        
        # Add first N messages
        for i in range(min(config.preserve_first_n, len(messages))):
            selected_indices.add(i)
            current_tokens += count_tokens(messages[i])
        
        # Add last N messages
        for i in range(max(0, len(messages) - config.preserve_last_n), len(messages)):
            if i not in selected_indices:
                selected_indices.add(i)
                current_tokens += count_tokens(messages[i])
        
        # Fill remaining budget with most recent complete groups
        for group, size in reversed(group_sizes):
            # Check if any message in group is already selected
            group_selected = any(idx in selected_indices for idx in group)
            
            if not group_selected and current_tokens + size <= config.window_size:
                for idx in group:
                    selected_indices.add(idx)
                current_tokens += size
            elif group_selected:
                # Ensure all messages in group are selected (for tool pairs)
                for idx in group:
                    if idx not in selected_indices:
                        selected_indices.add(idx)
                        current_tokens += count_tokens(messages[idx])
        
        # Build trimmed message list
        trimmed_messages = [messages[i] for i in sorted(selected_indices)]
        
        if verbose:
            trimmed_tokens = sum(count_tokens(msg) for msg in trimmed_messages)
            reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100)
            token_reduction = ((total_tokens - trimmed_tokens) / total_tokens * 100)
            
            print(f"[Sliding Window Hook FIXED] === RESULTS ===")
            print(f"[Sliding Window Hook FIXED] Messages: {len(messages)} → {len(trimmed_messages)} ({reduction:.1f}% reduction)")
            print(f"[Sliding Window Hook FIXED] Tokens: {total_tokens:,} → {trimmed_tokens:,} ({token_reduction:.1f}% reduction)")
            print(f"[Sliding Window Hook FIXED] Selected indices: {sorted(selected_indices)}")
        
        # Return trimmed messages
        return {"llm_input_messages": trimmed_messages}
    
    return sliding_window_hook