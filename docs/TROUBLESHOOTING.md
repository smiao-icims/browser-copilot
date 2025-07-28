# Browser Copilot Troubleshooting Guide 🔧

Quick solutions to common issues.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [ModelForge Configuration](#modelforge-configuration)
3. [Browser & Playwright Issues](#browser--playwright-issues)
4. [Test Execution Problems](#test-execution-problems)
5. [Token & Cost Issues](#token--cost-issues)
6. [Output & Reporting](#output--reporting)
7. [Performance Issues](#performance-issues)
8. [Common Error Messages](#common-error-messages)

## Installation Issues

### "Python 3.11+ required"

**Problem**: ModelForge requires Python 3.11 or higher.

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.11+ using pyenv
curl https://pyenv.run | bash
pyenv install 3.11.8
pyenv global 3.11.8

# Or use your system package manager
# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11
```

### "uv: command not found"

**Problem**: The uv package manager isn't installed.

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

### Dependency Installation Fails

**Problem**: `uv sync` fails with dependency errors.

**Solution**:
```bash
# Clear uv cache
uv cache clean

# Try installing core dependencies directly
pip install langchain langchain-core model-forge-llm playwright questionary
```

## ModelForge Configuration

### "Provider and model must be specified"

**Problem**: ModelForge isn't configured.

**Solution**:
```bash
# Check current configuration
uv run modelforge config show

# If empty, add a provider
uv run modelforge config add --provider github_copilot --model gpt-4o

# Set as default
uv run modelforge config set-default --provider github_copilot --model gpt-4o
```

### GitHub Copilot Authentication Failed

**Problem**: Device flow authentication not completing.

**Solution**:
1. Run the config command:
   ```bash
   uv run modelforge config add --provider github_copilot --model gpt-4o
   ```
2. When prompted, go to https://github.com/login/device
3. Enter the code shown in terminal
4. Authorize the application
5. Wait for terminal to confirm success

### "Invalid API key"

**Problem**: API key for OpenAI/Anthropic is invalid.

**Solution**:
```bash
# Re-add with correct key
uv run modelforge config add --provider openai --model gpt-4 --api-key sk-...

# Or use environment variable
export OPENAI_API_KEY="sk-..."
uv run modelforge config add --provider openai --model gpt-4
```

## Browser & Playwright Issues

### "Browser not found" or "Executable doesn't exist"

**Problem**: Playwright browsers aren't installed.

**Solution**:
```bash
# Install all browsers
npx playwright install

# Install specific browser
npx playwright install chromium
npx playwright install firefox
npx playwright install webkit

# Install with dependencies (Linux)
npx playwright install --with-deps chromium
```

### "npx: command not found"

**Problem**: Node.js isn't installed.

**Solution**:
```bash
# Install Node.js (macOS)
brew install node

# Install Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version  # Should be 18+
npm --version
```

### Browser Launches But Immediately Closes

**Problem**: Browser crashes on startup.

**Solution**:
```bash
# Run with debugging
browser-copilot test.md --save-trace --verbose

# Try different browser
browser-copilot test.md --browser firefox

# Disable GPU acceleration (Linux)
export DISPLAY=:0
browser-copilot test.md --browser chromium
```

### Headless Mode Issues

**Problem**: Tests fail in headless but work in headed mode.

**Solution**:
```bash
# Increase viewport size
browser-copilot test.md --headless --viewport-width 1920 --viewport-height 1080

# Disable web security (testing only)
browser-copilot test.md --headless --ignore-https-errors

# Add wait time for dynamic content
# In your test file, add explicit waits:
# "Wait for [element] to appear"
# "Wait 2 seconds for page to stabilize"
```

## Test Execution Problems

### "Element not found" or "Cannot click element"

**Common Causes**:
1. Page not fully loaded
2. Element is hidden or covered
3. Dynamic content not yet rendered
4. Incorrect selector description

**Solutions**:

```markdown
# Better: Use explicit waits
1. Navigate to https://example.com
2. Wait for page to load completely
3. Wait for "Login" button to be visible
4. Click the "Login" button

# Better: Be specific about elements
1. Click the blue "Submit" button at the bottom of the form
2. Click on the search input with placeholder "Search products..."
3. Click the "X" close button in the top-right corner of the modal
```

### Test Hangs or Times Out

**Problem**: Test execution stops responding.

**Solution**:
```bash
# Set explicit timeout
browser-copilot test.md --timeout 60  # 60 seconds

# Run with verbose to see where it hangs
browser-copilot test.md --verbose

# Check for infinite loops in test
# Avoid: "Keep clicking until X appears"
# Better: "Click up to 3 times or until X appears"
```

### Inconsistent Test Results

**Problem**: Test sometimes passes, sometimes fails.

**Solution**:

Create a reliable system prompt (`reliable.txt`):
```
Always follow these rules for reliable test execution:
1. Wait 2 seconds after any page navigation
2. Wait for elements to be visible before interacting
3. Take a screenshot before reporting any failure
4. If an element isn't found, wait 1 second and try once more
5. Dismiss any cookie banners or popups before proceeding
6. Scroll elements into view before clicking
```

Use: `browser-copilot test.md --system-prompt reliable.txt`

## Token & Cost Issues

### "Context length exceeded"

**Problem**: Test too large for model context window.

**Solutions**:
```bash
# Use high compression
browser-copilot large-test.md --compression-level high

# Split into smaller tests
# Instead of one 100-step test, create five 20-step tests

# Use a model with larger context
uv run modelforge config add --provider anthropic --model claude-3-opus  # 200k context
```

### High Token Usage / Costs

**Problem**: Tests consuming too many tokens.

**Solutions**:
```bash
# Enable compression (30% reduction)
browser-copilot test.md --compression-level high

# Reduce verbosity in tests
# Bad: "Navigate to the homepage at https://example.com and wait for it to fully load"
# Good: "Navigate to https://example.com"

# Monitor usage
browser-copilot test.md --verbose  # Shows token usage

# Use cheaper models for simple tests
uv run modelforge config add --provider openai --model gpt-3.5-turbo
```

### Token Optimization Not Working

**Problem**: Compression level not reducing tokens.

**Solution**:
```bash
# Verify optimization is enabled
browser-copilot test.md --verbose | grep "Token optimization"

# Check that it's not disabled
# Remove: --no-token-optimization

# Try maximum compression
browser-copilot test.md --compression-level high --verbose
```

## Output & Reporting

### Output File Not Created

**Problem**: `--output-file` not generating file.

**Solution**:
```bash
# Check permissions
ls -la $(dirname output.html)

# Use absolute path
browser-copilot test.md --output-file /absolute/path/to/output.html

# Create directory first
mkdir -p reports
browser-copilot test.md --output-file reports/output.html
```

### Reports Missing Information

**Problem**: JSON/HTML reports incomplete.

**Solution**:
```bash
# Ensure test completes successfully
browser-copilot test.md --output-format json --verbose

# Check for errors in verbose output
# Look for "Test execution failed"

# Try different format
browser-copilot test.md --output-format yaml  # More readable for debugging
```

### Screenshots Not Saved

**Problem**: No screenshots in output.

**Solution**:
```bash
# Don't disable screenshots
# Remove: --no-screenshots

# Explicitly request screenshots in test:
# "Take a screenshot of the current page"
# "Capture a screenshot showing the error"

# Check screenshot directory
ls ~/.browser_copilot/sessions/*/screenshots/
# or on Windows:
# dir %LOCALAPPDATA%\browser_copilot\sessions\*\screenshots\
```

## Performance Issues

### Tests Running Slowly

**Problem**: Test execution is slower than expected.

**Solutions**:
```bash
# Use headless mode (faster)
browser-copilot test.md --headless

# Enable token optimization
browser-copilot test.md --compression-level high

# Reduce screenshot frequency
# Only screenshot important states, not every step

# Use faster model
uv run modelforge config add --provider openai --model gpt-3.5-turbo
```

### High Memory Usage

**Problem**: Browser Copilot consuming too much RAM.

**Solution**:
```bash
# Close other applications
# Run one test at a time
# Use headless mode
browser-copilot test.md --headless

# Limit browser cache
export PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright
```

## Configuration Wizard Issues

### "Questionary not installed"

**Problem**: The interactive wizard requires the questionary library.

**Solution**:
```bash
# Install with uv
uv pip install questionary

# Or with pip
pip install questionary

# Then run wizard again
browser-copilot --setup-wizard
```

### Wizard Doesn't Show Arrow Navigation

**Problem**: Terminal doesn't support interactive mode.

**Solution**:
1. Use a modern terminal (iTerm2, Windows Terminal, etc.)
2. Ensure terminal supports ANSI escape codes
3. Try running in a different terminal emulator

### "No configuration found" Keeps Appearing

**Problem**: Configuration not saved properly.

**Solution**:
```bash
# Check if config exists
ls ~/.browser_copilot/settings/config.json

# Run wizard and ensure you save at the end
browser-copilot --setup-wizard

# Verify configuration was saved
cat ~/.browser_copilot/settings/config.json
```

## Common Error Messages

### "No module named 'browser_copilot'"

```bash
# Ensure you're in the project directory
cd /path/to/browser-copilot

# Reinstall
uv sync

# Or use python directly
python -m browser_copilot.cli test.md
```

### "MCP server failed to start"

```bash
# Install Playwright MCP server
npm install -g @playwright/mcp

# Verify installation
npx @playwright/mcp --version

# Check Node.js version
node --version  # Must be 18+
```

### "ValueError: model_max_prompt_tokens_exceeded"

```bash
# Your test is too large. Solutions:
# 1. Use high compression
browser-copilot test.md --compression-level high

# 2. Split the test
# 3. Use model with larger context
uv run modelforge config show  # Check current model limits
```

### "Connection refused" or "ECONNREFUSED"

```bash
# For API providers: Check internet connection
ping api.openai.com

# For local models: Ensure service is running
# Example for Ollama:
ollama serve

# Check firewall settings
sudo ufw status  # Linux
```

## Getting More Help

### Enable Debug Logging

```bash
# Maximum verbosity
browser-copilot test.md --verbose --save-trace --save-session

# Check logs
tail -f ~/.browser_copilot/logs/browser_copilot_*.log
```

### Collect Diagnostic Information

When reporting issues, include:

```bash
# System info
uname -a  # OS info
python --version
node --version
npx playwright --version

# Browser Copilot info
cd browser-copilot && git rev-parse HEAD  # Git commit
uv run modelforge config show  # Model config

# Error details
browser-copilot test.md --verbose 2>&1 | tee error.log
```

### Community Support

1. **GitHub Issues**: [github.com/smiao-icims/browser-copilot/issues](https://github.com/smiao-icims/browser-copilot/issues)
2. **Discussions**: [github.com/smiao-icims/browser-copilot/discussions](https://github.com/smiao-icims/browser-copilot/discussions)
3. **ModelForge Issues**: [github.com/smiao-icims/model-forge](https://github.com/smiao-icims/model-forge)

### Quick Fixes Checklist

☐ Python 3.11+ installed?
☐ Node.js 18+ installed?
☐ uv installed and in PATH?
☐ Dependencies installed with `uv sync`?
☐ ModelForge configured with `modelforge config show`?
☐ Playwright browsers installed with `npx playwright install`?
☐ Test file exists and readable?
☐ Running from browser-copilot directory?
☐ Internet connection for API calls?
☐ Sufficient disk space for logs/screenshots?