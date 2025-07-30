"""
Agent factory for creating browser automation agents

This module provides the AgentFactory class that handles the creation
and configuration of LangGraph ReAct agents for browser automation.
"""

from typing import Any

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession

from .context_management.base import ContextConfig
from .context_management.hooks import create_context_hook


class AgentFactory:
    """Factory for creating browser automation agents"""

    def __init__(self, llm: Any, provider_name: str = None, model_alias: str = None):
        """
        Initialize AgentFactory with LLM instance

        Args:
            llm: Initialized LLM instance from ModelForge
            provider_name: Optional provider name for HIL configuration
            model_alias: Optional model alias for HIL configuration
        """
        self.llm = llm
        self.provider_name = provider_name
        self.model_alias = model_alias

    async def create_browser_agent(
        self,
        session: ClientSession,
        recursion_limit: int = 100,
        context_strategy: str = "sliding-window",
        context_config: ContextConfig | None = None,
        hil_enabled: bool = False,
        checkpointer: Any | None = None,
        verbose: bool = False,
    ) -> Any:
        """
        Create a ReAct agent configured for browser automation

        Args:
            session: MCP client session for browser tools
            recursion_limit: Maximum recursion depth for agent execution
            context_strategy: Context management strategy
            context_config: Optional context configuration
            hil_enabled: Enable Human-in-the-Loop mode with ask_human tool
            checkpointer: Optional checkpointer for state persistence
            verbose: Enable verbose logging

        Returns:
            Configured LangGraph ReAct agent with browser tools
        """
        # Load MCP tools from the browser session
        tools = await load_mcp_tools(session)

        # Add HIL tools if enabled
        if hil_enabled:
            if verbose:
                print("[Agent] HIL is enabled, loading HIL tools...")

            from .hil_detection import ask_human, configure_hil_llm, confirm_action

            # Configure HIL with current LLM settings if available
            if self.provider_name and self.model_alias:
                configure_hil_llm(self.provider_name, self.model_alias)
                if verbose:
                    print(
                        f"[Agent] Configured HIL with {self.provider_name}/{self.model_alias}"
                    )

            tools.extend([ask_human, confirm_action])
            if verbose:
                print("[Agent] Added ask_human and confirm_action tools for HIL")
                print(f"[Agent] Total tools available: {len(tools)}")
                tool_names = []
                for t in tools:
                    if hasattr(t, "name"):
                        tool_names.append(t.name)
                    else:
                        tool_names.append(str(t))
                print(f"[Agent] Tool names: {tool_names}")
        else:
            if verbose:
                print("[Agent] HIL is disabled")

        # Create pre-model hook using the factory
        pre_model_hook = None
        if context_strategy != "no-op" and not context_config:
            # Skip hook creation if config is required but not provided
            pass
        else:
            pre_model_hook = create_context_hook(
                strategy=context_strategy, config=context_config, verbose=verbose
            )

        # No special configuration needed for HIL when using ask_human tools
        # The tools handle interrupts directly
        post_model_hook = None

        # Create checkpointer if using HIL and not provided
        if hil_enabled and not checkpointer:
            from langgraph.checkpoint.memory import MemorySaver

            checkpointer = MemorySaver()
            if verbose:
                print("[Agent] Created in-memory checkpointer for HIL mode")

        # Create ReAct agent with browser tools and hooks
        # Version v2 is required for post-model hooks (HIL support)
        agent_kwargs = {
            "model": self.llm,
            "tools": tools,
            "version": "v2",  # Required for post-model hooks
        }

        # Add hooks if configured
        if pre_model_hook:
            agent_kwargs["pre_model_hook"] = pre_model_hook
        if post_model_hook:
            agent_kwargs["post_model_hook"] = post_model_hook

        # Add checkpointer if available (required for interrupt)
        if checkpointer:
            agent_kwargs["checkpointer"] = checkpointer

        agent = create_react_agent(**agent_kwargs)

        # Configure agent with recursion limit
        agent = agent.with_config(recursion_limit=recursion_limit)

        # Store hook reference for metrics access (commented out - not needed for compiled graph)
        # if hasattr(pre_model_hook, "context_manager"):
        #     agent._context_manager = pre_model_hook.context_manager

        return agent

    def get_llm(self) -> Any:
        """
        Get the LLM instance used by this factory

        Returns:
            The LLM instance
        """
        return self.llm
