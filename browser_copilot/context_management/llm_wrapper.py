"""
LLM wrapper for context management

This wraps the LLM itself to apply context management
to all calls, regardless of the agent implementation.
"""

from typing import Any, List, Optional
from datetime import datetime, UTC

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatResult

from .base import Message, MessageType, ContextConfig
from .manager import BrowserCopilotContextManager


class ContextManagedLLM(BaseChatModel):
    """LLM wrapper that applies context management to all calls"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        context_manager: Optional[BrowserCopilotContextManager] = None,
        config: Optional[ContextConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize the context-managed LLM
        
        Args:
            llm: The underlying LLM
            context_manager: Optional context manager instance
            config: Optional context configuration
            verbose: Enable verbose logging
        """
        super().__init__()
        self.llm = llm
        self.context_manager = context_manager or BrowserCopilotContextManager(
            config=config,
            strategy="sliding-window"
        )
        self.verbose = verbose
        self._call_count = 0
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        """Generate a response with context management"""
        self._call_count += 1
        
        # Convert LangChain messages to our format
        for msg in messages:
            self._add_langchain_message(msg)
        
        # Get processed context
        processed_messages = self.context_manager.get_context()
        
        if self.verbose:
            print(f"\n[Context Management - Call {self._call_count}]")
            print(f"Original messages: {len(messages)}")
            print(f"Processed messages: {len(processed_messages)}")
            print(f"Reduction: {self.context_manager.get_metrics()['token_metrics']['reduction_percentage']:.1f}%")
        
        # Convert back to LangChain format
        langchain_messages = self._convert_to_langchain(processed_messages)
        
        # Call underlying LLM with processed messages
        return self.llm._generate(
            langchain_messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs
        )
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        """Async generate with context management"""
        self._call_count += 1
        
        # Convert LangChain messages to our format
        for msg in messages:
            self._add_langchain_message(msg)
        
        # Get processed context
        processed_messages = self.context_manager.get_context()
        
        if self.verbose:
            print(f"\n[Context Management - Call {self._call_count}]")
            print(f"Original messages: {len(messages)}")
            print(f"Processed messages: {len(processed_messages)}")
            print(f"Reduction: {self.context_manager.get_metrics()['token_metrics']['reduction_percentage']:.1f}%")
        
        # Convert back to LangChain format
        langchain_messages = self._convert_to_langchain(processed_messages)
        
        # Call underlying LLM with processed messages
        return await self.llm._agenerate(
            langchain_messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs
        )
    
    def _add_langchain_message(self, msg: BaseMessage) -> None:
        """Convert and add a LangChain message"""
        content = str(msg.content)
        
        if isinstance(msg, SystemMessage):
            msg_type = MessageType.SYSTEM
        elif isinstance(msg, AIMessage):
            msg_type = MessageType.ASSISTANT
        elif isinstance(msg, ToolMessage):
            msg_type = MessageType.TOOL_RESPONSE
            tool_name = getattr(msg, 'name', None)
        elif isinstance(msg, HumanMessage):
            msg_type = MessageType.USER
        else:
            msg_type = MessageType.USER
            
        message = Message(
            type=msg_type,
            content=content,
            timestamp=datetime.now(UTC),
            tool_name=getattr(msg, 'name', None) if hasattr(msg, 'name') else None
        )
        
        self.context_manager.add_message(message)
    
    def _convert_to_langchain(self, messages: List[Message]) -> List[BaseMessage]:
        """Convert our messages back to LangChain format"""
        result = []
        
        for msg in messages:
            if msg.type == MessageType.SYSTEM:
                result.append(SystemMessage(content=msg.content))
            elif msg.type == MessageType.ASSISTANT:
                result.append(AIMessage(content=msg.content))
            elif msg.type == MessageType.TOOL_RESPONSE:
                # ToolMessage requires both content and tool_call_id
                # Since we don't preserve tool_call_id, convert to AIMessage
                result.append(AIMessage(content=f"Tool Response: {msg.content}"))
            else:
                result.append(HumanMessage(content=msg.content))
        
        return result
    
    @property
    def _llm_type(self) -> str:
        """Return the LLM type"""
        return f"context_managed_{self.llm._llm_type}"
    
    def get_context_summary(self) -> str:
        """Get context management summary"""
        return self.context_manager.get_summary()
    
    def get_metrics(self) -> dict[str, Any]:
        """Get context management metrics"""
        return self.context_manager.get_metrics()