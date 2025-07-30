"""
Text utility functions for Browser Copilot

This module contains utility functions for text processing,
including test name extraction and normalization.
"""

import re
from pathlib import Path


def extract_test_name(test_content: str) -> str:
    """
    Extract test name from test content

    Args:
        test_content: The test file content

    Returns:
        Extracted test name or default
    """
    # Try to find a test name in the content
    lines = test_content.strip().split("\n")

    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()

        # Look for markdown headers
        if line.startswith("# "):
            name = line[2:].strip()
            # Remove any markdown formatting
            name = re.sub(r"\*\*|__|\[|\]|\(|\)", "", name)
            if name and len(name) < 100:
                return name

        # Look for "Test:" or "Test Name:" patterns
        if line.lower().startswith(("test:", "test name:", "scenario:")):
            name = line.split(":", 1)[1].strip()
            if name and len(name) < 100:
                return name

    return "Browser Test"


def normalize_test_name(test_name: str) -> str:
    """
    Normalize test name for use in file paths

    Args:
        test_name: The test name to normalize

    Returns:
        Normalized test name safe for file paths
    """
    # Remove special characters and replace with underscores
    normalized = re.sub(r"[^\w\s-]", "", test_name)
    normalized = re.sub(r"[-\s]+", "_", normalized)

    # Limit length
    if len(normalized) > 50:
        normalized = normalized[:50]

    # Ensure it starts with a letter or number
    if normalized and not normalized[0].isalnum():
        normalized = "test_" + normalized

    return normalized.lower() or "test"


def extract_test_name_from_path(test_path: Path) -> str:
    """
    Extract test name from file path

    Args:
        test_path: Path to test file

    Returns:
        Test name extracted from path
    """
    # Use the filename without extension
    name = test_path.stem

    # Clean up common prefixes
    for prefix in ["test_", "test-", "example_", "example-"]:
        if name.lower().startswith(prefix):
            name = name[len(prefix) :]

    # Convert to title case
    name = name.replace("_", " ").replace("-", " ")
    return name.title()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def indent_text(text: str, indent: int = 2) -> str:
    """
    Indent text by specified number of spaces

    Args:
        text: Text to indent
        indent: Number of spaces to indent

    Returns:
        Indented text
    """
    prefix = " " * indent
    return "\n".join(prefix + line for line in text.splitlines())


def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting from text

    Args:
        text: Text with markdown formatting

    Returns:
        Clean text without markdown
    """
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove emphasis
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    return text.strip()
