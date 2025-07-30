"""
Tests for test result data models
"""

from datetime import UTC, datetime

import pytest

from browser_copilot.models.execution import ExecutionTiming
from browser_copilot.models.metrics import TokenMetrics
from browser_copilot.models.results import BrowserTestResult, TestResult


class TestTestResult:
    """Test cases for TestResult model"""

    def test_construction_basic(self):
        """Test basic TestResult construction"""
        result = TestResult(
            success=True,
            test_name="Login Test",
            duration=15.5,
            steps_executed=10,
            report="Test completed successfully",
        )

        assert result.success is True
        assert result.test_name == "Login Test"
        assert result.duration == 15.5
        assert result.steps_executed == 10
        assert result.report == "Test completed successfully"
        assert result.error is None

    def test_construction_with_error(self):
        """Test TestResult with error"""
        result = TestResult(
            success=False,
            test_name="Failed Test",
            duration=5.0,
            steps_executed=3,
            report="Test failed",
            error="Element not found",
        )

        assert result.success is False
        assert result.error == "Element not found"

    def test_validation(self):
        """Test TestResult validation"""
        # Negative duration
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            TestResult(success=True, test_name="Test", duration=-1.0, steps_executed=5)

        # Negative steps
        with pytest.raises(ValueError, match="Steps executed cannot be negative"):
            TestResult(success=True, test_name="Test", duration=10.0, steps_executed=-1)

        # Empty test name
        with pytest.raises(ValueError, match="Test name cannot be empty"):
            TestResult(success=True, test_name="", duration=10.0, steps_executed=5)

    def test_to_dict(self):
        """Test TestResult serialization"""
        result = TestResult(
            success=True,
            test_name="API Test",
            duration=20.0,
            steps_executed=15,
            report="All assertions passed",
            error=None,
        )

        data = result.to_dict()
        assert data == {
            "success": True,
            "test_name": "API Test",
            "duration": 20.0,
            "steps_executed": 15,
            "report": "All assertions passed",
            "error": None,
        }

    def test_from_dict(self):
        """Test TestResult deserialization"""
        data = {
            "success": False,
            "test_name": "Regression Test",
            "duration": 30.5,
            "steps_executed": 20,
            "report": "Test failed at step 15",
            "error": "Timeout waiting for element",
        }

        result = TestResult.from_dict(data)
        assert result.success is False
        assert result.test_name == "Regression Test"
        assert result.duration == 30.5
        assert result.steps_executed == 20
        assert result.error == "Timeout waiting for element"


class TestBrowserTestResult:
    """Test cases for BrowserTestResult model"""

    def test_construction_minimal(self):
        """Test minimal BrowserTestResult construction"""
        result = BrowserTestResult(
            success=True, test_name="Simple Test", duration=10.0, steps_executed=5
        )

        assert result.success is True
        assert result.test_name == "Simple Test"
        assert result.duration == 10.0
        assert result.steps_executed == 5
        assert result.report == ""
        assert result.provider is None
        assert result.model is None
        assert result.browser is None
        assert result.headless is False
        assert result.viewport_size == "1920,1080"

    def test_construction_complete(self):
        """Test complete BrowserTestResult construction"""
        timing = ExecutionTiming(
            start=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 15, 10, 0, 30, tzinfo=UTC),
            duration_seconds=30.0,
        )

        token_metrics = TokenMetrics(
            total_tokens=1000,
            prompt_tokens=800,
            completion_tokens=200,
            estimated_cost=0.05,
        )

        result = BrowserTestResult(
            success=True,
            test_name="Full Test",
            duration=30.0,
            steps_executed=25,
            report="Comprehensive test report",
            provider="openai",
            model="gpt-4",
            browser="chrome",
            headless=True,
            viewport_size="1366,768",
            execution_time=timing,
            environment={"os": "linux", "version": "2.0"},
            token_usage=token_metrics,
            metrics={"custom": "value"},
            error=None,
            steps=[
                {"type": "navigate", "url": "https://example.com"},
                {"type": "click", "element": "button"},
            ],
            verbose_log={"entries": ["log1", "log2"]},
        )

        assert result.provider == "openai"
        assert result.model == "gpt-4"
        assert result.browser == "chrome"
        assert result.headless is True
        assert result.viewport_size == "1366,768"
        assert result.execution_time == timing
        assert result.token_usage == token_metrics
        assert len(result.steps) == 2

    def test_backward_compatibility_property(self):
        """Test backward compatibility duration_seconds property"""
        result = BrowserTestResult(
            success=True, test_name="Test", duration=25.5, steps_executed=10
        )

        # Should have both duration and duration_seconds
        assert result.duration == 25.5
        assert result.duration_seconds == 25.5

    def test_validation_viewport_format(self):
        """Test viewport size validation"""
        # Valid format
        result = BrowserTestResult(
            success=True,
            test_name="Test",
            duration=10.0,
            steps_executed=5,
            viewport_size="1920,1080",
        )
        assert result.viewport_size == "1920,1080"

        # Invalid format - missing comma
        with pytest.raises(ValueError, match="Invalid viewport size format"):
            BrowserTestResult(
                success=True,
                test_name="Test",
                duration=10.0,
                steps_executed=5,
                viewport_size="1920x1080",
            )

        # Invalid format - non-numeric
        with pytest.raises(ValueError, match="Invalid viewport size format"):
            BrowserTestResult(
                success=True,
                test_name="Test",
                duration=10.0,
                steps_executed=5,
                viewport_size="full,screen",
            )

    def test_to_dict_minimal(self):
        """Test minimal BrowserTestResult serialization"""
        result = BrowserTestResult(
            success=False,
            test_name="Quick Test",
            duration=5.0,
            steps_executed=3,
            error="Test failed",
        )

        data = result.to_dict()

        # Check required fields
        assert data["success"] is False
        assert data["test_name"] == "Quick Test"
        assert data["duration"] == 5.0
        assert data["duration_seconds"] == 5.0  # Backward compat
        assert data["steps_executed"] == 3
        assert data["error"] == "Test failed"

        # Check defaults
        assert data["headless"] is False
        assert data["viewport_size"] == "1920,1080"
        assert data["environment"] == {}
        assert data["metrics"] == {}
        assert data["steps"] == []

    def test_to_dict_complete(self):
        """Test complete BrowserTestResult serialization"""
        timing = ExecutionTiming(
            start=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 15, 10, 1, 0, tzinfo=UTC),
            duration_seconds=60.0,
        )

        token_metrics = TokenMetrics(
            total_tokens=2000,
            prompt_tokens=1500,
            completion_tokens=500,
            estimated_cost=0.10,
            context_usage_percentage=75.0,
        )

        result = BrowserTestResult(
            success=True,
            test_name="Complete Test",
            duration=60.0,
            steps_executed=30,
            report="Detailed report here",
            provider="anthropic",
            model="claude-3",
            browser="firefox",
            headless=True,
            viewport_size="1440,900",
            execution_time=timing,
            environment={"ci": "github", "branch": "main"},
            token_usage=token_metrics,
            metrics={"performance": 95.5},
            steps=[{"action": "test"}],
            verbose_log={"debug": True},
        )

        data = result.to_dict()

        # Check all fields
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3"
        assert data["browser"] == "firefox"
        assert data["headless"] is True
        assert data["viewport_size"] == "1440,900"
        assert data["execution_time"]["start"] == "2024-01-15T10:00:00+00:00"
        assert data["execution_time"]["duration_seconds"] == 60.0
        assert data["token_usage"]["total_tokens"] == 2000
        assert data["token_usage"]["context_usage_percentage"] == 75.0
        assert data["environment"]["ci"] == "github"
        assert data["metrics"]["performance"] == 95.5
        assert data["verbose_log"]["debug"] is True

    def test_from_dict_minimal(self):
        """Test minimal BrowserTestResult deserialization"""
        data = {
            "success": True,
            "test_name": "Basic Test",
            "duration": 12.5,
            "steps_executed": 8,
            "report": "Test passed",
        }

        result = BrowserTestResult.from_dict(data)
        assert result.success is True
        assert result.test_name == "Basic Test"
        assert result.duration == 12.5
        assert result.steps_executed == 8
        assert result.report == "Test passed"

    def test_from_dict_complete(self):
        """Test complete BrowserTestResult deserialization"""
        data = {
            "success": True,
            "test_name": "Full Test",
            "duration": 45.0,
            "duration_seconds": 45.0,  # Should be ignored in favor of duration
            "steps_executed": 20,
            "report": "All tests passed",
            "provider": "openai",
            "model": "gpt-4-turbo",
            "browser": "edge",
            "headless": True,
            "viewport_size": "1600,900",
            "execution_time": {
                "start": "2024-01-15T14:00:00+00:00",
                "end": "2024-01-15T14:00:45+00:00",
                "duration_seconds": 45.0,
                "timezone": "UTC",
            },
            "environment": {"test": "integration"},
            "token_usage": {
                "total_tokens": 3000,
                "prompt_tokens": 2000,
                "completion_tokens": 1000,
                "estimated_cost": 0.15,
                "cost_source": "api",
            },
            "metrics": {"coverage": 85.0},
            "steps": [{"step": 1}, {"step": 2}],
            "verbose_log": {"level": "debug"},
            "error": None,
        }

        result = BrowserTestResult.from_dict(data)
        assert result.success is True
        assert result.provider == "openai"
        assert result.model == "gpt-4-turbo"
        assert result.browser == "edge"
        assert result.headless is True
        assert result.execution_time is not None
        assert result.execution_time.start == datetime(
            2024, 1, 15, 14, 0, 0, tzinfo=UTC
        )
        assert result.token_usage is not None
        assert result.token_usage.total_tokens == 3000
        assert result.metrics["coverage"] == 85.0
        assert len(result.steps) == 2

    def test_from_dict_backward_compatibility(self):
        """Test handling of legacy duration_seconds field"""
        # Only duration_seconds provided (legacy format)
        data = {
            "success": True,
            "test_name": "Legacy Test",
            "duration_seconds": 20.0,  # Old field name
            "steps_executed": 10,
            "report": "Legacy format test",
        }

        result = BrowserTestResult.from_dict(data)
        assert result.duration == 20.0  # Should map to duration
        assert result.duration_seconds == 20.0  # Property should work

    def test_validation_inherited(self):
        """Test that parent class validation is applied"""
        # Should inherit validation from TestResult
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            BrowserTestResult(
                success=True, test_name="Test", duration=-5.0, steps_executed=10
            )
