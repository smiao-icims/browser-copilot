# HIL Interactive Mode Demo

This test demonstrates the interactive mode where you can provide real human input
during test execution. Perfect for test development and debugging.

## Test Steps:

1. Navigate to www.example.com
2. Take a screenshot to show the page loaded
3. Use ask_human to get your name: "What is your name for this test session?"
4. Output: "Hello [name], let's test the search functionality!"
5. Use ask_human to get search preference: "What would you like to search for today?"
6. Navigate to google.com
7. Enter the search term you provided
8. Take a screenshot of the search results
9. Use confirm_action: "Should I save these results for later analysis?"
10. Output final message based on confirmation

## Expected Behavior:

When run with `--hil-interactive`:
- The test will pause 3 times for your input
- You can provide custom responses or press Enter to use suggestions
- The test adapts based on your actual input

When run without `--hil-interactive`:
- LLM automatically provides appropriate responses
- Test runs without interruption

## Usage:

```bash
# Interactive mode - you control the responses
browser-copilot examples/hil-interactive-demo.md --hil-interactive

# Automated mode - LLM provides responses
browser-copilot examples/hil-interactive-demo.md
```
