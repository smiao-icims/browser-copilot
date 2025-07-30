"""
Tests for message analyzer
"""

from datetime import UTC, datetime

from browser_copilot.context_management import (
    ImportanceScorer,
    Message,
    MessageAnalyzer,
    MessageImportance,
    MessageType,
)


class TestMessageAnalyzer:
    """Test message analysis functionality"""

    def test_token_counting(self):
        """Test token counting accuracy"""
        analyzer = MessageAnalyzer()

        # Simple text
        count = analyzer.count_tokens("Hello, world!")
        assert count > 0
        assert count < 10  # Should be around 4 tokens

        # Longer text
        long_text = (
            "This is a much longer text that should have many more tokens. " * 10
        )
        long_count = analyzer.count_tokens(long_text)
        assert long_count > count
        assert long_count > 50

    def test_analyze_message_updates_token_count(self):
        """Test that analyze_message updates token count"""
        analyzer = MessageAnalyzer()

        message = Message(
            type=MessageType.USER,
            content="Test message content",
            timestamp=datetime.now(UTC),
            token_count=0,  # Not set
        )

        analyzed = analyzer.analyze_message(message)

        assert analyzed.token_count > 0
        assert analyzed.token_count < 20

    def test_importance_detection_critical(self):
        """Test detection of critical importance"""
        analyzer = MessageAnalyzer()

        critical_messages = [
            "Error: Failed to load page",
            "FATAL: System crashed",
            "Exception occurred during execution",
            "Critical failure in test",
        ]

        for content in critical_messages:
            message = Message(
                type=MessageType.ASSISTANT, content=content, timestamp=datetime.now(UTC)
            )
            analyzed = analyzer.analyze_message(message)
            assert analyzed.importance == MessageImportance.CRITICAL

    def test_importance_detection_high(self):
        """Test detection of high importance"""
        analyzer = MessageAnalyzer()

        high_messages = [
            "Warning: Page loading slowly",
            "Taking screenshot of current state",
            "Navigating to https://example.com",
            "Clicking on submit button",
            "Test passed successfully",
        ]

        for content in high_messages:
            message = Message(
                type=MessageType.ASSISTANT, content=content, timestamp=datetime.now(UTC)
            )
            analyzed = analyzer.analyze_message(message)
            assert analyzed.importance == MessageImportance.HIGH

    def test_importance_error_type_is_critical(self):
        """Test that ERROR type messages are always critical"""
        MessageAnalyzer()

        message = Message(
            type=MessageType.ERROR,
            content="Some regular content",
            timestamp=datetime.now(UTC),
        )

        # Should be critical due to type, not content
        assert message.importance == MessageImportance.CRITICAL

    def test_content_type_detection(self):
        """Test content type detection"""
        analyzer = MessageAnalyzer()

        test_cases = [
            ("DOM tree snapshot of the page", "snapshot"),
            ("Console messages: [info] Page loaded", "console"),
            ("Navigating to homepage", "navigation"),
            ("Clicking on login button", "interaction"),
            ("Error: Element not found", "error"),
            ("Just some general text", "general"),
        ]

        for content, expected_type in test_cases:
            message = Message(
                type=MessageType.TOOL_RESPONSE,
                content=content,
                timestamp=datetime.now(UTC),
            )
            content_type = analyzer.get_content_type(message)
            assert content_type == expected_type

    def test_tool_name_content_type(self):
        """Test content type detection based on tool name"""
        analyzer = MessageAnalyzer()

        message = Message(
            type=MessageType.TOOL_RESPONSE,
            content="Some content",
            timestamp=datetime.now(UTC),
            tool_name="browser_snapshot",
        )

        assert analyzer.get_content_type(message) == "snapshot"


class TestImportanceScorer:
    """Test importance scoring"""

    def test_base_scoring(self):
        """Test base importance scores"""
        scorer = ImportanceScorer()

        critical_msg = Message(
            type=MessageType.ASSISTANT,
            content="Critical error",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.CRITICAL,
        )

        high_msg = Message(
            type=MessageType.ASSISTANT,
            content="Important action",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.HIGH,
        )

        low_msg = Message(
            type=MessageType.ASSISTANT,
            content="Minor detail",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.LOW,
        )

        assert scorer.score_message(critical_msg) > scorer.score_message(high_msg)
        assert scorer.score_message(high_msg) > scorer.score_message(low_msg)
        assert scorer.score_message(critical_msg) <= 1.0
        assert scorer.score_message(low_msg) >= 0.0

    def test_error_boost(self):
        """Test that error messages get boosted scores"""
        scorer = ImportanceScorer()

        regular_msg = Message(
            type=MessageType.ASSISTANT,
            content="Regular message",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.MEDIUM,
        )

        error_msg = Message(
            type=MessageType.ERROR,
            content="Error message",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.MEDIUM,
        )

        regular_score = scorer.score_message(regular_msg)
        error_score = scorer.score_message(error_msg)

        assert error_score > regular_score

    def test_length_penalty(self):
        """Test that very long messages get penalized"""
        scorer = ImportanceScorer()

        short_msg = Message(
            type=MessageType.ASSISTANT,
            content="Short",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.MEDIUM,
            token_count=10,
        )

        long_msg = Message(
            type=MessageType.ASSISTANT,
            content="Long" * 500,
            timestamp=datetime.now(UTC),
            importance=MessageImportance.MEDIUM,
            token_count=1500,
        )

        very_long_msg = Message(
            type=MessageType.ASSISTANT,
            content="Very long" * 1000,
            timestamp=datetime.now(UTC),
            importance=MessageImportance.MEDIUM,
            token_count=3000,
        )

        short_score = scorer.score_message(short_msg)
        long_score = scorer.score_message(long_msg)
        very_long_score = scorer.score_message(very_long_msg)

        assert short_score > long_score
        assert long_score > very_long_score
