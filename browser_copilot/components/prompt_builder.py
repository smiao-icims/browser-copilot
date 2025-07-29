"""
Prompt Builder component for Browser Copilot

Constructs and optimizes prompts for test execution.
"""

from ..token_optimizer import TokenOptimizer
from .models import OptimizationMetrics


class PromptBuilder:
    """Constructs prompts for test execution"""

    DEFAULT_INSTRUCTIONS = """
IMPORTANT INSTRUCTIONS:
1. Execute each test step methodically using the browser automation tools
2. Use browser_snapshot before interacting with elements
3. Take screenshots at key points using browser_take_screenshot
4. Handle errors gracefully and continue if possible
5. Wait for page loads after navigation
6. For form fields - IMPORTANT:
   - Process each field completely before moving to the next
   - Click a field and immediately type in it (don't click multiple fields then type)
   - For each field: click it, then type the value right away
   - Never click all fields first and then go back to type
   - If a field doesn't accept input, click it again
7. Be especially careful with the first field in a form - complete it fully before moving on

At the end, generate a comprehensive test report in markdown format:

# Test Execution Report

## Summary
- Overall Status: PASSED or FAILED
- Duration: X seconds
- Browser: {browser}

## Test Results

### [Test Name]
**Status:** PASSED/FAILED

**Steps Executed:**
1. ✅ [Step description] - [What happened]
2. ❌ [Step description] - Error: [What went wrong]

**Screenshots Taken:**
- [List of screenshots with descriptions]

## Issues Encountered
[Any errors or unexpected behaviors]

## Recommendations
[Suggestions for improvement]

Execute the test now."""

    def __init__(self, optimizer: TokenOptimizer | None = None):
        """
        Initialize PromptBuilder

        Args:
            optimizer: Optional TokenOptimizer for prompt optimization
        """
        self.optimizer = optimizer

    def build(
        self,
        test_content: str,
        system_prompt: str | None = None,
        browser: str = "unknown",
    ) -> str:
        """
        Build complete prompt from test content

        Args:
            test_content: The test scenario content
            system_prompt: Optional custom system prompt
            browser: Browser name for report template

        Returns:
            Complete prompt ready for LLM
        """
        # Use custom system prompt if provided
        base_prompt = system_prompt if system_prompt else ""

        # Format instructions with browser info
        instructions = self.DEFAULT_INSTRUCTIONS.format(browser=browser)

        # Combine prompts
        full_prompt = f"""{base_prompt}{test_content.strip()}
{instructions}"""

        return full_prompt

    def optimize(self, prompt: str) -> tuple[str, OptimizationMetrics]:
        """
        Optimize prompt if optimizer available

        Args:
            prompt: The prompt to optimize

        Returns:
            Tuple of (optimized_prompt, optimization_metrics)
        """
        if not self.optimizer:
            # No optimization, return original with zero metrics
            word_count = len(prompt.split())
            metrics = OptimizationMetrics(
                original_tokens=word_count,
                optimized_tokens=word_count,
                reduction_percentage=0.0,
                strategies_applied=[],
            )
            return prompt, metrics

        # Optimize the prompt
        optimized_prompt = self.optimizer.optimize_prompt(prompt)

        # Get metrics from optimizer
        opt_metrics = self.optimizer.get_metrics()

        # Convert to our metrics format
        metrics = OptimizationMetrics(
            original_tokens=opt_metrics["original_tokens"],
            optimized_tokens=opt_metrics["optimized_tokens"],
            reduction_percentage=opt_metrics["reduction_percentage"],
            strategies_applied=opt_metrics["strategies_applied"],
        )

        return optimized_prompt, metrics

    def extract_test_name(self, test_content: str) -> str:
        """
        Extract test name from content

        Args:
            test_content: Test scenario content

        Returns:
            Extracted test name
        """
        lines = test_content.strip().split("\n")

        # Look for markdown heading
        for line in lines:
            if line.startswith("#"):
                return line.strip("# ").strip()

        # Use first non-empty line
        for line in lines:
            if line.strip():
                # Truncate if too long
                name = line.strip()
                if len(name) > 50:
                    name = name[:47] + "..."
                return name

        return "Browser Test"
