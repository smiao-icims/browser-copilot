"""
Tests for BrowserToolsManager
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
from browser_tools import BrowserToolsManager


@pytest.mark.unit
class TestBrowserToolsManager:
    """Test BrowserToolsManager functionality"""

    def test_get_valid_browsers(self):
        """Test getting valid browser list"""
        browsers = BrowserToolsManager.get_valid_browsers()

        assert "chromium" in browsers
        assert "chrome" in browsers
        assert "firefox" in browsers
        assert "safari" in browsers
        assert "webkit" in browsers
        assert "edge" in browsers
        assert "msedge" in browsers

    def test_map_browser_alias(self):
        """Test browser alias mapping"""
        assert BrowserToolsManager.map_browser_alias("chrome") == "chromium"
        assert BrowserToolsManager.map_browser_alias("edge") == "msedge"
        assert BrowserToolsManager.map_browser_alias("safari") == "webkit"
        assert BrowserToolsManager.map_browser_alias("firefox") == "firefox"
        assert BrowserToolsManager.map_browser_alias("chromium") == "chromium"

    def test_validate_browser(self):
        """Test browser validation"""
        # Valid browsers should not raise
        BrowserToolsManager.validate_browser("chromium")
        BrowserToolsManager.validate_browser("chrome")
        BrowserToolsManager.validate_browser("firefox")

        # Invalid browser should raise
        with pytest.raises(ValueError) as exc_info:
            BrowserToolsManager.validate_browser("invalid_browser")
        assert "Invalid browser 'invalid_browser'" in str(exc_info.value)

    def test_build_browser_args_basic(self):
        """Test building basic browser arguments"""
        args = BrowserToolsManager.build_browser_args(
            browser="chromium",
            viewport_width=1920,
            viewport_height=1080,
        )

        assert "@playwright/mcp" in args
        assert "--browser" in args
        assert "chromium" in args
        assert "--viewport-size" in args
        assert "1920,1080" in args
        assert "--isolated" in args  # Default

    def test_build_browser_args_headless(self):
        """Test building browser arguments with headless mode"""
        args = BrowserToolsManager.build_browser_args(
            browser="firefox",
            headless=True,
        )

        assert "--headless" in args

    def test_build_browser_args_no_screenshots(self):
        """Test building browser arguments without screenshots"""
        args = BrowserToolsManager.build_browser_args(
            browser="chromium",
            enable_screenshots=False,
        )

        assert "--no-screenshots" in args

    def test_build_browser_args_with_options(self, temp_dir):
        """Test building browser arguments with various options"""
        # Use a temporary directory for cross-platform compatibility
        session_dir = temp_dir / "test_session"

        args = BrowserToolsManager.build_browser_args(
            browser="chromium",
            device="iPhone 12",
            user_agent="Custom Agent",
            proxy_server="http://proxy:8080",
            proxy_bypass="localhost",
            ignore_https_errors=True,
            block_service_workers=True,
            save_trace=True,
            save_session=True,
            allowed_origins="https://example.com",
            blocked_origins="https://blocked.com",
            session_dir=session_dir,
        )

        assert "--device" in args
        assert "iPhone 12" in args
        assert "--user-agent" in args
        assert "Custom Agent" in args
        assert "--proxy-server" in args
        assert "http://proxy:8080" in args
        assert "--proxy-bypass" in args
        assert "localhost" in args
        assert "--ignore-https-errors" in args
        assert "--block-service-workers" in args
        assert "--save-trace" in args
        assert "--save-session" in args
        assert "--allowed-origins" in args
        assert "https://example.com" in args
        assert "--blocked-origins" in args
        assert "https://blocked.com" in args
        assert "--output-dir" in args
        # Check that the session directory path is in args (as a string)
        assert str(session_dir) in args

    def test_normalize_test_name(self):
        """Test test name normalization"""
        assert BrowserToolsManager.normalize_test_name("Test Name") == "test-name"
        assert BrowserToolsManager.normalize_test_name("Test@#$Name") == "testname"
        assert BrowserToolsManager.normalize_test_name("Test  Name") == "test-name"
        assert BrowserToolsManager.normalize_test_name("---Test---") == "test"
        assert BrowserToolsManager.normalize_test_name("") == "browser-test"
        assert BrowserToolsManager.normalize_test_name("a" * 60) == "a" * 50
        assert (
            BrowserToolsManager.normalize_test_name("Test-Name-123") == "test-name-123"
        )

    def test_create_session_directory(self, temp_dir):
        """Test session directory creation"""
        from datetime import datetime

        test_time = datetime(2025, 1, 26, 12, 30, 45)
        session_dir = BrowserToolsManager.create_session_directory(
            temp_dir, "Test Suite", test_time
        )

        assert session_dir.exists()
        assert session_dir.is_dir()
        assert "test-suite_20250126_123045" in str(session_dir)
        assert session_dir.parent.name == "sessions"

    def test_get_browser_info(self):
        """Test getting browser information"""
        info = BrowserToolsManager.get_browser_info("chromium")
        assert info["name"] == "Chromium"
        assert info["engine"] == "Blink"
        assert info["supports_headless"] is True
        assert info["default_viewport"]["width"] == 1920

        # Test alias
        info = BrowserToolsManager.get_browser_info("chrome")
        assert info["name"] == "Chromium"

        # Test unknown browser
        info = BrowserToolsManager.get_browser_info("unknown")
        assert info["engine"] == "Unknown"

    def test_filter_tools_by_preference(self):
        """Test filtering tools by user preferences"""
        # Create mock tools
        screenshot_tool = MagicMock()
        screenshot_tool.name = "browser_take_screenshot"

        click_tool = MagicMock()
        click_tool.name = "browser_click"

        type_tool = MagicMock()
        type_tool.name = "browser_type"

        tools = [screenshot_tool, click_tool, type_tool]

        # Test with screenshots enabled
        filtered = BrowserToolsManager.filter_tools_by_preference(
            tools, enable_screenshots=True
        )
        assert len(filtered) == 3
        assert screenshot_tool in filtered

        # Test with screenshots disabled
        filtered = BrowserToolsManager.filter_tools_by_preference(
            tools, enable_screenshots=False
        )
        assert len(filtered) == 2
        assert screenshot_tool not in filtered
        assert click_tool in filtered
        assert type_tool in filtered

    @pytest.mark.asyncio
    async def test_load_browser_tools(self):
        """Test loading browser tools from MCP server"""
        # Mock the dependencies
        mock_tools = [MagicMock(name=f"tool_{i}") for i in range(5)]
        mock_session = AsyncMock()

        with patch("browser_tools.stdio_client") as mock_stdio:
            with patch("browser_tools.ClientSession") as mock_client_session:
                with patch("browser_tools.load_mcp_tools") as mock_load_tools:
                    # Setup mocks
                    mock_stdio.return_value.__aenter__.return_value = (
                        AsyncMock(),
                        AsyncMock(),
                    )
                    mock_client_session.return_value.__aenter__.return_value = (
                        mock_session
                    )
                    mock_load_tools.return_value = mock_tools

                    # Test loading tools
                    tools, session = await BrowserToolsManager.load_browser_tools(
                        ["@playwright/mcp", "--browser", "chromium"]
                    )

                    assert len(tools) == 5
                    assert session == mock_session
                    mock_session.initialize.assert_called_once()
