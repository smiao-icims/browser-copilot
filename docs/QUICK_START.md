# Browser Pilot Quick Start Guide 🚀

Get up and running with Browser Pilot in 5 minutes!

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

## Installation

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/browser-pilot.git
cd browser-pilot

# Install dependencies with uv (recommended)
uv sync

# Or if you prefer pip
pip install -r requirements.txt
```

### 2. Configure ModelForge (One-time setup)

```bash
# Option A: Use GitHub Copilot (easiest)
uv run modelforge config add --provider github_copilot --model gpt-4o

# Option B: Use OpenAI
uv run modelforge config add --provider openai --model gpt-4 --api-key YOUR_KEY

# Option C: Use Anthropic
uv run modelforge config add --provider anthropic --model claude-3-sonnet --api-key YOUR_KEY

# Verify configuration
uv run modelforge config show
```

### 3. Test Installation

```bash
# Run a simple test
echo "Navigate to example.com and verify the title" | uv run browser-pilot -
```

## First Test

### Create Your First Test File

Create `my-first-test.md`:

```markdown
# My First Browser Test

1. Navigate to https://www.wikipedia.org
2. Click on the search box
3. Type "artificial intelligence"
4. Press Enter
5. Wait for results to load
6. Verify the page contains "Artificial intelligence"
7. Take a screenshot of the results
```

### Run the Test

```bash
# Run with visual browser (see what's happening)
uv run browser-pilot my-first-test.md

# Run headless (faster, no browser window)
uv run browser-pilot my-first-test.md --headless

# Run with detailed output
uv run browser-pilot my-first-test.md --verbose
```

## Common Use Cases

### 1. E-commerce Testing

```markdown
# Shopping Cart Test

1. Navigate to https://www.saucedemo.com
2. Type "standard_user" in the username field
3. Type "secret_sauce" in the password field
4. Click the login button
5. Wait for the products page to load
6. Click "Add to cart" on the first product
7. Click the shopping cart icon
8. Verify the cart contains 1 item
9. Click "Checkout"
10. Fill in checkout information:
    - First name: "Test"
    - Last name: "User"
    - Zip code: "12345"
11. Click "Continue"
12. Verify the total price is displayed
13. Take a screenshot of the checkout summary
```

Run it:
```bash
uv run browser-pilot shopping-test.md --headless --output-format html --output-file report.html
```

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
8. Type "This is a test message from Browser Pilot"
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

### 4. Search Functionality Testing

```markdown
# Search Test

1. Navigate to your-site.com
2. Click on the search icon or search box
3. Type "product name"
4. Press Enter or click search button
5. Wait for results to load
6. Verify search results contain "product name"
7. Verify at least 5 results are shown
8. Click on the first result
9. Verify product page loads
10. Take a screenshot
```

## Tips & Tricks

### 1. Save Time with Aliases

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias bp="uv run browser-pilot"
alias bph="uv run browser-pilot --headless"
alias bpv="uv run browser-pilot --verbose"

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
cat ~/Library/Application\ Support/browser_pilot/logs/browser_pilot_*.log
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

- **Issue with Browser Pilot?** Check our [GitHub Issues](https://github.com/yourusername/browser-pilot/issues)
- **ModelForge Problems?** Run `uv run modelforge config check`
- **Playwright Issues?** Try `npx playwright install`

Happy Testing! 🎉