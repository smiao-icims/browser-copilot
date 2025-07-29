"""
Reverse-order pre-model hooks that build context from most recent messages

This approach works backwards to ensure tool pairs are always kept together.
"""

from typing import Any, Dict, List, Set, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from .base import ContextConfig


def create_reverse_trim_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook that builds context in reverse order
    
    This ensures tool pairs are always kept together by:
    1. Starting from the most recent messages
    2. When including a ToolMessage, always including its AIMessage
    3. Stopping when token budget is exceeded
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def reverse_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trim messages by building from most recent, preserving tool pairs
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Reverse Trim Hook] Processing {len(messages)} messages")
            print(f"[Reverse Trim Hook] Max tokens: {config.window_size}")
            # Calculate total tokens in full state
            full_state_tokens = count_tokens(messages)
            print(f"[Reverse Trim Hook] Full state tokens: {full_state_tokens:,}")
        
        # Simple content-only token counter
        # This counts only the message content, not metadata or formatting
        def count_tokens(msgs: List[BaseMessage]) -> int:
            total_chars = 0
            for msg in msgs:
                if msg.content:
                    total_chars += len(str(msg.content))
            return total_chars // 4  # Rough estimate: 4 chars per token
        
        # Always include the first message (original prompt)
        trimmed_messages = []
        included_indices = set()
        token_count = 0
        
        # Add first message if it fits
        if messages:
            first_msg_tokens = count_tokens([messages[0]])
            if first_msg_tokens < config.window_size:
                trimmed_messages.append(messages[0])
                included_indices.add(0)
                token_count += first_msg_tokens
        
        # Build a map of tool_call_id to AIMessage index for quick lookup
        tool_call_to_ai_idx = {}
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tc_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                    if tc_id:
                        tool_call_to_ai_idx[tc_id] = i
        
        # Work backwards from the most recent message
        # We'll build a list of (index, message) tuples and sort at the end
        messages_to_include = []  # List of (original_index, message) tuples
        
        for i in range(len(messages) - 1, 0, -1):  # Skip first message (already handled)
            if i in included_indices:
                continue
                
            current_msg = messages[i]
            current_group = []  # Messages to add as a group
            
            # If it's a ToolMessage, we need to include its AIMessage
            if isinstance(current_msg, ToolMessage) and hasattr(current_msg, 'tool_call_id'):
                tool_call_id = current_msg.tool_call_id
                
                # Find the corresponding AIMessage
                if tool_call_id in tool_call_to_ai_idx:
                    ai_idx = tool_call_to_ai_idx[tool_call_id]
                    
                    # Only add if not already included
                    if ai_idx not in included_indices:
                        current_group.append((ai_idx, messages[ai_idx]))
                        included_indices.add(ai_idx)
                
                # Add the ToolMessage itself
                current_group.append((i, current_msg))
                included_indices.add(i)
                
            # If it's an AIMessage with tool calls, check if we have all its tool responses
            elif isinstance(current_msg, AIMessage) and hasattr(current_msg, 'tool_calls') and current_msg.tool_calls:
                # First add the AIMessage
                current_group.append((i, current_msg))
                included_indices.add(i)
                
                # Then find and add all corresponding ToolMessages
                for tool_call in current_msg.tool_calls:
                    tc_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                    if tc_id:
                        # Look forward for ToolMessages with this ID
                        for j in range(i + 1, len(messages)):
                            if j not in included_indices and isinstance(messages[j], ToolMessage):
                                if hasattr(messages[j], 'tool_call_id') and messages[j].tool_call_id == tc_id:
                                    current_group.append((j, messages[j]))
                                    included_indices.add(j)
                                    break
            else:
                # Regular message (Human, System, or AI without tool calls)
                current_group.append((i, current_msg))
                included_indices.add(i)
            
            # Check if adding these messages would exceed token budget
            group_messages = [msg for _, msg in current_group]
            new_token_count = count_tokens(group_messages)
            if token_count + new_token_count > config.window_size:
                if verbose:
                    print(f"[Reverse Trim Hook] Stopping at message {i}, would exceed token budget")
                    print(f"[Reverse Trim Hook]   Group size: {len(current_group)} messages, {new_token_count} tokens")
                    # Show details of large messages
                    for idx, msg in current_group:
                        msg_tokens = count_tokens([msg])
                        if msg_tokens > 1000:  # Show large messages
                            content_preview = str(msg.content)[:100] if msg.content else ""
                            print(f"[Reverse Trim Hook]   Message {idx}: {type(msg).__name__} - {msg_tokens} tokens")
                            print(f"[Reverse Trim Hook]     Preview: {content_preview}...")
                # Remove from included_indices since we're not adding them
                for idx, _ in current_group:
                    included_indices.discard(idx)
                break
            
            # Add all messages from this group
            messages_to_include.extend(current_group)
            token_count += new_token_count
        
        # Sort all messages by their original index to maintain order
        messages_to_include.sort(key=lambda x: x[0])
        
        # Extract just the messages and combine with first message
        for _, msg in messages_to_include:
            trimmed_messages.append(msg)
        
        # CRITICAL: Post-process to ensure ALL tool responses are included
        # for any AIMessage with tool_calls that we kept
        final_check_additions = []
        for i, msg in enumerate(trimmed_messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tc_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                    if tc_id:
                        # Check if we have the corresponding ToolMessage
                        has_response = any(
                            isinstance(m, ToolMessage) and 
                            hasattr(m, 'tool_call_id') and 
                            m.tool_call_id == tc_id 
                            for m in trimmed_messages
                        )
                        if not has_response:
                            # Find it in original messages
                            for j, orig_msg in enumerate(messages):
                                if (isinstance(orig_msg, ToolMessage) and 
                                    hasattr(orig_msg, 'tool_call_id') and 
                                    orig_msg.tool_call_id == tc_id):
                                    final_check_additions.append((j, orig_msg))
                                    if verbose:
                                        print(f"[Reverse Trim Hook] Adding missing ToolMessage for {tc_id}")
                                    break
        
        # Add any missing tool responses and re-sort
        if final_check_additions:
            all_messages = [(i, msg) for i, msg in enumerate(messages) if msg in trimmed_messages]
            all_messages.extend(final_check_additions)
            all_messages.sort(key=lambda x: x[0])
            trimmed_messages = [msg for _, msg in all_messages]
        
        if verbose:
            print(f"[Reverse Trim Hook] === RESULTS ===")
            print(f"[Reverse Trim Hook] State messages: {len(messages)} → LLM messages: {len(trimmed_messages)}")
            print(f"[Reverse Trim Hook] State tokens: {count_tokens(messages):,} → LLM tokens: {token_count:,}")
            
            # Calculate reductions
            msg_reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            token_reduction = ((count_tokens(messages) - token_count) / count_tokens(messages) * 100) if messages else 0
            
            print(f"[Reverse Trim Hook] Message reduction: {msg_reduction:.1f}% ({len(messages) - len(trimmed_messages)} messages removed)")
            print(f"[Reverse Trim Hook] Token reduction: {token_reduction:.1f}% ({count_tokens(messages) - token_count:,} tokens saved)")
            print(f"[Reverse Trim Hook] Budget utilization: {token_count / config.window_size * 100:.1f}% of {config.window_size:,} tokens")
            
            # Validate tool pairs
            tool_pairs_valid = validate_tool_pairs(trimmed_messages, verbose)
            if not tool_pairs_valid:
                print(f"[Reverse Trim Hook] WARNING: Tool pair validation failed!")
            
            # Debug: Show message types in final output
            msg_summary = []
            for i, msg in enumerate(trimmed_messages):
                msg_type = type(msg).__name__
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tc_ids = [tc.get('id', '?') if isinstance(tc, dict) else getattr(tc, 'id', '?') for tc in msg.tool_calls]
                    msg_summary.append(f"{i}: {msg_type} (tool_calls: {tc_ids})")
                elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                    msg_summary.append(f"{i}: {msg_type} (tool_call_id: {msg.tool_call_id})")
                else:
                    msg_summary.append(f"{i}: {msg_type}")
            print(f"[Reverse Trim Hook] Message sequence: {', '.join(msg_summary[:10])}{'...' if len(msg_summary) > 10 else ''}")
        
        return {"llm_input_messages": trimmed_messages}
    
    return reverse_trim_hook


def validate_tool_pairs(messages: List[BaseMessage], verbose: bool = False) -> bool:
    """
    Validate that all AIMessages with tool_calls have corresponding ToolMessages
    
    Args:
        messages: List of messages to validate
        verbose: Enable verbose logging
        
    Returns:
        True if all tool pairs are complete, False otherwise
    """
    # Collect all tool_call_ids from AIMessages
    expected_tool_ids = set()
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    expected_tool_ids.add(tc_id)
    
    # Collect all tool_call_ids from ToolMessages
    found_tool_ids = set()
    for msg in messages:
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            found_tool_ids.add(msg.tool_call_id)
    
    # Check for missing tool responses
    missing_ids = expected_tool_ids - found_tool_ids
    if missing_ids and verbose:
        print(f"[Validation] Missing tool responses for IDs: {missing_ids}")
    
    # Check for orphaned tool messages
    orphaned_ids = found_tool_ids - expected_tool_ids
    if orphaned_ids and verbose:
        print(f"[Validation] Orphaned tool messages with IDs: {orphaned_ids}")
    
    return len(missing_ids) == 0


def create_smart_reverse_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a smarter reverse hook with additional optimizations
    
    This version includes:
    1. Priority scoring for different message types
    2. Intelligent grouping of related messages
    3. Better handling of error messages
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def smart_reverse_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart reverse trimming with priorities
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Smart Reverse Hook] Processing {len(messages)} messages")
        
        # Score messages by importance
        def score_message(msg: BaseMessage, index: int) -> float:
            """Higher score = more important to keep"""
            score = 0.0
            
            # Recency bonus (more recent = higher score)
            recency_score = index / len(messages) * 10
            score += recency_score
            
            # Type-based scoring
            if isinstance(msg, HumanMessage):
                score += 5  # Human messages are important
            elif isinstance(msg, ToolMessage):
                score += 8  # Tool responses are critical
                # Error responses are even more important
                if "error" in str(msg.content).lower():
                    score += 10
            elif isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    score += 7  # AI messages with tool calls are important
                else:
                    score += 3  # Regular AI messages less so
            
            # Content-based scoring
            content = str(msg.content).lower()
            if "error" in content or "exception" in content:
                score += 15
            if "screenshot" in content:
                score += 5
            
            return score
        
        # Create groups of related messages (tool call + responses)
        message_groups = []
        current_group = []
        
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage) and current_group:
                # New interaction starting, save previous group
                message_groups.append(current_group)
                current_group = [(i, msg)]
            else:
                current_group.append((i, msg))
        
        if current_group:
            message_groups.append(current_group)
        
        # Score each group
        scored_groups = []
        for group in message_groups:
            group_score = sum(score_message(msg, idx) for idx, msg in group) / len(group)
            scored_groups.append((group_score, group))
        
        # Sort groups by score (highest first)
        scored_groups.sort(key=lambda x: x[0], reverse=True)
        
        # Build result by adding groups until we hit token limit
        result_messages = []
        included_indices = set()
        token_count = 0
        
        def count_tokens(msgs: List[BaseMessage]) -> int:
            total_chars = 0
            for msg in msgs:
                if msg.content:
                    total_chars += len(str(msg.content))
            return total_chars // 4
        
        # Always include first message
        if messages:
            result_messages.append(messages[0])
            included_indices.add(0)
            token_count = count_tokens([messages[0]])
        
        # Add groups by priority
        for score, group in scored_groups:
            group_messages = [msg for idx, msg in group if idx not in included_indices]
            group_tokens = count_tokens(group_messages)
            
            if token_count + group_tokens <= config.window_size:
                # Add group in original order
                for idx, msg in sorted(group, key=lambda x: x[0]):
                    if idx not in included_indices:
                        result_messages.append(msg)
                        included_indices.add(idx)
                token_count += group_tokens
            elif verbose:
                print(f"[Smart Reverse Hook] Skipping group with score {score:.1f} ({group_tokens} tokens)")
        
        # Sort result by original index to maintain order
        final_messages = sorted(
            [(i, msg) for i, msg in enumerate(messages) if i in included_indices],
            key=lambda x: x[0]
        )
        final_messages = [msg for _, msg in final_messages]
        
        if verbose:
            print(f"[Smart Reverse Hook] Kept {len(final_messages)} messages (~{token_count} tokens)")
            reduction = ((len(messages) - len(final_messages)) / len(messages) * 100) if messages else 0
            print(f"[Smart Reverse Hook] Message reduction: {reduction:.1f}%")
        
        return {"llm_input_messages": final_messages}
    
    return smart_reverse_hook