# Browser Copilot 🎯

A streamlined browser automation framework that uses AI-powered agents to execute natural language test scenarios.

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://badge.fury.io/py/browser-copilot-llm.svg)](https://pypi.org/project/browser-copilot-llm/)
[![CI Status](https://github.com/smiao-icims/browser-copilot/workflows/CI/badge.svg)](https://github.com/smiao-icims/browser-copilot/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Coverage](https://codecov.io/gh/smiao-icims/browser-copilot/branch/main/graph/badge.svg)](https://codecov.io/gh/smiao-icims/browser-copilot)

## 🎯 Getting Started in 3 Minutes

### Option 1: Install from PyPI (Recommended)
```bash
# 1. Install Browser Copilot from PyPI
pip install browser-copilot-llm

# 2. Run the setup wizard (2 minutes)
browser-copilot --setup-wizard

# 3. Create a test file (test.md)
cat > test.md << 'EOF'
# My First Test
1. Go to https://www.google.com
2. Search for "Browser Copilot AI testing"
3. Click on the first result
4. Take a screenshot
EOF

# 4. Run your test!
browser-copilot test.md
```

### Option 2: Install from Source
```bash
# 1. Clone and install
git clone https://github.com/smiao-icims/browser-copilot.git
cd browser-copilot
uv sync

# 2. Run the setup wizard
uv run browser-copilot --setup-wizard

# 3. Create and run your test
uv run browser-copilot test.md
```

That's it! You've just automated your first browser test. 🎉

## ✨ Features

- 🤖 **AI-Powered**: Uses LLMs to understand and execute test instructions written in plain English
- 🎯 **Simple**: Write tests in markdown - no coding required
- 🚀 **Efficient**: Single agent architecture with token optimization (20-30% reduction)
- 🔧 **Flexible**: Supports multiple LLM providers via [ModelForge](https://github.com/smiao-icims/model-forge) ([PyPI](https://pypi.org/project/model-forge-llm/))
- 📊 **Insightful**: Enhanced reports with timing, token usage, and cost analysis
- 🌐 **Cross-Browser**: Supports Chromium, Chrome, Firefox, Safari, Edge, and WebKit
- 🔍 **Verbose Mode**: Step-by-step debugging with dual console/file logging
- 💰 **Cost Optimization**: Built-in token optimization to reduce API costs
- 📝 **Multiple Formats**: Export results as JSON, YAML, XML, JUnit, HTML, or Markdown
- 🎛️ **Customizable**: System prompts, browser settings, and optimization levels
- 🧙 **Setup Wizard**: Interactive configuration with arrow-key navigation

## 🚀 Quick Start - Get Testing in 3 Minutes!

### 1️⃣ Install Browser Copilot

#### Option A: Install from PyPI (Recommended)
```bash
# Install with pip
pip install browser-copilot-llm

# Or with uv (faster)
uv pip install browser-copilot-llm
```

#### Option B: Install from Source
```bash
# Clone and install
git clone https://github.com/smiao-icims/browser-copilot.git
cd browser-copilot
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv if needed
uv sync  # Install dependencies
```

### 2️⃣ Run Setup Wizard (2 minutes)

```bash
# If installed from PyPI:
browser-copilot --setup-wizard

# If installed from source:
uv run browser-copilot --setup-wizard
```

The wizard will guide you through:
- 🤖 Selecting an LLM provider (GitHub Copilot recommended - no API key!)
- 🔐 Authentication setup
- 🌐 Browser configuration
- ✅ Validation with a test prompt

### 3️⃣ Create Your First Test

Create a file `my-test.md` with natural language instructions:

```markdown
# My First Test

1. Navigate to https://www.wikipedia.org
2. Search for "artificial intelligence"
3. Verify the page shows results about AI
4. Take a screenshot
```

### 4️⃣ Run Your Test!

```bash
# If installed from PyPI:
browser-copilot my-test.md

# If installed from source:
uv run browser-copilot my-test.md

# That's it! 🎉 You've just automated your first browser test.
```

### 🎯 Try Our Example Tests

> **Note**: If you installed from PyPI, first download the examples:
> ```bash
> # Download examples
> curl -O https://raw.githubusercontent.com/smiao-icims/browser-copilot/main/examples/saucedemo-shopping.md
> curl -O https://raw.githubusercontent.com/smiao-icims/browser-copilot/main/examples/google-ai-search.md
> ```

#### E-commerce Shopping Flow
```bash
# Run a complete shopping cart test
browser-copilot saucedemo-shopping.md

# Or from source repository:
uv run browser-copilot examples/saucedemo-shopping.md
```

This example demonstrates:
- Login with test credentials
- Adding products to cart
- Checkout process with form filling
- Order confirmation

#### AI-Powered Search
```bash
# Test Google's AI search features
browser-copilot google-ai-search.md

# Or from source repository:
uv run browser-copilot examples/google-ai-search.md
```

This example shows:
- Navigating to Google
- Using AI-powered search
- Verifying AI-generated responses
- Taking screenshots of results

👉 **Check out more examples in the `examples/` directory!**

### 💡 Pro Tips for Quick Success

```bash
# Save typing with an alias
alias bp="browser-copilot"  # For PyPI installation
# or
alias bp="uv run browser-copilot"  # For source installation

# Run any test headless
bp your-test.md --headless

# Get beautiful HTML reports
bp your-test.md --output-format html --output-file report.html

# Save money with token optimization
bp your-test.md --compression-level high  # 30% less tokens!

# Debug failing tests
bp failing-test.md --verbose --save-trace
```


👉 **[See More Examples](docs/COMMON_USE_CASES.md)** | 📘 **[Full Quick Start Guide](docs/QUICK_START.md)** | 🎯 **[Best Practices](docs/BEST_PRACTICES.md)**

## 📝 Writing Tests

Tests are written in simple markdown format with numbered steps:

```markdown
# Login Test

1. Navigate to https://example.com/login
2. Click on the email input field
3. Type "user@example.com"
4. Click on the password field  
5. Type "securepassword123"
6. Click the "Login" button
7. Verify that the dashboard page is displayed
8. Take a screenshot of the dashboard
```

## 📊 Example Output

```
╔═══════════════════════════════════════════╗
║      Browser Copilot v2.0                   ║
║   Simple • Reliable • Token Efficient     ║
╚═══════════════════════════════════════════╝

📄 Test Suite: login_test.md
   Size: 245 chars

🤖 Provider: github_copilot
   Model: gpt-4o

🚀 Executing test...
   Browser: chromium
   Mode: Headed

--------------------------------------------------
Status: ✅ PASSED
Duration: 28.3s
Steps: 15

📊 Token Usage:
   Total: 12,847
   Prompt: 12,214
   Completion: 633
   Cost: $0.0421

💡 Token Optimization:
   Reduction: 23.5%
   Tokens Saved: 3,200
   Cost Savings: $0.0096
   Strategies: whitespace, phrases, redundancy

📝 Results saved:
   - report: report_20250726_173422.md
   - results: results_20250726_173422.json
```

## 🆕 New Features in v2.0

### 🔍 Enhanced Verbose Mode
```bash
# Enable detailed step-by-step logging
browser-copilot test.md --verbose

# Logs are saved to ~/.browser_copilot/logs/
# Both console and file output for debugging
```

### 💰 Token Optimization
```bash
# Control optimization level
browser-copilot test.md --compression-level high  # 30% reduction
browser-copilot test.md --compression-level medium # 20% reduction (default)
browser-copilot test.md --compression-level low   # 10% reduction
browser-copilot test.md --no-token-optimization   # Disable
```

### 📤 Flexible Output Options
```bash
# Different output formats
browser-copilot test.md --output-format json
browser-copilot test.md --output-format yaml
browser-copilot test.md --output-format xml
browser-copilot test.md --output-format junit
browser-copilot test.md --output-format html
browser-copilot test.md --output-format markdown

# Output to file instead of console
browser-copilot test.md --output-file results.json
```

### 🎛️ Custom System Prompts
```bash
# Use custom instructions
browser-copilot test.md --system-prompt custom-prompt.txt

# Example prompt file:
cat > prompt.txt << EOF
You are a meticulous QA engineer. 
Always take screenshots before and after actions.
Wait 2 seconds after each navigation.
EOF
```

### 🔧 Configuration Management
```bash
# Save current settings as defaults
browser-copilot test.md --provider openai --model gpt-4 --save-config

# Use custom config file
browser-copilot test.md --config my-config.json

# Environment variables (override config file)
export BROWSER_PILOT_PROVIDER=anthropic
export BROWSER_PILOT_MODEL=claude-3-opus
export BROWSER_PILOT_BROWSER=firefox
```

## 🔧 Configuration

### Prerequisites

1. **Python 3.11+** (required by ModelForge)
2. **Node.js** (for Playwright MCP server)
3. **uv** - Fast Python package installer and resolver
4. **ModelForge** configured with at least one LLM provider

### Command Line Options

```
positional arguments:
  test_scenario         Test scenario file path or '-' for stdin

options:
  -h, --help           Show help message
  --provider PROVIDER  LLM provider (uses ModelForge discovery if not specified)
  --model MODEL        Model name (uses provider default if not specified)
  --browser BROWSER    Browser: chromium, chrome, firefox, safari, edge
  --headless           Run browser in headless mode
  --viewport-width W   Browser viewport width (default: 1920)
  --viewport-height H  Browser viewport height (default: 1080)
  -v, --verbose        Enable verbose output with step-by-step debugging
  -q, --quiet          Suppress all output except errors
  --output-format FMT  Output format: json, yaml, xml, junit, html, markdown
  --output-file FILE   Save results to file (stdout if not specified)
  --system-prompt FILE Custom system prompt file
  --timeout SECONDS    Test execution timeout
  --retry COUNT        Number of retries on failure
  --no-screenshots     Disable screenshot capture
  --no-token-optimization  Disable token optimization
  --config FILE        Path to configuration file
  --save-config        Save current settings as defaults
```

### Setting up ModelForge

```bash
# ModelForge is already installed with Browser Copilot (via model-forge-llm package)
# Just configure a provider:

# Configure a provider (e.g., GitHub Copilot)
modelforge config add --provider github_copilot --model gpt-4o

# Check configuration
modelforge config show
```

## 📁 Project Structure

```
browser-copilot/
├── browser_pilot/          # Main package
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── core.py            # Core automation engine
│   ├── cli.py             # Command-line interface
│   ├── reporter.py        # Report generation
│   ├── config_manager.py  # Configuration management
│   ├── storage_manager.py # Local storage handling
│   ├── io_handlers.py     # Input/output formatting
│   ├── verbose_logger.py  # Enhanced logging
│   ├── token_optimizer.py # Token optimization
│   └── test_enhancer.py   # Test suite enhancement
├── examples/              # Example test suites
│   ├── google-ai-search.md    # Google AI search test
│   └── saucedemo-shopping.md  # E-commerce shopping cart test
├── docs/                  # Documentation
│   └── specs/            # Technical specifications
└── tests/                 # Unit tests
```

## 📂 Local Storage

Browser Copilot stores data in platform-specific locations:

- **macOS**: `~/Library/Application Support/browser_pilot/`
- **Windows**: `%LOCALAPPDATA%\browser_pilot\`
- **Linux**: `~/.browser_copilot/`

Storage structure:
```
~/.browser_copilot/
├── logs/         # Verbose execution logs
├── settings/     # Configuration files
├── reports/      # Test reports
├── screenshots/  # Captured screenshots
├── cache/        # Temporary files
└── memory/       # Future: persistent memory

## 🎓 Learn More

- 📘 **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 5 minutes
- 🧙 **[Configuration Wizard Guide](docs/WIZARD_GUIDE.md)** - Interactive setup walkthrough
- 🎯 **[Common Use Cases](docs/COMMON_USE_CASES.md)** - Real-world testing examples
- 🔍 **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Solve common issues
- 🛠️ **[Configuration Guide](docs/CONFIGURATION.md)** - Advanced configuration
- 📊 **[Performance Guide](docs/PERFORMANCE.md)** - Optimization tips

## 🌟 Example Test Suites

Learn from our comprehensive examples in the `examples/` directory:

### 🛒 `saucedemo-shopping.md`
Complete e-commerce workflow including:
- User authentication
- Product browsing and selection
- Shopping cart management
- Multi-step checkout process
- Order confirmation

### 🔍 `google-ai-search.md`
AI-powered search testing:
- Google AI mode activation
- Search query execution
- AI response validation
- Screenshot capture
- Different search scenarios

Run any example:
```bash
# With PyPI installation (after downloading examples):
browser-copilot saucedemo-shopping.md
browser-copilot google-ai-search.md --headless

# With source installation:
uv run browser-copilot examples/saucedemo-shopping.md
uv run browser-copilot examples/google-ai-search.md --headless
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph)
- Browser automation powered by [Playwright](https://playwright.dev/) via [MCP](https://github.com/modelcontextprotocol)
- LLM management by [ModelForge](https://github.com/smiao-icims/model-forge)

---

<p align="center">
  <strong>Browser Copilot</strong> - Making browser testing as easy as writing a todo list 📝
  <br>
  Made with ❤️ by the Browser Copilot Team
</p>