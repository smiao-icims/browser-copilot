"""
Tests for VerboseLogger
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_pilot"))
from verbose_logger import VerboseLogger


@pytest.mark.unit
class TestVerboseLogger:
    """Test VerboseLogger functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir):
        """Set up test environment"""
        self.log_dir = temp_dir / "logs"
        self.log_dir.mkdir()
        self.logger = VerboseLogger(str(self.log_dir))

    def test_initialization(self):
        """Test logger initialization"""
        assert self.logger.log_dir.exists()
        assert self.logger.log_file.exists()
        assert self.logger.log_file.suffix == ".log"
        assert "browser_pilot_" in self.logger.log_file.name

    def test_log_message(self, capsys):
        """Test basic log message"""
        self.logger.log("Test message", level="INFO")

        # Check console output
        captured = capsys.readouterr()
        assert "Test message" in captured.out

        # Check file output
        log_content = self.logger.log_file.read_text()
        assert "Test message" in log_content
        assert "INFO" in log_content

    def test_log_levels(self, capsys):
        """Test different log levels"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in levels:
            self.logger.log(f"Test {level}", level=level)

        captured = capsys.readouterr()
        for level in levels:
            assert level in captured.out

    def test_log_with_data(self):
        """Test logging with additional data"""
        test_data = {"action": "click", "element": "button#submit", "result": "success"}

        self.logger.log("Action performed", data=test_data)

        log_content = self.logger.log_file.read_text()
        assert "Action performed" in log_content
        # Data should be JSON formatted in the file
        assert json.dumps(test_data, indent=2) in log_content

    def test_log_step(self, capsys):
        """Test step logging"""
        self.logger.log_step(1, "Navigate to homepage")
        self.logger.log_step(2, "Click login button")

        captured = capsys.readouterr()
        assert "Step 1: Navigate to homepage" in captured.out
        assert "Step 2: Click login button" in captured.out

    def test_log_error(self, capsys):
        """Test error logging"""
        error = Exception("Test error message")
        self.logger.log_error(error, context="During test execution")

        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Test error message" in captured.out
        assert "During test execution" in captured.out

        # Check file contains full error details
        log_content = self.logger.log_file.read_text()
        assert "Exception: Test error message" in log_content

    def test_log_telemetry(self):
        """Test telemetry logging"""
        telemetry_data = {
            "tokens_used": 1000,
            "cost": 0.02,
            "duration": 5.5,
            "model": "gpt-4",
        }

        self.logger.log_telemetry(telemetry_data)

        log_content = self.logger.log_file.read_text()
        assert "TELEMETRY" in log_content
        assert "tokens_used" in log_content
        assert "1000" in log_content

    def test_summary(self, capsys):
        """Test execution summary"""
        # Log some steps
        self.logger.log_step(1, "Step 1")
        self.logger.log_step(2, "Step 2")
        self.logger.log_error(Exception("Test error"))

        # Generate summary
        summary = self.logger.summary()

        captured = capsys.readouterr()
        assert "Execution Summary" in captured.out
        assert "Total steps: 2" in captured.out
        assert "Errors: 1" in captured.out
        assert "Log file:" in captured.out

        assert summary["total_steps"] == 2
        assert summary["errors"] == 1
        assert summary["log_file"] == str(self.logger.log_file)

    def test_context_manager(self, capsys):
        """Test using logger as context manager"""
        with VerboseLogger(str(self.log_dir)) as logger:
            logger.log("Inside context")

        captured = capsys.readouterr()
        assert "Starting Browser Pilot execution" in captured.out
        assert "Inside context" in captured.out
        assert "Execution Summary" in captured.out

    def test_filename_sanitization(self):
        """Test log filename sanitization"""
        # Create logger with test name containing special characters
        test_logger = VerboseLogger(
            str(self.log_dir), test_name="test/with:special*chars"
        )

        # Filename should have special chars replaced
        assert "/" not in test_logger.log_file.name
        assert ":" not in test_logger.log_file.name
        assert "*" not in test_logger.log_file.name

    def test_langchain_callback_methods(self):
        """Test LangChain callback handler methods"""
        # Test on_llm_start
        self.logger.on_llm_start(
            serialized={"name": "test_llm"},
            prompts=["Test prompt"],
            run_id="test_run_123",
        )

        # Test on_llm_end
        from unittest.mock import MagicMock

        response = MagicMock()
        response.generations = [[MagicMock(text="Test response")]]
        response.llm_output = {"token_usage": {"total_tokens": 100}}

        self.logger.on_llm_end(response, run_id="test_run_123")

        log_content = self.logger.log_file.read_text()
        assert "LLM Start" in log_content
        assert "test_llm" in log_content
        assert "Test prompt" in log_content
        assert "LLM End" in log_content
        assert "100" in log_content

    def test_on_chain_callbacks(self):
        """Test chain execution callbacks"""
        # Test on_chain_start
        self.logger.on_chain_start(
            serialized={"name": "test_chain"},
            inputs={"input": "test"},
            run_id="chain_123",
        )

        # Test on_chain_end
        self.logger.on_chain_end(outputs={"output": "result"}, run_id="chain_123")

        log_content = self.logger.log_file.read_text()
        assert "Chain Start" in log_content
        assert "test_chain" in log_content
        assert "Chain End" in log_content

    def test_on_tool_callbacks(self):
        """Test tool execution callbacks"""
        # Test on_tool_start
        self.logger.on_tool_start(
            serialized={"name": "browser_action"},
            input_str="click button",
            run_id="tool_123",
        )

        # Test on_tool_end
        self.logger.on_tool_end(output="Success", run_id="tool_123")

        log_content = self.logger.log_file.read_text()
        assert "Tool Start" in log_content
        assert "browser_action" in log_content
        assert "click button" in log_content
        assert "Tool End" in log_content
        assert "Success" in log_content

    def test_error_callbacks(self):
        """Test error handling callbacks"""
        error = Exception("Test error")

        # Test on_llm_error
        self.logger.on_llm_error(error, run_id="error_123")

        # Test on_chain_error
        self.logger.on_chain_error(error, run_id="error_456")

        # Test on_tool_error
        self.logger.on_tool_error(error, run_id="error_789")

        log_content = self.logger.log_file.read_text()
        assert log_content.count("ERROR") >= 3
        assert log_content.count("Test error") >= 3

    def test_concurrent_logging(self):
        """Test thread-safe concurrent logging"""
        import threading

        def log_messages(thread_id):
            for i in range(10):
                self.logger.log(f"Thread {thread_id} - Message {i}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Check all messages were logged
        log_content = self.logger.log_file.read_text()
        for i in range(5):
            for j in range(10):
                assert f"Thread {i} - Message {j}" in log_content
