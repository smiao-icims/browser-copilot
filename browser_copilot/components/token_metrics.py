"""
Token Metrics Collector component for Browser Copilot

Collects token usage and cost metrics from execution.
"""

import logging
from typing import Any

from modelforge.telemetry import TelemetryCallback

from ..models import OptimizationSavings
from ..models import TokenMetrics as NewTokenMetrics
from ..token_optimizer import TokenOptimizer
from .llm_manager import LLMManager

logger = logging.getLogger(__name__)


class TokenMetricsCollector:
    """Collects token usage and cost metrics"""

    def __init__(self, telemetry: TelemetryCallback, llm_manager: LLMManager):
        """
        Initialize TokenMetricsCollector

        Args:
            telemetry: Telemetry callback with usage data
            llm_manager: LLM manager for model metadata
        """
        self.telemetry = telemetry
        self.llm_manager = llm_manager

    def collect(self, optimizer: TokenOptimizer | None = None) -> NewTokenMetrics:
        """
        Collect token metrics from execution

        Args:
            optimizer: Optional token optimizer for savings calculation

        Returns:
            NewTokenMetrics with usage and cost data
        """
        try:
            # Extract base metrics from telemetry
            base_metrics = self._extract_from_telemetry()

            # Get token counts with defaults
            total_tokens = base_metrics.get("total_tokens", 0)
            prompt_tokens = base_metrics.get("prompt_tokens", 0)
            completion_tokens = base_metrics.get("completion_tokens", 0)

            # Get or estimate cost
            estimated_cost = base_metrics.get("estimated_cost")
            cost_source = "telemetry"

            # Try enhanced cost estimation if no cost from telemetry
            if estimated_cost is None and prompt_tokens > 0 and completion_tokens > 0:
                try:
                    llm = self.llm_manager.get_llm()
                    if hasattr(llm, "estimate_cost"):
                        estimated_cost = llm.estimate_cost(
                            prompt_tokens, completion_tokens
                        )
                        cost_source = "enhanced_llm"
                except Exception:
                    pass  # Keep cost as None

            # Calculate context usage if we have prompt tokens
            context_info = {}
            if prompt_tokens > 0:
                context_info = self._calculate_context_usage(prompt_tokens)

            # Calculate optimization savings if optimizer provided
            optimization_savings = None
            if optimizer:
                opt_data = self._calculate_optimization_savings(base_metrics, optimizer)
                optimization_savings = OptimizationSavings(
                    original_tokens=opt_data["original_tokens"],
                    optimized_tokens=opt_data["optimized_tokens"],
                    reduction_percentage=opt_data["reduction_percentage"],
                    strategies_applied=opt_data["strategies_applied"],
                    estimated_savings=opt_data.get("estimated_savings"),
                )

            return NewTokenMetrics(
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost=estimated_cost,
                cost_source=cost_source,
                context_length=context_info.get("context_length"),
                max_context_length=context_info.get("max_context_length"),
                context_usage_percentage=context_info.get("context_usage_percentage"),
                optimization_savings=optimization_savings,
            )

        except Exception as e:
            logger.warning(f"Error collecting token metrics: {e}")
            # Return minimal metrics on error
            return NewTokenMetrics(
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                estimated_cost=None,
            )

    def _extract_from_telemetry(self) -> dict[str, Any]:
        """
        Extract base metrics from telemetry

        Returns:
            Dictionary with available metrics
        """
        if not self.telemetry or not hasattr(self.telemetry, "metrics"):
            return {}

        metrics = self.telemetry.metrics
        if not metrics:
            return {}

        extracted = {}

        # Extract token usage if available
        if hasattr(metrics, "token_usage") and metrics.token_usage:
            token_usage = metrics.token_usage
            extracted.update(
                {
                    "total_tokens": getattr(token_usage, "total_tokens", 0),
                    "prompt_tokens": getattr(token_usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(token_usage, "completion_tokens", 0),
                }
            )

        # Extract cost if available
        if hasattr(metrics, "estimated_cost"):
            extracted["estimated_cost"] = metrics.estimated_cost

        return extracted

    def _calculate_context_usage(self, prompt_tokens: int) -> dict[str, Any]:
        """
        Calculate context utilization

        Args:
            prompt_tokens: Number of prompt tokens

        Returns:
            Dictionary with context usage data
        """
        try:
            metadata = self.llm_manager.get_model_metadata()
            context_length = metadata.context_length

            return {
                "context_length": prompt_tokens,
                "max_context_length": context_length,
                "context_usage_percentage": round(
                    (prompt_tokens / context_length) * 100, 2
                ),
            }
        except Exception:
            # Return empty if metadata unavailable
            return {}

    def _calculate_optimization_savings(
        self, base_metrics: dict[str, Any], optimizer: TokenOptimizer
    ) -> dict[str, Any]:
        """
        Calculate savings from optimization

        Args:
            base_metrics: Base token metrics
            optimizer: Token optimizer with metrics

        Returns:
            Dictionary with optimization savings
        """
        opt_metrics = optimizer.get_metrics()

        savings = {
            "original_tokens": opt_metrics["original_tokens"],
            "optimized_tokens": opt_metrics["optimized_tokens"],
            "reduction_percentage": opt_metrics["reduction_percentage"],
            "strategies_applied": opt_metrics["strategies_applied"],
        }

        # Estimate cost savings if we have cost data
        if (
            base_metrics.get("estimated_cost")
            and base_metrics.get("total_tokens", 0) > 0
        ):
            cost_per_token = (
                base_metrics["estimated_cost"] / base_metrics["total_tokens"]
            )
            tokens_saved = (
                opt_metrics["original_tokens"] - opt_metrics["optimized_tokens"]
            )
            savings["estimated_savings"] = round(tokens_saved * cost_per_token, 4)

        return savings
