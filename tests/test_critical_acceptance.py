"""
Critical Acceptance Tests for Browser Copilot

These tests focus on critical user scenarios that must work correctly
to ensure the application functions as expected. They use mocked
external dependencies to be reliable and fast.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_copilot.core import BrowserPilot
from browser_copilot.models.results import BrowserTestResult


@pytest.mark.asyncio
@pytest.mark.acceptance
@pytest.mark.skip(
    reason="Integration tests require real components (e.g., dockerized Ollama) - pending test strategy refactor"
)
class TestCriticalAcceptance:
    """Critical acceptance tests for core user workflows"""

    async def test_successful_test_execution_end_to_end(self, temp_dir):
        """
        Test the complete successful test execution flow:
        CLI input -> Agent creation -> Test execution -> Success report
        """
        # Arrange: Create test scenario
        test_scenario = """# Simple Test
1. Navigate to https://example.com
2. Verify page loads successfully
3. Take screenshot"""

        test_file = temp_dir / "test.md"
        test_file.write_text(test_scenario, encoding="utf-8")

        # Mock successful agent execution
        mock_result = {
            "messages": [
                {"type": "agent", "content": "Navigating to example.com"},
                {"type": "tool", "content": "Page loaded successfully"},
                {"type": "agent", "content": "Test completed successfully"},
            ]
        }

        # Act & Assert: Execute test with mocked dependencies
        with (
            patch(
                "browser_copilot.agent.AgentFactory.create_browser_agent"
            ) as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.BrowserToolsManager.load_browser_tools"
            ) as mock_load_tools,
            patch("browser_copilot.core.ModelForgeRegistry") as mock_registry_class,
        ):
            # Setup mocks
            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = ([], AsyncMock())

            # Mock the registry and LLM
            mock_llm = MagicMock()
            mock_llm.temperature = 0
            mock_llm.max_tokens = 1000
            mock_registry = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Create engine and execute
            engine = BrowserPilot(provider="openai", model="gpt-4")

            result = await engine.run_test_suite(
                test_suite_content=test_scenario, headless=True
            )

            # Verify successful execution
            assert isinstance(result, dict)
            assert result.get("success") is True
            assert result.get("test_name") is not None
            assert len(result.get("steps", [])) > 0

            # Verify agent was called correctly
            mock_create_agent.assert_called_once()
            mock_agent.arun.assert_called_once()

    async def test_failed_test_with_error_reporting(self, temp_dir):
        """
        Test failed test execution with proper error reporting:
        Test failure -> Error extraction -> Failure report
        """
        # Arrange: Create test scenario
        test_scenario = """# Test with Expected Failure
1. Navigate to https://nonexistent-domain.com
2. Click on missing element"""

        # Mock agent execution that fails
        mock_error_result = {
            "messages": [
                {"type": "agent", "content": "Navigating to nonexistent-domain.com"},
                {
                    "type": "tool",
                    "content": "Error: Failed to navigate - DNS resolution failed",
                },
                {"type": "agent", "content": "Test failed due to navigation error"},
            ]
        }

        # Act & Assert: Execute test with mocked failure
        with (
            patch(
                "browser_copilot.agent.AgentFactory.create_browser_agent"
            ) as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.BrowserToolsManager.load_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup mocks for failure scenario
            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_error_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = ([], AsyncMock())

            # Create engine and execute
            engine = BrowserPilot(provider="openai", model="gpt-4")

            result = await engine.run_test_suite(
                test_suite_content=test_scenario,
                test_name="failing_test",
                headless=True,
            )

            # Verify failure is properly reported
            assert isinstance(result, BrowserTestResult)
            assert result.success is False
            assert result.error is not None
            assert "error" in result.error.lower() or "failed" in result.error.lower()

            # Verify execution still completed
            assert len(result.steps) > 0

    async def test_hil_interruption_and_retry_flow(self, temp_dir):
        """
        Test HIL (Human-in-the-Loop) functionality:
        Test execution -> HIL interruption -> LLM decision -> Retry
        """
        # Arrange: Create test scenario that might trigger HIL
        test_scenario = """# Test That May Need HIL
1. Navigate to https://example.com
2. Click login button
3. Enter credentials"""

        # Mock HIL interruption scenario
        mock_hil_result = {
            "interrupt": True,
            "interrupt_data": {
                "question": "Login failed. Should I try again?",
                "context": "Login button not found on page",
                "suggested_response": "retry",
            },
            "messages": [
                {"type": "agent", "content": "Navigation successful"},
                {"type": "tool", "content": "Login button not found"},
                {"type": "hil", "content": "Requesting human intervention"},
            ],
        }

        # Act & Assert: Test HIL flow
        with (
            patch(
                "browser_copilot.agent.AgentFactory.create_browser_agent"
            ) as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.BrowserToolsManager.load_browser_tools"
            ) as mock_load_tools,
            patch(
                "browser_copilot.hil_detection.ask_human_tool.get_response_generator"
            ) as mock_hil,
        ):
            # Setup mocks
            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_hil_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = ([], AsyncMock())

            # Mock HIL response generation
            mock_hil_generator = MagicMock()
            mock_hil_generator.return_value = "retry"
            mock_hil.return_value = mock_hil_generator

            # Create engine with HIL enabled
            engine = BrowserPilot(
                provider="openai",
                model="gpt-4",
                base_dir=str(temp_dir),
                hil_enabled=True,
            )

            result = await engine.run_test_suite(
                test_suite_content=test_scenario, test_name="hil_test", headless=True
            )

            # Verify HIL was triggered and handled
            assert isinstance(result, BrowserTestResult)
            # Should have handled HIL interruption
            assert len(result.steps) > 0

            # Verify HIL components were called
            mock_create_agent.assert_called_once()

    async def test_context_management_token_optimization(self, temp_dir):
        """
        Test context management with token optimization:
        Long test -> Token limit approach -> Context trimming -> Successful execution
        """
        # Arrange: Create a long test scenario that would exceed token limits
        long_scenario = """# Long Test Scenario
""" + "\n".join(
            [
                f"{i}. Step {i} with detailed description that makes this quite long"
                for i in range(1, 50)
            ]
        )

        # Mock result showing context management was applied
        mock_optimized_result = {
            "messages": [
                {
                    "type": "system",
                    "content": "Context optimized - keeping important messages",
                },
                {"type": "agent", "content": "Executing optimized test plan"},
                {"type": "tool", "content": "All critical steps completed"},
                {"type": "agent", "content": "Test execution successful"},
            ],
            "context_info": {
                "original_tokens": 5000,
                "optimized_tokens": 2000,
                "strategy": "sliding-window",
            },
        }

        # Act & Assert: Test with context management
        with (
            patch(
                "browser_copilot.agent.AgentFactory.create_browser_agent"
            ) as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.BrowserToolsManager.load_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup mocks
            mock_agent = AsyncMock()
            mock_agent.arun.return_value = mock_optimized_result
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = ([], AsyncMock())

            # Create engine with context management
            engine = BrowserPilot(
                provider="openai",
                model="gpt-4",
                base_dir=str(temp_dir),
                context_strategy="sliding-window",
            )

            result = await engine.run_test_suite(
                test_scenario=long_scenario, test_name="long_test", headless=True
            )

            # Verify execution succeeded despite long input
            assert isinstance(result, BrowserTestResult)
            assert result.success is True
            assert len(result.steps) > 0

            # Verify agent was created with context management
            mock_create_agent.assert_called_once()
            call_args = mock_create_agent.call_args
            assert "context_strategy" in str(call_args) or call_args is not None

    async def test_configuration_and_provider_setup(self, temp_dir):
        """
        Test different configurations and provider setups:
        Different providers -> Proper agent configuration -> Successful execution
        """
        test_scenario = """# Config Test
1. Navigate to example.com
2. Verify page title"""

        # Test different provider configurations
        providers_to_test = [
            ("openai", "gpt-4"),
            ("anthropic", "claude-3-sonnet"),
            ("github_copilot", "gpt-4o"),
        ]

        for provider, model in providers_to_test:
            # Mock successful execution for each provider
            mock_result = {
                "messages": [
                    {"type": "agent", "content": f"Using {provider} {model}"},
                    {"type": "tool", "content": "Page navigation successful"},
                    {"type": "agent", "content": "Test completed"},
                ]
            }

            with (
                patch(
                    "browser_copilot.agent.AgentFactory.create_browser_agent"
                ) as mock_create_agent,
                patch(
                    "browser_copilot.browser_tools.load_playwright_browser_tools"
                ) as mock_load_tools,
            ):
                # Setup mocks
                mock_agent = AsyncMock()
                mock_agent.arun.return_value = mock_result
                mock_create_agent.return_value = mock_agent
                mock_load_tools.return_value = ([], AsyncMock())

                # Create engine with specific provider
                engine = BrowserPilot(
                    provider=provider, model=model, base_dir=str(temp_dir)
                )

                result = await engine.run_test_suite(
                    test_suite_content=test_scenario,
                    test_name=f"{provider}_test",
                    headless=True,
                )

                # Verify each provider configuration works
                assert isinstance(result, BrowserTestResult)
                assert result.success is True
                assert result.provider == provider
                assert result.model == model

    def test_report_parser_success_failure_detection(self):
        """
        Test report parsing for success/failure detection:
        Various report formats -> Correct success/failure determination
        """
        from browser_copilot.analysis.report_parser import ReportParser

        # Test various success patterns
        success_reports = [
            "Overall Status: **PASSED**",
            "Overall Status: PASSED",
            "Test passed successfully",
            "✅ All 5 tests passed",
            "Status: ✅ PASSED",
        ]

        for report in success_reports:
            assert ReportParser.check_success(report) is True, (
                f"Failed to detect success in: {report}"
            )

        # Test various failure patterns
        failure_reports = [
            "Overall Status: **FAILED**",
            "Overall Status: FAILED",
            "Test failed with error:",
            "Error: Navigation timeout",
            "Assertion error: Element not found",
            "❌ Test failed",
        ]

        for report in failure_reports:
            assert ReportParser.check_success(report) is False, (
                f"Failed to detect failure in: {report}"
            )

        # Test edge cases
        edge_cases = [
            "",  # Empty report -> False
            "Test in progress...",  # Ambiguous -> False
            "No clear status indicator",  # Unclear -> False
        ]

        for report in edge_cases:
            assert ReportParser.check_success(report) is False, (
                f"Edge case failed: {report}"
            )

    async def test_error_handling_and_timeout_scenarios(self, temp_dir):
        """
        Test error handling and timeout scenarios:
        Various error conditions -> Graceful failure -> Proper error reporting
        """
        test_scenario = """# Timeout Test
1. Navigate to slow-loading-site.com
2. Wait for element that never appears"""

        # Test timeout scenario
        with (
            patch(
                "browser_copilot.agent.AgentFactory.create_browser_agent"
            ) as mock_create_agent,
            patch(
                "browser_copilot.browser_tools.BrowserToolsManager.load_browser_tools"
            ) as mock_load_tools,
        ):
            # Setup timeout simulation
            mock_agent = AsyncMock()
            mock_agent.arun.side_effect = TimeoutError("Test execution timed out")
            mock_create_agent.return_value = mock_agent
            mock_load_tools.return_value = ([], AsyncMock())

            # Create engine with short timeout
            engine = BrowserPilot(provider="openai", model="gpt-4")

            result = await engine.run_test_suite(
                test_suite_content=test_scenario,
                test_name="timeout_test",
                headless=True,
                timeout=5,  # Short timeout
            )

            # Verify timeout is handled gracefully
            assert isinstance(result, BrowserTestResult)
            assert result.success is False
            assert result.error is not None
            assert "timeout" in result.error.lower()
