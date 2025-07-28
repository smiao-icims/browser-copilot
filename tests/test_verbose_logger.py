"""
Tests for VerboseLogger
"""

import logging
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
from verbose_logger import VerboseLogger


@pytest.mark.unit
class TestVerboseLogger:
    """Test VerboseLogger functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir):
        """Set up test environment"""
        from storage_manager import StorageManager

        self.storage = StorageManager(base_dir=temp_dir)
        self.logger = VerboseLogger(storage_manager=self.storage)
        self.log_dir = self.storage.get_logs_dir()

        yield  # This allows the test to run

        # Teardown - close the logger
        self.logger.close()

    def test_initialization(self):
        """Test logger initialization"""
        assert self.log_dir.exists()
        assert self.logger.log_file.exists()
        assert self.logger.log_file.suffix == ".log"
        assert "browser_copilot_" in self.logger.log_file.name

    def test_log_step(self, caplog):
        """Test step logging"""
        self.logger.log_step(
            "navigation", "Navigate to homepage", {"url": "https://example.com"}
        )

        # Check log output
        assert "Navigate to homepage" in caplog.text

        # Check file output
        log_content = self.logger.log_file.read_text()
        assert "Navigate to homepage" in log_content
        assert "NAVIGATION" in log_content  # Logger outputs uppercase step types

    def test_log_levels(self, caplog):
        """Test different log levels"""
        self.logger.log_step("debug_step", "Debug message", level="DEBUG")
        self.logger.log_step("info_step", "Info message", level="INFO")
        self.logger.log_step("warning_step", "Warning message", level="WARNING")
        self.logger.log_error("error_type", "Error message")

        # All should appear in log output
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_log_tool_call(self, caplog):
        """Test tool call logging"""
        tool_params = {"selector": "button#submit"}
        tool_result = {"success": True}

        self.logger.log_tool_call("click", tool_params, tool_result, duration_ms=150.5)

        assert "Tool: click" in caplog.text
        assert "150.5ms" in caplog.text

    def test_log_token_usage(self, caplog):
        """Test token usage logging"""
        self.logger.log_token_usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=0.003,
        )

        assert "Tokens used" in caplog.text
        assert "150" in caplog.text
        assert "$0.003" in caplog.text

    def test_log_error(self, caplog):
        """Test error logging"""
        self.logger.log_error(
            "test_error",
            "Something went wrong",
            {"context": "During test execution"},
            recoverable=False,
        )

        assert "ERROR" in caplog.text
        assert "Something went wrong" in caplog.text
        assert "test_error" in caplog.text

    def test_log_screenshot(self, caplog, temp_dir):
        """Test screenshot logging"""
        screenshot_path = temp_dir / "screenshot.png"
        screenshot_path.write_text("fake image data")

        self.logger.log_screenshot(screenshot_path, "Login page screenshot")

        assert "Screenshot saved" in caplog.text
        assert "screenshot.png" in caplog.text
        assert "Login page screenshot" in caplog.text

    def test_get_execution_summary(self):
        """Test execution summary"""
        # Log some steps and tool calls
        self.logger.log_step("action", "Step 1")
        self.logger.log_step("action", "Step 2")
        self.logger.log_tool_call("click", {}, {"success": True})
        self.logger.log_error("test_error", "Test error")

        # Get summary
        summary = self.logger.get_execution_summary()

        assert summary["session_id"] == self.logger.session_id
        assert summary["log_file"] == str(self.logger.log_file)
        assert summary["steps"] == 2
        assert summary["tool_calls"] == 1

    def test_test_lifecycle(self, caplog):
        """Test full test lifecycle logging"""
        test_config = {"browser": "chromium", "headless": True}

        # Start test
        self.logger.log_test_start("test_login", test_config)

        # Log some steps
        self.logger.log_step("navigation", "Navigate to login page")
        self.logger.log_step("input", "Enter credentials")

        # Complete test
        self.logger.log_test_complete(True, 5.2, "Test passed successfully")

        assert "Starting test: test_login" in caplog.text
        assert "Test PASSED" in caplog.text
        assert "5.20 seconds" in caplog.text  # Logger formats with 2 decimal places

    def test_disable_console_output(self, temp_dir):
        """Test logger with console output disabled"""
        from storage_manager import StorageManager

        storage = StorageManager(base_dir=temp_dir)
        logger = VerboseLogger(storage_manager=storage, console_enabled=False)
        try:
            logger.log_step("test", "Should not print to console")

            # Check that logger has no console handler (StreamHandler to stdout)
            # FileHandler is a subclass of StreamHandler, so check for stdout specifically
            has_console_handler = any(
                isinstance(handler, logging.StreamHandler)
                and hasattr(handler, "stream")
                and handler.stream == sys.stdout
                for handler in logger.logger.handlers
            )
            assert not has_console_handler

            # But file should contain the message
            log_content = logger.log_file.read_text()
            assert "Should not print to console" in log_content
        finally:
            logger.close()

    def test_disable_file_output(self, temp_dir, caplog):
        """Test logger with file output disabled"""
        from storage_manager import StorageManager

        storage = StorageManager(base_dir=temp_dir)
        logger = VerboseLogger(storage_manager=storage, file_enabled=False)
        try:
            logger.log_step("test", "Console only")

            # Console should have output
            assert "Console only" in caplog.text

            # File should not exist since file logging is disabled
            # The log_file path is created but not written to
            if logger.log_file.exists():
                assert logger.log_file.stat().st_size == 0
        finally:
            logger.close()

    def test_unicode_handling(self):
        """Test handling of unicode characters"""
        unicode_text = "Test with emoji 🚀 and special chars: ñ, ü, 中文"
        self.logger.log_step("unicode_test", unicode_text)

        log_content = self.logger.log_file.read_text(encoding="utf-8")
        assert unicode_text in log_content
        assert "🚀" in log_content

    def test_write_execution_summary(self):
        """Test execution summary writing"""
        # Log some activities
        self.logger.log_step("step1", "First step")
        self.logger.log_tool_call("navigate", {"url": "test.com"}, {"success": True})
        self.logger.log_token_usage(100, 50, 150, 0.003)

        # Write summary (internal method)
        self.logger._write_execution_summary()

        log_content = self.logger.log_file.read_text()
        assert "EXECUTION SUMMARY" in log_content
        # The summary is in JSON format
        assert '"steps": 1' in log_content
        assert '"tool_calls": 1' in log_content

    def test_get_log_file_path(self):
        """Test getting log file path"""
        path = self.logger.get_log_file_path()
        assert path == self.logger.log_file
        assert path.exists()
