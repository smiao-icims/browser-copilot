"""
Tests for the context manager
"""

from datetime import datetime, UTC

import pytest

from browser_copilot.context_management import (
    BrowserCopilotContextManager,
    ContextConfig,
    Message,
    MessageType,
    MessageImportance,
)


class TestBrowserCopilotContextManager:
    """Test the main context manager"""
    
    def test_initialization(self):
        """Test context manager initialization"""
        manager = BrowserCopilotContextManager()
        
        assert manager.config is not None
        assert manager.analyzer is not None
        assert manager.strategy is not None
        assert len(manager._raw_messages) == 0
    
    def test_strategy_selection(self):
        """Test different strategy selection"""
        # Default should be sliding-window
        manager1 = BrowserCopilotContextManager()
        assert manager1.metrics.strategy_name == "sliding-window"
        
        # Explicit no-op
        manager2 = BrowserCopilotContextManager(strategy="no-op")
        assert manager2.metrics.strategy_name == "no-op"
        
        # Invalid strategy
        with pytest.raises(ValueError):
            BrowserCopilotContextManager(strategy="invalid")
    
    def test_add_message(self):
        """Test adding messages"""
        manager = BrowserCopilotContextManager()
        
        message = Message(
            type=MessageType.USER,
            content="Test message",
            timestamp=datetime.now(UTC)
        )
        
        manager.add_message(message)
        
        assert len(manager._raw_messages) == 1
        assert manager._raw_messages[0].token_count > 0  # Should be analyzed
        assert manager._total_tokens > 0
    
    def test_get_context_empty(self):
        """Test getting context when empty"""
        manager = BrowserCopilotContextManager()
        context = manager.get_context()
        
        assert context == []
    
    def test_get_context_with_messages(self):
        """Test getting context with messages"""
        manager = BrowserCopilotContextManager()
        
        # Add some messages
        for i in range(10):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC)
            ))
        
        context = manager.get_context()
        
        assert len(context) == 10
        assert all(msg.token_count > 0 for msg in context)
    
    def test_no_op_vs_sliding_window(self):
        """Test difference between no-op and sliding window strategies"""
        # Create many messages that exceed window size
        messages = []
        for i in range(100):
            messages.append(Message(
                type=MessageType.USER,
                content=f"This is message number {i} with some longer content to ensure we have enough tokens. " * 3,
                timestamp=datetime.now(UTC)
            ))
        
        # No-op manager
        noop_manager = BrowserCopilotContextManager(
            strategy="no-op",
            config=ContextConfig(window_size=1000)
        )
        noop_manager.add_messages(messages)
        noop_context = noop_manager.get_context()
        
        # Sliding window manager
        sliding_manager = BrowserCopilotContextManager(
            strategy="sliding-window",
            config=ContextConfig(window_size=1000)
        )
        sliding_manager.add_messages(messages)
        sliding_context = sliding_manager.get_context()
        
        # No-op should return all messages
        assert len(noop_context) == 100
        
        # Sliding window should reduce messages
        assert len(sliding_context) < 100
        
        # Compare metrics
        noop_metrics = noop_manager.get_metrics()
        sliding_metrics = sliding_manager.get_metrics()
        
        assert noop_metrics["token_metrics"]["reduction_percentage"] == 0.0
        assert sliding_metrics["token_metrics"]["reduction_percentage"] > 0.0
    
    def test_critical_message_preservation(self):
        """Test that critical messages are preserved"""
        config = ContextConfig(
            window_size=500,  # Small window
            preserve_errors=True,
            preserve_first_n=5,
            preserve_last_n=5
        )
        manager = BrowserCopilotContextManager(
            strategy="sliding-window",
            config=config
        )
        
        # Add many regular messages with more tokens
        for i in range(50):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Regular message {i} with additional content to increase token count",
                timestamp=datetime.now(UTC)
            ))
        
        # Add a critical error
        manager.add_message(Message(
            type=MessageType.ERROR,
            content="Critical system error!",
            timestamp=datetime.now(UTC)
        ))
        
        # Add more regular messages
        for i in range(50, 100):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Regular message {i} with additional content to increase token count",
                timestamp=datetime.now(UTC)
            ))
        
        context = manager.get_context()
        
        # Should have reduced messages but kept the error
        assert len(context) < 101
        assert any(msg.content == "Critical system error!" for msg in context)
    
    def test_metrics(self):
        """Test metrics calculation"""
        manager = BrowserCopilotContextManager(
            config=ContextConfig(window_size=500)
        )
        
        # Add messages
        for i in range(50):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Message {i}" * 5,  # Make them longer
                timestamp=datetime.now(UTC)
            ))
        
        context = manager.get_context()
        metrics = manager.get_metrics()
        
        assert metrics["strategy"] == "sliding-window"
        assert metrics["token_metrics"]["original"] > 0
        assert metrics["token_metrics"]["processed"] > 0
        assert metrics["message_metrics"]["original"] == 50
        
        # Should have some reduction
        if len(context) < 50:
            assert metrics["token_metrics"]["reduction_percentage"] > 0
            assert metrics["token_metrics"]["saved"] > 0
    
    def test_clear_context(self):
        """Test clearing the context"""
        manager = BrowserCopilotContextManager()
        
        # Add messages
        for i in range(10):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC)
            ))
        
        assert len(manager._raw_messages) == 10
        assert manager._total_tokens > 0
        
        # Clear
        manager.clear_context()
        
        assert len(manager._raw_messages) == 0
        assert manager._total_tokens == 0
        assert len(manager.get_context()) == 0
    
    def test_get_summary(self):
        """Test summary generation"""
        manager = BrowserCopilotContextManager()
        
        # Empty summary
        assert "empty" in manager.get_summary().lower()
        
        # Add messages
        for i in range(20):
            manager.add_message(Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC)
            ))
        
        summary = manager.get_summary()
        
        assert "sliding-window" in summary
        assert "Original: 20 messages" in summary
        assert "tokens" in summary
        assert "Processing time" in summary
    
    def test_analyzer_integration(self):
        """Test that analyzer properly analyzes messages"""
        manager = BrowserCopilotContextManager()
        
        # Add message with error content
        error_msg = Message(
            type=MessageType.ASSISTANT,
            content="Error: Failed to connect",
            timestamp=datetime.now(UTC)
        )
        
        manager.add_message(error_msg)
        
        # Should be analyzed and marked as critical
        stored_msg = manager._raw_messages[0]
        assert stored_msg.importance == MessageImportance.CRITICAL
        assert stored_msg.token_count > 0