"""
Context Management for Browser Copilot

This package provides strategies for managing conversation context
to optimize token usage in ReAct agents.
"""

from .base import ContextConfig, ContextManager, ContextStrategy, Message, MessageType, MessageImportance
from .hooks import create_context_hook, get_strategy_info, list_strategies
from .metrics import ContextMetrics
from .analyzer import MessageAnalyzer, ImportanceScorer

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