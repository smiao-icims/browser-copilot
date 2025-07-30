# Human-in-the-Loop Solution for Browser Copilot

## Overview

Browser Copilot now supports proper human-in-the-loop (HIL) interactions using LangGraph's interrupt mechanism with custom tools.

## The Solution: AskHuman Tool

Instead of trying to detect HIL situations after the agent outputs a message, we provide the agent with explicit tools to ask for human input:

- `ask_human(question)` - Ask the user a question and wait for response
- `confirm_action(action)` - Request confirmation before proceeding

## How It Works

1. **Agent calls ask_human tool** when it needs input
2. **Tool uses interrupt()** to pause execution
3. **Execution resumes** with Command(resume=response)
4. **Agent continues** with the remaining steps

## Usage

### Enable HIL Mode

```bash
browser-copilot test.md --hil-use-interrupt
```

### Write Tests That Use ask_human

```markdown
# Test with Human Input

1. Navigate to example.com
2. Use ask_human tool to ask: "What search term should I use?"
3. Search for the provided term
4. Verify results are displayed
```

### Automated Mode

In automated testing, the ask_human tool provides suggested responses based on the question:
- Questions about colors → "blue"
- Questions about search → "artificial intelligence"
- Questions about names → "John Doe"
- Confirmation requests → "yes"

## Implementation Details

### Key Components

1. **ask_human_tool.py** - Implements the tools using interrupt()
2. **Checkpointing** - MemorySaver enables pause/resume
3. **Thread ID** - Unique ID for each test session
4. **Command(resume=...)** - Resumes execution with response

### Architecture

```
Agent → ask_human() → interrupt() → [pause]
                                     ↓
User/Auto → Command(resume="answer") → [resume]
                                       ↓
                                     Agent continues
```

## Advantages

1. **Explicit Control** - Agent decides when to ask for input
2. **Natural Flow** - Agent continues after receiving response
3. **No Detection Needed** - No complex HIL detection logic
4. **Tool-Based** - Works within LangGraph's tool framework

## Example Test Run

```bash
$ browser-copilot examples/hil-ask-human-test.md --hil-use-interrupt

[INFO] Starting test: HIL Test with AskHuman Tool
[Agent] Added ask_human and confirm_action tools for HIL
[INFO] 🔄 [HIL Interrupt] Agent paused for human input
[INFO] Auto-resuming with: blue
[INFO] Test PASSED in 12.89 seconds
```

## Migration from Detection-Based HIL

If you were using the old HIL detection approach:

1. Remove `--no-hil-detection` flag (detection is no longer needed)
2. Add `--hil-use-interrupt` flag
3. Update tests to use `ask_human` tool explicitly
4. Remove "Output:" style questions, use tool instead

## Limitations

- Requires explicit tool usage (agent won't automatically detect HIL)
- Only works with `--hil-use-interrupt` flag
- Requires checkpointing (adds slight overhead)

## Future Enhancements

- Add more specialized HIL tools (select_option, provide_credentials, etc.)
- Support for custom response strategies
- Integration with external input sources