# Verbose Mode Enhancements

## Overview

Enhanced verbose mode for Browser Copilot provides detailed step-by-step debugging information for QA engineers.

## What's New

### 1. Initial Prompt Display
When `--verbose` flag is set, the initial prompt sent to the LLM is now displayed:
```
============================================================
INITIAL PROMPT SENT TO LLM:
============================================================
[Full prompt content]
============================================================
```

### 2. Every Step Shown
- Previously: Steps were sampled every 5 steps
- Now: Every single step is displayed with detailed information

### 3. LLM Interactions
Each LLM call now shows:
- **Prompt preview**: First 500 characters of the prompt sent
- **Total prompt length**: Full character count
- **Response preview**: First 500 characters of the response
- **Token usage**: Detailed token consumption after each step

### 4. Tool Calls
For each tool invocation:
- Tool name clearly displayed
- Response content preview (first 200 characters)
- Execution details

## Example Output

```
[STEP 1] Processing...
[INFO]   Tool: browser_navigate
[DEBUG]   Response: ### Ran Playwright code...

[DEBUG] [LLM_CALL] Sending prompt to LLM
[DEBUG] Details: {
  "prompt_count": 1,
  "prompt_preview": "Human: # Google AI Search Example..."
}

[DEBUG] [LLM_RESPONSE] Received LLM response
[DEBUG] Details: {
  "response_preview": "I'll help you search for EARS..."
}
```

## Benefits for QA Engineers

1. **Complete Visibility**: See exactly what prompts are sent to the LLM
2. **Step-by-Step Tracking**: Monitor every action taken during test execution
3. **Debugging Aid**: Quickly identify where tests fail or behave unexpectedly
4. **Performance Insights**: Track token usage and response times
5. **Tool Transparency**: Understand which browser automation tools are used

## Usage

```bash
# Enable verbose mode
browser-copilot test.md --verbose

# Combine with other options
browser-copilot test.md --verbose --headless --output-format json
```

## Log Files

Verbose logs are saved to:
- **macOS**: `~/Library/Application Support/browser_copilot/logs/`
- **Windows**: `%LOCALAPPDATA%\browser_copilot\logs\`
- **Linux**: `~/.browser_copilot/logs/`

Log files include:
- Timestamp for each action
- Full prompt/response content
- Execution metrics
- Error details with stack traces