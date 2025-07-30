# Browser Copilot Configuration Guide ⚙️

Advanced configuration options for power users.

## Table of Contents

1. [Configuration Hierarchy](#configuration-hierarchy)
2. [Settings File](#settings-file)
3. [Environment Variables](#environment-variables)
4. [Command Line Options](#command-line-options)
5. [Model Configuration](#model-configuration)
6. [Browser Configuration](#browser-configuration)
7. [Storage Configuration](#storage-configuration)
8. [Performance Tuning](#performance-tuning)
9. [Custom System Prompts](#custom-system-prompts)
10. [CI/CD Configuration](#cicd-configuration)

## Configuration Hierarchy

Browser Copilot uses a hierarchical configuration system (highest priority first):

1. **Command Line Arguments** - Override everything
2. **Environment Variables** - Override config files
3. **User Settings File** - `~/.browser_copilot/settings/config.json`
4. **Project Config File** - `./browser-copilot-config.json`
5. **Default Values** - Built-in defaults

## Settings File

### Location

- **macOS**: `~/Library/Application Support/browser_copilot/settings/config.json`
- **Linux**: `~/.browser_copilot/settings/config.json`
- **Windows**: `%LOCALAPPDATA%\browser_copilot\settings\config.json`

### Example Configuration

```json
{
  "provider": "github_copilot",
  "model": "gpt-4o",
  "browser": "chromium",
  "headless": false,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "timeout": 300,
  "compression_level": "medium",
  "context_strategy": "sliding-window",
  "hil_enabled": true,
  "enable_screenshots": true,
  "output_format": "markdown",
  "storage": {
    "logs_retention_days": 7,
    "screenshots_retention_days": 30,
    "reports_retention_days": 90
  },
  "token_optimization": true,
  "verbose": false
}
```

### Creating Settings File

```bash
# Create with current options
browser-copilot examples/google-ai-search.md --provider openai --model gpt-4 --headless --save-config

# Edit directly
mkdir -p ~/.browser_copilot/settings
nano ~/.browser_copilot/settings/config.json
```

## Environment Variables

### Core Settings

```bash
# LLM Configuration
export BROWSER_PILOT_PROVIDER="openai"
export BROWSER_PILOT_MODEL="gpt-4"

# Browser Settings
export BROWSER_PILOT_BROWSER="firefox"
export BROWSER_PILOT_HEADLESS="true"
export BROWSER_PILOT_VIEWPORT_WIDTH="1280"
export BROWSER_PILOT_VIEWPORT_HEIGHT="720"

# Performance
export BROWSER_PILOT_COMPRESSION_LEVEL="high"
export BROWSER_PILOT_TIMEOUT="600"
export BROWSER_PILOT_TOKEN_OPTIMIZATION="true"

# Output
export BROWSER_PILOT_OUTPUT_FORMAT="json"
export BROWSER_PILOT_VERBOSE="true"
export BROWSER_PILOT_QUIET="false"

# Storage
export BROWSER_PILOT_SCREENSHOTS="true"
export BROWSER_PILOT_LOGS_RETENTION_DAYS="14"
```

### Using .env File

Note: .env file support is not built into Browser Copilot. Use environment variables directly:

```bash
# Set environment variables
export BROWSER_PILOT_PROVIDER=anthropic
export BROWSER_PILOT_MODEL=claude-3-opus
export BROWSER_PILOT_HEADLESS=true
export BROWSER_PILOT_COMPRESSION_LEVEL=high

# Or source from a file
source .env
browser-copilot examples/saucedemo-shopping.md
```

## Command Line Options

### Complete Options Reference

```bash
browser-copilot [OPTIONS] test_scenario

Positional Arguments:
  test_scenario         Test file path or '-' for stdin

Model Configuration:
  --provider PROVIDER   LLM provider (github_copilot, openai, anthropic)
  --model MODEL         Model name (gpt-4o, gpt-4, claude-3-opus)

Browser Options:
  --browser BROWSER     Browser: chromium, firefox, webkit, safari, edge
  --headless            Run without browser window
  --viewport-width W    Browser width in pixels (default: 1280)
  --viewport-height H   Browser height in pixels (default: 720)

Playwright Options:
  --device DEVICE       Emulate device (e.g., "iPhone 12")
  --user-agent STRING   Custom user agent
  --proxy-server URL    Proxy server (e.g., http://proxy:8080)
  --proxy-bypass LIST   Comma-separated bypass domains
  --ignore-https-errors Ignore certificate errors
  --block-service-workers Block service workers
  --save-trace          Save Playwright trace
  --save-session        Save browser session
  --allowed-origins LIST Semicolon-separated allowed origins
  --blocked-origins LIST Semicolon-separated blocked origins
  --no-isolated         Disable isolated browser context

Output Options:
  --output-format FMT   Output format: json, yaml, xml, junit, html, markdown
  --output-file FILE    Save output to file
  -v, --verbose         Detailed debug output
  -q, --quiet           Suppress non-error output

Optimization:
  --no-screenshots      Disable screenshots
  --no-token-optimization Disable token optimization
  --compression-level   Token optimization: none, low, medium, high

Testing Options:
  --system-prompt FILE  Custom system prompt file
  --timeout SECONDS     Test execution timeout in seconds
  --enhance-test        Use AI to enhance test scenario before execution

Configuration:
  --config FILE         Load config from file
  --save-config         Save current options as default

Context Management:
  --context-strategy    Strategy: no-op, sliding-window, smart-trim
  --context-window-size SIZE  Max tokens for context window
  --context-preserve-window N  Messages to always preserve
  --context-preserve-first N   Keep first N messages
  --context-preserve-last N    Keep last N messages

Human-in-the-Loop:
  --hil                 Enable HIL mode (enabled by default)
  --no-hil              Disable HIL for fully autonomous execution
  --hil-interactive     Enable interactive HIL mode
```

## Model Configuration

### Provider-Specific Settings

#### GitHub Copilot
```bash
# No API key needed - uses device flow auth
uv run modelforge config add --provider github_copilot --model gpt-4o

# Available models:
# - gpt-4o (recommended)
# - gpt-3.5-turbo
# - claude-3-sonnet
```

#### OpenAI
```bash
# With API key
export OPENAI_API_KEY="sk-..."
uv run modelforge config add --provider openai --model gpt-4

# Available models:
# - gpt-4-turbo-preview (128k context)
# - gpt-4 (8k context)
# - gpt-3.5-turbo (16k context)
```

#### Anthropic
```bash
# With API key
export ANTHROPIC_API_KEY="sk-ant-..."
uv run modelforge config add --provider anthropic --model claude-3-opus

# Available models:
# - claude-3-opus (200k context)
# - claude-3-sonnet (200k context)
# - claude-2.1 (100k context)
```

### Model Selection Strategy

```bash
# For simple tests (fast, cheap)
browser-copilot examples/google-ai-search.md --provider openai --model gpt-3.5-turbo

# For complex tests (reliable, smart)
browser-copilot examples/saucedemo-shopping.md --provider anthropic --model claude-3-opus

# For long tests (large context)
browser-copilot examples/context-heavy-test.md --provider anthropic --model claude-3-opus

# For cost-sensitive (with optimization)
browser-copilot examples/weather-forecast.md --provider openai --model gpt-3.5-turbo --compression-level high
```

## Browser Configuration

### Browser-Specific Settings

#### Chromium/Chrome
```bash
# Best compatibility
browser-copilot examples/google-ai-search.md --browser chromium

# With extensions support
browser-copilot examples/saucedemo-shopping.md --browser chrome --no-isolated
```

#### Firefox
```bash
# Better privacy
browser-copilot examples/google-ai-search.md --browser firefox

# With specific profile
FFIREFOX_PROFILE_PATH=/path/to/profile browser-copilot examples/weather-forecast.md --browser firefox
```

#### Safari/WebKit
```bash
# macOS testing
browser-copilot examples/google-ai-search.md --browser safari  # or webkit

# Mobile Safari emulation
browser-copilot examples/weather-forecast.md --browser webkit --device "iPhone 12"
```

### Mobile Device Emulation

```bash
# iPhone testing
browser-copilot examples/google-ai-search.md --device "iPhone 12 Pro"
browser-copilot examples/weather-forecast.md --device "iPhone 13 Pro Max"

# Android testing
browser-copilot examples/saucedemo-shopping.md --device "Pixel 5"
browser-copilot examples/google-ai-search.md --device "Galaxy S21"

# Tablet testing
browser-copilot examples/saucedemo-shopping.md --device "iPad Pro"
browser-copilot examples/weather-forecast.md --device "Galaxy Tab S7"

# List all devices
npx playwright devices
```

### Custom Viewport Sizes

```bash
# Desktop sizes
browser-copilot examples/saucedemo-shopping.md --viewport-width 1920 --viewport-height 1080  # Full HD
browser-copilot examples/google-ai-search.md --viewport-width 2560 --viewport-height 1440  # 2K
browser-copilot examples/weather-forecast.md --viewport-width 3840 --viewport-height 2160  # 4K

# Mobile sizes
browser-copilot examples/google-ai-search.md --viewport-width 375 --viewport-height 667   # iPhone 6/7/8
browser-copilot examples/weather-forecast.md --viewport-width 414 --viewport-height 896   # iPhone XR/11

# Tablet sizes
browser-copilot examples/saucedemo-shopping.md --viewport-width 768 --viewport-height 1024  # iPad
browser-copilot examples/icims-ats-job-search.md --viewport-width 1024 --viewport-height 1366 # iPad Pro
```

## Storage Configuration

### Directory Structure

```
~/.browser_copilot/
├── sessions/
│   └── test-name_20250126_143022/
│       ├── logs/
│       │   └── verbose_log.txt
│       ├── reports/
│       │   ├── report_20250126_143022.md
│       │   └── results_20250126_143022.json
│       └── screenshots/
│           └── screenshot_20250126_143022.png
├── logs/
│   └── browser_copilot_20250126_143022.log
├── settings/
│   └── config.json
├── cache/
└── memory/
```

### Retention Settings

```json
{
  "storage": {
    "logs_retention_days": 7,
    "screenshots_retention_days": 30,
    "reports_retention_days": 90,
    "cache_retention_days": 1,
    "max_storage_gb": 10
  }
}
```

### Manual Cleanup

```bash
# Clean specific types
rm -rf ~/.browser_copilot/sessions/*/screenshots/
rm -rf ~/.browser_copilot/logs/*.log

# Keep only recent sessions
find ~/.browser_copilot/sessions -type d -mtime +30 -exec rm -rf {} +

# Clean by size
du -sh ~/.browser_copilot/* | sort -rh | head -20
```

## Performance Tuning

### Token Optimization Strategies

```bash
# Maximum performance (may reduce reliability)
browser-copilot examples/weather-forecast.md \
  --compression-level high \
  --no-screenshots \
  --headless \
  --provider openai \
  --model gpt-3.5-turbo

# Balanced performance
browser-copilot examples/google-ai-search.md \
  --compression-level medium \
  --headless \
  --viewport-width 1280 \
  --viewport-height 720

# Maximum reliability (higher cost)
browser-copilot examples/saucedemo-shopping.md \
  --no-token-optimization \
  --verbose \
  --provider anthropic \
  --model claude-3-opus
```

### Timeout Configuration

```bash
# Quick tests
export BROWSER_PILOT_TIMEOUT=60  # 1 minute

# Standard tests
export BROWSER_PILOT_TIMEOUT=300  # 5 minutes (default)

# Long-running tests
export BROWSER_PILOT_TIMEOUT=1800  # 30 minutes

# No timeout (dangerous!)
export BROWSER_PILOT_TIMEOUT=0
```

### Running Multiple Tests

```bash
# Run tests sequentially
for test in tests/*.md; do
  echo "Running $test..."
  browser-copilot "$test" --headless
done

# Or use a shell script
#!/bin/bash
for test in "$@"; do
  browser-copilot "$test" --headless --output-file "results/${test%.md}.json"
done
```

## Custom System Prompts

### Creating Effective Prompts

#### Reliability-Focused
`reliable-testing.txt`:
```
You are a meticulous QA engineer focused on test reliability.

Rules:
1. Always wait for page loads to complete before proceeding
2. Wait for animations to finish before interacting with elements
3. If an element is not immediately found, wait up to 5 seconds
4. Take screenshots before and after critical actions
5. Scroll elements into view before clicking
6. Handle common interruptions:
   - Cookie consent banners: Accept and proceed
   - Newsletter popups: Close and continue
   - Chat widgets: Minimize or ignore
7. For form inputs, clear existing values before typing
8. Verify each action completed before moving to next step
```

#### Performance-Focused
`fast-testing.txt`:
```
You are an efficient test automation engineer.

Optimize for speed:
1. Minimize waits - only wait when necessary
2. Skip animations with immediate interactions
3. Take screenshots only for failures
4. Use fast selectors (IDs over text)
5. Batch similar actions together
6. Don't verify obvious outcomes
```

#### Domain-Specific
`ecommerce-testing.txt`:
```
You are testing an e-commerce platform.

Domain knowledge:
1. Always check inventory before adding to cart
2. Verify prices update with quantity changes
3. Check for applied discounts and coupons
4. Confirm shipping calculations
5. Validate payment form security indicators
6. Save order confirmation numbers
7. Check for email confirmation messages
```

### Using Custom Prompts

```bash
# Single test
browser-copilot examples/saucedemo-shopping.md --system-prompt reliable-testing.txt

# Set as default
export BROWSER_PILOT_SYSTEM_PROMPT="/path/to/reliable-testing.txt"

# Combine prompts
cat general-rules.txt domain-specific.txt > combined-prompt.txt
browser-copilot examples/google-ai-search.md --system-prompt combined-prompt.txt
```

## CI/CD Configuration

### GitHub Actions

`.github/workflows/browser-tests.yml`:
```yaml
name: Browser Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: uv sync

    - name: Install Playwright browsers
      run: npx playwright install chromium

    - name: Configure ModelForge
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        uv run modelforge config add --provider openai --model gpt-3.5-turbo

    - name: Run tests
      run: |
        uv run browser-copilot tests/smoke-test.md \
          --headless \
          --output-format junit \
          --output-file test-results.xml \
          --compression-level high

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          test-results.xml
          ~/.browser_copilot/sessions/*/reports/
          ~/.browser_copilot/sessions/*/screenshots/
```

### Jenkins Pipeline

`Jenkinsfile`:
```groovy
pipeline {
    agent any

    environment {
        BROWSER_PILOT_PROVIDER = 'openai'
        BROWSER_PILOT_MODEL = 'gpt-3.5-turbo'
        BROWSER_PILOT_HEADLESS = 'true'
        BROWSER_PILOT_COMPRESSION_LEVEL = 'high'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
                sh 'uv sync'
                sh 'npx playwright install chromium'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    uv run browser-copilot tests/*.md \
                        --output-format junit \
                        --output-file results.xml
                '''
            }
        }
    }

    post {
        always {
            junit 'results.xml'
            archiveArtifacts artifacts: '~/.browser_copilot/sessions/*/reports/*'
        }
    }
}
```

### Docker Configuration

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project
WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync
RUN npx playwright install --with-deps chromium

# Run tests
CMD ["uv", "run", "browser-copilot", "test.md", "--headless"]
```

### Environment-Specific Configs

`config.dev.json`:
```json
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "headless": false,
  "verbose": true,
  "compression_level": "low"
}
```

`config.staging.json`:
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "headless": true,
  "verbose": false,
  "compression_level": "medium",
  "timeout": 600
}
```

`config.prod.json`:
```json
{
  "provider": "anthropic",
  "model": "claude-3-opus",
  "headless": true,
  "verbose": false,
  "compression_level": "high",
  "timeout": 300
}
```

Usage:
```bash
# Development
browser-copilot examples/google-ai-search.md --config config.dev.json

# Staging
browser-copilot examples/saucedemo-shopping.md --config config.staging.json

# Production
browser-copilot examples/icims-ats-job-search.md --config config.prod.json
```
