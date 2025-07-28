"""
Tests for IO Handlers
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_pilot"))
from io_handlers import InputHandler, OutputHandler


@pytest.mark.unit
class TestInputHandler:
    """Test InputHandler functionality"""

    def test_read_from_file(self, temp_dir):
        """Test reading input from a file"""
        # Create test file
        test_file = temp_dir / "test_input.md"
        test_content = "# Test Scenario\n\n1. Navigate to example.com\n2. Click button"
        test_file.write_text(test_content)

        handler = InputHandler()
        result = handler.read(str(test_file))

        assert result == test_content

    def test_read_from_stdin(self, monkeypatch):
        """Test reading input from stdin"""
        test_content = "Test input from stdin"

        # Mock stdin
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO(test_content))

        handler = InputHandler()
        result = handler.read("-")

        assert result == test_content

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        handler = InputHandler()

        with pytest.raises(FileNotFoundError):
            handler.read("non_existent_file.md")

    def test_empty_file(self, temp_dir):
        """Test reading empty file"""
        test_file = temp_dir / "empty.md"
        test_file.write_text("")

        handler = InputHandler()
        result = handler.read(str(test_file))

        assert result == ""


@pytest.mark.unit
class TestOutputHandler:
    """Test OutputHandler functionality"""

    def test_format_json(self):
        """Test JSON output formatting"""
        handler = OutputHandler()

        test_data = {"success": True, "steps": 5, "duration": 10.5}

        result = handler.format(test_data, "json")
        parsed = json.loads(result)

        assert parsed == test_data

    def test_format_yaml(self):
        """Test YAML output formatting"""
        handler = OutputHandler()

        test_data = {"success": True, "steps": 5, "duration": 10.5}

        result = handler.format(test_data, "yaml")
        parsed = yaml.safe_load(result)

        assert parsed == test_data

    def test_format_xml(self):
        """Test XML output formatting"""
        handler = OutputHandler()

        test_data = {"success": True, "steps": 5, "error": None}

        result = handler.format(test_data, "xml")

        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert "<result>" in result
        assert "<success>True</success>" in result
        assert "<steps>5</steps>" in result

    def test_format_junit(self):
        """Test JUnit XML output formatting"""
        handler = OutputHandler()

        test_data = {
            "success": True,
            "test_name": "test_scenario",
            "duration_seconds": 10.5,
            "error": None,
        }

        result = handler.format(test_data, "junit")

        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert "<testsuites>" in result
        assert "<testsuite" in result
        assert "<testcase" in result
        assert 'name="test_scenario"' in result

    def test_format_html(self):
        """Test HTML output formatting"""
        handler = OutputHandler()

        test_data = {
            "success": True,
            "report": "# Test Report\n\n## Results\n- Status: PASSED",
        }

        result = handler.format(test_data, "html")

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "<h1>Test Report</h1>" in result
        assert "Status: PASSED" in result

    def test_format_markdown(self):
        """Test Markdown output formatting"""
        handler = OutputHandler()

        test_data = {
            "success": True,
            "report": "Test results",
            "steps_executed": 5,
            "duration_seconds": 10.5,
        }

        result = handler.format(test_data, "markdown")

        assert "# Browser Pilot Test Results" in result
        assert "**Status:** ✅ Success" in result
        assert "**Steps Executed:** 5" in result
        assert "**Duration:** 10.5 seconds" in result

    def test_write_to_file(self, temp_dir):
        """Test writing output to file"""
        handler = OutputHandler()

        test_data = {"test": "data"}
        output_file = temp_dir / "output.json"

        handler.write(test_data, "json", str(output_file))

        assert output_file.exists()
        with open(output_file) as f:
            parsed = json.load(f)
        assert parsed == test_data

    def test_write_to_stdout(self, capsys):
        """Test writing output to stdout"""
        handler = OutputHandler()

        test_data = {"test": "data"}
        handler.write(test_data, "json", None)

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == test_data

    def test_invalid_format(self):
        """Test handling of invalid output format"""
        handler = OutputHandler()

        with pytest.raises(ValueError, match="Unsupported output format"):
            handler.format({"test": "data"}, "invalid_format")

    def test_xml_special_characters(self):
        """Test XML formatting with special characters"""
        handler = OutputHandler()

        test_data = {
            "text": "Test & < > \" ' characters",
            "url": "https://example.com?param=value&other=test",
        }

        result = handler.format(test_data, "xml")

        # Check proper escaping
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result or "'" in result

    def test_junit_with_failure(self):
        """Test JUnit format with test failure"""
        handler = OutputHandler()

        test_data = {
            "success": False,
            "test_name": "failed_test",
            "duration_seconds": 5.0,
            "error": "Test failed: Element not found",
        }

        result = handler.format(test_data, "junit")

        assert "<failure" in result
        assert "Element not found" in result
        assert 'failures="1"' in result
