"""
Debug script to understand tool_calls in messages
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Create an AIMessage with tool_calls
ai_msg = AIMessage(
    content="I'll navigate to the page",
    tool_calls=[{
        "id": "call_123",
        "name": "browser_navigate",
        "args": {"url": "https://example.com"}
    }]
)

# The corresponding ToolMessage must have matching tool_call_id
tool_msg = ToolMessage(
    content="Navigation successful",
    tool_call_id="call_123"  # Must match the id in tool_calls
)

print("AIMessage attributes:")
print(f"- content: {ai_msg.content}")
print(f"- tool_calls: {ai_msg.tool_calls}")

print("\nToolMessage attributes:")
print(f"- content: {tool_msg.content}")
print(f"- tool_call_id: {tool_msg.tool_call_id}")

# Check what happens if we create messages without proper pairing
print("\n\nCreating orphaned ToolMessage:")
orphan_tool_msg = ToolMessage(
    content="Some response",
    tool_call_id="orphan_id"  # No matching AIMessage with this tool_call
)
print(f"This might cause issues: {orphan_tool_msg}")