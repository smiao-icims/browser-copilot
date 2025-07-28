"""
Tests for ConfigManager
"""

import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
from config_manager import ConfigManager
from storage_manager import StorageManager


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, cleanup_env):
        """Set up test environment"""
        # Create storage and config manager
        self.storage = StorageManager(base_dir=temp_dir)
        self.config = ConfigManager(storage_manager=self.storage)
        self.temp_dir = temp_dir

    def test_defaults(self):
        """Test default configuration values"""
        assert self.config.get("model_provider") == "openai"
        assert self.config.get("browser") == "chromium"
        assert self.config.get("verbose") is False
        assert self.config.get("timeout") == 60

    def test_cli_args_priority(self):
        """Test CLI arguments have highest priority"""
        # Set value in config file
        self.config.set("verbose", True)

        # Set environment variable
        os.environ["BROWSER_PILOT_VERBOSE"] = "false"

        # Set CLI argument (highest priority)
        self.config.set_cli_args({"verbose": True})

        # CLI argument should win
        assert self.config.get("verbose") is True

    def test_env_vars_priority(self):
        """Test environment variables priority"""
        # Set value in config file
        self.config.set("browser", "firefox")

        # Set environment variable (higher priority)
        os.environ["BROWSER_PILOT_BROWSER"] = "chrome"

        # Environment variable should win
        assert self.config.get("browser") == "chrome"

    def test_config_file_persistence(self):
        """Test configuration file persistence"""
        # Set some values
        self.config.set("model_name", "gpt-4-turbo")
        self.config.set("timeout", 120)

        # Create new config manager with same storage
        config2 = ConfigManager(storage_manager=self.storage)

        # Values should persist
        assert config2.get("model_name") == "gpt-4-turbo"
        assert config2.get("timeout") == 120

    def test_get_all(self):
        """Test getting all configuration values"""
        # Set various values
        self.config.set("model_name", "claude-3")
        os.environ["BROWSER_PILOT_BROWSER"] = "safari"
        self.config.set_cli_args({"verbose": True})

        all_config = self.config.get_all()

        # Check priority order is respected
        assert all_config["model_name"] == "claude-3"  # From config file
        assert all_config["browser"] == "safari"  # From env var
        assert all_config["verbose"] is True  # From CLI args
        assert all_config["timeout"] == 60  # From defaults

    def test_validation(self):
        """Test configuration validation"""
        # Valid configuration should have no errors
        errors = self.config.validate()
        assert len(errors) == 0

        # Invalid browser
        self.config.set_cli_args({"browser": "invalid"})
        errors = self.config.validate()
        assert any("Invalid browser" in error for error in errors)

        # Invalid timeout
        self.config.set_cli_args({"timeout": -1})
        errors = self.config.validate()
        assert any("Timeout must be positive" in error for error in errors)

    def test_reset(self):
        """Test resetting configuration"""
        # Change some values
        self.config.set("model_name", "custom-model")
        self.config.set("timeout", 300)

        # Reset specific key
        self.config.reset("model_name")
        assert self.config.get("model_name") == "gpt-4o-mini"  # Back to default
        assert self.config.get("timeout") == 300  # Unchanged

        # Reset all
        self.config.reset()
        assert self.config.get("timeout") == 60  # Back to default

    def test_export_import(self):
        """Test exporting and importing configuration"""
        # Set custom values
        self.config.set("model_name", "claude-3-opus")
        self.config.set("browser", "firefox")
        self.config.set("timeout", 180)

        # Export
        export_path = Path(self.temp_dir) / "export.json"
        self.config.export_config(export_path)

        # Reset and verify defaults restored
        self.config.reset()
        assert self.config.get("model_name") == "gpt-4o-mini"

        # Import
        self.config.import_config(export_path)
        assert self.config.get("model_name") == "claude-3-opus"
        assert self.config.get("browser") == "firefox"
        assert self.config.get("timeout") == 180

    def test_env_var_parsing(self):
        """Test environment variable type parsing"""
        # Boolean
        os.environ["BROWSER_PILOT_VERBOSE"] = "true"
        assert self.config.get("verbose") is True

        # Integer
        os.environ["BROWSER_PILOT_TIMEOUT"] = "300"
        assert self.config.get("timeout") == 300

        # Float
        os.environ["BROWSER_PILOT_TEMPERATURE"] = "0.5"
        assert self.config.get("temperature") == 0.5

        # String
        os.environ["BROWSER_PILOT_MODEL_NAME"] = "custom-model"
        assert self.config.get("model_name") == "custom-model"

    def test_helper_methods(self):
        """Test configuration helper methods"""
        # Model config
        model_config = self.config.get_model_config()
        assert model_config["provider"] == "openai"
        assert model_config["name"] == "gpt-4o-mini"

        # Browser config
        browser_config = self.config.get_browser_config()
        assert browser_config["browser"] == "chromium"
        assert browser_config["viewport"]["width"] == 1280

        # Output config
        output_config = self.config.get_output_config()
        assert output_config["format"] == "json"
        assert output_config["verbose"] is False
