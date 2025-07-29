"""
Context Management for Browser Copilot

This package provides strategies for managing conversation context
to optimize token usage in ReAct agents.
"""

from .base import ContextManager, ContextStrategy, Message, ContextConfig, MessageType, MessageImportance
from .metrics import ContextMetrics
from .analyzer import MessageAnalyzer, ImportanceScorer

__all__ = [
    "ContextManager",
    "ContextStrategy", 
    "Message",
    "ContextConfig",
    "MessageType",
    "MessageImportance",
    "ContextMetrics",
    "MessageAnalyzer",
    "ImportanceScorer",
]