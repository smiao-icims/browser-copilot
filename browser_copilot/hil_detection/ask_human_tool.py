"""
AskHuman tool for proper human-in-the-loop interactions.

This tool allows the agent to explicitly ask for human input and continue
execution after receiving a response, using LangGraph's interrupt mechanism.
"""

from typing import Any

from langchain_core.tools import tool
from langgraph.types import interrupt
from modelforge.registry import ModelForgeRegistry

# Cache for response generator to avoid recreating
_response_generator = None

# Configuration for HIL tools
_hil_config: dict[str, Any] = {
    "provider_name": "github_copilot",
    "model_alias": "gpt-4o",
}


def configure_hil_llm(provider_name: str, model_alias: str) -> None:
    """Configure the LLM settings for HIL response generation.

    Args:
        provider_name: The provider to use (e.g., 'github_copilot', 'openai')
        model_alias: The model to use (e.g., 'gpt-4o', 'gpt-4')
    """
    global _response_generator, _hil_config
    print(
        f"[HIL] configure_hil_llm called with provider={provider_name}, model={model_alias}"
    )
    _hil_config["provider_name"] = provider_name
    _hil_config["model_alias"] = model_alias
    # Reset the cached generator so it will be recreated with new settings
    _response_generator = None


def get_response_generator():
    """Get or create the response generator LLM instance."""
    global _response_generator
    if _response_generator is None:
        print(f"[HIL] Creating response generator with config: {_hil_config}")
        registry = ModelForgeRegistry()
        # Use the configured model settings
        _response_generator = registry.get_llm(
            provider_name=_hil_config["provider_name"],
            model_alias=_hil_config["model_alias"],
            enhanced=False,  # Explicitly use classic LLM to avoid future warning
        )
        _response_generator.temperature = 0.3
        _response_generator.max_tokens = 100
        print("[HIL] Response generator created successfully")
    return _response_generator


async def generate_suggested_response(question: str, context: str | None = None) -> str:
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

Here are examples of appropriate responses for test automation:

Example 1:
Question: "What is your favorite color?"
Response: "blue"

Example 2:
Question: "Should I retry the login process or proceed with a different test scenario?"
Context: Login failed with incorrect credentials error
Response: "retry"

Example 3:
Question: "The checkout process failed. Should I start over from the shopping cart or skip to the next test?"
Context: Payment gateway timeout after adding items to cart successfully
Response: "start over from shopping cart"

Example 4:
Question: "What search term should I use?"
Response: "artificial intelligence"

Example 5:
Question: "Enter your name for the registration form"
Response: "John Doe"

Example 6:
Question: "The page is loading slowly. Should I wait longer or continue with a timeout?"
Context: Page has been loading for 15 seconds
Response: "continue with timeout"

Example 7:
Question: "The login attempt seems to have failed. Should I try again or investigate further?"
Context: Login failed with an error message
Response: "try again"

Example 8:
Question: "Should I proceed with debugging or attempt another approach?"
Context: Form submission failed
Response: "attempt another approach"

Guidelines for your response:
- When asked "Should I try again or investigate further?" - ALWAYS choose "try again" or "retry" for login/form errors
- For retry/continue decisions: favor retry if the error is transient (timeout, network, form submission)
- For test flow decisions: prefer continuing from the last successful step rather than starting completely over
- Keep responses concise and action-oriented (e.g., "retry", "continue", "skip")
- Avoid responses like "investigate further" or "debug" - tests should take action, not investigate
- Default to retrying failed actions in automated tests
- Return ONLY the direct answer, not the question or any formatting

Response:"""

    try:
        print(f"[HIL] Invoking LLM with prompt length: {len(prompt)}")
        response = await llm.ainvoke(prompt)
        suggested = response.content.strip()
        print(f"[HIL] LLM raw response: {suggested}")
        # Ensure response is not too long
        if len(suggested) > 100:
            suggested = suggested[:100]
        return suggested
    except Exception as e:
        # Fallback to simple default if LLM fails
        print(f"[HIL] Warning: LLM response generation failed: {e}")
        import traceback

        traceback.print_exc()
        return "Continue with test"


@tool
async def ask_human(question: str, context: str | None = None) -> str:
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
    # Debug logging
    print("[HIL] ask_human tool called with:")
    print(f"[HIL]   Question: {question}")
    print(f"[HIL]   Context: {context}")

    # Generate suggested response using LLM
    suggested_response = await generate_suggested_response(question, context)

    print(f"[HIL]   Generated suggestion: {suggested_response}")

    # Prepare interrupt data
    interrupt_data = {
        "type": "human_question",
        "question": question,
        "context": context,
        "tool": "ask_human",
        "suggested_response": suggested_response,
    }

    # Use interrupt to pause execution
    human_response = interrupt(interrupt_data)

    # Return the response (will be the value from Command(resume=...))
    return human_response


async def generate_confirmation_response(
    action: str, details: str | None = None
) -> bool:
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

Here are examples of confirmation decisions for test automation:

Example 1:
Action: "Delete all items in shopping cart"
Details: "This will clear 3 items from the test cart"
Response: "yes" (normal test operation)

Example 2:
Action: "Submit order with total $5000"
Details: "Using test credit card ending in 4242"
Response: "yes" (test payment method)

Example 3:
Action: "Delete user account"
Details: "This will permanently remove the test account 'testuser123'"
Response: "yes" (test account deletion is expected)

Example 4:
Action: "Proceed with checkout despite validation errors?"
Details: "Missing required shipping address fields"
Response: "no" (cannot proceed without required data)

Example 5:
Action: "Continue test after login failure?"
Details: "Authentication failed 3 times"
Response: "yes" (continue to test error handling)

Guidelines:
- Confirm actions that are part of normal test flow
- Confirm actions using test data (test accounts, test payments)
- Reject only if the action would break the test or skip important validations
- When in doubt, confirm to keep the test moving

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
async def confirm_action(action: str, details: str | None = None) -> bool:
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
        "suggested_response": "yes" if suggested_confirmation else "no",
    }

    response = interrupt(interrupt_data)

    # Convert response to boolean
    if isinstance(response, bool):
        return response

    response_lower = str(response).lower()
    return response_lower in ["yes", "y", "true", "confirm", "proceed", "continue"]
