#!/usr/bin/env python3
"""Debug script to test sliding window trimming"""

from datetime import datetime, UTC
from browser_copilot.context_management.base import Message, MessageType, ContextConfig
from browser_copilot.context_management.strategies.sliding_window import SlidingWindowStrategy

# Create test messages with varying sizes
messages = []
for i in range(10):
    content = f"Message {i}: " + "x" * (100 * (i + 1))  # Increasing size
    token_count = len(content) // 4
    msg = Message(
        type=MessageType.USER if i % 3 == 0 else MessageType.ASSISTANT,
        content=content,
        timestamp=datetime.now(UTC),
        token_count=token_count
    )
    messages.append(msg)
    print(f"Message {i}: {token_count} tokens")

# Calculate total tokens
total_tokens = sum(msg.token_count for msg in messages)
print(f"\nTotal tokens: {total_tokens}")

# Test with different window sizes
for window_size in [500, 1000, 2000]:
    print(f"\n--- Testing with window_size={window_size} ---")
    
    config = ContextConfig(
        window_size=window_size,
        preserve_first_n=2,
        preserve_last_n=2
    )
    
    strategy = SlidingWindowStrategy()
    processed = strategy.process_messages(messages, config)
    
    processed_tokens = sum(msg.token_count for msg in processed)
    print(f"Processed messages: {len(processed)}/{len(messages)}")
    print(f"Processed tokens: {processed_tokens}")
    print(f"Reduction: {((total_tokens - processed_tokens) / total_tokens * 100):.1f}%")
    
    # Show which messages were kept
    kept_indices = []
    for i, orig_msg in enumerate(messages):
        for proc_msg in processed:
            if orig_msg.content == proc_msg.content:
                kept_indices.append(i)
                break
    print(f"Kept message indices: {kept_indices}")