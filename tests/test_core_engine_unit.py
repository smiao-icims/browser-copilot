"""
Unit tests for core execution engine (core.py)

These tests focus on unit testing individual methods and configurations
without running the full integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from browser_copilot.config_manager import ConfigManager
from browser_copilot.core import BrowserPilot


class TestBrowserPilotUnit:
    """Unit tests for BrowserPilot class"""

    def test_initialization_basic(self):
        """Test basic BrowserPilot initialization"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock the registry
            mock_llm = MagicMock()
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_llm.return_value = mock_llm
            mock_registry.return_value = mock_registry_instance

            # Create engine
            engine = BrowserPilot(provider="openai", model="gpt-4")

            # Verify basic attributes
            assert engine.provider == "openai"
            assert engine.model == "gpt-4"
            assert engine.llm == mock_llm
            assert hasattr(engine, "agent_factory")

    def test_initialization_with_config(self):
        """Test BrowserPilot initialization with ConfigManager"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock the registry
            mock_llm = MagicMock()
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_llm.return_value = mock_llm
            mock_registry.return_value = mock_registry_instance

            # Create config
            config = ConfigManager()
            config.set("browser", "firefox")
            config.set("headless", True)
            config.set("context_strategy", "sliding-window")
            config.set("hil", True)
            config.set("verbose", True)

            # Create engine
            engine = BrowserPilot(
                provider="anthropic", model="claude-3-sonnet", config=config
            )

            # Verify attributes
            assert engine.provider == "anthropic"
            assert engine.model == "claude-3-sonnet"
            assert engine.config.get("browser") == "firefox"
            assert engine.config.get("headless") is True
            assert engine.config.get("context_strategy") == "sliding-window"
            assert engine.config.get("hil") is True
            assert engine.config.get("verbose") is True

    def test_initialization_with_system_prompt(self):
        """Test BrowserPilot initialization with custom system prompt"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock the registry
            mock_llm = MagicMock()
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_llm.return_value = mock_llm
            mock_registry.return_value = mock_registry_instance

            # Create engine with custom prompt
            custom_prompt = "You are a specialized test agent"
            engine = BrowserPilot(
                provider="openai", model="gpt-4", system_prompt=custom_prompt
            )

            # Verify system prompt was stored
            assert hasattr(engine, "system_prompt")

    def test_initialization_error_handling(self):
        """Test BrowserPilot initialization error handling"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock registry instance to raise error on get_llm
            mock_registry_instance = MagicMock()
            from modelforge.exceptions import ProviderError

            mock_registry_instance.get_llm.side_effect = ProviderError(
                "Provider not available"
            )
            mock_registry.return_value = mock_registry_instance

            # Verify error is raised properly
            with pytest.raises(RuntimeError) as exc_info:
                BrowserPilot(provider="invalid", model="invalid")

            assert "Failed to load LLM" in str(exc_info.value)

    def test_agent_factory_creation(self):
        """Test that AgentFactory is properly created"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            with patch("browser_copilot.core.AgentFactory") as mock_factory_class:
                # Mock the registry
                mock_llm = MagicMock()
                mock_registry_instance = MagicMock()
                mock_registry_instance.get_llm.return_value = mock_llm
                mock_registry.return_value = mock_registry_instance

                # Create engine
                BrowserPilot(provider="openai", model="gpt-4")

                # Verify AgentFactory was created with correct params
                mock_factory_class.assert_called_once_with(mock_llm, "openai", "gpt-4")

    def test_config_defaults(self):
        """Test that default config values are set properly"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock the registry
            mock_llm = MagicMock()
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_llm.return_value = mock_llm
            mock_registry.return_value = mock_registry_instance

            # Create engine without config
            engine = BrowserPilot(provider="openai", model="gpt-4")

            # Verify we have a config
            assert engine.config is not None
            assert hasattr(engine.config, "get")

            # Verify HIL is enabled by default (most important default)
            assert engine.config.get("hil") is True

    def test_stream_handler_initialization(self):
        """Test StreamHandler initialization"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry:
            # Mock the registry
            mock_llm = MagicMock()
            mock_registry_instance = MagicMock()
            mock_registry_instance.get_llm.return_value = mock_llm
            mock_registry.return_value = mock_registry_instance

            # Create engine
            engine = BrowserPilot(provider="openai", model="gpt-4")

            # Verify StreamHandler was created if not provided
            assert hasattr(engine, "stream")
