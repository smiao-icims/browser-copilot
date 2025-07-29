"""
Tests for context management strategies
"""

from datetime import datetime, UTC

import pytest

from browser_copilot.context_management import ContextConfig, Message
from browser_copilot.context_management.base import MessageType, MessageImportance
from browser_copilot.context_management.strategies import NoOpStrategy, SlidingWindowStrategy


class TestNoOpStrategy:
    """Test the no-op baseline strategy"""
    
    def test_returns_all_messages(self):
        """No-op should return all messages unchanged"""
        strategy = NoOpStrategy()
        messages = [
            Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC),
                token_count=100
            )
            for i in range(10)
        ]
        config = ContextConfig()
        
        result = strategy.process_messages(messages, config)
        
        assert result == messages
        assert len(result) == 10
    
    def test_metrics_tracking(self):
        """No-op should track basic metrics"""
        strategy = NoOpStrategy()
        messages = [
            Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC),
                token_count=100
            )
            for i in range(5)
        ]
        config = ContextConfig()
        
        strategy.process_messages(messages, config)
        metrics = strategy.get_metrics()
        
        assert metrics["strategy"] == "no-op"
        assert metrics["total_messages_processed"] == 5
        assert metrics["total_tokens_processed"] == 500
        assert metrics["reduction_percentage"] == 0.0
        assert metrics["tokens_saved"] == 0


class TestSlidingWindowStrategy:
    """Test the sliding window strategy"""
    
    def test_under_window_size_returns_all(self):
        """Should return all messages if under window size"""
        strategy = SlidingWindowStrategy()
        messages = [
            Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC),
                token_count=100
            )
            for i in range(10)
        ]
        config = ContextConfig(window_size=2000)  # 10 messages * 100 tokens = 1000
        
        result = strategy.process_messages(messages, config)
        
        assert len(result) == 10
        metrics = strategy.get_metrics()
        assert metrics["token_metrics"]["reduction_percentage"] == 0.0
    
    def test_sliding_window_removes_middle_messages(self):
        """Should remove middle messages when over window size"""
        strategy = SlidingWindowStrategy()
        messages = []
        
        # Create 100 messages of 100 tokens each (10,000 tokens total)
        for i in range(100):
            messages.append(Message(
                type=MessageType.USER,
                content=f"Message {i}",
                timestamp=datetime.now(UTC),
                token_count=100
            ))
        
        # Window size of 3000 tokens
        config = ContextConfig(
            window_size=3000,
            preserve_first_n=5,  # 500 tokens
            preserve_last_n=10   # 1000 tokens
        )
        
        result = strategy.process_messages(messages, config)
        
        # Should have fewer messages
        assert len(result) < 100
        
        # Should preserve first 5
        assert result[0].content == "Message 0"
        assert result[4].content == "Message 4"
        
        # Should preserve last 10
        assert result[-10].content == "Message 90"
        assert result[-1].content == "Message 99"
        
        # Check metrics
        metrics = strategy.get_metrics()
        assert metrics["token_metrics"]["original"] == 10000
        assert metrics["token_metrics"]["processed"] <= 3000
        assert metrics["token_metrics"]["reduction_percentage"] > 0
    
    def test_preserves_critical_messages(self):
        """Should preserve critical messages regardless of position"""
        strategy = SlidingWindowStrategy()
        messages = []
        
        # Add regular messages
        for i in range(50):
            messages.append(Message(
                type=MessageType.USER,
                content=f"Regular message {i}",
                timestamp=datetime.now(UTC),
                token_count=100
            ))
        
        # Add a critical error in the middle
        error_msg = Message(
            type=MessageType.ERROR,
            content="Critical error occurred!",
            timestamp=datetime.now(UTC),
            token_count=100,
            importance=MessageImportance.CRITICAL
        )
        messages.insert(25, error_msg)
        
        config = ContextConfig(
            window_size=1500,  # 15 messages worth - room for preserved + critical
            preserve_errors=True,
            preserve_first_n=5,
            preserve_last_n=5
        )
        
        result = strategy.process_messages(messages, config)
        
        # Error message should be preserved
        assert any(msg.content == "Critical error occurred!" for msg in result)
        
        metrics = strategy.get_metrics()
        assert metrics["message_metrics"]["preserved"] > 0
        assert metrics["token_metrics"]["reduction_percentage"] > 0
    
    def test_comparison_with_noop(self):
        """Compare sliding window with no-op baseline"""
        noop = NoOpStrategy()
        sliding = SlidingWindowStrategy()
        
        # Create a large message set
        messages = [
            Message(
                type=MessageType.USER,
                content=f"Message {i}" * 10,  # Longer messages
                timestamp=datetime.now(UTC),
                token_count=200
            )
            for i in range(100)
        ]
        
        config = ContextConfig(window_size=5000)  # 25 messages worth
        
        # Process with both strategies
        noop_result = noop.process_messages(messages, config)
        sliding_result = sliding.process_messages(messages, config)
        
        # No-op should return all messages
        assert len(noop_result) == 100
        
        # Sliding window should reduce messages
        assert len(sliding_result) < 100
        
        # Compare metrics
        noop_metrics = noop.get_metrics()
        sliding_metrics = sliding.get_metrics()
        
        assert noop_metrics["reduction_percentage"] == 0.0
        assert sliding_metrics["token_metrics"]["reduction_percentage"] > 0
        
        # Calculate effectiveness
        token_savings = sliding_metrics["token_metrics"]["saved"]
        print(f"\nSliding window saved {token_savings} tokens ({sliding_metrics['token_metrics']['reduction_percentage']:.1f}% reduction)")