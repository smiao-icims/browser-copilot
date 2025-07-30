"""
Comprehensive tests for HIL (Human-in-the-Loop) system

This covers the ask_human tool and related HIL functionality
that currently has 0% coverage but is critical for interactive testing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_copilot.hil_detection.ask_human_tool import (
    ask_human,
    configure_hil_llm,
    confirm_action,
    generate_confirmation_response,
    generate_suggested_response,
    get_response_generator,
)


class TestHILSystemComprehensive:
    """Comprehensive tests for HIL system functionality"""

    def test_configure_hil_llm(self):
        """Test configuring HIL LLM settings"""
        # Test configuration with different providers
        configure_hil_llm("openai", "gpt-4")

        # Import the private config to verify
        from browser_copilot.hil_detection.ask_human_tool import _hil_config

        assert _hil_config["provider_name"] == "openai"
        assert _hil_config["model_alias"] == "gpt-4"

        # Test configuration change
        configure_hil_llm("anthropic", "claude-3")
        assert _hil_config["provider_name"] == "anthropic"
        assert _hil_config["model_alias"] == "claude-3"

    def test_get_response_generator_creation(self):
        """Test response generator LLM creation"""
        with patch(
            "browser_copilot.hil_detection.ask_human_tool.ModelForgeRegistry"
        ) as mock_registry_class:
            # Setup mock
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Reset cached generator
            import browser_copilot.hil_detection.ask_human_tool

            browser_copilot.hil_detection.ask_human_tool._response_generator = None

            # Get generator
            generator = get_response_generator()

            # Verify LLM was created with correct settings
            mock_registry.get_llm.assert_called_once()
            call_kwargs = mock_registry.get_llm.call_args.kwargs
            assert "provider_name" in call_kwargs
            assert "model_alias" in call_kwargs
            assert call_kwargs["enhanced"] is False

            # Verify temperature and max_tokens were set
            assert mock_llm.temperature == 0.3
            assert mock_llm.max_tokens == 100

            # Verify generator is cached
            generator2 = get_response_generator()
            assert generator is generator2

    @pytest.mark.asyncio
    async def test_generate_suggested_response_various_scenarios(self):
        """Test suggested response generation for different scenarios"""
        test_scenarios = [
            {
                "question": "What is your favorite color?",
                "context": None,
                "expected_type": str,
                "expected_reasonable": ["blue", "red", "green", "black"],
            },
            {
                "question": "Should I retry the login process or proceed with a different test scenario?",
                "context": "Login failed with incorrect credentials error",
                "expected_type": str,
                "expected_reasonable": ["retry", "proceed", "skip"],
            },
            {
                "question": "What search term should I use?",
                "context": "Testing search functionality",
                "expected_type": str,
                "expected_reasonable": ["test", "product", "example"],
            },
        ]

        with patch(
            "browser_copilot.hil_detection.ask_human_tool.get_response_generator"
        ) as mock_get_generator:
            # Setup mock LLM
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_get_generator.return_value = mock_llm

            for scenario in test_scenarios:
                # Configure mock response
                mock_response.content = scenario["expected_reasonable"][0]
                mock_llm.ainvoke.return_value = mock_response

                # Generate response
                response = await generate_suggested_response(
                    scenario["question"], scenario["context"]
                )

                # Verify response type
                assert isinstance(response, scenario["expected_type"])
                assert len(response) > 0

                # Verify prompt was constructed properly
                mock_llm.ainvoke.assert_called()
                prompt = mock_llm.ainvoke.call_args[0][0]
                assert scenario["question"] in prompt
                if scenario["context"]:
                    assert scenario["context"] in prompt

    @pytest.mark.asyncio
    async def test_generate_confirmation_response_scenarios(self):
        """Test confirmation response generation"""
        test_cases = [
            {
                "action": "Delete all items in shopping cart",
                "details": "This will clear 3 items from the test cart",
                "expected": True,  # Should confirm test operations
            },
            {
                "action": "Submit order with total $5000",
                "details": "Using test credit card ending in 4242",
                "expected": True,  # Test payment should be confirmed
            },
            {
                "action": "Proceed with checkout despite validation errors?",
                "details": "Missing required shipping address fields",
                "expected": False,  # Cannot proceed without required data
            },
        ]

        with patch(
            "browser_copilot.hil_detection.ask_human_tool.get_response_generator"
        ) as mock_get_generator:
            # Setup mock LLM
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_get_generator.return_value = mock_llm

            for test_case in test_cases:
                # Configure mock response
                mock_response.content = "yes" if test_case["expected"] else "no"
                mock_llm.ainvoke.return_value = mock_response

                # Generate confirmation
                result = await generate_confirmation_response(
                    test_case["action"], test_case["details"]
                )

                assert result == test_case["expected"]

                # Verify prompt included action and details
                prompt = mock_llm.ainvoke.call_args[0][0]
                assert test_case["action"] in prompt
                if test_case["details"]:
                    assert test_case["details"] in prompt

    @pytest.mark.asyncio
    async def test_ask_human_tool_with_interrupt(self):
        """Test ask_human tool with LangGraph interrupt mechanism"""
        with (
            patch(
                "browser_copilot.hil_detection.ask_human_tool.interrupt"
            ) as mock_interrupt,
            patch(
                "browser_copilot.hil_detection.ask_human_tool.generate_suggested_response"
            ) as mock_suggest,
        ):
            # Setup mocks
            mock_suggest.return_value = "suggested answer"
            mock_interrupt.return_value = "user response"

            # Call ask_human tool using invoke (LangChain tool interface)
            response = await ask_human.ainvoke(
                {
                    "question": "What is the test username?",
                    "context": "Need credentials for login test",
                }
            )

            # Verify interrupt was called with correct data
            mock_interrupt.assert_called_once()
            interrupt_data = mock_interrupt.call_args[0][0]

            assert interrupt_data["type"] == "human_question"
            assert interrupt_data["question"] == "What is the test username?"
            assert interrupt_data["context"] == "Need credentials for login test"
            assert interrupt_data["tool"] == "ask_human"
            assert interrupt_data["suggested_response"] == "suggested answer"

            # Verify response
            assert response == "user response"

    @pytest.mark.asyncio
    async def test_confirm_action_tool_with_interrupt(self):
        """Test confirm_action tool with interrupt mechanism"""
        with (
            patch(
                "browser_copilot.hil_detection.ask_human_tool.interrupt"
            ) as mock_interrupt,
            patch(
                "browser_copilot.hil_detection.ask_human_tool.generate_confirmation_response"
            ) as mock_confirm,
        ):
            # Setup mocks
            mock_confirm.return_value = True
            mock_interrupt.return_value = "yes"

            # Call confirm_action tool using invoke
            result = await confirm_action.ainvoke(
                {
                    "action": "Delete test account",
                    "details": "This will remove user 'test123'",
                }
            )

            # Verify interrupt was called
            mock_interrupt.assert_called_once()
            interrupt_data = mock_interrupt.call_args[0][0]

            assert interrupt_data["type"] == "confirmation_request"
            assert interrupt_data["action"] == "Delete test account"
            assert interrupt_data["details"] == "This will remove user 'test123'"
            assert interrupt_data["tool"] == "confirm_action"
            assert interrupt_data["suggested_response"] == "yes"

            # Verify result
            assert result is True

    @pytest.mark.asyncio
    async def test_confirmation_response_parsing(self):
        """Test parsing of confirmation responses"""
        with (
            patch(
                "browser_copilot.hil_detection.ask_human_tool.interrupt"
            ) as mock_interrupt,
            patch(
                "browser_copilot.hil_detection.ask_human_tool.generate_confirmation_response"
            ) as mock_confirm,
        ):
            mock_confirm.return_value = True

            # Test various response formats
            response_formats = [
                ("yes", True),
                ("YES", True),
                ("Yes", True),
                ("no", False),
                ("NO", False),
                ("n", False),
                ("y", True),
                ("true", True),
                ("false", False),
                ("invalid", False),  # Default to False for safety
            ]

            for response, expected in response_formats:
                mock_interrupt.return_value = response

                result = await confirm_action.ainvoke(
                    {"action": "Test action", "details": "Test details"}
                )
                assert result == expected

    @pytest.mark.asyncio
    async def test_error_handling_in_response_generation(self):
        """Test error handling when LLM fails"""
        with patch(
            "browser_copilot.hil_detection.ask_human_tool.get_response_generator"
        ) as mock_get_generator:
            # Setup mock to raise error
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("LLM API error")
            mock_get_generator.return_value = mock_llm

            # Test suggested response with error
            response = await generate_suggested_response(
                "What color?", "Testing error handling"
            )

            # Should return a reasonable default
            assert isinstance(response, str)
            assert len(response) > 0

            # Test confirmation with error
            confirmation = await generate_confirmation_response(
                "Delete item?", "Error test"
            )

            # Should default to True for test automation (to keep tests moving)
            assert confirmation is True

    def test_hil_config_persistence(self):
        """Test that HIL configuration persists across calls"""
        # Configure with specific settings
        configure_hil_llm("custom_provider", "custom_model")

        # Import and check config
        from browser_copilot.hil_detection.ask_human_tool import _hil_config

        assert _hil_config["provider_name"] == "custom_provider"
        assert _hil_config["model_alias"] == "custom_model"

        # Create new generator should use these settings
        with patch(
            "browser_copilot.hil_detection.ask_human_tool.ModelForgeRegistry"
        ) as mock_registry_class:
            mock_registry = MagicMock()
            mock_llm = MagicMock()
            mock_registry.get_llm.return_value = mock_llm
            mock_registry_class.return_value = mock_registry

            # Reset generator to force recreation
            import browser_copilot.hil_detection.ask_human_tool

            browser_copilot.hil_detection.ask_human_tool._response_generator = None

            # Get generator
            get_response_generator()

            # Verify custom settings were used
            call_kwargs = mock_registry.get_llm.call_args.kwargs
            assert call_kwargs["provider_name"] == "custom_provider"
            assert call_kwargs["model_alias"] == "custom_model"

    @pytest.mark.asyncio
    async def test_ask_human_tool_metadata(self):
        """Test ask_human tool has correct metadata"""
        # Verify tool is properly decorated
        assert hasattr(ask_human, "name")
        assert ask_human.name == "ask_human"
        assert hasattr(ask_human, "description")
        assert "human" in ask_human.description.lower()

        # Verify it's callable
        assert callable(ask_human)

    @pytest.mark.asyncio
    async def test_confirm_action_tool_metadata(self):
        """Test confirm_action tool has correct metadata"""
        # Verify tool is properly decorated
        assert hasattr(confirm_action, "name")
        assert confirm_action.name == "confirm_action"
        assert hasattr(confirm_action, "description")
        assert "confirm" in confirm_action.description.lower()

        # Verify it's callable
        assert callable(confirm_action)
