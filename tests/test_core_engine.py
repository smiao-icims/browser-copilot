"""
Tests for core execution engine (core.py)

These tests focus on the critical paths in BrowserPilot
that currently have very low test coverage (8%).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_copilot.core import BrowserPilot
from browser_copilot.models.results import BrowserTestResult


@pytest.mark.asyncio
class TestCoreEngine:
    """Test the core execution engine functionality"""

    async def test_engine_initialization_with_different_configs(self, temp_dir):
        """Test engine initialization with various configurations"""
        # Test basic initialization
        engine = BrowserPilot(provider="openai", model="gpt-4", base_dir=str(temp_dir))

        assert engine.provider == "openai"
        assert engine.model == "gpt-4"
        assert engine.base_dir == str(temp_dir)

        # Test with full configuration
        engine_full = BrowserPilot(
            provider="anthropic",
            model="claude-3-sonnet",
            base_dir=str(temp_dir),
            browser="firefox",
            headless=True,
            context_strategy="sliding-window",
            hil_enabled=True,
            verbose=True,
        )

        assert engine_full.provider == "anthropic"
        assert engine_full.model == "claude-3-sonnet"
        assert engine_full.browser == "firefox"
        assert engine_full.headless is True
        assert engine_full.context_strategy == "sliding-window"
        assert engine_full.hil_enabled is True
        assert engine_full.verbose is True

    async def test_agent_creation_and_configuration(self, temp_dir):
        """Test agent creation with different configurations"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup mocks
            mock_agent = AsyncMock()
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = []

            engine = BrowserPilot(
                provider="openai",
                model="gpt-4",
                base_dir=str(temp_dir),
                context_strategy="sliding-window",
                hil_enabled=True,
            )

            # Trigger agent creation by running a test
            test_scenario = "1. Navigate to example.com"
            mock_agent.arun.return_value = {"messages": []}

            await engine.run_test_suite(
                test_scenario=test_scenario, test_name="test", headless=True
            )

            # Verify agent was created with correct parameters
            mock_create_agent.assert_called_once()
            call_kwargs = mock_create_agent.call_args.kwargs

            # Check key parameters were passed
            assert "context_strategy" in call_kwargs
            assert "hil_enabled" in call_kwargs
            assert call_kwargs["hil_enabled"] is True

    async def test_test_execution_orchestration(self, temp_dir):
        """Test the main test execution orchestration logic"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup detailed mock response
            mock_result = {
                "messages": [
                    {"type": "human", "content": "Navigate to example.com"},
                    {"type": "ai", "content": "I'll navigate to example.com"},
                    {
                        "type": "tool",
                        "name": "browser_navigate",
                        "content": "Navigation successful",
                    },
                    {"type": "ai", "content": "Navigation completed successfully"},
                ]
            }

            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = [MagicMock()]

            engine = BrowserPilot(
                provider="openai", model="gpt-4", base_dir=str(temp_dir)
            )

            # Execute test
            result = await engine.run_test_suite(
                test_scenario="1. Navigate to example.com\n2. Verify page loads",
                test_name="orchestration_test",
                headless=True,
            )

            # Verify execution flow
            assert isinstance(result, BrowserTestResult)
            assert result.test_name == "orchestration_test"
            assert len(result.steps) > 0

            # Verify timing information
            assert result.duration > 0
            assert result.steps_executed >= 0

            # Verify agent interaction
            mock_agent.arun.assert_called_once()

    async def test_error_handling_in_execution(self, temp_dir):
        """Test error handling during test execution"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Test various error scenarios
            error_scenarios = [
                (Exception("General error"), "General error"),
                (TimeoutError("Test timeout"), "timeout"),
                (KeyboardInterrupt(), "interrupted"),
                (RuntimeError("Runtime issue"), "Runtime issue"),
            ]

            for error, expected_in_message in error_scenarios:
                mock_agent = AsyncMock()
                mock_agent.arun.side_effect = error
                mock_create_agent.return_value = mock_agent
                mock_load_tools.return_value = []

                engine = BrowserPilot(
                    provider="openai", model="gpt-4", base_dir=str(temp_dir)
                )

                result = await engine.run_test_suite(
                    test_scenario="1. This will fail",
                    test_name="error_test",
                    headless=True,
                )

                # Verify error is properly handled
                assert isinstance(result, BrowserTestResult)
                assert result.success is False
                assert result.error is not None

                # For non-interrupt errors, check error message content
                if not isinstance(error, KeyboardInterrupt):
                    assert expected_in_message.lower() in result.error.lower()

    async def test_hil_integration_in_core(self, temp_dir):
        """Test HIL integration within the core engine"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Mock HIL interruption scenario
            mock_agent = AsyncMock()

            # First call triggers HIL interruption
            interrupt_result = {
                "interrupt": True,
                "messages": [
                    {"type": "ai", "content": "Need human input"},
                    {"type": "tool", "content": "HIL interruption triggered"},
                ],
            }

            # Second call after HIL resolution
            continue_result = {
                "messages": [
                    {"type": "ai", "content": "Continuing after HIL"},
                    {"type": "tool", "content": "Test completed"},
                ]
            }

            mock_agent.arun.side_effect = [interrupt_result, continue_result]
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = []

            # Create engine with HIL enabled
            engine = BrowserPilot(
                provider="openai",
                model="gpt-4",
                base_dir=str(temp_dir),
                hil_enabled=True,
            )

            result = await engine.run_test_suite(
                test_scenario="1. Action that triggers HIL",
                test_name="hil_integration_test",
                headless=True,
            )

            # Verify HIL was handled
            assert isinstance(result, BrowserTestResult)
            # Should have processed multiple interactions
            mock_agent.arun.call_count >= 1

    async def test_context_strategy_integration(self, temp_dir):
        """Test context management strategy integration"""
        strategies_to_test = ["no-op", "sliding-window", "smart-trim"]

        for strategy in strategies_to_test:
            with (
                patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
                patch(
                    "browser_copilot.browser_tools.load_playwright_browser_tools"
                ) as mock_load_tools,
            ):
                # Mock successful execution
                mock_result = {
                    "messages": [
                        {"type": "ai", "content": f"Using {strategy} strategy"},
                        {"type": "tool", "content": "Context managed successfully"},
                    ]
                }

                mock_agent = AsyncMock()
                mock_agent.arun.return_value = mock_result
                mock_create_agent.return_value = mock_agent
                mock_load_tools.return_value = []

                engine = BrowserPilot(
                    provider="openai",
                    model="gpt-4",
                    base_dir=str(temp_dir),
                    context_strategy=strategy,
                )

                result = await engine.run_test_suite(
                    test_scenario="1. Test with context management",
                    test_name=f"{strategy}_test",
                    headless=True,
                )

                # Verify execution succeeded with strategy
                assert isinstance(result, BrowserTestResult)
                assert result.success is True

                # Verify strategy was passed to agent creation
                mock_create_agent.assert_called_once()
                call_kwargs = mock_create_agent.call_args.kwargs
                assert "context_strategy" in call_kwargs

    async def test_browser_configuration_handling(self, temp_dir):
        """Test different browser configurations"""
        browsers_to_test = ["chromium", "firefox", "webkit"]

        for browser in browsers_to_test:
            with (
                patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
                patch(
                    "browser_copilot.browser_tools.load_playwright_browser_tools"
                ) as mock_load_tools,
            ):
                mock_result = {
                    "messages": [{"type": "ai", "content": f"Using {browser}"}]
                }

                mock_agent = AsyncMock()
                mock_agent.arun.return_value = mock_result
                mock_create_agent.return_value = mock_agent
                mock_load_tools.return_value = []

                engine = BrowserPilot(
                    provider="openai",
                    model="gpt-4",
                    base_dir=str(temp_dir),
                    browser=browser,
                )

                result = await engine.run_test_suite(
                    test_scenario="1. Test browser configuration",
                    test_name=f"{browser}_test",
                    headless=True,
                )

                # Verify browser configuration
                assert isinstance(result, BrowserTestResult)
                assert result.browser == browser

    async def test_result_compilation_and_metrics(self, temp_dir):
        """Test result compilation and metrics calculation"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Mock detailed execution with timing
            mock_result = {
                "messages": [
                    {"type": "human", "content": "Step 1"},
                    {"type": "ai", "content": "Executing step 1"},
                    {"type": "tool", "name": "browser_navigate", "content": "Success"},
                    {"type": "human", "content": "Step 2"},
                    {"type": "ai", "content": "Executing step 2"},
                    {"type": "tool", "name": "browser_click", "content": "Clicked"},
                    {"type": "ai", "content": "Test completed successfully"},
                ]
            }

            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = []

            engine = BrowserPilot(
                provider="openai", model="gpt-4", base_dir=str(temp_dir), verbose=True
            )

            # Execute test and measure
            import time

            start_time = time.time()

            result = await engine.run_test_suite(
                test_scenario="1. Navigate\n2. Click button\n3. Verify",
                test_name="metrics_test",
                headless=True,
            )

            end_time = time.time()

            # Verify result compilation
            assert isinstance(result, BrowserTestResult)

            # Verify timing metrics
            assert result.duration > 0
            assert result.duration <= (end_time - start_time) + 1  # Allow some margin

            # Verify step extraction
            assert len(result.steps) > 0

            # Verify metadata
            assert result.provider == "openai"
            assert result.model == "gpt-4"
            assert result.test_name == "metrics_test"

    async def test_concurrent_execution_safety(self, temp_dir):
        """Test that engine handles concurrent executions safely"""
        with (
            patch("browser_copilot.core.create_browser_agent") as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.load_playwright_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup mocks for concurrent execution
            mock_result = {
                "messages": [
                    {"type": "ai", "content": "Concurrent test execution"},
                    {"type": "tool", "content": "Test completed"},
                ]
            }

            async def mock_run(*args, **kwargs):
                # Simulate some async work
                await asyncio.sleep(0.1)
                return mock_result

            mock_agent = AsyncMock()
            mock_agent.arun = mock_run
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = []

            engine = BrowserPilot(
                provider="openai", model="gpt-4", base_dir=str(temp_dir)
            )

            # Execute multiple tests concurrently
            tasks = []
            for i in range(3):
                task = engine.run_test_suite(
                    test_scenario=f"1. Concurrent test {i}",
                    test_name=f"concurrent_test_{i}",
                    headless=True,
                )
                tasks.append(task)

            # Wait for all to complete
            results = await asyncio.gather(*tasks)

            # Verify all executions succeeded
            assert len(results) == 3
            for i, result in enumerate(results):
                assert isinstance(result, BrowserTestResult)
                assert result.test_name == f"concurrent_test_{i}"
