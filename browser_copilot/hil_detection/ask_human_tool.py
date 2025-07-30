"""
AskHuman tool for proper human-in-the-loop interactions.

This tool allows the agent to explicitly ask for human input and continue
execution after receiving a response, using LangGraph's interrupt mechanism.
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from modelforge.registry import ModelForgeRegistry


# Cache for response generator to avoid recreating
_response_generator = None

# Configuration for HIL tools
_hil_config: Dict[str, Any] = {
    "provider_name": "github_copilot",
    "model_alias": "gpt-4o"
}


def configure_hil_llm(provider_name: str, model_alias: str) -> None:
    """Configure the LLM settings for HIL response generation.
    
    Args:
        provider_name: The provider to use (e.g., 'github_copilot', 'openai')
        model_alias: The model to use (e.g., 'gpt-4o', 'gpt-4')
    """
    global _response_generator, _hil_config
    _hil_config["provider_name"] = provider_name
    _hil_config["model_alias"] = model_alias
    # Reset the cached generator so it will be recreated with new settings
    _response_generator = None


def get_response_generator():
    """Get or create the response generator LLM instance."""
    global _response_generator
    if _response_generator is None:
        registry = ModelForgeRegistry()
        # Use the configured model settings
        _response_generator = registry.get_llm(
            provider_name=_hil_config["provider_name"],
            model_alias=_hil_config["model_alias"],
            enhanced=False  # Explicitly use classic LLM to avoid future warning
        )
        _response_generator.temperature = 0.3
        _response_generator.max_tokens = 100
    return _response_generator


async def generate_suggested_response(question: str, context: Optional[str] = None) -> str:
    """
    Use LLM to generate an appropriate response for automated testing.
    
    Args:
        question: The question being asked
        context: Optional context about the test
        
    Returns:
        A suggested response appropriate for automated testing
    """
    llm = get_response_generator()
    
    prompt = f"""You are helping with automated browser testing. The test agent is asking for human input.
Generate a brief, appropriate response for this question in an automated test context.

Question: {question}
{"Context: " + context if context else ""}

Guidelines:
- For color preferences: choose common colors like "blue", "red", or "green"
- For search queries: suggest relevant technical terms like "artificial intelligence", "machine learning"
- For names: use generic test names like "John Doe", "Jane Smith", "Test User"
- For yes/no questions: analyze the context and respond appropriately
- For numerical inputs: use reasonable test values (e.g., age: 25, quantity: 5)
- For dates: use current or near-future dates
- For email: use test@example.com format
- Keep responses short and appropriate for testing

Response:"""
    
    try:
        response = await llm.ainvoke(prompt)
        suggested = response.content.strip()
        # Ensure response is not too long
        if len(suggested) > 100:
            suggested = suggested[:100]
        return suggested
    except Exception as e:
        # Fallback to simple default if LLM fails
        print(f"[HIL] Warning: LLM response generation failed: {e}")
        return "Continue with test"


@tool
async def ask_human(question: str, context: Optional[str] = None) -> str:
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
    # Generate suggested response using LLM
    suggested_response = await generate_suggested_response(question, context)
    
    # Prepare interrupt data
    interrupt_data = {
        "type": "human_question",
        "question": question,
        "context": context,
        "tool": "ask_human",
        "suggested_response": suggested_response
    }
    
    # Use interrupt to pause execution
    human_response = interrupt(interrupt_data)
    
    # Return the response (will be the value from Command(resume=...))
    return human_response


async def generate_confirmation_response(action: str, details: Optional[str] = None) -> bool:
    """
    Use LLM to determine if an action should be confirmed in test context.
    
    Args:
        action: The action requiring confirmation
        details: Additional context
        
    Returns:
        True if action should be confirmed, False otherwise
    """
    llm = get_response_generator()
    
    prompt = f"""You are helping with automated browser testing. The test agent is asking for confirmation.
Analyze if this action should be confirmed in an automated test context.

Action: {action}
{"Details: " + details if details else ""}

Consider:
- Is this a normal test action that should proceed?
- Are there any risks or destructive operations?
- For test scenarios, we generally want to confirm actions unless they're clearly dangerous

Respond with only "yes" or "no".

Response:"""
    
    try:
        response = await llm.ainvoke(prompt)
        response_text = response.content.strip().lower()
        return response_text in ["yes", "y", "true", "confirm", "proceed"]
    except Exception as e:
        # Default to yes for test automation
        print(f"[HIL] Warning: LLM confirmation generation failed: {e}")
        return True


@tool
async def confirm_action(action: str, details: Optional[str] = None) -> bool:
    """
    Request human confirmation before performing an action.
    
    Args:
        action: The action that requires confirmation
        details: Additional details about the action
        
    Returns:
        True if confirmed, False otherwise
    """
    # Generate suggested confirmation using LLM
    suggested_confirmation = await generate_confirmation_response(action, details)
    
    interrupt_data = {
        "type": "confirmation_request",
        "action": action,
        "details": details,
        "tool": "confirm_action",
        "suggested_response": "yes" if suggested_confirmation else "no"
    }
    
    response = interrupt(interrupt_data)
    
    # Convert response to boolean
    if isinstance(response, bool):
        return response
    
    response_lower = str(response).lower()
    return response_lower in ["yes", "y", "true", "confirm", "proceed", "continue"]