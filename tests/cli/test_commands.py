"""
Tests for CLI command handlers
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from browser_copilot.cli.commands import (
    run_cleanup_command,
    run_config_command,
    run_storage_info_command,
    run_test_command,
)


@pytest.mark.unit
class TestCLICommands:
    """Test CLI command functions"""

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments"""
        args = MagicMock()
        args.cleanup_days = 7
        args.config_file = None
        args.verbose = False
        args.quiet = False
        args.test_scenario = "test.md"
        args.provider = "github_copilot"
        args.model = "gpt-4o"
        return args

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_cleanup_command(self, mock_storage, mock_args):
        """Test cleanup command execution"""
        mock_args.cleanup_days = 14
        mock_args.storage_info = False

        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.cleanup_old_logs.return_value = 3
        mock_storage_instance.cleanup_old_files.return_value = 2
        mock_storage_instance.get_cache_dir.return_value = "/cache"
        mock_storage_instance.get_screenshots_dir.return_value = "/screenshots"

        result = await run_cleanup_command(mock_args)

        assert result == 0  # Success
        mock_storage_instance.cleanup_old_logs.assert_called_once_with(days=14)
        assert mock_storage_instance.cleanup_old_files.call_count == 2

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_cleanup_command_error(self, mock_storage, mock_args, capsys):
        """Test cleanup command with error"""
        mock_storage.side_effect = Exception("Storage error")

        result = await run_cleanup_command(mock_args)

        assert result == 1  # Error
        captured = capsys.readouterr()
        assert "Storage error" in captured.err

    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.run_config_wizard")
    def test_run_config_command(self, mock_wizard, mock_config, mock_args):
        """Test config command execution"""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_wizard.return_value = True  # Successful completion

        result = run_config_command(mock_args)

        assert result == 0  # Success
        mock_wizard.assert_called_once()

    @patch("browser_copilot.cli.commands.run_config_wizard")
    def test_run_config_command_error(self, mock_wizard, mock_args, capsys):
        """Test config command with error"""
        mock_wizard.side_effect = Exception("Config error")

        result = run_config_command(mock_args)

        assert result == 1  # Error
        captured = capsys.readouterr()
        assert "Configuration failed" in captured.out

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_storage_info_command(self, mock_storage, mock_args, capsys):
        """Test storage info command execution"""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.get_storage_info.return_value = {
            "total_size": 1024 * 1024 * 50,  # 50MB
            "report_count": 10,
            "oldest_report": "2024-01-01T10:00:00",
            "newest_report": "2024-01-10T15:30:00",
            "directories": {
                "logs": 1024 * 1024 * 10,
                "reports": 1024 * 1024 * 20,
                "screenshots": 1024 * 1024 * 15,
                "cache": 1024 * 1024 * 5,
            },
            "file_counts": {
                "logs": 100,
                "reports": 10,
                "screenshots": 50,
                "cache": 200,
                "settings": 5,
            },
        }
        # Configure _format_bytes to return formatted strings
        mock_storage_instance._format_bytes.side_effect = (
            lambda size: f"{size / (1024 * 1024):.2f} MB"
        )
        mock_storage_instance.base_dir = "/test/storage"

        result = await run_storage_info_command(mock_args)

        assert result == 0  # Success
        captured = capsys.readouterr()
        assert "Storage Information" in captured.out
        assert "50.00 MB" in captured.out
        assert "Reports: 10" in captured.out

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_storage_info_command_error(
        self, mock_storage, mock_args, capsys
    ):
        """Test storage info command with error"""
        mock_storage.side_effect = Exception("Storage error")

        result = await run_storage_info_command(mock_args)

        assert result == 1  # Error
        captured = capsys.readouterr()
        assert "Storage error" in captured.err

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.BrowserTestExecutor")
    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.StorageManager")
    @patch("browser_copilot.cli.commands.print_header")
    @patch("browser_copilot.cli.commands.InputHandler")
    async def test_run_test_command_success(
        self,
        mock_input,
        mock_print_header,
        mock_storage,
        mock_config,
        mock_executor,
        mock_args,
    ):
        """Test successful test command execution"""
        # Setup mocks
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance

        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance
        mock_executor_instance.execute_test = AsyncMock(return_value={"success": True})
        mock_executor_instance.save_results.return_value = {"report": "/test/report.md"}
        mock_executor_instance.display_summary.return_value = None

        # Mock InputHandler static methods
        mock_input.read_from_file.return_value = "Test content"
        mock_input.validate_scenario.return_value = []

        # Add missing args attributes
        mock_args.system_prompt = None
        mock_args.save_config = False
        mock_args.enhance_test = False
        mock_args.no_isolated = False
        mock_args.device = None
        mock_args.user_agent = None
        mock_args.proxy_server = None
        mock_args.proxy_bypass = None
        mock_args.ignore_https_errors = False
        mock_args.block_service_workers = False
        mock_args.save_trace = False
        mock_args.save_session = False
        mock_args.allowed_origins = None
        mock_args.blocked_origins = None
        mock_args.output_format = "markdown"
        mock_args.output_file = None

        result = await run_test_command(mock_args)

        assert result == 0  # Success
        mock_print_header.assert_called_once()
        mock_executor_instance.execute_test.assert_called_once()
        mock_executor_instance.save_results.assert_called_once()
        mock_executor_instance.display_summary.assert_called_once()

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.BrowserTestExecutor")
    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.StorageManager")
    @patch("browser_copilot.cli.commands.print_header")
    @patch("browser_copilot.cli.commands.InputHandler")
    async def test_run_test_command_failure(
        self,
        mock_input,
        mock_print_header,
        mock_storage,
        mock_config,
        mock_executor,
        mock_args,
    ):
        """Test test command with test failures"""
        # Setup mocks
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance

        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance
        mock_executor_instance.execute_test = AsyncMock(return_value={"success": False})
        mock_executor_instance.save_results.return_value = {"report": "/test/report.md"}
        mock_executor_instance.display_summary.return_value = None

        # Mock InputHandler static methods
        mock_input.read_from_file.return_value = "Test content"
        mock_input.validate_scenario.return_value = []

        # Add missing args attributes
        mock_args.system_prompt = None
        mock_args.save_config = False
        mock_args.enhance_test = False
        mock_args.no_isolated = False
        mock_args.device = None
        mock_args.user_agent = None
        mock_args.proxy_server = None
        mock_args.proxy_bypass = None
        mock_args.ignore_https_errors = False
        mock_args.block_service_workers = False
        mock_args.save_trace = False
        mock_args.save_session = False
        mock_args.allowed_origins = None
        mock_args.blocked_origins = None
        mock_args.output_format = "markdown"
        mock_args.output_file = None

        result = await run_test_command(mock_args)

        assert result == 1  # Failure

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.InputHandler")
    @patch("browser_copilot.cli.commands.BrowserTestExecutor")
    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_test_command_stdin(
        self, mock_storage, mock_config, mock_executor, mock_input, mock_args
    ):
        """Test test command with stdin input"""
        mock_args.test_scenario = "-"

        # Setup mocks
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance

        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance
        mock_executor_instance.execute_test = AsyncMock(return_value={"success": True})
        mock_executor_instance.save_results.return_value = {"report": "/test/report.md"}
        mock_executor_instance.display_summary.return_value = None

        # Mock InputHandler static methods
        mock_input.read_from_stdin.return_value = "Test content from stdin"
        mock_input.validate_scenario.return_value = []

        # Add missing args attributes
        mock_args.system_prompt = None
        mock_args.save_config = False
        mock_args.enhance_test = False
        mock_args.no_isolated = False
        mock_args.device = None
        mock_args.user_agent = None
        mock_args.proxy_server = None
        mock_args.proxy_bypass = None
        mock_args.ignore_https_errors = False
        mock_args.block_service_workers = False
        mock_args.save_trace = False
        mock_args.save_session = False
        mock_args.allowed_origins = None
        mock_args.blocked_origins = None
        mock_args.output_format = "markdown"
        mock_args.output_file = None

        result = await run_test_command(mock_args)

        assert result == 0  # Success
        mock_executor_instance.execute_test.assert_called_once()

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.StorageManager")
    async def test_run_test_command_error(
        self, mock_storage, mock_config, mock_args, capsys
    ):
        """Test test command with configuration error"""
        mock_storage.side_effect = Exception("Storage init error")

        # The exception is expected to be raised, but we should handle it gracefully
        # Since the command doesn't have error handling for initialization,
        # the exception bubbles up
        with pytest.raises(Exception) as exc_info:
            await run_test_command(mock_args)
        assert "Storage init error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("browser_copilot.cli.commands.BrowserTestExecutor")
    @patch("browser_copilot.cli.commands.ConfigManager")
    @patch("browser_copilot.cli.commands.StorageManager")
    @patch("browser_copilot.cli.commands.InputHandler")
    async def test_run_test_command_quiet_mode(
        self, mock_input, mock_storage, mock_config, mock_executor, mock_args
    ):
        """Test test command in quiet mode"""
        mock_args.quiet = True

        # Setup mocks
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance

        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance
        mock_executor_instance.execute_test = AsyncMock(return_value={"success": True})
        mock_executor_instance.save_results.return_value = {"report": "/test/report.md"}
        mock_executor_instance.display_summary.return_value = None

        # Mock InputHandler static methods
        mock_input.read_from_file.return_value = "Test content"
        mock_input.validate_scenario.return_value = []

        # Add missing args attributes
        mock_args.system_prompt = None
        mock_args.save_config = False
        mock_args.enhance_test = False
        mock_args.no_isolated = False
        mock_args.device = None
        mock_args.user_agent = None
        mock_args.proxy_server = None
        mock_args.proxy_bypass = None
        mock_args.ignore_https_errors = False
        mock_args.block_service_workers = False
        mock_args.save_trace = False
        mock_args.save_session = False
        mock_args.allowed_origins = None
        mock_args.blocked_origins = None
        mock_args.output_format = "markdown"
        mock_args.output_file = None

        with patch("browser_copilot.cli.commands.print_header") as mock_print_header:
            result = await run_test_command(mock_args)

            assert result == 0  # Success
            mock_print_header.assert_not_called()  # No header in quiet mode
