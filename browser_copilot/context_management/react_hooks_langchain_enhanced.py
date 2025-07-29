"""
Enhanced LangChain trim strategy with message integrity preservation

This combines LangChain's trim_messages utility with our integrity-first approach
to ensure tool pairs are never broken while leveraging LangChain's trimming logic.
"""

from typing import Any, Dict, List, Set, Tuple, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.messages.utils import trim_messages

from .base import ContextConfig
from .debug_formatter import ContextDebugFormatter


def create_langchain_integrity_hook(
    config: ContextConfig,
    verbose: bool = False,
    formatter: Optional[ContextDebugFormatter] = None
) -> callable:
    """
    Create a hook that uses LangChain's trim_messages with integrity preservation
    
    This hook:
    1. Uses LangChain's trim_messages for the core trimming logic
    2. Validates and fixes any broken tool pairs after trimming
    3. Falls back to custom grouping if trim_messages fails
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        formatter: Optional debug formatter
        
    Returns:
        Pre-model hook function
    """
    if formatter is None:
        formatter = ContextDebugFormatter(use_rich=False)
    
    def langchain_integrity_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangChain trimming with message integrity preservation
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            formatter.format_hook_header(
                "LangChain + Integrity Hook",
                len(messages),
                config.window_size
            )
            formatter.format_message_analysis(messages)
        
        # Token counter for LangChain
        def token_counter(msgs):
            return sum(len(str(msg.content)) for msg in msgs if msg.content) // 4
        
        # First attempt: Use LangChain's trim_messages
        trimmed_messages = None
        try:
            trimmed_messages = trim_messages(
                messages,
                strategy="last",  # Keep most recent messages
                max_tokens=config.window_size,
                token_counter=token_counter,
                # These constraints help preserve conversation flow
                start_on="human",
                end_on=("human", "tool"),
                include_system=True,  # Always keep system messages
            )
        except Exception as e:
            if verbose:
                formatter.format_warning(f"LangChain trim_messages failed: {e}")
        
        # If trim_messages returned empty or failed, use fallback
        if not trimmed_messages:
            if verbose:
                formatter.format_info("Using fallback grouping strategy")
            trimmed_messages = fallback_group_trimming(
                messages, config.window_size, token_counter, verbose
            )
        
        # Now ensure message integrity
        trimmed_messages = ensure_message_integrity(
            trimmed_messages, messages, token_counter, config.window_size, verbose, formatter
        )
        
        # Calculate metrics for output
        if verbose:
            original_tokens = token_counter(messages)
            trimmed_tokens = token_counter(trimmed_messages)
            
            # Identify excluded messages
            trimmed_indices = {i for i, msg in enumerate(messages) if msg in trimmed_messages}
            excluded_messages = [
                (i, msg, token_counter([msg]))
                for i, msg in enumerate(messages)
                if i not in trimmed_indices
            ]
            
            formatter.format_results(
                original_count=len(messages),
                trimmed_count=len(trimmed_messages),
                original_tokens=original_tokens,
                trimmed_tokens=trimmed_tokens,
                excluded_messages=excluded_messages
            )
            
            # Validate final integrity
            errors = validate_tool_pairs(trimmed_messages)
            if errors:
                formatter.format_error(f"Tool pair validation failed: {errors}")
            else:
                formatter.format_tool_pair_validation(True)
        
        return {"llm_input_messages": trimmed_messages}
    
    return langchain_integrity_hook


def ensure_message_integrity(
    trimmed_messages: List[BaseMessage],
    original_messages: List[BaseMessage],
    token_counter: callable,
    max_tokens: int,
    verbose: bool,
    formatter: ContextDebugFormatter
) -> List[BaseMessage]:
    """
    Ensure message integrity by fixing any broken tool pairs
    
    This function:
    1. Identifies any AIMessages with tool_calls that are missing responses
    2. Adds the missing ToolMessages from the original messages
    3. If adding would exceed budget, removes the incomplete AIMessage instead
    """
    # Build indices for quick lookup
    trimmed_set = set(trimmed_messages)
    original_index_map = {msg: i for i, msg in enumerate(original_messages)}
    
    # Find all tool call IDs in trimmed messages
    ai_tool_calls = {}  # tool_call_id -> AIMessage
    found_tool_responses = set()  # tool_call_ids that have responses
    
    for msg in trimmed_messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    ai_tool_calls[tc_id] = msg
        elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            found_tool_responses.add(msg.tool_call_id)
    
    # Find missing tool responses
    missing_tool_ids = set(ai_tool_calls.keys()) - found_tool_responses
    
    if missing_tool_ids and verbose:
        formatter.format_warning(f"Found {len(missing_tool_ids)} missing tool responses")
    
    # Try to add missing tool responses
    messages_to_add = []
    for tc_id in missing_tool_ids:
        # Find the ToolMessage in original messages
        for msg in original_messages:
            if (isinstance(msg, ToolMessage) and 
                hasattr(msg, 'tool_call_id') and 
                msg.tool_call_id == tc_id):
                messages_to_add.append(msg)
                break
    
    # Check if adding these would exceed budget
    current_tokens = token_counter(trimmed_messages)
    additional_tokens = token_counter(messages_to_add)
    
    if current_tokens + additional_tokens <= max_tokens:
        # We can add the missing messages
        if messages_to_add and verbose:
            formatter.format_info(f"Adding {len(messages_to_add)} missing tool responses")
        
        # Add messages and sort by original order
        result_messages = list(trimmed_messages) + messages_to_add
        result_messages.sort(key=lambda msg: original_index_map.get(msg, float('inf')))
        return result_messages
    else:
        # We need to remove the incomplete AIMessages instead
        if verbose:
            formatter.format_warning(
                f"Cannot add missing tool responses without exceeding budget. "
                f"Removing incomplete AIMessages instead."
            )
        
        # Remove AIMessages that have missing tool responses
        incomplete_ai_messages = {ai_tool_calls[tc_id] for tc_id in missing_tool_ids}
        result_messages = [msg for msg in trimmed_messages if msg not in incomplete_ai_messages]
        
        return result_messages


def fallback_group_trimming(
    messages: List[BaseMessage],
    max_tokens: int,
    token_counter: callable,
    verbose: bool
) -> List[BaseMessage]:
    """
    Fallback trimming strategy that groups messages into atomic units
    
    Used when LangChain's trim_messages fails or returns empty results.
    """
    if not messages:
        return []
    
    # Always include first message
    result = [messages[0]]
    tokens = token_counter([messages[0]])
    
    # Group messages by interaction (AIMessage + its ToolMessages)
    groups = []
    i = 1  # Start after first message
    while i < len(messages):
        group = []
        
        # If it's an AIMessage with tool calls, include all responses
        if isinstance(messages[i], AIMessage) and hasattr(messages[i], 'tool_calls') and messages[i].tool_calls:
            group.append(messages[i])
            tool_ids = set()
            
            for tc in messages[i].tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    tool_ids.add(tc_id)
            
            # Collect tool responses
            j = i + 1
            while j < len(messages) and tool_ids:
                if (isinstance(messages[j], ToolMessage) and 
                    hasattr(messages[j], 'tool_call_id') and
                    messages[j].tool_call_id in tool_ids):
                    group.append(messages[j])
                    tool_ids.remove(messages[j].tool_call_id)
                j += 1
            
            groups.append(group)
            i = j
        else:
            # Single message group
            groups.append([messages[i]])
            i += 1
    
    # Add groups from most recent, respecting token budget
    for group in reversed(groups):
        group_tokens = token_counter(group)
        if tokens + group_tokens <= max_tokens:
            result.extend(group)
            tokens += group_tokens
        elif verbose:
            print(f"  Skipping group of {len(group)} messages ({group_tokens} tokens)")
    
    # Sort by original order
    message_order = {msg: i for i, msg in enumerate(messages)}
    result.sort(key=lambda msg: message_order.get(msg, float('inf')))
    
    return result


def validate_tool_pairs(messages: List[BaseMessage]) -> List[str]:
    """
    Validate that all tool pairs are complete
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Collect all tool calls from AIMessages
    expected_tool_ids = set()
    ai_message_indices = {}
    
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id:
                    expected_tool_ids.add(tc_id)
                    ai_message_indices[tc_id] = i
    
    # Collect all tool responses
    found_tool_ids = set()
    for msg in messages:
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            found_tool_ids.add(msg.tool_call_id)
    
    # Check for missing responses
    missing = expected_tool_ids - found_tool_ids
    for tc_id in missing:
        errors.append(f"Missing ToolMessage for tool_call_id: {tc_id} (from AIMessage at index {ai_message_indices[tc_id]})")
    
    # Check for orphaned tool messages
    orphaned = found_tool_ids - expected_tool_ids
    for tc_id in orphaned:
        errors.append(f"Orphaned ToolMessage with tool_call_id: {tc_id}")
    
    return errors