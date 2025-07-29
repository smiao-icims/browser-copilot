"""
Debug script to understand the bad request issue with sliding window
"""
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

# Create a ToolMessage like we do in the hook
tool_msg = ToolMessage(
    content="Test content",
    tool_call_id="preserved"
)

print("ToolMessage attributes:")
print(f"- content: {tool_msg.content}")
print(f"- tool_call_id: {tool_msg.tool_call_id}")
print(f"- type: {tool_msg.type}")

# Check what attributes a ToolMessage needs
print("\nToolMessage required fields:")
print(ToolMessage.__annotations__)

# Convert to dict to see structure
print("\nToolMessage as dict:")
print(tool_msg.dict())