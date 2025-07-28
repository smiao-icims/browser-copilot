"""
Input handler for Browser Copilot

Manages reading test scenarios from various sources.
"""

import sys
from pathlib import Path


class InputHandler:
    """Handles reading test scenarios from various sources"""

    @staticmethod
    def read_from_file(file_path: Path) -> str:
        """
        Read test scenario from file

        Args:
            file_path: Path to test scenario file

        Returns:
            Test scenario content

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Test scenario file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()

            return content

        except Exception as e:
            raise OSError(f"Failed to read test scenario file: {e}")

    @staticmethod
    def read_from_stdin() -> str:
        """
        Read test scenario from stdin

        Returns:
            Test scenario content

        Raises:
            ValueError: If stdin is empty
        """
        if sys.stdin.isatty():
            # Interactive mode - prompt user
            print("Enter test scenario (press Ctrl+D when done):")
            print("-" * 40)

        try:
            content = sys.stdin.read().strip()

            if not content:
                raise ValueError("No test scenario provided via stdin")

            return content

        except KeyboardInterrupt:
            raise ValueError("Test scenario input cancelled")

    @staticmethod
    def validate_scenario(scenario: str) -> list[str]:
        """
        Validate test scenario content

        Args:
            scenario: Test scenario content

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        # Check minimum length
        if len(scenario) < 10:
            warnings.append("Test scenario seems too short")

        # Check for common issues
        if scenario.startswith("{") or scenario.startswith("["):
            warnings.append(
                "Test scenario appears to be JSON - should be natural language"
            )

        if scenario.startswith("<"):
            warnings.append(
                "Test scenario appears to be XML - should be natural language"
            )

        # Check for common test keywords
        test_keywords = [
            "test",
            "verify",
            "check",
            "click",
            "navigate",
            "enter",
            "select",
        ]
        if not any(keyword in scenario.lower() for keyword in test_keywords):
            warnings.append("Test scenario may lack actionable test steps")

        return warnings
