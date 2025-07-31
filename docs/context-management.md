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

### 2. Sliding Window Strategy (Default)
- **Flag**: `--context-strategy sliding-window`
- **Description**: Sliding window that preserves first and last messages with middle filling
- **Algorithm**:
  1. **ALWAYS preserve first N Human/System messages** (e.g., test instructions, system prompts)
  2. **ALWAYS preserve last M messages** regardless of budget (with integrity for tool pairs)
  3. **Check total tokens** after adding both first N and last M
  4. **If budget remains**, fill backwards from message (last M - 1) with middle messages
  5. **If first N + last M exceed budget**, show warning but keep both (no middle messages)
- **Features**:
  - Message integrity maintained throughout (AIMessage/ToolMessage pairs stay together)
  - May exceed window size to preserve integrity
  - Clear warnings when budget is exceeded
  - Maintains strict message ordering (no sorting needed)
- **Token Usage**: Balanced reduction while preserving both initial and recent context
- **Best for**: Most browser automation scenarios where both test instructions and recent context are critical
- **Recommended**: Use `--context-preserve-first 2` and `--context-preserve-last 10` (defaults)

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
--context-window-size 25000  # Default: 25000
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
  --context-strategy sliding-window \
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
| sliding-window | 24,014 | 23% | Balanced, preserves context |
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

### Sliding Window Algorithm Example

With `--context-window-size 25000 --context-preserve-first 2 --context-preserve-last 10`:

#### Scenario 1: Within Budget
- **Messages**: 20 total (15,000 tokens)
- **Result**: All messages kept (under 25,000 token budget)

#### Scenario 2: First + Last Within Budget
- **Messages**: 30 total (40,000 tokens)
- **First 2**: Human (1,000) + System (500) = 1,500 tokens
- **Last 10**: Messages 20-29 = 18,000 tokens
- **Total**: 19,500 tokens (within 25,000 budget)
- **Result**: Keeps messages [0, 1, 20-29] + fills middle with messages 19, 18, 17... until budget exhausted

#### Scenario 3: First + Last Exceed Budget
- **Messages**: 35 total (50,000 tokens)
- **First 1**: Human (1,119 tokens)
- **Last 10**: Messages 25-34 = 31,805 tokens
- **Total**: 32,924 tokens (exceeds 25,000 budget)
- **Result**:
  - Keeps messages [0, 25-34] only
  - Shows warning: "WARNING: First 1 + Last 10 = 32,924 tokens (exceeds 25,000)"
  - No middle messages added
  - May include additional messages for integrity (e.g., message 22 if message 25 depends on it)

## Best Practices

1. **Start with the default**: `sliding-window` works well for most cases
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

## Quick Reference

### 🚀 Quick Start

```bash
# Just use the defaults (sliding window, 50k tokens)
browser-copilot examples/context-heavy-test.md

# Maximum token savings
browser-copilot examples/context-heavy-test.md --context-strategy smart-trim --context-window-size 10000

# Debug what's happening
browser-copilot examples/context-heavy-test.md --verbose
```

### 📊 Strategy Comparison

| Strategy | Command | Token Savings | Best For |
|----------|---------|---------------|----------|
| No-Op | `--context-strategy no-op` | 0% | Debugging |
| Sliding Window | `--context-strategy sliding-window` | 40-60% | Default, balanced |
| Smart Trim | `--context-strategy smart-trim` | 50-70% | Maximum savings |

### 🎯 Common Scenarios

**Long Shopping Flow (30+ steps)**
```bash
browser-copilot shopping-test.md \
  --context-strategy smart-trim \
  --context-window-size 15000
```

**Complex Form Filling**
```bash
browser-copilot form-test.md \
  --context-strategy sliding-window \
  --context-preserve-window 20
```

**Quick Navigation Test**
```bash
# No need for context management
browser-copilot quick-test.md --context-strategy no-op
```

### 📏 Window Size Guidelines

| Test Length | Recommended Window | Strategy |
|-------------|-------------------|----------|
| < 10 steps | 25000 (default) | Any |
| 10-30 steps | 15000-25000 | sliding-window |
| 30+ steps | 10000-15000 | smart-trim |
| Very long | 5000-10000 | smart-trim |
