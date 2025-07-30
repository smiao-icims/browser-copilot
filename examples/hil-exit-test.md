# HIL Exit Test

This test demonstrates the safety features of HIL interactive mode, including
the ability to exit the test at any point.

## Test Steps:

1. Navigate to www.example.com
2. Use ask_human: "What is your name?"
3. Output: "Hello [name]!"
4. Use ask_human: "Should I continue with more questions?"
5. If yes, use ask_human: "What's your favorite programming language?"
6. Navigate to github.com/search
7. Search for repositories in that language
8. Take a screenshot

## Testing Exit Feature:

To test the exit functionality, run with `--hil-interactive` and:
- At any prompt, type `exit`, `quit`, `stop`, or `abort`
- The test will terminate gracefully with a warning message

## Example Usage:

```bash
# Test exit functionality
browser-copilot examples/hil-exit-test.md --hil-interactive

# When prompted, type "exit" to see graceful termination
```