"""
Test result data models

Models for test execution results with browser-specific extensions.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from .base import ValidatedModel
from .execution import ExecutionStep, ExecutionTiming
from .metrics import TokenMetrics


@dataclass
class TestResult(ValidatedModel):
    """Basic test result model"""

    success: bool
    test_name: str
    duration: float
    steps_executed: int
    report: str = ""
    error: str | None = None

    def validate(self) -> None:
        """Validate test result constraints"""
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if self.steps_executed < 0:
            raise ValueError("Steps executed cannot be negative")
        if not self.test_name:
            raise ValueError("Test name cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "test_name": self.test_name,
            "duration": self.duration,
            "steps_executed": self.steps_executed,
            "report": self.report,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestResult":
        """Create from dictionary"""
        return cls(
            success=data["success"],
            test_name=data["test_name"],
            duration=data["duration"],
            steps_executed=data["steps_executed"],
            report=data.get("report", ""),
            error=data.get("error"),
        )


@dataclass
class BrowserTestResult(TestResult):
    """Complete browser test result"""

    # Provider information
    provider: str | None = None
    model: str | None = None
    browser: str | None = None

    # Browser configuration
    headless: bool = False
    viewport_size: str = "1920,1080"

    # Detailed metrics (using nested models)
    execution_time: ExecutionTiming | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    token_usage: TokenMetrics | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    # Optional fields
    steps: list[ExecutionStep] = field(default_factory=list)
    verbose_log: dict[str, Any] | None = None

    # Backward compatibility
    @property
    def duration_seconds(self) -> float:
        """Alias for backward compatibility"""
        return self.duration

    def validate(self) -> None:
        """Validate test result constraints"""
        # Call parent validation
        super().validate()

        # Validate viewport format
        if not re.match(r"^\d+,\d+$", self.viewport_size):
            raise ValueError(f"Invalid viewport size format: {self.viewport_size}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format"""
        result = {
            "success": self.success,
            "test_name": self.test_name,
            "duration": self.duration,
            "duration_seconds": self.duration,  # Backward compat
            "steps_executed": self.steps_executed,
            "report": self.report,
            "provider": self.provider,
            "model": self.model,
            "browser": self.browser,
            "headless": self.headless,
            "viewport_size": self.viewport_size,
            "environment": self.environment,
            "metrics": self.metrics,
            "steps": [
                step.to_dict() if hasattr(step, "to_dict") else step
                for step in self.steps
            ],
        }

        # Add optional fields if present
        if self.execution_time:
            result["execution_time"] = self.execution_time.to_dict()
        if self.token_usage:
            result["token_usage"] = self.token_usage.to_dict()
        if self.error:
            result["error"] = self.error
        if self.verbose_log is not None:
            result["verbose_log"] = self.verbose_log

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserTestResult":
        """Create from dictionary"""
        # Handle backward compatibility for duration field
        duration = data.get("duration", data.get("duration_seconds", 0.0))

        # Parse nested models if present
        execution_time = None
        if "execution_time" in data and data["execution_time"]:
            execution_time = ExecutionTiming.from_dict(data["execution_time"])

        token_usage = None
        if "token_usage" in data and data["token_usage"]:
            token_usage = TokenMetrics.from_dict(data["token_usage"])

        # Parse steps
        steps = []
        for step_data in data.get("steps", []):
            if isinstance(step_data, dict) and "type" in step_data:
                steps.append(ExecutionStep.from_dict(step_data))
            else:
                # For backward compatibility, keep raw dict steps
                steps.append(step_data)

        return cls(
            success=data["success"],
            test_name=data["test_name"],
            duration=duration,
            steps_executed=data["steps_executed"],
            report=data.get("report", ""),
            provider=data.get("provider"),
            model=data.get("model"),
            browser=data.get("browser"),
            headless=data.get("headless", False),
            viewport_size=data.get("viewport_size", "1920,1080"),
            execution_time=execution_time,
            environment=data.get("environment", {}),
            token_usage=token_usage,
            metrics=data.get("metrics", {}),
            error=data.get("error"),
            steps=steps,
            verbose_log=data.get("verbose_log"),
        )
