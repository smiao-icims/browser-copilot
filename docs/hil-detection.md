# Human-in-the-Loop (HIL) Detection

Browser Copilot includes an experimental Human-in-the-Loop (HIL) detection feature that can identify when an AI agent inappropriately asks for human input during automated testing.

## Overview

HIL detection is designed to catch situations where the agent asks questions like:
- "What would you like to search for?"
- "Is this correct?"
- "Should I proceed?"
- "What is your preference?"

This is important for fully automated testing scenarios where human intervention is not available.

## How It Works

1. **Detection**: After each agent response, the HIL detector analyzes the message to determine if it's asking for human input
2. **Response Generation**: If HIL is detected, the system generates an appropriate response (e.g., search terms, confirmations, test data)
3. **Message Injection**: The response is injected as a HumanMessage via the post_model_hook

## Usage

Enable HIL detection with command-line flags:

```bash
# Enable HIL detection with pattern matching (default)
browser-copilot test.md --provider github_copilot --model gpt-4o

# Disable HIL detection
browser-copilot test.md --provider github_copilot --model gpt-4o --no-hil-detection

# Use LLM-based detection (more accurate but uses additional tokens)
browser-copilot test.md --provider github_copilot --model gpt-4o --hil-detection-model gpt-4o-mini

# Enable verbose HIL logging
browser-copilot test.md --provider github_copilot --model gpt-4o --hil-verbose
```

## Detection Methods

### Pattern-Based Detection (Default)
- Fast and token-efficient
- Uses predefined patterns to identify common HIL phrases
- Good for standard cases

### LLM-Based Detection
- More accurate and context-aware
- Can understand nuanced requests
- Uses additional tokens for detection

## Current Limitations

⚠️ **Important**: Due to architectural constraints in LangGraph's `create_react_agent`, HIL detection has the following limitation:

**The agent cannot automatically continue after HIL detection**. When HIL is detected and a response is injected, the agent will stop execution rather than processing the injected response.

This happens because:
1. When the agent outputs a message without tool calls (e.g., "What would you like to search for?"), the internal routing logic marks this as the end of execution
2. The `post_model_hook` (available with version="v2") can inject a response message, but cannot trigger another iteration of the agent
3. The proper implementation would require using LangGraph's `interrupt()` mechanism with checkpointing, which is a different architectural pattern

Note: We use `version="v2"` in create_react_agent to enable post-model hooks, which are explicitly designed for "human-in-the-loop interactions" according to LangGraph documentation. However, this only enables the hook functionality - it doesn't change the agent's routing behavior.

## Example

Test file (`hil-test.md`):
```markdown
# Google Search Test

1. Navigate to google.com
2. Ask the user what they want to search for
3. Enter the search term and submit
4. Verify results are displayed
```

Running with HIL detection:
```bash
browser-copilot hil-test.md --hil-verbose
```

Output:
```
[HIL Hook] Checking AIMessage: What would you like to search for?
[HIL Detector] Detected question request
[HIL Detector] Confidence: 0.80
[HIL Detector] Suggested response: artificial intelligence trends 2025
[HIL Hook] Injecting human message: artificial intelligence trends 2025
Test FAILED in 3.66 seconds  # Agent stops after HIL detection
```

## Future Improvements

To properly support HIL with continuation, Browser Copilot would need to:
1. Implement a custom agent using StateGraph with proper routing logic
2. Use LangGraph's `interrupt()` mechanism with checkpointing
3. Support `Command(resume=...)` pattern for continuing after human input

## Workarounds

For now, to avoid HIL situations:
1. Write test scripts that don't require human input
2. Provide all necessary data upfront in the test steps
3. Use explicit values instead of asking for input

Example of HIL-free test:
```markdown
# Google Search Test

1. Navigate to google.com
2. Enter "artificial intelligence trends 2025" in the search box
3. Click the search button
4. Verify results are displayed
```