"""
Unit tests for the sliding window algorithm.

These tests verify the algorithm independently of the LangChain hook mechanism.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from browser_copilot.context_management.algorithms.sliding_window_algorithm import (
    SlidingWindowAlgorithm,
    SlidingWindowConfig,
)


class MockTokenCounter:
    """Mock token counter for testing."""

    def count_tokens(self, message) -> int:
        """Simple token counting based on message content length."""
        content = getattr(message, "content", "")
        # Approximate: 1 token per 4 characters
        return len(content) // 4 + 1


class TestSlidingWindowAlgorithm:
    """Test cases for the sliding window algorithm."""

    @pytest.fixture
    def token_counter(self):
        """Provide a mock token counter."""
        return MockTokenCounter()

    @pytest.fixture
    def default_config(self):
        """Provide default configuration."""
        return SlidingWindowConfig(
            window_size=100, preserve_first_n=2, preserve_last_n=3
        )

    def test_empty_messages(self, default_config, token_counter):
        """Test with empty message list."""
        algo = SlidingWindowAlgorithm(default_config, token_counter)
        result = algo.select_messages([])

        assert result.selected_indices == set()
        assert result.total_tokens == 0
        assert not result.exceeded_budget

    def test_under_budget(self, default_config, token_counter):
        """Test when all messages fit within budget."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="How are you?"),
            AIMessage(content="I'm doing well"),
        ]

        algo = SlidingWindowAlgorithm(default_config, token_counter)
        result = algo.select_messages(messages)

        # All messages should be selected
        assert result.selected_indices == {0, 1, 2, 3}
        assert not result.exceeded_budget

    def test_preserve_first_human_system(self, default_config, token_counter):
        """Test that first N Human/System messages are preserved."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="First human message"),
            AIMessage(content="AI response"),
            HumanMessage(content="Second human message"),
            AIMessage(content="Another AI response"),
        ]

        algo = SlidingWindowAlgorithm(default_config, token_counter)
        result = algo.select_messages(messages)

        # First 2 Human/System messages should be included
        assert 0 in result.selected_indices  # SystemMessage
        assert 1 in result.selected_indices  # First HumanMessage

    def test_preserve_last_messages(self, token_counter):
        """Test that last M messages are preserved."""
        config = SlidingWindowConfig(
            window_size=50, preserve_first_n=1, preserve_last_n=3
        )

        messages = [
            HumanMessage(content="Start"),
            AIMessage(content="Response 1" * 10),  # Make it large
            HumanMessage(content="Middle" * 10),  # Make it large
            AIMessage(content="Response 2" * 10),  # Make it large
            HumanMessage(content="Last 1"),
            AIMessage(content="Last 2"),
            HumanMessage(content="Last 3"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Last 3 messages should always be included
        assert 4 in result.selected_indices  # Last 3
        assert 5 in result.selected_indices  # Last 2
        assert 6 in result.selected_indices  # Last 1

    def test_tool_message_integrity(self, default_config, token_counter):
        """Test that tool message pairs are kept together."""
        tool_call_id = "tool_123"

        messages = [
            HumanMessage(content="Do something"),
            AIMessage(
                content="I'll help",
                tool_calls=[{"id": tool_call_id, "name": "test_tool", "args": {}}],
            ),
            ToolMessage(content="Tool result", tool_call_id=tool_call_id),
            HumanMessage(content="Thanks"),
        ]

        algo = SlidingWindowAlgorithm(default_config, token_counter)
        result = algo.select_messages(messages)

        # If AIMessage is selected, ToolMessage must be too
        if 1 in result.selected_indices:
            assert 2 in result.selected_indices
        # If ToolMessage is selected, AIMessage must be too
        if 2 in result.selected_indices:
            assert 1 in result.selected_indices

    def test_soft_budget_for_integrity(self, token_counter):
        """Test that budget can be exceeded to maintain integrity."""
        config = SlidingWindowConfig(
            window_size=20,  # Very small budget
            preserve_first_n=1,
            preserve_last_n=2,
        )

        tool_call_id = "tool_456"

        messages = [
            HumanMessage(
                content="Start message with some content that is longer to use more tokens"
            ),  # ~17 tokens
            AIMessage(
                content="Middle message with lots of content to use many many tokens here"
            ),  # ~16 tokens
            HumanMessage(
                content="Another message with more content here"
            ),  # ~10 tokens
            AIMessage(
                content="AI with tool call and more content",  # ~9 tokens
                tool_calls=[{"id": tool_call_id, "name": "test", "args": {}}],
            ),
            ToolMessage(
                content="Tool result data with extra content", tool_call_id=tool_call_id
            ),  # ~9 tokens
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Should exceed budget to keep tool pair together
        assert result.exceeded_budget
        assert result.exceeded_amount > 0
        # Both tool messages should be included
        assert 3 in result.selected_indices
        assert 4 in result.selected_indices

    def test_middle_filling_backwards(self, token_counter):
        """Test that middle messages are filled backwards."""
        config = SlidingWindowConfig(
            window_size=100, preserve_first_n=1, preserve_last_n=2
        )

        messages = [
            HumanMessage(content="First"),  # 0 - preserved (first)
            AIMessage(content="Response 1"),  # 1
            HumanMessage(content="Middle 1"),  # 2
            AIMessage(content="Response 2"),  # 3
            HumanMessage(content="Middle 2"),  # 4
            AIMessage(content="Response 3"),  # 5
            HumanMessage(content="Last 1"),  # 6 - preserved (last)
            AIMessage(content="Last 2"),  # 7 - preserved (last)
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Should have first, last 2, and fill backwards
        assert 0 in result.selected_indices  # First
        assert 6 in result.selected_indices  # Last 2
        assert 7 in result.selected_indices  # Last 2

        # Should fill from index 5 backwards
        if result.total_tokens < config.window_size:
            # If there's room, newer middle messages should be preferred
            assert 5 in result.selected_indices or 4 in result.selected_indices

    def test_complex_tool_dependencies(self, token_counter):
        """Test with multiple tool calls and complex dependencies."""
        config = SlidingWindowConfig(
            window_size=80, preserve_first_n=1, preserve_last_n=3
        )

        tool_id_1 = "tool_001"
        tool_id_2 = "tool_002"

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="Using tool 1",
                tool_calls=[{"id": tool_id_1, "name": "tool1", "args": {}}],
            ),
            ToolMessage(content="Result 1", tool_call_id=tool_id_1),
            HumanMessage(content="Continue"),
            AIMessage(
                content="Using tool 2",
                tool_calls=[{"id": tool_id_2, "name": "tool2", "args": {}}],
            ),
            ToolMessage(content="Result 2", tool_call_id=tool_id_2),
            HumanMessage(content="Final"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Verify tool pairs are kept together
        if 1 in result.selected_indices:
            assert 2 in result.selected_indices
        if 4 in result.selected_indices:
            assert 5 in result.selected_indices

    def test_first_plus_last_exceeds_budget(self, token_counter):
        """Test when first + last messages exceed budget."""
        config = SlidingWindowConfig(
            window_size=20,  # Very small
            preserve_first_n=2,
            preserve_last_n=3,
        )

        messages = [
            SystemMessage(content="Long system prompt " * 5),
            HumanMessage(content="Long first message " * 5),
            AIMessage(content="Middle 1"),
            HumanMessage(content="Middle 2"),
            AIMessage(content="Long last message 1 " * 5),
            HumanMessage(content="Long last message 2 " * 5),
            AIMessage(content="Long last message 3 " * 5),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Should include first 2 and last 3 despite exceeding budget
        assert 0 in result.selected_indices
        assert 1 in result.selected_indices
        assert 4 in result.selected_indices
        assert 5 in result.selected_indices
        assert 6 in result.selected_indices

        # Should exceed budget
        assert result.exceeded_budget

        # No middle messages should be included
        assert 2 not in result.selected_indices
        assert 3 not in result.selected_indices

    def test_tool_message_in_last_n_requires_ai_from_middle(self, token_counter):
        """Test when ToolMessage in last N requires AIMessage from middle."""
        config = SlidingWindowConfig(
            window_size=50, preserve_first_n=1, preserve_last_n=2
        )

        tool_call_id = "critical_tool"

        messages = [
            HumanMessage(content="Start"),  # 0 - first
            AIMessage(content="Response 1"),  # 1
            HumanMessage(content="Middle"),  # 2
            AIMessage(  # 3 - needed for integrity
                content="Using tool",
                tool_calls=[{"id": tool_call_id, "name": "tool", "args": {}}],
            ),
            HumanMessage(content="Another middle"),  # 4
            ToolMessage(content="Tool result", tool_call_id=tool_call_id),  # 5 - last 2
            HumanMessage(content="Final"),  # 6 - last 2
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Must include first, last 2, AND the AIMessage for integrity
        assert 0 in result.selected_indices  # First
        assert 5 in result.selected_indices  # Last 2 (ToolMessage)
        assert 6 in result.selected_indices  # Last 2
        assert 3 in result.selected_indices  # AIMessage for integrity

    def test_first_n_skips_ai_and_tool_messages(self, token_counter):
        """Test that first N only selects Human/System messages."""
        config = SlidingWindowConfig(
            window_size=15,  # Smaller window to force selection
            preserve_first_n=2,
            preserve_last_n=2,
        )

        tool_call_id = "early_tool"

        messages = [
            SystemMessage(content="System"),  # 0 - first Human/System
            AIMessage(  # 1 - SKIPPED (not Human/System)
                content="Using early tool",
                tool_calls=[{"id": tool_call_id, "name": "tool", "args": {}}],
            ),
            HumanMessage(content="First human"),  # 2 - first Human/System (2nd)
            ToolMessage(
                content="Tool result", tool_call_id=tool_call_id
            ),  # 3 - SKIPPED
            HumanMessage(content="Second human"),  # 4 - NOT first N (already have 2)
            AIMessage(content="Last 1"),  # 5 - last 2
            HumanMessage(content="Last 2"),  # 6 - last 2
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # First N should only include System and first Human message
        assert 0 in result.selected_indices  # System (first)
        assert 2 in result.selected_indices  # First Human (second)
        assert 1 not in result.selected_indices  # AIMessage skipped
        assert 5 in result.selected_indices  # Last 2
        assert 6 in result.selected_indices  # Last 2

    def test_multiple_tool_calls_in_one_ai_message(self, token_counter):
        """Test AIMessage with multiple tool calls."""
        config = SlidingWindowConfig(
            window_size=100, preserve_first_n=1, preserve_last_n=4
        )

        tool_id_1 = "multi_tool_1"
        tool_id_2 = "multi_tool_2"

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="Using multiple tools",
                tool_calls=[
                    {"id": tool_id_1, "name": "tool1", "args": {}},
                    {"id": tool_id_2, "name": "tool2", "args": {}},
                ],
            ),
            ToolMessage(content="Result 1", tool_call_id=tool_id_1),
            ToolMessage(content="Result 2", tool_call_id=tool_id_2),
            HumanMessage(content="End"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # If AIMessage is selected, both ToolMessages must be included
        if 1 in result.selected_indices:
            assert 2 in result.selected_indices
            assert 3 in result.selected_indices

    def test_orphaned_tool_message(self, token_counter):
        """Test ToolMessage without corresponding AIMessage when over budget."""
        config = SlidingWindowConfig(
            window_size=8,  # Small window to force trimming
            preserve_first_n=1,
            preserve_last_n=2,
        )

        messages = [
            HumanMessage(content="Start message here"),  # ~5 tokens
            # Orphaned ToolMessage (no corresponding AIMessage)
            ToolMessage(
                content="Orphaned result data here", tool_call_id="nonexistent"
            ),  # ~6 tokens
            HumanMessage(content="Another message here"),  # ~5 tokens
            AIMessage(content="Last AI message here"),  # ~5 tokens
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Orphaned ToolMessage should be filtered out when trimming
        assert 0 in result.selected_indices  # First
        assert 1 not in result.selected_indices  # Orphaned ToolMessage REMOVED
        assert 2 in result.selected_indices  # Last 2
        assert 3 in result.selected_indices  # Last 2

    def test_tool_message_far_from_ai_message(self, token_counter):
        """Test when ToolMessage is far from its AIMessage."""
        config = SlidingWindowConfig(
            window_size=80, preserve_first_n=1, preserve_last_n=2
        )

        tool_call_id = "distant_tool"

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="Tool call",
                tool_calls=[{"id": tool_call_id, "name": "tool", "args": {}}],
            ),
            HumanMessage(content="Filler 1"),
            AIMessage(content="Filler 2"),
            HumanMessage(content="Filler 3"),
            AIMessage(content="Filler 4"),
            ToolMessage(content="Delayed result", tool_call_id=tool_call_id),
            HumanMessage(content="End"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Algorithm should still find the connection despite distance
        if 6 in result.selected_indices:  # If ToolMessage selected
            assert 1 in result.selected_indices  # AIMessage must be too

    def test_interleaved_tool_calls(self, token_counter):
        """Test interleaved tool calls and results."""
        config = SlidingWindowConfig(
            window_size=120, preserve_first_n=1, preserve_last_n=5
        )

        tool_id_1 = "tool_A"
        tool_id_2 = "tool_B"

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="First tool",
                tool_calls=[{"id": tool_id_1, "name": "toolA", "args": {}}],
            ),
            AIMessage(
                content="Second tool before first completes",
                tool_calls=[{"id": tool_id_2, "name": "toolB", "args": {}}],
            ),
            ToolMessage(content="Result A", tool_call_id=tool_id_1),
            ToolMessage(content="Result B", tool_call_id=tool_id_2),
            HumanMessage(content="Done"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Verify correct pairing despite interleaving
        if 3 in result.selected_indices:  # ToolMessage A
            assert 1 in result.selected_indices  # AIMessage A
        if 4 in result.selected_indices:  # ToolMessage B
            assert 2 in result.selected_indices  # AIMessage B

    def test_no_human_or_system_messages(self, token_counter):
        """Test when there are no Human/System messages to preserve."""
        config = SlidingWindowConfig(
            window_size=50, preserve_first_n=2, preserve_last_n=2
        )

        messages = [
            AIMessage(content="AI 1"),
            AIMessage(content="AI 2"),
            AIMessage(content="AI 3"),
            AIMessage(content="AI 4"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Should only preserve last 2 since no Human/System messages exist
        assert 2 in result.selected_indices
        assert 3 in result.selected_indices
        # First messages won't be preserved as they're not Human/System

    def test_missing_tool_message_for_ai_call(self, token_counter):
        """Test when AIMessage has tool call but ToolMessage is missing."""
        config = SlidingWindowConfig(
            window_size=80, preserve_first_n=1, preserve_last_n=3
        )

        tool_call_id = "missing_result"

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="Tool call without result",
                tool_calls=[{"id": tool_call_id, "name": "tool", "args": {}}],
            ),
            # Missing ToolMessage here!
            HumanMessage(content="Continue without result"),
            AIMessage(content="Last message"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Should handle gracefully - AIMessage can exist without ToolMessage
        assert 0 in result.selected_indices  # First
        assert (
            1 in result.selected_indices
        )  # Last 3 (AIMessage with unfulfilled tool call)
        assert 2 in result.selected_indices  # Last 3
        assert 3 in result.selected_indices  # Last 3

    def test_malformed_tool_call_id(self, token_counter):
        """Test when tool_call_id doesn't match between messages."""
        config = SlidingWindowConfig(
            window_size=5,  # Small window to force trimming
            preserve_first_n=1,
            preserve_last_n=2,
        )

        messages = [
            HumanMessage(content="Start"),
            AIMessage(
                content="Tool call",
                tool_calls=[{"id": "call_123", "name": "tool", "args": {}}],
            ),
            ToolMessage(content="Result", tool_call_id="call_456"),  # Different ID!
            HumanMessage(content="End"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # ToolMessage with mismatched ID is orphaned and filtered out
        assert 0 in result.selected_indices  # First
        assert 2 not in result.selected_indices  # Orphaned ToolMessage REMOVED
        assert 3 in result.selected_indices  # Last 2
        # AIMessage may or may not be selected based on budget

    def test_multiple_orphaned_tool_messages(self, token_counter):
        """Test multiple orphaned ToolMessages are filtered out when trimming."""
        config = SlidingWindowConfig(
            window_size=12,  # Small window to force trimming
            preserve_first_n=1,
            preserve_last_n=2,
        )

        messages = [
            HumanMessage(content="Start"),  # 0
            ToolMessage(content="Orphan 1", tool_call_id="orphan1"),  # 1 - orphaned
            AIMessage(content="Normal AI"),  # 2
            ToolMessage(content="Orphan 2", tool_call_id="orphan2"),  # 3 - orphaned
            HumanMessage(content="Middle"),  # 4
            AIMessage(  # 5
                content="AI with tool",
                tool_calls=[{"id": "valid_tool", "name": "tool", "args": {}}],
            ),
            ToolMessage(
                content="Valid result", tool_call_id="valid_tool"
            ),  # 6 - valid pair
            HumanMessage(content="End"),  # 7
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Verify orphaned messages are filtered out
        assert 0 in result.selected_indices  # First
        assert 1 not in result.selected_indices  # Orphaned
        assert 3 not in result.selected_indices  # Orphaned
        assert 6 in result.selected_indices  # Last 2 (valid ToolMessage)
        assert 7 in result.selected_indices  # Last 2
        # The valid tool pair should be kept together
        if 6 in result.selected_indices:
            assert 5 in result.selected_indices  # AIMessage for integrity

    def test_orphaned_tool_message_under_budget(self, token_counter):
        """Test orphaned ToolMessages are kept when under budget."""
        config = SlidingWindowConfig(
            window_size=100,  # Large window - everything fits
            preserve_first_n=1,
            preserve_last_n=2,
        )

        messages = [
            HumanMessage(content="Start"),
            ToolMessage(content="Orphaned 1", tool_call_id="orphan1"),
            AIMessage(content="AI message"),
            ToolMessage(content="Orphaned 2", tool_call_id="orphan2"),
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Under budget - all messages kept including orphaned ones
        assert result.selected_indices == {0, 1, 2, 3}
        assert not result.exceeded_budget

    def test_tool_message_in_last_n_with_ai_message_before(self, token_counter):
        """Test critical bug: ToolMessage in last N with AIMessage before preserve range."""
        config = SlidingWindowConfig(
            window_size=25,  # Small window
            preserve_first_n=2,
            preserve_last_n=10,
        )

        tool_call_id = "browser_snapshot_123"

        # Simulate the exact scenario from the error
        messages = [
            HumanMessage(content="Test instruction"),  # 0 - preserve first
            SystemMessage(content="System prompt"),  # 1 - preserve first
            AIMessage(  # 2 - NOT in last 10
                content="I'll take a snapshot",
                tool_calls=[
                    {"id": tool_call_id, "name": "browser_snapshot", "args": {}}
                ],
            ),
            ToolMessage(
                content="Snapshot result", tool_call_id=tool_call_id
            ),  # 3 - in last 10
            HumanMessage(content="Continue"),  # 4
            AIMessage(content="Response 1"),  # 5 - last 10
            HumanMessage(content="Message 6"),  # 6 - last 10
            AIMessage(content="Response 7"),  # 7 - last 10
            HumanMessage(content="Message 8"),  # 8 - last 10
            AIMessage(content="Response 9"),  # 9 - last 10
            HumanMessage(content="Message 10"),  # 10 - last 10
            AIMessage(content="Response 11"),  # 11 - last 10
            HumanMessage(content="Message 12"),  # 12 - last 10
            AIMessage(content="Response 13"),  # 13 - last 10
            HumanMessage(content="Final message"),  # 14 - last 10
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # CRITICAL: If index 3 (ToolMessage) is selected, index 2 (AIMessage) MUST be too
        if 3 in result.selected_indices:
            assert 2 in result.selected_indices, "ToolMessage without its AIMessage!"

        # Verify first 2 are preserved
        assert 0 in result.selected_indices
        assert 1 in result.selected_indices

        # Verify last 10 are preserved (indices 5-14)
        for i in range(5, 15):
            assert i in result.selected_indices

    def test_no_gaps_in_message_sequence(self, token_counter):
        """Test that gaps in message sequences are filled."""
        config = SlidingWindowConfig(
            window_size=30,  # Small window
            preserve_first_n=1,
            preserve_last_n=5,
        )

        tool_call_id = "test_tool"

        messages = [
            HumanMessage(content="Start"),  # 0 - first
            AIMessage(content="Response 1"),  # 1
            AIMessage(  # 2
                content="Tool call",
                tool_calls=[{"id": tool_call_id, "name": "tool", "args": {}}],
            ),
            ToolMessage(
                content="Result", tool_call_id=tool_call_id
            ),  # 3 - may be selected for integrity
            HumanMessage(
                content="Middle message"
            ),  # 4 - THIS COULD BE SKIPPED creating a gap!
            AIMessage(content="Response 5"),  # 5 - last 5
            HumanMessage(content="Message 6"),  # 6 - last 5
            AIMessage(content="Response 7"),  # 7 - last 5
            HumanMessage(content="Message 8"),  # 8 - last 5
            AIMessage(content="Final"),  # 9 - last 5
        ]

        algo = SlidingWindowAlgorithm(config, token_counter)
        result = algo.select_messages(messages)

        # Convert to sorted list
        indices = sorted(result.selected_indices)

        # Check for no small gaps (gaps of 1-2 messages should be filled)
        for i in range(len(indices) - 1):
            gap = indices[i + 1] - indices[i] - 1
            # Small gaps (1-2 messages) should be filled
            assert gap == 0 or gap > 2, (
                f"Small gap of {gap} messages found between indices {indices[i]} and {indices[i + 1]}"
            )
