"""
Simple and correct sliding window implementation for ReAct agents

This implementation:
1. Preserves first N messages
2. Preserves last N messages  
3. Fills remaining window with messages from the middle
4. Always ensures message integrity (tool pairs)
"""

from typing import Any, Dict, List, Set
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

from .base import ContextConfig


def create_simple_sliding_window_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a simple sliding window hook that correctly trims messages
    
    Args:
        config: Context configuration with:
            - preserve_first_n: Number of first messages to always keep
            - preserve_last_n: Number of last messages to always keep
            - window_size: Total token budget
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def sliding_window_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sliding window trimming"""
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # Token counting function
        def count_tokens(msg: BaseMessage) -> int:
            return len(str(msg.content)) // 4 if msg.content else 0
        
        # Calculate total tokens
        total_tokens = sum(count_tokens(msg) for msg in messages)
        
        if verbose:
            print(f"\n[Simple Sliding Window] Processing {len(messages)} messages")
            print(f"[Simple Sliding Window] Total tokens: {total_tokens:,}")
            print(f"[Simple Sliding Window] Window size: {config.window_size:,}")
            print(f"[Simple Sliding Window] Preserve first: {config.preserve_first_n}, last: {config.preserve_last_n}")
        
        # If under window size, keep all
        if total_tokens <= config.window_size:
            if verbose:
                print(f"[Simple Sliding Window] Under window size, keeping all messages")
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
        
        # Step 2: Select messages based on sliding window parameters
        selected_indices = set()
        
        # 2a. Preserve first N messages
        for i in range(min(config.preserve_first_n, len(messages))):
            selected_indices.add(i)
        
        # 2b. Preserve last N messages
        start_last = max(0, len(messages) - config.preserve_last_n)
        for i in range(start_last, len(messages)):
            selected_indices.add(i)
        
        # Step 3: Ensure message integrity
        # If we selected any message, we must include all its dependencies
        def add_dependencies(idx: int):
            """Recursively add all dependencies of a message"""
            if idx in tool_dependencies:
                for dep_idx in tool_dependencies[idx]:
                    if dep_idx not in selected_indices:
                        selected_indices.add(dep_idx)
                        add_dependencies(dep_idx)  # Recursive for transitive dependencies
        
        # Check all selected messages for dependencies
        initial_selected = list(selected_indices)
        for idx in initial_selected:
            add_dependencies(idx)
        
        # Step 4: Calculate current token usage
        current_tokens = sum(count_tokens(messages[i]) for i in selected_indices)
        
        if verbose:
            print(f"[Simple Sliding Window] After preserving first/last + dependencies: {len(selected_indices)} messages, {current_tokens:,} tokens")
        
        # Step 5: Fill remaining budget with messages from the middle
        # Work backwards from the most recent unselected messages
        if current_tokens < config.window_size:
            # Get unselected indices in reverse order
            unselected = [i for i in range(len(messages)) if i not in selected_indices]
            unselected.reverse()  # Start from most recent
            
            for idx in unselected:
                msg_tokens = count_tokens(messages[idx])
                
                # Check if adding this message (and its dependencies) would fit
                test_indices = {idx}
                
                # Add dependencies to test set
                def get_all_dependencies(msg_idx: int, test_set: Set[int]):
                    if msg_idx in tool_dependencies:
                        for dep in tool_dependencies[msg_idx]:
                            if dep not in test_set:
                                test_set.add(dep)
                                get_all_dependencies(dep, test_set)
                
                get_all_dependencies(idx, test_indices)
                
                # Calculate tokens for all new messages
                new_tokens = sum(count_tokens(messages[i]) for i in test_indices if i not in selected_indices)
                
                if current_tokens + new_tokens <= config.window_size:
                    # Add this message and all its dependencies
                    selected_indices.update(test_indices)
                    current_tokens += new_tokens
                    if verbose:
                        print(f"[Simple Sliding Window] Added message {idx} with {len(test_indices)} total messages ({new_tokens} tokens)")
        
        # Step 6: Build final message list
        trimmed_messages = [messages[i] for i in sorted(selected_indices)]
        
        if verbose:
            trimmed_tokens = sum(count_tokens(msg) for msg in trimmed_messages)
            msg_reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            token_reduction = ((total_tokens - trimmed_tokens) / total_tokens * 100) if total_tokens else 0
            
            print(f"[Simple Sliding Window] === RESULTS ===")
            print(f"[Simple Sliding Window] Messages: {len(messages)} → {len(trimmed_messages)} ({msg_reduction:.1f}% reduction)")
            print(f"[Simple Sliding Window] Tokens: {total_tokens:,} → {trimmed_tokens:,} ({token_reduction:.1f}% reduction)")
            
            # Show which messages were kept
            kept_ranges = []
            start = None
            for i in sorted(selected_indices):
                if start is None:
                    start = i
                elif i != kept_ranges[-1][1] + 1:
                    kept_ranges.append((start, kept_ranges[-1][1] if kept_ranges else start))
                    start = i
                if i == sorted(selected_indices)[-1]:
                    kept_ranges.append((start, i))
            
            print(f"[Simple Sliding Window] Kept message ranges: {kept_ranges}")
        
        # Return the trimmed messages
        return {"llm_input_messages": trimmed_messages}
    
    return sliding_window_hook