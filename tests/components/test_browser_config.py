"""
Tests for BrowserConfigBuilder component
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp import StdioServerParameters

from browser_copilot.components.browser_config import BrowserConfigBuilder
from browser_copilot.components.exceptions import BrowserSetupError
from browser_copilot.components.models import BrowserOptions


class TestBrowserConfigBuilder:
    """Test cases for BrowserConfigBuilder"""

    @pytest.fixture
    def builder(self):
        """Create a BrowserConfigBuilder instance"""
        return BrowserConfigBuilder()

    @pytest.fixture
    def default_options(self):
        """Create default browser options"""
        return BrowserOptions()

    def test_validate_browser_valid_names(self, builder):
        """Test validation of valid browser names"""
        valid_browsers = ["chromium", "chrome", "firefox", "webkit", "safari", "edge"]
        
        for browser in valid_browsers:
            # Should not raise exception
            result = builder.validate_browser(browser)
            assert isinstance(result, str)

    def test_validate_browser_maps_aliases(self, builder):
        """Test browser alias mapping"""
        # Test aliases
        assert builder.validate_browser("chrome") == "chromium"
        assert builder.validate_browser("edge") == "msedge"
        assert builder.validate_browser("safari") == "webkit"
        
        # Test non-aliased browsers
        assert builder.validate_browser("chromium") == "chromium"
        assert builder.validate_browser("firefox") == "firefox"
        assert builder.validate_browser("webkit") == "webkit"

    def test_validate_browser_invalid_name(self, builder):
        """Test validation rejects invalid browser names"""
        with pytest.raises(BrowserSetupError) as exc_info:
            builder.validate_browser("invalid-browser")
        
        assert "Invalid browser 'invalid-browser'" in str(exc_info.value)
        assert "Must be one of:" in str(exc_info.value)

    def test_build_mcp_args_minimal(self, builder):
        """Test building MCP args with minimal options"""
        options = BrowserOptions()
        args = builder.build_mcp_args(options)
        
        assert args == [
            "@playwright/mcp",
            "--browser", "chromium",
            "--viewport-size", "1920,1080",
            "--isolated"
        ]

    def test_build_mcp_args_headless(self, builder):
        """Test building MCP args with headless mode"""
        options = BrowserOptions(headless=True)
        args = builder.build_mcp_args(options)
        
        assert "--headless" in args

    def test_build_mcp_args_no_screenshots(self, builder):
        """Test building MCP args with screenshots disabled"""
        options = BrowserOptions(enable_screenshots=False)
        args = builder.build_mcp_args(options)
        
        assert "--no-screenshots" in args

    def test_build_mcp_args_no_isolated(self, builder):
        """Test building MCP args without isolated mode"""
        options = BrowserOptions(no_isolated=True)
        args = builder.build_mcp_args(options)
        
        assert "--isolated" not in args

    def test_build_mcp_args_with_device(self, builder):
        """Test building MCP args with device emulation"""
        options = BrowserOptions(device="iPhone 12")
        args = builder.build_mcp_args(options)
        
        assert "--device" in args
        assert "iPhone 12" in args

    def test_build_mcp_args_with_user_agent(self, builder):
        """Test building MCP args with custom user agent"""
        options = BrowserOptions(user_agent="CustomBot/1.0")
        args = builder.build_mcp_args(options)
        
        assert "--user-agent" in args
        assert "CustomBot/1.0" in args

    def test_build_mcp_args_with_proxy(self, builder):
        """Test building MCP args with proxy settings"""
        options = BrowserOptions(
            proxy_server="http://proxy.example.com:8080",
            proxy_bypass="localhost,127.0.0.1"
        )
        args = builder.build_mcp_args(options)
        
        assert "--proxy-server" in args
        assert "http://proxy.example.com:8080" in args
        assert "--proxy-bypass" in args
        assert "localhost,127.0.0.1" in args

    def test_build_mcp_args_with_security_options(self, builder):
        """Test building MCP args with security options"""
        options = BrowserOptions(
            ignore_https_errors=True,
            block_service_workers=True
        )
        args = builder.build_mcp_args(options)
        
        assert "--ignore-https-errors" in args
        assert "--block-service-workers" in args

    def test_build_mcp_args_with_save_options(self, builder):
        """Test building MCP args with save options"""
        options = BrowserOptions(
            save_trace=True,
            save_session=True,
            output_dir="/tmp/test"
        )
        args = builder.build_mcp_args(options)
        
        assert "--save-trace" in args
        assert "--save-session" in args
        assert "--output-dir" in args
        assert "/tmp/test" in args

    def test_build_mcp_args_with_origin_restrictions(self, builder):
        """Test building MCP args with origin restrictions"""
        options = BrowserOptions(
            allowed_origins="https://example.com,https://test.com",
            blocked_origins="https://evil.com"
        )
        args = builder.build_mcp_args(options)
        
        assert "--allowed-origins" in args
        assert "https://example.com,https://test.com" in args
        assert "--blocked-origins" in args
        assert "https://evil.com" in args

    def test_build_mcp_args_custom_viewport(self, builder):
        """Test building MCP args with custom viewport"""
        options = BrowserOptions(viewport_width=1366, viewport_height=768)
        args = builder.build_mcp_args(options)
        
        assert "--viewport-size" in args
        assert "1366,768" in args

    def test_create_session_directory(self, builder, tmp_path):
        """Test session directory creation"""
        test_name = "Test Browser Automation"
        base_dir = tmp_path
        
        session_dir = builder.create_session_directory(test_name, base_dir)
        
        # Check directory was created
        assert session_dir.exists()
        assert session_dir.is_dir()
        
        # Check naming pattern
        assert "test-browser-automation" in str(session_dir)
        assert session_dir.parent.name == "sessions"

    def test_create_session_directory_normalizes_name(self, builder, tmp_path):
        """Test session directory name normalization"""
        test_names = [
            ("Test With Spaces", "test-with-spaces"),
            ("Test@With#Special$Chars", "testwithspecialchars"),
            ("Test--With---Multiple----Dashes", "test-with-multiple-dashes"),
            ("-Leading-Trailing-", "leading-trailing"),
            ("", "browser-test"),  # Empty name fallback
            ("A" * 100, "a" * 50),  # Long name truncation
        ]
        
        for test_name, expected_pattern in test_names:
            session_dir = builder.create_session_directory(test_name, tmp_path)
            dir_name = session_dir.parent.name
            assert dir_name == "sessions"
            assert expected_pattern in str(session_dir).lower()

    def test_get_server_params(self, builder):
        """Test getting complete server parameters"""
        options = BrowserOptions(browser="firefox", headless=True)
        params = builder.get_server_params(options)
        
        assert isinstance(params, StdioServerParameters)
        assert params.command == "npx"
        assert params.args[0] == "@playwright/mcp"
        assert "--browser" in params.args
        assert "firefox" in params.args
        assert "--headless" in params.args

    def test_get_server_params_with_output_dir(self, builder, tmp_path):
        """Test server params with output directory"""
        options = BrowserOptions(
            save_trace=True,
            output_dir=str(tmp_path / "output")
        )
        params = builder.get_server_params(options)
        
        assert "--output-dir" in params.args
        idx = params.args.index("--output-dir")
        assert params.args[idx + 1] == str(tmp_path / "output")

    def test_normalize_test_name(self, builder):
        """Test the internal normalize_test_name method"""
        # This tests the private method indirectly through public API
        test_cases = [
            ("Simple Test", "simple-test"),
            ("Test 123", "test-123"),
            ("Test!@#$%", "test"),
            ("   Spaces   ", "spaces"),
        ]
        
        for input_name, expected_pattern in test_cases:
            session_dir = builder.create_session_directory(input_name, Path("/tmp"))
            assert expected_pattern in str(session_dir).lower()

    @patch("browser_copilot.components.browser_config.datetime")
    def test_session_directory_timestamp(self, mock_datetime, builder, tmp_path):
        """Test session directory includes timestamp"""
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        session_dir = builder.create_session_directory("Test", tmp_path)
        
        assert "20240101_120000" in str(session_dir)

    def test_build_mcp_args_complete_example(self, builder):
        """Test building MCP args with all options"""
        options = BrowserOptions(
            browser="chrome",
            headless=True,
            viewport_width=1024,
            viewport_height=768,
            enable_screenshots=False,
            device="iPad Pro",
            user_agent="TestBot/2.0",
            proxy_server="http://proxy:3128",
            proxy_bypass="*.local",
            ignore_https_errors=True,
            block_service_workers=True,
            save_trace=True,
            save_session=True,
            allowed_origins="https://app.example.com",
            blocked_origins="https://ads.example.com",
            no_isolated=True,
            output_dir="/tmp/traces"
        )
        
        args = builder.build_mcp_args(options)
        
        # Verify all options are included
        assert "@playwright/mcp" in args
        assert "--browser" in args
        assert "chromium" in args  # chrome -> chromium
        assert "--headless" in args
        assert "--viewport-size" in args
        assert "1024,768" in args
        assert "--no-screenshots" in args
        assert "--device" in args
        assert "iPad Pro" in args
        assert "--user-agent" in args
        assert "TestBot/2.0" in args
        assert "--proxy-server" in args
        assert "--proxy-bypass" in args
        assert "--ignore-https-errors" in args
        assert "--block-service-workers" in args
        assert "--save-trace" in args
        assert "--save-session" in args
        assert "--allowed-origins" in args
        assert "--blocked-origins" in args
        assert "--isolated" not in args  # no_isolated=True
        assert "--output-dir" in args
        assert "/tmp/traces" in args