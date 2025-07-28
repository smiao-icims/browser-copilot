"""
Tests for StreamHandler
"""

import sys
from pathlib import Path

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from browser_copilot.io.stream_handler import StreamHandler


@pytest.mark.unit
class TestStreamHandler:
    """Test StreamHandler functionality"""

    def test_initialization(self):
        """Test handler initialization"""
        handler = StreamHandler()
        assert handler.verbose is False
        assert handler.quiet is False
        assert handler._buffer == []

        verbose_handler = StreamHandler(verbose=True)
        assert verbose_handler.verbose is True

        quiet_handler = StreamHandler(quiet=True)
        assert quiet_handler.quiet is True

    def test_write_info(self, capsys):
        """Test writing info messages"""
        handler = StreamHandler()
        handler.write("Test info message", "info")

        captured = capsys.readouterr()
        assert "[INFO] Test info message" in captured.out

    def test_write_error(self, capsys):
        """Test writing error messages"""
        handler = StreamHandler(quiet=True)  # Even in quiet mode
        handler.write("Test error message", "error")

        captured = capsys.readouterr()
        assert "[ERROR] Test error message" in captured.out

    def test_write_debug_verbose(self, capsys):
        """Test debug messages in verbose mode"""
        handler = StreamHandler(verbose=True)
        handler.write("Test debug message", "debug")

        captured = capsys.readouterr()
        assert "[DEBUG] Test debug message" in captured.out

    def test_write_debug_normal(self, capsys):
        """Test debug messages in normal mode (should not display)"""
        handler = StreamHandler(verbose=False)
        handler.write("Test debug message", "debug")

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_mode(self, capsys):
        """Test quiet mode suppresses non-error messages"""
        handler = StreamHandler(quiet=True)

        handler.write("Info message", "info")
        handler.write("Debug message", "debug")
        handler.write("Warning message", "warning")
        handler.write("Error message", "error")

        captured = capsys.readouterr()
        assert "Info message" not in captured.out
        assert "Debug message" not in captured.out
        assert "Warning message" not in captured.out
        assert "[ERROR] Error message" in captured.out

    def test_buffer_functionality(self):
        """Test message buffering"""
        handler = StreamHandler()

        handler.write("Message 1", "info")
        handler.write("Message 2", "debug")
        handler.write("Message 3", "error")

        buffer = handler.get_buffer()
        assert len(buffer) == 3
        assert buffer[0][1] == "info"
        assert buffer[0][2] == "Message 1"
        assert buffer[1][1] == "debug"
        assert buffer[1][2] == "Message 2"
        assert buffer[2][1] == "error"
        assert buffer[2][2] == "Message 3"

    def test_clear_buffer(self):
        """Test clearing the buffer"""
        handler = StreamHandler()

        handler.write("Test message", "info")
        assert len(handler.get_buffer()) == 1

        handler.clear_buffer()
        assert len(handler.get_buffer()) == 0

    def test_unknown_level(self):
        """Test handling unknown log level"""
        handler = StreamHandler()
        handler.write("Unknown level message", "unknown")

        # Unknown levels are still buffered
        buffer = handler.get_buffer()
        assert len(buffer) == 1
        assert buffer[0][1] == "unknown"
        assert buffer[0][2] == "Unknown level message"

    def test_buffer_immutability(self):
        """Test that get_buffer returns a copy"""
        handler = StreamHandler()
        handler.write("Test", "info")

        buffer1 = handler.get_buffer()
        buffer1.clear()  # Clear the returned buffer

        buffer2 = handler.get_buffer()
        assert len(buffer2) == 1  # Original buffer unchanged
