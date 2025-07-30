"""
Tests for metrics data models
"""

import pytest

from browser_copilot.models.metrics import OptimizationSavings, TokenMetrics


class TestOptimizationSavings:
    """Test cases for OptimizationSavings model"""

    def test_construction_valid(self):
        """Test valid OptimizationSavings construction"""
        savings = OptimizationSavings(
            original_tokens=1000,
            optimized_tokens=700,
            reduction_percentage=30.0,
            strategies_applied=["compression", "summarization"],
            estimated_savings=0.025,
        )

        assert savings.original_tokens == 1000
        assert savings.optimized_tokens == 700
        assert savings.reduction_percentage == 30.0
        assert savings.strategies_applied == ["compression", "summarization"]
        assert savings.estimated_savings == 0.025

    def test_construction_without_estimated_savings(self):
        """Test construction without optional estimated_savings"""
        savings = OptimizationSavings(
            original_tokens=500,
            optimized_tokens=400,
            reduction_percentage=20.0,
            strategies_applied=["deduplication"],
        )

        assert savings.estimated_savings is None

    def test_validation_token_counts(self):
        """Test validation of token counts"""
        # Original tokens less than optimized
        with pytest.raises(
            ValueError, match="Original tokens cannot be less than optimized"
        ):
            OptimizationSavings(
                original_tokens=500,
                optimized_tokens=600,  # More than original
                reduction_percentage=10.0,
                strategies_applied=[],
            )

    def test_validation_percentage_bounds(self):
        """Test validation of reduction percentage"""
        # Negative percentage
        with pytest.raises(
            ValueError, match="Reduction percentage must be between 0 and 100"
        ):
            OptimizationSavings(
                original_tokens=1000,
                optimized_tokens=900,
                reduction_percentage=-10.0,
                strategies_applied=[],
            )

        # Percentage over 100
        with pytest.raises(
            ValueError, match="Reduction percentage must be between 0 and 100"
        ):
            OptimizationSavings(
                original_tokens=1000,
                optimized_tokens=900,
                reduction_percentage=110.0,
                strategies_applied=[],
            )

    def test_to_dict(self):
        """Test OptimizationSavings serialization"""
        savings = OptimizationSavings(
            original_tokens=2000,
            optimized_tokens=1500,
            reduction_percentage=25.0,
            strategies_applied=["prompt_optimization", "context_reduction"],
            estimated_savings=0.05,
        )

        data = savings.to_dict()
        assert data == {
            "original_tokens": 2000,
            "optimized_tokens": 1500,
            "reduction_percentage": 25.0,
            "strategies_applied": ["prompt_optimization", "context_reduction"],
            "estimated_savings": 0.05,
        }

    def test_from_dict(self):
        """Test OptimizationSavings deserialization"""
        data = {
            "original_tokens": 1500,
            "optimized_tokens": 1000,
            "reduction_percentage": 33.33,
            "strategies_applied": ["caching"],
            "estimated_savings": 0.042,
        }

        savings = OptimizationSavings.from_dict(data)
        assert savings.original_tokens == 1500
        assert savings.optimized_tokens == 1000
        assert savings.reduction_percentage == 33.33
        assert savings.strategies_applied == ["caching"]
        assert savings.estimated_savings == 0.042


class TestTokenMetrics:
    """Test cases for TokenMetrics model"""

    def test_construction_basic(self):
        """Test basic TokenMetrics construction"""
        metrics = TokenMetrics(
            total_tokens=1000, prompt_tokens=800, completion_tokens=200
        )

        assert metrics.total_tokens == 1000
        assert metrics.prompt_tokens == 800
        assert metrics.completion_tokens == 200
        assert metrics.estimated_cost is None
        assert metrics.cost_source == "telemetry"

    def test_construction_with_cost(self):
        """Test TokenMetrics with cost information"""
        metrics = TokenMetrics(
            total_tokens=5000,
            prompt_tokens=3000,
            completion_tokens=2000,
            estimated_cost=0.15,
            cost_source="provider_api",
        )

        assert metrics.estimated_cost == 0.15
        assert metrics.cost_source == "provider_api"

    def test_construction_with_context_info(self):
        """Test TokenMetrics with context usage information"""
        metrics = TokenMetrics(
            total_tokens=10000,
            prompt_tokens=7000,
            completion_tokens=3000,
            context_length=9500,
            max_context_length=16000,
            context_usage_percentage=59.375,
        )

        assert metrics.context_length == 9500
        assert metrics.max_context_length == 16000
        assert metrics.context_usage_percentage == 59.375

    def test_construction_with_optimization(self):
        """Test TokenMetrics with optimization savings"""
        optimization = OptimizationSavings(
            original_tokens=2000,
            optimized_tokens=1500,
            reduction_percentage=25.0,
            strategies_applied=["compression"],
        )

        metrics = TokenMetrics(
            total_tokens=1500,
            prompt_tokens=1200,
            completion_tokens=300,
            optimization_savings=optimization,
        )

        assert metrics.optimization_savings == optimization
        assert metrics.optimization_savings.reduction_percentage == 25.0

    def test_validation_negative_tokens(self):
        """Test validation rejects negative token counts"""
        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            TokenMetrics(total_tokens=-100, prompt_tokens=50, completion_tokens=50)

    def test_validation_token_sum(self):
        """Test validation of token sum consistency"""
        with pytest.raises(
            ValueError, match="Total tokens must equal prompt \\+ completion tokens"
        ):
            TokenMetrics(
                total_tokens=1000,
                prompt_tokens=600,
                completion_tokens=300,  # Sum is 900, not 1000
            )

    def test_validation_context_percentage(self):
        """Test validation of context usage percentage"""
        # Negative percentage
        with pytest.raises(ValueError, match="Context usage must be between 0 and 100"):
            TokenMetrics(
                total_tokens=1000,
                prompt_tokens=800,
                completion_tokens=200,
                context_usage_percentage=-5.0,
            )

        # Over 100%
        with pytest.raises(ValueError, match="Context usage must be between 0 and 100"):
            TokenMetrics(
                total_tokens=1000,
                prompt_tokens=800,
                completion_tokens=200,
                context_usage_percentage=105.0,
            )

    def test_to_dict_minimal(self):
        """Test minimal TokenMetrics serialization"""
        metrics = TokenMetrics(
            total_tokens=500, prompt_tokens=400, completion_tokens=100
        )

        data = metrics.to_dict()
        assert data == {
            "total_tokens": 500,
            "prompt_tokens": 400,
            "completion_tokens": 100,
            "cost_source": "telemetry",
        }

    def test_to_dict_complete(self):
        """Test complete TokenMetrics serialization"""
        optimization = OptimizationSavings(
            original_tokens=2000,
            optimized_tokens=1500,
            reduction_percentage=25.0,
            strategies_applied=["smart_truncation"],
        )

        metrics = TokenMetrics(
            total_tokens=1500,
            prompt_tokens=1200,
            completion_tokens=300,
            estimated_cost=0.045,
            cost_source="calculated",
            context_length=15000,
            max_context_length=32000,
            context_usage_percentage=46.875,
            optimization_savings=optimization,
        )

        data = metrics.to_dict()
        assert data["total_tokens"] == 1500
        assert data["prompt_tokens"] == 1200
        assert data["completion_tokens"] == 300
        assert data["estimated_cost"] == 0.045
        assert data["cost_source"] == "calculated"
        assert data["context_length"] == 15000
        assert data["max_context_length"] == 32000
        assert data["context_usage_percentage"] == 46.875
        assert "optimization" in data
        assert data["optimization"]["reduction_percentage"] == 25.0

    def test_from_dict_minimal(self):
        """Test minimal TokenMetrics deserialization"""
        data = {
            "total_tokens": 1000,
            "prompt_tokens": 700,
            "completion_tokens": 300,
        }

        metrics = TokenMetrics.from_dict(data)
        assert metrics.total_tokens == 1000
        assert metrics.prompt_tokens == 700
        assert metrics.completion_tokens == 300
        assert metrics.cost_source == "telemetry"  # Default

    def test_from_dict_complete(self):
        """Test complete TokenMetrics deserialization"""
        data = {
            "total_tokens": 5000,
            "prompt_tokens": 3500,
            "completion_tokens": 1500,
            "estimated_cost": 0.125,
            "cost_source": "api_response",
            "context_length": 4800,
            "max_context_length": 8000,
            "context_usage_percentage": 60.0,
            "optimization": {
                "original_tokens": 6000,
                "optimized_tokens": 5000,
                "reduction_percentage": 16.67,
                "strategies_applied": ["deduplication", "compression"],
            },
        }

        metrics = TokenMetrics.from_dict(data)
        assert metrics.total_tokens == 5000
        assert metrics.estimated_cost == 0.125
        assert metrics.context_usage_percentage == 60.0
        assert metrics.optimization_savings is not None
        assert metrics.optimization_savings.original_tokens == 6000
        assert len(metrics.optimization_savings.strategies_applied) == 2

    def test_calculate_cost_method(self):
        """Test cost calculation method"""
        metrics = TokenMetrics(
            total_tokens=10000,
            prompt_tokens=7000,
            completion_tokens=3000,
            estimated_cost=0.30,
        )

        # Test cost per thousand tokens
        assert (
            metrics.cost_per_thousand_tokens() == 0.03
        )  # $0.30 for 10k tokens = $0.03 per 1k

    def test_calculate_cost_method_no_cost(self):
        """Test cost calculation when no cost is set"""
        metrics = TokenMetrics(
            total_tokens=1000, prompt_tokens=800, completion_tokens=200
        )

        assert metrics.cost_per_thousand_tokens() is None
