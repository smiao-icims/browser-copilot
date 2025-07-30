"""
Context management strategies for Browser Copilot.

This package implements the strategy pattern for different context
management approaches to optimize token usage in ReAct agents.
"""

from .base import ContextStrategy, PreModelHook
from .no_op import NoOpStrategy
from .sliding_window import SlidingWindowStrategy
from .smart_trim import SmartTrimStrategy

__all__ = [
    "ContextStrategy",
    "PreModelHook",
    "NoOpStrategy",
    "SlidingWindowStrategy",
    "SmartTrimStrategy",
]
