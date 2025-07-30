"""
AskHuman tool for proper human-in-the-loop interactions.

This tool allows the agent to explicitly ask for human input and continue
execution after receiving a response, using LangGraph's interrupt mechanism.
"""

from typing import Optional
from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_human(question: str, context: Optional[str] = None) -> str:
    """
    Ask a human for input when the agent needs clarification or data.
    
    This tool uses LangGraph's interrupt mechanism to pause execution
    and wait for human input. The agent will continue after receiving
    a response via Command(resume=...).
    
    Args:
        question: The question to ask the human
        context: Optional context about why the question is being asked
        
    Returns:
        The human's response
    """
    # In automated testing mode, we can provide default responses
    # based on common patterns
    interrupt_data = {
        "type": "human_question",
        "question": question,
        "context": context,
        "tool": "ask_human",
    }
    
    # Check for common test patterns and suggest responses
    question_lower = question.lower()
    if "color" in question_lower:
        interrupt_data["suggested_response"] = "blue"
    elif "search" in question_lower:
        interrupt_data["suggested_response"] = "artificial intelligence"
    elif "name" in question_lower:
        interrupt_data["suggested_response"] = "John Doe"
    elif "continue" in question_lower or "proceed" in question_lower:
        interrupt_data["suggested_response"] = "yes"
    else:
        interrupt_data["suggested_response"] = "Continue with the test"
    
    # Use interrupt to pause execution
    human_response = interrupt(interrupt_data)
    
    # Return the response (will be the value from Command(resume=...))
    return human_response


@tool
def confirm_action(action: str, details: Optional[str] = None) -> bool:
    """
    Request human confirmation before performing an action.
    
    Args:
        action: The action that requires confirmation
        details: Additional details about the action
        
    Returns:
        True if confirmed, False otherwise
    """
    interrupt_data = {
        "type": "confirmation_request",
        "action": action,
        "details": details,
        "tool": "confirm_action",
        "suggested_response": "yes"  # Default to yes in automated mode
    }
    
    response = interrupt(interrupt_data)
    
    # Convert response to boolean
    if isinstance(response, bool):
        return response
    
    response_lower = str(response).lower()
    return response_lower in ["yes", "y", "true", "confirm", "proceed", "continue"]