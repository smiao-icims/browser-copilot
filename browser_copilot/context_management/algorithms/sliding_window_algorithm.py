"""
Sliding window algorithm for message selection.

This module provides a pure algorithm implementation that's independent
of LangChain hooks and can be easily tested.
"""

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

# Type variable for messages
MessageT = TypeVar("MessageT")


class TokenCounter(Protocol):
    """Protocol for token counting functionality."""

    def count_tokens(self, message: Any) -> int:
        """Count tokens in a message."""
        ...


@dataclass
class SlidingWindowConfig:
    """Configuration for sliding window algorithm."""

    window_size: int
    preserve_first_n: int = 2
    preserve_last_n: int = 10


@dataclass
class MessageDependencies:
    """Dependencies between messages for tool calls."""

    # Maps message index to indices it depends on
    tool_dependencies: dict[int, set[int]]
    # Maps message index to indices that depend on it
    reverse_dependencies: dict[int, set[int]]


@dataclass
class SelectionResult:
    """Result of message selection."""

    selected_indices: set[int]
    total_tokens: int
    exceeded_budget: bool
    exceeded_amount: int = 0
    total_messages: int = 0

    @property
    def all_messages_selected(self) -> bool:
        """Check if all messages were selected."""
        return len(self.selected_indices) == self.total_messages


class SlidingWindowAlgorithm:
    """
    Pure algorithm implementation for sliding window message selection.

    This class is independent of LangChain hooks and can be tested separately.
    """

    def __init__(self, config: SlidingWindowConfig, token_counter: TokenCounter):
        """Initialize with configuration and token counter."""
        self.config = config
        self.token_counter = token_counter

    def select_messages(self, messages: list[Any]) -> SelectionResult:
        """
        Select messages according to sliding window algorithm.

        Args:
            messages: List of messages to select from

        Returns:
            SelectionResult with selected indices and token information
        """
        if not messages:
            return SelectionResult(set(), 0, False, 0, 0)

        # Calculate total tokens first
        total_tokens = sum(self.token_counter.count_tokens(msg) for msg in messages)

        # If under window size, keep all messages (including orphaned ones)
        if total_tokens <= self.config.window_size:
            return SelectionResult(
                set(range(len(messages))), total_tokens, False, 0, len(messages)
            )

        # Build dependencies for filtering
        dependencies = self._build_dependencies(messages)

        # Find orphaned ToolMessages (those without corresponding AIMessages)
        orphaned_tool_indices = self._find_orphaned_tool_messages(
            messages, dependencies
        )

        # Phase 1: Preserve first N Human/System messages
        first_selection = self._select_first_messages(messages)

        # Phase 2: Preserve last M messages with integrity
        last_m_start = max(
            len(first_selection.selected_indices),
            len(messages) - self.config.preserve_last_n,
        )
        last_selection = self._select_last_messages(
            messages, first_selection.selected_indices, dependencies, last_m_start
        )

        # Merge first and last selections
        selected_indices = (
            first_selection.selected_indices | last_selection.selected_indices
        )
        current_tokens = first_selection.total_tokens + last_selection.total_tokens

        # Phase 3: Fill middle if budget allows
        # Fill backwards from (last_m_start - 1)
        middle_result = self._fill_middle_messages(
            messages,
            selected_indices,
            current_tokens,
            dependencies,
            len(first_selection.selected_indices),
            last_m_start,  # This is where we should stop filling
        )

        # Remove orphaned ToolMessages from final selection
        final_indices = middle_result.selected_indices - orphaned_tool_indices

        # Final integrity check: ensure no gaps in selected messages
        # This prevents issues like having messages [0, 33, 35, 36] and missing 34
        # Pass the boundary to avoid filling gap between first N and the rest
        first_n_boundary = (
            max(first_selection.selected_indices)
            if first_selection.selected_indices
            else -1
        )
        final_indices = self._fill_sequence_gaps(
            messages,
            final_indices,
            middle_result.total_tokens,
            self.config.window_size,
            first_n_boundary,
        )

        # Critical: Ensure all tool call dependencies are satisfied
        # This prevents errors like "AIMessages with tool_calls that do not have corresponding ToolMessage"
        final_indices = self._ensure_tool_call_integrity(
            messages,
            final_indices,
            dependencies,
            self.config.window_size,
            first_n_boundary,
        )

        # Recalculate tokens after all adjustments
        final_tokens = sum(
            self.token_counter.count_tokens(messages[i]) for i in final_indices
        )

        exceeded = final_tokens > self.config.window_size
        exceeded_amount = max(0, final_tokens - self.config.window_size)

        return SelectionResult(
            final_indices, final_tokens, exceeded, exceeded_amount, len(messages)
        )

    def _build_dependencies(self, messages: list[Any]) -> MessageDependencies:
        """Build tool call dependencies between messages."""
        tool_deps: dict[int, set[int]] = {}
        reverse_deps: dict[int, set[int]] = {}

        for i, msg in enumerate(messages):
            if (
                isinstance(msg, AIMessage)
                and hasattr(msg, "tool_calls")
                and msg.tool_calls
            ):
                for tc in msg.tool_calls:
                    tc_id = (
                        tc.get("id")
                        if isinstance(tc, dict)
                        else getattr(tc, "id", None)
                    )
                    if tc_id:
                        # Find corresponding ToolMessage
                        for j in range(i + 1, len(messages)):
                            if (
                                isinstance(messages[j], ToolMessage)
                                and getattr(messages[j], "tool_call_id", None) == tc_id
                            ):
                                # Record bidirectional dependency
                                tool_deps.setdefault(i, set()).add(j)
                                reverse_deps.setdefault(j, set()).add(i)
                                break

        return MessageDependencies(tool_deps, reverse_deps)

    def _find_orphaned_tool_messages(
        self, messages: list[Any], dependencies: MessageDependencies
    ) -> set[int]:
        """Find ToolMessages without corresponding AIMessages."""
        orphaned_indices = set()

        for i, msg in enumerate(messages):
            if isinstance(msg, ToolMessage):
                # If this ToolMessage has no AIMessage that calls it, it's orphaned
                if i not in dependencies.reverse_dependencies:
                    orphaned_indices.add(i)

        return orphaned_indices

    def _select_first_messages(self, messages: list[Any]) -> SelectionResult:
        """Select first N Human/System messages."""
        selected_indices = set()
        total_tokens = 0
        count = 0

        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage | SystemMessage):
                selected_indices.add(i)
                total_tokens += self.token_counter.count_tokens(msg)
                count += 1
                if count >= self.config.preserve_first_n:
                    break

        return SelectionResult(selected_indices, total_tokens, False, 0, 0)

    def _select_last_messages(
        self,
        messages: list[Any],
        existing_indices: set[int],
        dependencies: MessageDependencies,
        last_m_start: int,
    ) -> SelectionResult:
        """Select last M messages with integrity."""
        selected_indices = set()
        total_tokens = 0

        # Add last M messages
        for i in range(last_m_start, len(messages)):
            if i not in existing_indices:
                selected_indices.add(i)
                total_tokens += self.token_counter.count_tokens(messages[i])

        # Ensure integrity for tool calls
        integrity_indices = self._get_integrity_dependencies(
            selected_indices, dependencies
        )

        # Add integrity dependencies
        for idx in integrity_indices:
            if idx not in existing_indices and idx not in selected_indices:
                selected_indices.add(idx)
                total_tokens += self.token_counter.count_tokens(messages[idx])

        # If integrity additions created gaps, fill them to maintain continuity
        if integrity_indices:
            all_selected = selected_indices | existing_indices
            sorted_all = sorted(all_selected)

            # Find small gaps that would break conversation flow
            for i in range(len(sorted_all) - 1):
                current = sorted_all[i]
                next_idx = sorted_all[i + 1]
                gap_size = next_idx - current - 1

                # Fill gaps of 1-2 messages to maintain flow
                if 0 < gap_size <= 2:
                    for j in range(current + 1, next_idx):
                        if j not in all_selected:
                            selected_indices.add(j)
                            total_tokens += self.token_counter.count_tokens(messages[j])

        return SelectionResult(selected_indices, total_tokens, False, 0, 0)

    def _get_integrity_dependencies(
        self, indices: set[int], dependencies: MessageDependencies
    ) -> set[int]:
        """Get all indices needed for message integrity."""
        integrity_additions = set()

        # Check ALL selected indices, not just those in range
        for i in indices:
            # If it's a ToolMessage, need its AIMessage (could be anywhere)
            if i in dependencies.reverse_dependencies:
                integrity_additions.update(dependencies.reverse_dependencies[i])
            # If it's an AIMessage, need its ToolMessages (could be anywhere)
            if i in dependencies.tool_dependencies:
                integrity_additions.update(dependencies.tool_dependencies[i])

        return integrity_additions

    def _fill_middle_messages(
        self,
        messages: list[Any],
        selected_indices: set[int],
        current_tokens: int,
        dependencies: MessageDependencies,
        left_boundary: int,
        right_boundary: int,
    ) -> SelectionResult:
        """Fill middle messages if budget allows."""
        # Check if we have budget
        if current_tokens >= self.config.window_size:
            return SelectionResult(selected_indices.copy(), current_tokens, True, 0, 0)

        remaining_budget = self.config.window_size - current_tokens
        working_indices = selected_indices.copy()
        working_tokens = current_tokens

        # Start from right_boundary - 1 (M-1) and work backwards
        # This ensures we fill contiguously from the last M messages backwards
        i = right_boundary - 1

        while i >= left_boundary and remaining_budget > 0:
            if i in working_indices:
                i -= 1
                continue

            # Get all messages needed for this index (including tool dependencies)
            needed_indices = self._get_message_group(i, dependencies, working_indices)

            if not needed_indices:
                i -= 1
                continue

            # Calculate tokens for all messages in the group
            tokens_needed = sum(
                self.token_counter.count_tokens(messages[idx]) for idx in needed_indices
            )

            # Check if the entire group fits in budget
            if tokens_needed <= remaining_budget:
                # Add all messages in the group
                working_indices.update(needed_indices)
                working_tokens += tokens_needed
                remaining_budget -= tokens_needed

                # After adding messages, check for integrity dependencies
                # This ensures if we added an AIMessage, we also have its ToolMessages
                added_indices = list(needed_indices)
                for idx in added_indices:
                    # Check if this message has dependencies we need to add
                    if idx in dependencies.tool_dependencies:
                        for tool_idx in dependencies.tool_dependencies[idx]:
                            if tool_idx not in working_indices and tool_idx < len(
                                messages
                            ):
                                tool_tokens = self.token_counter.count_tokens(
                                    messages[tool_idx]
                                )
                                if tool_tokens <= remaining_budget:
                                    working_indices.add(tool_idx)
                                    working_tokens += tool_tokens
                                    remaining_budget -= tool_tokens

                    # If it's a ToolMessage, ensure we have its AIMessage
                    if idx in dependencies.reverse_dependencies:
                        for ai_idx in dependencies.reverse_dependencies[idx]:
                            if ai_idx not in working_indices and ai_idx >= 0:
                                ai_tokens = self.token_counter.count_tokens(
                                    messages[ai_idx]
                                )
                                if ai_tokens <= remaining_budget:
                                    working_indices.add(ai_idx)
                                    working_tokens += ai_tokens
                                    remaining_budget -= ai_tokens
            else:
                # Can't fit this message group
                # Since we're filling contiguously backwards, we stop here
                break

            i -= 1

        return SelectionResult(working_indices, working_tokens, False, 0, 0)

    def _get_message_group(
        self, index: int, dependencies: MessageDependencies, existing: set[int]
    ) -> set[int]:
        """Get all messages that must be added together with this index."""
        to_add = {index}

        # If it's a ToolMessage, need its AIMessage
        if index in dependencies.reverse_dependencies:
            to_add.update(dependencies.reverse_dependencies[index])

        # If it's an AIMessage, need its ToolMessages
        if index in dependencies.tool_dependencies:
            to_add.update(dependencies.tool_dependencies[index])

        # Return only new indices
        return to_add - existing

    def _fill_sequence_gaps(
        self,
        messages: list[Any],
        indices: set[int],
        current_tokens: int,
        window_size: int,
        first_n_boundary: int = -1,
    ) -> set[int]:
        """Fill gaps in message sequence to maintain continuity."""
        if not indices:
            return indices

        working_indices = indices.copy()
        working_tokens = current_tokens
        remaining_budget = window_size - current_tokens

        # Keep filling gaps until no more gaps can be filled
        gaps_filled = True
        while gaps_filled and remaining_budget > 0:
            gaps_filled = False
            sorted_indices = sorted(working_indices)

            # Look for any gaps in the sequence
            for i in range(len(sorted_indices) - 1):
                curr_idx = sorted_indices[i]
                next_idx = sorted_indices[i + 1]
                gap_size = next_idx - curr_idx - 1

                # Skip the gap between first N messages and the rest
                # This preserves the sliding window structure
                if (
                    first_n_boundary >= 0
                    and curr_idx <= first_n_boundary
                    and next_idx > first_n_boundary
                ):
                    continue

                # Fill any gap to maintain continuity
                if gap_size > 0:
                    # Try to fill all messages in the gap
                    gap_messages = []
                    gap_total_tokens = 0

                    for gap_idx in range(curr_idx + 1, next_idx):
                        if gap_idx not in working_indices:
                            tokens = self.token_counter.count_tokens(messages[gap_idx])
                            gap_messages.append((gap_idx, tokens))
                            gap_total_tokens += tokens

                    # If we can afford to fill the entire gap, do it
                    if gap_total_tokens <= remaining_budget:
                        for gap_idx, tokens in gap_messages:
                            working_indices.add(gap_idx)
                            working_tokens += tokens
                            remaining_budget -= tokens
                        gaps_filled = True
                        break
                    # Otherwise, fill as many as we can from the beginning of the gap
                    else:
                        for gap_idx, tokens in gap_messages:
                            if tokens <= remaining_budget:
                                working_indices.add(gap_idx)
                                working_tokens += tokens
                                remaining_budget -= tokens
                                gaps_filled = True
                            else:
                                break
                        if gaps_filled:
                            break

        return working_indices

    def _ensure_tool_call_integrity(
        self,
        messages: list[Any],
        indices: set[int],
        dependencies: MessageDependencies,
        window_size: int,
        first_n_boundary: int = -1,
    ) -> set[int]:
        """Ensure tool call integrity at gap boundaries to prevent validation errors."""
        if not indices:
            return indices

        working_indices = indices.copy()
        sorted_indices = sorted(working_indices)

        # Since messages are ordered, we only need to check at gap boundaries
        # where we might have broken tool call pairs

        # Find gaps in the sequence (excluding the intentional gap after first N)
        gaps = []
        for i in range(len(sorted_indices) - 1):
            curr_idx = sorted_indices[i]
            next_idx = sorted_indices[i + 1]
            if next_idx - curr_idx > 1:
                # Skip the gap between first N messages and the rest
                if (
                    first_n_boundary >= 0
                    and curr_idx <= first_n_boundary
                    and next_idx > first_n_boundary
                ):
                    continue
                # Found a gap from curr_idx to next_idx
                gaps.append((curr_idx, next_idx))

        # For each gap, check if we broke any tool call relationships
        for last_before_gap, first_after_gap in gaps:
            # Check if the last message before gap has unsatisfied tool calls
            if last_before_gap in dependencies.tool_dependencies:
                for tool_idx in dependencies.tool_dependencies[last_before_gap]:
                    if tool_idx > last_before_gap and tool_idx < first_after_gap:
                        # This tool message was skipped, remove the AI message
                        working_indices.discard(last_before_gap)
                        break

            # Check if the first message after gap is a tool message missing its AI
            if first_after_gap in dependencies.reverse_dependencies:
                for ai_idx in dependencies.reverse_dependencies[first_after_gap]:
                    if ai_idx > last_before_gap and ai_idx < first_after_gap:
                        # The AI message for this tool was skipped, remove the tool message
                        working_indices.discard(first_after_gap)
                        break

        return working_indices
