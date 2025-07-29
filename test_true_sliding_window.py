#!/usr/bin/env python3
"""Test script for true sliding window implementation"""

import asyncio
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from browser_copilot.context_management.base import ContextConfig
from browser_copilot.context_management.true_sliding_window import create_true_sliding_window_hook


def create_test_messages():
    """Create test messages with varying sizes and tool calls"""
    messages = []
    
    # System message
    messages.append(SystemMessage(content="You are a helpful assistant."))
    
    # Initial human message
    messages.append(HumanMessage(content="Please search for information about Python."))
    
    # AI response with tool call
    ai_msg1 = AIMessage(
        content="I'll search for Python information.",
        tool_calls=[{"id": "call_001", "name": "search", "args": {"query": "Python programming"}}]
    )
    messages.append(ai_msg1)
    
    # Tool response
    messages.append(ToolMessage(
        content="Python is a high-level programming language..." + "x" * 500,
        tool_call_id="call_001"
    ))
    
    # More conversation
    messages.append(HumanMessage(content="Tell me more about Python's features."))
    
    # Another AI response with tool call
    ai_msg2 = AIMessage(
        content="Let me get more details about Python features.",
        tool_calls=[{"id": "call_002", "name": "search", "args": {"query": "Python features"}}]
    )
    messages.append(ai_msg2)
    
    # Tool response
    messages.append(ToolMessage(
        content="Python features include dynamic typing, garbage collection..." + "x" * 800,
        tool_call_id="call_002"
    ))
    
    # Add more messages to create a longer conversation
    for i in range(10):
        messages.append(HumanMessage(content=f"Question {i}: " + "x" * (100 * (i + 1))))
        messages.append(AIMessage(content=f"Answer {i}: " + "y" * (150 * (i + 1))))
    
    # Final messages with tool calls
    ai_msg3 = AIMessage(
        content="Let me search for the latest information.",
        tool_calls=[{"id": "call_003", "name": "search", "args": {"query": "Latest Python news"}}]
    )
    messages.append(ai_msg3)
    
    messages.append(ToolMessage(
        content="Latest Python news: Python 3.12 released..." + "z" * 1000,
        tool_call_id="call_003"
    ))
    
    return messages


def test_true_sliding_window():
    """Test the true sliding window implementation"""
    print("=" * 80)
    print("Testing True Sliding Window Implementation")
    print("=" * 80)
    
    # Create test messages
    messages = create_test_messages()
    print(f"\nCreated {len(messages)} test messages")
    
    # Calculate total tokens
    total_tokens = sum(len(str(msg.content)) // 4 for msg in messages)
    print(f"Total tokens: {total_tokens:,}")
    
    # Test with different window sizes
    window_sizes = [1000, 2000, 5000, 10000]
    
    for window_size in window_sizes:
        print(f"\n{'=' * 60}")
        print(f"Testing with window_size={window_size:,} tokens")
        print(f"{'=' * 60}")
        
        # Create config
        config = ContextConfig(
            window_size=window_size,
            preserve_first_n=0,  # True sliding window doesn't preserve first
            preserve_last_n=0    # Not used in true sliding window
        )
        
        # Create hook
        hook = create_true_sliding_window_hook(config, verbose=True)
        
        # Test the hook
        state = {"messages": messages}
        result = hook(state)
        
        if "llm_input_messages" in result:
            trimmed = result["llm_input_messages"]
            trimmed_tokens = sum(len(str(msg.content)) // 4 for msg in trimmed)
            
            print(f"\nSummary:")
            print(f"- Original: {len(messages)} messages, {total_tokens:,} tokens")
            print(f"- Trimmed: {len(trimmed)} messages, {trimmed_tokens:,} tokens")
            print(f"- Reduction: {((total_tokens - trimmed_tokens) / total_tokens * 100):.1f}%")
            
            # Check message integrity
            print("\nIntegrity check:")
            ai_with_tools = 0
            tool_responses = 0
            orphaned_tools = 0
            
            for msg in trimmed:
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    ai_with_tools += 1
                    # Check if all tool responses are present
                    for tc in msg.tool_calls:
                        tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                        found = any(
                            isinstance(m, ToolMessage) and getattr(m, 'tool_call_id', None) == tc_id
                            for m in trimmed
                        )
                        if not found:
                            print(f"  WARNING: Missing tool response for {tc_id}")
                elif isinstance(msg, ToolMessage):
                    tool_responses += 1
                    # Check if AI message is present
                    tc_id = getattr(msg, 'tool_call_id', None)
                    found = any(
                        isinstance(m, AIMessage) and hasattr(m, 'tool_calls') and m.tool_calls and
                        any(tc.get('id') == tc_id if isinstance(tc, dict) else getattr(tc, 'id', None) == tc_id for tc in m.tool_calls)
                        for m in trimmed
                    )
                    if not found:
                        orphaned_tools += 1
                        print(f"  WARNING: Orphaned tool response with id {tc_id}")
            
            print(f"  AI messages with tool calls: {ai_with_tools}")
            print(f"  Tool responses: {tool_responses}")
            print(f"  Orphaned tool responses: {orphaned_tools}")
            print(f"  Integrity maintained: {'YES' if orphaned_tools == 0 else 'NO'}")
        else:
            print("\nNo trimming applied (under window size)")


if __name__ == "__main__":
    test_true_sliding_window()