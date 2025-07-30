#!/bin/bash
# Test script for Human-in-the-Loop detection

echo "=== Testing Human-in-the-Loop Detection ==="
echo

# Test 1: Basic HIL test with LLM detection
echo "Test 1: Google search with HIL trigger (LLM detection)"
echo "----------------------------------------------"
python -m browser_copilot examples/hil-test-google-search.md \
    --provider github_copilot \
    --model gpt-4o \
    --browser chromium \
    --hil-verbose \
    --verbose

echo
echo "Test 2: Same test with pattern-only detection"
echo "--------------------------------------------"
python -m browser_copilot examples/hil-test-google-search.md \
    --provider github_copilot \
    --model gpt-4o \
    --browser chromium \
    --hil-detection-model none \
    --hil-verbose \
    --verbose

echo
echo "Test 3: Test with HIL detection disabled"
echo "---------------------------------------"
python -m browser_copilot examples/hil-test-google-search.md \
    --provider github_copilot \
    --model gpt-4o \
    --browser chromium \
    --no-hil-detection \
    --verbose

echo
echo "=== HIL Detection Tests Complete ==="