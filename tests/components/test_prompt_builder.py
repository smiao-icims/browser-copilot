"""
Tests for PromptBuilder component
"""

from unittest.mock import MagicMock

import pytest

from browser_copilot.components.models import OptimizationMetrics
from browser_copilot.components.prompt_builder import PromptBuilder
from browser_copilot.token_optimizer import OptimizationLevel, TokenOptimizer


class TestPromptBuilder:
    """Test cases for PromptBuilder"""

    @pytest.fixture
    def builder(self):
        """Create a PromptBuilder without optimizer"""
        return PromptBuilder()

    @pytest.fixture
    def mock_optimizer(self):
        """Create a mock TokenOptimizer"""
        optimizer = MagicMock(spec=TokenOptimizer)
        optimizer.optimize_prompt.return_value = "optimized prompt"
        optimizer.get_metrics.return_value = {
            "original_tokens": 100,
            "optimized_tokens": 70,
            "reduction_percentage": 30.0,
            "strategies_applied": ["whitespace", "instruction"],
        }
        return optimizer

    def test_build_basic_prompt(self, builder):
        """Test building a basic prompt"""
        test_content = "# Test Scenario\n1. Navigate to example.com\n2. Click button"
        
        prompt = builder.build(test_content)
        
        # Should contain test content
        assert test_content in prompt
        # Should contain instructions
        assert "IMPORTANT INSTRUCTIONS:" in prompt
        assert "Execute each test step methodically" in prompt
        assert "browser_snapshot" in prompt
        assert "browser_take_screenshot" in prompt
        # Should contain report format
        assert "Test Execution Report" in prompt
        assert "Overall Status: PASSED or FAILED" in prompt

    def test_build_with_custom_system_prompt(self, builder):
        """Test building with custom system prompt"""
        test_content = "# Test Scenario\n1. Test step"
        system_prompt = "You are a specialized testing agent."
        
        prompt = builder.build(test_content, system_prompt)
        
        # Should start with system prompt
        assert prompt.startswith(system_prompt)
        # Should still contain test content
        assert test_content in prompt
        # Should still contain instructions
        assert "IMPORTANT INSTRUCTIONS:" in prompt

    def test_build_includes_browser_info(self, builder):
        """Test prompt includes browser information"""
        test_content = "# Test"
        browser = "firefox"
        
        prompt = builder.build(test_content, browser=browser)
        
        # Should include browser in report template
        assert f"Browser: {browser}" in prompt

    def test_extract_test_name_from_heading(self, builder):
        """Test extracting test name from markdown heading"""
        test_cases = [
            ("# Shopping Cart Test\nSteps here", "Shopping Cart Test"),
            ("## Login Flow Test\nSteps", "Login Flow Test"),
            ("### API Test\nContent", "API Test"),
            ("#### Deep Heading\nText", "Deep Heading"),
        ]
        
        for content, expected in test_cases:
            assert builder.extract_test_name(content) == expected

    def test_extract_test_name_from_first_line(self, builder):
        """Test extracting test name from first non-empty line"""
        test_cases = [
            ("Shopping cart test\n1. Step one", "Shopping cart test"),
            ("\n\nLogin test\nSteps", "Login test"),
            ("   Whitespace test   \nContent", "Whitespace test"),
        ]
        
        for content, expected in test_cases:
            assert builder.extract_test_name(content) == expected

    def test_extract_test_name_truncation(self, builder):
        """Test test name truncation for long names"""
        long_name = "A" * 100
        content = f"{long_name}\nSteps"
        
        result = builder.extract_test_name(content)
        
        assert len(result) == 50  # 47 + "..."
        assert result.endswith("...")
        assert result.startswith("A" * 47)

    def test_extract_test_name_empty_content(self, builder):
        """Test extracting name from empty content"""
        test_cases = ["", "\n\n\n", "   \t   "]
        
        for content in test_cases:
            assert builder.extract_test_name(content) == "Browser Test"

    def test_optimize_without_optimizer(self, builder):
        """Test optimize returns original prompt when no optimizer"""
        prompt = "Test prompt content"
        
        result, metrics = builder.optimize(prompt)
        
        assert result == prompt
        assert isinstance(metrics, OptimizationMetrics)
        assert metrics.original_tokens == len(prompt.split())
        assert metrics.optimized_tokens == len(prompt.split())
        assert metrics.reduction_percentage == 0.0
        assert metrics.strategies_applied == []

    def test_optimize_with_optimizer(self, mock_optimizer):
        """Test optimize with token optimizer"""
        builder = PromptBuilder(optimizer=mock_optimizer)
        prompt = "Test prompt with many tokens to optimize"
        
        result, metrics = builder.optimize(prompt)
        
        assert result == "optimized prompt"
        assert isinstance(metrics, OptimizationMetrics)
        assert metrics.original_tokens == 100
        assert metrics.optimized_tokens == 70
        assert metrics.reduction_percentage == 30.0
        assert metrics.strategies_applied == ["whitespace", "instruction"]
        
        mock_optimizer.optimize_prompt.assert_called_once_with(prompt)
        mock_optimizer.get_metrics.assert_called_once()

    def test_prompt_includes_form_instructions(self, builder):
        """Test prompt includes specific form handling instructions"""
        prompt = builder.build("# Test")
        
        # Check for form-specific instructions
        assert "For form fields - IMPORTANT:" in prompt
        assert "Process each field completely before moving to the next" in prompt
        assert "Click a field and immediately type in it" in prompt
        assert "Never click all fields first and then go back to type" in prompt

    def test_prompt_template_structure(self, builder):
        """Test the overall structure of the prompt template"""
        test_content = "# Test Scenario"
        prompt = builder.build(test_content)
        
        # Verify major sections exist in order
        sections = [
            test_content,
            "IMPORTANT INSTRUCTIONS:",
            "Execute each test step",
            "Use browser_snapshot",
            "Take screenshots",
            "Handle errors gracefully",
            "Wait for page loads",
            "For form fields",
            "Test Execution Report",
            "## Summary",
            "## Test Results",
            "## Issues Encountered",
            "## Recommendations",
            "Execute the test now.",
        ]
        
        last_pos = -1
        for section in sections:
            pos = prompt.find(section)
            assert pos > last_pos, f"Section '{section}' not found in correct order"
            last_pos = pos

    def test_build_strips_whitespace(self, builder):
        """Test that build strips extra whitespace from content"""
        test_content = "\n\n   # Test   \n\n   Steps   \n\n"
        
        prompt = builder.build(test_content)
        
        # Should have cleaned content
        assert "# Test   \n\n   Steps" in prompt
        assert not prompt.startswith("\n\n")

    def test_default_instructions_constant(self, builder):
        """Test DEFAULT_INSTRUCTIONS is properly defined"""
        assert hasattr(builder, "DEFAULT_INSTRUCTIONS")
        assert isinstance(builder.DEFAULT_INSTRUCTIONS, str)
        assert len(builder.DEFAULT_INSTRUCTIONS) > 100
        assert "IMPORTANT INSTRUCTIONS:" in builder.DEFAULT_INSTRUCTIONS

    def test_optimizer_integration(self):
        """Test real TokenOptimizer integration"""
        # Create real optimizer
        real_optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)
        builder = PromptBuilder(optimizer=real_optimizer)
        
        test_content = "# Test Scenario\n" + ("Step " * 50)  # Long content
        prompt = builder.build(test_content)
        
        optimized, metrics = builder.optimize(prompt)
        
        # Should be optimized
        assert len(optimized) < len(prompt)
        assert metrics.reduction_percentage > 0
        assert len(metrics.strategies_applied) > 0