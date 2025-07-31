"""
Sliding window context management strategy.

This strategy preserves first N Human/System messages and fills the
remaining budget with the most recent messages, working backwards.
"""

from typing import Any

from ..algorithms.sliding_window_algorithm import (
    SlidingWindowAlgorithm,
    SlidingWindowConfig,
)
from .base import ContextStrategy, PreModelHook


class SlidingWindowStrategy(ContextStrategy):
    """
    True sliding window strategy that keeps last N tokens.

    This strategy:
    1. Preserves the first N Human and System messages (test instructions & system prompts)
    2. Preserves the last M messages (with integrity for tool pairs)
    3. Fills remaining budget with messages working backwards from (last M - 1)
    4. Uses a SOFT budget - message integrity is prioritized over token limit
    5. Filters out orphaned ToolMessages that have no corresponding AIMessage

    Note: The window_size is treated as a soft limit. Tool message pairs
    (AIMessage with tool_calls + corresponding ToolMessages) are kept together
    even if it means exceeding the budget.
    """

    def create_hook(self) -> PreModelHook:
        """
        Create a sliding window pre-model hook.

        Returns:
            A hook that implements sliding window trimming
        """
        # Create algorithm configuration
        algo_config = SlidingWindowConfig(
            window_size=self.config.window_size,
            preserve_first_n=self.config.preserve_first_n,
            preserve_last_n=self.config.preserve_last_n,
        )

        # Create token counter adapter
        token_counter = TokenCounterAdapter(self.count_tokens)

        # Create algorithm instance
        algorithm = SlidingWindowAlgorithm(algo_config, token_counter)

        def sliding_window_hook(state: dict[str, Any]) -> dict[str, Any]:
            """Apply sliding window using the algorithm."""
            messages = state.get("messages", [])

            if not messages:
                return {}

            # Log initial state if verbose
            if self.verbose:
                total_tokens = sum(self.count_tokens(msg) for msg in messages)
                self._log_initial_state(len(messages), total_tokens)

            # Run algorithm
            result = algorithm.select_messages(messages)

            # Check if no modification needed (all messages selected and under budget)
            if result.all_messages_selected and not result.exceeded_budget:
                if self.verbose:
                    print("[Sliding Window] Under window size, keeping all messages")
                return {}

            # Build trimmed messages in order
            trimmed_messages = [
                messages[i]
                for i in range(len(messages))
                if i in result.selected_indices
            ]

            # Log results if verbose
            if self.verbose:
                self._log_results(messages, trimmed_messages, result)

            return {"llm_input_messages": trimmed_messages}

        return sliding_window_hook

    def get_name(self) -> str:
        """Get strategy name."""
        return "sliding-window"

    def get_description(self) -> str:
        """Get strategy description."""
        return (
            "Sliding window that preserves first N Human/System messages and last M messages. "
            "After allocating first+last, fills remaining budget with middle messages working backwards. "
            "Maintains message integrity for tool call pairs and filters orphaned ToolMessages."
        )

    def _log_initial_state(self, message_count: int, total_tokens: int) -> None:
        """Log initial state information."""
        print(f"\n[Sliding Window] Processing {message_count} messages")
        print(f"[Sliding Window] Total tokens: {total_tokens:,}")
        print(f"[Sliding Window] Window size: {self.config.window_size:,}")
        print(
            f"[Sliding Window] Preserve first: {self.config.preserve_first_n} Human/System messages"
        )
        print(f"[Sliding Window] Preserve last: {self.config.preserve_last_n} messages")

    def _log_results(
        self, original_messages: list[Any], trimmed_messages: list[Any], result: Any
    ) -> None:
        """Log processing results."""
        original_count = len(original_messages)
        trimmed_count = len(trimmed_messages)
        original_tokens = sum(self.count_tokens(msg) for msg in original_messages)

        msg_reduction = (
            ((original_count - trimmed_count) / original_count * 100)
            if original_count
            else 0
        )
        token_reduction = (
            ((original_tokens - result.total_tokens) / original_tokens * 100)
            if original_tokens
            else 0
        )

        print("[Sliding Window] === RESULTS ===")
        print(
            f"[Sliding Window] Messages: {original_count} → {trimmed_count} "
            f"({msg_reduction:.1f}% reduction)"
        )
        print(
            f"[Sliding Window] Tokens: {original_tokens:,} → {result.total_tokens:,} "
            f"({token_reduction:.1f}% reduction)"
        )

        # Log selected indices
        self._log_selected_indices(result.selected_indices, result.total_tokens)

        # Log budget exceeded warning if applicable
        if result.exceeded_budget:
            print(
                f"[Sliding Window] NOTE: Exceeded window size by {result.exceeded_amount:,} tokens "
                "to maintain message integrity (expected behavior)"
            )

    def _log_selected_indices(self, indices: set[int], total_tokens: int) -> None:
        """Log which message indices were selected."""
        if len(indices) < 20:
            print(
                f"[Sliding Window] Kept indices: {sorted(indices)} ({total_tokens:,} tokens)"
            )
        else:
            # Show ranges for large sets
            ranges = self._format_index_ranges(sorted(indices))
            print(
                f"[Sliding Window] Kept ranges: {', '.join(ranges)} ({total_tokens:,} tokens)"
            )

    def _format_index_ranges(self, indices: list[int]) -> list[str]:
        """Format a list of indices as ranges."""
        if not indices:
            return []

        ranges = []
        start = indices[0]
        prev = indices[0]

        for idx in indices[1:]:
            if idx != prev + 1:
                ranges.append(f"{start}-{prev}" if start != prev else str(start))
                start = idx
            prev = idx

        # Add final range
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        return ranges


class TokenCounterAdapter:
    """Adapter to make token counting function compatible with protocol."""

    def __init__(self, count_tokens_fn):
        """Initialize with a token counting function."""
        self.count_tokens_fn = count_tokens_fn

    def count_tokens(self, message: Any) -> int:
        """Count tokens in a message."""
        return self.count_tokens_fn(message)
