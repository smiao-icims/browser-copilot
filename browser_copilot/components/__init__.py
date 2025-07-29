"""
Browser Copilot components for modular architecture

This package contains refactored components from core.py
"""

from .browser_config import BrowserConfigBuilder
from .exceptions import (
    AnalysisError,
    BrowserPilotError,
    BrowserSetupError,
    ConfigurationError,
    ExecutionError,
)
from .llm_manager import LLMManager
from .models import (
    BrowserOptions,
    ExecutionResult,
    ExecutionStep,
    ModelMetadata,
    OptimizationMetrics,
    TestResult,
    TokenMetrics,
)
from .prompt_builder import PromptBuilder
from .result_analyzer import ResultAnalyzer
from .test_executor import TestExecutor
from .token_metrics import TokenMetricsCollector

__all__ = [
    # Exceptions
    "BrowserPilotError",
    "ConfigurationError",
    "BrowserSetupError",
    "ExecutionError",
    "AnalysisError",
    # Core components
    "LLMManager",
    "BrowserConfigBuilder",
    "PromptBuilder",
    "TestExecutor",
    "ResultAnalyzer",
    "TokenMetricsCollector",
    # Models
    "BrowserOptions",
    "ExecutionStep",
    "ExecutionResult",
    "ModelMetadata",
    "TestResult",
    "TokenMetrics",
    "OptimizationMetrics",
]
