"""
Argument parser for Browser Copilot CLI

Handles command-line argument parsing and validation.
"""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Browser Copilot - AI-powered browser test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a test from file
  browser-copilot test.md

  # Run test from stdin
  echo "Navigate to example.com and verify title" | browser-copilot -

  # Run with custom output format
  browser-copilot test.md --output-format html --output-file report.html

  # Run with custom system prompt
  browser-copilot test.md --system-prompt prompt.txt

  # Use custom configuration
  browser-copilot test.md --provider anthropic --model claude-3-opus --browser firefox

  # Run cleanup of old files
  browser-copilot --cleanup

  # Configure defaults
  browser-copilot --config
        """,
    )

    # Positional argument for test scenario (optional for cleanup mode)
    parser.add_argument(
        "test_scenario",
        nargs="?",
        default="-",
        help="Test scenario file path or '-' for stdin (default: -). Not required when using --cleanup",
    )

    # Model configuration (now optional with smart defaults)
    model_group = parser.add_argument_group("Model Configuration")
    model_group.add_argument(
        "--provider", help="LLM provider (uses ModelForge discovery if not specified)"
    )
    model_group.add_argument(
        "--model", help="Model name (uses provider default if not specified)"
    )
    model_group.add_argument(
        "--temperature", type=float, help="Model temperature (0.0-1.0)"
    )
    model_group.add_argument(
        "--max-tokens", type=int, help="Maximum tokens for model response"
    )

    # Browser options
    browser_group = parser.add_argument_group("Browser Options")
    browser_group.add_argument(
        "--browser",
        choices=["chromium", "chrome", "firefox", "safari", "webkit", "edge", "msedge"],
        help="Browser to use (default: chromium)",
    )
    browser_group.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )
    browser_group.add_argument(
        "--viewport-width", type=int, help="Browser viewport width (default: 1280)"
    )
    browser_group.add_argument(
        "--viewport-height", type=int, help="Browser viewport height (default: 720)"
    )

    # Playwright MCP specific options
    playwright_group = parser.add_argument_group("Playwright MCP Options")
    playwright_group.add_argument(
        "--no-isolated",
        action="store_true",
        help="Disable isolated browser mode (default: isolated mode enabled for clean state)",
    )
    playwright_group.add_argument(
        "--device", help="Device to emulate (e.g., 'iPhone 15', 'Pixel 7')"
    )
    playwright_group.add_argument("--user-agent", help="Custom user agent string")
    playwright_group.add_argument(
        "--proxy-server", help="Proxy server URL (e.g., 'http://myproxy:3128')"
    )
    playwright_group.add_argument(
        "--proxy-bypass", help="Comma-separated domains to bypass proxy"
    )
    playwright_group.add_argument(
        "--ignore-https-errors",
        action="store_true",
        help="Ignore HTTPS certificate errors",
    )
    playwright_group.add_argument(
        "--block-service-workers",
        action="store_true",
        help="Block service workers for consistent testing",
    )
    playwright_group.add_argument(
        "--save-trace", action="store_true", help="Save Playwright trace for debugging"
    )
    playwright_group.add_argument(
        "--save-session", action="store_true", help="Save browser session for debugging"
    )
    playwright_group.add_argument(
        "--allowed-origins", help="Semicolon-separated list of allowed origins"
    )
    playwright_group.add_argument(
        "--blocked-origins", help="Semicolon-separated list of blocked origins"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-format",
        choices=["json", "yaml", "xml", "junit", "html", "markdown"],
        help="Output format for test results",
    )
    output_group.add_argument(
        "--output-file", type=str, help="Save results to specified file"
    )
    output_group.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Disable screenshot capture during tests",
    )

    # Testing options
    test_group = parser.add_argument_group("Testing Options")
    test_group.add_argument(
        "--timeout", type=int, help="Test execution timeout in seconds"
    )
    test_group.add_argument(
        "--system-prompt", type=str, help="Custom system prompt file path"
    )
    test_group.add_argument(
        "--enhance-test",
        action="store_true",
        help="Use AI to enhance test scenario before execution",
    )

    # Output control
    output_control_group = parser.add_argument_group("Output Control")
    output_control_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    output_control_group.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress all output except errors"
    )

    # Token optimization
    optimization_group = parser.add_argument_group("Token Optimization")
    optimization_group.add_argument(
        "--no-token-optimization",
        action="store_true",
        help="Disable automatic token optimization",
    )
    optimization_group.add_argument(
        "--compression-level",
        choices=["none", "low", "medium", "high"],
        help="Token compression level (default: medium)",
    )

    # Configuration management
    config_group = parser.add_argument_group("Configuration Management")
    config_group.add_argument(
        "--config",
        action="store_true",
        help="Run interactive configuration wizard",
    )
    config_group.add_argument(
        "--setup-wizard",
        action="store_true",
        help="Run interactive configuration wizard (alias for --config)",
    )
    config_group.add_argument(
        "--config-file", type=str, help="Path to custom configuration file"
    )
    config_group.add_argument(
        "--save-config",
        action="store_true",
        help="Save current settings as default configuration",
    )

    # Storage management
    storage_group = parser.add_argument_group("Storage Management")
    storage_group.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old logs and cache files",
    )
    storage_group.add_argument(
        "--cleanup-days",
        type=int,
        default=7,
        help="Number of days to keep files (default: 7)",
    )
    storage_group.add_argument(
        "--storage-info",
        action="store_true",
        help="Show storage usage information",
    )

    return parser


def parse_arguments():
    """Parse command line arguments"""
    parser = create_parser()
    return parser.parse_args()
