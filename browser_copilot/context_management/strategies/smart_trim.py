"""
Smart trim context management strategy.

This strategy analyzes message sizes individually and makes intelligent
decisions about what to keep based on content importance and size.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from .base import ContextStrategy, PreModelHook

# Removed debug_formatter import - using simple print statements instead


@dataclass
class MessageInfo:
    """Information about a message."""

    index: int
    message: BaseMessage
    tokens: int
    type: str
    has_tool_calls: bool
    tool_call_id: str | None


class SmartTrimStrategy(ContextStrategy):
    """
    Smart trim strategy that analyzes messages individually.

    This strategy:
    1. Analyzes all messages individually for size and importance
    2. Preserves tool pairs
    3. Makes intelligent decisions about what to keep
    4. Can skip very large messages if needed
    """

    def __init__(self, config=None, verbose=False):
        """
        Initialize smart trim strategy.

        Args:
            config: Configuration for the strategy
            verbose: Whether to enable verbose logging
        """
        super().__init__(config, verbose)

    def create_hook(self) -> PreModelHook:
        """
        Create a smart trim pre-model hook.

        Returns:
            A hook that implements smart trimming
        """

        def smart_trim_hook(state: dict[str, Any]) -> dict[str, Any]:
            """Smart trimming based on individual message analysis."""
            messages = state.get("messages", [])

            if not messages:
                return {}

            if self.verbose:
                print(f"\n[Smart Trim Hook] Processing {len(messages)} messages")
                print(f"[Smart Trim Hook] Window size: {self.config.window_size:,}")

            # Analyze all messages
            message_infos = self._analyze_messages(messages)

            if self.verbose:
                # Show message analysis
                total_tokens = sum(info.tokens for info in message_infos)
                print(f"[Smart Trim Hook] Total tokens: {total_tokens:,}")

            # Build tool dependency map
            tool_dependencies = {}  # tool_call_id -> AIMessage index
            for info in message_infos:
                if info.has_tool_calls:
                    msg = info.message
                    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                        for tc in msg.tool_calls:
                            tc_id = (
                                tc.get("id")
                                if isinstance(tc, dict)
                                else getattr(tc, "id", None)
                            )
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
            max_single_message_tokens = (
                self.config.window_size // 10
            )  # No single message should take >10% of budget

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
                if info.has_tool_calls and isinstance(info.message, AIMessage):
                    for j, other_info in enumerate(message_infos):
                        if other_info.tool_call_id and other_info.tool_call_id in [
                            (
                                tc.get("id")
                                if isinstance(tc, dict)
                                else getattr(tc, "id", None)
                            )
                            for tc in info.message.tool_calls
                        ]:
                            required_indices.add(j)

                # Calculate total tokens for this group
                group_tokens = sum(
                    message_infos[idx].tokens
                    for idx in required_indices
                    if idx not in included
                )

                # Skip if any single message is too large (unless it's critical)
                skip_group = False
                for idx in required_indices:
                    if (
                        idx not in included
                        and message_infos[idx].tokens > max_single_message_tokens
                    ):
                        if self.verbose:
                            print(
                                f"[Smart Trim Hook] WARNING: Message {idx} is very large ({message_infos[idx].tokens} tokens)"
                            )
                        # Only skip if it's not a critical tool pair
                        if (
                            len(required_indices) == 1
                        ):  # Single message, not part of a pair
                            skip_group = True
                            break

                if skip_group:
                    continue

                # Check if adding this group would exceed budget
                if token_count + group_tokens > self.config.window_size:
                    if self.verbose:
                        print(
                            f"[Smart Trim Hook] Stopping at message {i} - would exceed budget "
                        )
                        print(
                            f"[Smart Trim Hook] Current: {token_count}, would add: {group_tokens}"
                        )
                    break

                # Add all messages in the group
                included.update(required_indices)
                token_count += group_tokens

            # Build final message list
            result_messages = [
                info.message for info in message_infos if info.index in included
            ]

            if self.verbose:
                # Calculate totals
                original_tokens = sum(info.tokens for info in message_infos)

                # Prepare excluded messages info
                excluded_messages = [
                    (info.index, info.message, info.tokens)
                    for info in message_infos
                    if info.index not in included
                ]

                # Format results
                msg_reduction = (
                    ((len(messages) - len(result_messages)) / len(messages) * 100)
                    if messages
                    else 0
                )
                token_reduction = (
                    ((original_tokens - token_count) / original_tokens * 100)
                    if original_tokens
                    else 0
                )

                print("[Smart Trim Hook] === RESULTS ===")
                print(
                    f"[Smart Trim Hook] Messages: {len(messages)} → {len(result_messages)} ({msg_reduction:.1f}% reduction)"
                )
                print(
                    f"[Smart Trim Hook] Tokens: {original_tokens:,} → {token_count:,} ({token_reduction:.1f}% reduction)"
                )

                if excluded_messages:
                    print(
                        f"[Smart Trim Hook] Excluded {len(excluded_messages)} messages"
                    )
                    # Show first few excluded messages
                    for idx, msg, tokens in excluded_messages[:3]:
                        msg_type = type(msg).__name__
                        print(f"  - Message {idx}: {msg_type} ({tokens} tokens)")
                    if len(excluded_messages) > 3:
                        print(f"  ... and {len(excluded_messages) - 3} more")

            return {"llm_input_messages": result_messages}

        return smart_trim_hook

    def get_name(self) -> str:
        """Get strategy name."""
        return "smart-trim"

    def get_description(self) -> str:
        """Get strategy description."""
        return (
            "Intelligent trimming based on message importance and content analysis. "
            "Scores messages based on content importance, preserves high-value messages, "
            "and adaptively trims based on message patterns."
        )

    def _analyze_messages(self, messages: list[BaseMessage]) -> list[MessageInfo]:
        """
        Analyze all messages and return detailed information.

        Args:
            messages: List of messages to analyze

        Returns:
            List of MessageInfo for each message
        """
        message_infos = []

        for i, msg in enumerate(messages):
            # Calculate token count for this message
            tokens = self.count_tokens(msg)

            # Determine message type and metadata
            msg_type = type(msg).__name__
            has_tool_calls = (
                isinstance(msg, AIMessage)
                and hasattr(msg, "tool_calls")
                and bool(msg.tool_calls)
            )
            tool_call_id = (
                getattr(msg, "tool_call_id", None)
                if isinstance(msg, ToolMessage)
                else None
            )

            info = MessageInfo(
                index=i,
                message=msg,
                tokens=tokens,
                type=msg_type,
                has_tool_calls=has_tool_calls,
                tool_call_id=tool_call_id,
            )
            message_infos.append(info)

        if self.verbose:
            # Show size distribution
            size_buckets: dict[str, int] = defaultdict(int)
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
            print("[Message Analysis] Size distribution:")
            for bucket, count in sorted(size_buckets.items()):
                print(f"  {bucket} tokens: {count} messages")

            # Show largest messages
            largest = sorted(message_infos, key=lambda x: x.tokens, reverse=True)[:5]
            print("\n[Message Analysis] Largest messages:")
            for info in largest:
                content_preview = (
                    str(info.message.content)[:80] if info.message.content else ""
                )
                print(f"  Message {info.index}: {info.type} - {info.tokens} tokens")
                print(f"    Preview: {content_preview}...")

        return message_infos
