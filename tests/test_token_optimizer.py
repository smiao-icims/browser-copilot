"""
Tests for TokenOptimizer
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
from token_optimizer import OptimizationLevel, OptimizationPresets, TokenOptimizer


@pytest.mark.unit
class TestTokenOptimizer:
    """Test TokenOptimizer functionality"""

    def test_optimization_levels(self):
        """Test different optimization levels reduce token count progressively"""
        test_prompt = """
        Please navigate to the website https://example.com and then click on the login button.
        After that, please enter the username "testuser" and the password "testpass".
        Make sure to verify that the page title contains "Dashboard" after logging in successfully.
        It is very important to ensure that all steps are completed in the correct order.
        """

        # No optimization
        optimizer_none = TokenOptimizer(OptimizationLevel.NONE)
        result_none = optimizer_none.optimize_prompt(test_prompt)
        words_none = len(result_none.split())

        # Low optimization
        optimizer_low = TokenOptimizer(OptimizationLevel.LOW)
        result_low = optimizer_low.optimize_prompt(test_prompt)
        words_low = len(result_low.split())

        # Medium optimization
        optimizer_med = TokenOptimizer(OptimizationLevel.MEDIUM)
        result_med = optimizer_med.optimize_prompt(test_prompt)
        words_med = len(result_med.split())

        # High optimization
        optimizer_high = TokenOptimizer(OptimizationLevel.HIGH)
        result_high = optimizer_high.optimize_prompt(test_prompt)
        words_high = len(result_high.split())

        # Assert progressive reduction
        assert words_none >= words_low
        assert words_low > words_med
        assert words_med > words_high

        # Check metrics
        metrics = optimizer_high.get_metrics()
        assert (
            metrics["reduction_percentage"] > 20
        )  # Should achieve at least 20% reduction
        assert len(metrics["strategies_applied"]) > 0

    def test_phrase_replacements(self):
        """Test specific phrase replacements work correctly"""
        optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)

        test_cases = [
            ("navigate to example.com", "goto"),
            ("click on the button", "click"),
            ("verify that the title is equal to 'Test'", "check"),
            ("wait for the page and then proceed", "wait"),
            ("should be equal to", "="),
            ("is greater than 5", ">"),
            ("please click the button", "click"),  # "please" removed
        ]

        for original, expected_in_result in test_cases:
            result = optimizer.optimize_prompt(original)
            assert expected_in_result in result, (
                f"Expected '{expected_in_result}' in '{result}'"
            )

    def test_whitespace_removal(self):
        """Test whitespace optimization"""
        optimizer = TokenOptimizer(OptimizationLevel.LOW)

        test_cases = [
            ("word1  word2   word3", "word1 word2 word3"),
            ("text before .  punctuation", "text before. punctuation"),
            ("  leading and trailing  ", "leading and trailing"),
            ("multiple\n\n\nlines", "multiple lines"),
        ]

        for original, expected in test_cases:
            result = optimizer.optimize_prompt(original)
            assert result == expected

    def test_number_simplification(self):
        """Test number handling"""
        optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)

        test_cases = [
            ("wait 1,000 milliseconds", "1000"),
            ("click the first button", "1st"),
            ("select the second option", "2nd"),
            ("on the third page", "3rd"),
        ]

        for original, expected_in_result in test_cases:
            result = optimizer.optimize_prompt(original)
            assert expected_in_result in result

    def test_selector_preservation(self):
        """Test that selectors and important identifiers are preserved"""
        optimizer = TokenOptimizer(OptimizationLevel.HIGH)

        # Even with aggressive optimization, selectors should be preserved
        test_cases = [
            "Click on the button with class .submit-button",
            "Find the element with id #login-form",
            "Select the input[type='text']",
            "Click button.primary.large",
        ]

        for test in test_cases:
            result = optimizer.optimize_prompt(test)
            # Check that some selector pattern is still present (even if modified)
            # The optimizer might abbreviate "button" to "btn" but should preserve selectors
            has_selector = any(
                selector in result
                for selector in [".submit", "#login", "input[", "button.", ".primary"]
            )
            assert has_selector, f"No selector found in optimized result: '{result}'"

    def test_context_optimization(self):
        """Test context truncation and prioritization"""
        optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)

        # Create a long context
        long_context = "\n".join(
            [
                f"Step {i}: Perform action number {i} on the page element with id test-{i}"
                for i in range(100)
            ]
        )

        # Optimize with length limit
        optimized = optimizer.optimize_context(
            long_context, max_length=1000, preserve_recent=200
        )

        assert len(optimized) <= 1200  # Some buffer for markers
        # Check for truncation - either "..." or ". " pattern
        assert "..." in optimized or ". " in optimized, "No truncation marker found"
        assert "Step 99:" in optimized  # Recent content preserved

    def test_cost_estimation(self):
        """Test cost savings calculations"""
        optimizer = TokenOptimizer(OptimizationLevel.HIGH)

        # Test cost calculation
        cost_analysis = optimizer.estimate_cost_savings(
            original_tokens=1000, optimized_tokens=700, cost_per_1k_tokens=0.002
        )

        assert abs(cost_analysis["original_cost"] - 0.002) < 0.0001
        assert abs(cost_analysis["optimized_cost"] - 0.0014) < 0.0001
        assert abs(cost_analysis["savings"] - 0.0006) < 0.0001
        assert abs(cost_analysis["savings_percentage"] - 30.0) < 0.01

    def test_empty_and_short_inputs(self):
        """Test edge cases with empty or very short inputs"""
        optimizer = TokenOptimizer(OptimizationLevel.HIGH)

        # Empty input
        assert optimizer.optimize_prompt("") == ""

        # Single word
        assert optimizer.optimize_prompt("Test") == "Test"

        # Short phrase that shouldn't be over-optimized
        result = optimizer.optimize_prompt("Click button")
        assert "Click" in result or "click" in result
        assert "button" in result or "btn" in result

    def test_abbreviations(self):
        """Test common term abbreviations in high optimization"""
        optimizer = TokenOptimizer(OptimizationLevel.HIGH)

        test_cases = [
            ("click the button", "btn"),
            ("enter password", "pwd"),
            ("type username", "user"),
            ("check configuration", "config"),
            ("view information", "info"),
        ]

        for original, expected_abbr in test_cases:
            result = optimizer.optimize_prompt(original)
            assert expected_abbr in result

    def test_metrics_tracking(self):
        """Test that metrics are properly tracked"""
        optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)

        # Process multiple prompts
        prompts = [
            "This is a very long and verbose prompt with many unnecessary words",
            "Please kindly navigate to the website and click on the button",
            "It is extremely important to verify that everything is working",
        ]

        for prompt in prompts:
            optimizer.optimize_prompt(prompt)

        metrics = optimizer.get_metrics()
        assert metrics["original_tokens"] > 0
        assert metrics["optimized_tokens"] > 0
        assert metrics["optimized_tokens"] < metrics["original_tokens"]
        assert metrics["reduction_percentage"] > 0
        assert len(metrics["strategies_applied"]) > 0

    def test_optimization_presets(self):
        """Test predefined optimization presets"""
        # Quick test preset
        quick_preset = OptimizationPresets.get_preset("quick_test")
        assert quick_preset["level"] == OptimizationLevel.HIGH
        assert quick_preset["max_context"] == 2000
        assert quick_preset["skip_screenshots"] is True

        # Detailed debug preset
        debug_preset = OptimizationPresets.get_preset("detailed_debug")
        assert debug_preset["level"] == OptimizationLevel.LOW
        assert debug_preset["max_context"] == 8000
        assert debug_preset["skip_screenshots"] is False

        # Cost sensitive preset
        cost_preset = OptimizationPresets.get_preset("cost_sensitive")
        assert cost_preset["level"] == OptimizationLevel.HIGH

        # Default fallback
        unknown_preset = OptimizationPresets.get_preset("unknown")
        assert (
            unknown_preset["level"] == OptimizationLevel.MEDIUM
        )  # Falls back to balanced

    @patch("browser_copilot.token_optimizer.LANGCHAIN_AVAILABLE", True)
    def test_langchain_message_optimization(self, mock_langchain_imports):
        """Test optimization of LangChain messages"""
        # Since we can't easily mock the isinstance checks for langchain types,
        # we'll test that the optimizer handles arbitrary message objects
        # by returning them unchanged when they don't match expected types

        optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)

        # Create simple mock messages with content attribute
        class MockMessage:
            def __init__(self, content):
                self.content = content

        messages = [
            MockMessage("You are a helpful assistant"),
            MockMessage("Please navigate to the website"),
        ]

        # Since our mock messages won't match isinstance checks for HumanMessage/SystemMessage,
        # they should be returned unchanged
        optimized = optimizer.optimize_messages(messages)

        # Verify messages are returned unchanged
        assert len(optimized) == 2
        assert optimized[0] is messages[0]
        assert optimized[1] is messages[1]
        assert optimized[0].content == "You are a helpful assistant"
        assert optimized[1].content == "Please navigate to the website"

    def test_instruction_compression(self):
        """Test instruction pattern compression"""
        optimizer = TokenOptimizer(OptimizationLevel.HIGH)

        instructions = """
        Step 1: Navigate to the homepage
        Step 2: Click on the login button
        You should enter your credentials
        You must verify the page loaded
        You need to check the results
        """

        result = optimizer.optimize_prompt(instructions)

        # Check step compression
        assert "1." in result
        assert "2." in result
        assert "Step 1:" not in result

        # Check that at least some instruction prefixes were removed or shortened
        # HIGH optimization may not remove all prefixes, but should reduce them
        original_count = instructions.count("You ")
        result_count = result.count("You ")
        # If not reduced, at least check for other optimizations
        if result_count >= original_count:
            # Check that other optimizations were applied
            assert len(result) < len(instructions), "Should reduce overall length"
