# Human-in-the-Loop (HIL) Support

Browser Copilot supports human-in-the-loop interactions, allowing AI agents to ask for human input during test execution and continue afterward.

## Quick Start

HIL is **enabled by default**. To run in fully automated mode without HIL, use the `--no-hil` flag:

```bash
# HIL is enabled by default - the AI will make smart decisions
browser-copilot examples/hil-ask-human-test.md

# Disable HIL for fully autonomous execution
browser-copilot examples/google-ai-search.md --no-hil

# Enable interactive mode for real human input during testing
browser-copilot examples/hil-interactive-demo.md --hil-interactive
```

### HIL Modes

1. **Default Mode**: HIL enabled with LLM-generated responses
2. **Interactive Mode** (`--hil-interactive`): Prompts for real human input via console
3. **Disabled** (`--no-hil`): No HIL tools available

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
$ browser-copilot examples/hil-ask-human-test.md

[INFO] Starting test: HIL Test with AskHuman Tool
[Agent] Added ask_human and confirm_action tools for HIL
[INFO] 🔄 [HIL Interrupt] Agent paused for human input
[INFO] Auto-resuming with: blue
[INFO] Test PASSED in 12.89 seconds
```

To run without HIL:
```bash
$ browser-copilot examples/google-ai-search.md --no-hil
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

## Interactive Mode

When using `--hil-interactive`, the system will:

1. **Pause execution** when ask_human or confirm_action is called
2. **Display the question** and context in the console
3. **Show suggested response** from the LLM
4. **Wait for user input** - press Enter to use suggested or type your own
5. **Continue execution** with the provided response

### Safety Features:

- **Exit Commands**: Type `exit`, `quit`, `stop`, or `abort` to terminate execution
- **Interaction Limit**: Maximum 50 HIL interactions to prevent infinite loops
- **Recursion Protection**: Graceful handling when agent reaches recursion limit
- **Error Recovery**: Falls back to suggested response on input errors

### Example Interactive Session:

```
============================================================
🤔 HUMAN INPUT REQUIRED
============================================================

Question: What search term should I use?
Context: Testing Google search functionality

Suggested response: artificial intelligence

Enter your response (or press Enter to use suggested):
> machine learning

Using your response: machine learning
============================================================
```

## Implementation Details

- Uses LangGraph's checkpointing for state persistence
- Each test session gets a unique thread ID
- Interrupts are handled via `Command(resume=response)`
- Tools are added by default (use `--no-hil` to disable)
- Interactive mode reads from stdin for real human input
