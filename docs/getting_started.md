# Getting Started with Browser Copilot

This guide will help you get up and running with Browser Copilot in minutes.

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.8 or higher** installed
2. **Node.js and npm** installed (required for Playwright MCP server)
3. **ModelForge** configured with at least one LLM provider

## Installation

### 1. Install Browser Copilot

```bash
# Clone the repository
git clone https://github.com/smiao-icims/browser-copilot.git
cd browser-copilot

# Install the package
pip install -e .

# Or install from PyPI (when published)
pip install browser-copilot
```

### 2. Install Playwright MCP Server

Browser Copilot uses the Playwright MCP server for browser automation:

```bash
# Install the MCP server globally
npm install -g @playwright/mcp

# Verify installation
npx @playwright/mcp --help
```

### 3. Configure ModelForge

Browser Copilot uses ModelForge for LLM management. Set up at least one provider:

```bash
# Example: Configure GitHub Copilot
modelforge auth github_copilot

# Or configure OpenAI
modelforge config set openai.api_key YOUR_API_KEY

# Verify configuration
modelforge list
```

## Writing Your First Test

Create a simple test file `hello_world.md`:

```markdown
# Hello World Test

1. Navigate to https://example.com
2. Wait for the page to load
3. Take a screenshot
4. Verify the page title contains "Example Domain"
5. Find and report the main heading text
6. Close the browser
```

## Running Tests

### Basic Usage

```bash
browser-copilot --test-suite hello_world.md --provider github_copilot --model gpt-4o
```

### Common Options

```bash
# Run in headless mode (no browser UI)
browser-copilot --test-suite test.md --provider github_copilot --model gpt-4o --headless

# Use Firefox instead of Chrome
browser-copilot --test-suite test.md --provider github_copilot --model gpt-4o --browser firefox

# Custom viewport size
browser-copilot --test-suite test.md --provider github_copilot --model gpt-4o --viewport-size 1280,720

# Verbose output
browser-copilot --test-suite test.md --provider github_copilot --model gpt-4o --verbose
```

## Understanding the Output

After running a test, you'll see:

1. **Console Output**: Real-time progress and results
2. **Report File**: Detailed markdown report in `reports/report_TIMESTAMP.md`
3. **Results File**: JSON data in `reports/results_TIMESTAMP.json`
4. **Screenshots**: Any captured screenshots in the reports directory

### Example Output

```
╔═══════════════════════════════════════════╗
║      Browser Copilot v2.0                   ║
║   Simple • Reliable • Token Efficient     ║
╚═══════════════════════════════════════════╝

📄 Test Suite: hello_world.md
   Size: 234 chars

🤖 Provider: github_copilot
   Model: gpt-4o

🚀 Executing test...
   Browser: chromium
   Mode: Headed

--------------------------------------------------
Status: ✅ PASSED
Duration: 15.2s
Steps: 8

📊 Token Usage:
   Total: 5,432
   Prompt: 5,102
   Completion: 330
   Cost: $0.0234

📝 Results saved:
   - report: report_20250126_143022.md
   - results: results_20250126_143022.json
```

## Next Steps

- Check out the [examples](../examples/) directory for more test scenarios
- Read the [Test Writing Guide](test_writing_guide.md) for best practices
- Learn about [Advanced Features](advanced_features.md)
- Join our community for support and updates

## Troubleshooting

### Common Issues

1. **"npx: command not found"**
   - Install Node.js and npm from https://nodejs.org

2. **"Provider not found"**
   - Run `modelforge list` to see available providers
   - Configure a provider with `modelforge auth <provider>`

3. **"Browser not installed"**
   - The MCP server will prompt to install browsers
   - Or manually install: `npx playwright install chromium`

4. **Token limit exceeded**
   - Use simpler test suites
   - Break complex tests into smaller phases
   - Consider using a model with higher token limits

### Getting Help

- Create an issue on [GitHub](https://github.com/smiao-icims/browser-copilot/issues)
- Check the [FAQ](faq.md)
- Read the [API Reference](api_reference.md)