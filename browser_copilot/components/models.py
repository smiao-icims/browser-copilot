"""
Data models for Browser Copilot components
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
@dataclass
class ExecutionStep:
    """Represents a single execution step"""

    type: str  # "tool_call" | "agent_message"
    name: str | None
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of test execution"""

    steps: list[ExecutionStep]
    final_response: Any
    duration: float
    success: bool


@dataclass
class ModelMetadata:
    """Model capability information"""

    context_length: int
    supports_streaming: bool = True
    supports_tools: bool = True
    cost_per_1k_prompt: float | None = None
    cost_per_1k_completion: float | None = None


@dataclass
class BrowserOptions:
    """Browser configuration options"""

    browser: str = "chromium"
    headless: bool = False
    viewport_width: int = 1920
    viewport_height: int = 1080
    enable_screenshots: bool = True
    device: str | None = None
    user_agent: str | None = None
    proxy_server: str | None = None
    proxy_bypass: str | None = None
    ignore_https_errors: bool = False
    block_service_workers: bool = False
    save_trace: bool = False
    save_session: bool = False
    allowed_origins: str | None = None
    blocked_origins: str | None = None
    no_isolated: bool = False
    output_dir: str | None = None
    timeout: int | None = None


@dataclass
class TestResult:
    """Complete test execution result"""

    success: bool
    test_name: str
    duration: float
    steps_executed: int
    report: str
    token_usage: dict[str, Any]
    metrics: dict[str, Any]
    provider: str | None = None
    model: str | None = None
    browser: str | None = None
    error: str | None = None
    execution_time: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None
    verbose_log: dict[str, Any] | None = None


@dataclass
class TokenMetrics:
    """Token usage and cost metrics"""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float | None = None
    context_usage_percentage: float | None = None
    max_context_length: int | None = None
    optimization_savings: dict[str, Any] | None = None
    cost_source: str | None = None


@dataclass
class OptimizationMetrics:
    """Token optimization metrics"""

    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    strategies_applied: list[str]
    estimated_savings: float | None = None
