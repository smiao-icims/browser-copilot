"""
Experimental: Wrap prebuilt agent to handle HIL continuation.
"""

from typing import Any, Dict, AsyncIterator
from langchain_core.messages import HumanMessage


async def wrapped_agent_with_hil_retry(
    agent: Any,
    initial_input: Dict[str, Any],
    hil_detector: Any,
    max_retries: int = 3,
    verbose: bool = False
) -> AsyncIterator[Any]:
    """
    Experimental wrapper that retries agent execution after HIL detection.
    
    This is a workaround for the limitation that create_react_agent
    cannot continue after post_model_hook injects a message.
    
    Args:
        agent: The compiled agent from create_react_agent
        initial_input: Initial input with messages
        hil_detector: HIL detector instance
        max_retries: Maximum HIL retry attempts
        verbose: Enable verbose logging
        
    Yields:
        Agent execution chunks
    """
    current_input = initial_input
    retry_count = 0
    
    while retry_count < max_retries:
        hil_detected = False
        last_chunk = None
        
        # Stream the agent execution
        async for chunk in agent.astream(current_input):
            yield chunk
            last_chunk = chunk
            
            # Check if HIL was detected in post_model_hook
            if "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "metadata") and msg.metadata.get("hil_detected"):
                        hil_detected = True
                        if verbose:
                            print(f"\n[Wrapped Agent] HIL detected, will retry")
        
        # If no HIL detected, we're done
        if not hil_detected:
            break
            
        # If HIL was detected, prepare for retry
        retry_count += 1
        if verbose:
            print(f"\n[Wrapped Agent] Retrying after HIL (attempt {retry_count}/{max_retries})")
        
        # The messages should already include the HIL response from post_model_hook
        # Just continue with the updated state
        if last_chunk and "agent" in last_chunk:
            current_input = {"messages": last_chunk["agent"]["messages"]}
        else:
            # Shouldn't happen, but break if we can't get state
            break
    
    if retry_count >= max_retries and verbose:
        print(f"\n[Wrapped Agent] Max HIL retries reached")