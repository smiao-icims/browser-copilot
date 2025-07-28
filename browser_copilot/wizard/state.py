"""State management for the configuration wizard."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WizardState:
    """Manages the state throughout the wizard execution."""

    # Configuration values
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    browser: str = "chromium"
    headless: bool = True
    compression_level: str = "medium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30
    retry_count: int = 0
    no_screenshots: bool = False
    system_prompt: str | None = None

    # Navigation state
    current_step: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    # Validation results
    provider_validated: bool = False
    browser_validated: bool = False

    # GitHub Copilot specific
    github_token: str | None = None

    def to_config(self) -> dict[str, Any]:
        """Convert state to configuration format."""
        config = {
            "provider": self.provider,
            "model": self.model,
            "browser": self.browser,
            "headless": self.headless,
            "compression_level": self.compression_level,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "no_screenshots": self.no_screenshots,
        }

        # Add optional fields
        if self.api_key:
            config["api_key"] = self.api_key
        if self.system_prompt:
            config["system_prompt"] = self.system_prompt
        if self.github_token:
            config["github_token"] = self.github_token

        return config

    def update(self, data: dict[str, Any]) -> None:
        """Update state with new data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def save_history(self) -> None:
        """Save current state to history."""
        self.history.append(
            {
                "step": self.current_step,
                "provider": self.provider,
                "model": self.model,
                "browser": self.browser,
                "headless": self.headless,
                "compression_level": self.compression_level,
            }
        )

    def restore_from_history(self, step_index: int) -> None:
        """Restore state from history."""
        if 0 <= step_index < len(self.history):
            history_state = self.history[step_index]
            self.update(history_state)
            self.current_step = history_state["step"]

    def validate(self) -> list[str]:
        """Validate the current state."""
        errors = []

        if not self.provider:
            errors.append("Provider must be specified")
        if not self.model:
            errors.append("Model must be specified")
        if not self.browser:
            errors.append("Browser must be specified")

        return errors
