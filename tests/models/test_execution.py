"""
Tests for execution-related data models
"""

from datetime import UTC, datetime

import pytest

from browser_copilot.models.execution import (
    ExecutionMetadata,
    ExecutionStep,
    ExecutionTiming,
)


class TestExecutionTiming:
    """Test cases for ExecutionTiming model"""

    def test_construction_valid(self):
        """Test valid ExecutionTiming construction"""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 15, 10, 0, 30, tzinfo=UTC)

        timing = ExecutionTiming(
            start=start, end=end, duration_seconds=30.0, timezone="UTC"
        )

        assert timing.start == start
        assert timing.end == end
        assert timing.duration_seconds == 30.0
        assert timing.timezone == "UTC"

    def test_to_dict(self):
        """Test ExecutionTiming serialization"""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 15, 10, 0, 30, tzinfo=UTC)

        timing = ExecutionTiming(
            start=start, end=end, duration_seconds=30.0, timezone="America/New_York"
        )

        data = timing.to_dict()
        assert data == {
            "start": "2024-01-15T10:00:00+00:00",
            "end": "2024-01-15T10:00:30+00:00",
            "duration_seconds": 30.0,
            "timezone": "America/New_York",
        }

    def test_from_dict(self):
        """Test ExecutionTiming deserialization"""
        data = {
            "start": "2024-01-15T10:00:00+00:00",
            "end": "2024-01-15T10:00:30+00:00",
            "duration_seconds": 30.0,
            "timezone": "UTC",
        }

        timing = ExecutionTiming.from_dict(data)
        assert timing.start == datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        assert timing.end == datetime(2024, 1, 15, 10, 0, 30, tzinfo=UTC)
        assert timing.duration_seconds == 30.0
        assert timing.timezone == "UTC"

    def test_validation(self):
        """Test ExecutionTiming validation"""
        start = datetime(2024, 1, 15, 10, 0, 30, tzinfo=UTC)
        end = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)  # Before start

        with pytest.raises(ValueError, match="End time must be after start time"):
            ExecutionTiming(start=start, end=end, duration_seconds=30.0)

        # Negative duration
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            ExecutionTiming(start=end, end=start, duration_seconds=-30.0)


class TestExecutionStep:
    """Test cases for ExecutionStep model"""

    def test_construction_tool_call(self):
        """Test ExecutionStep construction for tool call"""
        step = ExecutionStep(
            type="tool_call",
            name="browser_navigate",
            content="Navigated to https://example.com",
        )

        assert step.type == "tool_call"
        assert step.name == "browser_navigate"
        assert step.content == "Navigated to https://example.com"
        assert isinstance(step.timestamp, datetime)
        assert step.metadata == {}

    def test_construction_agent_message(self):
        """Test ExecutionStep construction for agent message"""
        step = ExecutionStep(
            type="agent_message", name=None, content="Analyzing page structure..."
        )

        assert step.type == "agent_message"
        assert step.name is None
        assert step.content == "Analyzing page structure..."

    def test_construction_with_metadata(self):
        """Test ExecutionStep with custom metadata"""
        metadata = {"duration": 1.5, "retries": 2}
        step = ExecutionStep(
            type="tool_call",
            name="browser_click",
            content="Clicked button",
            metadata=metadata,
        )

        assert step.metadata == metadata

    def test_to_dict(self):
        """Test ExecutionStep serialization"""
        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        step = ExecutionStep(
            type="tool_call",
            name="browser_snapshot",
            content="Page snapshot taken",
            timestamp=timestamp,
            metadata={"size": 1024},
        )

        data = step.to_dict()
        assert data == {
            "type": "tool_call",
            "name": "browser_snapshot",
            "content": "Page snapshot taken",
            "timestamp": "2024-01-15T10:30:45+00:00",
            "metadata": {"size": 1024},
        }

    def test_from_dict(self):
        """Test ExecutionStep deserialization"""
        data = {
            "type": "agent_message",
            "name": None,
            "content": "Test completed",
            "timestamp": "2024-01-15T10:30:45+00:00",
            "metadata": {"final": True},
        }

        step = ExecutionStep.from_dict(data)
        assert step.type == "agent_message"
        assert step.name is None
        assert step.content == "Test completed"
        assert step.timestamp == datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        assert step.metadata == {"final": True}

    def test_validation(self):
        """Test ExecutionStep validation"""
        # Invalid type
        with pytest.raises(ValueError, match="Invalid step type"):
            ExecutionStep(
                type="invalid_type",  # type: ignore
                name="test",
                content="content",
            )

        # Tool call without name
        with pytest.raises(ValueError, match="Tool call must have a name"):
            ExecutionStep(type="tool_call", name=None, content="content")

        # Empty content
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ExecutionStep(type="agent_message", name=None, content="")


class TestExecutionMetadata:
    """Test cases for ExecutionMetadata model"""

    def test_construction_basic(self):
        """Test basic ExecutionMetadata construction"""
        metadata = ExecutionMetadata(
            test_name="Login Test",
            provider="openai",
            model="gpt-4",
            browser="chrome",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
        )

        assert metadata.test_name == "Login Test"
        assert metadata.provider == "openai"
        assert metadata.model == "gpt-4"
        assert metadata.browser == "chrome"
        assert metadata.headless is True
        assert metadata.viewport_width == 1920
        assert metadata.viewport_height == 1080

    def test_construction_with_defaults(self):
        """Test ExecutionMetadata with default values"""
        metadata = ExecutionMetadata(
            test_name="Test", provider="openai", model="gpt-4", browser="chrome"
        )

        # Check defaults
        assert metadata.headless is False
        assert metadata.viewport_width == 1920
        assert metadata.viewport_height == 1080
        assert metadata.token_optimization_enabled is False
        assert metadata.compression_level == "medium"
        assert metadata.verbose_enabled is False
        assert metadata.session_id is None
        assert metadata.tags == []
        assert metadata.custom_data == {}

    def test_construction_with_custom_values(self):
        """Test ExecutionMetadata with all custom values"""
        metadata = ExecutionMetadata(
            test_name="Complex Test",
            provider="anthropic",
            model="claude-3",
            browser="firefox",
            headless=True,
            viewport_width=1366,
            viewport_height=768,
            token_optimization_enabled=True,
            compression_level="high",
            verbose_enabled=True,
            session_id="test-123",
            tags=["regression", "critical"],
            custom_data={"environment": "staging", "version": "2.0"},
        )

        assert metadata.token_optimization_enabled is True
        assert metadata.compression_level == "high"
        assert metadata.verbose_enabled is True
        assert metadata.session_id == "test-123"
        assert metadata.tags == ["regression", "critical"]
        assert metadata.custom_data == {"environment": "staging", "version": "2.0"}

    def test_to_dict(self):
        """Test ExecutionMetadata serialization"""
        metadata = ExecutionMetadata(
            test_name="Test",
            provider="openai",
            model="gpt-4",
            browser="chrome",
            session_id="abc-123",
            tags=["smoke", "ui"],
        )

        data = metadata.to_dict()
        assert data["test_name"] == "Test"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["browser"] == "chrome"
        assert data["headless"] is False
        assert data["viewport_width"] == 1920
        assert data["viewport_height"] == 1080
        assert data["session_id"] == "abc-123"
        assert data["tags"] == ["smoke", "ui"]

    def test_from_dict(self):
        """Test ExecutionMetadata deserialization"""
        data = {
            "test_name": "API Test",
            "provider": "anthropic",
            "model": "claude",
            "browser": "edge",
            "headless": True,
            "viewport_width": 1440,
            "viewport_height": 900,
            "token_optimization_enabled": True,
            "compression_level": "low",
            "verbose_enabled": True,
            "session_id": "xyz-789",
            "tags": ["api", "integration"],
            "custom_data": {"api_version": "v2"},
        }

        metadata = ExecutionMetadata.from_dict(data)
        assert metadata.test_name == "API Test"
        assert metadata.provider == "anthropic"
        assert metadata.model == "claude"
        assert metadata.browser == "edge"
        assert metadata.token_optimization_enabled is True
        assert metadata.tags == ["api", "integration"]
        assert metadata.custom_data == {"api_version": "v2"}

    def test_validation(self):
        """Test ExecutionMetadata validation"""
        # Empty test name
        with pytest.raises(ValueError, match="Test name cannot be empty"):
            ExecutionMetadata(
                test_name="", provider="openai", model="gpt-4", browser="chrome"
            )

        # Invalid browser
        with pytest.raises(ValueError, match="Invalid browser"):
            ExecutionMetadata(
                test_name="Test",
                provider="openai",
                model="gpt-4",
                browser="invalid-browser",
            )

        # Invalid viewport dimensions
        with pytest.raises(ValueError, match="Viewport width must be positive"):
            ExecutionMetadata(
                test_name="Test",
                provider="openai",
                model="gpt-4",
                browser="chrome",
                viewport_width=0,
            )

        # Invalid compression level
        with pytest.raises(ValueError, match="Invalid compression level"):
            ExecutionMetadata(
                test_name="Test",
                provider="openai",
                model="gpt-4",
                browser="chrome",
                compression_level="invalid",  # type: ignore
            )
