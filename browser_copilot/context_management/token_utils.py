"""
Utilities for accurate token counting in context management
"""

import json

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

# Token estimation constants
CHARS_PER_TOKEN = 4  # Conservative estimate
MESSAGE_OVERHEAD = 50  # Overhead per message for formatting


def count_message_tokens(msg: BaseMessage) -> int:
    """
    Count tokens for a single message including all metadata

    This accounts for:
    - Message content
    - Message type/role
    - Tool calls and IDs
    - Additional formatting

    Args:
        msg: LangChain message

    Returns:
        Estimated token count
    """
    # Base content tokens
    content_tokens = len(str(msg.content)) // CHARS_PER_TOKEN if msg.content else 0

    # Add overhead for message structure
    total_tokens = content_tokens + MESSAGE_OVERHEAD

    # Add tokens for message type
    if isinstance(msg, HumanMessage):
        total_tokens += 10  # "Human: " prefix
    elif isinstance(msg, SystemMessage):
        total_tokens += 10  # "System: " prefix
    elif isinstance(msg, AIMessage):
        total_tokens += 15  # "Assistant: " prefix

        # Add tokens for tool calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                # Tool call structure adds significant tokens
                if isinstance(tool_call, dict):
                    # Estimate tokens for tool call JSON
                    tool_json = json.dumps(tool_call)
                    total_tokens += len(tool_json) // CHARS_PER_TOKEN
                else:
                    # Estimate for tool call object
                    total_tokens += 50  # Conservative estimate

    elif isinstance(msg, ToolMessage):
        total_tokens += 20  # "Tool: " prefix + tool metadata

        # Tool messages often have structured content
        if hasattr(msg, "name") and msg.name:
            total_tokens += len(msg.name) // CHARS_PER_TOKEN

        if hasattr(msg, "tool_call_id") and msg.tool_call_id:
            total_tokens += len(msg.tool_call_id) // CHARS_PER_TOKEN

    return total_tokens


def count_messages_tokens(messages: list[BaseMessage]) -> int:
    """
    Count total tokens for a list of messages

    Args:
        messages: List of LangChain messages

    Returns:
        Total estimated token count
    """
    return sum(count_message_tokens(msg) for msg in messages)


def estimate_prompt_tokens(messages: list[BaseMessage], system_prompt: str = "") -> int:
    """
    Estimate total tokens when messages are formatted as a prompt

    This includes:
    - System prompt
    - All messages with formatting
    - Additional prompt structure overhead

    Args:
        messages: List of messages
        system_prompt: Optional system prompt

    Returns:
        Estimated total prompt tokens
    """
    total = 0

    # System prompt tokens
    if system_prompt:
        total += len(system_prompt) // CHARS_PER_TOKEN
        total += 50  # Overhead for system prompt formatting

    # Message tokens
    total += count_messages_tokens(messages)

    # Overall prompt structure overhead
    total += 100  # Conservative estimate for prompt wrapper

    return total


def get_message_summary(msg: BaseMessage) -> str:
    """
    Get a short summary of a message for debugging

    Args:
        msg: Message to summarize

    Returns:
        Short summary string
    """
    msg_type = type(msg).__name__
    content_preview = str(msg.content)[:50] if msg.content else ""

    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
        tool_count = len(msg.tool_calls)
        return f"{msg_type} ({tool_count} tool calls)"
    elif isinstance(msg, ToolMessage) and hasattr(msg, "tool_call_id"):
        return f"{msg_type} (id: {msg.tool_call_id[:8]}...)"
    else:
        return f"{msg_type}: {content_preview}..."
