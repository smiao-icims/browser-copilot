"""
Tests for TokenMetricsCollector component
"""

from unittest.mock import MagicMock

import pytest
from modelforge.telemetry import TelemetryCallback

from browser_copilot.components.llm_manager import LLMManager
from browser_copilot.components.models import ModelMetadata
from browser_copilot.components.token_metrics import TokenMetricsCollector
from browser_copilot.models import TokenMetrics
from browser_copilot.token_optimizer import TokenOptimizer


class TestTokenMetricsCollector:
    """Test cases for TokenMetricsCollector"""

    @pytest.fixture
    def mock_telemetry(self):
        """Create a mock TelemetryCallback"""
        telemetry = MagicMock(spec=TelemetryCallback)
        # Mock metrics
        metrics = MagicMock()
        token_usage = MagicMock()
        token_usage.total_tokens = 1500
        token_usage.prompt_tokens = 1000
        token_usage.completion_tokens = 500
        metrics.token_usage = token_usage
        metrics.estimated_cost = 0.025
        telemetry.metrics = metrics
        return telemetry

    @pytest.fixture
    def mock_llm_manager(self):
        """Create a mock LLMManager"""
        manager = MagicMock(spec=LLMManager)
        # Mock metadata
        metadata = ModelMetadata(
            context_length=128000,
            supports_streaming=True,
            supports_tools=True,
            cost_per_1k_prompt=0.01,
            cost_per_1k_completion=0.03,
        )
        manager.get_model_metadata.return_value = metadata
        # Mock LLM
        llm = MagicMock()
        llm.context_length = 128000
        manager.get_llm.return_value = llm
        return manager

    @pytest.fixture
    def mock_optimizer(self):
        """Create a mock TokenOptimizer"""
        optimizer = MagicMock(spec=TokenOptimizer)
        optimizer.get_metrics.return_value = {
            "original_tokens": 2000,
            "optimized_tokens": 1500,
            "reduction_percentage": 25.0,
            "strategies_applied": ["whitespace", "instruction"],
        }
        return optimizer

    @pytest.fixture
    def collector(self, mock_telemetry, mock_llm_manager):
        """Create a TokenMetricsCollector instance"""
        return TokenMetricsCollector(mock_telemetry, mock_llm_manager)

    def test_collect_basic_metrics(self, collector):
        """Test collecting basic token metrics"""
        metrics = collector.collect()
        
        assert isinstance(metrics, TokenMetrics)
        assert metrics.total_tokens == 1500
        assert metrics.prompt_tokens == 1000
        assert metrics.completion_tokens == 500
        assert metrics.estimated_cost == 0.025
        assert metrics.cost_source == "telemetry"

    def test_collect_with_context_usage(self, collector):
        """Test collecting metrics with context usage calculation"""
        metrics = collector.collect()
        
        assert metrics.max_context_length == 128000
        assert metrics.context_usage_percentage == pytest.approx(0.78, rel=0.01)  # 1000/128000

    def test_collect_with_optimization(self, collector, mock_optimizer):
        """Test collecting metrics with optimization data"""
        metrics = collector.collect(optimizer=mock_optimizer)
        
        assert metrics.optimization_savings is not None
        assert metrics.optimization_savings.original_tokens == 2000
        assert metrics.optimization_savings.optimized_tokens == 1500
        assert metrics.optimization_savings.reduction_percentage == 25.0
        assert metrics.optimization_savings.strategies_applied == ["whitespace", "instruction"]
        # 500 tokens saved * (0.025 / 1500 tokens) = 0.0083
        assert metrics.optimization_savings.estimated_savings == pytest.approx(0.0083, rel=0.01)

    def test_extract_from_telemetry_no_metrics(self):
        """Test extraction when telemetry has no metrics"""
        telemetry = MagicMock(spec=TelemetryCallback)
        telemetry.metrics = None
        
        collector = TokenMetricsCollector(telemetry, MagicMock())
        metrics = collector._extract_from_telemetry()
        
        assert metrics == {}

    def test_extract_from_telemetry_no_token_usage(self, mock_llm_manager):
        """Test extraction when metrics has no token usage"""
        telemetry = MagicMock(spec=TelemetryCallback)
        telemetry.metrics = MagicMock()
        telemetry.metrics.token_usage = None
        telemetry.metrics.estimated_cost = 0.01
        
        collector = TokenMetricsCollector(telemetry, mock_llm_manager)
        metrics = collector._extract_from_telemetry()
        
        assert metrics["estimated_cost"] == 0.01
        assert "total_tokens" not in metrics

    def test_calculate_context_usage(self, collector):
        """Test context usage calculation"""
        usage = collector._calculate_context_usage(50000)
        
        assert usage["context_length"] == 50000
        assert usage["max_context_length"] == 128000
        assert usage["context_usage_percentage"] == pytest.approx(39.06, rel=0.01)

    def test_calculate_context_usage_no_metadata(self, mock_telemetry):
        """Test context usage when metadata unavailable"""
        # Mock manager without metadata
        manager = MagicMock(spec=LLMManager)
        manager.get_model_metadata.side_effect = RuntimeError("LLM not initialized")
        
        collector = TokenMetricsCollector(mock_telemetry, manager)
        usage = collector._calculate_context_usage(1000)
        
        assert usage == {}

    def test_calculate_optimization_savings(self, collector, mock_optimizer):
        """Test optimization savings calculation"""
        base_metrics = {
            "total_tokens": 1500,
            "estimated_cost": 0.025,
        }
        
        savings = collector._calculate_optimization_savings(base_metrics, mock_optimizer)
        
        assert savings["original_tokens"] == 2000
        assert savings["optimized_tokens"] == 1500
        assert savings["reduction_percentage"] == 25.0
        # 500 tokens saved * (0.025 / 1500) = 0.0083
        assert savings["estimated_savings"] == pytest.approx(0.0083, rel=0.01)

    def test_calculate_optimization_savings_no_cost(self, collector, mock_optimizer):
        """Test optimization savings without cost data"""
        base_metrics = {"total_tokens": 1500}
        
        savings = collector._calculate_optimization_savings(base_metrics, mock_optimizer)
        
        assert "estimated_savings" not in savings

    def test_collect_fallback_cost_estimation(self, mock_telemetry):
        """Test cost estimation fallback to LLM method"""
        # Remove cost from telemetry
        mock_telemetry.metrics.estimated_cost = None
        
        # Mock LLM with estimate_cost method
        manager = MagicMock(spec=LLMManager)
        llm = MagicMock()
        llm.estimate_cost.return_value = 0.03
        manager.get_llm.return_value = llm
        manager.get_model_metadata.return_value = ModelMetadata(context_length=128000)
        
        collector = TokenMetricsCollector(mock_telemetry, manager)
        metrics = collector.collect()
        
        assert metrics.estimated_cost == 0.03
        assert metrics.cost_source == "enhanced_llm"
        llm.estimate_cost.assert_called_once_with(1000, 500)

    def test_collect_no_cost_available(self, mock_telemetry, mock_llm_manager):
        """Test when no cost estimation is available"""
        # Remove cost from telemetry
        mock_telemetry.metrics.estimated_cost = None
        
        # Remove estimate_cost from LLM
        llm = mock_llm_manager.get_llm.return_value
        del llm.estimate_cost
        
        collector = TokenMetricsCollector(mock_telemetry, mock_llm_manager)
        metrics = collector.collect()
        
        assert metrics.estimated_cost is None
        assert metrics.cost_source == "telemetry"

    def test_collect_handles_exceptions(self, mock_telemetry, mock_llm_manager):
        """Test graceful handling of exceptions"""
        # Make telemetry raise exception
        mock_telemetry.metrics = None
        
        collector = TokenMetricsCollector(mock_telemetry, mock_llm_manager)
        metrics = collector.collect()
        
        # Should return default metrics
        assert metrics.total_tokens == 0
        assert metrics.prompt_tokens == 0
        assert metrics.completion_tokens == 0
        assert metrics.estimated_cost is None

    def test_full_collection_flow(self, collector, mock_optimizer):
        """Test complete metrics collection flow"""
        metrics = collector.collect(optimizer=mock_optimizer)
        
        # Check all fields are populated
        assert metrics.total_tokens == 1500
        assert metrics.prompt_tokens == 1000
        assert metrics.completion_tokens == 500
        assert metrics.estimated_cost == 0.025
        assert metrics.context_usage_percentage is not None
        assert metrics.max_context_length == 128000
        assert metrics.optimization_savings is not None
        assert metrics.cost_source == "telemetry"