"""
Browser Configuration Builder component

Handles browser-specific configuration and MCP server setup.
"""

import re
from datetime import datetime
from pathlib import Path

from mcp import StdioServerParameters

from .exceptions import BrowserSetupError
from .models import BrowserOptions


class BrowserConfigBuilder:
    """Builds MCP server configuration for browser automation"""

    VALID_BROWSERS = ["chromium", "chrome", "firefox", "webkit", "safari", "edge"]
    BROWSER_ALIASES = {
        "chrome": "chromium",
        "edge": "msedge",
        "safari": "webkit",
    }

    def validate_browser(self, browser: str) -> str:
        """
        Validate and normalize browser name

        Args:
            browser: Browser name to validate

        Returns:
            Normalized browser name for MCP

        Raises:
            BrowserSetupError: If browser name is invalid
        """
        if browser not in self.VALID_BROWSERS:
            raise BrowserSetupError(
                f"Invalid browser '{browser}'. "
                f"Must be one of: {', '.join(self.VALID_BROWSERS)}"
            )

        # Map aliases to actual browser names
        return self.BROWSER_ALIASES.get(browser, browser)

    def build_mcp_args(self, options: BrowserOptions) -> list[str]:
        """
        Build MCP server command arguments

        Args:
            options: Browser configuration options

        Returns:
            List of command arguments for MCP server
        """
        # Validate and normalize browser
        browser = self.validate_browser(options.browser)

        # Build viewport size string
        viewport_size = f"{options.viewport_width},{options.viewport_height}"

        # Start with base arguments
        args = [
            "@playwright/mcp",
            "--browser",
            browser,
            "--viewport-size",
            viewport_size,
        ]

        # Add optional flags
        if options.headless:
            args.append("--headless")

        if not options.enable_screenshots:
            args.append("--no-screenshots")

        # Add isolated mode by default unless explicitly disabled
        if not options.no_isolated:
            args.append("--isolated")

        # Device emulation
        if options.device:
            args.extend(["--device", options.device])

        # User agent
        if options.user_agent:
            args.extend(["--user-agent", options.user_agent])

        # Proxy settings
        if options.proxy_server:
            args.extend(["--proxy-server", options.proxy_server])
        if options.proxy_bypass:
            args.extend(["--proxy-bypass", options.proxy_bypass])

        # Security and debugging options
        if options.ignore_https_errors:
            args.append("--ignore-https-errors")
        if options.block_service_workers:
            args.append("--block-service-workers")

        # Save options
        if options.save_trace:
            args.append("--save-trace")
        if options.save_session:
            args.append("--save-session")

        # Origin restrictions
        if options.allowed_origins:
            args.extend(["--allowed-origins", options.allowed_origins])
        if options.blocked_origins:
            args.extend(["--blocked-origins", options.blocked_origins])

        # Output directory
        if options.output_dir:
            args.extend(["--output-dir", options.output_dir])

        return args

    def create_session_directory(self, test_name: str, base_dir: Path) -> Path:
        """
        Create directory for test session artifacts

        Args:
            test_name: Name of the test
            base_dir: Base directory for storage

        Returns:
            Path to created session directory
        """
        # Normalize test name for filesystem
        normalized_name = self._normalize_test_name(test_name)

        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create session directory
        session_dir = base_dir / "sessions" / f"{normalized_name}_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_dir

    def get_server_params(self, options: BrowserOptions) -> StdioServerParameters:
        """
        Get complete server parameters for MCP

        Args:
            options: Browser configuration options

        Returns:
            StdioServerParameters for MCP client
        """
        args = self.build_mcp_args(options)
        return StdioServerParameters(command="npx", args=args)

    def _normalize_test_name(self, test_name: str) -> str:
        """
        Normalize test name for use in file paths

        Args:
            test_name: Original test name

        Returns:
            Normalized test name safe for file paths
        """
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
