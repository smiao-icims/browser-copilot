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

Browser Copilot provides three context management strategies:

### 1. No-Op Strategy (Baseline)
- **Flag**: `--context-strategy no-op`
- **Description**: Disables context management entirely
- **Use Case**: Baseline comparison, debugging, or when token usage is not a concern
- **Token Usage**: Highest (no reduction)

### 2. True Sliding Window Strategy (Default)
- **Flag**: `--context-strategy true-sliding-window`
- **Description**: Sliding window that preserves Human/System messages and fills with recent messages
- **Features**:
  - Preserves first N Human and System messages (test instructions & system prompts)
  - Works backwards from most recent to fill remaining budget
  - Maintains message integrity (tool pairs) for recent messages
  - May exceed window size slightly to preserve integrity
- **Token Usage**: High reduction while preserving critical context
- **Best for**: Most browser automation scenarios
- **Recommended**: Use `--context-preserve-first 2` (default) to keep system prompt and test instructions

### 3. Smart Trim Strategy
- **Flag**: `--context-strategy smart-trim`
- **Description**: Intelligent trimming based on message importance and content analysis
- **Features**:
  - Scores messages based on content importance
  - Preserves high-value messages (errors, test steps, results)
  - Adaptive trimming based on message patterns
  - Maintains message integrity (tool pairs)
- **Token Usage**: Variable reduction based on content
- **Best for**: Complex tests where specific content matters more than recency

## Configuration Parameters

### Window Size
Controls the maximum token budget for message content:
```bash
--context-window-size 25000  # Default: 50000
```

### Preserve First Messages
Number of first Human/System messages to always keep (for true-sliding-window):
```bash
--context-preserve-first 2   # Default: 2
```

### Preserve Last Messages
Number of recent messages to always keep (for strategies that support it):
```bash
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

### Using True Sliding Window with Custom Parameters
```bash
python -m browser_copilot --test-suite examples/weather-forecast.md \
  --context-strategy true-sliding-window \
  --context-window-size 25000 \
  --context-preserve-first 2
```

### Using Smart Trim Strategy
```bash
python -m browser_copilot --test-suite examples/complex-form-test.md \
  --context-strategy smart-trim \
  --context-window-size 30000
```

### Verbose Mode for Debugging
```bash
python -m browser_copilot --test-suite examples/test.md \
  --context-strategy true-sliding-window \
  --verbose
```

With verbose mode, you'll see:
- Number of messages processed
- Token reduction percentage
- Which messages were preserved/dropped
- Message integrity validation

## Strategy Comparison

### Typical Results
For a shopping cart test with ~30 steps:

| Strategy | Token Usage | Reduction | Notes |
|----------|------------|-----------|-------|
| no-op | 31,245 | 0% | Baseline, no trimming |
| true-sliding-window | 24,014 | 23% | Balanced, preserves context |
| smart-trim | ~20,000-25,000 | 20-36% | Varies based on content |

## How It Works

### Message Flow
1. ReAct agent accumulates messages during execution
2. Before each LLM call, the pre_model_hook intercepts messages
3. Context management strategy processes messages
4. Trimmed messages are sent to the LLM
5. Original state remains unchanged

### Message Integrity
All strategies ensure AIMessage/ToolMessage pairs are kept together. If an AI message has tool calls, the corresponding tool responses are preserved to avoid "Bad Request" errors.

### Token Counting
Tokens are estimated using a simple heuristic: 4 characters ≈ 1 token. This provides fast, reasonable approximations without requiring model-specific tokenizers.

## Best Practices

1. **Start with the default**: `true-sliding-window` works well for most cases
2. **Adjust window size based on your model**: GPT-4 can handle larger windows than GPT-3.5
3. **Use verbose mode** to understand trimming behavior during development
4. **Monitor token usage** in production to optimize costs
5. **Use smart-trim** for tests with complex decision trees or important error messages

## Troubleshooting

### Agent loses context mid-test
- Increase `--context-window-size`
- Ensure `--context-preserve-first` is at least 2
- Try `smart-trim` strategy if specific messages are important

### Token usage still too high
- Decrease `--context-window-size`
- Use `smart-trim` for more aggressive but intelligent trimming
- Consider breaking long tests into smaller suites

### Bad Request errors
- This usually means tool pairs were broken (shouldn't happen with current strategies)
- Report as a bug if you encounter this