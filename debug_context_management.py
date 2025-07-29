"""
Debug script to verify context management is working
"""

import asyncio
from datetime import datetime, UTC

from browser_copilot.context_management import (
    BrowserCopilotContextManager,
    ContextConfig,
    Message,
    MessageType,
)


async def test_context_manager():
    """Test the context manager with sample messages"""
    
    # Create a context manager with small window
    config = ContextConfig(
        window_size=1000,  # Very small window
        preserve_first_n=2,
        preserve_last_n=3,
    )
    
    manager = BrowserCopilotContextManager(
        config=config,
        strategy="sliding-window"
    )
    
    # Add many messages
    print("Adding 50 messages...")
    for i in range(50):
        manager.add_message(Message(
            type=MessageType.USER,
            content=f"This is message number {i} with some content to increase token count. " * 5,
            timestamp=datetime.now(UTC)
        ))
    
    # Get processed context
    context = manager.get_context()
    
    print(f"\nOriginal messages: {len(manager._raw_messages)}")
    print(f"Processed messages: {len(context)}")
    print(f"\nContext summary:\n{manager.get_summary()}")
    
    # Show which messages were kept
    print("\nKept messages:")
    for i, msg in enumerate(context):
        preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  [{i}] {preview}")


async def test_no_op():
    """Test no-op strategy"""
    manager = BrowserCopilotContextManager(
        strategy="no-op"
    )
    
    # Add messages
    for i in range(10):
        manager.add_message(Message(
            type=MessageType.USER,
            content=f"Message {i}",
            timestamp=datetime.now(UTC)
        ))
    
    context = manager.get_context()
    print(f"\nNo-op strategy: {len(context)} messages (should be 10)")


if __name__ == "__main__":
    print("Testing Context Management\n" + "="*50)
    asyncio.run(test_context_manager())
    asyncio.run(test_no_op())