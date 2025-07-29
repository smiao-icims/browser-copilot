"""
Agent factory for creating browser automation agents

This module provides the AgentFactory class that handles the creation
and configuration of LangGraph ReAct agents for browser automation.
"""

from typing import Any, Optional

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession

from .context_management.base import ContextConfig
from .context_management.hooks import create_context_hook


class AgentFactory:
    """Factory for creating browser automation agents"""

    def __init__(self, llm: Any):
        """
        Initialize AgentFactory with LLM instance

        Args:
            llm: Initialized LLM instance from ModelForge
        """
        self.llm = llm

    async def create_browser_agent(
        self,
        session: ClientSession,
        recursion_limit: int = 100,
        context_strategy: str = "sliding-window",
        context_config: Optional[ContextConfig] = None,
        verbose: bool = False,
    ) -> Any:
        """
        Create a ReAct agent configured for browser automation

        Args:
            session: MCP client session for browser tools
            recursion_limit: Maximum recursion depth for agent execution
            context_strategy: Context management strategy
            context_config: Optional context configuration
            verbose: Enable verbose logging

        Returns:
            Configured LangGraph ReAct agent with browser tools
        """
        # Load MCP tools from the browser session
        tools = await load_mcp_tools(session)

        # Create pre-model hook using the factory
        pre_model_hook = None
        if context_strategy != "no-op" and not context_config:
            # Skip hook creation if config is required but not provided
            pass
        else:
            pre_model_hook = create_context_hook(
                strategy=context_strategy,
                config=context_config,
                verbose=verbose
            )

        # Create ReAct agent with browser tools and pre-model hook
        agent = create_react_agent(
            self.llm, 
            tools,
            pre_model_hook=pre_model_hook
        )

        # Configure agent with recursion limit
        agent = agent.with_config(recursion_limit=recursion_limit)
        
        # Store hook reference for metrics access
        if hasattr(pre_model_hook, 'context_manager'):
            agent._context_manager = pre_model_hook.context_manager

        return agent

    def get_llm(self) -> Any:
        """
        Get the LLM instance used by this factory

        Returns:
            The LLM instance
        """
        return self.llm
