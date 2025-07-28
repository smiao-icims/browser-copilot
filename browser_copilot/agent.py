"""
Agent factory for creating browser automation agents

This module provides the AgentFactory class that handles the creation
and configuration of LangGraph ReAct agents for browser automation.
"""

from typing import Any

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession


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
    ) -> Any:
        """
        Create a ReAct agent configured for browser automation

        Args:
            session: MCP client session for browser tools
            recursion_limit: Maximum recursion depth for agent execution

        Returns:
            Configured LangGraph ReAct agent with browser tools
        """
        # Load MCP tools from the browser session
        tools = await load_mcp_tools(session)

        # Create ReAct agent with browser tools
        agent = create_react_agent(self.llm, tools)

        # Configure agent with recursion limit
        agent = agent.with_config(recursion_limit=recursion_limit)

        return agent

    def get_llm(self) -> Any:
        """
        Get the LLM instance used by this factory

        Returns:
            The LLM instance
        """
        return self.llm
