"""
Constants and configuration values for Browser Copilot

This module contains all constant values, limits, and configuration
defaults used throughout the application.
"""

# Model context limits (fallback when model-forge metadata is unavailable)
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    # Common fallback limits - model-forge should provide accurate data
    "github_copilot_gpt_4o": 128000,
    "openai_gpt_4o": 128000,
    "anthropic_claude_3_5_sonnet": 200000,
    "google_gemini_1_5_pro": 2000000,
}

# Browser configurations
VALID_BROWSERS = ["chromium", "chrome", "firefox", "safari", "webkit", "edge", "msedge"]
BROWSER_ALIASES = {"chrome": "chromium", "edge": "msedge", "safari": "webkit"}

# Default viewport settings
DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 800

# Context management defaults
DEFAULT_CONTEXT_WINDOW_SIZE = 25000
DEFAULT_PRESERVE_FIRST_N = 2
DEFAULT_PRESERVE_LAST_N = 10
DEFAULT_COMPRESSION_LEVEL = "medium"

# Execution limits
DEFAULT_RECURSION_LIMIT = 200
DEFAULT_TIMEOUT_SECONDS = 300

# File and directory naming
SESSION_DIR_FORMAT = "{test_name}_{timestamp}"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Token optimization levels
OPTIMIZATION_LEVELS = {
    "off": "No compression",
    "low": "Basic whitespace removal",
    "medium": "Moderate compression (default)",
    "high": "Aggressive compression",
}

# Report formats
SUPPORTED_REPORT_FORMATS = ["markdown", "json", "html"]
DEFAULT_REPORT_FORMAT = "markdown"

# Logging levels
LOG_LEVELS = {
    "debug": "Detailed debugging information",
    "info": "General information",
    "warning": "Warning messages",
    "error": "Error messages only",
}
