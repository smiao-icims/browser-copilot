#!/bin/bash
# Compare different context management strategies

echo "=== Comparing Context Management Strategies ==="
echo ""

# Test file
TEST_FILE="examples/saucedemo-shopping.md"
WINDOW_SIZE=10000

echo "1. Testing no-op strategy (baseline)..."
echo "----------------------------------------"
uv run browser-copilot "$TEST_FILE" \
  --context-strategy no-op \
  --verbose 2>&1 | grep -E "(Tokens used:|Duration:|Status:)" | tail -3

echo ""
echo "2. Testing sliding-window strategy (custom implementation)..."
echo "------------------------------------------------------------"
uv run browser-copilot "$TEST_FILE" \
  --context-strategy sliding-window \
  --context-window-size $WINDOW_SIZE \
  --verbose 2>&1 | grep -E "(Tokens used:|Duration:|Status:|Token reduction:)" | tail -4

echo ""
echo "3. Testing langchain-trim strategy (LangChain's trim_messages)..."
echo "----------------------------------------------------------------"
uv run browser-copilot "$TEST_FILE" \
  --context-strategy langchain-trim \
  --context-window-size $WINDOW_SIZE \
  --verbose 2>&1 | grep -E "(Tokens used:|Duration:|Status:|Message reduction:)" | tail -4

echo ""
echo "=== Summary ==="
echo "- no-op: No context management (baseline)"
echo "- sliding-window: Custom implementation with tool pair preservation"
echo "- langchain-trim: LangChain's built-in trim_messages utility"
echo ""
echo "Note: Lower token usage indicates better context management"