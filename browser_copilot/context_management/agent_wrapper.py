"""
Agent wrapper for context management integration

This module provides a wrapper around LangGraph ReAct agents
to integrate sliding window context management.
"""

import asyncio
from datetime import datetime, UTC
from typing import Any, AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from .base import Message, MessageType, ContextConfig
from .manager import BrowserCopilotContextManager


class ContextManagedAgent:
    """Wrapper for ReAct agent with context management"""
    
    def __init__(
        self,
        agent: Any,
        context_manager: Optional[BrowserCopilotContextManager] = None,
        config: Optional[ContextConfig] = None
    ):
        """
        Initialize the context-managed agent
        
        Args:
            agent: The underlying ReAct agent
            context_manager: Optional context manager instance
            config: Optional context configuration
        """
        self.agent = agent
        self.context_manager = context_manager or BrowserCopilotContextManager(
            config=config,
            strategy="sliding-window"
        )
        self._message_buffer: list[Message] = []
    
    async def astream(
        self, 
        input_dict: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream agent responses with context management
        
        Args:
            input_dict: Input dictionary with messages
            
        Yields:
            Agent response chunks
        """
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract initial messages
        initial_messages = input_dict.get("messages", [])
        logger.info(f"Context wrapper received input type: {type(initial_messages)}")
        
        # Convert initial messages to our Message format
        if isinstance(initial_messages, str):
            # Single prompt string
            self._add_message(MessageType.USER, initial_messages)
        elif isinstance(initial_messages, list):
            # List of messages
            for msg in initial_messages:
                if isinstance(msg, str):
                    self._add_message(MessageType.USER, msg)
                elif isinstance(msg, dict):
                    self._add_message_from_dict(msg)
                elif hasattr(msg, 'content'):
                    # LangChain message objects
                    self._add_message_from_langchain(msg)
        
        # Process through context manager
        processed_messages = self.context_manager.get_context()
        
        # Convert back to format expected by agent
        agent_messages = self._convert_to_agent_format(processed_messages)
        
        # Update input with processed messages
        processed_input = input_dict.copy()
        processed_input["messages"] = agent_messages
        
        # Stream from agent and capture responses
        async for chunk in self.agent.astream(processed_input):
            # Capture agent messages for context
            self._capture_chunk_messages(chunk)
            
            # Yield the chunk unchanged
            yield chunk
    
    def _add_message(
        self, 
        msg_type: MessageType, 
        content: str,
        tool_name: Optional[str] = None
    ) -> None:
        """Add a message to the context manager"""
        message = Message(
            type=msg_type,
            content=content,
            timestamp=datetime.now(UTC),
            tool_name=tool_name
        )
        self.context_manager.add_message(message)
    
    def _add_message_from_dict(self, msg_dict: dict) -> None:
        """Convert dictionary message to our format"""
        msg_type = MessageType.USER  # Default
        content = msg_dict.get("content", "")
        
        if "role" in msg_dict:
            role = msg_dict["role"]
            if role == "system":
                msg_type = MessageType.SYSTEM
            elif role == "assistant":
                msg_type = MessageType.ASSISTANT
            elif role == "user":
                msg_type = MessageType.USER
        
        self._add_message(msg_type, content)
    
    def _add_message_from_langchain(self, msg: Any) -> None:
        """Convert LangChain message to our format"""
        content = str(msg.content) if hasattr(msg, 'content') else str(msg)
        
        if isinstance(msg, SystemMessage):
            msg_type = MessageType.SYSTEM
        elif isinstance(msg, AIMessage):
            msg_type = MessageType.ASSISTANT
        elif isinstance(msg, ToolMessage):
            msg_type = MessageType.TOOL_RESPONSE
            tool_name = getattr(msg, 'name', None)
            self._add_message(msg_type, content, tool_name)
            return
        else:
            msg_type = MessageType.USER
        
        self._add_message(msg_type, content)
    
    def _convert_to_agent_format(self, messages: list[Message]) -> list[Any]:
        """Convert our messages back to agent format"""
        # For now, return as strings. 
        # In a full implementation, we'd convert back to LangChain message types
        return [msg.content for msg in messages]
    
    def _capture_chunk_messages(self, chunk: dict[str, Any]) -> None:
        """Capture messages from agent chunks for context"""
        # Extract tool calls
        if "tools" in chunk:
            for tool_msg in chunk.get("tools", {}).get("messages", []):
                if hasattr(tool_msg, "name") and hasattr(tool_msg, "content"):
                    self._add_message(
                        MessageType.TOOL_CALL,
                        str(tool_msg.content),
                        tool_name=tool_msg.name
                    )
        
        # Extract agent messages
        if "agent" in chunk:
            for agent_msg in chunk.get("agent", {}).get("messages", []):
                if hasattr(agent_msg, "content") and agent_msg.content:
                    content = str(agent_msg.content)
                    # Only add substantial messages
                    if len(content) > 50:
                        self._add_message(MessageType.ASSISTANT, content)
    
    def get_context_summary(self) -> str:
        """Get a summary of the current context state"""
        return self.context_manager.get_summary()
    
    def get_metrics(self) -> dict[str, Any]:
        """Get context management metrics"""
        return self.context_manager.get_metrics()


def create_context_managed_agent(
    agent: Any,
    strategy: str = "sliding-window",
    config: Optional[ContextConfig] = None,
    model: str = "gpt-4"
) -> ContextManagedAgent:
    """
    Create a context-managed agent
    
    Args:
        agent: The underlying ReAct agent
        strategy: Context management strategy
        config: Optional context configuration
        model: Model name for token counting
        
    Returns:
        Context-managed agent wrapper
    """
    manager = BrowserCopilotContextManager(
        config=config,
        strategy=strategy,
        model=model
    )
    
    return ContextManagedAgent(agent, manager)