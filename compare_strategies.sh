#!/bin/bash
# Compare context management strategies

echo "Testing with NO-OP strategy (baseline - no context management)..."
echo "================================================"
python -m browser_copilot test_context_strategy.md \
    --provider github_copilot \
    --model gpt-4o \
    --context-strategy no-op \
    --verbose

echo -e "\n\nTesting with SLIDING-WINDOW strategy (optimized context management)..."
echo "================================================"
python -m browser_copilot test_context_strategy.md \
    --provider github_copilot \
    --model gpt-4o \
    --context-strategy sliding-window \
    --verbose

echo -e "\n\nDone! Check the token usage in both reports to see the difference."