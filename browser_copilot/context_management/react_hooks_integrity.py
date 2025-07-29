"""
Message integrity-first pre-model hooks for context management

These hooks prioritize message integrity over token limits, ensuring that
tool call pairs are NEVER broken, even if it means exceeding the token budget.
"""

from typing import Any, Dict, List, Set, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from .base import ContextConfig


def create_integrity_first_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a hook that prioritizes message integrity over token limits
    
    This hook:
    1. Groups messages into atomic units (AI + all its tool responses)
    2. Only trims at group boundaries
    3. Will exceed token budget to preserve integrity
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def integrity_first_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trim messages while maintaining absolute integrity
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Integrity First Hook] Processing {len(messages)} messages")
            print(f"[Integrity First Hook] Target budget: {config.window_size} tokens")
        
        # Simple token counter
        def count_tokens(msgs: List[BaseMessage]) -> int:
            return sum(len(str(msg.content)) for msg in msgs) // 4
        
        # Group messages into atomic units
        message_groups = []
        current_group = []
        group_starts = []  # Track where each group starts
        
        i = 0
        while i < len(messages):
            msg = messages[i]
            
            # Start a new group
            current_group = [(i, msg)]
            group_start = i
            
            # If it's an AIMessage with tool calls, collect ALL its tool responses
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_ids = set()
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id:
                        tool_ids.add(tc_id)
                
                # Look forward for all tool responses
                j = i + 1
                while j < len(messages) and tool_ids:
                    if isinstance(messages[j], ToolMessage) and hasattr(messages[j], 'tool_call_id'):
                        if messages[j].tool_call_id in tool_ids:
                            current_group.append((j, messages[j]))
                            tool_ids.remove(messages[j].tool_call_id)
                    j += 1
                
                # If we didn't find all tool responses, warn but continue
                if tool_ids and verbose:
                    print(f"[Integrity First Hook] WARNING: Missing tool responses for: {tool_ids}")
                
                # Skip past all messages we've included
                i = max(idx for idx, _ in current_group) + 1
            else:
                i += 1
            
            message_groups.append(current_group)
            group_starts.append(group_start)
        
        if verbose:
            print(f"[Integrity First Hook] Created {len(message_groups)} atomic groups")
        
        # Always include the first group (original prompt)
        result_messages = []
        token_count = 0
        
        if message_groups:
            first_group = message_groups[0]
            for _, msg in first_group:
                result_messages.append(msg)
            token_count = count_tokens(result_messages)
        
        # Work backwards, adding complete groups
        added_groups = {0} if message_groups else set()
        
        for i in range(len(message_groups) - 1, 0, -1):  # Skip first group
            if i in added_groups:
                continue
            
            group = message_groups[i]
            group_messages = [msg for _, msg in group]
            group_tokens = count_tokens(group_messages)
            
            # Check if adding this group would exceed budget
            if token_count + group_tokens > config.window_size:
                # For the LAST group we're adding, we MUST include it
                # to maintain integrity, even if it exceeds the budget
                if len(added_groups) == 1:  # Only have first group
                    if verbose:
                        print(f"[Integrity First Hook] Including group {i} despite exceeding budget "
                              f"({token_count + group_tokens} > {config.window_size}) to maintain integrity")
                    for idx, msg in group:
                        result_messages.append(msg)
                    token_count += group_tokens
                    added_groups.add(i)
                else:
                    if verbose:
                        print(f"[Integrity First Hook] Stopping at group {i} to stay within budget")
                break
            else:
                # Add the group
                for idx, msg in group:
                    result_messages.append(msg)
                token_count += group_tokens
                added_groups.add(i)
        
        # Sort by original index
        result_messages.sort(key=lambda msg: next(
            i for i, m in enumerate(messages) if m is msg
        ))
        
        if verbose:
            print(f"[Integrity First Hook] Kept {len(result_messages)} messages in {len(added_groups)} groups")
            print(f"[Integrity First Hook] Final token count: {token_count} "
                  f"({'OVER' if token_count > config.window_size else 'within'} budget)")
            
            # Validate integrity
            validation_errors = validate_message_integrity(result_messages, verbose)
            if validation_errors:
                print(f"[Integrity First Hook] CRITICAL: Integrity validation failed!")
                for error in validation_errors:
                    print(f"  - {error}")
        
        return {"llm_input_messages": result_messages}
    
    return integrity_first_hook


def validate_message_integrity(
    messages: List[BaseMessage], 
    verbose: bool = False
) -> List[str]:
    """
    Validate that message sequence maintains integrity
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check 1: All AIMessage tool_calls have corresponding ToolMessages
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    # Look for corresponding ToolMessage
                    found = False
                    for j in range(i + 1, len(messages)):
                        if (isinstance(messages[j], ToolMessage) and 
                            hasattr(messages[j], 'tool_call_id') and 
                            messages[j].tool_call_id == tc_id):
                            found = True
                            break
                    if not found:
                        errors.append(f"AIMessage at index {i} has tool_call {tc_id} without corresponding ToolMessage")
    
    # Check 2: All ToolMessages have preceding AIMessage with matching tool_call
    for i, msg in enumerate(messages):
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            tc_id = msg.tool_call_id
            # Look backwards for AIMessage
            found = False
            for j in range(i - 1, -1, -1):
                if isinstance(messages[j], AIMessage) and hasattr(messages[j], 'tool_calls'):
                    for tc in messages[j].tool_calls or []:
                        call_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                        if call_id == tc_id:
                            found = True
                            break
                if found:
                    break
            if not found:
                errors.append(f"ToolMessage at index {i} with tool_call_id {tc_id} has no preceding AIMessage")
    
    return errors


def create_group_based_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a hook that treats message groups as atomic units
    
    This is similar to integrity_first but with stricter grouping rules:
    - Human message starts a new interaction group
    - Groups include all messages until the next Human message
    - Groups are kept or discarded as complete units
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    def group_based_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trim messages by complete interaction groups
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            print(f"\n[Group Based Hook] Processing {len(messages)} messages")
        
        # Group messages by interactions (Human message starts new group)
        interaction_groups = []
        current_group = []
        
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage) and current_group:
                # Save previous group and start new one
                interaction_groups.append(current_group)
                current_group = [(i, msg)]
            else:
                current_group.append((i, msg))
        
        if current_group:
            interaction_groups.append(current_group)
        
        if verbose:
            print(f"[Group Based Hook] Found {len(interaction_groups)} interaction groups")
        
        # Simple token counter
        def count_tokens(msgs: List[Tuple[int, BaseMessage]]) -> int:
            return sum(len(str(msg.content)) for _, msg in msgs) // 4
        
        # Always include first group
        selected_groups = [interaction_groups[0]] if interaction_groups else []
        token_count = count_tokens(interaction_groups[0]) if interaction_groups else 0
        
        # Add groups from most recent, respecting token budget
        for i in range(len(interaction_groups) - 1, 0, -1):
            group = interaction_groups[i]
            group_tokens = count_tokens(group)
            
            if token_count + group_tokens <= config.window_size:
                selected_groups.insert(1, group)  # Insert after first
                token_count += group_tokens
            else:
                if verbose:
                    print(f"[Group Based Hook] Skipping group {i} ({group_tokens} tokens)")
        
        # Flatten and sort by index
        result_messages = []
        for group in selected_groups:
            result_messages.extend([msg for _, msg in group])
        
        if verbose:
            print(f"[Group Based Hook] Selected {len(selected_groups)} groups, {len(result_messages)} messages")
            print(f"[Group Based Hook] Token usage: {token_count} / {config.window_size}")
        
        return {"llm_input_messages": result_messages}
    
    return group_based_hook