# Simple HIL Test

This is a minimal test to verify HIL detection and continuation.

## Test Steps:

1. Navigate to www.example.com
2. Take a screenshot to verify the page loaded
3. Output: "What is your favorite color?"
4. After receiving a response, output: "You said your favorite color is [response]"
5. Take another screenshot to complete the test

## Expected Behavior:

- Step 3 should trigger HIL detection
- HIL handler should provide a response (e.g., "blue")
- Agent should continue with step 4 using the response
- Test should complete successfully