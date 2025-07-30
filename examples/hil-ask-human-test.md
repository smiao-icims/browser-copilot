# HIL Test with AskHuman Tool

This test demonstrates using the ask_human tool for proper human-in-the-loop interactions.

## Test Steps:

1. Navigate to www.example.com
2. Take a screenshot to verify the page loaded
3. Use the ask_human tool to ask: "What is your favorite color?"
4. After receiving the response, output: "You said your favorite color is [response]"
5. Take another screenshot to complete the test

## Expected Behavior:
- The ask_human tool should trigger an interrupt
- In automated mode, it should use the suggested response
- The agent should continue execution after receiving the response
- The test should complete successfully
