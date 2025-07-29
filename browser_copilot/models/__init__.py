"""
Browser Copilot Data Models

This package contains strongly-typed data models replacing legacy dictionaries
for improved type safety, validation, and developer experience.
"""

from .base import SerializableModel, ValidatedModel
from .execution import ExecutionMetadata, ExecutionStep, ExecutionTiming
from .metrics import OptimizationSavings, TokenMetrics
from .results import BrowserTestResult, TestResult
from .serialization import ModelEncoder, ModelSerializer

__all__ = [
    # Base classes
    "SerializableModel",
    "ValidatedModel",
    # Execution models
    "ExecutionStep",
    "ExecutionTiming",
    "ExecutionMetadata",
    # Metric models
    "OptimizationSavings",
    "TokenMetrics",
    # Result models
    "BrowserTestResult",
    "TestResult",
    # Serialization utilities
    "ModelEncoder",
    "ModelSerializer",
]
