"""
Simplified critical tests for BrowserPilot core functionality

These tests focus on testing the BrowserPilot class without complex mocking
of the entire agent execution pipeline. They test initialization, configuration,
and basic method calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from browser_copilot.core import BrowserPilot


class TestCriticalCoreSimplified:
    """Simplified critical tests for BrowserPilot"""

    def test_browser_pilot_initialization_basic(self):
        """Test BrowserPilot basic initialization without provider connection"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Test basic initialization
            pilot = BrowserPilot(provider="openai", model="gpt-4")
            assert pilot.provider == "openai"
            assert pilot.model == "gpt-4"
            assert pilot.config is not None
            assert pilot.stream is not None

    def test_browser_pilot_initialization_different_providers(self):
        """Test initialization with different providers"""
        providers = [
            ("anthropic", "claude-3-sonnet"),
            ("github_copilot", "gpt-4o"),
            ("openai", "gpt-3.5-turbo"),
        ]

        for provider, model in providers:
            with patch(
                "browser_copilot.core.ModelForgeRegistry"
            ) as mock_registry_class:
                # Setup mock registry
                mock_registry = MagicMock()
                mock_llm = MagicMock()
                mock_registry.get_llm.return_value = mock_llm
                mock_registry_class.return_value = mock_registry

                pilot = BrowserPilot(provider=provider, model=model)
                assert pilot.provider == provider
                assert pilot.model == model

    def test_prompt_building_method(self):
        """Test internal prompt building method"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            test_content = """# Login Test
1. Navigate to login page
2. Enter credentials
3. Click login button"""

            # Test internal prompt building method
            prompt = pilot._build_prompt(test_content)

            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "login" in prompt.lower()
            assert "navigate" in prompt.lower() or "goto" in prompt.lower()

    def test_success_checking_method(self):
        """Test internal success checking method"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Test various success/failure patterns that match ReportParser logic
            success_reports = [
                "overall status:**passed",  # Matches the regex pattern
                "overall status: passed",  # With space, should work
                "test passed successfully",  # Alternative pattern
            ]

            failure_reports = [
                "overall status:**failed",  # Matches the regex pattern
                "overall status: failed",  # With space, should work
                "test failed with error",  # Alternative pattern
            ]

            for report in success_reports:
                assert pilot._check_success(report) is True

            for report in failure_reports:
                assert pilot._check_success(report) is False

    def test_test_name_extraction_method(self):
        """Test internal test name extraction method"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            test_cases = [
                ("# Login Test\\n1. Step 1", "Login Test"),
                ("# E-commerce Checkout\\n1. Add to cart", "E-commerce Checkout"),
                ("No title\\n1. Step 1", "Browser Test"),
                ("", "Browser Test"),
            ]

            for content, expected_name in test_cases:
                extracted_name = pilot._extract_test_name(content)
                assert expected_name.lower() in extracted_name.lower()

    def test_browser_validation_method(self):
        """Test internal browser validation method"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            valid_browsers = pilot._get_valid_browsers()

            assert isinstance(valid_browsers, list)
            assert len(valid_browsers) > 0
            assert "chromium" in valid_browsers

            # Standard browsers should be supported
            for browser in ["chromium", "firefox", "webkit"]:
                assert browser in valid_browsers

    def test_configuration_attributes(self):
        """Test that basic configuration attributes are properly set"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Test with custom system prompt
            custom_prompt = "Custom test automation prompt"
            pilot = BrowserPilot(
                provider="openai", model="gpt-4", system_prompt=custom_prompt
            )

            assert pilot.provider == "openai"
            assert pilot.model == "gpt-4"
            assert pilot.system_prompt == custom_prompt
            assert pilot.config is not None
            assert pilot.stream is not None

    def test_registry_and_llm_initialization(self):
        """Test that registry and LLM are properly initialized"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Verify registry was created and LLM was requested
            mock_registry_class.assert_called_once()
            # Check that get_llm was called with correct provider and model
            call_args = mock_registry.get_llm.call_args
            assert call_args.kwargs["provider_name"] == "openai"
            assert call_args.kwargs["model_alias"] == "gpt-4"

            # Verify LLM and registry are stored
            assert pilot.registry == mock_registry
            assert pilot.llm == mock_llm

    def test_agent_factory_initialization(self):
        """Test that agent factory is properly initialized"""
        with (
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
            patch("browser_copilot.core.AgentFactory") as mock_agent_factory_class,
        ):
            # Setup mocks
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            mock_agent_factory = MagicMock()
            mock_agent_factory_class.return_value = mock_agent_factory

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Verify agent factory was created with correct parameters
            mock_agent_factory_class.assert_called_once_with(
                mock_llm, "openai", "gpt-4"
            )

            # Verify agent factory is stored
            assert pilot.agent_factory == mock_agent_factory

    def test_error_handling_in_initialization(self):
        """Test error handling during initialization"""
        from modelforge.exceptions import ProviderError

        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry to raise a specific ModelForge error
            mock_registry = MagicMock()
            mock_registry.get_llm.side_effect = ProviderError("Provider not found")
            mock_registry_class.return_value = mock_registry

            # Should raise RuntimeError with helpful message
            with pytest.raises(RuntimeError) as exc_info:
                BrowserPilot(provider="invalid", model="invalid")

            assert "Failed to load LLM" in str(exc_info.value)
            assert "Provider not found" in str(exc_info.value)
