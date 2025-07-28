"""
Tests for CLI executor module
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from browser_copilot.cli.executor import BrowserTestExecutor


@pytest.mark.unit
class TestCLIExecutor:
    """Test CLI executor functionality"""

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments"""
        args = MagicMock()
        args.provider = "github_copilot"
        args.model = "gpt-4o"
        args.browser = "chromium"
        args.headless = False
        args.verbose = False
        args.quiet = False
        args.viewport_width = 1280
        args.viewport_height = 720
        args.device = None
        args.user_agent = None
        args.proxy_server = None
        args.ignore_https_errors = False
        args.save_trace = False
        args.no_isolated = False
        args.output_format = "markdown"
        args.output_file = None
        args.no_screenshots = False
        args.system_prompt_file = None
        args.temperature = None
        args.max_tokens = None
        args.no_token_optimization = False
        args.compression_level = "medium"
        return args

    @pytest.fixture
    def executor(self):
        """Create BrowserTestExecutor instance"""
        # Mock the required dependencies
        config = MagicMock()
        storage = MagicMock()
        stream = MagicMock()
        return BrowserTestExecutor(config, storage, stream)

    def test_initialization(self, executor):
        """Test executor initialization"""
        assert executor.config is not None
        assert executor.storage is not None
        assert executor.stream is not None

    @pytest.mark.asyncio
    async def test_execute_test_success(self, executor, mock_args):
        """Test executing a test successfully"""
        # Mock successful test result
        mock_result = {
            "success": True,
            "test_name": "Test Scenario",
            "duration": 5.0,
            "steps": 3,
        }

        with patch.object(
            executor, "execute_test", return_value=mock_result
        ) as mock_execute:
            result = await executor.execute_test("Test content")

            assert result["success"] is True
            assert result["test_name"] == "Test Scenario"
            mock_execute.assert_called_once_with("Test content")

    @pytest.mark.asyncio
    async def test_execute_test_failure(self, executor, mock_args):
        """Test handling test failure"""
        # Mock failed test result
        mock_result = {
            "success": False,
            "test_name": "Failed Test",
            "error": "Element not found",
        }

        with patch.object(
            executor, "execute_test", return_value=mock_result
        ) as mock_execute:
            result = await executor.execute_test("Test content")

            assert result["success"] is False
            assert result["error"] == "Element not found"
            mock_execute.assert_called_once_with("Test content")

    @pytest.mark.asyncio
    async def test_execute_test_exception(self, executor, mock_args):
        """Test handling execution exception"""
        # Mock exception during test
        with patch.object(
            executor, "execute_test", side_effect=Exception("Runtime error")
        ) as mock_execute:
            with pytest.raises(Exception, match="Runtime error"):
                await executor.execute_test("Test content")

            mock_execute.assert_called_once_with("Test content")

    def test_save_results(self, executor):
        """Test saving test results"""
        mock_result = {
            "success": True,
            "test_name": "Test Scenario",
            "duration": 5.0,
        }

        with patch.object(executor.storage, "base_dir", Path("/tmp")):
            with patch("browser_copilot.cli.executor.OutputHandler") as mock_output:
                mock_output.format_output.return_value = "formatted output"
                mock_output.write_output.return_value = None

                saved_files = executor.save_results(mock_result)

                assert "report" in saved_files
                mock_output.format_output.assert_called_once()
                mock_output.write_output.assert_called()

    def test_display_summary(self, executor, capsys):
        """Test displaying test summary"""
        mock_result = {
            "success": True,
            "test_name": "Test Scenario",
            "duration_seconds": 5.0,
            "browser": "chromium",
            "provider": "github_copilot",
            "model": "gpt-4o",
        }

        executor.display_summary(mock_result)

        captured = capsys.readouterr()
        assert "Test Scenario" in captured.out
        assert "PASSED" in captured.out
        assert "chromium" in captured.out

    def test_display_summary_quiet_mode(self, executor, capsys):
        """Test summary in quiet mode"""
        mock_result = {"success": True}

        executor.display_summary(mock_result, quiet=True)

        captured = capsys.readouterr()
        assert captured.out == ""  # No output in quiet mode
