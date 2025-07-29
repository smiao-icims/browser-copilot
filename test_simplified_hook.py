"""
Test script to compare our implementation with the simplified LangChain approach
"""
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from browser_copilot.context_management.base import ContextConfig
from browser_copilot.context_management.react_hooks import create_sliding_window_hook
from browser_copilot.context_management.react_hooks_simplified import (
    create_sliding_window_hook_simplified,
    create_advanced_sliding_window_hook
)


async def test_hooks():
    # Create test configuration
    config = ContextConfig(
        window_size=1000,  # Small window to force trimming
        preserve_first_n=2,
        preserve_last_n=2,
    )
    
    # Create test messages
    messages = [
        HumanMessage(content="Start the test"),
        AIMessage(content="I'll help you test", tool_calls=[
            {"id": "call_1", "name": "navigate", "args": {"url": "test.com"}}
        ]),
        ToolMessage(content="Navigated successfully", tool_call_id="call_1"),
        HumanMessage(content="Take a screenshot"),
        AIMessage(content="Taking screenshot", tool_calls=[
            {"id": "call_2", "name": "screenshot", "args": {}}
        ]),
        ToolMessage(content="Screenshot taken", tool_call_id="call_2"),
        HumanMessage(content="Click the button"),
        AIMessage(content="Clicking button"),
        HumanMessage(content="What happened?"),
        AIMessage(content="The page loaded successfully"),
    ]
    
    state = {"messages": messages}
    
    print("=== Original Implementation ===")
    original_hook = create_sliding_window_hook(config, verbose=True)
    result1 = original_hook(state)
    print(f"Original returned {len(result1.get('llm_input_messages', messages))} messages\n")
    
    print("=== Simplified Implementation ===")
    simplified_hook = create_sliding_window_hook_simplified(config, verbose=True)
    result2 = simplified_hook(state)
    print(f"Simplified returned {len(result2.get('llm_input_messages', messages))} messages\n")
    
    print("=== Advanced Simplified Implementation ===")
    advanced_hook = create_advanced_sliding_window_hook(config, verbose=True)
    result3 = advanced_hook(state)
    print(f"Advanced returned {len(result3.get('llm_input_messages', messages))} messages\n")


if __name__ == "__main__":
    asyncio.run(test_hooks())