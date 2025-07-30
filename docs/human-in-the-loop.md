# Human-in-the-Loop (HIL) Support

Browser Copilot supports human-in-the-loop interactions, allowing AI agents to ask for human input during test execution and continue afterward.

## Quick Start

Enable HIL mode with the `--hil` flag:

```bash
browser-copilot test.md --hil
```

## How It Works

1. **Explicit Tools**: The agent has access to `ask_human` and `confirm_action` tools
2. **Interrupt Mechanism**: Tools use LangGraph's `interrupt()` to pause execution
3. **Automatic Resume**: In automated mode, suggested responses are used
4. **Continuation**: Agent continues with remaining steps after receiving input

## Writing HIL Tests

Use the `ask_human` tool in your test steps:

```markdown
# Search Test with Human Input

1. Navigate to google.com
2. Use ask_human tool to ask: "What should I search for?"
3. Enter the provided search term
4. Verify results are displayed
```

## Example

```bash
$ browser-copilot examples/hil-ask-human-test.md --hil

[INFO] Starting test: HIL Test with AskHuman Tool
[Agent] Added ask_human and confirm_action tools for HIL
[INFO] 🔄 [HIL Interrupt] Agent paused for human input
[INFO] Auto-resuming with: blue
[INFO] Test PASSED in 12.89 seconds
```

## Automatic Responses

HIL uses LLM-powered response generation with few-shot examples for intelligent decisions:

### Common Responses:
- Color preferences → "blue", "red", or "green"
- Search queries → "artificial intelligence", "machine learning"
- Names → "John Doe", "Jane Smith", "Test User"
- Email addresses → "test@example.com" format

### Test Flow Decisions:
- **Retry on transient errors**: Network timeouts, 500 errors → "retry"
- **Continue on validation errors**: Missing fields, auth failures → "proceed"
- **Resume from last checkpoint**: Partial failures → "start over from [last step]"
- **Skip on permanent errors**: 404 not found → "skip to next test"

The LLM analyzes context to make appropriate decisions for test automation scenarios.

## Implementation Details

- Uses LangGraph's checkpointing for state persistence
- Each test session gets a unique thread ID
- Interrupts are handled via `Command(resume=response)`
- Tools are only added when `--hil` flag is used