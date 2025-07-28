"""
Tests for CLI argument parser
"""

import sys
from pathlib import Path

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from browser_copilot.cli.parser import create_parser


@pytest.mark.unit
class TestCLIParser:
    """Test CLI argument parser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return create_parser()

    def test_default_arguments(self, parser):
        """Test parser with default arguments"""
        args = parser.parse_args([])

        assert args.test_scenario == "-"  # Default to stdin
        assert args.verbose is False
        assert args.quiet is False
        assert args.headless is False
        assert args.cleanup is False

    def test_test_scenario_argument(self, parser):
        """Test test scenario positional argument"""
        args = parser.parse_args(["test.md"])
        assert args.test_scenario == "test.md"

        args = parser.parse_args(["-"])
        assert args.test_scenario == "-"

    def test_model_configuration(self, parser):
        """Test model configuration arguments"""
        args = parser.parse_args(
            [
                "--provider",
                "openai",
                "--model",
                "gpt-4",
                "--temperature",
                "0.7",
                "--max-tokens",
                "2000",
            ]
        )

        assert args.provider == "openai"
        assert args.model == "gpt-4"
        assert args.temperature == 0.7
        assert args.max_tokens == 2000

    def test_browser_options(self, parser):
        """Test browser configuration arguments"""
        args = parser.parse_args(
            [
                "--browser",
                "firefox",
                "--headless",
                "--viewport-width",
                "1920",
                "--viewport-height",
                "1080",
            ]
        )

        assert args.browser == "firefox"
        assert args.headless is True
        assert args.viewport_width == 1920
        assert args.viewport_height == 1080

    def test_playwright_options(self, parser):
        """Test Playwright MCP specific options"""
        args = parser.parse_args(
            [
                "--no-isolated",
                "--device",
                "iPhone 12",
                "--user-agent",
                "Custom Agent",
                "--proxy-server",
                "http://proxy:8080",
                "--ignore-https-errors",
                "--save-trace",
            ]
        )

        assert args.no_isolated is True
        assert args.device == "iPhone 12"
        assert args.user_agent == "Custom Agent"
        assert args.proxy_server == "http://proxy:8080"
        assert args.ignore_https_errors is True
        assert args.save_trace is True

    def test_output_options(self, parser):
        """Test output configuration arguments"""
        args = parser.parse_args(
            [
                "--output-format",
                "json",
                "--output-file",
                "report.json",
                "--no-screenshots",
            ]
        )

        assert args.output_format == "json"
        assert args.output_file == "report.json"
        assert args.no_screenshots is True

    def test_verbose_quiet_options(self, parser):
        """Test verbose and quiet options"""
        # Test verbose
        args = parser.parse_args(["-v"])
        assert args.verbose is True
        assert args.quiet is False

        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

        # Test quiet
        args = parser.parse_args(["-q"])
        assert args.quiet is True
        assert args.verbose is False

        args = parser.parse_args(["--quiet"])
        assert args.quiet is True

    def test_token_optimization_options(self, parser):
        """Test token optimization arguments"""
        args = parser.parse_args(
            ["--no-token-optimization", "--compression-level", "high"]
        )

        assert args.no_token_optimization is True
        assert args.compression_level == "high"

    def test_config_management_options(self, parser):
        """Test configuration management arguments"""
        args = parser.parse_args(
            ["--config", "--config-file", "custom.yaml", "--save-config"]
        )

        assert args.config is True
        assert args.config_file == "custom.yaml"
        assert args.save_config is True

    def test_storage_management_options(self, parser):
        """Test storage management arguments"""
        args = parser.parse_args(
            ["--cleanup", "--cleanup-days", "14", "--storage-info"]
        )

        assert args.cleanup is True
        assert args.cleanup_days == 14
        assert args.storage_info is True

    def test_invalid_browser_choice(self, parser):
        """Test invalid browser choice raises error"""
        with pytest.raises(SystemExit):
            parser.parse_args(["--browser", "invalid_browser"])

    def test_invalid_output_format(self, parser):
        """Test invalid output format raises error"""
        with pytest.raises(SystemExit):
            parser.parse_args(["--output-format", "invalid_format"])

    def test_invalid_compression_level(self, parser):
        """Test invalid compression level raises error"""
        with pytest.raises(SystemExit):
            parser.parse_args(["--compression-level", "invalid_level"])

    def test_help_text(self, parser, capsys):
        """Test help text contains key information"""
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

        captured = capsys.readouterr()
        assert "Browser Copilot" in captured.out
        assert "AI-powered browser test automation" in captured.out
        assert "Examples:" in captured.out

    def test_setup_wizard_argument(self, parser):
        """Test --setup-wizard argument parsing"""
        args = parser.parse_args(["--setup-wizard"])
        assert args.setup_wizard is True

    def test_config_and_setup_wizard_are_aliases(self, parser):
        """Test that --config and --setup-wizard do the same thing"""
        config_args = parser.parse_args(["--config"])
        wizard_args = parser.parse_args(["--setup-wizard"])

        assert config_args.config is True
        assert wizard_args.setup_wizard is True
