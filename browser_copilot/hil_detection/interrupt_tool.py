"""
Human-in-the-loop tool using LangGraph's interrupt mechanism.
"""

from typing import Optional
from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_human(question: str) -> str:
    """
    Ask a human for input when the agent needs clarification or data.
    
    This tool uses LangGraph's interrupt mechanism to pause execution
    and wait for human input via the Command resume pattern.
    
    Args:
        question: The question to ask the human
        
    Returns:
        The human's response
    """
    # Use interrupt to pause execution and wait for human input
    human_response = interrupt({
        "type": "human_question",
        "question": question,
        "metadata": {
            "tool": "ask_human",
            "timestamp": None  # Would be filled by the system
        }
    })
    
    # The execution will resume here when a Command(resume=...) is provided
    return human_response.get("response", human_response.get("data", ""))


@tool  
def request_approval(action: str, details: Optional[str] = None) -> bool:
    """
    Request human approval before performing a critical action.
    
    Args:
        action: The action that requires approval
        details: Additional details about the action
        
    Returns:
        True if approved, False otherwise
    """
    approval_response = interrupt({
        "type": "approval_request",
        "action": action,
        "details": details,
        "metadata": {
            "tool": "request_approval",
            "critical": True
        }
    })
    
    return approval_response.get("approved", False)


# Example of how to use these tools with create_react_agent:
"""
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Create checkpointer (required for interrupt)
checkpointer = MemorySaver()

# Create agent with interrupt-enabled tools
agent = create_react_agent(
    model=llm,
    tools=[ask_human, request_approval, ...other_tools],
    checkpointer=checkpointer
)

# Run with config that includes thread_id
config = {"configurable": {"thread_id": "test-session-1"}}

# Initial run - will pause at interrupt
for chunk in agent.stream({"messages": [HumanMessage(content="...")]}, config):
    print(chunk)
    # Check if interrupted
    if "__interrupt__" in chunk:
        print("Agent is waiting for human input...")
        break

# Resume with human input
from langgraph.types import Command

for chunk in agent.stream(
    Command(resume={"response": "AI Advertisement"}), 
    config
):
    print(chunk)
"""