"""
Utility functions for CLI operations

Contains helper functions used across CLI modules.
"""

import re
from pathlib import Path


def normalize_test_name_for_path(test_name: str) -> str:
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


def read_system_prompt(prompt_file: str | None) -> str | None:
    """
    Read system prompt from file if provided

    Args:
        prompt_file: Path to system prompt file

    Returns:
        System prompt content or None
    """
    if not prompt_file:
        return None

    try:
        return Path(prompt_file).read_text().strip()
    except Exception as e:
        raise OSError(f"Failed to read system prompt file: {e}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_token_count(count: int) -> str:
    """
    Format token count with thousands separator

    Args:
        count: Token count

    Returns:
        Formatted token count
    """
    return f"{count:,}"


def get_status_emoji(success: bool) -> str:
    """
    Get status emoji based on success

    Args:
        success: Whether the test passed

    Returns:
        Appropriate emoji
    """
    return "✅" if success else "❌"
