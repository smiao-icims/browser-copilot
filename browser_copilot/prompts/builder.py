"""
Prompt building module for Browser Copilot

This module handles construction of prompts for test execution,
including system prompts and test instructions.
"""

from ..token_optimizer import TokenOptimizer


class PromptBuilder:
    """Builds prompts for test execution"""

    # Default test execution instructions
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
8. ERROR HANDLING - CRITICAL:
   - When you encounter an error or unexpected behavior, use the ask_human tool
   - Provide clear context about what went wrong and what you were trying to do
   - Wait for guidance before proceeding with alternative approaches
   - The ask_human tool helps ensure test reliability and correctness

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

    def __init__(
        self,
        system_prompt: str | None = None,
        token_optimizer: TokenOptimizer | None = None,
    ):
        """
        Initialize prompt builder

        Args:
            system_prompt: Custom system prompt to use
            token_optimizer: Token optimizer for prompt compression
        """
        self.system_prompt = system_prompt
        self.token_optimizer = token_optimizer

    def build_test_prompt(
        self,
        test_suite_content: str,
        browser: str = "Unknown",
        custom_instructions: str | None = None,
    ) -> str:
        """
        Build the test execution prompt with instructions

        Args:
            test_suite_content: The test suite content
            browser: Browser being used
            custom_instructions: Custom instructions to use instead of defaults

        Returns:
            Complete prompt for test execution
        """
        # Use custom system prompt if provided
        base_prompt = self.system_prompt if self.system_prompt else ""

        # Use custom or default instructions
        instructions = custom_instructions or self.DEFAULT_INSTRUCTIONS.format(
            browser=browser
        )

        # Combine all parts
        full_prompt = f"{base_prompt}{test_suite_content.strip()}\n{instructions}"

        # Apply token optimization if enabled
        if self.token_optimizer:
            optimized_prompt = self.token_optimizer.optimize_prompt(full_prompt)

            # Log optimization metrics
            metrics = self.token_optimizer.get_metrics()
            if metrics["reduction_percentage"] > 0:
                print(
                    f"[PromptBuilder] Prompt optimized: "
                    f"{metrics['reduction_percentage']:.1f}% reduction"
                )

            return optimized_prompt

        return full_prompt

    def build_hil_prompt(
        self,
        test_name: str,
        current_step: str,
        error_message: str,
        screenshot_description: str | None = None,
    ) -> str:
        """
        Build prompt for Human-in-the-Loop intervention

        Args:
            test_name: Name of the test
            current_step: Current test step
            error_message: Error that occurred
            screenshot_description: Optional screenshot context

        Returns:
            HIL prompt for decision making
        """
        prompt = f"""
Test Execution Decision Required

Test: {test_name}
Current Step: {current_step}
Error: {error_message}
"""

        if screenshot_description:
            prompt += f"Screenshot Context: {screenshot_description}\n"

        prompt += """
Analyze this situation and provide one of these responses:
1. CONTINUE - If the error is minor and the test can proceed
2. RETRY - If the step should be retried with modifications
3. SKIP - If this step should be skipped but test continues
4. FAIL - If this is a critical failure requiring test termination

Include reasoning and any specific instructions for retry scenarios.
"""

        return prompt

    def build_analysis_prompt(self, report_content: str) -> str:
        """
        Build prompt for analyzing test results

        Args:
            report_content: Test execution report

        Returns:
            Analysis prompt
        """
        return f"""
Analyze the following test execution report and provide insights:

{report_content}

Please provide:
1. Overall assessment of test execution
2. Key failures or issues identified
3. Potential root causes
4. Recommendations for improvement
5. Success rate summary
"""
