"""
Debug script to reproduce the bad request issue
"""
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from browser_copilot.context_management.react_hooks import create_sliding_window_hook
from browser_copilot.context_management.base import ContextConfig

async def test_hook():
    # Create a hook with small window
    config = ContextConfig(
        window_size=500,  # Very small to trigger windowing
        preserve_first_n=1,
        preserve_last_n=1,
    )
    
    hook = create_sliding_window_hook(config, verbose=True)
    
    # Create test messages including a ToolMessage
    # Make messages large enough to trigger windowing
    large_content = "x" * 500  # Large content to consume tokens
    
    messages = [
        HumanMessage(content="Test the website"),
        AIMessage(content=f"I'll test it now. {large_content}"),
        ToolMessage(
            content=f"Navigation successful. {large_content}", 
            tool_call_id="test-123"
        ),
        AIMessage(content=f"The test is complete. {large_content}"),
        HumanMessage(content="What happened?"),
        AIMessage(content="Here's the summary"),
    ]
    
    # Call the hook
    state = {"messages": messages}
    result = hook(state)
    
    # Check token counts
    if hasattr(hook, 'context_manager'):
        metrics = hook.context_manager.get_metrics()
        print(f"\nToken metrics:")
        if 'token_metrics' in metrics:
            print(f"  Original tokens: {metrics['token_metrics'].get('original_tokens', 0)}")
            print(f"  Processed tokens: {metrics['token_metrics'].get('processed_tokens', 0)}")
        print(f"  Window size: {config.window_size}")
    
    print("\nResult:")
    print(f"Number of messages returned: {len(result.get('llm_input_messages', []))}")
    
    for i, msg in enumerate(result.get('llm_input_messages', [])):
        print(f"{i}: {type(msg).__name__} - {msg.content[:50]}...")
        if isinstance(msg, ToolMessage):
            print(f"   tool_call_id: {msg.tool_call_id}")

if __name__ == "__main__":
    asyncio.run(test_hook())