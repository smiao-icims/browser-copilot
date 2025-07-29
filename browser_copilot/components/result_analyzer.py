"""
Result Analyzer component for Browser Copilot

Analyzes test execution results and determines success.
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from ..models import BrowserTestResult, ExecutionTiming
from .models import ExecutionResult


class ResultAnalyzer:
    """Analyzes test execution results"""

    SUCCESS_PATTERNS = [
        r"overall status[:\*]*\s*passed",
        r"status[:\*]*\s*passed",
        r"all tests passed",
        r"test passed successfully",
    ]

    FAILURE_PATTERNS = [
        r"overall status[:\*]*\s*failed",
        r"status[:\*]*\s*failed",
        r"test failed",
    ]

    def analyze(
        self, execution_result: ExecutionResult, test_metadata: dict[str, Any]
    ) -> BrowserTestResult:
        """
        Analyze execution result and build test result

        Args:
            execution_result: The execution result to analyze
            test_metadata: Metadata about the test execution

        Returns:
            BrowserTestResult with all analyzed data
        """
        # Extract test name
        test_name = self._extract_test_name(test_metadata)

        # Get report content
        report_content = ""
        if execution_result.final_response and hasattr(
            execution_result.final_response, "content"
        ):
            report_content = str(execution_result.final_response.content)

        # Determine success
        success = self.check_success(report_content)

        # Build execution time info
        start_time = datetime.now(UTC) - timedelta(seconds=execution_result.duration)
        execution_time = ExecutionTiming(
            start=start_time,
            end=start_time + timedelta(seconds=execution_result.duration),
            duration_seconds=execution_result.duration,
            timezone="UTC",
        )

        # Build metrics
        metrics = self._build_metrics(execution_result)

        # Build environment info
        environment = {
            "token_optimization_enabled": test_metadata.get(
                "token_optimization_enabled", False
            ),
            "compression_level": test_metadata.get("compression_level", "medium"),
        }

        # Extract browser configuration
        browser = None
        headless = False
        viewport_size = "1920,1080"
        if "browser_options" in test_metadata:
            browser_opts = test_metadata["browser_options"]
            browser = browser_opts.get("browser")
            headless = browser_opts.get("headless", False)
            width = browser_opts.get("viewport_width", 1920)
            height = browser_opts.get("viewport_height", 1080)
            viewport_size = f"{width},{height}"

        # Convert steps to dict format
        steps = [
            {
                "type": step.type,
                "name": step.name,
                "content": step.content,
                "timestamp": step.timestamp.isoformat(),
            }
            for step in execution_result.steps
        ]

        return BrowserTestResult(
            success=success,
            test_name=test_name,
            duration=execution_result.duration,
            steps_executed=len(execution_result.steps),
            report=report_content,
            provider=test_metadata.get("provider"),
            model=test_metadata.get("model"),
            browser=browser,
            headless=headless,
            viewport_size=viewport_size,
            execution_time=execution_time,
            environment=environment,
            token_usage=test_metadata.get(
                "token_metrics"
            ),  # Will be TokenMetrics model later
            metrics=metrics,
            error=test_metadata.get("error"),
            steps=steps,
            verbose_log=test_metadata.get("verbose_log"),
        )

    def check_success(self, report_content: str) -> bool:
        """
        Determine if test passed based on report

        Args:
            report_content: The test report content

        Returns:
            True if test passed, False otherwise
        """
        if not report_content:
            return False

        lower_content = report_content.lower()

        # Must have test execution report
        if not self._has_valid_report(report_content):
            return False

        # Check for success patterns
        has_success = any(
            re.search(pattern, lower_content, re.IGNORECASE)
            for pattern in self.SUCCESS_PATTERNS
        )

        # Check for explicit failure
        has_failure = any(
            re.search(pattern, lower_content, re.IGNORECASE)
            for pattern in self.FAILURE_PATTERNS
        )

        return has_success and not has_failure

    def _has_valid_report(self, content: str) -> bool:
        """
        Check if content contains valid test report

        Args:
            content: Content to check

        Returns:
            True if valid report structure found
        """
        return "test execution report" in content.lower()

    def _extract_test_name(self, metadata: dict[str, Any]) -> str:
        """
        Extract test name from metadata

        Args:
            metadata: Test metadata

        Returns:
            Test name or default
        """
        return metadata.get("test_name", "Browser Test")

    def _build_metrics(self, execution_result: ExecutionResult) -> dict[str, Any]:
        """
        Build metrics from execution result

        Args:
            execution_result: The execution result

        Returns:
            Metrics dictionary
        """
        total_steps = len(execution_result.steps)
        execution_time_ms = execution_result.duration * 1000

        return {
            "total_steps": total_steps,
            "execution_time_ms": execution_time_ms,
            "avg_step_time_ms": execution_time_ms / total_steps if total_steps else 0,
        }
