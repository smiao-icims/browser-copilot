"""
HIL handling using pre_model_hook to preemptively inject responses.
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from .detector import HILDetector


def create_hil_pre_model_hook(
    hil_detector: Optional[HILDetector] = None,
    verbose: bool = False
) -> callable:
    """
    Create a pre_model_hook that detects potential HIL situations and
    preemptively injects responses to prevent the agent from asking.
    
    This approach:
    1. Analyzes the conversation history
    2. Detects if the agent is likely to ask for human input
    3. Preemptively adds a human response to guide the agent
    
    Args:
        hil_detector: HIL detector instance
        verbose: Enable verbose logging
        
    Returns:
        A pre_model_hook function compatible with LangGraph v2
    """
    if hil_detector is None:
        hil_detector = HILDetector(verbose=verbose)
    
    # Track HIL state across calls
    hil_state = {"last_injection": None, "injection_count": 0}
    
    def hil_pre_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-model hook that preemptively handles HIL.
        """
        if verbose:
            print(f"\n[HIL Pre-Hook] Called with state keys: {list(state.keys())}")
        
        messages = state.get("messages", [])
        if not messages:
            return {"llm_input_messages": messages}
        
        # Check if we just injected a response in the previous call
        if hil_state["last_injection"]:
            # Clear the injection state
            hil_state["last_injection"] = None
            if verbose:
                print("[HIL Pre-Hook] Previous HIL injection detected, allowing agent to process")
            return {"llm_input_messages": messages}
        
        # Analyze conversation for potential HIL situations
        test_context = _extract_test_context(messages)
        
        # Look for patterns that suggest the agent might ask for input
        if _might_trigger_hil(messages, test_context):
            if verbose:
                print("[HIL Pre-Hook] Potential HIL situation detected")
            
            # Determine what kind of input might be needed
            suggested_input = _suggest_preemptive_input(messages, test_context)
            
            if suggested_input:
                if verbose:
                    print(f"[HIL Pre-Hook] Preemptively injecting: {suggested_input}")
                
                # Create a human message with the suggested input
                preemptive_msg = HumanMessage(
                    content=suggested_input,
                    metadata={
                        "source": "hil_pre_hook",
                        "type": "preemptive_injection",
                        "injection_count": hil_state["injection_count"]
                    }
                )
                
                # Track the injection
                hil_state["last_injection"] = suggested_input
                hil_state["injection_count"] += 1
                
                # Use llm_input_messages to provide input without updating state
                return {"llm_input_messages": messages + [preemptive_msg]}
        
        # Check if the last AI message was asking for input
        if messages and isinstance(messages[-1], AIMessage):
            last_ai_msg = messages[-1]
            
            # Skip if it has tool calls
            if not (hasattr(last_ai_msg, 'tool_calls') and last_ai_msg.tool_calls):
                # Detect if it's asking for input
                detection_result = hil_detector.detect(
                    message=last_ai_msg.content,
                    test_context=test_context,
                    recent_messages=messages[-5:]
                )
                
                if detection_result["is_hil"] and detection_result["confidence"] >= 0.7:
                    if verbose:
                        print(f"\n[HIL Pre-Hook] Detected HIL in last message: {detection_result['hil_type']}")
                        print(f"[HIL Pre-Hook] Injecting response: {detection_result['suggested_response']}")
                    
                    # Inject the response
                    response_msg = HumanMessage(
                        content=detection_result["suggested_response"],
                        metadata={
                            "source": "hil_detector",
                            "type": "reactive_injection",
                            "hil_type": detection_result["hil_type"],
                            "confidence": detection_result["confidence"]
                        }
                    )
                    
                    # Track the injection
                    hil_state["last_injection"] = detection_result["suggested_response"]
                    hil_state["injection_count"] += 1
                    
                    # Use llm_input_messages to provide input without updating state
                    return {"llm_input_messages": messages + [response_msg]}
        
        # No HIL handling needed - return messages as llm_input_messages
        return {"llm_input_messages": messages}
    
    return hil_pre_hook


def _extract_test_context(messages: List[BaseMessage]) -> str:
    """Extract test context from messages."""
    context_parts = []
    
    for msg in messages[:3]:
        if isinstance(msg, HumanMessage):
            # Look for test instructions
            content_lower = msg.content.lower()
            if any(word in content_lower for word in ["test", "step", "verify"]):
                context_parts.append(msg.content[:500])
    
    return " ".join(context_parts)


def _might_trigger_hil(messages: List[BaseMessage], test_context: str) -> bool:
    """
    Predict if the agent might ask for human input based on context.
    
    This looks for patterns like:
    - Test steps that mention "ask the user"
    - Recent navigation or screenshot actions that might precede a question
    - Patterns in the conversation that suggest upcoming HIL
    """
    test_lower = test_context.lower()
    
    # Check if test explicitly mentions asking for input
    hil_indicators = [
        "ask the user",
        "ask for user input",
        "get user input",
        "request input",
        "ask what",
        "ask for"
    ]
    
    if any(indicator in test_lower for indicator in hil_indicators):
        # Check if we recently did navigation or screenshots
        recent_tools = []
        for msg in messages[-3:]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    recent_tools.append(tool_call.get("name", ""))
        
        # If we just navigated or took screenshots, HIL might be coming
        if any(tool in recent_tools for tool in ["browser_navigate", "browser_snapshot", "browser_take_screenshot"]):
            return True
    
    return False


def _suggest_preemptive_input(messages: List[BaseMessage], test_context: str) -> Optional[str]:
    """
    Suggest input to preemptively provide based on context.
    """
    test_lower = test_context.lower()
    
    # Map common HIL scenarios to responses
    if "search" in test_lower and "what" in test_lower:
        return "Please search for: AI Advertisement"
    
    if "favorite color" in test_lower:
        return "blue"
    
    if "name" in test_lower and "enter" in test_lower:
        return "John Doe"
    
    if "email" in test_lower:
        return "test@example.com"
    
    # Check for specific test steps
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content_lower = msg.content.lower()
            
            # Look for numbered steps mentioning asking
            import re
            step_pattern = r'\d+\.\s*ask\s+(?:the\s+)?(?:user\s+)?(.+?)(?:\n|$)'
            matches = re.findall(step_pattern, content_lower)
            
            if matches:
                # Extract what to ask for
                ask_for = matches[0].strip()
                if "search" in ask_for:
                    return "Search for: artificial intelligence trends 2025"
                elif "name" in ask_for:
                    return "John Doe"
                elif "preference" in ask_for:
                    return "Option 1"
    
    return None