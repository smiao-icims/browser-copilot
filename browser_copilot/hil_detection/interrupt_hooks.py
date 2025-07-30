"""
Post-model hooks using LangGraph's interrupt() for proper HIL handling.

This implementation uses interrupt() with checkpointing to properly pause
and resume agent execution when human input is needed.
"""

from typing import Any, Dict, Optional
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from langgraph.types import interrupt

from .detector import HILDetector


def create_hil_post_hook_with_interrupt(
    detector_model: Optional[BaseChatModel] = None,
    verbose: bool = False,
    fallback_to_patterns: bool = True,
    confidence_threshold: float = 0.7
) -> callable:
    """
    Create a post-model hook that uses interrupt() for proper HIL handling.
    
    This implementation:
    1. Detects when the agent asks for human input
    2. Uses interrupt() to pause execution and checkpoint state
    3. Waits for Command(resume=...) to continue with human input
    
    Args:
        detector_model: LLM to use for HIL detection
        verbose: Enable verbose logging
        fallback_to_patterns: Use pattern matching if LLM fails
        confidence_threshold: Minimum confidence for HIL detection
        
    Returns:
        Post-model hook function for LangGraph v2
    """
    # Create detector instance
    detector = HILDetector(
        detector_model=detector_model,
        fallback_to_patterns=fallback_to_patterns,
        verbose=verbose
    )
    
    def hil_post_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-model hook that interrupts execution for HIL.
        """
        if verbose:
            print(f"\n[HIL Interrupt Hook] Called with state keys: {list(state.keys())}")
        
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        last_message = messages[-1]
        
        # Only check AI messages without tool calls
        if not isinstance(last_message, AIMessage):
            return {}
            
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            if verbose:
                print("[HIL Interrupt Hook] Message has tool calls, skipping")
            return {}
        
        # Extract test context
        test_context = _extract_test_context(messages)
        
        # Detect HIL
        detection_result = detector.detect(
            message=last_message.content,
            test_context=test_context,
            recent_messages=messages[-5:]
        )
        
        if detection_result["is_hil"] and detection_result["confidence"] >= confidence_threshold:
            if verbose:
                print(f"\n[HIL Interrupt Hook] Detected {detection_result['hil_type']} request")
                print(f"[HIL Interrupt Hook] Confidence: {detection_result['confidence']:.2f}")
                print(f"[HIL Interrupt Hook] Agent asked: {last_message.content}")
                print(f"[HIL Interrupt Hook] Suggested response: {detection_result['suggested_response']}")
                print("[HIL Interrupt Hook] Interrupting execution for human input...")
            
            # Use interrupt to pause execution
            # The interrupt data includes all context for handling
            human_response = interrupt({
                "type": "hil_request",
                "hil_type": detection_result["hil_type"],
                "agent_request": last_message.content,
                "suggested_response": detection_result["suggested_response"],
                "confidence": detection_result["confidence"],
                "reasoning": detection_result.get("reasoning", ""),
                "test_context": test_context[:500]  # Include some context
            })
            
            if verbose:
                print(f"[HIL Interrupt Hook] Received human response: {human_response}")
            
            # Create continuation message with the human response
            continuation_message = HumanMessage(
                content=human_response,
                metadata={
                    "source": "hil_interrupt",
                    "type": "human_response",
                    "hil_type": detection_result["hil_type"],
                    "original_request": last_message.content
                }
            )
            
            # Return the message to be added to state
            return {"messages": [continuation_message]}
        
        return {}
    
    return hil_post_hook


def _extract_test_context(messages: list) -> str:
    """Extract test context from messages."""
    context_parts = []
    
    for msg in messages[:3]:
        if isinstance(msg, HumanMessage):
            content_lower = msg.content.lower()
            if any(word in content_lower for word in ["test", "step", "verify"]):
                context_parts.append(msg.content[:500])
    
    return " ".join(context_parts)