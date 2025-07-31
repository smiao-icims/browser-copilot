"""
Input validation module for Browser Copilot

This module handles all input validation including test files,
configuration values, and runtime parameters.
"""

from pathlib import Path
from typing import Any

from ..constants import (
    BROWSER_ALIASES,
    LOG_LEVELS,
    OPTIMIZATION_LEVELS,
    SUPPORTED_REPORT_FORMATS,
    VALID_BROWSERS,
)


class ValidationError(Exception):
    """Raised when validation fails"""

    pass


class InputValidator:
    """Validates inputs for Browser Copilot"""

    @staticmethod
    def validate_test_file(test_file: Path) -> None:
        """
        Validate test file exists and is readable

        Args:
            test_file: Path to test file

        Raises:
            ValidationError: If file is invalid
        """
        if not test_file.exists():
            raise ValidationError(f"Test file not found: {test_file}")

        if not test_file.is_file():
            raise ValidationError(f"Not a file: {test_file}")

        if test_file.suffix.lower() not in [".md", ".markdown"]:
            raise ValidationError(
                f"Invalid test file format: {test_file.suffix}. "
                "Only Markdown (.md) files are supported."
            )

        try:
            test_file.read_text(encoding="utf-8")
        except Exception as e:
            raise ValidationError(f"Cannot read test file: {e}")

    @staticmethod
    def validate_browser(browser: str) -> str:
        """
        Validate and normalize browser name

        Args:
            browser: Browser name or alias

        Returns:
            Normalized browser name

        Raises:
            ValidationError: If browser is invalid
        """
        browser_lower = browser.lower()

        # Map aliases to actual names
        if browser_lower in BROWSER_ALIASES:
            browser_lower = BROWSER_ALIASES[browser_lower]

        if browser_lower not in VALID_BROWSERS:
            raise ValidationError(
                f"Invalid browser: {browser}. "
                f"Valid options: {', '.join(VALID_BROWSERS)}"
            )

        return browser_lower

    @staticmethod
    def validate_viewport(width: int, height: int) -> None:
        """
        Validate viewport dimensions

        Args:
            width: Viewport width
            height: Viewport height

        Raises:
            ValidationError: If dimensions are invalid
        """
        if width < 100 or width > 5000:
            raise ValidationError(
                f"Invalid viewport width: {width}. Must be between 100 and 5000 pixels."
            )

        if height < 100 or height > 5000:
            raise ValidationError(
                f"Invalid viewport height: {height}. "
                "Must be between 100 and 5000 pixels."
            )

    @staticmethod
    def validate_optimization_level(level: str) -> None:
        """
        Validate token optimization level

        Args:
            level: Optimization level

        Raises:
            ValidationError: If level is invalid
        """
        if level not in OPTIMIZATION_LEVELS:
            raise ValidationError(
                f"Invalid optimization level: {level}. "
                f"Valid options: {', '.join(OPTIMIZATION_LEVELS.keys())}"
            )

    @staticmethod
    def validate_report_format(format: str) -> None:
        """
        Validate report format

        Args:
            format: Report format

        Raises:
            ValidationError: If format is invalid
        """
        if format not in SUPPORTED_REPORT_FORMATS:
            raise ValidationError(
                f"Invalid report format: {format}. "
                f"Valid options: {', '.join(SUPPORTED_REPORT_FORMATS)}"
            )

    @staticmethod
    def validate_log_level(level: str) -> None:
        """
        Validate log level

        Args:
            level: Log level

        Raises:
            ValidationError: If level is invalid
        """
        if level not in LOG_LEVELS:
            raise ValidationError(
                f"Invalid log level: {level}. "
                f"Valid options: {', '.join(LOG_LEVELS.keys())}"
            )

    @staticmethod
    def validate_context_config(config: dict[str, Any]) -> None:
        """
        Validate context management configuration

        Args:
            config: Context configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
        """
        window_size = config.get("context_window_size", 25000)
        if not isinstance(window_size, int) or window_size < 1000:
            raise ValidationError(
                f"Invalid context window size: {window_size}. "
                "Must be an integer >= 1000."
            )

        preserve_first = config.get("context_preserve_first", 2)
        if not isinstance(preserve_first, int) or preserve_first < 0:
            raise ValidationError(
                f"Invalid preserve_first value: {preserve_first}. "
                "Must be a non-negative integer."
            )

        preserve_last = config.get("context_preserve_last", 10)
        if not isinstance(preserve_last, int) or preserve_last < 0:
            raise ValidationError(
                f"Invalid preserve_last value: {preserve_last}. "
                "Must be a non-negative integer."
            )

    @staticmethod
    def validate_proxy_config(config: dict[str, Any]) -> None:
        """
        Validate proxy configuration

        Args:
            config: Proxy configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
        """
        proxy_server = config.get("proxy_server")
        if proxy_server and not isinstance(proxy_server, str):
            raise ValidationError(
                f"Invalid proxy server: {proxy_server}. Must be a string URL."
            )

        proxy_bypass = config.get("proxy_bypass")
        if proxy_bypass and not isinstance(proxy_bypass, str):
            raise ValidationError(
                f"Invalid proxy bypass: {proxy_bypass}. Must be a string."
            )
