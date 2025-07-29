"""
Metrics data models

Models for token usage, costs, and optimization metrics.
"""

import dataclasses
from dataclasses import dataclass
from typing import Any

from .base import ValidatedModel


@dataclass
class OptimizationSavings(ValidatedModel):
    """Token optimization savings details"""

    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    strategies_applied: list[str]
    estimated_savings: float | None = None

    def validate(self) -> None:
        """Validate optimization constraints"""
        if self.original_tokens < self.optimized_tokens:
            raise ValueError("Original tokens cannot be less than optimized tokens")
        if not 0 <= self.reduction_percentage <= 100:
            raise ValueError("Reduction percentage must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "reduction_percentage": self.reduction_percentage,
            "strategies_applied": self.strategies_applied,
            "estimated_savings": self.estimated_savings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationSavings":
        """Create from dictionary"""
        return cls(
            original_tokens=data["original_tokens"],
            optimized_tokens=data["optimized_tokens"],
            reduction_percentage=data["reduction_percentage"],
            strategies_applied=data["strategies_applied"],
            estimated_savings=data.get("estimated_savings"),
        )


@dataclass
class TokenMetrics(ValidatedModel):
    """Token usage and cost metrics"""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float | None = None
    cost_source: str = "telemetry"

    # Context usage
    context_length: int | None = None
    max_context_length: int | None = None
    context_usage_percentage: float | None = None

    # Optimization
    optimization_savings: OptimizationSavings | None = None

    def validate(self) -> None:
        """Validate token metrics"""
        if (
            self.total_tokens < 0
            or self.prompt_tokens < 0
            or self.completion_tokens < 0
        ):
            raise ValueError("Token counts cannot be negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("Total tokens must equal prompt + completion tokens")
        if self.context_usage_percentage is not None:
            if not 0 <= self.context_usage_percentage <= 100:
                raise ValueError("Context usage must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_source": self.cost_source,
        }

        # Add optional fields
        if self.estimated_cost is not None:
            result["estimated_cost"] = self.estimated_cost
        if self.context_length is not None:
            result["context_length"] = self.context_length
        if self.max_context_length is not None:
            result["max_context_length"] = self.max_context_length
        if self.context_usage_percentage is not None:
            result["context_usage_percentage"] = self.context_usage_percentage
        if self.optimization_savings:
            result["optimization"] = dataclasses.asdict(self.optimization_savings)

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenMetrics":
        """Create from dictionary"""
        # Handle optimization savings if present
        optimization = None
        if "optimization" in data:
            optimization = OptimizationSavings.from_dict(data["optimization"])

        return cls(
            total_tokens=data["total_tokens"],
            prompt_tokens=data["prompt_tokens"],
            completion_tokens=data["completion_tokens"],
            estimated_cost=data.get("estimated_cost"),
            cost_source=data.get("cost_source", "telemetry"),
            context_length=data.get("context_length"),
            max_context_length=data.get("max_context_length"),
            context_usage_percentage=data.get("context_usage_percentage"),
            optimization_savings=optimization,
        )

    def cost_per_thousand_tokens(self) -> float | None:
        """Calculate cost per thousand tokens"""
        if self.estimated_cost is None or self.total_tokens == 0:
            return None
        return (self.estimated_cost / self.total_tokens) * 1000
