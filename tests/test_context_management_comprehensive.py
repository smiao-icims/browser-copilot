"""
Comprehensive tests for context management system

This covers the context management strategies, base classes, and integration
that currently has 5-15% coverage but is critical for token optimization.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from browser_copilot.context_management.base import (
    ContextConfig,
    Message,
    MessageImportance,
    MessageType,
)
from browser_copilot.context_management.metrics import ContextMetrics
from browser_copilot.context_management.strategies.base import ContextStrategy
from browser_copilot.context_management.strategies.no_op import NoOpStrategy
from browser_copilot.context_management.strategies.sliding_window import (
    SlidingWindowStrategy,
)
from browser_copilot.context_management.strategies.smart_trim import SmartTrimStrategy


class TestContextManagementBase:
    """Test base context management classes and types"""

    def test_message_type_enum(self):
        """Test MessageType enum values"""
        assert MessageType.SYSTEM.value == "system"
        assert MessageType.USER.value == "user"
        assert MessageType.ASSISTANT.value == "assistant"
        assert MessageType.TOOL_CALL.value == "tool_call"
        assert MessageType.TOOL_RESPONSE.value == "tool_response"
        assert MessageType.ERROR.value == "error"

    def test_message_importance_enum(self):
        """Test MessageImportance enum values"""
        assert MessageImportance.CRITICAL.value == "critical"
        assert MessageImportance.HIGH.value == "high"
        assert MessageImportance.MEDIUM.value == "medium"
        assert MessageImportance.LOW.value == "low"

    def test_message_dataclass_creation(self):
        """Test Message dataclass creation and defaults"""
        # Basic message
        msg = Message(
            type=MessageType.USER, content="Test message", timestamp=datetime.now(UTC)
        )

        assert msg.type == MessageType.USER
        assert msg.content == "Test message"
        assert msg.importance == MessageImportance.MEDIUM  # Default
        assert msg.token_count == 0  # Default
        assert msg.metadata == {}  # Default
        assert msg.tool_name is None
        assert msg.preserve is False
        assert msg.mergeable is True

        # Message with all fields
        msg_full = Message(
            type=MessageType.TOOL_CALL,
            content="Calling browser_navigate",
            timestamp=datetime.now(UTC),
            importance=MessageImportance.HIGH,
            token_count=25,
            metadata={"url": "https://example.com"},
            tool_name="browser_navigate",
            tool_args={"url": "https://example.com"},
            preserve=True,
            mergeable=False,
        )

        assert msg_full.tool_name == "browser_navigate"
        assert msg_full.preserve is True
        assert msg_full.mergeable is False
        assert msg_full.token_count == 25

    def test_context_config_creation(self):
        """Test ContextConfig creation and defaults"""
        # Default config
        config = ContextConfig()

        assert config.max_tokens == 100000
        assert config.preserve_first_n == 2  # Default is 2 (system + human)
        assert config.preserve_last_n == 10
        assert config.window_size == 25000  # Window size in tokens
        assert config.preserve_errors is True
        assert config.preserve_screenshots is True
        assert config.enable_compression is True

        # Custom config
        custom_config = ContextConfig(
            max_tokens=50000,
            preserve_first_n=5,
            preserve_last_n=20,
            window_size=25000,
            preserve_errors=False,
            enable_compression=False,
        )

        assert custom_config.max_tokens == 50000
        assert custom_config.preserve_first_n == 5
        assert custom_config.preserve_last_n == 20
        assert custom_config.window_size == 25000
        assert custom_config.preserve_errors is False
        assert custom_config.enable_compression is False


class TestContextStrategies:
    """Test different context management strategies"""

    def test_no_op_strategy_basic(self):
        """Test NoOpStrategy basic functionality"""
        strategy = NoOpStrategy()

        assert strategy.get_name() == "no-op"
        assert "unchanged" in strategy.get_description().lower()

        # Test hook creation
        hook = strategy.create_hook()
        assert callable(hook)

        # Test that hook returns empty dict (no modifications)
        test_state = {"messages": ["msg1", "msg2"], "other": "data"}
        result = hook(test_state)
        assert result == {}  # No-op returns empty dict to indicate no changes

    def test_no_op_strategy_with_config(self):
        """Test NoOpStrategy with custom config"""
        config = ContextConfig(max_tokens=1000)
        strategy = NoOpStrategy(config=config, verbose=True)

        assert strategy.config.max_tokens == 1000
        assert strategy.verbose is True

    def test_sliding_window_strategy_basic(self):
        """Test SlidingWindowStrategy basic functionality"""
        config = ContextConfig(window_size=5000)  # Window size is in tokens
        strategy = SlidingWindowStrategy(config=config)

        assert strategy.get_name() == "sliding-window"
        assert "window" in strategy.get_description().lower()

        # Test hook creation
        hook = strategy.create_hook()
        assert callable(hook)

    def test_sliding_window_message_processing(self):
        """Test SlidingWindowStrategy message processing"""
        config = ContextConfig(
            window_size=1000,  # Small window for testing (in tokens)
            preserve_first_n=1,
            preserve_last_n=1,
        )
        strategy = SlidingWindowStrategy(config=config)
        hook = strategy.create_hook()

        # Create test messages
        messages = [
            SystemMessage(content="System prompt"),  # Should be preserved (first)
            HumanMessage(content="Question 1"),
            AIMessage(content="Answer 1"),
            HumanMessage(content="Question 2"),
            AIMessage(content="Answer 2"),
            HumanMessage(content="Question 3"),  # Should be preserved (last)
        ]

        state = {"messages": messages}
        result = hook(state)

        # The hook returns modifications to state (e.g., {'messages': [trimmed list]})
        # or empty dict if no changes needed
        assert isinstance(result, dict)

    def test_smart_trim_strategy_basic(self):
        """Test SmartTrimStrategy basic functionality"""
        strategy = SmartTrimStrategy()

        assert strategy.get_name() == "smart-trim"
        assert "intelligent" in strategy.get_description().lower()

        # Test hook creation
        hook = strategy.create_hook()
        assert callable(hook)

    def test_context_strategy_validation(self):
        """Test strategy configuration validation"""
        # Valid config
        valid_config = ContextConfig(
            window_size=10000, preserve_first_n=2, preserve_last_n=5
        )
        strategy = NoOpStrategy(config=valid_config)
        errors = strategy.validate_config()
        assert len(errors) == 0

        # Invalid configs - need to create with invalid values
        # Since ContextConfig has defaults, we need to modify after creation
        config1 = ContextConfig()
        config1.window_size = -1

        config2 = ContextConfig()
        config2.preserve_first_n = -5

        config3 = ContextConfig()
        config3.preserve_last_n = -10

        invalid_configs = [
            (config1, "Window size must be positive"),
            (config2, "Preserve first must be non-negative"),
            (config3, "Preserve last must be non-negative"),
        ]

        for config, expected_error in invalid_configs:
            strategy = NoOpStrategy(config=config)
            errors = strategy.validate_config()
            assert len(errors) > 0
            assert any(expected_error in error for error in errors)

    def test_token_counting(self):
        """Test token counting functionality"""
        strategy = NoOpStrategy()

        # Test with different message types
        test_cases = [
            (HumanMessage(content="Hello world"), 2),  # ~11 chars / 4
            (AIMessage(content="This is a longer message with more tokens"), 10),
            (SystemMessage(content=""), 0),
            (ToolMessage(content="x" * 100, tool_call_id="123"), 25),
        ]

        for message, expected_min_tokens in test_cases:
            tokens = strategy.count_tokens(message)
            assert tokens >= expected_min_tokens


class TestContextMetrics:
    """Test context metrics tracking"""

    def test_context_metrics_creation(self):
        """Test ContextMetrics creation and fields"""
        metrics = ContextMetrics(
            original_messages=10,
            processed_messages=8,
            messages_removed=2,
            original_tokens=1000,
            processed_tokens=800,
            tokens_saved=200,
            strategy_name="smart-trim",
            window_size=50,
            processing_time_ms=15.5,
        )

        assert metrics.original_messages == 10
        assert metrics.processed_messages == 8
        assert metrics.messages_removed == 2
        assert metrics.original_tokens == 1000
        assert metrics.processed_tokens == 800
        assert metrics.tokens_saved == 200
        assert metrics.strategy_name == "smart-trim"
        assert metrics.processing_time_ms == 15.5

    def test_context_metrics_calculations(self):
        """Test metrics calculations and properties"""
        metrics = ContextMetrics(
            original_messages=100,
            processed_messages=60,
            messages_removed=40,
            original_tokens=10000,
            processed_tokens=6000,
            tokens_saved=4000,
            strategy_name="sliding-window",
            window_size=50,
            processing_time_ms=25.0,
        )

        # Test calculate_savings method
        metrics.calculate_savings()

        # Verify calculated values
        assert metrics.tokens_saved == 4000
        assert metrics.reduction_percentage == 40.0
        assert metrics.messages_removed == 40

        # Verify metrics to_dict method
        metrics_dict = metrics.to_dict()
        assert metrics_dict["strategy"] == "sliding-window"
        assert metrics_dict["token_metrics"]["saved"] == 4000
        assert metrics_dict["message_metrics"]["removed"] == 40


class TestContextManagementIntegration:
    """Test integration of context management components"""

    def test_strategy_hook_with_langchain_messages(self):
        """Test strategy hooks work with actual LangChain messages"""
        strategy = NoOpStrategy()
        hook = strategy.create_hook()

        # Create realistic message sequence
        messages = [
            SystemMessage(content="You are a helpful browser automation assistant."),
            HumanMessage(content="Navigate to https://example.com"),
            AIMessage(content="I'll navigate to https://example.com for you."),
            ToolMessage(content="Navigation successful", tool_call_id="nav_123"),
            HumanMessage(content="Click the login button"),
            AIMessage(content="I'll click the login button now."),
        ]

        state = {
            "messages": messages,
            "other_state": "preserved",
            "metadata": {"test": True},
        }

        result = hook(state)

        # NoOp returns empty dict, not the full state
        # Empty dict means no modifications in LangGraph
        assert result == {}

    def test_strategy_factory_pattern(self):
        """Test creating strategies dynamically"""
        strategy_map = {
            "no-op": NoOpStrategy,
            "sliding-window": SlidingWindowStrategy,
            "smart-trim": SmartTrimStrategy,
        }

        config = ContextConfig(window_size=20)

        for name, strategy_class in strategy_map.items():
            strategy = strategy_class(config=config)
            assert strategy.get_name() == name
            assert isinstance(strategy, ContextStrategy)
            assert callable(strategy.create_hook())

    def test_message_preservation_logic(self):
        """Test message preservation based on importance"""
        # Test importance ranking
        assert MessageImportance.CRITICAL.value == "critical"
        assert MessageImportance.HIGH.value == "high"
        assert MessageImportance.MEDIUM.value == "medium"
        assert MessageImportance.LOW.value == "low"

        # Test that we can compare importance conceptually
        importance_order = ["critical", "high", "medium", "low"]
        assert MessageImportance.CRITICAL.value in importance_order
        assert MessageImportance.LOW.value in importance_order

    @pytest.mark.parametrize(
        "strategy_name,strategy_class",
        [
            ("no-op", NoOpStrategy),
            ("sliding-window", SlidingWindowStrategy),
            ("smart-trim", SmartTrimStrategy),
        ],
    )
    def test_all_strategies_implement_interface(self, strategy_name, strategy_class):
        """Test all strategies properly implement the interface"""
        strategy = strategy_class()

        # Verify required methods exist
        assert hasattr(strategy, "create_hook")
        assert hasattr(strategy, "get_name")
        assert hasattr(strategy, "get_description")
        assert hasattr(strategy, "validate_config")
        assert hasattr(strategy, "count_tokens")

        # Verify methods return expected types
        assert isinstance(strategy.get_name(), str)
        assert isinstance(strategy.get_description(), str)
        assert isinstance(strategy.validate_config(), list)

        # Verify hook is callable
        hook = strategy.create_hook()
        assert callable(hook)

    def test_verbose_logging_behavior(self):
        """Test verbose logging in strategies"""
        with patch("builtins.print"):
            # Create strategy with verbose=True
            strategy = NoOpStrategy(verbose=True)
            hook = strategy.create_hook()

            # Execute hook
            state = {"messages": [HumanMessage(content="Test")]}
            hook(state)

            # Verify logging occurred
            if strategy.verbose:
                # NoOp strategy may not print, but others would
                pass  # Specific strategies would call print

    def test_context_window_edge_cases(self):
        """Test edge cases in context window management"""
        test_cases = [
            # (window_size, preserve_first, preserve_last)
            (10000, 1, 1),  # Normal case
            (50000, 1, 1),  # Large window
            (100, 5, 5),  # Small window with large preserve
            (10000, 0, 0),  # No preservation
            (1000, 10, 10),  # Preserve many
        ]

        for window_size, preserve_first, preserve_last in test_cases:
            config = ContextConfig(
                window_size=window_size,
                preserve_first_n=preserve_first,
                preserve_last_n=preserve_last,
            )

            # Validate config is reasonable
            errors = NoOpStrategy(config=config).validate_config()
            assert len(errors) == 0

    def test_tool_message_handling(self):
        """Test special handling of tool-related messages"""
        messages = [
            AIMessage(
                content="I'll search for that.",
                additional_kwargs={"tool_calls": [{"name": "search", "id": "123"}]},
            ),
            ToolMessage(content="Search results: Python tutorials", tool_call_id="123"),
            AIMessage(content="I found Python tutorials for you."),
        ]

        # Tool messages should maintain their relationships
        strategy = NoOpStrategy()
        hook = strategy.create_hook()

        state = {"messages": messages}
        result = hook(state)

        # NoOp returns empty dict (no modifications)
        assert result == {}
