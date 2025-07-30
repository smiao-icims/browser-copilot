"""
Execution-related data models

Models for test execution steps, timing, and metadata.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from .base import ValidatedModel


@dataclass
class ExecutionTiming(ValidatedModel):
    """Detailed execution timing information"""

    start: datetime
    end: datetime
    duration_seconds: float
    timezone: str = "UTC"

    def validate(self) -> None:
        """Validate timing constraints"""
        if self.end < self.start:
            raise ValueError("End time must be after start time")
        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionTiming":
        """Create from dictionary"""
        return cls(
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            duration_seconds=data["duration_seconds"],
            timezone=data.get("timezone", "UTC"),
        )


@dataclass
class ExecutionStep(ValidatedModel):
    """Single execution step with enhanced typing"""

    type: Literal["tool_call", "agent_message"]
    name: str | None
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate step constraints"""
        valid_types = ["tool_call", "agent_message"]
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid step type: {self.type}. Must be one of {valid_types}"
            )

        if self.type == "tool_call" and not self.name:
            raise ValueError("Tool call must have a name")

        if not self.content:
            raise ValueError("Content cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionStep":
        """Create from dictionary"""
        return cls(
            type=data["type"],
            name=data.get("name"),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ExecutionMetadata(ValidatedModel):
    """Metadata about test execution"""

    test_name: str
    provider: str
    model: str
    browser: str

    # Browser configuration
    headless: bool = False
    viewport_width: int = 1920
    viewport_height: int = 1080

    # Execution flags
    token_optimization_enabled: bool = False
    compression_level: Literal["low", "medium", "high"] = "medium"
    verbose_enabled: bool = False

    # Additional metadata
    session_id: str | None = None
    tags: list[str] = field(default_factory=list)
    custom_data: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate metadata constraints"""
        if not self.test_name:
            raise ValueError("Test name cannot be empty")

        # Allow common browser names and playwright browsers
        valid_browsers = [
            "chromium",
            "chrome",
            "firefox",
            "edge",
            "msedge",
            "safari",
            "webkit",
        ]
        if self.browser not in valid_browsers:
            raise ValueError(
                f"Invalid browser: {self.browser}. Must be one of {valid_browsers}"
            )

        if self.viewport_width <= 0:
            raise ValueError("Viewport width must be positive")

        if self.viewport_height <= 0:
            raise ValueError("Viewport height must be positive")

        valid_compression = ["low", "medium", "high"]
        if self.compression_level not in valid_compression:
            raise ValueError(
                f"Invalid compression level: {self.compression_level}. Must be one of {valid_compression}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_name": self.test_name,
            "provider": self.provider,
            "model": self.model,
            "browser": self.browser,
            "headless": self.headless,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "token_optimization_enabled": self.token_optimization_enabled,
            "compression_level": self.compression_level,
            "verbose_enabled": self.verbose_enabled,
            "session_id": self.session_id,
            "tags": self.tags,
            "custom_data": self.custom_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionMetadata":
        """Create from dictionary"""
        return cls(
            test_name=data["test_name"],
            provider=data["provider"],
            model=data["model"],
            browser=data["browser"],
            headless=data.get("headless", False),
            viewport_width=data.get("viewport_width", 1920),
            viewport_height=data.get("viewport_height", 1080),
            token_optimization_enabled=data.get("token_optimization_enabled", False),
            compression_level=data.get("compression_level", "medium"),
            verbose_enabled=data.get("verbose_enabled", False),
            session_id=data.get("session_id"),
            tags=data.get("tags", []),
            custom_data=data.get("custom_data", {}),
        )
