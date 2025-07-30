"""
Post-model hooks for Human-in-the-Loop detection using LangGraph's hook system.
"""

import json
from typing import Any, Callable, Dict, Optional

from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, BaseMessage
)
from langchain_core.language_models import BaseChatModel

from .detector import HILDetector
from .patterns import FALLBACK_HIL_PATTERNS


def create_hil_post_hook(
    detector_model: Optional[BaseChatModel] = None,
    verbose: bool = False,
    fallback_to_patterns: bool = True,
    confidence_threshold: float = 0.7
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a post-model hook that uses an LLM to detect and handle HIL responses.
    
    This hook is designed to work with LangGraph's create_react_agent function.
    The detector LLM acts as a "human supervisor" that can:
    1. Detect if the agent is asking for human input
    2. Decide how to respond appropriately  
    3. Inject continuation instructions back into the flow
    
    Args:
        detector_model: LLM to use for HIL detection (can be smaller/cheaper model)
        verbose: Whether to print detection details
        fallback_to_patterns: Whether to use regex patterns if LLM detection fails
        confidence_threshold: Minimum confidence score to trigger HIL handling
        
    Returns:
        A post-model hook function compatible with LangGraph
    """
    
    # Create detector instance
    detector = HILDetector(
        detector_model=detector_model,
        fallback_to_patterns=fallback_to_patterns,
        verbose=verbose
    )
    
    def hil_post_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-model hook that detects and handles HIL responses.
        
        Args:
            state: Current graph state containing messages
            
        Returns:
            State update with continuation message if HIL detected, empty dict otherwise
        """
        if verbose:
            print(f"\n[HIL Hook] Post-model hook called with state keys: {list(state.keys())}")
        
        # Get messages from state
        messages = state.get("messages", [])
        if not messages:
            if verbose:
                print("[HIL Hook] No messages in state")
            return {}
            
        # Get last message
        last_message = messages[-1]
        
        # Only check AI messages
        if not isinstance(last_message, AIMessage):
            if verbose:
                print(f"[HIL Hook] Last message is not AIMessage, it's {type(last_message).__name__}")
            return {}
            
        if verbose:
            print(f"[HIL Hook] Checking AIMessage: {last_message.content[:100]}...")
            
        # Skip if message has tool calls (agent is taking action)
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            if verbose:
                print("[HIL Hook] Message has tool calls, skipping")
            return {}
        
        # Extract test context from conversation
        test_context = _extract_test_context(messages)
        
        # Detect HIL with full context
        detection_result = detector.detect(
            message=last_message.content,
            test_context=test_context,
            recent_messages=messages[-5:]  # Last 5 messages for context
        )
        
        # Check if we should handle this as HIL
        if detection_result["is_hil"] and detection_result["confidence"] >= confidence_threshold:
            if verbose:
                print(f"\n[HIL Detector] Detected {detection_result['hil_type']} request")
                print(f"[HIL Detector] Confidence: {detection_result['confidence']:.2f}")
                print(f"[HIL Detector] Reasoning: {detection_result.get('reasoning', 'N/A')}")
                print(f"[HIL Detector] Suggested response: {detection_result['suggested_response']}")
            
            # Create continuation message
            continuation_message = HumanMessage(
                content=detection_result["suggested_response"],
                metadata={
                    "source": "hil_detector",
                    "type": "autonomous_continuation",
                    "hil_type": detection_result["hil_type"],
                    "confidence": detection_result["confidence"],
                    "original_request": last_message.content
                }
            )
            
            # Return state update with continuation message
            if verbose:
                print(f"[HIL Hook] Injecting human message: {continuation_message.content}")
                print(f"[HIL Hook] Current state keys: {list(state.keys())}")
                print(f"[HIL Hook] Current message count: {len(messages)}")
                
            # Check if we have access to agent state
            if "agent" in state:
                if verbose:
                    print(f"[HIL Hook] Agent state available: {list(state['agent'].keys())}")
            
            # Try to find if there's a way to signal continuation
            # The post_model_hook might need to return more than just messages
            state_update = {"messages": [continuation_message]}
            
            # Check for other state variables that might control flow
            if "should_continue" in state:
                state_update["should_continue"] = True
                if verbose:
                    print("[HIL Hook] Setting should_continue to True")
                    
            return state_update
        
        # No HIL detected, return empty update
        return {}
    
    return hil_post_hook


def _extract_test_context(messages: list[BaseMessage]) -> str:
    """
    Extract test context from message history.
    
    Looks for:
    - Initial human message with test instructions
    - System messages with test context
    - Recent test step completions
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Extracted test context as a string
    """
    context_parts = []
    
    # Find initial test instructions (usually first human message)
    for msg in messages[:3]:  # Check first few messages
        if isinstance(msg, HumanMessage):
            context_parts.append(f"Test Instructions: {msg.content}")
            break
    
    # Find system context
    for msg in messages[:3]:
        if isinstance(msg, SystemMessage):
            context_parts.append(f"System Context: {msg.content[:200]}...")
            break
    
    # Find recent test progress
    completed_steps = []
    for msg in reversed(messages[-10:]):  # Last 10 messages
        if isinstance(msg, AIMessage) and "step" in msg.content.lower():
            # Extract step completions
            if "completed" in msg.content.lower() or "✓" in msg.content:
                completed_steps.append(msg.content.split('\n')[0])
    
    if completed_steps:
        context_parts.append(f"Recent Progress: {'; '.join(completed_steps[-3:])}")
    
    return "\n".join(context_parts) if context_parts else "No specific test context found"


def create_simple_hil_hook(
    verbose: bool = False,
    auto_continue: bool = True
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a simple pattern-based HIL detection hook (no LLM required).
    
    This is a lightweight alternative that uses regex patterns for detection.
    Useful for testing or when LLM-based detection is not needed.
    
    Args:
        verbose: Whether to print detection details
        auto_continue: Whether to auto-generate continuation responses
        
    Returns:
        A post-model hook function
    """
    
    def simple_hil_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """Simple pattern-based HIL detection."""
        messages = state.get("messages", [])
        if not messages or not isinstance(messages[-1], AIMessage):
            return {}
            
        last_message = messages[-1]
        content = last_message.content.lower()
        
        # Check patterns
        for pattern in FALLBACK_HIL_PATTERNS:
            if pattern in content:
                if verbose:
                    print(f"\n[Simple HIL] Detected pattern: '{pattern}'")
                
                if auto_continue:
                    # Generate simple continuation
                    continuation = HumanMessage(
                        content="Yes, please continue with the next step.",
                        metadata={
                            "source": "simple_hil_detector",
                            "pattern_matched": pattern
                        }
                    )
                    return {"messages": [continuation]}
        
        return {}
    
    return simple_hil_hook