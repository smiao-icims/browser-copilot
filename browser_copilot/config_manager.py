"""
Configuration Manager for Browser Copilot

Manages configuration settings with priority order:
1. Command-line arguments (highest priority)
2. Environment variables
3. Config file (~/.browser_copilot/settings/config.json)
4. Smart defaults (lowest priority)
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    from browser_copilot.storage_manager import StorageManager
except ImportError:
    # For testing, when imported directly
    from storage_manager import StorageManager  # type: ignore[no-redef]


class ConfigManager:
    """Manages configuration with layered priority system"""

    # Environment variable prefix
    ENV_PREFIX = "BROWSER_PILOT_"

    # Default configuration values
    DEFAULTS = {
        # Model configuration
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
        # Browser configuration
        "browser": "chromium",
        "headless": False,
        "viewport_width": 1280,
        "viewport_height": 720,
        # Output configuration
        "output_format": "json",
        "output_file": None,
        "verbose": False,
        "quiet": False,
        # Storage configuration
        "logs_retention_days": 7,
        "reports_retention_days": 30,
        "screenshots_retention_days": 7,
        "enable_screenshots": True,
        # Test configuration
        "timeout": 60,
        "retry_count": 3,
        "parallel_tests": 1,
        # Token optimization
        "token_optimization": True,
        "max_context_length": 8000,
        "compression_level": "medium",
    }

    def __init__(self, storage_manager: StorageManager | None = None):
        """
        Initialize ConfigManager

        Args:
            storage_manager: Optional StorageManager instance. If not provided,
                           creates a new one.
        """
        self.storage = storage_manager or StorageManager()
        self.cli_args: dict[str, Any] = {}
        self._config_cache: dict[str, Any] | None = None

    def set_cli_args(self, args: dict[str, Any]) -> None:
        """
        Set command-line arguments (highest priority)

        Args:
            args: Dictionary of CLI arguments
        """
        # Filter out None values
        self.cli_args = {k: v for k, v in args.items() if v is not None}
        # Clear cache to force reload
        self._config_cache = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with priority handling

        Priority order:
        1. CLI arguments
        2. Environment variables
        3. Config file
        4. Defaults

        Args:
            key: Configuration key
            default: Default value if not found anywhere

        Returns:
            Configuration value
        """
        # 1. Check CLI arguments first (highest priority)
        if key in self.cli_args:
            return self.cli_args[key]

        # 2. Check environment variables
        env_key = f"{self.ENV_PREFIX}{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        # 3. Check config file
        if self._config_cache is None:
            self._load_config_file()

        if self._config_cache and key in self._config_cache:
            return self._config_cache[key]

        # 4. Check defaults
        if key in self.DEFAULTS:
            return self.DEFAULTS[key]

        # 5. Return provided default
        return default

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """
        Set configuration value

        Args:
            key: Configuration key
            value: Configuration value
            persist: Whether to save to config file
        """
        # Update in-memory cache
        if self._config_cache is None:
            self._load_config_file()

        # Ensure cache is initialized
        if self._config_cache is None:
            self._config_cache = {}

        self._config_cache[key] = value

        # Persist to file if requested
        if persist:
            self.storage.save_setting(key, value, "config")

    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration values with priorities applied

        Returns:
            Dictionary of all configuration values
        """
        # Start with defaults
        config = self.DEFAULTS.copy()

        # Layer config file values
        if self._config_cache is None:
            self._load_config_file()

        if self._config_cache:
            config.update(self._config_cache)

        # Layer environment variables
        for key in self.DEFAULTS:
            env_key = f"{self.ENV_PREFIX}{key.upper()}"
            env_value = os.environ.get(env_key)
            if env_value is not None:
                config[key] = self._parse_env_value(env_value)

        # Layer CLI arguments (highest priority)
        config.update(self.cli_args)

        return config

    def validate(self) -> list[str]:
        """
        Validate configuration settings

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        config = self.get_all()

        # Validate browser choice
        valid_browsers = ["chromium", "chrome", "firefox", "safari", "edge"]
        if config.get("browser") not in valid_browsers:
            errors.append(
                f"Invalid browser: {config.get('browser')}. Must be one of: {', '.join(valid_browsers)}"
            )

        # Validate output format
        valid_formats = ["json", "yaml", "xml", "junit", "html", "markdown"]
        if config.get("output_format") not in valid_formats:
            errors.append(
                f"Invalid output format: {config.get('output_format')}. Must be one of: {', '.join(valid_formats)}"
            )

        # Validate numeric values
        if config.get("timeout", 0) <= 0:
            errors.append("Timeout must be positive")

        if config.get("retry_count", 0) < 0:
            errors.append("Retry count must be non-negative")

        if config.get("parallel_tests", 1) < 1:
            errors.append("Parallel tests must be at least 1")

        # Validate viewport dimensions
        if config.get("viewport_width", 0) <= 0:
            errors.append("Viewport width must be positive")

        if config.get("viewport_height", 0) <= 0:
            errors.append("Viewport height must be positive")

        # Validate retention days
        for key in [
            "logs_retention_days",
            "reports_retention_days",
            "screenshots_retention_days",
        ]:
            if config.get(key, 0) < 0:
                errors.append(f"{key} must be non-negative")

        # Validate token optimization settings
        if config.get("max_context_length", 0) <= 0:
            errors.append("Max context length must be positive")

        valid_compression = ["none", "low", "medium", "high"]
        if config.get("compression_level") not in valid_compression:
            errors.append(
                f"Invalid compression level: {config.get('compression_level')}. Must be one of: {', '.join(valid_compression)}"
            )

        return errors

    def reset(self, key: str | None = None) -> None:
        """
        Reset configuration to defaults

        Args:
            key: Specific key to reset. If None, resets all.
        """
        if key:
            # Reset specific key
            if key in self.DEFAULTS:
                self.set(key, self.DEFAULTS[key])
            else:
                # Remove non-default key
                if self._config_cache and key in self._config_cache:
                    del self._config_cache[key]
                    # Update file
                    all_settings = self.storage.get_all_settings("config")
                    if key in all_settings:
                        del all_settings[key]
                        # Save updated settings
                        for k, v in all_settings.items():
                            self.storage.save_setting(k, v, "config")
        else:
            # Reset all to defaults
            self._config_cache = {}
            # Clear config file
            config_file = self.storage.get_settings_file("config")
            if config_file.exists():
                config_file.unlink()

    def export_config(self, path: Path) -> None:
        """
        Export current configuration to file

        Args:
            path: Path to export file
        """
        config = self.get_all()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def import_config(self, path: Path) -> None:
        """
        Import configuration from file

        Args:
            path: Path to import file
        """
        with open(path, encoding="utf-8") as f:
            config = json.load(f)

        # Validate imported config
        temp_cache = self._config_cache
        self._config_cache = config
        errors = self.validate()

        if errors:
            # Restore original config
            self._config_cache = temp_cache
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        # Save each setting
        for key, value in config.items():
            self.set(key, value)

    def get_model_config(self) -> dict[str, Any]:
        """
        Get model-specific configuration

        Returns:
            Dictionary of model configuration
        """
        return {
            "provider": self.get("model_provider"),
            "name": self.get("model_name"),
            "temperature": self.get("temperature"),
            "max_tokens": self.get("max_tokens"),
        }

    def get_browser_config(self) -> dict[str, Any]:
        """
        Get browser-specific configuration

        Returns:
            Dictionary of browser configuration
        """
        return {
            "browser": self.get("browser"),
            "headless": self.get("headless"),
            "viewport": {
                "width": self.get("viewport_width"),
                "height": self.get("viewport_height"),
            },
        }

    def get_output_config(self) -> dict[str, Any]:
        """
        Get output-specific configuration

        Returns:
            Dictionary of output configuration
        """
        return {
            "format": self.get("output_format"),
            "file": self.get("output_file"),
            "verbose": self.get("verbose"),
            "quiet": self.get("quiet"),
        }

    def _load_config_file(self) -> None:
        """Load configuration from file into cache"""
        self._config_cache = self.storage.get_all_settings("config") or {}

    def has_config(self) -> bool:
        """
        Check if any configuration exists (file or environment)

        Returns:
            True if configuration exists, False otherwise
        """
        # Check for config file
        if self._config_cache is None:
            self._load_config_file()

        if self._config_cache:
            return True

        # Check for any Browser Copilot environment variables
        for env_key in os.environ:
            if env_key.startswith(self.ENV_PREFIX):
                return True

        # Check for ModelForge configuration
        try:
            from modelforge.registry import ModelForgeRegistry

            registry = ModelForgeRegistry()
            if registry.get_default_provider():
                return True
        except Exception:
            pass

        return False

    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type

        Args:
            value: String value from environment

        Returns:
            Parsed value
        """
        # Try to parse as JSON first (handles bool, int, float, list, dict)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            return value
