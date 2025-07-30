"""
Context Management for Browser Copilot

This package provides strategies for managing conversation context
to optimize token usage in ReAct agents.
"""

from .analyzer import ImportanceScorer, MessageAnalyzer
from .base import (
    ContextConfig,
    ContextManager,
    ContextStrategy,
    Message,
    MessageImportance,
    MessageType,
)
from .hooks import create_context_hook, get_strategy_info, list_strategies
from .metrics import ContextMetrics

__all__ = [
    # Core classes
    "ContextConfig",
    "ContextManager",
    "ContextStrategy",
    "Message",
    "MessageType",
    "MessageImportance",
    "ContextMetrics",
    "MessageAnalyzer",
    "ImportanceScorer",
    # Factory functions
    "create_context_hook",
    "get_strategy_info",
    "list_strategies",
]
