# Context Management Quick Reference

## 🚀 Quick Start

```bash
# Just use the defaults (sliding window, 50k tokens)
browser-copilot test.md

# Maximum token savings
browser-copilot test.md --context-strategy langchain-trim --context-window-size 10000

# Debug what's happening
browser-copilot test.md --verbose
```

## 📊 Strategy Comparison

| Strategy | Command | Token Savings | Best For |
|----------|---------|---------------|----------|
| No-Op | `--context-strategy no-op` | 0% | Debugging |
| Sliding Window | `--context-strategy sliding-window` | 40-60% | Default, balanced |
| LangChain Trim | `--context-strategy langchain-trim` | 50-70% | Maximum savings |

## 🎯 Common Scenarios

### Long Shopping Flow (30+ steps)
```bash
browser-copilot shopping-test.md \
  --context-strategy langchain-trim \
  --context-window-size 15000
```

### Complex Form Filling
```bash
browser-copilot form-test.md \
  --context-strategy sliding-window \
  --context-preserve-window 20
```

### Quick Navigation Test
```bash
# No need for context management
browser-copilot quick-test.md --context-strategy no-op
```

### Debugging Context Issues
```bash
browser-copilot test.md \
  --context-strategy sliding-window \
  --verbose 2>&1 | grep "Hook"
```

## 📏 Window Size Guidelines

| Test Length | Recommended Window | Strategy |
|-------------|-------------------|----------|
| < 10 steps | 50000 (default) | Any |
| 10-30 steps | 15000-25000 | sliding-window |
| 30+ steps | 10000-15000 | langchain-trim |
| Very long | 5000-10000 | langchain-trim |

## 🔍 Monitoring

Watch for these in verbose output:
```
[Sliding Window Hook] Processing 45 messages
[Sliding Window Hook] Token reduction: 48.9%
[LangChain Trim Hook] Message reduction: 65.0%
```

## ⚠️ Troubleshooting

### "100% message reduction" error
```bash
# Increase window size
browser-copilot test.md --context-window-size 20000
```

### Agent loses context
```bash
# Preserve more messages
browser-copilot test.md \
  --context-preserve-window 30 \
  --context-preserve-last 15
```

### Need to see what's kept/dropped
```bash
# Use verbose mode
browser-copilot test.md --verbose | grep "DROPPED"
```