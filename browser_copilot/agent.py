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
        hil_detection: bool = True,
        hil_detection_model: Optional[str] = None,
        use_interrupt: bool = False,
        checkpointer: Optional[Any] = None,
        verbose: bool = False,
    ) -> Any:
        """
        Create a ReAct agent configured for browser automation

        Args:
            session: MCP client session for browser tools
            recursion_limit: Maximum recursion depth for agent execution
            context_strategy: Context management strategy
            context_config: Optional context configuration
            hil_detection: Enable Human-in-the-Loop detection
            hil_detection_model: Model to use for HIL detection (None for pattern-only)
            use_interrupt: Use interrupt() for HIL instead of automatic continuation
            checkpointer: Optional checkpointer for state persistence (required for interrupt)
            verbose: Enable verbose logging

        Returns:
            Configured LangGraph ReAct agent with browser tools
        """
        # Load MCP tools from the browser session
        tools = await load_mcp_tools(session)
        
        # Add HIL tools if using interrupt mode
        if hil_detection and use_interrupt:
            from .hil_detection.ask_human_tool import ask_human, confirm_action
            tools.extend([ask_human, confirm_action])
            if verbose:
                print("[Agent] Added ask_human and confirm_action tools for HIL")

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

        # Configure HIL detection with post_model_hook (version v2 feature)
        post_model_hook = None
        if hil_detection:
            if verbose:
                print(f"[Agent] Configuring HIL detection with model: {hil_detection_model}")
                print(f"[Agent] Using interrupt mode: {use_interrupt}")
            
            # Create detector model if specified (not 'none')
            detector_llm = None
            if hil_detection_model and hil_detection_model.lower() != 'none':
                # Use ModelForgeRegistry to create detector LLM
                from modelforge.registry import ModelForgeRegistry
                registry = ModelForgeRegistry()
                
                # Use same provider as main LLM if not specified
                if '/' in hil_detection_model:
                    provider, model = hil_detection_model.split('/', 1)
                else:
                    # Default to github_copilot for detector
                    provider = 'github_copilot'
                    model = hil_detection_model
                
                if verbose:
                    print(f"[Agent] Creating detector LLM with provider={provider}, model={model}")
                
                # Create detector LLM with minimal settings
                detector_llm = registry.get_llm(
                    provider_name=provider,
                    model_alias=model
                )
                
                # Configure detector settings
                if hasattr(detector_llm, 'temperature'):
                    detector_llm.temperature = 0
                if hasattr(detector_llm, 'max_tokens'):
                    detector_llm.max_tokens = 200
                    
                if verbose:
                    print(f"[Agent] Detector LLM created: {type(detector_llm).__name__}")
            
            # Choose HIL implementation based on use_interrupt
            if use_interrupt:
                # When using interrupt mode with ask_human tool,
                # we don't need the post_model_hook for HIL detection
                # The ask_human tool handles interrupts directly
                if verbose:
                    print("[Agent] Using ask_human tool for HIL, skipping post_model_hook")
            else:
                # Use existing automatic continuation attempt
                from .hil_detection.hooks import create_hil_post_hook
                post_model_hook = create_hil_post_hook(
                    detector_model=detector_llm,
                    verbose=verbose,
                    fallback_to_patterns=True,
                    confidence_threshold=0.7
                )
        
        # Create checkpointer if using interrupt mode and not provided
        if use_interrupt and not checkpointer:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
            if verbose:
                print("[Agent] Created in-memory checkpointer for interrupt mode")

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
