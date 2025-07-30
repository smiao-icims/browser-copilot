"""
HIL-aware agent using StateGraph for proper continuation after HIL detection.
"""

from typing import TypedDict, List, Literal, Optional, Any, Dict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from .detector import HILDetector


class HILAgentState(TypedDict):
    """State for HIL-aware agent."""
    messages: List[BaseMessage]
    hil_handled: bool
    hil_response: Optional[str]


def create_hil_aware_agent(
    llm: BaseChatModel,
    tools: list,
    hil_detector: Optional[HILDetector] = None,
    verbose: bool = False
) -> Any:
    """
    Create a HIL-aware agent that can properly continue after HIL detection.
    
    This uses a StateGraph to wrap the ReAct agent and handle HIL situations
    by routing back to the agent when human input is provided.
    
    Args:
        llm: Language model to use
        tools: List of tools available to the agent
        hil_detector: HIL detector instance (creates default if None)
        verbose: Enable verbose logging
        
    Returns:
        Compiled StateGraph that handles HIL
    """
    if hil_detector is None:
        hil_detector = HILDetector(verbose=verbose)
    
    def hil_post_hook(state: HILAgentState) -> HILAgentState:
        """
        Post-model hook that detects HIL and updates state accordingly.
        """
        if verbose:
            print(f"\n[HIL Graph Hook] Post-model hook called")
            print(f"[HIL Graph Hook] HIL already handled: {state.get('hil_handled', False)}")
        
        # Skip if we've already handled HIL in this iteration
        if state.get("hil_handled", False):
            return {"hil_handled": False}  # Reset for next iteration
            
        messages = state.get("messages", [])
        if not messages:
            return {}
            
        last_message = messages[-1]
        
        # Only check AI messages without tool calls
        if not isinstance(last_message, AIMessage):
            return {}
            
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return {}
            
        # Extract test context
        test_context = _extract_test_context(messages)
        
        # Detect HIL
        detection_result = hil_detector.detect(
            message=last_message.content,
            test_context=test_context,
            recent_messages=messages[-5:]
        )
        
        if detection_result["is_hil"] and detection_result["confidence"] >= 0.7:
            if verbose:
                print(f"\n[HIL Graph Hook] Detected {detection_result['hil_type']} request")
                print(f"[HIL Graph Hook] Suggested response: {detection_result['suggested_response']}")
            
            # Instead of injecting a message directly, store the response in state
            return {
                "hil_handled": True,
                "hil_response": detection_result["suggested_response"]
            }
        
        return {}
    
    # Create the base ReAct agent with our post_model_hook
    base_agent = create_react_agent(
        llm,
        tools,
        post_model_hook=hil_post_hook
    )
    
    # Create the StateGraph
    workflow = StateGraph(HILAgentState)
    
    # Define the agent node wrapper
    async def agent_node(state: HILAgentState) -> HILAgentState:
        """
        Wrapper for the base agent that handles HIL responses.
        """
        # If we have a HIL response, inject it as a human message
        if state.get("hil_response"):
            if verbose:
                print(f"\n[HIL Graph] Injecting HIL response: {state['hil_response']}")
            
            human_msg = HumanMessage(
                content=state["hil_response"],
                metadata={
                    "source": "hil_detector",
                    "type": "autonomous_continuation"
                }
            )
            
            # Add the human message to the conversation
            state["messages"].append(human_msg)
            # Clear the HIL response
            state["hil_response"] = None
        
        # Run the base agent asynchronously
        result = await base_agent.ainvoke(state)
        
        # Merge the results back into state
        return {**state, **result}
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    
    # Define routing logic
    def should_continue(state: HILAgentState) -> Literal["agent", "end"]:
        """
        Determine whether to continue or end based on HIL state.
        """
        # If HIL was handled and we have a response, continue to process it
        if state.get("hil_handled") and state.get("hil_response"):
            if verbose:
                print("[HIL Graph] HIL detected, routing back to agent")
            return "agent"
        
        # Check if the last message has tool calls
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    if verbose:
                        print("[HIL Graph] Agent has tool calls, continuing")
                    return "agent"
        
        if verbose:
            print("[HIL Graph] No HIL and no tool calls, ending")
        return "end"
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "agent": "agent",
            "end": END
        }
    )
    
    # Compile and return
    return workflow.compile()


def _extract_test_context(messages: List[BaseMessage]) -> str:
    """Extract test context from messages."""
    context_parts = []
    
    for msg in messages[:3]:
        if isinstance(msg, HumanMessage) and any(
            word in msg.content.lower() 
            for word in ["test", "steps", "verify"]
        ):
            context_parts.append(msg.content[:500])
            
    return " ".join(context_parts)