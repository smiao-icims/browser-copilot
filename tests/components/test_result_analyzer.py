"""
Tests for ResultAnalyzer component
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from browser_copilot.components.models import ExecutionResult, ExecutionStep
from browser_copilot.components.result_analyzer import ResultAnalyzer
from browser_copilot.models import BrowserTestResult


class TestResultAnalyzer:
    """Test cases for ResultAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create a ResultAnalyzer instance"""
        return ResultAnalyzer()

    @pytest.fixture
    def mock_execution_result(self):
        """Create a mock ExecutionResult"""
        steps = [
            ExecutionStep("tool_call", "browser_navigate", "Navigated to site"),
            ExecutionStep("agent_message", None, "Analyzing page structure for test execution"),
            ExecutionStep("tool_call", "browser_click", "Clicked submit button"),
        ]
        
        final_response = MagicMock()
        final_response.content = """# Test Execution Report

## Summary
- Overall Status: PASSED
- Duration: 5 seconds
- Browser: chromium

## Test Results

### Login Test
**Status:** PASSED

**Steps Executed:**
1. ✅ Navigated to login page
2. ✅ Entered credentials
3. ✅ Clicked submit
4. ✅ Verified successful login

**Screenshots Taken:**
- login_page.png
- dashboard.png

## Issues Encountered
None

## Recommendations
Test completed successfully."""
        
        return ExecutionResult(
            steps=steps,
            final_response=final_response,
            duration=5.0,
            success=True,
        )

    @pytest.fixture
    def test_metadata(self):
        """Create test metadata"""
        return {
            "test_name": "Login Test",
            "provider": "openai",
            "model": "gpt-4",
            "browser_options": {"browser": "chromium", "headless": False},
            "token_metrics": {
                "total_tokens": 1000,
                "prompt_tokens": 800,
                "completion_tokens": 200,
                "estimated_cost": 0.02,
            },
        }

    def test_analyze_successful_test(self, analyzer, mock_execution_result, test_metadata):
        """Test analyzing a successful test execution"""
        result = analyzer.analyze(mock_execution_result, test_metadata)
        
        assert isinstance(result, BrowserTestResult)
        assert result.success is True
        assert result.test_name == "Login Test"
        assert result.duration == 5.0
        assert result.steps_executed == 3
        assert "Test Execution Report" in result.report
        assert result.provider == "openai"
        assert result.model == "gpt-4"
        assert result.browser == "chromium"
        assert result.error is None

    def test_analyze_failed_test(self, analyzer, test_metadata):
        """Test analyzing a failed test execution"""
        # Create failed execution result
        final_response = MagicMock()
        final_response.content = """# Test Execution Report

## Summary
- Overall Status: FAILED
- Duration: 3 seconds

## Test Results

### Login Test
**Status:** FAILED

**Steps Executed:**
1. ✅ Navigated to login page
2. ❌ Failed to find login button - Error: Element not found

## Issues Encountered
Could not locate the login button on the page."""
        
        execution_result = ExecutionResult(
            steps=[ExecutionStep("tool_call", "browser_navigate", "Nav")],
            final_response=final_response,
            duration=3.0,
            success=False,
        )
        
        result = analyzer.analyze(execution_result, test_metadata)
        
        assert result.success is False
        assert result.duration == 3.0
        assert "FAILED" in result.report

    def test_analyze_no_final_response(self, analyzer, test_metadata):
        """Test analyzing execution with no final response"""
        execution_result = ExecutionResult(
            steps=[ExecutionStep("tool_call", "browser_click", "Click")],
            final_response=None,
            duration=1.0,
            success=False,
        )
        
        result = analyzer.analyze(execution_result, test_metadata)
        
        assert result.success is False
        assert result.report == ""
        assert result.steps_executed == 1

    def test_check_success_various_patterns(self, analyzer):
        """Test success checking with various patterns"""
        success_cases = [
            "Overall Status: PASSED",
            "overall status: passed",
            "Overall Status:** PASSED",
            "Status: PASSED",
            "status:** passed",
            "All tests passed successfully",
            "Test passed successfully",
        ]
        
        for content in success_cases:
            report = f"# Test Execution Report\n{content}"
            assert analyzer.check_success(report) is True

    def test_check_success_failure_patterns(self, analyzer):
        """Test success checking detects failures"""
        failure_cases = [
            "Overall Status: FAILED",
            "overall status:** failed",
            "Test failed with errors",
            "Status: FAILED",
        ]
        
        for content in failure_cases:
            report = f"# Test Execution Report\n{content}"
            assert analyzer.check_success(report) is False

    def test_check_success_no_report(self, analyzer):
        """Test success checking with no report"""
        assert analyzer.check_success("") is False
        assert analyzer.check_success("Random content without report") is False

    def test_check_success_mixed_signals(self, analyzer):
        """Test success checking with contradictory signals"""
        # Has success pattern but also failure - should be False
        report = """# Test Execution Report
Overall Status: PASSED
But actually test failed"""
        assert analyzer.check_success(report) is False

    def test_extract_test_name_from_metadata(self, analyzer):
        """Test test name extraction from metadata"""
        metadata = {"test_name": "Shopping Cart Test"}
        result = analyzer._extract_test_name(metadata)
        assert result == "Shopping Cart Test"

    def test_extract_test_name_fallback(self, analyzer):
        """Test test name extraction with fallback"""
        metadata = {}
        result = analyzer._extract_test_name(metadata)
        assert result == "Browser Test"

    def test_execution_time_in_result(self, analyzer, mock_execution_result, test_metadata):
        """Test that execution time is properly included in result"""
        result = analyzer.analyze(mock_execution_result, test_metadata)
        
        assert result.execution_time is not None
        assert result.execution_time.duration_seconds == 5.0
        assert result.execution_time.timezone == "UTC"
        assert result.execution_time.start < result.execution_time.end

    def test_build_metrics(self, analyzer, mock_execution_result):
        """Test building metrics structure"""
        metrics = analyzer._build_metrics(mock_execution_result)
        
        assert metrics["total_steps"] == 3
        assert metrics["execution_time_ms"] == 5000
        assert metrics["avg_step_time_ms"] == pytest.approx(1666.67, rel=1)

    def test_build_metrics_no_steps(self, analyzer):
        """Test building metrics with no steps"""
        execution_result = ExecutionResult(
            steps=[], final_response=None, duration=1.0, success=False
        )
        
        metrics = analyzer._build_metrics(execution_result)
        
        assert metrics["total_steps"] == 0
        assert metrics["avg_step_time_ms"] == 0

    def test_analyze_complete_structure(self, analyzer, mock_execution_result, test_metadata):
        """Test complete result structure"""
        result = analyzer.analyze(mock_execution_result, test_metadata)
        
        # Check all required fields
        assert hasattr(result, "success")
        assert hasattr(result, "test_name")
        assert hasattr(result, "duration")
        assert hasattr(result, "steps_executed")
        assert hasattr(result, "report")
        assert hasattr(result, "token_usage")
        assert hasattr(result, "metrics")
        assert hasattr(result, "provider")
        assert hasattr(result, "model")
        assert hasattr(result, "browser")
        assert hasattr(result, "error")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "environment")
        
        # Check nested structures
        assert result.execution_time.start is not None
        assert result.execution_time.end is not None
        assert result.execution_time.duration_seconds == 5.0
        assert "total_steps" in result.metrics
        assert "execution_time_ms" in result.metrics

    def test_analyze_with_error(self, analyzer, test_metadata):
        """Test analyzing execution with error"""
        execution_result = ExecutionResult(
            steps=[],
            final_response=None,
            duration=0.5,
            success=False,
        )
        
        metadata = test_metadata.copy()
        metadata["error"] = "Connection timeout"
        
        result = analyzer.analyze(execution_result, metadata)
        
        assert result.success is False
        assert result.error == "Connection timeout"

    def test_analyze_environment_info(self, analyzer, mock_execution_result):
        """Test environment information is captured"""
        metadata = {
            "test_name": "Test",
            "token_optimization_enabled": True,
            "compression_level": "high",
        }
        
        result = analyzer.analyze(mock_execution_result, metadata)
        
        assert result.environment == {
            "token_optimization_enabled": True,
            "compression_level": "high",
        }

    def test_success_patterns_case_insensitive(self, analyzer):
        """Test success patterns are case insensitive"""
        report = """# Test Execution Report
OVERALL STATUS: PASSED
Test Passed Successfully"""
        
        assert analyzer.check_success(report) is True

    def test_has_valid_report(self, analyzer):
        """Test report validation"""
        valid_report = "# Test Execution Report\nContent here"
        invalid_report = "Random content without proper header"
        
        assert analyzer._has_valid_report(valid_report) is True
        assert analyzer._has_valid_report(invalid_report) is False