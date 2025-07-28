# Browser Copilot Quick Start Guide 🚀

Get up and running with Browser Copilot in 3 minutes! This guide shows you the fastest way to start testing.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First Test](#first-test)
- [Common Use Cases](#common-use-cases)
- [Tips & Tricks](#tips--tricks)

## Prerequisites

### Required Software
1. **Python 3.11+** - Required by ModelForge
2. **Node.js 18+** - Required for Playwright browser automation
3. **uv** - Fast Python package manager (recommended)

### Quick Install Prerequisites

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Check installations
python --version  # Should be 3.11+
node --version    # Should be 18+
uv --version      # Should show version
```

## 🎯 The 3-Minute Setup

### Step 1: Install Browser Copilot

```bash
# Clone the repository
git clone https://github.com/smiao-icims/browser-copilot.git
cd browser-copilot

# Install dependencies with uv
uv sync
```

### Step 2: Run the Setup Wizard

```bash
uv run browser-copilot --setup-wizard
```

The interactive wizard will:
- 🤖 Help you choose an LLM provider (GitHub Copilot recommended - no API key!)
- 🔐 Set up authentication (device flow for GitHub Copilot)
- 🌐 Configure your browser (auto-detects installed browsers)
- ✅ Validate everything with a test prompt

💡 **Tip**: Just press Enter to accept the recommended defaults!

### Step 3: Write Your First Test

Create a file called `test.md` with natural language instructions:

```markdown
# My First Browser Test

1. Go to https://www.example.com
2. Verify the page title contains "Example Domain"
3. Take a screenshot
```

### Step 4: Run Your Test!

```bash
uv run browser-copilot test.md
```

That's it! You should see Browser Copilot:
1. Open a browser window
2. Navigate to example.com
3. Verify the title
4. Take a screenshot
5. Generate a detailed report

## 📝 Writing Tests in Natural Language

Browser Copilot understands tests written in plain English. Just number your steps:

### Example: Wikipedia Search Test

```markdown
# Wikipedia Search Test

1. Navigate to https://www.wikipedia.org
2. Search for "artificial intelligence"
3. Verify the results page shows information about AI
4. Click on the first search result
5. Take a screenshot of the article
```

### Example: Login Test

```markdown
# Login Test

1. Go to https://app.example.com/login
2. Enter "user@example.com" in the email field
3. Enter "password123" in the password field
4. Click the "Sign In" button
5. Verify the dashboard page loads
6. Check that "Welcome back" message appears
```

### Running Tests

```bash
# Basic run (with browser window)
uv run browser-copilot wikipedia-test.md

# Run headless (no browser window)
uv run browser-copilot wikipedia-test.md --headless

# Run with detailed debugging
uv run browser-copilot wikipedia-test.md --verbose

# Generate HTML report
uv run browser-copilot wikipedia-test.md --output-format html --output-file report.html
```

## Common Use Cases

### 1. E-commerce Testing

We provide a complete e-commerce example that you can run immediately:

```bash
# Run the SauceDemo shopping example
uv run browser-copilot examples/saucedemo-shopping.md

# Run it headless with HTML report
uv run browser-copilot examples/saucedemo-shopping.md --headless --output-format html --output-file report.html
```

**What this example tests:**
- User authentication (login/logout)
- Product browsing and selection
- Shopping cart management
- Multi-step checkout process
- Order confirmation

👉 View the full test: `cat examples/saucedemo-shopping.md`

### 2. Form Submission Testing

```markdown
# Contact Form Test

1. Navigate to your-website.com/contact
2. Wait for the page to load
3. Click on the "Name" field
4. Type "John Doe"
5. Click on the "Email" field
6. Type "john.doe@example.com"
7. Click on the "Message" field
8. Type "This is a test message from Browser Copilot"
9. Click the "Submit" button
10. Wait for confirmation message
11. Verify "Thank you" message appears
12. Take a screenshot of the confirmation
```

### 3. Login Flow Testing

```markdown
# Login Test

1. Navigate to app.example.com/login
2. Click "Accept Cookies" if present
3. Enter "testuser@example.com" in the email field
4. Enter "Test123!" in the password field
5. Click "Remember me" checkbox
6. Click the "Sign In" button
7. Wait for dashboard to load
8. Verify "Welcome back" text is visible
9. Verify user menu shows "testuser"
10. Take a screenshot of the dashboard
```

### 4. AI-Powered Search Testing

Test modern AI search features with our Google AI example:

```bash
# Run the Google AI search example
uv run browser-copilot examples/google-ai-search.md

# Try with your own search query
uv run browser-copilot examples/google-ai-search.md --verbose
```

**What this example demonstrates:**
- Activating Google's AI search mode
- Executing search queries
- Validating AI-generated responses
- Handling different search scenarios
- Screenshot capture of results

👉 View the full test: `cat examples/google-ai-search.md`

## Tips & Tricks

### 1. Save Time with Aliases

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias bp="uv run browser-copilot"
alias bph="uv run browser-copilot --headless"
alias bpv="uv run browser-copilot --verbose"

# Usage
bp my-test.md
bph my-test.md --output-format json
```

### 2. Use Custom System Prompts for Better Reliability

Create `reliable-prompt.txt`:
```
You are a careful QA engineer. Follow these rules:
1. Always wait 2 seconds after navigation
2. Take screenshots before and after major actions
3. If an element isn't found, wait 1 second and retry
4. Use specific selectors when possible
5. Verify each action completed before proceeding
```

Use it:
```bash
bp my-test.md --system-prompt reliable-prompt.txt
```

### 3. Optimize Token Usage for Cost Savings

```bash
# Low optimization (10% reduction) - most reliable
bp my-test.md --compression-level low

# Medium optimization (20% reduction) - default
bp my-test.md --compression-level medium

# High optimization (30% reduction) - most cost-effective
bp my-test.md --compression-level high

# See token usage in output
bp my-test.md --verbose
```

### 4. Different Output Formats for Different Needs

```bash
# HTML report for sharing
bp test.md --output-format html --output-file report.html

# JSON for CI/CD integration
bp test.md --output-format json --output-file results.json

# JUnit for test frameworks
bp test.md --output-format junit --output-file junit.xml

# YAML for configuration management
bp test.md --output-format yaml --output-file results.yaml
```

### 5. Debug Failed Tests

```bash
# Maximum visibility
bp failed-test.md --verbose --no-token-optimization

# Save browser session for debugging
bp failed-test.md --save-trace --save-session

# Check logs
cat ~/Library/Application\ Support/browser_copilot/logs/browser_copilot_*.log
```

### 6. CI/CD Integration

```bash
# Headless, JSON output, fail on error
bp regression-test.md --headless --output-format json --output-file results.json || exit 1

# With timeout for CI pipelines
bp smoke-test.md --headless --timeout 300
```

### 7. Batch Testing

```bash
# Run multiple tests
for test in tests/*.md; do
    echo "Running $test..."
    bp "$test" --headless --output-file "results/$(basename $test .md).json"
done
```

## Next Steps

1. **Explore Examples**: Check out the `examples/` directory for more test scenarios
2. **Read the Full Documentation**: See [README.md](../README.md) for all features
3. **Custom Configurations**: Learn about persistent settings in [Configuration Guide](./CONFIGURATION.md)
4. **Troubleshooting**: See [Troubleshooting Guide](./TROUBLESHOOTING.md) for common issues

## Getting Help

- **Issue with Browser Copilot?** Check our [GitHub Issues](https://github.com/smiao-icims/browser-copilot/issues)
- **ModelForge Problems?** Run `uv run modelforge config check`
- **Playwright Issues?** Try `npx playwright install`

Happy Testing! 🎉