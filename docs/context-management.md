# Context Management in Browser Copilot

## Overview

Browser Copilot uses context management strategies to optimize token usage in AI-powered browser automation. When running test suites, the AI agent accumulates message history that can grow significantly, leading to increased token consumption and costs. Context management helps control this growth while preserving essential conversation context.

## The Problem

During browser automation, the ReAct agent's message history grows with each step:
- Initial test prompt
- Browser navigation commands
- Page snapshots
- Click/type actions
- Tool responses
- Error messages

Without context management, token usage can easily double or triple during longer test runs, from ~15k to 30k+ tokens.

## Available Strategies

Browser Copilot provides four context management strategies:

### 1. No-Op Strategy (Baseline)
- **Flag**: `--context-strategy no-op`
- **Description**: Disables context management entirely
- **Use Case**: Baseline comparison, debugging, or when token usage is not a concern
- **Token Usage**: Highest (no reduction)

### 2. Sliding Window Strategy (Default)
- **Flag**: `--context-strategy sliding-window`
- **Description**: Custom implementation that intelligently manages message history
- **Features**:
  - Preserves tool call pairs (AIMessage + ToolMessage)
  - Importance-based scoring
  - Configurable window size
  - Preserves critical messages
- **Token Usage**: ~40-60% reduction

### 3. LangChain Trim Strategy
- **Flag**: `--context-strategy langchain-trim`
- **Description**: Uses LangChain's built-in `trim_messages` utility
- **Features**:
  - Simple and reliable
  - Maintains conversation flow
  - Preserves human/tool message boundaries
  - Fallback logic for edge cases
- **Token Usage**: ~50-70% reduction

### 4. LangChain Trim Advanced Strategy
- **Flag**: `--context-strategy langchain-trim-advanced`
- **Description**: Enhanced version with additional preservation rules
- **Features**:
  - Preserves first N and last N messages
  - Custom token counting support
  - Better handling of long conversations
- **Token Usage**: ~45-65% reduction

## Configuration Parameters

### Window Size
Controls the maximum token budget for message content (not including metadata or formatting):
```bash
--context-window-size 10000  # Default: 50000
```

**Note:** The window size counts only the actual message content, not the full prompt with metadata, tool calls, or system prompts. This makes it easier to predict and control.

### Preserve Window
Number of recent messages to always keep (sliding-window only):
```bash
--context-preserve-window 15  # Default: 10
```

### First/Last Message Preservation
Always keep the first N and last N messages:
```bash
--context-preserve-first 5   # Default: 5
--context-preserve-last 10   # Default: 10
```

## Usage Examples

### Basic Usage with Default Strategy
```bash
python -m browser_copilot --test-suite examples/google-ai-search.md
```

### Using No-Op Strategy (No Context Management)
```bash
python -m browser_copilot --test-suite examples/saucedemo-shopping.md \
  --context-strategy no-op
```

### Using Sliding Window with Custom Parameters
```bash
python -m browser_copilot --test-suite examples/weather-forecast.md \
  --context-strategy sliding-window \
  --context-window-size 15000 \
  --context-preserve-window 20
```

### Using LangChain Trim Strategy
```bash
python -m browser_copilot --test-suite examples/google-ai-search.md \
  --context-strategy langchain-trim \
  --context-window-size 8000
```

### Verbose Mode for Debugging
```bash
python -m browser_copilot --test-suite examples/test.md \
  --context-strategy sliding-window \
  --verbose
```

With verbose mode, you'll see:
- Number of messages processed
- Token reduction percentage
- Which messages were preserved/dropped
- Tool call pair preservation

## Strategy Comparison

### Performance Comparison Script
Use the included comparison script to evaluate strategies:
```bash
./compare_context_strategies.sh
```

This will run the same test with different strategies and show token usage for each.

### Typical Results
For a shopping cart test with ~30 steps:

| Strategy | Token Usage | Reduction | Notes |
|----------|------------|-----------|-------|
| no-op | 31,245 | 0% | Baseline |
| sliding-window | 18,747 | 40% | Good balance |
| langchain-trim | 15,498 | 50% | Most efficient |
| langchain-trim-advanced | 17,232 | 45% | Better context preservation |

## How It Works

### Message Flow
1. ReAct agent accumulates messages during execution
2. Before each LLM call, the pre_model_hook intercepts messages
3. Context management strategy processes messages
4. Trimmed messages are sent to the LLM
5. Original state remains unchanged

### Tool Call Pair Preservation
Critical for preventing "Bad Request" errors:
- AIMessages with tool_calls must keep their corresponding ToolMessages
- Breaking these pairs causes API errors
- All strategies preserve these relationships

### Message Importance (Sliding Window)
Messages are scored based on:
- Type (system > error > tool > assistant > user)
- Content (errors, screenshots, results)
- Position (recent messages score higher)
- Length (concise messages preferred)

## Best Practices

### Choosing a Strategy

1. **Use `langchain-trim` for**:
   - Simple test suites
   - Maximum token savings
   - Reliable operation

2. **Use `sliding-window` for**:
   - Complex test scenarios
   - Need for fine-tuned control
   - Custom importance scoring

3. **Use `no-op` for**:
   - Debugging issues
   - Short test suites
   - Baseline comparisons

### Window Size Guidelines

- **Small (5,000-10,000)**: Aggressive trimming, may lose context
- **Medium (10,000-25,000)**: Good balance for most tests
- **Large (25,000-50,000)**: Minimal trimming, preserves more context

### Monitoring Token Usage

Always run with `--verbose` during development to see:
```
[Sliding Window Hook] Processing 45 messages
[Sliding Window Hook] Reduced to 23 messages  
[Sliding Window Hook] Token reduction: 48.9%
```

## Troubleshooting

### Empty Message List Error
If you see "100% message reduction":
- Increase `--context-window-size`
- Use `--context-strategy sliding-window` instead
- Check if test has unusually long messages

### Bad Request Errors
If you see "Found AIMessages with tool_calls without ToolMessage":
- Ensure you're using latest version
- Try `--context-strategy langchain-trim`
- Report issue with `--verbose` output

### Loss of Context
If the agent seems to "forget" earlier steps:
- Increase `--context-window-size`
- Increase `--context-preserve-window`
- Consider using `no-op` for complex workflows

## Implementation Details

### File Structure
```
browser_copilot/context_management/
├── base.py                    # Core data models
├── manager.py                 # Context manager
├── metrics.py                 # Performance tracking
├── strategies/
│   ├── base.py               # Strategy interface
│   ├── no_op.py              # No-op implementation
│   ├── sliding_window.py     # Custom sliding window
│   └── langchain_trim.py     # LangChain wrappers
└── react_hooks.py            # LangGraph integration
```

### Key Components

1. **ContextConfig**: Configuration for all strategies
2. **ContextStrategy**: Base class for implementations
3. **BrowserCopilotContextManager**: Orchestrates strategies
4. **Pre-model Hooks**: Integration with LangGraph agents

## Future Improvements

1. **Semantic Compression**: Summarize old messages instead of dropping
2. **Dynamic Window Sizing**: Adjust based on test complexity
3. **Multi-level Caching**: Store summaries at checkpoints
4. **Custom Token Counters**: More accurate token estimation

## Conclusion

Context management is essential for cost-effective browser automation with AI. Start with the default `sliding-window` strategy and adjust based on your specific needs. Use `--verbose` mode to understand the impact and fine-tune parameters for optimal results.