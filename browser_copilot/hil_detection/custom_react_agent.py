"""
Custom ReAct agent with HIL-aware routing logic.
"""

from typing import Annotated, Sequence, TypedDict, Literal, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .detector import HILDetector


class AgentState(TypedDict):
    """State for the custom ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    hil_detected: bool
    hil_response: Optional[str]


def create_custom_react_agent_with_hil(
    llm: BaseChatModel,
    tools: list,
    hil_detector: Optional[HILDetector] = None,
    verbose: bool = False
) -> Any:
    """
    Create a custom ReAct agent with HIL-aware routing.
    
    This implementation builds a ReAct agent from scratch with custom
    should_continue logic that handles HIL detection and continuation.
    
    Args:
        llm: Language model to use
        tools: List of tools available to the agent
        hil_detector: HIL detector instance
        verbose: Enable verbose logging
        
    Returns:
        Compiled StateGraph with custom routing
    """
    if hil_detector is None:
        hil_detector = HILDetector(verbose=verbose)
    
    # Create the model calling function
    def call_model(state: AgentState) -> AgentState:
        """Call the LLM and potentially detect HIL."""
        if verbose:
            print("\n[Custom Agent] Calling model...")
            
        # If we have a pending HIL response, inject it first
        messages = list(state["messages"])
        if state.get("hil_response"):
            if verbose:
                print(f"[Custom Agent] Injecting HIL response: {state['hil_response']}")
            
            human_msg = HumanMessage(
                content=state["hil_response"],
                metadata={
                    "source": "hil_detector",
                    "type": "autonomous_continuation"
                }
            )
            messages.append(human_msg)
        
        # Call the model
        response = llm.invoke(messages)
        
        # Check for HIL if no tool calls
        hil_detected = False
        hil_response = None
        
        if not (hasattr(response, 'tool_calls') and response.tool_calls):
            # Detect HIL
            detection_result = hil_detector.detect(
                message=response.content,
                test_context=_extract_test_context(messages),
                recent_messages=messages[-5:]
            )
            
            if detection_result["is_hil"] and detection_result["confidence"] >= 0.7:
                if verbose:
                    print(f"\n[Custom Agent] HIL detected: {detection_result['hil_type']}")
                    print(f"[Custom Agent] Suggested response: {detection_result['suggested_response']}")
                
                hil_detected = True
                hil_response = detection_result["suggested_response"]
        
        # Return updated state
        return {
            "messages": [response],
            "hil_detected": hil_detected,
            "hil_response": hil_response
        }
    
    # Custom should_continue function with HIL awareness
    def should_continue_with_hil(state: AgentState) -> Literal["tools", "agent", "end"]:
        """
        Custom routing logic that handles HIL detection.
        
        This is the key difference from the prebuilt agent - we can
        route back to the agent when HIL is detected.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        if verbose:
            print(f"\n[Custom Agent] Routing decision...")
            print(f"[Custom Agent] HIL detected: {state.get('hil_detected', False)}")
            print(f"[Custom Agent] Has tool calls: {hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)}")
        
        # If HIL was detected and we have a response, continue to agent
        if state.get("hil_detected") and state.get("hil_response"):
            if verbose:
                print("[Custom Agent] Routing to agent for HIL handling")
            return "agent"
        
        # If there are tool calls, execute them
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            if verbose:
                print("[Custom Agent] Routing to tools")
            return "tools"
        
        # Otherwise, we're done
        if verbose:
            print("[Custom Agent] Routing to end")
        return "end"
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges with custom routing
    workflow.add_conditional_edges(
        "agent",
        should_continue_with_hil,
        {
            "tools": "tools",
            "agent": "agent",  # This allows looping back for HIL
            "end": END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
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