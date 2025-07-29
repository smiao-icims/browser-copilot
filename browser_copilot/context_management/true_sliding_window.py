"""
True sliding window implementation with Human message preservation

This implementation:
1. Preserves the first N Human messages (containing test instructions)
2. Works backwards from the most recent message to fill remaining budget
3. Always ensures message integrity (tool pairs) for non-preserved messages
4. May exceed window size to preserve integrity
"""

from typing import Any, Dict, List, Set
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage

from .base import ContextConfig


def create_true_sliding_window_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a true sliding window hook that keeps last N tokens
    
    Args:
        config: Context configuration with:
            - window_size: Total token budget
            - preserve_first_n: Number of first Human messages to always keep
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def true_sliding_window_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply true sliding window - preserve first N + keep last tokens"""
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # Token counting function
        def count_tokens(msg: BaseMessage) -> int:
            return len(str(msg.content)) // 4 if msg.content else 0
        
        # Calculate total tokens
        total_tokens = sum(count_tokens(msg) for msg in messages)
        
        if verbose:
            print(f"\n[True Sliding Window] Processing {len(messages)} messages")
            print(f"[True Sliding Window] Total tokens: {total_tokens:,}")
            print(f"[True Sliding Window] Window size: {config.window_size:,}")
            print(f"[True Sliding Window] Preserve first: {config.preserve_first_n} Human messages")
        
        # If under window size, keep all
        if total_tokens <= config.window_size:
            if verbose:
                print(f"[True Sliding Window] Under window size, keeping all messages")
            return {}
        
        # Step 1: Build tool dependency map
        tool_dependencies = {}  # Maps message index to indices it depends on
        tool_call_to_ai = {}    # Maps tool_call_id to AIMessage index
        
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                # This AIMessage depends on its tool responses
                tool_dependencies[i] = set()
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id:
                        tool_call_to_ai[tc_id] = i
            
            elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                tc_id = msg.tool_call_id
                if tc_id in tool_call_to_ai:
                    ai_idx = tool_call_to_ai[tc_id]
                    # The AIMessage depends on this ToolMessage
                    if ai_idx in tool_dependencies:
                        tool_dependencies[ai_idx].add(i)
                    # This ToolMessage depends on its AIMessage
                    tool_dependencies[i] = {ai_idx}
        
        # Step 2: First, preserve the first N Human messages ONLY (skip all non-Human messages)
        selected_indices = set()
        current_tokens = 0
        
        # Count and preserve ONLY Human messages, skip everything else
        human_count = 0
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                selected_indices.add(i)
                current_tokens += count_tokens(msg)
                human_count += 1
                if human_count >= config.preserve_first_n:
                    break
            # Non-Human messages are skipped entirely
        
        if verbose and human_count > 0:
            print(f"[True Sliding Window] Preserved first {human_count} Human messages ({current_tokens:,} tokens)")
        
        # Step 3: Work backwards from the end, selecting messages until we fill the window
        # Once we can't fit a message, we stop (unless needed for integrity)
        reached_limit = False
        
        for i in range(len(messages) - 1, -1, -1):
            # Skip if already selected
            if i in selected_indices:
                continue
            
            # If we've reached the limit, only continue for integrity checks
            if reached_limit:
                # Check if this message is needed for integrity
                is_needed = False
                for selected_idx in selected_indices:
                    if selected_idx in tool_dependencies and i in tool_dependencies[selected_idx]:
                        is_needed = True
                        break
                
                if not is_needed:
                    continue
            
            msg = messages[i]
            msg_tokens = count_tokens(msg)
            
            # Check if adding this message would exceed window
            # But we need to consider its dependencies too
            test_indices = {i}
            
            # Add all dependencies of this message
            def add_all_dependencies(idx: int, test_set: Set[int]):
                """Recursively add all dependencies"""
                if idx in tool_dependencies:
                    for dep_idx in tool_dependencies[idx]:
                        if dep_idx not in test_set:
                            test_set.add(dep_idx)
                            add_all_dependencies(dep_idx, test_set)
            
            add_all_dependencies(i, test_indices)
            
            # Calculate tokens for this message and all its dependencies
            new_indices = test_indices - selected_indices
            test_tokens = sum(count_tokens(messages[idx]) for idx in new_indices)
            
            # Check if we can fit this message group
            if current_tokens + test_tokens <= config.window_size:
                # Add this message and all its dependencies
                selected_indices.update(new_indices)
                current_tokens += test_tokens
                
                if verbose:
                    print(f"[True Sliding Window] Added message {i} with {len(test_indices)} dependencies ({test_tokens} tokens)")
            else:
                # Can't fit this message group
                reached_limit = True
                
                # Check if this is needed for integrity
                is_needed = False
                for selected_idx in selected_indices:
                    if selected_idx in tool_dependencies and i in tool_dependencies[selected_idx]:
                        is_needed = True
                        break
                
                if is_needed:
                    # Must include for integrity, even if it exceeds budget
                    selected_indices.update(new_indices)
                    current_tokens += test_tokens
                    
                    if verbose:
                        print(f"[True Sliding Window] FORCED inclusion of message {i} for integrity ({test_tokens} tokens over budget)")
                else:
                    if verbose:
                        print(f"[True Sliding Window] Skipped message {i} ({test_tokens} tokens would exceed budget) - stopping here")
        
        # Step 4: Build final message list
        trimmed_messages = [messages[i] for i in sorted(selected_indices)]
        
        if verbose:
            trimmed_tokens = sum(count_tokens(msg) for msg in trimmed_messages)
            msg_reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            token_reduction = ((total_tokens - trimmed_tokens) / total_tokens * 100) if total_tokens else 0
            
            print(f"[True Sliding Window] === RESULTS ===")
            print(f"[True Sliding Window] Messages: {len(messages)} → {len(trimmed_messages)} ({msg_reduction:.1f}% reduction)")
            print(f"[True Sliding Window] Tokens: {total_tokens:,} → {trimmed_tokens:,} ({token_reduction:.1f}% reduction)")
            
            # Show which messages were kept
            if len(selected_indices) < 20:  # Only show if reasonable number
                print(f"[True Sliding Window] Kept indices: {sorted(selected_indices)} ({trimmed_tokens:,} tokens)")
            else:
                # Show ranges for large sets
                indices = sorted(selected_indices)
                ranges = []
                start = indices[0]
                prev = indices[0]
                
                for idx in indices[1:]:
                    if idx != prev + 1:
                        if start == prev:
                            ranges.append(str(start))
                        else:
                            ranges.append(f"{start}-{prev}")
                        start = idx
                    prev = idx
                
                # Add final range
                if start == prev:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{prev}")
                
                print(f"[True Sliding Window] Kept ranges: {', '.join(ranges)} ({trimmed_tokens:,} tokens)")
            
            # Check if we exceeded budget for integrity
            if trimmed_tokens > config.window_size:
                print(f"[True Sliding Window] WARNING: Exceeded window size by {trimmed_tokens - config.window_size:,} tokens to maintain integrity")
        
        # Return the trimmed messages
        return {"llm_input_messages": trimmed_messages}
    
    return true_sliding_window_hook