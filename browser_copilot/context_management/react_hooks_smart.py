"""
Smart context management hooks that analyze message sizes individually
"""

from typing import Any, Dict, List, Tuple, NamedTuple
from collections import defaultdict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from .base import ContextConfig
from .debug_formatter import ContextDebugFormatter


class MessageInfo(NamedTuple):
    """Information about a message"""
    index: int
    message: BaseMessage
    tokens: int
    type: str
    has_tool_calls: bool
    tool_call_id: str = None


def analyze_messages(messages: List[BaseMessage], verbose: bool = False) -> List[MessageInfo]:
    """
    Analyze all messages and return detailed information
    
    Args:
        messages: List of messages to analyze
        verbose: Enable verbose logging
        
    Returns:
        List of MessageInfo for each message
    """
    message_infos = []
    
    for i, msg in enumerate(messages):
        # Calculate token count for this message
        tokens = len(str(msg.content)) // 4 if msg.content else 0
        
        # Determine message type and metadata
        msg_type = type(msg).__name__
        has_tool_calls = isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls
        tool_call_id = getattr(msg, 'tool_call_id', None) if isinstance(msg, ToolMessage) else None
        
        info = MessageInfo(
            index=i,
            message=msg,
            tokens=tokens,
            type=msg_type,
            has_tool_calls=has_tool_calls,
            tool_call_id=tool_call_id
        )
        message_infos.append(info)
    
    if verbose:
        # Show size distribution
        size_buckets = defaultdict(int)
        for info in message_infos:
            if info.tokens < 100:
                size_buckets["<100"] += 1
            elif info.tokens < 500:
                size_buckets["100-500"] += 1
            elif info.tokens < 1000:
                size_buckets["500-1K"] += 1
            elif info.tokens < 5000:
                size_buckets["1K-5K"] += 1
            else:
                size_buckets[">5K"] += 1
        
        print(f"\n[Message Analysis] Total messages: {len(message_infos)}")
        print(f"[Message Analysis] Size distribution:")
        for bucket, count in sorted(size_buckets.items()):
            print(f"  {bucket} tokens: {count} messages")
        
        # Show largest messages
        largest = sorted(message_infos, key=lambda x: x.tokens, reverse=True)[:5]
        print(f"\n[Message Analysis] Largest messages:")
        for info in largest:
            content_preview = str(info.message.content)[:80] if info.message.content else ""
            print(f"  Message {info.index}: {info.type} - {info.tokens} tokens")
            print(f"    Preview: {content_preview}...")
    
    return message_infos


def create_smart_trim_hook(
    config: ContextConfig,
    verbose: bool = False,
    use_rich_output: bool = None
) -> callable:
    """
    Create a hook that makes smart decisions based on individual message sizes
    
    This hook:
    1. Analyzes all messages individually
    2. Preserves tool pairs
    3. Makes intelligent decisions about what to keep
    4. Can skip very large messages if needed
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        use_rich_output: Use rich terminal output (auto-detected if None)
        
    Returns:
        Pre-model hook function
    """
    # Auto-detect rich output capability
    if use_rich_output is None:
        import os
        # Use rich if not in CI/CD and terminal supports it
        use_rich_output = os.isatty(1) and not os.getenv('CI')
    
    formatter = ContextDebugFormatter(use_rich=use_rich_output)
    def smart_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart trimming based on individual message analysis
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        if verbose:
            formatter.format_hook_header("Smart Trim Hook", len(messages), config.window_size)
        
        # Analyze all messages
        message_infos = analyze_messages(messages, verbose=False)  # We'll use formatter instead
        
        if verbose:
            # Use formatter for structured output
            formatter.format_message_analysis(messages)
        
        # Build tool dependency map
        tool_dependencies = {}  # tool_call_id -> AIMessage index
        for info in message_infos:
            if info.has_tool_calls:
                msg = info.message
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id:
                        tool_dependencies[tc_id] = info.index
        
        # Strategy: Include messages intelligently
        included = set()
        token_count = 0
        
        # Always include first message
        if message_infos:
            included.add(0)
            token_count += message_infos[0].tokens
        
        # Work backwards, but skip messages that are too large
        max_single_message_tokens = config.window_size // 10  # No single message should take >10% of budget
        
        for i in range(len(message_infos) - 1, 0, -1):
            info = message_infos[i]
            
            if i in included:
                continue
            
            # Check if this message is part of a tool pair
            required_indices = {i}
            
            # If it's a ToolMessage, we need its AIMessage
            if info.tool_call_id and info.tool_call_id in tool_dependencies:
                required_indices.add(tool_dependencies[info.tool_call_id])
            
            # If it's an AIMessage with tool calls, we need its ToolMessages
            if info.has_tool_calls:
                for j, other_info in enumerate(message_infos):
                    if (other_info.tool_call_id and 
                        other_info.tool_call_id in [
                            tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                            for tc in info.message.tool_calls
                        ]):
                        required_indices.add(j)
            
            # Calculate total tokens for this group
            group_tokens = sum(message_infos[idx].tokens for idx in required_indices if idx not in included)
            
            # Skip if any single message is too large (unless it's critical)
            skip_group = False
            for idx in required_indices:
                if idx not in included and message_infos[idx].tokens > max_single_message_tokens:
                    if verbose:
                        formatter.format_warning(
                            f"Message {idx} is very large ({message_infos[idx].tokens} tokens)"
                        )
                    # Only skip if it's not a critical tool pair
                    if len(required_indices) == 1:  # Single message, not part of a pair
                        skip_group = True
                        break
            
            if skip_group:
                continue
            
            # Check if adding this group would exceed budget
            if token_count + group_tokens > config.window_size:
                if verbose:
                    formatter.format_info(
                        f"Stopping at message {i} - would exceed budget "
                        f"(current: {token_count}, would add: {group_tokens})"
                    )
                break
            
            # Add all messages in the group
            included.update(required_indices)
            token_count += group_tokens
        
        # Build final message list
        result_messages = [info.message for info in message_infos if info.index in included]
        
        if verbose:
            # Calculate totals
            original_tokens = sum(info.tokens for info in message_infos)
            
            # Prepare excluded messages info
            excluded_messages = [
                (info.index, info.message, info.tokens)
                for info in message_infos
                if info.index not in included
            ]
            
            # Format results
            formatter.format_results(
                original_count=len(messages),
                trimmed_count=len(result_messages),
                original_tokens=original_tokens,
                trimmed_tokens=token_count,
                excluded_messages=excluded_messages
            )
            
            # Create JSON summary for metrics
            summary = ContextDebugFormatter.create_json_summary(
                hook_name="smart_trim",
                original_count=len(messages),
                trimmed_count=len(result_messages),
                original_tokens=original_tokens,
                trimmed_tokens=token_count,
                window_size=config.window_size,
                strategy="smart-trim"
            )
            
            # Store summary for potential metrics collection
            smart_trim_hook._last_summary = summary
        
        return {"llm_input_messages": result_messages}
    
    return smart_trim_hook