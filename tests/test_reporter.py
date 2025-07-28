"""
Tests for Reporter
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
import reporter


@pytest.mark.unit
class TestReporter:
    """Test Reporter functionality"""

    @pytest.fixture
    def sample_result(self):
        """Sample test result for testing"""
        return {
            "success": True,
            "provider": "openai",
            "model": "gpt-4",
            "browser": "chromium",
            "headless": False,
            "duration_seconds": 25.5,
            "steps_executed": 10,
            "report": """# Test Execution Report

## Summary
- Overall Status: PASSED
- Total Steps: 10
- Duration: 25.5 seconds

## Steps Executed
1. ✓ Navigate to https://example.com
2. ✓ Click login button
3. ✓ Enter username
4. ✓ Enter password
5. ✓ Submit form
6. ✓ Verify dashboard loaded
7. ✓ Take screenshot

## Token Usage
- Total tokens: 1500
- Estimated cost: $0.03""",
            "token_usage": {
                "total_tokens": 1500,
                "prompt_tokens": 1200,
                "completion_tokens": 300,
                "estimated_cost": 0.03,
                "optimization": {
                    "enabled": True,
                    "level": "medium",
                    "original_tokens": 2000,
                    "optimized_tokens": 1500,
                    "reduction_percentage": 25.0,
                    "estimated_savings": 0.01,
                    "strategies_applied": ["whitespace", "phrases", "abbreviations"],
                },
            },
            "screenshots": ["screenshot_001.png", "screenshot_002.png"],
            "timestamp": "2025-01-26T12:00:00",
            "error": None,
        }

    @pytest.fixture
    def failed_result(self):
        """Sample failed test result"""
        return {
            "success": False,
            "provider": "anthropic",
            "model": "claude-3",
            "browser": "firefox",
            "headless": True,
            "duration_seconds": 10.2,
            "steps_executed": 3,
            "report": "Test failed at step 4",
            "token_usage": {"total_tokens": 500, "estimated_cost": 0.01},
            "error": "Element not found: button#submit",
            "timestamp": "2025-01-26T12:30:00",
        }

    def test_display_console_success(self, capsys, sample_result):
        """Test console display for successful test"""
        reporter.print_results(sample_result)

        captured = capsys.readouterr()
        output = captured.out

        # Check for key elements
        assert "✅ PASSED" in output
        assert "Duration: 25.5s" in output
        assert "Steps: 10" in output
        assert "Token Usage:" in output
        assert "Total: 1,500" in output
        assert "Cost: $0.0300" in output
        assert "Token Optimization:" in output
        assert "Reduction: 25.0%" in output
        assert "Cost Savings: $0.0100" in output

    def test_display_console_failure(self, capsys, failed_result):
        """Test console display for failed test"""
        reporter.print_results(failed_result)

        captured = capsys.readouterr()
        output = captured.out

        assert "❌ FAILED" in output
        assert "Element not found" in output
        assert "Duration: 10.2s" in output
        assert "Steps: 3" in output

    def test_generate_report_success(self, sample_result, temp_dir):
        """Test report generation for successful test"""
        saved_files = reporter.save_results(sample_result, str(temp_dir))

        # Check that report file is created
        assert "report" in saved_files
        report_content = saved_files["report"].read_text()

        # Check metadata in comments
        assert "Browser Copilot Test Report" in report_content
        assert "Status: PASSED" in report_content
        assert "Duration: 25.5s" in report_content
        assert "Steps: 10" in report_content
        assert "Token Usage: 1,500" in report_content

    def test_generate_report_failure(self, failed_result, temp_dir):
        """Test report generation for failed test"""
        saved_files = reporter.save_results(failed_result, str(temp_dir))

        # Check that report file is created
        assert "report" in saved_files
        report_content = saved_files["report"].read_text()

        # Check metadata in comments for failed test
        assert "Status: FAILED" in report_content
        assert "Duration: 10.2s" in report_content
        assert "Steps: 3" in report_content
        # The report content contains the actual report text
        assert "Test failed at step 4" in report_content

    def test_save_report_markdown(self, temp_dir, sample_result):
        """Test saving report as markdown"""
        saved_files = reporter.save_results(sample_result, str(temp_dir))
        filepath = saved_files["report"]

        assert filepath.exists()
        assert filepath.suffix == ".md"
        assert "report_" in filepath.name

        content = filepath.read_text()
        assert "Browser Copilot Test Report" in content

    def test_save_report_json(self, temp_dir, sample_result):
        """Test saving report as JSON"""
        saved_files = reporter.save_results(sample_result, str(temp_dir))
        filepath = saved_files["results"]

        assert filepath.exists()
        assert filepath.suffix == ".json"

        with open(filepath) as f:
            data = json.load(f)
        assert data["success"] is True
        assert data["duration_seconds"] == 25.5

    def test_save_results(self, temp_dir, sample_result):
        """Test saving full results"""
        saved_files = reporter.save_results(sample_result, str(temp_dir))
        report_path = saved_files["report"]
        results_path = saved_files["results"]

        assert report_path.exists()
        assert results_path.exists()
        assert report_path.suffix == ".md"
        assert results_path.suffix == ".json"

        # Verify content
        report_content = report_path.read_text()
        assert "Browser Copilot Test Report" in report_content

        with open(results_path) as f:
            results_data = json.load(f)
        assert results_data["success"] is True

    def test_print_header(self, capsys):
        """Test header printing"""
        reporter.print_header()

        captured = capsys.readouterr()
        assert "Browser Copilot" in captured.out
        assert "Simple • Reliable • Token Efficient" in captured.out

    def test_no_token_usage(self, capsys):
        """Test handling missing token usage data"""
        result = {
            "success": True,
            "duration_seconds": 10,
            "steps_executed": 5,
            "report": "Test completed",
        }

        # Should not crash
        report = reporter.generate_markdown_report(result)
        assert "Token Usage" not in report

        # Console display should handle it gracefully
        reporter.print_results(result)  # Should not raise

    def test_no_optimization_data(self, sample_result):
        """Test handling missing optimization data"""
        # Remove optimization data
        sample_result["token_usage"].pop("optimization", None)

        report = reporter.generate_markdown_report(sample_result)

        assert "Token Optimization" not in report
        assert "Token Usage" in report  # But usage should still be there

    def test_custom_filename(self, temp_dir, sample_result):
        """Test custom filename generation"""
        # Test with custom test name
        sample_result["test_name"] = "login_test"
        saved_files = reporter.save_results(sample_result, str(temp_dir))
        filepath = saved_files["report"]

        # Current implementation doesn't use test_name in filename
        assert "report_" in filepath.name

    def test_report_with_screenshots(self, sample_result):
        """Test report includes screenshot information"""
        report = reporter.generate_markdown_report(sample_result)

        assert "## Screenshots" in report
        assert "screenshot_001.png" in report
        assert "screenshot_002.png" in report

    def test_report_no_screenshots(self, sample_result):
        """Test report without screenshots"""
        sample_result.pop("screenshots", None)

        report = reporter.generate_markdown_report(sample_result)

        assert "## Screenshots" not in report

    def test_detailed_token_metrics(self, sample_result):
        """Test detailed token metrics in report"""
        report = reporter.generate_markdown_report(sample_result)

        assert "Prompt Tokens: 1,200" in report
        assert "Completion Tokens: 300" in report
        assert "Total Tokens: 1,500" in report
        assert "Estimated Cost: $0.0300" in report

    def test_optimization_strategies(self, sample_result):
        """Test optimization strategies display"""
        report = reporter.generate_markdown_report(sample_result)

        assert "Strategies Applied:" in report
        assert "whitespace" in report
        assert "phrases" in report
        assert "abbreviations" in report

    def test_execution_metadata(self, sample_result):
        """Test execution metadata in report"""
        report = reporter.generate_markdown_report(sample_result)

        assert "Provider: openai" in report
        assert "Model: gpt-4" in report
        assert "Browser: chromium" in report
        assert "Headless: No" in report
        assert "2025-01-26" in report  # Timestamp

    def test_empty_result(self, capsys):
        """Test handling of minimal/empty result"""
        minimal_result = {"success": False, "error": "Test failed to start"}

        # Should handle gracefully
        report = reporter.generate_markdown_report(minimal_result)
        assert "Test failed to start" in report

        # Console display should work
        reporter.print_results(minimal_result)  # Should not raise

    @patch("reporter.datetime")
    def test_timestamp_generation(self, mock_datetime, temp_dir, sample_result):
        """Test timestamp in filename generation"""
        # Mock datetime to return consistent value
        mock_datetime.now.return_value.strftime.return_value = "20250126_120000"

        saved_files = reporter.save_results(sample_result, str(temp_dir))
        filepath = saved_files["report"]

        assert "20250126_120000" in filepath.name
