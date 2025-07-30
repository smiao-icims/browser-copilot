"""
Factory for creating context management hooks.

This module provides a clean interface for creating pre-model hooks
based on strategy names.
"""

from .base import ContextConfig
from .strategies import (
    ContextStrategy,
    NoOpStrategy,
    PreModelHook,
    SlidingWindowStrategy,
    SmartTrimStrategy,
)


def create_context_hook(
    strategy: str, config: ContextConfig | None = None, verbose: bool = False
) -> PreModelHook:
    """
    Create a context management hook based on strategy name.

    Args:
        strategy: Name of the strategy ("no-op", "sliding-window", "smart-trim")
        config: Configuration for the strategy (not needed for no-op)
        verbose: Whether to enable verbose logging

    Returns:
        A pre-model hook function

    Raises:
        ValueError: If strategy name is not recognized
    """
    strategy_classes = {
        "no-op": NoOpStrategy,
        "sliding-window": SlidingWindowStrategy,
        "smart-trim": SmartTrimStrategy,
    }

    if strategy not in strategy_classes:
        raise ValueError(
            f"Unknown strategy: {strategy}. "
            f"Available strategies: {', '.join(strategy_classes.keys())}"
        )

    # Create strategy instance
    strategy_class = strategy_classes[strategy]
    strategy_instance: ContextStrategy = strategy_class(config=config, verbose=verbose)  # type: ignore[abstract]

    # Validate configuration
    if config and strategy != "no-op":
        errors = strategy_instance.validate_config()
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    # Return the hook
    return strategy_instance.create_hook()


def get_strategy_info(strategy: str) -> dict:
    """
    Get information about a strategy.

    Args:
        strategy: Name of the strategy

    Returns:
        Dictionary with strategy information

    Raises:
        ValueError: If strategy name is not recognized
    """
    strategy_classes = {
        "no-op": NoOpStrategy,
        "sliding-window": SlidingWindowStrategy,
        "smart-trim": SmartTrimStrategy,
    }

    if strategy not in strategy_classes:
        raise ValueError(f"Unknown strategy: {strategy}")

    strategy_class = strategy_classes[strategy]
    instance: ContextStrategy = strategy_class(config=None, verbose=False)  # type: ignore[abstract]

    return {
        "name": instance.get_name(),
        "description": instance.get_description(),
        "requires_config": strategy != "no-op",
    }


def list_strategies() -> list[str]:
    """
    List all available context management strategies.

    Returns:
        List of strategy names
    """
    return ["no-op", "sliding-window", "smart-trim"]
