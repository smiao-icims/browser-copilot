#!/bin/bash

# Browser Pilot Example Test Runner
# This script runs a simple example test to verify your installation

echo "🚀 Browser Pilot Example Test Runner"
echo "===================================="
echo ""

# Check if browser-pilot is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check if the module can be imported
if ! uv run python -c "import browser_pilot" 2>/dev/null; then
    echo "⚠️  Browser Pilot module not found. Installing..."
    uv sync
fi

# Check for example file
if [ ! -f "examples/google-ai-search.md" ]; then
    echo "❌ Example test file not found. Please run from the browser-pilot directory."
    exit 1
fi

# Default values
PROVIDER="${BROWSER_PILOT_PROVIDER:-github_copilot}"
MODEL="${BROWSER_PILOT_MODEL:-gpt-4o}"
BROWSER="${BROWSER_PILOT_BROWSER:-chromium}"

echo "Configuration:"
echo "  Provider: $PROVIDER"
echo "  Model: $MODEL"
echo "  Browser: $BROWSER"
echo ""
echo "You can override these with environment variables:"
echo "  BROWSER_PILOT_PROVIDER, BROWSER_PILOT_MODEL, BROWSER_PILOT_BROWSER"
echo ""
echo "Starting test in 3 seconds..."
sleep 3

# Run the example test
uv run python -m browser_pilot \
    --test-suite examples/google-ai-search.md \
    --provider "$PROVIDER" \
    --model "$MODEL" \
    --browser "$BROWSER" \
    --verbose

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Example test completed successfully!"
    echo "Check the 'reports' directory for detailed results."
else
    echo ""
    echo "❌ Example test failed. Please check the error messages above."
    echo "Common issues:"
    echo "  - Ensure ModelForge is configured: modelforge list"
    echo "  - Ensure MCP server is installed: npm install -g @playwright/mcp"
    echo "  - Check browser is installed: npx playwright install $BROWSER"
fi