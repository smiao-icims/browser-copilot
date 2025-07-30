"""
Base strategy interface for context management.

This module defines the abstract base class that all context management
strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from langchain_core.messages import BaseMessage

from ..base import ContextConfig


@runtime_checkable
class PreModelHook(Protocol):
    """Protocol for pre-model hook functions."""

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook function signature."""
        ...


class ContextStrategy(ABC):
    """
    Abstract base class for context management strategies.

    Each strategy implements a different approach to managing message
    history to optimize token usage while preserving essential context.
    """

    def __init__(self, config: ContextConfig | None = None, verbose: bool = False):
        """
        Initialize the context strategy.

        Args:
            config: Configuration for the strategy
            verbose: Whether to enable verbose logging
        """
        self.config = config or ContextConfig()
        self.verbose = verbose

    @abstractmethod
    def create_hook(self) -> PreModelHook:
        """
        Create a pre-model hook function for this strategy.

        Returns:
            A callable that can be used as a pre_model_hook in LangGraph
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the human-readable name of this strategy.

        Returns:
            Strategy name
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get a description of how this strategy works.

        Returns:
            Strategy description
        """
        pass

    def validate_config(self) -> list[str]:
        """
        Validate the configuration for this strategy.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.config.window_size <= 0:
            errors.append("Window size must be positive")

        if self.config.preserve_first_n < 0:
            errors.append("Preserve first must be non-negative")

        if self.config.preserve_last_n < 0:
            errors.append("Preserve last must be non-negative")

        return errors

    def count_tokens(self, message: BaseMessage) -> int:
        """
        Estimate token count for a message.

        Uses the simple heuristic: 4 characters ≈ 1 token

        Args:
            message: Message to count tokens for

        Returns:
            Estimated token count
        """
        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )
        return len(content) // 4
