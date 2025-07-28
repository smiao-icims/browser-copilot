"""
Tests for InputHandler
"""

import io
import sys
from pathlib import Path

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from browser_copilot.io.input_handler import InputHandler


@pytest.mark.unit
class TestInputHandler:
    """Test InputHandler functionality"""

    def test_read_from_file(self, temp_dir):
        """Test reading input from a file"""
        # Create test file
        test_file = temp_dir / "test_input.md"
        test_content = "# Test Scenario\n\n1. Navigate to example.com\n2. Click button"
        test_file.write_text(test_content)

        result = InputHandler.read_from_file(test_file)
        assert result == test_content

    def test_read_from_file_with_whitespace(self, temp_dir):
        """Test reading file strips whitespace"""
        test_file = temp_dir / "whitespace.md"
        test_file.write_text("  \n  Test content  \n  ")

        result = InputHandler.read_from_file(test_file)
        assert result == "Test content"

    def test_read_from_stdin(self, monkeypatch):
        """Test reading input from stdin"""
        test_content = "Test input from stdin"

        # Mock stdin
        monkeypatch.setattr("sys.stdin", io.StringIO(test_content))

        result = InputHandler.read_from_stdin()
        assert result == test_content

    def test_read_from_stdin_interactive(self, monkeypatch, capsys):
        """Test reading from stdin in interactive mode"""
        test_content = "Interactive test"

        # Mock stdin as terminal
        mock_stdin = io.StringIO(test_content)
        mock_stdin.isatty = lambda: True
        monkeypatch.setattr("sys.stdin", mock_stdin)

        result = InputHandler.read_from_stdin()
        assert result == test_content

        # Check that prompt was displayed
        captured = capsys.readouterr()
        assert "Enter test scenario" in captured.out

    def test_read_from_stdin_empty(self, monkeypatch):
        """Test handling empty stdin input"""
        monkeypatch.setattr("sys.stdin", io.StringIO(""))

        with pytest.raises(ValueError) as exc_info:
            InputHandler.read_from_stdin()
        assert "No test scenario provided" in str(exc_info.value)

    def test_read_from_stdin_cancelled(self, monkeypatch):
        """Test handling KeyboardInterrupt"""
        mock_stdin = io.StringIO()
        mock_stdin.read = lambda: (_ for _ in ()).throw(KeyboardInterrupt())
        monkeypatch.setattr("sys.stdin", mock_stdin)

        with pytest.raises(ValueError) as exc_info:
            InputHandler.read_from_stdin()
        assert "cancelled" in str(exc_info.value)

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        with pytest.raises(FileNotFoundError) as exc_info:
            InputHandler.read_from_file(Path("non_existent_file.md"))
        assert "Test scenario file not found" in str(exc_info.value)

    def test_file_read_error(self, temp_dir, monkeypatch):
        """Test handling file read errors"""
        test_file = temp_dir / "error.md"
        test_file.write_text("content")

        # Mock open to raise an exception
        def mock_open(*args, **kwargs):
            raise PermissionError("Access denied")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(OSError) as exc_info:
            InputHandler.read_from_file(test_file)
        assert "Failed to read test scenario file" in str(exc_info.value)

    def test_empty_file(self, temp_dir):
        """Test reading empty file"""
        test_file = temp_dir / "empty.md"
        test_file.write_text("")

        result = InputHandler.read_from_file(test_file)
        assert result == ""

    def test_validate_scenario_valid(self):
        """Test scenario validation with valid content"""
        valid_scenario = """
        # Login Test
        1. Navigate to example.com
        2. Click login button
        3. Enter username
        4. Verify dashboard appears
        """

        warnings = InputHandler.validate_scenario(valid_scenario)
        assert len(warnings) == 0

    def test_validate_scenario_too_short(self):
        """Test validation of too short scenario"""
        warnings = InputHandler.validate_scenario("Short")
        assert any("too short" in w for w in warnings)

    def test_validate_scenario_json_format(self):
        """Test validation detects JSON format"""
        warnings = InputHandler.validate_scenario('{"test": "data"}')
        assert any("JSON" in w for w in warnings)

    def test_validate_scenario_xml_format(self):
        """Test validation detects XML format"""
        warnings = InputHandler.validate_scenario("<test>data</test>")
        assert any("XML" in w for w in warnings)

    def test_validate_scenario_no_keywords(self):
        """Test validation detects lack of test keywords"""
        warnings = InputHandler.validate_scenario(
            "This is just some random text without any actions"
        )
        assert any("actionable test steps" in w for w in warnings)
