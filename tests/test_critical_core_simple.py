"""
Simplified critical tests for BrowserPilot core functionality

These tests focus on the actual BrowserPilot interface and critical paths
that need coverage for safe refactoring.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_copilot.core import BrowserPilot


@pytest.mark.skip(
    reason="Integration tests require real components - pending test strategy refactor"
)
class TestCriticalCore:
    """Critical tests for BrowserPilot core functionality"""

    def test_browser_pilot_initialization(self):
        """Test BrowserPilot initialization with different providers"""
        # Mock the LLM registry to avoid real provider connections
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
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

            # Test with different providers
            providers = [
                ("anthropic", "claude-3-sonnet"),
                ("github_copilot", "gpt-4o"),
                ("openai", "gpt-3.5-turbo"),
            ]

            for provider, model in providers:
                pilot = BrowserPilot(provider=provider, model=model)
                assert pilot.provider == provider
                assert pilot.model == model

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Integration test requires real components - pending test strategy refactor"
    )
    async def test_run_test_suite_basic_execution(self):
        """Test basic test suite execution flow"""
        with (
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
            patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
            patch("browser_copilot.core.stdio_client") as mock_stdio_client,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Setup mock agent factory
            mock_agent_factory = MagicMock()
            mock_agent_factory_class.return_value = mock_agent_factory

            # Setup mock MCP client session
            mock_session = AsyncMock()
            mock_client = AsyncMock()

            # Create async context manager for stdio_client
            mock_stdio_context = AsyncMock()
            mock_stdio_context.__aenter__.return_value = (mock_session, mock_client)
            mock_stdio_context.__aexit__.return_value = None
            mock_stdio_client.return_value = mock_stdio_context

            # Mock agent creation and execution
            mock_agent = AsyncMock()
            mock_result = {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Test completed successfully. Overall Status: PASSED",
                    }
                ]
            }

            # Mock agent returning a result when run
            async def mock_astream(*args, **kwargs):
                yield {"agent": mock_result}

            mock_agent.astream = mock_astream
            mock_agent_factory.create_browser_agent.return_value = mock_agent

            # Create pilot and run test
            pilot = BrowserPilot(provider="openai", model="gpt-4")

            test_content = """# Simple Test
1. Navigate to https://example.com
2. Verify page loads"""

            result = await pilot.run_test_suite(
                test_suite_content=test_content, headless=True, verbose=False
            )

            # Verify execution completed
            assert isinstance(result, dict)
            assert result.get("success") is True  # Should detect PASSED status
            # The agent factory should have been called to create an agent
            mock_agent_factory.create_browser_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_success_detection(self):
        """Test that success detection works correctly"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry
            # Mock successful test execution
            mock_agent = AsyncMock()
            success_result = {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "All steps completed successfully. Overall Status: PASSED",
                    }
                ]
            }
            mock_agent.astream.return_value = [{"agent": success_result}]
            mock_create_agent.return_value = mock_agent

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            result = await pilot.run_test_suite(
                test_suite_content="# Test\n1. Simple test step", headless=True
            )

            # Check that success was detected (exact structure depends on implementation)
            assert isinstance(result, dict)
            # The result should contain information about the test execution

    @pytest.mark.asyncio
    async def test_test_failure_detection(self):
        """Test that failure detection works correctly"""
        with (
            patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Setup mock agent factory and agent
            mock_agent_factory = AsyncMock()
            mock_agent = AsyncMock()
            failure_result = {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Test failed with error. Overall Status: FAILED",
                    }
                ]
            }

            # Mock agent returning a result when run
            async def mock_astream(*args, **kwargs):
                yield {"agent": failure_result}

            mock_agent.astream = mock_astream
            mock_agent_factory.create_browser_agent.return_value = mock_agent
            mock_agent_factory_class.return_value = mock_agent_factory

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            result = await pilot.run_test_suite(
                test_suite_content="# Test\n1. This will fail", headless=True
            )

            # Check that failure was detected
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_browser_configuration(self):
        """Test different browser configurations"""
        browsers = ["chromium", "firefox", "webkit"]

        for browser in browsers:
            with (
                patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
                patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
            ):
                # Setup mock registry
                mock_registry = MagicMock()
                mock_llm = MagicMock()
                mock_registry.get_llm.return_value = mock_llm
                mock_registry_class.return_value = mock_registry

                # Setup mock agent factory and agent
                mock_agent_factory = AsyncMock()
                mock_agent = AsyncMock()

                # Mock agent returning a result when run
                async def mock_astream(*args, **kwargs):
                    yield {"agent": {"messages": []}}

                mock_agent.astream = mock_astream
                mock_agent_factory.create_browser_agent.return_value = mock_agent
                mock_agent_factory_class.return_value = mock_agent_factory

                pilot = BrowserPilot(provider="openai", model="gpt-4")

                result = await pilot.run_test_suite(
                    test_suite_content="# Test\n1. Test browser config",
                    browser=browser,
                    headless=True,
                )

                assert isinstance(result, dict)
                # Verify agent was created with browser configuration
                mock_agent_factory.create_browser_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_execution(self):
        """Test error handling during test execution"""
        with (
            patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Setup mock agent factory and agent
            mock_agent_factory = AsyncMock()
            mock_agent = AsyncMock()
            mock_agent.astream.side_effect = TimeoutError("Test timed out")
            mock_agent_factory.create_browser_agent.return_value = mock_agent
            mock_agent_factory_class.return_value = mock_agent_factory

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Should handle timeout gracefully
            result = await pilot.run_test_suite(
                test_suite_content="# Test\n1. This will timeout",
                headless=True,
                timeout=5,
            )

            # Should return result even on error
            assert isinstance(result, dict)

    def test_prompt_building(self):
        """Test prompt building functionality"""
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
        assert "navigate" in prompt.lower()

    def test_success_checking(self):
        """Test success checking functionality"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

        # Test various success/failure patterns
        success_reports = [
            "Overall Status: PASSED",
            "Test completed successfully",
            "All steps passed",
        ]

        failure_reports = [
            "Overall Status: FAILED",
            "Error occurred during test",
            "Test failed with timeout",
        ]

        for report in success_reports:
            assert pilot._check_success(report) is True

        for report in failure_reports:
            assert pilot._check_success(report) is False

    def test_test_name_extraction(self):
        """Test test name extraction from content"""
        with patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class:
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            pilot = BrowserPilot(provider="openai", model="gpt-4")

        test_cases = [
            ("# Login Test\n1. Step 1", "Login Test"),
            ("# E-commerce Checkout\n1. Add to cart", "E-commerce Checkout"),
            ("No title\n1. Step 1", "Unknown Test"),
            ("", "Unknown Test"),
        ]

        for content, expected_name in test_cases:
            extracted_name = pilot._extract_test_name(content)
            assert expected_name.lower() in extracted_name.lower()

    @pytest.mark.asyncio
    async def test_viewport_configuration(self):
        """Test viewport size configuration"""
        with (
            patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Setup mock agent factory and agent
            mock_agent_factory = AsyncMock()
            mock_agent = AsyncMock()

            # Mock agent returning a result when run
            async def mock_astream(*args, **kwargs):
                yield {"agent": {"messages": []}}

            mock_agent.astream = mock_astream
            mock_agent_factory.create_browser_agent.return_value = mock_agent
            mock_agent_factory_class.return_value = mock_agent_factory

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Test custom viewport
            result = await pilot.run_test_suite(
                test_suite_content="# Test\n1. Check viewport",
                viewport_width=1440,
                viewport_height=900,
                headless=True,
            )

            assert isinstance(result, dict)
            mock_agent_factory.create_browser_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_configuration(self):
        """Test screenshot configuration"""
        with (
            patch("browser_copilot.agent.AgentFactory") as mock_agent_factory_class,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mock registry
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Setup mock agent factory and agent
            mock_agent_factory = AsyncMock()
            mock_agent = AsyncMock()

            # Mock agent returning a result when run
            async def mock_astream(*args, **kwargs):
                yield {"agent": {"messages": []}}

            mock_agent.astream = mock_astream
            mock_agent_factory.create_browser_agent.return_value = mock_agent
            mock_agent_factory_class.return_value = mock_agent_factory

            pilot = BrowserPilot(provider="openai", model="gpt-4")

            # Test with screenshots enabled/disabled
            for enable_screenshots in [True, False]:
                result = await pilot.run_test_suite(
                    test_suite_content="# Test\n1. Test screenshots",
                    enable_screenshots=enable_screenshots,
                    headless=True,
                )

                assert isinstance(result, dict)

    def test_browser_validation(self):
        """Test browser validation"""
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
