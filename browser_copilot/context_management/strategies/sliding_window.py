"""
Sliding window context management strategy.

This strategy preserves first N Human/System messages and fills the
remaining budget with the most recent messages, working backwards.
"""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .base import ContextStrategy, PreModelHook


class SlidingWindowStrategy(ContextStrategy):
    """
    True sliding window strategy that keeps last N tokens.

    This strategy:
    1. Preserves the first N Human and System messages (test instructions & system prompts)
    2. Preserves the last M messages (with integrity for tool pairs)
    3. Fills remaining budget with messages working backwards from (last M - 1)
    4. Uses a SOFT budget - message integrity is prioritized over token limit

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

        def sliding_window_hook(state: dict[str, Any]) -> dict[str, Any]:
            """Apply sliding window - preserve first N + last M + fill middle."""
            messages = state.get("messages", [])

            if not messages:
                return {}

            # Calculate total tokens
            total_tokens = sum(self.count_tokens(msg) for msg in messages)

            if self.verbose:
                print(f"\n[Sliding Window] Processing {len(messages)} messages")
                print(f"[Sliding Window] Total tokens: {total_tokens:,}")
                print(f"[Sliding Window] Window size: {self.config.window_size:,}")
                print(
                    f"[Sliding Window] Preserve first: {self.config.preserve_first_n} Human/System messages"
                )
                print(
                    f"[Sliding Window] Preserve last: {self.config.preserve_last_n} messages"
                )

            # If under window size, keep all
            if total_tokens <= self.config.window_size:
                if self.verbose:
                    print("[Sliding Window] Under window size, keeping all messages")
                return {}

            # Step 1: Build tool dependency map
            tool_dependencies: dict[int, set[int]] = (
                {}
            )  # Maps message index to indices it depends on
            reverse_dependencies: dict[int, set[int]] = (
                {}
            )  # Maps message index to indices that depend on it

            for i, msg in enumerate(messages):
                if (
                    isinstance(msg, AIMessage)
                    and hasattr(msg, "tool_calls")
                    and msg.tool_calls
                ):
                    # This AIMessage has tool calls
                    for tc in msg.tool_calls:
                        tc_id = (
                            tc.get("id")
                            if isinstance(tc, dict)
                            else getattr(tc, "id", None)
                        )
                        if tc_id:
                            # Find the corresponding ToolMessage
                            for j in range(i + 1, len(messages)):
                                if (
                                    isinstance(messages[j], ToolMessage)
                                    and getattr(messages[j], "tool_call_id", None)
                                    == tc_id
                                ):
                                    # AIMessage depends on ToolMessage
                                    if i not in tool_dependencies:
                                        tool_dependencies[i] = set()
                                    tool_dependencies[i].add(j)
                                    # ToolMessage is depended on by AIMessage
                                    if j not in reverse_dependencies:
                                        reverse_dependencies[j] = set()
                                    reverse_dependencies[j].add(i)
                                    break

            # Step 2: First, preserve the first N Human/System messages
            selected_indices = set()
            current_tokens = 0

            # Count and preserve Human and System messages
            preserve_count = 0
            for i, msg in enumerate(messages):
                if isinstance(msg, HumanMessage | SystemMessage):
                    selected_indices.add(i)
                    current_tokens += self.count_tokens(msg)
                    preserve_count += 1
                    if preserve_count >= self.config.preserve_first_n:
                        break

            if self.verbose and preserve_count > 0:
                print(
                    f"[Sliding Window] Preserved first {preserve_count} Human/System messages ({current_tokens:,} tokens)"
                )

            # Step 3: ALWAYS add the last M messages (with integrity)
            # NOTE: Message integrity is MORE important than token budget - we use a soft budget
            last_m_start = max(
                preserve_count, len(messages) - self.config.preserve_last_n
            )

            # Add last M messages
            for i in range(last_m_start, len(messages)):
                if i not in selected_indices:
                    selected_indices.add(i)
                    current_tokens += self.count_tokens(messages[i])

            # Ensure integrity: if any message in last M is a ToolMessage, include its AIMessage
            # if any message in last M is an AIMessage with tools, include its ToolMessages
            # This may cause us to exceed our budget, but message integrity is critical
            integrity_additions = set()
            for i in range(last_m_start, len(messages)):
                # If it's a ToolMessage, we need its AIMessage
                if i in reverse_dependencies:
                    for dep_idx in reverse_dependencies[i]:
                        if dep_idx not in selected_indices:
                            integrity_additions.add(dep_idx)
                # If it's an AIMessage, we need its ToolMessages
                if i in tool_dependencies:
                    for dep_idx in tool_dependencies[i]:
                        if dep_idx not in selected_indices:
                            integrity_additions.add(dep_idx)

            # Add integrity dependencies (even if it exceeds budget)
            for idx in integrity_additions:
                selected_indices.add(idx)
                current_tokens += self.count_tokens(messages[idx])
                if self.verbose:
                    print(
                        f"[Sliding Window] Added message {idx} for integrity (soft budget)"
                    )

            last_m_count = len([i for i in selected_indices if i >= last_m_start])
            if self.verbose and last_m_count > 0:
                last_m_tokens = sum(
                    self.count_tokens(messages[i])
                    for i in selected_indices
                    if i >= last_m_start
                )
                print(
                    f"[Sliding Window] Preserved last {last_m_count} messages with integrity ({last_m_tokens:,} tokens)"
                )

            # Step 4: Check if we have budget left for middle messages
            if current_tokens > self.config.window_size:
                if self.verbose:
                    print(
                        f"[Sliding Window] WARNING: First {preserve_count} + Last {last_m_count} = {current_tokens:,} tokens (exceeds {self.config.window_size:,})"
                    )
                    print("[Sliding Window] No budget for middle messages")
            else:
                # Fill with messages from (last M - 1) backwards
                remaining_budget = self.config.window_size - current_tokens
                if self.verbose and remaining_budget > 0:
                    print(
                        f"[Sliding Window] Remaining budget for middle messages: {remaining_budget:,} tokens"
                    )

                # Find the rightmost unselected message before last M
                right_boundary = last_m_start - 1
                # Also consider any integrity additions that might be before last_m_start
                for idx in selected_indices:
                    if idx < last_m_start and idx > preserve_count:
                        right_boundary = min(right_boundary, idx - 1)

                # Work backwards from the right boundary
                i = right_boundary
                while i >= preserve_count and remaining_budget > 0:
                    if i in selected_indices:
                        i -= 1
                        continue

                    # Check what we need to add for this message
                    to_add = {i}

                    # If it's a ToolMessage, we need its AIMessage
                    if i in reverse_dependencies:
                        for dep_idx in reverse_dependencies[i]:
                            to_add.add(dep_idx)

                    # If it's an AIMessage with tool calls, we need ALL its ToolMessages
                    if i in tool_dependencies:
                        for dep_idx in tool_dependencies[i]:
                            to_add.add(dep_idx)

                    # Remove already selected messages from to_add
                    new_to_add = to_add - selected_indices

                    # If nothing new to add, skip
                    if not new_to_add:
                        i -= 1
                        continue

                    # Calculate tokens needed for NEW messages only
                    tokens_needed = sum(
                        self.count_tokens(messages[idx]) for idx in new_to_add
                    )

                    # Check if we can fit this
                    if tokens_needed <= remaining_budget:
                        selected_indices.update(new_to_add)
                        current_tokens += tokens_needed
                        remaining_budget -= tokens_needed

                        if self.verbose:
                            sorted_added = sorted(new_to_add)
                            if len(sorted_added) == 1:
                                print(
                                    f"[Sliding Window] Added middle message {sorted_added[0]} ({tokens_needed} tokens)"
                                )
                            else:
                                print(
                                    f"[Sliding Window] Added middle messages {sorted_added} ({tokens_needed} tokens)"
                                )
                    else:
                        # Cannot fit this message - STOP HERE
                        if self.verbose:
                            print(
                                f"[Sliding Window] Cannot fit message {i} ({tokens_needed} tokens) - stopping here"
                            )
                        break

                    i -= 1

            # Step 5: Build final message list in order
            trimmed_messages = []
            for i in range(len(messages)):
                if i in selected_indices:
                    trimmed_messages.append(messages[i])

            if self.verbose:
                self._print_results(
                    messages, trimmed_messages, total_tokens, selected_indices
                )

            # Return the trimmed messages
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
            "Maintains message integrity for tool call pairs."
        )

    def _print_results(
        self, messages, trimmed_messages, total_tokens, selected_indices
    ):
        """Print verbose results."""
        trimmed_tokens = sum(self.count_tokens(msg) for msg in trimmed_messages)
        msg_reduction = (
            ((len(messages) - len(trimmed_messages)) / len(messages) * 100)
            if messages
            else 0
        )
        token_reduction = (
            ((total_tokens - trimmed_tokens) / total_tokens * 100)
            if total_tokens
            else 0
        )

        print("[Sliding Window] === RESULTS ===")
        print(
            f"[Sliding Window] Messages: {len(messages)} → {len(trimmed_messages)} ({msg_reduction:.1f}% reduction)"
        )
        print(
            f"[Sliding Window] Tokens: {total_tokens:,} → {trimmed_tokens:,} ({token_reduction:.1f}% reduction)"
        )

        # Show which messages were kept
        if len(selected_indices) < 20:  # Only show if reasonable number
            print(
                f"[Sliding Window] Kept indices: {sorted(selected_indices)} ({trimmed_tokens:,} tokens)"
            )
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

            print(
                f"[Sliding Window] Kept ranges: {', '.join(ranges)} ({trimmed_tokens:,} tokens)"
            )

        # Check if we exceeded budget for integrity
        if trimmed_tokens > self.config.window_size:
            print(
                f"[Sliding Window] NOTE: Exceeded window size by {trimmed_tokens - self.config.window_size:,} tokens to maintain message integrity (expected behavior)"
            )
