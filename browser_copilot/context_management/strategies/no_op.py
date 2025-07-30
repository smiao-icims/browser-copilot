"""
No-op context management strategy.

This strategy does not modify messages and serves as a baseline
for comparison with other strategies.
"""

from typing import Any

from .base import ContextStrategy, PreModelHook


class NoOpStrategy(ContextStrategy):
    """
    No-operation strategy that passes messages through unchanged.

    This strategy is useful for:
    - Baseline comparisons
    - Debugging
    - When token usage is not a concern
    """

    def create_hook(self) -> PreModelHook:
        """
        Create a no-op pre-model hook.

        Returns:
            A hook that returns an empty dict (no modifications)
        """

        def no_op_hook(state: dict[str, Any]) -> dict[str, Any]:
            """No-op hook that doesn't modify messages."""
            if self.verbose:
                messages = state.get("messages", [])
                print(f"\n[No-Op Strategy] Processing {len(messages)} messages")
                print("[No-Op Strategy] Returning messages unchanged")

            # Return empty dict to keep messages unchanged
            return {}

        return no_op_hook

    def get_name(self) -> str:
        """Get strategy name."""
        return "no-op"

    def get_description(self) -> str:
        """Get strategy description."""
        return (
            "No-operation strategy that passes messages through unchanged. "
            "Useful for baseline comparison and debugging."
        )
