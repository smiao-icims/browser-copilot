"""
Tests for CLI utility functions
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent))
from browser_copilot.cli.utils import (
    format_duration,
    format_token_count,
    get_status_emoji,
    normalize_test_name_for_path,
    read_system_prompt,
)


@pytest.mark.unit
class TestCLIUtils:
    """Test CLI utility functions"""

    def test_normalize_test_name_for_path(self):
        """Test test name normalization"""
        assert normalize_test_name_for_path("Test Name") == "test-name"
        assert normalize_test_name_for_path("Test@#$Name") == "testname"
        assert normalize_test_name_for_path("Test  Name") == "test-name"
        assert normalize_test_name_for_path("---Test---") == "test"
        assert normalize_test_name_for_path("") == "browser-test"
        assert normalize_test_name_for_path("a" * 60) == "a" * 50
        assert normalize_test_name_for_path("Test-Name-123") == "test-name-123"
        assert normalize_test_name_for_path("UPPERCASE") == "uppercase"
        assert (
            normalize_test_name_for_path("with spaces and @#$ special")
            == "with-spaces-and-special"
        )

    def test_read_system_prompt(self, temp_dir):
        """Test reading system prompt from file"""
        # Test with None
        assert read_system_prompt(None) is None

        # Test with valid file
        prompt_file = temp_dir / "prompt.txt"
        prompt_content = "This is a test prompt\nWith multiple lines"
        prompt_file.write_text(prompt_content)
        assert read_system_prompt(str(prompt_file)) == prompt_content

        # Test with non-existent file
        with pytest.raises(OSError) as exc_info:
            read_system_prompt("/nonexistent/file.txt")
        assert "Failed to read system prompt file" in str(exc_info.value)

    def test_format_duration(self):
        """Test duration formatting"""
        # Seconds
        assert format_duration(0.5) == "0.5s"
        assert format_duration(30) == "30.0s"
        assert format_duration(59.9) == "59.9s"

        # Minutes
        assert format_duration(60) == "1m 0.0s"
        assert format_duration(90) == "1m 30.0s"
        assert format_duration(125.5) == "2m 5.5s"
        assert format_duration(3599) == "59m 59.0s"

        # Hours
        assert format_duration(3600) == "1h 0m"
        assert format_duration(3665) == "1h 1m"
        assert format_duration(7200) == "2h 0m"
        assert format_duration(10800) == "3h 0m"

    def test_format_token_count(self):
        """Test token count formatting"""
        assert format_token_count(0) == "0"
        assert format_token_count(100) == "100"
        assert format_token_count(1000) == "1,000"
        assert format_token_count(10000) == "10,000"
        assert format_token_count(1000000) == "1,000,000"

    def test_get_status_emoji(self):
        """Test status emoji selection"""
        assert get_status_emoji(True) == "✅"
        assert get_status_emoji(False) == "❌"
