"""
Stream handler for Browser Copilot

Handles streaming output for real-time feedback during test execution.
"""

from datetime import datetime


class StreamHandler:
    """Handles streaming output for real-time feedback"""

    def __init__(self, verbose: bool = False, quiet: bool = False):
        """
        Initialize StreamHandler

        Args:
            verbose: Enable verbose output
            quiet: Suppress all output except errors
        """
        self.verbose = verbose
        self.quiet = quiet
        self._buffer: list[tuple[datetime, str, str]] = []

    def write(self, message: str, level: str = "info") -> None:
        """
        Write message to appropriate stream

        Args:
            message: Message to write
            level: Message level (debug, info, warning, error)
        """
        self._buffer.append((datetime.now(), level, message))

        # Determine if message should be displayed
        should_display = False

        if level == "error":
            should_display = True  # Always show errors
        elif not self.quiet:
            if level in ["warning", "info"]:
                should_display = True
            elif level == "debug" and self.verbose:
                should_display = True

        if should_display:
            prefix = {
                "debug": "[DEBUG]",
                "info": "[INFO]",
                "warning": "[WARN]",
                "error": "[ERROR]",
            }.get(level, "")

            if prefix:
                print(f"{prefix} {message}")
            else:
                print(message)

    def get_buffer(self) -> list[tuple[datetime, str, str]]:
        """Get all buffered messages"""
        return self._buffer.copy()

    def clear_buffer(self) -> None:
        """Clear message buffer"""
        self._buffer.clear()
