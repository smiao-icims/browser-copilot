"""
Browser tools management for Browser Copilot

This module handles all browser-related functionality including:
- MCP server connection and management
- Browser tool loading and initialization
- Browser configuration and validation
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class BrowserToolsManager:
    """Manages browser automation tools and MCP server connections"""

    @staticmethod
    def get_valid_browsers() -> list[str]:
        """
        Get list of valid browser choices

        Returns:
            List of valid browser names
        """
        # Playwright supported browsers + common aliases
        return ["chromium", "chrome", "firefox", "safari", "webkit", "edge", "msedge"]

    @staticmethod
    def map_browser_alias(browser: str) -> str:
        """
        Map browser aliases to their actual names

        Args:
            browser: Browser name or alias

        Returns:
            Actual browser name for Playwright
        """
        browser_map = {"chrome": "chromium", "edge": "msedge", "safari": "webkit"}
        return browser_map.get(browser, browser)

    @staticmethod
    def validate_browser(browser: str) -> None:
        """
        Validate browser choice

        Args:
            browser: Browser name to validate

        Raises:
            ValueError: If browser is not valid
        """
        valid_browsers = BrowserToolsManager.get_valid_browsers()
        if browser not in valid_browsers:
            raise ValueError(
                f"Invalid browser '{browser}'. Must be one of: {', '.join(valid_browsers)}"
            )

    @staticmethod
    def build_browser_args(
        browser: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        headless: bool = False,
        enable_screenshots: bool = True,
        session_dir: Path | None = None,
        **kwargs,
    ) -> list[str]:
        """
        Build browser arguments for MCP server

        Args:
            browser: Browser name
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            headless: Whether to run in headless mode
            enable_screenshots: Whether to enable screenshot capture
            session_dir: Directory for saving traces/sessions
            **kwargs: Additional browser options

        Returns:
            List of browser arguments
        """
        # Map browser aliases
        actual_browser = BrowserToolsManager.map_browser_alias(browser)

        # Build viewport size
        viewport_size = f"{viewport_width},{viewport_height}"

        # Base arguments
        browser_args = [
            "@playwright/mcp",
            "--browser",
            actual_browser,
            "--viewport-size",
            viewport_size,
        ]

        # Add headless mode
        if headless:
            browser_args.append("--headless")

        # Screenshot control
        if not enable_screenshots:
            browser_args.append("--no-screenshots")

        # Add isolated mode by default unless explicitly disabled
        # This ensures each test run starts with a clean browser state
        if not kwargs.get("no_isolated", False):
            browser_args.append("--isolated")

        # Add device emulation if specified
        if kwargs.get("device"):
            browser_args.extend(["--device", kwargs["device"]])

        # Add user agent if specified
        if kwargs.get("user_agent"):
            browser_args.extend(["--user-agent", kwargs["user_agent"]])

        # Add proxy settings if specified
        if kwargs.get("proxy_server"):
            browser_args.extend(["--proxy-server", kwargs["proxy_server"]])
        if kwargs.get("proxy_bypass"):
            browser_args.extend(["--proxy-bypass", kwargs["proxy_bypass"]])

        # Add security and debugging options
        if kwargs.get("ignore_https_errors"):
            browser_args.append("--ignore-https-errors")
        if kwargs.get("block_service_workers"):
            browser_args.append("--block-service-workers")
        if kwargs.get("save_trace"):
            browser_args.append("--save-trace")
        if kwargs.get("save_session"):
            browser_args.append("--save-session")

        # Add origin restrictions if specified
        if kwargs.get("allowed_origins"):
            browser_args.extend(["--allowed-origins", kwargs["allowed_origins"]])
        if kwargs.get("blocked_origins"):
            browser_args.extend(["--blocked-origins", kwargs["blocked_origins"]])

        # Set output directory for traces/sessions if saving
        if session_dir and (kwargs.get("save_trace") or kwargs.get("save_session")):
            browser_args.extend(["--output-dir", str(session_dir)])

        return browser_args

    @staticmethod
    def create_session_directory(
        base_dir: Path, test_name: str, timestamp: datetime | None = None
    ) -> Path:
        """
        Create a session-specific output directory

        Args:
            base_dir: Base directory for storage
            test_name: Test name (will be normalized)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Path to session directory
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Normalize test name for file system
        test_name_normalized = BrowserToolsManager.normalize_test_name(test_name)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

        session_dir = base_dir / "sessions" / f"{test_name_normalized}_{timestamp_str}"
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_dir

    @staticmethod
    def normalize_test_name(test_name: str) -> str:
        """
        Normalize test name for use in file paths

        Args:
            test_name: Original test name

        Returns:
            Normalized test name safe for file paths
        """
        import re

        # Convert to lowercase and replace spaces with hyphens
        normalized = test_name.lower().replace(" ", "-")
        # Remove special characters, keep only alphanumeric and hyphens
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)
        # Remove multiple consecutive hyphens
        normalized = re.sub(r"-+", "-", normalized)
        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")
        # Ensure it's not empty
        if not normalized:
            normalized = "browser-test"
        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50].rstrip("-")
        return normalized

    @staticmethod
    async def load_browser_tools(
        browser_args: list[str], stream_handler=None
    ) -> tuple[list[Any], ClientSession]:
        """
        Load browser tools from MCP server

        Args:
            browser_args: Arguments for browser MCP server
            stream_handler: Optional handler for debug output

        Returns:
            Tuple of (tools list, client session)
        """
        server_params = StdioServerParameters(command="npx", args=browser_args)

        # Create stdio client connection
        read, write = await stdio_client(server_params).__aenter__()
        session = await ClientSession(read, write).__aenter__()
        await session.initialize()

        # Load tools
        tools = await load_mcp_tools(session)

        if stream_handler:
            stream_handler.write(f"Loaded {len(tools)} MCP browser tools", "debug")

        # Log available tools
        logger.debug(f"Available browser tools: {[tool.name for tool in tools]}")

        return tools, session

    @staticmethod
    def get_browser_info(browser: str) -> dict[str, Any]:
        """
        Get information about a browser

        Args:
            browser: Browser name

        Returns:
            Dictionary with browser information
        """
        actual_browser = BrowserToolsManager.map_browser_alias(browser)

        # Browser-specific information
        browser_info = {
            "chromium": {
                "name": "Chromium",
                "engine": "Blink",
                "supports_headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "notes": "Default browser, best compatibility",
            },
            "firefox": {
                "name": "Firefox",
                "engine": "Gecko",
                "supports_headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "notes": "Good for testing Firefox-specific features",
            },
            "webkit": {
                "name": "WebKit",
                "engine": "WebKit",
                "supports_headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "notes": "Safari's rendering engine",
            },
            "msedge": {
                "name": "Microsoft Edge",
                "engine": "Blink",
                "supports_headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "notes": "Edge-specific testing",
            },
        }

        return browser_info.get(
            actual_browser,
            {
                "name": browser,
                "engine": "Unknown",
                "supports_headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "notes": "Unknown browser",
            },
        )

    @staticmethod
    def filter_tools_by_preference(
        tools: list[Any], enable_screenshots: bool = True, **preferences
    ) -> list[Any]:
        """
        Filter tools based on user preferences

        Args:
            tools: List of available tools
            enable_screenshots: Whether screenshots are enabled
            **preferences: Additional preferences

        Returns:
            Filtered list of tools
        """
        filtered_tools = []

        for tool in tools:
            # Filter out screenshot tool if disabled
            if not enable_screenshots and "screenshot" in tool.name.lower():
                logger.debug(f"Filtering out screenshot tool: {tool.name}")
                continue

            # Add more filtering logic as needed
            filtered_tools.append(tool)

        return filtered_tools
